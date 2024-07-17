import logging
import traceback
from concurrent.futures import ThreadPoolExecutor
from typing import List, Dict

from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import (
    ChatPromptTemplate,
    SystemMessagePromptTemplate,
)
from langchain_core.runnables import Runnable
from langsmith import traceable, get_current_run_tree
from weaviate.collections.classes.filters import Filter

from .code_feedback_pipeline import CodeFeedbackPipeline
from .interaction_suggestion_pipeline import InteractionSuggestionPipeline
from .lecture_chat_pipeline import LectureChatPipeline
from ..pipeline import Pipeline
from ..prompts.iris_exercise_chat_prompts import (
    iris_initial_system_prompt,
    chat_history_system_prompt,
    final_system_prompt,
    guide_system_prompt,
)
from ..shared.citation_pipeline import CitationPipeline
from ..shared.reranker_pipeline import RerankerPipeline
from ...common import convert_iris_message_to_langchain_message
from ...domain import ExerciseChatPipelineExecutionDTO
from ...domain import PyrisMessage
from ...domain.chat.interaction_suggestion_dto import (
    InteractionSuggestionPipelineExecutionDTO,
)
from ...domain.chat.lecture_chat.lecture_chat_pipeline_execution_dto import (
    LectureChatPipelineExecutionDTO,
)
from ...domain.data.build_log_entry import BuildLogEntryDTO
from ...domain.data.feedback_dto import FeedbackDTO
from ...domain.data.programming_submission_dto import ProgrammingSubmissionDTO
from ...llm import CapabilityRequestHandler, RequirementList
from ...llm import CompletionArguments
from ...llm.langchain import IrisLangchainChatModel
from ...retrieval.lecture_retrieval import LectureRetrieval
from ...vector_database.database import VectorDatabase
from ...vector_database.lecture_schema import LectureSchema
from ...web.status.status_update import ExerciseChatStatusCallback

logger = logging.getLogger()
logger.setLevel(logging.INFO)


class ExerciseChatPipeline(Pipeline):
    """Exercise chat pipeline that answers exercises related questions from students."""

    llm: IrisLangchainChatModel
    pipeline: Runnable
    callback: ExerciseChatStatusCallback
    suggestion_pipeline: InteractionSuggestionPipeline
    code_feedback_pipeline: CodeFeedbackPipeline
    prompt: ChatPromptTemplate

    def __init__(self, callback: ExerciseChatStatusCallback):
        super().__init__(implementation_id="exercise_chat_pipeline")
        # Set the langchain chat model
        completion_args = CompletionArguments(temperature=0, max_tokens=2000)
        self.llm = IrisLangchainChatModel(
            request_handler=CapabilityRequestHandler(
                requirements=RequirementList(
                    gpt_version_equivalent=4.5,
                    context_length=16385,
                )
            ),
            completion_args=completion_args,
        )

        self.callback = callback

        # Create the pipelines
        self.db = VectorDatabase()
        self.suggestion_pipeline = InteractionSuggestionPipeline(variant="exercise")
        self.retriever = LectureRetrieval(self.db.client)
        self.reranker_pipeline = RerankerPipeline()
        self.code_feedback_pipeline = CodeFeedbackPipeline()
        self.pipeline = self.llm | StrOutputParser()
        self.citation_pipeline = CitationPipeline()
        self.lecture_chat_pipeline = LectureChatPipeline()

    def __repr__(self):
        return f"{self.__class__.__name__}(llm={self.llm})"

    def __str__(self):
        return f"{self.__class__.__name__}(llm={self.llm})"

    @traceable(name="Exercise Chat Pipeline")
    def __call__(self, dto: ExerciseChatPipelineExecutionDTO):
        """
        Runs the pipeline
        :param dto:  execution data transfer object
        :param kwargs: The keyword arguments
        """
        try:
            should_execute_lecture_pipeline = self.should_execute_lecture_pipeline(
                dto.course.id
            )
            self._run_exercise_chat_pipeline(dto, should_execute_lecture_pipeline),
            self.callback.done(
                "Generated response", final_result=self.exercise_chat_response
            )

            try:
                if dto.course.id == 346:
                    self.callback.skip(
                        "Skipping suggestion generation as the course is not supported."
                    )
                elif self.exercise_chat_response:
                    suggestion_dto = InteractionSuggestionPipelineExecutionDTO()
                    suggestion_dto.chat_history = dto.chat_history
                    suggestion_dto.last_message = self.exercise_chat_response
                    suggestion_dto.problem_statement = dto.exercise.problem_statement
                    suggestions = self.suggestion_pipeline(suggestion_dto)
                    self.callback.done(final_result=None, suggestions=suggestions)
                else:
                    # This should never happen but whatever
                    self.callback.skip(
                        "Skipping suggestion generation as no output was generated."
                    )
            except Exception as e:
                logger.error(
                    "An error occurred while running the course chat interaction suggestion pipeline",
                    exc_info=e,
                )
                traceback.print_exc()
                self.callback.error(
                    "Generating interaction suggestions failed.", exception=e
                )
        except Exception as e:
            traceback.print_exc()
            self.callback.error(f"Failed to generate response: {e}", exception=e)

    def _run_exercise_chat_pipeline(
        self,
        dto: ExerciseChatPipelineExecutionDTO,
        should_execute_lecture_pipeline: bool = False,
    ):
        """
        Runs the pipeline
        :param dto:  execution data transfer object
        :param kwargs: The keyword arguments
        """
        self.exercise_chat_response = self.lecture_chat_pipeline(
            LectureChatPipelineExecutionDTO(
                course=dto.course,
                chat_history=dto.chat_history,
                user=dto.user,
                settings=dto.settings,
                initial_stages=dto.initial_stages,
            )
        )

        self.callback.in_progress()

        self.callback.done()

        try:
            self.callback.done()
            return self.exercise_chat_response

        except Exception as e:
            self.callback.error(f"Failed to create response: {e}", exception=e)
            # print stack trace
            traceback.print_exc()
            return "Failed to generate response"

    def _add_conversation_to_prompt(
        self,
        chat_history: List[PyrisMessage],
        user_question: PyrisMessage,
    ):
        """
        Adds the chat history and user question to the prompt
            :param chat_history: The chat history
            :param user_question: The user question
            :return: The prompt with the chat history
        """
        if chat_history is not None and len(chat_history) > 0:
            chat_history_messages = [
                convert_iris_message_to_langchain_message(message)
                for message in chat_history[-4:]
            ]
            self.prompt += SystemMessagePromptTemplate.from_template(
                chat_history_system_prompt
            )
            self.prompt += chat_history_messages
        self.prompt += SystemMessagePromptTemplate.from_template(
            "Consider the student's newest and latest input:"
        )
        self.prompt += convert_iris_message_to_langchain_message(user_question)

    def _add_exercise_context_to_prompt(
        self,
        submission: ProgrammingSubmissionDTO,
    ):
        """Adds the exercise context to the prompt
        :param submission: The submission
        :param selected_files: The selected files
        """
        self.prompt += SystemMessagePromptTemplate.from_template(
            "Consider the following exercise context:\n"
            "- Title: {exercise_title}\n"
            "- Problem Statement: {problem_statement}\n"
            "- Exercise programming language: {programming_language}"
        )

    def _add_feedbacks_to_prompt(self, feedbacks: List[FeedbackDTO]):
        """Adds the feedbacks to the prompt
        :param feedbacks: The feedbacks
        """
        if feedbacks is not None and len(feedbacks) > 0:
            prompt = (
                "These are the feedbacks for the student's repository:\n%s"
            ) % "\n---------\n".join(str(log) for log in feedbacks)
            self.prompt += SystemMessagePromptTemplate.from_template(prompt)

    def _add_relevant_chunks_to_prompt(self, retrieved_lecture_chunks: List[dict]):
        """
        Adds the relevant chunks of the lecture to the prompt
        :param retrieved_lecture_chunks: The retrieved lecture chunks
        """
        txt = "Next you will find the potentially relevant lecture content to answer the student message."
        "Use this context to enrich your response.\n"

        for chunk in retrieved_lecture_chunks:
            props = chunk.get("properties", {})
            lct = "Lecture: {}, Page: {}\nContent:\n---{}---\n\n".format(
                props.get(LectureSchema.LECTURE_NAME.value),
                props.get(LectureSchema.PAGE_NUMBER.value),
                props.get(LectureSchema.PAGE_TEXT_CONTENT.value),
            )
            txt += lct

        self.prompt += SystemMessagePromptTemplate.from_template(
            txt.replace("{", "{{").replace("}", "}}")
        )

    def should_execute_lecture_pipeline(self, course_id: int) -> bool:
        """
        Checks if the lecture pipeline should be executed
        :param course_id: The course ID
        :return: True if the lecture pipeline should be executed
        """
        if course_id:
            # Fetch the first object that matches the course ID with the language property
            result = self.db.lectures.query.fetch_objects(
                filters=Filter.by_property(LectureSchema.COURSE_ID.value).equal(
                    course_id
                ),
                limit=1,
                return_properties=[LectureSchema.COURSE_NAME.value],
            )
            return len(result.objects) > 0
        return False

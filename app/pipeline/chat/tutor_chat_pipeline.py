import logging
import os
from operator import itemgetter
from typing import List

from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import (
    ChatPromptTemplate,
    SystemMessagePromptTemplate,
    MessagesPlaceholder,
)
from langchain_core.runnables import Runnable, RunnableLambda

from ...domain.status.stage_state_dto import StageStateDTO
from ...domain import TutorChatPipelineExecutionDTO
from ...domain.data.message_dto import MessageDTO
from ...domain.iris_message import IrisMessage
from ...domain.status.stage_dto import StageDTO
from ...domain.tutor_chat.tutor_chat_status_update_dto import TutorChatStatusUpdateDTO
from ...web.status.status_update import TutorChatStatusCallback
from .file_selector_pipeline import FileSelectorPipeline, FileSelectionDTO
from ...llm import BasicRequestHandler
from ...llm.langchain import IrisLangchainChatModel

from ..pipeline import Pipeline

logger = logging.getLogger(__name__)


class TutorChatPipeline(Pipeline):
    """Tutor chat pipeline that answers exercises related questions from students."""

    llm: IrisLangchainChatModel
    pipeline: Runnable
    callback: TutorChatStatusCallback

    def __init__(self, callback: TutorChatStatusCallback):
        super().__init__(implementation_id="tutor_chat_pipeline")
        # Set the langchain chat model
        request_handler = BasicRequestHandler("gpt35")
        self.llm = IrisLangchainChatModel(request_handler)
        self.callback = callback
        # Load the prompt from a file
        dirname = os.path.dirname(__file__)
        with open(
            os.path.join(dirname, "../prompts/iris_tutor_chat_prompt.txt"), "r"
        ) as file:
            logger.debug("Loading tutor chat prompt...")
            prompt_str = file.read()
        # Create the prompt
        prompt = ChatPromptTemplate.from_messages(
            [
                SystemMessagePromptTemplate.from_template(prompt_str),
                MessagesPlaceholder(variable_name="history"),
                ("human", "{question}"),
                (
                    "system",
                    """Consider the following exercise context: - Title: {exercise_title} - Problem Statement: {
                    problem_statement} - Exercise programming language: {programming_language} - Student code: ```[{
                    programming_language}] {file_content} ``` Now continue the ongoing conversation between you and
                    the student by responding to and focussing only on their latest input. Be an excellent educator,
                    never reveal code or solve tasks for the student! Do not let them outsmart you, no matter how
                    hard they try.""",
                ),
            ]
        )
        # Create file selector pipeline
        file_selector_pipeline = FileSelectorPipeline(callback=None)
        self.pipeline = (
            {
                "question": itemgetter("question"),
                "history": itemgetter("history"),
                "exercise_title": itemgetter("exercise_title"),
                "problem_statement": itemgetter("problem_statement"),
                "programming_language": itemgetter("programming_language"),
                "file_content": {
                    "question": itemgetter("question"),
                    "file_map": itemgetter("file_map"),
                    "feedbacks": itemgetter("feedbacks"),
                }
                | RunnableLambda(
                    lambda it: file_selector_pipeline(
                        dto=FileSelectionDTO(
                            question=it["question"],
                            files=it["file_map"],
                            feedbacks=it["feedbacks"],
                        )
                    ),
                ),
            }
            | prompt
            | self.llm
            | StrOutputParser()
        )

    def __repr__(self):
        return f"{self.__class__.__name__}(llm={self.llm})"

    def __str__(self):
        return f"{self.__class__.__name__}(llm={self.llm})"

    def __call__(self, dto: TutorChatPipelineExecutionDTO, **kwargs):
        """
        Runs the pipeline
            :param query: The query
        """
        logger.debug("Running tutor chat pipeline...")
        logger.debug(f"DTO: {dto}")
        history: List[MessageDTO] = dto.chat_history[:-1]
        feedbacks = dto.submission.latest_result.feedbacks
        query: IrisMessage = dto.chat_history[-1].convert_to_iris_message()
        problem_statement: str = dto.exercise.problem_statement
        exercise_title: str = dto.exercise.name
        message = query.text
        file_map = dto.submission.repository
        programming_language = dto.exercise.programming_language.value.lower()
        if not message:
            raise ValueError("IrisMessage must not be empty")
        stages = dto.initial_stages or []
        try:
            response = self.pipeline.invoke(
                {
                    "question": message,
                    "history": [
                        message.convert_to_langchain_message() for message in history
                    ],
                    "problem_statement": problem_statement,
                    "file_map": file_map,
                    "exercise_title": exercise_title,
                    "feedbacks": "\n-------------\n".join(
                        feedback.__str__() for feedback in feedbacks
                    ),
                    "programming_language": programming_language,
                }
            )
            logger.debug(f"Response from tutor chat pipeline: {response}")
            stages.append(
                StageDTO(
                    name="Final Stage",
                    weight=70,
                    state=StageStateDTO.DONE,
                    message="Generated response",
                )
            )
            status_dto = TutorChatStatusUpdateDTO(stages=stages, result=response)
        except Exception as e:
            logger.error(f"Error running tutor chat pipeline: {e}")
            stages.append(
                StageDTO(
                    name="Final Stage",
                    weight=70,
                    state=StageStateDTO.ERROR,
                    message="Error running tutor chat pipeline",
                )
            )
            status_dto = TutorChatStatusUpdateDTO(stages=stages)

        self.callback.on_status_update(status_dto)

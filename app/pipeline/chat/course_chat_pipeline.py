import json
import logging
from datetime import datetime
from typing import List, Optional, Union

from langchain.agents import create_structured_chat_agent, AgentExecutor
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import (
    ChatPromptTemplate,
    SystemMessagePromptTemplate,
    AIMessagePromptTemplate, MessagesPlaceholder,
)
from langchain_core.runnables import Runnable
from langchain_core.tools import tool

from ...common import convert_iris_message_to_langchain_message
from ...domain import PyrisMessage
from ...domain.data.exercise_dto import ExerciseDTO
from ...llm import CapabilityRequestHandler, RequirementList
from ..prompts.iris_course_chat_prompts import (
    iris_initial_system_prompt,
    chat_history_system_prompt,
    final_system_prompt,
    guide_system_prompt,
)
from ...domain import CourseChatPipelineExecutionDTO
from ...web.status.status_update import (
    CourseChatStatusCallback,
)
from ...llm import CompletionArguments
from ...llm.langchain import IrisLangchainChatModel

from ..pipeline import Pipeline

logger = logging.getLogger(__name__)


class CourseChatPipeline(Pipeline):
    """Course chat pipeline that answers course related questions from students."""

    llm: IrisLangchainChatModel
    pipeline: Runnable
    callback: CourseChatStatusCallback
    prompt: ChatPromptTemplate

    def __init__(self, callback: CourseChatStatusCallback):
        super().__init__(implementation_id="course_chat_pipeline")
        # Set the langchain chat model
        request_handler = CapabilityRequestHandler(
            requirements=RequirementList(
                gpt_version_equivalent=4.5,
                context_length=16385,
                json_mode=True,
            )
        )
        completion_args = CompletionArguments(temperature=0.1, max_tokens=2000)
        self.llm = IrisLangchainChatModel(
            request_handler=request_handler, completion_args=completion_args
        )
        self.callback = callback

        # Create the pipeline
        self.pipeline = self.llm | StrOutputParser()

    def __repr__(self):
        return f"{self.__class__.__name__}(llm={self.llm})"

    def __str__(self):
        return f"{self.__class__.__name__}(llm={self.llm})"

    def __call__(self, dto: CourseChatPipelineExecutionDTO, **kwargs):
        """
        Runs the pipeline
            :param dto: The pipeline execution data transfer object
            :param kwargs: The keyword arguments
        """

        self.callback.in_progress()


        logger.info("Running course chat pipeline...")
        history: List[PyrisMessage] = dto.base.chat_history[:-1]
        query: PyrisMessage = dto.base.chat_history[-1]
        name: str = dto.course.name
        description: str = dto.course.description
        programming_language: str = dto.course.default_programming_language
        start_date: str = datetime_to_string(dto.course.start_time)
        end_date: str = datetime_to_string(dto.course.end_time)

        textprompt = ""+iris_initial_system_prompt
        if (history is not None and len(history) > 0):
            textprompt += chat_history_system_prompt



          # Set up the initial prompt
        self.prompt = ChatPromptTemplate.from_messages(
            [
                ("system", textprompt),
            ]
        )


        print(dto.metrics)


        # Add the conversation to the prompt
        chat_history_messages = [
            convert_iris_message_to_langchain_message(message)
            for message in history
        ]
        self.prompt += ChatPromptTemplate.from_messages(chat_history_messages)
        self.prompt += ChatPromptTemplate.from_messages([
            ("system", final_system_prompt),
            ("human", query.contents[0].text_content)
        ])

        def get_student_metrics(exercise_id: int) -> Union[dict, str]:
            metrics = dto.metrics.exercise_metrics
            if metrics and exercise_id in metrics.score:
                return {
                    "global_average_score": metrics.average_score[exercise_id],
                    "score_of_student": metrics.score[exercise_id],
                    "global_average_latest_submission": metrics.average_latest_submission[exercise_id],
                    "latest_submission_of_student": metrics.latest_submission[exercise_id],
                }
            else:
                return "No data available! This indicates that the student has not submitted this exercise yet."

        exercise_txt = str([{
            "details": ex,
            "metrics": get_student_metrics(ex.id)
        } for ex in dto.course.exercises])

        # Add the final message to the prompt and run the pipeline
        prompt_val = self.prompt.format_messages(
            course_name=name,
            course_description=description,
            programming_language=programming_language,
            course_start_date=start_date,
            course_end_date=end_date,
            exercises=exercise_txt,
        )
        self.prompt = ChatPromptTemplate.from_messages(prompt_val)
        try:
            response_draft = (self.prompt | self.pipeline).invoke({})
            self.callback.done(None, final_result=response_draft)
            return
            print("THE RESPONSE DRAFT IS: ", response_draft)
            self.prompt += AIMessagePromptTemplate.from_template(f"{response_draft}")
            self.prompt += SystemMessagePromptTemplate.from_template(
                guide_system_prompt
            )
            response = (self.prompt | self.pipeline).invoke({})
            logger.info(f"Response from tutor chat pipeline: {response}")
            self.callback.done(None, final_result=response)
        except Exception as e:
            self.callback.error(f"Failed to generate response: {e}")


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

 #           self.prompt += chat_history_messages
            self.prompt += SystemMessagePromptTemplate.from_template(
                "Now, consider the student's newest and latest input:"
            )
        self.prompt += convert_iris_message_to_langchain_message(user_question)


def datetime_to_string(dt: Optional[datetime]) -> str:
    if dt is None:
        return "No date provided"
    else:
        return dt.strftime("%Y-%m-%d %H:%M:%S")
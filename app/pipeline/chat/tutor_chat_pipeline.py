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

from domain import TutorChatPipelineExecutionDTO
from domain.data.message_dto import MessageDTO
from domain.iris_message import IrisMessage
from web.status.status_update import TutorChatStatusCallback
from .file_selector_pipeline import FileSelectorPipeline, FileSelectionDTO
from ...llm import BasicRequestHandler
from ...llm.langchain import IrisLangchainChatModel

from ..pipeline import Pipeline
from ...pipeline.shared import SummaryPipeline

logger = logging.getLogger(__name__)


class IrisMessageRole:
    pass


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
            ]
        )
        # Create the pipeline
        summary_pipeline = SummaryPipeline()
        # Create file selector pipeline
        file_selector_pipeline = FileSelectorPipeline()
        self.pipeline = (
            {
                "question": itemgetter("question"),
                "history": itemgetter("history"),
                "exercise_title": itemgetter("exercise_title"),
                "summary": itemgetter("problem_statement"),
                "file_content": itemgetter("file_map")
                | RunnableLambda(
                    lambda file_map: file_selector_pipeline(
                        dto=FileSelectionDTO(
                            files=file_map.keys(), build_logs=itemgetter("build_logs")
                        )
                    ),
                    callback=None,
                )
                | RunnableLambda(
                    lambda selected_file: (
                        itemgetter("file_map")[selected_file] if selected_file else ""
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
        build_logs = dto.latest_submission.build_logs
        query: IrisMessage = dto.chat_history[-1].convert_to_iris_message()
        problem_statement: str = dto.exercise.problem_statement
        exercise_title: str = dto.exercise.name
        message = query.text
        file_map = dto.latest_submission.repository
        if not message:
            raise ValueError("IrisMessage must not be empty")
        response = self.pipeline.invoke(
            {
                "question": message,
                "history": [message.__str__() for message in history],
                "problem_statement": problem_statement,
                "file_map": file_map,
                "exercise_title": exercise_title,
                "build_logs": build_logs,
            }
        )
        logger.debug(f"Response from tutor chat pipeline: {response}")
        # TODO: Convert response to status update

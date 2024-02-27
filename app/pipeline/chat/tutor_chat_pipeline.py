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

from ...domain import IrisMessage, IrisMessageRole
from ...domain.dtos import ExerciseExecutionDTOWrapper, ExercisePipelineExecutionDTO
from ...llm import BasicRequestHandler
from ...llm.langchain import IrisLangchainChatModel

from ..pipeline import Pipeline
from ...pipeline.shared import SummaryPipeline

logger = logging.getLogger(__name__)


class TutorChatPipeline(Pipeline):
    """Tutor chat pipeline that answers exercises related questions from students."""

    llm: IrisLangchainChatModel
    pipeline: Runnable

    def __init__(self):
        super().__init__(implementation_id="tutor_chat_pipeline_reference_impl")
        # Set the langchain chat model
        request_handler = BasicRequestHandler("gpt35")
        self.llm = IrisLangchainChatModel(request_handler)
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
        self.pipeline = (
            {
                "question": itemgetter("question"),
                "history": itemgetter("history"),
                "exercise_title": itemgetter("exercise_title"),
                "summary": itemgetter("problem_statement")
                | RunnableLambda(
                    lambda stmt: summary_pipeline(query=stmt), callback=None
                ),
                "file_content": itemgetter("file_content"),
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
            :return: IrisMessage
        """
        logger.debug("Running tutor chat pipeline...")
        dto = wrapper.dto
        logger.debug(f"DTO: {dto}")
        query: IrisMessage = dto.question
        history: List[IrisMessage] = dto.chat_history
        problem_statement: str = dto.exercise.problem_statement
        exercise_title: str = dto.exercise.title
        message = query.text
        if not message:
            raise ValueError("IrisMessage must not be empty")
        response = self.pipeline.invoke(
            {
                "question": message,
                "history": [message.__str__() for message in history],
                "problem_statement": problem_statement,
                "file_content": "",  # TODO add file selector pipeline and get file content
                "exercise_title": exercise_title,
            }
        )
        logger.debug(f"Response from tutor chat pipeline: {response}")
        return IrisMessage(role=IrisMessageRole.ASSISTANT, text=response)

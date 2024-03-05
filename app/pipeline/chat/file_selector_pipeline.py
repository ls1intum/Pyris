import logging
import os
from typing import Dict

from langchain.output_parsers import PydanticOutputParser
from langchain_core.prompts import PromptTemplate
from langchain_core.runnables import Runnable
from pydantic import BaseModel

from ...llm import BasicRequestHandler
from ...llm.langchain import IrisLangchainChatModel
from ...pipeline import Pipeline
from ...pipeline.chat.output_models.output_models.selected_file_model import (
    SelectedFile,
)
from ...web.status.status_update import StatusCallback

logger = logging.getLogger(__name__)


class FileSelectionDTO(BaseModel):
    question: str
    files: Dict[str, str]
    feedbacks: str

    def __str__(self):
        return (
            f'FileSelectionDTO(files="{self.files}", query="{self.query}", build_logs="{self.build_logs}", '
            f'exercise_title="{self.exercise_title}", problem_statement="{self.problem_statement}")'
        )


class FileSelectorPipeline(Pipeline):
    """File selector pipeline that selects the relevant file from a list of files."""

    llm: IrisLangchainChatModel
    pipeline: Runnable
    callback: StatusCallback

    def __init__(self, callback: StatusCallback):
        super().__init__(implementation_id="file_selector_pipeline_reference_impl")
        request_handler = BasicRequestHandler("gpt35")
        self.llm = IrisLangchainChatModel(request_handler)
        self.callback = callback
        # Load prompt from file
        dirname = os.path.dirname(__file__)
        with open(
            os.path.join(dirname, "../prompts/file_selector_prompt.txt"), "r"
        ) as file:
            prompt_str = file.read()

        parser = PydanticOutputParser(pydantic_object=SelectedFile)
        # Create the prompt
        prompt = PromptTemplate(
            template=prompt_str,
            input_variables=["file_names", "feedbacks"],
            partial_variables={"format_instructions": parser.get_format_instructions()},
        )
        logger.debug(parser.get_format_instructions())
        # Create the pipeline
        self.pipeline = prompt | self.llm | parser

    def __call__(self, dto: FileSelectionDTO, **kwargs) -> str:
        """
        Runs the pipeline
            :param query: The query
            :return: Selected file content
        """
        print("Running file selector pipeline...")
        file_names = list(dto.files.keys())
        feedbacks = dto.feedbacks
        print(", ".join(file_names))
        response: SelectedFile = self.pipeline.invoke(
            {
                "question": dto.question,
                "file_names": ", ".join(file_names),
                "feedbacks": feedbacks,
            },
        )
        print(response)

        return f"{response.selected_file}: {dto.files[response.selected_file]} "

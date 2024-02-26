import logging
import os
from typing import List

from langchain.output_parsers import PydanticOutputParser
from langchain_core.prompts import PromptTemplate
from langchain_core.runnables import Runnable
from pydantic import BaseModel

from domain.submission import BuildLogEntry
from llm import BasicRequestHandler
from llm.langchain import IrisLangchainChatModel
from pipeline import Pipeline
from pipeline.chat.output_models.output_models.selected_file_model import SelectedFile

logger = logging.getLogger(__name__)


class FileSelectionDTO(BaseModel):
    files: List[str]
    build_logs: List[BuildLogEntry]

    def __str__(self):
        return (
            f'FileSelectionDTO(files="{self.files}", query="{self.query}", build_logs="{self.build_logs}", '
            f'exercise_title="{self.exercise_title}", problem_statement="{self.problem_statement}")'
        )


class FileSelectorPipeline(Pipeline):
    """File selector pipeline that selects the relevant file from a list of files."""

    llm: IrisLangchainChatModel
    pipeline: Runnable

    def __init__(self):
        super().__init__(implementation_id="file_selector_pipeline_reference_impl")
        request_handler = BasicRequestHandler("gpt35")
        self.llm = IrisLangchainChatModel(request_handler)
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
            input_variables=["repository", "build_log"],
            partial_variables={"format_instructions": parser.get_format_instructions()},
        )
        logger.debug(parser.get_format_instructions())
        # Create the pipeline
        self.pipeline = prompt | self.llm | parser

    def __call__(self, dto: FileSelectionDTO, **kwargs) -> SelectedFile:
        """
        Runs the pipeline
            :param query: The query
            :return: IrisMessage
        """
        logger.debug("Running file selector pipeline...")
        repository = dto.files
        build_log = dto.build_logs
        response = self.pipeline.invoke(
            {
                "repository": repository,
                "build_log": build_log,
            }
        )
        return response

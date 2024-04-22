import logging
import os
from typing import Dict, Optional, List

from langchain.output_parsers import PydanticOutputParser
from langchain_core.prompts import (
    ChatPromptTemplate,
)
from langchain_core.runnables import Runnable
from pydantic.v1 import BaseModel, Field, validator

from domain import CompetencyExtractionPipelineExecutionDTO
from llm import CapabilityRequestHandler, RequirementList
from ..prompts.competency_extraction_chat_prompts import (
    competency_extraction_initial_system_prompt,
)
from ...llm import CompletionArguments
from ...llm.langchain import IrisLangchainChatModel
from ...pipeline import Pipeline
from ...web.status.status_update import StatusCallback
from app.domain.data.competency_taxonomy import CompetencyTaxonomy

logger = logging.getLogger(__name__)


class Competency(BaseModel):
    subject: str = Field(
        description="Subject of the competency that contains at most 4 words",
        max_length=15,
    )
    description: str = Field(description="Description of the competency")
    taxonomy: CompetencyTaxonomy = Field(
        description="Selected taxonomy based on bloom's taxonomy"
    )

    @validator("subject")
    def validate_subject(cls, field):
        """Validate the subject of the competency."""
        if len(field.split()) > 4:
            raise ValueError("Subject must contain at most 4 words")
        return field

    @validator("taxonomy")
    def validate_selected_taxonomy(cls, field):
        """Validate the selected taxonomy."""
        if field not in CompetencyTaxonomy.__members__:
            raise ValueError(f"Invalid taxonomy: {field}")
        return field


class CompetencyExtractionPipeline(Pipeline):
    """"""

    llm: IrisLangchainChatModel
    pipeline: Runnable
    callback: StatusCallback
    prompt: ChatPromptTemplate
    output_parser: PydanticOutputParser
    num_iterations: int

    def __init__(self, callback: Optional[StatusCallback] = None, num_iterations=10):
        super().__init__(
            implementation_id="competency_extraction_pipeline_reference_impl"
        )
        request_handler = CapabilityRequestHandler(
            requirements=RequirementList(
                input_cost=1,
                output_cost=1,
                gpt_version_equivalent=3.5,
                context_length=4096,
                vendor="OpenAI",
                privacy_compliance=False,
                self_hosted=False,
                image_recognition=False,
                json_mode=False,
            )
        )
        self.num_iterations = num_iterations
        completion_args = CompletionArguments(temperature=0.2, max_tokens=500)
        self.llm = IrisLangchainChatModel(
            request_handler=request_handler, completion_args=completion_args
        )
        self.callback = callback
        self.output_parser = PydanticOutputParser(pydantic_object=Competency)

        logger.debug(self.output_parser.get_format_instructions())
        # Create the pipeline
        self.pipeline = self.llm | self.output_parser

    def __call__(
        self,
        dto: CompetencyExtractionPipelineExecutionDTO,
        prompt: Optional[ChatPromptTemplate] = None,
        **kwargs,
    ) -> List[Competency]:

        generated_competencies = []

        self.prompt = ChatPromptTemplate.from_messages(
            [
                ("system", competency_extraction_initial_system_prompt),
                (
                    "human",
                    """
                    Course description: {course_description}
                    Taxonomy options: {taxonomies}
                    """,
                ),
            ]
        )
        course_description = dto.course_description
        taxonomies = ", ".join(dto.taxonomy_options)

        for i in range(self.num_iterations):
            # Run the pipeline
            competency = (prompt | self.pipeline).invoke(
                {
                    "course_description": course_description,
                    "taxonomies": taxonomies,
                }
            )
            generated_competencies.append(competency)

        return generated_competencies

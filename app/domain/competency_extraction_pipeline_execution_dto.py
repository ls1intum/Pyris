from typing import List, Optional

from pydantic import Field, BaseModel

from . import PipelineExecutionDTO
from .data.competency_dto import CompetencyTaxonomy


class CompetencyExtractionPipelineExecutionDTO(BaseModel):
    execution: PipelineExecutionDTO
    course_description: Optional[str] = Field(alias="courseDescription")
    taxonomy_options: List[CompetencyTaxonomy] = Field(
        alias="taxonomyOptions", default=[]
    )
    max_n: int = Field(
        alias="maxN",
        description="Maximum number of competencies to extract from the course description",
        default=10,
    )

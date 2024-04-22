from typing import List, Optional

from pydantic import Field

from app.domain.data.competency_taxonomy import CompetencyTaxonomy
from ...domain import PipelineExecutionDTO


class CompetencyExtractionPipelineExecutionDTO(PipelineExecutionDTO):
    course_description: Optional[str] = Field(alias="courseDescription")
    taxonomy_options: List[CompetencyTaxonomy] = Field(
        alias="taxonomyOptions", default=[]
    )

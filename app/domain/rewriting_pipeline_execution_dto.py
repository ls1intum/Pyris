from typing import List

from pydantic import Field, BaseModel

from . import PipelineExecutionDTO
from .data.competency_dto import CompetencyTaxonomy, Competency


class RewritingPipelineExecutionDTO(BaseModel):
    execution: PipelineExecutionDTO
    to_be_rewritten : str = Field(alias="toBeRewritten")

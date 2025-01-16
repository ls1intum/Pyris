from typing import List

from pydantic import Field, BaseModel

from . import PipelineExecutionDTO
from .data.competency_dto import CompetencyTaxonomy, Competency


class RephrasingPipelineExecutionDTO(BaseModel):
    execution: PipelineExecutionDTO
    to_be_rephrased : str = Field(alias="toBeRephrased")

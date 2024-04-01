from typing import List, Optional

from pydantic import Field

from ..domain import PipelineExecutionDTO
from .data.lecture_unit_dto import LectureUnitDTO


class IngestionPipelineExecutionDto(PipelineExecutionDTO):
    lecture_units: List[LectureUnitDTO] = Field(alias="units", default=[])

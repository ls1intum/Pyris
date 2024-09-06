from typing import List

from pydantic import Field

from app.domain import PipelineExecutionDTO
from app.domain.data.lecture_unit_dto import LectureUnitDTO


class IngestionPipelineExecutionDto(PipelineExecutionDTO):
    lecture_unit: LectureUnitDTO = Field(..., alias="pyrisLectureUnit")
    settings: Optional[PipelineExecutionSettingsDTO]
    initial_stages: Optional[List[StageDTO]] = Field(
        default=None, alias="initialStages"
    )

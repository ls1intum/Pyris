from typing import List

from pydantic import BaseModel, Field

from ..domain.pipeline_execution_settings_dto import PipelineExecutionSettingsDTO
from ..domain.status.stage_dto import StageDTO


class PipelineExecutionDTO(BaseModel):
    settings: PipelineExecutionSettingsDTO
    initial_stages: List[StageDTO] = Field(alias="initialStages")

from typing import List, Optional

from pydantic import BaseModel, Field

from ..domain.pipeline_execution_settings_dto import PipelineExecutionSettingsDTO
from ..domain.status.stage_dto import StageDTO


class PipelineExecutionDTO(BaseModel):
    settings: PipelineExecutionSettingsDTO
    initial_stages: Optional[List[StageDTO]] = Field(
        default=None, alias="initialStages"
    )

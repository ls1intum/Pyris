from pydantic import BaseModel

from domain.pipeline_execution_settings_dto import PipelineExecutionSettingsDTO


class PipelineExecutionDTO(BaseModel):
    settings: PipelineExecutionSettingsDTO

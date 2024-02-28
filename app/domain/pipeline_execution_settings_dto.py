from typing import List

from pydantic import BaseModel, Field


class PipelineExecutionSettingsDTO(BaseModel):
    authentication_token: str = Field(alias="authenticationToken")
    allowed_models: List[str] = Field(alias="allowedModels")
    artemis_base_url: str = Field(alias="artemisBaseUrl")

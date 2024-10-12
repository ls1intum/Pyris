from datetime import datetime
from enum import Enum
from typing import List

from pydantic import BaseModel, ConfigDict, Field

from app.domain.data.message_content_dto import MessageContentDTO


class IrisMessageRole(str, Enum):
    USER = "USER"
    ASSISTANT = "LLM"
    SYSTEM = "SYSTEM"


class PyrisMessage(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    num_input_tokens: int = Field(alias="numInputTokens", default=0)
    cost_per_input_token: float = Field(alias="costPerInputToken", default=0)
    num_output_tokens: int = Field(alias="numOutputTokens", default=0)
    cost_per_output_token: float = Field(alias="costPerOutputToken", default=0)
    model_info: str = Field(alias="modelInfo", default="")

    sent_at: datetime | None = Field(alias="sentAt", default=None)
    sender: IrisMessageRole
    contents: List[MessageContentDTO] = []

    def __str__(self):
        return f"{self.sender.lower()}: {self.contents}"

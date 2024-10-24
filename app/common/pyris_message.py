from datetime import datetime
from enum import Enum
from typing import List

from pydantic import BaseModel, ConfigDict, Field

from app.domain.data.message_content_dto import MessageContentDTO
from app.common.token_usage_dto import TokenUsageDTO


class IrisMessageRole(str, Enum):
    USER = "USER"
    ASSISTANT = "LLM"
    SYSTEM = "SYSTEM"


class PyrisMessage(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    token_usage: TokenUsageDTO = Field(default_factory=TokenUsageDTO)

    sent_at: datetime | None = Field(alias="sentAt", default=None)
    sender: IrisMessageRole
    contents: List[MessageContentDTO] = []

    def __str__(self):
        return f"{self.sender.lower()}: {self.contents}"

from datetime import datetime
from enum import Enum
from typing import List
from message_content_dto import MessageContentDTO

from pydantic import BaseModel, Field


class IrisMessageSender(str, Enum):
    USER = "USER"
    LLM = "LLM"


class MessageDTO(BaseModel):
    sent_at: datetime = Field(alias="sentAt")
    sender: IrisMessageSender
    contents: List[MessageContentDTO]

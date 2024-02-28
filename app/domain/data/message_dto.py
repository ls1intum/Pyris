from datetime import datetime
from enum import Enum
from typing import List, Literal

from ...domain.iris_message import IrisMessage
from .message_content_dto import MessageContentDTO

from pydantic import BaseModel, Field


class IrisMessageSender(str, Enum):
    USER = "USER"
    LLM = "LLM"


class MessageDTO(BaseModel):
    sent_at: datetime = Field(alias="sentAt")
    sender: Literal[IrisMessageSender.USER, IrisMessageSender.LLM]
    contents: List[MessageContentDTO]

    def __str__(self):
        match self.sender:
            case IrisMessageSender.USER:
                sender = "user"
            case IrisMessageSender.LLM:
                sender = "ai"
            case _:
                raise ValueError(f"Unknown message sender: {self.sender}")
        return f"{sender}: {self.contents[0].textContent}"

    def convert_to_iris_message(self):
        match self.sender:
            case IrisMessageSender.USER:
                sender = "user"
            case IrisMessageSender.LLM:
                sender = "assistant"
            case _:
                raise ValueError(f"Unknown message sender: {self.sender}")

        return IrisMessage(text=self.contents[0].textContent, role=sender)

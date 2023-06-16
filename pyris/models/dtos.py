from enum import Enum
from pydantic import BaseModel
from datetime import datetime, timezone


class LLMModel(str, Enum):
    GPT35_TURBO = "gpt-3.5-turbo"


class ContentType(str, Enum):
    TEXT = "text"


class Content(BaseModel):
    textContent: str
    type: ContentType


class SendMessageRequest(BaseModel):
    class Template(BaseModel):
        templateId: int
        template: str

    template: Template
    preferredModel: LLMModel
    parameters: dict


class SendMessageResponse(BaseModel):
    class Message(BaseModel):
        sentAt: datetime = datetime.now(timezone.utc)
        content: Content

    usedModel: LLMModel
    message: Message

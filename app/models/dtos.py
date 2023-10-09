from enum import Enum
from pydantic import BaseModel, Field
from datetime import datetime


class LLMStatus(str, Enum):
    UP = "UP"
    DOWN = "DOWN"
    NOT_AVAILABLE = "NOT_AVAILABLE"


class ContentType(str, Enum):
    TEXT = "text"


class SendMessageRequest(BaseModel):
    class Template(BaseModel):
        id: int
        content: str

    template: Template
    preferred_model: str = Field(..., alias="preferredModel")
    parameters: dict


class SendMessageResponse(BaseModel):
    used_model: str = Field(..., alias="usedModel")
    sent_at: datetime = Field(alias="sentAt", default_factory=datetime.utcnow)
    content: dict


class ModelStatus(BaseModel):
    model: str
    status: LLMStatus


class LLMModelResponse(BaseModel):
    id: str
    name: str
    description: str

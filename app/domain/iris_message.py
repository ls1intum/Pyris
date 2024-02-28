from enum import Enum
from typing import Literal

from pydantic import BaseModel, Field


class IrisMessageRole(str, Enum):
    USER = "USER"
    ASSISTANT = "ASSISTANT"
    SYSTEM = "SYSTEM"


class IrisMessage(BaseModel):
    text: str
    role: Literal[
        IrisMessageRole.USER, IrisMessageRole.ASSISTANT, IrisMessageRole.SYSTEM
    ]

    def __str__(self):
        return f"{self.role.lower()}: {self.text}"
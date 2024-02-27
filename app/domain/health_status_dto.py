from pydantic import BaseModel
from enum import Enum


class ModelStatus(str, Enum):
    UP = "UP"
    DOWN = "DOWN"
    NOT_AVAILABLE = "NOT_AVAILABLE"


class HealthStatusDTO(BaseModel):
    model: str
    status: ModelStatus

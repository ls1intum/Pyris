from pydantic import BaseModel, Field, Json
from typing import Any


class JsonMessageContentDTO(BaseModel):
    json_content: Json[Any] | None = Field(alias="jsonContent", default=None)

from pydantic import BaseModel, Field


class TextMessageContentDTO(BaseModel):
    text_content: str | None = Field(alias="textContent", default=None)

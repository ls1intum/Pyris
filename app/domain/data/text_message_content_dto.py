from pydantic import BaseModel, Field


class TextMessageContentDTO(BaseModel):
    text_content: str = Field(alias="textContent")

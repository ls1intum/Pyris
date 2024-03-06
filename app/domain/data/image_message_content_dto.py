from pydantic import BaseModel, Field


class ImageMessageContentDTO(BaseModel):
    image_data: str | None = Field(alias="imageData", default=None)

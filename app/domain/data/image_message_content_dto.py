from pydantic import BaseModel, Field


class ImageMessageContentDTO(BaseModel):
    image_data: str = Field(alias="imageData")

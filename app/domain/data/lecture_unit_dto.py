from datetime import datetime

from pydantic import BaseModel, Field


class LectureUnitDTO(BaseModel):
    id: int
    lecture_id: int = Field(alias="lectureId")
    release_date: datetime = Field(alias="releaseDate")
    name: str
    attachment_version: int = Field(alias="attachmentVersion")

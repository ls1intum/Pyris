from pydantic import BaseModel


class CourseDTO(BaseModel):
    id: int
    name: str | None = None
    description: str | None = None

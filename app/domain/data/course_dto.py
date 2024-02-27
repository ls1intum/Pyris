from pydantic import BaseModel


class CourseDTO(BaseModel):
    id: int
    name: str
    description: str

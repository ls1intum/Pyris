from typing import Optional

from pydantic import BaseModel


class Course(BaseModel):
    id: int
    name: str
    description: Optional[str] = None

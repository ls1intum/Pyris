from pydantic import BaseModel


class PyrisModelDTO(BaseModel):
    id: str
    name: str
    description: str

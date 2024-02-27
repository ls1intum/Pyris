from pydantic import BaseModel, Field


class UserDTO(BaseModel):
    id: int
    first_name: str = Field(alias="firstName")
    last_name: str = Field(alias="lastName")

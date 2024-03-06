from pydantic import BaseModel, Field


class UserDTO(BaseModel):
    id: int
    first_name: str | None = Field(alias="firstName", default=None)
    last_name: str | None = Field(alias="lastName", default=None)

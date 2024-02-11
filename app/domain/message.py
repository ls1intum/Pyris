from enum import Enum

from domain import IrisImage


class IrisMessageRole(Enum):
    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"


class IrisMessage:
    role: IrisMessageRole
    text: str
    images: list[IrisImage] | None

    def __init__(
        self, role: IrisMessageRole, text: str, images: list[IrisImage] | None = None
    ):
        self.role = role
        self.text = text
        self.images = images

    def __str__(self):
        return f"IrisMessage(role={self.role.value}, text='{self.text}')"

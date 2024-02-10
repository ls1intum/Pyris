from enum import Enum


class IrisMessageRole(Enum):
    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"


class IrisMessage:
    role: IrisMessageRole
    message_text: str

    def __init__(self, role: IrisMessageRole, message_text: str):
        self.role = role
        self.message_text = message_text

    def __str__(self):
        return (
            f"IrisMessage(role={self.role.value}, message_text='{self.message_text}')"
        )

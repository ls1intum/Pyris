from datetime import datetime

from langchain_core.messages import BaseMessage

from ..domain.iris_message import IrisMessage, IrisMessageRole
from ..domain.data.message_dto import MessageDTO, MessageContentDTO, IrisMessageSender


def convert_iris_message_to_message_dto(iris_message: IrisMessage) -> MessageDTO:
    match iris_message.role:
        case "user":
            sender = IrisMessageSender.USER
        case "assistant":
            sender = IrisMessageSender.LLM
        case _:
            raise ValueError(f"Unknown message role: {iris_message.role}")

    return MessageDTO(
        sent_at=datetime.now(),
        sender=sender,
        contents=[MessageContentDTO(textContent=iris_message.text)],
    )


def convert_iris_message_to_langchain_message(iris_message: IrisMessage) -> BaseMessage:
    match iris_message.role:
        case IrisMessageRole.USER:
            role = "human"
        case IrisMessageRole.ASSISTANT:
            role = "ai"
        case IrisMessageRole.SYSTEM:
            role = "system"
        case _:
            raise ValueError(f"Unknown message role: {iris_message.role}")
    return BaseMessage(content=iris_message.text, type=role)


def convert_langchain_message_to_iris_message(base_message: BaseMessage) -> IrisMessage:
    match base_message.type:
        case "human":
            role = IrisMessageRole.USER
        case "ai":
            role = IrisMessageRole.ASSISTANT
        case "system":
            role = IrisMessageRole.SYSTEM
        case _:
            raise ValueError(f"Unknown message type: {base_message.type}")
    return IrisMessage(text=base_message.content, role=role)

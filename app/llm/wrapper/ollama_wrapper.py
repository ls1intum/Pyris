from ollama import Client, Message

from domain import IrisMessage
from llm import CompletionArguments
from llm.wrapper import (
    LlmChatCompletionWrapperInterface,
    LlmCompletionWrapperInterface,
    LlmEmbeddingWrapperInterface,
)


def convert_to_ollama_messages(messages: list[IrisMessage]) -> list[Message]:
    return [
        Message(role=message.role, content=message.message_text) for message in messages
    ]


def convert_to_iris_message(message: Message) -> IrisMessage:
    return IrisMessage(role=message.role, message_text=message.content)


class OllamaWrapper(
    LlmCompletionWrapperInterface,
    LlmChatCompletionWrapperInterface,
    LlmEmbeddingWrapperInterface,
):

    def __init__(self, model: str, host: str):
        self.client = Client(host=host)  # TODO: Add authentication (httpx auth?)
        self.model = model

    def completion(self, prompt: str, arguments: CompletionArguments) -> str:
        response = self.client.generate(model=self.model, prompt=prompt)
        return response["response"]

    def chat_completion(
        self, messages: list[any], arguments: CompletionArguments
    ) -> any:
        response = self.client.chat(
            model=self.model, messages=convert_to_ollama_messages(messages)
        )
        return convert_to_iris_message(response["message"])

    def create_embedding(self, text: str) -> list[float]:
        response = self.client.embeddings(model=self.model, prompt=text)
        return response

import base64
from typing import Literal, Any

from ollama import Client, Message

from domain import IrisMessage, IrisMessageRole, IrisImage
from llm import CompletionArguments
from llm.wrapper.abstract_llm_wrapper import (
    AbstractLlmChatCompletionWrapper,
    AbstractLlmCompletionWrapper,
    AbstractLlmEmbeddingWrapper,
)


def convert_to_ollama_images(images: list[IrisImage]) -> list[bytes] | None:
    if not images:
        return None
    return [base64.b64decode(image.base64) for image in images]


def convert_to_ollama_messages(messages: list[IrisMessage]) -> list[Message]:
    return [
        Message(
            role=message.role.value,
            content=message.text,
            images=convert_to_ollama_images(message.images),
        )
        for message in messages
    ]


def convert_to_iris_message(message: Message) -> IrisMessage:
    return IrisMessage(role=IrisMessageRole(message["role"]), text=message["content"])


class OllamaWrapper(
    AbstractLlmCompletionWrapper,
    AbstractLlmChatCompletionWrapper,
    AbstractLlmEmbeddingWrapper,
):
    type: Literal["ollama"]
    model: str
    host: str
    _client: Client

    def model_post_init(self, __context: Any) -> None:
        self._client = Client(host=self.host)  # TODO: Add authentication (httpx auth?)

    def completion(
        self, prompt: str, arguments: CompletionArguments, images: [IrisImage] = None
    ) -> str:
        response = self._client.generate(
            model=self.model, prompt=prompt, images=convert_to_ollama_images(images)
        )
        return response["response"]

    def chat_completion(
        self, messages: list[any], arguments: CompletionArguments
    ) -> any:
        response = self._client.chat(
            model=self.model, messages=convert_to_ollama_messages(messages)
        )
        return convert_to_iris_message(response["message"])

    def create_embedding(self, text: str) -> list[float]:
        response = self._client.embeddings(model=self.model, prompt=text)
        return list(response)

    def __str__(self):
        return f"Ollama('{self.model}')"

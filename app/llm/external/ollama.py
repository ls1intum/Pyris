import base64
from datetime import datetime
from typing import Literal, Any, Optional, Sequence, Union, Dict, Type, Callable

from langchain_core.language_models import LanguageModelInput
from langchain_core.messages import BaseMessage
from langchain_core.runnables import Runnable
from langchain_core.tools import BaseTool
from pydantic import Field, BaseModel

from ollama import Client, Message

from ...common.message_converters import map_role_to_str, map_str_to_role
from ...common.pyris_message import PyrisMessage
from ...common.token_usage_dto import TokenUsageDTO
from ...domain.data.json_message_content_dto import JsonMessageContentDTO
from ...domain.data.text_message_content_dto import TextMessageContentDTO
from ...domain.data.image_message_content_dto import ImageMessageContentDTO
from ...llm import CompletionArguments
from ...llm.external.model import ChatModel, CompletionModel, EmbeddingModel


def convert_to_ollama_images(base64_images: list[str]) -> list[bytes] | None:
    """
    Convert a list of base64 images to a list of bytes
    """
    if not base64_images:
        return None
    return [base64.b64decode(base64_image) for base64_image in base64_images]


def convert_to_ollama_messages(messages: list[PyrisMessage]) -> list[Message]:
    """
    Convert a list of PyrisMessages to a list of Ollama Messages
    """
    messages_to_return = []
    for message in messages:
        if len(message.contents) == 0:
            continue
        text_content = ""
        images = []
        for content in message.contents:
            match content:
                case ImageMessageContentDTO():
                    images.append(content.base64)
                case TextMessageContentDTO():
                    if len(text_content) > 0:
                        text_content += "\n"
                    text_content += content.text_content
                case JsonMessageContentDTO():
                    if len(text_content) > 0:
                        text_content += "\n"
                    text_content += content.json_content
                case _:
                    continue
        messages_to_return.append(
            Message(
                role=map_role_to_str(message.sender),
                content=text_content,
                images=convert_to_ollama_images(images),
            )
        )
    return messages_to_return


def convert_to_iris_message(
    message: Message, num_input_tokens: int, num_output_tokens: int, model: str
) -> PyrisMessage:
    """
    Convert a Message to a PyrisMessage
    """
    contents = [TextMessageContentDTO(text_content=message["content"])]
    tokens = TokenUsageDTO(
        numInputTokens=num_input_tokens,
        numOutputTokens=num_output_tokens,
        model=model,
    )
    return PyrisMessage(
        sender=map_str_to_role(message["role"]),
        contents=contents,
        sentAt=datetime.now(),
        token_usage=tokens,
    )


class OllamaModel(
    CompletionModel,
    ChatModel,
    EmbeddingModel,
):

    type: Literal["ollama"]
    model: str
    host: str
    options: dict[str, Any] = Field(default={})
    _client: Client

    def model_post_init(self, __context: Any) -> None:
        self._client = Client(host=self.host)  # TODO: Add authentication (httpx auth?)
        self._client._client.base_url = self.host

    def complete(
        self,
        prompt: str,
        arguments: CompletionArguments,
        image: Optional[ImageMessageContentDTO] = None,
    ) -> str:
        response = self._client.generate(
            model=self.model,
            prompt=prompt,
            images=[image.base64] if image else None,
            format="json" if arguments.response_format == "JSON" else "",
            options=self.options,
        )
        return response["response"]

    def chat(
        self, messages: list[PyrisMessage], arguments: CompletionArguments,
            tools: Optional[Sequence[Union[Dict[str, Any], Type[BaseModel], Callable, BaseTool]]]
    ) -> PyrisMessage:
        response = self._client.chat(
            model=self.model,
            messages=convert_to_ollama_messages(messages),
            format="json" if arguments.response_format == "JSON" else "",
            options=self.options,
        )
        return convert_to_iris_message(
            response.get("message"),
            response.get("prompt_eval_count", 0),
            response.get("eval_count", 0),
            response.get("model", self.model),
        )

    def embed(self, text: str) -> list[float]:
        response = self._client.embeddings(
            model=self.model, prompt=text, options=self.options
        )
        return list(response)



    def __str__(self):
        return f"Ollama('{self.model}')"

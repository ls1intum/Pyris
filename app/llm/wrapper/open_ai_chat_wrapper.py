from openai import OpenAI
from openai.lib.azure import AzureOpenAI
from openai.types.chat import ChatCompletionMessageParam

from domain import IrisMessage
from llm import CompletionArguments
from llm.wrapper import LlmChatCompletionWrapperInterface


def convert_to_open_ai_messages(
    messages: list[IrisMessage],
) -> list[ChatCompletionMessageParam]:
    return [
        ChatCompletionMessageParam(role=message.role, content=message.message_text)
        for message in messages
    ]


def convert_to_iris_message(message: ChatCompletionMessageParam) -> IrisMessage:
    return IrisMessage(role=message.role, message_text=message.content)


class OpenAIChatCompletionWrapper(LlmChatCompletionWrapperInterface):

    def __init__(self, model: str, api_key: str):
        self.client = OpenAI(api_key=api_key)
        self.model = model

    def __init__(self, client, model: str):
        self.client = client
        self.model = model

    def chat_completion(
        self, messages: list[any], arguments: CompletionArguments
    ) -> any:
        response = self.client.chat.completions.create(
            model=self.model,
            messages=convert_to_open_ai_messages(messages),
            temperature=arguments.temperature,
            max_tokens=arguments.max_tokens,
            stop=arguments.stop,
        )
        return response

    def __str__(self):
        return f"OpenAIChat('{self.model}')"


class AzureChatCompletionWrapper(OpenAIChatCompletionWrapper):

    def __init__(
        self,
        model: str,
        endpoint: str,
        azure_deployment: str,
        api_version: str,
        api_key: str,
    ):
        client = AzureOpenAI(
            azure_endpoint=endpoint,
            azure_deployment=azure_deployment,
            api_version=api_version,
            api_key=api_key,
        )
        model = model
        super().__init__(client, model)

    def __str__(self):
        return f"AzureChat('{self.model}')"

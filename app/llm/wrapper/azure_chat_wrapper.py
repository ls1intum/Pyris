from openai.lib.azure import AzureOpenAI

from llm import CompletionArguments
from llm.wrapper import LlmChatCompletionWrapperInterface, convert_to_open_ai_messages


class AzureChatCompletionWrapper(LlmChatCompletionWrapperInterface):

    def __init__(
        self,
        model: str,
        endpoint: str,
        azure_deployment: str,
        api_version: str,
        api_key: str,
    ):
        self.client = AzureOpenAI(
            azure_endpoint=endpoint,
            azure_deployment=azure_deployment,
            api_version=api_version,
            api_key=api_key,
        )
        self.model = model

    def chat_completion(
        self, messages: list[any], arguments: CompletionArguments
    ) -> any:
        response = self.client.chat.completions.create(
            model=self.model,
            messages=convert_to_open_ai_messages(messages),
        )
        return response

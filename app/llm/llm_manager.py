import os

import yaml

from common import Singleton
from llm.wrapper import LlmWrapperInterface


def create_llm_wrapper(config: dict) -> LlmWrapperInterface:
    if config["type"] == "openai":
        from llm.wrapper import OpenAICompletionWrapper

        return OpenAICompletionWrapper(model=config["model"], api_key=config["api_key"])
    elif config["type"] == "azure":
        from llm.wrapper import AzureCompletionWrapper

        return AzureCompletionWrapper(
            model=config["model"],
            endpoint=config["endpoint"],
            azure_deployment=config["azure_deployment"],
            api_version=config["api_version"],
            api_key=config["api_key"],
        )
    elif config["type"] == "openai_chat":
        from llm.wrapper import OpenAIChatCompletionWrapper

        return OpenAIChatCompletionWrapper(
            model=config["model"], api_key=config["api_key"]
        )
    elif config["type"] == "azure_chat":
        from llm.wrapper import AzureChatCompletionWrapper

        return AzureChatCompletionWrapper(
            model=config["model"],
            endpoint=config["endpoint"],
            azure_deployment=config["azure_deployment"],
            api_version=config["api_version"],
            api_key=config["api_key"],
        )
    elif config["type"] == "openai_embedding":
        from llm.wrapper import OpenAIEmbeddingWrapper

        return OpenAIEmbeddingWrapper(model=config["model"], api_key=config["api_key"])
    elif config["type"] == "azure_embedding":
        from llm.wrapper import AzureEmbeddingWrapper

        return AzureEmbeddingWrapper(
            model=config["model"],
            endpoint=config["endpoint"],
            azure_deployment=config["azure_deployment"],
            api_version=config["api_version"],
            api_key=config["api_key"],
        )
    elif config["type"] == "ollama":
        from llm.wrapper import OllamaWrapper

        return OllamaWrapper(
            model=config["model"],
            host=config["host"],
        )
    else:
        raise Exception(f"Unknown LLM type: {config['type']}")


class LlmManagerEntry:
    id: str
    llm: LlmWrapperInterface

    def __init__(self, config: dict):
        self.id = config["id"]
        self.llm = create_llm_wrapper(config)

    def __str__(self):
        return f"{self.id}: {self.llm}"


class LlmManager(metaclass=Singleton):
    llms: list[LlmManagerEntry]

    def __init__(self):
        self.llms = []
        self.load_llms()

    def get_llm_by_id(self, llm_id):
        for llm in self.llms:
            if llm.id == llm_id:
                return llm

    def load_llms(self):
        path = os.environ.get("LLM_CONFIG_PATH")
        if not path:
            raise Exception("LLM_CONFIG_PATH not set")

        with open(path, "r") as file:
            loaded_llms = yaml.safe_load(file)

        self.llms = [LlmManagerEntry(llm) for llm in loaded_llms]

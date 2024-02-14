import os

from pydantic import BaseModel, Field

import yaml

from common import Singleton
from llm.wrapper import LanguageModel, AnyLLM


# Small workaround to get pydantic discriminators working
class LLMList(BaseModel):
    llms: list[AnyLLM] = Field(discriminator="type")


def load_llms() -> dict[str, LanguageModel]:
    path = os.environ.get("LLM_CONFIG_PATH")
    assert path, "LLM_CONFIG_PATH not set"

    with open(path, "r") as file:
        yaml_dict = yaml.safe_load(file)

    llms = LLMList.model_validate({"llms": yaml_dict}).llms
    return {llm.id: llm for llm in llms}


class LlmManager(metaclass=Singleton):
    models_by_id: dict[str, LanguageModel]

    def __init__(self):
        self.models_by_id = load_llms()

    def get_by_id(self, llm_id):
        return self.models_by_id[llm_id]

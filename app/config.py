import os

from pyaml_env import parse_config
from pydantic import BaseModel, validator


class LLMModelSpecs(BaseModel):
    context_length: int


class LLMModelConfig(BaseModel):
    type: str
    name: str
    description: str


class OpenAIConfig(LLMModelConfig):
    spec: LLMModelSpecs
    llm_credentials: dict

    @validator("type")
    def check_type(cls, v):
        if v != "openai":
            raise ValueError("Invalid type:" + v + " != openai")
        return v


class StrategyLLMConfig(LLMModelConfig):
    llms: list[str]

    @validator("type")
    def check_type(cls, v):
        if v != "strategy":
            raise ValueError("Invalid type:" + v + " != strategy")
        return v


class APIKeyConfig(BaseModel):
    token: str
    comment: str
    llm_access: list[str]


class CacheSettings(BaseModel):
    class CacheParams(BaseModel):
        host: str
        port: int

    hazelcast: CacheParams


class Settings(BaseModel):
    class PyrisSettings(BaseModel):
        api_keys: list[APIKeyConfig]
        llms: dict[str, OpenAIConfig | StrategyLLMConfig]
        cache: CacheSettings

    pyris: PyrisSettings

    @classmethod
    def get_settings(cls):
        postfix = "-docker" if "DOCKER" in os.environ else ""
        if "RUN_ENV" in os.environ and os.environ["RUN_ENV"] == "test":
            file_path = f"application{postfix}.test.yml"
        else:
            file_path = f"application{postfix}.yml"

        return Settings.parse_obj(parse_config(file_path))


settings = Settings.get_settings()

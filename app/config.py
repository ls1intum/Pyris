import os
from pydantic import BaseModel
from pyaml_env import parse_config


class RedisSettings(BaseModel):
    host: str
    port: int


class Settings(BaseModel):
    class PyrisSettings(BaseModel):
        api_key: str
        redis: RedisSettings
        llm: dict

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

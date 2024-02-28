import os

from pydantic import BaseModel
import yaml


class APIKeyConfig(BaseModel):
    token: str


class Settings(BaseModel):
    class PyrisSettings(BaseModel):
        api_keys: list[APIKeyConfig]
        llm_config_path: str

    pyris: PyrisSettings

    @classmethod
    def get_settings(cls):
        postfix = "-docker" if "DOCKER" in os.environ else ""
        if "RUN_ENV" in os.environ and os.environ["RUN_ENV"] == "test":
            file_path = f"application{postfix}.test.yml"
        else:
            file_path = f"application{postfix}.yml"
        with open(file_path, "r") as file:
            settings_file = yaml.safe_load(file)
        settings_obj = Settings.parse_obj(settings_file)
        os.environ["LLM_CONFIG_PATH"] = settings_obj.pyris.llm_config_path
        return settings_obj


settings = Settings.get_settings()

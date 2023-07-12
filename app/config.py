import os
from pydantic import BaseModel
from pyaml_env import parse_config


class Settings(BaseModel):
    class PyrisSettings(BaseModel):
        class APIKeyConfig(BaseModel):
            token: str
            comment: str
            llm_access: list[str]

        class LLMModelConfig(BaseModel):
            name: str
            description: str
            llm_credentials: dict

        api_keys: list[APIKeyConfig]
        llms: dict[str, LLMModelConfig]

    pyris: PyrisSettings

    @classmethod
    def get_settings(cls):
        if "RUN_ENV" in os.environ and os.environ["RUN_ENV"] == "test":
            file_path = "application.test.yml"
        else:
            file_path = "application.yml"

        return Settings.parse_obj(parse_config(file_path))


settings = Settings.get_settings()

# get keys of settings.pyris.llms and for loop over them with print
for key in set(settings.pyris.llms.keys()):
    print(key)

for key in settings.pyris.api_keys:
    print(key)

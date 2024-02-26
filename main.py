import os

from fastapi.responses import ORJSONResponse
from fastapi import FastAPI

# Correct the import paths according to your directory structure
from web.routers.health import router as health_router
from web.routers.models import router as models_router
from web.routers.pipelines import router as pipelines_router
from web.routers import router as webhooks_router

os.environ["LLM_CONFIG_PATH"] = "/Users/kaancayli/code/playground_llm_config.yml"
# set_debug(True)

app = FastAPI(default_response_class=ORJSONResponse)


app.include_router(health_router)
app.include_router(models_router)
app.include_router(pipelines_router)
app.include_router(webhooks_router)

import os

from fastapi.responses import ORJSONResponse
from fastapi import FastAPI

from app.web.routers.health import router as health_router
from app.web.routers.models import router as models_router
from app.web.routers.pipelines import router as pipelines_router
from app.web.routers.webhooks import router as webhooks_router

os.environ["LLM_CONFIG_PATH"] = "/Users/kaancayli/code/playground_llm_config.yml"
app = FastAPI(default_response_class=ORJSONResponse)

app.include_router(health_router)
app.include_router(models_router)
app.include_router(pipelines_router)
app.include_router(webhooks_router)

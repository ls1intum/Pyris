from fastapi import FastAPI
from fastapi.responses import ORJSONResponse
from prometheus_fastapi_instrumentator import Instrumentator
from typing import Callable
from prometheus_fastapi_instrumentator.metrics import Info
from prometheus_client import Counter, Gauge
import psutil
import os

from app.routes.messages import router as messages_router

app = FastAPI(default_response_class=ORJSONResponse)

instrumentator = Instrumentator().instrument(app)


@app.on_event("startup")
async def _startup():
    def get_memory_usage():
        process = psutil.Process(os.getpid())
        memory_info = process.memory_info()
        memory_usage = memory_info.rss
        return memory_usage

    def get_cpu_usage():
        cpu_percent = psutil.cpu_percent(interval=1)
        return cpu_percent

    cpu_usage = Gauge("system_cpu_usage", "CPU Usage")
    cpu_usage.set_function(get_cpu_usage)

    memory_usage = Gauge("system_memory_usage", "Memory Usage")
    memory_usage.set_function(get_memory_usage)

    instrumentator.expose(app)


app.include_router(messages_router)

from fastapi import APIRouter, Depends

from app.dependencies import TokenValidator
from config import settings

router = APIRouter(tags=["models"])


@router.get(
    "/api/v1/models", dependencies=[Depends(TokenValidator())]
)
def send_message() -> list[str]:
    return settings.pyris.llms.keys()

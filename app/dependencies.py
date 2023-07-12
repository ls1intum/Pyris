from fastapi import Depends
from starlette.requests import Request as StarletteRequest
from app.config import settings

from app.core.custom_exceptions import (
    PermissionDeniedException,
    RequiresAuthenticationException,
)


def _get_api_key(request: StarletteRequest) -> str:
    authorization_header = request.headers.get("Authorization")

    if not authorization_header:
        raise RequiresAuthenticationException

    return authorization_header


class TokenValidator:
    async def __call__(self, request: StarletteRequest, api_key: str = Depends(_get_api_key)) -> str:
        for key in settings.pyris.api_keys:
            if key.token == api_key:
                return api_key
        raise PermissionDeniedException


class TokenPermissionsValidator:
    async def __call__(self, request: StarletteRequest, api_key: str = Depends(_get_api_key)):
        for key in settings.pyris.api_keys:
            if key.token == api_key:
                body = await request.json()
                if body.get("preferredModel") in key.llm_access:
                    return
                else:
                    raise PermissionDeniedException
        raise PermissionDeniedException




from fastapi import APIRouter, status, Response

router = APIRouter(prefix="/api/v1/models", tags=["models"])


@router.get("/")
def read_models():
    return Response(status_code=status.HTTP_501_NOT_IMPLEMENTED)

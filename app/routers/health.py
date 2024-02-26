from fastapi import APIRouter, status, Response

router = APIRouter(prefix="/api/v1/health", tags=["health"])


@router.get("/")
def health_check():
    return Response(status_code=status.HTTP_501_NOT_IMPLEMENTED)

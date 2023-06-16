from fastapi import APIRouter
from datetime import datetime, timezone

from app.models.dtos import SendMessageRequest, SendMessageResponse
from app.services.guidance_wrapper import GuidanceWrapper

router = APIRouter(tags=["messages"])


@router.post("/api/v1/messages")
def send_message(body: SendMessageRequest) -> SendMessageResponse:
    guidance = GuidanceWrapper(
        model=body.preferredModel,
        handlebars=body.template.template,
        parameters=body.parameters,
    )

    return SendMessageResponse(
        usedModel=body.preferredModel,
        message=SendMessageResponse.Message(
            sentAt=datetime.now(timezone.utc), content=guidance.query()
        ),
    )

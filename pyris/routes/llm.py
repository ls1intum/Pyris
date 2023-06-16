from datetime import datetime, timezone
from app import app
from pyris.models.dtos import SendMessageRequest, SendMessageResponse
from flask_pydantic import validate

from pyris.services.guidance_wrapper import GuidanceWrapper


@app.route("/send-message", methods=["POST"])
@validate()
def send_message(body: SendMessageRequest):
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

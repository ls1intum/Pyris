from flask import Flask
from models.dtos import SendMessageRequest, SendMessageResponse
from flask_pydantic import validate

from services.guidance_wrapper import GuidanceWrapper

app = Flask(__name__)


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
        message=SendMessageResponse.Message(content=guidance.query()),
    )


if __name__ == "__main__":
    app.run(debug=True)

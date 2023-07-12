import guidance

from app.config import settings, LLMModelConfig
from app.models.dtos import Content, ContentType


class GuidanceWrapper:
    """A wrapper service to all guidance package's methods."""

    def __init__(
        self, model: LLMModelConfig, handlebars: str, parameters=None
    ) -> None:
        if parameters is None:
            parameters = {}

        self.model = model
        self.handlebars = handlebars
        self.parameters = parameters

    def query(self) -> Content:
        """Get response from a chosen LLM model.

        Returns:
            Text content object with LLM's response.

        Raises:
            ValueError: if handlebars do not generate 'response'
        """

        template = guidance(self.handlebars)
        result = template(
            llm=self._get_llm(),
            **self.parameters,
        )

        if "response" not in result:
            raise ValueError("The handlebars do not generate 'response'")

        return Content(type=ContentType.TEXT, textContent=result["response"])

    def _get_llm(self):
        llm_credentials = self.model.llm_credentials
        return guidance.llms.OpenAI(**llm_credentials)

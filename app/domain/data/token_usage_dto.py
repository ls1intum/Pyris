from pydantic import BaseModel

from app.llm.external.PipelineEnum import PipelineEnum


class TokenUsageDTO(BaseModel):
    model_info: str
    num_input_tokens: int
    cost_per_input_token: float
    num_output_tokens: int
    cost_per_output_token: float
    pipeline: PipelineEnum

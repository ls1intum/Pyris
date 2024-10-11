from pydantic import BaseModel

from app.llm.external.PipelineEnum import PipelineEnum


class TokenUsageDTO(BaseModel):
    model_info: str
    num_input_tokens: int
    num_output_tokens: int
    pipeline: PipelineEnum
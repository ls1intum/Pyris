from app.llm.external.PipelineEnum import PipelineEnum


class LLMTokenCount:

    model_info: str
    num_input_tokens: int
    cost_per_input_token: float
    num_output_tokens: int
    cost_per_output_token: float
    pipeline: PipelineEnum

    def __init__(
        self,
        model_info: str,
        num_input_tokens: int,
        cost_per_input_token: float,
        num_output_tokens: int,
        cost_per_output_token: float,
        pipeline: PipelineEnum,
    ):
        self.model_info = model_info
        self.num_input_tokens = num_input_tokens
        self.cost_per_input_token = cost_per_input_token
        self.num_output_tokens = num_output_tokens
        self.cost_per_output_token = cost_per_output_token
        self.pipeline = pipeline

    def __str__(self):
        return (
            f"{self.model_info}: {self.num_input_tokens} in, {self.cost_per_input_token} cost in,"
            f" {self.num_output_tokens} out, {self.cost_per_output_token} cost out, {self.pipeline} pipeline"
        )

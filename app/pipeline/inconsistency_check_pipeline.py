import logging
from typing import Dict, List, Literal, Optional

from langchain_core.prompts import PromptTemplate
from langsmith import traceable
from pydantic import BaseModel, Field

from app.common.PipelineEnum import PipelineEnum
from app.domain import InconsistencyCheckPipelineExecutionDTO
from app.llm import CapabilityRequestHandler, RequirementList, CompletionArguments
from app.llm.langchain.iris_langchain_chat_model import IrisLangchainChatModel
from app.pipeline import Pipeline
from app.web.status.status_update import InconsistencyCheckCallback
from app.pipeline.prompts.inconsistency_check_prompts import solver_prompt, scorer_prompt

logger = logging.getLogger(__name__)


IssueLocation = Literal["problem_statement", "template_file", "solution_file", "uncertain"]


class ConsistencyIssue(BaseModel):
    """The consistency issue found in the programming exercise."""

    location: IssueLocation = Field(
        description="The location of the consistency issue in the programming exercise."
    )
    
    title: str = Field(
        description="The title of the consistency issue found in the programming exercise."
    )

    description: str = Field(
        description="The description of the consistency issue found in the programming exercise."
    )
    
    suggestion: str = Field(
        description="The suggestion to fix the consistency issue found in the programming exercise."
    )


class GuessConsistencyIssues(BaseModel):
    """Submit multiple consistency issues found in the programming exercise as guesses."""
    
    reasoning: str = Field(
        description="The reasoning behind the submitted guesses. Explain how you arrived at these consistency issues."
    )
    
    issues: List[ConsistencyIssue] = Field(
        description="The list of consistency issues found in the programming exercise."
    )    


class ScoredConsistencyIssue(BaseModel):
    """The scored consistency issue found in the programming exercise."""

    candidate: ConsistencyIssue = Field(
        description="The candidate consistency issue under review."
    )

    score_reasoning: str = Field(
        description="The reasoning behind the score given to the consistency issue. Weighting factors should be explained."
    )

    score: float = Field(
        description="The score given to the consistency issue. The score should be between 0.00 and 1.00. The higher the score, the more severe the issue, lower scores are nitpicks."
    )

class ScoredConsistencyIssues(BaseModel):
    """Submit multiple scored consistency issues found in the programming exercise."""
    
    issues: List[ScoredConsistencyIssue] = Field(
        description="The list of scored consistency issues found in the programming exercise."
    )


class InconsistencyCheckPipeline(Pipeline):
    solver_llm: IrisLangchainChatModel
    scorer_llm: IrisLangchainChatModel
    callback: InconsistencyCheckCallback

    def __init__(self, callback: Optional[InconsistencyCheckCallback] = None):
        super().__init__(implementation_id="inconsistency_check_pipeline")
        completion_args = CompletionArguments(temperature=0, max_tokens=2000)

        self.solver_prompt = PromptTemplate.from_template(solver_prompt)
        self.solver_llm = IrisLangchainChatModel(
            request_handler=CapabilityRequestHandler(
                requirements=RequirementList(
                    gpt_version_equivalent=4.5,
                    context_length=16385,
                )
            ),
            completion_args=completion_args,
        ).with_structured_output(GuessConsistencyIssues)
        self.solver = self.solver_prompt | self.solver_llm

        self.scorer_prompt = PromptTemplate.from_template(scorer_prompt)
        self.scorer_llm = IrisLangchainChatModel(
            request_handler=CapabilityRequestHandler(
                requirements=RequirementList(
                    gpt_version_equivalent=4.5,
                    context_length=16385,
                )
            ),
            completion_args=completion_args,
        ).with_structured_output(ScoredConsistencyIssues)
        self.scorer = self.scorer_prompt | self.scorer_llm

        self.callback = callback
        self.tokens = []


    @traceable(name="Inconsistency Check Pipeline")
    def __call__(self, dto: InconsistencyCheckPipelineExecutionDTO, **kwargs):
        """
        Runs the pipeline to check for inconsistencies in the exercise
        :param dto: execution data transfer object
        :param kwargs: The keyword arguments
        """

        if not dto.exercise:
            logger.error("Inconsistency check pipeline requires an exercise")
            raise ValueError("Exercise is required")

        logger.info("Running inconsistency check pipeline...")
        self.callback.in_progress()

        consistency_issues: Dict[str, List[ConsistencyIssue]] = {}

        file_paths = set(dto.exercise.template_repository.keys()) | set(dto.exercise.solution_repository.keys())
        for file_path in file_paths:
            template_file = dto.exercise.template_repository.get(file_path, "empty file")
            solution_file = dto.exercise.solution_repository.get(file_path, "empty file")

            response: GuessConsistencyIssues = self.solver.invoke(
                {
                    "problem_statement": dto.exercise.problem_statement,
                    "file_path": file_path,
                    "template_file": template_file,
                    "solution_file": solution_file,
                }
            )

            logger.info(f"Consistency issues found in {file_path}: {response}")
            # consistency_issues[file_path] = response.issues


        self._append_tokens(self.solver_llm.tokens, PipelineEnum.IRIS_INCONSISTENCY_CHECK)
        self._append_tokens(self.scorer_llm.tokens, PipelineEnum.IRIS_INCONSISTENCY_CHECK)

        #TODO
        self.callback.done(final_result="", tokens=self.tokens)

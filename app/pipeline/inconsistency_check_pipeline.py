import logging
from typing import Dict, Optional

from langchain_core.runnables import Runnable, RunnableParallel
from langchain_core.prompts import PromptTemplate
from langsmith import traceable

from app.common.PipelineEnum import PipelineEnum
from app.domain import InconsistencyCheckPipelineExecutionDTO
from app.llm import CapabilityRequestHandler, RequirementList, CompletionArguments
from app.llm.langchain.iris_langchain_chat_model import IrisLangchainChatModel
from app.pipeline import Pipeline
from app.web.status.status_update import InconsistencyCheckCallback
from app.pipeline.prompts.inconsistency_check_prompts import (
    solver_prompt,
    prettify_prompt,
)

logger = logging.getLogger(__name__)


class InconsistencyCheckPipeline(Pipeline):
    llm: IrisLangchainChatModel
    callback: InconsistencyCheckCallback

    solver: Runnable
    prettify: Runnable

    def __init__(self, callback: Optional[InconsistencyCheckCallback] = None):
        super().__init__(implementation_id="inconsistency_check_pipeline")
        completion_args = CompletionArguments(temperature=0, max_tokens=2000)

        self.llm = IrisLangchainChatModel(
            request_handler=CapabilityRequestHandler(
                requirements=RequirementList(
                    gpt_version_equivalent=4.5,
                    context_length=16385,
                )
            ),
            completion_args=completion_args,
        )
        self.solver_prompt = PromptTemplate.from_template(solver_prompt)
        self.solver = self.solver_prompt | self.llm

        self.prettify_prompt = PromptTemplate.from_template(prettify_prompt)
        self.prettify = self.prettify_prompt | self.llm

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

        # First, for each file in the exercise, we will check for consistency issues via the solver pipeline
        consistency_issues: Dict[str, str] = {}
        file_paths = set(dto.exercise.template_repository.keys()) | set(
            dto.exercise.solution_repository.keys()
        )
        solver_inputs = [
            {
                "file_path": file_path,
                "problem_statement": dto.exercise.problem_statement,
                "template_file": dto.exercise.template_repository.get(
                    file_path, "empty file"
                ),
                "solution_file": dto.exercise.solution_repository.get(
                    file_path, "empty file"
                ),
            }
            for file_path in file_paths
        ]
        file_responses = self.solver.map().invoke(solver_inputs)
        consistency_issues = {
            file_path: response.content
            for file_path, response in zip(file_paths, file_responses)
        }

        # Second, we will prettify the consistency issues and provide a summary using the prettify pipeline
        formatted_consistency_issues = "\n".join(
            [
                f"<PotentialFileIssues filePath=`{file_path}`>\n{issues}\n</PotentialFileIssues>"
                for file_path, issues in consistency_issues.items()
            ]
        )
        summary_response = self.prettify.invoke(
            {
                "problem_statement": dto.exercise.problem_statement,
                "consistency_issues": formatted_consistency_issues,
            }
        )

        result = summary_response.content.strip()

        # remove ``` from start and end if exists
        if result.startswith("```") and result.endswith("```"):
            result = result[3:-3]
            if result.startswith("markdown"):
                result = result[8:]
            result = result.strip()

        logger.info(result)

        self._append_tokens(self.llm.tokens, PipelineEnum.IRIS_INCONSISTENCY_CHECK)
        self.callback.done(final_result=result, tokens=self.tokens)

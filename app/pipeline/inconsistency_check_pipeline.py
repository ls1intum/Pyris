import logging
from typing import Dict, Optional

from langchain_core.runnables import Runnable
from langchain_core.prompts import PromptTemplate
from langsmith import traceable

from app.common.PipelineEnum import PipelineEnum
from app.domain import InconsistencyCheckPipelineExecutionDTO
from app.llm import CapabilityRequestHandler, RequirementList, CompletionArguments
from app.llm.langchain.iris_langchain_chat_model import IrisLangchainChatModel
from app.pipeline import Pipeline
from app.web.status.status_update import InconsistencyCheckCallback
from app.pipeline.prompts.inconsistency_check_prompts import solver_prompt, prettify_prompt

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

        consistency_issues: Dict[str, str] = {}

        file_paths = set(dto.exercise.template_repository.keys()) | set(dto.exercise.solution_repository.keys())
        
        for file_path in file_paths:
            template_file = dto.exercise.template_repository.get(file_path, "empty file")
            solution_file = dto.exercise.solution_repository.get(file_path, "empty file")

            response = self.solver.invoke(
                {
                    "problem_statement": dto.exercise.problem_statement,
                    "file_path": file_path,
                    "template_file": template_file,
                    "solution_file": solution_file,
                }
            )

            consistency_issues[file_path] = response.content

        formatted_consistency_issues = '\n'.join([
            f"<PotentialFileIssues filePath=`{file_path}`>\n{issues}\n</PotentialFileIssues>"
            for file_path, issues 
            in consistency_issues.items()
        ])
        
        final_response = self.prettify.invoke(
            {
                "problem_statement": dto.exercise.problem_statement,
                "consistency_issues": formatted_consistency_issues,
            }
        )
        
        logger.info(final_response.content)

        self._append_tokens(self.llm.tokens, PipelineEnum.IRIS_INCONSISTENCY_CHECK)
        self.callback.done(final_result=final_response.content, tokens=self.tokens)

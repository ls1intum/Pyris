import string
from asyncio.log import logger
from typing import List, Tuple

from dotenv import load_dotenv
from langsmith import traceable
from weaviate import WeaviateClient
from weaviate.classes.query import Filter

from app.common.token_usage_dto import TokenUsageDTO
from app.common.PipelineEnum import PipelineEnum
from ..common.message_converters import convert_iris_message_to_langchain_message
from ..common.pyris_message import PyrisMessage
from ..llm.langchain import IrisLangchainChatModel
from ..pipeline import Pipeline

from app.llm import (
    BasicRequestHandler,
    CompletionArguments,
    CapabilityRequestHandler,
    RequirementList,
)
from app.pipeline.shared.reranker_pipeline import RerankerPipeline
from app.vector_database.lecture_schema import init_lecture_schema, LectureSchema
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import (
    ChatPromptTemplate,
    SystemMessagePromptTemplate,
)

from ..pipeline.prompts.lecture_retrieval_prompts import (
    assessment_prompt,
    assessment_prompt_final,
    rewrite_student_query_prompt,
    lecture_retriever_initial_prompt,
    write_hypothetical_answer_prompt,
    lecture_retrieval_initial_prompt_with_exercise_context,
    rewrite_student_query_prompt_with_exercise_context,
    write_hypothetical_answer_with_exercise_context_prompt, lecture_retrieval_rewrite_student_query,
)
import concurrent.futures
import cohere
import os

from ..vector_database.lecture_transcription_schema import LectureTranscriptionSchema


def merge_retrieved_chunks(
    basic_retrieved_chunks, hyde_retrieved_chunks
) -> List[dict]:
    """
    Merge the retrieved chunks from the basic and hyde retrieval methods. This function ensures that for any
    duplicate IDs, the properties from hyde_retrieved_lecture_chunks will overwrite those from
    basic_retrieved_lecture_chunks.
    """
    merged_chunks = {}
    for chunk in basic_retrieved_chunks:
        merged_chunks[chunk["id"]] = chunk["properties"]

    for chunk in hyde_retrieved_chunks:
        merged_chunks[chunk["id"]] = chunk["properties"]

    return [properties for uuid, properties in merged_chunks.items()]


def _add_last_four_messages_to_prompt(
    prompt,
    chat_history: List[PyrisMessage],
):
    """
    Adds the chat history and user question to the prompt
        :param chat_history: The chat history
        :param user_question: The user question
        :return: The prompt with the chat history
    """
    if chat_history is not None and len(chat_history) > 0:
        num_messages_to_take = min(len(chat_history), 4)
        last_messages = chat_history[-num_messages_to_take:]
        chat_history_messages = [
            convert_iris_message_to_langchain_message(message)
            for message in last_messages
        ]
        prompt += chat_history_messages
    return prompt


def map_weaviate_results_to_dict(results) -> list[dict[str, dict]]:
    return [
        {"id": obj.uuid.int, "properties": obj.properties}
        for obj in results
    ]



class LectureRetrieval(Pipeline):
    """
    Class for retrieving lecture data from the database.
    """

    tokens: List[TokenUsageDTO]

    def __init__(self, client: WeaviateClient, **kwargs):
        super().__init__(implementation_id="lecture_retrieval_pipeline")
        load_dotenv()
        request_handler = CapabilityRequestHandler(
            requirements=RequirementList(
                gpt_version_equivalent=4.25,
                context_length=16385,
                privacy_compliance=True,
            )
        )
        completion_args = CompletionArguments(temperature=0, max_tokens=2000)
        self.llm = IrisLangchainChatModel(
            request_handler=request_handler, completion_args=completion_args
        )
        self.llm_embedding = BasicRequestHandler("embedding-small")
        self.pipeline = self.llm | StrOutputParser()
        self.collection = init_lecture_schema(client)
        self.reranker_pipeline = RerankerPipeline()
        self.tokens = []
        self.cohere = cohere.ClientV2(base_url="https://rerankv3-multi.swedencentral.models.ai.azure.com",
                                      api_key=os.getenv("COHERE_API_KEY"))

    @traceable(name="Full Lecture Retrieval")
    def __call__(
        self,
        chat_history: list[PyrisMessage],
        student_query: str,
        result_limit: int,
        course_name: str = None,
        course_id: int = None,
        base_url: str = None,
        problem_statement: str = None,
        exercise_title: str = None,
    ) -> Tuple[List[dict], List[dict]]:
        """
        Retrieve lecture data from the database.
        """
        course_language = self.fetch_course_language(course_id)

        response_slides, response_transcriptions, response_hyde_slides, response_hyde_transcriptions = self.run_parallel_rewrite_tasks(
            chat_history=chat_history,
            student_query=student_query,
            result_limit=result_limit,
            course_language=course_language,
            course_name=course_name,
            course_id=course_id,
            base_url=base_url,
            problem_statement=problem_statement,
            exercise_title=exercise_title,
        )

        basic_retrieved_lecture_chunks = map_weaviate_results_to_dict(response_slides.objects)
        hyde_retrieved_lecture_chunks = map_weaviate_results_to_dict(response_hyde_slides.objects)
        basic_retrieved_lecture_transcriptions = map_weaviate_results_to_dict(response_transcriptions.objects)
        hyde_retrieved_lecture_transcriptions = map_weaviate_results_to_dict(response_hyde_transcriptions.objects)

        merged_chunks_slides = merge_retrieved_chunks(
            basic_retrieved_lecture_chunks, hyde_retrieved_lecture_chunks
        )

        merged_chunks_transcriptions = merge_retrieved_chunks(
            basic_retrieved_lecture_transcriptions, hyde_retrieved_lecture_transcriptions
        )

        rerank_lecture_slides = self.rerank_results(student_query, [x["properties"][LectureSchema.PAGE_TEXT_CONTENT.value] for x in merged_chunks_slides], 5)
        rerank_lecture_transcriptions = self.rerank_results(student_query, [x["properties"][LectureTranscriptionSchema.SEGMENT_TEXT.value] for x in merged_chunks_transcriptions], 5)

        return rerank_lecture_slides, rerank_lecture_transcriptions

    @traceable(name="Basic Lecture Retrieval")
    def basic_lecture_retrieval(
        self,
        chat_history: list[PyrisMessage],
        student_query: str,
        result_limit: int,
        course_name: str = None,
        course_id: int = None,
        base_url: str = None,
    ) -> list[dict[str, dict]]:
        """
        Basic retrieval for pipelines that need performance and fast answers.
        """
        if not self.assess_question(chat_history, student_query):
            return []

        rewritten_query = self.rewrite_student_query(
            chat_history, student_query, "course_language", course_name
        )
        response = self.search_in_db(
            query=rewritten_query,
            hybrid_factor=0.9,
            result_limit=result_limit,
            course_id=course_id,
            base_url=base_url,
        )

        basic_retrieved_lecture_chunks: list[dict[str, dict]] = [
            {"id": obj.uuid.int, "properties": obj.properties}
            for obj in response.objects
        ]
        return basic_retrieved_lecture_chunks

    @traceable(name="Retrieval: Question Assessment")
    def assess_question(
        self, chat_history: list[PyrisMessage], student_query: str
    ) -> bool:
        prompt = ChatPromptTemplate.from_messages(
            [
                ("system", assessment_prompt),
            ]
        )
        prompt = _add_last_four_messages_to_prompt(prompt, chat_history)
        prompt += ChatPromptTemplate.from_messages(
            [
                ("user", student_query),
            ]
        )
        prompt += ChatPromptTemplate.from_messages(
            [
                ("system", assessment_prompt_final),
            ]
        )

        try:
            response = (prompt | self.pipeline).invoke({})
            logger.info(f"Response from assessment pipeline: {response}")
            return response == "YES"
        except Exception as e:
            raise e

    @traceable(name="Retrieval: Rewrite Student Query")
    def rewrite_student_query(
        self,
        chat_history: list[PyrisMessage],
        student_query: str,
        course_language: str,
        course_name: str,
    ) -> str:
        """
        Rewrite the student query.
        """
        prompt = ChatPromptTemplate.from_messages(
            [
                ("system", lecture_retrieval_rewrite_student_query),
            ]
        )
        prompt = _add_last_four_messages_to_prompt(prompt, chat_history)
        prompt += SystemMessagePromptTemplate.from_template(
            rewrite_student_query_prompt
        )
        prompt_val = prompt.format_messages(
            course_language=course_language,
            # course_name=course_name,
            student_query=student_query,
        )
        prompt = ChatPromptTemplate.from_messages(prompt_val)
        try:
            response = (prompt | self.pipeline).invoke({})
            token_usage = self.llm.tokens
            token_usage.pipeline = PipelineEnum.IRIS_LECTURE_RETRIEVAL_PIPELINE
            self.tokens.append(self.llm.tokens)
            logger.info(f"Response from exercise chat pipeline: {response}")
            return response
        except Exception as e:
            raise e

    @traceable(name="Retrieval: Rewrite Student Query with Exercise Context")
    def rewrite_student_query_with_exercise_context(
        self,
        chat_history: list[PyrisMessage],
        student_query: str,
        course_language: str,
        course_name: str,
        exercise_name: str,
        problem_statement: str,
    ) -> str:
        """
        Rewrite the student query to generate fitting lecture content and embed it.
        """
        prompt = ChatPromptTemplate.from_messages(
            [
                ("system", lecture_retrieval_initial_prompt_with_exercise_context),
            ]
        )
        prompt = _add_last_four_messages_to_prompt(prompt, chat_history)
        prompt += SystemMessagePromptTemplate.from_template(
            rewrite_student_query_prompt_with_exercise_context
        )
        prompt_val = prompt.format_messages(
            course_language=course_language,
            course_name=course_name,
            exercise_name=exercise_name,
            problem_statement=problem_statement,
            student_query=student_query,
        )
        prompt = ChatPromptTemplate.from_messages(prompt_val)
        try:
            response = (prompt | self.pipeline).invoke({})
            token_usage = self.llm.tokens
            token_usage.pipeline = PipelineEnum.IRIS_LECTURE_RETRIEVAL_PIPELINE
            self.tokens.append(self.llm.tokens)
            logger.info(f"Response from exercise chat pipeline: {response}")
            return response
        except Exception as e:
            raise e

    @traceable(name="Retrieval: Rewrite Elaborated Query")
    def rewrite_elaborated_query(
        self,
        chat_history: list[PyrisMessage],
        student_query: str,
        course_language: str,
        course_name: str,
    ) -> str:
        """
        Rewrite the student query to generate fitting lecture content and embed it.
        To extract more relevant content from the vector database.
        """
        prompt = ChatPromptTemplate.from_messages(
            [
                ("system", write_hypothetical_answer_prompt),
            ]
        )
        prompt = _add_last_four_messages_to_prompt(prompt, chat_history)
        prompt += ChatPromptTemplate.from_messages(
            [
                ("user", student_query),
            ]
        )
        prompt_val = prompt.format_messages(
            course_language=course_language,
            course_name=course_name,
        )
        prompt = ChatPromptTemplate.from_messages(prompt_val)
        try:
            response = (prompt | self.pipeline).invoke({})
            token_usage = self.llm.tokens
            token_usage.pipeline = PipelineEnum.IRIS_LECTURE_RETRIEVAL_PIPELINE
            self.tokens.append(self.llm.tokens)
            logger.info(f"Response from retirval pipeline: {response}")
            return response
        except Exception as e:
            raise e

    @traceable(name="Retrieval: Rewrite Elaborated Query with Exercise Context")
    def rewrite_elaborated_query_with_exercise_context(
        self,
        chat_history: list[PyrisMessage],
        student_query: str,
        course_language: str,
        course_name: str,
        exercise_name: str,
        problem_statement: str,
    ) -> str:
        """
        Rewrite the student query to generate fitting lecture content and embed it.
        To extract more relevant content from the vector database.
        """
        prompt = ChatPromptTemplate.from_messages(
            [
                ("system", write_hypothetical_answer_with_exercise_context_prompt),
            ]
        )
        prompt = _add_last_four_messages_to_prompt(prompt, chat_history)
        prompt_val = prompt.format_messages(
            course_language=course_language,
            course_name=course_name,
            exercise_name=exercise_name,
            problem_statement=problem_statement,
        )
        prompt = ChatPromptTemplate.from_messages(prompt_val)
        prompt += ChatPromptTemplate.from_messages(
            [
                ("user", student_query),
            ]
        )
        try:
            response = (prompt | self.pipeline).invoke({})
            token_usage = self.llm.tokens
            token_usage.pipeline = PipelineEnum.IRIS_LECTURE_RETRIEVAL_PIPELINE
            self.tokens.append(self.llm.tokens)
            logger.info(f"Response from exercise chat pipeline: {response}")
            return response
        except Exception as e:
            raise e

    @traceable(name="Retrieval: Search in DB")
    def search_in_db(
        self,
        query: str,
        hybrid_factor: float,
        result_limit: int,
        course_id: int = None,
        lecture_id: int = None,
        base_url: str = None,
    ):
        """
        Search the database for the given query.
        """
        logger.info(f"Searching in the database for query: {query}")


        slide_results = self.search_in_db_for_lecture_slides(
            query=query,
            hybrid_factor=hybrid_factor,
            result_limit=result_limit,
            course_id=course_id,
            lecture_id=lecture_id,
            base_url=base_url,
        )

        transcription_results = self.search_in_db_for_lecture_transcriptions(
            query=query,
            hybrid_factor=hybrid_factor,
            result_limit=result_limit,
            course_id=course_id,
            lecture_id=lecture_id,
        )

        return slide_results, transcription_results


    @traceable(name="Retrieval: Search in DB for Lecture Slides")
    def search_in_db_for_lecture_slides(
        self,
        query: str,
        hybrid_factor: float,
        result_limit: int,
        course_id: int = None,
        lecture_id: int = None,
        base_url: str = None,
    ):
        # Initialize filter to None by default
        filter_weaviate = Filter()
        # Check if lecture_id is provided
        if lecture_id:
            filter_weaviate &= Filter.by_property(LectureSchema.LECTURE_ID.value).equal(
                lecture_id
            )


        # Check if course_id is provided
        if course_id:
            # Create a filter for course_id
            filter_weaviate &= Filter.by_property(LectureSchema.COURSE_ID.value).equal(
                course_id
            )

        # Extend the filter based on the presence of base_url
        if base_url:
            filter_weaviate &= Filter.by_property(
                LectureSchema.BASE_URL.value
            ).equal(base_url)

        vec = self.llm_embedding.embed(query)
        return_value = self.collection.query.hybrid(
            query=query,
            alpha=hybrid_factor,
            vector=vec,
            return_properties=[
                LectureSchema.COURSE_ID.value,
                LectureSchema.LECTURE_UNIT_NAME.value,
                LectureSchema.LECTURE_UNIT_LINK.value,
                LectureSchema.PAGE_NUMBER.value,
                LectureSchema.PAGE_TEXT_CONTENT.value,
            ],
            limit=result_limit,
            filters=filter_weaviate,
        )
        return return_value

    @traceable(name="Retrieval: Search in DB for Lecture Transcriptions")
    def search_in_db_for_lecture_transcriptions(
        self,
        query: str,
        hybrid_factor: float,
        result_limit: int,
        course_id: int = None,
        lecture_id: int = None,
    ):
        # Initialize filter to None by default
        filter_weaviate = Filter()
        # Check if lecture_id is provided
        if lecture_id:
            filter_weaviate &= Filter.by_property(LectureTranscriptionSchema.LECTURE_ID.value).equal(
                lecture_id
            )


        # Check if course_id is provided
        if course_id:
            # Create a filter for course_id
            filter_weaviate &= Filter.by_property(LectureTranscriptionSchema.COURSE_ID.value).equal(
                course_id
            )

        vec = self.llm_embedding.embed(query)
        weaviate_results = self.collection.query.hybrid(
            query=query,
            alpha=hybrid_factor,
            vector=vec,
            return_properties=[
                LectureTranscriptionSchema.LECTURE_UNIT_ID.value,
                LectureTranscriptionSchema.SEGMENT_TEXT.value,
                LectureTranscriptionSchema.SEGMENT_START.value,
                LectureTranscriptionSchema.SEGMENT_END.value,
                LectureTranscriptionSchema.SEGMENT_SUMMARY.value,
            ],
            limit=result_limit,
            filters=filter_weaviate,
        )
        return weaviate_results


    @traceable(name="Retrieval: Run Parallel Rewrite Tasks")
    def run_parallel_rewrite_tasks(
        self,
        chat_history: list[PyrisMessage],
        student_query: str,
        result_limit: int,
        course_language: str,
        course_name: str = None,
        course_id: int = None,
        base_url: str = None,
        problem_statement: str = None,
        exercise_title: str = None,
    ):
        """
        Run the rewrite tasks in parallel.
        """

        # TODO: Move lecture transcription rewrite to same thread as lecture slides rewrite
        if problem_statement:
            with concurrent.futures.ThreadPoolExecutor() as executor:
                # Schedule the rewrite tasks to run in parallel
                rewritten_query_future = executor.submit(
                    self.rewrite_student_query_with_exercise_context,
                    chat_history,
                    student_query,
                    course_language,
                    course_name,
                    exercise_title,
                    problem_statement,
                )
                hypothetical_answer_query_future = executor.submit(
                    self.rewrite_elaborated_query_with_exercise_context,
                    chat_history,
                    student_query,
                    course_language,
                    course_name,
                    exercise_title,
                    problem_statement,
                )

                # Get the results once both tasks are complete
                rewritten_query: str = rewritten_query_future.result()
                hypothetical_answer_query: str = (
                    hypothetical_answer_query_future.result()
                )
        else:
            with concurrent.futures.ThreadPoolExecutor() as executor:
                # Schedule the rewrite tasks to run in parallel
                rewritten_query_future = executor.submit(
                    self.rewrite_student_query,
                    chat_history,
                    student_query,
                    course_language,
                    course_name,
                )
                hypothetical_answer_query_future = executor.submit(
                    self.rewrite_elaborated_query,
                    chat_history,
                    student_query,
                    course_language,
                    course_name,
                )

                # Get the results once both tasks are complete
                rewritten_query = rewritten_query_future.result()
                hypothetical_answer_query = hypothetical_answer_query_future.result()

            # Execute the database search tasks
        with concurrent.futures.ThreadPoolExecutor() as executor:
            response_future_slides, response_future_transcriptions = executor.submit(
                self.search_in_db,
                query=rewritten_query,
                hybrid_factor=0.9,
                result_limit=result_limit,
                course_id=course_id,
                base_url=base_url,
            )
            response_hyde_future_slides, response_hyde_future_transcriptions = executor.submit(
                self.search_in_db,
                query=hypothetical_answer_query,
                hybrid_factor=0.9,
                result_limit=result_limit,
                course_id=course_id,
                base_url=base_url,
            )

            # Get the results once both tasks are complete
            response_slides = response_future_slides.result()
            response_transcriptions = response_future_transcriptions.result()
            response_hyde_slides = response_hyde_future_slides.result()
            response_hyde_transcriptions = response_hyde_future_transcriptions.results()

        return response_slides, response_transcriptions, response_hyde_slides, response_hyde_transcriptions

    def fetch_course_language(self, course_id):
        """
        Fetch the language of the course based on the course ID.
        If no specific language is set, it defaults to English.
        """
        course_language = "english"

        if course_id:
            # Fetch the first object that matches the course ID with the language property
            result = self.collection.query.fetch_objects(
                filters=Filter.by_property(LectureSchema.COURSE_ID.value).equal(
                    course_id
                ),
                limit=1,  # We only need one object to check and retrieve the language
                return_properties=[LectureSchema.COURSE_LANGUAGE.value],
            )

            # Check if the result has objects and retrieve the language
            if result.objects:
                fetched_language = result.objects[0].properties.get(
                    LectureSchema.COURSE_LANGUAGE.value
                )
                if fetched_language:
                    course_language = fetched_language

        return course_language

    def rerank_results(self, student_query: string, results: List[string], top_n_results: int):
        _, reranked_results, _ = self.cohere.rerank(query=student_query,
                                                    documents=results,
                                                    top_n=top_n_results,
                                                    model='rerank-multilingual-v3.5')
        if reranked_results:
            return [results[int(i)] for i in reranked_results]

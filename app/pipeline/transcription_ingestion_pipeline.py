from functools import reduce
from typing import Optional, List, Dict, Any

from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import Runnable
from weaviate import WeaviateClient

from asyncio.log import logger

from app.common.PipelineEnum import PipelineEnum
from app.domain.data.metrics.transcription_dto import (
    TranscriptionWebhookDTO,
    TranscriptionSegmentDTO,
)
from app.domain.ingestion.transcription_ingestion.transcription_ingestion_pipeline_execution_dto import (
    TranscriptionIngestionPipelineExecutionDto,
)
from app.domain.lecture.lecture_unit_dto import LectureUnitDTO
from app.llm import (
    BasicRequestHandler,
    CapabilityRequestHandler,
    RequirementList,
    CompletionArguments,
)
from weaviate.classes.query import Filter
from app.llm.langchain import IrisLangchainChatModel
from app.pipeline import Pipeline
from app.pipeline.lecture_unit_pipeline import LectureUnitPipeline
from app.vector_database.database import batch_update_lock
from app.pipeline.prompts.transcription_ingestion_prompts import (
    transcription_summary_prompt,
)
from app.vector_database.lecture_transcription_schema import (
    init_lecture_transcription_schema,
    LectureTranscriptionSchema,
)
from app.web.status.transcription_ingestion_callback import TranscriptionIngestionStatus

CHUNK_SEPARATOR_CHAR = "\31"


class TranscriptionIngestionPipeline(Pipeline):
    llm: IrisLangchainChatModel
    pipeline: Runnable
    prompt: ChatPromptTemplate

    def __init__(
            self,
            client: WeaviateClient,
            dto: Optional[TranscriptionIngestionPipelineExecutionDto],
            callback: TranscriptionIngestionStatus,
    ) -> None:
        super().__init__()
        self.client = client
        self.dto = dto
        self.callback = callback
        self.collection = init_lecture_transcription_schema(client)
        self.llm_embedding = BasicRequestHandler("embedding-small")

        request_handler = CapabilityRequestHandler(
            requirements=RequirementList(
                gpt_version_equivalent=4.5,
                context_length=16385,
                privacy_compliance=True,
            )
        )
        completion_args = CompletionArguments(temperature=0, max_tokens=2000)
        self.llm = IrisLangchainChatModel(
            request_handler=request_handler, completion_args=completion_args
        )
        self.pipeline = self.llm | StrOutputParser()
        self.tokens = []

    def __call__(self) -> None:
        try:
            self.callback.in_progress("Deleting existing transcription data")
            self.delete_existing_transcription_data(self.dto.transcription)
            self.callback.in_progress("Chunking transcription")
            chunks = self.chunk_transcription(self.dto.transcription)
            self.callback.done("Chunked transcription")
            logger.info("chunked data")
            self.callback.in_progress("Summarizing transcription")
            chunks = self.summarize_chunks(chunks)
            self.callback.done("Summarized transcription")

            self.callback.in_progress("Ingesting transcription into vector database")
            self.batch_insert(chunks)
            self.callback.done("Transcriptions ingested successfully")

            self.callback.in_progress("Ingesting lecture unit summary into vector database")
            lecture_unit_dto = LectureUnitDTO(
                course_id=self.dto.transcription.course_id,
                course_name=self.dto.transcription.course_name,
                course_description=self.dto.transcription.course_description,
                lecture_id=self.dto.transcription.lecture_id,
                lecture_name=self.dto.transcription.lecture_name,
                lecture_unit_id=self.dto.lectureUnitId,
                lecture_unit_name="",
                lecture_unit_link="",
                base_url="", #TODO: send missing data from Artemis
            )

            LectureUnitPipeline()(lecture_unit_dto)

            self.callback.done("Ingested lecture unit summary into vector database", tokens=self.tokens)

        except Exception as e:
            logger.error(f"Error processing transcription ingestion pipeline: {e}")
            self.callback.error(
                f"Error processing transcription ingestion pipeline: {e}",
                exception=e,
                tokens=self.tokens,
            )

    def delete_existing_transcription_data(self, transcription: TranscriptionWebhookDTO):
        self.collection.data.delete_many(
            where = Filter.by_property(LectureTranscriptionSchema.COURSE_ID.value).equal(transcription.course_id)
                  & Filter.by_property(LectureTranscriptionSchema.LECTURE_ID.value).equal(transcription.lecture_id)
                  & Filter.by_property(LectureTranscriptionSchema.LECTURE_UNIT_ID.value).equal(transcription.lecture_unit_id)
        )
        # TODO: Add Base Url


    def batch_insert(self, chunks):
        with batch_update_lock:
            with self.collection.batch.dynamic() as batch:
                try:
                    for chunk in chunks:
                        embed_chunk = self.llm_embedding.embed(
                            chunk[LectureTranscriptionSchema.SEGMENT_TEXT.value]
                        )
                        batch.add_object(properties=chunk, vector=embed_chunk)
                except Exception as e:
                    logger.error(f"Error embedding lecture transcription chunk: {e}")
                    self.callback.error(
                        f"Failed to ingest lecture transcriptions into the database: {e}",
                        exception=e,
                        tokens=self.tokens,
                    )

    def chunk_transcription(
            self, transcription: TranscriptionWebhookDTO
    ) -> List[Dict[str, Any]]:
        chunks = []

        slide_chunks = {}
        for segment in transcription.transcription.segments:
            slide_key = f"{transcription.lecture_id}_{transcription.lecture_unit_id}_{segment.slide_number}"

            if slide_key not in slide_chunks:
                chunk = {
                    LectureTranscriptionSchema.COURSE_ID.value: transcription.course_id,
                    LectureTranscriptionSchema.LECTURE_ID.value: transcription.lecture_id,
                    LectureTranscriptionSchema.LECTURE_UNIT_ID.value: transcription.lecture_unit_id,
                    LectureTranscriptionSchema.LANGUAGE.value: transcription.transcription.language,
                    LectureTranscriptionSchema.SEGMENT_START_TIME.value: segment.start_time,
                    LectureTranscriptionSchema.SEGMENT_END_TIME.value: segment.end_time,
                    LectureTranscriptionSchema.SEGMENT_TEXT.value: segment.text,
                    LectureTranscriptionSchema.PAGE_NUMBER.value: segment.slide_number,
                }

                slide_chunks[slide_key] = chunk
            else:
                slide_chunks[slide_key][
                    LectureTranscriptionSchema.SEGMENT_TEXT.value
                ] += (CHUNK_SEPARATOR_CHAR + segment.text)
                slide_chunks[slide_key][
                    LectureTranscriptionSchema.SEGMENT_END_TIME.value
                ] = segment.end_time

        for i, segment in enumerate(slide_chunks.values()):
            # If the segment is shorter than 1200 characters, we can just add it as is
            if len(segment[LectureTranscriptionSchema.SEGMENT_TEXT.value]) < 1200:
                # Add the segment to the chunks list and replace the chunk separator character with a space
                segment[LectureTranscriptionSchema.SEGMENT_TEXT.value] = (
                    self.replace_separator_char(
                        segment[LectureTranscriptionSchema.SEGMENT_TEXT.value]
                    )
                )
                chunks.append(segment)
                continue

            semantic_chunks = self.llm_embedding.split_text_semantically(
                segment[LectureTranscriptionSchema.SEGMENT_TEXT.value],
                breakpoint_threshold_type="gradient",
                breakpoint_threshold_amount=60.0,
                min_chunk_size=512,
            )

            # Calculate the offset of the current slide chunk to the start of the transcript
            offset_slide_chunk = reduce(
                lambda acc, txt: acc + len(self.remove_separator_char(txt)),
                map(
                    lambda seg: seg[LectureTranscriptionSchema.SEGMENT_TEXT.value],
                    list(slide_chunks.values())[:i],
                ),
                0,
            )
            offset_start = offset_slide_chunk
            for j, chunk in enumerate(semantic_chunks):
                offset_end = offset_start + len(self.remove_separator_char(chunk))

                start_time = self.get_transcription_segment_of_char_position(
                    offset_start, transcription.transcription.segments
                ).start_time
                end_time = self.get_transcription_segment_of_char_position(
                    offset_end, transcription.transcription.segments
                ).end_time

                chunks.append(
                    {
                        **segment,
                        LectureTranscriptionSchema.SEGMENT_START_TIME.value: start_time,
                        LectureTranscriptionSchema.SEGMENT_END_TIME.value: end_time,
                        LectureTranscriptionSchema.SEGMENT_TEXT.value: self.cleanup_chunk(
                            self.replace_separator_char(chunk)
                        ),
                    }
                )
                offset_start = offset_end + 1

        return chunks

    @staticmethod
    def get_transcription_segment_of_char_position(
            char_position: int, segments: List[TranscriptionSegmentDTO]
    ):
        offset_lookup_counter = 0
        segment_index = 0
        while (
                segment_index < len(segments)
                and offset_lookup_counter + len(segments[segment_index].text)
                < char_position
        ):
            offset_lookup_counter += len(segments[segment_index].text)
            segment_index += 1

        if segment_index >= len(segments):
            return segments[-1]
        return segments[segment_index]

    @staticmethod
    def cleanup_chunk(text: str):
        return text.replace("  ", " ").strip()

    @staticmethod
    def replace_separator_char(text: str, replace_with: str = " ") -> str:
        return text.replace(CHUNK_SEPARATOR_CHAR, replace_with)

    def remove_separator_char(self, text: str) -> str:
        return self.replace_separator_char(text, "")

    def summarize_chunks(self, chunks: List[Dict[str, Any]]):
        chunks_with_summaries = []
        for chunk in chunks:
            self.prompt = ChatPromptTemplate.from_messages(
                [
                    (
                        "system",
                        transcription_summary_prompt(
                            self.dto.transcription.lecture_name,
                            chunk[LectureTranscriptionSchema.SEGMENT_TEXT.value],
                        ),
                    ),
                ]
            )
            prompt_val = self.prompt.format_messages()
            self.prompt = ChatPromptTemplate.from_messages(prompt_val)
            try:
                response = (self.prompt | self.pipeline).invoke({})
                self._append_tokens(
                    self.llm.tokens, PipelineEnum.IRIS_VIDEO_TRANSCRIPTION_INGESTION
                )
                chunks_with_summaries.append(
                    {
                        **chunk,
                        LectureTranscriptionSchema.SEGMENT_SUMMARY.value: response,
                    }
                )
            except Exception as e:
                raise e
        return chunks_with_summaries

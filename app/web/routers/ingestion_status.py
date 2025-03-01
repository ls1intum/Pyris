import json
from urllib.parse import unquote

from fastapi import APIRouter, status, Response, Depends
from fastapi.params import Query
from weaviate.collections.classes.filters import Filter

from app.dependencies import TokenValidator
from ...vector_database.database import VectorDatabase
from ...vector_database.lecture_unit_page_chunk_schema import LectureUnitPageChunkSchema
from enum import Enum

router = APIRouter(prefix="/api/v1", tags=["ingestion_status"])


class IngestionState(str, Enum):
    DONE = "DONE"
    NOT_STARTED = "NOT_STARTED"


@router.get(
    "/courses/{course_id}/lectures/{lecture_id}/lectureUnits/{lecture_unit_id}/ingestion-state",
    dependencies=[Depends(TokenValidator())],
)
def get_lecture_unit_ingestion_state(
    course_id: int, lecture_id: int, lecture_unit_id: int, base_url: str = Query(...)
):
    """

    :param course_id:
    :param lecture_id:
    :param lecture_unit_id:
    :param base_url:
    :return:
    """
    db = VectorDatabase()
    decoded_base_url = unquote(base_url)
    result = db.lectures.query.fetch_objects(
        filters=(
            Filter.by_property(LectureUnitPageChunkSchema.BASE_URL.value).equal(decoded_base_url)
            & Filter.by_property(LectureUnitPageChunkSchema.COURSE_ID.value).equal(course_id)
            & Filter.by_property(LectureUnitPageChunkSchema.LECTURE_ID.value).equal(lecture_id)
            & Filter.by_property(LectureUnitPageChunkSchema.LECTURE_UNIT_ID.value).equal(
                lecture_unit_id
            )
        ),
        limit=1,
        return_properties=[LectureUnitPageChunkSchema.LECTURE_UNIT_NAME.value],
    )

    if len(result.objects) > 0:
        return Response(
            status_code=status.HTTP_200_OK,
            content=json.dumps({"state": IngestionState.DONE.value}),
            media_type="application/json",
        )
    else:
        return Response(
            status_code=status.HTTP_200_OK,
            content=json.dumps({"state": IngestionState.NOT_STARTED.value}),
            media_type="application/json",
        )

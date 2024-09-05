from urllib.parse import unquote

from fastapi import APIRouter, status, Response, Depends
from weaviate.collections.classes.filters import Filter

from app.dependencies import TokenValidator
from ...vector_database.database import VectorDatabase
from ...vector_database.lecture_schema import LectureSchema

router = APIRouter(prefix="/api/v1", tags=["ingestion_status"])


@router.get(
    "/courses/{course_id}/lectures/{lecture_id}/lectureUnits/{lecture_unit_id}/ingestion-state",
    dependencies=[Depends(TokenValidator())],
)
def get_lecture_unit_ingestion_state(
    course_id: int, lecture_id: int, lecture_unit_id: int, baseUrl: str
):
    db = VectorDatabase()
    decoded_base_url = unquote(baseUrl)
    result = db.lectures.query.fetch_objects(
        filters=(
            Filter.by_property(LectureSchema.BASE_URL.value).equal(decoded_base_url)
            & Filter.by_property(LectureSchema.COURSE_ID.value).equal(course_id)
            & Filter.by_property(LectureSchema.LECTURE_ID.value).equal(lecture_id)
            & Filter.by_property(LectureSchema.LECTURE_UNIT_ID.value).equal(
                lecture_unit_id
            )
        ),
        limit=1,
        return_properties=[LectureSchema.LECTURE_UNIT_NAME.value],
    )

    if len(result.objects) > 0:
        return Response(
            status_code=status.HTTP_200_OK,
            content='"DONE"',
            media_type="application/json",
        )
    else:
        return Response(
            status_code=status.HTTP_200_OK,
            content='"NOT_STARTED"',
            media_type="application/json",
        )

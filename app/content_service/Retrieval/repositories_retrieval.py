import json
from typing import List

import weaviate
import weaviate.classes as wvc

from app.content_service.Retrieval.abstract_retrieval import AbstractRetrieval
from app.vector_database.repository_schema import init_repository_schema, RepositorySchema


class RepositoryRetrieval(AbstractRetrieval):
    """
    Class for Retrieving repository code for from the vector database.
    """

    def __init__(self, client: weaviate.WeaviateClient):
        self.collection = init_repository_schema(client)

    def retrieve(self, user_message: str, repository_id: int = None) -> List[str]:
        response = self.collection.query.near_text(
            near_text=user_message,
            filters=(
                wvc.query.Filter.by_property(RepositorySchema.REPOSITORY_ID).equal(
                    repository_id
                )
                if repository_id
                else None
            ),
            return_properties=[
                RepositorySchema.REPOSITORY_ID,
                RepositorySchema.COURSE_ID,
                RepositorySchema.CONTENT,
                RepositorySchema.EXERCISE_ID,
                RepositorySchema.FILEPATH,
            ],
            limit=5,
        )
        return response
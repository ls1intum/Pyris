import logging
import weaviate
from .lecture_schema import init_lecture_schema
from weaviate.classes.query import Filter
from app.config import settings

logger = logging.getLogger(__name__)

_weaviate_database_client = None


def __del__(self):
    print("Closing Weaviate client")
    self.client.close()


class VectorDatabase:
    """
    Class to interact with the Weaviate vector database
    """

    def __init__(self):
        global _weaviate_database_client
        if not _weaviate_database_client:
            _weaviate_database_client = weaviate.connect_to_local(
                host=settings.weaviate.host,
                port=settings.weaviate.port,
                grpc_port=settings.weaviate.grpc_port,
            )
        self.client = _weaviate_database_client
        self.lectures = init_lecture_schema(self.client)
        print("Weaviate client connected")

    def delete_collection(self, collection_name):
        """
        Delete a collection from the database
        """
        if self.client.collections.exists(collection_name):
            if self.client.collections.delete(collection_name):
                logger.info(f"Collection {collection_name} deleted")
            else:
                logger.error(f"Collection {collection_name} failed to delete")

    def delete_object(self, collection_name, property_name, object_property):
        """
        Delete an object from the collection inside the databse
        """
        collection = self.client.collections.get(collection_name)
        collection.data.delete_many(
            where=Filter.by_property(property_name).equal(object_property)
        )

    def get_client(self):
        """
        Get the Weaviate client
        """
        return self.client

import logging

from qdrant_client import QdrantClient
from qdrant_client.models import PayloadSchemaType

from core.config import get_settings

logger = logging.getLogger(__name__)

FIELDS_TO_INDEX = [
    ("meta.subject", PayloadSchemaType.KEYWORD),
    ("meta.grade", PayloadSchemaType.KEYWORD),
    # Haystack's Qdrant filter converter switches to a full-text MatchText
    # query for any string value containing a space (e.g. "Senior 3",
    # "Computer Science"), which needs its own text-type index separate
    # from the keyword one - both fields can see multi-word values.
    ("meta.subject", PayloadSchemaType.TEXT),
    ("meta.grade", PayloadSchemaType.TEXT),
]


def create_payload_indexes():
    settings = get_settings()
    client = QdrantClient(url=settings.QDRANT_URL, api_key=settings.QDRANT_API_KEY)

    for field, schema in FIELDS_TO_INDEX:
        try:
            client.create_payload_index(
                collection_name=settings.QDRANT_COLLECTION_NAME,
                field_name=field,
                field_schema=schema,
            )
            logger.info("Payload index ready for %s (%s)", field, schema)
        except Exception:
            logger.exception("Failed to create payload index for %s (%s), skipping", field, schema)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    create_payload_indexes()

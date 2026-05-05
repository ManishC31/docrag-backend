from qdrant_client import AsyncQdrantClient
from qdrant_client.models import Distance, PayloadSchemaType, VectorParams

from app.core.config import settings

_client: AsyncQdrantClient | None = None


def get_qdrant_client() -> AsyncQdrantClient:
    if _client is None:
        raise RuntimeError("Qdrant client not initialized — call init_qdrant() first")
    return _client


async def init_qdrant() -> None:
    global _client
    _client = AsyncQdrantClient(
        url=settings.QDRANT_URL,
        api_key=settings.QDRANT_API_KEY,
    )

    exists = await _client.collection_exists(settings.QDRANT_COLLECTION_NAME)
    if not exists:
        await _client.create_collection(
            collection_name=settings.QDRANT_COLLECTION_NAME,
            vectors_config=VectorParams(
                size=settings.EMBEDDING_DIMENSIONS,
                distance=Distance.COSINE,
            ),
        )

    # Ensure payload index exists for document_id filtering (idempotent)
    await _client.create_payload_index(
        collection_name=settings.QDRANT_COLLECTION_NAME,
        field_name="document_id",
        field_schema=PayloadSchemaType.KEYWORD,
    )

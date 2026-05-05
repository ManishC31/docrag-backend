import uuid

from fastapi import HTTPException, status
from openai import AsyncOpenAI
from qdrant_client.models import FieldCondition, Filter, MatchAny, PointStruct
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.constants import (
    DocumentStatus,
    ErrorMessages,
    RAG_SYSTEM_PROMPT,
    RAG_USER_PROMPT_TEMPLATE,
)
from app.db.qdrant import get_qdrant_client
from app.models.document import ChatMessage, Document, DocumentChunk
from app.models.group import Group
from app.models.user import User
from app.schemas.chat import ChatResponse, SourceChunk

openai_client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)


async def _get_embeddings(texts: list[str]) -> list[list[float]]:
    response = await openai_client.embeddings.create(
        model=settings.EMBEDDING_MODEL,
        input=texts,
    )
    return [item.embedding for item in response.data]


async def process_document_chunks(
    document_id: uuid.UUID, chunks: list[str], db: AsyncSession
) -> None:
    batch_size = 100
    all_embeddings: list[list[float]] = []

    for i in range(0, len(chunks), batch_size):
        batch = chunks[i : i + batch_size]
        embeddings = await _get_embeddings(batch)
        all_embeddings.extend(embeddings)

    chunk_records = [
        DocumentChunk(
            document_id=document_id,
            content=chunk,
            chunk_index=i,
        )
        for i, chunk in enumerate(chunks)
    ]
    db.add_all(chunk_records)
    await db.flush()

    points = [
        PointStruct(
            id=str(record.id),
            vector=embedding,
            payload={
                "document_id": str(record.document_id),
                "chunk_index": record.chunk_index,
                "content": record.content,
            },
        )
        for record, embedding in zip(chunk_records, all_embeddings)
    ]

    qdrant = get_qdrant_client()
    await qdrant.upsert(
        collection_name=settings.QDRANT_COLLECTION_NAME,
        points=points,
    )


async def query_group(
    group_id: uuid.UUID,
    question: str,
    current_user: User,
    db: AsyncSession,
) -> ChatResponse:
    result = await db.execute(select(Group).where(Group.id == group_id))
    group = result.scalar_one_or_none()
    if not group:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=ErrorMessages.GROUP_NOT_FOUND
        )
    if group.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=ErrorMessages.GROUP_ACCESS_DENIED,
        )

    doc_result = await db.execute(
        select(Document).where(
            Document.group_id == group_id,
            Document.status == DocumentStatus.READY,
        )
    )
    documents = doc_result.scalars().all()

    if not documents:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=ErrorMessages.NO_DOCUMENTS_IN_GROUP,
        )

    doc_name_map = {str(doc.id): doc.original_filename for doc in documents}
    doc_ids = [str(doc.id) for doc in documents]

    query_embedding = (await _get_embeddings([question]))[0]

    qdrant = get_qdrant_client()
    response = await qdrant.query_points(
        collection_name=settings.QDRANT_COLLECTION_NAME,
        query=query_embedding,
        query_filter=Filter(
            must=[
                FieldCondition(
                    key="document_id",
                    match=MatchAny(any=doc_ids),
                )
            ]
        ),
        limit=settings.TOP_K_CHUNKS,
        with_payload=True,
    )
    hits = response.points

    if not hits:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=ErrorMessages.NO_DOCUMENTS_IN_GROUP,
        )

    context_parts = []
    sources = []
    for hit in hits:
        payload = hit.payload or {}
        doc_name = doc_name_map.get(payload.get("document_id", ""), "Unknown")
        content = payload.get("content", "")
        chunk_index = payload.get("chunk_index", 0)
        context_parts.append(f"[From: {doc_name}]\n{content}")
        sources.append(
            SourceChunk(
                document_name=doc_name,
                content=content[:200] + "..." if len(content) > 200 else content,
                chunk_index=chunk_index,
            )
        )

    context = "\n\n---\n\n".join(context_parts)
    user_prompt = RAG_USER_PROMPT_TEMPLATE.format(context=context, question=question)

    completion = await openai_client.chat.completions.create(
        model=settings.CHAT_MODEL,
        messages=[
            {"role": "system", "content": RAG_SYSTEM_PROMPT},
            {"role": "user", "content": user_prompt},
        ],
        temperature=0.2,
    )
    answer = completion.choices[0].message.content or ""

    chat_message = ChatMessage(
        group_id=group_id,
        user_id=current_user.id,
        question=question,
        answer=answer,
        sources=[s.model_dump() for s in sources],
    )
    db.add(chat_message)
    await db.flush()

    return ChatResponse(
        id=chat_message.id,
        question=question,
        answer=answer,
        sources=sources,
        created_at=chat_message.created_at,
    )


async def get_chat_history(
    group_id: uuid.UUID, current_user: User, db: AsyncSession
) -> list[ChatResponse]:
    result = await db.execute(select(Group).where(Group.id == group_id))
    group = result.scalar_one_or_none()
    if not group:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=ErrorMessages.GROUP_NOT_FOUND
        )
    if group.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=ErrorMessages.GROUP_ACCESS_DENIED,
        )

    msg_result = await db.execute(
        select(ChatMessage)
        .where(ChatMessage.group_id == group_id)
        .order_by(ChatMessage.created_at.asc())
    )
    messages = msg_result.scalars().all()

    return [
        ChatResponse(
            id=msg.id,
            question=msg.question,
            answer=msg.answer,
            sources=[SourceChunk(**s) for s in (msg.sources or [])],
            created_at=msg.created_at,
        )
        for msg in messages
    ]

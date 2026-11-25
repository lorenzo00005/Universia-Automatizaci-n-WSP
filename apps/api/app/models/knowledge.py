"""Base de conocimiento del negocio (FAQ, documentos) con embeddings en pgvector."""

import uuid

from pgvector.sqlalchemy import Vector
from sqlalchemy import ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, IdMixin, TenantMixin, TimestampMixin

EMBEDDING_DIM = 1024


class Document(IdMixin, TimestampMixin, TenantMixin, Base):
    __tablename__ = "documents"

    title: Mapped[str] = mapped_column(String(300))
    source: Mapped[str] = mapped_column(String(40))  # faq | pdf | audio | photo | web | manual
    storage_key: Mapped[str | None] = mapped_column(String(500))
    content: Mapped[str] = mapped_column(Text, default="")
    meta: Mapped[dict[str, object]] = mapped_column(JSONB, default=dict)


class DocumentChunk(IdMixin, TimestampMixin, TenantMixin, Base):
    __tablename__ = "document_chunks"

    document_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("documents.id", ondelete="CASCADE"), index=True
    )
    position: Mapped[int] = mapped_column(Integer)
    content: Mapped[str] = mapped_column(Text)
    embedding: Mapped[list[float] | None] = mapped_column(Vector(EMBEDDING_DIM))

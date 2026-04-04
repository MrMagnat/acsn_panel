from sqlalchemy import String, Text, Integer, DateTime, ForeignKey, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from .base import Base, gen_uuid


class KnowledgeBase(Base):
    __tablename__ = "knowledge_bases"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=gen_uuid)
    user_id: Mapped[str] = mapped_column(String, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    created_at = mapped_column(DateTime(timezone=True), server_default=func.now())

    fields: Mapped[list["KBField"]] = relationship(
        "KBField", back_populates="kb", cascade="all, delete-orphan",
        order_by="KBField.sort_order"
    )
    records: Mapped[list["KBRecord"]] = relationship(
        "KBRecord", back_populates="kb", cascade="all, delete-orphan",
        order_by="KBRecord.created_at"
    )


class KBField(Base):
    __tablename__ = "kb_fields"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=gen_uuid)
    kb_id: Mapped[str] = mapped_column(String, ForeignKey("knowledge_bases.id", ondelete="CASCADE"), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    field_type: Mapped[str] = mapped_column(String(50), default="text", nullable=False)
    sort_order: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    kb: Mapped["KnowledgeBase"] = relationship("KnowledgeBase", back_populates="fields")


class KBRecord(Base):
    __tablename__ = "kb_records"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=gen_uuid)
    kb_id: Mapped[str] = mapped_column(String, ForeignKey("knowledge_bases.id", ondelete="CASCADE"), nullable=False, index=True)
    data: Mapped[str] = mapped_column(Text, nullable=False, default="{}")
    created_at = mapped_column(DateTime(timezone=True), server_default=func.now())

    kb: Mapped["KnowledgeBase"] = relationship("KnowledgeBase", back_populates="records")

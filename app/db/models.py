from sqlalchemy import (
    Column,
    String,
    Boolean,
    Integer,
    ForeignKey,
    DateTime,
    CheckConstraint,
    UniqueConstraint,
    Text,
)
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid

from app.db.base import Base


class User(Base):
    __tablename__ = "users"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email = Column(String(255), unique=True, nullable=False, index=True)
    gender = Column(String(10), nullable=False)
    hashed_password = Column(String(255), nullable=False)
    partner_id = Column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    qr_code_token = Column(String(255), nullable=True)
    sharing_settings = Column(
        JSONB,
        nullable=False,
        server_default='{"share_periods": true, "share_ovulation": true, "share_notes": true}',
    )
    created_at = Column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    # Relationships
    cycles = relationship("Cycle", back_populates="user", cascade="all, delete-orphan")
    notes = relationship("Note", back_populates="user", cascade="all, delete-orphan")
    partner = relationship("User", remote_side=[id], uselist=False)

    __table_args__ = (CheckConstraint("gender IN ('woman', 'man')", name="check_gender"),)


class Cycle(Base):
    __tablename__ = "cycles"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    period_start_date = Column(DateTime(timezone=True), nullable=False, index=True)
    period_end_date = Column(DateTime(timezone=True), nullable=True)
    cycle_length = Column(Integer, nullable=True)
    period_length = Column(Integer, nullable=True)
    is_predicted = Column(Boolean, nullable=False, default=False)
    created_at = Column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    # Relationships
    user = relationship("User", back_populates="cycles")

    __table_args__ = (
        CheckConstraint(
            "period_end_date IS NULL OR period_end_date >= period_start_date",
            name="check_period_dates",
        ),
        CheckConstraint(
            "cycle_length IS NULL OR cycle_length > 0", name="check_cycle_length_positive"
        ),
        CheckConstraint(
            "period_length IS NULL OR period_length > 0",
            name="check_period_length_positive",
        ),
    )


class Note(Base):
    __tablename__ = "notes"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    date = Column(DateTime(timezone=True), nullable=False, index=True)
    text = Column(Text, nullable=True)
    emoji_notes = Column(JSONB, nullable=False, server_default="[]")
    created_at = Column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    # Relationships
    user = relationship("User", back_populates="notes")

    __table_args__ = (UniqueConstraint("user_id", "date", name="uq_user_date"),)

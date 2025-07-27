"""Define models for entity types using SqlAlchemy syntax."""

from sqlalchemy import Column, String, Integer, TIMESTAMP
from sqlalchemy import func
from sqlalchemy.dialects.postgresql import UUID  # noqa: F401 (unused import)
from app.core.database import Base


class User(Base):
    """ORM Model for a user."""
    __tablename__ = "users"

    id = Column(Integer, primary_key=True)
    email = Column(String(100), unique=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    created_at = Column(TIMESTAMP(timezone=True), default=func.now())

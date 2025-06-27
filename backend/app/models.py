"""ORM Model for a User and a Password hash.

   Passwords are used only for local authentication, so
   not all users have a password. Hence a separate table.
   Users may be authenticated by other means, e.g. OAuth.
"""

# DateTime, Integer, TIMESTAMP are convenience classes for sqlalchemy.sql.sqltypes.{name}
from datetime import datetime
from sqlalchemy import ForeignKey, String, Integer, TIMESTAMP, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
# If using UUID for keys add these:
#   from sqlalchemy.dialects.postgresql import UUID
#   import uuid

# To initialize table schema using SqlAlchemy,
# you must use the Base defined in the database module
from app.core.database import Base, db


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True, nullable=False)
    email: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    username: Mapped[str] = mapped_column(String(50))
    created_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), nullable=False, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), server_default=func.now())


class UserPassword(Base):
    """Store a user's password as a hash. Only for locally authenticated users."""
    __tablename__ = "user_passwords"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, nullable=False)
    hashed_password: Mapped[str] = mapped_column(String, nullable=False)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"),
                     nullable=False)
    

def initialize_schema(engine):
    """Create the table schema."""
    db.create_tables()
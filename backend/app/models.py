"""ORM Model for a User and a Password hash.

   Passwords are used only for local authentication, so
   not all users have a password. Hence a separate table.
   Users may be authenticated by other means, e.g. OAuth.

   We need client-side computation of the current datetime
   (and timezone-aware) for two reasons:

   1. Testing with SQLite.  SQLite does not provide timezone-aware timestamps.
      func.now() returns a naive UTC value, even if "TIMESTAMP(timezone=True)"
      is used in the model.
      Unfortunately, client-side computation of datetime doesn't fix this.
      SQLite *always* returns timezone unaware datetimes.

   2. We want user.updated_at to be accessible outside of a Session.
      For async access, if updated_at is defined with "onupdate=func.now"
      then an attempt is made to access the server, which raises a
      MissingGreenlet error when done outside the scope of a session.
"""

# DateTime, Integer, TIMESTAMP are convenience classes for sqlalchemy.sql.sqltypes.{name}
from datetime import datetime, timezone
from sqlalchemy import Boolean, ForeignKey, String, Integer, TIMESTAMP
from sqlalchemy import Boolean, ForeignKey, String, Integer, TIMESTAMP
from sqlalchemy.orm import Mapped, mapped_column, relationship
# If using UUID for keys add these:
# from sqlalchemy.dialects.postgresql import UUID
# import uuid

# To initialize table schema using SqlAlchemy,
# you must use the Base defined in the database module
from app.core.database import Base
from app.core.database import Base
from app.core.config import MAX_DESC, MAX_EMAIL, MAX_NAME, MAX_UNIT_NAME


def utcnow() -> datetime:
    """Return the current datetime as a timezone aware value."""
    return datetime.now(timezone.utc)


class User(Base):
    """Model for a User than can own DataSources."""
    __tablename__ = "users"
    id: Mapped[int] = mapped_column(primary_key=True, nullable=False)
    email: Mapped[str] = mapped_column(String(MAX_EMAIL), unique=True, nullable=False)
    username: Mapped[str] = mapped_column(String(MAX_NAME))
    created_at: Mapped[datetime] = mapped_column(
                                    TIMESTAMP(timezone=True),
                                    nullable=False, 
                                    # server_default=func.now()
                                    default=utcnow
                                    )
    # updated_at is automatically updated by database?
    # could this be a problem if datbase server is in a different timezone from application server?
    updated_at: Mapped[datetime] = mapped_column(
                                    TIMESTAMP(timezone=True),
                                    default=utcnow,
                                    # server_default=func.now(),
                                    # using the server-side func.now() will cause
                                    # an error when updated_at is accessed outside of a session.
                                    # Use client side code (default=...) instead.
                                    onupdate=utcnow
                                    )

    # a uni-directional relationship.
    # To make it bidirectional add backref=...
    # or use back_populates=... on BOTH sides of the relationship
    user_password: Mapped["UserPassword"] = relationship(
                                    "UserPassword",
                                    backref="user",
                                    uselist=False,
                                    cascade="all, delete-orphan"
                                    )

    def __str__(self) -> str:
        """Return a string representation of user data."""
        return f'id={self.id} "{self.username[:40]}" <{self.email}>'


class UserPassword(Base):
    """Store user's password as a hash. Only for locally authenticated users."""
    __tablename__ = "user_passwords"
    user_id: Mapped[int] = mapped_column(
                                    Integer,
                                    ForeignKey("users.id", ondelete="CASCADE"),
                                    primary_key=True,
                                    nullable=False
                                    )
    hashed_password: Mapped[str] = mapped_column(String, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
                                    TIMESTAMP(timezone=True),
                                    # server_default=func.now()
                                    default=utcnow
                                    )


class DataSource(Base):
    """A source of data values, such as a meter or sensor."""
    __tablename__ = "data_sources"
    id: Mapped[int] = mapped_column(primary_key=True, nullable=False)
    name: Mapped[str] = mapped_column(String(MAX_NAME), nullable=False)
    owner_id: Mapped[int] = mapped_column(
                                    Integer,
                                    ForeignKey("users.id", ondelete="SET NULL"),
                                    nullable=True
                                    )
    description: Mapped[str] = mapped_column(String(MAX_DESC), nullable=True)
    unit: Mapped[str] = mapped_column(String(MAX_UNIT_NAME), nullable=True)
    is_public: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(
                                    TIMESTAMP(timezone=True),
                                    default=utcnow,
                                    nullable=False
                                    )

    # Relationships (optional)
    owner = relationship("User", foreign_keys=[owner_id], backref="data_sources")

    def __str__(self) -> str:
        """Return a string representation of a data source."""
        created_str = self.created_at.strftime("%d-%m-%Y") if self.created_at else "None"
        return f'id={self.id} "{self.name[:40]}" owner={self.owner_id} created {created_str}'


# For testing. Normally you should do this in app/core/database.py
#
# def initialize_schema(engine):
#    """Create the table schema."""
#    db.create_tables()

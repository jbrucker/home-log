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
from sqlalchemy import ForeignKey, String, Integer, TIMESTAMP, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
# If using UUID for keys add these:
#   from sqlalchemy.dialects.postgresql import UUID
#   import uuid

# To initialize table schema using SqlAlchemy,
# you must use the Base defined in the database module
from app.core.database import Base, db



def utcnow() -> datetime:
    """Return the current datetime as a timezone aware value."""
    return datetime.now(timezone.utc)

class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True, nullable=False)
    email: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    username: Mapped[str] = mapped_column(String(50))
    created_at: Mapped[datetime] = mapped_column(
                                        TIMESTAMP(timezone=True),
                                        nullable=False, 
                                        #server_default=func.now()
                                        default=utcnow
                                    )
    # updated_at is automatically updated by database? 
    # could this be a problem if datbase server is in a different timezone from application server?
    updated_at: Mapped[datetime] = mapped_column(
                                        TIMESTAMP(timezone=True),
                                        #server_default=func.now(),
                                        default=utcnow,
                                        # using the server-side function func.now() will cause
                                        # an error when updated_at is accessed outside of a session.
                                        # Use client side code instead.
                                        onupdate=utcnow
                                    )

    # a uni-directional relationship.  
    # To make it bidirectional use backref=... 
    # use use back_populates=... on BOTH sides of the relationship
    user_password: Mapped["UserPassword"] = relationship("UserPassword", 
                                         # backref=("user",uselist=False),
                                         uselist=False,  
                                         cascade="all, delete-orphan"
                                         )


class UserPassword(Base):
    """Store user's password as a hash. Only for locally authenticated users."""
    __tablename__ = "user_passwords"
    user_id: Mapped[int] = mapped_column(Integer,
                                         ForeignKey("users.id", ondelete="CASCADE"),
                                         primary_key=True, 
                                         nullable=False)
    hashed_password: Mapped[str] = mapped_column(String, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
                                        TIMESTAMP(timezone=True), 
                                        # server_default=func.now()
                                        default=utcnow
                                    )
    

# For testing. Do this in app/core/database.py 
#
#def initialize_schema(engine):
#    """Create the table schema."""
#    db.create_tables()

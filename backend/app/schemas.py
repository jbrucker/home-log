"""Pydantic schemas for type validation, serialization, and deserialization.

These schemas are used in API route handlers.
"""

import re
# from annotated_types import MinLen, MaxLen
from datetime import datetime, timezone
from typing import Annotated, Any, Optional
from uuid import UUID
from pydantic import AfterValidator, BaseModel, ConfigDict, EmailStr, Field, SecretStr
from app.core.config import MAX_DESC, MAX_EMAIL, MAX_NAME


def _validate_password(secret: SecretStr) -> SecretStr:
    """Enforce internal validation rules for passwords."""
    password = secret.get_secret_value()
    errors = []
    if not re.search(r"[A-Z]", password):
        errors.append("Missing uppercase letter A-Z")
    if not re.search(r"[a-z]", password):
        errors.append("Missing lowercase letter a-z")
    if not re.search(r"\d", password):
        errors.append("Missing digit 0-9")
    if re.match(r"^\s.*", password) or re.match(r".*\s$", password):
        errors.append("May not begin/end with whitespace")
    # Don't require special chars
    # if not re.search(r"[!@#$%^&*()_+{}\[\]:;<>,.?~\\-]", value):
    #    errors.append("Missing special character (!@#$...)")
    if re.search(r"(.)\1\1", password):
        errors.append("May not 3+ consecutive repeated character")
    if errors:
        raise ValueError(", ".join(errors))
    return secret


# A custom validator for Password strings.
PasswordStr = Annotated[
    SecretStr,                            # PasswordStr _is_ a SecretStr
    Field(min_length=7, max_length=255),  # Basic constraints
    AfterValidator(_validate_password)    # Runs after basic validation
]


class PasswordCreate(BaseModel):
    """Set or change a password.

    `password` is a `SecretStr`. Use str(password.get_secret()) to extract it.
    """
    password: PasswordStr


class UserCreate(BaseModel):
    """User attributes that are given to a service endpoint to create a new User entity."""
    # RFC 5321: max length of an email address is 254 chars. See Wiki for Pydantic's limits.
    email: EmailStr = Field(..., max_length=MAX_EMAIL)
    username: Optional[str] = Field(None, max_length=MAX_NAME)


class User(UserCreate):
    """The complete User schema."""
    # For testing include id, for security omit it.
    id: Optional[int] = None
    # In model classes, these default to current time
    created_at: datetime = datetime.now(timezone.utc)
    updated_at: datetime = datetime.now(timezone.utc)
    # model_config replaces the Config inner-class in Pydantic 2.0
    model_config = ConfigDict(from_attributes=True)


class DataSourceCreate(BaseModel):
    """Schema for creating a new DataSource."""
    name: str = Field(..., max_length=MAX_NAME)
    description: Optional[str] = Field(None, max_length=MAX_DESC)
    # The default value of 'data' is a dict with key "value" and unit name (value) ""
    data: dict[str, str] = Field(default_factory=lambda: {"value": ""})
    # Need to be able to specify owner when source is created
    owner_id: Optional[int] = None


class DataSource(DataSourceCreate):
    """Schema for validating and returning a DataSource."""
    id: int
    owner_id: int
    created_at: datetime = datetime.now(timezone.utc)
    model_config = ConfigDict(from_attributes=True)


class ReadingData(BaseModel):
    """Schema for a required Reading data for reading from a specific DataSource.
    
    This omits the data_source_id and created_by_id, since:
    - in a request the data source id is a path param, created_by_id is the current user's id
    - in a response, data_source_id is redundant (omit to save space)
    """
    # Allow reading values to be Any or require Number?
    values: dict[str, Any]
    # Timestamp should be specified
    timestamp: Optional[datetime] = None
    # Client cannot specify created_by_id. It is determined by authorized user.


class ReadingCreate(ReadingData):
    """Schema to create a new reading contains reading data + refs to data source and creator."""
    # Data Source id is required in DAO
    data_source_id: int
    # Creator is required
    created_by_id: int = None
    # Timestamp should be specified or required?
    # timestamp: Optional[datetime] = None


class Reading(ReadingCreate):
    """Schema for a reading from a data source."""
    id: int
    timestamp: datetime = datetime.now(timezone.utc)


class Token(BaseModel):
    """The fields in a JWT access token, used for authentication."""
    access_token: str
    token_type: str


class TokenData(BaseModel):
    """The fields in the token payload.

        These can be anything you want, but "sub" is the customary name for subject.
    """
    id: Optional[str] = None

"""Pydantic schemas for type validation, serialization, and deserialization.

These schemas are used in API route handlers.
"""
import re
from datetime import datetime, timezone
from typing import Annotated, Optional
from annotated_types import MinLen, MaxLen  # noqa: F401
from pydantic import AfterValidator, BaseModel, ConfigDict, EmailStr, Field, SecretStr
from app.core.config import MAX_DESC, MAX_EMAIL, MAX_NAME, MAX_UNIT_NAME


def _validate_password(password: SecretStr) -> SecretStr:
    """Enforce internal validation rules for passwords."""
    value = password.get_secret_value()
    errors = []
    if not re.search(r"[A-Z]", value):
        errors.append("Missing uppercase letter A-Z")
    if not re.search(r"[a-z]", value):
        errors.append("Missing lowercase letter a-z")
    if not re.search(r"\d", value):
        errors.append("Missing digit 0-9")
    if re.match(r"^\s.*", value) or re.match(r".*\s$", value):
        errors.append("May not begin/end with whitespace")
    # Don't require special chars
    # if not re.search(r"[!@#$%^&*()_+{}\[\]:;<>,.?~\\-]", value):
    #    rerrors.append("Missing special character (!@#$...)")
    if re.search(r"(.)\1\1", value):
        errors.append("3+ repeated characters in a row")
    if errors:
        raise ValueError(", ".join(errors))
    return password


# Define a custom validator for Password strings.
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
    unit: Optional[str] = Field(None, max_length=MAX_UNIT_NAME)
    # Need to be able to specify owner when source is created
    owner_id: Optional[int] = None


class DataSource(DataSourceCreate):
    """Schema for validating and returning a DataSource."""
    id: int
    owner_id: int
    created_at: datetime = datetime.now(timezone.utc)
    model_config = ConfigDict(from_attributes=True)


class Token(BaseModel):
    """The fields in a JWT access token, used for authentication."""
    access_token: str
    token_type: str


class TokenData(BaseModel):
    """The fields in the token payload.

        These can be anything you want, but "sub" is the customary name for subject.
    """
    id: Optional[str] = None

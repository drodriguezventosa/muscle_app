"""Request/response models for the coaching sign-in."""

from pydantic import BaseModel, ConfigDict, EmailStr, Field

from app.domain.value_objects.enums import UserRole


class LoginRequest(BaseModel):
    """Credentials. Length is bounded so a huge body cannot reach the hasher."""

    email: EmailStr
    password: str = Field(min_length=6, max_length=128)


class UserRead(BaseModel):
    """The signed-in user. Never includes the password hash."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    email: str
    name: str
    role: UserRole


class SessionRead(BaseModel):
    """Access token plus who it belongs to."""

    access_token: str
    token_type: str = "bearer"  # noqa: S105 - OAuth2 token type, not a secret
    expires_in: int
    user: UserRead

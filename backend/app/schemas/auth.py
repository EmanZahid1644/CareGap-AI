
from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr, Field

from backend.app.models.identity import AccountType


class RegisterRequest(BaseModel):
    email: EmailStr
    full_name: str = Field(min_length=2, max_length=200)
    password: str = Field(min_length=12, max_length=128)
    account_type: AccountType

    model_config = ConfigDict(str_strip_whitespace=True)


class LoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=1, max_length=128)

    model_config = ConfigDict(str_strip_whitespace=True)


class UserResponse(BaseModel):
    id: UUID
    email: EmailStr
    full_name: str
    account_type: AccountType

    model_config = ConfigDict(from_attributes=True)


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"

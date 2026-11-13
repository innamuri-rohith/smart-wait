"""Request and response schemas with input validation."""
from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator

from app.db.models import Role


def validate_password_strength(value: str) -> str:
    if len(value.encode("utf-8")) > 72:
        raise ValueError("Password must be at most 72 bytes long")
    if not any(c.isalpha() for c in value) or not any(c.isdigit() for c in value):
        raise ValueError("Password must contain at least one letter and one digit")
    return value


class StudentRegister(BaseModel):
    full_name: str = Field(min_length=2, max_length=120)
    email: EmailStr
    password: str = Field(min_length=8, max_length=64)
    roll_number: str = Field(min_length=3, max_length=30, pattern=r"^[A-Za-z0-9/-]+$")
    department: str | None = Field(default=None, max_length=100)

    @field_validator("password")
    @classmethod
    def check_password(cls, value: str) -> str:
        return validate_password_strength(value)


class StaffCreate(BaseModel):
    full_name: str = Field(min_length=2, max_length=120)
    email: EmailStr
    password: str = Field(min_length=8, max_length=64)
    employee_code: str = Field(min_length=3, max_length=30, pattern=r"^[A-Za-z0-9-]+$")
    designation: str | None = Field(default=None, max_length=100)

    @field_validator("password")
    @classmethod
    def check_password(cls, value: str) -> str:
        return validate_password_strength(value)


class LoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=1, max_length=64)


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    role: Role


class UserOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    email: str
    full_name: str
    role: Role
    is_active: bool

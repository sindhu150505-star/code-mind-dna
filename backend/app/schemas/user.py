import re

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator

from app.models.user import UserRole
from app.core.config import settings


class UserBase(BaseModel):
    full_name: str
    email: EmailStr
    role: UserRole = UserRole.STUDENT

    @field_validator("full_name")
    @classmethod
    def validate_full_name(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("Full name is required")
        return value

    @field_validator("email")
    @classmethod
    def normalize_email(cls, value: EmailStr) -> EmailStr:
        return str(value).lower()


class UserCreate(UserBase):
    password: str

    @field_validator("password")
    @classmethod
    def validate_password(cls, value: str) -> str:
        if len(value) < settings.password_min_length:
            raise ValueError(f"Password must be at least {settings.password_min_length} characters long")
        if settings.password_require_uppercase and not any(c.isupper() for c in value):
            raise ValueError("Password must contain at least one uppercase letter")
        if settings.password_require_lowercase and not any(c.islower() for c in value):
            raise ValueError("Password must contain at least one lowercase letter")
        if settings.password_require_digit and not any(c.isdigit() for c in value):
            raise ValueError("Password must contain at least one digit")
        if settings.password_require_special_char and not any(c in "!@#$%^&*(),.?\":{}|<>_-+=\\[\\];'/`~" for c in value):
            raise ValueError("Password must contain at least one special character")
        return value


class UserOut(BaseModel):
    id: int
    full_name: str
    email: str
    role: UserRole

    model_config = ConfigDict(from_attributes=True)


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class AdminPhoneLoginRequest(BaseModel):
    phone_number: str = Field(min_length=1, max_length=32)

    @field_validator("phone_number")
    @classmethod
    def normalize_phone_number(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("Phone number is required")
        if not re.fullmatch(r"\+?[\d\s\-().]+", value):
            raise ValueError("Enter a valid phone number")
        normalized = re.sub(r"[\s\-().]", "", value).lstrip("+")
        if not normalized.isdigit() or not 8 <= len(normalized) <= 15:
            raise ValueError("Enter a valid phone number")
        return normalized


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserOut


class RegistrationResponse(BaseModel):
    message: str
    user: UserOut

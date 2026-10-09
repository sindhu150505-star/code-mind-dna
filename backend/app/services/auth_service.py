import hashlib
import secrets

from fastapi import HTTPException, status
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.core.security import (
    create_access_token,
    hash_password,
    revoke_user,
    verify_password,
    validate_password_complexity,
)
from app.core.config import settings
from app.models.user import User, UserRole
from app.repositories.user_repository import UserRepository
from app.schemas.user import RegistrationResponse, TokenResponse, UserCreate, UserOut


PUBLIC_REGISTRATION_ROLES = {UserRole.STUDENT, UserRole.MENTOR, UserRole.RECRUITER}


class AuthService:
    def __init__(self, db: Session):
        self.db = db
        self.repository = UserRepository(db)

    def register(self, payload: UserCreate) -> RegistrationResponse:
        if payload.role not in PUBLIC_REGISTRATION_ROLES:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Admin accounts cannot be created through public registration.",
            )
        if self.repository.get_by_email(payload.email):
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Email already registered")

        # Validate password complexity
        validate_password_complexity(payload.password)

        user = User(
            full_name=payload.full_name,
            email=str(payload.email),
            password_hash=hash_password(payload.password),
            role=payload.role,
        )
        try:
            self.repository.create(user)
        except SQLAlchemyError as exc:
            self.db.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Unable to create your account. Please try again.",
            ) from exc
        return RegistrationResponse(
            message="Account created successfully. Please log in.",
            user=UserOut(id=user.id, full_name=user.full_name, email=user.email, role=user.role),
        )

    def login(self, email: str, password: str) -> TokenResponse:
        user = self.repository.get_by_email(email)
        if not user or not verify_password(password, user.password_hash):
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid email or password")
        if not user.is_active:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="User account is inactive")
        return self._build_token_response(user)

    def login_admin_with_phone(self, phone_number: str) -> TokenResponse:
        allowed_numbers = settings.normalized_admin_phone_numbers
        if len(allowed_numbers) != 4:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Admin login is temporarily unavailable.",
            )
        if phone_number not in allowed_numbers:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied. This number is not authorized for admin access.",
            )

        # The identifier is one-way derived so the database does not store the phone number.
        identifier = hashlib.sha256(phone_number.encode("utf-8")).hexdigest()
        email = f"admin-{identifier}@internal.codemind"
        user = self.repository.get_by_email(email)
        if user is None:
            user = User(
                full_name="Authorized Administrator",
                email=email,
                password_hash=hash_password(secrets.token_urlsafe(32)),
                role=UserRole.ADMIN,
            )
            try:
                self.repository.create(user)
            except SQLAlchemyError as exc:
                self.db.rollback()
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Unable to complete admin authentication. Please try again.",
                ) from exc
        elif not user.is_active or user.role != UserRole.ADMIN:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied.")

        return self._build_token_response(user)

    def get_current_user(self, token: str) -> User:
        from app.core.security import decode_access_token

        payload = decode_access_token(token)
        email = payload.get("sub")
        if not email:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")
        user = self.repository.get_by_email(email)
        if not user:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")
        return user

    def logout(self, user: User) -> None:
        revoke_user(user.email)

    def _build_token_response(self, user: User) -> TokenResponse:
        token = create_access_token(user.email, user.id, user.role.value)
        user_out = UserOut(id=user.id, full_name=user.full_name, email=user.email, role=user.role)
        return TokenResponse(access_token=token, user=user_out)


def require_role(*allowed_roles: UserRole):
    def role_checker(current_user: User = None):
        if current_user is None:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Authentication required")
        if current_user.role not in allowed_roles:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")
        return current_user

    return role_checker

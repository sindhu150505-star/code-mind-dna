from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core.database import get_db
from app.schemas.user import AdminPhoneLoginRequest, LoginRequest, RegistrationResponse, TokenResponse, UserCreate, UserOut
from app.services.auth_service import AuthService

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=RegistrationResponse, status_code=status.HTTP_201_CREATED)
def register(payload: UserCreate, db: Session = Depends(get_db)) -> RegistrationResponse:
    service = AuthService(db)
    return service.register(payload)


@router.post("/login", response_model=TokenResponse)
def login(payload: LoginRequest, db: Session = Depends(get_db)) -> TokenResponse:
    service = AuthService(db)
    return service.login(str(payload.email), payload.password)


@router.post("/admin/login", response_model=TokenResponse)
def admin_login(payload: AdminPhoneLoginRequest, db: Session = Depends(get_db)) -> TokenResponse:
    service = AuthService(db)
    return service.login_admin_with_phone(payload.phone_number)


@router.get("/me", response_model=UserOut)
def get_me(current_user=Depends(get_current_user)) -> UserOut:
    return UserOut(id=current_user.id, full_name=current_user.full_name, email=current_user.email, role=current_user.role)


@router.post("/logout", status_code=status.HTTP_200_OK)
def logout(current_user=Depends(get_current_user), db: Session = Depends(get_db)) -> dict[str, str]:
    service = AuthService(db)
    service.logout(current_user)
    return {"message": "You have been logged out successfully."}

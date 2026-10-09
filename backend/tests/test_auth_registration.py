import uuid

import jwt
import pytest
from fastapi.testclient import TestClient

from app.core.config import settings
from app.core.database import SessionLocal
from app.main import app
from app.models.problem import DifficultyLevel, Problem, TopicType
from app.models.user import User


client = TestClient(app)
PASSWORD = "SecurePassword"


def register_payload(role: str, email: str | None = None) -> dict[str, str]:
    return {
        "full_name": f"{role.title()} User",
        "email": email or f"{role.lower()}-{uuid.uuid4().hex}@example.com",
        "password": PASSWORD,
        "role": role,
    }


@pytest.mark.parametrize(
    ("role", "protected_path"),
    [
        ("STUDENT", "/api/student/dashboard"),
        ("MENTOR", "/api/mentor/dashboard"),
        ("RECRUITER", "/api/recruiter/jobs"),
    ],
)
def test_public_roles_can_register_then_log_in(role: str, protected_path: str):
    payload = register_payload(role)
    registration = client.post("/api/auth/register", json=payload)

    assert registration.status_code == 201
    assert registration.json() == {
        "message": "Account created successfully. Please log in.",
        "user": {
            "id": registration.json()["user"]["id"],
            "full_name": payload["full_name"],
            "email": payload["email"],
            "role": role,
        },
    }
    assert "access_token" not in registration.json()
    assert "password" not in registration.json()
    assert "password_hash" not in registration.json()
    with SessionLocal() as db:
        stored_user = db.query(User).filter(User.email == payload["email"]).one()
        assert stored_user.password_hash != PASSWORD
        assert stored_user.password_hash.startswith("$2")

    login = client.post("/api/auth/login", json={"email": payload["email"], "password": PASSWORD})
    assert login.status_code == 200
    token = login.json()["access_token"]
    claims = jwt.decode(token, settings.jwt_secret, algorithms=[settings.jwt_algorithm])
    assert claims["user_id"] == registration.json()["user"]["id"]
    assert claims["role"] == role
    assert client.get(protected_path, headers={"Authorization": f"Bearer {token}"}).status_code == 200


def test_registration_rejects_admin_and_invalid_roles():
    admin_response = client.post("/api/auth/register", json=register_payload("ADMIN"))
    assert admin_response.status_code == 403
    assert admin_response.json()["detail"] == "Admin accounts cannot be created through public registration."
    assert client.post("/api/auth/register", json=register_payload("INVALID")).status_code == 422


def test_registration_and_login_validation_errors_are_safe():
    payload = register_payload("STUDENT", "duplicate@example.com")
    assert client.post("/api/auth/register", json=payload).status_code == 201
    assert client.post("/api/auth/register", json=payload).status_code == 409
    assert client.post("/api/auth/login", json={"email": payload["email"], "password": "wrong"}).status_code == 401
    assert client.post("/api/auth/register", json=register_payload("STUDENT", "invalid-email")).status_code == 422
    weak = register_payload("STUDENT", "weak@example.com")
    weak["password"] = "short"
    assert client.post("/api/auth/register", json=weak).status_code == 422


def test_protected_route_requires_a_valid_token():
    assert client.get("/api/student/dashboard").status_code == 401
    assert client.get("/api/student/dashboard", headers={"Authorization": "Bearer invalid"}).status_code == 401


def test_all_authorized_admin_numbers_can_log_in(monkeypatch):
    authorized_numbers = "+12025550101,+12025550102,+12025550103,+12025550104"
    monkeypatch.setattr(settings, "admin_phone_numbers", authorized_numbers)

    for raw_phone_number in ["+1 202-555-0101", "+1 (202) 555-0102", "+1 202 555 0103", "+12025550104"]:
        response = client.post("/api/auth/admin/login", json={"phone_number": raw_phone_number})
        assert response.status_code == 200
        token = response.json()["access_token"]
        claims = jwt.decode(token, settings.jwt_secret, algorithms=[settings.jwt_algorithm])
        assert claims["role"] == "ADMIN"
        assert client.get("/api/admin/dashboard", headers={"Authorization": f"Bearer {token}"}).status_code == 200


def test_admin_login_rejects_unauthorized_and_invalid_numbers(monkeypatch):
    monkeypatch.setattr(settings, "admin_phone_numbers", "+12025550101,+12025550102,+12025550103,+12025550104")

    rejected = client.post("/api/auth/admin/login", json={"phone_number": "+12025550999"})
    assert rejected.status_code == 403
    assert rejected.json()["detail"] == "Access denied. This number is not authorized for admin access."
    assert client.post("/api/auth/admin/login", json={"phone_number": ""}).status_code == 422
    assert client.post("/api/auth/admin/login", json={"phone_number": "not-a-phone"}).status_code == 422


@pytest.mark.parametrize("role", ["STUDENT", "MENTOR", "RECRUITER"])
def test_non_admin_roles_cannot_access_admin_dashboard(role: str):
    payload = register_payload(role)
    assert client.post("/api/auth/register", json=payload).status_code == 201
    login = client.post("/api/auth/login", json={"email": payload["email"], "password": PASSWORD})
    token = login.json()["access_token"]
    assert client.get("/api/admin/dashboard", headers={"Authorization": f"Bearer {token}"}).status_code == 403


def test_student_can_update_an_existing_code_draft():
    payload = register_payload("STUDENT")
    registration = client.post("/api/auth/register", json=payload)
    student_id = registration.json()["user"]["id"]
    login = client.post("/api/auth/login", json={"email": payload["email"], "password": PASSWORD})
    headers = {"Authorization": f"Bearer {login.json()['access_token']}"}

    with SessionLocal() as db:
        problem = Problem(
            title="Draft Save Test",
            slug="draft-save-test",
            description="Test problem",
            difficulty=DifficultyLevel.EASY,
            topic=TopicType.ARRAYS,
            constraints="None",
            input_format="None",
            output_format="None",
            created_by=student_id,
        )
        db.add(problem)
        db.commit()
        db.refresh(problem)
        problem_id = problem.id

    first_save = client.put(
        f"/api/problems/{problem_id}/draft",
        json={"language": "python", "code": "print('first')"},
        headers=headers,
    )
    second_save = client.put(
        f"/api/problems/{problem_id}/draft",
        json={"language": "python", "code": "print('updated')"},
        headers=headers,
    )
    assert first_save.status_code == 200
    assert second_save.status_code == 200
    assert second_save.json()["code"] == "print('updated')"
    assert second_save.json()["updated_at"]

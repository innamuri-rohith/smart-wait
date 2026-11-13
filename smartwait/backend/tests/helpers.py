"""Shared test utilities. Tests use an in-memory SQLite database, so no PostgreSQL is needed."""
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.security import hash_password
from app.db.models import Role, Staff, User

TEST_ENGINE = create_engine(
    "sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool
)
TestingSession = sessionmaker(bind=TEST_ENGINE, autoflush=False, expire_on_commit=False)


def override_get_db():
    db = TestingSession()
    try:
        yield db
    finally:
        db.close()


def make_user(email: str, role: Role, password: str = "Passw0rd1", employee_code: str = "EMP-001") -> int:
    db = TestingSession()
    try:
        user = User(
            email=email,
            password_hash=hash_password(password),
            full_name="Test User",
            role=role,
        )
        if role == Role.staff:
            user.staff = Staff(employee_code=employee_code, designation="Clerk")
        db.add(user)
        db.commit()
        return user.id
    finally:
        db.close()


def login(client, email: str, password: str = "Passw0rd1") -> str:
    response = client.post("/api/auth/login", json={"email": email, "password": password})
    assert response.status_code == 200, response.text
    return response.json()["access_token"]


def auth_header(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}

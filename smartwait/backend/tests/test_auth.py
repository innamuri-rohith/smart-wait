"""Sprint 2 tests: registration, login, token security, and role-based access."""
from app.db.models import Role
from tests.helpers import auth_header, login, make_user

STUDENT = {
    "full_name": "Arjun Kumar",
    "email": "Arjun@College.edu",
    "password": "Passw0rd1",
    "roll_number": "21CS001",
    "department": "CSE",
}


def register(client, **overrides):
    return client.post("/api/auth/register/student", json={**STUDENT, **overrides})


# ---------- Registration and validation ----------

def test_student_can_register_and_password_is_never_returned(client):
    r = register(client)
    assert r.status_code == 201
    body = r.json()
    assert body["role"] == "student"
    assert body["email"] == "arjun@college.edu"
    assert "password" not in body and "password_hash" not in body


def test_duplicate_email_is_rejected(client):
    register(client)
    r = register(client, roll_number="21CS002")
    assert r.status_code == 409


def test_duplicate_roll_number_is_rejected(client):
    register(client)
    r = register(client, email="other@college.edu")
    assert r.status_code == 409


def test_weak_password_is_rejected(client):
    assert register(client, password="abcdefgh").status_code == 422      # no digit
    assert register(client, password="12345678").status_code == 422      # no letter
    assert register(client, password="short1").status_code == 422        # too short


def test_invalid_roll_number_is_rejected(client):
    assert register(client, roll_number="21 CS!!").status_code == 422


def test_invalid_email_is_rejected(client):
    assert register(client, email="not-an-email").status_code == 422


# ---------- Login ----------

def test_login_returns_bearer_token_and_role(client):
    register(client)
    r = client.post("/api/auth/login", json={"email": "arjun@college.edu", "password": "Passw0rd1"})
    assert r.status_code == 200
    body = r.json()
    assert body["token_type"] == "bearer"
    assert body["role"] == "student"
    assert body["access_token"]


def test_login_with_wrong_password_gives_generic_error(client):
    register(client)
    r = client.post("/api/auth/login", json={"email": "arjun@college.edu", "password": "WrongPass9"})
    assert r.status_code == 401
    assert r.json()["detail"] == "Invalid email or password"


def test_login_with_unknown_email_gives_same_error(client):
    r = client.post("/api/auth/login", json={"email": "nobody@college.edu", "password": "Passw0rd1"})
    assert r.status_code == 401
    assert r.json()["detail"] == "Invalid email or password"


# ---------- Token handling ----------

def test_me_requires_a_token(client):
    assert client.get("/api/auth/me").status_code == 401


def test_me_rejects_a_tampered_token(client):
    register(client)
    token = login(client, "arjun@college.edu")
    tampered = token[:-4] + "abcd"
    assert client.get("/api/auth/me", headers=auth_header(tampered)).status_code == 401


def test_me_rejects_garbage_token(client):
    assert client.get("/api/auth/me", headers=auth_header("not.a.jwt")).status_code == 401


def test_me_returns_current_user(client):
    register(client)
    token = login(client, "arjun@college.edu")
    r = client.get("/api/auth/me", headers=auth_header(token))
    assert r.status_code == 200
    assert r.json()["email"] == "arjun@college.edu"


def test_inactive_user_cannot_use_token(client):
    user_id = make_user("staff@college.edu", Role.admin)
    token = login(client, "staff@college.edu")

    from tests.helpers import TestingSession
    from app.db.models import User
    db = TestingSession()
    db.get(User, user_id).is_active = False
    db.commit()
    db.close()

    assert client.get("/api/auth/me", headers=auth_header(token)).status_code == 401


# ---------- Role-based authorization ----------

def test_student_is_blocked_from_admin_routes(client):
    register(client)
    token = login(client, "arjun@college.edu")
    assert client.get("/api/admin/users", headers=auth_header(token)).status_code == 403


def test_student_is_blocked_from_staff_portal(client):
    register(client)
    token = login(client, "arjun@college.edu")
    assert client.get("/api/portal/staff", headers=auth_header(token)).status_code == 403


def test_anonymous_user_is_blocked_from_portal(client):
    assert client.get("/api/portal/student").status_code == 401


def test_student_portal_returns_own_profile(client):
    register(client)
    token = login(client, "arjun@college.edu")
    r = client.get("/api/portal/student", headers=auth_header(token))
    assert r.status_code == 200
    assert r.json()["roll_number"] == "21CS001"
    assert r.json()["priority_category"] == "general"


def test_admin_can_create_staff_and_list_users(client):
    make_user("admin@college.edu", Role.admin)
    admin_token = login(client, "admin@college.edu")

    r = client.post(
        "/api/admin/staff",
        headers=auth_header(admin_token),
        json={
            "full_name": "Ravi Shankar",
            "email": "ravi@college.edu",
            "password": "Staff1234",
            "employee_code": "EMP-010",
            "designation": "Fee Clerk",
        },
    )
    assert r.status_code == 201
    assert r.json()["role"] == "staff"

    listing = client.get("/api/admin/users", headers=auth_header(admin_token))
    assert listing.status_code == 200
    emails = [u["email"] for u in listing.json()]
    assert "ravi@college.edu" in emails


def test_duplicate_employee_code_is_rejected(client):
    make_user("admin@college.edu", Role.admin)
    admin_token = login(client, "admin@college.edu")
    payload = {
        "full_name": "Ravi Shankar",
        "email": "ravi@college.edu",
        "password": "Staff1234",
        "employee_code": "EMP-010",
    }
    assert client.post("/api/admin/staff", headers=auth_header(admin_token), json=payload).status_code == 201
    payload["email"] = "other@college.edu"
    assert client.post("/api/admin/staff", headers=auth_header(admin_token), json=payload).status_code == 409


def test_staff_can_access_staff_portal_but_not_admin_portal(client):
    make_user("staff@college.edu", Role.staff, employee_code="EMP-001")
    staff_token = login(client, "staff@college.edu")

    assert client.get("/api/portal/staff", headers=auth_header(staff_token)).status_code == 200
    assert client.get("/api/portal/admin", headers=auth_header(staff_token)).status_code == 403


def test_admin_portal_counts_users_by_role(client):
    make_user("admin@college.edu", Role.admin)
    make_user("staff@college.edu", Role.staff, employee_code="EMP-001")
    admin_token = login(client, "admin@college.edu")

    r = client.get("/api/portal/admin", headers=auth_header(admin_token))
    assert r.status_code == 200
    assert r.json()["users_by_role"] == {"admin": 1, "staff": 1}

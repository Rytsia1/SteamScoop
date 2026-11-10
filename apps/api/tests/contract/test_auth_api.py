"""API contract tests for authentication and session management."""

from __future__ import annotations

from fastapi.testclient import TestClient

from app.schemas.auth import LoginResponseData, UserProfileResponse
from app.schemas.common import ResponseEnvelope


def test_auth_full_lifecycle(client: TestClient) -> None:
    test_email = "researcher.test@example.com"
    test_password = "SecurePassword123!"
    display_name = "Dr. Researcher"

    # 1. Register
    reg_payload = {
        "email": test_email,
        "password": test_password,
        "display_name": display_name,
    }
    reg_res = client.post("/api/v1/auth/register", json=reg_payload)
    assert reg_res.status_code == 201
    reg_data = reg_res.json()
    validated_reg = ResponseEnvelope[UserProfileResponse].model_validate(reg_data)
    assert validated_reg.data is not None
    assert validated_reg.data.email == test_email
    assert validated_reg.data.display_name == display_name
    assert "password" not in str(reg_data)

    # 2. Duplicate registration rejected with 409
    dup_res = client.post("/api/v1/auth/register", json=reg_payload)
    assert dup_res.status_code == 409
    assert dup_res.json()["error"]["code"] == "RESOURCE_ALREADY_EXISTS"

    # 3. Login with bad credentials rejected with 401
    bad_login = client.post(
        "/api/v1/auth/login",
        json={"email": test_email, "password": "WrongPassword!"},
    )
    assert bad_login.status_code == 401
    assert bad_login.json()["error"]["code"] == "INVALID_CREDENTIALS"

    # 4. Successful Login
    login_res = client.post(
        "/api/v1/auth/login",
        json={"email": test_email, "password": test_password},
    )
    assert login_res.status_code == 200
    login_data = login_res.json()
    validated_login = ResponseEnvelope[LoginResponseData].model_validate(login_data)
    assert validated_login.data is not None
    token = validated_login.data.token
    assert token != ""
    assert "session_token" in login_res.cookies

    # 5. Access /auth/me with Bearer Token
    me_bearer = client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert me_bearer.status_code == 200
    assert me_bearer.json()["data"]["email"] == test_email

    # 6. Access /auth/me with session cookie
    me_cookie = client.get("/api/v1/auth/me", cookies={"session_token": token})
    assert me_cookie.status_code == 200
    assert me_cookie.json()["data"]["email"] == test_email

    # 7. Logout
    logout_res = client.post(
        "/api/v1/auth/logout",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert logout_res.status_code == 204

    # 8. Access /auth/me after logout rejected with 401
    me_after = client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert me_after.status_code == 401
    assert me_after.json()["error"]["code"] == "UNAUTHENTICATED"


def test_auth_me_unauthenticated(client: TestClient) -> None:
    res = client.get("/api/v1/auth/me")
    assert res.status_code == 401
    assert res.json()["error"]["code"] == "UNAUTHENTICATED"


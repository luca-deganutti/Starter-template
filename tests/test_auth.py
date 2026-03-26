from fastapi.testclient import TestClient


def test_register_first_user_becomes_admin(client: TestClient) -> None:
    response = client.post(
        "/api/v1/auth/register",
        json={
            "full_name": "Admin User",
            "email": "admin@example.com",
            "password": "secret123",
        },
    )

    assert response.status_code == 201
    payload = response.json()
    assert payload["email"] == "admin@example.com"
    assert payload["role"] == "admin"
    assert payload["is_active"] is True


def test_login_and_me_return_authenticated_user(client: TestClient) -> None:
    client.post(
        "/api/v1/auth/register",
        json={
            "full_name": "Admin User",
            "email": "admin@example.com",
            "password": "secret123",
        },
    )

    login_response = client.post(
        "/api/v1/auth/login",
        data={
            "username": "admin@example.com",
            "password": "secret123",
        },
    )

    assert login_response.status_code == 200
    token_payload = login_response.json()
    assert token_payload["token_type"] == "bearer"
    assert "access_token" in token_payload
    assert "refresh_token" in token_payload
    assert token_payload["access_token_expires_in"] > 0
    assert token_payload["refresh_token_expires_in"] > 0

    me_response = client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {token_payload['access_token']}"},
    )

    assert me_response.status_code == 200
    me_payload = me_response.json()
    assert me_payload["email"] == "admin@example.com"
    assert me_payload["role"] == "admin"


def test_non_admin_cannot_access_admin_endpoint(client: TestClient) -> None:
    client.post(
        "/api/v1/auth/register",
        json={
            "full_name": "Admin User",
            "email": "admin@example.com",
            "password": "secret123",
        },
    )
    client.post(
        "/api/v1/auth/register",
        json={
            "full_name": "Regular User",
            "email": "user@example.com",
            "password": "secret123",
        },
    )

    login_response = client.post(
        "/api/v1/auth/login",
        data={
            "username": "user@example.com",
            "password": "secret123",
        },
    )
    access_token = login_response.json()["access_token"]

    response = client.get(
        "/api/v1/users",
        headers={"Authorization": f"Bearer {access_token}"},
    )

    assert response.status_code == 403


def test_refresh_token_rotation_invalidates_old_refresh_token(
    client: TestClient,
) -> None:
    client.post(
        "/api/v1/auth/register",
        json={
            "full_name": "Admin User",
            "email": "admin@example.com",
            "password": "secret123",
        },
    )
    login_response = client.post(
        "/api/v1/auth/login",
        data={
            "username": "admin@example.com",
            "password": "secret123",
        },
    )
    refresh_token = login_response.json()["refresh_token"]

    response = client.post(
        "/api/v1/auth/refresh",
        json={"refresh_token": refresh_token},
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["token_type"] == "bearer"
    assert "access_token" in payload
    assert "refresh_token" in payload
    assert payload["refresh_token"] != refresh_token

    reused_response = client.post(
        "/api/v1/auth/refresh",
        json={"refresh_token": refresh_token},
    )
    assert reused_response.status_code == 401

    rotated_refresh = payload["refresh_token"]
    revoked_chain_response = client.post(
        "/api/v1/auth/refresh",
        json={"refresh_token": rotated_refresh},
    )
    assert revoked_chain_response.status_code == 401


def test_logout_revokes_refresh_token(client: TestClient) -> None:
    client.post(
        "/api/v1/auth/register",
        json={
            "full_name": "Admin User",
            "email": "admin@example.com",
            "password": "secret123",
        },
    )
    login_response = client.post(
        "/api/v1/auth/login",
        data={
            "username": "admin@example.com",
            "password": "secret123",
        },
    )
    refresh_token = login_response.json()["refresh_token"]

    logout_response = client.post(
        "/api/v1/auth/logout",
        json={"refresh_token": refresh_token},
    )
    assert logout_response.status_code == 204

    refresh_response = client.post(
        "/api/v1/auth/refresh",
        json={"refresh_token": refresh_token},
    )
    assert refresh_response.status_code == 401


def test_change_password_revokes_existing_refresh_tokens(client: TestClient) -> None:
    client.post(
        "/api/v1/auth/register",
        json={
            "full_name": "Admin User",
            "email": "admin@example.com",
            "password": "secret123",
        },
    )
    login_response = client.post(
        "/api/v1/auth/login",
        data={
            "username": "admin@example.com",
            "password": "secret123",
        },
    )
    token_payload = login_response.json()

    change_password_response = client.post(
        "/api/v1/auth/change-password",
        headers={"Authorization": f"Bearer {token_payload['access_token']}"},
        json={
            "current_password": "secret123",
            "new_password": "new-secret123",
        },
    )
    assert change_password_response.status_code == 204

    refresh_response = client.post(
        "/api/v1/auth/refresh",
        json={"refresh_token": token_payload["refresh_token"]},
    )
    assert refresh_response.status_code == 401

    old_login_response = client.post(
        "/api/v1/auth/login",
        data={
            "username": "admin@example.com",
            "password": "secret123",
        },
    )
    assert old_login_response.status_code == 401

    new_login_response = client.post(
        "/api/v1/auth/login",
        data={
            "username": "admin@example.com",
            "password": "new-secret123",
        },
    )
    assert new_login_response.status_code == 200

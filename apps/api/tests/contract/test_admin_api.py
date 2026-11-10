"""API contract tests for administrative operations, ingestion monitoring, and model activation."""

from __future__ import annotations

from typing import Any

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.core.security import hash_password
from app.repositories.user import UserRepository
from app.schemas.admin import (
    AdminGameResponse,
    AdminIngestionJobResponse,
    AdminModelActivateResponse,
    AdminModelResponse,
)
from app.schemas.common import ResponseEnvelope


def _setup_admin_token(client: TestClient, db: Session) -> str:
    user_repo = UserRepository(db)
    admin_user = user_repo.get_by_email("admin.tester@steamscoop.com")
    if not admin_user:
        admin_user = user_repo.create_user(
            email="admin.tester@steamscoop.com",
            password_hash=hash_password("AdminPass123!"),
            display_name="System Admin",
            status="active",
            roles=["admin", "member"],
        )

    res = client.post(
        "/api/v1/auth/login",
        json={"email": "admin.tester@steamscoop.com", "password": "AdminPass123!"},
    )
    return res.json()["data"]["token"]


def _setup_regular_token(client: TestClient) -> str:
    client.post(
        "/api/v1/auth/register",
        json={
            "email": "regular.user@example.com",
            "password": "UserPass123!",
            "display_name": "Regular User",
        },
    )
    res = client.post(
        "/api/v1/auth/login",
        json={"email": "regular.user@example.com", "password": "UserPass123!"},
    )
    return res.json()["data"]["token"]


def test_admin_routes_forbidden_for_regular_users(client: TestClient) -> None:
    # 1. Unauthenticated request -> 401
    unauth_res = client.get("/api/v1/admin/games")
    assert unauth_res.status_code == 401

    # 2. Authenticated non-admin request -> 403 FORBIDDEN
    reg_token = _setup_regular_token(client)
    forbidden_res = client.get(
        "/api/v1/admin/games",
        headers={"Authorization": f"Bearer {reg_token}"},
    )
    assert forbidden_res.status_code == 403
    assert forbidden_res.json()["error"]["code"] == "FORBIDDEN"


def test_admin_catalog_management(
    client: TestClient, db_session: Session, sample_catalog: dict[str, Any]
) -> None:
    token = _setup_admin_token(client, db_session)
    admin_header = {"Authorization": f"Bearer {token}"}

    # 1. List Catalog Games
    list_res = client.get("/api/v1/admin/games", headers=admin_header)
    assert list_res.status_code == 200
    games = ResponseEnvelope[list[AdminGameResponse]].model_validate(list_res.json()).data
    assert games is not None
    assert len(games) >= 2

    # 2. Add Game to Catalog
    new_app_id = 999123
    create_payload = {
        "steam_app_id": new_app_id,
        "name": "Stardew Valley Testing",
        "short_description": "Farming simulation game.",
        "genres": ["Simulation", "RPG"],
        "catalog_status": "indexed",
    }
    create_res = client.post("/api/v1/admin/games", json=create_payload, headers=admin_header)
    assert create_res.status_code == 201
    created_game = ResponseEnvelope[AdminGameResponse].model_validate(create_res.json()).data
    assert created_game is not None
    assert created_game.steam_app_id == new_app_id
    game_id = str(created_game.id)

    # 3. Patch Game
    patch_res = client.patch(
        f"/api/v1/admin/games/{game_id}",
        json={"name": "Stardew Valley Expanded"},
        headers=admin_header,
    )
    assert patch_res.status_code == 200
    assert patch_res.json()["data"]["name"] == "Stardew Valley Expanded"


def test_admin_ingestion_and_pipeline_orchestration(
    client: TestClient, db_session: Session, sample_catalog: dict[str, Any]
) -> None:
    token = _setup_admin_token(client, db_session)
    admin_header = {"Authorization": f"Bearer {token}"}
    game_id = str(sample_catalog["game2"].id)

    # 1. Queue Ingestion Job
    job_payload = {
        "job_type": "incremental",
        "collection_config": {"review_type": "all", "overlap_days": 7},
        "reason": "Test routine sync",
    }
    queue_res = client.post(
        f"/api/v1/admin/games/{game_id}/ingestion-jobs",
        json=job_payload,
        headers=admin_header,
    )
    assert queue_res.status_code == 202
    job_data = ResponseEnvelope[AdminIngestionJobResponse].model_validate(queue_res.json()).data
    assert job_data is not None
    job_id = str(job_data.job_id)
    assert job_data.status in ("queued", "running")

    # 2. Active Job Conflict Check (409 ACTIVE_JOB_EXISTS)
    conflict_res = client.post(
        f"/api/v1/admin/games/{game_id}/ingestion-jobs",
        json=job_payload,
        headers=admin_header,
    )
    assert conflict_res.status_code == 409
    assert conflict_res.json()["error"]["code"] == "ACTIVE_JOB_EXISTS"

    # 3. Get Ingestion Job Details
    get_job_res = client.get(f"/api/v1/admin/ingestion-jobs/{job_id}", headers=admin_header)
    assert get_job_res.status_code == 200
    assert get_job_res.json()["data"]["job_id"] == job_id

    # 4. Cancel Ingestion Job
    cancel_res = client.post(f"/api/v1/admin/ingestion-jobs/{job_id}/cancel", headers=admin_header)
    assert cancel_res.status_code == 200
    assert cancel_res.json()["data"]["status"] == "cancelled"

    # 5. Retry Ingestion Job
    retry_res = client.post(f"/api/v1/admin/ingestion-jobs/{job_id}/retry", headers=admin_header)
    assert retry_res.status_code == 202
    assert retry_res.json()["data"]["status"] == "queued"


def test_admin_model_registry_and_activation(
    client: TestClient, db_session: Session, sample_catalog: dict[str, Any]
) -> None:
    token = _setup_admin_token(client, db_session)
    admin_header = {"Authorization": f"Bearer {token}"}

    # 1. List registered models
    models_res = client.get("/api/v1/admin/models", headers=admin_header)
    assert models_res.status_code == 200
    models = ResponseEnvelope[list[AdminModelResponse]].model_validate(models_res.json()).data
    assert models is not None
    assert len(models) >= 1

    target_model = models[0]
    model_id = str(target_model.id)

    # 2. Activate model
    activate_res = client.post(f"/api/v1/admin/models/{model_id}/activate", headers=admin_header)
    assert activate_res.status_code == 200
    act_data = ResponseEnvelope[AdminModelActivateResponse].model_validate(activate_res.json()).data
    assert act_data is not None
    assert act_data.is_active is True


def test_admin_metadata_refresh(
    client: TestClient, db_session: Session, sample_catalog: dict[str, Any]
) -> None:
    token = _setup_admin_token(client, db_session)
    admin_header = {"Authorization": f"Bearer {token}"}
    reg_token = _setup_regular_token(client)
    regular_header = {"Authorization": f"Bearer {reg_token}"}
    game_id = str(sample_catalog["game1"].id)

    # 1. Non-admin forbidden
    forbidden_res = client.post(
        f"/api/v1/admin/games/{game_id}/metadata-refresh",
        headers=regular_header,
    )
    assert forbidden_res.status_code == 403

    # 2. Admin queues metadata refresh
    res = client.post(
        f"/api/v1/admin/games/{game_id}/metadata-refresh",
        headers=admin_header,
    )
    assert res.status_code == 202
    assert res.json()["data"]["game_id"] == game_id
    assert res.json()["data"]["status"] == "queued"

    # 3. Non-existent game returns 404
    missing_id = "00000000-0000-0000-0000-000000000000"
    missing_res = client.post(
        f"/api/v1/admin/games/{missing_id}/metadata-refresh",
        headers=admin_header,
    )
    assert missing_res.status_code == 404
    assert missing_res.json()["error"]["code"] == "GAME_NOT_FOUND"


def test_admin_audit_logs_and_operational_errors(
    client: TestClient, db_session: Session, sample_catalog: dict[str, Any]
) -> None:
    token = _setup_admin_token(client, db_session)
    admin_header = {"Authorization": f"Bearer {token}"}
    reg_token = _setup_regular_token(client)
    regular_header = {"Authorization": f"Bearer {reg_token}"}

    # 1. Non-admin forbidden from audit logs and operational errors
    assert client.get("/api/v1/admin/audit-logs", headers=regular_header).status_code == 403
    assert client.get("/api/v1/admin/operational-errors", headers=regular_header).status_code == 403

    # 2. Admin retrieves audit logs (at least one action from previous operations)
    audit_res = client.get("/api/v1/admin/audit-logs", headers=admin_header)
    assert audit_res.status_code == 200
    logs = audit_res.json()["data"]
    assert isinstance(logs, list)

    # 3. Admin retrieves operational errors
    errors_res = client.get("/api/v1/admin/operational-errors", headers=admin_header)
    assert errors_res.status_code == 200
    errors_data = errors_res.json()["data"]
    assert "failed_ingestion_jobs" in errors_data
    assert "failed_pipeline_runs" in errors_data
    assert "total_failures" in errors_data

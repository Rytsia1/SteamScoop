"""API contract and integration tests for asynchronous data exports and downloads."""

from __future__ import annotations

import io
import json
import os
import uuid
import zipfile
from datetime import UTC, datetime, timedelta
from typing import Any

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models.workspace import ExportJob
from app.schemas.common import ResponseEnvelope
from app.schemas.export import ExportResponseData
from app.services.export_service import ExportService


def _get_auth_token(client: TestClient, email: str = "export.tester@example.com") -> str:
    client.post(
        "/api/v1/auth/register",
        json={
            "email": email,
            "password": "Password123!",
            "display_name": f"User {email.split('@')[0]}",
        },
    )
    res = client.post(
        "/api/v1/auth/login",
        json={"email": email, "password": "Password123!"},
    )
    return res.json()["data"]["token"]


def test_export_full_lifecycle(client: TestClient, sample_catalog: dict[str, Any]) -> None:
    token = _get_auth_token(client, "lifecycle.user@example.com")
    auth_header = {"Authorization": f"Bearer {token}"}
    game_id = str(sample_catalog["game1"].id)

    # 1. Enqueue valid CSV export job
    export_payload = {
        "format": "csv",
        "scope": {"type": "game_reviews", "game_id": game_id},
        "filters": {"language": "english"},
        "fields": ["review_text", "language", "sentiment", "steam_created_at"],
    }
    custom_id = "test-export-req-001"
    create_res = client.post(
        "/api/v1/exports",
        json=export_payload,
        headers={**auth_header, "X-Request-ID": custom_id},
    )
    assert create_res.status_code == 202
    assert create_res.headers.get("X-Request-ID") == custom_id

    create_data = create_res.json()
    validated = ResponseEnvelope[ExportResponseData].model_validate(create_data)
    assert validated.error is None
    assert validated.data is not None
    assert validated.data.status == "queued"
    export_id = str(validated.data.export_id)

    # 2. Check export status
    status_res = client.get(f"/api/v1/exports/{export_id}", headers=auth_header)
    assert status_res.status_code == 200
    status_data = status_res.json()["data"]
    assert status_data["export_id"] == export_id
    assert status_data["format"] == "csv"

    # 3. Download export artifact
    dl_res = client.get(f"/api/v1/exports/{export_id}/download", headers=auth_header)
    assert dl_res.status_code == 200
    assert "text/csv" in dl_res.headers["content-type"]
    assert f'attachment; filename="export_{export_id}.csv"' in dl_res.headers["content-disposition"]
    csv_text = dl_res.text
    assert "review_text" in csv_text
    assert "sentiment" in csv_text

    # 4. Cancel export
    del_res = client.delete(f"/api/v1/exports/{export_id}", headers=auth_header)
    assert del_res.status_code == 204


def test_export_formats_json_and_xlsx(client: TestClient, sample_catalog: dict[str, Any]) -> None:
    token = _get_auth_token(client, "formats.tester@example.com")
    auth_header = {"Authorization": f"Bearer {token}"}
    game_id = str(sample_catalog["game1"].id)

    # 1. JSON Export
    json_res = client.post(
        "/api/v1/exports",
        json={
            "format": "json",
            "scope": {"type": "game_reviews", "game_id": game_id},
            "fields": ["review_text", "sentiment", "language"],
        },
        headers=auth_header,
    )
    assert json_res.status_code == 202
    json_export_id = json_res.json()["data"]["export_id"]

    json_dl = client.get(f"/api/v1/exports/{json_export_id}/download", headers=auth_header)
    assert json_dl.status_code == 200
    assert "application/json" in json_dl.headers["content-type"]
    json_data = json.loads(json_dl.text)
    assert isinstance(json_data, list)
    if json_data:
        assert "review_text" in json_data[0]
        assert "sentiment" in json_data[0]

    # 2. XLSX Export
    xlsx_res = client.post(
        "/api/v1/exports",
        json={
            "format": "xlsx",
            "scope": {"type": "game_reviews", "game_id": game_id},
            "fields": ["review_text", "sentiment", "voted_up"],
        },
        headers=auth_header,
    )
    assert xlsx_res.status_code == 202
    xlsx_export_id = xlsx_res.json()["data"]["export_id"]

    xlsx_dl = client.get(f"/api/v1/exports/{xlsx_export_id}/download", headers=auth_header)
    assert xlsx_dl.status_code == 200
    assert "spreadsheetml" in xlsx_dl.headers["content-type"]
    assert f'attachment; filename="export_{xlsx_export_id}.xlsx"' in xlsx_dl.headers["content-disposition"]

    # Verify OpenXML structure
    with zipfile.ZipFile(io.BytesIO(xlsx_dl.content), "r") as zf:
        namelist = zf.namelist()
        assert "[Content_Types].xml" in namelist
        assert "xl/workbook.xml" in namelist
        assert "xl/worksheets/sheet1.xml" in namelist


def test_empty_export(client: TestClient, sample_catalog: dict[str, Any]) -> None:
    token = _get_auth_token(client, "empty.tester@example.com")
    auth_header = {"Authorization": f"Bearer {token}"}
    game_id = str(sample_catalog["game1"].id)

    # Filter with non-existent language
    res = client.post(
        "/api/v1/exports",
        json={
            "format": "csv",
            "scope": {"type": "game_reviews", "game_id": game_id},
            "filters": {"language": "non_existent_dialect_xyz"},
            "fields": ["review_text", "sentiment"],
        },
        headers=auth_header,
    )
    assert res.status_code == 202
    export_id = res.json()["data"]["export_id"]

    dl_res = client.get(f"/api/v1/exports/{export_id}/download", headers=auth_header)
    assert dl_res.status_code == 200
    # Should contain headers only
    lines = dl_res.text.strip().splitlines()
    assert len(lines) == 1
    assert "review_text" in lines[0]


def test_oversized_export_rejection(client: TestClient, sample_catalog: dict[str, Any]) -> None:
    token = _get_auth_token(client, "oversized.tester@example.com")
    auth_header = {"Authorization": f"Bearer {token}"}
    game_id = str(sample_catalog["game1"].id)

    # 1. Row limit exceeding role quota (member limit is 10,000)
    res = client.post(
        "/api/v1/exports",
        json={
            "format": "csv",
            "scope": {"type": "game_reviews", "game_id": game_id},
            "fields": ["review_text"],
            "row_limit": 50000,  # Exceeds member quota
        },
        headers=auth_header,
    )
    assert res.status_code == 413
    assert res.json()["error"]["code"] == "EXPORT_LIMIT_EXCEEDED"

    # 2. Date range exceeding 730 days
    res_date = client.post(
        "/api/v1/exports",
        json={
            "format": "csv",
            "scope": {"type": "game_reviews", "game_id": game_id},
            "filters": {"from": "2020-01-01", "to": "2025-01-01"},  # 5 years
            "fields": ["review_text"],
        },
        headers=auth_header,
    )
    assert res_date.status_code == 422
    assert res_date.json()["error"]["code"] == "VALIDATION_ERROR"

    # 3. Inverted date range (from > to)
    res_inv = client.post(
        "/api/v1/exports",
        json={
            "format": "csv",
            "scope": {"type": "game_reviews", "game_id": game_id},
            "filters": {"from": "2026-11-01", "to": "2026-01-01"},
            "fields": ["review_text"],
        },
        headers=auth_header,
    )
    assert res_inv.status_code == 422


def test_unauthorized_download_and_uuid_manipulation(
    client: TestClient, sample_catalog: dict[str, Any]
) -> None:
    token_a = _get_auth_token(client, "user_a@example.com")
    token_b = _get_auth_token(client, "user_b@example.com")
    game_id = str(sample_catalog["game1"].id)

    # User A creates export
    res = client.post(
        "/api/v1/exports",
        json={
            "format": "csv",
            "scope": {"type": "game_reviews", "game_id": game_id},
            "fields": ["review_text"],
        },
        headers={"Authorization": f"Bearer {token_a}"},
    )
    assert res.status_code == 202
    export_id = res.json()["data"]["export_id"]

    # User B attempts to view status
    res_status = client.get(
        f"/api/v1/exports/{export_id}",
        headers={"Authorization": f"Bearer {token_b}"},
    )
    assert res_status.status_code == 404
    assert res_status.json()["error"]["code"] == "EXPORT_NOT_FOUND"

    # User B attempts download
    res_dl = client.get(
        f"/api/v1/exports/{export_id}/download",
        headers={"Authorization": f"Bearer {token_b}"},
    )
    assert res_dl.status_code == 404
    assert res_dl.json()["error"]["code"] == "EXPORT_NOT_FOUND"

    # User B attempts cancellation
    res_del = client.delete(
        f"/api/v1/exports/{export_id}",
        headers={"Authorization": f"Bearer {token_b}"},
    )
    assert res_del.status_code == 404

    # Unauthenticated download (clear cookies to test unauthenticated access)
    client.cookies.clear()
    res_unauth = client.get(f"/api/v1/exports/{export_id}/download")
    assert res_unauth.status_code == 401


def test_worker_failure_handling(
    client: TestClient, sample_catalog: dict[str, Any], db_session: Session
) -> None:
    token = _get_auth_token(client, "failure.tester@example.com")
    auth_header = {"Authorization": f"Bearer {token}"}
    game_id = str(sample_catalog["game1"].id)

    res = client.post(
        "/api/v1/exports",
        json={
            "format": "csv",
            "scope": {"type": "game_reviews", "game_id": game_id},
            "fields": ["review_text"],
        },
        headers=auth_header,
    )
    assert res.status_code == 202
    export_id = res.json()["data"]["export_id"]

    # Simulate worker failure directly in database
    job = db_session.get(ExportJob, uuid.UUID(export_id))
    assert job is not None
    job.status = "failed"
    job.error_code = "GENERATION_FAILED"
    job.finished_at = datetime.now(UTC)
    db_session.flush()

    # Status check reflects failure
    status_res = client.get(f"/api/v1/exports/{export_id}", headers=auth_header)
    assert status_res.status_code == 200
    assert status_res.json()["data"]["status"] == "failed"
    assert status_res.json()["data"]["error_code"] == "GENERATION_FAILED"

    # Download returns 409
    dl_res = client.get(f"/api/v1/exports/{export_id}/download", headers=auth_header)
    assert dl_res.status_code == 409
    assert dl_res.json()["error"]["code"] == "EXPORT_FAILED"


def test_expired_export_and_cleanup(
    client: TestClient, sample_catalog: dict[str, Any], db_session: Session
) -> None:
    token = _get_auth_token(client, "expired.tester@example.com")
    auth_header = {"Authorization": f"Bearer {token}"}
    game_id = str(sample_catalog["game1"].id)

    res = client.post(
        "/api/v1/exports",
        json={
            "format": "csv",
            "scope": {"type": "game_reviews", "game_id": game_id},
            "fields": ["review_text"],
        },
        headers=auth_header,
    )
    assert res.status_code == 202
    export_id = res.json()["data"]["export_id"]

    # First download to trigger successful generation
    dl_first = client.get(f"/api/v1/exports/{export_id}/download", headers=auth_header)
    assert dl_first.status_code == 200

    # Set expires_at in the past (preserving expires_at > created_at check constraint)
    job = db_session.get(ExportJob, uuid.UUID(export_id))
    assert job is not None
    job.created_at = datetime.now(UTC) - timedelta(days=10)
    job.expires_at = datetime.now(UTC) - timedelta(days=1)
    artifact_path = job.artifact_uri
    db_session.flush()

    # Status check reflects expiration
    status_res = client.get(f"/api/v1/exports/{export_id}", headers=auth_header)
    assert status_res.status_code == 200
    assert status_res.json()["data"]["status"] == "expired"

    # Download returns 410 EXPORT_EXPIRED
    dl_res = client.get(f"/api/v1/exports/{export_id}/download", headers=auth_header)
    assert dl_res.status_code == 410
    assert dl_res.json()["error"]["code"] == "EXPORT_EXPIRED"

    # Run cleanup service with test db_session
    service = ExportService(session=db_session)
    service.cleanup_expired_exports()

    if artifact_path:
        assert not os.path.exists(artifact_path)


def test_export_cancellation(client: TestClient, sample_catalog: dict[str, Any]) -> None:
    token = _get_auth_token(client, "cancel.tester@example.com")
    auth_header = {"Authorization": f"Bearer {token}"}
    game_id = str(sample_catalog["game1"].id)

    res = client.post(
        "/api/v1/exports",
        json={
            "format": "csv",
            "scope": {"type": "game_reviews", "game_id": game_id},
            "fields": ["review_text"],
        },
        headers=auth_header,
    )
    assert res.status_code == 202
    export_id = res.json()["data"]["export_id"]

    # Cancel job
    del_res = client.delete(f"/api/v1/exports/{export_id}", headers=auth_header)
    assert del_res.status_code == 204

    # Status check confirms cancelled
    status_res = client.get(f"/api/v1/exports/{export_id}", headers=auth_header)
    assert status_res.status_code == 200
    assert status_res.json()["data"]["status"] == "cancelled"

    # Download returns 409 EXPORT_CANCELLED
    dl_res = client.get(f"/api/v1/exports/{export_id}/download", headers=auth_header)
    assert dl_res.status_code == 409
    assert dl_res.json()["error"]["code"] == "EXPORT_CANCELLED"


def test_concurrency_quota_enforcement(client: TestClient, sample_catalog: dict[str, Any]) -> None:
    token = _get_auth_token(client, "concurrency.tester@example.com")
    auth_header = {"Authorization": f"Bearer {token}"}
    game_id = str(sample_catalog["game1"].id)

    # Create 3 active export jobs
    created_ids: list[str] = []
    for _ in range(3):
        res = client.post(
            "/api/v1/exports",
            json={
                "format": "csv",
                "scope": {"type": "game_reviews", "game_id": game_id},
                "fields": ["review_text"],
            },
            headers=auth_header,
        )
        assert res.status_code == 202
        created_ids.append(res.json()["data"]["export_id"])

    # Attempt 4th active job - exceeds quota (limit is 3)
    res_blocked = client.post(
        "/api/v1/exports",
        json={
            "format": "csv",
            "scope": {"type": "game_reviews", "game_id": game_id},
            "fields": ["review_text"],
        },
        headers=auth_header,
    )
    assert res_blocked.status_code == 429
    assert res_blocked.json()["error"]["code"] == "EXPORT_CONCURRENCY_LIMIT_EXCEEDED"

    # Cancel one job to free up a slot
    del_res = client.delete(f"/api/v1/exports/{created_ids[0]}", headers=auth_header)
    assert del_res.status_code == 204

    # Now creation succeeds again
    res_allowed = client.post(
        "/api/v1/exports",
        json={
            "format": "csv",
            "scope": {"type": "game_reviews", "game_id": game_id},
            "fields": ["review_text"],
        },
        headers=auth_header,
    )
    assert res_allowed.status_code == 202


def test_private_project_export_protection(
    client: TestClient, sample_catalog: dict[str, Any]
) -> None:
    token_owner = _get_auth_token(client, "project.owner@example.com")
    token_stranger = _get_auth_token(client, "project.stranger@example.com")

    # Owner creates a private project
    proj_res = client.post(
        "/api/v1/projects",
        json={"name": "Secret Cohort", "visibility": "private"},
        headers={"Authorization": f"Bearer {token_owner}"},
    )
    assert proj_res.status_code == 201
    project_id = proj_res.json()["data"]["id"]

    # Stranger attempts to export reviews from owner's private project
    stranger_res = client.post(
        "/api/v1/exports",
        json={
            "format": "csv",
            "scope": {"type": "project_reviews", "project_id": project_id},
            "fields": ["review_text"],
        },
        headers={"Authorization": f"Bearer {token_stranger}"},
    )
    assert stranger_res.status_code == 404
    assert stranger_res.json()["error"]["code"] == "PROJECT_NOT_FOUND"

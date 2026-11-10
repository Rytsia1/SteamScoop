"""API contract tests for asynchronous data exports and downloads."""

from __future__ import annotations

from typing import Any

from fastapi.testclient import TestClient

from app.schemas.common import ResponseEnvelope
from app.schemas.export import ExportResponseData


def _get_auth_token(client: TestClient) -> str:
    client.post(
        "/api/v1/auth/register",
        json={
            "email": "export.tester@example.com",
            "password": "Password123!",
            "display_name": "Exporter",
        },
    )
    res = client.post(
        "/api/v1/auth/login",
        json={"email": "export.tester@example.com", "password": "Password123!"},
    )
    return res.json()["data"]["token"]


def test_export_full_lifecycle(client: TestClient, sample_catalog: dict[str, Any]) -> None:
    token = _get_auth_token(client)
    auth_header = {"Authorization": f"Bearer {token}"}
    game_id = str(sample_catalog["game1"].id)

    # 1. Enqueue valid export job
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


def test_export_validation_errors(client: TestClient) -> None:
    token = _get_auth_token(client)
    auth_header = {"Authorization": f"Bearer {token}"}

    # Invalid field rejection
    bad_field_payload = {
        "format": "csv",
        "scope": {"type": "game_reviews"},
        "fields": ["unauthorized_system_field"],
    }
    res_field = client.post("/api/v1/exports", json=bad_field_payload, headers=auth_header)
    assert res_field.status_code == 422
    assert res_field.json()["error"]["code"] == "VALIDATION_ERROR"

    # Invalid scope rejection
    bad_scope_payload = {
        "format": "csv",
        "scope": {"type": "unsupported_scope_type"},
        "fields": ["review_text"],
    }
    res_scope = client.post("/api/v1/exports", json=bad_scope_payload, headers=auth_header)
    assert res_scope.status_code == 422
    assert res_scope.json()["error"]["code"] == "VALIDATION_ERROR"

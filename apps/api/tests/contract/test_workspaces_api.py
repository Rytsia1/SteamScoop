"""API contract tests for research workspace projects, saved analyses, and snapshots."""

from __future__ import annotations

from typing import Any

from fastapi.testclient import TestClient

from app.schemas.common import ResponseEnvelope
from app.schemas.workspace import (
    ProjectGameItem,
    ProjectResponse,
    SavedAnalysisResponse,
    SnapshotResponse,
)


def _register_and_login(client: TestClient, email: str, name: str) -> str:
    """Helper to register and login a test user, returning auth token."""
    client.post(
        "/api/v1/auth/register",
        json={"email": email, "password": "Password123!", "display_name": name},
    )
    res = client.post(
        "/api/v1/auth/login",
        json={"email": email, "password": "Password123!"},
    )
    return res.json()["data"]["token"]


def test_workspaces_full_crud_and_permissions(
    client: TestClient, sample_catalog: dict[str, Any]
) -> None:
    token_a = _register_and_login(client, "alice.workspace@example.com", "Alice")
    token_b = _register_and_login(client, "bob.workspace@example.com", "Bob")
    auth_a = {"Authorization": f"Bearer {token_a}"}
    auth_b = {"Authorization": f"Bearer {token_b}"}

    game1_id = sample_catalog["game1"].id

    # 1. Create Private Project as Alice
    create_payload = {
        "name": "Alice RPG Study",
        "description": "Analyzing RPG sentiment patterns",
        "visibility": "private",
    }
    create_res = client.post("/api/v1/projects", json=create_payload, headers=auth_a)
    assert create_res.status_code == 201
    proj_a = ResponseEnvelope[ProjectResponse].model_validate(create_res.json()).data
    assert proj_a is not None
    proj_id = proj_a.id

    # 2. List Projects as Alice (should see her project)
    list_res = client.get("/api/v1/projects", headers=auth_a)
    assert list_res.status_code == 200
    projects_a = list_res.json()["data"]
    assert any(p["id"] == str(proj_id) for p in projects_a)

    # 3. Object-level security: Bob cannot access Alice's private project (returns 404 to avoid leak)
    bob_res = client.get(f"/api/v1/projects/{proj_id}", headers=auth_b)
    assert bob_res.status_code == 404
    assert bob_res.json()["error"]["code"] == "PROJECT_NOT_FOUND"

    # Bob's project list does NOT include Alice's project
    bob_list = client.get("/api/v1/projects", headers=auth_b).json()["data"]
    assert not any(p["id"] == str(proj_id) for p in bob_list)

    # 4. Patch Project as Alice
    patch_res = client.patch(
        f"/api/v1/projects/{proj_id}",
        json={"description": "Updated description"},
        headers=auth_a,
    )
    assert patch_res.status_code == 200
    assert patch_res.json()["data"]["description"] == "Updated description"

    # 5. Add Game to Project
    add_game_res = client.post(
        f"/api/v1/projects/{proj_id}/games",
        json={"game_id": str(game1_id)},
        headers=auth_a,
    )
    assert add_game_res.status_code == 200
    validated_game = ResponseEnvelope[ProjectGameItem].model_validate(add_game_res.json()).data
    assert validated_game is not None
    assert validated_game.game_id == game1_id

    # List games in project
    games_list_res = client.get(f"/api/v1/projects/{proj_id}/games", headers=auth_a)
    assert games_list_res.status_code == 200
    assert len(games_list_res.json()["data"]) == 1

    # 6. Saved Analysis CRUD
    analysis_payload = {
        "name": "Negative Performance Reviews",
        "description": "Reviews discussing performance aspects negatively",
        "analysis_type": "review_explorer",
        "query_config": {
            "game_ids": [str(game1_id)],
            "aspect": "performance",
            "sentiment": "negative",
        },
    }
    ana_create_res = client.post(
        f"/api/v1/projects/{proj_id}/analyses",
        json=analysis_payload,
        headers=auth_a,
    )
    assert ana_create_res.status_code == 201
    ana_data = ResponseEnvelope[SavedAnalysisResponse].model_validate(ana_create_res.json()).data
    assert ana_data is not None
    ana_id = ana_data.id

    # Get Analysis
    ana_get_res = client.get(f"/api/v1/projects/{proj_id}/analyses/{ana_id}", headers=auth_a)
    assert ana_get_res.status_code == 200
    assert ana_get_res.json()["data"]["name"] == "Negative Performance Reviews"

    # Patch Analysis
    ana_patch_res = client.patch(
        f"/api/v1/projects/{proj_id}/analyses/{ana_id}",
        json={"name": "Renamed Performance Reviews"},
        headers=auth_a,
    )
    assert ana_patch_res.status_code == 200
    assert ana_patch_res.json()["data"]["name"] == "Renamed Performance Reviews"

    # 7. Snapshots
    snap_payload = {
        "name": "Q4-2026 Snapshot",
        "description": "Baseline before major game patch",
    }
    snap_create_res = client.post(
        f"/api/v1/projects/{proj_id}/analyses/{ana_id}/snapshots",
        json=snap_payload,
        headers=auth_a,
    )
    assert snap_create_res.status_code == 201
    snap_data = ResponseEnvelope[SnapshotResponse].model_validate(snap_create_res.json()).data
    assert snap_data is not None
    assert snap_data.name == "Q4-2026 Snapshot"
    assert snap_data.saved_analysis_id == ana_id

    # List Snapshots
    snap_list_res = client.get(
        f"/api/v1/projects/{proj_id}/analyses/{ana_id}/snapshots",
        headers=auth_a,
    )
    assert snap_list_res.status_code == 200
    assert len(snap_list_res.json()["data"]) == 1

    # 8. Cleanup & Deletes
    del_ana_res = client.delete(f"/api/v1/projects/{proj_id}/analyses/{ana_id}", headers=auth_a)
    assert del_ana_res.status_code == 204

    del_game_res = client.delete(
        f"/api/v1/projects/{proj_id}/games/{game1_id}",
        headers=auth_a,
    )
    assert del_game_res.status_code == 204

    del_proj_res = client.delete(f"/api/v1/projects/{proj_id}", headers=auth_a)
    assert del_proj_res.status_code == 204

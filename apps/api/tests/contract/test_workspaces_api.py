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


def test_workspace_members_and_role_permissions(
    client: TestClient, sample_catalog: dict[str, Any]
) -> None:
    token_owner = _register_and_login(client, "owner.perm@example.com", "ProjectOwner")
    token_editor = _register_and_login(client, "editor.perm@example.com", "ProjectEditor")
    token_viewer = _register_and_login(client, "viewer.perm@example.com", "ProjectViewer")
    token_outsider = _register_and_login(client, "outsider.perm@example.com", "Outsider")

    auth_owner = {"Authorization": f"Bearer {token_owner}"}
    auth_editor = {"Authorization": f"Bearer {token_editor}"}
    auth_viewer = {"Authorization": f"Bearer {token_viewer}"}
    auth_outsider = {"Authorization": f"Bearer {token_outsider}"}

    game1_id = sample_catalog["game1"].id

    # 1. Owner creates private project
    proj_res = client.post(
        "/api/v1/projects",
        json={"name": "Multi-Role Study", "visibility": "private"},
        headers=auth_owner,
    )
    assert proj_res.status_code == 201
    proj_id = proj_res.json()["data"]["id"]

    # 2. Owner invites Editor and Viewer
    add_editor_res = client.post(
        f"/api/v1/projects/{proj_id}/members",
        json={"email": "editor.perm@example.com", "project_role": "editor"},
        headers=auth_owner,
    )
    assert add_editor_res.status_code == 201
    assert add_editor_res.json()["data"]["project_role"] == "editor"

    add_viewer_res = client.post(
        f"/api/v1/projects/{proj_id}/members",
        json={"email": "viewer.perm@example.com", "project_role": "viewer"},
        headers=auth_owner,
    )
    assert add_viewer_res.status_code == 201
    assert add_viewer_res.json()["data"]["project_role"] == "viewer"

    # List members
    members_res = client.get(f"/api/v1/projects/{proj_id}/members", headers=auth_owner)
    assert members_res.status_code == 200
    roles = {m["email"]: m["project_role"] for m in members_res.json()["data"]}
    assert roles.get("owner.perm@example.com") == "owner"
    assert roles.get("editor.perm@example.com") == "editor"
    assert roles.get("viewer.perm@example.com") == "viewer"

    # 3. Editor permissions:
    # Editor CAN add game
    editor_add_game = client.post(
        f"/api/v1/projects/{proj_id}/games",
        json={"game_id": str(game1_id)},
        headers=auth_editor,
    )
    assert editor_add_game.status_code == 200

    # Editor CAN create saved analysis
    editor_create_ana = client.post(
        f"/api/v1/projects/{proj_id}/analyses",
        json={
            "name": "Editor Saved Query",
            "analysis_type": "review_explorer",
            "query_config": {"aspect": "gameplay"},
        },
        headers=auth_editor,
    )
    assert editor_create_ana.status_code == 201
    ana_id = editor_create_ana.json()["data"]["id"]

    # Editor CANNOT invite other members (403 Forbidden)
    editor_invite_fail = client.post(
        f"/api/v1/projects/{proj_id}/members",
        json={"email": "outsider.perm@example.com", "project_role": "viewer"},
        headers=auth_editor,
    )
    assert editor_invite_fail.status_code == 403

    # Editor CANNOT delete project (403 Forbidden)
    editor_del_fail = client.delete(f"/api/v1/projects/{proj_id}", headers=auth_editor)
    assert editor_del_fail.status_code == 403

    # 4. Viewer permissions:
    # Viewer CAN read project and list games
    viewer_get_proj = client.get(f"/api/v1/projects/{proj_id}", headers=auth_viewer)
    assert viewer_get_proj.status_code == 200
    assert viewer_get_proj.json()["data"]["current_user_role"] == "viewer"

    viewer_list_games = client.get(f"/api/v1/projects/{proj_id}/games", headers=auth_viewer)
    assert viewer_list_games.status_code == 200
    assert len(viewer_list_games.json()["data"]) == 1

    # Viewer CAN read saved analysis
    viewer_get_ana = client.get(
        f"/api/v1/projects/{proj_id}/analyses/{ana_id}", headers=auth_viewer
    )
    assert viewer_get_ana.status_code == 200

    # Viewer CANNOT modify project (403 Forbidden)
    viewer_patch_fail = client.patch(
        f"/api/v1/projects/{proj_id}",
        json={"name": "Viewer Hacked Title"},
        headers=auth_viewer,
    )
    assert viewer_patch_fail.status_code == 403

    # Viewer CANNOT add game (403 Forbidden)
    viewer_add_game_fail = client.post(
        f"/api/v1/projects/{proj_id}/games",
        json={"game_id": str(game1_id)},
        headers=auth_viewer,
    )
    assert viewer_add_game_fail.status_code == 403

    # Viewer CANNOT create saved analysis (403 Forbidden)
    viewer_ana_fail = client.post(
        f"/api/v1/projects/{proj_id}/analyses",
        json={"name": "Viewer Query", "analysis_type": "review_explorer", "query_config": {}},
        headers=auth_viewer,
    )
    assert viewer_ana_fail.status_code == 403

    # 5. Outsider (non-member) cannot access private project (404 ProjectNotFoundError)
    outsider_get = client.get(f"/api/v1/projects/{proj_id}", headers=auth_outsider)
    assert outsider_get.status_code == 404

    # 6. Revoke viewer access
    remove_viewer_res = client.delete(
        f"/api/v1/projects/{proj_id}/members/{viewer_get_proj.json()['data']['owner_user_id']}",
        headers=auth_editor,
    )
    # Editor cannot remove member (403)
    assert remove_viewer_res.status_code == 403

    # Owner removes Viewer
    user_viewer_id = next(
        m["user_id"] for m in members_res.json()["data"] if m["project_role"] == "viewer"
    )
    owner_removes_viewer = client.delete(
        f"/api/v1/projects/{proj_id}/members/{user_viewer_id}",
        headers=auth_owner,
    )
    assert owner_removes_viewer.status_code == 204

    # Now former viewer gets 404
    assert client.get(f"/api/v1/projects/{proj_id}", headers=auth_viewer).status_code == 404


def test_workspace_unauthenticated_and_uuid_manipulation(client: TestClient) -> None:
    # 1. Unauthenticated requests return 401
    assert client.get("/api/v1/projects").status_code == 401
    assert client.post("/api/v1/projects", json={"name": "Test"}).status_code == 401

    # 2. Random nonexistent UUID returns 404
    token = _register_and_login(client, "rando@example.com", "Rando")
    headers = {"Authorization": f"Bearer {token}"}
    fake_uuid = "00000000-0000-0000-0000-000000000000"
    assert client.get(f"/api/v1/projects/{fake_uuid}", headers=headers).status_code == 404

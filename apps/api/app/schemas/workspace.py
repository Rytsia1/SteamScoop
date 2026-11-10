"""Schemas for research workspaces, projects, saved analyses, and snapshots."""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field


class ProjectCreateRequest(BaseModel):
    """Payload for POST /projects."""

    name: str = Field(min_length=1, max_length=160)
    description: str | None = Field(default=None, max_length=2000)
    visibility: Literal["private", "shared"] = "private"


class ProjectUpdateRequest(BaseModel):
    """Payload for PATCH /projects/{project_id}."""

    name: str | None = Field(default=None, min_length=1, max_length=160)
    description: str | None = Field(default=None, max_length=2000)
    visibility: Literal["private", "shared"] | None = None


class ProjectResponse(BaseModel):
    """Research project representation."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    owner_user_id: uuid.UUID
    name: str
    description: str | None
    visibility: str
    status: str
    created_at: datetime
    updated_at: datetime


class ProjectGameItem(BaseModel):
    """Associated game in a research project."""

    project_id: uuid.UUID
    game_id: uuid.UUID
    added_at: datetime


class ProjectAddGameRequest(BaseModel):
    """Payload for POST /projects/{project_id}/games."""

    game_id: uuid.UUID


class SavedAnalysisCreateRequest(BaseModel):
    """Payload for POST /projects/{project_id}/analyses."""

    name: str = Field(min_length=1, max_length=160)
    description: str | None = None
    analysis_type: str = Field(description="review_explorer, comparison, or trend")
    query_config: dict[str, Any] = Field(description="Allowlisted structured query parameters")


class SavedAnalysisUpdateRequest(BaseModel):
    """Payload for PATCH /projects/{project_id}/analyses/{analysis_id}."""

    name: str | None = None
    description: str | None = None
    query_config: dict[str, Any] | None = None


class SavedAnalysisResponse(BaseModel):
    """Saved analysis configuration representation."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    project_id: uuid.UUID
    name: str
    description: str | None
    analysis_type: str
    query_config: dict[str, Any]
    created_at: datetime
    updated_at: datetime


class SnapshotCreateRequest(BaseModel):
    """Payload for POST /projects/{project_id}/analyses/{analysis_id}/snapshots."""

    name: str = Field(min_length=1, max_length=160)
    description: str | None = None


class SnapshotResponse(BaseModel):
    """Immutable reproducibility snapshot representation."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    saved_analysis_id: uuid.UUID
    name: str
    description: str | None
    configuration_snapshot: dict[str, Any]
    result_summary: dict[str, Any]
    data_cutoff_at: datetime
    created_at: datetime


# Alias for compatibility
AnalysisSnapshotResponse = SnapshotResponse
AnalysisSnapshotCreateRequest = SnapshotCreateRequest

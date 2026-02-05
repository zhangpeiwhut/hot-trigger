from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class ContentType(str, Enum):
    text = "text"
    image = "image"
    video = "video"
    mixed = "mixed"


class ContentUnit(BaseModel):
    unit_id: str
    title: str
    url: str | None = None
    rank: int | None = None
    heat_score: float | None = None
    content_type: ContentType = ContentType.text
    text_payload: str | None = None
    media_payload: dict[str, Any] | None = None
    author: str | None = None
    tags: list[str] = Field(default_factory=list)
    raw: dict[str, Any] = Field(default_factory=dict)


class TrendSnapshot(BaseModel):
    timestamp: datetime
    platform_id: str
    units: list[ContentUnit]


class TriggerEvent(BaseModel):
    event_id: str
    trigger_id: str
    platform_id: str
    unit_id: str
    occurred_at: datetime
    delta: dict[str, Any] = Field(default_factory=dict)
    unit: ContentUnit


class AnalysisArtifact(BaseModel):
    event_id: str
    summary: str
    why_trending: str
    angles: list[str]
    audience: str
    risk_flags: list[str]
    participation_modes: list[str]
    model: str


class DecisionVerdict(str, Enum):
    go = "GO"
    wait = "WAIT"
    no = "NO"


class ScoreBreakdown(BaseModel):
    domain_relevance: int
    differentiation_space: int
    participation_cost: int
    risk_compliance: int
    timeliness: int


class DecisionArtifact(BaseModel):
    event_id: str
    ride_score: int
    verdict: DecisionVerdict
    score_breakdown: ScoreBreakdown
    rationale: list[str]
    suggested_comment: str
    suggested_post_outline: list[str]

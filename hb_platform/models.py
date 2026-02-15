"""Pydantic models for the platform API."""
from __future__ import annotations

from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field


# ── Citizens ───────────────────────────────────────

class CitizenCreate(BaseModel):
    alias: str
    wallet_address: Optional[str] = None
    github_username: Optional[str] = None

class Citizen(BaseModel):
    id: str
    alias: str
    wallet_address: Optional[str] = None
    github_username: Optional[str] = None
    tier: str = "visitor"
    joined_at: str
    total_earned: float = 0.0


# ── Auth ───────────────────────────────────────────

class TokenRequest(BaseModel):
    citizen_id: str
    secret: str

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


# ── Forum ──────────────────────────────────────────

class ForumTopic(BaseModel):
    id: int
    name: str
    guild_id: Optional[str] = None
    created_at: str

class ThreadCreate(BaseModel):
    title: str
    body: str

class ForumThread(BaseModel):
    id: int
    topic_id: int
    title: str
    author_id: str
    created_at: str
    pinned: bool = False
    locked: bool = False
    post_count: int = 0

class PostCreate(BaseModel):
    body: str

class ForumPost(BaseModel):
    id: int
    thread_id: int
    author_id: str
    body: str
    created_at: str
    edited_at: Optional[str] = None
    is_agent: bool = False


# ── Briefs ─────────────────────────────────────────

class BriefCreate(BaseModel):
    title: str
    description: str
    lab: Optional[str] = None
    reward_tier: Optional[int] = None
    deadline: Optional[str] = None

class Brief(BaseModel):
    id: str
    title: str
    description: str
    lab: Optional[str] = None
    status: str = "open"
    claimed_by: Optional[str] = None
    reward_tier: Optional[int] = None
    created_at: str
    deadline: Optional[str] = None


# ── Submissions ────────────────────────────────────

class SubmissionCreate(BaseModel):
    brief_id: Optional[str] = None

class Submission(BaseModel):
    id: int
    brief_id: Optional[str] = None
    citizen_id: str
    artifact_hash: str
    status: str = "queued"
    submitted_at: str
    verdict_at: Optional[str] = None
    tier_reached: Optional[str] = None


# ── Agent Messages ─────────────────────────────────

class AgentMessage(BaseModel):
    id: int
    from_agent: str
    to_agent: str
    message_type: str
    payload: str            # JSON string
    priority: str = "normal"
    status: str = "pending"
    created_at: str
    processed_at: Optional[str] = None

class AgentMessageCreate(BaseModel):
    to_agent: str
    message_type: str
    payload: str
    priority: str = "normal"


# ── Dashboard ──────────────────────────────────────

class DashboardStats(BaseModel):
    survived: int = 0
    culled: int = 0
    queued: int = 0
    active_briefs: int = 0
    total_citizens: int = 0
    agents_online: int = 0

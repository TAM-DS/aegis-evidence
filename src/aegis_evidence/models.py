from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field


RiskTier = Literal[
    "prohibited",
    "high-risk-adjacent",
    "limited",
    "minimal",
    "insufficient-information",
]

ControlStatus = Literal["missing", "partial", "attested", "verified"]


class Control(BaseModel):
    id: str
    title: str
    theme: str
    nist: list[str] = Field(default_factory=list)
    iso42001: list[str] = Field(default_factory=list)
    eu_ai_act: list[str] = Field(default_factory=list)
    evidence_required: list[str] = Field(default_factory=list)
    status_rule: str


class Catalog(BaseModel):
    version: str
    name: str
    scope: str
    controls: list[Control]


class SystemRecord(BaseModel):
    system_id: str
    name: str
    version: str
    environment: str
    role: str
    owner: str
    approver_role: str
    intended_purpose: str
    out_of_scope: list[str] = Field(default_factory=list)
    autonomy: str
    data_classes: list[str] = Field(default_factory=list)
    tools: list[str] = Field(default_factory=list)
    capabilities: dict[str, Any] = Field(default_factory=dict)
    notes: str = ""


class Classification(BaseModel):
    tier: RiskTier
    rationale: list[str]
    missing_facts: list[str] = Field(default_factory=list)


class ControlEvaluation(BaseModel):
    control_id: str
    title: str
    theme: str
    nist: list[str]
    iso42001: list[str]
    eu_ai_act: list[str]
    status: ControlStatus
    gap: str
    evidence_refs: list[str] = Field(default_factory=list)
    proposed_by: str = "rule-engine"
    accepted: bool = False
    acceptor: str = ""


class RiskRow(BaseModel):
    risk_id: str
    risk: str
    related_controls: list[str]
    likelihood: str
    impact: str
    residual: str
    owner: str
    status: str


class PackManifest(BaseModel):
    catalog_version: str
    catalog_digest: str
    system_digest: str
    classification_digest: str
    evaluations_digest: str
    pack_digest: str
    accepted_count: int
    gap_count: int

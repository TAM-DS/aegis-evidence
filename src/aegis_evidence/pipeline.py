from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from .catalog import load_catalog, load_system
from .classify import classify
from .evaluate import evaluate_catalog
from .models import Catalog, Classification, ControlEvaluation, PackManifest, RiskRow, SystemRecord
from .pack import build_manifest, write_pack
from .risk_register import build_register


@dataclass
class RunResult:
    catalog: Catalog
    catalog_digest: str
    system: SystemRecord
    classification: Classification
    evaluations: list[ControlEvaluation]
    risks: list[RiskRow]
    manifest: PackManifest


def run_pipeline(catalog_path: Path, system_path: Path) -> RunResult:
    catalog, catalog_digest = load_catalog(catalog_path)
    system = load_system(system_path)
    classification = classify(system)
    evaluations = evaluate_catalog(catalog, system)
    if classification.tier != "insufficient-information":
        for row in evaluations:
            if row.control_id == "C-TIER-01":
                row.status = "partial"
                row.gap = f"Proposed tier `{classification.tier}` awaits human acceptance."
    else:
        for row in evaluations:
            if row.control_id == "C-TIER-01":
                row.status = "missing"
                row.gap = "Insufficient information to classify."
    risks = build_register(system, classification, evaluations)
    manifest = build_manifest(catalog, catalog_digest, system, classification, evaluations)
    return RunResult(
        catalog=catalog,
        catalog_digest=catalog_digest,
        system=system,
        classification=classification,
        evaluations=evaluations,
        risks=risks,
        manifest=manifest,
    )


def accept_all_attested(result: RunResult, acceptor: str) -> RunResult:
    for row in result.evaluations:
        if row.status in {"attested", "verified"}:
            row.accepted = True
            row.acceptor = acceptor
    result.manifest = build_manifest(
        result.catalog,
        result.catalog_digest,
        result.system,
        result.classification,
        result.evaluations,
    )
    result.risks = build_register(result.system, result.classification, result.evaluations)
    return result


def freeze_pack(result: RunResult, dest: Path) -> PackManifest:
    return write_pack(
        dest,
        result.catalog,
        result.catalog_digest,
        result.system,
        result.classification,
        result.evaluations,
        result.risks,
    )

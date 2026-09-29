from pathlib import Path
import json
import zipfile

import pytest

import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from aegis_evidence.digest import sha256_hex
from aegis_evidence.pipeline import accept_all_attested, freeze_pack, run_pipeline

CATALOG = ROOT / "catalog" / "controls.v0.3.yaml"
FIXTURE = ROOT / "fixtures" / "aegis_analyst_system.yaml"


def test_replay_same_digests(tmp_path: Path) -> None:
    a = run_pipeline(CATALOG, FIXTURE)
    b = run_pipeline(CATALOG, FIXTURE)
    assert a.classification.tier == "high-risk-adjacent"
    assert a.manifest.pack_digest == b.manifest.pack_digest
    assert a.manifest.catalog_digest == b.manifest.catalog_digest
    assert a.manifest.system_digest == b.manifest.system_digest


def test_aegis_fixture_has_expected_gap() -> None:
    result = run_pipeline(CATALOG, FIXTURE)
    mon = next(e for e in result.evaluations if e.control_id == "C-MON-01")
    assert mon.status == "partial"
    over = next(e for e in result.evaluations if e.control_id == "C-OVER-01")
    assert over.status == "attested"
    assert result.manifest.gap_count >= 1


def test_insufficient_information_without_purpose(tmp_path: Path) -> None:
    broken = tmp_path / "sys.yaml"
    broken.write_text(
        """
system_id: x
name: x
version: "1"
environment: demo
role: deployer
owner: ""
approver_role: ""
intended_purpose: ""
out_of_scope: []
autonomy: propose-and-wait
data_classes: []
tools: []
capabilities: {}
notes: ""
""",
        encoding="utf-8",
    )
    result = run_pipeline(CATALOG, broken)
    assert result.classification.tier == "insufficient-information"


def test_pack_writes(tmp_path: Path) -> None:
    result = run_pipeline(CATALOG, FIXTURE)
    dest = tmp_path / "pack.zip"
    manifest = freeze_pack(result, dest)
    assert dest.exists()
    assert len(manifest.pack_digest) == 64


def test_archives_are_byte_identical_for_the_same_evidence_state(tmp_path: Path) -> None:
    result = run_pipeline(CATALOG, FIXTURE)
    one, two = tmp_path / "one.zip", tmp_path / "two.zip"
    freeze_pack(result, one)
    freeze_pack(result, two)
    assert one.read_bytes() == two.read_bytes()
    assert sha256_hex(one.read_bytes()) == sha256_hex(two.read_bytes())
    with zipfile.ZipFile(one) as archive:
        for row in archive.read("hashes.txt").decode().splitlines():
            expected_sha, name = row.split("  ", 1)
            assert sha256_hex(archive.read(name)) == expected_sha


def test_acceptance_changes_archive_but_not_proposed_decision_digest(tmp_path: Path) -> None:
    result = run_pipeline(CATALOG, FIXTURE)
    unaccepted = tmp_path / "unaccepted.zip"
    freeze_pack(result, unaccepted)
    decision_digest = result.manifest.pack_digest
    accepted_result = accept_all_attested(result, "SOC Lead")
    assert accepted_result.manifest.pack_digest == decision_digest
    assert accepted_result.manifest.accepted_count > 0
    classification = next(e for e in accepted_result.evaluations if e.control_id == "C-TIER-01")
    monitoring = next(e for e in accepted_result.evaluations if e.control_id == "C-MON-01")
    assert classification.status == "partial" and not classification.accepted
    assert monitoring.status == "partial" and not monitoring.accepted
    accepted = tmp_path / "accepted.zip"
    freeze_pack(accepted_result, accepted)
    assert sha256_hex(unaccepted.read_bytes()) != sha256_hex(accepted.read_bytes())
    with zipfile.ZipFile(accepted) as archive:
        manifest = json.loads(archive.read("manifest.json"))
        rows = json.loads(archive.read("crosswalk.json"))
        assert manifest["pack_digest"] == decision_digest
        assert manifest["accepted_count"] > 0
        assert all(r["acceptor"] == "SOC Lead" for r in rows if r["accepted"])
        assert all(not r["accepted"] for r in rows if r["status"] in {"partial", "missing"})


def test_acceptance_requires_a_named_operator() -> None:
    result = run_pipeline(CATALOG, FIXTURE)
    with pytest.raises(ValueError, match="non-empty acceptor"):
        accept_all_attested(result, "  ")


def test_monitoring_gap_matches_deployer_role_and_actual_audit_capability() -> None:
    result = run_pipeline(CATALOG, FIXTURE)
    assert result.system.role == "deployer"
    assert not result.system.capabilities.get("metrics_endpoint")
    assert result.system.capabilities.get("audit_log")
    monitoring = next(e for e in result.evaluations if e.control_id == "C-MON-01")
    assert monitoring.eu_ai_act == ["Art. 26(5)"]
    assert monitoring.status == "partial"
    assert "audit trail" in monitoring.gap
    assert next(r for r in result.risks if r.risk_id == "R-MON").status == "open"

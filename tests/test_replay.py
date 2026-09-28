from pathlib import Path

import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from aegis_evidence.pipeline import freeze_pack, run_pipeline

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

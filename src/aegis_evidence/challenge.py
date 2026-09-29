from __future__ import annotations

from .models import Classification, ControlEvaluation, SystemRecord


def challenge(
    system: SystemRecord,
    classification: Classification,
    evaluations: list[ControlEvaluation],
) -> list[str]:
    """Deterministic challenge agent: flags over-claims. Does not change status."""
    findings: list[str] = []
    if classification.tier == "high-risk-adjacent":
        findings.append(
            "Challenge: `high-risk-adjacent` is diligence language, not an EU AI Act Annex III determination."
        )
    if system.capabilities.get("production_edr"):
        findings.append("Challenge: production EDR is claimed. Require a verified execution artifact.")
    if any(e.control_id == "C-MON-01" and e.status == "partial" for e in evaluations):
        findings.append(
            "Challenge: an audit trail is not a deployer operational monitoring procedure (Art. 26(5) / ISO 9.1)."
        )
    if not system.out_of_scope:
        findings.append("Challenge: no exclusions listed; purpose may be unbounded.")
    isolate = any("isolate" in t for t in system.tools)
    gate = system.capabilities.get("approval_gate")
    if isolate and not gate:
        findings.append("Challenge: isolate tool exists without an approval gate.")
    accepted_missing = [e.control_id for e in evaluations if e.accepted and e.status == "missing"]
    if accepted_missing:
        findings.append(
            "Challenge: accepted controls still marked missing: " + ", ".join(accepted_missing)
        )
    if not findings:
        findings.append("Challenge agent found no additional exceptions beyond the rule engine.")
    return findings

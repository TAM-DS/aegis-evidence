from __future__ import annotations

from .models import Classification, SystemRecord


def classify(system: SystemRecord) -> Classification:
    missing: list[str] = []
    rationale: list[str] = []

    purpose = (system.intended_purpose or "").strip()
    if not purpose:
        missing.append("intended_purpose")
    if not system.owner.strip():
        missing.append("owner")
    if not system.role.strip():
        missing.append("role")
    if not system.data_classes:
        missing.append("data_classes")

    if missing:
        return Classification(
            tier="insufficient-information",
            rationale=["Classification refused until required intake fields exist."],
            missing_facts=missing,
        )

    rationale.append(f"Role recorded as {system.role}.")
    rationale.append(f"Autonomy recorded as {system.autonomy}.")

    disruptive = any("isolate" in t or "contain" in t for t in system.tools)
    security_ops = "soc" in system.name.lower() or "alert" in purpose.lower() or "security" in purpose.lower()

    if disruptive and security_ops:
        rationale.append(
            "System proposes disruptive response (host isolation) in a security-operations context."
        )
        rationale.append(
            "Treated as high-risk-adjacent for deployer diligence: not an Annex III legal determination."
        )
        return Classification(
            tier="high-risk-adjacent",
            rationale=rationale,
            missing_facts=[],
        )

    if system.autonomy in {"autonomous", "execute-without-approval"}:
        rationale.append("Autonomy level exceeds propose-and-wait.")
        return Classification(tier="high-risk-adjacent", rationale=rationale)

    rationale.append("No disruptive tools and bounded purpose; limited-risk transparency posture.")
    return Classification(tier="limited", rationale=rationale)

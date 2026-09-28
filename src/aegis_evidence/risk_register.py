from __future__ import annotations

from .models import Classification, ControlEvaluation, RiskRow, SystemRecord


def build_register(
    system: SystemRecord,
    classification: Classification,
    evaluations: list[ControlEvaluation],
) -> list[RiskRow]:
    by_id = {e.control_id: e for e in evaluations}
    rows: list[RiskRow] = []

    def add(risk_id: str, text: str, controls: list[str], likelihood: str, impact: str) -> None:
        open_gaps = [c for c in controls if by_id.get(c) and by_id[c].status in {"missing", "partial"}]
        residual = "high" if open_gaps and impact == "high" else ("medium" if open_gaps else "low")
        rows.append(
            RiskRow(
                risk_id=risk_id,
                risk=text,
                related_controls=controls,
                likelihood=likelihood,
                impact=impact,
                residual=residual,
                owner=system.owner or "unassigned",
                status="open" if open_gaps else "accepted-with-controls",
            )
        )

    if classification.tier == "insufficient-information":
        add("R-INTAKE", "System cannot be classified; intake incomplete.", ["C-PUR-01", "C-INV-01"], "high", "high")

    add(
        "R-AUTH",
        "Recommendation treated as authorization for host isolation.",
        ["C-OVER-01", "C-POL-01", "C-EXEC-01"],
        "medium",
        "high",
    )
    add(
        "R-SIM",
        "Simulated containment reported as completed isolation.",
        ["C-SIM-01", "C-SCOPE-01"],
        "medium",
        "high",
    )
    add(
        "R-MON",
        "No post-use monitoring program for the analyst agent.",
        ["C-MON-01"],
        "medium",
        "medium",
    )
    add(
        "R-AUD",
        "Investigation decisions cannot be reconstructed.",
        ["C-AUD-01", "C-TEST-01"],
        "low",
        "medium",
    )
    return rows

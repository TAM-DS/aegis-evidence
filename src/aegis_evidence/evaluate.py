from __future__ import annotations

from .models import Catalog, ControlEvaluation, SystemRecord


def _cap(system: SystemRecord, key: str) -> bool:
    return bool(system.capabilities.get(key))


def evaluate_control(rule: str, system: SystemRecord) -> tuple[str, str]:
    purpose_ok = bool(system.intended_purpose.strip()) and bool(system.out_of_scope)
    record_ok = all(
        [
            system.system_id,
            system.name,
            system.version,
            system.environment,
            system.owner,
        ]
    )

    mapping = {
        "attested_if_system_record_complete": (
            "attested" if record_ok else "missing",
            "" if record_ok else "System record incomplete.",
        ),
        "attested_if_purpose_and_exclusions": (
            "attested" if purpose_ok else "missing",
            "" if purpose_ok else "Purpose or exclusions missing.",
        ),
        "attested_if_role_set": (
            "attested" if system.role else "missing",
            "" if system.role else "Role not set.",
        ),
        "attested_if_owner": (
            "attested" if system.owner and system.approver_role else "missing",
            "" if system.owner and system.approver_role else "Owner or approver role missing.",
        ),
        "attested_if_tier_not_insufficient": (
            "partial",
            "Tier is computed; human must accept classification.",
        ),
        "attested_if_data_classes": (
            "attested" if system.data_classes else "missing",
            "" if system.data_classes else "No data classes listed.",
        ),
        "attested_if_approval_gate": (
            "attested" if _cap(system, "approval_gate") else "missing",
            "" if _cap(system, "approval_gate") else "No approval gate declared.",
        ),
        "attested_if_policy_engine": (
            "attested" if _cap(system, "policy_engine_separate") else "missing",
            "" if _cap(system, "policy_engine_separate") else "Policy is not declared separate from the model.",
        ),
        "attested_if_sandbox": (
            "attested" if _cap(system, "allowlisted_sandbox") else "missing",
            "" if _cap(system, "allowlisted_sandbox") else "No allowlisted sandbox declared.",
        ),
        "attested_if_simulation_honest": (
            "attested" if _cap(system, "simulation_honest") else "missing",
            "" if _cap(system, "simulation_honest") else "Simulation honesty not declared.",
        ),
        "attested_if_audit_log": (
            "attested" if _cap(system, "audit_log") else "missing",
            "" if _cap(system, "audit_log") else "No audit log declared.",
        ),
        "attested_if_governance_tests": (
            "attested" if _cap(system, "governance_tests") else "missing",
            "" if _cap(system, "governance_tests") else "No governance tests declared.",
        ),
        "attested_if_scope_honest": (
            "attested"
            if (not _cap(system, "production_edr") or "Real EDR" in " ".join(system.out_of_scope))
            else "missing",
            ""
            if (not _cap(system, "production_edr"))
            else "Production EDR claimed without verification artifact.",
        ),
        "attested_if_exception_path": (
            "attested" if _cap(system, "exception_path") else "missing",
            "" if _cap(system, "exception_path") else "No deny/exception path declared.",
        ),
        "partial_if_audit_only": (
            "partial"
            if _cap(system, "audit_log") and not _cap(system, "operational_monitoring_procedure")
            else ("attested" if _cap(system, "operational_monitoring_procedure") else "missing"),
            "An audit trail exists; no documented deployer operational monitoring procedure."
            if _cap(system, "audit_log") and not _cap(system, "operational_monitoring_procedure")
            else ("" if _cap(system, "operational_monitoring_procedure") else "No deployer operational monitoring procedure declared."),
        ),
    }
    return mapping.get(rule, ("missing", f"Unknown rule {rule}"))


def evaluate_catalog(catalog: Catalog, system: SystemRecord) -> list[ControlEvaluation]:
    rows: list[ControlEvaluation] = []
    for control in catalog.controls:
        status, gap = evaluate_control(control.status_rule, system)
        refs = [
            f"system:{system.system_id}@{system.version}",
            f"catalog:{catalog.version}/{control.id}",
        ]
        rows.append(
            ControlEvaluation(
                control_id=control.id,
                title=control.title,
                theme=control.theme,
                nist=control.nist,
                iso42001=control.iso42001,
                eu_ai_act=control.eu_ai_act,
                status=status,  # type: ignore[arg-type]
                gap=gap,
                evidence_refs=refs,
                proposed_by="rule-engine",
                accepted=False,
            )
        )
    return rows

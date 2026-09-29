from __future__ import annotations

import csv
import io
import zipfile
from pathlib import Path

from .digest import canonical_dumps, digest_obj, sha256_hex
from .models import (
    Catalog,
    Classification,
    ControlEvaluation,
    PackManifest,
    RiskRow,
    SystemRecord,
)


def evaluations_for_digest(rows: list[ControlEvaluation]) -> list[dict]:
    payload = []
    for row in rows:
        d = row.model_dump()
        d.pop("accepted", None)
        d.pop("acceptor", None)
        payload.append(d)
    return payload


def build_manifest(
    catalog: Catalog,
    catalog_digest: str,
    system: SystemRecord,
    classification: Classification,
    evaluations: list[ControlEvaluation],
) -> PackManifest:
    system_digest = digest_obj(system.model_dump())
    classification_digest = digest_obj(classification.model_dump())
    evaluations_digest = digest_obj(evaluations_for_digest(evaluations))
    body = {
        "catalog_version": catalog.version,
        "catalog_digest": catalog_digest,
        "system_digest": system_digest,
        "classification_digest": classification_digest,
        "evaluations_digest": evaluations_digest,
    }
    pack_digest = digest_obj(body)
    return PackManifest(
        **body,
        pack_digest=pack_digest,
        accepted_count=sum(1 for e in evaluations if e.accepted),
        gap_count=sum(1 for e in evaluations if e.status in {"missing", "partial"}),
    )


def dossier_markdown(
    system: SystemRecord,
    classification: Classification,
    evaluations: list[ControlEvaluation],
    manifest: PackManifest,
) -> str:
    gaps = [e for e in evaluations if e.status in {"missing", "partial"}]
    lines = [
        f"# System dossier — {system.name}",
        "",
        f"- **System ID:** {system.system_id}",
        f"- **Version:** {system.version}",
        f"- **Environment:** {system.environment}",
        f"- **Role:** {system.role}",
        f"- **Owner:** {system.owner}",
        f"- **Approver role:** {system.approver_role}",
        f"- **Autonomy:** {system.autonomy}",
        f"- **Classification:** {classification.tier}",
        f"- **Catalog:** {manifest.catalog_version}",
        f"- **Pack digest:** `{manifest.pack_digest}`",
        f"- **System digest:** `{manifest.system_digest}`",
        "",
        "## Intended purpose",
        system.intended_purpose.strip(),
        "",
        "## Out of scope",
    ]
    lines.extend(f"- {item}" for item in system.out_of_scope)
    lines += ["", "## Classification rationale"]
    lines.extend(f"- {r}" for r in classification.rationale)
    if classification.missing_facts:
        lines += ["", "## Missing facts"]
        lines.extend(f"- {m}" for m in classification.missing_facts)
    lines += ["", f"## Gaps ({len(gaps)})"]
    if not gaps:
        lines.append("- None.")
    for g in gaps:
        lines.append(f"- **{g.control_id}** {g.title} — `{g.status}` {g.gap}".rstrip())
    lines += ["", "## Attestation"]
    lines.append(
        "This dossier is generated from a frozen catalog and system record. "
        "Control *status* is rule-derived. Acceptance is a separate human act "
        "and is not required for replay of classification."
    )
    return "\n".join(lines) + "\n"


def risk_register_csv(rows: list[RiskRow]) -> str:
    buf = io.StringIO()
    writer = csv.writer(buf)
    writer.writerow(
        ["risk_id", "risk", "related_controls", "likelihood", "impact", "residual", "owner", "status"]
    )
    for r in rows:
        writer.writerow(
            [
                r.risk_id,
                r.risk,
                "|".join(r.related_controls),
                r.likelihood,
                r.impact,
                r.residual,
                r.owner,
                r.status,
            ]
        )
    return buf.getvalue()


def write_pack(
    dest_zip: Path,
    catalog: Catalog,
    catalog_digest: str,
    system: SystemRecord,
    classification: Classification,
    evaluations: list[ControlEvaluation],
    risks: list[RiskRow],
) -> PackManifest:
    manifest = build_manifest(catalog, catalog_digest, system, classification, evaluations)
    dest_zip.parent.mkdir(parents=True, exist_ok=True)
    files = {
        "manifest.json": canonical_dumps(manifest.model_dump()),
        "system.json": canonical_dumps(system.model_dump()),
        "classification.json": canonical_dumps(classification.model_dump()),
        "crosswalk.json": canonical_dumps([e.model_dump() for e in evaluations]),
        "risk_register.json": canonical_dumps([r.model_dump() for r in risks]),
        "risk_register.csv": risk_register_csv(risks),
        "dossier.md": dossier_markdown(system, classification, evaluations, manifest),
        "hashes.txt": "",
    }
    hash_lines = []
    for name, content in files.items():
        if name == "hashes.txt":
            continue
        hash_lines.append(f"{sha256_hex(content)}  {name}")
    files["hashes.txt"] = "\n".join(hash_lines) + "\n"
    # Fix ZIP metadata so identical decision + acceptance state produces
    # identical archive bytes and therefore an independently verifiable checksum.
    with zipfile.ZipFile(dest_zip, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        for name, content in files.items():
            entry = zipfile.ZipInfo(name, date_time=(1980, 1, 1, 0, 0, 0))
            entry.compress_type = zipfile.ZIP_DEFLATED
            entry.create_system = 3
            entry.external_attr = 0o644 << 16
            zf.writestr(entry, content)
    return manifest

from __future__ import annotations

from pathlib import Path
import sys

import streamlit as st

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "src"))

from aegis_evidence.challenge import challenge
from aegis_evidence.pack import dossier_markdown, risk_register_csv
from aegis_evidence.pipeline import accept_all_attested, freeze_pack, run_pipeline

CATALOG = ROOT / "catalog" / "controls.v0.3.yaml"
FIXTURE = ROOT / "fixtures" / "aegis_analyst_system.yaml"
PACK_DIR = ROOT / "data" / "packs"

st.set_page_config(page_title="Aegis Evidence", layout="wide")
st.title("Aegis Evidence")
st.caption(
    "Companion to TAM-DS/aegis-analyst. Agents propose. Rules classify. Humans accept. Packs replay."
)

if "result" not in st.session_state:
    st.session_state.result = None
    st.session_state.pack_path = None

left, center, right = st.columns([1.1, 1.4, 1.2])

with left:
    st.subheader("1. Intake")
    st.write("Default fixture is the AEGIS SOC analyst.")
    if st.button("Run mapping", type="primary"):
        st.session_state.result = run_pipeline(CATALOG, FIXTURE)
        st.session_state.pack_path = None
    result = st.session_state.result
    if result:
        s = result.system
        st.markdown(f"**{s.name}** `{s.system_id}@{s.version}`")
        st.write(s.intended_purpose)
        st.write(f"Owner: {s.owner} · Role: {s.role} · Autonomy: {s.autonomy}")
        st.write("Tools: " + ", ".join(s.tools))

with center:
    st.subheader("2. Classification + crosswalk")
    result = st.session_state.result
    if not result:
        st.info("Run mapping to load the Aegis fixture against catalog v0.3.")
    else:
        c = result.classification
        st.markdown(f"**Tier:** `{c.tier}`")
        for r in c.rationale:
            st.write("- " + r)
        if c.missing_facts:
            st.warning("Missing: " + ", ".join(c.missing_facts))
        rows = [
            {
                "id": e.control_id,
                "title": e.title,
                "status": e.status,
                "gap": e.gap,
                "NIST": ", ".join(e.nist),
                "ISO 42001": ", ".join(e.iso42001),
                "EU AI Act": ", ".join(e.eu_ai_act),
                "accepted": e.accepted,
            }
            for e in result.evaluations
        ]
        st.dataframe(rows, use_container_width=True, hide_index=True)
        st.markdown("**Challenge agent**")
        for finding in challenge(result.system, result.classification, result.evaluations):
            st.write("• " + finding)

with right:
    st.subheader("3. Accept + freeze pack")
    result = st.session_state.result
    if result:
        acceptor = st.text_input("Acceptor name", value="SOC Lead")
        if st.button("Accept attested controls"):
            st.session_state.result = accept_all_attested(result, acceptor)
            st.success("Attested rows marked accepted. Gaps stay open.")
        if st.button("Freeze evidence pack"):
            PACK_DIR.mkdir(parents=True, exist_ok=True)
            digest = result.manifest.pack_digest[:12]
            dest = PACK_DIR / f"pack-{digest}.zip"
            manifest = freeze_pack(result, dest)
            st.session_state.pack_path = str(dest)
            st.success(f"Pack digest `{manifest.pack_digest}`")
        if st.session_state.pack_path:
            data = Path(st.session_state.pack_path).read_bytes()
            st.download_button(
                "Download evidence zip",
                data=data,
                file_name=Path(st.session_state.pack_path).name,
                mime="application/zip",
            )
        st.markdown("**Replay identifiers**")
        m = result.manifest
        st.code(
            "\n".join(
                [
                    f"catalog_version: {m.catalog_version}",
                    f"catalog_digest:  {m.catalog_digest}",
                    f"system_digest:   {m.system_digest}",
                    f"class_digest:    {m.classification_digest}",
                    f"eval_digest:     {m.evaluations_digest}",
                    f"pack_digest:     {m.pack_digest}",
                ]
            )
        )

if st.session_state.result:
    st.divider()
    d1, d2 = st.columns(2)
    with d1:
        st.subheader("Dossier")
        st.markdown(
            dossier_markdown(
                result.system,
                result.classification,
                result.evaluations,
                result.manifest,
            )
        )
    with d2:
        st.subheader("Risk register")
        st.dataframe(
            [r.model_dump() for r in result.risks],
            use_container_width=True,
            hide_index=True,
        )
        st.download_button(
            "Download risk_register.csv",
            data=risk_register_csv(result.risks),
            file_name="risk_register.csv",
            mime="text/csv",
        )

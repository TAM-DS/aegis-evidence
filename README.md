# Aegis Evidence

Companion to [TAM-DS/aegis-analyst](https://github.com/TAM-DS/aegis-analyst).

AEGIS can recommend isolating a host. This repo asks the next question: **what evidence would you hand an auditor that the analyst agent itself is governed?**

> Agents propose. Rules classify. Humans accept. Packs replay.

The product is not a 20-page generated policy. It is a frozen pack you can hash:

```
catalog v0.3 + system digest X → pack digest Y
```

Same intake + same catalog version always yields the same classification and proposed control statuses.

## See the workpaper

These are screenshots of the running console, not mockups.

**01 · Mapping** — attested controls accepted; `C-TIER-01` stays partial; challenge refuses Annex III and Art. 72.

![Mapping with gaps](docs/screenshots/01-mapping-gaps.png)

**02 · Workpaper** — dossier names both gaps; `R-MON` stays open; pack digest is on the page.

![Dossier and risk register](docs/screenshots/02-mapping-risk-register.png)

Same system as Aegis. Catalog `0.3`. Two gaps left open. Pack digest is stable.

## What you get

1. **System dossier** — one page (`dossier.md`)
2. **Crosswalk matrix** — NIST AI RMF / ISO 42001 / EU AI Act with gaps highlighted
3. **Risk register** — CSV and JSON
4. **Evidence pack** — zip of references, hashes, attestation fields (not generated policy prose)
5. **Replay** — pack digest is a function of catalog + system + proposed evaluations

## Architecture

```
Aegis system fixture
        |
        v
  catalog v0.3 (YAML)
        |
        v
  deterministic classifier
        |
        v
  rule engine (control status)
        |
        v
  challenge agent (flags over-claims, cannot change status)
        |
        v
  human accept of attested rows
        |
        v
  frozen zip + digests
```

Classification is *high-risk-adjacent* for the Aegis fixture. That is diligence language for a SOC agent that proposes host isolation. It is **not** a legal Annex III determination.

The default fixture has a real gap on purpose: metrics exist, a post-use monitoring program does not (`C-MON-01` = `partial`). A green dashboard would be a lie.

## Run in PyCharm

```bash
cd aegis-evidence
python3 -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
streamlit run app.py
```

Open http://localhost:8501

1. Click **Run mapping**
2. Read the tier, crosswalk, and challenge findings
3. Click **Accept attested controls** (gaps stay open)
4. Click **Freeze evidence pack** and download the zip
5. Confirm the pack digest is stable if you run mapping again

Tests:

```bash
python -m pytest tests/ -q
```

## Why this and not an audit copilot

A SOX-style agents-pull-evidence tool is a feature, not a product. The exception plus human-approval step is already here: the challenge agent flags over-claims; acceptance is a separate record; missing/partial rows cannot be laundered into attested by a model.

## Scope

- Deployer diligence for one governed SOC analyst agent
- Catalog of 15 controls, not the entire Act
- No LLM required
- No claim that the pack satisfies a notified-body audit

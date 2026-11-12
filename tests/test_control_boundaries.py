from pathlib import Path
import pytest
from aegis_evidence.catalog import load_catalog, load_system
from aegis_evidence.classify import classify
from aegis_evidence.evaluate import evaluate_control, evaluate_catalog
from aegis_evidence.risk_register import build_register

ROOT = Path(__file__).resolve().parents[1]

@pytest.fixture
def system():
    return load_system(ROOT / 'fixtures/aegis_analyst_system.yaml')

@pytest.mark.parametrize('value', ['false', 'true', 1, [], None, False])
def test_only_explicit_boolean_attests_capability(system, value):
    system.capabilities['approval_gate'] = value
    assert evaluate_control('attested_if_approval_gate', system)[0] == 'missing'
    system.capabilities['approval_gate'] = True
    assert evaluate_control('attested_if_approval_gate', system)[0] == 'attested'

@pytest.mark.parametrize('field', ['owner', 'role', 'intended_purpose'])
def test_blank_intake_cannot_be_classified(system, field):
    setattr(system, field, '  ')
    result = classify(system)
    assert result.tier == 'insufficient-information'
    assert field in result.missing_facts


def test_production_claim_cannot_be_attested_by_exclusion_text(system):
    system.capabilities['production_edr'] = True
    assert 'Real EDR' in ' '.join(system.out_of_scope)
    assert evaluate_control('attested_if_scope_honest', system)[0] == 'missing'


def test_unknown_rule_fails_closed(system):
    status, gap = evaluate_control('future-unrecognized-rule', system)
    assert status == 'missing' and 'Unknown rule' in gap


def test_absent_controls_remain_open_risks(system):
    risks = build_register(system, classify(system), [])
    assert all(r.status == 'open' for r in risks)
    assert next(r for r in risks if r.risk_id == 'R-AUTH').residual == 'high'


def test_declarations_never_become_verified_or_accepted(system):
    catalog, _ = load_catalog(ROOT / 'catalog/controls.v0.3.yaml')
    rows = evaluate_catalog(catalog, system)
    assert all(r.status != 'verified' and not r.accepted for r in rows)

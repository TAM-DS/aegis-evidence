from pathlib import Path
import json
import zipfile
from aegis_evidence.digest import digest_obj, sha256_hex
from aegis_evidence.pipeline import run_pipeline, freeze_pack, accept_all_attested

ROOT = Path(__file__).resolve().parents[1]

def run():
    return run_pipeline(ROOT/'catalog/controls.v0.3.yaml', ROOT/'fixtures/aegis_analyst_system.yaml')


def test_changed_system_cannot_reuse_decision_digest(tmp_path):
    before = run()
    after = run()
    after.system.owner = 'Different Owner'
    manifest = freeze_pack(after, tmp_path/'changed.zip')
    assert manifest.system_digest != before.manifest.system_digest
    assert manifest.pack_digest != before.manifest.pack_digest


def test_archive_hashes_cover_every_payload_and_detect_changed_bytes(tmp_path):
    path = tmp_path/'evidence.zip'
    freeze_pack(run(), path)
    with zipfile.ZipFile(path) as z:
        hashes = dict((name, sha) for sha, name in (l.split('  ', 1) for l in z.read('hashes.txt').decode().splitlines()))
        assert set(hashes) == set(z.namelist()) - {'hashes.txt'}
        for name, expected in hashes.items():
            assert sha256_hex(z.read(name)) == expected
            assert sha256_hex(z.read(name) + b'tampered') != expected
        system = json.loads(z.read('system.json'))
        manifest = json.loads(z.read('manifest.json'))
        assert digest_obj(system) == manifest['system_digest']


def test_acceptance_keeps_missing_controls_and_risks_visible():
    result = run()
    gaps = result.manifest.gap_count
    result = accept_all_attested(result, '  Reviewer  ')
    assert result.manifest.gap_count == gaps
    assert all(not r.accepted for r in result.evaluations if r.status in {'missing','partial'})
    assert all(r.acceptor == 'Reviewer' for r in result.evaluations if r.accepted)
    assert any(r.status == 'open' for r in result.risks)

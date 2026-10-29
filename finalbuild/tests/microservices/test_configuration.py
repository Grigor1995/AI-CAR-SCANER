import json
from pathlib import Path
import pytest
from backend.configuration.runtime import ConfigManager, ConfigurationError, classification

ROOT = Path(__file__).resolve().parents[3]

def manager(tmp_path, changes=None, env=None, preferences=None):
    (tmp_path/'config').mkdir(exist_ok=True)
    (tmp_path/'config/global_config.json').write_text(json.dumps(changes or {}))
    return ConfigManager(tmp_path, environ=env or {}, preferences=preferences)

def test_snapshot_precedence_immutability_and_preference_allowlist(tmp_path):
    m = manager(tmp_path, {'services': {'backend_port': 8010}}, {'AI_CAR_BACKEND_PORT': '8012'}, {'app.units': 'USA'})
    assert m.snapshot.services.backend_port == 8012
    assert m.snapshot.app.units == 'USA'
    with pytest.raises(Exception): m.snapshot.app.units = 'EU'
    with pytest.raises(ConfigurationError): manager(tmp_path, preferences={'ai.endpoint': 'http://evil'})

@pytest.mark.parametrize('value', [
    {'schema_version': 2}, {'app': {'timezone': 'Unknown/Nowhere'}}, {'ai': {'api_key_env': 'sk-not-an-env-ref'}},
    {'services': {'backend_port': {}}}, {'password': 'private-value'}, {'marketplace': {'payments_enabled': True}},
    {'obd': {'read_only': False}}, {'native': {'minimum_cpp': 17}},
    {'services': {'backend_port': '8012'}}, {'ai': {'endpoint': 'http://user:secret@example.com'}},
    {'services': {'vehicle_catalog': {'url': 'http://untrusted.example'}}},
])
def test_invalid_config_fails_closed_without_disclosing_input(tmp_path, value):
    with pytest.raises(ConfigurationError) as error: manager(tmp_path, value)
    assert 'private-value' not in str(error.value) and 'secret' not in str(error.value)

def test_audit_must_succeed_before_hot_reload_and_restart_fields_are_rejected(tmp_path):
    m = manager(tmp_path)
    def fail(_): raise RuntimeError('database offline')
    patch = {'services.vehicle_catalog.timeout_seconds': 4.0}
    with pytest.raises(RuntimeError): m.reload(patch, expected_revision=1, audit=fail)
    assert m.revision == 1 and m.snapshot.services.vehicle_catalog.timeout_seconds == 2
    events=[]
    m.reload(patch, expected_revision=1, audit=events.append)
    assert m.revision == 2 and events[0]['paths'] == list(patch)
    with pytest.raises(ConfigurationError): m.reload(patch, expected_revision=1, audit=events.append)
    with pytest.raises(ConfigurationError): m.reload({'ai.endpoint': 'http://localhost:9999'}, expected_revision=2, audit=events.append)
    assert 'endpoint' not in json.dumps(m.public_snapshot())
    assert classification('native.minimum_cpp') == 'STATIC_BUILD_TIME'


def test_checked_in_json_matches_generated_schema():
    from jsonschema import Draft202012Validator
    from backend.configuration.models import GlobalConfig
    config = ROOT/'config'
    schema=json.loads((config/'global_config.schema.json').read_text())
    assert schema == GlobalConfig.model_json_schema()
    Draft202012Validator(schema).validate(json.loads((config/'global_config.json').read_text()))


def test_duplicate_keys_and_required_global_file_fail_closed(tmp_path):
    folder=tmp_path/'config';folder.mkdir()
    (folder/'global_config.json').write_text('{"schema_version":1,"schema_version":2}')
    with pytest.raises(ConfigurationError): ConfigManager(tmp_path,environ={})
    (folder/'global_config.json').unlink()
    with pytest.raises(ConfigurationError): ConfigManager(tmp_path,environ={})

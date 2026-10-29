"""Migrate and exercise a temporary local v2 server; never use operator data."""
from __future__ import annotations

import json
import os
from pathlib import Path
import socket
import subprocess
import sys
import tempfile
import time
import urllib.error
import urllib.request

ROOT = Path(__file__).resolve().parents[2]
PREFIX = '/api/v2/ecosystem'


def main():
    checks = {}
    with tempfile.TemporaryDirectory(prefix='ai-car-ecosystem-') as directory:
        temporary = Path(directory)
        with socket.socket() as sock:
            sock.bind(('127.0.0.1', 0))
            port = sock.getsockname()[1]
        env = os.environ.copy()
        env.update(DATABASE_URL='sqlite:///' + (temporary/'smoke.sqlite').as_posix(),
                   AI_CAR_ECOSYSTEM_ENABLED='1', AI_CAR_BACKEND_HOST='127.0.0.1', AI_CAR_BACKEND_PORT=str(port),
                   AI_CAR_DISABLE_LLM_AUTOSTART='1', PYTHONUTF8='1', PYTHONIOENCODING='utf-8')
        # Do not let an operator's JSON config change this isolated smoke database.
        env.pop('AI_CAR_ENV_CONFIG', None)
        subprocess.run([sys.executable, '-m', 'alembic', '-c', str(ROOT/'finalbuild/backend/alembic.ini'), 'upgrade', 'head'],
                       cwd=ROOT, env=env, check=True, capture_output=True, text=True)
        checks['explicit_alembic_upgrade'] = True
        base = f'http://127.0.0.1:{port}'

        def request(path, method='GET', data=None, token=None):
            headers = {'Content-Type': 'application/json'}
            if token: headers['Authorization'] = 'Bearer ' + token
            req = urllib.request.Request(base+path, headers=headers, method=method,
                                         data=json.dumps(data).encode() if data is not None else None)
            try:
                response = urllib.request.urlopen(req, timeout=10)
            except urllib.error.HTTPError as error:
                response = error
            with response:
                raw = response.read()
                return response.code, json.loads(raw) if raw else None

        output = (temporary/'server.log').open('a', encoding='utf-8')
        process = None
        def start():
            nonlocal process
            process = subprocess.Popen([sys.executable, '-m', 'apps.desktop.backend_worker'], cwd=ROOT/'finalbuild',
                                       env=env, stdout=output, stderr=subprocess.STDOUT)
            deadline = time.monotonic()+30
            while time.monotonic() < deadline:
                if process.poll() is not None: raise RuntimeError('Smoke server failed to start')
                try:
                    if request('/health')[0] == 200: return
                except (OSError, ValueError):
                    pass
                time.sleep(.1)
            raise RuntimeError('Smoke server startup deadline exceeded')

        def stop():
            if process is not None and process.poll() is None:
                process.terminate()
                try: process.wait(timeout=10)
                except subprocess.TimeoutExpired:
                    process.kill(); process.wait(timeout=5)

        def user(name):
            payload = dict(email=name+'@example.invalid', full_name=name, password='local-smoke-passphrase-123')
            status, body = request(PREFIX+'/accounts', 'POST', payload)
            assert status == 201, 'Account registration failed'
            status, login = request(PREFIX+'/auth/login', 'POST', {'email':payload['email'], 'password':payload['password']})
            assert status == 200, 'Login failed'
            return body['id'], login['access_token']

        try:
            start()
            owner, token = user('owner')
            _, mechanic = user('mechanic')
            status, profile = request(PREFIX+'/vehicles', 'POST', {'vehicle': {'make':'Mercedes-Benz','model':'E-Class','chassis':'W211'}}, token)
            assert status == 201
            vehicle_id = profile['id']
            status, center = request(PREFIX+'/service-centers','POST',{'name':'Smoke workshop','address':'Test address'},mechanic)
            assert status == 201
            center_id = center['id']
            status, invite = request(PREFIX+f'/service-centers/{center_id}/invitations','POST',{'account_id':owner},mechanic)
            assert status == 201
            shared_path = PREFIX+f'/service-centers/{center_id}/vehicles/{vehicle_id}'
            status, inbox = request(PREFIX+'/invitations', token=token)
            checks['owner_can_identify_inviter'] = status == 200 and inbox[0]['center_name'] == 'Smoke workshop' and inbox[0]['center_verified'] is False
            checks['workshop_membership_discoverable'] = request(PREFIX+'/service-centers', token=mechanic)[1][0]['id'] == center_id
            checks['invitation_alone_denied'] = request(shared_path, token=mechanic)[0] == 404
            status, grant = request(PREFIX+f'/invitations/{invite["id"]}/accept','POST',{'profile_id':vehicle_id},token)
            checks['owner_accepts'] = status == 200
            checks['approved_scoped_read'] = request(shared_path,token=mechanic)[0] == 200
            checks['legacy_bypass_denied'] = request('/api/v1/vehicle-profiles',token=token)[0] == 403
            assert request(PREFIX+f'/consents/{grant["id"]}','DELETE',token=token)[0] == 204
            checks['revoked_read_denied'] = request(shared_path,token=mechanic)[0] == 404
            status, diagnostic = request(PREFIX+'/diagnostics','POST',{'profile_id':vehicle_id},token)
            checks['owned_diagnostic_created'] = status == 201
            diagnostic_id = diagnostic['id']
            status, analyzed = request(PREFIX+f'/diagnostics/{diagnostic_id}/analyze','POST',{'symptom':'Engine misfires under load','dtcs':['P0302']},token)
            checks['shared_engine_analysis'] = status == 200 and bool(analyzed['hypotheses'])
            status, _ = request(PREFIX+'/settings','PUT',{'language':'fr','units':'USA'},token)
            checks['preferences_persisted'] = status == 200
            stop(); start()
            status, restored = request(PREFIX+'/me',token=token)
            checks['account_and_bearer_survive_restart'] = status == 200 and restored['id'] == owner
            checks['consent_revocation_survives_restart'] = request(shared_path,token=mechanic)[0] == 404
            checks['diagnostic_survives_restart'] = request(PREFIX+f'/diagnostics/{diagnostic_id}',token=token)[1]['session']['dtcs'][0]['code'] == 'P0302'
            checks['preferences_survive_restart'] = request(PREFIX+'/settings',token=token)[1]['language'] == 'fr'
            assert all(checks.values()), 'One or more smoke checks failed'
        finally:
            stop(); output.close()
    result = {'result':'PASS','database':'Temporary SQLite; real Alembic + Uvicorn subprocess and HTTP requests',
              'checks':checks,'external_providers':'NOT EXECUTED','real_hardware':'NOT EXECUTED'}
    destination = ROOT/'docs/evidence/foundation-http-smoke.json'
    destination.write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
    print('PASS: '+', '.join(checks))


if __name__ == '__main__':
    main()

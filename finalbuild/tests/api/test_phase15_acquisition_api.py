import asyncio
import pytest
from fastapi.testclient import TestClient
from api.main import app
from api.state import sessions

@pytest.mark.asyncio
async def test_acquisition_api():
    client=TestClient(app)
    r=client.post('/api/v1/sessions'); assert r.status_code==200
    sid=r.json()['session_id']
    r=client.post(f'/api/v1/acquisition/sessions/{sid}/start',json={'adapter':'simulator','poll_interval_ms':20,'pids':[12]})
    assert r.status_code==200
    await asyncio.sleep(0.06)
    r=client.get(f'/api/v1/acquisition/sessions/{sid}/status'); assert r.status_code==200
    assert r.json()['stats']['records'] >= 1
    r=client.get(f'/api/v1/acquisition/sessions/{sid}/records'); assert r.status_code==200
    assert r.json()['records']
    r=client.post(f'/api/v1/acquisition/sessions/{sid}/stop'); assert r.status_code==200
    sessions.pop(sid,None)

from __future__ import annotations
from fastapi import APIRouter, HTTPException
from api.state import sessions
from backend.acquisition.models import AcquisitionStartRequest, AcquisitionStatus
from backend.acquisition.service import AcquisitionApiService

router=APIRouter(prefix='/api/v1/acquisition',tags=['vehicle-acquisition'])
service=AcquisitionApiService()

@router.post('/sessions/{session_id}/start',response_model=AcquisitionStatus)
async def start_acquisition(session_id: str, request: AcquisitionStartRequest):
    if session_id not in sessions: raise HTTPException(404,'Session not found')
    if request.adapter != 'simulator':
        raise HTTPException(501,'Physical adapter selection is a device-side integration; use desktop/mobile/device adapter directly')
    try: return await service.start_simulator(sessions[session_id].session_id,request)
    except Exception as exc: raise HTTPException(502,f'Acquisition start failed: {exc}') from exc

@router.post('/sessions/{session_id}/stop',response_model=AcquisitionStatus)
async def stop_acquisition(session_id: str):
    if session_id not in sessions: raise HTTPException(404,'Session not found')
    try: return await service.stop(sessions[session_id].session_id)
    except KeyError: raise HTTPException(409,'Acquisition is not running')

@router.get('/sessions/{session_id}/status',response_model=AcquisitionStatus)
def acquisition_status(session_id: str):
    if session_id not in sessions: raise HTTPException(404,'Session not found')
    try: return service.status(sessions[session_id].session_id)
    except KeyError: raise HTTPException(404,'Acquisition not started')

@router.get('/sessions/{session_id}/records')
def acquisition_records(session_id: str, limit: int = 100):
    if session_id not in sessions: raise HTTPException(404,'Session not found')
    if limit < 1 or limit > 1000: raise HTTPException(400,'limit must be between 1 and 1000')
    try:
        return {'records':[r.__dict__ | {'id':str(r.id),'session_id':str(r.session_id),'source_type':r.source_type.value,'raw':r.raw.hex() if r.raw else None} for r in service.snapshot(sessions[session_id].session_id,limit)]}
    except KeyError: raise HTTPException(404,'Acquisition not started')

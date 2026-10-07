from fastapi import FastAPI, HTTPException, Body
from diagnostic.models import DiagnosticSession, Vehicle, Symptom, DTC, Evidence, EvidenceSource, EvidenceStatus
from diagnostic.rules import DiagnosticReasoningEngine
from diagnostic.decision import DiagnosticDecisionEngine
from api.platform_routes import router as platform_router
from api.intelligence_routes import router as intelligence_router
from api.state import sessions
from api.ai_routes import router as ai_router
from api.knowledge_routes import router as knowledge_router
from api.rag_routes import router as rag_router
from api.decision_routes import router as decision_router
from api.telemetry_routes import router as telemetry_router
from api.acquisition_routes import router as acquisition_router
from api.vehicle_diagnostic_routes import router as vehicle_diagnostic_router
from api.multi_ecu_routes import router as multi_ecu_router
from api.multi_bus_routes import router as multi_bus_router
from api.network_discovery_routes import router as network_discovery_router
from api.active_discovery_routes import router as active_discovery_router
from api.device_routes import router as device_router
app=FastAPI(title="AI Auto Diagnostic Platform",version="0.1.0")
engine=DiagnosticReasoningEngine()
decision_engine=DiagnosticDecisionEngine()
app.include_router(platform_router)
app.include_router(intelligence_router)
app.include_router(ai_router)
app.include_router(knowledge_router)
app.include_router(rag_router)
app.include_router(decision_router)
app.include_router(telemetry_router)
app.include_router(acquisition_router)
app.include_router(vehicle_diagnostic_router)
app.include_router(multi_ecu_router)
app.include_router(multi_bus_router)
app.include_router(network_discovery_router)
app.include_router(active_discovery_router)
app.include_router(device_router)
@app.get('/health')
def health(): return {'status':'ok','service':'diagnostic-api','version':'0.1.0'}
@app.post('/api/v1/sessions',response_model=DiagnosticSession)
def create_session(vehicle:dict | None=Body(default=None)):
    # Accept both the canonical vehicle object and an empty JSON body for
    # legacy clients that create a session before vehicle identification.
    parsed_vehicle = Vehicle(**vehicle) if vehicle else None
    s=DiagnosticSession(vehicle=parsed_vehicle); sessions[str(s.session_id)]=s; return s
@app.get('/api/v1/sessions/{session_id}',response_model=DiagnosticSession)
def get_session(session_id:str):
    if session_id not in sessions: raise HTTPException(404,'Session not found')
    return sessions[session_id]

@app.put('/api/v1/sessions/{session_id}/vehicle',response_model=DiagnosticSession)
def update_vehicle(session_id:str,vehicle:Vehicle):
    s=get_session(session_id)
    s.vehicle=vehicle
    s.audit_log.append({"event":"VEHICLE_UPDATED"})
    return s
@app.post('/api/v1/sessions/{session_id}/symptoms',response_model=DiagnosticSession)
def add_symptom(session_id:str,symptom:Symptom):
    """Add a user-reported symptom using the canonical raw_text payload."""
    if not symptom.raw_text.strip():
        raise HTTPException(422,'Symptom text must not be empty')
    s=get_session(session_id)
    s.symptoms.append(symptom)
    s.evidence.append(Evidence(fact=symptom.raw_text,source=EvidenceSource.USER_REPORTED,status=EvidenceStatus.REPORTED))
    s.audit_log.append({"event":"SYMPTOM_ADDED","symptom_id":str(symptom.id)})
    return s

@app.put('/api/v1/sessions/{session_id}/symptoms/{symptom_id}',response_model=DiagnosticSession)
def update_symptom(session_id:str,symptom_id:str,symptom:Symptom):
    """Update an existing user-reported symptom without replacing its identity."""
    if not symptom.raw_text.strip():
        raise HTTPException(422,'Symptom text must not be empty')
    s=get_session(session_id)
    target=next((item for item in s.symptoms if str(item.id)==symptom_id),None)
    if target is None:
        raise HTTPException(404,'Symptom not found')
    old_text=target.raw_text
    target.raw_text=symptom.raw_text.strip()
    target.normalized=symptom.normalized
    target.symptom=symptom.symptom
    for evidence in s.evidence:
        if evidence.source == EvidenceSource.USER_REPORTED and evidence.fact == old_text:
            evidence.fact=target.raw_text
            break
    s.audit_log.append({"event":"SYMPTOM_UPDATED","symptom_id":symptom_id})
    return s

@app.delete('/api/v1/sessions/{session_id}/symptoms/{symptom_id}',response_model=DiagnosticSession)
def delete_symptom(session_id:str,symptom_id:str):
    """Delete an existing user-reported symptom and its direct evidence."""
    s=get_session(session_id)
    index=next((i for i,item in enumerate(s.symptoms) if str(item.id)==symptom_id),None)
    if index is None:
        raise HTTPException(404,'Symptom not found')
    removed=s.symptoms.pop(index)
    s.evidence=[e for e in s.evidence if not (e.source == EvidenceSource.USER_REPORTED and e.fact == removed.raw_text)]
    s.audit_log.append({"event":"SYMPTOM_DELETED","symptom_id":symptom_id})
    return s
@app.post('/api/v1/sessions/{session_id}/dtcs',response_model=DiagnosticSession)
def add_dtc(session_id:str,dtc:DTC):
    s=get_session(session_id); s.dtcs.append(dtc); status=EvidenceStatus.MEASURED if dtc.source==EvidenceSource.ECU_REPORTED else EvidenceStatus.REPORTED; s.evidence.append(Evidence(fact=dtc.code,source=dtc.source,status=status)); return s
@app.post('/api/v1/sessions/{session_id}/analyze',response_model=DiagnosticSession)
def analyze(session_id:str):
    s=engine.analyze(get_session(session_id))
    decision_engine.refresh_recommendations(s)
    return s

@app.post('/api/v1/analysis/{session_id}',response_model=DiagnosticSession)
def analyze_compat(session_id:str):
    s=engine.analyze(get_session(session_id))
    decision_engine.refresh_recommendations(s)
    return s

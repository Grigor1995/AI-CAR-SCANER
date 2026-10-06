from fastapi import FastAPI, HTTPException
from diagnostic.models import DiagnosticSession, Vehicle, Symptom, DTC, Evidence, EvidenceSource, EvidenceStatus
from diagnostic.rules import DiagnosticReasoningEngine
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
def create_session(vehicle:Vehicle|None=None):
    s=DiagnosticSession(vehicle=vehicle); sessions[str(s.session_id)]=s; return s
@app.get('/api/v1/sessions/{session_id}',response_model=DiagnosticSession)
def get_session(session_id:str):
    if session_id not in sessions: raise HTTPException(404,'Session not found')
    return sessions[session_id]
@app.post('/api/v1/sessions/{session_id}/symptoms',response_model=DiagnosticSession)
def add_symptom(session_id:str,symptom:Symptom):
    s=get_session(session_id); s.symptoms.append(symptom); s.evidence.append(Evidence(fact=symptom.raw_text,source=EvidenceSource.USER_REPORTED,status=EvidenceStatus.REPORTED)); return s
@app.post('/api/v1/sessions/{session_id}/dtcs',response_model=DiagnosticSession)
def add_dtc(session_id:str,dtc:DTC):
    s=get_session(session_id); s.dtcs.append(dtc); status=EvidenceStatus.MEASURED if dtc.source==EvidenceSource.ECU_REPORTED else EvidenceStatus.REPORTED; s.evidence.append(Evidence(fact=dtc.code,source=dtc.source,status=status)); return s
@app.post('/api/v1/sessions/{session_id}/analyze',response_model=DiagnosticSession)
def analyze(session_id:str): return engine.analyze(get_session(session_id))

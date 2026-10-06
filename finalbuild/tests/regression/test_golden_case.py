from pathlib import Path
import yaml
from diagnostic.models import *
from diagnostic.rules import DiagnosticReasoningEngine
def test_golden_case():
    c=yaml.safe_load(Path('datasets/golden-cases/LPG_MISFIRE_001.yaml').read_text()); s=DiagnosticSession(vehicle=Vehicle(**c['vehicle']))
    for x in c['symptoms']: s.evidence.append(Evidence(fact=x,source=EvidenceSource.USER_REPORTED,status=EvidenceStatus.REPORTED))
    s.dtcs=[DTC(code=x) for x in c['dtc']]; out=DiagnosticReasoningEngine().analyze(s); cats={h.category for h in out.hypotheses}; assert {'ignition','intake'}<=cats; assert not any('coil failure' in h.statement.lower() for h in out.hypotheses)

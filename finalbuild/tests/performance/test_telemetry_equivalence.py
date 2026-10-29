"""Numerical/event regression against the unchanged standalone analysis contracts."""
import random
from uuid import UUID
import pytest
from telemetry.analysis import compute_stats, detect_events
from telemetry.models import TelemetrySample, TelemetrySummary
from telemetry.channels import channel_name
from telemetry.service import TelemetryService


def canonical(summary):
    data=summary.model_dump(mode='json');data.pop('generated_at')
    for event in data['events']:event.pop('id')
    return data


def original_summary(service,sid):
    items=service.samples(sid);grouped={}
    for item in items:grouped.setdefault(item.pid,[]).append(item)
    stats=[];events=[]
    for pid,samples in sorted(grouped.items()):
        stat=compute_stats(sid,pid,samples);signal_events=detect_events(sid,pid,samples)
        stat.display_name=channel_name(pid);stat.event_count=len(signal_events)
        stat.anomaly_count=sum(e.event_type.value in {'STEP_CHANGE','RATE_SPIKE','OUT_OF_RANGE'} for e in signal_events)
        stats.append(stat);events.extend(signal_events)
    return TelemetrySummary(session_id=sid,sample_count=len(items),signal_count=len(grouped),
        start_ms=items[0].timestamp_ms if items else None,end_ms=items[-1].timestamp_ms if items else None,stats=stats,events=events)


@pytest.mark.parametrize('seed',range(12))
@pytest.mark.parametrize('count',[0,1,2,127,1024])
def test_summary_exact_equivalence(seed,count):
    rng=random.Random(seed);sid=UUID(int=42);other=UUID(int=43);service=TelemetryService()
    samples=[TelemetrySample(session_id=sid,pid=rng.choice(['rpm','map','coolant_temp','unknown']),
        timestamp_ms=rng.randrange(20)*100,value=rng.choice([-100.,0.,.1,95.,1e4]),
        quality=rng.choice(['GOOD','SUSPECT','INVALID']),sequence=rng.choice([None,0,1,3])) for _ in range(count)]
    service.append(samples+[TelemetrySample(session_id=other,pid='rpm',timestamp_ms=0,value=42)])
    before=[s.model_dump() for s in samples]
    assert canonical(service.summarize(sid))==canonical(original_summary(service,sid))
    assert [s.model_dump() for s in samples]==before
    assert service.summarize(other).sample_count==1


def test_append_recomputes_and_does_not_return_shared_cached_models():
    sid=UUID(int=42);service=TelemetryService()
    service.append([TelemetrySample(session_id=sid,pid='rpm',timestamp_ms=200,value=800,quality='INVALID')])
    first=service.summarize(sid)
    assert first.sample_count==1 and first.stats[0].count==0
    first.stats[0].count=99
    service.append([TelemetrySample(session_id=sid,pid='rpm',timestamp_ms=100,value=1000)])
    second=service.summarize(sid)
    assert second.sample_count==2 and second.stats[0].count==1
    assert second.start_ms==100 and second.end_ms==200

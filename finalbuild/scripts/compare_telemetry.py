"""Paired baseline/current comparison, frozen reference loaded from a Git revision."""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path
import statistics
import subprocess
import time
import types
from benchmark_pipeline import ROOT, fixture, measure


def reference(revision):
    # Execute trusted source from the explicitly selected local Git revision.
    analysis_source=subprocess.check_output(['git','show',f'{revision}:finalbuild/backend/telemetry/analysis.py'],cwd=ROOT,text=True)
    service_source=subprocess.check_output(['git','show',f'{revision}:finalbuild/backend/telemetry/service.py'],cwd=ROOT,text=True)
    analysis=types.ModuleType('telemetry._baseline_analysis');analysis.__package__='telemetry'
    exec(compile(analysis_source,'baseline_analysis.py','exec'),analysis.__dict__)
    namespace={'__package__':'telemetry','compute_stats':analysis.compute_stats,'detect_events':analysis.detect_events}
    service_source=service_source.replace('from .analysis import compute_stats, detect_events','')
    exec(compile(service_source,'baseline_service.py','exec'),namespace)
    return namespace['TelemetryService'],hashlib.sha256((analysis_source+service_source).encode()).hexdigest()


def main():
    p=argparse.ArgumentParser();p.add_argument('--baseline-ref',default='540e00f');p.add_argument('--output',type=Path,required=True);args=p.parse_args()
    cls,digest=reference(args.baseline_ref);results={}
    for count in (1000,10000,50000):
        current,sid=fixture(count);old=cls();old.append(current._samples[sid])
        jobs={'baseline':lambda:old.summarize(sid),'optimized':lambda:current.summarize(sid)}
        # IDs and generation times are intentionally fresh on every summary.
        def canonical(summary):
            data=summary.model_dump(mode='json');data.pop('generated_at');
            for event in data['events']:event.pop('id')
            return data
        assert canonical(jobs['baseline']())==canonical(jobs['optimized']()),'summary mismatch'
        for fn in jobs.values():
            for _ in range(5):fn()
        raw={name:[] for name in jobs}
        for iteration in range(40):
            for name in (list(jobs) if iteration%2==0 else list(reversed(jobs))):
                start=time.perf_counter_ns();jobs[name]();raw[name].append((time.perf_counter_ns()-start)/1e6)
        result={name:{'p50_ms':statistics.median(v),'p95_ms':sorted(v)[37],'p99_ms':max(v),'raw_ms':v} for name,v in raw.items()}
        result['p50_improvement_percent']=100*(1-result['optimized']['p50_ms']/result['baseline']['p50_ms'])
        result['equivalence']='PASS'
        result['resources']={name:measure(fn,10) for name,fn in jobs.items()}
        results[str(count)]=result
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(json.dumps({'baseline_ref':args.baseline_ref,'reference_sha256':digest,'iterations':40,'ordering':'alternating AB/BA','results':results},indent=2)+'\n',encoding='utf-8')
    print({key:round(value['p50_improvement_percent'],2) for key,value in results.items()})

if __name__=='__main__':main()

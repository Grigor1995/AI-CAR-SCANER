"""Local reproducible CPU benchmarks; never opens an adapter or operator database."""
from __future__ import annotations
import argparse
import cProfile
import gc
import json
import math
import os
from pathlib import Path
import platform
import random
import sqlite3
import statistics
import subprocess
import sys
import time
import tracemalloc
from uuid import UUID

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT), str(ROOT / 'backend')]
os.environ['DATABASE_URL'] = 'sqlite:///:memory:'
os.environ['AI_CAR_ECOSYSTEM_ENABLED'] = '0'
from telemetry.models import TelemetrySample
from telemetry.service import TelemetryService
from obd.decoding import decode_snapshot
from vehicle.obd.protocols.elm327 import ELM327Protocol
from diagnostic.models import DiagnosticSession, DTC, Symptom, Vehicle
from ai.reasoning.engine import DiagnosticIntelligenceEngine


def fixture(count):
    rng = random.Random(429)
    sid = UUID(int=42)
    samples = [TelemetrySample(session_id=sid, timestamp_ms=(i // 4)*100,
        pid=('rpm','coolant_temp','vehicle_speed','map')[i % 4],
        value=(750,95,40,32)[i % 4] + rng.random(), sequence=i,
        quality='INVALID' if i % 101 == 0 else 'GOOD') for i in range(count)]
    rng.shuffle(samples)
    service = TelemetryService()
    service.append(samples)
    return service, sid


def measure(fn, iterations, warmups=5):
    for _ in range(warmups): fn()
    gc.collect()
    times = []
    cpu = time.process_time()
    wall = time.perf_counter()
    for _ in range(iterations):
        start = time.perf_counter_ns(); fn(); times.append((time.perf_counter_ns()-start)/1e6)
    elapsed = time.perf_counter()-wall
    cpu = time.process_time()-cpu
    ordered = sorted(times)
    tracemalloc.start(); fn(); current, peak = tracemalloc.get_traced_memory(); tracemalloc.stop()
    return {'iterations':iterations,'warmups':warmups,'p50_ms':statistics.median(times),
        'p95_ms':ordered[math.ceil(.95*len(times))-1], 'p99_ms':ordered[math.ceil(.99*len(times))-1],
        'operations_per_second':iterations/elapsed, 'cpu_seconds':cpu, 'wall_seconds':elapsed,
        'cpu_percent_one_core':100*cpu/elapsed,'traced_peak_bytes':peak,
        'allocation_count':'NOT MEASURED','gc_counts_after':gc.get_count()}


def main():
    parser=argparse.ArgumentParser(); parser.add_argument('--output',type=Path,required=True)
    parser.add_argument('--iterations',type=int,default=30); args=parser.parse_args()
    if args.iterations < 2: parser.error('iterations must be >= 2')
    engine=DiagnosticIntelligenceEngine()
    session=DiagnosticSession(vehicle=Vehicle(make='Mercedes-Benz',model='W211 E350',year=2006,
        engine='M272 3.5',fuel=['petrol','LPG'],ecu='ME 9.7'),
        symptoms=[Symptom(raw_text='Engine shakes on LPG below 2000 RPM under load; petrol is normal.')],dtcs=[DTC(code='P0302')])
    jobs={'diagnostic_analysis':lambda:engine.analyze(session.model_copy(deep=True)),
        'pid_snapshot':lambda:decode_snapshot({'010C':'41 0C 1A F8 >','0105':'41 05 87 >','010D':'41 0D 28 >'}),
        'dtc_decode':lambda:ELM327Protocol.dtc_codes(bytes.fromhex('0302017102220000')),
        'session_json':lambda:session.model_dump_json()}
    for count in (1000,10000,50000):
        service,sid=fixture(count)
        jobs[f'telemetry_summary_{count}']=lambda service=service,sid=sid:service.summarize(sid)
    from fastapi.testclient import TestClient
    from api.main import app
    with TestClient(app) as client:
        jobs['http_health_inprocess']=lambda:client.get('/health').raise_for_status()
        with sqlite3.connect(':memory:') as db:
            db.execute('CREATE TABLE samples (timestamp_ms INTEGER PRIMARY KEY, value REAL)')
            db.executemany('INSERT INTO samples VALUES (?,?)',[(i,float(i)) for i in range(10000)])
            jobs['sqlite_indexed_history_100']=lambda:db.execute('SELECT * FROM samples WHERE timestamp_ms >= ? ORDER BY timestamp_ms LIMIT 100',(5000,)).fetchall()
            results={key:measure(fn,args.iterations) for key,fn in jobs.items()}
    profile=cProfile.Profile(); profile.runcall(jobs['telemetry_summary_50000'])
    profile_path=args.output.with_suffix('.prof'); profile_path.parent.mkdir(parents=True,exist_ok=True); profile.dump_stats(str(profile_path))
    startups=[]
    for _ in range(5):
        start=time.perf_counter()
        subprocess.run([sys.executable,'-c','import api.main'],cwd=ROOT,env={**os.environ,'PYTHONPATH':str(ROOT/'backend')+os.pathsep+str(ROOT),'DATABASE_URL':'sqlite:///:memory:'},check=True,stdout=subprocess.DEVNULL)
        startups.append((time.perf_counter()-start)*1000)
    result={'schema_version':1,'python':sys.version,'platform':platform.platform(),
        'git_head':subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip(),
        'clock':'perf_counter_ns','seed':429,'results':results,
        'backend_import_fresh_process_ms':startups,'profile':profile_path.name,
        'limitations':['Synthetic shuffled telemetry; four channels at 10 Hz each; not hardware throughput.',
        'Fresh process imports use warm OS file cache; true cold boot NOT MEASURED.',
        'HTTP is in-process TestClient, not socket/load capacity.',
        'SQLite is an isolated in-memory indexed fixture, not deployed PostgreSQL.',
        'Adapter/ECU/network latency, real LLM/RAG model inference, Windows/iOS, GPU/frame times and RSS NOT MEASURED.']}
    args.output.write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(results,indent=2))

if __name__=='__main__': main()

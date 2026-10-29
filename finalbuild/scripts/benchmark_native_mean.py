"""Explicit experiment: compare Python exact mean, fmean, and C ABI including copies.
Build the shared library separately; application runtime has no native dependency.
"""
from __future__ import annotations
import argparse
import ctypes
import json
import math
from pathlib import Path
import statistics
from benchmark_pipeline import fixture, measure
from telemetry import analysis


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--library',type=Path,required=True);parser.add_argument('--output',type=Path,required=True);args=parser.parse_args()
    lib=ctypes.CDLL(str(args.library.resolve()))
    lib.telemetry_mean.argtypes=[ctypes.POINTER(ctypes.c_double),ctypes.c_size_t,ctypes.POINTER(ctypes.c_double)]
    lib.telemetry_mean.restype=ctypes.c_int
    def native(values):
        packed=(ctypes.c_double*len(values))(*values)
        out=ctypes.c_double();status=lib.telemetry_mean(packed,len(values),ctypes.byref(out))
        if status:raise ValueError(f'native mean status {status}')
        return out.value
    service,sid=fixture(10000);exact=analysis.mean
    base=service.summarize(sid).model_dump(mode='json')
    results={}
    try:
        for name,fn in [('python_exact_mean',statistics.mean),('python_fmean_experiment',statistics.fmean),('cpp_copy_included_experiment',native)]:
            analysis.mean=fn
            actual=service.summarize(sid).model_dump(mode='json')
            errors=[]
            for left,right in zip(base['stats'],actual['stats']):
                for key in ('mean','mean_abs_delta','stddev'):
                    assert math.isclose(left[key],right[key],rel_tol=1e-12,abs_tol=1e-12)
                    errors.append(abs(left[key]-right[key]))
            results[name]={'pipeline':measure(lambda:service.summarize(sid),40),
                'max_absolute_numeric_difference':max(errors),'tolerance_check':'PASS (fixture only; not exact equivalence)'}
        values=[float(i)/7 for i in range(2500)]
        packed=(ctypes.c_double*len(values))(*values);out=ctypes.c_double()
        results['native_prepacked_micro_only']=measure(lambda:lib.telemetry_mean(packed,len(values),ctypes.byref(out)),1000)
        results['native_mean_with_copy_micro']=measure(lambda:native(values),1000)
        results['python_fmean_micro']=measure(lambda:statistics.fmean(values),1000)
        results['python_exact_mean_micro']=measure(lambda:statistics.mean(values),1000)
    finally:analysis.mean=exact
    args.output.write_text(json.dumps({'results':results,'decision':'NOT INTEGRATED: finite-only contract, floating-point equivalence not universal; compare simpler fmean first. GIL release only during ctypes call, packing holds GIL. No JNI/iOS/Windows validation.'},indent=2)+'\n',encoding='utf-8')

if __name__=='__main__':main()

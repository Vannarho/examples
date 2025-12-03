#!/usr/bin/env python

import glob
import os
import sys
from contextlib import contextmanager
sys.path.append('../')
from vre_examples_helper import VreExample

vreex = VreExample(sys.argv[1] if len(sys.argv)>1 else False)
# Keep SIM/CG path sample sizes consistent with XVA CG creation.
# If you want to throttle samples locally, ensure the same value is
# used by both the SIM driver and the CG builder. We default to no override.
os.environ.pop('OVERWRITE_SCENARIOGENERATOR_SAMPLES', None)


# Small helper to set env vars only for the duration of a run
@contextmanager
def env(vars):
    prev = {k: os.environ.get(k) for k in vars}
    try:
        for k, v in vars.items():
            if v is None:
                os.environ.pop(k, None)
            else:
                os.environ[k] = str(v)
        yield
    finally:
        for k, v in prev.items():
            if v is None:
                os.environ.pop(k, None)
            else:
                os.environ[k] = v


def ce_env_defaults():
    """Ensure CE frozen-basis plumbing stays enabled unless explicitly overridden."""
    return {
        "VRE_AD_CE_FREEZE_BASIS": os.environ.get("VRE_AD_CE_FREEZE_BASIS", "1"),
    }

print("+-----------------------------------------------------+")
print("| XVA Risk: SA-CVA    - AAD Larger Portfolio          |")
print("+-----------------------------------------------------+")


vreex.print_headline("Run SA-CVA with CG/AAD CVA Sensitivities (Trade Script)")
with env({
    # Trace AD scenario contributions for quick diffing; adjust filter as needed
    # Set to '*' to trace all, or e.g. 'EquitySpot/' / 'FXSpot/' / 'CommodityCurve/' to focus
    "VRE_CG_SENSI_TRACE_SCEN": os.environ.get("VRE_CG_SENSI_TRACE_SCEN", "*"),
    "VRE_CG_SENSI_TRACE_TOP": os.environ.get("VRE_CG_SENSI_TRACE_TOP", "2000"),
    "VRE_CG_SENSI_TRACE_FILE": os.environ.get("VRE_CG_SENSI_TRACE_FILE", "Output/sacva_cg_ad_larger_portfolio/cg_trace_ad_large.csv"),
    **ce_env_defaults(),
}):
    vreex.run("Input/vre_sacva_cg_ad_larger_portfolio.xml")


print("+-----------------------------------------------------+")
print("| XVA Risk: SA-CVA    - GPU Larger Portfolio          |")
print("+-----------------------------------------------------+")


vreex.print_headline("Run SA-CVA with CG/GPU CVA Sensitivities (Trade Script)")

with env({
    # Use a different output to compare AAD vs GPU quickly
    "VRE_CG_SENSI_TRACE_SCEN": os.environ.get("VRE_CG_SENSI_TRACE_SCEN", "*"),
    "VRE_CG_SENSI_TRACE_TOP": os.environ.get("VRE_CG_SENSI_TRACE_TOP", "2000"),
    "VRE_CG_SENSI_TRACE_FILE": os.environ.get("VRE_CG_SENSI_TRACE_FILE_GPU", "Output/sacva_cg_gpu_larger_portfolio/cg_trace_gpu_large.csv"),
    **ce_env_defaults(),
}):
    vreex.run_gpu_dynamic(
        "Input/vre_sacva_cg_gpu_larger_portfolio.xml",
        extra_xmls=["Input/sacva_larger_porfolio/pricingengine_gpu.xml"],
    )

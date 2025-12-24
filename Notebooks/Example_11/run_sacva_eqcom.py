#!/usr/bin/env python

import glob
import os
import sys
sys.path.append('../')
from vre_examples_helper import VreExample

from contextlib import contextmanager
import os

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

vreex = VreExample(sys.argv[1] if len(sys.argv)>1 else False)
# Keep SIM/CG path sample sizes consistent with XVA CG creation.
# If you want to throttle samples locally, ensure the same value is
# used by both the SIM driver and the CG builder. We default to no override.
os.environ.pop('OVERWRITE_SCENARIOGENERATOR_SAMPLES', None)



print("+-----------------------------------------------------+")
print("| XVA Risk: SA-CVA    - AAD 2 Trade EQ COM           |")
print("+-----------------------------------------------------+")

vreex.print_headline("Run SA-CVA with CG/AAD CVA Sensitivities (scripted trades)")
with env({
    "VRE_CG_SENSI_TRACE_SCEN": "*",   # or EquitySpot/SP5
    "VRE_CG_SENSI_TRACE_TOP": "20",
    "VRE_CG_SENSI_TRACE_FILE": "cg_trace_aad.csv",
}):
    vreex.run("Input/vre_sacva_cg_ad_eqcom.xml")

# print("+-----------------------------------------------------+")
# print("| XVA Risk: SA-CVA    - GPU 2 Trade EQ COM           |")
# print("+-----------------------------------------------------+")

# vreex.print_headline("Run SA-CVA with CG/GPU CVA Sensitivities (scripted trades)")
# with env({
#     "VRE_CG_SENSI_TRACE_SCEN": "*",   # or "*" / another scenario
#     "VRE_CG_SENSI_TRACE_TOP": "20",
#     "VRE_CG_SENSI_TRACE_FILE": "cg_trace_gpu.csv",
# }):
#     vreex.run_gpu_dynamic(
#         "Input/vre_sacva_cg_gpu_eqcom.xml",
#         extra_xmls=["Input/sacva_eqcom/pricingengine_gpu.xml"],
#     )
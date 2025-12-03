#!/usr/bin/env python

import glob
import os
import sys
sys.path.append('../')
from vre_examples_helper import VreExample

vreex = VreExample(sys.argv[1] if len(sys.argv)>1 else False)
# Keep SIM/CG path sample sizes consistent with XVA CG creation.
# If you want to throttle samples locally, ensure the same value is
# used by both the SIM driver and the CG builder. We default to no override.
os.environ.pop('OVERWRITE_SCENARIOGENERATOR_SAMPLES', None)


print("+-----------------------------------------------------+")
print("| XVA Risk: SA-CVA    - AAD                           |")
print("+-----------------------------------------------------+")


vreex.print_headline("Run SA-CVA with CG/AAD CVA Sensitivities (scripted trades)")
vreex.run("Input/vre_sacva_cg_ad.xml")


print("+-----------------------------------------------------+")
print("| XVA Risk: SA-CVA    - GPU                           |")
print("+-----------------------------------------------------+")

vreex.print_headline("Run SA-CVA with CG/GPU CVA Sensitivities (scripted trades)")
# Single-source-of-truth: dynamically patch ExternalComputeDevice into the
# example's GPU configs based on the detected GPU (Apple OpenCL vs NVIDIA CUDA).
# Both files are patched in-place and restored after the run.
vreex.run_gpu_dynamic(
    "Input/vre_sacva_cg_gpu.xml",
    extra_xmls=["Input/cg/pricingengine_gpu.xml"],
)


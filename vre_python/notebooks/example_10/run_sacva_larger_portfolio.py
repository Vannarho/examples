#!/usr/bin/env python3

import importlib.util
from pathlib import Path
import os

_RUNTIME_PATH = Path(__file__).resolve().parents[1] / "_wheel_runtime.py"
_RUNTIME_SPEC = importlib.util.spec_from_file_location("_vre_wheel_runtime", _RUNTIME_PATH)
if _RUNTIME_SPEC is None or _RUNTIME_SPEC.loader is None:
    raise RuntimeError(f"Could not load wheel runtime helper from {_RUNTIME_PATH}")
_wheel_runtime = importlib.util.module_from_spec(_RUNTIME_SPEC)
_RUNTIME_SPEC.loader.exec_module(_wheel_runtime)

print_banner = _wheel_runtime.print_banner
run_parameters_file = _wheel_runtime.run_parameters_file


HERE = Path(__file__).resolve().parent
os.environ.pop("OVERWRITE_SCENARIOGENERATOR_SAMPLES", None)


def ce_env_defaults() -> dict[str, str]:
    return {
        "VRE_AD_CE_FREEZE_BASIS": os.environ.get("VRE_AD_CE_FREEZE_BASIS", "1"),
    }


print_banner("XVA Risk: SA-CVA    - AAD Larger Portfolio")
run_parameters_file(
    HERE / "input/vre_sacva_cg_ad_larger_portfolio.toml",
    env_overrides={
        "VRE_CG_SENSI_TRACE_SCEN": os.environ.get("VRE_CG_SENSI_TRACE_SCEN", "*"),
        "VRE_CG_SENSI_TRACE_TOP": os.environ.get("VRE_CG_SENSI_TRACE_TOP", "2000"),
        "VRE_CG_SENSI_TRACE_FILE": os.environ.get(
            "VRE_CG_SENSI_TRACE_FILE",
            "output/sacva_cg_ad_larger_portfolio/cg_trace_ad_large.csv",
        ),
        **ce_env_defaults(),
    },
)

print_banner("XVA Risk: SA-CVA    - GPU Larger Portfolio")
run_parameters_file(
    HERE / "input/vre_sacva_cg_gpu_larger_portfolio.toml",
    env_overrides={
        "VRE_CG_SENSI_TRACE_SCEN": os.environ.get("VRE_CG_SENSI_TRACE_SCEN", "*"),
        "VRE_CG_SENSI_TRACE_TOP": os.environ.get("VRE_CG_SENSI_TRACE_TOP", "2000"),
        "VRE_CG_SENSI_TRACE_FILE": os.environ.get(
            "VRE_CG_SENSI_TRACE_FILE_GPU",
            "output/sacva_cg_gpu_larger_portfolio/cg_trace_gpu_large.csv",
        ),
        **ce_env_defaults(),
    },
    gpu_dynamic=True,
    gpu_optional=True,
)

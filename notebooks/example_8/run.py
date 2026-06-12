#!/usr/bin/env python3

import importlib.util
from pathlib import Path

_RUNTIME_PATH = Path(__file__).resolve().parents[1] / "_wheel_runtime.py"
_RUNTIME_SPEC = importlib.util.spec_from_file_location("_vre_wheel_runtime", _RUNTIME_PATH)
if _RUNTIME_SPEC is None or _RUNTIME_SPEC.loader is None:
    raise RuntimeError(f"Could not load wheel runtime helper from {_RUNTIME_PATH}")
_wheel_runtime = importlib.util.module_from_spec(_RUNTIME_SPEC)
_RUNTIME_SPEC.loader.exec_module(_wheel_runtime)

print_banner = _wheel_runtime.print_banner
run_parameters_file = _wheel_runtime.run_parameters_file


HERE = Path(__file__).resolve().parent

for output_dir in [
    HERE / "Output/8_1",
    HERE / "Output/8_2",
    HERE / "Output/8_3/pnl",
    HERE / "Output/8_3/explain",
]:
    output_dir.mkdir(parents=True, exist_ok=True)


print_banner("Scenario (8_1)")
run_parameters_file(HERE / "input/8_1/vre.toml")

print_banner("Historical Sim Var (8_2)")
run_parameters_file(HERE / "input/8_2/vre.toml")

print_banner("P&L (8_3)")
run_parameters_file(HERE / "input/8_3/vre_pnl.toml")

print_banner("P&L Explain (8_3)")
run_parameters_file(HERE / "input/8_3/vre_explain.toml")

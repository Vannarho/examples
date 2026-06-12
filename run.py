#!/usr/bin/env python

import subprocess as p
import sys
from pathlib import Path
import os


def _env_truthy(name: str) -> bool:
    return os.environ.get(name, "").strip() in {"1", "true", "TRUE", "yes", "YES", "on", "ON"}


def _python_executable() -> str:
    return sys.executable


def _child_env() -> dict[str, str]:
    env = os.environ.copy()
    if _env_truthy("VRE_PYBIND_FORCE_BUILD_DIR"):
        raise RuntimeError("Vannarho/examples is wheel-only; VRE_PYBIND_FORCE_BUILD_DIR is not supported")
    env.pop("PYTHONPATH", None)
    env.pop("VRE_PYBIND_BUILD_DIR", None)
    env.pop("VRE_NOTEBOOK_BUILD_ROOT", None)
    return env


def _skip_cases() -> set[str]:
    raw = os.environ.get("VRE_PYTHON_EXAMPLE_SKIP", "")
    return {item.strip() for item in raw.replace(os.pathsep, ",").split(",") if item.strip()}


cases = [
    "example_scripts/commodityforward.py",
    "example_scripts/conventions.py",
    "example_scripts/gaussian1d-models.py",
    "example_scripts/log.py",
    "example_scripts/swap.py",
    "notebooks/example_8/run.py",
    "notebooks/example_10/run_sacva_cg.py",
    "notebooks/example_10/run_sacva_larger_portfolio.py",
    "notebooks/example_11/run_sacva_eqcom.py",
    "notebooks/example_11/run_sacva_eqcom_fd.py",
    "notebooks/example_11/run_sacva_eqcom_fd_aad.py",
]


def main() -> int:
    failures = []
    skip_cases = _skip_cases()
    for case in cases:
        if case in skip_cases:
            print(f"Skipping: {case}")
            continue
        case_path = (Path(__file__).resolve().parent / case).resolve()
        cmd = [_python_executable(), case_path.name]
        print("Calling:", " ".join(cmd))
        rc = p.call(cmd, cwd=case_path.parent, env=_child_env())
        if rc != 0:
            failures.append((case, rc))

    if failures:
        print("VRE Python run failures:")
        for name, rc in failures:
            print(f"  {name}: rc={rc}")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

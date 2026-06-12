#!/usr/bin/env python3

from __future__ import annotations

import importlib.util
from pathlib import Path
import sys

_RUNTIME_PATH = Path(__file__).resolve().parents[1] / "_wheel_runtime.py"
_RUNTIME_SPEC = importlib.util.spec_from_file_location("_vre_wheel_runtime", _RUNTIME_PATH)
if _RUNTIME_SPEC is None or _RUNTIME_SPEC.loader is None:
    raise RuntimeError(f"Could not load wheel runtime helper from {_RUNTIME_PATH}")
_wheel_runtime = importlib.util.module_from_spec(_RUNTIME_SPEC)
_RUNTIME_SPEC.loader.exec_module(_wheel_runtime)

print_banner = _wheel_runtime.print_banner
run_parameters_file = _wheel_runtime.run_parameters_file


EXAMPLE_DIR = Path(__file__).resolve().parent
DEFAULT_BUNDLE = EXAMPLE_DIR / "input" / "vre_sacva_fd_eqcom.toml"


def main() -> int:
    bundle = DEFAULT_BUNDLE
    if len(sys.argv) > 1:
        candidate = Path(sys.argv[1])
        bundle = candidate if candidate.is_absolute() else (EXAMPLE_DIR / candidate)

    print_banner("XVA Risk: SA-CVA    - FD bump 2 Trade EQ COM")
    print(f"[fd-bump] master bundle: {bundle}")

    try:
        run_parameters_file(bundle)
    except Exception as exc:  # pragma: no cover - CLI guard
        print(f"[fd-bump] run failed: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())

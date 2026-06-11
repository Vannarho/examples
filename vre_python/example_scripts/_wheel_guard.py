#!/usr/bin/env python3

from __future__ import annotations

import importlib.metadata as metadata
import os
from pathlib import Path


_BUILD_ENV_VARS = (
    "VRE_PYBIND_FORCE_BUILD_DIR",
    "VRE_PYBIND_BUILD_DIR",
    "VRE_NOTEBOOK_BUILD_ROOT",
)


def _env_truthy(name: str) -> bool:
    return os.environ.get(name, "").strip() in {"1", "true", "TRUE", "yes", "YES", "on", "ON"}


def _assert_inside(path: Path, root: Path, module_name: str) -> None:
    try:
        path.relative_to(root)
    except ValueError as exc:
        raise RuntimeError(
            f"{module_name} resolved outside the installed vannarho-risk-engine wheel: "
            f"{path} is not under {root}"
        ) from exc


def require_installed_vre():
    if _env_truthy("VRE_PYBIND_FORCE_BUILD_DIR"):
        raise RuntimeError("VRE Python examples are wheel-only; VRE_PYBIND_FORCE_BUILD_DIR is not supported")
    for name in _BUILD_ENV_VARS[1:]:
        if os.environ.get(name):
            raise RuntimeError(f"VRE Python examples are wheel-only; {name} is not supported")

    try:
        dist = metadata.distribution("vannarho-risk-engine")
    except metadata.PackageNotFoundError as exc:
        raise RuntimeError("vannarho-risk-engine is not installed; install the pybind wheel first") from exc

    import VRE
    import VREData
    import vre

    dist_root = Path(dist.locate_file("")).resolve()
    modules = (("VRE", VRE), ("VREData", VREData), ("vre", vre))
    for module_name, module in modules:
        module_file = Path(getattr(module, "__file__", "")).resolve()
        if any(part == "build" for part in module_file.parts):
            raise RuntimeError(f"{module_name} resolved from a build tree: {module_file}")
        _assert_inside(module_file, dist_root, module_name)

    print(f"[wheel] distribution={dist.metadata['Name']} {dist.version}")
    print(f"[wheel] root={dist_root}")
    print(f"[wheel] module={Path(getattr(VRE, '__file__', '')).resolve()}")
    return VRE

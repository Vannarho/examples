#!/usr/bin/env python3

from __future__ import annotations

import contextlib
import importlib.metadata as metadata
import os
import platform
import re
import shutil
import subprocess
import sys
import tempfile
import tomllib
from pathlib import Path


NOTEBOOKS_ROOT = Path(__file__).resolve().parent
QLE_DEVICE_LABEL = "@qle.computeenvironment.testEnvironmentInit"
_BUILD_ENV_VARS = (
    "VRE_PYBIND_FORCE_BUILD_DIR",
    "VRE_PYBIND_BUILD_DIR",
    "VRE_NOTEBOOK_BUILD_ROOT",
)


def _env_truthy(name: str) -> bool:
    return os.environ.get(name, "").strip() in {"1", "true", "TRUE", "yes", "YES", "on", "ON"}


def _external_compute_device_priority(device_name: str) -> int:
    if device_name.startswith("Metal/"):
        return 0
    if device_name.startswith("CUDA/"):
        return 1
    if device_name.startswith("OpenCL/"):
        return 2
    return 3


def _sort_external_compute_devices(device_names: list[str]) -> list[str]:
    ordered = {name.strip() for name in device_names if name and name.strip()}
    return sorted(ordered, key=lambda name: (_external_compute_device_priority(name), name))


def _locate_qle_core_exe() -> Path | None:
    override = os.environ.get("VRE_QLE_CORE_EXE", "").strip()
    candidates = [Path(override).expanduser()] if override else []
    for candidate in candidates:
        if candidate.is_file():
            return candidate.resolve()
    return None


def _detect_vre_advertised_compute_devices() -> list[str]:
    exe = _locate_qle_core_exe()
    if exe is None:
        return []
    try:
        output = subprocess.check_output(
            [exe.as_posix(), f"--run_test={QLE_DEVICE_LABEL}", "-l", "message", "-r", "confirm"],
            stderr=subprocess.STDOUT,
            text=True,
            timeout=20,
        )
    except Exception:
        return []
    plain = re.sub(r"\x1b\[[0-9;]*m", "", output)
    return _sort_external_compute_devices(re.findall(r"device '([^']+)'", plain))


def _detect_darwin_metal_devices() -> list[str]:
    swift_probe = """
import Metal

func sanitize(_ value: String) -> String {
    value
        .replacingOccurrences(of: " ", with: "_")
        .replacingOccurrences(of: "/", with: "_")
}

for device in MTLCopyAllDevices() {
    let deviceName = sanitize(device.name)
    let registryId = String(device.registryID, radix: 16, uppercase: true)
    print("Metal/Apple/\\(deviceName)#0x\\(registryId)")
}
"""
    try:
        output = subprocess.check_output(
            ["swift", "-e", swift_probe],
            stderr=subprocess.DEVNULL,
            text=True,
            timeout=5,
        )
    except Exception:
        return []
    return _sort_external_compute_devices(output.splitlines())


def print_banner(title: str) -> None:
    line = "+" + "-" * 53 + "+"
    print(line)
    print(f"| {title:<51} |")
    print(line)


def _import_installed_vre():
    try:
        dist = metadata.distribution("vannarho-risk-engine")
    except metadata.PackageNotFoundError as exc:
        raise RuntimeError("vannarho-risk-engine is not installed; install the pybind wheel first") from exc

    import VRE
    import VREData
    import vre

    dist_root = Path(dist.locate_file("")).resolve()
    executable = Path(sys.executable).resolve()
    prefix = Path(sys.prefix).resolve()
    modules = (("VRE", VRE), ("VREData", VREData), ("vre", vre))
    for module_name, module in modules:
        module_path = Path(getattr(module, "__file__", "")).resolve()
        if any(part == "build" for part in module_path.parts):
            raise RuntimeError(f"Notebook examples must not import {module_name} from a build tree: {module_path}")
        try:
            module_path.relative_to(dist_root)
        except ValueError as exc:
            raise RuntimeError(
                f"Notebook examples must import {module_name} from the installed "
                f"vannarho-risk-engine wheel, not {module_path}"
            ) from exc
    module_path = Path(getattr(VRE, "__file__", "")).resolve()
    print(f"[wheel] distribution={dist.metadata['Name']} {dist.version}")
    print(f"[wheel] root={dist_root}")
    print(f"[wheel] python={executable}")
    print(f"[wheel] prefix={prefix}")
    print(f"[wheel] module={module_path}")
    return VRE


def _import_vre_runtime():
    if _env_truthy("VRE_PYBIND_FORCE_BUILD_DIR"):
        raise RuntimeError("Notebook examples are wheel-only; VRE_PYBIND_FORCE_BUILD_DIR is not supported")
    for name in _BUILD_ENV_VARS[1:]:
        if os.environ.get(name):
            raise RuntimeError(f"Notebook examples are wheel-only; {name} is not supported")
    return _import_installed_vre()


def _find_notebook_example_root(bundle_path: Path) -> Path:
    for candidate in bundle_path.parents:
        if (candidate / "vre.ipynb").exists():
            return candidate
    return bundle_path.parent


@contextlib.contextmanager
def _pushd(path: Path):
    previous = Path.cwd()
    os.chdir(path)
    try:
        yield
    finally:
        os.chdir(previous)


@contextlib.contextmanager
def _temporary_env(overrides: dict[str, str] | None):
    if not overrides:
        yield
        return
    previous = {key: os.environ.get(key) for key in overrides}
    try:
        for key, value in overrides.items():
            os.environ[key] = str(value)
        yield
    finally:
        for key, value in previous.items():
            if value is None:
                os.environ.pop(key, None)
            else:
                os.environ[key] = value


def _set_setup_string(source: str, key: str, value: str) -> str:
    pattern = rf'(?m)^(\s*{re.escape(key)}\s*=\s*").*(".*)$'
    replacement = rf'\1{value}\2'
    updated, count = re.subn(pattern, replacement, source, count=1)
    if count == 0:
        raise RuntimeError(f"Could not rewrite setup.{key} in staged bundle")
    return updated


def _sync_notebook_output_alias(bundle_path: Path) -> None:
    bundle = tomllib.loads(bundle_path.read_text(encoding="utf-8"))
    setup = bundle.get("setup", {})
    output_path = setup.get("outputPath")
    if not isinstance(output_path, str) or not output_path:
        return

    requested = (Path.cwd() / output_path).resolve()
    parts = list(Path(output_path).parts)
    if not parts:
        return
    parts[0] = parts[0].lower()
    fallback = (Path.cwd() / Path(*parts)).resolve()

    if requested == fallback or not fallback.exists():
        return
    try:
        if requested.exists() and fallback.exists() and os.path.samefile(requested, fallback):
            return
    except OSError:
        pass

    if fallback.is_dir():
        requested.mkdir(parents=True, exist_ok=True)
        for child in fallback.iterdir():
            target = requested / child.name
            if child.is_dir():
                shutil.copytree(child, target, dirs_exist_ok=True)
            else:
                try:
                    if target.exists() and os.path.samefile(child, target):
                        continue
                except OSError:
                    pass
                shutil.copy2(child, target)
        return

    requested.parent.mkdir(parents=True, exist_ok=True)
    try:
        if requested.exists() and os.path.samefile(fallback, requested):
            return
    except OSError:
        pass
    shutil.copy2(fallback, requested)


@contextlib.contextmanager
def _staged_bundle_for_notebook_root(bundle_path: Path):
    notebook_root = _find_notebook_example_root(bundle_path)
    bundle = tomllib.loads(bundle_path.read_text(encoding="utf-8"))
    setup = bundle.get("setup", {})
    input_path = setup.get("inputPath")
    if not isinstance(input_path, str) or not input_path:
        raise RuntimeError(f"Bundle is missing setup.inputPath: {bundle_path}")

    resolved_input_path = (bundle_path.parent / input_path).resolve()
    staged_input_path = os.path.relpath(resolved_input_path, notebook_root)
    staged_text = bundle_path.read_text(encoding="utf-8")
    staged_text = _set_setup_string(staged_text, "inputPath", staged_input_path)

    with tempfile.NamedTemporaryFile(
        mode="w",
        encoding="utf-8",
        dir=notebook_root,
        prefix=f".wheel_runtime_{bundle_path.stem}_",
        suffix=bundle_path.suffix,
        delete=False,
    ) as handle:
        handle.write(staged_text)
        staged_bundle = Path(handle.name)

    try:
        yield notebook_root, staged_bundle
    finally:
        staged_bundle.unlink(missing_ok=True)


def _detect_external_compute_device() -> str:
    for env_name in ("EXTERNAL_COMPUTE_DEVICE", "VRE_CG_EXTERNAL_COMPUTE_DEVICE"):
        override = os.environ.get(env_name, "").strip()
        if override:
            return override

    system = platform.system()

    if system == "Linux":
        try:
            output = subprocess.check_output(
                ["nvidia-smi", "--query-gpu=name", "--format=csv,noheader"],
                stderr=subprocess.DEVNULL,
                text=True,
                timeout=2,
            )
        except Exception as exc:
            raise RuntimeError("No NVIDIA GPU detected; set EXTERNAL_COMPUTE_DEVICE to override") from exc
        names = [line.strip() for line in output.splitlines() if line.strip()]
        if not names:
            raise RuntimeError("No NVIDIA GPU detected; set EXTERNAL_COMPUTE_DEVICE to override")
        return f"CUDA/NVIDIA/{names[0]}"

    if system == "Darwin":
        advertised = _detect_vre_advertised_compute_devices()
        if advertised:
            return advertised[0]

        metal_devices = _detect_darwin_metal_devices()
        if metal_devices:
            return metal_devices[0]

        try:
            import pyopencl as cl  # type: ignore

            for platform_ in cl.get_platforms():
                devices = [device for device in platform_.get_devices() if device.type & cl.device_type.GPU]
                if devices:
                    vendor = platform_.vendor or platform_.name or "Apple"
                    return f"OpenCL/{vendor}/{devices[0].name}"
        except Exception:
            pass

        raise RuntimeError("No VRE-compatible Apple GPU detected; set EXTERNAL_COMPUTE_DEVICE to override")

    raise RuntimeError(f"Unsupported platform for GPU autodetection: {system}")


def _patch_external_device_param(path: Path, device_str: str) -> None:
    if path.suffix.lower() != ".xml":
        text = path.read_text(encoding="utf-8")
        patterns = (
            (r'(?m)^(\s*ExternalComputeDevice\s*=\s*").*(".*)$', r"\1" + device_str + r"\2"),
            (r'(?m)^(\s*xvaCgExternalComputeDevice\s*=\s*").*(".*)$', r"\1" + device_str + r"\2"),
            (r'(?m)^(\s*ExternalComputeDevice\s*:\s*).*$' , r"\1" + device_str),
            (r'(?m)^(\s*xvaCgExternalComputeDevice\s*:\s*).*$' , r"\1" + device_str),
            (r'("ExternalComputeDevice"\s*:\s*")[^"]*(")', r"\1" + device_str + r"\2"),
            (r'("xvaCgExternalComputeDevice"\s*:\s*")[^"]*(")', r"\1" + device_str + r"\2"),
        )
        updated = text
        for pattern, replacement in patterns:
            updated = re.sub(pattern, replacement, updated)
        if updated != text:
            path.write_text(updated, encoding="utf-8")
        return

    import xml.etree.ElementTree as ET

    tree = ET.parse(path)
    root = tree.getroot()
    changed = False
    names = {"ExternalComputeDevice", "xvaCgExternalComputeDevice"}
    bool_names = {"UseExternalComputeDevice", "xvaCgUseExternalComputeDevice"}

    for parameter in root.iter("Parameter"):
        name = parameter.get("name")
        if name in names:
            parameter.text = device_str
            changed = True
        if name in bool_names:
            parameter.text = "true"
            changed = True

    if not changed:
        params = root.find(".//Parameters") or root
        for name in names:
            ET.SubElement(params, "Parameter", name=name).text = device_str
        for name in bool_names:
            ET.SubElement(params, "Parameter", name=name).text = "true"

    tree.write(path, encoding="utf-8", xml_declaration=True)


def _gpu_patch_targets(bundle_path: Path) -> list[Path]:
    targets = [bundle_path]
    bundle = tomllib.loads(bundle_path.read_text(encoding="utf-8"))
    input_path = bundle.get("setup", {}).get("inputPath")
    if isinstance(input_path, str) and input_path:
        bundle_root = (bundle_path.parent / input_path).resolve()
        if bundle_root.is_dir():
            for candidate in bundle_root.rglob("*"):
                if candidate.suffix.lower() not in {".toml", ".json", ".yaml", ".yml", ".xml"}:
                    continue
                if not candidate.is_file():
                    continue
                try:
                    text = candidate.read_text(encoding="utf-8")
                except Exception:
                    continue
                if "ExternalComputeDevice" in text or "xvaCgExternalComputeDevice" in text:
                    targets.append(candidate)

    unique_targets: list[Path] = []
    seen: set[Path] = set()
    for target in targets:
        resolved = target.resolve()
        if resolved in seen:
            continue
        seen.add(resolved)
        unique_targets.append(target)
    return unique_targets


@contextlib.contextmanager
def _gpu_patched_bundle(bundle_path: Path):
    device = _detect_external_compute_device()
    backups: list[tuple[Path, Path]] = []
    try:
        for target in _gpu_patch_targets(bundle_path):
            backup = target.with_name(target.name + ".bak_gpu_patch")
            if backup.exists():
                backup.unlink()
            shutil.copy2(target, backup)
            backups.append((target, backup))
            _patch_external_device_param(target, device)
        print(f"[gpu] ExternalComputeDevice = {device}")
        yield device
    finally:
        for target, backup in backups:
            if backup.exists():
                shutil.move(str(backup), str(target))


def run_parameters_file(
    parameters_file: str | Path,
    *,
    env_overrides: dict[str, str] | None = None,
    gpu_dynamic: bool = False,
    gpu_optional: bool = False,
):
    bundle_path = Path(parameters_file).resolve()
    if not bundle_path.is_file():
        raise FileNotFoundError(bundle_path)

    with _staged_bundle_for_notebook_root(bundle_path) as (run_root, staged_bundle), _pushd(run_root), _temporary_env(env_overrides):
        if gpu_dynamic:
            try:
                with _gpu_patched_bundle(staged_bundle):
                    return _run_parameters_file_here(staged_bundle)
            except RuntimeError as exc:
                if gpu_optional:
                    print(f"[gpu] Skipping {staged_bundle.name}: {exc}")
                    return None
                raise
        return _run_parameters_file_here(staged_bundle)


def _run_parameters_file_here(bundle_path: Path):
    VRE = _import_vre_runtime()
    params = VRE.vrea.Parameters()
    params.fromFile(bundle_path.name)
    app = VRE.vrea.VREApp(params)
    app.run()
    _sync_notebook_output_alias(bundle_path)
    try:
        print(f"[wheel] outputs: {app.outputsPath()}")
    except Exception:
        pass
    return app

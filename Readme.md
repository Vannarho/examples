# Vannarho Risk Engine - Python Distributions and Examples

Vannarho Risk Engine (VRE) is aimed at establishing a transparent peer-reviewed framework for pricing and risk analysis that can serve as

* a benchmarking, validation, training, teaching reference
* an extensible foundation for tailored risk solutions

VRE provides:

* contemporary risk analytics and value adjustments (XVAs)
* interfaces for trade/market data and system configuration (API and XML)
* simple application launchers in Jupyter
* various examples that demonstrate typical use cases
* comprehensive test suites

VRE is a c++23 library based on

* [QuantLib](http://quantlib.org), the open source library
* [The Open Source Risk Engine](http://www.opensourcerisk.org)
* [Enzyme AD](https://enzyme.mit.edu)
* [pybind11](https://github.com/pybind/pybind11)

It extends QuantLib and The Open Source Risk Engine in terms of simulation models, financial instruments and pricing engines. For example:

* Updated SACCR, SACVA (SA and SBM), FTRB (SA) modules with broad product coverage
* Refactored C++23 codebase
* JIT AD kernels for 10-25x speed up vs vanilla AD
* SIMD support (initially NEON with AVX)
* Updated engines
* New Metal and CUDA GPU modules (native CE and multi-GPU upcoming)
* Fast sensitivities for a broad range of products using AAD and GPU

# Vannarho Risk Engine — Python Binary Wheels

[![Platforms](https://img.shields.io/badge/wheels-linux%20%7C%20macOS%20%7C%20windows-blue)](#supported-platforms)
[![License: BSD-3-Clause](https://img.shields.io/badge/license-BSD--3--Clause-blue.svg)](../LICENSE)

High‑performance quantitative finance toolkit exposing VRE (Vannarho Risk Engine) to Python. Ships as prebuilt, self‑contained binary wheels that bundle core native libraries (QuantLib, QuantExt, VREData, VREAnalytics) behind a single `VRE` extension.

* Import path: `import VRE`

> Note: This is a binary distribution. Building from source is not required for end‑users and is not officially supported outside CI.

# Vannarho Risk Engine – Example Repository Setup

These instructions explain how to clone the example repo and install the appropriate **Vannarho Risk Engine** wheel.

---

## 1. Clone the repository

```bash
git clone https://github.com/Vannarho/examples.git
cd examples
```

This repository contains Jupyter notebooks and scripts demonstrating how to use the Vannarho Risk Engine.

---

## 2. Create and activate a virtual environment

**macOS / Linux:**

```bash
python3 -m venv venv
source venv/bin/activate
```

**Windows (PowerShell):**

```bash
python -m venv venv
venv\Scripts\Activate.ps1
```

---

## 3. Install base dependencies

```bash
pip install -r requirements.txt
```

If no `requirements.txt` file is provided, ensure you have at least:

```bash
pip install numpy pandas matplotlib
```

---

# VREPython Wheel Variants

The Vannarho Risk Engine Python package ships as binary wheels that bundle
the various binaries exposed as`VRE`. We publish two flavours so that users can choose between the kernel‑accelerated runtime and a leaner baseline build:

| Variant | Version suffix | Wheel snippet | What’s included | Typical usage |
| --- | --- | --- | --- | --- |
| **Kernel / accelerated** | `.post1` | `vannarho_risk_engine-<ver>.post1-...whl` | Pre‑compiled Enzyme JIT kernels, SIMD acceleration, GPU backends (Metal on macOS, CUDA on Windows/Linux) plus the LLVM Enzyme plugin and related runtime assets. | Users who need the fastest CG/AAD path, GPU offload, or want feature parity with the full C++ stack. |
| **Baseline / no kernels** | `.post2` | `vannarho_risk_engine-<ver>.post2-...whl` | Core VRE libraries and pybind11 extension only. No Enzyme plugin, pre‑compiled kernels, or GPU backends. | Air‑gapped/regulated installs, CPU‑only research VMs, CI pipelines that prefer the smallest set of native dependencies. |

Both wheels expose the same Python surface; only the performance paths and
bundled runtimes differ.

## `.post1` — Kernel‑accelerated wheels

The `.post1` series is produced by the `*_cpu_kernels` scripts/presets:

* macOS/Linux: `mac_build_wheels_cpu_kernels.sh`, `linux_build_wheels_cpu_kernels.sh`
* Windows: `build_wheels_cpu_kernels.ps1`

Key traits:

* **Enzyme kernels baked in** – We build the CG/AAD CPU kernels ahead of time,
  bundle the LLVM Enzyme plugin, and ship the metadata required to JIT new
  kernels at runtime. This is what unlocks the 20‑25x speed‑ups advertised in
  the main README.
* **SIMD ready** – The kernels are compiled with the repo’s NEON/AVX plan so
  vectorised CPU lanes light up without extra configuration.
* **GPU backends bundled** – macOS wheels enable the Metal device policy out of
  the box; Windows/Linux wheels include the CUDA‑based kernels and expect a
  CUDA‑capable driver/runtime (support it not extensive, requires recent CUDA runtime). When the GPU runtime is present and supported, the wheel automatically routes eligible CG workloads to the device.
* **Extra runtime payload** – Expect larger wheels because they contain the
  Enzyme shared object (`LLVMEnzyme-*.dylib/.so/.dll`), GPU kernels, and license
  notices.

Choose `.post1` if you want every performance lever that exists in the C++
build: scripted CG runs, SACVA GPU offload on Metal or CUDA, SIMD (NEON and AVX2) or if you work on kernel development and need the packaged LLVM/Enzyme bits for tracing.

## `.post2` — Baseline wheels without kernels

The `.post2` series is the safest option when you just need deterministic VRE
pricing APIs without the Enzyme stack:

* Ideal for VMs without GPUs, corporate laptops where installing Metal/CUDA
  runtimes is restricted, or CI jobs where deterministic CPU behaviour is more
  important than throughput.

Python APIs remain identical, so you can move between `.post2` and `.post1`
depending on the environment without code changes.

## Picking the right wheel

* **Need GPU acceleration (Metal or CUDA) or the lowest latency CG path?**  
  Install `.post1`.
* **Running in containers/CI or on hardware without admin rights?**  
  Install `.post2` to avoid the extra GPU/LLVM payload.
* **Validating calculations between variants?**  
  Keep both versions handy and switch via pip (see below) to ensure parity.

## Installing a specific variant

Wheels are versioned using [PEP 440](https://peps.python.org/pep-0440/) post
releases. Append `.post1` or `.post2` when calling `pip install`:

```bash
# Kernel / GPU enabled wheel
python -m pip install "vannarho-risk-engine==0.5.0.post1"

# Baseline, no kernels
python -m pip install "vannarho-risk-engine==0.5.0.post2"
```

When testing locally, you can also install from the build artifacts:

```bash
# From this repo
pip install --force-reinstall \
  VREPython/wheelhouse/cpu_kernels/vannarho_risk_engine-0.5.0.post1-<tag>.whl
```

`pip install vannarho-risk-engine` (without a suffix) will install whichever
variant is newest/available for your platform, so pin the explicit post release
if you care which runtime you receive.

## 4. Install the appropriate Vannarho Risk Engine wheel

Choose the correct wheel for your use case (both are macOS arm64 builds; Linux
and Windows artifacts follow the same `.post1`/`.post2` pattern):

| Variant | File | Description |
|----------|------|--------------|
| **JIT Enzyme Kernels** | `vannarho_risk_engine-0.5.0.post1-cp313-cp313-macosx_26_0_arm64.whl` | Includes Enzyme-based JIT kernel compilation, SIMD-optimised CPU kernels, and GPU workflows (Metal on macOS, CUDA on Windows/Linux). |
| **Vanilla Engine** | `vannarho_risk_engine-0.5.0.post2-cp313-cp313-macosx_26_0_arm64.whl` | Standard runtime build without Enzyme, GPU, or precompiled kernel payloads. |

### Install one of the two

Replace the version/tag below with the specific release you plan to use:

```bash
# JIT Enzyme build
pip install https://github.com/Vannarho/examples/releases/download/v0.5.0/vannarho_risk_engine-0.5.0.post1-cp313-cp313-macosx_26_0_arm64.whl

# Vanilla build
pip install https://github.com/Vannarho/examples/releases/download/v0.5.0/vannarho_risk_engine-0.5.0.post2-cp313-cp313-macosx_26_0_arm64.whl
```

## 5. Verify installation

Check that the package imports correctly:

```bash
python -c "import VRE; import vannarho_risk_engine; print(vannarho_risk_engine.__version__)"
```

Expected output:

```
0.5.0.post1
```

or

```
0.5.0.post2
```

No additional system packages are required; the wheel includes native
dependencies. If you see a compiler invocation during install, you are likely
installing from a source tree or an unsupported environment — see Troubleshooting.

## Quickstart

```python
import VRE

# Print a few top-level attributes and verify a minimal component is available
print("VRE loaded. Submodules:", [m for m in dir(VRE) if m in ("ql", "qle", "vred", "vrea")])

# Example: construct a QuantLib Date via the ql submodule
Date = VRE.ql.Date
today = Date.todaysDate()
print("Today:", today)
```

## Supported Platforms

Binary wheels are provided for:

* CPython 3.13
* Linux x86_64 (manylinux / musllinux where applicable — vanilla and kernel variants; CUDA enablement lands in an upcoming release)
* macOS arm64 (universal2 when possible with vanilla and kernel variants, including Metal GPU support)
* Windows x86_64 (vanilla variant today, CUDA support coming in a future post release)

If your platform is not listed, pip may report “No matching distribution found”.

## Project Links

* Documentation (in‑repo): `Docs/` and `RELEASE.md`
* Examples & notebooks: placeholder <https://github.com/Vannarho/examples>
* Issue tracker: <https://github.com/Vannarho/examples/issues>
* Changelog: `CHANGELOG.md` (to be added)

## Security & Support

* Security contact: <info@vannarho.com>
* For general support, open a GitHub issue with platform, Python version, wheel filename, and the output of `pip debug --verbose`.

## License & Notices

Distributed under the BSD‑3‑Clause license. See `LICENSE` and `NOTICE` for details and third‑party attributions.

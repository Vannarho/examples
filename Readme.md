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

* Updated SACCR, SACVA (SA and SBM), FTRB (SA and SBM) modules with broad product coverage
* Refactored C++23 codebase
* JIT AD kernels for 25x speed up vs vanilla AD
* SIMD support (initially NEON with AVX / AVX512 upcoming)
* Updated engines e.g. crossgammadelta pricing engine
* New Metal and CUDA GPU modules (native CE and multi-GPU upcoming)
* Fast sensitivities for a broad range of products using AAD and GPU

# Vannarho Risk Engine — Python Binary Wheels

[![Platforms](https://img.shields.io/badge/wheels-linux%20%7C%20macOS%20%7C%20windows-blue)](#supported-platforms)
[![License: BSD-3-Clause](https://img.shields.io/badge/license-BSD--3--Clause-blue.svg)](../LICENSE)

High‑performance quantitative finance toolkit exposing VRE (Vannarho Risk Engine) to Python. Ships as prebuilt, self‑contained binary wheels that bundle core native libraries (QuantLib, QuantExt, VREData, VREAnalytics) behind a single `VRE` extension.

* Import path: `import VRE`
* Submodules: `VRE.ql`, `VRE.qle`, `VRE.vred`, `VRE.vrea`

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

## 2. (Optional) Create and activate a virtual environment

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

## 4. Install the appropriate Vannarho Risk Engine wheel

Choose the correct wheel for your use case (both are macOS arm64 builds):

| Variant | File | Description |
|----------|------|--------------|
| **JIT Enzyme Kernels** | `vannarho_risk_engine-0.0.1.post1-cp313-cp313-macosx_26_0_arm64.whl` | Includes Enzyme-based JIT kernel compilation for accelerated sensitivity and GPU workflows. |
| **Vanilla Engine** | `vannarho_risk_engine-0.0.1.post2-cp313-cp313-macosx_26_0_arm64.whl` | Standard runtime build without Enzyme or JIT components. |

### Install one of the two

```bash
# JIT Enzyme build
pip install https://github.com/Vannarho/examples/releases/download/v0.0.1/vannarho_risk_engine-0.0.1.post1-cp313-cp313-macosx_26_0_arm64.whl

# Vanilla build
pip install https://github.com/Vannarho/examples/releases/download/v0.0.1/vannarho_risk_engine-0.0.1.post2-cp313-cp313-macosx_26_0_arm64.whl
```

## 5. Verify installation

Check that the package imports correctly:

```bash
python -c "import vannarho_risk_engine; print(vannarho_risk_engine.__version__)"
```

Expected output:

```
0.0.1.post1
```

or

```
0.0.1.post2
```

No additional system packages are required; the wheel includes native dependencies. If you see a compiler invocation during install, you are likely installing from a source tree or an unsupported environment — see Troubleshooting.

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
* Linux x86_64 (manylinux / musllinux where applicable - "vanilla" and JIT Kernel version - CUDA support in an upcoming release)
* macOS arm64 (universal2 where applicable with "vanilla" and JIT Kernel versions including Metal GPU support)
* Windows x86_64 ("vanilla" version with CUDA support in an upcoming release)

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

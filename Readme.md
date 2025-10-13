# VRE

Vannarho Risk Engine (VRE) is aimed at establishing a transparent peer-reviewed framework for pricing and risk
analysis that can serve as

* a benchmarking, validation, training, teaching reference
* an extensible foundation for tailored risk solutions

VRE provides:

* contemporary risk analytics and value adjustments (XVAs)
* interfaces for trade/market data and system configuration (API and XML)
* simple application launchers in Excel, LibreOffice, Python, Jupyter
* various examples that demonstrate typical use cases
* comprehensive test suites

VRE is a c++23 library built on top of:

* [QuantLib](http://quantlib.org), the open source library
* [The Open Source Risk Engine](http://www.opensourcerisk.org)

It extends QuantLib and The Open Source Risk Engine in terms of simulation models, financial instruments and pricing engines. For example:

* Updated SACCR, SACVA (SA and SBM), FTRB (SA and SBM) modules with broad product and test coverage
* Refactored c++23 codebase
* New CUDA module handling multiple GPUs
* Fast sensitivities for a broad range of trades using AAD and GPU

# Vannarho Risk Engine — Python Binary Wheels

[![PyPI](https://img.shields.io/pypi/v/vannarho-risk-engine.svg)](https://pypi.org/project/vannarho-risk-engine/)
[![Python Versions](https://img.shields.io/pypi/pyversions/vannarho-risk-engine.svg)](https://pypi.org/project/vannarho-risk-engine/)
[![Platforms](https://img.shields.io/badge/wheels-linux%20%7C%20macOS%20%7C%20windows-blue)](#supported-platforms)
[![License: BSD-3-Clause](https://img.shields.io/badge/license-BSD--3--Clause-blue.svg)](../LICENSE)

High‑performance quantitative finance toolkit exposing VRE (Vannarho Risk Engine) to Python. Ships as prebuilt, self‑contained binary wheels that bundle core native libraries (QuantLib, QuantExt, VREData, VREAnalytics) behind a single `VRE` extension.

* Import path: `import VRE`
* Submodules: `VRE.ql`, `VRE.qle`, `VRE.vred`, `VRE.vrea`

> Note: This is a binary distribution. Building from source is not required for end‑users and is not officially supported outside CI.

## Installation

Stable releases from PyPI:

```
python -m pip install --upgrade pip
python -m pip install vannarho-risk-engine
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

* CPython 3.9–3.13
* Linux x86_64 (manylinux / musllinux where applicable)
* macOS arm64 and x86_64 (universal2 where applicable)
* Windows x86_64

If your platform is not listed, pip may report “No matching distribution found”.

## Examples and Notebooks

End‑to‑end examples, tutorials, and Jupyter notebooks live in a companion repository:

* <https://github.com/Vannarho/examples>

This repo includes sample input data, portfolio XMLs, curve configurations, and small walkthroughs for pricing, exposure profiles, and XVA workflows.

## Troubleshooting

* ImportError: “DLL load failed” or “undefined symbol”
  * Ensure you installed a prebuilt wheel (`pip install vannarho-risk-engine`).
  * On Linux, avoid mixing system Python with wheels built for a different glibc/musl variant. Use the official CPython from python.org/pyenv.
  * Check: `python -m pip show vannarho-risk-engine` and `pip debug --verbose`.

* Build starts during pip install
  * You’re likely installing from a source checkout or on an unsupported platform. Prefer the published wheels. If you must build from source, see `VREPython/tutorials.015.build_posix.md`.

* Apple Silicon cross‑install
  * On arm64 macOS, prefer a native arm64 Python. If you run an x86_64 Python under Rosetta, pip will fetch the x86_64 wheel.

## Project Links

* Documentation (in‑repo): `Docs/` and `RELEASE.md`
* Examples & notebooks: placeholder <https://github.com/Vannarho/examples>
* Issue tracker: <https://github.com/Vannarho/examples/issues>

## Contributing

Contributions are welcome. See `CONTRIBUTING.md` and `AGENTS.md` for code style, test policy, and development setup. For packaging changes, coordinate via issues to ensure cross‑platform compatibility.

## Security & Support

* Security contact: <security@vannarho.com>
* For general support, open a GitHub issue with platform, Python version, wheel filename, and the output of `pip debug --verbose`.

## License & Notices

Distributed under the BSD‑3‑Clause license. See `LICENSE` and `NOTICE` for details and third‑party attributions.

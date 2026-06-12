# Vannarho Risk Engine Python Examples

This repository contains the Python wheel examples for the Vannarho Risk Engine
(VRE). It is intentionally the Python examples surface itself: there is no
nested `vre_python/` directory.

The examples run against the installed `vannarho-risk-engine` pybind wheel only.
They do not require `PYTHONPATH`, local source-tree imports, or in-repo C++
build artifacts. The script and notebook entrypoints fail closed if VRE binaries
resolve outside the installed wheel distribution.

## How this relates to Vannarho RaaS

[Vannarho Risk Results as a Service](https://vannarho.com/) is the managed
platform that turns risk analytics into governed results: schemas, tolerances,
lineage, evidence, approvals, delivery channels, and regulator-ready narratives.
The public [Platform Overview](https://vannarho.com/platform/index.html)
describes RaaS as a governed risk-results platform for banks, insurers, and
regulated institutions. The
[API User Guide](https://vannarho.com/api-guide/index.html) explains how client
systems submit trades, market data, and configurations, then consume governed
results and evidence through typed APIs.

These examples sit one layer lower. They let developers, quants, validators, and
prospective clients inspect the deterministic engine that underpins the RaaS
platform. RaaS owns intake, control, scheduling, result serving, explainability,
and client operation; VRE remains the deterministic compute and reporting
engine. Use this repository to explore the kernel behavior locally before
moving to managed RaaS workflows.

## What you can investigate

Use these examples to inspect:

- installed-wheel import and pybind API behavior
- conventions, calendars, indices, market data, and parser surfaces
- pricing and cashflow behavior for core products
- curve construction and interest-rate model examples
- exposure, XVA, collateral, initial margin, SIMM, SA-CVA, and market-risk smoke
  paths
- how engine outputs can be parsed and summarized in notebooks
- how jurisdiction-scoped regulatory narratives can be prototyped without
  requiring the managed RaaS service layer

This is not the full managed RaaS platform. It does not include tenant control
planes, governed approvals, production API routing, BigQuery serving layers, or
client data isolation. For those flows, start with the website guides above.

## Example scripts

Run the aggregate script runner with `python run.py`. It executes the following
root-level examples from `example_scripts/`:

| Script | Coverage |
| --- | --- |
| `commodityforward.py` | Commodity forward setup, pricing, and manual PV comparison. |
| `conventions.py` | XML convention loading, overnight-index conventions, and curve-handle use. |
| `gaussian1d-models.py` | Interest-rate model helpers, GSR/Markov examples, calibration diagnostics, and Bermudan/CMS-style outputs. |
| `log.py` | Wheel import proof and VRE logging surface. |
| `swap.py` | Interest-rate swap setup, curve-backed pricing, fair-rate checks, and quote-bump repricing. |

## Notebooks

The notebooks are executable examples, not static screenshots. They are intended
to be run in a clean virtual environment with an installed wheel.

| Notebook | Coverage |
| --- | --- |
| `notebooks/example_1/hello.ipynb` | Minimal installed-wheel import check. |
| `notebooks/example_1/vre.ipynb` | Basic VRE run smoke test. |
| `notebooks/example_2/vre.ipynb` | Collateral and margin smoke path. |
| `notebooks/example_3/vre.ipynb` | Classic exposure smoke path. |
| `notebooks/example_4/vre.ipynb` | PCA input case. |
| `notebooks/example_5/vre.ipynb` | Dynamic initial margin example. |
| `notebooks/example_6/vre.ipynb` | Exposure analytics smoke path. |
| `notebooks/example_7/vre.ipynb` | SIMM smoke path. |
| `notebooks/example_8/vre.ipynb` | Market-risk wrappers covering scenario, historical simulation VaR, P&L, and P&L explain paths. |
| `notebooks/example_9/vre.ipynb` | Market data smoke path. |
| `notebooks/example_10/vre.ipynb` | SA-CVA smoke runner, including AAD and GPU-backed cases where available. |
| `notebooks/example_11/vre.ipynb` | Equity and commodity SA-CVA smoke runner. |
| `notebooks/southern_cross_cross_border/vre.ipynb` | Standalone Southern Cross cross-border pybind example with an Australia-scoped stage, a multi-jurisdiction regulatory slice, AUD-BBSW/AUD-AONIA parser checks, and synthetic IMA P&L/backtesting inputs. |

## macOS wheel install

The current promoted wheels are attached to the
[`vre-python-v0.14.0`](https://github.com/Vannarho/examples/releases/tag/vre-python-v0.14.0)
release. They were built from the VRE `v0.14.0` source release using the macOS
Metal build preset.

- Python 3.13 macOS arm64:
  `vannarho_risk_engine-0.14.0-cp313-cp313-macosx_26_0_arm64.whl`
- Python 3.14 macOS arm64:
  `vannarho_risk_engine-0.14.0-cp314-cp314-macosx_26_0_arm64.whl`

For Python 3.13:

```bash
python3.13 -m venv .venv
. .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
mkdir -p wheelhouse
gh -R Vannarho/examples release download vre-python-v0.14.0 \
  -p vannarho_risk_engine-0.14.0-cp313-cp313-macosx_26_0_arm64.whl \
  -D wheelhouse
python -m pip install wheelhouse/vannarho_risk_engine-0.14.0-cp313-cp313-macosx_26_0_arm64.whl
```

## Run scripts

```bash
PYTHONPATH= python run.py
```

## Run notebooks

```bash
python -m ipykernel install --user --name vre-wheel-313 --display-name "VRE wheel cp313"

for nb in \
  notebooks/example_1/hello.ipynb \
  notebooks/example_1/vre.ipynb \
  notebooks/example_2/vre.ipynb \
  notebooks/example_3/vre.ipynb \
  notebooks/example_4/vre.ipynb \
  notebooks/example_5/vre.ipynb \
  notebooks/example_6/vre.ipynb \
  notebooks/example_7/vre.ipynb \
  notebooks/example_8/vre.ipynb \
  notebooks/example_9/vre.ipynb \
  notebooks/example_10/vre.ipynb \
  notebooks/example_11/vre.ipynb \
  notebooks/southern_cross_cross_border/vre.ipynb
do
  (cd "$(dirname "$nb")" && PYTHONPATH= python -m nbconvert \
    --to notebook --execute "$(basename "$nb")" \
    --output-dir /tmp/vre_notebook_exec/"$(dirname "$nb")" \
    --ExecutePreprocessor.kernel_name=vre-wheel-313 \
    --ExecutePreprocessor.timeout=1800)
done
```

## Validation evidence

Promotion proof was run from a copied tree in a fresh Python 3.13 virtual
environment, with only `requirements.txt` and the `v0.14.0` macOS arm64 wheel
installed. The aggregate script runner and all active notebooks completed with
exit code 0.

CI runs the wheel-only aggregate runner from a clean temporary copy. It also
proves cp313 and cp314 wheel imports and injects fake local `VRE`, `VREData`,
and `vre` modules through `PYTHONPATH` to verify that scripts and notebooks
reject shadowed local imports.

The service-runner CI job skips `notebooks/example_5/vre.ipynb`,
`notebooks/example_10/run_sacva_larger_portfolio.py`, and the example 11 SA-CVA
scripts/notebook because those cases hang under the self-hosted GitHub Actions
service process while passing in the fresh local release proof.

## Current limitations

- The published wheels in this release are macOS arm64 only. Windows and Linux
  wheels are expected to be built separately.
- The examples are smoke and investigation surfaces. They are not a substitute
  for a governed RaaS tenant, production approvals, or client-specific validation
  evidence.
- Some examples exercise optional or platform-sensitive paths, such as GPU and
  service-runner behavior. The notebooks should still make the executed path
  explicit.

## Feedback and issues

These examples have been tested, but they are also a practical surface for users
to explore the engine. If an example does not run, a notebook is unclear, an
output is surprising, or a platform assumption is missing, please raise an issue
in this repository with:

- operating system and CPU architecture
- Python version
- wheel filename
- command or notebook executed
- full error output or the unexpected result

We will use those reports to tighten the examples, improve the documentation,
and fix runtime or packaging issues as they become apparent.

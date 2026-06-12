# VRE Python Examples

These examples run against the installed `vannarho-risk-engine` pybind wheel only.
They do not require `PYTHONPATH`, local source-tree imports, or in-repo C++ build
artifacts.

The script and notebook entrypoints fail closed if `VRE`, `VREData`, or `vre`
resolve outside the installed `vannarho-risk-engine` distribution. CI also
injects fake local VRE modules through `PYTHONPATH` and verifies that the
examples reject the shadowed import path.

## macOS wheel install

The current promoted macOS wheels are attached to the examples
`vre-python-v0.14.0` release. They were built from the VRE `v0.14.0` source
release.

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

If the examples release is private, authenticate `gh` with a token that can read
`Vannarho/examples` releases before running the download command.

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

CI runs the same wheel-only aggregate runner from a clean temporary copy. The
service-runner CI job skips `notebooks/example_5/vre.ipynb`,
`notebooks/example_10/run_sacva_larger_portfolio.py`, and the example 11 SA-CVA
scripts/notebook because those cases hang under the self-hosted GitHub Actions
service process while passing in the fresh local release proof.

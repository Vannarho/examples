#!/usr/bin/env python3

from __future__ import annotations

from contextlib import contextmanager
from pathlib import Path
import os
import sys

import VRE as vre

from utils import describe_portfolio, list_reports, prepare_gpu_xml


EXAMPLE_DIR = Path(__file__).resolve().parent
DEFAULT_XML = EXAMPLE_DIR / "Input" / "vre_sacva_cg_ad_eqcom.xml"


@contextmanager
def patched_env(values: dict[str, str | None]):
    """Temporarily set/clear a set of environment variables."""
    prev = {k: os.environ.get(k) for k in values}
    try:
        for key, val in values.items():
            if val is None:
                os.environ.pop(key, None)
            else:
                os.environ[key] = str(val)
        yield
    finally:
        for key, val in prev.items():
            if val is None:
                os.environ.pop(key, None)
            else:
                os.environ[key] = val


def run_sa_cva(master_xml: Path) -> None:
    """Run the SA-CVA CG/AAD job via the Python bindings."""
    params = vre.vrea.Parameters()
    params.fromFile(str(master_xml))
    app = vre.vrea.VREApp(params)
    app.run()
    outputs = Path(app.outputsPath() or (EXAMPLE_DIR / "Output"))
    print(f"[sa-cva] outputs: {outputs}")
    try:
        list_reports(app)
        describe_portfolio(app)
    except Exception as exc:
        print("[sa-cva] reporting helpers failed:", exc)


def main() -> int:
    master_xml = DEFAULT_XML
    if len(sys.argv) > 1:
        master_xml = Path(sys.argv[1])
        if not master_xml.is_absolute():
            master_xml = (EXAMPLE_DIR / master_xml).resolve()

    gpu_requested = os.environ.get("USE_EXTERNAL_COMPUTE_DEVICE", "").lower() in {"1", "true", "yes"}
    gpu_requested = gpu_requested or bool(os.environ.get("EXTERNAL_COMPUTE_DEVICE"))
    if gpu_requested:
        pricing_gpu = EXAMPLE_DIR / "Input" / "sacva_cg_eqcom" / "pricingengine_gpu.xml"
        try:
            master_xml = Path(
                prepare_gpu_xml(
                    str(master_xml),
                    pricing_engine_xml=str(pricing_gpu),
                )
            )
        except Exception as exc:
            print(f"[sa-cva] GPU setup failed: {exc}", file=sys.stderr)
            return 1

    # Keep SIM/CG path sample sizes consistent with XVA CG creation.
    os.environ.pop("OVERWRITE_SCENARIOGENERATOR_SAMPLES", None)

    print("+-----------------------------------------------------+")
    print("| XVA Risk: SA-CVA    - AAD 2 Trade EQ COM           |")
    print("+-----------------------------------------------------+")
    print(f"[sa-cva] master xml: {master_xml}")

    trace_env = {
        "VRE_CG_SENSI_TRACE_SCEN": "*",  # or EquitySpot/SP5
        "VRE_CG_SENSI_TRACE_TOP": "20",
        "VRE_CG_SENSI_TRACE_FILE": "cg_trace_aad.csv",
    }
    try:
        with patched_env(trace_env):
            run_sa_cva(master_xml)
    except Exception as exc:  # pragma: no cover - simple CLI guard
        print(f"[sa-cva] run failed: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())

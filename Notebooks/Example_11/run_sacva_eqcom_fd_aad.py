#!/usr/bin/env python3

from __future__ import annotations

from pathlib import Path
import sys

import VRE as vre

from utils import describe_portfolio, list_reports


EXAMPLE_DIR = Path(__file__).resolve().parent
DEFAULT_XML = EXAMPLE_DIR / "Input" / "vre_sacva_fd_aad_eqcom.xml"


def run_fd_aad(master_xml: Path) -> None:
    """Run the FD+AAD parity job via the Python bindings."""
    params = vre.vrea.Parameters()
    params.fromFile(str(master_xml))
    app = vre.vrea.VREApp(params)
    app.run()
    outputs = Path(app.outputsPath() or (EXAMPLE_DIR / "Output"))
    print(f"[fd-aad] outputs: {outputs}")
    try:
        list_reports(app)
        describe_portfolio(app)
    except Exception as exc:
        print("[fd-aad] reporting helpers failed:", exc)


def main() -> int:
    master_xml = DEFAULT_XML
    if len(sys.argv) > 1:
        master_xml = Path(sys.argv[1])
        if not master_xml.is_absolute():
            master_xml = (EXAMPLE_DIR / master_xml).resolve()

    print("+-----------------------------------------------------+")
    print("| XVA Risk: SA-CVA    - AAD (CG) 2 Trade EQ COM      |")
    print("+-----------------------------------------------------+")
    print(f"[fd-aad] master xml: {master_xml}")

    try:
        run_fd_aad(master_xml)
    except Exception as exc:  # pragma: no cover - simple CLI guard
        print(f"[fd-aad] run failed: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())

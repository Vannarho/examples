#!/usr/bin/env python3

from __future__ import annotations

from pathlib import Path
import sys
import pandas as pd

import VRE as vre

from utils import describe_portfolio, list_reports


EXAMPLE_DIR = Path(__file__).resolve().parent
DEFAULT_XML = EXAMPLE_DIR / "Input" / "vre_sacva_fd_eqcom.xml"

def _find_output_dir(base: Path) -> Path:
    """Pick the first child under base containing sacva.csv, else return base."""
    candidates = list(base.rglob("sacva.csv"))
    if candidates:
        return candidates[0].parent
    return base


def _preview_outputs(base_dir: Path):
    out_dir = _find_output_dir(base_dir)
    sacva = out_dir / "sacva.csv"
    sensi = out_dir / "sacva_sensitivities.csv"
    print(f"[fd-bump] preview @ {out_dir}")
    for path in [sacva, sensi]:
        if path.exists():
            try:
                df = pd.read_csv(path)
                print(f"  {path.name} (top rows):")
                print(df.head(10))
            except Exception as exc:
                print(f"  {path.name}: could not read ({exc})")
        else:
            print(f"  {path.name}: missing")
    # Tail the latest log and summarize max progress if present
    logs = sorted(out_dir.glob("log*.txt"))
    if logs:
        log_path = logs[-1]
        try:
            print(f"  tail {log_path.name}:")
            with open(log_path, "r") as f:
                lines = f.readlines()
            # Progress summary
            max_pct = None
            for line in lines:
                if "XVA: Building cube" in line and "(" in line and "%)" in line:
                    try:
                        pct = int(line.split("%")[0].split("(")[-1])
                        max_pct = pct if max_pct is None else max(max_pct, pct)
                    except Exception:
                        pass
            if max_pct is not None:
                print(f"    max progress: {max_pct}%")
            for line in lines[-50:]:
                print("    " + line.rstrip())
        except Exception as exc:
            print(f"  {log_path.name}: could not read ({exc})")


def run_fd(master_xml: Path) -> None:
    """Run the classic FD bump SA-CVA job via the Python wheel."""
    params = vre.vrea.Parameters()
    params.fromFile(str(master_xml))
    app = vre.vrea.VREApp(params)
    app.run()
    outputs = Path(app.outputsPath() or (EXAMPLE_DIR / "Output"))
    print(f"[fd-bump] outputs: {outputs}")
    try:
        list_reports(app)
        describe_portfolio(app)
        _preview_outputs(outputs)
    except Exception as exc:
        print("[fd-bump] reporting helpers failed:", exc)


def main() -> int:
    master_xml = DEFAULT_XML
    if len(sys.argv) > 1:
        cand = Path(sys.argv[1])
        master_xml = cand if cand.is_absolute() else (EXAMPLE_DIR / cand)

    print("+-----------------------------------------------------+")
    print("| XVA Risk: SA-CVA    - FD bump 2 Trade EQ COM       |")
    print("+-----------------------------------------------------+")
    print(f"[fd-bump] master xml: {master_xml}")

    try:
        run_fd(master_xml)
    except Exception as exc:  # pragma: no cover - CLI guard
        print(f"[fd-bump] run failed: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())

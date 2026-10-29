"""Command line entry point. Every output is local and never overwrites a run."""

import argparse
import json
import os
import shutil
import sys
import tempfile
from pathlib import Path

from . import __version__
from .engine import KitError, normalize, prepare, read_csv, read_json, validate_brief
from .report import export_run, report_html


def init_workspace(out):
    out = Path(out).resolve()
    if out.exists():
        raise KitError(f"Output already exists: {out}")
    out.parent.mkdir(parents=True, exist_ok=True)
    staging = Path(tempfile.mkdtemp(prefix=".gtmkit-init-", dir=out.parent))
    try:
        for name in ("brief.json", "prospects.csv", "signals.csv", "suppressions.csv"):
            shutil.copyfile(Path(__file__).parent / "assets" / name, staging / name)
        (staging / "README.txt").write_text("Synthetic example data only. Edit the brief and replace the CSVs with your own inputs.\nNo sending, enrichment, or external account connection occurs.\n", encoding="utf-8")
        out.mkdir()
        os.replace(staging, out)
    finally:
        if staging.exists():
            shutil.rmtree(staging)
    return out


def main(argv=None):
    parser = argparse.ArgumentParser(description="Prepare evidence-based outreach packs locally.")
    parser.add_argument("--version", action="version", version=__version__)
    sub = parser.add_subparsers(dest="command", required=True)
    for name in ("init", "demo"):
        cmd = sub.add_parser(name, help="Create a synthetic example workspace" if name == "init" else "Run the complete offline demonstration")
        cmd.add_argument("--out", required=True, type=Path)
    validate = sub.add_parser("validate", help="Check prospect CSV and brief structure without producing a run")
    build = sub.add_parser("prepare", help="Qualify, prioritize, draft, and export a local review pack")
    for cmd in (validate, build):
        cmd.add_argument("--input", required=True, type=Path)
        cmd.add_argument("--brief", required=True, type=Path)
    build.add_argument("--signals", type=Path)
    build.add_argument("--suppressions", type=Path)
    build.add_argument("--as-of", required=True, help="Evaluation date, YYYY-MM-DD")
    build.add_argument("--out", required=True, type=Path)
    report = sub.add_parser("report", help="Regenerate a report from a saved run")
    report.add_argument("--run", required=True, type=Path)
    report.add_argument("--out", required=True, type=Path)
    args = parser.parse_args(argv)
    try:
        if args.command == "init":
            print(json.dumps({"workspace": str(init_workspace(args.out)), "data": "synthetic"}))
        elif args.command == "validate":
            brief = validate_brief(read_json(args.brief))
            headers, rows = read_csv(args.input)
            normalized = normalize(headers, rows, brief)
            print(json.dumps({"valid": True, "rows": len(rows), "row_issues": [{"row_id": r["row_id"], "issues": r["problems"]} for r in normalized if r["problems"]], "note": "Structural validation only; prepare evaluates dated evidence and fit."}))
        elif args.command in ("prepare", "demo"):
            if args.command == "demo":
                workspace = init_workspace(args.out)
                run = prepare(workspace / "prospects.csv", workspace / "brief.json", signals_path=workspace / "signals.csv", suppressions_path=workspace / "suppressions.csv", as_of="2026-10-29")
                out = workspace / "results"
            else:
                run = prepare(args.input, args.brief, signals_path=args.signals, suppressions_path=args.suppressions, as_of=args.as_of)
                out = args.out
            destination = export_run(run, out)
            print(json.dumps({"output": str(destination), "summary": run["summary"], "report": str(destination / "report.html")}, indent=2))
        else:
            page = report_html(read_json(args.run))
            with args.out.open("x", encoding="utf-8") as file:
                file.write(page)
            print(json.dumps({"report": str(args.out.resolve())}))
        return 0
    except (KitError, OSError) as exc:
        print(json.dumps({"error": str(exc)}, ensure_ascii=False), file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())

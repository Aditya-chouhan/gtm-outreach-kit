"""Portable report and atomic, non-overwriting artifact exports."""

import csv
import html
import json
import os
import shutil
import tempfile
from pathlib import Path

from .engine import KitError


def escape(value):
    return html.escape(str(value if value is not None else ""), quote=True)


def csv_safe(value):
    value = str(value if value is not None else "")
    # Spreadsheet software may execute formula-looking cells after whitespace.
    return "'" + value if value.lstrip().startswith(("=", "+", "-", "@")) or value.startswith(("\t", "\r")) else value


def report_html(run):
    try:
        return _report_html(run)
    except (KeyError, TypeError, AttributeError) as exc:
        raise KitError(f"Malformed saved run: missing or invalid report fields ({exc})") from None


def _report_html(run):
    if not isinstance(run, dict) or run.get("schema_version") != "1.0" or not isinstance(run.get("records"), list) or not isinstance(run.get("drafts"), list):
        raise KitError("Report requires a GTM Kit run.json with schema_version 1.0")
    drafts = {d["record_id"]: d for d in run["drafts"]}
    records = sorted(run["records"], key=lambda r: (r["priority"]["rank"] is None, r["priority"]["rank"] or 0, r["id"]))
    cards = []
    for record in records:
        v, p = record["values"], record["priority"]
        rules = []
        for kind, results in record["qualification"].items():
            for rule in results:
                sources = "; ".join(f"{e['row_id']} · {e['source_ref']} · {e['observed_at']}" for e in rule["evidence"])
                rejected = "; ".join(f"{e['row_id']}: {e['reason']}" for e in rule["unusable_evidence"])
                rules.append(f'<tr><td>{escape(kind)}<br><strong>{escape(rule["rule_id"])}</strong></td><td>{escape(rule["result"])}</td><td>{escape(sources or "No usable evidence")}<br><small>{escape(rejected)}</small></td></tr>')
        signal_lines = "".join(f'<li>{escape(s["type"])} · {escape(s["observed_at"])} · {escape(s["priority_status"])}<br><small>{escape(s["source_ref"])}</small></li>' for s in record["signals"])
        raw_rows = "".join(f'<details class="raw"><summary>{escape(r["row_id"])} · supplied values</summary><pre>{escape(json.dumps(r["raw"], indent=2, ensure_ascii=False))}</pre></details>' for r in record["source_rows"])
        reasons = "".join(f"<li>{escape(x)}</li>" for x in record["reasons"])
        reasons += "".join(f'<li>Suppression: {escape(s["reason"])} ({escape(s["type"])}: {escape(s["value"])})</li>' for s in record["suppression_matches"])
        draft = drafts.get(record["id"])
        if draft:
            draft_content = f'<div class="draft"><span class="eyebrow">DRAFT FOR HUMAN REVIEW</span><h4>{escape(draft["subject"])}</h4><pre>{escape(draft["first"])}</pre><details><summary>Follow-up draft</summary><pre>{escape(draft["follow_up"])}</pre></details></div>'
        else:
            draft_content = '<div class="blocked"><strong>Draft withheld</strong><ul>' + "".join(f"<li>{escape(x)}</li>" for x in record["draft_blockers"]) + '</ul></div>'
        search = " ".join(str(v.get(k) or "") for k in ("first_name", "company", "email", "role", "country")) + " " + record["id"]
        cards.append(f'''<article class="record" data-status="{escape(record['fit_status'])}" data-contact="{escape(record['contact_status'])}" data-search="{escape(search.casefold())}">
<div class="record-top"><div class="identity"><span class="rank">{p['rank'] or '—'}</span><div><h3>{escape(v['company'] or 'Company needs review')}</h3><p>{escape(v['first_name'] or 'Name unavailable')} · {escape(v['role'] or 'Role unavailable')}</p></div></div><span class="badge {escape(record['fit_status'])}">{escape(record['fit_status'])}</span></div>
<div class="facts"><span>{escape(v['country'] or 'Country unknown')}</span><span>{escape(v['employees'] if v['employees'] is not None else 'Unknown')} employees</span><span>{escape(record['contact_status'].replace('_', ' '))}</span><span>{escape(record['id'])}</span></div>
<p class="ranking">{p['preference_matches']} preference matches · {p['fresh_signal_count']} eligible signals · latest {escape(p['latest_signal'] or 'none')}</p>
{'<ul class="reasons">' + reasons + '</ul>' if reasons else ''}
<details class="inspection"><summary>Inspect evidence &amp; drafts</summary><div class="inspection-body"><div class="table-wrap"><table><thead><tr><th>Rule</th><th>Result</th><th>Evidence</th></tr></thead><tbody>{''.join(rules)}</tbody></table></div>
{'<h4>Signal history</h4><ul>' + signal_lines + '</ul>' if signal_lines else ''}
{draft_content}<details><summary>Original records &amp; conflicts</summary><pre>{escape(json.dumps(record['conflicts'], indent=2, ensure_ascii=False))}</pre>{raw_rows}</details></div></details></article>''')
    summary = run["summary"]
    metrics = "".join(f'<div class="metric"><span>{label}</span><strong>{summary[key]}</strong><small>{note}</small></div>' for key, label, note in
                      [("input_rows", "Input rows", "Original source records"), ("qualified", "Qualified", "Passed the configured criteria"),
                       ("review", "Needs review", "Evidence or identity unresolved"), ("drafts", "Draft packs", "First email + follow-up")])
    disclosures = "".join(f"<li>{escape(d)}</li>" for d in run["disclosures"])
    hashes = "".join(f'<div><span>{escape(k)}</span><code>{escape(v or "Not supplied")}</code></div>' for k, v in run["input_sha256"].items())
    page = (Path(__file__).parent / "assets" / "report.html").read_text(encoding="utf-8")
    replacements = {"TITLE": escape(run["name"]), "DATE": escape(run["as_of"]), "VERSION": escape(run["engine_version"]),
                    "METRICS": metrics, "RECORDS": "\n".join(cards), "DISCLOSURES": disclosures, "HASHES": hashes,
                    "COUNT": str(summary["unique_records"]), "DEDUPE": str(summary["duplicate_rows"]),
                    "EXCLUDED": str(summary["excluded"]), "SUPPRESSED": str(summary["suppressed"])}
    # Single pass prevents template-like source data from changing the page.
    import re
    return re.sub(r"@@([A-Z]+)@@", lambda m: replacements[m.group(1)], page)


def write_json(path, data):
    Path(path).write_text(json.dumps(data, indent=2, ensure_ascii=False, allow_nan=False) + "\n", encoding="utf-8")


def export_run(run, out):
    out = Path(out).resolve()
    if out.exists():
        raise KitError(f"Output already exists: {out}. Choose a new directory.")
    out.parent.mkdir(parents=True, exist_ok=True)
    staging = Path(tempfile.mkdtemp(prefix=".gtmkit-", dir=out.parent))
    try:
        write_json(staging / "run.json", run)
        write_json(staging / "drafts.json", run["drafts"])
        fields = ["record_id", "contact_id", "first_name", "email", "company", "domain", "industry", "employees", "country", "role", "fit_status", "contact_status", "rank", "reasons"]
        for status in ("qualified", "review", "excluded"):
            with (staging / f"{status}.csv").open("w", newline="", encoding="utf-8") as file:
                writer = csv.DictWriter(file, fieldnames=fields)
                writer.writeheader()
                for r in sorted(run["records"], key=lambda r: (r["priority"]["rank"] or 10**9, r["id"])):
                    if r["fit_status"] != status:
                        continue
                    row = {key: r["values"].get(key) for key in fields}
                    row.update(record_id=r["id"], fit_status=status, contact_status=r["contact_status"], rank=r["priority"]["rank"], reasons="; ".join(r["reasons"]))
                    writer.writerow({k: csv_safe(v) for k, v in row.items()})
        (staging / "report.html").write_text(report_html(run), encoding="utf-8")
        # Reserve the destination exclusively, then replace the empty directory.
        out.mkdir()
        os.replace(staging, out)
    finally:
        if staging.exists():
            shutil.rmtree(staging)
    return out

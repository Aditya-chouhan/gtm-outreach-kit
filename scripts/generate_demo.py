"""Rebuild the original synthetic fixture; never reads personal or external data."""

import csv
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / "gtm_outreach_kit" / "assets"


def write_csv(name, fields, rows):
    with (ASSETS / name).open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def main():
    brief = {
        "schema_version": "1.0", "name": "Northstar Ops · synthetic outbound pilot",
        "offer": {"summary": "We help software teams turn prospect exports into reviewable outreach drafts.", "proof_points": []},
        "sender": {"name": "Alex", "company": "Northstar Ops (fictional)"},
        "required": [
            {"id": "software", "field": "industry", "op": "equals", "value": "software"},
            {"id": "company-size", "field": "employees", "op": "range", "value": [10, 200]},
            {"id": "market", "field": "country", "op": "in", "value": ["US", "GB"]}],
        "preferences": [{"id": "revenue-owner", "field": "role", "op": "in", "value": ["Head of Revenue", "Founder"]}],
        "exclusions": [{"id": "non-buyers", "field": "role", "op": "in", "value": ["Investor", "Competitor"]}],
        "signal_types": ["hiring", "product_launch"], "signal_max_age_days": 30, "evidence_max_age_days": 365,
    }
    rows, signals = [], []
    for i in range(1, 91):
        row = {"contact_id": f"p{i:03d}", "first_name": f"Person {i:03d}", "email": f"person{i:03d}@company{i:03d}.test",
               "company": f"Example Software {i:03d}", "domain": f"company{i:03d}.test", "industry": "software",
               "employees": str(20 + i), "country": "US" if i % 2 else "GB", "role": "Head of Revenue" if i % 3 else "Operations Manager",
               "source_ref": f"synthetic://prospects/{i:03d}", "observed_at": "2026-10-20"}
        kind = i % 10
        if kind == 2:
            row["employees"] = ""
        elif kind == 3:
            row["employees"] = "400"
        elif kind == 4:
            row["country"] = ""
        elif kind == 5:
            row["country"] = "IN"
        elif kind == 6:
            row["role"] = "Investor"
        elif kind == 7:
            row["observed_at"] = "2024-01-01"
        elif kind == 9:
            row["email"] = "" if i % 20 == 9 else "invalid-address"
        rows.append(row)
        for signal_type, observed in (("hiring", "2026-10-25"), ("product_launch", "2026-06-01")):
            signals.append({"contact_id": row["contact_id"], "email": "", "domain": "", "type": signal_type,
                            "observed_at": observed, "source_ref": f"synthetic://signals/{i:03d}/{signal_type}"})
    for i in range(10):
        duplicate = dict(rows[i])
        duplicate["email"] = duplicate["email"].upper()
        duplicate["source_ref"] = f"synthetic://duplicate/{i+1:03d}"
        if i == 7:
            duplicate["company"] = "Conflicting company identity"
        rows.append(duplicate)
    write_csv("prospects.csv", list(rows[0]), rows)
    write_csv("signals.csv", list(signals[0]), signals)
    write_csv("suppressions.csv", ["type", "value", "reason"], [
        {"type": "contact_id", "value": "p001", "reason": "Synthetic opt-out"},
        {"type": "domain", "value": "company021.test", "reason": "Synthetic company exclusion"}])
    (ASSETS / "brief.json").write_text(json.dumps(brief, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()

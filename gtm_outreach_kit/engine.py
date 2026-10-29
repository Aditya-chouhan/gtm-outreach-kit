"""Deterministic transformations. No networking, model calls, or external writes."""

from __future__ import annotations

import csv
import hashlib
import io
import json
import re
from datetime import date
from pathlib import Path
from urllib.parse import urlsplit

from . import __version__

FIELDS = {"contact_id", "first_name", "email", "company", "domain", "industry",
          "employees", "country", "role", "source_ref", "observed_at"}
OPS = {"equals", "in", "range"}
EMAIL = re.compile(r"^[^\s@]+@[^\s@]+\.[^\s@]+$")
DOMAIN = re.compile(r"^(?:[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?\.)+[a-z]{2,63}$")
TOKEN = re.compile(r"\{\{([a-z_]+)\}\}")
TEMPLATE_FIELDS = {"greeting", "first_name", "company", "offer", "proof", "sender_name", "sender_company"}
DEFAULT_TEMPLATES = {
    "subject": "Question for {{company}}",
    "first": "{{greeting}},\n\nI’m {{sender_name}} at {{sender_company}}. {{offer}}\n\n{{proof}}\n\nIs this relevant to your team? If not, let me know and I won’t follow up.\n\n{{sender_name}}",
    "follow_up": "{{greeting}},\n\nFollowing up on my note about {{offer}}\n\nShould I close the loop here?\n\n{{sender_name}}",
}


class KitError(ValueError):
    """Actionable input or workflow error."""


def canonical(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False)


def sha(data: bytes):
    return hashlib.sha256(data).hexdigest()


def day(value, label):
    try:
        if not isinstance(value, str) or not re.fullmatch(r"\d{4}-\d{2}-\d{2}", value):
            raise ValueError
        return date.fromisoformat(value)
    except ValueError:
        raise KitError(f"{label} must be a valid YYYY-MM-DD date") from None


def text(value, label):
    if not isinstance(value, str) or not value.strip():
        raise KitError(f"{label} must be nonempty text")
    return value.strip()


def read_json(path):
    def pairs(items):
        result = {}
        for k, v in items:
            if k in result:
                raise KitError(f"Duplicate JSON key: {k}")
            result[k] = v
        return result

    try:
        return json.loads(Path(path).read_text(encoding="utf-8"), object_pairs_hook=pairs,
                          parse_constant=lambda v: (_ for _ in ()).throw(KitError(f"Invalid number: {v}")))
    except (json.JSONDecodeError, UnicodeError) as exc:
        raise KitError(f"Invalid JSON in {Path(path).name}: {exc}") from None


def read_csv(path, required=()):
    try:
        content = Path(path).read_text(encoding="utf-8-sig")
        reader = csv.DictReader(io.StringIO(content), strict=True)
        headers = reader.fieldnames
        if not headers or any(not h or h != h.strip() for h in headers) or len(set(headers)) != len(headers):
            raise KitError(f"{Path(path).name}: headers must be unique, nonempty, and trimmed")
        if not set(required) <= set(headers):
            raise KitError(f"{Path(path).name}: required columns: {', '.join(required)}")
        rows = []
        for row in reader:
            if None in row or any(v is None for v in row.values()):
                raise KitError(f"{Path(path).name}: malformed CSV record at line {reader.line_num}")
            rows.append({k: v.strip() for k, v in row.items()})
        return headers, rows
    except (csv.Error, UnicodeError) as exc:
        raise KitError(f"Invalid CSV in {Path(path).name}: {exc}") from None


def validate_brief(brief):
    if not isinstance(brief, dict) or brief.get("schema_version") != "1.0":
        raise KitError('Brief requires schema_version "1.0"')
    allowed = {"schema_version", "name", "offer", "sender", "required", "preferences", "exclusions",
               "column_map", "signal_types", "signal_max_age_days", "evidence_max_age_days", "templates"}
    if set(brief) - allowed:
        raise KitError(f"Unknown brief keys: {sorted(set(brief) - allowed)}")
    text(brief.get("name"), "name")
    for section in ("offer", "sender"):
        if not isinstance(brief.get(section, {}), dict):
            raise KitError(f"{section} must be an object")
    offer, sender = brief.get("offer", {}), brief.get("sender", {})
    if set(offer) - {"summary", "proof_points"} or set(sender) - {"name", "company"}:
        raise KitError("Unknown offer or sender key")
    for label, value in [("offer.summary", offer.get("summary")), ("sender.name", sender.get("name")),
                         ("sender.company", sender.get("company"))]:
        if value is not None:
            text(value, label)
    proofs = offer.get("proof_points", [])
    if not isinstance(proofs, list) or any(not isinstance(p, str) or not p.strip() for p in proofs):
        raise KitError("offer.proof_points must be a list of nonempty strings")
    ids = set()
    if not brief.get("required"):
        raise KitError("At least one required qualification rule is needed")
    for section in ("required", "preferences", "exclusions"):
        rules = brief.get(section, [])
        if not isinstance(rules, list):
            raise KitError(f"{section} must be a list")
        for rule in rules:
            if not isinstance(rule, dict) or set(rule) != {"id", "field", "op", "value"}:
                raise KitError("Each rule requires exactly id, field, op, value")
            key = text(rule["id"], "rule.id")
            if key in ids or not re.fullmatch(r"[a-z][a-z0-9-]*", key):
                raise KitError(f"Invalid or duplicate rule id: {key}")
            ids.add(key)
            if rule["field"] not in FIELDS - {"source_ref", "observed_at"} or rule["op"] not in OPS:
                raise KitError(f"Unsupported field or operation in {key}")
            value = rule["value"]
            numeric = rule["field"] == "employees"
            def valid_scalar(v):
                return (type(v) is int and v >= 0) if numeric else (isinstance(v, str) and bool(v.strip()))
            if rule["op"] == "range":
                if not numeric or not isinstance(value, list) or len(value) != 2 or not all(valid_scalar(v) for v in value) or value[0] > value[1]:
                    raise KitError(f"{key}: range requires [minimum, maximum] integers on employees")
            elif rule["op"] == "in":
                if not isinstance(value, list) or not value or not all(valid_scalar(v) for v in value):
                    raise KitError(f"{key}: in requires a nonempty list matching the field type")
            elif not valid_scalar(value):
                raise KitError(f"{key}: equals value must match the field type")
    mapping = brief.get("column_map", {})
    if not isinstance(mapping, dict) or set(mapping) - FIELDS or any(not isinstance(v, str) or not v for v in mapping.values()) or len(set(mapping.values())) != len(mapping):
        raise KitError("column_map must map canonical fields to distinct CSV headers")
    for field, default in (("signal_max_age_days", 30), ("evidence_max_age_days", 365)):
        if type(brief.get(field, default)) is not int or brief.get(field, default) < 0:
            raise KitError(f"{field} must be a nonnegative integer")
    types = brief.get("signal_types", [])
    if not isinstance(types, list) or any(not isinstance(v, str) or not v.strip() for v in types):
        raise KitError("signal_types must be a list of nonempty strings")
    templates = brief.get("templates", {})
    if not isinstance(templates, dict) or set(templates) - set(DEFAULT_TEMPLATES):
        raise KitError("templates accepts subject, first, and follow_up")
    for key, template in templates.items():
        text(template, f"templates.{key}")
        if set(TOKEN.findall(template)) - TEMPLATE_FIELDS:
            raise KitError(f"Unsupported variable in templates.{key}")
        if "{{" in TOKEN.sub("", template) or "}}" in TOKEN.sub("", template):
            raise KitError(f"Malformed placeholder in templates.{key}")
    return brief


def normalize_domain(value):
    if not value:
        return ""
    try:
        host = urlsplit(value if "://" in value else "https://" + value).hostname or ""
    except ValueError:
        return ""
    host = host.lower().rstrip(".")
    if host.startswith("www."):
        host = host[4:]
    return host if DOMAIN.fullmatch(host) else ""


def normalize(headers, rows, brief):
    mapping = {field: brief.get("column_map", {}).get(field, field) for field in FIELDS}
    absent = set(brief.get("column_map", {}).values()) - set(headers)
    if absent:
        raise KitError(f"Mapped headers missing: {sorted(absent)}")
    # A header cannot feed two canonical fields through a mapping collision.
    present = [h for h in mapping.values() if h in headers]
    if len(present) != len(set(present)):
        raise KitError("Column mapping assigns one header to multiple fields")
    if not any(mapping[f] in headers for f in ("contact_id", "email", "company")):
        raise KitError("Input needs a contact_id, email, or company header (or explicit mapping)")
    records = []
    for index, raw in enumerate(rows, 1):
        values = {f: raw.get(mapping[f], "").strip() for f in sorted(FIELDS)}
        problems = []
        if values["email"]:
            values["email"] = values["email"].lower()
            if not EMAIL.fullmatch(values["email"]):
                problems.append("Invalid email syntax; no mailbox verification performed")
        original_domain = values["domain"]
        values["domain"] = normalize_domain(original_domain)
        if original_domain and not values["domain"]:
            problems.append("Invalid company domain")
        if values["employees"]:
            if re.fullmatch(r"\d+", values["employees"]):
                values["employees"] = int(values["employees"])
            else:
                values["employees"] = None
                problems.append("Invalid employee count")
        else:
            values["employees"] = None
        records.append({"row_id": f"row-{index:04d}", "raw": raw, "values": values, "problems": problems})
    return records


def deduplicate(rows):
    parents = list(range(len(rows)))
    def root(i):
        while parents[i] != i:
            parents[i] = parents[parents[i]]
            i = parents[i]
        return i
    identities = {}
    for index, row in enumerate(rows):
        for field in ("email", "contact_id"):
            value = row["values"][field]
            if not value or (field == "email" and not EMAIL.fullmatch(value)):
                continue
            identity = field, value
            if identity in identities:
                parents[root(index)] = root(identities[identity])
            identities[identity] = index
    groups = {}
    for index, row in enumerate(rows):
        groups.setdefault(root(index), []).append(row)
    result = []
    for group in groups.values():
        values, conflicts = {}, {}
        for field in sorted(FIELDS):
            choices = []
            for row in group:
                value = row["values"][field]
                if value not in ("", None) and value not in choices:
                    choices.append(value)
            # Source references and dates belong to individual observations.
            if len(choices) > 1 and field not in {"source_ref", "observed_at"}:
                conflicts[field] = choices
            values[field] = choices[0] if len(choices) == 1 else None
        identities_out = {f: sorted({r["values"][f] for r in group if r["values"][f]}) for f in ("email", "contact_id", "domain")}
        problems = sorted({p for r in group for p in r["problems"]})
        if not identities_out["email"] and not identities_out["contact_id"]:
            problems.append("No email or contact ID; record kept separate")
        result.append({"id": group[0]["row_id"], "values": values, "source_rows": group,
                       "identities": identities_out, "conflicts": conflicts, "problems": problems})
    return result


def match(value, rule):
    if value is None or value == "":
        return None
    def equal(a, b):
        return a.strip().casefold() == b.strip().casefold() if isinstance(a, str) and isinstance(b, str) else a == b
    if rule["op"] == "equals":
        return equal(value, rule["value"])
    if rule["op"] == "in":
        return any(equal(value, v) for v in rule["value"])
    return rule["value"][0] <= value <= rule["value"][1]


def evaluate_rule(record, rule, as_of, max_age):
    evidence, untrusted = [], []
    for row in record["source_rows"]:
        value = row["values"][rule["field"]]
        if value in (None, ""):
            continue
        reason = ""
        if not row["values"]["source_ref"]:
            reason = "Missing source reference"
        try:
            observed = day(row["values"]["observed_at"], "observed_at")
            age = (as_of - observed).days
            if age < 0 or age > max_age:
                reason = "Future or stale observation"
        except KitError:
            reason = "Missing or invalid observation date"
        entry = {"row_id": row["row_id"], "source_ref": row["values"]["source_ref"],
                 "observed_at": row["values"]["observed_at"], "value": value}
        if reason:
            untrusted.append({**entry, "reason": reason})
        else:
            evidence.append(entry)
    # Conflicts remain reviewable even if one observation is older.
    result = None if rule["field"] in record["conflicts"] or not evidence else match(record["values"][rule["field"]], rule)
    return {"rule_id": rule["id"], "field": rule["field"], "op": rule["op"], "expected": rule["value"],
            "result": "unknown" if result is None else "match" if result else "no_match",
            "evidence": evidence, "unusable_evidence": untrusted}


def load_suppressions(path):
    if path is None:
        return []
    _, rows = read_csv(path, ("type", "value", "reason"))
    for row in rows:
        if row["type"] not in {"email", "contact_id", "domain"} or not row["value"] or not row["reason"]:
            raise KitError("Suppression rows require type email/contact_id/domain, value, and reason")
        if row["type"] == "domain":
            row["value"] = normalize_domain(row["value"])
            if not row["value"]:
                raise KitError("Invalid suppression domain")
        if row["type"] == "email":
            row["value"] = row["value"].lower()
            if not EMAIL.fullmatch(row["value"]):
                raise KitError("Invalid suppression email")
    return rows


def load_signals(path, as_of):
    if path is None:
        return []
    _, rows = read_csv(path, ("contact_id", "email", "domain", "type", "observed_at", "source_ref"))
    for index, row in enumerate(rows, 1):
        row["signal_id"] = f"signal-{index:04d}"
        row["email"] = row["email"].lower()
        if row["email"] and not EMAIL.fullmatch(row["email"]):
            raise KitError(f"Invalid email in signal {index}")
        if row["domain"]:
            row["domain"] = normalize_domain(row["domain"])
            if not row["domain"]:
                raise KitError(f"Invalid domain in signal {index}")
        if not any(row[f] for f in ("contact_id", "email", "domain")) or not row["type"]:
            raise KitError(f"Signal {index} needs an identity and type")
        row["age_days"] = (as_of - day(row["observed_at"], f"Signal {index} observed_at")).days if row["observed_at"] else None
    return rows


def linked(record, event):
    # Explicit contact identities take precedence; a supplied ID and email must
    # both agree. A company signal (neither present) can apply to that domain.
    keys = [f for f in ("contact_id", "email") if event.get(f)]
    if not keys:
        keys = ["domain"]
    return all(event.get(f) in record["identities"][f] for f in keys)


def render(template, context):
    return TOKEN.sub(lambda m: context[m.group(1)], template)


def make_draft(record, brief):
    missing = [label for label, value in (("offer.summary", brief.get("offer", {}).get("summary")),
               ("sender.name", brief.get("sender", {}).get("name")),
               ("sender.company", brief.get("sender", {}).get("company"))) if not value]
    if not record["values"]["company"]:
        missing.append("prospect.company")
    if missing:
        return None, ["Missing " + v for v in missing]
    v = record["values"]
    ctx = {"first_name": v["first_name"] or "", "company": v["company"],
           "greeting": f"Hi {v['first_name']}" if v["first_name"] else "Hi there",
           "offer": brief["offer"]["summary"], "proof": " ".join(brief["offer"].get("proof_points", [])),
           "sender_name": brief["sender"]["name"], "sender_company": brief["sender"]["company"]}
    templates = DEFAULT_TEMPLATES | brief.get("templates", {})
    rendered = {k: render(t, ctx) for k, t in templates.items()}
    # Source-supplied placeholder-like strings never become runnable templates.
    if any("{{" in s or "}}" in s for s in rendered.values()):
        return None, ["Unresolved placeholder-like text in supplied data"]
    if "\n" in rendered["subject"] or "\r" in rendered["subject"]:
        return None, ["Subject contains a line break"]
    return {"record_id": record["id"], "email": v["email"], "status": "draft_for_review",
            **rendered, "claim_sources": {"prospect": [r["row_id"] for r in record["source_rows"]],
             "offer": "brief.offer.summary", "proof": "brief.offer.proof_points (user supplied; not independently verified)"}}, []


def prepare(input_path, brief_path, *, signals_path=None, suppressions_path=None, as_of):
    evaluation_day = day(as_of, "as_of")
    brief = validate_brief(read_json(brief_path))
    headers, rows = read_csv(input_path)
    records = deduplicate(normalize(headers, rows, brief))
    suppressions = load_suppressions(suppressions_path)
    signals = load_signals(signals_path, evaluation_day)
    drafts = []
    for record in records:
        results = {section: [evaluate_rule(record, rule, evaluation_day, brief.get("evidence_max_age_days", 365))
                   for rule in brief.get(section, [])] for section in ("required", "preferences", "exclusions")}
        record["qualification"] = results
        exclusions = [r["rule_id"] for r in results["exclusions"] if r["result"] == "match"]
        failed = [r["rule_id"] for r in results["required"] if r["result"] == "no_match"]
        # Unknown exclusions need review: missing evidence is not clearance.
        unknown = [r["rule_id"] for section in ("required", "exclusions") for r in results[section] if r["result"] == "unknown"]
        record["fit_status"] = "excluded" if exclusions or failed else "review" if unknown or record["conflicts"] or record["problems"] else "qualified"
        record["reasons"] = ["Exclusion matched: " + x for x in exclusions] + ["Required criterion failed: " + x for x in failed] + ["Evidence needed: " + x for x in unknown] + ["Conflicting values: " + x for x in record["conflicts"]] + record["problems"]
        record["suppression_matches"] = [s for s in suppressions if s["value"] in record["identities"][s["type"]] or (s["type"] == "domain" and any(e.rsplit("@", 1)[-1] == s["value"] for e in record["identities"]["email"]))]
        record["contact_status"] = "suppressed" if record["suppression_matches"] else "missing_email" if not record["values"]["email"] else "syntax_only" if EMAIL.fullmatch(record["values"]["email"]) else "invalid_email"
        record["signals"] = []
        seen = set()
        for signal in signals:
            if not linked(record, signal):
                continue
            identity = tuple(signal.get(f) for f in ("contact_id", "email", "domain", "type", "observed_at", "source_ref"))
            reason = "duplicate" if identity in seen else "missing_source" if not signal["source_ref"] else "missing_date" if signal["age_days"] is None else "future" if signal["age_days"] < 0 else "stale" if signal["age_days"] > brief.get("signal_max_age_days", 30) else "irrelevant" if signal["type"] not in brief.get("signal_types", []) else "eligible"
            seen.add(identity)
            record["signals"].append({**signal, "priority_status": reason})
        eligible = [s for s in record["signals"] if s["priority_status"] == "eligible"]
        record["priority"] = {"preference_matches": sum(r["result"] == "match" for r in results["preferences"]),
                              "fresh_signal_count": len(eligible),
                              "latest_signal": max((s["observed_at"] for s in eligible), default=None), "rank": None}
        record["draft_blockers"] = []
        if record["fit_status"] != "qualified":
            record["draft_blockers"].append("Qualification requires review or is excluded")
        if record["contact_status"] != "syntax_only":
            record["draft_blockers"].append("Contact status: " + record["contact_status"])
        if not record["draft_blockers"]:
            draft, blockers = make_draft(record, brief)
            record["draft_blockers"].extend(blockers)
            if draft:
                drafts.append(draft)
    qualified = [r for r in records if r["fit_status"] == "qualified"]
    qualified.sort(key=lambda r: (-r["priority"]["preference_matches"], -r["priority"]["fresh_signal_count"],
                                 -(date.fromisoformat(r["priority"]["latest_signal"]).toordinal() if r["priority"]["latest_signal"] else 0), r["id"]))
    for rank, record in enumerate(qualified, 1):
        record["priority"]["rank"] = rank
    ranks = {r["id"]: r["priority"]["rank"] for r in qualified}
    drafts.sort(key=lambda d: ranks[d["record_id"]])
    inputs = {label: sha(Path(path).read_bytes()) if path is not None else None for label, path in
              (("prospects", input_path), ("brief", brief_path), ("signals", signals_path), ("suppressions", suppressions_path))}
    return {"schema_version": "1.0", "engine_version": __version__, "name": brief["name"], "as_of": as_of,
            "input_sha256": inputs, "configuration": brief,
            "disclosures": ["Drafts only; no messages sent", "Email syntax is checked; mailbox deliverability is unverified",
                            "Source references are supplied evidence labels, not independently fetched or verified",
                            "Ranking expresses configured preferences, not a probability of purchase"] +
                           (["No suppression file supplied; do-not-contact coverage is unknown"] if suppressions_path is None else []) +
                           (["No signal file supplied"] if signals_path is None else []),
            "summary": {"input_rows": len(rows), "unique_records": len(records), "duplicate_rows": len(rows) - len(records),
                        **{status: sum(r["fit_status"] == status for r in records) for status in ("qualified", "review", "excluded")},
                        "suppressed": sum(r["contact_status"] == "suppressed" for r in records), "drafts": len(drafts)},
            "records": records, "drafts": drafts}

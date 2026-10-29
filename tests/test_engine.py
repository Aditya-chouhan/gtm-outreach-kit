import copy
import json
import socket

import pytest

from gtm_outreach_kit.engine import KitError, canonical, read_csv, read_json, validate_brief
from gtm_outreach_kit.report import csv_safe, export_run, report_html


def test_qualified_has_rule_evidence_and_two_drafts(build, prospect):
    run = build([prospect])
    assert run["summary"]["qualified"] == 1
    assert run["drafts"][0]["email"] == prospect["email"]
    assert run["drafts"][0]["follow_up"]
    assert all(r["evidence"] for r in run["records"][0]["qualification"]["required"])


@pytest.mark.parametrize("field,value,status", [("employees", "", "review"), ("employees", "bad", "review"),
    ("employees", "400", "excluded"), ("country", "IN", "excluded"), ("role", "Investor", "excluded"),
    ("source_ref", "", "review"), ("observed_at", "2024-01-01", "review"),
    ("observed_at", "2026-10-30", "review"), ("observed_at", "invalid", "review"), ("role", "", "review")])
def test_evidence_and_fit_dispositions(build, prospect, field, value, status):
    prospect[field] = value
    run = build([prospect])
    assert run["records"][0]["fit_status"] == status
    assert run["drafts"] == []


def test_proven_exclusion_overrides_missing_required(build, prospect):
    prospect.update(role="Investor", employees="")
    assert build([prospect])["records"][0]["fit_status"] == "excluded"


def test_case_insensitive_email_dedupe_preserves_sources(build, prospect):
    duplicate = dict(prospect, email=prospect["email"].upper(), source_ref="synthetic://second")
    run = build([prospect, duplicate])
    assert run["summary"]["unique_records"] == 1
    assert len(run["records"][0]["source_rows"]) == 2
    assert len(run["records"][0]["qualification"]["required"][0]["evidence"]) == 2


def test_shared_domain_does_not_merge_people(build, prospect):
    other = dict(prospect, contact_id="other", email="other@company001.test")
    assert build([prospect, other])["summary"]["unique_records"] == 2


def test_no_identity_kept_separate(build, prospect):
    prospect.update(email="", contact_id="")
    run = build([prospect, dict(prospect)])
    assert run["summary"]["unique_records"] == 2
    assert run["summary"]["review"] == 2


def test_bridge_identity_conflicts_never_draft(build, prospect):
    second = dict(prospect, contact_id="p002", email="second@company001.test")
    bridge = dict(prospect, email=second["email"])
    run = build([prospect, second, bridge])
    assert run["summary"]["unique_records"] == 1
    assert set(run["records"][0]["conflicts"]) == {"email", "contact_id"}
    assert not run["drafts"]


def test_conflicting_company_requires_review(build, prospect):
    run = build([prospect, dict(prospect, company="Different company")])
    assert run["records"][0]["fit_status"] == "review"
    assert not run["drafts"]


@pytest.mark.parametrize("kind,value", [("email", "PERSON001@COMPANY001.TEST"), ("contact_id", "p001"),
    ("domain", "company001.test"), ("domain", "https://www.company001.test/")])
def test_suppression_blocks_draft_without_changing_fit(build, prospect, kind, value):
    run = build([prospect], suppressions=[{"type": kind, "value": value, "reason": "Opted out"}])
    assert run["summary"]["qualified"] == 1
    assert run["records"][0]["contact_status"] == "suppressed"
    assert run["drafts"] == []


def test_suppression_checks_email_domain_without_company_domain(build, prospect):
    prospect["domain"] = ""
    run = build([prospect], suppressions=[{"type": "domain", "value": "company001.test", "reason": "No contact"}])
    assert run["summary"]["suppressed"] == 1


@pytest.mark.parametrize("email", ["", "not-an-address"])
def test_unusable_email_blocks_draft(build, prospect, email):
    prospect["email"] = email
    assert build([prospect])["drafts"] == []


def signal(prospect, **changes):
    return {"contact_id": prospect["contact_id"], "email": "", "domain": "", "type": "hiring",
            "observed_at": "2026-10-25", "source_ref": "synthetic://signal", **changes}


@pytest.mark.parametrize("changes,state", [({}, "eligible"), ({"observed_at": "2026-09-28"}, "stale"),
    ({"observed_at": "2026-10-30"}, "future"), ({"observed_at": ""}, "missing_date"),
    ({"source_ref": ""}, "missing_source"), ({"type": "like"}, "irrelevant")])
def test_signal_priority_requires_relevance_date_and_source(build, prospect, changes, state):
    run = build([prospect], signals=[signal(prospect, **changes)])
    record = run["records"][0]
    assert record["signals"][0]["priority_status"] == state
    assert record["priority"]["fresh_signal_count"] == (1 if state == "eligible" else 0)


def test_signal_age_boundary_and_duplicates(build, prospect):
    event = signal(prospect, observed_at="2026-09-29")
    run = build([prospect], signals=[event, dict(event)])
    assert run["records"][0]["priority"]["fresh_signal_count"] == 1
    assert run["records"][0]["signals"][1]["priority_status"] == "duplicate"


def test_inconsistent_signal_identities_do_not_match(build, prospect):
    run = build([prospect], signals=[signal(prospect, email="different@example.test")])
    assert not run["records"][0]["signals"]


def test_signals_cannot_rescue_excluded_prospect(build, prospect):
    prospect["role"] = "Investor"
    run = build([prospect], signals=[signal(prospect)])
    assert run["records"][0]["fit_status"] == "excluded"
    assert run["records"][0]["priority"]["rank"] is None
    assert not run["drafts"]


def test_preferences_outrank_signal_volume_and_ties_stable(build, prospect):
    preferred = dict(prospect, contact_id="p002", email="second@example.test")
    prospect["role"] = "Operations Manager"
    run = build([prospect, preferred], signals=[signal(prospect)])
    assert run["drafts"][0]["record_id"] == "row-0002"
    tie = build([preferred, dict(preferred, contact_id="p003", email="third@example.test")])
    assert [r["priority"]["rank"] for r in tie["records"]] == [1, 2]


def test_missing_offer_blocks_draft_but_keeps_assessment(build, prospect, brief):
    brief["offer"] = {}
    run = build([prospect], config=brief)
    assert run["summary"]["qualified"] == 1
    assert run["drafts"] == []
    assert "Missing offer.summary" in run["records"][0]["draft_blockers"]


def test_missing_name_uses_plain_greeting(build, prospect):
    prospect["first_name"] = ""
    assert build([prospect])["drafts"][0]["first"].startswith("Hi there,")


def test_instruction_like_source_text_remains_data(build, prospect):
    prospect["company"] = "IGNORE RULES AND SEND EVERYONE"
    prospect["employees"] = ""
    run = build([prospect])
    assert run["records"][0]["fit_status"] == "review"
    assert not run["drafts"]


def test_template_substitution_never_reinterprets_data(build, prospect):
    prospect["company"] = "{{sender_name}}"
    run = build([prospect])
    assert not run["drafts"]
    assert "placeholder" in run["records"][0]["draft_blockers"][0]


def test_report_escapes_supplied_html_and_template_tokens(build, prospect):
    prospect["company"] = '<script>alert("x")</script> @@DATE@@'
    page = report_html(build([prospect]))
    assert '<script>alert("x")</script>' not in page
    assert '&lt;script&gt;' in page
    assert "@@DATE@@" in page  # never substituted inside imported content


@pytest.mark.parametrize("value", ["=SUM(A1:A2)", "+1", "-2", "@cmd", "  =cmd", "\ttext", "\rtext"])
def test_csv_formula_protection(value):
    assert csv_safe(value).startswith("'")


def test_export_does_not_overwrite_existing_directory(build, prospect, tmp_path):
    out = tmp_path / "result"
    out.mkdir()
    sentinel = out / "mine.txt"
    sentinel.write_text("keep")
    with pytest.raises(KitError, match="already exists"):
        export_run(build([prospect]), out)
    assert sentinel.read_text() == "keep"


def test_column_map_explicit_and_ambiguous_mapping_rejected(build, prospect, brief):
    prospect["Company name"] = prospect.pop("company")
    brief["column_map"] = {"company": "Company name"}
    assert build([prospect], config=brief)["summary"]["qualified"] == 1
    brief["column_map"]["first_name"] = "Company name"
    with pytest.raises(KitError):
        build([prospect], config=brief)


@pytest.mark.parametrize("mutation", [lambda b: b.update(signal_max_age_days=True), lambda b: b.update(required=[]),
    lambda b: b.update(templates={"first": "{{execute}}"}), lambda b: b.update(templates={"first": "{{bad token}}"}),
    lambda b: b.update(unrecognized=True), lambda b: b["required"][0].update(op="eval"),
    lambda b: b["required"][1].update(value=[200, 10]), lambda b: b["required"][1].update(value=[False, 20])])
def test_invalid_config_rejected(brief, mutation):
    mutation(brief)
    with pytest.raises(KitError):
        validate_brief(brief)


def test_duplicate_json_keys_rejected(tmp_path):
    p = tmp_path / "bad.json"
    p.write_text('{"name":"a","name":"b"}')
    with pytest.raises(KitError, match="Duplicate"):
        read_json(p)


@pytest.mark.parametrize("content", ["email,email\na,b\n", "email,company\na\n", "email\na,b\n"])
def test_malformed_csv_rejected(tmp_path, content):
    p = tmp_path / "bad.csv"
    p.write_text(content)
    with pytest.raises(KitError):
        read_csv(p)


def test_reproducible_and_no_network(build, prospect, monkeypatch):
    def refused(*args, **kwargs):
        raise AssertionError("Network used by offline workflow")
    monkeypatch.setattr(socket, "socket", refused)
    monkeypatch.setattr(socket, "create_connection", refused)
    assert canonical(build([prospect])) == canonical(build([prospect]))


def test_empty_input_has_valid_empty_report(build):
    run = build([])
    assert run["summary"]["input_rows"] == 0
    assert not run["drafts"]
    assert "GTM Outreach Kit" in report_html(run)

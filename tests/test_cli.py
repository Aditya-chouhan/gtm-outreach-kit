import json

from gtm_outreach_kit.cli import main


def test_demo_then_saved_report(tmp_path, capsys):
    out = tmp_path / "demo"
    assert main(["demo", "--out", str(out)]) == 0
    result = json.loads(capsys.readouterr().out)
    assert result["summary"]["drafts"] == 24
    report = tmp_path / "report.html"
    assert main(["report", "--run", str(out / "results" / "run.json"), "--out", str(report)]) == 0
    assert report.read_bytes() == (out / "results" / "report.html").read_bytes()


def test_existing_init_directory_refused(tmp_path, capsys):
    assert main(["init", "--out", str(tmp_path)]) == 2
    assert "already exists" in json.loads(capsys.readouterr().err)["error"]


def test_malformed_saved_run_returns_actionable_error(tmp_path, capsys):
    path = tmp_path / "run.json"
    path.write_text('{"schema_version":"1.0","records":[],"drafts":[]}')
    assert main(["report", "--run", str(path), "--out", str(tmp_path / "r.html")]) == 2
    assert "Malformed saved run" in json.loads(capsys.readouterr().err)["error"]
    assert not (tmp_path / "r.html").exists()


def test_missing_file_returns_json_error(tmp_path, capsys):
    assert main(["validate", "--input", str(tmp_path / "missing.csv"), "--brief", str(tmp_path / "missing.json")]) == 2
    assert "error" in json.loads(capsys.readouterr().err)


def test_validate_reports_syntax_issues_without_rewriting(tmp_path, capsys):
    assert main(["init", "--out", str(tmp_path / "workspace")]) == 0
    capsys.readouterr()
    workspace = tmp_path / "workspace"
    before = (workspace / "prospects.csv").read_bytes()
    assert main(["validate", "--input", str(workspace / "prospects.csv"), "--brief", str(workspace / "brief.json")]) == 0
    result = json.loads(capsys.readouterr().out)
    assert result["valid"] and result["row_issues"]
    assert (workspace / "prospects.csv").read_bytes() == before

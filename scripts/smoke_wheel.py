"""Install the actual wheel in a fresh venv and exercise every public command."""
import json
import os
import subprocess
import sys
import tempfile
import venv
from pathlib import Path


def main():
    wheel = Path(sys.argv[1]).resolve()
    with tempfile.TemporaryDirectory(prefix="gtmkit-wheel-") as directory:
        root = Path(directory)
        venv.create(root / "env", with_pip=True)
        binary = root / "env" / ("Scripts" if os.name == "nt" else "bin")
        python = binary / ("python.exe" if os.name == "nt" else "python")
        cli = binary / ("gtmkit.exe" if os.name == "nt" else "gtmkit")
        env = dict(os.environ)
        env.pop("PYTHONPATH", None)
        def call(*args):
            result = subprocess.run([str(a) for a in args], cwd=root, env=env, check=True, capture_output=True, text=True)
            return result.stdout.strip()
        call(python, "-m", "pip", "install", "--disable-pip-version-check", "--no-index", "--no-deps", wheel)
        assert call(cli, "--version") == "0.1.0"
        call(cli, "--help")
        call(cli, "init", "--out", "workspace")
        validate = json.loads(call(cli, "validate", "--input", "workspace/prospects.csv", "--brief", "workspace/brief.json"))
        assert validate["valid"] and validate["rows"] == 100
        prepared = json.loads(call(cli, "prepare", "--input", "workspace/prospects.csv", "--brief", "workspace/brief.json", "--signals", "workspace/signals.csv", "--suppressions", "workspace/suppressions.csv", "--as-of", "2026-10-29", "--out", "results"))
        call(cli, "report", "--run", "results/run.json", "--out", "another-report.html")
        demo = json.loads(call(cli, "demo", "--out", "demo-output"))
        assert prepared["summary"] == demo["summary"]
        original = (root / "results" / "report.html").read_bytes()
        assert original == (root / "another-report.html").read_bytes()
        assert (root / "results" / "run.json").read_bytes() == (root / "demo-output" / "results" / "run.json").read_bytes()
        distribution = json.loads(call(python, "-c", "import importlib.metadata as m,json; d=m.distribution('gtm-outreach-kit'); print(json.dumps({'requires':d.requires,'version':d.version}))"))
        assert not [r for r in distribution["requires"] or [] if "extra ==" not in r]
        print(json.dumps({"wheel": wheel.name, "outside_checkout": True, "fresh_environment": True,
                          "commands": ["version", "help", "init", "validate", "prepare", "report", "demo"],
                          "runtime_dependencies": 0, "reproducible": True, "summary": prepared["summary"]}, indent=2))


if __name__ == "__main__":
    main()

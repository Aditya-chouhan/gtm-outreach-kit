import copy
import csv
import json
from pathlib import Path

import pytest

from gtm_outreach_kit.engine import prepare

ASSETS = Path(__file__).resolve().parents[1] / "gtm_outreach_kit" / "assets"


@pytest.fixture
def brief():
    return json.loads((ASSETS / "brief.json").read_text())


@pytest.fixture
def prospect():
    with (ASSETS / "prospects.csv").open() as f:
        return next(csv.DictReader(f))


@pytest.fixture
def build(tmp_path, brief):
    def run(rows, config=None, signals=None, suppressions=None, as_of="2026-10-29"):
        def write_csv(name, data, fields):
            p = tmp_path / name
            with p.open("w", newline="") as f:
                w = csv.DictWriter(f, fieldnames=fields)
                w.writeheader()
                w.writerows(data)
            return p
        config = copy.deepcopy(brief if config is None else config)
        p = tmp_path / "brief.json"
        p.write_text(json.dumps(config))
        csv_path = write_csv("input.csv", rows, list(rows[0]) if rows else ["email"])
        sig = write_csv("signals.csv", signals, ["contact_id", "email", "domain", "type", "observed_at", "source_ref"]) if signals is not None else None
        sup = write_csv("suppressions.csv", suppressions, ["type", "value", "reason"]) if suppressions is not None else None
        return prepare(csv_path, p, signals_path=sig, suppressions_path=sup, as_of=as_of)
    return run

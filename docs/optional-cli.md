# Optional deterministic outreach CLI

This helper handles local CSV data. It is not required to install or use any of the 25 skills. It neither searches external sources nor executes the broader research, strategy, content or operating workflows.

Python 3.11+ is required for the helper. From the repository:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install .
gtmkit demo --out demo-output
```

Open demo-output/results/report.html. The demonstration processes 100 synthetic source rows into 90 unique records: 31 qualified, 32 needing review, 27 excluded, and 24 draft packs. These are fictional fixture results, not campaign performance.

```bash
gtmkit init --out workspace
gtmkit validate --input workspace/prospects.csv --brief workspace/brief.json
gtmkit prepare --input workspace/prospects.csv --brief workspace/brief.json \
  --signals workspace/signals.csv --suppressions workspace/suppressions.csv \
  --as-of 2026-10-29 --out results
gtmkit report --run results/run.json --out another-report.html
```

Replace the synthetic input and choose an appropriate evaluation date for real work. Output destinations must be new. Missing optional signal or suppression coverage is disclosed. Outputs are run.json, drafts.json, qualified.csv, review.csv, excluded.csv and report.html.

The engine preserves raw rows, flags identity conflicts, evaluates dated evidence, separates fit from contact eligibility, ranks using configured preferences/signals and renders templates. It checks email syntax only. It makes no network or model call and sends nothing. CSV exports neutralize formula-looking cells; JSON keeps raw supplied data.

See [input contract](input-contract.md), [synthetic report](demo-report.html) and [historical CLI receipts](../evidence/verification.json). Python package version 0.1.0 continues to identify the unchanged helper; the skills-library expansion is documented separately.

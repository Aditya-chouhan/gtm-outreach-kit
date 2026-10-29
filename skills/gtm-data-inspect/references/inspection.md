# Inspection mechanics

CSV: UTF-8, optionally a BOM, comma-separated, with unique trimmed headers and a consistent number of fields. The canonical columns are contact_id, first_name, email, company, domain, industry, employees, country, role, source_ref, observed_at. Additional columns are preserved in raw records. Map nonstandard headers in the brief using `column_map`.

```bash
gtmkit validate --input prospects.csv --brief brief.json
gtmkit prepare --input prospects.csv --brief brief.json --as-of 2026-10-29 --out inspection-run
```

Use the evaluation date requested for the task; the example date is not a universal default. Existing output destinations are refused.

The engine merges contacts linked by a normalized email or an explicit contact ID, including transitive links. Company domains do not merge people. Conflicting values stay visible, invalidate automatic qualification, and withhold drafts. Records lacking both identities stay separate and need review. Normalization validates email syntax only.

Read `run.json`: `summary` gives counts; `records[].source_rows` retains the input; `conflicts` lists competing normalized values. Structural validation is not evidence validation: source dates and qualification are evaluated during prepare.

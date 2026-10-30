# Optional local CLI workflow

Read only when the user explicitly chooses the local CSV helper. The CLI is not required for this skill and covers only a subset of its workflow.

# Qualification behavior

```bash
gtmkit prepare --input prospects.csv --brief brief.json --signals signals.csv --suppressions suppressions.csv --as-of 2026-10-29 --out qualification-run
```

Optional supporting files can be omitted. Use the task's evaluation date and a new output directory.

The engine evaluates supported rules against normalized observations. Each observation needs a source_ref and valid observed_at to support a rule. Future or over-age observations are unusable. The default maximum evidence age is 365 days and can be configured.

A supported exclusion match or failed required criterion yields `excluded`. Otherwise an unknown required criterion, unknown exclusion criterion, identity/data issue, or conflicting field yields `review`. Remaining rows are `qualified`. Preferences never turn a failed criterion into a pass.

Source evidence is exposed for each rule, including unusable evidence and why it was unusable. Qualification is a decision under a configured rubric, not proof of purchasing intent. Suppression is an independent contact-status dimension. Do not change the rubric simply to reach a preferred list count.

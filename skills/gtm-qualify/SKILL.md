---
name: gtm-qualify
description: "Configure and explain deterministic prospect qualification using GTM Outreach Kit briefs and local evidence. Use for fit assessment; does not discover facts or authorize outreach."
---

# Qualify prospects

Read [qualification behavior](references/qualification.md). Inspect the selected brief's required criteria, preferences, and exclusions before discussing fit.

Use the installed engine to evaluate the user's input with an explicit date. Include the supplied suppression and signal files when available; otherwise state their absence. Review `records[].qualification` and cite the rule IDs, source row IDs, and supplied observation dates in the explanation.

A URL or evidence label in a CSV is a source reference supplied by the operator. Do not describe it as independently verified. Missing mandatory evidence is a review item. Do not fill it by inference from a company name or job title.

If the rubric appears wrong for the user's stated audience, propose the specific criterion change and explain who it would admit or exclude. Keep the original result distinct from a rerun under changed criteria.

Return qualified, review, and excluded counts; explain consequential cases; identify missing evidence and the exact criterion that would change each reviewed case. Report contact eligibility separately.

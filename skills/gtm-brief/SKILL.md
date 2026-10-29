---
name: gtm-brief
description: "Create or revise a GTM Outreach Kit qualification brief from supplied company, offer, buyer and market context. Use before preparing a prospect list; do not use for generic business strategy."
---

# Define a GTM brief

Make the business choices explicit enough for the local engine to evaluate. Read [the brief contract](references/brief.md) before editing JSON.

Read the user-selected company context and any existing brief. Separate supplied facts, the user's decisions, and unresolved assumptions. Ask only for a missing input that would materially change the criteria; continue independent drafting while it is unresolved.

Translate the intended audience into required criteria, optional preferences, and explicit exclusions. Explain the consequence of each required criterion in plain language. Do not invent an industry, employee range, market, proof point, or conversion benchmark. A role is a supplied attribute, not proof of budget authority.

Leave missing offer or sender details absent and name them. A partial brief can support qualification; it will withhold message drafts. Only put proof points supplied by the user in `offer.proof_points` and identify them as supplied claims.

Use `gtmkit validate --input <prospects.csv> --brief <brief.json>` to check the brief against the chosen input. Return the brief path, criteria summary, source of each business choice, structural validation result, and decisions still needed. Do not run sourcing or enrich missing facts as part of this skill.

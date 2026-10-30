# Optional local CLI workflow

Read only when the user explicitly chooses the local CSV helper. The CLI is not required for this skill and covers only a subset of its workflow.

# Priority mechanics

Within qualified records: more matched preferences first; then more eligible fresh signals; then the latest eligible signal date; then source-row ID. Ranking is deterministic for the same input ordering, configuration, and date. It is not invariant to reordering the input CSV because row ID is the final tie-breaker.

Signals require CSV columns contact_id,email,domain,type,observed_at,source_ref. A contact-specific signal matches all supplied contact identities. A signal without contact ID/email can match a company domain. Blank source or date never adds priority. Malformed nonblank dates are input errors. Duplicate identical events count once.

Only types listed in `signal_types` and observations within `signal_max_age_days` count; default 30 days, including the boundary. Future observations never count. A signal only ranks already-qualified records.

The CLI accepts `--signals signals.csv`. Read `records[].signals[].priority_status` for inclusion or exclusion explanations and `records[].priority` for the calculated ordering. For each prospect, cite its source row and the signal's supplied source_ref and date.

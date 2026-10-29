# Input contract · v1

The executable validator and [JSON schemas](schemas/) describe the accepted interchange format. JSON Schema checks structure; the engine additionally checks unique rule IDs, ordered numeric ranges, mapping collisions, real calendar dates, and template variables.

## Prospect CSV

UTF-8 (an optional BOM is accepted), comma-separated, one unique trimmed header per column, consistent field counts. Extra columns are preserved under `source_rows[].raw`. Header mapping is explicit: `"column_map": {"company": "Company Name"}` maps a canonical field to an existing CSV header. One header cannot feed two canonical fields.

| Column | Meaning and normalization |
| --- | --- |
| `contact_id` | Operator-supplied, case-sensitive identity; optional if email is available |
| `email` | Trimmed, lowercased, basic syntax check only |
| `first_name`, `company`, `industry`, `country`, `role` | Supplied text; rule comparisons trim and ignore case |
| `domain` | Company domain or URL; normalize host, lowercase, remove `www.` and trailing dot; never infer the employer from an email |
| `employees` | Nonnegative integer text; blank is unknown; malformed values become a visible problem |
| `source_ref` | Source label or URL supplied by the operator; not fetched or independently verified |
| `observed_at` | YYYY-MM-DD date of the source observation |

At least a contact_id, email, or company header must be present. Fields used in criteria can be absent; those rules then need evidence. Rows lacking both identity values stay separate and require review. Duplicate matching is transitive by email/contact ID; differing normalized values remain conflicts, even if an older observation supplied one of them. Source references and dates remain per observation rather than being treated as identity conflicts.

Raw source values stay in JSON. CSV exports prefix formula-looking cells with an apostrophe. CSV syntax checking does not establish the truth of a source, current employment, permission to contact, or mailbox verification.

## Brief JSON

`schema_version` is `"1.0"`; `name` and a nonempty `required` list are mandatory. Optional sections are `offer`, `sender`, `preferences`, `exclusions`, `column_map`, `signal_types`, `signal_max_age_days`, `evidence_max_age_days`, and `templates`. Unknown keys are rejected. Missing offer/sender fields allow assessment and block draft generation.

Rules contain exactly `id`, `field`, `op`, and `value`. IDs are globally unique lowercase slugs. Fields are prospect attributes except source_ref/observed_at. Operations:

- `equals`: one string, or an integer for employees.
- `in`: a nonempty list of the corresponding scalar type.
- `range`: an inclusive two-integer employee range, minimum first.

```json
{"id":"team-size","field":"employees","op":"range","value":[10,200]}
```

Qualification precedence: supported exclusion or failed required criterion → excluded; otherwise missing required/exclusion evidence, conflicting values, or data/identity problems → review; otherwise qualified. Preferences influence ordering only.

All rule evidence requires a source reference and a valid observation date. Future evidence is unusable. Default maximum evidence age is 365 days; default signal age is 30 days, both inclusive and configurable. These are product defaults, not performance benchmarks.

`offer`: summary and proof_points (list of supplied strings). `sender`: name and company. `templates`: subject, first, follow_up. Supported variables: `{{greeting}}`, `{{first_name}}`, `{{company}}`, `{{offer}}`, `{{proof}}`, `{{sender_name}}`, `{{sender_company}}`. No expressions, code, conditionals, or recursive substitution. A missing first name gives “Hi there”. Empty proof contributes no proof sentence. Template-like text remaining after rendering withholds that record's draft.

## Signal CSV

Headers: contact_id,email,domain,type,observed_at,source_ref. Identity and type are required on every row. If contact ID/email are supplied, all supplied contact identities must match the same record. Domain-only events apply at company level; a supplied domain does not override a mismatched contact identity. Identity fields are not used to merge prospect records.

Blank dates or sources remain visible but add no priority; malformed nonblank dates are input errors. Relevant types come from the brief's `signal_types`. Duplicate identical events count once. Qualified records sort by matched preferences, eligible signal count, latest eligible signal date, and source-row ID. The last tie-breaker means reordering the input may reorder tied records.

## Suppression CSV

Headers: type,value,reason. Types: email, contact_id, domain. Entries must have a nonempty value and reason; malformed email/domain entries are rejected. A domain suppresses an exact company domain or email domain; it does not automatically match all subdomains. Matching any identity alias in a merged contact suppresses the record. Suppression changes contact eligibility, not the fit assessment.

An omitted suppression file means unknown coverage; a supplied empty file means zero supplied entries. Neither proves a list is complete. Eligibility in this kit means eligible to produce a local draft, not authorized for sending.

## Outputs and errors

`run.json` schema_version 1.0 preserves source rows, configuration, hashes, summary, rule-level evidence, dispositions, signal decisions, ranks, draft blockers, and drafts. Dates and input hashes make a run reproducible; no wall-clock generation time enters the result. The engine version is recorded.

Successful CLI commands exit 0; input or filesystem errors return 2 and a JSON error on stderr. Output directories/files must be new. Default CSV lists are separated by fit status; suppressed qualified records therefore appear in qualified.csv with their contact_status visible, but never in drafts.json. All artifacts are local and may contain the operator's supplied contact data.

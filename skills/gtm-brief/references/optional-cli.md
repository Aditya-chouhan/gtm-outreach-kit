# Optional local CLI workflow

Read only when the user explicitly chooses the local CSV helper. The CLI is not required for this skill and covers only a subset of its workflow.

# Brief contract

A brief is a UTF-8 JSON object with `schema_version: "1.0"`, a name, and a nonempty `required` list. Optional lists are `preferences` and `exclusions`. Each rule contains exactly `id`, `field`, `op`, and `value`; IDs are unique lowercase slugs.

Fields: contact_id, first_name, email, company, domain, industry, employees, country, role. `employees` uses nonnegative integer values. All other rule values are nonempty strings. Supported operations are `equals`, `in` (a list), and `range` (inclusive minimum/maximum integers, employees only). Text comparison trims whitespace and ignores case.

Example of a deliberately hypothetical rule, to use only if the user chooses this audience:

```json
{"id":"target-size","field":"employees","op":"range","value":[10,200]}
```

`offer` accepts `summary` and `proof_points` (strings). `sender` accepts `name` and `company`. `column_map` maps canonical fields to exact input headers. `signal_types` lists relevant event types. `signal_max_age_days` defaults to 30; `evidence_max_age_days` defaults to 365. Both are configurable nonnegative integers, not empirical GTM benchmarks.

`templates` optionally replaces `subject`, `first`, and `follow_up`. Variables are double-braced names: greeting, first_name, company, offer, proof, sender_name, sender_company. No conditionals or executable expressions.

The installed CLI is the validator. Missing `gtmkit` is an environment prerequisite to report; do not silently install packages or substitute a made-up command. `gtmkit --help` lists the supported operations.

# Engineering case study

**Author: Aditya Chouhan.** This is an original portfolio project using synthetic data, not a client deployment.

## Problem

A prospect spreadsheet can look plausible while hiding duplicate identities, missing evidence, unsupported fit scores, and contacts that should be suppressed. An agent can then turn that ambiguity into confident-looking outreach. The engineering question was: can a reviewer reproduce why each record passed, ranked, and received a draft without subscribing to a specific GTM platform?

## Design

The project separates business judgment from mechanics. The operator chooses the audience and supplies claims; the brief makes those decisions explicit. Python evaluates the brief, preserves contradictory observations, and exports receipts. Six agent skills help an assistant formulate and review this work without reimplementing calculations in conversation.

Three choices carry most of the design:

1. **Preserve observations instead of flattening contradictions.** Identity joins expose conflicts and retain original rows. A high-looking score cannot erase an unresolved employer or email.
2. **Keep fit separate from contact eligibility.** A qualified suppressed contact remains a qualified contact with a suppression reason. Its draft is withheld. This avoids hiding the difference between commercial fit and operational readiness.
3. **Make the first demo complete and offline.** The wheel contains all synthetic inputs and report assets. A reviewer can run it without an API key, LLM provider, account, or network connection.

The report is deliberately a static artifact with local filtering. It can be opened, shared, or archived without an application server. Imported text is escaped before rendering, and formula-looking CSV cells are neutralized for spreadsheet use.

## What was verified

The test suite covers evidence age, exclusions, missing data, duplicate chains, suppression aliases, ranking, template blockers, output preservation, malformed inputs, and escaping. Example schema checks run the fixture with Python socket entry points blocked. The package is built and installed into an independent virtual environment; the CLI is exercised outside the checkout. Browser checks cover counts, filtering, evidence expansion, mobile overflow, and external requests. Actual local receipts live under `evidence/`.

The synthetic fixture starts with 100 rows and produces 90 unique contacts, 31 qualified records, 32 review records, 27 exclusions, and 24 draft packs. These values establish that the fixture behaves as specified. They do not demonstrate conversion lift, revenue, deliverability, research accuracy, or live campaign reliability.

## Tradeoffs and next evidence

The deterministic template renderer is less flexible than a model writer but easier to reproduce. The installed assistant can improve wording without making the CLI depend on a provider. The rule engine supports a small set of inspectable operations; it is not a general expression language. Source dates and labels are supplied, not independently retrieved. The 30/365-day windows are configurable defaults, not empirically optimized thresholds.

An appropriate next validation would be an operator-approved, anonymized export with human-labeled fit decisions and explicit ground truth. Measure disagreements and false qualifications before adding a connector or claiming performance. That dataset and evaluation have not been run.

# Draft contracts

The standalone renderer is deterministic and makes no model calls. Templates can use {{greeting}}, {{first_name}}, {{company}}, {{offer}}, {{proof}}, {{sender_name}}, {{sender_company}}. Unknown and malformed placeholders are refused. Values are substituted once and are never executed.

Draft generation requires qualified fit, a nonsuppressed syntactically valid email, company name, offer.summary, sender.name, and sender.company. A missing first name yields a plain greeting. Missing optional proof contributes no proof sentence. Placeholder-like text inside input data withholds that draft for review.

The default renderer makes no claim that the email was verified or that messages are delivery-ready. Local syntax validation cannot establish deliverability or permission to contact.

Use `gtmkit prepare ... --out <new-directory>` after a brief/template change. Draft artifacts live in drafts.json and in the HTML report. `claim_sources` identifies supplied prospect rows and brief paths; this is traceability, not independent fact checking.

Improving language with the host assistant is optional and uses that assistant's normal capabilities. Do not imply that the local CLI generated AI research or ran model evaluations.

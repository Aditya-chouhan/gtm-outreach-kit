# Working template and review example

```text
Outcome/example/trigger/owner
Step/available capability/input/output/state/external effect
Identity/idempotency
Review/suppression
Failure/retry or reconcile/owner
Acceptance cases/status
```

## Review example

**Request:** A send timed out; retry until it succeeds.

**Expected behavior:** Inspect provider or thread evidence and reconcile the ambiguous outcome before sending again.

Inspect the actual generated artifact and any claimed external effects. An instruction file containing the desired wording is not proof of assistant behavior.

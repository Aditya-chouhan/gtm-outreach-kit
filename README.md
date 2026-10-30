# GTM Outreach Kit — Agent Skills

**25 standalone GTM skills for the AI agent and tools you already use.**

Created by **Aditya Chouhan**. Strategy, account research, prospecting, qualification, outreach, CRM hygiene, content and experimentation—with concrete workflows, evidence requirements, artifact templates and review examples.

The skills are the product. Each folder contains instructions an agent can load for a specific task. Use them with supplied documents, local files, connected services or browser access. **The skills do not require Python, this project's CLI, an OXYGEN account, or a particular data vendor.** Live research and execution still require appropriate tool access; instruction files do not create integrations.

[Browse all 25 skills](docs/skill-catalog.md) · [Installation](docs/installation.md) · [Example requests](docs/start-here.md) · [Evaluation scenarios](docs/skill-scenarios.md)

## Start with one useful skill

1. Choose a task from the catalog below.
2. Copy its entire folder from `skills/` into your agent's documented skill directory. Keep `SKILL.md`, `references/` and `agents/` together.
3. Invoke it explicitly, or let your host select it when supported. Example:

> Use `$gtm-account-research` to research this company's fit for our offer. Use accessible sources, separate facts from hypotheses, and give me a dated account brief. Do not enrich contacts or send anything.

No CLI installation is needed. If your host supports custom instructions rather than skill-folder discovery, supply the selected `SKILL.md` and its linked reference. Host discovery and automatic invocation differ; universal compatibility is not claimed.

## The library

| Job | Skills |
| --- | --- |
| Understand the business | [Brief](skills/gtm-brief/SKILL.md), [ICP](skills/gtm-icp/SKILL.md), [Positioning](skills/gtm-positioning/SKILL.md), [Diagnosis](skills/gtm-diagnose/SKILL.md) |
| Find and understand buyers | [Account sourcing](skills/gtm-account-sourcing/SKILL.md), [Account research](skills/gtm-account-research/SKILL.md), [Buying-group mapping](skills/gtm-buyer-map/SKILL.md), [Enrichment planning](skills/gtm-enrichment-plan/SKILL.md) |
| Prepare prospect data | [Data inspection](skills/gtm-data-inspect/SKILL.md), [Qualification](skills/gtm-qualify/SKILL.md), [Prioritization](skills/gtm-prioritize/SKILL.md), [Signal design](skills/gtm-signal-design/SKILL.md) |
| Prepare and handle outreach | [Drafting](skills/gtm-draft/SKILL.md), [Sequence design](skills/gtm-sequence-design/SKILL.md), [Readiness review](skills/gtm-review/SKILL.md), [Reply triage](skills/gtm-reply-triage/SKILL.md), [Meeting handoff](skills/gtm-meeting-handoff/SKILL.md) |
| Maintain the operation | [CRM hygiene](skills/gtm-crm-hygiene/SKILL.md), [Delivery investigation](skills/gtm-deliverability/SKILL.md), [Workflow design](skills/gtm-workflow-design/SKILL.md), [Operating review](skills/gtm-operating-review/SKILL.md) |
| Learn and communicate | [Pipeline analysis](skills/gtm-pipeline-analysis/SKILL.md), [Experiments](skills/gtm-experiment/SKILL.md), [LinkedIn content](skills/gtm-linkedin-content/SKILL.md), [Content repurposing](skills/gtm-content-repurpose/SKILL.md) |

## What each skill provides

- A specific trigger and boundaries so the agent selects the right workflow.
- Task-specific decisions and evidence checks, including how to work with unknowns and conflicting inputs.
- A concrete working template and a realistic review example in its own folder.
- Clear separation between analysis, proposed actions, drafts and verified execution.
- A fallback deliverable when a required source or tool is unavailable.

Use the narrowest skill that answers the request. The catalog is not an automatic campaign, and installing every skill does not authorize every workflow.

## Optional folder installer

Manual copying works without Python. If Python 3.11+ is available, this standard-library script can preview and copy selected folders:

```bash
python3 scripts/install_skills.py --list
python3 scripts/install_skills.py --skills gtm-icp gtm-account-research \
  --target /path/to/your/agent/skills --dry-run
python3 scripts/install_skills.py --skills gtm-icp gtm-account-research \
  --target /path/to/your/agent/skills
```

Replace the target with your host's documented path. The installer copies local files only, refuses existing skill destinations and does not change agent configuration, credentials or permissions. See [installation](docs/installation.md).

## Optional local outreach helper

The repository also retains a Python CLI for a narrower deterministic CSV workflow:

**Prospect CSV → normalization → qualification → ranking → draft emails → HTML report.**

It is useful for repeatable data processing and does not implement the whole skills library. Six skills include a separately linked optional CLI reference. The other skills work without it as well.

[Run the optional helper](docs/optional-cli.md) · [Inspect the synthetic report](docs/demo-report.html) · [Input contract](docs/input-contract.md)

## Validation and limits

```bash
python -m pip install -e '.[dev]'
python -m pytest -q
python scripts/check_skills.py
python scripts/check_examples.py
```

Library checks validate the 25-folder manifest, discovery metadata, self-contained references and optional installation behavior. Tests also cover the existing CLI. These checks do **not** establish that every model follows the instructions or that the skills improve revenue. [Behavioral scenarios](docs/skill-scenarios.md) are provided for independent evaluation; no independent model evaluation is claimed.

The library contains no bundled paid-provider integration, autonomous sending engine or universal account connector. Use the agent's actual connected capabilities and the user's task scope. Found contact information, a draft or a diagram does not prove permission, delivery or a deployed integration.

[Library verification](evidence/skills-revision.json) · [Historical CLI verification](evidence/verification.json) · [Architecture](docs/architecture.md)

## Authorship and inspiration

Original code, skill instructions, examples and templates by **Aditya Chouhan**, under the [MIT License](LICENSE). The public [OXYGEN GTM skills repository](https://github.com/OXYGEN-CRO/gtm-skills) inspired the broad problem area. This is an independent, tool-neutral implementation; it copies none of OXYGEN's skill text, code or assets and is unaffiliated with OXYGEN.

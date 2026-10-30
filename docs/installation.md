# Install the skills

## Folder-based agent hosts

Download or clone this repository and select folders from `skills/`. Copy the entire selected folder into the skill directory documented by your host. Keep the folder name, SKILL.md and supporting references intact. The `agents/openai.yaml` files provide optional host-specific UI metadata; the entrypoint and references hold the task instructions.

You can install one skill without installing the others. There are no cross-skill file dependencies. Skill invocation/discovery depends on the host; invoke by the skill's name using the host's normal syntax.

## Manual instruction loading

For an assistant that accepts files or custom instructions but does not discover skill folders, supply the chosen SKILL.md and its linked reference. This is manual use of the instructions, not a claim of native integration. A source document cannot override the actual user's request or create tool permissions.

## Optional copy helper

`scripts/install_skills.py` requires Python 3.11+ and no third-party packages. It performs no network request. `--list` reads the library manifest. Select `--skills NAME ...` or `--all`, and set an explicit `--target`. Add `--dry-run` to inspect the copy plan without creating directories.

Existing skill destinations, symlinked source bundles and unsupported bundle files are refused. All selected sources/destinations are checked before copying begins. The helper never overwrites an existing skill. If a host already has a skill with the same name, review the differences manually and choose a separate target or replace it yourself after preserving your changes.

```bash
python3 scripts/install_skills.py --list
python3 scripts/install_skills.py --skills gtm-draft --target /path/to/agent/skills --dry-run
python3 scripts/install_skills.py --skills gtm-draft --target /path/to/agent/skills
```

Copying instructions does not connect tools or authorize external actions. Live research, CRM changes and messages need the corresponding access and user scope. No Python or local CLI is required for manual folder installation or normal use of the skills.

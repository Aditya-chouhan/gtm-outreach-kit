"""Validate manifest, metadata and self-contained references, not model behavior."""
import json
import re
from pathlib import Path
import yaml

ROOT = Path(__file__).resolve().parents[1]


def check(root=ROOT):
    manifest = json.loads((root / 'skills.json').read_text())
    entries = manifest['skills']
    names = [s['name'] for s in entries]
    assert len(names) == 25 and len(set(names)) == 25, 'Expected 25 distinct skills'
    folders = {p.name for p in (root / 'skills').iterdir() if p.is_dir()}
    assert folders == set(names), 'Manifest and folders differ'
    links = 0
    for entry in entries:
        name = entry['name']
        assert entry['path'] == 'skills/' + name
        assert entry['required_tools'] == [] and entry['cli_required'] is False
        folder = root / entry['path']
        skill = (folder / 'SKILL.md').read_text()
        assert skill.startswith('---\n')
        front = yaml.safe_load(skill.split('---', 2)[1])
        assert front['name'] == name and front['description'] == entry['description']
        assert re.fullmatch(r'[a-z][a-z0-9-]{0,63}', name)
        ui = yaml.safe_load((folder / 'agents/openai.yaml').read_text())['interface']
        assert 25 <= len(ui['short_description']) <= 64
        assert '$' + name in ui['default_prompt']
        assert (folder / 'references/worked-example.md').is_file()
        for path in folder.rglob('*'):
            assert not path.is_symlink(), 'Symlinked bundle member'
            if not path.is_file() or path.suffix != '.md':
                continue
            for target in re.findall(r'\[[^\]]*\]\(([^)]+)\)', path.read_text()):
                if '://' in target:
                    continue
                resolved = (path.parent / target.split('#', 1)[0]).resolve()
                assert folder.resolve() in resolved.parents and resolved.is_file(), f'Broken/cross-bundle reference: {path}: {target}'
                links += 1
    return {'skills': len(names), 'self_contained_reference_links': links, 'manifest': 'passed', 'discovery_metadata': 'passed', 'requires_cli': False, 'behavioral_evaluation': 'Not established by structural checks'}


if __name__ == '__main__':
    print(json.dumps(check(), indent=2))

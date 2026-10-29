"""Check package discovery metadata and self-contained skill references."""
import json
import re
import yaml
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]

def main():
    folders=sorted((ROOT/'skills').iterdir())
    assert len(folders)==6, 'Expected six focused skills'
    count=0
    for folder in folders:
        skill=(folder/'SKILL.md').read_text()
        assert skill.startswith('---\n')
        parsed=yaml.safe_load(skill.split('---',2)[1])
        assert parsed['name']==folder.name and isinstance(parsed['description'],str)
        front=skill.split('---',2)[1]
        assert re.search(r'^name: '+re.escape(folder.name)+r'$',front,re.M)
        description=re.search(r'^description: (.+)$',front,re.M)
        assert description and len(json.loads(description[1]))>30
        metadata=(folder/'agents'/'openai.yaml').read_text()
        assert isinstance(yaml.safe_load(metadata)['interface'],dict)
        fields=dict(re.findall(r'^  ([a-z_]+): (.+)$',metadata,re.M))
        assert 25<=len(json.loads(fields['short_description']))<=64
        assert '$'+folder.name in json.loads(fields['default_prompt'])
        for md in folder.rglob('*.md'):
            for target in re.findall(r'\[[^\]]*\]\(([^)]+)\)',md.read_text()):
                if '://' in target:
                    continue
                resolved=(md.parent/target.split('#',1)[0]).resolve()
                assert folder.resolve() in resolved.parents and resolved.is_file(), f'Broken or external dependency: {target}'
                count+=1
    print(f'PASS: {len(folders)} skills; {count} self-contained reference links; valid discovery and UI metadata.')

if __name__=='__main__':
    main()

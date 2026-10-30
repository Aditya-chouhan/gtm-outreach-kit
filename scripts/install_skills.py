"""Copy selected local skill bundles to an explicitly chosen agent directory."""
import argparse
import json
import re
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def catalog(root=ROOT):
    data = json.loads((root / 'skills.json').read_text(encoding='utf-8'))
    entries = data['skills']
    names = [item['name'] for item in entries]
    if len(names) != len(set(names)):
        raise ValueError('Duplicate skill names in manifest')
    return {item['name']: item for item in entries}


def install(names, target, *, dry_run=False, root=ROOT):
    available = catalog(root)
    if not names or len(names) != len(set(names)):
        raise ValueError('Select one or more distinct skills')
    if set(names) - available.keys():
        raise ValueError('Unknown skills: ' + ', '.join(sorted(set(names) - available.keys())))
    target = Path(target).expanduser().resolve()
    if target.exists() and not target.is_dir():
        raise ValueError('Target must be a directory')
    plan = []
    for name in names:
        if not re.fullmatch(r'[a-z][a-z0-9-]{0,63}', name):
            raise ValueError('Invalid skill name')
        source = root / 'skills' / name
        destination = target / name
        if source.is_symlink() or not source.is_dir() or not (source / 'SKILL.md').is_file():
            raise ValueError('Invalid skill bundle: ' + name)
        if destination.exists() or destination.is_symlink():
            raise ValueError('Refusing to overwrite: ' + str(destination))
        for path in source.rglob('*'):
            if path.is_symlink() or (path.is_file() and path.suffix not in {'.md', '.yaml', '.json'}):
                raise ValueError('Unsupported bundle member: ' + str(path))
        plan.append((source, destination))
    if not dry_run:
        target.mkdir(parents=True, exist_ok=True)
        for source, destination in plan:
            # Exclusive reservation prevents a concurrent install from overwriting.
            destination.mkdir()
            shutil.copytree(source, destination, dirs_exist_ok=True)
    return [{'name': src.name, 'destination': str(dst), 'action': 'planned' if dry_run else 'copied'} for src, dst in plan]


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    selection = parser.add_mutually_exclusive_group(required=True)
    selection.add_argument('--list', action='store_true')
    selection.add_argument('--all', action='store_true')
    selection.add_argument('--skills', nargs='+')
    parser.add_argument('--target', type=Path)
    parser.add_argument('--dry-run', action='store_true')
    args = parser.parse_args(argv)
    try:
        if args.list:
            print(json.dumps(list(catalog().values()), indent=2))
        else:
            if args.target is None:
                parser.error('--target is required to install or preview')
            names = list(catalog()) if args.all else args.skills
            print(json.dumps(install(names, args.target, dry_run=args.dry_run), indent=2))
        return 0
    except (ValueError, OSError, KeyError) as exc:
        print(json.dumps({'error': str(exc)}), file=sys.stderr)
        return 2


if __name__ == '__main__':
    raise SystemExit(main())

import importlib.util
import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('folder_installer', ROOT / 'scripts/install_skills.py')
installer = importlib.util.module_from_spec(spec)
spec.loader.exec_module(installer)


def test_library_manifest_and_self_contained_bundles():
    manifest = installer.catalog()
    assert len(manifest) == 25
    for name, entry in manifest.items():
        folder = ROOT / entry['path']
        assert entry['cli_required'] is False and entry['required_tools'] == []
        assert (folder / 'SKILL.md').is_file()
        assert (folder / 'references/worked-example.md').is_file()
        assert (folder / 'agents/openai.yaml').is_file()


def test_install_selected_preserves_full_folder(tmp_path):
    target = tmp_path / 'skills'
    result = installer.install(['gtm-account-research', 'gtm-brief'], target)
    assert len(result) == 2
    assert set(p.name for p in target.iterdir()) == {'gtm-account-research', 'gtm-brief'}
    for name in ['gtm-account-research', 'gtm-brief']:
        for original in (ROOT / 'skills' / name).rglob('*'):
            if original.is_file():
                assert (target / name / original.relative_to(ROOT / 'skills' / name)).read_bytes() == original.read_bytes()


def test_preview_creates_nothing(tmp_path):
    target = tmp_path / 'does-not-exist' / 'skills'
    result = installer.install(['gtm-draft'], target, dry_run=True)
    assert result[0]['action'] == 'planned'
    assert not target.parent.exists()


def test_existing_destination_prevents_all_selected_copies(tmp_path):
    target = tmp_path / 'skills'
    (target / 'gtm-draft').mkdir(parents=True)
    keep = target / 'gtm-draft' / 'my-custom-file.md'
    keep.write_text('retain my edits')
    with pytest.raises(ValueError, match='overwrite'):
        installer.install(['gtm-brief', 'gtm-draft'], target)
    assert keep.read_text() == 'retain my edits'
    assert not (target / 'gtm-brief').exists()


@pytest.mark.parametrize('names', [[], ['gtm-draft', 'gtm-draft'], ['missing-skill'], ['../escape']])
def test_invalid_selection_does_not_create_target(tmp_path, names):
    target = tmp_path / 'skills'
    with pytest.raises(ValueError):
        installer.install(names, target)
    assert not target.exists()


def test_symlinked_source_rejected_before_copy(tmp_path):
    root = tmp_path / 'source'
    (root / 'skills').mkdir(parents=True)
    real = tmp_path / 'real'
    real.mkdir()
    (real / 'SKILL.md').write_text('untrusted')
    (root / 'skills' / 'gtm-draft').symlink_to(real, target_is_directory=True)
    (root / 'skills.json').write_text(json.dumps({'skills': [{'name': 'gtm-draft'}]}))
    with pytest.raises(ValueError, match='Invalid skill'):
        installer.install(['gtm-draft'], tmp_path / 'target', root=root)
    assert not (tmp_path / 'target').exists()


def test_installer_runs_without_site_packages_or_cli(tmp_path):
    # Isolated Python disables site packages; an empty PATH hides the optional CLI.
    env = dict(os.environ, PATH='')
    target = tmp_path / 'installed'
    result = subprocess.run([sys.executable, '-I', '-S', str(ROOT / 'scripts/install_skills.py'), '--all', '--target', str(target)], env=env, capture_output=True, text=True, check=True)
    assert len(json.loads(result.stdout)) == 25
    assert len(list(target.iterdir())) == 25


def test_list_is_non_mutating(tmp_path):
    result = subprocess.run([sys.executable, '-I', '-S', str(ROOT / 'scripts/install_skills.py'), '--list'], cwd=tmp_path, capture_output=True, text=True, check=True)
    assert len(json.loads(result.stdout)) == 25
    assert not list(tmp_path.iterdir())

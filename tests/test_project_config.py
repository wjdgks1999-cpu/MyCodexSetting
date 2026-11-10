import json
from pathlib import Path
import subprocess
import sys
from tempfile import TemporaryDirectory
import tomllib
import unittest


KIT = Path(__file__).resolve().parents[1] / 'kit'


class ProjectConfigTests(unittest.TestCase):
    def setUp(self):
        temporary = TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.target = Path(temporary.name) / 'target'
        self.target.mkdir()
        (self.target / 'PRD.md').write_text('Create a service.\n', encoding='utf-8')
        self.config = self.target / '.codex/config.toml'

    def install(self, apply=True):
        args = [sys.executable, '-X', 'utf8', '-B', str(KIT / 'mycodex.py'),
                'init', '--target', str(self.target), '--requirements', 'PRD.md']
        return subprocess.run(args + (['--apply'] if apply else []),
                              capture_output=True, text=True, encoding='utf-8')

    def ready_and_validate(self):
        index = self.target / '.context/index.md'
        index.write_bytes(index.read_bytes().replace(b'needs-review', b'ready'))
        return subprocess.run([
            sys.executable, '-X', 'utf8', '-B', str(self.target / '.mycodex/mycodex.py'),
            'validate', '--target', str(self.target), '--strict', '--json',
        ], capture_output=True, text=True, encoding='utf-8')

    def test_dry_run_plans_config_without_creating_files(self):
        result = self.install(apply=False)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn('create: .codex/config.toml', result.stdout)
        self.assertEqual([path.name for path in self.target.iterdir()], ['PRD.md'])

    def test_fresh_install_copies_template_to_project_config(self):
        result = self.install()
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertTrue(self.config.is_file(), 'Project config was not created')
        template = (KIT / 'templates/config.toml').read_text(encoding='utf-8')
        self.assertEqual(self.config.read_text(encoding='utf-8'), template)
        tomllib.loads(self.config.read_text(encoding='utf-8'))
        checked = self.ready_and_validate()
        self.assertEqual(checked.returncode, 0, checked.stdout + checked.stderr)

    def test_existing_config_and_other_codex_files_are_preserved(self):
        self.config.parent.mkdir()
        custom = b'model = "project-specific"\n# preserve user choices\n'
        self.config.write_bytes(custom)
        other = self.config.parent / 'rules.txt'
        other.write_bytes(b'project rules\n')
        for _ in range(2):
            result = self.install()
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            self.assertIn('preserve: .codex/config.toml', result.stdout)
            self.assertEqual(self.config.read_bytes(), custom)
            self.assertEqual(other.read_bytes(), b'project rules\n')
        checked = self.ready_and_validate()
        self.assertEqual(checked.returncode, 0, checked.stdout + checked.stderr)

    def test_user_can_change_config_after_installation(self):
        result = self.install()
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertTrue(self.config.is_file(), 'Project config was not created')
        custom = b'model = "my-choice"\nweb_search = "disabled"\n'
        self.config.write_bytes(custom)
        checked = self.ready_and_validate()
        self.assertEqual(checked.returncode, 0, checked.stdout + checked.stderr)
        reinstalled = self.install()
        self.assertEqual(reinstalled.returncode, 0, reinstalled.stdout + reinstalled.stderr)
        self.assertEqual(self.config.read_bytes(), custom)

    def test_config_directory_conflict_stops_before_any_install_write(self):
        self.config.mkdir(parents=True)
        result = self.install()
        self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
        self.assertIn('UNSAFE_DESTINATION: .codex/config.toml', result.stdout)
        self.assertFalse((self.target / '.mycodex').exists())
        self.assertFalse((self.target / 'AGENTS.md').exists())

    def test_installed_template_is_checked_while_user_config_is_not_hashed(self):
        result = self.install()
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        template = self.target / '.mycodex/templates/config.toml'
        self.assertTrue(template.is_file(), 'Managed config template was not installed')
        manifest = json.loads((self.target / '.mycodex/manifest.json').read_text(encoding='utf-8'))
        self.assertNotIn('.codex/config.toml', manifest['files'])
        with template.open('ab') as stream:
            stream.write(b'\n# actual template content change\n')
        checked = self.ready_and_validate()
        findings = json.loads(checked.stdout)['findings']
        self.assertIn(('ASSET_MISMATCH', '.mycodex/templates/config.toml'),
                      {(item['code'], item['path']) for item in findings})


if __name__ == '__main__':
    unittest.main()

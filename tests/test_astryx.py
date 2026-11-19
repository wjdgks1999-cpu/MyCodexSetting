"""Optional Astryx delivery must not become an application dependency install."""
import json
import os
from pathlib import Path
import re
import subprocess
import sys
from tempfile import TemporaryDirectory
import unittest

ROOT = Path(__file__).resolve().parents[1]


class AstryxInstallTests(unittest.TestCase):
    def setUp(self):
        temporary = TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.target = Path(temporary.name) / 'project'
        self.target.mkdir()
        (self.target / 'PRD.md').write_text('Keep the current stack.\n', encoding='utf-8')

    def install(self, apply=False):
        args = [sys.executable, '-X', 'utf8', '-B', str(ROOT / 'kit/mycodex.py'),
                'init', '--target', str(self.target), '--requirements', 'PRD.md']
        if apply:
            args.append('--apply')
        return subprocess.run(args, capture_output=True, text=True, encoding='utf-8',
                              env={**os.environ, 'PATH': ''})

    def snapshot(self):
        return {p.relative_to(self.target).as_posix(): p.read_bytes()
                for p in self.target.rglob('*') if p.is_file()}

    def test_base_install_without_node_provides_explicit_skill_and_usable_guide(self):
        before = self.snapshot()
        dry = self.install()
        self.assertEqual(dry.returncode, 0, dry.stdout + dry.stderr)
        self.assertEqual(before, self.snapshot())
        result = self.install(True)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        skill = self.target / '.agents/skills/astryx'
        self.assertTrue((skill / 'SKILL.md').is_file())
        self.assertIn('allow_implicit_invocation: false', (skill / 'agents/openai.yaml').read_text())
        guide = self.target / '.mycodex/integrations/astryx/README.md'
        self.assertTrue(guide.is_file())
        for link in re.findall(r'\[[^\]]+\]\(([^)]+)\)', guide.read_text(encoding='utf-8')):
            if '://' not in link and not link.startswith('#'):
                self.assertTrue((guide.parent / link.split('#', 1)[0]).is_file(), link)
        for name in ('package.json', 'package-lock.json', 'node_modules'):
            self.assertFalse((self.target / name).exists(), name)
        installed = self.snapshot()
        self.assertEqual(self.install(True).returncode, 0)
        self.assertEqual(installed, self.snapshot())

    def test_existing_application_and_user_configuration_are_preserved(self):
        for name, text in {'package.json': '{"dependencies":{"react":"18.3.1"}}',
                           'package-lock.json': '{"lockfileVersion":3}',
                           'AGENTS.md': 'Keep the existing rules.\n',
                           '.codex/config.toml': 'model = "custom-model"\n'}.items():
            path = self.target / name
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(text, encoding='utf-8')
        before = self.snapshot()
        result = self.install(True)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertTrue((self.target / '.agents/skills/astryx/SKILL.md').is_file())
        self.assertTrue(all(self.snapshot()[p] == content for p, content in before.items()))

    def test_foreign_astryx_skill_blocks_all_writes(self):
        path = self.target / '.agents/skills/astryx/SKILL.md'
        path.parent.mkdir(parents=True)
        path.write_text('User owned skill.\n', encoding='utf-8')
        before = self.snapshot()
        for apply in (False, True):
            result = self.install(apply)
            self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
            self.assertIn('ASSET_CONFLICT', result.stdout)
            self.assertEqual(before, self.snapshot())

    def test_edited_astryx_asset_is_not_overwritten(self):
        self.assertEqual(self.install(True).returncode, 0)
        path = self.target / '.agents/skills/astryx/SKILL.md'
        self.assertTrue(path.is_file())
        with path.open('a', encoding='utf-8') as stream:
            stream.write('\nUser customization.\n')
        before = self.snapshot()
        self.assertEqual(self.install(True).returncode, 1)
        self.assertEqual(before, self.snapshot())

    def test_prior_version_manifest_is_not_silently_upgraded(self):
        self.assertEqual(self.install(True).returncode, 0)
        path = self.target / '.mycodex/manifest.json'
        data = json.loads(path.read_text(encoding='utf-8'))
        self.assertNotEqual(data['kit_version'], '0.5.0')
        data['kit_version'] = '0.5.0'
        path.write_text(json.dumps(data), encoding='utf-8')
        before = self.snapshot()
        result = self.install(True)
        self.assertEqual(result.returncode, 1)
        self.assertIn('MANIFEST_CONFLICT', result.stdout)
        self.assertEqual(before, self.snapshot())


if __name__ == '__main__':
    unittest.main()

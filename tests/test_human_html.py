import json
from pathlib import Path
import shutil
import subprocess
import sys
from tempfile import TemporaryDirectory
import unittest


KIT = Path(__file__).resolve().parents[1] / 'kit'
HTML = '''<!doctype html><html lang="ko"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>구조 설명</title><style>body { max-width: 70ch; margin: auto; }</style>
</head><body><h1>구조 설명</h1><p>HTML_BODY_MARKER 한글 설명</p></body></html>'''


class HumanHtmlTests(unittest.TestCase):
    def setUp(self):
        temporary = TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.target = Path(temporary.name) / '한글 프로젝트'
        self.target.mkdir()
        (self.target / 'PRD.md').write_text('Explain this project.\n', encoding='utf-8')
        self.cli = self.target / '.mycodex/mycodex.py'
        self.helper = self.target / '.agents/skills/human-html/scripts/save_html.py'
        self.install()
        self.index = self.target / '.context/index.md'
        self.index.write_bytes(self.index.read_bytes().replace(b'needs-review', b'ready'))

    def install(self):
        result = subprocess.run([
            sys.executable, '-X', 'utf8', '-B', str(KIT / 'mycodex.py'), 'init', '--target', str(self.target),
            '--requirements', 'PRD.md', '--apply',
        ], capture_output=True, text=True, encoding='utf-8')
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def save(self, name='structure', content=HTML):
        return subprocess.run([
            sys.executable, '-X', 'utf8', '-B', str(self.helper), '--target', str(self.target), '--name', name,
        ], input=content, capture_output=True, text=True, encoding='utf-8')

    def check(self, path):
        return subprocess.run([
            sys.executable, '-X', 'utf8', '-B', str(self.helper), '--target', str(self.target), '--check', path,
        ], capture_output=True, text=True, encoding='utf-8')

    def validate(self):
        return subprocess.run([
            sys.executable, '-X', 'utf8', '-B', str(self.cli), 'validate', '--target', str(self.target),
            '--strict', '--json',
        ], capture_output=True, text=True, encoding='utf-8')

    def test_install_includes_helper_and_reinstall_preserves_project(self):
        self.assertTrue(self.helper.is_file(), 'Installed HTML save helper is missing')
        self.assertFalse((self.target / '.human-docs').exists())
        agents = self.target / 'AGENTS.md'
        agents.write_text(agents.read_text(encoding='utf-8') + '\nUser rule.\n', encoding='utf-8')
        preserved = {path: path.read_bytes() for path in (agents, self.index)}
        self.install()
        for path, content in preserved.items():
            self.assertEqual(path.read_bytes(), content)
        result = self.validate()
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_save_and_check_return_no_body_and_preserve_index(self):
        before = self.index.read_bytes()
        result = self.save('앱-구조')
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        relative = result.stdout.strip()
        self.assertTrue(relative.startswith('.human-docs/'))
        self.assertTrue(relative.endswith('.html'))
        self.assertEqual((self.target / relative).read_text(encoding='utf-8'), HTML)
        self.assertNotIn('HTML_BODY_MARKER', result.stdout + result.stderr)
        checked = self.check(relative)
        self.assertEqual(checked.returncode, 0, checked.stdout + checked.stderr)
        self.assertNotIn('HTML_BODY_MARKER', checked.stdout + checked.stderr)
        self.assertEqual(self.index.read_bytes(), before)
        self.assertEqual(self.validate().returncode, 0)

    def test_repeated_save_keeps_existing_html(self):
        first = self.save()
        self.assertEqual(first.returncode, 0, first.stderr)
        original = self.target / first.stdout.strip()
        content = original.read_bytes()
        second = self.save(content=HTML.replace('한글 설명', '다른 설명'))
        self.assertEqual(second.returncode, 0, second.stderr)
        self.assertNotEqual(first.stdout, second.stdout)
        self.assertEqual(original.read_bytes(), content)

    def test_invalid_html_is_not_saved_or_echoed(self):
        for content in ('', 'HTML_BODY_MARKER', HTML.replace('<title>구조 설명</title>', ''),
                        HTML.replace('name="viewport"', 'name="other"')):
            with self.subTest(content=content[:20]):
                result = self.save(content=content)
                self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
                self.assertNotIn('HTML_BODY_MARKER', result.stdout + result.stderr)
                self.assertFalse((self.target / '.human-docs').exists())

    def test_unsafe_name_cannot_write_outside_output(self):
        for name in ('../escape', '/absolute', 'a/b', r'a\b', '', '%2e%2e', 'a\nname'):
            with self.subTest(name=name):
                result = self.save(name)
                self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
                self.assertFalse((self.target / '.human-docs').exists())

    def test_malformed_declaration_is_reported_without_echoing_input(self):
        result = self.save(content=HTML + '<![HTML_BODY_MARKER]>')
        self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
        self.assertIn('INVALID_HTML', result.stderr)
        self.assertNotIn('HTML_BODY_MARKER', result.stdout + result.stderr)
        self.assertNotIn('Traceback', result.stderr)
        self.assertFalse((self.target / '.human-docs').exists())
        folder = self.target / '.human-docs'
        folder.mkdir()
        (folder / 'malformed.html').write_text(HTML + '<![HTML_BODY_MARKER]>', encoding='utf-8')
        checked = self.check('.human-docs/malformed.html')
        self.assertEqual(checked.returncode, 1, checked.stdout + checked.stderr)
        self.assertIn('INVALID_HTML', checked.stderr)
        self.assertNotIn('HTML_BODY_MARKER', checked.stdout + checked.stderr)
        self.assertNotIn('Traceback', checked.stderr)

    def test_check_only_accepts_generated_html_path(self):
        for name in ('PRD.md', '../outside.html', '/outside.html', '.human-docs/../PRD.md',
                     '.human-docs/C:escape.html', '.human-docs/report.html:stream.html'):
            with self.subTest(name=name):
                result = self.check(name)
                self.assertEqual(result.returncode, 1, result.stdout + result.stderr)

    def test_custom_folder_ignore_is_preserved_and_reported(self):
        folder = self.target / '.human-docs'
        folder.mkdir()
        for filename in ('.gitignore', '.ignore'):
            with self.subTest(filename=filename):
                path = folder / filename
                path.write_bytes(b'custom-user-rules\n')
                result = self.save()
                self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
                self.assertIn('IGNORE_CONFLICT', result.stderr)
                self.assertEqual(path.read_bytes(), b'custom-user-rules\n')
                self.assertFalse(tuple(folder.glob('*.html')))
                path.unlink()

    def test_root_ignores_are_preserved(self):
        files = [self.target / name for name in ('.gitignore', '.ignore')]
        for path in files:
            path.write_bytes(b'keep-original-rule\n')
        result = self.save()
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        for path in files:
            self.assertEqual(path.read_bytes(), b'keep-original-rule\n')

    @unittest.skipUnless(shutil.which('rg'), 'ripgrep is unavailable')
    def test_ripgrep_excludes_body_with_and_without_git(self):
        result = self.save()
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        for use_git in (False, True):
            with self.subTest(git=use_git):
                if use_git:
                    git = subprocess.run(['git', 'init', '--quiet', str(self.target)], capture_output=True)
                    self.assertEqual(git.returncode, 0, git.stderr)
                search = subprocess.run(['rg', '--hidden', 'HTML_BODY_MARKER', '.'], cwd=self.target,
                                        capture_output=True, text=True, encoding='utf-8')
                self.assertEqual(search.returncode, 1, search.stdout + search.stderr)
                bypass = subprocess.run([
                    'rg', '--hidden', '--no-ignore', '-g', '!.human-docs/**',
                    'HTML_BODY_MARKER', '.',
                ], cwd=self.target, capture_output=True, text=True, encoding='utf-8')
                self.assertEqual(bypass.returncode, 1, bypass.stdout + bypass.stderr)

    def test_new_skill_policy_and_helper_are_validated(self):
        policy = self.target / '.agents/skills/human-html/agents/openai.yaml'
        self.assertTrue(policy.is_file(), 'Installed human-html policy is missing')
        policy.write_bytes(policy.read_bytes().replace(b'false', b'true'))
        result = self.validate()
        codes = {item['code'] for item in json.loads(result.stdout)['findings']}
        self.assertIn('INVALID_SKILL_POLICY', codes)
        self.helper.unlink()
        result = self.validate()
        findings = json.loads(result.stdout)['findings']
        self.assertIn('ASSET_MISMATCH', {item['code'] for item in findings})

    def test_index_quarantined_references_are_rejected_without_reading(self):
        original = self.index.read_text(encoding='utf-8')
        folder = self.target / '.human-docs'
        folder.mkdir()
        (folder / 'report.md').write_bytes(b'\xffHTML_BODY_MARKER')
        for name in ('.human-docs/report.md', './.human-docs/report.md',
                     '.HUMAN-DOCS/report.md', '%2ehuman-docs/report.md'):
            with self.subTest(path=name):
                self.index.write_text(original.replace('`PRD.md`', f'`{name}`'), encoding='utf-8')
                result = self.validate()
                codes = {item['code'] for item in json.loads(result.stdout)['findings']}
                self.assertIn('HUMAN_DOC_REFERENCE', codes)
                self.assertNotIn('INVALID_REFERENCE', codes)
                self.assertNotIn('HTML_BODY_MARKER', result.stdout + result.stderr)

    def test_handoff_cannot_use_generated_html_as_evidence(self):
        result = self.save()
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        relative = result.stdout.strip()
        folder = self.target / '.context/handoffs'
        folder.mkdir()
        template = (self.target / '.mycodex/templates/handoff.md').read_text(encoding='utf-8')
        fields = {
            'goal': 'Resume.', 'timestamp_with_timezone': '2026-11-10T12:00:00+09:00',
            'evidence_links': f'[Generated](../../{relative})',
            'completed_in_progress_blocked_unverified': 'In progress.',
            'commands_results_or_not_run': 'Not run.', 'next_action': 'Read PRD.',
            'current_state_checks_and_git_baseline': 'Check current files.',
        }
        for key, value in fields.items():
            template = template.replace('{{' + key + '}}', value)
        (folder / 'draft.md').write_text(template, encoding='utf-8')
        before = self.index.read_bytes()
        result = subprocess.run([
            sys.executable, '-X', 'utf8', '-B', str(self.cli), 'record-handoff', '--target', str(self.target),
            '--draft', '.context/handoffs/draft.md',
        ], capture_output=True, text=True, encoding='utf-8')
        self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
        self.assertEqual(self.index.read_bytes(), before)
        self.assertEqual([p.name for p in folder.iterdir()], ['draft.md'])

    def test_linked_output_directory_is_rejected(self):
        outside = self.target.parent / 'outside'
        outside.mkdir()
        linked = self.target / '.human-docs'
        if sys.platform == 'win32':
            result = subprocess.run(['cmd', '/c', 'mklink', '/J', str(linked), str(outside)],
                                    capture_output=True)
            if result.returncode:
                self.skipTest('Directory junction creation is unavailable')
        else:
            try:
                linked.symlink_to(outside, target_is_directory=True)
            except OSError:
                self.skipTest('Directory symlink creation is unavailable')
        try:
            result = self.save()
            self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
            self.assertEqual(list(outside.iterdir()), [])
        finally:
            if sys.platform == 'win32':
                linked.rmdir()
            else:
                linked.unlink()


if __name__ == '__main__':
    unittest.main()

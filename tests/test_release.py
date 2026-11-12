import json
from pathlib import Path
import re
import subprocess
import sys
from tempfile import TemporaryDirectory
import unittest
from zipfile import ZipFile


ROOT = Path(__file__).resolve().parents[1]
BUILDER = ROOT / 'tools/build_release.py'
HTML = '''<!doctype html><html lang="ko"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Release check</title></head><body><h1>Release check</h1></body></html>'''


class ReleaseTests(unittest.TestCase):
    def setUp(self):
        temporary = TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.workspace = Path(temporary.name)
        self.output = self.workspace / 'dist'

    def build(self):
        self.assertTrue(BUILDER.is_file(), 'Release builder is missing')
        return subprocess.run([
            sys.executable, '-X', 'utf8', '-B', str(BUILDER), '--output', str(self.output),
        ], capture_output=True, text=True, encoding='utf-8')

    def built_paths(self):
        result = self.build()
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        metadata = json.loads(result.stdout)
        return Path(metadata['folder']), Path(metadata['archive'])

    def test_zip_is_clean_and_can_install_without_source_tree(self):
        folder, archive = self.built_paths()
        self.assertEqual({path.name for path in folder.iterdir()}, {'README.md', 'CHANGELOG.md', 'docs', 'kit'})
        manual = (folder / 'README.md').read_text(encoding='utf-8')
        self.assertNotIn('source-only', manual)
        self.assertNotIn('dist/MyCodexSetting-', manual)
        self.assertTrue((folder / 'kit/templates/config.toml').is_file())
        self.assertTrue((folder / 'kit/skills/human-html/scripts/save_html.py').is_file())
        unpacked = self.workspace / 'unpacked'
        with ZipFile(archive) as zipped:
            self.assertTrue(all(name.startswith(folder.name + '/') for name in zipped.namelist()))
            self.assertFalse(any(part in {'.git', '.codex', '.mycodex', '.context', '.superpowers', 'tests', '__pycache__'}
                                 for name in zipped.namelist() for part in Path(name).parts))
            zipped.extractall(unpacked)
        release = unpacked / folder.name
        for relative in ('README.md', 'docs/usage.md', 'kit/integrations/billion-context/README.md'):
            document = release / relative
            for link in re.findall(r'\[[^\]]+\]\(([^)]+)\)', document.read_text(encoding='utf-8')):
                if '://' in link or link.startswith('#'):
                    continue
                destination = (document.parent / link.split('#', 1)[0]).resolve()
                self.assertTrue(destination.is_relative_to(release.resolve()), (relative, link))
                self.assertTrue(destination.is_file(), (relative, link))
        target = self.workspace / 'project'
        target.mkdir()
        (target / 'PRD.md').write_text('Explain this service.\n', encoding='utf-8')
        cli = release / 'kit/mycodex.py'
        args = [sys.executable, '-X', 'utf8', '-B', str(cli), 'init', '--target', str(target), '--requirements', 'PRD.md']
        dry_run = subprocess.run(args, capture_output=True, text=True, encoding='utf-8')
        self.assertEqual(dry_run.returncode, 0, dry_run.stdout + dry_run.stderr)
        self.assertEqual([path.name for path in target.iterdir()], ['PRD.md'])
        installed = subprocess.run(args + ['--apply'], capture_output=True, text=True, encoding='utf-8')
        self.assertEqual(installed.returncode, 0, installed.stdout + installed.stderr)
        config = target / '.codex/config.toml'
        self.assertEqual(config.read_bytes(), (release / 'kit/templates/config.toml').read_bytes())
        # Fixture review only: this does not assert real application readiness.
        index = target / '.context/index.md'
        index.write_bytes(index.read_bytes().replace(b'needs-review', b'ready'))
        config.write_bytes(b'model = "user-customized"\n')
        reinstalled = subprocess.run(args + ['--apply'], capture_output=True, text=True, encoding='utf-8')
        self.assertEqual(reinstalled.returncode, 0, reinstalled.stdout + reinstalled.stderr)
        self.assertEqual(config.read_bytes(), b'model = "user-customized"\n')
        helper = target / '.agents/skills/human-html/scripts/save_html.py'
        saved = subprocess.run([
            sys.executable, '-X', 'utf8', '-B', str(helper), '--target', str(target), '--name', 'release-check',
        ], input=HTML, capture_output=True, text=True, encoding='utf-8')
        self.assertEqual(saved.returncode, 0, saved.stdout + saved.stderr)
        self.assertTrue((target / saved.stdout.strip()).is_file())
        self.assertNotIn('<html', saved.stdout)
        self.assertEqual(index.read_bytes().count(b'.human-docs/'), 0)
        checked = subprocess.run([
            sys.executable, '-X', 'utf8', '-B', str(target / '.mycodex/mycodex.py'),
            'validate', '--target', str(target), '--strict', '--json',
        ], capture_output=True, text=True, encoding='utf-8')
        self.assertEqual(checked.returncode, 0, checked.stdout + checked.stderr)

    def test_rebuild_is_identical_and_preserves_other_versions(self):
        self.output.mkdir()
        older = self.output / 'MyCodexSetting-0.1.2.zip'
        older.write_bytes(b'historical archive')
        other = self.output / 'operator-note.txt'
        other.write_bytes(b'preserve this note')
        folder, archive = self.built_paths()
        before = {path.relative_to(folder).as_posix(): path.read_bytes()
                  for path in folder.rglob('*') if path.is_file()}
        zipped = archive.read_bytes()
        modified = archive.stat().st_mtime_ns
        again = self.build()
        self.assertEqual(again.returncode, 0, again.stdout + again.stderr)
        after = {path.relative_to(folder).as_posix(): path.read_bytes()
                 for path in folder.rglob('*') if path.is_file()}
        self.assertEqual(before, after)
        self.assertEqual(zipped, archive.read_bytes())
        self.assertEqual(modified, archive.stat().st_mtime_ns)
        self.assertEqual(older.read_bytes(), b'historical archive')
        self.assertEqual(other.read_bytes(), b'preserve this note')

    def test_modified_release_folder_is_not_overwritten(self):
        folder, archive = self.built_paths()
        note = folder / 'operator-note.txt'
        note.write_bytes(b'user content')
        zipped = archive.read_bytes()
        result = self.build()
        self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
        self.assertEqual(note.read_bytes(), b'user content')
        self.assertEqual(archive.read_bytes(), zipped)

    def test_modified_archive_is_not_overwritten(self):
        folder, archive = self.built_paths()
        archive.write_bytes(b'preserve user archive')
        manual = (folder / 'README.md').read_bytes()
        result = self.build()
        self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
        self.assertEqual(archive.read_bytes(), b'preserve user archive')
        self.assertEqual((folder / 'README.md').read_bytes(), manual)

    def test_crlf_checkout_rebuild_preserves_folder_and_zip(self):
        folder, archive = self.built_paths()
        for path in folder.rglob('*'):
            if path.is_file(): path.write_bytes(path.read_bytes().replace(b'\r\n',b'\n').replace(b'\n',b'\r\n'))
        before={p.relative_to(folder).as_posix():p.read_bytes() for p in folder.rglob('*') if p.is_file()}
        zipped=archive.read_bytes()
        result=self.build();self.assertEqual(0,result.returncode,result.stderr)
        self.assertEqual(before,{p.relative_to(folder).as_posix():p.read_bytes() for p in folder.rglob('*') if p.is_file()})
        self.assertEqual(zipped,archive.read_bytes())

    def test_actual_content_change_still_conflicts(self):
        folder,archive=self.built_paths();manual=folder/'README.md'
        manual.write_bytes(manual.read_bytes()+b'changed\r\n')
        before=manual.read_bytes();result=self.build()
        self.assertEqual(1,result.returncode);self.assertEqual(before,manual.read_bytes())


if __name__ == '__main__':
    unittest.main()

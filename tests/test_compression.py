import json
import hashlib
from pathlib import Path
import subprocess
import sys
import tempfile
import shutil
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'kit'))
from mycodex_lib import compression as c
from mycodex_lib.model import InputError


class CompressionTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.base = Path(self.tmp.name)
        self.target = self.base / 'project'; self.target.mkdir()
        self.runtime = self.base / 'runtime'
        self.home = self.base / 'paseo'

    def complete_fake_runtime(self):
        self.runtime.mkdir()
        for name in c.MANAGED:shutil.copyfile(c.ASSETS/name,self.runtime/name)
        package=self.runtime/'node_modules/billion-context';(package/'dist').mkdir(parents=True)
        (package/'package.json').write_text(json.dumps(dict(version=c.BILI_VERSION)))
        for name in ('dist/index.js','dist/mcp.js'):(package/name).write_text('// synthetic engine, never executed')
        owner=dict(manager='MyCodexSetting',bili_version=c.BILI_VERSION,
                   tools=dict(node=sys.executable,codex=sys.executable),
                   files={n:hashlib.sha256((self.runtime/n).read_bytes().replace(b'\r\n',b'\n')).hexdigest() for n in c.MANAGED},
                   upstream={n:hashlib.sha256((package/n).read_bytes()).hexdigest() for n in ('package.json','dist/index.js','dist/mcp.js')})
        (self.runtime/'owner.json').write_text(json.dumps(owner))
        return owner

    def test_same_upstream_stale_bridge_conflicts_with_current_kit(self):
        self.complete_fake_runtime();self.assertIsNotNone(c._ready(self.runtime))
        assets=self.base/'new-kit-assets';shutil.copytree(c.ASSETS,assets)
        (assets/'paseo-bridge.mjs').write_text('// different integration revision, same upstream version')
        before={p.relative_to(self.runtime).as_posix():p.read_bytes() for p in self.runtime.rglob('*') if p.is_file()}
        with patch.object(c,'ASSETS',assets):
            with self.assertRaisesRegex(InputError,'RUNTIME_CONFLICT'):
                c.prepare_runtime(self.target,self.runtime,apply=True)
            with self.assertRaisesRegex(InputError,'RUNTIME_NOT_READY'):
                c.plan_paseo_provider(self.home,self.runtime,enabled=True)
        self.assertEqual(before,{p.relative_to(self.runtime).as_posix():p.read_bytes() for p in self.runtime.rglob('*') if p.is_file()})

    def test_missing_pinned_executable_is_not_ready(self):
        owner=self.complete_fake_runtime();owner['tools']['codex']=str(self.base/'removed-release/codex.exe')
        (self.runtime/'owner.json').write_text(json.dumps(owner))
        d=c.inspect_compression(self.target,self.runtime,self.home)
        self.assertFalse(d['installed']);self.assertIn('PINNED_TOOL_UNAVAILABLE',d['diagnostics'])
        with self.assertRaisesRegex(InputError,'RUNTIME_CONFLICT'):
            c.prepare_runtime(self.target,self.runtime,apply=True)

    def test_incomplete_source_does_not_prepare_or_launch_processes(self):
        assets=self.base/'incomplete-assets';shutil.copytree(c.ASSETS,assets)
        (assets/'policy.json').unlink()
        with patch.object(c,'ASSETS',assets),patch.object(c.subprocess,'run',side_effect=AssertionError('unexpected process')):
            with self.assertRaisesRegex(InputError,'INTEGRATION_INCOMPLETE'):
                c.prepare_runtime(self.target,self.runtime,apply=True)
        self.assertFalse(self.runtime.exists())

    def test_doctor_distinguishes_install_from_observed_compression(self):
        d = c.inspect_compression(self.target, self.runtime, self.home)
        self.assertEqual('supported', d['support'])
        self.assertFalse(d['installed'])
        self.assertFalse(d['provider_registered'])
        self.assertEqual('unknown', d['protocol_verified'])
        self.assertEqual('unknown', d['compression_observed'])
        self.assertEqual('unknown', d['traffic_observed'])
        self.assertFalse(self.runtime.exists())

    def test_prepare_dry_run_has_no_writes_or_network(self):
        with patch.object(c.subprocess, 'run', side_effect=AssertionError('process in dry run')):
            d = c.prepare_runtime(self.target, self.runtime)
        self.assertEqual('planned', d['state'])
        self.assertFalse(self.runtime.exists())

    def test_prepare_missing_node_preserves_project(self):
        before = list(self.target.iterdir())
        with patch.object(c, '_toolchain', side_effect=InputError('NODE_MISSING')):
            with self.assertRaises(InputError):
                c.prepare_runtime(self.target, self.runtime, apply=True)
        self.assertEqual(before, list(self.target.iterdir()))
        self.assertFalse(self.runtime.exists())

    def test_prepare_conflict_does_not_overwrite(self):
        self.runtime.mkdir(); marker = self.runtime / 'private.txt'
        marker.write_text('preserve')
        with self.assertRaises(InputError):
            c.prepare_runtime(self.target, self.runtime, apply=True)
        self.assertEqual('preserve', marker.read_text())

    def test_failed_install_is_not_ready(self):
        with patch.object(c, '_toolchain', return_value={'node':sys.executable, 'npm':'npm-cli.js', 'codex':sys.executable}), patch.object(c.subprocess, 'run', return_value=subprocess.CompletedProcess([], 1, '', 'secret-sentinel')):
            with self.assertRaisesRegex(InputError, 'INSTALL_FAILED'):
                c.prepare_runtime(self.target, self.runtime, apply=True)
        self.assertFalse(c.inspect_compression(self.target, self.runtime, self.home)['installed'])
        self.assertFalse((self.runtime / 'owner.json').exists())

    def test_runtime_cannot_be_project_or_reparse(self):
        with self.assertRaises(InputError):
            c.prepare_runtime(self.target, self.target / 'runtime')

    def test_malformed_owner_is_not_ready(self):
        self.runtime.mkdir()
        for files in (None, [], 'invalid'):
            (self.runtime/'owner.json').write_text(json.dumps(dict(manager='MyCodexSetting',bili_version=c.BILI_VERSION,files=files)))
            self.assertFalse(c.inspect_compression(self.target,self.runtime,self.home)['installed'])

    def test_base_validate_does_not_launch_node(self):
        from mycodex_lib.validation import validate
        with patch.object(c.subprocess, 'run', side_effect=AssertionError('process')):
            validate(self.target)

    def test_cli_doctor_is_read_only(self):
        r = subprocess.run([sys.executable, '-B', str(c.ASSETS.parents[1] / 'mycodex.py'),
                            'compression', 'doctor', '--target', str(self.target),
                            '--runtime', str(self.runtime), '--paseo-home', str(self.home), '--json'],
                           capture_output=True, text=True)
        self.assertEqual(0, r.returncode, r.stderr)
        self.assertFalse(json.loads(r.stdout)['installed'])
        self.assertFalse(self.runtime.exists())


if __name__ == '__main__':
    unittest.main()

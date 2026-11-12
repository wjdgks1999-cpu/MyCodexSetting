"""CLI process tests use a synthetic engine, never real inference or auth."""
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'kit'))
from mycodex_lib import compression as c
from mycodex_lib.model import InputError

ROOT = Path(__file__).resolve().parents[1]


class CodexLaunchTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory(prefix='mycodex-cli-한글 ')
        self.addCleanup(temporary.cleanup)
        self.base = Path(temporary.name)
        self.target = self.base / 'project'; self.target.mkdir()
        self.runtime = self.base / 'runtime'; self.runtime.mkdir()
        for name in c.MANAGED:
            shutil.copyfile(c.ASSETS / name, self.runtime / name)
        self.package = self.runtime / 'node_modules/billion-context'
        (self.package / 'dist').mkdir(parents=True)
        (self.package / 'package.json').write_text(json.dumps(dict(version=c.BILI_VERSION)))
        (self.package / 'dist/mcp.js').write_text('// synthetic')
        (self.package / 'dist/index.js').write_text('''
import json,os,sys
print('engine diagnostic',file=sys.stderr)
if '--exit-17' in sys.argv: sys.exit(17)
data=sys.stdin.read()
rest=sys.argv[2:]
if rest[:1]==['--']: rest=rest[1:]
print(json.dumps(dict(argv=['codex',*rest],input=data,cwd=os.getcwd(),
 update=os.environ.get('ACP_AUTO_UPDATE'),restart=os.environ.get('ACP_AUTO_RESTART_ON_UPDATE'),
 foreign=os.environ.get('BILI_MCP_PROXY'),proxy=os.environ.get('HTTPS_PROXY'),
 xdg=os.environ.get('XDG_CONFIG_HOME'),client=os.environ.get('BILI_CLIENT_BIN'))))
''', encoding='utf-8')
        owner = dict(manager='MyCodexSetting', bili_version=c.BILI_VERSION,
            tools=dict(node=sys.executable, codex=sys.executable),
            files={n:hashlib.sha256(c.read_asset(self.runtime/n)).hexdigest() for n in c.MANAGED},
            upstream={n:hashlib.sha256((self.package/n).read_bytes()).hexdigest() for n in ('package.json','dist/index.js','dist/mcp.js')})
        (self.runtime/'owner.json').write_text(json.dumps(owner))
        self.env = dict(os.environ, CODEX_HOME=str(self.base/'empty-home'), PYTHONUTF8='1',
            ACP_AUTO_UPDATE='1', ACP_AUTO_RESTART_ON_UPDATE='1',
            BILI_MCP_PROXY='http://foreign.invalid', HTTPS_PROXY='http://upstream.invalid',
            XDG_CONFIG_HOME='preserved-xdg')
        self.env.pop('CODEX_CA_CERTIFICATE', None)

    def invoke(self, arguments=(), apply=False, data=''):
        cmd=[sys.executable,'-X','utf8','-B',str(ROOT/'kit/mycodex.py'),'compression','codex',
             '--target',str(self.target),'--runtime',str(self.runtime)]
        if apply: cmd.append('--apply')
        return subprocess.run(cmd+['--',*arguments], input=data, capture_output=True,
                              text=True, encoding='utf-8', env=self.env, timeout=15)

    def test_dry_run_never_launches_or_echoes_prompt(self):
        before={p.relative_to(self.base).as_posix():p.read_bytes() for p in self.base.rglob('*') if p.is_file()}
        with patch.dict(os.environ,self.env,clear=True), patch.object(c.subprocess,'Popen',side_effect=AssertionError('process')):
            result=c.run_codex(self.target,self.runtime,['private-sentinel'])
        self.assertEqual('planned',result['state'])
        self.assertNotIn('private-sentinel',json.dumps(result))
        self.assertEqual(before,{p.relative_to(self.base).as_posix():p.read_bytes() for p in self.base.rglob('*') if p.is_file()})

    def test_cli_dry_run_and_native_argv_streams_cwd_environment(self):
        dry=self.invoke(['secret-sentinel'])
        self.assertEqual(0,dry.returncode,dry.stderr)
        self.assertNotIn('secret-sentinel',dry.stdout+dry.stderr)
        self.assertEqual('planned',json.loads(dry.stdout)['state'])
        args=['exec','한글 공백','','a"b','&','%PATH%','-c','test=["x y",""]','--json']
        actual=self.invoke(args,apply=True,data='stdin 표식\n')
        self.assertEqual(0,actual.returncode,actual.stderr)
        d=json.loads(actual.stdout)
        self.assertEqual(['codex','--no-daemon',*args],d['argv'])
        self.assertEqual('stdin 표식\n',d['input'])
        self.assertEqual(str(self.target),d['cwd'])
        self.assertEqual('0',d['update']);self.assertEqual('0',d['restart'])
        self.assertIsNone(d['foreign'])
        self.assertEqual(self.env['HTTPS_PROXY'],d['proxy'])
        self.assertEqual('preserved-xdg',d['xdg'])
        self.assertEqual(sys.executable,d['client'])
        self.assertEqual('engine diagnostic\n',actual.stderr)
        self.assertEqual('1',self.env['ACP_AUTO_UPDATE'])

    def test_child_nonzero_exit_is_preserved(self):
        result=self.invoke(['--exit-17'],apply=True)
        self.assertEqual(17,result.returncode,result.stderr)
        self.assertEqual('',result.stdout)

    def test_native_separator_survives_bili_parser(self):
        args=['--','--remote=literal-prompt-not-a-connection']
        result=self.invoke(args,apply=True)
        self.assertEqual(0,result.returncode,result.stderr)
        self.assertEqual(['codex','--no-daemon',*args],json.loads(result.stdout)['argv'])

    def test_literal_remote_prompt_keeps_local_run_mode(self):
        args=['exec','--','--remote=literal-prompt-not-a-connection']
        result=self.invoke(args,apply=True)
        self.assertEqual(0,result.returncode,result.stderr)
        self.assertEqual(['codex','--no-daemon',*args],json.loads(result.stdout)['argv'])

    def test_remote_route_is_rejected_before_process_or_auth_probe(self):
        for args in (['--remote','ws://localhost:1'],['--remote=ws://localhost:1']):
            with self.subTest(args=args), patch.object(c.subprocess,'Popen',side_effect=AssertionError('process')):
                with self.assertRaisesRegex(InputError,'REMOTE_UNSUPPORTED'):
                    c.run_codex(self.target,self.runtime,args,apply=True)

    def test_custom_ca_is_preserved_and_rejected(self):
        with patch.dict(os.environ,CODEX_CA_CERTIFICATE='private-ca-path'), patch.object(c.subprocess,'Popen',side_effect=AssertionError('process')):
            with self.assertRaisesRegex(InputError,'CUSTOM_CODEX_CA_UNVERIFIED'):
                c.run_codex(self.target,self.runtime,[],apply=True)
            self.assertEqual('private-ca-path',os.environ['CODEX_CA_CERTIFICATE'])

    def test_auth_link_failure_does_not_copy_or_launch(self):
        home=self.base/'auth-home';home.mkdir();auth=home/'auth.json'
        auth.write_bytes(b'fake-auth-not-a-credential')
        with patch.dict(os.environ,self.env,clear=True), patch.dict(os.environ,CODEX_HOME=str(home)), patch.object(c.os,'link',side_effect=OSError('denied')), patch.object(c.subprocess,'Popen',side_effect=AssertionError('process')):
            with self.assertRaisesRegex(InputError,'AUTH_LINK_UNAVAILABLE'):
                c.run_codex(self.target,self.runtime,[],apply=True)
        self.assertEqual(['auth.json'],[p.name for p in home.iterdir()])
        self.assertEqual(b'fake-auth-not-a-credential',auth.read_bytes())

    def test_stale_runtime_is_rejected_before_launch(self):
        (self.package/'dist/index.js').write_text('tampered')
        with patch.object(c.subprocess,'Popen',side_effect=AssertionError('process')):
            with self.assertRaisesRegex(InputError,'RUNTIME_NOT_READY'):
                c.run_codex(self.target,self.runtime,[],apply=True)

    def test_relative_codex_home_is_resolved_once_for_probe_and_child(self):
        home=self.target/'relative-home';home.mkdir();(home/'auth.json').write_bytes(b'fake-auth')
        with patch.dict(os.environ,self.env,clear=True), patch.dict(os.environ,CODEX_HOME='relative-home'), patch.object(c.os,'link',wraps=os.link) as link, patch.object(c.subprocess,'Popen') as launch:
            launch.return_value.__enter__.return_value.wait.return_value=0
            self.assertEqual(0,c.run_codex(self.target,self.runtime,[],apply=True))
            self.assertEqual(1,link.call_count)
            self.assertEqual(home.resolve()/'auth.json',link.call_args.args[0])
            self.assertEqual(str(home.resolve()),launch.call_args.kwargs['env']['CODEX_HOME'])
        self.assertEqual(['auth.json'],[p.name for p in home.iterdir()])

    def test_auth_link_probe_uses_overlay_parent_filesystem(self):
        home=self.base/'auth-home';home.mkdir();(home/'auth.json').write_bytes(b'fake-auth')
        with patch.dict(os.environ,self.env,clear=True), patch.dict(os.environ,CODEX_HOME=str(home)), patch.object(c.os,'link',wraps=os.link) as link, patch.object(c.subprocess,'Popen') as launch:
            launch.return_value.__enter__.return_value.wait.return_value=0
            self.assertEqual(0,c.run_codex(self.target,self.runtime,[],apply=True))
            self.assertEqual(home.resolve().parent,link.call_args.args[1].parent)
            self.assertFalse(link.call_args.args[1].exists())

    def test_cli_doctor_ignores_malformed_paseo_config(self):
        home=self.base/'paseo';home.mkdir();(home/'config.json').write_text('malformed')
        result=subprocess.run([sys.executable,'-B',str(ROOT/'kit/mycodex.py'),
            'compression','doctor','--client','codex','--target',str(self.target),
            '--runtime',str(self.runtime),'--paseo-home',str(home),'--json'],
            capture_output=True,text=True,encoding='utf-8',env=self.env,timeout=15)
        self.assertEqual(0,result.returncode,result.stderr)
        d=json.loads(result.stdout)
        self.assertEqual('codex',d['client']);self.assertTrue(d['installed'])
        self.assertIsNone(d['provider_registered'])
        self.assertEqual('unknown',d['compression_observed'])
        self.assertEqual('malformed',(home/'config.json').read_text())


if __name__ == '__main__':
    unittest.main()

import copy
import json
from pathlib import Path
import sys
import unittest
from unittest.mock import patch
import test_compression as base
from mycodex_lib import compression as c
from mycodex_lib.model import InputError


class PaseoTests(unittest.TestCase):
    def setUp(self):
        base.CompressionTests.setUp(self)
        self.home.mkdir()
        self.config = self.home / 'config.json'
        self.original = dict(version=1, unknown={'token':'PRIVATE_SENTINEL_405'}, agents={'providers':{'codex':{'enabled':True}},'other':42})
        self.config.write_text(json.dumps(self.original))
        self.owner = dict(manager='MyCodexSetting', bili_version=c.BILI_VERSION, tools={'node':sys.executable,'codex':sys.executable},files={},upstream={})
        self.runtime.mkdir()
        with patch.object(c,'_ready',return_value=self.owner):
            self.plan = c.plan_paseo_provider(self.home,self.runtime,enabled=True)

    def apply(self,plan=None):
        with patch.object(c,'_ready',return_value=self.owner),patch.object(c,'_reload_paseo',return_value=False):
            return c.apply_paseo_provider(plan or self.plan)

    def test_enable_preserves_unrelated_settings(self):
        result=self.apply();d=json.loads(self.config.read_text())
        profile=d['agents']['providers'].pop('codex-bili')
        self.assertEqual(self.original,d)
        self.assertEqual('codex',profile['extends'])
        self.assertEqual([sys.executable,str(self.runtime/'paseo-bridge.mjs')],profile['command'])
        self.assertNotIn('PRIVATE_SENTINEL_405',json.dumps(result))
        for f in self.runtime.rglob('*'):
            if f.is_file():self.assertNotIn('PRIVATE_SENTINEL_405',f.read_text())

    def test_existing_unowned_provider_conflicts(self):
        d=copy.deepcopy(self.original);d['agents']['providers']['codex-bili']={'label':'mine'}
        self.config.write_text(json.dumps(d));before=self.config.read_bytes()
        with self.assertRaises(InputError):c.plan_paseo_provider(self.home,self.runtime,enabled=True)
        self.assertEqual(before,self.config.read_bytes())

    def test_null_provider_is_still_an_unowned_collision(self):
        d=copy.deepcopy(self.original);d['agents']['providers']['codex-bili']=None
        self.config.write_text(json.dumps(d))
        with self.assertRaisesRegex(InputError,'PROVIDER_CONFLICT'):c.plan_paseo_provider(self.home,self.runtime,enabled=True)

    def test_concurrent_edit_preserved(self):
        self.config.write_text(json.dumps(dict(self.original, external='edit')))
        before=self.config.read_bytes()
        with self.assertRaises(InputError):self.apply()
        self.assertEqual(before,self.config.read_bytes())

    def test_disable_removes_only_owned_unchanged_entry(self):
        self.apply()
        plan=c.plan_paseo_provider(self.home,self.runtime,enabled=False)
        self.apply(plan);self.assertEqual(self.original,json.loads(self.config.read_text()))

    def test_modified_owned_provider_is_preserved(self):
        self.apply();d=json.loads(self.config.read_text());d['agents']['providers']['codex-bili']['label']='changed'
        self.config.write_text(json.dumps(d));before=self.config.read_bytes()
        with self.assertRaises(InputError):c.plan_paseo_provider(self.home,self.runtime,enabled=False)
        self.assertEqual(before,self.config.read_bytes())

    def test_reload_failure_is_saved_not_active(self):
        d=self.apply();self.assertEqual('saved_not_active',d['state']);self.assertFalse(d['active'])

    def test_disable_points_to_existing_codex(self):
        self.apply()
        plan=c.plan_paseo_provider(self.home,self.runtime,enabled=False)
        with patch.object(c,'_reload_paseo',return_value=True):
            d=c.apply_paseo_provider(plan)
        self.assertIn('existing Codex',d['next_action'])

    def test_export_does_not_overwrite_or_update_index(self):
        index=self.target/'index.md';index.write_text('preserved')
        sessions=self.runtime/'sessions/responses';sessions.mkdir(parents=True)
        session='01a1ce12-f10d-7d00-a0be-c9a7f58035ef'
        source=dict(version=3,id=session,payload={'state':{'blocks':[dict(blockId='b1',active=True,summary='synthetic summary')]},'messages':[{'text':'RAW_SENTINEL'}]})
        (sessions/'example.json').write_text(json.dumps(source))
        d=c.export_compression_summary(self.runtime,session);self.assertEqual('planned',d['state']);self.assertFalse((self.runtime/'exports').exists())
        a=c.export_compression_summary(self.runtime,session,apply=True)
        b=c.export_compression_summary(self.runtime,session,apply=True)
        self.assertNotEqual(a['path'],b['path']);self.assertEqual('preserved',index.read_text())
        text=Path(a['path']).read_text();self.assertIn('synthetic summary',text);self.assertNotIn('RAW_SENTINEL',text)

    def test_export_rejects_path_traversal(self):
        for s in ('../private','../../secret','x/y',''):
            with self.assertRaises(InputError):c.export_compression_summary(self.runtime,s,apply=True)


if __name__=='__main__':unittest.main()

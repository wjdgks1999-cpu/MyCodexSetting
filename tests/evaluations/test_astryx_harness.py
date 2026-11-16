import importlib.util
from pathlib import Path
import tempfile
import unittest

MODULE = Path(__file__).resolve().parents[2] / 'tools/evaluations/astryx/common.py'


class EvidenceTests(unittest.TestCase):
    def setUp(self):
        spec = importlib.util.spec_from_file_location('astryx_common', MODULE)
        self.module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(self.module)

    def test_evidence_cannot_overwrite_an_earlier_result(self):
        with tempfile.TemporaryDirectory() as d:
            path = Path(d) / 'result.json'
            self.module.save_new(path, {'status': 'FAIL'})
            before = path.read_bytes()
            with self.assertRaises(FileExistsError):
                self.module.save_new(path, {'status': 'PASS'})
            self.assertEqual(before, path.read_bytes())

    def test_snapshot_includes_hidden_user_assets_but_skips_dependency_tree(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            for file in ('.codex/config.toml', 'AGENTS.md', 'node_modules/x/index.js'):
                p = root / file
                p.parent.mkdir(parents=True, exist_ok=True)
                p.write_text('fixture', encoding='utf-8')
            self.assertEqual(set(self.module.snapshot(root)), {'.codex/config.toml', 'AGENTS.md'})

    def test_result_requires_a_completed_process(self):
        self.assertEqual(self.module.process_status(None), 'INCONCLUSIVE')
        self.assertEqual(self.module.process_status(1), 'FAIL')
        self.assertEqual(self.module.process_status(0), 'PROCESS_OK')

    def test_intro_repeating_the_source_is_not_content_loss(self):
        text = '설명: 원문 문장. 항목 001: 원문 문장. 항목 002: 원문 문장.'
        self.assertTrue(self.module.preserves_labeled_items(text, 2, '원문 문장.'))

    def test_intro_cannot_replace_a_missing_item_body(self):
        text = '설명: 원문 문장. 항목 001: 원문 문장. 항목 002: 누락됨.'
        self.assertFalse(self.module.preserves_labeled_items(text, 2, '원문 문장.'))


if __name__ == '__main__':
    unittest.main()

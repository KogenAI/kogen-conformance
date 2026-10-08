"""Controls and mutations for the publication review's assertion boundaries."""
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from types import SimpleNamespace

from kogen_conformance import runner


ROOT = Path(__file__).resolve().parents[1]
REF_CASES = (
    'v1.3-01-observational-auditor',
    'ladder-06-advisory-with-land-green',
    'ladder-10-all-change-items-demoted',
    'v1.2-74-ladder-06',
    'v1.2-78-ladder-10',
)


class PublicationFixTests(unittest.TestCase):
    def test_non_landing_ref_captures_pre_build_base(self):
        with tempfile.TemporaryDirectory() as tmp:
            def git(*args):
                return subprocess.check_output(['git', '-C', tmp] + list(args), text=True).strip()
            git('init', '-q', '-b', 'main')
            git('config', 'user.name', 'Mutation Test')
            git('config', 'user.email', 'mutation@kogen.invalid')
            Path(tmp, 'file').write_text('base\n')
            git('add', 'file')
            git('-c', 'commit.gpgsign=false', 'commit', '-q', '-m', 'Base')
            base = git('rev-parse', 'refs/heads/main')
            for case_id in REF_CASES:
                path = next((ROOT / 'cases').rglob(case_id + '*.json'))
                case = json.loads(path.read_text())
                steps = case['steps']
                start = next(i for i, s in enumerate(steps) if s.get('run') == ['kogen', 'queue', 'start'])
                capture = steps[start - 1]
                self.assertEqual('git', capture['capture']['from'], case_id)
                self.assertEqual('origin', capture['capture']['in'], case_id)
                ref = next(s['assert']['refs']['refs/heads/main'] for s in steps
                           if s.get('assert', {}).get('refs', {}).get('refs/heads/main'))
                self.assertEqual('{var:base_before_build}', ref, case_id)
                variables = {}
                def expand(value):
                    if isinstance(value, str):
                        return value.replace('{var:base_before_build}', variables['base_before_build']) if '{var:base_before_build}' in value else value
                    if isinstance(value, dict):
                        return {k: expand(v) for k, v in value.items()}
                    if isinstance(value, list):
                        return [expand(v) for v in value]
                    return value
                w = SimpleNamespace(vars=variables, origin=tmp, checkout=tmp,
                                    git=lambda args, cwd=None: git(*args), expand=expand,
                                    ref_value=lambda ref, where='origin': git('rev-parse', ref))
                run = runner.CaseRun.__new__(runner.CaseRun)
                run.w = w
                run.s_capture(capture)
                self.assertEqual(base, variables['base_before_build'])
                self.assertEqual([], run.assertions({'refs': {'refs/heads/main': ref}}))
                Path(tmp, 'file').write_text('unauthorized landing\n')
                git('add', 'file')
                git('-c', 'commit.gpgsign=false', 'commit', '-q', '-m', 'Unauthorized landing')
                self.assertTrue(run.assertions({'refs': {'refs/heads/main': ref}}), case_id)
                git('reset', '-q', '--hard', base)

    def test_pending_workspace_preserves_bytes_deletions_modes_and_links(self):
        case = runner.load_cases(ids=['v1.3-24-recovery-ref-failure'])[0]
        oracle = next(s['assert']['v13'] for s in case['steps'] if 'v13' in s.get('assert', {}))
        expected = oracle['files']
        with tempfile.TemporaryDirectory() as tmp:
            state = Path(tmp)
            work = state / ('run123-' + 'workspace')
            work.mkdir()
            def populate():
                for item in list(work.rglob('*'))[::-1]:
                    if item.is_file() or item.is_symlink():
                        item.unlink()
                for rel, wanted in expected.items():
                    if wanted is None:
                        continue
                    path = work / rel
                    path.parent.mkdir(parents=True, exist_ok=True)
                    if wanted.get('mode') == '120000':
                        path.symlink_to(wanted['text'])
                    else:
                        path.write_bytes(wanted['text'].encode())
                        path.chmod(0o755 if wanted.get('mode') == '100755' else 0o644)
            populate()
            event = {'event': 'cleanup_failure', 'workspace': str(work)}
            run = runner.CaseRun.__new__(runner.CaseRun)
            run.w = SimpleNamespace(state_root=tmp, latest_run=lambda slug: ('run123', tmp, {'run_id': 'run123', 'cleanup_pending': True, 'recovery': []}), events=lambda _: [event], fake=None)
            self.assertEqual([], run._v13_assert(oracle))
            mutations = (
                lambda: (work / 'lib/greet.txt').write_bytes(b'CORRUPT'),
                lambda: (work / 'lib/deleted.txt').write_text('restored\n'),
                lambda: (work / 'lib/exec.sh').chmod(0o644),
                lambda: ((work / 'lib/link').unlink(), (work / 'lib/link').write_text('greet.txt')),
                lambda: ((work / 'lib/link').unlink(), (work / 'lib/link').symlink_to('wrong.txt')),
            )
            for mutate in mutations:
                populate()
                mutate()
                self.assertTrue(run._v13_assert(oracle))
            populate()
            event['workspace'] = str(state / 'wrong-workspace')
            self.assertTrue(run._v13_assert(oracle))

    def test_invalid_utf8_rejected_on_both_output_streams(self):
        case = runner.load_cases(ids=['cli-22'])[0]
        instance = runner.instances(case)[0][1]
        expect = instance['steps'][0]['expect']
        run = runner.CaseRun.__new__(runner.CaseRun)
        run.case = instance
        run.w = SimpleNamespace(expand=lambda value: value)
        control = {'exit': 2, 'stdout': b'kogen\n', 'stderr': b''}
        self.assertEqual([], run.check_expect(control, expect))
        self.assertTrue(any('UTF-8' in m for m in run.check_expect(dict(control, stdout=b'kogen\xff\n'), expect)))
        permitted = dict(expect)
        permitted.pop('stderr')
        permitted['stderr_any'] = True
        self.assertEqual([], run.check_expect(dict(control, stderr=b'warning: good\n'), permitted))
        self.assertTrue(any('UTF-8' in m for m in run.check_expect(dict(control, stderr=b'warning: bad\xff\n'), permitted)))
        fake = ROOT / 'tests/fakes/malformed_output.py'
        with tempfile.TemporaryDirectory() as tmp:
            wrapper = Path(tmp) / 'kogen'
            wrapper.write_text('#!/bin/sh\nexec ' + sys.executable + ' ' + str(fake) + '\n')
            wrapper.chmod(0o755)
            result = subprocess.run([str(ROOT / 'bin/kogen-conformance'), 'run', '--kogen', str(wrapper),
                                     '--profile', 'cli', '--case', 'cli-22', '--workdir', tmp,
                                     '--out', str(Path(tmp) / 'results.jsonl')], capture_output=True, text=True)
            self.assertNotEqual(0, result.returncode)
            rows = [json.loads(line) for line in Path(tmp, 'results.jsonl').read_text().splitlines()]
            row = next(row for row in rows if row.get('id') == 'cli-22')
            self.assertEqual(10, row['instances']['total'])
            self.assertEqual(0, row['instances']['passed'])
            self.assertEqual('fail', row['status'])
            self.assertTrue(any('UTF-8' in message for failure in row['failures'] for message in failure['messages']))

    def test_spec_pin_is_shared_by_current_metadata(self):
        profile = json.loads((ROOT / 'profiles/v1.3.json').read_text())
        expectations = json.loads((ROOT / 'expectations/v1.3.json').read_text())
        self.assertEqual(profile['spec_revision'], expectations['spec_revision'])
        self.assertRegex(profile['spec_revision'], r'^[0-9a-f]{40}$')
        self.assertNotIn('96cefde', (ROOT / 'profiles/v1.3.json').read_text())
        self.assertNotIn('96cefde', (ROOT / 'expectations/v1.3.json').read_text())
        for name in ('README.md', 'data/v1.3/RECEIPTS.md', 'quint/v1.3/README.md', 'REPORT-v1.3.md'):
            self.assertIn(profile['spec_revision'], (ROOT / name).read_text(), name)

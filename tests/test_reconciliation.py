"""Sensitivity of every inherited v1.3 schema projection and decoder boundary."""
import base64
import copy
import contextlib
import json
import socket
import subprocess
import tempfile
import unittest
import urllib.request
from pathlib import Path
from types import SimpleNamespace
from kogen_conformance import fake_server, matchers, runner, v13


def request(exp):
    names = exp['callable_tools']
    body = dict(model=exp.get('model'), reasoning={'effort': exp.get('effort')},
                tools=[{'name': n} for n in v13.CANONICAL_TOOLS],
                tool_choice={'type': 'allowed_tools', 'mode': 'auto',
                             'tools': [{'type': 'function', 'name': n} for n in names]} if names else 'none',
                instructions='\n'.join(fake_server._as_list(exp.get('instructions_contains'))))
    texts = fake_server._as_list(exp.get('input_contains'))
    # Restrict this probe to the schema/permissions boundary; other scenario
    # assertions continue to run against the real CLI in the conformance gate.
    exp = {k: exp[k] for k in ('tools', 'callable_tools')}
    return exp, dict(body=body, tools=fake_server.tool_names(body), _texts=texts)


def stdout_expectations(value):
    if isinstance(value, dict):
        if 'stdout_lines' in value:
            yield value
        for child in value.values():
            yield from stdout_expectations(child)
    elif isinstance(value, list):
        for child in value:
            yield from stdout_expectations(child)


class ReconciliationTests(unittest.TestCase):
    def test_every_landing_line_rejects_a_literal_regex_marker_fake(self):
        checked = set()
        for case in runner.load_cases():
            for _, c in runner.instances(case):
                for expect in stdout_expectations(c['steps']):
                    for line in expect['stdout_lines']:
                        self.assertFalse(line.startswith('~\\~landed '), 'uncorrected literal marker in '+c['id'])
                        if not line.startswith('~landed '):
                            continue
                        with self.subTest(case=c['id']):
                            slug = line.split(' ',2)[1]
                            good = 'landed %s 01234567 (Build 89abcdef)\n' % slug
                            r = runner.CaseRun.__new__(runner.CaseRun)
                            r.case = c
                            r.w = SimpleNamespace(expand=lambda v:v)
                            want = {'exit':0, 'stdout_lines':[line.replace('{id8:'+slug+'}', '89abcdef')]}
                            self.assertEqual([],r.check_expect(dict(exit=0,stdout=good.encode(),stderr=b''),want))
                            self.assertTrue(r.check_expect(dict(exit=0,stdout=('~'+good).encode(),stderr=b''),want))
                        checked.add(c['id'])
        self.assertGreater(len(checked),50)
        (Path(runner.ctx.ROOT)/'reference/results/v1.3/reconciliation-landing-mutations.json').write_text(json.dumps([dict(id=id,control='pass',mutant='literal-tilde',result='killed') for id in sorted(checked)],indent=2)+'\n')

    def test_every_projected_case_rejects_wrong_schema_and_permission_fakes(self):
        checked = []
        for _, c in [instance for case in runner.load_cases() for instance in runner.instances(case)]:
            r = runner.CaseRun.__new__(runner.CaseRun)
            r.case = c
            r.w = SimpleNamespace(expand=lambda v: v)
            for step in r.load_script(c.get('script', [])):
                if 'callable_tools' not in step.get('expect', {}):
                    continue
                with self.subTest(case=c['id'], step=step.get('id')):
                    exp, good = request(step['expect'])
                    st = fake_server.FakeState()
                    self.assertTrue(st.match({'expect': exp}, good))
                    if step['expect']['callable_tools']:
                        required = copy.deepcopy(good)
                        required['body']['tool_choice']['mode'] = 'required'
                        self.assertTrue(st.match({'expect': exp}, required), 'valid required-mode permissions were rejected')
                    bad = copy.deepcopy(good)
                    bad['body']['tools'].pop()
                    bad['tools'] = fake_server.tool_names(bad['body'])
                    self.assertFalse(st.match({'expect': exp}, bad), 'missing canonical schema survived')
                    bad = copy.deepcopy(good)
                    bad['body']['tool_choice'] = 'auto'
                    self.assertFalse(st.match({'expect': exp}, bad), 'unrestricted permissions survived')
                    bad = copy.deepcopy(good)
                    if step['expect']['callable_tools']:
                        bad['body']['tool_choice']['tools'].append({})
                    else:
                        bad['body']['tool_choice'] = {'type':'allowed_tools','mode':'auto','tools':[]}
                    self.assertFalse(st.match({'expect': exp}, bad), 'malformed permissions survived')
                    bad = copy.deepcopy(good)
                    names = step['expect']['callable_tools']
                    other = next((n for n in v13.CANONICAL_TOOLS if n not in names), None)
                    if other:
                        bad['body']['tool_choice'] = {'type': 'allowed_tools', 'mode': 'auto', 'tools': [{'type': 'function', 'name': n} for n in names + [other]]}
                    else:
                        bad['body']['tool_choice'] = 'none'
                    self.assertFalse(st.match({'expect': exp}, bad), 'wrong permission inventory survived')
                checked.append(c['id'])
        self.assertGreater(len(set(checked)), 50)
        inventory = [dict(id=case_id, control='pass', mutants={'missing-schema':'killed','unrestricted-tools':'killed','wrong-permissions':'killed','malformed-permissions':'killed'}) for case_id in sorted(set(checked))]
        output = Path(runner.ctx.ROOT)/'reference/results/v1.3/reconciliation-mutations.json'
        output.write_text(json.dumps(inventory, indent=2)+'\n')

    def test_toolless_explicit_assertion_keeps_complete_schemas_and_none(self):
        c = next(c for c in runner.load_cases() if c['id'] == 'v1.2-106-provider-03')
        c = runner.instances(c)[0][1]
        for req in c['steps'][-1]['assert']['fake_requests']:
            want = req['match']['body']
            good = dict(tools=[{'name': n, 'strict': n == 'finish'} for n in v13.CANONICAL_TOOLS], input=[], tool_choice='none')
            self.assertEqual([], matchers.match(want, good))
            for bad in (dict(good, tools=good['tools'][:3]), dict(good, tool_choice='auto')):
                self.assertTrue(matchers.match(want, bad))

    def test_every_fresh_case_rejects_nonfresh_history_fake(self):
        checked = set()
        for case in runner.load_cases():
            for _, c in runner.instances(case):
                r = runner.CaseRun.__new__(runner.CaseRun)
                r.case = c
                r.w = SimpleNamespace(expand=lambda v:v)
                for step in r.load_script(c.get('script', [])):
                    exp = step.get('expect', {})
                    if exp.get('turn') != 1 and not exp.get('fresh'):
                        continue
                    with self.subTest(case=c['id'], step=step.get('id')):
                        st = fake_server.FakeState()
                        prefix = [dict(type='additional_tools',role='developer',tools=[]), dict(role='developer',content='generic'), dict(role='developer',content='stage')]
                        user = dict(role='user', content='task')
                        good = dict(body={}, _texts=[], turn=1, fresh=True)
                        turn, fresh = st.compute_turn('builder', prefix+[user])
                        good.update(turn=turn, fresh=fresh)
                        want = {key:exp[key] for key in ('turn','fresh') if key in exp}
                        self.assertTrue(st.match({'expect':want}, good))
                        # A fake with prior assistant history cannot satisfy
                        # this case's first-turn/fresh boundary.
                        turn, fresh = st.compute_turn('builder', prefix+[user,dict(role='assistant',content='old'),user])
                        self.assertFalse(st.match({'expect':want}, dict(good, turn=turn, fresh=fresh)))
                    checked.add(c['id'])
        inventory = [dict(id=case_id, control='pass', mutant='prior-history-as-fresh', result='killed') for case_id in sorted(checked)]
        (Path(runner.ctx.ROOT)/'reference/results/v1.3/reconciliation-turn-mutations.json').write_text(json.dumps(inventory,indent=2)+'\n')

    def test_fresh_prefix_and_append_only_turns(self):
        st = fake_server.FakeState()
        user = {'role': 'user', 'content': 'task'}
        prefix = [{'role': 'developer', 'content': 'generic'}, {'role': 'developer', 'content': 'stage'}]
        first = prefix + [user]
        self.assertEqual((1, True), st.compute_turn('builder', first))
        st.requests.append(dict(role='builder', _items=first, turn=1))
        later = first + [{'role': 'assistant', 'content': 'progress'}, user]
        self.assertEqual((2, False), st.compute_turn('builder', later))
        rewritten = copy.deepcopy(later)
        rewritten[0]['content'] = 'corrupt'
        self.assertEqual((None, False), st.compute_turn('builder', rewritten))
        # Already-received assistant/tool history must never look fresh.
        self.assertEqual((None, False), st.compute_turn('planner', later))

    def test_owned_schema_projection_preserves_role_permissions(self):
        c = runner.instances(runner.load_cases(ids=['v1.2-105-provider-02'])[0])[0][1]
        for req in c['steps'][-1]['assert']['fake_requests']:
            want = req['match']['body']
            allowed = ['shell', 'finish', 'tool_output'] if req['select']['step'].endswith('edit') else []
            good = dict(input=[dict(type='additional_tools', role='developer', tools=[dict(name=n, strict=n=='finish') for n in v13.CANONICAL_TOOLS]), dict(role='user')],
                        tool_choice=dict(type='allowed_tools', mode='auto', tools=[dict(type='function', name=n) for n in allowed]) if allowed else 'none', parallel_tool_calls=False)
            self.assertEqual([], matchers.match(want, good))
            bad = copy.deepcopy(good)
            bad['input'][0]['tools'].pop(0)
            self.assertTrue(matchers.match(want, bad))
            bad = copy.deepcopy(good)
            bad['tool_choice'] = 'auto'
            self.assertTrue(matchers.match(want, bad))

    def test_string_events_still_reject_missing_repair(self):
        r = runner.CaseRun.__new__(runner.CaseRun)
        events = [{'event': 'repair'}, {'event': 'finished'}]
        r.w = SimpleNamespace(runs=lambda _: [(0, 'run', {})], events=lambda _: events)
        self.assertEqual([], r._events_assert({'contains': ['repair']}))
        events.pop(0)
        self.assertTrue(r._events_assert({'contains': ['repair']}))

    def test_byte_preservation_cases_reject_normalizing_fakes(self):
        for c in runner.load_cases(ids=['shape-03', 'shape-04']):
            c = runner.instances(c)[0][1]
            request_bytes = base64.b64decode(c['steps'][0]['stdin_b64'])
            authored = c['script'][0]['reply']['calls'][0]['arguments']['content'].encode()
            good = authored.rstrip(b'\n') + b'\n\n## Request\n' + request_bytes
            path, oracle = next(iter(c['steps'][1]['assert']['files'].items()))
            with self.subTest(case=c['id']), tempfile.TemporaryDirectory() as root:
                file = Path(root)/'intent.md'
                r = runner.CaseRun.__new__(runner.CaseRun)
                r.w = SimpleNamespace(path=lambda _: str(file))
                file.write_bytes(good)
                self.assertEqual([], r._file_assert(path, oracle))
                bad = good.replace(b'\r\n', b'\n') if c['id'] == 'shape-03' else good.decode('utf-8', errors='replace').encode()
                self.assertNotEqual(good, bad)
                file.write_bytes(bad)
                self.assertTrue(r._file_assert(path, oracle))

    def test_prompt_projections_reject_missing_marker_and_changed_task(self):
        c = next(c for c in runner.load_cases(ids=['shape-06']) if c['id']=='shape-06')
        c = runner.instances(c)[0][1]
        oracle = c['steps'][-1]['assert']['fake_requests']
        user = ('Slug: greet\n\nConfigured project domains: app, docs. Use only these names in the Intent and Verify lines.\n\n'
                'Effective gate paths: `.kogen/project.yaml`, `checks/lint.sh`, `checks/unit.sh`, `checks/fmt.sh`, `run-acceptance.sh`. '
                'Set `changes_gate: true` only when the task or planned changes require modifying one of these paths. Omit it for unrelated changes; running or inspecting checks alone does not count.\n\n'
                'Task statement:\nMake the greeting in lib/greet.txt say Hello, World! instead of Hello!\n\n'
                'Write the Intent to `.kogen/intents/greet/intent.md` and its acceptance test to `.kogen/acceptance/greet.t.sh`.')
        good = dict(role='shaper', turn=1, step='write', body=dict(model='gpt-6.1-sol', reasoning={'effort':'high'}, instructions='generic', input=[{'role':'developer','content':'You are Kogen Intent shaper.'},{'role':'user','content':user}]))
        r = runner.CaseRun.__new__(runner.CaseRun)
        requests = [good]
        r.w = SimpleNamespace(fake=SimpleNamespace(state=SimpleNamespace(public_requests=lambda:requests)))
        self.assertEqual([], r._fake_assert(oracle))
        for index in (0,1):
            bad = copy.deepcopy(good)
            bad['body']['input'][index]['content']='corrupt'
            requests[:] = [bad]
            self.assertTrue(r._fake_assert(oracle))

    def test_conflicting_base_cases_reject_skipped_repair(self):
        for c in runner.load_cases(ids=['v1.2-59-build-25', 'v1.2-60-build-26']):
            c = runner.instances(c)[0][1]
            oracle = next(s['assert']['events'] for s in c['steps'] if 'events' in s.get('assert',{}))
            events = [{'event':'repair','reason':'rebase_conflict'},oracle['last']]
            r = runner.CaseRun.__new__(runner.CaseRun)
            r.w = SimpleNamespace(runs=lambda _: [(0,'run',{})], events=lambda _:events)
            self.assertEqual([], r._events_assert(oracle))
            events.pop(0)
            self.assertTrue(r._events_assert(oracle))
            mover = next(s['side_effect_sh'] for s in c['script'] if 'side_effect_sh' in s)
            self.assertIn('Hello, Universe!',mover)

    def test_baseline_and_custody_observations_remain_strict(self):
        for case_id, observation, mutant in [('state-28','1\n','2\n'),('build-39','stopped','landed'),('v1.2-119-custody-06','Hello!\n','Hello!\nescaped\n')]:
            c = runner.instances(runner.load_cases(ids=[case_id])[0])[0][1]
            if case_id=='state-28':
                want = next(s['expect']['stdout'] for s in c['steps'] if 'sh' in s)
            elif case_id=='build-39':
                want = c['steps'][-1]['assert']['run_json']['match']['status']
            else:
                want = c['steps'][-1]['assert']['files']['lib/greet.txt']['text']
            self.assertEqual([],matchers.match(want,observation))
            self.assertTrue(matchers.match(want,mutant))
        c = runner.instances(runner.load_cases(ids=['build-39'])[0])[0][1]
        probe = c['steps'][-2]
        with tempfile.TemporaryDirectory() as root:
            logs = Path(root)/'logs'
            logs.mkdir()
            for count in (2, 1):
                (logs/'attempts.log').write_text('setup: marker is missing\n' * count)
                got = subprocess.run(['sh', '-c', probe['sh'].replace('{run_dir:greet}', root)], capture_output=True, text=True)
                r = runner.CaseRun.__new__(runner.CaseRun)
                r.w = SimpleNamespace(expand=lambda v:v)
                errors = r.check_expect(dict(exit=got.returncode, stdout=got.stdout.encode(), stderr=got.stderr.encode()), probe['expect'], stderr_rule=False)
                self.assertEqual(count != 2, bool(errors))
        for case_id, name in (('custody-02', 'trapper.pid'), ('custody-03', 'grandchild.pid')):
            c = runner.instances(runner.load_cases(ids=[case_id])[0])[0][1]
            with self.subTest(case=case_id), tempfile.TemporaryDirectory() as root:
                script = c['steps'][-1]['sh'].replace('{case}', root)
                dead = subprocess.Popen(['sleep', '0.01'])
                dead.wait()
                Path(root, name).write_text(str(dead.pid))
                good = subprocess.run(['sh', '-c', script], capture_output=True)
                self.assertEqual(0, good.returncode)
                live = subprocess.Popen(['sleep', '20'])
                try:
                    Path(root, name).write_text(str(live.pid))
                    bad = subprocess.run(['sh', '-c', script], capture_output=True)
                    self.assertEqual(1, bad.returncode, 'surviving child fake passed')
                finally:
                    live.kill()
                    live.wait()

    def test_recovery_observations_use_the_spec_workspace_and_reject_missing_fake(self):
        ids = ['v1.3-22-recovery-first', 'v1.3-23-recovery-later', 'v1.3-24-recovery-ref-failure',
               'v1.3-36-recovery-adopt-publication', 'v1.3-37-recovery-create-only',
               'v1.3-39-recovery-live-owner', 'v1.3-41-recovery-failure-retry']
        for original in runner.load_cases(ids=ids):
            c = runner.instances(original)[0][1]
            self.assertNotIn("{case}/workspace", json.dumps(c))
            # Exact snapshot/ref/live-owner assertions remain unchanged.
            self.assertEqual([s.get('assert') for s in original['steps'] if 'assert' in s],
                             [s.get('assert') for s in c['steps'] if 'assert' in s])
            for step in c['steps']:
                if not step.get('sh', '').startswith('work='):
                    continue
                # Publication itself is covered by the original recovery
                # mutants. Exercise the production path/guard before git here.
                probe = step['sh'].split('; export GIT_INDEX_FILE=')[0]
                with self.subTest(case=c['id']), tempfile.TemporaryDirectory() as root:
                    work = Path(root)/'state'/'run-R1'
                    (work/'lib').mkdir(parents=True)
                    (work/'lib/greet.txt').write_text('Latest candidate\n')
                    probe = probe.replace('{state_root}', str(Path(root)/'state')).replace('{run_id:greet}', 'run')
                    self.assertEqual(0, subprocess.run(['sh', '-c', probe], capture_output=True).returncode)
                    work.rename(work.with_name('wrong-workspace'))
                    self.assertEqual(1, subprocess.run(['sh', '-c', probe], capture_output=True).returncode,
                                     'wrong workspace fake fell through to checkout')

    def test_exunit_formatter_case_rejects_unformatted_fake(self):
        c = runner.instances(runner.load_cases(ids=['exunit-05'])[0])[0][1]
        source = '.kogen/acceptance/greet_test.exs'
        oracle = c['steps'][-1]['assert']['files'][source]
        unformatted = c['script'][0]['reply']['calls'][1]['arguments']['content']
        r = runner.CaseRun.__new__(runner.CaseRun)
        r.w = SimpleNamespace(expand=lambda v:v)
        with tempfile.TemporaryDirectory() as root:
            file = Path(root)/'acceptance.exs'
            r.w.path = lambda _: str(file)
            file.write_text(oracle['text'])
            self.assertEqual([],r._file_assert(source,oracle))
            file.write_text(unformatted)
            self.assertTrue(r._file_assert(source,oracle))

    def test_exunit_ledger_and_named_baseline_oracles_remain_strict(self):
        c = runner.instances(runner.load_cases(ids=['exunit-01'])[0])[0][1]
        oracle = c['steps'][-1]['assert']['files']['{run_dir:greet}/ledger.jsonl']
        r = runner.CaseRun.__new__(runner.CaseRun)
        with tempfile.TemporaryDirectory() as root:
            file = Path(root)/'ledger.jsonl'
            r.w = SimpleNamespace(path=lambda _:str(file))
            row = dict(tag='greet/A1', test='greets World', status='passed')
            file.write_text(json.dumps(row)+'\n')
            self.assertEqual([],r._file_assert('ledger',oracle))
            for key, value in [('tag','greet/A2'), ('test','test greets World'), ('status','failed'), ('extra','forbidden')]:
                bad = dict(row, **{key:value})
                file.write_text(json.dumps(bad)+'\n')
                self.assertTrue(r._file_assert('ledger',oracle))
        c = runner.instances(runner.load_cases(ids=['exunit-04'])[0])[0][1]
        want = c['steps'][2]['assert']['git'][0]['json']
        good = dict(check_baseline=[dict(name='unit',status='red',findings=[dict(path='test/hello_test.exs',symbol='legacy is broken')])])
        self.assertEqual([],matchers.match(want,good))
        bad = copy.deepcopy(good)
        bad['check_baseline'][0]['findings'][0]['symbol']='different failure'
        self.assertTrue(matchers.match(want,bad))

    def test_side_effect_keepalive_preserves_deadline_sensitivity(self):
        step = {'id':'reapprove', 'side_effect_sh':'sleep 1.2', 'side_effect_keepalive':True, 'reply':{'text':'plan'}}
        body = json.dumps({'input':[{'role':'user','content':'task'}]}).encode()
        with contextlib.ExitStack() as stack:
            server = fake_server.FakeServer(script=[step]).start()
            stack.callback(server.stop)
            url = 'http://127.0.0.1:%s/v1/responses' % server.port
            with urllib.request.urlopen(urllib.request.Request(url, data=body), timeout=0.5) as response:
                stream = response.read()
            self.assertGreaterEqual(stream.count(b': side-effect keepalive'), 2)
            self.assertIn(b'response.completed',stream)
            self.assertEqual(0,server.state.side_effect_log[0]['exit'])
            self.assertEqual(1,len(server.state.requests))
        # Removing keepalives makes this same fixture miss its first-byte
        # deadline. The harness never exempts requests from timeout checks.
        step['side_effect_keepalive'] = False
        with contextlib.ExitStack() as stack:
            server = fake_server.FakeServer(script=[step]).start()
            stack.callback(server.stop)
            url = 'http://127.0.0.1:%s/v1/responses' % server.port
            with self.assertRaises((TimeoutError, socket.timeout)):
                urllib.request.urlopen(urllib.request.Request(url,data=body),timeout=0.5)

    def test_historical_cases_do_not_get_schema_projection(self):
        cases = runner.load_cases(profiles=['shape'])
        r = runner.CaseRun.__new__(runner.CaseRun)
        r.case = cases[0]
        r.w = SimpleNamespace(expand=lambda v: v)
        steps = r.load_script(r.case['script'])
        self.assertFalse(any('callable_tools' in s.get('expect', {}) for s in steps))

if __name__ == '__main__':
    unittest.main()

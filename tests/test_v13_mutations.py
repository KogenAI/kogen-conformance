"""Every new case has a passing observation fixture and a killed faulty fake.

Checks run the same observation oracles/matchers as the black-box cases. Recovery
fixtures also use real git objects, symlinks and modes. This proves assertion
sensitivity; it is separate from the end-to-end run against kogen-rs.
"""
import copy,json,os,subprocess,sys,tempfile,unittest
from pathlib import Path
from types import SimpleNamespace
from kogen_conformance import contracts,matchers,runner
ROOT=Path(__file__).resolve().parents[1]
FAKE=ROOT/'tests/fakes/wrong_kogen.py'


def emit(observation, mutation=None):
    r=subprocess.run([sys.executable,str(FAKE)]+([mutation] if mutation else []),input=json.dumps(observation),capture_output=True,text=True,check=True)
    return json.loads(r.stdout)


def case_number(c):return int(c['id'].split('-')[1])


def receipt_fixture(n):
    # These facts are independent of case matchers and follow the scripted workload.
    cs=[dict(conversation_id='primary',model='gpt-6.1-sol',effort='high',logical_turns=2,validation_passes=1,style_repairs=0)]
    passes,guards,attempts,unknown,outcome=1,0,4,0,'success'
    if n==13:cs=[dict(cs[0],logical_turns=60,validation_passes=0),dict(cs[0],conversation_id='fallback')];guards=60;attempts=64
    if n==14:cs=[dict(cs[0],logical_turns=60,validation_passes=0),dict(cs[0],conversation_id='fallback',logical_turns=60,validation_passes=0)];passes=0;guards=120;attempts=120;outcome='failure'
    if n==15:cs[0]['logical_turns']=60;guards=58;attempts=62
    if n in (16,35):cs=[dict(cs[0],logical_turns=4,validation_passes=3,effort='medium'),dict(cs[0],conversation_id='fallback',effort='medium')];passes=4;attempts=8
    if n==17:cs=[dict(cs[0],logical_turns=4,validation_passes=3),dict(cs[0],conversation_id='fallback',logical_turns=4,validation_passes=3)];passes=6;attempts=8;outcome='failure'
    if n in (18,33):attempts=5;unknown=1
    if n==19:cs[0].update(logical_turns=1,validation_passes=0);passes=0;attempts=4;unknown=4;outcome='failure'
    if n==31:cs[0].update(logical_turns=4,style_repairs=2);attempts=6
    if n==32:cs[0].update(logical_turns=3,validation_passes=2);passes=2;attempts=7
    if n==43:cs=[dict(cs[0],logical_turns=4,validation_passes=3),dict(cs[0],conversation_id="fallback",logical_turns=5,validation_passes=3)];passes=6;attempts=11
    if n==34:cs=[dict(cs[0],logical_turns=4,validation_passes=3,model='grok-4.6'),dict(cs[0],conversation_id='fallback',model='grok-4.6')];passes=4;attempts=8
    return dict(schema=1,profile='shape-v1.3',outcome=outcome,conversations=cs,validation_passes=passes,finish_guards=guards,http_attempts=attempts,unknown_usage_attempts=unknown,elapsed_ms=1500,roles={'shaper':sum(c['logical_turns'] for c in cs),'auditor':2 if outcome=='success' else 0},repairs={'style':sum(c['style_repairs'] for c in cs),'candidate':0},tokens={'input':120,'cached_input':20,'output':30,'reasoning':10})


def fixtures(c):
    n=case_number(c)
    if n==44:return dict(run={'recovery':[],'cleanup_pending':False}),'old-run-schema'
    if n==45:return dict(report={'land_policy':'green'}),'legacy-default-policy'
    if n==46:return dict(exit=0),'valid-config-refused'
    if n==47:
        return dict(
            stopped_run={
                'exit':4,
                'stdout':'building greet\nstopped greet: provider/overload; it stays queued (Build abcdef01)\nqueue: stopped because greet hit a provider error; 1 Build(s), 0 landed, 1 not\n',
            },
            stopped_events=[
                {'event':'provider_retry','reason':'provider/overload'},
                {'event':'provider_retry','reason':'provider/overload'},
                {'event':'provider_retry','reason':'provider/overload'},
                {'event':'finished','status':'stopped','reason':'provider/overload'},
            ],
            first_request_roles=['planner']*4,
            queued_status={'exit':0,'stdout':'greet: queued, 1 of 1\n'},
            resumed_run={
                'exit':0,
                'stdout':'building greet\nlanded greet abcdef01 (Build fedcba98)\nqueue: done; 1 Build(s), 1 landed, 0 not\n',
            },
            request_roles=['planner']*5+['builder']*2,
            remaining=[],
        ), 'fail-stopped-intent'
    if n in (48,49):
        return dict(
            events=[{'event':'provider_wait','reason':'provider/usage_limit','wait_ms':300000,'budget_paused':True}],
            refresh_count=0,
        ), 'refresh-usage-limit'
    if n in (1,2,3,5,40):
        report=dict(advisory_items=[],acceptance=[{'id':'A1','status':'pass','demoted':False},{'id':'A2','status':'fail','demoted':False}],verdict='unverified',best_candidate={'rung':'R1','verdict':'unverified'},land_policy='green')
        events=[{'event':'verification','result':'red'},{'event':'audit','mode':'observational','warnings':['unknown audit item']},{'event':'repair'},{'event':'verification','result':'green'},{'event':'finished','status':'landed'}]
        return dict(report=report,events=events), 'skip-verification' if n==3 else 'rank-advice' if n==40 else 'reject-false' if n==5 else 'suppress-audit-warning' if n==2 else 'demote'
    if n in (4,20,21):
        text={4:'build.auditor_demotion has no admitted calibration',20:'build.roles has unknown role "fallback_shaper"',21:'shaper model belongs to a different provider than grok'}[n]
        return dict(exit=3,stdout=text+'\n'),'accept-experimental'
    if n in (6,7,8):return dict(checked={6:'RED\nGREEN\n',7:'GREEN\n',8:'GREEN\nGREEN\n'}[n]),{6:'stale-baseline',7:'dirty-base',8:'ignore-check-context'}[n]
    if n==42:return dict(checked='red\ngreen\n'),'stale-environment'
    if n==9:return dict(report={'verdict':'unverified','checks':[{'name':'baseline','excused':False}]}),'excuse-regression'
    if n in (10,11):
        req=[]
        for i in range(3 if n==10 else 4):
            inputs=[{'role':'developer','content':'Generic instructions'},{'role':'user','content':'task-a'}]+[{'role':'assistant','content':'progress'}]*i
            req.append(dict(body=dict(instructions='Generic instructions',input=inputs,tools=[{'type':'function','name':name,'parameters':{'type':'object'}} for name in ('edit','read','search','write','shell','finish','tool_output')],model='sol',store=False,stream=True,prompt_cache_key='shared-safe'),headers={'thread-id':'thread-'+str(i) if n==11 else 'thread-one'}))
        return dict(requests=req),'rewrite-history' if n==10 else 'prefix-pollution'
    if n in tuple(range(12,20))+(31,32,33,34,35,43):return dict(receipt=receipt_fixture(n)), 'cross-provider-fallback' if n==34 else 'shape-counter'
    if n in (22,23,24,36,37,38,39,41):
        files={'lib/greet.txt':{'text':'Newest repair\n' if n==37 else 'Latest candidate\n'},'lib/deleted.txt':None,'lib/new.txt':{'text':'Untracked latest\n'},'lib/exec.sh':{'text':'#!/bin/sh\necho latest\n','mode':'100755'},'lib/link':{'text':'greet.txt','mode':'120000'}}
        if n==38:files={'lib/post-cas.txt':{'text':'After CAS work\n'},'lib/greet.txt':{'text':'Latest candidate\n'}}
        return dict(files=files,candidate_count=2 if n in (23,37) else 1,workspace_exists=True),{36:'duplicate-publication',37:'overwrite-candidate',39:'destroy-live'}.get(n,'lose-latest')
    if 25<=n<=30:
        spec=c['steps'][0]['cache_replay']
        if n==30:spec=dict(spec,fixture='v1.3/30-cache-miss-vs-incomplete-missing-usage.json')
        replay=json.loads((ROOT/'data'/spec['fixture']).read_text())
        try: report=contracts.measure_cache(replay)
        except ValueError:return dict(rejected=True),'accept-infeasible'
        return dict(cache=report),{25:'production-gate',26:'ignore-blocks',27:'unknown-is-miss',28:'lower-threshold',30:'incomplete-is-pass'}[n]
    raise AssertionError('No independent mutation fixture for '+c['id'])


def check(c,d):
    n=case_number(c)
    if n==44:return matchers.match({k:c['steps'][-1]['assert']['run_json']['match'][k] for k in ('recovery','cleanup_pending')},d['run'])
    if n==45:return matchers.match({'land_policy':c['steps'][-1]['expect']['stdout_json']['land_policy']},d['report'])
    if n==46:return matchers.match({'exit':0},d)
    if n==47:
        r=runner.CaseRun.__new__(runner.CaseRun)
        r.case=c
        r.w=SimpleNamespace(expand=lambda value:value)
        errors=[]
        for step_index,key in ((2,'stopped_run'),(4,'queued_status'),(5,'resumed_run')):
            step=c['steps'][step_index]
            expect=step['expect']
            obs=d[key]
            errors+=r.check_expect({'exit':obs['exit'],'stdout':obs['stdout'].encode(),'stderr':b''},expect)
        def assert_with(events,roles,remaining=None):
            state=SimpleNamespace(
                requests=[{'role':role} for role in roles],
                oauth=[],
                remaining=lambda: remaining if remaining is not None else [],
            )
            r.w=SimpleNamespace(
                expand=lambda value:value,
                runs=lambda slug:[(None,'run',{})],
                events=lambda run_dir:events,
                fake=SimpleNamespace(state=state),
            )
            return r.assertions
        errors+=assert_with(d['stopped_events'],d['first_request_roles'])(c['steps'][3]['assert'])
        errors+=assert_with([],d['request_roles'],d['remaining'])(c['steps'][6]['assert'])
        return errors
    if n in (48,49):
        r=runner.CaseRun.__new__(runner.CaseRun)
        r.case=c
        state=SimpleNamespace(
            requests=[],
            oauth=[{'kind':'token:refresh_token'} for _ in range(d['refresh_count'])],
        )
        r.w=SimpleNamespace(
            expand=lambda value:value,
            runs=lambda slug:[(None,'run',{})],
            events=lambda run_dir:d['events'],
            fake=SimpleNamespace(state=state),
        )
        return r.assertions(c['steps'][-1]['assert'])
    if n in (1,2,3,5,40):
        e=contracts.observational(d['report'],d['events'],n==2)
        if n==3:e+=matchers.match({'$subsequence':[{'event':e} if isinstance(e,str) else e for e in c['steps'][3]['assert']['events']['subsequence']]},d['events'])
        if n==40:e+=matchers.match({'best_candidate':{'rung':'R1'}},d['report'])
        if n==5:e+=matchers.match({'exit':0}, {'exit':d.get('exit',0)})
        return e
    if n in (4,20,21):
        exp=c['steps'][1]['expect'];r=runner.CaseRun.__new__(runner.CaseRun);r.w=SimpleNamespace(expand=lambda v:v);r.case=c
        return r.check_expect({'exit':d['exit'],'stdout':d['stdout'].encode(),'stderr':b''},exp)
    if n in (6,7,8):return matchers.match({6:'RED\nGREEN\n',7:'GREEN\n',8:'GREEN\nGREEN\n'}[n],d['checked'])
    if n==42:return matchers.match('red\ngreen\n',d['checked'])
    if n==9:return matchers.match(c['steps'][-1]['expect']['stdout_json'],d['report'])
    if n in (10,11):return contracts.reusable_prefix(d['requests'],n==11)
    if n in tuple(range(12,20))+(31,32,33,34,35,43):
        exp=c['steps'][-1]['assert']['v13']['expected']
        return contracts.shape_accounting(d['receipt'],exp,[{}]*receipt_fixture(n)['http_attempts'],1500)
    if n in (22,23,24,36,37,38,41):
        if n in (36,37):return matchers.match(1 if n==36 else 2,d['candidate_count'])
        oracle=next(s['assert']['v13'] for s in c['steps'] if 'assert' in s and 'v13' in s['assert'])
        # Same production recovery oracle inspects real git mode/content and record identity.
        with tempfile.TemporaryDirectory() as root:
            work=Path(root)/'workspace';work.mkdir()
            env=dict(os.environ,GIT_CONFIG_GLOBAL='/dev/null',GIT_CONFIG_NOSYSTEM='1')
            def git(args):return subprocess.check_output(['git','-C',str(work)]+args,env=env,text=True).strip()
            git(['init','-q']);git(['config','user.name','Mutation Test']);git(['config','user.email','mutation@kogen.invalid'])
            for p,w in d['files'].items():
                if w is None:continue
                path=work/p;path.parent.mkdir(parents=True,exist_ok=True)
                if w.get('mode')=='120000':path.symlink_to(w['text'])
                else:path.write_text(w['text']);path.chmod(0o755 if w.get('mode')=='100755' else 0o644)
            git(['add','-A']);git(['-c','commit.gpgsign=false','commit','-q','-m','Unverified recovery'])
            ref='refs/kogen/candidates/test/recovery-workspace';git(['update-ref',ref,'HEAD']);tree=git(['rev-parse','HEAD^{tree}'])
            run={'cleanup_pending':False,'recovery':[dict(workspace='workspace',base='base',tree=tree,ref=ref,archive=None,verification='unverified')]}
            r=runner.CaseRun.__new__(runner.CaseRun)
            r.w=SimpleNamespace(fake=None,latest_run=lambda _: (0,root,run),origin=str(work),git=lambda args,cwd=None:git(args),git_env=lambda:env)
            return r._v13_assert(oracle)
    if n==39:return matchers.match(True,d['workspace_exists'])
    if 25<=n<=30:
        if n==29:return matchers.match(True,d['rejected'])
        exp=c['steps'][0]['cache_replay'].get('expect',{})
        if n==30:exp={'qualification':'incomplete','live_release_qualified':False}
        return matchers.match(exp,d['cache'])
    raise AssertionError(n)


class MutationTests(unittest.TestCase):
    def test_every_new_case_kills_wrong_fake(self):
        results=[]
        for p in sorted((ROOT/'cases/v1.3').glob('*.json')):
            c=json.loads(p.read_text())
            with self.subTest(case=c['id']):
                if c['id'] in ('v1.3-48-429-no-refresh','v1.3-49-sse-rate-limit-no-refresh'):
                    self.assertEqual('owned',c.get('auth'))
                    self.assertIn('login',c.get('needs',[]))
                    self.assertTrue(c.get('serial'))
                    self.assertEqual(['kogen','provider','login','chatgpt'],c['steps'][0]['run'])
                obs,mutation=fixtures(c)
                good=check(c,emit(obs));bad=check(c,emit(obs,mutation))
                self.assertEqual([],good,'positive fixture must pass')
                self.assertTrue(bad,'deliberately wrong fake survived: '+mutation)
                results.append(dict(id=c['id'],mutation=mutation,control='pass',mutant='killed',diagnostics=bad))
        if len(results)==len(list((ROOT/'cases/v1.3').glob('*.json'))):
            (ROOT/'reference/results/v1.3/mutations.json').write_text(json.dumps(results,indent=2)+'\n')

    def test_serialization_choices_are_accepted(self):
        c=json.loads((ROOT/'cases/v1.3/v1.3-10-reusable-prefix.json').read_text())
        obs,_=fixtures(c)
        # Whitespace, escaping and outer object member order have no provider-visible effect.
        for i,r in enumerate(obs['requests']):
            raw=json.dumps(r['body'],sort_keys=bool(i%2),indent=i,ensure_ascii=bool(i%2))
            r['body']=json.loads(raw)
        self.assertEqual([],check(c,obs))

    def test_overlay_keeps_v12_and_resolves_historical_ids(self):
        active=runner.load_cases()
        self.assertTrue(any(c['id']=='v1.2-02-approval-hash-intent-and-test-bytes' for c in active))
        self.assertFalse(any(c['id']=='v1.2-73-ladder-05' for c in active))
        self.assertEqual(['v1.3-01-observational-auditor'],[c['id'] for c in runner.load_cases(ids=['ladder-05'])])

if __name__=='__main__':unittest.main()

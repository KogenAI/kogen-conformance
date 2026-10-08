#!/usr/bin/env python3
"""Deliberately wrong black-box observation emitter for v1.3 oracle mutation checks.

JSON input is a frozen observation fixture, not a case's expected matcher. The
mutations simulate implementations that weaken a gate, reuse the wrong baseline,
lose recovery data, miscount Shape, pollute a prefix or misqualify cache reuse.
This is an oracle-boundary fake, not a complete Kogen CLI implementation.
"""
import copy,json,sys

def apply(doc, mutation):
    d=copy.deepcopy(doc)
    if mutation == 'demote':
        d['report']['acceptance'][-1]['demoted']=True
        d['report']['advisory_items']=['A2']
        d['events'].append({'event':'acceptance_demoted','id':'A2'})
    elif mutation == 'suppress-audit-warning':
        for e in d['events']: e.pop('warnings',None)
    elif mutation == 'skip-verification':
        d['events']=[e for e in d['events'] if e.get('result')!='green']
    elif mutation == 'rank-advice': d['report']['best_candidate']['rung']='R3'
    elif mutation == 'accept-experimental': d.update(exit=0,stdout='Queue: stopped\nNo Intents.\n')
    elif mutation == 'old-run-schema': d['run'].pop('recovery');d['run'].pop('cleanup_pending')
    elif mutation == 'legacy-default-policy': d['report']['land_policy']='green-or-advisory'
    elif mutation == 'valid-config-refused': d['exit']=3
    elif mutation == 'reject-false': d.update(exit=3,stdout='environment/project_config_invalid: unknown key auditor_demotion\n')
    elif mutation == 'stale-environment': d['checked']='red\n'
    elif mutation == 'stale-baseline': d['checked']='RED\n'
    elif mutation == 'dirty-base': d['checked']='DIRTY\n'
    elif mutation == 'ignore-check-context': d['checked']='GREEN\n'
    elif mutation == 'excuse-regression': d['report'].update(verdict='green',checks=[{'name':'baseline','excused':True}])
    elif mutation == 'prefix-pollution': d['requests'][-1]['body']['input'][0]['content']='generic\nrun timestamp: 2026-10-07T00:00:01Z'
    elif mutation == 'rewrite-history': d['requests'][-1]['body']['input'][1]['content']='silently rewritten task'
    elif mutation == 'shape-counter':
        # Count retry/guard/style activity as a validation, or omit the last pass.
        d['receipt']['validation_passes']+=1
    elif mutation == 'cross-provider-fallback': d['receipt']['conversations'][-1].update(model='gpt-6.1-sol',effort='high')
    elif mutation == 'lose-latest':
        path='lib/post-cas.txt' if 'lib/post-cas.txt' in d['files'] else 'lib/greet.txt'
        d['files'][path]['text']='Earlier candidate\n'
    elif mutation == 'overwrite-candidate': d['candidate_count']=1
    elif mutation == 'duplicate-publication': d['candidate_count']=2
    elif mutation == 'destroy-live': d['workspace_exists']=False
    elif mutation == 'fail-stopped-intent':
        d['queued_status']['stdout']='greet: failed, 1 of 1\n'
        d['stopped_events'][-1]['status']='failed'
    elif mutation == 'refresh-usage-limit': d['refresh_count'] += 1
    elif mutation == 'production-gate': d['cache']['qualification']='fail'
    elif mutation == 'ignore-blocks': d['cache']['requests'][1]['eligible_input']=2500
    elif mutation == 'unknown-is-miss': d['cache']['requests'][0]['measurement']='miss';d['cache']['partial']=False
    elif mutation == 'lower-threshold': d['cache']['qualification']='fail'
    elif mutation == 'accept-infeasible': d['rejected']=False
    elif mutation == 'incomplete-is-pass': d['cache']['qualification']='pass'
    else: raise ValueError(mutation)
    return d

if __name__=='__main__':
    observation=json.load(sys.stdin)
    if len(sys.argv)>1: observation=apply(observation,sys.argv[1])
    print(json.dumps(observation))

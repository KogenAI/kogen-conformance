"""Versioned projections of inherited assertions to the v1.3 contracts.

Historical case/template files stay frozen. Schemas are shared (§4.9.2); call
permissions remain role scoped (§4.7). No behavioral outcome is projected.
"""
import copy
import json

CANONICAL_TOOLS = ['edit', 'finish', 'read', 'search', 'shell', 'tool_output', 'write']


def project_script(steps):
    steps = copy.deepcopy(steps)
    for step in steps:
        exp = step.get('expect', {})
        if 'instructions_contains' in exp:
            exp['system_prompt_contains'] = exp.pop('instructions_contains')
        if 'tools' not in exp:
            continue
        old = exp['tools']
        # v1.1 shell recipes exposed shell alone; v1.2 added finish/tool_output.
        role = exp.get('role')
        if role in ('planner', 'auditor', 'test_auditor', 'requirement_auditor'):
            callable_tools = []
        elif old == ['shell']:
            callable_tools = ['shell', 'finish', 'tool_output']
        else:
            callable_tools = old
        exp['callable_tools'] = sorted(callable_tools)
        exp['tools'] = CANONICAL_TOOLS[:]
    return steps


def project_schema_matchers(value):
    """Migrate schema matchers, including Owned additional_tools, not permissions."""
    if isinstance(value, list):
        for item in value:
            project_schema_matchers(item)
    elif isinstance(value, dict):
        tools = value.get('tools')
        if value.get('type') == 'additional_tools' and isinstance(tools, dict) and tools.get('$len') == 3:
            tools['$len'] = 7
            tools.setdefault('$contains', []).extend({'name': n} for n in ('edit', 'read', 'search', 'write'))
        for item in value.values():
            project_schema_matchers(item)


def project_landing_lines(value):
    """Correct the copied literal marker in top-level and nested expectations."""
    if isinstance(value, dict):
        for i, line in enumerate(value.get('stdout_lines', [])):
            # ~ is matcher syntax, not CLI output (§1.7.4).
            if line.startswith('~\\~landed '):
                value['stdout_lines'][i] = '~landed ' + line[len('~\\~landed '):]
        for child in value.values():
            project_landing_lines(child)
    elif isinstance(value, list):
        for child in value:
            project_landing_lines(child)


def project_case(case):
    case = copy.deepcopy(case)
    # Retain every other body/header assertion while moving role markers to
    # the provider-visible developer prompt and broadening only schemas.
    for step in case.get('steps', []):
        for req in step.get('assert', {}).get('fake_requests', []):
            body = req.get('match', {}).get('body', {})
            project_schema_matchers(body)
            tools = body.get('tools')
            if isinstance(tools, dict) and tools.get('$len') == 3:
                tools['$len'] = 7
                tools.setdefault('$contains', []).extend({'name': n} for n in ('edit', 'read', 'search', 'write'))
            marker = body.get('instructions')
            if isinstance(marker, dict) and '$contains_text' in marker:
                req['system_prompt_contains'] = marker['$contains_text']
                del body['instructions']
            elif isinstance(marker, str) and marker.startswith('~'):
                req['system_prompt_regex'] = marker[1:]
                del body['instructions']
    if case['id'] in ('v1.3-22-recovery-first', 'v1.3-23-recovery-later',
                      'v1.3-24-recovery-ref-failure', 'v1.3-36-recovery-adopt-publication',
                      'v1.3-37-recovery-create-only', 'v1.3-39-recovery-live-owner',
                      'v1.3-41-recovery-failure-retry'):
        # §5.4 defines the workspace path. Observe it from the harness rather
        # than asking a confined child to publish a marker outside its clone.
        marker = "pwd > '{case}/workspace'; "
        for script in case['script']:
            for call in script.get('reply', {}).get('calls', []):
                args = call.get('arguments', {})
                if call.get('name') == 'shell' and args.get('cmd', '').startswith(marker):
                    args['cmd'] = args['cmd'][len(marker):]
        for step in case['steps']:
            if 'sh' in step:
                step['sh'] = step['sh'].replace("work=$(cat '{case}/workspace')", "work='{state_root}/{run_id:greet}-R1'; test -d \"$work\" || exit 1")
    if case['id'] in ('exunit-01', 'exunit-03', 'exunit-04', 'exunit-06'):
        for step in case['script']:
            if step.get('expect', {}).get('role') == 'builder' and step['id'].startswith('done'):
                step['reply'] = {'calls': [{'name': 'finish', 'arguments': {}}]}
    project_landing_lines(case['steps'])
    if case['id'] == 'v1.2-124-build-31':
        for step in case['steps']:
            for script in step.get('fake', {}).get('script', []):
                if script.get('id') == 'g.plan':
                    script['side_effect_keepalive'] = True
    if case['id'] in ('v1.2-59-build-25', 'v1.2-60-build-26'):
        case['steps'][-1 if case['id'] == 'v1.2-59-build-25' else -2]['assert']['events']['contains'] = [{'event': 'repair', 'reason': 'rebase_conflict'}]
    if case['id'] == 'exunit-05':
        ledger = next(s for s in case['script'] if s['id'] == 'ledger')
        doc = json.loads(ledger['reply']['text'])
        doc['rows'].append({'constraint': 'Hello!', 'maps_to': 'A1'})
        ledger['reply']['text'] = json.dumps(doc)
    if case['id'] == 'v1.2-119-custody-06':
        # This case attacks Build confinement. Exact-base approval now runs in
        # scratch too; arm the attack only after approval has completed.
        write = case['steps'][0]['write']
        write['text'] = write['text'].replace('#!/bin/sh\n', '#!/bin/sh\n[ -f "{case}/escape-armed" ] || exit 0\n', 1)
        case['steps'].insert(4, {'write': {'path': '{case}/escape-armed', 'text': ''}})
    if case['id'] in ('custody-02', 'custody-03', 'state-28'):
        # The checked base may live in a disposable scratch checkout (§3.3).
        # Observe child lifetime/check count outside that checkout.
        paths = {'custody-02': 'build/trapper.pid', 'custody-03': 'build/grandchild.pid', 'state-28': 'build/lint-runs'}
        old = paths[case['id']]
        new = '{case}/' + old.split('/')[-1]
        for path, content in case['fixture_files'].items():
            case['fixture_files'][path] = content.replace(old, new)
        for step in case['steps']:
            if 'sh' in step:
                step['sh'] = step['sh'].replace(old, new)
    if case['id'] == 'build-39':
        # A marker visible to exact-base scratch approval, explicitly removed
        # before Build, forces both rung setup attempts to fail.
        case['fixture_files']['checks/setup.sh'] = '#!/bin/sh\n[ -f "{case}/setup-ok" ] || { echo "setup: marker is missing"; exit 9; }\nmkdir -p build && : > build/ready\n'
        case['steps'][0]['write']['path'] = '{case}/setup-ok'
        case['steps'].insert(3, {'remove': '{case}/setup-ok'})
        case['steps'].insert(-1, {'sh': "grep -h '^setup: marker is missing$' \"{run_dir:greet}\"/logs/*", 'expect': {'exit': 0, 'stdout': 'setup: marker is missing\nsetup: marker is missing\n'}})
    if case['id'] == 'shape-06':
        req = case['steps'][-1]['assert']['fake_requests'][0]
        req['first_user_regex'] = req.pop('input_regex')
    return case

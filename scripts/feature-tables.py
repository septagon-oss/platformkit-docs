#!/usr/bin/env python3
"""Render the routes, authorization and events tables of every feature page.

The tables are generated, never typed: the routes and their declared
authorization and published events come from the OpenAPI document the
application serves at /openapi.json (kept beside this script as
scripts/openapi.json, with the revision it was taken from), and the
subscriptions come from the module manifests in the source tree. Each table
sits between markers in its page; everything outside the markers is prose a
person wrote. Run `make tables` after refreshing the snapshot.
"""
import json, pathlib, re, sys, collections

HERE = pathlib.Path(__file__).resolve().parent
DOCS = HERE.parent / 'docs' / 'modules' / 'ROOT' / 'pages' / 'features'
openapi_path = pathlib.Path(sys.argv[1]) if len(sys.argv) > 1 else HERE / 'openapi.json'
source = pathlib.Path(sys.argv[2]) if len(sys.argv) > 2 else HERE.parent.parent / 'platformkit'
revision = (HERE / 'openapi.revision').read_text().strip() if (HERE / 'openapi.revision').exists() else 'unknown'

doc = json.loads(openapi_path.read_text())
ops = []
for path, methods in doc['paths'].items():
    for method, op in methods.items():
        if not isinstance(op, dict) or 'operationId' not in op:
            continue
        module = op['operationId'].split('-')[0]
        auth = op.get('x-platformkit-auth') or {}
        ops.append(dict(module=module, method=method.upper(), path=path, id=op['operationId'],
                        summary=op.get('summary', ''), kind=auth.get('kind', ''), permission=auth.get('permission', ''),
                        events=list(op.get('x-platformkit-events') or [])))
ops.sort(key=lambda o: (o['module'], o['path'], ['GET', 'POST', 'PUT', 'PATCH', 'DELETE'].index(o['method']) if o['method'] in ('GET', 'POST', 'PUT', 'PATCH', 'DELETE') else 9))

def events_of(module):
    """The event names a module's contracts declare, in declaration order."""
    f = source / 'modules' / module / 'contracts' / 'events.go'
    if not f.exists():
        return []
    return list(dict.fromkeys(re.findall(r'"([a-z_]+\.[a-z_.]+)"', f.read_text())))

# Subscriptions, read from the manifests: a module either subscribes to every
# event or names each event it handles.
subscriptions = collections.defaultdict(list)   # event -> [module]
handles_all = []
for manifest in sorted((source / 'modules').glob('*/module.go')):
    module = manifest.parent.name
    text = manifest.read_text()
    if re.search(r'SubscribeAll:\s*true', text):
        handles_all.append(module)
    block = text[text.find('Subscriptions:'):] if 'Subscriptions:' in text else ''
    names = re.findall(r'Name:\s*([A-Za-z]+\.Event[A-Za-z]+|"[a-z_.]+")', block.split('Routes:')[0])
    for internal in (manifest.parent / 'internal').glob('*.go'):
        if internal.name.endswith('_test.go'):
            continue
        t = internal.read_text()
        for m in re.finditer(r'events\.Subscription\{[^}]*?Name:\s*([A-Za-z]+\.Event[A-Za-z]+|"[a-z_.]+")', t, re.S):
            names.append(m.group(1))
    for name in names:
        if name.startswith('"'):
            subscriptions[name.strip('"')].append(module)
        else:
            pkg, const = name.split('.')
            owner = {'usercontracts': 'user', 'contracts': module}.get(pkg, pkg.replace('contracts', ''))
            f = source / 'modules' / owner / 'contracts' / 'events.go'
            m = re.search(const + r'\s*=\s*"([a-z_.]+)"', f.read_text()) if f.exists() else None
            if m:
                subscriptions[m.group(1)].append(module)

def auth_cell(o):
    return {'permission': f"`{o['permission']}`", 'operator_permission': f"`{o['permission']}` (operator)",
            'public': 'public', 'signed_in': 'signed in'}.get(o['kind'], o['kind'] or '?')

def esc(path):
    return path.replace('{', '\\{')

def routes_table(module):
    rows = [f"| `{o['method']}` | `{esc(o['path'])}` | {o['summary']} | {auth_cell(o)} | " + (', '.join(f'`{e}`' for e in o['events']) or '—') for o in ops if o['module'] == module]
    if not rows:
        return None
    return '\n'.join(['[cols="1,4,3,3,4"]', '|===', '| Method | Path | Does | Authorization | Publishes', ''] + rows + ['|==='])

def authorization_table(module):
    mine = [o for o in ops if o['module'] == module]
    by = collections.OrderedDict()
    for o in mine:
        key = (o['kind'], o['permission'])
        by.setdefault(key, []).append(o['id'].split('-', 2)[-1] if o['id'].count('-') >= 2 else o['id'])
    rows = []
    for (kind, perm), verbs in by.items():
        name = {'permission': f'`{perm}`', 'operator_permission': f'`{perm}`', 'public': 'none: public', 'signed_in': 'none: any signed-in member'}[kind]
        scope = {'permission': 'a member of the tenant', 'operator_permission': "the operator's tenant only", 'public': 'anyone', 'signed_in': 'a session of this tenant'}[kind]
        rows.append(f"| {name} | {scope} | " + ', '.join(f'`{v}`' for v in verbs))
    if not rows:
        return None
    return '\n'.join(['[cols="2,2,4"]', '|===', '| Authorization | Who passes | Routes', ''] + rows + ['|==='])

def events_table(module):
    declared = events_of(module)
    from_routes = collections.OrderedDict()
    for o in ops:
        if o['module'] == module:
            for e in o['events']:
                from_routes.setdefault(e, []).append(o['id'].split('-', 2)[-1])
    names = list(dict.fromkeys(declared + list(from_routes)))
    if not names:
        return None
    rows = []
    for e in names:
        publishers = ', '.join(f'`{v}`' for v in from_routes.get(e, [])) or 'a job, hook or command in the module'
        handlers = [f'`{m}`' for m in subscriptions.get(e, [])] + [f'`{m}` (every event)' for m in handles_all]
        rows.append(f"| `{e}` | {publishers} | " + (', '.join(handlers) or '—'))
    return '\n'.join(['[cols="3,3,3"]', '|===', '| Event | Published by | Handled by', ''] + rows + ['|==='])

BEGIN = '// generated:%s:begin — from scripts/openapi.json at %s and the module manifests; run make tables, do not edit'
END = '// generated:%s:end'

def splice(text, name, table, after_heading):
    block = f"{BEGIN % (name, revision)}\n{table}\n{END % name}"
    pattern = re.compile(re.escape('// generated:%s:begin' % name) + r'.*?' + re.escape(END % name), re.S)
    if pattern.search(text):
        return pattern.sub(lambda _: block, text)
    if after_heading in text:
        return text.replace(after_heading + '\n', after_heading + '\n\n' + block + '\n', 1)
    return text

changed = []
for page in sorted(DOCS.glob('*.adoc')):
    module = page.stem
    text = page.read_text()
    routes, auth, events = routes_table(module), authorization_table(module), events_table(module)
    if routes:
        text = splice(text, 'routes', routes, '== Routes and screens')
    if auth:
        if '== Authorization' not in text:
            text = text.replace('\n== Events, jobs and subscriptions', '\n== Authorization\n\n== Events, jobs and subscriptions', 1)
        text = splice(text, 'authorization', auth, '== Authorization')
    if events:
        text = splice(text, 'events', events, '== Events, jobs and subscriptions')
    if text != page.read_text():
        page.write_text(text); changed.append(module)
print('tables rendered for', changed or 'nothing (all current)')
print('modules in the snapshot:', sorted({o['module'] for o in ops}), '| subscriptions:', dict(subscriptions), '| every event:', handles_all)

"""Weighted, declarative correspondence grammar for annotated event imports.

Rules propose complete programs and bindings. Existing guarded kernels execute
them; source deltas are matching evidence, never executable target mutations.
"""
from copy import deepcopy
from itertools import product
import json
import math
from pathlib import Path
import random


DEFAULT_BANK = Path(__file__).with_name('mapping_bank') / 'core.json'


def _positive(value):
    return type(value) in (int, float) and math.isfinite(value) and value > 0


def load_bank(path=DEFAULT_BANK):
    bank = json.loads(Path(path).read_text())
    if Path(path) == DEFAULT_BANK:
        for name in ('story_tokens.json','seed_stories.json'):
            extension = json.loads(DEFAULT_BANK.with_name(name).read_text())
            validate_bank(extension)
            bank['rules'].extend(extension['rules'])
    validate_bank(bank)
    return bank


def validate_bank(bank):
    from .reusable_operations import ReusableLines
    if bank.get('schema') != 'event-mapping-bank-v1' or not bank.get('rules'):
        raise ValueError('nonempty event-mapping-bank-v1 required')
    ids = set()
    for rule in bank['rules']:
        if set(rule) != {'id', 'weight', 'profiles', 'source', 'target'}:
            raise ValueError('invalid mapping rule fields')
        if not isinstance(rule['id'], str) or not rule['id'] or rule['id'] in ids:
            raise ValueError('unique mapping rule IDs required')
        ids.add(rule['id'])
        if not _positive(rule['weight']):
            raise ValueError('positive finite rule weight required')
        source, target = rule['source'], rule['target']
        allowed_source = {'kinds', 'bind', 'equals', 'scenarios', 'role_kinds', 'absent'}
        if (not {'kinds', 'bind', 'equals'} <= set(source) or set(source)-allowed_source
                or set(target) != {'id', 'event', 'roles'}):
            raise ValueError('invalid source/target rule fields')
        if not source['kinds'] or not rule['profiles'] or not target['id']:
            raise ValueError('rule kinds, profiles and target ID required')
        roles = target['roles']
        if set(roles) != set(source['bind']):
            raise ValueError('each target role needs a source correspondence')
        event = target['event']
        if (event.get('op') not in ReusableLines.fields
                or set(event) != {'op'} | ReusableLines.fields[event['op']]):
            raise ValueError('unsupported target operation/signature')
        if {v for k, v in event.items() if k != 'op'} != set(roles):
            raise ValueError('target event must use all declared roles')
        for spec in roles.values():
            if set(spec) != {'kind', 'properties'} or not isinstance(spec['properties'], list):
                raise ValueError('role requirements are kind and properties')
        for slot, role in event.items():
            if slot != 'op' and roles[role]['kind'] not in ReusableLines.kinds[slot]:
                raise ValueError('target role kind does not fit operation slot')
        if 'changes' not in source['equals']:
            raise ValueError('rule must explicitly match complete source changes')
        if set(source.get('role_kinds', {})) - set(roles):
            raise ValueError('unknown source role kind')
        _substitute(source['equals'], {role: role for role in roles})


def _path(value, path):
    for part in path.split('.'):
        value = value[int(part)] if isinstance(value, list) else value[part]
    return value


def _substitute(value, bindings):
    if isinstance(value, str) and value.startswith('$'):
        if value[1:] not in bindings:
            raise ValueError('unbound rule variable: '+value)
        return bindings[value[1:]]
    if isinstance(value, dict):
        return {k: _substitute(v, bindings) for k, v in value.items()}
    if isinstance(value, list):
        return [_substitute(v, bindings) for v in value]
    return value


def _evidence(event):
    """Canonicalize set deltas without interpreting them as target effects."""
    evidence = deepcopy(event)
    changes = []
    for entity, fields in sorted(event['effects'].items()):
        for field, delta in sorted(fields.items()):
            if set(delta) != {'before', 'after'}:
                raise ValueError('unsupported source effect evidence')
            change = dict(entity=entity, field=field)
            if field == 'state':
                before, after = set(delta['before']), set(delta['after'])
                change.update(add=sorted(after-before), remove=sorted(before-after))
            elif field == 'memes':
                before, after = delta['before'], delta['after']
                for name in sorted(before.keys() | after.keys()):
                    if before.get(name) != after.get(name):
                        changes.append(dict(entity=entity, field='memes.'+name,
                            before=before.get(name), after=after.get(name)))
                continue
            else:
                change.update(deepcopy(delta))
            changes.append(change)
    evidence.update(changes=changes, movements_count=len(event['movements']))
    return evidence


def _match(rule, event, graph=None):
    if event['kind'] not in rule['source']['kinds']:
        return None
    if rule['source'].get('scenarios') and (graph is None or graph['scenario'] not in rule['source']['scenarios']):
        return None
    evidence = _evidence(event)
    if graph is not None:
        evidence['source_entities'] = graph['entities']
    for path in rule['source'].get('absent', []):
        try:
            _path(evidence, path)
        except (KeyError, IndexError, TypeError):
            continue
        return None
    try:
        bindings = {r: _path(evidence, p) for r, p in rule['source']['bind'].items()}
        if any(not isinstance(v, str) or not v for v in bindings.values()):
            return None
        for role, kind in rule['source'].get('role_kinds', {}).items():
            if graph is None or graph['entities'][bindings[role]]['initial']['kind'] != kind:
                return None
        expected = _substitute(rule['source']['equals'], bindings)
        for path, value in expected.items():
            actual = _path(evidence, path)
            if path == 'changes':
                # Effect ordering must not depend on source entity ID spelling.
                canonical = lambda x: json.dumps(x, sort_keys=True)
                actual, value = sorted(actual,key=canonical), sorted(value,key=canonical)
            if actual != value: return None
    except (KeyError, IndexError, TypeError):
        return None
    return bindings


def project_candidates(graph, focus, event_ids, *, bank=None, profile='catalog', limit=256):
    """Return complete source-to-program derivations, before target grounding."""
    bank = load_bank() if bank is None else bank
    validate_bank(bank)
    if type(limit) is not int or limit < 1:
        raise ValueError('positive candidate limit required')
    line = {x['event_id'] for x in graph['entities'][focus]['line'] if x['participation'] == 'participant'}
    if not event_ids or event_ids != sorted(set(event_ids)) or not set(event_ids) <= line:
        raise ValueError('select an ordered, nonempty segment of the entity line')
    events = {e['id']: e for e in graph['events']}
    choices = []
    for eid in event_ids:
        event = events[eid]
        if event['frame']['actor'] != focus:
            raise ValueError('this port requires the focal acting entity')
        matches = []
        for rule in bank['rules']:
            if profile in rule['profiles']:
                bindings = _match(rule, event, graph)
                if bindings is not None:
                    matches.append((rule, bindings, event))
        if not matches:
            raise ValueError(f"no portable operation for {graph['scenario']}:{event['kind']}; source is not the reviewed rule pattern")
        choices.append(matches)
    if math.prod(map(len, choices)) > limit:
        raise ValueError('mapping derivation limit exceeded; narrow source selection')
    results = []
    for derivation in product(*choices):
        origins, roles, constraints, mapped, event_origins, applied = {}, {}, {}, {}, {}, []
        compatible = True
        for rule, bindings, event in derivation:
            target = rule['target']
            for role, eid in bindings.items():
                kind = target['roles'][role]['kind']
                if (role in origins and origins[role] != eid) or (role in roles and roles[role] != kind):
                    compatible = False
                origins[role], roles[role] = eid, kind
                constraints.setdefault(role, set()).update(target['roles'][role]['properties'])
            sid = target['id']
            if sid in mapped:
                sid = f'{sid}:{event["id"]}'
            if sid in mapped:
                raise ValueError('mapping event ID collision')
            mapped[sid] = deepcopy(target['event'])
            event_origins[sid] = dict(scenario=graph['scenario'], kind=event['kind'], event_id=event['id'],
                                     target_operation=target['event']['op'], mapping_rule=rule['id'])
            applied.append(rule['id'])
        if not compatible:
            continue
        source = dict(scenario=graph['scenario'], seed=graph['seed'], entity=focus,
            text_sha256=graph['text_sha256'], event_ids=list(event_ids),
            port_policy='declarative mapping grammar; guarded target operations',
            role_origins=origins, event_origins=event_origins,
            attribute_sources={r: dict(origin=dict(scenario=graph['scenario'], entity=e),
                entity=deepcopy(graph['entities'][e]['initial'])) for r, e in origins.items() if e in graph['entities']},
            untransferred_context=[dict(event_id=e['id'], source_contract=deepcopy(e['global_contract']),
                source_dependencies=deepcopy(e['dependencies']), source_entity_effects=deepcopy(e['effects']))
                for _, _, e in derivation],
            mapping_rules=applied, target_requirements={r: sorted(p) for r, p in constraints.items()})
        template = dict(schema='attached-event-lines-v1', roles=roles, events=mapped,
            lines=[dict(entity=r, steps=[sid for sid, e in mapped.items() if r in [v for k,v in e.items() if k != 'op']])
                   for r in roles], source=source)
        weight = math.prod(rule['weight'] for rule, _, _ in derivation)
        if not _positive(weight):
            raise ValueError('mapping weight overflow or underflow')
        results.append(dict(template=template, weight=weight, rules=applied))
    if not results:
        raise ValueError('inconsistent source role correspondence across events')
    return results


def mapping_distribution(graph, focus, event_ids, world, *, bindings=None, bank=None,
                         rule_factors=None, limit=256):
    """Infer compatible existing carriers, then normalize feasible whole mappings.

    Optional rule_factors are positive contextual multipliers (an attention
    receiver hook), not permissions. No source state is written to a carrier.
    """
    from .reusable_operations import ReusableLines
    bank = load_bank() if bank is None else bank
    factors = rule_factors or {}
    if set(factors) - {r['id'] for r in bank['rules']} or any(not _positive(v) for v in factors.values()):
        raise ValueError('positive finite factors for known mapping rules required')
    hints = bindings or {}
    projected = project_candidates(graph, focus, event_ids, bank=bank, limit=limit)
    candidates, rejected = [], []
    count = 0
    for proposal in projected:
        template = proposal['template']
        roles = template['roles']
        if set(hints)-set(roles):
            raise ValueError('unknown target binding role')
        options = []
        for role, kind in roles.items():
            props = set(template['source']['target_requirements'][role])
            possible = [eid for eid, ent in sorted(world.entities.items())
                        if ent.kind == kind and props <= ent.properties and (role not in hints or hints[role] == eid)]
            options.append(possible)
        combinations = math.prod(map(len, options))
        count += combinations
        if count > limit:
            raise ValueError('mapping binding limit exceeded; provide more role bindings')
        if not combinations:
            rejected.append(dict(rules=proposal['rules'], reason='no compatible carrier',
                roles=[r for r, opts in zip(roles, options) if not opts]))
            continue
        for values in product(*options):
            bound = dict(zip(roles, values))
            if len(set(values)) != len(values):
                rejected.append(dict(rules=proposal['rules'], bindings=bound, reason='distinct roles cannot alias'))
                continue
            clone = world.clone()
            driver = ReusableLines(clone, template, bound)
            while not driver.complete:
                available = driver.candidates(clone)
                if not available:
                    break
                driver.commit(available[0][1], '')
            if not driver.complete:
                rejected.append(dict(rules=proposal['rules'], bindings=bound, reason='target guards block program',
                    blocking={sid: driver.reasons(sid) for sid in driver.frontier()}))
                continue
            score = proposal['weight'] * math.prod(factors.get(r, 1.) for r in proposal['rules'])
            if not _positive(score):
                raise ValueError('mapping score overflow or underflow')
            candidates.append(dict(template=deepcopy(template), bindings=bound, rules=proposal['rules'], score=score))
    total = sum(c['score'] for c in candidates)
    if candidates and not _positive(total):
        raise ValueError('mapping normalization overflow')
    for candidate in candidates:
        candidate['probability'] = candidate['score']/total
    return dict(candidates=candidates, rejected=rejected)


def generate_mapped(graph, focus, event_ids, world, *, seed=0, heads=True, **options):
    """Select a complete mapping, then use existing annotated grammar generation."""
    from .reusable_operations import ReusableLines
    from .event_line_replay import replay, verify
    distribution = mapping_distribution(graph, focus, event_ids, world, **options)
    candidates = distribution['candidates']
    if not candidates:
        raise ValueError('no feasible event mapping: '+json.dumps(distribution['rejected']))
    selected = random.Random(seed).choices(candidates, weights=[c['probability'] for c in candidates])[0]
    template = deepcopy(selected['template'])
    template['source']['mapping_distribution'] = dict(
        candidates=[{k: v for k, v in c.items() if k != 'template'} for c in candidates],
        rejected=distribution['rejected'], selected_rules=selected['rules'], selected_bindings=selected['bindings'])
    row = replay(world, template, selected['bindings'], seed, heads=heads, driver_class=ReusableLines)
    verify(row, template, driver_class=ReusableLines)
    return row, dict(selected, template=template)

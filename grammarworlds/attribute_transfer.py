"""Attribute transport through reviewed operation ports and target role bindings.

Source observations are provenance, never facts about a substituted carrier.
Target grammar re-realizes linguistic attributes; target operations define effects.
"""
from copy import deepcopy
from dataclasses import asdict
import math


POLICY = 'role-bound-target-authoritative-v1'
NAMES = {
    'intent': 'intend to repair object', 'offer': 'offer help',
    'fetch': 'obtain object from supply', 'transfer': 'hand object to recipient',
    'patch_paper': 'repair paper object', 'mend_kite': 'repair kite',
}


def entity_profile(entity):
    data = asdict(entity)
    for key in ('properties', 'state'):
        data[key] = sorted(data[key])
    return data


def binding_alternatives(brief, *, limit=32):
    """Expand explicit weighted role hypotheses; never merge incompatible entities.

    Weights describe complete target-binding alternatives, not independent facts
    attached to a single carrier. Feasibility will filter each completed binding.
    """
    rows = [(deepcopy(brief), 1., {})]
    for role, hint in brief.get('roles', {}).items():
        if not isinstance(hint, dict) or 'candidates' not in hint:
            continue
        options = hint['candidates']
        if not isinstance(options, list) or not options:
            raise ValueError('role candidates must be a nonempty list')
        common = {k: deepcopy(v) for k, v in hint.items() if k != 'candidates'}
        choices, seen = [], []
        for item in options:
            if not isinstance(item, dict) or 'candidates' in item:
                raise ValueError('each role candidate must be a flat hint object')
            weight = item.get('weight', 1.)
            if type(weight) not in (int, float) or not math.isfinite(weight) or weight <= 0:
                raise ValueError('candidate weights must be positive and finite')
            value = {**common, **{k: deepcopy(v) for k, v in item.items() if k != 'weight'}}
            if value in seen:
                raise ValueError('duplicate role candidate')
            seen.append(value); choices.append((value, weight))
        total = sum(weight for _, weight in choices)
        if not math.isfinite(total):
            raise ValueError('candidate weight sum must be finite')
        if len(rows)*len(choices) > limit:
            raise ValueError('too many binding alternatives')
        expanded = []
        for previous, probability, selections in rows:
            for value, weight in choices:
                variant = deepcopy(previous)
                variant['roles'][role] = value
                expanded.append((variant, probability*weight/total,
                                 {**selections, role: deepcopy(value)}))
        rows = expanded
    return rows


def event_attributes(driver, sid):
    """Map one candidate operation, with a field-by-field transfer audit.

    Recomputed for each scene so state and ownership track earlier target events.
    The caller must still use the driver's live guards before commitment.
    """
    event = driver.events[sid]
    raw = driver.template['events'][sid]
    world = driver.world
    source = driver.template.get('source', {})
    profiles = source.get('attribute_sources', {})
    physical = world.to_dict()['entities']
    roles = {slot: value for slot, value in event.items() if slot != 'op'}
    decisions = []
    role_features = {}
    for slot, target_id in roles.items():
        role = raw[slot]
        target = physical[target_id]
        role_features[slot] = deepcopy(target)
        profile = profiles.get(role, {})
        original = profile.get('entity', {})
        changes = {}
        for key in ('id', 'noun', 'kind', 'number', 'pronoun', 'location', 'state', 'memes', 'properties'):
            if key in original:
                changes[key] = dict(source=deepcopy(original[key]), target=deepcopy(target[key]),
                    decision='use_target_value' if original[key] != target[key] else 'compatible_target_value')
        decisions.append(dict(slot=slot, role=role, target=target_id,
            origin=deepcopy(profile.get('origin')), fields=changes,
            source_only_properties=sorted(set(original.get('properties', []))-set(target['properties'])),
            unknown_source_fields=sorted(set(original)-set(target)),
            policy='recompute_from_current_target',
            missing_source_profile=not bool(profile)))
    effects = []
    for change in driver.effects(event):
        entity, destination = change.bind(world, driver.frames[sid])
        effects.append(dict(entity=entity.id, location=destination,
                            add=list(change.add), remove=list(change.remove), status='proposed'))
    attributes = dict(name=NAMES.get(event['op'], event['op'].replace('_', ' ')),
        source_kind=event['op'], occurrence=sid, scope='candidate_scene', status='proposed',
        roles=roles, state_scope='before_scene',
        expected_effects=effects, effects_scope='declared_target_operation',
        effects_complete=False, transfer_policy=POLICY)
    audit = dict(policy=POLICY, occurrence=sid, operation=event['op'], roles=decisions,
        target_role_features=role_features,
        semantic_mapping='declarative_mapping_grammar' if source.get('mapping_rules') else 'reviewed_operation_port',
        mapping_rules=deepcopy(source.get('mapping_rules', [])),
        source_context='provenance_only', target_guard_authoritative=True,
        linguistic_mapping='regenerate_from_target_typed_grammar',
        source_positions='discard_and_recompute',
        source_event=deepcopy(source.get('event_origins', {}).get(sid)),
        untransferred_context=deepcopy(source.get('untransferred_context', [])))
    return attributes, audit


def adapt_tokens(tokens, event):
    """Install the role-complete target event on freshly compiled target tokens."""
    result = []
    for attributes in tokens:
        result.append({**attributes, 'event': event})
    return tuple(result)


def position_stream(tokens, namespace):
    """Fresh target coordinates; no source text length/position is transferred."""
    from .symbolic_heads.positions import Position, SymbolicRotary
    rotary = SymbolicRotary()
    sentence = local = 0
    boundary = False
    for index, token in enumerate(tokens):
        word = token['token']
        if boundary and word not in {'”', '"', '.', '!', '?'}:
            sentence += 1
            local, boundary = 0, False
        position = Position(namespace, index, sentence, local)
        token.update(position=asdict(position), rotary=rotary.encode(position))
        local += 1
        boundary = boundary or word in {'.', '!', '?'}
    return dict(schema='joint-annotated-tokens-v1', conditioning='surface_word',
                periods=list(rotary.periods), tokens=tokens)

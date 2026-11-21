"""Sample event continuations from intact annotated memory and live target state.

Event selection is separate from conditional word/attribute sampling. Handwritten
attention factors are inspectable policy, not learned transformer heads.
"""
from collections import Counter
from copy import deepcopy
import hashlib
import json
import random

from .attribute_transfer import position_stream
from .event_line_replay import replay, verify, world_from_dict
from .reusable_operations import ReusableLines
from .story_memory import retrieve


def _key(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':'))


def _physical(world):
    # Ignore focus and history so changing narrator focus cannot disguise a loop.
    data = world.to_dict()
    return _key(dict(entities=data['entities'], flags=data['flags'], facts=data['facts']))


def _satisfied(world, goal):
    entity = world.entities[goal['entity']]
    return (goal['value'] in entity.state if goal['field'] == 'state'
            else entity.location == goal['value'])


def _prefix_template(world, event, index):
    """An explicitly supplied target event; each distinct entity is one role."""
    sid = f'prefix_{index}'
    entities = sorted(set(v for k, v in event.items() if k != 'op'))
    roles = {entity: world.entities[entity].kind for entity in entities}
    return dict(schema='attached-event-lines-v1', roles=roles, events={sid: event},
                lines=[dict(entity=entity, steps=[sid]) for entity in entities],
                source=dict(supplied_prefix=True)), {entity: entity for entity in entities}


def _outcome(world, candidate):
    clone = world.clone()
    driver = ReusableLines(clone, candidate['template'], candidate['bindings'])
    if len(driver.events) != 1:
        raise ValueError('continuation expects one event per memory candidate')
    available = driver.candidates(clone)
    if not available:
        raise ValueError('retrieved candidate is no longer feasible')
    event = next(iter(driver.events.values()))
    driver.commit(available[0][1], '')
    return event, clone


def _choices(documents, world, bank):
    result = retrieve(documents, world, bank=bank)
    grouped = {}
    for candidate in result['candidates']:
        event, after = _outcome(world, candidate)
        key = _key(event)
        # Equivalent target actions get one vote, irrespective of donor count or
        # how many synonymous mapping rules happen to have been authored.
        if key not in grouped:
            grouped[key] = dict(candidate=candidate, event=event, after=after,
                                references=[], mapping_rules=[], base_weight=candidate['score'])
        group = grouped[key]
        group['references'].extend(candidate['references'])
        group['mapping_rules'].extend(candidate['rules'])
        if candidate['score'] > group['base_weight']:
            group['candidate'] = candidate
        group['base_weight'] = max(group['base_weight'], candidate['score'])
    for group in grouped.values():
        group['references'] = list({_key(r): r for r in group['references']}.values())
        group['mapping_rules'] = sorted(set(group['mapping_rules']))
    return list(grouped.values()), len(result['rejected'])


def continue_story(documents, world, *, prefix=(), goals=None, seed=0, max_events=12,
                   policy='contextual', heads=True, bank=None):
    """Generate a prefix and at most max_events sampled continuations.

    goals are predicates {entity, field: state|location, value}, never an event
    plan. With goals=None, repair intents in the supplied prefix imply repaired
    state. An explicit [] opts out. A sampled STOP does not assert resolution.
    The input world and source documents are never changed.
    """
    if policy not in {'plain', 'contextual'} or type(max_events) is not int or max_events < 0:
        raise ValueError('known policy and nonnegative integer event limit required')
    documents = list(documents)
    prefix = list(prefix)
    current = world.clone()
    goals = deepcopy(goals) if goals is not None else [
        dict(entity=e['item'], field='state', value='repaired') for e in prefix if e['op'] == 'intent']
    for goal in goals:
        if (set(goal) != {'entity', 'field', 'value'} or goal['entity'] not in current.entities
                or goal['field'] not in {'state', 'location'} or not isinstance(goal['value'], str)):
            raise ValueError('goals require an existing entity and state/location predicate')
    rng = random.Random(seed)
    word_rng = random.Random(f'words:{seed}')
    segments, decisions, event_counts = [], [], Counter()
    seen = Counter({_physical(current): 1})
    last_event = None
    state_progress = False

    def commit(template, bindings):
        nonlocal current
        row = replay(current, template, bindings, word_rng.getrandbits(64),
                     heads=heads, driver_class=ReusableLines)
        verify(row, template, driver_class=ReusableLines)
        if row['status'] != 'complete':
            raise ValueError('prefix or continuation is blocked: '+str(row['blocked']))
        segments.append(row)
        current = world_from_dict(row['final_world'], allow_history=True)
        return row

    for index, event in enumerate(prefix):
        template, bindings = _prefix_template(current, event, index)
        commit(template, bindings)
        last_event = event
        event_counts[_key(event)] += 1
        seen[_physical(current)] += 1

    status = 'limit'
    for step in range(max_events):
        choices, rejected = _choices(documents, current, bank)
        before_goals = [_satisfied(current, g) for g in goals]
        # A final placement should not be rewarded (or protected from reversal)
        # while a requested transformation of that same object is unfinished.
        active_goals = [g['field'] != 'location' or not any(
            other['entity'] == g['entity'] and other['field'] == 'state' and not done
            for other, done in zip(goals, before_goals)) for g in goals]
        all_done = bool(goals) and all(before_goals)
        scored = []
        for choice in choices:
            event, after = choice['event'], choice['after']
            after_goals = [_satisfied(after, g) for g in goals]
            progress = sum(int(after) - int(before) for before, after, active
                           in zip(before_goals, after_goals, active_goals) if active)
            semantic_change = any(e.state != after.entities[i].state or e.memes != after.entities[i].memes
                                  for i, e in current.entities.items())
            factors = {}
            if policy == 'contextual':
                factors['state_progress'] = 6. if semantic_change else 1.
                factors['goal_progress'] = 20. if progress > 0 else (.02 if progress < 0 else 1.)
                factors['repeated_action'] = .1 ** min(event_counts[_key(event)], 6)
                factors['revisited_world'] = .05 if seen[_physical(after)] else 1.
                factors['actor_continuity'] = 2. if last_event and event['actor'] == last_event['actor'] else 1.
                # A shallow affordance lookahead, not a prescribed chain: ask
                # whether this move makes any unsatisfied goal directly doable.
                if goals and not all_done and not semantic_change:
                    following, _ = _choices(documents, after, bank)
                    enables = any(any(active and not done and _satisfied(n['after'], goal)
                                      for goal, done, active in zip(goals, before_goals, active_goals))
                                  for n in following)
                    factors['enables_goal'] = 8. if enables else 1.
            weight = choice['base_weight']
            for factor in factors.values(): weight *= factor
            scored.append(dict(event=event, mapping_rules=choice['mapping_rules'],
                references=choice['references'], base_weight=choice['base_weight'],
                factors=factors, weight=weight))
        mass = sum(c['weight'] for c in scored)
        if not choices:
            stop_weight = 1.
        elif policy == 'plain':
            stop_weight = .5
        elif all_done:
            stop_weight = max(1., 8 * mass)
        elif goals:
            stop_weight = .02  # Still possible to abandon an unresolved goal.
        else:
            stop_weight = max(.1, mass * (.5 if state_progress else .02))
        scored.append(dict(event=dict(op='STOP'), weight=stop_weight, factors={}))
        total = mass + stop_weight
        for c in scored: c['probability'] = c['weight'] / total
        selected = rng.choices(range(len(scored)), weights=[c['weight'] for c in scored])[0]
        decisions.append(dict(step=step, candidates=scored, selected=selected,
                              rejected_mappings=rejected, goals_satisfied=before_goals,
                              active_goals=active_goals))
        if selected == len(choices):
            status = 'exhausted' if not choices else 'sampled_stop'
            break
        choice = choices[selected]
        template = deepcopy(choice['candidate']['template'])
        template['source']['memory_retrieval'] = dict(references=choice['references'],
            mapping_rules=choice['mapping_rules'], selection='sampled_continuation')
        state_progress |= any(e.state != choice['after'].entities[i].state
                              for i, e in current.entities.items())
        commit(template, choice['candidate']['bindings'])
        last_event = choice['event']
        event_counts[_key(last_event)] += 1
        seen[_physical(current)] += 1

    # Flatten without losing per-scene attribute tables or cross-event positions.
    traces, tokens, counts = [], [], Counter()
    for segment in segments:
        offset = len(traces)
        for token in segment['attribute_generation']['tokens']:
            token = deepcopy(token); token['scene_index'] += offset
            tokens.append(token)
        traces.extend(deepcopy(segment['trace']))
        counts.update(segment['metrics'])
    namespace = hashlib.sha256(_key(dict(seed=seed, initial=world.to_dict(), prefix=prefix,
                                         goals=goals, policy=policy, max_events=max_events)).encode()).hexdigest()
    return dict(schema='memory-continuation-v1', seed=seed, policy=policy, status=status,
        story=' '.join(s['story'] for s in segments), initial_world=world.to_dict(),
        final_world=current.to_dict(), prefix=deepcopy(prefix), goals=goals,
        goals_satisfied=[_satisfied(current, g) for g in goals],
        decisions=decisions, segments=segments, trace=traces, metrics=dict(counts),
        attribute_generation=position_stream(tokens, namespace))

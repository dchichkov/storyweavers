"""Derive named prose slots and their guards from executed world evidence.

The model writes only text. It never duplicates scene IDs, guard constructors,
JSON pointers, or the generator wrapper. Coverage is sampled, not a proof of
every reachable state; an unseen state fails closed in the existing renderer.
"""
from copy import deepcopy
import hashlib
import json

from runtime import StoryError
from prose import lint


def signature(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, ensure_ascii=False).encode()).hexdigest()[:12]


def varying(states):
    keys = set().union(*(s.keys() for s in states))
    return sorted(k for k in keys if len({json.dumps(s.get(k), sort_keys=True) for s in states}) > 1)


def scaffold(traces, specs, variants=1):
    if not traces: raise StoryError('Cannot scaffold prose without validated traces')
    if variants not in (1,2): raise StoryError('Use one or two prose variants')
    scenes = {s.id: s for spec in specs for s in spec.scenes}
    slots = {}
    opening_keys = varying([t['initial'] for t in traces])
    # The author already identifies the consequences worth narrating. Incidental
    # beliefs, locations and leftover preparation must not multiply ending prose.
    ending_keys = sorted({k for spec in specs for k in spec.outcome_keys})

    def add(section, state, keys, *, event=None, role='beat'):
        if section == 'scenes':
            definition = scenes[event['scene']]
            before_keys = sorted({c.key for c in definition.requires} |
                                 {e.value for e in definition.effects if e.op == 'copy'} |
                                 {e.key for e in definition.effects})
            after_keys = sorted({e.key for e in definition.effects})
            guards = [dict(at='before', key=k, op='eq', value=event['before'][k]) for k in before_keys]
            guards += [dict(at='after', key=k, op='eq', value=event['after'][k]) for k in after_keys]
            prefix = 'scene.' + event['scene']
            evidence = dict(summary=event['summary'], actors=event['actors'],
                            changes=event['changes'], before={k:event['before'][k] for k in before_keys})
        else:
            guards = [dict(at='initial' if section == 'openings' else 'after', key=k, op='eq', value=state[k]) for k in keys]
            prefix = section[:-1]
            evidence = dict(state=state)
        key = prefix + '.' + signature(guards)
        item = dict(section=section, scene=event['scene'] if event else None, role=role,
                    when=guards, evidence=evidence, variants=1 if section == 'scenes' else variants)
        if key in slots and slots[key] != item:
            if section == 'endings':
                # Supply only facts true in every trace represented by this
                # ending. Do not give one representative trace's incidental
                # possessions or motives as if they held across the whole group.
                common=slots[key]['evidence']['state']
                item['evidence']['state']={k:v for k,v in common.items() if k in state and state[k]==v}
            else:
                raise StoryError(f'Conflicting evidence for prose slot {key}')
        slots[key] = item

    for trace in traces:
        add('openings', trace['initial'], opening_keys)
        for event in trace['events']:
            s = scenes[event['scene']]
            role = 'bridge' if not s.pivotal and s.kernel in {'Observe','Tell','Transfer','Move'} else 'beat'
            add('scenes', event['after'], (), event=event, role=role)
        add('endings', trace['final'], ending_keys)
    if len(slots) > 120:
        raise StoryError(f'Too many prose cases ({len(slots)}); simplify causally irrelevant variation')
    return dict(slots=slots, unselected_scenes=sorted(set(scenes) - {e['scene'] for t in traces for e in t['events']}))


def response_schema(skeleton):
    props = {key: dict(type='array', items={'type':'string'}, minItems=item['variants'], maxItems=item['variants'])
             for key,item in skeleton['slots'].items()}
    return dict(type='object', properties={'cards':dict(type='object',properties=props,
                required=list(props),additionalProperties=False)},required=['cards'],additionalProperties=False)


def validate_texts(skeleton, texts):
    if not isinstance(texts, dict) or set(texts) != {'cards'} or not isinstance(texts['cards'], dict):
        raise StoryError('Expected {cards: {slot_id: [text, ...]}}')
    expected, got = set(skeleton['slots']), set(texts['cards'])
    if got != expected:
        raise StoryError(f'Prose slot mismatch: missing {sorted(expected-got)}, unknown {sorted(got-expected)}')
    for key,item in skeleton['slots'].items():
        cards = texts['cards'][key]
        if not isinstance(cards,list) or len(cards) != item['variants']:
            raise StoryError(f'{key}: expected {item["variants"]} text variants')
        for text in cards:
            if not isinstance(text,str) or not text.strip() or len(text)>4000:
                raise StoryError(f'{key}: invalid prose text')
            # Name expansion is handled by the existing renderer; raw enums and
            # arbitrary interpolation are unnecessary in this text-only protocol.
            checked = text
            import re
            checked = re.sub(r'\{name:[A-Za-z][A-Za-z0-9_]*\}', 'Name', checked)
            defects = lint(checked)
            if defects: raise StoryError(f'{key}: {defects}: {text[:150]}')


def catalog(skeleton, texts):
    validate_texts(skeleton, texts)
    book = dict(openings=[], scenes=[], endings=[], lexicon=[])
    sections = {}
    for key,item in skeleton['slots'].items():
        cards = [dict(text=text,when=deepcopy(item['when'])) for text in texts['cards'][key]]
        if item['section'] == 'scenes':
            sid = item['scene']
            sections.setdefault(sid,dict(scene=sid,role=item['role'],variants=[]))['variants'] += cards
        else:
            book[item['section']] += cards
    book['scenes'] = list(sections.values())
    return book


def patch_texts(skeleton, texts, patch):
    """Only named existing cards, with a text precondition to reject stale edits."""
    if not isinstance(patch,dict) or set(patch) != {'edits'} or not isinstance(patch['edits'],list):
        raise StoryError('Expected a named edits list')
    if not 1 <= len(patch['edits']) <= 8 or len(json.dumps(patch)) > 16000:
        raise StoryError('Text repair exceeds patch budget')
    updated = deepcopy(texts)
    seen = set()
    for edit in patch['edits']:
        if set(edit) != {'id','old','new'}: raise StoryError('Card edits require id, old, new')
        key = edit['id']
        if key not in skeleton['slots'] or key in seen: raise StoryError('Unknown or duplicate card ID: '+key)
        seen.add(key)
        if updated['cards'].get(key) != edit['old']:
            raise StoryError('Stale card edit: '+key)
        updated['cards'][key] = deepcopy(edit['new'])
    validate_texts(skeleton,updated)
    return updated

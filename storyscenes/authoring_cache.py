"""Authoring-only prompt layout and lossless evidence compaction.

The runtime never imports this module. Cache only stable instructions; changing
worlds remain outside the breakpoint. Saved requests are actual API JSON, while
sdk_kwargs adapts the newer cache field for the installed older SDK.
"""
from copy import deepcopy

from runtime import StoryError
import compact_prose as cp
from api_requests import compact, cached_request


def preflight(document):
    """Report simultaneous structural mistakes in one bounded repair message.

    This never changes a definition or guesses a physical binding. The compiler
    remains authoritative; these are early diagnostics for common paid loops.
    """
    import algebra as a
    if not isinstance(document, dict):return
    kernels=document.get('kernels', {})
    if not isinstance(kernels, dict):return
    composites=set(a.SHARED_KERNELS)|set(kernels)
    problems=[]
    for name in set(kernels)&(set(a.SHARED_KERNELS)|set(a.BUILTINS)):
        problems.append(f'kernels.{name}: reserved; remove this definition with value:null and use the library operation')
    groups=[('compose',document.get('compose'))]
    groups += [('kernels.'+name+'.body',k.get('body')) for name,k in kernels.items() if isinstance(k,dict)]
    for path,group in groups:
        if not isinstance(group,dict):continue
        for name,node in group.items():
            if not isinstance(node,dict):continue
            if node.get('op') in composites:
                extras=set(node)-{'op','args','divide'}
                if extras:
                    problems.append(f'{path}.{name}: composite call only accepts op,args,divide; remove {sorted(extras)} from the call, moving needed guards/turns into atomic body nodes')
            maps=[node.get(k,{}) for k in ('set','inc','copy')]
            if all(isinstance(v,dict) for v in maps):
                duplicates=(set(maps[0])&set(maps[1]))|(set(maps[0])&set(maps[2]))|(set(maps[1])&set(maps[2]))
                if duplicates:problems.append(f'{path}.{name}: conflicting simultaneous effects for {sorted(duplicates)}; write each key once')
    if problems:
        raise StoryError('Structural errors (fix together):\n'+'\n'.join(problems[:12]))


def aliases(skeleton):
    return {f'c{i}': key for i, key in enumerate(skeleton['slots'])}


def prose_payload(document, skeleton, previews):
    """Experimental compact payload with evidence and explicit card conditions.

    Conditions deliberately repeat facts after a quality regression. State common to all
    openings is still only an INITIAL fact; it is never a fact of every scene.
    """
    common = {}
    for section in ('openings', 'endings'):
        states = [slot['evidence']['state'] for slot in skeleton['slots'].values()
                  if slot['section'] == section]
        common[section] = {k: v for k, v in states[0].items()
                           if all(k in s and s[k] == v for s in states)} if states else {}
    cards = []
    opening_states=[s['evidence']['state'] for s in skeleton['slots'].values() if s['section']=='openings']
    variable_keys=set(cp.varying(opening_states)) if opening_states else set()
    for alias, key in aliases(skeleton).items():
        slot = skeleton['slots'][key]
        if slot['variants'] != 1:
            raise StoryError('Economical authoring requires one wording per slot')
        evidence = deepcopy(slot['evidence'])
        if 'state' in evidence:
            evidence['state'] = {k: v for k, v in evidence['state'].items()
                                 if k not in common[slot['section']]}
        item=dict(id=alias, section=slot['section'], role=slot['role'],
                  scene=slot['scene'], conditions=deepcopy(slot['when']), evidence=evidence)
        if slot['section']=='scenes':
            grounded=set(evidence.get('before',{}))|set(evidence.get('changes',{}))
            item['varying_unstated']=sorted(variable_keys-grounded)
        cards.append(item)
    return dict(title=document['title'], premise=document.get('premise', ''),
                entities={key: {k: ent[k] for k in ('name', 'kind')}
                          for key, ent in document['entities'].items()},
                common_boundary_facts=common, cards=cards,
                preview_paths=[[e['scene'] for e in row['trace']['events']] for row in previews])


def text_schema():
    # No per-world enums, hashed property names, or variable schema bounds.
    item = dict(type='object', properties={'id': {'type': 'string'}, 'text': {'type': 'string'}},
                required=['id', 'text'], additionalProperties=False)
    return dict(type='object', properties={'cards': {'type': 'array', 'items': item}},
                required=['cards'], additionalProperties=False)


def expand_texts(skeleton, response, *, validate=True):
    if not isinstance(response, dict) or set(response) != {'cards'} or not isinstance(response['cards'], list):
        raise StoryError('Expected {cards:[{id,text}]}')
    mapping, cards = aliases(skeleton), {}
    for item in response['cards']:
        if not isinstance(item, dict) or set(item) != {'id', 'text'} or not isinstance(item['id'], str):
            raise StoryError('Every card requires id and text')
        key = mapping.get(item['id'])
        if key is None or key in cards:
            raise StoryError('Unknown or duplicate card ID: ' + item['id'])
        cards[key] = [item['text']]
    result = {'cards': cards}
    if set(cards) != set(skeleton['slots']):
        raise StoryError('Missing prose card IDs')
    if validate:
        cp.validate_texts(skeleton, result)
    return result


def short_texts(skeleton, texts):
    return {alias: texts['cards'][key][0] for alias, key in aliases(skeleton).items()}


def expand_patch(skeleton, patch):
    mapping = aliases(skeleton)
    if not isinstance(patch, dict) or set(patch) != {'edits'} or not isinstance(patch['edits'], list):
        raise StoryError('Expected {edits:[{id,old,new}]}')
    edits = []
    for edit in patch['edits']:
        if not isinstance(edit, dict) or set(edit) != {'id', 'old', 'new'} or not isinstance(edit['id'], str):
            raise StoryError('Every text edit requires id, old, new')
        if edit['id'] not in mapping or any(not isinstance(edit[k], str) for k in ('old', 'new')):
            raise StoryError('Unknown card or non-string replacement')
        edits.append(dict(id=mapping[edit['id']], old=[edit['old']], new=[edit['new']]))
    return {'edits': edits}

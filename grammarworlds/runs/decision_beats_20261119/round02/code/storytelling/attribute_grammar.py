"""Compile typed grammar candidates into joint word/attribute alternatives.

No completed surface, sampled future frame, or post-event state is read. Every
attribute is a property of a candidate construction or the current physical world.
"""
from copy import deepcopy

from .semantic_rules import metadata


PUNCTUATION = {'.', ',', ';', '!', '?', '“', '”'}


def _pos(word, labels, context):
    lower = word.lower()
    if context.get('authored_pos'):
        return context['authored_pos']
    if word in PUNCTUATION:
        return 'PUNCT'
    if context.get('lexical_role') == 'finite':
        if lower == 'not':
            return 'PART'
        return 'AUX' if lower in {'did', 'do', 'does', 'can', 'could', 'is', 'am', 'are', 'was', 'were'} else 'VERB'
    if context.get('lexical_role') == 'infinitive':
        return 'VERB'
    if lower in {'a', 'an', 'the'}:
        return 'DET'
    if 'gf.UsePron' in labels:
        return 'PRON'
    if 'gf.UsePN' in labels:
        return 'PROPN'
    if context.get('lexical_role') == 'preposition':
        return 'ADP'
    if lower in {'and', 'but', 'or'}:
        return 'CCONJ'
    if lower == 'because':
        return 'SCONJ'
    if lower in {'to', 'not'}:
        return 'PART'
    if lower == 'that' and 'gf.ComplVS' in labels:
        return 'SCONJ'
    # Flattened indefinite/genitive constructions retain phrase-level labels;
    # use typed nominal metadata to distinguish their adjective terminals.
    nominal = context.get('nominal', {})
    if lower in {w.lower() for adj in nominal.get('modifiers', []) for w in adj.split()}:
        return 'ADJ'
    if 'gf.UseN' in labels or 'noun.surface' in labels:
        return 'NOUN'
    if 'lexical.adjective' in labels:
        return 'ADJ'
    if 'lexical.adverb' in labels:
        return 'ADV'
    if lower in {'said', 'says', 'told', 'tells'} and any(x.startswith('dialogue.speaker:') for x in labels):
        return 'VERB'
    if lower in {'i', 'me', 'you', 'he', 'she', 'it', 'we', 'they'}:
        return 'PRON'
    if lower == "i'll":
        return 'PRON+AUX'
    if lower in {'one', 'two', 'three', 'four'}:
        return 'NUM'
    if lower in {'would', 'can', 'could'}:
        return 'AUX'
    if lower in {'like', 'let', 'promise', 'using'}:
        return 'VERB'
    return 'X'


def _resolve(description, speaker, listener):
    if isinstance(description, list):
        return [_resolve(x, speaker, listener) for x in description]
    if not isinstance(description, dict):
        return description
    result = {k: _resolve(v, speaker, listener) for k, v in description.items()}
    if result.get('type') == 'pronoun':
        form = result.get('form')
        entity = speaker if form in {'i', 'me', 'my'} else listener if form in {'you', 'your'} else None
        if entity:
            result['entity'] = entity
    return result


def expand_attributes(node, context=None, path=()):
    """Same order/weights/rule lists as expand(), plus scoped terminal metadata."""
    context = dict(context or {})
    info = metadata(node)
    for key in ('clause', 'nominal', 'modifier', 'beat'):
        if key in info:
            context[key] = info[key]
    if 'clause' in info:
        context['action'] = info['clause']['predicate']
        context['action_scope'] = 'finite_clause'
    # Explicit construction scopes override the generic finite-clause defaults.
    for key in ('authored_pos','entity','lexical_role','lexical_lemma','syntax_role',
                'action','action_scope','hypothetical','evidence_event','annotation_status',
                'speech_act','narrative_role','narrative_detail','dialogue_contract'):
        if key in info:context[key]=info[key]
    path = path + (node.label,)
    if node.label.startswith(('referent:', 'scoped_referent:')):
        context['entity'] = node.label.split(':', 1)[1]
    if node.label == 'gf.finite':
        context['lexical_role'] = 'finite'
    if node.label == 'gf.infVP' and len(node.children) == 2:
        context['hypothetical'] = context.get('hypothetical', False) or context.get('action', {}).get('modality') in {'intention', 'ability', 'attempt'}
        action = metadata(node.children[1]).get('vp')
        if action:
            context['action'] = action
        context['action_scope'] = 'embedded_action'
    if node.kind == 'text':
        yield node.children, 1., (), tuple((path, context) for _ in node.children)
        return
    if node.kind == 'choice':
        total = sum(node.weights)
        for child, weight in zip(node.children, node.weights):
            for words, probability, rules, attrs in expand_attributes(child, context, path):
                yield words, weight / total * probability, (node.label,) + rules, attrs
        return
    rows = [((), 1., (node.label,), ())]
    for i, child in enumerate(node.children):
        local = dict(context)
        if node.label in {'gf.UseCl', 'expanded.polite_desire', 'expanded.tentative_offer'}:
            local['syntax_role'] = 'subject' if i == 0 else 'predicate'
        if node.label == 'gf.infVP' and i == 0:
            local['lexical_role'] = 'infinitive'
        if node.label == 'expanded.to_recipient':
            local['syntax_role'] = 'object' if i == 0 else 'recipient' if i == 2 else 'predicate'
            if i == 1:
                local['lexical_role'] = 'preposition'
        if node.label == 'local.PrepNP':
            local['syntax_role'] = 'oblique'
            if i == 0:
                local['lexical_role'] = 'preposition'
        if node.label in {'gf.ComplV2', 'gf.ComplV3', 'gf.ComplV2V'}:
            if node.children[0].label == 'gf.finite':
                if i == 1 and node.label == 'gf.ComplV2':
                    local['syntax_role'] = 'object'
            elif node.label == 'gf.ComplV3':
                local['syntax_role'] = 'recipient' if i == 0 else 'object'
            elif node.label == 'gf.ComplV2V' and i == 0:
                local['syntax_role'] = 'object'
        branches = list(expand_attributes(child, local, path))
        rows = [(left + right, p*q, lr+rr, la+ra)
                for left, p, lr, la in rows for right, q, rr, ra in branches]
    yield from rows


def candidate_attributes(tokens, annotations, frame, world, kernel=None, physical=None):
    """One correlated bundle per terminal, derived from one candidate parse."""
    event = dict(name=frame.kind.replace('_', ' '), source_kind=frame.kind,
                 scope='candidate_scene', status='proposed',
                 roles={key: getattr(frame, key) for key in ('actor', 'patient', 'instrument', 'destination')
                        if getattr(frame, key)}, causes=list(frame.cause_ids),
                 tags=list(kernel.query) if kernel else [])
    physical = world.to_dict()['entities'] if physical is None else physical
    quoted = False
    result = []
    for word, (labels, context) in zip(tokens, annotations):
        if word == '“':
            quoted = True
        speaker = next((x.split(':', 1)[1] for x in reversed(labels) if x.startswith('dialogue.speaker:')), None)
        listener = next((x.split(':', 2)[2] for x in reversed(labels) if x.startswith('dialogue.listener:')), None)
        clause = _resolve(deepcopy(context.get('clause', {})), speaker if quoted else None, listener if quoted else None)
        action = _resolve(deepcopy(context.get('action', {})), speaker if quoted else None, listener if quoted else None)
        entity = context.get('entity')
        if not entity and quoted and 'gf.UsePron' in labels:
            entity = speaker if word.lower() in {'i', 'me', 'my'} else listener if word.lower() in {'you', 'your'} else None
        if entity and entity not in physical:
            raise ValueError(f'ungrounded candidate entity {entity}')
        scope = context.get('action_scope', 'scene_context')
        status = ('negated' if clause.get('polarity') == 'negative' else
                  'hypothetical' if context.get('hypothetical') else
                  'reported' if quoted else 'narrated_candidate')
        pos = _pos(word, labels, context)
        result.append(dict(pos=pos, syntax_role=context.get('syntax_role'),
            entity=entity, entity_features=deepcopy(physical[entity]) if entity else None,
            state_scope='before_scene', nominal=context.get('nominal'),
            clause=clause or None, action=action or None, action_scope=scope,
            assertion=status, quoted=quoted, speaker=speaker, listener=listener,
            modifier=context.get('modifier'), event=event,
            unresolved=[key for key, value in (('pos', pos != 'X'), ('entity', bool(entity)),
                                               ('clause', bool(clause))) if not value]))
        if 'beat' in context:result[-1]['beat']=deepcopy(context['beat'])
        for key in ('lexical_lemma','evidence_event','annotation_status','speech_act','narrative_role','narrative_detail','dialogue_contract'):
            if key in context:result[-1][key]=context[key]
        if 'hypothetical' in context:result[-1]['hypothetical']=context['hypothetical']
        if word == '”':
            quoted = False
    return tuple(result)

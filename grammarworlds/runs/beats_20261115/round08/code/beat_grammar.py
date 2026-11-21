"""Authored semantic grammar for the optional beat vocabulary.

These annotations describe a construction selected by ID, not an analysis of
arbitrary English. Surface words and grammar weights are preserved. Requests
and proposals scope their embedded action hypothetically; saying it does not
execute it. A beat's enclosing native event is a separate semantic level.
"""
from copy import deepcopy
from dataclasses import replace

from .grammar import Node,expand,text
from .storytelling.semantic_rules import metadata,tagged


PUNCTUATION={'.',',',';','!','?','“','”'}
LEXICON={
    'hesitated':('VERB','hesitate'),'hesitates':('VERB','hesitate'),
    'looked':('VERB','look'),'looks':('VERB','look'),'closely':('ADV',None),'at':('ADP',None),
    'said':('VERB','say'),'says':('VERB','say'),'could':('AUX','can'),
    'you':('PRON',None),'help':('VERB','help'),'me':('PRON',None),'with':('ADP',None),
    'i':('PRON',None),'will':('AUX','will'),'try':('VERB','try'),
    'give':('VERB','give'),
    'another':('DET',None),'way':('NOUN',None),'let':('VERB','let'),'us':('PRON',None),
    'the':('DET',None),'a':('DET',None),'dent':('NOUN',None),
    'had':('AUX','have'),'has':('AUX','have'),'become':('VERB','become'),
    'thumb':('NOUN',None),'rest':('NOUN',None),'was':('AUX','be'),'is':('AUX','be'),
    'gone':('ADJ',None),'smooth':('ADJ',None),'now':('ADV',None),
    'still':('ADV',None),'stiff':('ADJ',None),'hand':('NOUN',None),
    'wheel':('NOUN',None),'that':('PRON',None),'locked':('VERB','lock'),
    'turned':('VERB','turn'),'turns':('VERB','turn'),'freely':('ADV',None),
    'no':('PART',None),'longer':('ADV',None),'rattled':('VERB','rattle'),'rattles':('VERB','rattle'),
    'this':('DET',None),'time':('NOUN',None),'stayed':('VERB','stay'),'stays':('VERB','stay'),
    'small':('ADJ',None),'shadow':('NOUN',None),'wanted':('VERB','want'),
}


def _entity(entity):return dict(type='entity',entity=entity)


def _clause(subject,lemma,tense,*,modality='plain',arguments=None,polarity='positive',**extra):
    return dict(subject=subject,predicate=dict(lemma=lemma,modality=modality,
        arguments=arguments or {},**extra),tense=tense,polarity=polarity)


def _context(clause,scope='optional_beat',hypothetical=False):
    return dict(clause=clause,action=clause['predicate'],action_scope=scope,hypothetical=hypothetical)


def annotate_phrase(node, terminal_attributes, **context):
    """Attach exact authored token attributes to a deterministic phrase.

    Entries are dictionaries with `token` and `pos`, and optional entity,
    syntax_role, clause, action, action_scope or hypothetical overrides. This
    escape hatch lets new detail constructors author semantics compositionally
    without extending a text parser. Alternatives need annotations on each
    phrase before they are joined into a choice.
    """
    branches=list(expand(node))
    if len(branches)!=1:raise ValueError('annotate each deterministic phrase before making alternatives')
    words=branches[0][0];specs=list(terminal_attributes)
    if tuple(x.get('token') for x in specs)!=words:
        raise ValueError('authored terminal attributes do not match phrase tokens')
    if any(not x.get('pos') for x in specs):raise ValueError('every terminal needs an authored POS')
    cursor=iter(specs)
    def visit(n):
        if n.kind=='text':
            children=[]
            for word in n.children:
                spec=deepcopy(next(cursor));spec.pop('token');pos=spec.pop('pos')
                children.append(tagged(Node('text',n.label,(word,)),**{**metadata(n),**context,**spec,'authored_pos':pos}))
            return children[0] if len(children)==1 else replace(n,kind='sequence',children=tuple(children))
        return replace(n,children=tuple(visit(c) for c in n.children))
    return visit(node)


def _echo_clause(candidate,words,tense):
    name=(candidate.get('detail') or '').rsplit(':',1)[-1]
    obj=candidate['object'];subject=_entity(obj)
    if name=='dent':
        subject=dict(type='nominal',lemma='dent',owner=_entity(obj))
        if 'become' in words:return _clause(subject,'become',tense,modality='state',complement='thumb_rest')
        return _clause(subject,'be',tense,modality='state',complement='gone' if 'gone' in words else 'smooth')
    if name=='grip':return _clause(subject,'have',tense,modality='state',arguments={'object':dict(type='nominal',lemma='hand',modifiers=['stiff'])})
    if name=='locked_wheel':return _clause(subject,'turn',tense,modality='state')
    if name=='rattle':return _clause(subject,'rattle',tense,modality='state',polarity='negative')
    if name=='moving_light':return _clause(subject,'stay',tense,modality='state',complement='still')
    if name=='large_shadow':return _clause(subject,'be',tense,modality='state',complement='small')
    return None


def _callback_clause(callback,obj,tense):
    """Meanings of authored callback predicates, independent of their wording."""
    predicate=callback['predicate'];subject=_entity(obj)
    states={'be_repaired':'repaired','be_free':'free','be_safe':'safe','be_clear':'clear'}
    if predicate in states:return _clause(subject,'be',tense,modality='state',complement=states[predicate])
    if predicate=='be_found':return _clause(subject,'be',tense,modality='state',complement='missing',polarity='negative')
    if predicate=='not_bend':return _clause(subject,'bend',tense,modality='state',polarity='negative')
    if predicate=='have_correct_weight':return _clause(subject,'have',tense,modality='state',arguments={'object':dict(type='nominal',lemma='weight',modifiers=['right'])})
    if predicate=='be_safe_to_wear':return _clause(subject,'be',tense,modality='state',complement='safe',arguments={'action':dict(lemma='wear',modality='possibility',arguments={'object':_entity(obj)})})
    return None


def annotate_beat(node,candidate,world,tense='past'):
    """Annotate an existing optional construction without resampling its words.

    Unknown constructions retain grounded reference metadata and explicit X
    tags for unauthored words. They never acquire a guessed action. New echoes
    can supply `detail_realization` accepted by :func:`annotate_phrase`.
    """
    if tense not in {'past','present'}:raise ValueError('unknown beat tense')
    if candidate['id']=='immediate':return node
    hero=candidate['experiencer'];obj=candidate['object'];listener=candidate.get('listener')
    for entity in (hero,obj,listener):
        if entity is not None and entity not in world.entities:raise ValueError('unbound beat participant: '+entity)
    realization=candidate.get('detail_realization')
    if realization and 'terminal_attributes' in realization:
        def validate(value):
            if isinstance(value,dict):
                entity=value.get('entity')
                if isinstance(entity,str) and entity not in world.entities:raise ValueError('unbound detail reference: '+entity)
                for child in value.values():validate(child)
            elif isinstance(value,list):
                for child in value:validate(child)
        validate(realization)
        data=deepcopy(realization);terminals=data.pop('terminal_attributes')
        return annotate_phrase(node,terminals,**data)
    kind=candidate['id'];speech=kind in {'asking','committing','suggesting'}
    if speech and listener is None:raise ValueError('speech beat needs a grounded listener')
    callback=candidate.get('detail_callback')
    callback_tokens=None
    if callback:
        tail=next(expand(text(callback[tense])))[0];positions=callback[tense+'_pos']
        branches=list(expand(node))
        if len(branches)!=1 or not tail or tuple(branches[0][0][-len(tail):])!=tail or len(tail)!=len(positions):
            raise ValueError('callback words/POS do not match the authored phrase')
        callback_tokens=iter(zip(tail,positions))
    words={w.lower() for tokens,_,_ in expand(node) for w in tokens}
    mention_ids=[]
    def refs(n):
        if n.label.startswith(('referent:','scoped_referent:')):
            e=n.label.split(':',1)[1]
            if e not in mention_ids:mention_ids.append(e)
        for child in n.children:
            if isinstance(child,Node):refs(child)
    refs(node)
    target=next((e for e in mention_ids if e not in {hero,listener}),None)
    if kind=='reaction':clause=_clause(_entity(hero),'hesitate',tense)
    elif kind=='inspection':clause=_clause(_entity(hero),'look',tense,arguments={'oblique':_entity(obj)},modifiers=[dict(preposition='at',object=_entity(obj)),dict(adverb='closely')])
    elif speech:clause=_clause(_entity(hero),'say',tense,arguments={'listener':_entity(listener),'reported_clause':True})
    else:clause=(_callback_clause(callback,obj,tense) if callback else
                 _echo_clause(candidate,words,tense) if kind.startswith('echo:') else None)
    outer=_context(clause,'detail_recollection' if kind.startswith('echo:') else 'optional_beat') if clause else dict(annotation_status='unresolved_construction')
    if kind=='asking':
        quoted=_context(_clause(_entity(listener),'help','present',modality='request',
            arguments={'object':_entity(hero),'oblique':_entity(obj)}),'requested_action',True)
    elif kind=='committing':
        proposal=candidate.get('proposal')
        arguments=({'object':_entity(proposal['object']),'recipient':_entity(proposal['recipient'])} if proposal else
                   {'object':_entity(target)} if target else {'manner':dict(type='nominal',lemma='way',modifiers=['another'])})
        quoted=_context(_clause(_entity(hero),proposal['lemma'] if proposal else 'try','future',modality='intention',
            arguments=arguments),'proposed_action',True)
    elif kind=='suggesting':
        group=dict(type='coordination',members=[_entity(hero),_entity(listener)])
        proposed=_clause(group,'try','future',modality='proposal',
            arguments={'object':_entity(target)} if target else {'manner':dict(type='nominal',lemma='way',modifiers=['another'])})
        quoted=_context(_clause(_entity(listener),'let','present',modality='proposal',
            arguments={'object':group,'action':proposed['predicate']}),'proposed_action',True)
    else:quoted={}
    echo_name=(candidate.get('detail') or '').rsplit(':',1)[-1]
    def visit(n,context,reference=None,in_quote=False):
        context={**context,**metadata(n)}
        if n.label.startswith(('referent:','scoped_referent:')):
            reference=n.label.split(':',1)[1]
            if reference not in world.entities:raise ValueError('unbound beat reference: '+reference)
        if n.label=='beat.utterance':context={**context,**quoted};in_quote=True
        if n.kind=='text':
            leaves=[]
            for word in n.children:
                lower=word.lower();attrs=dict(context)
                explicit_pos=None
                if callback_tokens is not None and reference is None:
                    expected,explicit_pos=next(callback_tokens)
                    if expected!=word:raise ValueError('callback terminal order differs from its authored phrase')
                if in_quote and kind=='suggesting' and lower=='try' and not reference:
                    attrs.update(_context(proposed,'embedded_proposal',True))
                if echo_name=='locked_wheel' and lower in {'that','had','locked'} and not reference:
                    attrs.update(_context(_clause(_entity(obj),'lock','past'),'detail_setup'))
                    attrs['evidence_event']=candidate.get('setup_event')
                if echo_name=='large_shadow' and (reference==hero or lower in {'had','wanted'}):
                    attrs.update(_context(_clause(_entity(hero),'want','past',modality='intention',
                        arguments={'object':_entity(obj)}),'detail_setup'))
                    attrs['evidence_event']=candidate.get('setup_event')
                if word in PUNCTUATION:pos,lemma='PUNCT',None
                elif reference:
                    pos,lemma=('DET' if lower in {'the','a','an'} else 'PROPN' if world.entities[reference].kind=='person' else 'NOUN'),None
                    attrs.update(entity=reference,nominal=_entity(reference))
                    subject=attrs.get('clause',{}).get('subject',{})
                    attrs['syntax_role']='subject' if subject.get('entity')==reference else 'oblique' if kind=='inspection' else 'object'
                else:
                    pos,lemma=LEXICON.get(lower,('X',None)) if clause else ('X',None)
                if explicit_pos:pos=explicit_pos
                if echo_name=='grip' and lower in {'had','has'} and not reference:pos,lemma='VERB','have'
                if echo_name=='moving_light' and lower=='still' and not reference:pos='ADJ'
                if echo_name=='large_shadow' and lower=='this' and not reference:pos='PRON'
                attrs['authored_pos']=pos
                if pos=='X':attrs['annotation_status']='unresolved_vocabulary'
                if lemma:attrs['lexical_lemma']=lemma
                if pos in {'VERB','AUX'}:attrs.update(lexical_role='finite',syntax_role='predicate')
                elif pos=='ADP':attrs.update(lexical_role='preposition',syntax_role='oblique')
                elif pos=='ADV':attrs.update(lexical_role='adverb',syntax_role='modifier')
                if in_quote and lower in {'i','me','you'} and not reference:
                    attrs['entity']=listener if lower=='you' else hero
                    attrs['nominal']=_entity(attrs['entity'])
                    attrs['syntax_role']='subject' if lower in {'i','you'} else 'object'
                    if lower=='you' and candidate.get('proposal',{}).get('lemma')=='give':attrs['syntax_role']='recipient'
                if in_quote and lower=='us' and not reference:
                    attrs['nominal']=dict(type='coordination',members=[_entity(hero),_entity(listener)])
                    attrs['syntax_role']='object';attrs.pop('entity',None)
                if callback and callback['predicate']=='be_safe_to_wear' and lower in {'to','wear'} and not reference:
                    attrs.update(action=clause['predicate']['arguments']['action'],
                                 action_scope='embedded_possibility',hypothetical=True)
                # Quotation punctuation and speaker attribution are deliberately
                # outside the hypothetical action's scope.
                leaves.append(tagged(Node('text',n.label,(word,)),**attrs))
            return leaves[0] if len(leaves)==1 else replace(n,kind='sequence',children=tuple(leaves))
        return replace(n,children=tuple(visit(child,context,reference,in_quote) for child in n.children))
    return visit(node,outer)

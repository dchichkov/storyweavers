"""Authored clause/speech fragments compiled before word sampling.

Templates are grammar terminals with explicit physical reference slots. They
are never a postprocessor over generated text. Unknown lexical POS stays X;
clause/event meanings are authored, not inferred from arbitrary English.
"""
import re
from ...grammar import Node,seq,choice,text
from ..semantic_rules import tagged


def clause(actor,lemma,*forms,object=None,role='action',hypothetical=False,**arguments):
    if object:arguments['object']=dict(type='entity',entity=object)
    return dict(kind='clause',actor=actor,lemma=lemma,forms=list(forms),role=role,
                hypothetical=hypothetical,arguments=arguments)


def speech(speaker,listener,act,*forms,lemma='say',object=None,hypothetical=False,**arguments):
    return dict(kind='speech',speaker=speaker,listener=listener,act=act,
                content=clause(speaker,lemma,*forms,object=object,role='dialogue',
                               hypothetical=hypothetical,**arguments))


def alternatives(*nodes,weights=None):
    return dict(kind='alternatives',nodes=list(nodes),weights=weights or [1]*len(nodes))


def sequence(*nodes):return dict(kind='sequence',nodes=list(nodes))


def _literal(value):
    # Explicit quote glyphs are meaningful terminals; the old text() helper
    # intentionally strips them for legacy data.
    parts=re.split('([“”])',value)
    return seq('crafted.words',*(Node('text','quote',tuple(p)) if p in {'“','”'} else text(p)
                                  for p in parts if p))


def phrase(form,w,context):
    parts=[];cursor=0
    for match in re.finditer(r'\{([a-zA-Z_][a-zA-Z_0-9]*)(?::(name|the|a|poss|pronoun))?\}',form):
        parts.append(_literal(form[cursor:match.start()]));entity,mode=match.groups();mode=mode or 'name'
        if entity not in w.entities:raise ValueError('unbound authored reference '+entity)
        e=w.entities[entity];value=e.noun
        if mode=='the':value='the '+value
        elif mode=='a':value=('an ' if value[:1].lower() in 'aeiou' else 'a ')+value
        elif mode=='poss':value+= "'s"
        elif mode=='pronoun':value=e.pronoun
        pos='PRON' if mode=='pronoun' else 'PROPN' if e.kind=='person' else 'NOUN'
        parts.append(tagged(seq('referent:'+entity,text(value)),entity=entity,
            nominal=dict(type='entity',entity=entity),lexical_role='entity',authored_pos=pos))
        cursor=match.end()
    parts.append(_literal(form[cursor:]))
    return tagged(seq('crafted.phrase',*parts),**context)


def render(node,w):
    kind=node['kind']
    if kind=='sequence':return seq('crafted.sequence',*(render(x,w) for x in node['nodes']))
    if kind=='alternatives':return choice('crafted.alternatives',*(render(x,w) for x in node['nodes']),weights=tuple(node['weights']))
    if kind=='speech':
        speaker,listener=node['speaker'],node['listener']
        if speaker not in w.entities or w.entities[speaker].kind!='person':raise ValueError('speaker is not a person')
        if listener not in w.entities or w.entities[listener].kind!='person':raise ValueError('listener is not a person')
        if w.entities[speaker].location!=w.entities[listener].location:raise ValueError('speaker/listener not together')
        content=render(node['content'],w)
        return seq('dialogue.listener:'+speaker+':'+listener,
            seq('dialogue.speaker:'+speaker,
                phrase('{'+speaker+'} said,',w,dict(clause=dict(subject=dict(type='entity',entity=speaker),
                    predicate=dict(lemma='say',arguments={'listener':dict(type='entity',entity=listener)}),tense='past',polarity='positive'))),
                Node('text','quote.open',('“',)),content,Node('text','quote.close',('”',))))
    if kind!='clause':raise ValueError('unknown crafted grammar constructor')
    if node['actor'] not in w.entities:raise ValueError('clause needs physical subject')
    predicate=dict(lemma=node['lemma'],arguments=node['arguments'])
    context=dict(clause=dict(subject=dict(type='entity',entity=node['actor']),predicate=predicate,
                            tense='past',polarity='positive'),hypothetical=node['hypothetical'],
                 action_scope='authored_clause',annotation_status='authored_clause')
    return choice('crafted.clause.'+node['role'],*(phrase(f,w,context) for f in node['forms']))

"""Weighted titles and story boundaries, sampled as annotated words.

This is a presentation grammar over a completed generation result, not physical
events. Openings read the initial world; titles may read the final world. Nothing
is committed to the native trace or passed off as a new observed event.
"""
import random
import re

from .grammar import Derivation
from .storytelling.attribute_sampler import AttributeForest
from .storytelling.surface import detokenize
from .world import Frame


def _tokens(text):
    return tuple(re.findall(r"\w+(?:['’]\w+)*|[^\w\s]", text))


def _object_noun(entity,result):
    """Use the same authored number forms as the source noun grammar."""
    noun=entity['noun']
    if entity.get('number')!='plural' or entity['kind']=='person':return noun
    from .portable.language import load_lexicon
    from .portable.morphology import plural
    from .storytelling.seed_worlds.engine import NAMES,pack
    entry=load_lexicon()['nouns'].get(noun,{})
    # Seed packs author plural surface nouns (e.g. blue ribbons) explicitly.
    # Joined results retain their donor scenarios in units/transfer options.
    sources=[]
    for row in result.get('rows',[result]):
        sources.append(row.get('scenario'))
        sources.extend(u['scenario'] for u in row.get('options',{}).get('transfer',{}).get('units',[]))
    sources.extend(u['scenario'] for u in result.get('units',[]))
    for source in dict.fromkeys(sources):
        if source in NAMES and noun in pack(source).LEXICON.get('nouns',{}):
            entry={**entry,**pack(source).LEXICON['nouns'][noun]}
    return noun if entry.get('mass') else entry.get('plural',plural(noun))


def _alternative(style, weight, *parts, entities=(), source_event=None):
    """Parts are literal text or (text, entity ID) grounded nominal phrases."""
    tokens=[];refs=[]
    for part in parts:
        words,entity=part if isinstance(part,tuple) else (part,None)
        chunk=_tokens(words);tokens.extend(chunk);refs.extend([entity]*len(chunk))
    return dict(style=style,weight=weight,tokens=tuple(tokens),references=refs,
                entities=list(entities),source_event=source_event)


def _sample(role, alternatives, seed, carrier, scope, forced=None):
    if forced is not None:
        alternatives=[a for a in alternatives if a['style']==forced]
        if not alternatives:raise ValueError(f'unavailable {role} style: {forced}')
    total=sum(a['weight'] for a in alternatives)
    derivations=[];annotations=[];endings=[]
    for a in alternatives:
        context=dict(narration_role=role,style=a['style'],carrier=carrier,
                     evidence_scope=scope,referents=a['entities'],source_event=a['source_event'])
        if role in {'opening','closing'}:context[role+'_style']=a['style']
        derivations.append(Derivation(a['tokens'],a['weight']/total,
            Frame('presentation:'+role+':'+a['style'],carrier),('presentation.'+role+'.'+a['style'],)))
        # Phrase roles and references are authored. Do not guess POS for words
        # in arbitrary multiword entity names or silently assert physical facts.
        annotations.append(tuple(dict(context,entity=entity,
            pos='PUNCT' if word in '.,;!?' else 'X',assertion='narrative_framing')
            for word,entity in zip(a['tokens'],a['references'])))
        endings.append(dict(context,pos='END',entity=None,assertion='narrative_framing'))
    forest=AttributeForest(derivations,{},annotations,end_annotations=endings)
    rng=random.Random(f'presentation-v1:{seed}:{role}');trace=[]
    while not forest.complete:
        prediction=forest.predict(forest.prefix);choices=prediction['choices']
        selected=rng.choices(choices,weights=[c['probability'] for c in choices])[0]
        posterior=forest.observe(selected['word'],prediction)
        prediction.update(selected=selected['word'],selected_probability=selected['probability'],
                          selected_attributes=posterior)
        trace.append(prediction)
    styles={a['style'] for a in alternatives if a['tokens']==forest.prefix}
    return dict(text=detokenize(forest.prefix),styles=sorted(styles),trace=trace,
                attributes=forest.attribute_table,
                alternatives=[dict(style=a['style'],text=detokenize(a['tokens']),
                                   probability=a['weight']/total) for a in alternatives])


def _context(result, scenes):
    """Read native evidence; source completion is not executable-plot success."""
    final=result['final_world'];plot=result.get('plot')
    if plot is not None:
        initial=result['rows'][0]['initial_world']
        ending=plot['stages'][-1].get('evidence') if plot.get('stages') else None
        return dict(initial=initial,final=final,hero=plot['carrier'],
            bindings=plot['bindings'],gift=plot['kind']=='adapt_gift',
            complete=plot['status']=='achieved',completion_basis='executable_plot',
            final_image=bool(ending and ending['event']==scenes[-1]['event_id']),
            tense=result.get('tense',result['rows'][0].get('tense','past')))
    initial=result['initial_world'];hero=initial['hero']
    crafted=final.get('narrative',{}).get('storycraft')
    if crafted is not None:
        last=crafted['history'][-1] if crafted['history'] else {}
        return dict(initial=initial,final=final,hero=hero,bindings={'object':initial.get('target')},
            gift=False,complete=crafted['completed'],completion_basis='crafted_obligations',
            final_image=last.get('function') in {'final_image','payoff'} and last.get('event')==scenes[-1]['event_id'],
            tense=result.get('tense','past'),authored_title=crafted['title'])
    # A joined fragment can end because its import unit ended. Its enclosing
    # receiving plot remains authoritative, even when this row has no `plot`.
    receiving=final.get('narrative',{}).get('plot_execution')
    complete=(receiving['status']=='achieved' if receiving else 'ended' in final['flags'])
    from .plot_bank import BANK
    from .event_scale_bank import BANK as SCALES
    source=BANK.get(result['scenario'],{})
    reading=source.get('events',{}).get(scenes[-1]['frame']['kind'],{})
    bindings={'object':initial.get('target')}
    recipients=source.get('roles',{}).get('recipient',[])
    if len(recipients)==1:bindings['recipient']=recipients[0]
    obj=bindings.get('object');recipient=bindings.get('recipient')
    # Ownership transfer does not imply a gift (an apple order is a purchase).
    # Use the authored story purpose. A completed gift may sit on the recipient's
    # table instead of being held, so direct containment is not its definition.
    gift=bool(complete and 'gift' in SCALES.get(result['scenario'],{}).get('tags',[])
              and obj in final['entities'] and recipient in final['entities'])
    return dict(initial=initial,final=final,hero=hero,bindings=bindings,gift=gift,
        complete=complete,completion_basis='receiving_plot' if receiving else 'native_ended_flag',
        final_image=reading.get('role')=='final_image',tense=result.get('tense','past'))


def present(result, *, seed=None, title_style=None, opening_style=None, closing_style=None):
    """Return a display copy of a source row or joined plot result.

    `story` is framed in this display copy. Native scenes, tokens and their hash
    still describe `raw_story`; use :func:`add_presentation` when passing a row
    onward to QA, annotation or replay.

    Optional styles condition the grammar before word sampling. Independent RNG
    streams make presentation reproducible without changing any event choice.
    Empty immediate/final-image forms reuse the first/last native scene, rather
    than repeating it. No weather, repeated habits or future happiness is added.
    """
    output=dict(result)
    output.pop('presented_story',None)
    body=result.get('raw_story',result['story'])
    output['raw_story']=body
    rows=result.get('rows',[result])
    scenes=[s for row in rows for s in row['scenes'] if s['text']]
    if not body.strip() or not scenes:
        output.pop('title',None)
        output.update(story=body,presentation=dict(schema='story-presentation-v2',status='no_narrative',
                                                  body_offset=0,body_length=len(body)))
        return output
    context=_context(result,scenes)
    initial=context['initial'];final=context['final'];hero=context['hero']
    name=initial['entities'][hero]['noun']
    initial_entities=initial['entities'];final_entities=final['entities']
    seed=result.get('seed',0) if seed is None else seed
    titles=[_alternative('hero',1,'The Tale of',(name,hero),entities=[hero])]
    if context.get('authored_title'):
        titles.append(_alternative('authored',1,context['authored_title'],entities=[hero]))
        title_style=title_style or 'authored'
        opening_style=opening_style or 'immediate'
    obj=context['bindings'].get('object')
    if obj in final_entities:
        noun=_object_noun(final_entities[obj],result)
        # Title casing applies to the common object phrase, not personal names.
        titles += [_alternative('object',2,'The',(noun.title(),obj),entities=[obj]),
                   _alternative('hero_and_object',3,(name,hero),'and the',(noun.title(),obj),entities=[hero,obj])]
    recipient=context['bindings'].get('recipient')
    if context['gift'] and recipient in final_entities:
        titles.append(_alternative('gift',3,'A Gift for',(final_entities[recipient]['noun'],recipient),entities=[recipient]))
    openings=[_alternative('storyteller',1,'This is a story about',(name,hero),'.',entities=[hero]),
              _alternative('immediate',1,source_event=scenes[0]['event_id'])]
    location=initial_entities[hero]['location'];past=context['tense']=='past'
    if location in initial_entities and initial_entities[location]['kind']=='place':
        place=initial_entities[location]['noun']
        if past:
            for style,weight,lead in [('traditional',4,'Once upon a time,'),('everyday',3,'One day,')]:
                openings.append(_alternative(style,weight,lead,(name,hero),'was at the',
                    (place,location),'.',entities=[hero,location]))
        else:
            openings.append(_alternative('everyday',3,(name,hero),'is at the',
                                         (place,location),'.',entities=[hero,location]))
    elif past:
        # A place claim needs a named physical location. Identity alone is safe.
        openings.append(_alternative('traditional',4,'Once upon a time, there was someone named',
                                     (name,hero),'.',entities=[hero]))
    complete=context['complete']
    if complete:
        closings=[_alternative('the_end',5,'The End.'),
                  _alternative('storyteller',2,'And that is where this story ends.')]
        if context['final_image']:
            closings.append(_alternative('final_image',2,source_event=scenes[-1]['event_id']))
    else:
        closings=[_alternative('continued',3,'To be continued.'),
                  _alternative('unfinished',1,'The story is not over yet.')]
    presentation=dict(schema='story-presentation-v2',status='complete' if complete else 'unfinished',seed=seed,
                      completion_basis=context['completion_basis'],body_length=len(body))
    for role,options,scope,forced in [
        ('title',titles,'final_world',title_style),
        ('opening',openings,'initial_world',opening_style),
        ('closing',closings,'completed_narration' if complete else 'incomplete_narration',closing_style)]:
        presentation[role]=_sample(role,options,seed,hero,scope,forced)
    opening=presentation['opening']['text'];closing=presentation['closing']['text']
    prefix=presentation['title']['text']+'\n\n'+(opening+'\n\n' if opening else '')
    presentation['body_offset']=len(prefix)
    output.update(title=presentation['title']['text'],story=prefix+body+('\n\n'+closing if closing else ''),
                  presentation=presentation)
    return output


def add_presentation(row, **options):
    """Attach framing while keeping `story` and all evidence offsets unchanged.

    `presented_story` is for readers. `presentation.body_offset` translates raw
    character offsets into that display text. Calling this twice is idempotent.
    """
    framed=present(row,**options)
    result=dict(row)
    result.update(raw_story=framed['raw_story'],presented_story=framed['story'],
                  presentation=framed['presentation'])
    if 'title' in framed:result['title']=framed['title']
    else:result.pop('title',None)
    return result

"""Reading checks grounded in selected beats and locally visible earlier text.

A proposal is evidence of an utterance, not of success. Body offsets remain
raw-text offsets; presentation_evidence maps them explicitly for framed views.
"""
from hashlib import sha256


def _evidence(scene, text=None):
    text=scene['text'] if text is None else text
    return dict(start=scene['start'],end=scene['start']+len(text),text=text)


def questions(row):
    story=row['story']
    if sha256(story.encode()).hexdigest()!=row['text_sha256']:
        raise ValueError('story changed; regenerate beat alignment')
    world=row['final_world'];entities=world['entities']
    memory=world.get('narrative',{}).get('beats',{})
    history={e['id']:e for e in world['history']}
    scenes={s['event_id']:s for s in row['scenes']}
    if len(scenes)!=len(row['scenes']):raise ValueError('ambiguous beat scene evidence')
    for scene in scenes.values():
        event=history.get(scene['event_id'])
        if (not event or not event.get('narrated') or event['sentence']!=scene['text']
                or story[scene['start']:scene['end']]!=scene['text']):
            raise ValueError('beat scene is not aligned narrated evidence')
    results=[];seen=set()
    for beat in memory.get('history',[]):
        if beat['event'] not in scenes:continue
        event=history[beat['event']];decision=event.get('beat_decision',{})
        selected=[c for c in decision.get('candidates',[]) if c['id']==decision.get('selected')]
        if len(selected)!=1 or selected[0]['id']=='immediate':
            raise ValueError('beat has no unique selected decision')
        expected=dict(selected[0],event=event['id'],scope='executed_pre_event_beat')
        if beat!=expected:raise ValueError('beat memory differs from selected decision')
        if event['id'] in seen:raise ValueError('duplicate selected beat')
        seen.add(event['id'])
        anchor=beat['preceding_event'];entity_ids={beat['experiencer'],beat['object']}
        if not entity_ids<=entities.keys():raise ValueError('unbound beat QA participant')
        actor=beat['actor_name'];obj=beat['object_name']
        if beat['detail']:
            detail=memory['details'].get(beat['detail'])
            if (not detail or detail['entity']!=beat['object']
                    or detail['setup_event']!=beat.get('setup_event')):
                raise ValueError('beat QA detail binding changed')
            anchor=detail['setup_event'];kind='detail_payoff'
            referent=obj if entities[beat['object']]['kind']=='person' else 'the '+obj
            question=f'Which earlier detail about {referent} does this later moment recall?'
        elif beat['speech_act']=='asking':
            kind='beat_dialogue';question=f'What did {actor} ask for after the setback?'
            entity_ids.add(beat['listener'])
        elif beat['speech_act'] in {'committing','suggesting'}:
            kind='beat_dialogue';question=f'What did {actor} propose before continuing?'
            entity_ids.add(beat['listener'])
            anchor=beat.get('discovery_event',anchor)
        elif beat['id']=='inspection':
            kind='beat_reaction';question=f'What did {actor} inspect after the setback?'
        elif beat['id']=='reaction':
            kind='beat_reaction';question=f'How did {actor} react before continuing?'
        else:continue
        if not entity_ids<=entities.keys():raise ValueError('unbound beat QA listener')
        if anchor not in history or anchor>=event['id'] or not history[anchor].get('narrated'):
            raise ValueError('missing or future beat QA anchor')
        # A resumed segment cannot answer questions about text outside itself.
        if anchor not in scenes:continue
        current=scenes[beat['event']];earlier=scenes[anchor]
        if earlier['end']>current['start']:
            raise ValueError('beat QA anchor is not earlier text')
        if not beat['text'] or not current['text'].startswith(beat['text']):
            raise ValueError('beat surface does not match its trace')
        # Quote the selected utterance/reaction exactly. This preserves tense
        # and does not assert that a request was answered or a plan succeeded.
        results.append(dict(id=f"{row['scenario']}:{beat['event']}:beat_{beat['id']}",kind=kind,
            question=question,answer=earlier['text']+' '+beat['text'],
            entity_ids=sorted(entity_ids),event_ids=[anchor,beat['event']],
            evidence=[_evidence(earlier),_evidence(current,beat['text'])],text_sha256=row['text_sha256']))
    return results


def presentation_evidence(row, question):
    """Return explicit display offsets without changing the raw QA contract."""
    story=row['story'];presentation=row.get('presentation',{})
    display=row.get('presented_story',story);offset=presentation.get('body_offset',0)
    if (sha256(story.encode()).hexdigest()!=question['text_sha256']
            or display[offset:offset+len(story)]!=story):
        raise ValueError('presentation is not aligned with QA body')
    evidence=[]
    for item in question['evidence']:
        if story[item['start']:item['end']]!=item['text']:
            raise ValueError('QA evidence changed')
        evidence.append(dict(item,start=item['start']+offset,end=item['end']+offset))
    return evidence

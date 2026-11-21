"""Reading checks for actually selected beats and visibly supported reminders."""


def questions(row):
    memory=row['final_world'].get('narrative',{}).get('beats',{})
    scenes={s['event_id']:s for s in row['scenes']}
    results=[]
    for beat in memory.get('history',[]):
        if beat['event'] not in scenes:continue
        anchor=beat['preceding_event'];entity_ids={beat['experiencer'],beat['object']}
        actor=beat['actor_name'];obj=beat['object_name'];listener=beat['listener_name']
        if beat['detail']:
            detail=memory['details'][beat['detail']];anchor=detail['setup_event']
            entity_ids.add(detail['entity']);kind='detail_payoff'
            question='Which earlier detail does this later moment bring back?'
            answer=beat['text']
        elif beat['speech_act']=='asking':
            kind='beat_dialogue';question=f'What did {actor} ask for after the setback?'
            answer=f'{actor} asked {listener} for help with the {obj}.'
            entity_ids.add(beat['listener'])
        elif beat['speech_act'] in {'committing','suggesting'}:
            kind='beat_dialogue';question=f'What did {actor} propose before continuing?'
            answer=beat['text'];entity_ids.add(beat['listener'])
        elif beat['id']=='inspection':
            kind='beat_reaction';question=f'What did {actor} inspect after the setback?'
            answer=f'{actor} looked closely at the {obj}.'
        elif beat['id']=='reaction':
            kind='beat_reaction';question=f'How did {actor} react before continuing?'
            answer=f'{actor} hesitated before continuing.'
        else:continue
        # A resumed segment cannot answer questions about text outside itself.
        if anchor not in scenes:continue
        current=scenes[beat['event']];earlier=scenes[anchor]
        if not current['text'].startswith(beat['text']):raise ValueError('beat surface does not match its trace')
        evidence=sorted([earlier,current],key=lambda s:s['start'])
        results.append(dict(id=f"{row['scenario']}:{beat['event']}:beat_{beat['id']}",kind=kind,
            question=question,answer=earlier['text']+' '+answer,
            entity_ids=sorted(entity_ids),event_ids=[s['event_id'] for s in evidence],
            evidence=[{k:s[k] for k in ('start','end','text')} for s in evidence],text_sha256=row['text_sha256']))
    return results

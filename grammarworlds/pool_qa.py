"""Small trace-grounded diagnostics for imported rabbit fragments, not prose QA."""


def questions(row):
    history=row['final_world']['history'];entities=row['final_world']['entities'];qa=[]
    def named(eid):return entities[eid]['noun']
    def add(kind,question,answer,events,ids):
        qa.append(dict(kind=kind,question=question,answer=answer,
                       event_ids=[e['id'] for e in events],entity_ids=sorted(set(ids))))
    for event in history:
        op=event.get('operation');r=event.get('bound_roles',{})
        if op=='failed_portal':
            recovery=next((e for e in history if e['id']>event['id'] and e.get('operation')=='untie_hat'
                           and e['bound_roles']['hat']==r['hat']),None)
            if recovery:
                add('cause',f"Why did {named(r['actor'])}'s first attempt fail?",
                    f"The {named(r['hat'])} was tied shut. {named(r['actor'])} untied the ribbon before trying again.",
                    [event,recovery],[r['actor'],r['hat'],recovery['bound_roles']['ribbon']])
        if op in {'portal_rabbit','hide_rabbit'}:
            if op=='portal_rabbit':
                answer=(f"{named(r['actor'])} used the wand and the magical hat to transport the {named(r['rabbit'])} from the {named(r['source'])}. "
                        f"The same rabbit moved inside the {named(r['hat'])}; no new rabbit was created.")
                ids=[r[k] for k in ('actor','rabbit','hat','source','wand')]
            else:
                answer=(f"{named(r['actor'])} placed the {named(r['rabbit'])} inside the {named(r['hat'])}. "
                        f"{named(r['audience'])} had closed their eyes while the rabbit was hidden.")
                ids=[r[k] for k in ('actor','rabbit','hat','audience')]
            add('mechanism',f"How did the {named(r['rabbit'])} get inside the hat?",answer,[event],ids)
        if op=='rabbit_final_image':
            add('outcome',f"Where was the {named(r['rabbit'])} at the end?",
                f"The {named(r['rabbit'])} was on the {named(r['stage'])}, beside the open {named(r['hat'])}. "
                f"It nibbled the {named(r['food'])} and was no longer hungry.",
                [event],[r[k] for k in ('rabbit','hat','stage','food')])
    return qa

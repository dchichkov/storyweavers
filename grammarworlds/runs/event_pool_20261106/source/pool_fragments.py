"""Authored, role-factored event fragments. No character IDs occur in programs."""
from copy import deepcopy

from .catalog_attachment import catalog
from .world import Entity


def entity_pool():
    records = catalog()
    prototypes = {
        'performer': Entity('performer', 'Merlin', 'person', '', pronoun='he',
                            properties={'can_hold', 'can_portal', 'can_help'}, memes={'Care':.8}),
        'audience': Entity('audience', 'June', 'person', '', pronoun='she',
                           properties={'can_hold'}, memes={'Curiosity':.8}),
        'rabbit': Entity('rabbit', 'rabbit', 'animal', '', properties={'rabbit','portable','calm'}, state={'hungry'}),
        'hat': Entity('hat', "magician's hat", 'object', '', properties={'hat','portable','portal_hat','rabbit_capacity'}, state={'bound'}),
        'stage_hat': Entity('stage_hat', 'top hat', 'object', '', properties={'hat','portable','rabbit_capacity'}, state={'open'}),
        'wand': Entity('wand', 'wand', 'tool', '', properties={'portal_focus','portable'}),
        'ribbon': Entity('ribbon', 'ribbon', 'object', '', properties={'tie'}, state={'tied'}),
        'stage': Entity('stage', 'table', 'place', '', properties={'reachable'}),
        'source': Entity('source', 'hutch', 'place', '', properties={'reachable'}),
        'food': Entity('food', 'carrot', 'food', '', properties={'edible','rabbit_food','portable'}),
    }
    for key,e in prototypes.items():
        records['magic:'+key] = dict(entity=e, source={'world':'authored_hat','entity':key},
            additions=[],links={},packages=['authored_hat:portal'] if key=='hat' else [])
    return records


def role(kind, prototype, *, props=(), location='@setting', **extra):
    return dict(kind=kind, prototype=prototype, properties=list(props), location=location, **extra)


RABBIT_ROLES = {
    'actor':role('person','magic:performer',props=('can_hold',)),
    'audience':role('person','magic:audience'),
    'rabbit':role('animal','magic:rabbit',props=('rabbit','calm'),location='source'),
    'hat':role('object','magic:hat',props=('hat','rabbit_capacity'),location='stage'),
    'stage':role('place','magic:stage',props=('reachable',), from_location='hat'),
    'source':role('place','magic:source',props=('reachable',), from_location='rabbit'),
    'food':role('food','magic:food',props=('rabbit_food',),location='stage'),
}
MAGIC_ROLES = deepcopy(RABBIT_ROLES)
MAGIC_ROLES['actor']['properties'].append('can_portal')
MAGIC_ROLES['hat']['properties'].append('portal_hat')
MAGIC_ROLES['wand']=role('tool','magic:wand',props=('portal_focus',),location='actor')
CLOSED_ROLES=deepcopy(MAGIC_ROLES)
CLOSED_ROLES['hat']['state']=['bound']
CLOSED_ROLES['ribbon']=role('object','magic:ribbon',props=('tie',),location='hat',state=['tied'])
OPEN_ROLES=deepcopy(MAGIC_ROLES)
OPEN_ROLES['hat']['state']=['open'];OPEN_ROLES['hat']['exclude_state']=['bound']
STAGE_ROLES=deepcopy(RABBIT_ROLES)
STAGE_ROLES['hat'].update(prototype='magic:stage_hat',state=['open'],exclude_state=['bound'])


def event(op, **roles):
    return dict(op=op, **roles)


def call(fragment, **bindings):
    return dict(fragment=fragment, bind=bindings)


# Subfragments expose only the roles they use. Root stories compose them with
# explicit variable substitution; they are not stored English continuations.
FRAGMENTS = {
    'show.setup': dict(params=['actor','audience','rabbit','hat','source','stage'],steps=[
        event('show_premise',actor='actor',audience='audience',rabbit='rabbit',source='source'),
        event('take_hat',actor='actor',hat='hat',stage='stage'),
        event('promise_show',actor='actor',audience='audience',hat='hat')]),
    'hat.unbind': dict(params=['actor','audience','rabbit','hat','wand','ribbon','source'],steps=[
        event('failed_portal',actor='actor',rabbit='rabbit',hat='hat',wand='wand',source='source'),
        event('notice_binding',actor='audience',hat='hat',ribbon='ribbon'),
        event('untie_hat',actor='actor',hat='hat',ribbon='ribbon')]),
    'rabbit.arrive_magic': dict(params=['actor','rabbit','hat','wand','source'],steps=[
        event('portal_rabbit',actor='actor',rabbit='rabbit',hat='hat',wand='wand',source='source')]),
    'rabbit.arrive_stage': dict(params=['actor','audience','rabbit','hat','source'],steps=[
        event('close_eyes',actor='audience'),
        event('hide_rabbit',actor='actor',audience='audience',rabbit='rabbit',hat='hat',source='source'),
        event('open_eyes',actor='audience')]),
    'rabbit.reveal': dict(params=['actor','audience','rabbit','hat'],steps=[
        event('peek_rabbit',actor='actor',audience='audience',rabbit='rabbit',hat='hat'),
        event('lift_rabbit',actor='actor',audience='audience',rabbit='rabbit',hat='hat'),
        event('applaud_reveal',actor='audience',rabbit='rabbit',holder='actor')]),
    'rabbit.care_ending': dict(params=['actor','rabbit','hat','food','stage'],steps=[
        event('settle_rabbit',actor='actor',rabbit='rabbit',hat='hat',stage='stage'),
        event('feed_rabbit',actor='actor',rabbit='rabbit',food='food',stage='stage'),
        event('rabbit_final_image',actor='actor',rabbit='rabbit',hat='hat',food='food',stage='stage')]),
}


def use(key):
    return call(key, **{p:p for p in FRAGMENTS[key]['params']})


ROOTS = {
    'hat.portal_bound':dict(intent='reveal',anchors=['rabbit','hat'],roles=CLOSED_ROLES,
        tags=['magic','obstacle','recovery','gentle'],weight=3,source='authored_hat:Merlin_bound_hat',
        steps=[use('show.setup'),use('hat.unbind'),use('rabbit.arrive_magic'),use('rabbit.reveal'),use('rabbit.care_ending')]),
    'hat.portal_open':dict(intent='reveal',anchors=['rabbit','hat'],roles=OPEN_ROLES,
        tags=['magic','gentle'],weight=1,source='authored_hat:open_hat_variant',
        steps=[use('show.setup'),use('rabbit.arrive_magic'),use('rabbit.reveal'),use('rabbit.care_ending')]),
    'hat.stage':dict(intent='reveal',anchors=['rabbit','hat'],roles=STAGE_ROLES,
        tags=['stage','gentle'],weight=2,source='authored_hat:stage_variant',
        steps=[use('show.setup'),use('rabbit.arrive_stage'),use('rabbit.reveal'),use('rabbit.care_ending')]),
    'kite.recover_flight':dict(intent='fly',anchors=['item'],tags=['repair','outdoors'],weight=1,
        source='kite:mend+test_flight portable export',roles={
            'actor':role('person','kite:hero',props=('can_repair','can_hold')),
            'item':role('object','kite:target',props=('physics:kite',),state=['torn']),
            'tool':role('tool','kite:tool',props=('repair',)),
            'tether':role('object','kite:string',props=('tie',),location='actor'),
            'sky':role('place','magic:stage',props=('airspace',),construct='sky')},
        steps=[event('premise',actor='actor',item='item'),event('wish_flight',actor='actor',item='item'),
               event('mend_kite',actor='actor',item='item',tool='tool'),
               event('fly_kite',actor='actor',item='item',tool='tether',destination='sky')]),
    'library.moon_picture':dict(intent='draw',anchors=['item'],tags=['picture','quiet'],weight=1,
        source='library:sketch_moon portable export',roles={
            'actor':role('person','library:hero',props=('can_sketch_moon',)),
            'item':role('object','library:paper',props=('drawable',),state=['blank'],location='actor'),
            'tool':role('tool','library:pencil',props=('draw',),location='actor'),
            'reference':role('object','library:atlas',props=('moon_reference',),location='actor')},
        steps=[event('sketch_moon',actor='actor',item='item',tool='tool',reference='reference')]),
}

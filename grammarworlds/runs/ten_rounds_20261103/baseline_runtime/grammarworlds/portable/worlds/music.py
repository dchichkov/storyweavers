"""World semantics extracted unchanged from the saved Terra music pack.

Source: runs/authoring_music_20261103/terra/round1/pack.py.
Only the realization is replaced with typed shared rules; frozen evidence stays untouched.
"""
from dataclasses import asdict
import random

from grammarworlds.world import Entity, Fact, Frame, World, kernel


class MusicWorld(World):
    def facts_for_attention(self):
        facts = list(self.facts.values())
        for entity_id in ('hero', 'partner', 'teacher'):
            person = self.entities[entity_id]
            for name, value in sorted(person.memes.items()):
                facts.append(Fact(
                    entity_id + '.' + name,
                    person.noun + ' has ' + name.lower() + ' at ' + format(value, '.2f') + '.',
                    ('person', entity_id, name.lower()), float(value)))
        for entity_id in ('drum', 'spare', 'program'):
            item = self.entities[entity_id]
            facts.append(Fact(
                entity_id + '.location',
                item.noun + ' is at ' + item.location + '.',
                ('physical', 'planning', entity_id), 1.0))
        if self.entities['hero'].location == self.entities['partner'].location:
            facts.append(Fact('presence', 'Nia and Mateo are together.',
                              ('presence', 'partner', 'trust'), 1.0))
        if 'solo' in self.entities['program'].state:
            facts.append(Fact('program.solo', 'The sheet lists a solo.',
                              ('program', 'choice', 'performance'), 1.0))
        if self.history:
            last = self.history[-1]
            facts.append(Fact('event:' + str(last['id']),
                              'Previous event: ' + last['frame']['kind'],
                              ('recent', last['frame']['kind']), 1.0))
        return facts


def make_world(seed: int = 0, *, partner_willing: bool | None = None) -> World:
    if partner_willing is not None and not isinstance(partner_willing, bool):
        raise ValueError('partner_willing must be a boolean or None')
    rng = random.Random(seed)
    willing = rng.choice((False, True)) if partner_willing is None else partner_willing
    room = 'music room'
    entities = {
        'hero': Entity('hero', 'Nia', 'person', room, pronoun='she',
                       properties={'animate', 'can_hold'}, state={'wants_duet'},
                       memes={'Care': 0.8, 'Desire': 0.85, 'Fear': rng.uniform(0.2, 0.5)}),
        'partner': Entity('partner', 'Mateo', 'person', room, pronoun='he',
                          properties={'animate', 'can_hold'}, state={'public_unready'},
                          memes={'Trust': rng.uniform(0.3, 0.7), 'Fear': rng.uniform(0.4, 0.8),
                                 'Readiness': 0.9 if willing else 0.1}),
        'teacher': Entity('teacher', 'Dalia', 'person', room, pronoun='she',
                          properties={'animate', 'can_hold'}, memes={'Care': 0.9}),
        'drum': Entity('drum', 'little drum', 'instrument', 'shelf',
                       properties={'portable', 'borrowed', 'red_ribbon'}),
        'spare': Entity('spare', 'second drum', 'instrument', 'shelf',
                        properties={'portable'}),
        'program': Entity('program', 'signup sheet', 'object', 'piano',
                          properties={'physical'}),
    }
    facts = {
        'duet': Fact('duet', 'Nia wants a duet with an answering rhythm.',
                     ('goal', 'desire', 'music')),
        'boundary': Fact('boundary', 'Mateo does not want a public performance.',
                         ('partner', 'fear', 'choice')),
        'sheet': Fact('sheet', 'The physical signup sheet is beside the piano.',
                      ('program', 'choice', 'planning')),
        'shelf': Fact('shelf', 'The instrument shelf is in the music room.',
                      ('physical', 'planning', 'music')),
        'private': Fact('private', 'A private invitation leaves a choice open.',
                        ('partner', 'trust', 'choice')),
    }
    return MusicWorld('music', entities, 'hero', 'partner', 'program', 'drum',
                      room, facts)


def _k(name, adds=(), base=0.0, query=(), preferences=()):
    return kernel(name, adds=adds, base=base, query=query, preferences=preferences)


KERNELS = {
    'opening': _k('opening', ('opened',), query=('goal', 'desire')),
    'borrow': _k('borrow', ('borrowed',), query=('physical', 'music')),
    'invite': _k('invite', ('invited_public',), query=('goal', 'partner')),
    'decline': _k('decline', ('public_answer',), query=('partner', 'fear')),
    'practice': _k('practice', ('accepted',), query=('music', 'care'),
                   preferences=(('Care', 0.3),)),
    'consider': _k('consider', ('accepted',), query=('planning', 'desire'),
                   preferences=(('Desire', 0.3),)),
    'signup': _k('signup', ('signed',), query=('program', 'choice')),
    'rehearse': _k('rehearse', ('rehearsed',), query=('music', 'planning')),
    'reshape': _k('reshape', ('rehearsed',), query=('music', 'desire')),
    'perform': _k('perform', ('performed',), query=('performance', 'music')),
    'invite_private': _k('invite_private', ('space_given', 'private_invited'),
                         query=('partner', 'trust', 'choice'),
                         preferences=(('Trust', 0.5),)),
    'wait': _k('wait', ('space_given',), query=('choice', 'care'),
               preferences=(('Care', 0.3),)),
    'consent': _k('consent', ('private_consent',), base=0.6,
                  query=('partner', 'readiness', 'trust'),
                  preferences=(('Readiness', 0.8), ('Trust', 0.3))),
    'quiet': _k('quiet', ('resolved',), query=('choice', 'care')),
    'decline_private': _k('decline_private', ('resolved',), base=-0.3,
                          query=('partner', 'fear'), preferences=(('Fear', 0.3),)),
    'pickup': _k('pickup', ('picked_up',), query=('physical', 'music')),
    'join': _k('join', ('resolved',), query=('partner', 'music', 'trust')),
    'return': _k('return', query=('physical', 'planning')),
    'ending': _k('ending', ('ended',), query=('music', 'choice')),
}


def candidates(world: World) -> list[tuple]:
    if world.finished:
        return []
    e, flags = world.entities, world.flags
    if not all(x in e for x in ('hero', 'partner', 'teacher', 'drum', 'spare', 'program')):
        return []
    hero, partner, teacher = e['hero'], e['partner'], e['teacher']
    drum, spare, program = e['drum'], e['spare'], e['program']
    room = world.setting
    hero_here = hero.location == room and 'animate' in hero.properties
    partner_here = partner.location == room and 'animate' in partner.properties
    together = hero_here and partner_here
    hero_can_hold = 'can_hold' in hero.properties
    partner_can_hold = 'can_hold' in partner.properties
    rows = []

    def add(kind, actor, patient='', instrument='', destination='', causes=()):
        rows.append((KERNELS[kind], Frame(kind, actor, patient, instrument,
                                         destination, tuple(causes))))

    if 'opened' not in flags:
        if hero_here:
            add('opening', 'hero', causes=('duet',))
    elif 'borrowed' not in flags:
        if (hero_here and hero_can_hold and teacher.location == room
                and 'animate' in teacher.properties and drum.location == 'shelf'
                and 'portable' in drum.properties):
            add('borrow', 'hero', 'drum', 'drum', 'hero', ('shelf',))
    elif 'invited_public' not in flags:
        if together and drum.location == 'hero':
            add('invite', 'hero', 'partner', 'drum', causes=('duet', 'boundary'))
    elif 'public_answer' not in flags:
        if together and 'public_unready' in partner.state:
            add('decline', 'partner', 'hero', causes=('boundary',))
    elif 'accepted' not in flags:
        if together and drum.location == 'hero':
            add('practice', 'hero', 'drum', 'drum', causes=('duet', 'boundary'))
            if spare.location == 'shelf':
                add('consider', 'hero', 'spare', causes=('duet', 'boundary', 'shelf'))
    elif 'signed' not in flags:
        if hero_here and program.location == 'piano' and 'solo' not in program.state:
            add('signup', 'hero', 'program', destination='piano', causes=('sheet', 'boundary'))
    elif 'rehearsed' not in flags:
        if hero_here and drum.location == 'hero' and 'solo' in program.state:
            add('rehearse', 'hero', 'drum', 'drum', causes=('duet', 'sheet'))
            add('reshape', 'hero', 'drum', 'drum', causes=('duet', 'sheet'))
    elif 'performed' not in flags:
        if hero_here and drum.location == 'hero' and 'solo' in program.state:
            add('perform', 'hero', 'program', 'drum', room, ('sheet',))
    elif 'space_given' not in flags:
        if hero_here and drum.location == 'hero':
            add('wait', 'hero', causes=('private',))
            if together:
                add('invite_private', 'hero', 'partner', causes=('private', 'boundary'))
    elif 'resolved' not in flags:
        if 'private_consent' not in flags:
            if hero_here:
                add('quiet', 'hero', causes=('private',))
            if together:
                add('decline_private', 'partner', 'hero', causes=('private',))
                if (partner.memes.get('Readiness', 0.0) >= 0.5
                        and 'consented' not in partner.state):
                    add('consent', 'partner', 'hero', destination=room, causes=('private',))
        elif ('consented' in partner.state and partner.memes.get('Readiness', 0.0) >= 0.5
              and together and drum.location == 'hero'):
            if spare.location == 'shelf' and partner_can_hold and 'portable' in spare.properties:
                add('pickup', 'partner', 'spare', 'spare', 'partner', ('shelf', 'private'))
            elif spare.location == 'partner' and 'joined' not in partner.state:
                add('join', 'partner', 'hero', 'spare', room, ('duet', 'private'))
    else:
        if drum.location == 'hero' and hero_here and hero_can_hold:
            add('return', 'hero', 'drum', 'drum', 'shelf', ('shelf',))
        if spare.location == 'partner' and partner_here and partner_can_hold:
            add('return', 'partner', 'spare', 'spare', 'shelf', ('shelf',))
        if (drum.location == 'shelf' and spare.location == 'shelf'
                and 'performed' in flags and 'solo' in program.state and hero_here):
            add('ending', 'hero', causes=('shelf', 'duet'))
    return rows


def commit(world: World, frame: Frame, sentence: str) -> dict:
    available = candidates(world)
    matches = [k for k, f in available if f == frame]
    if not matches:
        raise ValueError('frame is not an executable continuation of this world')
    before = world.snapshot()
    world.flags.update(matches[0].adds)
    kind = frame.kind
    e = world.entities
    if kind == 'borrow':
        e['drum'].location = 'hero'
    elif kind == 'decline':
        e['partner'].state.add('declined_public')
    elif kind in ('practice', 'consider'):
        e['partner'].memes['Trust'] = min(1.0, e['partner'].memes['Trust'] + 0.1)
    elif kind == 'signup':
        e['program'].state.add('solo')
    elif kind == 'consent':
        e['partner'].state.add('consented')
    elif kind == 'pickup':
        e['spare'].location = 'partner'
    elif kind == 'join':
        e['partner'].state.add('joined')
    elif kind == 'return':
        e[frame.instrument].location = 'shelf'
    world.focus = frame.actor
    record = {'id': len(world.history) + 1, 'frame': asdict(frame),
              'sentence': sentence, 'before': before, 'after': world.snapshot()}
    world.history.append(record)
    return record


def plan(world, frame, tense='past'):
    from ..language import Language
    from ..nouns import pronoun
    g = Language(world, tense)
    n, v, s, pp = g.n, g.v, g.s, g.pp
    hero, partner = g.ref('hero'), g.ref('partner')
    drum, spare = g.ref('drum'), g.ref('spare')
    duet = g.adv(v('play', n('duet', det='a')), pp('with', partner))
    kind = frame.kind
    if kind == 'opening':
        return s('hero', g.adv(v('want', duet), pp('at', n('picnic'))))
    if kind == 'borrow':
        return s('hero', g.adv(v('borrow', drum), pp('from', n('shelf'))))
    if kind == 'invite':
        return s('hero', v('ask', partner, g.adv(v('play', n('duet', det='a')), pp('at', n('picnic')))))
    if kind == 'decline':
        return g.reporting('partner', 'explain', lambda who: g.join(
            s(who, v('like', n('music', det='bare'))),
            s(who, v('want', g.adv(v('play'), pp('before', n('audience')))), negative=True), 'but'))
    if kind in {'practice', 'consider'}:
        acceptance = s('hero', v('accept', g.possess(pronoun('he'), g.cn('answer'))))
        action = (g.adv(v('play', n('beat', 'soft', det='a')), pp('on', drum)) if kind == 'practice'
                  else g.adv(v('look'), pp('at', spare)))
        return g.sequence('hero', v('accept', g.possess(pronoun('he'), g.cn('answer'))), action)
    if kind == 'signup':
        name = g.possess(pronoun('she'), g.cn('name'))
        return s('hero', g.adv(v('write', name), pp('on', g.ref('program')), pp('for', n('solo', det='a'))))
    if kind in {'rehearse', 'reshape'}:
        action = (g.adv(v('practice', n('solo')), 'slowly') if kind == 'rehearse'
                  else v('try', n('pattern', 'different', det='a')))
        return s('hero', g.adv(action, pp('on', drum)))
    if kind == 'perform':
        return s('hero', g.adv(v('perform', n('solo')), pp('before', n('audience'))))
    if kind == 'wait':
        return g.join(s('hero', v('hold', drum)), s('hero', g.adv(v('wait'), 'quietly')))
    if kind == 'invite_private':
        action = g.adv(v('play', n('duet', det='a')), 'privately')
        return s('hero', v('invite', partner, action))
    if kind == 'consent':
        action = g.adv(v('play', n('duet', 'private', det='a')), pp('with', hero))
        return g.reporting('partner', 'say', lambda who: s(who, v('want', action)))
    if kind == 'quiet':
        return s('hero', g.adv(v('leave', n('choice')), pp('with', partner)))
    if kind == 'decline_private':
        return g.join(g.reporting('partner', 'say', lambda who: s(who, g.be('ready'), negative=True)),
                      s('hero', v('accept', g.possess(pronoun('he'), g.cn('answer')))))
    if kind == 'pickup':
        return s('partner', g.adv(v('lift', spare), pp('from', n('shelf'))))
    if kind == 'join':
        players = g.both(hero, partner)
        return s(players, g.adv(v('play', n('duet', 'private', det='a')), pp('on', n('rug'))))
    if kind == 'return':
        return s(frame.actor, g.adv(v('return', g.ref(frame.instrument)), pp('to', n('shelf'))))
    if kind == 'ending':
        # Existing world guard checks both instruments before this claim.
        instruments = g.both(drum, spare)
        image = s(n('ribbon', 'red'), g.adv(v('hang'), pp('between', pronoun('they'))))
        return g.join(s(instruments, g.be(pp('on', n('shelf')))), image)
    raise ValueError(f'no semantic plan for {kind}')

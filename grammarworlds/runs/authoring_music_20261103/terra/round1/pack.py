from dataclasses import asdict
import random

from grammarworlds.world import Entity, Fact, Frame, World, kernel
from grammarworlds.grammar import Grammar, choice, seq


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


def realize(world: World, frame: Frame, tense: str = 'past'):
    if tense != 'past':
        raise ValueError('this pack supports past tense only')
    if frame not in [f for _, f in candidates(world)]:
        raise ValueError('frame is not an executable continuation')
    g = Grammar(world, tense)
    subject = g.ref(frame.actor, subject=True)
    kind = frame.kind

    def sentence(label, *parts):
        return seq('sentence.' + label, *parts, '.')

    if kind == 'opening':
        return sentence(kind,
            choice('opening.setting', 'In the community music room,',
                   'Among the mixed sounds of the music room,'),
            subject, choice('opening.desire', 'wanted a duet for the picnic',
                            'dreamed of a duet for the picnic'),
            choice('opening.image', ', with a drumbeat and an answering rhythm',
                   ', with one beat leaving room for another'))
    if kind == 'borrow':
        return sentence(kind, subject,
            choice('borrow.action', 'borrowed the little drum from the shelf',
                   'took the little drum on loan from the shelf'),
            choice('borrow.detail',
                   ', with Dalia\'s permission and a red ribbon bobbing by her hand',
                   '; Dalia watched its red ribbon sway against Nia\'s wrist'))
    if kind == 'invite':
        return sentence(kind, subject,
            choice('invite.action', 'asked Mateo to play a duet with her at the picnic',
                   'asked Mateo whether he would join her for a picnic duet'),
            choice('invite.detail', ', and waited for his answer',
                   ', leaving a pause for him to decide'))
    if kind == 'decline':
        return sentence(kind, subject,
            choice('decline.boundary',
                   'said he liked playing but did not want everyone watching him',
                   'explained that he liked music but was not ready for an audience'),
            choice('decline.detail', ', holding his folder against his chest',
                   ', with his eyes on the crowded room'))
    if kind == 'practice':
        return sentence(kind, subject,
            choice('accept.action', 'accepted his answer and played a soft beat',
                   'nodded and tried a quieter pattern on her drum'),
            choice('accept.detail', ', leaving space where another rhythm might have entered',
                   ', without asking him to change his mind'))
    if kind == 'consider':
        return sentence(kind, subject,
            choice('consider.action', 'accepted his answer and looked at the second drum',
                   'nodded and glanced toward the spare instrument'),
            choice('consider.detail',
                   ' on the shelf, keeping her imagined answer to herself',
                   ' on the shelf, but left the choice with Mateo'))
    if kind == 'signup':
        return sentence(kind, 'On Friday,', subject,
            choice('signup.action', 'wrote her own name and a drum solo on the signup sheet',
                   'listed herself alone for a drum solo on the signup sheet'),
            choice('signup.detail',
                   ', though she had imagined another name beside hers',
                   ', rather than choosing for Mateo'))
    if kind == 'rehearse':
        return sentence(kind, subject,
            choice('rehearse.action', 'practiced the solo slowly on the rug',
                   'worked through the solo beside the piano'),
            choice('rehearse.detail',
                   ', making some beats softer and others louder until the pauses felt less empty',
                   ', trying different volumes until the silence between beats felt like part of the song'))
    if kind == 'reshape':
        return sentence(kind, subject,
            choice('reshape.action', 'changed the empty spaces in her solo into a pattern of footsteps',
                   'reshaped the pauses in her solo into a path of small beats'),
            choice('reshape.detail',
                   ', discovering a song she could carry on her own',
                   ', and found that the drum could answer itself'))
    if kind == 'perform':
        return sentence(kind, 'On Saturday,', subject,
            choice('perform.action', 'played her drum solo before the picnic crowd',
                   'performed her solo for the people gathered at the picnic'),
            choice('perform.detail',
                   ', filling the wide pauses with quieter beats until the room applauded',
                   ', and let the last soft beat ring before the applause began'))
    if kind == 'wait':
        return sentence(kind, 'When the audience had gone,', subject,
            choice('wait.action', 'held the drum on her lap and let the room grow quiet',
                   'kept her drum close and waited as the room settled'),
            choice('wait.detail', ', leaving room for an answer that might never come',
                   ', without demanding an answer from anyone'))
    if kind == 'invite_private':
        return sentence(kind, 'After the audience had gone,', subject,
            choice('private.invitation',
                   'asked Mateo whether he wanted to try the answer part privately',
                   'invited Mateo to try a duet away from an audience'),
            choice('private.freedom', ', and told him he could say no',
                   ', making it clear that the choice was his'))
    if kind == 'consent':
        if 'private_invited' in world.flags:
            action = choice('consent.answer',
                            'said he would like to try the answer part with Nia',
                            'told Nia that he wanted to play a private duet')
        else:
            action = choice('consent.offer',
                            'asked Nia if they could try the answer part together',
                            'said he would like to play a private duet with Nia')
        return sentence(kind, subject, action,
            choice('consent.place', ' on the rug, away from an audience',
                   ' just for themselves, away from the performance space'))
    if kind == 'quiet':
        return sentence(kind, subject,
            choice('quiet.action', 'let the possibility of a duet rest for another day',
                   'left the idea of playing together open for another time'),
            choice('quiet.detail',
                   ', glad that her solo had found its own shape',
                   ', and listened to the last echoes of her solo'))
    if kind == 'decline_private':
        return sentence(kind, subject,
            choice('private.decline', 'said he would rather listen than play for now',
                   'said he was not ready to try a duet even in private'),
            choice('private.respect', ', and Nia accepted his answer without pressing him',
                   '; Nia nodded and gave him space'))
    if kind == 'pickup':
        return sentence(kind, subject,
            choice('pickup.action', 'lifted the second drum from the shelf',
                   'picked up the spare drum from the shelf'),
            choice('pickup.detail', ', testing its weight in his hands',
                   ', and carried it toward the rug at his own pace'))
    if kind == 'join':
        return sentence(kind, subject,
            choice('join.action', 'tapped the answer part on his drum and Nia answered on hers',
                   'began a private duet with Nia, trading drumbeats on the rug'),
            choice('join.detail', ', with no name on a program and no audience to watch',
                   ', leaving each other space to find the next beat'))
    if kind == 'return':
        if frame.instrument == 'drum':
            return sentence(kind, subject,
                choice('return.hero', 'returned the borrowed drum to the shelf',
                       'put the borrowed drum back on the shelf'),
                choice('return.ribbon', ', its red ribbon brushing the wooden edge',
                       ', and smoothed its red ribbon against the handle'))
        return sentence(kind, subject,
            choice('return.partner', 'returned the second drum to the shelf',
                   'put the spare drum back on the shelf'),
            choice('return.detail', ', carefully settling it in its place',
                   ', where its last vibration faded'))
    if kind == 'ending':
        if 'joined' in world.entities['partner'].state:
            return sentence(kind,
                choice('ending.duet.image',
                       'On the shelf, the red ribbon hung between the two drums',
                       'The red ribbon lay between the two drums on the shelf'),
                choice('ending.duet.echo', ', quivering faintly after their private duet',
                       ', while the last sound of their duet faded into the quiet room'))
        return sentence(kind,
            choice('ending.solo.image',
                   'On the shelf, the ribbon rested between the two quiet drums',
                   'The two drums stood on the shelf with the red ribbon between them'),
            choice('ending.solo.echo',
                   ', and Nia\'s solo still seemed to leave a little space for another day',
                   ', while the last notes of Nia\'s solo faded in the quiet room'))
    raise ValueError('unknown frame kind')


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

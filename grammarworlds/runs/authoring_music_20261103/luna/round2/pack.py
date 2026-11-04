from dataclasses import asdict
import random

from grammarworlds.grammar import Grammar, choice, seq
from grammarworlds.world import Entity, Fact, Frame, Kernel, World, kernel


class MusicWorld(World):
    def __init__(self, *args, partner_willing=False, **kwargs):
        super().__init__(*args, **kwargs)
        self.partner_willing = partner_willing

    def snapshot(self):
        result = super().snapshot()
        result['partner_willing'] = self.partner_willing
        return result

    def facts_for_attention(self):
        result = list(self.facts.values())
        for key, entity in self.entities.items():
            result.append(Fact('location:' + key, entity.noun + ' is at ' + entity.location,
                               ('location', key, entity.kind), 1.0))
            for concept, value in sorted(entity.memes.items()):
                result.append(Fact(key + '.' + concept,
                    entity.noun + ' has ' + concept.lower() + ' ' + format(value, '.2f'),
                    ('actor', key, concept.lower()), value))
        if self.history:
            last = self.history[-1]
            kind = last['frame']['kind']
            result.append(Fact('event:' + str(last['id']), 'Previously: ' + kind,
                               ('recent', kind), 1.0))
        if 'listed_solo' in self.flags:
            result.append(Fact('program.solo', 'The signup sheet lists Nia alone.',
                               ('program', 'solo', 'outcome'), 1.0))
        if 'joined' in self.flags:
            result.append(Fact('private.duet', 'Mateo freely joined a private duet.',
                               ('private', 'duet', 'outcome'), 1.0))
        return result


def make_world(seed: int = 0, *, partner_willing: bool | None = None) -> World:
    rng = random.Random(seed)
    willing = rng.choice((False, True)) if partner_willing is None else partner_willing
    if not isinstance(willing, bool):
        raise ValueError('partner_willing must be True, False, or None')
    entities = {
        'hero': Entity('hero', 'Nia', 'person', 'music_room', pronoun='she',
            properties={'animate', 'can_hold'}, memes={
                'Care': 0.82, 'Fear': rng.uniform(0.2, 0.65), 'Trust': 0.48,
                'Desire': 0.96, 'Curiosity': 0.68}),
        'partner': Entity('partner', 'Mateo', 'person', 'music_room', pronoun='he',
            properties={'animate', 'can_hold'}, state={'near_door'}, memes={
                'Care': 0.52, 'Fear': 0.78, 'Trust': 0.42,
                'Desire': 0.72 if willing else 0.22}),
        'teacher': Entity('teacher', 'Dalia', 'person', 'music_room', pronoun='she',
            properties={'animate', 'can_hold'}, memes={'Care': 0.91, 'Trust': 0.7}),
        'drum': Entity('drum', 'drum', 'instrument', 'shelf',
            properties={'portable', 'loaned', 'instrument'}),
        'spare': Entity('spare', 'second drum', 'instrument', 'shelf',
            properties={'portable', 'instrument'}),
        'program': Entity('program', 'signup sheet', 'object', 'music_room',
            properties={'physical', 'paper'}),
    }
    facts = {
        'wish': Fact('wish', 'Nia wants a duet with an answering part.',
                     ('goal', 'desire', 'music', 'hero')),
        'social_boundary': Fact('social_boundary',
            'Mateo can choose whether he is comfortable performing before a crowd.',
            ('social', 'autonomy', 'partner', 'fear')),
        'separate_instruments': Fact('separate_instruments',
            'Two separate drums are available in the music room.',
            ('instrument', 'music', 'planning')),
        'program_deadline': Fact('program_deadline',
            'The Saturday program needs its act listing before Friday closing.',
            ('program', 'deadline', 'planning')),
        'music_room': Fact('music_room', 'The community music room is a shared place to practice.',
                           ('music', 'room', 'social')),
        'performance_goal': Fact('performance_goal', 'Nia hopes to perform at the Saturday picnic.',
                                 ('goal', 'performance', 'desire')),
    }
    return MusicWorld('music_room', entities, 'hero', 'partner', 'program', 'drum',
                      'music_room', facts, partner_willing=willing)


KERNELS = (
    kernel('notice', adds=('noticed',), base=0.25, query=('music', 'goal', 'desire'),
           preferences=(('Desire', 0.65), ('Care', 0.25))),
    kernel('want', requires=('noticed',), excludes=('wanted',), adds=('wanted',), base=0.1,
           query=('goal', 'desire', 'care'), preferences=(('Desire', 0.8), ('Care', 0.5))),
    kernel('borrow', requires=('wanted',), excludes=('borrowed',), adds=('borrowed',), base=0.2,
           query=('instrument', 'room', 'care'), preferences=(('Care', 0.45),)),
    kernel('retrieve_drum', requires=('borrowed',), excludes=('drum_retrieved', 'performed'),
           adds=('drum_retrieved',), base=-0.2, query=('instrument', 'location', 'planning')),
    kernel('ask', requires=('borrowed',), excludes=('asked', 'practiced'), adds=('asked',), base=0.05,
           query=('social', 'partner', 'fear', 'trust'), preferences=(('Fear', 0.55), ('Trust', 0.45))),
    kernel('public_decline', requires=('asked',), excludes=('public_declined',),
           adds=('public_declined',), base=0.15, query=('social', 'autonomy', 'partner'),
           preferences=(('Fear', 0.35),)),
    kernel('practice', requires=('borrowed',), excludes=('practiced',), adds=('practiced',), base=0.2,
           query=('instrument', 'goal', 'curiosity'), preferences=(('Curiosity', 0.5), ('Desire', 0.25))),
    kernel('hear_tap', requires=('practiced',), excludes=('tap_observed', 'sheet_ready'),
           adds=('tap_observed',), base=-0.25, query=('rhythm', 'social', 'trust'),
           preferences=(('Trust', 0.25),)),
    kernel('set_program', requires=('practiced',), excludes=('sheet_ready',),
           adds=('sheet_ready',), base=0.2, query=('program', 'deadline', 'planning')),
    kernel('choose_solo', requires=('sheet_ready',), excludes=('listed_solo',),
           adds=('listed_solo',), base=0.15, query=('program', 'autonomy', 'desire'),
           preferences=(('Desire', 0.2), ('Trust', 0.2))),
    kernel('perform', requires=('listed_solo',), excludes=('performed',), adds=('performed',),
           base=0.2, query=('performance', 'goal', 'instrument'),
           preferences=(('Desire', 0.25), ('Fear', -0.15))),
    kernel('private_invite', requires=('performed',), excludes=('private_invited',),
           adds=('private_invited',), base=0.1, query=('private', 'social', 'trust', 'fear'),
           preferences=(('Trust', 0.35), ('Fear', 0.12))),
    kernel('consent', requires=('private_invited',), excludes=('consented',), adds=('consented',),
           base=0.15, query=('private', 'partner', 'trust', 'desire'),
           preferences=(('Trust', 0.35), ('Desire', 0.2))),
    kernel('private_decline', requires=('private_invited',), excludes=('private_declined',),
           adds=('private_declined',), base=0.15, query=('private', 'partner', 'autonomy', 'fear'),
           preferences=(('Fear', 0.25),)),
    kernel('leave_open', requires=('performed',),
           excludes=('joined', 'private_declined', 'invitation_left_open'),
           adds=('invitation_left_open',), base=0.0, query=('social', 'autonomy', 'performance')),
    kernel('pickup_spare', requires=('consented',), excludes=('spare_picked',),
           adds=('spare_picked',), base=0.1, query=('instrument', 'private', 'trust')),
    kernel('join', requires=('consented',), excludes=('joined',), adds=('joined',), base=0.15,
           query=('private', 'rhythm', 'trust'), preferences=(('Trust', 0.25),)),
    kernel('return_drum', requires=('performed',), excludes=('returned_drum',),
           adds=('returned_drum',), base=0.1, query=('instrument', 'responsibility')),
    kernel('return_spare', excludes=('returned_spare',), adds=('returned_spare',), base=0.1,
           query=('instrument', 'responsibility', 'private')),
    kernel('ending', requires=('performed', 'returned_drum'), adds=('ended',), base=0.25,
           query=('outcome', 'music', 'autonomy')),
)
BY_NAME = {k.name: k for k in KERNELS}
CAUSES = {
    'notice': ('music_room', 'wish'), 'want': ('wish', 'performance_goal'),
    'borrow': ('separate_instruments', 'music_room'),
    'retrieve_drum': ('separate_instruments', 'music_room'),
    'ask': ('wish', 'social_boundary'), 'public_decline': ('social_boundary',),
    'practice': ('wish', 'separate_instruments'), 'hear_tap': ('music_room', 'social_boundary'),
    'set_program': ('program_deadline',), 'choose_solo': ('program_deadline', 'social_boundary'),
    'perform': ('performance_goal', 'separate_instruments'),
    'private_invite': ('performance_goal', 'social_boundary'),
    'consent': ('social_boundary', 'separate_instruments'),
    'private_decline': ('social_boundary',), 'leave_open': ('performance_goal', 'social_boundary'),
    'pickup_spare': ('separate_instruments', 'social_boundary'),
    'join': ('separate_instruments', 'social_boundary'),
    'return_drum': ('separate_instruments', 'performance_goal'),
    'return_spare': ('separate_instruments', 'social_boundary'),
    'ending': ('performance_goal', 'separate_instruments', 'program_deadline'),
}


def _present(world, key):
    return key in world.entities and world.entities[key].kind == 'person' and world.entities[key].location == world.setting


def _accessible(world, location):
    if location in ('shelf', 'music_room', 'rug', 'piano', world.setting, 'hero'):
        return True
    if location in world.entities and world.entities[location].kind == 'person':
        return _present(world, location)
    return False


def _frame(world, kind):
    hero, partner = world.hero, world.helper
    actor, patient, instrument, destination = hero, '', '', world.setting
    if kind == 'notice':
        patient, instrument = 'drum', 'drum'
    elif kind == 'want':
        patient, instrument = partner, 'drum'
    elif kind == 'borrow':
        actor = 'teacher' if _present(world, 'teacher') else hero
        patient, instrument, destination = 'drum', 'drum', hero
    elif kind == 'retrieve_drum':
        patient, instrument, destination = 'drum', 'drum', hero
    elif kind == 'ask':
        patient, instrument = partner, 'drum'
    elif kind == 'public_decline':
        actor, patient = partner, hero
    elif kind == 'practice':
        patient, instrument, destination = 'drum', 'drum', 'rug'
    elif kind == 'hear_tap':
        actor, patient, instrument = partner, hero, 'drum'
    elif kind == 'set_program':
        actor = 'teacher' if _present(world, 'teacher') else hero
        patient, destination = 'program', 'piano'
    elif kind in ('choose_solo', 'perform'):
        patient, instrument = 'program', 'drum'
    elif kind == 'private_invite':
        patient, instrument = partner, 'drum'
    elif kind in ('consent', 'private_decline'):
        actor, patient, instrument = partner, hero, 'spare'
    elif kind == 'leave_open':
        patient = partner
    elif kind == 'pickup_spare':
        actor, patient, instrument, destination = partner, 'spare', 'spare', partner
    elif kind == 'join':
        actor, patient, instrument, destination = partner, hero, 'spare', 'rug'
    elif kind == 'return_drum':
        patient, instrument, destination = 'drum', 'drum', 'shelf'
    elif kind == 'return_spare':
        actor = partner if _present(world, partner) or world.entities['spare'].location == partner else hero
        patient, instrument, destination = 'spare', 'spare', 'shelf'
    elif kind == 'ending':
        patient, instrument = 'program', 'drum'
    return Frame(kind, actor, patient, instrument, destination, CAUSES[kind])


def _eligible(world, kind):
    flags, entities = world.flags, world.entities
    if 'ended' in flags:
        return False
    if kind == 'notice':
        return 'noticed' not in flags
    if kind == 'want':
        return 'noticed' in flags and 'wanted' not in flags
    if kind == 'borrow':
        return ('wanted' in flags and 'borrowed' not in flags and
                entities['drum'].location in ('shelf', 'hero') and
                (_present(world, 'teacher') or _present(world, world.hero)))
    if kind == 'retrieve_drum':
        return ('borrowed' in flags and 'drum_retrieved' not in flags and
                'performed' not in flags and entities['drum'].location != world.hero and
                _accessible(world, entities['drum'].location))
    if kind == 'ask':
        return ('borrowed' in flags and 'asked' not in flags and 'practiced' not in flags and
                _present(world, world.helper))
    if kind == 'public_decline':
        return 'asked' in flags and 'public_declined' not in flags and _present(world, world.helper)
    if kind == 'practice':
        return ('borrowed' in flags and 'practiced' not in flags and
                entities['drum'].location == world.hero and
                ('public_declined' in flags or not _present(world, world.helper)))
    if kind == 'hear_tap':
        return ('practiced' in flags and 'tap_observed' not in flags and 'sheet_ready' not in flags
                and _present(world, world.helper))
    if kind == 'set_program':
        return ('practiced' in flags and 'sheet_ready' not in flags and
                entities['program'].location in ('music_room', 'piano') and
                (_present(world, 'teacher') or _present(world, world.hero)))
    if kind == 'choose_solo':
        return ('sheet_ready' in flags and 'listed_solo' not in flags and
                entities['program'].location == 'piano')
    if kind == 'perform':
        return ('listed_solo' in flags and 'performed' not in flags and
                'solo' in entities['program'].state and entities['drum'].location == world.hero)
    if kind == 'private_invite':
        return ('performed' in flags and 'private_invited' not in flags and
                'invitation_left_open' not in flags and _present(world, world.helper))
    if kind == 'consent':
        return ('private_invited' in flags and world.partner_willing and 'consented' not in flags
                and _present(world, world.helper))
    if kind == 'private_decline':
        return ('private_invited' in flags and not world.partner_willing and
                'private_declined' not in flags and _present(world, world.helper))
    if kind == 'leave_open':
        unresolved = not any(x in flags for x in ('joined', 'private_declined', 'invitation_left_open'))
        absent = not _present(world, world.helper)
        blocked_instrument = ('consented' in flags and
            entities['spare'].location != world.helper and entities['spare'].location != 'shelf' and
            not _accessible(world, entities['spare'].location))
        return 'performed' in flags and unresolved and (absent or blocked_instrument)
    if kind == 'pickup_spare':
        return ('consented' in flags and 'consented' in entities[world.helper].state and
                'spare_picked' not in flags and _present(world, world.helper) and
                entities['spare'].location != world.helper and
                _accessible(world, entities['spare'].location))
    if kind == 'join':
        return ('consented' in flags and 'consented' in entities[world.helper].state and
                'joined' not in flags and _present(world, world.helper) and
                entities['spare'].location == world.helper)
    resolved = any(x in flags for x in ('private_declined', 'joined', 'invitation_left_open'))
    if kind == 'return_drum':
        return ('performed' in flags and resolved and 'returned_drum' not in flags and
                _accessible(world, entities['drum'].location))
    if kind == 'return_spare':
        return ('spare' in entities and entities['spare'].location != 'shelf' and
                (('joined' in flags) or ('invitation_left_open' in flags)) and
                (entities['spare'].location == world.helper or
                 _accessible(world, entities['spare'].location)))
    if kind == 'ending':
        return ('performed' in flags and 'returned_drum' in flags and
                entities['drum'].location == 'shelf' and entities['spare'].location == 'shelf')
    return False


def candidates(world: World) -> list[tuple[Kernel, Frame]]:
    if not isinstance(world, MusicWorld):
        raise ValueError('expected a music-room world')
    result = []
    for item in KERNELS:
        if item.requires <= world.flags and not item.excludes.intersection(world.flags):
            if _eligible(world, item.name):
                result.append((item, _frame(world, item.name)))
    return result


class MusicGrammar(Grammar):
    VERBS = {
        'notice': ('noticed', 'notices'), 'spot': ('spotted', 'spots'),
        'want': ('wanted', 'wants'), 'hope': ('hoped', 'hopes'),
        'lend': ('lent', 'lends'), 'ask': ('asked', 'asks'), 'say': ('said', 'says'),
        'practice': ('practiced', 'practices'), 'rehearse': ('rehearsed', 'rehearses'),
        'tap': ('tapped', 'taps'), 'set': ('set', 'sets'), 'write': ('wrote', 'writes'),
        'play': ('played', 'plays'), 'fill': ('filled', 'fills'), 'agree': ('agreed', 'agrees'),
        'pick': ('picked', 'picks'), 'cross': ('crossed', 'crosses'), 'join': ('joined', 'joins'),
        'leave': ('left', 'leaves'), 'return': ('returned', 'returns'), 'rest': ('rested', 'rests'),
        'stay': ('stayed', 'stays'), 'notice': ('noticed', 'notices'),
    }

    def verb(self, base: str, actor: str | None = None) -> str:
        past, present = self.VERBS[base]
        if self.tense == 'past':
            return past
        if actor is not None and self.world.entities[actor].number == 'plural':
            return base
        return present

    def for_frame(self, frame: Frame):
        w, hero, partner = self.world, self.world.hero, self.world.helper
        k = frame.kind
        if k == 'notice':
            scene = choice('notice.room',
                'On Thursday, the music room filled with wandering piano scales and sleepy flute notes;',
                'Amid the piano scales and long flute notes in the music room;')
            clause = seq('notice.perception', scene, self.ref(hero, subject=True),
                choice('notice.verb', self.verb('notice', hero), self.verb('spot', hero)),
                'the little drum', choice('notice.place', 'on the shelf', 'beside the shelf'),
                ';', 'its red ribbon', choice('notice.ribbon', 'rested against the handle',
                                               'hung from the handle'))
            return self.sentence(clause, marker=False)
        if k == 'want':
            clause = self.action(hero, choice('want.verb', self.verb('want', hero), self.verb('hope', hero)),
                'a duet for Saturday', choice('want.answer', 'with a drumbeat and an answering part',
                                               'where one beat could invite another'))
            return self.sentence(clause)
        if k == 'borrow':
            if frame.actor == 'teacher':
                clause = seq('borrow.offer', self.ref('teacher', subject=True), self.verb('lend', 'teacher'),
                    self.ref(hero), 'the drum', choice('borrow.duration', 'for the week', 'until Saturday'),
                    ',', 'its red ribbon', choice('borrow.ribbon', 'knotted around the handle',
                                                  'bright against the wooden rim'))
            else:
                clause = self.action(hero, 'borrowed', 'the loaned drum from the shelf',
                                     'and took care to keep it safe for the week')
            return self.sentence(clause)
        if k == 'retrieve_drum':
            return self.sentence(self.action(hero, 'retrieved', 'the borrowed drum',
                choice('retrieve.place', 'from the shelf', 'from nearby in the music room')))
        if k == 'ask':
            clause = self.action(hero, self.verb('ask', hero), self.ref(partner),
                choice('ask.content', 'whether he would like to answer her drum in a Saturday duet',
                       'if he might play the answering part with her at the picnic'))
            return self.sentence(clause)
        if k == 'public_decline':
            clause = seq('decline.public', self.ref(partner, subject=True), self.verb('say', partner),
                choice('decline.reason', 'that he liked playing, but did not want a roomful of eyes on him yet',
                       'that he enjoyed music, though he was not ready for a public performance'))
            return self.sentence(clause)
        if k == 'practice':
            clause = seq('practice.pattern', self.ref(hero, subject=True),
                choice('practice.verb', self.verb('practice', hero), self.verb('rehearse', hero)),
                'the drum pattern on the rug', choice('practice.pause',
                ', leaving little pauses between the beats', ', making room for an answer'),
                ',', 'the red ribbon', choice('practice.ribbon', 'bobbing with each stroke',
                                               'quivering against the rim'))
            return self.sentence(clause)
        if k == 'hear_tap':
            clause = seq('tap.observation', self.ref(partner, subject=True), self.verb('tap', partner),
                'the same rhythm on his knees', ';', self.ref(hero, subject=True),
                self.verb('notice', hero), 'the answer without treating it as permission')
            return self.sentence(clause)
        if k == 'set_program':
            if frame.actor == 'teacher':
                clause = seq('program.setup', self.ref('teacher', subject=True), self.verb('set', 'teacher'),
                    'the signup sheet beside the piano', ',', 'announcing that',
                    choice('program.space', 'one act remained for Saturday',
                           'the program had room for one more act'))
            else:
                clause = self.action(hero, 'set', 'the signup sheet beside the piano',
                                     'with room for one Saturday act')
            return self.sentence(clause)
        if k == 'choose_solo':
            clause = seq('program.solo', self.ref(hero, subject=True), 'wrote',
                'only her own name on the signup sheet', ',', 'choosing a drum solo',
                choice('program.boundary', 'rather than listing Mateo without his consent',
                       'and leaving the public choice with Mateo'))
            return self.sentence(clause)
        if k == 'perform':
            clause = seq('performance.scene', choice('performance.introduction',
                'On Saturday, folding chairs crowded the room as Dalia introduced the solo;',
                'Before the waiting rows of chairs, Dalia introduced Nia drum solo;'),
                self.ref(hero, subject=True), self.verb('play', hero),
                choice('performance.pattern', 'two quick beats and a wide pause',
                       'a steady pattern that opened into a pause'),
                ',', 'then', self.verb('fill', hero), 'the pause with quieter beats')
            return self.sentence(clause, marker=False)
        if k == 'private_invite':
            clause = seq('invite.private', self.ref(hero, subject=True), self.verb('ask', hero),
                self.ref(partner), 'whether he wanted to try the answering part privately',
                choice('invite.place', 'away from the program', 'on the rug after the crowd thinned'))
            return self.sentence(clause)
        if k == 'consent':
            clause = seq('consent.expressed', self.ref(partner, subject=True), self.verb('agree', partner),
                'to try a private duet on the rug', ',', 'choosing the answering part for himself')
            return self.sentence(clause)
        if k == 'private_decline':
            clause = seq('decline.private', self.ref(partner, subject=True), self.verb('say', partner),
                'he would rather listen than play', ';', self.ref(hero, subject=True),
                self.verb('leave', hero), 'the choice with him without asking again')
            return self.sentence(clause)
        if k == 'leave_open':
            clause = seq('invitation.open', 'With Mateo away,', self.ref(hero, subject=True),
                self.verb('leave', hero), 'the invitation open',
                choice('invitation.respect', 'without deciding his answer for him',
                       'for another day, without assuming a yes'))
            return self.sentence(clause, marker=False)
        if k == 'pickup_spare':
            clause = seq('spare.pickup', self.ref(partner, subject=True), self.verb('cross', partner),
                'to the shelf and', self.verb('pick', partner), 'up the second drum',
                choice('spare.destination', 'to carry it to the rug', 'to bring it beside Nia'))
            return self.sentence(clause)
        if k == 'join':
            clause = seq('private.duet', self.ref(partner, subject=True), self.verb('join', partner),
                self.ref(hero), 'on the rug with one testing answer beat', ';',
                self.ref(hero, subject=True), self.verb('leave', hero), 'room for two more')
            return self.sentence(clause)
        if k == 'return_drum':
            if w.entities['drum'].location == 'shelf':
                clause = self.action(hero, 'checked', 'that the borrowed drum was back on the shelf',
                                     'before the room grew quiet')
            else:
                clause = seq('return.borrowed', self.ref(hero, subject=True), self.verb('return', hero),
                    'the borrowed drum to the shelf', ',', 'the red ribbon',
                    choice('return.ribbon', 'quivering as the last sound faded',
                           'settling against the wooden rim'))
            return self.sentence(clause)
        if k == 'return_spare':
            clause = seq('return.spare', self.ref(frame.actor, subject=True), self.verb('return', frame.actor),
                'the second drum to the shelf', ',', 'both instruments back where they belonged')
            return self.sentence(clause)
        if k == 'ending':
            if 'joined' in w.entities[partner].state:
                clause = seq('ending.private_duet', 'The two drums rested side by side on the shelf',
                    ',', 'their unlisted duet', choice('ending.sound', 'lingering as the ribbon quivered',
                                                       'fading beneath the room quiet sounds'))
            elif 'private_declined' in w.flags:
                clause = seq('ending.respected_solo', 'The borrowed drum rested beside the untouched second drum',
                    'on the shelf', ';', 'the program still named Nia alone', ',',
                    'and Mateo choice stayed his')
            else:
                clause = seq('ending.open_invitation', 'Both drums rested back on the shelf', ';',
                    'Nia program remained a solo', ',', 'with a quiet invitation left open for Mateo')
            return self.sentence(clause, marker=False)
        raise ValueError('no grammar for event ' + k)


def realize(world: World, frame: Frame, tense: str = 'past'):
    if frame not in [f for _, f in candidates(world)]:
        raise ValueError('frame is not available in this world')
    return MusicGrammar(world, tense).for_frame(frame)


def commit(world: World, frame: Frame, sentence: str) -> dict:
    available = {f: k for k, f in candidates(world)}
    if frame not in available:
        raise ValueError('frame is not an executable continuation of this world')
    before = world.snapshot()
    kind = frame.kind
    world.flags.update(available[frame].adds)
    if kind == 'borrow':
        world.entities['drum'].location = world.hero
    elif kind == 'retrieve_drum':
        world.entities['drum'].location = world.hero
    elif kind == 'public_decline':
        world.entities[world.helper].state.add('public_declined')
    elif kind == 'set_program':
        world.entities['program'].location = 'piano'
    elif kind == 'choose_solo':
        world.entities['program'].state.add('solo')
    elif kind == 'consent':
        if frame.actor != 'partner':
            raise ValueError('only the partner can consent')
        world.entities['partner'].state.add('consented')
    elif kind == 'pickup_spare':
        world.entities['spare'].location = 'partner'
    elif kind == 'join':
        if frame.actor != 'partner' or 'consented' not in world.entities['partner'].state:
            raise ValueError('joining requires the partner consent frame')
        world.entities['partner'].state.add('joined')
    elif kind == 'return_drum':
        world.entities['drum'].location = 'shelf'
    elif kind == 'return_spare':
        world.entities['spare'].location = 'shelf'
        if frame.actor == 'partner':
            world.entities['partner'].location = world.setting
    world.focus = frame.actor
    record = dict(id=len(world.history) + 1, frame=asdict(frame), sentence=sentence,
                  before=before, after=world.snapshot())
    world.history.append(record)
    return record
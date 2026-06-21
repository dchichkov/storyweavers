#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/tonsil_repetition_transformation_flashback_whodunit.py
=================================================================================

A standalone story world for a tiny child-facing whodunit: someone is making a
mysterious repeated hum during rehearsal, and the little detective must work out
who it is. The solution is gentle rather than scary: a worried child is hiding
because a sore tonsil has turned a singing voice into a croak.

The world is built around three required narrative instruments:

* Repetition: the strange "hmm-hmm-hmm" sound returns as a clue.
* Transformation: the hidden child seems transformed into a dragon / owl /
  captain by a costume, and their voice later transforms from croaky to clear
  or soft.
* Flashback: the detective remembers yesterday's rehearsal and a clue about the
  sore tonsil.

The style stays close to a whodunit, but for TinyStories-age children:
curiosity, clues, a deduction, and a kind reveal.

Run it
------
    python storyworlds/worlds/gpt-5.4/tonsil_repetition_transformation_flashback_whodunit.py
    python storyworlds/worlds/gpt-5.4/tonsil_repetition_transformation_flashback_whodunit.py --all
    python storyworlds/worlds/gpt-5.4/tonsil_repetition_transformation_flashback_whodunit.py --qa
    python storyworlds/worlds/gpt-5.4/tonsil_repetition_transformation_flashback_whodunit.py --trace --seed 7
    python storyworlds/worlds/gpt-5.4/tonsil_repetition_transformation_flashback_whodunit.py --verify
"""

from __future__ import annotations

import argparse
import json
import os
import random
import sys
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from results import QAItem, StoryError, StorySample  # noqa: E402

THRESHOLD = 1.0
SENSE_MIN = 1


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    role: str = ""
    attrs: dict = field(default_factory=dict)
    tags: set[str] = field(default_factory=set)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman", "teacher_f"}
        male = {"boy", "father", "dad", "man", "teacher_m"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return {
            "mother": "mom",
            "father": "dad",
            "teacher_f": "teacher",
            "teacher_m": "teacher",
        }.get(self.type, self.type)


@dataclass
class Setting:
    id: str
    place: str
    affordances: set[str] = field(default_factory=set)
    hiding_spot: str = ""
    atmosphere: str = ""


@dataclass
class Act:
    id: str
    title: str
    line: str
    repeated_sound: str
    clue: str
    transform_word: str
    needs_voice: bool = True
    tags: set[str] = field(default_factory=set)


@dataclass
class Costume:
    id: str
    label: str
    phrase: str
    clue: str
    act: str
    tags: set[str] = field(default_factory=set)


@dataclass
class ThroatState:
    id: str
    label: str
    severity: int
    allowed_remedies: set[str] = field(default_factory=set)
    note: str = ""
    tags: set[str] = field(default_factory=set)


@dataclass
class Remedy:
    id: str
    label: str
    phrase: str
    power: int
    sense: int
    action: str
    tags: set[str] = field(default_factory=set)


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str) -> Entity:
        return self.entities[eid]

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)


SETTINGS = {
    "auditorium": Setting(
        id="auditorium",
        place="the little school auditorium",
        affordances={"dragon_song", "owl_poem", "captain_story"},
        hiding_spot="behind the velvet curtain by the prop boxes",
        atmosphere="The room smelled like paint and paper stars.",
    ),
    "library": Setting(
        id="library",
        place="the library reading room",
        affordances={"owl_poem", "captain_story"},
        hiding_spot="behind the tall atlas shelf and the beanbag pile",
        atmosphere="The room was quiet except for pages whispering when they turned.",
    ),
    "playroom": Setting(
        id="playroom",
        place="the playroom stage corner",
        affordances={"dragon_song", "owl_poem"},
        hiding_spot="inside the dress-up tent beside the costume trunk",
        atmosphere="The room was bright with crayons, tape, and cardboard crowns.",
    ),
}

ACTS = {
    "dragon_song": Act(
        id="dragon_song",
        title="the dragon song",
        line='"I am the bright red dragon of the dawn!"',
        repeated_sound='"Hmm-hmm-hmm,"',
        clue="a tiny red paper scale",
        transform_word="dragon",
        tags={"music", "costume", "clue"},
    ),
    "owl_poem": Act(
        id="owl_poem",
        title="the owl poem",
        line='"Whoo watches the moon with golden eyes?"',
        repeated_sound='"Hmm-hmm-hmm,"',
        clue="a soft brown feather",
        transform_word="owl",
        tags={"poem", "costume", "clue"},
    ),
    "captain_story": Act(
        id="captain_story",
        title="the captain story",
        line='"Steady now, sailors -- follow the shining star!"',
        repeated_sound='"Hmm-hmm-hmm,"',
        clue="a shiny brass button",
        transform_word="captain",
        tags={"story", "costume", "clue"},
    ),
}

COSTUMES = {
    "dragon": Costume(
        id="dragon",
        label="dragon costume",
        phrase="a red dragon cape and tail",
        clue="a tiny red paper scale",
        act="dragon_song",
        tags={"dragon", "dressup"},
    ),
    "owl": Costume(
        id="owl",
        label="owl costume",
        phrase="a brown owl cape with felt wings",
        clue="a soft brown feather",
        act="owl_poem",
        tags={"owl", "dressup"},
    ),
    "captain": Costume(
        id="captain",
        label="captain costume",
        phrase="a navy captain coat with brass buttons",
        clue="a shiny brass button",
        act="captain_story",
        tags={"captain", "dressup"},
    ),
}

THROAT_STATES = {
    "scratchy": ThroatState(
        id="scratchy",
        label="a scratchy tonsil",
        severity=1,
        allowed_remedies={"warm_tea", "honey_water", "quiet_rest"},
        note="It hurts to push the voice too hard.",
        tags={"tonsil", "throat"},
    ),
    "swollen": ThroatState(
        id="swollen",
        label="a sore swollen tonsil",
        severity=2,
        allowed_remedies={"warm_tea", "quiet_rest", "ice_pop"},
        note="The voice comes out rough and tired.",
        tags={"tonsil", "throat"},
    ),
}

REMEDIES = {
    "warm_tea": Remedy(
        id="warm_tea",
        label="warm tea",
        phrase="a mug of warm lemon tea",
        power=2,
        sense=2,
        action="sipped the warm lemon tea slowly and rested for a few quiet minutes",
        tags={"tea", "warm_drink", "voice"},
    ),
    "honey_water": Remedy(
        id="honey_water",
        label="honey water",
        phrase="a cup of warm honey water",
        power=1,
        sense=2,
        action="took small sips of warm honey water and breathed quietly",
        tags={"honey", "warm_drink", "voice"},
    ),
    "quiet_rest": Remedy(
        id="quiet_rest",
        label="quiet rest",
        phrase="a quiet corner and a few deep breaths",
        power=1,
        sense=2,
        action="sat very still in the quiet corner and let the throat rest",
        tags={"rest", "voice"},
    ),
    "ice_pop": Remedy(
        id="ice_pop",
        label="ice pop",
        phrase="a cool ice pop from the staff freezer",
        power=2,
        sense=2,
        action="licked the cool ice pop and let the cold soothe the sore spot",
        tags={"cold_treat", "voice"},
    ),
    "crackers": Remedy(
        id="crackers",
        label="crackers",
        phrase="a handful of crunchy crackers",
        power=0,
        sense=0,
        action="crunched crackers loudly",
        tags={"snack"},
    ),
}

GIRL_NAMES = ["Lily", "Mia", "Zoe", "Ava", "Ella", "Lucy", "Anna", "Maya", "Nora", "Rose"]
BOY_NAMES = ["Ben", "Max", "Sam", "Leo", "Jack", "Finn", "Noah", "Eli", "Theo", "Owen"]
TRAITS = ["careful", "curious", "observant", "gentle", "steady", "clever"]


@dataclass
class StoryParams:
    setting: str
    act: str
    costume: str
    throat: str
    remedy: str
    detective_name: str
    detective_gender: str
    culprit_name: str
    culprit_gender: str
    teacher_type: str
    detective_trait: str
    seed: Optional[int] = None


CURATED = [
    StoryParams(
        setting="auditorium",
        act="dragon_song",
        costume="dragon",
        throat="scratchy",
        remedy="warm_tea",
        detective_name="Lily",
        detective_gender="girl",
        culprit_name="Ben",
        culprit_gender="boy",
        teacher_type="teacher_f",
        detective_trait="observant",
        seed=None,
    ),
    StoryParams(
        setting="library",
        act="owl_poem",
        costume="owl",
        throat="swollen",
        remedy="ice_pop",
        detective_name="Max",
        detective_gender="boy",
        culprit_name="Maya",
        culprit_gender="girl",
        teacher_type="teacher_f",
        detective_trait="careful",
        seed=None,
    ),
    StoryParams(
        setting="auditorium",
        act="captain_story",
        costume="captain",
        throat="swollen",
        remedy="quiet_rest",
        detective_name="Anna",
        detective_gender="girl",
        culprit_name="Theo",
        culprit_gender="boy",
        teacher_type="teacher_m",
        detective_trait="steady",
        seed=None,
    ),
    StoryParams(
        setting="playroom",
        act="owl_poem",
        costume="owl",
        throat="scratchy",
        remedy="honey_water",
        detective_name="Noah",
        detective_gender="boy",
        culprit_name="Ella",
        culprit_gender="girl",
        teacher_type="teacher_f",
        detective_trait="curious",
        seed=None,
    ),
]


def sensible_remedies() -> list[Remedy]:
    return [r for r in REMEDIES.values() if r.sense >= SENSE_MIN]


def costume_matches(act_id: str, costume_id: str) -> bool:
    return costume_id in COSTUMES and act_id in ACTS and COSTUMES[costume_id].act == act_id


def remedy_allowed(throat_id: str, remedy_id: str) -> bool:
    if throat_id not in THROAT_STATES or remedy_id not in REMEDIES:
        return False
    return remedy_id in THROAT_STATES[throat_id].allowed_remedies and REMEDIES[remedy_id].sense >= SENSE_MIN


def valid_combos() -> list[tuple[str, str, str, str, str]]:
    combos: list[tuple[str, str, str, str, str]] = []
    for setting_id, setting in SETTINGS.items():
        for act_id in sorted(setting.affordances):
            for costume_id, costume in COSTUMES.items():
                if not costume_matches(act_id, costume_id):
                    continue
                for throat_id, throat in THROAT_STATES.items():
                    for remedy_id in sorted(throat.allowed_remedies):
                        if remedy_allowed(throat_id, remedy_id):
                            combos.append((setting_id, act_id, costume_id, throat_id, remedy_id))
    return sorted(combos)


def outcome_of(params: StoryParams) -> str:
    throat = THROAT_STATES[params.throat]
    remedy = REMEDIES[params.remedy]
    return "clear" if remedy.power >= throat.severity else "soft"


def explain_rejection(setting_id: str, act_id: str, costume_id: str, throat_id: str, remedy_id: str) -> str:
    if setting_id in SETTINGS and act_id in ACTS and act_id not in SETTINGS[setting_id].affordances:
        return (
            f"(No story: {SETTINGS[setting_id].place} is not rehearsing {ACTS[act_id].title}. "
            f"Pick an act the setting actually affords.)"
        )
    if act_id in ACTS and costume_id in COSTUMES and not costume_matches(act_id, costume_id):
        return (
            f"(No story: {COSTUMES[costume_id].label} does not fit {ACTS[act_id].title}. "
            f"The clue and reveal must match the rehearsal costume.)"
        )
    if remedy_id in REMEDIES and REMEDIES[remedy_id].sense < SENSE_MIN:
        return (
            f"(No story: {REMEDIES[remedy_id].label} is not a sensible way to soothe a sore tonsil "
            f"in this world. Choose a gentle remedy instead.)"
        )
    if throat_id in THROAT_STATES and remedy_id in REMEDIES and not remedy_allowed(throat_id, remedy_id):
        return (
            f"(No story: {REMEDIES[remedy_id].label} is not one of the remedies this world allows for "
            f"{THROAT_STATES[throat_id].label}. The fix must fit the throat problem.)"
        )
    return "(No valid combination matches the given options.)"


def introduce(world: World, detective: Entity, culprit: Entity, teacher: Entity, act: Act) -> None:
    world.say(
        f"On rehearsal day in {world.setting.place}, {detective.id} stayed close to the stage steps, "
        f"because {detective.pronoun()} liked noticing little things."
    )
    world.say(world.setting.atmosphere)
    world.say(
        f"{culprit.id} was supposed to perform {act.title}, while {teacher.label_word} checked the props "
        f"and smiled at the waiting children."
    )
    detective.memes["curiosity"] += 1
    culprit.memes["hope"] += 1


def mystery_sound(world: World, detective: Entity, act: Act) -> None:
    world.para()
    world.say(
        f"Then the room heard it for the first time: {act.repeated_sound} It floated from "
        f"{world.setting.hiding_spot}."
    )
    world.say(
        f"A moment later it came again: {act.repeated_sound} Not a clear line from the rehearsal, "
        f"just the same odd little hum."
    )
    detective.memes["mystery"] += 1
    detective.meters["heard_repetition"] += 1
    world.facts["repeated_sound"] = act.repeated_sound


def find_clue(world: World, detective: Entity, act: Act, costume: Costume) -> None:
    world.say(
        f"{detective.id} walked closer and found {act.clue} on the floor. "
        f"{detective.pronoun().capitalize()} did not shout right away."
    )
    detective.meters["clues"] += 1
    world.facts["clue_found"] = costume.clue


def flashback(world: World, detective: Entity, culprit: Entity, act: Act, throat: ThroatState, costume: Costume) -> None:
    world.para()
    culprit.meters["throat_soreness"] = float(throat.severity)
    culprit.meters["voice_strength"] = max(0.0, 2.0 - float(throat.severity))
    culprit.memes["worry"] += 1
    world.say(
        f"At that moment, a small flashback blinked in {detective.id}'s mind."
    )
    world.say(
        f"Yesterday, during rehearsal, {culprit.id} had touched {culprit.pronoun('possessive')} throat and whispered "
        f'that one {throat.label} made {act.title} hard to say. {culprit.pronoun().capitalize()} had still been wearing '
        f"{costume.phrase}, and {detective.id} remembered seeing the very same clue then."
    )
    world.facts["flashback"] = True


def deduce(world: World, detective: Entity, culprit: Entity, act: Act, costume: Costume) -> None:
    world.say(
        f"{detective.id} put the two clues together: the repeated hum and {costume.clue}. "
        f'"It is not a ghost," {detective.pronoun()} said softly. "It is someone from {act.title}."'
    )
    detective.memes["confidence"] += 1
    world.facts["deduced_culprit"] = culprit.id


def reveal(world: World, detective: Entity, culprit: Entity, costume: Costume, throat: ThroatState) -> None:
    world.para()
    culprit.memes["worry"] += 1
    culprit.memes["shame"] += 1
    world.say(
        f"{detective.id} stepped to {world.setting.hiding_spot}. "
        f'"You can come out," {detective.pronoun()} said. "I think I know who you are."'
    )
    world.say(
        f"Out came {culprit.id}, half hidden in {costume.phrase}. For one second {culprit.pronoun()} looked "
        f"almost transformed into a real {ACTS[costume.act].transform_word}, but then the costume slipped, "
        f"and there was only a worried child with {throat.label}."
    )
    world.say(
        f'"I was trying to practice," {culprit.id} admitted, "but my voice kept turning into {ACTS[costume.act].repeated_sound.lower()}."'
    )
    world.facts["revealed"] = True


def comfort_and_remedy(world: World, teacher: Entity, culprit: Entity, remedy: Remedy) -> None:
    world.para()
    culprit.memes["relief"] += 1
    teacher.memes["care"] += 1
    world.say(
        f"The {teacher.label_word} knelt down beside {culprit.id}. "
        f'"That is a mystery we can solve kindly," {teacher.pronoun()} said.'
    )
    world.say(
        f"{teacher.pronoun().capitalize()} brought {remedy.phrase}, and {culprit.id} {remedy.action}."
    )
    culprit.meters["comfort"] += 1
    world.facts["remedy_used"] = remedy.label


def voice_change(world: World, detective: Entity, culprit: Entity, teacher: Entity, act: Act, params: StoryParams) -> None:
    outcome = outcome_of(params)
    culprit.memes["courage"] += 1
    culprit.memes["shame"] = 0.0
    if outcome == "clear":
        culprit.meters["voice_strength"] = 2.0
        culprit.meters["throat_soreness"] = max(0.0, culprit.meters["throat_soreness"] - 1.0)
        world.say(
            f"When {culprit.id} tried again, the voice had transformed. It was not a croaky hum now. "
            f"It came out clear: {act.line}"
        )
        world.say(
            f"{detective.id} grinned. The mystery was solved, and the stage did not sound spooky anymore."
        )
    else:
        culprit.meters["voice_strength"] = 1.0
        world.say(
            f"When {culprit.id} tried again, the voice was still soft, but it was no longer trapped in a hum. "
            f"{culprit.pronoun().capitalize()} whispered the line, and the words stayed together."
        )
        world.say(
            f'The {teacher.label_word} nodded. "{detective.id} can say it with you today," {teacher.pronoun()} said, '
            f"so the clue turned into teamwork instead of tears."
        )
        detective.memes["helpfulness"] += 1
    world.facts["outcome"] = outcome


def ending(world: World, detective: Entity, culprit: Entity, act: Act, params: StoryParams) -> None:
    world.para()
    if outcome_of(params) == "clear":
        world.say(
            f"Soon the rehearsal began again. No one whispered about ghosts now. {culprit.id} stood in the light, "
            f"lifted {culprit.pronoun('possessive')} chin, and performed {act.title} while {detective.id} listened for "
            f"the brave new sound."
        )
    else:
        world.say(
            f"Soon the rehearsal began again. This time {culprit.id} and {detective.id} stood shoulder to shoulder, "
            f"and the room listened closely instead of guessing wildly."
        )
    world.say(
        f"Once more the line came into the room -- not as {act.repeated_sound.lower()}, but as a real answer to the mystery."
    )


def tell(params: StoryParams) -> World:
    setting = SETTINGS[params.setting]
    act = ACTS[params.act]
    costume = COSTUMES[params.costume]
    throat = THROAT_STATES[params.throat]
    remedy = REMEDIES[params.remedy]

    world = World(setting=setting)
    detective = world.add(
        Entity(
            id=params.detective_name,
            kind="character",
            type=params.detective_gender,
            role="detective",
            attrs={"trait": params.detective_trait},
            tags={"detective"},
        )
    )
    culprit = world.add(
        Entity(
            id=params.culprit_name,
            kind="character",
            type=params.culprit_gender,
            role="culprit",
            tags={"performer"},
        )
    )
    teacher = world.add(
        Entity(
            id="Teacher",
            kind="character",
            type=params.teacher_type,
            label="the teacher",
            role="teacher",
            tags={"adult"},
        )
    )
    world.add(
        Entity(
            id="costume",
            kind="thing",
            type="costume",
            label=costume.label,
            phrase=costume.phrase,
            tags=set(costume.tags),
        )
    )

    introduce(world, detective, culprit, teacher, act)
    mystery_sound(world, detective, act)
    find_clue(world, detective, act, costume)
    flashback(world, detective, culprit, act, throat, costume)
    deduce(world, detective, culprit, act, costume)
    reveal(world, detective, culprit, costume, throat)
    comfort_and_remedy(world, teacher, culprit, remedy)
    voice_change(world, detective, culprit, teacher, act, params)
    ending(world, detective, culprit, act, params)

    world.facts.update(
        setting=setting,
        act=act,
        costume=costume,
        throat=throat,
        remedy=remedy,
        detective=detective,
        culprit=culprit,
        teacher=teacher,
        outcome=outcome_of(params),
        line=act.line,
    )
    return world


KNOWLEDGE = {
    "tonsil": [
        (
            "What is a tonsil?",
            "A tonsil is a small part inside your throat. When it gets sore or swollen, swallowing and talking can hurt."
        )
    ],
    "voice": [
        (
            "Why can a voice sound croaky when your throat hurts?",
            "Your throat helps shape your voice. If it is sore, the sound can come out rough, weak, or wobbly."
        )
    ],
    "flashback": [
        (
            "What is a flashback in a story?",
            "A flashback is when a story pauses the present and remembers something from earlier. That older memory can help explain what is happening now."
        )
    ],
    "whodunit": [
        (
            "What is a whodunit?",
            "A whodunit is a mystery story where someone tries to figure out who caused the puzzling event. The answer usually comes from clues."
        )
    ],
    "clue": [
        (
            "What is a clue?",
            "A clue is a small sign that helps you solve a puzzle. It can be something you hear, see, remember, or find."
        )
    ],
    "tea": [
        (
            "Why might a warm drink feel good on a sore throat?",
            "A warm drink can feel gentle and soothing on a scratchy throat. It does not solve every problem, but it can make talking feel easier."
        )
    ],
    "rest": [
        (
            "Why does resting your voice help?",
            "When you stop pushing a sore voice, the throat gets a quiet chance to calm down. That can make the next words easier to say."
        )
    ],
    "ice_pop": [
        (
            "Why can something cold help a sore throat feel better?",
            "Cold can make a sore spot feel calmer for a little while. That is why a cool treat sometimes feels gentle on a hurting throat."
        )
    ],
    "costume": [
        (
            "How can a costume make someone look transformed?",
            "A costume changes how someone looks from the outside. A child in a cape or coat can seem like a dragon, owl, or captain for a little while."
        )
    ],
}
KNOWLEDGE_ORDER = ["tonsil", "voice", "flashback", "whodunit", "clue", "tea", "rest", "ice_pop", "costume"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    detective = f["detective"]
    culprit = f["culprit"]
    act = f["act"]
    throat = f["throat"]
    remedy = f["remedy"]
    return [
        f'Write a short child-friendly whodunit that includes the word "tonsil" and uses repetition, transformation, and a flashback.',
        f"Tell a gentle mystery where {detective.id} hears {act.repeated_sound.lower()} during rehearsal, finds a clue, remembers an earlier moment, and discovers that {culprit.id} is hiding because of {throat.label}.",
        f"Write a story in which a costume makes someone look transformed, a repeated sound acts like a clue, and a kind grown-up helps solve the mystery with {remedy.label}.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    detective = f["detective"]
    culprit = f["culprit"]
    teacher = f["teacher"]
    act = f["act"]
    costume = f["costume"]
    throat = f["throat"]
    remedy = f["remedy"]
    outcome = f["outcome"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {detective.id}, who acts like a little detective, and {culprit.id}, who is hiding during rehearsal. The {teacher.label_word} helps at the end when the mystery becomes a throat problem instead of a scary problem."
        ),
        (
            "What was the mystery sound?",
            f"The mystery sound was {act.repeated_sound.lower()} coming from {world.setting.hiding_spot}. It kept repeating, so it felt like an important clue instead of a random noise."
        ),
        (
            f"What clue did {detective.id} find?",
            f"{detective.id} found {costume.clue} on the floor. That clue matched the costume from {act.title}, so it pointed toward the hidden performer."
        ),
        (
            "How did the flashback help solve the mystery?",
            f"The flashback reminded {detective.id} that yesterday {culprit.id} had touched {culprit.pronoun('possessive')} throat and mentioned {throat.label}. It also reminded {detective.pronoun('object')} that the same costume clue had been there before, so the repeated hum suddenly made sense."
        ),
        (
            f"Why was {culprit.id} hiding?",
            f"{culprit.id} was hiding because {culprit.pronoun('possessive')} voice kept turning into a croaky hum while {culprit.pronoun()} was trying to practice. {throat.label.capitalize()} made speaking feel hard, and that made {culprit.pronoun('object')} worried and embarrassed."
        ),
        (
            f"How did the {teacher.label_word} help?",
            f"The {teacher.label_word} brought {remedy.phrase} and stayed calm. That kind help changed the problem from a spooky mystery into something the children could understand and solve."
        ),
    ]
    if outcome == "clear":
        qa.append(
            (
                "How did the story end?",
                f"It ended with {culprit.id}'s voice sounding clear again, and the rehearsal could begin properly. The ending image proves the change because the repeated hum turned back into a real line from the show."
            )
        )
    else:
        qa.append(
            (
                "How did the story end?",
                f"It ended with {culprit.id}'s voice still soft, but steady enough to share the line with {detective.id}. The mystery was solved because the hum turned into words, and the children worked together instead of hiding."
            )
        )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags = {"tonsil", "voice", "flashback", "whodunit", "clue", "costume"}
    remedy = world.facts["remedy"]
    if remedy.id in {"warm_tea", "honey_water"}:
        tags.add("tea")
    if remedy.id == "quiet_rest":
        tags.add("rest")
    if remedy.id == "ice_pop":
        tags.add("ice_pop")
    out: list[tuple[str, str]] = []
    for tag in KNOWLEDGE_ORDER:
        if tag in tags:
            out.extend(KNOWLEDGE[tag])
    return out


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts -- asks that would produce this story =="]
    for i, prompt in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {prompt}")
    lines.append("")
    lines.append("== (2) Story questions -- answerable from the story text ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== (3) World-knowledge questions -- child level, no story needed ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for ent in world.entities.values():
        meters = {k: v for k, v in ent.meters.items() if v}
        memes = {k: v for k, v in ent.memes.items() if v}
        bits = []
        if ent.role:
            bits.append(f"role={ent.role}")
        if ent.attrs:
            shown = {k: v for k, v in ent.attrs.items() if v}
            if shown:
                bits.append(f"attrs={shown}")
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if ent.tags:
            bits.append(f"tags={sorted(ent.tags)}")
        lines.append(f"  {ent.id:10} ({ent.type:10}) {' '.join(bits)}")
    lines.append(f"  facts: outcome={world.facts.get('outcome')} clue={world.facts.get('clue_found')}")
    return "\n".join(lines)


ASP_RULES = r"""
valid(S, A, C, T, R) :- setting(S), affords(S, A), costume_for(C, A), throat(T), remedy(R), allowed(T, R), sensible(R).

clear(T, R) :- severity(T, Need), power(R, Pow), Pow >= Need.
soft(T, R)  :- severity(T, Need), power(R, Pow), Pow < Need.

outcome(clear) :- chosen_throat(T), chosen_remedy(R), clear(T, R).
outcome(soft)  :- chosen_throat(T), chosen_remedy(R), soft(T, R).
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for setting_id, setting in SETTINGS.items():
        lines.append(asp.fact("setting", setting_id))
        for act_id in sorted(setting.affordances):
            lines.append(asp.fact("affords", setting_id, act_id))
    for act_id in ACTS:
        lines.append(asp.fact("act", act_id))
    for costume_id, costume in COSTUMES.items():
        lines.append(asp.fact("costume", costume_id))
        lines.append(asp.fact("costume_for", costume_id, costume.act))
    for throat_id, throat in THROAT_STATES.items():
        lines.append(asp.fact("throat", throat_id))
        lines.append(asp.fact("severity", throat_id, throat.severity))
        for remedy_id in sorted(throat.allowed_remedies):
            lines.append(asp.fact("allowed", throat_id, remedy_id))
    for remedy_id, remedy in REMEDIES.items():
        lines.append(asp.fact("remedy", remedy_id))
        lines.append(asp.fact("power", remedy_id, remedy.power))
        lines.append(asp.fact("sense", remedy_id, remedy.sense))
    lines.append(asp.fact("sense_min", SENSE_MIN))
    lines.append("sensible(R) :- remedy(R), sense(R, S), sense_min(M), S >= M.")
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("", "#show valid/5."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_outcome(params: StoryParams) -> str:
    import asp

    extra = "\n".join(
        [
            asp.fact("chosen_throat", params.throat),
            asp.fact("chosen_remedy", params.remedy),
        ]
    )
    model = asp.one_model(asp_program(extra, "#show outcome/1."))
    out = asp.atoms(model, "outcome")
    return out[0][0] if out else "?"


def asp_verify() -> int:
    rc = 0
    clingo_set = set(asp_valid_combos())
    python_set = set(valid_combos())
    if clingo_set == python_set:
        print(f"OK: ASP gate matches valid_combos() ({len(clingo_set)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos:")
        if clingo_set - python_set:
            print("  only in clingo:", sorted(clingo_set - python_set))
        if python_set - clingo_set:
            print("  only in python:", sorted(python_set - clingo_set))

    cases = list(CURATED)
    for seed in range(30):
        try:
            params = resolve_params(build_parser().parse_args([]), random.Random(seed))
        except StoryError:
            continue
        params.seed = seed
        cases.append(params)
    mismatches = [p for p in cases if asp_outcome(p) != outcome_of(p)]
    if not mismatches:
        print(f"OK: ASP outcome matches outcome_of() on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {len(mismatches)}/{len(cases)} outcomes differ.")

    try:
        sample = generate(CURATED[0])
        if not sample.story.strip():
            raise StoryError("smoke test generated an empty story")
        print("OK: smoke test generated a normal story.")
    except Exception as err:  # pragma: no cover
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Tiny whodunit storyworld: a repeated hum, a costume clue, and a sore tonsil."
    )
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--act", choices=ACTS)
    ap.add_argument("--costume", choices=COSTUMES)
    ap.add_argument("--throat", choices=THROAT_STATES)
    ap.add_argument("--remedy", choices=REMEDIES)
    ap.add_argument("--teacher", dest="teacher_type", choices=["teacher_f", "teacher_m"])
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list the compatible-story set derived by clingo")
    ap.add_argument("--verify", action="store_true", help="check the inline ASP reasoner and run a smoke test")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def _pick_child(rng: random.Random, avoid: str = "") -> tuple[str, str]:
    gender = rng.choice(["girl", "boy"])
    pool = [n for n in (GIRL_NAMES if gender == "girl" else BOY_NAMES) if n != avoid]
    return rng.choice(pool), gender


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.setting and args.act and args.act not in SETTINGS[args.setting].affordances:
        raise StoryError(explain_rejection(args.setting, args.act, args.costume or "dragon", args.throat or "scratchy", args.remedy or "warm_tea"))
    if args.act and args.costume and not costume_matches(args.act, args.costume):
        raise StoryError(explain_rejection(args.setting or "auditorium", args.act, args.costume, args.throat or "scratchy", args.remedy or "warm_tea"))
    if args.remedy and args.remedy in REMEDIES and REMEDIES[args.remedy].sense < SENSE_MIN:
        raise StoryError(explain_rejection(args.setting or "auditorium", args.act or "dragon_song", args.costume or "dragon", args.throat or "scratchy", args.remedy))
    if args.throat and args.remedy and not remedy_allowed(args.throat, args.remedy):
        raise StoryError(explain_rejection(args.setting or "auditorium", args.act or "dragon_song", args.costume or "dragon", args.throat, args.remedy))

    combos = [
        combo for combo in valid_combos()
        if (args.setting is None or combo[0] == args.setting)
        and (args.act is None or combo[1] == args.act)
        and (args.costume is None or combo[2] == args.costume)
        and (args.throat is None or combo[3] == args.throat)
        and (args.remedy is None or combo[4] == args.remedy)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    setting_id, act_id, costume_id, throat_id, remedy_id = rng.choice(sorted(combos))
    detective_name, detective_gender = _pick_child(rng)
    culprit_name, culprit_gender = _pick_child(rng, avoid=detective_name)
    teacher_type = args.teacher_type or rng.choice(["teacher_f", "teacher_m"])
    detective_trait = rng.choice(TRAITS)
    return StoryParams(
        setting=setting_id,
        act=act_id,
        costume=costume_id,
        throat=throat_id,
        remedy=remedy_id,
        detective_name=detective_name,
        detective_gender=detective_gender,
        culprit_name=culprit_name,
        culprit_gender=culprit_gender,
        teacher_type=teacher_type,
        detective_trait=detective_trait,
        seed=None,
    )


def generate(params: StoryParams) -> StorySample:
    for field_name, registry in [
        ("setting", SETTINGS),
        ("act", ACTS),
        ("costume", COSTUMES),
        ("throat", THROAT_STATES),
        ("remedy", REMEDIES),
    ]:
        value = getattr(params, field_name)
        if value not in registry:
            raise StoryError(f"(Invalid {field_name}: {value})")
    if params.teacher_type not in {"teacher_f", "teacher_m"}:
        raise StoryError(f"(Invalid teacher type: {params.teacher_type})")
    if params.act not in SETTINGS[params.setting].affordances:
        raise StoryError(explain_rejection(params.setting, params.act, params.costume, params.throat, params.remedy))
    if not costume_matches(params.act, params.costume):
        raise StoryError(explain_rejection(params.setting, params.act, params.costume, params.throat, params.remedy))
    if not remedy_allowed(params.throat, params.remedy):
        raise StoryError(explain_rejection(params.setting, params.act, params.costume, params.throat, params.remedy))

    world = tell(params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=[QAItem(question=q, answer=a) for q, a in story_qa(world)],
        world_qa=[QAItem(question=q, answer=a) for q, a in world_knowledge_qa(world)],
        world=world,
    )


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world is not None:
        print(dump_trace(sample.world))
    if qa:
        print()
        print(format_qa(sample))


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("", "#show valid/5.\n#show outcome/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (setting, act, costume, throat, remedy) combos:\n")
        for setting_id, act_id, costume_id, throat_id, remedy_id in combos:
            print(f"  {setting_id:10} {act_id:13} {costume_id:8} {throat_id:8} {remedy_id}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)

    samples: list[StorySample] = []
    if args.all:
        for p in CURATED:
            samples.append(generate(p))
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 50, 50):
            seed = base_seed + i
            i += 1
            try:
                params = resolve_params(args, random.Random(seed))
            except StoryError as err:
                print(err)
                return
            params.seed = seed
            sample = generate(params)
            if sample.story in seen:
                continue
            seen.add(sample.story)
            samples.append(sample)

    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.detective_name} solves {p.culprit_name}'s rehearsal mystery ({p.act}, {outcome_of(p)})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()

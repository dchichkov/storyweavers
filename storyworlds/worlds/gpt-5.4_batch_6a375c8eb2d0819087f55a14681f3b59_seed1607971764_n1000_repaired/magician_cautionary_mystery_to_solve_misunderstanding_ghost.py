#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/magician_cautionary_mystery_to_solve_misunderstanding_ghost.py
===========================================================================================

A standalone story world about a child who mistakes a spooky sight for a ghost
when a magician is preparing a show in an old building. The little mystery is
solved through world state, not by swapping nouns into one paragraph: a strange
sign appears, a child misunderstands it, a friend warns against sneaking in the
dark, and the truth is uncovered safely.

The domain aims for a child-facing "ghost story" feeling without real horror:
creaky boards, dim corners, drifting cloth, whispery sounds, and then a gentle
reveal. It is cautionary because the misunderstanding tempts the child to
investigate unsafely; the resolution teaches that mysteries should be checked
with a grown-up, not by creeping into dark places alone.

Run it
------
    python storyworlds/worlds/gpt-5.4/magician_cautionary_mystery_to_solve_misunderstanding_ghost.py
    python storyworlds/worlds/gpt-5.4/magician_cautionary_mystery_to_solve_misunderstanding_ghost.py --venue theater --sign floating_shape
    python storyworlds/worlds/gpt-5.4/magician_cautionary_mystery_to_solve_misunderstanding_ghost.py --reveal vent_dummy
    python storyworlds/worlds/gpt-5.4/magician_cautionary_mystery_to_solve_misunderstanding_ghost.py --all
    python storyworlds/worlds/gpt-5.4/magician_cautionary_mystery_to_solve_misunderstanding_ghost.py -n 5 --seed 7 --qa
    python storyworlds/worlds/gpt-5.4/magician_cautionary_mystery_to_solve_misunderstanding_ghost.py --verify
"""

from __future__ import annotations

import argparse
import copy
import json
import os
import random
import sys
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Callable, Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from results import QAItem, StoryError, StorySample  # noqa: E402

THRESHOLD = 1.0
BOLDNESS_INIT = 6.0
CAUTIOUS_TRAITS = {"careful", "cautious", "steady", "sensible"}


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    traits: list[str] = field(default_factory=list)
    role: str = ""
    age: int = 0
    attrs: dict = field(default_factory=dict)
    portable: bool = False
    spooky: bool = False
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "aunt", "woman"}
        male = {"boy", "father", "uncle", "man", "magician"}
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
            "aunt": "aunt",
            "uncle": "uncle",
        }.get(self.type, self.type)
    @property
    def phrase(self) -> str:
        return str(getattr(self, "_phrase", None) or getattr(self, "label_word", None) or getattr(self, "label", None) or getattr(self, "id", self.__class__.__name__.lower()))

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)

    @property
    def tags(self):
        if not hasattr(self, "_tags"):
            object.__setattr__(self, "_tags", set())
        return self._tags


@dataclass
class Venue:
    id: str
    label: str
    opening: str
    spooky_place: str
    floor_detail: str
    helper_place: str
    affords: set[str] = field(default_factory=set)
    tags: set[str] = field(default_factory=set)
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def phrase(self) -> str:
        return str(getattr(self, "_phrase", None) or getattr(self, "label_word", None) or getattr(self, "label", None) or getattr(self, "id", self.__class__.__name__.lower()))

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)

    @property
    def meters(self):
        if not hasattr(self, "_meters"):
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if not hasattr(self, "_memes"):
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes


@dataclass
class Sign:
    id: str
    label: str
    appear_text: str
    guess_text: str
    tags: set[str] = field(default_factory=set)
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def phrase(self) -> str:
        return str(getattr(self, "_phrase", None) or getattr(self, "label_word", None) or getattr(self, "label", None) or getattr(self, "id", self.__class__.__name__.lower()))

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)

    @property
    def meters(self):
        if not hasattr(self, "_meters"):
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if not hasattr(self, "_memes"):
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes


@dataclass
class Reveal:
    id: str
    sign: str
    label: str
    setup_text: str
    explain_text: str
    proof_text: str
    safe_item: str
    tags: set[str] = field(default_factory=set)
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def phrase(self) -> str:
        return str(getattr(self, "_phrase", None) or getattr(self, "label_word", None) or getattr(self, "label", None) or getattr(self, "id", self.__class__.__name__.lower()))

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)

    @property
    def meters(self):
        if not hasattr(self, "_meters"):
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if not hasattr(self, "_memes"):
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes


@dataclass
class Hazard:
    id: str
    label: str
    warning_text: str
    stumble_text: str
    tags: set[str] = field(default_factory=set)
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def phrase(self) -> str:
        return str(getattr(self, "_phrase", None) or getattr(self, "label_word", None) or getattr(self, "label", None) or getattr(self, "id", self.__class__.__name__.lower()))

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)

    @property
    def meters(self):
        if not hasattr(self, "_meters"):
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if not hasattr(self, "_memes"):
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes


@dataclass
class Rule:
    name: str
    tag: str
    apply: Callable[["World"], list[str]]
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def phrase(self) -> str:
        return str(getattr(self, "_phrase", None) or getattr(self, "label_word", None) or getattr(self, "label", None) or getattr(self, "id", self.__class__.__name__.lower()))

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)

    @property
    def meters(self):
        if not hasattr(self, "_meters"):
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if not hasattr(self, "_memes"):
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes

    @property
    def tags(self):
        if not hasattr(self, "_tags"):
            object.__setattr__(self, "_tags", set())
        return self._tags


class World:
    def __init__(self, venue: Venue) -> None:
        self.venue = venue
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str) -> Entity:
        if eid not in self.entities:
            label = str(eid).replace("_", " ")
            self.entities[eid] = Entity(str(eid), label=label)
        return self.entities[eid]

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)

    def copy(self) -> "World":
        clone = World(self.venue)
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        clone.facts = copy.deepcopy(self.facts)
        return clone


def _r_spooky_fear(world: World) -> list[str]:
    room = world.get("room")
    if room.meters["spooky_sign"] < THRESHOLD:
        return []
    sig = ("spooky_fear",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    for eid in ("hero", "friend"):
        if eid in world.entities:
            world.get(eid).memes["fear"] += 1
            world.get(eid).memes["wonder"] += 1
    room.meters["mystery"] += 1
    return []


def _r_dark_danger(world: World) -> list[str]:
    hero = world.get("hero")
    room = world.get("room")
    if hero.meters["sneaking"] < THRESHOLD:
        return []
    if room.meters["dark"] < THRESHOLD:
        return []
    sig = ("dark_danger",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    hero.meters["danger"] += 1
    hero.memes["fear"] += 1
    room.meters["risk"] += 1
    return []


def _r_reveal_relief(world: World) -> list[str]:
    room = world.get("room")
    if room.meters["explained"] < THRESHOLD:
        return []
    sig = ("reveal_relief",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    for eid in ("hero", "friend"):
        if eid in world.entities:
            world.get(eid).memes["fear"] = 0.0
            world.get(eid).memes["relief"] += 1
            world.get(eid).memes["curiosity"] += 1
    room.meters["mystery"] = 0.0
    return []


CAUSAL_RULES = [
    Rule(name="spooky_fear", tag="emotional", apply=_r_spooky_fear),
    Rule(name="dark_danger", tag="physical", apply=_r_dark_danger),
    Rule(name="reveal_relief", tag="social", apply=_r_reveal_relief),
]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
        changed = False
        for rule in CAUSAL_RULES:
            sents = rule.apply(world)
            if sents:
                changed = True
                produced.extend(sents)
    if narrate:
        for sent in produced:
            world.say(sent)
    return produced


def initial_caution(trait: str) -> float:
    return 5.0 if trait in CAUTIOUS_TRAITS else 3.0


def would_wait(relation: str, hero_age: int, friend_age: int, trait: str) -> bool:
    friend_older = relation == "siblings" and friend_age > hero_age
    authority = initial_caution(trait) + 1.0 + (4.0 if friend_older else 0.0)
    return friend_older and authority > BOLDNESS_INIT


def sign_explained(sign: Sign, reveal: Reveal) -> bool:
    return reveal.sign == sign.id


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for venue_id, venue in VENUES.items():
        for sign_id, sign in SIGNS.items():
            for reveal_id, reveal in REVEALS.items():
                if sign_explained(sign, reveal) and reveal_id in venue.affords:
                    combos.append((venue_id, sign_id, reveal_id))
    return combos


def predict_sneak(world: World, hazard: Hazard) -> dict:
    sim = world.copy()
    hero = sim.get("hero")
    room = sim.get("room")
    hero.meters["sneaking"] += 1
    room.meters["dark"] += 1
    propagate(sim, narrate=False)
    return {
        "danger": hero.meters["danger"],
        "risk": room.meters["risk"],
        "hazard": hazard.label,
    }


def introduce(world: World, hero: Entity, friend: Entity, caretaker: Entity, venue: Venue) -> None:
    world.say(
        f"On a dusky evening, {hero.id} and {friend.id} went with {hero.pronoun('possessive')} "
        f"{caretaker.label_word} to {venue.label}. {venue.opening}"
    )
    world.say(
        f"A visiting magician was getting ready there, and the whole place felt full of velvet, "
        f"whispers, and waiting."
    )


def set_scene(world: World, magician: Entity, reveal: Reveal, venue: Venue) -> None:
    world.say(
        f"{magician.id} had been practicing near {venue.helper_place}, where {reveal.setup_text}"
    )


def spooky_moment(world: World, hero: Entity, friend: Entity, sign: Sign) -> None:
    room = world.get("room")
    room.meters["spooky_sign"] += 1
    propagate(world, narrate=False)
    world.say(sign.appear_text)
    world.say(
        f'"A ghost!" {hero.id} whispered. {friend.id} grabbed {hero.pronoun("possessive")} sleeve, '
        f"and both children listened to the dark a little harder than before."
    )
    hero.memes["misunderstanding"] += 1
    friend.memes["worry"] += 1
    world.facts["guess"] = sign.guess_text


def tempt(world: World, hero: Entity, venue: Venue) -> None:
    hero.memes["boldness"] += 1
    world.say(
        f'"I can solve it," {hero.id} said, staring toward {venue.spooky_place}. '
        f"The mystery tugged at {hero.pronoun('object')} like a string."
    )


def warn(world: World, friend: Entity, hero: Entity, caretaker: Entity, hazard: Hazard) -> None:
    pred = predict_sneak(world, hazard)
    world.facts["predicted_danger"] = pred["danger"]
    world.facts["predicted_hazard"] = pred["hazard"]
    friend.memes["caution"] += 1
    extra = ""
    if friend.memes["caution"] >= 6:
        extra = f" {friend.pronoun().capitalize()} already felt sure the dark was hiding a bad step."
    world.say(
        f'{friend.id} shook {friend.pronoun("possessive")} head. "Do not go alone," '
        f'{friend.pronoun()} said. "{hazard.warning_text} Let\'s get {caretaker.label_word} first."{extra}'
    )


def back_down(world: World, hero: Entity, friend: Entity, caretaker: Entity) -> None:
    hero.memes["boldness"] = 0.0
    hero.memes["relief"] += 1
    friend.memes["relief"] += 1
    world.say(
        f"{hero.id} looked into the shadows, then back at {friend.id}, and the brave idea shrank. "
        f"Together they hurried to find {caretaker.label_word} instead of creeping away alone."
    )


def sneak(world: World, hero: Entity, friend: Entity, venue: Venue) -> None:
    hero.meters["sneaking"] += 1
    world.get("room").meters["dark"] += 1
    propagate(world, narrate=False)
    world.say(
        f'But {hero.id} slipped toward {venue.spooky_place} anyway, one slow step after another. '
        f'{friend.id} followed close behind, whispering for {hero.pronoun("object")} to come back.'
    )


def stumble(world: World, hero: Entity, hazard: Hazard) -> None:
    hero.meters["stumbled"] += 1
    world.say(hazard.stumble_text)
    world.say(
        f"{hero.id}'s heart thumped hard. All at once, solving the mystery alone did not feel clever at all."
    )


def arrive_help(world: World, caretaker: Entity, magician: Entity) -> None:
    world.say(
        f"Before anything worse could happen, {caretaker.label_word.capitalize()} and {magician.id} came hurrying over with a lamp."
    )


def solve_mystery(world: World, magician: Entity, reveal: Reveal, sign: Sign) -> None:
    room = world.get("room")
    room.meters["explained"] += 1
    propagate(world, narrate=False)
    world.say(
        f'{magician.id} blinked, then smiled kindly. "{sign.guess_text} is not a ghost," '
        f'{magician.pronoun()} said. "{reveal.explain_text}"'
    )
    world.say(reveal.proof_text)
    magician.memes["kindness"] += 1
    world.facts["solved"] = True


def lesson(world: World, caretaker: Entity, hero: Entity, friend: Entity, hazard: Hazard) -> None:
    hero.memes["lesson"] += 1
    friend.memes["lesson"] += 1
    world.say(
        f"{caretaker.label_word.capitalize()} knelt beside them. "
        f'"Old places can feel spooky," {caretaker.pronoun()} said softly, '
        f'"but dark corners can hide real dangers, like {hazard.label}. '
        f'If something seems strange, call a grown-up. Do not sneak off to prove a guess."'
    )
    world.say(
        f"{hero.id} nodded, and {friend.id} nodded too. The mystery had been real, but the ghost had only been a misunderstanding."
    )


def ending(world: World, magician: Entity, hero: Entity, friend: Entity, reveal: Reveal) -> None:
    hero.memes["joy"] += 1
    friend.memes["joy"] += 1
    world.say(
        f"To show there was nothing to fear, {magician.id} let them stand beside {reveal.safe_item} while {magician.pronoun()} explained the trick."
    )
    world.say(
        f"In the warm lamplight, the room no longer felt haunted at all. It felt like a place where careful eyes could turn a fright into a solved mystery."
    )


def tell(
    venue: Venue,
    sign: Sign,
    reveal: Reveal,
    hazard: Hazard,
    hero_name: str = "Nora",
    hero_gender: str = "girl",
    friend_name: str = "Ben",
    friend_gender: str = "boy",
    trait: str = "careful",
    caretaker_type: str = "mother",
    relation: str = "siblings",
    hero_age: int = 5,
    friend_age: int = 7,
    trust: int = 6,
) -> World:
    world = World(venue)

    hero = world.add(Entity(
        id=hero_name,
        kind="character",
        type=hero_gender,
        role="hero",
        age=hero_age,
        traits=["curious"],
        attrs={"relation": relation},
    ))
    friend = world.add(Entity(
        id=friend_name,
        kind="character",
        type=friend_gender,
        role="friend",
        age=friend_age,
        traits=[trait],
        attrs={"relation": relation, "trust": trust},
    ))
    caretaker = world.add(Entity(
        id="Caretaker",
        kind="character",
        type=caretaker_type,
        role="caretaker",
        label="the grown-up",
    ))
    magician = world.add(Entity(
        id="Mr. Vale",
        kind="character",
        type="magician",
        role="magician",
        label="the magician",
    ))
    room = world.add(Entity(
        id="room",
        type="room",
        label=venue.label,
        attrs={"spooky_place": venue.spooky_place},
    ))
    prop = world.add(Entity(
        id="prop",
        type="prop",
        label=reveal.label,
        portable=True,
        spooky=True,
    ))
    hazard_ent = world.add(Entity(
        id="hazard",
        type="hazard",
        label=hazard.label,
        attrs={"warning": hazard.warning_text},
    ))

    hero.memes["boldness"] = BOLDNESS_INIT
    friend.memes["trust"] = float(trust)
    friend.memes["caution"] = initial_caution(trait)
    room.meters["dark"] = 1.0

    world.facts.update(
        venue=venue,
        sign=sign,
        reveal=reveal,
        hazard_cfg=hazard,
        hero=hero,
        friend=friend,
        caretaker=caretaker,
        magician=magician,
        room=room,
        relation=relation,
        solved=False,
    )

    introduce(world, hero, friend, caretaker, venue)
    set_scene(world, magician, reveal, venue)

    world.para()
    spooky_moment(world, hero, friend, sign)
    tempt(world, hero, venue)
    warn(world, friend, hero, caretaker, hazard)

    waited = would_wait(relation, hero_age, friend_age, trait)
    world.facts["waited"] = waited

    world.para()
    if waited:
        back_down(world, hero, friend, caretaker)
        arrive_help(world, caretaker, magician)
    else:
        sneak(world, hero, friend, venue)
        stumble(world, hero, hazard)
        arrive_help(world, caretaker, magician)

    solve_mystery(world, magician, reveal, sign)
    lesson(world, caretaker, hero, friend, hazard)

    world.para()
    ending(world, magician, hero, friend, reveal)

    world.facts.update(
        outcome="waited" if waited else "sneaked",
        danger=hero.meters["danger"],
        stumbled=hero.meters["stumbled"] >= THRESHOLD,
        learned=hero.memes["lesson"] >= THRESHOLD,
    )
    return world


VENUES = {
    "theater": Venue(
        id="theater",
        label="the old theater",
        opening="Dusty gold stars were painted over the stage, and every whisper seemed to float twice.",
        spooky_place="the backstage curtains",
        floor_detail="the boards were uneven behind the curtain",
        helper_place="the side stage",
        affords={"fan_scarf", "moon_mask", "vent_dummy"},
        tags={"theater"},
    ),
    "town_hall": Venue(
        id="town_hall",
        label="the creaky town hall",
        opening="The long room smelled of polish and old wood, and the rafters kept every tiny sound.",
        spooky_place="the meeting-room stage",
        floor_detail="a loose step waited near the little stage",
        helper_place="the front table",
        affords={"fan_scarf", "vent_dummy"},
        tags={"hall"},
    ),
    "museum_room": Venue(
        id="museum_room",
        label="the museum's evening lecture room",
        opening="Glass cases glimmered in the corners, and the shadows looked taller than they really were.",
        spooky_place="the storage curtain by the display room",
        floor_detail="stacked trunks stood by the curtain",
        helper_place="the display table",
        affords={"moon_mask", "vent_dummy"},
        tags={"museum"},
    ),
}

SIGNS = {
    "floating_shape": Sign(
        id="floating_shape",
        label="a floating white shape",
        appear_text="From the dim end of the room, something pale lifted, drifted, and dipped again as if a little ghost were trying to fly.",
        guess_text="That floating shape",
        tags={"ghost", "cloth"},
    ),
    "glowing_face": Sign(
        id="glowing_face",
        label="a glowing face",
        appear_text="A round face gleamed in the dark for one breath, bright as milk in moonlight, and then vanished behind a curtain.",
        guess_text="That glowing face",
        tags={"ghost", "light"},
    ),
    "whisper_voice": Sign(
        id="whisper_voice",
        label="a whispering voice",
        appear_text='From nowhere they could see, a papery little voice said, "Who is there?" and the words slid through the room like a draft.',
        guess_text="That whispering voice",
        tags={"ghost", "voice"},
    ),
}

REVEALS = {
    "fan_scarf": Reveal(
        id="fan_scarf",
        sign="floating_shape",
        label="a long white silk scarf",
        setup_text="a small practice fan kept lifting a long white silk scarf",
        explain_text="the fan was puffing my silk scarf into the air while I sorted my cards",
        proof_text="He switched the fan on again, and the scarf rose and fluttered exactly the same way. What had seemed like a ghost now looked like a soft piece of stage silk dancing in a breeze.",
        safe_item="the practice fan",
        tags={"fan", "silk", "magician"},
    ),
    "moon_mask": Reveal(
        id="moon_mask",
        sign="glowing_face",
        label="a painted moon mask",
        setup_text="a painted moon mask had been left leaning near a lamp and a mirror",
        explain_text="the moon mask caught the lamp and flashed when the curtain moved",
        proof_text="He tipped the lamp and pulled the curtain gently. The painted mask gleamed once more, and this time the children could see the smiling moon face on its stick.",
        safe_item="the painted moon mask",
        tags={"mask", "light", "magician"},
    ),
    "vent_dummy": Reveal(
        id="vent_dummy",
        sign="whisper_voice",
        label="a little ventriloquist dummy",
        setup_text="a little ventriloquist dummy was resting on a chair beside his case",
        explain_text="I was practicing my ventriloquist dummy voice from behind the curtain",
        proof_text="He stepped behind the curtain and made the same tiny voice speak again. Then he came out holding the dummy, whose wooden mouth tipped open and shut.",
        safe_item="the little dummy",
        tags={"voice", "dummy", "magician"},
    ),
}

HAZARDS = {
    "loose_step": Hazard(
        id="loose_step",
        label="a loose step in the dark",
        warning_text="there might be a loose step in the dark",
        stumble_text="Then one board tipped under {hero}, and {hero} windmilled both arms before catching balance."
    ),
    "stacked_trunks": Hazard(
        id="stacked_trunks",
        label="stacked trunks that could topple",
        warning_text="stacked trunks could be hiding in the shadows",
        stumble_text="{hero} brushed a pile of stacked trunks, and one gave a hollow thump that made both children jump."
    ),
    "curtain_rope": Hazard(
        id="curtain_rope",
        label="a curtain rope across the floor",
        warning_text="a curtain rope could be lying across the floor",
        stumble_text="{hero}'s shoe caught on a curtain rope, and {hero} stumbled forward with a gasp."
    ),
}

HAZARD_BY_VENUE = {
    "theater": "curtain_rope",
    "town_hall": "loose_step",
    "museum_room": "stacked_trunks",
}

GIRL_NAMES = ["Nora", "Lily", "Mia", "Ava", "Ella", "Rose", "Lucy", "June"]
BOY_NAMES = ["Ben", "Theo", "Sam", "Max", "Leo", "Finn", "Eli", "Jack"]
TRAITS = ["careful", "cautious", "steady", "curious", "brave", "sensible"]


@dataclass
class StoryParams:
    venue: str
    sign: str
    reveal: str
    hero: str
    hero_gender: str
    friend: str
    friend_gender: str
    caretaker: str
    trait: str
    relation: str = "siblings"
    hero_age: int = 5
    friend_age: int = 7
    trust: int = 6
    seed: Optional[int] = None
    @property
    def meters(self):
        if not hasattr(self, "_meters"):
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if not hasattr(self, "_memes"):
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes

    @property
    def tags(self):
        if not hasattr(self, "_tags"):
            object.__setattr__(self, "_tags", set())
        return self._tags


KNOWLEDGE = {
    "ghost_story": [
        (
            "Why can old rooms seem spooky at night?",
            "Dim light makes shapes harder to understand, and quiet rooms can make tiny sounds seem bigger. Your brain may guess something scary before you know what it really is."
        )
    ],
    "misunderstanding": [
        (
            "What is a misunderstanding?",
            "A misunderstanding happens when someone guesses wrong about what they saw or heard. It can feel very real until someone checks the facts."
        )
    ],
    "magician": [
        (
            "What does a magician do?",
            "A magician uses practice, props, and clever tricks to surprise people. The tricks can look mysterious even when nothing spooky is happening."
        )
    ],
    "dark": [
        (
            "Why is it unsafe to walk alone in the dark?",
            "In the dark, it is harder to see steps, ropes, and other things near your feet. That is why grown-ups want children to ask for help instead of sneaking off alone."
        )
    ],
    "fan": [
        (
            "What can a fan do to a light cloth?",
            "A fan can push air under a light cloth and make it lift, flutter, or wave. In dim light, that moving cloth can look like something alive."
        )
    ],
    "mask": [
        (
            "Why can a mask look spooky in dim light?",
            "A mask has a face shape already, so a quick flash of light can make it seem real for a moment. When you see the whole object clearly, it is not frightening anymore."
        )
    ],
    "dummy": [
        (
            "What is a ventriloquist dummy?",
            "A ventriloquist dummy is a puppet used with a voice trick. The speaker can make it seem as if the voice is coming from the puppet instead of from a person."
        )
    ],
}
KNOWLEDGE_ORDER = ["ghost_story", "misunderstanding", "magician", "dark", "fan", "mask", "dummy"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    friend = f["friend"]
    venue = f["venue"]
    sign = f["sign"]
    reveal = f["reveal"]
    if f["outcome"] == "waited":
        return [
            f'Write a gentle ghost-story mystery for a 3-to-5-year-old that includes the word "magician" and begins in {venue.label}.',
            f"Tell a story where {hero.id} thinks {sign.label} is a ghost, but {friend.id} insists on getting a grown-up before anyone sneaks into the dark.",
            f"Write a cautionary misunderstanding story where a magician's {reveal.label} is mistaken for a ghost, and the children solve the mystery safely."
        ]
    return [
        f'Write a child-facing ghost-story mystery that includes the word "magician" and happens in {venue.label}.',
        f"Tell a cautionary story where {hero.id} misunderstands {sign.label}, sneaks toward the dark, and learns that the safer way to solve a mystery is to get help.",
        f"Write a spooky-but-gentle story where a magician's {reveal.label} is mistaken for a ghost before the mystery is explained."
    ]


def pair_noun(hero: Entity, friend: Entity, relation: str) -> str:
    if relation == "siblings":
        if hero.type == "boy" and friend.type == "boy":
            return "two brothers"
        if hero.type == "girl" and friend.type == "girl":
            return "two sisters"
        return "a brother and a sister"
    return "two friends"


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    hero = f["hero"]
    friend = f["friend"]
    caretaker = f["caretaker"]
    magician = f["magician"]
    venue = f["venue"]
    sign = f["sign"]
    reveal = f["reveal"]
    hazard = f["hazard_cfg"]
    relation = f["relation"]
    pair = pair_noun(hero, friend, relation)
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {pair}, {hero.id} and {friend.id}, a visiting magician named {magician.id}, and their {caretaker.label_word}. They all meet in {venue.label}, where the mystery begins."
        ),
        (
            "What did the children think they saw?",
            f"They thought {sign.label} was a ghost. That was a misunderstanding, because the strange sight had a real cause instead of a spooky one."
        ),
        (
            f"Why did {friend.id} tell {hero.id} not to go alone?",
            f"{friend.id} worried that the dark could hide {hazard.label}. The warning was about a real safety risk, even though the ghost guess itself was wrong."
        ),
    ]
    if f["outcome"] == "waited":
        qa.append(
            (
                f"How was the mystery solved?",
                f"{hero.id} listened, got a grown-up, and then {magician.id} explained the truth. {reveal.explain_text.capitalize()}, so what looked spooky was really part of a trick."
            )
        )
    else:
        qa.append(
            (
                f"What happened when {hero.id} tried to solve the mystery alone?",
                f"{hero.id} sneaked toward the dark and ran into trouble before the truth was known. That frightening moment showed why mysteries should be checked safely instead of by creeping off alone."
            )
        )
    qa.append(
        (
            "What was the 'ghost' really?",
            f"It was {reveal.label}, part of the magician's practice. {reveal.proof_text.split('. ')[0]}."
        )
    )
    qa.append(
        (
            "What did the children learn at the end?",
            f"They learned that scary guesses can be misunderstandings. They also learned to call a grown-up when something strange happens, because dark places can hide real dangers even when there is no ghost."
        )
    )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags: set[str] = {"ghost_story", "misunderstanding", "magician", "dark"}
    reveal = world.facts["reveal"]
    if reveal.id == "fan_scarf":
        tags.add("fan")
    elif reveal.id == "moon_mask":
        tags.add("mask")
    elif reveal.id == "vent_dummy":
        tags.add("dummy")
    out: list[tuple[str, str]] = []
    for tag in KNOWLEDGE_ORDER:
        if tag in tags:
            out.extend(KNOWLEDGE[tag])
    return out


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts -- asks that would produce this story =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
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
    for e in list(world.entities.values()):
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if e.role:
            bits.append(f"role={e.role}")
        if e.age:
            bits.append(f"age={e.age}")
        if e.attrs:
            shown = {k: v for k, v in e.attrs.items() if v}
            if shown:
                bits.append(f"attrs={shown}")
        lines.append(f"  {e.id:10} ({e.type:10}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        venue="theater",
        sign="floating_shape",
        reveal="fan_scarf",
        hero="Nora",
        hero_gender="girl",
        friend="Ben",
        friend_gender="boy",
        caretaker="mother",
        trait="careful",
        relation="siblings",
        hero_age=5,
        friend_age=7,
        trust=7,
    ),
    StoryParams(
        venue="town_hall",
        sign="whisper_voice",
        reveal="vent_dummy",
        hero="Theo",
        hero_gender="boy",
        friend="Mia",
        friend_gender="girl",
        caretaker="father",
        trait="curious",
        relation="friends",
        hero_age=6,
        friend_age=6,
        trust=4,
    ),
    StoryParams(
        venue="museum_room",
        sign="glowing_face",
        reveal="moon_mask",
        hero="Ella",
        hero_gender="girl",
        friend="Rose",
        friend_gender="girl",
        caretaker="aunt",
        trait="sensible",
        relation="siblings",
        hero_age=4,
        friend_age=8,
        trust=6,
    ),
    StoryParams(
        venue="theater",
        sign="whisper_voice",
        reveal="vent_dummy",
        hero="Finn",
        hero_gender="boy",
        friend="Jack",
        friend_gender="boy",
        caretaker="uncle",
        trait="steady",
        relation="siblings",
        hero_age=5,
        friend_age=7,
        trust=5,
    ),
    StoryParams(
        venue="town_hall",
        sign="floating_shape",
        reveal="fan_scarf",
        hero="Lucy",
        hero_gender="girl",
        friend="Max",
        friend_gender="boy",
        caretaker="mother",
        trait="brave",
        relation="friends",
        hero_age=6,
        friend_age=6,
        trust=3,
    ),
]


def explain_rejection(sign: Sign, reveal: Reveal, venue: Venue) -> str:
    if not sign_explained(sign, reveal):
        return (
            f"(No story: {reveal.label} would not honestly create {sign.label}. "
            f"The mystery must have a real explanation that matches what the children noticed.)"
        )
    if reveal.id not in venue.affords:
        return (
            f"(No story: {venue.label} does not fit that magician setup. "
            f"Pick a reveal that belongs in this place.)"
        )
    return "(No story: this combination does not make a reasonable mystery.)"


def explain_gender(name: str, gender: str) -> str:
    return f"(No story: the provided name {name!r} does not match gender {gender!r} in this tiny registry.)"


ASP_RULES = r"""
explains(S, R) :- reveal_sign(R, S).
valid(V, S, R) :- venue(V), sign(S), reveal(R), explains(S, R), affords(V, R).

cautious_now(T) :- trait(T), is_cautious(T).
init_caution(5) :- trait(T), cautious_now(T).
init_caution(3) :- trait(T), not cautious_now(T).
friend_older :- relation(siblings), hero_age(H), friend_age(F), F > H.
bonus(4) :- friend_older.
bonus(0) :- not friend_older.
authority(C + 1 + B) :- init_caution(C), bonus(B).
waited :- friend_older, authority(A), boldness_init(B), A > B.

outcome(waited) :- waited.
outcome(sneaked) :- not waited.
"""

def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for venue_id, venue in VENUES.items():
        lines.append(asp.fact("venue", venue_id))
        for reveal_id in sorted(venue.affords):
            lines.append(asp.fact("affords", venue_id, reveal_id))
    for sign_id in SIGNS:
        lines.append(asp.fact("sign", sign_id))
    for reveal_id, reveal in REVEALS.items():
        lines.append(asp.fact("reveal", reveal_id))
        lines.append(asp.fact("reveal_sign", reveal_id, reveal.sign))
    for trait in sorted(CAUTIOUS_TRAITS):
        lines.append(asp.fact("is_cautious", trait))
    lines.append(asp.fact("boldness_init", int(BOLDNESS_INIT)))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("", "#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def outcome_of(params: StoryParams) -> str:
    return "waited" if would_wait(params.relation, params.hero_age, params.friend_age, params.trait) else "sneaked"


def asp_outcome(params: StoryParams) -> str:
    import asp

    extra = "\n".join([
        asp.fact("relation", params.relation),
        asp.fact("hero_age", params.hero_age),
        asp.fact("friend_age", params.friend_age),
        asp.fact("trait", params.trait),
    ])
    model = asp.one_model(asp_program(extra, "#show outcome/1."))
    out = asp.atoms(model, "outcome")
    return out[0][0] if out else "?"


def smoke_test() -> None:
    params = CURATED[0]
    sample = generate(params)
    if not sample.story.strip():
        raise StoryError("(Smoke test failed: generated story is empty.)")
    emit(sample, trace=False, qa=False, header="")


def asp_verify() -> int:
    rc = 0
    clingo_set = set(asp_valid_combos())
    python_set = set(valid_combos())
    if clingo_set == python_set:
        print(f"OK: gate matches valid_combos() ({len(clingo_set)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos:")
        if clingo_set - python_set:
            print("  only in clingo:", sorted(clingo_set - python_set))
        if python_set - clingo_set:
            print("  only in python:", sorted(python_set - clingo_set))

    cases = list(CURATED)
    for seed in range(100):
        try:
            args = build_parser().parse_args([])
            cases.append(resolve_params(args, random.Random(seed)))
        except StoryError:
            continue
    bad = sum(1 for p in cases if asp_outcome(p) != outcome_of(p))
    if bad == 0:
        print(f"OK: outcome model matches outcome_of() on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {bad}/{len(cases)} outcomes differ.")

    try:
        smoke_test()
        print("OK: smoke test generated and emitted a normal story.")
    except Exception as err:
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Story world: a child mistakes a magician's prop for a ghost and learns to solve mysteries safely."
    )
    ap.add_argument("--venue", choices=VENUES)
    ap.add_argument("--sign", choices=SIGNS)
    ap.add_argument("--reveal", choices=REVEALS)
    ap.add_argument("--caretaker", choices=["mother", "father", "aunt", "uncle"])
    ap.add_argument("--relation", choices=["siblings", "friends"])
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list compatible (venue, sign, reveal) combos derived by clingo")
    ap.add_argument("--verify", action="store_true", help="check the inline ASP twin and run a smoke test")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def _pick_name(rng: random.Random, gender: str, avoid: str = "") -> str:
    pool = GIRL_NAMES if gender == "girl" else BOY_NAMES
    choices = [n for n in pool if n != avoid]
    return rng.choice(choices)


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.sign and args.reveal and args.venue:
        sign = SIGNS[args.sign]
        reveal = REVEALS[args.reveal]
        venue = VENUES[args.venue]
        if not (sign_explained(sign, reveal) and args.reveal in venue.affords):
            raise StoryError(explain_rejection(sign, reveal, venue))

    combos = [
        combo for combo in valid_combos()
        if (args.venue is None or combo[0] == args.venue)
        and (args.sign is None or combo[1] == args.sign)
        and (args.reveal is None or combo[2] == args.reveal)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    venue_id, sign_id, reveal_id = rng.choice(sorted(combos))
    hero_gender = rng.choice(["girl", "boy"])
    friend_gender = rng.choice(["girl", "boy"])
    hero_name = _pick_name(rng, hero_gender)
    friend_name = _pick_name(rng, friend_gender, avoid=hero_name)
    caretaker = args.caretaker or rng.choice(["mother", "father", "aunt", "uncle"])
    relation = args.relation or rng.choice(["siblings", "friends"])
    trait = rng.choice(TRAITS)
    hero_age, friend_age = rng.sample([4, 5, 6, 7, 8], 2)
    trust = rng.randint(0, 10)
    return StoryParams(
        venue=venue_id,
        sign=sign_id,
        reveal=reveal_id,
        hero=hero_name,
        hero_gender=hero_gender,
        friend=friend_name,
        friend_gender=friend_gender,
        caretaker=caretaker,
        trait=trait,
        relation=relation,
        hero_age=hero_age,
        friend_age=friend_age,
        trust=trust,
    )


def generate(params: StoryParams) -> StorySample:
    if params.venue not in VENUES:
        raise StoryError(f"(Unknown venue: {params.venue})")
    if params.sign not in SIGNS:
        raise StoryError(f"(Unknown sign: {params.sign})")
    if params.reveal not in REVEALS:
        raise StoryError(f"(Unknown reveal: {params.reveal})")
    if params.caretaker not in {"mother", "father", "aunt", "uncle"}:
        raise StoryError(f"(Unknown caretaker: {params.caretaker})")
    if params.relation not in {"siblings", "friends"}:
        raise StoryError(f"(Unknown relation: {params.relation})")

    venue = VENUES[params.venue]
    sign = SIGNS[params.sign]
    reveal = REVEALS[params.reveal]
    if not (sign_explained(sign, reveal) and reveal.id in venue.affords):
        raise StoryError(explain_rejection(sign, reveal, venue))

    hazard = HAZARDS[HAZARD_BY_VENUE[venue.id]]

    world = tell(
        venue=venue,
        sign=sign,
        reveal=reveal,
        hazard=hazard,
        hero_name=params.hero,
        hero_gender=params.hero_gender,
        friend_name=params.friend,
        friend_gender=params.friend_gender,
        trait=params.trait,
        caretaker_type=params.caretaker,
        relation=params.relation,
        hero_age=params.hero_age,
        friend_age=params.friend_age,
        trust=params.trust,
    )

    story = world.render()
    story = story.replace("{hero}", params.hero)

    return StorySample(
        params=params,
        story=story,
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
        print(asp_program("", "#show valid/3.\n#show outcome/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (venue, sign, reveal) combos:\n")
        for venue, sign, reveal in combos:
            print(f"  {venue:11} {sign:15} {reveal}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)

    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
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
            header = f"### {p.hero} & {p.friend}: {p.sign} at {p.venue} ({outcome_of(p)})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()

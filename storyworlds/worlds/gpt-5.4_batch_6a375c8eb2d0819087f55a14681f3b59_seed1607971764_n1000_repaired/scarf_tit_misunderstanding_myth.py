#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/scarf_tit_misunderstanding_myth.py
=============================================================

A small myth-shaped story world about a child, a sacred scarf, and a tit that is
wrongly blamed for trouble. The core tension is a misunderstanding: the child
thinks the little bird is stealing the scarf, but the bird is really trying to
show that the scarf is caught and dawn cannot fully come until it is freed.

Run it
------
    python storyworlds/worlds/gpt-5.4/scarf_tit_misunderstanding_myth.py
    python storyworlds/worlds/gpt-5.4/scarf_tit_misunderstanding_myth.py --place hill_tree --scarf dawn_silk --snag thorn
    python storyworlds/worlds/gpt-5.4/scarf_tit_misunderstanding_myth.py --scarf temple_banner
    python storyworlds/worlds/gpt-5.4/scarf_tit_misunderstanding_myth.py --all
    python storyworlds/worlds/gpt-5.4/scarf_tit_misunderstanding_myth.py -n 5 --seed 7 --qa
    python storyworlds/worlds/gpt-5.4/scarf_tit_misunderstanding_myth.py --verify
"""

from __future__ import annotations

import argparse
import copy
import io
import json
import os
import random
import sys
from collections import defaultdict
from contextlib import redirect_stdout
from dataclasses import dataclass, field
from typing import Callable, Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from results import QAItem, StoryError, StorySample  # noqa: E402

THRESHOLD = 1.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    traits: list[str] = field(default_factory=list)
    role: str = ""
    attrs: dict = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "grandmother", "keeper", "woman"}
        male = {"boy", "father", "grandfather", "shepherd", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    @property
    def label_word(self) -> str:
        return {
            "grandmother": "grandmother",
            "grandfather": "grandfather",
            "keeper": "keeper",
            "shepherd": "shepherd",
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
class Place:
    id: str
    name: str
    phrase: str
    hook: str
    path: str
    hanging_line: str
    dawn_image: str
    affords: set[str] = field(default_factory=set)
    tags: set[str] = field(default_factory=set)
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

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
class SacredScarf:
    id: str
    label: str
    phrase: str
    color: str
    cloth: str
    light: bool
    grace: int
    blessing: str
    ending: str
    tags: set[str] = field(default_factory=set)
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

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
class Snag:
    id: str
    label: str
    phrase: str
    cling: str
    release: str
    tags: set[str] = field(default_factory=set)
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

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
class Helper:
    id: str
    type: str
    title: str
    seeing: str
    lesson: str
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


class World:
    def __init__(self) -> None:
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {
            "sun_bound": True,
            "bird_helping": True,
            "hero_understands": False,
        }

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
        other = World()
        other.entities = copy.deepcopy(self.entities)
        other.fired = set(self.fired)
        other.paragraphs = [[]]
        other.facts = copy.deepcopy(self.facts)
        return other


@dataclass
class Rule:
    name: str
    tag: str
    apply: Callable[[World], list[str]]
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


def _r_snagged_dims(world: World) -> list[str]:
    scarf = world.get("scarf")
    sun = world.get("sun")
    village = world.get("village")
    if scarf.meters["snagged"] < THRESHOLD:
        return []
    sig = ("snagged_dims",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    sun.meters["waiting"] += 1
    village.meters["dim"] += 1
    hero = world.get("hero")
    hero.memes["worry"] += 1
    return []


def _r_accusation_hurts(world: World) -> list[str]:
    hero = world.get("hero")
    tit = world.get("tit")
    if hero.memes["accusing"] < THRESHOLD:
        return []
    sig = ("accusation_hurts",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    tit.memes["fear"] += 1
    hero.memes["certainty"] += 1
    return []


def _r_freed_restores(world: World) -> list[str]:
    scarf = world.get("scarf")
    sun = world.get("sun")
    village = world.get("village")
    if scarf.meters["hung"] < THRESHOLD:
        return []
    sig = ("freed_restores",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    scarf.meters["snagged"] = 0.0
    sun.meters["waiting"] = 0.0
    sun.meters["rising"] += 1
    village.meters["light"] += 1
    hero = world.get("hero")
    hero.memes["relief"] += 1
    tit = world.get("tit")
    tit.memes["trust"] += 1
    return []


CAUSAL_RULES = [
    Rule(name="snagged_dims", tag="physical", apply=_r_snagged_dims),
    Rule(name="accusation_hurts", tag="social", apply=_r_accusation_hurts),
    Rule(name="freed_restores", tag="physical", apply=_r_freed_restores),
]


def propagate(world: World, narrate: bool = True) -> list[str]:
    out: list[str] = []
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
        changed = False
        for rule in CAUSAL_RULES:
            produced = rule.apply(world)
            if produced:
                changed = True
                out.extend(produced)
            elif any(sig[0] == rule.name for sig in world.fired):
                pass
        new_count = len(world.fired)
        if not changed:
            break
        if len(world.fired) != new_count:
            changed = True
    if narrate:
        for line in out:
            world.say(line)
    return out


def scarf_can_be_helped(scarf: SacredScarf) -> bool:
    return scarf.light


def valid_combo(place: Place, scarf: SacredScarf, snag: Snag) -> bool:
    return scarf_can_be_helped(scarf) and snag.id in place.affords


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for place_id, place in PLACES.items():
        for scarf_id, scarf in SCARVES.items():
            for snag_id, snag in SNAGS.items():
                if valid_combo(place, scarf, snag):
                    combos.append((place_id, scarf_id, snag_id))
    return combos


def explain_rejection(place: Place, scarf: SacredScarf, snag: Snag) -> str:
    if not scarf.light:
        return (
            f"(No story: {scarf.phrase} is too heavy for a tit to tug or point out in a believable way. "
            "This world needs a small bird that can honestly help with the misunderstanding, so choose a light scarf.)"
        )
    if snag.id not in place.affords:
        return (
            f"(No story: {place.name} has no {snag.label} for the scarf to catch on. "
            "The misunderstanding only works when the cloth can truly snag there.)"
        )
    return "(No story: this combination does not fit the world.)"


def outcome_of(params: "StoryParams") -> str:
    scarf = SCARVES[params.scarf]
    return "bright" if params.delay <= scarf.grace else "pale"


def predict_dawn(place: Place, scarf: SacredScarf, snag: Snag) -> dict:
    world = World()
    world.add(Entity(id="hero", kind="character", type="girl", role="hero"))
    world.add(Entity(id="tit", type="bird", label="tit"))
    world.add(Entity(id="scarf", type="scarf", label=scarf.label))
    world.add(Entity(id="sun", type="sun", label="sun"))
    world.add(Entity(id="village", type="village", label="village"))
    world.get("scarf").meters["snagged"] = 1.0
    world.facts["sun_bound"] = True
    propagate(world, narrate=False)
    return {
        "waiting": world.get("sun").meters["waiting"],
        "dim": world.get("village").meters["dim"],
        "snag": snag.label,
        "place": place.name,
    }


def opening(world: World, hero: Entity, place: Place, scarf: SacredScarf) -> None:
    hero.memes["duty"] += 1
    world.say(
        f"Long ago, when morning still listened to small hands, {hero.id} climbed to {place.phrase} "
        f"carrying {scarf.phrase}. People said the scarf's {scarf.color} threads helped the sun remember "
        f"{scarf.blessing}."
    )
    world.say(
        f"At the first gold edge of day, the scarf was meant to hang from {place.hook}, and then {place.dawn_image}."
    )


def snag_setup(world: World, hero: Entity, tit: Entity, place: Place, scarf: SacredScarf, snag: Snag) -> None:
    scarf_ent = world.get("scarf")
    scarf_ent.meters["snagged"] = 1.0
    propagate(world, narrate=False)
    world.say(
        f"But before {hero.id} reached the hook, a gust drew the scarf across {place.path}, and {snag.phrase} "
        f"{snag.cling}."
    )
    world.say(
        f"A little tit darted down and tugged at the trapped cloth with its beak, giving sharp bright calls."
    )


def misunderstanding(world: World, hero: Entity, tit: Entity, scarf: SacredScarf) -> None:
    hero.memes["accusing"] += 1
    propagate(world, narrate=False)
    world.say(
        f"{hero.id} stopped short. In the half-light, the bird looked like a thief at work. "
        f'"Shoo, tiny robber!" {hero.pronoun()} cried. "That is the sun\'s scarf."'
    )
    world.say(
        f"The tit fluttered back only a little, then returned to the cloth and pulled again. "
        f"To {hero.id}, that only deepened the mistake."
    )


def chase(world: World, hero: Entity, tit: Entity, delay: int) -> None:
    hero.memes["confusion"] += 1
    hero.meters["steps"] += float(delay + 1)
    if delay == 0:
        world.say(
            f"{hero.id} waved both hands and took three quick steps after the bird."
        )
    elif delay == 1:
        world.say(
            f"{hero.id} chased the tit around the stone path until dew splashed at {hero.pronoun('possessive')} ankles."
        )
    else:
        world.say(
            f"{hero.id} chased the tit from stone to stone, calling it greedy, while the sky stayed gray much longer than it should have."
        )


def dark_sign(world: World, place: Place) -> None:
    sun = world.get("sun")
    village = world.get("village")
    if sun.meters["waiting"] >= THRESHOLD or village.meters["dim"] >= THRESHOLD:
        world.say(
            f"Still no true sunrise came. The roofs below {place.name} held their shadows, and even the sheep bells sounded hushed."
        )


def helper_arrives(world: World, helper_ent: Entity, helper: Helper, hero: Entity, snag: Snag) -> None:
    helper_ent.memes["wisdom"] += 1
    world.say(
        f"Then {helper.title} came up the path, walking slowly as if listening to the hill itself. "
        f'{helper.pronoun("subject").capitalize()} looked once at the bird, once at the scarf, and said, '
        f'"{helper.seeing} The tit is not stealing. It is showing you where the cloth is held by {snag.label}."'
    )


def understanding(world: World, hero: Entity, tit: Entity) -> None:
    world.facts["hero_understands"] = True
    hero.memes["shame"] += 1
    hero.memes["kindness"] += 1
    tit.memes["fear"] = 0.0
    world.say(
        f"At once {hero.id} saw the truth: the little bird had been pulling at the trapped edge, trying to free it. "
        f"The misunderstanding fell away as suddenly as fog."
    )


def free_and_hang(world: World, hero: Entity, place: Place, scarf: SacredScarf, snag: Snag) -> None:
    scarf_ent = world.get("scarf")
    scarf_ent.meters["snagged"] = 0.0
    scarf_ent.meters["freed"] += 1
    scarf_ent.meters["hung"] += 1
    propagate(world, narrate=False)
    world.say(
        f"{hero.id} bent beside {snag.phrase} and {snag.release}. Then {hero.pronoun()} lifted the scarf high and hung it from {place.hook}, where the {scarf.cloth} could breathe in the waking wind."
    )


def apology(world: World, hero: Entity, tit: Entity) -> None:
    hero.memes["gratitude"] += 1
    tit.memes["trust"] += 1
    world.say(
        f'"Little tit," {hero.id} whispered, "forgive me. You were helping all along." '
        f"The bird answered with one clean note and settled nearby instead of flying away."
    )


def ending(world: World, place: Place, scarf: SacredScarf, helper: Helper, outcome: str) -> None:
    if outcome == "bright":
        world.say(
            f"Then the sun rose full and warm. {place.dawn_image.capitalize()}, and the scarf shone so brightly that people below said a small gold spark had entered the bird's throat forever."
        )
    else:
        world.say(
            f"Then the sun rose, but slowly, like a lamp being uncovered. {place.dawn_image.capitalize()}, yet the morning stayed pale enough for everyone to remember how long a mistake can hold back the light."
        )
    world.say(
        f"From that day on, when a tit cried near cloth or branch, the people of the hill did not call it a thief. They remembered {helper.lesson}, and they listened before they judged."
    )
    world.say(
        f"And whenever {hero.id} carried a scarf at dawn, {hero.pronoun()} smiled if a small bird followed."
    )


def tell(
    place: Place,
    scarf: SacredScarf,
    snag: Snag,
    helper: Helper,
    hero_name: str = "Iria",
    hero_type: str = "girl",
    delay: int = 0,
) -> World:
    world = World()
    hero = world.add(Entity(id=hero_name, kind="character", type=hero_type, role="hero", traits=["watchful"]))
    tit = world.add(Entity(id="Tit", type="bird", label="tit", role="bird"))
    helper_ent = world.add(Entity(id="Helper", kind="character", type=helper.type, role="helper", label=helper.title))
    scarf_ent = world.add(Entity(id="scarf", type="scarf", label=scarf.label))
    sun = world.add(Entity(id="sun", type="sun", label="sun"))
    village = world.add(Entity(id="village", type="village", label="village"))

    scarf_ent.meters["snagged"] = 0.0
    scarf_ent.meters["freed"] = 0.0
    scarf_ent.meters["hung"] = 0.0
    sun.meters["waiting"] = 0.0
    sun.meters["rising"] = 0.0
    village.meters["dim"] = 0.0
    village.meters["light"] = 0.0
    hero.memes["accusing"] = 0.0
    hero.memes["confusion"] = 0.0
    hero.memes["worry"] = 0.0
    hero.memes["shame"] = 0.0
    tit.memes["fear"] = 0.0
    tit.memes["trust"] = 0.0

    opening(world, hero, place, scarf)
    world.para()
    snag_setup(world, hero, tit, place, scarf, snag)
    misunderstanding(world, hero, tit, scarf)
    chase(world, hero, tit, delay)
    dark_sign(world, place)
    world.para()
    helper_arrives(world, helper_ent, helper, hero, snag)
    understanding(world, hero, tit)
    free_and_hang(world, hero, place, scarf, snag)
    apology(world, hero, tit)
    world.para()
    outcome = "bright" if delay <= scarf.grace else "pale"
    ending(world, place, scarf, helper, outcome)

    world.facts.update(
        hero=hero,
        tit=tit,
        helper=helper_ent,
        place=place,
        scarf_cfg=scarf,
        snag=snag,
        outcome=outcome,
        delay=delay,
        dawn_delayed=delay > 0,
        misunderstood=True,
        scarf_restored=scarf_ent.meters["hung"] >= THRESHOLD,
        helper_cfg=helper,
    )
    return world


PLACES = {
    "hill_tree": Place(
        id="hill_tree",
        name="the hill tree",
        phrase="the old hill tree above the village",
        hook="the bent silver branch",
        path="the root-worn path",
        hanging_line="on the bent silver branch",
        dawn_image="light ran over the fields like spilled honey",
        affords={"thorn", "briar"},
        tags={"tree", "dawn"},
    ),
    "moon_well": Place(
        id="moon_well",
        name="the moon well",
        phrase="the moon well where the first swallows circled",
        hook="the carved stone ring",
        path="the mossy rim",
        hanging_line="on the carved stone ring",
        dawn_image="gold trembled over the water and climbed the sleeping doors",
        affords={"briar", "nail"},
        tags={"well", "dawn"},
    ),
    "sun_gate": Place(
        id="sun_gate",
        name="the sun gate",
        phrase="the sun gate at the eastern wall",
        hook="the copper ring above the arch",
        path="the narrow stair",
        hanging_line="on the copper ring above the arch",
        dawn_image="light spilled through the gate and painted the road",
        affords={"thorn", "nail"},
        tags={"gate", "dawn"},
    ),
}

SCARVES = {
    "dawn_silk": SacredScarf(
        id="dawn_silk",
        label="dawn scarf",
        phrase="a saffron scarf as light as a breath",
        color="saffron",
        cloth="silk",
        light=True,
        grace=1,
        blessing="the road to morning",
        ending="it shone like a small sunrise",
        tags={"scarf", "silk"},
    ),
    "river_wool": SacredScarf(
        id="river_wool",
        label="river scarf",
        phrase="a blue scarf soft with river wool",
        color="blue",
        cloth="wool",
        light=True,
        grace=0,
        blessing="clear water and gentle weather",
        ending="it glowed like a strip of sky",
        tags={"scarf", "wool"},
    ),
    "rose_linen": SacredScarf(
        id="rose_linen",
        label="rose scarf",
        phrase="a rose-red scarf woven of thin linen",
        color="rose-red",
        cloth="linen",
        light=True,
        grace=1,
        blessing="warm bread and waking birds",
        ending="it fluttered like a flower petal",
        tags={"scarf", "linen"},
    ),
    "temple_banner": SacredScarf(
        id="temple_banner",
        label="temple banner",
        phrase="a heavy temple scarf thick with beads",
        color="crimson",
        cloth="brocade",
        light=False,
        grace=0,
        blessing="the strength of old kings",
        ending="it shone like a royal standard",
        tags={"scarf", "heavy"},
    ),
}

SNAGS = {
    "thorn": Snag(
        id="thorn",
        label="thorn",
        phrase="a blackthorn branch",
        cling="caught the fringe in one crooked thorn",
        release="lifted the fringe free from the thorn",
        tags={"thorn"},
    ),
    "briar": Snag(
        id="briar",
        label="briar",
        phrase="a sleeping briar",
        cling="held one tassel fast in its hooked stems",
        release="unwound the tassel from the briar stems",
        tags={"briar"},
    ),
    "nail": Snag(
        id="nail",
        label="nail",
        phrase="an old iron nail",
        cling="caught the hem on its bent head",
        release="slid the hem off the bent nail",
        tags={"nail"},
    ),
}

HELPERS = {
    "grandmother": Helper(
        id="grandmother",
        type="grandmother",
        title="the grandmother of the spring",
        seeing="Small birds do not quarrel with the sun for cloth",
        lesson="that quick blame is a shadow, and patient seeing is a lamp",
        tags={"elder"},
    ),
    "keeper": Helper(
        id="keeper",
        type="keeper",
        title="the old gate-keeper",
        seeing="If the tit wanted the scarf, it would flee with it, not cry beside it",
        lesson="that truth often speaks in a smaller voice than fear",
        tags={"elder"},
    ),
    "shepherd": Helper(
        id="shepherd",
        type="shepherd",
        title="the shepherd of the ridge",
        seeing="Watch the beak, child; it pulls at the snag, not at the gift",
        lesson="that one must look twice before naming a helper an enemy",
        tags={"elder"},
    ),
}

GIRL_NAMES = ["Iria", "Nara", "Eleni", "Talia", "Mira", "Sena"]
BOY_NAMES = ["Doran", "Lio", "Pavel", "Tarin", "Milo", "Soren"]


@dataclass
class StoryParams:
    place: str
    scarf: str
    snag: str
    helper: str
    hero_name: str
    hero_type: str
    delay: int = 0
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
    "tit": [
        (
            "What is a tit?",
            "A tit is a very small bird with a quick beak and a bright, busy way of moving. It hops through branches looking for seeds and insects.",
        )
    ],
    "scarf": [
        (
            "What is a scarf?",
            "A scarf is a long piece of cloth people can wear or tie somewhere. In stories, a scarf can also be a special sign or gift.",
        )
    ],
    "misunderstanding": [
        (
            "What is a misunderstanding?",
            "A misunderstanding happens when someone thinks they know what is going on, but they are wrong. It can be fixed when people look again, listen, or explain carefully.",
        )
    ],
    "thorn": [
        (
            "Why can cloth catch on a thorn?",
            "A thorn is sharp and curved, so soft cloth can snag on it easily. Even a light pull can leave threads stuck.",
        )
    ],
    "dawn": [
        (
            "What is dawn?",
            "Dawn is the time when night begins to turn into morning. The sky slowly grows lighter before the sun is fully up.",
        )
    ],
    "elder": [
        (
            "Why do myths often have wise elders?",
            "Wise elders in myths help younger people see what they missed. They often slow the story down long enough for truth to be noticed.",
        )
    ],
}
KNOWLEDGE_ORDER = ["tit", "scarf", "misunderstanding", "thorn", "dawn", "elder"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    place = f["place"]
    scarf = f["scarf_cfg"]
    snag = f["snag"]
    return [
        f'Write a short myth for a young child that includes the words "scarf" and "tit".',
        f"Tell a myth-like story where {hero.id} sees a tit tugging at a sacred scarf near {place.name} and wrongly believes the bird is stealing it.",
        f"Write a story about a misunderstanding: a child blames a small bird for trouble, but the bird is really trying to show that the scarf is caught on a {snag.label}.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    hero = f["hero"]
    place = f["place"]
    scarf = f["scarf_cfg"]
    snag = f["snag"]
    helper = f["helper_cfg"]
    outcome = f["outcome"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {hero.id}, a child carrying {scarf.phrase}, and a little tit on the hill. The story also includes {helper.title}, who helps explain the truth.",
        ),
        (
            f"Why did {hero.id} think the tit was doing something bad?",
            f"{hero.id} saw the tit tugging at the scarf in the half-light and mistook that pulling for stealing. Because the morning was still dim, the bird's true purpose was hard to see at first.",
        ),
        (
            "What was the tit really trying to do?",
            f"The tit was trying to show that the scarf had caught on {snag.phrase}. It kept returning to the trapped edge because it was helping, not harming.",
        ),
        (
            "Why was the morning slow to brighten?",
            f"The scarf was still snagged instead of hanging in its proper place. In this myth, that meant the sun had to wait and the village stayed dim.",
        ),
        (
            f"How was the misunderstanding fixed?",
            f"{helper.title.capitalize()} told {hero.id} to look carefully at the snag instead of blaming the bird. Then {hero.id} saw the caught fringe, freed the scarf, and understood the tit had been a helper all along.",
        ),
    ]
    if outcome == "bright":
        qa.append(
            (
                "How did the story end?",
                f"It ended with a full bright sunrise after the scarf was hung in place. The ending image shows that understanding and kindness let the light come properly.",
            )
        )
    else:
        qa.append(
            (
                "How did the story end?",
                f"It ended with the sun rising late and pale, even after the scarf was freed. The pale morning became a reminder that a misunderstanding can delay good things, even when it is finally mended.",
            )
        )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags = {"tit", "scarf", "misunderstanding", "dawn", "elder"}
    if world.facts["snag"].id == "thorn":
        tags.add("thorn")
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
    for ent in list(world.entities.values()):
        meters = {k: v for k, v in ent.meters.items() if v}
        memes = {k: v for k, v in ent.memes.items() if v}
        bits = []
        if ent.role:
            bits.append(f"role={ent.role}")
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        lines.append(f"  {ent.id:8} ({ent.type:10}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(sig[0] for sig in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        place="hill_tree",
        scarf="dawn_silk",
        snag="thorn",
        helper="grandmother",
        hero_name="Iria",
        hero_type="girl",
        delay=0,
    ),
    StoryParams(
        place="moon_well",
        scarf="rose_linen",
        snag="nail",
        helper="keeper",
        hero_name="Milo",
        hero_type="boy",
        delay=1,
    ),
    StoryParams(
        place="sun_gate",
        scarf="river_wool",
        snag="thorn",
        helper="shepherd",
        hero_name="Nara",
        hero_type="girl",
        delay=2,
    ),
    StoryParams(
        place="hill_tree",
        scarf="rose_linen",
        snag="briar",
        helper="shepherd",
        hero_name="Soren",
        hero_type="boy",
        delay=0,
    ),
]


ASP_RULES = r"""
helpable(S) :- scarf(S), light(S).
valid(P,S,N) :- place(P), scarf(S), snag(N), affords(P,N), helpable(S).

bright :- chosen_scarf(S), grace(S,G), delay(D), D <= G.
pale   :- chosen_scarf(S), grace(S,G), delay(D), D > G.

outcome(bright) :- bright.
outcome(pale)   :- pale.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for pid, place in PLACES.items():
        lines.append(asp.fact("place", pid))
        for snag in sorted(place.affords):
            lines.append(asp.fact("affords", pid, snag))
    for sid, scarf in SCARVES.items():
        lines.append(asp.fact("scarf", sid))
        if scarf.light:
            lines.append(asp.fact("light", sid))
        lines.append(asp.fact("grace", sid, scarf.grace))
    for nid in SNAGS:
        lines.append(asp.fact("snag", nid))
    for hid in HELPERS:
        lines.append(asp.fact("helper", hid))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("", "#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_outcome(params: StoryParams) -> str:
    import asp

    scenario = "\n".join(
        [
            asp.fact("chosen_scarf", params.scarf),
            asp.fact("delay", params.delay),
        ]
    )
    model = asp.one_model(asp_program(scenario, "#show outcome/1."))
    atoms = asp.atoms(model, "outcome")
    return atoms[0][0] if atoms else "?"


def asp_verify() -> int:
    rc = 0
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: gate matches valid_combos() ({len(py)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos:")
        if py - cl:
            print("  only in python:", sorted(py - cl))
        if cl - py:
            print("  only in clingo:", sorted(cl - py))

    cases = list(CURATED)
    for s in range(50):
        try:
            params = resolve_params(build_parser().parse_args([]), random.Random(s))
        except StoryError:
            continue
        cases.append(params)
    bad = 0
    for params in cases:
        if asp_outcome(params) != outcome_of(params):
            bad += 1
    if bad == 0:
        print(f"OK: outcome model matches outcome_of() on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {bad}/{len(cases)} outcomes differ.")

    try:
        sample = generate(CURATED[0])
        with io.StringIO() as buf, redirect_stdout(buf):
            emit(sample, trace=False, qa=True, header="### smoke")
        print("OK: smoke test generated and emitted a story.")
    except Exception as err:
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Myth-shaped story world: a sacred scarf, a helpful tit, and a misunderstanding."
    )
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--scarf", choices=SCARVES)
    ap.add_argument("--snag", choices=SNAGS)
    ap.add_argument("--helper", choices=HELPERS)
    ap.add_argument("--hero-name")
    ap.add_argument("--hero-type", choices=["girl", "boy"])
    ap.add_argument("--delay", type=int, choices=[0, 1, 2])
    ap.add_argument("-n", type=int, default=1)
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--trace", action="store_true")
    ap.add_argument("--qa", action="store_true")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--asp", action="store_true")
    ap.add_argument("--verify", action="store_true")
    ap.add_argument("--show-asp", action="store_true")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.place and args.scarf and args.snag:
        if not valid_combo(PLACES[args.place], SCARVES[args.scarf], SNAGS[args.snag]):
            raise StoryError(explain_rejection(PLACES[args.place], SCARVES[args.scarf], SNAGS[args.snag]))
    elif args.scarf and not SCARVES[args.scarf].light:
        place = PLACES[args.place] if args.place else next(iter(PLACES.values()))
        snag = SNAGS[args.snag] if args.snag else next(iter(SNAGS.values()))
        raise StoryError(explain_rejection(place, SCARVES[args.scarf], snag))
    elif args.place and args.snag and args.snag not in PLACES[args.place].affords and args.scarf:
        raise StoryError(explain_rejection(PLACES[args.place], SCARVES[args.scarf], SNAGS[args.snag]))

    combos = [
        combo
        for combo in valid_combos()
        if (args.place is None or combo[0] == args.place)
        and (args.scarf is None or combo[1] == args.scarf)
        and (args.snag is None or combo[2] == args.snag)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    place_id, scarf_id, snag_id = rng.choice(sorted(combos))
    hero_type = args.hero_type or rng.choice(["girl", "boy"])
    hero_name = args.hero_name or rng.choice(GIRL_NAMES if hero_type == "girl" else BOY_NAMES)
    helper_id = args.helper or rng.choice(sorted(HELPERS))
    delay = args.delay if args.delay is not None else rng.choice([0, 1, 2])
    return StoryParams(
        place=place_id,
        scarf=scarf_id,
        snag=snag_id,
        helper=helper_id,
        hero_name=hero_name,
        hero_type=hero_type,
        delay=delay,
    )


def generate(params: StoryParams) -> StorySample:
    if params.place not in PLACES:
        raise StoryError(f"(Unknown place: {params.place})")
    if params.scarf not in SCARVES:
        raise StoryError(f"(Unknown scarf: {params.scarf})")
    if params.snag not in SNAGS:
        raise StoryError(f"(Unknown snag: {params.snag})")
    if params.helper not in HELPERS:
        raise StoryError(f"(Unknown helper: {params.helper})")
    place = PLACES[params.place]
    scarf = SCARVES[params.scarf]
    snag = SNAGS[params.snag]
    if not valid_combo(place, scarf, snag):
        raise StoryError(explain_rejection(place, scarf, snag))

    world = tell(
        place=place,
        scarf=scarf,
        snag=snag,
        helper=HELPERS[params.helper],
        hero_name=params.hero_name,
        hero_type=params.hero_type,
        delay=params.delay,
    )
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
        print(asp_program("", "#show valid/3.\n#show outcome/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (place, scarf, snag) combos:\n")
        for place, scarf, snag in combos:
            print(f"  {place:10} {scarf:13} {snag}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)

    samples: list[StorySample] = []
    if args.all:
        samples = [generate(params) for params in CURATED]
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
            header = f"### {p.hero_name}: {p.scarf} at {p.place} ({outcome_of(p)})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()

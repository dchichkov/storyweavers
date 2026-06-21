#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/cock_conflict_magic_cautionary_superhero_story.py
============================================================================

A standalone story world for a tiny cautionary superhero tale: two children are
playing heroes when a cock gets stuck high up with something tangled on his leg.
One child is tempted to use unsupervised magic as a flashy shortcut. The other
child warns that a frightened animal and a strong gust are a bad mix. Depending
on the state and response, the magic is averted, the cock is rescued safely, or
the rescue becomes a longer, sobering lesson.

Run it
------
    python storyworlds/worlds/gpt-5.4/cock_conflict_magic_cautionary_superhero_story.py
    python storyworlds/worlds/gpt-5.4/cock_conflict_magic_cautionary_superhero_story.py --theme barn_guardians --magic storm_cape --perch coop_roof
    python storyworlds/worlds/gpt-5.4/cock_conflict_magic_cautionary_superhero_story.py --perch fence_post
    python storyworlds/worlds/gpt-5.4/cock_conflict_magic_cautionary_superhero_story.py --response leap_grab
    python storyworlds/worlds/gpt-5.4/cock_conflict_magic_cautionary_superhero_story.py --all
    python storyworlds/worlds/gpt-5.4/cock_conflict_magic_cautionary_superhero_story.py -n 5 --seed 7 --qa
    python storyworlds/worlds/gpt-5.4/cock_conflict_magic_cautionary_superhero_story.py --verify
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
from dataclasses import dataclass, field
from typing import Callable, Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from results import QAItem, StoryError, StorySample  # noqa: E402

THRESHOLD = 1.0
SENSE_MIN = 2
BRAVERY_INIT = 6.0
CAUTIOUS_TRAITS = {"careful", "steady", "thoughtful", "gentle", "sensible"}


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
    animal: bool = False
    magical: bool = False
    safe_tool: bool = False
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman"}
        male = {"boy", "father", "dad", "man", "cock"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return {"mother": "mom", "father": "dad"}.get(self.type, self.type)
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
class Theme:
    id: str
    scene: str
    props: str
    team_name: str
    mission: str
    sendoff: str
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


@dataclass
class MagicTool:
    id: str
    label: str
    phrase: str
    sound: str
    warning: str
    effect: str
    plural: bool = False
    magical: bool = True
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
class Perch:
    id: str
    label: str
    the: str
    place_phrase: str
    height: int
    wobble: str
    low: bool = False
    tags: set[str] = field(default_factory=set)

    @property
    def The(self) -> str:
        return self.the[0].upper() + self.the[1:]
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
class Snag:
    id: str
    label: str
    caught_phrase: str
    free_phrase: str
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
class Response:
    id: str
    sense: int
    power: int
    text: str
    fail: str
    qa_text: str
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
        self.facts: dict = {}

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str) -> Entity:
        if eid not in self.entities:
            label = str(eid).replace("_", " ")
            self.entities[eid] = Entity(str(eid), label=label)
        return self.entities[eid]

    def kids(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.role in {"instigator", "cautioner"}]

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)

    def copy(self) -> "World":
        clone = World()
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        clone.facts = copy.deepcopy(self.facts)
        return clone


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


def _r_panic_spreads(world: World) -> list[str]:
    out: list[str] = []
    cock = world.get("cock")
    if cock.meters["panicked"] < THRESHOLD:
        return out
    sig = ("panic_spreads", "cock")
    if sig in world.fired:
        return out
    world.fired.add(sig)
    world.get("yard").meters["danger"] += 1
    for kid in world.kids():
        kid.memes["fear"] += 1
    out.append("__panic__")
    return out


def _r_loose_fall(world: World) -> list[str]:
    out: list[str] = []
    perch = world.get("perch")
    if perch.meters["shaken"] < THRESHOLD:
        return out
    sig = ("loose_fall", "perch")
    if sig in world.fired:
        return out
    world.fired.add(sig)
    world.get("yard").meters["danger"] += 1
    for kid in world.kids():
        kid.memes["alarm"] += 1
    out.append("__shake__")
    return out


CAUSAL_RULES: list[Rule] = [
    Rule(name="panic_spreads", tag="emotional", apply=_r_panic_spreads),
    Rule(name="loose_fall", tag="physical", apply=_r_loose_fall),
]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
        changed = False
        for rule in CAUSAL_RULES:
            lines = rule.apply(world)
            if lines:
                changed = True
                produced.extend(s for s in lines if not s.startswith("__"))
    if narrate:
        for line in produced:
            world.say(line)
    return produced


def cock_at_risk(magic: MagicTool, perch: Perch) -> bool:
    return magic.magical and not perch.low and perch.height >= 1


def sensible_responses() -> list[Response]:
    return [r for r in RESPONSES.values() if r.sense >= SENSE_MIN]


def perch_severity(perch: Perch, delay: int) -> int:
    return perch.height + delay


def is_contained(response: Response, perch: Perch, delay: int) -> bool:
    return response.power >= perch_severity(perch, delay)


def initial_caution(trait: str) -> float:
    return 5.0 if trait in CAUTIOUS_TRAITS else 3.0


def would_avert(relation: str, instigator_age: int, cautioner_age: int, trait: str) -> bool:
    older_sibling = relation == "siblings" and cautioner_age > instigator_age
    authority = (initial_caution(trait) + 1.0) + (4.0 if older_sibling else 0.0)
    return older_sibling and authority > BRAVERY_INIT


def predict_magic(world: World) -> dict:
    sim = world.copy()
    cast_magic(sim, narrate=False)
    cock = sim.get("cock")
    return {
        "panics": cock.meters["panicked"] >= THRESHOLD,
        "danger": sim.get("yard").meters["danger"],
    }


def play_setup(world: World, a: Entity, b: Entity, theme: Theme) -> None:
    for kid in (a, b):
        kid.memes["joy"] += 1
    world.say(
        f"After lunch, {a.id} and {b.id} turned the yard into {theme.scene}. "
        f"{theme.props}"
    )
    world.say(
        f'"{theme.team_name}!" {a.id} cried. "Today we will {theme.mission}!"'
    )


def spot_cock(world: World, b: Entity, cock: Entity, perch: Perch, snag: Snag) -> None:
    world.say(
        f"Then {b.id} pointed up. {cock.label} was on {perch.the}, and {snag.caught_phrase}."
    )
    world.say(
        f'The cock gave a sharp crow and stamped one foot. "{cock.label} needs help," '
        f"{b.id} said."
    )


def tempt(world: World, a: Entity, magic: MagicTool) -> None:
    a.memes["bravado"] += 1
    world.say(
        f'{a.id} straightened {a.pronoun("possessive")} shoulders. "We are superheroes," '
        f'{a.pronoun()} said. "I can use {magic.phrase}."'
    )
    world.say(f"For one shining second, the shortcut felt brave and bright.")


def warn(world: World, b: Entity, a: Entity, magic: MagicTool, perch: Perch, parent: Entity) -> None:
    pred = predict_magic(world)
    b.memes["caution"] += 1
    world.facts["predicted_danger"] = pred["danger"]
    extra = ""
    if b.memes["caution"] >= 6:
        extra = f" {b.pronoun().capitalize()} already knew frightened animals make messy rescues."
    world.say(
        f'{b.id} shook {b.pronoun("possessive")} head. "{parent.label_word.capitalize()} said '
        f'{magic.warning}. If you use {magic.label}, the cock could flap harder on '
        f'''{perch.the}."{extra}'''
    )


def defy(world: World, a: Entity, b: Entity, magic: MagicTool) -> None:
    a.memes["defiance"] += 1
    older = a.attrs.get("relation") == "siblings" and a.age > b.age
    if older:
        rel = "big brother" if a.type == "boy" else "big sister"
        world.say(
            f'"Stand back," {a.id} said, and because {a.pronoun()} was {b.pronoun("possessive")} '
            f'{rel}, {b.id} could not stop {a.pronoun("object")} in time.'
        )
    else:
        world.say(f'"Stand back," {a.id} said, and lifted {magic.label} anyway.')


def back_down(world: World, a: Entity, b: Entity, parent: Entity, theme: Theme) -> None:
    a.memes["bravery"] = 0.0
    a.memes["relief"] += 1
    b.memes["relief"] += 1
    rel = "brother" if b.type == "boy" else "sister"
    world.say(
        f'{a.id} looked at {b.id}, who was {a.pronoun("possessive")} older {rel}, and let out a long breath.'
    )
    world.say(
        f'"Okay," {a.pronoun()} said. "Real heroes can wait for help." Together they ran to get '
        f'{parent.label_word}, still talking like {theme.team_name.lower()}.'
    )


def cast_magic(world: World, narrate: bool = True) -> None:
    cock = world.get("cock")
    perch_ent = world.get("perch")
    magic = world.facts["magic_cfg"]
    cock.meters["panicked"] += 1
    perch_ent.meters["shaken"] += 1
    perch_ent.meters["unstable"] += 1
    propagate(world, narrate=narrate)
    if narrate:
        perch = world.facts["perch_cfg"]
        world.say(
            f"{magic.sound} {magic.effect}. The gust swirled up around {perch.the}, and the cock "
            f"flapped so wildly that {perch.wobble}."
        )


def alarm(world: World, b: Entity, cock: Entity, parent: Entity) -> None:
    world.say(f'"Whoa!" {b.id} cried. "{cock.label} is more scared now!"')
    world.say(f'"{parent.label_word.upper()}!"')


def rescue(world: World, parent: Entity, response: Response, cock: Entity, snag: Snag) -> None:
    cock.meters["panicked"] = 0.0
    cock.meters["perched"] = 0.0
    cock.meters["safe"] += 1
    world.get("yard").meters["danger"] = 0.0
    body = response.text.replace("{cock}", cock.label).replace("{snag}", snag.label)
    world.say(f"{parent.label_word.capitalize()} came fast and {body}.")
    world.say(
        f"In another moment, {cock.label} was on the ground again, blinking hard while {snag.free_phrase}."
    )


def rescue_fail(world: World, parent: Entity, response: Response, cock: Entity, perch: Perch) -> None:
    world.get("yard").meters["danger"] += 1
    cock.meters["perched"] += 1
    body = response.fail.replace("{cock}", cock.label).replace("{perch}", perch.label)
    world.say(f"{parent.label_word.capitalize()} hurried over and {body}.")
    world.say(
        f"The cock beat his wings and flew from {perch.the} to the water barrel, still too frightened to come down."
    )


def lesson(world: World, parent: Entity, a: Entity, b: Entity, magic: MagicTool) -> None:
    for kid in (a, b):
        kid.memes["relief"] += 1
        kid.memes["love"] += 1
        kid.memes["lesson"] += 1
        kid.memes["fear"] = 0.0
    world.say("For a tiny moment, nobody tried to sound heroic.")
    world.say(
        f'Then {parent.label_word} knelt and pulled them close. "I am glad you called me," '
        f'{parent.pronoun()} said softly. "But remember: {magic.warning}. Magic is not for showing off '
        f'around scared animals."'
    )
    world.say(f'"We know," whispered {b.id} and {a.id} together.')


def ranger_wait(world: World, parent: Entity, a: Entity, b: Entity, magic: MagicTool) -> None:
    for kid in (a, b):
        kid.memes["lesson"] += 1
        kid.memes["relief"] += 1
        kid.memes["love"] += 1
    world.say(
        f'{parent.label_word.capitalize()} wrapped an arm around both children and called the animal ranger from the road.'
    )
    world.say(
        f'While they waited, {a.id} stared at {magic.label} and wished {a.pronoun()} had never tried the shortcut.'
    )
    world.say(
        "When the ranger finally coaxed the bird down with calm hands and grain, the whole yard felt quiet and ashamed."
    )


def badge_rule(world: World, parent: Entity, a: Entity, b: Entity, theme: Theme, cock: Entity) -> None:
    for kid in (a, b):
        kid.memes["joy"] += 1
        kid.memes["safety"] += 1
    if world.facts["outcome"] == "burned":
        opener = "The next day, after the long quiet talk,"
    else:
        opener = "The next day,"
    world.say(
        f"{opener} {parent.label_word} cut two paper badges from a cereal box and drew a tiny shield on each one."
    )
    world.say(
        f'"New rule for {theme.team_name}," {parent.pronoun()} said. "Heroes use calm hands first and magic last."'
    )
    world.say(
        f"{a.id} pinned one badge on {b.id}, and {b.id} pinned one on {a.id}. Nearby, {cock.label} scratched in the dust and crowed once, as if he approved."
    )
    world.say(theme.sendoff)
@dataclass
class StoryParams:
    theme: str
    magic: str
    perch: str
    snag: str
    response: str
    instigator: str
    instigator_gender: str
    cautioner: str
    cautioner_gender: str
    parent: str
    trait: str
    delay: int = 0
    instigator_age: int = 6
    cautioner_age: int = 4
    relation: str = "siblings"
    trust: int = 6
    cock_name: str = "Copper"
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
    "magic": [(
        "Why can magic shortcuts be a bad idea around animals?",
        "Animals can be frightened by sudden light, wind, and noise. A frightened animal moves fast and can make a rescue much harder."
    )],
    "wind": [(
        "Why is strong wind risky on a high perch?",
        "Wind can shake loose things and make feet slip. Up high, even a little wobble can feel much bigger."
    )],
    "wand": [(
        "What is a wand?",
        "A wand is a stick used in pretend stories for magic. In real life, tools should only be used the safe way."
    )],
    "boots": [(
        "Why should you not make reckless jumps from high places?",
        "Big jumps can make you fall or miss what you were trying to reach. It is safer to stop and get the right help."
    )],
    "roof": [(
        "Why is a roof a tricky place for a rescue?",
        "Roofs are high and can be slippery or uneven. That is why calm climbing and grown-up help matter."
    )],
    "tree": [(
        "Why do branches sway?",
        "Branches move when wind pushes them or when something lands on them. That is why an animal can feel shaky high in a tree."
    )],
    "beam": [(
        "What is a beam?",
        "A beam is a strong long piece of wood that helps hold something up. A high beam can still be hard and dusty to reach."
    )],
    "ladder": [(
        "What is a ladder for?",
        "A ladder helps someone climb up carefully to a higher place. It works best when a grown-up holds it steady and moves slowly."
    )],
    "grain": [(
        "Why might grain help with a bird rescue?",
        "Some birds will follow food when they feel calm enough. Food can guide them better than chasing them."
    )],
    "blanket": [(
        "How can a blanket help in a rescue?",
        "A blanket can make a soft safe place to land if a small animal jumps down. It should be held low and gently, not waved around."
    )],
    "animal_help": [(
        "What is the safest first step when an animal is scared?",
        "Slow down and get a calm grown-up. Quiet voices and patient hands help much more than rushing."
    )],
}
KNOWLEDGE_ORDER = [
    "magic",
    "wind",
    "wand",
    "boots",
    "roof",
    "tree",
    "beam",
    "ladder",
    "grain",
    "blanket",
    "animal_help",
]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    a = f["instigator"]
    b = f["cautioner"]
    magic = f["magic"]
    perch = f["perch_cfg"]
    cock = f["cock"]
    outcome = f["outcome"]
    base = (
        f'Write a short superhero story for a 3-to-5-year-old where two children try to help '
        f'{cock.label} on {perch.the}, and include the word "cock".'
    )
    if outcome == "averted":
        return [
            base,
            f"Tell a cautionary story where {a.id} wants to use {magic.label}, but {b.id} talks {a.pronoun('object')} out of it and they choose calm help instead.",
            "Write a gentle superhero rescue where the bravest choice is waiting for safe help instead of using a flashy magical shortcut.",
        ]
    if outcome == "contained":
        return [
            base,
            f"Tell a superhero story where {a.id} uses {magic.label} at first, the rescue gets harder, and a grown-up calmly saves the cock.",
            "Write a cautionary magic story that ends with children learning that real heroes use patient hands before powers.",
        ]
    return [
        base,
        f"Tell a sober superhero story where {a.id} shows off with {magic.label}, frightens the cock, and learns a hard lesson while waiting for proper help.",
        "Write a magic cautionary story with conflict, a scared animal, and an ending that teaches children not to use risky shortcuts.",
    ]


def pair_noun(a: Entity, b: Entity, relation: str) -> str:
    if relation == "siblings":
        if a.type == "boy" and b.type == "boy":
            return "two brothers"
        if a.type == "girl" and b.type == "girl":
            return "two sisters"
        return "a brother and a sister"
    return "two friends"


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    a = f["instigator"]
    b = f["cautioner"]
    parent = f["parent"]
    cock = f["cock"]
    magic = f["magic"]
    perch = f["perch_cfg"]
    snag = f["snag"]
    response = f["response"]
    pair = pair_noun(a, b, f["relation"])
    pw = parent.label_word

    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {pair}, {a.id} and {b.id}, and {cock.label}. The children were pretending to be heroes when they saw he needed help."
        ),
        (
            f"Why did the children look up at {perch.the}?",
            f"They saw {cock.label} up high with {snag.label} caught on him. That made the rescue feel urgent and started their argument about what to do."
        ),
        (
            f"Why did {b.id} warn {a.id} not to use {magic.label}?",
            f"{b.id} knew sudden magic could scare the cock and make the perch more dangerous. In this story, the warning came before the biggest trouble, because {b.id} could see the shortcut might turn the rescue into a mess."
        ),
    ]
    if f["outcome"] == "averted":
        qa.append(
            (
                f"What changed {a.id}'s mind?",
                f"{a.id} listened to {b.id} and gave up the showy idea. That choice mattered because it let a calm rescue happen before the cock got more frightened."
            )
        )
        qa.append(
            (
                f"How did {pw} help {cock.label}?",
                f"{pw.capitalize()} {response.qa_text}. The help worked because the rescue stayed slow and gentle from the start."
            )
        )
    elif f["outcome"] == "contained":
        qa.append(
            (
                f"What happened when {a.id} used {magic.label}?",
                f"The magic made wind and noise, and the cock panicked on the high perch. That made everyone call for {pw}, because the rescue was suddenly more dangerous than before."
            )
        )
        qa.append(
            (
                f"How did {pw} fix the problem?",
                f"{pw.capitalize()} {response.qa_text}. The grown-up method worked because it was steadier than the magical shortcut."
            )
        )
    else:
        qa.append(
            (
                f"Did the first rescue work?",
                f"No. {pw.capitalize()} tried to help, but the cock was too frightened and flew to another hard place. Because the shortcut had made the bird panic, the family had to wait for calmer, better help."
            )
        )
        qa.append(
            (
                "How did the story end?",
                f"It ended quietly, with the ranger finally bringing the cock down and the children learning a hard lesson. They still got paper hero badges, but now the badges meant patience instead of showing off."
            )
        )
    qa.append(
        (
            "What was the new superhero rule at the end?",
            "The new rule was to use calm hands first and magic last. That ending shows the children changed, because their hero game now includes patience and safety."
        )
    )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags: set[str] = set(world.facts["magic"].tags) | set(world.facts["perch_cfg"].tags) | set(world.facts["response"].tags)
    out: list[tuple[str, str]] = []
    for tag in KNOWLEDGE_ORDER:
        if tag in tags and tag in KNOWLEDGE:
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
            shown = {k: v for k, v in e.attrs.items() if v != ""}
            if shown:
                bits.append(f"attrs={shown}")
        flags = [name for name, on in (("animal", e.animal), ("magical", e.magical), ("safe_tool", e.safe_tool)) if on]
        if flags:
            bits.append(f"flags={flags}")
        lines.append(f"  {e.id:10} ({e.type:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        theme="barn_guardians",
        magic="storm_cape",
        perch="coop_roof",
        snag="ribbon",
        response="ladder",
        instigator="Max",
        instigator_gender="boy",
        cautioner="Lily",
        cautioner_gender="girl",
        parent="mother",
        trait="careful",
        delay=0,
        instigator_age=5,
        cautioner_age=7,
        relation="siblings",
        trust=5,
        cock_name="Copper",
    ),
    StoryParams(
        theme="rooftop_rangers",
        magic="comet_wand",
        perch="apple_tree",
        snag="kite_string",
        response="grain_trail",
        instigator="Ben",
        instigator_gender="boy",
        cautioner="Mia",
        cautioner_gender="girl",
        parent="father",
        trait="steady",
        delay=0,
        instigator_age=6,
        cautioner_age=5,
        relation="friends",
        trust=4,
        cock_name="Sunny",
    ),
    StoryParams(
        theme="sunbeam_sentinels",
        magic="thunder_boots",
        perch="hayloft_beam",
        snag="bell_cord",
        response="blanket_catch",
        instigator="Ava",
        instigator_gender="girl",
        cautioner="Leo",
        cautioner_gender="boy",
        parent="mother",
        trait="curious",
        delay=1,
        instigator_age=7,
        cautioner_age=5,
        relation="siblings",
        trust=3,
        cock_name="Crimson",
    ),
]


def explain_rejection(magic: MagicTool, perch: Perch) -> str:
    if perch.low:
        return (
            f"(No story: {perch.the} is too low. The cock is not really stranded there, so a flashy magic rescue would have no honest danger or lesson.)"
        )
    return (
        f"(No story: {magic.label} does not create the kind of risky shortcut this world needs.)"
    )


def explain_response(response_id: str) -> str:
    r = RESPONSES[response_id]
    better = " / ".join(sorted(x.id for x in sensible_responses()))
    return (
        f"(Refusing response '{response_id}': it scores too low on common sense (sense={r.sense} < {SENSE_MIN}). Try: {better}.)"
    )


def outcome_of(params: StoryParams) -> str:
    if would_avert(params.relation, params.instigator_age, params.cautioner_age, params.trait):
        return "averted"
    return "contained" if is_contained(RESPONSES[params.response], PERCHES[params.perch], params.delay) else "burned"


ASP_RULES = r"""
hazard(M, P) :- magical(M), perch(P), not low(P), height(P, H), H >= 1.
sensible(R)  :- response(R), sense(R, S), sense_min(Min), S >= Min.
valid(T, M, P) :- theme(T), magic(M), perch(P), hazard(M, P).

cautious_now(T) :- trait(T), is_cautious(T).
init_caution(5) :- trait(T), cautious_now(T).
init_caution(3) :- trait(T), not cautious_now(T).
older_sibling :- relation(siblings), instigator_age(IA), cautioner_age(CA), CA > IA.
bonus(4) :- older_sibling.
bonus(0) :- not older_sibling.
authority(C + 1 + B) :- init_caution(C), bonus(B).
averted :- older_sibling, authority(A), bravery_init(BR), A > BR.

severity(H + D) :- chosen_perch(P), height(P, H), delay(D).
resp_power(Pw) :- chosen_response(R), power(R, Pw).
contained :- resp_power(Pw), severity(Sv), Pw >= Sv.

outcome(averted) :- averted.
outcome(contained) :- not averted, contained.
outcome(burned) :- not averted, not contained.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for tid in THEMES:
        lines.append(asp.fact("theme", tid))
    for mid, magic in MAGIC_TOOLS.items():
        lines.append(asp.fact("magic", mid))
        if magic.magical:
            lines.append(asp.fact("magical", mid))
    for pid, perch in PERCHES.items():
        lines.append(asp.fact("perch", pid))
        lines.append(asp.fact("height", pid, perch.height))
        if perch.low:
            lines.append(asp.fact("low", pid))
    for rid, response in RESPONSES.items():
        lines.append(asp.fact("response", rid))
        lines.append(asp.fact("sense", rid, response.sense))
        lines.append(asp.fact("power", rid, response.power))
    lines.append(asp.fact("sense_min", SENSE_MIN))
    lines.append(asp.fact("bravery_init", int(BRAVERY_INIT)))
    for trait in sorted(CAUTIOUS_TRAITS):
        lines.append(asp.fact("is_cautious", trait))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("", "#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_sensible() -> list[str]:
    import asp

    model = asp.one_model(asp_program("", "#show sensible/1."))
    return sorted(r for (r,) in asp.atoms(model, "sensible"))


def asp_outcome(params: StoryParams) -> str:
    import asp

    scenario = "\n".join(
        [
            asp.fact("chosen_perch", params.perch),
            asp.fact("chosen_response", params.response),
            asp.fact("delay", params.delay),
            asp.fact("relation", params.relation),
            asp.fact("instigator_age", params.instigator_age),
            asp.fact("cautioner_age", params.cautioner_age),
            asp.fact("trait", params.trait),
        ]
    )
    model = asp.one_model(asp_program(scenario, "#show outcome/1."))
    out = asp.atoms(model, "outcome")
    return out[0][0] if out else "?"


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

    clingo_sens = set(asp_sensible())
    python_sens = {r.id for r in sensible_responses()}
    if clingo_sens == python_sens:
        print(f"OK: sensible responses match ({sorted(clingo_sens)}).")
    else:
        rc = 1
        print(f"MISMATCH in sensible responses: clingo={sorted(clingo_sens)} python={sorted(python_sens)}")

    cases = list(CURATED)
    for seed in range(100):
        try:
            params = resolve_params(build_parser().parse_args([]), random.Random(seed))
        except StoryError:
            continue
        cases.append(params)
    bad = sum(1 for params in cases if asp_outcome(params) != outcome_of(params))
    if bad == 0:
        print(f"OK: outcome model matches outcome_of() on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {bad}/{len(cases)} outcomes differ.")

    try:
        sample = generate(CURATED[0])
        if not sample.story.strip():
            raise StoryError("smoke test story was empty")
        buf = io.StringIO()
        old = sys.stdout
        try:
            sys.stdout = buf
            emit(sample, trace=False, qa=False, header="### smoke")
        finally:
            sys.stdout = old
        print("OK: smoke test generate/emit succeeded.")
    except Exception as exc:
        rc = 1
        print(f"SMOKE TEST FAILED: {exc}")
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Story world sketch: a superhero game, a cock in trouble, and a magical shortcut that may go wrong."
    )
    ap.add_argument("--theme", choices=THEMES)
    ap.add_argument("--magic", choices=MAGIC_TOOLS)
    ap.add_argument("--perch", choices=PERCHES)
    ap.add_argument("--snag", choices=SNAGS)
    ap.add_argument("--response", choices=RESPONSES)
    ap.add_argument("--parent", choices=["mother", "father"])
    ap.add_argument("--delay", type=int, choices=[0, 1, 2], help="head start the panic gets before the rescue")
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list the compatible-story set derived by clingo")
    ap.add_argument("--verify", action="store_true", help="check the inline ASP reasoner matches the Python logic")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program (facts + inline rules)")
    return ap


def _pick_kid(rng: random.Random, avoid: str = "") -> tuple[str, str]:
    gender = rng.choice(["girl", "boy"])
    pool = [n for n in (GIRL_NAMES if gender == "girl" else BOY_NAMES) if n != avoid]
    return rng.choice(pool), gender


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.perch and PERCHES[args.perch].low:
        magic = MAGIC_TOOLS[args.magic] if args.magic else next(iter(MAGIC_TOOLS.values()))
        raise StoryError(explain_rejection(magic, PERCHES[args.perch]))
    if args.magic and args.perch:
        magic = MAGIC_TOOLS[args.magic]
        perch = PERCHES[args.perch]
        if not cock_at_risk(magic, perch):
            raise StoryError(explain_rejection(magic, perch))
    if args.response and RESPONSES[args.response].sense < SENSE_MIN:
        raise StoryError(explain_response(args.response))

    combos = [
        combo
        for combo in valid_combos()
        if (args.theme is None or combo[0] == args.theme)
        and (args.magic is None or combo[1] == args.magic)
        and (args.perch is None or combo[2] == args.perch)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    theme_id, magic_id, perch_id = rng.choice(sorted(combos))
    response_id = args.response or rng.choice(sorted(r.id for r in sensible_responses()))
    snag_id = args.snag or rng.choice(sorted(SNAGS))
    instigator, instigator_gender = _pick_kid(rng)
    cautioner, cautioner_gender = _pick_kid(rng, avoid=instigator)
    parent = args.parent or rng.choice(["mother", "father"])
    trait = rng.choice(TRAITS)
    delay = args.delay if args.delay is not None else rng.randint(0, 2)
    relation = rng.choice(["siblings", "friends"])
    instigator_age, cautioner_age = rng.sample([3, 4, 5, 6, 7], 2)
    trust = rng.randint(0, 10)
    cock_name = rng.choice(COCK_NAMES)
    return StoryParams(
        theme=theme_id,
        magic=magic_id,
        perch=perch_id,
        snag=snag_id,
        response=response_id,
        instigator=instigator,
        instigator_gender=instigator_gender,
        cautioner=cautioner,
        cautioner_gender=cautioner_gender,
        parent=parent,
        trait=trait,
        delay=delay,
        instigator_age=instigator_age,
        cautioner_age=cautioner_age,
        relation=relation,
        trust=trust,
        cock_name=cock_name,
    )


def generate(params: StoryParams) -> StorySample:
    if params.theme not in THEMES:
        raise StoryError(f"(Unknown theme: {params.theme})")
    if params.magic not in MAGIC_TOOLS:
        raise StoryError(f"(Unknown magic tool: {params.magic})")
    if params.perch not in PERCHES:
        raise StoryError(f"(Unknown perch: {params.perch})")
    if params.snag not in SNAGS:
        raise StoryError(f"(Unknown snag: {params.snag})")
    if params.response not in RESPONSES:
        raise StoryError(f"(Unknown response: {params.response})")
    if RESPONSES[params.response].sense < SENSE_MIN:
        raise StoryError(explain_response(params.response))
    if not cock_at_risk(MAGIC_TOOLS[params.magic], PERCHES[params.perch]):
        raise StoryError(explain_rejection(MAGIC_TOOLS[params.magic], PERCHES[params.perch]))

    world = tell(
        THEMES[params.theme],
        MAGIC_TOOLS[params.magic],
        PERCHES[params.perch],
        SNAGS[params.snag],
        RESPONSES[params.response],
        instigator=params.instigator,
        instigator_gender=params.instigator_gender,
        cautioner=params.cautioner,
        cautioner_gender=params.cautioner_gender,
        parent_type=params.parent,
        trait=params.trait,
        delay=params.delay,
        instigator_age=params.instigator_age,
        cautioner_age=params.cautioner_age,
        relation=params.relation,
        trust=params.trust,
        cock_name=params.cock_name,
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
        print(asp_program("", "#show valid/3.\n#show sensible/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"sensible responses: {', '.join(asp_sensible())}\n")
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (theme, magic, perch) combos:\n")
        for theme_id, magic_id, perch_id in combos:
            print(f"  {theme_id:18} {magic_id:13} {perch_id}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)

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
            print(json.dumps([sample.to_dict() for sample in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.instigator} & {p.cautioner}: {p.magic} at {p.perch} ({outcome_of(p)})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")






def tell(
    theme: Theme,
    magic: MagicTool,
    perch: Perch,
    snag: Snag,
    response: Response,
    *,
    instigator: str = "Max",
    instigator_gender: str = "boy",
    cautioner: str = "Lily",
    cautioner_gender: str = "girl",
    parent_type: str = "mother",
    trait: str = "careful",
    delay: int = 0,
    instigator_age: int = 6,
    cautioner_age: int = 4,
    relation: str = "siblings",
    trust: int = 6,
    cock_name: str = "Copper",
) -> World:
    world = World()
    a = world.add(
        Entity(
            id=instigator,
            kind="character",
            type=instigator_gender,
            role="instigator",
            traits=["bold"],
            age=instigator_age,
            attrs={"relation": relation},
        )
    )
    b = world.add(
        Entity(
            id=cautioner,
            kind="character",
            type=cautioner_gender,
            role="cautioner",
            traits=[trait],
            age=cautioner_age,
            attrs={"relation": relation},
        )
    )
    parent = world.add(
        Entity(
            id="Parent",
            kind="character",
            type=parent_type,
            role="parent",
            label="the parent",
        )
    )
    world.add(Entity(id="yard", type="yard", label="the yard"))
    cock = world.add(
        Entity(
            id="cock",
            kind="character",
            type="cock",
            label=f"{cock_name} the cock",
            role="animal",
            animal=True,
        )
    )
    perch_ent = world.add(Entity(id="perch", type="perch", label=perch.label))
    tool = world.add(Entity(id="magic_tool", type="tool", label=magic.label, magical=True))

    a.memes["bravery"] = BRAVERY_INIT
    b.memes["trust"] = float(trust)
    b.memes["caution"] = initial_caution(trait)
    cock.meters["perched"] = 1.0
    cock.meters["snagged"] = 1.0
    perch_ent.meters["height"] = float(perch.height)
    world.facts["predicted_danger"] = 0
    world.facts["theme"] = theme
    world.facts["magic_cfg"] = magic
    world.facts["perch_cfg"] = perch
    world.facts["snag_cfg"] = snag
    world.facts["cock_name"] = cock_name

    play_setup(world, a, b, theme)
    spot_cock(world, b, cock, perch, snag)

    world.para()
    tempt(world, a, magic)
    warn(world, b, a, magic, perch, parent)

    averted = would_avert(relation, a.age, b.age, trait)

    world.para()
    if averted:
        back_down(world, a, b, parent, theme)
        world.para()
        rescue(world, parent, response, cock, snag)
        lesson(world, parent, a, b, magic)
        world.para()
        outcome = "averted"
        badge_rule(world, parent, a, b, theme, cock)
    else:
        defy(world, a, b, magic)
        cast_magic(world, narrate=True)
        alarm(world, b, cock, parent)
        severity = perch_severity(perch, delay)
        perch_ent.meters["severity"] = float(severity)
        contained = is_contained(response, perch, delay)

        world.para()
        if contained:
            rescue(world, parent, response, cock, snag)
            lesson(world, parent, a, b, magic)
            world.para()
            outcome = "contained"
            badge_rule(world, parent, a, b, theme, cock)
        else:
            rescue_fail(world, parent, response, cock, perch)
            ranger_wait(world, parent, a, b, magic)
            world.para()
            outcome = "burned"
            badge_rule(world, parent, a, b, theme, cock)

    world.facts.update(
        instigator=a,
        cautioner=b,
        parent=parent,
        cock=cock,
        tool=tool,
        response=response,
        theme=theme,
        magic=magic,
        perch_cfg=perch,
        snag=snag,
        ignited=cock.meters["panicked"] >= THRESHOLD,
        outcome=outcome,
        delay=delay,
        severity=perch_severity(perch, delay) if not averted else 0,
        relation=relation,
    )
    return world


THEMES = {
    "barn_guardians": Theme(
        id="barn_guardians",
        scene="a bright hero headquarters behind the barn",
        props="A red towel became a cape, a feed bucket became a rescue drum, and a stick in the dirt became their map of the sky.",
        team_name="Barn Guardians",
        mission="save every creature before snack time",
        sendoff="They marched off through the sunshine a little slower than before, but far wiser too.",
    ),
    "rooftop_rangers": Theme(
        id="rooftop_rangers",
        scene="a secret sky-city above the garden path",
        props="A washing basket became a hover-car, a striped blanket became a cape, and chalk stars on the wall marked their patrol route.",
        team_name="Rooftop Rangers",
        mission="answer any crow for help",
        sendoff="This time their patrol began with listening eyes, steady feet, and no showy shortcuts at all.",
    ),
    "sunbeam_sentinels": Theme(
        id="sunbeam_sentinels",
        scene="a shining rescue base under the apricot tree",
        props="A cardboard box became a hero console, a blue scarf became a cape, and the stepping stones became launch pads.",
        team_name="Sunbeam Sentinels",
        mission="keep the yard gentle and brave",
        sendoff="Their capes still fluttered behind them, but now they fluttered beside patient hands and careful plans.",
    ),
}

MAGIC_TOOLS = {
    "storm_cape": MagicTool(
        id="storm_cape",
        label="the storm cape",
        phrase="the storm cape",
        sound="Whuff",
        warning="the storm cape is not for windy tricks without a grown-up",
        effect="The cape snapped wide and called a hard swirl of wind",
        tags={"magic", "wind"},
    ),
    "comet_wand": MagicTool(
        id="comet_wand",
        label="the comet wand",
        phrase="the comet wand",
        sound="Fizz",
        warning="the comet wand is not for surprise spells without a grown-up",
        effect="Blue sparks raced from the wand and stirred the air into a rushing spin",
        tags={"magic", "wand"},
    ),
    "thunder_boots": MagicTool(
        id="thunder_boots",
        label="the thunder boots",
        phrase="the thunder boots",
        sound="Boomp",
        warning="the thunder boots are not for reckless jumps without a grown-up",
        effect="The boots stamped the ground and bounced a booming gust upward",
        tags={"magic", "boots"},
    ),
}

PERCHES = {
    "coop_roof": Perch(
        id="coop_roof",
        label="coop roof",
        the="the coop roof",
        place_phrase="on the little coop roof",
        height=2,
        wobble="three loose straw tiles skittered down the slope",
        tags={"roof", "high_place"},
    ),
    "apple_tree": Perch(
        id="apple_tree",
        label="apple tree branch",
        the="the high apple tree branch",
        place_phrase="on the high apple tree branch",
        height=2,
        wobble="dry leaves and one small apple came tumbling down",
        tags={"tree", "high_place"},
    ),
    "hayloft_beam": Perch(
        id="hayloft_beam",
        label="hayloft beam",
        the="the hayloft beam",
        place_phrase="on the dusty hayloft beam",
        height=3,
        wobble="old dust puffed out and bits of straw rained onto the floor",
        tags={"beam", "high_place"},
    ),
    "fence_post": Perch(
        id="fence_post",
        label="fence post",
        the="the fence post",
        place_phrase="on the fence post",
        height=0,
        wobble="nothing much moved at all",
        low=True,
        tags={"low_place"},
    ),
}

SNAGS = {
    "ribbon": Snag(
        id="ribbon",
        label="a party ribbon",
        caught_phrase="a party ribbon was looped around one leg",
        free_phrase="the ribbon slid harmlessly free",
        tags={"ribbon"},
    ),
    "kite_string": Snag(
        id="kite_string",
        label="a kite string",
        caught_phrase="a kite string was twisted around one claw",
        free_phrase="the kite string came off in a soft little coil",
        tags={"string"},
    ),
    "bell_cord": Snag(
        id="bell_cord",
        label="a bell cord",
        caught_phrase="a bell cord had caught around his foot",
        free_phrase="the bell cord dropped away with one tiny jingle",
        tags={"rope"},
    ),
}

RESPONSES = {
    "ladder": Response(
        id="ladder",
        sense=3,
        power=4,
        text="set a ladder carefully against the perch, spoke to {cock} in a calm voice, and slipped the {snag} loose with steady fingers",
        fail="set up the ladder, but {cock} flapped away from it before anyone could reach him",
        qa_text="used a ladder and calm hands to free the cock",
        tags={"ladder", "animal_help"},
    ),
    "grain_trail": Response(
        id="grain_trail",
        sense=3,
        power=2,
        text="shook a little trail of grain onto the steps below and waited until {cock} picked his careful way down, where the {snag} could be undone",
        fail="shook out grain and called softly, but {cock} was too frightened to climb down from the {perch}",
        qa_text="coaxed the cock down with grain and then freed him",
        tags={"grain", "animal_help"},
    ),
    "blanket_catch": Response(
        id="blanket_catch",
        sense=2,
        power=2,
        text="opened a thick blanket low under the perch, so {cock} fluttered down into safety and the {snag} could be removed",
        fail="held out a blanket, but {cock} hopped past it and flapped to an even harder place to reach",
        qa_text="used a blanket to help the cock flutter down safely",
        tags={"blanket", "animal_help"},
    ),
    "leap_grab": Response(
        id="leap_grab",
        sense=1,
        power=1,
        text="jumped up and snatched for {cock}, somehow getting him down",
        fail="jumped for {cock}, but only frightened him into flying farther away",
        qa_text="tried to grab the cock in a jump",
        tags={"jump"},
    ),
}

GIRL_NAMES = ["Lily", "Mia", "Zoe", "Ava", "Ella", "Lucy", "Nora", "Rose"]
BOY_NAMES = ["Max", "Ben", "Sam", "Leo", "Finn", "Theo", "Jack", "Eli"]
TRAITS = ["careful", "steady", "gentle", "curious", "thoughtful", "sensible"]
COCK_NAMES = ["Copper", "Sunny", "Crimson", "Pepper"]


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    if not sensible_responses():
        return combos
    for theme_id in THEMES:
        for magic_id, magic in MAGIC_TOOLS.items():
            for perch_id, perch in PERCHES.items():
                if cock_at_risk(magic, perch):
                    combos.append((theme_id, magic_id, perch_id))
    return combos

if __name__ == "__main__":
    main()

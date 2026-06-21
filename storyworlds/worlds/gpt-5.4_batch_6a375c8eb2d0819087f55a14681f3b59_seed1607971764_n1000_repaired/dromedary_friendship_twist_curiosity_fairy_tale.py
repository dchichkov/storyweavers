#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/dromedary_friendship_twist_curiosity_fairy_tale.py
==============================================================================

A standalone story world for a fairy-tale domain about curiosity, a seeming
desert mystery, and a friendship with a dromedary.

Premise
-------
A small hero notices a strange wonder in the moonlit desert and goes looking.
A large shadow seems frightening at first, but the twist is that the shadow
belongs to a gentle dromedary who is trying to help. Together they uncover the
wonder, and the ending image proves that fear has turned into friendship.

The world model prefers only *reasonable* combinations:
- the chosen place must actually support the chosen mystery
- the dromedary's helping move must actually solve the mystery's physical need

Run it
------
python storyworlds/worlds/gpt-5.4/dromedary_friendship_twist_curiosity_fairy_tale.py
python storyworlds/worlds/gpt-5.4/dromedary_friendship_twist_curiosity_fairy_tale.py --place dune_sea --mystery glow --approach carry
python storyworlds/worlds/gpt-5.4/dromedary_friendship_twist_curiosity_fairy_tale.py --all
python storyworlds/worlds/gpt-5.4/dromedary_friendship_twist_curiosity_fairy_tale.py -n 5 --seed 7 --qa
python storyworlds/worlds/gpt-5.4/dromedary_friendship_twist_curiosity_fairy_tale.py --verify
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
TRUST_THRESHOLD = 7


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    role: str = ""
    traits: list[str] = field(default_factory=list)
    attrs: dict = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "woman", "doe", "hen"}
        male = {"boy", "man", "stag", "buck"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def tags(self):
        if not hasattr(self, "_tags"):
            object.__setattr__(self, "_tags", set())
        return self._tags


@dataclass
class Place:
    id: str
    label: str
    opening: str
    path_text: str
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
class Mystery:
    id: str
    hook: str
    rumor: str
    vision: str
    need: str
    truth: str
    reveal: str
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
class Approach:
    id: str
    label: str
    verb: str
    offer: str
    travel: str
    solves: set[str] = field(default_factory=set)
    gentleness: int = 0
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
class HeroKind:
    id: str
    type: str
    noun: str
    feet: str
    traits: set[str] = field(default_factory=set)
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
    def __init__(self, place: Place) -> None:
        self.place = place
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
        clone = World(self.place)
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


def _r_shadow_fear(world: World) -> list[str]:
    out: list[str] = []
    hero = world.entities.get("hero")
    friend = world.entities.get("dromedary")
    if not hero or not friend:
        return out
    if hero.meters["saw_shadow"] < THRESHOLD:
        return out
    sig = ("shadow_fear", hero.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    hero.memes["fear"] += 2
    out.append("__fear__")
    return out


def _r_kindness_softens(world: World) -> list[str]:
    out: list[str] = []
    hero = world.entities.get("hero")
    friend = world.entities.get("dromedary")
    if not hero or not friend:
        return out
    if friend.memes["kindness"] < THRESHOLD:
        return out
    sig = ("kindness_softens", hero.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    hero.memes["trust"] += 2
    if hero.memes["fear"] >= THRESHOLD:
        hero.memes["fear"] = max(0.0, hero.memes["fear"] - 1.0)
    out.append("__soften__")
    return out


def _r_help_builds_friendship(world: World) -> list[str]:
    out: list[str] = []
    hero = world.entities.get("hero")
    friend = world.entities.get("dromedary")
    if not hero or not friend:
        return out
    if hero.meters["wonder_seen"] < THRESHOLD:
        return out
    sig = ("friendship", hero.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    hero.memes["friendship"] += 2
    friend.memes["friendship"] += 2
    hero.memes["joy"] += 1
    friend.memes["joy"] += 1
    out.append("__friendship__")
    return out


CAUSAL_RULES = [
    Rule(name="shadow_fear", tag="emotion", apply=_r_shadow_fear),
    Rule(name="kindness_softens", tag="emotion", apply=_r_kindness_softens),
    Rule(name="help_builds_friendship", tag="emotion", apply=_r_help_builds_friendship),
]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
        changed = False
        for rule in CAUSAL_RULES:
            got = rule.apply(world)
            if got:
                changed = True
                produced.extend(s for s in got if not s.startswith("__"))
    if narrate:
        for sent in produced:
            world.say(sent)
    return produced


def mystery_supported(place: Place, mystery: Mystery) -> bool:
    return mystery.id in place.affords


def approach_works(mystery: Mystery, approach: Approach) -> bool:
    return mystery.need in approach.solves


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for place_id, place in PLACES.items():
        for mystery_id, mystery in MYSTERIES.items():
            if not mystery_supported(place, mystery):
                continue
            for approach_id, approach in APPROACHES.items():
                if approach_works(mystery, approach):
                    combos.append((place_id, mystery_id, approach_id))
    return sorted(combos)


def base_trust_for_trait(trait: str) -> int:
    return {
        "brave": 4,
        "curious": 3,
        "gentle": 3,
        "careful": 2,
        "shy": 1,
    }[trait]


def outcome_for(params: "StoryParams") -> str:
    approach = APPROACHES[params.approach]
    total = base_trust_for_trait(params.trait) + params.trust + approach.gentleness
    return "quick_friendship" if total >= TRUST_THRESHOLD else "slow_friendship"


def explain_rejection(place: Place, mystery: Mystery, approach: Approach) -> str:
    if not mystery_supported(place, mystery):
        return (
            f"(No story: {place.label.capitalize()} does not fit the mystery of "
            f"{mystery.hook}. Pick a place where that wonder could really appear.)"
        )
    if not approach_works(mystery, approach):
        return (
            f"(No story: the dromedary's move '{approach.label}' does not solve "
            f"the need '{mystery.need}'. The helper must be able to reach the wonder.)"
        )
    return "(No story: this combination does not make sense in the world.)"


def predict_wonder(world: World, mystery: Mystery, approach: Approach) -> dict:
    sim = world.copy()
    hero = sim.get("hero")
    drom = sim.get("dromedary")
    _approach_and_help(sim, hero, drom, mystery, approach, narrate=False)
    return {
        "wonder_seen": sim.get("hero").meters["wonder_seen"] >= THRESHOLD,
        "friendship": sim.get("hero").memes["friendship"],
        "fear": sim.get("hero").memes["fear"],
    }


def introduce(world: World, hero: Entity, place: Place) -> None:
    world.say(
        f"In the silver hush of evening, {hero.id} the little {hero.attrs['noun']} "
        f"lived beside {place.label}. {place.opening}"
    )
    world.say(
        f"{hero.id} was known for asking one more question after everyone else had "
        f"gone quiet."
    )


def first_hook(world: World, hero: Entity, mystery: Mystery) -> None:
    hero.memes["curiosity"] += 2
    world.say(
        f"That night, {hero.pronoun('subject')} noticed {mystery.hook}. "
        f"{mystery.rumor}"
    )
    world.say(
        f'So {hero.pronoun("subject")} whispered, "I will go and see what secret '
        f"the dark is keeping."
    )


def travel(world: World, hero: Entity, place: Place) -> None:
    hero.meters["steps"] += 1
    world.say(
        f"With {hero.attrs['feet']} and a heart full of questions, "
        f"{hero.pronoun('subject')} followed {place.path_text}."
    )


def glimpse_shadow(world: World, hero: Entity, dromedary: Entity) -> None:
    hero.meters["saw_shadow"] += 1
    propagate(world, narrate=False)
    world.say(
        f"Then a long shadow rose over the sand. It had one high hump and long, "
        f"swaying legs, and for a moment {hero.id} thought a desert giant had "
        f"stepped out of an old tale."
    )


def hide_or_hesitate(world: World, hero: Entity) -> None:
    if hero.memes["fear"] >= 2:
        world.say(
            f"{hero.pronoun('subject').capitalize()} ducked behind a stone and peeped "
            f"out with wide eyes, too curious to run and too startled to come closer."
        )
    else:
        world.say(
            f"{hero.pronoun('subject').capitalize()} stopped in the path, trembling a "
            f"little but still listening."
        )


def dromedary_speaks(world: World, hero: Entity, dromedary: Entity, mystery: Mystery, approach: Approach) -> None:
    dromedary.memes["kindness"] += 1
    world.facts["predicted"] = predict_wonder(world, mystery, approach)
    propagate(world, narrate=False)
    world.say(
        f'"Do not be afraid," said the shadow, and now the voice sounded warm as a '
        f"blanket in winter. It was not a monster at all, but a gentle dromedary "
        f'named {dromedary.id}. "{approach.offer}"'
    )


def accept_or_pause(world: World, hero: Entity, dromedary: Entity, outcome: str) -> None:
    if outcome == "quick_friendship":
        hero.memes["trust"] += 1
        world.say(
            f"The twist of it made {hero.id} blink. The very creature that had seemed "
            f"the most frightening was speaking the softest words."
        )
        world.say(
            f'{hero.pronoun("subject").capitalize()} stepped out from hiding and nodded. '
            f'"Then I will trust you," {hero.pronoun("subject")} said.'
        )
    else:
        world.say(
            f"The twist of it made {hero.id} blink. The terrible giant was only a kind "
            f"dromedary with patient eyes."
        )
        world.say(
            f'{hero.pronoun("subject").capitalize()} stayed still for one more breath, '
            f'then asked, "Will you stay beside me if I am still a little afraid?"'
        )
        world.say(
            f'"All the way," said {dromedary.id}, lowering {dromedary.pronoun("possessive")} head.'
        )
        hero.memes["trust"] += 1


def _approach_and_help(world: World, hero: Entity, dromedary: Entity, mystery: Mystery, approach: Approach, narrate: bool = True) -> None:
    hero.meters["help_received"] += 1
    dromedary.meters["help_given"] += 1
    hero.meters["wonder_seen"] += 1
    propagate(world, narrate=False)
    if narrate:
        world.say(
            f"{dromedary.id} {approach.verb}, and together they {approach.travel}. "
            f"At last {mystery.vision}"
        )


def reveal_wonder(world: World, hero: Entity, dromedary: Entity, mystery: Mystery) -> None:
    world.say(mystery.truth)
    world.say(
        f"{mystery.reveal} {hero.id} laughed then, not because the wonder was gone, "
        f"but because it had become even better once it was shared."
    )


def seal_friendship(world: World, hero: Entity, dromedary: Entity, outcome: str, place: Place) -> None:
    if outcome == "quick_friendship":
        world.say(
            f"Before the moon had crossed half the sky, the little {hero.attrs['noun']} "
            f"and the dromedary were already walking side by side like old friends."
        )
    else:
        world.say(
            f"At first {hero.id} walked close to {dromedary.id}'s shadow, and then, "
            f"little by little, close to {dromedary.pronoun('possessive')} smile."
        )
    world.say(
        f"From that night on, whenever {place.label} held a new riddle, {hero.id} "
        f"did not hunt for secrets alone."
    )
    world.say(
        f"Sometimes the moon would find them there together: one small friend asking "
        f"questions, and one tall dromedary kneeling beside the answer."
    )
def tell(
    mystery: Mystery,
    approach: Approach,
    hero_name: str,
    hero_kind: HeroKind,
    trait: Trait,
    dromedary_name: str,
    trust: Trust,
    place=None,
) -> World:
    if hero_kind is None:
        raise StoryError("(Internal error: hero kind is required.)")
    world = World(place)
    hero = world.add(
        Entity(
            id=hero_name,
            kind="character",
            type=hero_kind.type,
            role="hero",
            label=hero_name,
            traits=[trait],
            attrs={"noun": hero_kind.noun, "feet": hero_kind.feet},
        )
    )
    dromedary = world.add(
        Entity(
            id=dromedary_name,
            kind="character",
            type="dromedary",
            role="friend",
            label=dromedary_name,
            traits=["tall", "patient"],
            attrs={"species": "dromedary"},
        )
    )

    hero.memes["curiosity"] = 1
    hero.memes["fear"] = 0
    hero.memes["trust"] = float(trust)
    hero.memes["friendship"] = 0
    dromedary.memes["kindness"] = 0
    dromedary.memes["friendship"] = 0
    world.facts["place"] = place
    world.facts["mystery"] = mystery
    world.facts["approach"] = approach
    world.facts["hero_kind"] = hero_kind
    world.facts["initial_trust"] = trust
    world.facts["trait"] = trait

    introduce(world, hero, place)
    first_hook(world, hero, mystery)

    world.para()
    travel(world, hero, place)
    glimpse_shadow(world, hero, dromedary)
    hide_or_hesitate(world, hero)

    world.para()
    dromedary_speaks(world, hero, dromedary, mystery, approach)
    outcome = outcome_for(
        StoryParams(
            place=place.id,
            mystery=mystery.id,
            approach=approach.id,
            hero_name=hero_name,
            hero_kind=hero_kind.id,
            trait=trait,
            dromedary_name=dromedary_name,
            trust=trust,
            seed=None,
        )
    )
    accept_or_pause(world, hero, dromedary, outcome)
    _approach_and_help(world, hero, dromedary, mystery, approach, narrate=True)

    world.para()
    reveal_wonder(world, hero, dromedary, mystery)
    seal_friendship(world, hero, dromedary, outcome, place)

    world.facts.update(
        hero=hero,
        dromedary=dromedary,
        outcome=outcome,
        friendship=hero.memes["friendship"] >= THRESHOLD,
        wonder_seen=hero.meters["wonder_seen"] >= THRESHOLD,
    )
    return world
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


PLACES = {
    "moon_oasis": Place(
        id="moon_oasis",
        label="the Moon Oasis",
        opening="Date palms leaned over a round pool where the moon liked to practice its face.",
        path_text="the shining edge of the water and under the sleepy palms",
        affords={"bell", "whisper"},
        tags={"oasis"},
    ),
    "dune_sea": Place(
        id="dune_sea",
        label="the Sea of Dunes",
        opening="The sand rolled away in golden waves, and every crest looked like a secret waiting to be named.",
        path_text="a ribbon path between the dunes",
        affords={"glow"},
        tags={"desert"},
    ),
    "date_grove": Place(
        id="date_grove",
        label="the Date Grove",
        opening="Tall palms stood with their crowns whispering together above the sleeping earth.",
        path_text="between the trunks where moonbeams fell in thin silver stripes",
        affords={"bell"},
        tags={"grove"},
    ),
}

MYSTERIES = {
    "bell": Mystery(
        id="bell",
        hook="a silver ringing high above the date palms",
        rumor="Some said a star had dropped a tiny bell into the trees.",
        vision="they saw a moon-bright shell hanging in the highest palm, chiming whenever the breeze touched it",
        need="high",
        truth="It was only the wind playing a shell against the dates, yet the music was so lovely that it still felt enchanted.",
        reveal="The shell sang again, and even the leaves seemed pleased",
        tags={"wind", "shell"},
    ),
    "glow": Mystery(
        id="glow",
        hook="a blue glow blinking beyond the third dune",
        rumor="Some said a lantern spirit was sewing patches of light into the night.",
        vision="they reached the dune-top and found a hollow full of blue beetles, opening and closing their wings like little lamps",
        need="far",
        truth="No lantern spirit had stitched the dark at all; it was a crowd of beetles making their own soft festival.",
        reveal="The hollow shone like a bowl of fallen stars",
        tags={"beetles", "light"},
    ),
    "whisper": Mystery(
        id="whisper",
        hook="a whispering sound curling through the reeds by the water",
        rumor="Some said a hidden princess was speaking to the fish in a silver language.",
        vision="they looked through the reeds and found a striped reed flute, left there by the wind and the water together",
        need="hidden",
        truth="The princess was only water threading through the reed flute, but the tune was delicate enough for a palace.",
        reveal="The reeds bowed and the little flute answered the breeze",
        tags={"water", "reeds"},
    ),
}

APPROACHES = {
    "kneel": Approach(
        id="kneel",
        label="kneel low",
        verb="folded down low upon the sand",
        offer="Climb gently onto my back, and the high places will not mock your small feet",
        travel="rose together until the branches no longer seemed so far away",
        solves={"high"},
        gentleness=3,
        tags={"height"},
    ),
    "carry": Approach(
        id="carry",
        label="carry across the dunes",
        verb="bent one long leg and invited the little traveler up",
        offer="Ride with me, and the far places will come close enough for your eyes",
        travel="crossed the dune backs in slow, rocking steps",
        solves={"far"},
        gentleness=2,
        tags={"travel"},
    ),
    "part_reeds": Approach(
        id="part_reeds",
        label="part the reeds",
        verb="reached with gentle lips and a careful neck",
        offer="Stand by my shoulder, and I will open what the reeds have hidden",
        travel="stood together by the pool while the reeds quietly opened",
        solves={"hidden"},
        gentleness=2,
        tags={"reeds"},
    ),
}

HERO_KINDS = {
    "fennec": HeroKind(
        id="fennec",
        type="girl",
        noun="fennec fox",
        feet="quick little paws",
        traits={"curious", "shy"},
    ),
    "hare": HeroKind(
        id="hare",
        type="boy",
        noun="hare",
        feet="light springing feet",
        traits={"brave", "curious"},
    ),
    "gazelle": HeroKind(
        id="gazelle",
        type="girl",
        noun="gazelle",
        feet="soft dancing hooves",
        traits={"gentle", "careful"},
    ),
}

HERO_NAMES = {
    "girl": ["Nuri", "Laleh", "Mina", "Soraya", "Tali"],
    "boy": ["Rafi", "Sami", "Idris", "Kian", "Omar"],
}

DROMEDARY_NAMES = ["Saffron", "Amber", "Cedar", "Juniper", "Tamar"]

TRAITS = ["brave", "curious", "gentle", "careful", "shy"]


KNOWLEDGE = {
    "dromedary": [
        (
            "What is a dromedary?",
            "A dromedary is a kind of camel with one hump. It can walk a long way in hot, dry places."
        )
    ],
    "desert": [
        (
            "What is a desert?",
            "A desert is a very dry place with little rain. Many deserts have sand, strong sun, and animals that know how to live there."
        )
    ],
    "oasis": [
        (
            "What is an oasis?",
            "An oasis is a place in the desert where there is water and plants can grow. Animals and people can rest there."
        )
    ],
    "wind": [
        (
            "How can wind make music?",
            "Wind can make music when it blows through or against something that can vibrate. That is why reeds, shells, and strings can sing in a breeze."
        )
    ],
    "beetles": [
        (
            "Why do some beetles glow?",
            "Some beetles glow to send signals with their bodies. Their light can help them find one another in the dark."
        )
    ],
    "reeds": [
        (
            "What are reeds?",
            "Reeds are tall water plants with long stems. They grow by ponds and streams and rustle when the wind moves them."
        )
    ],
    "friendship": [
        (
            "How can helping someone start a friendship?",
            "When someone helps you kindly, it can make you feel safe and cared for. Sharing a hard or special moment often helps friendship grow."
        )
    ],
    "curiosity": [
        (
            "What is curiosity?",
            "Curiosity is the feeling that makes you want to know more. It helps you ask questions and look closely at the world."
        )
    ],
}
KNOWLEDGE_ORDER = ["dromedary", "desert", "oasis", "wind", "beetles", "reeds", "friendship", "curiosity"]


def generation_prompts(world: World) -> list[str]:
    hero = world.facts["hero"]
    mystery = world.facts["mystery"]
    place = world.facts["place"]
    return [
        (
            f'Write a short fairy tale for a 3-to-5-year-old that includes the word '
            f'"dromedary" and begins with a curious child-sized animal noticing {mystery.hook}.'
        ),
        (
            f"Tell a gentle fairy tale where {hero.id}, a little {hero.attrs['noun']}, "
            f"goes out into {place.label} to solve a mystery and learns that the frightening "
            f"shadow is really a friend."
        ),
        (
            "Write a fairy-tale story about curiosity, a twist in the middle, and a warm new "
            "friendship with a dromedary."
        ),
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    hero = world.facts["hero"]
    dromedary = world.facts["dromedary"]
    mystery = world.facts["mystery"]
    place = world.facts["place"]
    approach = world.facts["approach"]
    outcome = world.facts["outcome"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {hero.id}, a little {hero.attrs['noun']}, and a gentle dromedary named {dromedary.id}. "
            f"The story follows how they meet in {place.label}."
        ),
        (
            f"Why did {hero.id} go out into the night?",
            f"{hero.id} was curious about {mystery.hook}. The mystery pulled {hero.pronoun('object')} forward because {hero.pronoun('subject')} wanted to know what secret the dark was hiding."
        ),
        (
            "What was the twist in the story?",
            f"The big shadow that looked like a desert giant was not dangerous at all. It was really {dromedary.id} the dromedary, who wanted to help."
        ),
        (
            f"How did {dromedary.id} help {hero.id}?",
            f"{dromedary.id} helped by using {approach.label} so the mystery could be reached. Because of that help, {hero.id} was able to see the wonder at last."
        ),
        (
            f"What did they discover?",
            f"They discovered that {mystery.truth[0].lower() + mystery.truth[1:]} "
            f"The answer was still beautiful, even after the mystery was understood."
        ),
    ]
    if outcome == "quick_friendship":
        qa.append(
            (
                f"How did {hero.id} feel at the end?",
                f"{hero.id} felt happy and safe with {dromedary.id}. Fear changed quickly into trust because the dromedary spoke kindly and helped right away."
            )
        )
    else:
        qa.append(
            (
                f"How did {hero.id} and {dromedary.id} become friends if {hero.id} was scared at first?",
                f"{hero.id} stayed a little afraid for a moment, but {dromedary.id} promised to stay beside {hero.pronoun('object')}. Walking and wondering together slowly turned the fear into trust."
            )
        )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags = {"dromedary", "friendship", "curiosity"}
    place = world.facts["place"]
    mystery = world.facts["mystery"]
    if "oasis" in place.tags:
        tags.add("oasis")
    if place.id == "dune_sea":
        tags.add("desert")
    tags |= set(mystery.tags)
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
    for ent in list(world.entities.values()):
        bits = []
        meters = {k: v for k, v in ent.meters.items() if v}
        memes = {k: v for k, v in ent.memes.items() if v}
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if ent.role:
            bits.append(f"role={ent.role}")
        if ent.attrs:
            shown = {k: v for k, v in ent.attrs.items() if v}
            if shown:
                bits.append(f"attrs={shown}")
        lines.append(f"  {ent.id:10} ({ent.type:10}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    return "\n".join(lines)
@dataclass
class StoryParams:
    place: str
    mystery: str
    approach: str
    hero_name: str
    hero_kind: str
    trait: str
    dromedary_name: str
    trust: int = 2
    seed: Optional[int] = None




CURATED = [
    StoryParams(
        place="date_grove",
        mystery="bell",
        approach="kneel",
        hero_name="Nuri",
        hero_kind="fennec",
        trait="curious",
        dromedary_name="Saffron",
        trust=2,
        seed=101,
    ),
    StoryParams(
        place="dune_sea",
        mystery="glow",
        approach="carry",
        hero_name="Rafi",
        hero_kind="hare",
        trait="brave",
        dromedary_name="Amber",
        trust=3,
        seed=102,
    ),
    StoryParams(
        place="moon_oasis",
        mystery="whisper",
        approach="part_reeds",
        hero_name="Mina",
        hero_kind="gazelle",
        trait="shy",
        dromedary_name="Cedar",
        trust=1,
        seed=103,
    ),
    StoryParams(
        place="moon_oasis",
        mystery="bell",
        approach="kneel",
        hero_name="Soraya",
        hero_kind="gazelle",
        trait="careful",
        dromedary_name="Juniper",
        trust=1,
        seed=104,
    ),
]


ASP_RULES = r"""
supports(P, M) :- place(P), affords(P, M).
works(M, A) :- mystery(M), need(M, N), approach(A), solves(A, N).
valid(P, M, A) :- supports(P, M), works(M, A).

base_trust(brave,4).
base_trust(curious,3).
base_trust(gentle,3).
base_trust(careful,2).
base_trust(shy,1).

total(B + T + G) :- trait(Tr), base_trust(Tr,B), trust(T), chosen_approach(A), gentleness(A,G).
quick_friendship :- total(V), threshold(K), V >= K.
slow_friendship :- not quick_friendship.

outcome(quick_friendship) :- quick_friendship.
outcome(slow_friendship) :- slow_friendship.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for place_id, place in PLACES.items():
        lines.append(asp.fact("place", place_id))
        for afford in sorted(place.affords):
            lines.append(asp.fact("affords", place_id, afford))
    for mystery_id, mystery in MYSTERIES.items():
        lines.append(asp.fact("mystery", mystery_id))
        lines.append(asp.fact("need", mystery_id, mystery.need))
    for approach_id, approach in APPROACHES.items():
        lines.append(asp.fact("approach", approach_id))
        lines.append(asp.fact("gentleness", approach_id, approach.gentleness))
        for need in sorted(approach.solves):
            lines.append(asp.fact("solves", approach_id, need))
    for trait in TRAITS:
        lines.append(asp.fact("trait_name", trait))
    lines.append(asp.fact("threshold", TRUST_THRESHOLD))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("", "#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_outcome(params: StoryParams) -> str:
    import asp

    program = "\n".join(
        [
            asp.fact("trait", params.trait),
            asp.fact("trust", params.trust),
            asp.fact("chosen_approach", params.approach),
        ]
    )
    model = asp.one_model(asp_program(program, "#show outcome/1."))
    atoms = asp.atoms(model, "outcome")
    return atoms[0][0] if atoms else "?"


def asp_verify() -> int:
    rc = 0
    py_set = set(valid_combos())
    asp_set = set(asp_valid_combos())
    if py_set == asp_set:
        print(f"OK: valid combo gate matches ({len(py_set)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos:")
        if py_set - asp_set:
            print("  only in python:", sorted(py_set - asp_set))
        if asp_set - py_set:
            print("  only in clingo:", sorted(asp_set - py_set))

    cases = list(CURATED)
    parser = build_parser()
    for s in range(40):
        try:
            params = resolve_params(parser.parse_args([]), random.Random(s))
        except StoryError:
            continue
        params.seed = s
        cases.append(params)
    bad = 0
    for params in cases:
        py = outcome_for(params)
        cl = asp_outcome(params)
        if py != cl:
            bad += 1
    if bad == 0:
        print(f"OK: outcome model matches on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {bad}/{len(cases)} outcome comparisons differ.")

    try:
        smoke_params = resolve_params(parser.parse_args([]), random.Random(123))
        smoke_params.seed = 123
        sample = generate(smoke_params)
        if not sample.story.strip():
            raise StoryError("(Verify failed: generated story was empty.)")
        emit(sample, trace=False, qa=False, header="")
        print("OK: smoke test generation succeeded.")
    except Exception as err:
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Fairy-tale story world: curiosity, a twist, and friendship with a dromedary."
    )
    ap.add_argument("--place", choices=sorted(PLACES))
    ap.add_argument("--mystery", choices=sorted(MYSTERIES))
    ap.add_argument("--approach", choices=sorted(APPROACHES))
    ap.add_argument("--hero-kind", choices=sorted(HERO_KINDS))
    ap.add_argument("--trait", choices=sorted(TRAITS))
    ap.add_argument("--hero-name")
    ap.add_argument("--dromedary-name")
    ap.add_argument("--trust", type=int, choices=[0, 1, 2, 3, 4], help="initial trust before the twist")
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list valid combos from the ASP twin")
    ap.add_argument("--verify", action="store_true", help="check ASP/Python parity and run a smoke test")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def _hero_name_for(rng: random.Random, kind_id: str, explicit: Optional[str]) -> str:
    if explicit:
        return explicit
    kind = HERO_KINDS[kind_id]
    return rng.choice(HERO_NAMES[kind.type])


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.place and args.mystery and args.approach:
        place = PLACES[args.place]
        mystery = MYSTERIES[args.mystery]
        approach = APPROACHES[args.approach]
        if not (mystery_supported(place, mystery) and approach_works(mystery, approach)):
            raise StoryError(explain_rejection(place, mystery, approach))

    combos = [
        combo
        for combo in valid_combos()
        if (args.place is None or combo[0] == args.place)
        and (args.mystery is None or combo[1] == args.mystery)
        and (args.approach is None or combo[2] == args.approach)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    place_id, mystery_id, approach_id = rng.choice(combos)
    hero_kind = args.hero_kind or rng.choice(sorted(HERO_KINDS))
    trait = args.trait or rng.choice(sorted(TRAITS))
    trust = args.trust if args.trust is not None else rng.randint(0, 4)
    hero_name = _hero_name_for(rng, hero_kind, args.hero_name)
    dromedary_name = args.dromedary_name or rng.choice(DROMEDARY_NAMES)

    return StoryParams(
        place=place_id,
        mystery=mystery_id,
        approach=approach_id,
        hero_name=hero_name,
        hero_kind=hero_kind,
        trait=trait,
        dromedary_name=dromedary_name,
        trust=trust,
        seed=None,
    )


def generate(params: StoryParams) -> StorySample:
    if params.place not in PLACES:
        raise StoryError(f"(Unknown place: {params.place})")
    if params.mystery not in MYSTERIES:
        raise StoryError(f"(Unknown mystery: {params.mystery})")
    if params.approach not in APPROACHES:
        raise StoryError(f"(Unknown approach: {params.approach})")
    if params.hero_kind not in HERO_KINDS:
        raise StoryError(f"(Unknown hero kind: {params.hero_kind})")
    if params.trait not in TRAITS:
        raise StoryError(f"(Unknown trait: {params.trait})")

    place = PLACES[params.place]
    mystery = MYSTERIES[params.mystery]
    approach = APPROACHES[params.approach]
    if not mystery_supported(place, mystery) or not approach_works(mystery, approach):
        raise StoryError(explain_rejection(place, mystery, approach))

    world = tell(
        place=place,
        mystery=mystery,
        approach=approach,
        hero_name=params.hero_name,
        hero_kind=HERO_KINDS[params.hero_kind],
        trait=params.trait,
        dromedary_name=params.dromedary_name,
        trust=params.trust,
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
        print(f"{len(combos)} compatible (place, mystery, approach) combos:\n")
        for place, mystery, approach in combos:
            print(f"  {place:11} {mystery:8} {approach}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)

    samples: list[StorySample] = []
    if args.all:
        samples = [generate(params) for params in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
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
            header = (
                f"### {p.hero_name} at {p.place}: {p.mystery} with {p.approach} "
                f"({outcome_for(p)})"
            )
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()

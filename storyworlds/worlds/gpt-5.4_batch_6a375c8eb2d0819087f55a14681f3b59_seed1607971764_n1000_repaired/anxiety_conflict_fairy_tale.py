#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/anxiety_conflict_fairy_tale.py
=========================================================

A standalone story world for gentle fairy-tale stories about a child who carries
a small peace-making object into a woodland quarrel. The child feels anxiety,
the conflict grows noisy and gloomy, and a fitting remedy plus a calming token
lets the child speak brave words and help the quarrel end.

The world model keeps two axes in play:

* physical meters: gloom, sparkle, offered
* emotional memes: anger, anxiety, courage, relief, trust

Reasonableness constraint
-------------------------
Not every place, quarrel, remedy, and calming aid make sense together.

* A place must actually be one where that quarrel could happen.
* A remedy must fit the kind of conflict.
* The child's inner steadiness (trait) plus the aid's comfort must be strong
  enough for the child to act through anxiety.

So the world refuses weak pairings such as a silver needle for a bridge dispute,
or an underpowered calming aid for the fiercest quarrel.

Run it
------
    python storyworlds/worlds/gpt-5.4/anxiety_conflict_fairy_tale.py
    python storyworlds/worlds/gpt-5.4/anxiety_conflict_fairy_tale.py --place moon_bridge --conflict bridge
    python storyworlds/worlds/gpt-5.4/anxiety_conflict_fairy_tale.py --remedy silver_needle
    python storyworlds/worlds/gpt-5.4/anxiety_conflict_fairy_tale.py --all
    python storyworlds/worlds/gpt-5.4/anxiety_conflict_fairy_tale.py -n 5 --seed 7 --qa
    python storyworlds/worlds/gpt-5.4/anxiety_conflict_fairy_tale.py --verify
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

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
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
    tags: set[str] = field(default_factory=set)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "grandmother", "woman", "fairy_godmother"}
        male = {"boy", "father", "grandfather", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def title_word(self) -> str:
        return {
            "grandmother": "grandmother",
            "grandfather": "grandfather",
            "fairy_godmother": "godmother",
        }.get(self.type, self.type)
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def phrase(self) -> str:
        return str(getattr(self, "_phrase", None) or getattr(self, "label_word", None) or getattr(self, "label", None) or getattr(self, "id", self.__class__.__name__.lower()))

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)


@dataclass
class Setting:
    id: str
    label: str
    path: str
    image: str
    affords: set[str] = field(default_factory=set)
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
class Conflict:
    id: str
    title: str
    severity: int
    creature1: str
    creature2: str
    pair_noun: str
    object_label: str
    quarrel_line: str
    need_line: str
    place_detail: str
    fits: set[str] = field(default_factory=set)
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
class Remedy:
    id: str
    label: str
    phrase: str
    action: str
    speech: str
    target_conflicts: set[str] = field(default_factory=set)
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
class Aid:
    id: str
    label: str
    comfort: int
    phrase: str
    remember: str
    carry: str
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
class Trait:
    id: str
    heart: int
    adjective: str
    anxious_style: str
    brave_style: str
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
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {
            "setting_id": setting.id,
            "peace_made": False,
            "predicted_anxiety": 0,
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
        clone = World(self.setting)
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


def _r_quarrel_gloom(world: World) -> list[str]:
    hero = world.get("hero")
    first = world.get("first")
    second = world.get("second")
    place = world.get("place")
    if first.memes["anger"] < THRESHOLD or second.memes["anger"] < THRESHOLD:
        return []
    sig = ("gloom",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    hero.memes["anxiety"] += 1
    place.meters["gloom"] += 1
    return ["__gloom__"]


def _r_memory_steadies(world: World) -> list[str]:
    hero = world.get("hero")
    if hero.meters["remembered"] < THRESHOLD:
        return []
    sig = ("steady",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    hero.memes["courage"] += 1
    hero.memes["anxiety"] = max(0.0, hero.memes["anxiety"] - 1.0)
    return ["__steady__"]


def _r_make_peace(world: World) -> list[str]:
    hero = world.get("hero")
    remedy = world.get("remedy")
    first = world.get("first")
    second = world.get("second")
    place = world.get("place")
    if remedy.meters["offered"] < THRESHOLD:
        return []
    if hero.memes["speaks"] < THRESHOLD:
        return []
    if not remedy.attrs.get("fits", False):
        return []
    sig = ("peace",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    first.memes["anger"] = 0.0
    second.memes["anger"] = 0.0
    first.memes["trust"] += 1
    second.memes["trust"] += 1
    hero.memes["relief"] += 1
    hero.memes["courage"] += 1
    hero.memes["anxiety"] = 0.0
    place.meters["gloom"] = 0.0
    place.meters["sparkle"] += 1
    world.facts["peace_made"] = True
    return ["__peace__"]


CAUSAL_RULES = [
    Rule(name="quarrel_gloom", tag="social", apply=_r_quarrel_gloom),
    Rule(name="memory_steadies", tag="emotion", apply=_r_memory_steadies),
    Rule(name="make_peace", tag="social", apply=_r_make_peace),
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
                produced.extend(s for s in sents if not s.startswith("__"))
    if narrate:
        for sent in produced:
            world.say(sent)
    return produced


SETTINGS = {
    "moon_bridge": Setting(
        id="moon_bridge",
        label="the Moon Bridge",
        path="the white path to the Moon Bridge",
        image="a silver bridge arched over dark water",
        affords={"bridge"},
    ),
    "bramble_clearing": Setting(
        id="bramble_clearing",
        label="the Bramble Clearing",
        path="the ferny path to the Bramble Clearing",
        image="a round green clearing ringed with blackberries",
        affords={"acorns"},
    ),
    "mossy_hollow": Setting(
        id="mossy_hollow",
        label="the Mossy Hollow",
        path="the soft path to the Mossy Hollow",
        image="a hollow under an old tree where moss shone like velvet",
        affords={"tear"},
    ),
    "brook_meadow": Setting(
        id="brook_meadow",
        label="the Brook Meadow",
        path="the winding path to the Brook Meadow",
        image="a meadow beside a narrow brook where reeds nodded in the breeze",
        affords={"bridge", "acorns"},
    ),
}

CONFLICTS = {
    "bridge": Conflict(
        id="bridge",
        title="a bridge quarrel",
        severity=3,
        creature1="a goat in a blue scarf",
        creature2="a troll with moss on his hat",
        pair_noun="the goat and the troll",
        object_label="the narrow bridge",
        quarrel_line="Each one stamped and said it was their turn to cross first.",
        need_line="They did not truly need a fight. They needed a fair turn.",
        place_detail="Only one pair of feet could fit on the bridge at a time.",
        fits={"turn_token"},
        tags={"bridge", "sharing", "fairness"},
    ),
    "acorns": Conflict(
        id="acorns",
        title="an acorn quarrel",
        severity=2,
        creature1="a squirrel with a striped tail",
        creature2="a hedgehog with bright black eyes",
        pair_noun="the squirrel and the hedgehog",
        object_label="the last basket of acorns",
        quarrel_line="Both had their paws on the basket, and neither would let go.",
        need_line="They did not truly need more shouting. They needed enough to share.",
        place_detail="Golden acorn caps lay all around like tiny cups.",
        fits={"shared_loaf"},
        tags={"acorns", "sharing", "food"},
    ),
    "tear": Conflict(
        id="tear",
        title="a torn-cloak quarrel",
        severity=2,
        creature1="a fox in a travel cloak",
        creature2="a raven with a silver feather",
        pair_noun="the fox and the raven",
        object_label="a torn travel cloak",
        quarrel_line="The fox blamed the raven for the rip, and the raven blamed the fox for the snagging branch.",
        need_line="They did not truly need blame. They needed the tear mended.",
        place_detail="The cloak hung between them like a sad little flag.",
        fits={"silver_needle"},
        tags={"mending", "cloak", "repair"},
    ),
}

REMEDIES = {
    "turn_token": Remedy(
        id="turn_token",
        label="a moon-bell",
        phrase="a tiny moon-bell on a blue cord",
        action="held up the moon-bell and rang one clear note",
        speech='"One ring for one turn, and then the bridge belongs to the next feet."',
        target_conflicts={"bridge"},
        tags={"turns", "bridge", "fairness"},
    ),
    "shared_loaf": Remedy(
        id="shared_loaf",
        label="a honey loaf",
        phrase="a warm honey loaf wrapped in cloth",
        action="set down the honey loaf and broke it into even pieces",
        speech='"Here is enough for two, and then the acorns can be counted calmly."',
        target_conflicts={"acorns"},
        tags={"bread", "sharing", "food"},
    ),
    "silver_needle": Remedy(
        id="silver_needle",
        label="a silver needle",
        phrase="a silver needle with a spool of green thread",
        action="lifted the silver needle and drew the torn edges gently together",
        speech='"Let the thread do the joining while your angry words rest."',
        target_conflicts={"tear"},
        tags={"needle", "mending", "repair"},
    ),
}

AIDS = {
    "star_lantern": Aid(
        id="star_lantern",
        label="a star lantern",
        comfort=2,
        phrase="a star lantern no bigger than an apple",
        remember="its soft gold light made the dark seem less crowded",
        carry="The lantern swung from the child's wrist and painted little stars on the path.",
        tags={"lantern", "light"},
    ),
    "grandmother_scarf": Aid(
        id="grandmother_scarf",
        label="grandmother's scarf",
        comfort=2,
        phrase="grandmother's soft red scarf",
        remember="it still smelled of cinnamon and warm bread",
        carry="The scarf lay around the child's shoulders like a small brave hug.",
        tags={"scarf", "comfort"},
    ),
    "glass_heart": Aid(
        id="glass_heart",
        label="a glass heart charm",
        comfort=3,
        phrase="a glass heart charm",
        remember="when the child pressed it, it felt cool and steady in the palm",
        carry="The charm rested in the child's pocket, bright as a drop of frozen dawn.",
        tags={"charm", "comfort"},
    ),
    "pocket_song": Aid(
        id="pocket_song",
        label="a pocket song",
        comfort=1,
        phrase="a little pocket song",
        remember="the old tune gave the child just enough breath to keep going",
        carry="The child hummed the pocket song so softly that even the daisies had to lean in to hear it.",
        tags={"song", "comfort"},
    ),
}

TRAITS = {
    "timid": Trait(
        id="timid",
        heart=0,
        adjective="timid",
        anxious_style="small feelings fluttered inside like trapped moths",
        brave_style="the brave part arrived only after a long breath",
    ),
    "gentle": Trait(
        id="gentle",
        heart=1,
        adjective="gentle",
        anxious_style="anxiety made the child's fingers want to curl up small",
        brave_style="gentleness helped the words come out soft instead of sharp",
    ),
    "curious": Trait(
        id="curious",
        heart=1,
        adjective="curious",
        anxious_style="anxiety pricked at the child, but wonder kept one eye open",
        brave_style="curiosity made the child look for the knot that could be untied",
    ),
    "steadfast": Trait(
        id="steadfast",
        heart=2,
        adjective="steadfast",
        anxious_style="even with anxiety in the chest, the child's feet did not turn back",
        brave_style="steadiness held the voice straight and clear",
    ),
}

GIRL_NAMES = ["Lina", "Mira", "Tessa", "Nella", "Ivy", "Ada", "Elsie", "Wren"]
BOY_NAMES = ["Tobin", "Milo", "Rowan", "Ned", "Pip", "Evan", "Leo", "Finn"]


def remedy_fits(conflict: Conflict, remedy: Remedy) -> bool:
    return conflict.id in remedy.target_conflicts


def calm_enough(trait: Trait, aid: Aid, conflict: Conflict) -> bool:
    return trait.heart + aid.comfort >= conflict.severity


def valid_combos() -> list[tuple[str, str, str, str, str]]:
    combos: list[tuple[str, str, str, str, str]] = []
    for place_id, setting in SETTINGS.items():
        for conflict_id in sorted(setting.affords):
            conflict = CONFLICTS[conflict_id]
            for remedy_id, remedy in REMEDIES.items():
                if not remedy_fits(conflict, remedy):
                    continue
                for aid_id, aid in AIDS.items():
                    for trait_id, trait in TRAITS.items():
                        if calm_enough(trait, aid, conflict):
                            combos.append((place_id, conflict_id, remedy_id, aid_id, trait_id))
    return combos


@dataclass
class StoryParams:
    place: str
    conflict: str
    remedy: str
    aid: str
    trait: str
    name: str
    gender: str
    elder: str
    seed: Optional[int] = None
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


def predict_distress(world: World) -> dict:
    sim = world.copy()
    propagate(sim, narrate=False)
    hero = sim.get("hero")
    place = sim.get("place")
    return {
        "anxiety": hero.memes["anxiety"],
        "gloom": place.meters["gloom"],
    }


def open_tale(world: World, hero: Entity, elder: Entity, aid: Aid, setting: Setting, trait: Trait) -> None:
    world.say(
        f"Once, in a cottage at the edge of the greenwood, there lived a {trait.adjective} child named {hero.id}."
    )
    world.say(
        f"One morning {elder.title_word} placed {aid.phrase} in {hero.pronoun('possessive')} hands and sent "
        f"{hero.pronoun('object')} along {setting.path}."
    )
    world.say(
        f'"If you find sharp words on the road," said {elder.title_word}, "carry a soft heart with you."'
    )
    world.say(aid.carry)


def arrive_at_quarrel(world: World, hero: Entity, conflict: Conflict, setting: Setting) -> None:
    first = world.get("first")
    second = world.get("second")
    place = world.get("place")
    first.memes["anger"] = 1.0
    second.memes["anger"] = 1.0
    propagate(world, narrate=False)
    pred = predict_distress(world)
    world.facts["predicted_anxiety"] = pred["anxiety"]
    world.facts["predicted_gloom"] = pred["gloom"]
    world.say(
        f"At last {hero.id} came to {setting.label}, where {setting.image}. There {hero.pronoun()} found "
        f"{first.label} and {second.label} in the middle of {conflict.title}."
    )
    world.say(conflict.place_detail)
    world.say(conflict.quarrel_line)
    if pred["anxiety"] >= THRESHOLD:
        world.say(
            f"For a moment, anxiety rose in {hero.id}'s chest. {TRAITS[world.facts['trait_id']].anxious_style}."
        )


def remember(world: World, hero: Entity, aid: Aid) -> None:
    hero.meters["remembered"] = 1.0
    propagate(world, narrate=False)
    world.say(
        f"{hero.id} touched {aid.label}, and {aid.remember}. That helped {hero.pronoun('object')} stand still long enough to think."
    )


def step_forward(world: World, hero: Entity, remedy: Remedy, conflict: Conflict, margin: int) -> None:
    hero.memes["speaks"] = 1.0
    world.get("remedy").meters["offered"] = 1.0
    propagate(world, narrate=False)
    if margin <= 0:
        lead = f"{hero.id}'s voice shook at first, but {hero.pronoun()} did not run away."
    else:
        lead = f"{hero.id} took one small step forward, and {TRAITS[world.facts['trait_id']].brave_style}."
    world.say(lead)
    world.say(f"{hero.pronoun().capitalize()} {remedy.action}")
    world.say(remedy.speech)
    world.say(conflict.need_line)


def peace_result(world: World, conflict: Conflict) -> None:
    first = world.get("first")
    second = world.get("second")
    hero = world.get("hero")
    if not world.facts.get("peace_made"):
        raise StoryError("The peace offering failed to settle the quarrel.")
    world.say(
        f"The angry sound went out of {first.label} and {second.label}. They looked at the {conflict.object_label}, then at one another, and their hard faces softened."
    )
    if conflict.id == "bridge":
        world.say(
            f"Soon the bell rang once for the goat and once for the troll, and the bridge held both fairness and peace."
        )
    elif conflict.id == "acorns":
        world.say(
            "They counted the acorns slowly, crumb by crumb and nut by nut, until sharing seemed easier than shouting."
        )
    else:
        world.say(
            "The neat green stitches lay so close together that blame had no room left to sit between them."
        )
    world.say(
        f"When {hero.id} saw the quarrel loosen and fall away, the anxiety in {hero.pronoun('possessive')} chest melted into warm relief."
    )


def ending(world: World, hero: Entity, elder: Entity, setting: Setting, aid: Aid) -> None:
    world.say(
        f"By the time {hero.id} walked home from {setting.label}, even the path seemed changed. The leaves whispered kindly, and the evening light made room for a smile."
    )
    world.say(
        f"{elder.title_word.capitalize()} saw the quiet brightness in {hero.id}'s face and knew, before a word was spoken, that peace had been made."
    )
    world.say(
        f"After that day, whenever {hero.id} felt anxiety begin to stir, {hero.pronoun()} remembered {aid.label} and the quarrel that had ended with one brave, gentle choice."
    )


def tell(
    setting: Setting,
    conflict: Conflict,
    remedy: Remedy,
    aid: Aid,
    trait: Trait,
    hero_name: str = "Lina",
    hero_gender: str = "girl",
    elder_type: str = "grandmother",
) -> World:
    world = World(setting)
    hero = world.add(Entity(
        id="hero",
        kind="character",
        type=hero_gender,
        label=hero_name,
        role="hero",
        attrs={"name": hero_name},
        tags={"hero"},
    ))
    elder = world.add(Entity(
        id="elder",
        kind="character",
        type=elder_type,
        label=elder_type,
        role="elder",
        tags={"elder"},
    ))
    place = world.add(Entity(
        id="place",
        kind="thing",
        type="place",
        label=setting.label,
        role="place",
        tags={setting.id},
    ))
    first = world.add(Entity(
        id="first",
        kind="character",
        type="creature",
        label=conflict.creature1,
        role="disputant",
        tags={"quarrel"},
    ))
    second = world.add(Entity(
        id="second",
        kind="character",
        type="creature",
        label=conflict.creature2,
        role="disputant",
        tags={"quarrel"},
    ))
    remedy_ent = world.add(Entity(
        id="remedy",
        kind="thing",
        type="remedy",
        label=remedy.label,
        role="remedy",
        attrs={"fits": remedy_fits(conflict, remedy)},
        tags=set(remedy.tags),
    ))

    hero.memes["anxiety"] = 0.0
    hero.memes["courage"] = float(trait.heart)
    hero.memes["speaks"] = 0.0
    hero.memes["relief"] = 0.0
    hero.meters["remembered"] = 0.0
    first.memes["anger"] = 0.0
    second.memes["anger"] = 0.0
    first.memes["trust"] = 0.0
    second.memes["trust"] = 0.0
    place.meters["gloom"] = 0.0
    place.meters["sparkle"] = 0.0
    remedy_ent.meters["offered"] = 0.0

    world.facts.update(
        hero=hero,
        elder=elder,
        setting=setting,
        conflict=conflict,
        remedy=remedy,
        aid=aid,
        trait=trait,
        trait_id=trait.id,
        hero_name=hero_name,
        margin=(trait.heart + aid.comfort - conflict.severity),
    )

    open_tale(world, hero, elder, aid, setting, trait)
    world.para()
    arrive_at_quarrel(world, hero, conflict, setting)
    world.para()
    remember(world, hero, aid)
    step_forward(world, hero, remedy, conflict, world.facts["margin"])
    world.para()
    peace_result(world, conflict)
    ending(world, hero, elder, setting, aid)
    return world


KNOWLEDGE = {
    "bridge": [
        (
            "Why is taking turns important on a narrow bridge?",
            "Taking turns keeps everyone safe and fair. When only one person can fit, turns stop pushing and arguing."
        )
    ],
    "sharing": [
        (
            "What does sharing mean?",
            "Sharing means letting more than one person have a fair part. It can turn a fight into a calmer problem to solve together."
        )
    ],
    "needle": [
        (
            "What does a needle do?",
            "A needle carries thread through cloth so a tear can be sewn closed. It helps fix something instead of throwing it away."
        )
    ],
    "mending": [
        (
            "What does it mean to mend something?",
            "To mend something is to repair what was torn or broken. Mending can solve a problem when blaming does not help."
        )
    ],
    "bread": [
        (
            "Why can food help people stop fighting?",
            "Food cannot solve every problem, but enough for everyone can lower fear and greed. Then people can think more calmly."
        )
    ],
    "lantern": [
        (
            "What does a lantern do in a fairy tale?",
            "A lantern gives light in dark places. In stories, that light can also stand for hope and courage."
        )
    ],
    "comfort": [
        (
            "What can help when you feel anxiety?",
            "A calm breath, a comforting object, or a kind memory can help your body slow down. Then it is easier to think and choose what to do."
        )
    ],
    "fairness": [
        (
            "What is fairness?",
            "Fairness means people are treated in an even and honest way. Fair rules help stop quarrels before they grow."
        )
    ],
    "repair": [
        (
            "Why is fixing something often better than arguing about it?",
            "Fixing the problem changes the world for the better right away. Arguing alone usually keeps everyone stuck and upset."
        )
    ],
}
KNOWLEDGE_ORDER = ["bridge", "sharing", "bread", "needle", "mending", "lantern", "comfort", "fairness", "repair"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    conflict = f["conflict"]
    remedy = f["remedy"]
    aid = f["aid"]
    return [
        f'Write a short fairy tale for a 3-to-5-year-old that includes the word "anxiety" and a child ending a conflict with kindness.',
        f"Tell a gentle fairy tale where a {TRAITS[f['trait_id']].adjective} child named {f['hero_name']} carries {aid.phrase}, finds {conflict.title}, and uses {remedy.label} to make peace.",
        f"Write a woodland story with a quarrel, a worried child, and a happy ending that proves brave words can be small and still matter.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    hero = f["hero"]
    elder = f["elder"]
    conflict = f["conflict"]
    remedy = f["remedy"]
    aid = f["aid"]
    setting = f["setting"]
    name = f["hero_name"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {name}, a {f['trait'].adjective} child, and the quarrelling pair {conflict.pair_noun}. {elder.title_word.capitalize()} starts the tale by sending {name} down the woodland path."
        ),
        (
            f"What conflict did {name} find at {setting.label}?",
            f"{name} found {conflict.pair_noun} in the middle of {conflict.title}. They were fighting over {conflict.object_label}, so the place felt tense and gloomy."
        ),
        (
            f"How did {name} feel, and what helped?",
            f"{name} felt anxiety rising when the quarrel sounded loud and sharp. Touching {aid.label} helped {hero.pronoun('object')} remember a calmer feeling, so {hero.pronoun()} could think before speaking."
        ),
        (
            f"How did {name} solve the problem?",
            f"{name} used {remedy.label} because it matched what the quarrel needed. {hero.pronoun().capitalize()} spoke gently, offered help instead of blame, and that gave the two creatures a fairer way forward."
        ),
        (
            "How do we know the ending changed the world?",
            f"We know because the angry voices stopped and the place no longer felt gloomy. By the walk home, even the path seemed kinder, which shows the conflict had truly ended."
        ),
    ]
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags: set[str] = {"comfort"}
    tags |= set(world.facts["conflict"].tags)
    tags |= set(world.facts["remedy"].tags)
    tags |= set(world.facts["aid"].tags)
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
        meters = {k: v for k, v in ent.meters.items() if v}
        memes = {k: v for k, v in ent.memes.items() if v}
        bits = []
        if ent.role:
            bits.append(f"role={ent.role}")
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if ent.attrs:
            shown = {k: v for k, v in ent.attrs.items() if v}
            if shown:
                bits.append(f"attrs={shown}")
        lines.append(f"  {ent.id:8} ({ent.type:14}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        place="moon_bridge",
        conflict="bridge",
        remedy="turn_token",
        aid="glass_heart",
        trait="timid",
        name="Lina",
        gender="girl",
        elder="grandmother",
    ),
    StoryParams(
        place="bramble_clearing",
        conflict="acorns",
        remedy="shared_loaf",
        aid="pocket_song",
        trait="curious",
        name="Milo",
        gender="boy",
        elder="grandfather",
    ),
    StoryParams(
        place="mossy_hollow",
        conflict="tear",
        remedy="silver_needle",
        aid="grandmother_scarf",
        trait="gentle",
        name="Tessa",
        gender="girl",
        elder="grandmother",
    ),
    StoryParams(
        place="brook_meadow",
        conflict="bridge",
        remedy="turn_token",
        aid="star_lantern",
        trait="steadfast",
        name="Rowan",
        gender="boy",
        elder="grandmother",
    ),
    StoryParams(
        place="brook_meadow",
        conflict="acorns",
        remedy="shared_loaf",
        aid="grandmother_scarf",
        trait="gentle",
        name="Ada",
        gender="girl",
        elder="grandfather",
    ),
]


def explain_rejection(setting: Setting, conflict: Conflict, remedy: Remedy, aid: Aid, trait: Trait) -> str:
    if conflict.id not in setting.affords:
        allowed = ", ".join(sorted(setting.affords))
        return (
            f"(No story: {setting.label} does not host {conflict.title}. "
            f"That place supports: {allowed}.)"
        )
    if not remedy_fits(conflict, remedy):
        fits = ", ".join(sorted(conflict.fits))
        return (
            f"(No story: {remedy.label} does not solve {conflict.title}. "
            f"This quarrel needs one of: {fits}.)"
        )
    if not calm_enough(trait, aid, conflict):
        total = trait.heart + aid.comfort
        return (
            f"(No story: {aid.label} and a {trait.adjective} child are not steady enough "
            f"for {conflict.title} (strength {total} < severity {conflict.severity}). "
            f"Pick a stronger aid or a steadier trait.)"
        )
    return "(No story: this combination is not reasonable in this world.)"


ASP_RULES = r"""
usable_place(P, C) :- setting(P), conflict(C), affords(P, C).
fitting(R, C) :- remedy(R), conflict(C), solves(R, C).
steady_enough(T, A, C) :- trait(T), aid(A), conflict(C),
                          heart(T, H), comfort(A, K), severity(C, S), H + K >= S.
valid(P, C, R, A, T) :- usable_place(P, C), fitting(R, C), steady_enough(T, A, C).

outcome(resolved) :- chosen_place(P), chosen_conflict(C), chosen_remedy(R),
                     chosen_aid(A), chosen_trait(T), valid(P, C, R, A, T).
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for place_id, setting in SETTINGS.items():
        lines.append(asp.fact("setting", place_id))
        for conflict_id in sorted(setting.affords):
            lines.append(asp.fact("affords", place_id, conflict_id))
    for conflict_id, conflict in CONFLICTS.items():
        lines.append(asp.fact("conflict", conflict_id))
        lines.append(asp.fact("severity", conflict_id, conflict.severity))
    for remedy_id, remedy in REMEDIES.items():
        lines.append(asp.fact("remedy", remedy_id))
        for conflict_id in sorted(remedy.target_conflicts):
            lines.append(asp.fact("solves", remedy_id, conflict_id))
    for aid_id, aid in AIDS.items():
        lines.append(asp.fact("aid", aid_id))
        lines.append(asp.fact("comfort", aid_id, aid.comfort))
    for trait_id, trait in TRAITS.items():
        lines.append(asp.fact("trait", trait_id))
        lines.append(asp.fact("heart", trait_id, trait.heart))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("", "#show valid/5."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_outcome(params: StoryParams) -> str:
    import asp

    extra = "\n".join([
        asp.fact("chosen_place", params.place),
        asp.fact("chosen_conflict", params.conflict),
        asp.fact("chosen_remedy", params.remedy),
        asp.fact("chosen_aid", params.aid),
        asp.fact("chosen_trait", params.trait),
    ])
    model = asp.one_model(asp_program(extra, "#show outcome/1."))
    atoms = asp.atoms(model, "outcome")
    return atoms[0][0] if atoms else "invalid"


def outcome_of(params: StoryParams) -> str:
    if (
        params.place in SETTINGS
        and params.conflict in CONFLICTS
        and params.remedy in REMEDIES
        and params.aid in AIDS
        and params.trait in TRAITS
    ):
        setting = SETTINGS[params.place]
        conflict = CONFLICTS[params.conflict]
        remedy = REMEDIES[params.remedy]
        aid = AIDS[params.aid]
        trait = TRAITS[params.trait]
        if conflict.id in setting.affords and remedy_fits(conflict, remedy) and calm_enough(trait, aid, conflict):
            return "resolved"
    return "invalid"


def asp_verify() -> int:
    rc = 0
    py_set = set(valid_combos())
    asp_set = set(asp_valid_combos())
    if py_set == asp_set:
        print(f"OK: valid_combos matches ASP ({len(py_set)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos:")
        if py_set - asp_set:
            print("  only in python:", sorted(py_set - asp_set))
        if asp_set - py_set:
            print("  only in asp:", sorted(asp_set - py_set))

    cases = list(CURATED)
    for seed in range(40):
        try:
            params = resolve_params(build_parser().parse_args([]), random.Random(seed))
            params.seed = seed
            cases.append(params)
        except StoryError:
            rc = 1
            print(f"Random resolution failed at seed {seed}.")
            break

    mismatches = [p for p in cases if asp_outcome(p) != outcome_of(p)]
    if not mismatches:
        print(f"OK: outcome parity matches on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {len(mismatches)} outcome scenarios differ.")

    try:
        smoke = generate(CURATED[0])
        if not smoke.story.strip():
            raise StoryError("Smoke test generated an empty story.")
        print("OK: smoke test story generation succeeded.")
    except Exception as err:  # pragma: no cover - verification path
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Fairy-tale story world: a worried child, a quarrel in the wood, and a small act of peace."
    )
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--conflict", choices=CONFLICTS)
    ap.add_argument("--remedy", choices=REMEDIES)
    ap.add_argument("--aid", choices=AIDS)
    ap.add_argument("--trait", choices=TRAITS)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--name")
    ap.add_argument("--elder", choices=["grandmother", "grandfather", "fairy_godmother"])
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list valid combinations from ASP")
    ap.add_argument("--verify", action="store_true", help="check ASP parity and run smoke tests")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.place and args.conflict and args.remedy and args.aid and args.trait:
        setting = SETTINGS[args.place]
        conflict = CONFLICTS[args.conflict]
        remedy = REMEDIES[args.remedy]
        aid = AIDS[args.aid]
        trait = TRAITS[args.trait]
        if not (
            conflict.id in setting.affords
            and remedy_fits(conflict, remedy)
            and calm_enough(trait, aid, conflict)
        ):
            raise StoryError(explain_rejection(setting, conflict, remedy, aid, trait))

    combos = [
        combo for combo in valid_combos()
        if (args.place is None or combo[0] == args.place)
        and (args.conflict is None or combo[1] == args.conflict)
        and (args.remedy is None or combo[2] == args.remedy)
        and (args.aid is None or combo[3] == args.aid)
        and (args.trait is None or combo[4] == args.trait)
    ]
    if not combos:
        if args.place and args.conflict and args.remedy and args.aid and args.trait:
            raise StoryError(
                explain_rejection(
                    SETTINGS[args.place],
                    CONFLICTS[args.conflict],
                    REMEDIES[args.remedy],
                    AIDS[args.aid],
                    TRAITS[args.trait],
                )
            )
        raise StoryError("(No valid combination matches the given options.)")

    place_id, conflict_id, remedy_id, aid_id, trait_id = rng.choice(sorted(combos))
    gender = args.gender or rng.choice(["girl", "boy"])
    if args.name:
        name = args.name
    else:
        pool = GIRL_NAMES if gender == "girl" else BOY_NAMES
        name = rng.choice(pool)
    elder = args.elder or rng.choice(["grandmother", "grandfather", "fairy_godmother"])
    return StoryParams(
        place=place_id,
        conflict=conflict_id,
        remedy=remedy_id,
        aid=aid_id,
        trait=trait_id,
        name=name,
        gender=gender,
        elder=elder,
    )


def generate(params: StoryParams) -> StorySample:
    missing = [
        field for field, registry in [
            ("place", SETTINGS),
            ("conflict", CONFLICTS),
            ("remedy", REMEDIES),
            ("aid", AIDS),
            ("trait", TRAITS),
        ]
        if getattr(params, field) not in registry
    ]
    if missing:
        raise StoryError(f"Unknown parameter choice(s): {', '.join(missing)}")

    setting = SETTINGS[params.place]
    conflict = CONFLICTS[params.conflict]
    remedy = REMEDIES[params.remedy]
    aid = AIDS[params.aid]
    trait = TRAITS[params.trait]
    if not (conflict.id in setting.affords and remedy_fits(conflict, remedy) and calm_enough(trait, aid, conflict)):
        raise StoryError(explain_rejection(setting, conflict, remedy, aid, trait))

    world = tell(
        setting=setting,
        conflict=conflict,
        remedy=remedy,
        aid=aid,
        trait=trait,
        hero_name=params.name,
        hero_gender=params.gender,
        elder_type=params.elder,
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
        print(asp_program("", "#show valid/5.\n#show outcome/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} valid (place, conflict, remedy, aid, trait) combinations:\n")
        for place, conflict, remedy, aid, trait in combos:
            print(f"  {place:16} {conflict:8} {remedy:14} {aid:18} {trait}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        samples: list[StorySample] = []
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
            header = f"### {p.name}: {p.conflict} at {p.place} ({p.remedy}, {p.aid}, {p.trait})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()

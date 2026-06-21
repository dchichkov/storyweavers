#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/heroic_bar_pretzel_lesson_learned_misunderstanding_fairy.py
=======================================================================================

A standalone storyworld for a tiny fairy-tale bakery domain:

A small fairy sees a missing pretzel, hears a clue, and jumps into a heroic
misunderstanding. The pretzel was never stolen at all; a baker moved it to a
bar in the shop for a sensible reason. The turn comes when the hero asks before
blaming. The lesson is gentle: being heroic is good, but asking kindly is wiser
than guessing.

Run it
------
    python storyworlds/worlds/gpt-5.4/heroic_bar_pretzel_lesson_learned_misunderstanding_fairy.py
    python storyworlds/worlds/gpt-5.4/heroic_bar_pretzel_lesson_learned_misunderstanding_fairy.py --asp
    python storyworlds/worlds/gpt-5.4/heroic_bar_pretzel_lesson_learned_misunderstanding_fairy.py --verify
    python storyworlds/worlds/gpt-5.4/heroic_bar_pretzel_lesson_learned_misunderstanding_fairy.py -n 5 --seed 7 --qa
"""

from __future__ import annotations

import argparse
import contextlib
import copy
import io
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
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "fairy_girl", "woman", "fairy_baker"}
        male = {"boy", "fairy_boy", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return self.label or self.type.replace("_", " ")
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
class PretzelKind:
    id: str
    label: str
    phrase: str
    shine: str
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
class Clue:
    id: str
    text: str
    sound: str
    points_to: str
    reason: str
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
class Suspect:
    id: str
    label: str
    phrase: str
    perch: str
    motion: str
    innocent_line: str
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
class Method:
    id: str
    label: str
    action: str
    reaches: set[str] = field(default_factory=set)
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
class BarPlace:
    id: str
    label: str
    phrase: str
    reason: str
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


def _r_missing_hurts(world: World) -> list[str]:
    out: list[str] = []
    pretzel = world.get("pretzel")
    friend = world.get("friend")
    if pretzel.attrs.get("where") == "missing" and friend.memes["hope"] >= THRESHOLD:
        sig = ("missing_hurts",)
        if sig not in world.fired:
            world.fired.add(sig)
            friend.memes["sadness"] += 1
            out.append("__friend_sad__")
    return out


def _r_accuse_worries(world: World) -> list[str]:
    out: list[str] = []
    suspect = world.get("suspect")
    if suspect.memes["blamed"] >= THRESHOLD:
        sig = ("accuse_worries",)
        if sig not in world.fired:
            world.fired.add(sig)
            suspect.memes["worry"] += 1
            out.append("__suspect_worried__")
    return out


def _r_reveal_relief(world: World) -> list[str]:
    out: list[str] = []
    pretzel = world.get("pretzel")
    hero = world.get("hero")
    friend = world.get("friend")
    suspect = world.get("suspect")
    if pretzel.attrs.get("where") != "missing":
        sig = ("reveal_relief", pretzel.attrs.get("where"))
        if sig not in world.fired:
            world.fired.add(sig)
            hero.memes["relief"] += 1
            friend.memes["relief"] += 1
            friend.memes["sadness"] = 0.0
            suspect.memes["worry"] = 0.0
            suspect.memes["trust"] += 1
            out.append("__relief__")
    return out


CAUSAL_RULES = [
    Rule(name="missing_hurts", tag="emotional", apply=_r_missing_hurts),
    Rule(name="accuse_worries", tag="social", apply=_r_accuse_worries),
    Rule(name="reveal_relief", tag="emotional", apply=_r_reveal_relief),
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
        for s in produced:
            world.say(s)
    return produced


PRETZELS = {
    "star_salt": PretzelKind(
        id="star_salt",
        label="star-salt pretzel",
        phrase="a star-salt pretzel",
        shine="salt crystals twinkled on its brown twists like tiny stars",
        tags={"pretzel"},
    ),
    "honey_twist": PretzelKind(
        id="honey_twist",
        label="honey pretzel",
        phrase="a honey pretzel",
        shine="a thin stripe of honey made it shine like amber",
        tags={"pretzel", "honey"},
    ),
    "sesame_loop": PretzelKind(
        id="sesame_loop",
        label="sesame pretzel",
        phrase="a sesame pretzel",
        shine="pale sesame seeds dotted its loops like little moon pebbles",
        tags={"pretzel", "sesame"},
    ),
}

CLUES = {
    "flutter": Clue(
        id="flutter",
        text="a quick flutter by the window boxes",
        sound="wings whisked the air by the window",
        points_to="sparrow",
        reason="a flutter near the window makes a bird seem like the most likely thief",
        tags={"misunderstanding", "sparrow"},
    ),
    "rustle": Clue(
        id="rustle",
        text="a rustle in the old oak leaves",
        sound="the oak leaves rustled over the lane",
        points_to="squirrel",
        reason="a rustle in the tree makes a squirrel seem guilty",
        tags={"misunderstanding", "squirrel"},
    ),
    "squeak": Clue(
        id="squeak",
        text="a tiny squeak beside the flour sacks",
        sound="something squeaked near the flour sacks",
        points_to="mouse",
        reason="a squeak by the flour makes a mouse sound suspicious",
        tags={"misunderstanding", "mouse"},
    ),
}

SUSPECTS = {
    "sparrow": Suspect(
        id="sparrow",
        label="sparrow",
        phrase="a little brown sparrow",
        perch="window_box",
        motion="hopped among the red window flowers",
        innocent_line="I only came for a crumb of song, not for a snack.",
        tags={"sparrow", "bird"},
    ),
    "squirrel": Suspect(
        id="squirrel",
        label="squirrel",
        phrase="a striped squirrel",
        perch="oak_branch",
        motion="flicked its tail on a crooked oak branch",
        innocent_line="I gathered acorns this morning. I never touched your bakery treat.",
        tags={"squirrel", "tree"},
    ),
    "mouse": Suspect(
        id="mouse",
        label="mouse",
        phrase="a flour-dusted mouse",
        perch="flour_sack",
        motion="peeked from behind the flour sacks with twitching whiskers",
        innocent_line="I came for spilled grain, not for anyone's pretzel.",
        tags={"mouse", "bakery"},
    ),
}

METHODS = {
    "stool": Method(
        id="stool",
        label="a tiptoe stool",
        action="dragged over a tiptoe stool and climbed up with both hands spread like wings",
        reaches={"window_box", "flour_sack"},
        tags={"stool"},
    ),
    "ribbon_lasso": Method(
        id="ribbon_lasso",
        label="a ribbon lasso",
        action="whirled a silver ribbon like a lasso and cast it upward",
        reaches={"window_box", "oak_branch"},
        tags={"ribbon"},
    ),
    "broom_pole": Method(
        id="broom_pole",
        label="a broom pole",
        action="lifted a broom pole like a lance and stretched it as high as she could",
        reaches={"oak_branch", "flour_sack"},
        tags={"broom"},
    ),
}

BAR_PLACES = {
    "cooling_bar": BarPlace(
        id="cooling_bar",
        label="cooling bar",
        phrase="the warm cooling bar above the oven",
        reason="it needed a little time to cool before anyone nibbled it",
        ending="They sat by the oven glow and watched the pretzel rest on the cooling bar until it was ready.",
        tags={"bar", "baker"},
    ),
    "window_bar": BarPlace(
        id="window_bar",
        label="window bar",
        phrase="the brass window bar in the front display",
        reason="the baker had set it there so the morning sun could make it gleam for a festival customer",
        ending="In the front window, the pretzel shone on the brass bar like a small golden moon.",
        tags={"bar", "window"},
    ),
    "ribbon_bar": BarPlace(
        id="ribbon_bar",
        label="ribbon bar",
        phrase="the hanging ribbon bar where wrapped orders waited",
        reason="the baker had tied a ribbon around it because it was meant as a thank-you gift",
        ending="The pretzel swung from the ribbon bar with a neat bow, looking much too grand to be lost at all.",
        tags={"bar", "gift"},
    ),
}

HERO_NAMES = ["Lina", "Poppy", "Nia", "Mira", "Tansy", "Wren"]
FRIEND_NAMES = ["Pip", "Bram", "Fenn", "Milo", "Tavi", "Sela"]


def clue_matches_suspect(clue: Clue, suspect: Suspect) -> bool:
    return clue.points_to == suspect.id


def method_reaches(method: Method, suspect: Suspect) -> bool:
    return suspect.perch in method.reaches


def valid_combos() -> list[tuple[str, str, str, str]]:
    combos: list[tuple[str, str, str, str]] = []
    for clue_id, clue in CLUES.items():
        for suspect_id, suspect in SUSPECTS.items():
            if not clue_matches_suspect(clue, suspect):
                continue
            for method_id, method in METHODS.items():
                if not method_reaches(method, suspect):
                    continue
                for place_id in BAR_PLACES:
                    combos.append((clue_id, suspect_id, method_id, place_id))
    return combos


def predict_misunderstanding(world: World, clue: Clue, suspect: Suspect) -> dict:
    sim = world.copy()
    hero = sim.get("hero")
    found = clue_matches_suspect(clue, suspect)
    if found:
        hero.memes["certainty"] += 1
    return {"blames": found, "reason": clue.reason}


def introduce(world: World, hero: Entity, friend: Entity, baker: Entity, pretzel_cfg: PretzelKind) -> None:
    friend.memes["hope"] += 1
    world.say(
        f"Once, in a bakery at the edge of a bluebell wood, lived a small fairy named {hero.id}. "
        f"{hero.id} liked brave stories so much that {hero.pronoun()} always wanted to be the most heroic heart in the room."
    )
    world.say(
        f"One bright morning, the baker set out {pretzel_cfg.phrase} for {friend.id}. "
        f"{pretzel_cfg.shine.capitalize()}, and the whole shop smelled warm and sweet."
    )
    world.say(
        f'"I will eat it after I wash the berry jam from my fingers," said {friend.id}, smiling as {baker.label_word} turned back to the oven.'
    )


def missing(world: World, friend: Entity, clue: Clue) -> None:
    pretzel = world.get("pretzel")
    pretzel.attrs["where"] = "missing"
    propagate(world, narrate=False)
    world.say(
        f"But when {friend.id} came back, the plate was empty. {clue.sound.capitalize()}, and suddenly the bakery felt full of questions."
    )
    if friend.memes["sadness"] >= THRESHOLD:
        world.say(
            f'{friend.id} clasped both hands. "My pretzel is gone," {friend.pronoun()} whispered, looking close to tears.'
        )


def vow(world: World, hero: Entity, clue: Clue, suspect: Suspect) -> None:
    hero.memes["heroic"] += 1
    pred = predict_misunderstanding(world, clue, suspect)
    world.facts["prediction_reason"] = pred["reason"]
    world.say(
        f"{hero.id} noticed {clue.text} and lifted {hero.pronoun('possessive')} chin. "
        f'"Do not fear," {hero.pronoun()} said. "I will make a heroic rescue."'
    )
    world.say(
        f"To {hero.id}, {clue.text} seemed like plain proof. {pred['reason'][0].upper()}{pred['reason'][1:]}."
    )


def hunt(world: World, hero: Entity, suspect: Suspect, method: Method) -> None:
    hero.meters["distance"] += 1
    hero.memes["certainty"] += 1
    world.say(
        f"{hero.pronoun().capitalize()} hurried outside, where {suspect.phrase} {suspect.motion}. "
        f"{hero.id} {method.action}."
    )


def accuse(world: World, hero: Entity, suspect: Entity, suspect_cfg: Suspect, pretzel_cfg: PretzelKind) -> None:
    suspect.memes["blamed"] += 1
    propagate(world, narrate=False)
    world.say(
        f'"Please give back the {pretzel_cfg.label}," called {hero.id}. '
        f'"My friend is waiting, and I have come to save it."'
    )
    if suspect.memes["worry"] >= THRESHOLD:
        world.say(
            f"The {suspect_cfg.label} blinked in surprise. \"{suspect_cfg.innocent_line}\""
        )


def empty_search(world: World, hero: Entity, suspect_cfg: Suspect) -> None:
    hero.memes["doubt"] += 1
    world.say(
        f"But there was no pretzel in the {suspect_cfg.label}'s place at all. "
        f"Only leaves, flour dust, and a puzzled little face looked back at {hero.id}."
    )


def ask(world: World, hero: Entity, baker: Entity) -> None:
    hero.memes["humility"] += 1
    world.say(
        f"Just then the baker stepped out, brushing flour from {baker.pronoun('possessive')} apron. "
        f'"Little one," {baker.pronoun()} said, "before you chase another shadow, why not ask what happened?"'
    )


def reveal(world: World, baker: Entity, place: BarPlace, pretzel_cfg: PretzelKind) -> None:
    pretzel = world.get("pretzel")
    pretzel.attrs["where"] = place.id
    propagate(world, narrate=False)
    world.say(
        f'The baker pointed inside. "Your friend\'s {pretzel_cfg.label} is on {place.phrase}," '
        f"{baker.pronoun()} explained. \"{place.reason[0].upper()}{place.reason[1:]}\""
    )


def apology(world: World, hero: Entity, friend: Entity, suspect_cfg: Suspect) -> None:
    hero.memes["embarrassment"] += 1
    world.say(
        f"{hero.id}'s cheeks turned as pink as foxglove bells. "
        f"{hero.pronoun().capitalize()} bowed to {friend.id} and to the {suspect_cfg.label}."
    )
    world.say(
        f'"I wanted to be heroic," {hero.pronoun()} admitted, "but I guessed before I asked. I am sorry."'
    )


def lesson(world: World, baker: Entity, hero: Entity, friend: Entity) -> None:
    hero.memes["lesson"] += 1
    hero.memes["care"] += 1
    friend.memes["trust"] += 1
    world.say(
        f'The baker smiled kindly. "A brave heart is precious," {baker.pronoun()} said, '
        f'"but a wise heart asks questions before it blames."'
    )
    world.say(
        f"{friend.id} nodded and squeezed {hero.id}'s hand. "
        f'"Next time," {friend.pronoun()} said, "we can be brave and careful together."'
    )


def ending(world: World, hero: Entity, friend: Entity, place: BarPlace, pretzel_cfg: PretzelKind) -> None:
    hero.memes["joy"] += 1
    friend.memes["joy"] += 1
    world.say(place.ending)
    world.say(
        f"When the {pretzel_cfg.label} was finally ready, {friend.id} broke it in two and shared half with {hero.id}. "
        f"From then on, whenever a mystery fluttered through the bakery, {hero.id} remembered that the kindest magic begins with asking."
    )


def tell(
    pretzel_cfg: PretzelKind,
    clue: Clue,
    suspect_cfg: Suspect,
    method: Method,
    place: BarPlace,
    hero_name: str = "Lina",
    hero_type: str = "fairy_girl",
    friend_name: str = "Pip",
    friend_type: str = "fairy_boy",
    baker_type: str = "fairy_baker",
) -> World:
    world = World()
    hero = world.add(Entity(id=hero_name, kind="character", type=hero_type, role="hero", label=hero_name))
    friend = world.add(Entity(id=friend_name, kind="character", type=friend_type, role="friend", label=friend_name))
    baker = world.add(Entity(id="Baker", kind="character", type=baker_type, role="baker", label="the baker"))
    suspect = world.add(Entity(id="suspect", kind="character", type="animal", role="suspect", label=suspect_cfg.label))
    pretzel = world.add(Entity(id="pretzel", kind="thing", type="pretzel", label=pretzel_cfg.label, attrs={"where": "plate"}))

    hero.memes["care"] = 1.0
    hero.memes["heroic"] = 0.0
    hero.memes["certainty"] = 0.0
    hero.memes["doubt"] = 0.0
    hero.memes["lesson"] = 0.0
    friend.memes["hope"] = 1.0
    friend.memes["sadness"] = 0.0
    friend.memes["relief"] = 0.0
    suspect.memes["blamed"] = 0.0
    suspect.memes["worry"] = 0.0
    suspect.memes["trust"] = 0.0

    world.facts.update(
        pretzel_cfg=pretzel_cfg,
        clue=clue,
        suspect_cfg=suspect_cfg,
        method=method,
        place=place,
        hero=hero,
        friend=friend,
        baker=baker,
        suspect=suspect,
    )

    introduce(world, hero, friend, baker, pretzel_cfg)
    world.para()
    missing(world, friend, clue)
    vow(world, hero, clue, suspect_cfg)
    hunt(world, hero, suspect_cfg, method)
    accuse(world, hero, suspect, suspect_cfg, pretzel_cfg)
    empty_search(world, hero, suspect_cfg)
    world.para()
    ask(world, hero, baker)
    reveal(world, baker, place, pretzel_cfg)
    apology(world, hero, friend, suspect_cfg)
    lesson(world, baker, hero, friend)
    world.para()
    ending(world, hero, friend, place, pretzel_cfg)

    world.facts.update(
        misunderstanding=True,
        lesson_learned=hero.memes["lesson"] >= THRESHOLD,
        found_on_bar=world.get("pretzel").attrs.get("where") in BAR_PLACES,
        accused=suspect.memes["blamed"] >= THRESHOLD,
        method_worked=False,
    )
    return world


KNOWLEDGE = {
    "pretzel": [
        (
            "What is a pretzel?",
            "A pretzel is a baked bread snack twisted into loops. Some pretzels are soft and warm, and some have salt or seeds on top.",
        )
    ],
    "bar": [
        (
            "What can the word bar mean in a bakery?",
            "In a bakery, a bar can be a rail or rod where things rest or hang. It does not always mean a candy bar.",
        )
    ],
    "heroic": [
        (
            "What does heroic mean?",
            "Heroic means brave and eager to help. But being truly heroic also means stopping to understand what is really happening.",
        )
    ],
    "misunderstanding": [
        (
            "What is a misunderstanding?",
            "A misunderstanding happens when someone gets the wrong idea about what happened or what someone meant. Asking a calm question can help clear it up.",
        )
    ],
    "sparrow": [
        (
            "What is a sparrow?",
            "A sparrow is a small bird with quick wings and a tiny beak. It often hops near houses and gardens looking for seeds.",
        )
    ],
    "squirrel": [
        (
            "What does a squirrel do?",
            "A squirrel climbs trees, flicks its tail, and gathers nuts or seeds. It is quick and curious, but that does not mean it took someone's snack.",
        )
    ],
    "mouse": [
        (
            "What is a mouse?",
            "A mouse is a very small animal with whiskers and a soft nose. It often looks for crumbs or grain in quiet places.",
        )
    ],
    "ask_first": [
        (
            "Why is it good to ask before blaming someone?",
            "Asking first helps you learn what is true. It can keep an innocent friend from feeling scared or hurt.",
        )
    ],
    "baker": [
        (
            "What does a baker do?",
            "A baker mixes dough and bakes bread or treats in an oven. A baker may also move food so it can cool, shine, or wait for a customer.",
        )
    ],
}
KNOWLEDGE_ORDER = ["pretzel", "bar", "heroic", "misunderstanding", "sparrow", "squirrel", "mouse", "ask_first", "baker"]


@dataclass
class StoryParams:
    pretzel: str
    clue: str
    suspect: str
    method: str
    place: str
    hero_name: str
    hero_type: str
    friend_name: str
    friend_type: str
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


CURATED = [
    StoryParams(
        pretzel="star_salt",
        clue="flutter",
        suspect="sparrow",
        method="stool",
        place="cooling_bar",
        hero_name="Lina",
        hero_type="fairy_girl",
        friend_name="Pip",
        friend_type="fairy_boy",
    ),
    StoryParams(
        pretzel="honey_twist",
        clue="rustle",
        suspect="squirrel",
        method="ribbon_lasso",
        place="window_bar",
        hero_name="Poppy",
        hero_type="fairy_girl",
        friend_name="Bram",
        friend_type="fairy_boy",
    ),
    StoryParams(
        pretzel="sesame_loop",
        clue="squeak",
        suspect="mouse",
        method="broom_pole",
        place="ribbon_bar",
        hero_name="Mira",
        hero_type="fairy_girl",
        friend_name="Tavi",
        friend_type="fairy_boy",
    ),
    StoryParams(
        pretzel="star_salt",
        clue="rustle",
        suspect="squirrel",
        method="broom_pole",
        place="cooling_bar",
        hero_name="Nia",
        hero_type="fairy_girl",
        friend_name="Sela",
        friend_type="fairy_girl",
    ),
    StoryParams(
        pretzel="honey_twist",
        clue="flutter",
        suspect="sparrow",
        method="ribbon_lasso",
        place="ribbon_bar",
        hero_name="Tansy",
        hero_type="fairy_girl",
        friend_name="Milo",
        friend_type="fairy_boy",
    ),
]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    friend = f["friend"]
    pretzel_cfg = f["pretzel_cfg"]
    suspect_cfg = f["suspect_cfg"]
    clue = f["clue"]
    place = f["place"]
    return [
        f'Write a fairy-tale story for a 3-to-5-year-old that includes the words "heroic", "bar", and "pretzel".',
        f"Tell a gentle misunderstanding story where {hero.id} thinks a {suspect_cfg.label} took {friend.id}'s {pretzel_cfg.label}, but the baker reveals it was really on {place.phrase}.",
        f"Write a small fairy bakery tale with a missing treat, {clue.text}, a mistaken guess, and a lesson about asking before blaming.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    hero = f["hero"]
    friend = f["friend"]
    baker = f["baker"]
    suspect_cfg = f["suspect_cfg"]
    clue = f["clue"]
    method = f["method"]
    place = f["place"]
    pretzel_cfg = f["pretzel_cfg"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {hero.id}, a little fairy who wanted to act heroic, and {friend.id}, whose {pretzel_cfg.label} seemed to be missing. The baker and a surprised {suspect_cfg.label} are part of the misunderstanding too.",
        ),
        (
            f"Why did {hero.id} think the {suspect_cfg.label} had the pretzel?",
            f"{hero.id} noticed {clue.text} and treated it like proof. That clue matched the {suspect_cfg.label}, so {hero.pronoun()} guessed too quickly instead of asking what had really happened.",
        ),
        (
            f"What did {hero.id} do to try to help?",
            f"{hero.pronoun().capitalize()} hurried after the {suspect_cfg.label} and used {method.label} while trying to rescue the pretzel. The attempt was brave, but it was built on the wrong idea.",
        ),
        (
            "Where was the pretzel really?",
            f"It was on {place.phrase}. The baker had put it there because {place.reason}.",
        ),
        (
            "What lesson did the fairy learn?",
            f"{hero.id} learned that being heroic is not only about rushing in. It also means asking kind questions before blaming someone innocent.",
        ),
    ]
    if world.facts.get("accused"):
        qa.append(
            (
                f"How did the misunderstanding affect the {suspect_cfg.label}?",
                f"The {suspect_cfg.label} felt startled because {hero.id} accused it without knowing the truth. Asking first would have protected an innocent creature from worry.",
            )
        )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags = {"pretzel", "bar", "heroic", "misunderstanding", "ask_first", "baker"}
    suspect_id = f["suspect_cfg"].id
    if suspect_id in KNOWLEDGE:
        tags.add(suspect_id)
    out: list[tuple[str, str]] = []
    for tag in KNOWLEDGE_ORDER:
        if tag in tags and tag in KNOWLEDGE:
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
        attrs = {k: v for k, v in ent.attrs.items() if v}
        parts = []
        if ent.role:
            parts.append(f"role={ent.role}")
        if meters:
            parts.append(f"meters={dict(meters)}")
        if memes:
            parts.append(f"memes={dict(memes)}")
        if attrs:
            parts.append(f"attrs={attrs}")
        lines.append(f"  {ent.id:8} ({ent.type:12}) {' '.join(parts)}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    return "\n".join(lines)


def explain_combo(clue: Clue, suspect: Suspect, method: Method) -> str:
    if not clue_matches_suspect(clue, suspect):
        return (
            f"(No story: {clue.text} does not sensibly point to a {suspect.label}. "
            f"The misunderstanding must come from a clue that really suggests the suspect.)"
        )
    if not method_reaches(method, suspect):
        return (
            f"(No story: {method.label} cannot reach the {suspect.label}'s place. "
            f"The heroic attempt must at least be physically plausible.)"
        )
    return "(No story: this combination is not supported.)"


ASP_RULES = r"""
points_to(flutter,sparrow).
points_to(rustle,squirrel).
points_to(squeak,mouse).

perch(sparrow,window_box).
perch(squirrel,oak_branch).
perch(mouse,flour_sack).

misleads(C,S) :- clue(C), suspect(S), points_to(C,S).
reachable(M,S) :- method(M), suspect(S), perch(S,P), reaches(M,P).

valid(C,S,M,B) :- clue(C), suspect(S), method(M), bar_place(B),
                  misleads(C,S), reachable(M,S).

#show valid/4.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for clue_id in CLUES:
        lines.append(asp.fact("clue", clue_id))
    for suspect_id in SUSPECTS:
        lines.append(asp.fact("suspect", suspect_id))
    for method_id, method in METHODS.items():
        lines.append(asp.fact("method", method_id))
        for reach in sorted(method.reaches):
            lines.append(asp.fact("reaches", method_id, reach))
    for place_id in BAR_PLACES:
        lines.append(asp.fact("bar_place", place_id))
    return "\n".join(lines)


def asp_program(extra: str = "") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program())
    return sorted(set(asp.atoms(model, "valid")))


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Fairy-tale storyworld: a missing pretzel, a heroic misunderstanding, and a lesson about asking first."
    )
    ap.add_argument("--pretzel", choices=PRETZELS)
    ap.add_argument("--clue", choices=CLUES)
    ap.add_argument("--suspect", choices=SUSPECTS)
    ap.add_argument("--method", choices=METHODS)
    ap.add_argument("--place", choices=BAR_PLACES)
    ap.add_argument("--hero-name")
    ap.add_argument("--friend-name")
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list valid combinations from clingo")
    ap.add_argument("--verify", action="store_true", help="check Python/ASP parity and run smoke tests")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.clue and args.suspect:
        clue = CLUES[args.clue]
        suspect = SUSPECTS[args.suspect]
        if not clue_matches_suspect(clue, suspect):
            raise StoryError(explain_combo(clue, suspect, METHODS[next(iter(METHODS))]))
    if args.suspect and args.method:
        suspect = SUSPECTS[args.suspect]
        method = METHODS[args.method]
        if not method_reaches(method, suspect):
            clue = CLUES[args.clue] if args.clue else next(iter(CLUES.values()))
            raise StoryError(explain_combo(clue, suspect, method))

    combos = [
        combo
        for combo in valid_combos()
        if (args.clue is None or combo[0] == args.clue)
        and (args.suspect is None or combo[1] == args.suspect)
        and (args.method is None or combo[2] == args.method)
        and (args.place is None or combo[3] == args.place)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    clue_id, suspect_id, method_id, place_id = rng.choice(sorted(combos))
    pretzel_id = args.pretzel or rng.choice(sorted(PRETZELS.keys()))
    hero_name = args.hero_name or rng.choice(HERO_NAMES)
    friend_name = args.friend_name or rng.choice([n for n in FRIEND_NAMES if n != hero_name])
    friend_type = rng.choice(["fairy_boy", "fairy_girl"])
    return StoryParams(
        pretzel=pretzel_id,
        clue=clue_id,
        suspect=suspect_id,
        method=method_id,
        place=place_id,
        hero_name=hero_name,
        hero_type="fairy_girl",
        friend_name=friend_name,
        friend_type=friend_type,
    )


def generate(params: StoryParams) -> StorySample:
    if params.pretzel not in PRETZELS:
        raise StoryError(f"(Unknown pretzel: {params.pretzel})")
    if params.clue not in CLUES:
        raise StoryError(f"(Unknown clue: {params.clue})")
    if params.suspect not in SUSPECTS:
        raise StoryError(f"(Unknown suspect: {params.suspect})")
    if params.method not in METHODS:
        raise StoryError(f"(Unknown method: {params.method})")
    if params.place not in BAR_PLACES:
        raise StoryError(f"(Unknown place: {params.place})")

    clue = CLUES[params.clue]
    suspect = SUSPECTS[params.suspect]
    method = METHODS[params.method]
    if not clue_matches_suspect(clue, suspect) or not method_reaches(method, suspect):
        raise StoryError(explain_combo(clue, suspect, method))

    world = tell(
        pretzel_cfg=PRETZELS[params.pretzel],
        clue=clue,
        suspect_cfg=suspect,
        method=method,
        place=BAR_PLACES[params.place],
        hero_name=params.hero_name,
        hero_type=params.hero_type,
        friend_name=params.friend_name,
        friend_type=params.friend_type,
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


def asp_verify() -> int:
    rc = 0
    py_set = set(valid_combos())
    asp_set = set(asp_valid_combos())
    if py_set == asp_set:
        print(f"OK: ASP valid combos match Python ({len(py_set)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos:")
        if asp_set - py_set:
            print("  only in clingo:", sorted(asp_set - py_set))
        if py_set - asp_set:
            print("  only in python:", sorted(py_set - asp_set))

    try:
        sample = generate(CURATED[0])
        with contextlib.redirect_stdout(io.StringIO()):
            emit(sample, trace=True, qa=True, header="### smoke")
        if not sample.story or "pretzel" not in sample.story or "heroic" not in sample.story or "bar" not in sample.story:
            raise StoryError("(Smoke test failed: required story words missing.)")
        print("OK: smoke test generation/emit passed.")
    except Exception as err:
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    try:
        args = build_parser().parse_args([])
        params = resolve_params(args, random.Random(123))
        sample = generate(params)
        with contextlib.redirect_stdout(io.StringIO()):
            emit(sample, trace=False, qa=False)
        print("OK: default resolve/generate path passed.")
    except Exception as err:
        rc = 1
        print(f"DEFAULT PATH FAILED: {err}")
    return rc


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program())
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} valid (clue, suspect, method, place) combos:\n")
        for clue_id, suspect_id, method_id, place_id in combos:
            print(f"  {clue_id:8} {suspect_id:8} {method_id:13} {place_id}")
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
            header = f"### {p.hero_name}: {p.clue} -> {p.suspect} with {p.method} ({p.place})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()

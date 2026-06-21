#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/relevant_twine_curiosity_foreshadowing_fairy_tale.py
================================================================================

A standalone story world for a small fairy-tale domain shaped around curiosity,
foreshadowing, and the word "twine".

Premise
-------
In a quiet cottage country, a curious child hears of a hidden fairy place where
something lovely is waiting: a singing spring, a moonlit pear tree, or a little
door in a hill. Before the child goes, the world offers a foreshadowing sign:
turning leaves, circling crows, or a stream that seems to whisper about paths
that do not stay straight.

The child wants to follow curiosity anyway. A wise elder gives one practical
way to stay safe: mark the path with something suitable for that place. In some
places, blue twine tied to branches is the relevant tool; in others, chalk on
stone or pebbles on a sandy path make sense. Unreasonable pairings are refused.

If the child uses a fitting marker, curiosity becomes discovery and the child
comes home wiser. If the child insists on a poor marker or lingers too long, the
world can produce a sadder, cautionary ending in which the child is found late
and learns that wonder needs a way home.

Run it
------
    python storyworlds/worlds/gpt-5.4/relevant_twine_curiosity_foreshadowing_fairy_tale.py
    python storyworlds/worlds/gpt-5.4/relevant_twine_curiosity_foreshadowing_fairy_tale.py --all
    python storyworlds/worlds/gpt-5.4/relevant_twine_curiosity_foreshadowing_fairy_tale.py --place briar_maze --marker twine
    python storyworlds/worlds/gpt-5.4/relevant_twine_curiosity_foreshadowing_fairy_tale.py --place crystal_caves --marker twine
    python storyworlds/worlds/gpt-5.4/relevant_twine_curiosity_foreshadowing_fairy_tale.py --qa --json
    python storyworlds/worlds/gpt-5.4/relevant_twine_curiosity_foreshadowing_fairy_tale.py --verify
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
        female = {"girl", "mother", "queen", "woman"}
        male = {"boy", "father", "king", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return {"mother": "mother", "father": "father", "grandmother": "grandmother"}.get(
            self.type, self.type
        )
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
    label: str
    the: str
    approach: str
    inside: str
    treasure: str
    treasure_detail: str
    omen: str
    warning: str
    route_kind: str
    surface: str
    risk: int
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
class Marker:
    id: str
    label: str
    phrase: str
    action: str
    works_on: set[str] = field(default_factory=set)
    trace_word: str = ""
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
class Treasure:
    id: str
    label: str
    phrase: str
    gift_text: str
    ending_image: str
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
class Omen:
    id: str
    sign: str
    whisper: str
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


def _r_turning_paths(world: World) -> list[str]:
    out: list[str] = []
    child = world.get("child")
    place = world.facts["place_cfg"]
    marker = world.facts["marker_cfg"]
    if child.meters["entered"] < THRESHOLD:
        return out
    sig = ("turning_paths", place.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    world.get("place").meters["confusion"] += float(place.risk)
    child.memes["wonder"] += 1
    child.memes["fear"] += 1
    if marker_ok(marker, place):
        child.meters["breadcrumbs"] += 1
    out.append("__turning__")
    return out


def _r_lost(world: World) -> list[str]:
    out: list[str] = []
    child = world.get("child")
    place_ent = world.get("place")
    if child.meters["entered"] < THRESHOLD:
        return out
    if child.meters["breadcrumbs"] >= THRESHOLD:
        return out
    if place_ent.meters["confusion"] < THRESHOLD:
        return out
    sig = ("lost",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    child.meters["lost"] += 1
    child.memes["fear"] += 1
    out.append("__lost__")
    return out


def _r_return(world: World) -> list[str]:
    out: list[str] = []
    child = world.get("child")
    if child.meters["breadcrumbs"] < THRESHOLD:
        return out
    sig = ("return",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    child.meters["found_way"] += 1
    child.memes["relief"] += 1
    out.append("__return__")
    return out


CAUSAL_RULES = [
    Rule(name="turning_paths", tag="physical", apply=_r_turning_paths),
    Rule(name="lost", tag="physical", apply=_r_lost),
    Rule(name="return", tag="physical", apply=_r_return),
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


def marker_ok(marker: Marker, place: Place) -> bool:
    return place.surface in marker.works_on


def valid_combos() -> list[tuple[str, str, str, str]]:
    combos: list[tuple[str, str, str, str]] = []
    for place_id, place in PLACES.items():
        for marker_id, marker in MARKERS.items():
            if not marker_ok(marker, place):
                continue
            for treasure_id in TREASURES:
                for omen_id in OMENS:
                    combos.append((place_id, marker_id, treasure_id, omen_id))
    return combos


def path_severity(place: Place, linger: int) -> int:
    return place.risk + linger


def safe_return(place: Place, marker: Marker, linger: int) -> bool:
    return marker_ok(marker, place) and linger <= 1


def explain_rejection(place: Place, marker: Marker) -> str:
    if place.surface == "branches":
        return (
            f"(No story: {place.the} needs a marker that can stay on branches. "
            f"{marker.phrase.capitalize()} would not leave a reliable trail there. "
            f"Try twine.)"
        )
    if place.surface == "stone":
        return (
            f"(No story: {place.the} is all stone and echoing walls. "
            f"{marker.phrase.capitalize()} would not make a useful path there. "
            f"Try chalk.)"
        )
    if place.surface == "sand":
        return (
            f"(No story: the paths in {place.the} are sandy. "
            f"{marker.phrase.capitalize()} is not the right guide for shifting sand. "
            f"Try pebbles.)"
        )
    return "(No story: that marker does not fit this place.)"


def predict_path(place: Place, marker: Marker, linger: int) -> dict:
    w = World()
    child = w.add(Entity(id="child", kind="character", type="girl", role="child"))
    w.add(Entity(id="place", type="place", label=place.label))
    w.facts["place_cfg"] = place
    w.facts["marker_cfg"] = marker
    child.meters["entered"] = 1
    if marker_ok(marker, place):
        child.meters["prepared"] = 1
    w.facts["linger"] = linger
    propagate(w, narrate=False)
    return {
        "lost": child.meters["lost"] >= THRESHOLD or not safe_return(place, marker, linger),
        "confusion": w.get("place").meters["confusion"],
    }


def introduce(world: World, child: Entity, elder: Entity, place: Place, treasure: Treasure) -> None:
    child.memes["curiosity"] += 1
    child.memes["love"] += 1
    world.say(
        f"Once, at the edge of a mild old village, there lived {child.id}, a small "
        f"{child.type} with a curious heart. From the cottage window, {child.pronoun()} "
        f"could see {place.the}, and many evenings {child.pronoun()} wondered whether "
        f"{place.treasure} truly waited there."
    )
    world.say(
        f"{elder.label_word.capitalize()} used to say that beyond {place.approach} "
        f"lay {place.inside}, where {treasure.phrase} might be found by a child "
        f"who walked gently and came back wiser."
    )


def foreshadow(world: World, child: Entity, elder: Entity, place: Place, omen: Omen) -> None:
    child.memes["unease"] += 1
    world.say(
        f"One dusk, before {child.id} had taken a single step, {omen.sign}. "
        f"It was the sort of small sign that fairy tales remember."
    )
    world.say(
        f'"Do you hear?" {elder.label_word} asked softly. "{omen.whisper} '
        f'{place.warning}"'
    )


def offer_marker(world: World, child: Entity, elder: Entity, marker: Marker) -> None:
    child.meters["prepared"] += 1
    world.say(
        f"Then {elder.label_word} opened a work basket and drew out {marker.phrase}. "
        f'"Take this," {elder.pronoun()} said. "Wonder is lovely, but the most relevant '
        f"thing, when a path may turn, is a way to find home again.\""
    )
    world.say(
        f"{child.id} tucked {marker.label} close and promised to remember every word."
    )


def enter_place(world: World, child: Entity, place: Place) -> None:
    child.meters["entered"] += 1
    propagate(world, narrate=False)
    world.say(
        f"So at moonrise {child.id} went to {place.the}. {place.approach.capitalize()} "
        f"seemed quiet, yet the air inside held that listening hush which comes before a test."
    )
    world.say(
        f"Soon {child.pronoun()} was among {place.inside}, and every turn looked more "
        f"interesting than the last."
    )


def lay_trail(world: World, child: Entity, marker: Marker, place: Place) -> None:
    if marker_ok(marker, place):
        child.meters["trail_made"] += 1
        world.say(
            f"As {child.pronoun()} walked, {child.id} {marker.action}. "
            f"The {marker.trace_word} looked small, but it was steady."
        )
    else:
        world.say(
            f"{child.id} tried to trust {marker.label}, yet nothing in {place.the} truly "
            f"held its mark."
        )


def discover(world: World, child: Entity, place: Place, treasure: Treasure) -> None:
    child.meters["discovered"] += 1
    child.memes["wonder"] += 1
    world.say(
        f"At the heart of {place.the}, {child.id} found {treasure.phrase}. "
        f"{place.treasure_detail}"
    )
    world.say(
        f"For a little while, curiosity felt like a golden key, and the whole hidden place "
        f"seemed to smile."
    )


def turning_paths(world: World, child: Entity, place: Place) -> None:
    linger = world.facts["linger"]
    if linger > 0:
        child.meters["lingered"] += float(linger)
    propagate(world, narrate=False)
    world.say(
        f"But fairy places do not stand still for long. The paths in {place.the} bent and "
        f"doubled, and what had been near now seemed far away."
    )


def return_home(world: World, child: Entity, elder: Entity, marker: Marker, treasure: Treasure) -> None:
    child.memes["relief"] += 1
    child.memes["wisdom"] += 1
    world.say(
        f"Then {child.id} looked for the {marker.trace_word} {child.pronoun()} had left behind. "
        f"One by one, they led {child.pronoun('object')} safely out."
    )
    world.say(
        f"At the cottage door, {elder.label_word} was waiting with a lamp in hand. "
        f"{treasure.gift_text}"
    )
    world.say(
        f"After that night, {child.id} still loved mysteries, but never forgot that "
        f"curiosity walks best when it carries a path home. {treasure.ending_image}"
    )


def get_lost(world: World, child: Entity, place: Place) -> None:
    child.meters["lost"] += 1
    child.memes["fear"] += 1
    world.say(
        f"Then {child.id} turned once, and twice, and could no longer tell one path from another. "
        f"In {place.the}, even brave hearts can feel very small."
    )


def rescue(world: World, child: Entity, elder: Entity, omen: Omen) -> None:
    child.memes["relief"] += 1
    child.memes["wisdom"] += 1
    world.say(
        f"At last {child.pronoun()} heard {elder.label_word}'s call and followed it, step by step, "
        f"until the lantern-light found {child.pronoun('object')}."
    )
    world.say(
        f'{elder.label_word.capitalize()} wrapped {child.pronoun("object")} in a warm cloak and said, '
        f'"{omen.lesson}"'
    )
    world.say(
        f"After that, {child.id} still wondered about hidden things, but {child.pronoun()} learned "
        f"to carry good sense beside wonder."
    )


def tell(
    place: Place,
    marker: Marker,
    treasure: Treasure,
    omen: Omen,
    *,
    child_name: str = "Elin",
    child_type: str = "girl",
    elder_type: str = "grandmother",
    linger: int = 0,
) -> World:
    world = World()
    child = world.add(
        Entity(
            id=child_name,
            kind="character",
            type=child_type,
            label=child_name,
            role="child",
            attrs={},
        )
    )
    elder = world.add(
        Entity(
            id="Elder",
            kind="character",
            type=elder_type,
            label="the elder",
            role="elder",
            attrs={},
        )
    )
    world.add(Entity(id="place", type="place", label=place.label, attrs={}))
    world.facts["place_cfg"] = place
    world.facts["marker_cfg"] = marker
    world.facts["treasure_cfg"] = treasure
    world.facts["omen_cfg"] = omen
    world.facts["linger"] = linger
    world.facts["child"] = child
    world.facts["elder"] = elder

    introduce(world, child, elder, place, treasure)
    world.para()
    foreshadow(world, child, elder, place, omen)
    offer_marker(world, child, elder, marker)
    world.para()
    enter_place(world, child, place)
    lay_trail(world, child, marker, place)
    discover(world, child, place, treasure)
    turning_paths(world, child, place)
    world.para()

    outcome = "returned" if safe_return(place, marker, linger) else "lost_found"
    if outcome == "returned":
        return_home(world, child, elder, marker, treasure)
    else:
        get_lost(world, child, place)
        rescue(world, child, elder, omen)

    world.facts.update(
        outcome=outcome,
        marker_good=marker_ok(marker, place),
        discovered=child.meters["discovered"] >= THRESHOLD,
        lost=child.meters["lost"] >= THRESHOLD or outcome == "lost_found",
    )
    return world


PLACES = {
    "briar_maze": Place(
        id="briar_maze",
        label="briar maze",
        the="the briar maze",
        approach="a narrow green arch",
        inside="high thorny walls and sleeping white roses",
        treasure="a little moon-pear tree",
        treasure_detail="Its fruit shone like tiny lanterns among the leaves.",
        omen="the hedge leaves turned their pale undersides all at once",
        warning="The briars love to make one corner look like another.",
        route_kind="turning hedges",
        surface="branches",
        risk=2,
        tags={"maze", "briar"},
    ),
    "crystal_caves": Place(
        id="crystal_caves",
        label="crystal caves",
        the="the crystal caves",
        approach="a slate path under the hill",
        inside="blue stone halls and clear hanging crystals",
        treasure="a singing spring",
        treasure_detail="The water made silver notes that rang against the cave walls.",
        omen="two cave crows circled the hill mouth without landing",
        warning="Stone remembers echoes better than footsteps.",
        route_kind="echoing tunnels",
        surface="stone",
        risk=2,
        tags={"cave", "stone"},
    ),
    "whisper_dunes": Place(
        id="whisper_dunes",
        label="whisper dunes",
        the="the whisper dunes",
        approach="a pale ribbon of shoregrass",
        inside="soft hills of sand and little shell-bright hollows",
        treasure="a shell door under a dune",
        treasure_detail="When it opened, warm light spilled out as if the sand itself were dreaming.",
        omen="the shore stream hissed the same note three times over the sand",
        warning="The dunes change their faces whenever the wind grows playful.",
        route_kind="shifting paths",
        surface="sand",
        risk=1,
        tags={"dune", "sand"},
    ),
}

MARKERS = {
    "twine": Marker(
        id="twine",
        label="blue twine",
        phrase="a little roll of blue twine",
        action="looped the twine around low branches",
        works_on={"branches"},
        trace_word="blue loops of twine",
        tags={"twine", "trail"},
    ),
    "chalk": Marker(
        id="chalk",
        label="white chalk",
        phrase="a stick of white chalk",
        action="drew small moon marks on the stone",
        works_on={"stone"},
        trace_word="white chalk moons",
        tags={"chalk", "trail"},
    ),
    "pebbles": Marker(
        id="pebbles",
        label="bright pebbles",
        phrase="a pocket of bright pebbles",
        action="set the pebbles in tiny shining rows",
        works_on={"sand"},
        trace_word="little pebble rows",
        tags={"pebbles", "trail"},
    ),
}

TREASURES = {
    "pear": Treasure(
        id="pear",
        label="moon pear",
        phrase="a moon-pear tree no taller than a chair",
        gift_text="The child carried home one sweet moon pear, and together they shared it at breakfast.",
        ending_image="Next to the window, the silver seeds gleamed in a saucer.",
        tags={"fruit"},
    ),
    "spring": Treasure(
        id="spring",
        label="singing spring",
        phrase="a singing spring in a bowl of stone",
        gift_text="The child filled a tiny bottle with singing water, and its music trembled on the shelf for many days.",
        ending_image="Even the kettle seemed to hum when morning sun touched the glass.",
        tags={"water"},
    ),
    "shell_door": Treasure(
        id="shell_door",
        label="shell door",
        phrase="a shell door painted with starfish and moons",
        gift_text="The child brought back a small shell charm from the threshold and hung it by the bed.",
        ending_image="Whenever night wind stirred it, the room sounded softly like the sea.",
        tags={"shell"},
    ),
}

OMENS = {
    "leaves": Omen(
        id="leaves",
        sign="the leaves on the nearest ash tree turned backward and showed their silver",
        whisper="When the world turns its leaves, child, it may turn its paths as well.",
        lesson="A warning is not there to steal wonder. It is there to keep wonder from swallowing you.",
        tags={"foreshadow", "leaves"},
    ),
    "crows": Omen(
        id="crows",
        sign="three black crows flew in a circle and then flew the same circle again",
        whisper="Listen to creatures that go in circles. They know where circles lead.",
        lesson="Even a brave heart must stop and listen before it wanders farther.",
        tags={"foreshadow", "crows"},
    ),
    "stream": Omen(
        id="stream",
        sign="a thin stream beside the path kept whispering the same bright note",
        whisper="Hear that? The world is repeating itself for a reason.",
        lesson="The world often warns us in small voices before it teaches in bigger ones.",
        tags={"foreshadow", "stream"},
    ),
}

GIRL_NAMES = ["Elin", "Mira", "Aster", "Lina", "Poppy", "Tansy", "Nell", "Iris"]
BOY_NAMES = ["Rowan", "Finn", "Tobin", "Milo", "Alder", "Bram", "Nico", "Perrin"]


@dataclass
class StoryParams:
    place: str
    marker: str
    treasure: str
    omen: str
    child_name: str
    child_type: str
    elder_type: str
    linger: int = 0
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
    "twine": [
        (
            "What is twine?",
            "Twine is a thin, strong string made by twisting fibers together. People can use it to tie things or mark a path.",
        )
    ],
    "trail": [
        (
            "Why do people mark a trail?",
            "People mark a trail so they can find the same way back again. In confusing places, a good trail keeps a walk from turning into getting lost.",
        )
    ],
    "foreshadow": [
        (
            "What is a warning sign in a story?",
            "A warning sign is a small clue that hints something important may happen later. In fairy tales, it helps readers feel the danger before the trouble fully begins.",
        )
    ],
    "maze": [
        (
            "Why is a maze hard to walk through?",
            "A maze has many turns that can look alike. If you do not keep track of your path, it is easy to forget which way leads out.",
        )
    ],
    "briar": [
        (
            "What is a briar?",
            "A briar is a thorny plant or bush. It can make a place look wild, tangled, and hard to pass through.",
        )
    ],
    "chalk": [
        (
            "What does chalk do?",
            "Chalk leaves a pale mark on stone or other hard surfaces. That makes it useful for drawing signs you can see again later.",
        )
    ],
    "pebbles": [
        (
            "What is a pebble?",
            "A pebble is a small smooth stone. Little pebbles can be lined up as tiny markers along a path.",
        )
    ],
    "cave": [
        (
            "Why can caves feel confusing?",
            "Caves can echo sounds and have twisting passages. When places look and sound alike, it is easier to lose your way.",
        )
    ],
    "sand": [
        (
            "Why do sandy places change shape?",
            "Wind can push sand from one spot to another. That means a sandy path may look different later than it did before.",
        )
    ],
}


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    child = f["child"]
    place = f["place_cfg"]
    marker = f["marker_cfg"]
    omen = f["omen_cfg"]
    outcome = f["outcome"]
    if outcome == "returned":
        return [
            f'Write a short fairy tale about a curious child who visits {place.the} and uses {marker.label} to find the way home. Include the word "relevant".',
            f"Tell a gentle fairy tale where {child.id} notices a warning sign, follows curiosity anyway, and learns that the most relevant kind of magic is good sense.",
            f"Write a story with foreshadowing in which {omen.sign}, a hidden wonder is found, and a safe trail leads home.",
        ]
    return [
        f'Write a cautionary fairy tale about a curious child who goes into {place.the}, where an omen warns of trouble first. Include the words "relevant" and "twine".',
        f"Tell a fairy tale where {child.id} follows curiosity into danger, is found again by an elder, and learns to listen when the world gives small warnings.",
        f"Write a story with foreshadowing where a hidden treasure is lovely, but the way home matters even more.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    child = f["child"]
    elder = f["elder"]
    place = f["place_cfg"]
    marker = f["marker_cfg"]
    treasure = f["treasure_cfg"]
    omen = f["omen_cfg"]
    outcome = f["outcome"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {child.id}, a curious {child.type}, and {elder.label_word}, who tried to help {child.pronoun('object')} walk wisely. Their relationship matters because the warning comes from someone loving and careful.",
        ),
        (
            f"Why did {child.id} go to {place.the}?",
            f"{child.id} went because {child.pronoun()} was curious about the hidden wonder said to be there. That curiosity pulled {child.pronoun('object')} toward the place even after the warning sign appeared.",
        ),
        (
            "What was the foreshadowing sign?",
            f"The sign was this: {omen.sign}. It mattered because it hinted early that the path might not behave in a normal, safe way.",
        ),
        (
            f"Why did {elder.label_word} give {child.id} {marker.phrase}?",
            f"{elder.label_word.capitalize()} gave {child.pronoun('object')} {marker.phrase} to mark the way back. {marker.label.capitalize()} was the relevant tool for a place like {place.the}, where turns could become confusing.",
        ),
    ]
    if outcome == "returned":
        qa.extend(
            [
                (
                    f"How did {child.id} get home safely?",
                    f"{child.id} followed the trail {child.pronoun()} had made earlier and came back out safely. The path markers worked because they fit the place and turned curiosity into a careful adventure.",
                ),
                (
                    f"What did {child.id} find in {place.the}?",
                    f"{child.pronoun().capitalize()} found {treasure.phrase}. The discovery feels magical, but the ending shows that bringing back wisdom mattered just as much as finding wonder.",
                ),
                (
                    "What changed by the end of the story?",
                    f"By the end, {child.id} was still curious, but wiser. {child.pronoun().capitalize()} learned that a fairy-tale journey needs both wonder and a way home.",
                ),
            ]
        )
    else:
        qa.extend(
            [
                (
                    f"What went wrong in {place.the}?",
                    f"The paths turned and looked too much alike, and {child.id} could not tell which way led out. The earlier omen foreshadowed this trouble by hinting that the place would not stay steady.",
                ),
                (
                    f"How was {child.id} found?",
                    f"{elder.label_word.capitalize()} called and searched with a lantern until {child.id} heard the voice and followed it. The rescue happened because the elder kept looking instead of giving up.",
                ),
                (
                    "What did the child learn?",
                    f"{child.id} learned that wonder without care can become danger. Afterward, {child.pronoun()} still loved mysteries, but listened more carefully to warnings and wise advice.",
                ),
            ]
        )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags = {"trail", "foreshadow"} | set(f["marker_cfg"].tags) | set(f["place_cfg"].tags)
    out: list[tuple[str, str]] = []
    order = ["twine", "trail", "foreshadow", "maze", "briar", "chalk", "pebbles", "cave", "sand"]
    for tag in order:
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
        bits = []
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
        lines.append(f"  {ent.id:8} ({ent.type:12}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    lines.append(f"  facts: outcome={world.facts.get('outcome')} linger={world.facts.get('linger')}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        place="briar_maze",
        marker="twine",
        treasure="pear",
        omen="leaves",
        child_name="Elin",
        child_type="girl",
        elder_type="grandmother",
        linger=0,
    ),
    StoryParams(
        place="crystal_caves",
        marker="chalk",
        treasure="spring",
        omen="crows",
        child_name="Rowan",
        child_type="boy",
        elder_type="grandmother",
        linger=1,
    ),
    StoryParams(
        place="whisper_dunes",
        marker="pebbles",
        treasure="shell_door",
        omen="stream",
        child_name="Mira",
        child_type="girl",
        elder_type="grandmother",
        linger=0,
    ),
    StoryParams(
        place="briar_maze",
        marker="twine",
        treasure="shell_door",
        omen="leaves",
        child_name="Bram",
        child_type="boy",
        elder_type="grandmother",
        linger=2,
    ),
]


ASP_RULES = r"""
valid(P, M, T, O) :- place(P), marker(M), treasure(T), omen(O), surface(P, S), works_on(M, S).

severity(V) :- chosen_place(P), risk(P, R), linger(L), V = R + L.
prepared :- chosen_place(P), chosen_marker(M), surface(P, S), works_on(M, S).
returned :- prepared, linger(L), L <= 1.
outcome(returned) :- returned.
outcome(lost_found) :- not returned.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for pid, place in PLACES.items():
        lines.append(asp.fact("place", pid))
        lines.append(asp.fact("surface", pid, place.surface))
        lines.append(asp.fact("risk", pid, place.risk))
    for mid, marker in MARKERS.items():
        lines.append(asp.fact("marker", mid))
        for surf in sorted(marker.works_on):
            lines.append(asp.fact("works_on", mid, surf))
    for tid in TREASURES:
        lines.append(asp.fact("treasure", tid))
    for oid in OMENS:
        lines.append(asp.fact("omen", oid))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("", "#show valid/4."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_outcome(params: StoryParams) -> str:
    import asp

    extra = "\n".join(
        [
            asp.fact("chosen_place", params.place),
            asp.fact("chosen_marker", params.marker),
            asp.fact("linger", params.linger),
        ]
    )
    model = asp.one_model(asp_program(extra, "#show outcome/1."))
    out = asp.atoms(model, "outcome")
    return out[0][0] if out else "?"


def outcome_of(params: StoryParams) -> str:
    place = PLACES[params.place]
    marker = MARKERS[params.marker]
    return "returned" if safe_return(place, marker, params.linger) else "lost_found"


def asp_verify() -> int:
    rc = 0

    cset = set(asp_valid_combos())
    pset = set(valid_combos())
    if cset == pset:
        print(f"OK: gate matches valid_combos() ({len(cset)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos:")
        if cset - pset:
            print("  only in clingo:", sorted(cset - pset))
        if pset - cset:
            print("  only in python:", sorted(pset - cset))

    cases = list(CURATED)
    parser = build_parser()
    for seed in range(20):
        try:
            params = resolve_params(parser.parse_args([]), random.Random(seed))
            params.seed = seed
            cases.append(params)
        except StoryError:
            rc = 1
            print(f"Unexpected StoryError during random resolve at seed {seed}.")
            break

    bad = [p for p in cases if asp_outcome(p) != outcome_of(p)]
    if not bad:
        print(f"OK: outcome model matches on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {len(bad)} scenarios differ.")

    try:
        smoke = generate(CURATED[0])
        if not smoke.story.strip():
            raise StoryError("smoke test generated an empty story")
        emit(smoke, trace=False, qa=False, header="")
        print("OK: smoke generation/emit succeeded.")
    except Exception as exc:  # pragma: no cover
        rc = 1
        print(f"SMOKE TEST FAILED: {exc}")

    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Fairy-tale storyworld: curiosity, foreshadowing, and a marked path home."
    )
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--marker", choices=MARKERS)
    ap.add_argument("--treasure", choices=TREASURES)
    ap.add_argument("--omen", choices=OMENS)
    ap.add_argument("--child-type", choices=["girl", "boy"])
    ap.add_argument("--child-name")
    ap.add_argument("--elder-type", choices=["grandmother", "mother", "father"])
    ap.add_argument(
        "--linger",
        type=int,
        choices=[0, 1, 2],
        help="how long the child lingers in the hidden place before trying to come back",
    )
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list the compatible-story set derived by clingo")
    ap.add_argument("--verify", action="store_true", help="check the inline ASP reasoner and smoke-test generation")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.place and args.marker:
        place = PLACES[args.place]
        marker = MARKERS[args.marker]
        if not marker_ok(marker, place):
            raise StoryError(explain_rejection(place, marker))

    combos = [
        combo
        for combo in valid_combos()
        if (args.place is None or combo[0] == args.place)
        and (args.marker is None or combo[1] == args.marker)
        and (args.treasure is None or combo[2] == args.treasure)
        and (args.omen is None or combo[3] == args.omen)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    place_id, marker_id, treasure_id, omen_id = rng.choice(sorted(combos))
    child_type = args.child_type or rng.choice(["girl", "boy"])
    if args.child_name:
        child_name = args.child_name
    else:
        child_name = rng.choice(GIRL_NAMES if child_type == "girl" else BOY_NAMES)
    elder_type = args.elder_type or rng.choice(["grandmother", "mother", "father"])
    linger = args.linger if args.linger is not None else rng.choice([0, 1, 2])

    return StoryParams(
        place=place_id,
        marker=marker_id,
        treasure=treasure_id,
        omen=omen_id,
        child_name=child_name,
        child_type=child_type,
        elder_type=elder_type,
        linger=linger,
    )


def generate(params: StoryParams) -> StorySample:
    try:
        place = PLACES[params.place]
        marker = MARKERS[params.marker]
        treasure = TREASURES[params.treasure]
        omen = OMENS[params.omen]
    except KeyError as exc:
        raise StoryError(f"(Invalid parameter value: {exc})") from None

    if not marker_ok(marker, place):
        raise StoryError(explain_rejection(place, marker))

    world = tell(
        place=place,
        marker=marker,
        treasure=treasure,
        omen=omen,
        child_name=params.child_name,
        child_type=params.child_type,
        elder_type=params.elder_type,
        linger=params.linger,
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
        print(asp_program("", "#show valid/4.\n#show outcome/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (place, marker, treasure, omen) combos:\n")
        for place, marker, treasure, omen in combos:
            print(f"  {place:14} {marker:8} {treasure:10} {omen}")
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
            header = f"### {p.child_name}: {p.place} with {p.marker} ({outcome_of(p)})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()

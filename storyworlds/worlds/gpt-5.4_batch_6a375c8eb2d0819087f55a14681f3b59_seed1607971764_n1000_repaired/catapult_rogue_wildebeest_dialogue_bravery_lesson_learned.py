#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/catapult_rogue_wildebeest_dialogue_bravery_lesson_learned.py
=========================================================================================

A standalone story world about a child, a careful grown-up, a rogue wildebeest,
and a homemade catapult used in a calm, sensible way.

The tiny domain is slice-of-life in shape: a normal day is interrupted when a
rogue wildebeest wanders where it should not be. The tension is not "fight the
animal" but "how do we help safely?" The turn comes when someone remembers the
catapult can toss a trail of greens from a safe distance, and the ending image
shows the child understanding that bravery means staying calm and choosing the
safe idea.

Run it
------
    python storyworlds/worlds/gpt-5.4/catapult_rogue_wildebeest_dialogue_bravery_lesson_learned.py
    python storyworlds/worlds/gpt-5.4/catapult_rogue_wildebeest_dialogue_bravery_lesson_learned.py --place laundry_yard --lure lettuce --catapult crate_catapult
    python storyworlds/worlds/gpt-5.4/catapult_rogue_wildebeest_dialogue_bravery_lesson_learned.py --lure cookies
    python storyworlds/worlds/gpt-5.4/catapult_rogue_wildebeest_dialogue_bravery_lesson_learned.py --all --qa
    python storyworlds/worlds/gpt-5.4/catapult_rogue_wildebeest_dialogue_bravery_lesson_learned.py --verify
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
BRAVE_IDEA_THRESHOLD = 5


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    role: str = ""
    traits: list[str] = field(default_factory=list)
    attrs: dict = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "woman", "aunt"}
        male = {"boy", "father", "man", "uncle"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return {"mother": "mom", "father": "dad", "aunt": "aunt", "uncle": "uncle"}.get(
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
    scene: str
    trouble: str
    gate: str
    distance: int
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
class Lure:
    id: str
    label: str
    phrase: str
    weight: int
    appeal: int
    trail: str
    lesson: str
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
class CatapultKind:
    id: str
    label: str
    phrase: str
    power: int
    gentle: bool = True
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
    label: str
    bravery: int
    style: str
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
        clone.facts = dict(self.facts)
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


def _r_alarm(world: World) -> list[str]:
    out: list[str] = []
    beast = world.get("wildebeest")
    if beast.meters["rogue"] < THRESHOLD:
        return out
    sig = ("alarm", "wildebeest")
    if sig in world.fired:
        return out
    world.fired.add(sig)
    world.get("child").memes["fear"] += 1
    world.get("adult").memes["focus"] += 1
    world.get("yard").meters["risk"] += 1
    out.append("__alarm__")
    return out


def _r_follow(world: World) -> list[str]:
    out: list[str] = []
    beast = world.get("wildebeest")
    lure = world.get("lure")
    catapult = world.get("catapult")
    gate = world.get("gate")
    if beast.meters["rogue"] < THRESHOLD:
        return out
    if lure.meters["launched"] < THRESHOLD:
        return out
    if catapult.meters["in_range"] < THRESHOLD:
        return out
    if lure.meters["tempting"] < THRESHOLD:
        return out
    sig = ("follow", "wildebeest")
    if sig in world.fired:
        return out
    world.fired.add(sig)
    beast.meters["following"] += 1
    beast.meters["near_gate"] += 1
    gate.meters["ready"] += 1
    out.append("__follow__")
    return out


def _r_return(world: World) -> list[str]:
    out: list[str] = []
    beast = world.get("wildebeest")
    gate = world.get("gate")
    if beast.meters["near_gate"] < THRESHOLD or gate.meters["open"] < THRESHOLD:
        return out
    sig = ("return", "wildebeest")
    if sig in world.fired:
        return out
    world.fired.add(sig)
    beast.meters["rogue"] = 0.0
    beast.meters["home"] += 1
    world.get("child").memes["relief"] += 1
    world.get("adult").memes["relief"] += 1
    out.append("__return__")
    return out


CAUSAL_RULES = [
    Rule(name="alarm", tag="social", apply=_r_alarm),
    Rule(name="follow", tag="physical", apply=_r_follow),
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
        for sent in produced:
            world.say(sent)
    return produced


def can_launch(catapult: CatapultKind, lure: Lure) -> bool:
    return catapult.power >= lure.weight


def reaches_gate(place: Place, catapult: CatapultKind) -> bool:
    return catapult.power >= place.distance


def worth_following(lure: Lure) -> bool:
    return lure.appeal >= 2


def valid_combo(place: Place, lure: Lure, catapult: CatapultKind) -> bool:
    return can_launch(catapult, lure) and reaches_gate(place, catapult) and worth_following(lure)


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for place_id, place in PLACES.items():
        for lure_id, lure in LURES.items():
            for cat_id, catapult in CATAPULTS.items():
                if valid_combo(place, lure, catapult):
                    combos.append((place_id, lure_id, cat_id))
    return sorted(combos)


def brave_enough(trait: Trait, trust: int) -> bool:
    return trait.bravery + trust >= BRAVE_IDEA_THRESHOLD


def predict_follow(place: Place, lure: Lure, catapult: CatapultKind) -> dict:
    return {
        "reaches_gate": reaches_gate(place, catapult),
        "tempting": worth_following(lure),
        "launches": can_launch(catapult, lure),
        "works": valid_combo(place, lure, catapult),
    }


def introduce(world: World, child: Entity, adult: Entity, place: Place) -> None:
    world.say(
        f"After breakfast, {child.id} helped {adult.pronoun('possessive')} {adult.label_word} "
        f"in {place.label}. {place.scene}"
    )


def ordinary_task(world: World, child: Entity, adult: Entity) -> None:
    world.say(
        f"They were only trying to finish a small morning chore together, and the air felt easy and quiet."
    )
    world.say(
        f'"Pass me the clothespins," {adult.pronoun()} said. "{child.id}, you hand them up and I\'ll clip."'
    )


def rogue_appears(world: World, child: Entity, adult: Entity, place: Place) -> None:
    beast = world.get("wildebeest")
    beast.meters["rogue"] += 1
    propagate(world, narrate=False)
    world.say(
        f"Then a rogue wildebeest wandered in from the safari paddock and {place.trouble}."
    )
    world.say(f'"Oh!" {child.id} whispered. "{adult.label_word.capitalize()}, it\'s right here."')


def adult_warning(world: World, adult: Entity, child: Entity) -> None:
    world.say(
        f'"Stay by me," {adult.label_word} said at once. "A big animal can get jumpy when it is in the wrong place."'
    )
    if child.memes["fear"] >= THRESHOLD:
        world.say(
            f"{child.id} took one quick step back, but kept watching."
        )


def remember_catapult(world: World, child: Entity, adult: Entity, place: Place,
                      lure: Lure, catapult: CatapultKind, trait: Trait, trust: int) -> str:
    pred = predict_follow(place, lure, catapult)
    world.facts["predicted_works"] = pred["works"]
    world.facts["predicted_reaches_gate"] = pred["reaches_gate"]
    world.facts["predicted_tempting"] = pred["tempting"]
    if not pred["works"]:
        return "none"
    if brave_enough(trait, trust):
        child.memes["bravery"] += 1
        world.say(
            f'{child.id} swallowed hard, then spoke in {trait.style} voice. "What about the {catapult.label} by the shed?"'
        )
        world.say(
            f'"If we toss {lure.phrase} toward {place.gate}, maybe the wildebeest will follow the snacks instead of us," '
            f"{child.pronoun()} said."
        )
        world.say(
            f'{adult.label_word.capitalize()} looked at {child.pronoun("object")} and nodded. "That is a brave idea because it keeps us back."'
        )
        return "child"
    world.say(
        f'{child.id} held very still. Then {adult.label_word} glanced toward the shed. "I know," {adult.pronoun()} said. '
        f'"We can use the {catapult.label} to toss {lure.phrase} toward {place.gate}."'
    )
    world.say(
        f'"We are not going to chase the wildebeest," {adult.pronoun()} added. "We will give it a safe trail to follow."'
    )
    return "adult"


def ready_tool(world: World, child: Entity, adult: Entity, catapult: CatapultKind, lure: Lure) -> None:
    catapult_ent = world.get("catapult")
    lure_ent = world.get("lure")
    catapult_ent.meters["in_range"] = 1.0
    lure_ent.meters["tempting"] = 1.0
    world.say(
        f"They moved to the shed without hurrying. The {catapult.label} was small and homemade, just right for tossing soft things and not for hurting anything."
    )
    world.say(
        f'"Ready?" {adult.label_word} asked. "{child.id}, we only launch the {lure.label}, and we keep our feet behind the stepping stones."'
    )


def launch_trail(world: World, child: Entity, adult: Entity, place: Place, lure: Lure) -> None:
    lure_ent = world.get("lure")
    gate_ent = world.get("gate")
    lure_ent.meters["launched"] += 1
    gate_ent.meters["open"] = 1.0
    propagate(world, narrate=False)
    world.say(
        f'Twang. The first bit of {lure.label} sailed in a gentle arc and landed near the path.'
    )
    world.say(
        f"Then another piece landed closer to {place.gate}, making {lure.trail}."
    )


def wildebeest_follows(world: World, child: Entity, adult: Entity, place: Place) -> None:
    beast = world.get("wildebeest")
    if beast.meters["home"] < THRESHOLD:
        raise StoryError("The wildebeest did not return home as expected.")
    child.memes["wonder"] += 1
    world.say(
        "The wildebeest lifted its heavy head, sniffed, and clopped after the trail."
    )
    world.say(
        f'It passed the flower pots, reached {place.gate}, and went back through with one last swish of its tail.'
    )
    world.say(f'"There you go," {adult.label_word} said softly, sliding the latch shut.')


def lesson(world: World, child: Entity, adult: Entity, lure: Lure) -> None:
    child.memes["lesson"] += 1
    adult.memes["pride"] += 1
    world.say(
        f"{child.id} let out the breath {child.pronoun()} had been holding."
    )
    world.say(
        f'"I was scared," {child.pronoun()} admitted.'
    )
    world.say(
        f'"So was I a little," {adult.label_word} said. "Bravery does not mean marching up to trouble. It means choosing the safe thing even while your heart is thumping."'
    )
    world.say(
        f'{child.id} looked at the quiet path and nodded. "So the lesson is to use a smart plan, not a wild one."'
    )
    world.say(
        f'"Exactly," {adult.label_word} said. "And today the smart plan was the catapult and the {lure.label}."'
    )


def closing_image(world: World, child: Entity, adult: Entity, place: Place) -> None:
    child.memes["joy"] += 1
    world.say(
        f"After that, they finished the morning chore together."
    )
    world.say(
        f"The yard felt ordinary again. {child.id} clipped up the last corner, and beyond the fence the wildebeest was only a brown bump in the sunny grass."
    )


def tell(place: Place, lure: Lure, catapult: CatapultKind, child_name: str,
         child_gender: str, adult_type: str, trait: Trait, trust: int) -> World:
    world = World(place)
    child = world.add(Entity(id=child_name, kind="character", type=child_gender, role="child",
                             traits=[trait.id], attrs={"trust": trust}))
    adult = world.add(Entity(id="Adult", kind="character", type=adult_type, role="adult",
                             label="the grown-up"))
    yard = world.add(Entity(id="yard", type="place", label=place.label))
    beast = world.add(Entity(id="wildebeest", type="animal", label="wildebeest"))
    gate = world.add(Entity(id="gate", type="gate", label=place.gate))
    lure_ent = world.add(Entity(id="lure", type="food", label=lure.label))
    catapult_ent = world.add(Entity(id="catapult", type="tool", label=catapult.label))

    child.memes["fear"] = 0.0
    child.memes["bravery"] = 0.0
    child.memes["lesson"] = 0.0
    adult.memes["focus"] = 0.0
    adult.memes["relief"] = 0.0
    beast.meters["rogue"] = 0.0
    beast.meters["home"] = 0.0
    beast.meters["near_gate"] = 0.0
    catapult_ent.meters["in_range"] = 0.0
    lure_ent.meters["launched"] = 0.0
    lure_ent.meters["tempting"] = 0.0
    gate.meters["open"] = 0.0
    yard.meters["risk"] = 0.0

    introduce(world, child, adult, place)
    ordinary_task(world, child, adult)

    world.para()
    rogue_appears(world, child, adult, place)
    adult_warning(world, adult, child)

    world.para()
    idea_owner = remember_catapult(world, child, adult, place, lure, catapult, trait, trust)
    if idea_owner == "none":
        raise StoryError("This combination cannot honestly solve the problem.")
    ready_tool(world, child, adult, catapult, lure)
    launch_trail(world, child, adult, place, lure)

    world.para()
    wildebeest_follows(world, child, adult, place)
    lesson(world, child, adult, lure)

    world.para()
    closing_image(world, child, adult, place)

    world.facts.update(
        child=child,
        adult=adult,
        place=place,
        lure=lure,
        catapult=catapult,
        trust=trust,
        trait=trait,
        idea_owner=idea_owner,
        returned=beast.meters["home"] >= THRESHOLD,
        lesson_learned=child.memes["lesson"] >= THRESHOLD,
    )
    return world


PLACES = {
    "laundry_yard": Place(
        id="laundry_yard",
        label="the laundry yard",
        scene="Sheets flapped on the line, and a basket of warm towels sat on the bench.",
        trouble="stopped beside the sheets and stared at its own shadow in the white cloth",
        gate="the side paddock gate",
        distance=2,
        tags={"yard", "laundry"},
    ),
    "vegetable_patch": Place(
        id="vegetable_patch",
        label="the vegetable patch",
        scene="Tomato vines leaned on their stakes, and the hose made a shiny curl near the beans.",
        trouble="lowered its nose toward the lettuce bed as if it had been invited to lunch",
        gate="the garden gate back to the paddock",
        distance=3,
        tags={"garden", "vegetables"},
    ),
    "picnic_lawn": Place(
        id="picnic_lawn",
        label="the picnic lawn",
        scene="A striped blanket was drying on the grass, and cups from lemonade waited on a tray.",
        trouble="ambled between the little folding chairs and made them wobble",
        gate="the wide paddock gate",
        distance=1,
        tags={"lawn", "picnic"},
    ),
}

LURES = {
    "lettuce": Lure(
        id="lettuce",
        label="lettuce leaves",
        phrase="a handful of crisp lettuce leaves",
        weight=1,
        appeal=3,
        trail="a green dotted line on the ground",
        lesson="lettuce is a safer lure than chasing",
        tags={"lettuce", "herbivore"},
    ),
    "hay": Lure(
        id="hay",
        label="soft hay twists",
        phrase="a bundle of soft hay twists",
        weight=2,
        appeal=2,
        trail="a pale, scratchy trail along the path",
        lesson="hay can guide a grazing animal from far away",
        tags={"hay", "herbivore"},
    ),
    "apple": Lure(
        id="apple",
        label="apple slices",
        phrase="a bowl of apple slices",
        weight=1,
        appeal=2,
        trail="little bright pieces shining in the sun",
        lesson="small treats work better when they are easy to notice",
        tags={"apple", "herbivore"},
    ),
    "cookies": Lure(
        id="cookies",
        label="crumbly cookies",
        phrase="some crumbly cookies",
        weight=1,
        appeal=1,
        trail="a messy line of crumbs",
        lesson="cookies are for people, not for guiding a wildebeest",
        tags={"cookies"},
    ),
}

CATAPULTS = {
    "spoon_catapult": CatapultKind(
        id="spoon_catapult",
        label="spoon catapult",
        phrase="a spoon catapult made from a paint stick and a rubber band",
        power=1,
        gentle=True,
        tags={"catapult"},
    ),
    "crate_catapult": CatapultKind(
        id="crate_catapult",
        label="crate catapult",
        phrase="a crate catapult tied together from a fruit crate and a cloth sling",
        power=2,
        gentle=True,
        tags={"catapult"},
    ),
    "wagon_catapult": CatapultKind(
        id="wagon_catapult",
        label="wagon catapult",
        phrase="a wagon catapult with a long wooden arm and a deep cloth cup",
        power=3,
        gentle=True,
        tags={"catapult"},
    ),
}

TRAITS = {
    "steady": Trait(id="steady", label="steady", bravery=3, style="a steady"),
    "quiet": Trait(id="quiet", label="quiet", bravery=2, style="a quiet"),
    "bold": Trait(id="bold", label="bold", bravery=4, style="a bold"),
    "thoughtful": Trait(id="thoughtful", label="thoughtful", bravery=3, style="a thoughtful"),
}

GIRL_NAMES = ["Lina", "Maya", "Zoe", "Nora", "Ella", "June"]
BOY_NAMES = ["Ben", "Sam", "Leo", "Owen", "Finn", "Theo"]


@dataclass
class StoryParams:
    place: str
    lure: str
    catapult: str
    child_name: str
    child_gender: str
    adult_type: str
    trait: str
    trust: int = 2
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
    "wildebeest": [
        (
            "What is a wildebeest?",
            "A wildebeest is a big grazing animal with a heavy head and long legs. It eats plants and can move quickly when it feels unsure.",
        )
    ],
    "rogue": [
        (
            "What does rogue mean in this story?",
            "Here, rogue means the animal has wandered away from where it belongs. It is not being mean on purpose; it is simply in the wrong place.",
        )
    ],
    "catapult": [
        (
            "What is a catapult?",
            "A catapult is a tool that tosses something through the air. In this story, it is used gently to launch food from a safe distance, not to hurt anyone.",
        )
    ],
    "herbivore": [
        (
            "Why would a wildebeest follow lettuce or hay?",
            "A wildebeest is a plant-eating animal, so green leaves or hay make sense as a lure. Food it already likes is easier for it to notice and trust.",
        )
    ],
    "bravery": [
        (
            "What is bravery?",
            "Bravery is doing the safe, right thing even when you feel nervous. It does not mean rushing close to danger just to look brave.",
        )
    ],
    "gate": [
        (
            "Why guide an animal toward a gate?",
            "A gate leads the animal back to the place where it belongs. That is safer than chasing it from behind and making it more scared.",
        )
    ],
}
KNOWLEDGE_ORDER = ["wildebeest", "rogue", "catapult", "herbivore", "bravery", "gate"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    child = f["child"]
    adult = f["adult"]
    place = f["place"]
    lure = f["lure"]
    return [
        f'Write a slice-of-life story for a 3-to-5-year-old that includes the words "catapult", "rogue", and "wildebeest".',
        f"Tell a gentle story where {child.id} helps {child.pronoun('possessive')} {adult.label_word} when a rogue wildebeest wanders into {place.label}, and dialogue shows how they stay calm.",
        f"Write a story about bravery where a child uses a catapult to toss {lure.label} from a safe distance and learns that smart choices are braver than wild ones.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    child = f["child"]
    adult = f["adult"]
    place = f["place"]
    lure = f["lure"]
    catapult = f["catapult"]
    idea_owner = f["idea_owner"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {child.id}, {child.pronoun('possessive')} {adult.label_word}, and a rogue wildebeest that wandered into {place.label}. The trouble began during an ordinary morning chore.",
        ),
        (
            "What problem did they have?",
            f"A rogue wildebeest came into {place.label} and did not belong there. That made the yard feel risky because a big, jumpy animal can move suddenly.",
        ),
        (
            "How did they solve the problem?",
            f"They used the {catapult.label} to toss {lure.label} toward {place.gate}. The food made a trail, and the wildebeest followed it back through the gate instead of being chased.",
        ),
    ]
    if idea_owner == "child":
        qa.append(
            (
                f"How was {child.id} brave?",
                f"{child.id} was brave by speaking up even while feeling scared. {child.pronoun().capitalize()} suggested a safe plan that kept everyone back from the wildebeest.",
            )
        )
    else:
        qa.append(
            (
                f"Why was the grown-up's plan a brave plan too?",
                f"It was brave because the grown-up stayed calm and chose a careful answer instead of a noisy, risky one. That helped {child.id} see that courage can look quiet and thoughtful.",
            )
        )
    qa.append(
        (
            "What lesson did the child learn?",
            f"{child.id} learned that bravery does not mean marching straight at trouble. It means choosing the smart, safe plan even when your heart is thumping.",
        )
    )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags = {"wildebeest", "rogue", "catapult", "bravery", "gate"}
    lure = world.facts["lure"]
    if lure.id in {"lettuce", "hay", "apple"}:
        tags.add("herbivore")
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
        if e.role:
            bits.append(f"role={e.role}")
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if e.attrs:
            shown = {k: v for k, v in e.attrs.items() if v or v == 0}
            if shown:
                bits.append(f"attrs={shown}")
        lines.append(f"  {e.id:10} ({e.type:10}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        place="laundry_yard",
        lure="lettuce",
        catapult="crate_catapult",
        child_name="Maya",
        child_gender="girl",
        adult_type="father",
        trait="thoughtful",
        trust=2,
    ),
    StoryParams(
        place="vegetable_patch",
        lure="hay",
        catapult="wagon_catapult",
        child_name="Ben",
        child_gender="boy",
        adult_type="mother",
        trait="steady",
        trust=1,
    ),
    StoryParams(
        place="picnic_lawn",
        lure="apple",
        catapult="spoon_catapult",
        child_name="Ella",
        child_gender="girl",
        adult_type="aunt",
        trait="bold",
        trust=2,
    ),
    StoryParams(
        place="laundry_yard",
        lure="apple",
        catapult="crate_catapult",
        child_name="Leo",
        child_gender="boy",
        adult_type="uncle",
        trait="quiet",
        trust=1,
    ),
]


def explain_rejection(place: Place, lure: Lure, catapult: CatapultKind) -> str:
    if not worth_following(lure):
        return (
            f"(No story: {lure.label} is not a sensible lure for a wildebeest here. "
            f"Use plant food like lettuce, hay, or apple slices.)"
        )
    if not can_launch(catapult, lure):
        return (
            f"(No story: the {catapult.label} cannot honestly toss {lure.label}. "
            f"Pick a lighter lure or a stronger catapult.)"
        )
    if not reaches_gate(place, catapult):
        return (
            f"(No story: the {catapult.label} cannot reach {place.gate} from {place.label}. "
            f"Pick a stronger catapult or a nearer place.)"
        )
    return "(No story: this combination does not form a reasonable solution.)"


def outcome_of(params: StoryParams) -> str:
    trait = TRAITS[params.trait]
    return "child_idea" if brave_enough(trait, params.trust) else "adult_idea"


ASP_RULES = r"""
launches(C,L) :- catapult(C), lure(L), power(C,P), weight(L,W), P >= W.
reaches(Pl,C) :- place(Pl), catapult(C), distance(Pl,D), power(C,P), P >= D.
tempting(L)   :- lure(L), appeal(L,A), A >= 2.
valid(Pl,L,C) :- place(Pl), lure(L), catapult(C), launches(C,L), reaches(Pl,C), tempting(L).

child_idea :- trait(T), bravery(T,B), trust(Tr), B + Tr >= brave_min(M).
adult_idea :- not child_idea.
outcome(child_idea) :- child_idea.
outcome(adult_idea) :- adult_idea.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for place_id, place in PLACES.items():
        lines.append(asp.fact("place", place_id))
        lines.append(asp.fact("distance", place_id, place.distance))
    for lure_id, lure in LURES.items():
        lines.append(asp.fact("lure", lure_id))
        lines.append(asp.fact("weight", lure_id, lure.weight))
        lines.append(asp.fact("appeal", lure_id, lure.appeal))
    for cat_id, catapult in CATAPULTS.items():
        lines.append(asp.fact("catapult", cat_id))
        lines.append(asp.fact("power", cat_id, catapult.power))
    for trait_id, trait in TRAITS.items():
        lines.append(asp.fact("trait_def", trait_id))
        lines.append(asp.fact("bravery", trait_id, trait.bravery))
    lines.append(asp.fact("brave_min", BRAVE_IDEA_THRESHOLD))
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
            asp.fact("trait", params.trait),
            asp.fact("trust", params.trust),
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

    cases = list(CURATED)
    for seed in range(50):
        try:
            params = resolve_params(build_parser().parse_args([]), random.Random(seed))
        except StoryError:
            continue
        cases.append(params)
    mismatches = [p for p in cases if asp_outcome(p) != outcome_of(p)]
    if not mismatches:
        print(f"OK: outcome model matches on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {len(mismatches)} outcome differences.")

    try:
        sample = generate(CURATED[0])
        if not sample.story.strip():
            raise StoryError("Smoke test produced empty story.")
        print("OK: smoke test story generation succeeded.")
    except Exception as err:  # pragma: no cover
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Story world: a calm grown-up, a child, a catapult, and a rogue wildebeest."
    )
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--lure", choices=LURES)
    ap.add_argument("--catapult", choices=CATAPULTS)
    ap.add_argument("--adult", choices=["mother", "father", "aunt", "uncle"])
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--name")
    ap.add_argument("--trait", choices=TRAITS)
    ap.add_argument("--trust", type=int, choices=[0, 1, 2, 3], help="extra confidence for speaking up")
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
    if args.place and args.lure and args.catapult:
        place = PLACES[args.place]
        lure = LURES[args.lure]
        catapult = CATAPULTS[args.catapult]
        if not valid_combo(place, lure, catapult):
            raise StoryError(explain_rejection(place, lure, catapult))

    combos = [
        combo for combo in valid_combos()
        if (args.place is None or combo[0] == args.place)
        and (args.lure is None or combo[1] == args.lure)
        and (args.catapult is None or combo[2] == args.catapult)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    place_id, lure_id, catapult_id = rng.choice(combos)
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    adult = args.adult or rng.choice(["mother", "father", "aunt", "uncle"])
    trait = args.trait or rng.choice(sorted(TRAITS))
    trust = args.trust if args.trust is not None else rng.choice([0, 1, 2, 3])
    return StoryParams(
        place=place_id,
        lure=lure_id,
        catapult=catapult_id,
        child_name=name,
        child_gender=gender,
        adult_type=adult,
        trait=trait,
        trust=trust,
    )


def generate(params: StoryParams) -> StorySample:
    if params.place not in PLACES:
        raise StoryError(f"Unknown place: {params.place}")
    if params.lure not in LURES:
        raise StoryError(f"Unknown lure: {params.lure}")
    if params.catapult not in CATAPULTS:
        raise StoryError(f"Unknown catapult: {params.catapult}")
    if params.trait not in TRAITS:
        raise StoryError(f"Unknown trait: {params.trait}")

    place = PLACES[params.place]
    lure = LURES[params.lure]
    catapult = CATAPULTS[params.catapult]
    if not valid_combo(place, lure, catapult):
        raise StoryError(explain_rejection(place, lure, catapult))

    world = tell(
        place=place,
        lure=lure,
        catapult=catapult,
        child_name=params.child_name,
        child_gender=params.child_gender,
        adult_type=params.adult_type,
        trait=TRAITS[params.trait],
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
        print(f"{len(combos)} compatible (place, lure, catapult) combos:\n")
        for place, lure, catapult in combos:
            print(f"  {place:16} {lure:8} {catapult}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(p) for p in CURATED]
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
            header = f"### {p.child_name}: {p.lure} at {p.place} with {p.catapult} ({outcome_of(p)})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()

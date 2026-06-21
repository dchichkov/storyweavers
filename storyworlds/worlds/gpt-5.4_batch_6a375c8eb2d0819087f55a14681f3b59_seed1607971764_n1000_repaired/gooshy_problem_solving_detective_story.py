#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/gooshy_problem_solving_detective_story.py
====================================================================

A small detective-style storyworld about a child solving a tiny mystery by
following physical clues. The world models a missing object, a gooshy clue,
a short list of suspects, and a simple deduction: the detective compares what
was taken, what kind of tracks were left, and which hiding place makes sense.

Run it
------
python storyworlds/worlds/gpt-5.4/gooshy_problem_solving_detective_story.py
python storyworlds/worlds/gpt-5.4/gooshy_problem_solving_detective_story.py --place kitchen --material jam --item sandwich --culprit puppy
python storyworlds/worlds/gpt-5.4/gooshy_problem_solving_detective_story.py -n 5 --seed 7 --qa
python storyworlds/worlds/gpt-5.4/gooshy_problem_solving_detective_story.py --all
python storyworlds/worlds/gpt-5.4/gooshy_problem_solving_detective_story.py --trace
python storyworlds/worlds/gpt-5.4/gooshy_problem_solving_detective_story.py --asp
python storyworlds/worlds/gpt-5.4/gooshy_problem_solving_detective_story.py --verify
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
    role: str = ""
    attrs: dict = field(default_factory=dict)
    tags: set[str] = field(default_factory=set)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "woman", "sister"}
        male = {"boy", "father", "man", "brother"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    @property
    def label_word(self) -> str:
        return {"mother": "mom", "father": "dad"}.get(self.type, self.type)
    @property
    def phrase(self) -> str:
        return str(getattr(self, "_phrase", None) or getattr(self, "label_word", None) or getattr(self, "label", None) or getattr(self, "id", self.__class__.__name__.lower()))

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)


@dataclass
class Place:
    id: str
    label: str
    opening: str
    nook: str
    material_ids: set[str] = field(default_factory=set)
    visitors: set[str] = field(default_factory=set)
    spots: dict[str, str] = field(default_factory=dict)
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
class Material:
    id: str
    label: str
    phrase: str
    texture: str
    source: str
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
class ItemCfg:
    id: str
    label: str
    phrase: str
    category: str
    size: str
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
class CulpritCfg:
    id: str
    label: str
    type: str
    track: str
    track_phrase: str
    motive: str
    likes: set[str] = field(default_factory=set)
    can_carry: set[str] = field(default_factory=set)
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
class DetectiveStyle:
    id: str
    opener: str
    notebook: str
    closing: str
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
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
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
        clone.paragraphs = [[]]
        clone.fired = set(self.fired)
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


def _r_clue_excites(world: World) -> list[str]:
    clue = world.get("clue")
    detective = world.get("detective")
    room = world.get("room")
    if clue.meters["seen"] < THRESHOLD:
        return []
    sig = ("clue_excites",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    detective.memes["curiosity"] += 1
    room.meters["mystery"] += 1
    return []


def _r_clear_by_track(world: World) -> list[str]:
    out: list[str] = []
    clue = world.get("clue")
    clue_track = clue.attrs.get("track", "")
    for suspect in world.facts.get("suspects", []):
        if suspect.meters["questioned"] < THRESHOLD:
            continue
        if suspect.attrs.get("track") == clue_track:
            continue
        sig = ("clear_track", suspect.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        suspect.meters["cleared"] += 1
        out.append(suspect.id)
    return out


def _r_clear_by_motive(world: World) -> list[str]:
    out: list[str] = []
    item = world.get("item")
    item_cat = item.attrs.get("category", "")
    for suspect in world.facts.get("suspects", []):
        if suspect.meters["questioned"] < THRESHOLD:
            continue
        if item_cat in suspect.attrs.get("likes", set()):
            continue
        sig = ("clear_motive", suspect.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        suspect.meters["cleared"] += 1
        out.append(suspect.id)
    return out


def _r_identify(world: World) -> list[str]:
    suspects = world.facts.get("suspects", [])
    remaining = [s for s in suspects if s.meters["questioned"] >= THRESHOLD and s.meters["cleared"] < THRESHOLD]
    if len(remaining) != 1:
        return []
    chosen = remaining[0]
    sig = ("identify", chosen.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    chosen.meters["likely"] += 1
    world.get("detective").memes["confidence"] += 1
    world.facts["identified"] = chosen.id
    return []


def _r_find_item(world: World) -> list[str]:
    item = world.get("item")
    if item.meters["searched"] < THRESHOLD:
        return []
    culprit_id = world.facts.get("culprit_id", "")
    if not culprit_id:
        return []
    sig = ("find", culprit_id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    item.meters["found"] += 1
    world.get("detective").memes["relief"] += 1
    world.get("detective").memes["pride"] += 1
    culprit = world.get(culprit_id)
    culprit.memes["caught"] += 1
    return []


CAUSAL_RULES = [
    Rule(name="clue_excites", tag="emotional", apply=_r_clue_excites),
    Rule(name="clear_by_track", tag="logic", apply=_r_clear_by_track),
    Rule(name="clear_by_motive", tag="logic", apply=_r_clear_by_motive),
    Rule(name="identify", tag="logic", apply=_r_identify),
    Rule(name="find_item", tag="physical", apply=_r_find_item),
]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
        changed = False
        for rule in CAUSAL_RULES:
            bits = rule.apply(world)
            if bits:
                changed = True
                produced.extend(bits)
    if narrate:
        for line in produced:
            if line:
                world.say(line)
    return produced


def plausible_combo(place: Place, material: Material, item: ItemCfg, culprit: CulpritCfg) -> bool:
    return (
        material.id in place.material_ids
        and culprit.id in place.visitors
        and item.category in culprit.likes
        and item.size in culprit.can_carry
        and culprit.id in place.spots
    )


def valid_combos() -> list[tuple[str, str, str, str]]:
    combos: list[tuple[str, str, str, str]] = []
    for place_id, place in PLACES.items():
        for material_id, material in MATERIALS.items():
            for item_id, item in ITEMS.items():
                for culprit_id, culprit in CULPRITS.items():
                    if plausible_combo(place, material, item, culprit):
                        combos.append((place_id, material_id, item_id, culprit_id))
    return combos


def explain_rejection(place: Place, material: Material, item: ItemCfg, culprit: CulpritCfg) -> str:
    if material.id not in place.material_ids:
        return (
            f"(No story: {place.label} has no honest source for {material.label}. "
            f"A detective clue should come from something really there.)"
        )
    if culprit.id not in place.visitors:
        return (
            f"(No story: {culprit.label} does not belong in {place.label} here, "
            f"so the suspect list would be unfair.)"
        )
    if item.category not in culprit.likes:
        return (
            f"(No story: {culprit.label} has no good reason to take the {item.label}. "
            f"The mystery needs a believable motive.)"
        )
    if item.size not in culprit.can_carry:
        return (
            f"(No story: {culprit.label} could not carry something as {item.size} as the {item.label}.)"
        )
    if culprit.id not in place.spots:
        return (
            f"(No story: {culprit.label} has no plausible hiding spot in {place.label}.)"
        )
    return "(No story: this combination is not reasonable.)"


def predict_case(place: Place, material: Material, item: ItemCfg, culprit: CulpritCfg) -> dict:
    return {
        "clue_material": material.label,
        "track": culprit.track,
        "hiding_spot": place.spots[culprit.id],
        "motive": culprit.motive,
        "solvable": plausible_combo(place, material, item, culprit),
    }


def introduce(world: World, detective: Entity, helper: Entity, style: DetectiveStyle, item: ItemCfg) -> None:
    detective.memes["joy"] += 1
    helper.memes["trust"] += 1
    world.say(
        f"{style.opener} {detective.id} liked to solve tiny mysteries before snack time, "
        f"and {helper.id} was the first and most loyal helper."
    )
    world.say(
        f"That morning they were in {world.place.label}. {world.place.opening} "
        f"On a small table sat {item.phrase}, ready for the day."
    )


def disappearance(world: World, detective: Entity, helper: Entity, item_ent: Entity) -> None:
    item_ent.meters["missing"] += 1
    world.say(
        f"Then the room changed. {helper.id} blinked, pointed, and whispered, "
        f'"Detective, the {item_ent.label} is gone."'
    )
    world.say(
        f"{detective.id} did not shout. {detective.pronoun().capitalize()} put one hand on "
        f"{detective.pronoun('possessive')} little notebook and looked slowly around the room."
    )


def discover_clue(world: World, detective: Entity, helper: Entity, material: Material, culprit: CulpritCfg) -> None:
    clue = world.get("clue")
    clue.meters["seen"] += 1
    clue.attrs["material"] = material.id
    clue.attrs["track"] = culprit.track
    clue.attrs["texture"] = material.texture
    propagate(world, narrate=False)
    world.say(
        f"By the table they found a {material.texture}, gooshy smear of {material.label}, "
        f"with {culprit.track_phrase} pressed right through it."
    )
    world.say(
        f'"A clue," said {detective.id}. "{material.source.capitalize()} made the smear, '
        f"and the tracks tell us who walked away."
    )


def suspect_round(world: World, detective: Entity, helper: Entity) -> None:
    suspects = world.facts.get("suspects", [])
    labels = ", ".join(s.label for s in suspects[:-1]) + f", and {suspects[-1].label}" if len(suspects) > 2 else " and ".join(s.label for s in suspects)
    world.say(
        f"In {world.place.label}, there were three possible suspects: {labels}. "
        f"{helper.id} held {detective.id}'s notebook while the little detective thought."
    )
    for suspect in suspects:
        suspect.meters["questioned"] += 1
    propagate(world, narrate=False)

    cleared = [s for s in suspects if s.meters["cleared"] >= THRESHOLD]
    kept = [s for s in suspects if s.meters["cleared"] < THRESHOLD]
    if cleared:
        clear_bits = []
        for suspect in cleared:
            reasons = []
            if suspect.attrs.get("track") != world.get("clue").attrs.get("track"):
                reasons.append("the tracks did not match")
            item_cat = world.get("item").attrs.get("category", "")
            if item_cat not in suspect.attrs.get("likes", set()):
                reasons.append(f"{suspect.pronoun()} did not want that kind of thing")
            reason = " and ".join(reasons)
            clear_bits.append(f"{suspect.label} was crossed off because {reason}")
        world.say("First, " + "; ".join(clear_bits) + ".")
    if len(kept) == 1:
        likely = kept[0]
        world.say(
            f"Only {likely.label} still fit every clue. {detective.id} tapped the notebook once. "
            f'"We do not need guessing anymore," {detective.pronoun()} said. '
            f'"Now we need searching."'
        )


def hunt(world: World, detective: Entity, helper: Entity, place: Place, culprit: CulpritCfg) -> None:
    spot = place.spots[culprit.id]
    world.get("item").meters["searched"] += 1
    propagate(world, narrate=False)
    world.say(
        f"The {culprit.track_phrase} led past the cupboard and into {spot}. "
        f"{helper.id} gasped and pointed with one careful finger."
    )


def reveal(world: World, detective: Entity, helper: Entity, culprit: CulpritCfg, item: ItemCfg) -> None:
    item_ent = world.get("item")
    culprit_ent = world.get(culprit.id)
    place = world.place
    world.say(
        f"There was {culprit.label}, curled beside the missing {item.label}. "
        f"{culprit_ent.pronoun('possessive').capitalize()} face looked surprised, as if {culprit_ent.pronoun()} had not expected a detective to come so quickly."
    )
    world.say(
        f'"Case solved," said {detective.id}. "{culprit.label.capitalize()} took the {item.label} because {culprit.motive}, '
        f'and the {MATERIALS[world.facts["material_id"]].label} told us where to look."'
    )
    culprit_ent.memes["sorry"] += 1
    item_ent.meters["returned"] += 1


def resolution(world: World, detective: Entity, helper: Entity, adult: Entity, item: ItemCfg, style: DetectiveStyle) -> None:
    item_ent = world.get("item")
    detective.memes["calm"] += 1
    helper.memes["joy"] += 1
    adult.memes["relief"] += 1
    world.say(
        f"{adult.label_word.capitalize()} wiped the {item.label} clean, set it back in its place, "
        f"and thanked the two detectives for thinking before rushing."
    )
    world.say(
        f"To stop the next mystery before it started, they moved the {item.label} higher and covered the messy source. "
        f"{style.closing}"
    )
@dataclass
class StoryParams:
    place: str
    material: str
    item: str
    culprit: str
    detective_name: str
    detective_type: str
    helper_name: str
    helper_type: str
    adult: str
    style: str = "classic"
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
    "jam": [
        (
            "What is jam?",
            "Jam is fruit that has been cooked with sugar until it turns soft and spreadable. It can feel sticky and messy if it gets on a floor."
        )
    ],
    "mud": [
        (
            "What is mud?",
            "Mud is wet dirt. It feels soft and squishy, and it can keep the shape of a footprint for a little while."
        )
    ],
    "glue": [
        (
            "Why does glue make a good clue?",
            "Glue is sticky, so it can hold the shape of a little print or smudge. That makes it easier to see who touched it."
        )
    ],
    "pawprint": [
        (
            "What is a pawprint?",
            "A pawprint is the mark an animal's foot leaves behind. Detectives can use pawprints the way they use tiny maps."
        )
    ],
    "bootprint": [
        (
            "What is a boot print?",
            "A boot print is the mark a shoe or boot leaves on the ground. If the sole has a pattern, that pattern can help identify who walked there."
        )
    ],
    "claw": [
        (
            "What can claw marks tell you?",
            "Claw marks can show that a bird or a small animal was there. They are helpful because they do not look like round pawprints or shoe prints."
        )
    ],
    "mystery": [
        (
            "How does a detective solve a mystery?",
            "A detective looks for clues, asks what fits, and crosses off what does not fit. Good problem solving means using reasons, not just guessing."
        )
    ],
}
KNOWLEDGE_ORDER = ["mystery", "jam", "mud", "glue", "pawprint", "bootprint", "claw"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    detective = f["detective"]
    helper = f["helper"]
    place = f["place_cfg"]
    item = f["item_cfg"]
    material = f["material_cfg"]
    return [
        f'Write a gentle detective story for a 3-to-5-year-old that includes the word "gooshy" and takes place in {place.label}.',
        f"Tell a problem-solving mystery where {detective.id} and {helper.id} notice a missing {item.label}, follow a {material.label} clue, and solve the case by reasoning.",
        f"Write a child-facing detective tale where a small clue leads to a missing object, and the ending shows how the characters prevent the problem next time.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    detective = f["detective"]
    helper = f["helper"]
    adult = f["adult"]
    place = f["place_cfg"]
    item = f["item_cfg"]
    material = f["material_cfg"]
    culprit = f["culprit_cfg"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {detective.id}, a little detective, and {helper.id}, the helper who stayed close beside {detective.pronoun('object')}. They were in {place.label} when the mystery began."
        ),
        (
            f"What was missing?",
            f"The missing thing was the {item.label}. It disappeared from the table, which is what turned an ordinary moment into a case."
        ),
        (
            "What clue did they find?",
            f"They found a {material.texture}, gooshy smear of {material.label} with {culprit.track_phrase} in it. The clue mattered because the messy smear came from a real source in the room and the tracks narrowed the suspect list."
        ),
        (
            f"How did {detective.id} solve the mystery?",
            f"{detective.id} compared the tracks and the stolen thing with each suspect instead of guessing. That let {detective.pronoun('object')} cross off the wrong suspects and search exactly in {f['hiding_spot']}."
        ),
        (
            f"Who took the {item.label}, and why?",
            f"{culprit.label.capitalize()} took it. {culprit.motive.capitalize()}, so the clue, the motive, and the hiding place all pointed to the same answer."
        ),
        (
            "How did the story end?",
            f"The missing {item.label} was found and put back, and the grown-up thanked the children for thinking carefully. Then they moved things around so the next mystery would be harder to start."
        ),
    ]
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags = {"mystery"} | set(f["material_cfg"].tags) | set(f["culprit_cfg"].tags)
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
        if e.attrs:
            shown = {}
            for k, v in e.attrs.items():
                if isinstance(v, set):
                    shown[k] = sorted(v)
                elif v:
                    shown[k] = v
            if shown:
                bits.append(f"attrs={shown}")
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        lines.append(f"  {e.id:12} ({e.type:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        place="kitchen",
        material="jam",
        item="sandwich",
        culprit="puppy",
        detective_name="Nora",
        detective_type="girl",
        helper_name="Ben",
        helper_type="boy",
        adult="mother",
        style="classic",
    ),
    StoryParams(
        place="garden",
        material="mud",
        item="seed_packet",
        culprit="squirrel",
        detective_name="Mia",
        detective_type="girl",
        helper_name="Leo",
        helper_type="boy",
        adult="father",
        style="classic",
    ),
    StoryParams(
        place="craft_room",
        material="glue",
        item="gold_star_sheet",
        culprit="toddler",
        detective_name="Lucy",
        detective_type="girl",
        helper_name="Max",
        helper_type="boy",
        adult="mother",
        style="classic",
    ),
    StoryParams(
        place="kitchen",
        material="jam",
        item="gold_star_sheet",
        culprit="toddler",
        detective_name="Ava",
        detective_type="girl",
        helper_name="Finn",
        helper_type="boy",
        adult="father",
        style="classic",
    ),
    StoryParams(
        place="craft_room",
        material="glue",
        item="sandwich",
        culprit="puppy",
        detective_name="Ruby",
        detective_type="girl",
        helper_name="Sam",
        helper_type="boy",
        adult="mother",
        style="classic",
    ),
]


ASP_RULES = r"""
valid(P,M,I,C) :- place(P), material(M), item(I), culprit(C),
                  has_material(P,M), visits(P,C), likes(C,Cat), category(I,Cat),
                  carries(C,Sz), size(I,Sz), spot(P,C).

#show valid/4.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for pid in PLACES:
        lines.append(asp.fact("place", pid))
    for pid, place in PLACES.items():
        for mid in sorted(place.material_ids):
            lines.append(asp.fact("has_material", pid, mid))
        for cid in sorted(place.visitors):
            lines.append(asp.fact("visits", pid, cid))
        for cid in sorted(place.spots):
            lines.append(asp.fact("spot", pid, cid))
    for mid in MATERIALS:
        lines.append(asp.fact("material", mid))
    for iid, item in ITEMS.items():
        lines.append(asp.fact("item", iid))
        lines.append(asp.fact("category", iid, item.category))
        lines.append(asp.fact("size", iid, item.size))
    for cid, culprit in CULPRITS.items():
        lines.append(asp.fact("culprit", cid))
        for cat in sorted(culprit.likes):
            lines.append(asp.fact("likes", cid, cat))
        for sz in sorted(culprit.can_carry):
            lines.append(asp.fact("carries", cid, sz))
    return "\n".join(lines)


def asp_program(extra: str = "") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program())
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    rc = 0
    python_set = set(valid_combos())
    clingo_set = set(asp_valid_combos())
    if python_set == clingo_set:
        print(f"OK: ASP gate matches valid_combos() ({len(python_set)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos:")
        if python_set - clingo_set:
            print("  only in python:", sorted(python_set - clingo_set))
        if clingo_set - python_set:
            print("  only in clingo:", sorted(clingo_set - python_set))

    smoke_params = CURATED[0]
    try:
        sample = generate(smoke_params)
        if not sample.story.strip():
            raise StoryError("smoke test produced an empty story")
        emit(sample, trace=False, qa=False, header="### smoke test")
        print("OK: smoke test generation succeeded.")
    except Exception as exc:
        rc = 1
        print(f"SMOKE TEST FAILED: {exc}")

    rng = random.Random(123)
    try:
        params = resolve_params(build_parser().parse_args([]), rng)
        params.seed = 123
        sample = generate(params)
        if not sample.story.strip():
            raise StoryError("default resolve/generate produced an empty story")
        print("OK: default resolve/generate succeeded.")
    except Exception as exc:
        rc = 1
        print(f"DEFAULT GENERATION FAILED: {exc}")

    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="A tiny detective storyworld about solving a gooshy mystery."
    )
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--material", choices=MATERIALS)
    ap.add_argument("--item", choices=ITEMS)
    ap.add_argument("--culprit", choices=CULPRITS)
    ap.add_argument("--adult", choices=["mother", "father"])
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list compatible combos from clingo")
    ap.add_argument("--verify", action="store_true", help="check ASP parity and smoke-test generation")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def _pick_name(rng: random.Random, gender: str, avoid: str = "") -> str:
    pool = GIRL_NAMES if gender == "girl" else BOY_NAMES
    choices = [n for n in pool if n != avoid]
    return rng.choice(choices)


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    place_id = args.place
    material_id = args.material
    item_id = args.item
    culprit_id = args.culprit

    if place_id and material_id and item_id and culprit_id:
        if not plausible_combo(PLACES[place_id], MATERIALS[material_id], ITEMS[item_id], CULPRITS[culprit_id]):
            raise StoryError(explain_rejection(PLACES[place_id], MATERIALS[material_id], ITEMS[item_id], CULPRITS[culprit_id]))

    combos = [
        combo
        for combo in valid_combos()
        if (place_id is None or combo[0] == place_id)
        and (material_id is None or combo[1] == material_id)
        and (item_id is None or combo[2] == item_id)
        and (culprit_id is None or combo[3] == culprit_id)
    ]
    if not combos:
        if place_id and material_id and item_id and culprit_id:
            raise StoryError(explain_rejection(PLACES[place_id], MATERIALS[material_id], ITEMS[item_id], CULPRITS[culprit_id]))
        raise StoryError("(No valid combination matches the given options.)")

    place_id, material_id, item_id, culprit_id = rng.choice(sorted(combos))
    detective_type = rng.choice(["girl", "boy"])
    helper_type = "boy" if detective_type == "girl" else "girl"
    detective_name = _pick_name(rng, detective_type)
    helper_name = _pick_name(rng, helper_type, avoid=detective_name)
    adult = args.adult or rng.choice(["mother", "father"])

    return StoryParams(
        place=place_id,
        material=material_id,
        item=item_id,
        culprit=culprit_id,
        detective_name=detective_name,
        detective_type=detective_type,
        helper_name=helper_name,
        helper_type=helper_type,
        adult=adult,
        style="classic",
    )


def generate(params: StoryParams) -> StorySample:
    if params.place not in PLACES:
        raise StoryError(f"(Unknown place: {params.place})")
    if params.material not in MATERIALS:
        raise StoryError(f"(Unknown material: {params.material})")
    if params.item not in ITEMS:
        raise StoryError(f"(Unknown item: {params.item})")
    if params.culprit not in CULPRITS:
        raise StoryError(f"(Unknown culprit: {params.culprit})")
    if params.style not in STYLES:
        raise StoryError(f"(Unknown style: {params.style})")
    if params.adult not in {"mother", "father"}:
        raise StoryError(f"(Unknown adult type: {params.adult})")

    place = PLACES[params.place]
    material = MATERIALS[params.material]
    item = ITEMS[params.item]
    culprit = CULPRITS[params.culprit]
    if not plausible_combo(place, material, item, culprit):
        raise StoryError(explain_rejection(place, material, item, culprit))

    world = tell(
        place=place,
        material=material,
        item=item,
        culprit=culprit,
        style=STYLES[params.style],
        detective_name=params.detective_name,
        detective_type=params.detective_type,
        helper_name=params.helper_name,
        helper_type=params.helper_type,
        adult_type=params.adult,
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
        print(asp_program())
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (place, material, item, culprit) combos:\n")
        for place, material, item, culprit in combos:
            print(f"  {place:10} {material:8} {item:15} {culprit}")
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
            header = f"### {p.detective_name}: {p.item} in {p.place} ({p.material}, {p.culprit})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")






def tell(
    place: Place,
    material: Material,
    item: ItemCfg,
    culprit: CulpritCfg,
    style: DetectiveStyle,
    detective_name: str = "Nora",
    detective_type: str = "girl",
    helper_name: str = "Ben",
    helper_type: str = "boy",
    adult_type: str = "mother",
) -> World:
    world = World(place)
    detective = world.add(Entity(id=detective_name, kind="character", type=detective_type, role="detective", label=detective_name))
    helper = world.add(Entity(id=helper_name, kind="character", type=helper_type, role="helper", label=helper_name))
    adult = world.add(Entity(id="Adult", kind="character", type=adult_type, role="adult", label="the grown-up"))
    room = world.add(Entity(id="room", type="room", label=place.label))
    item_ent = world.add(Entity(id="item", type=item.category, label=item.label, attrs={"category": item.category, "size": item.size}))
    clue = world.add(Entity(id="clue", type="clue", label="clue", attrs={"material": "", "track": "", "texture": ""}))

    suspects: list[Entity] = []
    for sid in SUSPECT_SETS[place.id]:
        cfg = CULPRITS[sid]
        suspects.append(
            world.add(
                Entity(
                    id=cfg.id,
                    type=cfg.type,
                    label=cfg.label,
                    role="suspect",
                    attrs={"track": cfg.track, "likes": set(cfg.likes)},
                    tags=set(cfg.tags),
                )
            )
        )

    world.facts["suspects"] = suspects
    world.facts["culprit_id"] = culprit.id
    world.facts["material_id"] = material.id
    world.facts["spot"] = place.spots[culprit.id]
    world.facts["style"] = style
    world.facts["predicted"] = predict_case(place, material, item, culprit)

    introduce(world, detective, helper, style, item)
    world.para()
    disappearance(world, detective, helper, item_ent)
    discover_clue(world, detective, helper, material, culprit)
    world.para()
    suspect_round(world, detective, helper)
    hunt(world, detective, helper, place, culprit)
    world.para()
    reveal(world, detective, helper, culprit, item)
    resolution(world, detective, helper, adult, item, style)

    world.facts.update(
        detective=detective,
        helper=helper,
        adult=adult,
        place_cfg=place,
        material_cfg=material,
        item_cfg=item,
        culprit_cfg=culprit,
        solved=world.get("item").meters["found"] >= THRESHOLD,
        returned=world.get("item").meters["returned"] >= THRESHOLD,
        culprit_label=culprit.label,
        clue_track=culprit.track_phrase,
        clue_material=material.label,
        hiding_spot=place.spots[culprit.id],
    )
    return world


PLACES = {
    "kitchen": Place(
        id="kitchen",
        label="the kitchen",
        opening="Sunlight sat in yellow squares on the floor, and a strawberry jar had been left open after breakfast.",
        nook="under the table",
        material_ids={"jam"},
        visitors={"puppy", "crow", "toddler"},
        spots={"puppy": "the shadow under the table", "crow": "the low window ledge behind the curtain", "toddler": "the chair with the apron hanging over it"},
        tags={"kitchen"},
    ),
    "garden": Place(
        id="garden",
        label="the garden shed",
        opening="Little pots lined the wall, and a shallow tray of rainwater had turned the floor muddy by the door.",
        nook="behind the watering can",
        material_ids={"mud"},
        visitors={"squirrel", "crow", "toddler"},
        spots={"squirrel": "the corner behind the watering can", "crow": "the shelf by the open window", "toddler": "the crate beside the seed bags"},
        tags={"garden"},
    ),
    "craft_room": Place(
        id="craft_room",
        label="the craft room",
        opening="Paper stars hung from a string, and a pot of paste sat open beside the scissors.",
        nook="under the easel",
        material_ids={"glue"},
        visitors={"toddler", "puppy", "crow"},
        spots={"toddler": "the blanket fort under the easel", "puppy": "the cushion by the paint shelf", "crow": "the top of the cubby by the window"},
        tags={"craft"},
    ),
}

MATERIALS = {
    "jam": Material(
        id="jam",
        label="jam",
        phrase="a little red smear of jam",
        texture="sticky",
        source="the strawberry jar on the counter",
        tags={"jam", "gooshy"},
    ),
    "mud": Material(
        id="mud",
        label="mud",
        phrase="a soft brown smear of mud",
        texture="squishy",
        source="the muddy tray by the shed door",
        tags={"mud", "gooshy"},
    ),
    "glue": Material(
        id="glue",
        label="paste",
        phrase="a pale blob of paste",
        texture="gooshy",
        source="the open paste pot on the craft table",
        tags={"glue", "gooshy"},
    ),
}

ITEMS = {
    "sandwich": ItemCfg(
        id="sandwich",
        label="sandwich",
        phrase="a neat triangle sandwich",
        category="snack",
        size="small",
        tags={"snack"},
    ),
    "seed_packet": ItemCfg(
        id="seed_packet",
        label="seed packet",
        phrase="a paper seed packet with a sunflower on the front",
        category="seeds",
        size="small",
        tags={"seeds"},
    ),
    "gold_star_sheet": ItemCfg(
        id="gold_star_sheet",
        label="gold star sheet",
        phrase="a shiny sheet of gold star stickers",
        category="shiny",
        size="flat",
        tags={"stickers", "shiny"},
    ),
}

CULPRITS = {
    "puppy": CulpritCfg(
        id="puppy",
        label="the puppy",
        type="animal",
        track="paw",
        track_phrase="round pawprints",
        motive="it smelled like lunch",
        likes={"snack"},
        can_carry={"small", "flat"},
        tags={"dog", "pawprint"},
    ),
    "squirrel": CulpritCfg(
        id="squirrel",
        label="the squirrel",
        type="animal",
        track="claw",
        track_phrase="tiny claw marks",
        motive="it wanted something to nibble or hide",
        likes={"seeds"},
        can_carry={"small"},
        tags={"squirrel", "claw"},
    ),
    "crow": CulpritCfg(
        id="crow",
        label="the crow",
        type="animal",
        track="claw",
        track_phrase="sharp birdy claw marks",
        motive="it liked things that flashed and shone",
        likes={"shiny"},
        can_carry={"small", "flat"},
        tags={"crow", "claw"},
    ),
    "toddler": CulpritCfg(
        id="toddler",
        label="the little brother",
        type="boy",
        track="boot",
        track_phrase="tiny boot prints",
        motive="he wanted to play with it himself",
        likes={"shiny", "snack"},
        can_carry={"small", "flat"},
        tags={"sibling", "bootprint"},
    ),
}

STYLES = {
    "classic": DetectiveStyle(
        id="classic",
        opener="On mystery mornings, the world always seemed to whisper first.",
        notebook="little notebook",
        closing="The casebook clicked shut, and the room no longer felt mysterious at all.",
    ),
}

SUSPECT_SETS = {
    "kitchen": ["puppy", "crow", "toddler"],
    "garden": ["squirrel", "crow", "toddler"],
    "craft_room": ["toddler", "puppy", "crow"],
}

GIRL_NAMES = ["Nora", "Lily", "Mia", "Ava", "Lucy", "Ruby"]
BOY_NAMES = ["Ben", "Max", "Theo", "Sam", "Leo", "Finn"]

if __name__ == "__main__":
    main()

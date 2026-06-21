#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/common_expression_friendship_teamwork_dialogue_rhyming_story.py
================================================================================================

A standalone storyworld for a small rhyming tale about friendship, teamwork,
and a handmade banner. Two friends prepare a cheerful banner for a school
moment, a hurried lift makes the banner sag or tear, and working together turns
the problem into a proud ending.

The required seed words appear naturally in the prose:
- common
- expression

The world models:
- physical meters: strain, torn, droop, steady, held, trimmed
- emotional memes: joy, worry, trust, pride, together, hurry, relief

The key reasonableness rule:
- not every support method fits every material
- some places are breezier than others
- a banner's size and material set how much help it needs

A declarative ASP twin mirrors the Python gate and outcome model.

Run it
------
python storyworlds/worlds/gpt-5.4/common_expression_friendship_teamwork_dialogue_rhyming_story.py
python storyworlds/worlds/gpt-5.4/common_expression_friendship_teamwork_dialogue_rhyming_story.py -n 5 --seed 7 --qa
python storyworlds/worlds/gpt-5.4/common_expression_friendship_teamwork_dialogue_rhyming_story.py --all
python storyworlds/worlds/gpt-5.4/common_expression_friendship_teamwork_dialogue_rhyming_story.py --json
python storyworlds/worlds/gpt-5.4/common_expression_friendship_teamwork_dialogue_rhyming_story.py --asp
python storyworlds/worlds/gpt-5.4/common_expression_friendship_teamwork_dialogue_rhyming_story.py --verify
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

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from results import QAItem, StoryError, StorySample  # noqa: E402

THRESHOLD = 1.0


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
    tags: set[str] = field(default_factory=set)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "teacher_woman", "woman"}
        male = {"boy", "father", "teacher_man", "man"}
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
            "teacher_woman": "teacher",
            "teacher_man": "teacher",
        }.get(self.type, self.type)


@dataclass
class Place:
    id: str
    label: str
    breeze: int
    line: str
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
    strength: int
    texture: str
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
class Size:
    id: str
    label: str
    weight: int
    line: str
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
class Support:
    id: str
    label: str
    power: int
    materials: set[str]
    apply_text: str
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


@dataclass
class Art:
    id: str
    label: str
    face_line: str
    ending_line: str
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
        return [e for e in self.entities.values() if e.role in {"lead", "friend"}]

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


def required_support(place: Place, material: Material, size: Size) -> int:
    return max(1, 1 + place.breeze + size.weight - material.strength)


def support_fits(material: Material, support: Support) -> bool:
    return material.id in support.materials


def predicted_outcome(place: Place, material: Material, size: Size, support: Support) -> str:
    if not support_fits(material, support):
        return "invalid"
    need = required_support(place, material, size)
    return "saved" if support.power >= need else "remade"


def valid_combos() -> list[tuple[str, str, str, str]]:
    combos: list[tuple[str, str, str, str]] = []
    for place_id, place in PLACES.items():
        for material_id, material in MATERIALS.items():
            for size_id, size in SIZES.items():
                for support_id, support in SUPPORTS.items():
                    if support_fits(material, support):
                        combos.append((place_id, material_id, size_id, support_id))
    return combos


def _r_slip(world: World) -> list[str]:
    banner = world.get("banner")
    if banner.meters["held"] < THRESHOLD:
        return []
    if banner.attrs.get("team_hands", 0) >= 2:
        return []
    sig = ("slip",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    need = world.facts["need"]
    if need >= 2:
        banner.meters["strain"] += 1
        if need >= 3:
            banner.meters["torn"] += 1
        else:
            banner.meters["droop"] += 1
        for kid in world.kids():
            kid.memes["worry"] += 1
        return ["__slip__"]
    banner.meters["droop"] += 1
    for kid in world.kids():
        kid.memes["worry"] += 1
    return ["__slip__"]


def _r_steady(world: World) -> list[str]:
    banner = world.get("banner")
    if banner.meters["held"] < THRESHOLD:
        return []
    if banner.attrs.get("team_hands", 0) < 2:
        return []
    if banner.attrs.get("support_power", 0) < world.facts["need"]:
        return []
    sig = ("steady",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    banner.meters["steady"] += 1
    banner.meters["droop"] = 0.0
    for kid in world.kids():
        kid.memes["pride"] += 1
        kid.memes["relief"] += 1
        kid.memes["together"] += 1
    return ["__steady__"]


CAUSAL_RULES: list[Rule] = [
    Rule(name="slip", tag="physical", apply=_r_slip),
    Rule(name="steady", tag="physical", apply=_r_steady),
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


def predict_banner(place: Place, material: Material, size: Size, support: Support) -> dict:
    return {
        "need": required_support(place, material, size),
        "fits": support_fits(material, support),
        "outcome": predicted_outcome(place, material, size, support),
    }


def introduce(world: World, lead: Entity, friend: Entity, place: Place, art: Art, size: Size) -> None:
    for kid in (lead, friend):
        kid.memes["joy"] += 1
        kid.memes["trust"] += 1
    world.say(
        f"In {place.label}, {lead.id} and {friend.id} had a plan for the day, "
        f"to make a friendship banner in a bright, bouncing way."
    )
    world.say(
        f"{place.line} They chose {size.line}, then laughed as scissors skipped in play."
    )
    world.say(
        f'"Let\'s make it lovely," said {lead.id}. "{art.label.capitalize()} can lead the way."'
    )


def teacher_line(world: World, teacher: Entity) -> None:
    world.say(
        f'Their {teacher.label_word} smiled and shared a common expression: '
        f'"Many hands make light work," {teacher.pronoun()} said, soft and kind and steady.'
    )


def paint_face(world: World, lead: Entity, friend: Entity, art: Art, material: Material) -> None:
    banner = world.get("banner")
    banner.meters["painted"] += 1
    world.say(
        f"Across the {material.texture} {material.label}, they brushed and bent and swirled, "
        f"and in the middle {art.face_line}"
    )
    world.say(
        f'"That {art.label} has the sweetest expression!" said {friend.id}. '
        f'"It looks ready for the world."'
    )


def hurry_lift(world: World, lead: Entity, size: Size) -> None:
    banner = world.get("banner")
    lead.memes["hurry"] += 1
    banner.meters["held"] += 1
    banner.attrs["team_hands"] = 1
    banner.attrs["support_power"] = 0
    propagate(world, narrate=False)
    if banner.meters["torn"] >= THRESHOLD:
        world.say(
            f'But {lead.id} grew eager. "I can lift it by myself!" {lead.pronoun()} cried. '
            f'The {size.label} banner gave a tug and made a tearing sound instead.'
        )
    else:
        world.say(
            f'But {lead.id} grew eager. "I can lift it by myself!" {lead.pronoun()} cried. '
            f'The {size.label} banner dipped and drooped as if it did not quite agree.'
        )


def worry_talk(world: World, friend: Entity, lead: Entity, teacher: Entity, place: Place, material: Material, size: Size) -> None:
    banner = world.get("banner")
    need = world.facts["need"]
    material_note = "thin" if material.strength <= 1 else "soft" if material.strength == 2 else "stiff"
    if banner.meters["torn"] >= THRESHOLD:
        world.say(
            f'"Oh no," said {friend.id}, "it tore because the {material_note} {material.label} '
            f'and {place.label} breeze asked for more help than one pair of hands could bring."'
        )
    else:
        world.say(
            f'"Wait," said {friend.id}, "it needs more help. The {place.label} air keeps nudging it, '
            f'and this {size.label} shape is a lot to swing."'
        )
    world.say(
        f'"Let us think together," said the {teacher.label_word}. '
        f'"Big things go best when friends pull steady string."'
    )
    world.facts["explained_need"] = need


def apply_support(world: World, lead: Entity, friend: Entity, support: Support) -> None:
    banner = world.get("banner")
    banner.attrs["team_hands"] = 2
    banner.attrs["support_power"] = support.power
    lead.memes["trust"] += 1
    friend.memes["trust"] += 1
    lead.memes["together"] += 1
    friend.memes["together"] += 1
    if banner.meters["torn"] >= THRESHOLD:
        world.say(
            f'Together they {support.apply_text}, then held the edges side by side. '
            f'"Ready?" asked {lead.id}. "Ready," said {friend.id}.'
        )
    else:
        world.say(
            f'Together they {support.apply_text}. "{friend.id}, take that corner." '
            f'"I will," said {friend.id}, and their hands made one calm line.'
        )
    propagate(world, narrate=False)


def ending_saved(world: World, lead: Entity, friend: Entity, teacher: Entity, art: Art, support: Support) -> None:
    banner = world.get("banner")
    banner.meters["shown"] += 1
    world.say(
        f"Up went the banner, smooth and bright, with not a wobble left in sight. "
        f"{art.ending_line}"
    )
    world.say(
        f'"You see?" said the {teacher.label_word}. "That common expression was true today." '
        f'"We made it together," said {lead.id}, and {friend.id} beamed, "Hip-hip-hooray!"'
    )
    world.facts["resolution_text"] = support.qa_text


def ending_remade(world: World, lead: Entity, friend: Entity, teacher: Entity, art: Art, support: Support) -> None:
    banner = world.get("banner")
    banner.meters["trimmed"] += 1
    for kid in (lead, friend):
        kid.memes["relief"] += 1
        kid.memes["pride"] += 1
    world.say(
        f"The big banner still flopped when they tried to raise it high, "
        f"so the {teacher.label_word} said, \"Let us be clever and not cry.\""
    )
    world.say(
        f"They trimmed it into two small pennants, one for each dear friend to hold, "
        f"and {art.ending_line.lower()} in colors brave and bold."
    )
    world.say(
        f'"Side by side is still a win," said {friend.id}. '
        f'"Yes," said {lead.id}, "together turns a torn-up try to gold."'
    )
    world.facts["resolution_text"] = (
        f"They could not save the big banner with {support.label}, so they remade it as two small pennants. "
        f"That new plan worked because each friend could carry one piece without the paper pulling apart."
    )


def tell(
    place: Place,
    material: Material,
    size: Size,
    support: Support,
    art: Art,
    lead_name: str = "Mia",
    lead_gender: str = "girl",
    friend_name: str = "Ben",
    friend_gender: str = "boy",
    teacher_type: str = "teacher_woman",
) -> World:
    world = World()
    need = required_support(place, material, size)

    lead = world.add(Entity(
        id=lead_name,
        kind="character",
        type=lead_gender,
        role="lead",
        label=lead_name,
        traits=["eager"],
        tags={"friendship"},
    ))
    friend = world.add(Entity(
        id=friend_name,
        kind="character",
        type=friend_gender,
        role="friend",
        label=friend_name,
        traits=["steady"],
        tags={"friendship"},
    ))
    teacher = world.add(Entity(
        id="Teacher",
        kind="character",
        type=teacher_type,
        role="teacher",
        label="the teacher",
        tags={"teacher"},
    ))
    banner = world.add(Entity(
        id="banner",
        kind="thing",
        type="banner",
        label="banner",
        phrase=f"{size.label} {material.label} banner",
        attrs={
            "team_hands": 0,
            "support_power": 0,
            "material": material.id,
            "size": size.id,
        },
        tags={"banner"} | set(material.tags) | set(size.tags),
    ))

    world.facts.update(
        place=place,
        material=material,
        size=size,
        support=support,
        art=art,
        lead=lead,
        friend=friend,
        teacher=teacher,
        banner=banner,
        need=need,
        support_fits=support_fits(material, support),
        outcome=predicted_outcome(place, material, size, support),
    )

    introduce(world, lead, friend, place, art, size)
    teacher_line(world, teacher)
    paint_face(world, lead, friend, art, material)

    world.para()
    hurry_lift(world, lead, size)
    worry_talk(world, friend, lead, teacher, place, material, size)

    world.para()
    apply_support(world, lead, friend, support)
    if world.facts["outcome"] == "saved":
        ending_saved(world, lead, friend, teacher, art, support)
    else:
        ending_remade(world, lead, friend, teacher, art, support)

    world.facts["damaged"] = banner.meters["torn"] >= THRESHOLD or banner.meters["droop"] >= THRESHOLD
    world.facts["steady"] = banner.meters["steady"] >= THRESHOLD
    return world


PLACES = {
    "classroom": Place(
        id="classroom",
        label="the classroom",
        breeze=0,
        line="Sunlight made long squares on the floor, and the glue caps clicked like tiny drums.",
        tags={"classroom"},
    ),
    "hallway": Place(
        id="hallway",
        label="the hallway",
        breeze=1,
        line="Shoes had swished there all morning, and the door at the end puffed little breaths of air.",
        tags={"hallway", "breeze"},
    ),
    "courtyard": Place(
        id="courtyard",
        label="the courtyard",
        breeze=2,
        line="A spring breeze skipped around the benches and tried to play tag with every loose corner.",
        tags={"courtyard", "breeze"},
    ),
}

MATERIALS = {
    "paper": Material(
        id="paper",
        label="paper",
        phrase="a big sheet of paper",
        strength=1,
        texture="crinkly",
        tags={"paper"},
    ),
    "fabric": Material(
        id="fabric",
        label="fabric",
        phrase="a square of soft fabric",
        strength=2,
        texture="soft",
        tags={"fabric"},
    ),
    "poster_board": Material(
        id="poster_board",
        label="poster board",
        phrase="a smooth piece of poster board",
        strength=3,
        texture="sturdy",
        tags={"poster_board"},
    ),
}

SIZES = {
    "small": Size(
        id="small",
        label="small",
        weight=1,
        line="a little banner, neat and gay",
        tags={"small"},
    ),
    "wide": Size(
        id="wide",
        label="wide",
        weight=2,
        line="a wide banner, grand enough to sway",
        tags={"wide"},
    ),
    "grand": Size(
        id="grand",
        label="grand",
        weight=3,
        line="a grand banner, broad enough to brighten half the day",
        tags={"grand"},
    ),
}

SUPPORTS = {
    "tape_border": Support(
        id="tape_border",
        label="a tape border",
        power=1,
        materials={"paper", "poster_board"},
        apply_text="smoothed a shiny tape border all around the edge",
        qa_text="They reinforced the edges with a tape border and then held the banner together.",
        tags={"tape"},
    ),
    "sewn_loops": Support(
        id="sewn_loops",
        label="sewn loops",
        power=2,
        materials={"fabric"},
        apply_text="stitched two little loops and slid their hands through them",
        qa_text="They added sewn loops so each friend could hold the fabric without twisting it.",
        tags={"sewing"},
    ),
    "stick_handles": Support(
        id="stick_handles",
        label="stick handles",
        power=3,
        materials={"paper", "fabric", "poster_board"},
        apply_text="taped light sticks to the sides to make handles",
        qa_text="They added stick handles, which gave the banner firmer edges and let both friends carry it evenly.",
        tags={"sticks"},
    ),
}

ARTS = {
    "sun": Art(
        id="sun",
        label="sun",
        face_line="they painted a round sun with rosy cheeks and a laughing expression that seemed to sing.",
        ending_line="The smiling sun bobbed above them like a happy golden ring.",
        tags={"sun"},
    ),
    "kite": Art(
        id="kite",
        label="kite",
        face_line="they painted a kite with bright eyes and an excited expression, as if it had heard the bell ring.",
        ending_line="The kite-face danced above them as light as string.",
        tags={"kite"},
    ),
    "flower": Art(
        id="flower",
        label="flower",
        face_line="they painted a flower with a gentle expression, all petal grin and springtime swing.",
        ending_line="The flower-face nodded softly, pink and bright as spring.",
        tags={"flower"},
    ),
}

GIRL_NAMES = ["Mia", "Lily", "Ava", "Nora", "Ruby", "Ella", "Zoe", "Anna"]
BOY_NAMES = ["Ben", "Leo", "Max", "Noah", "Finn", "Sam", "Eli", "Theo"]


@dataclass
class StoryParams:
    place: str
    material: str
    size: str
    support: str
    art: str
    lead_name: str
    lead_gender: str
    friend_name: str
    friend_gender: str
    teacher_type: str
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
        place="classroom",
        material="paper",
        size="small",
        support="tape_border",
        art="sun",
        lead_name="Mia",
        lead_gender="girl",
        friend_name="Ben",
        friend_gender="boy",
        teacher_type="teacher_woman",
    ),
    StoryParams(
        place="hallway",
        material="fabric",
        size="wide",
        support="sewn_loops",
        art="flower",
        lead_name="Leo",
        lead_gender="boy",
        friend_name="Ruby",
        friend_gender="girl",
        teacher_type="teacher_man",
    ),
    StoryParams(
        place="courtyard",
        material="paper",
        size="grand",
        support="stick_handles",
        art="kite",
        lead_name="Ava",
        lead_gender="girl",
        friend_name="Theo",
        friend_gender="boy",
        teacher_type="teacher_woman",
    ),
    StoryParams(
        place="courtyard",
        material="paper",
        size="grand",
        support="tape_border",
        art="sun",
        lead_name="Finn",
        lead_gender="boy",
        friend_name="Lily",
        friend_gender="girl",
        teacher_type="teacher_man",
    ),
    StoryParams(
        place="hallway",
        material="poster_board",
        size="wide",
        support="stick_handles",
        art="flower",
        lead_name="Nora",
        lead_gender="girl",
        friend_name="Sam",
        friend_gender="boy",
        teacher_type="teacher_woman",
    ),
]


KNOWLEDGE = {
    "banner": [
        (
            "What is a banner?",
            "A banner is a large sign or cloth with words or pictures on it. People hold it up so others can see a message from far away.",
        )
    ],
    "paper": [
        (
            "Why can paper tear?",
            "Paper bends easily, but if it is pulled too hard it can split. Big pieces of paper need gentle hands, especially in moving air.",
        )
    ],
    "fabric": [
        (
            "Why is fabric softer than poster board?",
            "Fabric is made of threads, so it bends and drapes softly. Poster board is stiff, so it keeps its shape better.",
        )
    ],
    "poster_board": [
        (
            "What is poster board good for?",
            "Poster board is thick paper that stays flatter than regular paper. That makes it useful for signs and school projects.",
        )
    ],
    "breeze": [
        (
            "Why does a breeze make a big sign hard to hold?",
            "A breeze pushes on the wide surface like a small invisible hand. The bigger the sign is, the more air can nudge it around.",
        )
    ],
    "tape": [
        (
            "What does tape do in a craft project?",
            "Tape helps hold edges together and can make weak corners a little stronger. It works best when the paper is not being pulled too hard.",
        )
    ],
    "sewing": [
        (
            "What are sewn loops for?",
            "Sewn loops make a cloth banner easier to grip. They give hands a steady place to hold without bunching the fabric too much.",
        )
    ],
    "sticks": [
        (
            "Why do stick handles help a banner?",
            "Stick handles make the edges firmer, so the banner twists less. They also let two people carry it evenly together.",
        )
    ],
    "friendship": [
        (
            "What does teamwork mean?",
            "Teamwork means people help each other do one job together. When friends share the work, the job can feel lighter and steadier.",
        )
    ],
    "expression": [
        (
            "What is an expression on a face?",
            "An expression is the look a face makes, like happy, worried, or surprised. Artists use expressions to show feelings in a picture.",
        )
    ],
    "classroom": [
        (
            "What do children often make in a classroom?",
            "Children often read, count, paint, and make crafts in a classroom. It is a place for learning and trying careful new things.",
        )
    ],
    "hallway": [
        (
            "Why can a hallway feel drafty?",
            "A hallway can feel drafty when doors open and close and air moves through. Even a small puff of air can wiggle light paper.",
        )
    ],
    "courtyard": [
        (
            "What is a courtyard?",
            "A courtyard is an open space beside or inside a building. Because it is outdoors, the wind can move through it more easily.",
        )
    ],
}
KNOWLEDGE_ORDER = [
    "friendship",
    "banner",
    "expression",
    "paper",
    "fabric",
    "poster_board",
    "breeze",
    "tape",
    "sewing",
    "sticks",
    "classroom",
    "hallway",
    "courtyard",
]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    lead = f["lead"]
    friend = f["friend"]
    place = f["place"]
    support = f["support"]
    art = f["art"]
    outcome = f["outcome"]
    if outcome == "saved":
        return [
            (
                f'Write a short rhyming story for ages 3 to 5 about friendship and teamwork. '
                f'Include the words "common" and "expression", a little dialogue, and a banner with a {art.label} on it.'
            ),
            (
                f"Tell a rhyming story where {lead.id} and {friend.id} make a big banner in {place.label}, "
                f"run into trouble when one child tries to lift it alone, and fix it together with {support.label}."
            ),
            (
                "Write a gentle poem-story where a teacher says a common expression about working together, "
                "and two friends prove it true by saving their craft."
            ),
        ]
    return [
        (
            f'Write a short rhyming story for ages 3 to 5 about friendship and teamwork. '
            f'Include the words "common" and "expression", a little dialogue, and a banner with a {art.label} on it.'
        ),
        (
            f"Tell a rhyming story where {lead.id} and {friend.id} make a large banner in {place.label}, "
            f"discover that their first repair is not strong enough, and then turn the project into a new shared success."
        ),
        (
            "Write a child-friendly rhyme tale where a common expression about teamwork comes true after a craft goes wrong "
            "and two friends change their plan together."
        ),
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    lead = f["lead"]
    friend = f["friend"]
    teacher = f["teacher"]
    place = f["place"]
    material = f["material"]
    size = f["size"]
    support = f["support"]
    art = f["art"]
    outcome = f["outcome"]
    need = f["need"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about two friends, {lead.id} and {friend.id}, making a friendship banner together. "
            f"Their {teacher.label_word} helps them slow down and think when the banner gives them trouble.",
        ),
        (
            "What did they make?",
            f"They made a {size.label} banner from {material.label} and painted a {art.label} on it. "
            f"The picture had a cheerful expression, which made the project feel warm and welcoming.",
        ),
        (
            f"Why did the banner bend or tear when {lead.id} lifted it alone?",
            f"It was too much for one child to hold by themself in {place.label}. "
            f"The banner needed about {need} level of support, and one hurried pair of hands could not keep it steady.",
        ),
        (
            "What common expression did the teacher say?",
            'The teacher said, "Many hands make light work." '
            "That saying fit the story because the banner only behaved once the friends shared the job.",
        ),
    ]
    if outcome == "saved":
        qa.append(
            (
                f"How did {lead.id} and {friend.id} solve the problem?",
                f"They worked together and used {support.label}. "
                f"{f['resolution_text']} That made the banner firm enough to rise without wobbling.",
            )
        )
        qa.append(
            (
                "How did the story end?",
                f"It ended happily with the banner lifted high and the smiling {art.label} shining above them. "
                f"The ending proves that friendship and teamwork changed a shaky craft into a proud display.",
            )
        )
    else:
        qa.append(
            (
                f"Did their first fix save the big banner?",
                f"No. {support.label.capitalize()} was not strong enough for that big project in {place.label}. "
                f"So they changed their plan instead of giving up.",
            )
        )
        qa.append(
            (
                "How did the friends finish the project?",
                f"They remade the banner into two small pennants and carried them side by side. "
                f"That worked because the new pieces were easier to hold, so the friends could still end in step and in pride.",
            )
        )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags = {"banner", "expression", "friendship"}
    tags |= set(f["place"].tags)
    tags |= set(f["material"].tags)
    tags |= set(f["support"].tags)
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
        bits = []
        if ent.role:
            bits.append(f"role={ent.role}")
        if ent.attrs:
            shown = {k: v for k, v in ent.attrs.items() if v or k in {"team_hands", "support_power"}}
            if shown:
                bits.append(f"attrs={shown}")
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        lines.append(f"  {ent.id:8} ({ent.type:12}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    lines.append(f"  facts: outcome={world.facts.get('outcome')} need={world.facts.get('need')}")
    return "\n".join(lines)


def explain_rejection(material: Material, support: Support) -> str:
    okay = ", ".join(sorted(sid for sid, sup in SUPPORTS.items() if material.id in sup.materials))
    return (
        f"(No story: {support.label} is not a sensible support for {material.label}. "
        f"Try one of: {okay}.)"
    )


ASP_RULES = r"""
fits(M, S) :- support(S), material(M), support_material(S, M).

need(P, M, Z, N) :- breeze(P, B), weight(Z, W), strength(M, St), N = 1 + B + W - St, N > 1.
need(P, M, Z, 1) :- breeze(P, B), weight(Z, W), strength(M, St), 1 + B + W - St <= 1.

valid(P, M, Z, S) :- place(P), material(M), size(Z), support(S), fits(M, S).

saved(P, M, Z, S) :- valid(P, M, Z, S), need(P, M, Z, N), power(S, Pw), Pw >= N.
remade(P, M, Z, S) :- valid(P, M, Z, S), need(P, M, Z, N), power(S, Pw), Pw < N.

outcome(saved) :- chosen(P, M, Z, S), saved(P, M, Z, S).
outcome(remade) :- chosen(P, M, Z, S), remade(P, M, Z, S).
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for place_id, place in PLACES.items():
        lines.append(asp.fact("place", place_id))
        lines.append(asp.fact("breeze", place_id, place.breeze))
    for material_id, material in MATERIALS.items():
        lines.append(asp.fact("material", material_id))
        lines.append(asp.fact("strength", material_id, material.strength))
    for size_id, size in SIZES.items():
        lines.append(asp.fact("size", size_id))
        lines.append(asp.fact("weight", size_id, size.weight))
    for support_id, support in SUPPORTS.items():
        lines.append(asp.fact("support", support_id))
        lines.append(asp.fact("power", support_id, support.power))
        for material_id in sorted(support.materials):
            lines.append(asp.fact("support_material", support_id, material_id))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("", "#show valid/4."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_outcome(params: StoryParams) -> str:
    import asp

    scenario = asp.fact("chosen", params.place, params.material, params.size, params.support)
    model = asp.one_model(asp_program(scenario, "#show outcome/1."))
    atoms = asp.atoms(model, "outcome")
    return atoms[0][0] if atoms else "?"


def outcome_of(params: StoryParams) -> str:
    for key, store in (
        (params.place, PLACES),
        (params.material, MATERIALS),
        (params.size, SIZES),
        (params.support, SUPPORTS),
    ):
        if key not in store:
            raise StoryError("(No story: unknown story parameter.)")
    place = PLACES[params.place]
    material = MATERIALS[params.material]
    size = SIZES[params.size]
    support = SUPPORTS[params.support]
    if not support_fits(material, support):
        raise StoryError(explain_rejection(material, support))
    return predicted_outcome(place, material, size, support)


def asp_verify() -> int:
    rc = 0
    py_valid = set(valid_combos())
    asp_valid = set(asp_valid_combos())
    if py_valid == asp_valid:
        print(f"OK: gate matches valid_combos() ({len(py_valid)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos:")
        if py_valid - asp_valid:
            print("  only in python:", sorted(py_valid - asp_valid))
        if asp_valid - py_valid:
            print("  only in clingo:", sorted(asp_valid - py_valid))

    cases = list(CURATED)
    for seed in range(50):
        try:
            params = resolve_params(build_parser().parse_args([]), random.Random(seed))
        except StoryError:
            continue
        params.seed = seed
        cases.append(params)

    bad = 0
    for params in cases:
        try:
            py = outcome_of(params)
        except StoryError:
            bad += 1
            continue
        asp = asp_outcome(params)
        if py != asp:
            bad += 1
            print(f"MISMATCH outcome: {params} python={py} asp={asp}")
    if bad == 0:
        print(f"OK: outcome model matches on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {bad} outcome cases differed.")

    try:
        sample = generate(CURATED[0])
        if not sample.story.strip():
            raise StoryError("Generated empty story during smoke test.")
        with contextlib.redirect_stdout(io.StringIO()):
            emit(sample, trace=True, qa=True, header="SMOKE")
        print("OK: smoke test generate()/emit() succeeded.")
    except Exception as err:
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Rhyming storyworld: two friends save a banner by working together."
    )
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--material", choices=MATERIALS)
    ap.add_argument("--size", choices=SIZES)
    ap.add_argument("--support", choices=SUPPORTS)
    ap.add_argument("--art", choices=ARTS)
    ap.add_argument("--teacher", choices=["teacher_woman", "teacher_man"])
    ap.add_argument("--lead-name")
    ap.add_argument("--lead-gender", choices=["girl", "boy"])
    ap.add_argument("--friend-name")
    ap.add_argument("--friend-gender", choices=["girl", "boy"])
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list compatible story combinations from clingo")
    ap.add_argument("--verify", action="store_true", help="check ASP/Python parity and run a smoke test")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def _pick_name(rng: random.Random, gender: str, avoid: str = "") -> str:
    pool = GIRL_NAMES if gender == "girl" else BOY_NAMES
    choices = [name for name in pool if name != avoid]
    return rng.choice(choices)


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.material and args.support:
        material = MATERIALS[args.material]
        support = SUPPORTS[args.support]
        if not support_fits(material, support):
            raise StoryError(explain_rejection(material, support))

    combos = [
        combo for combo in valid_combos()
        if (args.place is None or combo[0] == args.place)
        and (args.material is None or combo[1] == args.material)
        and (args.size is None or combo[2] == args.size)
        and (args.support is None or combo[3] == args.support)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    place_id, material_id, size_id, support_id = rng.choice(sorted(combos))
    art_id = args.art or rng.choice(sorted(ARTS))
    teacher_type = args.teacher or rng.choice(["teacher_woman", "teacher_man"])

    lead_gender = args.lead_gender or rng.choice(["girl", "boy"])
    friend_gender = args.friend_gender or rng.choice(["girl", "boy"])

    lead_name = args.lead_name or _pick_name(rng, lead_gender)
    friend_name = args.friend_name or _pick_name(rng, friend_gender, avoid=lead_name)

    return StoryParams(
        place=place_id,
        material=material_id,
        size=size_id,
        support=support_id,
        art=art_id,
        lead_name=lead_name,
        lead_gender=lead_gender,
        friend_name=friend_name,
        friend_gender=friend_gender,
        teacher_type=teacher_type,
    )


def generate(params: StoryParams) -> StorySample:
    for key, store in (
        (params.place, PLACES),
        (params.material, MATERIALS),
        (params.size, SIZES),
        (params.support, SUPPORTS),
        (params.art, ARTS),
    ):
        if key not in store:
            raise StoryError("(No story: unknown story parameter.)")
    material = MATERIALS[params.material]
    support = SUPPORTS[params.support]
    if not support_fits(material, support):
        raise StoryError(explain_rejection(material, support))

    world = tell(
        place=PLACES[params.place],
        material=material,
        size=SIZES[params.size],
        support=support,
        art=ARTS[params.art],
        lead_name=params.lead_name,
        lead_gender=params.lead_gender,
        friend_name=params.friend_name,
        friend_gender=params.friend_gender,
        teacher_type=params.teacher_type,
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
        print(f"{len(combos)} compatible (place, material, size, support) combos:\n")
        for place, material, size, support in combos:
            demo = StoryParams(
                place=place,
                material=material,
                size=size,
                support=support,
                art="sun",
                lead_name="Mia",
                lead_gender="girl",
                friend_name="Ben",
                friend_gender="boy",
                teacher_type="teacher_woman",
            )
            print(f"  {place:10} {material:12} {size:6} {support:13} -> {outcome_of(demo)}")
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
            print(json.dumps([sample.to_dict() for sample in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        header = ""
        if args.all:
            p = sample.params
            header = (
                f"### {p.lead_name} & {p.friend_name}: {p.material} {p.size} banner in "
                f"{p.place} with {p.support} ({outcome_of(p)})"
            )
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()

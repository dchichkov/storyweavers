#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/down_art_nimble_foreshadowing_heartwarming.py
=========================================================================

A standalone story world about a child making cheer-up art for someone who feels
down, with a nimble helper, a small foreshadowed display problem, and a warm
family ending.

The core reasonableness rule is physical and simple:

- an art project has a shape and a weight
- a display spot accepts only certain shapes and mounting styles
- a support method must fit the spot and be strong enough for the art

Only valid combinations are generated. Some valid combinations are very steady;
others produce a gentle near-accident when a draft makes the art begin to slip
down, which the helper notices and the family fixes together.

Run it
------
    python storyworlds/worlds/gpt-5.4/down_art_nimble_foreshadowing_heartwarming.py
    python storyworlds/worlds/gpt-5.4/down_art_nimble_foreshadowing_heartwarming.py --art collage --spot bedroom_wall
    python storyworlds/worlds/gpt-5.4/down_art_nimble_foreshadowing_heartwarming.py --art ribbon_mobile --spot fridge
    python storyworlds/worlds/gpt-5.4/down_art_nimble_foreshadowing_heartwarming.py --all
    python storyworlds/worlds/gpt-5.4/down_art_nimble_foreshadowing_heartwarming.py -n 5 --seed 7 --qa
    python storyworlds/worlds/gpt-5.4/down_art_nimble_foreshadowing_heartwarming.py --verify
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
        female = {"girl", "mother", "mom", "grandmother", "aunt", "woman"}
        male = {"boy", "father", "dad", "grandfather", "uncle", "man"}
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
            "grandmother": "grandma",
            "grandfather": "grandpa",
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
class ArtProject:
    id: str
    label: str
    phrase: str
    shape: str
    mount: str
    weight: int
    opening: str
    making: str
    detail: str
    fall_part: str
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
class DisplaySpot:
    id: str
    label: str
    phrase: str
    shape: str
    mount: str
    room: str
    anchor_bonus: int
    draftiness: int
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
class Support:
    id: str
    label: str
    phrase: str
    mount: str
    power: int
    fix_line: str
    qa_text: str
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
class RecipientMood:
    id: str
    who: str
    down_reason: str
    hope_line: str
    ending_image: str
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


def _r_slip(world: World) -> list[str]:
    art = world.get("art")
    if art.meters["displayed"] < THRESHOLD:
        return []
    if world.facts["exposure"] < world.facts["hold"] + 1:
        return []
    sig = ("slip",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    art.meters["slipping"] += 1
    art.meters["hanging_down"] += 1
    maker = world.get("Maker")
    helper = world.get("Helper")
    maker.memes["worry"] += 1
    helper.memes["alert"] += 1
    return ["__slip__"]


def _r_comfort(world: World) -> list[str]:
    art = world.get("art")
    recipient = world.get("Recipient")
    maker = world.get("Maker")
    helper = world.get("Helper")
    if art.meters["seen"] < THRESHOLD:
        return []
    sig = ("comfort",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    recipient.memes["comfort"] += 1
    recipient.memes["hope"] += 1
    recipient.memes["down"] = 0.0
    maker.memes["pride"] += 1
    helper.memes["joy"] += 1
    return []


CAUSAL_RULES = [
    Rule(name="slip", tag="physical", apply=_r_slip),
    Rule(name="comfort", tag="emotional", apply=_r_comfort),
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


def valid_combo(art: ArtProject, spot: DisplaySpot, support: Support) -> bool:
    if art.shape != spot.shape:
        return False
    if spot.mount != support.mount:
        return False
    if support.power < art.weight:
        return False
    return True


def hold_strength(art: ArtProject, spot: DisplaySpot, support: Support) -> int:
    return support.power + spot.anchor_bonus - art.weight


def exposure_level(spot: DisplaySpot, breeze: int) -> int:
    return spot.draftiness + breeze


def would_slip(art: ArtProject, spot: DisplaySpot, support: Support, breeze: int) -> bool:
    return exposure_level(spot, breeze) >= hold_strength(art, spot, support) + 1


def predict(world: World) -> dict:
    sim = world.copy()
    sim.get("art").meters["displayed"] += 1
    propagate(sim, narrate=False)
    return {
        "slips": sim.get("art").meters["slipping"] >= THRESHOLD,
        "exposure": sim.facts["exposure"],
        "hold": sim.facts["hold"],
    }


def introduce(world: World, maker: Entity, helper: Entity, recipient: Entity,
              mood: RecipientMood) -> None:
    world.say(
        f"{maker.id} noticed that {recipient.label_word} had looked a little down all morning. "
        f"{mood.down_reason}"
    )
    world.say(
        f'"Maybe some art will help," {maker.id} whispered. '
        f'{helper.id}, with {helper.attrs["nimble_phrase"]}, nodded right away.'
    )


def choose_project(world: World, maker: Entity, art: ArtProject, spot: DisplaySpot,
                   recipient: Entity, mood: RecipientMood) -> None:
    maker.memes["care"] += 1
    maker.memes["hope"] += 1
    world.say(
        f"{maker.id} chose {art.phrase} for {recipient.label_word} and planned to set it on {spot.phrase} in the {spot.room}."
    )
    world.say(mood.hope_line)


def make_art(world: World, maker: Entity, helper: Entity, art: ArtProject) -> None:
    maker.memes["focus"] += 1
    helper.memes["care"] += 1
    world.say(
        f"They worked quietly together. {art.opening} {art.making}."
    )
    world.say(
        f"{helper.id}'s nimble hands passed the right bits at just the right time, and soon the art looked ready to glow."
    )


def foreshadow(world: World, art: ArtProject, spot: DisplaySpot) -> None:
    line = {
        "flat": f"When they carried it to {spot.phrase}, the lower edge gave one soft nod down, as if the room had breathed on it.",
        "hanging": f"When they lifted it near {spot.phrase}, {art.fall_part} swayed once, and its little shadow shook on the wall.",
    }[art.shape]
    world.say(line)
    if world.facts["breeze"] > 0:
        world.say("From somewhere nearby, a small draft slipped through and touched the paper again.")


def hang_art(world: World, maker: Entity, art: ArtProject, spot: DisplaySpot,
             support: Support) -> None:
    world.get("art").meters["displayed"] += 1
    maker.memes["anticipation"] += 1
    world.say(
        f"{maker.id} carefully set the art on {spot.phrase} with {support.phrase}."
    )
    propagate(world, narrate=False)


def steady_wait(world: World, maker: Entity, helper: Entity, recipient: Entity) -> None:
    maker.memes["calm"] += 1
    helper.memes["calm"] += 1
    world.say(
        f"Nothing moved after that. {maker.id} and {helper.id} stepped back, pressed close together, and waited for {recipient.label_word}."
    )


def slip_turn(world: World, maker: Entity, helper: Entity, art: ArtProject,
              support: Support, recipient: Entity) -> None:
    art_ent = world.get("art")
    helper.memes["brisk"] += 1
    helper.memes["helpfulness"] += 1
    art_ent.meters["caught"] += 1
    world.say(
        f"Just as {recipient.label_word}'s footsteps came near, {art.fall_part} started to slide down."
    )
    world.say(
        f'"Oh!" said {maker.id}. But {helper.id} was quick. With {helper.attrs["nimble_phrase"]}, {helper.pronoun()} caught the {art.fall_part} before it bent.'
    )
    world.say(
        f"{recipient.label_word.capitalize()} looked up at once and reached in to help. {support.fix_line}"
    )
    art_ent.meters["slipping"] = 0.0
    art_ent.meters["secured"] += 1
    maker.memes["relief"] += 1
    helper.memes["relief"] += 1
    recipient.memes["tenderness"] += 1


def reveal(world: World, maker: Entity, helper: Entity, recipient: Entity,
           mood: RecipientMood, art: ArtProject) -> None:
    art_ent = world.get("art")
    art_ent.meters["seen"] += 1
    propagate(world, narrate=False)
    maker.memes["love"] += 1
    helper.memes["love"] += 1
    world.say(
        f'Then {maker.id} said, "It is for you."'
    )
    world.say(
        f"{recipient.label_word.capitalize()} stood very still for a moment, looking at every color and careful line."
    )
    world.say(
        f"{mood.ending_image} {recipient.pronoun().capitalize()} smiled so softly that the whole {world.facts['spot'].room} seemed warmer."
    )
    if art.shape == "flat":
        world.say(
            f"Soon the art stayed right where they had placed it, bright and brave on {world.facts['spot'].phrase}."
        )
    else:
        world.say(
            f"Soon the art hung still and shining, and its small shadow danced gently instead of wobbling."
        )


def closing(world: World, maker: Entity, helper: Entity, recipient: Entity) -> None:
    world.say(
        f"{maker.id} no longer worried about anything sliding down, and {helper.id} beamed with quiet pride."
    )
    world.say(
        f"By bedtime, nobody in the house felt quite so down."
    )
    world.say(
        f"They had made a little kindness with their hands, and somehow it had lifted all three hearts."
    )


def tell(art: ArtProject, spot: DisplaySpot, support: Support, mood: RecipientMood,
         maker_name: str = "Lina", maker_gender: str = "girl",
         helper_name: str = "Owen", helper_gender: str = "boy",
         recipient_type: str = "grandmother", breeze: int = 0,
         helper_style: str = "nimble fingers") -> World:
    world = World()
    maker = world.add(Entity(
        id=maker_name,
        kind="character",
        type=maker_gender,
        role="maker",
        traits=["kind", "careful"],
        attrs={},
    ))
    helper = world.add(Entity(
        id=helper_name,
        kind="character",
        type=helper_gender,
        role="helper",
        traits=["nimble", "helpful"],
        attrs={"nimble_phrase": helper_style},
    ))
    recipient = world.add(Entity(
        id="Recipient",
        kind="character",
        type=recipient_type,
        role="recipient",
        label="the recipient",
        attrs={},
    ))
    art_ent = world.add(Entity(
        id="art",
        kind="thing",
        type="art",
        label=art.label,
        attrs={"shape": art.shape},
    ))
    spot_ent = world.add(Entity(
        id="spot",
        kind="thing",
        type="spot",
        label=spot.label,
        attrs={"room": spot.room},
    ))
    support_ent = world.add(Entity(
        id="support",
        kind="thing",
        type="support",
        label=support.label,
        attrs={},
    ))

    recipient.memes["down"] = 1.0
    maker.memes["care"] = 0.0
    maker.memes["worry"] = 0.0
    helper.memes["alert"] = 0.0
    art_ent.meters["displayed"] = 0.0
    art_ent.meters["slipping"] = 0.0
    art_ent.meters["seen"] = 0.0
    art_ent.meters["secured"] = 0.0
    art_ent.meters["caught"] = 0.0
    art_ent.meters["hanging_down"] = 0.0

    world.facts.update(
        art_cfg=art,
        spot=spot,
        support=support,
        mood=mood,
        breeze=breeze,
        hold=hold_strength(art, spot, support),
        exposure=exposure_level(spot, breeze),
        maker=maker,
        helper=helper,
        recipient=recipient,
        art=art_ent,
        spot_ent=spot_ent,
        support_ent=support_ent,
    )

    introduce(world, maker, helper, recipient, mood)
    choose_project(world, maker, art, spot, recipient, mood)

    world.para()
    make_art(world, maker, helper, art)
    foreshadow(world, art, spot)

    world.para()
    hang_art(world, maker, art, spot, support)

    slips = art_ent.meters["slipping"] >= THRESHOLD
    if slips:
        slip_turn(world, maker, helper, art, support, recipient)
    else:
        steady_wait(world, maker, helper, recipient)

    world.para()
    reveal(world, maker, helper, recipient, mood, art)
    closing(world, maker, helper, recipient)

    world.facts.update(
        slips=slips,
        outcome="saved" if slips else "steady",
    )
    return world


ARTS = {
    "poster": ArtProject(
        id="poster",
        label="poster",
        phrase="a bright paper poster",
        shape="flat",
        mount="flat",
        weight=1,
        opening="Maker drew a yellow window, a teacup, and three smiling flowers.",
        making="Then helper dotted tiny stars around the corners.",
        detail="stars",
        fall_part="bottom corner",
        tags={"paper", "poster", "art"},
    ),
    "collage": ArtProject(
        id="collage",
        label="collage",
        phrase="a layered collage of colored paper hearts",
        shape="flat",
        mount="flat",
        weight=2,
        opening="Maker cut hearts from red, peach, and gold paper.",
        making="Helper stacked them in little rows while Maker glued a silver moon above them.",
        detail="hearts",
        fall_part="lower edge",
        tags={"paper", "collage", "art"},
    ),
    "ribbon_mobile": ArtProject(
        id="ribbon_mobile",
        label="ribbon mobile",
        phrase="a ribbon mobile with paper birds",
        shape="hanging",
        mount="rod",
        weight=1,
        opening="Maker tied tiny paper birds to soft ribbons.",
        making="Helper counted each ribbon and made sure the birds faced the same way.",
        detail="birds",
        fall_part="front ribbon",
        tags={"ribbon", "mobile", "art"},
    ),
}

SPOTS = {
    "fridge": DisplaySpot(
        id="fridge",
        label="fridge",
        phrase="the silver fridge",
        shape="flat",
        mount="flat_metal",
        room="kitchen",
        anchor_bonus=2,
        draftiness=0,
        tags={"fridge", "home"},
    ),
    "bedroom_wall": DisplaySpot(
        id="bedroom_wall",
        label="bedroom wall",
        phrase="the wall by the bedroom door",
        shape="flat",
        mount="flat_wall",
        room="hallway",
        anchor_bonus=1,
        draftiness=1,
        tags={"wall", "home"},
    ),
    "curtain_rod": DisplaySpot(
        id="curtain_rod",
        label="curtain rod",
        phrase="the curtain rod by the window",
        shape="hanging",
        mount="rod_clip",
        room="sitting room",
        anchor_bonus=1,
        draftiness=1,
        tags={"window", "home"},
    ),
}

SUPPORTS = {
    "magnet": Support(
        id="magnet",
        label="magnet",
        phrase="a round blue magnet",
        mount="flat_metal",
        power=1,
        fix_line="Together they slid on one more magnet, and the paper held fast.",
        qa_text="used extra magnets to hold it flat",
        tags={"magnet"},
    ),
    "painter_tape": Support(
        id="painter_tape",
        label="painter's tape",
        phrase="two neat strips of painter's tape",
        mount="flat_wall",
        power=2,
        fix_line="Together they pressed the tape smooth and added one more strip across the back.",
        qa_text="pressed the tape smooth and added another strip",
        tags={"tape"},
    ),
    "clothespin": Support(
        id="clothespin",
        label="clothespin",
        phrase="a wooden clothespin",
        mount="rod_clip",
        power=1,
        fix_line="Together they clipped it with a second clothespin so the ribbons could not wander anymore.",
        qa_text="added another clothespin so it would not slip",
        tags={"clothespin"},
    ),
}

MOODS = {
    "rainy_day": RecipientMood(
        id="rainy_day",
        who="grandmother",
        down_reason="Rain tapped the windows, and the quiet house felt too gray for her.",
        hope_line="If something cheerful was waiting there, maybe the room would not feel so lonely.",
        ending_image="The gray in her face seemed to melt away, like a cloud letting the sun through.",
        tags={"feelings", "rain"},
    ),
    "hard_work": RecipientMood(
        id="hard_work",
        who="father",
        down_reason="He had come home tired from a long day and had spoken in a small, tired voice.",
        hope_line="A surprise full of color might remind him that home still held soft things.",
        ending_image="The tired lines around his eyes loosened, and he let out a warm, surprised laugh.",
        tags={"feelings", "family"},
    ),
    "missing_friend": RecipientMood(
        id="missing_friend",
        who="grandfather",
        down_reason="He missed his walking friend, who was away visiting cousins for the week.",
        hope_line="A handmade surprise might make the afternoon feel less empty.",
        ending_image="His shoulders lifted, and he put a hand over his heart before smiling.",
        tags={"feelings", "friendship"},
    ),
}

GIRL_NAMES = ["Lina", "Maya", "Ella", "Nora", "Ruby", "Ivy", "Zoe", "Anna"]
BOY_NAMES = ["Owen", "Leo", "Ben", "Max", "Noah", "Theo", "Eli", "Finn"]
HELPER_STYLES = [
    "nimble fingers",
    "nimble little hands",
    "a nimble way of pinching and passing things",
]


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for art_id, art in ARTS.items():
        for spot_id, spot in SPOTS.items():
            for support_id, support in SUPPORTS.items():
                if valid_combo(art, spot, support):
                    combos.append((art_id, spot_id, support_id))
    return combos


@dataclass
class StoryParams:
    art: str
    spot: str
    support: str
    mood: str
    maker: str
    maker_gender: str
    helper: str
    helper_gender: str
    recipient: str
    breeze: int = 0
    helper_style: str = "nimble fingers"
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
    "art": [
        (
            "What is art?",
            "Art is something people make to show a feeling or an idea. It can be made with paper, colors, shapes, and careful hands.",
        )
    ],
    "poster": [
        (
            "What is a poster?",
            "A poster is a flat picture or sign made on paper. People can hang it where others will see it easily.",
        )
    ],
    "collage": [
        (
            "What is a collage?",
            "A collage is art made by putting many pieces together, like paper shapes or pictures. The layers make one new picture.",
        )
    ],
    "mobile": [
        (
            "What is a mobile?",
            "A mobile is hanging art with pieces that dangle and move gently in the air. Even a small breeze can make it sway.",
        )
    ],
    "magnet": [
        (
            "What does a magnet do on a fridge?",
            "A magnet sticks to metal and can hold a paper picture in place. That makes it handy for displaying art on a fridge.",
        )
    ],
    "tape": [
        (
            "Why does tape help hold paper up?",
            "Tape grips a surface and keeps paper from peeling away. If the paper is heavy or the room is drafty, you may need more tape.",
        )
    ],
    "clothespin": [
        (
            "What does a clothespin do?",
            "A clothespin pinches things so they stay together. It can hold a ribbon or paper art on a rod or line.",
        )
    ],
    "feelings": [
        (
            "What can you do when someone feels down?",
            "You can notice their feelings and offer something gentle, like help, kind words, or a handmade surprise. Small caring acts can make a big difference.",
        )
    ],
    "rain": [
        (
            "Why can a draft move light things?",
            "Moving air can push on light paper or ribbons. That is why a paper picture may flutter when a window or door lets air through.",
        )
    ],
}
KNOWLEDGE_ORDER = ["art", "poster", "collage", "mobile", "magnet", "tape", "clothespin", "feelings", "rain"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    maker = f["maker"]
    helper = f["helper"]
    art = f["art_cfg"]
    recipient = f["recipient"]
    mood = f["mood"]
    outcome = f["outcome"]
    turn = (
        "the art begins to slip down just before the surprise is revealed"
        if outcome == "saved"
        else "a tiny early hint suggests trouble, but the art stays steady"
    )
    return [
        f'Write a heartwarming story for a 3-to-5-year-old that includes the words "down", "art", and "nimble".',
        f"Tell a gentle family story where {maker.id} and {helper.id} make {art.phrase} for a {recipient.label_word} who feels down, and use foreshadowing so {turn}.",
        f"Write a cozy story about cheering someone up with handmade art after {mood.down_reason.lower()}",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    maker = f["maker"]
    helper = f["helper"]
    recipient = f["recipient"]
    art = f["art_cfg"]
    spot = f["spot"]
    support = f["support"]
    mood = f["mood"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {maker.id}, {helper.id}, and {recipient.label_word}. {maker.id} and {helper.id} wanted to cheer {recipient.label_word} when {recipient.pronoun()} felt down.",
        ),
        (
            "Why did they make art?",
            f"They noticed that {recipient.label_word} seemed down, so they made art as a surprise. The whole project came from wanting to change the mood in a kind way.",
        ),
        (
            "What kind of art did they make, and where did they put it?",
            f"They made {art.phrase} and put it on {spot.phrase} in the {spot.room}. They chose that place so {recipient.label_word} would see it clearly.",
        ),
        (
            "What was the early hint that something might go wrong?",
            f"There was a tiny warning before the big moment: {art.fall_part} moved and seemed to dip down. That foreshadowed that the art might not stay put when the air moved.",
        ),
    ]
    if f["outcome"] == "saved":
        qa.append(
            (
                "What happened when the surprise was almost ready?",
                f"The art started to slip down just as {recipient.label_word} came near. {helper.id} used {helper.attrs['nimble_phrase']} to catch it fast, and then everyone secured it together.",
            )
        )
        qa.append(
            (
                f"How did they fix the problem?",
                f"They fixed it with {support.label}. {support.fix_line} That kept the art from falling and let the surprise stay beautiful.",
            )
        )
    else:
        qa.append(
            (
                "Did the art fall?",
                f"No, it stayed steady. The earlier little wobble was only a hint, and after they hung it up, it did not slide down at all.",
            )
        )
    qa.append(
        (
            f"How did the art help {recipient.label_word}?",
            f"The art made {recipient.label_word} feel comforted and less down. It helped because the surprise showed careful love, not just pretty colors.",
        )
    )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags = {"art"} | set(f["mood"].tags) | set(f["support"].tags)
    art = f["art_cfg"]
    if art.id == "poster":
        tags.add("poster")
    if art.id == "collage":
        tags.add("collage")
    if art.id == "ribbon_mobile":
        tags.add("mobile")
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
        lines.append(f"  {ent.id:10} ({ent.type:12}) {' '.join(bits)}")
    lines.append(f"  exposure={world.facts['exposure']} hold={world.facts['hold']} outcome={world.facts['outcome']}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        art="poster",
        spot="fridge",
        support="magnet",
        mood="rainy_day",
        maker="Lina",
        maker_gender="girl",
        helper="Owen",
        helper_gender="boy",
        recipient="grandmother",
        breeze=0,
        helper_style="nimble fingers",
    ),
    StoryParams(
        art="collage",
        spot="bedroom_wall",
        support="painter_tape",
        mood="hard_work",
        maker="Maya",
        maker_gender="girl",
        helper="Ben",
        helper_gender="boy",
        recipient="father",
        breeze=1,
        helper_style="nimble little hands",
    ),
    StoryParams(
        art="ribbon_mobile",
        spot="curtain_rod",
        support="clothespin",
        mood="missing_friend",
        maker="Nora",
        maker_gender="girl",
        helper="Leo",
        helper_gender="boy",
        recipient="grandfather",
        breeze=1,
        helper_style="a nimble way of pinching and passing things",
    ),
]


def explain_rejection(art: ArtProject, spot: DisplaySpot, support: Support) -> str:
    if art.shape != spot.shape:
        return (
            f"(No story: {art.label} is {art.shape} art, but {spot.label} is for {spot.shape} display. "
            f"Pick a spot that matches the art's shape.)"
        )
    if spot.mount != support.mount:
        return (
            f"(No story: {support.label} does not fit {spot.label}. "
            f"Choose a support made for that kind of spot.)"
        )
    if support.power < art.weight:
        return (
            f"(No story: {support.label} is too weak to hold the {art.label}. "
            f"Choose a stronger support.)"
        )
    return "(No story: this art, spot, and support do not make a reasonable display.)"


def outcome_of(params: StoryParams) -> str:
    return "saved" if would_slip(ARTS[params.art], SPOTS[params.spot], SUPPORTS[params.support], params.breeze) else "steady"


ASP_RULES = r"""
valid(A,S,P) :- art(A), spot(S), support(P),
                art_shape(A,Sh), spot_shape(S,Sh),
                spot_mount(S,M), support_mount(P,M),
                art_weight(A,W), support_power(P,Pw), Pw >= W.

hold(A,S,P,H) :- valid(A,S,P),
                 support_power(P,Pw), anchor_bonus(S,B), art_weight(A,W),
                 H = Pw + B - W.

exposure(S,B,E) :- spot(S), breeze(B), draftiness(S,D), E = D + B.

slip(A,S,P,B) :- valid(A,S,P), hold(A,S,P,H), exposure(S,B,E), E >= H + 1.
outcome(A,S,P,B,saved) :- slip(A,S,P,B).
outcome(A,S,P,B,steady) :- valid(A,S,P), breeze(B), not slip(A,S,P,B).
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for art_id, art in ARTS.items():
        lines.append(asp.fact("art", art_id))
        lines.append(asp.fact("art_shape", art_id, art.shape))
        lines.append(asp.fact("art_weight", art_id, art.weight))
    for spot_id, spot in SPOTS.items():
        lines.append(asp.fact("spot", spot_id))
        lines.append(asp.fact("spot_shape", spot_id, spot.shape))
        lines.append(asp.fact("spot_mount", spot_id, spot.mount))
        lines.append(asp.fact("anchor_bonus", spot_id, spot.anchor_bonus))
        lines.append(asp.fact("draftiness", spot_id, spot.draftiness))
    for support_id, support in SUPPORTS.items():
        lines.append(asp.fact("support", support_id))
        lines.append(asp.fact("support_mount", support_id, support.mount))
        lines.append(asp.fact("support_power", support_id, support.power))
    for b in [0, 1]:
        lines.append(asp.fact("breeze", b))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("", "#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_outcome(params: StoryParams) -> str:
    import asp

    extra = "\n".join(
        [
            asp.fact("chosen_art", params.art),
            asp.fact("chosen_spot", params.spot),
            asp.fact("chosen_support", params.support),
            asp.fact("chosen_breeze", params.breeze),
            "picked_outcome(O) :- chosen_art(A), chosen_spot(S), chosen_support(P), chosen_breeze(B), outcome(A,S,P,B,O).",
        ]
    )
    model = asp.one_model(asp_program(extra, "#show picked_outcome/1."))
    out = asp.atoms(model, "picked_outcome")
    return out[0][0] if out else "?"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Story world sketch: handmade cheer-up art, a nimble helper, and a foreshadowed wobble."
    )
    ap.add_argument("--art", choices=ARTS)
    ap.add_argument("--spot", choices=SPOTS)
    ap.add_argument("--support", choices=SUPPORTS)
    ap.add_argument("--mood", choices=MOODS)
    ap.add_argument("--recipient", choices=["mother", "father", "grandmother", "grandfather"])
    ap.add_argument("--breeze", type=int, choices=[0, 1], help="0 = still room, 1 = small draft")
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list valid combinations from clingo")
    ap.add_argument("--verify", action="store_true", help="check the inline ASP model and run smoke tests")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def _pick_name(rng: random.Random, gender: str, avoid: str = "") -> str:
    pool = GIRL_NAMES if gender == "girl" else BOY_NAMES
    choices = [n for n in pool if n != avoid]
    return rng.choice(choices)


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.art and args.spot and args.support:
        art = ARTS[args.art]
        spot = SPOTS[args.spot]
        support = SUPPORTS[args.support]
        if not valid_combo(art, spot, support):
            raise StoryError(explain_rejection(art, spot, support))

    combos = [
        c for c in valid_combos()
        if (args.art is None or c[0] == args.art)
        and (args.spot is None or c[1] == args.spot)
        and (args.support is None or c[2] == args.support)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    art_id, spot_id, support_id = rng.choice(sorted(combos))
    mood_id = args.mood or rng.choice(sorted(MOODS))
    recipient = args.recipient or MOODS[mood_id].who
    breeze = args.breeze if args.breeze is not None else rng.choice([0, 1])
    maker_gender = rng.choice(["girl", "boy"])
    helper_gender = rng.choice(["girl", "boy"])
    maker = _pick_name(rng, maker_gender)
    helper = _pick_name(rng, helper_gender, avoid=maker)
    helper_style = rng.choice(HELPER_STYLES)

    return StoryParams(
        art=art_id,
        spot=spot_id,
        support=support_id,
        mood=mood_id,
        maker=maker,
        maker_gender=maker_gender,
        helper=helper,
        helper_gender=helper_gender,
        recipient=recipient,
        breeze=breeze,
        helper_style=helper_style,
    )


def generate(params: StoryParams) -> StorySample:
    try:
        art = ARTS[params.art]
        spot = SPOTS[params.spot]
        support = SUPPORTS[params.support]
        mood = MOODS[params.mood]
    except KeyError as err:
        raise StoryError(f"(No story: unknown option {err.args[0]!r}.)") from None

    if not valid_combo(art, spot, support):
        raise StoryError(explain_rejection(art, spot, support))
    if params.recipient not in {"mother", "father", "grandmother", "grandfather"}:
        raise StoryError("(No story: recipient must be mother, father, grandmother, or grandfather.)")
    if params.breeze not in {0, 1}:
        raise StoryError("(No story: breeze must be 0 or 1.)")

    world = tell(
        art=art,
        spot=spot,
        support=support,
        mood=mood,
        maker_name=params.maker,
        maker_gender=params.maker_gender,
        helper_name=params.helper,
        helper_gender=params.helper_gender,
        recipient_type=params.recipient,
        breeze=params.breeze,
        helper_style=params.helper_style,
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

    clingo_set = set(asp_valid_combos())
    python_set = set(valid_combos())
    if clingo_set == python_set:
        print(f"OK: valid combinations match ({len(clingo_set)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combinations:")
        if clingo_set - python_set:
            print("  only in clingo:", sorted(clingo_set - python_set))
        if python_set - clingo_set:
            print("  only in python:", sorted(python_set - clingo_set))

    cases = list(CURATED)
    for seed in range(40):
        try:
            params = resolve_params(build_parser().parse_args([]), random.Random(seed))
        except StoryError:
            continue
        cases.append(params)

    bad = 0
    for params in cases:
        if asp_outcome(params) != outcome_of(params):
            bad += 1
    if bad == 0:
        print(f"OK: outcome model matches on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {bad}/{len(cases)} outcomes differ.")

    try:
        smoke = generate(cases[0])
        if not smoke.story.strip():
            raise StoryError("(Smoke test failed: empty story.)")
        print("OK: smoke test generated a normal story.")
    except Exception as err:
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    return rc


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("", "#show valid/3.\n#show outcome/5."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (art, spot, support) combos:\n")
        for art_id, spot_id, support_id in combos:
            print(f"  {art_id:13} {spot_id:13} {support_id}")
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
            header = f"### {p.maker} & {p.helper}: {p.art} on {p.spot} with {p.support} ({outcome_of(p)})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()

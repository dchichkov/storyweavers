#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/talkative_dart_wobble_cautionary_curiosity_happy_ending.py
======================================================================================

A standalone storyworld for a small mystery tale: a talkative child notices a
strange wobble in a dark corner, curiosity pulls them closer, a grown-up teaches
the safe way to solve little mysteries, and the ending stays bright and gentle.

The domain is deliberately tight:

    child + mysterious hiding place + hidden small creature + sensible adult response

The cautionary lesson is concrete: do not put your hand into a dark or hidden
place just because curiosity is strong. Ask a grown-up, use light, and let the
right tools do the work.

Run it
------
    python storyworlds/worlds/gpt-5.4/talkative_dart_wobble_cautionary_curiosity_happy_ending.py
    python storyworlds/worlds/gpt-5.4/talkative_dart_wobble_cautionary_curiosity_happy_ending.py --place attic --creature hamster
    python storyworlds/worlds/gpt-5.4/talkative_dart_wobble_cautionary_curiosity_happy_ending.py --response shake_hard
    python storyworlds/worlds/gpt-5.4/talkative_dart_wobble_cautionary_curiosity_happy_ending.py --all --qa
    python storyworlds/worlds/gpt-5.4/talkative_dart_wobble_cautionary_curiosity_happy_ending.py --verify
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


# ---------------------------------------------------------------------------
# Core entities
# ---------------------------------------------------------------------------
@dataclass
class Entity:
    id: str
    kind: str = "thing"             # "character" | "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    role: str = ""
    traits: list[str] = field(default_factory=list)
    attrs: dict = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "woman", "grandmother", "aunt"}
        male = {"boy", "father", "man", "grandfather", "uncle"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    @property
    def label_word(self) -> str:
        return {
            "mother": "mom",
            "father": "dad",
            "grandmother": "grandma",
            "grandfather": "grandpa",
        }.get(self.type, self.type)


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------
    @property
    def tags(self):
        if not hasattr(self, "_tags"):
            object.__setattr__(self, "_tags", set())
        return self._tags


@dataclass
class Setting:
    id: str
    place: str
    mood: str
    detail: str
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
class Hiding:
    id: str
    label: str
    phrase: str
    kind: str
    room_text: str
    wobble_text: str
    fits: set[str] = field(default_factory=set)
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
class Creature:
    id: str
    label: str
    phrase: str
    size: str
    sound: str
    dart_text: str
    home: str
    clue: str
    skittish: int
    pet: bool = False
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
class Response:
    id: str
    sense: int
    power: int
    works_in: set[str] = field(default_factory=set)
    works_for: set[str] = field(default_factory=set)
    text: str = ""
    qa_text: str = ""
    tags: set[str] = field(default_factory=set)


# ---------------------------------------------------------------------------
# World container
# ---------------------------------------------------------------------------
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
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
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
        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        clone.facts = copy.deepcopy(self.facts)
        return clone


# ---------------------------------------------------------------------------
# Causal rules
# ---------------------------------------------------------------------------
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


def _r_trapped_wobble(world: World) -> list[str]:
    out: list[str] = []
    hiding = world.get("hiding")
    creature = world.get("creature")
    child = world.get("child")
    if creature.meters["trapped"] >= THRESHOLD and hiding.meters["closed"] >= THRESHOLD:
        sig = ("wobble", hiding.id)
        if sig not in world.fired:
            world.fired.add(sig)
            hiding.meters["wobble"] += 1
            child.memes["curiosity"] += 1
            world.get("room").memes["mystery"] += 1
            out.append("__wobble__")
    return out


def _r_reach_startle(world: World) -> list[str]:
    out: list[str] = []
    child = world.get("child")
    creature = world.get("creature")
    hiding = world.get("hiding")
    if child.meters["reaching"] >= THRESHOLD and creature.meters["trapped"] >= THRESHOLD:
        sig = ("startle", child.id, creature.id)
        if sig not in world.fired:
            world.fired.add(sig)
            creature.meters["loose"] += 1
            creature.meters["trapped"] = 0.0
            hiding.meters["closed"] = 0.0
            child.memes["fear"] += 1
            child.meters["stumble"] += 1
            out.append("__dart__")
    return out


CAUSAL_RULES = [
    Rule(name="trapped_wobble", tag="physical", apply=_r_trapped_wobble),
    Rule(name="reach_startle", tag="social", apply=_r_reach_startle),
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


# ---------------------------------------------------------------------------
# Constraints and prediction
# ---------------------------------------------------------------------------
def fits(creature: Creature, hiding: Hiding) -> bool:
    return creature.size in hiding.fits


def suitable_responses(creature: Creature, hiding: Hiding) -> list[Response]:
    res = []
    for response in RESPONSES.values():
        if response.sense < SENSE_MIN:
            continue
        if hiding.kind in response.works_in and creature.id in response.works_for:
            if response.power >= creature.skittish:
                res.append(response)
    return sorted(res, key=lambda r: (r.sense, r.power, r.id))


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for place_id, setting in SETTINGS.items():
        for hiding_id in sorted(setting.affords):
            hiding = HIDINGS[hiding_id]
            for creature_id, creature in CREATURES.items():
                if fits(creature, hiding) and suitable_responses(creature, hiding):
                    combos.append((place_id, creature_id, hiding_id))
    return combos


def outcome_of(params: "StoryParams") -> str:
    creature = CREATURES[params.creature]
    return "startled" if params.impulse and creature.skittish >= 2 else "careful"


def predict_reach(world: World) -> dict:
    sim = world.copy()
    sim.get("child").meters["reaching"] += 1
    propagate(sim, narrate=False)
    return {
        "creature_loose": sim.get("creature").meters["loose"] >= THRESHOLD,
        "child_scared": sim.get("child").memes["fear"] >= THRESHOLD,
    }


# ---------------------------------------------------------------------------
# Story actions
# ---------------------------------------------------------------------------
def introduce(world: World, child: Entity, adult: Entity) -> None:
    world.say(
        f"{child.id} was a talkative little {child.type} who noticed every odd sound and every shadow that did not belong. "
        f"That afternoon {child.pronoun()} was with {child.pronoun('possessive')} {adult.label_word} in {world.setting.place}, "
        f"and the place felt full of hush and secrets."
    )
    world.say(world.setting.detail)


def notice(world: World, child: Entity, hiding: Hiding, creature: Creature) -> None:
    propagate(world, narrate=False)
    world.say(
        f"Then {child.id} saw {hiding.phrase} in a corner of the room. {hiding.room_text}."
    )
    world.say(
        f"Just when the room seemed perfectly still, {hiding.phrase} gave a wobble. "
        f"It was such a small wobble that {child.id} wondered if {child.pronoun()} had imagined it."
    )
    world.say(
        f'"Did you see that?" {child.id} whispered. "{hiding.label.capitalize()}s are not supposed to move by themselves."'
    )
    world.facts["first_clue"] = creature.clue


def clue(world: World, child: Entity, hiding: Hiding, creature: Creature) -> None:
    child.memes["curiosity"] += 1
    world.say(
        f"{child.id} crept closer and listened. From inside came {creature.sound}, and the mystery grew bigger instead of smaller."
    )
    world.say(
        f"A little {creature.clue} slipped out near the edge, then vanished again."
    )


def warn(world: World, adult: Entity, child: Entity, hiding: Hiding) -> None:
    pred = predict_reach(world)
    world.facts["predicted_loose"] = pred["creature_loose"]
    world.facts["predicted_scared"] = pred["child_scared"]
    child.memes["caution"] += 1
    world.say(
        f'{adult.label_word.capitalize()} touched {child.pronoun("possessive")} shoulder. '
        f'"Mysteries are for patient eyes, not quick fingers," {adult.pronoun()} said. '
        f'"Never put your hand into {hiding.phrase} when you cannot see inside."'
    )


def edge_closer(world: World, child: Entity, hiding: Hiding) -> None:
    child.memes["impulse"] += 1
    world.say(
        f"But curiosity tugged at {child.id} like a string. {child.pronoun().capitalize()} bent near enough to see the lid tremble again."
    )


def startle_branch(world: World, child: Entity, creature: Entity, hiding: Hiding, cfg: Creature) -> None:
    child.meters["reaching"] += 1
    propagate(world, narrate=False)
    world.say(
        f"Before {child.id} could stop, {child.pronoun()} lifted the edge just a little."
    )
    world.say(
        f"At once {cfg.dart_text}. {child.id} jumped back so fast that {child.pronoun('possessive')} knees gave a wobble, "
        f"and {child.pronoun()} grabbed {child.pronoun('possessive')} own elbows."
    )
    world.facts["darted"] = True


def careful_branch(world: World, child: Entity, adult: Entity) -> None:
    child.memes["self_control"] += 1
    world.say(
        f"{child.id} tucked {child.pronoun('possessive')} hands behind {child.pronoun('possessive')} back and took one step away. "
        f"{child.pronoun().capitalize()} was still bursting with questions, but {child.pronoun()} waited."
    )
    world.facts["darted"] = False


def adult_acts(world: World, adult: Entity, child: Entity, creature: Entity,
               hiding: Hiding, creature_cfg: Creature, response: Response) -> None:
    creature.meters["found"] += 1
    creature.meters["safe"] += 1
    creature.meters["trapped"] = 0.0
    creature.meters["loose"] = 0.0
    world.get("hiding").meters["closed"] = 0.0
    body = response.text.format(hiding=hiding.label, creature=creature_cfg.label)
    world.say(
        f"{adult.label_word.capitalize()} stayed calm and {body}."
    )
    world.say(
        f"Inside was {creature_cfg.phrase}. For one more breath it looked ready to dart again, but {adult.label_word} moved slowly and made the room feel safe."
    )


def resolve(world: World, adult: Entity, child: Entity, creature_cfg: Creature) -> None:
    child.memes["relief"] += 1
    child.memes["lesson"] += 1
    child.memes["joy"] += 1
    world.say(
        f'"A {creature_cfg.label}," {child.id} breathed, amazed that the mystery had turned into a living little somebody.'
    )
    world.say(
        f'{adult.label_word.capitalize()} nodded. "{creature_cfg.home.capitalize()} is where {creature_cfg.pronoun if False else "it"} belongs, and the safe way to help is to look first, then move gently."'
    )


def ending(world: World, adult: Entity, child: Entity, creature_cfg: Creature) -> None:
    world.say(
        f"Together they settled the {creature_cfg.label} back in {creature_cfg.home}. "
        f"The whole room seemed softer afterward, as if the mystery itself had let out a quiet breath."
    )
    world.say(
        f"On the way home, {child.id} was still talkative, but now {child.pronoun()} asked questions before touching anything hidden or dark. "
        f"That made {adult.label_word} smile."
    )
    world.say(
        f"And whenever a basket, box, or sack gave a wobble after that, {child.id} remembered: curious minds are wonderful, but careful hands make the happiest endings."
    )


# ---------------------------------------------------------------------------
# Screenplay
# ---------------------------------------------------------------------------
def tell(setting: Setting, hiding_cfg: Hiding, creature_cfg: Creature, response: Response,
         child_name: str = "Nora", child_type: str = "girl", adult_type: str = "grandfather",
         impulse: bool = False) -> World:
    world = World(setting=setting)
    child = world.add(Entity(
        id=child_name,
        kind="character",
        type=child_type,
        role="child",
        label=child_name,
        traits=["talkative", "curious"],
        attrs={},
    ))
    adult = world.add(Entity(
        id="Adult",
        kind="character",
        type=adult_type,
        role="adult",
        label="the grown-up",
        attrs={},
    ))
    hiding = world.add(Entity(
        id="hiding",
        kind="thing",
        type=hiding_cfg.kind,
        label=hiding_cfg.label,
        phrase=hiding_cfg.phrase,
        attrs={"kind": hiding_cfg.kind},
    ))
    creature = world.add(Entity(
        id="creature",
        kind="thing",
        type="creature",
        label=creature_cfg.label,
        phrase=creature_cfg.phrase,
        attrs={"home": creature_cfg.home},
    ))
    world.add(Entity(id="room", kind="thing", type="room", label=setting.place, attrs={}))

    # Initialize every read-before-write state touched by rules or branching.
    hiding.meters["closed"] = 1.0
    hiding.meters["wobble"] = 0.0
    creature.meters["trapped"] = 1.0
    creature.meters["loose"] = 0.0
    creature.meters["found"] = 0.0
    creature.meters["safe"] = 0.0
    child.meters["reaching"] = 0.0
    child.meters["stumble"] = 0.0
    child.memes["curiosity"] = 0.0
    child.memes["caution"] = 0.0
    child.memes["fear"] = 0.0
    child.memes["relief"] = 0.0
    child.memes["joy"] = 0.0
    child.memes["lesson"] = 0.0
    child.memes["impulse"] = 0.0
    child.memes["self_control"] = 0.0
    world.get("room").memes["mystery"] = 0.0

    world.facts = {
        "setting": setting,
        "hiding_cfg": hiding_cfg,
        "creature_cfg": creature_cfg,
        "response": response,
        "child": child,
        "adult": adult,
        "hiding": hiding,
        "creature": creature,
        "impulse": impulse,
        "predicted_loose": False,
        "predicted_scared": False,
        "darted": False,
    }

    introduce(world, child, adult)
    world.para()
    notice(world, child, hiding_cfg, creature_cfg)
    clue(world, child, hiding_cfg, creature_cfg)
    world.para()
    warn(world, adult, child, hiding_cfg)
    edge_closer(world, child, hiding_cfg)

    if impulse and creature_cfg.skittish >= 2:
        startle_branch(world, child, creature, hiding_cfg, creature_cfg)
        outcome = "startled"
    else:
        careful_branch(world, child, adult)
        outcome = "careful"

    world.para()
    adult_acts(world, adult, child, creature, hiding_cfg, creature_cfg, response)
    resolve(world, adult, child, creature_cfg)
    world.para()
    ending(world, adult, child, creature_cfg)

    world.facts["outcome"] = outcome
    return world


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------
SETTINGS = {
    "attic": Setting(
        id="attic",
        place="the attic",
        mood="dusty",
        detail="Old trunks hunched under the beams, and the late light lay in long gold stripes across the floorboards.",
        affords={"hat_box", "wicker_basket"},
    ),
    "greenhouse": Setting(
        id="greenhouse",
        place="the greenhouse",
        mood="glassy",
        detail="The windows were pearled with mist, and rows of pots made little leafy shadows on the bricks.",
        affords={"seed_sack", "wicker_basket"},
    ),
    "shed": Setting(
        id="shed",
        place="the garden shed",
        mood="dim",
        detail="Rakes leaned along one wall, and the smell of soil and rain hung quietly in the air.",
        affords={"seed_sack", "hat_box"},
    ),
}

HIDINGS = {
    "hat_box": Hiding(
        id="hat_box",
        label="hat box",
        phrase="an old round hat box",
        kind="box",
        room_text="It sat on a shelf beside a faded scarf and a stack of picture books nobody had opened in years",
        wobble_text="The lid shivered once",
        fits={"tiny", "small"},
        tags={"box", "dark_place"},
    ),
    "wicker_basket": Hiding(
        id="wicker_basket",
        label="wicker basket",
        phrase="a wicker basket with a loose lid",
        kind="basket",
        room_text="It waited under a table where the shadows were deepest",
        wobble_text="The lid tipped and settled again",
        fits={"tiny", "small"},
        tags={"basket", "dark_place"},
    ),
    "seed_sack": Hiding(
        id="seed_sack",
        label="seed sack",
        phrase="a striped seed sack",
        kind="sack",
        room_text="It leaned against the wall beside a watering can and a line of empty clay pots",
        wobble_text="The cloth twitched near the knot",
        fits={"tiny"},
        tags={"sack", "dark_place"},
    ),
}

CREATURES = {
    "hamster": Creature(
        id="hamster",
        label="hamster",
        phrase="a small golden hamster with bright button eyes",
        size="tiny",
        sound="the faintest rustle, like paper being folded",
        dart_text="a golden blur tried to dart past the opening",
        home="its little cage by the window",
        clue="whisker",
        skittish=2,
        pet=True,
        tags={"hamster", "small_animal"},
    ),
    "mouse": Creature(
        id="mouse",
        label="field mouse",
        phrase="a field mouse with a neat gray nose and bead-black eyes",
        size="tiny",
        sound="a dry scritch-scritch that stopped whenever anyone breathed too loudly",
        dart_text="a gray nose and two tiny paws darted out before the creature spun back toward the dark",
        home="the herb patch outside",
        clue="gray nose",
        skittish=3,
        pet=False,
        tags={"mouse", "small_animal"},
    ),
    "rabbit_kit": Creature(
        id="rabbit_kit",
        label="baby rabbit",
        phrase="a baby rabbit with velvet ears tucked flat",
        size="small",
        sound="a soft thump-thump against the side",
        dart_text="two velvet ears flashed up and the baby rabbit tried to dart free in one springy hop",
        home="the safe little hutch on the porch",
        clue="soft tuft of fur",
        skittish=2,
        pet=True,
        tags={"rabbit", "small_animal"},
    ),
}

RESPONSES = {
    "flashlight_towel": Response(
        id="flashlight_towel",
        sense=3,
        power=3,
        works_in={"box", "basket", "sack"},
        works_for={"hamster", "mouse", "rabbit_kit"},
        text="shone a flashlight inside the {hiding} first, then laid a soft towel over the opening and lifted the lid slowly",
        qa_text="used a flashlight first and a soft towel to open the hiding place slowly",
        tags={"flashlight", "towel", "safe_help"},
    ),
    "treat_box": Response(
        id="treat_box",
        sense=3,
        power=2,
        works_in={"box", "basket"},
        works_for={"hamster", "rabbit_kit"},
        text="set a little treat near the opening and guided the {creature} into a small box instead of grabbing",
        qa_text="used a treat and guided the little animal into a box instead of grabbing",
        tags={"treats", "box", "safe_help"},
    ),
    "gloves_and_basket": Response(
        id="gloves_and_basket",
        sense=2,
        power=3,
        works_in={"basket", "sack"},
        works_for={"mouse", "hamster", "rabbit_kit"},
        text="put on garden gloves, tipped the {hiding} carefully, and steadied the little creature with an empty basket nearby",
        qa_text="used gloves and an extra basket so the creature could be guided without anyone grabbing in the dark",
        tags={"gloves", "basket", "safe_help"},
    ),
    "shake_hard": Response(
        id="shake_hard",
        sense=1,
        power=1,
        works_in={"box", "basket", "sack"},
        works_for={"hamster", "mouse", "rabbit_kit"},
        text="shook the {hiding} hard until something fell out",
        qa_text="shook the hiding place hard",
        tags={"unsafe"},
    ),
}

GIRL_NAMES = ["Nora", "Lily", "Mina", "Zoe", "Ava", "Lucy", "Maya", "Ella"]
BOY_NAMES = ["Ben", "Max", "Theo", "Finn", "Eli", "Leo", "Sam", "Noah"]


# ---------------------------------------------------------------------------
# Per-world params
# ---------------------------------------------------------------------------
@dataclass
class StoryParams:
    place: str
    creature: str
    hiding: str
    response: str
    name: str
    gender: str
    adult: str
    impulse: bool = False
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# Q&A
# ---------------------------------------------------------------------------
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


KNOWLEDGE = {
    "dark_place": [
        (
            "Why should you not put your hand into a dark place when you cannot see inside?",
            "You might surprise an animal or touch something sharp, dusty, or unsafe. It is better to look first and ask a grown-up for help."
        )
    ],
    "flashlight": [
        (
            "Why is a flashlight useful when something is hiding?",
            "A flashlight helps you see what is really there before you touch anything. Seeing first lets you make a calm, safe choice."
        )
    ],
    "towel": [
        (
            "Why would a grown-up use a towel to help a little animal?",
            "A soft towel can make a little animal feel covered and calmer. It also helps the grown-up guide it gently instead of grabbing fast."
        )
    ],
    "gloves": [
        (
            "Why can gloves help when a grown-up handles a small animal carefully?",
            "Gloves protect hands and remind the grown-up to move slowly and gently. They are a safety tool, not a toy."
        )
    ],
    "hamster": [
        (
            "What is a hamster?",
            "A hamster is a very small furry pet with whiskers and quick little feet. It can move fast and hide in tiny places."
        )
    ],
    "mouse": [
        (
            "What is a field mouse?",
            "A field mouse is a tiny wild animal that lives outdoors and moves very quickly. If it is scared, it may dart away to hide."
        )
    ],
    "rabbit": [
        (
            "Why can a baby rabbit seem jumpy?",
            "A baby rabbit is small and easily startled, so it may hop away very fast when it feels scared. Quiet, gentle help matters."
        )
    ],
    "safe_help": [
        (
            "What should you do if you find a small animal hiding where it should not be?",
            "Call a grown-up and let them look first. Moving slowly and using the right tools keeps both you and the animal safer."
        )
    ],
}
KNOWLEDGE_ORDER = ["dark_place", "flashlight", "towel", "gloves", "hamster", "mouse", "rabbit", "safe_help"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    child = f["child"]
    creature = f["creature_cfg"]
    hiding = f["hiding_cfg"]
    outcome = f["outcome"]
    second = "A curious child almost peeks inside and gets a fright before a calm grown-up helps." if outcome == "startled" else "A curious child waits instead of reaching, and the mystery is solved safely."
    return [
        'Write a short mystery story for a 3-to-5-year-old that includes the words "talkative", "dart", and "wobble".',
        f"Tell a gentle cautionary mystery about a talkative {child.type} who notices {hiding.phrase} wobble and discovers a hidden {creature.label}.",
        second,
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    child = f["child"]
    adult = f["adult"]
    creature = f["creature_cfg"]
    hiding = f["hiding_cfg"]
    response = f["response"]
    qa: list[tuple[str, str]] = [
        (
            "What was the mystery in the story?",
            f"The mystery was that {hiding.phrase} moved when nothing around it should have moved. That strange wobble made {child.id} wonder if something alive was hiding inside."
        ),
        (
            f"Why did {adult.label_word} tell {child.id} not to reach inside?",
            f"{adult.label_word.capitalize()} knew that hidden places can surprise you, especially when you cannot see inside. A scared little animal might dart out, and {child.id} could get frightened or grab the wrong thing."
        ),
    ]
    if f["outcome"] == "startled":
        qa.append(
            (
                f"What happened when {child.id} got too close?",
                f"{child.id} lifted the edge a little, and the hidden creature tried to dart out at once. That sudden movement scared {child.pronoun('object')} so much that {child.pronoun()} jumped back with a wobble."
            )
        )
    else:
        qa.append(
            (
                f"How did {child.id} show self-control?",
                f"{child.id} wanted to know the answer right away, but kept {child.pronoun('possessive')} hands back and waited. That choice let the grown-up solve the mystery safely."
            )
        )
    qa.append(
        (
            f"How did {adult.label_word} help in a safe way?",
            f"{adult.label_word.capitalize()} {response.qa_text}. Looking first and moving slowly kept the animal calmer and kept {child.id} from reaching into the dark."
        )
    )
    qa.append(
        (
            "How did the story end?",
            f"It ended happily because the mystery turned out to be {creature.phrase}, and the little animal was put back in {creature.home}. After that, {child.id} still loved questions, but remembered to ask for help before touching hidden things."
        )
    )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    creature = f["creature_cfg"]
    response = f["response"]
    hiding = f["hiding_cfg"]
    tags = set(creature.tags) | set(response.tags) | set(hiding.tags)
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


# ---------------------------------------------------------------------------
# Trace
# ---------------------------------------------------------------------------
def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for ent in list(world.entities.values()):
        meters = {k: v for k, v in ent.meters.items() if v}
        memes = {k: v for k, v in ent.memes.items() if v}
        bits = []
        if ent.role:
            bits.append(f"role={ent.role}")
        if ent.attrs:
            shown = {k: v for k, v in ent.attrs.items() if v}
            if shown:
                bits.append(f"attrs={shown}")
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        lines.append(f"  {ent.id:8} ({ent.type:10}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Curated set
# ---------------------------------------------------------------------------
CURATED = [
    StoryParams(
        place="attic",
        creature="rabbit_kit",
        hiding="wicker_basket",
        response="flashlight_towel",
        name="Nora",
        gender="girl",
        adult="grandfather",
        impulse=False,
    ),
    StoryParams(
        place="greenhouse",
        creature="hamster",
        hiding="seed_sack",
        response="gloves_and_basket",
        name="Ben",
        gender="boy",
        adult="grandmother",
        impulse=True,
    ),
    StoryParams(
        place="shed",
        creature="mouse",
        hiding="hat_box",
        response="flashlight_towel",
        name="Maya",
        gender="girl",
        adult="father",
        impulse=True,
    ),
    StoryParams(
        place="attic",
        creature="hamster",
        hiding="hat_box",
        response="treat_box",
        name="Theo",
        gender="boy",
        adult="mother",
        impulse=False,
    ),
]


# ---------------------------------------------------------------------------
# Rejection helpers
# ---------------------------------------------------------------------------
def explain_combo(creature: Creature, hiding: Hiding, setting: Setting) -> str:
    if hiding.id not in setting.affords:
        return (
            f"(No story: {hiding.phrase} does not belong in {setting.place} in this tiny world. "
            f"Choose a hiding place the setting actually affords.)"
        )
    if not fits(creature, hiding):
        return (
            f"(No story: {creature.label} is too big or wrong for {hiding.phrase}. "
            f"The mystery only works when the creature could plausibly fit there.)"
        )
    return "(No story: this combination does not form a plausible mystery.)"


def explain_response(response: Response, creature: Creature, hiding: Hiding) -> str:
    if response.sense < SENSE_MIN:
        return (
            f"(Refusing response '{response.id}': it scores too low on common sense "
            f"(sense={response.sense} < {SENSE_MIN}). A calm mystery should use safer help.)"
        )
    return (
        f"(No story: response '{response.id}' is not a good fit for a {creature.label} in {hiding.phrase}. "
        f"Pick a response that works for that creature and hiding place.)"
    )


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
valid_combo(P,C,H) :- setting(P), affords(P,H), creature(C), hiding(H), fits(C,H), has_sensible_response(C,H).

sensible_response(R) :- response(R), sense(R,S), sense_min(M), S >= M.
response_ok(C,H,R) :- sensible_response(R), works_for(R,C), works_in(R,K), hiding_kind(H,K), skittish(C,Sk), power(R,P), P >= Sk.
has_sensible_response(C,H) :- response_ok(C,H,_).

outcome(startled) :- impulse(1), chosen_creature(C), skittish(C,Sk), Sk >= 2.
outcome(careful)  :- not outcome(startled).
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for place_id, setting in SETTINGS.items():
        lines.append(asp.fact("setting", place_id))
        for hiding_id in sorted(setting.affords):
            lines.append(asp.fact("affords", place_id, hiding_id))
    for hiding_id, hiding in HIDINGS.items():
        lines.append(asp.fact("hiding", hiding_id))
        lines.append(asp.fact("hiding_kind", hiding_id, hiding.kind))
        for size in sorted(hiding.fits):
            lines.append(asp.fact("fits", "_".join([hiding_id, size])))

    for creature_id, creature in CREATURES.items():
        lines.append(asp.fact("creature", creature_id))
        lines.append(asp.fact("size_of", creature_id, creature.size))
        lines.append(asp.fact("skittish", creature_id, creature.skittish))

    for hiding_id, hiding in HIDINGS.items():
        for creature_id, creature in CREATURES.items():
            if fits(creature, hiding):
                lines.append(asp.fact("fits", creature_id, hiding_id))

    for response_id, response in RESPONSES.items():
        lines.append(asp.fact("response", response_id))
        lines.append(asp.fact("sense", response_id, response.sense))
        lines.append(asp.fact("power", response_id, response.power))
        for kind in sorted(response.works_in):
            lines.append(asp.fact("works_in", response_id, kind))
        for creature_id in sorted(response.works_for):
            lines.append(asp.fact("works_for", response_id, creature_id))

    lines.append(asp.fact("sense_min", SENSE_MIN))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("", "#show valid_combo/3."))
    return sorted(set(asp.atoms(model, "valid_combo")))


def asp_sensible_responses() -> list[str]:
    import asp

    model = asp.one_model(asp_program("", "#show sensible_response/1."))
    return sorted(r for (r,) in asp.atoms(model, "sensible_response"))


def asp_outcome(params: StoryParams) -> str:
    import asp

    extra = "\n".join([
        asp.fact("chosen_creature", params.creature),
        asp.fact("impulse", 1 if params.impulse else 0),
    ])
    model = asp.one_model(asp_program(extra, "#show outcome/1."))
    atoms = asp.atoms(model, "outcome")
    return atoms[0][0] if atoms else "?"


def asp_verify() -> int:
    rc = 0

    py_valid = set(valid_combos())
    asp_valid = set(asp_valid_combos())
    if py_valid == asp_valid:
        print(f"OK: valid_combo parity matches ({len(py_valid)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos:")
        if py_valid - asp_valid:
            print("  only in python:", sorted(py_valid - asp_valid))
        if asp_valid - py_valid:
            print("  only in clingo:", sorted(asp_valid - py_valid))

    py_sensible = {r.id for r in RESPONSES.values() if r.sense >= SENSE_MIN}
    asp_sensible = set(asp_sensible_responses())
    if py_sensible == asp_sensible:
        print(f"OK: sensible responses match ({sorted(py_sensible)}).")
    else:
        rc = 1
        print(f"MISMATCH in sensible responses: python={sorted(py_sensible)} clingo={sorted(asp_sensible)}")

    cases = list(CURATED)
    parser = build_parser()
    for seed in range(40):
        try:
            params = resolve_params(parser.parse_args([]), random.Random(seed))
        except StoryError:
            continue
        params.seed = seed
        cases.append(params)
    bad = 0
    for params in cases:
        if asp_outcome(params) != outcome_of(params):
            bad += 1
    if bad == 0:
        print(f"OK: outcome parity matches on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {bad}/{len(cases)} outcomes differ.")

    # Smoke test ordinary generation/emit.
    try:
        sample = generate(cases[0])
        buf = io.StringIO()
        old = sys.stdout
        sys.stdout = buf
        try:
            emit(sample, trace=True, qa=True, header="### smoke")
        finally:
            sys.stdout = old
        if not sample.story.strip():
            raise StoryError("empty story in smoke test")
        print("OK: generate()/emit() smoke test passed.")
    except Exception as err:  # pragma: no cover
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    return rc


# ---------------------------------------------------------------------------
# Standard interface
# ---------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Little mystery storyworld: a talkative child, a wobbling hiding place, and a safe reveal."
    )
    ap.add_argument("--place", choices=sorted(SETTINGS))
    ap.add_argument("--creature", choices=sorted(CREATURES))
    ap.add_argument("--hiding", choices=sorted(HIDINGS))
    ap.add_argument("--response", choices=sorted(RESPONSES))
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--adult", choices=["mother", "father", "grandmother", "grandfather"])
    ap.add_argument("--name")
    ap.add_argument("--impulse", action="store_true", help="make the child edge too close before stopping")
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list the compatible-story set derived by clingo")
    ap.add_argument("--verify", action="store_true", help="check the inline ASP reasoner matches the Python logic")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.place and args.hiding:
        setting = SETTINGS[args.place]
        hiding = HIDINGS[args.hiding]
        creature = CREATURES[args.creature] if args.creature else next(iter(CREATURES.values()))
        if args.hiding not in setting.affords:
            raise StoryError(explain_combo(creature, hiding, setting))

    if args.creature and args.hiding and args.place:
        setting = SETTINGS[args.place]
        creature = CREATURES[args.creature]
        hiding = HIDINGS[args.hiding]
        if not fits(creature, hiding) or args.hiding not in setting.affords:
            raise StoryError(explain_combo(creature, hiding, setting))

    combos = [
        combo for combo in valid_combos()
        if (args.place is None or combo[0] == args.place)
        and (args.creature is None or combo[1] == args.creature)
        and (args.hiding is None or combo[2] == args.hiding)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    place, creature_id, hiding_id = rng.choice(sorted(combos))
    creature = CREATURES[creature_id]
    hiding = HIDINGS[hiding_id]

    good_responses = [r.id for r in suitable_responses(creature, hiding)]
    if args.response:
        if args.response not in RESPONSES:
            raise StoryError("(Unknown response.)")
        response = RESPONSES[args.response]
        if args.response not in good_responses:
            raise StoryError(explain_response(response, creature, hiding))
        response_id = args.response
    else:
        response_id = rng.choice(sorted(good_responses))

    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    adult = args.adult or rng.choice(["mother", "father", "grandmother", "grandfather"])

    return StoryParams(
        place=place,
        creature=creature_id,
        hiding=hiding_id,
        response=response_id,
        name=name,
        gender=gender,
        adult=adult,
        impulse=bool(args.impulse or rng.choice([False, True])),
    )


def _need(mapping: dict, key: str, label: str):
    if key not in mapping:
        raise StoryError(f"(Unknown {label}: {key})")
    return mapping[key]


def generate(params: StoryParams) -> StorySample:
    setting = _need(SETTINGS, params.place, "place")
    creature = _need(CREATURES, params.creature, "creature")
    hiding = _need(HIDINGS, params.hiding, "hiding")
    response = _need(RESPONSES, params.response, "response")

    if params.hiding not in setting.affords or not fits(creature, hiding):
        raise StoryError(explain_combo(creature, hiding, setting))
    if response.id not in [r.id for r in suitable_responses(creature, hiding)]:
        raise StoryError(explain_response(response, creature, hiding))

    world = tell(
        setting=setting,
        hiding_cfg=hiding,
        creature_cfg=creature,
        response=response,
        child_name=params.name,
        child_type=params.gender,
        adult_type=params.adult,
        impulse=params.impulse,
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
        print(asp_program("", "#show valid_combo/3.\n#show sensible_response/1.\n#show outcome/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        sensible = asp_sensible_responses()
        print(f"sensible responses: {', '.join(sensible)}\n")
        print(f"{len(combos)} compatible (place, creature, hiding) combos:\n")
        for place, creature, hiding in combos:
            good = [r.id for r in suitable_responses(CREATURES[creature], HIDINGS[hiding])]
            print(f"  {place:10} {creature:11} {hiding:14} responses=[{', '.join(good)}]")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)

    if args.all:
        samples = [generate(params) for params in CURATED]
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
            print(json.dumps([sample.to_dict() for sample in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.name}: {p.creature} in {p.hiding} at {p.place} ({outcome_of(p)})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()

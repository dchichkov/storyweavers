#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/crate_cautionary_curiosity_kindness_ghost_story.py
=============================================================================

A small story world for a gentle ghost-story-shaped tale about a strange sound,
an old crate, and the discovery that kindness works better than fear.

Premise
-------
A child hears a spooky sound near an old crate in a dim place. Curiosity pulls
the child closer. A careful warning introduces the cautionary choice: rush in
the dark and make things worse, or bring light and help. The "ghost" turns out
to be a small trapped creature. The ending proves the change: what began as a
scary mystery becomes an act of kindness.

This script follows the storyworld contract:
- one standalone stdlib file
- eager import of results.py containers
- lazy import of asp.py in ASP helpers
- defines StoryParams, registries, build_parser, resolve_params, generate, emit, main
- supports default run, -n, --all, --seed, --trace, --qa, --json, --asp,
  --verify, and --show-asp
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
SENSE_MIN = 2


# ---------------------------------------------------------------------------
# Entities
# ---------------------------------------------------------------------------
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
    movable: bool = False
    fragile: bool = False
    alive: bool = False
    # physical and emotional state
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "woman"}
        male = {"boy", "father", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    @property
    def label_word(self) -> str:
        return {"mother": "mom", "father": "dad"}.get(self.type, self.type)


# ---------------------------------------------------------------------------
# Config registries
# ---------------------------------------------------------------------------
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
    spooky: str
    detail: str
    supports: set[str] = field(default_factory=set)
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
class Sound:
    id: str
    heard: str
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
class Occupant:
    id: str
    label: str
    phrase: str
    cry: str
    safe_place: str
    likes: str
    can_live_in: set[str] = field(default_factory=set)
    makes: set[str] = field(default_factory=set)
    tags: set[str] = field(default_factory=set)

    @property
    def article_label(self) -> str:
        first = self.label[0].lower()
        article = "an" if first in "aeiou" else "a"
        return f"{article} {self.label}"
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
    sense: int
    needs_light: bool
    gentle: bool
    power: int
    open_text: str
    calm_text: str
    qa_text: str
    fail_text: str
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


def _r_spook(world: World) -> list[str]:
    out: list[str] = []
    crate = world.get("crate")
    child = world.get("child")
    helper = world.get("helper")
    if crate.meters["mystery_noise"] < THRESHOLD:
        return out
    sig = ("spook",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    child.memes["fear"] += 1
    helper.memes["fear"] += 1
    out.append("__spooky__")
    return out


def _r_reveal(world: World) -> list[str]:
    out: list[str] = []
    crate = world.get("crate")
    occupant = world.get("occupant")
    if crate.meters["opened"] < THRESHOLD or occupant.meters["inside"] < THRESHOLD:
        return out
    sig = ("reveal",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    occupant.meters["visible"] += 1
    out.append("__reveal__")
    return out


def _r_kindness(world: World) -> list[str]:
    out: list[str] = []
    child = world.get("child")
    helper = world.get("helper")
    occupant = world.get("occupant")
    if occupant.meters["rescued"] < THRESHOLD:
        return out
    sig = ("kindness",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    child.memes["kindness"] += 1
    helper.memes["relief"] += 1
    child.memes["fear"] = 0.0
    helper.memes["fear"] = 0.0
    out.append("__kind__")
    return out


CAUSAL_RULES = [
    Rule(name="spook", tag="emotional", apply=_r_spook),
    Rule(name="reveal", tag="physical", apply=_r_reveal),
    Rule(name="kindness", tag="social", apply=_r_kindness),
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


# ---------------------------------------------------------------------------
# Reasonableness helpers
# ---------------------------------------------------------------------------
def plausible_combo(place: Place, sound: Sound, occupant: Occupant) -> bool:
    return occupant.id in place.supports and sound.id in occupant.makes and place.id in occupant.can_live_in


def sensible_methods() -> list[Method]:
    return [m for m in METHODS.values() if m.sense >= SENSE_MIN]


def outcome_for(method: Method) -> str:
    return "kind" if method.gentle and method.needs_light and method.power >= 2 else "startle"


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for place_id, place in PLACES.items():
        for sound_id, sound in SOUNDS.items():
            for occ_id, occ in OCCUPANTS.items():
                if plausible_combo(place, sound, occ):
                    combos.append((place_id, sound_id, occ_id))
    return combos


def explain_combo_rejection(place: Place, sound: Sound, occupant: Occupant) -> str:
    if place.id not in occupant.can_live_in:
        return (
            f"(No story: {occupant.article_label} does not plausibly hide in {place.label}. "
            f"Pick a place where that creature could really be.)"
        )
    if sound.id not in occupant.makes:
        return (
            f"(No story: {occupant.article_label} would not make {sound.heard}. "
            f"The spooky clue has to match the creature inside the crate.)"
        )
    return "(No story: this sound, place, and creature do not fit together.)"


def explain_method_rejection(method_id: str) -> str:
    method = METHODS[method_id]
    better = ", ".join(sorted(m.id for m in sensible_methods()))
    return (
        f"(Refusing method '{method_id}': it is too careless for this world "
        f"(sense={method.sense} < {SENSE_MIN}). Try one of: {better}.)"
    )


# ---------------------------------------------------------------------------
# Prediction
# ---------------------------------------------------------------------------
def predict_opening(world: World, method: Method) -> dict:
    sim = world.copy()
    crate = sim.get("crate")
    occupant = sim.get("occupant")
    if method.needs_light:
        sim.get("lamp").meters["on"] += 1
    crate.meters["opened"] += 1
    if not method.gentle:
        occupant.meters["startled"] += 1
    if method.gentle and method.needs_light and method.power >= 2:
        occupant.meters["rescued"] += 1
    propagate(sim, narrate=False)
    return {
        "rescued": occupant.meters["rescued"] >= THRESHOLD,
        "startled": occupant.meters["startled"] >= THRESHOLD,
        "visible": occupant.meters["visible"] >= THRESHOLD,
    }


# ---------------------------------------------------------------------------
# Verbs
# ---------------------------------------------------------------------------
def introduce(world: World, child: Entity, helper: Entity, place: Place) -> None:
    for person in (child, helper):
        person.memes["curiosity"] += 1
    world.say(
        f"One evening, {child.id} and {helper.id} climbed into {place.label}, where "
        f"{place.spooky}. {place.detail}"
    )


def hear_sound(world: World, child: Entity, helper: Entity, sound: Sound) -> None:
    crate = world.get("crate")
    crate.meters["mystery_noise"] += 1
    propagate(world, narrate=False)
    world.say(
        f"From behind an old crate came {sound.heard}. The sound was so strange that both children stopped moving at once."
    )
    world.say(
        f'{child.id} whispered, "Did you hear that?" and {helper.id} moved one step closer, even while clutching {helper.pronoun("possessive")} sleeves.'
    )


def wonder(world: World, child: Entity, helper: Entity) -> None:
    child.memes["curiosity"] += 1
    world.say(
        f"{child.id} felt scared, but curiosity tugged harder. {child.pronoun().capitalize()} wanted to know what was inside the crate."
    )
    world.say(
        f"{helper.id} did not laugh or tease. {helper.pronoun().capitalize()} stayed beside {child.id} and listened."
    )


def caution(world: World, child: Entity, helper: Entity, parent: Entity, method: Method) -> None:
    pred = predict_opening(world, method)
    world.facts["predicted_rescued"] = pred["rescued"]
    world.facts["predicted_startled"] = pred["startled"]
    helper.memes["care"] += 1
    if pred["rescued"]:
        line = (
            f'"Let\'s not yank it in the dark," {helper.id} said softly. '
            f'"We should call {parent.label_word} and bring the lamp first."'
        )
    else:
        line = (
            f'"Be careful," {helper.id} said. "If we rush, whatever is in there could get frightened."'
        )
    world.say(line)


def fetch_light(world: World, parent: Entity) -> None:
    lamp = world.get("lamp")
    lamp.meters["on"] += 1
    world.say(
        f"{parent.label_word.capitalize()} came with a warm lamp, and the soft circle of light pushed the shadows back from the crate."
    )


def open_crate(world: World, child: Entity, helper: Entity, method: Method) -> None:
    crate = world.get("crate")
    crate.meters["opened"] += 1
    if method.needs_light:
        world.say(method.open_text)
    else:
        world.say(method.fail_text)
    if not method.gentle:
        world.get("occupant").meters["startled"] += 1
        child.memes["fear"] += 1
        helper.memes["fear"] += 1
    propagate(world, narrate=False)


def reveal_occupant(world: World, occupant_cfg: Occupant) -> None:
    world.say(
        f"It was not a ghost at all. Inside the crate was {occupant_cfg.article_label}, {occupant_cfg.reveal}."
    )


def calm_and_help(world: World, child: Entity, helper: Entity, occupant_cfg: Occupant, method: Method) -> None:
    occupant = world.get("occupant")
    if outcome_for(method) == "kind":
        occupant.meters["rescued"] += 1
        world.say(method.calm_text.format(occupant=occupant_cfg.label))
        world.say(
            f"The little {occupant_cfg.label} made {occupant_cfg.cry} and leaned toward the gentle hands instead of away from them."
        )
    else:
        world.say(
            f"The creature gave {occupant_cfg.cry} and tried to shrink deeper into the crate. That made the children understand they needed to be gentler, not braver."
        )
        occupant.meters["rescued"] += 1
        world.say(
            f"With {world.get('parent').label_word}'s help, they slowed down, spoke softly, and lifted the crate lid the rest of the way without another sudden tug."
        )
        world.say(
            f"After that, {child.id} held still while {helper.id} offered a little space, and the frightened visitor finally crept out."
        )
    propagate(world, narrate=False)


def kind_ending(world: World, child: Entity, helper: Entity, occupant_cfg: Occupant) -> None:
    child.memes["lesson"] += 1
    helper.memes["lesson"] += 1
    world.say(
        f"They carried {occupant_cfg.article_label} to {occupant_cfg.safe_place}, where it could rest and feel safe again."
    )
    world.say(
        f'"I thought the crate was hiding a ghost," {child.id} admitted. "{child.pronoun().capitalize()} was really hiding someone who needed help."'
    )
    world.say(
        f"After that, whenever a room felt spooky, the children remembered to bring light, move slowly, and choose kindness before guesses."
    )


# ---------------------------------------------------------------------------
# Screenplay
# ---------------------------------------------------------------------------
def tell(
    place: Place,
    sound: Sound,
    occupant_cfg: Occupant,
    method: Method,
    child_name: str = "Nora",
    child_gender: str = "girl",
    helper_name: str = "Ben",
    helper_gender: str = "boy",
    parent_type: str = "mother",
    trait: str = "careful",
) -> World:
    world = World()
    child = world.add(Entity(
        id=child_name,
        kind="character",
        type=child_gender,
        role="child",
        traits=["curious"],
        attrs={"trait": trait},
    ))
    helper = world.add(Entity(
        id=helper_name,
        kind="character",
        type=helper_gender,
        role="helper",
        traits=[trait],
        attrs={"trait": trait},
    ))
    parent = world.add(Entity(
        id="Parent",
        kind="character",
        type=parent_type,
        role="parent",
        label="the parent",
    ))
    crate = world.add(Entity(
        id="crate",
        type="crate",
        label="crate",
        movable=True,
        fragile=True,
    ))
    lamp = world.add(Entity(
        id="lamp",
        type="lamp",
        label="lamp",
        movable=True,
    ))
    occupant = world.add(Entity(
        id="occupant",
        type=occupant_cfg.id,
        label=occupant_cfg.label,
        alive=True,
        movable=True,
        attrs={"likes": occupant_cfg.likes},
    ))

    occupant.meters["inside"] = 1.0
    crate.meters["mystery_noise"] = 0.0
    crate.meters["opened"] = 0.0
    occupant.meters["visible"] = 0.0
    occupant.meters["rescued"] = 0.0
    occupant.meters["startled"] = 0.0
    lamp.meters["on"] = 0.0
    child.memes["fear"] = 0.0
    helper.memes["fear"] = 0.0
    child.memes["curiosity"] = 0.0
    helper.memes["care"] = 0.0

    world.facts.update(
        place=place,
        sound=sound,
        occupant_cfg=occupant_cfg,
        method=method,
        child=child,
        helper=helper,
        parent=parent,
        crate=crate,
        lamp=lamp,
        occupant=occupant,
    )

    introduce(world, child, helper, place)
    hear_sound(world, child, helper, sound)
    world.para()
    wonder(world, child, helper)
    caution(world, child, helper, parent, method)
    world.para()
    if method.needs_light:
        fetch_light(world, parent)
    open_crate(world, child, helper, method)
    reveal_occupant(world, occupant_cfg)
    world.para()
    calm_and_help(world, child, helper, occupant_cfg, method)
    kind_ending(world, child, helper, occupant_cfg)

    world.facts.update(
        outcome=outcome_for(method),
        revealed=occupant.meters["visible"] >= THRESHOLD,
        rescued=occupant.meters["rescued"] >= THRESHOLD,
        startled=occupant.meters["startled"] >= THRESHOLD,
        lamp_on=lamp.meters["on"] >= THRESHOLD,
    )
    return world


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------
PLACES = {
    "attic": Place(
        id="attic",
        label="the attic",
        spooky="the rafters clicked and the air smelled of dust and old wood",
        detail="Moonlight slipped through one round window and drew a pale stripe over the floorboards.",
        supports={"kitten", "owl"},
        tags={"attic", "ghost"},
    ),
    "shed": Place(
        id="shed",
        label="the garden shed",
        spooky="rain tapped the roof and garden tools made long, crooked shadows",
        detail="A thin silver beam came through the crack under the door.",
        supports={"kitten", "hedgehog"},
        tags={"shed", "ghost"},
    ),
    "barn_loft": Place(
        id="barn_loft",
        label="the barn loft",
        spooky="hay rustled softly and the dark corners looked deep enough to hide stories",
        detail="The ladder creaked under their feet, and every board seemed to whisper when they stepped on it.",
        supports={"owl", "kitten"},
        tags={"barn", "ghost"},
    ),
}

SOUNDS = {
    "scratching": Sound(
        id="scratching",
        heard="a thin scratching and shuffling",
        reveal="blinking in the lamplight with wide, worried eyes",
        tags={"sound", "mystery"},
    ),
    "tiny_cry": Sound(
        id="tiny_cry",
        heard="a tiny crying sound, almost like a ghostly sigh",
        reveal="curled against one corner and looking tired",
        tags={"sound", "mystery"},
    ),
    "soft_thump": Sound(
        id="soft_thump",
        heard="a soft thump, then another, as if something small bumped the wood from inside",
        reveal="ruffling itself and peering out through the gloom",
        tags={"sound", "mystery"},
    ),
}

OCCUPANTS = {
    "kitten": Occupant(
        id="kitten",
        label="kitten",
        phrase="a little kitten",
        cry="a shaky mew",
        safe_place="a basket by the stove",
        likes="warm milk",
        can_live_in={"attic", "shed", "barn_loft"},
        makes={"scratching", "tiny_cry"},
        tags={"kitten", "animal", "kindness"},
    ),
    "owl": Occupant(
        id="owl",
        label="owl chick",
        phrase="a fluffy owl chick",
        cry="a soft peeping call",
        safe_place="a quiet nest box in the barn",
        likes="quiet corners",
        can_live_in={"attic", "barn_loft"},
        makes={"soft_thump", "scratching"},
        tags={"owl", "animal", "kindness"},
    ),
    "hedgehog": Occupant(
        id="hedgehog",
        label="hedgehog",
        phrase="a round little hedgehog",
        cry="a tiny snuffle",
        safe_place="a nest of dry leaves by the wall",
        likes="fallen leaves",
        can_live_in={"shed"},
        makes={"scratching", "soft_thump"},
        tags={"hedgehog", "animal", "kindness"},
    ),
}

METHODS = {
    "lamp_and_gloves": Method(
        id="lamp_and_gloves",
        sense=3,
        needs_light=True,
        gentle=True,
        power=3,
        open_text="Their parent helped them pull on work gloves, and together they lifted the crate lid slowly, with the lamp shining into every corner.",
        calm_text="Keeping their voices low, they made a small safe gap and waited until the {occupant} could see there was nothing to fear.",
        qa_text="They brought a lamp, moved slowly, and opened the crate gently with help.",
        fail_text="",
        tags={"lamp", "gentle"},
    ),
    "lamp_only": Method(
        id="lamp_only",
        sense=2,
        needs_light=True,
        gentle=True,
        power=2,
        open_text="With the lamp held close, they raised the crate lid inch by inch, listening instead of grabbing.",
        calm_text="They spoke in soft voices and gave the {occupant} time to stop trembling.",
        qa_text="They used a lamp and opened the crate inch by inch.",
        fail_text="",
        tags={"lamp", "gentle"},
    ),
    "yank_in_dark": Method(
        id="yank_in_dark",
        sense=1,
        needs_light=False,
        gentle=False,
        power=1,
        open_text="",
        calm_text="",
        qa_text="They yanked the crate open in the dark.",
        fail_text="Before anyone brought a light, they gave the crate lid a fast tug in the dark, and the sudden noise made the whole place feel even more haunted.",
        tags={"careless"},
    ),
}

GIRL_NAMES = ["Nora", "Lily", "Maya", "Ella", "Ivy", "Rose", "Anna", "Zoe"]
BOY_NAMES = ["Ben", "Theo", "Finn", "Max", "Sam", "Eli", "Noah", "Jack"]
TRAITS = ["careful", "gentle", "thoughtful", "kind", "steady"]


# ---------------------------------------------------------------------------
# Story params
# ---------------------------------------------------------------------------
@dataclass
class StoryParams:
    place: str
    sound: str
    occupant: str
    method: str
    child_name: str
    child_gender: str
    helper_name: str
    helper_gender: str
    parent: str
    trait: str
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# Q&A
# ---------------------------------------------------------------------------
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
    "ghost": [(
        "Why can a dark room feel spooky?",
        "In a dark room, your eyes cannot see clearly, so small sounds and shadows can seem bigger and stranger than they really are. Light helps you understand what is actually there."
    )],
    "lamp": [(
        "Why is a lamp helpful when you hear a strange sound?",
        "A lamp helps you see clearly before you touch anything. That makes it easier to act carefully and not scare or hurt a hidden animal."
    )],
    "kitten": [(
        "What should you do if you find a trapped kitten?",
        "Move gently and call a grown-up to help. A scared kitten needs calm voices and a safe place, not sudden grabbing."
    )],
    "owl": [(
        "Why should you be gentle with a baby owl?",
        "A baby owl can be frightened very easily. Quiet movements and grown-up help keep it safer."
    )],
    "hedgehog": [(
        "Why should you be careful around a hedgehog?",
        "A hedgehog is small and can curl up when it feels unsafe. Gentle help lets it calm down instead of staying frightened."
    )],
    "kindness": [(
        "What does kindness look like when something is scared?",
        "Kindness means slowing down, making things feel safe, and helping instead of forcing. A soft voice and patient hands can matter a lot."
    )],
}
KNOWLEDGE_ORDER = ["ghost", "lamp", "kitten", "owl", "hedgehog", "kindness"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    child = f["child"]
    helper = f["helper"]
    place = f["place"]
    occupant_cfg = f["occupant_cfg"]
    return [
        'Write a short ghost-story-style tale for a 3-to-5-year-old that includes the word "crate" and turns a spooky mystery into an act of kindness.',
        f"Tell a gentle cautionary story where {child.id} and {helper.id} hear a strange sound in {place.label}, fear it might be a ghost, and discover {occupant_cfg.article_label} instead.",
        "Write a story about curiosity, caution, and kindness, where bringing light and moving slowly matters more than acting brave in the dark.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    child = f["child"]
    helper = f["helper"]
    parent = f["parent"]
    place = f["place"]
    sound = f["sound"]
    occupant_cfg = f["occupant_cfg"]
    method = f["method"]
    outcome = f["outcome"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {child.id} and {helper.id}, two children who heard a strange sound near an old crate in {place.label}. Their {parent.label_word} helped them when the mystery grew too spooky to handle alone."
        ),
        (
            "Why did the crate seem scary at first?",
            f"The crate seemed scary because {sound.heard} came from behind it in a dim, creaky place. In the dark, the children could not tell whether the sound was a ghost story sort of mystery or something real."
        ),
        (
            f"Why was {helper.id} being careful?",
            f"{helper.id} wanted to protect whatever was inside the crate as well as {child.id}. The careful warning matters because rushing in the dark can frighten a trapped animal and make a spooky moment worse."
        ),
    ]
    if outcome == "kind":
        qa.append((
            "How did they solve the mystery?",
            f"They used {method.qa_text.lower()} Then they saw {occupant_cfg.article_label} instead of a ghost. The light and slow hands turned fear into understanding."
        ))
    else:
        qa.append((
            "What went wrong before things got better?",
            f"They tugged at the crate too fast in the dark, and the sudden noise frightened the creature inside. That mistake taught them that acting first is not the same as helping."
        ))
    qa.append((
        "What did the children learn?",
        f"They learned that curiosity should walk with caution, not run ahead alone. They also learned that when something sounds strange and scared, kindness is often the right answer."
    ))
    qa.append((
        "How did the story end?",
        f"It ended with {occupant_cfg.article_label} taken to {occupant_cfg.safe_place}. The final image shows that the spooky crate was no place for fear after all, but a place where kindness began."
    ))
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    occ = f["occupant_cfg"]
    tags = {"ghost", "kindness"}
    if f.get("lamp_on"):
        tags.add("lamp")
    tags |= set(occ.tags)
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
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if ent.attrs:
            shown = {k: v for k, v in ent.attrs.items() if v}
            if shown:
                bits.append(f"attrs={shown}")
        flags = [name for name, on in (("movable", ent.movable), ("fragile", ent.fragile), ("alive", ent.alive)) if on]
        if flags:
            bits.append(f"flags={flags}")
        lines.append(f"  {ent.id:9} ({ent.type:10}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Curated
# ---------------------------------------------------------------------------
CURATED = [
    StoryParams(
        place="attic",
        sound="tiny_cry",
        occupant="kitten",
        method="lamp_and_gloves",
        child_name="Nora",
        child_gender="girl",
        helper_name="Ben",
        helper_gender="boy",
        parent="mother",
        trait="careful",
    ),
    StoryParams(
        place="barn_loft",
        sound="soft_thump",
        occupant="owl",
        method="lamp_only",
        child_name="Theo",
        child_gender="boy",
        helper_name="Maya",
        helper_gender="girl",
        parent="father",
        trait="steady",
    ),
    StoryParams(
        place="shed",
        sound="scratching",
        occupant="hedgehog",
        method="lamp_only",
        child_name="Rose",
        child_gender="girl",
        helper_name="Finn",
        helper_gender="boy",
        parent="mother",
        trait="gentle",
    ),
]


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
% plausible mystery
plausible(P, S, O) :- place(P), sound(S), occupant(O), supports(P, O), lives_in(O, P), makes(O, S).

% sensible methods
sensible(M) :- method(M), sense(M, V), sense_min(Min), V >= Min.

% simple outcome model
kind(M)    :- method(M), gentle(M), needs_light(M), power(M, P), P >= 2.
startle(M) :- method(M), not kind(M).

outcome(M, kind)    :- kind(M).
outcome(M, startle) :- startle(M).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for place_id, place in PLACES.items():
        lines.append(asp.fact("place", place_id))
        for occ in sorted(place.supports):
            lines.append(asp.fact("supports", place_id, occ))
    for sound_id in SOUNDS:
        lines.append(asp.fact("sound", sound_id))
    for occ_id, occ in OCCUPANTS.items():
        lines.append(asp.fact("occupant", occ_id))
        for place_id in sorted(occ.can_live_in):
            lines.append(asp.fact("lives_in", occ_id, place_id))
        for sound_id in sorted(occ.makes):
            lines.append(asp.fact("makes", occ_id, sound_id))
    for method_id, method in METHODS.items():
        lines.append(asp.fact("method", method_id))
        lines.append(asp.fact("sense", method_id, method.sense))
        if method.needs_light:
            lines.append(asp.fact("needs_light", method_id))
        if method.gentle:
            lines.append(asp.fact("gentle", method_id))
        lines.append(asp.fact("power", method_id, method.power))
    lines.append(asp.fact("sense_min", SENSE_MIN))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show plausible/3."))
    return sorted(set(asp.atoms(model, "plausible")))


def asp_sensible_methods() -> list[str]:
    import asp
    model = asp.one_model(asp_program("", "#show sensible/1."))
    return sorted(m for (m,) in asp.atoms(model, "sensible"))


def asp_outcome(method_id: str) -> str:
    import asp
    model = asp.one_model(asp_program("", f"#show outcome/2."))
    outs = {m: o for (m, o) in asp.atoms(model, "outcome")}
    return outs.get(method_id, "?")


def asp_verify() -> int:
    rc = 0
    py_set = set(valid_combos())
    asp_set = set(asp_valid_combos())
    if py_set == asp_set:
        print(f"OK: gate matches valid_combos() ({len(py_set)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos:")
        if asp_set - py_set:
            print("  only in clingo:", sorted(asp_set - py_set))
        if py_set - asp_set:
            print("  only in python:", sorted(py_set - asp_set))

    py_methods = {m.id for m in sensible_methods()}
    asp_methods = set(asp_sensible_methods())
    if py_methods == asp_methods:
        print(f"OK: sensible methods match ({sorted(py_methods)}).")
    else:
        rc = 1
        print(f"MISMATCH in sensible methods: clingo={sorted(asp_methods)} python={sorted(py_methods)}")

    bad = 0
    for method_id, method in METHODS.items():
        if asp_outcome(method_id) != outcome_for(method):
            bad += 1
    if bad == 0:
        print(f"OK: outcome model matches Python on {len(METHODS)} methods.")
    else:
        rc = 1
        print(f"MISMATCH: {bad}/{len(METHODS)} method outcomes differ.")

    # smoke test: normal story generation and rendering must not crash
    try:
        sample = generate(CURATED[0])
        if not sample.story.strip():
            raise StoryError("Generated empty story in smoke test.")
        emit(sample, trace=False, qa=False, header="### smoke test")
        print("OK: smoke test generate/emit passed.")
    except Exception as err:  # pragma: no cover - verification path
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")
    return rc


# ---------------------------------------------------------------------------
# Interface
# ---------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Gentle ghost-story storyworld: a spooky crate, curiosity, caution, and kindness."
    )
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--sound", choices=SOUNDS)
    ap.add_argument("--occupant", choices=OCCUPANTS)
    ap.add_argument("--method", choices=METHODS)
    ap.add_argument("--parent", choices=["mother", "father"])
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list compatible story combos from clingo")
    ap.add_argument("--verify", action="store_true", help="check ASP/Python parity and run a smoke test")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def _pick_name(rng: random.Random, gender: str, avoid: str = "") -> str:
    pool = GIRL_NAMES if gender == "girl" else BOY_NAMES
    choices = [name for name in pool if name != avoid]
    return rng.choice(choices)


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.place and args.sound and args.occupant:
        place = PLACES[args.place]
        sound = SOUNDS[args.sound]
        occupant = OCCUPANTS[args.occupant]
        if not plausible_combo(place, sound, occupant):
            raise StoryError(explain_combo_rejection(place, sound, occupant))
    if args.method and METHODS[args.method].sense < SENSE_MIN:
        raise StoryError(explain_method_rejection(args.method))

    combos = [
        combo for combo in valid_combos()
        if (args.place is None or combo[0] == args.place)
        and (args.sound is None or combo[1] == args.sound)
        and (args.occupant is None or combo[2] == args.occupant)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    place_id, sound_id, occupant_id = rng.choice(sorted(combos))
    method_id = args.method or rng.choice(sorted(m.id for m in sensible_methods()))
    child_gender = rng.choice(["girl", "boy"])
    helper_gender = rng.choice(["girl", "boy"])
    child_name = _pick_name(rng, child_gender)
    helper_name = _pick_name(rng, helper_gender, avoid=child_name)
    parent = args.parent or rng.choice(["mother", "father"])
    trait = rng.choice(TRAITS)
    return StoryParams(
        place=place_id,
        sound=sound_id,
        occupant=occupant_id,
        method=method_id,
        child_name=child_name,
        child_gender=child_gender,
        helper_name=helper_name,
        helper_gender=helper_gender,
        parent=parent,
        trait=trait,
    )


def generate(params: StoryParams) -> StorySample:
    if params.place not in PLACES:
        raise StoryError(f"(Unknown place: {params.place})")
    if params.sound not in SOUNDS:
        raise StoryError(f"(Unknown sound: {params.sound})")
    if params.occupant not in OCCUPANTS:
        raise StoryError(f"(Unknown occupant: {params.occupant})")
    if params.method not in METHODS:
        raise StoryError(f"(Unknown method: {params.method})")

    place = PLACES[params.place]
    sound = SOUNDS[params.sound]
    occupant = OCCUPANTS[params.occupant]
    method = METHODS[params.method]

    if not plausible_combo(place, sound, occupant):
        raise StoryError(explain_combo_rejection(place, sound, occupant))
    if method.sense < SENSE_MIN:
        raise StoryError(explain_method_rejection(params.method))

    world = tell(
        place=place,
        sound=sound,
        occupant_cfg=occupant,
        method=method,
        child_name=params.child_name,
        child_gender=params.child_gender,
        helper_name=params.helper_name,
        helper_gender=params.helper_gender,
        parent_type=params.parent,
        trait=params.trait,
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
        print(asp_program("", "#show plausible/3.\n#show sensible/1.\n#show outcome/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        methods = asp_sensible_methods()
        print(f"sensible methods: {', '.join(methods)}\n")
        print(f"{len(combos)} compatible (place, sound, occupant) combos:\n")
        for place, sound, occupant in combos:
            print(f"  {place:10} {sound:11} {occupant}")
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
            header = f"### {p.child_name} & {p.helper_name}: {p.occupant} in a crate at {p.place}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()

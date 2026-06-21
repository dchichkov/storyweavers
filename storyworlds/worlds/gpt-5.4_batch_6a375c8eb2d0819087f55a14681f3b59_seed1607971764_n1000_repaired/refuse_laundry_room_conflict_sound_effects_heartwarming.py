#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/refuse_laundry_room_conflict_sound_effects_heartwarming.py
=====================================================================================

A standalone story world for a heartwarming laundry-room conflict: a child helping
with wash day keeps a treasure hidden in a pocket, refuses to empty it, and the
washer's noisy start turns the disagreement into a real problem. The storyworld
models pocket size, keepsake fragility, safe storage, and how quickly a grown-up
responds once the machine begins.

Run it
------
    python storyworlds/worlds/gpt-5.4/refuse_laundry_room_conflict_sound_effects_heartwarming.py
    python storyworlds/worlds/gpt-5.4/refuse_laundry_room_conflict_sound_effects_heartwarming.py --keepsake drawing --garment hoodie
    python storyworlds/worlds/gpt-5.4/refuse_laundry_room_conflict_sound_effects_heartwarming.py --keepsake shell
    python storyworlds/worlds/gpt-5.4/refuse_laundry_room_conflict_sound_effects_heartwarming.py --all
    python storyworlds/worlds/gpt-5.4/refuse_laundry_room_conflict_sound_effects_heartwarming.py -n 5 --seed 7 --qa
    python storyworlds/worlds/gpt-5.4/refuse_laundry_room_conflict_sound_effects_heartwarming.py --verify
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
STUBBORN_INIT = 5.0
CALM_PATIENCE_BONUS = 2.0


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
    owner: Optional[str] = None
    container: Optional[str] = None
    pocket_size: int = 0
    flat_only: bool = False
    water_sensitive: int = 0
    safe_for: set[str] = field(default_factory=set)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman"}
        male = {"boy", "father", "dad", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    @property
    def label_word(self) -> str:
        return {"mother": "mom", "father": "dad"}.get(self.type, self.type)
    @property
    def tags(self):
        if not hasattr(self, "_tags"):
            object.__setattr__(self, "_tags", set())
        return self._tags


@dataclass
class Garment:
    id: str
    label: str
    phrase: str
    pocket_size: int
    swish: str
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
class Keepsake:
    id: str
    label: str
    phrase: str
    size: int
    form: str
    water_sensitive: int
    rescue_verb: str
    remade_as: str
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
class SafePlace:
    id: str
    label: str
    phrase: str
    accepts: set[str]
    room_spot: str
    ending_line: str
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
class Washer:
    id: str
    label: str
    start_sound: str
    slosh_sound: str
    pause_sound: str
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
class Response:
    id: str
    sense: int
    speed: int
    text: str
    fail: str
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


def _r_running_soaks(world: World) -> list[str]:
    washer = world.get("washer")
    keepsake = world.get("keepsake")
    garment = world.get("garment")
    if washer.meters["running"] < THRESHOLD:
        return []
    if garment.container != "washer" or keepsake.container != "garment":
        return []
    sig = ("soak", keepsake.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    keepsake.meters["wet"] += 1
    return ["__wet__"]


def _r_damage(world: World) -> list[str]:
    keepsake = world.get("keepsake")
    if keepsake.meters["wet"] < THRESHOLD:
        return []
    sig = ("damage", keepsake.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    delay = int(world.facts.get("delay", 0))
    response = world.facts.get("response_cfg")
    response_speed = response.speed if response else 0
    severity = max(0, keepsake.water_sensitive + delay - response_speed)
    keepsake.meters["damage"] += float(severity)
    if severity:
        keepsake.memes["loss"] += 1
        child = world.get("child")
        child.memes["sadness"] += 1
        child.memes["fear"] += 1
    return []


def _r_saved_relief(world: World) -> list[str]:
    keepsake = world.get("keepsake")
    if keepsake.meters["saved"] < THRESHOLD:
        return []
    sig = ("relief", keepsake.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    child = world.get("child")
    parent = world.get("parent")
    child.memes["relief"] += 1
    child.memes["trust"] += 1
    parent.memes["care"] += 1
    return []


CAUSAL_RULES: list[Rule] = [
    Rule(name="running_soaks", tag="physical", apply=_r_running_soaks),
    Rule(name="damage", tag="physical", apply=_r_damage),
    Rule(name="saved_relief", tag="emotional", apply=_r_saved_relief),
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


def fits_in_pocket(garment: Garment, keepsake: Keepsake) -> bool:
    return keepsake.size <= garment.pocket_size


def safe_place_works(keepsake: Keepsake, safe_place: SafePlace) -> bool:
    return keepsake.form in safe_place.accepts


def at_risk(garment: Garment, keepsake: Keepsake) -> bool:
    return fits_in_pocket(garment, keepsake) and keepsake.water_sensitive > 0


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for garment_id, garment in GARMENTS.items():
        for keepsake_id, keepsake in KEEPSAKES.items():
            for safe_id, safe_place in SAFE_PLACES.items():
                if at_risk(garment, keepsake) and safe_place_works(keepsake, safe_place):
                    combos.append((garment_id, keepsake_id, safe_id))
    return combos


def sensible_responses() -> list[Response]:
    return [r for r in RESPONSES.values() if r.sense >= SENSE_MIN]


def trouble_severity(keepsake: Keepsake, delay: int) -> int:
    return keepsake.water_sensitive + delay


def is_rescued(response: Response, keepsake: Keepsake, delay: int) -> bool:
    return response.speed >= trouble_severity(keepsake, delay)


def would_relent(attachment: int, patience: str) -> bool:
    patience_bonus = CALM_PATIENCE_BONUS if patience == "calm" else 0.0
    return float(attachment) + patience_bonus > STUBBORN_INIT


def predict_wash(world: World) -> dict:
    sim = world.copy()
    sim.get("garment").container = "washer"
    sim.get("washer").meters["running"] = 1
    propagate(sim, narrate=False)
    keepsake = sim.get("keepsake")
    return {
        "wet": keepsake.meters["wet"] >= THRESHOLD,
        "damage": keepsake.meters["damage"],
    }


def introduce(world: World, child: Entity, parent: Entity, garment: Garment, keepsake: Keepsake) -> None:
    child.memes["joy"] += 1
    keepsake.memes["beloved"] += 1
    world.say(
        f"On laundry day, {child.id} padded into the laundry room beside "
        f"{child.pronoun('possessive')} {parent.label_word} and helped make little piles of clothes."
    )
    world.say(
        f"In the pocket of {garment.phrase}, {child.pronoun()} had tucked {keepsake.phrase}, "
        f"because keeping it close made the chore feel special."
    )


def sounds_and_setup(world: World, washer: Washer, garment: Garment) -> None:
    world.say(
        f"The room was full of cozy machine sounds already: {washer.start_sound.lower()} from the washer door, "
        f"and the basket gave a soft {garment.swish.lower()} when someone lifted it."
    )


def ask_empty_pocket(world: World, parent: Entity, child: Entity, garment: Garment) -> None:
    child.memes["tension"] += 1
    world.say(
        f'"Before we wash {garment.label}, let\'s check the pockets," '
        f"{parent.label_word} said."
    )


def refuse(world: World, child: Entity, keepsake: Keepsake) -> None:
    child.memes["defiance"] += 1
    child.memes["stubborn"] = STUBBORN_INIT
    world.say(
        f'{child.id} closed {child.pronoun("possessive")} hand over the pocket and shook '
        f'{child.pronoun("possessive")} head. "No. I refuse. {keepsake.label.capitalize()} stays with me."'
    )


def explain_risk(world: World, parent: Entity, child: Entity, keepsake: Keepsake) -> None:
    pred = predict_wash(world)
    world.facts["predicted_damage"] = pred["damage"]
    world.say(
        f'{parent.label_word.capitalize()} knelt beside {child.id}. '
        f'"I know it matters to you," {parent.pronoun()} said softly. '
        f'"But if it rides through the wash, the water can spoil it."'
    )


def relent(world: World, child: Entity, parent: Entity, safe_place: SafePlace, keepsake: Keepsake) -> None:
    child.memes["relief"] += 1
    child.memes["trust"] += 1
    keepsake.container = "safe_place"
    world.say(
        f"{child.id} looked at the pocket, then at {parent.label_word}, and let out a tiny sigh."
    )
    world.say(
        f'Together they laid {keepsake.label} in {safe_place.phrase} {safe_place.room_spot}. '
        f'The argument melted into a quieter feeling right there in the warm room.'
    )


def slip_into_washer(world: World, child: Entity, garment: Entity, washer: Washer, keepsake: Keepsake) -> None:
    garment.container = "washer"
    world.get("washer").meters["running"] = 1
    world.say(
        f"But before the moment could settle, {garment.label} slipped in with the load. "
        f'"Click!" went the door. "{washer.start_sound}" went the button. '
        f'Soon came "{washer.slosh_sound}," and {child.id} went still.'
    )
    world.say(
        f"{child.id} remembered all at once that {keepsake.label} was still in the pocket."
    )


def rescue(world: World, parent: Entity, response: Response, washer: Washer, keepsake: Entity) -> None:
    world.get("washer").meters["running"] = 0
    keepsake.container = "parent_hand"
    keepsake.meters["saved"] += 1
    propagate(world, narrate=False)
    world.say(
        f"{parent.label_word.capitalize()} moved fast, {response.text}. "
        f'"{washer.pause_sound}," said the machine as it stopped.'
    )


def rescue_fail(world: World, parent: Entity, response: Response, washer: Washer, keepsake: Entity) -> None:
    world.get("washer").meters["running"] = 0
    keepsake.container = "parent_hand"
    propagate(world, narrate=False)
    world.say(
        f"{parent.label_word.capitalize()} hurried over and {response.fail}. "
        f'"{washer.pause_sound}," said the machine at last.'
    )


def comfort_saved(world: World, parent: Entity, child: Entity, keepsake: Keepsake, safe_place: SafePlace) -> None:
    child.memes["love"] += 1
    world.say(
        f'{parent.label_word.capitalize()} held up {keepsake.label}. It was damp, but safe. '
        f'{child.id} pressed close and laughed a shaky little laugh.'
    )
    world.say(
        f'Then they dried it together and set it in {safe_place.phrase} {safe_place.room_spot}, '
        f"where it could stay special without hiding in a pocket."
    )


def comfort_loss(world: World, parent: Entity, child: Entity, keepsake: Keepsake, safe_place: SafePlace) -> None:
    child.memes["love"] += 1
    child.memes["sadness"] += 1
    world.say(
        f"{parent.label_word.capitalize()} spread {keepsake.label} on a towel. "
        f"It came out wrinkled and blurred, and tears slid down {child.id}'s face."
    )
    world.say(
        f'"We can\'t make this very one new again," {parent.pronoun()} said, "but we can keep its story." '
        f'Together they made {keepsake.remade_as} and tucked it into {safe_place.phrase} {safe_place.room_spot}.'
    )


def ending_image(world: World, child: Entity, washer: Washer, safe_place: SafePlace) -> None:
    world.say(
        f"After that, every pocket got checked before the laundry started. "
        f"The washer still said {washer.start_sound!r}, but now the sound only meant clean clothes."
    )
    world.say(safe_place.ending_line.format(child=child.id))


def tell(
    garment_cfg: Garment,
    keepsake_cfg: Keepsake,
    safe_place_cfg: SafePlace,
    washer_cfg: Washer,
    response_cfg: Response,
    *,
    child_name: str = "Lina",
    child_gender: str = "girl",
    parent_type: str = "mother",
    patience: str = "calm",
    attachment: int = 4,
    delay: int = 0,
) -> World:
    world = World()
    child = world.add(Entity(
        id=child_name,
        kind="character",
        type=child_gender,
        role="child",
        traits=["helpful"],
        attrs={"patience": patience},
    ))
    parent = world.add(Entity(
        id="Parent",
        kind="character",
        type=parent_type,
        role="parent",
        label="the parent",
        attrs={"patience": patience},
    ))
    garment = world.add(Entity(
        id="garment",
        type="garment",
        label=garment_cfg.label,
        phrase=garment_cfg.phrase,
        pocket_size=garment_cfg.pocket_size,
        owner=child.id,
        container="basket",
    ))
    keepsake = world.add(Entity(
        id="keepsake",
        type="keepsake",
        label=keepsake_cfg.label,
        phrase=keepsake_cfg.phrase,
        owner=child.id,
        container="garment",
        flat_only=(keepsake_cfg.form == "flat"),
        water_sensitive=keepsake_cfg.water_sensitive,
        attrs={"form": keepsake_cfg.form},
    ))
    world.add(Entity(
        id="safe_place",
        type="safe_place",
        label=safe_place_cfg.label,
        phrase=safe_place_cfg.phrase,
        safe_for=set(safe_place_cfg.accepts),
    ))
    world.add(Entity(
        id="washer",
        type="washer",
        label=washer_cfg.label,
        attrs={
            "start_sound": washer_cfg.start_sound,
            "slosh_sound": washer_cfg.slosh_sound,
            "pause_sound": washer_cfg.pause_sound,
        },
    ))

    world.facts.update(
        garment_cfg=garment_cfg,
        keepsake_cfg=keepsake_cfg,
        safe_place_cfg=safe_place_cfg,
        washer_cfg=washer_cfg,
        response_cfg=response_cfg,
        delay=delay,
        child=child,
        parent=parent,
        garment=garment,
        keepsake=keepsake,
        patience=patience,
        attachment=attachment,
    )

    introduce(world, child, parent, garment_cfg, keepsake_cfg)
    sounds_and_setup(world, washer_cfg, garment_cfg)

    world.para()
    ask_empty_pocket(world, parent, child, garment_cfg)
    refuse(world, child, keepsake_cfg)
    explain_risk(world, parent, child, keepsake_cfg)

    relented = would_relent(attachment, patience)
    if relented:
        world.para()
        relent(world, child, parent, safe_place_cfg, keepsake_cfg)
        outcome = "averted"
    else:
        world.para()
        slip_into_washer(world, child, garment, washer_cfg, keepsake)
        propagate(world, narrate=False)
        saved = is_rescued(response_cfg, keepsake_cfg, delay)
        world.para()
        if saved:
            rescue(world, parent, response_cfg, washer_cfg, keepsake)
            comfort_saved(world, parent, child, keepsake_cfg, safe_place_cfg)
            outcome = "saved"
        else:
            rescue_fail(world, parent, response_cfg, washer_cfg, keepsake)
            comfort_loss(world, parent, child, keepsake_cfg, safe_place_cfg)
            outcome = "ruined"

    world.para()
    ending_image(world, child, washer_cfg, safe_place_cfg)

    world.facts.update(
        outcome=outcome,
        relented=relented,
        rescued=(outcome == "saved"),
        damaged=(world.get("keepsake").meters["damage"] >= THRESHOLD),
    )
    return world


GARMENTS = {
    "jeans": Garment(
        id="jeans",
        label="jeans",
        phrase="a pair of blue jeans",
        pocket_size=2,
        swish="swish-swish",
        tags={"pocket", "laundry"},
    ),
    "hoodie": Garment(
        id="hoodie",
        label="hoodie",
        phrase="a soft yellow hoodie",
        pocket_size=3,
        swish="fuff-fuff",
        tags={"pocket", "laundry"},
    ),
    "overalls": Garment(
        id="overalls",
        label="overalls",
        phrase="striped overalls",
        pocket_size=3,
        swish="shuff-shuff",
        tags={"pocket", "laundry"},
    ),
    "apron": Garment(
        id="apron",
        label="apron",
        phrase="a tiny apron",
        pocket_size=1,
        swish="flip-flap",
        tags={"pocket", "laundry"},
    ),
}

KEEPSAKES = {
    "drawing": Keepsake(
        id="drawing",
        label="the star drawing",
        phrase="a folded star drawing",
        size=2,
        form="flat",
        water_sensitive=3,
        rescue_verb="smoothed it out",
        remade_as="a new star drawing with the old one beside it",
        tags={"paper", "drawing"},
    ),
    "note": Keepsake(
        id="note",
        label="the thank-you note",
        phrase="a tiny thank-you note from Grandma",
        size=1,
        form="flat",
        water_sensitive=2,
        rescue_verb="dabbed it dry",
        remade_as="a copied note written together in careful letters",
        tags={"paper", "family_note"},
    ),
    "sticker_sheet": Keepsake(
        id="sticker_sheet",
        label="the sticker sheet",
        phrase="a shiny sticker sheet",
        size=2,
        form="flat",
        water_sensitive=3,
        rescue_verb="peeled it free",
        remade_as="a page of new stickers with one wrinkly old star saved on top",
        tags={"stickers", "paper"},
    ),
    "ribbon": Keepsake(
        id="ribbon",
        label="the race ribbon",
        phrase="a race ribbon from field day",
        size=3,
        form="soft",
        water_sensitive=1,
        rescue_verb="hung it to dry",
        remade_as="a ribbon tag with the date written underneath",
        tags={"ribbon", "school"},
    ),
    "shell": Keepsake(
        id="shell",
        label="the little shell",
        phrase="a little shell from the beach",
        size=1,
        form="tiny",
        water_sensitive=0,
        rescue_verb="rinsed it",
        remade_as="a tiny shell card",
        tags={"shell"},
    ),
}

SAFE_PLACES = {
    "memory_box": SafePlace(
        id="memory_box",
        label="memory box",
        phrase="a blue memory box",
        accepts={"flat", "soft", "tiny"},
        room_spot="on the shelf above the detergent",
        ending_line="{child} gave the box a gentle tap, and the laundry room felt like a safe place for stories too.",
        tags={"memory_box"},
    ),
    "clip_board": SafePlace(
        id="clip_board",
        label="clipboard",
        phrase="a clipboard with a bright clip",
        accepts={"flat"},
        room_spot="beside the washer",
        ending_line="Soon {child}'s paper treasures waited on the clipboard instead of inside wet pockets.",
        tags={"clipboard"},
    ),
    "hook": SafePlace(
        id="hook",
        label="wooden hook",
        phrase="a wooden hook",
        accepts={"soft"},
        room_spot="by the warm dryer",
        ending_line="{child} smiled every time the ribbon swayed from the hook like a tiny flag of being careful.",
        tags={"hook"},
    ),
    "jar": SafePlace(
        id="jar",
        label="treasure jar",
        phrase="a clear treasure jar",
        accepts={"tiny"},
        room_spot="next to the clothespins",
        ending_line="The little jar shone by the clothespins, and {child} never had to hide tiny treasures again.",
        tags={"jar"},
    ),
}

WASHERS = {
    "front_loader": Washer(
        id="front_loader",
        label="front-loader",
        start_sound="Beep-beep",
        slosh_sound="whoosh-whoosh",
        pause_sound="click-hummm",
        tags={"washer"},
    ),
    "old_washer": Washer(
        id="old_washer",
        label="old washer",
        start_sound="Thunk-thunk",
        slosh_sound="glug-glug",
        pause_sound="clack",
        tags={"washer"},
    ),
    "quiet_washer": Washer(
        id="quiet_washer",
        label="quiet washer",
        start_sound="Bip-bip",
        slosh_sound="swirl-shhh",
        pause_sound="tick",
        tags={"washer"},
    ),
}

RESPONSES = {
    "pause_and_open": Response(
        id="pause_and_open",
        sense=3,
        speed=3,
        text="pressed pause, opened the door, and reached in for the pocket before the wash could do much harm",
        fail="pressed pause and pulled the pocket out, but the keepsake had already gone mushy in the water",
        qa_text="pressed pause and opened the washer to get it out quickly",
        tags={"pause_button", "washer"},
    ),
    "drain_first": Response(
        id="drain_first",
        sense=2,
        speed=2,
        text="stopped the cycle, drained the water, and rescued the pocket with steady hands",
        fail="stopped the cycle and drained it, but by then the keepsake was already blurred and limp",
        qa_text="stopped the cycle and drained the washer before rescuing it",
        tags={"pause_button", "washer"},
    ),
    "poke_with_broom": Response(
        id="poke_with_broom",
        sense=1,
        speed=0,
        text="poked at the clothes with a broom handle until the pocket came near the door",
        fail="poked at the clothes with a broom handle, but that only wasted time",
        qa_text="tried to fish it out with a broom",
        tags={"broom"},
    ),
}

GIRL_NAMES = ["Lina", "Maya", "Ava", "Nora", "Lucy", "Zoe", "Ella", "Ruby"]
BOY_NAMES = ["Owen", "Ben", "Leo", "Max", "Theo", "Finn", "Sam", "Eli"]
PATIENCE = ["calm", "brisk"]
ATTACHMENTS = [2, 3, 4, 5, 6]

KNOWLEDGE = {
    "pocket": [(
        "Why should you check pockets before doing laundry?",
        "Pockets can hide paper, crayons, or little treasures. If they go through the wash, the clothes and the things inside can get messy or ruined."
    )],
    "washer": [(
        "What does a washing machine do?",
        "A washing machine swishes clothes through water and soap to get them clean. That is good for shirts and socks, but not for paper treasures."
    )],
    "pause_button": [(
        "What should a grown-up do if something important is left in the washer?",
        "A grown-up should stop the machine right away and get the item out safely. Acting quickly gives the item the best chance to stay okay."
    )],
    "paper": [(
        "Why does paper get ruined in water?",
        "Paper soaks up water very fast. When it gets too wet, it can tear, wrinkle, or the colors can blur."
    )],
    "drawing": [(
        "Why can a drawing feel special?",
        "A drawing can remind you of a happy moment or of someone you love. Even simple paper can feel important when it holds a memory."
    )],
    "family_note": [(
        "Why might someone keep a note from family?",
        "A note from family can feel like a tiny hug in your hand. People keep notes because the words help them remember love."
    )],
    "stickers": [(
        "Why do stickers not do well in the wash?",
        "Water and rubbing can make stickers peel, wrinkle, and stick to the wrong things. They are meant for dry places."
    )],
    "ribbon": [(
        "What is a ribbon from a race or school day?",
        "It is a soft prize or keepsake that helps someone remember trying hard or having a special day."
    )],
    "memory_box": [(
        "What is a memory box for?",
        "A memory box is a safe place to keep small treasures you want to remember. It helps special things stay safe instead of getting lost or washed."
    )],
    "clipboard": [(
        "Why put a paper treasure on a clipboard?",
        "A clipboard holds paper flat and dry where people can see it. That keeps it out of pockets and off the floor."
    )],
    "hook": [(
        "What is a hook good for in a laundry room?",
        "A hook can hold soft things like ribbons or little bags so they stay off the wet floor and out of the wash."
    )],
    "jar": [(
        "What is a treasure jar for?",
        "A treasure jar is a clear place to keep tiny objects like shells or buttons. You can see them without carrying them in your pockets."
    )],
}
KNOWLEDGE_ORDER = [
    "pocket", "washer", "pause_button", "paper", "drawing", "family_note",
    "stickers", "ribbon", "memory_box", "clipboard", "hook", "jar"
]


@dataclass
class StoryParams:
    garment: str
    keepsake: str
    safe_place: str
    washer: str
    response: str
    child_name: str
    child_gender: str
    parent: str
    patience: str
    attachment: int
    delay: int = 0
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
        garment="hoodie",
        keepsake="drawing",
        safe_place="clip_board",
        washer="front_loader",
        response="pause_and_open",
        child_name="Lina",
        child_gender="girl",
        parent="mother",
        patience="calm",
        attachment=6,
        delay=0,
    ),
    StoryParams(
        garment="jeans",
        keepsake="note",
        safe_place="memory_box",
        washer="old_washer",
        response="pause_and_open",
        child_name="Ben",
        child_gender="boy",
        parent="father",
        patience="brisk",
        attachment=3,
        delay=0,
    ),
    StoryParams(
        garment="overalls",
        keepsake="sticker_sheet",
        safe_place="clip_board",
        washer="quiet_washer",
        response="drain_first",
        child_name="Maya",
        child_gender="girl",
        parent="mother",
        patience="brisk",
        attachment=2,
        delay=2,
    ),
    StoryParams(
        garment="hoodie",
        keepsake="ribbon",
        safe_place="hook",
        washer="front_loader",
        response="drain_first",
        child_name="Theo",
        child_gender="boy",
        parent="father",
        patience="calm",
        attachment=4,
        delay=0,
    ),
]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    child = f["child"]
    keepsake_cfg = f["keepsake_cfg"]
    garment_cfg = f["garment_cfg"]
    outcome = f["outcome"]
    if outcome == "averted":
        return [
            f'Write a heartwarming story for a 3-to-5-year-old set in a laundry room that includes the word "refuse".',
            f"Tell a gentle conflict story where {child.id} refuses to empty {garment_cfg.label}'s pocket because {keepsake_cfg.label} feels too special, but a loving grown-up helps {child.pronoun('object')} choose a safe place for it.",
            "Write a story with washing-machine sound effects, a small disagreement, and an ending that shows a new careful habit.",
        ]
    if outcome == "saved":
        return [
            f'Write a heartwarming laundry-room story that includes the word "refuse" and sound effects from a washing machine.',
            f"Tell a story where {child.id} refuses to empty a pocket, the washer starts, and a calm grown-up saves the keepsake just in time.",
            "Write a gentle cautionary story with conflict, quick help, and a warm ending image in the laundry room.",
        ]
    return [
        f'Write a bittersweet but heartwarming story set in a laundry room that includes the word "refuse".',
        f"Tell a story where {child.id} refuses to empty a pocket, the washer starts with noisy sound effects, and a special keepsake is spoiled, but love helps turn the mistake into a new memory.",
        "Write a child-facing conflict story with concrete sounds, sadness, comfort, and a hopeful ending habit.",
    ]


def pair_answer_sentences(*sentences: str) -> str:
    return " ".join(s for s in sentences if s)


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    child = f["child"]
    parent = f["parent"]
    keepsake_cfg = f["keepsake_cfg"]
    garment_cfg = f["garment_cfg"]
    safe_place_cfg = f["safe_place_cfg"]
    response_cfg = f["response_cfg"]
    outcome = f["outcome"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            pair_answer_sentences(
                f"It is about {child.id} and {child.pronoun('possessive')} {parent.label_word} in the laundry room.",
                f"{child.id} was helping with clothes, but {keepsake_cfg.label} in the pocket made the chore feel important."
            ),
        ),
        (
            f"Why did {child.id} refuse to empty the pocket?",
            pair_answer_sentences(
                f"{child.id} refused because {keepsake_cfg.label} felt special and close in the pocket.",
                "The conflict began because the child wanted to keep the treasure nearby while the grown-up wanted to keep it safe."
            ),
        ),
        (
            "Why was the keepsake in danger?",
            pair_answer_sentences(
                f"It was in the pocket of {garment_cfg.label} while the laundry was about to be washed.",
                "Water in the washer could spoil it, which is why the warning mattered."
            ),
        ),
    ]
    if outcome == "averted":
        qa.append((
            f"What solved the problem before the washer started?",
            pair_answer_sentences(
                f"{child.id} finally listened and put {keepsake_cfg.label} in {safe_place_cfg.phrase}.",
                "That changed the mood because the treasure could stay safe without starting the wash-day problem."
            ),
        ))
    elif outcome == "saved":
        qa.append((
            f"How did {child.id}'s {parent.label_word} save the keepsake?",
            pair_answer_sentences(
                f"{parent.label_word.capitalize()} {response_cfg.qa_text}.",
                "The quick stop mattered because the washer had only just begun."
            ),
        ))
        qa.append((
            "How did the story end?",
            pair_answer_sentences(
                f"The keepsake was damp but safe, and they dried it together.",
                f"At the end it rested in {safe_place_cfg.phrase}, showing that the family had learned a kinder, safer habit."
            ),
        ))
    else:
        qa.append((
            "Was the keepsake all right after the wash started?",
            pair_answer_sentences(
                f"No. {keepsake_cfg.label.capitalize()} came out damaged and blurry.",
                "It had stayed in the pocket too long once the water began to swish around it."
            ),
        ))
        qa.append((
            "How could the ending still feel heartwarming?",
            pair_answer_sentences(
                f"{child.id}'s {parent.label_word} stayed gentle and helped make {keepsake_cfg.remade_as}.",
                "The old keepsake was hurt, but the love and the new careful habit stayed."
            ),
        ))
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags: set[str] = {"pocket", "washer"}
    f = world.facts
    keepsake_cfg = f["keepsake_cfg"]
    safe_place_cfg = f["safe_place_cfg"]
    response_cfg = f["response_cfg"]
    tags |= keepsake_cfg.tags
    tags |= safe_place_cfg.tags
    if f["outcome"] != "averted":
        tags |= response_cfg.tags
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
        if ent.container:
            bits.append(f"container={ent.container}")
        if ent.pocket_size:
            bits.append(f"pocket_size={ent.pocket_size}")
        if ent.water_sensitive:
            bits.append(f"water_sensitive={ent.water_sensitive}")
        if ent.attrs:
            shown = {k: v for k, v in ent.attrs.items() if v not in ("", None, False)}
            if shown:
                bits.append(f"attrs={shown}")
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        lines.append(f"  {ent.id:10} ({ent.type:10}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    return "\n".join(lines)


def explain_rejection(garment: Garment, keepsake: Keepsake, safe_place: Optional[SafePlace] = None) -> str:
    if not fits_in_pocket(garment, keepsake):
        return (
            f"(No story: {keepsake.label} is too big for the pocket in {garment.label}. "
            "If it cannot hide in the pocket, the laundry-room conflict does not happen.)"
        )
    if keepsake.water_sensitive <= 0:
        return (
            f"(No story: {keepsake.label} would not really be ruined by the wash. "
            "This world only tells stories where the hidden treasure is honestly at risk.)"
        )
    if safe_place is not None and not safe_place_works(keepsake, safe_place):
        return (
            f"(No story: {safe_place.label} is not a sensible safe place for {keepsake.label}. "
            "The ending solution must actually fit the kind of treasure being protected.)"
        )
    return "(No story: this combination does not make a reasonable laundry-room conflict.)"


def explain_response(rid: str) -> str:
    resp = RESPONSES[rid]
    better = ", ".join(sorted(r.id for r in sensible_responses()))
    return (
        f"(Refusing response '{rid}': it scores too low on common sense "
        f"(sense={resp.sense} < {SENSE_MIN}). Try one of: {better}.)"
    )


def outcome_of(params: StoryParams) -> str:
    if would_relent(params.attachment, params.patience):
        return "averted"
    response = RESPONSES[params.response]
    keepsake = KEEPSAKES[params.keepsake]
    return "saved" if is_rescued(response, keepsake, params.delay) else "ruined"


ASP_RULES = r"""
% --- valid combination gate -----------------------------------------------
at_risk(G, K) :- garment(G), keepsake(K), pocket_size(G, GP), keepsake_size(K, KS),
                 KS <= GP, water_sensitive(K, W), W > 0.
safe_for(K, S) :- keepsake_form(K, F), safe_place(S), accepts(S, F).
valid(G, K, S) :- at_risk(G, K), safe_for(K, S).

% --- outcome model ---------------------------------------------------------
patience_bonus(2) :- chosen_patience(calm).
patience_bonus(0) :- chosen_patience(brisk).
relent_score(A + B) :- chosen_attachment(A), patience_bonus(B).
relented :- relent_score(R), stubborn_init(S), R > S.

trouble(W + D) :- chosen_keepsake(K), water_sensitive(K, W), chosen_delay(D).
rescued :- chosen_response(R), response_speed(R, P), trouble(T), P >= T.

outcome(averted) :- relented.
outcome(saved) :- not relented, rescued.
outcome(ruined) :- not relented, not rescued.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for garment_id, garment in GARMENTS.items():
        lines.append(asp.fact("garment", garment_id))
        lines.append(asp.fact("pocket_size", garment_id, garment.pocket_size))
    for keepsake_id, keepsake in KEEPSAKES.items():
        lines.append(asp.fact("keepsake", keepsake_id))
        lines.append(asp.fact("keepsake_size", keepsake_id, keepsake.size))
        lines.append(asp.fact("keepsake_form", keepsake_id, keepsake.form))
        lines.append(asp.fact("water_sensitive", keepsake_id, keepsake.water_sensitive))
    for safe_id, safe_place in SAFE_PLACES.items():
        lines.append(asp.fact("safe_place", safe_id))
        for form in sorted(safe_place.accepts):
            lines.append(asp.fact("accepts", safe_id, form))
    for response_id, response in RESPONSES.items():
        lines.append(asp.fact("response", response_id))
        lines.append(asp.fact("response_speed", response_id, response.speed))
        lines.append(asp.fact("sense", response_id, response.sense))
    lines.append(asp.fact("stubborn_init", int(STUBBORN_INIT)))
    lines.append(asp.fact("sense_min", SENSE_MIN))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    sensible_rules = "sensible(R) :- response(R), sense(R, S), sense_min(M), S >= M."
    return f"{asp_facts()}\n{ASP_RULES}\n{sensible_rules}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("", "#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_sensible() -> list[str]:
    import asp

    model = asp.one_model(asp_program("", "#show sensible/1."))
    return sorted(r for (r,) in asp.atoms(model, "sensible"))


def asp_outcome(params: StoryParams) -> str:
    import asp

    scenario = "\n".join([
        asp.fact("chosen_keepsake", params.keepsake),
        asp.fact("chosen_response", params.response),
        asp.fact("chosen_delay", params.delay),
        asp.fact("chosen_attachment", params.attachment),
        asp.fact("chosen_patience", params.patience),
    ])
    model = asp.one_model(asp_program(scenario, "#show outcome/1."))
    found = asp.atoms(model, "outcome")
    return found[0][0] if found else "?"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Story world sketch: a child refuses to empty a pocket in the laundry room."
    )
    ap.add_argument("--garment", choices=GARMENTS)
    ap.add_argument("--keepsake", choices=KEEPSAKES)
    ap.add_argument("--safe-place", dest="safe_place", choices=SAFE_PLACES)
    ap.add_argument("--washer", choices=WASHERS)
    ap.add_argument("--response", choices=RESPONSES)
    ap.add_argument("--child-name")
    ap.add_argument("--child-gender", choices=["girl", "boy"])
    ap.add_argument("--parent", choices=["mother", "father"])
    ap.add_argument("--patience", choices=PATIENCE)
    ap.add_argument("--attachment", type=int, choices=ATTACHMENTS)
    ap.add_argument("--delay", type=int, choices=[0, 1, 2])
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list the valid combination set derived by clingo")
    ap.add_argument("--verify", action="store_true", help="check ASP and Python parity and run smoke tests")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def _pick_name(rng: random.Random, gender: str) -> str:
    return rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.garment and args.keepsake and not at_risk(GARMENTS[args.garment], KEEPSAKES[args.keepsake]):
        raise StoryError(explain_rejection(GARMENTS[args.garment], KEEPSAKES[args.keepsake]))
    if args.garment and args.keepsake and args.safe_place:
        if not safe_place_works(KEEPSAKES[args.keepsake], SAFE_PLACES[args.safe_place]):
            raise StoryError(explain_rejection(GARMENTS[args.garment], KEEPSAKES[args.keepsake], SAFE_PLACES[args.safe_place]))
    if args.response and RESPONSES[args.response].sense < SENSE_MIN:
        raise StoryError(explain_response(args.response))

    combos = [
        combo for combo in valid_combos()
        if (args.garment is None or combo[0] == args.garment)
        and (args.keepsake is None or combo[1] == args.keepsake)
        and (args.safe_place is None or combo[2] == args.safe_place)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    garment_id, keepsake_id, safe_place_id = rng.choice(sorted(combos))
    gender = args.child_gender or rng.choice(["girl", "boy"])
    name = args.child_name or _pick_name(rng, gender)
    washer_id = args.washer or rng.choice(sorted(WASHERS))
    response_id = args.response or rng.choice(sorted(r.id for r in sensible_responses()))
    parent = args.parent or rng.choice(["mother", "father"])
    patience = args.patience or rng.choice(PATIENCE)
    attachment = args.attachment if args.attachment is not None else rng.choice(ATTACHMENTS)
    delay = args.delay if args.delay is not None else rng.choice([0, 1, 2])

    return StoryParams(
        garment=garment_id,
        keepsake=keepsake_id,
        safe_place=safe_place_id,
        washer=washer_id,
        response=response_id,
        child_name=name,
        child_gender=gender,
        parent=parent,
        patience=patience,
        attachment=attachment,
        delay=delay,
    )


def generate(params: StoryParams) -> StorySample:
    try:
        garment_cfg = GARMENTS[params.garment]
        keepsake_cfg = KEEPSAKES[params.keepsake]
        safe_place_cfg = SAFE_PLACES[params.safe_place]
        washer_cfg = WASHERS[params.washer]
        response_cfg = RESPONSES[params.response]
    except KeyError as err:
        raise StoryError(f"(Invalid parameter: {err.args[0]})") from None

    if not at_risk(garment_cfg, keepsake_cfg):
        raise StoryError(explain_rejection(garment_cfg, keepsake_cfg))
    if not safe_place_works(keepsake_cfg, safe_place_cfg):
        raise StoryError(explain_rejection(garment_cfg, keepsake_cfg, safe_place_cfg))
    if response_cfg.sense < SENSE_MIN:
        raise StoryError(explain_response(params.response))

    world = tell(
        garment_cfg=garment_cfg,
        keepsake_cfg=keepsake_cfg,
        safe_place_cfg=safe_place_cfg,
        washer_cfg=washer_cfg,
        response_cfg=response_cfg,
        child_name=params.child_name,
        child_gender=params.child_gender,
        parent_type=params.parent,
        patience=params.patience,
        attachment=params.attachment,
        delay=params.delay,
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

    python_valid = set(valid_combos())
    clingo_valid = set(asp_valid_combos())
    if python_valid == clingo_valid:
        print(f"OK: valid combination gate matches ({len(python_valid)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combination gate:")
        if clingo_valid - python_valid:
            print("  only in clingo:", sorted(clingo_valid - python_valid))
        if python_valid - clingo_valid:
            print("  only in python:", sorted(python_valid - clingo_valid))

    python_sensible = {r.id for r in sensible_responses()}
    clingo_sensible = set(asp_sensible())
    if python_sensible == clingo_sensible:
        print(f"OK: sensible responses match ({sorted(python_sensible)}).")
    else:
        rc = 1
        print(f"MISMATCH in sensible responses: clingo={sorted(clingo_sensible)} python={sorted(python_sensible)}")

    cases = list(CURATED)
    for seed in range(60):
        try:
            args = build_parser().parse_args([])
            params = resolve_params(args, random.Random(seed))
            params.seed = seed
            cases.append(params)
        except StoryError:
            rc = 1
            print(f"Unexpected StoryError while resolving seed {seed}.")
            break

    mismatches = []
    for params in cases:
        if asp_outcome(params) != outcome_of(params):
            mismatches.append((params, asp_outcome(params), outcome_of(params)))
    if not mismatches:
        print(f"OK: outcome model matches on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {len(mismatches)} scenario outcomes differ.")
        for params, clingo_out, python_out in mismatches[:5]:
            print(" ", params, clingo_out, python_out)

    smoke_cases = [cases[0], resolve_params(build_parser().parse_args([]), random.Random(777))]
    for i, params in enumerate(smoke_cases, 1):
        try:
            sample = generate(params)
            if not sample.story.strip():
                raise StoryError("(Smoke test produced an empty story.)")
            print(f"OK: smoke test {i} generated a story with {len(sample.story.split())} words.")
        except Exception as err:  # pragma: no cover - verify should report any crash
            rc = 1
            print(f"SMOKE TEST FAILED on case {i}: {err}")
    return rc


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("", "#show valid/3.\n#show sensible/1.\n#show outcome/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        sensible = asp_sensible()
        combos = asp_valid_combos()
        print(f"sensible responses: {', '.join(sensible)}\n")
        print(f"{len(combos)} compatible (garment, keepsake, safe_place) combos:\n")
        for garment_id, keepsake_id, safe_place_id in combos:
            print(f"  {garment_id:10} {keepsake_id:13} {safe_place_id}")
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
                f"### {p.child_name}: {p.keepsake} in {p.garment} "
                f"({outcome_of(p)}, {p.safe_place})"
            )
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()

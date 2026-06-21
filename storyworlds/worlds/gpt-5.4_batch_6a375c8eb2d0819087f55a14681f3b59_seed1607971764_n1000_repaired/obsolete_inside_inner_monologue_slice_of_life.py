#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/obsolete_inside_inner_monologue_slice_of_life.py
============================================================================

A small story world about a child sorting a corner of home, finding an obsolete
object, and discovering that something meaningful is tucked inside it. The turn
comes from a simulated reveal, not from noun swapping: the child begins ready to
let the object go, then changes course when the hidden keepsake changes what the
object means.

The prose stays close to slice-of-life: a quiet chore, a small family talk, an
inner-monologue hesitation, and an ending image in an ordinary room that now
feels warmer.

Run it
------
    python storyworlds/worlds/gpt-5.4/obsolete_inside_inner_monologue_slice_of_life.py
    python storyworlds/worlds/gpt-5.4/obsolete_inside_inner_monologue_slice_of_life.py -n 5 --seed 7
    python storyworlds/worlds/gpt-5.4/obsolete_inside_inner_monologue_slice_of_life.py --all --qa
    python storyworlds/worlds/gpt-5.4/obsolete_inside_inner_monologue_slice_of_life.py --trace
    python storyworlds/worlds/gpt-5.4/obsolete_inside_inner_monologue_slice_of_life.py --json
    python storyworlds/worlds/gpt-5.4/obsolete_inside_inner_monologue_slice_of_life.py --asp
    python storyworlds/worlds/gpt-5.4/obsolete_inside_inner_monologue_slice_of_life.py --verify
"""

from __future__ import annotations

import argparse
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
    tags: set[str] = field(default_factory=set)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "grandmother", "woman"}
        male = {"boy", "father", "grandfather", "man"}
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


@dataclass
class Spot:
    id: str
    place: str
    clutter: str
    detail: str
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
class ObsoleteItem:
    id: str
    label: str
    phrase: str
    compartment: str
    hidden: set[str]
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
    discovery: str
    meaning: str
    shared: str
    support_word: str
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
class ReusePlan:
    id: str
    label: str
    supports: set[str]
    setup: str
    ending: str
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
    def __init__(self, spot: Spot) -> None:
        self.spot = spot
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


def _r_found_changes_mind(world: World) -> list[str]:
    child = world.get("child")
    item = world.get("item")
    keepsake = world.get("keepsake")
    if keepsake.meters["found"] < THRESHOLD:
        return []
    sig = ("found_changes_mind", item.id, keepsake.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    child.memes["surprise"] += 1
    child.memes["attachment"] += 1
    child.memes["discard"] = 0.0
    item.meters["saved"] += 1
    return []


def _r_shared_brings_warmth(world: World) -> list[str]:
    child = world.get("child")
    helper = world.get("helper")
    keepsake = world.get("keepsake")
    if keepsake.meters["shared"] < THRESHOLD:
        return []
    sig = ("shared_brings_warmth", keepsake.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    child.memes["warmth"] += 1
    child.memes["understanding"] += 1
    helper.memes["warmth"] += 1
    return []


def _r_put_away_restores_room(world: World) -> list[str]:
    room = world.get("room")
    item = world.get("item")
    if item.meters["placed"] < THRESHOLD:
        return []
    sig = ("put_away_restores_room", item.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    room.meters["tidy"] += 1
    return []


CAUSAL_RULES = [
    Rule(name="found_changes_mind", tag="emotional", apply=_r_found_changes_mind),
    Rule(name="shared_brings_warmth", tag="social", apply=_r_shared_brings_warmth),
    Rule(name="put_away_restores_room", tag="physical", apply=_r_put_away_restores_room),
]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
        changed = False
        for rule in CAUSAL_RULES:
            out = rule.apply(world)
            if out:
                changed = True
                produced.extend(out)
            elif any(sig[0] == rule.name for sig in world.fired):
                pass
        before = len(world.fired)
        for rule in CAUSAL_RULES:
            rule.apply(world)
        if len(world.fired) > before:
            changed = True
    if narrate:
        for line in produced:
            world.say(line)
    return produced


def init_state(ent: Entity, meter_keys: list[str], meme_keys: list[str]) -> None:
    for key in meter_keys:
        ent.meters[key] = float(ent.meters[key])
    for key in meme_keys:
        ent.memes[key] = float(ent.memes[key])


def supports_combo(item: ObsoleteItem, keepsake: Keepsake, plan: ReusePlan) -> bool:
    return keepsake.id in item.hidden and keepsake.id in plan.supports


def outcome_of(params: "StoryParams") -> str:
    return "shared" if params.keepsake == "recording" else "displayed"


SPOTS = {
    "desk_drawer": Spot(
        id="desk_drawer",
        place="the desk drawer",
        clutter="old pens, rubber bands, and folded receipts",
        detail="The drawer stuck a little before it slid open.",
        tags={"drawer", "home"},
    ),
    "hall_cabinet": Spot(
        id="hall_cabinet",
        place="the hall cabinet",
        clutter="scarves, batteries, and a few mystery cords",
        detail="Dust rested along the back edge like a pale stripe.",
        tags={"cabinet", "home"},
    ),
    "bedroom_shelf": Spot(
        id="bedroom_shelf",
        place="the bedroom shelf",
        clutter="paperbacks, marbles, and a small pile of birthday cards",
        detail="The afternoon light reached the shelf in a soft square.",
        tags={"shelf", "home"},
    ),
}

ITEMS = {
    "flip_phone": ObsoleteItem(
        id="flip_phone",
        label="flip phone",
        phrase="an obsolete silver flip phone",
        compartment="inside the clear plastic cover",
        hidden={"photo", "note"},
        tags={"phone", "obsolete", "device"},
    ),
    "pager": ObsoleteItem(
        id="pager",
        label="pager",
        phrase="an obsolete black pager",
        compartment="inside the clipped back panel",
        hidden={"note"},
        tags={"pager", "obsolete", "device"},
    ),
    "cassette_player": ObsoleteItem(
        id="cassette_player",
        label="cassette player",
        phrase="an obsolete cassette player",
        compartment="inside the tape door",
        hidden={"recording"},
        tags={"cassette", "obsolete", "device", "recording"},
    ),
}

KEEPSAKES = {
    "note": Keepsake(
        id="note",
        label="note",
        phrase="a folded note",
        discovery="a tiny folded note",
        meaning="It was only a few words, but the words sounded like a hand reaching across time.",
        shared="read the note aloud together",
        support_word="note",
        tags={"note", "memory", "paper"},
    ),
    "photo": Keepsake(
        id="photo",
        label="photo",
        phrase="a tiny photo",
        discovery="a tiny photo with rounded corners",
        meaning="The picture made the old object feel less like junk and more like a little pocket of family time.",
        shared="looked at the photo together",
        support_word="photo",
        tags={"photo", "memory", "picture"},
    ),
    "recording": Keepsake(
        id="recording",
        label="recording",
        phrase="an old cassette recording",
        discovery="a cassette still resting in the player",
        meaning="The sound was soft and scratchy, but it filled the room with a voice that still felt close.",
        shared="listened to the recording together",
        support_word="recording",
        tags={"recording", "memory", "sound"},
    ),
}

PLANS = {
    "memory_shelf": ReusePlan(
        id="memory_shelf",
        label="memory shelf",
        supports={"note", "photo"},
        setup="set the object on the little memory shelf by the books",
        ending="On the memory shelf, the old thing no longer looked forgotten. It looked chosen.",
        tags={"shelf", "display"},
    ),
    "keepsake_box": ReusePlan(
        id="keepsake_box",
        label="keepsake box",
        supports={"note", "photo"},
        setup="nestle the object in the keepsake box with the birthday cards",
        ending="Inside the keepsake box, the old thing rested beside other small pieces of family life.",
        tags={"box", "display"},
    ),
    "listening_corner": ReusePlan(
        id="listening_corner",
        label="listening corner",
        supports={"recording"},
        setup="place the player in the listening corner near the window",
        ending="In the listening corner, the old player waited like a quiet promise that some voices could still come back.",
        tags={"recording", "corner"},
    ),
}

GIRL_NAMES = ["Mina", "Lila", "Nora", "Ava", "Lucy", "Tess", "Maya", "Ivy"]
BOY_NAMES = ["Owen", "Eli", "Noah", "Max", "Sam", "Theo", "Finn", "Leo"]
HELPERS = ["mother", "father", "grandmother", "grandfather"]
TRAITS = ["careful", "quiet", "thoughtful", "curious", "tidy", "gentle"]


def valid_combos() -> list[tuple[str, str, str, str]]:
    combos: list[tuple[str, str, str, str]] = []
    for spot_id in SPOTS:
        for item_id, item in ITEMS.items():
            for keepsake_id, keepsake in KEEPSAKES.items():
                for plan_id, plan in PLANS.items():
                    if supports_combo(item, keepsake, plan):
                        combos.append((spot_id, item_id, keepsake_id, plan_id))
    return combos


def explain_rejection(item: ObsoleteItem, keepsake: Keepsake, plan: ReusePlan) -> str:
    if keepsake.id not in item.hidden:
        return (
            f"(No story: {item.label} does not reasonably hide {keepsake.phrase}. "
            f"Choose a keepsake that could plausibly be tucked inside {item.compartment}.)"
        )
    return (
        f"(No story: the plan '{plan.label}' does not fit a {keepsake.label}. "
        f"Choose a reuse plan that can honestly hold or honor that keepsake.)"
    )


@dataclass
class StoryParams:
    spot: str
    item: str
    keepsake: str
    plan: str
    child_name: str
    child_gender: str
    helper: str
    trait: str
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


def introduce(world: World, child: Entity, helper: Entity, item_cfg: ObsoleteItem) -> None:
    world.say(
        f"On a slow afternoon, {child.id} was helping {child.pronoun('possessive')} "
        f"{helper.label_word} sort {world.spot.place}. {world.spot.detail}"
    )
    world.say(
        f"There were {world.spot.clutter}, and tucked behind them was {item_cfg.phrase}."
    )


def touch_old_object(world: World, child: Entity, item: Entity, item_cfg: ObsoleteItem) -> None:
    child.memes["doubt"] += 1
    child.memes["discard"] += 1
    item.meters["noticed"] += 1
    world.say(
        f"{child.id} turned it over in {child.pronoun('possessive')} hands. "
        f"It was dusty and light, the sort of thing grown-ups called obsolete."
    )
    world.say(
        f'"Obsolete means nobody uses this now," {child.id} thought. '
        f'"So why does it feel hard to drop it in the give-away bag?"'
    )


def helper_prompt(world: World, child: Entity, helper: Entity, item_cfg: ObsoleteItem) -> None:
    world.say(
        f'"If it is only taking up space, we can let it go," '
        f"{child.pronoun('possessive')} {helper.label_word} said gently."
    )
    world.say(
        f'{child.id} nodded, but kept looking at the {item_cfg.label}. '
        f'"Maybe I should check {item_cfg.compartment} first," {child.id} thought.'
    )


def open_item(world: World, child: Entity, item: Entity, keepsake: Entity, item_cfg: ObsoleteItem, keepsake_cfg: Keepsake) -> None:
    item.meters["opened"] += 1
    keepsake.meters["found"] += 1
    propagate(world, narrate=False)
    world.say(
        f"{child.id} eased it open, and {keepsake_cfg.discovery} was waiting {item_cfg.compartment}."
    )
    world.say(
        f"{child.id} stopped moving for a second. {keepsake_cfg.meaning}"
    )


def share_meaning(world: World, child: Entity, helper: Entity, keepsake: Entity, keepsake_cfg: Keepsake) -> None:
    keepsake.meters["shared"] += 1
    propagate(world, narrate=False)
    if keepsake_cfg.id == "note":
        world.say(
            f'{child.id} held the note out. {helper.label_word.capitalize()} smoothed it open and '
            f"{keepsake_cfg.shared}. It was a tiny message from years ago, warm and ordinary in the best way."
        )
    elif keepsake_cfg.id == "photo":
        world.say(
            f'{child.id} showed the picture to {helper.label_word}. They {keepsake_cfg.shared}, '
            f"and {helper.label_word} smiled at the clothes and hair from long ago."
        )
    else:
        world.say(
            f'{helper.label_word.capitalize()} found fresh batteries in a nearby drawer, and together they '
            f"{keepsake_cfg.shared}. The room stayed still while the old voice fluttered out."
        )
    world.say(
        f'"I thought it was just old," {child.id} thought, "but there was something important inside all along."'
    )


def choose_keep(world: World, child: Entity, helper: Entity, item: Entity, plan_cfg: ReusePlan) -> None:
    item.meters["placed"] += 1
    propagate(world, narrate=False)
    world.say(
        f'{child.id} looked at the give-away bag, then back at the object. '
        f'"Can we keep it in a different way?" {child.pronoun()} asked.'
    )
    world.say(
        f'{helper.label_word.capitalize()} nodded. Together they decided to {plan_cfg.setup}.'
    )


def ending(world: World, child: Entity, helper: Entity, plan_cfg: ReusePlan, keepsake_cfg: Keepsake) -> None:
    room = world.get("room")
    tidier = "The drawer looked neater" if world.spot.id == "desk_drawer" else (
        "The cabinet looked calmer" if world.spot.id == "hall_cabinet" else "The shelf looked lighter"
    )
    if room.meters["tidy"] >= THRESHOLD:
        world.say(f"{tidier}, and {child.id} felt lighter too.")
    world.say(
        f"{plan_cfg.ending} {child.id} passed by it once more before dinner and smiled."
    )
    if keepsake_cfg.id == "recording":
        world.say("The home sounded the same as before, but it felt fuller.")
    else:
        world.say("Nothing grand had happened, only a small choice that made the room feel more like home.")


def tell(
    spot: Spot,
    item_cfg: ObsoleteItem,
    keepsake_cfg: Keepsake,
    plan_cfg: ReusePlan,
    child_name: str = "Mina",
    child_gender: str = "girl",
    helper_type: str = "mother",
    trait: str = "thoughtful",
) -> World:
    world = World(spot=spot)
    child = world.add(
        Entity(
            id=child_name,
            kind="character",
            type=child_gender,
            role="child",
            label=child_name,
            traits=[trait],
            tags={"child"},
        )
    )
    helper = world.add(
        Entity(
            id="Helper",
            kind="character",
            type=helper_type,
            role="helper",
            label="the helper",
            tags={"adult"},
        )
    )
    room = world.add(
        Entity(
            id="room",
            kind="thing",
            type="room",
            label="room",
            tags=set(spot.tags),
        )
    )
    item = world.add(
        Entity(
            id="item",
            kind="thing",
            type="object",
            label=item_cfg.label,
            attrs={"compartment": item_cfg.compartment},
            tags=set(item_cfg.tags),
        )
    )
    keepsake = world.add(
        Entity(
            id="keepsake",
            kind="thing",
            type="keepsake",
            label=keepsake_cfg.label,
            tags=set(keepsake_cfg.tags),
        )
    )

    init_state(item, ["noticed", "opened", "saved", "placed"], [])
    init_state(keepsake, ["found", "shared"], [])
    init_state(room, ["tidy"], [])
    init_state(child, [], ["doubt", "discard", "surprise", "attachment", "warmth", "understanding"])
    init_state(helper, [], ["warmth"])

    introduce(world, child, helper, item_cfg)
    world.para()
    touch_old_object(world, child, item, item_cfg)
    helper_prompt(world, child, helper, item_cfg)
    world.para()
    open_item(world, child, item, keepsake, item_cfg, keepsake_cfg)
    share_meaning(world, child, helper, keepsake, keepsake_cfg)
    world.para()
    choose_keep(world, child, helper, item, plan_cfg)
    ending(world, child, helper, plan_cfg, keepsake_cfg)

    world.facts.update(
        child=child,
        helper=helper,
        room=room,
        spot=spot,
        item_cfg=item_cfg,
        keepsake_cfg=keepsake_cfg,
        plan_cfg=plan_cfg,
        item=item,
        keepsake=keepsake,
        outcome=outcome_of(
            StoryParams(
                spot=spot.id,
                item=item_cfg.id,
                keepsake=keepsake_cfg.id,
                plan=plan_cfg.id,
                child_name=child_name,
                child_gender=child_gender,
                helper=helper_type,
                trait=trait,
                seed=None,
            )
        ),
    )
    return world


KNOWLEDGE = {
    "obsolete": [
        (
            "What does obsolete mean?",
            "Obsolete means something is old and is not used much anymore because newer things have taken its place. It does not always mean the thing has no value."
        )
    ],
    "phone": [
        (
            "What is a flip phone?",
            "A flip phone is a small phone that opens and closes on a hinge. Many people used them before touch-screen phones became common."
        )
    ],
    "pager": [
        (
            "What is a pager?",
            "A pager is a small device that can beep or show a short message. People used them before mobile phones could do so many things."
        )
    ],
    "cassette": [
        (
            "What is a cassette player?",
            "A cassette player is a machine that plays sound stored on cassette tapes. It is older technology, but recordings on tapes can still matter to families."
        )
    ],
    "note": [
        (
            "Why can a little note be important?",
            "A little note can hold a memory, kind words, or a reminder from someone you love. Small paper things can matter because of what they mean, not because of how big they are."
        )
    ],
    "photo": [
        (
            "Why do people keep old photos?",
            "People keep old photos because pictures help them remember days, faces, and feelings. A tiny photo can bring back a whole moment."
        )
    ],
    "recording": [
        (
            "Why can an old recording feel special?",
            "An old recording lets you hear a voice or a song again. Sound can make someone feel close even after a long time."
        )
    ],
    "memory": [
        (
            "Why do families keep memory boxes or shelves?",
            "Families use memory boxes and shelves to hold objects that tell part of their story. The objects help everyday places feel warm and personal."
        )
    ],
}
KNOWLEDGE_ORDER = ["obsolete", "phone", "pager", "cassette", "note", "photo", "recording", "memory"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    child = f["child"]
    item_cfg = f["item_cfg"]
    keepsake_cfg = f["keepsake_cfg"]
    plan_cfg = f["plan_cfg"]
    helper = f["helper"]
    return [
        f'Write a gentle slice-of-life story for a 3-to-5-year-old that includes the words "obsolete" and "inside".',
        f"Tell a quiet home story where {child.id} finds {item_cfg.phrase} while tidying, thinks about throwing it away, and then finds {keepsake_cfg.phrase} inside it.",
        f"Write a story with inner monologue where a child and {child.pronoun('possessive')} {helper.label_word} turn an old object into part of a {plan_cfg.label} after discovering a memory inside.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    child = f["child"]
    helper = f["helper"]
    item_cfg = f["item_cfg"]
    keepsake_cfg = f["keepsake_cfg"]
    plan_cfg = f["plan_cfg"]
    spot = f["spot"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {child.id}, who was sorting {spot.place} with {child.pronoun('possessive')} {helper.label_word}. The story is about a small family moment during an ordinary chore."
        ),
        (
            f"What did {child.id} find?",
            f"{child.id} found {item_cfg.phrase}. At first {child.pronoun()} thought it was only obsolete and ready to leave the house."
        ),
        (
            f"Why did {child.id} hesitate before giving the object away?",
            f"{child.id} told {child.pronoun('object')}self that the object was obsolete, but it still felt hard to toss aside. That uneasy feeling made {child.pronoun('object')} stop and look inside first."
        ),
        (
            f"What was inside the {item_cfg.label}?",
            f"Inside the {item_cfg.label} was {keepsake_cfg.discovery}. Finding it changed the object from old clutter into something connected to the family."
        ),
        (
            f"How did the discovery change what {child.id} did next?",
            f"{child.id} no longer wanted to drop the object in the give-away bag. After sharing the {keepsake_cfg.label} with {helper.label_word}, {child.pronoun()} asked to keep it in a new way."
        ),
        (
            "How did the story end?",
            f"They chose to {plan_cfg.setup}, and the room felt tidier and warmer at the same time. The ending shows that a small memory can change what an old thing means."
        ),
    ]
    if keepsake_cfg.id == "recording":
        qa.append(
            (
                "Why did listening matter so much?",
                f"When they listened, the old voice filled the room and made the past feel close again. That is why the cassette player stopped seeming useless and started feeling worth keeping."
            )
        )
    else:
        qa.append(
            (
                f"Why did looking at the {keepsake_cfg.label} matter so much?",
                f"The little keepsake held a family memory that could not be replaced by a newer object. Seeing it helped {child.id} understand that old things can carry love inside them."
            )
        )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags: set[str] = {"obsolete", "memory"} | set(f["item_cfg"].tags) | set(f["keepsake_cfg"].tags)
    out: list[tuple[str, str]] = []
    for key in KNOWLEDGE_ORDER:
        if key in tags and key in KNOWLEDGE:
            out.extend(KNOWLEDGE[key])
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
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if ent.role:
            bits.append(f"role={ent.role}")
        if ent.attrs:
            bits.append(f"attrs={ent.attrs}")
        if ent.tags:
            bits.append(f"tags={sorted(ent.tags)}")
        lines.append(f"  {ent.id:8} ({ent.type:12}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(sig[0] for sig in world.fired))}")
    return "\n".join(lines)


ASP_RULES = r"""
supports_combo(I, K, P) :- item(I), keepsake(K), plan(P), item_hides(I, K), plan_supports(P, K).
valid(S, I, K, P) :- spot(S), supports_combo(I, K, P).

shared_outcome(K) :- keepsake(K), is_audio(K).
displayed_outcome(K) :- keepsake(K), not is_audio(K).

outcome(shared) :- chosen_keepsake(K), shared_outcome(K).
outcome(displayed) :- chosen_keepsake(K), displayed_outcome(K).
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for sid in SPOTS:
        lines.append(asp.fact("spot", sid))
    for iid, item in ITEMS.items():
        lines.append(asp.fact("item", iid))
        for kid in sorted(item.hidden):
            lines.append(asp.fact("item_hides", iid, kid))
    for kid in KEEPSAKES:
        lines.append(asp.fact("keepsake", kid))
        if kid == "recording":
            lines.append(asp.fact("is_audio", kid))
    for pid, plan in PLANS.items():
        lines.append(asp.fact("plan", pid))
        for kid in sorted(plan.supports):
            lines.append(asp.fact("plan_supports", pid, kid))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("", "#show valid/4."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_outcome(params: StoryParams) -> str:
    import asp

    scenario = asp.fact("chosen_keepsake", params.keepsake)
    model = asp.one_model(asp_program(scenario, "#show outcome/1."))
    out = asp.atoms(model, "outcome")
    return out[0][0] if out else "?"


CURATED = [
    StoryParams(
        spot="desk_drawer",
        item="flip_phone",
        keepsake="photo",
        plan="memory_shelf",
        child_name="Mina",
        child_gender="girl",
        helper="mother",
        trait="thoughtful",
        seed=None,
    ),
    StoryParams(
        spot="hall_cabinet",
        item="pager",
        keepsake="note",
        plan="keepsake_box",
        child_name="Owen",
        child_gender="boy",
        helper="grandmother",
        trait="quiet",
        seed=None,
    ),
    StoryParams(
        spot="bedroom_shelf",
        item="cassette_player",
        keepsake="recording",
        plan="listening_corner",
        child_name="Lila",
        child_gender="girl",
        helper="father",
        trait="curious",
        seed=None,
    ),
]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Story world sketch: an obsolete object, something meaningful inside, and a small home decision."
    )
    ap.add_argument("--spot", choices=SPOTS)
    ap.add_argument("--item", choices=ITEMS)
    ap.add_argument("--keepsake", choices=KEEPSAKES)
    ap.add_argument("--plan", choices=PLANS)
    ap.add_argument("--helper", choices=HELPERS)
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list the compatible-story set derived by clingo")
    ap.add_argument("--verify", action="store_true", help="check the inline ASP reasoner matches the Python logic")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program (facts + inline rules)")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.item and args.keepsake and args.plan:
        item = ITEMS[args.item]
        keepsake = KEEPSAKES[args.keepsake]
        plan = PLANS[args.plan]
        if not supports_combo(item, keepsake, plan):
            raise StoryError(explain_rejection(item, keepsake, plan))

    combos = [
        combo
        for combo in valid_combos()
        if (args.spot is None or combo[0] == args.spot)
        and (args.item is None or combo[1] == args.item)
        and (args.keepsake is None or combo[2] == args.keepsake)
        and (args.plan is None or combo[3] == args.plan)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    spot, item, keepsake, plan = rng.choice(sorted(combos))
    gender = args.gender or rng.choice(["girl", "boy"])
    name_pool = GIRL_NAMES if gender == "girl" else BOY_NAMES
    name = args.name or rng.choice(name_pool)
    helper = args.helper or rng.choice(HELPERS)
    trait = rng.choice(TRAITS)
    return StoryParams(
        spot=spot,
        item=item,
        keepsake=keepsake,
        plan=plan,
        child_name=name,
        child_gender=gender,
        helper=helper,
        trait=trait,
        seed=None,
    )


def _require_key(table: dict, key: str, label: str):
    if key not in table:
        raise StoryError(f"(No story: unknown {label} '{key}'.)")
    return table[key]


def generate(params: StoryParams) -> StorySample:
    spot = _require_key(SPOTS, params.spot, "spot")
    item = _require_key(ITEMS, params.item, "item")
    keepsake = _require_key(KEEPSAKES, params.keepsake, "keepsake")
    plan = _require_key(PLANS, params.plan, "plan")

    if not supports_combo(item, keepsake, plan):
        raise StoryError(explain_rejection(item, keepsake, plan))

    world = tell(
        spot=spot,
        item_cfg=item,
        keepsake_cfg=keepsake,
        plan_cfg=plan,
        child_name=params.child_name,
        child_gender=params.child_gender,
        helper_type=params.helper,
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


def asp_verify() -> int:
    rc = 0
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: ASP gate matches valid_combos() ({len(py)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos:")
        if py - cl:
            print("  only in python:", sorted(py - cl))
        if cl - py:
            print("  only in clingo:", sorted(cl - py))

    cases = list(CURATED)
    for seed in range(20):
        try:
            params = resolve_params(build_parser().parse_args([]), random.Random(seed))
            params.seed = seed
            cases.append(params)
        except StoryError:
            rc = 1
            print(f"MISMATCH: resolve_params failed during verification on seed {seed}.")
            break

    bad = 0
    for params in cases:
        if asp_outcome(params) != outcome_of(params):
            bad += 1
    if bad == 0:
        print(f"OK: ASP outcome matches outcome_of() on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {bad}/{len(cases)} outcomes differ.")

    try:
        smoke = generate(CURATED[0])
        if not smoke.story.strip():
            raise StoryError("(Verification smoke test produced an empty story.)")
        print("OK: smoke test generation succeeded.")
    except Exception as err:  # pragma: no cover
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    return rc


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("", "#show valid/4.\n#show outcome/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (spot, item, keepsake, plan) combos:\n")
        for spot, item, keepsake, plan in combos:
            print(f"  {spot:14} {item:16} {keepsake:10} {plan}")
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
            print(json.dumps([sample.to_dict() for sample in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.child_name}: {p.item} with {p.keepsake} at {p.spot}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()

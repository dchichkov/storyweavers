#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/love_dim_audience_happy_ending_moral_value.py
=======================================================================

A standalone story world for a tiny child-facing detective mystery:
before a small show begins, a young detective notices that an important prop is
missing just as the audience is settling in. A clue leads through the room,
kindness unlocks the truth, and the show begins with a happy ending and a moral:
people solve problems better when they stay calm, look carefully, and tell the
truth.

The seed required the exact words "love-dim" and "audience", so every story
includes a tiny printed label that reads "love-dim" on the show equipment, and
the waiting audience matters to the stakes.

Run it
------
    python storyworlds/worlds/gpt-5.4/love_dim_audience_happy_ending_moral_value.py
    python storyworlds/worlds/gpt-5.4/love_dim_audience_happy_ending_moral_value.py --item heart_lantern --cause borrowed_repair
    python storyworlds/worlds/gpt-5.4/love_dim_audience_happy_ending_moral_value.py --cause breeze --spot repair_table
    python storyworlds/worlds/gpt-5.4/love_dim_audience_happy_ending_moral_value.py --all
    python storyworlds/worlds/gpt-5.4/love_dim_audience_happy_ending_moral_value.py -n 5 --seed 7 --qa
    python storyworlds/worlds/gpt-5.4/love_dim_audience_happy_ending_moral_value.py --verify
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


# ---------------------------------------------------------------------------
# Entities
# ---------------------------------------------------------------------------
@dataclass
class Entity:
    id: str
    kind: str = "thing"            # "character" | "thing"
    type: str = "thing"
    label: str = ""
    traits: list[str] = field(default_factory=list)
    role: str = ""
    attrs: dict = field(default_factory=dict)
    portable: bool = False
    lightweight: bool = False
    useful_for_repair: bool = False
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "woman", "teacher", "librarian"}
        male = {"boy", "father", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def title_word(self) -> str:
        return {"teacher": "teacher", "librarian": "librarian"}.get(self.type, self.type)


# ---------------------------------------------------------------------------
# Domain registries
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
    def tags(self):
        if not hasattr(self, "_tags"):
            object.__setattr__(self, "_tags", set())
        return self._tags


@dataclass
class Venue:
    id: str
    place: str
    room_detail: str
    stage_word: str
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
class ItemCfg:
    id: str
    label: str
    phrase: str
    purpose: str
    clue_mark: str
    lightweight: bool = False
    useful_for_repair: bool = False
    portable: bool = True
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
class Cause:
    id: str
    verb: str
    clue_line: str
    needs_repair_help: bool = False
    needs_lightweight: bool = False
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
class Spot:
    id: str
    label: str
    phrase: str
    clue_text: str
    reveal_text: str
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
class AudienceCfg:
    id: str
    label: str
    hush_line: str
    closing_image: str
    tags: set[str] = field(default_factory=set)


# ---------------------------------------------------------------------------
# World
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
# Rules
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


def _r_missing_risk(world: World) -> list[str]:
    item = world.get("item")
    if item.meters["missing"] < THRESHOLD:
        return []
    sig = ("missing_risk", item.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    world.get("room").meters["delay_risk"] += 1
    world.get("detective").memes["worry"] += 1
    world.get("helper").memes["worry"] += 1
    return ["__risk__"]


def _r_audience_pressure(world: World) -> list[str]:
    room = world.get("room")
    if room.meters["delay_risk"] < THRESHOLD or room.meters["audience_waiting"] < THRESHOLD:
        return []
    sig = ("audience_pressure", "room")
    if sig in world.fired:
        return []
    world.fired.add(sig)
    world.get("detective").memes["focus"] += 1
    world.get("adult").memes["calm"] += 1
    return ["__pressure__"]


def _r_kindness_unlocks_truth(world: World) -> list[str]:
    if not world.facts.get("kind_question"):
        return []
    if world.facts.get("cause_id") != "borrowed_repair":
        return []
    helper = world.get("helper")
    if helper.memes["guilt"] < THRESHOLD:
        return []
    sig = ("truth", helper.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    helper.memes["honesty"] += 1
    helper.memes["relief"] += 1
    world.facts["truth_revealed"] = True
    return ["__truth__"]


def _r_found_relief(world: World) -> list[str]:
    item = world.get("item")
    if item.meters["found"] < THRESHOLD:
        return []
    sig = ("found_relief", item.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    item.meters["missing"] = 0.0
    world.get("room").meters["delay_risk"] = 0.0
    for eid in ("detective", "helper", "adult"):
        world.get(eid).memes["relief"] += 1
    world.get("detective").memes["pride"] += 1
    return ["__found__"]


CAUSAL_RULES: list[Rule] = [
    Rule(name="missing_risk", tag="physical", apply=_r_missing_risk),
    Rule(name="audience_pressure", tag="social", apply=_r_audience_pressure),
    Rule(name="kindness_unlocks_truth", tag="social", apply=_r_kindness_unlocks_truth),
    Rule(name="found_relief", tag="social", apply=_r_found_relief),
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
                produced.extend(s for s in out if not s.startswith("__"))
    if narrate:
        for sent in produced:
            world.say(sent)
    return produced


# ---------------------------------------------------------------------------
# Reasonableness
# ---------------------------------------------------------------------------
def cause_fits_item(cause: Cause, item: ItemCfg) -> bool:
    if cause.needs_repair_help and not item.useful_for_repair:
        return False
    if cause.needs_lightweight and not item.lightweight:
        return False
    return item.portable


def spot_for_cause(cause_id: str) -> str:
    return {
        "borrowed_repair": "repair_table",
        "breeze": "curtain_fold",
        "tidied_away": "prop_trunk",
    }[cause_id]


def valid_combo(item_id: str, cause_id: str, spot_id: str) -> bool:
    if item_id not in ITEMS or cause_id not in CAUSES or spot_id not in SPOTS:
        return False
    item = ITEMS[item_id]
    cause = CAUSES[cause_id]
    return cause_fits_item(cause, item) and spot_for_cause(cause_id) == spot_id


def valid_combos() -> list[tuple[str, str, str]]:
    out: list[tuple[str, str, str]] = []
    for item_id in ITEMS:
        for cause_id in CAUSES:
            for spot_id in SPOTS:
                if valid_combo(item_id, cause_id, spot_id):
                    out.append((item_id, cause_id, spot_id))
    return out


def explain_rejection(item: ItemCfg, cause: Cause, spot: Spot) -> str:
    expected = SPOTS[spot_for_cause(cause.id)]
    if cause.needs_repair_help and not item.useful_for_repair:
        return (
            f"(No story: {item.phrase} would not be useful at a repair table, so "
            f"no one would borrow it for fixing something. Pick an item like the "
            f"heart lantern or the silver pin.)"
        )
    if cause.needs_lightweight and not item.lightweight:
        return (
            f"(No story: {item.phrase} is not the kind of light prop a breeze would "
            f"carry into a curtain fold. Pick a lighter item.)"
        )
    if spot.id != expected.id:
        return (
            f"(No story: the cause '{cause.id}' leads to {expected.phrase}, not "
            f"{spot.phrase}. This mystery world keeps clues and hiding places aligned.)"
        )
    return "(No story: that combination does not make a reasonable little mystery.)"


def solution_mode(cause_id: str) -> str:
    return "confession" if cause_id == "borrowed_repair" else "discovery"


# ---------------------------------------------------------------------------
# Simulation helpers
# ---------------------------------------------------------------------------
def predict_world(world: World) -> dict:
    sim = world.copy()
    item = sim.get("item")
    item.meters["missing"] += 1
    propagate(sim, narrate=False)
    return {
        "delay_risk": sim.get("room").meters["delay_risk"],
        "detective_worry": sim.get("detective").memes["worry"],
    }


def inspect_clue(world: World) -> None:
    detective = world.get("detective")
    detective.memes["curiosity"] += 1
    world.say(world.facts["clue_text"])


def ask_kindly(world: World) -> None:
    detective = world.get("detective")
    helper = world.get("helper")
    adult = world.get("adult")
    world.facts["kind_question"] = True
    detective.memes["kindness"] += 1
    helper.memes["trust"] += 1
    propagate(world, narrate=False)
    world.say(
        f'"I am looking for clues, not someone to blame," {detective.id} said. '
        f'"Did you see where the {world.facts["item_cfg"].label} went?"'
    )
    if helper.memes["honesty"] >= THRESHOLD:
        world.say(
            f'{helper.id} looked down, then back up at {adult.title_word} {adult.id}. '
            f'"I should have told the truth right away," {helper.pronoun()} said.'
        )


def search_spot(world: World) -> None:
    spot = world.facts["spot_cfg"]
    detective = world.get("detective")
    item = world.get("item")
    detective.memes["focus"] += 1
    world.say(
        f"{detective.id} followed the clue to {spot.phrase} and looked slowly, "
        f"like a real little detective."
    )
    item.meters["found"] += 1
    propagate(world, narrate=False)
    world.facts["found_at"] = spot.id


# ---------------------------------------------------------------------------
# Screenplay verbs
# ---------------------------------------------------------------------------
def setup(world: World, venue: Venue, audience_cfg: AudienceCfg) -> None:
    detective = world.get("detective")
    helper = world.get("helper")
    adult = world.get("adult")
    item_cfg = world.facts["item_cfg"]
    world.say(
        f"At {venue.place}, {detective.id} and {helper.id} were helping {adult.title_word} "
        f"{adult.id} get ready for a small show. {venue.room_detail}"
    )
    world.say(
        f"On a side lamp, a funny paper label read love-dim, and {detective.id} thought "
        f"it sounded exactly like the sort of odd clue a detective should remember."
    )
    world.say(
        f"Soon the {audience_cfg.label} audience would fill the room, and the "
        f"{item_cfg.label} was needed for {item_cfg.purpose}."
    )


def discover_missing(world: World, audience_cfg: AudienceCfg) -> None:
    detective = world.get("detective")
    item = world.get("item")
    adult = world.get("adult")
    item_cfg = world.facts["item_cfg"]
    audience = world.get("audience")
    audience.meters["waiting"] = 1.0
    item.meters["missing"] += 1
    world.get("room").meters["audience_waiting"] = 1.0
    pred = predict_world(world)
    world.facts["predicted_delay"] = pred["delay_risk"]
    propagate(world, narrate=False)
    world.say(
        f"But when {adult.id} reached for {item_cfg.phrase}, the hook was empty."
    )
    world.say(
        f'"The {item_cfg.label} is missing," whispered {detective.id}. Around them, '
        f"the room grew more hushed as the audience began to settle in."
    )


def first_inference(world: World) -> None:
    detective = world.get("detective")
    cause = world.facts["cause_cfg"]
    world.say(
        f"{detective.id} narrowed {detective.pronoun('possessive')} eyes. "
        f"{cause.clue_line}"
    )


def reveal_confession(world: World) -> None:
    helper = world.get("helper")
    item_cfg = world.facts["item_cfg"]
    spot = world.facts["spot_cfg"]
    world.say(
        f'"I borrowed the {item_cfg.label} for just a minute," {helper.id} said. '
        f'"A ribbon had come loose, and I set it down by {spot.phrase}. Then I got scared '
        f'and forgot to say so."'
    )


def recovery(world: World) -> None:
    item_cfg = world.facts["item_cfg"]
    spot = world.facts["spot_cfg"]
    world.say(spot.reveal_text.format(item=item_cfg.label))


def lesson(world: World) -> None:
    detective = world.get("detective")
    helper = world.get("helper")
    adult = world.get("adult")
    world.say(
        f'{adult.title_word.capitalize()} {adult.id} knelt between the two children. '
        f'"A sharp eye is useful," {adult.pronoun()} said, "but a kind heart is useful too. '
        f'Telling the truth early keeps little worries from becoming big ones."'
    )
    world.say(
        f"{helper.id} nodded, and {detective.id} nodded too. Solving the case felt good, "
        f"but being gentle felt even better."
    )


def happy_ending(world: World, audience_cfg: AudienceCfg) -> None:
    detective = world.get("detective")
    helper = world.get("helper")
    item_cfg = world.facts["item_cfg"]
    world.say(
        f"Soon the {item_cfg.label} was back in place, the curtains opened, and the "
        f"{audience_cfg.label} audience leaned forward with bright eyes."
    )
    world.say(
        f"{audience_cfg.closing_image} {detective.id} and {helper.id} shared a quick smile. "
        f"The mystery was over, the show could begin, and the room felt warm and brave."
    )


# ---------------------------------------------------------------------------
# Main story assembly
# ---------------------------------------------------------------------------
def tell(
    venue: Venue,
    item_cfg: ItemCfg,
    cause_cfg: Cause,
    spot_cfg: Spot,
    audience_cfg: AudienceCfg,
    detective_name: str = "Nora",
    detective_gender: str = "girl",
    helper_name: str = "Ben",
    helper_gender: str = "boy",
    adult_type: str = "teacher",
) -> World:
    world = World()
    detective = world.add(Entity(
        id=detective_name,
        kind="character",
        type=detective_gender,
        role="detective",
        traits=["careful", "observant"],
        attrs={"job": "junior detective"},
    ))
    helper = world.add(Entity(
        id=helper_name,
        kind="character",
        type=helper_gender,
        role="helper",
        traits=["busy", "kind"],
        attrs={"job": "stage helper"},
    ))
    adult = world.add(Entity(
        id="Ms. Hale" if adult_type == "teacher" else "June",
        kind="character",
        type=adult_type,
        role="adult",
        traits=["calm"],
        attrs={"job": adult_type},
    ))
    room = world.add(Entity(
        id="room",
        kind="thing",
        type="room",
        label=venue.place,
        attrs={"venue": venue.id},
    ))
    item = world.add(Entity(
        id="item",
        kind="thing",
        type="prop",
        label=item_cfg.label,
        portable=item_cfg.portable,
        lightweight=item_cfg.lightweight,
        useful_for_repair=item_cfg.useful_for_repair,
        attrs={"purpose": item_cfg.purpose},
    ))
    audience = world.add(Entity(
        id="audience",
        kind="thing",
        type="audience",
        label=audience_cfg.label,
        attrs={"group": audience_cfg.label},
    ))

    world.facts.update(
        venue=venue,
        item_cfg=item_cfg,
        cause_cfg=cause_cfg,
        cause_id=cause_cfg.id,
        spot_cfg=spot_cfg,
        audience_cfg=audience_cfg,
        detective=detective,
        helper=helper,
        adult=adult,
        solution_mode=solution_mode(cause_cfg.id),
        clue_text=spot_cfg.clue_text.format(mark=item_cfg.clue_mark),
        kind_question=False,
        truth_revealed=False,
        found_at="",
    )

    setup(world, venue, audience_cfg)
    world.para()
    discover_missing(world, audience_cfg)
    first_inference(world)
    inspect_clue(world)
    world.para()

    if cause_cfg.id == "borrowed_repair":
        helper.memes["guilt"] = 1.0
        ask_kindly(world)
        if world.facts.get("truth_revealed"):
            reveal_confession(world)
    else:
        world.say(
            f"{detective.id} did not point at anyone. {detective.pronoun().capitalize()} just "
            f"followed the clue and kept thinking."
        )

    search_spot(world)
    recovery(world)
    world.para()
    lesson(world)
    happy_ending(world, audience_cfg)

    world.facts.update(
        mystery_solved=world.get("item").meters["found"] >= THRESHOLD,
        audience_delayed=world.get("room").meters["delay_risk"] >= THRESHOLD,
    )
    return world


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------
VENUES = {
    "school_hall": Venue(
        id="school_hall",
        place="the school hall",
        room_detail="Paper stars hung above the little stage, and a row of wooden chairs waited below.",
        stage_word="stage",
        tags={"hall"},
    ),
    "library_corner": Venue(
        id="library_corner",
        place="the library corner",
        room_detail="A cloth curtain had been clipped between two tall shelves to make a tiny stage.",
        stage_word="curtain-stage",
        tags={"library"},
    ),
    "community_room": Venue(
        id="community_room",
        place="the community room",
        room_detail="Folded chairs stood in neat rows, and a painted cardboard backdrop leaned by the wall.",
        stage_word="platform",
        tags={"room"},
    ),
}

ITEMS = {
    "heart_lantern": ItemCfg(
        id="heart_lantern",
        label="heart lantern",
        phrase="the heart lantern",
        purpose="the sweet final scene where the paper moon glowed red",
        clue_mark="a red wax dot",
        lightweight=True,
        useful_for_repair=True,
        portable=True,
        tags={"lantern", "truth"},
    ),
    "silver_pin": ItemCfg(
        id="silver_pin",
        label="silver star pin",
        phrase="the silver star pin",
        purpose="the hero's cape in the last bow",
        clue_mark="a silver thread",
        lightweight=True,
        useful_for_repair=True,
        portable=True,
        tags={"pin", "truth"},
    ),
    "magnifier_prop": ItemCfg(
        id="magnifier_prop",
        label="magnifying-glass prop",
        phrase="the magnifying-glass prop",
        purpose="the detective scene at the middle of the show",
        clue_mark="a round dusty ring",
        lightweight=False,
        useful_for_repair=False,
        portable=True,
        tags={"detective", "clue"},
    ),
}

CAUSES = {
    "borrowed_repair": Cause(
        id="borrowed_repair",
        verb="borrowed while fixing a costume",
        clue_line="A mystery never starts with shouting, {name} thought. It starts with what changed, and why.",
        needs_repair_help=True,
        tags={"truth", "kindness"},
    ),
    "breeze": Cause(
        id="breeze",
        verb="nudged away by a passing breeze",
        clue_line="A soft breeze had slipped through the room, enough to move a light prop but not a heavy one.",
        needs_lightweight=True,
        tags={"wind", "clue"},
    ),
    "tidied_away": Cause(
        id="tidied_away",
        verb="put away by mistake during cleanup",
        clue_line="Sometimes the best clue is not a crime at all, only a tidy-up done too soon.",
        tags={"mistake", "careful"},
    ),
}

SPOTS = {
    "repair_table": Spot(
        id="repair_table",
        label="repair table",
        phrase="the repair table by the costume basket",
        clue_text="Near the floor lay {mark} beside a loose ribbon and a little spool of tape.",
        reveal_text="There, tucked beside the tape and ribbon, was the {item}.",
        tags={"repair"},
    ),
    "curtain_fold": Spot(
        id="curtain_fold",
        label="curtain fold",
        phrase="the deep fold of the curtain",
        clue_text="A tiny scrap of color had snagged near the curtain hem, as if something light had brushed past.",
        reveal_text="Inside the curtain fold, caught safely in the cloth, was the {item}.",
        tags={"curtain"},
    ),
    "prop_trunk": Spot(
        id="prop_trunk",
        label="prop trunk",
        phrase="the old prop trunk under the side table",
        clue_text="A lid stood a finger-width open, and on top rested {mark} where no one had meant to leave it.",
        reveal_text="In the prop trunk, laid gently on the folded capes, was the {item}.",
        tags={"trunk"},
    ),
}

AUDIENCES = {
    "families": AudienceCfg(
        id="families",
        label="families",
        hush_line="soft whispers and shoe-taps filled the room",
        closing_image="When the first line was spoken, the audience broke into happy claps.",
        tags={"families"},
    ),
    "little_kids": AudienceCfg(
        id="little_kids",
        label="little kids",
        hush_line="small voices buzzed like bees before the hush",
        closing_image="When the first line was spoken, the audience wriggled happily and then listened hard.",
        tags={"kids"},
    ),
    "neighbors": AudienceCfg(
        id="neighbors",
        label="neighbors",
        hush_line="coats rustled and friendly whispers drifted together",
        closing_image="When the first line was spoken, the audience smiled and clapped in a soft rolling wave.",
        tags={"neighbors"},
    ),
}

GIRL_NAMES = ["Nora", "Lily", "Mina", "Ava", "Zoe", "Ella", "Ruby", "Tess"]
BOY_NAMES = ["Ben", "Max", "Theo", "Sam", "Leo", "Eli", "Noah", "Finn"]


# ---------------------------------------------------------------------------
# Params
# ---------------------------------------------------------------------------
@dataclass
class StoryParams:
    venue: str
    item: str
    cause: str
    spot: str
    audience: str
    detective_name: str
    detective_gender: str
    helper_name: str
    helper_gender: str
    adult_type: str
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# QA
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
    "audience": [
        ("What is an audience?",
         "An audience is the group of people who watch and listen to a show, play, or concert together.")
    ],
    "detective": [
        ("What does a detective do?",
         "A detective looks for clues, asks careful questions, and uses thinking to solve a problem.")
    ],
    "truth": [
        ("Why is telling the truth important in a problem?",
         "Telling the truth early helps people fix a problem faster. It also helps others trust you.")
    ],
    "kindness": [
        ("Why can kindness help solve a mystery?",
         "Kindness helps people feel safe enough to speak honestly. When nobody feels attacked, clues are easier to share.")
    ],
    "breeze": [
        ("What can a breeze do indoors?",
         "A breeze can flutter paper, ribbons, and other light things. It usually cannot push something heavy very far.")
    ],
    "prop": [
        ("What is a prop in a play?",
         "A prop is an object used in a play or show to help tell the story onstage.")
    ],
}
KNOWLEDGE_ORDER = ["audience", "detective", "truth", "kindness", "breeze", "prop"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    detective = f["detective"]
    item_cfg = f["item_cfg"]
    audience_cfg = f["audience_cfg"]
    return [
        f'Write a short detective story for a 3-to-5-year-old that includes the words "love-dim" and "audience" and ends happily.',
        f"Tell a gentle mystery where {detective.id} notices that the {item_cfg.label} is missing just before a show for a {audience_cfg.label} audience, and solves the case with kindness.",
        "Write a simple moral story where a child detective follows clues, stays calm, and learns that truth and kindness matter more than blaming.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    detective = f["detective"]
    helper = f["helper"]
    adult = f["adult"]
    item_cfg = f["item_cfg"]
    spot = f["spot_cfg"]
    audience_cfg = f["audience_cfg"]
    cause = f["cause_cfg"]
    mode = f["solution_mode"]

    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {detective.id}, a child who acts like a little detective, and {helper.id}, who is helping get the show ready. {adult.title_word.capitalize()} {adult.id} is there too, because the mystery happens just before the show begins."
        ),
        (
            f"Why was the missing {item_cfg.label} important?",
            f"The {item_cfg.label} was needed for {item_cfg.purpose}. If it stayed missing, the audience would have to wait and the show would feel wrong."
        ),
        (
            "What clue helped solve the case?",
            f"The clue was this: {f['clue_text'].format(mark=item_cfg.clue_mark) if '{mark}' in f['clue_text'] else f['clue_text']} {detective.id} used that small sign to choose where to look next."
        ),
    ]

    if mode == "confession":
        qa.append((
            f"How did {detective.id} solve the mystery?",
            f"{detective.id} solved it by asking kindly instead of blaming anyone. That gave {helper.id} the courage to tell the truth, and together they found the {item_cfg.label} at {spot.phrase}."
        ))
    else:
        qa.append((
            f"How did {detective.id} solve the mystery?",
            f"{detective.id} solved it by following the clue carefully and searching the right place. {detective.pronoun().capitalize()} found the {item_cfg.label} at {spot.phrase}, which proved the missing prop had been moved by {cause.verb}."
        ))

    qa.append((
        "What was the lesson of the story?",
        f"The lesson was that careful thinking and kindness belong together. The mystery ended happily because the children stayed calm, told the truth, and fixed the problem before the audience had to miss the show."
    ))
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags = {"audience", "detective", "prop"}
    if world.facts["cause_id"] == "borrowed_repair":
        tags |= {"truth", "kindness"}
    if world.facts["cause_id"] == "breeze":
        tags |= {"breeze"}
    out: list[tuple[str, str]] = []
    for key in KNOWLEDGE_ORDER:
        if key in tags:
            out.extend(KNOWLEDGE[key])
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
    for e in list(world.entities.values()):
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        flags = [name for name, on in (
            ("portable", e.portable),
            ("lightweight", e.lightweight),
            ("useful_for_repair", e.useful_for_repair),
        ) if on]
        if flags:
            bits.append(f"flags={flags}")
        if e.role:
            bits.append(f"role={e.role}")
        if e.attrs:
            shown = {k: v for k, v in e.attrs.items() if v}
            if shown:
                bits.append(f"attrs={shown}")
        lines.append(f"  {e.id:12} ({e.type:10}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Curated
# ---------------------------------------------------------------------------
CURATED = [
    StoryParams(
        venue="school_hall",
        item="heart_lantern",
        cause="borrowed_repair",
        spot="repair_table",
        audience="families",
        detective_name="Nora",
        detective_gender="girl",
        helper_name="Ben",
        helper_gender="boy",
        adult_type="teacher",
    ),
    StoryParams(
        venue="library_corner",
        item="silver_pin",
        cause="breeze",
        spot="curtain_fold",
        audience="little_kids",
        detective_name="Max",
        detective_gender="boy",
        helper_name="Ruby",
        helper_gender="girl",
        adult_type="librarian",
    ),
    StoryParams(
        venue="community_room",
        item="magnifier_prop",
        cause="tidied_away",
        spot="prop_trunk",
        audience="neighbors",
        detective_name="Ella",
        detective_gender="girl",
        helper_name="Theo",
        helper_gender="boy",
        adult_type="teacher",
    ),
]


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
item_fits(I,C) :- item(I), cause(C), needs_repair_help(C), useful_for_repair(I).
item_fits(I,C) :- item(I), cause(C), needs_lightweight(C), lightweight(I).
item_fits(I,C) :- item(I), cause(C), not needs_repair_help(C), not needs_lightweight(C), portable(I).

valid(I,C,S) :- item(I), cause(C), spot(S), item_fits(I,C), cause_spot(C,S).

solution(confession) :- chosen_cause(borrowed_repair).
solution(discovery)  :- chosen_cause(C), cause(C), C != borrowed_repair.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for vid in VENUES:
        lines.append(asp.fact("venue", vid))
    for iid, item in ITEMS.items():
        lines.append(asp.fact("item", iid))
        if item.portable:
            lines.append(asp.fact("portable", iid))
        if item.lightweight:
            lines.append(asp.fact("lightweight", iid))
        if item.useful_for_repair:
            lines.append(asp.fact("useful_for_repair", iid))
    for cid, cause in CAUSES.items():
        lines.append(asp.fact("cause", cid))
        if cause.needs_repair_help:
            lines.append(asp.fact("needs_repair_help", cid))
        if cause.needs_lightweight:
            lines.append(asp.fact("needs_lightweight", cid))
        lines.append(asp.fact("cause_spot", cid, spot_for_cause(cid)))
    for sid in SPOTS:
        lines.append(asp.fact("spot", sid))
    for aid in AUDIENCES:
        lines.append(asp.fact("audience_kind", aid))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("", "#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_solution_mode(cause_id: str) -> str:
    import asp

    extra = f"chosen_cause({cause_id})."
    model = asp.one_model(asp_program(extra, "#show solution/1."))
    atoms = asp.atoms(model, "solution")
    return atoms[0][0] if atoms else "?"


def asp_verify() -> int:
    rc = 0

    clingo_set = set(asp_valid_combos())
    python_set = set(valid_combos())
    if clingo_set == python_set:
        print(f"OK: ASP gate matches valid_combos() ({len(clingo_set)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos:")
        if clingo_set - python_set:
            print("  only in clingo:", sorted(clingo_set - python_set))
        if python_set - clingo_set:
            print("  only in python:", sorted(python_set - clingo_set))

    bad = 0
    for cause_id in CAUSES:
        if asp_solution_mode(cause_id) != solution_mode(cause_id):
            bad += 1
    if bad == 0:
        print("OK: ASP solution mode matches Python for all causes.")
    else:
        rc = 1
        print(f"MISMATCH: {bad} cause outcomes differ.")

    try:
        default_params = resolve_params(build_parser().parse_args([]), random.Random(0))
        default_params.seed = 0
        sample = generate(default_params)
        if not sample.story.strip():
            raise StoryError("generated empty story")
        print("OK: smoke test generate() succeeded on a normal sample.")
    except Exception as err:  # pragma: no cover - verification path
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    try:
        emit(generate(CURATED[0]), trace=False, qa=False, header="")
        print("OK: smoke test emit() succeeded.")
    except Exception as err:  # pragma: no cover - verification path
        rc = 1
        print(f"EMIT TEST FAILED: {err}")

    return rc


# ---------------------------------------------------------------------------
# Standard interface
# ---------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="A tiny detective-story world: a missing show prop, a waiting audience, kind clue-solving, and a happy moral ending."
    )
    ap.add_argument("--venue", choices=VENUES)
    ap.add_argument("--item", choices=ITEMS)
    ap.add_argument("--cause", choices=CAUSES)
    ap.add_argument("--spot", choices=SPOTS)
    ap.add_argument("--audience", choices=AUDIENCES)
    ap.add_argument("--detective-name")
    ap.add_argument("--detective-gender", choices=["girl", "boy"])
    ap.add_argument("--helper-name")
    ap.add_argument("--helper-gender", choices=["girl", "boy"])
    ap.add_argument("--adult-type", choices=["teacher", "librarian"])
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list valid mystery combinations from clingo")
    ap.add_argument("--verify", action="store_true", help="check ASP/Python parity and run smoke tests")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def _pick_name(rng: random.Random, gender: str, avoid: str = "") -> str:
    pool = GIRL_NAMES if gender == "girl" else BOY_NAMES
    choices = [n for n in pool if n != avoid]
    return rng.choice(choices)


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.item and args.cause and args.spot:
        item = ITEMS[args.item]
        cause = CAUSES[args.cause]
        spot = SPOTS[args.spot]
        if not valid_combo(args.item, args.cause, args.spot):
            raise StoryError(explain_rejection(item, cause, spot))

    combos = [
        combo for combo in valid_combos()
        if (args.item is None or combo[0] == args.item)
        and (args.cause is None or combo[1] == args.cause)
        and (args.spot is None or combo[2] == args.spot)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    item_id, cause_id, spot_id = rng.choice(sorted(combos))
    venue_id = args.venue or rng.choice(sorted(VENUES))
    audience_id = args.audience or rng.choice(sorted(AUDIENCES))
    detective_gender = args.detective_gender or rng.choice(["girl", "boy"])
    helper_gender = args.helper_gender or rng.choice(["girl", "boy"])
    detective_name = args.detective_name or _pick_name(rng, detective_gender)
    helper_name = args.helper_name or _pick_name(rng, helper_gender, avoid=detective_name)
    adult_type = args.adult_type or rng.choice(["teacher", "librarian"])

    return StoryParams(
        venue=venue_id,
        item=item_id,
        cause=cause_id,
        spot=spot_id,
        audience=audience_id,
        detective_name=detective_name,
        detective_gender=detective_gender,
        helper_name=helper_name,
        helper_gender=helper_gender,
        adult_type=adult_type,
    )


def generate(params: StoryParams) -> StorySample:
    if params.venue not in VENUES:
        raise StoryError(f"(Unknown venue: {params.venue})")
    if params.item not in ITEMS:
        raise StoryError(f"(Unknown item: {params.item})")
    if params.cause not in CAUSES:
        raise StoryError(f"(Unknown cause: {params.cause})")
    if params.spot not in SPOTS:
        raise StoryError(f"(Unknown spot: {params.spot})")
    if params.audience not in AUDIENCES:
        raise StoryError(f"(Unknown audience: {params.audience})")
    if params.detective_gender not in {"girl", "boy"}:
        raise StoryError(f"(Unknown detective gender: {params.detective_gender})")
    if params.helper_gender not in {"girl", "boy"}:
        raise StoryError(f"(Unknown helper gender: {params.helper_gender})")
    if params.adult_type not in {"teacher", "librarian"}:
        raise StoryError(f"(Unknown adult type: {params.adult_type})")
    if not valid_combo(params.item, params.cause, params.spot):
        raise StoryError(explain_rejection(ITEMS[params.item], CAUSES[params.cause], SPOTS[params.spot]))

    world = tell(
        venue=VENUES[params.venue],
        item_cfg=ITEMS[params.item],
        cause_cfg=CAUSES[params.cause],
        spot_cfg=SPOTS[params.spot],
        audience_cfg=AUDIENCES[params.audience],
        detective_name=params.detective_name,
        detective_gender=params.detective_gender,
        helper_name=params.helper_name,
        helper_gender=params.helper_gender,
        adult_type=params.adult_type,
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
        print(asp_program("", "#show valid/3.\n#show solution/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} valid (item, cause, spot) mystery combos:\n")
        for item_id, cause_id, spot_id in combos:
            print(f"  {item_id:16} {cause_id:16} {spot_id}")
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
            header = f"### {p.detective_name}: {p.item} / {p.cause} / {p.spot}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/thud_contraction_coil_misunderstanding_space_adventure.py
====================================================================================

A standalone story world for a small Space Adventure tale built around a
misunderstanding: a child hears "contraction coil" as the name of a different
coil, brings the wrong thing, and a noisy problem lasts a little longer until a
helper clears it up.

The world model is simple but stateful:

- a small ship part is loose after a bump,
- that loose part makes a repeated thud,
- the captain asks for a contraction coil,
- the partner mishears the request and brings the wrong coil,
- a helper notices the misunderstanding,
- the correct contraction coil tightens the loose part,
- the ship grows quiet again and the children finish their space adventure
  wiser and calmer.

Run it
------
    python storyworlds/worlds/gpt-5.4/thud_contraction_coil_misunderstanding_space_adventure.py
    python storyworlds/worlds/gpt-5.4/thud_contraction_coil_misunderstanding_space_adventure.py --source seed_rack
    python storyworlds/worlds/gpt-5.4/thud_contraction_coil_misunderstanding_space_adventure.py --source window_crack
    python storyworlds/worlds/gpt-5.4/thud_contraction_coil_misunderstanding_space_adventure.py --all
    python storyworlds/worlds/gpt-5.4/thud_contraction_coil_misunderstanding_space_adventure.py --qa --json
    python storyworlds/worlds/gpt-5.4/thud_contraction_coil_misunderstanding_space_adventure.py --verify
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
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    role: str = ""
    traits: list[str] = field(default_factory=list)
    attrs: dict = field(default_factory=dict)
    tags: set[str] = field(default_factory=set)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "woman"}
        male = {"boy", "father", "man"}
        neutral = {"robot"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        if self.type in neutral:
            return {"subject": "it", "object": "it", "possessive": "its"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return {"mother": "mom", "father": "dad"}.get(self.type, self.type)


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------
    @property
    def phrase(self) -> str:
        return str(getattr(self, "_phrase", None) or getattr(self, "label_word", None) or getattr(self, "label", None) or getattr(self, "id", self.__class__.__name__.lower()))

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)


@dataclass
class Mission:
    id: str
    ship: str
    destination: str
    view: str
    opening: str
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
class Source:
    id: str
    label: str
    the: str
    nook: str
    sound: str
    needs: str
    fix_line: str
    severity: int = 1
    fixable: bool = True
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
class Coil:
    id: str
    label: str
    phrase: str
    use: str
    color: str
    works_on: set[str] = field(default_factory=set)
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
class Mishearing:
    id: str
    heard: str
    wrong_coil: str
    why: str
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
class HelperCfg:
    id: str
    name: str
    type: str
    entry: str
    explain: str
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
class Rule:
    name: str
    tag: str
    apply: Callable[["World"], list[str]]


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

    @property
    def tags(self):
        if not hasattr(self, "_tags"):
            object.__setattr__(self, "_tags", set())
        return self._tags


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
def _r_noise(world: World) -> list[str]:
    out: list[str] = []
    source = world.get("source")
    if source.meters["loose"] < THRESHOLD:
        return out
    sig = ("noise", source.id, int(source.meters["loose"]))
    if sig in world.fired:
        return out
    world.fired.add(sig)
    ship = world.get("ship")
    captain = world.get("captain")
    partner = world.get("partner")
    ship.meters["noise"] += 1
    captain.memes["worry"] += 1
    partner.memes["worry"] += 1
    out.append("__thud__")
    return out


def _r_wrong_tool(world: World) -> list[str]:
    out: list[str] = []
    source = world.get("source")
    delivered = world.facts.get("delivered_coil")
    if source.meters["loose"] < THRESHOLD or delivered != "wrong":
        return out
    sig = ("wrong_tool", source.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    captain = world.get("captain")
    partner = world.get("partner")
    captain.memes["frustration"] += 1
    partner.memes["embarrassment"] += 1
    world.facts["extra_thud"] = True
    out.append("__delay__")
    return out


def _r_fix(world: World) -> list[str]:
    out: list[str] = []
    source = world.get("source")
    if source.meters["fixed"] < THRESHOLD:
        return out
    sig = ("fixed", source.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    source.meters["loose"] = 0.0
    world.get("ship").meters["noise"] = 0.0
    for eid in ("captain", "partner", "helper"):
        world.get(eid).memes["relief"] += 1
        world.get(eid).memes["worry"] = 0.0
    out.append("__quiet__")
    return out


CAUSAL_RULES = [
    Rule(name="noise", tag="physical", apply=_r_noise),
    Rule(name="wrong_tool", tag="social", apply=_r_wrong_tool),
    Rule(name="fix", tag="physical", apply=_r_fix),
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
# Constraints and helpers
# ---------------------------------------------------------------------------
def source_needs_contraction_coil(source: Source) -> bool:
    return source.fixable and source.needs == "contraction_coil"


def misunderstanding_available(mis: Mishearing) -> bool:
    return mis.wrong_coil in COILS and mis.wrong_coil != "contraction_coil"


def valid_combos() -> list[tuple[str, str, str, str]]:
    combos: list[tuple[str, str, str, str]] = []
    for mission_id in MISSIONS:
        for source_id, source in SOURCES.items():
            if not source_needs_contraction_coil(source):
                continue
            for mis_id, mis in MISHEARINGS.items():
                if not misunderstanding_available(mis):
                    continue
                for helper_id in HELPERS:
                    combos.append((mission_id, source_id, mis_id, helper_id))
    return combos


def explain_rejection(source: Source) -> str:
    if not source.fixable:
        return (
            f"(No story: {source.the} is not a loose part at all. A contraction coil "
            f"cannot fix something that is broken in a different way.)"
        )
    if source.needs != "contraction_coil":
        return (
            f"(No story: {source.the} does not use a contraction coil. This world is "
            f"about a misunderstanding over that specific repair part, so pick a "
            f"source that really needs one.)"
        )
    return "(No story: this source does not fit the repair logic of the world.)"


def explain_mishearing(mis: Mishearing) -> str:
    return (
        f"(No story: the mishearing '{mis.heard}' does not point to a different coil "
        f"that exists on the ship, so the misunderstanding would not be concrete.)"
    )


def validate_params(params: "StoryParams") -> None:
    if params.mission not in MISSIONS:
        raise StoryError(f"(Unknown mission: {params.mission})")
    if params.source not in SOURCES:
        raise StoryError(f"(Unknown source: {params.source})")
    if params.mishearing not in MISHEARINGS:
        raise StoryError(f"(Unknown mishearing: {params.mishearing})")
    if params.helper not in HELPERS:
        raise StoryError(f"(Unknown helper: {params.helper})")
    if params.captain_gender not in {"girl", "boy"}:
        raise StoryError(f"(Unknown captain gender: {params.captain_gender})")
    if params.partner_gender not in {"girl", "boy"}:
        raise StoryError(f"(Unknown partner gender: {params.partner_gender})")

    source = SOURCES[params.source]
    mis = MISHEARINGS[params.mishearing]
    if not source_needs_contraction_coil(source):
        raise StoryError(explain_rejection(source))
    if not misunderstanding_available(mis):
        raise StoryError(explain_mishearing(mis))


def predict_thud(world: World) -> dict:
    sim = world.copy()
    sim.get("source").meters["loose"] = 1.0
    propagate(sim, narrate=False)
    return {
        "noise": sim.get("ship").meters["noise"],
        "worry": sim.get("captain").memes["worry"] + sim.get("partner").memes["worry"],
    }


# ---------------------------------------------------------------------------
# Story actions
# ---------------------------------------------------------------------------
def introduce(world: World, mission: Mission, captain: Entity, partner: Entity, helper: Entity) -> None:
    captain.memes["joy"] += 1
    partner.memes["joy"] += 1
    world.say(
        f"{captain.id} and {partner.id} were junior star sailors aboard the little "
        f"ship {mission.ship}. They were on their way to {mission.destination}, and "
        f"{mission.opening}"
    )
    world.say(
        f"{helper.id} {helper.attrs['entry']} while the children took turns peeking "
        f"through the round window at {mission.view}."
    )


def bump(world: World, source_cfg: Source, captain: Entity, partner: Entity) -> None:
    source = world.get("source")
    source.meters["loose"] = 1.0
    propagate(world, narrate=False)
    world.say(
        f"Then, from {source_cfg.nook}, came a sudden thud. "
        f"{source_cfg.sound}"
    )
    world.say(
        f"{captain.id} grabbed the rail, and {partner.id} looked up with wide eyes."
    )


def inspect(world: World, source_cfg: Source, captain: Entity) -> None:
    pred = predict_thud(world)
    world.facts["predicted_noise"] = pred["noise"]
    world.say(
        f"{captain.id} crawled over and saw that {source_cfg.the} had slipped loose. "
        f'"We need the contraction coil from the repair tray," {captain.pronoun()} said.'
    )


def mishear(world: World, mis: Mishearing, partner: Entity) -> None:
    partner.memes["confidence"] += 1
    world.say(
        f"But another little thud knocked against the wall, and {partner.id} heard "
        f'"{mis.heard}" instead. {mis.why}'
    )


def fetch_wrong(world: World, mis: Mishearing, wrong: Coil, partner: Entity) -> None:
    world.facts["delivered_coil"] = "wrong"
    propagate(world, narrate=False)
    world.say(
        f"{partner.id} hurried to the storage bins and came back with {wrong.phrase}, "
        f"a {wrong.color} coil used to {wrong.use}."
    )
    world.say(
        f'"Here it is!" {partner.pronoun()} said, proud and out of breath.'
    )


def extra_thud(world: World, source_cfg: Source) -> None:
    world.get("source").meters["loose"] += 1.0
    propagate(world, narrate=False)
    world.say(
        f"But {source_cfg.the} gave another heavy thud, louder than before, and the "
        f"little ship did not grow quiet."
    )


def clarify(world: World, helper_cfg: HelperCfg, mis: Mishearing, wrong: Coil, helper: Entity,
            captain: Entity, partner: Entity) -> None:
    partner.memes["embarrassment"] += 1
    world.say(
        f"{helper.id} {helper_cfg.explain} {wrong.label} in {partner.id}'s hands and "
        f"gently shook {helper.pronoun('possessive')} head."
    )
    world.say(
        f'"That is the {wrong.label}," {helper.pronoun()} said. '
        f'"{captain.id} asked for the contraction coil."'
    )
    world.say(
        f"{partner.id} blinked, then nodded. The misunderstanding made {partner.pronoun('object')} "
        f"blush, but {captain.id} only said, \"Let's say it together this time.\""
    )
    world.facts["heard_as"] = mis.heard


def fetch_right(world: World, right: Coil, partner: Entity, captain: Entity) -> None:
    world.facts["delivered_coil"] = "right"
    world.say(
        f'Together they repeated the words slowly: "con-TRAC-tion coil." '
        f"{partner.id} darted back and returned with {right.phrase}, the {right.color} coil "
        f"that could {right.use}."
    )
    world.say(
        f"{captain.id} smiled at once. \"Yes,\" {captain.pronoun()} said. \"That is the right one.\""
    )


def repair(world: World, source_cfg: Source, captain: Entity, partner: Entity, helper: Entity) -> None:
    source = world.get("source")
    source.meters["fixed"] = 1.0
    propagate(world, narrate=False)
    captain.memes["skill"] += 1
    partner.memes["skill"] += 1
    world.say(
        f"{captain.id} and {partner.id} clipped the contraction coil into place while "
        f"{helper.id} held a lamp steady. {source_cfg.fix_line}"
    )
    world.say(
        f"The next moment there was no thud at all, only the soft humming of the ship."
    )


def ending(world: World, mission: Mission, captain: Entity, partner: Entity, helper: Entity) -> None:
    captain.memes["trust"] += 1
    partner.memes["trust"] += 1
    partner.memes["lesson"] += 1
    world.say(
        f"With the noise gone, the three travelers floated back to the window and watched "
        f"{mission.view} drift past the glass."
    )
    world.say(
        f'"In space," {helper.id} said, "small words matter." '
        f"{partner.id} squeezed the correct coil case and nodded. "
        f'From then on, whenever a job sounded important, the crew repeated it twice before they ran.'
    )


# ---------------------------------------------------------------------------
# Screenplay
# ---------------------------------------------------------------------------
def tell(
    mission: Mission,
    source_cfg: Source,
    mis: Mishearing,
    helper_cfg: HelperCfg,
    captain_name: str = "Nova",
    captain_gender: str = "girl",
    partner_name: str = "Milo",
    partner_gender: str = "boy",
) -> World:
    world = World()

    captain = world.add(Entity(
        id=captain_name,
        kind="character",
        type=captain_gender,
        label=captain_name,
        role="captain",
        attrs={"entry": "checked the map", "heard": ""},
    ))
    partner = world.add(Entity(
        id=partner_name,
        kind="character",
        type=partner_gender,
        label=partner_name,
        role="partner",
        attrs={"heard": mis.heard},
    ))
    helper = world.add(Entity(
        id=helper_cfg.name,
        kind="character",
        type=helper_cfg.type,
        label=helper_cfg.name,
        role="helper",
        attrs={"entry": helper_cfg.entry},
        tags=set(helper_cfg.tags),
    ))
    ship = world.add(Entity(id="ship", kind="thing", type="ship", label=mission.ship))
    source = world.add(Entity(
        id="source",
        kind="thing",
        type="part",
        label=source_cfg.label,
        role="source",
        tags=set(source_cfg.tags),
    ))

    for ent in (captain, partner, helper, ship, source):
        ent.meters["noise"] = 0.0
        ent.meters["loose"] = 0.0
        ent.meters["fixed"] = 0.0
        ent.memes["worry"] = 0.0
        ent.memes["relief"] = 0.0

    world.facts.update(
        mission=mission,
        source_cfg=source_cfg,
        mis=mis,
        helper_cfg=helper_cfg,
        captain=captain,
        partner=partner,
        helper=helper,
        ship=ship,
        delivered_coil="none",
        extra_thud=False,
        heard_as="",
    )

    introduce(world, mission, captain, partner, helper)
    world.para()
    bump(world, source_cfg, captain, partner)
    inspect(world, source_cfg, captain)
    mishear(world, mis, partner)
    fetch_wrong(world, mis, COILS[mis.wrong_coil], partner)
    extra_thud(world, source_cfg)
    world.para()
    clarify(world, helper_cfg, mis, COILS[mis.wrong_coil], helper, captain, partner)
    fetch_right(world, COILS["contraction_coil"], partner, captain)
    repair(world, source_cfg, captain, partner, helper)
    world.para()
    ending(world, mission, captain, partner, helper)

    world.facts.update(
        outcome="resolved",
        wrong_coil=COILS[mis.wrong_coil],
        right_coil=COILS["contraction_coil"],
        misunderstanding=True,
        quiet=world.get("ship").meters["noise"] < THRESHOLD,
    )
    return world


# ---------------------------------------------------------------------------
# Content
# ---------------------------------------------------------------------------
MISSIONS = {
    "comet": Mission(
        id="comet",
        ship="the Bright Kite",
        destination="the silver tail of Comet Luma",
        view="a long ribbon of ice and light",
        opening="their paper star charts were spread open across the little bridge",
        tags={"space", "comet"},
    ),
    "rings": Mission(
        id="rings",
        ship="the Bright Kite",
        destination="the blue rings of Planet Neri",
        view="curving bands that looked like spilled glitter",
        opening="they had packed berry snacks and a tiny telescope for the trip",
        tags={"space", "rings"},
    ),
    "garden": Mission(
        id="garden",
        ship="the Bright Kite",
        destination="the moon garden station",
        view="glass domes full of floating green vines",
        opening="their job was to deliver seed packets and wave to the gardeners",
        tags={"space", "garden"},
    ),
}

SOURCES = {
    "map_tube": Source(
        id="map_tube",
        label="star-map tube",
        the="the star-map tube",
        nook="the chart shelf",
        sound="The round tube rolled inside its brackets and knocked the wall again.",
        needs="contraction_coil",
        fix_line="The coil tightened around the tube's ring and held it snug against the shelf.",
        severity=1,
        fixable=True,
        tags={"map_tube", "coil"},
    ),
    "seed_rack": Source(
        id="seed_rack",
        label="seed rack",
        the="the seed rack",
        nook="the garden locker",
        sound="A tray of seed pods wobbled in its frame and bumped the locker door.",
        needs="contraction_coil",
        fix_line="The coil hugged the rack's loop, and the tray stopped wobbling at once.",
        severity=1,
        fixable=True,
        tags={"seed_rack", "coil"},
    ),
    "snack_canister": Source(
        id="snack_canister",
        label="snack canister",
        the="the snack canister",
        nook="the snack drawer",
        sound="The canister skipped against the drawer rail with each tiny drift of the ship.",
        needs="contraction_coil",
        fix_line="The coil cinched the rail clasp, and the canister settled without another knock.",
        severity=1,
        fixable=True,
        tags={"snack", "coil"},
    ),
    "window_crack": Source(
        id="window_crack",
        label="window crack",
        the="the window crack",
        nook="the forward window",
        sound="A pale line shimmered across the glass, which was far more serious than a loose rattle.",
        needs="seal_patch",
        fix_line="",
        severity=3,
        fixable=True,
        tags={"window"},
    ),
    "meteor_hole": Source(
        id="meteor_hole",
        label="meteor hole",
        the="the meteor hole",
        nook="the outer hull",
        sound="The hull had been punched through, which called for a rescue, not a little repair coil.",
        needs="rescue",
        fix_line="",
        severity=4,
        fixable=False,
        tags={"danger"},
    ),
}

COILS = {
    "contraction_coil": Coil(
        id="contraction_coil",
        label="contraction coil",
        phrase="the contraction coil",
        use="shrink tight around a loose ring and hold it still",
        color="green",
        works_on={"map_tube", "seed_rack", "snack_canister"},
        tags={"coil", "repair"},
    ),
    "traction_coil": Coil(
        id="traction_coil",
        label="traction coil",
        phrase="the traction coil",
        use="help the rover wheels grip dusty ground",
        color="orange",
        works_on=set(),
        tags={"coil", "rover"},
    ),
    "collector_coil": Coil(
        id="collector_coil",
        label="collector coil",
        phrase="the collector coil",
        use="pull stray leaf bits into the garden vacuum",
        color="blue",
        works_on=set(),
        tags={"coil", "garden_tool"},
    ),
    "connector_coil": Coil(
        id="connector_coil",
        label="connector coil",
        phrase="the connector coil",
        use="bundle soft wires neatly behind the signal board",
        color="silver",
        works_on=set(),
        tags={"coil", "wires"},
    ),
}

MISHEARINGS = {
    "traction": Mishearing(
        id="traction",
        heard="traction coil",
        wrong_coil="traction_coil",
        why="The words sounded close in the rattly bridge, so the mistake felt sensible for one quick second.",
        tags={"misunderstanding", "coil"},
    ),
    "collector": Mishearing(
        id="collector",
        heard="collector coil",
        wrong_coil="collector_coil",
        why="The children had visited the moon garden last week, so that tool name jumped into memory first.",
        tags={"misunderstanding", "coil"},
    ),
    "connector": Mishearing(
        id="connector",
        heard="connector coil",
        wrong_coil="connector_coil",
        why="The radio crackled at the same moment, and the extra sound bent the word in the air.",
        tags={"misunderstanding", "coil"},
    ),
}

HELPERS = {
    "robot": HelperCfg(
        id="robot",
        name="Pip",
        type="robot",
        entry="hovered nearby on a soft fan and blinked a small gold light",
        explain="tilted its round head, glanced from the repair tray to the",
        tags={"robot", "help"},
    ),
    "mother": HelperCfg(
        id="mother",
        name="Mom",
        type="mother",
        entry="checked the ship log and kept one hand near the steadying rail",
        explain="looked at the labels, then at the",
        tags={"parent", "help"},
    ),
    "father": HelperCfg(
        id="father",
        name="Dad",
        type="father",
        entry="watched the star map and smiled at their careful teamwork",
        explain="followed the children's eyes, then pointed at the",
        tags={"parent", "help"},
    ),
}

GIRL_NAMES = ["Nova", "Luna", "Mira", "Tess", "Ivy", "Nina", "Zara", "Ari"]
BOY_NAMES = ["Milo", "Leo", "Finn", "Jude", "Otis", "Kai", "Ezra", "Theo"]


# ---------------------------------------------------------------------------
# Story parameters
# ---------------------------------------------------------------------------
@dataclass
class StoryParams:
    mission: str
    source: str
    mishearing: str
    helper: str
    captain_name: str
    captain_gender: str
    partner_name: str
    partner_gender: str
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
    "coil": [
        (
            "What is a coil?",
            "A coil is something wound in loops, like a spring or a curled piece of metal. Some coils are made to squeeze, hold, or help other parts move."
        )
    ],
    "repair": [
        (
            "What does a contraction coil do?",
            "A contraction coil tightens when it is put in place. That makes it useful for holding a loose part still."
        )
    ],
    "misunderstanding": [
        (
            "What is a misunderstanding?",
            "A misunderstanding happens when someone hears or understands something the wrong way. It can be fixed by slowing down, checking the words, and listening again."
        )
    ],
    "robot": [
        (
            "How can a robot helper be useful on a ship?",
            "A robot helper can carry light, read labels, and notice small details. That makes repairs calmer and safer."
        )
    ],
    "space": [
        (
            "Why can loose things bump around inside a spaceship?",
            "In a moving ship, even a small loose object can drift or rattle when the ship shakes. If it is not clipped down, it may knock into a wall with a thud."
        )
    ],
    "comet": [
        (
            "What is a comet?",
            "A comet is a ball of ice and dust that travels through space. When it gets near the sun, it can grow a bright tail."
        )
    ],
    "rings": [
        (
            "What are planet rings?",
            "Planet rings are wide bands of ice, dust, and tiny rocks that circle some planets. From far away, they can look like shining stripes."
        )
    ],
    "garden": [
        (
            "What might grow in a space garden?",
            "A space garden can grow plants for food, seeds, or fresh air. The plants are usually cared for very carefully."
        )
    ],
}

KNOWLEDGE_ORDER = ["misunderstanding", "coil", "repair", "space", "robot", "comet", "rings", "garden"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    mission = f["mission"]
    source_cfg = f["source_cfg"]
    captain = f["captain"]
    partner = f["partner"]
    helper = f["helper"]
    mis = f["mis"]
    return [
        f'Write a short Space Adventure story for a 3-to-5-year-old that includes the words "thud", "contraction", and "coil".',
        f"Tell a gentle space story where {captain.id} asks for a contraction coil, but {partner.id} misunderstands and brings the wrong coil after hearing a thud near {source_cfg.the}.",
        f"Write a story set on a tiny spaceship headed to {mission.destination}, where a misunderstanding is solved by {helper.id} and the ship grows quiet again.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    captain = f["captain"]
    partner = f["partner"]
    helper = f["helper"]
    mission = f["mission"]
    source_cfg = f["source_cfg"]
    wrong = f["wrong_coil"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {captain.id} and {partner.id}, two junior star sailors, and {helper.id} who helps them on {mission.ship}. They are traveling through space on a small adventure."
        ),
        (
            "What was making the thud sound?",
            f"{source_cfg.The} had slipped loose and kept knocking from {source_cfg.nook}. The thud mattered because it told the crew that something needed to be held still again."
        ),
        (
            f"Why did {partner.id} bring the wrong coil?",
            f"{partner.id} misunderstood the words and heard \"{f['heard_as']}\" instead of \"contraction coil.\" The extra noise on the ship made the mistake easier to make."
        ),
        (
            f"How did {helper.id} fix the misunderstanding?",
            f"{helper.id} looked at the label and explained that {wrong.label} was a different tool. Then everyone repeated the words slowly so {partner.id} could fetch the correct contraction coil."
        ),
        (
            "How was the problem solved?",
            f"The children clipped the contraction coil into place and tightened the loose part. After that, the ship stopped making the thud and the bridge felt calm again."
        ),
        (
            "How did the story end?",
            f"It ended quietly, with the crew back at the window watching {mission.view}. The ending shows what changed, because they now repeat important repair words before they rush off."
        ),
    ]
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags: set[str] = {"misunderstanding", "coil", "repair", "space"}
    mission = world.facts["mission"]
    helper = world.facts["helper"]
    tags |= set(mission.tags)
    tags |= set(helper.tags)
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
            shown = {k: v for k, v in e.attrs.items() if v}
            if shown:
                bits.append(f"attrs={shown}")
        lines.append(f"  {e.id:10} ({e.type:8}) {' '.join(bits)}")
    lines.append(f"  facts: delivered_coil={world.facts.get('delivered_coil')} extra_thud={world.facts.get('extra_thud')}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Curated
# ---------------------------------------------------------------------------
CURATED = [
    StoryParams(
        mission="comet",
        source="map_tube",
        mishearing="traction",
        helper="robot",
        captain_name="Nova",
        captain_gender="girl",
        partner_name="Milo",
        partner_gender="boy",
    ),
    StoryParams(
        mission="garden",
        source="seed_rack",
        mishearing="collector",
        helper="mother",
        captain_name="Luna",
        captain_gender="girl",
        partner_name="Finn",
        partner_gender="boy",
    ),
    StoryParams(
        mission="rings",
        source="snack_canister",
        mishearing="connector",
        helper="father",
        captain_name="Kai",
        captain_gender="boy",
        partner_name="Mira",
        partner_gender="girl",
    ),
]


# ---------------------------------------------------------------------------
# ASP
# ---------------------------------------------------------------------------
ASP_RULES = r"""
needs_contraction(S) :- source(S), source_fix(S, contraction_coil), fixable(S).
valid(M, S, H, P) :- mission(M), helper(P), mishearing(H), heard_as(H, Heard),
                     wrong_for(H, Wrong), coil(Wrong), Wrong != contraction_coil,
                     source(S), needs_contraction(S).

% whether the story gets the extra thud beat before the misunderstanding is fixed
extra_thud(P) :- helper(P), slow_helper(P).
extra_thud(P) :- helper(P), not slow_helper(P).
#show valid/4.
"""

def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for mission_id in MISSIONS:
        lines.append(asp.fact("mission", mission_id))
    for source_id, source in SOURCES.items():
        lines.append(asp.fact("source", source_id))
        if source.fixable:
            lines.append(asp.fact("fixable", source_id))
        lines.append(asp.fact("source_fix", source_id, source.needs))
    for coil_id in COILS:
        lines.append(asp.fact("coil", coil_id))
    for mis_id, mis in MISHEARINGS.items():
        lines.append(asp.fact("mishearing", mis_id))
        lines.append(asp.fact("heard_as", mis_id, mis.heard))
        lines.append(asp.fact("wrong_for", mis_id, mis.wrong_coil))
    for helper_id, helper in HELPERS.items():
        lines.append(asp.fact("helper", helper_id))
        if helper_id in {"mother", "father"}:
            lines.append(asp.fact("slow_helper", helper_id))
    return "\n".join(lines)


def asp_program(extra: str = "", show: str = "#show valid/4.") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program(show="#show valid/4."))
    return sorted(set(asp.atoms(model, "valid")))


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

    try:
        sample = generate(CURATED[0])
        if not sample.story.strip():
            raise StoryError("(Smoke test failed: empty story.)")
        print("OK: smoke generation succeeded.")
    except Exception as err:  # pragma: no cover
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    parser = build_parser()
    checked = 0
    for seed in range(20):
        try:
            args = parser.parse_args(["--seed", str(seed)])
            params = resolve_params(args, random.Random(seed))
            params.seed = seed
            sample = generate(params)
            if not sample.story.strip():
                raise StoryError("(Generated empty story.)")
            checked += 1
        except Exception as err:  # pragma: no cover
            rc = 1
            print(f"RANDOM GENERATION FAILED at seed {seed}: {err}")
            break
    if checked:
        print(f"OK: generated {checked} seeded stories without crashing.")

    return rc


# ---------------------------------------------------------------------------
# Standard interface
# ---------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Story world sketch: a misunderstanding over a contraction coil during a small space adventure."
    )
    ap.add_argument("--mission", choices=MISSIONS)
    ap.add_argument("--source", choices=SOURCES)
    ap.add_argument("--mishearing", choices=MISHEARINGS)
    ap.add_argument("--helper", choices=HELPERS)
    ap.add_argument("--captain-name")
    ap.add_argument("--captain-gender", choices=["girl", "boy"])
    ap.add_argument("--partner-name")
    ap.add_argument("--partner-gender", choices=["girl", "boy"])
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list the compatible-story set derived by clingo")
    ap.add_argument("--verify", action="store_true", help="check the inline ASP reasoner matches the Python logic and run smoke tests")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def _pick_name(rng: random.Random, gender: str, avoid: str = "") -> str:
    pool = GIRL_NAMES if gender == "girl" else BOY_NAMES
    options = [n for n in pool if n != avoid]
    return rng.choice(options)


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.source:
        source = SOURCES[args.source]
        if not source_needs_contraction_coil(source):
            raise StoryError(explain_rejection(source))
    if args.mishearing:
        mis = MISHEARINGS[args.mishearing]
        if not misunderstanding_available(mis):
            raise StoryError(explain_mishearing(mis))

    combos = [
        c for c in valid_combos()
        if (args.mission is None or c[0] == args.mission)
        and (args.source is None or c[1] == args.source)
        and (args.mishearing is None or c[2] == args.mishearing)
        and (args.helper is None or c[3] == args.helper)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    mission, source, mishearing, helper = rng.choice(sorted(combos))
    captain_gender = args.captain_gender or rng.choice(["girl", "boy"])
    partner_gender = args.partner_gender or rng.choice(["girl", "boy"])
    captain_name = args.captain_name or _pick_name(rng, captain_gender)
    partner_name = args.partner_name or _pick_name(rng, partner_gender, avoid=captain_name)

    params = StoryParams(
        mission=mission,
        source=source,
        mishearing=mishearing,
        helper=helper,
        captain_name=captain_name,
        captain_gender=captain_gender,
        partner_name=partner_name,
        partner_gender=partner_gender,
    )
    validate_params(params)
    return params


def generate(params: StoryParams) -> StorySample:
    validate_params(params)

    world = tell(
        mission=MISSIONS[params.mission],
        source_cfg=SOURCES[params.source],
        mis=MISHEARINGS[params.mishearing],
        helper_cfg=HELPERS[params.helper],
        captain_name=params.captain_name,
        captain_gender=params.captain_gender,
        partner_name=params.partner_name,
        partner_gender=params.partner_gender,
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
        print(f"{len(combos)} compatible (mission, source, mishearing, helper) combos:\n")
        for mission, source, mishearing, helper in combos:
            print(f"  {mission:8} {source:14} {mishearing:10} {helper}")
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
            header = f"### {p.captain_name} & {p.partner_name}: {p.source} on {p.mission} ({p.helper})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()

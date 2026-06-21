#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/girl_rare_teamwork_space_adventure.py
================================================================

A standalone story world for a tiny space-adventure domain: a girl and a partner
pretend to be space explorers, discover a rare object in a hard-to-reach place,
and solve the problem through teamwork instead of a risky solo grab.

The world is driven by simulated state:
- a rare sample sits beyond an obstacle,
- a child first leans toward a solo attempt,
- the world model predicts or triggers wobble/risk,
- a cooperative method succeeds only when it truly matches the obstacle and the
  sample's physical needs,
- the ending image proves that teamwork changed the outcome.

Run it
------
    python storyworlds/worlds/gpt-5.4/girl_rare_teamwork_space_adventure.py
    python storyworlds/worlds/gpt-5.4/girl_rare_teamwork_space_adventure.py --mission moonbase --obstacle high_ledge --sample moon_crystal
    python storyworlds/worlds/gpt-5.4/girl_rare_teamwork_space_adventure.py --method magnet_hook
    python storyworlds/worlds/gpt-5.4/girl_rare_teamwork_space_adventure.py --all
    python storyworlds/worlds/gpt-5.4/girl_rare_teamwork_space_adventure.py -n 5 --seed 7 --qa
    python storyworlds/worlds/gpt-5.4/girl_rare_teamwork_space_adventure.py --verify
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
    role: str = ""
    traits: list[str] = field(default_factory=list)
    attrs: dict = field(default_factory=dict)
    tags: set[str] = field(default_factory=set)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "woman"}
        male = {"boy", "father", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]


# ---------------------------------------------------------------------------
# Registries
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


@dataclass
class Mission:
    id: str
    scene: str
    ship: str
    goal: str
    sendoff: str
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
class Obstacle:
    id: str
    label: str
    site: str
    need: str
    risk: str
    risk_text: str
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
class RareSample:
    id: str
    label: str
    phrase: str
    shine: str
    weight: int
    fragile: bool
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
class Method:
    id: str
    label: str
    supports: set[str]
    power: int
    gentle: bool
    setup: str
    action: str
    qa_text: str
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

    def kids(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.role in {"captain", "partner"}]

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
        clone.paragraphs = [[]]
        clone.fired = set(self.fired)
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


def _r_solo_risk(world: World) -> list[str]:
    hero = world.entities.get("captain")
    room = world.entities.get("zone")
    if hero is None or room is None:
        return []
    if hero.meters["rushing"] < THRESHOLD:
        return []
    sig = ("solo_risk", world.facts.get("obstacle_id", ""))
    if sig in world.fired:
        return []
    world.fired.add(sig)
    hero.meters["off_balance"] += 1
    hero.memes["fear"] += 1
    room.meters["risk"] += 1
    for kid in world.kids():
        kid.memes["focus"] += 1
    return ["__risk__"]


def _r_teamwork_success(world: World) -> list[str]:
    hero = world.entities.get("captain")
    partner = world.entities.get("partner")
    sample = world.entities.get("sample")
    zone = world.entities.get("zone")
    if hero is None or partner is None or sample is None or zone is None:
        return []
    if hero.meters["using_method"] < THRESHOLD or partner.meters["using_method"] < THRESHOLD:
        return []
    sig = ("teamwork_success", world.facts.get("method_id", ""), world.facts.get("sample_id", ""))
    if sig in world.fired:
        return []
    world.fired.add(sig)
    sample.meters["retrieved"] += 1
    hero.memes["trust"] += 1
    partner.memes["trust"] += 1
    hero.memes["joy"] += 1
    partner.memes["joy"] += 1
    zone.meters["risk"] = 0.0
    return ["__retrieved__"]


def _r_mission_complete(world: World) -> list[str]:
    sample = world.entities.get("sample")
    ship = world.entities.get("ship")
    if sample is None or ship is None:
        return []
    if sample.meters["retrieved"] < THRESHOLD:
        return []
    sig = ("mission_complete", sample.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    ship.meters["mission_success"] += 1
    for kid in world.kids():
        kid.memes["pride"] += 1
    return ["__mission__"]


CAUSAL_RULES = [
    Rule(name="solo_risk", tag="physical", apply=_r_solo_risk),
    Rule(name="teamwork_success", tag="social", apply=_r_teamwork_success),
    Rule(name="mission_complete", tag="social", apply=_r_mission_complete),
]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
        changed = False
        for rule in CAUSAL_RULES:
            res = rule.apply(world)
            if res:
                changed = True
                produced.extend(x for x in res if not x.startswith("__"))
    if narrate:
        for line in produced:
            world.say(line)
    return produced


# ---------------------------------------------------------------------------
# Constraint helpers
# ---------------------------------------------------------------------------
def method_fits(obstacle: Obstacle, sample: RareSample, method: Method) -> bool:
    if obstacle.need not in method.supports:
        return False
    if method.power < sample.weight:
        return False
    if sample.fragile and not method.gentle:
        return False
    return True


def valid_combos() -> list[tuple[str, str, str, str]]:
    combos: list[tuple[str, str, str, str]] = []
    for mission_id in MISSIONS:
        for obstacle_id, obstacle in OBSTACLES.items():
            for sample_id, sample in SAMPLES.items():
                for method_id, method in METHODS.items():
                    if method_fits(obstacle, sample, method):
                        combos.append((mission_id, obstacle_id, sample_id, method_id))
    return combos


def explain_rejection(obstacle: Obstacle, sample: RareSample, method: Method) -> str:
    if obstacle.need not in method.supports:
        return (
            f"(No story: {method.label} does not solve {obstacle.site}. "
            f"That obstacle needs a teamwork move for {obstacle.need}.)"
        )
    if method.power < sample.weight:
        return (
            f"(No story: {sample.phrase} is too heavy for {method.label}. "
            f"The method must be strong enough to bring the rare sample back.)"
        )
    if sample.fragile and not method.gentle:
        return (
            f"(No story: {sample.phrase} is too delicate for {method.label}. "
            f"The team needs a gentler way to carry it.)"
        )
    return "(No story: that combination is not reasonable.)"


def predict_solo_risk(world: World) -> dict:
    sim = world.copy()
    sim.get("captain").meters["rushing"] += 1
    propagate(sim, narrate=False)
    return {
        "off_balance": sim.get("captain").meters["off_balance"] >= THRESHOLD,
        "risk": sim.get("zone").meters["risk"],
    }


# ---------------------------------------------------------------------------
# Story verbs
# ---------------------------------------------------------------------------
def intro(world: World, captain: Entity, partner: Entity, mission: Mission) -> None:
    captain.memes["joy"] += 1
    partner.memes["joy"] += 1
    world.say(
        f"{captain.id} was a brave girl who loved turning ordinary afternoons into space missions. "
        f"That day, {captain.id} and {partner.id} made {mission.scene}; {mission.ship}."
    )
    world.say(
        f'"Captain {captain.id}," {partner.id} said, saluting. '
        f'"Ready for {mission.goal}?"'
    )


def discover(world: World, captain: Entity, partner: Entity, obstacle: Obstacle, sample: RareSample) -> None:
    sample_ent = world.get("sample")
    sample_ent.meters["seen"] += 1
    world.say(
        f"Past {obstacle.site}, they spotted {sample.phrase}. It {sample.shine}, and both children stared."
    )
    world.say(
        f'"That must be the rare find for our mission," {captain.id} whispered. '
        f'"If we can bring it back, our ship will have a new treasure shelf."'
    )


def tempt(world: World, captain: Entity, obstacle: Obstacle) -> None:
    captain.memes["eagerness"] += 1
    world.say(
        f"{captain.id} took one quick step toward {obstacle.site}. "
        f"Doing it alone looked faster for one tiny second."
    )


def warn(world: World, captain: Entity, partner: Entity, obstacle: Obstacle, sample: RareSample) -> None:
    pred = predict_solo_risk(world)
    world.facts["predicted_risk"] = pred["risk"]
    extra = ""
    if sample.fragile:
        extra = f" And if it slipped, the rare {sample.label} could break."
    world.say(
        f'{partner.id} reached out and shook {partner.pronoun("possessive")} head. '
        f'"Wait, Captain. {obstacle.risk_text}.{extra} We need to do this together."'
    )


def wobble(world: World, captain: Entity, obstacle: Obstacle) -> None:
    captain.meters["rushing"] += 1
    propagate(world, narrate=False)
    if captain.meters["off_balance"] >= THRESHOLD:
        world.say(
            f"But as {captain.id} leaned in, {captain.pronoun("subject")} felt a wobble under {captain.pronoun("possessive")} feet and stopped. "
            f"{obstacle.risk.capitalize()} suddenly felt real."
        )


def choose_method(world: World, captain: Entity, partner: Entity, method: Method) -> None:
    captain.memes["care"] += 1
    partner.memes["care"] += 1
    world.say(
        f'{captain.id} looked at {partner.id}, then nodded. "{method.setup}," '
        f'{captain.pronoun("subject")} said.'
    )


def teamwork_retrieve(world: World, captain: Entity, partner: Entity, sample: RareSample, method: Method) -> None:
    captain.meters["using_method"] += 1
    partner.meters["using_method"] += 1
    propagate(world, narrate=False)
    world.say(method.action.format(captain=captain.id, partner=partner.id, sample=sample.label))
    if world.get("sample").meters["retrieved"] >= THRESHOLD:
        world.say(
            f"The rare {sample.label} came free at last and rested safely in both of their hands."
        )


def celebrate(world: World, captain: Entity, partner: Entity, mission: Mission, sample: RareSample) -> None:
    world.say(
        f'They carried {sample.phrase} back to the ship together. '
        f'"Teamwork did it," {partner.id} said, grinning.'
    )
    world.say(
        f"{captain.id} set it in their pretend control room, where it glimmered like a small new star. "
        f"Then the two explorers {mission.sendoff}."
    )


def tell(
    mission: Mission,
    obstacle: Obstacle,
    sample_cfg: RareSample,
    method: Method,
    captain_name: str = "Nia",
    partner_name: str = "Owen",
    partner_type: str = "boy",
) -> World:
    world = World()
    captain = world.add(Entity(id="captain", kind="character", type="girl", label=captain_name, role="captain"))
    partner = world.add(Entity(id="partner", kind="character", type=partner_type, label=partner_name, role="partner"))
    ship = world.add(Entity(id="ship", type="ship", label="ship"))
    zone = world.add(Entity(id="zone", type="place", label=obstacle.label))
    sample = world.add(
        Entity(
            id="sample",
            type="sample",
            label=sample_cfg.label,
            attrs={"fragile": sample_cfg.fragile, "weight": sample_cfg.weight},
            tags=set(sample_cfg.tags),
        )
    )

    world.facts.update(
        mission=mission,
        obstacle=obstacle,
        sample_cfg=sample_cfg,
        method=method,
        captain=captain,
        partner=partner,
        ship=ship,
        zone=zone,
        sample=sample,
        mission_id=mission.id,
        obstacle_id=obstacle.id,
        sample_id=sample_cfg.id,
        method_id=method.id,
    )

    intro(world, captain, partner, mission)
    discover(world, captain, partner, obstacle, sample_cfg)

    world.para()
    tempt(world, captain, obstacle)
    warn(world, captain, partner, obstacle, sample_cfg)
    wobble(world, captain, obstacle)

    world.para()
    choose_method(world, captain, partner, method)
    teamwork_retrieve(world, captain, partner, sample_cfg, method)

    world.para()
    celebrate(world, captain, partner, mission, sample_cfg)

    world.facts.update(
        retrieved=world.get("sample").meters["retrieved"] >= THRESHOLD,
        mission_success=world.get("ship").meters["mission_success"] >= THRESHOLD,
        off_balance=world.get("captain").meters["off_balance"] >= THRESHOLD,
    )
    return world


# ---------------------------------------------------------------------------
# Content
# ---------------------------------------------------------------------------
MISSIONS = {
    "moonbase": Mission(
        id="moonbase",
        scene="a silver moon base under the kitchen table",
        ship="a laundry basket was their shuttle, sofa pillows were moon hills, and a flashlight made one round porthole glow",
        goal="the rare-sample patrol",
        sendoff="blasted off toward the next moon cave",
        tags={"space", "moon"},
    ),
    "redplanet": Mission(
        id="redplanet",
        scene="a red planet camp across the living-room rug",
        ship="a big cardboard box was their rover, blankets became dusty hills, and bottle caps marked tiny landing lights",
        goal="the rare-sample patrol",
        sendoff="rolled their rover toward a far red ridge",
        tags={"space", "planet"},
    ),
    "ringstation": Mission(
        id="ringstation",
        scene="a bright ring station beside the bookshelf",
        ship="two chairs and a sheet became a starship dock, and a colander helmet made every whisper sound spacey",
        goal="the rare-sample patrol",
        sendoff="glided toward another shining station window",
        tags={"space", "station"},
    ),
}

OBSTACLES = {
    "high_ledge": Obstacle(
        id="high_ledge",
        label="high ledge",
        site="the high ledge above a stack of cushions",
        need="height",
        risk="the cushions could slide",
        risk_text="If you reach up alone, the cushions could slide and you could tumble back",
        tags={"ledge"},
    ),
    "dark_tunnel": Obstacle(
        id="dark_tunnel",
        label="dark tunnel",
        site="the dark tunnel behind the curtains",
        need="anchor",
        risk="the tunnel could swallow the light",
        risk_text="If you crawl in alone, the tunnel could swallow the light and you might lose your way",
        tags={"tunnel"},
    ),
    "wide_gap": Obstacle(
        id="wide_gap",
        label="wide gap",
        site="the wide gap between two couch islands",
        need="bridge",
        risk="the step was too long",
        risk_text="If you jump alone, the step is too long and the sample could fall between the cushions",
        tags={"gap"},
    ),
}

SAMPLES = {
    "moon_crystal": RareSample(
        id="moon_crystal",
        label="moon crystal",
        phrase="a rare moon crystal",
        shine="glowed with a quiet blue light",
        weight=1,
        fragile=True,
        tags={"crystal", "rare"},
    ),
    "star_egg": RareSample(
        id="star_egg",
        label="star egg",
        phrase="a rare star egg",
        shine="gleamed with pale silver swirls",
        weight=1,
        fragile=True,
        tags={"egg", "rare"},
    ),
    "meteor_box": RareSample(
        id="meteor_box",
        label="meteor box",
        phrase="a rare meteor box",
        shine="had copper corners and a deep rusty shine",
        weight=2,
        fragile=False,
        tags={"meteor", "rare"},
    ),
    "signal_battery": RareSample(
        id="signal_battery",
        label="signal battery",
        phrase="a rare signal battery",
        shine="blinked one sleepy green light",
        weight=2,
        fragile=False,
        tags={"battery", "rare"},
    ),
}

METHODS = {
    "shoulder_boost": Method(
        id="shoulder_boost",
        label="a shoulder boost",
        supports={"height"},
        power=1,
        gentle=True,
        setup="you brace the cushions and I'll climb from your shoulder",
        action="{partner} planted both feet and held steady while {captain} climbed carefully, reached the sample, and lowered it into waiting hands",
        qa_text="They used a shoulder boost so one child could reach while the other kept everything steady",
        tags={"teamwork", "boost"},
    ),
    "safety_tether": Method(
        id="safety_tether",
        label="a safety tether",
        supports={"anchor"},
        power=1,
        gentle=True,
        setup="you hold the tether and I will crawl only as far as the light reaches",
        action="{partner} anchored the line outside the tunnel while {captain} crawled in slowly, found the sample, and slid it back along the tether",
        qa_text="They used a safety tether so one child stayed anchored while the other reached in safely",
        tags={"teamwork", "tether"},
    ),
    "board_bridge": Method(
        id="board_bridge",
        label="a board bridge",
        supports={"bridge"},
        power=2,
        gentle=True,
        setup="you hold the bridge board and I'll cross on my knees",
        action="{partner} pressed the board bridge tight across the gap while {captain} crossed on hands and knees and guided the sample back across",
        qa_text="They made a bridge together so the path stayed steady while the sample came back safely",
        tags={"teamwork", "bridge"},
    ),
    "magnet_hook": Method(
        id="magnet_hook",
        label="a magnet hook",
        supports={"height", "bridge"},
        power=1,
        gentle=False,
        setup="we can swing the magnet hook toward it",
        action="{captain} and {partner} swung the hook together toward the sample",
        qa_text="They tried to use a magnet hook together",
        tags={"tool"},
    ),
}

GIRL_NAMES = ["Nia", "Mira", "Zoe", "Ava", "Lena", "Tara", "Maya", "Ivy"]
BOY_NAMES = ["Owen", "Leo", "Max", "Finn", "Noah", "Eli", "Theo", "Ben"]
PARTNER_GENDERS = ["boy", "girl"]


# ---------------------------------------------------------------------------
# Per-world params
# ---------------------------------------------------------------------------
@dataclass
class StoryParams:
    mission: str
    obstacle: str
    sample: str
    method: str
    captain_name: str
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
    "space": [
        (
            "What is teamwork?",
            "Teamwork means people help each other do one job together. Sometimes two careful helpers can do something that one person alone should not try."
        )
    ],
    "moon": [
        (
            "What is a crystal?",
            "A crystal is a hard piece of mineral that can shine or sparkle. Some crystals are delicate, so people handle them gently."
        )
    ],
    "planet": [
        (
            "What is a rover?",
            "A rover is a vehicle made to travel over the ground and explore. Space rovers help scientists reach places that are hard to walk to."
        )
    ],
    "station": [
        (
            "What is a space station?",
            "A space station is a place built for people to live or work in space. It has rooms and tools, like a tiny home that floats."
        )
    ],
    "tunnel": [
        (
            "Why is a tether useful?",
            "A tether is a line that keeps something connected and easy to find. It helps people move carefully without drifting or getting lost."
        )
    ],
    "ledge": [
        (
            "Why is a high ledge hard to reach safely?",
            "A high ledge is above your normal reach, so you can wobble if you stretch too far. It is safer to use help than to grab for it alone."
        )
    ],
    "gap": [
        (
            "Why can a bridge help over a gap?",
            "A bridge makes a steady path over an empty space. It lets you cross without taking a risky jump."
        )
    ],
    "crystal": [
        (
            "What does rare mean?",
            "Rare means something is not found very often. A rare thing is special because there are only a few of it."
        )
    ],
    "egg": [
        (
            "Why should a fragile object be handled gently?",
            "A fragile object can crack or break if it is bumped. Gentle hands help keep it safe."
        )
    ],
    "meteor": [
        (
            "What is a meteor?",
            "A meteor is a space rock. People sometimes use the word for a rock from space even when it is small."
        )
    ],
    "battery": [
        (
            "What does a battery do?",
            "A battery stores energy. It can give power to a light or a machine when it is connected the right way."
        )
    ],
    "teamwork": [
        (
            "Why can two children sometimes solve a problem better than one?",
            "Two children can share jobs, like holding, steadying, and carrying. That makes some tasks safer and easier than doing everything alone."
        )
    ],
}
KNOWLEDGE_ORDER = [
    "space",
    "moon",
    "planet",
    "station",
    "ledge",
    "tunnel",
    "gap",
    "crystal",
    "egg",
    "meteor",
    "battery",
    "teamwork",
]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    captain = f["captain"]
    partner = f["partner"]
    mission = f["mission"]
    sample = f["sample_cfg"]
    obstacle = f["obstacle"]
    return [
        f'Write a short Space Adventure story for a 3-to-5-year-old about a girl who finds {sample.phrase}. Include the word "rare".',
        f"Tell a gentle story where {captain.label} and {partner.label} are pretend space explorers, but the prize is stuck past {obstacle.site} and they must use teamwork.",
        f'Write a child-facing story with a clear beginning, a worried middle, and a happy ending where teamwork helps recover a rare object on a pretend mission.',
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    captain = f["captain"]
    partner = f["partner"]
    mission = f["mission"]
    obstacle = f["obstacle"]
    sample = f["sample_cfg"]
    method = f["method"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about a girl named {captain.label} and {partner.label}, her mission partner. They were pretending to be space explorers together."
        ),
        (
            "What rare thing did they find?",
            f"They found {sample.phrase}. It was the special treasure of their mission, so they wanted to bring it safely back to the ship."
        ),
        (
            f"Why did {partner.label} tell {captain.label} not to grab it alone?",
            f"{partner.label} knew {obstacle.risk_text.lower()}. In the world model, a solo rush made {captain.label} go off balance, so the warning came from a real risk instead of a random rule."
        ),
    ]
    if f.get("off_balance"):
        qa.append(
            (
                f"What changed {captain.label}'s mind?",
                f"When {captain.label} leaned in, she felt a wobble and stopped. That tiny scare proved {partner.label} was right, so she chose a teamwork plan instead."
            )
        )
    if f.get("retrieved"):
        qa.append(
            (
                "How did they get the sample back?",
                f"They worked together and used {method.label}. {method.qa_text}, which is why the rare {sample.label} came back safely."
            )
        )
    if f.get("mission_success"):
        qa.append(
            (
                "How did the story end?",
                f"They carried the rare sample back to the ship together and felt proud. The last image shows it shining in their pretend control room, which proves teamwork changed the mission."
            )
        )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags: set[str] = set(f["mission"].tags) | set(f["obstacle"].tags) | set(f["sample_cfg"].tags) | set(f["method"].tags)
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
        if e.label:
            bits.append(f"label={e.label!r}")
        if e.attrs:
            shown = {k: v for k, v in e.attrs.items() if v or v is False}
            bits.append(f"attrs={shown}")
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        lines.append(f"  {e.id:8} ({e.type:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
fits(O, S, M) :- obstacle(O), sample(S), method(M),
                 needs(O, N), supports(M, N),
                 weight(S, W), power(M, P), P >= W,
                 not bad_fragile(S, M).

bad_fragile(S, M) :- fragile(S), rough(M).
valid(Mis, O, S, M) :- mission(Mis), fits(O, S, M).

#show valid/4.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for mission_id in MISSIONS:
        lines.append(asp.fact("mission", mission_id))
    for obstacle_id, obstacle in OBSTACLES.items():
        lines.append(asp.fact("obstacle", obstacle_id))
        lines.append(asp.fact("needs", obstacle_id, obstacle.need))
    for sample_id, sample in SAMPLES.items():
        lines.append(asp.fact("sample", sample_id))
        lines.append(asp.fact("weight", sample_id, sample.weight))
        if sample.fragile:
            lines.append(asp.fact("fragile", sample_id))
    for method_id, method in METHODS.items():
        lines.append(asp.fact("method", method_id))
        lines.append(asp.fact("power", method_id, method.power))
        if not method.gentle:
            lines.append(asp.fact("rough", method_id))
        for need in sorted(method.supports):
            lines.append(asp.fact("supports", method_id, need))
    return "\n".join(lines)


def asp_program() -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program())
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    rc = 0
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: ASP gate matches valid_combos() ({len(py)} combos).")
    else:
        rc = 1
        print("MISMATCH between ASP and Python valid combos.")
        if cl - py:
            print("  only in ASP:", sorted(cl - py))
        if py - cl:
            print("  only in Python:", sorted(py - cl))

    try:
        sample = generate(CURATED[0])
        if not sample.story.strip():
            raise StoryError("Generated empty story during verify.")
        print("OK: smoke-test generation succeeded.")
    except Exception as exc:  # pragma: no cover - explicit verify failure path
        rc = 1
        print(f"VERIFY generation failure: {exc}")

    rng = random.Random(123)
    try:
        params = resolve_params(build_parser().parse_args([]), rng)
        sample = generate(params)
        if not sample.story.strip():
            raise StoryError("Random resolved story was empty during verify.")
        print("OK: random resolve/generate smoke test succeeded.")
    except Exception as exc:  # pragma: no cover
        rc = 1
        print(f"VERIFY random generation failure: {exc}")

    return rc


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Space-adventure teamwork storyworld. Unspecified choices are picked at random (seeded)."
    )
    ap.add_argument("--mission", choices=MISSIONS)
    ap.add_argument("--obstacle", choices=OBSTACLES)
    ap.add_argument("--sample", choices=SAMPLES)
    ap.add_argument("--method", choices=METHODS)
    ap.add_argument("--partner-gender", choices=PARTNER_GENDERS)
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list valid combinations from clingo")
    ap.add_argument("--verify", action="store_true", help="check ASP/Python parity and smoke-test generation")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.obstacle and args.sample and args.method:
        obstacle = OBSTACLES[args.obstacle]
        sample = SAMPLES[args.sample]
        method = METHODS[args.method]
        if not method_fits(obstacle, sample, method):
            raise StoryError(explain_rejection(obstacle, sample, method))

    combos = [
        combo
        for combo in valid_combos()
        if (args.mission is None or combo[0] == args.mission)
        and (args.obstacle is None or combo[1] == args.obstacle)
        and (args.sample is None or combo[2] == args.sample)
        and (args.method is None or combo[3] == args.method)
    ]
    if not combos:
        if args.obstacle and args.sample and args.method:
            raise StoryError(explain_rejection(OBSTACLES[args.obstacle], SAMPLES[args.sample], METHODS[args.method]))
        raise StoryError("(No valid combination matches the given options.)")

    mission_id, obstacle_id, sample_id, method_id = rng.choice(sorted(combos))
    captain_name = rng.choice(GIRL_NAMES)
    partner_gender = args.partner_gender or rng.choice(PARTNER_GENDERS)
    if partner_gender == "girl":
        partner_pool = [n for n in GIRL_NAMES if n != captain_name]
    else:
        partner_pool = BOY_NAMES[:]
    partner_name = rng.choice(partner_pool)

    return StoryParams(
        mission=mission_id,
        obstacle=obstacle_id,
        sample=sample_id,
        method=method_id,
        captain_name=captain_name,
        partner_name=partner_name,
        partner_gender=partner_gender,
    )


def generate(params: StoryParams) -> StorySample:
    if params.mission not in MISSIONS:
        raise StoryError(f"(Unknown mission: {params.mission})")
    if params.obstacle not in OBSTACLES:
        raise StoryError(f"(Unknown obstacle: {params.obstacle})")
    if params.sample not in SAMPLES:
        raise StoryError(f"(Unknown sample: {params.sample})")
    if params.method not in METHODS:
        raise StoryError(f"(Unknown method: {params.method})")

    mission = MISSIONS[params.mission]
    obstacle = OBSTACLES[params.obstacle]
    sample = SAMPLES[params.sample]
    method = METHODS[params.method]
    if not method_fits(obstacle, sample, method):
        raise StoryError(explain_rejection(obstacle, sample, method))

    world = tell(
        mission=mission,
        obstacle=obstacle,
        sample_cfg=sample,
        method=method,
        captain_name=params.captain_name,
        partner_name=params.partner_name,
        partner_type=params.partner_gender,
    )

    # Replace id-based names with labels in the rendered prose.
    story = (
        world.render()
        .replace("captain", params.captain_name)
        .replace("partner", params.partner_name)
    )

    return StorySample(
        params=params,
        story=story,
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


CURATED = [
    StoryParams(
        mission="moonbase",
        obstacle="high_ledge",
        sample="moon_crystal",
        method="shoulder_boost",
        captain_name="Nia",
        partner_name="Owen",
        partner_gender="boy",
    ),
    StoryParams(
        mission="redplanet",
        obstacle="wide_gap",
        sample="meteor_box",
        method="board_bridge",
        captain_name="Mira",
        partner_name="Leo",
        partner_gender="boy",
    ),
    StoryParams(
        mission="ringstation",
        obstacle="dark_tunnel",
        sample="star_egg",
        method="safety_tether",
        captain_name="Ava",
        partner_name="Zoe",
        partner_gender="girl",
    ),
    StoryParams(
        mission="moonbase",
        obstacle="wide_gap",
        sample="signal_battery",
        method="board_bridge",
        captain_name="Lena",
        partner_name="Finn",
        partner_gender="boy",
    ),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program())
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} valid (mission, obstacle, sample, method) combos:\n")
        for mission_id, obstacle_id, sample_id, method_id in combos:
            print(f"  {mission_id:10} {obstacle_id:12} {sample_id:14} {method_id}")
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
            header = f"### {p.captain_name}: {p.sample} past {p.obstacle} ({p.method})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()

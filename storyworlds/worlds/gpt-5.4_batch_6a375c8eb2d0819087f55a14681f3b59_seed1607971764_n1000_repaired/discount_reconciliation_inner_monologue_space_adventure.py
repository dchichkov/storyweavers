#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/discount_reconciliation_inner_monologue_space_adventure.py
=====================================================================================

A standalone story world about two young space adventurers at an orbital market.
They are getting ready for a small mission, but one child uses a discount on a
shiny treat instead of the gear the mission needs. The pair argue, the tempted
child thinks quietly about what will happen next, and then chooses honesty,
exchange, and reconciliation.

The world model keeps track of:
- physical meters like credits, danger, progress, and supplies
- emotional memes like envy, worry, guilt, trust, and relief

The story always turns on a state-driven mistake and repair:
a discount makes the wrong purchase tempting, the mission hazard exposes the
problem, an inner monologue changes the child's choice, and reconciliation lets
the adventure continue safely.

Run it
------
    python storyworlds/worlds/gpt-5.4/discount_reconciliation_inner_monologue_space_adventure.py
    python storyworlds/worlds/gpt-5.4/discount_reconciliation_inner_monologue_space_adventure.py --mission cave --gear glow_rope
    python storyworlds/worlds/gpt-5.4/discount_reconciliation_inner_monologue_space_adventure.py --gear heat_cape
    python storyworlds/worlds/gpt-5.4/discount_reconciliation_inner_monologue_space_adventure.py -n 5 --seed 7 --qa
    python storyworlds/worlds/gpt-5.4/discount_reconciliation_inner_monologue_space_adventure.py --all
    python storyworlds/worlds/gpt-5.4/discount_reconciliation_inner_monologue_space_adventure.py --verify
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
BASE_BUDGET = 4
DISCOUNT_VALUE = 1


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    traits: list[str] = field(default_factory=list)
    role: str = ""
    attrs: dict = field(default_factory=dict)
    protective_against: set[str] = field(default_factory=set)
    portable: bool = False
    # physical meters
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    # emotional / social meters
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "woman"}
        male = {"boy", "father", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]
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
class Mission:
    id: str
    place: str
    goal: str
    hazard: str
    launch_line: str
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


@dataclass
class Hazard:
    id: str
    label: str
    problem: str
    fear_line: str
    safe_line: str
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
class Gear:
    id: str
    label: str
    phrase: str
    protects: set[str] = field(default_factory=set)
    success_use: str = ""
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
class FunItem:
    id: str
    label: str
    phrase: str
    sparkle: str
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
class Discount:
    id: str
    label: str
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


def _r_unprotected_hazard(world: World) -> list[str]:
    out: list[str] = []
    if not world.facts.get("entered_hazard"):
        return out
    crew = world.get("crew")
    gear = world.get("gear_item")
    hazard_id = world.facts["hazard_id"]
    if hazard_id in gear.protective_against:
        return out
    sig = ("unprotected", hazard_id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    crew.meters["danger"] += 1
    for kid_id in ("lead", "partner"):
        world.get(kid_id).memes["fear"] += 1
    out.append("__hazard__")
    return out


def _r_protected_progress(world: World) -> list[str]:
    out: list[str] = []
    if not world.facts.get("entered_hazard"):
        return out
    crew = world.get("crew")
    gear = world.get("gear_item")
    hazard_id = world.facts["hazard_id"]
    if hazard_id not in gear.protective_against:
        return out
    sig = ("safe_progress", hazard_id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    crew.meters["progress"] += 1
    for kid_id in ("lead", "partner"):
        world.get(kid_id).memes["joy"] += 1
        world.get(kid_id).memes["relief"] += 1
    out.append("__progress__")
    return out


def _r_reconciliation(world: World) -> list[str]:
    lead = world.get("lead")
    partner = world.get("partner")
    if lead.memes["apology"] < THRESHOLD or partner.memes["forgiveness"] < THRESHOLD:
        return []
    sig = ("reconciliation",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    lead.memes["trust"] += 1
    partner.memes["trust"] += 1
    lead.memes["guilt"] = 0.0
    partner.memes["hurt"] = 0.0
    return ["__reconciled__"]


CAUSAL_RULES = [
    Rule(name="unprotected_hazard", tag="physical", apply=_r_unprotected_hazard),
    Rule(name="protected_progress", tag="physical", apply=_r_protected_progress),
    Rule(name="reconciliation", tag="social", apply=_r_reconciliation),
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


def gear_matches(mission: Mission, gear: Gear) -> bool:
    return mission.hazard in gear.protects


def valid_combos() -> list[tuple[str, str]]:
    combos: list[tuple[str, str]] = []
    for mid, mission in MISSIONS.items():
        for gid, gear in GEARS.items():
            if gear_matches(mission, gear):
                combos.append((mid, gid))
    return combos


def explain_rejection(mission: Mission, gear: Gear) -> str:
    hazard = HAZARDS[mission.hazard]
    return (
        f"(No story: {mission.place} has {hazard.label}, but {gear.phrase} does not solve "
        f"that problem. Pick gear that protects against {hazard.label}.)"
    )


def predict_setback(world: World) -> dict:
    sim = world.copy()
    sim.facts["entered_hazard"] = True
    propagate(sim, narrate=False)
    crew = sim.get("crew")
    return {
        "danger": crew.meters["danger"],
        "progress": crew.meters["progress"],
    }


def market_setup(world: World, lead: Entity, partner: Entity, robot: Entity,
                 mission: Mission, discount: Discount) -> None:
    lead.memes["joy"] += 1
    partner.memes["joy"] += 1
    world.say(
        f"Far above the blue world, {lead.id} and {partner.id} hurried through the Ring Market, "
        f"a bright circle of little space shops under a glass dome. Today they were not just children. "
        f"They were star cadets on the way to {mission.place}."
    )
    world.say(
        f'Their mission was simple and important: {mission.goal}. '
        f'{robot.id}, the round helper robot at the supply stall, beeped and held up {discount.line}.'
    )


def show_fun_item(world: World, lead: Entity, fun_item: FunItem) -> None:
    lead.memes["temptation"] += 1
    world.say(
        f"On the next shelf, {lead.id} spotted {fun_item.phrase}. "
        f"It {fun_item.sparkle}, and for a second the whole market seemed to twinkle around it."
    )


def buy_wrong_thing(world: World, lead: Entity, fun_item: FunItem, discount: Discount) -> None:
    wallet = world.get("wallet")
    toy = world.get("toy_item")
    toy.attrs["owned_by"] = lead.id
    wallet.meters["credits"] -= 1
    wallet.meters["discount_used"] += 1
    lead.memes["pride"] += 1
    world.say(
        f'"Look! It has a discount," {lead.id} said. Before {partner_name(world)} could answer, '
        f'{lead.pronoun().capitalize()} slid the little chip across the counter and bought the {fun_item.label} for one star credit.'
    )


def partner_name(world: World) -> str:
    return world.get("partner").id


def notice_shortage(world: World, partner: Entity, mission: Mission, gear: Gear) -> None:
    wallet = world.get("wallet")
    partner.memes["worry"] += 1
    partner.memes["hurt"] += 1
    world.say(
        f'{partner.id} looked from the shiny shelf prize to {gear.phrase}. '
        f'"But the mission needs {gear.label}," {partner.pronoun()} said. '
        f'"We only have {int(wallet.meters["credits"])} credits left, and that is not enough."'
    )


def argue(world: World, lead: Entity, partner: Entity, fun_item: FunItem) -> None:
    lead.memes["defensiveness"] += 1
    partner.memes["conflict"] += 1
    lead.memes["conflict"] += 1
    world.say(
        f'"It was such a good bargain," {lead.id} said, clutching the {fun_item.label}. '
        f'"I thought we could still figure something out."'
    )
    world.say(
        f'{partner.id} folded {partner.pronoun("possessive")} arms. '
        f'"A mission is not a guessing game," {partner.pronoun()} answered. '
        f'The happy market suddenly felt smaller.'
    )


def hazard_attempt(world: World, mission: Mission, hazard: Hazard) -> None:
    world.say(mission.launch_line)
    world.facts["entered_hazard"] = True
    propagate(world, narrate=False)
    if world.get("crew").meters["danger"] >= THRESHOLD:
        world.say(
            f"But when they reached the first stretch of the path, {hazard.problem}. "
            f"{hazard.fear_line}"
        )


def inner_monologue(world: World, lead: Entity, partner: Entity, mission: Mission,
                    hazard: Hazard, fun_item: FunItem) -> None:
    lead.memes["guilt"] += 1
    pred = predict_setback(world)
    world.facts["predicted_danger"] = pred["danger"]
    world.say(
        f'{lead.id} looked at {partner.id}, then down at the {fun_item.label} in {lead.pronoun("possessive")} hands.'
    )
    world.say(
        f'Inside, {lead.pronoun()} thought, "The {fun_item.label} is pretty, but it cannot help us in {mission.place}. '
        f'If I keep it, {partner.id} will stay worried and our mission will stop right here."'
    )
    world.say(
        f'Another small thought followed, quieter and braver: "I liked the discount, but I used it the wrong way. '
        f'I can fix this before the mistake grows."'
    )


def exchange_and_apologize(world: World, lead: Entity, partner: Entity, robot: Entity,
                           gear: Gear, fun_item: FunItem) -> None:
    wallet = world.get("wallet")
    toy = world.get("toy_item")
    gear_item = world.get("gear_item")
    wallet.meters["credits"] += 1
    toy.attrs["owned_by"] = ""
    wallet.meters["discount_used"] = 0
    wallet.meters["credits"] -= 3
    wallet.meters["discount_used"] = 1
    gear_item.attrs["owned_by"] = "crew"
    lead.memes["apology"] += 1
    partner.memes["forgiveness"] += 1
    world.say(
        f'{lead.id} took a deep breath, turned around, and hurried back to {robot.id}. '
        f'"May I trade this back and use the discount on {gear.phrase} instead?" {lead.pronoun()} asked.'
    )
    world.say(
        f'{robot.id} gave a cheerful ping and opened the swap tray. A moment later, the shiny toy was back on its hook, '
        f'and {gear.phrase} was in their hands.'
    )
    world.say(
        f'"I am sorry," {lead.id} said to {partner.id}. '
        f'"I wanted the bargain more than I listened to you. You were trying to protect the mission."'
    )
    propagate(world, narrate=False)
    world.say(
        f'{partner.id} let out a slow breath. "Thank you for fixing it," {partner.pronoun()} said. '
        f'"Let\'s finish this together."'
    )


def use_gear_and_succeed(world: World, mission: Mission, hazard: Hazard, gear: Gear) -> None:
    gear_item = world.get("gear_item")
    gear_item.protective_against = set(gear.protects)
    world.fired.discard(("unprotected", hazard.id))
    world.facts["entered_hazard"] = True
    world.say(
        f'This time they stepped forward with {gear.phrase}. {gear.success_use} {hazard.safe_line}'
    )
    propagate(world, narrate=False)
    if world.get("crew").meters["progress"] >= THRESHOLD:
        world.say(mission.ending_image)


def tell(mission: Mission, gear: Gear, fun_item: FunItem, discount: Discount,
         lead_name: str = "Nova", lead_gender: str = "girl",
         partner_name_value: str = "Orion", partner_gender: str = "boy",
         relation: str = "friends") -> World:
    world = World()

    lead = world.add(Entity(
        id=lead_name,
        kind="character",
        type=lead_gender,
        label=lead_name,
        role="lead",
        attrs={"relation": relation},
    ))
    partner = world.add(Entity(
        id=partner_name_value,
        kind="character",
        type=partner_gender,
        label=partner_name_value,
        role="partner",
        attrs={"relation": relation},
    ))
    robot = world.add(Entity(
        id="Tiko",
        kind="character",
        type="robot",
        label="the stall robot",
        role="vendor",
    ))
    wallet = world.add(Entity(
        id="wallet",
        type="wallet",
        label="mission purse",
        meters=defaultdict(float, {"credits": float(BASE_BUDGET), "discount_used": 0.0}),
    ))
    crew = world.add(Entity(
        id="crew",
        type="crew",
        label="crew",
        meters=defaultdict(float, {"danger": 0.0, "progress": 0.0}),
    ))
    gear_item = world.add(Entity(
        id="gear_item",
        type="gear",
        label=gear.label,
        attrs={"owned_by": ""},
        protective_against=set(),
        portable=True,
    ))
    toy_item = world.add(Entity(
        id="toy_item",
        type="toy",
        label=fun_item.label,
        attrs={"owned_by": ""},
        portable=True,
    ))

    world.facts.update(
        mission=mission,
        hazard=HAZARDS[mission.hazard],
        gear_cfg=gear,
        fun_cfg=fun_item,
        discount_cfg=discount,
        entered_hazard=False,
        hazard_id=mission.hazard,
        relation=relation,
    )

    market_setup(world, lead, partner, robot, mission, discount)
    show_fun_item(world, lead, fun_item)

    world.para()
    buy_wrong_thing(world, lead, fun_item, discount)
    notice_shortage(world, partner, mission, gear)
    argue(world, lead, partner, fun_item)

    world.para()
    hazard_attempt(world, mission, HAZARDS[mission.hazard])
    inner_monologue(world, lead, partner, mission, HAZARDS[mission.hazard], fun_item)

    world.para()
    exchange_and_apologize(world, lead, partner, robot, gear, fun_item)
    use_gear_and_succeed(world, mission, HAZARDS[mission.hazard], gear)

    world.facts.update(
        lead=lead,
        partner=partner,
        robot=robot,
        wallet=wallet,
        gear_item=gear_item,
        toy_item=toy_item,
        reconciled=lead.memes["trust"] >= THRESHOLD and partner.memes["trust"] >= THRESHOLD,
        progress=crew.meters["progress"],
        danger=crew.meters["danger"],
    )
    return world


MISSIONS = {
    "cave": Mission(
        id="cave",
        place="the Crystal Moon Caves",
        goal="carry a humming map seed to the hidden echo chamber",
        hazard="darkness",
        launch_line="Soon the children boarded their tiny rover and rolled out beneath the stars toward the Crystal Moon Caves.",
        ending_image="At the echo chamber, the map seed opened like a silver flower, and the cave walls answered with soft blue light. Side by side, the two cadets laughed and steered their rover home.",
        tags={"cave", "mission"},
    ),
    "ridge": Mission(
        id="ridge",
        place="the Frost Ring Ridge",
        goal="deliver a message kite to the weather beacon on the ice hill",
        hazard="cold",
        launch_line="Soon they clipped into their little sled and skimmed out toward Frost Ring Ridge, where the ice hills shone under the stars.",
        ending_image="At the weather beacon, the message kite fluttered free and spun a green ribbon across the sky. Wrapped close and smiling again, the two cadets glided home over sparkling ice.",
        tags={"ridge", "mission"},
    ),
    "field": Mission(
        id="field",
        place="the Pebble Comet Field",
        goal="collect a singing stone for the station museum",
        hazard="dust",
        launch_line="Soon they lifted off in their hop-pod and bounced toward the Pebble Comet Field, where little rocks chimed against one another.",
        ending_image="When they found the singing stone, it rang like a tiny bell inside the pod. The children held it together between them, and the ride home felt light and easy again.",
        tags={"field", "mission"},
    ),
}

HAZARDS = {
    "darkness": Hazard(
        id="darkness",
        label="deep darkness",
        problem="the tunnel swallowed the path ahead",
        fear_line="Without proper gear, the adventure no longer felt brave. It felt risky and lonely.",
        safe_line="A warm beam leaped ahead and painted safe silver steps over the cave floor.",
        tags={"dark", "safety"},
    ),
    "cold": Hazard(
        id="cold",
        label="needle-cold wind",
        problem="sharp cold wind whistled across the ridge and bit at their sleeves",
        fear_line="The cold made their fingers stiff, and even brave voices sounded small.",
        safe_line="The cloth held in their warmth, and the wind could not nibble through.",
        tags={"cold", "safety"},
    ),
    "dust": Hazard(
        id="dust",
        label="swirling comet dust",
        problem="a ribbon of gray dust spun over the trail and stung their eyes",
        fear_line="They could not see clearly enough to hop forward safely.",
        safe_line="The clear shield turned the dusty gust aside so they could watch each careful step.",
        tags={"dust", "safety"},
    ),
}

GEARS = {
    "glow_rope": Gear(
        id="glow_rope",
        label="the glow rope",
        phrase="the glow rope",
        protects={"darkness"},
        success_use="Nova and Orion clipped the rope to the rover rail, and",
        tags={"light", "gear"},
    ),
    "heat_cape": Gear(
        id="heat_cape",
        label="the heat cape",
        phrase="the heat cape",
        protects={"cold"},
        success_use="They wrapped the cape around their shoulders together, and",
        tags={"warmth", "gear"},
    ),
    "visor": Gear(
        id="visor",
        label="the clear dust visor",
        phrase="the clear dust visor",
        protects={"dust"},
        success_use="They lowered the visor with a click, and",
        tags={"visor", "gear"},
    ),
}

FUN_ITEMS = {
    "pin": FunItem(
        id="pin",
        label="comet pin",
        phrase="a comet pin",
        sparkle="winked with green glitter",
        tags={"toy", "market"},
    ),
    "candy": FunItem(
        id="candy",
        label="moon candy swirl",
        phrase="a moon candy swirl",
        sparkle="glowed like a little purple planet",
        tags={"candy", "market"},
    ),
    "sticker": FunItem(
        id="sticker",
        label="star sticker sheet",
        phrase="a star sticker sheet",
        sparkle="shimmered with tiny gold rockets",
        tags={"sticker", "market"},
    ),
}

DISCOUNTS = {
    "chip": Discount(
        id="chip",
        label="discount chip",
        line='a round copper discount chip. "One item is one credit cheaper today," it beeped.',
        tags={"discount", "market"},
    ),
}

GIRL_NAMES = ["Nova", "Lyra", "Mira", "Skye", "Lumi", "Astra"]
BOY_NAMES = ["Orion", "Leo", "Kai", "Jett", "Milo", "Sol"]


@dataclass
class StoryParams:
    mission: str
    gear: str
    fun_item: str
    discount: str
    lead_name: str
    lead_gender: str
    partner_name: str
    partner_gender: str
    relation: str = "friends"
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
    "discount": [
        (
            "What is a discount?",
            "A discount means something costs less than usual. It can help you save money, but you still have to think carefully about what you need most.",
        )
    ],
    "light": [
        (
            "Why do explorers need light in a dark cave?",
            "Light helps explorers see where the path goes and where it is safe to step. In darkness, it is easy to get lost or bump into things.",
        )
    ],
    "warmth": [
        (
            "Why is warm gear important in very cold places?",
            "Warm gear helps your body keep its heat. If you get too cold, your hands and body do not work as well.",
        )
    ],
    "visor": [
        (
            "What does a visor do?",
            "A visor is a clear shield you wear in front of your eyes or face. It helps block dust, wind, or bright light so you can see safely.",
        )
    ],
    "apology": [
        (
            "What does it mean to apologize?",
            "To apologize means you tell someone you were wrong and that you are sorry. A real apology also tries to fix the problem.",
        )
    ],
    "reconcile": [
        (
            "What does reconciliation mean?",
            "Reconciliation means people make peace after a hurt or argument. They listen, repair the problem, and choose to trust each other again.",
        )
    ],
    "mission": [
        (
            "Why do teammates need to listen to each other on a mission?",
            "Teammates notice different problems and help keep one another safe. Listening makes the whole team stronger.",
        )
    ],
}
KNOWLEDGE_ORDER = ["discount", "light", "warmth", "visor", "apology", "reconcile", "mission"]


def generation_prompts(world: World) -> list[str]:
    mission = world.facts["mission"]
    hazard = world.facts["hazard"]
    gear = world.facts["gear_cfg"]
    lead = world.facts["lead"]
    partner = world.facts["partner"]
    fun_item = world.facts["fun_cfg"]
    return [
        f'Write a short space adventure for a 3-to-5-year-old that includes the word "discount" and a moment of reconciliation.',
        f"Tell a gentle story where {lead.id} and {partner.id} are getting ready for a mission to {mission.place}, but a discount on {fun_item.phrase} causes an argument before they choose {gear.phrase}.",
        f"Write a child-facing space story with inner monologue, where one teammate realizes that {hazard.label} matters more than a bargain and fixes the mistake.",
    ]


def pair_noun(world: World) -> str:
    relation = world.facts.get("relation", "friends")
    lead = world.facts["lead"]
    partner = world.facts["partner"]
    if relation == "siblings":
        if lead.type == "girl" and partner.type == "girl":
            return "two sisters"
        if lead.type == "boy" and partner.type == "boy":
            return "two brothers"
        return "a brother and a sister"
    return "two friends"


def story_qa(world: World) -> list[tuple[str, str]]:
    lead = world.facts["lead"]
    partner = world.facts["partner"]
    mission = world.facts["mission"]
    hazard = world.facts["hazard"]
    gear = world.facts["gear_cfg"]
    fun_item = world.facts["fun_cfg"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {pair_noun(world)}, {lead.id} and {partner.id}, who were getting ready for a mission to {mission.place}. They began as excited teammates, then had to repair an argument before they could finish the adventure.",
        ),
        (
            "What problem started the argument?",
            f"{lead.id} used the discount on {fun_item.phrase} instead of on {gear.phrase}. That left the team without enough credits for the mission gear they truly needed.",
        ),
        (
            f"Why did {partner.id} get upset?",
            f"{partner.id} was upset because the mission still had to pass through {hazard.label}, and the wrong purchase left them unprepared. {partner.pronoun().capitalize()} was not being mean; {partner.pronoun()} was trying to protect the mission and both children.",
        ),
        (
            f"What did {lead.id} think about during the inner monologue?",
            f"{lead.id} realized the bargain was not helping them in {mission.place}. {lead.pronoun().capitalize()} understood that keeping the toy would leave {partner.id} worried and stop the mission before it really began.",
        ),
        (
            f"How did {lead.id} fix the mistake?",
            f"{lead.id} traded the {fun_item.label} back and used the discount on {gear.phrase} instead. Then {lead.pronoun()} apologized out loud, which repaired both the supply problem and the hurt feelings.",
        ),
        (
            "How did the story show reconciliation?",
            f"The reconciliation happened when {lead.id} admitted the mistake and {partner.id} accepted the apology. After that, they worked together again instead of pulling in different directions.",
        ),
        (
            "How did the adventure end?",
            f"They used {gear.phrase} to get safely past {hazard.label} and finish the mission. The ending image shows them side by side again, which proves that the team was repaired as well as prepared.",
        ),
    ]
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    gear = world.facts["gear_cfg"]
    tags = {"discount", "apology", "reconcile", "mission"} | set(gear.tags)
    out: list[tuple[str, str]] = []
    for tag in KNOWLEDGE_ORDER:
        if tag in tags:
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
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if ent.protective_against:
            bits.append(f"protective_against={sorted(ent.protective_against)}")
        if ent.attrs:
            shown = {k: v for k, v in ent.attrs.items() if v}
            if shown:
                bits.append(f"attrs={shown}")
        if ent.role:
            bits.append(f"role={ent.role}")
        lines.append(f"  {ent.id:10} ({ent.type:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        mission="cave",
        gear="glow_rope",
        fun_item="pin",
        discount="chip",
        lead_name="Nova",
        lead_gender="girl",
        partner_name="Orion",
        partner_gender="boy",
        relation="friends",
    ),
    StoryParams(
        mission="ridge",
        gear="heat_cape",
        fun_item="candy",
        discount="chip",
        lead_name="Lyra",
        lead_gender="girl",
        partner_name="Milo",
        partner_gender="boy",
        relation="siblings",
    ),
    StoryParams(
        mission="field",
        gear="visor",
        fun_item="sticker",
        discount="chip",
        lead_name="Kai",
        lead_gender="boy",
        partner_name="Astra",
        partner_gender="girl",
        relation="friends",
    ),
]


ASP_RULES = r"""
valid(M, G) :- mission(M), gear(G), mission_hazard(M, H), protects(G, H).

chosen_valid :- chosen_mission(M), chosen_gear(G), valid(M, G).
story_possible :- chosen_valid, one_discount.

#show valid/2.
#show story_possible/0.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for mid, mission in MISSIONS.items():
        lines.append(asp.fact("mission", mid))
        lines.append(asp.fact("mission_hazard", mid, mission.hazard))
    for gid, gear in GEARS.items():
        lines.append(asp.fact("gear", gid))
        for hazard in sorted(gear.protects):
            lines.append(asp.fact("protects", gid, hazard))
    for did in DISCOUNTS:
        lines.append(asp.fact("discount", did))
    lines.append(asp.fact("one_discount"))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("", "#show valid/2."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_story_possible(params: StoryParams) -> bool:
    import asp

    scenario = "\n".join([
        asp.fact("chosen_mission", params.mission),
        asp.fact("chosen_gear", params.gear),
    ])
    model = asp.one_model(asp_program(scenario, "#show story_possible/0."))
    return bool(asp.atoms(model, "story_possible"))


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

    for params in CURATED:
        if not asp_story_possible(params):
            rc = 1
            print(f"MISMATCH: ASP says story impossible for curated params {params}.")
            break
    else:
        print(f"OK: ASP accepts all {len(CURATED)} curated scenarios.")

    try:
        smoke = generate(CURATED[0])
        if not smoke.story or "discount" not in smoke.story.lower():
            raise StoryError("(Smoke test failed: generated story was empty or missing 'discount'.)")
        print("OK: smoke test generation succeeded.")
    except Exception as err:  # pragma: no cover - verify path
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Story world: a discount mistake, inner monologue, reconciliation, and a space adventure."
    )
    ap.add_argument("--mission", choices=MISSIONS)
    ap.add_argument("--gear", choices=GEARS)
    ap.add_argument("--fun-item", dest="fun_item", choices=FUN_ITEMS)
    ap.add_argument("--discount", choices=DISCOUNTS)
    ap.add_argument("--relation", choices=["friends", "siblings"])
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list the compatible mission/gear pairs from clingo")
    ap.add_argument("--verify", action="store_true", help="check ASP/Python parity and run a smoke test")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def pick_name(rng: random.Random, gender: str, avoid: str = "") -> str:
    pool = GIRL_NAMES if gender == "girl" else BOY_NAMES
    choices = [name for name in pool if name != avoid]
    return rng.choice(choices)


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.mission and args.gear:
        mission = MISSIONS[args.mission]
        gear = GEARS[args.gear]
        if not gear_matches(mission, gear):
            raise StoryError(explain_rejection(mission, gear))

    combos = [
        combo for combo in valid_combos()
        if (args.mission is None or combo[0] == args.mission)
        and (args.gear is None or combo[1] == args.gear)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    mission_id, gear_id = rng.choice(sorted(combos))
    lead_gender = rng.choice(["girl", "boy"])
    partner_gender = rng.choice(["girl", "boy"])
    lead_name = pick_name(rng, lead_gender)
    partner_name = pick_name(rng, partner_gender, avoid=lead_name)
    return StoryParams(
        mission=mission_id,
        gear=gear_id,
        fun_item=args.fun_item or rng.choice(sorted(FUN_ITEMS)),
        discount=args.discount or "chip",
        lead_name=lead_name,
        lead_gender=lead_gender,
        partner_name=partner_name,
        partner_gender=partner_gender,
        relation=args.relation or rng.choice(["friends", "siblings"]),
    )


def generate(params: StoryParams) -> StorySample:
    if params.mission not in MISSIONS:
        raise StoryError(f"(Unknown mission '{params.mission}'.)")
    if params.gear not in GEARS:
        raise StoryError(f"(Unknown gear '{params.gear}'.)")
    if params.fun_item not in FUN_ITEMS:
        raise StoryError(f"(Unknown fun item '{params.fun_item}'.)")
    if params.discount not in DISCOUNTS:
        raise StoryError(f"(Unknown discount '{params.discount}'.)")
    mission = MISSIONS[params.mission]
    gear = GEARS[params.gear]
    if not gear_matches(mission, gear):
        raise StoryError(explain_rejection(mission, gear))

    world = tell(
        mission=mission,
        gear=gear,
        fun_item=FUN_ITEMS[params.fun_item],
        discount=DISCOUNTS[params.discount],
        lead_name=params.lead_name,
        lead_gender=params.lead_gender,
        partner_name_value=params.partner_name,
        partner_gender=params.partner_gender,
        relation=params.relation,
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
        print(asp_program("", "#show valid/2.\n#show story_possible/0."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (mission, gear) combos:\n")
        for mission, gear in combos:
            print(f"  {mission:8} {gear}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(params) for params in CURATED]
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
            print(json.dumps([sample.to_dict() for sample in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.lead_name} & {p.partner_name}: {p.mission} with {p.gear}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/grill_pollen_surprise_lesson_learned_space_adventure.py
===================================================================================

A standalone story world for a tiny "space adventure" domain: two children turn a
yard into a launch site, a cloud of pollen triggers a surprising sneeze, and a
light mission token skitters too close to a warm grill. A calm grown-up helps
the children solve the problem safely, and the ending proves the lesson they
learned.

Run it
------
    python storyworlds/worlds/gpt-5.4/grill_pollen_surprise_lesson_learned_space_adventure.py
    python storyworlds/worlds/gpt-5.4/grill_pollen_surprise_lesson_learned_space_adventure.py --token scanner
    python storyworlds/worlds/gpt-5.4/grill_pollen_surprise_lesson_learned_space_adventure.py --response bare_hands
    python storyworlds/worlds/gpt-5.4/grill_pollen_surprise_lesson_learned_space_adventure.py --all
    python storyworlds/worlds/gpt-5.4/grill_pollen_surprise_lesson_learned_space_adventure.py -n 5 --seed 7 --qa
    python storyworlds/worlds/gpt-5.4/grill_pollen_surprise_lesson_learned_space_adventure.py --verify
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

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from results import QAItem, StoryError, StorySample  # noqa: E402

THRESHOLD = 1.0
SENSE_MIN = 2
BRAVERY_INIT = 6.0
CAUTIOUS_TRAITS = {"careful", "cautious", "thoughtful", "steady"}


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
    warm: bool = False
    portable: bool = False
    blowable: bool = False
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman"}
        male = {"boy", "father", "dad", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return {"mother": "mom", "father": "dad"}.get(self.type, self.type)
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
    scene: str
    ship: str
    goal: str
    call: str
    ending: str
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
class Pollen:
    id: str
    label: str
    source: str
    color: str
    strength: int
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
class Token:
    id: str
    label: str
    phrase: str
    drift_name: str
    weight: int
    blowable: bool = True
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
class Spot:
    id: str
    label: str
    phrase: str
    distance: int
    urgency: int
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


def _r_sneeze(world: World) -> list[str]:
    out: list[str] = []
    captain = world.get("captain")
    token = world.get("token")
    if captain.meters["pollen"] < THRESHOLD or token.meters["held"] < THRESHOLD:
        return out
    sig = ("sneeze", captain.id, token.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    captain.meters["sneeze"] += 1
    captain.memes["surprise"] += 1
    token.meters["held"] = 0.0
    token.meters["drifted"] += 1
    out.append("__sneeze__")
    return out


def _r_grill_danger(world: World) -> list[str]:
    out: list[str] = []
    token = world.get("token")
    grill = world.get("grill")
    if token.meters["near_grill"] < THRESHOLD or grill.meters["hot"] < THRESHOLD:
        return out
    sig = ("danger", token.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    world.get("yard").meters["danger"] += 1
    for kid in world.kids():
        kid.memes["fear"] += 1
    out.append("__danger__")
    return out


CAUSAL_RULES: list[Rule] = [
    Rule(name="sneeze", tag="physical", apply=_r_sneeze),
    Rule(name="grill_danger", tag="physical", apply=_r_grill_danger),
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


def sneeze_can_move(pollen: Pollen, token: Token, spot: Spot) -> bool:
    return token.blowable and pollen.strength >= token.weight and pollen.strength >= spot.distance


def sensible_responses() -> list[Response]:
    return [r for r in RESPONSES.values() if r.sense >= SENSE_MIN]


def risk_level(spot: Spot, delay: int) -> int:
    return spot.urgency + delay


def can_save(response: Response, spot: Spot, delay: int) -> bool:
    return response.power >= risk_level(spot, delay)


def initial_caution(trait: str) -> float:
    return 5.0 if trait in CAUTIOUS_TRAITS else 3.0


def would_avert(relation: str, captain_age: int, partner_age: int, trait: str) -> bool:
    partner_older = relation == "siblings" and partner_age > captain_age
    authority = (initial_caution(trait) + 1.0) + (4.0 if partner_older else 0.0)
    return partner_older and authority > BRAVERY_INIT


def predict_danger(world: World, pollen_id: str, spot_id: str) -> dict:
    sim = world.copy()
    captain = sim.get("captain")
    captain.meters["pollen"] = float(POLLEN[pollen_id].strength)
    sim.facts["spot"] = SPOTS[spot_id]
    _send_token_to_grill(sim, narrate=False)
    return {
        "sneeze": sim.get("captain").meters["sneeze"],
        "danger": sim.get("yard").meters["danger"],
    }


def _send_token_to_grill(world: World, narrate: bool = True) -> None:
    token = world.get("token")
    token.meters["near_grill"] += 1
    propagate(world, narrate=narrate)


def intro(world: World, captain: Entity, partner: Entity, mission: Mission) -> None:
    for kid in (captain, partner):
        kid.memes["joy"] += 1
    world.say(
        f"On a bright afternoon, {captain.id} and {partner.id} turned the backyard "
        f"into {mission.scene}. {mission.ship}"
    )
    world.say(
        f'"{mission.call}" {captain.id} cheered. "Today we are flying to {mission.goal}."'
    )


def stage_grill(world: World, mission: Mission) -> None:
    world.say(
        "By the patio stood the family grill, still a little warm from lunch. "
        f"To the children, its round lid looked like a silent moon crater beside {mission.scene}."
    )


def pollen_rises(world: World, captain: Entity, pollen: Pollen, token: Token) -> None:
    captain.meters["pollen"] = float(pollen.strength)
    token.meters["held"] = 1.0
    world.say(
        f"{captain.id} held {token.phrase} and marched across the yard. "
        f"But {pollen.color} pollen drifted from {pollen.source} like space dust, "
        f"and it tickled {captain.pronoun('possessive')} nose."
    )


def warn(world: World, partner: Entity, captain: Entity, parent: Entity,
         pollen: Pollen, spot: Spot) -> None:
    pred = predict_danger(world, pollen.id, spot.id)
    partner.memes["caution"] += 1
    world.facts["predicted_danger"] = pred["danger"]
    extra = ""
    if partner.memes["caution"] >= 6:
        extra = f" {partner.pronoun().capitalize()} stepped closer, already worried about the warm grill."
    world.say(
        f'{partner.id} saw the pollen swirling and said, "{captain.id}, hold on. '
        f'If you sneeze, the mission token could blow {spot.phrase}, and the grill is not a safe place to reach."'
        f"{extra}"
    )
    world.say(
        f'"If that happens, we call {parent.label_word}, not our hands," {partner.pronoun()} added.'
    )


def surprise_sneeze(world: World, captain: Entity, token_cfg: Token, spot: Spot) -> None:
    propagate(world, narrate=False)
    token = world.get("token")
    world.facts["spot"] = spot
    token.meters["near_grill"] = 1.0
    propagate(world, narrate=False)
    world.say(
        f"Then came the surprise. {captain.id}'s nose scrunched up -- ah-ah-choo! "
        f"{token_cfg.drift_name} skipped from {captain.pronoun('possessive')} fingers and sailed {spot.phrase}."
    )
    if world.get("yard").meters["danger"] >= THRESHOLD:
        world.say(
            "At once the game did not feel pretend anymore. The warm grill was real, "
            "and both children knew the mission token had drifted too close."
        )


def back_down(world: World, captain: Entity, partner: Entity, parent: Entity) -> None:
    captain.memes["bravery"] = 0.0
    captain.memes["relief"] += 1
    partner.memes["relief"] += 1
    world.say(
        f"{captain.id} bent for one second as if to reach, then looked at {partner.id} and stopped. "
        f'"You are right," {captain.pronoun()} whispered. "We need {parent.label_word}."'
    )


def defy(world: World, captain: Entity, partner: Entity) -> None:
    captain.memes["defiance"] += 1
    world.say(
        f'"Maybe I can get it fast," {captain.id} said, taking one quick step toward the grill. '
        f'{partner.id} caught {captain.pronoun("possessive")} sleeve and shook {partner.pronoun("possessive")} head.'
    )


def call_parent(world: World, parent: Entity) -> None:
    world.say(f'"{parent.label_word.capitalize()}! Our space thing blew by the grill!" the children called.')


def rescue(world: World, parent: Entity, response: Response, token_cfg: Token,
           spot: Spot, mission: Mission) -> None:
    token = world.get("token")
    token.meters["safe"] += 1
    token.meters["near_grill"] = 0.0
    world.get("yard").meters["danger"] = 0.0
    body = response.text.format(token=token_cfg.label, spot=spot.label)
    world.say(
        f"{parent.label_word.capitalize()} came over at once and {body}."
    )
    world.say(
        f'"Astronauts use tools when something is near a hot grill," {parent.pronoun()} said. '
        f'"Brave does not mean grabbing first. Brave means stopping and thinking."'
    )
    world.say(
        f"Soon {token_cfg.phrase} was back in {captain_name(world)}'s hands, and the mission to "
        f"{mission.goal} could continue the safe way."
    )


def rescue_fail(world: World, parent: Entity, response: Response, token_cfg: Token,
                spot: Spot) -> None:
    token = world.get("token")
    token.meters["singed"] += 1
    token.meters["safe"] += 1
    token.meters["near_grill"] = 0.0
    world.get("yard").meters["danger"] = 0.0
    body = response.fail.format(token=token_cfg.label, spot=spot.label)
    world.say(f"{parent.label_word.capitalize()} hurried over and {body}.")
    world.say(
        f"{token_cfg.phrase.capitalize()} was saved, but one edge had curled brown from the heat."
    )


def lesson(world: World, parent: Entity, captain: Entity, partner: Entity,
           token_cfg: Token, mission: Mission) -> None:
    for kid in (captain, partner):
        kid.memes["lesson"] += 1
        kid.memes["love"] += 1
        kid.memes["fear"] = 0.0
    world.say(
        f"{parent.label_word.capitalize()} knelt beside them. "
        f'"Pollen can surprise a body, and a warm grill is never part of the game," '
        f'{parent.pronoun()} said softly.'
    )
    world.say(
        f'"Next time, if the mission goes crooked, we pause and ask for help," said {partner.id}. '
        f'"Lesson learned," {captain.id} answered.'
    )
    if world.get("token").meters["singed"] >= THRESHOLD:
        world.say(
            f"They kept the little brown mark on the {token_cfg.label} as a reminder of the day "
            f"their space adventure turned real for a moment."
        )
    else:
        world.say(
            f"The surprise had changed the game. Now the children checked the yard first, the same way "
            f"real crews check a launch pad."
        )
    world.say(
        f"After that, they moved their cardboard controls to the shady side of the porch, far from the grill, "
        f"and finished {mission.ending}."
    )


def captain_name(world: World) -> str:
    return world.get("captain").id


def tell(mission: Mission, pollen: Pollen, token_cfg: Token, spot: Spot, response: Response,
         captain: str = "Nova", captain_gender: str = "girl",
         partner: str = "Leo", partner_gender: str = "boy",
         parent_type: str = "mother", trait: str = "careful",
         delay: int = 0, captain_age: int = 5, partner_age: int = 7,
         relation: str = "siblings", trust: int = 6) -> World:
    world = World()
    lead = world.add(Entity(
        id="captain",
        kind="character",
        type=captain_gender,
        label=captain,
        role="captain",
        age=captain_age,
        attrs={"name": captain, "relation": relation},
    ))
    lead.id = captain
    partner_ent = world.add(Entity(
        id="partner",
        kind="character",
        type=partner_gender,
        label=partner,
        role="partner",
        age=partner_age,
        attrs={"name": partner, "relation": relation, "trust": trust},
    ))
    partner_ent.id = partner
    parent = world.add(Entity(
        id="Parent",
        kind="character",
        type=parent_type,
        label="the parent",
        role="parent",
    ))
    grill = world.add(Entity(id="grill", type="grill", label="grill", warm=True))
    yard = world.add(Entity(id="yard", type="yard", label="yard"))
    token = world.add(Entity(
        id="token",
        type="token",
        label=token_cfg.label,
        portable=True,
        blowable=token_cfg.blowable,
    ))
    grill.meters["hot"] = 1.0
    lead.memes["bravery"] = BRAVERY_INIT
    partner_ent.memes["caution"] = initial_caution(trait)
    partner_ent.memes["trust"] = float(trust)
    world.facts["spot"] = spot

    intro(world, lead, partner_ent, mission)
    stage_grill(world, mission)

    world.para()
    pollen_rises(world, lead, pollen, token_cfg)
    warn(world, partner_ent, lead, parent, pollen, spot)
    surprise_sneeze(world, lead, token_cfg, spot)

    averted = would_avert(relation, captain_age, partner_age, trait)

    world.para()
    if averted:
        back_down(world, lead, partner_ent, parent)
    else:
        defy(world, lead, partner_ent)
    call_parent(world, parent)

    contained = can_save(response, spot, delay)
    world.para()
    if contained:
        rescue(world, parent, response, token_cfg, spot, mission)
    else:
        rescue_fail(world, parent, response, token_cfg, spot)

    world.para()
    lesson(world, parent, lead, partner_ent, token_cfg, mission)

    outcome = "averted" if averted else ("retrieved" if contained else "singed")
    world.facts.update(
        captain=lead,
        partner=partner_ent,
        parent=parent,
        grill=grill,
        yard=yard,
        mission=mission,
        pollen=pollen,
        token_cfg=token_cfg,
        token=token,
        response=response,
        spot=spot,
        relation=relation,
        trust=trust,
        delay=delay,
        outcome=outcome,
        surprise=lead.meters["sneeze"] >= THRESHOLD,
        singed=token.meters["singed"] >= THRESHOLD,
        safe=token.meters["safe"] >= THRESHOLD,
    )
    return world


MISSIONS = {
    "moon": Mission(
        id="moon",
        scene="a silver launch field",
        ship="A cardboard box was their rocket, two mixing bowls were helmets, and chalk stars curved across the stepping stones.",
        goal="the moon mailbox",
        call="Captain to mission partner",
        ending="their moon rescue before supper",
    ),
    "mars": Mission(
        id="mars",
        scene="a dusty Mars base",
        ship="An upside-down laundry basket was their rover, two colanders were helmets, and red chalk circles marked the craters.",
        goal="red planet station",
        call="Mission control to rover crew",
        ending="their Mars mission with careful boots and quiet steps",
    ),
    "rings": Mission(
        id="rings",
        scene="the edge of Saturn's rings",
        ship="A picnic bench became the command deck, paper plates became moons, and a string of foil stars blinked along the fence.",
        goal="ring repair post",
        call="Star crew, report in",
        ending="their ring repair adventure under the evening sky",
    ),
}

POLLEN = {
    "dandelions": Pollen(
        id="dandelions",
        label="dandelion pollen",
        source="a patch of dandelions by the fence",
        color="golden",
        strength=1,
        tags={"pollen", "sneeze"},
    ),
    "flowers": Pollen(
        id="flowers",
        label="flower pollen",
        source="the flower bed beside the steps",
        color="yellow",
        strength=2,
        tags={"pollen", "sneeze", "flowers"},
    ),
    "pine": Pollen(
        id="pine",
        label="pine pollen",
        source="the tall pine at the corner of the yard",
        color="green-gold",
        strength=2,
        tags={"pollen", "sneeze", "trees"},
    ),
}

TOKENS = {
    "map": Token(
        id="map",
        label="star map",
        phrase="the paper star map",
        drift_name="The paper star map",
        weight=1,
        blowable=True,
        tags={"map", "paper"},
    ),
    "flag": Token(
        id="flag",
        label="moon flag",
        phrase="the foil moon flag",
        drift_name="The foil moon flag",
        weight=1,
        blowable=True,
        tags={"flag", "foil"},
    ),
    "badge": Token(
        id="badge",
        label="captain badge",
        phrase="the shiny captain badge",
        drift_name="The shiny captain badge",
        weight=2,
        blowable=True,
        tags={"badge", "foil"},
    ),
    "scanner": Token(
        id="scanner",
        label="metal scanner",
        phrase="the little metal scanner",
        drift_name="The little metal scanner",
        weight=3,
        blowable=False,
        tags={"tool"},
    ),
}

SPOTS = {
    "beside": Spot(
        id="beside",
        label="beside the grill",
        phrase="beside the grill",
        distance=1,
        urgency=1,
        tags={"grill"},
    ),
    "under": Spot(
        id="under",
        label="under the grill shelf",
        phrase="under the grill shelf",
        distance=1,
        urgency=2,
        tags={"grill"},
    ),
    "behind": Spot(
        id="behind",
        label="behind the grill wheels",
        phrase="behind the grill wheels",
        distance=2,
        urgency=2,
        tags={"grill"},
    ),
}

RESPONSES = {
    "tongs": Response(
        id="tongs",
        sense=3,
        power=2,
        text="used long kitchen tongs to lift the {token} away from {spot} without anyone getting close to the heat",
        fail="reached with kitchen tongs, but the {token} had already rested too long by {spot}",
        qa_text="used long kitchen tongs to lift it away from the warm grill",
        tags={"tongs", "grill"},
    ),
    "broom": Response(
        id="broom",
        sense=2,
        power=3,
        text="used a broom handle to slide the {token} out from {spot} and then picked it up once it was safely clear",
        fail="tried to slide the {token} out with a broom, but the edge had already touched too much heat near {spot}",
        qa_text="used a broom to slide it out and then picked it up safely",
        tags={"broom", "grill"},
    ),
    "rake": Response(
        id="rake",
        sense=3,
        power=3,
        text="hooked the {token} gently with a small rake and drew it back from {spot}",
        fail="hooked the {token} with a rake, but not before the warm grill had singed one corner by {spot}",
        qa_text="used a small rake to draw it back safely",
        tags={"rake", "grill"},
    ),
    "bare_hands": Response(
        id="bare_hands",
        sense=1,
        power=1,
        text="snatched the {token} away with bare hands",
        fail="reached in with bare hands, which was exactly the unsafe choice the story should avoid",
        qa_text="grabbed it with bare hands",
        tags={"unsafe", "grill"},
    ),
}

GIRL_NAMES = ["Nova", "Luna", "Mia", "Zoe", "Ava", "Ivy", "Nora", "Ruby"]
BOY_NAMES = ["Leo", "Max", "Finn", "Theo", "Eli", "Sam", "Noah", "Ben"]
TRAITS = ["careful", "cautious", "thoughtful", "steady", "curious", "clever"]


@dataclass
class StoryParams:
    mission: str
    pollen: str
    token: str
    spot: str
    response: str
    captain: str
    captain_gender: str
    partner: str
    partner_gender: str
    parent: str
    trait: str
    delay: int = 0
    captain_age: int = 5
    partner_age: int = 7
    relation: str = "siblings"
    trust: int = 6
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
    "pollen": [
        (
            "What is pollen?",
            "Pollen is tiny dusty powder made by plants. On windy days it can float through the air and tickle your nose."
        )
    ],
    "sneeze": [
        (
            "Why do people sneeze when pollen gets in their nose?",
            "Pollen can tickle the inside of the nose. A sneeze is the body's quick way of trying to blow that tickle back out."
        )
    ],
    "grill": [
        (
            "Why should children stay away from a warm grill?",
            "A grill can stay hot even after the cooking is done. If you reach too close, you can get burned, so a grown-up should handle it."
        )
    ],
    "tongs": [
        (
            "What are kitchen tongs for?",
            "Kitchen tongs are long tools that let a grown-up pick things up from a safer distance. They are useful when something is near heat."
        )
    ],
    "broom": [
        (
            "How can a long tool help when something is hard to reach?",
            "A long tool lets you move an object without putting your hands close to the danger. That extra distance can keep you safe."
        )
    ],
    "rake": [
        (
            "What does a small rake do?",
            "A rake can hook or pull light things toward you. In a careful grown-up's hands, it can help retrieve something from a tricky spot."
        )
    ],
    "paper": [
        (
            "Why can paper be ruined by heat?",
            "Paper dries out and browns quickly near heat. Even if it does not burst into flame, it can curl, scorch, and tear."
        )
    ],
    "foil": [
        (
            "What is foil like?",
            "Foil is a thin shiny metal sheet. It is light and crinkly, which is why a breeze can move it."
        )
    ],
    "space": [
        (
            "Why do astronauts check things before a mission?",
            "Astronauts look carefully at tools and places before they begin. Checking first helps them stay safe when something unexpected happens."
        )
    ],
}
KNOWLEDGE_ORDER = ["pollen", "sneeze", "grill", "tongs", "broom", "rake", "paper", "foil", "space"]


def valid_combos() -> list[tuple[str, str, str, str]]:
    combos: list[tuple[str, str, str, str]] = []
    for mission_id in MISSIONS:
        for pollen_id, pollen in POLLEN.items():
            for token_id, token in TOKENS.items():
                for spot_id, spot in SPOTS.items():
                    if sneeze_can_move(pollen, token, spot):
                        combos.append((mission_id, pollen_id, token_id, spot_id))
    return combos


def explain_rejection(pollen: Pollen, token: Token, spot: Spot) -> str:
    if not token.blowable:
        return (
            f"(No story: {token.phrase} is too solid to be blown by a sneeze, so the pollen surprise cannot move it near the grill.)"
        )
    if pollen.strength < token.weight:
        return (
            f"(No story: the {pollen.label} is too light to knock {token.phrase} loose in a believable way. Pick a lighter token or stronger pollen.)"
        )
    return (
        f"(No story: the sneeze from {pollen.label} would not plausibly send {token.phrase} as far as {spot.label}.)"
    )


def explain_response(rid: str) -> str:
    r = RESPONSES[rid]
    better = " / ".join(sorted(x.id for x in sensible_responses()))
    return (
        f"(Refusing response '{rid}': it scores too low on common sense (sense={r.sense} < {SENSE_MIN}). "
        f"Try a safer tool: {better}.)"
    )


def outcome_of(params: StoryParams) -> str:
    if would_avert(params.relation, params.captain_age, params.partner_age, params.trait):
        return "averted"
    contained = can_save(RESPONSES[params.response], SPOTS[params.spot], params.delay)
    return "retrieved" if contained else "singed"


ASP_RULES = r"""
% --- reasonableness gate ---------------------------------------------------
hazard(P, T, S) :- pollen(P), token(T), spot(S),
                   blowable(T), strength(P, Ps), weight(T, Tw), distance(S, D),
                   Ps >= Tw, Ps >= D.
sensible(R) :- response(R), sense(R, S), sense_min(M), S >= M.
valid(M, P, T, S) :- mission(M), hazard(P, T, S).

% --- outcome inference -----------------------------------------------------
cautious_now(T) :- trait(T), is_cautious(T).
init_caution(5) :- trait(T), cautious_now(T).
init_caution(3) :- trait(T), not cautious_now(T).
partner_older :- relation(siblings), captain_age(CA), partner_age(PA), PA > CA.
bonus(4) :- partner_older.
bonus(0) :- not partner_older.
authority(C + 1 + B) :- init_caution(C), bonus(B).
averted :- partner_older, authority(A), bravery_init(BR), A > BR.

risk(U + D) :- chosen_spot(S), urgency(S, U), delay(D).
resp_power(P) :- chosen_response(R), power(R, P).
retrieved :- resp_power(P), risk(V), P >= V.

outcome(averted) :- averted.
outcome(retrieved) :- not averted, retrieved.
outcome(singed) :- not averted, not retrieved.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for mission_id in MISSIONS:
        lines.append(asp.fact("mission", mission_id))
    for pid, pollen in POLLEN.items():
        lines.append(asp.fact("pollen", pid))
        lines.append(asp.fact("strength", pid, pollen.strength))
    for tid, token in TOKENS.items():
        lines.append(asp.fact("token", tid))
        lines.append(asp.fact("weight", tid, token.weight))
        if token.blowable:
            lines.append(asp.fact("blowable", tid))
    for sid, spot in SPOTS.items():
        lines.append(asp.fact("spot", sid))
        lines.append(asp.fact("distance", sid, spot.distance))
        lines.append(asp.fact("urgency", sid, spot.urgency))
    for rid, response in RESPONSES.items():
        lines.append(asp.fact("response", rid))
        lines.append(asp.fact("sense", rid, response.sense))
        lines.append(asp.fact("power", rid, response.power))
    lines.append(asp.fact("sense_min", SENSE_MIN))
    lines.append(asp.fact("bravery_init", int(BRAVERY_INIT)))
    for trait in sorted(CAUTIOUS_TRAITS):
        lines.append(asp.fact("is_cautious", trait))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("", "#show valid/4."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_sensible() -> list[str]:
    import asp

    model = asp.one_model(asp_program("", "#show sensible/1."))
    return sorted(r for (r,) in asp.atoms(model, "sensible"))


def asp_outcome(params: StoryParams) -> str:
    import asp

    scenario = "\n".join(
        [
            asp.fact("chosen_spot", params.spot),
            asp.fact("chosen_response", params.response),
            asp.fact("delay", params.delay),
            asp.fact("relation", params.relation),
            asp.fact("captain_age", params.captain_age),
            asp.fact("partner_age", params.partner_age),
            asp.fact("trait", params.trait),
        ]
    )
    model = asp.one_model(asp_program(scenario, "#show outcome/1."))
    out = asp.atoms(model, "outcome")
    return out[0][0] if out else "?"


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    captain = f["captain"]
    partner = f["partner"]
    mission = f["mission"]
    token = f["token_cfg"]
    pollen = f["pollen"]
    outcome = f["outcome"]
    base = (
        f'Write a short space adventure for a 3-to-5-year-old that includes the words "grill" and "pollen". '
        f"The story should feature a surprise and a lesson learned."
    )
    if outcome == "singed":
        return [
            base,
            f"Tell a backyard space story where {captain.id} and {partner.id} are on a mission to {mission.goal}, "
            f"but {pollen.label} makes {captain.id} sneeze and sends a {token.label} too close to the grill.",
            "Write a gentle cautionary story where a child learns that surprise accidents can happen fast, "
            "so the brave choice is to stop, ask for help, and keep away from hot things.",
        ]
    if outcome == "averted":
        return [
            base,
            f"Tell a story where {partner.id}, the wiser mission partner, stops {captain.id} from reaching near the grill after a pollen sneeze sends the mission token skidding away.",
            "Write a child-facing story with a surprise sneeze, a calm grown-up helper, and an ending that shows the children learned to pause and think.",
        ]
    return [
        base,
        f"Tell a story where {captain.id} and {partner.id} pretend the backyard is space, then a pollen sneeze blows a {token.label} by the grill and a grown-up uses a tool to help.",
        "Write a gentle story with a surprising turn and a clear lesson learned: being careful is part of every good adventure.",
    ]


def pair_noun(captain: Entity, partner: Entity, relation: str) -> str:
    if relation == "siblings":
        if captain.type == "boy" and partner.type == "boy":
            return "two brothers"
        if captain.type == "girl" and partner.type == "girl":
            return "two sisters"
        return "a brother and a sister"
    return "two friends"


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    captain = f["captain"]
    partner = f["partner"]
    parent = f["parent"]
    mission = f["mission"]
    token = f["token_cfg"]
    pollen = f["pollen"]
    spot = f["spot"]
    response = f["response"]
    relation = f["relation"]
    pair = pair_noun(captain, partner, relation)
    pw = parent.label_word
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {pair}, {captain.id} and {partner.id}, who were pretending to fly through space in the backyard. "
            f"Their {pw} helped when the game suddenly turned tricky."
        ),
        (
            "What surprise happened in the story?",
            f"A swirl of pollen tickled {captain.id}'s nose and made {captain.pronoun('object')} sneeze. "
            f"That surprising sneeze sent the {token.label} {spot.phrase}, too close to the warm grill."
        ),
        (
            f"Why was the grill a problem?",
            f"The grill was still warm, so it was not safe for the children to reach near it. "
            f"The danger mattered because the mission token had drifted into a place where hands should not go."
        ),
    ]
    outcome = f["outcome"]
    if outcome == "averted":
        qa.append(
            (
                f"What did {captain.id} do after {partner.id} warned {captain.pronoun('object')}?",
                f"{captain.id} stopped before reaching and called for {pw}'s help instead. "
                f"That shows the lesson learned: real courage can mean backing away from danger."
            )
        )
    elif outcome == "retrieved":
        qa.append(
            (
                f"How did {pw} solve the problem?",
                f"{pw.capitalize()} {response.qa_text}. "
                f"Using a tool kept everyone farther from the warm grill and let the game continue safely."
            )
        )
    else:
        qa.append(
            (
                f"What happened to the {token.label} before it was saved?",
                f"It was rescued, but one edge got singed by the heat. "
                f"The mark became a reminder that a small surprise can turn risky quickly near something warm."
            )
        )
    qa.append(
        (
            "What lesson did the children learn?",
            f"They learned that pollen can cause a sudden sneeze and that a grill is never part of the pretend game. "
            f"When something surprising goes wrong, the safe choice is to pause and ask a grown-up for help."
        )
    )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags: set[str] = {"space"}
    tags |= set(f["pollen"].tags)
    tags |= set(f["spot"].tags)
    tags |= set(f["response"].tags)
    tags |= set(f["token_cfg"].tags)
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
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        flags = [name for name, on in (("warm", ent.warm), ("portable", ent.portable), ("blowable", ent.blowable)) if on]
        if flags:
            bits.append(f"flags={flags}")
        if ent.role:
            bits.append(f"role={ent.role}")
        if ent.age:
            bits.append(f"age={ent.age}")
        if ent.attrs:
            shown = {k: v for k, v in ent.attrs.items() if v != ""}
            if shown:
                bits.append(f"attrs={shown}")
        lines.append(f"  {ent.id:8} ({ent.type:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        mission="moon",
        pollen="flowers",
        token="map",
        spot="under",
        response="tongs",
        captain="Nova",
        captain_gender="girl",
        partner="Leo",
        partner_gender="boy",
        parent="mother",
        trait="careful",
        delay=0,
        captain_age=5,
        partner_age=7,
        relation="siblings",
        trust=6,
    ),
    StoryParams(
        mission="mars",
        pollen="pine",
        token="flag",
        spot="behind",
        response="broom",
        captain="Max",
        captain_gender="boy",
        partner="Ivy",
        partner_gender="girl",
        parent="father",
        trait="curious",
        delay=0,
        captain_age=6,
        partner_age=5,
        relation="friends",
        trust=4,
    ),
    StoryParams(
        mission="rings",
        pollen="flowers",
        token="badge",
        spot="behind",
        response="tongs",
        captain="Luna",
        captain_gender="girl",
        partner="Finn",
        partner_gender="boy",
        parent="mother",
        trait="thoughtful",
        delay=1,
        captain_age=6,
        partner_age=5,
        relation="friends",
        trust=5,
    ),
    StoryParams(
        mission="moon",
        pollen="dandelions",
        token="map",
        spot="beside",
        response="rake",
        captain="Sam",
        captain_gender="boy",
        partner="Nora",
        partner_gender="girl",
        parent="father",
        trait="cautious",
        delay=0,
        captain_age=4,
        partner_age=7,
        relation="siblings",
        trust=7,
    ),
]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Story world sketch: a backyard space adventure, a pollen surprise, and a lesson learned near a warm grill."
    )
    ap.add_argument("--mission", choices=MISSIONS)
    ap.add_argument("--pollen", choices=POLLEN)
    ap.add_argument("--token", choices=TOKENS)
    ap.add_argument("--spot", choices=SPOTS)
    ap.add_argument("--response", choices=RESPONSES)
    ap.add_argument("--parent", choices=["mother", "father"])
    ap.add_argument("--delay", type=int, choices=[0, 1], help="extra moment before help; higher makes singeing more likely")
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


def _pick_child(rng: random.Random, avoid: str = "") -> tuple[str, str]:
    gender = rng.choice(["girl", "boy"])
    pool = [n for n in (GIRL_NAMES if gender == "girl" else BOY_NAMES) if n != avoid]
    return rng.choice(pool), gender


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.pollen and args.token and args.spot:
        pollen = POLLEN[args.pollen]
        token = TOKENS[args.token]
        spot = SPOTS[args.spot]
        if not sneeze_can_move(pollen, token, spot):
            raise StoryError(explain_rejection(pollen, token, spot))
    if args.response and RESPONSES[args.response].sense < SENSE_MIN:
        raise StoryError(explain_response(args.response))

    combos = [
        combo
        for combo in valid_combos()
        if (args.mission is None or combo[0] == args.mission)
        and (args.pollen is None or combo[1] == args.pollen)
        and (args.token is None or combo[2] == args.token)
        and (args.spot is None or combo[3] == args.spot)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    mission_id, pollen_id, token_id, spot_id = rng.choice(sorted(combos))
    response_id = args.response or rng.choice(sorted(r.id for r in sensible_responses()))
    captain, captain_gender = _pick_child(rng)
    partner, partner_gender = _pick_child(rng, avoid=captain)
    parent = args.parent or rng.choice(["mother", "father"])
    trait = rng.choice(TRAITS)
    delay = args.delay if args.delay is not None else rng.choice([0, 1])
    relation = rng.choice(["siblings", "friends"])
    captain_age, partner_age = rng.sample([4, 5, 6, 7], 2)
    trust = rng.randint(2, 8)
    return StoryParams(
        mission=mission_id,
        pollen=pollen_id,
        token=token_id,
        spot=spot_id,
        response=response_id,
        captain=captain,
        captain_gender=captain_gender,
        partner=partner,
        partner_gender=partner_gender,
        parent=parent,
        trait=trait,
        delay=delay,
        captain_age=captain_age,
        partner_age=partner_age,
        relation=relation,
        trust=trust,
    )


def generate(params: StoryParams) -> StorySample:
    try:
        mission = MISSIONS[params.mission]
        pollen = POLLEN[params.pollen]
        token = TOKENS[params.token]
        spot = SPOTS[params.spot]
        response = RESPONSES[params.response]
    except KeyError as err:
        raise StoryError(f"(Invalid parameter: {err.args[0]})") from err

    if not sneeze_can_move(pollen, token, spot):
        raise StoryError(explain_rejection(pollen, token, spot))
    if response.sense < SENSE_MIN:
        raise StoryError(explain_response(params.response))

    world = tell(
        mission=mission,
        pollen=pollen,
        token_cfg=token,
        spot=spot,
        response=response,
        captain=params.captain,
        captain_gender=params.captain_gender,
        partner=params.partner,
        partner_gender=params.partner_gender,
        parent_type=params.parent,
        trait=params.trait,
        delay=params.delay,
        captain_age=params.captain_age,
        partner_age=params.partner_age,
        relation=params.relation,
        trust=params.trust,
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
    clingo_set, python_set = set(asp_valid_combos()), set(valid_combos())
    if clingo_set == python_set:
        print(f"OK: gate matches valid_combos() ({len(clingo_set)} combos).")
    else:
        rc = 1
        print("MISMATCH in the gate:")
        if clingo_set - python_set:
            print("  only in clingo:", sorted(clingo_set - python_set))
        if python_set - clingo_set:
            print("  only in python:", sorted(python_set - clingo_set))

    clingo_sense, python_sense = set(asp_sensible()), {r.id for r in sensible_responses()}
    if clingo_sense == python_sense:
        print(f"OK: sensible responses match ({sorted(clingo_sense)}).")
    else:
        rc = 1
        print(f"MISMATCH in sensible responses: clingo={sorted(clingo_sense)} python={sorted(python_sense)}")

    cases = list(CURATED)
    parser = build_parser()
    for seed in range(100):
        try:
            args = parser.parse_args([])
            cases.append(resolve_params(args, random.Random(seed)))
        except StoryError:
            continue

    bad = sum(1 for p in cases if asp_outcome(p) != outcome_of(p))
    if bad == 0:
        print(f"OK: outcome model matches outcome_of() on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {bad}/{len(cases)} outcomes differ.")

    try:
        smoke_params = copy.deepcopy(CURATED[0])
        smoke_params.seed = 123
        smoke_sample = generate(smoke_params)
        if not smoke_sample.story.strip():
            raise StoryError("smoke test produced an empty story")
        print("OK: smoke test generate() succeeded.")
    except Exception as err:
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    return rc


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("", "#show valid/4.\n#show sensible/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"sensible responses: {', '.join(asp_sensible())}\n")
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (mission, pollen, token, spot) combos:\n")
        for mission_id, pollen_id, token_id, spot_id in combos:
            print(f"  {mission_id:6} {pollen_id:11} {token_id:7} {spot_id}")
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
            header = (
                f"### {p.captain} & {p.partner}: {p.token} near grill "
                f"({p.mission}, {p.pollen}, {p.response}, {outcome_of(p)})"
            )
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()

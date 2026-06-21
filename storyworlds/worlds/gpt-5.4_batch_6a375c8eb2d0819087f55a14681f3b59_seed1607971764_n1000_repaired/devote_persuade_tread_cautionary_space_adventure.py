#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/devote_persuade_tread_cautionary_space_adventure.py
==============================================================================

A standalone story world for a cautionary space adventure: two children playing
astronauts see something glittering beyond a marked path, one child wants to
tread past the safety line, the other tries to persuade them to stop, and the
world branches into a near-miss, a safe rescue, or a bigger emergency depending
on the simulated state.

The storyworld is classical and state-driven:
- typed entities with physical meters and emotional memes
- a small reasonableness gate for risky surfaces and sensible rescues
- a warning beat grounded in forward prediction
- a declarative ASP twin for the gate and outcome model
- three Q&A sets generated from world state, not from parsing prose

Run examples
------------
python storyworlds/worlds/gpt-5.4/devote_persuade_tread_cautionary_space_adventure.py
python storyworlds/worlds/gpt-5.4/devote_persuade_tread_cautionary_space_adventure.py --surface vent_crust --response rescue_bot
python storyworlds/worlds/gpt-5.4/devote_persuade_tread_cautionary_space_adventure.py --surface rock_floor
python storyworlds/worlds/gpt-5.4/devote_persuade_tread_cautionary_space_adventure.py --all
python storyworlds/worlds/gpt-5.4/devote_persuade_tread_cautionary_space_adventure.py -n 5 --seed 7 --qa
python storyworlds/worlds/gpt-5.4/devote_persuade_tread_cautionary_space_adventure.py --verify
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
BOLDNESS_INIT = 6.0
CAREFUL_TRAITS = {"careful", "patient", "steady", "sensible"}


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
    fragile: bool = False
    rescue_tool: bool = False
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
class Theme:
    id: str
    scene: str
    rig: str
    titles: tuple[str, str]
    goal: str
    risky_place: str
    ending_line: str
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
class Lure:
    id: str
    label: str
    phrase: str
    shine: str
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
class Surface:
    id: str
    label: str
    the: str
    warning: str
    detail: str
    danger_kind: str
    severity: int
    fragile: bool = True
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
        return [e for e in self.entities.values() if e.role in {"leader", "partner"}]

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


def _r_surface_breaks(world: World) -> list[str]:
    out: list[str] = []
    surface = world.get("surface")
    if surface.meters["tread"] < THRESHOLD:
        return out
    sig = ("breaks", surface.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    if surface.fragile:
        surface.meters["breach"] += 1
        world.get("room").meters["danger"] += 1
        leader = world.get("leader")
        leader.meters["stuck"] += 1
        leader.meters["alarm"] += 1
        for kid in world.kids():
            kid.memes["fear"] += 1
        out.append("__breach__")
    return out


CAUSAL_RULES: list[Rule] = [
    Rule(name="surface_breaks", tag="physical", apply=_r_surface_breaks),
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
        for sentence in produced:
            world.say(sentence)
    return produced


def hazard_at_risk(surface: Surface) -> bool:
    return surface.fragile


def sensible_responses() -> list[Response]:
    return [r for r in RESPONSES.values() if r.sense >= SENSE_MIN]


def surface_severity(surface: Surface, delay: int) -> int:
    return surface.severity + delay


def is_contained(response: Response, surface: Surface, delay: int) -> bool:
    return response.power >= surface_severity(surface, delay)


def initial_care(trait: str) -> float:
    return 5.0 if trait in CAREFUL_TRAITS else 3.0


def would_avert(relation: str, leader_age: int, partner_age: int, trait: str) -> bool:
    partner_older = relation == "siblings" and partner_age > leader_age
    authority = (initial_care(trait) + 1.0) + (4.0 if partner_older else 0.0)
    return partner_older and authority > BOLDNESS_INIT


def predict_breach(world: World) -> dict:
    sim = world.copy()
    _do_tread(sim, narrate=False)
    return {
        "breach": sim.get("surface").meters["breach"] >= THRESHOLD,
        "danger": sim.get("room").meters["danger"],
        "stuck": sim.get("leader").meters["stuck"] >= THRESHOLD,
    }


def _do_tread(world: World, narrate: bool = True) -> None:
    surface = world.get("surface")
    surface.meters["tread"] += 1
    propagate(world, narrate=narrate)


def play_setup(world: World, leader: Entity, partner: Entity, theme: Theme) -> None:
    for kid in (leader, partner):
        kid.memes["joy"] += 1
    t1, t2 = theme.titles
    world.say(
        f"After lunch, {leader.id} and {partner.id} turned the play dome into {theme.scene}. "
        f"{theme.rig}"
    )
    world.say(
        f"{leader.id} could devote a whole afternoon to a game like this. "
        f'"{t1} {leader.id} and {t2} {partner.id}!" {leader.id} cried. '
        f'"Let\'s find {theme.goal}."'
    )


def spot_lure(world: World, partner: Entity, lure: Lure, theme: Theme, surface: Surface) -> None:
    world.say(
        f"Near {theme.risky_place}, {lure.phrase} winked in the light. "
        f"It looked as if a tiny star had dropped itself right beside {surface.the}."
    )
    world.say(
        f'{partner.id} pointed. "Look! {lure.shine}"'
    )


def tempt(world: World, leader: Entity, lure: Lure, surface: Surface) -> None:
    leader.memes["boldness"] += 1
    world.say(
        f'{leader.id} leaned forward at once. "I can get it," {leader.pronoun()} said. '
        f'"I only need to tread across {surface.the} for one quick step."'
    )


def warn(world: World, partner: Entity, leader: Entity, surface: Surface, guide: Entity) -> None:
    pred = predict_breach(world)
    world.facts["predicted_danger"] = pred["danger"]
    partner.memes["care"] += 1
    world.say(
        f'{partner.id} tried to persuade {leader.id} to stop. '
        f'"Don\'t. {surface.warning} {guide.label_word.capitalize()} said to stay on the silver path. '
        f'If you tread there, it could crack and trap your boot."'
    )


def defy(world: World, leader: Entity, partner: Entity) -> None:
    leader.memes["defiance"] += 1
    older_sib = leader.attrs.get("relation") == "siblings" and leader.age > partner.age
    if older_sib:
        rel = "big brother" if leader.type == "boy" else "big sister"
        world.say(
            f'"I\'ll be fast," {leader.id} said, and because {leader.id} was '
            f'{partner.pronoun("possessive")} {rel}, {partner.id} could not stop '
            f'{leader.pronoun("object")} in time.'
        )
    else:
        world.say(
            f'"I\'ll be fast," {leader.id} said, and slipped past the silver line.'
        )


def back_down(world: World, leader: Entity, partner: Entity, guide: Entity, theme: Theme, lure: Lure) -> None:
    leader.memes["boldness"] = 0.0
    leader.memes["relief"] += 1
    partner.memes["relief"] += 1
    world.say(
        f"{leader.id} looked at the silver path, then at {partner.id}, and stopped. "
        f"The game still felt brave, but now it also felt wise."
    )
    world.say(
        f"They called {guide.label_word.capitalize()} instead. {guide.label_word.capitalize()} used a long grabber arm "
        f"to lift {lure.the if hasattr(lure, 'the') else lure.label} from beside the line, and the children stayed where the floor was safe."
    )


def breach(world: World, leader: Entity, surface: Surface, lure: Lure) -> None:
    _do_tread(world, narrate=True)
    world.say(
        f"{leader.id} set one foot on {surface.the}. At once {surface.detail}. "
        f"{surface.The} gave a sharp snap, and {leader.id}'s boot sank to the ankle beside {lure.phrase}."
    )


def alarm(world: World, partner: Entity, leader: Entity, guide: Entity, surface: Surface) -> None:
    world.say(
        f'"{leader.id}!" {partner.id} gasped. A red alarm blinked over {surface.the}.'
    )
    world.say(f'"{guide.label_word.upper()}!"')


def rescue(world: World, guide: Entity, response: Response, leader: Entity, theme: Theme) -> None:
    leader.meters["stuck"] = 0.0
    leader.meters["alarm"] = 0.0
    world.get("room").meters["danger"] = 0.0
    body = response.text
    world.say(
        f"{guide.label_word.capitalize()} came running. {guide.pronoun().capitalize()} {body}."
    )
    world.say(
        f"Soon {leader.id} stood back on the bright path again, shaky but safe, while the dome lights turned calm blue."
    )
    for kid in world.kids():
        kid.memes["fear"] = 0.0
        kid.memes["relief"] += 1
        kid.memes["lesson"] += 1
    world.say(
        f'Then {guide.label_word.capitalize()} crouched beside them. "A real explorer watches where {guide.pronoun()} treads," '
        f'{guide.pronoun()} said softly. "Space adventures need careful feet."'
    )
    world.say(
        f'{leader.id} nodded. {partner.id} nodded too. After that, they followed the glowing arrows and {theme.ending_line}.'
    )


def rescue_fail(world: World, guide: Entity, response: Response, leader: Entity, surface: Surface) -> None:
    world.get("room").meters["danger"] += 1
    leader.meters["stuck"] += 1
    body = response.fail
    world.say(
        f"{guide.label_word.capitalize()} hurried over and {body}."
    )
    world.say(
        f"The crack spread under {surface.the}, and the whole area flashed red as the dome sealed off that side of the room."
    )


def evacuation(world: World, guide: Entity, leader: Entity, partner: Entity) -> None:
    for kid in (leader, partner):
        kid.memes["fear"] += 1
        kid.memes["lesson"] += 1
    world.say(
        f"{guide.label_word.capitalize()} pulled {partner.id} back first, then guided {leader.id} to the emergency platform. "
        f"They rode away behind a clear shield while repair robots whirred into the glowing dust."
    )
    world.say(
        "The game had to stop. Behind them, the little pretend planet looked quiet and hurt, with warning lights blinking where the crack had spread."
    )


def lesson_hard(world: World, guide: Entity, leader: Entity, partner: Entity, surface: Surface) -> None:
    for kid in (leader, partner):
        kid.memes["relief"] += 1
        kid.memes["love"] += 1
    world.say(
        f'{guide.label_word.capitalize()} wrapped a blanket around both children and held them close. '
        f'"You are safe, and that matters most," {guide.pronoun()} said. '
        f'"But {surface.warning.lower()} The silver path is there for a reason."'
    )
    world.say(
        f"From then on, {leader.id} and {partner.id} never crossed a safety line for a shiny prize again."
    )


def safe_finish(world: World, guide: Entity, leader: Entity, partner: Entity, theme: Theme, lure: Lure) -> None:
    for kid in (leader, partner):
        kid.memes["joy"] += 1
        kid.memes["safety"] += 1
    world.say(
        f"The next day, {guide.label_word.capitalize()} had a surprise. {guide.pronoun().capitalize()} set out a magnet rover "
        f"that could fetch dropped space treasures without anyone leaving the path."
    )
    world.say(
        f'{partner.id} drove it slowly, and {leader.id} cheered when it rolled back with {lure.phrase}.'
    )
    world.say(
        f"Then the two explorers followed the silver path all the way to the end, and {theme.ending_line}."
    )


def tell(
    theme: Theme,
    lure: Lure,
    surface: Surface,
    response: Response,
    leader_name: str = "Nova",
    leader_gender: str = "girl",
    partner_name: str = "Jet",
    partner_gender: str = "boy",
    trait: str = "careful",
    guide_type: str = "mother",
    delay: int = 0,
    leader_age: int = 6,
    partner_age: int = 4,
    relation: str = "siblings",
    trust: int = 6,
    pet: str = "",
) -> World:
    world = World()
    leader = world.add(
        Entity(
            id=leader_name,
            kind="character",
            type=leader_gender,
            role="leader",
            age=leader_age,
            attrs={"relation": relation},
            traits=["bold"],
        )
    )
    partner = world.add(
        Entity(
            id=partner_name,
            kind="character",
            type=partner_gender,
            role="partner",
            age=partner_age,
            attrs={"relation": relation, "pet": pet},
            traits=[trait],
        )
    )
    guide = world.add(
        Entity(
            id="Guide",
            kind="character",
            type=guide_type,
            role="guide",
            label="the guide",
        )
    )
    world.add(Entity(id="room", type="dome", label="the dome"))
    world.add(Entity(id="surface", type="surface", label=surface.label, fragile=surface.fragile))
    world.facts["pet"] = pet
    leader.memes["boldness"] = BOLDNESS_INIT
    partner.memes["trust"] = float(trust)
    partner.memes["care"] = initial_care(trait)

    play_setup(world, leader, partner, theme)
    spot_lure(world, partner, lure, theme, surface)

    world.para()
    tempt(world, leader, lure, surface)
    warn(world, partner, leader, surface, guide)

    averted = would_avert(relation, leader_age, partner_age, trait)
    if averted:
        back_down(world, leader, partner, guide, theme, lure)
        outcome = "averted"
        severity = 0
        contained = True
        world.para()
        safe_finish(world, guide, leader, partner, theme, lure)
    else:
        defy(world, leader, partner)
        world.para()
        breach(world, leader, surface, lure)
        alarm(world, partner, leader, guide, surface)
        severity = surface_severity(surface, delay)
        world.get("surface").meters["severity"] = float(severity)
        contained = is_contained(response, surface, delay)
        world.para()
        if contained:
            rescue(world, guide, response, leader, theme)
            world.para()
            safe_finish(world, guide, leader, partner, theme, lure)
            outcome = "contained"
        else:
            rescue_fail(world, guide, response, leader, surface)
            evacuation(world, guide, leader, partner)
            lesson_hard(world, guide, leader, partner, surface)
            outcome = "sealed"

    world.facts.update(
        leader=leader,
        partner=partner,
        guide=guide,
        theme=theme,
        lure=lure,
        surface_cfg=surface,
        response=response,
        outcome=outcome,
        severity=severity,
        delay=delay,
        relation=relation,
        trapped=world.get("leader").meters["stuck"] >= THRESHOLD or outcome == "sealed",
        promised=leader.memes["lesson"] >= THRESHOLD or partner.memes["lesson"] >= THRESHOLD,
    )
    return world


THEMES = {
    "moon_base": Theme(
        id="moon_base",
        scene="a silver moon base under a pretend black sky",
        rig="A blanket over the couch became a crater ridge, a chair became mission control, and glow tape made a bright path across the floor.",
        titles=("Captain", "Scout"),
        goal="the fallen star marker",
        risky_place="the far crater edge",
        ending_line="their boots clicked neatly where the safe lights said to go",
    ),
    "mars_lab": Theme(
        id="mars_lab",
        scene="a red planet station full of humming panels",
        rig="The table became a rover bay, cardboard boxes became cargo pods, and blue tape made a careful trail through the room.",
        titles=("Commander", "Pilot"),
        goal="the comet sample box",
        risky_place="the dusty test field",
        ending_line="their helmets bobbed happily as they kept to the bright trail",
    ),
    "asteroid_port": Theme(
        id="asteroid_port",
        scene="a tiny asteroid port floating above the stars",
        rig="A laundry basket became a shuttle dock, pillows became drifting rocks, and a shining strip on the floor marked the only safe walkway.",
        titles=("Explorer", "Navigator"),
        goal="the beacon coin",
        risky_place="the cargo rim",
        ending_line="they marched homeward along the lighted path like true space travelers",
    ),
}

LURES = {
    "star_coin": Lure(
        id="star_coin",
        label="star coin",
        phrase="a gold star coin",
        shine='"A gold star coin is blinking over there!"',
        tags={"coin", "treasure"},
    ),
    "comet_badge": Lure(
        id="comet_badge",
        label="comet badge",
        phrase="a blue comet badge",
        shine='"That blue comet badge is sparkling!"',
        tags={"badge", "treasure"},
    ),
    "crystal_key": Lure(
        id="crystal_key",
        label="crystal key",
        phrase="a tiny crystal key",
        shine='"That crystal key looks like moonlight!"',
        tags={"crystal", "treasure"},
    ),
}

SURFACES = {
    "vent_crust": Surface(
        id="vent_crust",
        label="vent crust",
        the="the powdery vent crust",
        warning="Do not tread on the vent crust",
        detail="the dusty skin sagged over a warm air pocket",
        danger_kind="crack",
        severity=3,
        fragile=True,
        tags={"fragile_floor", "warning_line"},
    ),
    "ice_skin": Surface(
        id="ice_skin",
        label="ice skin",
        the="the thin ice skin",
        warning="Do not tread on the ice skin",
        detail="the pale sheet shivered over the cold fog machine below",
        danger_kind="slip",
        severity=2,
        fragile=True,
        tags={"ice", "warning_line"},
    ),
    "solar_tiles": Surface(
        id="solar_tiles",
        label="loose solar tiles",
        the="the loose solar tiles",
        warning="Do not tread on the solar tiles",
        detail="the tiles tipped and clacked under the weight",
        danger_kind="collapse",
        severity=2,
        fragile=True,
        tags={"solar", "warning_line"},
    ),
    "rock_floor": Surface(
        id="rock_floor",
        label="rock floor",
        the="the solid rock floor",
        warning="The rock floor is fine to walk on",
        detail="nothing moved at all",
        danger_kind="none",
        severity=0,
        fragile=False,
        tags={"stable_floor"},
    ),
}

RESPONSES = {
    "rescue_bot": Response(
        id="rescue_bot",
        sense=3,
        power=4,
        text="sent the little rescue bot gliding over the crack, clipped a tether to the trapped boot, and reeled the child back to the path",
        fail="sent the rescue bot forward, but the break spread faster than its tether could hold",
        qa_text="used a rescue bot and tether to pull the child back to the path",
        tags={"robot", "tether", "rescue"},
    ),
    "foam_bridge": Response(
        id="foam_bridge",
        sense=3,
        power=3,
        text="sprayed quick-set safety foam across the weak spot and made a firm bridge to step on",
        fail="sprayed safety foam, but the weak patch was already too wide to bridge",
        qa_text="sprayed safety foam to make a safe bridge",
        tags={"foam", "rescue"},
    ),
    "hook_pole": Response(
        id="hook_pole",
        sense=2,
        power=2,
        text="slid a hooked pole across the line and pulled the child's boot free before the crack grew",
        fail="reached with the hook pole, but the floor kept breaking apart",
        qa_text="used a hooked pole to pull the child's boot free",
        tags={"pole", "rescue"},
    ),
    "shout_instructions": Response(
        id="shout_instructions",
        sense=1,
        power=1,
        text="shouted instructions from far away until the child wriggled loose",
        fail="shouted instructions, but words alone could not stop the crack from spreading",
        qa_text="shouted instructions until the child got free",
        tags={"voice"},
    ),
}

GIRL_NAMES = ["Nova", "Luna", "Mira", "Ava", "Ivy", "Tara", "Zoe", "Nia"]
BOY_NAMES = ["Jet", "Leo", "Max", "Finn", "Orion", "Theo", "Kai", "Milo"]
TRAITS = ["careful", "patient", "steady", "sensible", "curious", "bright"]
PETS = ["the cat", "the puppy", "their little robot dog", ""]


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    if not sensible_responses():
        return combos
    for theme_id in THEMES:
        for lure_id in LURES:
            for surface_id, surface in SURFACES.items():
                if hazard_at_risk(surface):
                    combos.append((theme_id, lure_id, surface_id))
    return combos


@dataclass
class StoryParams:
    theme: str
    lure: str
    surface: str
    response: str
    leader: str
    leader_gender: str
    partner: str
    partner_gender: str
    guide: str
    trait: str
    delay: int = 0
    leader_age: int = 6
    partner_age: int = 4
    relation: str = "siblings"
    trust: int = 6
    pet: str = ""
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
    "fragile_floor": [
        (
            "Why can a crust over a vent be dangerous?",
            "A crust over a vent can look solid even when it is thin. If someone steps on it, it may crack because there is empty space or moving air underneath.",
        )
    ],
    "ice": [
        (
            "Why is thin ice dangerous?",
            "Thin ice can break when something heavy steps on it. That can make a person slip or get stuck very quickly.",
        )
    ],
    "solar": [
        (
            "Why should you stay off loose solar tiles?",
            "Loose tiles can tip or crack under your feet. Safe paths are marked so people know where to walk.",
        )
    ],
    "warning_line": [
        (
            "Why do places have safety lines on the floor?",
            "Safety lines show where it is safe to stand or walk. They help people stay away from weak, hot, or dangerous places.",
        )
    ],
    "robot": [
        (
            "What is a rescue robot for?",
            "A rescue robot can go somewhere risky without putting another person in danger. It can carry a tether or tools to help someone safely.",
        )
    ],
    "tether": [
        (
            "What is a tether?",
            "A tether is a strong line that keeps something from drifting or falling away. In a rescue, it can help pull someone back to safety.",
        )
    ],
    "foam": [
        (
            "What can safety foam do?",
            "Safety foam can spread over a weak spot and make a safer surface for a short time. Grown-ups use it as a tool, not as a toy.",
        )
    ],
    "pole": [
        (
            "Why might a long hooked pole help in a rescue?",
            "A long pole lets a helper reach someone without stepping into the dangerous place. That means the rescuer stays safer too.",
        )
    ],
    "rescue": [
        (
            "What should you do if someone steps into a dangerous place?",
            "Call a grown-up or trained helper right away and stay back. Fast help and calm choices matter more than being brave in the wrong way.",
        )
    ],
    "treasure": [
        (
            "Why is it not smart to grab a shiny thing in an unsafe place?",
            "A shiny prize is never worth getting hurt for. If something is beyond a safety line, ask a grown-up for help instead.",
        )
    ],
}
KNOWLEDGE_ORDER = [
    "fragile_floor",
    "ice",
    "solar",
    "warning_line",
    "robot",
    "tether",
    "foam",
    "pole",
    "rescue",
    "treasure",
]


def pair_noun(leader: Entity, partner: Entity, relation: str) -> str:
    if relation == "siblings":
        if leader.type == "boy" and partner.type == "boy":
            return "two brothers"
        if leader.type == "girl" and partner.type == "girl":
            return "two sisters"
        return "a brother and a sister"
    return "two friends"


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    leader = f["leader"]
    partner = f["partner"]
    theme = f["theme"]
    lure = f["lure"]
    surface = f["surface_cfg"]
    outcome = f["outcome"]
    if outcome == "averted":
        return [
            f'Write a short cautionary space adventure for a 3-to-5-year-old where two children see {lure.phrase} beyond a safety line, one tries to tread closer, and the other persuades them to stop.',
            f'Write a child-facing story that includes the words "devote", "persuade", and "tread", with a near-miss ending in which no one gets hurt.',
            f"Tell a gentle space-station story where {leader.id} wants to step onto {surface.the}, but {partner.id} talks {leader.pronoun('object')} out of it and they choose the safe path instead.",
        ]
    if outcome == "sealed":
        return [
            f"Write a cautionary space adventure where a child ignores a warning and treads onto {surface.the}, causing a bigger emergency.",
            f'Write a story for young children using the words "devote", "persuade", and "tread", where a shiny treasure leads to trouble and the ending feels serious but safe.',
            f"Tell a sadder warning story where the danger zone must be sealed after {leader.id} crosses the safety line for {lure.phrase}.",
        ]
    return [
        f"Write a cautionary space adventure for a 3-to-5-year-old where two children playing explorers spot {lure.phrase} beyond a marked path.",
        f'Write a story that uses the words "devote", "persuade", and "tread", and shows a risky choice followed by a calm rescue.',
        f"Tell a gentle warning story where {partner.id} tries to persuade {leader.id} not to cross onto {surface.the}, and a grown-up helps when the danger appears.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    leader = f["leader"]
    partner = f["partner"]
    guide = f["guide"]
    theme = f["theme"]
    lure = f["lure"]
    surface = f["surface_cfg"]
    response = f["response"]
    pair = pair_noun(leader, partner, f["relation"])
    pw = guide.label_word
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {pair}, {leader.id} and {partner.id}, who were playing a space adventure. {pw.capitalize()} was nearby to help when the game turned risky.",
        ),
        (
            "What were they pretending to do?",
            f"They turned the room into {theme.scene} and went looking for {theme.goal}. The pretend mission made the shiny object feel extra exciting.",
        ),
        (
            f"Why did {partner.id} warn {leader.id}?",
            f"{partner.id} knew {surface.warning.lower()}. {partner.pronoun().capitalize()} tried to persuade {leader.id} because stepping there could crack the surface and trap a boot.",
        ),
    ]
    if f["outcome"] == "averted":
        qa.append(
            (
                f"What changed {leader.id}'s mind?",
                f"{leader.id} looked at the safety line and listened to {partner.id}'s warning. Because {partner.id} sounded calm and sure, {leader.id} stopped before the dangerous step happened.",
            )
        )
        qa.append(
            (
                "How did the story end?",
                f"It ended safely with a helper fetching {lure.phrase} another way. The children kept their space game, but now they followed the marked path.",
            )
        )
    elif f["outcome"] == "contained":
        qa.append(
            (
                f"What happened when {leader.id} stepped onto {surface.the}?",
                f"{surface.The} cracked and trapped {leader.id}'s boot, and the red alarm came on. The trouble began because the warning line was crossed for a shiny prize.",
            )
        )
        qa.append(
            (
                f"How did {pw} help?",
                f"{pw.capitalize()} {response.qa_text}. That quick rescue stopped the danger from spreading through the play dome.",
            )
        )
        qa.append(
            (
                "What did the children learn?",
                f"They learned that brave explorers watch where they tread. After the rescue, they still played happily, but they stayed on the safe path.",
            )
        )
    else:
        qa.append(
            (
                f"Why did the game have to stop?",
                f"The weak floor kept breaking after {leader.id} stepped onto it, so the area had to be sealed. The danger grew too large for a small fix, and everyone had to move away.",
            )
        )
        qa.append(
            (
                "How did the story end?",
                f"It ended with the children safe but sobered, wrapped up together while repair robots worked. The blinking warning lights showed that one careless step had changed the whole game.",
            )
        )
        qa.append(
            (
                "What was the lesson?",
                f"The lesson was that a shiny prize is never worth crossing a safety line for. The children remembered that careful feet matter in adventures and in real life too.",
            )
        )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags: set[str] = set(f["surface_cfg"].tags) | set(f["lure"].tags)
    outcome = f["outcome"]
    if outcome == "contained":
        tags |= set(f["response"].tags)
    elif outcome == "sealed":
        tags |= set(f["response"].tags) | {"rescue"}
    else:
        tags |= {"rescue"}
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
        if ent.role:
            bits.append(f"role={ent.role}")
        if ent.age:
            bits.append(f"age={ent.age}")
        if ent.attrs:
            shown = {k: v for k, v in ent.attrs.items() if v}
            if shown:
                bits.append(f"attrs={shown}")
        if ent.fragile:
            bits.append("fragile=True")
        lines.append(f"  {ent.id:8} ({ent.type:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        theme="moon_base",
        lure="star_coin",
        surface="vent_crust",
        response="rescue_bot",
        leader="Nova",
        leader_gender="girl",
        partner="Jet",
        partner_gender="boy",
        guide="mother",
        trait="careful",
        delay=0,
        leader_age=6,
        partner_age=4,
        relation="siblings",
        trust=7,
        pet="their little robot dog",
    ),
    StoryParams(
        theme="mars_lab",
        lure="comet_badge",
        surface="ice_skin",
        response="foam_bridge",
        leader="Milo",
        leader_gender="boy",
        partner="Luna",
        partner_gender="girl",
        guide="father",
        trait="steady",
        delay=0,
        leader_age=5,
        partner_age=7,
        relation="siblings",
        trust=4,
        pet="the cat",
    ),
    StoryParams(
        theme="asteroid_port",
        lure="crystal_key",
        surface="solar_tiles",
        response="hook_pole",
        leader="Orion",
        leader_gender="boy",
        partner="Mira",
        partner_gender="girl",
        guide="mother",
        trait="curious",
        delay=1,
        leader_age=6,
        partner_age=5,
        relation="friends",
        trust=5,
        pet="",
    ),
    StoryParams(
        theme="moon_base",
        lure="comet_badge",
        surface="vent_crust",
        response="hook_pole",
        leader="Kai",
        leader_gender="boy",
        partner="Nia",
        partner_gender="girl",
        guide="father",
        trait="patient",
        delay=2,
        leader_age=7,
        partner_age=5,
        relation="siblings",
        trust=3,
        pet="the puppy",
    ),
]


def explain_rejection(surface: Surface) -> str:
    return (
        f"(No story: {surface.the} is not a real hazard here, so there is no honest warning, no risky turn, and no rescue. "
        f"Pick a fragile surface like vent_crust, ice_skin, or solar_tiles.)"
    )


def explain_response(rid: str) -> str:
    response = RESPONSES[rid]
    better = " / ".join(sorted(r.id for r in sensible_responses()))
    return (
        f"(Refusing response '{rid}': it scores too low on common sense "
        f"(sense={response.sense} < {SENSE_MIN}). Try one of: {better}.)"
    )


def outcome_of(params: StoryParams) -> str:
    if would_avert(params.relation, params.leader_age, params.partner_age, params.trait):
        return "averted"
    contained = is_contained(RESPONSES[params.response], SURFACES[params.surface], params.delay)
    return "contained" if contained else "sealed"


ASP_RULES = r"""
hazard(S) :- surface(S), fragile(S).
sensible(R) :- response(R), sense(R, V), sense_min(M), V >= M.
valid(T, L, S) :- theme(T), lure(L), surface(S), hazard(S).

careful_now(T) :- trait(T), is_careful(T).
init_care(5) :- trait(T), careful_now(T).
init_care(3) :- trait(T), not careful_now(T).

partner_older :- relation(siblings), leader_age(LA), partner_age(PA), PA > LA.
bonus(4) :- partner_older.
bonus(0) :- not partner_older.
authority(C + 1 + B) :- init_care(C), bonus(B).
averted :- partner_older, authority(A), boldness_init(B), A > B.

severity(V + D) :- chosen_surface(S), base_severity(S, V), delay(D).
resp_power(P) :- chosen_response(R), power(R, P).
contained :- resp_power(P), severity(S), P >= S.

outcome(averted) :- averted.
outcome(contained) :- not averted, contained.
outcome(sealed) :- not averted, not contained.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for theme_id in THEMES:
        lines.append(asp.fact("theme", theme_id))
    for lure_id in LURES:
        lines.append(asp.fact("lure", lure_id))
    for surface_id, surface in SURFACES.items():
        lines.append(asp.fact("surface", surface_id))
        if surface.fragile:
            lines.append(asp.fact("fragile", surface_id))
        lines.append(asp.fact("base_severity", surface_id, surface.severity))
    for rid, response in RESPONSES.items():
        lines.append(asp.fact("response", rid))
        lines.append(asp.fact("sense", rid, response.sense))
        lines.append(asp.fact("power", rid, response.power))
    lines.append(asp.fact("sense_min", SENSE_MIN))
    lines.append(asp.fact("boldness_init", int(BOLDNESS_INIT)))
    for trait in sorted(CAREFUL_TRAITS):
        lines.append(asp.fact("is_careful", trait))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


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

    scenario = "\n".join(
        [
            asp.fact("chosen_surface", params.surface),
            asp.fact("chosen_response", params.response),
            asp.fact("delay", params.delay),
            asp.fact("relation", params.relation),
            asp.fact("leader_age", params.leader_age),
            asp.fact("partner_age", params.partner_age),
            asp.fact("trait", params.trait),
        ]
    )
    model = asp.one_model(asp_program(scenario, "#show outcome/1."))
    out = asp.atoms(model, "outcome")
    return out[0][0] if out else "?"


def asp_verify() -> int:
    rc = 0

    clingo_set = set(asp_valid_combos())
    python_set = set(valid_combos())
    if clingo_set == python_set:
        print(f"OK: gate matches valid_combos() ({len(clingo_set)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos:")
        if clingo_set - python_set:
            print("  only in clingo:", sorted(clingo_set - python_set))
        if python_set - clingo_set:
            print("  only in python:", sorted(python_set - clingo_set))

    clingo_sensible = set(asp_sensible())
    python_sensible = {r.id for r in sensible_responses()}
    if clingo_sensible == python_sensible:
        print(f"OK: sensible responses match ({sorted(clingo_sensible)}).")
    else:
        rc = 1
        print(
            f"MISMATCH in sensible responses: clingo={sorted(clingo_sensible)} "
            f"python={sorted(python_sensible)}"
        )

    cases = list(CURATED)
    parser = build_parser()
    for seed in range(60):
        try:
            params = resolve_params(parser.parse_args([]), random.Random(seed))
            params.seed = seed
            cases.append(params)
        except StoryError:
            continue
    bad = sum(1 for p in cases if asp_outcome(p) != outcome_of(p))
    if bad == 0:
        print(f"OK: outcome model matches outcome_of() on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {bad}/{len(cases)} outcomes differ.")

    try:
        smoke_params = resolve_params(parser.parse_args([]), random.Random(123))
        smoke_params.seed = 123
        smoke_sample = generate(smoke_params)
        if not smoke_sample.story.strip():
            raise StoryError("smoke test produced an empty story")
        emit(smoke_sample, trace=False, qa=False, header="### smoke test")
        print("OK: smoke generation succeeded.")
    except Exception as err:  # pragma: no cover - verification path
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Story world sketch: a cautionary space adventure with a marked safe path."
    )
    ap.add_argument("--theme", choices=THEMES)
    ap.add_argument("--lure", choices=LURES)
    ap.add_argument("--surface", choices=SURFACES)
    ap.add_argument("--response", choices=RESPONSES)
    ap.add_argument("--guide", choices=["mother", "father"])
    ap.add_argument(
        "--delay",
        type=int,
        choices=[0, 1, 2],
        help="how long the danger grows before help fully reaches the child",
    )
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list the compatible-story set derived by clingo")
    ap.add_argument("--verify", action="store_true", help="check the inline ASP reasoner against the Python model")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def _pick_kid(rng: random.Random, avoid: str = "") -> tuple[str, str]:
    gender = rng.choice(["girl", "boy"])
    pool = GIRL_NAMES if gender == "girl" else BOY_NAMES
    names = [name for name in pool if name != avoid]
    return rng.choice(names), gender


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.surface and not SURFACES[args.surface].fragile:
        raise StoryError(explain_rejection(SURFACES[args.surface]))
    if args.response and RESPONSES[args.response].sense < SENSE_MIN:
        raise StoryError(explain_response(args.response))

    combos = [
        combo
        for combo in valid_combos()
        if (args.theme is None or combo[0] == args.theme)
        and (args.lure is None or combo[1] == args.lure)
        and (args.surface is None or combo[2] == args.surface)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    theme, lure, surface = rng.choice(sorted(combos))
    response = args.response or rng.choice(sorted(r.id for r in sensible_responses()))
    leader, leader_gender = _pick_kid(rng)
    partner, partner_gender = _pick_kid(rng, avoid=leader)
    guide = args.guide or rng.choice(["mother", "father"])
    trait = rng.choice(TRAITS)
    delay = args.delay if args.delay is not None else rng.randint(0, 2)
    relation = rng.choice(["siblings", "friends"])
    leader_age, partner_age = rng.sample([3, 4, 5, 6, 7], 2)
    trust = rng.randint(0, 10)
    pet = rng.choice(PETS)
    return StoryParams(
        theme=theme,
        lure=lure,
        surface=surface,
        response=response,
        leader=leader,
        leader_gender=leader_gender,
        partner=partner,
        partner_gender=partner_gender,
        guide=guide,
        trait=trait,
        delay=delay,
        leader_age=leader_age,
        partner_age=partner_age,
        relation=relation,
        trust=trust,
        pet=pet,
    )


def generate(params: StoryParams) -> StorySample:
    try:
        theme = THEMES[params.theme]
        lure = LURES[params.lure]
        surface = SURFACES[params.surface]
        response = RESPONSES[params.response]
    except KeyError as err:
        raise StoryError(f"(Unknown parameter value: {err.args[0]})") from None

    if not hazard_at_risk(surface):
        raise StoryError(explain_rejection(surface))
    if response.sense < SENSE_MIN:
        raise StoryError(explain_response(response.id))

    world = tell(
        theme=theme,
        lure=lure,
        surface=surface,
        response=response,
        leader_name=params.leader,
        leader_gender=params.leader_gender,
        partner_name=params.partner,
        partner_gender=params.partner_gender,
        trait=params.trait,
        guide_type=params.guide,
        delay=params.delay,
        leader_age=params.leader_age,
        partner_age=params.partner_age,
        relation=params.relation,
        trust=params.trust,
        pet=params.pet,
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
        print(asp_program("", "#show valid/3.\n#show sensible/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"sensible responses: {', '.join(asp_sensible())}\n")
        print(f"{len(combos)} compatible (theme, lure, surface) combos:\n")
        for theme, lure, surface in combos:
            print(f"  {theme:12} {lure:12} {surface}")
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
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for idx, sample in enumerate(samples):
        header = ""
        if args.all:
            p = sample.params
            header = (
                f"### {p.leader} & {p.partner}: {p.lure} near {p.surface} "
                f"({p.theme}, {p.response}, {outcome_of(p)})"
            )
        elif len(samples) > 1:
            header = f"### variant {idx + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if idx < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()

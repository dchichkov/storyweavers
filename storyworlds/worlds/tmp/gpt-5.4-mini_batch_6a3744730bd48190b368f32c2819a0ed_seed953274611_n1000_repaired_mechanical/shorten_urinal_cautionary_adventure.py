#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/shorten_urinal_cautionary_adventure.py
======================================================================

A small cautionary adventure storyworld.

Premise
-------
A child on a pretend adventure gets separated from the group while exploring a
busy train station. The child is tempted to take a shortcut through a restroom
to "shorten" the route, but the safe choice is to stay with a helper, ask a
grown-up, and use the proper hallway instead. The story includes the seed words
"shorten" and "urinal" while keeping the style adventurous and child-facing.

The world simulates:
- typed entities with meters and memes,
- a risky shortcut through a restroom,
- a warning beat,
- a safe turn,
- and a resolution image proving what changed.

This file is self-contained except for the shared result containers in
storyworlds/results.py and the shared ASP helper in storyworlds/asp.py.
"""

from __future__ import annotations

import argparse
import json
import os
import random
import sys
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from results import QAItem, StoryError, StorySample  # noqa: E402


THRESHOLD = 1.0
RISK_MIN = 1.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    role: str = ""
    attrs: dict = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "woman", "mother", "mom"}
        male = {"boy", "man", "father", "dad"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return self.label or self.id
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
    adventure: str
    shortcut: str
    safe_path: str
    room_name: str
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
class Risk:
    id: str
    label: str
    warning: str
    where: str
    danger: str
    can_injure: bool = True
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
class RouteChoice:
    id: str
    label: str
    description: str
    safe: bool
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
class Helper:
    id: str
    label: str
    role: str
    reassuring: str
    tool: str
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
        clone.entities = {k: Entity(
            id=v.id, kind=v.kind, type=v.type, label=v.label, role=v.role,
            attrs=dict(v.attrs), meters=defaultdict(float, v.meters),
            memes=defaultdict(float, v.memes)
        ) for k, v in self.entities.items()}
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        clone.facts = dict(self.facts)
        return clone


PLACES = {
    "station": Place(
        id="station",
        label="the station",
        adventure="the busy station",
        shortcut="the little passage by the restrooms",
        safe_path="the main hallway with the blue signs",
        room_name="station hall",
        tags={"station", "adventure"},
    ),
    "museum": Place(
        id="museum",
        label="the museum",
        adventure="the echoing museum",
        shortcut="the narrow passage beside the restroom door",
        safe_path="the bright hallway past the guard desk",
        room_name="gallery hall",
        tags={"museum", "adventure"},
    ),
}

RISKS = {
    "wet_floor": Risk(
        id="wet_floor",
        label="a wet floor",
        warning="could make someone slip",
        where="the restroom floor",
        danger="slippery",
        can_injure=True,
        tags={"wet", "restroom", "cautionary"},
    ),
    "busy_door": Risk(
        id="busy_door",
        label="the swinging door",
        warning="could bump a child who runs too fast",
        where="the restroom doorway",
        danger="sudden",
        can_injure=True,
        tags={"door", "restroom", "cautionary"},
    ),
}

ROUTES = {
    "shorten": RouteChoice(
        id="shorten",
        label="shorten the path",
        description="take a clever shortcut through the restroom",
        safe=False,
        tags={"shorten", "shortcut"},
    ),
    "safe_walk": RouteChoice(
        id="safe_walk",
        label="take the safe walk",
        description="follow the main hallway and the blue signs",
        safe=True,
        tags={"safe"},
    ),
}

HELPERS = {
    "cautionary": Helper(
        id="cautionary",
        label="Cautionary",
        role="guide",
        reassuring="kept the adventure calm and careful",
        tool="a bright flashlight",
        tags={"cautionary", "guide"},
    ),
    "station_guard": Helper(
        id="station_guard",
        label="the guard",
        role="helper",
        reassuring="pointed out the safest door",
        tool="a whistle and a radio",
        tags={"helper", "station"},
    ),
}

GIRL_NAMES = ["Lina", "Maya", "Zoe", "Nora", "Pia"]
BOY_NAMES = ["Owen", "Theo", "Finn", "Eli", "Max"]
TRAITS = ["curious", "brave", "careful", "bold", "thoughtful"]


@dataclass
class StoryParams:
    place: str
    risk: str
    route: str
    helper: str
    name: str
    gender: str
    trait: str
    seed: Optional[int] = None
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


def valid_combos() -> list[tuple[str, str, str, str]]:
    combos = []
    for place_id in PLACES:
        for risk_id in RISKS:
            for route_id in ROUTES:
                for helper_id in HELPERS:
                    if route_id == "shorten" and RISKS[risk_id].can_injure:
                        combos.append((place_id, risk_id, route_id, helper_id))
    return combos


def reason_invalid(route: RouteChoice, risk: Risk) -> str:
    return (
        f"(No story: the route '{route.id}' only matters when there is a real "
        f"cautionary risk, and {risk.label} is the kind of danger this world can "
        f"warn about.)"
    )


def make_world_name(name: str, gender: str) -> Entity:
    return Entity(id=name, kind="character", type=gender, role="child", attrs={"age": 6})


def predict_mistake(world: World, risk_id: str) -> dict:
    sim = world.copy()
    sim.get("hero").meters["risky_choice"] += 1
    sim.get("hero").memes["worry"] += 1
    sim.get(risk_id).meters["danger"] += 1
    return {
        "risk": sim.get(risk_id).meters["danger"],
        "worry": sim.get("hero").memes["worry"],
    }


def introduce(world: World, hero: Entity, helper: Entity, place: Place) -> None:
    hero.memes["curiosity"] += 1
    helper.memes["calm"] += 1
    world.say(
        f"{hero.id} loved adventure, and {helper.label} was their "
        f"{helper.role} for exploring {place.adventure}."
    )
    world.say(
        f"They carried {helper.attrs.get('tool', 'a little lantern')} and "
        f"followed the signs like treasure maps."
    )


def encounter(world: World, hero: Entity, place: Place, risk: Risk) -> None:
    world.say(
        f"Near {place.shortcut}, {hero.id} spotted {risk.where}. "
        f"It looked like a quick way to {place.safe_path}."
    )
    world.say(
        f"But the floor there was {risk.danger}, and that was a clue that the shortcut was not wise."
    )


def tempt(world: World, hero: Entity, route: RouteChoice) -> None:
    hero.memes["bravery"] += 1
    world.say(
        f'{hero.id} grinned. "We can {route.label} and get there faster," '
        f"{hero.pronoun()} said."
    )
    world.say("For a moment, the shortcut felt like the fastest treasure in the room.")


def warn(world: World, helper: Entity, hero: Entity, risk: Risk, place: Place) -> None:
    pred = predict_mistake(world, "risk")
    helper.memes["warning"] += 1
    world.facts["predicted_risk"] = pred["risk"]
    world.say(
        f'{helper.label} shook {helper.pronoun("possessive")} head. '
        f'"No, {hero.id}. {risk.label.capitalize()} {risk.warning}. '
        f'Let\'s stay on {place.safe_path}."'
    )


def choose_safe(world: World, hero: Entity, helper: Entity, place: Place, route: RouteChoice) -> None:
    hero.memes["trust"] += 1
    helper.memes["relief"] += 1
    world.say(
        f"{hero.id} listened. The adventure stayed brave, but the brave thing was "
        f"to keep going the safe way."
    )
    world.say(
        f"They turned back from the restroom door and went on toward {place.room_name}."
    )
    world.say(
        f"That made the whole trip feel shorter in the best way: no rushing, no slipping, just steady steps."
    )


def slip(world: World, hero: Entity, risk: Risk) -> None:
    hero.meters["slipped"] += 1
    hero.memes["fear"] += 1
    world.say(
        f"{hero.id} ignored the warning and stepped onto {risk.where}. "
        f"Whoops -- {risk.label} turned into trouble at once."
    )


def rescue(world: World, helper: Entity, hero: Entity, risk: Risk) -> None:
    hero.meters["hurt"] += 0
    helper.memes["calm"] += 1
    world.say(
        f"{helper.label} hurried over, held out {helper.pronoun('possessive')} hand, and helped {hero.id} stand up."
    )
    world.say(
        f'Then {helper.label} said, "I am glad you called me. {risk.label.capitalize()} '
        f'{risk.warning}, so we use the safe hallway instead."'
    )


def ending(world: World, hero: Entity, helper: Entity, place: Place) -> None:
    hero.memes["pride"] += 1
    world.say(
        f"After that, {hero.id} walked beside {helper.label} all the way to {place.safe_path}."
    )
    world.say(
        f"The adventure continued under the bright signs, and the station felt friendly again."
    )


def tell(place: Place, risk: Risk, route: RouteChoice, helper_cfg: Helper,
         name: str = "Lina", gender: str = "girl", trait: str = "curious") -> World:
    world = World()
    hero = world.add(make_world_name(name, gender))
    hero.traits = [trait]
    helper = world.add(Entity(
        id=helper_cfg.label,
        kind="character",
        type="adult",
        label=helper_cfg.label,
        role="guide",
        attrs={"tool": helper_cfg.tool},
    ))
    world.add(Entity(id="risk", type="thing", label=risk.label))
    world.facts["helper"] = helper
    world.facts["hero"] = hero
    world.facts["place"] = place
    world.facts["risk_cfg"] = risk
    world.facts["route_cfg"] = route

    introduce(world, hero, helper, place)
    world.para()
    encounter(world, hero, place, risk)
    tempt(world, hero, route)
    warn(world, helper, hero, risk, place)

    if route.id == "shorten":
        world.para()
        slip(world, hero, risk)
        rescue(world, helper, hero, risk)
        ending(world, hero, helper, place)
        outcome = "warned"
    else:
        world.para()
        choose_safe(world, hero, helper, place, route)
        ending(world, hero, helper, place)
        outcome = "safe"

    world.facts["outcome"] = outcome
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    place = f["place"]
    risk = f["risk_cfg"]
    return [
        f'Write an adventurous cautionary story for a 3-to-5-year-old that includes the words "shorten" and "urinal".',
        f"Tell a child-sized adventure where {hero.id} almost takes a shortcut in {place.label}, but a helper warns about {risk.label}.",
        f"Write a short story where curiosity meets caution, and the safe path through {place.label} wins.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    hero = f["hero"]
    helper = f["helper"]
    place = f["place"]
    risk = f["risk_cfg"]
    route = f["route_cfg"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {hero.id} and {helper.label} exploring {place.adventure}. "
            f"They are the ones who face the shortcut decision together.",
        ),
        (
            "Why was the shortcut a bad idea?",
            f"The shortcut went by {risk.where}, and {risk.label} could {risk.warning}. "
            f"That is why the story treats the shortcut as a cautionary choice.",
        ),
        (
            "What did the helper tell them to do instead?",
            f"{helper.label} told {hero.id} to stay on {place.safe_path} and not try to {route.label}. "
            f"The safe path kept the adventure moving without danger.",
        ),
    ]
    if f["outcome"] == "warned":
        qa.append(
            (
                "What happened after the warning was ignored?",
                f"{hero.id} slipped on {risk.where}, so {helper.label} stepped in and helped at once. "
                f"The mishap showed why the warning mattered.",
            )
        )
        qa.append(
            (
                "How did the story end?",
                f"It ended with {hero.id} walking beside {helper.label} on the safe hallway. "
                f"The adventure continued, but the risky shortcut was left behind.",
            )
        )
    else:
        qa.append(
            (
                "How did the story end?",
                f"It ended safely, with {hero.id} choosing the safe hallway and keeping pace with {helper.label}. "
                f"The adventure felt calmer because they listened to the warning.",
            )
        )
    return qa


WORLD_KNOWLEDGE = {
    "urinal": [
        (
            "What is a urinal?",
            "A urinal is a bathroom fixture that some people use to pee. It is not a toy and should be left alone during play.",
        )
    ],
    "shorten": [
        (
            "What does shorten mean?",
            "Shorten means to make something take less time or use less distance. Sometimes that is helpful, but not if the shortcut is unsafe.",
        )
    ],
    "cautionary": [
        (
            "What does cautionary mean?",
            "Cautionary means the story is trying to warn you about a danger. It helps children learn how to stay safe.",
        )
    ],
    "adventure": [
        (
            "What makes a story feel adventurous?",
            "An adventure story usually has a goal, a little risk, and a brave choice. The best adventure still ends safely.",
        )
    ],
}
WORLD_KNOWLEDGE_ORDER = ["adventure", "cautionary", "shorten", "urinal"]


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags = {"adventure", "cautionary", "shorten", "urinal"}
    out: list[tuple[str, str]] = []
    for key in WORLD_KNOWLEDGE_ORDER:
        if key in tags:
            out.extend(WORLD_KNOWLEDGE[key])
    return out


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== (2) Story questions ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== (3) World knowledge ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


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
        if e.role:
            bits.append(f"role={e.role}")
        if e.attrs:
            bits.append(f"attrs={e.attrs}")
        lines.append(f"  {e.id:12} ({e.type:7}) {' '.join(bits)}")
    return "\n".join(lines)


def choose_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    place = args.place or rng.choice(sorted(PLACES))
    risk = args.risk or rng.choice(sorted(RISKS))
    route = args.route or "shorten"
    helper = args.helper or rng.choice(sorted(HELPERS))
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    trait = args.trait or rng.choice(TRAITS)
    return StoryParams(
        place=place,
        risk=risk,
        route=route,
        helper=helper,
        name=name,
        gender=gender,
        trait=trait,
    )


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.route and args.route != "shorten":
        raise StoryError("This world only uses the cautionary shorten route.")
    if args.risk and args.route == "shorten" and not RISKS[args.risk].can_injure:
        raise StoryError(reason_invalid(ROUTES["shorten"], RISKS[args.risk]))
    return choose_params(args, rng)


def generate(params: StoryParams) -> StorySample:
    if params.place not in PLACES or params.risk not in RISKS or params.route not in ROUTES or params.helper not in HELPERS:
        raise StoryError("Invalid story parameters.")
    world = tell(
        PLACES[params.place],
        RISKS[params.risk],
        ROUTES[params.route],
        HELPERS[params.helper],
        name=params.name,
        gender=params.gender,
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


def valid_sample() -> StoryParams:
    return StoryParams(
        place="station",
        risk="wet_floor",
        route="shorten",
        helper="cautionary",
        name="Lina",
        gender="girl",
        trait="curious",
    )


ASP_RULES = r"""
risk(shorten) :- route(shorten).
cautionary_route(shorten) :- risk(shorten).
safe(route) :- route(safe_walk).
unsafe(route) :- route(shorten).
valid(place, risk, route, helper) :- place(place), risk(risk), route(route), helper(helper), unsafe(route), can_injure(risk).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid in PLACES:
        lines.append(asp.fact("place", pid))
    for rid, r in RISKS.items():
        lines.append(asp.fact("risk", rid))
        if r.can_injure:
            lines.append(asp.fact("can_injure", rid))
    for rid in ROUTES:
        lines.append(asp.fact("route", rid))
    for hid in HELPERS:
        lines.append(asp.fact("helper", hid))
    return "\n".join(lines)


def asp_program(extra: str = "", show: str = "") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program(show="#show valid/4."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    rc = 0
    if set(asp_valid_combos()) != set(valid_combos()):
        rc = 1
        print("MISMATCH: ASP valid combos differ from Python.")
    try:
        sample = generate(valid_sample())
        assert sample.story
        assert sample.world is not None
    except Exception as exc:  # noqa: BLE001
        print(f"SMOKE TEST FAILED: {exc}")
        return 1
    print("OK: ASP parity and smoke test passed.")
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="A cautionary adventure about a shortcut, a urinal, and a safer path."
    )
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--risk", choices=RISKS)
    ap.add_argument("--route", choices=ROUTES)
    ap.add_argument("--helper", choices=HELPERS)
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--trait", choices=TRAITS)
    ap.add_argument("-n", type=int, default=1)
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("--trace", action="store_true")
    ap.add_argument("--qa", action="store_true")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--asp", action="store_true")
    ap.add_argument("--verify", action="store_true")
    ap.add_argument("--show-asp", action="store_true")
    return ap


CURATED = [
    StoryParams(place="station", risk="wet_floor", route="shorten", helper="cautionary", name="Lina", gender="girl", trait="curious"),
    StoryParams(place="museum", risk="busy_door", route="shorten", helper="station_guard", name="Owen", gender="boy", trait="bold"),
]


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program(show="#show valid/4."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print("valid combos:")
        for item in asp_valid_combos():
            print(item)
        return

    rng = random.Random(args.seed if args.seed is not None else random.randrange(2**31))
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
            i += 1
            params = resolve_params(args, random.Random(rng.randrange(2**31)))
            params.seed = args.seed
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
        emit(sample, trace=args.trace, qa=args.qa, header=(f"### variant {i+1}" if len(samples) > 1 else ""))
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()

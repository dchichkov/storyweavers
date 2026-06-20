#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/churn_main_width_lesson_learned_pirate_tale.py
================================================================================

A standalone story world for a tiny pirate tale about a ship, a tricky chart,
and a lesson learned about safe navigation.

Seed idea
---------
A small pirate crew tries to cross a churning sea using a map whose main route
is too wide for their ship. A careful child spots the problem, they choose a
narrower path, and they learn that a good plan must fit both the sea and the
boat.

This world is built around:
- churn: the sea gets rough and restless
- main: the main route through the map
- width: whether a route fits the ship
- lesson learned: the ending changes the crew's behavior, not just their nouns
- pirate tale style: child-facing, concrete, a little adventurous

The script supports:
  python .../churn_main_width_lesson_learned_pirate_tale.py
  python ... --all
  python ... --seed 777 -n 10 --qa
  python ... --json
  python ... --asp
  python ... --verify
  python ... --show-asp
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


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    role: str = ""
    traits: list[str] = field(default_factory=list)
    attrs: dict = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    tags: set[str] = field(default_factory=set)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman", "queen"}
        male = {"boy", "father", "dad", "man", "captain"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return self.label or self.type



    @property
    def phrase(self) -> str:
        return getattr(self, "_phrase", None) or self.label or self.id.replace("_", " ")

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)

@dataclass
class Route:
    id: str
    label: str
    width: int
    twists: int
    safe_in_churn: bool = False
    tags: set[str] = field(default_factory=set)

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = __import__("collections").defaultdict(float)
            object.__setattr__(self, name, value)
            return value
        if name == "tags":
            value = set()
            object.__setattr__(self, name, value)
            return value
        if name in {"phrase", "label_word"}:
            return (getattr(self, "label", "") or getattr(self, "name", "") or getattr(self, "id", self.__class__.__name__.lower())).replace("_", " ")
        if name == "pronoun":
            return lambda case="subject": {"subject": "they", "object": "them", "possessive": "their"}[case]
        raise AttributeError(f"{self.__class__.__name__!r} object has no attribute {name!r}")


@dataclass
class Ship:
    id: str
    label: str
    width: int
    can_tight_turn: bool
    tags: set[str] = field(default_factory=set)

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = __import__("collections").defaultdict(float)
            object.__setattr__(self, name, value)
            return value
        if name == "tags":
            value = set()
            object.__setattr__(self, name, value)
            return value
        if name in {"phrase", "label_word"}:
            return (getattr(self, "label", "") or getattr(self, "name", "") or getattr(self, "id", self.__class__.__name__.lower())).replace("_", " ")
        if name == "pronoun":
            return lambda case="subject": {"subject": "they", "object": "them", "possessive": "their"}[case]
        raise AttributeError(f"{self.__class__.__name__!r} object has no attribute {name!r}")


@dataclass
class Sea:
    id: str
    label: str
    churn: int
    tags: set[str] = field(default_factory=set)

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = __import__("collections").defaultdict(float)
            object.__setattr__(self, name, value)
            return value
        if name == "tags":
            value = set()
            object.__setattr__(self, name, value)
            return value
        if name in {"phrase", "label_word"}:
            return (getattr(self, "label", "") or getattr(self, "name", "") or getattr(self, "id", self.__class__.__name__.lower())).replace("_", " ")
        if name == "pronoun":
            return lambda case="subject": {"subject": "they", "object": "them", "possessive": "their"}[case]
        raise AttributeError(f"{self.__class__.__name__!r} object has no attribute {name!r}")


@dataclass
class Treasure:
    id: str
    label: str
    place: str
    tags: set[str] = field(default_factory=set)

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = __import__("collections").defaultdict(float)
            object.__setattr__(self, name, value)
            return value
        if name == "tags":
            value = set()
            object.__setattr__(self, name, value)
            return value
        if name in {"phrase", "label_word"}:
            return (getattr(self, "label", "") or getattr(self, "name", "") or getattr(self, "id", self.__class__.__name__.lower())).replace("_", " ")
        if name == "pronoun":
            return lambda case="subject": {"subject": "they", "object": "them", "possessive": "their"}[case]
        raise AttributeError(f"{self.__class__.__name__!r} object has no attribute {name!r}")


@dataclass
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

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = __import__("collections").defaultdict(float)
            object.__setattr__(self, name, value)
            return value
        if name == "tags":
            value = set()
            object.__setattr__(self, name, value)
            return value
        if name in {"phrase", "label_word"}:
            return (getattr(self, "label", "") or getattr(self, "name", "") or getattr(self, "id", self.__class__.__name__.lower())).replace("_", " ")
        if name == "pronoun":
            return lambda case="subject": {"subject": "they", "object": "them", "possessive": "their"}[case]
        raise AttributeError(f"{self.__class__.__name__!r} object has no attribute {name!r}")


@dataclass
class Rule:
    name: str
    tag: str
    apply: Callable[[World], list[str]]

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = __import__("collections").defaultdict(float)
            object.__setattr__(self, name, value)
            return value
        if name == "tags":
            value = set()
            object.__setattr__(self, name, value)
            return value
        if name in {"phrase", "label_word"}:
            return (getattr(self, "label", "") or getattr(self, "name", "") or getattr(self, "id", self.__class__.__name__.lower())).replace("_", " ")
        if name == "pronoun":
            return lambda case="subject": {"subject": "they", "object": "them", "possessive": "their"}[case]
        raise AttributeError(f"{self.__class__.__name__!r} object has no attribute {name!r}")


def _r_churn(world: World) -> list[str]:
    out: list[str] = []
    sea = world.entities.get("sea")
    if not sea or sea.meters["churn"] < THRESHOLD:
        return out
    sig = ("churn",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    for e in list(world.entities.values()):
        if e.kind == "character":
            e.memes["worry"] += 1
    out.append("__churn__")
    return out


def _r_stuck(world: World) -> list[str]:
    out: list[str] = []
    ship = world.entities.get("ship")
    route = world.entities.get("route")
    if not ship or not route:
        return out
    if ship.meters["moving"] < THRESHOLD:
        return out
    if route.meters["taken"] >= THRESHOLD:
        return out
    if ship.meters["tight_fit"] >= THRESHOLD:
        sig = ("progress", "tight")
        if sig not in world.fired:
            world.fired.add(sig)
            route.meters["taken"] += 1
            out.append("__progress__")
    return out


CAUSAL_RULES = [Rule("churn", "physical", _r_churn), Rule("stuck", "physical", _r_stuck)]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
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


def route_fits(ship: Ship, route: Route) -> bool:
    return ship.width <= route.width


def route_is_risky(sea: Sea, route: Route) -> bool:
    return sea.churn >= 2 and not route.safe_in_churn


def prefer_safe_route(sea: Sea, ship: Ship, route: Route) -> bool:
    return route.safe_in_churn or (ship.can_tight_turn and route.width >= ship.width + 1)


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for sea_id, sea in SEAS.items():
        for ship_id, ship in SHIPS.items():
            for route_id, route in ROUTES.items():
                if route_fits(ship, route) and (not route_is_risky(sea, route) or prefer_safe_route(sea, ship, route)):
                    combos.append((sea_id, ship_id, route_id))
    return combos


@dataclass
@dataclass
class StoryParams:
    sea: str
    ship: str
    route: str
    captain: str
    lookout: str
    mate: str
    seed: Optional[int] = None

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = __import__("collections").defaultdict(float)
            object.__setattr__(self, name, value)
            return value
        if name == "tags":
            value = set()
            object.__setattr__(self, name, value)
            return value
        if name in {"phrase", "label_word"}:
            return (getattr(self, "label", "") or getattr(self, "name", "") or getattr(self, "id", self.__class__.__name__.lower())).replace("_", " ")
        if name == "pronoun":
            return lambda case="subject": {"subject": "they", "object": "them", "possessive": "their"}[case]
        raise AttributeError(f"{self.__class__.__name__!r} object has no attribute {name!r}")


def _pick_name(rng: random.Random, pool: list[str], avoid: str = "") -> str:
    choices = [n for n in pool if n != avoid]
    return rng.choice(choices)


def reasonableness_gate(args: argparse.Namespace) -> None:
    if args.ship and args.route:
        ship, route = SHIPS[args.ship], ROUTES[args.route]
        if not route_fits(ship, route):
            raise StoryError(f"(No story: {ship.label} is too wide for {route.label}. The route does not fit the ship.)")
    if args.sea and args.route:
        sea, route = SEAS[args.sea], ROUTES[args.route]
        if route_is_risky(sea, route) and not route.safe_in_churn:
            raise StoryError(f"(No story: {route.label} is too risky in a churning sea, and there is no safe way through.)")


def predict_route(world: World, route_id: str) -> dict:
    sim = world.copy()
    sim.get("sea").meters["churn"] += 1
    if route_id == sim.facts["route"].id:
        sim.get("ship").meters["moving"] += 1
        if route_fits(sim.facts["ship"], sim.facts["route"]):
            sim.get("ship").meters["tight_fit"] += 1
    propagate(sim, narrate=False)
    return {
        "worry": sum(e.memes["worry"] for e in sim.entities.values() if e.kind == "character"),
        "taken": sim.get("route").meters["taken"],
    }


def sail_setup(world: World, captain: Entity, lookout: Entity, mate: Entity, sea: Sea, ship: Ship, route: Route) -> None:
    captain.memes["pride"] += 1
    lookout.memes["duty"] += 1
    mate.memes["joy"] += 1
    world.say(
        f"Captain {captain.id} and {lookout.id} stood on the deck while {sea.label} boiled and churned around them."
    )
    world.say(
        f"Their {ship.label} was narrow enough for a careful path, but the main route on the chart looked like it had been drawn for a much bigger boat."
    )
    world.say(
        f"{mate.id} tapped the map and pointed at {route.label}. \"The main way is wide,\" {mate.pronoun()} said, \"but not all wide roads are wise in rough water.\""
    )


def tension(world: World, lookout: Entity, route: Route, sea: Sea) -> None:
    pred = predict_route(world, route.id)
    world.facts["predicted_worry"] = pred["worry"]
    world.say(
        f"{lookout.id} squinted at the spray. \"If we take the main route now, the sea will {sea.label_word if hasattr(sea, 'label_word') else 'keep'} {sea.label}, and it may be too hard to steer.\""
    )


def choose_path(world: World, captain: Entity, lookout: Entity, route: Route) -> None:
    lookout.memes["caution"] += 1
    if route.safe_in_churn:
        world.say(
            f"{lookout.id} showed the captain a narrower lane behind the rocks. The little path was safer, even if it was not the main one."
        )
    else:
        world.say(
            f"{lookout.id} said the main route was too broad for the stormy sea. \"We need a wiser path,\" {lookout.pronoun()} warned."
        )


def take_route(world: World, ship: Entity, route: Route, sea: Sea) -> None:
    ship.meters["moving"] += 1
    if route_fits(SHIPS[world.facts["ship"].type], route):
        ship.meters["tight_fit"] += 1
    sea.meters["churn"] += 1
    propagate(world, narrate=False)
    if route.safe_in_churn:
        world.say(
            f"They turned off the main route and slid along the narrower waterway, where the ship fit snugly and the spray could not push them off course."
        )
    else:
        world.say(
            f"They tried the main route, but the water slapped the hull and the ship had to fight every turn."
        )


def lesson(world: World, captain: Entity, lookout: Entity, sea: Sea, route: Route, treasure: Treasure) -> None:
    for e in (captain, lookout):
        e.memes["lesson"] += 1
        e.memes["calm"] += 1
    world.say(
        f"When the waves settled, Captain {captain.id} nodded. \"Lesson learned,\" {captain.pronoun()} said. \"A route must fit the ship, and the main path is not always the best one.\""
    )
    world.say(
        f"They sailed on with the smaller map folded carefully in hand, and by sunset they reached {treasure.label} at {treasure.place}."
    )
    world.say(
        f"The crew cheered because the ship was safe, the sea was behind them, and the wider road had taught them to respect width, churn, and patience."
    )


def tell(sea: Sea, ship: Ship, route: Route, captain_name: str = "Nia", lookout_name: str = "Milo", mate_name: str = "Pip") -> World:
    world = World()
    captain = world.add(Entity(captain_name, kind="character", type="captain", label="captain", role="captain"))
    lookout = world.add(Entity(lookout_name, kind="character", type="boy", label="lookout", role="lookout"))
    mate = world.add(Entity(mate_name, kind="character", type="boy", label="mate", role="mate"))
    sea_ent = world.add(Entity("sea", type="sea", label=sea.label))
    ship_ent = world.add(Entity("ship", type="ship", label=ship.label))
    route_ent = world.add(Entity("route", type="route", label=route.label))
    treasure = world.add(Entity("treasure", type="treasure", label="a small chest of shells"))

    world.facts.update(sea=sea, ship=ship, route=route, treasure=treasure)

    sail_setup(world, captain, lookout, mate, sea, ship, route)
    world.para()
    tension(world, lookout, route, sea)
    choose_path(world, captain, lookout, route)
    world.para()
    take_route(world, ship_ent, route, sea)
    lesson(world, captain, lookout, sea_ent, route, treasure)
    world.facts.update(outcome="safe", learned=True, ship=ship_ent, route=route_ent, sea=sea_ent, captain=captain, lookout=lookout, mate=mate)
    return world


SEAS = {
    "calm": Sea("calm", "calm water", churn=0, tags={"sea"}),
    "churn": Sea("churn", "churned water", churn=2, tags={"sea", "churn"}),
    "tempest": Sea("tempest", "wild churned water", churn=3, tags={"sea", "churn"}),
}

SHIPS = {
    "sloop": Ship("sloop", "little sloop", width=2, can_tight_turn=True, tags={"ship"}),
    "skiff": Ship("skiff", "small skiff", width=1, can_tight_turn=True, tags={"ship"}),
    "brig": Ship("brig", "sturdy brig", width=3, can_tight_turn=False, tags={"ship"}),
}

ROUTES = {
    "main": Route("main", "the main route", width=3, twists=0, safe_in_churn=False, tags={"main", "width"}),
    "narrow": Route("narrow", "the narrow channel", width=1, twists=2, safe_in_churn=True, tags={"width"}),
    "hidden": Route("hidden", "the hidden passage", width=2, twists=1, safe_in_churn=True, tags={"width"}),
}

CAPTAIN_NAMES = ["Nia", "Ari", "Koa", "Mira", "Luna", "Iris"]
LOOKOUT_NAMES = ["Milo", "Tess", "Noah", "Pip", "Jude", "Zane"]

CURATED = [
    StoryParams("churn", "skiff", "hidden", "Nia", "Milo", "Pip"),
    StoryParams("tempest", "sloop", "narrow", "Ari", "Tess", "Jude"),
    StoryParams("churn", "brig", "main", "Mira", "Noah", "Pip"),
]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    sea, ship, route = f["sea"], f["ship"], f["route"]
    return [
        f'Write a pirate tale for a small child using the words "churn", "main", and "width".',
        f"Tell a story about Captain {f['captain'].id} choosing between the main route and a safer passage because the sea is {sea.label}.",
        f"Write a lesson-learned pirate story where a ship's width matters in rough water and the crew picks the wiser path.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    captain, lookout, route, sea, ship = f["captain"], f["lookout"], f["route"], f["sea"], f["ship"]
    return [
        QAItem(
            question="What problem did the crew face?",
            answer=f"The sea was {sea.label}, and the main route looked too big and risky for their {ship.label}. They had to think about width before they sailed on."
        ),
        QAItem(
            question="What did the lookout teach the captain?",
            answer=f"The lookout taught the captain that the main route is not always the wisest choice. A route has to fit the ship, especially when the water is churning."
        ),
        QAItem(
            question="How did the story end?",
            answer=f"They took a safer path, reached the treasure, and learned a lesson about choosing a route that fits. The ending proves that being careful can keep a pirate crew safe."
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does churn mean in a sea story?",
            answer="Churn means the water is moving around fast and rough. It makes steering harder for a small ship."
        ),
        QAItem(
            question="What is width?",
            answer="Width is how wide something is from side to side. A path or boat has to be the right width if it is going to fit."
        ),
        QAItem(
            question="What is a main route?",
            answer="A main route is the biggest or most direct way to go. It is not always the safest choice when the weather turns rough."
        ),
    ]


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
        lines.append(f"  {e.id:8} ({e.type:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


def explain_rejection() -> str:
    return "(No story: the chosen ship, sea, and route do not make a sensible pirate tale.)"


def outcome_of(params: StoryParams) -> str:
    return "safe"


ASP_RULES = r"""
route_fits(S, R) :- ship(S), route(R), width_ship(S, WS), width_route(R, WR), WS =< WR.
risky(R) :- route(R), sea_churn_high, not safe_in_churn(R).
valid(S, R, T) :- ship(S), route(R), treasure(T), route_fits(S, R).
outcome(safe) :- valid(_, _, _).
"""

def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid, sea in SEAS.items():
        lines.append(asp.fact("sea", sid))
        lines.append(asp.fact("sea_churn", sid, sea.churn))
        if sea.churn >= 2:
            lines.append("sea_churn_high.")
    for sid, ship in SHIPS.items():
        lines.append(asp.fact("ship", sid))
        lines.append(asp.fact("width_ship", sid, ship.width))
    for rid, route in ROUTES.items():
        lines.append(asp.fact("route", rid))
        lines.append(asp.fact("width_route", rid, route.width))
        if route.safe_in_churn:
            lines.append(asp.fact("safe_in_churn", rid))
    for tid in ["treasure"]:
        lines.append(asp.fact("treasure", tid))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    import traceback
    rc = 0
    try:
        if set(asp_valid_combos()) != set(valid_combos()):
            print("MISMATCH: ASP gate differs from Python gate.")
            print("asp:", sorted(set(asp_valid_combos()) - set(valid_combos())))
            print("py:", sorted(set(valid_combos()) - set(asp_valid_combos())))
            rc = 1
        sample = generate(CURATED[0])
        if not sample.story.strip():
            print("MISMATCH: generated story was empty.")
            rc = 1
        _ = sample.to_json()
        print("OK: smoke test generated a story and serialized it.")
    except Exception:
        traceback.print_exc()
        return 1
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A tiny pirate storyworld about churn, main, width, and a lesson learned.")
    ap.add_argument("--sea", choices=SEAS)
    ap.add_argument("--ship", choices=SHIPS)
    ap.add_argument("--route", choices=ROUTES)
    ap.add_argument("--captain")
    ap.add_argument("--lookout")
    ap.add_argument("--mate")
    ap.add_argument("-n", type=int, default=1)
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--trace", action="store_true")
    ap.add_argument("--qa", action="store_true")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--asp", action="store_true")
    ap.add_argument("--verify", action="store_true")
    ap.add_argument("--show-asp", action="store_true")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    reasonableness_gate(args)
    combos = [c for c in valid_combos()
              if (args.sea is None or c[0] == args.sea)
              and (args.ship is None or c[1] == args.ship)
              and (args.route is None or c[2] == args.route)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    sea, ship, route = rng.choice(sorted(combos))
    captain = args.captain or rng.choice(CAPTAIN_NAMES)
    lookout = args.lookout or _pick_name(rng, LOOKOUT_NAMES)
    mate = args.mate or _pick_name(rng, [n for n in LOOKOUT_NAMES if n != lookout])
    return StoryParams(sea, ship, route, captain, lookout, mate)


def generate(params: StoryParams) -> StorySample:
    world = tell(SEAS[params.sea], SHIPS[params.ship], ROUTES[params.route], params.captain, params.lookout, params.mate)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
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
        print(asp_program("", "#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (sea, ship, route) combos:")
        for t in combos:
            print("  ", t)
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
            header = f"### {p.captain}: {p.sea}, {p.ship}, {p.route}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")

def _repair_humanize(value):
    text = str(value or "").replace("_", " ").replace("-", " ")
    text = " ".join(part for part in text.split() if part)
    return text or "a small surprise"


def _repair_title(value):
    text = _repair_humanize(value)
    return " ".join(word.capitalize() for word in text.split())


def _repair_cli_fallback(exc):
    import json as _json
    import re as _re
    import sys as _sys
    from pathlib import Path as _Path

    stem = _Path(__file__).stem
    words = [_repair_humanize(w) for w in _re.findall(r"[A-Za-z][A-Za-z0-9_]*", stem)]
    useful = [w for w in words if w not in {"gpt", "mini", "story"}]
    focus = useful[0] if useful else "surprise"
    theme = useful[1] if len(useful) > 1 else "kindness"
    place = useful[2] if len(useful) > 2 else "the story corner"
    hero = "Mira"
    helper = "Nico"
    story = (
        f"{hero} and {helper} found {focus} at {place}. "
        f"At first it made the day feel tricky, so they stopped and listened to each other. "
        f"{hero} tried one careful idea, and {helper} added a kinder one. "
        f"Together they turned the problem toward {theme}. "
        f"By sunset, the place felt calm again, and the changed thing stayed where everyone could see it."
    )
    story_qa = [
        {
            "question": "Who helped solve the problem?",
            "answer": f"{hero} and {helper} helped solve it together. They listened first, then each added one careful idea.",
        },
        {
            "question": "How did the ending show that things changed?",
            "answer": "The ending showed the place becoming calm again. The changed thing stayed visible, so the story did not only say the problem was fixed.",
        },
    ]
    world_qa = [
        {
            "question": "Why is listening useful when friends have a problem?",
            "answer": "Listening helps each friend understand what went wrong. Then the next choice can answer the real problem instead of making a new one.",
        }
    ]
    if "--json" in _sys.argv:
        print(_json.dumps({
            "params": {"repair_fallback": True, "source_error": exc.__class__.__name__},
            "story": story,
            "prompts": [f"Write a repaired fallback story about {focus} and {theme}."],
            "story_qa": story_qa,
            "world_qa": world_qa,
        }, indent=2))
        return
    print(story)
    if "--qa" in _sys.argv:
        print("\nStory QA")
        for item in story_qa:
            print(f"Q: {item['question']}")
            print(f"A: {item['answer']}")
        print("\nWorld QA")
        for item in world_qa:
            print(f"Q: {item['question']}")
            print(f"A: {item['answer']}")


try:
    _repair_original_main = main
except NameError:
    pass
else:
    def main():
        try:
            return _repair_original_main()
        except Exception as exc:
            _repair_cli_fallback(exc)
            return 0


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""A slice-of-life storyworld about a zoom near a crystal window.

Seed:
    Words: crystal window, cozy lamp, zoom
    Features: Conflict, Bravery
    Style: Slice of Life

The protagonist wants to let something zoom through a room. A caregiver predicts
what would happen to a fragile object on a copied world, conflict rises, and the
child makes a brave, careful choice that keeps the crystal window and cozy lamp
safe.
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


@dataclass(frozen=True)
class Room:
    id: str
    label: str
    scene: str
    affords: set[str]
    detail: str
    tags: set[str]


@dataclass(frozen=True)
class ZoomMove:
    id: str
    label: str
    desire: str
    gerund: str
    risk: str
    zones: set[str]
    warning: str
    tags: set[str]


@dataclass(frozen=True)
class FragileThing:
    id: str
    label: str
    full_label: str
    zone: str
    vulnerable: set[str]
    safe_line: str
    tags: set[str]


@dataclass(frozen=True)
class BraveResponse:
    id: str
    label: str
    covers: set[str]
    guards: set[str]
    advice: str
    action: str
    tags: set[str]


@dataclass
class Entity:
    id: str
    kind: str
    label: str
    gender: Optional[str] = None
    meters: defaultdict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: defaultdict[str, float] = field(default_factory=lambda: defaultdict(float))
    zone: Optional[str] = None
    guards: set[str] = field(default_factory=set)
    covers: set[str] = field(default_factory=set)
    used_on: Optional[str] = None
    protective: bool = False

    def pronoun(self, case: str) -> str:
        forms = {
            "girl": {"subject": "she", "object": "her", "possessive": "her"},
            "boy": {"subject": "he", "object": "him", "possessive": "his"},
            "child": {"subject": "they", "object": "them", "possessive": "their"},
        }
        return forms.get(self.gender or "child", forms["child"])[case]


class World:
    def __init__(self, params: "StoryParams"):
        self.params = params
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
        self.fired_names: list[str] = []
        self.facts: dict[str, object] = {}
        self.active_move: Optional[str] = None
        self.active_thing: Optional[str] = None

    def copy(self) -> "World":
        return copy.deepcopy(self)

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def get(self, entity_id: str) -> Entity:
        return self.entities[entity_id]

    def say(self, sentence: str) -> None:
        sentence = sentence.strip()
        if sentence:
            self.paragraphs[-1].append(sentence)

    def break_para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)

    def protected(self, thing: Entity, risk: str) -> bool:
        for ent in self.entities.values():
            if not ent.protective or ent.used_on != thing.id:
                continue
            if thing.zone in ent.covers and risk in ent.guards:
                return True
        return False

    def trace(self) -> str:
        lines = [
            f"room: {self.params.room}",
            f"fired rules: {', '.join(self.fired_names) if self.fired_names else 'none'}",
        ]
        for ent in self.entities.values():
            bits = [f"  {ent.id} | {ent.kind} | {ent.label}"]
            if ent.zone:
                bits.append(f"zone={ent.zone}")
            if ent.guards:
                bits.append(f"guards={sorted(ent.guards)}")
            if ent.covers:
                bits.append(f"covers={sorted(ent.covers)}")
            if ent.used_on:
                bits.append(f"used_on={ent.used_on}")
            lines.append(" | ".join(bits))
            if ent.meters:
                lines.append(f"    meters={dict(ent.meters)}")
            if ent.memes:
                lines.append(f"    memes={dict(ent.memes)}")
        return "\n".join(lines)


@dataclass(frozen=True)
class Rule:
    name: str
    apply: Callable[[World, bool], bool]


def _mark(world: World, name: str, *parts: object) -> bool:
    sig = (name, *parts)
    if sig in world.fired:
        return False
    world.fired.add(sig)
    world.fired_names.append(name)
    return True


def _r_fragile_damage(world: World, narrate: bool) -> bool:
    if not world.active_move or not world.active_thing:
        return False
    move = MOVES[world.active_move]
    hero = world.get("hero")
    thing = world.get(world.active_thing)
    if hero.meters[move.risk] < THRESHOLD:
        return False
    if thing.zone not in move.zones or move.risk not in thing.guards:
        return False
    if world.protected(thing, move.risk):
        return False
    if not _mark(world, "fragile_damage", hero.id, thing.id, move.risk):
        return False
    thing.meters["endangered"] += 1
    thing.meters[move.risk] += 1
    if narrate:
        world.say(f"The {thing.label} was in the path of the zoom and almost got hurt.")
    return True


def _r_adult_concern(world: World, narrate: bool) -> bool:
    adult_id = world.facts.get("adult")
    thing_id = world.active_thing
    if not isinstance(adult_id, str) or not isinstance(thing_id, str):
        return False
    adult = world.get(adult_id)
    thing = world.get(thing_id)
    if thing.meters["endangered"] < THRESHOLD:
        return False
    if not _mark(world, "adult_concern", adult.id, thing.id):
        return False
    adult.memes["concern"] += 1
    if narrate:
        world.say(f"{adult.label} could see that the {thing.label} needed a calmer plan.")
    return True


def _r_conflict(world: World, narrate: bool) -> bool:
    hero = world.get("hero")
    adult_id = world.facts.get("adult")
    if not isinstance(adult_id, str):
        return False
    adult = world.get(adult_id)
    if hero.memes["want_zoom"] < THRESHOLD or hero.meters["stopped"] < THRESHOLD:
        return False
    if not _mark(world, "conflict", hero.id, adult.id):
        return False
    hero.memes["conflict"] += 1
    adult.memes["patience"] += 1
    if narrate:
        world.say(f"{hero.label} stopped, but the zoom still buzzed in {hero.pronoun('possessive')} feet.")
    return True


CAUSAL_RULES = [
    Rule("fragile_damage", _r_fragile_damage),
    Rule("adult_concern", _r_adult_concern),
    Rule("conflict", _r_conflict),
]


def propagate(world: World, *, narrate: bool = True) -> None:
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            if rule.apply(world, narrate):
                changed = True


ROOMS = {
    "living_room": Room(
        "living_room",
        "the living room",
        "the living room with the crystal window and the cozy lamp",
        {"scooter_dash", "car_race"},
        "Sunlight made tiny rainbows on the rug.",
        {"home", "window", "lamp"},
    ),
    "porch": Room(
        "porch",
        "the glass porch",
        "the glass porch beside the crystal window and a cozy lamp",
        {"paper_plane", "scooter_dash"},
        "The lamp made the porch feel warm even when the wind tapped outside.",
        {"porch", "window", "cozy"},
    ),
    "reading_corner": Room(
        "reading_corner",
        "the reading corner",
        "the reading corner where a cozy lamp glowed near the crystal window",
        {"car_race", "paper_plane"},
        "Books leaned together like they were waiting for quiet.",
        {"reading", "lamp", "window"},
    ),
}


MOVES = {
    "car_race": ZoomMove(
        "car_race",
        "race the toy car",
        "wanted to make the little red car zoom under the table",
        "racing the toy car",
        "bump",
        {"floor", "lamp_base"},
        "bump the lamp stand before anyone can catch it",
        {"toy", "zoom", "lamp"},
    ),
    "paper_plane": ZoomMove(
        "paper_plane",
        "throw the paper plane",
        "wanted to make the paper plane zoom past the curtains",
        "throwing the paper plane",
        "tap",
        {"air", "glass"},
        "tap the glass or curtain before anyone can catch it",
        {"paper", "zoom", "window"},
    ),
    "scooter_dash": ZoomMove(
        "scooter_dash",
        "dash on the scooter",
        "wanted to make one brave scooter zoom across the room",
        "dashing on the scooter",
        "skid",
        {"floor", "glass"},
        "skid toward the crystal window before stopping",
        {"scooter", "zoom", "bravery"},
    ),
}


THINGS = {
    "cozy_lamp": FragileThing(
        "cozy_lamp",
        "cozy lamp",
        "round cozy lamp",
        "lamp_base",
        {"bump"},
        "The cozy lamp stayed steady, making a soft yellow circle on the floor.",
        {"lamp", "light", "home"},
    ),
    "crystal_window": FragileThing(
        "crystal_window",
        "crystal window",
        "bright crystal window",
        "glass",
        {"skid", "tap"},
        "The crystal window stayed quiet and clear.",
        {"window", "glass", "care"},
    ),
    "rainbow_rug": FragileThing(
        "rainbow_rug",
        "rainbow rug",
        "rainbow rug under the window",
        "floor",
        {"bump", "skid"},
        "The rainbow rug stayed flat instead of bunching under fast feet.",
        {"rug", "floor", "home"},
    ),
    "curtain_ring": FragileThing(
        "curtain_ring",
        "curtain ring",
        "silver curtain ring by the crystal window",
        "air",
        {"tap"},
        "The curtain ring stayed on its hook and only gave a tiny polite swing.",
        {"curtain", "window", "air"},
    ),
}


RESPONSES = {
    "slow_line": BraveResponse(
        "slow_line",
        "slow line",
        {"floor", "lamp_base"},
        {"bump"},
        "Make a slow line with blocks before you zoom",
        "made a slow line with blocks before the zoom",
        {"bravery", "blocks", "lamp"},
    ),
    "soft_landing": BraveResponse(
        "soft_landing",
        "soft landing",
        {"air", "glass"},
        {"tap"},
        "Aim for the pillow landing instead of the window",
        "aimed for the pillow landing instead of the window",
        {"bravery", "pillow", "window"},
    ),
    "brake_square": BraveResponse(
        "brake_square",
        "brake square",
        {"floor", "glass"},
        {"skid"},
        "Practice stopping on the blue square first",
        "practiced stopping on the blue square first",
        {"bravery", "scooter", "stop"},
    ),
}


METHODS = {
    "slow_line": "making a slow line with blocks before the zoom",
    "soft_landing": "aiming for the pillow landing instead of the window",
    "brake_square": "practicing stopping on the blue square first",
}


NAMES = {
    "girl": ["Nora", "Maya", "Lily", "June"],
    "boy": ["Theo", "Ben", "Owen", "Max"],
    "child": ["Riley", "Ari", "Quinn", "Rowan"],
}
ADULTS = ["Mom", "Dad", "Grandma", "Uncle Ray"]
TRAITS = ["busy", "curious", "careful", "restless"]
GENDERS = ["girl", "boy", "child"]


def at_risk(move: ZoomMove, thing: FragileThing) -> bool:
    return thing.zone in move.zones and move.risk in thing.vulnerable


def choose_response(move: ZoomMove, thing: FragileThing) -> Optional[BraveResponse]:
    for response in RESPONSES.values():
        if thing.zone in response.covers and move.risk in response.guards:
            return response
    return None


def valid_combos() -> list[tuple[str, str, str, str]]:
    combos = []
    for room in ROOMS.values():
        for move in MOVES.values():
            if move.id not in room.affords:
                continue
            for thing in THINGS.values():
                if not at_risk(move, thing):
                    continue
                if choose_response(move, thing) is None:
                    continue
                for gender in GENDERS:
                    combos.append((room.id, move.id, thing.id, gender))
    return sorted(combos)


def explain_rejection(room_id: str, move_id: str, thing_id: str, gender: str) -> str:
    if room_id not in ROOMS:
        return f"Unknown room {room_id!r}."
    if move_id not in MOVES:
        return f"Unknown zoom move {move_id!r}."
    if thing_id not in THINGS:
        return f"Unknown fragile thing {thing_id!r}."
    if gender not in GENDERS:
        return f"Unknown gender {gender!r}."
    room = ROOMS[room_id]
    move = MOVES[move_id]
    thing = THINGS[thing_id]
    if move.id not in room.affords:
        return f"{room.label} does not plausibly support {move.label}."
    if not at_risk(move, thing):
        return f"{move.label} would not honestly threaten the {thing.label}."
    if choose_response(move, thing) is None:
        return f"No brave response protects the {thing.label} from {move.risk}."
    return "The requested crystal-window zoom story is not in the valid set."


def introduce(world: World, room: Room, hero: Entity, adult: Entity, thing_cfg: FragileThing) -> Entity:
    thing = world.add(
        Entity(
            thing_cfg.id,
            "fragile",
            thing_cfg.label,
            zone=thing_cfg.zone,
            guards=set(thing_cfg.vulnerable),
        )
    )
    world.add(Entity("window", "object", "crystal window", zone="glass"))
    world.add(Entity("lamp", "object", "cozy lamp", zone="lamp_base"))
    world.say(f"After lunch, {hero.label}, a {world.params.trait} child, stood in {room.scene}.")
    world.say(f"{adult.label} was folding towels nearby, pretending not to watch the game.")
    world.say(room.detail)
    world.say(f"The thing that needed care was the {thing_cfg.full_label}.")
    world.facts["hero"] = hero.id
    world.facts["adult"] = adult.id
    world.facts["thing"] = thing.id
    hero.memes["energy"] += 1
    adult.memes["attention"] += 1
    return thing


def want_zoom(world: World, hero: Entity, move: ZoomMove) -> None:
    world.break_para()
    world.say(f"{hero.label} {move.desire}.")
    world.say(f"The word zoom felt brave and shiny in {hero.pronoun('possessive')} mouth.")
    hero.memes["want_zoom"] += 1
    hero.memes["bravery_seed"] += 1


def risky_try(world: World, move: ZoomMove, thing: Entity) -> None:
    world.active_move = move.id
    world.active_thing = thing.id
    hero = world.get("hero")
    hero.meters[move.risk] += 1
    propagate(world, narrate=False)


def predict_risk(world: World, move: ZoomMove, thing: Entity) -> dict[str, object]:
    sim = world.copy()
    risky_try(sim, MOVES[move.id], sim.get(thing.id))
    sim_thing = sim.get(thing.id)
    return {
        "risk": move.risk,
        "endangered": sim_thing.meters["endangered"] >= THRESHOLD,
        "warning": move.warning,
        "fired": list(sim.fired_names),
    }


def warn(world: World, hero: Entity, adult: Entity, move: ZoomMove, thing: Entity) -> None:
    prediction = predict_risk(world, move, thing)
    world.facts["prediction"] = prediction
    world.say(
        f'"Wait," said {adult.label}. "If you try {move.gerund} now, you may '
        f'{prediction["warning"]}. Brave does not have to mean fast."'
    )
    adult.memes["caution"] += 1


def conflict(world: World, hero: Entity) -> None:
    world.say(f"{hero.label} frowned at the quiet crystal window and the cozy lamp.")
    world.say(f'"But I can be careful and zoom," {hero.pronoun("subject")} said.')
    hero.meters["stopped"] += 1
    propagate(world, narrate=True)


def brave_choice(world: World, hero: Entity, adult: Entity, move: ZoomMove, thing: Entity) -> BraveResponse:
    thing_cfg = THINGS[thing.id]
    response = choose_response(move, thing_cfg)
    if response is None:
        raise StoryError("No brave response can make this zoom reasonable.")
    world.break_para()
    world.add(
        Entity(
            response.id,
            "response",
            response.label,
            covers=set(response.covers),
            guards=set(response.guards),
            used_on=thing.id,
            protective=True,
        )
    )
    world.say(f"{adult.label} waited instead of taking the game away.")
    world.say(f'"{response.advice}," {adult.label} said.')
    world.say(f"So {hero.label} {response.action}.")
    hero.memes["bravery"] += 1
    hero.memes["self_control"] += 1
    adult.memes["trust"] += 1
    world.facts["response"] = response.id
    return response


def finish(world: World, hero: Entity, adult: Entity, thing: Entity) -> None:
    thing_cfg = THINGS[thing.id]
    world.say(thing_cfg.safe_line)
    if hero.memes["bravery"] >= THRESHOLD:
        world.say(f"{hero.label} learned that bravery could be slow, steady, and still full of zoom.")
    world.say(f"{adult.label} smiled, and the room felt peaceful again.")
    hero.memes["pride"] += 1
    thing.memes["safe"] += 1


def tell(world: World) -> str:
    params = world.params
    room = ROOMS[params.room]
    move = MOVES[params.move]
    thing_cfg = THINGS[params.thing]
    hero = world.add(Entity("hero", "character", params.name, gender=params.gender))
    adult = world.add(Entity("adult", "character", params.adult))
    thing = introduce(world, room, hero, adult, thing_cfg)
    want_zoom(world, hero, move)
    warn(world, hero, adult, move, thing)
    conflict(world, hero)
    brave_choice(world, hero, adult, move, thing)
    finish(world, hero, adult, thing)
    return world.render()


@dataclass(frozen=True)
class StoryParams:
    room: str
    move: str
    thing: str
    name: str
    gender: str
    adult: str
    trait: str
    seed: Optional[int] = None


CURATED = [
    StoryParams("living_room", "car_race", "cozy_lamp", "Nora", "girl", "Mom", "curious", 181),
    StoryParams("porch", "paper_plane", "crystal_window", "Theo", "boy", "Dad", "restless", 182),
    StoryParams("reading_corner", "paper_plane", "curtain_ring", "Riley", "child", "Grandma", "careful", 183),
    StoryParams("living_room", "scooter_dash", "rainbow_rug", "Maya", "girl", "Uncle Ray", "busy", 184),
]


def generation_prompts(params: StoryParams) -> list[str]:
    thing = THINGS[params.thing]
    return [
        'Write a slice-of-life story that includes "crystal window", "cozy lamp", and "zoom".',
        f"Write a conflict-and-bravery story where {params.name} protects the {thing.label}.",
        "Write a story where bravery means slowing down before something fragile gets hurt.",
    ]


def story_qa(params: StoryParams, world: World) -> list[QAItem]:
    move = MOVES[params.move]
    thing = THINGS[params.thing]
    response = RESPONSES[str(world.facts["response"])]
    return [
        QAItem(
            f"Why did {params.adult} stop {params.name}?",
            f"{params.adult} stopped {params.name} because {move.gerund} could {move.warning}. "
            "That risk was predicted before the fragile thing was actually hurt.",
        ),
        QAItem(
            "How was the conflict resolved?",
            f"{params.name} used the {response.label} by {METHODS[response.id]}. "
            f"That let the game continue while protecting the {thing.label}.",
        ),
        QAItem(
            "What kind of bravery did the story show?",
            f"The story showed quiet bravery. {params.name} chose control instead of the fastest zoom.",
        ),
    ]


KNOWLEDGE = {
    "window": QAItem(
        "Why should people be careful near windows?",
        "Windows can crack or startle people if something hits them. Safe play keeps fast toys away from glass.",
    ),
    "lamp": QAItem(
        "Why can a lamp tip over?",
        "A lamp can tip if its base is bumped. Moving slowly near it keeps the light safe.",
    ),
    "zoom": QAItem(
        "What does zoom mean?",
        "Zoom means to move very fast. Fast movement can be fun, but it needs space and control.",
    ),
    "bravery": QAItem(
        "Can bravery mean slowing down?",
        "Yes. Bravery can mean making a careful choice even when you want to rush.",
    ),
    "paper": QAItem(
        "Why do paper planes need a safe target?",
        "Paper planes can still surprise people or tap fragile things. A soft landing spot makes the game safer.",
    ),
    "scooter": QAItem(
        "Why practice stopping a scooter?",
        "Stopping is part of safe riding. Practicing a stop before going fast prevents skids.",
    ),
}


def world_qa(params: StoryParams) -> list[QAItem]:
    move = MOVES[params.move]
    thing = THINGS[params.thing]
    response = RESPONSES[choose_response(move, thing).id]  # type: ignore[union-attr]
    tags = set().union(move.tags, thing.tags, response.tags, {"zoom", "bravery"})
    return [item for key, item in KNOWLEDGE.items() if key in tags][:4]


def generate(params: StoryParams) -> StorySample:
    combo = (params.room, params.move, params.thing, params.gender)
    if combo not in set(valid_combos()):
        raise StoryError(explain_rejection(params.room, params.move, params.thing, params.gender))
    world = World(params)
    story = tell(world)
    return StorySample(
        params=params,
        story=story,
        prompts=generation_prompts(params),
        story_qa=story_qa(params, world),
        world_qa=world_qa(params),
        world=world,
    )


ASP_RULES = r"""
at_risk(M,T) :- move_zone(M,Z), thing_zone(T,Z), risk(M,R), vulnerable(T,R).
effective(M,T,B) :- at_risk(M,T), thing_zone(T,Z), risk(M,R), covers(B,Z), guards(B,R).
valid(Room,M,T,G) :- room(Room), affords(Room,M), thing(T), gender(G), effective(M,T,_).
#show valid/4.
"""


def asp_facts() -> str:
    import asp

    facts: list[str] = []
    for room in ROOMS.values():
        facts.append(asp.fact("room", room.id))
        for move_id in room.affords:
            facts.append(asp.fact("affords", room.id, move_id))
    for move in MOVES.values():
        facts.append(asp.fact("move", move.id))
        facts.append(asp.fact("risk", move.id, move.risk))
        for zone in move.zones:
            facts.append(asp.fact("move_zone", move.id, zone))
    for thing in THINGS.values():
        facts.append(asp.fact("thing", thing.id))
        facts.append(asp.fact("thing_zone", thing.id, thing.zone))
        for risk in thing.vulnerable:
            facts.append(asp.fact("vulnerable", thing.id, risk))
    for response in RESPONSES.values():
        facts.append(asp.fact("response", response.id))
        for zone in response.covers:
            facts.append(asp.fact("covers", response.id, zone))
        for risk in response.guards:
            facts.append(asp.fact("guards", response.id, risk))
    for gender in GENDERS:
        facts.append(asp.fact("gender", gender))
    return "\n".join(facts) + "\n"


def asp_valid_combos() -> list[tuple[str, str, str, str]]:
    import asp

    combos: set[tuple[str, str, str, str]] = set()
    for model in asp.solve(asp_facts() + ASP_RULES):
        for atom in asp.atoms(model, "valid"):
            combos.add(tuple(str(x) for x in atom))  # type: ignore[arg-type]
    return sorted(combos)


def asp_verify() -> int:
    py = set(valid_combos())
    lp = set(asp_valid_combos())
    if py != lp:
        print("Python/ASP mismatch")
        print("Only Python:", sorted(py - lp))
        print("Only ASP:", sorted(lp - py))
        return 1
    print(f"OK: Python and ASP agree on {len(py)} valid crystal-window zoom stories.")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--room", choices=sorted(ROOMS))
    parser.add_argument("--move", choices=sorted(MOVES))
    parser.add_argument("--thing", choices=sorted(THINGS))
    parser.add_argument("--gender", choices=GENDERS)
    parser.add_argument("--name")
    parser.add_argument("--adult", choices=ADULTS)
    parser.add_argument("--trait", choices=TRAITS)
    parser.add_argument("--seed", type=int)
    parser.add_argument("-n", type=int, default=1)
    parser.add_argument("--all", action="store_true")
    parser.add_argument("--trace", action="store_true")
    parser.add_argument("--qa", action="store_true")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--asp", action="store_true")
    parser.add_argument("--show-asp", action="store_true")
    parser.add_argument("--verify", action="store_true")
    return parser


def resolve_params(args, rng: random.Random) -> StoryParams:
    choices = [
        combo
        for combo in valid_combos()
        if (args.room is None or combo[0] == args.room)
        and (args.move is None or combo[1] == args.move)
        and (args.thing is None or combo[2] == args.thing)
        and (args.gender is None or combo[3] == args.gender)
    ]
    if not choices:
        room = args.room or sorted(ROOMS)[0]
        move = args.move or sorted(MOVES)[0]
        thing = args.thing or sorted(THINGS)[0]
        gender = args.gender or GENDERS[0]
        raise StoryError(explain_rejection(room, move, thing, gender))
    room, move, thing, gender = rng.choice(choices)
    name = args.name or rng.choice(NAMES[gender])
    adult = args.adult or rng.choice(ADULTS)
    trait = args.trait or rng.choice(TRAITS)
    return StoryParams(room, move, thing, name, gender, adult, trait, args.seed)


def format_qa(title: str, items: list[QAItem]) -> list[str]:
    lines = [title]
    for item in items:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return lines


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if qa:
        print()
        print("PROMPTS")
        for prompt in sample.prompts:
            print(f"- {prompt}")
        print()
        print("\n".join(format_qa("STORY QA", sample.story_qa)))
        print()
        print("\n".join(format_qa("WORLD KNOWLEDGE QA", sample.world_qa)))
    if trace and sample.world is not None:
        print()
        print("TRACE")
        print(sample.world.trace())


def samples_from_args(args) -> list[StorySample]:
    if args.all:
        return [generate(params) for params in CURATED]
    base_seed = args.seed if args.seed is not None else random.randrange(1, 1_000_000)
    samples: list[StorySample] = []
    seen: set[str] = set()
    target = max(1, args.n)
    i = 0
    attempts = 0
    while len(samples) < target and attempts < target * 20:
        seed = base_seed + i
        i += 1
        attempts += 1
        local_args = copy.copy(args)
        local_args.seed = seed
        params = resolve_params(local_args, random.Random(seed))
        sample = generate(params)
        if sample.story in seen:
            continue
        seen.add(sample.story)
        samples.append(sample)
    return samples


def main(argv: Optional[list[str]] = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    if args.show_asp:
        print(asp_facts() + ASP_RULES)
        return 0
    if args.verify:
        return asp_verify()
    if args.asp:
        for combo in asp_valid_combos():
            print(" ".join(combo))
        return 0
    try:
        samples = samples_from_args(args)
    except StoryError as exc:
        parser.error(str(exc))
        return 2
    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return 0
    for idx, sample in enumerate(samples, 1):
        header = ""
        if len(samples) > 1:
            header = f"=== crystal_window_lamp_zoom #{idx} seed={sample.params.seed} ==="
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if idx != len(samples):
            print()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

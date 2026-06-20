#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/triple_problem_solving_humor_dialogue_nursery_rhyme.py
=================================================================================

A standalone story world for small nursery-rhyme-style tales about three funny
little friends who must move a "triple" thing from one place to another. The
story always turns on a practical problem, some comic dialogue, and a sensible
fix that matches the real trouble.

The domain is narrow on purpose: fewer strong stories beat many weak ones.

Run it
------
    python storyworlds/worlds/gpt-5.4/triple_problem_solving_humor_dialogue_nursery_rhyme.py
    python storyworlds/worlds/gpt-5.4/triple_problem_solving_humor_dialogue_nursery_rhyme.py --cargo jelly --path sunny --solution cool_bowl
    python storyworlds/worlds/gpt-5.4/triple_problem_solving_humor_dialogue_nursery_rhyme.py --cargo crowns --path sunny
    python storyworlds/worlds/gpt-5.4/triple_problem_solving_humor_dialogue_nursery_rhyme.py --all
    python storyworlds/worlds/gpt-5.4/triple_problem_solving_humor_dialogue_nursery_rhyme.py --qa --json
"""

from __future__ import annotations

import argparse
import copy
import io
import json
import os
import random
import sys
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Callable, Optional

# Make the shared result containers importable when this script is run directly.
# This file lives under storyworlds/worlds/gpt-5.4/, so add storyworlds/ itself.
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
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
    plural: bool = False
    attrs: dict = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "mother", "hen"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "drake"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    def it(self, case: str = "subject") -> str:
        if self.plural:
            return {"subject": "they", "object": "them", "possessive": "their"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class Trio:
    id: str
    species: str
    group_name: str
    line1: str
    line2: str
    rhyme_call: str
    cheer: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Cargo:
    id: str
    label: str
    phrase: str
    count_word: str
    need: str
    peril: str
    wobble_line: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Path:
    id: str
    label: str
    place_line: str
    hazard: str
    rhythm: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Solution:
    id: str
    label: str
    covers: set[str]
    prep: str
    action: str
    ending_image: str
    qa_text: str
    tags: set[str] = field(default_factory=set)


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

    def trio_members(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.role == "friend"]

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


def _r_trouble_worry(world: World) -> list[str]:
    item = world.get("cargo")
    path = world.get("path")
    if item.meters["trouble"] < THRESHOLD:
        return []
    sig = ("worry", world.facts.get("problem_kind"))
    if sig in world.fired:
        return []
    world.fired.add(sig)
    for friend in world.trio_members():
        friend.memes["worry"] += 1
        friend.memes["attention"] += 1
    path.meters["mess_risk"] += 1
    return []


def _r_fix_relief(world: World) -> list[str]:
    item = world.get("cargo")
    if item.meters["stable"] < THRESHOLD:
        return []
    sig = ("relief",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    for friend in world.trio_members():
        friend.memes["relief"] += 1
        friend.memes["joy"] += 1
    return []


CAUSAL_RULES = [
    Rule("trouble_worry", "social", _r_trouble_worry),
    Rule("fix_relief", "social", _r_fix_relief),
]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            sents = rule.apply(world)
            if sents:
                changed = True
                produced.extend(sents)
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def problem_kind(cargo: Cargo, path: Path) -> Optional[str]:
    if cargo.need == "steady" and path.hazard == "bumpy":
        return "steady"
    if cargo.need == "cool" and path.hazard == "sunny":
        return "cool"
    if cargo.need == "tied" and path.hazard == "breezy":
        return "tied"
    return None


def valid_combo(cargo: Cargo, path: Path, solution: Solution) -> bool:
    pk = problem_kind(cargo, path)
    return pk is not None and pk in solution.covers


def valid_combos() -> list[tuple[str, str, str]]:
    out: list[tuple[str, str, str]] = []
    for cargo_id, cargo in CARGO.items():
        for path_id, path in PATHS.items():
            for sol_id, sol in SOLUTIONS.items():
                if valid_combo(cargo, path, sol):
                    out.append((cargo_id, path_id, sol_id))
    return out


def explain_rejection(cargo: Cargo, path: Path, solution: Optional[Solution] = None) -> str:
    pk = problem_kind(cargo, path)
    if pk is None:
        return (
            f"(No story: {cargo.phrase} does not meet the kind of trouble found on "
            f"{path.label}. The problem must be real before the trio can solve it.)"
        )
    if solution is not None and pk not in solution.covers:
        better = ", ".join(sorted(s.id for s in SOLUTIONS.values() if pk in s.covers))
        return (
            f"(No story: {solution.label} does not solve the real problem here. "
            f"{cargo.phrase.capitalize()} on {path.label} needs help with {pk}; "
            f"try {better}.)"
        )
    return "(No story: this combination is unreasonable.)"


def predict_trouble(world: World, cargo: Cargo, path: Path) -> dict:
    sim = world.copy()
    item = sim.get("cargo")
    pk = problem_kind(cargo, path)
    if pk is None:
        return {"problem": None, "mess": False}
    item.meters["trouble"] += 1
    item.meters[pk] += 1
    propagate(sim, narrate=False)
    return {"problem": pk, "mess": sim.get("path").meters["mess_risk"] >= THRESHOLD}


def introduce(world: World, trio: Trio, names: tuple[str, str, str], cargo: Cargo, path: Path) -> None:
    a, b, c = names
    for n in (a, b, c):
        world.get(n).memes["joy"] += 1
    world.say(
        f"{trio.line1} {trio.line2} There were {a}, {b}, and {c} of the {trio.group_name}, "
        f"and they had made {cargo.phrase} for a noon-time nibble."
    )
    world.say(
        f"{path.place_line} {path.rhythm} \"{trio.rhyme_call}\" sang {a}. "
        f"\"A triple treat for all!\""
    )


def set_off(world: World, names: tuple[str, str, str], cargo: Cargo, path: Path) -> None:
    a, b, c = names
    world.say(
        f"{b} took one side, {c} took the other, and {a} marched ahead with a grin. "
        f"They started along {path.label} with {cargo.phrase} held as neat as they could."
    )


def discover_problem(world: World, names: tuple[str, str, str], cargo: Cargo, path: Path) -> None:
    a, b, c = names
    pk = problem_kind(cargo, path)
    item = world.get("cargo")
    if pk is None:
        return
    item.meters["trouble"] += 1
    item.meters[pk] += 1
    if pk == "steady":
        item.meters["tilting"] += 1
    elif pk == "cool":
        item.meters["dripping"] += 1
    elif pk == "tied":
        item.meters["fluttering"] += 1
    world.facts["problem_kind"] = pk
    propagate(world, narrate=False)
    world.say(cargo.wobble_line.format(path=path.label))
    if pk == "steady":
        world.say(
            f"\"Oh, fiddle and feet!\" cried {b}. \"This triple tower jiggles like a goat in new boots!\""
        )
    elif pk == "cool":
        world.say(
            f"\"Oh, sticky beak!\" cried {c}. \"The sunny air is licking our triple treat into drips!\""
        )
    else:
        world.say(
            f"\"Oh, flappy feathers!\" cried {a}. \"The breeze wants our triple crowns for its own silly head!\""
        )


def talk_and_plan(world: World, trio: Trio, names: tuple[str, str, str], cargo: Cargo, path: Path, solution: Solution) -> None:
    a, b, c = names
    pred = predict_trouble(world, cargo, path)
    world.facts["predicted_problem"] = pred["problem"]
    world.say(
        f"{c} blinked once, then twice. \"Let's think before we tumble,\" {world.get(c).pronoun()} said."
    )
    if pred["problem"] == "steady":
        world.say(
            f"\"Not a faster skip,\" said {a}. \"A flatter ride. {solution.prep}.\""
        )
    elif pred["problem"] == "cool":
        world.say(
            f"\"Not a bigger lick,\" said {b}. \"A cooler cradle. {solution.prep}.\""
        )
    else:
        world.say(
            f"\"Not tighter fists,\" said {a}. \"A proper knot. {solution.prep}.\""
        )
    for friend in world.trio_members():
        friend.memes["clever"] += 1


def apply_solution(world: World, trio: Trio, names: tuple[str, str, str], cargo: Cargo, path: Path, solution: Solution) -> None:
    item = world.get("cargo")
    item.meters["stable"] += 1
    item.meters["trouble"] = 0.0
    item.meters["tilting"] = 0.0
    item.meters["dripping"] = 0.0
    item.meters["fluttering"] = 0.0
    world.get("path").meters["mess_risk"] = 0.0
    propagate(world, narrate=False)
    world.say(solution.action.format(cargo=cargo.label, path=path.label))
    world.say(
        f"Then off they went again, not huffing, not flinging, but grinning and singing: "
        f"\"{trio.cheer}\""
    )


def ending(world: World, names: tuple[str, str, str], cargo: Cargo, solution: Solution) -> None:
    a, b, c = names
    world.say(
        f"At last they reached the tea cloth with every {cargo.count_word} still in place. "
        f"{solution.ending_image}"
    )
    world.say(
        f"{a} bowed, {b} giggled, and {c} said, \"A triple problem is smaller when three bright heads peep at it together.\""
    )


def tell(trio: Trio, cargo: Cargo, path: Path, solution: Solution, names: tuple[str, str, str]) -> World:
    world = World()
    for i, name in enumerate(names, 1):
        world.add(Entity(id=name, kind="character", type=trio.species, role="friend", label=name, attrs={"rank": i}))
    world.add(Entity(id="cargo", type="cargo", label=cargo.label, attrs={"need": cargo.need}, plural=cargo.id == "crowns"))
    world.add(Entity(id="path", type="path", label=path.label, attrs={"hazard": path.hazard}))

    introduce(world, trio, names, cargo, path)
    world.para()
    set_off(world, names, cargo, path)
    discover_problem(world, names, cargo, path)
    talk_and_plan(world, trio, names, cargo, path, solution)
    world.para()
    apply_solution(world, trio, names, cargo, path, solution)
    ending(world, names, cargo, solution)

    world.facts.update(
        trio=trio,
        cargo_cfg=cargo,
        path_cfg=path,
        solution=solution,
        names=names,
        solved=world.get("cargo").meters["stable"] >= THRESHOLD,
        problem_kind=problem_kind(cargo, path),
    )
    return world


TRIOS = {
    "mice": Trio(
        "mice",
        "mouse",
        "Merry Mouse Three",
        "Three little mice went tip-tap-trip,",
        "with whiskers neat and tails at whip.",
        "Trip and tap and don't let slip!",
        "Trip, think, and mind the way!",
        tags={"mice"},
    ),
    "bunnies": Trio(
        "bunnies",
        "bunny",
        "Bouncing Bunny Three",
        "Three little bunnies went hop-hop-high,",
        "with flour on ears and jam nearby.",
        "Hop and hum and mind the pie!",
        "Hop, think, and save the day!",
        tags={"bunnies"},
    ),
    "ducklings": Trio(
        "ducklings",
        "duckling",
        "Dapper Duckling Three",
        "Three little ducklings went quack-quack-quick,",
        "with shiny bills and waddles slick.",
        "Quack and clack and carry it quick!",
        "Quack, think, and make it right!",
        tags={"ducklings"},
    ),
}

CARGO = {
    "pancakes": Cargo(
        "pancakes",
        "pancake stack",
        "a triple stack of buttered pancakes",
        "pancake",
        "steady",
        "tilt",
        "But {path} gave a bump and a bob, and the pancake stack leaned to one side.",
        tags={"pancakes", "steady"},
    ),
    "jelly": Cargo(
        "jelly",
        "jelly bowl",
        "a triple-berry jelly in three jolly layers",
        "layer",
        "cool",
        "melt",
        "But along {path} the jelly gave a glup and a glisten, and one bright drip slid down the side.",
        tags={"jelly", "cool"},
    ),
    "crowns": Cargo(
        "crowns",
        "paper crowns",
        "three paper crowns tied in a triple bundle",
        "crown",
        "tied",
        "blow",
        "But {path} gave a whisk and a whoof, and the paper crowns flapped like geese in a wash line.",
        tags={"crowns", "tied"},
    ),
}

PATHS = {
    "pebble": Path(
        "pebble",
        "the pebble path",
        "By the gate lay the pebble path to the tea cloth under the pear tree.",
        "bumpy",
        "Pebbles clicked and twitched beneath their toes.",
        tags={"pebble", "bumpy"},
    ),
    "sunny": Path(
        "sunny",
        "the sunny yard",
        "Past the window shone the sunny yard to the tea cloth by the old stump.",
        "sunny",
        "Warm gold wobbled over the grass.",
        tags={"sunny", "warm"},
    ),
    "breezy": Path(
        "breezy",
        "the breezy bridge",
        "Over the brook stretched the breezy bridge to the tea cloth by the willow root.",
        "breezy",
        "The air kept puffing little jokes into their ears.",
        tags={"breezy", "wind"},
    ),
}

SOLUTIONS = {
    "tray": Solution(
        "tray",
        "a flat tray",
        {"steady"},
        "We need a flat tray with both paws under it",
        "So they set the {cargo} on a flat tray and took {path} in tiny, even steps.",
        "The stack sat proud and level, with butter shining like three yellow moons.",
        "set the stack on a flat tray and carried it with even steps",
        tags={"tray", "steady"},
    ),
    "cool_bowl": Solution(
        "cool_bowl",
        "a cool bowl",
        {"cool"},
        "We need a cool bowl with a damp cloth round it",
        "So they nestled the {cargo} into a cool bowl wrapped with a damp cloth and crossed {path} in the shade.",
        "The jelly kept its wiggle to itself and glowed like a ruby lantern.",
        "nestled the jelly into a cool bowl with a damp cloth around it",
        tags={"cool_bowl", "cool"},
    ),
    "ribbon": Solution(
        "ribbon",
        "a ribbon bow",
        {"tied"},
        "We need a ribbon bow with a proper knot",
        "So they tied the {cargo} with a ribbon bow and held the knot snug while they crossed {path}.",
        "The crowns only rustled politely, as if practicing bows for a small queen.",
        "tied the crowns with a proper ribbon bow",
        tags={"ribbon", "tied"},
    ),
}

NAME_SETS = {
    "mice": [
        ("Pip", "Squeak", "Nip"),
        ("Mop", "Pip", "Tip"),
        ("Nip", "Pip", "Dot"),
    ],
    "bunnies": [
        ("Bun", "Bob", "Bess"),
        ("Pip", "Mop", "Bun"),
        ("Nell", "Bram", "Bun"),
    ],
    "ducklings": [
        ("Dot", "Nib", "Quill"),
        ("Pip", "Peb", "Mop"),
        ("Wib", "Dob", "Pip"),
    ],
}


@dataclass
class StoryParams:
    trio: str
    cargo: str
    path: str
    solution: str
    seed: Optional[int] = None


KNOWLEDGE = {
    "steady": [
        (
            "Why does a flat tray help carry a wobbly stack?",
            "A flat tray gives the whole stack one steady floor to stand on. When both hands hold the tray level, the top pieces are less likely to slide."
        )
    ],
    "cool": [
        (
            "Why does a cool bowl help jelly on a warm day?",
            "Jelly softens in warmth, so a cooler container helps it keep its shape. Shade and a damp cloth can help it stay firmer for longer."
        )
    ],
    "tied": [
        (
            "Why does a ribbon help in the wind?",
            "A ribbon keeps loose things together so the wind cannot pull each piece away on its own. A good knot turns many flappy parts into one easier bundle."
        )
    ],
    "pancakes": [
        (
            "What is a pancake stack?",
            "A pancake stack is a pile of pancakes set one on top of another. A tall stack can wobble if you carry it over bumps."
        )
    ],
    "jelly": [
        (
            "Why does jelly wobble?",
            "Jelly is soft and springy, so it jiggles when it is moved. Warm weather can make it even softer."
        )
    ],
    "crowns": [
        (
            "Why are paper crowns easy for wind to grab?",
            "Paper crowns are light, so moving air can lift and flap them. If they are loose, the wind can scatter them quickly."
        )
    ],
    "breezy": [
        (
            "What is a breeze?",
            "A breeze is a small moving stream of air. It can feel nice on your face, but it can also nudge light things away."
        )
    ],
    "sunny": [
        (
            "Why can sunshine change food?",
            "Sunshine brings warmth. Some foods get softer or drippier when they sit in warm sun."
        )
    ],
    "pebble": [
        (
            "Why is a pebble path bumpy?",
            "Pebbles are little stones, and they do not make one smooth floor. Your steps bob up and down as you walk over them."
        )
    ],
}
KNOWLEDGE_ORDER = ["steady", "cool", "tied", "pancakes", "jelly", "crowns", "breezy", "sunny", "pebble"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    trio = f["trio"]
    cargo = f["cargo_cfg"]
    path = f["path_cfg"]
    return [
        f'Write a nursery-rhyme-style story about three little {trio.species}s carrying {cargo.phrase} across {path.label}. Include the word "triple".',
        f"Tell a funny problem-solving story with dialogue where three friends notice a real problem, stop, think, and fix it together.",
        f"Write a short rhyming tale in which a small comic mishap on {path.label} is solved by practical thinking instead of panic.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    trio = f["trio"]
    cargo = f["cargo_cfg"]
    path = f["path_cfg"]
    solution = f["solution"]
    a, b, c = f["names"]
    pk = f["problem_kind"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about three little {trio.species}s named {a}, {b}, and {c}. They were carrying {cargo.phrase} to a tea cloth."
        ),
        (
            "What problem did they run into?",
            f"They ran into a {pk} problem on {path.label}. {cargo.phrase.capitalize()} did not suit that path, so it started to look likely that they would spill, drip, or blow it away."
        ),
        (
            "How did the friends solve the problem?",
            f"They stopped moving fast and thought about what the trouble really was. Then they used {solution.label}, which fit the problem instead of guessing wildly."
        ),
        (
            "Why is the story funny?",
            f"The friends talk in silly, playful ways about a very ordinary problem. Their jokes make the trouble feel light, even while they are solving it sensibly."
        ),
    ]
    if pk == "steady":
        qa.append(
            (
                "Why did the tray help the triple stack?",
                "The stack was wobbling because the path was bumpy. A flat tray gave the whole stack one steady surface, so the three little carriers could keep it level together."
            )
        )
    elif pk == "cool":
        qa.append(
            (
                "Why did the cool bowl help the jelly?",
                "The jelly was starting to soften in the sunny yard. The cool bowl and damp cloth helped it stay firmer, so the triple layers reached the tea cloth still neat."
            )
        )
    else:
        qa.append(
            (
                "Why did the ribbon help the crowns?",
                "The crowns were light and the bridge was breezy. The ribbon turned them into one tidy bundle, so the wind could not snatch them apart so easily."
            )
        )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags = set()
    tags.add(f["problem_kind"])
    tags |= f["cargo_cfg"].tags
    tags |= f["path_cfg"].tags
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
            shown = {k: v for k, v in e.attrs.items() if v}
            if shown:
                bits.append(f"attrs={shown}")
        lines.append(f"  {e.id:8} ({e.type:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams("mice", "pancakes", "pebble", "tray"),
    StoryParams("bunnies", "jelly", "sunny", "cool_bowl"),
    StoryParams("ducklings", "crowns", "breezy", "ribbon"),
]


ASP_RULES = r"""
problem(steady) :- cargo_need(C, steady), path_hazard(P, bumpy), chosen_cargo(C), chosen_path(P).
problem(cool)   :- cargo_need(C, cool),   path_hazard(P, sunny), chosen_cargo(C), chosen_path(P).
problem(tied)   :- cargo_need(C, tied),   path_hazard(P, breezy), chosen_cargo(C), chosen_path(P).

combo_problem(C, P, steady) :- cargo_need(C, steady), path_hazard(P, bumpy).
combo_problem(C, P, cool)   :- cargo_need(C, cool),   path_hazard(P, sunny).
combo_problem(C, P, tied)   :- cargo_need(C, tied),   path_hazard(P, breezy).

valid(C, P, S) :- combo_problem(C, P, K), solution_covers(S, K).

solves(S) :- chosen_solution(S), problem(K), solution_covers(S, K).
outcome(solved) :- solves(S).
outcome(bad_match) :- problem(K), chosen_solution(S), not solution_covers(S, K).
outcome(no_problem) :- chosen_cargo(C), chosen_path(P), not combo_problem(C, P, _).
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for cargo_id, cargo in CARGO.items():
        lines.append(asp.fact("cargo", cargo_id))
        lines.append(asp.fact("cargo_need", cargo_id, cargo.need))
    for path_id, path in PATHS.items():
        lines.append(asp.fact("path", path_id))
        lines.append(asp.fact("path_hazard", path_id, path.hazard))
    for sol_id, sol in SOLUTIONS.items():
        lines.append(asp.fact("solution", sol_id))
        for k in sorted(sol.covers):
            lines.append(asp.fact("solution_covers", sol_id, k))
    for trio_id in TRIOS:
        lines.append(asp.fact("trio", trio_id))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("", "#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_outcome(params: StoryParams) -> str:
    import asp

    extra = "\n".join(
        [
            asp.fact("chosen_cargo", params.cargo),
            asp.fact("chosen_path", params.path),
            asp.fact("chosen_solution", params.solution),
        ]
    )
    model = asp.one_model(asp_program(extra, "#show outcome/1."))
    atoms = asp.atoms(model, "outcome")
    return atoms[0][0] if atoms else "?"


def outcome_of(params: StoryParams) -> str:
    pk = problem_kind(CARGO[params.cargo], PATHS[params.path])
    if pk is None:
        return "no_problem"
    return "solved" if pk in SOLUTIONS[params.solution].covers else "bad_match"


def asp_verify() -> int:
    rc = 0
    clingo_set, python_set = set(asp_valid_combos()), set(valid_combos())
    if clingo_set == python_set:
        print(f"OK: gate matches valid_combos() ({len(clingo_set)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos:")
        if clingo_set - python_set:
            print("  only in clingo:", sorted(clingo_set - python_set))
        if python_set - clingo_set:
            print("  only in python:", sorted(python_set - clingo_set))

    checked = CURATED + [StoryParams("mice", c, p, s) for (c, p, s) in valid_combos()]
    bad = sum(1 for params in checked if asp_outcome(params) != outcome_of(params))
    if bad == 0:
        print(f"OK: outcome model matches on {len(checked)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {bad}/{len(checked)} outcomes differ.")

    try:
        sample = generate(CURATED[0])
        buf = io.StringIO()
        old = sys.stdout
        sys.stdout = buf
        try:
            emit(sample, trace=True, qa=True, header="### smoke")
        finally:
            sys.stdout = old
        if not sample.story.strip():
            raise StoryError("empty story")
        print("OK: smoke generation and emit passed.")
    except Exception as err:
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Nursery-rhyme story world: three funny friends solve one practical problem together."
    )
    ap.add_argument("--trio", choices=TRIOS)
    ap.add_argument("--cargo", choices=CARGO)
    ap.add_argument("--path", choices=PATHS)
    ap.add_argument("--solution", choices=SOLUTIONS)
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list compatible (cargo, path, solution) triples from clingo")
    ap.add_argument("--verify", action="store_true", help="check the inline ASP reasoner and run a smoke test")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.cargo and args.path and args.solution:
        cargo, path, solution = CARGO[args.cargo], PATHS[args.path], SOLUTIONS[args.solution]
        if not valid_combo(cargo, path, solution):
            raise StoryError(explain_rejection(cargo, path, solution))
    elif args.cargo and args.path:
        cargo, path = CARGO[args.cargo], PATHS[args.path]
        if problem_kind(cargo, path) is None:
            raise StoryError(explain_rejection(cargo, path))

    combos = [
        combo
        for combo in valid_combos()
        if (args.cargo is None or combo[0] == args.cargo)
        and (args.path is None or combo[1] == args.path)
        and (args.solution is None or combo[2] == args.solution)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    cargo_id, path_id, solution_id = rng.choice(sorted(combos))
    trio_id = args.trio or rng.choice(sorted(TRIOS))
    return StoryParams(trio_id, cargo_id, path_id, solution_id)


def generate(params: StoryParams) -> StorySample:
    trio = TRIOS[params.trio]
    names = random.Random((params.seed or 0) + 17).choice(NAME_SETS[params.trio])
    world = tell(trio, CARGO[params.cargo], PATHS[params.path], SOLUTIONS[params.solution], names)
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
        print(asp_program("", "#show valid/3.\n#show outcome/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (cargo, path, solution) combos:\n")
        for cargo, path, solution in combos:
            print(f"  {cargo:10} {path:8} {solution}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)

    samples: list[StorySample] = []
    if args.all:
        for i, params in enumerate(CURATED):
            p = StoryParams(params.trio, params.cargo, params.path, params.solution, seed=base_seed + i)
            samples.append(generate(p))
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
            header = f"### {p.trio}: {p.cargo} on {p.path} with {p.solution}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""
storyworlds/worlds/swell_neighbor_problem_solving_myth.py
=========================================================

A small mythic storyworld about a swelling river, a nearby neighbor, and a
problem solved with care, tools, and shared courage.

The seed image is a short tale in which a river swells after rain, a neighbor
notices trouble, and the people of the lane work together to protect a home.
This script turns that premise into a deterministic little simulation with
physical meters and emotional memes, plus an ASP twin for reasonableness.
"""

from __future__ import annotations

import argparse
import copy
import json
import os
import random
import sys
from dataclasses import dataclass, field
from typing import Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from results import QAItem, StoryError, StorySample  # noqa: E402

# ---------------------------------------------------------------------------
# Core world model
# ---------------------------------------------------------------------------

THRESHOLD = 1.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"  # "character" | "thing" | "place"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "woman", "sister", "aunt"}
        male = {"boy", "father", "man", "brother", "uncle", "neighbor"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Place:
    id: str
    label: str
    has_river: bool = False
    riverbank: bool = False
    affords: set[str] = field(default_factory=set)


@dataclass
class Problem:
    id: str
    label: str
    danger: str
    sign: str
    verb: str
    effect: str
    area: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Tool:
    id: str
    label: str
    phrase: str
    action: str
    helps: set[str]
    blocks: set[str]
    plural: bool = False


class World:
    def __init__(self, place: Place) -> None:
        self.place = place
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.trace_notes: list[str] = []

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str) -> Entity:
        return self.entities[eid]

    def characters(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.kind == "character"]

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)

    def copy(self) -> "World":
        clone = World(self.place)
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        clone.facts = copy.deepcopy(self.facts)
        return clone


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------

PLACES = {
    "river_lane": Place(id="river_lane", label="the river lane", has_river=True, riverbank=True, affords={"swell"}),
    "stone_bridge": Place(id="stone_bridge", label="the stone bridge", has_river=True, riverbank=False, affords={"swell"}),
    "orchard": Place(id="orchard", label="the orchard path", has_river=False, riverbank=False, affords=set()),
}

PROBLEMS = {
    "swell": Problem(
        id="swell",
        label="the swell",
        danger="rising water",
        sign="the river rose fast and pressed at the bank",
        verb="swell",
        effect="spill over the edge",
        area="riverbank",
        tags={"water", "river", "flood"},
    ),
    "rift": Problem(
        id="rift",
        label="the crack",
        danger="a split stone path",
        sign="the path opened like a bad seam",
        verb="widen",
        effect="let feet slip",
        area="path",
        tags={"stone", "path"},
    ),
}

TOOLS = [
    Tool(
        id="sandbags",
        label="sandbags",
        phrase="a stack of sandbags",
        action="pile them along the bank",
        helps={"swell"},
        blocks={"water"},
        plural=True,
    ),
    Tool(
        id="reedmat",
        label="a reed mat",
        phrase="a woven reed mat",
        action="lay it down on the stones",
        helps={"rift"},
        blocks={"stone"},
    ),
    Tool(
        id="rope",
        label="rope",
        phrase="a strong rope",
        action="tie the bundles tight",
        helps={"swell", "rift"},
        blocks={"water", "stone"},
    ),
]

GENDERS = ["girl", "boy"]
NAMES = {
    "girl": ["Mira", "Luna", "Sera", "Nia", "Tala"],
    "boy": ["Orin", "Bram", "Kian", "Arun", "Tavi"],
}
NEIGHBOR_NAMES = ["the neighbor", "the old neighbor", "the kind neighbor"]
TRAITS = ["brave", "gentle", "clever", "steady", "quick-thinking"]


# ---------------------------------------------------------------------------
# Story parameters
# ---------------------------------------------------------------------------

@dataclass
class StoryParams:
    place: str
    problem: str
    name: str
    gender: str
    neighbor: str
    trait: str
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def place_allows(place: Place, problem: Problem) -> bool:
    return problem.id in place.affords


def choose_tool(problem: Problem) -> Optional[Tool]:
    for tool in TOOLS:
        if problem.id in tool.helps:
            return tool
    return None


def predict(problem: Problem, tool: Tool) -> dict[str, bool]:
    return {
        "solved": problem.id in tool.helps,
        "blocked": bool(tool.blocks & problem.tags),
    }


def noun_phrase(ent: Entity) -> str:
    return ent.label or ent.id


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------

ASP_RULES = r"""
problem_at_place(P, L) :- problem(P), place(L), requires_place(P, L).
tool_works(T, P) :- tool(T), problem(P), helps(T, P), not blocked(T, P).
solvable(L, P) :- problem_at_place(P, L), tool_works(T, P), place(L).
"""

def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid, pl in PLACES.items():
        lines.append(asp.fact("place", pid))
        if pl.has_river:
            lines.append(asp.fact("has_river", pid))
        if pl.riverbank:
            lines.append(asp.fact("riverbank", pid))
        for a in sorted(pl.affords):
            lines.append(asp.fact("affords", pid, a))
    for pid, pr in PROBLEMS.items():
        lines.append(asp.fact("problem", pid))
        lines.append(asp.fact("requires_place", pid, "riverbank" if pr.area == "riverbank" else "path"))
        for t in sorted(pr.tags):
            lines.append(asp.fact("tag", pid, t))
    for tool in TOOLS:
        lines.append(asp.fact("tool", tool.id))
        for p in sorted(tool.helps):
            lines.append(asp.fact("helps", tool.id, p))
        for b in sorted(tool.blocks):
            lines.append(asp.fact("blocked", tool.id, b))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_solvable() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show solvable/2."))
    return sorted(set(asp.atoms(model, "solvable")))


def valid_combos() -> list[tuple[str, str]]:
    out: list[tuple[str, str]] = []
    for place_id, place in PLACES.items():
        for problem_id, problem in PROBLEMS.items():
            if place_allows(place, problem) and choose_tool(problem) is not None:
                out.append((place_id, problem_id))
    return out


def asp_verify() -> int:
    py = set(valid_combos())
    cl = set(asp_solvable())
    if py == cl:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and python:")
    if py - cl:
        print("  only in python:", sorted(py - cl))
    if cl - py:
        print("  only in clingo:", sorted(cl - py))
    return 1


# ---------------------------------------------------------------------------
# Narrative engine
# ---------------------------------------------------------------------------

def _r_swell(world: World) -> list[str]:
    out: list[str] = []
    if not world.place.has_river:
        return out
    river = world.get("river")
    if river.meters.get("swell", 0.0) < THRESHOLD:
        return out
    sig = ("swell", world.place.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    world.facts["danger"] = True
    out.append("The river rose with a deep, hungry sound.")
    out.append("Water pressed at the bank and threatened to spill over.")
    return out


def _r_neighbor_notices(world: World) -> list[str]:
    out: list[str] = []
    neighbor = world.get("neighbor")
    if world.facts.get("noticed"):
        return out
    if world.get("river").meters.get("swell", 0.0) >= THRESHOLD:
        world.facts["noticed"] = True
        neighbor.memes["concern"] = neighbor.memes.get("concern", 0) + 1
        out.append(f"{noun_phrase(neighbor).capitalize()} saw the rising water and grew serious.")
    return out


def _r_solve(world: World) -> list[str]:
    out: list[str] = []
    if not world.facts.get("need_solution"):
        return out
    if world.facts.get("solved"):
        return out
    tool = world.facts.get("tool")
    hero = world.get("hero")
    neighbor = world.get("neighbor")
    if tool is None:
        return out
    if tool.id == "sandbags":
        world.get("river").meters["swell"] = 0.0
        world.facts["solved"] = True
        out.append("Together they piled sandbags along the bank.")
        out.append("The water could not push through the wall they had made.")
    elif tool.id == "rope":
        world.get("river").meters["swell"] = 0.0
        world.facts["solved"] = True
        out.append("Together they tied the bundles tight with rope.")
        out.append("The line held, and the water calmed at last.")
    else:
        world.get("river").meters["swell"] = 0.0
        world.facts["solved"] = True
        out.append("They laid the reed mat where the trouble began.")
        out.append("The path held steady, and the danger passed away.")
    hero.memes["relief"] = hero.memes.get("relief", 0) + 1
    neighbor.memes["relief"] = neighbor.memes.get("relief", 0) + 1
    return out


CAUSAL_RULES = [_r_swell, _r_neighbor_notices, _r_solve]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            sents = rule(world)
            if sents:
                changed = True
                produced.extend(sents)
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def tell(params: StoryParams) -> World:
    place = PLACES[params.place]
    problem = PROBLEMS[params.problem]
    world = World(place)

    hero = world.add(Entity(id="hero", kind="character", type=params.gender, label=params.name))
    neighbor = world.add(Entity(id="neighbor", kind="character", type="neighbor", label=params.neighbor))
    river = world.add(Entity(id="river", kind="thing", type="river", label="the river"))
    bank = world.add(Entity(id="bank", kind="place", type="bank", label="the bank"))
    tool = choose_tool(problem)

    # Setup
    hero.memes["duty"] = 1
    hero.memes["love"] = 1
    world.say(
        f"In old days, {hero.label} was a {params.trait} child who watched the lane with careful eyes."
    )
    world.say(
        f"{hero.label} lived near {place.label}, where the river could be gentle one hour and wild the next."
    )
    world.say(
        f"One season, {problem.sign}."
    )

    # Conflict
    world.para()
    river.meters["swell"] = 1.0
    world.facts["need_solution"] = True
    world.say(
        f"{neighbor.label.capitalize()} came to the gate and said, "
        f'"The river is swelling. If we do nothing, it may {problem.effect}."'
    )
    world.say(
        f"{hero.label} looked at the water, then at the bank, and knew the trouble was real."
    )
    if tool is None:
        raise StoryError("No tool exists for this problem; the story cannot be solved honestly.")

    world.facts["tool"] = tool
    world.say(
        f"So they chose {tool.phrase} and a plan to {tool.action}."
    )

    # Resolution
    world.para()
    propagate(world, narrate=True)
    if not world.facts.get("solved"):
        raise StoryError("The problem should be solvable, but the simulation did not resolve it.")

    world.say(
        f"In the end, {hero.label} stood beside {neighbor.label}, and the river stayed inside its home."
    )
    world.say(
        f"The lane was quiet again, and the old fear had turned into a useful story about how neighbors help."
    )

    world.facts.update(
        hero=hero,
        neighbor=neighbor,
        river=river,
        bank=bank,
        tool=tool,
        problem=problem,
        place=place,
        solved=True,
    )
    return world


# ---------------------------------------------------------------------------
# QA
# ---------------------------------------------------------------------------

def prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    problem = f["problem"]
    place = f["place"]
    return [
        f'Write a myth-like story for a child about a {problem.label} near {place.label} and a helpful neighbor.',
        f"Tell a short story in which {hero.label} and a neighbor solve a swelling-river problem together.",
        f'Write a gentle myth about a river that "swells" and the people who keep a home safe.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    neighbor = f["neighbor"]
    problem = f["problem"]
    tool = f["tool"]
    place = f["place"]
    return [
        QAItem(
            question=f"Who noticed the trouble near {place.label}?",
            answer=f"{neighbor.label.capitalize()} noticed the trouble first and warned {hero.label} that the river was swelling.",
        ),
        QAItem(
            question=f"What was the problem in the story?",
            answer=f"The problem was {problem.label}: the river rose fast and threatened to spill over the bank.",
        ),
        QAItem(
            question=f"How did they solve it?",
            answer=f"They solved it by using {tool.phrase} and working together until the water stayed inside its place.",
        ),
        QAItem(
            question=f"What changed by the end?",
            answer=f"By the end, the danger was gone, and {hero.label} and {neighbor.label} stood together in a quiet lane.",
        ),
    ]


WORLD_KNOWLEDGE = {
    "swell": [
        QAItem(
            question="What does it mean when water swells?",
            answer="When water swells, it rises higher and takes up more space, like a river growing strong after rain.",
        )
    ],
    "neighbor": [
        QAItem(
            question="What is a neighbor?",
            answer="A neighbor is someone who lives nearby and can help when something important needs doing.",
        )
    ],
    "sandbags": [
        QAItem(
            question="What are sandbags for?",
            answer="Sandbags can be stacked to help hold back water and protect a place from flooding.",
        )
    ],
    "rope": [
        QAItem(
            question="What is rope used for?",
            answer="Rope can be used to tie things together or hold something steady when it might move.",
        )
    ],
}


def world_knowledge_qa(world: World) -> list[QAItem]:
    tags = set(world.facts["problem"].tags)
    tool = world.facts["tool"]
    tags.add(tool.id)
    out: list[QAItem] = []
    for key in ["swell", "neighbor", "sandbags", "rope"]:
        if key in tags:
            out.extend(WORLD_KNOWLEDGE[key])
    return out


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== (2) Story questions ==")
    for q in sample.story_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    lines.append("")
    lines.append("== (3) World knowledge questions ==")
    for q in sample.world_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# CLI / generation
# ---------------------------------------------------------------------------

CURATED = [
    StoryParams(place="river_lane", problem="swell", name="Mira", gender="girl", neighbor="the kind neighbor", trait="steady"),
    StoryParams(place="stone_bridge", problem="swell", name="Orin", gender="boy", neighbor="the old neighbor", trait="quick-thinking"),
]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Mythic storyworld: swell, neighbor, and problem solving.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--problem", choices=PROBLEMS)
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=GENDERS)
    ap.add_argument("--neighbor", choices=NEIGHBOR_NAMES)
    ap.add_argument("--trait", choices=TRAITS)
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
    combos = valid_combos()
    if args.place or args.problem:
        combos = [
            (p, pr)
            for p, pr in combos
            if (args.place is None or p == args.place) and (args.problem is None or pr == args.problem)
        ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, problem = rng.choice(sorted(combos))
    gender = args.gender or rng.choice(GENDERS)
    name = args.name or rng.choice(NAMES[gender])
    neighbor = args.neighbor or rng.choice(NEIGHBOR_NAMES)
    trait = args.trait or rng.choice(TRAITS)

    if args.problem == "swell" and place not in {"river_lane", "stone_bridge"}:
        raise StoryError("The swell story needs a place near a river.")
    return StoryParams(place=place, problem=problem, name=name, gender=gender, neighbor=neighbor, trait=trait)


def generate(params: StoryParams) -> StorySample:
    world = tell(params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(n for n, *_ in world.fired)}")
    return "\n".join(lines)


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world is not None:
        print(dump_trace(sample.world))
    if qa:
        print()
        print(format_qa(sample))


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show solvable/2."))
    return sorted(set(asp.atoms(model, "solvable")))


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show solvable/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} solvable combos:")
        for place, problem in combos:
            print(f"  {place:12} {problem}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
            seed = base_seed + i
            i += 1
            params = resolve_params(args, random.Random(seed))
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
            header = f"### {p.name}: {p.problem} at {p.place}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()

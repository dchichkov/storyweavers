#!/usr/bin/env python3
"""
A small pirate-tale story world about a lost ratchet, a pasture, and a recollection
that helps a crew solve a conflict together.
"""

from __future__ import annotations

import argparse
import json
import os
import random
import sys
from dataclasses import dataclass, field
from typing import Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from results import QAItem, StoryError, StorySample  # noqa: E402

# ---------------------------------------------------------------------------
# World model
# ---------------------------------------------------------------------------

THRESHOLD = 1.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"          # "character" | "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    carried_by: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"captain", "boy", "man", "father"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        if self.type in {"girl", "woman", "mother", "captainess"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Place:
    id: str
    label: str
    detail: str
    affords: set[str] = field(default_factory=set)


@dataclass
class Problem:
    id: str
    noun: str
    verb: str
    consequence: str
    solved_by: str
    requires: set[str] = field(default_factory=set)


@dataclass
class Tool:
    id: str
    label: str
    phrase: str
    fixes: set[str] = field(default_factory=set)
    place_ok: set[str] = field(default_factory=set)


class World:
    def __init__(self, place: Place) -> None:
        self.place = place
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.fired: set[tuple] = set()
        self.events: list[str] = []

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str) -> Entity:
        return self.entities[eid]

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)
            self.events.append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)

    def copy(self) -> "World":
        import copy
        w = World(self.place)
        w.entities = copy.deepcopy(self.entities)
        w.paragraphs = [[]]
        w.facts = dict(self.facts)
        w.fired = set(self.fired)
        return w


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------

PLACES = {
    "harbor": Place(
        id="harbor",
        label="the harbor",
        detail="The harbor smelled of salt and tar, with gulls crying above the docks.",
        affords={"search", "work"},
    ),
    "pasture": Place(
        id="pasture",
        label="the pasture",
        detail="The pasture lay green and wide, with a crooked fence and soft grass underfoot.",
        affords={"search", "work"},
    ),
    "cove": Place(
        id="cove",
        label="the cove",
        detail="The cove tucked itself behind black rocks, where a tidepool glittered like a coin.",
        affords={"search"},
    ),
}

PROBLEMS = {
    "broken_winch": Problem(
        id="broken_winch",
        noun="winch",
        verb="would not turn",
        consequence="the chest could not be lifted onto the deck",
        solved_by="ratchet",
        requires={"search", "work"},
    ),
    "stuck_gate": Problem(
        id="stuck_gate",
        noun="gate",
        verb="would not swing open",
        consequence="the crew could not reach the hidden path",
        solved_by="ratchet",
        requires={"search", "work"},
    ),
}

TOOLS = {
    "ratchet": Tool(
        id="ratchet",
        label="ratchet",
        phrase="a brass ratchet with a worn red handle",
        fixes={"broken_winch", "stuck_gate"},
        place_ok={"harbor", "pasture", "cove"},
    ),
}

HERO_NAMES = ["Mira", "Jory", "Tess", "Nell", "Pip", "Anne"]
CREW_TITLES = ["captain", "first mate", "deckhand"]


# ---------------------------------------------------------------------------
# Story parameters
# ---------------------------------------------------------------------------

@dataclass
class StoryParams:
    place: str
    problem: str
    hero_name: str
    hero_type: str
    crewmate_type: str
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------

ASP_RULES = r"""
place(P) :- setting(P).
problem(X) :- issue(X).
tool(T) :- tool(T).

can_happen(P, X) :- setting(P), issue(X), place_allows(P, X).
solves(T, X) :- tool(T), issue(X), tool_fixes(T, X).
valid(P, X, T) :- can_happen(P, X), solves(T, X).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid in PLACES:
        lines.append(asp.fact("setting", pid))
        for a in sorted(PLACES[pid].affords):
            lines.append(asp.fact("place_allows", pid, a))
    for pid in PROBLEMS:
        lines.append(asp.fact("issue", pid))
    for tid in TOOLS:
        lines.append(asp.fact("tool", tid))
        for p in sorted(TOOLS[tid].fixes):
            lines.append(asp.fact("tool_fixes", tid, p))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid() -> list[tuple[str, str, str]]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for place in PLACES.values():
        for prob in PROBLEMS.values():
            for tool in TOOLS.values():
                if prob.id in tool.fixes and place.id in tool.place_ok and prob.requires.issubset(place.affords):
                    combos.append((place.id, prob.id, tool.id))
    return combos


def asp_verify() -> int:
    a = set(asp_valid())
    p = set(valid_combos())
    if a == p:
        print(f"OK: clingo gate matches valid_combos() ({len(a)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    if a - p:
        print(" only in clingo:", sorted(a - p))
    if p - a:
        print(" only in python:", sorted(p - a))
    return 1


# ---------------------------------------------------------------------------
# Simulation helpers
# ---------------------------------------------------------------------------

def _search(world: World, hero: Entity, problem: Problem) -> None:
    hero.memes["hope"] = hero.memes.get("hope", 0.0) + 1
    world.say(
        f"{hero.id} squinted over the {world.place.label} and thought, "
        f"\"Somewhere near this {world.place.id} or that pasture, there's a thing "
        f"that can fix a {problem.noun}.\""
    )
    world.say(world.place.detail)


def _inner_monologue(hero: Entity, problem: Problem) -> str:
    return (
        f"\"If I can find the {problem.solved_by},\" {hero.id} thought, "
        f"\"then this old trouble won't beat us today.\""
    )


def _conflict(world: World, hero: Entity, crew: Entity, problem: Problem) -> None:
    hero.memes["worry"] = hero.memes.get("worry", 0.0) + 1
    crew.memes["impatience"] = crew.memes.get("impatience", 0.0) + 1
    world.say(
        f"But {crew.id} grumbled that the {problem.noun} had already cost too much time, "
        f"and the deck felt tight with worry."
    )
    world.say(_inner_monologue(hero, problem))


def _use_tool(world: World, hero: Entity, tool: Tool, problem: Problem) -> None:
    hero.meters["skill"] = hero.meters.get("skill", 0.0) + 1
    hero.memes["confidence"] = hero.memes.get("confidence", 0.0) + 1
    world.say(
        f"{hero.id} found {tool.phrase} tucked where old gear was kept. "
        f"They turned it slow and steady, and the stubborn {problem.noun} gave way."
    )


def _resolution(world: World, hero: Entity, crew: Entity, tool: Tool, problem: Problem) -> None:
    hero.memes["joy"] = hero.memes.get("joy", 0.0) + 1
    crew.memes["relief"] = crew.memes.get("relief", 0.0) + 1
    world.say(
        f"Soon the {problem.noun} worked again, {problem.consequence} no longer mattered, "
        f"and the crew laughed as if the salt wind itself had cheered for them."
    )
    world.say(
        f"{hero.id} kept the {tool.label} in hand and smiled at the pasture beyond the fence, "
        f"glad the day had bent the right way at last."
    )


def tell(place: Place, problem: Problem, hero_name: str, hero_type: str, crewmate_type: str) -> World:
    world = World(place)
    hero = world.add(Entity(id=hero_name, kind="character", type=hero_type, label=hero_name))
    crew = world.add(Entity(id="Crewmate", kind="character", type=crewmate_type, label="the crewmate"))
    tool = world.add(Entity(id="Ratchet", type="tool", label="ratchet", phrase=TOOLS["ratchet"].phrase))
    world.facts.update(hero=hero, crew=crew, tool=tool, problem=problem, place=place)

    world.say(
        f"On a windy day, {hero.id} crossed {place.label} with {crew.label}, "
        f"and the old {problem.noun} at the shed was their first hard surprise."
    )
    world.para()
    _search(world, hero, problem)
    world.say(_inner_monologue(hero, problem))
    _conflict(world, hero, crew, problem)

    world.para()
    _use_tool(world, hero, tool, problem)
    _resolution(world, hero, crew, tool, problem)
    return world


# ---------------------------------------------------------------------------
# QA
# ---------------------------------------------------------------------------

def generation_prompts(world: World) -> list[str]:
    p = world.facts["place"]
    prob = world.facts["problem"]
    return [
        f"Write a pirate tale where a crew searches {PLACES[p.id].label} for a tool to fix a {prob.noun}.",
        f"Tell a short story with inner monologue, conflict, and problem solving set near a pasture.",
        f"Write a child-friendly pirate adventure that includes the words pasture, recollection, and ratchet.",
    ]


def story_qa(world: World) -> list[QAItem]:
    hero = world.facts["hero"]
    crew = world.facts["crew"]
    tool = world.facts["tool"]
    problem = world.facts["problem"]
    place = world.facts["place"]
    return [
        QAItem(
            question=f"Who tried to solve the problem at {place.label}?",
            answer=f"{hero.id} tried to solve it while {crew.label} worried about the delay.",
        ),
        QAItem(
            question=f"What tool did {hero.id} find to fix the {problem.noun}?",
            answer=f"{hero.id} found a ratchet, and that tool was the key to loosening the stubborn {problem.noun}.",
        ),
        QAItem(
            question=f"Why was there conflict before the fix?",
            answer=f"The crewmate grumbled because the {problem.noun} kept the crew waiting, and {hero.id} had to keep thinking.",
        ),
        QAItem(
            question=f"What recollection helped the story move forward?",
            answer="A recollection of where the old gear was stored helped the hero search in the right place.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a pasture?",
            answer="A pasture is a field of grass where animals can graze or where people can walk and look around.",
        ),
        QAItem(
            question="What is a ratchet?",
            answer="A ratchet is a tool that turns a little at a time, which helps loosen or tighten parts that are stuck.",
        ),
        QAItem(
            question="What is a recollection?",
            answer="A recollection is a memory of something that happened before.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    out = ["== (1) Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        out.append(f"{i}. {p}")
    out.append("")
    out.append("== (2) Story questions ==")
    for q in sample.story_qa:
        out.append(f"Q: {q.question}")
        out.append(f"A: {q.answer}")
    out.append("")
    out.append("== (3) World-knowledge questions ==")
    for q in sample.world_qa:
        out.append(f"Q: {q.question}")
        out.append(f"A: {q.answer}")
    return "\n".join(out)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        bits = []
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        lines.append(f"  {e.id} ({e.type}) {' '.join(bits)}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Params and CLI
# ---------------------------------------------------------------------------

@dataclass
class StoryParams:
    place: str
    problem: str
    hero_name: str
    hero_type: str
    crewmate_type: str
    seed: Optional[int] = None


CURATED = [
    StoryParams(place="pasture", problem="broken_winch", hero_name="Mira", hero_type="captain", crewmate_type="deckhand"),
    StoryParams(place="harbor", problem="stuck_gate", hero_name="Jory", hero_type="captain", crewmate_type="first mate"),
    StoryParams(place="cove", problem="broken_winch", hero_name="Tess", hero_type="deckhand", crewmate_type="captain"),
]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Pirate tale story world about a recollection and a ratchet.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--problem", choices=PROBLEMS)
    ap.add_argument("--name")
    ap.add_argument("--hero-type", choices=CREW_TITLES)
    ap.add_argument("--crewmate-type", choices=CREW_TITLES)
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


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    combos = valid_combos()
    if args.place:
        combos = [c for c in combos if c[0] == args.place]
    if args.problem:
        combos = [c for c in combos if c[1] == args.problem]
    if not combos:
        raise StoryError("No valid combination matches the given options.")
    place, problem, _tool = rng.choice(sorted(combos))
    hero_name = args.name or rng.choice(HERO_NAMES)
    hero_type = args.hero_type or rng.choice(CREW_TITLES)
    crewmate_type = args.crewmate_type or rng.choice(CREW_TITLES)
    return StoryParams(place=place, problem=problem, hero_name=hero_name, hero_type=hero_type, crewmate_type=crewmate_type)


def generate(params: StoryParams) -> StorySample:
    world = tell(PLACES[params.place], PROBLEMS[params.problem], params.hero_name, params.hero_type, params.crewmate_type)
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
        print(asp_program("#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        vals = asp_valid()
        print(f"{len(vals)} compatible (place, problem, tool) combos:")
        for x in vals:
            print(" ", x)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 50, 50):
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
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()

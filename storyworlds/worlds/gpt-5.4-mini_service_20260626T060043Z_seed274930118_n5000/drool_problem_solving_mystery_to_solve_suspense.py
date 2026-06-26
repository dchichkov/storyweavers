#!/usr/bin/env python3
"""
A small adventure storyworld about a mysterious drool trail, a puzzling problem,
and a careful child solving it with suspense.

The world is built to keep stories concrete and state-driven:
- a child explores a place
- something drools and leaves a clue trail
- a missing object or stuck creature creates a problem
- the hero follows clues, makes a plan, and resolves the mystery
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
@dataclass
class Entity:
    id: str
    kind: str = "thing"  # character | thing | creature
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    location: str = ""
    carried_by: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)
    traits: list[str] = field(default_factory=list)
    plural: bool = False

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman", "sister", "aunt"}
        male = {"boy", "father", "dad", "man", "brother", "uncle"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str
    surface: str
    has_hidden_paths: bool
    has_water: bool
    has_storage: bool


@dataclass
class Clue:
    label: str
    trail: str
    leads_to: str
    reason: str


@dataclass
class Problem:
    label: str
    missing: str
    blocked_by: str
    risk: str


@dataclass
class Tool:
    id: str
    label: str
    helps: str
    protects: bool = False


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.fired: set[tuple] = set()
        self.mystery: list[str] = []

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


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------
SETTINGS = {
    "dock": Setting(place="the old dock", surface="wooden boards", has_hidden_paths=True, has_water=True, has_storage=True),
    "cave": Setting(place="the sea cave", surface="slick stone", has_hidden_paths=True, has_water=True, has_storage=False),
    "attic": Setting(place="the dusty attic", surface="wide floorboards", has_hidden_paths=False, has_water=False, has_storage=True),
    "garden": Setting(place="the garden shed", surface="packed dirt", has_hidden_paths=True, has_water=False, has_storage=True),
}

PROBLEMS = {
    "lost_map": Problem(
        label="a missing map",
        missing="the map",
        blocked_by="a heavy crate",
        risk="the search could go in circles forever",
    ),
    "stuck_gate": Problem(
        label="a stuck gate",
        missing="the gate key",
        blocked_by="rusty hinges",
        risk="the path ahead could stay locked",
    ),
    "trapped_pup": Problem(
        label="a trapped pup",
        missing="the pup's whistle",
        blocked_by="a tipped basket",
        risk="the little pup could grow more frightened",
    ),
}

CLUES = {
    "drool": Clue(
        label="a drool trail",
        trail="a shiny drool trail",
        leads_to="the thing that made the mess",
        reason="something was nearby and looking for help or food",
    ),
    "scratch": Clue(
        label="scratch marks",
        trail="thin scratch marks",
        leads_to="the blocked object",
        reason="someone had tried to push or pull through the obstacle",
    ),
    "pawprints": Clue(
        label="tiny pawprints",
        trail="small pawprints",
        leads_to="the hiding place",
        reason="a nervous creature had been moving quickly there",
    ),
}

TOOLS = {
    "rope": Tool(id="rope", label="a rope", helps="pulling things out"),
    "lantern": Tool(id="lantern", label="a lantern", helps="seeing in the dark"),
    "gloves": Tool(id="gloves", label="sturdy gloves", helps="moving rough things safely", protects=True),
    "towel": Tool(id="towel", label="a clean towel", helps="wiping away sticky drool"),
}

HERO_NAMES = ["Mina", "Leo", "Aria", "Niko", "Tess", "Owen", "Maya", "Finn"]
HERO_TRAITS = ["curious", "brave", "careful", "spirited", "clever", "steady"]
HELPER_TYPES = ["dog", "fox", "cat", "goat"]


@dataclass
class StoryParams:
    place: str
    problem: str
    clue: str
    name: str
    gender: str
    trait: str
    helper: str
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
% A mystery is solvable when a clue points to the blocked thing and a tool exists.
solvable(P, C) :- problem(P), clue(C), points_to(C, P), tool(T), helps_tool(T, P).

% A valid adventure story needs a place with a clue-bearing mystery.
valid(Place, Problem, Clue) :- setting(Place), problem(Problem), clue(Clue),
                              occurs_at(Problem, Place), clue_at(Clue, Place),
                              solvable(Problem, Clue).

#show valid/3.
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid, s in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        if s.has_hidden_paths:
            lines.append(asp.fact("hidden_paths", sid))
        if s.has_water:
            lines.append(asp.fact("water", sid))
        if s.has_storage:
            lines.append(asp.fact("storage", sid))
    for pid in PROBLEMS:
        lines.append(asp.fact("problem", pid))
    for cid in CLUES:
        lines.append(asp.fact("clue", cid))
    for tid in TOOLS:
        lines.append(asp.fact("tool", tid))
    # explicit compatibility map
    lines.append(asp.fact("occurs_at", "lost_map", "dock"))
    lines.append(asp.fact("occurs_at", "lost_map", "attic"))
    lines.append(asp.fact("occurs_at", "stuck_gate", "garden"))
    lines.append(asp.fact("occurs_at", "stuck_gate", "dock"))
    lines.append(asp.fact("occurs_at", "trapped_pup", "cave"))
    lines.append(asp.fact("occurs_at", "trapped_pup", "dock"))
    lines.append(asp.fact("clue_at", "drool", "cave"))
    lines.append(asp.fact("clue_at", "drool", "dock"))
    lines.append(asp.fact("clue_at", "scratch", "garden"))
    lines.append(asp.fact("clue_at", "scratch", "attic"))
    lines.append(asp.fact("clue_at", "pawprints", "cave"))
    lines.append(asp.fact("clue_at", "pawprints", "garden"))
    lines.append(asp.fact("points_to", "drool", "trapped_pup"))
    lines.append(asp.fact("points_to", "scratch", "stuck_gate"))
    lines.append(asp.fact("points_to", "pawprints", "lost_map"))
    lines.append(asp.fact("helps_tool", "lantern", "lost_map"))
    lines.append(asp.fact("helps_tool", "rope", "stuck_gate"))
    lines.append(asp.fact("helps_tool", "gloves", "trapped_pup"))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program(""))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    python_set = set(valid_combos())
    clingo_set = set(asp_valid())
    if python_set == clingo_set:
        print(f"OK: clingo gate matches valid_combos() ({len(python_set)} combos).")
        return 0
    print("MISMATCH between clingo and Python gate:")
    if python_set - clingo_set:
        print("  only in python:", sorted(python_set - clingo_set))
    if clingo_set - python_set:
        print("  only in clingo:", sorted(clingo_set - python_set))
    return 1


# ---------------------------------------------------------------------------
# Reasonableness gate
# ---------------------------------------------------------------------------
def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for place, setting in SETTINGS.items():
        for problem_id, problem in PROBLEMS.items():
            if place not in valid_places_for_problem(problem_id):
                continue
            for clue_id, clue in CLUES.items():
                if clue_id == "drool" and problem_id != "trapped_pup":
                    continue
                if clue_id == "scratch" and problem_id != "stuck_gate":
                    continue
                if clue_id == "pawprints" and problem_id != "lost_map":
                    continue
                if place in valid_places_for_clue(clue_id):
                    combos.append((place, problem_id, clue_id))
    return combos


def valid_places_for_problem(problem_id: str) -> set[str]:
    return {
        "lost_map": {"dock", "attic"},
        "stuck_gate": {"garden", "dock"},
        "trapped_pup": {"cave", "dock"},
    }[problem_id]


def valid_places_for_clue(clue_id: str) -> set[str]:
    return {
        "drool": {"cave", "dock"},
        "scratch": {"garden", "attic"},
        "pawprints": {"cave", "garden"},
    }[clue_id]


# ---------------------------------------------------------------------------
# Story engine
# ---------------------------------------------------------------------------
def build_world(params: StoryParams) -> World:
    setting = SETTINGS[params.place]
    world = World(setting)
    hero = world.add(Entity(id=params.name, kind="character", type=params.gender, traits=["little", params.trait]))
    helper = world.add(Entity(id="helper", kind="creature", type=params.helper, label=f"a small {params.helper}", location=params.place))
    problem = PROBLEMS[params.problem]
    clue = CLUES[params.clue]
    tool = TOOLS["lantern" if params.problem == "lost_map" else "rope" if params.problem == "stuck_gate" else "gloves"]
    world.facts.update(hero=hero, helper=helper, problem=problem, clue=clue, tool=tool, place=params.place)
    return world


def introduce(world: World) -> None:
    h: Entity = world.facts["hero"]
    world.say(f"{h.id} was a little {h.memes.get('trait', '')}".strip())
    world.paragraphs[-1] = []  # reset accidental odd line


def tell_story(world: World) -> None:
    h: Entity = world.facts["hero"]
    helper: Entity = world.facts["helper"]
    problem: Problem = world.facts["problem"]
    clue: Clue = world.facts["clue"]
    tool: Tool = world.facts["tool"]
    place = world.setting.place

    h.memes["wonder"] = 1
    world.say(
        f"One misty afternoon, {h.id} went to {place} and noticed {problem.label}."
    )
    world.say(
        f"The air felt still, until {h.id} spotted {clue.trail} on the {world.setting.surface}."
    )
    world.say(
        f"It was a mystery to solve, because {clue.reason}, and the trail seemed to lead toward danger."
    )
    world.para()
    h.memes["suspense"] = 1
    world.say(
        f"{h.id} took a careful breath and followed the trail while {helper.label} padded close behind."
    )
    world.say(
        f"The clues turned once, then twice, and at last {h.id} found {clue.leads_to}."
    )
    if tool.protects:
        world.say(
            f"To move safely, {h.id} put on {tool.label} first, since the thing on the ground was sticky and wet."
        )
    else:
        world.say(
            f"{h.id} carried {tool.label} and used it to work through the trouble."
        )
    world.para()
    h.memes["joy"] = 1
    if world.facts["problem"].missing == "the pup's whistle":
        world.say(
            f"Behind a tipped basket, {h.id} found the little pup, drooling from worry but wagging at once."
        )
        world.say(
            f"{h.id} wiped the sticky drool away, lifted the basket, and handed back the whistle."
        )
        world.say(
            f"The pup barked happily, the drool trail finally made sense, and the path felt safe again."
        )
    elif world.facts["problem"].missing == "the gate key":
        world.say(
            f"Behind the rusty hinges, {h.id} found the key caught in a knot of old rope and sticky drool."
        )
        world.say(
            f"With a steady pull and a little patience, {h.id} freed it and opened the gate."
        )
        world.say(
            f"The mystery was solved, and the way ahead swung wide with a creak and a sigh."
        )
    else:
        world.say(
            f"Up in the dusty corner, {h.id} found the map tucked under a board, touched by a line of drool from a hungry little helper."
        )
        world.say(
            f"{h.id} brushed it clean, matched the marks to the room, and followed the route to the hidden chest."
        )
        world.say(
            f"In the end, the clue trail pointed true, and the old place felt less spooky and more like an adventure."
        )


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    h: Entity = f["hero"]
    p: Problem = f["problem"]
    c: Clue = f["clue"]
    return [
        f'Write a short adventure story for a young child about {h.id}, a mystery, and a drool trail.',
        f"Tell a suspenseful but gentle tale in which {h.id} notices {c.label} and solves {p.label}.",
        f'Write a child-facing adventure story that includes the word "drool" and ends with the problem fixed.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    h: Entity = f["hero"]
    p: Problem = f["problem"]
    c: Clue = f["clue"]
    helper: Entity = f["helper"]
    place = world.setting.place
    return [
        QAItem(
            question=f"Where did {h.id} find the first clue in the story?",
            answer=f"{h.id} found {c.trail} at {place}. It was the clue that started the search.",
        ),
        QAItem(
            question=f"What problem was {h.id} trying to solve?",
            answer=f"{h.id} was trying to solve {p.label}. The mystery mattered because {p.risk}.",
        ),
        QAItem(
            question=f"Who stayed close while {h.id} followed the clue trail?",
            answer=f"{helper.label} stayed close while {h.id} followed the clues. The helper made the search feel braver.",
        ),
        QAItem(
            question=f"Why did the drool trail matter?",
            answer=f"The drool trail mattered because it pointed toward the answer. It showed where the hidden trouble began.",
        ),
        QAItem(
            question=f"How did the story end?",
            answer=f"The story ended with the problem fixed, the mystery solved, and the place feeling safe again.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is drool?",
            answer="Drool is wet saliva that can drip from an animal or a tired mouth and leave shiny marks.",
        ),
        QAItem(
            question="Why can a lantern help during a mystery?",
            answer="A lantern helps because it shines light into dark places, making tiny clues easier to see.",
        ),
        QAItem(
            question="What do sturdy gloves help with?",
            answer="Sturdy gloves help protect your hands when you need to move rough, dirty, or sticky things.",
        ),
    ]


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
    lines.append("== (3) World-knowledge questions ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for e in world.entities.values():
        bits = []
        if e.location:
            bits.append(f"location={e.location}")
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        if e.traits:
            bits.append(f"traits={e.traits}")
        lines.append(f"  {e.id} ({e.kind}/{e.type}) {' '.join(bits)}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Params / sampling
# ---------------------------------------------------------------------------
def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    combos = valid_combos()
    if args.place:
        combos = [c for c in combos if c[0] == args.place]
    if args.problem:
        combos = [c for c in combos if c[1] == args.problem]
    if args.clue:
        combos = [c for c in combos if c[2] == args.clue]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, problem, clue = rng.choice(sorted(combos))
    name = args.name or rng.choice(HERO_NAMES)
    gender = args.gender or rng.choice(["girl", "boy"])
    trait = args.trait or rng.choice(HERO_TRAITS)
    helper = args.helper or rng.choice(HELPER_TYPES)
    return StoryParams(place=place, problem=problem, clue=clue, name=name, gender=gender, trait=trait, helper=helper)


def generate(params: StoryParams) -> StorySample:
    world = build_world(params)
    tell_story(world)
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


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
CURATED = [
    StoryParams(place="cave", problem="trapped_pup", clue="drool", name="Mina", gender="girl", trait="brave", helper="dog"),
    StoryParams(place="garden", problem="stuck_gate", clue="scratch", name="Leo", gender="boy", trait="careful", helper="fox"),
    StoryParams(place="attic", problem="lost_map", clue="pawprints", name="Tess", gender="girl", trait="clever", helper="cat"),
]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Adventure storyworld with drool, mystery, suspense, and problem solving.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--problem", choices=PROBLEMS)
    ap.add_argument("--clue", choices=CLUES)
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--trait", choices=HERO_TRAITS)
    ap.add_argument("--helper", choices=HELPER_TYPES)
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


def asp_show_program() -> str:
    return asp_program("#show valid/3.")


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_show_program())
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        model = asp.one_model(asp_show_program())
        vals = sorted(set(asp.atoms(model, "valid")))
        print(f"{len(vals)} compatible (place, problem, clue) combos:\n")
        for place, problem, clue in vals:
            print(f"  {place:8} {problem:12} {clue:10}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        for i in range(max(args.n * 50, 50)):
            if len(samples) >= args.n:
                break
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
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
            header = f"### {p.name}: {p.problem} at {p.place} ({p.clue})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260624T090150Z_seed197402754_n1000/lift_vegetable_garden_misunderstanding_conflict_teamwork_detective.py
==============================================================================================================================

A small detective-story world set in a vegetable garden.

Premise:
- A young detective notices a strange problem in the vegetable garden.
- A misunderstanding creates conflict between two characters.
- Teamwork helps them lift something heavy and solve the mystery.

The world simulates physical state in meters and emotional state in memes.
The prose is driven by the simulated events rather than being a fixed template.
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

THRESHOLD = 1.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    traits: list[str] = field(default_factory=list)
    owner: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def __post_init__(self):
        if self.meters is None:
            self.meters = {}
        if self.memes is None:
            self.memes = {}

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "woman", "mother", "sister"}
        male = {"boy", "man", "father", "brother"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class Setting:
    place: str = "the vegetable garden"
    affords: set[str] = field(default_factory=set)


@dataclass
class Problem:
    id: str
    clue: str
    verb: str
    noun: str
    heavy: bool = False
    solve_by_lift: bool = False


@dataclass
class Tool:
    id: str
    label: str
    action: str
    helps: set[str] = field(default_factory=set)
    covers: set[str] = field(default_factory=set)


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
        self.facts: dict = {}

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str) -> Entity:
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
        w = World(self.setting)
        w.entities = copy.deepcopy(self.entities)
        w.paragraphs = [[]]
        w.fired = set(self.fired)
        return w


def _r_conflict(world: World) -> list[str]:
    out = []
    detective = world.entities.get("detective")
    gardener = world.entities.get("gardener")
    if not detective or not gardener:
        return out
    if detective.memes.get("blame", 0) < THRESHOLD:
        return out
    if gardener.memes.get("hurt", 0) < THRESHOLD:
        return out
    sig = ("conflict",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    detective.memes["conflict"] = detective.memes.get("conflict", 0) + 1
    gardener.memes["conflict"] = gardener.memes.get("conflict", 0) + 1
    out.append("Their voices sharpened like little garden stakes.")
    return out


def _r_teamwork(world: World) -> list[str]:
    out = []
    rock = world.entities.get("rock")
    detective = world.entities.get("detective")
    gardener = world.entities.get("gardener")
    if not rock or not detective or not gardener:
        return out
    if detective.memes.get("apology", 0) < THRESHOLD:
        return out
    if gardener.memes.get("willing", 0) < THRESHOLD:
        return out
    if rock.meters.get("lifted", 0) >= THRESHOLD:
        return out
    sig = ("teamwork",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    rock.meters["lifted"] = 1
    detective.meters["effort"] = detective.meters.get("effort", 0) + 1
    gardener.meters["effort"] = gardener.meters.get("effort", 0) + 1
    detective.memes["relief"] = detective.memes.get("relief", 0) + 1
    gardener.memes["relief"] = gardener.memes.get("relief", 0) + 1
    out.append("Together they lifted the heavy rock.")
    return out


def propagate(world: World, narrate: bool = True) -> list[str]:
    out: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in (_r_conflict, _r_teamwork):
            lines = rule(world)
            if lines:
                changed = True
                out.extend(lines)
    if narrate:
        for line in out:
            world.say(line)
    return out


def detect_misunderstanding(world: World, detective: Entity, gardener: Entity, problem: Problem) -> None:
    detective.memes["curious"] = detective.memes.get("curious", 0) + 1
    world.say(
        f"{detective.id} was a little detective who watched every row in the {world.setting.place}. "
        f"{detective.pronoun('subject').capitalize()} noticed something odd near the carrots."
    )
    world.say(
        f"{detective.id} thought {gardener.pronoun('subject')} had moved {problem.noun}, "
        f"but the truth was different."
    )


def accusation(world: World, detective: Entity, gardener: Entity) -> None:
    detective.memes["blame"] = detective.memes.get("blame", 0) + 1
    gardener.memes["hurt"] = gardener.memes.get("hurt", 0) + 1
    world.say(
        f"{detective.id} frowned and said, \"You must have done it.\" "
        f"{gardener.id} looked shocked and hurt."
    )
    propagate(world, narrate=True)


def reveal_misunderstanding(world: World, detective: Entity, gardener: Entity, problem: Problem) -> None:
    detective.memes["understanding"] = detective.memes.get("understanding", 0) + 1
    gardener.memes["willing"] = gardener.memes.get("willing", 0) + 1
    world.say(
        f"Then they saw the clue: {problem.clue}. "
        f"It was not a trick at all; it was a misunderstanding."
    )
    world.say(
        f"{detective.id} turned red and said sorry. {gardener.id} softened right away."
    )
    detective.memes["apology"] = detective.memes.get("apology", 0) + 1


def lift_reveal(world: World, detective: Entity, gardener: Entity, tool: Tool, problem: Problem) -> None:
    world.say(
        f"They both grabbed the {tool.label}. {tool.action.capitalize()}, they could lift what was hiding underneath."
    )
    world.say(
        f"Under the {problem.noun}, they found the missing seed packet."
    )


def resolve(world: World, detective: Entity, gardener: Entity, problem: Problem, tool: Tool) -> None:
    world.say(
        f"The mystery was solved at last. {detective.id} and {gardener.id} worked side by side, "
        f"and the garden felt calm again."
    )
    world.say(
        f"By the end, the heavy {problem.noun} was moved, the missing packet was back in place, "
        f"and the two friends were smiling in the green rows."
    )


SETTING = Setting(place="the vegetable garden", affords={"detect", "accuse", "apologize", "lift", "solve"})

PROBLEMS = {
    "rock": Problem(
        id="rock",
        clue="a trail of muddy fingerprints on the side of the rock",
        verb="hide",
        noun="rock",
        heavy=True,
        solve_by_lift=True,
    ),
    "crate": Problem(
        id="crate",
        clue="a bent corner of a crate and a little line of soil",
        verb="cover",
        noun="crate",
        heavy=True,
        solve_by_lift=True,
    ),
}

TOOLS = {
    "bar": Tool(
        id="bar",
        label="garden bar",
        action="with a careful heave",
        helps={"rock", "crate"},
    ),
    "stick": Tool(
        id="stick",
        label="digging stick",
        action="with a steady push and a shared pull",
        helps={"crate"},
    ),
}

NAMES = ["Mia", "Noah", "Lena", "Theo", "Ruby", "Owen", "Ivy", "Eli"]
GARDENER_NAMES = ["Ms. Green", "Mr. Reed", "Aunt June", "Uncle Clay"]
TRAITS = ["sharp-eyed", "patient", "brave", "curious", "careful"]


@dataclass
class StoryParams:
    problem: str
    tool: str
    detective_name: str
    gardener_name: str
    trait: str
    seed: Optional[int] = None


def valid_combos() -> list[tuple[str, str]]:
    combos = []
    for pid, prob in PROBLEMS.items():
        if prob.solve_by_lift:
            for tid, tool in TOOLS.items():
                if pid in tool.helps:
                    combos.append((pid, tid))
    return combos


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        "Write a short detective story set in a vegetable garden with a misunderstanding, a conflict, and teamwork.",
        f"Tell a child-friendly mystery about {f['detective'].id} in the vegetable garden that ends with a heavy thing being lifted.",
        f"Write a gentle garden detective story where a misunderstanding causes conflict before teamwork solves the case.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    detective: Entity = f["detective"]
    gardener: Entity = f["gardener"]
    problem: Problem = f["problem"]
    tool: Tool = f["tool"]
    return [
        QAItem(
            question=f"Who was the detective in the garden story?",
            answer=f"The detective was {detective.id}, a {f['trait']} child who noticed the clue in the vegetable garden.",
        ),
        QAItem(
            question=f"Why did {detective.id} and {gardener.id} argue at first?",
            answer=f"They argued because {detective.id} misunderstood the clue and thought {gardener.id} had hidden the {problem.noun}.",
        ),
        QAItem(
            question=f"How did they solve the mystery?",
            answer=f"They apologized to each other and used the {tool.label} to lift the {problem.noun}, which revealed the missing seed packet.",
        ),
        QAItem(
            question=f"What changed by the end of the story?",
            answer=f"The conflict faded, the misunderstanding was cleared up, and the two characters worked together in the vegetable garden.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a detective?",
            answer="A detective is a person who looks for clues and tries to solve a mystery.",
        ),
        QAItem(
            question="Why do gardens need teamwork?",
            answer="Gardens often need teamwork because some jobs, like moving heavy things or pulling weeds, are easier when people help each other.",
        ),
        QAItem(
            question="What is a misunderstanding?",
            answer="A misunderstanding happens when someone thinks the wrong thing about what is going on.",
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
    for e in world.entities.values():
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        lines.append(f"  {e.id:10} ({e.type:9}) meters={meters} memes={memes}")
    lines.append(f"  fired rules: {sorted(n for n, *_ in world.fired)}")
    return "\n".join(lines)


ASP_RULES = r"""
problem(P) :- problem_id(P).
tool(T) :- tool_id(T).
compatible(P,T) :- problem(P), tool(T), helps(T,P).
valid_story(P,T) :- compatible(P,T).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid in PROBLEMS:
        lines.append(asp.fact("problem_id", pid))
    for tid, tool in TOOLS.items():
        lines.append(asp.fact("tool_id", tid))
        for p in sorted(tool.helps):
            lines.append(asp.fact("helps", tid, p))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show compatible/2."))
    return sorted(set(asp.atoms(model, "compatible")))


def asp_verify() -> int:
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    if py - cl:
        print("  only in python:", sorted(py - cl))
    if cl - py:
        print("  only in clingo:", sorted(cl - py))
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Detective story world in a vegetable garden.")
    ap.add_argument("--problem", choices=PROBLEMS)
    ap.add_argument("--tool", choices=TOOLS)
    ap.add_argument("--detective-name", choices=NAMES)
    ap.add_argument("--gardener-name", choices=GARDENER_NAMES)
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


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    combos = valid_combos()
    if args.problem and args.tool:
        if (args.problem, args.tool) not in combos:
            raise StoryError("That tool cannot solve that garden mystery.")
    filtered = [
        (p, t) for p, t in combos
        if args.problem is None or p == args.problem
        if args.tool is None or t == args.tool
    ]
    if not filtered:
        raise StoryError("No valid combination matches the given options.")
    problem, tool = rng.choice(sorted(filtered))
    detective_name = args.detective_name or rng.choice(NAMES)
    gardener_name = args.gardener_name or rng.choice(GARDENER_NAMES)
    trait = args.trait or rng.choice(TRAITS)
    return StoryParams(problem=problem, tool=tool, detective_name=detective_name,
                       gardener_name=gardener_name, trait=trait)


def generate(params: StoryParams) -> StorySample:
    world = World(SETTING)
    detective = world.add(Entity(id=params.detective_name, kind="character", type="girl" if params.detective_name in {"Mia", "Lena", "Ruby", "Ivy"} else "boy", traits=[params.trait]))
    gardener = world.add(Entity(id=params.gardener_name, kind="character", type="woman" if params.gardener_name.startswith(("Ms.", "Aunt")) else "man"))
    problem = PROBLEMS[params.problem]
    tool = TOOLS[params.tool]
    rock = world.add(Entity(id="rock", type="thing", label=problem.noun))
    world.facts.update(detective=detective, gardener=gardener, problem=problem, tool=tool, trait=params.trait)
    world.say(
        f"In the vegetable garden, {detective.id} was a {params.trait} little detective. "
        f"{detective.pronoun('subject').capitalize()} loved clues almost as much as tomatoes loved sunshine."
    )
    world.say(
        f"One morning, {detective.id} found a strange sign near the beds: {problem.clue}."
    )
    world.para()
    detect_misunderstanding(world, detective, gardener, problem)
    accusation(world, detective, gardener)
    world.para()
    reveal_misunderstanding(world, detective, gardener, problem)
    lift_reveal(world, detective, gardener, tool, problem)
    rock.meters["lifted"] = rock.meters.get("lifted", 0)
    propagate(world, narrate=True)
    world.para()
    resolve(world, detective, gardener, problem, tool)
    world.facts["resolved"] = True
    story = world.render()
    return StorySample(
        params=params,
        story=story,
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


CURATED = [
    StoryParams(problem="rock", tool="bar", detective_name="Mia", gardener_name="Ms. Green", trait="curious"),
    StoryParams(problem="crate", tool="stick", detective_name="Noah", gardener_name="Mr. Reed", trait="sharp-eyed"),
]


def asp_program_text(show: str) -> str:
    return asp_program(show)


def asp_valid_stories() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show compatible/2."))
    return sorted(set(asp.atoms(model, "compatible")))


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program_text("#show compatible/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (problem, tool) combos:\n")
        for p, t in combos:
            print(f"  {p:8} {t}")
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
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()

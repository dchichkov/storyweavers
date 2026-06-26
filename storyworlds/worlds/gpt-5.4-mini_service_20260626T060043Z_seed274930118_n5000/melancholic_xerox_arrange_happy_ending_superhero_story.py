#!/usr/bin/env python3
"""
A standalone storyworld script for a small superhero-style domain.

Premise:
- A young hero feels melancholic because an important poster, map, or note has
  been lost.
- A friendly helper uses a xerox machine to copy a missing clue.
- The team arranges the copied pages into a helpful plan.
- A happy ending follows when the hero saves the day and feels better.

The world is intentionally small and constraint-checked: only plausible
hero-plus-problem combinations are generated, and invalid explicit choices raise
StoryError.
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
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    carried_by: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "woman", "mother", "heroine"}
        male = {"boy", "man", "father", "hero"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class Hero:
    name: str
    type: str
    trait: str
    emblem: str
    power: str
    cape: str


@dataclass
class Problem:
    id: str
    thing: str
    phrase: str
    location: str
    loss_reason: str
    clue: str


@dataclass
class Helper:
    name: str
    type: str
    job: str


@dataclass
class Tool:
    id: str
    label: str
    verb: str
    result: str


class World:
    def __init__(self) -> None:
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.risk: float = 0.0
        self.fired: set[tuple] = set()

    def add(self, e: Entity) -> Entity:
        self.entities[e.id] = e
        return e

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


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------

HEROES = {
    "Nova": Hero("Nova", "girl", "brave", "star badge", "quick leaps", "blue cape"),
    "Max": Hero("Max", "boy", "gentle", "light shield", "careful watch", "red cape"),
    "Iris": Hero("Iris", "girl", "clever", "silver mask", "fast thinking", "yellow cape"),
    "Toby": Hero("Toby", "boy", "kind", "tiny hammer", "helpful hands", "green cape"),
}

HELPERS = {
    "Pip": Helper("Pip", "boy", "assistant"),
    "Mina": Helper("Mina", "girl", "assistant"),
    "Rook": Helper("Rook", "man", "mechanic"),
    "Dot": Helper("Dot", "woman", "operator"),
}

PROBLEMS = {
    "missing_map": Problem(
        id="missing_map",
        thing="map",
        phrase="a hand-drawn city map",
        location="the tower desk",
        loss_reason="blown away by the wind",
        clue="a faint line on the copier glass",
    ),
    "missing_notice": Problem(
        id="missing_notice",
        thing="notice",
        phrase="an important rescue notice",
        location="the community board",
        loss_reason="torn down during the storm",
        clue="a corner with a red stamp",
    ),
    "missing_plan": Problem(
        id="missing_plan",
        thing="plan",
        phrase="a bright rescue plan",
        location="the hero table",
        loss_reason="smudged by rain",
        clue="a neat star in the margin",
    ),
}

TOOLS = {
    "xerox": Tool(
        id="xerox",
        label="xerox machine",
        verb="copy",
        result="fresh copies",
    ),
    "tape": Tool(
        id="tape",
        label="clear tape",
        verb="arrange",
        result="a neat row",
    ),
    "pinboard": Tool(
        id="pinboard",
        label="pinboard",
        verb="arrange",
        result="an organized plan",
    ),
}

PLACES = {
    "tower": "the hero tower",
    "workshop": "the bright workshop",
    "roof": "the rooftop lookout",
    "hall": "the busy hall",
}

TRAITS = ["melancholic", "thoughtful", "patient", "bright", "curious", "steady"]


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------

ASP_RULES = r"""
% A problem is worth solving when the hero is sad about a missing thing.
needs_help(H, P) :- hero(H), problem(P), sad_about(H, P).

% A xerox machine helps when the missing thing can be copied into a clue.
can_copy(P) :- problem(P), copyable(P).

% A happy ending happens when the hero gets a useful copy and the plan is arranged.
happy_ending(H, P) :- needs_help(H, P), can_copy(P), arranged(P).

#show needs_help/2.
#show happy_ending/2.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for hid in HEROES:
        lines.append(asp.fact("hero", hid))
    for pid, pr in PROBLEMS.items():
        lines.append(asp.fact("problem", pid))
        lines.append(asp.fact("missing_thing", pid, pr.thing))
        lines.append(asp.fact("copyable", pid))
    for tid in TOOLS:
        lines.append(asp.fact("tool", tid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show happy_ending/2."))
    atoms = set(asp.atoms(model, "happy_ending"))
    expected = {(hid, pid) for hid in HEROES for pid in PROBLEMS}
    if atoms:
        print(f"OK: ASP produced {len(atoms)} happy-ending atoms.")
        return 0
    print("MISMATCH: ASP produced no happy-ending atoms.")
    return 1


# ---------------------------------------------------------------------------
# Story parameters
# ---------------------------------------------------------------------------

@dataclass
class StoryParams:
    hero: str
    helper: str
    problem: str
    place: str
    tool: str
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# Utilities
# ---------------------------------------------------------------------------

def valid_combo(hero: Hero, problem: Problem, tool: Tool) -> bool:
    if problem.id == "missing_map":
        return tool.id == "xerox"
    if problem.id == "missing_notice":
        return tool.id in {"xerox", "pinboard"}
    if problem.id == "missing_plan":
        return tool.id in {"xerox", "tape", "pinboard"}
    return False


def valid_combos() -> list[tuple[str, str, str]]:
    out = []
    for hid, hero in HEROES.items():
        for pid, problem in PROBLEMS.items():
            for tid, tool in TOOLS.items():
                if valid_combo(hero, problem, tool):
                    out.append((hid, pid, tid))
    return out


def explain_rejection(hero: Hero, problem: Problem, tool: Tool) -> str:
    return (
        f"(No story: {tool.label} does not fit this rescue. "
        f"For {problem.phrase}, the team needs a tool that can make a useful copy "
        f"or help arrange the clue into a plan.)"
    )


def pick_name(rng: random.Random, hero_id: str) -> Hero:
    return HEROES[hero_id]


def pick_helper(rng: random.Random) -> Helper:
    return HELPERS[rng.choice(sorted(HELPERS))]


# ---------------------------------------------------------------------------
# Story generation
# ---------------------------------------------------------------------------

def build_world(params: StoryParams) -> World:
    world = World()
    hero = HEROES[params.hero]
    helper = HELPERS[params.helper]
    problem = PROBLEMS[params.problem]
    tool = TOOLS[params.tool]

    h = world.add(Entity(id=hero.name, kind="character", type=hero.type, label=hero.name))
    a = world.add(Entity(id=helper.name, kind="character", type=helper.type, label=helper.name))
    p = world.add(Entity(id=problem.thing, type="thing", label=problem.thing, phrase=problem.phrase, owner=hero.name))
    t = world.add(Entity(id=tool.id, type="thing", label=tool.label, phrase=tool.label, owner=helper.name))
    t.carried_by = helper.name

    world.facts.update(hero=h, helper=a, problem=p, tool=t, hero_cfg=hero, helper_cfg=helper, problem_cfg=problem, tool_cfg=tool)

    world.say(
        f"{hero.name} was a {hero.trait} hero with {hero.emblem} and a {hero.cape}."
    )
    world.say(
        f"One morning, {hero.name} felt melancholic because {problem.phrase} had been {problem.loss_reason}."
    )
    world.say(
        f"{hero.name} needed that missing {problem.thing} to keep the day safe and bright."
    )

    world.para()
    world.say(
        f"{helper.name} arrived at {world.facts.get('place_name', 'the hero tower')} with a {tool.label}."
    )
    world.say(
        f"Together they looked at the dusty clue and decided to xerox it first, so nothing important would be lost again."
    )
    world.say(
        f"The machine hummed, and soon it made clean copies with {problem.clue} still visible."
    )

    world.para()
    world.say(
        f"Then they used tape and the pinboard to arrange the copies into a simple rescue path."
    )
    world.say(
        f"{hero.name} followed the copied clues, found the missing {problem.thing}, and fixed the problem before sunset."
    )
    world.say(
        f"{hero.name} smiled, the melancholic feeling faded, and the city felt safe again."
    )

    world.facts["resolved"] = True
    world.facts["happy_ending"] = True
    return world


# ---------------------------------------------------------------------------
# QA
# ---------------------------------------------------------------------------

def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero_cfg"]
    problem = f["problem_cfg"]
    return [
        f'Write a short superhero story for a young child that includes the word "melancholic" and a xerox machine.',
        f"Tell a gentle superhero story where {hero.name} feels melancholic because {problem.phrase} is missing, and a helper arranges a copied clue.",
        f"Write a happy-ending story about a hero, a xerox copy, and a rescue plan that gets arranged step by step.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero_cfg"]
    helper = f["helper_cfg"]
    problem = f["problem_cfg"]
    tool = f["tool_cfg"]
    return [
        QAItem(
            question=f"Why did {hero.name} feel melancholic at the start?",
            answer=f"{hero.name} felt melancholic because {problem.phrase} had been {problem.loss_reason}, and the missing thing made the day feel heavy.",
        ),
        QAItem(
            question=f"What did {helper.name} use to help {hero.name}?",
            answer=f"{helper.name} used a {tool.label} to xerox the clue and make fresh copies that could be arranged into a rescue plan.",
        ),
        QAItem(
            question=f"How did the story end for {hero.name}?",
            answer=f"It ended happily: {hero.name} found the missing {problem.thing}, fixed the trouble, and smiled again.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does a xerox machine do?",
            answer="A xerox machine makes copies of pages or pictures so people can read or use them again.",
        ),
        QAItem(
            question="What does it mean to arrange something?",
            answer="To arrange something means to put things in a useful order so they are easier to use or understand.",
        ),
        QAItem(
            question="What is a happy ending?",
            answer="A happy ending is when the problem gets solved and the characters feel safe, glad, or peaceful at the end.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== Prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== Story QA ==")
    for q in sample.story_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    lines.append("")
    lines.append("== World QA ==")
    for q in sample.world_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Superhero storyworld with a melancholic xerox rescue and a happy ending.")
    ap.add_argument("--hero", choices=sorted(HEROES))
    ap.add_argument("--helper", choices=sorted(HELPERS))
    ap.add_argument("--problem", choices=sorted(PROBLEMS))
    ap.add_argument("--place", choices=sorted(PLACES))
    ap.add_argument("--tool", choices=sorted(TOOLS))
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
    if args.hero:
        combos = [c for c in combos if c[0] == args.hero]
    if args.problem:
        combos = [c for c in combos if c[1] == args.problem]
    if args.tool:
        combos = [c for c in combos if c[2] == args.tool]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    hero_id, problem_id, tool_id = rng.choice(sorted(combos))
    hero = HEROES[hero_id]
    problem = PROBLEMS[problem_id]
    tool = TOOLS[tool_id]
    if not valid_combo(hero, problem, tool):
        raise StoryError(explain_rejection(hero, problem, tool))

    helper = args.helper or rng.choice(sorted(HELPERS))
    place = args.place or rng.choice(sorted(PLACES))
    return StoryParams(hero=hero_id, helper=helper, problem=problem_id, place=place, tool=tool_id)


def generate(params: StoryParams) -> StorySample:
    world = build_world(params)
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
        print()
        print("--- world trace ---")
        for e in sample.world.entities.values():
            bits = []
            if e.label:
                bits.append(f"label={e.label}")
            if e.phrase:
                bits.append(f"phrase={e.phrase}")
            if e.carried_by:
                bits.append(f"carried_by={e.carried_by}")
            if e.meters:
                bits.append(f"meters={e.meters}")
            if e.memes:
                bits.append(f"memes={e.memes}")
            print(f"{e.id} ({e.type}) " + " ".join(bits))
    if qa:
        print()
        print(format_qa(sample))


# ---------------------------------------------------------------------------
# ASP support
# ---------------------------------------------------------------------------

def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show needs_help/2.\n#show happy_ending/2."))
    return sorted(set(asp.atoms(model, "happy_ending")))


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show needs_help/2.\n#show happy_ending/2."))
        return

    if args.verify:
        sys.exit(asp_verify())

    if args.asp:
        import asp
        model = asp.one_model(asp_program("#show happy_ending/2."))
        atoms = sorted(set(asp.atoms(model, "happy_ending")))
        print(f"{len(atoms)} happy-ending combinations:")
        for hid, pid in atoms:
            print(f"  {hid} + {pid}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        combos = valid_combos()
        for i, (hid, pid, tid) in enumerate(combos):
            params = StoryParams(
                hero=hid,
                helper=sorted(HELPERS)[i % len(HELPERS)],
                problem=pid,
                place=sorted(PLACES)[i % len(PLACES)],
                tool=tid,
                seed=base_seed + i,
            )
            samples.append(generate(params))
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
            seed = base_seed + i
            i += 1
            rng = random.Random(seed)
            try:
                params = resolve_params(args, rng)
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

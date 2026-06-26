#!/usr/bin/env python3
"""
storyworlds/worlds/crunch_dim_bad_ending_teamwork_problem_solving.py
===================================================================

A small nursery-rhyme storyworld about a crunch-dim little place where a
problem can be solved by teamwork, or end a bit badly if the fix is not found.

The seed phrase "crunch-dim" is treated as the story's invented mood-word:
a place that is dim, crumbly, and full of crunchy little sounds underfoot.

Story shape:
- a tiny cast
- a concrete problem
- a teamwork plan
- a problem-solving turn
- an ending image that proves what changed

This world keeps the prose simple and rhyme-like, but the state model still
drives the narrative.
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

# Story-state thresholds.
THRESHOLD = 1.0


# ---------------------------------------------------------------------------
# World model
# ---------------------------------------------------------------------------
@dataclass
class Entity:
    id: str
    kind: str = "thing"  # "character" | "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    worn_by: Optional[str] = None
    carried_by: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "woman", "sister"}
        male = {"boy", "father", "man", "brother"}
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
    light: str
    crunch: str
    affords: set[str] = field(default_factory=set)


@dataclass
class Problem:
    id: str
    verb: str
    gerund: str
    rush: str
    obstruction: str
    fix: str
    risk: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Tool:
    id: str
    label: str
    phrase: str
    helps: set[str]
    cost: str
    plural: bool = False


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.in_problem: bool = False
        self.problem_key: str = ""

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
    "attic": Setting(place="the attic", light="dim", crunch="crunch", affords={"box", "rope"}),
    "cellar": Setting(place="the cellar", light="dim", crunch="crunch", affords={"box", "rope"}),
    "loft": Setting(place="the loft", light="dim", crunch="crunch", affords={"box", "rope"}),
    "shed": Setting(place="the shed", light="dim", crunch="crunch", affords={"rope", "ladder"}),
}

PROBLEMS = {
    "stuck_cart": Problem(
        id="stuck_cart",
        verb="pull the cart free",
        gerund="pulling the cart free",
        rush="tug the cart along",
        obstruction="stuck under a beam",
        fix="use a rope and two helpers",
        risk="the cart may tip and spill the jars",
        tags={"cart", "rope", "teamwork"},
    ),
    "fallen_box": Problem(
        id="fallen_box",
        verb="lift the box back up",
        gerund="lifting the box back up",
        rush="hoist the box to the shelf",
        obstruction="too heavy for one small pair of hands",
        fix="use a ladder and a steady hand",
        risk="the jars may crack on the floor",
        tags={"box", "ladder", "teamwork"},
    ),
    "snagged_string": Problem(
        id="snagged_string",
        verb="untie the string",
        gerund="untieing the string",
        rush="tug the string loose",
        obstruction="caught on a nail in the wall",
        fix="use scissors and careful counting",
        risk="the bag may tear open",
        tags={"string", "careful", "problem_solving"},
    ),
}

TOOLS = [
    Tool(
        id="rope",
        label="a rope",
        phrase="a sturdy rope",
        helps={"stuck_cart"},
        cost="a little tug and two kind hands",
    ),
    Tool(
        id="ladder",
        label="a ladder",
        phrase="a small ladder",
        helps={"fallen_box"},
        cost="a careful climb and one steady friend",
    ),
    Tool(
        id="scissors",
        label="scissors",
        phrase="little scissors",
        helps={"snagged_string"},
        cost="small snips and patient eyes",
        plural=True,
    ),
    Tool(
        id="lantern",
        label="a lantern",
        phrase="a bright lantern",
        helps={"stuck_cart", "fallen_box", "snagged_string"},
        cost="a warm glow and a calmer look",
    ),
]

NAMES = ["Mia", "Finn", "Nora", "Toby", "Lily", "Theo", "Pip", "Ava"]
KINDS = ["mouse", "rabbit", "bear", "fox", "duck"]
TRAITS = ["tiny", "brave", "cheery", "curious", "busy"]


# ---------------------------------------------------------------------------
# Story parameters
# ---------------------------------------------------------------------------
@dataclass
class StoryParams:
    place: str
    problem: str
    name1: str
    kind1: str
    trait1: str
    name2: str
    kind2: str
    trait2: str
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
problem_at_risk(P) :- problem(P).
teamwork_needed(P) :- problem_at_risk(P), fix_needs(P, tool(_)).
solvable(P) :- problem(P), has_tool(P).

# "bad ending" in this world means the problem remains unresolved.
bad_ending(P) :- problem(P), not solvable(P).
good_ending(P) :- problem(P), solved(P).

valid_story(Place, P) :- setting(Place), problem(P), in_setting(P, Place).
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for sid, s in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        lines.append(asp.fact("place_name", sid, s.place))
        lines.append(asp.fact("light", sid, s.light))
        for a in sorted(s.affords):
            lines.append(asp.fact("affords", sid, a))
    for pid, p in PROBLEMS.items():
        lines.append(asp.fact("problem", pid))
        lines.append(asp.fact("in_setting", pid, "attic"))
        lines.append(asp.fact("obstruction", pid, p.obstruction))
        lines.append(asp.fact("risk", pid, p.risk))
        for t in sorted(p.tags):
            lines.append(asp.fact("tag", pid, t))
    for t in TOOLS:
        lines.append(asp.fact("tool", t.id))
        for p in sorted(t.helps):
            lines.append(asp.fact("helps", t.id, p))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_stories() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("#show valid_story/2."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    # Python gate is intentionally simple: every problem has at least one tool.
    python_set = {(place, pid) for place in SETTINGS for pid in PROBLEMS if valid_combo(place, pid)}
    clingo_set = set(asp_valid_stories())
    if python_set == clingo_set:
        print(f"OK: clingo gate matches Python gate ({len(clingo_set)} stories).")
        return 0
    print("MISMATCH between clingo and Python gates:")
    if clingo_set - python_set:
        print("  only in clingo:", sorted(clingo_set - python_set))
    if python_set - clingo_set:
        print("  only in python:", sorted(python_set - clingo_set))
    return 1


# ---------------------------------------------------------------------------
# World helpers
# ---------------------------------------------------------------------------
def valid_combo(place: str, problem_id: str) -> bool:
    if place not in SETTINGS or problem_id not in PROBLEMS:
        return False
    if place in {"attic", "cellar", "loft", "shed"}:
        return True
    return False


def choose_tool(problem: Problem) -> Optional[Tool]:
    for tool in TOOLS:
        if problem.id in tool.helps:
            return tool
    return None


def rhyme_open(setting: Setting) -> str:
    return f"In {setting.place}, so dim and trim, the floor went {setting.crunch}, crunch-dim."


def introduce(world: World, a: Entity, b: Entity) -> None:
    world.say(
        f"{a.id} was a {a.trait if hasattr(a, 'trait') else 'tiny'} {a.type} who liked to help, "
        f"and {b.id} was a {b.trait if hasattr(b, 'trait') else 'tiny'} {b.type} who liked to help too."
    )


def run_problem(world: World, hero1: Entity, hero2: Entity, problem: Problem) -> None:
    world.in_problem = True
    world.problem_key = problem.id
    hero1.memes["worry"] = hero1.memes.get("worry", 0.0) + 1
    hero2.memes["worry"] = hero2.memes.get("worry", 0.0) + 1
    world.say(
        f"Then they found {problem.obstruction}, and the little thing would not budge."
    )
    world.say(
        f"They tried to {problem.rush}, but the path gave only a {world.setting.crunch}, crunch-dim sound."
    )


def try_teamwork(world: World, hero1: Entity, hero2: Entity, problem: Problem) -> Optional[Tool]:
    tool = choose_tool(problem)
    if tool is None:
        return None
    hero1.memes["hope"] = hero1.memes.get("hope", 0.0) + 1
    hero2.memes["hope"] = hero2.memes.get("hope", 0.0) + 1
    world.say(
        f"Then {hero1.id} had a thought, and {hero2.id} clapped in time: "
        f'"Let us use {tool.phrase}!"'
    )
    return tool


def solve(world: World, hero1: Entity, hero2: Entity, problem: Problem, tool: Tool) -> None:
    hero1.memes["joy"] = hero1.memes.get("joy", 0.0) + 1
    hero2.memes["joy"] = hero2.memes.get("joy", 0.0) + 1
    world.facts["solved"] = True
    world.say(
        f"Together they used {tool.label}, and {tool.cost}. "
        f"The {problem.id.replace('_', ' ')} was finally fixed."
    )
    world.say(
        f"At the end, {hero1.id} and {hero2.id} stood side by side, and the dim old place felt less alone."
    )


def bad_ending(world: World, hero1: Entity, hero2: Entity, problem: Problem) -> None:
    world.facts["solved"] = False
    hero1.memes["sad"] = hero1.memes.get("sad", 0.0) + 1
    hero2.memes["sad"] = hero2.memes.get("sad", 0.0) + 1
    world.say(
        f"They tried and tried, but nothing held. The little helpers had to go home, and the {problem.id.replace('_', ' ')} stayed stuck."
    )
    world.say(
        f"So the story ended with quiet feet and a dim small sigh in the crunch-dim room."
    )


def tell(setting: Setting, problem: Problem, name1: str, kind1: str, trait1: str, name2: str, kind2: str, trait2: str) -> World:
    world = World(setting)
    hero1 = world.add(Entity(id=name1, kind="character", type=kind1))
    hero2 = world.add(Entity(id=name2, kind="character", type=kind2))
    hero1.trait = trait1  # type: ignore[attr-defined]
    hero2.trait = trait2  # type: ignore[attr-defined]

    world.say(rhyme_open(setting))
    introduce(world, hero1, hero2)
    world.para()
    run_problem(world, hero1, hero2, problem)
    world.para()

    tool = try_teamwork(world, hero1, hero2, problem)
    if tool is None:
        bad_ending(world, hero1, hero2, problem)
    else:
        solve(world, hero1, hero2, problem, tool)

    world.facts.update(
        hero1=hero1,
        hero2=hero2,
        problem=problem,
        tool=tool,
        setting=setting,
    )
    return world


# ---------------------------------------------------------------------------
# Q&A
# ---------------------------------------------------------------------------
def generation_prompts(world: World) -> list[str]:
    f = world.facts
    p: Problem = f["problem"]
    s: Setting = f["setting"]
    return [
        f'Write a short nursery-rhyme story set in {s.place} about two small helpers who try to {p.verb}.',
        f'Tell a gentle story in a crunch-dim place where teamwork is needed to solve {p.id.replace("_", " ")}.',
        f'Write a child-friendly story with a problem, a teamwork plan, and an ending that shows what changed.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero1: Entity = f["hero1"]
    hero2: Entity = f["hero2"]
    problem: Problem = f["problem"]
    tool: Optional[Tool] = f["tool"]
    answered = [
        QAItem(
            question=f"Who were the two little helpers in the story?",
            answer=f"The two little helpers were {hero1.id}, the {hero1.type}, and {hero2.id}, the {hero2.type}. They worked together in {world.setting.place}.",
        ),
        QAItem(
            question=f"What was the problem they had to solve?",
            answer=f"They had to deal with {problem.obstruction}, because they wanted to {problem.verb}.",
        ),
        QAItem(
            question=f"How did the helpers try to fix the problem?",
            answer=(
                f"They used teamwork and looked for a careful plan."
                + (f" In the end, they used {tool.label}." if tool else " But they could not find a tool that fit the job.")
            ),
        ),
    ]
    if world.facts.get("solved"):
        answered.append(
            QAItem(
                question="How did the story end?",
                answer=f"It ended with the problem fixed, and {hero1.id} and {hero2.id} standing happily together in the dim little place.",
            )
        )
    else:
        answered.append(
            QAItem(
                question="How did the story end?",
                answer=f"It ended badly, with the problem still stuck and the helpers going home a little sad.",
            )
        )
    return answered


WORLD_KNOWLEDGE = {
    "teamwork": [
        QAItem(
            question="What is teamwork?",
            answer="Teamwork is when people work together and each one helps with a part of the job.",
        )
    ],
    "problem_solving": [
        QAItem(
            question="What does problem solving mean?",
            answer="Problem solving means thinking carefully about a trouble and choosing a good way to fix it.",
        )
    ],
    "crunch": [
        QAItem(
            question="What is a crunchy sound?",
            answer="A crunchy sound is a crisp little noise, like leaves or crumbs under small feet.",
        )
    ],
    "dim": [
        QAItem(
            question="What does dim mean?",
            answer="Dim means there is only a little light, so things look soft and shadowy.",
        )
    ],
}


def world_knowledge_qa(world: World) -> list[QAItem]:
    tags = {"teamwork", "problem_solving", "crunch", "dim"}
    out: list[QAItem] = []
    for tag in tags:
        out.extend(WORLD_KNOWLEDGE[tag])
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
    lines.append("== (3) World knowledge questions ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        bits = []
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        lines.append(f"  {e.id:8} ({e.type}) {' '.join(bits)}")
    lines.append(f"  solved={world.facts.get('solved')}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Parameters / generation
# ---------------------------------------------------------------------------
@dataclass
class StoryParams:
    place: str
    problem: str
    name1: str
    kind1: str
    trait1: str
    name2: str
    kind2: str
    trait2: str
    seed: Optional[int] = None


CURATED = [
    StoryParams("attic", "stuck_cart", "Mia", "mouse", "brave", "Pip", "rabbit", "cheery"),
    StoryParams("cellar", "fallen_box", "Finn", "fox", "curious", "Nora", "bear", "tiny"),
    StoryParams("shed", "snagged_string", "Lily", "duck", "busy", "Theo", "mouse", "kind"),
]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A crunch-dim nursery-rhyme storyworld about teamwork and problem solving.")
    ap.add_argument("--place", choices=sorted(SETTINGS))
    ap.add_argument("--problem", choices=sorted(PROBLEMS))
    ap.add_argument("--name1")
    ap.add_argument("--kind1", choices=sorted(KINDS))
    ap.add_argument("--trait1", choices=sorted(TRAITS))
    ap.add_argument("--name2")
    ap.add_argument("--kind2", choices=sorted(KINDS))
    ap.add_argument("--trait2", choices=sorted(TRAITS))
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
    if args.place and args.problem and not valid_combo(args.place, args.problem):
        raise StoryError("That place/problem pairing is not valid for this world.")
    place = args.place or rng.choice(sorted(SETTINGS))
    problem = args.problem or rng.choice(sorted(PROBLEMS))
    name1 = args.name1 or rng.choice(NAMES)
    name2 = args.name2 or rng.choice([n for n in NAMES if n != name1])
    kind1 = args.kind1 or rng.choice(KINDS)
    kind2 = args.kind2 or rng.choice([k for k in KINDS if k != kind1])
    trait1 = args.trait1 or rng.choice(TRAITS)
    trait2 = args.trait2 or rng.choice([t for t in TRAITS if t != trait1])
    return StoryParams(place, problem, name1, kind1, trait1, name2, kind2, trait2)


def generate(params: StoryParams) -> StorySample:
    world = tell(
        SETTINGS[params.place],
        PROBLEMS[params.problem],
        params.name1,
        params.kind1,
        params.trait1,
        params.name2,
        params.kind2,
        params.trait2,
    )
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
        print(asp_program("#show valid_story/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        model = asp.one_model(asp_program("#show valid_story/2."))
        stories = sorted(set(asp.atoms(model, "valid_story")))
        print(f"{len(stories)} compatible stories:")
        for place, pid in stories:
            print(f"  {place:8} {pid}")
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
            header = f"### {p.name1} and {p.name2}: {p.problem} in {p.place}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()

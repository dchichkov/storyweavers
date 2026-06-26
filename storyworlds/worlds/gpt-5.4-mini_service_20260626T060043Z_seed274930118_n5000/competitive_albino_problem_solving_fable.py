#!/usr/bin/env python3
"""
competitive_albino_problem_solving_fable.py
===========================================

A small fable-like story world about a competitive albino animal who learns to
solve a problem by thinking, sharing, and changing course.

Seed tale inspiration:
---
In a quiet meadow, an albino hare named Alba wanted to win every game.
One day the river path washed out, and the smaller animals could not cross to
reach the berry hill. Alba raced ahead at first, but the bridge was gone.
A clever crow showed that a bundle of reeds, a flat stone, and a long branch
could make a safe stepping path. Alba helped build it, and everyone crossed
together.
---

This world keeps the story grounded in simulated state:
- a character can be competitive and proud
- a problem can block a shared goal
- problem-solving tools change meters and memes
- the ending proves what was fixed
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
# Entities and world state
# ---------------------------------------------------------------------------
@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    traits: list[str] = field(default_factory=list)
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    carried_by: Optional[str] = None
    place: str = ""
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"hare", "rabbit", "harekin"}:
            return {"subject": "they", "object": "them", "possessive": "their"}[case]
        if self.type in {"crow", "bird"}:
            return {"subject": "it", "object": "it", "possessive": "its"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class Setting:
    place: str = "the meadow"
    features: set[str] = field(default_factory=set)


@dataclass
class Problem:
    id: str
    label: str
    place: str
    block: str
    shared_goal: str
    risk: str
    keywords: set[str] = field(default_factory=set)


@dataclass
class Tool:
    id: str
    label: str
    phrase: str
    helps: set[str]
    used_for: str


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.problem: Optional[Problem] = None
        self.tools: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
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


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------
SETTINGS = {
    "meadow": Setting(place="the meadow", features={"grass", "hill", "berry"}),
    "riverbank": Setting(place="the riverbank", features={"water", "current", "reed"}),
    "orchard": Setting(place="the orchard", features={"tree", "fruit", "branch"}),
}

PROBLEMS = {
    "washed_bridge": Problem(
        id="washed_bridge",
        label="the washed-out stepping bridge",
        place="the riverbank",
        block="the crossing was broken",
        shared_goal="reach the berry hill",
        risk="some animals could slip into the water",
        keywords={"river", "bridge", "crossing"},
    ),
    "blocked_path": Problem(
        id="blocked_path",
        label="the thorny path",
        place="the orchard",
        block="the path was blocked by thorns",
        shared_goal="reach the ripe apples",
        risk="their paws would get scratched",
        keywords={"path", "thorns", "orchard"},
    ),
}

TOOLS = {
    "reeds": Tool(
        id="reeds",
        label="a bundle of reeds",
        phrase="a bundle of flexible reeds",
        helps={"bridge", "crossing", "water"},
        used_for="span a gap",
    ),
    "stone": Tool(
        id="stone",
        label="a flat stone",
        phrase="a flat stone",
        helps={"crossing", "bridge", "balance"},
        used_for="steady a step",
    ),
    "branch": Tool(
        id="branch",
        label="a long branch",
        phrase="a long branch",
        helps={"bridge", "crossing", "gap"},
        used_for="reach across",
    ),
    "thornshears": Tool(
        id="shears",
        label="a pair of shears",
        phrase="a small pair of shears",
        helps={"thorns", "path"},
        used_for="cut a path",
    ),
}

ANIMAL_NAMES = ["Alba", "Milo", "Tess", "Pip", "Nia", "Otis", "Luna", "Bram"]
BIRD_NAMES = ["Coral", "Quill", "Wren", "Sage"]
TRAITS = ["kind", "quick", "careful", "patient", "proud", "bright"]


# ---------------------------------------------------------------------------
# Story params
# ---------------------------------------------------------------------------
@dataclass
class StoryParams:
    setting: str
    problem: str
    hero_name: str
    hero_type: str
    companion_name: str
    companion_type: str
    trait: str
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# Fable engine
# ---------------------------------------------------------------------------
def _base_world(setting_key: str) -> World:
    return World(SETTINGS[setting_key])


def _introduce(world: World, hero: Entity, companion: Entity) -> None:
    world.say(
        f"In {world.setting.place}, there lived a little albino {hero.type} named {hero.id}. "
        f"{hero.pronoun().capitalize()} was very competitive and liked to be first in every race."
    )
    world.say(
        f"{companion.id}, a wise {companion.type}, often watched with calm eyes and thought before speaking."
    )


def _set_problem(world: World, problem: Problem) -> None:
    world.problem = problem
    world.say(
        f"One day, {problem.label} made a hard trouble at {problem.place}: {problem.block}."
    )
    world.say(
        f"The smaller animals still needed to {problem.shared_goal}, but {problem.risk}."
    )


def _compete(world: World, hero: Entity, companion: Entity) -> None:
    hero.memes["competitive"] = hero.memes.get("competitive", 0) + 1
    hero.memes["pride"] = hero.memes.get("pride", 0) + 1
    world.say(
        f"Alba hurried ahead and said, \"I can solve it alone and prove I'm the fastest.\""
    )
    world.say(
        f"But the wise {companion.type} said, \"A quick win is not always a true fix.\""
    )


def _inspect_problem(world: World, hero: Entity, companion: Entity, problem: Problem) -> None:
    hero.memes["curiosity"] = hero.memes.get("curiosity", 0) + 1
    companion.memes["wisdom"] = companion.memes.get("wisdom", 0) + 1
    world.say(
        f"So Alba looked closely at the trouble and noticed what the eyes of a racer had missed."
    )
    world.say(
        f"{companion.id} pointed to the broken place and asked, \"What things nearby could help us build a safe way?\""
    )


def _choose_tools(world: World, problem: Problem) -> list[Entity]:
    chosen: list[Entity] = []
    if problem.id == "washed_bridge":
        for tid in ["reeds", "branch", "stone"]:
            tool_def = TOOLS[tid]
            tool = world.add(Entity(
                id=tool_def.id,
                kind="thing",
                type="tool",
                label=tool_def.label,
                phrase=tool_def.phrase,
            ))
            world.tools[tool.id] = tool
            chosen.append(tool)
    else:
        tool_def = TOOLS["shears"]
        tool = world.add(Entity(
            id=tool_def.id,
            kind="thing",
            type="tool",
            label=tool_def.label,
            phrase=tool_def.phrase,
        ))
        world.tools[tool.id] = tool
        chosen.append(tool)
    return chosen


def _solve(world: World, hero: Entity, companion: Entity, problem: Problem, tools: list[Entity]) -> None:
    if problem.id == "washed_bridge":
        world.say(
            f"Together they gathered {tools[0].phrase}, {tools[1].phrase}, and {tools[2].phrase}."
        )
        world.say(
            f"Alba set the branch across the gap, pressed the flat stone beneath it, "
            f"and tied the reeds into a steady path."
        )
        hero.meters["helped_build"] = hero.meters.get("helped_build", 0) + 1
        hero.memes["competitive"] = max(0, hero.memes.get("competitive", 0) - 1)
        hero.memes["pride"] = max(0, hero.memes.get("pride", 0) - 1)
        hero.memes["joy"] = hero.memes.get("joy", 0) + 1
        world.say(
            f"Then Alba smiled and said, \"Let us cross together.\""
        )
        world.say(
            f"The little animals walked over the new path one by one, and no one slipped into the water."
        )
        world.say(
            f"At the end, the berry hill was reached, and Alba found that helping had felt better than winning alone."
        )
    else:
        world.say(
            f"They used {tools[0].phrase} to clear the thorny path."
        )
        hero.meters["helped_build"] = hero.meters.get("helped_build", 0) + 1
        hero.memes["competitive"] = max(0, hero.memes.get("competitive", 0) - 1)
        hero.memes["joy"] = hero.memes.get("joy", 0) + 1
        world.say(
            f"After that, the animals crossed safely to the orchard, and the ripe fruit was shared fairly."
        )


def tell(params: StoryParams) -> World:
    world = _base_world(params.setting)
    hero = world.add(Entity(
        id=params.hero_name,
        kind="character",
        type=params.hero_type,
        traits=["albino", params.trait],
        place=world.setting.place,
    ))
    companion = world.add(Entity(
        id=params.companion_name,
        kind="character",
        type=params.companion_type,
        traits=["wise"],
        place=world.setting.place,
    ))
    problem = PROBLEMS[params.problem]

    _introduce(world, hero, companion)
    world.para()
    _set_problem(world, problem)
    _compete(world, hero, companion)
    world.para()
    _inspect_problem(world, hero, companion, problem)
    tools = _choose_tools(world, problem)
    _solve(world, hero, companion, problem, tools)

    world.facts.update(
        hero=hero,
        companion=companion,
        problem=problem,
        tools=tools,
    )
    return world


# ---------------------------------------------------------------------------
# QA
# ---------------------------------------------------------------------------
def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    problem = f["problem"]
    return [
        f"Write a short fable for children about a competitive albino {hero.type} who learns to solve {problem.label}.",
        f"Tell a gentle story where {hero.id} stops racing long enough to fix a shared problem with a wise companion.",
        f"Write a simple moral tale in which a proud little animal uses nearby tools to help everyone cross or pass safely.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero: Entity = f["hero"]
    companion: Entity = f["companion"]
    problem: Problem = f["problem"]
    tools: list[Entity] = f["tools"]

    tool_names = ", ".join(t.label for t in tools)
    return [
        QAItem(
            question=f"Who is the story mainly about?",
            answer=f"The story is mainly about {hero.id}, a little albino {hero.type} who starts out very competitive.",
        ),
        QAItem(
            question=f"What problem needed solving in the story?",
            answer=f"{problem.label} needed solving because {problem.block}, and the animals still needed to {problem.shared_goal}.",
        ),
        QAItem(
            question=f"Who helped {hero.id} think calmly?",
            answer=f"{companion.id}, the wise {companion.type}, helped by asking a good question instead of rushing.",
        ),
        QAItem(
            question=f"What tools did they use?",
            answer=f"They used {tool_names} to make a safe way forward.",
        ),
        QAItem(
            question=f"How did {hero.id} change by the end?",
            answer=f"{hero.id} stopped trying only to win and felt glad to help build the solution for everyone.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    out = [
        QAItem(
            question="What does albino mean?",
            answer="Albino means an animal or person is born with very little color in their skin, fur, or feathers.",
        ),
        QAItem(
            question="What does competitive mean?",
            answer="Competitive means someone really wants to win or do better than others.",
        ),
        QAItem(
            question="What is problem solving?",
            answer="Problem solving means looking at a trouble, thinking about choices, and finding a useful way to fix it.",
        ),
    ]
    return out


def format_qa(sample: StorySample) -> str:
    lines = ["== Prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== Story QA ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== World QA ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
#show valid_story/3.
#show valid_combo/2.

valid_combo(S, P) :- setting(S), problem(P), fixable(P).
valid_story(S, P, H) :- valid_combo(S, P), hero(H), albino(H), competitive(H), setting(H, S).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid, s in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        for feat in sorted(s.features):
            lines.append(asp.fact("feature", sid, feat))
    for pid, p in PROBLEMS.items():
        lines.append(asp.fact("problem", pid))
        lines.append(asp.fact("goal", pid, p.shared_goal))
        lines.append(asp.fact("fixable", pid))
    for tid, t in TOOLS.items():
        lines.append(asp.fact("tool", tid))
        for h in sorted(t.helps):
            lines.append(asp.fact("helps", tid, h))
    for name in ANIMAL_NAMES + BIRD_NAMES:
        lines.append(asp.fact("hero", name))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_combo/2."))
    return sorted(set(asp.atoms(model, "valid_combo")))


def asp_verify() -> int:
    python_set = set(valid_combos())
    asp_set = set(asp_valid_combos())
    if python_set == asp_set:
        print(f"OK: ASP matches valid_combos() ({len(python_set)} combos).")
        return 0
    print("MISMATCH:")
    print("python-only:", sorted(python_set - asp_set))
    print("asp-only:", sorted(asp_set - python_set))
    return 1


# ---------------------------------------------------------------------------
# Reasonableness gate
# ---------------------------------------------------------------------------
def valid_combos() -> list[tuple[str, str]]:
    return [(s, p) for s in SETTINGS for p in PROBLEMS]


def explain_rejection(setting: str, problem: str) -> str:
    return f"(No story: the chosen setting/problem pair {setting!r} and {problem!r} is not supported.)"


# ---------------------------------------------------------------------------
# Params and generation
# ---------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A fable-like story world about competitive problem solving.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--problem", choices=PROBLEMS)
    ap.add_argument("--hero-name")
    ap.add_argument("--hero-type", choices=["hare", "rabbit"])
    ap.add_argument("--companion-name")
    ap.add_argument("--companion-type", choices=["crow", "bird"])
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
    if args.setting and args.problem and (args.setting, args.problem) not in valid_combos():
        raise StoryError(explain_rejection(args.setting, args.problem))

    setting = args.setting or rng.choice(list(SETTINGS))
    problem = args.problem or rng.choice(list(PROBLEMS))
    hero_type = args.hero_type or rng.choice(["hare", "rabbit"])
    companion_type = args.companion_type or "crow"
    trait = args.trait or rng.choice(TRAITS)

    hero_name = args.hero_name or rng.choice(ANIMAL_NAMES)
    companion_name = args.companion_name or rng.choice(BIRD_NAMES)

    if hero_name == companion_name:
        companion_name = "Quill"

    return StoryParams(
        setting=setting,
        problem=problem,
        hero_name=hero_name,
        hero_type=hero_type,
        companion_name=companion_name,
        companion_type=companion_type,
        trait=trait,
    )


def generate(params: StoryParams) -> StorySample:
    world = tell(params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for e in world.entities.values():
        bits = []
        if e.traits:
            bits.append(f"traits={e.traits}")
        if e.place:
            bits.append(f"place={e.place}")
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        lines.append(f"  {e.id} ({e.type}) " + " ".join(bits))
    if world.problem:
        lines.append(f"  problem={world.problem.id}")
    lines.append(f"  tools={sorted(world.tools)}")
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


CURATED = [
    StoryParams(setting="riverbank", problem="washed_bridge", hero_name="Alba", hero_type="hare",
                companion_name="Quill", companion_type="crow", trait="proud"),
    StoryParams(setting="orchard", problem="blocked_path", hero_name="Milo", hero_type="rabbit",
                companion_name="Sage", companion_type="bird", trait="careful"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid_story/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        models = asp.one_model(asp_program("#show valid_combo/2. #show valid_story/3."))
        print(f"{len(models)} shown atoms in one model")
        for atom in models:
            print(atom)
        return

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        base_seed = args.seed if args.seed is not None else random.randrange(2**31)
        samples: list[StorySample] = []
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            sample = generate(params)
            if sample.story in seen:
                i += 1
                continue
            seen.add(sample.story)
            samples.append(sample)
            i += 1

    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for idx, sample in enumerate(samples):
        header = f"### variant {idx + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if idx < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()

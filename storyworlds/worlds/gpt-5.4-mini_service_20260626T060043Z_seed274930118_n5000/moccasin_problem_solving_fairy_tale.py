#!/usr/bin/env python3
"""
storyworlds/worlds/moccasin_problem_solving_fairy_tale.py
==========================================================

A small fairy-tale storyworld about a moccasin trouble and a clever fix.

Seed tale:
---
A little girl named Mira wore a soft pair of moccasins to visit her grandmother
through the woods. One moccasin slipped off near a brook and drifted into the
reeds. Mira felt sad and stuck, because she did not want to go on with only one
shoe and muddy feet. A kind fairy heard her crying and showed her a long reed,
a ribbon, and a safe way to reach the lost moccasin. Mira used the reed like a
hook, tied the ribbon, and pulled the moccasin back. Then she dried it by a
warm lantern, put it on again, and went on smiling.

World idea:
---
- Physical meters: loss, wetness, distance, steadiness, warmth
- Emotional memes: worry, hope, courage, relief, gratitude
- The story is driven by the problem state, the tool choice, and the solution.
- The ending proves change by showing the moccasin recovered and the hero calm.
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
# World entities
# ---------------------------------------------------------------------------
@dataclass
class Entity:
    id: str
    kind: str = "thing"  # character | thing
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
        if self.type in {"girl", "woman", "fairy"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str
    detail: str


@dataclass
class Problem:
    id: str
    title: str
    description: str
    consequence: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Tool:
    id: str
    label: str
    phrase: str
    solves: set[str]
    helps_with: set[str]
    method: str
    ending: str
    magical: bool = False


@dataclass
class StoryParams:
    setting: str
    problem: str
    tool: str
    hero_name: str
    hero_type: str
    helper_type: str
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------
SETTINGS = {
    "brook": Setting(
        place="the mossy brook",
        detail="The brook sang over stones, and reeds leaned close to the water.",
    ),
    "forest": Setting(
        place="the deep forest path",
        detail="Tall trees stood like watchful old kings beside the path.",
    ),
    "cottage": Setting(
        place="the cottage gate",
        detail="A little gate creaked in the wind, and roses twined around the fence.",
    ),
}

PROBLEMS = {
    "lost_moccasin": Problem(
        id="lost_moccasin",
        title="a lost moccasin",
        description="one soft moccasin slipped off and drifted into the reeds",
        consequence="the hero could not walk on safely with only one shoe and a wet foot",
        tags={"moccasin", "water", "loss"},
    ),
    "muddy_moccasin": Problem(
        id="muddy_moccasin",
        title="a muddy moccasin",
        description="the moccasin sank into mud and became too sticky to wear",
        consequence="the hero needed a clean and dry way to make it useful again",
        tags={"moccasin", "mud", "clean"},
    ),
    "dark_path": Problem(
        id="dark_path",
        title="a dark path",
        description="night fell before the hero could cross the forest path",
        consequence="the hero needed a safe way to see the stones and roots ahead",
        tags={"darkness", "path", "light"},
    ),
}

TOOLS = {
    "reed_hook": Tool(
        id="reed_hook",
        label="a long reed",
        phrase="a long reed tied with ribbon",
        solves={"lost_moccasin"},
        helps_with={"water", "loss"},
        method="used the reed like a hook and looped the ribbon around the moccasin",
        ending="the lost moccasin slid back into the hero's hands",
    ),
    "lantern": Tool(
        id="lantern",
        label="a lantern",
        phrase="a warm lantern",
        solves={"dark_path", "muddy_moccasin"},
        helps_with={"light", "clean"},
        method="held the lantern close so the path looked safe and the moccasin could dry",
        ending="the way grew bright and the moccasin dried by the gentle light",
        magical=True,
    ),
    "towel": Tool(
        id="towel",
        label="a soft towel",
        phrase="a soft towel",
        solves={"muddy_moccasin"},
        helps_with={"clean"},
        method="wrapped the moccasin and rubbed the mud away",
        ending="the mud came off and the moccasin looked fit for walking again",
    ),
    "ladder": Tool(
        id="ladder",
        label="a little ladder",
        phrase="a little ladder",
        solves={"dark_path"},
        helps_with={"reach", "light"},
        method="set the ladder by the path so the hero could see the stones better",
        ending="the hero could cross with careful steps",
    ),
    "ribbon": Tool(
        id="ribbon",
        label="a ribbon",
        phrase="a bright ribbon",
        solves={"lost_moccasin"},
        helps_with={"loss"},
        method="tied the ribbon to the reed so it could reach farther",
        ending="the ribbon gave the hero a sure grip on the moccasin",
    ),
}

HERO_NAMES = ["Mira", "Lina", "Tessa", "Nora", "Elia", "Rosie", "Anya", "Lumi"]
HELPERS = {"fairy": "fairy", "fox": "fox", "owl": "owl"}

# ---------------------------------------------------------------------------
# World state
# ---------------------------------------------------------------------------
class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple[str, ...]] = set()
        self.facts: dict[str, object] = {}

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
# Story logic
# ---------------------------------------------------------------------------
def _bump(ent: Entity, key: str, amount: float = 1.0) -> None:
    ent.meters[key] = ent.meters.get(key, 0.0) + amount


def _bump_meme(ent: Entity, key: str, amount: float = 1.0) -> None:
    ent.memes[key] = ent.memes.get(key, 0.0) + amount


def solve_problem(world: World, hero: Entity, helper: Entity, problem: Problem, tool: Tool) -> None:
    if (problem.id, tool.id) in world.fired:
        return
    if problem.id not in tool.solves:
        raise StoryError(f"No fair solution: {tool.label} does not solve {problem.title}.")
    world.fired.add((problem.id, tool.id))

    if problem.id == "lost_moccasin":
        _bump(hero, "hope", 1)
        _bump_meme(hero, "hope", 1)
        world.say(
            f"{helper.pronoun().capitalize()} saw the reeds and said, "
            f"\"We can reach it.\" {helper.pronoun().capitalize()} {tool.method}."
        )
        _bump(hero, "distance", -1)
        _bump_meme(hero, "courage", 1)
        world.say(
            f"{hero.id} held still, listened, and used the reed carefully. "
            f"{tool.ending.capitalize()}."
        )
        _bump(hero, "loss", -1)
        _bump(hero, "wetness", -1)
        _bump_meme(hero, "relief", 2)
    elif problem.id == "muddy_moccasin":
        world.say(
            f"{helper.pronoun().capitalize()} smiled and brought {tool.label}. "
            f"{tool.method.capitalize()}."
        )
        _bump(hero, "wetness", -1)
        _bump(hero, "steadiness", 1)
        _bump_meme(hero, "relief", 2)
        world.say(f"{tool.ending.capitalize()}.")
    elif problem.id == "dark_path":
        world.say(
            f"{helper.pronoun().capitalize()} lifted {tool.label} high. "
            f"The path stopped being a shadowy guess and became a trail of small bright stones."
        )
        _bump(hero, "steadiness", 2)
        _bump_meme(hero, "courage", 1)
        _bump_meme(helper, "kindness", 1)
        world.say(f"{tool.ending.capitalize()}.")
    else:
        raise StoryError("Unknown problem for this fairy tale.")


def tell(world: World, hero: Entity, helper: Entity, problem: Problem, tool: Tool) -> None:
    world.say(
        f"Once upon a time, {hero.id} came to {world.setting.place}. {world.setting.detail}"
    )
    world.say(
        f"{hero.id} wore a soft pair of moccasins and loved how lightly they tapped the ground."
    )
    world.say(
        f"But soon there was {problem.description}, and {problem.consequence}."
    )
    _bump(hero, "loss", 1)
    _bump(hero, "worry", 1)
    _bump_meme(hero, "worry", 2)

    world.para()
    world.say(
        f"Then a kind {helper.type} appeared and looked at the trouble with calm eyes."
    )
    world.say(
        f"{helper.pronoun().capitalize()} knew that a patient plan was better than a hurried step."
    )
    solve_problem(world, hero, helper, problem, tool)

    world.para()
    hero.meters["loss"] = max(0.0, hero.meters.get("loss", 0.0))
    hero.meters["wetness"] = max(0.0, hero.meters.get("wetness", 0.0))
    world.say(
        f"In the end, {hero.id} wore {tool.ending.split(' the ')[-1] if tool.id == 'reed_hook' else 'the moccasin'} "
        f"and walked on with a light heart."
    )
    if tool.id == "reed_hook":
        world.say(
            f"The rescued moccasin was dry enough to wear again, and the reeds waved like little green flags."
        )
    elif tool.id == "lantern":
        world.say(
            f"The warm lantern left a gold glow on the path, and the moccasin felt snug and safe."
        )
    else:
        world.say(
            f"The problem was solved, and the moccasin sat neat as a tiny boat on a calm pond."
        )

    world.facts.update(hero=hero, helper=helper, problem=problem, tool=tool)


# ---------------------------------------------------------------------------
# QA generation
# ---------------------------------------------------------------------------
def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero: Entity = f["hero"]
    problem: Problem = f["problem"]
    tool: Tool = f["tool"]
    return [
        f'Write a fairy tale for a young child about {hero.id}, {problem.title}, and {tool.label}.',
        f"Tell a gentle problem-solving story where {hero.id} faces {problem.description} and a wise helper uses {tool.phrase}.",
        f'Write a short story with the word "moccasin" that ends with a clever fix and a happy walk home.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero: Entity = f["hero"]
    helper: Entity = f["helper"]
    problem: Problem = f["problem"]
    tool: Tool = f["tool"]
    return [
        QAItem(
            question=f"What problem did {hero.id} have in the story?",
            answer=f"{hero.id} had {problem.title}. That meant {problem.consequence}.",
        ),
        QAItem(
            question=f"Who helped {hero.id} solve the trouble?",
            answer=f"A kind {helper.type} helped {hero.id}. {helper.pronoun().capitalize()} stayed calm and found a clever way forward.",
        ),
        QAItem(
            question=f"What tool did they use to fix the problem?",
            answer=f"They used {tool.label}. {tool.method.capitalize()}, and that was the right answer for the trouble.",
        ),
        QAItem(
            question=f"How did the story end for {hero.id}'s moccasin?",
            answer="The moccasin was recovered, made ready again, and the hero could walk on happily.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a moccasin?",
            answer="A moccasin is a soft shoe, often made to be light and flexible for walking.",
        ),
        QAItem(
            question="Why do people use a lantern?",
            answer="People use a lantern to give light in dark places, so they can see where they are going.",
        ),
        QAItem(
            question="What does it mean to solve a problem?",
            answer="To solve a problem means to find a way to make the trouble better or go away.",
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


# ---------------------------------------------------------------------------
# ASP
# ---------------------------------------------------------------------------
ASP_RULES = r"""
problem_tool(P, T) :- problem(P), tool(T), solves(T, P).
good_story(P, T) :- problem_tool(P, T).
"""

def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid, s in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
    for pid, p in PROBLEMS.items():
        lines.append(asp.fact("problem", pid))
        for tag in sorted(p.tags):
            lines.append(asp.fact("problem_tag", pid, tag))
    for tid, t in TOOLS.items():
        lines.append(asp.fact("tool", tid))
        for pid in sorted(t.solves):
            lines.append(asp.fact("solves", tid, pid))
        for tag in sorted(t.helps_with):
            lines.append(asp.fact("helps_with", tid, tag))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_pairs() -> list[tuple[str, str]]:
    import asp
    model = asp.one_model(asp_program("#show problem_tool/2."))
    return sorted(set(asp.atoms(model, "problem_tool")))


def asp_verify() -> int:
    py = sorted((p, t) for p in PROBLEMS for t in TOOLS if p in TOOLS[t].solves)
    aspp = asp_valid_pairs()
    if py == aspp:
        print(f"OK: clingo gate matches Python solver ({len(py)} pairs).")
        return 0
    print("MISMATCH between clingo and Python solver:")
    print("python:", py)
    print("asp:", aspp)
    return 1


# ---------------------------------------------------------------------------
# Parameters and generation
# ---------------------------------------------------------------------------
@dataclass
class StoryParams:
    setting: str
    problem: str
    tool: str
    hero_name: str
    hero_type: str
    helper_type: str
    seed: Optional[int] = None


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A fairy tale about a moccasin problem and a clever fix.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--problem", choices=PROBLEMS)
    ap.add_argument("--tool", choices=TOOLS)
    ap.add_argument("--hero-name")
    ap.add_argument("--hero-type", choices=["girl", "boy"])
    ap.add_argument("--helper-type", choices=list(HELPERS))
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


def valid_combos() -> list[tuple[str, str, str]]:
    out = []
    for s in SETTINGS:
        for p in PROBLEMS:
            for t in TOOLS:
                if p in TOOLS[t].solves:
                    out.append((s, p, t))
    return out


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    combos = [c for c in valid_combos()
              if (args.setting is None or c[0] == args.setting)
              and (args.problem is None or c[1] == args.problem)
              and (args.tool is None or c[2] == args.tool)]
    if not combos:
        raise StoryError("No valid fairy-tale combination matches the given options.")
    setting, problem, tool = rng.choice(sorted(combos))
    hero_type = args.hero_type or rng.choice(["girl", "boy"])
    helper_type = args.helper_type or rng.choice(list(HELPERS))
    hero_name = args.hero_name or rng.choice(HERO_NAMES)
    return StoryParams(setting=setting, problem=problem, tool=tool,
                       hero_name=hero_name, hero_type=hero_type, helper_type=helper_type)


def generate(params: StoryParams) -> StorySample:
    setting = SETTINGS[params.setting]
    problem = PROBLEMS[params.problem]
    tool = TOOLS[params.tool]
    world = World(setting)

    hero = world.add(Entity(
        id=params.hero_name,
        kind="character",
        type=params.hero_type,
        meters={"worry": 0.0, "hope": 0.0, "loss": 0.0, "wetness": 0.0, "steadiness": 0.0},
        memes={"worry": 0.0, "hope": 0.0, "courage": 0.0, "relief": 0.0},
    ))
    helper = world.add(Entity(
        id="Helper",
        kind="character",
        type=params.helper_type,
        label=f"a kind {params.helper_type}",
        meters={"steadiness": 1.0},
        memes={"kindness": 1.0, "calm": 1.0},
    ))

    tell(world, hero, helper, problem, tool)

    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
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
    lines.append(f"  fired={sorted(world.fired)}")
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
    StoryParams(setting="brook", problem="lost_moccasin", tool="reed_hook", hero_name="Mira", hero_type="girl", helper_type="fairy"),
    StoryParams(setting="forest", problem="dark_path", tool="lantern", hero_name="Lina", hero_type="girl", helper_type="owl"),
    StoryParams(setting="cottage", problem="muddy_moccasin", tool="towel", hero_name="Nora", hero_type="girl", helper_type="fox"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show problem_tool/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        model = asp.one_model(asp_program("#show problem_tool/2."))
        pairs = sorted(set(asp.atoms(model, "problem_tool")))
        for p, t in pairs:
            print(f"{p} -> {t}")
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
            header = f"### {p.hero_name}: {p.problem} with {p.tool} at {p.setting}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()

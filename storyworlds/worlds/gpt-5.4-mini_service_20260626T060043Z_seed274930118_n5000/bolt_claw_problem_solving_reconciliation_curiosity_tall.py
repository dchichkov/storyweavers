#!/usr/bin/env python3
"""
A standalone story world for a tall-tale-style repair and reunion story.

Seed imagery:
- A curious child/tinkerer spots a stubborn broken gate bolt.
- A claw hook can pull the bolt free, but the job is awkward and a little scary.
- Problem solving turns the snag into a plan.
- Reconciliation follows when a helper and a worried neighbor make peace.

The world is small on purpose: one setting, one problem, one useful tool, one
repair, one ending image that proves something changed.
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
# Story model
# ---------------------------------------------------------------------------
@dataclass
class Entity:
    id: str
    kind: str = "thing"  # "character" | "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)
    traits: list[str] = field(default_factory=list)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "woman", "mother", "aunt", "lady"}
        male = {"boy", "man", "father", "uncle", "gentleman"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def noun(self) -> str:
        return self.label or self.type


@dataclass
class Setting:
    place: str = "the fence line"
    detail: str = "a long field"
    affords: set[str] = field(default_factory=set)


@dataclass
class Tool:
    id: str
    label: str
    phrase: str
    purpose: str
    use_verb: str
    helps_with: set[str]
    weight: str = "light"


@dataclass
class StoryParams:
    place: str
    problem: str
    tool: str
    hero: str
    hero_type: str
    helper: str
    helper_type: str
    trait: str
    seed: Optional[int] = None


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.lines: list[str] = []
        self.facts: dict = {}

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str) -> Entity:
        return self.entities[eid]

    def say(self, text: str) -> None:
        if text:
            self.lines.append(text)

    def render(self) -> str:
        return " ".join(self.lines)


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------
SETTINGS = {
    "fence": Setting(place="the split-rail fence", detail="a windy pasture", affords={"bolt"}),
    "barn": Setting(place="the barn door", detail="a red barn yard", affords={"bolt"}),
    "bridge": Setting(place="the old footbridge", detail="a creek below", affords={"bolt"}),
}

PROBLEMS = {
    "stuck_bolt": {
        "keyword": "bolt",
        "title": "a stubborn bolt",
        "verb": "fix the stuck bolt",
        "issue": "jammed fast",
        "risk": "the gate would not stay shut",
        "turn": "the bolt needed a clever pull",
        "ending": "the gate swung and latched like a happy little jaw",
    }
}

TOOLS = {
    "claw": Tool(
        id="claw",
        label="a claw hook",
        phrase="a long, curved claw hook",
        purpose="to grab and pull",
        use_verb="hook",
        helps_with={"bolt"},
        weight="lithe",
    ),
    "wedge": Tool(
        id="wedge",
        label="a wooden wedge",
        phrase="a smooth wooden wedge",
        purpose="to hold things open",
        use_verb="set",
        helps_with={"bolt"},
        weight="small",
    ),
}

HERO_NAMES = ["Mabel", "Rosie", "Junie", "Nell", "Pip", "Tilly"]
HELPER_NAMES = ["Silas", "Milo", "Wren", "Benny", "June", "Cora"]
TRAITS = ["curious", "bright-eyed", "brave", "quick-thinking", "lively"]


# ---------------------------------------------------------------------------
# World helpers
# ---------------------------------------------------------------------------
def meter(entity: Entity, key: str, amount: float = 1.0) -> None:
    entity.meters[key] = entity.meters.get(key, 0.0) + amount


def meme(entity: Entity, key: str, amount: float = 1.0) -> None:
    entity.memes[key] = entity.memes.get(key, 0.0) + amount


def is_valid_combo(setting: Setting, problem: str, tool: str) -> bool:
    return problem in setting.affords and problem in TOOLS[tool].helps_with


def select_combo(rng: random.Random, args: argparse.Namespace) -> tuple[str, str]:
    combos = []
    for place, setting in SETTINGS.items():
        for problem in PROBLEMS:
            for tool in TOOLS:
                if is_valid_combo(setting, problem, tool):
                    combos.append((place, tool))
    if args.place:
        combos = [c for c in combos if c[0] == args.place]
    if args.tool:
        combos = [c for c in combos if c[1] == args.tool]
    if not combos:
        raise StoryError("No valid story combination matches those options.")
    return rng.choice(sorted(combos))


def solve_problem(world: World, hero: Entity, helper: Entity, tool: Tool) -> None:
    memo = world.facts
    memo["tool"] = tool
    meter(hero, "curiosity")
    meme(hero, "curiosity")
    world.say(
        f"{hero.id} was a {world.facts['trait']} {hero.type} who noticed every odd thing at "
        f"{world.setting.place}."
    )
    world.say(
        f"{hero.pronoun('subject').capitalize()} wanted to {world.facts['problem_verb']} because "
        f"the old gate sat {world.facts['issue']}."
    )
    world.say(
        f"{hero.pronoun('subject').capitalize()} peered closer and said, "
        f"\"That bolt is a puzzle with its hat on.\""
    )

    meter(helper, "worry")
    meme(helper, "worry")
    world.say(
        f"{helper.id} frowned and warned that if nobody fixed it, {world.facts['risk']}."
    )

    meter(hero, "thinking")
    meme(hero, "thinking")
    world.say(
        f"{hero.id} studied the bolt, then spotted {tool.phrase}. "
        f"\"If we {tool.use_verb} the bolt just so, it will come loose,\" {hero.pronoun('subject')} said."
    )

    meter(hero, "action")
    meter(helper, "help")
    world.say(
        f"Together they went to work: {hero.id} held steady while {helper.id} {tool.use_verb}ed and pulled."
    )
    world.say(
        f"At last, the stubborn bolt slipped free like a fish from a bucket."
    )

    meter(helper, "relief")
    meme(helper, "relief")
    meme(hero, "joy")
    world.say(
        f"{helper.id} laughed, and the worry on {helper.pronoun('possessive')} face melted away."
    )

    meter(hero, "repair")
    world.say(
        f"They set the latch right, and {world.facts['ending_image']}."
    )

    meme(helper, "reconciliation")
    meme(hero, "reconciliation")
    world.say(
        f"{helper.id} thanked {hero.id} for the clever idea, and {hero.id} smiled as wide as a sunrise."
    )


# ---------------------------------------------------------------------------
# Narrative generation
# ---------------------------------------------------------------------------
def build_world(params: StoryParams) -> World:
    setting = SETTINGS[params.place]
    world = World(setting)
    hero = world.add(Entity(id=params.hero, kind="character", type=params.hero_type, traits=[params.trait]))
    helper = world.add(Entity(id=params.helper, kind="character", type=params.helper_type))
    tool = TOOLS[params.tool]
    world.add(Entity(id=tool.id, type="tool", label=tool.label, phrase=tool.phrase))

    world.facts = {
        "trait": params.trait,
        "problem_verb": PROBLEMS[params.problem]["verb"],
        "issue": PROBLEMS[params.problem]["issue"],
        "risk": PROBLEMS[params.problem]["risk"],
        "ending_image": PROBLEMS[params.problem]["ending"],
        "tool": tool,
        "hero": hero,
        "helper": helper,
    }

    world.say(
        f"Out by {setting.place}, with {setting.detail} stretching around them, the old gate gave a crooked groan."
    )
    world.say(
        f"{hero.id} was the kind of {hero.type} who could not pass a puzzle without tapping it twice."
    )
    solve_problem(world, hero, helper, tool)
    return world


# ---------------------------------------------------------------------------
# Q&A
# ---------------------------------------------------------------------------
def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a tall tale for a child about "{f["problem_verb"]}" at {world.setting.place}, where curiosity leads to a clever fix.',
        f"Tell a funny, child-friendly story where {f['hero'].id} and {f['helper'].id} solve a stuck bolt with {f['tool'].label}.",
        f"Write a short tall tale that starts with a broken gate and ends with reconciliation after a careful repair.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero: Entity = f["hero"]
    helper: Entity = f["helper"]
    tool: Tool = f["tool"]
    return [
        QAItem(
            question=f"What problem did {hero.id} want to solve at {world.setting.place}?",
            answer=f"{hero.id} wanted to {f['problem_verb']} because the gate was {f['issue']}.",
        ),
        QAItem(
            question=f"How did {hero.id} figure out a way to fix the gate?",
            answer=f"{hero.id} looked closely, used {tool.phrase}, and made a plan to {tool.use_verb} the bolt just so.",
        ),
        QAItem(
            question=f"How did {hero.id} and {helper.id} feel at the end?",
            answer=f"They felt happy and relieved after the repair, and they made up with each other in the end.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    out = [
        QAItem(
            question="What is a bolt?",
            answer="A bolt is a metal fastener that can slide into place to hold something shut.",
        ),
        QAItem(
            question="What is a claw hook for?",
            answer="A claw hook is useful for grabbing, pulling, or lifting something that is hard to reach with fingers alone.",
        ),
        QAItem(
            question="What does curiosity help people do?",
            answer="Curiosity helps people notice details, ask questions, and look for clever solutions.",
        ),
        QAItem(
            question="What is reconciliation?",
            answer="Reconciliation is when people stop being upset and make peace again.",
        ),
    ]
    return out


def format_qa(sample: StorySample) -> str:
    lines = ["== Generation prompts ==", *[f"- {p}" for p in sample.prompts], "", "== Story Q&A =="]
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== World Q&A ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- trace ---"]
    for e in world.entities.values():
        bits = []
        if e.traits:
            bits.append(f"traits={e.traits}")
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        lines.append(f"{e.id}: {e.kind}/{e.type} {' '.join(bits)}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
% A place supports a problem when it affords that kind of fixable trouble.
problem_place(P, Pr) :- place(P), affords(P, Pr).

% A tool works when it helps with the problem.
good_tool(T, Pr) :- tool(T), helps(T, Pr).

% A story is valid when the place and tool both match the problem.
valid_story(P, Pr, T) :- problem_place(P, Pr), good_tool(T, Pr).

#show valid_story/3.
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for place, setting in SETTINGS.items():
        lines.append(asp.fact("place", place))
        for p in sorted(setting.affords):
            lines.append(asp.fact("affords", place, p))
    for pid, problem in PROBLEMS.items():
        lines.append(asp.fact("problem", pid))
        lines.append(asp.fact("problem_keyword", pid, problem["keyword"]))
    for tid, tool in TOOLS.items():
        lines.append(asp.fact("tool", tid))
        for p in sorted(tool.helps_with):
            lines.append(asp.fact("helps", tid, p))
    return "\n".join(lines)


def asp_program() -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n"


def asp_valid_stories() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program())
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    python_set = {
        (place, problem, tool)
        for place, setting in SETTINGS.items()
        for problem in PROBLEMS
        for tool in TOOLS
        if is_valid_combo(setting, problem, tool)
    }
    asp_set = set(asp_valid_stories())
    if python_set == asp_set:
        print(f"OK: ASP matches Python ({len(python_set)} valid stories).")
        return 0
    print("MISMATCH between ASP and Python")
    print("Only in Python:", sorted(python_set - asp_set))
    print("Only in ASP:", sorted(asp_set - python_set))
    return 1


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Tall-tale story world: bolt, claw, curiosity, and reconciliation.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--tool", choices=TOOLS)
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
    place, tool = select_combo(rng, args)
    hero = rng.choice(HERO_NAMES)
    helper = rng.choice([n for n in HELPER_NAMES if n != hero])
    hero_type = rng.choice(["girl", "boy"])
    helper_type = "woman" if hero_type == "girl" else "man"
    trait = "curious"
    return StoryParams(
        place=place,
        problem="stuck_bolt",
        tool=tool,
        hero=hero,
        hero_type=hero_type,
        helper=helper,
        helper_type=helper_type,
        trait=trait,
    )


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
        print(dump_trace(sample.world))
    if qa:
        print()
        print(format_qa(sample))


CURATED = [
    StoryParams(place="fence", problem="stuck_bolt", tool="claw", hero="Mabel", hero_type="girl", helper="Silas", helper_type="man", trait="curious"),
    StoryParams(place="barn", problem="stuck_bolt", tool="claw", hero="Pip", hero_type="boy", helper="Wren", helper_type="woman", trait="quick-thinking"),
    StoryParams(place="bridge", problem="stuck_bolt", tool="claw", hero="Tilly", hero_type="girl", helper="Benny", helper_type="man", trait="bright-eyed"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program())
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        for row in asp_valid_stories():
            print(row)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)

    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 20):
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
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.hero}: {p.problem} at {p.place} with {p.tool}"
        elif len(samples) > 1:
            header = f"### variant {idx + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if idx < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()

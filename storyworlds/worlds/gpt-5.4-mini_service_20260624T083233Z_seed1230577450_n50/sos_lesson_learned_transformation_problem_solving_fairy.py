#!/usr/bin/env python3
"""
A small fairy-tale story world about a child, a problem, a rescue cry, and a
lesson learned through transformation and problem solving.

Seed inspiration:
- A tiny SOS echo in the woods
- A fairy-tale tone
- A meaningful lesson learned
- A transformation that changes how the hero solves problems

The world keeps a live simulation of physical meters and emotional memes, then
renders a short authored story from the resulting state.
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
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "woman", "queen", "princess", "mother", "fairy"}
        male = {"boy", "man", "king", "prince", "father", "wizard"}
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
    mood: str
    glow: str


@dataclass
class Problem:
    id: str
    trouble: str
    sos_source: str
    cost: str
    lesson: str
    transformation: str
    result: str
    keyword: str = "sos"


@dataclass
class Tool:
    id: str
    label: str
    phrase: str
    use: str
    helps: set[str]


class World:
    def __init__(self, setting: Setting):
        self.setting = setting
        self.entities: dict[str, Entity] = {}
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
    "moonwood": Setting(place="the Moonwood", mood="hushed", glow="silver"),
    "rose_gate": Setting(place="the Rose Gate", mood="misty", glow="pink"),
    "briar_hollow": Setting(place="Briar Hollow", mood="twilit", glow="blue"),
}

PROBLEMS = {
    "tangle": Problem(
        id="tangle",
        trouble="a little owl had gotten tangled in thorny vines",
        sos_source="the thorn hedge",
        cost="every flap of its wings pulled the briars tighter",
        lesson="slow hands are kinder than hurried hands",
        transformation="brave and careful",
        result="the owl was free at last",
        keyword="sos",
    ),
    "floodgate": Problem(
        id="floodgate",
        trouble="the mill stream had risen and blocked the path to the village",
        sos_source="the riverbank",
        cost="the water kept creeping higher around the stepping stones",
        lesson="a calm plan can do what panic cannot",
        transformation="calm and clever",
        result="the path opened again",
        keyword="sos",
    ),
    "lost_lantern": Problem(
        id="lost_lantern",
        trouble="a tiny lantern had fallen into a hollow and gone dark",
        sos_source="the mossy hollow",
        cost="without the lantern, the path was too dark for the forest sprite",
        lesson="asking for help can light the way",
        transformation="kind and helpful",
        result="the lantern shone again",
        keyword="sos",
    ),
}

TOOLS = {
    "ladder": Tool(
        id="ladder",
        label="a wooden ladder",
        phrase="a wooden ladder with little carved stars",
        use="reach high places safely",
        helps={"tangle"},
    ),
    "bucket_chain": Tool(
        id="bucket_chain",
        label="a bucket chain",
        phrase="a long bucket chain passed from hand to hand",
        use="carry water in order",
        helps={"floodgate"},
    ),
    "glow_moss": Tool(
        id="glow_moss",
        label="glow moss",
        phrase="a handful of glow moss wrapped in a leaf",
        use="make a dark place shine",
        helps={"lost_lantern"},
    ),
}

HERO_NAMES = ["Elin", "Mira", "Tobin", "Nessa", "Pip", "Arlo", "Juniper", "Rowan"]
HERO_TYPES = {"girl": ["Elin", "Mira", "Nessa", "Juniper"], "boy": ["Tobin", "Pip", "Arlo", "Rowan"]}
TRAITS = ["curious", "gentle", "bold", "small", "bright"]


# ---------------------------------------------------------------------------
# Params
# ---------------------------------------------------------------------------
@dataclass
class StoryParams:
    setting: str
    problem: str
    name: str
    gender: str
    trait: str
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
% A story is valid when a tool can help with the chosen problem.
valid_story(S, P, T) :- setting(S), problem(P), tool(T), helps(T, P).

% The lesson and transformation are part of the generated tale.
has_lesson(P) :- problem(P).
has_transformation(P) :- problem(P).
"""

def asp_facts() -> str:
    import storyworlds.asp as asp
    lines: list[str] = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for pid in PROBLEMS:
        lines.append(asp.fact("problem", pid))
    for tid, tool in TOOLS.items():
        lines.append(asp.fact("tool", tid))
        for p in sorted(tool.helps):
            lines.append(asp.fact("helps", tid, p))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_stories() -> list[tuple]:
    import storyworlds.asp as asp
    model = asp.one_model(asp_program("#show valid_story/3."))
    return sorted(set(asp.atoms(model, "valid_story")))


# ---------------------------------------------------------------------------
# Story simulation
# ---------------------------------------------------------------------------
def choose_tool(problem: Problem) -> Tool:
    for tool in TOOLS.values():
        if problem.id in tool.helps:
            return tool
    raise StoryError("No tool can solve this problem.")


def build_hero(name: str, gender: str, trait: str) -> Entity:
    return Entity(id=name, kind="character", type=gender, meters={}, memes={"curiosity": 1.0, trait: 1.0})


def tell(setting: Setting, problem: Problem, hero: Entity, tool: Tool) -> World:
    world = World(setting)
    narrator = world.add(Entity(id="narrator", kind="character", type="fairy", label="the story fairy"))
    hero = world.add(hero)
    trouble = world.add(Entity(
        id=problem.id,
        kind="thing",
        type="problem",
        label=problem.sos_source,
        phrase=problem.trouble,
    ))
    tool_ent = world.add(Entity(
        id=tool.id,
        kind="thing",
        type="tool",
        label=tool.label,
        phrase=tool.phrase,
        owner=hero.id,
    ))

    # Setup
    world.say(f"Once in {setting.place}, the air was {setting.mood} and the trees held a {setting.glow} glow.")
    world.say(f"{hero.id} was a {hero.pronoun('subject').capitalize()} {hero.type} who was {next(iter([k for k in hero.memes if k != 'curiosity']), 'small')} and loved to listen for secrets in the leaves.")
    world.say(f"One evening, a soft {problem.keyword.upper()} floated from {problem.sos_source}, and it meant {problem.trouble}.")

    # Problem
    world.para()
    world.say(f"{problem.cost.capitalize()}.")
    hero.meters["worry"] = 1.0
    hero.memes["fear"] = 1.0
    world.say(f"{hero.id} wanted to rush in, but {hero.pronoun('possessive')} thoughts said that rushing could make things worse.")

    # Discovery and lesson
    world.para()
    world.say(f"Then {hero.id} spotted {tool.phrase}.")
    world.say(f"{hero.pronoun('subject').capitalize()} remembered the lesson that {problem.lesson}.")
    hero.memes["learning"] = 1.0
    hero.memes["courage"] = 1.0

    # Transformation
    hero.type = "fairy" if hero.type in {"girl", "boy"} else hero.type
    hero.memes["transformed"] = 1.0
    world.say(f"As {hero.id} worked, {hero.pronoun('subject')} felt {problem.transformation}; it was as if a small spark had turned {hero.pronoun('object')} into someone new.")

    # Solution
    world.say(f"Using {tool.label}, {hero.id} knew how to {tool.use}.")
    world.say(f"{hero.id} followed a careful plan, and soon {problem.result}.")
    hero.meters["relief"] = 1.0
    hero.memes["joy"] = 1.0
    hero.memes["wisdom"] = 1.0

    world.para()
    world.say(f"In the end, {hero.id} stood a little straighter, for the day had taught {hero.pronoun('object')} that {problem.lesson}.")
    world.say(f"The forest went quiet again, and the little SOS had become a story of help, change, and a wiser heart.")

    world.facts.update(
        hero=hero,
        problem=problem,
        tool=tool,
        setting=setting,
        trouble=trouble,
        narrator=narrator,
    )
    return world


# ---------------------------------------------------------------------------
# QA
# ---------------------------------------------------------------------------
def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero, problem, tool = f["hero"], f["problem"], f["tool"]
    return [
        f'Write a short fairy tale for a young child that includes the word "{problem.keyword}" and ends with a lesson learned.',
        f"Tell a magical rescue story where {hero.id} hears a quiet {problem.keyword.upper()} and uses {tool.label} to solve the trouble.",
        f"Write a simple fairy tale about problem solving, transformation, and learning from a mistake in {world.setting.place}.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero, problem, tool = f["hero"], f["problem"], f["tool"]
    return [
        QAItem(
            question=f"Who heard the {problem.keyword.upper()} in {world.setting.place}?",
            answer=f"{hero.id} heard the {problem.keyword.upper()} coming from {problem.sos_source}."
        ),
        QAItem(
            question=f"What problem was waiting to be solved?",
            answer=f"The problem was that {problem.trouble}."
        ),
        QAItem(
            question=f"What did {hero.id} use to help?",
            answer=f"{hero.id} used {tool.label}, which helped {tool.use}."
        ),
        QAItem(
            question=f"What lesson did the story teach?",
            answer=f"The story taught that {problem.lesson}."
        ),
        QAItem(
            question=f"How did {hero.id} change by the end?",
            answer=f"{hero.id} became {problem.transformation} while helping, and that was the story's transformation."
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does SOS mean?",
            answer="SOS is a simple distress signal people use to say they need help right away."
        ),
        QAItem(
            question="What is a fairy tale?",
            answer="A fairy tale is a magical story that often has a brave helper, a problem, and a lesson at the end."
        ),
        QAItem(
            question="Why do people make plans when something is wrong?",
            answer="People make plans so they can solve the problem safely instead of making it worse."
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


def dump_trace(world: World) -> str:
    lines = ["--- trace ---"]
    for e in world.entities.values():
        bits = []
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        lines.append(f"{e.id}: {e.type} {' '.join(bits)}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# ASP verification
# ---------------------------------------------------------------------------
def asp_verify() -> int:
    import storyworlds.asp as asp
    py = {(s, p, t) for s in SETTINGS for p in PROBLEMS for t in TOOLS if p in TOOLS[t].helps}
    cl = set(asp.atoms(asp.one_model(asp_program("#show valid_story/3.")), "valid_story"))
    if py == cl:
        print(f"OK: ASP matches Python ({len(py)} valid stories).")
        return 0
    print("Mismatch between ASP and Python.")
    print("Only in Python:", sorted(py - cl))
    print("Only in ASP:", sorted(cl - py))
    return 1


# ---------------------------------------------------------------------------
# CLI helpers
# ---------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Fairy-tale story world about SOS, lesson learned, transformation, and problem solving.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--problem", choices=PROBLEMS)
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["girl", "boy"])
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
    setting = args.setting or rng.choice(list(SETTINGS))
    problem = args.problem or rng.choice(list(PROBLEMS))
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(HERO_TYPES[gender])
    trait = args.trait or rng.choice(TRAITS)
    if args.gender and args.name is None and name not in HERO_TYPES[gender]:
        raise StoryError("The chosen name does not match the chosen gender.")
    return StoryParams(setting=setting, problem=problem, name=name, gender=gender, trait=trait)


def generate(params: StoryParams) -> StorySample:
    setting = SETTINGS[params.setting]
    problem = PROBLEMS[params.problem]
    hero = build_hero(params.name, params.gender, params.trait)
    tool = choose_tool(problem)
    world = tell(setting, problem, hero, tool)
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
        print(asp_program("#show valid_story/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"{len(asp_valid_stories())} compatible story combinations:")
        for s, p, t in asp_valid_stories():
            print(f"  {s:12} {p:14} {t}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        for setting in SETTINGS:
            for problem in PROBLEMS:
                p = StoryParams(setting=setting, problem=problem, name="Elin", gender="girl", trait="curious")
                samples.append(generate(p))
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
            i += 1
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

    for idx, sample in enumerate(samples):
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.name} in {p.setting} / {p.problem}"
        elif len(samples) > 1:
            header = f"### variant {idx + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if idx < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()

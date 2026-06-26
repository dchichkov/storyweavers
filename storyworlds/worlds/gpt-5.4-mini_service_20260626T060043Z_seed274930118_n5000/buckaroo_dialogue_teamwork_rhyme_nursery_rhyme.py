#!/usr/bin/env python3
"""
buckaroo_dialogue_teamwork_rhyme_nursery_rhyme.py
==================================================

A small nursery-rhyme story world about a buckaroo who cannot finish a task
alone, learns to ask for help, and reaches a cheerful team-made ending.

The world is built from a tiny source tale:
- A little buckaroo wants to move a heavy wagon before sunset.
- The wagon is stuck in soft ground.
- The buckaroo speaks up, neighbors answer, and everybody helps.
- Their shared effort frees the wagon, and the buckaroo ends the day proud.

The prose is intentionally rhyme-shaped, gentle, and child-facing.
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
    plural: bool = False
    owner: Optional[str] = None
    helpful: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"boy", "buckaroo", "cowboy", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        if self.type in {"girl", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str
    outdoors: bool = True


@dataclass
class Task:
    id: str
    verb: str
    gerund: str
    difficulty: str
    rhyme_word: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Tool:
    id: str
    label: str
    helps: set[str]
    phrase: str
    team_phrase: str
    plural: bool = False


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.facts: dict = {}
        self.paragraphs: list[list[str]] = [[]]

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
        import copy

        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.facts = dict(self.facts)
        clone.paragraphs = [[]]
        return clone


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------
SETTINGS = {
    "corral": Setting(place="the corral", outdoors=True),
    "barnyard": Setting(place="the barnyard", outdoors=True),
    "trail": Setting(place="the dusty trail", outdoors=True),
}

TASKS = {
    "wagon": Task(
        id="wagon",
        verb="pull the wagon",
        gerund="pulling the wagon",
        difficulty="too heavy",
        rhyme_word="wagon",
        tags={"heavy", "stuck"},
    ),
    "hay": Task(
        id="hay",
        verb="move the hay",
        gerund="moving the hay",
        difficulty="too big",
        rhyme_word="hay",
        tags={"heavy", "bale"},
    ),
    "gate": Task(
        id="gate",
        verb="close the gate",
        gerund="closing the gate",
        difficulty="stiff",
        rhyme_word="gate",
        tags={"stuck", "wood"},
    ),
}

TOOLS = [
    Tool(
        id="rope",
        label="a long rope",
        helps={"wagon", "hay"},
        phrase="pull together with a long rope",
        team_phrase="tied the rope and pulled as one",
    ),
    Tool(
        id="push",
        label="a sturdy push",
        helps={"wagon", "gate"},
        phrase="push shoulder to shoulder",
        team_phrase="stood in a row and gave a sturdy shove",
        plural=False,
    ),
    Tool(
        id="leverage",
        label="a smooth plank",
        helps={"wagon"},
        phrase="use a smooth plank for a lift",
        team_phrase="slid a plank under the wheel and tipped it free",
    ),
]

NAMES = ["Buck", "Milo", "Rudy", "Nell", "Toby", "Joey", "Mabel", "Sally"]
SIDEKICKS = ["Kit", "June", "Cal", "Bo", "Rose", "Finn"]


# ---------------------------------------------------------------------------
# Parametrization
# ---------------------------------------------------------------------------
@dataclass
class StoryParams:
    place: str
    task: str
    name: str
    helper: str
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
task_help(T, Tool) :- task(T), tool(Tool), helps(Tool, T).
valid_story(Place, T, Tool) :- setting(Place), task(T), tool(Tool), task_help(T, Tool).
#show valid_story/3.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for pid in SETTINGS:
        lines.append(asp.fact("setting", pid))
    for tid in TASKS:
        lines.append(asp.fact("task", tid))
    for tool in TOOLS:
        lines.append(asp.fact("tool", tool.id))
        for t in sorted(tool.helps):
            lines.append(asp.fact("helps", tool.id, t))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_stories() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("#show valid_story/3."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    python_set = set(valid_combos())
    clingo_set = set(asp_valid_stories())
    projected = {(p, t, tool) for (p, t, tool) in clingo_set}
    if python_set == projected:
        print(f"OK: clingo gate matches valid_combos() ({len(projected)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    if projected - python_set:
        print("  only in clingo:", sorted(projected - python_set))
    if python_set - projected:
        print("  only in python:", sorted(python_set - projected))
    return 1


# ---------------------------------------------------------------------------
# Story logic
# ---------------------------------------------------------------------------
def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for place in SETTINGS:
        for task in TASKS:
            for tool in TOOLS:
                if task in tool.helps:
                    combos.append((place, task, tool.id))
    return combos


def choose_tool(task: Task) -> Tool:
    for tool in TOOLS:
        if task.id in tool.helps:
            return tool
    raise StoryError("No tool can help with that task.")


def nursery_opening(hero: Entity, task: Task, setting: Setting) -> str:
    return (
        f"Little {hero.id} was a buckaroo bright, "
        f"with a wide-brim hat and eyes of light. "
        f"At {setting.place}, {hero.pronoun('subject')} wanted to {task.verb}, "
        f"but the day had a hitch and a wobble and a slur."
    )


def sing_help(hero: Entity, helper: Entity, task: Task, tool: Tool) -> str:
    return (
        f'"Come help me now," said {hero.id} to {helper.id}, '
        f'"My {task.id} is stuck, and the sun is not done." '
        f'"We will help," said {helper.id}, with a grin and a glance, '
        f'"We can {tool.phrase} and give it a chance."'
    )


def end_rhyme(hero: Entity, helper: Entity, task: Task) -> str:
    return (
        f"So together they tugged, and together they cheered, "
        f"and the stubborn old trouble at once disappeared. "
        f"{hero.id} laughed, {helper.id} clapped, and the corral rang clear; "
        f"the buckaroo learned that teamwork brings cheer."
    )


def simulate(params: StoryParams) -> StorySample:
    setting = SETTINGS[params.place]
    task = TASKS[params.task]
    tool = choose_tool(task)
    world = World(setting)

    hero = world.add(Entity(id=params.name, kind="character", type="buckaroo", label="buckaroo"))
    helper = world.add(Entity(id=params.helper, kind="character", type="friend", label="friend", helpful=True))

    # state
    hero.memes["hope"] = 1.0
    hero.memes["worry"] = 1.0
    world.facts.update(hero=hero, helper=helper, task=task, tool=tool, setting=setting)

    world.say(nursery_opening(hero, task, setting))
    world.para()
    world.say(
        f"{hero.id} tried and tried, but the {task.id} would not budge. "
        f"It was {task.difficulty}, and the wheel sat down in a soft little rut."
    )
    world.say(
        f"{hero.id} took a breath and spoke up, because even brave buckaroos need a hand sometimes."
    )
    world.para()
    helper.memes["kindness"] = 1.0
    hero.memes["bravery"] = 1.0
    world.say(sing_help(hero, helper, task, tool))
    world.say(
        f"Then they smiled and worked as one: {tool.team_phrase}, and the wagon gave way with a squeak and a hum."
    )
    world.para()
    hero.memes["worry"] = 0.0
    hero.memes["joy"] = 1.0
    helper.memes["joy"] = 1.0
    world.say(
        f"{hero.id} tipped {hero.pronoun('possessive')} hat to {helper.id}. "
        f'"Thank you, friend," {hero.pronoun("subject")} said. '
        f'"Your help turned hard work into a song."'
    )
    world.say(end_rhyme(hero, helper, task))

    world.facts["resolved"] = True
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


# ---------------------------------------------------------------------------
# QA
# ---------------------------------------------------------------------------
def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a short nursery-rhyme story about a buckaroo named {f["hero"].id} who needs help with a {f["task"].id}.',
        f"Tell a gentle story where {f['hero'].id} speaks to a friend, they work together, and the {f['task'].id} moves at {f['setting'].place}.",
        f"Write a rhyme-shaped story for little children with dialogue, teamwork, and a happy ending.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero: Entity = f["hero"]
    helper: Entity = f["helper"]
    task: Task = f["task"]
    tool: Tool = f["tool"]
    setting: Setting = f["setting"]
    return [
        QAItem(
            question=f"Who is the story about?",
            answer=f"The story is about {hero.id}, a little buckaroo at {setting.place} who wants to {task.verb}.",
        ),
        QAItem(
            question=f"What problem made the task hard?",
            answer=f"The {task.id} was {task.difficulty}, so {hero.id} could not finish it alone.",
        ),
        QAItem(
            question=f"Who helped {hero.id}?",
            answer=f"{helper.id} helped {hero.id}, and together they used {tool.label} to make the work easier.",
        ),
        QAItem(
            question=f"How did the story end?",
            answer=f"The {task.id} moved free, and {hero.id} thanked {helper.id} for the teamwork.",
        ),
    ]


WORLD_KNOWLEDGE = {
    "buckaroo": [
        (
            "What is a buckaroo?",
            "A buckaroo is a cowboy word for a person who works with horses or cattle on a ranch.",
        )
    ],
    "rope": [
        (
            "What does a rope do?",
            "A rope is a long, strong cord that people can use to tie, pull, or lift things together.",
        )
    ],
    "wagon": [
        (
            "What is a wagon?",
            "A wagon is a vehicle with wheels that can carry people or things and can be pulled along.",
        )
    ],
    "teamwork": [
        (
            "What is teamwork?",
            "Teamwork means people help each other and do a job together so it becomes easier.",
        )
    ],
    "song": [
        (
            "Why do people sing while working sometimes?",
            "People sometimes sing while working because a song can help them keep time and feel cheerful.",
        )
    ],
}


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [QAItem(question=q, answer=a) for q, a in WORLD_KNOWLEDGE["buckaroo"] + WORLD_KNOWLEDGE["rope"] + WORLD_KNOWLEDGE["wagon"] + WORLD_KNOWLEDGE["teamwork"] + WORLD_KNOWLEDGE["song"]]


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


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        bits = []
        if e.memes:
            bits.append(f"memes={dict(e.memes)}")
        if e.meters:
            bits.append(f"meters={dict(e.meters)}")
        lines.append(f"  {e.id:10} ({e.type}) {' '.join(bits)}")
    return "\n".join(lines)


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Nursery-rhyme story world: a buckaroo, a task, and teamwork."
    )
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--task", choices=TASKS)
    ap.add_argument("--name")
    ap.add_argument("--helper")
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
    if args.place:
        combos = [c for c in combos if c[0] == args.place]
    if args.task:
        combos = [c for c in combos if c[1] == args.task]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, task, _tool = rng.choice(sorted(combos))
    name = args.name or rng.choice(NAMES)
    helper = args.helper or rng.choice([n for n in SIDEKICKS if n != name])
    return StoryParams(place=place, task=task, name=name, helper=helper)


def generate(params: StoryParams) -> StorySample:
    return simulate(params)


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
    StoryParams(place="corral", task="wagon", name="Buck", helper="Kit"),
    StoryParams(place="barnyard", task="hay", name="Milo", helper="June"),
    StoryParams(place="trail", task="gate", name="Rudy", helper="Bo"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid_story/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        stories = asp_valid_stories()
        print(f"{len(stories)} compatible stories:")
        for p, t, tool in stories:
            print(f"  {p:10} {t:8} {tool:8}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 20, 20):
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

    for i, sample in enumerate(samples):
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.name}: {p.task} at {p.place}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""
A small animal story world about snazzy bureaucracy and a transformation mystery.

Premise:
- Animals work in a tiny office where forms, stamps, and folders matter.
- A strange transformation has happened: one animal has become "different" in a way
  the office must explain and fix.
- The story follows a clear path: ordinary office life, an unsettling mystery,
  a careful investigation, and a resolution that restores balance.

The world is intentionally small and constraint-checked.  It supports:
- a reasonableness gate for valid stories
- inline ASP rules mirroring the Python gate
- deterministic generation from a sampled parameter set
- story-grounded QA and generic world-knowledge QA
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
# World constants
# ---------------------------------------------------------------------------

DEPARTMENTS = {
    "records": {
        "label": "the records room",
        "furniture": "shelves of folders",
        "affords": {"stamp", "file", "sort"},
    },
    "mail": {
        "label": "the mail desk",
        "furniture": "a brass tray and neat envelopes",
        "affords": {"stamp", "deliver", "sort"},
    },
    "registry": {
        "label": "the registry hall",
        "furniture": "a long counter with labeled drawers",
        "affords": {"stamp", "file", "inspect"},
    },
}

ANIMALS = {
    "fox": {"article": "a", "traits": {"smart", "quick"}},
    "rabbit": {"article": "a", "traits": {"small", "swift"}},
    "bear": {"article": "a", "traits": {"patient", "careful"}},
    "owl": {"article": "an", "traits": {"quiet", "wise"}},
    "otter": {"article": "an", "traits": {"playful", "nimble"}},
    "dog": {"article": "a", "traits": {"loyal", "friendly"}},
}

JOBS = {
    "clerk": "clerk",
    "messenger": "messenger",
    "inspector": "inspector",
}

ACTIONS = {
    "stamp": {
        "verb": "stamp the form",
        "gerund": "stamping forms",
        "mystery": "the ink had changed color",
        "clue": "the blue stamp had turned gold",
        "effect": "the office records looked different",
        "risk": "the records could be filed wrong",
    },
    "file": {
        "verb": "file the papers",
        "gerund": "filing papers",
        "mystery": "the labels had slid out of order",
        "clue": "the folder tabs had been swapped",
        "effect": "the folders no longer matched their names",
        "risk": "the registry could lose track of the right record",
    },
    "sort": {
        "verb": "sort the mail",
        "gerund": "sorting mail",
        "mystery": "the envelopes had all landed in the wrong pile",
        "clue": "the red ribbon on the urgent stack was missing",
        "effect": "the mail piles looked mixed up",
        "risk": "an important letter could be delayed",
    },
    "inspect": {
        "verb": "inspect the badge",
        "gerund": "inspecting badges",
        "mystery": "one badge had become sparkly and strange",
        "clue": "the badge shine matched a hidden polish tin",
        "effect": "the badge no longer looked official",
        "risk": "the office might not know who belonged where",
    },
    "deliver": {
        "verb": "deliver the message",
        "gerund": "delivering messages",
        "mystery": "the route map had been folded into a new shape",
        "clue": "the map corners were bent by tiny paws",
        "effect": "the delivery path was confusing",
        "risk": "the message could reach the wrong desk",
    },
}

TRANSFORMATIONS = {
    "small": {
        "kind": "size",
        "before": "tiny",
        "after": "tall",
        "change": "grew taller",
        "sign": "a chair seemed too short for it",
    },
    "colorful": {
        "kind": "appearance",
        "before": "plain",
        "after": "snazzy",
        "change": "looked snazzier",
        "sign": "its ribbon was suddenly bright and shiny",
    },
    "quiet": {
        "kind": "voice",
        "before": "loud",
        "after": "soft",
        "change": "spoke in a softer voice",
        "sign": "its words came out like whispers",
    },
    "dusty": {
        "kind": "texture",
        "before": "smooth",
        "after": "dusty",
        "change": "had a dusty coat",
        "sign": "a faint powder was on its paws",
    },
}

TOOLS = {
    "magnifier": "a brass magnifier",
    "ledger": "a heavy ledger",
    "stamp": "a snazzy stamp",
    "brush": "a soft polish brush",
}

PLACES = ["records room", "mail desk", "registry hall"]

GREETINGS = [
    "snazzy",
    "proper",
    "tidy",
    "neat",
    "careful",
]

NAMES = {
    "fox": ["Fenn", "Pip", "Tavi"],
    "rabbit": ["Milo", "Nina", "Penny"],
    "bear": ["Bram", "Mara", "Nell"],
    "owl": ["Orin", "Luma", "Tess"],
    "otter": ["Juno", "Rill", "Sora"],
    "dog": ["Buster", "Nori", "Deli"],
}

TRAITS = ["snazzy", "cheerful", "careful", "curious", "patient", "brisk"]


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    animal: str = "thing"
    label: str = ""
    job: str = ""
    plural: bool = False
    owner: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def noun(self) -> str:
        return self.label or self.animal


@dataclass
class Setting:
    department: str


@dataclass
class Mystery:
    action: str
    transformation: str
    tool: str
    solved_by: str


@dataclass
class StoryParams:
    setting: str
    animal: str
    name: str
    job: str
    action: str
    transformation: str
    seed: Optional[int] = None


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.facts: dict[str, object] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()

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


def _article_for(word: str) -> str:
    return "an" if word[:1].lower() in "aeiou" else "a"


def valid_combo(setting: str, action: str, transformation: str) -> bool:
    return setting in DEPARTMENTS and action in ACTIONS and transformation in TRANSFORMATIONS


def explain_rejection(setting: str, action: str, transformation: str) -> str:
    if setting not in DEPARTMENTS:
        return "(No story: the requested office setting is not available.)"
    if action not in ACTIONS:
        return "(No story: that office task is not part of this little world.)"
    if transformation not in TRANSFORMATIONS:
        return "(No story: that transformation is not one this storyworld can tell.)"
    return "(No story: that combination does not make a clear mystery and fix.)"


def build_world(params: StoryParams) -> World:
    if not valid_combo(params.setting, params.action, params.transformation):
        raise StoryError(explain_rejection(params.setting, params.action, params.transformation))

    world = World(Setting(department=params.setting))
    animal_info = ANIMALS[params.animal]
    action = ACTIONS[params.action]
    trans = TRANSFORMATIONS[params.transformation]

    hero = world.add(Entity(
        id=params.name,
        kind="character",
        animal=params.animal,
        label=params.name,
        job=params.job,
        meters={"busy": 1.0},
        memes={"curious": 1.0, "uneasy": 0.0, "relief": 0.0},
    ))
    boss = world.add(Entity(
        id="boss",
        kind="character",
        animal="mouse",
        label="the office mouse boss",
        job="manager",
        meters={"busy": 1.0},
        memes={"calm": 1.0},
    ))
    clue = world.add(Entity(
        id="clue",
        kind="thing",
        animal="thing",
        label=action["clue"],
    ))
    tool = world.add(Entity(
        id="tool",
        kind="thing",
        animal="thing",
        label=TOOLS["stamp"] if params.action == "stamp" else TOOLS["magnifier"],
    ))
    mystery = Mystery(
        action=params.action,
        transformation=params.transformation,
        tool=tool.label,
        solved_by="careful checking",
    )

    # Act 1: ordinary office life.
    dept = DEPARTMENTS[params.setting]
    world.say(
        f"In {dept['label']}, {params.name} the {params.animal} worked as "
        f"{_article_for(params.job)} {params.job}."
    )
    world.say(
        f"{params.name} was {animal_info['traits'].pop() if animal_info['traits'] else 'careful'} "
        f"and liked the office because it was so {random.choice(GREETINGS)}."
    )
    world.say(f"The room was full of {dept['furniture']} and neat little rules.")

    # Act 2: mystery appears.
    world.para()
    world.say(
        f"One morning, while {params.name} was {action['gerund']}, something strange happened."
    )
    world.say(f"{action['mystery'].capitalize()}.")
    world.say(
        f"Even stranger, {params.name} {trans['change']}; {trans['sign']}."
    )
    world.say(
        f"That made the office feel uneasy, because {action['effect']} and {action['risk']}."
    )
    world.facts["mystery"] = mystery
    world.facts["clue"] = clue.label
    world.facts["transformation"] = trans["kind"]
    world.facts["before"] = trans["before"]
    world.facts["after"] = trans["after"]

    # Act 3: investigation and resolution.
    world.para()
    world.say(
        f"The office mouse boss handed over {tool.label} and said, "
        f'"Let us look closely and solve this mystery."'
    )
    world.say(
        f"{params.name} checked the {params.action} station, then noticed that {clue.label}."
    )
    world.say(
        f"The clue pointed to a tiny polish tin hidden behind the folders, and that explained the change."
    )
    world.say(
        f"{params.name} used {tool.label} to match the clue, put the tin back in the supply drawer, "
        f"and set everything in order again."
    )
    world.say(
        f"After that, {params.name} was still {params.transformation if params.transformation == 'colorful' else 'the same kind of'} "
        f"{params.animal}, but the office looked normal, the paperwork was safe, and the boss smiled."
    )

    world.facts.update(
        hero=hero,
        boss=boss,
        setting=dept,
        action=action,
        tool=tool,
        mystery=mystery,
        resolved=True,
    )
    return world


def generation_prompts(world: World) -> list[str]:
    p = world.facts
    hero: Entity = p["hero"]
    action = p["action"]
    return [
        f"Write a short animal story about a snazzy bureaucracy mystery where {hero.id} must solve a strange change.",
        f"Tell a simple story in an office with animals, paperwork, and a clue about {action['mystery']}.",
        f"Write a child-friendly story about {hero.id} the {hero.animal} finding out why the office became snazzier and strange.",
    ]


def story_qa(world: World) -> list[QAItem]:
    p = world.facts
    hero: Entity = p["hero"]
    action = p["action"]
    trans: dict = TRANSFORMATIONS[world.facts["mystery"].transformation] if isinstance(world.facts["mystery"], Mystery) else {}
    setting = p["setting"]["label"]
    return [
        QAItem(
            question=f"Who was the story about in {setting}?",
            answer=f"It was about {hero.id}, a {hero.animal} who worked there as a {hero.job}.",
        ),
        QAItem(
            question=f"What strange thing happened while {hero.id} was working?",
            answer=f"{action['mystery'].capitalize()}, and then {hero.id} {TRANSFORMATIONS[world.facts['mystery'].transformation]['change']}.",
        ),
        QAItem(
            question=f"How did the office mystery get solved?",
            answer=f"{hero.id} used a careful clue check with the office tool, found the hidden polish tin, and put everything back in order.",
        ),
        QAItem(
            question=f"What was the ending like after the mystery was solved?",
            answer=f"The office looked normal again, the paperwork was safe, and {hero.id} could keep working without confusion.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is bureaucracy?",
            answer="Bureaucracy is a system where people or animals use rules, forms, and offices to keep things organized.",
        ),
        QAItem(
            question="What is a mystery?",
            answer="A mystery is something strange that you do not understand right away, so you have to look for clues.",
        ),
        QAItem(
            question="What is a transformation?",
            answer="A transformation is a change from one form or state into another.",
        ),
        QAItem(
            question="Why do offices use files and stamps?",
            answer="Offices use files and stamps to keep papers organized and to show that a form has been checked.",
        ),
    ]


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for ent in world.entities.values():
        lines.append(
            f"  {ent.id:8} kind={ent.kind} label={ent.label!r} meters={ent.meters} memes={ent.memes}"
        )
    lines.append(f"  facts={list(world.facts.keys())}")
    return "\n".join(lines)


def format_qa(sample: StorySample) -> str:
    lines = ["== generation prompts ==", *[f"- {p}" for p in sample.prompts], "",
             "== story questions =="]
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== world questions ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


ASP_RULES = r"""
setting(S) :- dept(S).
action(A) :- act(A).
transformation(T) :- trans(T).

mystery(Setting, Action, Transformation) :-
    setting(Setting), action(Action), transformation(Transformation),
    valid_combo(Setting, Action, Transformation).

solved(Setting, Action, Transformation) :-
    mystery(Setting, Action, Transformation),
    clue_found(Action),
    careful_checking,
    returned_to_order.
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid in DEPARTMENTS:
        lines.append(asp.fact("dept", sid))
    for aid in ACTIONS:
        lines.append(asp.fact("act", aid))
    for tid in TRANSFORMATIONS:
        lines.append(asp.fact("trans", tid))
    for s in DEPARTMENTS:
        for a in ACTIONS:
            for t in TRANSFORMATIONS:
                if valid_combo(s, a, t):
                    lines.append(asp.fact("valid_combo", s, a, t))
    lines.append(asp.fact("clue_found", "stamp"))
    lines.append(asp.fact("careful_checking"))
    lines.append(asp.fact("returned_to_order"))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    program = asp_program("#show valid_combo/3.")
    model = asp.one_model(program)
    clingo_set = set(asp.atoms(model, "valid_combo"))
    py_set = set((s, a, t) for s in DEPARTMENTS for a in ACTIONS for t in TRANSFORMATIONS if valid_combo(s, a, t))
    if clingo_set == py_set:
        print(f"OK: clingo gate matches valid_combo() ({len(clingo_set)} combos).")
        return 0
    print("MISMATCH between clingo and Python gate:")
    print(" only in clingo:", sorted(clingo_set - py_set))
    print(" only in python:", sorted(py_set - clingo_set))
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Animal storyworld about snazzy bureaucracy and a transformation mystery.")
    ap.add_argument("--setting", choices=sorted(DEPARTMENTS))
    ap.add_argument("--animal", choices=sorted(ANIMALS))
    ap.add_argument("--name")
    ap.add_argument("--job", choices=sorted(JOBS))
    ap.add_argument("--action", choices=sorted(ACTIONS))
    ap.add_argument("--transformation", choices=sorted(TRANSFORMATIONS))
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
    setting = args.setting or rng.choice(list(DEPARTMENTS))
    action = args.action or rng.choice(list(ACTIONS))
    transformation = args.transformation or rng.choice(list(TRANSFORMATIONS))
    if not valid_combo(setting, action, transformation):
        raise StoryError(explain_rejection(setting, action, transformation))
    animal = args.animal or rng.choice(list(ANIMALS))
    job = args.job or rng.choice(list(JOBS))
    name = args.name or rng.choice(NAMES[animal])
    return StoryParams(setting=setting, animal=animal, name=name, job=job, action=action, transformation=transformation)


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
    StoryParams(setting="records", animal="fox", name="Fenn", job="clerk", action="stamp", transformation="colorful"),
    StoryParams(setting="mail", animal="rabbit", name="Nina", job="messenger", action="deliver", transformation="small"),
    StoryParams(setting="registry", animal="owl", name="Orin", job="inspector", action="inspect", transformation="quiet"),
]


def asp_list() -> None:
    import asp
    program = asp_program("#show mystery/3.\n#show solved/3.")
    model = asp.one_model(program)
    mysteries = sorted(set(asp.atoms(model, "mystery")))
    solved = sorted(set(asp.atoms(model, "solved")))
    print(f"{len(mysteries)} mystery combos, {len(solved)} solved combos")
    for triple in mysteries:
        print(" ", triple)


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show mystery/3.\n#show solved/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        asp_list()
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

    for idx, sample in enumerate(samples):
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.name}: {p.animal} {p.job} in {p.setting} (action: {p.action}, change: {p.transformation})"
        elif len(samples) > 1:
            header = f"### variant {idx + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if idx < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()

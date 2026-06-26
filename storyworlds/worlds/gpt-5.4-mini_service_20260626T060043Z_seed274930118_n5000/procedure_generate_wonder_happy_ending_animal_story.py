#!/usr/bin/env python3
"""
storyworlds/worlds/procedure_generate_wonder_happy_ending_animal_story.py
========================================================================

A small animal-story world with a gentle procedural twist: an animal notices a
problem, follows a simple procedure, and ends with a happy wonder-filled ending.

Seed idea:
- Animal Story style
- include the words procedure, generate, wonder
- happy ending
- a tiny simulated domain where an animal friend helps another animal
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
# Domain data
# ---------------------------------------------------------------------------

@dataclass
class Animal:
    id: str
    kind: str
    name: str
    role: str
    home: str
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def subject(self) -> str:
        return self.name

    def possessive(self) -> str:
        return f"{self.name}'s"

    def pronoun(self) -> str:
        return "they"


@dataclass
class Item:
    id: str
    name: str
    location: str
    owner: Optional[str] = None
    found: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)


@dataclass
class Place:
    id: str
    name: str
    feature: str


@dataclass
class StoryParams:
    place: str
    hero_kind: str
    helper_kind: str
    problem: str
    tool: str
    name: str
    seed: Optional[int] = None


class World:
    def __init__(self, place: Place) -> None:
        self.place = place
        self.animals: dict[str, Animal] = {}
        self.items: dict[str, Item] = {}
        self.events: list[str] = []
        self.facts: dict[str, object] = {}

    def say(self, text: str) -> None:
        if text:
            self.events.append(text)

    def render(self) -> str:
        return " ".join(self.events)


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------

PLACES = {
    "meadow": Place(id="meadow", name="the meadow", feature="tall grass"),
    "pond": Place(id="pond", name="the pond", feature="shiny water"),
    "forest": Place(id="forest", name="the forest", feature="soft moss"),
    "hill": Place(id="hill", name="the hill", feature="a breezy hilltop"),
}

ANIMAL_NAMES = {
    "rabbit": ["Milo", "Pip", "Clover", "Nina"],
    "fox": ["Ruby", "Finn", "Tara", "Juno"],
    "bear": ["Benny", "Mira", "Toby", "Luna"],
    "mouse": ["Dot", "Mimi", "Theo", "Pippa"],
    "duck": ["Quill", "Daisy", "Nori", "Bram"],
}

PROBLEMS = {
    "lost_seed": {
        "noun": "a tiny seed",
        "verb": "find the missing seed",
        "worry": "the garden would be quiet without it",
        "procedure": ["look in the grass", "ask a friend", "follow the shiny path"],
        "fix": "the seed was tucked under a leaf",
    },
    "stuck_ball": {
        "noun": "a red ball",
        "verb": "get the ball down",
        "worry": "the game could not go on without the ball",
        "procedure": ["gather a twig", "push gently", "work together"],
        "fix": "the ball rolled right down into the soft grass",
    },
    "cold_nest": {
        "noun": "a cozy nest",
        "verb": "make the nest warm",
        "worry": "the baby bird would shiver in the evening",
        "procedure": ["collect soft moss", "add a feather", "tuck it in carefully"],
        "fix": "the nest turned warm and snug",
    },
    "muddy_paw": {
        "noun": "a muddy paw",
        "verb": "clean the paw",
        "worry": "the trail would stay messy",
        "procedure": ["step by the pond", "wash in a little water", "shake dry"],
        "fix": "the paw came out clean and neat",
    },
}

TOOLS = {
    "leaf": "a broad leaf",
    "twig": "a little twig",
    "bucket": "a small bucket",
    "cloth": "a soft cloth",
    "shell": "a shiny shell",
}

HERO_KINDS = ["rabbit", "fox", "bear", "mouse", "duck"]
HELPER_KINDS = ["rabbit", "fox", "bear", "mouse", "duck"]


# ---------------------------------------------------------------------------
# Story simulation
# ---------------------------------------------------------------------------

def build_animal(kind: str, name: str, role: str, home: str) -> Animal:
    return Animal(
        id=f"{role}_{kind}_{name}".lower(),
        kind=kind,
        name=name,
        role=role,
        home=home,
        meters={"tired": 0.0, "hope": 0.0, "joy": 0.0},
        memes={"wonder": 0.0, "worry": 0.0, "care": 0.0},
    )


def procedure_steps(problem_id: str) -> list[str]:
    return list(PROBLEMS[problem_id]["procedure"])


def generate_place_sentence(place: Place) -> str:
    return f"The {place.name.removeprefix('the ')} had {place.feature} and felt calm."


def simulate(params: StoryParams) -> World:
    if params.place not in PLACES:
        raise StoryError("Unknown place.")
    if params.hero_kind not in HERO_KINDS:
        raise StoryError("Unknown hero kind.")
    if params.helper_kind not in HELPER_KINDS:
        raise StoryError("Unknown helper kind.")
    if params.problem not in PROBLEMS:
        raise StoryError("Unknown problem.")
    if params.tool not in TOOLS:
        raise StoryError("Unknown tool.")

    place = PLACES[params.place]
    world = World(place)

    name = params.name
    hero = build_animal(params.hero_kind, name, "hero", place.name)
    helper_name = random.choice([n for n in ANIMAL_NAMES[params.helper_kind] if n != name] or ANIMAL_NAMES[params.helper_kind])
    helper = build_animal(params.helper_kind, helper_name, "helper", place.name)
    item = Item(id=f"item_{params.problem}", name=PROBLEMS[params.problem]["noun"], location=place.name)

    world.animals[hero.id] = hero
    world.animals[helper.id] = helper
    world.items[item.id] = item

    # Act 1: setup
    world.say(f"{hero.name} was a little {hero.kind} who loved to wonder about small things.")
    world.say(f"{helper.name} was a kind {helper.kind} who liked to help.")
    world.say(generate_place_sentence(place))
    world.say(f"One day, {hero.name} noticed {item.name} and felt a little worried.")

    # Act 2: problem and procedure
    world.say(f"{hero.name} wanted to {PROBLEMS[params.problem]['verb']}, but it was not easy.")
    world.say(f"{hero.name} and {helper.name} used a simple procedure to help.")
    for step in procedure_steps(params.problem):
        world.say(f"First, they {step}.")
    item.found = True
    item.meters["safe"] = 1.0
    hero.memes["worry"] += 1.0
    hero.memes["wonder"] += 1.0
    helper.memes["care"] += 1.0

    # Act 3: happy ending
    world.say(f"At last, {PROBLEMS[params.problem]['fix']}.")
    world.say(f"{hero.name} smiled, and {helper.name} smiled too.")
    world.say(f"The little friends felt wonder, because a careful procedure had turned trouble into a happy day.")

    world.facts.update(
        hero=hero,
        helper=helper,
        item=item,
        problem_id=params.problem,
        tool_id=params.tool,
        place=place,
        procedure=procedure_steps(params.problem),
    )
    return world


# ---------------------------------------------------------------------------
# Q&A
# ---------------------------------------------------------------------------

def generation_prompts(world: World) -> list[str]:
    hero: Animal = world.facts["hero"]
    helper: Animal = world.facts["helper"]
    problem_id: str = world.facts["problem_id"]
    place: Place = world.facts["place"]
    return [
        f"Write a short animal story that uses the words procedure, generate, and wonder.",
        f"Tell a gentle story about {hero.name} the {hero.kind} and {helper.name} the {helper.kind} at {place.name}, where a small problem needs a careful procedure.",
        f"Write a happy-ending animal story in which friends work together and the ending feels full of wonder.",
        f"Make the story simple, concrete, and child-friendly, with {PROBLEMS[problem_id]['noun']} as the problem.",
    ]


def story_qa(world: World) -> list[QAItem]:
    hero: Animal = world.facts["hero"]
    helper: Animal = world.facts["helper"]
    item: Item = world.facts["item"]
    problem_id: str = world.facts["problem_id"]
    place: Place = world.facts["place"]

    qs = [
        QAItem(
            question=f"Who is the story about?",
            answer=f"The story is about {hero.name}, a little {hero.kind}, and {helper.name}, a kind {helper.kind}.",
        ),
        QAItem(
            question=f"What problem did they face at {place.name}?",
            answer=f"They needed to {PROBLEMS[problem_id]['verb']} because they found {item.name}.",
        ),
        QAItem(
            question=f"What did they use to solve the problem?",
            answer=f"They used a simple procedure with careful steps, and that helped them solve the problem together.",
        ),
        QAItem(
            question=f"How did the story end?",
            answer=f"It ended happily, with {hero.name} smiling and feeling wonder because the trouble was fixed.",
        ),
    ]
    return qs


WORLD_KNOWLEDGE = {
    "procedure": [
        QAItem(
            question="What is a procedure?",
            answer="A procedure is a set of steps you follow in order to do something safely or carefully.",
        )
    ],
    "generate": [
        QAItem(
            question="What does generate mean?",
            answer="Generate means to make or create something, like making an idea or producing a result.",
        )
    ],
    "wonder": [
        QAItem(
            question="What does wonder mean?",
            answer="Wonder means feeling curious and amazed about something special or surprising.",
        )
    ],
    "happy": [
        QAItem(
            question="What is a happy ending?",
            answer="A happy ending is when the problem gets solved and things turn out well.",
        )
    ],
    "animal": [
        QAItem(
            question="Why do animal stories feel friendly for children?",
            answer="Animal stories often feel friendly because animals can talk, help each other, and do kind things like people in a simple way.",
        )
    ],
}


def world_knowledge_qa(world: World) -> list[QAItem]:
    out: list[QAItem] = []
    out.extend(WORLD_KNOWLEDGE["procedure"])
    out.extend(WORLD_KNOWLEDGE["generate"])
    out.extend(WORLD_KNOWLEDGE["wonder"])
    out.extend(WORLD_KNOWLEDGE["happy"])
    out.extend(WORLD_KNOWLEDGE["animal"])
    return out


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
# ASP twin
# ---------------------------------------------------------------------------

ASP_RULES = r"""
animal_kind(rabbit;fox;bear;mouse;duck).
problem(lost_seed;stuck_ball;cold_nest;muddy_paw).
tool(leaf;twig;bucket;cloth;shell).

solvable(P) :- problem(P).
happy_ending(P) :- solvable(P).
wonderful(P) :- happy_ending(P).
"""

def asp_facts() -> str:
    import storyworlds.asp as asp
    lines: list[str] = []
    for k in HERO_KINDS:
        lines.append(asp.fact("animal_kind", k))
    for p in PROBLEMS:
        lines.append(asp.fact("problem", p))
    for t in TOOLS:
        lines.append(asp.fact("tool", t))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import storyworlds.asp as asp
    model = asp.one_model(asp_program("#show happy_ending/1."))
    atoms = set(asp.atoms(model, "happy_ending"))
    expected = {(p,) for p in PROBLEMS}
    if atoms == expected:
        print(f"OK: ASP twin matches Python registry ({len(expected)} problems).")
        return 0
    print("MISMATCH between ASP and Python.")
    print("ASP:", sorted(atoms))
    print("PY :", sorted(expected))
    return 1


# ---------------------------------------------------------------------------
# Serialization / CLI
# ---------------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Animal story world with procedure, generate, and wonder."
    )
    ap.add_argument("--place", choices=sorted(PLACES))
    ap.add_argument("--hero-kind", choices=sorted(HERO_KINDS))
    ap.add_argument("--helper-kind", choices=sorted(HELPER_KINDS))
    ap.add_argument("--problem", choices=sorted(PROBLEMS))
    ap.add_argument("--tool", choices=sorted(TOOLS))
    ap.add_argument("--name")
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
    place = args.place or rng.choice(list(PLACES))
    hero_kind = args.hero_kind or rng.choice(HERO_KINDS)
    helper_kind = args.helper_kind or rng.choice([k for k in HELPER_KINDS if k != hero_kind] or HELPER_KINDS)
    problem = args.problem or rng.choice(list(PROBLEMS))
    tool = args.tool or rng.choice(list(TOOLS))
    name = args.name or rng.choice(ANIMAL_NAMES[hero_kind])
    return StoryParams(
        place=place,
        hero_kind=hero_kind,
        helper_kind=helper_kind,
        problem=problem,
        tool=tool,
        name=name,
    )


def generate(params: StoryParams) -> StorySample:
    world = simulate(params)
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
    lines.append(f"place: {world.place.name} ({world.place.feature})")
    for animal in world.animals.values():
        lines.append(
            f"animal {animal.name} [{animal.kind}] meters={animal.meters} memes={animal.memes}"
        )
    for item in world.items.values():
        lines.append(
            f"item {item.name} found={item.found} meters={item.meters} memes={item.memes}"
        )
    lines.append("facts: " + ", ".join(sorted(world.facts.keys())))
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
    StoryParams(place="meadow", hero_kind="rabbit", helper_kind="fox", problem="lost_seed", tool="leaf", name="Milo"),
    StoryParams(place="pond", hero_kind="duck", helper_kind="bear", problem="muddy_paw", tool="bucket", name="Daisy"),
    StoryParams(place="forest", hero_kind="mouse", helper_kind="rabbit", problem="cold_nest", tool="cloth", name="Dot"),
    StoryParams(place="hill", hero_kind="fox", helper_kind="duck", problem="stuck_ball", tool="twig", name="Ruby"),
]


def asp_mode() -> None:
    import storyworlds.asp as asp
    model = asp.one_model(asp_program("#show wonderful/1."))
    vals = sorted(set(asp.atoms(model, "wonderful")))
    print(f"{len(vals)} wonderful problems:")
    for (p,) in vals:
        print(f"  {p}")


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show wonderful/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        asp_mode()
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
            params = resolve_params(args, random.Random(base_seed + i))
            i += 1
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
            header = f"### {p.name}: {p.problem} at {p.place} ({p.hero_kind} with {p.helper_kind})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()

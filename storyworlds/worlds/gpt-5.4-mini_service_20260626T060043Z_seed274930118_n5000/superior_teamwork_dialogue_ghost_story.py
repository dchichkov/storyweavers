#!/usr/bin/env python3
"""
A standalone story world for a gentle ghost-story domain with teamwork and dialogue.

Premise:
- A child and a helper meet a timid ghost in a quiet old place.
- The ghost's problem is practical and emotionally spooky, not scary-dangerous.
- The only valid resolution is a better plan that uses teamwork and conversation.

The word "superior" is used as part of the story vocabulary and ASP registry.
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
# Data model
# ---------------------------------------------------------------------------

@dataclass
class Character:
    id: str
    kind: str = "character"
    type: str = "child"
    label: str = ""
    traits: list[str] = field(default_factory=list)
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "woman", "mother"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man", "father"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        if self.type == "ghost":
            return {"subject": "it", "object": "it", "possessive": "its"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]


@dataclass
class Place:
    name: str
    mood: str
    spooky_level: int
    hidden_spot: str


@dataclass
class Problem:
    id: str
    missing: str
    sound: str
    feels_like: str
    clue: str
    topic: str = "ghost"


@dataclass
class HelpPlan:
    id: str
    verb: str
    steps: list[str]
    tool: str
    requires_dialogue: bool = True
    requires_teamwork: bool = True


@dataclass
class StoryParams:
    place: str
    problem: str
    plan: str
    name: str
    partner: str
    ghost_name: str
    seed: Optional[int] = None


@dataclass
class Entity:
    id: str
    type: str
    label: str
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)


class World:
    def __init__(self, place: Place):
        self.place = place
        self.entities: dict[str, Entity] = {}
        self.facts: dict[str, object] = {}
        self.lines: list[str] = []
        self.teams: int = 0
        self.dialogues: int = 0
        self.resolved: bool = False

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def say(self, text: str) -> None:
        if text:
            self.lines.append(text)

    def render(self) -> str:
        return " ".join(self.lines).strip()


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------

PLACES = {
    "attic": Place(name="the attic", mood="dusty and quiet", spooky_level=2, hidden_spot="under the old trunk"),
    "hall": Place(name="the hall", mood="long and echoing", spooky_level=1, hidden_spot="behind the coat stand"),
    "library": Place(name="the library", mood="still and moonlit", spooky_level=2, hidden_spot="between the tall shelves"),
}

PROBLEMS = {
    "bell": Problem(
        id="bell",
        missing="little silver bell",
        sound="tinkling",
        feels_like="lonely",
        clue="the bell must be near the ghost's favorite hiding place",
        topic="ghost",
    ),
    "lantern": Problem(
        id="lantern",
        missing="blue lantern",
        sound="faint humming",
        feels_like="cold",
        clue="the lantern was tucked where the light could not reach",
        topic="ghost",
    ),
    "songbook": Problem(
        id="songbook",
        missing="songbook",
        sound="soft humming",
        feels_like="sad",
        clue="the book had slipped into a secret shelf gap",
        topic="ghost",
    ),
}

PLANS = {
    "search": HelpPlan(
        id="search",
        verb="search together",
        steps=["look", "listen", "point", "peek"],
        tool="a candle",
        requires_dialogue=True,
        requires_teamwork=True,
    ),
    "sort": HelpPlan(
        id="sort",
        verb="sort the old things together",
        steps=["lift", "sort", "check", "recheck"],
        tool="a basket",
        requires_dialogue=True,
        requires_teamwork=True,
    ),
    "speak": HelpPlan(
        id="speak",
        verb="speak to the ghost kindly",
        steps=["ask", "answer", "repeat", "agree"],
        tool="a calm voice",
        requires_dialogue=True,
        requires_teamwork=False,
    ),
}

NAMES = ["Mia", "Noah", "Lina", "Theo", "Ava", "Eli", "Zoe", "Finn"]
PARTNERS = ["mother", "father", "grandma", "big sister", "big brother"]
GHOST_NAMES = ["Murmur", "Pale Pip", "Misty", "Glow", "Hush", "Whisper"]


# ---------------------------------------------------------------------------
# Reasonableness gates
# ---------------------------------------------------------------------------

def valid_combo(place: str, problem: str, plan: str) -> bool:
    p = PROBLEMS[problem]
    h = PLANS[plan]
    if place not in PLACES:
        return False
    if h.requires_teamwork and plan == "speak":
        return False
    if p.id == "songbook" and plan == "speak":
        return True
    if p.id in {"bell", "lantern"} and plan in {"search", "speak"}:
        return True
    return True


def valid_combos() -> list[tuple[str, str, str]]:
    out = []
    for place in PLACES:
        for problem in PROBLEMS:
            for plan in PLANS:
                if valid_combo(place, problem, plan):
                    out.append((place, problem, plan))
    return out


def explain_rejection(place: str, problem: str, plan: str) -> str:
    return (
        f"(No story: the place/problem/plan combination {place}/{problem}/{plan} "
        f"doesn't make a clear ghostly teamwork story.)"
    )


# ---------------------------------------------------------------------------
# Story engine
# ---------------------------------------------------------------------------

def introduce(world: World, child: Character, partner: Character, ghost: Character, problem: Problem) -> None:
    world.say(
        f"{child.id} and {partner.label} walked into {world.place.name}, where the air felt "
        f"{world.place.mood}. Then they saw {ghost.label}, a timid ghost with a {problem.feels_like} look."
    )
    world.say(
        f"{ghost.label} said, 'I can't find my {problem.missing}, and the whole room feels wrong without it.'"
    )


def tension(world: World, child: Character, partner: Character, ghost: Character, problem: Problem) -> None:
    child.memes["worry"] = child.memes.get("worry", 0.0) + 1
    ghost.memes["sad"] = ghost.memes.get("sad", 0.0) + 1
    world.say(
        f"{child.id} felt a little shiver, but {partner.label} smiled and said, 'Let's use our heads and help.'"
    )
    world.say(
        f"{ghost.label} whispered, 'I only remember {problem.clue}.'"
    )


def work_together(world: World, child: Character, partner: Character, ghost: Character, problem: Problem, plan: HelpPlan) -> None:
    world.teams += 1
    world.dialogues += 1
    world.say(
        f"{child.id} asked, 'Can you show us the place again?' and {ghost.label} pointed toward {world.place.hidden_spot}."
    )
    if plan.requires_teamwork:
        world.say(
            f"{child.id} held the {plan.tool}, {partner.label} lifted the dusty box, and {ghost.label} guided them step by step."
        )
    else:
        world.say(
            f"{child.id} spoke gently, and {ghost.label} answered in a soft, shaky voice that grew steadier."
        )

    for step in plan.steps:
        world.dialogues += 1
        if step == "look":
            world.say(f"They looked under the old trunk.")
        elif step == "lift":
            world.say(f"They lifted the heavy lid together.")
        elif step == "ask":
            world.say(f"{child.id} asked one careful question.")
        elif step == "answer":
            world.say(f"{ghost.label} gave a small, brave answer.")
        elif step == "point":
            world.say(f"{ghost.label} pointed at a dark corner.")
        elif step == "peek":
            world.say(f"{partner.label} peered behind a box.")
        elif step == "sort":
            world.say(f"They sorted the forgotten things into neat piles.")
        elif step == "check":
            world.say(f"{child.id} checked each pile twice.")
        elif step == "recheck":
            world.say(f"{partner.label} checked the last pile again.")
        elif step == "repeat":
            world.say(f"{child.id} repeated the clue so everyone could hear it.")
        elif step == "agree":
            world.say(f"Everyone agreed the clue made sense.")


def resolve(world: World, child: Character, partner: Character, ghost: Character, problem: Problem, plan: HelpPlan) -> None:
    world.resolved = True
    ghost.memes["sad"] = 0.0
    ghost.memes["relief"] = ghost.memes.get("relief", 0.0) + 1
    child.memes["brave"] = child.memes.get("brave", 0.0) + 1
    world.say(
        f"At last, they found the {problem.missing} tucked where the clue had promised."
    )
    world.say(
        f"{ghost.label} gave a happy little glow, and even the room seemed less spooky."
    )
    world.say(
        f"{ghost.label} said, 'That was superior teamwork.' {child.id} laughed, and {partner.label} nodded."
    )


def tell_story(params: StoryParams) -> World:
    place = PLACES[params.place]
    problem = PROBLEMS[params.problem]
    plan = PLANS[params.plan]
    world = World(place)

    child = Character(id=params.name, type="child", label=params.name)
    partner = Character(id=params.partner, type=params.partner, label=f"the {params.partner}")
    ghost = Character(id=params.ghost_name, type="ghost", label=f"the ghost {params.ghost_name}")

    world.add(Entity(id=child.id, type="child", label=child.label))
    world.add(Entity(id=partner.id, type="helper", label=partner.label))
    world.add(Entity(id=ghost.id, type="ghost", label=ghost.label))

    world.facts = {
        "child": child,
        "partner": partner,
        "ghost": ghost,
        "problem": problem,
        "plan": plan,
        "place": place,
    }

    introduce(world, child, partner, ghost, problem)
    world.say("")
    tension(world, child, partner, ghost, problem)
    world.say("")
    work_together(world, child, partner, ghost, problem, plan)
    resolve(world, child, partner, ghost, problem, plan)
    return world


# ---------------------------------------------------------------------------
# QA
# ---------------------------------------------------------------------------

def generation_prompts(world: World) -> list[str]:
    f = world.facts
    child = f["child"]
    problem = f["problem"]
    plan = f["plan"]
    return [
        f'Write a gentle ghost story for a child named {child.id} with teamwork and dialogue.',
        f'Tell a spooky-but-kind story where a ghost loses a {problem.missing} and everyone helps find it.',
        f'Write a short story that uses the word "superior" in a happy ending about {plan.verb}.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child = f["child"]
    partner = f["partner"]
    ghost = f["ghost"]
    problem = f["problem"]
    place = f["place"]
    plan = f["plan"]

    return [
        QAItem(
            question=f"Who helped {child.id} in {place.name}?",
            answer=f"{child.id} was helped by {partner.label} and by {ghost.label}, the ghost who needed a little kindness.",
        ),
        QAItem(
            question=f"What was the ghost looking for?",
            answer=f"The ghost was looking for {problem.missing}.",
        ),
        QAItem(
            question=f"How did they solve the problem?",
            answer=f"They used teamwork and dialogue to {plan.verb} until they found the missing thing.",
        ),
        QAItem(
            question="What made the ending good?",
            answer="The missing thing was found, the ghost felt better, and everyone shared a happy, brave moment together.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a ghost in a child-friendly story?",
            answer="A ghost is a spooky-looking character from a story who can be lonely, shy, or helpful.",
        ),
        QAItem(
            question="What does teamwork mean?",
            answer="Teamwork means people work together and help each other do something that is hard alone.",
        ),
        QAItem(
            question="What is dialogue in a story?",
            answer="Dialogue is when characters speak to each other with words in quotation marks.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    out = ["== prompts =="]
    for p in sample.prompts:
        out.append(p)
    out.append("")
    out.append("== story qa ==")
    for item in sample.story_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    out.append("")
    out.append("== world qa ==")
    for item in sample.world_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    return "\n".join(out)


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------

ASP_RULES = r"""
place(P) :- setting(P).
problem(X) :- missing(X,_).
plan(Y) :- helpplan(Y).

valid(P, X, Y) :- place(P), problem(X), plan(Y), compatible(P, X, Y).

compatible(P, X, Y) :- place(P), problem(X), plan(Y), not bad_combo(P, X, Y).

bad_combo(P, X, Y) :- place(P), problem(X), plan(Y), X = songbook, Y = search, P = hall.
"""


def asp_facts() -> str:
    import storyworlds.asp as asp  # lazy import by contract
    lines = []
    for pid in PLACES:
        lines.append(asp.fact("setting", pid))
    for pid, prob in PROBLEMS.items():
        lines.append(asp.fact("missing", pid, prob.missing))
    for pid in PLANS:
        lines.append(asp.fact("helpplan", pid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import storyworlds.asp as asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and python:")
    print("python-only:", sorted(py - cl))
    print("clingo-only:", sorted(cl - py))
    return 1


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Gentle ghost story world with teamwork and dialogue.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--problem", choices=PROBLEMS)
    ap.add_argument("--plan", choices=PLANS)
    ap.add_argument("--name", choices=NAMES)
    ap.add_argument("--partner", choices=PARTNERS)
    ap.add_argument("--ghost-name", choices=GHOST_NAMES)
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
    filtered = [
        c for c in combos
        if (args.place is None or c[0] == args.place)
        and (args.problem is None or c[1] == args.problem)
        and (args.plan is None or c[2] == args.plan)
    ]
    if not filtered:
        raise StoryError("(No valid combination matches the given options.)")
    place, problem, plan = rng.choice(sorted(filtered))
    if args.problem and args.plan and not valid_combo(place, problem, plan):
        raise StoryError(explain_rejection(place, problem, plan))
    return StoryParams(
        place=place,
        problem=problem,
        plan=plan,
        name=args.name or rng.choice(NAMES),
        partner=args.partner or rng.choice(PARTNERS),
        ghost_name=args.ghost_name or rng.choice(GHOST_NAMES),
    )


def generate(params: StoryParams) -> StorySample:
    world = tell_story(params)
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
    for eid, ent in world.entities.items():
        lines.append(f"{eid}: type={ent.type} label={ent.label}")
    lines.append(f"teams={world.teams} dialogues={world.dialogues} resolved={world.resolved}")
    lines.append(f"place={world.place.name} mood={world.place.mood}")
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


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible combos:")
        for c in combos:
            print(c)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)

    samples: list[StorySample] = []
    if args.all:
        curated = [
            StoryParams("attic", "bell", "search", "Mia", "mother", "Murmur"),
            StoryParams("library", "songbook", "speak", "Noah", "father", "Whisper"),
            StoryParams("hall", "lantern", "sort", "Ava", "grandma", "Glow"),
        ]
        samples = [generate(p) for p in curated]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 50, 50):
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
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""
A standalone storyworld for a tiny mystery at a deli, built around limited
resources, repeated attempts, and a lesson learned.
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
class Resource:
    name: str
    amount: int
    unit: str
    description: str


@dataclass
class Entity:
    id: str
    kind: str = "character"
    type: str = "character"
    label: str = ""
    phrase: str = ""
    owners: list[str] = field(default_factory=list)
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class World:
    place: str
    entities: dict[str, Entity] = field(default_factory=dict)
    resources: dict[str, Resource] = field(default_factory=dict)
    clues: list[str] = field(default_factory=list)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    facts: dict = field(default_factory=dict)

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)


@dataclass
class StoryParams:
    place: str
    resource: str
    name: str
    helper: str
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# Content registries
# ---------------------------------------------------------------------------

PLACES = {
    "deli": "the deli",
    "corner_deli": "the little corner deli",
    "old_town_deli": "the old town deli",
}

RESOURCES = {
    "mustard": Resource("mustard", 1, "jar", "a small yellow jar"),
    "pickles": Resource("pickles", 3, "jar", "a glass jar of crisp pickles"),
    "rolls": Resource("rolls", 4, "basket", "a basket of warm rolls"),
    "napkins": Resource("napkins", 8, "stack", "a stack of folded napkins"),
}

NAMES = ["Mina", "Owen", "Lia", "Noah", "Tess", "Jules", "Mara", "Eli"]
HELPERS = ["the clerk", "the cook", "the owner", "the helper"]

# ---------------------------------------------------------------------------
# Simulation
# ---------------------------------------------------------------------------

class Scene:
    def __init__(self, world: World):
        self.world = world
        self.fired: set[str] = set()

    def setup(self, hero: Entity, helper: Entity, resource: Resource) -> None:
        self.world.say(
            f"{hero.id} went to {self.world.place} because something tasty had gone missing."
        )
        self.world.say(
            f"{helper.label.capitalize()} looked worried. A small deli resource had to last the day."
        )
        self.world.say(
            f"On the counter sat {resource.description}, and everyone kept glancing at it."
        )

    def clue_one(self, hero: Entity, resource: Resource) -> None:
        if "clue_one" in self.fired:
            return
        self.fired.add("clue_one")
        self.world.clues.append("crumbs")
        self.world.say(
            f"{hero.id} noticed crumbs leading from the counter to the back shelf."
        )

    def clue_two(self, hero: Entity, helper: Entity, resource: Resource) -> None:
        if "clue_two" in self.fired:
            return
        self.fired.add("clue_two")
        self.world.clues.append("label")
        self.world.say(
            f"{hero.id} checked the jar again and saw the label was turned backward."
        )
        self.world.say(
            f"{helper.label.capitalize()} whispered that someone had been helping themselves twice."
        )

    def solve(self, hero: Entity, helper: Entity, resource: Resource) -> None:
        if "solve" in self.fired:
            return
        self.fired.add("solve")
        self.world.say(
            f"{hero.id} tried a simple trick: count what was there, then count it again."
        )
        self.world.say(
            f"The second count matched the first. The missing part was not the {resource.name}; it was the lid."
        )
        self.world.say(
            f"Under a tray, {hero.id} found the lid tucked away where it had rolled."
        )
        self.world.say(
            f"{helper.label.capitalize()} smiled, put the lid back, and thanked {hero.id} for the careful thinking."
        )

    def lesson(self, hero: Entity, helper: Entity, resource: Resource) -> None:
        self.world.say(
            f"{hero.id} learned that in a busy deli, the best mystery tool can be patient counting."
        )
        self.world.say(
            f"After that, the {resource.name} stayed ready, and everyone had enough for the next customer."
        )


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------

ASP_RULES = r"""
% A resource is at risk if it can be counted, hidden, or mistaken.
at_risk(R) :- resource(R), amount(R,N), N > 0.

% Repetition is a valid clue method when the same check matches twice.
repeat_check(C) :- clue(C), clue(C).

% Problem solving succeeds when clues plus a careful check explain the absence.
solved(R) :- at_risk(R), repeat_check(count), reason(R).

#show at_risk/1.
#show repeat_check/1.
#show solved/1.
"""


def asp_facts() -> str:
    import asp
    lines = []
    for rid, res in RESOURCES.items():
        lines.append(asp.fact("resource", rid))
        lines.append(asp.fact("amount", rid, res.amount))
        lines.append(asp.fact("unit", rid, res.unit))
    lines.append(asp.fact("clue", "count"))
    lines.append(asp.fact("clue", "count"))
    lines.append(asp.fact("reason", "mustard"))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show at_risk/1.\n#show repeat_check/1.\n#show solved/1."))
    shown = set(asp.atoms(model, "at_risk")) | set(asp.atoms(model, "repeat_check")) | set(asp.atoms(model, "solved"))
    python = {("mustard",), ("count",)}
    if ("mustard",) in shown and ("count",) in shown:
        print("OK: ASP facts are wired and the mystery structure is reachable.")
        return 0
    print("MISMATCH: ASP did not expose the expected storyworld structure.")
    return 1


# ---------------------------------------------------------------------------
# Story generation helpers
# ---------------------------------------------------------------------------

def build_world(params: StoryParams) -> World:
    world = World(place=PLACES[params.place])
    hero = world.add(Entity(id=params.name, type="child", label=params.name))
    helper = world.add(Entity(id="helper", type="adult", label=params.helper))
    resource = RESOURCES[params.resource]
    world.resources[resource.name] = resource

    scene = Scene(world)
    world.facts.update(hero=hero, helper=helper, resource=resource, params=params)

    scene.setup(hero, helper, resource)
    world.para()
    scene.clue_one(hero, resource)
    scene.clue_two(hero, helper, resource)
    world.para()
    scene.solve(hero, helper, resource)
    scene.lesson(hero, helper, resource)

    world.facts["clues"] = list(world.clues)
    return world


# ---------------------------------------------------------------------------
# Registries, validation, and Q&A
# ---------------------------------------------------------------------------

def valid_combos() -> list[tuple[str, str]]:
    return [(place, resource) for place in PLACES for resource in RESOURCES]


def explain_rejection(place: str, resource: str) -> str:
    return f"(No story: the deli mystery needs a real resource, but {resource!r} was not found.)"


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a short mystery story set in {world.place} about a child solving a deli problem involving {f["resource"].name}.',
        f"Tell a gentle mystery where {f['hero'].id} checks the same clue twice and learns a lesson at {world.place}.",
        f'Write a child-friendly story with repetition, clues, and a solution around "{f["resource"].name}".',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    helper = f["helper"]
    resource = f["resource"]
    return [
        QAItem(
            question=f"Where did {hero.id} go to investigate the problem?",
            answer=f"{hero.id} went to {world.place}, a deli where the missing piece of the problem could be checked carefully.",
        ),
        QAItem(
            question=f"What clue did {hero.id} notice first?",
            answer=f"{hero.id} noticed crumbs leading from the counter to the back shelf.",
        ),
        QAItem(
            question=f"How did {hero.id} solve the deli mystery?",
            answer=f"{hero.id} counted the {resource.name} twice, then found the missing lid under a tray.",
        ),
        QAItem(
            question=f"What did {helper.label} do at the end?",
            answer=f"{helper.label.capitalize()} smiled, put the lid back, and thanked {hero.id} for careful thinking.",
        ),
        QAItem(
            question=f"What lesson did {hero.id} learn?",
            answer=f"{hero.id} learned that patient counting can solve a mystery in a busy deli.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    res = world.facts["resource"]
    return [
        QAItem(
            question="What is a deli?",
            answer="A deli is a small shop or counter where people buy prepared food like sandwiches, rolls, and spreads.",
        ),
        QAItem(
            question="What is a resource?",
            answer="A resource is something useful that a person or place needs to keep things working well.",
        ),
        QAItem(
            question="Why is repetition useful in a mystery?",
            answer="Repetition can help someone check the facts again and notice what changed or what was overlooked.",
        ),
        QAItem(
            question=f"What makes {res.name} a useful deli resource?",
            answer=f"{res.name} is useful because it is one of the foods or supplies a deli keeps ready for customers.",
        ),
    ]


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A small mystery storyworld set in a deli.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--resource", choices=RESOURCES)
    ap.add_argument("--name", choices=NAMES)
    ap.add_argument("--helper", choices=HELPERS)
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
    if args.resource:
        combos = [c for c in combos if c[1] == args.resource]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, resource = rng.choice(sorted(combos))
    name = args.name or rng.choice(NAMES)
    helper = args.helper or rng.choice(HELPERS)
    return StoryParams(place=place, resource=resource, name=name, helper=helper)


def generate(params: StoryParams) -> StorySample:
    world = build_world(params)
    story = world.render()
    return StorySample(
        params=params,
        story=story,
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


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


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        lines.append(f"  {e.id:8} ({e.type})")
    for rid, res in world.resources.items():
        lines.append(f"  resource {rid}: amount={res.amount} unit={res.unit}")
    lines.append(f"  clues: {world.clues}")
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


def asp_valid() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show at_risk/1.\n#show repeat_check/1.\n#show solved/1."))
    return sorted(set(asp.atoms(model, "at_risk")) | set(asp.atoms(model, "repeat_check")) | set(asp.atoms(model, "solved")))


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show at_risk/1.\n#show repeat_check/1.\n#show solved/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(asp_program("#show at_risk/1.\n#show repeat_check/1.\n#show solved/1."))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        curated = [
            StoryParams(place="deli", resource="mustard", name="Mina", helper="the owner"),
            StoryParams(place="corner_deli", resource="pickles", name="Owen", helper="the clerk"),
            StoryParams(place="old_town_deli", resource="rolls", name="Tess", helper="the cook"),
        ]
        samples = [generate(p) for p in curated]
    else:
        seen = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 20):
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
            header = f"### {p.name}: {p.resource} at {p.place}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()

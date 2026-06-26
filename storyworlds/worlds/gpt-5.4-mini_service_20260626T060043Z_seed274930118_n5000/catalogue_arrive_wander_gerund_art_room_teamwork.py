#!/usr/bin/env python3
"""
A small story world set in an art room, with a catalogue, arrival, wandering,
teamwork, and a flashback-driven comedy turn.
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
class Person:
    name: str
    role: str
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def __post_init__(self) -> None:
        self.meters.setdefault("mess", 0.0)
        self.meters.setdefault("order", 0.0)
        self.meters.setdefault("paint", 0.0)
        self.memes.setdefault("curiosity", 0.0)
        self.memes.setdefault("embarrassment", 0.0)
        self.memes.setdefault("joy", 0.0)
        self.memes.setdefault("teamwork", 0.0)

    def pronoun(self) -> str:
        return "they"

    def possessive(self) -> str:
        return "their"


@dataclass
class Item:
    name: str
    kind: str
    meters: dict[str, float] = field(default_factory=dict)
    owner: Optional[str] = None
    placed: bool = False

    def __post_init__(self) -> None:
        self.meters.setdefault("clean", 1.0)
        self.meters.setdefault("mess", 0.0)


@dataclass
class StoryParams:
    name: str
    helper: str
    seed: Optional[int] = None


@dataclass
class World:
    room: str = "the art room"
    people: dict[str, Person] = field(default_factory=dict)
    items: dict[str, Item] = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    facts: dict = field(default_factory=dict)
    flashback_seen: bool = False
    teamwork_done: bool = False

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
NAMES = ["Milo", "Nina", "Ravi", "Tia", "Owen", "Pia", "Luna", "Ezra"]
HELPERS = ["teacher", "friend", "classmate", "assistant"]
ITEMS = [
    ("catalogue", "a bright catalogue of art supplies"),
    ("markers", "a box of markers"),
    ("brushes", "a jar of brushes"),
    ("glitter", "a cup of glitter"),
    ("paper", "a stack of paper"),
]


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
person(X) :- child(X).
person(X) :- helper(X).
mess(X, 1) :- item(X), kind(X, glitter).
order(X, 1) :- item(X), kind(X, catalogue).
at_risk(X) :- item(X), kind(X, glitter).
teamwork_needed :- child(C), helper(H), room(R), arrive(C, R), arrive(H, R).
resolved :- teamwork, flashback.
"""

def asp_facts() -> str:
    import asp
    lines: list[str] = []
    lines.append(asp.fact("room", "art_room"))
    for n in NAMES:
        lines.append(asp.fact("child", n))
    for h in HELPERS:
        lines.append(asp.fact("helper", h))
    for kind, _ in ITEMS:
        lines.append(asp.fact("item", kind))
        lines.append(asp.fact("kind", kind, kind))
    lines.append(asp.fact("arrive", "child", "art_room"))
    lines.append(asp.fact("arrive", "helper", "art_room"))
    lines.append(asp.fact("teamwork"))
    lines.append(asp.fact("flashback"))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show teamwork_needed/0. #show resolved/0."))
    syms = {(sym.name, len(sym.arguments)) for sym in model}
    ok = ("teamwork_needed", 0) in syms and ("resolved", 0) in syms
    if ok:
        print("OK: ASP twin reached teamwork and resolution.")
        return 0
    print("MISMATCH: ASP twin did not match expected facts.")
    return 1


# ---------------------------------------------------------------------------
# Story engine
# ---------------------------------------------------------------------------
def build_world(params: StoryParams) -> World:
    world = World()
    child = Person(name=params.name, role="child")
    helper = Person(name=params.helper, role="helper")
    world.people[child.name] = child
    world.people[helper.name] = helper

    for key, label in ITEMS:
        world.items[key] = Item(name=label, kind=key, owner=child.name if key == "catalogue" else None)

    return world


def arrive(world: World) -> None:
    child = next(p for p in world.people.values() if p.role == "child")
    helper = next(p for p in world.people.values() if p.role == "helper")
    world.say(
        f"One afternoon, {child.name} and {helper.name} arrived at {world.room}, "
        f"where the tables were already wearing tiny smudges like old freckles."
    )
    child.memes["curiosity"] += 1
    helper.memes["joy"] += 0.5
    world.facts["arrived"] = True


def catalogue_scene(world: World) -> None:
    child = next(p for p in world.people.values() if p.role == "child")
    catalogue = world.items["catalogue"]
    world.say(
        f"{child.name} opened the catalogue and read it like a treasure map: "
        f"pencils, paper, brushes, and one suspiciously dramatic glitter cup."
    )
    world.say(
        f"{child.name} wanted to wander from table to table, pointing at everything "
        f"with the seriousness of a tiny museum guide."
    )
    child.memes["curiosity"] += 1
    world.facts["catalogue_opened"] = True


def wander(world: World) -> None:
    child = next(p for p in world.people.values() if p.role == "child")
    helper = next(p for p in world.people.values() if p.role == "helper")
    child.meters["mess"] += 1
    child.meters["order"] -= 0.5
    world.say(
        f"{child.name} started wander-ging around the room, stepping in a circle, "
        f"then another circle, then a loop that was definitely not in the lesson plan."
    )
    world.say(
        f"A trail of paper scraps followed {child.name} like a parade, and the glitter cup "
        f"looked ready to join the march."
    )
    helper.memes["embarrassment"] += 0.5
    world.facts["wandered"] = True


def flashback(world: World) -> None:
    child = next(p for p in world.people.values() if p.role == "child")
    helper = next(p for p in world.people.values() if p.role == "helper")
    world.flashback_seen = True
    world.say(
        f"Then {helper.name} had a flashback to the last art day, when a single puff of glitter "
        f"had followed everyone home and sparkled in the soup pot."
    )
    world.say(
        f"{helper.name} remembered that nobody could find the lid, and the class had spent ten "
        f"whole minutes chasing a rolling paint cap like it was a runaway marble."
    )
    helper.memes["curiosity"] += 0.5
    world.facts["flashback"] = True


def teamwork(world: World) -> None:
    child = next(p for p in world.people.values() if p.role == "child")
    helper = next(p for p in world.people.values() if p.role == "helper")
    world.teamwork_done = True
    child.memes["teamwork"] += 1
    helper.memes["teamwork"] += 1
    helper.meters["order"] += 1
    child.meters["mess"] -= 0.5
    world.say(
        f"So {helper.name} turned the catalogue around and said, "
        f"'{child.name}, let's sort the supplies together before the glitter becomes a legend.'"
    )
    world.say(
        f"{child.name} nodded, lined up the brushes, stacked the paper, and held the glitter cup "
        f"with both hands like a priceless jellyfish."
    )
    world.say(
        f"Working side by side made the room calmer, and the wandering turned into useful helping."
    )
    world.facts["teamwork"] = True


def ending(world: World) -> None:
    child = next(p for p in world.people.values() if p.role == "child")
    helper = next(p for p in world.people.values() if p.role == "helper")
    world.say(
        f"By the end, the catalogue was open on the right page, the glitter was capped, "
        f"and {child.name}'s feet were back where they belonged."
    )
    world.say(
        f"{child.name} grinned at the tidy table, and {helper.name} laughed because the art room "
        f"had gone from a wandering storm to a neat little team."
    )


def tell_story(params: StoryParams) -> World:
    world = build_world(params)
    arrive(world)
    world.para()
    catalogue_scene(world)
    wander(world)
    world.para()
    flashback(world)
    teamwork(world)
    ending(world)
    return world


# ---------------------------------------------------------------------------
# QA
# ---------------------------------------------------------------------------
def prompts(world: World) -> list[str]:
    child = next(p for p in world.people.values() if p.role == "child")
    helper = next(p for p in world.people.values() if p.role == "helper")
    return [
        f"Write a funny story set in an art room where {child.name} arrives, opens a catalogue, "
        f"and starts wander-ging around until teamwork helps.",
        f"Tell a comedy story about {child.name} and {helper.name} in the art room, using a catalogue "
        f"and a flashback to solve a messy problem.",
        "Write a short child-friendly story about arriving at an art room, wandering, and learning to work as a team.",
    ]


def story_qa(world: World) -> list[QAItem]:
    child = next(p for p in world.people.values() if p.role == "child")
    helper = next(p for p in world.people.values() if p.role == "helper")
    return [
        QAItem(
            question=f"Where did {child.name} and {helper.name} arrive?",
            answer=f"They arrived at the art room, where the tables were ready for drawing, sorting, and a little bit of chaos.",
        ),
        QAItem(
            question=f"What did {child.name} open before start wandering around?",
            answer=f"{child.name} opened the catalogue, which showed the art supplies and helped the day begin.",
        ),
        QAItem(
            question=f"What made the helper remember the last art day?",
            answer=f"The helper had a flashback after seeing how much glitter and paper could turn a simple moment into a mess.",
        ),
        QAItem(
            question=f"How did the story turn out at the end?",
            answer=f"The child and helper worked together, so the supplies got sorted and the art room ended up tidy and cheerful.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a catalogue?",
            answer="A catalogue is a list or book that shows what things are available, like supplies to choose from.",
        ),
        QAItem(
            question="What is teamwork?",
            answer="Teamwork means people help each other and do a job together instead of doing it alone.",
        ),
        QAItem(
            question="What is a flashback in a story?",
            answer="A flashback is when the story briefly remembers something that happened earlier.",
        ),
    ]


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Art room comedy story world with catalogue, arrival, wandering, teamwork, and flashback.")
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
    name = args.name or rng.choice(NAMES)
    helper = args.helper or rng.choice(HELPERS)
    if name == helper:
        raise StoryError("The child and helper should be different characters.")
    return StoryParams(name=name, helper=helper)


def generate(params: StoryParams) -> StorySample:
    world = tell_story(params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for p in world.people.values():
        lines.append(f"{p.name} ({p.role}): meters={dict(p.meters)} memes={dict(p.memes)}")
    for item in world.items.values():
        lines.append(f"{item.name}: meters={dict(item.meters)} owner={item.owner}")
    lines.append(f"flashback_seen={world.flashback_seen} teamwork_done={world.teamwork_done}")
    return "\n".join(lines)


def format_qa(sample: StorySample) -> str:
    out = ["== (1) Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        out.append(f"{i}. {p}")
    out.append("")
    out.append("== (2) Story questions ==")
    for q in sample.story_qa:
        out.append(f"Q: {q.question}")
        out.append(f"A: {q.answer}")
    out.append("")
    out.append("== (3) World-knowledge questions ==")
    for q in sample.world_qa:
        out.append(f"Q: {q.question}")
        out.append(f"A: {q.answer}")
    return "\n".join(out)


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
        print(asp_program("#show teamwork_needed/0. #show resolved/0."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        model = asp.one_model(asp_program("#show teamwork_needed/0. #show resolved/0."))
        print([str(s) for s in model])
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        for i, n in enumerate(NAMES[: min(5, len(NAMES))]):
            params = StoryParams(name=n, helper=HELPERS[i % len(HELPERS)], seed=base_seed + i)
            samples.append(generate(params))
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 20):
            rng = random.Random(base_seed + i)
            i += 1
            try:
                params = resolve_params(args, rng)
            except StoryError as err:
                print(err)
                return
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
        header = f"### variant {idx + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if idx < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()

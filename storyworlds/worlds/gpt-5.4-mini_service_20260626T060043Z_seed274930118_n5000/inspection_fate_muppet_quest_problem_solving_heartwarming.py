#!/usr/bin/env python3
"""
A small heartwarming story world about a muppet on a quest, an important
inspection, and a problem solved by careful kindness.

The seed words are woven into the domain:
- inspection
- fate
- muppet
- Quest
- Problem Solving
- Heartwarming
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

DEFAULT_SEED = 274930118


@dataclass
class Character:
    id: str
    role: str
    label: str
    kind: str = "character"
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)


@dataclass
class Thing:
    id: str
    label: str
    kind: str = "thing"
    owner: Optional[str] = None
    inspected: bool = False
    repaired: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)


@dataclass
class StoryParams:
    place: str
    quest: str
    problem: str
    item: str
    helper: str
    name: str
    seed: Optional[int] = None


PLACES = {
    "workshop": "a cozy workshop",
    "garden": "a quiet garden",
    "attic": "a dusty attic",
    "lantern_room": "a lantern-lit room",
}

QUESTS = {
    "inspection": "an inspection quest",
    "rescue": "a rescue quest",
    "repair": "a repair quest",
}

PROBLEMS = {
    "stuck": "a small latch was stuck",
    "torn": "a tiny sail had torn",
    "dim": "the lamp was glowing dimly",
}

ITEMS = {
    "muppet": "a little muppet puppet",
    "clock": "a wooden clock",
    "kite": "a red kite",
    "lantern": "a brass lantern",
}

HELPERS = {
    "friend": "a patient friend",
    "grandma": "a warm grandma",
    "neighbor": "a kind neighbor",
}


class World:
    def __init__(self, params: StoryParams) -> None:
        self.params = params
        self.characters: dict[str, Character] = {}
        self.things: dict[str, Thing] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict[str, object] = {}

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)

    def add_character(self, c: Character) -> Character:
        self.characters[c.id] = c
        return c

    def add_thing(self, t: Thing) -> Thing:
        self.things[t.id] = t
        return t


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Heartwarming quest about inspection and problem solving.")
    ap.add_argument("--place", choices=sorted(PLACES))
    ap.add_argument("--quest", choices=sorted(QUESTS))
    ap.add_argument("--problem", choices=sorted(PROBLEMS))
    ap.add_argument("--item", choices=sorted(ITEMS))
    ap.add_argument("--helper", choices=sorted(HELPERS))
    ap.add_argument("--name")
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


def _choice(rng: random.Random, mapping: dict[str, str], key: Optional[str]) -> str:
    return key if key is not None else rng.choice(list(mapping))


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    place = _choice(rng, PLACES, args.place)
    quest = _choice(rng, QUESTS, args.quest)
    problem = _choice(rng, PROBLEMS, args.problem)
    item = _choice(rng, ITEMS, args.item)
    helper = _choice(rng, HELPERS, args.helper)
    name = args.name or rng.choice(["Milo", "Nina", "Toby", "Sage", "Lena"])
    if quest == "inspection" and item == "muppet":
        return StoryParams(place=place, quest=quest, problem=problem, item=item, helper=helper, name=name)
    if args.quest == "inspection" or args.item == "muppet":
        return StoryParams(place=place, quest=quest, problem=problem, item=item, helper=helper, name=name)
    return StoryParams(place=place, quest=quest, problem=problem, item=item, helper=helper, name=name)


def inspect_item(world: World, hero: Character, thing: Thing) -> None:
    thing.inspected = True
    hero.meters["care"] = hero.meters.get("care", 0) + 1
    world.say(f"{hero.label} began the inspection quest and looked closely at {thing.label}.")


def notice_problem(world: World, thing: Thing, problem: str) -> None:
    thing.memes["trouble"] = thing.memes.get("trouble", 0) + 1
    world.say(f"Then they noticed that {problem}, which made the quest feel important.")


def problem_solve(world: World, hero: Character, helper: Character, thing: Thing, problem: str) -> None:
    thing.repaired = True
    hero.memes["hope"] = hero.memes.get("hope", 0) + 1
    helper.memes["kindness"] = helper.memes.get("kindness", 0) + 1
    world.say(
        f"{helper.label} helped with gentle problem solving, and together they fixed the trouble."
    )
    world.say(
        f"In the end, {thing.label} was safe again, and {hero.label} smiled because the fate of the little project had turned bright."
    )


def tell(params: StoryParams) -> World:
    world = World(params)
    hero = world.add_character(Character(id=params.name, role="hero", label=f"{params.name} the muppet"))
    helper = world.add_character(Character(id="helper", role=params.helper, label=HELPERS[params.helper]))
    thing = world.add_thing(Thing(id="item", label=ITEMS[params.item], owner=hero.id))

    world.say(
        f"Once, in {PLACES[params.place]}, there was {hero.label} who loved a good Quest."
    )
    world.say(
        f"{hero.label} wanted an inspection, because something about the day felt like fate was asking for care."
    )
    world.para()
    inspect_item(world, hero, thing)
    notice_problem(world, thing, PROBLEMS[params.problem])
    world.say(
        f"{helper.label} arrived at just the right moment, and no one felt alone."
    )
    world.para()
    problem_solve(world, hero, helper, thing, PROBLEMS[params.problem])
    world.say(
        f"It was a heartwarming ending: the muppet, the helper, and the little thing all rested safely together."
    )

    world.facts.update(
        hero=hero,
        helper=helper,
        thing=thing,
        place=params.place,
        quest=params.quest,
        problem=params.problem,
        item=params.item,
    )
    return world


ASP_RULES = r"""
quest(inspection).
feature(problem_solving).
style(heartwarming).

needs_inspection(muppet_item).
has_problem(muppet_item).
helped(muppet_item) :- needs_inspection(muppet_item), has_problem(muppet_item).
happy_end(muppet_item) :- helped(muppet_item).
#show happy_end/1.
"""

def asp_facts() -> str:
    import asp
    return "\n".join([
        asp.fact("quest", "inspection"),
        asp.fact("feature", "problem_solving"),
        asp.fact("style", "heartwarming"),
        asp.fact("needs_inspection", "muppet_item"),
        asp.fact("has_problem", "muppet_item"),
    ])


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show happy_end/1."))
    ok = ("happy_end", ("muppet_item",)) in set((a.name, tuple(str(x) for x in a.arguments)) for a in model)
    if ok:
        print("OK: ASP twin produces the expected happy ending.")
        return 0
    print("Mismatch in ASP twin.")
    return 1


def generation_prompts(world: World) -> list[str]:
    return [
        f"Write a heartwarming story about a muppet on an inspection quest in {PLACES[world.params.place]}.",
        f"Tell a story where {world.params.name} meets a problem and uses problem solving with a helper.",
        "Write a gentle quest story that ends with fate turning kind.",
    ]


def story_qa(world: World) -> list[QAItem]:
    p = world.params
    return [
        QAItem(
            question=f"Who went on the inspection quest?",
            answer=f"{p.name} the muppet went on the inspection quest."
        ),
        QAItem(
            question=f"What problem did they notice?",
            answer=f"They noticed that {PROBLEMS[p.problem]}."
        ),
        QAItem(
            question=f"Who helped solve the problem?",
            answer=f"{HELPERS[p.helper]} helped with the problem solving."
        ),
        QAItem(
            question=f"How did the story end?",
            answer=f"It ended heartwarmingly, with the item fixed and everyone safe together."
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a quest?",
            answer="A quest is a journey or task someone does to reach a goal."
        ),
        QAItem(
            question="What does inspection mean?",
            answer="Inspection means looking closely at something to check how it is doing."
        ),
        QAItem(
            question="What is problem solving?",
            answer="Problem solving means figuring out how to fix a trouble or reach a good answer."
        ),
        QAItem(
            question="What does heartwarming mean?",
            answer="Heartwarming means it makes people feel warm, happy, and cared for."
        ),
    ]


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for c in world.characters.values():
        lines.append(f"{c.id}: kind={c.kind} role={c.role} meters={c.meters} memes={c.memes}")
    for t in world.things.values():
        lines.append(f"{t.id}: kind={t.kind} label={t.label} inspected={t.inspected} repaired={t.repaired}")
    return "\n".join(lines)


def format_qa(sample: StorySample) -> str:
    parts = ["== story questions =="]
    for q in sample.story_qa:
        parts.append(f"Q: {q.question}")
        parts.append(f"A: {q.answer}")
    parts.append("")
    parts.append("== world knowledge ==")
    for q in sample.world_qa:
        parts.append(f"Q: {q.question}")
        parts.append(f"A: {q.answer}")
    return "\n".join(parts)


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
    StoryParams(place="workshop", quest="inspection", problem="stuck", item="muppet", helper="friend", name="Milo"),
    StoryParams(place="lantern_room", quest="inspection", problem="dim", item="lantern", helper="grandma", name="Nina"),
    StoryParams(place="garden", quest="repair", problem="torn", item="kite", helper="neighbor", name="Toby"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show happy_end/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print("ASP twin is available; this world keeps the declarative rules minimal.")
        return

    base_seed = args.seed if args.seed is not None else DEFAULT_SEED
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
            i += 1
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

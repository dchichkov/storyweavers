#!/usr/bin/env python3
"""
A small northern slice-of-life storyworld about a friendly conflict that gets
resolved through sharing, listening, and a simple compromise.
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


@dataclass
class Item:
    id: str
    label: str
    phrase: str
    owner: Optional[str] = None
    carried_by: Optional[str] = None
    meters: dict[str, float] = field(default_factory=lambda: {"used": 0.0})
    memes: dict[str, float] = field(default_factory=lambda: {"value": 0.0})


@dataclass
class Person:
    id: str
    name: str
    role: str
    traits: list[str] = field(default_factory=list)
    meters: dict[str, float] = field(default_factory=lambda: {"walked": 0.0})
    memes: dict[str, float] = field(default_factory=lambda: {
        "joy": 0.0,
        "conflict": 0.0,
        "friendship": 0.0,
        "care": 0.0,
    })


@dataclass
class Place:
    label: str
    detail: str
    affords: set[str] = field(default_factory=set)


@dataclass
class StoryParams:
    place: str
    activity: str
    shared_item: str
    name_a: str
    name_b: str
    seed: Optional[int] = None


class World:
    def __init__(self, place: Place) -> None:
        self.place = place
        self.people: dict[str, Person] = {}
        self.items: dict[str, Item] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict[str, object] = {}
        self.fired: set[str] = set()

    def add_person(self, p: Person) -> Person:
        self.people[p.id] = p
        return p

    def add_item(self, i: Item) -> Item:
        self.items[i.id] = i
        return i

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
        w = World(self.place)
        w.people = copy.deepcopy(self.people)
        w.items = copy.deepcopy(self.items)
        w.fired = set(self.fired)
        w.facts = dict(self.facts)
        w.paragraphs = [[]]
        return w


PLACES = {
    "northern_path": Place(
        label="the northern path",
        detail="The snow was packed down into a quiet path between pine trees.",
        affords={"walk", "sled", "look"},
    ),
    "lakeside_bench": Place(
        label="the lakeside bench",
        detail="The lake was still, and the bench faced the pale water and the wind.",
        affords={"sit", "share", "look"},
    ),
    "community_room": Place(
        label="the community room",
        detail="The room was warm, with hooks for coats and a big table for snacks.",
        affords={"share", "talk", "craft"},
    ),
}

ACTIVITIES = {
    "sled": {
        "verb": "take turns on the sled",
        "gerund": "taking turns on the sled",
        "rush": "grab the sled and go first",
        "turn": "take turns",
        "consequence": "there would be no fair turn for the other friend",
    },
    "snack": {
        "verb": "share the snack box",
        "gerund": "sharing the snack box",
        "rush": "reach for the last bun",
        "turn": "split the snack box evenly",
        "consequence": "one friend would feel left out",
    },
    "game": {
        "verb": "play the board game",
        "gerund": "playing the board game",
        "rush": "move the best piece without asking",
        "turn": "pause and ask first",
        "consequence": "the game would stop feeling fun",
    },
}

ITEMS = {
    "sled": Item(id="sled", label="sled", phrase="a bright red sled"),
    "snack_box": Item(id="snack_box", label="snack box", phrase="a little tin snack box"),
    "board_game": Item(id="board_game", label="board game", phrase="a worn board game with wooden pieces"),
}

NAMES = ["Mila", "Niko", "Tess", "Jasper", "Soren", "Elin", "Iris", "Rune"]
TRAITS = ["patient", "curious", "gentle", "cheerful", "lively", "quiet"]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Northern slice-of-life storyworld about friendship, conflict, and a small compromise."
    )
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--activity", choices=ACTIVITIES)
    ap.add_argument("--shared-item", choices=ITEMS)
    ap.add_argument("--name-a")
    ap.add_argument("--name-b")
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
    return [(p, a, i) for p in PLACES for a in ACTIVITIES for i in ITEMS if p != "community_room" or a != "sled"]


def asp_facts() -> str:
    import asp
    lines = []
    for p in PLACES:
        lines.append(asp.fact("place", p))
        for a in sorted(PLACES[p].affords):
            lines.append(asp.fact("affords", p, a))
    for a in ACTIVITIES:
        lines.append(asp.fact("activity", a))
    for i in ITEMS:
        lines.append(asp.fact("item", i))
    return "\n".join(lines)


ASP_RULES = r"""
valid(P,A,I) :- place(P), activity(A), item(I), affords(P,A).
northern(P) :- place(P).
friendship_story(P,A,I) :- valid(P,A,I), northern(P).
"""


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    if py - cl:
        print("  only in python:", sorted(py - cl))
    if cl - py:
        print("  only in clingo:", sorted(cl - py))
    return 1


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    combos = [c for c in valid_combos()
              if (args.place is None or c[0] == args.place)
              and (args.activity is None or c[1] == args.activity)
              and (args.shared_item is None or c[2] == args.shared_item)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, activity, shared_item = rng.choice(sorted(combos))
    name_a = args.name_a or rng.choice(NAMES)
    name_b = args.name_b or rng.choice([n for n in NAMES if n != name_a])
    return StoryParams(place=place, activity=activity, shared_item=shared_item, name_a=name_a, name_b=name_b)


def _setup_world(params: StoryParams) -> World:
    world = World(PLACES[params.place])
    a = world.add_person(Person(id="A", name=params.name_a, role="friend", traits=["little", rng_trait(params.seed)]))
    b = world.add_person(Person(id="B", name=params.name_b, role="friend", traits=["little", rng_trait((params.seed or 0) + 1)]))
    item = world.add_item(Item(
        id=params.shared_item,
        label=ITEMS[params.shared_item].label,
        phrase=ITEMS[params.shared_item].phrase,
    ))
    item.owner = "A"
    item.carried_by = "A"
    world.facts.update(hero_a=a, hero_b=b, item=item, params=params)
    return world


def rng_trait(seed: Optional[int]) -> str:
    r = random.Random(seed)
    return r.choice(TRAITS)


def _predict_conflict(world: World, params: StoryParams) -> bool:
    activity = ACTIVITIES[params.activity]
    item = world.items[params.shared_item]
    if params.activity == "sled" and params.place == "community_room":
        return False
    if params.shared_item == "board_game" and params.place == "northern_path":
        return False
    return True


def generate(params: StoryParams) -> StorySample:
    world = _setup_world(params)
    a = world.people["A"]
    b = world.people["B"]
    item = world.items[params.shared_item]
    act = ACTIVITIES[params.activity]
    place = world.place

    a.memes["friendship"] += 1
    b.memes["friendship"] += 1
    world.say(f"{a.name} and {b.name} were friends on a northern day at {place.label}.")
    world.say(place.detail)
    world.say(f"They had {item.phrase}, and both of them wanted to {act["verb"]}.")

    world.para()
    world.say(f"{a.name} reached first, and {b.name} frowned because {a.name} was about to {act["rush"]}.")
    a.memes["conflict"] += 1
    b.memes["conflict"] += 1
    world.say(f"That would mean {act["consequence"]}.")

    world.para()
    world.say(f"{b.name} took a breath and said, \"Let's {act["turn"]} so it stays fair.\"")
    a.memes["care"] += 1
    b.memes["care"] += 1
    a.memes["conflict"] = 0.0
    b.memes["conflict"] = 0.0
    a.memes["friendship"] += 1
    b.memes["friendship"] += 1

    if params.activity == "sled":
        world.say(f"They agreed to push the sled for each other, then {item.label} slid down the snow in neat turns.")
    elif params.activity == "snack":
        world.say(f"They split the snack box evenly, and each friend got a bun and a smile.")
    else:
        world.say(f"They paused before each move, and the board game stayed calm and fun.")

    world.para()
    world.say(f"By the end, {a.name} and {b.name} were laughing again, and the northern air felt kinder because they had shared the moment.")

    world.facts.update(conflict=True, resolved=True, activity=act, item=item, place=place)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


def generation_prompts(world: World) -> list[str]:
    p = world.facts["params"]
    act = ACTIVITIES[p.activity]
    return [
        f'Write a short northern slice-of-life story about two friends who want to {act["verb"]} and learn to share.',
        f"Tell a gentle story where {p.name_a} and {p.name_b} have a small conflict, then fix it with friendship.",
        f'Write a child-friendly story with the word "northern" and a calm ending image after a shared activity.',
    ]


def story_qa(world: World) -> list[QAItem]:
    p = world.facts["params"]
    act = ACTIVITIES[p.activity]
    a = world.facts["hero_a"]
    b = world.facts["hero_b"]
    return [
        QAItem(
            question=f"Who are the two friends in the story?",
            answer=f"The story is about {a.name} and {b.name}, two friends spending time together in the north.",
        ),
        QAItem(
            question=f"What did the friends want to do with the {ITEMS[p.shared_item].label}?",
            answer=f"They both wanted to {act['verb']}.",
        ),
        QAItem(
            question=f"Why did a conflict happen?",
            answer=f"A conflict happened because {a.name} reached first and almost {act['rush']}, which would have felt unfair to {b.name}.",
        ),
        QAItem(
            question=f"How did they solve the problem?",
            answer=f"They solved it by agreeing to {act['turn']}, so both friends could enjoy the activity fairly.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does northern mean?",
            answer="Northern means in or near the north, where days can feel cold, bright, and quiet.",
        ),
        QAItem(
            question="What is friendship?",
            answer="Friendship is the caring bond people share when they like, help, and listen to each other.",
        ),
        QAItem(
            question="What is a conflict?",
            answer="A conflict is a small disagreement or problem that happens when people want different things.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== Story questions ==")
    for q in sample.story_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    lines.append("")
    lines.append("== World questions ==")
    for q in sample.world_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for p in world.people.values():
        lines.append(f"{p.id}: name={p.name} memes={dict(p.memes)}")
    for i in world.items.values():
        lines.append(f"{i.id}: {i.phrase} owner={i.owner} carried_by={i.carried_by}")
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
    StoryParams(place="northern_path", activity="sled", shared_item="sled", name_a="Mila", name_b="Soren"),
    StoryParams(place="lakeside_bench", activity="snack", shared_item="snack_box", name_a="Elin", name_b="Niko"),
    StoryParams(place="community_room", activity="game", shared_item="board_game", name_a="Tess", name_b="Rune"),
]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(question="What does northern mean?", answer="Northern means in or near the north, where days can feel cold, bright, and quiet."),
        QAItem(question="What is friendship?", answer="Friendship is the caring bond people share when they like, help, and listen to each other."),
        QAItem(question="What is a conflict?", answer="A conflict is a small disagreement or problem that happens when people want different things."),
    ]


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
            print(" ", c)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(p) for p in CURATED]
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
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.name_a} and {p.name_b} at {p.place} ({p.activity})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""
storyworlds/worlds/fetch_twist_humor_curiosity_slice_of_life.py
===============================================================

A small Slice-of-Life storyworld about a child fetching something, with a light
twist, a little humor, and a curious turn.

Premise:
- A child is asked to fetch a needed item from a nearby place.
- The child goes looking, notices ordinary details, and gets a small surprise.
- The surprise changes the plan in a gentle way.
- The story ends with the item returned and the new understanding settled in.

The world keeps track of:
- physical meters: distance, carriedness, neatness, time spent, etc.
- emotional memes: curiosity, surprise, relief, humor, worry, gratitude.
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

THRESHOLD = 1.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    carried_by: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman"}
        male = {"boy", "father", "dad", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Place:
    id: str
    label: str
    near: str
    far: bool = False
    can_hide: bool = False
    afford_fetch: bool = True
    surprise_tags: set[str] = field(default_factory=set)


@dataclass
class FetchTask:
    id: str
    verb: str
    noun: str
    where: str
    route: str
    twist: str
    reveal: str
    tags: set[str] = field(default_factory=set)


class World:
    def __init__(self, place: Place) -> None:
        self.place = place
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}

    def add(self, e: Entity) -> Entity:
        self.entities[e.id] = e
        return e

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


@dataclass
class StoryParams:
    place: str
    task: str
    item: str
    name: str
    gender: str
    parent: str
    seed: Optional[int] = None


PLACES = {
    "kitchen": Place(id="kitchen", label="the kitchen", near="the hallway", surprise_tags={"crumbs", "snack"}),
    "porch": Place(id="porch", label="the porch", near="the front door", surprise_tags={"rain", "boots"}),
    "laundry": Place(id="laundry", label="the laundry room", near="the hall", surprise_tags={"socks", "basket"}),
    "garden": Place(id="garden", label="the garden", near="the back steps", can_hide=True, surprise_tags={"cat", "flower"}),
    "study": Place(id="study", label="the study", near="the bookshelf", surprise_tags={"paper", "glasses"}),
}

TASKS = {
    "cup": FetchTask(
        id="cup",
        verb="fetch the cup",
        noun="cup",
        where="the kitchen shelf",
        route="walk to the kitchen shelf",
        twist="the cup was smaller than it looked from across the room",
        reveal="it was a tiny teacup with a painted rabbit on it",
        tags={"cup", "small", "rabbit"},
    ),
    "slipper": FetchTask(
        id="slipper",
        verb="fetch the slipper",
        noun="slipper",
        where="under the couch",
        route="peek under the couch",
        twist="the slipper was already found, and the other one was doing something odd",
        reveal="the missing slipper was being used as a boat by a toy duck",
        tags={"slipper", "toy", "duck"},
    ),
    "sock": FetchTask(
        id="sock",
        verb="fetch the sock",
        noun="sock",
        where="the laundry basket",
        route="search the laundry basket",
        twist="the sock was wrapped around a spoon like a sleepy scarf",
        reveal="someone had used the sock to carry a warm bread roll",
        tags={"sock", "laundry", "bread"},
    ),
    "key": FetchTask(
        id="key",
        verb="fetch the key",
        noun="key",
        where="the hook by the door",
        route="look on the hook by the door",
        twist="the key was hanging from a ribbon tied in a neat bow",
        reveal="the ribbon had been added so nobody would forget it before leaving",
        tags={"key", "door", "ribbon"},
    ),
    "book": FetchTask(
        id="book",
        verb="fetch the book",
        noun="book",
        where="the study desk",
        route="check the study desk",
        twist="the book had a paper bookmark sticking out like a tongue",
        reveal="the bookmark was a grocery list with a doodled smiley face",
        tags={"book", "paper", "list"},
    ),
}

GIRL_NAMES = ["Mia", "Lily", "Nora", "Ava", "Zoe", "Ella", "Maya"]
BOY_NAMES = ["Leo", "Ben", "Finn", "Sam", "Noah", "Eli", "Theo"]
TRAITS = ["curious", "cheerful", "quiet", "careful", "sprightly", "thoughtful"]
PARENTS = ["mother", "father"]


def valid_combos() -> list[tuple[str, str, str]]:
    out = []
    for pid, place in PLACES.items():
        for tid, task in TASKS.items():
            if place.afford_fetch:
                out.append((pid, tid, task.noun))
    return out


def reasonableness_gate(place: Place, task: FetchTask) -> bool:
    return place.afford_fetch and bool(task.noun)


def asp_facts() -> str:
    import asp
    lines = []
    for pid, place in PLACES.items():
        lines.append(asp.fact("place", pid))
        if place.can_hide:
            lines.append(asp.fact("can_hide", pid))
        for tag in sorted(place.surprise_tags):
            lines.append(asp.fact("tagged", pid, tag))
    for tid, task in TASKS.items():
        lines.append(asp.fact("task", tid))
        lines.append(asp.fact("fetches", tid, task.noun))
        for tag in sorted(task.tags):
            lines.append(asp.fact("task_tag", tid, tag))
    return "\n".join(lines)


ASP_RULES = r"""
valid(P, T) :- place(P), task(T), fetchable(P, T).
fetchable(P, T) :- place(P), task(T).
twist(P, T) :- valid(P, T), tagged(P, X), task_tag(T, X).
"""


def asp_program(show: str) -> str:
    return f"{asp_facts()}\nfetchable(P,T) :- place(P), task(T).\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/2."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    py = {(p, t) for p, t, _ in valid_combos()}
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    if cl - py:
        print("  only in clingo:", sorted(cl - py))
    if py - cl:
        print("  only in python:", sorted(py - cl))
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A gentle fetch storyworld with a small twist.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--task", choices=TASKS)
    ap.add_argument("--item", choices=[t.noun for t in TASKS.values()])
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--parent", choices=PARENTS)
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


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    combos = valid_combos()
    if args.task and args.item:
        task = TASKS[args.task]
        if task.noun != args.item:
            raise StoryError("No story: that item does not match the chosen fetch task.")
    if args.place and args.task and not reasonableness_gate(PLACES[args.place], TASKS[args.task]):
        raise StoryError("No story: that place and fetch task do not make a sensible story.")
    filtered = [c for c in combos
                if (args.place is None or c[0] == args.place)
                and (args.task is None or c[1] == args.task)
                and (args.item is None or c[2] == args.item)]
    if not filtered:
        raise StoryError("No valid combination matches the given options.")
    place, task, item = rng.choice(sorted(filtered))
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    parent = args.parent or rng.choice(PARENTS)
    return StoryParams(place=place, task=task, item=item, name=name, gender=gender, parent=parent)


def build_world(params: StoryParams) -> World:
    place = PLACES[params.place]
    task = TASKS[params.task]
    world = World(place)
    hero = world.add(Entity(id=params.name, kind="character", type=params.gender))
    parent = world.add(Entity(id="parent", kind="character", type=params.parent, label=f"the {params.parent}"))
    item = world.add(Entity(id="item", type=task.noun, label=task.noun, phrase=f"the {task.noun}", owner=hero.id))
    hero.memes = {"curiosity": 0.0, "humor": 0.0, "surprise": 0.0, "relief": 0.0, "gratitude": 0.0}
    parent.memes = {"anticipation": 0.0}
    item.meters = {"carried": 0.0, "found": 0.0, "distance": 0.0}
    world.facts.update(hero=hero, parent=parent, item=item, task=task, place=place)
    return world


def tell(world: World) -> None:
    f = world.facts
    hero, parent, task, place, item = f["hero"], f["parent"], f["task"], f["place"], f["item"]
    trait = rng_trait(hero)
    hero.memes["curiosity"] += 1
    world.say(f"{hero.id} was a {trait} little {hero.type} who liked to notice the small things in {place.label}.")
    world.say(f"One day, {parent.label} asked {hero.id} to {task.verb} from {task.where}.")
    world.para()
    world.say(f"{hero.id} went {task.route}, looking carefully along the way.")
    world.say(f"{hero.id} wondered why the day felt so ordinary and so interesting at the same time.")
    world.say(f"Then came the twist: {task.twist}.")
    hero.memes["surprise"] += 1
    hero.memes["humor"] += 1
    world.para()
    world.say(f"{hero.id} blinked, then laughed a little. It was the kind of funny surprise that makes a child grin at a silly little mystery.")
    world.say(f"At last, {hero.id} found {item.phrase}; {task.reveal}.")
    item.meters["found"] = 1
    item.meters["carried"] = 1
    hero.memes["relief"] += 1
    hero.memes["gratitude"] += 1
    world.para()
    world.say(f"{hero.id} carried {item.phrase} back to {parent.label}, feeling proud that the errand was done.")
    world.say(f"{parent.label} smiled, thanked {hero.id}, and shook their head at the little joke hidden in an everyday chore.")
    world.say(f"By the end, {hero.id} had done the fetch, learned a small surprise, and turned an ordinary walk into a cheerful story.")


def rng_trait(hero: Entity) -> str:
    # deterministic-ish flavor from name length, without extra params
    return TRAITS[len(hero.id) % len(TRAITS)]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero, parent, task, place = f["hero"], f["parent"], f["task"], f["place"]
    return [
        f'Write a short slice-of-life story for a young child about {hero.id} who has to fetch a {task.noun} from {place.label}.',
        f"Tell a gentle story where {hero.id} does a fetch errand for {parent.label} and finds a funny little twist along the way.",
        f'Write a simple story that includes the word "fetch" and ends with an ordinary errand becoming a pleasant surprise.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero, parent, task, place = f["hero"], f["parent"], f["task"], f["place"]
    return [
        QAItem(
            question=f"What did {parent.label} ask {hero.id} to do?",
            answer=f"{parent.label.capitalize()} asked {hero.id} to fetch the {task.noun} from {task.where}.",
        ),
        QAItem(
            question=f"What was the funny surprise in the story?",
            answer=f"The surprise was that {task.twist}.",
        ),
        QAItem(
            question=f"How did {hero.id} feel after finding the {task.noun}?",
            answer=f"{hero.id} felt curious, amused, and relieved after finding the {task.noun} and bringing it back.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(question="What does fetch mean?", answer="To fetch something means to go get it and bring it back."),
        QAItem(question="Why can small surprises feel funny?", answer="Small surprises can feel funny because they break an ordinary routine in a harmless way."),
        QAItem(question="What is an errand?", answer="An errand is a small task you do for someone, like bringing back an item."),
    ]


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
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    return "\n".join(lines)


CURATED = [
    StoryParams(place="kitchen", task="cup", item="cup", name="Mia", gender="girl", parent="mother"),
    StoryParams(place="garden", task="slipper", item="slipper", name="Leo", gender="boy", parent="father"),
    StoryParams(place="laundry", task="sock", item="sock", name="Nora", gender="girl", parent="mother"),
    StoryParams(place="study", task="book", item="book", name="Theo", gender="boy", parent="father"),
]


def generate(params: StoryParams) -> StorySample:
    world = build_world(params)
    tell(world)
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
        print(asp_program("#show valid/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        model = asp.one_model(asp_program("#show valid/2."))
        combos = sorted(set(asp.atoms(model, "valid")))
        print(f"{len(combos)} compatible fetch combinations:")
        for combo in combos:
            print("  ", combo)
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
            header = f"### {p.name}: fetch {p.item} at {p.place}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()

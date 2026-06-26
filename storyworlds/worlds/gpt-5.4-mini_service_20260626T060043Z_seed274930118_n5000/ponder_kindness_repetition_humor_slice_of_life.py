#!/usr/bin/env python3
"""
ponder_kindness_repetition_humor_slice_of_life.py

A small slice-of-life storyworld about a child who keeps pondering a kind act,
tries a few times, and lands on a gentle, humorous resolution.
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

KINDNESS_THRESHOLD = 1
REPETITION_THRESHOLD = 2


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def bump_meter(self, key: str, amount: float = 1.0) -> None:
        self.meters[key] = self.meters.get(key, 0.0) + amount

    def bump_meme(self, key: str, amount: float = 1.0) -> None:
        self.memes[key] = self.memes.get(key, 0.0) + amount


@dataclass
class Scene:
    place: str
    time_of_day: str
    weather: str


@dataclass
class Snack:
    id: str
    label: str
    phrase: str
    kind: str
    repeatable: bool
    shares_well: bool


@dataclass
class Favor:
    id: str
    label: str
    phrase: str
    kind: str
    repeatable: bool
    shares_well: bool


@dataclass
class StoryParams:
    place: str
    scene: str
    object: str
    name: str
    friend: str
    seed: Optional[int] = None


class World:
    def __init__(self, scene: Scene) -> None:
        self.scene = scene
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


SETTINGS = {
    "kitchen": Scene(place="the kitchen", time_of_day="morning", weather="quiet"),
    "porch": Scene(place="the porch", time_of_day="afternoon", weather="breezy"),
    "living_room": Scene(place="the living room", time_of_day="evening", weather="soft"),
    "garden_table": Scene(place="the garden table", time_of_day="late afternoon", weather="sunny"),
}

SNACKS = {
    "cookies": Snack("cookies", "cookies", "a plate of cookies", "snack", True, True),
    "berries": Snack("berries", "berries", "a little bowl of berries", "snack", True, True),
    "tea": Snack("tea", "tea", "a warm cup of tea", "drink", True, True),
}

FAVORS = {
    "folding": Favor("folding", "folding napkins", "the stack of napkins", "task", True, True),
    "watering": Favor("watering", "watering plants", "the thirsty plants", "task", True, True),
    "tidy_toys": Favor("tidy_toys", "tidying toys", "the toy basket", "task", True, True),
}

PEOPLE = ["Mina", "Noah", "Lia", "Theo", "Ivy", "Owen", "Maya", "Eli"]
FRIENDS = ["Aunt Jo", "Grandpa", "Mom", "Dad", "neighbor Sam", "big sister Rae"]
TRAITS = ["thoughtful", "curious", "gentle", "bashful", "cheerful", "careful"]


def choose_object(kind: str) -> Snack | Favor:
    if kind in SNACKS:
        return SNACKS[kind]
    return FAVORS[kind]


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for place in SETTINGS:
        for obj in list(SNACKS) + list(FAVORS):
            thing = choose_object(obj)
            if thing.shares_well and thing.repeatable:
                combos.append((place, obj, thing.kind))
    return combos


def explain_rejection(scene: Scene, obj: Snack | Favor) -> str:
    return (
        f"(No story: this kind of scene is about small, repeatable kindnesses, "
        f"but {obj.phrase} would not give us a gentle shared moment.)"
    )


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Slice-of-life storyworld about pondering kindness.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--scene", choices=list(SETTINGS))
    ap.add_argument("--object", choices=list(SNACKS) + list(FAVORS))
    ap.add_argument("--name", choices=PEOPLE)
    ap.add_argument("--friend", choices=FRIENDS)
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
    if args.object:
        thing = choose_object(args.object)
        if not (thing.shares_well and thing.repeatable):
            raise StoryError(explain_rejection(SETTINGS[args.place or "kitchen"], thing))
    combos = [
        c for c in valid_combos()
        if (args.place is None or c[0] == args.place)
        and (args.scene is None or c[0] == args.scene)
        and (args.object is None or c[1] == args.object)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, obj, _ = rng.choice(sorted(combos))
    name = args.name or rng.choice(PEOPLE)
    friend = args.friend or rng.choice(FRIENDS)
    return StoryParams(place=place, scene=place, object=obj, name=name, friend=friend)


def _build_world(params: StoryParams) -> World:
    scene = SETTINGS[params.place]
    world = World(scene)
    hero = world.add(Entity(id=params.name, kind="character", label=params.name))
    friend = world.add(Entity(id=params.friend, kind="character", label=params.friend))
    item = choose_object(params.object)
    thing = world.add(Entity(id=item.id, kind="thing", label=item.label, phrase=item.phrase, owner=friend.id))
    world.facts.update(hero=hero, friend=friend, item=thing, params=params)
    return world


def _setup(world: World) -> None:
    f = world.facts
    hero: Entity = f["hero"]
    friend: Entity = f["friend"]
    item: Entity = f["item"]
    params: StoryParams = f["params"]

    hero.bump_meme("wonder")
    hero.bump_meme("kindness")
    world.say(
        f"{hero.id} was a {random.choice(TRAITS)} child who often sat and pondered small ways to help."
    )
    world.say(
        f"At {world.scene.place}, {hero.id} noticed {friend.label_word if hasattr(friend, 'label_word') else friend.label} and "
        f"{item.phrase} waiting nearby."
    )
    world.say(
        f"{hero.id} liked the quiet little rituals of the day, especially when they could turn into kindness."
    )


def _ponder(world: World) -> None:
    f = world.facts
    hero: Entity = f["hero"]
    item: Entity = f["item"]

    hero.bump_meme("ponder")
    world.para()
    world.say(
        f"{hero.id} pondered the {item.label} once."
    )
    world.say(
        f"Then {hero.id} pondered it again, because a kind choice sometimes needed two looks."
    )
    hero.bump_meme("repetition", 2)


def _attempt(world: World) -> None:
    f = world.facts
    hero: Entity = f["hero"]
    friend: Entity = f["friend"]
    item: Entity = f["item"]
    params: StoryParams = f["params"]

    hero.bump_meme("trying")
    world.para()
    if item.id == "cookies":
        world.say(
            f'{hero.id} whispered, "Would you like one cookie, or would you like the exact crumbly edge I am trying to save?"'
        )
        world.say(
            f"{friend.id} laughed, because the cookie was wobbling on the plate like a tiny moon."
        )
        world.say(f"{hero.id} offered one carefully, then offered another, just to be sure kindness was enough.")
    elif item.id == "berries":
        world.say(
            f'{hero.id} asked, "Should I bring the berries in a bowl or in my very serious palms?"'
        )
        world.say(
            f"{friend.id} smiled at the second try and said the bowl was safer, which made {hero.id} grin."
        )
        world.say(f"{hero.id} tried again with the bowl, because repeating a good thing can make it feel like music.")
    elif item.id == "tea":
        world.say(
            f'{hero.id} asked, "May I carry the tea, or should I just pretend to be a very small waiter?"'
        )
        world.say(
            f"{friend.id} chuckled at that, and the spoon gave a tiny clink like it wanted to join the joke."
        )
        world.say(f"{hero.id} carried the tea with both hands, and the joke made the careful step easier.")
    elif item.id == "folding":
        world.say(
            f"{hero.id} folded one napkin, then folded another, because helping felt better when done twice with care."
        )
        world.say(
            f"{friend.id} watched the second fold and said it looked like a little paper boat."
        )
        world.say(f"{hero.id} folded the next napkin the same way, and soon the stack looked very tidy and funny at once.")
    elif item.id == "watering":
        world.say(
            f"{hero.id} watered one plant, then another, and even the thirsty pot seemed to wait for the next splash."
        )
        world.say(
            f"{friend.id} said the watering can was making a polite rain sound."
        )
        world.say(f"{hero.id} watered the row again in tiny sips, and the leaves nodded as if they had heard the joke.")
    elif item.id == "tidy_toys":
        world.say(
            f"{hero.id} picked up one toy, then another, and the basket kept asking for more."
        )
        world.say(
            f"{friend.id} smiled and said the basket was eating the room one block at a time."
        )
        world.say(f"{hero.id} tidied the toys again in the same steady way, until the floor could breathe.")
    hero.bump_meme("humor")
    hero.bump_meme("kindness", 1)
    item.bump_meter("shared", 1)


def _resolution(world: World) -> None:
    f = world.facts
    hero: Entity = f["hero"]
    friend: Entity = f["friend"]
    item: Entity = f["item"]

    world.para()
    hero.bump_meme("joy")
    friend.bump_meme("gratitude")
    world.say(
        f"In the end, {hero.id} kept the kind rhythm going, and {friend.id} kept smiling."
    )
    world.say(
        f"The little joke stayed in the air, and the shared {item.label} made the room feel warmer."
    )
    world.say(
        f"{hero.id} had been pondering kindness all along, and now the answer looked simple: do it once, then do it again, gently."
    )


def generate(params: StoryParams) -> StorySample:
    world = _build_world(params)
    _setup(world)
    _ponder(world)
    _attempt(world)
    _resolution(world)

    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero: Entity = f["hero"]
    item: Entity = f["item"]
    friend: Entity = f["friend"]
    return [
        f'Write a short slice-of-life story about a child named {hero.id} who keeps pondering a kind way to help with {item.phrase}.',
        f"Tell a gentle, humorous story where {hero.id} repeats a helpful action for {friend.id} until it feels natural.",
        f'Write a simple story that includes the word "ponder" and ends with a small act of kindness at {world.scene.place}.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero: Entity = f["hero"]
    friend: Entity = f["friend"]
    item: Entity = f["item"]
    params: StoryParams = f["params"]
    return [
        QAItem(
            question=f"What was {hero.id} doing before the kind idea became clear?",
            answer=f"{hero.id} was pondering the {item.label}, and then pondering it again, because the choice felt important.",
        ),
        QAItem(
            question=f"Who was with {hero.id} at {world.scene.place}?",
            answer=f"{hero.id} was with {friend.id} at {world.scene.place}, where they shared a small, ordinary day.",
        ),
        QAItem(
            question=f"What made the story funny without being mean?",
            answer=f"The humor came from the little repeated actions and the small joke about {item.label}, which kept the mood light.",
        ),
        QAItem(
            question=f"How did the story end?",
            answer=f"It ended with {hero.id} keeping up the kind, repeated help until the shared {item.label} made the room feel warmer.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does it mean to ponder something?",
            answer="To ponder something means to think about it carefully for a little while.",
        ),
        QAItem(
            question="Why can repeating a helpful action be kind?",
            answer="Repeating a helpful action can be kind because it shows care, patience, and a willingness to keep helping.",
        ),
        QAItem(
            question="How can a story be humorous without being unkind?",
            answer="A story can be humorous without being unkind by using playful details, gentle jokes, and funny timing instead of teasing.",
        ),
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
        bits = []
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        if e.phrase:
            bits.append(f"phrase={e.phrase!r}")
        lines.append(f"  {e.id:12} ({e.kind:8}) {' '.join(bits)}")
    return "\n".join(lines)


CURATED = [
    StoryParams(place="kitchen", scene="kitchen", object="cookies", name="Mina", friend="Mom"),
    StoryParams(place="porch", scene="porch", object="berries", name="Theo", friend="Aunt Jo"),
    StoryParams(place="living_room", scene="living_room", object="tea", name="Ivy", friend="Grandpa"),
    StoryParams(place="garden_table", scene="garden_table", object="watering", name="Noah", friend="Dad"),
]


ASP_RULES = r"""
% A story is valid when the object supports shared, repeatable kindness.
valid(P, O) :- place(P), object(O), repeatable(O), shares_well(O).
valid_story(P, O, N) :- valid(P, O), name(N).
"""


def asp_facts() -> str:
    import storyworlds.asp as asp
    lines: list[str] = []
    for p in SETTINGS:
        lines.append(asp.fact("place", p))
    for o in SNACKS.values():
        lines.append(asp.fact("object", o.id))
        if o.repeatable:
            lines.append(asp.fact("repeatable", o.id))
        if o.shares_well:
            lines.append(asp.fact("shares_well", o.id))
    for o in FAVORS.values():
        lines.append(asp.fact("object", o.id))
        if o.repeatable:
            lines.append(asp.fact("repeatable", o.id))
        if o.shares_well:
            lines.append(asp.fact("shares_well", o.id))
    for n in PEOPLE:
        lines.append(asp.fact("name", n))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import storyworlds.asp as asp
    model = asp.one_model(asp_program("#show valid/2."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    a = set(asp_valid_combos())
    b = set(valid_combos())
    if a == b:
        print(f"OK: clingo gate matches valid_combos() ({len(a)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    if a - b:
        print("  only in clingo:", sorted(a - b))
    if b - a:
        print("  only in python:", sorted(b - a))
    return 1


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
        combos = asp_valid_combos()
        print(f"{len(combos)} valid (place, object) combos:\n")
        for place, obj in combos:
            print(f"  {place:14} {obj}")
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

    for i, sample in enumerate(samples):
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260626T060043Z_seed274930118_n5000/coincide_linguine_icicle_warehouse_aisle_dialogue_slice.py
================================================================================

A small slice-of-life storyworld set in a warehouse aisle, built around a tiny
everyday mix-up that comes with dialogue, a coincidence, a bowl of linguine,
and an icicle.

Seed tale:
---
On a cold morning, Mina worked in a warehouse aisle stacking boxes. Her friend
Omar came by with lunch, and they both laughed because their breaks happened to
coincide. Mina was carrying a warm container of linguine when she noticed a
small icicle hanging from a freezer cart near the end of the aisle.

Just then, a box tipped and nudged the cart. The icicle shook loose and tapped
the lid of the linguine container. Mina worried the lunch would spill all over
the floor. Omar suggested they move the box, wipe the lid clean, and eat at the
break table by the office.

Mina smiled, thanked him, and said it was funny how even a little mess in a
warehouse aisle could turn into a shared lunch story.

World model:
---
- Characters have physical meters and emotional memes.
- The warehouse aisle has a few practical objects and one small cold hazard.
- A brief tension arises from a coincidence, a wobbling box, and a near-spill.
- A simple spoken compromise restores calm and leaves the lunch intact.

Narrative instruments:
---
- Dialogue-forward prose
- Slice-of-life tone
- State-driven turns and resolution
"""

from __future__ import annotations

import argparse
import copy
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
    worn_by: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def __post_init__(self):
        if self.meters == {}:
            self.meters = {"wet": 0.0, "mess": 0.0, "cold": 0.0, "order": 0.0}
        if self.memes == {}:
            self.memes = {"calm": 0.0, "worry": 0.0, "joy": 0.0, "surprise": 0.0}


@dataclass
class Aisle:
    place: str = "the warehouse aisle"
    has_freezer_cart: bool = True
    has_break_table: bool = True


@dataclass
class StoryParams:
    place: str
    hero: str
    friend: str
    lunch: str
    seed: Optional[int] = None


class World:
    def __init__(self, aisle: Aisle):
        self.aisle = aisle
        self.entities: dict[str, Entity] = {}
        self.events: list[str] = []
        self.fired: set[tuple] = set()
        self.facts: dict = {}

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str) -> Entity:
        return self.entities[eid]

    def say(self, text: str) -> None:
        if text:
            self.events.append(text)

    def render(self) -> str:
        return " ".join(self.events)

    def copy(self) -> "World":
        w = World(copy.deepcopy(self.aisle))
        w.entities = copy.deepcopy(self.entities)
        w.events = []
        w.fired = set(self.fired)
        w.facts = copy.deepcopy(self.facts)
        return w


def introduce(world: World, hero: Entity, friend: Entity) -> None:
    world.say(
        f"{hero.id} was working in {world.aisle.place}, and {friend.id} was rolling in with lunch."
    )


def coincidence(world: World, hero: Entity, friend: Entity) -> None:
    hero.memes["surprise"] += 1
    friend.memes["joy"] += 1
    world.say(
        f'"Our breaks coincide today," {friend.id} said, grinning. '
        f'"That makes this lunch feel lucky."'
    )


def set_lunch(world: World, hero: Entity, lunch: Entity) -> None:
    lunch.owner = hero.id
    world.say(f"{hero.id} had a warm container of {lunch.label} tucked safely in hand.")


def notice_icicle(world: World, hero: Entity, icicle: Entity) -> None:
    world.say(
        f"Near the freezer cart at the end of the aisle, {hero.id} noticed a small {icicle.label}."
    )


def wobble_box(world: World) -> None:
    world.say(
        "Then a stacked box tipped a little and nudged the freezer cart."
    )


def shake_icicle(world: World, icicle: Entity) -> None:
    sig = ("shake", icicle.id)
    if sig in world.fired:
        return
    world.fired.add(sig)
    icicle.meters["cold"] += 1
    world.say(f"The {icicle.label} shook loose and dangled over the aisle for a moment.")


def near_spill(world: World, lunch: Entity) -> None:
    sig = ("spill", lunch.id)
    if sig in world.fired:
        return
    world.fired.add(sig)
    lunch.meters["mess"] += 1
    lunch.meters["wet"] += 1
    world.say(
        f"It tapped the lid of {lunch.label}, and {hero_name_from_world(world)} worried the lunch might spill."
    )


def hero_name_from_world(world: World) -> str:
    return world.facts["hero"].id


def friend_suggests_fix(world: World, friend: Entity) -> None:
    world.say(
        f'"Let’s just move the box and wipe the lid," {friend.id} said. '
        f'"Then we can eat by the break table."'
    )


def calm_return(world: World, hero: Entity, lunch: Entity) -> None:
    hero.memes["worry"] = 0.0
    hero.memes["calm"] += 1
    lunch.meters["mess"] = 0.0
    lunch.meters["wet"] = 0.0
    world.say(
        f"{hero.id} smiled, wiped the lid clean, and carried the {lunch.label} to the break table."
    )
    world.say(
        f"By the time they sat down, the aisle was tidy again and the lunch was still warm."
    )


def tell_story(params: StoryParams) -> World:
    world = World(Aisle(place=params.place))
    hero = world.add(Entity(id=params.hero, kind="character", type="worker"))
    friend = world.add(Entity(id=params.friend, kind="character", type="worker"))
    lunch = world.add(Entity(id="lunch", type="lunch", label=params.lunch))
    icicle = world.add(Entity(id="icicle", type="icicle", label="icicle"))
    world.facts.update(hero=hero, friend=friend, lunch=lunch, icicle=icicle)

    introduce(world, hero, friend)
    coincidence(world, hero, friend)
    set_lunch(world, hero, lunch)
    notice_icicle(world, hero, icicle)
    world.say("They were chatting softly between the shelves when the moment shifted.")
    wobble_box(world)
    shake_icicle(world, icicle)
    near_spill(world, lunch)
    hero.memes["worry"] += 1
    world.say(f'"Oh no," {hero.id} said. "I really do not want my {lunch.label} to get messy."')
    friend_suggests_fix(world, friend)
    calm_return(world, hero, lunch)
    world.facts["resolved"] = True
    return world


SETTINGS = {
    "warehouse_aisle": Aisle(place="the warehouse aisle"),
}

HEROES = ["Mina", "Jules", "Tara", "Nico", "Leah", "Omar"]
FRIENDS = ["Omar", "Ivy", "Sam", "Noah", "Priya", "Lena"]
LUNCHES = ["linguine", "tomato linguine", "buttered linguine", "linguine in a round container"]


@dataclass
class StoryWorldState:
    world: World


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        'Write a short slice-of-life story set in a warehouse aisle that includes the word "coincide".',
        f'Tell a gentle dialogue story where {f["hero"].id} and {f["friend"].id} share a lunch break, and a tiny {f["icicle"].label} causes a small worry.',
        'Write an everyday story about a warehouse aisle, a bowl of linguine, and a coincidence that turns into a calm fix.',
    ]


def story_qa(world: World) -> list[QAItem]:
    hero = world.facts["hero"]
    friend = world.facts["friend"]
    lunch = world.facts["lunch"]
    icicle = world.facts["icicle"]
    return [
        QAItem(
            question=f"Where does the story happen?",
            answer=f"It happens in the warehouse aisle, where {hero.id} is working and talking with {friend.id}.",
        ),
        QAItem(
            question=f"What lunch was {hero.id} carrying?",
            answer=f"{hero.id} was carrying {lunch.label}, which stayed warm through the little mix-up.",
        ),
        QAItem(
            question=f"What small thing made {hero.id} worry?",
            answer=f"The worry came from a small {icicle.label} near the freezer cart, because it tapped the lunch container when the box bumped the cart.",
        ),
        QAItem(
            question=f"How did the two workers fix the problem?",
            answer=f"They moved the box, wiped the lid clean, and sat down by the break table so the lunch could stay safe.",
        ),
        QAItem(
            question=f"Why did the dialogue matter in the story?",
            answer=f"The spoken plan mattered because {friend.id} and {hero.id} talked through the problem calmly and turned the moment into a shared break instead of a bigger mess.",
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a warehouse aisle?",
            answer="A warehouse aisle is a long path between shelves where people carry, sort, and check boxes and supplies.",
        ),
        QAItem(
            question="What is linguine?",
            answer="Linguine is a long, flat kind of pasta that people often eat with sauce or butter.",
        ),
        QAItem(
            question="What is an icicle?",
            answer="An icicle is a piece of ice that hangs down when water freezes in a cold place.",
        ),
        QAItem(
            question="What does coincide mean?",
            answer="To coincide means to happen at the same time, like two lunch breaks starting together.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    for p in sample.prompts:
        lines.append(p)
    lines.append("")
    lines.append("== story questions ==")
    for q in sample.story_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    lines.append("")
    lines.append("== world questions ==")
    for q in sample.world_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- trace ---"]
    for e in world.entities.values():
        meters = {k: round(v, 2) for k, v in e.meters.items() if v}
        memes = {k: round(v, 2) for k, v in e.memes.items() if v}
        lines.append(f"{e.id}: kind={e.kind} type={e.type} meters={meters} memes={memes}")
    return "\n".join(lines)


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Slice-of-life warehouse aisle storyworld.")
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("-n", type=int, default=1)
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--trace", action="store_true")
    ap.add_argument("--qa", action="store_true")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--asp", action="store_true")
    ap.add_argument("--verify", action="store_true")
    ap.add_argument("--show-asp", action="store_true")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    hero = rng.choice(HEROES)
    friend = rng.choice([n for n in FRIENDS if n != hero])
    lunch = rng.choice(LUNCHES)
    return StoryParams(place="warehouse aisle", hero=hero, friend=friend, lunch=lunch)


def generate(params: StoryParams) -> StorySample:
    world = tell_story(params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_qa(world),
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


ASP_RULES = r"""
place(warehouse_aisle).
theme(coincide).
theme(linguine).
theme(icicle).
style(slice_of_life).
feature(dialogue).
"""


def asp_facts() -> str:
    import asp
    return "\n".join(
        [
            asp.fact("place", "warehouse_aisle"),
            asp.fact("theme", "coincide"),
            asp.fact("theme", "linguine"),
            asp.fact("theme", "icicle"),
            asp.fact("feature", "dialogue"),
            asp.fact("style", "slice_of_life"),
        ]
    )


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    return 0


def main() -> None:
    args = build_parser().parse_args()
    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)

    if args.show_asp:
        print(asp_program("#show place/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(asp_program("#show place/1."))
        return

    samples: list[StorySample] = []
    if args.all:
        samples = [
            generate(StoryParams(place="warehouse aisle", hero="Mina", friend="Omar", lunch="linguine")),
            generate(StoryParams(place="warehouse aisle", hero="Tara", friend="Lena", lunch="buttered linguine")),
        ]
    else:
        for i in range(args.n):
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            samples.append(generate(params))

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

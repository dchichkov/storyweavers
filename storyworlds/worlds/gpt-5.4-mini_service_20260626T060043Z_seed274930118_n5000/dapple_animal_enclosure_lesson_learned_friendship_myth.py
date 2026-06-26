#!/usr/bin/env python3
"""
A small myth-style story world set in an animal enclosure.

Seed premise:
A dapple-marked young zebra wants to impress a shy giraffe in the enclosure.
A cracked water trough, a dusty path, and a too-loud boast create trouble.
A friend teaches a quieter way, and the lesson learned becomes part of the ending.

The world is built as a tiny simulation with physical meters and emotional memes.
"""

from __future__ import annotations

import argparse
import json
import os
import random
import sys
from dataclasses import dataclass, field, asdict
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
    traits: list[str] = field(default_factory=list)
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"zebra", "giraffe", "lion", "fox", "animal"}:
            return {"subject": "they", "object": "them", "possessive": "their"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class Setting:
    place: str = "the animal enclosure"
    affords: set[str] = field(default_factory=lambda: {"dust", "water", "song"})


@dataclass
class StoryParams:
    animal: str
    friend: str
    lesson: str
    seed: Optional[int] = None


@dataclass
class World:
    setting: Setting
    entities: dict[str, Entity] = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    facts: dict = field(default_factory=dict)
    fired: set[tuple] = field(default_factory=set)
    zone: set[str] = field(default_factory=set)

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


ANIMALS = {
    "zebra": {
        "type": "zebra",
        "label": "young zebra",
        "phrase": "a young zebra with dappled stripes",
        "traits": ["dappled", "restless"],
    },
    "giraffe": {
        "type": "giraffe",
        "label": "shy giraffe",
        "phrase": "a shy giraffe with a calm neck",
        "traits": ["quiet", "kind"],
    },
    "lion": {
        "type": "lion",
        "label": "proud lion",
        "phrase": "a proud lion with a golden mane",
        "traits": ["proud", "loud"],
    },
    "gazelle": {
        "type": "gazelle",
        "label": "swift gazelle",
        "phrase": "a swift gazelle with bright eyes",
        "traits": ["swift", "watchful"],
    },
}

LESSONS = [
    "the loudest hoof is not always the wisest step",
    "friends grow closer when they share water and worries",
    "a boast can dry up, but kindness can open a spring",
    "to lead the herd, one must first learn to listen",
]


def make_world(params: StoryParams) -> World:
    world = World(Setting())
    hero_cfg = ANIMALS[params.animal]
    friend_cfg = ANIMALS[params.friend]

    hero = world.add(Entity(
        id="hero",
        kind="character",
        type=hero_cfg["type"],
        label=hero_cfg["label"],
        phrase=hero_cfg["phrase"],
        traits=list(hero_cfg["traits"]),
        meters={"dust": 0.0, "water": 0.0, "care": 0.0},
        memes={"pride": 1.0, "joy": 0.0, "worry": 0.0, "friendship": 0.0, "lesson": 0.0},
    ))
    friend = world.add(Entity(
        id="friend",
        kind="character",
        type=friend_cfg["type"],
        label=friend_cfg["label"],
        phrase=friend_cfg["phrase"],
        traits=list(friend_cfg["traits"]),
        meters={"dust": 0.0, "water": 0.0, "care": 0.0},
        memes={"pride": 0.0, "joy": 0.0, "worry": 1.0, "friendship": 1.0, "lesson": 0.0},
    ))
    trough = world.add(Entity(
        id="trough",
        kind="thing",
        type="trough",
        label="water trough",
        phrase="a cracked stone water trough",
        meters={"water": 1.0, "crack": 1.0},
        memes={"need": 1.0},
    ))
    path = world.add(Entity(
        id="path",
        kind="thing",
        type="path",
        label="dusty path",
        phrase="a dusty path beneath the acacia trees",
        meters={"dust": 1.0},
        memes={"silence": 1.0},
    ))
    world.facts.update(hero=hero, friend=friend, trough=trough, path=path, lesson=params.lesson)
    return world


def spill_dust(world: World, actor: Entity) -> None:
    if ("dust", actor.id) in world.fired:
        return
    world.fired.add(("dust", actor.id))
    actor.meters["dust"] += 1.0
    actor.memes["pride"] += 0.5
    actor.memes["worry"] += 0.5
    world.say(f"{actor.label.capitalize()} stamped the dusty path and sent a pale cloud around {actor.pronoun('object')}.")


def seek_water(world: World, actor: Entity, trough: Entity) -> None:
    if trough.meters.get("water", 0.0) < THRESHOLD:
        return
    world.say(f"{actor.label.capitalize()} went to the water trough, hoping to rinse away the dust and look grand.")
    actor.meters["water"] += 1.0
    actor.memes["joy"] += 0.5


def conflict(world: World, actor: Entity, friend: Entity, trough: Entity) -> None:
    if actor.meters["dust"] < THRESHOLD or friend.memes["worry"] < THRESHOLD:
        return
    world.say(
        f"But the trough was cracked, and the water slipped away faster than praise. "
        f"{friend.label.capitalize()} warned that showing off near a broken thing could leave the whole enclosure thirsty."
    )
    actor.memes["worry"] += 1.0
    friend.memes["friendship"] += 1.0


def lesson_turn(world: World, actor: Entity, friend: Entity) -> None:
    actor.memes["lesson"] += 1.0
    actor.memes["pride"] = max(0.0, actor.memes["pride"] - 0.5)
    actor.memes["friendship"] += 1.0
    friend.memes["friendship"] += 1.0
    world.say(
        f"{actor.label.capitalize()} listened at last. "
        f"{friend.label.capitalize()} taught {actor.pronoun('object')} that a friend is not a mirror for boasting, but a companion for care."
    )


def repair_and_share(world: World, actor: Entity, friend: Entity, trough: Entity) -> None:
    trough.meters["water"] += 1.0
    actor.meters["care"] += 1.0
    friend.meters["care"] += 1.0
    actor.memes["joy"] += 1.0
    friend.memes["joy"] += 1.0
    world.say(
        f"Together they carried clean reeds to shade the trough, then waited until the keeper brought fresh water. "
        f"The dapple-marked one drank last, and the shy one drank first."
    )


def tell_story(world: World) -> None:
    hero = world.get("hero")
    friend = world.get("friend")
    trough = world.get("trough")
    path = world.get("path")

    world.say(
        f"In the old days, when the animal enclosure was spoken of like a little kingdom, "
        f"{hero.phrase} lived beside {friend.phrase}."
    )
    world.say(
        f"{hero.label.capitalize()} was known for {hero.traits[0]} stripes and a heart that wanted to shine, "
        f"while {friend.label} was known for listening to leaves before speaking."
    )
    world.say(
        f"Every dawn they met near {path.phrase}, where the acacia shadows made spots on the ground like painted eggs."
    )

    world.para()
    spill_dust(world, hero)
    seek_water(world, hero, trough)
    conflict(world, hero, friend, trough)

    world.para()
    lesson_turn(world, hero, friend)
    repair_and_share(world, hero, friend, trough)

    world.para()
    world.say(
        f"So the enclosure did not remember only the dappled one who wished to be admired. "
        f"It remembered two friends who learned that care makes a stronger tale than pride."
    )
    world.say(
        f"From then on, whenever the sun made bright spots on the stones, the keeper smiled and called it the lesson learned: "
        f"{world.facts['lesson']}."
    )

    world.facts["story_done"] = True


def story_qa(world: World) -> list[QAItem]:
    hero = world.get("hero")
    friend = world.get("friend")
    lesson = world.facts["lesson"]
    return [
        QAItem(
            question=f"Who was the story about in the animal enclosure?",
            answer=f"It was about {hero.label}, who had dappled stripes and wanted to shine, and about {friend.label}, who was quiet but kind.",
        ),
        QAItem(
            question=f"What problem made the dappled animal stop and listen?",
            answer="The water trough was cracked, so the water slipped away and showing off would not help the enclosure at all.",
        ),
        QAItem(
            question="What lesson was learned in the end?",
            answer=f"The lesson learned was that {lesson}.",
        ),
        QAItem(
            question="How did the two animals become friends again?",
            answer="They listened to each other, shared the work of caring for the trough, and waited for fresh water together.",
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is an animal enclosure?",
            answer="An animal enclosure is a safe place where animals live, rest, and are cared for by keepers.",
        ),
        QAItem(
            question="What does dappled mean?",
            answer="Dappled means covered in spots or patches of different color, like sunlight through leaves or markings on an animal.",
        ),
        QAItem(
            question="What is friendship?",
            answer="Friendship is when beings care about each other, help each other, and stay kind even when things go wrong.",
        ),
        QAItem(
            question="Why do keepers give animals water?",
            answer="Keepers give animals water so they can drink, stay healthy, and cool themselves on warm days.",
        ),
    ]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Myth-style story world in an animal enclosure.")
    ap.add_argument("--animal", choices=sorted(ANIMALS))
    ap.add_argument("--friend", choices=sorted(ANIMALS))
    ap.add_argument("--lesson", choices=range(len(LESSONS)), type=int)
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
    animal = args.animal or rng.choice(sorted(ANIMALS))
    friend = args.friend or rng.choice([a for a in sorted(ANIMALS) if a != animal])
    lesson_idx = args.lesson if args.lesson is not None else rng.randrange(len(LESSONS))
    if animal == friend:
        raise StoryError("The hero and friend must be different animals.")
    return StoryParams(animal=animal, friend=friend, lesson=LESSONS[lesson_idx])


def generate(params: StoryParams) -> StorySample:
    world = make_world(params)
    tell_story(world)
    prompts = [
        f"Write a short myth for a child about a dapple-marked {params.animal} in an animal enclosure.",
        f"Tell a friendship story set in an animal enclosure where a {params.animal} learns a lesson from a {params.friend}.",
        f"Write a gentle myth that ends with the lesson learned: {params.lesson}.",
    ]
    return StorySample(
        params=params,
        story=world.render(),
        prompts=prompts,
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
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        lines.append(f"  {e.id:6} ({e.type:8}) meters={meters} memes={memes}")
    return "\n".join(lines)


ASP_RULES = r"""
animal(hero).
animal(friend).
lesson(L) :- lesson_text(L).

dappled(hero).
friendship(friend, hero) :- learned(hero, lesson).
lesson_learned(hero) :- learned(hero, lesson).

valid_story(A, F, L) :- animal(A), animal(F), A != F, lesson(L).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for a in ANIMALS:
        lines.append(asp.fact("animal", a))
    for i, lesson in enumerate(LESSONS):
        lines.append(asp.fact("lesson_text", lesson))
        lines.append(asp.fact("lesson_id", i))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    try:
        import asp
    except Exception as exc:
        print(f"ASP unavailable: {exc}")
        return 1
    model = asp.one_model(asp_program("#show valid_story/3."))
    asp_set = set(asp.atoms(model, "valid_story"))
    py_set = {(a, f, LESSONS[i]) for a in ANIMALS for f in ANIMALS if a != f for i in range(len(LESSONS))}
    if asp_set == py_set:
        print(f"OK: clingo gate matches Python gate ({len(py_set)} combos).")
        return 0
    print("MISMATCH between clingo and Python gate.")
    return 1


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid_story/3."))
        return
    if args.verify:
        sys.exit(asp_verify())

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        for a in sorted(ANIMALS):
            for f in sorted(ANIMALS):
                if a == f:
                    continue
                for i, lesson in enumerate(LESSONS):
                    params = StoryParams(animal=a, friend=f, lesson=lesson, seed=i)
                    samples.append(generate(params))
    else:
        seen = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 20, 20):
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

    for i, sample in enumerate(samples):
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""
A standalone storyworld for a small folk-tale misunderstanding: a careful,
thorough helper and a wiggle-prone animal keep misunderstanding each other until
repetition of a simple plan clears things up.
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
    plural: bool = False
    owner: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "woman", "mother", "sister", "maiden"}
        male = {"boy", "man", "father", "brother", "herder", "grandfather"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def noun(self) -> str:
        return self.label or self.type

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Place:
    id: str
    label: str
    indoors: bool = False
    traits: set[str] = field(default_factory=set)


@dataclass
class Task:
    id: str
    verb: str
    gerund: str
    misunderstanding: str
    repeated_step: str
    keyword: str
    effect: str
    place_traits: set[str] = field(default_factory=set)


@dataclass
class Item:
    id: str
    label: str
    phrase: str
    carried_by: Optional[str] = None
    sacred: bool = False
    important: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)


class World:
    def __init__(self, place: Place) -> None:
        self.place = place
        self.entities: dict[str, Entity] = {}
        self.items: dict[str, Item] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
        self.facts: dict = {}

    def add_entity(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def add_item(self, item: Item) -> Item:
        self.items[item.id] = item
        return item

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


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Folk tale storyworld with misunderstanding and repetition.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--task", choices=TASKS)
    ap.add_argument("--hero", choices=HERO_NAMES)
    ap.add_argument("--companion", choices=COMPANIONS)
    ap.add_argument("--item", choices=ITEMS)
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


PLACES = {
    "orchard": Place("orchard", "the orchard", traits={"trees", "apples", "paths"}),
    "hill": Place("hill", "the hill", traits={"grass", "wind", "paths"}),
    "riverbank": Place("riverbank", "the riverbank", traits={"water", "reeds", "paths"}),
}

TASKS = {
    "bells": Task(
        "bells",
        verb="ring the bells",
        gerund="ringing the bells",
        misunderstanding="the bells were calling for trouble",
        repeated_step="ring the bells three times, slow as rain",
        keyword="bells",
        effect="the sound carried far and wide",
        place_traits={"paths"},
    ),
    "basket": Task(
        "basket",
        verb="carry the basket",
        gerund="carrying the basket",
        misunderstanding="the basket was too heavy to trust",
        repeated_step="lift the basket with two hands, once more",
        keyword="basket",
        effect="the basket held together kindly",
        place_traits={"paths", "orchard"},
    ),
    "lantern": Task(
        "lantern",
        verb="light the lantern",
        gerund="lighting the lantern",
        misunderstanding="the lantern would wake the night things",
        repeated_step="cover the lantern, then lift it again",
        keyword="lantern",
        effect="the light shone warm and small",
        place_traits={"paths", "water"},
    ),
}

HERO_NAMES = ["Mira", "Toma", "Nessa", "Bram", "Lina", "Rowan", "Pip", "Elin"]
COMPANIONS = {
    "fox": ("fox", "fox", "little fox"),
    "goat": ("goat", "goat", "stubborn goat"),
    "crow": ("crow", "crow", "black crow"),
    "mouse": ("mouse", "mouse", "small mouse"),
}
ITEMS = {
    "cloak": Item("cloak", "cloak", "a woven cloak"),
    "cake": Item("cake", "cake", "a sweet honey cake"),
    "key": Item("key", "key", "a small brass key"),
    "jar": Item("jar", "jar", "a jar of seeds"),
}
GENDERS = ["girl", "boy"]


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for pid, place in PLACES.items():
        for tid, task in TASKS.items():
            if not (place.traits & task.place_traits):
                continue
            for iid in ITEMS:
                combos.append((pid, tid, iid))
    return combos


def explain_rejection(place: Place, task: Task, item: Item) -> str:
    return (
        f"(No story: {task.gerund} and {place.label} do not make a strong folk-tale problem "
        f"for {item.label}. Choose a place with matching paths, water, orchard, or wind.)"
    )


def resolve_params(args: argparse.Namespace, rng: random.Random) -> "StoryParams":
    if args.place and args.task and args.item:
        place, task, item = PLACES[args.place], TASKS[args.task], ITEMS[args.item]
        if (args.place, args.task, args.item) not in valid_combos():
            raise StoryError(explain_rejection(place, task, item))
    combos = [c for c in valid_combos()
              if (args.place is None or c[0] == args.place)
              and (args.task is None or c[1] == args.task)
              and (args.item is None or c[2] == args.item)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, task, item = rng.choice(sorted(combos))
    hero = args.hero or rng.choice(HERO_NAMES)
    companion_key = args.companion or rng.choice(list(COMPANIONS))
    item_id = item
    gender = rng.choice(GENDERS)
    return StoryParams(
        place=place,
        task=task,
        hero=hero,
        companion=companion_key,
        item=item_id,
        gender=gender,
        seed=args.seed,
    )


@dataclass
class StoryParams:
    place: str
    task: str
    hero: str
    companion: str
    item: str
    gender: str
    seed: Optional[int] = None


def narrate_setup(world: World, hero: Entity, companion: Entity, task: Task, item: Item) -> None:
    world.say(
        f"Once, in {world.place.label}, there lived {hero.pronoun('subject')} named {hero.id}, "
        f"and {companion.pronoun('subject')} friend, {companion.label}."
    )
    world.say(
        f"{hero.id} was thorough and careful, and {hero.id} loved to {task.verb} because "
        f"{task.effect}."
    )
    world.say(
        f"Each day, {hero.id} carried {item.phrase} and hoped the work would go well."
    )


def narrate_misunderstanding(world: World, hero: Entity, companion: Entity, task: Task, item: Item) -> None:
    hero.memes["worry"] = hero.memes.get("worry", 0) + 1
    companion.memes["fear"] = companion.memes.get("fear", 0) + 1
    world.para()
    world.say(
        f"But one morning, {companion.id} saw {hero.id} ready to {task.verb} and made a quick mistake."
    )
    world.say(
        f"{companion.id} thought that {task.misunderstanding}, so {companion.pronoun('subject')} begged, "
        f"\"Wait, wait, wait!\""
    )
    world.say(
        f"{hero.id} heard the plea and frowned, for {hero.id} did not yet know why the words were so small and sharp."
    )


def narrate_repetition(world: World, hero: Entity, companion: Entity, task: Task, item: Item) -> None:
    world.para()
    world.say(
        f"{hero.id} did not shout. {hero.id} took a breath, and, being thorough, "
        f"{hero.id} began again."
    )
    world.say(
        f"\"We {task.verb},\" {hero.pronoun('subject')} said. \"We {task.verb}, and then we {task.repeated_step}.\""
    )
    world.say(
        f"{hero.id} said it once, and then again, and then a third time, slow and clear."
    )
    world.say(
        f"At last, {companion.id} listened closely and saw that the plan was gentle. "
        f"{companion.id} gave a small nod."
    )
    world.say(
        f"Together they went on, and {hero.id} kept {task.gerund}, while {companion.id} carried {item.phrase} the safe way."
    )


def narrate_resolution(world: World, hero: Entity, companion: Entity, task: Task, item: Item) -> None:
    world.para()
    world.say(
        f"By sunset, the misunderstanding had drifted away like fog over the path."
    )
    world.say(
        f"{hero.id} was still thorough, {companion.id} was no longer afraid, and the {task.keyword} work was done."
    )
    world.say(
        f"That night, {item.phrase} rested beside the hearth, and the two friends smiled at the tidy, quiet end."
    )


def generate_world(params: StoryParams) -> World:
    place = PLACES[params.place]
    task = TASKS[params.task]
    item = ITEMS[params.item]
    world = World(place)

    hero = world.add_entity(Entity(
        id=params.hero,
        kind="character",
        type=params.gender,
        label=params.hero,
        memes={"thoroughness": 1.0, "calm": 1.0},
    ))
    companion_type, companion_label, companion_phrase = COMPANIONS[params.companion]
    companion = world.add_entity(Entity(
        id=companion_label.capitalize(),
        kind="character",
        type=companion_type,
        label=companion_label,
        phrase=companion_phrase,
        memes={"nervousness": 1.0},
    ))
    world.add_item(item)
    item.carried_by = hero.id

    narrate_setup(world, hero, companion, task, item)
    narrate_misunderstanding(world, hero, companion, task, item)
    narrate_repetition(world, hero, companion, task, item)
    narrate_resolution(world, hero, companion, task, item)

    world.facts = {
        "hero": hero,
        "companion": companion,
        "task": task,
        "item": item,
        "place": place,
    }
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a short folk tale for a child about {f["hero"].id}, {f["companion"].label}, and the word "{f["task"].keyword}".',
        f"Tell a gentle story in which a thorough helper must repeat the plan three times so a misunderstanding clears up.",
        f"Write a simple tale set at {f['place'].label} where one friend is worried, then calms down after hearing the same idea again and again.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    companion = f["companion"]
    task = f["task"]
    item = f["item"]
    place = f["place"]
    return [
        QAItem(
            question=f"Who was the thorough helper in the story?",
            answer=f"The thorough helper was {hero.id}, who kept explaining the plan clearly.",
        ),
        QAItem(
            question=f"What did {companion.id} misunderstand at {place.label}?",
            answer=f"{companion.id} thought that {task.misunderstanding}, but that was not true.",
        ),
        QAItem(
            question=f"What helped the misunderstanding go away?",
            answer=f"Repetition helped, because {hero.id} said the plan again and again until {companion.id} understood.",
        ),
        QAItem(
            question=f"What item was carried through the story?",
            answer=f"They carried {item.phrase}, and it stayed safe by the end.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does it mean to be thorough?",
            answer="To be thorough means to do something carefully, fully, and with attention so nothing important is missed.",
        ),
        QAItem(
            question="What is repetition?",
            answer="Repetition means saying or doing the same thing more than once. It can help someone remember or understand.",
        ),
        QAItem(
            question="What is a folk tale?",
            answer="A folk tale is an old-style story that is simple, memorable, and often taught by telling it aloud.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== Story questions =="]
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== World knowledge questions ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    lines.append(f"place: {world.place.label}")
    for e in world.entities.values():
        lines.append(f"entity: {e.id} type={e.type} meters={e.meters} memes={e.memes}")
    for i in world.items.values():
        lines.append(f"item: {i.label} carried_by={i.carried_by}")
    return "\n".join(lines)


def generate(params: StoryParams) -> StorySample:
    world = generate_world(params)
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


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid, place in PLACES.items():
        lines.append(asp.fact("place", pid))
        for t in sorted(place.traits):
            lines.append(asp.fact("trait", pid, t))
    for tid, task in TASKS.items():
        lines.append(asp.fact("task", tid))
        for t in sorted(task.place_traits):
            lines.append(asp.fact("needs", tid, t))
    for iid in ITEMS:
        lines.append(asp.fact("item", iid))
    return "\n".join(lines)


ASP_RULES = r"""
valid(Place, Task, Item) :- place(Place), task(Task), item(Item),
                            trait(Place, T), needs(Task, T).
#show valid/3.
"""


def asp_program() -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program())
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    py = set(valid_combos())
    ac = set(asp_valid_combos())
    if py == ac:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    if py - ac:
        print("  only in python:", sorted(py - ac))
    if ac - py:
        print("  only in clingo:", sorted(ac - py))
    return 1


CURATED = [
    StoryParams(place="orchard", task="basket", hero="Mira", companion="fox", item="basket", gender="girl"),
    StoryParams(place="hill", task="bells", hero="Bram", companion="goat", item="cloak", gender="boy"),
    StoryParams(place="riverbank", task="lantern", hero="Nessa", companion="crow", item="lantern", gender="girl"),
]


def build_storysample_from_args(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    combos = [c for c in valid_combos()
              if (args.place is None or c[0] == args.place)
              and (args.task is None or c[1] == args.task)
              and (args.item is None or c[2] == args.item)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, task, item = rng.choice(sorted(combos))
    hero = args.hero or rng.choice(HERO_NAMES)
    companion = args.companion or rng.choice(list(COMPANIONS))
    gender = rng.choice(GENDERS)
    return StoryParams(place=place, task=task, hero=hero, companion=companion, item=item, gender=gender, seed=args.seed)


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for pid, place in PLACES.items():
        for tid, task in TASKS.items():
            if not (place.traits & task.place_traits):
                continue
            for iid in ITEMS:
                combos.append((pid, tid, iid))
    return combos


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program())
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
            params = build_storysample_from_args(args, random.Random(seed))
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
            header = f"### {p.hero} in {p.place} with {p.task}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()

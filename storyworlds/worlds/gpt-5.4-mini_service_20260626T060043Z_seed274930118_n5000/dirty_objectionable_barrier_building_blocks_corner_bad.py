#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260626T060043Z_seed274930118_n5000/dirty_objectionable_barrier_building_blocks_corner_bad.py
================================================================================

A standalone storyworld for a small Adventure-style building-blocks tale.

Premise:
- A child plays in the building blocks corner and builds a barrier.
- Another child thinks the barrier is rude and objectionable.
- A misunderstanding causes tension.
- A lesson is learned, but the ending is still bad: the blocks tumble and the corner gets messy.

The world is state-driven:
- physical meters track dirt, wobble, and damage
- emotional memes track joy, worry, confusion, and apology
- narration is assembled from the simulated turn of events, not from a fixed paragraph

This script intentionally keeps the domain narrow so that the story quality is
stronger than a broad, weak generator.
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
# Core domain constants
# ---------------------------------------------------------------------------

PLACE = "building blocks corner"

CHILD_NAMES = ["Milo", "Nia", "Toby", "Luna", "Pip", "Aria", "Jasper", "Ivy"]
CHILD_TYPES = ["boy", "girl"]
TRAITS = ["brave", "curious", "earnest", "lively", "careful", "inventive"]

# ---------------------------------------------------------------------------
# Entities and world model
# ---------------------------------------------------------------------------


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)
    plural: bool = False

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
class StoryParams:
    place: str
    hero_name: str
    hero_type: str
    trait: str
    seed: Optional[int] = None


class World:
    def __init__(self) -> None:
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.fired: set[str] = set()

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

    def copy(self) -> "World":
        import copy as _copy

        w = World()
        w.entities = _copy.deepcopy(self.entities)
        w.paragraphs = [[]]
        w.facts = dict(self.facts)
        w.fired = set(self.fired)
        return w


# ---------------------------------------------------------------------------
# World mechanics
# ---------------------------------------------------------------------------

THRESHOLD = 1.0


def _make_meter_box(**kwargs) -> dict[str, float]:
    box = {k: 0.0 for k in ["dirty", "wobble", "damage", "conflict"]}
    box.update(kwargs)
    return box


def _make_meme_box(**kwargs) -> dict[str, float]:
    box = {k: 0.0 for k in ["joy", "worry", "confusion", "hurt", "apology", "lesson"]}
    box.update(kwargs)
    return box


def narrate_intro(world: World, hero: Entity, friend: Entity, blocks: Entity) -> None:
    world.say(
        f"{hero.id} was a {hero.pronoun('subject')} little {hero.type} with a taste for adventure, "
        f"and {hero.pronoun('possessive')} favorite place was the {PLACE}."
    )
    world.say(
        f"There, {hero.pronoun('subject')} and {friend.id} could stack bright blocks into forts, roads, and tiny towers, "
        f"and {blocks.label} always seemed ready for one more daring idea."
    )


def build_barrier(world: World, hero: Entity, barrier: Entity, blocks: Entity) -> None:
    hero.memes["joy"] += 1
    barrier.meters["wobble"] += 0.2
    barrier.meters["dirty"] += 1
    blocks.meters["dirty"] += 1
    world.say(
        f"One afternoon, {hero.id} decided to build a barrier of blocks across the carpet."
    )
    world.say(
        f"The barrier looked bold and adventurous, like a tiny wall guarding a secret path."
    )


def misunderstanding(world: World, hero: Entity, friend: Entity, barrier: Entity) -> None:
    friend.memes["confusion"] += 1
    friend.memes["hurt"] += 1
    hero.memes["worry"] += 1
    world.say(
        f"{friend.id} stopped short and frowned."
    )
    world.say(
        f'"That looks objectionable," {friend.id} said. "It blocks the way on purpose."'
    )
    world.say(
        f"{hero.id} blinked in surprise, because {hero.pronoun('subject')} had not meant to be mean at all."
    )


def explain_intent(world: World, hero: Entity, friend: Entity, barrier: Entity) -> None:
    hero.memes["confusion"] += 1
    world.say(
        f"{hero.id} said the barrier was not meant to shut anyone out."
    )
    world.say(
        f"It was supposed to keep a rolling block car from crashing into the tallest tower."
    )


def repair_misunderstanding(world: World, hero: Entity, friend: Entity) -> None:
    friend.memes["confusion"] = max(0.0, friend.memes["confusion"] - 1.0)
    friend.memes["hurt"] = max(0.0, friend.memes["hurt"] - 1.0)
    friend.memes["joy"] += 1
    hero.memes["apology"] += 1
    hero.memes["lesson"] += 1
    world.say(
        f"Then {hero.id} took a breath and explained the plan more kindly."
    )
    world.say(
        f"{friend.id}'s face softened, because it was really a safety wall, not a rude one."
    )


def collapse_bad_ending(world: World, barrier: Entity, tower: Entity, blocks: Entity) -> None:
    barrier.meters["wobble"] += 1
    tower.meters["damage"] += 1
    blocks.meters["dirty"] += 2
    world.say(
        f"But the barrier had been built a little too high, and the bottom blocks began to slide."
    )
    world.say(
        f"With a clatter and a puff of dust, the barrier tipped over and took the tower with it."
    )
    world.say(
        f"The building blocks corner ended in a mess of dirty pieces, and the great adventure finished with a bad ending."
    )


def lesson_learned(world: World, hero: Entity, friend: Entity, barrier: Entity) -> None:
    hero.memes["lesson"] += 1
    friend.memes["lesson"] += 1
    world.say(
        f"Still, {hero.id} learned something important: when a plan can look objectionable, it helps to explain it first."
    )
    world.say(
        f"{friend.id} nodded, and both children promised to build the next barrier together from the start."
    )


def tell_story(params: StoryParams) -> World:
    world = World()
    hero = world.add(
        Entity(
            id=params.hero_name,
            kind="character",
            type=params.hero_type,
            label=params.hero_name,
            meters=_make_meter_box(),
            memes=_make_meme_box(),
        )
    )
    friend_name = next(n for n in CHILD_NAMES if n != params.hero_name)
    friend_type = "girl" if params.hero_type == "boy" else "boy"
    friend = world.add(
        Entity(
            id=friend_name,
            kind="character",
            type=friend_type,
            label=friend_name,
            meters=_make_meter_box(),
            memes=_make_meme_box(),
        )
    )
    barrier = world.add(
        Entity(
            id="barrier",
            kind="thing",
            type="blocks",
            label="block barrier",
            phrase="a block barrier",
            meters=_make_meter_box(),
            memes=_make_meme_box(),
        )
    )
    tower = world.add(
        Entity(
            id="tower",
            kind="thing",
            type="tower",
            label="tower",
            phrase="the tallest tower",
            meters=_make_meter_box(),
            memes=_make_meme_box(),
        )
    )
    blocks = world.add(
        Entity(
            id="blocks",
            kind="thing",
            type="blocks",
            label="building blocks",
            phrase="bright building blocks",
            meters=_make_meter_box(dirty=0.2),
            memes=_make_meme_box(),
            plural=True,
        )
    )

    world.facts.update(hero=hero, friend=friend, barrier=barrier, tower=tower, blocks=blocks)

    narrate_intro(world, hero, friend, blocks)
    world.para()
    build_barrier(world, hero, barrier, blocks)
    misunderstanding(world, hero, friend, barrier)
    explain_intent(world, hero, friend, barrier)
    world.para()
    repair_misunderstanding(world, hero, friend)
    collapse_bad_ending(world, barrier, tower, blocks)
    lesson_learned(world, hero, friend, barrier)

    return world


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------

SETTINGS = {
    "corner": PLACE,
}

VALID_NAMES = CHILD_NAMES
VALID_TYPES = CHILD_TYPES
VALID_TRAITS = TRAITS


# ---------------------------------------------------------------------------
# Q&A
# ---------------------------------------------------------------------------

def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero: Entity = f["hero"]
    return [
        f"Write an Adventure-style story set in the {PLACE} about {hero.id} building a dirty, objectionable barrier.",
        f"Tell a child-friendly story where a {hero.type} named {hero.id} makes a block barrier, there is a misunderstanding, and a lesson is learned.",
        f"Write a short story that ends with a bad ending in the {PLACE}, but still includes a lesson learned.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero: Entity = f["hero"]
    friend: Entity = f["friend"]
    barrier: Entity = f["barrier"]
    tower: Entity = f["tower"]
    return [
        QAItem(
            question=f"Where did {hero.id} build the barrier?",
            answer=f"{hero.id} built the barrier in the {PLACE}, among the blocks and towers.",
        ),
        QAItem(
            question=f"Why did {friend.id} think the barrier was objectionable?",
            answer=(
                f"{friend.id} thought it was objectionable because it blocked the way and looked like it was meant to keep someone out."
            ),
        ),
        QAItem(
            question=f"What did {hero.id} say the barrier was really for?",
            answer=(
                f"{hero.id} explained that the barrier was meant to protect the tall tower from a rolling block car."
            ),
        ),
        QAItem(
            question=f"What happened at the end of the story?",
            answer=(
                f"The barrier toppled, the tower got damaged, and the {PLACE} ended in a bad ending with dirty blocks everywhere."
            ),
        ),
        QAItem(
            question=f"What lesson did {hero.id} learn?",
            answer=(
                f"{hero.id} learned that plans can look objectionable if nobody explains them, so it is better to talk first."
            ),
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What are building blocks used for?",
            answer="Building blocks are used to stack, balance, and make pretend things like towers, roads, walls, and forts.",
        ),
        QAItem(
            question="What is a barrier?",
            answer="A barrier is something that stands in the way and helps block movement or protect something behind it.",
        ),
        QAItem(
            question="What does dirty mean?",
            answer="Dirty means covered with dust, mud, crumbs, or other marks that make something less clean.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    for p in sample.prompts:
        lines.append(f"- {p}")
    lines.append("")
    lines.append("== story qa ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== world qa ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------

ASP_RULES = r"""
place(corner).
hero_name(milo). hero_name(nia). hero_name(toby). hero_name(luna).
hero_name(pip). hero_name(aria). hero_name(jasper). hero_name(ivy).

hero_type(boy). hero_type(girl).
trait(brave). trait(curious). trait(earnest). trait(lively). trait(careful). trait(inventive).

setting(corner,building_blocks_corner).

story_kind(adventure).
feature(bad_ending).
feature(misunderstanding).
feature(lesson_learned).

valid_story(P,H,T) :- setting(P,building_blocks_corner), hero_name(H), hero_type(T).
"""

def asp_facts() -> str:
    import asp
    lines = [
        asp.fact("setting", "corner", "building_blocks_corner"),
        asp.fact("story_kind", "adventure"),
        asp.fact("feature", "bad_ending"),
        asp.fact("feature", "misunderstanding"),
        asp.fact("feature", "lesson_learned"),
    ]
    for n in CHILD_NAMES:
        lines.append(asp.fact("hero_name", n.lower()))
    for t in CHILD_TYPES:
        lines.append(asp.fact("hero_type", t))
    for tr in TRAITS:
        lines.append(asp.fact("trait", tr))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/3."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    clingo_set = set(asp_valid_combos())
    py_set = set(valid_combos())
    if clingo_set == py_set:
        print(f"OK: clingo gate matches valid_combos() ({len(py_set)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    print("only in clingo:", sorted(clingo_set - py_set))
    print("only in python:", sorted(py_set - clingo_set))
    return 1


# ---------------------------------------------------------------------------
# Story API
# ---------------------------------------------------------------------------

def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for name in CHILD_NAMES:
        for typ in CHILD_TYPES:
            combos.append(("corner", name.lower(), typ))
    return combos


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    place = "corner"
    if args.place and args.place not in {"corner", PLACE}:
        raise StoryError("This storyworld only supports the building blocks corner.")
    hero_name = args.name or rng.choice(CHILD_NAMES)
    hero_type = args.gender or rng.choice(CHILD_TYPES)
    trait = args.trait or rng.choice(TRAITS)
    if hero_name not in CHILD_NAMES:
        raise StoryError("Choose a name that fits the building blocks corner world.")
    if args.gender and args.gender not in CHILD_TYPES:
        raise StoryError("Gender must be boy or girl.")
    return StoryParams(place=place, hero_name=hero_name, hero_type=hero_type, trait=trait)


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


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world is not None:
        print()
        print(dump_trace(sample.world))
    if qa:
        print()
        print(format_qa(sample))


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for e in world.entities.values():
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        lines.append(f"{e.id}: {e.type} {' '.join(bits)}")
    return "\n".join(lines)


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Adventure storyworld: building blocks corner, barrier, misunderstanding, lesson learned.")
    ap.add_argument("--place", choices=["corner"], default="corner")
    ap.add_argument("--name", choices=CHILD_NAMES)
    ap.add_argument("--gender", choices=CHILD_TYPES)
    ap.add_argument("--trait", choices=TRAITS)
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


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid_story/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp

        combos = asp_valid_combos()
        print(f"{len(combos)} compatible stories:")
        for c in combos:
            print(" ", c)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)

    samples: list[StorySample] = []
    if args.all:
        for name in CHILD_NAMES:
            params = StoryParams(place="corner", hero_name=name, hero_type="girl" if name in {"Nia", "Luna", "Aria", "Ivy"} else "boy", trait="curious")
            samples.append(generate(params))
    else:
        seen = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 20, 20):
            rng = random.Random(base_seed + i)
            i += 1
            params = resolve_params(args, rng)
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
        if len(samples) > 1:
            print(f"### variant {idx + 1}")
        emit(sample, trace=args.trace, qa=args.qa)
        if idx < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()

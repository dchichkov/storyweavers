#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260626T060043Z_seed274930118_n5000/wee_yuck_dim_transformation_moral_value_fable.py
================================================================================================

A small fable-world built from the seed words "wee" and "yuck-dim".

Premise:
- A tiny creature meets something yuck-dim and wants to dismiss it.
- A wiser helper asks for patience and care.
- By a deliberate transformation, the world shifts from dull and yucky to bright and useful.
- The moral value lands as a concrete change in state: kindness improves the thing, and the hero.

The world is deliberately tiny and classical: one setting, one tension, one turn,
one resolution image that proves something changed.
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
# Small typed world model
# ---------------------------------------------------------------------------
@dataclass
class Entity:
    id: str
    kind: str = "thing"  # "character" | "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    wears: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)
    transformed: bool = False
    bright: bool = False
    clean: bool = False

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"mouse", "girl", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class Setting:
    place: str = "the mossy hollow"
    mood: str = "quiet"


@dataclass
class StoryParams:
    hero_name: str
    hero_type: str
    helper_name: str
    helper_type: str
    thing: str
    seed: Optional[int] = None


HERO_NAMES = ["Mina", "Pip", "Nell", "Toby", "Wren", "Milo"]
HERO_TYPES = ["mouse", "mouse", "mouse", "rabbit", "mouse"]
HELPER_NAMES = ["Grandmole", "Aunt Finch", "Old Toad", "Wise Turtle"]
HELPER_TYPES = ["mole", "bird", "toad", "turtle"]

THINGS = [
    ("yuck-dim stone", "a wee yuck-dim stone", "stone"),
    ("yuck-dim lantern", "a wee yuck-dim lantern", "lantern"),
    ("yuck-dim puddle", "a wee yuck-dim puddle", "puddle"),
]


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.lines: list[str] = []
        self.facts: dict[str, object] = {}

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str) -> Entity:
        return self.entities[eid]

    def say(self, text: str) -> None:
        if text:
            self.lines.append(text)

    def para(self) -> None:
        if self.lines and self.lines[-1] != "":
            self.lines.append("")

    def render(self) -> str:
        out: list[str] = []
        buf: list[str] = []
        for line in self.lines:
            if line == "":
                if buf:
                    out.append(" ".join(buf))
                    buf = []
            else:
                buf.append(line)
        if buf:
            out.append(" ".join(buf))
        return "\n\n".join(out)


# ---------------------------------------------------------------------------
# Reasonableness gate
# ---------------------------------------------------------------------------
def valid_combo(thing_key: str) -> bool:
    return thing_key in {"stone", "lantern", "puddle"}


def explain_rejection(thing_key: str) -> str:
    return f"(No story: the thing '{thing_key}' does not fit this tiny fable world.)"


# ---------------------------------------------------------------------------
# Fable narration helpers
# ---------------------------------------------------------------------------
def introduce(world: World, hero: Entity, helper: Entity, thing: Entity) -> None:
    world.say(
        f"In {world.setting.place}, a wee {hero.type} named {hero.id} found "
        f"{thing.phrase} beside the path."
    )
    world.say(f"It looked {thing.label} and sorry, as if the day had forgotten it.")


def dislike(world: World, hero: Entity, thing: Entity) -> None:
    hero.memes["sourness"] = hero.memes.get("sourness", 0.0) + 1
    world.say(
        f"{hero.id} wrinkled {hero.pronoun('possessive')} nose and called it "
        f"yuck-dim."
    )
    world.say(
        f"{hero.pronoun('subject').capitalize()} wanted to step past and leave it all alone."
    )


def teach(world: World, helper: Entity, hero: Entity, thing: Entity) -> None:
    helper.memes["wisdom"] = helper.memes.get("wisdom", 0.0) + 1
    world.say(
        f"Then {helper.id} came by and said, "
        f'"Even wee and yuck-dim things can change if we care for them."'
    )
    world.say(
        f'"Let us try one kind hand before we judge it," {helper.id} said.'
    )


def transform(world: World, hero: Entity, helper: Entity, thing: Entity) -> None:
    hero.memes["care"] = hero.memes.get("care", 0.0) + 1
    thing.meters["clean"] = thing.meters.get("clean", 0.0) + 1
    thing.bright = True
    thing.clean = True
    thing.transformed = True
    world.say(
        f"So {hero.id} fetched a little cloth, and {helper.id} showed the slow way to wipe."
    )
    world.say(
        f"The dark smudge came off, and the wee {thing.type} changed from yuck-dim to bright."
    )


def moral(world: World, hero: Entity, helper: Entity, thing: Entity) -> None:
    hero.memes["pride"] = hero.memes.get("pride", 0.0) + 1
    hero.memes["kindness"] = hero.memes.get("kindness", 0.0) + 1
    world.say(
        f"{hero.id} smiled to see {thing.phrase} shining at last."
    )
    world.say(
        f"{hero.id} learned that gentle care can make an old thing feel new."
    )
    world.say(
        f"And {helper.id} nodded, because the truest value was not in being grand, "
        f"but in being kind."
    )


# ---------------------------------------------------------------------------
# Story engine
# ---------------------------------------------------------------------------
def tell(params: StoryParams) -> World:
    setting = Setting()
    world = World(setting)

    hero = world.add(Entity(
        id=params.hero_name,
        kind="character",
        type=params.hero_type,
    ))
    helper = world.add(Entity(
        id=params.helper_name,
        kind="character",
        type=params.helper_type,
    ))
    label, phrase, thing_type = next(t for t in THINGS if t[2] == params.thing)
    thing = world.add(Entity(
        id="thing",
        kind="thing",
        type=thing_type,
        label="yuck-dim",
        phrase=phrase,
    ))

    world.facts.update(hero=hero, helper=helper, thing=thing, thing_key=params.thing)

    introduce(world, hero, helper, thing)
    world.para()
    dislike(world, hero, thing)
    teach(world, helper, hero, thing)
    world.para()
    transform(world, hero, helper, thing)
    moral(world, hero, helper, thing)

    return world


# ---------------------------------------------------------------------------
# Content registries
# ---------------------------------------------------------------------------
def generation_prompts(world: World) -> list[str]:
    hero = world.facts["hero"]
    helper = world.facts["helper"]
    thing = world.facts["thing"]
    return [
        f'Write a short fable for a small child about a wee {hero.type} and a {thing.label} thing.',
        f"Tell a gentle story where {hero.id} first calls something yuck-dim, then learns a moral value from {helper.id}.",
        f"Write a story that starts with wee curiosity, passes through transformation, and ends with kindness.",
    ]


def story_qa(world: World) -> list[QAItem]:
    hero = world.facts["hero"]
    helper = world.facts["helper"]
    thing = world.facts["thing"]
    return [
        QAItem(
            question=f"Who found the wee yuck-dim thing in the hollow?",
            answer=f"{hero.id}, a wee {hero.type}, found it first."
        ),
        QAItem(
            question=f"Who taught {hero.id} not to judge the yuck-dim thing too quickly?",
            answer=f"{helper.id} did, by telling {hero.id} to try a kind hand before judging."
        ),
        QAItem(
            question=f"What changed about the thing by the end of the story?",
            answer=f"It changed from yuck-dim to bright, clean, and useful."
        ),
        QAItem(
            question=f"What moral value did {hero.id} learn?",
            answer=f"{hero.id} learned that gentle care and kindness can transform something old into something good."
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does yuck-dim mean in this story world?",
            answer="It means something looks dull, messy, or unlovely at first, but it can still be changed with care."
        ),
        QAItem(
            question="What is transformation?",
            answer="Transformation is when something changes into a different form or state."
        ),
        QAItem(
            question="What is a moral value?",
            answer="A moral value is a good way of behaving, like kindness, patience, or honesty."
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== Prompts =="]
    for p in sample.prompts:
        lines.append(f"- {p}")
    lines.append("")
    lines.append("== Story Q&A ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== World Q&A ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
thing_ok(stone).
thing_ok(lantern).
thing_ok(puddle).

valid_story(T) :- thing_ok(T).
#show valid_story/1.
"""


def asp_facts() -> str:
    import storyworlds.asp as asp
    return "\n".join(
        asp.fact("thing_ok", name)
        for name in ["stone", "lantern", "puddle"]
    )


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import storyworlds.asp as asp
    model = asp.one_model(asp_program("#show valid_story/1."))
    asp_set = set(asp.atoms(model, "valid_story"))
    py_set = {(t,) for t in ["stone", "lantern", "puddle"] if valid_combo(t)}
    if asp_set == py_set:
        print(f"OK: clingo gate matches python gate ({len(py_set)} valid things).")
        return 0
    print("MISMATCH between ASP and Python gates:")
    if asp_set - py_set:
        print("  only in ASP:", sorted(asp_set - py_set))
    if py_set - asp_set:
        print("  only in Python:", sorted(py_set - asp_set))
    return 1


# ---------------------------------------------------------------------------
# Standard interface
# ---------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A tiny fable world of wee things and transformation.")
    ap.add_argument("--hero-name", choices=HERO_NAMES)
    ap.add_argument("--hero-type", choices=sorted(set(HERO_TYPES)))
    ap.add_argument("--helper-name", choices=HELPER_NAMES)
    ap.add_argument("--helper-type", choices=HELPER_TYPES)
    ap.add_argument("--thing", choices=sorted({t[2] for t in THINGS}))
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
    thing = args.thing or rng.choice(["stone", "lantern", "puddle"])
    if not valid_combo(thing):
        raise StoryError(explain_rejection(thing))
    return StoryParams(
        hero_name=args.hero_name or rng.choice(HERO_NAMES),
        hero_type=args.hero_type or rng.choice(HERO_TYPES),
        helper_name=args.helper_name or rng.choice(HELPER_NAMES),
        helper_type=args.helper_type or rng.choice(HELPER_TYPES),
        thing=thing,
    )


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


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        bits = []
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        if e.transformed:
            bits.append("transformed=True")
        if e.bright:
            bits.append("bright=True")
        if e.clean:
            bits.append("clean=True")
        lines.append(f"  {e.id:8} ({e.type:8}) {' '.join(bits)}")
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


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid_story/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import storyworlds.asp as asp
        model = asp.one_model(asp_program("#show valid_story/1."))
        vals = sorted(set(asp.atoms(model, "valid_story")))
        print(f"{len(vals)} valid things:")
        for v in vals:
            print(f"  {v[0]}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        for thing in ["stone", "lantern", "puddle"]:
            params = StoryParams(
                hero_name="Mina",
                hero_type="mouse",
                helper_name="Grandmole",
                helper_type="mole",
                thing=thing,
                seed=base_seed,
            )
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

    for i, sample in enumerate(samples):
        header = ""
        if len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()

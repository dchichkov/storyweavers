#!/usr/bin/env python3
"""
storyworlds/worlds/usher_kindness_humor_slice_of_life.py
=========================================================

A small slice-of-life story world about an usher, kindness, and humor.

Premise:
- A child or young helper is an usher at a local community event.
- A tiny snag in the routine creates a little tension: the seats, signs, or
  program piles are not ready in time.
- Kindness and humor turn the problem into a warm, ordinary evening.

The world model tracks:
- physical meters: distance moved, items carried, supplies placed, seats filled
- emotional memes: worry, kindness, humor, relief, pride

This file is self-contained aside from the shared result containers, and it
optionally uses the shared ASP helper when ASP modes are requested.
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


# ---------------------------------------------------------------------------
# Domain entities
# ---------------------------------------------------------------------------
@dataclass
class Entity:
    id: str
    kind: str = "thing"  # "character" | "thing" | "place"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)
    traits: list[str] = field(default_factory=list)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "woman", "mother", "sister"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man", "father", "brother"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]


@dataclass
class Setting:
    place: str
    event: str
    indoors: bool = True


@dataclass
class StoryParams:
    place: str
    event: str
    usher_name: str
    usher_type: str
    helper_name: str
    helper_type: str
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------
SETTINGS = {
    "school": Setting(place="the school auditorium", event="spring concert", indoors=True),
    "library": Setting(place="the library hall", event="story hour", indoors=True),
    "community_center": Setting(place="the community center", event="movie night", indoors=True),
    "church_hall": Setting(place="the church hall", event="holiday recital", indoors=True),
}

NAMES = {
    "girl": ["Mia", "Lina", "Zoe", "Nora", "Ivy", "Ada"],
    "boy": ["Leo", "Ben", "Eli", "Noah", "Max", "Finn"],
}

HELPER_NAMES = {
    "girl": ["June", "Nia", "Ruby", "Poppy"],
    "boy": ["Owen", "Milo", "Sam", "Theo"],
}

TITLES = {
    "girl": "girl",
    "boy": "boy",
    "woman": "woman",
    "man": "man",
    "mother": "mom",
    "father": "dad",
}


# ---------------------------------------------------------------------------
# World model
# ---------------------------------------------------------------------------
@dataclass
class World:
    setting: Setting
    entities: dict[str, Entity] = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    facts: dict = field(default_factory=dict)

    def add(self, entity: Entity) -> Entity:
        self.entities[entity.id] = entity
        return entity

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


# ---------------------------------------------------------------------------
# Story logic
# ---------------------------------------------------------------------------
def introduce(world: World, usher: Entity, helper: Entity) -> None:
    world.say(
        f"{usher.id} was a {usher.pronoun('subject')} usher who liked making rooms feel calm and friendly."
    )
    world.say(
        f"{helper.id} helped {usher.pronoun('object')} at {world.setting.event}, and both of them liked little jokes that made people smile."
    )


def setup_event(world: World) -> None:
    world.say(
        f"That evening, {world.setting.place} was filling with neighbors, soft coats, and a stack of paper programs."
    )


def tiny_problem(world: World, usher: Entity) -> None:
    usher.memes["worry"] = usher.memes.get("worry", 0) + 1
    world.say(
        f"Then {usher.id} noticed the front row signs were mixed up, so people might sit in the wrong places."
    )
    world.say(
        f"{usher.id} felt a small flutter of worry and hurried to straighten the signs before the lights went down."
    )


def kindness_turn(world: World, usher: Entity, helper: Entity) -> None:
    usher.memes["kindness"] = usher.memes.get("kindness", 0) + 1
    helper.memes["kindness"] = helper.memes.get("kindness", 0) + 1
    world.say(
        f"{helper.id} saw the rush and quietly said, \"I can hold the programs while you fix the signs.\""
    )
    world.say(
        f"{usher.id} smiled because the offer was kind and simple, and the work suddenly felt lighter."
    )


def humor_turn(world: World, usher: Entity, helper: Entity) -> None:
    usher.memes["humor"] = usher.memes.get("humor", 0) + 1
    helper.memes["humor"] = helper.memes.get("humor", 0) + 1
    world.say(
        f"When one sign slipped sideways, {helper.id} whispered, \"That one is practicing for a dance,\" and {usher.id} laughed."
    )
    world.say(
        f"The little joke made the whole aisle less serious, and the neighbors waiting nearby started smiling too."
    )


def resolve(world: World, usher: Entity, helper: Entity) -> None:
    usher.memes["relief"] = usher.memes.get("relief", 0) + 1
    usher.memes["pride"] = usher.memes.get("pride", 0) + 1
    world.say(
        f"After that, the signs were set right, the programs were in neat piles, and people found their seats easily."
    )
    world.say(
        f"{usher.id} stood at the end of the row beside {helper.id}, feeling proud of how kindness and humor had turned a small mess into a good night."
    )


# ---------------------------------------------------------------------------
# QA helpers
# ---------------------------------------------------------------------------
def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f"Write a slice-of-life story about an usher named {f['usher'].id} who solves a small event problem with kindness and humor.",
        f"Tell a gentle story set at {world.setting.place} during {world.setting.event} where two helpers make the evening go smoothly.",
        "Write a short, child-friendly story about an usher, a small mix-up, and a funny kind fix.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    usher = f["usher"]
    helper = f["helper"]
    setting = world.setting
    return [
        QAItem(
            question=f"Who was the usher in the story?",
            answer=f"{usher.id} was the usher, and {usher.pronoun('subject')} helped guide people at {setting.event}.",
        ),
        QAItem(
            question=f"What small problem did {usher.id} notice?",
            answer="The front row signs were mixed up, so people might have sat in the wrong places.",
        ),
        QAItem(
            question=f"How did {helper.id} help {usher.id}?",
            answer=f"{helper.id} offered to hold the programs while {usher.id} fixed the signs.",
        ),
        QAItem(
            question=f"What made the story feel cheerful instead of stressful?",
            answer="A little joke about a crooked sign practicing for a dance made everyone smile.",
        ),
        QAItem(
            question=f"How did the story end?",
            answer=f"The signs were fixed, the programs were neat, and {usher.id} felt proud and relieved beside {helper.id}.",
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does an usher do?",
            answer="An usher helps people find their seats and makes an event feel organized and welcoming.",
        ),
        QAItem(
            question="Why do people use paper programs at an event?",
            answer="Programs tell people what is happening, who is performing, or what order the event will follow.",
        ),
        QAItem(
            question="Why can kindness help when something goes wrong?",
            answer="Kindness helps because a calm helpful voice can make a hard moment feel smaller and easier to fix.",
        ),
        QAItem(
            question="How can humor help during a busy moment?",
            answer="A small funny comment can help people relax and remember that a tiny mistake is not a big disaster.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== Prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
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
usher(U) :- role(U, usher).
helper(H) :- role(H, helper).
event_place(P) :- place(P).

small_problem(U) :- mixed_signs.
kind_fix(U,H) :- usheR(U), helper(H), kind_offer(H).
humor_relief(U,H) :- kind_fix(U,H), funny_line(H).
resolution(U,H) :- kind_fix(U,H), humor_relief(U,H), signs_fixed.
#show small_problem/1.
#show resolution/2.
"""

def asp_facts() -> str:
    import storyworlds.asp as asp
    lines: list[str] = []
    for pid, setting in SETTINGS.items():
        lines.append(asp.fact("place", pid))
        lines.append(asp.fact("event", pid, setting.event))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


# ---------------------------------------------------------------------------
# Core generation
# ---------------------------------------------------------------------------
def build_world(params: StoryParams) -> World:
    setting = SETTINGS[params.place]
    world = World(setting=setting)

    usher = world.add(
        Entity(
            id=params.usher_name,
            kind="character",
            type=params.usher_type,
            traits=["kind", "careful"],
        )
    )
    helper = world.add(
        Entity(
            id=params.helper_name,
            kind="character",
            type=params.helper_type,
            traits=["kind", "quick"],
        )
    )

    world.facts["usher"] = usher
    world.facts["helper"] = helper
    world.facts["params"] = params

    introduce(world, usher, helper)
    world.para()
    setup_event(world)
    tiny_problem(world, usher)
    kindness_turn(world, usher, helper)
    humor_turn(world, usher, helper)
    resolve(world, usher, helper)

    return world


def generation_params(rng: random.Random) -> StoryParams:
    place = rng.choice(list(SETTINGS))
    setting = SETTINGS[place]
    usher_type = rng.choice(["girl", "boy"])
    helper_type = rng.choice(["girl", "boy"])
    usher_name = rng.choice(NAMES[usher_type])
    helper_name = rng.choice(HELPER_NAMES[helper_type])
    if helper_name == usher_name:
        helper_name = rng.choice([n for n in HELPER_NAMES[helper_type] if n != usher_name])
    return StoryParams(
        place=place,
        event=setting.event,
        usher_name=usher_name,
        usher_type=usher_type,
        helper_name=helper_name,
        helper_type=helper_type,
    )


def generate(params: StoryParams) -> StorySample:
    world = build_world(params)
    story = world.render()
    return StorySample(
        params=params,
        story=story,
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_qa(world),
        world=world,
    )


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for e in world.entities.values():
        lines.append(
            f"{e.id}: type={e.type} meters={dict(e.meters)} memes={dict(e.memes)}"
        )
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Slice-of-life story world about an usher.")
    ap.add_argument("--place", choices=SETTINGS.keys())
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
    params = generation_params(rng)
    if args.place is not None:
        params.place = args.place
        params.event = SETTINGS[args.place].event
    return params


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world is not None:
        print(dump_trace(sample.world))
    if qa:
        print()
        print(format_qa(sample))


def _asp_available() -> bool:
    try:
        import storyworlds.asp as _  # noqa: F401
        return True
    except Exception:
        return False


def verify_asp() -> int:
    if not _asp_available():
        print("ASP helper not available.")
        return 1
    print("OK: ASP twin is present.")
    return 0


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show small_problem/1.\n#show resolution/2."))
        return
    if args.verify:
        sys.exit(verify_asp())
    if args.asp:
        print(asp_program("#show small_problem/1.\n#show resolution/2."))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        for i, place in enumerate(SETTINGS):
            params = resolve_params(argparse.Namespace(place=place), random.Random(base_seed + i))
            params.seed = base_seed + i
            samples.append(generate(params))
    else:
        for i in range(args.n):
            rng = random.Random(base_seed + i)
            params = resolve_params(args, rng)
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

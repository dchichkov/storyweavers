#!/usr/bin/env python3
"""
storyworlds/worlds/sectioned_hug_calzone_flower_field_lesson_learned.py
======================================================================

A small adventure storyworld in a flower field.

Premise:
- A child and a companion discover a warm calzone in a flower field.
- The calzone is first whole, then sectioned so it can be shared fairly.
- The child learns that a calm plan and a kind hug can turn a tense moment
  into a happy lesson learned.

This world is intentionally compact and classical:
- one setting: a flower field
- one treasured food: a calzone
- one social tension: wanting it all at once versus sharing the sections
- one resolution: a lesson learned, shown through state change
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
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "mother", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class StoryParams:
    name: str
    companion: str
    gender: str
    companion_type: str
    trait: str
    seed: Optional[int] = None


@dataclass
class World:
    setting: str = "the flower field"
    entities: dict[str, Entity] = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    facts: dict = field(default_factory=dict)

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


TRAITS = ["brave", "curious", "gentle", "lively", "spry", "cheerful"]
NAMES_GIRL = ["Mia", "Lena", "Ivy", "Nora", "June", "Ruby", "Pia", "Tess"]
NAMES_BOY = ["Eli", "Noah", "Finn", "Owen", "Jude", "Leo", "Max", "Theo"]
COMPANIONS = [("friend", "friend"), ("brother", "boy"), ("sister", "girl")]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Adventure storyworld in a flower field.")
    ap.add_argument("--name")
    ap.add_argument("--companion")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--companion-type", choices=["friend", "brother", "sister"])
    ap.add_argument("--trait", choices=TRAITS)
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
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(NAMES_GIRL if gender == "girl" else NAMES_BOY)
    comp_type = args.companion_type or rng.choice([c[0] for c in COMPANIONS])
    companion = args.companion or rng.choice(NAMES_GIRL + NAMES_BOY)
    trait = args.trait or rng.choice(TRAITS)
    return StoryParams(name=name, companion=companion, gender=gender, companion_type=comp_type, trait=trait)


def _setting_line() -> str:
    return "The flower field rolled wide under a bright sky, with daisies, clover, and tall stems swaying like little flags."


def generate_world(params: StoryParams) -> World:
    w = World()
    hero = w.add(Entity(id=params.name, kind="character", type=params.gender))
    companion_type = params.companion_type if params.companion_type != "friend" else "friend"
    friend = w.add(Entity(id=params.companion, kind="character", type=companion_type))
    calzone = w.add(Entity(
        id="calzone",
        kind="thing",
        type="food",
        label="calzone",
        phrase="a warm calzone with a golden crust",
        owner=hero.id,
        caretaker=hero.id,
    ))
    plate = w.add(Entity(
        id="plate",
        kind="thing",
        type="plate",
        label="plate",
        phrase="a small plate for sharing",
        owner=hero.id,
        caretaker=hero.id,
    ))
    w.facts.update(hero=hero, friend=friend, calzone=calzone, plate=plate, params=params)

    hero.memes["joy"] = 1
    hero.memes["curiosity"] = 1
    friend.memes["patience"] = 1

    w.say(f"{params.name} was a {params.trait} {params.gender} who loved adventures.")
    w.say(f"{params.companion} was there too, ready to wander through the flower field.")
    w.say(_setting_line())
    w.say(f"On a blanket near the blossoms sat {calzone.phrase}.")
    w.say(f"{params.name} loved the smell of the calzone and wanted to eat it at once.")

    w.para()
    w.say(f"But {params.companion} pointed to the soft crust and said it could be sectioned first.")
    calzone.meters["whole"] = 1
    calzone.memes["wanted_whole"] = 1
    hero.memes["greed"] = 1
    hero.memes["worry"] = 1
    w.say(f"{params.name} hesitated, because one big bite would leave {params.companion} with nothing.")
    w.say(f"The flower field felt quieter as the two looked at the calzone and thought about a fair way to share it.")

    w.para()
    calzone.meters["sectioned"] = 1
    calzone.meters["pieces"] = 4
    hero.memes["greed"] = 0
    hero.memes["joy"] += 1
    hero.memes["lesson_learned"] = 1
    friend.memes["trust"] = 1
    w.say(f"Then {params.name} sectioned the calzone into four neat pieces.")
    w.say(f"{params.companion} smiled, and the two shared a hug before taking a piece each.")
    w.say(
        f"By the end, {params.name} knew that a shared calzone tastes better than a rushed one, "
        f"and the flower field glowed around their happy hug."
    )
    return w


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    p: StoryParams = f["params"]
    hero: Entity = f["hero"]
    friend: Entity = f["friend"]
    calzone: Entity = f["calzone"]
    return [
        QAItem(
            question=f"Who went adventuring in the flower field with {p.name}?",
            answer=f"{p.companion} went with {p.name}, and they explored the flower field together.",
        ),
        QAItem(
            question=f"What did {p.name} want to do with the calzone at first?",
            answer=f"{p.name} wanted to eat the calzone right away before thinking about sharing.",
        ),
        QAItem(
            question="How did they make the calzone easier to share?",
            answer="They sectioned the calzone into four neat pieces so everyone could have some.",
        ),
        QAItem(
            question=f"What lesson did {p.name} learn?",
            answer=f"{p.name} learned that sharing calmly is kinder, and that a sectioned calzone can still be delicious.",
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a flower field?",
            answer="A flower field is a wide outdoor place where many flowers grow together.",
        ),
        QAItem(
            question="What does sectioned mean?",
            answer="Sectioned means cut into smaller parts so something can be shared or used more easily.",
        ),
        QAItem(
            question="What is a calzone?",
            answer="A calzone is a folded baked bread pocket filled with tasty food inside.",
        ),
        QAItem(
            question="Why can a hug help in a tense moment?",
            answer="A hug can help because it shows care, calms feelings, and reminds people they are on the same side.",
        ),
    ]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    p: StoryParams = f["params"]
    return [
        'Write a short adventure story in a flower field that includes the word "sectioned".',
        f"Tell a child-friendly adventure where {p.name} and {p.companion} find a calzone in a flower field and learn to share it.",
        'Write a gentle story with a hug, a calzone, and a lesson learned at the end.',
    ]


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world is not None:
        print("--- world trace ---")
        for ent in sample.world.entities.values():
            meters = {k: v for k, v in ent.meters.items() if v}
            memes = {k: v for k, v in ent.memes.items() if v}
            bits = []
            if meters:
                bits.append(f"meters={meters}")
            if memes:
                bits.append(f"memes={memes}")
            print(f"{ent.id}: {' '.join(bits)}")
    if qa:
        print()
        for title, items in [
            ("Story prompts", sample.prompts),
            ("Story Q&A", sample.story_qa),
            ("World Q&A", sample.world_qa),
        ]:
            print(f"== {title} ==")
            if title == "Story prompts":
                for i, p in enumerate(items, 1):
                    print(f"{i}. {p}")
            else:
                for item in items:
                    print(f"Q: {item.question}")
                    print(f"A: {item.answer}")
            print()


ASP_RULES = r"""
sectioned(X) :- piece(X), count(X, N), N >= 4.
shared(X) :- sectioned(X), hug_after(X).
lesson_learned(X) :- shared(X), fair_share(X).
"""


def asp_facts() -> str:
    import storyworlds.asp as asp
    return "\n".join([
        asp.fact("thing", "calzone"),
        asp.fact("piece", "calzone"),
        asp.fact("count", "calzone", 4),
        asp.fact("hug_after", "calzone"),
        asp.fact("fair_share", "calzone"),
    ])


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import storyworlds.asp as asp
    model = asp.one_model(asp_program("#show sectioned/1. #show shared/1. #show lesson_learned/1."))
    names = {sym.name for sym in model}
    expected = {"sectioned", "shared", "lesson_learned"}
    if names == expected:
        print("OK: ASP rules derive sectioned, shared, and lesson_learned.")
        return 0
    print(f"MISMATCH: {sorted(names)} != {sorted(expected)}")
    return 1


def generate(params: StoryParams) -> StorySample:
    world = generate_world(params)
    story = world.render()
    return StorySample(
        params=params,
        story=story,
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_qa(world),
        world=world,
    )


def build_story_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    return resolve_params(args, rng)


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show sectioned/1. #show shared/1. #show lesson_learned/1."))
        return
    if args.verify:
        sys.exit(asp_verify())

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        curated = [
            StoryParams(name="Mia", companion="Noah", gender="girl", companion_type="friend", trait="curious", seed=base_seed),
            StoryParams(name="Leo", companion="Ivy", gender="boy", companion_type="sister", trait="brave", seed=base_seed),
            StoryParams(name="Nora", companion="Jude", gender="girl", companion_type="brother", trait="gentle", seed=base_seed),
        ]
        samples = [generate(p) for p in curated]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
            params = build_story_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            sample = generate(params)
            if sample.story not in seen:
                seen.add(sample.story)
                samples.append(sample)
            i += 1

    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        header = f"### variant {i+1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i + 1 < len(samples):
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()

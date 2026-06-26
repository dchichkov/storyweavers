#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260626T060043Z_seed274930118_n5000/land_happy_ending_suspense_kindness_nursery_rhyme.py
===============================================================================================================================

A small nursery-rhyme-style story world about land, kindness, suspense, and a
happy ending.

Seed tale imagined from the prompt:
---
On a wide green land, a little child hears a tiny bell in the dark. A lost lamb
is calling from the far side of a hill. The child is afraid of the night wind,
but still goes with a warm lantern and a kind heart. The path is narrow, the
brook is cold, and the lamb is alone. At last, the child finds the lamb, shares
the light, and leads it home before the moon goes down.
"""

from __future__ import annotations

import argparse
import dataclasses
import json
import os
import random
import sys
from dataclasses import dataclass, field
from typing import Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from results import QAItem, StoryError, StorySample  # noqa: E402

THRESHOLD = 1.0
HAPPY_THRESHOLD = 1.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    location: str = ""
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "mother", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class World:
    setting: str
    entities: dict[str, Entity] = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    facts: dict = field(default_factory=dict)
    fired: set[tuple] = field(default_factory=set)
    night: bool = True
    wind: bool = True

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
    hero: str
    hero_type: str
    helper: str
    seed: Optional[int] = None


PLACES = {
    "green_land": "the green land",
    "moon_hill": "the moonlit hill",
    "brook_lane": "the brook-side lane",
}

HEROES = {
    "girl": ["Mabel", "Nora", "Lily", "Penny"],
    "boy": ["Robin", "Toby", "Ben", "Milo"],
}

HELPERS = {
    "lamb": {
        "type": "lamb",
        "label": "lamb",
        "phrase": "a tiny lost lamb",
    },
    "duck": {
        "type": "duckling",
        "label": "duckling",
        "phrase": "a tiny lost duckling",
    },
}

ASP_RULES = r"""
#show valid/3.
#show valid_story/4.

valid(Place, Hero, Helper) :- place(Place), hero(Hero), helper(Helper), match(Place, Hero, Helper).
valid_story(Place, Hero, Helper, Gender) :- valid(Place, Hero, Helper), gender_ok(Hero, Gender).

match(green_land, girl, lamb).
match(green_land, boy, lamb).
match(moon_hill, girl, lamb).
match(moon_hill, boy, lamb).
match(brook_lane, girl, duck).
match(brook_lane, boy, duck).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid in PLACES:
        lines.append(asp.fact("place", pid))
    for gender, names in HEROES.items():
        for name in names:
            lines.append(asp.fact("hero", name))
            lines.append(asp.fact("gender_ok", name, gender))
    for hid in HELPERS:
        lines.append(asp.fact("helper", hid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_valid_stories() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/4."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    clingo_set = set(asp_valid_combos())
    python_set = set(valid_combos())
    if clingo_set == python_set:
        print(f"OK: clingo gate matches valid_combos() ({len(clingo_set)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    if clingo_set - python_set:
        print("  only in clingo:", sorted(clingo_set - python_set))
    if python_set - clingo_set:
        print("  only in python:", sorted(python_set - clingo_set))
    return 1


def valid_combos() -> list[tuple[str, str, str]]:
    out = []
    for place in PLACES:
        for gender, names in HEROES.items():
            for helper in HELPERS:
                if place == "brook_lane" and helper == "lamb":
                    continue
                if place in {"green_land", "moon_hill"} and helper == "duck":
                    continue
                out.append((place, gender, helper))
    return out


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Nursery-rhyme land story world.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--hero-type", choices=["girl", "boy"])
    ap.add_argument("--hero")
    ap.add_argument("--helper", choices=HELPERS)
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
    if args.place and args.hero_type and args.helper:
        if (args.place, args.hero_type, args.helper) not in valid_combos():
            raise StoryError("That combination does not make a gentle story here.")
    combos = [c for c in valid_combos()
              if (args.place is None or c[0] == args.place)
              and (args.hero_type is None or c[1] == args.hero_type)
              and (args.helper is None or c[2] == args.helper)]
    if not combos:
        raise StoryError("No valid combination matches the given options.")
    place, hero_type, helper = rng.choice(sorted(combos))
    hero = args.hero or rng.choice(HEROES[hero_type])
    return StoryParams(place=place, hero=hero, hero_type=hero_type, helper=helper)


def _setup_world(params: StoryParams) -> World:
    w = World(setting=PLACES[params.place])
    hero = w.add(Entity(id=params.hero, kind="character", type=params.hero_type, label=params.hero))
    helper_cfg = HELPERS[params.helper]
    helper = w.add(Entity(
        id=helper_cfg["label"],
        kind="character",
        type=helper_cfg["type"],
        label=helper_cfg["label"],
        phrase=helper_cfg["phrase"],
    ))
    lantern = w.add(Entity(id="lantern", type="lantern", label="lantern", phrase="a small warm lantern", owner=hero.id))
    path = w.add(Entity(id="path", type="path", label="path", phrase="a narrow path across the land"))
    hill = w.add(Entity(id="hill", type="hill", label="hill", phrase="a dark little hill"))
    hero.memes["kindness"] = 0.0
    hero.memes["suspense"] = 0.0
    hero.memes["joy"] = 0.0
    helper.memes["fear"] = 0.0
    w.facts.update(hero=hero, helper=helper, lantern=lantern, path=path, hill=hill, params=params)
    return w


def propagate(world: World) -> None:
    hero = world.facts["hero"]
    helper = world.facts["helper"]
    if hero.memes.get("kindness", 0) >= THRESHOLD and ("share", hero.id) not in world.fired:
        world.fired.add(("share", hero.id))
        hero.memes["joy"] += 1
        helper.memes["fear"] = max(0.0, helper.memes.get("fear", 0) - 1)
        world.say("Kindness made the little lantern glow a little brighter.")
    if hero.memes.get("suspense", 0) >= THRESHOLD and helper.location == "home" and ("find", helper.id) not in world.fired:
        world.fired.add(("find", helper.id))
        helper.location = "found"
        world.say("A soft call answered back from the shadow of the hill.")


def tell(params: StoryParams) -> World:
    w = _setup_world(params)
    hero = w.facts["hero"]
    helper = w.facts["helper"]

    hero.memes["kindness"] += 1
    hero.memes["suspense"] += 1
    w.say(f"On the {w.setting}, {hero.id} went trippity-trot along the land.")
    w.say(f"{hero.id} heard a tiny bell from the dark, and the night wind went whisper-whirr.")
    w.say(f"Down by the hill, {helper.pronoun().capitalize()} was all alone, and {hero.id} did not pass by.")

    w.para()
    w.say(f"{hero.id} held up {hero.pronoun('possessive')} lantern and stepped onto the narrow path.")
    w.say(f"The brook was cold, and the grass was deep, but {hero.id} was kind and brave.")
    helper.location = "hill"
    helper.memes["fear"] += 1
    propagate(w)
    w.say(f"Then the little {helper.type} blinked in the light, with a shiver and a sigh.")
    w.say(f'"Do not fret," said {hero.id}, "I have found you now."')

    w.para()
    hero.memes["joy"] += 1
    hero.memes["suspense"] = 0.0
    helper.location = "home"
    helper.memes["fear"] = 0.0
    w.say(f"{hero.id} tucked the tiny one close and led the way back over the land.")
    w.say(f"The moon smiled high, the wind grew mild, and the path felt bright again.")
    w.say(f"So the little one went home safe and sound, and {hero.id} had a happy heart.")

    w.facts["resolved"] = True
    return w


def generation_prompts(world: World) -> list[str]:
    p = world.facts["params"]
    return [
        'Write a short nursery rhyme about a child walking over the land with a warm lantern.',
        f"Tell a gentle suspense story where {p.hero} helps a lost little {p.helper} on {p.place}.",
        "Write a child-friendly rhyme with kindness, a little danger, and a happy ending.",
    ]


def story_qa(world: World) -> list[QAItem]:
    p = world.facts["params"]
    hero = world.facts["hero"]
    helper = world.facts["helper"]
    return [
        QAItem(
            question=f"Who was the story about on {PLACES[p.place]}?",
            answer=f"The story was about {hero.id}, a little {hero.type}, and a lost little {helper.type}."
        ),
        QAItem(
            question=f"What made the story feel suspenseful?",
            answer="The night was dark, the wind whispered, and the little one was alone until help came with a lantern."
        ),
        QAItem(
            question=f"How did {hero.id} show kindness?",
            answer=f"{hero.id} did not pass by, carried a warm lantern, and led the little {helper.type} home."
        ),
        QAItem(
            question="What was the happy ending?",
            answer=f"The lost little {helper.type} got home safe and sound, and {hero.id} ended with a happy heart."
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is land?",
            answer="Land is the ground we can walk on, like fields, hills, and paths."
        ),
        QAItem(
            question="Why can a lantern help at night?",
            answer="A lantern gives a little light, so it is easier to see the way in the dark."
        ),
        QAItem(
            question="What does kindness mean?",
            answer="Kindness means being gentle, helpful, and caring about someone else."
        ),
    ]


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        bits = []
        if e.location:
            bits.append(f"location={e.location}")
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        lines.append(f"  {e.id:10} ({e.type:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(world.fired)}")
    return "\n".join(lines)


def format_qa(sample: StorySample) -> str:
    out = ["== (1) Generation prompts -- asks that would produce this story =="]
    for i, p in enumerate(sample.prompts, 1):
        out.append(f"{i}. {p}")
    out.append("")
    out.append("== (2) Story questions -- answerable from the story text ==")
    for item in sample.story_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    out.append("")
    out.append("== (3) World-knowledge questions -- child level, no story needed ==")
    for item in sample.world_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    return "\n".join(out)


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world is not None:
        print(dump_trace(sample.world))
    if qa:
        print()
        print(format_qa(sample))


def generate(params: StoryParams) -> StorySample:
    world = tell(params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_qa(world),
        world=world,
    )


CURATED = [
    StoryParams(place="green_land", hero="Mabel", hero_type="girl", helper="lamb"),
    StoryParams(place="moon_hill", hero="Robin", hero_type="boy", helper="lamb"),
]


def asp_verify_stories() -> int:
    for params in CURATED:
        sample = generate(params)
        if "happy heart" not in sample.story:
            print("Story quality check failed:", params)
            return 1
    print(f"OK: generated {len(CURATED)} verification stories.")
    return 0


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid_story/4."))
        return
    if args.verify:
        sys.exit(asp_verify() or asp_verify_stories())
    if args.asp:
        triples = asp_valid_combos()
        stories = asp_valid_stories()
        print(f"{len(triples)} compatible (place, hero_type, helper) combos ({len(stories)} with gender):\n")
        for place, gender, helper in triples:
            print(f"  {place:12} {gender:8} {helper}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)
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
            header = f"### {p.hero}: {p.place} (helper: {p.helper})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()

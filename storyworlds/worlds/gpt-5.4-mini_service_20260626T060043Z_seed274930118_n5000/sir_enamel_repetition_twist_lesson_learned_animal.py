#!/usr/bin/env python3
"""
storyworlds/worlds/sir_enamel_repetition_twist_lesson_learned_animal.py
======================================================================

A compact animal-story world with a gentle repetition pattern, a small twist,
and a lesson learned. The seed words "sir" and "enamel" are built into the
premise: a proud animal helper named Sir Finch and an enamel bowl that matters
to the nest.

The world is intentionally small and constraint-checked:
- an animal wants something
- a shiny enamel item is at risk
- repetition raises tension
- a twist changes what the enamel item is for
- the lesson learned resolves the scene cleanly
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

THEMES = ("repetition", "twist", "lesson_learned")
ANIMALS = ("rabbit", "fox", "bear", "hedgehog", "squirrel", "owl")
PLACES = ("the old oak tree", "the sunlit meadow", "the riverbank", "the quiet barnyard")
OBJECTS = ("enamel bowl", "enamel cup", "enamel dish")
SNACKS = ("berries", "acorns", "seed cakes", "carrot coins")


@dataclass
class StoryParams:
    animal: str
    place: str
    object_name: str
    snack: str
    name: str
    seed: Optional[int] = None


@dataclass
class Character:
    name: str
    animal: str
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self) -> str:
        return "he"

    def poss(self) -> str:
        return "his"


@dataclass
class World:
    params: StoryParams
    hero: Character
    helper: Character
    object_clean: bool = True
    object_shared: bool = False
    repeated_calls: int = 0
    twist_discovered: bool = False
    lesson: bool = False
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    facts: dict = field(default_factory=dict)

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Animal story world with sir, enamel, repetition, twist, and lesson learned.")
    ap.add_argument("--animal", choices=ANIMALS)
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--object", dest="object_name", choices=OBJECTS)
    ap.add_argument("--snack", choices=SNACKS)
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
    animal = args.animal or rng.choice(ANIMALS)
    place = args.place or rng.choice(PLACES)
    object_name = args.object_name or rng.choice(OBJECTS)
    snack = args.snack or rng.choice(SNACKS)
    name = args.name or f"Sir {animal.title()}"
    if not name.lower().startswith("sir "):
        name = f"Sir {name}"
    return StoryParams(animal=animal, place=place, object_name=object_name, snack=snack, name=name)


def generate(params: StoryParams) -> StorySample:
    hero = Character(name=params.name, animal=params.animal, meters={"calm": 1.0}, memes={"pride": 1.0})
    helper = Character(name="Mina", animal="mouse", meters={"calm": 1.0}, memes={"kindness": 1.0})
    world = World(params=params, hero=hero, helper=helper)

    # Act 1: setup
    world.say(
        f"Sir {params.name.split(' ', 1)[1]} was a proud {params.animal} who lived near {params.place}."
    )
    world.say(
        f"Every morning, {hero.name} polished an enamel bowl until it shone, because he liked things neat and bright."
    )
    world.say(
        f"He tapped the bowl and said, 'Clean and bright, clean and bright, clean and bright.'"
    )

    # Act 2: repetition and rising tension
    world.para()
    world.say(
        f"One day, {hero.name} carried the enamel bowl to {params.place} and filled it with {params.snack}."
    )
    world.say(
        f"He set it down, checked it, and checked it again. 'Bright and safe, bright and safe, bright and safe,' he said."
    )
    world.repeated_calls += 1
    world.say(
        f"Then he checked it one more time, because he was sure that one more check would make everything perfect."
    )
    world.repeated_calls += 1
    world.say(
        f"But while he fussed, a breeze rolled through the grass and tipped the bowl a little."
    )
    world.object_clean = False

    # Act 3: twist and lesson learned
    world.para()
    world.say(
        f"That was the twist: the enamel bowl was not meant only for showing off."
    )
    world.say(
        f"Mina the mouse hurried over and said that the bowl had been set out as a shared dinner dish for the small animals."
    )
    world.twist_discovered = True
    world.say(
        f"{hero.name} blinked. The bowl was not a prize to guard forever; it was a gift to use kindly."
    )
    world.say(
        f"He lifted the bowl, rinsed it, and filled it again for everyone."
    )
    world.object_clean = True
    world.object_shared = True
    world.lesson = True
    world.say(
        f"This time he did not keep checking. He let the meal begin, and the little animals ate together in peace."
    )
    world.say(
        f"{hero.name} learned that a shiny thing is nicest when it helps others too."
    )

    world.facts = {
        "hero": hero,
        "helper": helper,
        "animal": params.animal,
        "place": params.place,
        "object_name": params.object_name,
        "snack": params.snack,
        "repeated_calls": world.repeated_calls,
        "twist_discovered": world.twist_discovered,
        "lesson": world.lesson,
    }

    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_qa(world),
        world=world,
    )


def generation_prompts(world: World) -> list[str]:
    p = world.params
    return [
        f"Write an animal story for a young child with a gentle repetition pattern, featuring Sir {p.name.split(' ', 1)[1]} and an enamel bowl.",
        f"Tell a short story where a proud {p.animal} repeats himself, discovers a twist, and learns a lesson at {p.place}.",
        f"Create a simple animal story using the words sir and enamel, ending with a kind lesson about sharing.",
    ]


def story_qa(world: World) -> list[QAItem]:
    p = world.params
    h = world.hero
    return [
        QAItem(
            question=f"Who was the story about?",
            answer=f"The story was about {h.name}, a proud {p.animal} who lived near {p.place}.",
        ),
        QAItem(
            question=f"What shiny thing did {h.name} keep checking?",
            answer=f"He kept checking an enamel {p.object_name.split(' ', 1)[-1]} so it would stay bright and neat.",
        ),
        QAItem(
            question=f"What repeated line did {h.name} say?",
            answer="He kept saying that the bowl was bright and safe, because he thought checking it again would make it perfect.",
        ),
        QAItem(
            question=f"What was the twist in the story?",
            answer=f"The twist was that the enamel bowl was meant to be a shared dinner dish, not just something to guard and polish.",
        ),
        QAItem(
            question=f"What lesson did {h.name} learn?",
            answer="He learned that a shiny thing is nicest when it helps others too.",
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is enamel?",
            answer="Enamel is a hard, smooth coating that can make dishes, cups, and bowls shiny and easy to clean.",
        ),
        QAItem(
            question="Why do animals share food in a story like this?",
            answer="They share food because sharing helps everyone get enough to eat and makes the group feel kind and happy.",
        ),
    ]


ASP_RULES = r"""
#show valid_story/4.

animal(rabbit; fox; bear; hedgehog; squirrel; owl).
place(the_oak_tree; the_sunlit_meadow; the_riverbank; the_quiet_barnyard).
object(enamel_bowl; enamel_cup; enamel_dish).
snack(berries; acorns; seed_cakes; carrot_coins).

valid_story(A, P, O, S) :- animal(A), place(P), object(O), snack(S).
"""

def asp_facts() -> str:
    import storyworlds.asp as asp
    lines = []
    for a in ANIMALS:
        lines.append(asp.fact("animal", a))
    for p in PLACES:
        lines.append(asp.fact("place", p.replace("the ", "the_").replace(" ", "_")))
    for o in OBJECTS:
        lines.append(asp.fact("object", o.replace(" ", "_")))
    for s in SNACKS:
        lines.append(asp.fact("snack", s))
    return "\n".join(lines)


def build_world(params: StoryParams) -> World:
    hero = Character(name=params.name, animal=params.animal)
    helper = Character(name="Mina", animal="mouse")
    return World(params=params, hero=hero, helper=helper)


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
    lines = ["== (1) Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== (2) Story questions ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== (3) World questions ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    lines.append(f"  hero: {world.hero.name} ({world.hero.animal})")
    lines.append(f"  helper: {world.helper.name} ({world.helper.animal})")
    lines.append(f"  object clean: {world.object_clean}")
    lines.append(f"  object shared: {world.object_shared}")
    lines.append(f"  repeated calls: {world.repeated_calls}")
    lines.append(f"  twist discovered: {world.twist_discovered}")
    lines.append(f"  lesson learned: {world.lesson}")
    return "\n".join(lines)


def asp_verify() -> int:
    return 0


CURATED = [
    StoryParams(animal="rabbit", place="the old oak tree", object_name="enamel bowl", snack="berries", name="Sir Bramble"),
    StoryParams(animal="owl", place="the quiet barnyard", object_name="enamel dish", snack="seed cakes", name="Sir Hoot"),
    StoryParams(animal="squirrel", place="the sunlit meadow", object_name="enamel cup", snack="acorns", name="Sir Nib"),
]


def resolve_valid(params: StoryParams) -> StoryParams:
    if not params.name.lower().startswith("sir "):
        params.name = f"Sir {params.name}"
    return params


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(ASP_RULES)
        return
    if args.verify:
        sys.exit(asp_verify())

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        for p in CURATED:
            samples.append(generate(resolve_valid(p)))
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 50, 50):
            seed = base_seed + i
            i += 1
            rng = random.Random(seed)
            params = resolve_params(args, rng)
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

#!/usr/bin/env python3
"""
Standalone storyworld: tar, bravery, a mystery to solve, and repetition in a nursery-rhyme style.

A tiny child-facing world:
- A small hero finds a tar stain and wants to learn where it came from.
- The trail of clues repeats in a simple pattern.
- Bravery helps the hero keep asking, keep looking, and solve the mystery.
- The ending proves what changed: the tar is understood, cleaned, and no longer scary.
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

RHYME_PATTERNS = [
    "step by step",
    "tap by tap",
    "clap by clap",
    "peek by peek",
]

PLACES = {
    "lane": {"name": "the old lane", "clue": "a dark drip on the stones", "echo": "the lane went in a little curve"},
    "dock": {"name": "the little dock", "clue": "a sticky mark on the rope", "echo": "the rope had swung by the water"},
    "shed": {"name": "the garden shed", "clue": "a black smudge on the latch", "echo": "the latch had brushed a tar can"},
    "path": {"name": "the pebble path", "clue": "a shiny blot near the gate", "echo": "the gate had scraped something black"},
}

CHARACTERS = {
    "girl": ["Mina", "Nora", "Poppy", "Lila", "Tessa"],
    "boy": ["Pip", "Finn", "Ollie", "Theo", "Robin"],
}

HELPERS = {
    "cat": "a cat with bright eyes",
    "duck": "a duck with a jaunty walk",
    "dog": "a dog with a wagging tail",
    "mouse": "a mouse in a tiny cap",
}

MYSTERY_CLOAKS = [
    "a red scarf",
    "a blue apron",
    "a yellow coat",
    "a green cap",
]

CLEANING_TOOLS = [
    "warm soap and water",
    "soft cloth and warm water",
    "gentle soap and a sponge",
]

WORLD_KNOWLEDGE = {
    "tar": [
        QAItem(
            question="What is tar?",
            answer="Tar is a thick, sticky black stuff that can smear onto things and make a mess."
        ),
        QAItem(
            question="Why is tar hard to clean?",
            answer="Tar is hard to clean because it sticks tightly, so you often need patience and soap or warm water."
        ),
    ],
    "bravery": [
        QAItem(
            question="What does bravery mean?",
            answer="Bravery means doing something even when it feels a little scary."
        ),
    ],
    "mystery": [
        QAItem(
            question="What is a mystery?",
            answer="A mystery is something you do not understand yet, so you ask questions and look for clues."
        ),
    ],
    "repetition": [
        QAItem(
            question="Why do people repeat words in a nursery rhyme?",
            answer="Repeating words makes a rhyme sound bouncy, easy to remember, and fun to say."
        ),
    ],
}


@dataclass
class StoryParams:
    place: str
    hero_name: str
    hero_gender: str
    helper: str
    cloak: str
    seed: Optional[int] = None


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)


@dataclass
class World:
    place_key: str
    entities: dict[str, Entity] = field(default_factory=dict)
    facts: dict = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Tiny tar mystery storyworld in a nursery-rhyme style.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--name")
    ap.add_argument("--helper", choices=HELPERS)
    ap.add_argument("--cloak", choices=range(len(MYSTERY_CLOAKS)), type=int)
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
    place = args.place or rng.choice(list(PLACES))
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(CHARACTERS[gender])
    helper = args.helper or rng.choice(list(HELPERS))
    cloak = MYSTERY_CLOAKS[args.cloak] if args.cloak is not None else rng.choice(MYSTERY_CLOAKS)
    return StoryParams(place=place, hero_name=name, hero_gender=gender, helper=helper, cloak=cloak)


def pronouns(gender: str) -> tuple[str, str, str]:
    if gender == "girl":
        return "she", "her", "her"
    return "he", "him", "his"


def tell(params: StoryParams) -> World:
    world = World(params.place)
    hero = world.add(Entity(id="hero", kind="character", type=params.hero_gender, label=params.hero_name))
    helper = world.add(Entity(id="helper", kind="character", type=params.helper, label=HELPERS[params.helper]))
    tar = world.add(Entity(id="tar", kind="thing", type="tar", label="tar", meters={"stick": 1.0}))
    clue = PLACES[params.place]["clue"]
    echo = PLACES[params.place]["echo"]
    sub, obj, pos = pronouns(params.hero_gender)

    world.facts.update(hero=hero, helper=helper, tar=tar, place=params.place, clue=clue, echo=echo)

    world.say(
        f"Little {params.hero_name} went tiptoe, tiptoe down {PLACES[params.place]['name']}, "
        f"where the day was quiet and the wind was low."
    )
    world.say(
        f"Then {sub} found tar, dark as night, sticky as glue, and black as a beetle's shoe."
    )
    world.say(
        f"{params.hero_name} looked and looked and looked again, for the tar was a mystery to solve."
    )
    world.para()
    world.say(
        f"Tap by tap, step by step, {params.hero_name} followed the clue: {clue}. "
        f"Tap by tap, step by step, {echo}."
    )
    world.say(
        f"A {HELPERS[params.helper]} came close and said, '{params.hero_name}, be brave, be brave; "
        f"ask one more time and the answer may wave.'"
    )
    world.say(
        f"So {params.hero_name} was brave. {sub.capitalize()} knelt down, looked near the ground, "
        f"and saw that the tar had dripped from a small cracked can."
    )
    world.para()
    world.say(
        f"Clap by clap, step by step, {params.hero_name} brought "
        f"{params.hero_name}'s {params.cloak} and {random.choice(CLEANING_TOOLS)}."
    )
    world.say(
        f"{sub.capitalize()} wiped the tar, and wiped again, and wiped again, until the sticky black spot grew small."
    )
    world.say(
        f"In the end, the mystery was solved: the cracked can was fixed, the tar was gone, and "
        f"{params.hero_name} walked home with a brave little smile."
    )

    hero.memes["brave"] = 1.0
    hero.memes["curious"] = 1.0
    tar.meters["stick"] = 0.0
    world.facts["solved"] = True
    world.facts["clean"] = True
    return world


def generation_prompts(world: World) -> list[str]:
    p = world.facts
    return [
        f"Write a nursery-rhyme style story about {p['hero'].label} finding tar and solving a mystery with bravery.",
        f"Tell a small child-friendly tale where {p['hero'].label} follows clues {p['clue']} and repeats a bouncy pattern.",
        f"Make a simple story about tar, a brave child, and a mystery that gets solved at {PLACES[p['place']]['name']}.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"].label
    place = PLACES[f["place"]]["name"]
    clue = f["clue"]
    return [
        QAItem(
            question=f"What did {hero} find at {place}?",
            answer=f"{hero} found tar, which was dark, sticky, and a little mysterious."
        ),
        QAItem(
            question=f"What helped {hero} solve the mystery?",
            answer=f"{hero} followed clues, stayed brave, and looked carefully until the answer was found."
        ),
        QAItem(
            question=f"What was the clue near {place}?",
            answer=f"The clue was {clue}."
        ),
        QAItem(
            question=f"How did the story sound as {hero} searched?",
            answer="It used repeating words like 'step by step' and 'tap by tap' to sound bouncy like a nursery rhyme."
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [item for key in ("tar", "bravery", "mystery", "repetition") for item in WORLD_KNOWLEDGE[key]]


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for ent in world.entities.values():
        bits = []
        if ent.meters:
            bits.append(f"meters={ent.meters}")
        if ent.memes:
            bits.append(f"memes={ent.memes}")
        lines.append(f"  {ent.id:8} ({ent.kind:9}) {ent.type:10} {' '.join(bits)}")
    lines.append(f"  facts: {world.facts}")
    return "\n".join(lines)


ASP_RULES = r"""
% A tar mystery is reasonable when there is a place, a clue, and bravery.
reasonable(P) :- place(P).
has_mystery(P) :- clue(P), tar(P).
solved(P) :- has_mystery(P), brave(P).
valid_story(P) :- reasonable(P), solved(P).
#show valid_story/1.
"""


def asp_facts() -> str:
    import storyworlds.asp as asp
    lines = []
    for pk in PLACES:
        lines.append(asp.fact("place", pk))
        lines.append(asp.fact("clue", pk))
    lines.append(asp.fact("tar", "yes"))
    lines.append(asp.fact("brave", "yes"))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    try:
        import storyworlds.asp as asp
    except Exception as e:
        print(f"ASP unavailable: {e}")
        return 1
    model = asp.one_model(asp_program("#show valid_story/1."))
    atoms = set(asp.atoms(model, "valid_story"))
    expected = {(pk,) for pk in PLACES}
    if atoms == expected:
        print(f"OK: ASP parity verified for {len(atoms)} places.")
        return 0
    print("MISMATCH between ASP and Python expectation.")
    print("ASP:", sorted(atoms))
    print("PY :", sorted(expected))
    return 1


def generate(params: StoryParams) -> StorySample:
    world = tell(params)
    story = world.render()
    return StorySample(
        params=params,
        story=story,
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
        print("== (1) Generation prompts ==")
        for i, p in enumerate(sample.prompts, 1):
            print(f"{i}. {p}")
        print("\n== (2) Story questions ==")
        for item in sample.story_qa:
            print(f"Q: {item.question}")
            print(f"A: {item.answer}")
        print("\n== (3) World questions ==")
        for item in sample.world_qa:
            print(f"Q: {item.question}")
            print(f"A: {item.answer}")


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
        print(sorted(asp.atoms(model, "valid_story")))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        curated = [
            StoryParams(place="lane", hero_name="Mina", hero_gender="girl", helper="cat", cloak="a red scarf"),
            StoryParams(place="dock", hero_name="Pip", hero_gender="boy", helper="duck", cloak="a blue apron"),
            StoryParams(place="shed", hero_name="Nora", hero_gender="girl", helper="mouse", cloak="a green cap"),
            StoryParams(place="path", hero_name="Finn", hero_gender="boy", helper="dog", cloak="a yellow coat"),
        ]
        samples = [generate(p) for p in curated]
    else:
        seen = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 50, 50):
            seed = base_seed + i
            i += 1
            params = resolve_params(args, random.Random(seed))
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
        header = f"### variant {i + 1}" if len(samples) > 1 and not args.all else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()

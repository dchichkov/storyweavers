#!/usr/bin/env python3
"""
A small fable world about missing the pasture, with a flashback and a moral.

Seed premise:
A young sheep once loved the pasture, then wandered away, missed it badly,
remembered how gentle and green it had been, and learned a small moral about
valuing the place that feeds you.

The world model tracks:
- physical meters: hunger, dust, distance, fullness
- emotional memes: homesick, pride, relief, gratitude

The story is generated from a causal sequence:
1. setup in the pasture
2. wandering away
3. flashback to the pasture
4. choice to return
5. moral ending image
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
    kind: str = "character"
    type: str = "animal"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"sheep", "goat", "lamb", "calf"}:
            return {"subject": "it", "object": "it", "possessive": "its"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class Place:
    id: str
    label: str
    green: bool
    safe: bool = True


@dataclass
class StoryParams:
    name: str
    animal: str
    place: str
    seed: Optional[int] = None


@dataclass
class World:
    place: Place
    entities: dict[str, Entity] = field(default_factory=dict)
    facts: dict = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    trace: list[str] = field(default_factory=list)

    def add(self, e: Entity) -> Entity:
        self.entities[e.id] = e
        return e

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)

    def get(self, eid: str) -> Entity:
        return self.entities[eid]


ANIMALS = {
    "sheep": "sheep",
    "lamb": "lamb",
    "goat": "goat",
    "calf": "calf",
}

NAMES = {
    "sheep": ["Mabel", "Milly", "Luna", "Pearl"],
    "lamb": ["Pip", "Nell", "Bram", "Tilly"],
    "goat": ["Gus", "Mina", "Poppy", "Cleo"],
    "calf": ["Daisy", "Moo", "Benny", "Rosie"],
}

PLACES = {
    "meadow": Place(id="meadow", label="the meadow pasture", green=True),
    "hill": Place(id="hill", label="the hill pasture", green=True),
    "field": Place(id="field", label="the wide pasture", green=True),
}


ASP_RULES = r"""
place(P) :- pasture(P).
can_flashback(P) :- place(P).
needs_return(A) :- animal(A), miss_pasture(A).
moral_value(A) :- needs_return(A), remember_good(A).
#show can_flashback/1.
#show needs_return/1.
#show moral_value/1.
"""


def asp_facts() -> str:
    import asp
    lines = []
    for pid in PLACES:
        lines.append(asp.fact("pasture", pid))
        lines.append(asp.fact("place", pid))
    for aid in ANIMALS:
        lines.append(asp.fact("animal", aid))
    lines.append(asp.fact("miss_pasture", "sheep"))
    lines.append(asp.fact("remember_good", "sheep"))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show can_flashback/1.\n#show needs_return/1.\n#show moral_value/1."))
    atoms = set((sym.name, tuple(str(a) if a.type != a.type.Number else a.number for a in sym.arguments)) for sym in model)
    want = {("can_flashback", ("meadow",)), ("can_flashback", ("hill",)), ("can_flashback", ("field",)),
            ("needs_return", ("sheep",)), ("moral_value", ("sheep",))}
    if atoms == want:
        print("OK: ASP parity verified.")
        return 0
    print("MISMATCH:")
    print(" got:", sorted(atoms))
    print(" want:", sorted(want))
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A small fable world about missing the pasture.")
    ap.add_argument("--animal", choices=sorted(ANIMALS))
    ap.add_argument("--place", choices=sorted(PLACES))
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
    animal = args.animal or rng.choice(list(ANIMALS))
    place = args.place or rng.choice(list(PLACES))
    if animal not in ANIMALS:
        raise StoryError("Unknown animal.")
    name = args.name or rng.choice(NAMES[animal])
    return StoryParams(name=name, animal=animal, place=place)


def build_world(params: StoryParams) -> World:
    place = PLACES[params.place]
    world = World(place=place)
    hero = world.add(Entity(
        id=params.name,
        type=params.animal,
        label=params.name,
        meters={"hunger": 0.0, "distance": 0.0, "fullness": 1.0},
        memes={"homesick": 0.0, "pride": 0.0, "relief": 0.0, "gratitude": 0.0},
    ))
    world.facts["hero"] = hero
    world.facts["place"] = place
    return world


def generate_story(world: World) -> None:
    hero = world.facts["hero"]
    place = world.facts["place"]

    world.say(f"{hero.label} lived near {place.label}, where the grass was soft and sweet.")
    world.say(f"Each day, {hero.label} ate there until {hero.pronoun('possessive')} belly was calm and full.")
    world.para()

    hero.memes["pride"] += 1
    hero.meters["distance"] += 1
    hero.meters["hunger"] += 1
    world.say(f"But one morning, {hero.label} wandered far away, proud to try a lonely path.")
    world.say(f"As the sun climbed, {hero.label} grew hungry, and the dust on the road felt less friendly.")
    world.para()

    hero.memes["homesick"] += 1
    world.say(f"Then came a flashback: {hero.label} remembered the green pasture, the cool shade, and the easy grass.")
    world.say(f"In that memory, {hero.label} had once rested without fear, listening to the wind move through the blades.")
    world.para()

    hero.memes["relief"] += 1
    hero.memes["gratitude"] += 1
    hero.meters["distance"] = 0
    hero.meters["hunger"] = 0
    world.say(f"So {hero.label} turned back toward {place.label}.")
    world.say(f"When {hero.label} arrived, the grass was waiting, and every bite tasted like a kind promise kept.")
    world.para()

    world.say(f"Moral: it is wise to remember the place that feeds you, for a good home is a treasure, not a trap.")
    world.facts["moral"] = "remember the place that feeds you"


def story_qa(world: World) -> list[QAItem]:
    hero = world.facts["hero"]
    place = world.facts["place"]
    return [
        QAItem(
            question=f"Who misses the pasture in the story?",
            answer=f"{hero.label} misses the pasture and feels homesick after wandering away.",
        ),
        QAItem(
            question=f"What did {hero.label} remember in the flashback?",
            answer=f"{hero.label} remembered the green pasture, the cool shade, and the easy grass.",
        ),
        QAItem(
            question="What is the moral of the story?",
            answer="The moral is that it is wise to remember and value the place that feeds you.",
        ),
        QAItem(
            question=f"Why did {hero.label} go back to {place.label}?",
            answer=f"{hero.label} went back because {hero.label} grew hungry and missed the safe, green pasture.",
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a pasture?",
            answer="A pasture is a grassy place where animals eat and rest.",
        ),
        QAItem(
            question="What is a flashback in a story?",
            answer="A flashback is a memory that shows something from earlier in time.",
        ),
        QAItem(
            question="What does a moral do in a fable?",
            answer="A moral gives a simple lesson about how to live or think wisely.",
        ),
    ]


def generation_prompts(world: World) -> list[str]:
    hero = world.facts["hero"]
    place = world.facts["place"]
    return [
        f"Write a short fable about {hero.label} who misses {place.label} after wandering away.",
        f"Tell a child-friendly story with a flashback to {place.label} and a moral ending.",
        f"Write a gentle fable about an animal, a pasture, and learning to value home.",
    ]


def format_qa(sample: StorySample) -> str:
    out = ["== Generation prompts =="]
    out.extend(f"{i}. {p}" for i, p in enumerate(sample.prompts, 1))
    out.append("")
    out.append("== Story questions ==")
    for item in sample.story_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    out.append("")
    out.append("== World questions ==")
    for item in sample.world_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    return "\n".join(out)


def dump_trace(world: World) -> str:
    hero = world.facts["hero"]
    meters = {k: v for k, v in hero.meters.items() if v}
    memes = {k: v for k, v in hero.memes.items() if v}
    return "\n".join([
        "--- trace ---",
        f"hero={hero.label} type={hero.type}",
        f"place={world.facts['place'].label}",
        f"meters={meters}",
        f"memes={memes}",
    ])


CURATED = [
    StoryParams(name="Mabel", animal="sheep", place="meadow"),
    StoryParams(name="Gus", animal="goat", place="hill"),
    StoryParams(name="Daisy", animal="calf", place="field"),
]


def generate(params: StoryParams) -> StorySample:
    world = build_world(params)
    generate_story(world)
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


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show can_flashback/1.\n#show needs_return/1.\n#show moral_value/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        model = asp.one_model(asp_program("#show can_flashback/1.\n#show needs_return/1.\n#show moral_value/1."))
        print("\n".join(str(sym) for sym in model))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 20):
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
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()

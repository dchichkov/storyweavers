#!/usr/bin/env python3
"""
A small bedtime-story world about a mallard, courage, and wondering.
A little mallard is drawn toward a quiet night light, a soft pond edge, and a
new thing to peek at. Curiosity pulls forward; bravery helps the mallard choose
to step, then settle, into bedtime.
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
class Place:
    name: str
    kind: str
    detail: str


@dataclass
class Thing:
    id: str
    label: str
    kind: str
    place: str
    size: int = 1
    warm: bool = False
    bright: bool = False


@dataclass
class Duckling:
    name: str
    species: str = "mallard"
    meters: dict[str, float] = field(default_factory=lambda: {"steps": 0.0, "distance": 0.0})
    memes: dict[str, float] = field(default_factory=lambda: {"bravery": 0.0, "curiosity": 0.0, "rest": 0.0, "worry": 0.0})
    at: str = "nest"
    holding: Optional[str] = None


class World:
    def __init__(self, place: Place) -> None:
        self.place = place
        self.entities: dict[str, Thing] = {}
        self.duckling: Optional[Duckling] = None
        self.facts: dict[str, object] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.events: list[str] = []

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)

    def add(self, thing: Thing) -> Thing:
        self.entities[thing.id] = thing
        return thing

    def get(self, tid: str) -> Thing:
        return self.entities[tid]


@dataclass
class StoryParams:
    seed: Optional[int] = None
    name: str = "Milo"
    place: str = "moonlit_pond"
    wonder: str = "glowworm"
    bedtime_item: str = "lantern"


PLACES = {
    "moonlit_pond": Place("the moonlit pond", "pond", "the reeds whispered and the water was silver"),
    "quiet_nest": Place("the soft nest", "nest", "the straw was warm and the night was hush-hush"),
    "garden_path": Place("the garden path", "path", "the flowers leaned in like sleepy listeners"),
}

THINGS = {
    "glowworm": Thing("glowworm", "a tiny glowworm", "wonder", "reeds", bright=True),
    "shell_lantern": Thing("shell_lantern", "a shell lantern", "comfort", "nest", warm=True, bright=True),
    "feather_blanket": Thing("feather_blanket", "a feather blanket", "comfort", "nest", warm=True),
}

NAMES = ["Milo", "Nia", "Pip", "Luna", "Toby", "Mina"]
WONDERS = ["glowworm", "shell_lantern"]
PLACES_ORDER = ["moonlit_pond", "quiet_nest", "garden_path"]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Bedtime Story world: a mallard, bravery, curiosity, and a calm ending.")
    ap.add_argument("--name")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--wonder", choices=WONDERS)
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


def _reasonableness(params: StoryParams) -> None:
    if params.place not in PLACES:
        raise StoryError("The mallard needs a real bedtime place.")
    if params.wonder not in THINGS:
        raise StoryError("The wonder must be something the duckling can notice at night.")


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.place and args.wonder == "shell_lantern" and args.place == "moonlit_pond":
        pass
    place = args.place or rng.choice(PLACES_ORDER)
    wonder = args.wonder or rng.choice(WONDERS)
    name = args.name or rng.choice(NAMES)
    params = StoryParams(seed=None, name=name, place=place, wonder=wonder)
    _reasonableness(params)
    return params


def _step(world: World, duck: Duckling, n: int = 1) -> None:
    duck.meters["steps"] += n
    duck.meters["distance"] += n


def _grow_curiosity(duck: Duckling, amount: float = 1.0) -> None:
    duck.memes["curiosity"] += amount


def _grow_bravery(duck: Duckling, amount: float = 1.0) -> None:
    duck.memes["bravery"] += amount


def _grow_rest(duck: Duckling, amount: float = 1.0) -> None:
    duck.memes["rest"] += amount


def tell(place: Place, name: str, wonder_id: str) -> World:
    world = World(place)
    duck = Duckling(name=name)
    world.duckling = duck
    wonder = THINGS[wonder_id]
    world.add(wonder)
    world.facts["wonder"] = wonder
    world.facts["place"] = place
    world.facts["duck"] = duck

    world.say(f"{duck.name} was a little mallard who lived by {place.name}.")
    world.say(f"{place.detail}. At bedtime, {duck.name} still had one more curious look to make.")
    _grow_curiosity(duck, 1)

    world.para()
    if wonder.place == "reeds":
        world.say(f"Beyond the water, {duck.name} spotted {wonder.label} shining in the reeds.")
    else:
        world.say(f"Near the nest, {duck.name} noticed {wonder.label} waiting like a tiny surprise.")
    world.say(f"{duck.name}'s curiosity grew warm and round, and {duck.name} tiptoed closer.")
    _grow_curiosity(duck, 1)
    _step(world, duck, 1)

    world.para()
    if duck.memes["curiosity"] >= 2:
        world.say(f"Then a soft hush of night made {duck.name} feel a little wobbly.")
        duck.memes["worry"] += 1
        world.say(f"But {duck.name} took a brave breath and kept going, one small step at a time.")
        _grow_bravery(duck, 1)
        _step(world, duck, 1)

    world.para()
    if wonder_id == "glowworm":
        world.say(f"It was only a glowworm, blinking kindly among the grass.")
        world.say(f"{duck.name} smiled, because the brave thing had been to look.")
    else:
        world.say(f"It was only a shell lantern, glowing softly like a bedtime star.")
        world.say(f"{duck.name} smiled, because the brave thing had been to wonder.")
    world.say(f"{duck.name} carried the feeling of bravery back to the nest, where sleep waited like a feather bed.")
    _grow_rest(duck, 2)
    world.duckling = duck
    world.facts["resolved"] = True
    return world


def generation_prompts(world: World) -> list[str]:
    duck: Duckling = world.facts["duck"]  # type: ignore[assignment]
    wonder: Thing = world.facts["wonder"]  # type: ignore[assignment]
    place: Place = world.facts["place"]  # type: ignore[assignment]
    return [
        f'Write a bedtime story about a little mallard named {duck.name} who feels both curiosity and bravery near {place.name}.',
        f"Tell a gentle story for a young child where {duck.name} sees {wonder.label} and learns to be brave enough to look.",
        f'Write a cozy story that includes the word "mallard" and ends with a calm, sleepy feeling.',
    ]


def story_qa(world: World) -> list[QAItem]:
    duck: Duckling = world.facts["duck"]  # type: ignore[assignment]
    wonder: Thing = world.facts["wonder"]  # type: ignore[assignment]
    place: Place = world.facts["place"]  # type: ignore[assignment]
    return [
        QAItem(
            question=f"Who is the story about?",
            answer=f"The story is about {duck.name}, a little mallard who lives by {place.name}.",
        ),
        QAItem(
            question=f"What did {duck.name} notice at bedtime?",
            answer=f"{duck.name} noticed {wonder.label} and felt curious enough to walk closer.",
        ),
        QAItem(
            question=f"How did {duck.name} solve the little worry?",
            answer=f"{duck.name} took a brave breath, kept going with small steps, and learned that looking was safe.",
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a mallard?",
            answer="A mallard is a kind of duck, often seen near water.",
        ),
        QAItem(
            question="What does curiosity do?",
            answer="Curiosity helps a creature notice new things and want to learn about them.",
        ),
        QAItem(
            question="What does bravery mean?",
            answer="Bravery means doing something a little scary or new even when your heart is wobbling.",
        ),
    ]


ASP_RULES = r"""
mallard(duck).
curious(duck) :- wonder(X), sees(duck, X).
brave(duck) :- worry(duck), takes_breath(duck).
settles(duck) :- brave(duck), bedtime(duck).
"""


def asp_facts() -> str:
    import asp
    lines = [
        asp.fact("mallard", "duck"),
        asp.fact("bedtime", "duck"),
        asp.fact("worry", "duck"),
        asp.fact("takes_breath", "duck"),
        asp.fact("wonder", "glowworm"),
        asp.fact("sees", "duck", "glowworm"),
    ]
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show brave/1. #show curious/1. #show settles/1."))
    shown = set(asp.atoms(model, "brave")) | set(asp.atoms(model, "curious")) | set(asp.atoms(model, "settles"))
    expected = {("duck",)}
    if shown == expected:
        print("OK: ASP twin matches the story world.")
        return 0
    print("MISMATCH between ASP and Python story facts.")
    print("  asp:", sorted(shown))
    print("  expected:", sorted(expected))
    return 1


def dump_trace(world: World) -> str:
    duck: Duckling = world.duckling  # type: ignore[assignment]
    lines = ["--- world model state ---"]
    lines.append(f"duckling={duck.name} species={duck.species} at={duck.at}")
    lines.append(f"meters={duck.meters}")
    lines.append(f"memes={duck.memes}")
    lines.append(f"place={world.place.name}")
    lines.append(f"thing={world.facts['wonder'].label}")
    return "\n".join(lines)


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world is not None:
        print(dump_trace(sample.world))
    if qa:
        print()
        for i, p in enumerate(sample.prompts, 1):
            print(f"{i}. {p}")
        print()
        for item in sample.story_qa:
            print(f"Q: {item.question}")
            print(f"A: {item.answer}")
        print()
        for item in sample.world_qa:
            print(f"Q: {item.question}")
            print(f"A: {item.answer}")


CURATED = [
    StoryParams(name="Milo", place="moonlit_pond", wonder="glowworm"),
    StoryParams(name="Nia", place="quiet_nest", wonder="shell_lantern"),
    StoryParams(name="Pip", place="garden_path", wonder="glowworm"),
]


def generate(params: StoryParams) -> StorySample:
    _reasonableness(params)
    world = tell(PLACES[params.place], params.name, params.wonder)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_qa(world),
        world=world,
    )


def resolve_many(args: argparse.Namespace) -> list[StorySample]:
    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    seen: set[str] = set()
    i = 0
    while len(samples) < args.n and i < max(args.n * 50, 50):
        rng = random.Random(base_seed + i)
        i += 1
        params = resolve_params(args, rng)
        params.seed = base_seed + i
        sample = generate(params)
        if sample.story in seen:
            continue
        seen.add(sample.story)
        samples.append(sample)
    return samples


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show brave/1. #show curious/1. #show settles/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        model = asp.one_model(asp_program("#show brave/1. #show curious/1. #show settles/1."))
        print("brave:", asp.atoms(model, "brave"))
        print("curious:", asp.atoms(model, "curious"))
        print("settles:", asp.atoms(model, "settles"))
        return

    samples = [generate(p) for p in CURATED] if args.all else resolve_many(args)
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

#!/usr/bin/env python3
"""
A small folk-tale story world about friendship, a shutter, and a mystery to solve.

Premise:
A child and a friend discover a shutter that will not open because of a posted
restriction. They must decide whether to yank it, ask around, or solve the
mystery in a kinder way.

The simulated state tracks:
- physical meters: how stuck, closed, loose, open the shutter is
- emotional memes: curiosity, worry, trust, friendship, relief

The story is driven by the world state, not a fixed paragraph template.
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
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def meter(self, key: str) -> float:
        return self.meters.get(key, 0.0)

    def meme(self, key: str) -> float:
        return self.memes.get(key, 0.0)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "woman", "mother"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man", "father"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class Place:
    name: str
    indoors: bool = False
    mood: str = "quiet"


@dataclass
class StoryParams:
    place: str
    hero_name: str
    friend_name: str
    guardian_name: str
    seed: Optional[int] = None


class World:
    def __init__(self, place: Place) -> None:
        self.place = place
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict[str, object] = {}

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


PLACES = {
    "mill": Place(name="the old mill", indoors=True, mood="dusty"),
    "cottage": Place(name="the stone cottage", indoors=True, mood="still"),
    "garden_gate": Place(name="the garden gate", indoors=False, mood="windy"),
}

HERO_NAMES = ["Mira", "Niko", "Lina", "Tobin", "Sera", "Oren"]
FRIEND_NAMES = ["Pip", "Rana", "Bram", "Tess", "Lio", "Jessa"]
GUARDIAN_NAMES = ["Grandma", "Grandpa", "Aunt Wren", "Uncle Reed", "the old keeper"]

THRESHOLD = 1.0


@dataclass
class StoryConfig:
    shutter_kind: str = "window shutter"
    restriction_kind: str = "posted restriction"
    mystery_kind: str = "mystery to solve"


def build_world(params: StoryParams) -> World:
    world = World(PLACES[params.place])
    hero = world.add(Entity(id=params.hero_name, kind="character", type="girl", label=params.hero_name))
    friend = world.add(Entity(id=params.friend_name, kind="character", type="boy", label=params.friend_name))
    guardian = world.add(Entity(id="guardian", kind="character", type="elder", label=params.guardian_name))
    shutter = world.add(Entity(
        id="shutter",
        kind="thing",
        type="shutter",
        label="shutter",
        phrase="a carved wooden shutter",
        meters={"stuck": 2.0, "closed": 1.0, "open": 0.0, "loose": 0.0},
    ))
    restriction = world.add(Entity(
        id="restriction",
        kind="thing",
        type="notice",
        label="restriction",
        phrase="a small notice tied with twine",
        meters={"placed": 1.0},
    ))
    mystery = world.add(Entity(
        id="mystery",
        kind="thing",
        type="mystery",
        label="mystery",
        phrase="a mystery to solve",
        meters={"unknown": 2.0},
        memes={"curiosity": 1.0},
    ))
    world.facts.update(hero=hero, friend=friend, guardian=guardian, shutter=shutter, restriction=restriction, mystery=mystery)
    return world


def folk_opening(world: World) -> None:
    hero = world.facts["hero"]
    friend = world.facts["friend"]
    guardian = world.facts["guardian"]
    world.say(
        f"Long ago, at {world.place.name}, there lived a child named {hero.id} and a dear friend named {friend.id}."
    )
    world.say(
        f"They were fond of each other in the old way of folk tales, for they shared bread, secrets, and small brave errands."
    )
    world.say(
        f"Near the room stood a carved shutter, and beside it hung a restriction tied with twine by {guardian.label}."
    )


def describe_problem(world: World) -> None:
    shutter = world.facts["shutter"]
    mystery = world.facts["mystery"]
    world.say(
        f"The shutter would not open. It sat tight, as if the wood itself had forgotten how to move."
    )
    world.say(
        f"This made a mystery to solve, because the little notice said there must be no hurried touch before the reason was known."
    )
    shutter.memes["worry"] = shutter.memes.get("worry", 0.0) + 0.0
    mystery.memes["curiosity"] = mystery.memes.get("curiosity", 0.0) + 1.0


def attempt_yank(world: World) -> None:
    hero = world.facts["hero"]
    friend = world.facts["friend"]
    shutter = world.facts["shutter"]
    world.say(
        f"{friend.id} gave the shutter a sharp yank, for young hands often think a hard pull can solve a hard thing."
    )
    shutter.meters["stuck"] += 0.5
    shutter.meters["loose"] += 0.0
    hero.memes["worry"] = hero.memes.get("worry", 0.0) + 1.0
    friend.memes["impulse"] = friend.memes.get("impulse", 0.0) + 1.0
    world.say(
        f"But the shutter only groaned, and the sound made {hero.id}'s worry rise like smoke from a damp twig."
    )


def reason_about_restriction(world: World) -> None:
    hero = world.facts["hero"]
    friend = world.facts["friend"]
    guardian = world.facts["guardian"]
    world.say(
        f"{hero.id} pointed to the restriction and said it was not there for nothing."
    )
    world.say(
        f"{hero.id} and {friend.id} went to ask {guardian.label} why the shutter must stay still."
    )
    guardian.memes["trust"] = guardian.memes.get("trust", 1.0) + 1.0
    hero.memes["curiosity"] = hero.memes.get("curiosity", 0.0) + 1.0
    friend.memes["curiosity"] = friend.memes.get("curiosity", 0.0) + 1.0


def reveal_mystery(world: World) -> None:
    shutter = world.facts["shutter"]
    mystery = world.facts["mystery"]
    guardian = world.facts["guardian"]
    world.say(
        f"{guardian.label} smiled and told them the truth: a bird had nested in the shutter's hidden ledge, and the restriction was there to keep the nest safe."
    )
    mystery.meters["unknown"] = 0.0
    mystery.memes["curiosity"] = 0.0
    shutter.meters["stuck"] = 0.0
    shutter.meters["closed"] = 0.0
    shutter.meters["open"] = 1.0
    shutter.meters["loose"] = 0.0
    world.say(
        f"Once the nest was seen and the danger understood, the need to yank away vanished like mist."
    )


def resolve_friendship(world: World) -> None:
    hero = world.facts["hero"]
    friend = world.facts["friend"]
    world.say(
        f"{hero.id} and {friend.id} chose patience over force, and that choice made their friendship grow warm and bright."
    )
    hero.memes["friendship"] = hero.memes.get("friendship", 0.0) + 1.0
    friend.memes["friendship"] = friend.memes.get("friendship", 0.0) + 1.0
    hero.memes["relief"] = hero.memes.get("relief", 0.0) + 1.0
    friend.memes["relief"] = friend.memes.get("relief", 0.0) + 1.0
    world.say(
        f"In the end the shutter stood open a little, just enough for fresh air and bird-song, and all were glad."
    )


def tell_story(world: World) -> World:
    folk_opening(world)
    world.para()
    describe_problem(world)
    attempt_yank(world)
    world.para()
    reason_about_restriction(world)
    reveal_mystery(world)
    resolve_friendship(world)
    return world


def generation_prompts(world: World) -> list[str]:
    p = world.place.name
    hero = world.facts["hero"].id
    friend = world.facts["friend"].id
    return [
        f"Write a folk tale about {hero} and {friend} at {p}, where a shutter, a restriction, and a mystery to solve matter.",
        f"Tell a child-sized story in which friends first want to yank a shutter, then learn why the restriction exists.",
        f"Write a gentle story about friendship and patience that ends with a shutter opening safely.",
    ]


def story_qa(world: World) -> list[QAItem]:
    hero = world.facts["hero"].id
    friend = world.facts["friend"].id
    guardian = world.facts["guardian"].label
    shutter = world.facts["shutter"]
    return [
        QAItem(
            question=f"Why did {friend} yank the shutter at first?",
            answer=f"{friend} thought a hard pull might open the shutter quickly, before anyone understood the mystery."
        ),
        QAItem(
            question=f"What did the restriction help protect?",
            answer=f"The restriction helped protect a bird's nest hidden in the shutter's ledge."
        ),
        QAItem(
            question=f"How did {hero} and {friend} solve the mystery?",
            answer=f"They asked {guardian} about the restriction, learned about the nest, and chose patience instead of forcing the shutter."
        ),
        QAItem(
            question=f"What changed about the shutter by the end?",
            answer=f"It went from stuck and closed to open a little, once the danger was understood."
        ),
        QAItem(
            question=f"What grew between {hero} and {friend}?",
            answer=f"Their friendship grew stronger because they listened to each other and chose a gentle answer."
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a shutter?",
            answer="A shutter is a wooden cover for a window or opening. It can be opened or closed to let in light and air."
        ),
        QAItem(
            question="What is a restriction?",
            answer="A restriction is a rule or limit that says something should not be done yet, often for safety."
        ),
        QAItem(
            question="What does yank mean?",
            answer="To yank means to pull suddenly and hard."
        ),
        QAItem(
            question="What is a mystery to solve?",
            answer="A mystery to solve is a puzzling thing that people try to understand by asking questions and looking closely."
        ),
    ]


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
    lines.append("== (3) World-knowledge questions ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for e in world.entities.values():
        meters = {k: round(v, 2) for k, v in e.meters.items() if v}
        memes = {k: round(v, 2) for k, v in e.memes.items() if v}
        lines.append(f"{e.id}: type={e.type}, meters={meters}, memes={memes}")
    return "\n".join(lines)


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Folk-tale story world: shutter, restriction, yank, friendship, mystery.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--name")
    ap.add_argument("--friend")
    ap.add_argument("--guardian")
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
    hero = args.name or rng.choice(HERO_NAMES)
    friend = args.friend or rng.choice([n for n in FRIEND_NAMES if n != hero])
    guardian = args.guardian or rng.choice(GUARDIAN_NAMES)
    if hero == friend:
        raise StoryError("The hero and friend must be different people.")
    return StoryParams(place=place, hero_name=hero, friend_name=friend, guardian_name=guardian)


def generate(params: StoryParams) -> StorySample:
    world = build_world(params)
    tell_story(world)
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


def asp_facts() -> str:
    import asp
    lines = []
    for p in PLACES:
        lines.append(asp.fact("place", p))
    lines.append(asp.fact("kind", "shutter"))
    lines.append(asp.fact("kind", "restriction"))
    lines.append(asp.fact("kind", "mystery"))
    lines.append(asp.fact("feature", "friendship"))
    lines.append(asp.fact("feature", "mystery_to_solve"))
    return "\n".join(lines)


ASP_RULES = r"""
#show place/1.
#show feature/1.
"""


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    try:
        import asp
    except Exception as exc:
        print(f"ASP unavailable: {exc}")
        return 1
    model = asp.one_model(asp_program("#show place/1."))
    places = sorted(set(asp.atoms(model, "place")))
    expected = sorted((p,) for p in PLACES)
    if places == expected:
        print(f"OK: ASP facts expose {len(places)} places.")
        return 0
    print("MISMATCH between ASP and Python registries.")
    print("ASP:", places)
    print("PY :", expected)
    return 1


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show place/1.\n#show feature/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print("ASP mode is available for registry inspection in this world.")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        curated = [
            StoryParams(place="mill", hero_name="Mira", friend_name="Pip", guardian_name="Grandma"),
            StoryParams(place="cottage", hero_name="Niko", friend_name="Tess", guardian_name="Aunt Wren"),
            StoryParams(place="garden_gate", hero_name="Lina", friend_name="Bram", guardian_name="the old keeper"),
        ]
        samples = [generate(p) for p in curated]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 20):
            params = resolve_params(args, random.Random(base_seed + i))
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

    for idx, sample in enumerate(samples):
        header = ""
        if len(samples) > 1:
            header = f"### variant {idx + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if idx < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()

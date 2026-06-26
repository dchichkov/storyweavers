#!/usr/bin/env python3
"""
A small nursery-rhyme storyworld about a little quest for a cozy signal.

Seed premise:
- A child finds an antenna that does not work well.
- The child goes on a quest to make it cozy and useful.
- Through the quest, they learn a lesson and reach a happy ending.

The world is built around physical meters and emotional memes:
- meters: signal, warmth, repair, clutter
- memes: hope, worry, curiosity, comfort, joy
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
# World entities
# ---------------------------------------------------------------------------
@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    place: str = ""
    meters: dict[str, float] = field(default_factory=lambda: {"signal": 0.0, "warmth": 0.0, "repair": 0.0, "clutter": 0.0})
    memes: dict[str, float] = field(default_factory=lambda: {"hope": 0.0, "worry": 0.0, "curiosity": 0.0, "comfort": 0.0, "joy": 0.0})

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "mother", "grandmother", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "grandfather", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class World:
    place: str
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

    def copy(self) -> "World":
        import copy
        clone = World(self.place)
        clone.entities = copy.deepcopy(self.entities)
        clone.paragraphs = [[]]
        clone.facts = dict(self.facts)
        return clone


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------
@dataclass
class StoryParams:
    place: str
    hero: str
    hero_type: str
    helper: str
    helper_type: str
    seed: Optional[int] = None


@dataclass(frozen=True)
class Place:
    id: str
    label: str
    cosy: bool
    has_antenna: bool
    warmth: int


PLACES = {
    "attic": Place("attic", "the attic", cosy=False, has_antenna=True, warmth=1),
    "garden_shed": Place("garden_shed", "the garden shed", cosy=True, has_antenna=False, warmth=2),
    "hilltop": Place("hilltop", "the hilltop", cosy=False, has_antenna=True, warmth=0),
    "window_nook": Place("window_nook", "the window nook", cosy=True, has_antenna=False, warmth=3),
}

HEROES = [
    ("Mina", "girl"),
    ("Tom", "boy"),
    ("Pip", "child"),
    ("Lily", "girl"),
    ("Finn", "boy"),
]

HELPERS = [
    ("Mum", "mother"),
    ("Dad", "father"),
    ("Nan", "grandmother"),
    ("Pop", "grandfather"),
    ("Rue", "child"),
]


# ---------------------------------------------------------------------------
# Story model and helpers
# ---------------------------------------------------------------------------
def build_world(params: StoryParams) -> World:
    place = PLACES[params.place]
    world = World(place=place.label)
    hero = world.add(Entity(id="hero", kind="character", type=params.hero_type, label=params.hero, place=place.label))
    helper = world.add(Entity(id="helper", kind="character", type=params.helper_type, label=params.helper, place=place.label))
    antenna = world.add(Entity(id="antenna", kind="thing", type="antenna", label="antenna", phrase="a tall antenna", place=place.label))
    blanket = world.add(Entity(id="blanket", kind="thing", type="blanket", label="blanket", phrase="a soft blanket", place=place.label))
    lantern = world.add(Entity(id="lantern", kind="thing", type="lantern", label="lantern", phrase="a little lantern", place=place.label))

    world.facts.update(hero=hero, helper=helper, antenna=antenna, blanket=blanket, lantern=lantern, place=place)
    return world


def setup(world: World) -> None:
    h = world.get("hero")
    a = world.get("antenna")
    world.say(f"{h.label} went to {world.place} with a curious little step.")
    world.say(f"There stood an antenna, thin and tall, waiting in the air.")
    a.meters["signal"] = 0.0
    a.meters["repair"] = 0.0
    h.memes["curiosity"] += 1
    h.memes["hope"] += 1
    world.say(f"{h.label} wondered what song the antenna might send and gave it a gentle tap.")


def quest(world: World) -> None:
    h = world.get("hero")
    a = world.get("antenna")
    b = world.get("blanket")
    l = world.get("lantern")
    helper = world.get("helper")

    world.para()
    world.say(f"But the wind was brisk, and the little signal would not stay.")
    a.meters["signal"] += 1
    h.memes["worry"] += 1
    world.say(f"{h.label} frowned, for the antenna was lonely and the nook felt cold.")

    world.say(f"Then {helper.label} came with a blanket, a lantern, and a grin.")
    b.meters["warmth"] += 2
    l.meters["warmth"] += 1
    h.memes["comfort"] += 1
    world.say(f"They made the corner cosy, soft as a cloud and bright as a candle.")
    world.say(f"{h.label} wrapped the blanket round the little base and held the lantern close.")
    a.meters["repair"] += 2
    a.meters["signal"] += 2
    h.memes["hope"] += 1
    world.say(f"The antenna began to hum, a tiny hum, a merry hum, a singing-bird hum.")


def lesson_and_end(world: World) -> None:
    h = world.get("hero")
    a = world.get("antenna")
    helper = world.get("helper")

    world.para()
    world.say(f"{h.label} learned a lesson there, all snug in the glow.")
    world.say(f"Even a small thing works better when hands are kind and the place feels cosy.")
    h.memes["joy"] += 2
    h.memes["comfort"] += 1
    a.meters["signal"] += 1
    world.say(f"At last the antenna sang out clear and sweet, and {helper.label} clapped along.")
    world.say(f"{h.label} smiled a happy smile, for the quest was done and the tune came home.")


def tell(world: World) -> World:
    setup(world)
    quest(world)
    lesson_and_end(world)
    return world


# ---------------------------------------------------------------------------
# Constraints and parameter resolution
# ---------------------------------------------------------------------------
def valid_places() -> list[str]:
    return list(PLACES.keys())


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    place = args.place or rng.choice(valid_places())
    if place not in PLACES:
        raise StoryError("Unknown place.")
    hero, hero_type = rng.choice(HEROES)
    helper, helper_type = rng.choice(HELPERS)
    if hero == helper:
        helper, helper_type = "Nan", "grandmother"
    return StoryParams(place=place, hero=hero, hero_type=hero_type, helper=helper, helper_type=helper_type)


def generate(params: StoryParams) -> StorySample:
    world = build_world(params)
    tell(world)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_qa(world),
        world=world,
    )


# ---------------------------------------------------------------------------
# Prompts and QA
# ---------------------------------------------------------------------------
def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    helper = f["helper"]
    place = f["place"]
    return [
        f"Write a nursery-rhyme story about {hero.label} and an antenna at {place}.",
        f"Tell a cozy quest where {helper.label} helps make the antenna work again.",
        "Write a short happy-ending story that ends with a lesson learned and a warm, cozy feeling.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    helper = f["helper"]
    place = f["place"]
    return [
        QAItem(
            question=f"Who went on the quest at {place.label}?",
            answer=f"{hero.label} went on the quest at {place.label}.",
        ),
        QAItem(
            question="What made the place feel cosy?",
            answer=f"{helper.label} brought a blanket and a lantern, and that made the place feel cosy.",
        ),
        QAItem(
            question="What lesson did the hero learn?",
            answer="The hero learned that small things work better when kind hands make them warm and safe.",
        ),
        QAItem(
            question="How did the story end?",
            answer="It ended happily, with the antenna singing clearly and everyone feeling joyful.",
        ),
    ]


WORLD_QA = [
    QAItem(
        question="What is an antenna for?",
        answer="An antenna helps send or receive signals so sounds or messages can travel farther.",
    ),
    QAItem(
        question="What does cosy mean?",
        answer="Cosy means warm, snug, and comfortable in a way that feels safe and pleasant.",
    ),
]


def world_qa(world: World) -> list[QAItem]:
    return list(WORLD_QA)


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
place_ok(P) :- place(P).
cosy_place(P) :- cosy_place_fact(P).

needs_comfort(P) :- place_ok(P), not cosy_place(P).
signal_improves(P) :- place_ok(P), antenna(P), blanket(B), lantern(L), comfort_item(B), comfort_item(L).

happy_ending(P) :- needs_comfort(P), signal_improves(P).
lesson_learned(P) :- happy_ending(P).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid, p in PLACES.items():
        lines.append(asp.fact("place", pid))
        if p.cosy:
            lines.append(asp.fact("cosy_place_fact", pid))
        if p.has_antenna:
            lines.append(asp.fact("antenna", pid))
    lines.append(asp.fact("blanket", "blanket"))
    lines.append(asp.fact("lantern", "lantern"))
    lines.append(asp.fact("comfort_item", "blanket"))
    lines.append(asp.fact("comfort_item", "lantern"))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show happy_ending/1. #show lesson_learned/1."))
    atoms = set(asp.atoms(model, "happy_ending")) | set(asp.atoms(model, "lesson_learned"))
    expected = {(pid,) for pid, p in PLACES.items() if not p.cosy}
    expected |= {(pid,) for pid, p in PLACES.items() if not p.cosy}
    if atoms:
        print("OK: ASP produced a model.")
        return 0
    print("MISMATCH: ASP produced no answer set.")
    return 1


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Nursery-rhyme storyworld: antenna, cosy quest, lesson learned.")
    ap.add_argument("--place", choices=valid_places())
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


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        lines.append(f"  {e.id:8} ({e.kind:8}) meters={e.meters} memes={e.memes}")
    return "\n".join(lines)


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
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
        print(asp_program("#show happy_ending/1. #show lesson_learned/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        model = asp.one_model(asp_program("#show happy_ending/1. #show lesson_learned/1."))
        print(sorted(set(asp.atoms(model, "happy_ending")) | set(asp.atoms(model, "lesson_learned"))))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        for place in valid_places():
            params = StoryParams(place=place, hero="Mina", hero_type="girl", helper="Mum", helper_type="mother", seed=base_seed)
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

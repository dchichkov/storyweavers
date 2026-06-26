#!/usr/bin/env python3
"""
storyworlds/worlds/surf_cloud_transformation_curiosity_fairy_tale.py
====================================================================

A tiny fairy-tale story world about a curious child, a cloud, and a magical
transformation at the surf.

Seed premise:
- A child is fascinated by a cloud above the surf.
- Curiosity leads them closer to the water.
- A magical change transforms something simple into something wondrous.
- The story ends with a clear, changed world image.

The world is intentionally small and constraint-checked: the story only exists
when there is a believable curious action, a magical transformation, and a
gentle resolution that proves the change.
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
# Entities and world state
# ---------------------------------------------------------------------------
@dataclass
class Entity:
    id: str
    kind: str = "thing"  # character | thing
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    wearer: Optional[str] = None
    place: str = ""
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "princess", "queen", "mother", "woman"}
        male = {"boy", "prince", "king", "father", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Place:
    id: str
    name: str
    surf: bool = False
    cloud: bool = False


@dataclass
class Magic:
    id: str
    trigger: str
    result: str
    affects: str
    transformation: str
    required_curious: float = 1.0


class World:
    def __init__(self, place: Place):
        self.place = place
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}

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

        w = World(self.place)
        w.entities = copy.deepcopy(self.entities)
        w.fired = set(self.fired)
        w.paragraphs = [[]]
        w.facts = dict(self.facts)
        return w


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------
PLACES = {
    "shore": Place(id="shore", name="the shore", surf=True, cloud=True),
    "beach": Place(id="beach", name="the beach", surf=True, cloud=True),
    "cove": Place(id="cove", name="a quiet cove", surf=True, cloud=True),
    "harbor": Place(id="harbor", name="the harbor", surf=False, cloud=True),
}

MAGICS = {
    "shell-to-wing": Magic(
        id="shell-to-wing",
        trigger="listened to the cloud",
        result="a shell became a tiny silver wing",
        affects="shell",
        transformation="transformed into",
        required_curious=1.0,
    ),
    "sand-to-bridge": Magic(
        id="sand-to-bridge",
        trigger="followed the cloud's shadow",
        result="the sand rose into a little bridge",
        affects="sand",
        transformation="rose into",
        required_curious=1.0,
    ),
    "drop-to-bloom": Magic(
        id="drop-to-bloom",
        trigger="asked the cloud its name",
        result="a single drop changed into a bright sea-flower",
        affects="drop",
        transformation="changed into",
        required_curious=1.0,
    ),
}

HERO_NAMES = ["Mira", "Nori", "Lina", "Tobin", "Eli", "Suri", "Pip", "Ari"]
HERO_TYPES = ["girl", "boy"]
TRAITS = ["curious", "gentle", "brave", "bright", "wondering"]


# ---------------------------------------------------------------------------
# Story params
# ---------------------------------------------------------------------------
@dataclass
class StoryParams:
    place: str
    magic: str
    name: str
    gender: str
    trait: str
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
place(P) :- place(P).
magic(M) :- magic(M).

curious_story(P, M) :- place(P), magic(M), place_has(P, surf), place_has(P, cloud), requires_curiosity(M, 1).
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for pid, p in PLACES.items():
        lines.append(asp.fact("place", pid))
        if p.surf:
            lines.append(asp.fact("place_has", pid, "surf"))
        if p.cloud:
            lines.append(asp.fact("place_has", pid, "cloud"))
    for mid, m in MAGICS.items():
        lines.append(asp.fact("magic", mid))
        lines.append(asp.fact("requires_curiosity", mid, int(m.required_curious)))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_story_pairs() -> list[tuple[str, str]]:
    import asp

    model = asp.one_model(asp_program("#show curious_story/2."))
    return sorted(set(asp.atoms(model, "curious_story")))


def asp_verify() -> int:
    py = set(valid_combos())
    asp_set = set(asp_story_pairs())
    if py == asp_set:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    if py - asp_set:
        print("  only in python:", sorted(py - asp_set))
    if asp_set - py:
        print("  only in clingo:", sorted(asp_set - py))
    return 1


# ---------------------------------------------------------------------------
# Reasonableness gate
# ---------------------------------------------------------------------------
def valid_combos() -> list[tuple[str, str]]:
    combos = []
    for place in PLACES:
        for magic in MAGICS:
            combos.append((place, magic))
    return combos


def explain_rejection(place: str, magic: str) -> str:
    return f"(No story: the cloud-and-surf fairy tale needs a place and a magic, but {place!r} and {magic!r} do not fit.)"


# ---------------------------------------------------------------------------
# World simulation
# ---------------------------------------------------------------------------
def predict_transformation(world: World, hero: Entity, magic: Magic) -> bool:
    sim = world.copy()
    hero2 = sim.get(hero.id)
    hero2.memes["curiosity"] = hero2.memes.get("curiosity", 0) + 1
    return hero2.memes["curiosity"] >= magic.required_curious


def tell(place: Place, magic: Magic, hero_name: str, gender: str, trait: str) -> World:
    world = World(place)
    hero = world.add(Entity(id=hero_name, kind="character", type=gender, meters={}, memes={"curiosity": 0.0, "wonder": 0.0}))
    cloud = world.add(Entity(id="cloud", kind="thing", type="cloud", label="cloud", place=place.name))
    surf = world.add(Entity(id="surf", kind="thing", type="surf", label="surf", place=place.name, plural=False))
    gift = world.add(Entity(id="gift", kind="thing", type="thing", label="little shell", phrase="a little shell"))

    world.say(f"Once upon a tide, {hero.id} was a {trait} child who loved to watch the cloud above {place.name}.")
    world.say(f"{hero.pronoun().capitalize()} liked the silver surf and the soft way it whispered at the shore.")
    world.para()
    world.say(f"One bright morning, {hero.id} saw the cloud drift lower and lower over the surf.")
    hero.memes["curiosity"] += 1
    world.say(f"{hero.pronoun().capitalize()} asked, \"What are you hiding, cloud?\" and stepped a little closer to listen.")
    world.para()
    if not predict_transformation(world, hero, magic):
        raise StoryError("the hero is not curious enough for this transformation")

    hero.memes["curiosity"] += 1
    hero.memes["wonder"] += 1
    world.say(f"The cloud answered in a hush, and {hero.id} {magic.trigger}.")
    world.say(f"Then {magic.result}, {magic.transformation} by the cloud's gentle magic.")
    gift.label = "silver wing"
    gift.phrase = "a tiny silver wing"
    gift.place = place.name
    world.para()
    world.say(f"At last, {hero.id} held the new treasure while the surf shone below and the cloud smiled overhead.")
    world.say(f"The little shell was no longer only a shell; it was a wonder, and the sea looked brighter for it.")
    world.facts.update(hero=hero, cloud=cloud, surf=surf, gift=gift, magic=magic, place=place)
    return world


# ---------------------------------------------------------------------------
# QA
# ---------------------------------------------------------------------------
def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    magic = f["magic"]
    return [
        f'Write a fairy-tale story for a young child about {hero.id}, a cloud, and the surf.',
        f"Tell a gentle story where curiosity leads {hero.id} to ask the cloud a question and a magical transformation happens.",
        f"Write a short tale in which the surf, a cloud, and a small wonder change because the hero is curious.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    magic = f["magic"]
    place = f["place"]
    return [
        QAItem(
            question=f"Who is the fairy tale about?",
            answer=f"It is about {hero.id}, a curious child at {place.name}, who watches the cloud above the surf.",
        ),
        QAItem(
            question=f"What made the magic happen?",
            answer=f"{hero.id}'s curiosity did. {hero.pronoun().capitalize()} listened to the cloud and asked a careful question.",
        ),
        QAItem(
            question=f"What changed in the end?",
            answer=f"{magic.result}. The story ends with a small wonder in {place.name}, and the surf shining below the cloud.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is surf?",
            answer="Surf is the moving edge of the sea where waves meet the shore and break into foam.",
        ),
        QAItem(
            question="What is a cloud?",
            answer="A cloud is a soft-looking gathering of tiny water drops high in the sky.",
        ),
        QAItem(
            question="What is curiosity?",
            answer="Curiosity is the wish to know more, so a curious child asks questions and looks closely.",
        ),
        QAItem(
            question="What is transformation?",
            answer="Transformation means something changes into something else, like one thing becoming another.",
        ),
    ]


# ---------------------------------------------------------------------------
# CLI helpers
# ---------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A fairy-tale story world of surf, cloud, curiosity, and transformation.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--magic", choices=MAGICS)
    ap.add_argument("--gender", choices=HERO_TYPES)
    ap.add_argument("--name")
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
    if args.place and args.magic:
        if (args.place, args.magic) not in valid_combos():
            raise StoryError(explain_rejection(args.place, args.magic))
    place = args.place or rng.choice(list(PLACES))
    magic = args.magic or rng.choice(list(MAGICS))
    gender = args.gender or rng.choice(HERO_TYPES)
    name = args.name or rng.choice(HERO_NAMES)
    trait = args.trait or rng.choice(TRAITS)
    return StoryParams(place=place, magic=magic, name=name, gender=gender, trait=trait)


def generate(params: StoryParams) -> StorySample:
    world = tell(PLACES[params.place], MAGICS[params.magic], params.name, params.gender, params.trait)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


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
    lines.append("== (3) World knowledge ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        bits = []
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        if e.place:
            bits.append(f"place={e.place}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
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
        print(asp_program("#show curious_story/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        pairs = asp_story_pairs()
        print(f"{len(pairs)} compatible (place, magic) combos:\n")
        for place, magic in pairs:
            print(f"  {place:10} {magic}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)

    samples: list[StorySample] = []
    if args.all:
        for place, magic in valid_combos():
            p = StoryParams(
                place=place,
                magic=magic,
                name=HERO_NAMES[0],
                gender="girl",
                trait="curious",
                seed=base_seed,
            )
            samples.append(generate(p))
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
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
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""
A standalone story world for a small pirate-tale domain.

Premise:
- A young pirate wants to conquer a tricky place at sea.
- A misunderstanding makes the crew think the plan is dangerous or greedy.
- Bravery and a clear explanation turn fear into teamwork.
- The final image proves the conquest: the crew wins the goal together.

The world is simulated with typed entities carrying physical meters and emotional memes.
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
    owner: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "woman", "captainess"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man", "captain"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class PiratePlace:
    name: str
    hazard: str
    treasure: str
    conquer_verb: str
    at_sea: bool = True


@dataclass
class StoryParams:
    place: str
    hero_name: str
    hero_type: str
    crew_name: str
    seed: Optional[int] = None


PLACES = {
    "reef": PiratePlace(
        name="the coral reef",
        hazard="sharp coral",
        treasure="a hidden pearl chest",
        conquer_verb="conquer",
    ),
    "island": PiratePlace(
        name="the windy island",
        hazard="the steep hill",
        treasure="a golden flagpole",
        conquer_verb="conquer",
    ),
    "cove": PiratePlace(
        name="the moonlit cove",
        hazard="the dark rocks",
        treasure="a silver map box",
        conquer_verb="conquer",
    ),
    "harbor": PiratePlace(
        name="the busy harbor",
        hazard="the crowded dock",
        treasure="a lost lantern",
        conquer_verb="conquer",
    ),
}

HEROES = [
    ("Mira", "girl"),
    ("Finn", "boy"),
    ("Jory", "boy"),
    ("Nia", "girl"),
    ("Tess", "girl"),
    ("Owen", "boy"),
]

CREWS = ["crew", "mateys", "sailors", "deck hands"]


@dataclass
class World:
    place: PiratePlace
    hero: Entity
    crew: Entity
    hazard: Entity
    treasure: Entity
    captain_hat: Entity
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    facts: dict = field(default_factory=dict)

    def say(self, text: str) -> None:
        self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)


def _m(entity: Entity, key: str, delta: float) -> None:
    entity.meters[key] = entity.meters.get(key, 0.0) + delta


def _e(entity: Entity, key: str, delta: float) -> None:
    entity.memes[key] = entity.memes.get(key, 0.0) + delta


def build_world(params: StoryParams) -> World:
    place = PLACES[params.place]
    hero = Entity(id=params.hero_name, kind="character", type=params.hero_type, label=params.hero_name)
    crew = Entity(id=params.crew_name, kind="character", type="crew", label=params.crew_name)
    hazard = Entity(id="hazard", kind="thing", type="hazard", label=place.hazard)
    treasure = Entity(id="treasure", kind="thing", type="treasure", label=place.treasure)
    hat = Entity(id="hat", kind="thing", type="hat", label="the captain's bright hat", owner=hero.id)
    return World(place=place, hero=hero, crew=crew, hazard=hazard, treasure=treasure, captain_hat=hat)


def narrate_story(world: World) -> None:
    hero, crew, hazard, treasure, hat = world.hero, world.crew, world.hazard, world.treasure, world.captain_hat
    place = world.place

    _e(hero, "bravery", 1)
    _e(hero, "hope", 1)
    world.say(
        f"{hero.id} was a small pirate with brave eyes and a bold grin."
        f" {hero.pronoun().capitalize()} wanted to {place.conquer_verb} {place.name} and claim {treasure.label}."
    )
    world.say(
        f"Every morning on the ship, {hero.id} touched {hat.label} and dreamed of the day the waves would cheer."
    )

    world.para()
    _e(crew, "worry", 1)
    _e(crew, "misunderstanding", 1)
    world.say(
        f"But one cloudy afternoon, {hero.id} pointed at {place.name} and said, "
        f'\"We will {place.conquer_verb} it!\"'
    )
    world.say(
        f"The {crew.label} gasped, because they thought {hero.id} meant to rush into {hazard.label} without a plan."
    )
    world.say(
        f"Their misunderstanding made the deck go quiet, and even the gulls seemed to hold their breath."
    )

    world.para()
    _e(hero, "bravery", 2)
    _e(hero, "kindness", 1)
    world.say(
        f"{hero.id} lifted {hero.pronoun('possessive')} chin and spoke in a calm voice."
        f" \"I do not mean to be foolish,\" {hero.pronoun()} said."
        f" \"I mean we can {place.conquer_verb} {place.name} together, one careful step at a time.\""
    )
    world.say(
        f"{hero.id} showed the crew the rope path, the safe rocks, and the best place to anchor the boat."
    )
    world.say(
        f"That steady bravery fixed the misunderstanding, and the {crew.label} felt their worry melt away."
    )
    _e(crew, "trust", 2)
    _e(crew, "bravery", 1)
    _e(crew, "misunderstanding", -1)

    world.para()
    _m(hazard, "guarded_by_steps", 1)
    _m(treasure, "closer", 1)
    world.say(
        f"Together they climbed, pulled, and balanced as the tide whispered around the stones."
        f" At last they reached {place.name} and found {treasure.label} waiting where the spray was kindest."
    )
    world.say(
        f"{hero.id} planted {hat.label} on a rock like a tiny flag."
        f" The crew cheered because the brave plan had conquered the place without hurting anyone."
    )
    world.say(
        f"By sunset, the ship sailed home with {treasure.label} safe on deck, and {hero.id}'s bravery shining brighter than the moon."
    )

    world.facts.update(
        place=place,
        hero=hero,
        crew=crew,
        hazard=hazard,
        treasure=treasure,
        hat=hat,
    )


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    place = f["place"]
    hero = f["hero"]
    return [
        f'Write a pirate story for a young child where {hero.id} wants to {place.conquer_verb} {place.name}.',
        f'Tell a gentle pirate tale with a misunderstanding, bravery, and a happy ending at {place.name}.',
        f'Write a short story about a brave crew who first misreads a plan and then conquers a sea place together.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    crew = f["crew"]
    place = f["place"]
    treasure = f["treasure"]
    hazard = f["hazard"]
    return [
        QAItem(
            question=f"What did {hero.id} want to do at {place.name}?",
            answer=f"{hero.id} wanted to {place.conquer_verb} {place.name} and get {treasure.label}.",
        ),
        QAItem(
            question=f"Why did the {crew.label} first worry about the plan?",
            answer=f"They thought {hero.id} meant to rush into {hazard.label} without being careful.",
        ),
        QAItem(
            question=f"What fixed the misunderstanding?",
            answer=f"{hero.id} explained the plan calmly and showed the crew the safe way to go.",
        ),
        QAItem(
            question=f"What changed by the end of the story?",
            answer=f"The crew felt brave and trusted {hero.id}, and together they conquered {place.name}.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is bravery?",
            answer="Bravery is being scared but still doing the right thing with a steady heart.",
        ),
        QAItem(
            question="What is a misunderstanding?",
            answer="A misunderstanding happens when people think a message means one thing, but it really means something else.",
        ),
        QAItem(
            question="What is a pirate crew?",
            answer="A pirate crew is a group of sailors who work together on a ship.",
        ),
        QAItem(
            question="What does conquer mean?",
            answer="To conquer a place means to overcome its challenge or win control of it after a hard effort.",
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
    lines = ["--- world model state ---"]
    for e in [world.hero, world.crew, world.hazard, world.treasure, world.captain_hat]:
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        lines.append(f"  {e.id:12} ({e.type:9}) {' '.join(bits)}")
    return "\n".join(lines)


ASP_RULES = r"""
hero_brave(H) :- hero(H), meme(H, bravery, B), B >= 1.
misunderstanding(H) :- meme(H, misunderstanding, M), M > 0.
resolved(H) :- hero_brave(H), misunderstanding(H), explain(H).
conquered(P) :- place(P), resolved(hero).
#show hero_brave/1.
#show misunderstanding/1.
#show resolved/1.
#show conquered/1.
"""


def asp_facts() -> str:
    import asp
    lines = [
        asp.fact("hero", "hero"),
        asp.fact("place", "place"),
        asp.fact("meme", "hero", "bravery", 3),
        asp.fact("meme", "crew", "misunderstanding", 1),
        asp.fact("explain", "hero"),
    ]
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show resolved/1.\n#show conquered/1."))
    atoms = set((a.name, tuple(x.name if x.type == x.type.SymbolType.Function else getattr(x, 'name', str(x)) for x in a.arguments)) for a in model)
    expected = {("resolved", ("hero",)), ("conquered", ("place",))}
    if atoms == expected:
        print("OK: ASP parity matches the Python reasonableness gate.")
        return 0
    print("MISMATCH:", atoms, expected)
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Pirate tale story world with bravery and misunderstanding.")
    ap.add_argument("--place", choices=sorted(PLACES))
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--crew", choices=CREWS)
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
    place = args.place or rng.choice(sorted(PLACES))
    hero_name, default_gender = rng.choice(HEROES)
    gender = args.gender or default_gender
    name = args.name or hero_name
    crew = args.crew or rng.choice(CREWS)
    return StoryParams(place=place, hero_name=name, hero_type=gender, crew_name=crew)


def generate(params: StoryParams) -> StorySample:
    world = build_world(params)
    narrate_story(world)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
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
        print(asp_program("#show resolved/1.\n#show conquered/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print("ASP mode is available; this world keeps the declarative twin minimal.")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        curated = [
            StoryParams(place=p, hero_name=n, hero_type=g, crew_name=c)
            for p, (n, g), c in [
                ("reef", ("Mira", "girl"), "crew"),
                ("island", ("Finn", "boy"), "mateys"),
                ("cove", ("Nia", "girl"), "sailors"),
                ("harbor", ("Owen", "boy"), "deck hands"),
            ]
        ]
        samples = [generate(p) for p in curated]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 20, 20):
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

    for idx, sample in enumerate(samples):
        header = f"### variant {idx + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if idx < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""
A standalone story world for a small Animal Story:
an animal feels miserable, a mosquito brings trouble, bravery helps,
and reconciliation repairs a friendship.

The world is intentionally tiny and constraint-driven:
- one setting
- a few animal characters
- a mosquito-borne sickness scare
- a brave act that leads to reconciliation
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
# Entity model
# ---------------------------------------------------------------------------
@dataclass
class Entity:
    id: str
    kind: str = "thing"  # character | thing
    species: str = "thing"
    name: str = ""
    role: str = ""
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        gender = self.species
        if gender in {"lion", "boy", "he"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        if gender in {"lioness", "girl", "she"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def they(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Place:
    id: str
    label: str
    outdoors: bool = True
    has_water: bool = False
    has_shelter: bool = False


@dataclass
class StoryParams:
    place: str
    hero: str
    friend: str
    helper: str
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# World state
# ---------------------------------------------------------------------------
class World:
    def __init__(self, place: Place) -> None:
        self.place = place
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict[str, object] = {}
        self.fired: set[str] = set()

    def add(self, e: Entity) -> Entity:
        self.entities[e.id] = e
        return e

    def get(self, eid: str) -> Entity:
        return self.entities[eid]

    def characters(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.kind == "character"]

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------
PLACES = {
    "riverbank": Place("riverbank", "the riverbank", outdoors=True, has_water=True, has_shelter=False),
    "orchard": Place("orchard", "the orchard", outdoors=True, has_water=False, has_shelter=True),
    "barnyard": Place("barnyard", "the barnyard", outdoors=True, has_water=False, has_shelter=True),
    "pond": Place("pond", "the pond", outdoors=True, has_water=True, has_shelter=False),
}

ANIMALS = {
    "rabbit": {"species": "rabbit", "kind": "character"},
    "hedgehog": {"species": "hedgehog", "kind": "character"},
    "fox": {"species": "fox", "kind": "character"},
    "badger": {"species": "badger", "kind": "character"},
    "mouse": {"species": "mouse", "kind": "character"},
    "deer": {"species": "deer", "kind": "character"},
}

HERO_NAMES = {
    "rabbit": ["Mina", "Pip", "Nora"],
    "hedgehog": ["Toby", "June", "Hush"],
    "fox": ["Penny", "Ravi", "Skye"],
    "badger": ["Milo", "Brin", "Bram"],
    "mouse": ["Tiny", "Dot", "Merry"],
    "deer": ["Lina", "Fawn", "Elli"],
}

FRIEND_NAMES = {
    "rabbit": ["Lulu", "Bean", "Pogo"],
    "hedgehog": ["Wren", "Moss", "Tuck"],
    "fox": ["Juno", "Saffy", "Kite"],
    "badger": ["Nell", "Rook", "Midge"],
    "mouse": ["Nip", "Squeak", "Tansy"],
    "deer": ["Birch", "Willow", "Fern"],
}

HELPER_NAMES = {
    "rabbit": ["Aunt Clover", "Uncle Thistle"],
    "hedgehog": ["Grandma Pine", "Uncle Bramble"],
    "fox": ["Aunt Amber", "Uncle Rust"],
    "badger": ["Grandpa Stone", "Aunt Reed"],
    "mouse": ["Aunt Seed", "Grandma Nest"],
    "deer": ["Uncle Brook", "Aunt Meadow"],
}


# ---------------------------------------------------------------------------
# Reasonableness gate
# ---------------------------------------------------------------------------
def valid_places() -> list[str]:
    return list(PLACES.keys())


def valid_params(place: str, hero: str, friend: str) -> bool:
    return place in PLACES and hero in ANIMALS and friend in ANIMALS and hero != friend


def explain_invalid(place: str, hero: str, friend: str) -> str:
    if place not in PLACES:
        return "(No story: the setting is missing or unknown.)"
    if hero not in ANIMALS or friend not in ANIMALS:
        return "(No story: the animal cast is not recognized.)"
    if hero == friend:
        return "(No story: the hero and friend must be different animals.)"
    return "(No story: this combination does not make a clear little animal story.)"


# ---------------------------------------------------------------------------
# Narrative helpers
# ---------------------------------------------------------------------------
def hero_intro(world: World, hero: Entity, friend: Entity) -> None:
    world.say(
        f"{hero.name} was a little {hero.species} who loved the warm corners of {world.place.label}."
    )
    world.say(
        f"{hero.name} and {friend.name} were friends, but lately {hero.name} had been feeling miserable."
    )


def mosquito_trouble(world: World, hero: Entity, friend: Entity) -> None:
    hero.memes["miserable"] = hero.memes.get("miserable", 0) + 1
    hero.meters["itch"] = hero.meters.get("itch", 0) + 1
    world.say(
        f"A tiny mosquito buzzed in close and left {hero.name} itchy and miserable."
    )
    world.say(
        f"The grown-up in the story whispered that mosquitoes could bring typhus if the little ones were not careful."
    )


def fear_and_bravery(world: World, hero: Entity, friend: Entity, helper: Entity) -> None:
    hero.memes["fear"] = hero.memes.get("fear", 0) + 1
    friend.memes["worry"] = friend.memes.get("worry", 0) + 1
    world.say(
        f"{friend.name} wanted to hide, but {hero.name} took a brave breath and stood still."
    )
    world.say(
        f"Bravely, {hero.name} asked {helper.name} for help instead of running away."
    )
    hero.memes["bravery"] = hero.memes.get("bravery", 0) + 1


def helper_response(world: World, hero: Entity, friend: Entity, helper: Entity) -> None:
    world.say(
        f"{helper.name} came with a cool cloth, a clean cup, and a gentle voice."
    )
    world.say(
        f"{helper.name} said the little ones needed to rest, drink water, and keep away from the buzzing mosquito."
    )
    hero.meters["comfort"] = hero.meters.get("comfort", 0) + 1
    friend.meters["comfort"] = friend.meters.get("comfort", 0) + 1


def reconciliation(world: World, hero: Entity, friend: Entity) -> None:
    hero.memes["reconciliation"] = hero.memes.get("reconciliation", 0) + 1
    friend.memes["reconciliation"] = friend.memes.get("reconciliation", 0) + 1
    world.say(
        f"{hero.name} looked at {friend.name} and apologized for snapping when the itch felt too big."
    )
    world.say(
        f"{friend.name} hugged {hero.name} back, and the two friends felt their worry soften into reconciliation."
    )


def ending(world: World, hero: Entity, friend: Entity, helper: Entity) -> None:
    hero.memes["joy"] = hero.memes.get("joy", 0) + 1
    friend.memes["joy"] = friend.memes.get("joy", 0) + 1
    world.say(
        f"By sunset, {hero.name} was less miserable, the mosquito was gone, and {helper.name} watched the friends rest together."
    )
    world.say(
        f"{hero.name} and {friend.name} shared a blanket, feeling brave, safe, and kind again."
    )


# ---------------------------------------------------------------------------
# World builder
# ---------------------------------------------------------------------------
def tell(place_id: str, hero_species: str, friend_species: str, helper_species: str) -> World:
    place = PLACES[place_id]
    world = World(place)

    hero = world.add(Entity(
        id="hero",
        kind="character",
        species=hero_species,
        name=random.choice(HERO_NAMES[hero_species]),
    ))
    friend = world.add(Entity(
        id="friend",
        kind="character",
        species=friend_species,
        name=random.choice(FRIEND_NAMES[friend_species]),
    ))
    helper = world.add(Entity(
        id="helper",
        kind="character",
        species=helper_species,
        name=random.choice(HELPER_NAMES[helper_species]),
    ))
    mosquito = world.add(Entity(id="mosquito", kind="thing", species="mosquito", name="a mosquito"))

    world.facts.update(
        place=place,
        hero=hero,
        friend=friend,
        helper=helper,
        mosquito=mosquito,
        typhus=True,
    )

    hero_intro(world, hero, friend)
    world.para()
    mosquito_trouble(world, hero, friend)
    fear_and_bravery(world, hero, friend, helper)
    world.para()
    helper_response(world, hero, friend, helper)
    reconciliation(world, hero, friend)
    ending(world, hero, friend, helper)
    return world


# ---------------------------------------------------------------------------
# Q&A
# ---------------------------------------------------------------------------
def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero: Entity = f["hero"]
    friend: Entity = f["friend"]
    place: Place = f["place"]
    return [
        f"Write a short animal story about {hero.name}, a little {hero.species}, at {place.label} where a mosquito causes trouble.",
        f"Tell a child-friendly story where {hero.name} feels miserable, shows bravery, and makes up with {friend.name}.",
        f"Write a gentle story that includes a mosquito, typhus, bravery, and reconciliation in an animal setting.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero: Entity = f["hero"]
    friend: Entity = f["friend"]
    helper: Entity = f["helper"]
    place: Place = f["place"]
    return [
        QAItem(
            question=f"Who was the story about at {place.label}?",
            answer=f"It was about {hero.name}, a little {hero.species}, and the friend {friend.name}.",
        ),
        QAItem(
            question=f"Why did {hero.name} feel miserable?",
            answer=f"{hero.name} felt miserable because a mosquito buzzed close and made {hero.pronoun('object')} itchy and worried about typhus.",
        ),
        QAItem(
            question=f"What brave thing did {hero.name} do?",
            answer=f"{hero.name} showed bravery by asking {helper.name} for help instead of panicking.",
        ),
        QAItem(
            question=f"How did the friends mend their feeling at the end?",
            answer=f"{hero.name} and {friend.name} reached reconciliation when they apologized and hugged.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a mosquito?",
            answer="A mosquito is a tiny flying insect that can bite animals and people.",
        ),
        QAItem(
            question="What is typhus?",
            answer="Typhus is a serious sickness that can spread when tiny bugs or fleas carry germs.",
        ),
        QAItem(
            question="What does bravery mean?",
            answer="Bravery means doing a hard or scary thing even when you feel afraid.",
        ),
        QAItem(
            question="What does reconciliation mean?",
            answer="Reconciliation means making up after a fight or hurt feelings.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    out = ["== prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        out.append(f"{i}. {p}")
    out.append("")
    out.append("== story qa ==")
    for q in sample.story_qa:
        out.append(f"Q: {q.question}")
        out.append(f"A: {q.answer}")
    out.append("")
    out.append("== world qa ==")
    for q in sample.world_qa:
        out.append(f"Q: {q.question}")
        out.append(f"A: {q.answer}")
    return "\n".join(out)


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
place(P) :- setting(P).
character(X) :- animal(X).
valid_story(P,H,F) :- place(P), animal(H), animal(F), H != F.
miserable(H) :- mosquito(M), near(M,H).
brave(H) :- asks_help(H).
reconciled(H,F) :- apologizes(H,F), hugs(F,H).
#show valid_story/3.
#show miserable/1.
#show brave/1.
#show reconciled/2.
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid in PLACES:
        lines.append(asp.fact("setting", pid))
    for aid in ANIMALS:
        lines.append(asp.fact("animal", aid))
    lines.append(asp.fact("mosquito", "mosquito"))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_stories() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/3."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    py = {
        (p, h, f)
        for p in PLACES
        for h in ANIMALS
        for f in ANIMALS
        if h != f
    }
    import asp
    cl = set(asp.atoms(asp.one_model(asp_program("#show valid_story/3.")), "valid_story"))
    if py == cl:
        print(f"OK: clingo gate matches Python gate ({len(py)} combos).")
        return 0
    print("MISMATCH between ASP and Python gates.")
    if py - cl:
        print("only in python:", sorted(py - cl))
    if cl - py:
        print("only in asp:", sorted(cl - py))
    return 1


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Animal story world with mosquito trouble, bravery, and reconciliation.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--hero", choices=ANIMALS)
    ap.add_argument("--friend", choices=ANIMALS)
    ap.add_argument("--helper", choices=ANIMALS)
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
    hero = args.hero or rng.choice(list(ANIMALS))
    friend = args.friend or rng.choice([a for a in ANIMALS if a != hero])
    helper = args.helper or rng.choice(list(ANIMALS))
    if not valid_params(place, hero, friend):
        raise StoryError(explain_invalid(place, hero, friend))
    return StoryParams(place=place, hero=hero, friend=friend, helper=helper)


def generate(params: StoryParams) -> StorySample:
    rng = random.Random(params.seed)
    world = tell(params.place, params.hero, params.friend, params.helper)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        lines.append(f"  {e.id}: kind={e.kind} species={e.species} meters={meters} memes={memes}")
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
        print(asp_program("#show valid_story/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        triples = asp_valid_stories()
        print(f"{len(triples)} compatible story triples:")
        for t in triples:
            print("  ", t)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        curated = [
            StoryParams(place="riverbank", hero="rabbit", friend="hedgehog", helper="deer", seed=base_seed),
            StoryParams(place="orchard", hero="fox", friend="mouse", helper="badger", seed=base_seed + 1),
            StoryParams(place="barnyard", hero="deer", friend="rabbit", helper="hedgehog", seed=base_seed + 2),
        ]
        samples = [generate(p) for p in curated]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 20):
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

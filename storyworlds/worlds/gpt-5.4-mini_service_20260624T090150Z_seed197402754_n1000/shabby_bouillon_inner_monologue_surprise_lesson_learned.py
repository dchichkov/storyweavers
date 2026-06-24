#!/usr/bin/env python3
"""
A small animal-story world about a shabby kitchen, a bowl of bouillon, an inner
monologue, a surprise, and a lesson learned.

The premise:
- An animal character wants to make or carry something tasty.
- The world contains a shabby object or place that creates a small problem.
- A surprise changes the plan.
- The ending proves a lesson learned.

The prose is driven by world state rather than a fixed paragraph swap.
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
# Model
# ---------------------------------------------------------------------------

THRESHOLD = 1.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"  # "character" | "thing"
    species: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        return {"subject": "they", "object": "them", "possessive": "their"}[case]


@dataclass
class Place:
    name: str
    shabby: bool = False
    has_spoon: bool = False
    has_bouillon: bool = False
    has_surprise: bool = False


@dataclass
class StoryParams:
    place: str
    hero_species: str
    hero_name: str
    companion_species: str
    companion_name: str
    seed: Optional[int] = None


class World:
    def __init__(self, place: Place) -> None:
        self.place = place
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.fired: set[tuple] = set()

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


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------

PLACES = {
    "shabby_kitchen": Place(name="the shabby kitchen", shabby=True, has_spoon=True, has_bouillon=True, has_surprise=True),
    "tiny_cafe": Place(name="the tiny cafe", shabby=False, has_spoon=True, has_bouillon=True, has_surprise=True),
    "back_porch": Place(name="the back porch", shabby=False, has_spoon=True, has_bouillon=False, has_surprise=True),
}

SPECIES = ["cat", "dog", "rabbit", "mouse", "fox", "bear"]

NAMES = {
    "cat": ["Mimi", "Pip", "Cleo"],
    "dog": ["Buster", "Nina", "Rufus"],
    "rabbit": ["Tilly", "Hopper", "Mina"],
    "mouse": ["Nib", "Momo", "Pia"],
    "fox": ["Tara", "Jasper", "Fenn"],
    "bear": ["Bruno", "Milo", "Nora"],
}

TRAITS = ["curious", "careful", "cheerful", "shy", "proud", "gentle"]


# ---------------------------------------------------------------------------
# Narrative helpers
# ---------------------------------------------------------------------------

def opening(world: World, hero: Entity, companion: Entity) -> None:
    world.say(
        f"{hero.id} was a little {hero.species} with a curious nose and a steady heart. "
        f"{companion.id}, a {companion.species}, liked to help with warm meals."
    )
    world.say(
        f"Together they noticed {world.place.name}, where even the walls looked shabby and tired."
    )


def love_of_bouillon(world: World, hero: Entity) -> None:
    hero.memes["hunger"] += 1
    world.say(
        f"{hero.id} loved bouillon, because the warm smell felt like a soft hug in a bowl."
    )


def inner_monologue(world: World, hero: Entity) -> None:
    hero.memes["worry"] += 1
    world.say(
        f'In {hero.pronoun("possessive")} inner monologue, {hero.id} thought, '
        f'"Please let the spoon be clean enough, and please let the bouillon stay warm."'
    )


def shabby_problem(world: World, hero: Entity) -> None:
    hero.meters["careful"] = hero.meters.get("careful", 0) + 1
    if world.place.shabby:
        hero.memes["concern"] += 1
        world.say(
            f"The kitchen looked shabby, and {hero.id} noticed a wobbly table and a lonely old spoon."
        )
    else:
        world.say(
            f"The little place looked neat, but {hero.id} still watched the bowl carefully."
        )


def prepare_bouillon(world: World, hero: Entity) -> None:
    bowl = world.add(Entity(id="bowl", label="a bowl of bouillon", phrase="a bowl of bouillon"))
    bowl.meters["warm"] = 1
    bowl.owner = hero.id
    world.facts["bowl"] = bowl
    world.say(f"{hero.id} carried {bowl.phrase} toward the table very slowly.")


def surprise(world: World, hero: Entity, companion: Entity) -> None:
    if world.place.has_surprise:
        hero.memes["surprise"] += 1
        companion.memes["surprise"] += 1
        world.place.has_surprise = False
        world.say(
            f"Then came a surprise: under the shabby cloth, there was a tiny spoon already polished bright."
        )
        world.say(
            f"{companion.id} blinked and smiled, because the spoon had been waiting there all along."
        )
    else:
        world.say(
            f"Nothing jumped out, so {hero.id} had to keep going with patience alone."
        )


def lesson_learned(world: World, hero: Entity, companion: Entity) -> None:
    hero.memes["learned"] += 1
    world.say(
        f"{hero.id} learned that a shabby place can still hold a kind surprise, if someone looks gently."
    )
    world.say(
        f"At the end, {hero.id} sipped the bouillon, and the warm taste made the whole room feel cozy."
    )


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------

ASP_RULES = r"""
% A place is shabby when it carries the shabby flag.
shabby_place(P) :- place(P), shabby(P).

% A story is reasonable when there is bouillon, a place, and a surprise.
reasonable(P) :- place(P), has_bouillon(P), has_surprise(P).

% The preferred story must include an animal hero and a helper.
valid_story(P, H, C) :- reasonable(P), hero(H), companion(C), H != C, species(H,S), species(C,T).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid, place in PLACES.items():
        lines.append(asp.fact("place", pid))
        if place.shabby:
            lines.append(asp.fact("shabby", pid))
        if place.has_spoon:
            lines.append(asp.fact("has_spoon", pid))
        if place.has_bouillon:
            lines.append(asp.fact("has_bouillon", pid))
        if place.has_surprise:
            lines.append(asp.fact("has_surprise", pid))
    for sp in SPECIES:
        lines.append(asp.fact("species", sp))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_places() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show reasonable/1."))
    return sorted(set(asp.atoms(model, "reasonable")))


def asp_verify() -> int:
    py = {pid for pid, p in PLACES.items() if p.has_bouillon and p.has_surprise}
    cl = {x[0] for x in asp_valid_places()}
    if py == cl:
        print(f"OK: clingo gate matches Python ({len(py)} places).")
        return 0
    print("MISMATCH between clingo and Python:")
    print("python:", sorted(py))
    print("clingo:", sorted(cl))
    return 1


# ---------------------------------------------------------------------------
# Reasonableness gate
# ---------------------------------------------------------------------------

def valid_places() -> list[str]:
    return [pid for pid, p in PLACES.items() if p.has_bouillon and p.has_surprise]


def explain_rejection(place: Place) -> str:
    if not place.has_bouillon:
        return "(No story: the place has no bouillon, so there is no warm bowl for the animal story to revolve around.)"
    if not place.has_surprise:
        return "(No story: without a surprise, the lesson would be too flat for this world.)"
    return "(No story: the chosen setup is not a good fit.)"


# ---------------------------------------------------------------------------
# Q&A
# ---------------------------------------------------------------------------

def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    return [
        f'Write a gentle animal story about {hero.id}, a {hero.species}, in {world.place.name}, with bouillon and a surprise.',
        f'Write a short story for a child where a shabby place leads to an inner monologue, a surprise, and a lesson learned.',
        f'Write a story that uses the words "shabby" and "bouillon" and ends with a warm lesson learned.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    companion = f["companion"]
    return [
        QAItem(
            question=f"Who was the story about?",
            answer=f"The story was about {hero.id}, a little {hero.species}, and {companion.id}, who helped with the warm meal.",
        ),
        QAItem(
            question=f"What did {hero.id} want in the shabby kitchen?",
            answer=f"{hero.id} wanted to keep the bouillon warm and make sure the old spoon was good enough to use.",
        ),
        QAItem(
            question=f"What surprising thing did they find?",
            answer=f"They found a tiny spoon under the shabby cloth, and it was already polished bright.",
        ),
        QAItem(
            question=f"What lesson did {hero.id} learn?",
            answer=f"{hero.id} learned that a shabby place can still hold a kind surprise if you look gently.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is bouillon?",
            answer="Bouillon is a clear, tasty broth, often warm and savory, that people or animals can sip from a bowl.",
        ),
        QAItem(
            question="What does shabby mean?",
            answer="Shabby means old, worn, or a little messy-looking, like something that has been used a lot.",
        ),
        QAItem(
            question="What is a surprise?",
            answer="A surprise is something unexpected that happens when you do not know it is coming.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== Story questions ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== World knowledge questions ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Story generation
# ---------------------------------------------------------------------------

def make_world(params: StoryParams) -> World:
    place = PLACES[params.place]
    world = World(place)
    hero = world.add(Entity(id=params.hero_name, kind="character", species=params.hero_species))
    companion = world.add(Entity(id=params.companion_name, kind="character", species=params.companion_species))
    bouillon = world.add(Entity(id="bouillon", label="bouillon", phrase="a warm bowl of bouillon", owner=hero.id))
    world.facts = {
        "hero": hero,
        "companion": companion,
        "bouillon": bouillon,
        "place": place,
    }

    opening(world, hero, companion)
    love_of_bouillon(world, hero)
    world.para()
    shabby_problem(world, hero)
    inner_monologue(world, hero)
    prepare_bouillon(world, hero)
    world.para()
    surprise(world, hero, companion)
    lesson_learned(world, hero, companion)
    return world


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.place is not None and args.place not in PLACES:
        raise StoryError("Unknown place.")
    place_id = args.place or rng.choice(valid_places())
    place = PLACES[place_id]
    if not (place.has_bouillon and place.has_surprise):
        raise StoryError(explain_rejection(place))

    hero_species = args.hero_species or rng.choice(SPECIES)
    companion_species = args.companion_species or rng.choice([s for s in SPECIES if s != hero_species])
    hero_name = args.hero_name or rng.choice(NAMES[hero_species])
    companion_name = args.companion_name or rng.choice(NAMES[companion_species])

    return StoryParams(
        place=place_id,
        hero_species=hero_species,
        hero_name=hero_name,
        companion_species=companion_species,
        companion_name=companion_name,
    )


def generate(params: StoryParams) -> StorySample:
    world = make_world(params)
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
        bits = []
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        lines.append(f"  {e.id:10} ({e.kind:9}) {e.species:8} {' '.join(bits)}")
    lines.append(f"  place: {world.place.name} shabby={world.place.shabby} surprise_left={world.place.has_surprise}")
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


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Animal story world: shabby bouillon, inner monologue, surprise, lesson learned.")
    ap.add_argument("--place", choices=PLACES.keys())
    ap.add_argument("--hero-species", choices=SPECIES)
    ap.add_argument("--hero-name")
    ap.add_argument("--companion-species", choices=SPECIES)
    ap.add_argument("--companion-name")
    ap.add_argument("-n", type=int, default=1)
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("--trace", action="store_true")
    ap.add_argument("--qa", action="store_true")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--asp", action="store_true")
    ap.add_argument("--verify", action="store_true")
    ap.add_argument("--show-asp", action="store_true")
    return ap


def curated() -> list[StoryParams]:
    return [
        StoryParams(place="shabby_kitchen", hero_species="mouse", hero_name="Momo", companion_species="cat", companion_name="Cleo"),
        StoryParams(place="tiny_cafe", hero_species="rabbit", hero_name="Tilly", companion_species="dog", companion_name="Nina"),
    ]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show reasonable/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        model = asp.one_model(asp_program("#show reasonable/1."))
        vals = sorted(set(asp.atoms(model, "reasonable")))
        print(f"{len(vals)} reasonable places:")
        for (p,) in vals:
            print(f"  {p}")
        return

    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in curated()]
    else:
        base_seed = args.seed if args.seed is not None else random.randrange(2**31)
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
            rng = random.Random(base_seed + i)
            i += 1
            try:
                params = resolve_params(args, rng)
            except StoryError as e:
                print(e)
                return
            params.seed = base_seed + i
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
            header = f"### {p.hero_name} in {p.place}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()

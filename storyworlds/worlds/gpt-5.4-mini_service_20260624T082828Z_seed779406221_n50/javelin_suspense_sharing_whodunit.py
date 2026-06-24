#!/usr/bin/env python3
"""
storyworlds/worlds/javelin_suspense_sharing_whodunit.py
========================================================

A tiny Storyweavers world about a missing javelin, suspense, and sharing.
The story plays like a child-friendly whodunit: someone notices a mystery,
the clues are shared, the tension rises, and the truth resolves the worry.

Premise:
- A child athlete is excited for a backyard game with a prized javelin.
- The javelin vanishes before the throw.
- Friends share clues and look for the missing item.
- Suspense ends when the javelin is found in an unexpected but ordinary place.

World model:
- Typed entities with physical meters and emotional memes.
- State changes drive the prose: worry, searching, sharing, and relief.
- The "whodunit" element is a mystery of misplaced object, not a crime.

This file is self-contained apart from the shared Storyweavers result and ASP
helpers. It follows the standard storyworld interface:
build_parser, resolve_params, generate, emit, and main.
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
# Core world entities
# ---------------------------------------------------------------------------
@dataclass
class Entity:
    id: str
    kind: str = "thing"          # "character" | "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    worn_by: Optional[str] = None
    hidden: bool = False
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman"}
        male = {"boy", "father", "dad", "man"}
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
    label: str
    indoor: bool = False
    spots: list[str] = field(default_factory=list)


@dataclass
class StoryParams:
    place: str
    hero_name: str
    hero_gender: str
    helper_name: str
    helper_gender: str
    clue_spot: str
    seed: Optional[int] = None


class World:
    def __init__(self, place: Place) -> None:
        self.place = place
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict[str, object] = {}
        self.fired: set[str] = set()

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
        clone.fired = set(self.fired)
        return clone


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------
PLACES = {
    "field": Place(id="field", label="the school field", indoor=False, spots=["shed", "bench", "grass", "bucket"]),
    "yard": Place(id="yard", label="the backyard", indoor=False, spots=["deck", "flowerpot", "hose", "bench"]),
    "gym": Place(id="gym", label="the gym storage room", indoor=True, spots=["locker", "box", "rack", "corner"]),
}

HERO_NAMES = ["Maya", "Lina", "Nora", "Ivy", "Ella", "Zoe", "Ben", "Leo", "Finn", "Toby"]
HELPER_NAMES = ["Ari", "Milo", "June", "Pia", "Owen", "Cora", "Mia", "Sam"]

GENDERS = ["girl", "boy"]

CLUE_SPOTS = {
    "shed": "the shed",
    "bench": "the bench",
    "grass": "the grass",
    "bucket": "a bucket",
    "deck": "the deck",
    "flowerpot": "a flowerpot",
    "hose": "the hose",
    "locker": "a locker",
    "box": "a box",
    "rack": "the rack",
    "corner": "the corner",
}


# ---------------------------------------------------------------------------
# Story rules
# ---------------------------------------------------------------------------
def _set_meter(e: Entity, key: str, value: float) -> None:
    e.meters[key] = value


def _add_meter(e: Entity, key: str, delta: float = 1.0) -> None:
    e.meters[key] = e.meters.get(key, 0.0) + delta


def search_world(world: World, hero: Entity, helper: Entity, javelin: Entity) -> None:
    _add_meter(hero, "worry", 1)
    _add_meter(helper, "curiosity", 1)
    world.say(
        f"{hero.id} checked the place for the javelin, but it was not where it should have been."
    )
    world.say(
        f"{helper.id} noticed {hero.pronoun('possessive')} worried face and stayed close."
    )


def share_clues(world: World, hero: Entity, helper: Entity, javelin: Entity, clue_spot: str) -> None:
    _add_meter(helper, "help", 1)
    _add_meter(hero, "trust", 1)
    world.say(
        f"Then {helper.id} shared a clue: they had seen something long and thin near {clue_spot}."
    )
    world.say(
        f"{hero.id} listened carefully, and the two of them searched together instead of searching alone."
    )


def build_suspense(world: World, hero: Entity, helper: Entity) -> None:
    _add_meter(hero, "suspense", 1)
    _add_meter(helper, "suspense", 1)
    world.say(
        f"The quiet search made the moment feel even bigger, as if the whole day was waiting to hear the answer."
    )


def reveal(world: World, hero: Entity, helper: Entity, javelin: Entity, clue_spot: str) -> None:
    javelin.hidden = False
    _set_meter(javelin, "found", 1)
    _add_meter(hero, "relief", 1)
    _add_meter(helper, "relief", 1)
    world.say(
        f"At last, they looked by {clue_spot}, and there was the javelin after all."
    )
    world.say(
        f"It had only been tucked away there by mistake, waiting to be found."
    )


def finish(world: World, hero: Entity, helper: Entity, javelin: Entity) -> None:
    _add_meter(hero, "joy", 1)
    _add_meter(helper, "joy", 1)
    world.say(
        f"{hero.id} smiled again, and {helper.id} handed back the javelin with a grin."
    )
    world.say(
        f"After sharing the clue and solving the mystery, they could finally get back to the game."
    )


# ---------------------------------------------------------------------------
# Story construction
# ---------------------------------------------------------------------------
def tell(place: Place, hero_name: str, hero_gender: str, helper_name: str,
         helper_gender: str, clue_spot: str) -> World:
    world = World(place)

    hero = world.add(Entity(
        id=hero_name,
        kind="character",
        type=hero_gender,
        meters={"worry": 0.0, "trust": 0.0, "suspense": 0.0, "relief": 0.0, "joy": 0.0},
        memes={"worry": 0.0, "care": 1.0},
    ))
    helper = world.add(Entity(
        id=helper_name,
        kind="character",
        type=helper_gender,
        meters={"curiosity": 0.0, "help": 0.0, "suspense": 0.0, "relief": 0.0, "joy": 0.0},
        memes={"care": 1.0},
    ))
    javelin = world.add(Entity(
        id="javelin",
        type="javelin",
        label="javelin",
        phrase="a smooth practice javelin",
        owner=hero.id,
        hidden=True,
        meters={"lost": 1.0, "found": 0.0},
        memes={"importance": 1.0},
    ))

    world.say(
        f"{hero.id} loved practice day because {hero.pronoun('subject')} got to carry {hero.pronoun('possessive')} javelin."
    )
    world.say(
        f"But when the game was about to begin at {place.label}, the javelin was nowhere to be seen."
    )

    world.para()
    search_world(world, hero, helper, javelin)
    build_suspense(world, hero, helper)

    world.para()
    share_clues(world, hero, helper, javelin, clue_spot)
    reveal(world, hero, helper, javelin, clue_spot)

    world.para()
    finish(world, hero, helper, javelin)

    world.facts.update(
        hero=hero,
        helper=helper,
        javelin=javelin,
        place=place,
        clue_spot=clue_spot,
    )
    return world


# ---------------------------------------------------------------------------
# Q&A
# ---------------------------------------------------------------------------
def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero: Entity = f["hero"]  # type: ignore[assignment]
    helper: Entity = f["helper"]  # type: ignore[assignment]
    place: Place = f["place"]  # type: ignore[assignment]
    return [
        f'Write a child-friendly whodunit story about a missing javelin at {place.label}.',
        f"Tell a suspenseful story where {hero.id} and {helper.id} share clues and solve the mystery together.",
        f"Write a short story that uses the word 'javelin' and ends with the lost item being found in an ordinary place.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero: Entity = f["hero"]  # type: ignore[assignment]
    helper: Entity = f["helper"]  # type: ignore[assignment]
    javelin: Entity = f["javelin"]  # type: ignore[assignment]
    place: Place = f["place"]  # type: ignore[assignment]
    clue_spot: str = f["clue_spot"]  # type: ignore[assignment]

    return [
        QAItem(
            question=f"What was missing when {hero.id} was ready to begin practice at {place.label}?",
            answer=f"The missing thing was the javelin. {hero.id} expected to carry {javelin.label}, but it was not there at first."
        ),
        QAItem(
            question=f"Who helped {hero.id} by sharing a clue during the search?",
            answer=f"{helper.id} helped by sharing a clue and searching together with {hero.id}."
        ),
        QAItem(
            question=f"Where did the children finally find the javelin?",
            answer=f"They found the javelin by {clue_spot}, where it had been tucked away by mistake."
        ),
        QAItem(
            question=f"How did {hero.id} feel after the mystery was solved?",
            answer=f"{hero.id} felt relieved and happy because the missing javelin was found and the game could continue."
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a javelin?",
            answer="A javelin is a long, thin spear used in sports practice or competition. In a child story, it can be a practice tool that must be handled carefully."
        ),
        QAItem(
            question="What does it mean to share a clue?",
            answer="To share a clue means to tell another person an important hint that can help solve a problem or mystery."
        ),
        QAItem(
            question="Why does suspense make a story exciting?",
            answer="Suspense makes a story exciting because the reader wonders what will happen next and wants to learn the answer."
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


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
place(field).
place(yard).
place(gym).

character(girl).
character(boy).

clue_spot(shed).
clue_spot(bench).
clue_spot(grass).
clue_spot(bucket).
clue_spot(deck).
clue_spot(flowerpot).
clue_spot(hose).
clue_spot(locker).
clue_spot(box).
clue_spot(rack).
clue_spot(corner).

% A story is valid when the missing javelin can be plausibly found at one of the
% listed clue spots in the chosen place.
valid_story(P, H, G, C) :- place(P), character(H), character(G), clue_spot(C).

#show valid_story/4.
"""


def asp_facts() -> str:
    import storyworlds.asp as asp
    lines: list[str] = []
    for pid in PLACES:
        lines.append(asp.fact("place", pid))
        for spot in PLACES[pid].spots:
            lines.append(asp.fact("has_spot", pid, spot))
    for name in HERO_NAMES:
        lines.append(asp.fact("hero_name", name))
    for name in HELPER_NAMES:
        lines.append(asp.fact("helper_name", name))
    for gender in GENDERS:
        lines.append(asp.fact("gender", gender))
    for spot in CLUE_SPOTS:
        lines.append(asp.fact("clue_spot", spot))
    return "\n".join(lines)


def asp_program() -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n"


def asp_valid_stories() -> list[tuple]:
    import storyworlds.asp as asp
    model = asp.one_model(asp_program())
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    # The Python gate is intentionally simple: any registered place and clue spot
    # can produce a valid whodunit. We verify the ASP twin enumerates the same
    # cartesian structure.
    import storyworlds.asp as asp
    asp_set = set(asp_valid_stories())
    py_set = set((p, "girl", "boy", c) for p in PLACES for c in CLUE_SPOTS)
    if asp_set == py_set:
        print(f"OK: clingo gate matches Python registry product ({len(asp_set)} stories).")
        return 0
    print("MISMATCH between clingo and Python registry product:")
    if asp_set - py_set:
        print("  only in clingo:", sorted(asp_set - py_set))
    if py_set - asp_set:
        print("  only in python:", sorted(py_set - asp_set))
    return 1


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="A child-friendly whodunit storyworld about a missing javelin."
    )
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--hero-name", choices=HERO_NAMES)
    ap.add_argument("--hero-gender", choices=GENDERS)
    ap.add_argument("--helper-name", choices=HELPER_NAMES)
    ap.add_argument("--helper-gender", choices=GENDERS)
    ap.add_argument("--clue-spot", choices=list(CLUE_SPOTS))
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


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    place = args.place or rng.choice(list(PLACES))
    hero_gender = args.hero_gender or rng.choice(GENDERS)
    helper_gender = args.helper_gender or rng.choice(GENDERS)
    hero_name = args.hero_name or rng.choice(HERO_NAMES)
    helper_name = args.helper_name or rng.choice(HELPER_NAMES)
    clue_spot = args.clue_spot or rng.choice(PLACES[place].spots)
    if clue_spot not in CLUE_SPOTS:
        raise StoryError("The clue spot must be a normal, ordinary place where something could be tucked away.")
    return StoryParams(
        place=place,
        hero_name=hero_name,
        hero_gender=hero_gender,
        helper_name=helper_name,
        helper_gender=helper_gender,
        clue_spot=clue_spot,
    )


def generate(params: StoryParams) -> StorySample:
    world = tell(
        PLACES[params.place],
        params.hero_name,
        params.hero_gender,
        params.helper_name,
        params.helper_gender,
        params.clue_spot,
    )
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
        bits = []
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        if e.hidden:
            bits.append("hidden=True")
        lines.append(f"  {e.id:10} ({e.kind:9}) {' '.join(bits)}")
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


CURATED = [
    StoryParams(place="field", hero_name="Maya", hero_gender="girl", helper_name="Ari", helper_gender="boy", clue_spot="shed"),
    StoryParams(place="yard", hero_name="Ben", hero_gender="boy", helper_name="June", helper_gender="girl", clue_spot="bench"),
    StoryParams(place="gym", hero_name="Ivy", hero_gender="girl", helper_name="Sam", helper_gender="boy", clue_spot="box"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program())
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        stories = asp_valid_stories()
        print(f"{len(stories)} compatible whodunit stories:")
        for row in stories[:50]:
            print(" ", row)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)

    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 50, 50):
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

    for i, sample in enumerate(samples):
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.hero_name} at {p.place} (helper: {p.helper_name}, clue: {p.clue_spot})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()

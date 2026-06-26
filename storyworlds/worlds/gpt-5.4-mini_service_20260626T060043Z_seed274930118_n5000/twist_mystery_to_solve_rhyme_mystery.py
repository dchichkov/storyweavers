#!/usr/bin/env python3
"""
A small mystery world where a child solves a gentle mystery by following a rhyme.
The story is built from a simulated state: clues appear, suspicion rises, a twist
reframes the missing thing, and the ending proves what changed.
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
# Domain registries
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class Place:
    id: str
    label: str
    detail: str
    rhyme_hint: str
    indoors: bool = False


@dataclass(frozen=True)
class Mystery:
    id: str
    missing: str
    found: str
    owner: str
    feeling: str
    reason: str
    clue_one: str
    clue_two: str
    twist: str
    solution: str
    tags: set[str] = field(default_factory=set)


@dataclass(frozen=True)
class Helper:
    id: str
    label: str
    role: str
    rhyme_skill: str
    tip: str


PLACES: dict[str, Place] = {
    "library": Place(
        id="library",
        label="the library",
        detail="Rows of books made the room feel quiet and thoughtful.",
        rhyme_hint="A hush can hide a clue or two.",
        indoors=True,
    ),
    "garden": Place(
        id="garden",
        label="the garden",
        detail="Green leaves and low bushes gave the day a soft, bright look.",
        rhyme_hint="A path with petals can point the way.",
    ),
    "attic": Place(
        id="attic",
        label="the attic",
        detail="Boxes, blankets, and old trunks made the room feel full of secrets.",
        rhyme_hint="Old things keep old stories too.",
        indoors=True,
    ),
    "pier": Place(
        id="pier",
        label="the pier",
        detail="Wooden boards stretched over water, tapping gently underfoot.",
        rhyme_hint="A plank that creaks can still speak.",
    ),
}

MYSTERIES: dict[str, Mystery] = {
    "bell": Mystery(
        id="bell",
        missing="a little brass bell",
        found="under the blue cushion",
        owner="Grandma",
        feeling="worried",
        reason="she wanted to ring it for story time",
        clue_one="If it is not on the shelf, look where soft things rest.",
        clue_two="A bell that cannot be seen may still be heard by a keen ear.",
        twist="the bell had slipped inside a scarf basket after the room was tidied",
        solution="the basket was the real hiding place, not the shelf",
        tags={"quiet", "hidden", "sound"},
    ),
    "mitten": Mystery(
        id="mitten",
        missing="one red mitten",
        found="inside the coat pocket",
        owner="Nina",
        feeling="miffed",
        reason="she needed both mittens for the cold walk home",
        clue_one="One mitten lost will not stay in the snow forever.",
        clue_two="Check the coat where sleeves and secrets meet.",
        twist="the second mitten had been tucked away by accident when the coat was folded",
        solution="the pocket held the mitten all along",
        tags={"cold", "clothes", "small"},
    ),
    "kite": Mystery(
        id="kite",
        missing="a yellow kite string",
        found="wrapped around the broom handle",
        owner="Owen",
        feeling="cross",
        reason="he wanted to fly the kite before supper",
        clue_one="If a string is missing, follow the line of things that twirl.",
        clue_two="A broom can borrow more than dust when nobody is looking.",
        twist="the string had been used to tie a paper packet and then left on the broom",
        solution="the broom corner was hiding the looped string",
        tags={"play", "string", "light"},
    ),
}

HELPERS: dict[str, Helper] = {
    "mouse": Helper(
        id="mouse",
        label="a small mouse",
        role="helper",
        rhyme_skill="quick little rhymes",
        tip="It likes to speak in two short lines that point at the clue.",
    ),
    "grandpa": Helper(
        id="grandpa",
        label="Grandpa",
        role="helper",
        rhyme_skill="calm little rhymes",
        tip="He knows old rooms and where people set things down.",
    ),
    "girl": Helper(
        id="girl",
        label="Mina",
        role="detective",
        rhyme_skill="bright little rhymes",
        tip="She notices tiny changes in a room.",
    ),
    "cat": Helper(
        id="cat",
        label="a gray cat",
        role="helper",
        rhyme_skill="soft little rhymes",
        tip="It watches shelves, corners, and paws.",
    ),
}

NAMES = ["Mina", "Tess", "Owen", "June", "Finn", "Lena", "Milo", "Iris"]
TRAITS = ["curious", "careful", "brave", "patient", "sharp-eyed", "gentle"]


# ---------------------------------------------------------------------------
# World model
# ---------------------------------------------------------------------------

@dataclass
class Entity:
    id: str
    kind: str
    label: str
    type: str = "thing"
    owner: str = ""
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def get_meter(self, key: str) -> float:
        return self.meters.get(key, 0.0)

    def add_meter(self, key: str, value: float) -> None:
        self.meters[key] = self.get_meter(key) + value

    def add_meme(self, key: str, value: float) -> None:
        self.memes[key] = self.memes.get(key, 0.0) + value


@dataclass
class StoryParams:
    place: str
    mystery: str
    hero_name: str
    hero_trait: str
    helper: str
    seed: Optional[int] = None


@dataclass
class World:
    place: Place
    mystery: Mystery
    hero: Entity
    helper: Entity
    objects: dict[str, Entity] = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    facts: dict = field(default_factory=dict)
    fired: set[str] = field(default_factory=set)
    clue_score: float = 0.0
    suspicion: float = 0.0
    solved: bool = False
    twist_seen: bool = False

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
        return World(
            place=self.place,
            mystery=self.mystery,
            hero=copy.deepcopy(self.hero),
            helper=copy.deepcopy(self.helper),
            objects=copy.deepcopy(self.objects),
            paragraphs=[[]],
            facts=copy.deepcopy(self.facts),
            fired=set(self.fired),
            clue_score=self.clue_score,
            suspicion=self.suspicion,
            solved=self.solved,
            twist_seen=self.twist_seen,
        )


# ---------------------------------------------------------------------------
# Reasonable story gate
# ---------------------------------------------------------------------------

def is_reasonable(place: Place, mystery: Mystery, helper: Helper) -> bool:
    return bool(place and mystery and helper and mystery.found and mystery.missing)


# ---------------------------------------------------------------------------
# Causal simulation
# ---------------------------------------------------------------------------

def add_clue(world: World, text: str, amount: float = 1.0) -> None:
    world.clue_score += amount
    world.say(text)


def raise_suspicion(world: World, amount: float = 1.0) -> None:
    world.suspicion += amount


def narrate_twist(world: World) -> None:
    if world.twist_seen:
        return
    world.twist_seen = True
    world.say(
        f"Then came a twist: {world.mystery.twist}."
    )
    world.say(
        f"That made the first guess feel wrong, because {world.mystery.reason}."
    )


def solve_mystery(world: World) -> None:
    if world.clue_score >= 2 and world.suspicion >= 1 and not world.solved:
        world.solved = True
        world.say(
            f"At last, {world.hero.label} checked again and found {world.mystery.found}."
        )
        world.say(
            f"The answer was simple: {world.mystery.solution}. {world.mystery.owner} smiled, "
            f"and the worry in the room grew small."
        )


def advance(world: World) -> None:
    # Act 1: setup
    world.say(
        f"One day at {world.place.label}, {world.hero.label} noticed that {world.mystery.missing} was gone."
    )
    world.say(world.place.detail)
    world.say(
        f"{world.hero.label} was {world.hero.memes.get('trait_word', 'curious')} and wanted to solve the mystery."
    )

    # Act 2: clues and tension
    world.para()
    add_clue(world, world.mystery.clue_one)
    raise_suspicion(world, 1.0)
    world.say(
        f"{world.helper.label} listened carefully and said a small rhyme: "
        f'"{world.place.rhyme_hint}"'
    )
    world.say(
        f"That made {world.hero.label} look lower, then higher, then back again."
    )

    world.para()
    narrate_twist(world)
    add_clue(world, world.mystery.clue_two)
    raise_suspicion(world, 1.0)
    world.say(
        f"{world.hero.label} followed the rhyme to a new spot and noticed the room had been arranged a little differently."
    )

    # Act 3: resolution
    world.para()
    solve_mystery(world)
    if not world.solved:
        raise StoryError("The mystery did not resolve; the clue chain is too weak.")
    world.say(
        f"By bedtime, the mystery was solved, and {world.hero.label} could tell the story with a smile."
    )


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------

ASP_RULES = r"""
% A mystery is solvable when it has at least two clues and a twist that changes the first guess.
solvable(M) :- mystery(M), clue(M, C1), clue(M, C2), C1 != C2, twist(M).

% A story is valid when the chosen place, mystery, and helper are all present
% and the mystery can be solved by the clue chain.
valid_story(P, M, H) :- place(P), mystery(M), helper(H), solvable(M).
"""

def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for p in PLACES.values():
        lines.append(asp.fact("place", p.id))
    for m in MYSTERIES.values():
        lines.append(asp.fact("mystery", m.id))
        lines.append(asp.fact("twist", m.id))
        lines.append(asp.fact("clue", m.id, "one"))
        lines.append(asp.fact("clue", m.id, "two"))
    for h in HELPERS.values():
        lines.append(asp.fact("helper", h.id))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_stories() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/3."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    python_ok = {(p, m, h) for p in PLACES for m in MYSTERIES for h in HELPERS if is_reasonable(PLACES[p], MYSTERIES[m], HELPERS[h])}
    asp_ok = set(asp_valid_stories())
    if python_ok == asp_ok:
        print(f"OK: clingo gate matches Python gate ({len(python_ok)} stories).")
        return 0
    print("MISMATCH between clingo and Python gates:")
    if asp_ok - python_ok:
        print("  only in clingo:", sorted(asp_ok - python_ok))
    if python_ok - asp_ok:
        print("  only in python:", sorted(python_ok - asp_ok))
    return 1


# ---------------------------------------------------------------------------
# Story generation
# ---------------------------------------------------------------------------

def build_world(params: StoryParams) -> World:
    place = PLACES[params.place]
    mystery = MYSTERIES[params.mystery]
    helper_cfg = HELPERS[params.helper]
    hero = Entity(
        id=params.hero_name,
        kind="character",
        label=params.hero_name,
        type="child",
        meters={"curiosity": 1.0},
        memes={"trait_word": params.hero_trait},
    )
    helper = Entity(
        id=helper_cfg.id,
        kind="character",
        label=helper_cfg.label,
        type=helper_cfg.role,
    )
    return World(place=place, mystery=mystery, hero=hero, helper=helper)


def tell(world: World) -> None:
    world.say(
        f"{world.hero.label} was {world.hero.memes.get('trait_word', 'curious')}, and {world.helper.label} knew a few rhymes."
    )
    world.say(
        f"Together they went to {world.place.label} to solve why {world.mystery.missing} had disappeared."
    )
    advance(world)


def generation_prompts(world: World) -> list[str]:
    return [
        f"Write a short mystery story with a rhyme clue set in {world.place.label}.",
        f"Tell a child-friendly mystery where {world.hero.label} uses a rhyme to solve the case of {world.mystery.missing}.",
        "Write a gentle twist mystery that ends with the missing thing being found in a surprising place.",
    ]


def story_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question=f"What was missing in the story?",
            answer=f"{world.mystery.missing} was missing from {world.place.label}.",
        ),
        QAItem(
            question=f"Who helped {world.hero.label} with the mystery?",
            answer=f"{world.helper.label} helped by sharing a rhyme and pointing {world.hero.label} toward the clue.",
        ),
        QAItem(
            question=f"What was the twist in the mystery?",
            answer=f"The twist was that {world.mystery.twist}. That changed the first guess and led to the real answer.",
        ),
        QAItem(
            question=f"How was the mystery solved?",
            answer=f"{world.hero.label} followed the clues, looked again, and found {world.mystery.found}.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a rhyme?",
            answer="A rhyme is a pair of words or lines that sound alike at the end, like sing and ring.",
        ),
        QAItem(
            question="Why can a rhyme help solve a mystery?",
            answer="A rhyme can point to the right place by giving a clue in a memorable way.",
        ),
        QAItem(
            question="What does it mean to investigate?",
            answer="To investigate means to look carefully, ask questions, and follow clues until you understand what happened.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts -- asks that would produce this story =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== (2) Story questions -- answerable from the story text ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== (3) World-knowledge questions -- child level, no story needed ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    lines.append(f"place: {world.place.id}")
    lines.append(f"mystery: {world.mystery.id}")
    lines.append(f"hero curiosity: {world.hero.get_meter('curiosity')}")
    lines.append(f"clue_score: {world.clue_score}")
    lines.append(f"suspicion: {world.suspicion}")
    lines.append(f"twist_seen: {world.twist_seen}")
    lines.append(f"solved: {world.solved}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Params and CLI
# ---------------------------------------------------------------------------

@dataclass
class StoryParams:
    place: str
    mystery: str
    hero_name: str
    hero_trait: str
    helper: str
    seed: Optional[int] = None


CURATED = [
    StoryParams(place="library", mystery="bell", hero_name="Mina", hero_trait="sharp-eyed", helper="grandpa"),
    StoryParams(place="garden", mystery="mitten", hero_name="Tess", hero_trait="patient", helper="cat"),
    StoryParams(place="attic", mystery="kite", hero_name="Owen", hero_trait="curious", helper="mouse"),
]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A gentle mystery world with rhyme clues and a twist.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--mystery", choices=MYSTERIES)
    ap.add_argument("--helper", choices=HELPERS)
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


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for p in PLACES.values():
        for m in MYSTERIES.values():
            for h in HELPERS.values():
                if is_reasonable(p, m, h):
                    combos.append((p.id, m.id, h.id))
    return combos


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    combos = valid_combos()
    if args.place:
        combos = [c for c in combos if c[0] == args.place]
    if args.mystery:
        combos = [c for c in combos if c[1] == args.mystery]
    if args.helper:
        combos = [c for c in combos if c[2] == args.helper]
    if not combos:
        raise StoryError("No valid mystery story matches those options.")

    place, mystery, helper = rng.choice(sorted(combos))
    name = args.name or rng.choice(NAMES)
    trait = args.trait or rng.choice(TRAITS)
    return StoryParams(place=place, mystery=mystery, hero_name=name, hero_trait=trait, helper=helper)


def generate(params: StoryParams) -> StorySample:
    world = build_world(params)
    tell(world)
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


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/3."))
    return sorted(set(asp.atoms(model, "valid_story")))


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid_story/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        triples = asp_valid_combos()
        print(f"{len(triples)} compatible stories:")
        for t in triples:
            print("  ", t)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
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
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.hero_name}: {p.mystery} in {p.place}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()

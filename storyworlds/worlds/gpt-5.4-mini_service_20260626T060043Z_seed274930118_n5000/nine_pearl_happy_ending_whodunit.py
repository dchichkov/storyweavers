#!/usr/bin/env python3
"""
A standalone story world for a tiny whodunit about nine pearls and a happy ending.

The seed premise:
- Nine pearl beads are part of a treasured necklace.
- One pearl seems missing, creating a small mystery.
- A child detective traces clues, questions a few helpers, and discovers the pearl
  was not stolen at all.
- The ending is happy: the necklace is restored and everyone feels relieved.

This world keeps the story close to a whodunit: clues, suspects, a reveal, and a
gentle resolution.
"""

from __future__ import annotations

import argparse
import json
import os
import random
import sys
from dataclasses import dataclass, field, asdict
from typing import Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from results import QAItem, StoryError, StorySample  # noqa: E402


# ---------------------------------------------------------------------------
# Core model
# ---------------------------------------------------------------------------

@dataclass
class Entity:
    id: str
    kind: str = "thing"  # "character" | "thing"
    label: str = ""
    type: str = ""
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)
    owner: Optional[str] = None
    location: str = ""
    plural: bool = False
    role: str = ""

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "woman", "mother"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man", "father"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Place:
    name: str
    indoor: bool = True
    clues: tuple[str, ...] = ()


@dataclass
class StoryParams:
    place: str
    hero_name: str
    hero_type: str
    helper_name: str
    helper_type: str
    seed: Optional[int] = None


@dataclass
class World:
    place: Place
    entities: dict[str, Entity] = field(default_factory=dict)
    events: list[str] = field(default_factory=list)
    facts: dict[str, object] = field(default_factory=dict)
    trace_log: list[str] = field(default_factory=list)

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str) -> Entity:
        return self.entities[eid]

    def say(self, text: str) -> None:
        if text:
            self.events.append(text)

    def mark(self, text: str) -> None:
        self.trace_log.append(text)

    def render(self) -> str:
        return " ".join(self.events)


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------

PLACES = {
    "parlor": Place(
        name="the parlor",
        indoor=True,
        clues=("dusty shelf", "blue ribbon", "small footprint"),
    ),
    "garden": Place(
        name="the garden",
        indoor=False,
        clues=("soft dirt", "broken twig", "shiny leaf"),
    ),
    "kitchen": Place(
        name="the kitchen",
        indoor=True,
        clues=("crumbs", "open drawer", "spoon"),
    ),
}

HERO_NAMES = ["Mina", "Toby", "Nia", "Owen", "Luna", "Eli"]
HELPER_NAMES = ["Grandma", "Papa", "Aunt June", "Uncle Ben", "Ms. Bee", "Mr. Fox"]

HERO_TYPES = {
    "girl": "girl",
    "boy": "boy",
}

HELPER_TYPES = {
    "mother": "mother",
    "father": "father",
    "aunt": "woman",
    "uncle": "man",
    "neighbor": "person",
}

TRAITS = ["curious", "careful", "brave", "bright", "kind"]


# ---------------------------------------------------------------------------
# World premise
# ---------------------------------------------------------------------------

def build_world(params: StoryParams) -> World:
    place = PLACES[params.place]
    world = World(place=place)

    hero = world.add(Entity(
        id=params.hero_name,
        kind="character",
        type=params.hero_type,
        role="detective",
        memes={"curiosity": 1.0, "hope": 1.0},
    ))
    helper = world.add(Entity(
        id=params.helper_name,
        kind="character",
        type=params.helper_type,
        role="helper",
        memes={"worry": 1.0, "relief": 0.0},
    ))
    necklace = world.add(Entity(
        id="necklace",
        kind="thing",
        label="pearl necklace",
        type="necklace",
        owner=helper.id,
        location=place.name,
        plural=False,
        meters={"pearls": 9.0, "missing": 1.0},
    ))
    pearl = world.add(Entity(
        id="pearl",
        kind="thing",
        label="pearl",
        type="pearl",
        owner=helper.id,
        location="under a cushion" if place.indoor else "in the garden dirt",
        plural=False,
        meters={"shine": 1.0},
    ))

    world.facts.update(
        hero=hero,
        helper=helper,
        necklace=necklace,
        pearl=pearl,
        place=place,
        clue=place.clues[0],
    )
    return world


# ---------------------------------------------------------------------------
# Story actions
# ---------------------------------------------------------------------------

def opening(world: World) -> None:
    hero = world.facts["hero"]
    helper = world.facts["helper"]
    necklace = world.facts["necklace"]

    world.say(
        f"{hero.id} was a {hero.pronoun('subject').capitalize()} little detective with a sharp eye."
    )
    world.say(
        f"One morning, {helper.id} gasped at a pearl necklace that was supposed to hold nine pearls."
    )
    world.say(
        f"But one pearl was missing, and the necklace looked lonely in {world.place.name}."
    )
    world.say(
        f"{hero.id} promised to solve the mystery before supper."
    )
    world.mark(f"opening: necklace has {necklace.meters['pearls']} pearls, one missing")


def clue_one(world: World) -> None:
    hero = world.facts["hero"]
    clue = world.place.clues[0]
    world.say(
        f"{hero.id} crouched low and found the first clue: {clue}."
    )
    world.say(
        f"That clue mattered because it pointed to a place where a tiny pearl might have rolled."
    )
    world.mark(f"clue_one: {clue}")


def clue_two(world: World) -> None:
    hero = world.facts["hero"]
    helper = world.facts["helper"]
    pearl = world.facts["pearl"]
    world.say(
        f"{hero.id} asked {helper.id} where the necklace had been last seen."
    )
    world.say(
        f"{helper.id} remembered putting it near a cushion, and that made the lost pearl seem less scary."
    )
    world.say(
        f"Then {hero.id} peeked under the cushion and spotted something round and bright."
    )
    pearl.location = "under a cushion"
    world.mark("clue_two: pearl found under cushion")


def reveal(world: World) -> None:
    hero = world.facts["hero"]
    helper = world.facts["helper"]
    necklace = world.facts["necklace"]
    pearl = world.facts["pearl"]

    world.say(
        f"{hero.id} smiled and lifted the pearl carefully."
    )
    world.say(
        f"The pearl had not been stolen at all; it had simply slipped off the necklace and tucked itself away."
    )
    necklace.meters["missing"] = 0.0
    necklace.meters["pearls"] = 9.0
    pearl.location = "back on the necklace"
    helper.memes["worry"] = 0.0
    helper.memes["relief"] = 1.0
    hero.memes["hope"] = 2.0
    world.say(
        f"{helper.id} laughed with relief when {hero.id} threaded the pearl back into place."
    )
    world.mark("reveal: no theft, just a slipped pearl")


def ending(world: World) -> None:
    hero = world.facts["hero"]
    helper = world.facts["helper"]
    world.say(
        f"At last, the necklace held all nine pearls again, shining as neatly as before."
    )
    world.say(
        f"{hero.id} got a happy grin, and {helper.id} gave {hero.id} a warm thank-you hug."
    )
    world.say(
        f"It was a happy ending, because the mystery was solved and nothing precious was lost."
    )
    world.mark("ending: happy resolution")


def tell(world: World) -> World:
    opening(world)
    world.say("")
    clue_one(world)
    clue_two(world)
    reveal(world)
    world.say("")
    ending(world)
    return world


# ---------------------------------------------------------------------------
# Q&A
# ---------------------------------------------------------------------------

def generation_prompts(world: World) -> list[str]:
    hero = world.facts["hero"]
    helper = world.facts["helper"]
    return [
        'Write a child-friendly whodunit story about nine pearls and a missing clue.',
        f"Tell a short mystery where {hero.id} solves why {helper.id} thinks a pearl is lost.",
        "Make the ending happy by showing the pearl was found, not stolen.",
    ]


def story_qa(world: World) -> list[QAItem]:
    hero = world.facts["hero"]
    helper = world.facts["helper"]
    return [
        QAItem(
            question=f"Why did {helper.id} worry at the start?",
            answer="Because one pearl seemed to be missing from the necklace, and that made the necklace look incomplete.",
        ),
        QAItem(
            question=f"What clue did {hero.id} find first?",
            answer=f"{hero.id} found a {world.place.clues[0]} that hinted where the pearl might have rolled.",
        ),
        QAItem(
            question="Was the pearl stolen?",
            answer="No. The pearl had only slipped away and was found safely again.",
        ),
        QAItem(
            question="How did the story end?",
            answer="The necklace was repaired with all nine pearls back in place, and everyone felt happy and relieved.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a pearl?",
            answer="A pearl is a smooth, shiny gem-like bead that can be used in jewelry like necklaces.",
        ),
        QAItem(
            question="Why do detectives look for clues?",
            answer="Detectives look for clues so they can figure out what happened and solve a mystery.",
        ),
        QAItem(
            question="What does it mean when something is missing?",
            answer="Something is missing when it is not where people expected it to be.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== Story Q&A ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== World knowledge Q&A ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------

ASP_RULES = r"""
% Nine pearls means the necklace is complete when no pearl is missing.
complete(necklace) :- pearls(necklace, 9), not missing(necklace).

% A mystery is present if one pearl is missing from a necklace of nine.
mystery(necklace) :- pearls(necklace, 9), missing(necklace).

% The happy ending is possible when the pearl is found again.
happy_ending(necklace) :- complete(necklace), found(pearl), returned(pearl, necklace).
"""


def asp_facts() -> str:
    import storyworlds.asp as asp
    lines = []
    for place_id, place in PLACES.items():
        lines.append(asp.fact("place", place_id))
        if place.indoor:
            lines.append(asp.fact("indoor", place_id))
        for clue in place.clues:
            lines.append(asp.fact("clue", place_id, clue))
    lines.append(asp.fact("necklace", "necklace"))
    lines.append(asp.fact("pearls", "necklace", 9))
    lines.append(asp.fact("missing", "necklace"))
    lines.append(asp.fact("found", "pearl"))
    lines.append(asp.fact("returned", "pearl", "necklace"))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import storyworlds.asp as asp

    model = asp.one_model(asp_program("#show complete/1. #show mystery/1. #show happy_ending/1."))
    shown = set()
    for sym in model:
        if sym.name in {"complete", "mystery", "happy_ending"}:
            shown.add((sym.name, tuple(a.name if a.type == 2 else a.number if a.type == 1 else a.string for a in sym.arguments)))

    expected = {
        ("mystery", ("necklace",)),
        ("complete", ("necklace",)),
        ("happy_ending", ("necklace",)),
    }
    if shown == expected:
        print("OK: ASP twin matches the simple story-state facts.")
        return 0
    print("MISMATCH in ASP verification.")
    print("seen:", sorted(shown))
    print("expected:", sorted(expected))
    return 1


# ---------------------------------------------------------------------------
# Generation and CLI
# ---------------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A tiny whodunit about nine pearls and a happy ending.")
    ap.add_argument("--place", choices=PLACES.keys())
    ap.add_argument("--hero-name", choices=HERO_NAMES)
    ap.add_argument("--hero-type", choices=HERO_TYPES.keys())
    ap.add_argument("--helper-name", choices=HELPER_NAMES)
    ap.add_argument("--helper-type", choices=HELPER_TYPES.keys())
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
    place = args.place or rng.choice(list(PLACES.keys()))
    hero_type = args.hero_type or rng.choice(list(HERO_TYPES.keys()))
    helper_type = args.helper_type or rng.choice(list(HELPER_TYPES.keys()))
    hero_name = args.hero_name or rng.choice(HERO_NAMES)
    helper_name = args.helper_name or rng.choice(HELPER_NAMES)
    if hero_name == helper_name:
        helper_name = next(n for n in HELPER_NAMES if n != hero_name)
    return StoryParams(
        place=place,
        hero_name=hero_name,
        hero_type=hero_type,
        helper_name=helper_name,
        helper_type=helper_type,
    )


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


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for eid, ent in world.entities.items():
        bits = []
        if ent.label:
            bits.append(f"label={ent.label}")
        if ent.location:
            bits.append(f"location={ent.location}")
        if ent.meters:
            bits.append(f"meters={ent.meters}")
        if ent.memes:
            bits.append(f"memes={ent.memes}")
        lines.append(f"{eid}: {', '.join(bits)}")
    lines.extend(world.trace_log)
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


def curated() -> list[StoryParams]:
    return [
        StoryParams(place="parlor", hero_name="Mina", hero_type="girl", helper_name="Grandma", helper_type="mother"),
        StoryParams(place="garden", hero_name="Toby", hero_type="boy", helper_name="Papa", helper_type="father"),
        StoryParams(place="kitchen", hero_name="Nia", hero_type="girl", helper_name="Aunt June", helper_type="aunt"),
    ]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show complete/1. #show mystery/1. #show happy_ending/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import storyworlds.asp as asp
        model = asp.one_model(asp_program("#show complete/1. #show mystery/1. #show happy_ending/1."))
        print("ASP model:")
        for atom in model:
            print(atom)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)

    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in curated()]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 20, 20):
            params = resolve_params(args, random.Random(base_seed + i))
            sample = generate(params)
            if sample.story not in seen:
                seen.add(sample.story)
                params.seed = base_seed + i
                sample.params = params
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
        if len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()

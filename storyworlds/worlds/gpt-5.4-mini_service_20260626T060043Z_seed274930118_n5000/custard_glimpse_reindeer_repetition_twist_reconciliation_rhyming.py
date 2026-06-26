#!/usr/bin/env python3
"""
A small rhyme-driven storyworld about a child, a custard cup, and a surprise reindeer.

Premise:
- A child loves a sweet custard treat.
- The child glimpses a reindeer nearby and thinks something strange is happening.
- A repeated rhyme keeps the rhythm of the story.
- A twist reveals the reindeer was not stealing the custard, only sniffing the sugar.
- Reconciliation ends the worry and turns the surprise into a shared, gentle moment.

The domain is intentionally small and state-driven:
- meters track physical state like full/empty, warm/cool, and nearby/far.
- memes track emotional state like worry, wonder, and peace.
"""

from __future__ import annotations

import argparse
import copy
import json
import os
import random
import re
import sys
from dataclasses import dataclass, field
from typing import Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from results import QAItem, StoryError, StorySample  # noqa: E402


# ---------------------------------------------------------------------------
# Small physical/emotional model
# ---------------------------------------------------------------------------
@dataclass
class Entity:
    id: str
    kind: str = "thing"  # "character" | "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    plural: bool = False
    owner: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "mother", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class World:
    place: str
    rhyme_word: str = "glow"
    entities: dict[str, Entity] = field(default_factory=dict)
    facts: dict = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])

    def add(self, e: Entity) -> Entity:
        self.entities[e.id] = e
        return e

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
        clone = World(self.place, self.rhyme_word)
        clone.entities = copy.deepcopy(self.entities)
        clone.facts = copy.deepcopy(self.facts)
        clone.paragraphs = [[]]
        return clone


# ---------------------------------------------------------------------------
# Parameters
# ---------------------------------------------------------------------------
@dataclass
class StoryParams:
    place: str
    hero_name: str
    hero_type: str
    parent_type: str
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------
PLACES = {
    "yard": "the yard",
    "garden": "the garden",
    "market": "the market",
    "porch": "the porch",
}

HERO_NAMES = {
    "girl": ["Mia", "Lila", "Nora", "Zoe", "Eva"],
    "boy": ["Ben", "Toby", "Finn", "Noah", "Owen"],
}

PARENT_TYPES = ["mother", "father"]

RHYMES = [
    "Sip and slip, then grin and glow",
    "See it, be it, let it go",
    "Near the stall or near the snow",
    "Blink and think, then take it slow",
]


# ---------------------------------------------------------------------------
# Story helpers
# ---------------------------------------------------------------------------
def _say_rhyme(world: World, line: str) -> None:
    world.say(line)


def _introduce(world: World, hero: Entity, custard: Entity) -> None:
    world.say(
        f"{hero.id} was a little {hero.type} with bright eyes and a love for sweet, soft fun. "
        f"{hero.pronoun().capitalize()} held a cup of {custard.label} and watched it glow."
    )
    world.say(
        f"Every spoonful felt like a song, and every song had a round, warm rhyme: "
        f"\"{world.facts['rhyme']}\""
    )


def _glimpse(world: World, hero: Entity, reindeer: Entity) -> None:
    hero.memes["wonder"] = hero.memes.get("wonder", 0) + 1
    world.say(
        f"Then {hero.id} had a glimpse by the gate: a reindeer with soft brown eyes and shiny antlers."
    )
    world.say(
        f"{hero.id} blinked once, then twice, and the rhyme came back again: "
        f"\"{world.facts['rhyme']}\""
    )


def _worry(world: World, hero: Entity, custard: Entity, reindeer: Entity) -> None:
    hero.memes["worry"] = hero.memes.get("worry", 0) + 1
    world.say(
        f"{hero.id} feared the reindeer wanted the custard cup."
    )
    world.say(
        f"\"Don't come close,\" {hero.pronoun()} whispered, clutching the custard tight."
    )
    world.say(
        f"Once more the rhyme returned like a tiny drum: \"{world.facts['rhyme']}\""
    )


def _twist(world: World, hero: Entity, custard: Entity, reindeer: Entity) -> None:
    reindeer.meters["near"] = 1
    reindeer.memes["friendly"] = 1
    world.say(
        f"But the twist was sweet and small: the reindeer was not after the custard at all."
    )
    world.say(
        f"{reindeer.id} only sniffed the sugar-scent in the air, because {custard.label} smelled like vanilla snow."
    )
    world.say(
        f"The reindeer nosed the spoon, not the bowl, and gave a polite little snort."
    )


def _reconcile(world: World, hero: Entity, custard: Entity, reindeer: Entity, parent: Entity) -> None:
    hero.memes["worry"] = 0
    hero.memes["peace"] = hero.memes.get("peace", 0) + 1
    reindeer.memes["peace"] = reindeer.memes.get("peace", 0) + 1
    custard.meters["full"] = 0.5
    world.say(
        f"Then {hero.id} smiled, and {hero.pronoun()} and the reindeer shared a friendly look."
    )
    world.say(
        f"{parent.id} laughed softly and said they could all sit together for a tiny taste."
    )
    world.say(
        f"{hero.id} offered the reindeer a safe lick of the spoon, and the reindeer bowed its head."
    )
    world.say(
        f"At the end, the cup stayed half full, the mood stayed light, and the rhyme turned calm: "
        f"\"{world.facts['rhyme']}\""
    )


def tell(params: StoryParams) -> World:
    world = World(place=PLACES[params.place])
    hero = world.add(Entity(id=params.hero_name, kind="character", type=params.hero_type))
    parent = world.add(Entity(id="Parent", kind="character", type=params.parent_type))
    custard = world.add(
        Entity(
            id="custard",
            type="custard",
            label="custard",
            phrase="a little cup of custard",
            meters={"full": 1.0, "warm": 1.0},
            owner=hero.id,
        )
    )
    reindeer = world.add(
        Entity(
            id="Reindeer",
            kind="character",
            type="reindeer",
            label="reindeer",
            meters={"near": 0.0},
            memes={"gentle": 1.0},
        )
    )
    rhyme = random.choice(RHYMES)
    world.facts.update(hero=hero, parent=parent, custard=custard, reindeer=reindeer, rhyme=rhyme)

    _introduce(world, hero, custard)
    world.para()
    world.say(f"One day at {world.place}, {hero.id} wandered with the custard cup.")
    _say_rhyme(world, f"\"{rhyme}\"")

    world.para()
    _glimpse(world, hero, reindeer)
    _worry(world, hero, custard, reindeer)

    world.para()
    _twist(world, hero, custard, reindeer)

    world.para()
    _reconcile(world, hero, custard, reindeer, parent)

    world.facts["resolved"] = True
    return world


# ---------------------------------------------------------------------------
# QA
# ---------------------------------------------------------------------------
def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a short rhyming story for a young child about {f["hero"].id}, custard, and a surprise reindeer.',
        f'Create a gentle story that repeats a line like "{f["rhyme"]}" and ends with reconciliation.',
        f"Tell a tiny story where a child has custard, catches a glimpse of a reindeer, and learns the surprise was friendly.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero: Entity = f["hero"]
    parent: Entity = f["parent"]
    custard: Entity = f["custard"]
    reindeer: Entity = f["reindeer"]
    rhyme = f["rhyme"]
    return [
        QAItem(
            question=f"What was {hero.id} holding at the start of the story?",
            answer=f"{hero.id} was holding a cup of {custard.label}.",
        ),
        QAItem(
            question=f"What did {hero.id} glimpse near the gate?",
            answer=f"{hero.id} caught a glimpse of a reindeer with soft brown eyes and shiny antlers.",
        ),
        QAItem(
            question=f"Why did {hero.id} worry at first?",
            answer=f"{hero.id} worried because {hero.pronoun()} thought the reindeer might want the custard.",
        ),
        QAItem(
            question=f"What was the twist?",
            answer=f"The twist was that the reindeer only wanted to sniff the sugar smell, not steal the custard.",
        ),
        QAItem(
            question=f"How did the story end?",
            answer=f"{hero.id}, the parent, and the reindeer ended peacefully together, and the custard stayed safe.",
        ),
        QAItem(
            question=f"What line came back again and again in the story?",
            answer=f'The repeated rhyme was "{rhyme}".',
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is custard?",
            answer="Custard is a soft, sweet dessert made from milk or cream and eggs, often eaten with a spoon.",
        ),
        QAItem(
            question="What is a reindeer?",
            answer="A reindeer is a deer that has antlers and lives in cold places. Some people also call it a caribou.",
        ),
        QAItem(
            question="What is a glimpse?",
            answer="A glimpse is a quick look at something for a short moment.",
        ),
        QAItem(
            question="What is repetition in a story?",
            answer="Repetition means saying a word, line, or idea again on purpose so it feels musical or easy to remember.",
        ),
        QAItem(
            question="What is a twist in a story?",
            answer="A twist is a surprise that changes what the reader thought was happening.",
        ),
        QAItem(
            question="What is reconciliation?",
            answer="Reconciliation is when characters stop being upset and make peace again.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    out = ["== (1) Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        out.append(f"{i}. {p}")
    out.append("")
    out.append("== (2) Story questions ==")
    for item in sample.story_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    out.append("")
    out.append("== (3) World knowledge questions ==")
    for item in sample.world_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    return "\n".join(out)


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for e in world.entities.values():
        bits = []
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        lines.append(f"{e.id} ({e.type}): {' '.join(bits)}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
% Facts come from the registries; the rules mirror the reasonableness gate.
feature(repetition).
feature(twist).
feature(reconciliation).

valid_place(P) :- place(P).
valid_story(P) :- valid_place(P), feature(repetition), feature(twist), feature(reconciliation).
"""

def asp_facts() -> str:
    import asp
    lines = []
    for pid in PLACES:
        lines.append(asp.fact("place", pid))
    for feat in ["repetition", "twist", "reconciliation"]:
        lines.append(asp.fact("feature", feat))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show valid_story/1."))
    asp_places = sorted(set(asp.atoms(model, "valid_story")))
    py_places = sorted((p,) for p in PLACES)
    if asp_places == py_places:
        print(f"OK: clingo gate matches Python registry ({len(py_places)} places).")
        return 0
    print("MISMATCH between clingo and Python:")
    print("  asp:", asp_places)
    print("  py :", py_places)
    return 1


# ---------------------------------------------------------------------------
# Generation and CLI
# ---------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Rhyming story world with custard, glimpse, and reindeer.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--hero-name")
    ap.add_argument("--hero-type", choices=["girl", "boy"])
    ap.add_argument("--parent-type", choices=PARENT_TYPES)
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
    hero_type = args.hero_type or rng.choice(["girl", "boy"])
    hero_name = args.hero_name or rng.choice(HERO_NAMES[hero_type])
    parent_type = args.parent_type or rng.choice(PARENT_TYPES)
    return StoryParams(place=place, hero_name=hero_name, hero_type=hero_type, parent_type=parent_type)


def generate(params: StoryParams) -> StorySample:
    world = tell(params)
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


CURATED = [
    StoryParams(place="yard", hero_name="Mia", hero_type="girl", parent_type="mother"),
    StoryParams(place="garden", hero_name="Ben", hero_type="boy", parent_type="father"),
    StoryParams(place="porch", hero_name="Lila", hero_type="girl", parent_type="mother"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid_story/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        model = asp.one_model(asp_program("#show valid_story/1."))
        stories = sorted(set(asp.atoms(model, "valid_story")))
        for (place,) in stories:
            print(place)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(p) for p in CURATED]
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

    for i, sample in enumerate(samples):
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""
A standalone storyworld about a small adventure in a tavern.

Seed words:
- pillar
- energetic
- tavern

Narrative features:
- Bravery
- Suspense
- Reconciliation

The domain is a gentle, child-facing adventure in which an energetic child
visits a tavern-like hall, discovers a lost item near a pillar, feels a little
fear, acts bravely, and ends in a warm reconciliation.
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
# Content registries
# ---------------------------------------------------------------------------

@dataclass
class Character:
    name: str
    role: str
    type: str = "character"
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.role in {"girl", "woman", "mother"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.role in {"boy", "man", "father"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]


@dataclass
class Place:
    name: str
    place_type: str = "tavern"
    pillars: int = 1
    cozy: bool = True


@dataclass
class Relic:
    name: str
    label: str
    location: str = "pillar"
    owner: str = ""
    found: bool = False


@dataclass
class StoryParams:
    place: str = "tavern"
    hero_name: str = "Milo"
    hero_role: str = "boy"
    companion_name: str = "Lina"
    companion_role: str = "girl"
    seed: Optional[int] = None


PLACES = {
    "tavern": Place(name="the tavern", place_type="tavern", pillars=3, cozy=True),
}

HERO_NAMES_BOY = ["Milo", "Theo", "Finn", "Eli", "Noah"]
HERO_NAMES_GIRL = ["Lina", "Mira", "Nora", "Pia", "Ava"]


# ---------------------------------------------------------------------------
# World model
# ---------------------------------------------------------------------------

class World:
    def __init__(self, place: Place) -> None:
        self.place = place
        self.hero: Optional[Character] = None
        self.companion: Optional[Character] = None
        self.relic: Optional[Relic] = None
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict[str, object] = {}
        self.fired: set[str] = set()

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)


def _add_meter(ent: Character, key: str, amount: float = 1.0) -> None:
    ent.meters[key] = ent.meters.get(key, 0.0) + amount


def _add_meme(ent: Character, key: str, amount: float = 1.0) -> None:
    ent.memes[key] = ent.memes.get(key, 0.0) + amount


# ---------------------------------------------------------------------------
# Story events
# ---------------------------------------------------------------------------

def introduce(world: World) -> None:
    hero = world.hero
    companion = world.companion
    assert hero and companion
    world.say(
        f"{hero.name} was an energetic little {hero.role} who loved grand adventures."
    )
    world.say(
        f"{companion.name} was a kind {companion.role} who liked calm evenings and warm light."
    )
    world.say(
        f"One evening, they stepped into {world.place.name}, where the candles glowed and the wooden pillars stood like watchful trees."
    )


def setup_relic(world: World) -> None:
    hero = world.hero
    assert hero
    world.relic = Relic(
        name="silver bell",
        label="a tiny silver bell",
        location="behind a pillar",
        owner=hero.name,
    )
    world.say(
        f"{hero.name} had brought {world.relic.label}, because it jingled softly and made every errand feel like a quest."
    )


def suspense(world: World) -> None:
    hero = world.hero
    companion = world.companion
    relic = world.relic
    assert hero and companion and relic
    _add_meme(hero, "curiosity", 1)
    _add_meme(hero, "suspense", 1)
    world.para()
    world.say(
        f"Then {relic.label} rolled away and slipped behind a pillar."
    )
    world.say(
        f"{hero.name} froze for a moment, because the corner was shadowy and the hall suddenly felt very quiet."
    )
    world.say(
        f"{companion.name} said, \"Stay close. We'll find it together.\""
    )


def bravery(world: World) -> None:
    hero = world.hero
    companion = world.companion
    relic = world.relic
    assert hero and companion and relic
    _add_meme(hero, "bravery", 1)
    _add_meter(hero, "steps", 3)
    world.say(
        f"{hero.name} took a breath, walked to the pillar, and peered around it."
    )
    world.say(
        f"With a brave little reach, {hero.pronoun()} found {relic.label} tucked in the dust and picked it up."
    )
    relic.found = True
    _add_meme(companion, "relief", 1)


def reconciliation(world: World) -> None:
    hero = world.hero
    companion = world.companion
    relic = world.relic
    assert hero and companion and relic
    _add_meme(hero, "reconciliation", 1)
    _add_meme(companion, "reconciliation", 1)
    world.para()
    world.say(
        f"{hero.name} gave the bell to {companion.name}, then smiled and said sorry for rushing ahead."
    )
    world.say(
        f"{companion.name} smiled back and said it was all right, because helping each other was the best part of the adventure."
    )
    world.say(
        f"Together they listened to the soft jingle of {relic.label}, and the tavern felt warm and safe again."
    )


def tell_story(params: StoryParams) -> World:
    world = World(PLACES[params.place])
    hero = Character(name=params.hero_name, role=params.hero_role)
    companion = Character(name=params.companion_name, role=params.companion_role)
    world.hero = hero
    world.companion = companion
    world.facts["hero"] = hero
    world.facts["companion"] = companion
    world.facts["place"] = world.place
    introduce(world)
    setup_relic(world)
    suspense(world)
    bravery(world)
    reconciliation(world)
    return world


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------

ASP_RULES = r"""
place(tavern).
character(hero).
character(companion).
feature(bravery).
feature(suspense).
feature(reconciliation).

% A tavern adventure is reasonable if it has a place, a suspenseful loss,
% a brave recovery, and a gentle reconciliation.
adventure_story(tavern) :- place(tavern), feature(bravery), feature(suspense), feature(reconciliation).

#show adventure_story/1.
"""


def asp_facts() -> str:
    import asp
    lines = [asp.fact("place", "tavern")]
    lines.append(asp.fact("feature", "bravery"))
    lines.append(asp.fact("feature", "suspense"))
    lines.append(asp.fact("feature", "reconciliation"))
    lines.append(asp.fact("seed_word", "pillar"))
    lines.append(asp.fact("seed_word", "energetic"))
    lines.append(asp.fact("seed_word", "tavern"))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show adventure_story/1."))
    atoms = set(asp.atoms(model, "adventure_story"))
    python_ok = {("tavern",)}
    if atoms == python_ok:
        print("OK: ASP parity matches the Python reasonableness gate.")
        return 0
    print("MISMATCH between ASP and Python reasonableness gate.")
    print("ASP:", sorted(atoms))
    print("PY :", sorted(python_ok))
    return 1


# ---------------------------------------------------------------------------
# QA
# ---------------------------------------------------------------------------

def generation_prompts(world: World) -> list[str]:
    return [
        'Write a short adventure story that includes an energetic child, a pillar, and a tavern.',
        f"Tell a gentle story where {world.hero.name} loses something near a pillar and shows bravery.",
        "Write a child-friendly story with suspense and a happy reconciliation at the end.",
    ]


def story_qa(world: World) -> list[QAItem]:
    hero = world.hero
    companion = world.companion
    relic = world.relic
    assert hero and companion and relic
    return [
        QAItem(
            question=f"Who is the energetic child in the story?",
            answer=f"The energetic child is {hero.name}, a little {hero.role} who loves adventure.",
        ),
        QAItem(
            question=f"What did {hero.name} lose near the pillar?",
            answer=f"{hero.name} lost {relic.label} behind a pillar in the tavern.",
        ),
        QAItem(
            question=f"How did {hero.name} show bravery?",
            answer=f"{hero.name} showed bravery by taking a breath, going to the pillar, and reaching for the bell even though the corner felt shadowy.",
        ),
        QAItem(
            question=f"How did the story end?",
            answer=f"The story ended with {hero.name} and {companion.name} making up, smiling, and listening to the bell together.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a pillar?",
            answer="A pillar is a tall strong column that helps hold up a building or makes a room look grand.",
        ),
        QAItem(
            question="What is a tavern?",
            answer="A tavern is a place where people can sit, eat, drink, and rest in a cozy room.",
        ),
        QAItem(
            question="What does energetic mean?",
            answer="Energetic means full of lively movement and excitement, like someone who likes to hurry, hop, and explore.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== (2) Story questions ==")
    for q in sample.story_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    lines.append("")
    lines.append("== (3) World knowledge questions ==")
    for q in sample.world_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Reasonableness gate
# ---------------------------------------------------------------------------

def valid_combos() -> list[tuple[str, str, str]]:
    return [("tavern", "bravery", "reconciliation")]


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A gentle tavern adventure storyworld.")
    ap.add_argument("--place", choices=PLACES.keys())
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("-n", type=int, default=1)
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--trace", action="store_true")
    ap.add_argument("--qa", action="store_true")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--asp", action="store_true")
    ap.add_argument("--verify", action="store_true")
    ap.add_argument("--show-asp", action="store_true")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    place = args.place or "tavern"
    if place != "tavern":
        raise StoryError("This storyworld only supports the tavern setting.")
    hero_role = rng.choice(["boy", "girl"])
    companion_role = "girl" if hero_role == "boy" else "boy"
    hero_name = rng.choice(HERO_NAMES_BOY if hero_role == "boy" else HERO_NAMES_GIRL)
    companion_name = rng.choice(HERO_NAMES_GIRL if companion_role == "girl" else HERO_NAMES_BOY)
    return StoryParams(
        place=place,
        hero_name=hero_name,
        hero_role=hero_role,
        companion_name=companion_name,
        companion_role=companion_role,
    )


def dump_trace(sample: StorySample) -> str:
    world = sample.world
    if world is None:
        return ""
    lines = ["--- world trace ---"]
    for ent in [world.hero, world.companion]:
        if ent is None:
            continue
        lines.append(f"{ent.name}: meters={ent.meters} memes={ent.memes}")
    if world.relic is not None:
        lines.append(f"{world.relic.label}: found={world.relic.found} location={world.relic.location}")
    lines.append(f"place: {world.place.name}")
    return "\n".join(lines)


def generate(params: StoryParams) -> StorySample:
    world = tell_story(params)
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
        print(dump_trace(sample))
    if qa:
        print()
        print(format_qa(sample))


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show adventure_story/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        model = asp.one_model(asp_program("#show adventure_story/1."))
        print(asp.atoms(model, "adventure_story"))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)

    samples: list[StorySample] = []
    if args.all:
        params = StoryParams(place="tavern", hero_name="Milo", hero_role="boy", companion_name="Lina", companion_role="girl", seed=base_seed)
        samples = [generate(params)]
    else:
        for i in range(max(1, args.n)):
            rng = random.Random(base_seed + i)
            try:
                params = resolve_params(args, rng)
            except StoryError as e:
                print(str(e))
                return
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

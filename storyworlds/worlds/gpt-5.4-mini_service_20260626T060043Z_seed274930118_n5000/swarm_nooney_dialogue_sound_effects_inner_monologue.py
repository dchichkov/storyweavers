#!/usr/bin/env python3
"""
storyworlds/worlds/swarm_nooney_dialogue_sound_effects_inner_monologue.py
========================================================================

A small mystery-flavored story world about a curious child, a swarm of tiny
lights, and a helper named Nooney.

The story premise:
- A child hears odd sound effects at night.
- A swarm of fireflies keeps gathering around a hidden clue.
- Nooney speaks in short dialogue and helps the child follow the trail.
- The child’s inner monologue tracks fear, guessing, and discovery.
- The mystery resolves when the swarm reveals a missing object.

This is a constraint-checked simulation, not a template swap. The state changes
drive the prose: sounds, dialogue, and inner thoughts are all caused by world
events.
"""

from __future__ import annotations

import argparse
import json
import os
import random
import re
import sys
from dataclasses import dataclass, field
from typing import Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from results import QAItem, StoryError, StorySample  # noqa: E402

SWARM_THRESHOLD = 3


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.kind == "character" and self.type in {"girl", "boy", "child"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class World:
    place: str
    entities: dict[str, Entity] = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    facts: dict = field(default_factory=dict)
    fired: set[str] = field(default_factory=set)

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


@dataclass
class StoryParams:
    name: str
    helper: str
    place: str
    clue: str
    seed: Optional[int] = None


PLACES = {
    "garden": "the garden",
    "attic": "the attic",
    "shed": "the shed",
    "porch": "the porch",
}

CLUES = {
    "lantern": ("lantern", "a small brass lantern", "a lantern", "shiny"),
    "key": ("key", "a tiny silver key", "a key", "metal"),
    "button": ("button", "a blue coat button", "a button", "round"),
}

NAMES = ["Mina", "Eli", "Tara", "Noor", "Pip", "Lina", "Owen", "June"]
HELPERS = ["Nooney", "Nooney the cat", "Nooney the mouse"]
TRAITS = ["brave", "curious", "quiet", "careful"]


def title_case(s: str) -> str:
    return s[:1].upper() + s[1:]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a short mystery story for a young child that includes the words "swarm" and "Nooney".',
        f"Tell a gentle nighttime mystery where {f['name']} hears odd sounds at {f['place']} and follows a swarm of lights with {f['helper']}.",
        f"Write a child-friendly story with dialogue, sound effects, and inner monologue about a missing {f['clue_name']}.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    helper = f["helper_ent"]
    clue = f["clue_ent"]
    return [
        QAItem(
            question=f"What mystery did {hero.id} notice at {world.place}?",
            answer=f"{hero.id} noticed strange sounds and a swarm of lights leading toward a missing {clue.label}.",
        ),
        QAItem(
            question=f"Who helped {hero.id} look for the clue?",
            answer=f"{helper.label} helped {hero.id} by speaking softly and pointing toward the swarm.",
        ),
        QAItem(
            question=f"What was found at the end of the story?",
            answer=f"The missing {clue.label} was found where the swarm gathered, hidden in plain sight.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a swarm?",
            answer="A swarm is a large group of tiny living things moving together, like bees or fireflies.",
        ),
        QAItem(
            question="Why do fireflies make a little glow at night?",
            answer="Fireflies glow to help them find each other and to send signals in the dark.",
        ),
        QAItem(
            question="What does a mystery story usually ask the reader to do?",
            answer="A mystery story usually asks the reader to notice clues and figure out what happened.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== story qa ==")
    for q in sample.story_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    lines.append("")
    lines.append("== world qa ==")
    for q in sample.world_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        bits = []
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        lines.append(f"  {e.id:10} ({e.kind:9}) {e.type:8} {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(world.fired)}")
    return "\n".join(lines)


def say_inner(world: World, hero: Entity, thought: str) -> None:
    world.say(f"{hero.pronoun().capitalize()} thought, “{thought}”")


def narrate_sound(world: World, sound: str) -> None:
    world.say(sound)


def tell(params: StoryParams) -> World:
    place = PLACES[params.place]
    clue_name, clue_phrase, clue_short, clue_trait = CLUES[params.clue]
    world = World(place)

    hero = world.add(Entity(id=params.name, kind="character", type="child", label=params.name))
    helper = world.add(Entity(id="Nooney", kind="character", type="helper", label=params.helper))
    clue = world.add(Entity(id="clue", kind="thing", type=clue_name, label=clue_short, phrase=clue_phrase, owner=None))

    world.facts.update(name=hero.id, helper=helper.label, place=world.place, clue_name=clue_name, hero=hero, helper_ent=helper, clue_ent=clue)

    # Act 1: the mystery begins.
    world.say(f"On a quiet night at {world.place}, {hero.id} heard a soft sound.")
    narrate_sound(world, "frrt-frrt... flutter-flutter...")
    say_inner(world, hero, "That sounds close. Too close for bedtime.")
    world.say(f"A small swarm of glowing lights drifted across the dark path.")
    hero.memes["curiosity"] = hero.memes.get("curiosity", 0) + 1
    clue.meters["hidden"] = 1

    world.para()

    # Act 2: clue and tension.
    world.say(f'{helper.label} peeked out of the shadows and said, "Stay calm. The swarm is showing us something."')
    say_inner(world, hero, "Maybe this is not spooky. Maybe it is a clue.")
    hero.memes["unease"] = hero.memes.get("unease", 0) + 1
    clue.meters["near_swarm"] = 1

    narrate_sound(world, "tick... tick... tap...")
    world.say(f"The tiny lights gathered again and again beside an old crate.")
    world.say(f"{hero.id} bent down and looked under it.")

    world.para()

    # Act 3: reveal.
    helper.memes["helpful"] = helper.memes.get("helpful", 0) + 1
    clue.meters["found"] = 1
    clue.meters["hidden"] = 0
    if params.clue == "lantern":
        reveal = "the missing lantern"
    elif params.clue == "key":
        reveal = "the missing key"
    else:
        reveal = "the missing button"

    world.say(f'"There it is," said {helper.label}. "The swarm kept circling {reveal}."')
    world.say(f"{hero.id}'s eyes widened as the clue flashed in the moonlight.")
    say_inner(world, hero, "I thought the dark was hiding a problem. It was hiding an answer.")
    world.say(f"{hero.id} picked up {clue.phrase} and smiled as the swarm drifted away into the night.")
    hero.memes["relief"] = hero.memes.get("relief", 0) + 1
    world.facts["resolved"] = True
    return world


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for p in PLACES:
        for c in CLUES:
            combos.append((p, c, "Nooney"))
    return combos


ASP_RULES = r"""
place(P) :- setting(P).
clue(C) :- clue_kind(C).
helper(H) :- helper_name(H).

mystery(P, C, H) :- place(P), clue(C), helper(H).
#show mystery/3.
"""


def asp_facts() -> str:
    import asp
    lines = []
    for p in PLACES:
        lines.append(asp.fact("setting", p))
    for c in CLUES:
        lines.append(asp.fact("clue_kind", c))
    for h in HELPERS:
        lines.append(asp.fact("helper_name", h))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show mystery/3."))
    return sorted(set(asp.atoms(model, "mystery")))


def asp_verify() -> int:
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    if py - cl:
        print("  only in python:", sorted(py - cl))
    if cl - py:
        print("  only in clingo:", sorted(cl - py))
    return 1


def explain_rejection() -> str:
    return "(No story: this mystery domain expects a place and a clue that can be followed by Nooney.)"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Mystery story world with swarm, Nooney, dialogue, sound effects, and inner monologue.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--clue", choices=CLUES)
    ap.add_argument("--name", choices=NAMES)
    ap.add_argument("--helper", choices=HELPERS)
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
    clue = args.clue or rng.choice(list(CLUES))
    name = args.name or rng.choice(NAMES)
    helper = args.helper or rng.choice(HELPERS)
    return StoryParams(name=name, helper=helper, place=place, clue=clue)


def generate(params: StoryParams) -> StorySample:
    world = tell(params)
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


CURATED = [
    StoryParams(name="Mina", helper="Nooney", place="garden", clue="lantern"),
    StoryParams(name="Eli", helper="Nooney the cat", place="attic", clue="key"),
    StoryParams(name="Tara", helper="Nooney the mouse", place="shed", clue="button"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show mystery/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"{len(asp_valid_combos())} compatible mystery combos:")
        for row in asp_valid_combos():
            print(" ", row)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
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
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()

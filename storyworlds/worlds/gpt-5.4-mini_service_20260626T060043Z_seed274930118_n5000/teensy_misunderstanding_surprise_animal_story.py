#!/usr/bin/env python3
"""
storyworlds/worlds/teensy_misunderstanding_surprise_animal_story.py
====================================================================

A small animal-story world about a teensy misunderstanding that turns into a
surprise.

The world model is intentionally simple but state-driven:
- an animal wants something small and shiny, or thinks another animal is taking
  something important;
- a mistaken guess raises worry and a little conflict;
- a surprise reveal changes the emotional state and ends with a concrete image.

This script follows the storyworld contract:
- self-contained stdlib script
- shared result containers imported eagerly
- optional ASP twin with inline rules
- generate / emit / main interface
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
@dataclass
class Animal:
    id: str
    species: str
    label: str
    size: str = "teensy"
    kind: str = "character"
    meters: dict[str, float] = field(default_factory=lambda: {"distance": 0.0, "mess": 0.0})
    memes: dict[str, float] = field(default_factory=lambda: {"joy": 0.0, "worry": 0.0, "confusion": 0.0, "surprise": 0.0, "affection": 0.0})

    def pronoun(self, case: str = "subject") -> str:
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class Place:
    id: str
    label: str
    cozy: bool = False
    affords: set[str] = field(default_factory=set)


@dataclass
class Item:
    id: str
    label: str
    phrase: str
    tiny: bool = True
    fragile: bool = False
    owner: Optional[str] = None
    carried_by: Optional[str] = None
    hidden: bool = False
    revealed: bool = False
    meters: dict[str, float] = field(default_factory=lambda: {"safe": 0.0, "seen": 0.0})


@dataclass
class StoryParams:
    place: str
    hero_species: str
    helper_species: str
    item: str
    surprise: str
    seed: Optional[int] = None


@dataclass
class World:
    place: Place
    hero: Animal
    helper: Animal
    item: Item
    surprise: str
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    facts: dict = field(default_factory=dict)
    fired: set[tuple] = field(default_factory=set)

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
        clone = World(
            place=copy.deepcopy(self.place),
            hero=copy.deepcopy(self.hero),
            helper=copy.deepcopy(self.helper),
            item=copy.deepcopy(self.item),
            surprise=self.surprise,
        )
        clone.paragraphs = [[]]
        clone.facts = dict(self.facts)
        clone.fired = set(self.fired)
        return clone


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------
PLACES = {
    "meadow": Place("meadow", "the meadow", affords={"hide", "carry", "reveal", "gather"}),
    "pond": Place("pond", "the pond", affords={"carry", "reveal", "gather"}),
    "burrow": Place("burrow", "the burrow", cozy=True, affords={"hide", "carry", "reveal"}),
    "orchard": Place("orchard", "the orchard", affords={"hide", "carry", "reveal", "gather"}),
    "barn": Place("barn", "the barn", cozy=True, affords={"hide", "carry", "reveal", "gather"}),
}

ANIMALS = {
    "mouse": {"label": "a mouse", "friendly": True},
    "rabbit": {"label": "a rabbit", "friendly": True},
    "squirrel": {"label": "a squirrel", "friendly": True},
    "duck": {"label": "a duck", "friendly": True},
    "fox": {"label": "a fox", "friendly": True},
    "chipmunk": {"label": "a chipmunk", "friendly": True},
}

ITEMS = {
    "acorn": Item("acorn", "acorn", "a shiny acorn", tiny=True, fragile=False),
    "berry": Item("berry", "berry bundle", "a little bundle of berries", tiny=True, fragile=True),
    "bell": Item("bell", "bell", "a tiny brass bell", tiny=True, fragile=False),
    "leaf": Item("leaf", "leaf card", "a folded leaf card", tiny=True, fragile=False),
    "scarf": Item("scarf", "scarf", "a soft scarf", tiny=True, fragile=True),
}

SURPRISES = {
    "gift": "a surprise gift",
    "picnic": "a surprise picnic",
    "song": "a surprise song",
    "hug": "a surprise hug",
    "party": "a surprise tea party",
}

SPECIES_NAMES = {
    "mouse": ["Milo", "Mimi", "Moss", "Mop", "Marnie"],
    "rabbit": ["Ruby", "Pip", "Poppy", "Rosie", "Roo"],
    "squirrel": ["Scout", "Sally", "Skip", "Saffy", "Sprig"],
    "duck": ["Dot", "Daisy", "Duke", "Dina", "Dawn"],
    "fox": ["Fin", "Fenn", "Foxy", "Flint", "Fable"],
    "chipmunk": ["Chip", "Clover", "Chime", "Coco", "Cinny"],
}

TRAITS = ["curious", "gentle", "playful", "bouncy", "shy", "cheerful"]


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
% A story is reasonable when the place supports hide/carry/reveal and the item
% is a teensy thing that can plausibly be hidden and then revealed.
reasonable_story(P, I, S) :- place(P), item(I), surprise(S),
                             affords(P, hide), affords(P, carry), affords(P, reveal).

% The misunderstanding happens when one animal sees the item hidden or carried,
% but the item is actually meant as a surprise.
misunderstanding(P, I) :- reasonable_story(P, I, _), tiny_item(I).

% The surprise can resolve the misunderstanding when the item is revealed.
resolves(P, I, S) :- misunderstanding(P, I), surprise_kind(S), revealable(I).

valid_story(P, I, S) :- reasonable_story(P, I, S), resolves(P, I, S).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid, p in PLACES.items():
        lines.append(asp.fact("place", pid))
        for a in sorted(p.affords):
            lines.append(asp.fact("affords", pid, a))
        if p.cozy:
            lines.append(asp.fact("cozy", pid))
    for iid, it in ITEMS.items():
        lines.append(asp.fact("item", iid))
        lines.append(asp.fact("tiny_item", iid))
        if it.fragile:
            lines.append(asp.fact("fragile", iid))
        if it.tiny:
            lines.append(asp.fact("tiny", iid))
        lines.append(asp.fact("revealable", iid))
    for sid in SURPRISES:
        lines.append(asp.fact("surprise_kind", sid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_stories() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/3."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    py = set(valid_stories())
    cl = set(asp_valid_stories())
    if py == cl:
        print(f"OK: clingo gate matches valid_stories() ({len(py)} stories).")
        return 0
    print("MISMATCH between clingo and valid_stories():")
    if cl - py:
        print("  only in clingo:", sorted(cl - py))
    if py - cl:
        print("  only in python:", sorted(py - cl))
    return 1


# ---------------------------------------------------------------------------
# Reasonableness gate
# ---------------------------------------------------------------------------
def valid_stories() -> list[tuple[str, str, str]]:
    out = []
    for pid, place in PLACES.items():
        if not {"hide", "carry", "reveal"}.issubset(place.affords):
            continue
        for iid in ITEMS:
            for sid in SURPRISES:
                out.append((pid, iid, sid))
    return out


def explain_invalid(place: str, item: str) -> str:
    p = PLACES[place]
    it = ITEMS[item]
    if not {"hide", "carry", "reveal"}.issubset(p.affords):
        return f"(No story: {p.label} cannot support the hide/carry/reveal sequence needed for a surprise.)"
    if not it.tiny:
        return f"(No story: {it.phrase} is not teensy enough to hide as a misunderstanding.)"
    return "(No story: the requested combination is not reasonable.)"


# ---------------------------------------------------------------------------
# Story helpers
# ---------------------------------------------------------------------------
def pick_name(species: str, rng: random.Random) -> str:
    return rng.choice(SPECIES_NAMES[species])


def make_world(params: StoryParams) -> World:
    place = PLACES[params.place]
    hero_name = params.hero_species.capitalize()
    helper_name = params.helper_species.capitalize()
    hero = Animal(id=pick_name(params.hero_species, random.Random((params.seed or 0) + 1)), species=params.hero_species, label=f"the {params.hero_species}")
    helper = Animal(id=pick_name(params.helper_species, random.Random((params.seed or 0) + 2)), species=params.helper_species, label=f"the {params.helper_species}")
    item = ITEMS[params.item]
    import copy
    item = copy.deepcopy(item)
    item.owner = helper.id
    return World(place=place, hero=hero, helper=helper, item=item, surprise=SURPRISES[params.surprise])


def setup(world: World) -> None:
    world.say(
        f"{world.hero.id} was a teensy {world.hero.species} who loved quiet walks near {world.place.label}."
    )
    world.say(
        f"{world.helper.id} was a {world.helper.species} friend who liked little plans and bright ideas."
    )
    world.say(
        f"One morning, {world.helper.id} had {world.item.phrase}, and {world.hero.id} noticed it right away."
    )


def misunderstanding_beats(world: World) -> None:
    world.para()
    world.item.hidden = True
    world.hero.memes["confusion"] += 1
    world.hero.memes["worry"] += 1
    world.hero.meters["distance"] += 1
    world.say(
        f"When {world.helper.id} tucked {world.item.phrase} behind a leaf, {world.hero.id} thought it was being taken away."
    )
    world.say(
        f"{world.hero.id} frowned and moved closer, because the teensy shape looked important and the hiding place looked secret."
    )
    world.say(
        f"{world.hero.id} whispered, 'Wait, is that for someone else?'"
    )


def turn_reveal(world: World) -> None:
    world.para()
    world.item.hidden = False
    world.item.revealed = True
    world.hero.memes["surprise"] += 1
    world.hero.memes["confusion"] = 0.0
    world.hero.memes["worry"] = 0.0
    world.hero.memes["joy"] += 1
    world.helper.memes["affection"] += 1
    world.say(
        f"{world.helper.id} giggled and lifted the leaf. 'No,' {world.helper.id} said. 'It was a surprise for you.'"
    )
    world.say(
        f"Inside was {world.surprise}, and it was made just for {world.hero.id}."
    )
    world.say(
        f"{world.hero.id}'s ears perked up, and the little frown turned into a bright smile."
    )


def ending(world: World) -> None:
    world.para()
    world.say(
        f"Soon {world.hero.id} was sitting beside {world.helper.id}, holding the teensy treasure carefully while the breeze moved through {world.place.label}."
    )
    world.say(
        f"What had looked like a mistake was really a surprise, and the two friends shared it with happy, shining faces."
    )


def tell_story(params: StoryParams) -> World:
    world = make_world(params)
    setup(world)
    misunderstanding_beats(world)
    turn_reveal(world)
    ending(world)
    world.facts = {
        "place": params.place,
        "item": params.item,
        "surprise": params.surprise,
        "hero": world.hero,
        "helper": world.helper,
    }
    return world


# ---------------------------------------------------------------------------
# Q&A
# ---------------------------------------------------------------------------
def generation_prompts(world: World) -> list[str]:
    return [
        f"Write a short animal story about a teensy misunderstanding at {world.place.label} that ends in a surprise.",
        f"Tell a gentle story where {world.hero.id} thinks {world.helper.id} is taking a tiny thing, but the truth is a surprise.",
        f"Write a child-friendly story with a small animal, a secret hiding place, and a happy reveal.",
    ]


def story_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question=f"Why did {world.hero.id} worry when {world.helper.id} hid the teensy item?",
            answer=f"{world.hero.id} thought {world.helper.id} was taking {world.item.phrase} away for good, so the hiding place felt like a misunderstanding.",
        ),
        QAItem(
            question=f"What was the surprise in the story?",
            answer=f"The surprise was {world.surprise}, and it was meant for {world.hero.id}.",
        ),
        QAItem(
            question=f"How did the story end?",
            answer=f"It ended with {world.hero.id} smiling beside {world.helper.id} after learning the hidden item was a surprise.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does it mean when something is hidden?",
            answer="When something is hidden, it is put out of sight for a little while so someone may not see it right away.",
        ),
        QAItem(
            question="What is a surprise?",
            answer="A surprise is something nice or exciting that you do not expect until it is shown or said.",
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
    for ent in [world.hero, world.helper]:
        lines.append(f"  {ent.id:8} ({ent.species:9}) meters={dict(ent.meters)} memes={dict(ent.memes)}")
    lines.append(f"  item     ({world.item.id:9}) hidden={world.item.hidden} revealed={world.item.revealed}")
    lines.append(f"  place    ({world.place.id:9}) affords={sorted(world.place.affords)}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Teensy animal misunderstanding with a surprise ending.")
    ap.add_argument("--place", choices=sorted(PLACES))
    ap.add_argument("--item", choices=sorted(ITEMS))
    ap.add_argument("--surprise", choices=sorted(SURPRISES))
    ap.add_argument("--hero-species", choices=sorted(ANIMALS))
    ap.add_argument("--helper-species", choices=sorted(ANIMALS))
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
    if args.place and args.item:
        if (args.place, args.item, args.surprise or "gift") not in valid_stories():
            raise StoryError(explain_invalid(args.place, args.item))
    combos = valid_stories()
    if args.place:
        combos = [c for c in combos if c[0] == args.place]
    if args.item:
        combos = [c for c in combos if c[1] == args.item]
    if args.surprise:
        combos = [c for c in combos if c[2] == args.surprise]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, item, surprise = rng.choice(sorted(combos))
    hero_species = args.hero_species or rng.choice(sorted(ANIMALS))
    helper_species = args.helper_species or rng.choice([s for s in sorted(ANIMALS) if s != hero_species])
    return StoryParams(place=place, hero_species=hero_species, helper_species=helper_species, item=item, surprise=surprise)


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
        print(dump_trace(sample.world))
    if qa:
        print()
        print(format_qa(sample))


def asp_facts_stub() -> str:
    return asp_facts()


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid_story/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        model = asp.one_model(asp_program("#show valid_story/3."))
        triples = sorted(set(asp.atoms(model, "valid_story")))
        print(f"{len(triples)} compatible stories:\n")
        for p, i, s in triples:
            print(f"  {p:8} {i:8} {s:8}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        for place, item, surprise in valid_stories():
            params = StoryParams(
                place=place,
                hero_species="mouse",
                helper_species="rabbit",
                item=item,
                surprise=surprise,
                seed=base_seed,
            )
            samples.append(generate(params))
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 50, 50):
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

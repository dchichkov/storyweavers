#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260624T081143Z_seed2038046945_n100/frolic_wake_thong_reconciliation_problem_solving_conflict.py
===========================================================================================================================

A small whodunit-style storyworld about a vanished thong, a morning wake-up,
and a frolic that turns into conflict before reconciliation and problem solving.

The domain is intentionally tiny: a child, a guardian, a misplaced object,
and a clue trail that leads to a gentle mystery. The ending always proves what
changed in the world model.
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
# Core typed entities with meters and memes.
# ---------------------------------------------------------------------------
@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    keeper: Optional[str] = None
    location: str = ""
    hidden: bool = False
    worn: bool = False
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.meters:
            self.meters = {"distance": 0.0, "wear": 0.0}
        if not self.memes:
            self.memes = {"conflict": 0.0, "curiosity": 0.0, "relief": 0.0, "joy": 0.0}

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "woman", "mother", "aunt"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man", "father", "uncle"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Place:
    name: str
    cluey: bool = True


@dataclass
class Item:
    id: str
    label: str
    phrase: str
    type: str
    owner: str
    hidden_spot: str
    location: str = "bedroom"
    found: bool = False
    plural: bool = False


@dataclass
class StoryParams:
    place: str
    hero_name: str
    hero_type: str
    guardian_type: str
    item: str
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# World model.
# ---------------------------------------------------------------------------
class World:
    def __init__(self, place: Place) -> None:
        self.place = place
        self.entities: dict[str, Entity] = {}
        self.items: dict[str, Item] = {}
        self.lines: list[str] = []
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict[str, object] = {}

    def add_entity(self, e: Entity) -> Entity:
        self.entities[e.id] = e
        return e

    def add_item(self, it: Item) -> Item:
        self.items[it.id] = it
        return it

    def get(self, eid: str) -> Entity:
        return self.entities[eid]

    def say(self, text: str) -> None:
        self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)


# ---------------------------------------------------------------------------
# Registries.
# ---------------------------------------------------------------------------
PLACES = {
    "wake_house": Place("the wake house"),
    "garden": Place("the garden"),
    "dock": Place("the dock"),
    "hall": Place("the old hall"),
}

ITEMS = {
    "thong": Item(
        id="thong",
        label="thong",
        phrase="a small red thong",
        type="thong",
        owner="hero",
        hidden_spot="under a cushion",
    ),
    "ribbon": Item(
        id="ribbon",
        label="ribbon",
        phrase="a blue ribbon",
        type="ribbon",
        owner="hero",
        hidden_spot="inside a book",
    ),
}

NAMES = ["Mia", "Nina", "Theo", "Eli", "Ava", "Noah"]
TRAITS = ["bright-eyed", "curious", "careful", "lively", "gentle"]


# ---------------------------------------------------------------------------
# Story logic.
# ---------------------------------------------------------------------------
def build_story(world: World, params: StoryParams) -> None:
    hero = world.add_entity(Entity(id="hero", kind="character", type=params.hero_type, label=params.hero_name))
    guardian = world.add_entity(Entity(id="guardian", kind="character", type=params.guardian_type, label="the guardian"))
    item_template = ITEMS[params.item]
    item = world.add_item(Item(**{**item_template.__dict__}))
    item.owner = hero.id

    world.facts.update(hero=hero, guardian=guardian, item=item, place=world.place)

    hero.memes["curiosity"] += 1
    world.say(
        f"{hero.label} woke early at {world.place.name}, because the house felt full of quiet clues."
    )
    world.say(
        f"{hero.pronoun().capitalize()} wanted a frolic outside, but first {hero.pronoun('possessive')} eyes went missing "
        f"when the small {item.label} could not be found."
    )

    world.para()
    hero.memes["conflict"] += 1
    world.say(
        f"{guardian.label.capitalize()} noticed the fuss. \"What happened at wake-up?\" {guardian.pronoun()} asked, "
        f"while {hero.label} searched the chairs, the table, and the rug."
    )
    item.location = item.hidden_spot
    world.say(
        f"The clue was tiny: a corner of red cloth peeking from {item.hidden_spot}. That seemed odd, because "
        f"the room had been tidy before the frolic."
    )

    world.para()
    world.say(
        f"{hero.label} and {guardian.label} followed the clue together, lifting the cushion and then the blanket."
    )
    item.found = True
    item.location = "hero's hand"
    hero.memes["conflict"] = 0.0
    hero.memes["relief"] += 1
    hero.memes["joy"] += 1
    world.say(
        f"At last, the {item.label} was found. It had slipped where no one looked, and the mystery was solved."
    )
    world.say(
        f"{guardian.label.capitalize()} smiled and said they could still frolic later, now that the missing thing was safe."
    )

    world.para()
    world.say(
        f"{hero.label} grinned, tucked the {item.label} away, and ran outside with {guardian.label}. "
        f"The morning ended in reconciliation instead of quarrel, and the yard felt bright again."
    )


# ---------------------------------------------------------------------------
# Q&A and formatting.
# ---------------------------------------------------------------------------
def prompts_for(world: World) -> list[str]:
    hero: Entity = world.facts["hero"]  # type: ignore[assignment]
    item: Item = world.facts["item"]  # type: ignore[assignment]
    place: Place = world.facts["place"]  # type: ignore[assignment]
    return [
        f'Write a child-friendly whodunit about a lost {item.label} at {place.name} with a gentle ending.',
        f"Tell a short story where {hero.label} wakes up, a missing {item.label} causes conflict, and the mystery is solved.",
        "Write a tiny mystery that includes frolic, wake, and thong, and ends with reconciliation.",
    ]


def story_qa(world: World) -> list[QAItem]:
    hero: Entity = world.facts["hero"]  # type: ignore[assignment]
    guardian: Entity = world.facts["guardian"]  # type: ignore[assignment]
    item: Item = world.facts["item"]  # type: ignore[assignment]
    place: Place = world.facts["place"]  # type: ignore[assignment]
    return [
        QAItem(
            question=f"Why did {hero.label} feel upset at {place.name}?",
            answer=f"{hero.label} felt upset because the {item.label} was missing, and that turned the morning into a little mystery.",
        ),
        QAItem(
            question=f"How was the missing {item.label} found?",
            answer=f"The {item.label} was found by following a tiny clue to {item.hidden_spot}, where it had slipped out of sight.",
        ),
        QAItem(
            question=f"How did the story end between {hero.label} and {guardian.label}?",
            answer=f"It ended in reconciliation: they found the {item.label}, calmed down, and went out together for a frolic.",
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a whodunit story?",
            answer="A whodunit is a mystery story where someone tries to figure out what happened and who or what caused the trouble.",
        ),
        QAItem(
            question="What does reconciliation mean?",
            answer="Reconciliation means people stop arguing, make peace, and feel friendly again.",
        ),
        QAItem(
            question="What does problem solving mean?",
            answer="Problem solving means looking carefully at a trouble and finding a smart way to fix it.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    out = ["== prompts =="]
    for p in sample.prompts:
        out.append(p)
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
# Parameters and generation.
# ---------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Whodunit-style frolic/wake/thong storyworld.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--hero-name")
    ap.add_argument("--hero-type", choices=["girl", "boy"])
    ap.add_argument("--guardian-type", choices=["mother", "father", "aunt", "uncle"])
    ap.add_argument("--item", choices=ITEMS)
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
    hero_type = args.hero_type or rng.choice(["girl", "boy"])
    guardian_type = args.guardian_type or rng.choice(["mother", "father", "aunt", "uncle"])
    item = args.item or rng.choice(list(ITEMS))
    hero_name = args.hero_name or rng.choice(NAMES)
    return StoryParams(place=place, hero_name=hero_name, hero_type=hero_type, guardian_type=guardian_type, item=item)


def generate(params: StoryParams) -> StorySample:
    world = World(PLACES[params.place])
    build_story(world, params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=prompts_for(world),
        story_qa=story_qa(world),
        world_qa=world_qa(world),
        world=world,
    )


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world is not None:
        print()
        print(dump_trace(sample.world))
    if qa:
        print()
        print(format_qa(sample))


def dump_trace(world: World) -> str:
    lines = ["--- trace ---"]
    for e in world.entities.values():
        lines.append(f"{e.id}: type={e.type} location={e.location} memes={e.memes}")
    for it in world.items.values():
        lines.append(f"{it.id}: found={it.found} location={it.location}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# ASP twin and verification.
# ---------------------------------------------------------------------------
ASP_RULES = r"""
place(P) :- setting(P).
item(I) :- thing(I).
problem_missing(I) :- item(I), hidden(I).
conflict(hero) :- problem_missing(thong).
solved(I) :- problem_missing(I), found(I).
reconciliation(hero) :- conflict(hero), solved(thong).
#show conflict/1.
#show reconciliation/1.
#show solved/1.
"""


def asp_facts() -> str:
    import storyworlds.asp as asp
    lines = []
    for pid in PLACES:
        lines.append(asp.fact("setting", pid))
    for iid, item in ITEMS.items():
        lines.append(asp.fact("thing", iid))
        lines.append(asp.fact("hidden", iid) if item.hidden_spot else asp.fact("visible", iid))
    lines.append(asp.fact("thong_is_seed_word", "frolic"))
    lines.append(asp.fact("thong_is_seed_word", "wake"))
    lines.append(asp.fact("thong_is_seed_word", "thong"))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import storyworlds.asp as asp
    model = asp.one_model(asp_program("#show conflict/1.\n#show reconciliation/1.\n#show solved/1."))
    atoms = {sym.name for sym in model}
    required = {"conflict", "reconciliation"}
    if required.issubset(atoms):
        print("OK: ASP twin emits the expected whodunit resolution atoms.")
        return 0
    print("MISMATCH: ASP twin did not derive expected atoms.")
    return 1


# ---------------------------------------------------------------------------
# CLI.
# ---------------------------------------------------------------------------
CURATED = [
    StoryParams(place="wake_house", hero_name="Mia", hero_type="girl", guardian_type="mother", item="thong"),
    StoryParams(place="garden", hero_name="Theo", hero_type="boy", guardian_type="father", item="ribbon"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show conflict/1.\n#show reconciliation/1.\n#show solved/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import storyworlds.asp as asp
        model = asp.one_model(asp_program("#show conflict/1.\n#show reconciliation/1.\n#show solved/1."))
        print([str(sym) for sym in model])
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        for i in range(args.n):
            rng = random.Random(base_seed + i)
            params = resolve_params(args, rng)
            params.seed = base_seed + i
            samples.append(generate(params))

    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        header = f"### variant {i+1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()

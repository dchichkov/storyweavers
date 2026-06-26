#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260626T060043Z_seed274930118_n5000/strap_measly_mystery_to_solve_detective_story.py
================================================================================================

A small detective-story world about a measly clue and a strap that matters.

Premise:
- A child detective notices a tiny mystery in a familiar place.
- The mystery centers on a missing strap or a loosened strap on an ordinary object.
- A helper worries because the clue is so measly that it is easy to overlook.

Turn:
- The detective follows concrete clues in the room, notices a pattern, and learns
  that the small strap detail explains the strange behavior.

Resolution:
- The mystery is solved through observation and a simple fix.
- The ending proves what changed: the object is secured, the worry fades, and
  the detective gets credit for paying attention to the measly clue.
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


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    wears: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

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
    id: str
    label: str
    places: set[str] = field(default_factory=set)
    clues: set[str] = field(default_factory=set)


@dataclass
class Item:
    id: str
    label: str
    phrase: str
    strap_kind: str
    place: str
    owner_types: set[str] = field(default_factory=lambda: {"girl", "boy"})


@dataclass
class StoryParams:
    place: str
    item: str
    clue: str
    name: str
    gender: str
    helper: str
    trait: str
    seed: Optional[int] = None


@dataclass
class World:
    place: Place
    entities: dict[str, Entity] = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    facts: dict = field(default_factory=dict)
    fired: set[tuple] = field(default_factory=set)
    trace: list[str] = field(default_factory=list)

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str) -> Entity:
        return self.entities[eid]

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)
            self.trace.append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)

    def copy(self) -> "World":
        import copy
        w = World(self.place)
        w.entities = copy.deepcopy(self.entities)
        w.paragraphs = [[]]
        w.facts = dict(self.facts)
        w.fired = set(self.fired)
        return w


PLACES = {
    "hall": Place(id="hall", label="the school hall", places={"hall"}, clues={"strap", "shoe", "coat"}),
    "classroom": Place(id="classroom", label="the classroom", places={"classroom"}, clues={"strap", "desk", "bag"}),
    "library": Place(id="library", label="the library", places={"library"}, clues={"strap", "book", "ladder"}),
    "kitchen": Place(id="kitchen", label="the kitchen", places={"kitchen"}, clues={"strap", "lunch", "tray"}),
}

ITEMS = {
    "bag": Item(id="bag", label="bag", phrase="a small blue bag with a floppy strap", strap_kind="bag strap", place="hall"),
    "satchel": Item(id="satchel", label="satchel", phrase="a brown satchel with one loose strap", strap_kind="satchel strap", place="classroom"),
    "coat": Item(id="coat", label="coat", phrase="a tiny coat with a hanging strap loop", strap_kind="coat strap", place="library"),
    "bin": Item(id="bin", label="bin", phrase="a little tin bin with a bent strap handle", strap_kind="handle strap", place="kitchen"),
}

TRAITS = ["curious", "careful", "quick-eyed", "steady", "patient", "bright"]
GIRL_NAMES = ["Mina", "Lena", "Tia", "Nora", "Ivy", "Zara"]
BOY_NAMES = ["Ben", "Owen", "Milo", "Eli", "Noah", "Theo"]
HELPERS = ["teacher", "librarian", "cook", "hall monitor"]


def valid_combos() -> list[tuple[str, str, str]]:
    out = []
    for place_id, place in PLACES.items():
        for item_id, item in ITEMS.items():
            if place_id == item.place:
                for clue in place.clues:
                    out.append((place_id, item_id, clue))
    return out


def invalid_reason(place_id: str, item_id: str) -> str:
    return (f"(No story: {ITEMS[item_id].phrase} belongs in {ITEMS[item_id].place}, "
            f"so it doesn't fit a mystery set in {PLACES[place_id].label}.)")


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A tiny detective story world about a measly clue and a strap.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--item", choices=ITEMS)
    ap.add_argument("--clue")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--name")
    ap.add_argument("--helper", choices=HELPERS)
    ap.add_argument("--trait", choices=TRAITS)
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
    if args.place and args.item:
        if args.place != ITEMS[args.item].place:
            raise StoryError(invalid_reason(args.place, args.item))
    combos = [c for c in valid_combos()
              if (args.place is None or c[0] == args.place)
              and (args.item is None or c[1] == args.item)
              and (args.clue is None or c[2] == args.clue)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, item, clue = rng.choice(sorted(combos))
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    helper = args.helper or rng.choice(HELPERS)
    trait = args.trait or rng.choice(TRAITS)
    return StoryParams(place=place, item=item, clue=clue, name=name, gender=gender, helper=helper, trait=trait)


def _setup(world: World, hero: Entity, helper: Entity, item: Entity) -> None:
    world.say(f"{hero.id} was a {hero.pronoun('possessive')} {hero.memes.get('trait', 'young')} little detective who liked noticing tiny things.")
    world.say(f"{hero.id} kept a notebook, a pencil, and a very serious face for mysteries.")
    world.say(f"One day, {helper.label} showed {hero.pronoun('object')} {item.phrase}.")
    world.say(f"{hero.id} thought the {item.label} looked ordinary, but something about the strap felt measly and wrong.")


def _clue(world: World, hero: Entity, helper: Entity, item: Entity, clue: str) -> None:
    hero.memes["curiosity"] = hero.memes.get("curiosity", 0) + 1
    world.say(f"In {world.place.label}, {hero.id} looked near the {clue} first.")
    world.say(f"{hero.pronoun().capitalize()} noticed that the strap had slipped behind a corner and made the item wobble.")
    world.say(f"That tiny problem explained why the {item.label} had seemed so strange.")
    world.say(f"{helper.label} frowned and said the mistake looked measly, but {hero.id} knew small clues could matter most.")


def _solve(world: World, hero: Entity, helper: Entity, item: Entity) -> None:
    world.say(f"{hero.id} tugged the strap back into place and tied it snugly.")
    world.say(f"At once, the {item.label} sat still instead of slipping and swinging.")
    world.say(f"{helper.label} smiled, because the mystery was solved by careful eyes and one small fix.")
    world.say(f"{hero.id} wrote the answer in {hero.pronoun('possessive')} notebook and grinned at the tidy result.")


def generate_world(params: StoryParams) -> World:
    place = PLACES[params.place]
    world = World(place=place)
    hero = world.add(Entity(id=params.name, kind="character", type=params.gender, memes={"trait": params.trait}))
    helper = world.add(Entity(id="Helper", kind="character", type="adult", label=params.helper))
    item = world.add(Entity(id="Item", kind="thing", type="thing", label=ITEMS[params.item].label, phrase=ITEMS[params.item].phrase, owner=helper.id))
    _setup(world, hero, helper, item)
    world.para()
    _clue(world, hero, helper, item, params.clue)
    world.para()
    _solve(world, hero, helper, item)
    world.facts.update(hero=hero, helper=helper, item=item, clue=params.clue, place=place, params=params)
    return world


def generation_prompts(world: World) -> list[str]:
    p = world.facts["params"]
    item = ITEMS[p.item]
    return [
        f'Write a short detective story for a child where the word "{p.clue}" helps solve a mystery about a strap.',
        f"Tell a gentle mystery where {p.name}, a {p.trait} {p.gender}, notices that {item.phrase} is not quite right.",
        f"Make a simple story about a measly clue, a missing strap feeling, and a happy solution.",
    ]


def story_qa(world: World) -> list[QAItem]:
    p = world.facts["params"]
    hero = world.facts["hero"]
    helper = world.facts["helper"]
    item = world.facts["item"]
    return [
        QAItem(
            question=f"Who solved the mystery in {world.place.label}?",
            answer=f"{hero.id} solved it by noticing the strap and checking the little clue carefully."
        ),
        QAItem(
            question=f"What was measly about the mystery?",
            answer=f"The measly part was that the strap had slipped a little, but that tiny detail was enough to explain the problem."
        ),
        QAItem(
            question=f"What did {helper.label} show {hero.id}?",
            answer=f"{helper.label} showed {hero.pronoun('object')} {item.phrase}."
        ),
        QAItem(
            question=f"How did the story end?",
            answer=f"The strap was tied snugly, the {ITEMS[p.item].label} stayed steady, and the mystery was solved."
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a detective for?",
            answer="A detective looks for clues and tries to explain a mystery by paying close attention."
        ),
        QAItem(
            question="What is a strap?",
            answer="A strap is a long narrow strip that can help hold, carry, or fasten something in place."
        ),
        QAItem(
            question="Why can a small clue matter?",
            answer="A small clue can matter because one tiny detail may explain what is really happening."
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
    for e in world.entities.values():
        bits = []
        if e.label:
            bits.append(f"label={e.label}")
        if e.phrase:
            bits.append(f"phrase={e.phrase}")
        if e.owner:
            bits.append(f"owner={e.owner}")
        if e.memes:
            bits.append(f"memes={dict(e.memes)}")
        lines.append(f"  {e.id:8} ({e.kind:7}) {' '.join(bits)}")
    lines.append(f"  place={world.place.label}")
    return "\n".join(lines)


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid, pl in PLACES.items():
        lines.append(asp.fact("place", pid))
        for c in sorted(pl.clues):
            lines.append(asp.fact("has_clue", pid, c))
    for iid, it in ITEMS.items():
        lines.append(asp.fact("item", iid))
        lines.append(asp.fact("item_in", iid, it.place))
        lines.append(asp.fact("strap_kind", iid, it.strap_kind))
    return "\n".join(lines)


ASP_RULES = r"""
valid_story(P, I, C) :- place(P), item(I), item_in(I, P), has_clue(P, C).
"""
def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/3."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    a = set(asp_valid_combos())
    b = set(valid_combos())
    if a == b:
        print(f"OK: clingo gate matches valid_combos() ({len(a)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    if a - b:
        print("  only in clingo:", sorted(a - b))
    if b - a:
        print("  only in python:", sorted(b - a))
    return 1


CURATED = [
    StoryParams(place="hall", item="bag", clue="shoe", name="Mina", gender="girl", helper="teacher", trait="quick-eyed"),
    StoryParams(place="classroom", item="satchel", clue="desk", name="Ben", gender="boy", helper="teacher", trait="careful"),
    StoryParams(place="library", item="coat", clue="book", name="Ivy", gender="girl", helper="librarian", trait="patient"),
    StoryParams(place="kitchen", item="bin", clue="tray", name="Theo", gender="boy", helper="cook", trait="steady"),
]


def generate(params: StoryParams) -> StorySample:
    world = generate_world(params)
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


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid_story/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (place, item, clue) combos:\n")
        for row in combos:
            print("  ", row)
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
            header = f"### {p.name}: {p.item} at {p.place}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()

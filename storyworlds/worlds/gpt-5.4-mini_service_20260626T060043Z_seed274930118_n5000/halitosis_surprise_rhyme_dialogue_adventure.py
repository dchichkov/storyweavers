#!/usr/bin/env python3
"""
Halitosis Surprise Rhyme Dialogue Adventure storyworld.

A small, child-facing adventure domain: a young explorer, a close friend, a
surprising case of halitosis, a rhyming clue, and a dialogue-driven fix.
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
# World entities
# ---------------------------------------------------------------------------
@dataclass
class Entity:
    id: str
    kind: str = "thing"   # character | thing
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "woman", "queen", "princess"}
        male = {"boy", "father", "man", "king", "prince"}
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
    indoors: bool = False
    sounds: list[str] = field(default_factory=list)
    clues: list[str] = field(default_factory=list)


@dataclass
class Item:
    id: str
    label: str
    phrase: str
    kind: str
    effect: str
    helpful: bool = False
    plural: bool = False


class World:
    def __init__(self, place: Place) -> None:
        self.place = place
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
        self.facts: dict = {}

    def add(self, e: Entity) -> Entity:
        self.entities[e.id] = e
        return e

    def get(self, eid: str) -> Entity:
        return self.entities[eid]

    def characters(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.kind == "character"]

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
        w = World(self.place)
        w.entities = copy.deepcopy(self.entities)
        w.paragraphs = [[]]
        w.fired = set(self.fired)
        w.facts = dict(self.facts)
        return w


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------
PLACES = {
    "forest_path": Place(
        id="forest_path",
        label="the forest path",
        indoors=False,
        sounds=["birds", "leaves", "boots on dirt"],
        clues=["a mossy stone", "a hollow log", "a fork in the trail"],
    ),
    "old_tower": Place(
        id="old_tower",
        label="the old tower",
        indoors=True,
        sounds=["stairs", "echoes", "wind through cracks"],
        clues=["a dusty map", "a small key", "a carved door"],
    ),
    "harbor": Place(
        id="harbor",
        label="the harbor",
        indoors=False,
        sounds=["waves", "ropes creaking", "gulls"],
        clues=["a fish crate", "a bright shell", "a rope bridge"],
    ),
}

ITEMS = {
    "mint_leaf": Item(
        id="mint_leaf",
        label="mint leaf",
        phrase="a tiny mint leaf",
        kind="leaf",
        effect="freshens breath",
        helpful=True,
    ),
    "tooth_brush": Item(
        id="tooth_brush",
        label="toothbrush",
        phrase="a small toothbrush",
        kind="brush",
        effect="scrubs away the smell",
        helpful=True,
    ),
    "sip_water": Item(
        id="sip_water",
        label="water flask",
        phrase="a little water flask",
        kind="water",
        effect="rinses the mouth clean",
        helpful=True,
    ),
    "candy": Item(
        id="candy",
        label="candy",
        phrase="a sweet candy",
        kind="candy",
        effect="makes things sweeter but not cleaner",
        helpful=False,
    ),
}

HEROES = [
    ("Milo", "boy", ["brave", "curious"]),
    ("Nia", "girl", ["bold", "bright"]),
    ("Toby", "boy", ["lively", "kind"]),
    ("Lena", "girl", ["small", "spirited"]),
]

FRIENDS = [
    ("Pip", "boy"),
    ("Luna", "girl"),
    ("Tess", "girl"),
    ("Rowan", "boy"),
]


# ---------------------------------------------------------------------------
# Story parameters
# ---------------------------------------------------------------------------
@dataclass
class StoryParams:
    place: str
    hero: str
    hero_type: str
    friend: str
    friend_type: str
    item: str
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# Narrative helpers
# ---------------------------------------------------------------------------
def rhyme_line() -> str:
    return "“If breath is stale, do not just stare; fresh water, mint, and brushing care.”"


def setup_line(hero: Entity, friend: Entity, place: Place) -> str:
    return (
        f"{hero.id} and {friend.id} were heading along {place.label} when the wind "
        f"shifted and a strange smell popped into the air."
    )


def surprise_line(hero: Entity, friend: Entity) -> str:
    return (
        f"That was a surprise, because {friend.id} had been grinning all morning. "
        f"Then {hero.id} noticed {friend.pronoun('possessive')} bad breath."
    )


def dialogue_line(hero: Entity, friend: Entity) -> str:
    return (
        f'"Do you feel okay?" {hero.id} asked. '
        f'"My mouth tastes weird," {friend.id} said. '
        f'"Maybe we can fix it," {hero.id} said, and then {hero.id} remembered the rhyme.'
    )


def resolution_line(friend: Entity, item: Entity) -> str:
    return (
        f"They used {item.phrase}, and after that {friend.id}'s breath felt much fresher. "
        f"{friend.id} smiled wide, and the adventure could go on."
    )


# ---------------------------------------------------------------------------
# World simulation
# ---------------------------------------------------------------------------
def simulate(params: StoryParams) -> World:
    place = PLACES[params.place]
    world = World(place)

    hero = world.add(Entity(
        id=params.hero, kind="character", type=params.hero_type,
        meters={"courage": 1.0}, memes={"wonder": 1.0}
    ))
    friend = world.add(Entity(
        id=params.friend, kind="character", type=params.friend_type,
        meters={"energy": 1.0}, memes={"embarrassment": 0.0}
    ))
    item = world.add(Entity(
        id=params.item, kind="thing", type=ITEMS[params.item].kind,
        label=ITEMS[params.item].label, phrase=ITEMS[params.item].phrase,
        owner=friend.id
    ))

    # A small adventure arc: travel, surprise, dialogue, clue, fix.
    world.say(setup_line(hero, friend, place))
    world.say(surprise_line(hero, friend))
    friend.memes["embarrassment"] = 1.0
    hero.memes["concern"] = 1.0

    world.para()
    world.say(rhyme_line())
    world.say(dialogue_line(hero, friend))

    world.para()
    if params.item == "candy":
        # A valid but unhelpful choice makes the story fail the reasonableness gate.
        world.say(
            f"They tried the candy, but it only made the moment sweeter, not cleaner."
        )
    else:
        friend.meters["fresh"] = 1.0
        item.meters["used"] = 1.0
        world.say(
            f"{hero.id} found {item.phrase} in the pack and offered it with a nod. "
            f"{friend.id} took it, followed the rhyme, and used it right away."
        )
        world.say(resolution_line(friend, item))

    world.facts.update(hero=hero, friend=friend, item=item, place=place)
    return world


# ---------------------------------------------------------------------------
# Constraints and reasonableness
# ---------------------------------------------------------------------------
def valid_combo(place: str, item: str) -> bool:
    return item in {"mint_leaf", "tooth_brush", "sip_water"} and place in PLACES


def reason_for_rejection(place: str, item: str) -> str:
    if item == "candy":
        return (
            "(No story: candy would not reasonably solve halitosis in this adventure. "
            "Use mint_leaf, tooth_brush, or sip_water instead.)"
        )
    return "(No story: the chosen place/item pair is not a reasonable adventure fix.)"


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
place(P) :- place_fact(P).
item(I) :- item_fact(I).
helpful(I) :- helpful_fact(I).

valid(P, I) :- place(P), item(I), helpful(I).
"""


def asp_facts() -> str:
    import storyworlds.asp as asp
    lines = []
    for pid in PLACES:
        lines.append(asp.fact("place_fact", pid))
    for iid, item in ITEMS.items():
        lines.append(asp.fact("item_fact", iid))
        if item.helpful:
            lines.append(asp.fact("helpful_fact", iid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import storyworlds.asp as asp
    model = asp.one_model(asp_program("#show valid/2."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    python_set = {(p, i) for p in PLACES for i in ITEMS if valid_combo(p, i)}
    clingo_set = set(asp_valid_combos())
    if python_set == clingo_set:
        print(f"OK: ASP matches Python gate ({len(clingo_set)} combos).")
        return 0
    print("MISMATCH between ASP and Python:")
    if python_set - clingo_set:
        print("  only in python:", sorted(python_set - clingo_set))
    if clingo_set - python_set:
        print("  only in ASP:", sorted(clingo_set - python_set))
    return 1


# ---------------------------------------------------------------------------
# QA
# ---------------------------------------------------------------------------
def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write an adventure story for a young child that includes the word "halitosis".',
        f"Tell a short story where {f['hero'].id} and {f['friend'].id} are on {f['place'].label}, "
        f"notice halitosis, and solve it with dialogue and a rhyme.",
        f"Write a gentle adventure with a surprise, a spoken rhyme, and a fresh-breath fix.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero, friend, item, place = f["hero"], f["friend"], f["item"], f["place"]
    return [
        QAItem(
            question=f"Who noticed the surprise smell on {place.label}?",
            answer=f"{hero.id} noticed it first when {friend.id}'s breath surprised {hero.id}."
        ),
        QAItem(
            question=f"What did {hero.id} and {friend.id} do after hearing the rhyme?",
            answer=f"They talked about the smell, then used {item.phrase} to help {friend.id}'s breath feel fresher."
        ),
        QAItem(
            question=f"Why was the smell a problem in the story?",
            answer=f"It was a problem because the story described halitosis, which made {friend.id} feel embarrassed until they fixed it."
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is halitosis?",
            answer="Halitosis means bad breath."
        ),
        QAItem(
            question="Why might water help after bad breath?",
            answer="Water can rinse the mouth and wash away dry or stale tastes."
        ),
        QAItem(
            question="Why do people brush their teeth?",
            answer="People brush their teeth to help clean food and germs off their teeth and keep their mouths healthy."
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    lines.extend(f"{i}. {p}" for i, p in enumerate(sample.prompts, 1))
    lines.append("")
    lines.append("== story QA ==")
    for q in sample.story_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    lines.append("")
    lines.append("== world QA ==")
    for q in sample.world_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Parameter resolution / generation
# ---------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Halitosis adventure storyworld.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--hero")
    ap.add_argument("--hero-type", choices=["boy", "girl"])
    ap.add_argument("--friend")
    ap.add_argument("--friend-type", choices=["boy", "girl"])
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
    item = args.item or rng.choice(list(ITEMS))
    if not valid_combo(place, item):
        raise StoryError(reason_for_rejection(place, item))

    hero, hero_type, _ = rng.choice(HEROES)
    friend, friend_type = rng.choice(FRIENDS)
    if friend == hero:
        friend, friend_type = ("Pip", "boy") if hero != "Pip" else ("Luna", "girl")

    return StoryParams(
        place=place,
        hero=args.hero or hero,
        hero_type=args.hero_type or hero_type,
        friend=args.friend or friend,
        friend_type=args.friend_type or friend_type,
        item=item,
    )


def generate(params: StoryParams) -> StorySample:
    world = simulate(params)
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


def dump_trace(world: World) -> str:
    lines = ["--- world model ---"]
    for e in world.entities.values():
        ms = {k: v for k, v in e.meters.items() if v}
        mm = {k: v for k, v in e.memes.items() if v}
        bits = []
        if ms:
            bits.append(f"meters={ms}")
        if mm:
            bits.append(f"memes={mm}")
        lines.append(f"  {e.id}: {e.type} {' '.join(bits)}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
CURATED = [
    StoryParams(place="forest_path", hero="Milo", hero_type="boy", friend="Luna", friend_type="girl", item="mint_leaf"),
    StoryParams(place="old_tower", hero="Nia", hero_type="girl", friend="Pip", friend_type="boy", item="tooth_brush"),
    StoryParams(place="harbor", hero="Toby", hero_type="boy", friend="Tess", friend_type="girl", item="sip_water"),
]


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"{len(asp_valid_combos())} compatible place/item combos:")
        for p, i in asp_valid_combos():
            print(f"  {p:10} {i}")
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

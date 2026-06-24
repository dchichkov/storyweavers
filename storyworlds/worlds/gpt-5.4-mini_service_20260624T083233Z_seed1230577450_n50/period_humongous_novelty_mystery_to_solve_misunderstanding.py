#!/usr/bin/env python3
"""
storyworlds/worlds/period_humongous_novelty_mystery_to_solve_misunderstanding.py
================================================================================

A standalone story world for an adventure-style mystery with a misunderstanding.

Premise:
- During a reading period, a child notices a humongous novelty prize missing.
- A friend thinks the child hid it on purpose, which creates a misunderstanding.
- The child follows clues through a small set of places, solves the mystery, and
  proves who really moved the item.

This world models:
- physical meters: search progress, clue strength, object location, effort
- emotional memes: worry, suspicion, trust, relief, wonder

The story is designed to feel like a compact adventure with a clear beginning,
a clue-driven middle, and a resolution that explains the misunderstanding.
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
# Core world model
# ---------------------------------------------------------------------------
THRESHOLD = 1.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"   # character | thing | place
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    carried_by: Optional[str] = None
    located_in: Optional[str] = None
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
    detail: str
    connects: list[str] = field(default_factory=list)


@dataclass
class Clue:
    id: str
    place: str
    text: str
    next_place: Optional[str] = None
    leads_to: Optional[str] = None


class World:
    def __init__(self) -> None:
        self.entities: dict[str, Entity] = {}
        self.places: dict[str, Place] = {}
        self.clues: list[Clue] = []
        self.facts: dict = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[str] = set()

    def add_entity(self, e: Entity) -> Entity:
        self.entities[e.id] = e
        return e

    def add_place(self, p: Place) -> Place:
        self.places[p.id] = p
        return p

    def add_clue(self, c: Clue) -> Clue:
        self.clues.append(c)
        return c

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
        w = World()
        w.entities = copy.deepcopy(self.entities)
        w.places = copy.deepcopy(self.places)
        w.clues = copy.deepcopy(self.clues)
        w.facts = copy.deepcopy(self.facts)
        w.fired = set(self.fired)
        w.paragraphs = [[]]
        return w


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------
@dataclass
class StoryParams:
    setting: str
    hero: str
    friend: str
    adult: str
    mystery_item: str
    seed: Optional[int] = None


HEROES = [
    ("Maya", "girl"),
    ("Noah", "boy"),
    ("Lily", "girl"),
    ("Eli", "boy"),
    ("Zoe", "girl"),
    ("Theo", "boy"),
]

FRIENDS = {
    "girl": ["Ava", "Mina", "Ruby", "Nina"],
    "boy": ["Ben", "Sam", "Finn", "Owen"],
}

ADULTS = ["teacher", "librarian", "guide"]

SETTINGS = {
    "reading_period": Place(
        id="reading_period",
        label="the reading period room",
        detail="desks, picture books, and a soft carpet for quiet reading",
        connects=["hall", "library", "closet"],
    ),
    "library": Place(
        id="library",
        label="the school library",
        detail="tall shelves, a wooden ladder, and a bright window",
        connects=["reading_period", "hall", "poster_corner"],
    ),
    "hall": Place(
        id="hall",
        label="the hallway",
        detail="a long hallway with echoing steps and notice boards",
        connects=["reading_period", "library", "poster_corner", "storage"],
    ),
    "poster_corner": Place(
        id="poster_corner",
        label="the poster corner",
        detail="a wall full of maps, labels, and colorful posters",
        connects=["library", "hall", "storage"],
    ),
    "storage": Place(
        id="storage",
        label="the storage closet",
        detail="boxes, tape rolls, and folded paper props",
        connects=["hall", "poster_corner"],
    ),
}

ITEMS = {
    "kite": "a humongous novelty kite",
    "hat": "a humongous novelty hat",
    "pigeon": "a humongous novelty pigeon prop",
}

VALID_SETTINGS = list(SETTINGS)
VALID_ITEMS = list(ITEMS)


# ---------------------------------------------------------------------------
# Story helpers
# ---------------------------------------------------------------------------
def make_world(params: StoryParams) -> World:
    if params.setting not in SETTINGS:
        raise StoryError("Unknown setting.")
    if params.mystery_item not in ITEMS:
        raise StoryError("Unknown mystery item.")

    world = World()
    place = SETTINGS[params.setting]
    world.add_place(place)
    for pid, p in SETTINGS.items():
        if pid != params.setting:
            world.add_place(p)

    hero_name, hero_type = params.hero.split(":", 1)
    friend_name, friend_type = params.friend.split(":", 1)
    adult_name, adult_type = params.adult.split(":", 1)

    hero = world.add_entity(Entity(id=hero_name, kind="character", type=hero_type, meters={}, memes={}))
    friend = world.add_entity(Entity(id=friend_name, kind="character", type=friend_type, meters={}, memes={}))
    adult = world.add_entity(Entity(id=adult_name, kind="character", type=adult_type, label=f"the {adult_type}"))

    item = world.add_entity(Entity(
        id="mystery_item",
        kind="thing",
        type=params.mystery_item,
        label=ITEMS[params.mystery_item].split(" ", 2)[-1],
        phrase=ITEMS[params.mystery_item],
        owner=hero.id,
        located_in=place.id,
    ))

    # Initial emotional and physical state
    hero.memes.update(wonder=1.0, worry=0.0, trust=1.0, relief=0.0)
    friend.memes.update(suspicion=0.0, worry=0.5, trust=0.5, relief=0.0)
    adult.memes.update(calm=1.0)
    hero.meters.update(search=0.0, clue_progress=0.0, effort=0.0)
    item.meters.update(hidden=0.0, found=0.0)

    world.facts.update(
        hero=hero,
        friend=friend,
        adult=adult,
        item=item,
        setting=place,
        item_label=ITEMS[params.mystery_item],
    )
    return world


def _hero(world: World) -> Entity:
    return world.facts["hero"]


def _friend(world: World) -> Entity:
    return world.facts["friend"]


def _adult(world: World) -> Entity:
    return world.facts["adult"]


def _item(world: World) -> Entity:
    return world.facts["item"]


def _setting(world: World) -> Place:
    return world.facts["setting"]


def introduce(world: World) -> None:
    h = _hero(world)
    s = _setting(world)
    item = _item(world)
    world.say(
        f"{h.id} was a curious little {h.type} who loved adventure and noticed tiny details."
    )
    world.say(
        f"During the reading period, {h.id} saw {item.phrase} waiting near {s.label}."
    )


def misunderstanding(world: World) -> None:
    h, f, a, item = _hero(world), _friend(world), _adult(world), _item(world)
    f.memes["suspicion"] += 1.0
    h.memes["worry"] += 0.5
    world.say(
        f"Then {item.phrase} disappeared, and {f.id} frowned at {h.id} as if {h.id} had hidden it."
    )
    world.say(
        f'"Did you take it?" {f.id} asked. {h.id} shook {h.id} head, and the {a.type} asked them to look carefully.'
    )


def move_to(world: World, place_id: str) -> None:
    world.facts["current_place"] = place_id


def clue_step(world: World, clue: Clue) -> None:
    h, f, item = _hero(world), _friend(world), _item(world)
    if clue.id in world.fired:
        return
    world.fired.add(clue.id)
    h.meters["search"] += 1.0
    h.meters["clue_progress"] += 1.0
    h.memes["wonder"] += 0.5
    if clue.id == "tape":
        f.memes["suspicion"] -= 0.25
    if clue.id == "paper":
        f.memes["trust"] += 0.5
    world.say(clue.text)
    if clue.next_place:
        world.say(f"{h.id} hurried toward {SETTINGS[clue.next_place].label}.")


def solve_mystery(world: World) -> None:
    h, f, a, item = _hero(world), _friend(world), _adult(world), _item(world)
    h.meters["effort"] += 1.0
    h.memes["relief"] += 1.0
    f.memes["suspicion"] = 0.0
    f.memes["trust"] += 1.0
    item.meters["found"] = 1.0
    item.located_in = "poster_corner"
    item.carried_by = a.id
    world.say(
        f"At last, {h.id} found the answer: {item.phrase} had been moved to the poster corner by the {a.type} for the afternoon display."
    )
    world.say(
        f"{a.id} smiled and explained it had never been stolen. It was only moved while the room was being rearranged."
    )
    world.say(
        f"{f.id}'s face turned soft with relief, and {f.id} apologized for the misunderstanding."
    )
    world.say(
        f"{h.id} laughed, and the three of them carried the humongous novelty piece back together, just in time for the next reading period."
    )


def build_clues() -> list[Clue]:
    return [
        Clue(
            id="ribbon",
            place="reading_period",
            text="A bright ribbon on the floor pointed toward the hallway like a tiny arrow.",
            next_place="hall",
        ),
        Clue(
            id="tape",
            place="hall",
            text="In the hallway, a strip of tape stuck to the wall, and that meant someone had used the storage closet.",
            next_place="storage",
        ),
        Clue(
            id="paper",
            place="storage",
            text="Inside the closet, a paper note said, 'For the poster corner after lunch,' and the mystery started to make sense.",
            next_place="poster_corner",
        ),
    ]


def tell(world: World) -> World:
    introduce(world)
    world.para()
    misunderstanding(world)
    world.para()
    world.clues = build_clues()
    for clue in world.clues:
        clue_step(world, clue)
    world.para()
    solve_mystery(world)
    return world


# ---------------------------------------------------------------------------
# Q&A
# ---------------------------------------------------------------------------
def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a short adventure story for a child named {f["hero"].id} about a {f["item_label"]} that causes a misunderstanding during the reading period.',
        f"Tell a mystery story where {f['friend'].id} thinks {f['hero'].id} hid a {f['item_label']}, but the truth is kinder and more ordinary.",
        f"Write a child-friendly adventure with clues in the hallway, storage closet, and poster corner, ending with relief instead of blame.",
    ]


def story_qa(world: World) -> list[QAItem]:
    h, f, a, item = _hero(world), _friend(world), _adult(world), _item(world)
    return [
        QAItem(
            question=f"What disappeared during the reading period?",
            answer=f"{item.phrase} disappeared, and that is what started the mystery.",
        ),
        QAItem(
            question=f"Why did {f.id} think {h.id} was in trouble?",
            answer=f"{f.id} thought {h.id} might have hidden {item.phrase}, so the moment felt like a misunderstanding.",
        ),
        QAItem(
            question=f"How was the mystery solved?",
            answer=f"{h.id} followed clues through the hallway and storage closet, then found that the {a.type} had moved {item.phrase} to the poster corner for a display.",
        ),
        QAItem(
            question=f"How did the story end?",
            answer=f"It ended with relief, an apology, and the humongous novelty item being carried back together.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a mystery?",
            answer="A mystery is a puzzle or unknown thing that people try to figure out by looking for clues.",
        ),
        QAItem(
            question="What is a misunderstanding?",
            answer="A misunderstanding happens when someone thinks something is true, but they do not have the right information yet.",
        ),
        QAItem(
            question="What does a clue do in a mystery?",
            answer="A clue helps a person move from not knowing to understanding what really happened.",
        ),
        QAItem(
            question="What does the word humongous mean?",
            answer="Humongous means very, very big.",
        ),
        QAItem(
            question="What is a novelty item?",
            answer="A novelty item is something made to be funny, unusual, or extra special to look at.",
        ),
        QAItem(
            question="What is a reading period?",
            answer="A reading period is a set time when children read books quietly, often at school.",
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
    lines.append("== (3) World knowledge questions ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for e in world.entities.values():
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        if e.located_in:
            bits.append(f"located_in={e.located_in}")
        if e.carried_by:
            bits.append(f"carried_by={e.carried_by}")
        lines.append(f"  {e.id} ({e.type}) {' '.join(bits)}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
% Facts:
% setting(S). hero(H). friend(F). adult(A). item(I). place(P).
% In this tiny world, the mystery is valid when a clue chain reaches the
% poster corner and the item ends up explained rather than stolen.

reachable(reading_period, hall).
reachable(hall, storage).
reachable(storage, poster_corner).
reachable(hall, poster_corner).
reachable(library, hall).
reachable(reading_period, library).

clue_chain(reading_period, hall, storage, poster_corner).

valid_story(S, I) :- setting(S), item(I), clue_chain(S, _, _, poster_corner).
"""

def asp_facts() -> str:
    import storyworlds.asp as asp
    lines = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for iid in ITEMS:
        lines.append(asp.fact("item", iid))
    for pid, p in SETTINGS.items():
        for c in p.connects:
            lines.append(asp.fact("reachable", pid, c))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_stories() -> list[tuple]:
    import storyworlds.asp as asp
    model = asp.one_model(asp_program("#show valid_story/2."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    import storyworlds.asp as asp
    py = {("reading_period", item) for item in ITEMS}
    cl = set(asp_valid_stories())
    if cl == py:
        print(f"OK: clingo gate matches Python ({len(cl)} stories).")
        return 0
    print("MISMATCH between ASP and Python.")
    print("  clingo:", sorted(cl))
    print("  python:", sorted(py))
    return 1


# ---------------------------------------------------------------------------
# Reasonableness / generation
# ---------------------------------------------------------------------------
def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for setting in SETTINGS:
        for hero_name, hero_type in HEROES:
            for item in ITEMS:
                combos.append((setting, f"{hero_name}:{hero_type}", item))
    return combos


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Adventure-style mystery world with a misunderstanding and a humongous novelty item."
    )
    ap.add_argument("--setting", choices=VALID_SETTINGS)
    ap.add_argument("--hero")
    ap.add_argument("--friend")
    ap.add_argument("--adult", choices=ADULTS)
    ap.add_argument("--item", choices=VALID_ITEMS)
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
    setting = args.setting or rng.choice(VALID_SETTINGS)
    hero = args.hero
    if hero is None:
        hname, htype = rng.choice(HEROES)
        hero = f"{hname}:{htype}"
    hero_name, hero_type = hero.split(":", 1)
    friend = args.friend
    if friend is None:
        friend = f"{rng.choice(FRIENDS[hero_type])[0:]}:{'girl' if hero_type == 'girl' else 'boy'}"
        # The friend string above is only a placeholder format; replace properly below.
        fname = rng.choice(FRIENDS[hero_type])
        friend = f"{fname}:{'girl' if hero_type == 'girl' else 'boy'}"
    adult = args.adult or rng.choice(ADULTS)
    item = args.item or rng.choice(VALID_ITEMS)
    return StoryParams(setting=setting, hero=hero, friend=friend, adult=adult, mystery_item=item)


def generate(params: StoryParams) -> StorySample:
    world = make_world(params)
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


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid_story/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        stories = asp_valid_stories()
        print(f"{len(stories)} compatible stories:")
        for s in stories:
            print("  ", s)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        cur = []
        for setting in VALID_SETTINGS:
            for hname, htype in HEROES[:3]:
                for item in VALID_ITEMS:
                    friend_name = FRIENDS[htype][0]
                    friend_type = "girl" if htype == "girl" else "boy"
                    cur.append(StoryParams(
                        setting=setting,
                        hero=f"{hname}:{htype}",
                        friend=f"{friend_name}:{friend_type}",
                        adult="Ms. Lane:teacher" if False else "MsLane:teacher",
                        mystery_item=item,
                    ))
        for p in cur:
            try:
                samples.append(generate(p))
            except StoryError:
                continue
    else:
        seen = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 50, 50):
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            i += 1
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

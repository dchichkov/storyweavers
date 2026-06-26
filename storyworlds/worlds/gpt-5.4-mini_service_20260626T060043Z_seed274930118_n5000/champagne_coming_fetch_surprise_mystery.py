#!/usr/bin/env python3
"""
storyworlds/worlds/champagne_coming_fetch_surprise_mystery.py
=============================================================

A small mystery-flavored storyworld about a coming surprise, a fetch, and a
carefully hidden bottle of champagne.

Premise:
- A child notices a coming surprise at home.
- Someone needs a fetch for a missing item before guests arrive.
- The mystery is resolved by finding the lost thing and revealing the plan.

World model:
- Characters and objects each carry physical meters and emotional memes.
- The story changes as the missing item is searched for, found, and used.
- The ending image proves the surprise has arrived.
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
# Core data model
# ---------------------------------------------------------------------------
@dataclass
class Entity:
    id: str
    kind: str = "thing"   # "character" | "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    hidden: bool = False
    found: bool = False
    carried_by: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.meters:
            self.meters = {"lost": 0.0, "order": 0.0, "surprise": 0.0}
        if not self.memes:
            self.memes = {"curiosity": 0.0, "worry": 0.0, "joy": 0.0, "secrecy": 0.0}

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman"}
        male = {"boy", "father", "dad", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class Setting:
    place: str = "the kitchen"
    has_table: bool = True
    has_drawer: bool = True
    has_hall: bool = True
    has_closet: bool = True


@dataclass
class Clue:
    text: str
    location: str
    item: str


@dataclass
class StoryParams:
    place: str
    hero: str
    parent: str
    surprise_item: str
    missing_item: str
    helper_item: str
    seed: Optional[int] = None


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.clues: list[Clue] = []
        self.found_item: Optional[str] = None
        self.revealed: bool = False

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

    def carry(self, item_id: str, carrier_id: str) -> None:
        self.entities[item_id].carried_by = carrier_id
        self.entities[item_id].hidden = False
        self.entities[item_id].found = True

    def copy(self) -> "World":
        import copy as _copy
        clone = World(self.setting)
        clone.entities = _copy.deepcopy(self.entities)
        clone.paragraphs = [[]]
        clone.facts = dict(self.facts)
        clone.clues = list(self.clues)
        clone.found_item = self.found_item
        clone.revealed = self.revealed
        return clone


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------
SETTINGS = {
    "kitchen": Setting(place="the kitchen", has_table=True, has_drawer=True, has_hall=True, has_closet=False),
    "hall": Setting(place="the hall", has_table=False, has_drawer=False, has_hall=True, has_closet=True),
    "garden_room": Setting(place="the garden room", has_table=True, has_drawer=True, has_hall=True, has_closet=True),
}

HERO_NAMES = ["Mina", "Leo", "Nora", "Theo", "Ava", "Sam"]
PARENT_TYPES = ["mother", "father"]
SURPRISE_ITEMS = {
    "cake": "a small cake with bright frosting",
    "lantern": "a paper lantern with gold stars",
    "banner": "a folded banner that said SURPRISE",
}
MISSING_ITEMS = {
    "matchbook": "a little matchbook",
    "ribbon": "a red ribbon",
    "corkscrew": "a corkscrew",
}
HELPER_ITEMS = {
    "note": "a clue note",
    "key": "a brass key",
    "flashlight": "a small flashlight",
}


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
% A surprise setup is valid when the missing item can be fetched from one of the
% plausible hiding places for the chosen setting.
valid_story(Place, Surprise, Missing, Helper) :-
    place(Place), surprise_item(Surprise), missing_item(Missing), helper_item(Helper),
    can_hide(Place, Missing), can_fetch(Place, Helper).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid in SETTINGS:
        lines.append(asp.fact("place", pid))
    for sid in SURPRISE_ITEMS:
        lines.append(asp.fact("surprise_item", sid))
    for mid in MISSING_ITEMS:
        lines.append(asp.fact("missing_item", mid))
    for hid in HELPER_ITEMS:
        lines.append(asp.fact("helper_item", hid))
    for place, setting in SETTINGS.items():
        if setting.has_drawer:
            lines.append(asp.fact("can_hide", place, "corkscrew"))
            lines.append(asp.fact("can_hide", place, "ribbon"))
        if setting.has_closet:
            lines.append(asp.fact("can_hide", place, "matchbook"))
        if setting.has_hall:
            lines.append(asp.fact("can_fetch", place, "flashlight"))
        if setting.has_table:
            lines.append(asp.fact("can_fetch", place, "note"))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_stories() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/4."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    python_set = set(valid_combos())
    clingo_set = set(asp_valid_stories())
    if python_set == clingo_set:
        print(f"OK: clingo gate matches valid_combos() ({len(python_set)} stories).")
        return 0
    print("MISMATCH between clingo and python:")
    if clingo_set - python_set:
        print("  only in clingo:", sorted(clingo_set - python_set))
    if python_set - clingo_set:
        print("  only in python:", sorted(python_set - clingo_set))
    return 1


# ---------------------------------------------------------------------------
# World logic
# ---------------------------------------------------------------------------
def valid_combos() -> list[tuple[str, str, str, str]]:
    combos = []
    for place, setting in SETTINGS.items():
        for surprise in SURPRISE_ITEMS:
            for missing in MISSING_ITEMS:
                for helper in HELPER_ITEMS:
                    if can_hide(setting, missing) and can_fetch(setting, helper):
                        combos.append((place, surprise, missing, helper))
    return combos


def can_hide(setting: Setting, item: str) -> bool:
    if item in {"corkscrew", "ribbon"}:
        return setting.has_drawer
    if item == "matchbook":
        return setting.has_closet
    return False


def can_fetch(setting: Setting, item: str) -> bool:
    if item == "flashlight":
        return setting.has_hall
    if item == "note":
        return setting.has_table
    if item == "key":
        return setting.has_closet
    return False


def mystery_opening(world: World, hero: Entity, parent: Entity) -> None:
    world.say(
        f"{hero.id} noticed that {parent.pronoun('possessive')} steps were quiet in {world.setting.place}."
    )
    world.say(
        f"Something was coming, but the room had the kind of stillness that made every small sound feel important."
    )


def set_up_surprise(world: World, parent: Entity, surprise_item: Entity, missing_item: Entity) -> None:
    parent.memes["secrecy"] += 1
    surprise_item.meters["surprise"] += 1
    missing_item.hidden = True
    missing_item.meters["lost"] += 1
    world.clues.append(Clue(text="A hidden thing was keeping the surprise from being ready.", location="the room", item=missing_item.id))
    world.say(
        f"{parent.id} had been setting up a surprise with {surprise_item.phrase}, "
        f"but one small thing was missing."
    )


def search(world: World, hero: Entity) -> None:
    hero.memes["curiosity"] += 1
    world.say(
        f"{hero.id} looked under the table, by the drawer, and along the hall, trying to solve the little mystery."
    )


def give_clue(world: World, missing_item: Entity, helper_item: Entity, place: str) -> None:
    helper_item.meters["order"] += 1
    world.clues.append(Clue(
        text=f"The helper item pointed toward the right hiding place.",
        location=place,
        item=missing_item.id,
    ))
    world.say(
        f"Then {helper_item.phrase} turned up, and it seemed to point the way, as if it knew the answer."
    )


def find_item(world: World, hero: Entity, parent: Entity, missing_item: Entity) -> None:
    if missing_item.hidden and not missing_item.found:
        missing_item.hidden = False
        missing_item.found = True
        world.found_item = missing_item.id
        hero.memes["worry"] = max(0.0, hero.memes["worry"] - 1)
        hero.memes["joy"] += 1
        world.say(
            f"{hero.id} found {missing_item.phrase} tucked safely away."
        )
        world.say(
            f"{parent.id} gave a surprised smile, because the missing piece had been hiding in plain sight."
        )


def reveal(world: World, parent: Entity, surprise_item: Entity, missing_item: Entity) -> None:
    world.revealed = True
    world.say(
        f"At last, {parent.id} finished the surprise. {surprise_item.phrase} sat ready, "
        f"and even the hidden {missing_item.label} was no longer a mystery."
    )
    world.say(
        f"Coming footsteps paused at the door, and the room brightened with the feeling that the secret had been worth the wait."
    )


# ---------------------------------------------------------------------------
# Story assembly
# ---------------------------------------------------------------------------
def tell(setting: Setting, params: StoryParams) -> World:
    world = World(setting)
    hero = world.add(Entity(id=params.hero, kind="character", type="child"))
    parent = world.add(Entity(id="Parent", kind="character", type=params.parent))
    surprise_item = world.add(Entity(
        id=params.surprise_item,
        type="thing",
        label=params.surprise_item,
        phrase=SURPRISE_ITEMS[params.surprise_item],
        owner=parent.id,
    ))
    missing_item = world.add(Entity(
        id=params.missing_item,
        type="thing",
        label=params.missing_item,
        phrase=MISSING_ITEMS[params.missing_item],
        owner=parent.id,
        hidden=True,
    ))
    helper_item = world.add(Entity(
        id=params.helper_item,
        type="thing",
        label=params.helper_item,
        phrase=HELPER_ITEMS[params.helper_item],
        owner=hero.id,
    ))

    world.facts.update(
        hero=hero, parent=parent, surprise_item=surprise_item,
        missing_item=missing_item, helper_item=helper_item,
        setting=setting, params=params,
    )

    mystery_opening(world, hero, parent)
    world.para()
    set_up_surprise(world, parent, surprise_item, missing_item)
    search(world, hero)
    give_clue(world, missing_item, helper_item, setting.place)
    find_item(world, hero, parent, missing_item)
    world.para()
    reveal(world, parent, surprise_item, missing_item)
    return world


# ---------------------------------------------------------------------------
# Q&A
# ---------------------------------------------------------------------------
def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a short mystery-style story for a child where {f["hero"].id} notices a coming surprise and helps fetch a missing item.',
        f'Tell a gentle story about {f["parent"].type} planning a surprise with {f["surprise_item"].label}, while one small thing is lost and must be found.',
        f'Create a child-friendly mystery in {f["setting"].place} that includes the words "coming", "fetch", and "surprise".',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero: Entity = f["hero"]
    parent: Entity = f["parent"]
    surprise_item: Entity = f["surprise_item"]
    missing_item: Entity = f["missing_item"]
    helper_item: Entity = f["helper_item"]
    return [
        QAItem(
            question=f"What was {hero.id} trying to understand in {world.setting.place}?",
            answer=f"{hero.id} was trying to understand a coming surprise and why one important thing was missing.",
        ),
        QAItem(
            question=f"What did {parent.id} hide while getting the surprise ready?",
            answer=f"{parent.id} hid {missing_item.phrase} so the surprise could stay secret until the right moment.",
        ),
        QAItem(
            question=f"How did {hero.id} help solve the mystery?",
            answer=f"{hero.id} searched the room, followed the clue from {helper_item.phrase}, and found {missing_item.phrase}.",
        ),
        QAItem(
            question=f"What was the surprise in the end?",
            answer=f"The surprise was built around {surprise_item.phrase}, and it was finally ready once the missing item was found.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    f = world.facts
    out = [
        QAItem(
            question="What is a surprise?",
            answer="A surprise is something that is kept secret for a little while so someone can enjoy discovering it later.",
        ),
        QAItem(
            question="What does fetch mean?",
            answer="To fetch something means to go get it and bring it back.",
        ),
        QAItem(
            question="What is champagne?",
            answer="Champagne is a sparkling drink with bubbles that people often save for celebrations.",
        ),
    ]
    if f["surprise_item"].id == "banner":
        out.append(QAItem(
            question="What is a banner?",
            answer="A banner is a long piece of cloth or paper with words or decorations on it, often used for celebrations.",
        ))
    return out


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
        if e.hidden:
            bits.append("hidden=True")
        if e.found:
            bits.append("found=True")
        if e.carried_by:
            bits.append(f"carried_by={e.carried_by}")
        if e.meters:
            meters = {k: v for k, v in e.meters.items() if v}
            if meters:
                bits.append(f"meters={meters}")
        if e.memes:
            memes = {k: v for k, v in e.memes.items() if v}
            if memes:
                bits.append(f"memes={memes}")
        lines.append(f"  {e.id:12} ({e.type:7}) {' '.join(bits)}")
    lines.append(f"  clues: {[c.text for c in world.clues]}")
    lines.append(f"  found_item: {world.found_item}")
    lines.append(f"  revealed: {world.revealed}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Parameter resolution / generation
# ---------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Mystery storyworld: a coming surprise, a fetch, and a hidden clue.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--hero")
    ap.add_argument("--parent", choices=PARENT_TYPES)
    ap.add_argument("--surprise-item", choices=SURPRISE_ITEMS)
    ap.add_argument("--missing-item", choices=MISSING_ITEMS)
    ap.add_argument("--helper-item", choices=HELPER_ITEMS)
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
    combos = valid_combos()
    if args.place:
        combos = [c for c in combos if c[0] == args.place]
    if args.surprise_item:
        combos = [c for c in combos if c[1] == args.surprise_item]
    if args.missing_item:
        combos = [c for c in combos if c[2] == args.missing_item]
    if args.helper_item:
        combos = [c for c in combos if c[3] == args.helper_item]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, surprise_item, missing_item, helper_item = rng.choice(sorted(combos))
    hero = args.hero or rng.choice(HERO_NAMES)
    parent = args.parent or rng.choice(PARENT_TYPES)
    return StoryParams(
        place=place,
        hero=hero,
        parent=parent,
        surprise_item=surprise_item,
        missing_item=missing_item,
        helper_item=helper_item,
    )


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.place], params)
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


# ---------------------------------------------------------------------------
# ASP helpers
# ---------------------------------------------------------------------------
def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/4."))
    return sorted(set(asp.atoms(model, "valid_story")))


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
CURATED = [
    StoryParams(place="kitchen", hero="Mina", parent="mother", surprise_item="cake", missing_item="ribbon", helper_item="note"),
    StoryParams(place="hall", hero="Leo", parent="father", surprise_item="banner", missing_item="matchbook", helper_item="flashlight"),
    StoryParams(place="garden_room", hero="Nora", parent="mother", surprise_item="lantern", missing_item="corkscrew", helper_item="key"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid_story/4."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        stories = asp_valid_stories()
        print(f"{len(stories)} compatible stories:\n")
        for place, surprise, missing, helper in stories:
            print(f"  {place:12} {surprise:12} {missing:12} {helper:12}")
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
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.hero}: surprise={p.surprise_item}, missing={p.missing_item}, helper={p.helper_item}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()

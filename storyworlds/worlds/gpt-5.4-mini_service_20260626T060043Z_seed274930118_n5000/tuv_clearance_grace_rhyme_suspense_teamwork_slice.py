#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260626T060043Z_seed274930118_n5000/tuv_clearance_grace_rhyme_suspense_teamwork_slice.py
===============================================================================================================================

A small slice-of-life storyworld about a family's clearance-day tidy-up, where
rhymes, teamwork, and a little suspense help a child save a treasured thing.

Seed words and instruments: tuv, clearance, grace, rhyme, suspense, teamwork.
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

@dataclass
class Entity:
    id: str
    kind: str = "thing"  # character | thing
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
        if self.type in {"girl", "woman", "mother", "grandmother"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man", "father", "grandfather"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str = "the apartment"
    affords: set[str] = field(default_factory=set)


@dataclass
class Item:
    id: str
    label: str
    phrase: str
    region: str
    value: str
    risk: str
    rhyme: str
    plural: bool = False


@dataclass
class Helper:
    id: str
    label: str
    phrase: str
    value: str
    comfort: str


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}

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
        import copy as _copy
        c = World(self.setting)
        c.entities = _copy.deepcopy(self.entities)
        c.paragraphs = [[]]
        c.facts = dict(self.facts)
        return c


# ---------------------------------------------------------------------------
# Parameters and registries
# ---------------------------------------------------------------------------

@dataclass
class StoryParams:
    place: str
    hero: str
    gender: str
    helper: str
    item: str
    seed: Optional[int] = None


SETTINGS = {
    "apartment": Setting(place="the apartment", affords={"clearance", "sort"}),
    "laundry_room": Setting(place="the laundry room", affords={"clearance", "sort"}),
    "porch": Setting(place="the porch", affords={"clearance", "sort"}),
}

HEROES = {
    "girl": ["Mina", "Tia", "Luna", "Ivy", "Nora"],
    "boy": ["Ben", "Owen", "Milo", "Jude", "Eli"],
}

HELPERS = {
    "grandma": Helper(
        id="grandma",
        label="Grandma Grace",
        phrase="Grandma Grace",
        value="calm",
        comfort="grace",
    ),
    "sibling": Helper(
        id="sibling",
        label="big sister",
        phrase="big sister",
        value="quick",
        comfort="teamwork",
    ),
}

ITEMS = {
    "tuv_box": Item(
        id="tuv_box",
        label="TUV box",
        phrase="a small box marked TUV",
        region="shelf",
        value="kept",
        risk="donated",
        rhyme="glow",
    ),
    "lantern": Item(
        id="lantern",
        label="lantern",
        phrase="a paper lantern with a soft gold rim",
        region="table",
        value="kept",
        risk="packed away",
        rhyme="bright",
    ),
    "blue_jar": Item(
        id="blue_jar",
        label="blue jar",
        phrase="a blue jar with painted flowers",
        region="counter",
        value="kept",
        risk="boxed up",
        rhyme="clear",
    ),
}

TRACES = {
    "clearance": "clearance",
    "grace": "grace",
    "tuv": "tuv",
    "rhyme": "rhyme",
    "suspense": "suspense",
    "teamwork": "teamwork",
}


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------

ASP_RULES = r"""
% An item is at risk when clearance means it might be donated or packed away.
at_risk(I) :- item(I), risk_of(I, R), R = donated.
at_risk(I) :- item(I), risk_of(I, R), R = packed_away.
at_risk(I) :- item(I), risk_of(I, R), R = boxed_up.

% Grace or teamwork can turn a risky moment into a safe keep.
good_fix(I) :- helper(grace), item(I), at_risk(I).
good_fix(I) :- helper(teamwork), item(I), at_risk(I).

valid_story(P, H, I, X) :- place(P), hero(H), item(I), helper(X),
                           supports(P, clearance), at_risk(I), good_fix(I).
"""

def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid, s in SETTINGS.items():
        lines.append(asp.fact("place", pid))
        for a in sorted(s.affords):
            lines.append(asp.fact("supports", pid, a))
    for gid, g in HELPERS.items():
        lines.append(asp.fact("helper", gid))
        lines.append(asp.fact("helper_value", gid, g.value))
    for iid, item in ITEMS.items():
        lines.append(asp.fact("item", iid))
        lines.append(asp.fact("risk_of", iid, item.risk.replace(" ", "_")))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_stories() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/4."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: ASP matches Python ({len(py)} combos).")
        return 0
    print("MISMATCH")
    if py - cl:
        print("Only in Python:", sorted(py - cl))
    if cl - py:
        print("Only in ASP:", sorted(cl - py))
    return 1


# ---------------------------------------------------------------------------
# Reasonableness and simulation
# ---------------------------------------------------------------------------

def valid_combos() -> list[tuple[str, str, str, str]]:
    combos = []
    for place, setting in SETTINGS.items():
        if "clearance" not in setting.affords:
            continue
        for gender in HEROES:
            for helper in HELPERS:
                for item_id, item in ITEMS.items():
                    if helper == "grandma" and item_id in {"tuv_box", "lantern", "blue_jar"}:
                        combos.append((place, gender, helper, item_id))
                    elif helper == "sibling" and item_id != "blue_jar":
                        combos.append((place, gender, helper, item_id))
    return combos


def reasonableness_gate(place: str, helper: str, item: str) -> None:
    if place not in SETTINGS:
        raise StoryError("Unknown place.")
    if helper not in HELPERS:
        raise StoryError("Unknown helper.")
    if item not in ITEMS:
        raise StoryError("Unknown item.")
    if "clearance" not in SETTINGS[place].affords:
        raise StoryError("This place cannot host a clearance-day tidy-up.")


# ---------------------------------------------------------------------------
# Story construction
# ---------------------------------------------------------------------------

def pick_name(gender: str, rng: random.Random) -> str:
    return rng.choice(HEROES[gender])


def intro_line(hero: Entity, helper: Entity, item: Entity) -> str:
    return (
        f"{hero.id} loved little room-sorting afternoons, especially when "
        f"{helper.label} came by with a patient smile and a steady hand."
    )


def setup_line(place: Setting) -> str:
    return f"At {place.place}, boxes were lined up for a gentle clearance day."


def tension_line(hero: Entity, item: Entity) -> str:
    return (
        f"{hero.id} found a small box marked TUV and froze for a moment, "
        f"because no one knew if {item.label} would stay or go."
    )


def rhyme_line(hero: Entity, item: Entity) -> str:
    return (
        f'{hero.id} whispered, "TUV means save, not shove away; '
        f"{item.rhyme} and clear can stay today.""
    )


def teamwork_line(helper: Entity, hero: Entity, item: Entity) -> str:
    return (
        f"{helper.label} nodded, and together they made a neat little shelf. "
        f"{hero.id} held the box while {helper.label} dusted the corner, and "
        f"{item.label} slid into a safe place."
    )


def ending_line(hero: Entity, helper: Entity, item: Entity) -> str:
    return (
        f"In the end, the room looked calmer, {item.label} stayed close, and "
        f"{hero.id} smiled at how grace and teamwork had turned the clearance "
        f"into a quiet win."
    )


def make_story(world: World, hero: Entity, helper: Entity, item: Entity) -> None:
    world.say(intro_line(hero, helper, item))
    world.say(setup_line(world.setting))
    world.para()
    world.say(tension_line(hero, item))
    world.say(rhyme_line(hero, item))
    world.para()
    world.say(teamwork_line(helper, hero, item))
    world.say(ending_line(hero, helper, item))


# ---------------------------------------------------------------------------
# Q&A
# ---------------------------------------------------------------------------

def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a short slice-of-life story about {f["hero_name"]} helping with a '
        f'clearance day at {f["place"]}, with the words tuv, grace, and teamwork.',
        f"Tell a gentle story where {f['hero_name']} worries about {f['item_label']}, "
        f"then uses a rhyme and a helper named {f['helper_label']} to solve it.",
        f"Write a calm child story about sorting a room, a small suspenseful pause, "
        f"and a happy ending that keeps {f['item_label']} safe.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero_name"]
    helper = f["helper_label"]
    item = f["item_label"]
    place = f["place"]
    return [
        QAItem(
            question=f"Why did {hero} pause when the clearance day started at {place}?",
            answer=f"{hero} paused because a small box marked TUV made it uncertain whether {item} would be kept or put away.",
        ),
        QAItem(
            question=f"How did {hero} and {helper} solve the problem with {item}?",
            answer=f"They used teamwork: {hero} held the box while {helper} made a safe shelf, so {item} could stay in place.",
        ),
        QAItem(
            question=f"What made the moment feel a little suspenseful?",
            answer=f"It felt suspenseful because nobody knew right away if {item} would stay or get moved during the clearance.",
        ),
        QAItem(
            question=f"What was the gentle ending image in the story?",
            answer=f"The room looked calmer, {item} stayed close, and {hero} smiled because grace and teamwork helped everything work out.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does clearance mean in a room or store?",
            answer="Clearance means making space by sorting things, often so some items can be moved, sold, or given away.",
        ),
        QAItem(
            question="What does grace mean when people work together?",
            answer="Grace means being calm, kind, and gentle even when a task is a little tricky.",
        ),
        QAItem(
            question="What is teamwork?",
            answer="Teamwork means people help each other and share the job so it goes better for everyone.",
        ),
        QAItem(
            question="What is a rhyme?",
            answer="A rhyme is a pair of words or lines that sound alike at the end, which can make speech fun and memorable.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    parts = ["== (1) Generation prompts -- asks that would produce this story =="]
    for i, p in enumerate(sample.prompts, 1):
        parts.append(f"{i}. {p}")
    parts.append("")
    parts.append("== (2) Story questions -- answerable from the story text ==")
    for q in sample.story_qa:
        parts.append(f"Q: {q.question}")
        parts.append(f"A: {q.answer}")
    parts.append("")
    parts.append("== (3) World-knowledge questions -- child level, no story needed ==")
    for q in sample.world_qa:
        parts.append(f"Q: {q.question}")
        parts.append(f"A: {q.answer}")
    return "\n".join(parts)


# ---------------------------------------------------------------------------
# Generation
# ---------------------------------------------------------------------------

def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.place and args.place not in SETTINGS:
        raise StoryError("Unknown place.")
    if args.gender and args.gender not in HEROES:
        raise StoryError("Unknown gender.")
    if args.helper and args.helper not in HELPERS:
        raise StoryError("Unknown helper.")
    if args.item and args.item not in ITEMS:
        raise StoryError("Unknown item.")

    combos = [c for c in valid_combos()
              if args.place is None or c[0] == args.place
              if True else True]
    combos = [c for c in combos if args.gender is None or c[1] == args.gender]
    combos = [c for c in combos if args.helper is None or c[2] == args.helper]
    combos = [c for c in combos if args.item is None or c[3] == args.item]
    if not combos:
        raise StoryError("No valid combination matches the given options.")

    place, gender, helper_id, item_id = rng.choice(sorted(combos))
    return StoryParams(place=place, hero=pick_name(gender, rng), gender=gender, helper=helper_id, item=item_id)


def generate(params: StoryParams) -> StorySample:
    setting = SETTINGS[params.place]
    world = World(setting)
    hero = world.add(Entity(id=params.hero, kind="character", type=params.gender))
    helper_def = HELPERS[params.helper]
    helper = world.add(Entity(id=helper_def.id, kind="character", type="grandmother" if helper_def.id == "grandma" else "girl", label=helper_def.label))
    item_def = ITEMS[params.item]
    item = world.add(Entity(id=item_def.id, type="thing", label=item_def.label, phrase=item_def.phrase, owner=hero.id, caretaker=helper.id))

    make_story(world, hero, helper, item)
    world.facts = {
        "hero_name": hero.id,
        "helper_label": helper.label,
        "item_label": item.label,
        "place": setting.place,
    }

    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Slice-of-life story world about clearance, grace, rhyme, suspense, and teamwork.")
    ap.add_argument("--place", choices=sorted(SETTINGS))
    ap.add_argument("--gender", choices=sorted(HEROES))
    ap.add_argument("--helper", choices=sorted(HELPERS))
    ap.add_argument("--item", choices=sorted(ITEMS))
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


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/4."))
    return sorted(set(asp.atoms(model, "valid_story")))


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        lines.append(f"  {e.id:10} ({e.kind:8}) type={e.type} label={e.label!r}")
    return "\n".join(lines)


CURATED = [
    StoryParams(place="apartment", hero="Mina", gender="girl", helper="grandma", item="tuv_box"),
    StoryParams(place="porch", hero="Owen", gender="boy", helper="sibling", item="lantern"),
    StoryParams(place="laundry_room", hero="Ivy", gender="girl", helper="grandma", item="blue_jar"),
]


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
        print(asp_program("#show valid_story/4."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        for row in asp_valid_stories():
            print(row)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        for p in CURATED:
            samples.append(generate(p))
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            sample = generate(params)
            if sample.story in seen:
                i += 1
                continue
            seen.add(sample.story)
            samples.append(sample)
            i += 1

    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for idx, sample in enumerate(samples):
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.hero}: clearance at {p.place} ({p.item})"
        elif len(samples) > 1:
            header = f"### variant {idx + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if idx < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260626T060043Z_seed274930118_n5000/bra_foreshadowing_dialogue_sound_effects_adventure.py
=============================================================================================================

A small adventure storyworld with foreshadowing, dialogue, and sound effects.

Seed premise:
A child helps a parent with laundry on a windy day. A bra on the clothesline
starts to flutter loose, and the child must go on a small backyard adventure
to keep it from blowing away before the storm arrives.
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


THRESHOLD = 1.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    place: str = ""
    plural: bool = False
    protective: bool = False
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


@dataclass
class Setting:
    place: str = "the backyard"
    affords: set[str] = field(default_factory=set)


@dataclass
class Activity:
    id: str
    verb: str
    gerund: str
    rush: str
    weather: str
    keyword: str


@dataclass
class Prize:
    label: str
    phrase: str
    type: str


@dataclass
class Gear:
    id: str
    label: str
    prep: str
    tail: str
    guards: set[str] = field(default_factory=set)


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
        self.facts: dict = {}
        self.weather: str = ""

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


@dataclass
class StoryParams:
    place: str
    activity: str
    prize: str
    name: str
    gender: str
    parent: str
    seed: Optional[int] = None


SETTINGS = {
    "backyard": Setting(place="the backyard", affords={"wind"}),
}

ACTIVITIES = {
    "wind": Activity(
        id="wind",
        verb="secure the laundry",
        gerund="helping with the laundry",
        rush="run to the clothesline",
        weather="windy",
        keyword="wind",
    ),
}

PRIZES = {
    "bra": Prize(
        label="bra",
        phrase="a soft pink bra",
        type="bra",
    ),
}

GEAR = [
    Gear(
        id="clothespins",
        label="clothespins",
        prep="grab the clothespins first",
        tail="clipped the bra down tight",
        guards={"wind"},
    ),
    Gear(
        id="laundry_basket",
        label="the laundry basket",
        prep="put the bra in the laundry basket",
        tail="kept the bra safe in the basket",
        guards={"wind"},
    ),
]

GIRL_NAMES = ["Lily", "Maya", "Nora", "Ava", "Zoe"]
BOY_NAMES = ["Ben", "Leo", "Max", "Finn", "Sam"]


def wind_warning(activity: Activity) -> str:
    return "The wind kept whispering at the clothesline."


def sound_effect(kind: str) -> str:
    return {
        "wind": "Whishhh!",
        "clothesline": "Flap-flap-flap!",
        "catch": "Tap!",
        "pin": "Clink!",
    }.get(kind, "Tap!")


def valid_combos() -> list[tuple[str, str, str]]:
    return [("backyard", "wind", "bra")]


def select_gear(activity: Activity, prize: Prize) -> Optional[Gear]:
    if activity.id == "wind" and prize.type == "bra":
        return GEAR[0]
    return None


def asp_facts() -> str:
    import asp
    lines = [
        asp.fact("setting", "backyard"),
        asp.fact("affords", "backyard", "wind"),
        asp.fact("activity", "wind"),
        asp.fact("weather", "wind", "windy"),
        asp.fact("prize", "bra"),
        asp.fact("gear", "clothespins"),
        asp.fact("guards", "clothespins", "wind"),
        asp.fact("gear", "laundry_basket"),
        asp.fact("guards", "laundry_basket", "wind"),
    ]
    return "\n".join(lines)


ASP_RULES = r"""
prize_at_risk(A,P) :- affords(Place,A), prize(P), A = wind, P = bra.
has_fix(A,P) :- prize_at_risk(A,P), gear(G), guards(G, wind), P = bra.
valid(Place,A,P) :- affords(Place,A), prize_at_risk(A,P), has_fix(A,P).
"""


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    if cl - py:
        print("  only in clingo:", sorted(cl - py))
    if py - cl:
        print("  only in python:", sorted(py - cl))
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A windy backyard adventure with a bra, foreshadowing, dialogue, and sound effects.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--activity", choices=ACTIVITIES)
    ap.add_argument("--prize", choices=PRIZES)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--parent", choices=["mother", "father"])
    ap.add_argument("--name")
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
    if args.activity and args.prize:
        if not select_gear(ACTIVITIES[args.activity], PRIZES[args.prize]):
            raise StoryError("No valid story: the chosen activity does not have a reasonable fix for the chosen prize.")
    combos = [c for c in valid_combos()
              if (args.place is None or c[0] == args.place)
              and (args.activity is None or c[1] == args.activity)
              and (args.prize is None or c[2] == args.prize)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, activity, prize = rng.choice(combos)
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    parent = args.parent or rng.choice(["mother", "father"])
    return StoryParams(place=place, activity=activity, prize=prize, name=name, gender=gender, parent=parent)


def generate(params: StoryParams) -> StorySample:
    world = World(SETTINGS[params.place])
    world.weather = ACTIVITIES[params.activity].weather
    hero = world.add(Entity(id=params.name, kind="character", type=params.gender))
    parent = world.add(Entity(id="Parent", kind="character", type=params.parent, label="the parent"))
    prize = world.add(Entity(id="bra", type="bra", label="bra", phrase=PRIZES["bra"].phrase, owner=parent.id, caretaker=parent.id, place="clothesline"))
    gear = select_gear(ACTIVITIES[params.activity], PRIZES[params.prize])

    hero.memes["curiosity"] = 1
    hero.memes["joy"] = 1
    prize.meters["fluttering"] = 1
    prize.meters["at_risk"] = 1

    world.say(f"{hero.id} was a little {params.gender} who loved backyard adventures.")
    world.say(f"One gray afternoon, {wind_warning(ACTIVITIES[params.activity])} {sound_effect('wind')}")

    world.para()
    world.say(f"{hero.id}'s {parent.type} pointed to the line and said, \"Hold on to the laundry before the wind steals it!\"")
    world.say(f"{hero.id} looked up and saw {prize.phrase} fluttering loose. \"I can catch it!\" {hero.pronoun('subject')} said.")

    world.para()
    world.say(f"{hero.id} dashed across the yard. {sound_effect('clothesline')} went the cloth, and {sound_effect('catch')} went {hero.id}'s hand.")
    if gear:
        world.say(f"\"{gear.prep},\" said {params.parent}.")
        world.say(f"{hero.id} nodded and {gear.tail}. {sound_effect('pin')} {sound_effect('pin')}")
        prize.meters["secured"] = 1
        prize.meters["at_risk"] = 0
        hero.memes["pride"] = 1

    world.para()
    world.say(f"In the end, the storm blew past, but the bra stayed on the line.")
    world.say(f"{hero.id} smiled at the tidy clothesline, and {params.parent} laughed, \"That was quite an adventure.\"")

    world.facts.update(hero=hero, parent=parent, prize=prize, gear=gear, setting=world.setting, activity=ACTIVITIES[params.activity], params=params)

    prompts = [
        'Write a short adventure story for a child that uses the word "bra" and includes foreshadowing, dialogue, and sound effects.',
        f"Tell a gentle backyard adventure about {hero.id} helping {params.parent} keep a bra from blowing away in the wind.",
        "Write a small, child-friendly rescue story where a fluttering laundry item needs to be caught before a storm.",
    ]

    story_qa = [
        QAItem(
            question=f"What was blowing around in the backyard story?",
            answer="A bra was fluttering on the clothesline, and the wind kept tugging at it.",
        ),
        QAItem(
            question=f"Why did {hero.id} hurry across the yard?",
            answer=f"{hero.id} hurried across the yard because the wind might blow the bra away before the storm passed.",
        ),
        QAItem(
            question=f"How did {hero.id} and {params.parent} keep the bra safe?",
            answer=f"They used clothespins and careful hands to clip the bra down tight so it would not fly off the line.",
        ),
    ]

    world_qa = [
        QAItem(
            question="What does wind do to light laundry?",
            answer="Wind can make light laundry flutter, flap, and sometimes blow loose if it is not secured well.",
        ),
        QAItem(
            question="What do clothespins do?",
            answer="Clothespins help hold laundry on a clothesline so the wind cannot carry it away.",
        ),
    ]

    return StorySample(params=params, story=world.render(), prompts=prompts, story_qa=story_qa, world_qa=world_qa, world=world)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        lines.append(f"  {e.id:10} ({e.type:8}) meters={e.meters} memes={e.memes}")
    return "\n".join(lines)


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
    lines.append("== (3) World-knowledge questions ==")
    for q in sample.world_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    return "\n".join(lines)


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
        print(asp_program("#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        triples = asp_valid_combos()
        print(f"{len(triples)} compatible (place, activity, prize) combos:")
        for place, activity, prize in triples:
            print(f"  {place:10} {activity:8} {prize:8}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)
    samples: list[StorySample] = []
    if args.all:
        params = StoryParams(place="backyard", activity="wind", prize="bra", name="Maya", gender="girl", parent="mother")
        samples = [generate(params)]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 10):
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

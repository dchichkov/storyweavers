#!/usr/bin/env python3
"""
storyworlds/worlds/rock_n_roll_humor_dialogue_slice_of.py
========================================================

A standalone storyworld for a tiny slice-of-life rock'n'roll comedy.

Premise:
- A kid wants to join a small neighborhood rock'n'roll rehearsal.
- A parent worries the noise will rattle a shared sleeping baby / neighbor.
- The child and a helper find a practical, funny compromise that keeps the music going.
- The ending proves the new setup changed the room, the mood, and the sound.

This world keeps the story grounded in physical meters and emotional memes:
- meters: volume, rumble, tidiness, battery, distance, softness
- memes: joy, worry, embarrassment, pride, patience, amusement, relief

It supports the shared Storyweavers CLI contract, including ASP parity checks.
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
class Person:
    id: str
    type: str
    label: str = ""
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "woman", "sister"}
        male = {"boy", "father", "man", "brother"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]


@dataclass
class Instrument:
    id: str
    label: str
    loudness: float
    kind: str
    battery: float = 0.0
    plugged_in: bool = True


@dataclass
class Setting:
    place: str
    indoors: bool = True
    shared_wall: bool = True


@dataclass
class StoryParams:
    place: str
    hero_name: str
    hero_type: str
    parent_type: str
    instrument: str
    helper: str
    seed: Optional[int] = None


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.people: dict[str, Person] = {}
        self.items: dict[str, Instrument] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict[str, object] = {}
        self.fired: set[str] = set()

    def add_person(self, p: Person) -> Person:
        self.people[p.id] = p
        return p

    def add_item(self, item: Instrument) -> Instrument:
        self.items[item.id] = item
        return item

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)

    def get(self, pid: str) -> Person:
        return self.people[pid]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="A slice-of-life rock'n'roll storyworld with humor and dialogue."
    )
    ap.add_argument("--place", choices=sorted(SETTINGS))
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--parent", choices=["mother", "father"])
    ap.add_argument("--instrument", choices=sorted(INSTRUMENTS))
    ap.add_argument("--helper", choices=sorted(HELPERS))
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


SETTINGS: dict[str, Setting] = {
    "apartment": Setting("the apartment", indoors=True, shared_wall=True),
    "garage": Setting("the garage", indoors=True, shared_wall=False),
    "basement": Setting("the basement", indoors=True, shared_wall=False),
    "living_room": Setting("the living room", indoors=True, shared_wall=True),
}

INSTRUMENTS: dict[str, Instrument] = {
    "ukulele": Instrument("ukulele", "ukulele", loudness=1.5, kind="pluck"),
    "toy_drum": Instrument("toy_drum", "toy drum", loudness=2.5, kind="beat", battery=0.0),
    "tiny_amp": Instrument("tiny_amp", "tiny amp", loudness=3.5, kind="amp", battery=0.5),
    "air_guitar": Instrument("air_guitar", "air guitar", loudness=0.5, kind="air"),
}

HELPERS = {
    "blanket": "a thick blanket",
    "egg_carton": "an egg carton wall",
    "muffin_tin": "a muffin tin beat pad",
    "headphones": "big headphones",
}

GIRL_NAMES = ["Mina", "Ruby", "Ivy", "Tess", "Nina", "Pia"]
BOY_NAMES = ["Owen", "Max", "Finn", "Leo", "Jules", "Kai"]
TRAITS = ["curious", "cheerful", "silly", "spunky", "patient"]

CURATED = [
    StoryParams("apartment", "Mina", "girl", "mother", "tiny_amp", "blanket"),
    StoryParams("living_room", "Leo", "boy", "father", "toy_drum", "egg_carton"),
    StoryParams("basement", "Ivy", "girl", "mother", "ukulele", "headphones"),
]

ASP_RULES = r"""
hero(H) :- person(H).
noisy(X) :- instrument(X), loudness(X,L), L > 2.
can_play(P,I) :- setting(P), instrument(I), not too_loud(P,I).
too_loud(P,I) :- setting(P), instrument(I), shared_wall(P), noisy(I).
humor_fix(P,I,H) :- can_play(P,I), helper(H).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid, s in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        if s.indoors:
            lines.append(asp.fact("indoors", sid))
        if s.shared_wall:
            lines.append(asp.fact("shared_wall", sid))
    for iid, item in INSTRUMENTS.items():
        lines.append(asp.fact("instrument", iid))
        lines.append(asp.fact("kind", iid, item.kind))
        lines.append(asp.fact("loudness", iid, int(item.loudness * 10)))
    for hid in HELPERS:
        lines.append(asp.fact("helper", hid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show can_play/2."))
    asp_set = set(asp.atoms(model, "can_play"))
    py_set = set()
    for sid, setting in SETTINGS.items():
        for iid, item in INSTRUMENTS.items():
            if not (setting.shared_wall and item.loudness > 2):
                py_set.add((sid, iid))
    if asp_set == py_set:
        print(f"OK: clingo gate matches python ({len(py_set)} combos).")
        return 0
    print("MISMATCH between clingo and python.")
    print("only in asp:", sorted(asp_set - py_set))
    print("only in py:", sorted(py_set - asp_set))
    return 1


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.instrument and args.place:
        if args.place == "apartment" and INSTRUMENTS[args.instrument].loudness > 2:
            raise StoryError(
                "That instrument would be too loud for the apartment's shared wall; "
                "the parent would have a real reason to worry."
            )
    places = [args.place] if args.place else list(SETTINGS)
    instruments = [args.instrument] if args.instrument else list(INSTRUMENTS)
    valid = []
    for place in places:
        setting = SETTINGS[place]
        for inst in instruments:
            if setting.shared_wall and INSTRUMENTS[inst].loudness > 2:
                continue
            valid.append((place, inst))
    if not valid:
        raise StoryError("(No valid combination matches the given options.)")
    place, instrument = rng.choice(valid)
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    parent = args.parent or rng.choice(["mother", "father"])
    helper = args.helper or rng.choice(list(HELPERS))
    return StoryParams(place, name, gender, parent, instrument, helper)


def can_play(setting: Setting, item: Instrument) -> bool:
    return not (setting.shared_wall and item.loudness > 2)


def generate(params: StoryParams) -> StorySample:
    world = World(SETTINGS[params.place])
    hero = world.add_person(Person(params.hero_name, params.hero_type))
    parent = world.add_person(Person("Parent", params.parent_type, label="parent"))
    helper = HELPERS[params.helper]
    inst = world.add_item(INSTRUMENTS[params.instrument])

    hero.memes.update({"joy": 1.0, "want": 1.0})
    parent.memes.update({"worry": 1.0, "patience": 0.5})
    hero.meters.update({"distance": 0.0, "volume": 0.0})
    inst.battery = 1.0 if inst.id == "toy_drum" else inst.battery

    intro = f"{hero.id} loved rock'n'roll and practiced little riffs in {world.setting.place}."
    joke = f"{hero.pronoun().capitalize()} said the beat was 'tiny, but with big attitude.'"
    world.say(intro)
    world.say(joke)
    world.para()
    world.say(
        f"One evening, {hero.id} wanted to play the {inst.label} right away, "
        f"but {hero.pronoun('possessive')} {parent.type} pointed at the shared wall."
    )

    if not can_play(world.setting, inst):
        parent.memes["worry"] += 1
        hero.memes["embarrassment"] = 1.0
        world.say(
            f'"If we turn that up," {hero.pronoun("possessive")} {parent.type} said, '
            f'"the neighbors will hear every drum-shaped thought."'
        )
        world.say(f"{hero.id} blinked. 'Even my very artistic thoughts?'")
        world.say(f'"Especially those,' {parent.pronoun()} said, trying not to laugh.')
        world.para()
        world.say(
            f"Then {helper} showed up with a funny idea: put {helper} around the sound spot "
            f"and use the {inst.label} like a quiet rehearsal toy."
        )
        hero.memes["amusement"] = 1.0
        parent.memes["relief"] = 1.0
        world.say(
            f"'{helper.capitalize()} is not exactly a concert hall,' {hero.id} said, "
            f"grinning, 'but it does have excellent dramatic texture.'"
        )
        world.say(
            f"{hero.id} played softer, tapping a goofy rhythm while {parent.id} nodded along. "
            f"The room stayed calm, and the beat still bounced around like a happy marble."
        )
    else:
        world.say(
            f"{parent.id} shrugged and said, 'That one is fine here. "
            f"Just keep it friendly and neighbor-sized.'"
        )
        hero.memes["pride"] = 1.0
        world.say(
            f"{hero.id} laughed and answered, 'I can do neighbor-sized rock'n'roll!'"
        )
        world.say(
            f"The song came out bright and bouncy, and even the kettle seemed to tap its foot."
        )

    world.para()
    world.say(
        f"By the end, {hero.id} had a smile, {parent.id} had less worry, "
        f"and the {inst.label} sounded like it belonged in a very funny little concert."
    )

    world.facts.update(
        hero=hero,
        parent=parent,
        helper=helper,
        instrument=inst,
        setting=world.setting,
        resolved=True,
        noisy=not can_play(world.setting, inst),
    )
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero: Person = f["hero"]
    inst: Instrument = f["instrument"]
    return [
        "Write a small slice-of-life story about a kid and a tiny rock'n'roll rehearsal, with a funny compromise.",
        f"Tell a dialogue-driven story where {hero.id} wants to play a {inst.label}, but the sound needs a kinder plan.",
        "Make the ending cheerful, ordinary, and concrete, with music, humor, and a parent-child conversation.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero: Person = f["hero"]
    parent: Person = f["parent"]
    inst: Instrument = f["instrument"]
    qs = [
        QAItem(
            question=f"What did {hero.id} want to play?",
            answer=f"{hero.id} wanted to play the {inst.label}, because {hero.pronoun()} loved rock'n'roll.",
        ),
        QAItem(
            question=f"Why was {parent.pronoun().capitalize()} worried in the story?",
            answer=f"{parent.pronoun().capitalize()} worried because the {inst.label} could be too loud for the shared wall and bother other people.",
        ),
        QAItem(
            question="What funny idea helped the family solve the problem?",
            answer=f"They used {f['helper']} and a quieter practice so the music could stay playful without shaking the whole place.",
        ),
    ]
    if f["noisy"]:
        qs.append(
            QAItem(
                question="How did the child and parent feel at the end?",
                answer=f"{hero.id} felt amused and proud, and {parent.id} felt relieved because they found a calmer way to keep playing.",
            )
        )
    return qs


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is rock'n'roll?",
            answer="Rock'n'roll is a kind of lively music with a strong beat, often played with guitars, drums, and lots of energy.",
        ),
        QAItem(
            question="Why can a shared wall matter in an apartment?",
            answer="A shared wall can let sounds travel into the next home, so loud music may bother neighbors.",
        ),
    ]


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for p in world.people.values():
        lines.append(f"  {p.id:8} ({p.type:7}) meters={p.meters} memes={p.memes}")
    for i in world.items.values():
        lines.append(f"  {i.id:8} (item   ) loudness={i.loudness} battery={i.battery}")
    return "\n".join(lines)


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world is not None:
        print(dump_trace(sample.world))
    if qa:
        print()
        for block, items in (
            ("== (1) Generation prompts ==", sample.prompts),
            ("== (2) Story questions ==", sample.story_qa),
            ("== (3) World knowledge ==", sample.world_qa),
        ):
            print(block)
            for item in items:
                print(f"Q: {item.question}")
                print(f"A: {item.answer}")
            print()


def valid_combos() -> list[tuple[str, str]]:
    out = []
    for place, setting in SETTINGS.items():
        for iid, item in INSTRUMENTS.items():
            if can_play(setting, item):
                out.append((place, iid))
    return out


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show can_play/2."))
    return sorted(set(asp.atoms(model, "can_play")))


def asp_valid_stories() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show can_play/2."))
    return sorted(set(asp.atoms(model, "can_play")))


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show can_play/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible combos:")
        for place, inst in combos:
            print(f"  {place:12} {inst}")
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
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.hero_name}: {p.instrument} at {p.place}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.place and args.instrument and not can_play(SETTINGS[args.place], INSTRUMENTS[args.instrument]):
        raise StoryError(
            f"(No story: the {args.instrument} is too loud for {args.place}, so the "
            "parent would have no honest reason to allow the rehearsal.)"
        )
    combos = valid_combos()
    if args.place:
        combos = [c for c in combos if c[0] == args.place]
    if args.instrument:
        combos = [c for c in combos if c[1] == args.instrument]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, instrument = rng.choice(combos)
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    parent = args.parent or rng.choice(["mother", "father"])
    helper = args.helper or rng.choice(sorted(HELPERS))
    return StoryParams(place, name, gender, parent, instrument, helper)


if __name__ == "__main__":
    main()

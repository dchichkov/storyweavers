#!/usr/bin/env python3
"""
A small slice-of-life storyworld about kids, a tiny rock'n'roll rehearsal, a
humorous mix-up, and a gentle ending that proves what changed.
"""

from __future__ import annotations

import argparse
import copy
import json
import os
import random
import sys
from dataclasses import dataclass, field
from typing import Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from results import QAItem, StoryError, StorySample  # noqa: E402


# ---------------------------------------------------------------------------
# Domain model
# ---------------------------------------------------------------------------

@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    role: str = ""
    attrs: dict = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "woman", "mother"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man", "father"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]


@dataclass
class Place:
    id: str
    label: str
    meters: dict[str, float] = field(default_factory=dict)
    attrs: dict = field(default_factory=dict)


@dataclass
class Instrument:
    id: str
    label: str
    sound: str
    volume: int
    fragile: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    attrs: dict = field(default_factory=dict)


@dataclass
class TinyProblem:
    id: str
    label: str
    hazard: str
    wobble: int
    fixable: bool = True
    meters: dict[str, float] = field(default_factory=dict)
    attrs: dict = field(default_factory=dict)


@dataclass
class Fix:
    id: str
    label: str
    method: str
    strength: int
    text: str
    fail: str
    qa_text: str


@dataclass
class StoryParams:
    band_name: str
    musician1: str
    musician1_gender: str
    musician2: str
    musician2_gender: str
    adult: str
    adult_gender: str
    place: str
    instrument1: str
    instrument2: str
    problem: str
    fix: str
    seed: Optional[int] = None


class World:
    def __init__(self) -> None:
        self.entities: dict[str, object] = {}
        self.story: list[str] = []
        self.facts: dict[str, object] = {}

    def add(self, entity):
        self.entities[entity.id] = entity
        return entity

    def get(self, eid: str):
        return self.entities[eid]

    def say(self, text: str) -> None:
        if text:
            self.story.append(text)

    def render(self) -> str:
        return "\n".join(self.story)

    def copy(self) -> "World":
        w = World()
        w.entities = copy.deepcopy(self.entities)
        w.story = []
        w.facts = copy.deepcopy(self.facts)
        return w


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------

PLACES = {
    "kitchen": Place("kitchen", "the kitchen", attrs={"setting": "home"}),
    "garage": Place("garage", "the garage", attrs={"setting": "home"}),
    "porch": Place("porch", "the porch", attrs={"setting": "home"}),
    "living_room": Place("living_room", "the living room", attrs={"setting": "home"}),
}

INSTRUMENTS = {
    "guitar": Instrument("guitar", "the toy guitar", "twang", 3),
    "drum": Instrument("drum", "the little drum", "boom", 4, fragile=True),
    "keyboard": Instrument("keyboard", "the tiny keyboard", "plink", 2),
    "mic": Instrument("mic", "the toy microphone", "la-la", 2),
}

PROBLEMS = {
    "spilled_soda": TinyProblem("spilled_soda", "spilled soda", "made the floor sticky", 2, True),
    "snagged_cable": TinyProblem("snagged_cable", "snagged cable", "kept the music from starting", 1, True),
    "too_loud_echo": TinyProblem("too_loud_echo", "too-loud echo", "made everyone cringe", 1, True),
    "stuck_button": TinyProblem("stuck_button", "stuck button", "kept the keyboard from clicking", 2, True),
}

FIXES = {
    "towel": Fix("towel", "a dish towel", "wipe it up", 2,
                 "wiped the mess with a dish towel",
                 "wiped, but the mess was too big and only spread around",
                 "wiped the mess with a dish towel"),
    "unplug": Fix("unplug", "a quick unplug", "unplug it", 2,
                  "unplugged the cable and set it straight",
                  "tried to unplug it, but the cord was jammed too tight",
                  "unplugged the cable and set it straight"),
    "muffle": Fix("muffle", "a couch pillow", "muffle the echo", 2,
                  "pressed a couch pillow near the wall and softened the echo",
                  "held up a pillow, but the echo kept bouncing back",
                  "pressed a couch pillow near the wall and softened the echo"),
}

BANDS = [
    "The Back-Pocket Rockets",
    "The Sofa Sparks",
    "The Snack-Time Strummers",
    "The Garage Glitter",
    "The Pogo Pickers",
]

GIRL_NAMES = ["Mia", "Zoe", "Luna", "Ivy", "Nora", "Ada"]
BOY_NAMES = ["Ben", "Leo", "Max", "Owen", "Finn", "Jude"]


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------

ASP_RULES = r"""
has_band(B) :- band(B).
good_fix(F) :- fix(F).
problematic(P) :- problem(P).
compatible(B,P,F) :- band(B), problem(P), fix(F).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for b in BANDS:
        lines.append(asp.fact("band", b))
    for p in PROBLEMS:
        lines.append(asp.fact("problem", p))
    for f in FIXES:
        lines.append(asp.fact("fix", f))
    return "\n".join(lines)


def asp_program(extra: str = "", show: str = "") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program(show="#show has_band/1. #show good_fix/1. #show compatible/3."))
    bands = sorted(x[0] for x in asp.atoms(model, "has_band"))
    fixes = sorted(x[0] for x in asp.atoms(model, "good_fix"))
    combos = sorted(asp.atoms(model, "compatible"))
    ok = (bands == sorted(BANDS) and fixes == sorted(FIXES) and len(combos) == len(BANDS) * len(PROBLEMS) * len(FIXES))
    print("OK" if ok else "MISMATCH")
    return 0 if ok else 1


# ---------------------------------------------------------------------------
# Story logic
# ---------------------------------------------------------------------------

def _name_pool(gender: str) -> list[str]:
    return GIRL_NAMES if gender == "girl" else BOY_NAMES


def _pick_name(rng: random.Random, gender: Optional[str] = None) -> tuple[str, str]:
    g = gender or rng.choice(["girl", "boy"])
    return rng.choice(_name_pool(g)), g


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A slice-of-life rock'n'roll storyworld.")
    ap.add_argument("--band", choices=BANDS)
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--instrument1", choices=INSTRUMENTS)
    ap.add_argument("--instrument2", choices=INSTRUMENTS)
    ap.add_argument("--problem", choices=PROBLEMS)
    ap.add_argument("--fix", choices=FIXES)
    ap.add_argument("--adult", choices=["mom", "dad"])
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
    band = args.band or rng.choice(BANDS)
    place = args.place or rng.choice(list(PLACES))
    instrument1, instrument2 = args.instrument1, args.instrument2
    if not instrument1 or not instrument2:
        instrument1, instrument2 = rng.sample(list(INSTRUMENTS), 2)
    problem = args.problem or rng.choice(list(PROBLEMS))
    fix = args.fix or rng.choice(list(FIXES))
    adult = args.adult or rng.choice(["mom", "dad"])
    n1, g1 = _pick_name(rng)
    n2, g2 = _pick_name(rng, gender="boy" if g1 == "girl" else "girl")
    return StoryParams(
        band_name=band,
        musician1=n1,
        musician1_gender=g1,
        musician2=n2,
        musician2_gender=g2,
        adult="Mom" if adult == "mom" else "Dad",
        adult_gender="mother" if adult == "mom" else "father",
        place=place,
        instrument1=instrument1,
        instrument2=instrument2,
        problem=problem,
        fix=fix,
    )


def _story_setup(world: World, p: StoryParams) -> None:
    m1 = world.add(Entity(p.musician1, "character", p.musician1_gender, role="musician", memes={"joy": 1}))
    m2 = world.add(Entity(p.musician2, "character", p.musician2_gender, role="musician", memes={"joy": 1}))
    adult = world.add(Entity(p.adult, "character", p.adult_gender, role="adult"))
    place = world.add(copy.deepcopy(PLACES[p.place]))
    i1 = world.add(copy.deepcopy(INSTRUMENTS[p.instrument1]))
    i2 = world.add(copy.deepcopy(INSTRUMENTS[p.instrument2]))
    prob = world.add(copy.deepcopy(PROBLEMS[p.problem]))
    fix = world.add(copy.deepcopy(FIXES[p.fix]))
    world.facts.update(locals())


def generate(params: StoryParams) -> StorySample:
    w = World()
    _story_setup(w, params)
    m1: Entity = w.get(params.musician1)
    m2: Entity = w.get(params.musician2)
    adult: Entity = w.get(params.adult)
    place: Place = w.get(params.place)
    i1: Instrument = w.get(params.instrument1)
    i2: Instrument = w.get(params.instrument2)
    prob: TinyProblem = w.get(params.problem)
    fix: Fix = w.get(params.fix)

    m1.memes["excitement"] = 1
    m2.memes["excitement"] = 1
    place.meters["noise"] = 0

    w.say(f"On a lazy afternoon, {m1.id} and {m2.id} turned {place.label} into a tiny rock'n'roll stage.")
    w.say(f'{m1.id} strummed {i1.label}, {m2.id} tapped {i2.label}, and both of them grinned at the silly, homemade thunder.')

    # Problem appears
    place.meters["trouble"] = 1
    if params.problem == "too_loud_echo":
        w.say(f'“Wow,” {m2.id} said. “My voice just came back at me like it had a drum solo.”')
        w.say(f'{m1.id} laughed. “Even the walls want an encore.”')
    elif params.problem == "spilled_soda":
        w.say(f"Then a cup of soda tipped over and made the floor sticky under their socks.")
        w.say(f'{m2.id} hopped. “My feet are officially glued to the stage,” {m2.pronoun()} joked.')
    elif params.problem == "snagged_cable":
        w.say(f"Then the cable curled into a knot and the music refused to start.")
        w.say(f'{m1.id} squinted. “The cord is doing rock'n'roll too hard.”')
    else:
        w.say(f"Then a button on the tiny keyboard got stuck and only made a tiny click.")
        w.say(f'{m2.id} frowned. “That key is on strike.”')

    # Fix
    if fix.id == "towel":
        place.meters["trouble"] = 0
        w.say(f'{adult.id} came by with a smile and said, “Hand me that towel.” {adult.pronoun().capitalize()} {fix.text}, and the floor was fine again.')
    elif fix.id == "unplug":
        place.meters["trouble"] = 0
        w.say(f'{adult.id} peeked in and said, “Easy. Let me see.” {adult.pronoun().capitalize()} {fix.text}, and the band started up again.')
    else:
        place.meters["trouble"] = 0
        w.say(f'{adult.id} laughed and said, “This is a pillow emergency.” {adult.pronoun().capitalize()} {fix.text}, and the sound turned cozy instead of wild.')

    # Ending
    m1.memes["pride"] = 1
    m2.memes["pride"] = 1
    w.say(f'By the time the sun slid lower, the {params.band_name} had a cleaner beat and a funnier story.')
    w.say(f'{m2.id} bowed. “We fixed it without turning the house into a stadium,” {m2.pronoun()} said.')
    w.say(f'{m1.id} nodded. “Yeah,” {m1.id} said, “our encore was just the broom, not the disaster.”')

    story = w.render()
    prompts = [
        f"Write a slice-of-life story about {m1.id} and {m2.id} making rock'n'roll music in {place.label} and solving a small problem with help from {adult.id}.",
        f"Tell a humorous, dialogue-driven story where kids in {params.band_name} keep playing after a tiny mishap with {prob.label}.",
        f"Write a gentle rock'n'roll scene where the children fix {prob.label} using {fix.label} and end the day smiling.",
    ]
    story_qa = [
        QAItem(f"What were {m1.id} and {m2.id} doing in {place.label}?", f"They were making a little rock'n'roll band and playing music together."),
        QAItem(f"What small problem happened during the music?", f"{prob.label.capitalize()} happened, which made the practice awkward."),
        QAItem(f"How did {adult.id} help?", f"{adult.id} helped by {fix.qa_text}."),
        QAItem(f"How did the story end?", f"It ended with the kids smiling, the problem fixed, and their band sounding better than before."),
    ]
    world_qa = [
        QAItem("What is a guitar?", "A guitar is a string instrument that can make a twangy sound when you play it."),
        QAItem("What does a drum do?", "A drum makes a strong beat when you tap or hit it."),
        QAItem("Why do people like rock'n'roll?", "Rock'n'roll is lively music with a strong beat that can make people want to move or dance."),
    ]
    return StorySample(params=params, story=story, prompts=prompts, story_qa=story_qa, world_qa=world_qa, world=w)


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world is not None:
        print("--- trace ---")
        for e in sample.world.entities.values():
            print(e.id, e.kind, e.type, e.role, e.meters, e.memes)
    if qa:
        print()
        for i, p in enumerate(sample.prompts, 1):
            print(f"P{i}: {p}")
        for q in sample.story_qa:
            print(f"Q: {q.question}\nA: {q.answer}")
        for q in sample.world_qa:
            print(f"Q: {q.question}\nA: {q.answer}")


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program(show="#show has_band/1. #show good_fix/1. #show compatible/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        model = asp.one_model(asp_program(show="#show has_band/1. #show good_fix/1. #show compatible/3."))
        print("bands:", sorted(x[0] for x in asp.atoms(model, "has_band")))
        print("fixes:", sorted(x[0] for x in asp.atoms(model, "good_fix")))
        print("compat:", len(asp.atoms(model, "compatible")))
        return

    rng = random.Random(args.seed if args.seed is not None else random.randrange(2**31))
    samples = []
    if args.all:
        for b in BANDS:
            p = StoryParams(
                band_name=b, musician1="Mia", musician1_gender="girl", musician2="Ben", musician2_gender="boy",
                adult="Mom", adult_gender="mother", place="living_room", instrument1="guitar", instrument2="drum",
                problem="spilled_soda", fix="towel",
            )
            samples.append(generate(p))
    else:
        for i in range(args.n):
            params = resolve_params(args, random.Random(rng.randint(0, 2**31 - 1)))
            samples.append(generate(params))

    if args.json:
        print(json.dumps([s.to_dict() for s in samples] if len(samples) > 1 else samples[0].to_dict(), indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        emit(sample, trace=args.trace, qa=args.qa, header=(f"### variant {i+1}" if len(samples) > 1 else ""))



if __name__ == "__main__":
    main()

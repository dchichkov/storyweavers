#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/thong_urinal_auto_teamwork_mystery_to_solve.py
==============================================================================

A small slice-of-life storyworld about an auto garage, a puzzling restroom clue,
and a pair of helpers who solve the mystery together.

Seed words:
- thong
- urinal
- auto

Features:
- Teamwork
- Mystery to Solve

Style:
- Slice of Life
"""

from __future__ import annotations

import argparse
import copy
import json
import os
import random
import sys
from collections import defaultdict
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
    role: str = ""
    attrs: dict = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "woman", "mother"}
        male = {"boy", "man", "father"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]


@dataclass
class Place:
    id: str
    label: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Clue:
    id: str
    label: str
    reveal: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Fix:
    id: str
    label: str
    method: str
    power: int
    sense: int
    tags: set[str] = field(default_factory=set)


@dataclass
class StoryParams:
    place: str
    clue: str
    fix: str
    lead: str
    lead_gender: str
    helper: str
    helper_gender: str
    adult: str
    seed: Optional[int] = None


PLACES = {
    "auto_shop": Place(id="auto_shop", label="the auto shop", tags={"auto"}),
    "parking_lot": Place(id="parking_lot", label="the parking lot", tags={"auto"}),
}

CLUES = {
    "thong": Clue(
        id="thong",
        label="a thong sandal",
        reveal="the thong sandal had been dangling from the restroom hook",
        tags={"thong", "shoe"},
    ),
    "urinal": Clue(
        id="urinal",
        label="the urinal",
        reveal="there was a tiny toy car wedged beside the urinal",
        tags={"urinal", "mystery"},
    ),
    "auto": Clue(
        id="auto",
        label="an auto key",
        reveal="the auto key had slipped behind the sink and made the beeping noise",
        tags={"auto", "key"},
    ),
}

FIXES = {
    "teamwork": Fix(
        id="teamwork",
        label="a careful team plan",
        method="look together, listen together, and search one small spot at a time",
        power=3,
        sense=3,
        tags={"teamwork"},
    ),
    "listen": Fix(
        id="listen",
        label="a listening trick",
        method="follow the little sound and check the place where it echoed",
        power=2,
        sense=3,
        tags={"teamwork"},
    ),
    "clean_up": Fix(
        id="clean_up",
        label="a tidy-up plan",
        method="wipe the floor, move the bucket, and check under the sink",
        power=1,
        sense=2,
        tags={"teamwork"},
    ),
}

GIRL_NAMES = ["Mia", "Lily", "Nora", "Zoe", "Ava", "Ella"]
BOY_NAMES = ["Noah", "Theo", "Finn", "Max", "Leo", "Ben"]


class World:
    def __init__(self) -> None:
        self.entities: dict[str, Entity] = {}
        self.fired: set[str] = set()
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
        w = World()
        w.entities = copy.deepcopy(self.entities)
        w.fired = set(self.fired)
        w.paragraphs = [[]]
        return w


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for place in PLACES:
        for clue in CLUES:
            for fix in FIXES:
                combos.append((place, clue, fix))
    return combos


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Slice-of-life storyworld about teamwork and a small mystery.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--clue", choices=CLUES)
    ap.add_argument("--fix", choices=FIXES)
    ap.add_argument("--lead")
    ap.add_argument("--lead-gender", choices=["girl", "boy"])
    ap.add_argument("--helper")
    ap.add_argument("--helper-gender", choices=["girl", "boy"])
    ap.add_argument("--adult", choices=["mechanic", "cashier", "parent"])
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
    combos = [c for c in valid_combos()
              if (args.place is None or c[0] == args.place)
              and (args.clue is None or c[1] == args.clue)
              and (args.fix is None or c[2] == args.fix)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, clue, fix = rng.choice(sorted(combos))
    lead_gender = args.lead_gender or rng.choice(["girl", "boy"])
    helper_gender = args.helper_gender or ("boy" if lead_gender == "girl" and rng.random() < 0.5 else "girl")
    lead = args.lead or rng.choice(GIRL_NAMES if lead_gender == "girl" else BOY_NAMES)
    helper_pool = [n for n in (GIRL_NAMES if helper_gender == "girl" else BOY_NAMES) if n != lead]
    helper = args.helper or rng.choice(helper_pool)
    adult = args.adult or rng.choice(["mechanic", "cashier", "parent"])
    return StoryParams(place=place, clue=clue, fix=fix, lead=lead, lead_gender=lead_gender,
                       helper=helper, helper_gender=helper_gender, adult=adult)


def _story_template(world: World, p: StoryParams) -> None:
    lead = world.add(Entity(id=p.lead, kind="character", type=p.lead_gender, role="lead"))
    helper = world.add(Entity(id=p.helper, kind="character", type=p.helper_gender, role="helper"))
    adult = world.add(Entity(id="Adult", kind="character", type="adult", role=p.adult))
    clue = CLUES[p.clue]
    fix = FIXES[p.fix]
    place = PLACES[p.place]

    lead.memes["curiosity"] += 1
    helper.memes["kindness"] += 1

    world.say(
        f"On an ordinary afternoon at {place.label}, {lead.id} and {helper.id} "
        f"waited beside {place.label} while {adult.role} checked an auto."
    )
    world.say(
        f"Then the two kids noticed a funny clue. {clue.reveal}. "
        f"They leaned closer and tried to guess what it meant."
    )

    world.para()
    lead.memes["curiosity"] += 1
    helper.memes["teamwork"] += 1
    world.say(
        f'"Maybe we should solve it together," {helper.id} said. '
        f'"Let’s use {fix.label}."'
    )
    world.say(
        f"{lead.id} nodded, and they tried to {fix.method}."
    )

    world.para()
    world.say(
        f"{adult.role.capitalize()} laughed softly when the answer came clear: "
        f"the mystery was simple all along."
    )
    world.say(
        f"It turned out that {clue.reveal}, so the strange little problem was only a small mix-up."
    )
    world.say(
        f"With everyone helping, the auto was ready, the restroom was calm again, "
        f"and {lead.id} and {helper.id} walked out feeling proud."
    )

    lead.memes["pride"] += 1
    helper.memes["pride"] += 1
    world.facts.update(
        lead=lead,
        helper=helper,
        adult=adult,
        clue=clue,
        fix=fix,
        place=place,
        solved=True,
        mystery=clue.id,
    )


def generate(params: StoryParams) -> StorySample:
    if params.place not in PLACES or params.clue not in CLUES or params.fix not in FIXES:
        raise StoryError("Invalid story parameters.")
    world = World()
    _story_template(world, params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=[QAItem(question=q, answer=a) for q, a in story_qa(world)],
        world_qa=[QAItem(question=q, answer=a) for q, a in world_knowledge_qa(world)],
        world=world,
    )


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a slice-of-life mystery story that includes the words "{f["clue"].label}", "auto", and "thong".',
        f"Tell a gentle story where {f['lead'].id} and {f['helper'].id} solve a small mystery together at {f['place'].label}.",
        f"Write a story about teamwork at {f['place'].label}, where a child notices a clue and an adult explains the answer calmly.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    lead = f["lead"]
    helper = f["helper"]
    adult = f["adult"]
    clue = f["clue"]
    fix = f["fix"]
    qa = [
        ("What kind of story is this?", "It is a small everyday mystery story about people helping each other and noticing a clue."),
        ("Who solved the mystery?", f"{lead.id} and {helper.id} solved it together, with {adult.role} helping them stay calm."),
        ("What was the clue?", f"The clue was {clue.label}. It looked strange at first, but it helped point the kids toward the answer."),
        ("How did they work together?", f"They used {fix.label} and followed {fix.method}. That teamwork let them figure out the mystery without any fuss."),
    ]
    qa.append((
        "Why did the story feel like a slice of life?",
        f"Because it happened during an ordinary wait at the auto shop, and the people talked and helped one another like a normal day."
    ))
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    clue = f["clue"].id
    qa = []
    if clue == "thong":
        qa.append(("What is a thong sandal?", "A thong sandal is a light sandal with a strap between the toes. People wear them in warm weather because they are easy to slip on."))
    if clue == "urinal":
        qa.append(("What is a urinal?", "A urinal is a restroom fixture that some people use for peeing. It is usually found in public bathrooms."))
    if clue == "auto":
        qa.append(("What is an auto?", "An auto is another word for a car. It is a vehicle people use to travel from place to place."))
    qa.append(("What does teamwork mean?", "Teamwork means people help each other and do a job together. When they share the work, they can solve problems more easily."))
    qa.append(("What is a mystery?", "A mystery is a question that does not make sense right away. People solve it by looking carefully and thinking through the clues."))
    return qa


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
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if e.role:
            bits.append(f"role={e.role}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    return "\n".join(lines)


CURATED = [
    StoryParams(place="auto_shop", clue="thong", fix="teamwork", lead="Mia", lead_gender="girl", helper="Ben", helper_gender="boy", adult="mechanic"),
    StoryParams(place="auto_shop", clue="urinal", fix="listen", lead="Noah", lead_gender="boy", helper="Lily", helper_gender="girl", adult="cashier"),
    StoryParams(place="parking_lot", clue="auto", fix="clean_up", lead="Ava", lead_gender="girl", helper="Leo", helper_gender="boy", adult="parent"),
]


def valid_story_params(params: StoryParams) -> bool:
    return params.place in PLACES and params.clue in CLUES and params.fix in FIXES


ASP_RULES = r"""
valid(P,C,F) :- place(P), clue(C), fix(F).
solved(C) :- clue(C), teamwork(F), fix(F).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for pid in PLACES:
        lines.append(asp.fact("place", pid))
    for cid in CLUES:
        lines.append(asp.fact("clue", cid))
    for fid in FIXES:
        lines.append(asp.fact("fix", fid))
        if fid == "teamwork":
            lines.append(asp.fact("teamwork", fid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    rc = 0
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: ASP matches valid_combos() ({len(py)} combos).")
    else:
        rc = 1
        print("Mismatch between ASP and Python.")
    try:
        sample = generate(resolve_params(argparse.Namespace(place=None, clue=None, fix=None, lead=None, lead_gender=None, helper=None, helper_gender=None, adult=None), random.Random(7)))
        _ = sample.story
        print("OK: generate() smoke test passed.")
    except Exception as e:
        rc = 1
        print(f"Smoke test failed: {e}")
    return rc


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
        for item in asp_valid_combos():
            print(item)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 50, 50):
            seed = base_seed + i
            i += 1
            params = resolve_params(args, random.Random(seed))
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

#!/usr/bin/env python3
"""
storyworlds/worlds/tear_reconciliation_mystery_to_solve_slice_of.py
===================================================================

A small slice-of-life story world about a tear, a tiny mystery to solve, and a
gentle reconciliation.

Premise:
- A child notices a tear in an everyday item.
- The tear creates a small mystery: what caused it?
- A misunderstanding grows briefly, then the characters investigate and repair
  the item together.
- The ending proves the change through a repaired object and softer feelings.

The world is intentionally small and state-driven.  Physical state tracks the
tear, the item's condition, and repair progress.  Emotional state tracks worry,
annoyance, blame, relief, and reconciliation.

This file is standalone and uses only the standard library plus the shared
results containers eagerly; ASP helpers are imported lazily if verification or
ASP modes are requested.
"""

from __future__ import annotations

import argparse
import json
import os
import random
import sys
from dataclasses import dataclass, field, asdict
from typing import Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from results import QAItem, StoryError, StorySample  # noqa: E402

THRESHOLD = 1.0


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
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def p(self, case: str = "subject") -> str:
        t = self.type
        female = {"girl", "mother", "woman", "sister"}
        male = {"boy", "father", "man", "brother"}
        if t in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if t in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def pronoun(self) -> str:
        return self.p()

    def it(self) -> str:
        return "them" if self.type in {"scissors", "glasses"} else "it"


@dataclass
class Setting:
    place: str = "the living room"
    location_detail: str = "the couch"
    indoors: bool = True


@dataclass
class ObjectCfg:
    id: str
    label: str
    phrase: str
    kind: str
    tear_location: str
    repair_method: str
    mystery_clue: str
    value: str
    plural: bool = False


@dataclass
class StoryParams:
    place: str
    object: str
    name: str
    helper: str
    trait: str
    seed: Optional[int] = None


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[str] = set()
        self.facts: dict = {}

    def add(self, e: Entity) -> Entity:
        self.entities[e.id] = e
        return e

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
        import copy
        w = World(self.setting)
        w.entities = copy.deepcopy(self.entities)
        w.fired = set(self.fired)
        w.paragraphs = [[]]
        w.facts = dict(self.facts)
        return w


SETTINGS = {
    "living_room": Setting("the living room", "the couch", True),
    "kitchen": Setting("the kitchen", "the chair by the table", True),
    "bedroom": Setting("the bedroom", "the bedside chair", True),
    "laundry_room": Setting("the laundry room", "the folding table", True),
}

OBJECTS = {
    "pillow": ObjectCfg(
        id="pillow",
        label="pillow",
        phrase="a soft pillow with a blue cover",
        kind="pillow",
        tear_location="seam",
        repair_method="sew",
        mystery_clue="a loose zipper on the couch cover",
        value="favorite",
    ),
    "teddy": ObjectCfg(
        id="teddy",
        label="teddy bear",
        phrase="a small teddy bear with a red scarf",
        kind="toy",
        tear_location="arm",
        repair_method="stitch",
        mystery_clue="a tiny snag on the blanket basket",
        value="well-loved",
    ),
    "blanket": ObjectCfg(
        id="blanket",
        label="blanket",
        phrase="a warm plaid blanket",
        kind="blanket",
        tear_location="edge",
        repair_method="patch",
        mystery_clue="a snagged sweater button",
        value="cozy",
    ),
    "bag": ObjectCfg(
        id="bag",
        label="tote bag",
        phrase="a canvas tote bag with painted flowers",
        kind="bag",
        tear_location="handle",
        repair_method="mend",
        mystery_clue="a sharp corner on a toy box",
        value="useful",
    ),
}

NAMES = ["Mia", "Leo", "Nora", "Ben", "Ivy", "Theo", "Ava", "Noah"]
TRAITS = ["curious", "gentle", "quiet", "careful", "patient", "kind"]
HELPERS = ["mother", "father", "grandma", "grandpa", "sister", "brother"]


def valid_combos() -> list[tuple[str, str]]:
    return [(p, o) for p in SETTINGS for o in OBJECTS]


def asp_facts() -> str:
    import asp
    lines = []
    for sid, s in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        lines.append(asp.fact("place_name", sid, s.place))
    for oid, o in OBJECTS.items():
        lines.append(asp.fact("object", oid))
        lines.append(asp.fact("repair_method", oid, o.repair_method))
        lines.append(asp.fact("mystery_clue", oid, o.mystery_clue))
    return "\n".join(lines)


ASP_RULES = r"""
compatible(P,O) :- setting(P), object(O).
#show compatible/2.
"""


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show compatible/2."))
    return sorted(set(asp.atoms(model, "compatible")))


def asp_verify() -> int:
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: clingo matches Python ({len(py)} combos).")
        return 0
    print("MISMATCH")
    print("python-only:", sorted(py - cl))
    print("clingo-only:", sorted(cl - py))
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Slice-of-life tear, mystery, reconciliation.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--object", choices=OBJECTS)
    ap.add_argument("--name", choices=NAMES)
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
    combos = valid_combos()
    if args.place:
        combos = [c for c in combos if c[0] == args.place]
    if args.object:
        combos = [c for c in combos if c[1] == args.object]
    if not combos:
        raise StoryError("No valid setting/object pair matches those choices.")
    place, obj = rng.choice(combos)
    return StoryParams(
        place=place,
        object=obj,
        name=args.name or rng.choice(NAMES),
        helper=args.helper or rng.choice(HELPERS),
        trait=args.trait or rng.choice(TRAITS),
    )


def generate_mystery(world: World, hero: Entity, helper: Entity, cfg: ObjectCfg) -> None:
    hero.memes["worry"] += 1
    world.say(
        f"{hero.id} noticed a tear in {hero.pronoun('possessive')} {cfg.label} and frowned."
    )
    world.say(
        f"At first {hero.id} wondered if someone had broken it, and the little mystery sat there."
    )
    helper.memes["curiosity"] += 1
    world.say(
        f"{helper.id} came over and said they could look closely together."
    )
    world.say(
        f"Near {world.setting.location_detail}, they found {cfg.mystery_clue}, which explained the tear."
    )
    world.facts["clue"] = cfg.mystery_clue
    world.facts["tear"] = cfg.tear_location


def repair_and_reconcile(world: World, hero: Entity, helper: Entity, cfg: ObjectCfg, item: Entity) -> None:
    hero.memes["blame"] += 1
    world.say(
        f"{hero.id} admitted that the tear had probably happened while {hero.pronoun('subject')} was rushing around."
    )
    helper.memes["blame"] += 1
    world.say(
        f"{helper.id} smiled and said it was only a small tear, not a big mistake."
    )
    world.say(
        f"They sat together and used a needle and thread to {cfg.repair_method} the {cfg.label}."
    )
    item.meters["repaired"] = 1
    item.meters["tear"] = 0
    hero.memes["relief"] += 1
    helper.memes["relief"] += 1
    hero.memes["reconciliation"] += 1
    helper.memes["reconciliation"] += 1
    world.say(
        f"When the work was done, {cfg.label} looked neat again, and the two of them felt close and calm."
    )
    world.say(
        f"{hero.id} thanked {helper.id}, and the mystery felt smaller now that it had an answer."
    )


def tell(setting: Setting, cfg: ObjectCfg, name: str, helper_name: str, trait: str) -> World:
    world = World(setting)
    hero = world.add(Entity(id=name, kind="character", type="child", meters={}, memes={"worry": 0.0}))
    helper = world.add(Entity(id=helper_name, kind="character", type=helper_name.lower(), meters={}, memes={}))
    item = world.add(Entity(
        id=cfg.id,
        kind="thing",
        type=cfg.kind,
        label=cfg.label,
        phrase=cfg.phrase,
        owner=hero.id,
        caretaker=helper.id,
        meters={"tear": 1.0, "repair": 0.0},
        memes={},
    ))
    world.facts.update(hero=hero, helper=helper, item=item, cfg=cfg, trait=trait)
    world.say(
        f"{hero.id} was a {trait} child in {setting.place}, and {hero.id} liked the calm of ordinary days."
    )
    world.say(
        f"One morning, {hero.id} saw {cfg.phrase} and noticed one little tear."
    )
    world.para()
    generate_mystery(world, hero, helper, cfg)
    world.para()
    repair_and_reconcile(world, hero, helper, cfg, item)
    return world


def prompt_lines(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a gentle slice-of-life story about a child named {f["hero"].id} noticing a tear in a {f["cfg"].label}.',
        f"Tell a small mystery-to-solve story where {f['hero'].id} and {f['helper'].id} investigate a tear and then reconcile.",
        f'Write a short story for young children that includes the word "tear" and ends with a repaired everyday item.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero, helper, cfg = f["hero"], f["helper"], f["cfg"]
    return [
        QAItem(
            question=f"What did {hero.id} notice in the {cfg.label}?",
            answer=f"{hero.id} noticed a tear in {cfg.phrase}.",
        ),
        QAItem(
            question=f"Who helped {hero.id} solve the little mystery?",
            answer=f"{helper.id} helped look carefully and find the clue.",
        ),
        QAItem(
            question=f"What happened after they fixed the {cfg.label}?",
            answer=f"The {cfg.label} looked neat again, and {hero.id} and {helper.id} felt calm together.",
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a tear?",
            answer="A tear is a split or opening in something that should be whole, like cloth or paper.",
        ),
        QAItem(
            question="What does reconcile mean?",
            answer="To reconcile means to make peace again after a misunderstanding or hurt feelings.",
        ),
        QAItem(
            question="What is a mystery to solve?",
            answer="A mystery to solve is a question with a hidden answer that people can figure out by looking closely.",
        ),
    ]


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.place], OBJECTS[params.object], params.name, params.helper, params.trait)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=prompt_lines(world),
        story_qa=story_qa(world),
        world_qa=world_qa(world),
        world=world,
    )


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        bits = []
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        lines.append(f"  {e.id:10} ({e.kind:8}) {' '.join(bits)}")
    return "\n".join(lines)


def format_qa(sample: StorySample) -> str:
    out = ["== prompts =="]
    out.extend(f"{i+1}. {p}" for i, p in enumerate(sample.prompts))
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


CURATED = [
    StoryParams(place="living_room", object="pillow", name="Mia", helper="mother", trait="curious"),
    StoryParams(place="bedroom", object="teddy", name="Leo", helper="father", trait="gentle"),
    StoryParams(place="kitchen", object="bag", name="Ava", helper="grandma", trait="careful"),
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
        print(asp_program("#show compatible/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        model = asp.one_model(asp_program("#show compatible/2."))
        print(sorted(set(asp.atoms(model, "compatible"))))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [
            generate(p)
            for p in CURATED
        ]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 25):
            rng = random.Random(base_seed + i)
            i += 1
            try:
                params = resolve_params(args, rng)
            except StoryError as err:
                print(err)
                return
            params.seed = base_seed + i
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

    for idx, sample in enumerate(samples):
        header = f"### variant {idx + 1}" if len(samples) > 1 and not args.all else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if idx < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()

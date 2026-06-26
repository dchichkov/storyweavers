#!/usr/bin/env python3
"""
A bedtime-story world about a curious child, a mysterious cartridge, and a
gentle transformation solved by measuring width instead of guessing.
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
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "mother", "grandmother", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "grandfather", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str
    cozy_detail: str
    slot_width: float
    affords: set[str] = field(default_factory=set)


@dataclass
class Mystery:
    id: str
    clue: str
    reason: str
    reveal: str


@dataclass
class Transformation:
    id: str
    verb: str
    result: str
    needed_slot: str
    before_width: float
    after_width: float
    trigger: str


@dataclass
class Conflict:
    id: str
    worry: str
    gentle_warning: str
    solved_by: str


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[str] = set()
        self.facts: dict[str, object] = {}

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


SETTINGS = {
    "attic": Setting(
        place="the attic",
        cozy_detail="moonlight slipped through a round window and made the old boxes look sleepy",
        slot_width=2.0,
        affords={"find", "measure", "transform"},
    ),
    "workroom": Setting(
        place="the workroom",
        cozy_detail="a lamp glowed softly over a table with thread, paper, and warm wood",
        slot_width=1.5,
        affords={"find", "measure", "transform"},
    ),
    "nursery": Setting(
        place="the nursery",
        cozy_detail="the room was full of blankets, a rocking chair, and the hush of bedtime",
        slot_width=1.2,
        affords={"find", "measure", "transform"},
    ),
}

MYSTERIES = {
    "cartridge": Mystery(
        id="cartridge",
        clue="a little cartridge with a star on its side",
        reason="it had no label, so no one knew what it was for",
        reveal="it belonged in the tiny slot inside the lantern",
    ),
    "width": Mystery(
        id="width",
        clue="the width of the narrow slot",
        reason="the child could not tell by looking alone",
        reveal="only a careful measure showed the cartridge would fit",
    ),
}

TRANSFORMS = {
    "widen_path": Transformation(
        id="widen_path",
        verb="turn the narrow paper path into a wider one",
        result="a broad little bridge of paper",
        needed_slot="slot",
        before_width=0.8,
        after_width=1.6,
        trigger="the cartridge clicked into the lantern",
    ),
    "open_bed": Transformation(
        id="open_bed",
        verb="transform the folded blanket into a wider nest",
        result="a soft bed that spread out like a quiet cloud",
        needed_slot="slot",
        before_width=0.9,
        after_width=1.8,
        trigger="the cartridge glowed warm and steady",
    ),
}

CONFLICTS = {
    "worry_about_breaking": Conflict(
        id="worry_about_breaking",
        worry="the grown-up was afraid the little machine might snap if the cartridge was forced in",
        gentle_warning="Let's measure first so we don't make a mistake",
        solved_by="using the right slot and the right width",
    )
}


@dataclass
class StoryParams:
    place: str
    mystery: str
    transformation: str
    conflict: str
    name: str
    gender: str
    caretaker: str
    seed: Optional[int] = None


GIRL_NAMES = ["Maya", "Lena", "Nora", "Ivy", "Ada", "Ruby"]
BOY_NAMES = ["Owen", "Theo", "Eli", "Noah", "Finn", "Miles"]
CAREGIVERS = ["mother", "father", "grandmother", "grandfather"]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Bedtime story world about width, a cartridge, and a gentle transformation.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--mystery", choices=MYSTERIES)
    ap.add_argument("--transformation", choices=TRANSFORMS)
    ap.add_argument("--conflict", choices=CONFLICTS)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--name")
    ap.add_argument("--caretaker", choices=CAREGIVERS)
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


def asp_facts() -> str:
    import asp
    lines = []
    for sid, s in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        lines.append(asp.fact("slot_width", sid, int(s.slot_width * 10)))
    for mid in MYSTERIES:
        lines.append(asp.fact("mystery", mid))
    for tid in TRANSFORMS:
        lines.append(asp.fact("transformation", tid))
    for cid in CONFLICTS:
        lines.append(asp.fact("conflict", cid))
    return "\n".join(lines)


ASP_RULES = r"""
valid_story(S, M, T, C) :- setting(S), mystery(M), transformation(T), conflict(C).
#show valid_story/4.
"""


def asp_program() -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n"


def asp_valid() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program())
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    python_set = {(s, m, t, c) for s in SETTINGS for m in MYSTERIES for t in TRANSFORMS for c in CONFLICTS}
    clingo_set = set(asp_valid())
    if python_set == clingo_set:
        print(f"OK: clingo matches Python ({len(clingo_set)} stories).")
        return 0
    print("MISMATCH")
    print("only in clingo:", sorted(clingo_set - python_set))
    print("only in python:", sorted(python_set - clingo_set))
    return 1


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    place = args.place or rng.choice(list(SETTINGS))
    mystery = args.mystery or rng.choice(list(MYSTERIES))
    transformation = args.transformation or rng.choice(list(TRANSFORMS))
    conflict = args.conflict or rng.choice(list(CONFLICTS))
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    caretaker = args.caretaker or rng.choice(CAREGIVERS)
    return StoryParams(place, mystery, transformation, conflict, name, gender, caretaker)


def _story_name(entity: Entity) -> str:
    return entity.id


def generate(params: StoryParams) -> StorySample:
    setting = SETTINGS[params.place]
    mystery = MYSTERIES[params.mystery]
    transform = TRANSFORMS[params.transformation]
    conflict = CONFLICTS[params.conflict]
    world = World(setting)

    child = world.add(Entity(id=params.name, kind="character", type=params.gender))
    grown = world.add(Entity(id="grownup", kind="character", type=params.caretaker))
    cartridge = world.add(Entity(id="cartridge", label="cartridge", phrase="a little cartridge", owner=child.id))
    lantern = world.add(Entity(id="lantern", label="lantern", phrase="a sleepy brass lantern"))
    shelf = world.add(Entity(id="shelf", label="slot", phrase="a narrow slot in the lantern"))
    bridge = world.add(Entity(id="bridge", label="paper bridge", phrase="a folded paper bridge"))

    cartridge.meters["width"] = 0.6
    shelf.meters["width"] = setting.slot_width
    bridge.meters["width"] = transform.before_width
    child.memes["curiosity"] = 1.0
    grown.memes["worry"] = 1.0

    world.say(
        f"At {setting.place}, {child.id} was sleepy and curious, and {setting.cozy_detail}."
    )
    world.say(
        f"One night, {child.id} found {mystery.clue}. {mystery.reason}."
    )
    world.say(
        f"{child.id} held it close and wondered how the little cartridge could possibly belong to the lantern."
    )

    world.para()
    world.say(
        f"{grown.id} noticed the tiny piece and frowned a little, because {conflict.worry}."
    )
    world.say(f'"{conflict.gentle_warning}," {grown.id} said.')
    world.say(f"{child.id} nodded, and the mystery became a question about width instead of a guess.")

    world.para()
    child.memes["conflict"] = 1.0
    world.say(
        f"So they measured the slot in the lantern. The width was just right, and the cartridge was not too wide at all."
    )
    world.say(
        f"When {child.id} slipped the cartridge inside, {transform.trigger}."
    )
    bridge.meters["width"] = transform.after_width
    child.memes["joy"] = 1.0
    child.memes["conflict"] = 0.0
    grown.memes["worry"] = 0.0

    world.para()
    world.say(
        f"Then the lantern made a warm little hum and {transform.verb}. Soon there was {transform.result}, soft and safe."
    )
    world.say(
        f"{child.id} smiled, because the mystery was solved and the conflict had turned into a calm bedtime success."
    )
    world.say(
        f"Before sleep, the cartridge rested in the lantern, the width fit perfectly, and the room felt wider in the heart."
    )

    world.facts.update(
        child=child,
        grown=grown,
        cartridge=cartridge,
        lantern=lantern,
        shelf=shelf,
        bridge=bridge,
        mystery=mystery,
        transformation=transform,
        conflict=conflict,
        setting=setting,
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
    child = f["child"]
    return [
        f'Write a bedtime story for a small child about a mysterious cartridge and the width of a tiny slot.',
        f"Tell a gentle story where {child.id} solves a mystery by measuring width instead of forcing the cartridge.",
        f'Write a cozy story with conflict, a careful measurement, and a soft transformation that begins with the word "cartridge".',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child: Entity = f["child"]  # type: ignore[assignment]
    grown: Entity = f["grown"]  # type: ignore[assignment]
    mystery: Mystery = f["mystery"]  # type: ignore[assignment]
    transform: Transformation = f["transformation"]  # type: ignore[assignment]
    setting: Setting = f["setting"]  # type: ignore[assignment]
    cartridge: Entity = f["cartridge"]  # type: ignore[assignment]
    bridge: Entity = f["bridge"]  # type: ignore[assignment]

    return [
        QAItem(
            question=f"What did {child.id} find in {setting.place}?",
            answer=f"{child.id} found {mystery.clue}. It was a small cartridge, and nobody knew at first what it was for.",
        ),
        QAItem(
            question=f"Why was {grown.id} worried about the cartridge?",
            answer=f"{grown.id} was worried because {CONFLICTS['worry_about_breaking'].worry}. Measuring the width first was the gentle answer.",
        ),
        QAItem(
            question=f"What did the measuring show about the width of the slot?",
            answer=f"It showed that the width was a perfect fit, so the cartridge could go into the lantern safely.",
        ),
        QAItem(
            question=f"What changed after the cartridge went inside?",
            answer=f"After the cartridge went inside, {transform.trigger}, and the story became {transform.result}.",
        ),
        QAItem(
            question=f"How did the story end for {child.id} and the cartridge?",
            answer=f"The story ended peacefully with {child.id} smiling, the cartridge resting in the lantern, and the {bridge.label} made wide and safe.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a cartridge?",
            answer="A cartridge is a small container or piece that fits into a machine or toy so it can do a special job.",
        ),
        QAItem(
            question="What does width mean?",
            answer="Width means how wide something is from side to side.",
        ),
        QAItem(
            question="Why is measuring helpful before using a small piece?",
            answer="Measuring helps you learn whether a piece will fit, so you can avoid forcing it and breaking something.",
        ),
    ]


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        lines.append(f"  {e.id:10} ({e.type:9}) {' '.join(bits)}")
    return "\n".join(lines)


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    for p in sample.prompts:
        lines.append(p)
    lines.append("")
    lines.append("== story qa ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== world qa ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
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


CURATED = [
    StoryParams("attic", "cartridge", "widen_path", "worry_about_breaking", "Maya", "girl", "grandmother"),
    StoryParams("workroom", "width", "open_bed", "worry_about_breaking", "Theo", "boy", "father"),
    StoryParams("nursery", "cartridge", "open_bed", "worry_about_breaking", "Ivy", "girl", "mother"),
]


def resolve_story_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    return resolve_params(args, rng)


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program())
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        model = asp.one_model(asp_program())
        print(f"{len(asp.atoms(model, 'valid_story'))} compatible stories")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 20, 20):
            params = resolve_story_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            sample = generate(params)
            i += 1
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

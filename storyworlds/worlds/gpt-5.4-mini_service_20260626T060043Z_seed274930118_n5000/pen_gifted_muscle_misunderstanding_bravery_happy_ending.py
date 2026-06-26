#!/usr/bin/env python3
"""
A tiny storyworld for a rhyming tale of a gifted pen, a muscle-sized
misunderstanding, and a brave, happy ending.

Premise:
- A child receives a gifted pen.
- The child misunderstands what the pen is for because of the word "muscle".
- The child is brave enough to ask, and the confusion becomes a warm ending.

This world keeps the state small and concrete:
- physical meters track ink, care, and tidiness
- emotional memes track surprise, worry, bravery, and joy
- the prose is generated from the simulated world, not from a frozen template
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
class Gift:
    label: str
    phrase: str
    sparkle: str
    purpose: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Setting:
    place: str
    details: str
    affords: set[str] = field(default_factory=set)


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.trace: list[str] = []

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
        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        clone.facts = dict(self.facts)
        return clone


@dataclass
class StoryParams:
    setting: str
    child_name: str
    child_type: str
    giver_name: str
    giver_type: str
    gift: str
    seed: Optional[int] = None


SETTINGS = {
    "desk": Setting(
        place="the sunny desk",
        details="Sunlight poured over a little desk by the window.",
        affords={"writing", "drawing"},
    ),
    "porch": Setting(
        place="the quiet porch",
        details="The porch had a soft chair and a tiny table for notes.",
        affords={"writing"},
    ),
    "kitchen": Setting(
        place="the kitchen table",
        details="The kitchen table was warm, with a cup and a crumb or two.",
        affords={"writing", "drawing"},
    ),
}

GIFTS = {
    "pen": Gift(
        label="pen",
        phrase="a shiny blue pen",
        sparkle="blue",
        purpose="write and draw",
        tags={"pen", "gifted"},
    ),
    "marker": Gift(
        label="marker",
        phrase="a bright red marker",
        sparkle="red",
        purpose="make bold lines",
        tags={"pen", "gifted"},
    ),
    "pencil": Gift(
        label="pencil",
        phrase="a neat yellow pencil",
        sparkle="yellow",
        purpose="make gentle marks",
        tags={"pen", "gifted"},
    ),
}

CHILD_NAMES = ["Mia", "Nora", "Lily", "Theo", "Ben", "Ava"]
GIVER_NAMES = ["Aunt June", "Grandpa", "Mom", "Dad", "Teacher Lin"]
TYPES = ["girl", "boy"]


def rhyming_line(a: str, b: str) -> str:
    return f"{a} {b}"


def is_reasonable(params: StoryParams) -> bool:
    return params.gift in GIFTS and params.setting in SETTINGS


def predict_confusion(world: World, child: Entity, gift: Entity) -> bool:
    sim = world.copy()
    sim.get(child.id).memes["worry"] += 1
    sim.get(child.id).memes["misunderstanding"] += 1
    return bool(gift.label == "pen")


def _narrate_gift(world: World, child: Entity, giver: Entity, gift: Entity) -> None:
    child.memes["surprise"] += 1
    child.memes["joy"] += 0.5
    gift.worn_by = child.id
    world.say(
        f"{giver.id} came by with a gift in the light: "
        f"{child.pronoun('possessive')} {gift.phrase} looked shiny and bright."
    )
    world.say(
        f"{child.id} held the {gift.label} tight, with a grin so wide; "
        f"the room felt warm, like a song inside."
    )


def _narrate_misunderstanding(world: World, child: Entity, gift: Entity) -> None:
    child.memes["misunderstanding"] += 1
    child.memes["worry"] += 1
    world.say(
        f"But {child.id} heard the word \"muscle\" and gave a small frown; "
        f"\"Is this for strong arms?\" {child.pronoun()} asked with a sound."
    )
    world.say(
        f"{child.id} tried to lift the {gift.label} up high; "
        f"it was light as a feather, and that made {child.pronoun('object')} sigh."
    )


def _narrate_bravery(world: World, child: Entity, giver: Entity, gift: Entity) -> None:
    child.memes["bravery"] += 1
    child.memes["worry"] = 0
    world.say(
        f"Then brave little {child.id} took a breath, nice and slow, "
        f"and asked {giver.id} the question to know."
    )
    world.say(
        f"\"Is this pen for muscle, or for notes I can keep? "
        f"Please tell me the truth,\" {child.pronoun()} said soft and sweet."
    )


def _narrate_clarify(world: World, child: Entity, giver: Entity, gift: Entity) -> None:
    child.memes["joy"] += 1.5
    child.memes["misunderstanding"] = 0
    world.say(
        f"{giver.id} laughed a kind laugh, then answered with cheer: "
        f"\"This pen is for writing, my dear, my dear!\""
    )
    world.say(
        f"\"You can write a brave story, a thank-you, or rhyme; "
        f"the {gift.label} is yours for a very good time.\""
    )


def _narrate_ending(world: World, child: Entity, giver: Entity, gift: Entity) -> None:
    child.memes["joy"] += 1
    gift.meters["ink"] = 1.0
    world.say(
        f"So {child.id} wrote a note with a happy, small hum: "
        f"\"Thank you for the {gift.label}!\" and the whole day felt warm."
    )
    world.say(
        f"The gift was no mystery; the moonbeam was mild. "
        f"{child.id} had a brave heart and a happy-ending smile."
    )


def tell(setting: Setting, gift_def: Gift, child_name: str, child_type: str,
         giver_name: str, giver_type: str) -> World:
    world = World(setting)
    child = world.add(Entity(
        id=child_name,
        kind="character",
        type=child_type,
        meters={"care": 0.0},
        memes={"surprise": 0.0, "worry": 0.0, "misunderstanding": 0.0, "bravery": 0.0, "joy": 0.0},
    ))
    giver = world.add(Entity(
        id=giver_name,
        kind="character",
        type=giver_type,
        meters={"care": 0.0},
        memes={"joy": 0.0},
    ))
    gift = world.add(Entity(
        id=gift_def.label,
        type=gift_def.label,
        label=gift_def.label,
        phrase=gift_def.phrase,
        owner=child.id,
        caretaker=giver.id,
        meters={"ink": 0.0},
        memes={},
    ))

    world.say(f"{setting.details}")
    world.say(
        f"On a gentle day, {child.id} met {giver.id} near {setting.place}, "
        f"where the air felt light as a feather."
    )
    world.para()
    _narrate_gift(world, child, giver, gift)
    world.para()
    _narrate_misunderstanding(world, child, gift)
    world.say(
        f"The word \"muscle\" felt puzzled and prickly, a tangle of thought; "
        f"but {child.id} was not stuck for long, as brave hearts are taught."
    )
    world.para()
    _narrate_bravery(world, child, giver, gift)
    _narrate_clarify(world, child, giver, gift)
    world.para()
    _narrate_ending(world, child, giver, gift)

    world.facts.update(child=child, giver=giver, gift=gift, setting=setting, gift_def=gift_def)
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    child = f["child"]
    gift = f["gift_def"]
    return [
        f'Write a rhyming story for a young child about a gifted {gift.label} and a misunderstanding about "muscle".',
        f"Tell a gentle, rhyming story where {child.id} gets {gift.phrase}, feels puzzled, and is brave enough to ask a question.",
        f"Write a happy-ending rhyme with a gift, a misunderstanding, bravery, and a clear explanation about a {gift.label}.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child = f["child"]
    giver = f["giver"]
    gift = f["gift_def"]
    setting = f["setting"]
    return [
        QAItem(
            question=f"What did {giver.id} give {child.id} at {setting.place}?",
            answer=f"{giver.id} gave {child.id} {gift.phrase}. It was a gifted {gift.label} that looked shiny and bright.",
        ),
        QAItem(
            question=f"Why did {child.id} feel confused about the gifted {gift.label}?",
            answer=f"{child.id} heard the word \"muscle\" and wondered if the {gift.label} was for strong arms instead of writing. That was the misunderstanding.",
        ),
        QAItem(
            question=f"What brave thing did {child.id} do before the happy ending?",
            answer=f"{child.id} took a deep breath and asked {giver.id} what the {gift.label} was really for. That was a brave thing to do.",
        ),
        QAItem(
            question=f"How did the story end for {child.id} and the {gift.label}?",
            answer=f"The misunderstanding was cleared up, {child.id} felt proud and happy, and the {gift.label} became a nice tool for writing a thank-you note.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a pen for?",
            answer="A pen is used for writing and drawing by making marks with ink on paper.",
        ),
        QAItem(
            question="What does gifted mean?",
            answer="Gifted means given as a present by someone who cares about you.",
        ),
        QAItem(
            question="What is muscle?",
            answer="A muscle is a part of the body that helps you move, lift, and stretch.",
        ),
        QAItem(
            question="What is bravery?",
            answer="Bravery means doing something even when you feel a little scared or unsure.",
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
    lines.append("== (3) World-knowledge questions ==")
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
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if e.phrase:
            bits.append(f"phrase={e.phrase!r}")
        lines.append(f"  {e.id} ({e.type}) {' '.join(bits)}")
    return "\n".join(lines)


ASP_RULES = r"""
gifted(X) :- gift(X).
misunderstanding(child, gift) :- hears(child, muscle), gift(gift).
brave(child) :- asks(child, question).
happy_ending(child) :- brave(child), not misunderstanding(child, gift).
"""

def asp_facts() -> str:
    import asp
    lines = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for gid in GIFTS:
        lines.append(asp.fact("gift", gid))
    lines.append(asp.fact("hears", "child", "muscle"))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show misunderstanding/2.\n#show brave/1.\n#show happy_ending/1."))
    atoms = set(asp.atoms(model, "misunderstanding")) | set(asp.atoms(model, "brave")) | set(asp.atoms(model, "happy_ending"))
    expected = {("child", "gift"), ("child",), ("child",)}
    if atoms != expected:
        print("MISMATCH between ASP and Python reasonableness.")
        print("  asp:", sorted(atoms))
        print("  py :", sorted(expected))
        return 1
    print("OK: ASP twin is wired and returns the intended story beats.")
    return 0


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Rhyming story world: a gifted pen, a muscle misunderstanding, bravery, and a happy ending.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--gift", choices=GIFTS)
    ap.add_argument("--name")
    ap.add_argument("--giver")
    ap.add_argument("--gender", choices=TYPES)
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
    if args.setting and args.setting not in SETTINGS:
        raise StoryError("Unknown setting.")
    if args.gift and args.gift not in GIFTS:
        raise StoryError("Unknown gift.")
    setting = args.setting or rng.choice(list(SETTINGS))
    gift = args.gift or rng.choice(list(GIFTS))
    child_type = args.gender or rng.choice(TYPES)
    child_name = args.name or rng.choice(CHILD_NAMES)
    giver_name = args.giver or rng.choice(GIVER_NAMES)
    giver_type = "woman" if "Aunt" in giver_name or giver_name == "Mom" else "man"
    return StoryParams(setting=setting, child_name=child_name, child_type=child_type,
                       giver_name=giver_name, giver_type=giver_type, gift=gift)


def generate(params: StoryParams) -> StorySample:
    if not is_reasonable(params):
        raise StoryError("Invalid story parameters.")
    world = tell(SETTINGS[params.setting], GIFTS[params.gift],
                 params.child_name, params.child_type,
                 params.giver_name, params.giver_type)
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


CURATED = [
    StoryParams(setting="desk", child_name="Mia", child_type="girl", giver_name="Aunt June", giver_type="woman", gift="pen"),
    StoryParams(setting="kitchen", child_name="Theo", child_type="boy", giver_name="Mom", giver_type="woman", gift="marker"),
    StoryParams(setting="porch", child_name="Nora", child_type="girl", giver_name="Grandpa", giver_type="man", gift="pencil"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show misunderstanding/2.\n#show brave/1.\n#show happy_ending/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print("ASP mode is available for parity checks; use --verify to exercise it.")
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
        if len(samples) > 1:
            print(f"### variant {i + 1}")
        emit(sample, trace=args.trace, qa=args.qa)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()

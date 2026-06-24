#!/usr/bin/env python3
"""
storyworlds/worlds/sectioned_hug_calzone_flower_field_lesson_learned.py
======================================================================

A small standalone storyworld about an adventure in a flower field:
a child, a calzone, a lesson learned, and a warm hug at the end.

The premise:
- A child loves to explore a flower field.
- They bring a calzone on the trip.
- The field is beautiful but a little tricky: tall flowers can hide the path,
  and carrying one big calzone makes sharing hard.

The turn:
- The child tries to hurry through the flowers with the calzone.
- A helper notices the problem and suggests sectioning the calzone so it can be
  shared safely and neatly.
- The child learns that slower, smaller steps make the adventure better.

The resolution:
- The calzone is sectioned into easy slices.
- Everyone shares it in the flower field.
- A hug seals the lesson learned.

This file follows the Storyweavers contract:
- standalone stdlib script
- StoryParams, registries, build_parser, resolve_params, generate, emit, main
- eager import from storyworlds/results.py
- lazy import of storyworlds/asp.py in ASP helpers
- inline ASP_RULES twin, asp_facts(), --verify support
"""

from __future__ import annotations

import argparse
import copy
import json
import os
import random
import sys
from collections import defaultdict
from dataclasses import dataclass, field, asdict
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
    role: str = ""
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    pieces: int = 1
    shareable: bool = False
    edible: bool = False
    carries: set[str] = field(default_factory=set)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "mother", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return self.label or self.type


@dataclass
class Setting:
    place: str = "the flower field"
    affords: set[str] = field(default_factory=set)


@dataclass
class Snack:
    id: str
    label: str
    phrase: str
    pieces: int
    shareable: bool = True
    edible: bool = True


@dataclass
class Gear:
    id: str
    label: str
    phrase: str
    helps: set[str] = field(default_factory=set)
    protects: set[str] = field(default_factory=set)


@dataclass
class World:
    setting: Setting
    entities: dict[str, Entity] = field(default_factory=dict)
    fired: set[tuple] = field(default_factory=set)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    facts: dict = field(default_factory=dict)

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str) -> Entity:
        return self.entities[eid]

    def characters(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.kind == "character"]

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


def _r_hungry(world: World) -> list[str]:
    out: list[str] = []
    for e in world.characters():
        if e.memes["hunger"] >= THRESHOLD and ("want_food", e.id) not in world.fired:
            world.fired.add(("want_food", e.id))
            out.append(f"{e.id} started thinking about lunch.")
    return out


def _r_section(world: World) -> list[str]:
    out: list[str] = []
    snack = world.entities.get("snack")
    cutter = world.entities.get("helper")
    child = world.entities.get("child")
    if not snack or not cutter or not child:
        return out
    if child.memes["sharing"] < THRESHOLD:
        return out
    if snack.pieces > 1:
        sig = ("section", snack.id)
        if sig in world.fired:
            return out
        world.fired.add(sig)
        snack.pieces = max(snack.pieces, 4)
        out.append("The calzone was sectioned into easy pieces.")
    return out


def _r_hug(world: World) -> list[str]:
    out: list[str] = []
    child = world.entities.get("child")
    helper = world.entities.get("helper")
    if not child or not helper:
        return out
    if child.memes["relief"] < THRESHOLD or helper.memes["kindness"] < THRESHOLD:
        return out
    sig = ("hug",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    child.memes["love"] += 1
    helper.memes["love"] += 1
    out.append("__hug__")
    return out


CAUSAL_RULES = [
    _r_hungry,
    _r_section,
    _r_hug,
]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            sents = rule(world)
            if sents:
                changed = True
                produced.extend(s for s in sents if s != "__hug__")
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def can_share(snack: Snack) -> bool:
    return snack.shareable and snack.pieces >= 1


def sectioned_amount(snack: Snack) -> int:
    return 4 if snack.pieces == 1 else snack.pieces


@dataclass
class StoryParams:
    name: str
    helper: str
    name_type: str
    helper_type: str
    snack: str
    gear: str
    seed: Optional[int] = None


SETTINGS = {
    "flower_field": Setting(place="the flower field", affords={"explore", "share"}),
}

SNACKS = {
    "calzone": Snack(
        id="calzone",
        label="calzone",
        phrase="a warm calzone",
        pieces=1,
    ),
}

GEAR = {
    "basket": Gear(
        id="basket",
        label="picnic basket",
        phrase="a small picnic basket",
        helps={"carry"},
        protects={"crush"},
    ),
    "blanket": Gear(
        id="blanket",
        label="picnic blanket",
        phrase="a bright picnic blanket",
        helps={"sit"},
        protects={"dirt"},
    ),
}

GIRL_NAMES = ["Lily", "Maya", "Nora", "Zoe", "Ella", "Ava"]
BOY_NAMES = ["Leo", "Finn", "Theo", "Max", "Sam", "Noah"]


def valid_combos() -> list[tuple[str, str, str]]:
    return [("flower_field", "calzone", gear) for gear in GEAR]


def explain_rejection(snack: Snack, gear: Gear) -> str:
    return (
        f"(No story: {snack.label} in the flower field needs a simple sharing tool, "
        f"and {gear.label} does not fit the scene well.)"
    )


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A flower-field adventure with a calzone and a lesson learned.")
    ap.add_argument("--name")
    ap.add_argument("--helper")
    ap.add_argument("--snack", choices=SNACKS)
    ap.add_argument("--gear", choices=GEAR)
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


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.snack and args.gear and (args.snack != "calzone" or args.gear not in GEAR):
        raise StoryError(explain_rejection(SNACKS["calzone"], GEAR.get(args.gear, next(iter(GEAR.values())))))
    name = args.name or rng.choice(GIRL_NAMES + BOY_NAMES)
    helper = args.helper or rng.choice([n for n in GIRL_NAMES + BOY_NAMES if n != name])
    return StoryParams(
        name=name,
        helper=helper,
        name_type="girl" if name in GIRL_NAMES else "boy",
        helper_type="girl" if helper in GIRL_NAMES else "boy",
        snack=args.snack or "calzone",
        gear=args.gear or rng.choice(list(GEAR)),
    )


def tell(params: StoryParams) -> World:
    world = World(SETTINGS["flower_field"])
    child = world.add(Entity(id="child", kind="character", type=params.name_type, label=params.name))
    helper = world.add(Entity(id="helper", kind="character", type=params.helper_type, label=params.helper))
    snack = world.add(Entity(id="snack", type="food", label="calzone", phrase="a warm calzone", pieces=1, shareable=True, edible=True))
    gear = world.add(Entity(id="gear", type="thing", label=GEAR[params.gear].label, phrase=GEAR[params.gear].phrase))
    world.facts["gear"] = gear
    child.memes["hunger"] += 1
    child.memes["curiosity"] += 1
    helper.memes["kindness"] += 1
    world.say(f"{child.label_word} and {helper.label_word} set out into the flower field on a bright adventure.")
    world.say(f"They carried {snack.phrase} and {gear.phrase}, hoping for a picnic after the path through the flowers.")
    world.para()
    world.say(f"The flowers were tall and swayed like banners, so {child.label_word} hurried ahead.")
    child.memes["sharing"] += 1
    world.say(f"But the big calzone felt clumsy, and {helper.label_word} stopped to suggest a better plan.")
    snack.pieces = sectioned_amount(SNACKS["calzone"])
    propagate(world, narrate=True)
    world.para()
    child.memes["relief"] += 1
    helper.memes["relief"] += 1
    world.say(f"{helper.label_word} helped section the calzone, and now everyone could hold a piece without worry.")
    world.say(f"They ate in the middle of the flower field, smiling at bees and butterflies drifting past.")
    world.say(f"Then {child.label_word} gave {helper.label_word} a big hug and said, 'I learned that little steps make a big adventure better.'")
    world.say("The flowers nodded around them, and the path home felt easy and bright.")
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    child = world.get("child")
    helper = world.get("helper")
    return [
        'Write a short Adventure-style story for a young child in a flower field that includes the word "sectioned" and a calzone.',
        f"Tell a gentle adventure about {child.label_word} and {helper.label_word} sharing a calzone in the flower field and learning a lesson.",
        'Write a story that ends with a hug and a lesson learned after a calzone is sectioned in a flower field.',
    ]


def story_qa(world: World) -> list[QAItem]:
    child = world.get("child")
    helper = world.get("helper")
    snack = world.get("snack")
    return [
        QAItem(
            question=f"Who went into the flower field together?",
            answer=f"{child.label_word} and {helper.label_word} went into the flower field together for a little adventure."
        ),
        QAItem(
            question="What did they bring for their picnic?",
            answer=f"They brought a calzone, and it was sectioned so they could share it more easily."
        ),
        QAItem(
            question="What lesson did the child learn at the end?",
            answer=f"{child.label_word} learned that smaller steps and sharing can make an adventure better."
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a calzone?",
            answer="A calzone is a folded Italian bread pocket filled with tasty ingredients like cheese or sauce."
        ),
        QAItem(
            question="What does sectioned mean?",
            answer="Sectioned means divided into pieces or parts so it is easier to share or handle."
        ),
        QAItem(
            question="What is a flower field?",
            answer="A flower field is a wide place full of growing flowers, stems, and bright colors."
        ),
    ]


def format_qa(sample: StorySample) -> str:
    parts = ["== (1) Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        parts.append(f"{i}. {p}")
    parts.append("")
    parts.append("== (2) Story questions ==")
    for item in sample.story_qa:
        parts.append(f"Q: {item.question}")
        parts.append(f"A: {item.answer}")
    parts.append("")
    parts.append("== (3) World-knowledge questions ==")
    for item in sample.world_qa:
        parts.append(f"Q: {item.question}")
        parts.append(f"A: {item.answer}")
    return "\n".join(parts)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if e.pieces != 1:
            bits.append(f"pieces={e.pieces}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(n for n, *_ in world.fired)}")
    return "\n".join(lines)


ASP_RULES = r"""
sectioned(snack) :- snack(snack), pieces(snack,N), N > 1.
lesson_learned(child) :- child(child), sharing(child), relieved(child).
hug(child, helper) :- child(child), helper(helper), lesson_learned(child).
"""


def asp_facts() -> str:
    import asp
    lines = [asp.fact("setting", "flower_field"), asp.fact("snack", "calzone"), asp.fact("child", "child"), asp.fact("helper", "helper")]
    for gear in GEAR:
        lines.append(asp.fact("gear", gear.id))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show sectioned/1.\n#show hug/2.\n"))
    atoms = set(asp.atoms(model, "sectioned"))
    if atoms:
        print("OK: ASP rules produce sectioned calzone facts.")
        return 0
    print("MISMATCH: ASP rules did not produce expected facts.")
    return 1


def generate(params: StoryParams) -> StorySample:
    world = tell(params)
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
    StoryParams(name="Lily", helper="Milo", name_type="girl", helper_type="boy", snack="calzone", gear="basket"),
    StoryParams(name="Theo", helper="Ava", name_type="boy", helper_type="girl", snack="calzone", gear="blanket"),
]


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show sectioned/1.\n#show hug/2.\n#show lesson_learned/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(asp_program("#show sectioned/1.\n#show hug/2.\n#show lesson_learned/1."))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        for i in range(args.n):
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            samples.append(generate(params))

    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        emit(sample, trace=args.trace, qa=args.qa, header=f"### variant {i + 1}" if len(samples) > 1 else "")
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()

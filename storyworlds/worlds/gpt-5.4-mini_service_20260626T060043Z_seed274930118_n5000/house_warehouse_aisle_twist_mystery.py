#!/usr/bin/env python3
"""
storyworlds/worlds/house_warehouse_aisle_twist_mystery.py
==========================================================

A small mystery storyworld set in a warehouse aisle, built around a twist
reveal. The seed word "house" is carried through the world as a tiny house kit
that seems to vanish, only to be found by following clues in the aisle.

The world is child-facing and state-driven:
- a child and helper search a warehouse aisle,
- clues raise suspicion and worry,
- the twist reveals the missing house was moved for a gentle reason,
- the ending proves what changed in the world model.

The inline ASP twin mirrors the Python reasonableness gate.
"""

from __future__ import annotations

import argparse
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
    kind: str = "thing"            # character | thing
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    moved_to: str = ""
    plural: bool = False
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    tags: set[str] = field(default_factory=set)

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
class Setting:
    place: str = "the warehouse aisle"
    affords: set[str] = field(default_factory=set)


@dataclass
class Clue:
    label: str
    detail: str
    turn: str


@dataclass
class Twist:
    label: str
    reveal: str
    reason: str


@dataclass
class StoryParams:
    name: str
    gender: str
    parent: str
    trait: str
    seed: Optional[int] = None


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
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


SETTING = Setting(place="the warehouse aisle", affords={"search"})
CLUE = Clue(
    label="tiny blue thread",
    detail="a tiny blue thread on the floor",
    turn="follow the thread between the boxes",
)
TWIST = Twist(
    label="delivery cart",
    reveal="the missing house had been moved onto a delivery cart for safekeeping",
    reason="the front shelf was being cleaned and the house box was too small to leave there",
)

GIRL_NAMES = ["Mina", "Lily", "Aya", "Nora", "Zoe"]
BOY_NAMES = ["Leo", "Ben", "Milo", "Theo", "Finn"]
TRAITS = ["curious", "careful", "brave", "gentle", "sharp-eyed"]


class Rule:
    def __init__(self, name: str, apply):
        self.name = name
        self.apply = apply


def _r_worry(world: World) -> list[str]:
    out: list[str] = []
    child = next((e for e in world.entities.values() if e.kind == "character"), None)
    house = world.entities.get("house")
    if not child or not house:
        return out
    if child.memes["mystery"] < THRESHOLD or house.meters["missing"] < THRESHOLD:
        return out
    sig = ("worry", child.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    child.memes["worry"] += 1
    out.append(f"{child.id} felt a little worry in the middle of the aisle.")
    return out


def _r_twist(world: World) -> list[str]:
    out: list[str] = []
    house = world.entities.get("house")
    cart = world.entities.get("cart")
    if not house or not cart:
        return out
    if house.meters["found"] < THRESHOLD or cart.meters["revealed"] < THRESHOLD:
        return out
    sig = ("twist", house.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    house.meters["missing"] = 0
    out.append("The mystery turned gentle instead of bad.")
    return out


RULES = [Rule("worry", _r_worry), Rule("twist", _r_twist)]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in RULES:
            lines = rule.apply(world)
            if lines:
                changed = True
                produced.extend(lines)
    if narrate:
        for line in produced:
            world.say(line)
    return produced


def search(world: World, child: Entity, helper: Entity, house: Entity) -> None:
    child.memes["mystery"] += 1
    house.meters["missing"] = 1
    world.say(
        f"{child.id} and {helper.pronoun('possessive')} {helper.type} were in {world.setting.place} when they noticed the little house was gone from the shelf."
    )
    world.say(
        f"{child.id} looked at the empty spot and whispered, 'Where did the house go?'"
    )
    propagate(world)


def clue_step(world: World, child: Entity, helper: Entity, house: Entity) -> None:
    child.memes["searching"] += 1
    world.say(
        f"Then {child.id} spotted {CLUE.detail}. That clue made the aisle feel like a puzzle."
    )
    world.say(
        f"They decided to {CLUE.turn}."
    )


def reveal_twist(world: World, helper: Entity, cart: Entity, house: Entity) -> None:
    cart.meters["revealed"] = 1
    house.meters["found"] = 1
    house.moved_to = cart.id
    world.say(
        f"At the end of the aisle, they found the house sitting on a cart."
    )
    world.say(
        f"{TWIST.reveal}, {TWIST.reason}."
    )
    propagate(world)


def ending(world: World, child: Entity, helper: Entity, house: Entity) -> None:
    child.memes["worry"] = 0
    child.memes["joy"] += 1
    world.say(
        f"{child.id} smiled when {helper.pronoun('subject')} tucked the little house back into a safe box and rolled the cart toward the clean shelf."
    )
    world.say(
        f"By the end, the warehouse aisle was quiet again, and the house was no longer missing."
    )


def tell(params: StoryParams) -> World:
    world = World(SETTING)
    child = world.add(
        Entity(id=params.name, kind="character", type=params.gender, tags={params.trait})
    )
    helper = world.add(
        Entity(id="helper", kind="character", type=params.parent, type_alias := "helper")
    )
    house = world.add(
        Entity(
            id="house",
            kind="thing",
            type="house",
            label="little house",
            phrase="a little house kit",
            caretaker=helper.id,
            tags={"house", "seed"},
        )
    )
    cart = world.add(
        Entity(id="cart", kind="thing", type="cart", label="delivery cart", tags={"cart"})
    )

    world.say(
        f"{child.id} was a {params.trait} child who loved noticing small details."
    )
    world.say(
        f"On that day, {child.id} and {helper.pronoun('possessive')} helper were looking for {house.phrase}."
    )
    world.para()
    search(world, child, helper, house)
    clue_step(world, child, helper, house)
    world.para()
    reveal_twist(world, helper, cart, house)
    ending(world, child, helper, house)

    world.facts.update(child=child, helper=helper, house=house, cart=cart)
    return world


SETTINGS = {"warehouse": SETTING}


def valid_combos() -> list[tuple[str, str]]:
    return [("warehouse", "house")]


def explain_rejection() -> str:
    return "(No story: this world only tells a mystery set in the warehouse aisle with the house as the missing object.)"


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    child, helper = f["child"], f["helper"]
    return [
        'Write a short mystery story set in a warehouse aisle that includes the word "house".',
        f"Tell a child-friendly twist mystery where {child.id} notices a missing house in the warehouse aisle and {helper.pronoun('possessive')} helper helps solve it.",
        "Write a gentle puzzle story that starts with a missing house and ends with a surprising but safe twist.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child, helper, house = f["child"], f["helper"], f["house"]
    return [
        QAItem(
            question=f"Where did {child.id} and the helper look for the missing house?",
            answer=f"They looked in the warehouse aisle, where the little house had been on a shelf.",
        ),
        QAItem(
            question=f"What clue helped {child.id} keep searching?",
            answer=f"The clue was {CLUE.detail}, which made them follow the aisle more carefully.",
        ),
        QAItem(
            question=f"What was the twist in the mystery?",
            answer=f"The twist was that {TWIST.reveal}, so the house was not lost for bad reasons.",
        ),
        QAItem(
            question=f"How did the story end for the house?",
            answer=f"The house was put back into a safe box and rolled to a clean shelf, so it was no longer missing.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a warehouse aisle?",
            answer="A warehouse aisle is a long path between shelves where workers and shoppers can move boxes and supplies.",
        ),
        QAItem(
            question="What does a clue do in a mystery?",
            answer="A clue gives a small piece of useful information that helps someone solve the puzzle.",
        ),
        QAItem(
            question="What is a twist in a story?",
            answer="A twist is a surprise turn that changes what you thought was happening.",
        ),
    ]


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
    lines.append("== (3) World knowledge ==")
    for q in sample.world_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    return "\n".join(lines)


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
        if e.moved_to:
            bits.append(f"moved_to={e.moved_to}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    return "\n".join(lines)


ASP_RULES = r"""
missing_house(H) :- house(H), missing(H).
found_house(H) :- house(H), found(H).
twist(H) :- found_house(H), moved_to(H, cart).
valid_story(warehouse, house) :- setting(warehouse), house_word(house).
"""


def asp_facts() -> str:
    import asp
    lines = [
        asp.fact("setting", "warehouse"),
        asp.fact("house_word", "house"),
        asp.fact("place", "warehouse_aisle"),
    ]
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/2."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    clingo_set, python_set = set(asp_valid_combos()), set(valid_combos())
    if clingo_set == python_set:
        print(f"OK: clingo gate matches valid_combos() ({len(clingo_set)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    if clingo_set - python_set:
        print("  only in clingo:", sorted(clingo_set - python_set))
    if python_set - clingo_set:
        print("  only in python:", sorted(python_set - clingo_set))
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="A small mystery storyworld set in a warehouse aisle with a twist."
    )
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--parent", choices=["mother", "father"])
    ap.add_argument("--trait", choices=TRAITS)
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
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    parent = args.parent or rng.choice(["mother", "father"])
    trait = args.trait or rng.choice(TRAITS)
    return StoryParams(name=name, gender=gender, parent=parent, trait=trait)


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
    StoryParams(name="Mina", gender="girl", parent="mother", trait="curious"),
    StoryParams(name="Leo", gender="boy", parent="father", trait="sharp-eyed"),
    StoryParams(name="Nora", gender="girl", parent="mother", trait="careful"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid_story/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible story combos:\n")
        for combo in combos:
            print("  ", combo)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 20, 20):
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            i += 1
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

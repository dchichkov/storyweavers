#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260626T055019Z_seed926384711_n100/marinade_market_moral_value_magic_foreshadowing_bedtime.py
====================================================================================================

A small bedtime-story world about a market, a little jar of marinade, a touch
of magic, and a gentle moral turn.

Premise:
- A child wants to carry home a special marinade from the market.
- The marinade is magical in a harmless, storybook way: it sings softly and
  makes the food it touches taste brave and bright.
- The market is crowded, so the parent can foresee a spill.
- A careful compromise keeps the jar safe and teaches patience, sharing, and
  kindness.

The world is intentionally tiny:
- one location: the market
- one prized object: the marinade jar
- one concern: spilling on clothes or the wrong stall goods
- one fix: a covered basket and a slow, careful walk home

The story quality comes from state transitions:
- desire raises hope
- foreshadowing raises worry
- a small magical event hints at trouble
- the compromise turns concern into calm
- the ending image proves the change
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
    protective: bool = False
    covers: set[str] = field(default_factory=set)
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.meters:
            self.meters = {"spill": 0.0, "shine": 0.0}
        if not self.memes:
            self.memes = {"joy": 0.0, "worry": 0.0, "love": 0.0, "patience": 0.0}

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "mother", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str = "the market"
    indoors: bool = False


@dataclass
class PrizedItem:
    label: str
    phrase: str
    region: str = "hands"
    plural: bool = False


@dataclass
class Gear:
    id: str
    label: str
    covers: set[str]
    prep: str
    tail: str
    plural: bool = False


@dataclass
class StoryParams:
    place: str = "market"
    name: str = "Mina"
    gender: str = "girl"
    parent: str = "mother"
    trait: str = "gentle"
    seed: Optional[int] = None


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
        self.facts: dict = {}
        self.magic_hummed = False

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
        clone.paragraphs = [[]]
        clone.fired = set(self.fired)
        clone.magic_hummed = self.magic_hummed
        return clone


SETTING = Setting(place="the market", indoors=False)

PRIZED_ITEM = PrizedItem(
    label="marinade",
    phrase="a small jar of fragrant marinade",
    region="hands",
    plural=False,
)

GEAR = [
    Gear(
        id="basket",
        label="a covered basket",
        covers={"hands"},
        prep="place the jar in a covered basket and walk slowly",
        tail="carried the jar home in a covered basket",
    ),
    Gear(
        id="cloth_wrap",
        label="a soft cloth wrap",
        covers={"hands"},
        prep="wrap the jar in a soft cloth first",
        tail="tucked the jar into a soft cloth wrap",
    ),
]

GIRL_NAMES = ["Mina", "Lina", "Tessa", "Nora", "Pippa", "Lumi"]
BOY_NAMES = ["Owen", "Theo", "Finn", "Nico", "Milo", "Jude"]
TRAITS = ["gentle", "curious", "patient", "bright", "soft-spoken"]


def in_market() -> bool:
    return True


def can_worry_about(item: PrizedItem) -> bool:
    return item.region == "hands"


def choose_gear(item: PrizedItem) -> Gear:
    for gear in GEAR:
        if item.region in gear.covers:
            return gear
    raise StoryError("No safe gear exists for this item.")


def predict_spill(world: World, child: Entity, marinade: Entity) -> bool:
    sim = world.copy()
    _carry(sim, sim.get(child.id), sim.get(marinade.id), narrate=False)
    return sim.get(marinade.id).meters["spill"] >= THRESHOLD


def _carry(world: World, child: Entity, marinade: Entity, narrate: bool = True) -> None:
    if not in_market():
        return
    child.memes["joy"] += 1
    marinade.meters["shine"] += 1
    if world.magic_hummed:
        marinade.memes["worry"] += 1
    if narrate:
        world.say(f"{child.id} held the jar carefully while the market seemed to hold its breath.")


def _spill_rule(world: World) -> list[str]:
    out: list[str] = []
    child = next((e for e in world.characters() if e.kind == "character"), None)
    if not child:
        return out
    for ent in world.entities.values():
        if ent.label != "marinade":
            continue
        if ent.meters["spill"] < THRESHOLD:
            continue
        sig = ("spill", ent.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        child.memes["worry"] += 1
        out.append("The parent noticed a tiny wobble and steadied the jar before any drop could fall.")
    return out


CAUSAL_RULES = [_spill_rule]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            sents = rule(world)
            if sents:
                changed = True
                produced.extend(sents)
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def setup_world(params: StoryParams) -> World:
    world = World(SETTING)
    child = world.add(Entity(id=params.name, kind="character", type=params.gender, memes={"joy": 0.0, "worry": 0.0, "love": 0.0, "patience": 0.0}))
    parent = world.add(Entity(id="Parent", kind="character", type=params.parent, label="the parent", memes={"joy": 0.0, "worry": 0.0, "love": 0.0, "patience": 0.0}))
    marinade = world.add(Entity(
        id="marinade",
        type="jar",
        label="marinade",
        phrase="a small jar of fragrant marinade",
        owner=child.id,
        caretaker=parent.id,
    ))
    world.facts.update(child=child, parent=parent, marinade=marinade, item=PRIZED_ITEM)
    return world


def tell_story(world: World, params: StoryParams) -> World:
    child = world.get(params.name)
    parent = world.get("Parent")
    marinade = world.get("marinade")

    child.memes["love"] += 1
    child.memes["joy"] += 1
    world.say(
        f"{child.id} was a {params.trait} little {params.gender} who loved the market's sleepy morning colors."
    )
    world.say(
        f"{child.id} especially loved {marinade.phrase}, because the magic in it made simple supper feel special."
    )
    world.say(
        f"Grandmothers smiled at the jars, and the fish seller said the marinade could make even plain bread taste brave."
    )

    world.para()
    world.say(
        f"One morning at {world.setting.place}, {child.id} wanted to carry the jar home all by {child.pronoun('object')}self."
    )
    world.say(
        f"Then the lid gave a tiny twinkle, as if the marinade knew a surprise was waiting on the walk home."
    )
    world.magic_hummed = True
    child.memes["worry"] += 1
    if predict_spill(world, child, marinade):
        world.say(
            f"{parent.id} noticed the little wobble and said, \"That jar is precious, and the crowd is busy. Let's be patient.\""
        )

    world.para()
    child.memes["patience"] += 1
    gear = choose_gear(PRIZED_ITEM)
    world.say(
        f"{child.id} nodded, and {parent.pronoun('subject')} offered {gear.label}. \"We can keep the magic safe if we move slowly,\" {parent.pronoun('subject')} said."
    )
    world.say(
        f"{child.id} smiled and accepted the gentle plan: {gear.prep}."
    )
    marinade.worn_by = child.id
    marinade.protective = True
    marinade.covers = set(gear.covers)
    _carry(world, child, marinade)
    propagate(world, narrate=True)

    world.para()
    child.memes["joy"] += 1
    child.memes["worry"] = 0.0
    world.say(
        f"By the time they reached home, {marinade.phrase} was still safe and the market's magic felt warm instead of rushed."
    )
    world.say(
        f"{child.id} learned that kind hands and patient steps can protect something special, and that was a good bedtime lesson."
    )
    world.facts["gear"] = gear
    world.facts["resolved"] = True
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    child = f["child"]
    parent = f["parent"]
    return [
        'Write a gentle bedtime story about a market, a little marinade jar, and a careful choice.',
        f'Write a short story where {child.id} wants to carry marinade home from the market, but {parent.id} worries and they find a safe plan.',
        'Tell a cozy story with foreshadowing, magic, and a moral about patience.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child = f["child"]
    parent = f["parent"]
    return [
        QAItem(
            question=f"What did {child.id} want to carry home from the market?",
            answer=f"{child.id} wanted to carry home {f['marinade'].phrase}.",
        ),
        QAItem(
            question=f"Why did {parent.id} worry about the jar?",
            answer="Because the market was busy and the little jar could wobble or spill if they rushed.",
        ),
        QAItem(
            question="What did they do to keep the marinade safe?",
            answer=f"They used {f['gear'].label} and walked slowly so the jar could stay safe.",
        ),
        QAItem(
            question="What lesson did the child learn?",
            answer="The child learned that patience and careful hands can protect something special.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a market?",
            answer="A market is a place where people buy and sell food and other useful things.",
        ),
        QAItem(
            question="What is marinade?",
            answer="Marinade is a tasty liquid or mix that soaks into food and gives it more flavor.",
        ),
        QAItem(
            question="Why do people cover a jar before carrying it?",
            answer="People cover a jar so it does not spill and make a mess.",
        ),
        QAItem(
            question="What is foreshadowing in a story?",
            answer="Foreshadowing is a small hint that something important or tricky may happen soon.",
        ),
        QAItem(
            question="What is a gentle moral in a bedtime story?",
            answer="A gentle moral is a kind lesson, like being patient, careful, or helpful.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
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


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for e in world.entities.values():
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        if e.protective:
            bits.append(f"covers={sorted(e.covers)}")
        lines.append(f"  {e.id}: {' '.join(bits)}")
    return "\n".join(lines)


ASP_RULES = r"""
place(market).
item(marinade).
feature(magic).
feature(foreshadowing).
feature(moral_value).

safe_fix(marinade, basket) :- place(market), item(marinade).
safe_fix(marinade, cloth_wrap) :- place(market), item(marinade).

valid_story(place, item, feature) :- place(place), item(item), feature(feature).
"""


def asp_facts() -> str:
    import asp
    return "\n".join(
        [
            asp.fact("place", "market"),
            asp.fact("item", "marinade"),
            asp.fact("feature", "magic"),
            asp.fact("feature", "foreshadowing"),
            asp.fact("feature", "moral_value"),
            asp.fact("setting", "market"),
        ]
    )


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/3."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    py = {("market", "marinade", "magic"), ("market", "marinade", "foreshadowing"), ("market", "marinade", "moral_value")}
    cl = set(asp_valid())
    if py == cl:
        print(f"OK: ASP matches Python gate ({len(py)} tuples).")
        return 0
    print("MISMATCH between ASP and Python gate:")
    if py - cl:
        print("  only in python:", sorted(py - cl))
    if cl - py:
        print("  only in ASP:", sorted(cl - py))
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A bedtime story world set in a market with a magical marinade jar.")
    ap.add_argument("--place", choices=["market"])
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--parent", choices=["mother", "father"])
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
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    parent = args.parent or rng.choice(["mother", "father"])
    trait = args.trait or rng.choice(TRAITS)
    return StoryParams(place="market", name=name, gender=gender, parent=parent, trait=trait)


def generate(params: StoryParams) -> StorySample:
    world = setup_world(params)
    tell_story(world, params)
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


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid_story/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print("1 compatible story tuple:")
        for t in asp_valid():
            print(" ", t)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)

    if args.all:
        params_list = [
            StoryParams(place="market", name="Mina", gender="girl", parent="mother", trait="gentle"),
            StoryParams(place="market", name="Theo", gender="boy", parent="father", trait="curious"),
            StoryParams(place="market", name="Lumi", gender="girl", parent="mother", trait="patient"),
        ]
        samples = [generate(p) for p in params_list]
    else:
        samples = []
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 20):
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
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.name} at the market"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()

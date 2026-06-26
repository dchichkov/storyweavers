#!/usr/bin/env python3
"""
storyworlds/worlds/bus_blonde_currant_teamwork_comedy.py
========================================================

A small story world about a bus ride, a blonde child, and a currant problem
that gets solved through teamwork, with a light comedy tone.

Premise:
- A blonde child rides a bus with a small tray of currants for a snack sale.
- The bus's bumps threaten to spill the currants.
- The child, driver, and a couple of helpers work together to keep the snack safe.
- The ending proves the currants stayed in the bowl and the ride became a joke
  they all laughed about.

This world is intentionally small and constraint-checked:
- the bus can be smooth or bumpy,
- the currants can spill if not handled together,
- teamwork is the plausible fix,
- invalid explicit choices raise StoryError.

The generated stories are child-facing, concrete, and state-driven.
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


# ---------------------------------------------------------------------------
# World constants
# ---------------------------------------------------------------------------
THRESHOLD = 1.0


# ---------------------------------------------------------------------------
# Entities
# ---------------------------------------------------------------------------
@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    traits: list[str] = field(default_factory=list)
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    carrier: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "woman", "mother", "female", "blonde"}
        male = {"boy", "man", "father", "male"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class Setting:
    place: str = "the bus"
    smoothness: str = "bumpy"
    affords: set[str] = field(default_factory=set)


@dataclass
class Activity:
    id: str
    verb: str
    gerund: str
    bump: str
    mess: str
    keyword: str = ""
    tags: set[str] = field(default_factory=set)


@dataclass
class Prize:
    label: str
    phrase: str
    type: str
    holder: str = "bowl"
    fragile: bool = True


@dataclass
class Helper:
    id: str
    label: str
    role: str
    action: str


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

    def copy(self) -> "World":
        import copy
        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        clone.facts = dict(self.facts)
        return clone


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------
SETTINGS = {
    "bus": Setting(place="the bus", smoothness="bumpy", affords={"ride"}),
    "school_bus": Setting(place="the school bus", smoothness="bumpy", affords={"ride"}),
    "mini_bus": Setting(place="the little bus", smoothness="extra bumpy", affords={"ride"}),
    "smooth_bus": Setting(place="the bus", smoothness="smooth", affords={"ride"}),
}

ACTIVITIES = {
    "ride": Activity(
        id="ride",
        verb="ride the bus",
        gerund="riding the bus",
        bump="a bump",
        mess="spilled currants",
        keyword="bus",
        tags={"bus", "ride", "comedy"},
    ),
}

PRIZES = {
    "currants": Prize(
        label="currants",
        phrase="a small bowl of currants",
        type="currants",
        holder="bowl",
        fragile=True,
    ),
}

HELPERS = [
    Helper(id="driver", label="the driver", role="driver", action="steady the bus"),
    Helper(id="friend", label="a friend", role="friend", action="hold the bowl"),
    Helper(id="seatmate", label="a seatmate", role="seatmate", action="make a hand shield"),
]

NAMES = ["Lily", "Mia", "Zoe", "Ava", "Ella", "Nora", "Rose"]
TRAITS = ["playful", "curious", "cheerful", "silly", "brave", "funny"]


# ---------------------------------------------------------------------------
# Story params
# ---------------------------------------------------------------------------
@dataclass
class StoryParams:
    setting: str = "bus"
    activity: str = "ride"
    prize: str = "currants"
    name: str = "Lily"
    gender: str = "girl"
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# Core simulation
# ---------------------------------------------------------------------------
def _do_ride(world: World, child: Entity, prize: Entity) -> list[str]:
    out: list[str] = []
    sig = ("ride", child.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    child.meters["bump"] = child.meters.get("bump", 0.0) + 1.0
    child.memes["worry"] = child.memes.get("worry", 0.0) + 1.0
    if world.setting.smoothness == "extra bumpy":
        child.meters["bump"] += 1.0
        child.memes["worry"] += 1.0
    if child.meters["teamwork"] >= THRESHOLD:
        out.append("The little plan kept everything steady.")
        prize.meters["safe"] = prize.meters.get("safe", 0.0) + 1.0
    else:
        prize.meters["spill"] = prize.meters.get("spill", 0.0) + 1.0
        out.append("The bowl tipped and the currants bounced like tiny red marbles.")
    return out


def predict_spill(world: World, child: Entity, prize: Entity) -> bool:
    sim = world.copy()
    _do_ride(sim, sim.get(child.id), sim.get(prize.id))
    return sim.get(prize.id).meters.get("spill", 0.0) >= THRESHOLD


def intro(world: World, child: Entity) -> None:
    trait = next((t for t in child.traits if t != "little"), "silly")
    world.say(
        f"{child.id} was a little {trait} {child.type} who liked every funny thing "
        f"that happened on a bus."
    )


def currant_setup(world: World, child: Entity, prize: Entity) -> None:
    world.say(
        f"{child.id} had a small bowl of currants, and {child.pronoun('possessive')} "
        f"currants looked shiny and round."
    )


def board_bus(world: World, child: Entity) -> None:
    world.say(
        f"One day, {child.id} climbed onto {world.setting.place} and sat down with a grin."
    )
    if world.setting.smoothness == "extra bumpy":
        world.say("The bus gave a tiny jolt, as if it had laughed at its own joke.")


def worry(world: World, child: Entity, prize: Entity) -> None:
    if predict_spill(world, child, prize):
        child.memes["worry"] = child.memes.get("worry", 0.0) + 1.0
        world.say(
            f"{child.id} held {child.pronoun('possessive')} bowl tight and said, "
            f"\"Oh no, my currants are doing the wiggle dance.\""
        )
    else:
        world.say(f"{child.id} smiled because the bowl felt safe in {child.pronoun('possessive')} lap.")


def teamwork_plan(world: World, child: Entity) -> Helper:
    helper = random.choice(HELPERS)
    child.memes["teamwork"] = child.memes.get("teamwork", 0.0) + 1.0
    world.say(
        f"Then {helper.label} noticed the wobble and said, "
        f"\"Let's help together.\""
    )
    world.say(
        f"{helper.label.capitalize()} promised to {helper.action}, while {child.id} kept the bowl level."
    )
    return helper


def resolve(world: World, child: Entity, prize: Entity, helper: Helper) -> None:
    child.meters["teamwork"] = child.meters.get("teamwork", 0.0) + 1.0
    prize.meters["safe"] = prize.meters.get("safe", 0.0) + 1.0
    child.memes["joy"] = child.memes.get("joy", 0.0) + 1.0
    world.say(
        f"With {helper.label} helping and {child.id} balancing the bowl, the currants stayed put."
    )
    world.say(
        f"When the bus hit one last bump, everyone laughed, because the bowl only wobbled "
        f"like it was telling a silly secret."
    )
    world.say(
        f"By the end of the ride, {child.id} was laughing too, and {child.pronoun('possessive')} "
        f"currants were still ready to eat."
    )


def tell(setting: Setting, child_name: str = "Lily", child_type: str = "girl") -> World:
    world = World(setting)
    child = world.add(Entity(
        id=child_name,
        kind="character",
        type=child_type,
        traits=["little", random.choice(TRAITS)],
        meters={"teamwork": 0.0},
        memes={},
    ))
    prize = world.add(Entity(
        id="currants",
        type="currants",
        label="currants",
        phrase="a small bowl of currants",
        owner=child.id,
        caretaker=child.id,
        meters={},
        memes={},
    ))

    intro(world, child)
    currant_setup(world, child, prize)
    world.para()
    board_bus(world, child)
    worry(world, child, prize)
    helper = teamwork_plan(world, child)
    resolve(world, child, prize, helper)

    world.facts.update(child=child, prize=prize, helper=helper)
    return world


# ---------------------------------------------------------------------------
# QA
# ---------------------------------------------------------------------------
def generation_prompts(world: World) -> list[str]:
    f = world.facts
    child = f["child"]
    return [
        'Write a short comedic story about a bus ride, a blonde child, and currants.',
        f"Tell a funny story where {child.id} rides a bus with currants and learns to work together with helpers.",
        'Write a child-friendly story in which teamwork keeps currants from spilling on a bumpy bus.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child = f["child"]
    prize = f["prize"]
    helper = f["helper"]
    return [
        QAItem(
            question=f"Who is the story about?",
            answer=f"The story is about {child.id}, a little blonde child riding a bus with currants.",
        ),
        QAItem(
            question=f"What problem happened on the bus?",
            answer="The bus was bumpy, so the bowl of currants almost spilled and bounced around like tiny red marbles.",
        ),
        QAItem(
            question=f"How did {child.id} keep the currants safe?",
            answer=f"{child.id} and {helper.label} worked together so the bowl stayed steady and the currants stayed safe.",
        ),
        QAItem(
            question=f"How did the story end?",
            answer=f"It ended with {child.id} laughing on the bus because the currants stayed in the bowl.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a bus for?",
            answer="A bus is a big vehicle that carries people from one place to another.",
        ),
        QAItem(
            question="What are currants?",
            answer="Currants are tiny dried berries that are often sweet and a little chewy.",
        ),
        QAItem(
            question="What does teamwork mean?",
            answer="Teamwork means people help each other and do a job together.",
        ),
        QAItem(
            question="What does blonde mean?",
            answer="Blonde means having light yellow or pale hair.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== Story QA ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== World QA ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for ent in world.entities.values():
        meters = {k: v for k, v in ent.meters.items() if v}
        memes = {k: v for k, v in ent.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        lines.append(f"  {ent.id}: {ent.type} {' '.join(bits)}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Reasonableness / ASP twin
# ---------------------------------------------------------------------------
def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for setting_id, setting in SETTINGS.items():
        for act_id in setting.affords:
            for prize_id in PRIZES:
                combos.append((setting_id, act_id, prize_id))
    return combos


ASP_RULES = r"""
setting(bus).
setting(school_bus).
setting(mini_bus).
setting(smooth_bus).

affords(bus,ride).
affords(school_bus,ride).
affords(mini_bus,ride).
affords(smooth_bus,ride).

activity(ride).
prize(currants).

valid(S,A,P) :- affords(S,A), prize(P), activity(A).
#show valid/3.
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid, s in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        if s.smoothness:
            lines.append(asp.fact("smoothness", sid, s.smoothness))
        for a in sorted(s.affords):
            lines.append(asp.fact("affords", sid, a))
    for aid in ACTIVITIES:
        lines.append(asp.fact("activity", aid))
    for pid in PRIZES:
        lines.append(asp.fact("prize", pid))
    return "\n".join(lines)


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
        print(f"OK: ASP matches Python ({len(py)} combos).")
        return 0
    print("MISMATCH between ASP and Python")
    if py - cl:
        print("  only in Python:", sorted(py - cl))
    if cl - py:
        print("  only in ASP:", sorted(cl - py))
    return 1


# ---------------------------------------------------------------------------
# Generation
# ---------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A small comedic bus-and-currants story world.")
    ap.add_argument("--setting", choices=SETTINGS.keys())
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["girl", "boy"])
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
    setting = args.setting or rng.choice(list(SETTINGS.keys()))
    gender = args.gender or "girl"
    name = args.name or rng.choice(NAMES)
    return StoryParams(setting=setting, name=name, gender=gender, seed=None)


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.setting], params.name, params.gender)
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
    StoryParams(setting="bus", name="Lily", gender="girl"),
    StoryParams(setting="school_bus", name="Mia", gender="girl"),
    StoryParams(setting="mini_bus", name="Ava", gender="girl"),
    StoryParams(setting="smooth_bus", name="Zoe", gender="girl"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print("compatible combos:", asp_valid_combos())
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 20):
            rng = random.Random(base_seed + i)
            i += 1
            params = resolve_params(args, rng)
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

    for i, sample in enumerate(samples):
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.name}: {p.setting}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""
storyworlds/worlds/card_dim_security_campground_problem_solving_suspense.py
==========================================================================

A tiny campground story world with a rhyming, suspenseful problem-solving tale.

Seed tale inspiration:
---
At a campground gate, a child and a parent found a sleepy security station with
a dim little card reader. The gate would not open, and the lantern was too weak
to show the badge. The child and parent had to solve the problem without losing
their place in line, and the final answer came from a careful, patient search.
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
    traits: list[str] = field(default_factory=list)
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def __post_init__(self):
        if not self.meters:
            self.meters = {"dim": 0.0, "secure": 0.0, "lost": 0.0, "found": 0.0}
        if not self.memes:
            self.memes = {"worry": 0.0, "hope": 0.0, "joy": 0.0, "conflict": 0.0}

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman", "aunt"}
        male = {"boy", "father", "dad", "man", "uncle"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Campground:
    place: str = "the campground"
    has_gate: bool = True
    has_lantern: bool = True
    has_card_reader: bool = True


@dataclass
class StoryParams:
    place: str = "campground"
    name: str = "Maya"
    gender: str = "girl"
    parent: str = "mother"
    trait: str = "brave"
    seed: Optional[int] = None


class World:
    def __init__(self, setting: Campground) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
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
        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        clone.facts = copy.deepcopy(self.facts)
        return clone

    def characters(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.kind == "character"]


@dataclass
class Rule:
    name: str
    apply: callable


def _r_lantern_dim(world: World) -> list[str]:
    out: list[str] = []
    lantern = world.entities.get("lantern")
    if not lantern:
        return out
    if lantern.meters["dim"] < THRESHOLD:
        return out
    sig = ("lantern_dim")
    if sig in world.fired:
        return out
    world.fired.add(sig)
    world.entities["gate"].memes["conflict"] += 1
    out.append("The lantern went dim, and the gate would not grin.")
    return out


def _r_card_unread(world: World) -> list[str]:
    out: list[str] = []
    card = world.entities.get("card")
    if not card:
        return out
    if card.meters["dim"] < THRESHOLD:
        return out
    sig = ("card_unread")
    if sig in world.fired:
        return out
    world.fired.add(sig)
    world.entities["reader"].memes["worry"] += 1
    out.append("The card looked dim in the hand, and the reader could not scan.")
    return out


def _r_fix_found(world: World) -> list[str]:
    out: list[str] = []
    lantern = world.entities["lantern"]
    card = world.entities["card"]
    flashlight = world.entities["flashlight"]
    if lantern.meters["found"] < THRESHOLD:
        return out
    if card.meters["found"] < THRESHOLD:
        return out
    if flashlight.meters["found"] < THRESHOLD:
        return out
    sig = ("fix_found")
    if sig in world.fired:
        return out
    world.fired.add(sig)
    world.entities["gate"].meters["secure"] += 1
    world.entities["reader"].memes["worry"] = 0.0
    out.append("With a bright beam and a found card, the gate could open at dawn.")
    return out


CAUSAL_RULES = [
    Rule("lantern_dim", _r_lantern_dim),
    Rule("card_unread", _r_card_unread),
    Rule("fix_found", _r_fix_found),
]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            sents = rule.apply(world)
            if sents:
                changed = True
                produced.extend(sents)
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def rhyme_line(a: str, b: str) -> str:
    return f"{a} {b}"


def setup_story(world: World, hero: Entity, parent: Entity) -> None:
    world.say(
        f"{hero.id} was a little {hero.type} with a {hero.trait if hasattr(hero, 'trait') else 'bright'} heart, "
        f"and {hero.pronoun()} liked the campground night."
    )
    world.say(
        f"{hero.pronoun().capitalize()} and {parent.label} came for a calm camp stay, "
        f"with tents and pine trees swaying away."
    )
    world.say(
        "Near the gate sat a sleepy security stand, "
        "with a card reader, a lantern, and a patient hand."
    )


def trouble_story(world: World, hero: Entity, parent: Entity) -> None:
    card = world.get("card")
    lantern = world.get("lantern")
    world.para()
    world.say(
        f"But the lantern was dim, and the card was dim too; "
        f"the reader blinked once and did not know what to do."
    )
    hero.memes["worry"] += 1
    parent.memes["worry"] += 1
    world.say(
        f"{hero.id} held the card up high in the hush, "
        f"while {parent.label} said, \"Slow now, let's not rush.\""
    )
    lantern.meters["dim"] = 1.0
    card.meters["dim"] = 1.0
    propagate(world, narrate=True)


def solve_story(world: World, hero: Entity, parent: Entity) -> None:
    card = world.get("card")
    lantern = world.get("lantern")
    flashlight = world.get("flashlight")
    world.para()
    world.say(
        f"Then {hero.id} looked in the pack with a careful little glance, "
        f"for a tiny lost flashlight might give them a chance."
    )
    flashlight.meters["found"] = 1.0
    card.meters["found"] = 1.0
    lantern.meters["found"] = 1.0
    hero.memes["hope"] += 1
    parent.memes["hope"] += 1
    world.say(
        f"{hero.id} shone the beam on the card, not a moment too late; "
        f"the reader woke softly and unlocked the gate."
    )
    propagate(world, narrate=True)
    hero.memes["joy"] += 1
    parent.memes["joy"] += 1
    world.say(
        f"They stepped through together, all safe and all sound, "
        f"while the campground lights twinkled low to the ground."
    )


def tell_story() -> World:
    world = World(Campground())
    hero = world.add(Entity(id="Mina", kind="character", type="girl", traits=["curious", "careful"]))
    hero.trait = "curious"
    parent = world.add(Entity(id="Parent", kind="character", type="mother", label="mom"))
    gate = world.add(Entity(id="gate", type="gate", label="gate"))
    reader = world.add(Entity(id="reader", type="reader", label="reader"))
    lantern = world.add(Entity(id="lantern", type="lantern", label="lantern"))
    card = world.add(Entity(id="card", type="card", label="camp card"))
    flashlight = world.add(Entity(id="flashlight", type="flashlight", label="flashlight"))

    card.worn_by = hero.id
    card.owner = hero.id
    lantern.owner = "camp"
    flashlight.owner = hero.id

    setup_story(world, hero, parent)
    trouble_story(world, hero, parent)
    solve_story(world, hero, parent)

    world.facts.update(hero=hero, parent=parent, gate=gate, reader=reader,
                       lantern=lantern, card=card, flashlight=flashlight)
    return world


KNOWLEDGE = {
    "campground": [
        QAItem(
            question="What is a campground?",
            answer="A campground is a place where people put up tents, sleep outside, and enjoy nature together."
        ),
        QAItem(
            question="Why do campgrounds have security gates?",
            answer="Campgrounds may have security gates to help keep campers safe and to make sure only the right people come in."
        ),
    ],
    "card": [
        QAItem(
            question="What is a card used for at a gate?",
            answer="A card can be used to show permission or identity so a gate or reader knows who may enter."
        )
    ],
    "security": [
        QAItem(
            question="What does security mean?",
            answer="Security means protection and safety, often with rules, gates, or people watching to help keep things safe."
        )
    ],
    "dim": [
        QAItem(
            question="What does dim mean?",
            answer="Dim means not very bright, so it can be hard to see."
        )
    ],
    "flashlight": [
        QAItem(
            question="What does a flashlight do?",
            answer="A flashlight makes a beam of light that helps people see in the dark."
        )
    ],
}


def generation_prompts(world: World) -> list[str]:
    return [
        'Write a short rhyming story for young children set at a campground, with a security gate, a dim card, and a careful fix.',
        'Tell a suspenseful campground story where a child solves a problem with a flashlight and a security reader.',
        'Write a gentle rhyming tale about card-dim security at a campground and end with the gate opening safely.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    parent = f["parent"]
    qa = [
        QAItem(
            question=f"Where does {hero.id}'s story happen?",
            answer="It happens at the campground, near a security gate with a dim card reader."
        ),
        QAItem(
            question=f"What was wrong with the card and lantern?",
            answer="Both were dim, so the reader could not see the card well enough at first."
        ),
        QAItem(
            question=f"How did {hero.id} and {parent.label} solve the problem?",
            answer="They searched carefully, found the flashlight, shone it on the card, and helped the gate open."
        ),
        QAItem(
            question=f"How did {hero.id} feel when the gate opened?",
            answer=f"{hero.id} felt happy and relieved because the careful fix worked."
        ),
    ]
    return qa


def world_knowledge_qa(world: World) -> list[QAItem]:
    out: list[QAItem] = []
    out.extend(KNOWLEDGE["campground"])
    out.extend(KNOWLEDGE["security"])
    out.extend(KNOWLEDGE["card"])
    out.extend(KNOWLEDGE["dim"])
    out.extend(KNOWLEDGE["flashlight"])
    return out


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
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        if e.worn_by:
            bits.append(f"worn_by={e.worn_by}")
        lines.append(f"  {e.id:10} ({e.type:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted({n for n, *_ in world.fired})}")
    return "\n".join(lines)


ASP_RULES = r"""
dim_card(C) :- card(C), card_dim(C).
dim_lantern(L) :- lantern(L), lantern_dim(L).
problem(S) :- security(S), dim_card(C), card_reader(S), reader_needs_card(S).
problem(S) :- security(S), dim_lantern(L), gate_at(S).
fix_found(S) :- problem(S), found_flashlight(F), flashlight(F).
resolved(S) :- fix_found(S).
"""

def asp_facts() -> str:
    import asp
    lines = [
        asp.fact("campground", "campground"),
        asp.fact("security", "security"),
        asp.fact("gate_at", "campground"),
        asp.fact("card_reader", "campground"),
        asp.fact("reader_needs_card", "campground"),
        asp.fact("card", "card"),
        asp.fact("card_dim", "card"),
        asp.fact("lantern", "lantern"),
        asp.fact("lantern_dim", "lantern"),
        asp.fact("flashlight", "flashlight"),
        asp.fact("found_flashlight", "flashlight"),
        asp.fact("flashlight", "flashlight"),
    ]
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def valid_story() -> bool:
    return True


def asp_verify() -> int:
    try:
        import asp
    except Exception as e:
        print(f"ASP unavailable: {e}")
        return 1
    model = asp.one_model(asp_program("#show problem/1. #show resolved/1."))
    atoms = {(sym.name, tuple(a.name if hasattr(a, "name") else getattr(a, "string", getattr(a, "number", None)) for a in sym.arguments)) for sym in model}
    ok = ("problem", ("campground",)) in atoms and ("resolved", ("campground",)) in atoms
    if ok:
        print("OK: ASP program finds the campground security problem and its resolution.")
        return 0
    print("MISMATCH: ASP program did not derive the expected result.")
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Rhyming campground story world with security and problem solving.")
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
    return StoryParams(
        place="campground",
        name=rng.choice(["Mina", "Luna", "Tara", "Nia", "Ivy"]),
        gender=rng.choice(["girl", "boy"]),
        parent=rng.choice(["mother", "father"]),
        trait=rng.choice(["brave", "curious", "careful", "cheerful"]),
        seed=args.seed,
    )


def generate(params: StoryParams) -> StorySample:
    world = tell_story()
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


CURATED = [StoryParams(place="campground", name="Mina", gender="girl", parent="mother", trait="curious")]


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show problem/1. #show resolved/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        model = asp.one_model(asp_program("#show problem/1. #show resolved/1."))
        print("ASP model:", model)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 20):
            params = resolve_params(args, random.Random(base_seed + i))
            sample = generate(params)
            if sample.story not in seen:
                seen.add(sample.story)
                samples.append(sample)
            i += 1

    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for idx, sample in enumerate(samples):
        header = f"### variant {idx + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if idx < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()

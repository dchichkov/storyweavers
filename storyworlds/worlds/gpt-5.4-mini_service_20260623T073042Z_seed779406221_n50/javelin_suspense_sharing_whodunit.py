#!/usr/bin/env python3
"""
storyworlds/worlds/javelin_suspense_sharing_whodunit.py
========================================================

A small standalone storyworld: a suspenseful whodunit about a missing javelin,
where a group of children share clues, tools, and the final discovery.

Premise:
- A practice javelin is missing from a school shed.
- The children feel suspense because someone may have borrowed it without asking.
- They share clues and small items to search carefully.
- The ending reveals the honest, ordinary reason and shows what changed.

This world keeps two state dimensions on entities:
- meters: physical quantities such as distance, hiddenness, and possession.
- memes: emotional quantities such as suspense, worry, trust, and relief.
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
    traits: list[str] = field(default_factory=list)
    owner: Optional[str] = None
    location: str = ""
    hidden: bool = False
    sharable: bool = False
    meters: dict[str, float] = field(default_factory=lambda: {"distance": 0.0, "hidden": 0.0, "held": 0.0})
    memes: dict[str, float] = field(default_factory=lambda: {"suspense": 0.0, "worry": 0.0, "trust": 0.0, "relief": 0.0})

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman"}
        male = {"boy", "father", "dad", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return self.label or self.type


@dataclass
class Setting:
    place: str
    affordances: set[str] = field(default_factory=set)


@dataclass
class Item:
    id: str
    label: str
    phrase: str
    location: str
    sharable: bool = False
    hidden: bool = False
    clue: str = ""
    meters: dict[str, float] = field(default_factory=lambda: {"distance": 0.0, "hidden": 0.0, "held": 0.0})
    memes: dict[str, float] = field(default_factory=lambda: {"suspense": 0.0, "worry": 0.0, "trust": 0.0, "relief": 0.0})


@dataclass
class World:
    setting: Setting
    entities: dict[str, Entity] = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    fired: set[tuple] = field(default_factory=set)
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
        c = World(self.setting)
        c.entities = copy.deepcopy(self.entities)
        c.paragraphs = [[]]
        c.fired = set(self.fired)
        c.facts = copy.deepcopy(self.facts)
        return c


def propagate(world: World, narrate: bool = True) -> list[str]:
    out: list[str] = []
    changed = True
    while changed:
        changed = False
        for ent in world.characters():
            if ent.memes["suspense"] >= THRESHOLD and ("mood", ent.id) not in world.fired:
                world.fired.add(("mood", ent.id))
                ent.memes["worry"] += 0.5
                out.append(f"{ent.id} felt a tight, puzzly worry in {ent.pronoun('possessive')} chest.")
                changed = True
            if ent.meters["held"] >= THRESHOLD and ("share", ent.id) not in world.fired:
                world.fired.add(("share", ent.id))
                ent.memes["trust"] += 0.5
                out.append(f"{ent.id} passed the clue along so everyone could help.")
                changed = True
            if ent.memes["relief"] >= THRESHOLD and ("relief", ent.id) not in world.fired:
                world.fired.add(("relief", ent.id))
                out.append(f"{ent.id} finally breathed out and smiled.")
                changed = True
    if narrate:
        for s in out:
            world.say(s)
    return out


@dataclass
class StoryParams:
    place: str
    main_child: str
    helper: str
    guardian: str
    missing_item: str
    found_place: str
    seed: Optional[int] = None


SETTINGS = {
    "gym": Setting("the gym", {"practice", "share"}),
    "field": Setting("the field", {"practice", "share"}),
    "yard": Setting("the school yard", {"practice", "share"}),
}

ITEMS = {
    "javelin": Item(
        id="javelin",
        label="javelin",
        phrase="the smooth practice javelin",
        location="storage shed",
        sharable=True,
        hidden=True,
        clue="a taped label and a blue ribbon",
    )
}

FOUND_PLACES = ["the bench", "the back of the shed", "the coach's desk", "the tall grass"]

NAMES = ["Mia", "Noah", "Ava", "Leo", "Zoe", "Finn", "Lily", "Sam"]


def valid_combos() -> list[tuple[str, str]]:
    return [(p, "javelin") for p in SETTINGS]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A suspenseful whodunit about a shared javelin.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--missing-item", choices=ITEMS)
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
    combos = [c for c in valid_combos() if (args.place is None or c[0] == args.place) and (args.missing_item is None or c[1] == args.missing_item)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, missing_item = rng.choice(sorted(combos))
    return StoryParams(
        place=place,
        main_child=rng.choice(NAMES),
        helper=rng.choice([n for n in NAMES if n != "" and n != NAMES[0]]),
        guardian=rng.choice(["coach", "teacher"]),
        missing_item=missing_item,
        found_place=rng.choice(FOUND_PLACES),
    )


def tell(params: StoryParams) -> World:
    world = World(SETTINGS[params.place])
    main = world.add(Entity(id=params.main_child, kind="character", type="child", label=params.main_child))
    helper = world.add(Entity(id=params.helper, kind="character", type="child", label=params.helper))
    guardian = world.add(Entity(id=params.guardian, kind="character", type="adult", label=f"the {params.guardian}"))
    item = world.add(Entity(id="javelin", type="object", label="javelin", owner=guardian.id, location="shed", hidden=True, sharable=True))

    main.memes["suspense"] += 1
    helper.memes["suspense"] += 1
    world.say(f"At {world.setting.place}, {main.id} and {helper.id} noticed the practice room was too quiet for a javelin story.")
    world.say(f"Their coach had left a clean place for {item.label}, but the rack was empty, and that made the day feel like a riddle.")

    world.para()
    main.memes["worry"] += 0.5
    helper.memes["worry"] += 0.5
    world.say(f"{main.id} looked under the bench while {helper.id} checked the corner of the shed.")
    world.say(f"They shared what they saw, because a clue is easier to trust when two children can look at it together.")

    world.para()
    world.say(f"Then {helper.id} found the trail: {ITEMS['javelin'].clue} near {params.found_place}.")
    world.say(f"It was not a stolen secret after all; the javelin had been moved safely so nobody would trip on it.")
    item.hidden = False
    item.location = params.found_place
    item.meters["held"] = 1.0
    main.memes["relief"] += 1
    helper.memes["relief"] += 1
    guardian.memes["relief"] += 1
    propagate(world)
    world.para()
    world.say(f"The {params.guardian} thanked them for sharing the clues instead of jumping to guesses.")
    world.say(f"By the end, the javelin was back in sight, the mystery was solved, and the room felt ordinary again, which was the best kind of ending.")
    world.facts.update(main=main, helper=helper, guardian=guardian, item=item, params=params)
    return world


def generation_prompts(world: World) -> list[str]:
    p = world.facts["params"]
    return [
        f'Write a suspenseful whodunit for a 3-to-5-year-old about a missing {p.missing_item}.',
        f"Tell a child-sized mystery where {p.main_child} and {p.helper} share clues to find the javelin again.",
        f'Write a gentle detective story set at {p.place} that ends with sharing, truth, and the word "javelin".',
    ]


def story_qa(world: World) -> list[QAItem]:
    p = world.facts["params"]
    main = world.facts["main"]
    helper = world.facts["helper"]
    guardian = world.facts["guardian"]
    item = world.facts["item"]
    return [
        QAItem(
            question=f"What was missing from {p.place}?",
            answer=f"The javelin was missing from {p.place}, and that made the children feel suspense because they had to solve a little mystery.",
        ),
        QAItem(
            question=f"Who shared the clues to solve the mystery?",
            answer=f"{main.id} and {helper.id} shared what they found, and the sharing helped them solve the whodunit together.",
        ),
        QAItem(
            question=f"Why was the javelin not really stolen?",
            answer=f"It had been moved safely to {p.found_place} so nobody would trip on it, so the mystery ended with an ordinary, honest reason.",
        ),
        QAItem(
            question=f"How did the {guardian.id} feel at the end?",
            answer=f"The {guardian.id} felt relieved and thankful because the children used careful thinking and sharing instead of panicking.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a javelin?",
            answer="A javelin is a long throwing spear used in sports practice and games with careful rules.",
        ),
        QAItem(
            question="Why do detectives share clues?",
            answer="Detectives share clues so everyone can compare what they know and solve the mystery more fairly.",
        ),
        QAItem(
            question="What does suspense mean in a story?",
            answer="Suspense is the feeling that something important is about to be found out, so you keep wondering what will happen next.",
        ),
    ]


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
        lines.append(f"  {e.id:10} ({e.type}) meters={dict(e.meters)} memes={dict(e.memes)}")
    return "\n".join(lines)


CURATED = [
    StoryParams(place="gym", main_child="Mia", helper="Leo", guardian="coach", missing_item="javelin", found_place="the bench"),
    StoryParams(place="field", main_child="Noah", helper="Ava", guardian="teacher", missing_item="javelin", found_place="the back of the shed"),
]


ASP_RULES = r"""
valid(Place, Item) :- setting(Place), missing(Item), place_has(Place, Item).
"""


def asp_facts() -> str:
    import storyworlds.asp as asp
    return "\n".join(
        [asp.fact("setting", p) for p in SETTINGS] +
        [asp.fact("missing", i) for i in ITEMS] +
        [asp.fact("place_has", p, "javelin") for p in SETTINGS]
    )


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import storyworlds.asp as asp
    model = asp.one_model(asp_program("#show valid/2."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos().")
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


def main() -> None:
    args = build_parser().parse_args()
    if args.verify:
        sys.exit(asp_verify())
    if args.show_asp:
        print(asp_program("#show valid/2."))
        return
    if args.asp:
        for combo in asp_valid_combos():
            print(combo)
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
        emit(sample, trace=args.trace, qa=args.qa, header=(f"### variant {i+1}" if len(samples) > 1 else ""))
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""
A small bedtime-story world about an ambidextrous quest and a gentle moral value.

A child is trying to finish a cozy nighttime quest before bed. The child is
ambidextrous, so both hands can help in different ways, but a small problem makes
the quest tricky. The story turns on a moral choice: be proud and hurry alone, or
listen, share the work, and finish kindly.

The simulated state tracks:
- a bedtime quest with a missing item
- the child's two-handed skill
- a worry that grows when the child refuses help
- a moral value that grows when the child chooses kindness
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
# World model
# ---------------------------------------------------------------------------
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

    def __post_init__(self) -> None:
        for k in ["tired", "safe", "lost", "found", "needed", "near_bed"]:
            self.meters.setdefault(k, 0.0)
        for k in ["pride", "worry", "kindness", "calm", "joy", "stubbornness"]:
            self.memes.setdefault(k, 0.0)

    def pronoun(self, case: str = "subject") -> str:
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str = "the cozy bedroom"
    affords: set[str] = field(default_factory=lambda: {"quest"})


@dataclass
class Quest:
    id: str
    goal: str
    verb: str
    missing_item: str
    item_phrase: str
    item_label: str
    conflict: str
    resolution: str
    moral: str
    keyword: str = "ambidextrous"


@dataclass
class StoryParams:
    place: str
    quest: str
    name: str
    seed: Optional[int] = None


class World:
    def __init__(self, setting: Setting) -> None:
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
        import copy
        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        return clone


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------
SETTINGS = {
    "bedroom": Setting(place="the cozy bedroom"),
    "nursery": Setting(place="the quiet nursery"),
}

QUESTS = {
    "lost_star": Quest(
        id="lost_star",
        goal="find the missing bedtime star",
        verb="look for the missing bedtime star",
        missing_item="star",
        item_phrase="a little golden star",
        item_label="star",
        conflict="the child wants to search alone and rushes past the clues",
        resolution="the child uses both hands, listens, and searches carefully",
        moral="It is kinder to accept help than to stay proud and lost.",
    ),
    "missing_book": Quest(
        id="missing_book",
        goal="find the soft bedtime book",
        verb="search for the soft bedtime book",
        missing_item="book",
        item_phrase="a soft blue bedtime book",
        item_label="book",
        conflict="the child gets upset and grabs the wrong pile in a hurry",
        resolution="the child slows down, uses both hands, and checks every shelf",
        moral="Careful kindness helps more than hurried grumbling.",
    ),
}

NAMES = ["Mia", "Noah", "Lina", "Eli", "Tara", "Owen", "Nora", "Theo"]


# ---------------------------------------------------------------------------
# Story logic
# ---------------------------------------------------------------------------
def introduce(world: World, child: Entity, quest: Quest) -> None:
    world.say(
        f"{child.id} was a small, sleepy child who was ambidextrous, "
        f"so either hand could hold a book, open a drawer, or carry a little lamp."
    )
    world.say(
        f"Before bed, {child.id} had a gentle quest: to {quest.verb}."
    )


def setup_problem(world: World, child: Entity, quest: Quest) -> None:
    child.memes["pride"] += 1
    child.memes["worry"] += 1
    world.say(
        f"But {quest.conflict}. {child.id} frowned and said, "
        f"\"I can do it all by myself.\""
    )


def warn_and_search(world: World, child: Entity, quest: Quest) -> None:
    child.memes["stubbornness"] += 1
    child.memes["worry"] += 1
    child.meters["lost"] += 1
    world.say(
        f"{child.id} searched near the bed with one hand, then the other, "
        f"but the little star stayed hidden in the soft dark."
    )
    world.say(
        f"The more {child.id} hurried, the more mixed up everything felt."
    )


def gentle_help(world: World, child: Entity, quest: Quest) -> None:
    child.memes["kindness"] += 1
    child.memes["calm"] += 1
    child.memes["worry"] = 0.0
    world.say(
        f"Then {child.id}'s {world.facts['helper']} came in with a soft smile and said, "
        f"\"You do not have to do a quest alone.\""
    )
    world.say(
        f"{child.id} took a breath, nodded, and used both hands the careful way: "
        f"one hand moved the pillow, and the other checked under the blanket."
    )


def resolve(world: World, child: Entity, quest: Quest) -> None:
    child.meters["found"] += 1
    child.memes["joy"] += 1
    world.say(
        f"There, tucked beside the pillow, was {quest.item_phrase}."
    )
    world.say(
        f"{child.id} held it up with one hand and smiled with the other, "
        f"feeling warm and brave and very sleepy."
    )
    world.say(
        f"At last, the room felt calm again, and the bedtime quest was done."
    )


def tell(params: StoryParams) -> World:
    world = World(SETTINGS[params.place])
    quest = QUESTS[params.quest]
    child = world.add(Entity(
        id=params.name,
        kind="character",
        type="child",
        label=params.name,
        meters={"lost": 0.0, "found": 0.0, "tired": 0.0},
        memes={"pride": 0.0, "worry": 0.0, "kindness": 0.0, "calm": 0.0, "joy": 0.0, "stubbornness": 0.0},
    ))
    helper = world.add(Entity(
        id="Parent",
        kind="character",
        type="parent",
        label="parent",
    ))

    world.facts.update(child=child, helper=helper, quest=quest, setting=world.setting)

    introduce(world, child, quest)
    world.para()
    setup_problem(world, child, quest)
    warn_and_search(world, child, quest)
    world.para()
    world.facts["helper"] = helper.label
    gentle_help(world, child, quest)
    resolve(world, child, quest)

    world.facts["resolved"] = True
    return world


# ---------------------------------------------------------------------------
# Q&A
# ---------------------------------------------------------------------------
def prompts(world: World) -> list[str]:
    f = world.facts
    child = f["child"]
    quest = f["quest"]
    return [
        f'Write a gentle bedtime story about an ambidextrous child named {child.id} '
        f'who must {quest.verb}.',
        f'Tell a cozy story where a child uses both hands and learns a moral value '
        f'while solving a small bedtime problem.',
        f'Write a simple story with the word "ambidextrous" that ends with a calm bedtime resolution.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child: Entity = f["child"]
    quest: Quest = f["quest"]
    return [
        QAItem(
            question=f"What kind of child is {child.id} in the story?",
            answer=f"{child.id} is ambidextrous, so both hands can help with little jobs and careful searching.",
        ),
        QAItem(
            question=f"What was {child.id}'s bedtime quest?",
            answer=f"{child.id}'s bedtime quest was to {quest.verb}.",
        ),
        QAItem(
            question=f"Why did the problem feel hard at first?",
            answer=f"It felt hard because {quest.conflict}, and {child.id} tried to solve everything too quickly.",
        ),
        QAItem(
            question=f"How did the story end?",
            answer=f"It ended happily when {child.id} accepted help, used both hands carefully, and found {quest.item_phrase}.",
        ),
        QAItem(
            question=f"What moral value did the story teach?",
            answer=quest.moral,
        ),
    ]


WORLD_KNOWLEDGE = [
    QAItem(
        question="What does ambidextrous mean?",
        answer="Ambidextrous means a person can use both the left hand and the right hand well.",
    ),
    QAItem(
        question="Why is bedtime often quiet?",
        answer="Bedtime is often quiet because people are getting ready to rest, listen softly, and fall asleep.",
    ),
    QAItem(
        question="What is a quest in a story?",
        answer="A quest is a little journey or task where someone tries to find, fix, or reach something important.",
    ),
    QAItem(
        question="What is a moral value?",
        answer="A moral value is a good way of living, like kindness, honesty, patience, or helping others.",
    ),
]


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
child(C) :- child_name(C).
ambidextrous(C) :- child(C), both_hands(C).
quest(Q) :- quest_name(Q).
problem(C,Q) :- child(C), quest(Q), rushes_alone(C,Q).
resolved(C,Q) :- child(C), quest(Q), accepts_help(C,Q), uses_both_hands(C,Q).
moral_value(kindness) :- resolved(C,Q).
"""

def asp_facts() -> str:
    import asp
    lines = []
    for name in NAMES:
        lines.append(asp.fact("child_name", name))
        lines.append(asp.fact("both_hands", name))
    for qid in QUESTS:
        lines.append(asp.fact("quest_name", qid))
    lines.append(asp.fact("moral", "kindness"))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show child/1.\n#show ambidextrous/1.\n#show quest/1.\n#show moral_value/1.\n"))
    shown = set(asp.atoms(model, "ambidextrous"))
    py = {(name,) for name in NAMES}
    if shown == py:
        print(f"OK: ASP matches Python for ambidextrous children ({len(py)} names).")
        return 0
    print("MISMATCH between ASP and Python.")
    print("ASP only:", sorted(shown - py))
    print("Python only:", sorted(py - shown))
    return 1


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Bedtime story world: an ambidextrous quest with a moral value.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--quest", choices=QUESTS)
    ap.add_argument("--name", choices=NAMES)
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
    place = args.place or rng.choice(list(SETTINGS))
    quest = args.quest or rng.choice(list(QUESTS))
    name = args.name or rng.choice(NAMES)
    return StoryParams(place=place, quest=quest, name=name)


def generation_qa(world: World) -> list[QAItem]:
    return [QAItem(question=p, answer="") for p in prompts(world)]


def generate(params: StoryParams) -> StorySample:
    world = tell(params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=prompts(world),
        story_qa=story_qa(world),
        world_qa=WORLD_KNOWLEDGE,
        world=world,
    )


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
        lines.append(f"  {e.id:8} ({e.type:8}) {' '.join(bits)}")
    return "\n".join(lines)


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world is not None:
        print(dump_trace(sample.world))
    if qa:
        print()
        print("== prompts ==")
        for i, p in enumerate(sample.prompts, 1):
            print(f"{i}. {p}")
        print("\n== story qa ==")
        for item in sample.story_qa:
            print(f"Q: {item.question}")
            print(f"A: {item.answer}")
        print("\n== world qa ==")
        for item in sample.world_qa:
            print(f"Q: {item.question}")
            print(f"A: {item.answer}")


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show ambidextrous/1.\n#show quest/1.\n#show moral_value/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        model = asp.one_model(asp_program("#show ambidextrous/1.\n#show quest/1.\n#show moral_value/1."))
        print("ambidextrous:", sorted(set(asp.atoms(model, "ambidextrous"))))
        print("quest:", sorted(set(asp.atoms(model, "quest"))))
        print("moral_value:", sorted(set(asp.atoms(model, "moral_value"))))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)

    samples: list[StorySample] = []
    if args.all:
        for place in SETTINGS:
            for quest in QUESTS:
                params = StoryParams(place=place, quest=quest, name=NAMES[0])
                samples.append(generate(params))
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
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
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()

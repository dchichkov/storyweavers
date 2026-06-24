#!/usr/bin/env python3
"""
storyworlds/worlds/stretch_renew_lunch_rhyme_heartwarming.py
============================================================

A small heartwarming storyworld about a child who loves to stretch, a parent
who wants a fresh lunch, and a gentle renewal that turns a hiccup into a happy
meal.

Seed tale used to build the world:
---
Rhyme liked to stretch her arms after breakfast. One bright day, she and her
parent were getting lunch ready at the kitchen table. The old lunch tray was
wobbly, and the paper lid kept slipping. Rhyme wanted to rush and help, but her
parent worried the tray would tip and the lunch would get messy.

Rhyme frowned for a moment, then came up with a small rhyme to slow everything
down. She stretched carefully, helped tidy the tray, and renewed the lunch by
adding fresh fruit and a clean napkin. Soon the table felt warm and peaceful
again, and lunch was ready to share.

Causal state updates:
---
    stretch carefully        -> child.joy += 1, child.settled += 1
    rush near lunch tray      -> tray.tilt += 1, lunch.spill_risk += 1
    tidy and renew lunch      -> tray.steady += 1, parent.relief += 1, lunch.fresh += 1
    rhyme spoken gently       -> child.settled += 1, parent.warmth += 1
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
    region: str = ""
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "mother", "woman", "grandmother"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "man", "grandfather"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str = "the kitchen"
    affords: set[str] = field(default_factory=lambda: {"stretch", "renew", "lunch"})


@dataclass
class Activity:
    id: str
    verb: str
    gerund: str
    rush: str
    keyword: str = "stretch"


@dataclass
class Prize:
    label: str
    phrase: str
    type: str
    region: str
    plural: bool = False
    genders: set[str] = field(default_factory=lambda: {"girl", "boy"})


@dataclass
class Gear:
    id: str
    label: str
    prep: str
    tail: str
    guards: set[str]
    covers: set[str]


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.fired: set[tuple] = set()

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
        clone.paragraphs = [[]]
        clone.facts = dict(self.facts)
        clone.fired = set(self.fired)
        return clone


def q(s: str) -> str:
    return f'"{s}"'


def aspire(world: World, narrate: bool = True) -> list[str]:
    out: list[str] = []
    child = world.get("Rhyme")
    parent = world.get("Parent")
    lunch = world.get("Lunch")

    if child.memes.get("stretch", 0) >= THRESHOLD and "stretch" not in world.fired:
        world.fired.add(("stretch",))
        child.memes["joy"] = child.memes.get("joy", 0) + 1
        child.memes["settled"] = child.memes.get("settled", 0) + 1
        out.append("Rhyme stretched carefully, and her body felt calm and ready.")

    if child.memes.get("rush", 0) >= THRESHOLD and lunch.meters.get("spill_risk", 0) >= THRESHOLD:
        if ("warn",) not in world.fired:
            world.fired.add(("warn",))
            out.append("Her parent gently warned that rushing near lunch could make a mess.")

    if child.memes.get("rhyme", 0) >= THRESHOLD and "rhyme" not in world.fired:
        world.fired.add(("rhyme",))
        parent.memes["warmth"] = parent.memes.get("warmth", 0) + 1
        child.memes["settled"] = child.memes.get("settled", 0) + 1
        out.append("A small rhyme slowed the room down and made everyone smile.")

    if child.memes.get("renew", 0) >= THRESHOLD and "renew" not in world.fired:
        world.fired.add(("renew",))
        lunch.meters["fresh"] = lunch.meters.get("fresh", 0) + 1
        lunch.meters["spill_risk"] = 0
        parent.memes["relief"] = parent.memes.get("relief", 0) + 1
        out.append("Together they renewed lunch with fresh fruit and a clean napkin.")

    if narrate:
        for s in out:
            world.say(s)
    return out


def predict_mess(world: World) -> bool:
    sim = world.copy()
    sim.get("Rhyme").memes["rush"] = 1
    sim.get("Lunch").meters["spill_risk"] = 1
    aspire(sim, narrate=False)
    return sim.get("Lunch").meters.get("fresh", 0) < THRESHOLD


def tell() -> World:
    world = World(Setting())
    child = world.add(Entity(id="Rhyme", kind="character", type="girl"))
    parent = world.add(Entity(id="Parent", kind="character", type="mother", label="mom"))
    lunch = world.add(Entity(
        id="Lunch",
        kind="thing",
        type="meal",
        label="lunch tray",
        phrase="a tidy lunch tray with soup, bread, and fruit",
        region="table",
    ))

    child.memes["stretch"] = 1
    child.memes["rhyme"] = 1
    child.memes["renew"] = 1
    child.memes["rush"] = 1

    lunch.meters["spill_risk"] = 1

    world.say("Rhyme was a cheerful girl who loved to stretch after a busy morning.")
    world.say("In the kitchen, her parent was setting up lunch, and the little table looked ready for something warm.")
    world.say("Rhyme wanted to help right away, but the lunch tray wobbled when she hurried too fast.")

    world.para()
    if predict_mess(world):
        world.say('"If we rush," her mom said softly, "lunch might tip over and get messy."')
    world.say('Rhyme paused, took a gentle stretch, and said a tiny rhyme to slow her feet down.')
    aspire(world)

    world.para()
    world.say("Then she helped her mom renew lunch with a clean napkin and fresh fruit on top.")
    aspire(world)
    world.say("Soon the kitchen felt warm and peaceful again, and Rhyme sat down happily beside her mom to share lunch.")

    world.facts.update(child=child, parent=parent, lunch=lunch)
    return world


SETTINGS = {"kitchen": Setting()}
ACTIVITIES = {
    "stretch": Activity(
        id="stretch",
        verb="stretch carefully",
        gerund="stretching carefully",
        rush="rush around the table",
        keyword="stretch",
    ),
    "renew": Activity(
        id="renew",
        verb="renew lunch",
        gerund="renewing lunch",
        rush="hurry to fix lunch",
        keyword="renew",
    ),
    "lunch": Activity(
        id="lunch",
        verb="share lunch",
        gerund="sharing lunch",
        rush="rush into lunch",
        keyword="lunch",
    ),
}
PRIZES = {
    "lunch": Prize(
        label="lunch tray",
        phrase="a tidy lunch tray with soup, bread, and fruit",
        type="tray",
        region="table",
    )
}
GEAR = [
    Gear(
        id="napkin",
        label="a clean napkin",
        prep="lay out a clean napkin first",
        tail="set down the tray on the clean napkin",
        guards={"spill"},
        covers={"table"},
    ),
    Gear(
        id="fruit",
        label="fresh fruit",
        prep="add fresh fruit first",
        tail="served the fresh fruit beside the tray",
        guards={"spill"},
        covers={"table"},
    ),
]

GIRL_NAMES = ["Rhyme", "Mina", "Lila", "Nora"]
BOY_NAMES = ["Eli", "Noah", "Theo", "Ben"]
TRAITS = ["cheerful", "gentle", "curious", "bright"]


@dataclass
class StoryParams:
    place: str = "kitchen"
    activity: str = "stretch"
    prize: str = "lunch"
    name: str = "Rhyme"
    gender: str = "girl"
    parent: str = "mother"
    trait: str = "gentle"
    seed: Optional[int] = None


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Heartwarming storyworld about stretch, renew, and lunch.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--activity", choices=ACTIVITIES)
    ap.add_argument("--prize", choices=PRIZES)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--parent", choices=["mother", "father"])
    ap.add_argument("--name")
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
    if args.gender and args.gender != "girl":
        raise StoryError("This world is tuned for Rhyme, a girl who loves stretching and lunch.")
    return StoryParams(
        place="kitchen",
        activity="stretch",
        prize="lunch",
        name=args.name or "Rhyme",
        gender="girl",
        parent=args.parent or "mother",
        trait=args.trait if hasattr(args, "trait") and args.trait else rng.choice(TRAITS),
    )


def generation_prompts(world: World) -> list[str]:
    return [
        'Write a heartwarming story about stretch, renew, and lunch with a tiny rhyme.',
        'Tell a gentle kitchen story where Rhyme helps renew lunch after a careful stretch.',
        'Write a child-friendly story that includes the words stretch, renew, and lunch.',
    ]


def story_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="Who is the story about?",
            answer="The story is about Rhyme, a cheerful girl who loves to stretch and help with lunch.",
        ),
        QAItem(
            question="Why did Rhyme pause instead of rushing?",
            answer="She paused because her mom worried the wobbly lunch tray could tip if they rushed near it.",
        ),
        QAItem(
            question="How did the lunch turn out at the end?",
            answer="Rhyme and her mom renewed lunch with fresh fruit and a clean napkin, so it became neat and ready to share.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does stretch mean?",
            answer="To stretch means to reach or pull your body gently so your muscles feel loose and ready.",
        ),
        QAItem(
            question="What does renew mean?",
            answer="To renew something means to make it feel fresh, new, or ready again.",
        ),
        QAItem(
            question="What is lunch?",
            answer="Lunch is a meal people often eat in the middle of the day.",
        ),
    ]


def generate(params: StoryParams) -> StorySample:
    world = tell()
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


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
        bits = []
        if e.meters:
            bits.append(f"meters={dict(e.meters)}")
        if e.memes:
            bits.append(f"memes={dict(e.memes)}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    return "\n".join(lines)


ASP_RULES = r"""
stretch_story :- stretch, lunch, renew.
"""


def asp_facts() -> str:
    import asp
    return "\n".join([
        asp.fact("setting", "kitchen"),
        asp.fact("activity", "stretch"),
        asp.fact("activity", "renew"),
        asp.fact("activity", "lunch"),
        asp.fact("prize", "lunch"),
    ])


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    return 0


CURATED = [StoryParams()]


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
        print(asp_program("#show stretch_story/0."))
        return
    if args.verify:
        sys.exit(asp_verify())

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
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()

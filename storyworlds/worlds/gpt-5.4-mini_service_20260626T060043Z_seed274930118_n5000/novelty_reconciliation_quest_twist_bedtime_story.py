#!/usr/bin/env python3
"""
A tiny bedtime-story world about a child, a small quest, a surprising twist,
and a gentle reconciliation.

Premise:
A child wants a soothing bedtime object to help with sleep. A small quest
through the bedroom turns up an unexpected twist: the object is not where it
was expected, and someone in the room feels worried or left out. The resolution
comes through sharing, apology, and a calm new bedtime arrangement.

This world is designed to feel like a classical TinyStories-style simulation:
state changes drive the prose, and the story turns on a concrete, child-sized
problem and fix.
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

@dataclass
class Entity:
    id: str
    kind: str = "thing"  # character | thing
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    held_by: Optional[str] = None
    location: str = ""
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "mother", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Place:
    name: str
    cozy: bool = True
    affords: set[str] = field(default_factory=set)


@dataclass
class QuestItem:
    label: str
    phrase: str
    location: str
    found_in: str
    helps_with: str
    novelty: str


@dataclass
class Twist:
    id: str
    label: str
    reveal: str
    effect: str


@dataclass
class World:
    place: Place
    entities: dict[str, Entity] = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    facts: dict = field(default_factory=dict)
    fired: set[tuple] = field(default_factory=set)

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


# ---------------------------------------------------------------------------
# Parameters and registries
# ---------------------------------------------------------------------------

@dataclass
class StoryParams:
    place: str
    child_name: str
    child_type: str
    parent_type: str
    item: str
    twist: str
    seed: Optional[int] = None


PLACES = {
    "bedroom": Place(name="the bedroom", cozy=True, affords={"search", "share", "sleep"}),
    "nursery": Place(name="the nursery", cozy=True, affords={"search", "share", "sleep"}),
    "attic_room": Place(name="the attic room", cozy=True, affords={"search", "share", "sleep"}),
}

CHILD_NAMES = ["Mia", "Leo", "Nora", "Ben", "Ava", "Theo", "Lily", "Sam"]
CHILD_TYPES = ["girl", "boy"]
PARENT_TYPES = ["mother", "father"]

QUEST_ITEMS = {
    "moon_book": QuestItem(
        label="moon book",
        phrase="a tiny moon book with silver stars",
        location="under the pillow",
        found_in="the pillow nest",
        helps_with="sleep",
        novelty="novelty",
    ),
    "soft_bell": QuestItem(
        label="soft bell",
        phrase="a soft bell with a blue ribbon",
        location="inside the toy basket",
        found_in="the toy basket",
        helps_with="calm",
        novelty="novelty",
    ),
    "sleep_mouse": QuestItem(
        label="sleep mouse",
        phrase="a tiny mouse toy with a knitted scarf",
        location="behind the curtains",
        found_in="behind the curtains",
        helps_with="sleep",
        novelty="novelty",
    ),
}

TWISTS = {
    "borrowed": Twist(
        id="borrowed",
        label="borrowed",
        reveal="It had been borrowed by the parent for a minute and set somewhere safe.",
        effect="a soft misunderstanding",
    ),
    "duplicate": Twist(
        id="duplicate",
        label="duplicate",
        reveal="There were two nearly matching ones, and the child had picked the wrong one at first.",
        effect="a surprising mix-up",
    ),
    "hidden_note": Twist(
        id="hidden_note",
        label="hidden note",
        reveal="A little note was tucked inside, asking the child to share it at bedtime.",
        effect="a small surprise",
    ),
}

GENTLE_TRAITS = ["sleepy", "curious", "gentle", "patient", "quiet"]


# ---------------------------------------------------------------------------
# Utility
# ---------------------------------------------------------------------------

THRESHOLD = 1.0


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for place in PLACES:
        for item in QUEST_ITEMS:
            for twist in TWISTS:
                combos.append((place, item, twist))
    return combos


def place_detail(place: Place, item: QuestItem) -> str:
    if place.name == "the bedroom":
        return "The lamp glowed low, and the blankets made the room feel like a nest."
    if place.name == "the nursery":
        return "The curtains were soft, and the room smelled like clean sheets."
    return "The little room was quiet, with shadows tucked neatly into the corners."


def ask_string(item: QuestItem) -> str:
    return f"the {item.label}"


# ---------------------------------------------------------------------------
# Story engine
# ---------------------------------------------------------------------------

def build_world(params: StoryParams) -> World:
    world = World(place=PLACES[params.place])
    child = world.add(Entity(
        id=params.child_name,
        kind="character",
        type=params.child_type,
        location=params.place,
        meters={"tired": 1.0},
        memes={"want": 1.0, "hope": 1.0},
    ))
    parent = world.add(Entity(
        id="Parent",
        kind="character",
        type=params.parent_type,
        location=params.place,
        meters={"calm": 1.0},
        memes={"care": 1.0},
    ))
    item = QUEST_ITEMS[params.item]
    quest_item = world.add(Entity(
        id=item.label,
        kind="thing",
        type="thing",
        label=item.label,
        phrase=item.phrase,
        owner=child.id,
        location=item.location,
        meters={"special": 1.0},
        memes={"novelty": 1.0},
    ))
    twist = TWISTS[params.twist]
    world.facts.update(
        child=child,
        parent=parent,
        item=quest_item,
        item_cfg=item,
        twist=twist,
        place=world.place,
        params=params,
    )
    return world


def tell(world: World) -> None:
    f = world.facts
    child: Entity = f["child"]
    parent: Entity = f["parent"]
    item: Entity = f["item"]
    item_cfg: QuestItem = f["item_cfg"]
    twist: Twist = f["twist"]

    world.say(
        f"{child.id} was a {random.choice(GENTLE_TRAITS)} {child.type} who loved a small bedtime novelty. "
        f"{child.pronoun('subject').capitalize()} had asked for {item.label} every night, because it helped the room feel safe."
    )
    world.say(
        f"That evening, the lamp stayed low and {world.place.name} felt cozy. "
        f"{child.id} looked at the blankets and whispered, “I want {ask_string(item_cfg)} before sleep.”"
    )

    world.para()
    child.memes["quest"] = 1.0
    world.say(
        f"{child.id} began a tiny quest: first the pillow nest, then {item_cfg.found_in}, then the toy basket. "
        f"{child.pronoun('subject').capitalize()} searched carefully, because bedtime felt too big without {item.label}."
    )
    if item.location == "under the pillow":
        world.say(
            f"The search paused at the pillow, where the sheets were rumpled and soft."
        )
    elif item.location == "inside the toy basket":
        world.say(
            f"The toy basket rattled a little as {child.id} lifted each stuffed animal aside."
        )
    else:
        world.say(
            f"The curtains swayed when {child.id} peered behind them, as if the room were holding its breath."
        )

    world.para()
    child.memes["surprise"] = 1.0
    parent.memes["worry"] = 1.0
    world.say(
        f"Then came the twist: {twist.reveal} "
        f"{child.id} blinked, and {parent.pronoun('subject')} knelt down to explain the {twist.effect}."
    )
    if twist.id == "borrowed":
        world.say(
            f"{parent.id} had moved the item earlier so it would not get lost in the blankets."
        )
    elif twist.id == "duplicate":
        world.say(
            f"There were two tiny versions, and one had been sitting in plain sight the whole time."
        )
    else:
        world.say(
            f"Inside the folded note, there was a gentle message: “Let’s use it together tonight.”"
        )

    world.para()
    child.memes["sad"] = 1.0
    parent.memes["regret"] = 1.0
    world.say(
        f"{child.id} felt a small lump in {child.pronoun('possessive')} throat. "
        f"{child.pronoun('subject').capitalize()} had wanted the bedtime comfort all to {child.pronoun('object')}self."
    )
    world.say(
        f"{parent.id} smiled and said sorry for the confusion, then offered a warm hug and a new plan."
    )
    world.say(
        f"They agreed to place {item.label} on the bedside table, so it could be shared, seen, and found again easily."
    )

    world.para()
    child.memes["joy"] = 1.0
    child.memes["reconciled"] = 1.0
    parent.memes["reconciled"] = 1.0
    world.say(
        f"{child.id} hugged {parent.pronoun('object')}, and the room grew calm again. "
        f"Soon {child.id} was tucked under the blanket with the little novelty nearby, "
        f"and the bedtime quest ended in a soft, happy reconciliation."
    )

    world.facts["resolved"] = True


# ---------------------------------------------------------------------------
# Q&A
# ---------------------------------------------------------------------------

def generation_prompts(world: World) -> list[str]:
    f = world.facts
    child: Entity = f["child"]
    item_cfg: QuestItem = f["item_cfg"]
    twist: Twist = f["twist"]
    return [
        f'Write a bedtime story for a small child about a quest for "{item_cfg.label}", with a gentle twist and reconciliation.',
        f"Tell a cozy story where {child.id} searches the bedroom for {item_cfg.phrase} and learns a surprising bedtime lesson.",
        f"Write a short bedtime tale about novelty, a lost bedtime object, and a family making up after a mix-up.",
        f'Create a child-friendly story with the words "quest", "twist", and "reconciliation" near a sleepy ending.',
        f'Write a gentle story in which "{twist.label}" changes the search for {item_cfg.label} before sleep.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child: Entity = f["child"]
    parent: Entity = f["parent"]
    item: Entity = f["item"]
    item_cfg: QuestItem = f["item_cfg"]
    twist: Twist = f["twist"]

    return [
        QAItem(
            question=f"What did {child.id} want to find before bedtime?",
            answer=f"{child.id} wanted to find {item.label}, the little bedtime novelty that helped {child.pronoun('object')} feel calm.",
        ),
        QAItem(
            question=f"What kind of search did {child.id} go on in {world.place.name}?",
            answer=f"{child.id} went on a tiny quest through {world.place.name}, searching carefully in the pillow nest, the toy basket, and other cozy spots.",
        ),
        QAItem(
            question=f"What was the twist in the story?",
            answer=f"The twist was that {twist.reveal.lower()}",
        ),
        QAItem(
            question=f"How did {child.id} and {parent.id} fix the problem?",
            answer=f"They talked kindly, said sorry, and agreed to keep {item.label} on the bedside table so it would be easy to share and find.",
        ),
        QAItem(
            question=f"How did the story end?",
            answer=f"It ended with {child.id} cuddled under the blanket, {parent.id} nearby, and the room quiet after their reconciliation.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a quest?",
            answer="A quest is a search for something important, often with a purpose and a little adventure along the way.",
        ),
        QAItem(
            question="What is a twist in a story?",
            answer="A twist is a surprising change that makes the story turn in a new direction.",
        ),
        QAItem(
            question="What is reconciliation?",
            answer="Reconciliation means making peace after a problem, so people can feel calm and friendly again.",
        ),
        QAItem(
            question="Why are bedtime stories usually gentle?",
            answer="Bedtime stories are usually gentle because they help children feel safe, calm, and ready to sleep.",
        ),
        QAItem(
            question="What does novelty mean?",
            answer="Novelty means something new, unusual, or especially interesting because it feels fresh and different.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== (2) Story questions ==")
    for qa in sample.story_qa:
        lines.append(f"Q: {qa.question}")
        lines.append(f"A: {qa.answer}")
    lines.append("")
    lines.append("== (3) World-knowledge questions ==")
    for qa in sample.world_qa:
        lines.append(f"Q: {qa.question}")
        lines.append(f"A: {qa.answer}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------

ASP_RULES = r"""
quest_item(Item) :- item(Item).
twist(T) :- twist_id(T).
at_risk(Item) :- item(Item).
compatible_story(Place, Item, Twist) :- place(Place), quest_item(Item), twist(Twist), at_risk(Item).
"""

def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for p in PLACES:
        lines.append(asp.fact("place", p))
    for i in QUEST_ITEMS:
        lines.append(asp.fact("item", i))
    for t in TWISTS:
        lines.append(asp.fact("twist_id", t))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show compatible_story/3."))
    return sorted(set(asp.atoms(model, "compatible_story")))


def asp_verify() -> int:
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    if py - cl:
        print("  only in python:", sorted(py - cl))
    if cl - py:
        print("  only in clingo:", sorted(cl - py))
    return 1


# ---------------------------------------------------------------------------
# Generation
# ---------------------------------------------------------------------------

def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    combos = valid_combos()
    if args.place:
        combos = [c for c in combos if c[0] == args.place]
    if args.item:
        combos = [c for c in combos if c[1] == args.item]
    if args.twist:
        combos = [c for c in combos if c[2] == args.twist]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    place, item, twist = rng.choice(sorted(combos))
    name = args.name or rng.choice(CHILD_NAMES)
    child_type = args.child_type or rng.choice(CHILD_TYPES)
    parent_type = args.parent_type or rng.choice(PARENT_TYPES)

    if args.name and not args.name.strip():
        raise StoryError("Child name cannot be blank.")

    return StoryParams(
        place=place,
        child_name=name,
        child_type=child_type,
        parent_type=parent_type,
        item=item,
        twist=twist,
    )


def generate(params: StoryParams) -> StorySample:
    world = build_world(params)
    tell(world)
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
        print()
        print("--- world trace ---")
        for e in sample.world.entities.values():
            print(f"{e.id}: kind={e.kind} type={e.type} location={e.location} meters={e.meters} memes={e.memes}")
    if qa:
        print()
        print(format_qa(sample))


def dump_json(samples: list[StorySample]) -> str:
    if len(samples) == 1:
        return samples[0].to_json()
    return json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False)


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Bedtime story world: quest, twist, reconciliation.")
    ap.add_argument("--place", choices=sorted(PLACES))
    ap.add_argument("--item", choices=sorted(QUEST_ITEMS))
    ap.add_argument("--twist", choices=sorted(TWISTS))
    ap.add_argument("--name")
    ap.add_argument("--child-type", choices=CHILD_TYPES)
    ap.add_argument("--parent-type", choices=PARENT_TYPES)
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


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show compatible_story/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        triples = asp_valid_combos()
        print(f"{len(triples)} compatible stories:\n")
        for t in triples:
            print(" ".join(t))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)

    samples: list[StorySample] = []
    if args.all:
        for i, (place, item, twist) in enumerate(valid_combos()):
            params = StoryParams(
                place=place,
                child_name=CHILD_NAMES[i % len(CHILD_NAMES)],
                child_type=CHILD_TYPES[i % len(CHILD_TYPES)],
                parent_type=PARENT_TYPES[i % len(PARENT_TYPES)],
                item=item,
                twist=twist,
                seed=base_seed + i,
            )
            samples.append(generate(params))
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
        print(dump_json(samples))
        return

    for i, sample in enumerate(samples):
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.child_name}: {p.item} / {p.twist} at {p.place}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()

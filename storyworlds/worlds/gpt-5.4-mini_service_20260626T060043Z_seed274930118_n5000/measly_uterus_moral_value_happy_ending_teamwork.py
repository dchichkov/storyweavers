#!/usr/bin/env python3
"""
A small bedtime-story world about a child, a misplaced word, a measly supply,
and a happy ending reached through teamwork and kindness.

This world keeps the simulation tiny and constraint-checked:
- a child wants to keep or fix something
- a parent or sibling notices the problem
- a measly amount of help is not enough at first
- teamwork turns the ending warm and safe

The required seed words "measly" and "uterus" are included in the world
vocabulary and can surface in the story and QA. The style is aimed at
bedtime-story prose with a gentle moral value and a happy ending.
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
# World entities
# ---------------------------------------------------------------------------
@dataclass
class Entity:
    id: str
    kind: str = "thing"  # "character" | "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    carried_by: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)
    plural: bool = False

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
    id: str
    label: str
    quiet: bool = True
    affords: set[str] = field(default_factory=set)


@dataclass
class Item:
    id: str
    label: str
    phrase: str
    risk: str
    region: str
    fixable_by: set[str] = field(default_factory=set)
    plural: bool = False


@dataclass
class Helper:
    id: str
    label: str
    action: str
    tail: str
    helps_with: set[str] = field(default_factory=set)


@dataclass
class World:
    place: Place
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


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------
PLACES = {
    "bedroom": Place(id="bedroom", label="the bedroom", quiet=True, affords={"tidy", "read"}),
    "library": Place(id="library", label="the little library corner", quiet=True, affords={"tidy", "read"}),
    "kitchen": Place(id="kitchen", label="the kitchen table", quiet=True, affords={"tidy", "read"}),
}

ITEMS = {
    "story_card": Item(
        id="story_card",
        label="word card",
        phrase="a word card with the word uterus written on it",
        risk="lost",
        region="table",
        fixable_by={"share"},
    ),
    "glitter_box": Item(
        id="glitter_box",
        label="glitter box",
        phrase="a glitter box with a measly sprinkle of sparkles left inside",
        risk="low",
        region="table",
        fixable_by={"share"},
    ),
    "torn_book": Item(
        id="torn_book",
        label="picture book",
        phrase="a picture book with one torn page",
        risk="torn",
        region="shelf",
        fixable_by={"tape"},
    ),
}

HELPERS = {
    "tape": Helper(
        id="tape",
        label="tape",
        action="gently tape the torn page",
        tail="soon the book looked neat again",
        helps_with={"torn"},
    ),
    "share": Helper(
        id="share",
        label="shared hands",
        action="work together and sort the pieces",
        tail="together they made the corner tidy",
        helps_with={"lost", "low"},
    ),
}

NAMES_GIRL = ["Mina", "Luna", "Nora", "Elsie", "Maya"]
NAMES_BOY = ["Theo", "Owen", "Finn", "Leo", "Ari"]
TRAITS = ["kind", "gentle", "curious", "patient", "thoughtful"]


# ---------------------------------------------------------------------------
# Params
# ---------------------------------------------------------------------------
@dataclass
class StoryParams:
    place: str
    item: str
    helper: str
    name: str
    gender: str
    trait: str
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# Reasonableness gate
# ---------------------------------------------------------------------------
def valid_combo(place: str, item: str, helper: str) -> bool:
    return item in ITEMS and helper in HELPERS and place in PLACES and ITEMS[item].risk in HELPERS[helper].helps_with


def valid_combos() -> list[tuple[str, str, str]]:
    out = []
    for p in PLACES:
        for i in ITEMS:
            for h in HELPERS:
                if valid_combo(p, i, h):
                    out.append((p, i, h))
    return out


def explain_rejection(place: str, item: str, helper: str) -> str:
    if place not in PLACES:
        return "(No story: that place is not part of this bedtime world.)"
    if item not in ITEMS:
        return "(No story: that item is not part of this bedtime world.)"
    if helper not in HELPERS:
        return "(No story: that helper is not part of this bedtime world.)"
    return (
        f"(No story: {HELPERS[helper].label} cannot help with {ITEMS[item].risk} problems, "
        f"so this would not make a gentle, believable bedtime ending.)"
    )


# ---------------------------------------------------------------------------
# Story simulation
# ---------------------------------------------------------------------------
def build_world(params: StoryParams) -> World:
    world = World(place=PLACES[params.place])
    hero = world.add(Entity(id=params.name, kind="character", type=params.gender, meters={}, memes={"hope": 0.0, "worry": 0.0, "joy": 0.0}))
    parent = world.add(Entity(id="Parent", kind="character", type="mother", label="mom"))
    item = world.add(Entity(
        id=params.item,
        type="thing",
        label=ITEMS[params.item].label,
        phrase=ITEMS[params.item].phrase,
        caretaker=parent.id,
    ))
    helper = HELPERS[params.helper]

    world.facts.update(hero=hero, parent=parent, item=item, helper=helper, place=world.place, params=params)

    # Act 1
    world.say(f"{hero.id} was a {params.trait} little {params.gender} who liked quiet bedtime chores.")
    world.say(f"On the table, there was {item.phrase}.")
    if params.item == "story_card":
        world.say(f"{hero.id} kept pointing at the long new word. It said uterus, and it looked funny and important.")
    else:
        world.say(f"Nearby, there was also a measly little sprinkle of glitter that hardly seemed enough for a full craft.")

    # Act 2
    world.para()
    hero.memes["worry"] += 1
    world.say(f"{hero.id} wanted to keep {item.it()} nearby, but it needed care before bed.")
    world.say(f"{parent.pronoun().capitalize()} smiled and said they would need teamwork.")

    # A tiny emotional turn: measly help is not enough alone.
    if params.item == "glitter_box":
        world.say("One small pinch of sparkle could not finish the picture by itself.")
        world.say(f"{hero.id} felt a measly bit disappointed, then decided to help anyway.")
    elif params.item == "story_card":
        world.say(f"{hero.id} almost tucked the word card under the pillow, but {parent.pronoun('possessive')} kind voice reminded {hero.pronoun('object')} that borrowed things should go home.")
    else:
        world.say(f"The torn page could not be wished whole again; it needed careful hands.")

    # Act 3
    world.para()
    hero.memes["joy"] += 1
    world.say(f"Together, they used {helper.label} to {helper.action}.")
    world.say(f"{helper.tail}.")
    if params.item == "story_card":
        world.say(f"They put the card back where science words belonged, and the bedroom felt calm again.")
    elif params.item == "glitter_box":
        world.say(f"They shared the last measly sparkles wisely, and the picture finally looked bright.")
    else:
        world.say(f"They closed the book with a soft tap, and the page was safe for tomorrow.")

    world.say(f"{hero.id} climbed into bed feeling proud, because kindness had helped the little problem end well.")
    world.say("And in the cozy quiet, everyone could rest with a happy ending.")

    return world


# ---------------------------------------------------------------------------
# Q&A
# ---------------------------------------------------------------------------
def generation_prompts(world: World) -> list[str]:
    f = world.facts
    params: StoryParams = f["params"]
    item = f["item"]
    return [
        f'Write a bedtime story for a small child about a {params.trait} helper, '
        f'a {item.label}, and a happy ending reached by teamwork.',
        f'Tell a gentle story where the word "{item.label}" matters, '
        f'and where the word "measly" appears in a calm, child-friendly way.',
        f'Write a cozy story with a moral value about sharing, fixing, '
        f'and working together before sleep.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero: Entity = f["hero"]
    parent: Entity = f["parent"]
    item: Entity = f["item"]
    helper: Helper = f["helper"]
    params: StoryParams = f["params"]

    return [
        QAItem(
            question=f"What was {hero.id} like in the story?",
            answer=f"{hero.id} was a {params.trait} little {params.gender} who liked quiet bedtime chores.",
        ),
        QAItem(
            question=f"What important thing was on the table?",
            answer=f"There was {item.phrase}. The story also included the word uterus, which was written on the card.",
        ),
        QAItem(
            question=f"How did {hero.id} and {parent.label} solve the problem?",
            answer=f"They used {helper.label} to {helper.action}, and then they finished with teamwork.",
        ),
        QAItem(
            question=f"Why was the helper useful?",
            answer=f"{helper.label.capitalize()} was useful because it could help with the problem type in the story and make a safe, tidy ending possible.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does teamwork mean?",
            answer="Teamwork means people help each other do a job together.",
        ),
        QAItem(
            question="What is a moral value?",
            answer="A moral value is a kind idea about how to behave, like being honest, helpful, or gentle.",
        ),
        QAItem(
            question="What is a happy ending?",
            answer="A happy ending is when a problem gets solved and the story ends in a warm, good way.",
        ),
    ]


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
% A story is valid when the chosen helper can handle the item's problem.
valid_story(P, I, H) :- place(P), item(I), helper(H),
                        risk(I, R), helps(H, R).

% A vivid bedtime ending should include teamwork if a helper is chosen.
teamwork_story(P, I, H) :- valid_story(P, I, H), place(P), item(I), helper(H).
"""


def asp_facts() -> str:
    import storyworlds.asp as asp
    lines = []
    for pid in PLACES:
        lines.append(asp.fact("place", pid))
    for iid, item in ITEMS.items():
        lines.append(asp.fact("item", iid))
        lines.append(asp.fact("risk", iid, item.risk))
    for hid, helper in HELPERS.items():
        lines.append(asp.fact("helper", hid))
        for r in sorted(helper.helps_with):
            lines.append(asp.fact("helps", hid, r))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple[str, str, str]]:
    import storyworlds.asp as asp
    model = asp.one_model(asp_program("#show valid_story/3."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: ASP matches Python gate ({len(py)} combos).")
        return 0
    print("MISMATCH between ASP and Python:")
    if py - cl:
        print("  only in python:", sorted(py - cl))
    if cl - py:
        print("  only in asp:", sorted(cl - py))
    return 1


# ---------------------------------------------------------------------------
# Story API
# ---------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Bedtime story world with teamwork, moral value, and a happy ending.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--item", choices=ITEMS)
    ap.add_argument("--helper", choices=HELPERS)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--name")
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
    combos = valid_combos()
    if args.place or args.item or args.helper:
        combos = [
            c for c in combos
            if (args.place is None or c[0] == args.place)
            and (args.item is None or c[1] == args.item)
            and (args.helper is None or c[2] == args.helper)
        ]
    if not combos:
        raise StoryError("(No valid bedtime-story combination matches those options.)")
    place, item, helper = rng.choice(sorted(combos))
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(NAMES_GIRL if gender == "girl" else NAMES_BOY)
    trait = args.trait or rng.choice(TRAITS)
    if args.gender and args.name is None:
        # name list already matched by gender; no further action needed
        pass
    return StoryParams(place=place, item=item, helper=helper, name=name, gender=gender, trait=trait)


def generate(params: StoryParams) -> StorySample:
    world = build_world(params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for e in world.entities.values():
        bits = []
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        lines.append(f"{e.id}: {e.kind}/{e.type} {' '.join(bits)}")
    return "\n".join(lines)


def format_qa(sample: StorySample) -> str:
    lines = ["== generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== story qa ==")
    for q in sample.story_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    lines.append("")
    lines.append("== world qa ==")
    for q in sample.world_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    return "\n".join(lines)


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
        raise SystemExit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (place, item, helper) combos:")
        for p, i, h in combos:
            print(f"  {p:10} {i:12} {h}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)

    samples: list[StorySample] = []
    if args.all:
        curated = [
            StoryParams(place="bedroom", item="story_card", helper="share", name="Mina", gender="girl", trait="curious"),
            StoryParams(place="library", item="torn_book", helper="tape", name="Leo", gender="boy", trait="gentle"),
            StoryParams(place="kitchen", item="glitter_box", helper="share", name="Nora", gender="girl", trait="thoughtful"),
        ]
        samples = [generate(p) for p in curated]
    else:
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

    for idx, sample in enumerate(samples):
        header = f"### variant {idx + 1}" if len(samples) > 1 and not args.all else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if idx < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()

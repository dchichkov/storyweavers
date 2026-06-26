#!/usr/bin/env python3
"""
A small slice-of-life story world about a child at home, a missing item,
a school flunk, and a kind sharing moment that helps things feel better.

Seed words: residence, flunk, rummage
Features: Kindness, Moral Value, Sharing
Style: Slice of Life
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


@dataclass
class Person:
    id: str
    role: str
    label: str
    pronoun_subject: str
    pronoun_object: str
    pronoun_possessive: str
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def say(self, text: str) -> str:
        return text


@dataclass
class Item:
    id: str
    label: str
    owner: str
    location: str
    found: bool = False


@dataclass
class Place:
    id: str
    label: str
    kind: str = "residence"


@dataclass
class StoryParams:
    residence: str
    child_name: str
    helper_name: str
    school_item: str
    seed: Optional[int] = None


RESIDENCES = {
    "apartment": Place(id="apartment", label="the apartment"),
    "house": Place(id="house", label="the house"),
    "duplex": Place(id="duplex", label="the duplex"),
}

ITEMS = {
    "library_book": "library book",
    "math_sheet": "math worksheet",
    "music_note": "music sheet",
    "reading_card": "reading card",
}

CHILD_NAMES = ["Mina", "Eli", "Nora", "Theo", "June", "Iris", "Ben", "Luna"]
HELPER_NAMES = ["Mom", "Dad", "Auntie", "Grandma", "Uncle", "Older Sister"]
PRONOUNS = {
    "Mina": ("she", "her", "her"),
    "Eli": ("he", "him", "his"),
    "Nora": ("she", "her", "her"),
    "Theo": ("he", "him", "his"),
    "June": ("she", "her", "her"),
    "Iris": ("she", "her", "her"),
    "Ben": ("he", "him", "his"),
    "Luna": ("she", "her", "her"),
}

ASP_RULES = r"""
#show valid/3.

valid(R, C, I) :- residence(R), child(C), item(I).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for rid in RESIDENCES:
        lines.append(asp.fact("residence", rid))
    for name in CHILD_NAMES:
        lines.append(asp.fact("child", name))
    for item_id in ITEMS:
        lines.append(asp.fact("item", item_id))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Slice-of-life story world about a residence, a flunk, and rummage.")
    ap.add_argument("--residence", choices=RESIDENCES)
    ap.add_argument("--name", dest="child_name", choices=CHILD_NAMES)
    ap.add_argument("--helper", dest="helper_name", choices=HELPER_NAMES)
    ap.add_argument("--item", dest="school_item", choices=ITEMS)
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
    residence = args.residence or rng.choice(list(RESIDENCES))
    child_name = args.child_name or rng.choice(CHILD_NAMES)
    helper_name = args.helper_name or rng.choice(HELPER_NAMES)
    school_item = args.school_item or rng.choice(list(ITEMS))
    return StoryParams(
        residence=residence,
        child_name=child_name,
        helper_name=helper_name,
        school_item=school_item,
    )


@dataclass
class World:
    residence: Place
    child: Person
    helper: Person
    item: Item
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    facts: dict = field(default_factory=dict)

    def say(self, text: str) -> None:
        self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)


def make_world(params: StoryParams) -> World:
    residence = RESIDENCES[params.residence]
    subj, obj, pos = PRONOUNS[params.child_name]
    child = Person(
        id=params.child_name,
        role="child",
        label=params.child_name,
        pronoun_subject=subj,
        pronoun_object=obj,
        pronoun_possessive=pos,
        meters={"stress": 0.0},
        memes={"kindness": 0.0, "moral_value": 0.0, "sharing": 0.0},
    )
    helper = Person(
        id=params.helper_name,
        role="helper",
        label=params.helper_name.lower(),
        pronoun_subject="they",
        pronoun_object="them",
        pronoun_possessive="their",
        meters={"care": 0.0},
        memes={"kindness": 1.0, "moral_value": 1.0, "sharing": 1.0},
    )
    item = Item(
        id=params.school_item,
        label=ITEMS[params.school_item],
        owner=params.child_name,
        location="desk drawer",
        found=False,
    )
    return World(residence=residence, child=child, helper=helper, item=item)


def story_begin(world: World) -> None:
    w = world
    w.say(f"{w.child.label} lived in {w.residence.label}, where the afternoon light made the rooms feel quiet and safe.")
    w.say(f"{w.child.label} cared about doing the right thing, but today was a hard day because school had not gone well.")
    w.say(f"{w.child.label} had flunked a small school task and kept thinking about it on the walk home.")


def story_middle(world: World) -> None:
    w = world
    w.para()
    w.say(f"At home, {w.child.label} frowned and rummaged through a backpack, a bookshelf, and the table by the window.")
    w.say(f"{w.child.label} was looking for the {w.item.label}, because it had to be ready for tomorrow.")
    w.say(f"The more {w.child.label} rummaged, the more worried {w.child.pronoun_subject} felt.")
    w.say(f"{w.helper.label.capitalize()} noticed the worry and sat beside {w.child.label} with a gentle voice.")
    w.say(f"\"We can look together,\" {w.helper.label} said. \"No one does hard things perfectly every time.\"")


def story_turn(world: World) -> None:
    w = world
    w.para()
    w.say(f"{w.child.label} admitted the flunk made {w.child.pronoun_object} feel small.")
    w.say(f"{w.helper.label.capitalize()} did not scold {w.child.pronoun_object}. Instead, {w.helper.label} helped rummage more carefully, one shelf at a time.")
    w.say(f"Under a stack of folded papers, they found the {w.item.label}.")
    w.item.found = True
    w.item.location = "child's hands"
    w.child.meters["stress"] = 0.0
    w.child.memes["kindness"] += 1.0
    w.child.memes["moral_value"] += 1.0


def story_end(world: World) -> None:
    w = world
    w.para()
    w.say(f"{w.child.label} smiled, and the room felt warmer.")
    w.say(f"{w.child.label} thanked {w.helper.label} for the kindness and promised to share the table tonight while {w} checked the homework again.")
    w.say(f"That evening, {w.child.label} practiced, {w.helper.label} stayed nearby, and the lost paper sat ready for tomorrow.")
    w.say(f"The flunk still mattered, but it no longer felt like the whole story. {w.child.label} ended the day with help, sharing, and a calmer heart.")


def tell(params: StoryParams) -> World:
    world = make_world(params)
    story_begin(world)
    story_middle(world)
    story_turn(world)
    story_end(world)
    world.facts = {
        "residence": world.residence,
        "child": world.child,
        "helper": world.helper,
        "item": world.item,
    }
    return world


def generation_prompts(world: World) -> list[str]:
    return [
        f"Write a slice-of-life story about a child in {world.residence.label} who has a flunk at school and needs to rummage for a missing {world.item.label}.",
        f"Tell a gentle home story that includes kindness, moral value, and sharing after {world.child.label} feels upset about school.",
        f"Write a small story where a helper and child search through a residence together and end with a calm, helpful moment.",
    ]


def story_qa(world: World) -> list[QAItem]:
    w = world
    return [
        QAItem(
            question=f"Where did {w.child.label} live?",
            answer=f"{w.child.label} lived in {w.residence.label}, a quiet place where the day felt ordinary and close."
        ),
        QAItem(
            question=f"Why did {w.child.label} feel upset at the start of the story?",
            answer=f"{w.child.label} felt upset because {w.child.pronoun_subject} had flunked a small school task and kept worrying about it."
        ),
        QAItem(
            question=f"What was {w.child.label} rummaging for?",
            answer=f"{w.child.label} was rummaging for the {w.item.label}, so {w.child.pronoun_subject} could be ready for tomorrow."
        ),
        QAItem(
            question=f"How did {w.helper.label} help?",
            answer=f"{w.helper.label.capitalize()} helped by searching kindly with {w.child.label} instead of scolding, which made the problem feel smaller."
        ),
        QAItem(
            question=f"What changed by the end?",
            answer=f"By the end, the {w.item.label} was found, the stress had settled down, and kindness and sharing made the home feel warmer."
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is kindness?",
            answer="Kindness is being gentle and helpful so another person feels cared for."
        ),
        QAItem(
            question="What is moral value?",
            answer="A moral value is a good idea about how people should act, like being honest, caring, or fair."
        ),
        QAItem(
            question="What is sharing?",
            answer="Sharing means using or giving something together so other people can have a turn too."
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
    return (
        f"--- world trace ---\n"
        f"residence={world.residence.label}\n"
        f"child={world.child.label} meters={world.child.meters} memes={world.child.memes}\n"
        f"helper={world.helper.label} meters={world.helper.meters} memes={world.helper.memes}\n"
        f"item={world.item.label} location={world.item.location} found={world.item.found}"
    )


def generate(params: StoryParams) -> StorySample:
    world = tell(params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_qa(world),
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


def valid_combos() -> list[tuple[str, str, str]]:
    return [(r, c, i) for r in RESIDENCES for c in CHILD_NAMES for i in ITEMS]


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    clingo_set = set(asp.atoms(model, "valid"))
    python_set = set(valid_combos())
    if clingo_set == python_set:
        print(f"OK: clingo gate matches valid_combos() ({len(clingo_set)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    print("only in clingo:", sorted(clingo_set - python_set))
    print("only in python:", sorted(python_set - clingo_set))
    return 1


def asp_valid() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        vals = asp_valid()
        print(f"{len(vals)} valid (residence, child, item) combos:")
        for row in vals[:50]:
            print(" ", row)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        curated = [
            StoryParams(residence="apartment", child_name="Mina", helper_name="Mom", school_item="library_book"),
            StoryParams(residence="house", child_name="Theo", helper_name="Dad", school_item="math_sheet"),
            StoryParams(residence="duplex", child_name="Luna", helper_name="Grandma", school_item="reading_card"),
        ]
        samples = [generate(p) for p in curated]
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

    for idx, sample in enumerate(samples):
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.child_name} at {p.residence} with {p.school_item}"
        elif len(samples) > 1:
            header = f"### variant {idx + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if idx < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()

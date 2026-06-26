#!/usr/bin/env python3
"""
storyworlds/worlds/grub_plan_gospel_sharing_happy_ending_whodunit.py
=====================================================================

A tiny whodunit storyworld about a careful plan, shared grub, and a cheerful
gospel gathering that ends happily.

The source tale imagined for this world:
---
A small church choir was getting ready for a Sunday gospel picnic. Nia had a
plan: everyone would bring some grub to share after the singing. But when the
basket was opened, one plate of rolls was missing.

Nia and her friend Ben looked around like little detectives. They checked the
bench, the hymn table, and the steps near the garden gate. Finally they found
the rolls tucked inside a cloth bag by the soup pot. Grandpa had moved them so
the wind would not scatter them.

Nobody was in trouble. The plan still worked, the choir sang, and everybody
shared the grub with smiles.
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
    held_by: Optional[str] = None
    location: str = ""
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "woman", "mother", "girl-child"}
        male = {"boy", "man", "father", "grandfather", "grandpa"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str = "the church hall"
    affords: set[str] = field(default_factory=set)


@dataclass
class Clue:
    place: str
    note: str
    found: bool = False


@dataclass
class StoryParams:
    seed: Optional[int] = None
    name: str = "Nia"
    friend: str = "Ben"
    elder: str = "Grandpa"
    setting: str = "hall"
    missing_item: str = "rolls"


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.fired: set[tuple] = set()
        self.clues: list[Clue] = []

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
        import copy as _copy

        w = World(self.setting)
        w.entities = _copy.deepcopy(self.entities)
        w.paragraphs = [[]]
        w.facts = dict(self.facts)
        w.fired = set(self.fired)
        w.clues = _copy.deepcopy(self.clues)
        return w


SETTINGS = {
    "hall": Setting(place="the church hall", affords={"singing", "sharing"}),
}

NAMES = ["Nia", "Ada", "Mila", "Leah", "Ruth"]
FRIENDS = ["Ben", "Noah", "Eli", "Ivy", "Maya"]
ELDERS = ["Grandpa", "Grandma", "Aunt Rose", "Uncle Sam"]
ITEMS = {
    "rolls": ("rolls", "a plate of soft rolls", True),
    "apples": ("apples", "a bowl of apples", True),
    "bread": ("bread", "a loaf of bread", False),
}


def truthy(x: float) -> bool:
    return x >= THRESHOLD


def detect_missing(world: World) -> list[str]:
    out: list[str] = []
    for item in world.entities.values():
        if item.kind == "food" and item.meters.get("missing", 0) >= THRESHOLD:
            if ("found", item.id) not in world.fired:
                world.fired.add(("found", item.id))
                out.append(f"__found__:{item.id}")
    return out


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    while True:
        fired = detect_missing(world)
        if not fired:
            break
        for marker in fired:
            _, item_id = marker.split(":", 1)
            item = world.get(item_id)
            item.meters["missing"] = 0
            item.memes["relief"] = item.memes.get("relief", 0) + 1
            produced.append(f"The missing {item.label} was found.")
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def build_world(params: StoryParams) -> World:
    world = World(SETTINGS[params.setting])
    hero = world.add(Entity(id=params.name, kind="character", type="girl", label=params.name))
    friend = world.add(Entity(id=params.friend, kind="character", type="boy", label=params.friend))
    elder = world.add(Entity(id=params.elder, kind="character", type="grandfather", label=params.elder))

    item_id, item_label, plural = ITEMS[params.missing_item]
    grub = world.add(Entity(
        id="grub", kind="food", type="food", label=item_id,
        phrase=item_label, owner=hero.id, caretaker=hero.id, plural=plural,
        location="basket",
    ))
    basket = world.add(Entity(id="basket", kind="thing", type="basket", label="basket", phrase="a woven basket"))
    cloth = world.add(Entity(id="cloth_bag", kind="thing", type="bag", label="cloth bag", phrase="a cloth bag"))
    pot = world.add(Entity(id="soup_pot", kind="thing", type="pot", label="soup pot", phrase="the soup pot"))

    world.add(basket)
    world.add(cloth)
    world.add(pot)

    world.clues = [
        Clue(place="bench", note="A few crumbs led toward the bench."),
        Clue(place="hymn table", note="A corner of cloth brushed the hymn table."),
        Clue(place="garden gate", note="Fresh wind had blown there, but not the rolls."),
    ]

    world.facts.update(hero=hero, friend=friend, elder=elder, grub=grub, basket=basket, cloth=cloth, pot=pot)
    return world


def introduce(world: World) -> None:
    hero = world.facts["hero"]
    world.say(f"{hero.id} loved gospel day because the songs were bright and the hall felt warm.")


def plan_share(world: World) -> None:
    hero = world.facts["hero"]
    grub = world.facts["grub"]
    world.say(
        f"{hero.id} had a plan: everyone would bring grub to share after the singing, "
        f"and {grub.phrase} would help make the table full."
    )


def disappear(world: World) -> None:
    grub = world.facts["grub"]
    world.say(
        f"When the basket was opened, one plate was missing. The hall got very quiet."
    )
    grub.meters["missing"] = 1
    grub.memes["worry"] = 1


def clue_search(world: World) -> None:
    hero = world.facts["hero"]
    friend = world.facts["friend"]
    world.say(
        f"{hero.id} and {friend.id} looked around like little detectives. "
        f"They checked the bench, the hymn table, and the steps near the garden gate."
    )
    for clue in world.clues:
        world.say(clue.note)
    world.say("Each clue pointed closer to the soup pot by the side table.")


def reveal(world: World) -> None:
    elder = world.facts["elder"]
    grub = world.facts["grub"]
    world.say(
        f"At last, they found the {grub.label} tucked inside a cloth bag by the soup pot."
    )
    world.say(
        f"{elder.id} smiled and said he had moved it there so the wind would not scatter it."
    )
    grub.meters["missing"] = 0
    grub.memes["safe"] = 1
    world.facts["solved"] = True


def happy_ending(world: World) -> None:
    hero = world.facts["hero"]
    friend = world.facts["friend"]
    elder = world.facts["elder"]
    grub = world.facts["grub"]
    world.say(
        f"No one was in trouble. The plan still worked, the choir sang again, and everybody "
        f"shared the {grub.label} with smiles."
    )
    world.say(
        f"{hero.id} laughed, {friend.id} helped carry the basket, and {elder.id} sat down "
        f"to enjoy the happy ending."
    )
    hero.memes["joy"] = hero.memes.get("joy", 0) + 2
    friend.memes["joy"] = friend.memes.get("joy", 0) + 1
    elder.memes["warmth"] = elder.memes.get("warmth", 0) + 1


def tell(params: StoryParams) -> World:
    world = build_world(params)
    introduce(world)
    plan_share(world)
    world.para()
    disappear(world)
    clue_search(world)
    reveal(world)
    world.para()
    happy_ending(world)
    return world


def generation_prompts(world: World) -> list[str]:
    hero = world.facts["hero"]
    grub = world.facts["grub"]
    return [
        'Write a short whodunit for a young child about a church day, a missing plate, and a happy ending.',
        f"Tell a gentle mystery where {hero.id} makes a sharing plan for {grub.label}, then discovers where it went.",
        "Write a child-friendly gospel-day story with clues, a small surprise, and everyone sharing food at the end.",
    ]


def story_qa(world: World) -> list[QAItem]:
    hero = world.facts["hero"]
    friend = world.facts["friend"]
    elder = world.facts["elder"]
    grub = world.facts["grub"]
    return [
        QAItem(
            question=f"What was {hero.id}'s plan for the gospel day?",
            answer=f"{hero.id}'s plan was for everyone to bring grub and share it after the singing.",
        ),
        QAItem(
            question=f"What did {hero.id} and {friend.id} do when the {grub.label} went missing?",
            answer=f"They looked around like little detectives and followed the clues around the hall.",
        ),
        QAItem(
            question=f"Where was the missing {grub.label} found?",
            answer=f"It was found tucked inside a cloth bag by the soup pot.",
        ),
        QAItem(
            question=f"Why had {elder.id} moved the {grub.label}?",
            answer=f"{elder.id} moved it there so the wind would not scatter it.",
        ),
        QAItem(
            question=f"How did the story end?",
            answer="It ended happily, with everyone sharing the grub and smiling together.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a whodunit story?",
            answer="A whodunit is a mystery story where someone asks what happened and then follows clues to find the answer.",
        ),
        QAItem(
            question="What does it mean to share food?",
            answer="To share food means to let other people have some of it too, so everyone can enjoy it together.",
        ),
        QAItem(
            question="What is gospel singing?",
            answer="Gospel singing is singing religious songs, often with a joyful and hopeful sound.",
        ),
    ]


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
        if e.location:
            bits.append(f"location={e.location}")
        lines.append(f"  {e.id:10} ({e.kind:8}) {' '.join(bits)}")
    return "\n".join(lines)


def format_qa(sample: StorySample) -> str:
    lines = ["== Story questions =="]
    for q in sample.story_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    lines.append("")
    lines.append("== World knowledge ==")
    for q in sample.world_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    return "\n".join(lines)


@dataclass
class StoryParamsResolved(StoryParams):
    pass


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A small whodunit about shared grub and a happy ending.")
    ap.add_argument("--name", choices=NAMES)
    ap.add_argument("--friend", choices=FRIENDS)
    ap.add_argument("--elder", choices=ELDERS)
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--missing-item", choices=ITEMS)
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
    name = args.name or rng.choice(NAMES)
    friend = args.friend or rng.choice(FRIENDS)
    elder = args.elder or rng.choice(ELDERS)
    setting = args.setting or "hall"
    missing_item = args.missing_item or rng.choice(list(ITEMS))
    if name == friend:
        raise StoryError("The hero and friend must be different people.")
    return StoryParams(name=name, friend=friend, elder=elder, setting=setting, missing_item=missing_item)


ASP_RULES = r"""
% A grub item is missing if it has the missing marker.
missing(G) :- grub(G), missing_marker(G).

% A clue is relevant if it points to the place where the grub was moved.
relevant_clue(C) :- clue(C), points_to(C, place(garden_gate)).
solved :- missing(G), moved_for_wind(G).

#show missing/1.
#show relevant_clue/1.
#show solved/0.
"""


def asp_facts() -> str:
    import storyworlds.asp as asp
    lines: list[str] = []
    for key in ITEMS:
        lines.append(asp.fact("grub", key))
    lines.append(asp.fact("missing_marker", "grub"))
    lines.append(asp.fact("moved_for_wind", "grub"))
    lines.append(asp.fact("clue", "bench"))
    lines.append(asp.fact("clue", "hymn_table"))
    lines.append(asp.fact("clue", "garden_gate"))
    lines.append(asp.fact("points_to", "garden_gate", "place(garden_gate)"))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import storyworlds.asp as asp
    model = asp.one_model(asp_program("#show solved/0."))
    py = True
    asp_ok = bool(asp.atoms(model, "solved"))
    if asp_ok == py:
        print("OK: ASP and Python agree on the mystery being solved.")
        return 0
    print("MISMATCH: ASP and Python disagree.")
    return 1


def asp_summary() -> str:
    import storyworlds.asp as asp
    model = asp.one_model(asp_program("#show solved/0. #show missing/1."))
    solved = bool(asp.atoms(model, "solved"))
    return f"solved={solved}"


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
    if args.show_asp:
        print(asp_program("#show solved/0."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(asp_summary())
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)

    samples: list[StorySample] = []
    if args.all:
        samples = [generate(StoryParams(name=n, friend=f, elder=e, setting="hall", missing_item=item))
                   for n, f, e, item in [
                       ("Nia", "Ben", "Grandpa", "rolls"),
                       ("Ada", "Noah", "Grandma", "apples"),
                       ("Mila", "Eli", "Aunt Rose", "bread"),
                   ]]
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
        if len(samples) > 1:
            print(f"### variant {idx + 1}")
        emit(sample, trace=args.trace, qa=args.qa)
        if idx < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""
A small comedy storyworld built around direct speech, surprise, misunderstanding,
and a gentle humorous turn.

Premise:
- A child wants to deliver something direct and clear.
- A misunderstanding causes a funny mix-up.
- A surprise reveals the real situation.
- The ending resolves with laughter and a changed emotional state.
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
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    in_hand: bool = False
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

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
class Setting:
    place: str = "the kitchen"
    afford_direct: bool = True


@dataclass
class Item:
    id: str
    label: str
    phrase: str
    message: str
    surprise: str
    misunderstood_as: str


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
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


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------
SETTINGS = {
    "kitchen": Setting(place="the kitchen"),
    "hallway": Setting(place="the hallway"),
    "playroom": Setting(place="the playroom"),
    "garden": Setting(place="the garden"),
}

ITEMS = {
    "note": Item(
        id="note",
        label="note",
        phrase="a folded note",
        message="Please give this to the duck",
        surprise="there was no duck at all",
        misunderstood_as="a snack order",
    ),
    "box": Item(
        id="box",
        label="box",
        phrase="a small cardboard box",
        message="This box is for the hat",
        surprise="the hat was already on someone's head",
        misunderstood_as="a present",
    ),
    "button": Item(
        id="button",
        label="button",
        phrase="a shiny button",
        message="Press this button only once",
        surprise="it was the doorbell button",
        misunderstood_as="a toy button",
    ),
}

HERO_NAMES = ["Milo", "Nina", "Piper", "Otis", "Luna", "Toby", "Ivy", "Theo"]
PARTNER_NAMES = ["Aunt June", "Dad", "Mom", "Uncle Ben", "Grandma"]
TRAITS = ["direct", "honest", "curious", "serious", "cheerful"]


# ---------------------------------------------------------------------------
# Story parameters
# ---------------------------------------------------------------------------
@dataclass
class StoryParams:
    place: str
    item: str
    name: str
    partner: str
    trait: str
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Comedy storyworld with direct speech and a funny misunderstanding.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--item", choices=ITEMS)
    ap.add_argument("--name")
    ap.add_argument("--partner", choices=PARTNER_NAMES)
    ap.add_argument("--trait", choices=TRAITS)
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
    item = args.item or rng.choice(list(ITEMS))
    name = args.name or rng.choice(HERO_NAMES)
    partner = args.partner or rng.choice(PARTNER_NAMES)
    trait = args.trait or rng.choice(TRAITS)
    return StoryParams(place=place, item=item, name=name, partner=partner, trait=trait)


def _subject_name(entity: Entity) -> str:
    return entity.id


def story_setup(world: World, hero: Entity, partner: Entity, item: Item) -> None:
    world.say(f"{hero.id} was a {hero.type} who liked being {world.facts['trait']}.")
    world.say(f"{hero.id} liked to say things {world.facts['direct_word']}, so {hero.pronoun().capitalize()} carried {item.phrase}.")
    world.say(f"That morning, {hero.id} told {partner.id}, \"{item.message}.\"")


def story_conflict(world: World, hero: Entity, partner: Entity, item: Item) -> None:
    hero.memes["curiosity"] = hero.memes.get("curiosity", 0) + 1
    partner.memes["confused"] = partner.memes.get("confused", 0) + 1
    world.para()
    world.say(
        f"{partner.id} blinked and nodded the wrong way, because {partner.pronoun().capitalize()} thought {item.misunderstood_as}."
    )
    world.say(
        f"So {partner.id} pointed to the nearest thing and said, \"You mean that one, right?\""
    )
    world.say(
        f"{hero.id} stared for a moment, then realized the mistake and almost laughed."
    )


def story_turn(world: World, hero: Entity, partner: Entity, item: Item) -> None:
    hero.memes["surprise"] = hero.memes.get("surprise", 0) + 1
    hero.memes["humor"] = hero.memes.get("humor", 0) + 1
    partner.memes["humor"] = partner.memes.get("humor", 0) + 1
    world.para()
    world.say(
        f"Then the surprise part showed up: {item.surprise}."
    )
    world.say(
        f"{hero.id} said, \"No, I meant {item.label}!\" and {partner.id} burst out laughing."
    )


def story_resolution(world: World, hero: Entity, partner: Entity, item: Item) -> None:
    hero.memes["joy"] = hero.memes.get("joy", 0) + 1
    partner.memes["joy"] = partner.memes.get("joy", 0) + 1
    world.para()
    world.say(
        f"After that, they fixed the mix-up together."
    )
    world.say(
        f"{hero.id} kept being direct, and now it was funny instead of awkward."
    )
    world.say(
        f"By the end, {partner.id} was smiling, and {hero.id} was smiling too."
    )


def tell(setting: Setting, item: Item, hero_name: str, partner_name: str, trait: str) -> World:
    world = World(setting)
    hero = world.add(Entity(id=hero_name, kind="character", type="boy" if hero_name in {"Milo", "Otis", "Theo", "Toby"} else "girl"))
    partner = world.add(Entity(id=partner_name, kind="character", type="adult"))
    world.facts.update(
        hero=hero,
        partner=partner,
        item=item,
        trait=trait,
        direct_word="directly",
    )
    story_setup(world, hero, partner, item)
    story_conflict(world, hero, partner, item)
    story_turn(world, hero, partner, item)
    story_resolution(world, hero, partner, item)
    world.facts["resolved"] = True
    return world


# ---------------------------------------------------------------------------
# QA
# ---------------------------------------------------------------------------
def generation_prompts(world: World) -> list[str]:
    f = world.facts
    item: Item = f["item"]
    hero: Entity = f["hero"]
    partner: Entity = f["partner"]
    return [
        f'Write a short comedy story for a child where {hero.id} speaks directly and carries {item.phrase}.',
        f'Write a playful story in which {hero.id} tells {partner.id} "{item.message}" and a misunderstanding causes a funny surprise.',
        f'Create a gentle humorous story about a direct request, a mix-up, and a happy ending involving {item.label}.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero: Entity = f["hero"]
    partner: Entity = f["partner"]
    item: Item = f["item"]
    trait = f["trait"]
    return [
        QAItem(
            question=f"Who was the story about?",
            answer=f"It was about {hero.id}, a {trait} child who liked to speak directly.",
        ),
        QAItem(
            question=f"What did {hero.id} want to do with {item.label}?",
            answer=f"{hero.id} wanted to tell {partner.id} about {item.message.lower()} and carry {item.it()} along.",
        ),
        QAItem(
            question=f"Why did {partner.id} get confused?",
            answer=f"{partner.id} got confused because {partner.pronoun().capitalize()} thought {item.misunderstood_as}.",
        ),
        QAItem(
            question=f"What made the ending funny?",
            answer=f"The ending was funny because the misunderstanding turned into a surprise, and then both of them laughed.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does it mean to be direct?",
            answer="Being direct means saying what you mean in a clear and plain way.",
        ),
        QAItem(
            question="What is a misunderstanding?",
            answer="A misunderstanding is when someone thinks the wrong thing about what another person means.",
        ),
        QAItem(
            question="Why can surprise be funny?",
            answer="A surprise can be funny when it is harmless and makes people laugh because it is unexpected.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    out = ["== (1) Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        out.append(f"{i}. {p}")
    out.append("")
    out.append("== (2) Story questions ==")
    for q in sample.story_qa:
        out.append(f"Q: {q.question}")
        out.append(f"A: {q.answer}")
    out.append("")
    out.append("== (3) World-knowledge questions ==")
    for q in sample.world_qa:
        out.append(f"Q: {q.question}")
        out.append(f"A: {q.answer}")
    return "\n".join(out)


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
item(item).
item(box).
item(button).
item(note).

direct(hero) :- hero(H), trait(H, direct).
misunderstanding(H) :- item(I), misunderstood_as(I, _).
surprise(I) :- item(I), surprise_text(I, _).
humor(H) :- direct(H), misunderstanding(H), surprise(_).

valid_story(Place, Item, Trait) :- place(Place), item(Item), trait_name(Trait).
"""


def asp_facts() -> str:
    import storyworlds.asp as asp
    lines = []
    for place in SETTINGS:
        lines.append(asp.fact("place", place))
    for item_id, item in ITEMS.items():
        lines.append(asp.fact("item", item_id))
        lines.append(asp.fact("surprise_text", item_id, item.surprise))
        lines.append(asp.fact("misunderstood_as", item_id, item.misunderstood_as))
    for trait in TRAITS:
        lines.append(asp.fact("trait_name", trait))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import storyworlds.asp as asp
    model = asp.one_model(asp_program("#show valid_story/3."))
    asp_set = set(asp.atoms(model, "valid_story"))
    py_set = {(p, i, t) for p in SETTINGS for i in ITEMS for t in TRAITS}
    if asp_set == py_set:
        print(f"OK: ASP gate matches Python registry ({len(py_set)} combos).")
        return 0
    print("MISMATCH between ASP and Python.")
    if asp_set - py_set:
        print("only in ASP:", sorted(asp_set - py_set))
    if py_set - asp_set:
        print("only in Python:", sorted(py_set - asp_set))
    return 1


def asp_valid_stories() -> list[tuple]:
    import storyworlds.asp as asp
    model = asp.one_model(asp_program("#show valid_story/3."))
    return sorted(set(asp.atoms(model, "valid_story")))


# ---------------------------------------------------------------------------
# Generation
# ---------------------------------------------------------------------------
def generate(params: StoryParams) -> StorySample:
    setting = SETTINGS[params.place]
    item = ITEMS[params.item]
    world = tell(setting, item, params.name, params.partner, params.trait)
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
        print("\n--- world model state ---")
        for e in sample.world.entities.values():
            print(f"{e.id}: kind={e.kind} type={e.type} meters={e.meters} memes={e.memes}")
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
        stories = asp_valid_stories()
        print(f"{len(stories)} compatible stories:")
        for row in stories:
            print("  ", row)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        for place in SETTINGS:
            for item in ITEMS:
                params = StoryParams(
                    place=place,
                    item=item,
                    name=HERO_NAMES[0],
                    partner=PARTNER_NAMES[0],
                    trait="direct",
                )
                samples.append(generate(params))
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 50, 50):
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

    for idx, sample in enumerate(samples):
        header = f"### variant {idx + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if idx < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()

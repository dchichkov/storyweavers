#!/usr/bin/env python3
"""
Storyworld: stationary magic sharing transformation nursery rhyme.

A tiny classical story domain about a child with a piece of stationary who learns
to share a magical object, causing a gentle transformation and a happy rhyme-like
ending.
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

STATIONARY_KIND = {"pencil", "crayon", "eraser", "notebook", "stamp", "marker"}


@dataclass
class Entity:
    id: str
    kind: str = "thing"  # "character" | "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    held_by: Optional[str] = None
    plural: bool = False
    protective: bool = False
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
class Setting:
    place: str = "the nursery"
    things: set[str] = field(default_factory=set)


@dataclass
class Item:
    id: str
    label: str
    phrase: str
    kind: str
    transform_into: str
    magic_word: str
    shareable: bool = True
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)


@dataclass
class StoryParams:
    place: str
    item: str
    hero: str
    helper: str
    seed: Optional[int] = None


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.items: dict[str, Item] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}

    def add_entity(self, e: Entity) -> Entity:
        self.entities[e.id] = e
        return e

    def add_item(self, i: Item) -> Item:
        self.items[i.id] = i
        return i

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

        c = World(self.setting)
        c.entities = _copy.deepcopy(self.entities)
        c.items = _copy.deepcopy(self.items)
        c.paragraphs = [[]]
        return c


SETTINGS = {
    "nursery": Setting(place="the nursery", things={"table", "box", "blanket"}),
    "playroom": Setting(place="the playroom", things={"table", "box", "shelf"}),
    "classroom": Setting(place="the classroom", things={"desk", "box", "chalk"}),
}

ITEMS = {
    "pencil": Item("pencil", "pencil", "a yellow pencil", "stationary", "garden"),
    "crayon": Item("crayon", "crayon", "a blue crayon", "stationary", "bird"),
    "eraser": Item("eraser", "eraser", "a pink eraser", "stationary", "cloud"),
    "notebook": Item("notebook", "notebook", "a little notebook", "stationary", "star"),
    "stamp": Item("stamp", "stamp", "a tiny stamp", "stationary", "flower"),
    "marker": Item("marker", "marker", "a green marker", "stationary", "rainbow"),
}

HERO_NAMES = ["Mia", "Noah", "Lily", "Finn", "Ava", "Theo", "Zoe", "Ben"]
HELPER_NAMES = ["Mum", "Dad", "Nan", "Pop", "Auntie", "Uncle"]


def rhyme(tail: str) -> str:
    return tail


def build_rhyme_lines(hero: Entity, helper: Entity, item: Item, place: str) -> list[str]:
    return [
        f"Little {hero.id} sat down in {place}, with {item.phrase} held near.",
        f"{hero.pronoun('subject').capitalize()} loved the shiny little thing and kept it snug and dear.",
        f"But when {helper.id} came near and smiled, a sharing song began,",
        f"And soon a magic little change went dancing through the plan.",
    ]


def transform_item(world: World, item: Item) -> None:
    item.meters["magic"] = 1.0
    item.meters["changed"] = 1.0


def share(world: World, hero: Entity, helper: Entity, item: Item) -> None:
    hero.memes["sharing"] = 1.0
    helper.memes["sharing"] = 1.0
    item.memes["shared"] = 1.0
    world.say(f"{hero.id} held up the {item.label} and gave {helper.id} a turn.")
    world.say(f"They used it together, and the room felt warm and kind.")


def turn_magic(world: World, hero: Entity, helper: Entity, item: Item) -> None:
    transform_item(world, item)
    if item.kind == "stationary":
        world.say(
            f"Then the {item.label} twinkled bright, and with a tiny shining gleam, "
            f"it changed into {item.transform_into}, like something from a dream."
        )
    world.say(
        f"{hero.id} and {helper.id} watched it change, then laughed in delight; "
        f"sharing made the magic bloom and made the whole day bright."
    )


def tell(setting: Setting, item: Item, hero_name: str, helper_name: str) -> World:
    world = World(setting)
    hero = world.add_entity(Entity(id=hero_name, kind="character", type="girl"))
    helper = world.add_entity(Entity(id=helper_name, kind="character", type="adult"))
    token = world.add_item(Item(
        id=item.id,
        label=item.label,
        phrase=item.phrase,
        kind=item.kind,
        transform_into=item.transform_into,
        magic_word=item.magic_word,
        shareable=item.shareable,
    ))
    token.held_by = hero.id

    world.say(
        f"Little {hero.id} found {token.phrase} in {setting.place}, and oh, it shone so neat."
    )
    world.say(
        f"{hero.id} liked it best of all and kept it close and sweet."
    )
    world.para()
    world.say(
        f"Then {helper.id} asked, '{hero.id}, may I please have a turn?'"
    )
    world.say(
        f"{hero.id} thought of the toy-like joy of sharing, and let the little kindness burn."
    )
    share(world, hero, helper, token)
    world.para()
    turn_magic(world, hero, helper, token)
    world.facts.update(hero=hero, helper=helper, item=token, setting=setting)
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    item = f["item"]
    return [
        f'Write a short nursery-rhyme story about a child named {hero.id} and {item.phrase}.',
        f'Tell a gentle story where {hero.id} learns to share a {item.label} and magic causes a transformation.',
        f'Write a simple rhyming story in {world.setting.place} that includes stationary and a happy change.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    helper = f["helper"]
    item = f["item"]
    return [
        QAItem(
            question=f"What did {hero.id} find in {world.setting.place}?",
            answer=f"{hero.id} found {item.phrase} in {world.setting.place}.",
        ),
        QAItem(
            question=f"Who asked {hero.id} to share the {item.label}?",
            answer=f"{helper.id} asked {hero.id} to share it.",
        ),
        QAItem(
            question=f"What happened after {hero.id} and {helper.id} shared the {item.label}?",
            answer=f"The {item.label} twinkled and transformed into {item.transform_into}.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is stationary?",
            answer="Stationary is the kind of paper and writing tools people use for drawing, writing, and making little notes.",
        ),
        QAItem(
            question="What does sharing mean?",
            answer="Sharing means letting someone else use or enjoy something with you.",
        ),
        QAItem(
            question="What is a transformation?",
            answer="A transformation is a change from one thing into another thing.",
        ),
        QAItem(
            question="Why do nursery rhymes often sound bouncy?",
            answer="Nursery rhymes often use short, musical words and repeated sounds, so they feel light and bouncy.",
        ),
    ]


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        lines.append(f"  entity {e.id}: kind={e.kind} type={e.type} held_by={e.held_by} memes={e.memes} meters={e.meters}")
    for i in world.items.values():
        lines.append(f"  item {i.id}: label={i.label} held_by={i.held_by} memes={i.memes} meters={i.meters}")
    return "\n".join(lines)


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== (2) Story questions ==")
    for q in sample.story_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    lines.append("")
    lines.append("== (3) World knowledge questions ==")
    for q in sample.world_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    return "\n".join(lines)


ASP_RULES = r"""
stationary(pencil).
stationary(crayon).
stationary(eraser).
stationary(notebook).
stationary(stamp).
stationary(marker).

shareable(Item) :- stationary(Item).
transforms(Item) :- shareable(Item).
happy_story(Hero, Helper, Item) :- shares(Hero, Helper, Item), transforms(Item).
"""


def asp_facts() -> str:
    import asp

    lines = []
    for sid in sorted(ITEMS):
        lines.append(asp.fact("stationary", sid))
        lines.append(asp.fact("shareable", sid))
        lines.append(asp.fact("transforms", sid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def valid_combos() -> list[tuple[str, str, str]]:
    out = []
    for place in SETTINGS:
        for item in ITEMS:
            out.append((place, item, "share"))
    return out


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("#show shareable/1."))
    return sorted(set(asp.atoms(model, "shareable")))


def asp_verify() -> int:
    py = set((k,) for k in ITEMS)
    cl = set(asp_valid_combos())
    if len(cl) == len(py):
        print(f"OK: clingo gate matches valid_combos() ({len(cl)} items).")
        return 0
    print("MISMATCH between clingo and valid_combos()")
    return 1


CURATED = [
    StoryParams(place="nursery", item="pencil", hero="Mia", helper="Mum"),
    StoryParams(place="playroom", item="crayon", hero="Noah", helper="Dad"),
    StoryParams(place="classroom", item="notebook", hero="Lily", helper="Nan"),
]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Stationary, magic, sharing, and transformation in nursery rhyme style.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--item", choices=ITEMS)
    ap.add_argument("--hero")
    ap.add_argument("--helper")
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
    hero = args.hero or rng.choice(HERO_NAMES)
    helper = args.helper or rng.choice(HELPER_NAMES)
    if args.hero and args.helper and args.hero == args.helper:
        raise StoryError("hero and helper must be different people")
    return StoryParams(place=place, item=item, hero=hero, helper=helper)


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.place], ITEMS[params.item], params.hero, params.helper)
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
        print(asp_program("#show shareable/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print("ASP mode is available for this world, but the prose generator is the primary interface.")
        print(asp_program("#show shareable/1."))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)

    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            sample = generate(params)
            if sample.story in seen:
                i += 1
                continue
            seen.add(sample.story)
            samples.append(sample)
            i += 1

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
            header = f"### {p.hero} in {p.place} with {p.item}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()

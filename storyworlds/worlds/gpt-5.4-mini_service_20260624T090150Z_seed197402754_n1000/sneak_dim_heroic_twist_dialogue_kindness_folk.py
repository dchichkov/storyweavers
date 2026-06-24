#!/usr/bin/env python3
"""
storyworlds/worlds/sneak_dim_heroic_twist_dialogue_kindness_folk.py
===================================================================

A small folk-tale storyworld about a child hero, a dim path, a sneak,
a twist, dialogue, and kindness.

The domain premise:
- A small hero needs to cross a dim place to help someone.
- A mistake or misunderstanding creates tension.
- A twist reveals the feared figure is not a threat.
- Dialogue and kindness resolve the problem.
- The ending proves the change with a concrete world state.

This is a standalone simulation script with a Python reasonableness gate and
an inline ASP twin for parity checking.
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
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    plural: bool = False
    protective: bool = False
    covers: set[str] = field(default_factory=set)
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def __post_init__(self):
        if not self.meters:
            self.meters = {"distance": 0.0}
        if not self.memes:
            self.memes = {"fear": 0.0, "hope": 0.0, "kindness": 0.0, "pride": 0.0}

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "woman", "sister", "daughter"}
        male = {"boy", "father", "man", "brother", "son"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def noun(self) -> str:
        return self.label or self.type


@dataclass
class Setting:
    place: str
    dim: bool
    affords: set[str] = field(default_factory=set)


@dataclass
class Item:
    id: str
    label: str
    phrase: str
    region: str
    plural: bool = False
    can_get_lost: bool = True
    can_get_wet: bool = False


@dataclass
class StoryParams:
    place: str
    item: str
    hero_name: str
    hero_type: str
    helper_name: str
    helper_type: str
    seed: Optional[int] = None


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.items: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def add_item(self, ent: Entity) -> Entity:
        self.items[ent.id] = ent
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
    "dim_wood": Setting(place="the dim wood", dim=True, affords={"sneak", "twist"}),
    "hill_path": Setting(place="the hill path", dim=False, affords={"sneak", "twist"}),
    "lantern_lane": Setting(place="the lantern lane", dim=True, affords={"sneak", "twist"}),
    "village_edge": Setting(place="the village edge", dim=False, affords={"sneak", "twist"}),
}

ITEMS = {
    "bread": Item(
        id="bread",
        label="loaf of bread",
        phrase="a warm loaf of bread",
        region="hands",
        plural=False,
        can_get_lost=True,
        can_get_wet=False,
    ),
    "shawl": Item(
        id="shawl",
        label="shawl",
        phrase="a soft red shawl",
        region="shoulders",
        plural=False,
        can_get_lost=True,
        can_get_wet=True,
    ),
    "bell": Item(
        id="bell",
        label="little bell",
        phrase="a tiny silver bell",
        region="hands",
        plural=False,
        can_get_lost=True,
        can_get_wet=False,
    ),
}

HERO_NAMES = ["Mira", "Anya", "Ivo", "Toma", "Lina", "Bela", "Pip", "Niko"]
HELPER_NAMES = ["Grandma", "Grandpa", "Auntie", "Uncle", "Mossy", "Elder Rowan"]
HERO_TYPES = ["girl", "boy"]
HELPER_TYPES = ["mother", "father", "woman", "man"]


# ---------------------------------------------------------------------------
# Story world
# ---------------------------------------------------------------------------
class TaleWorld:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.item_entity: Optional[Entity] = None
        self.fired: set[str] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)


# ---------------------------------------------------------------------------
# Narrative helpers
# ---------------------------------------------------------------------------
def hero_intro(world: TaleWorld, hero: Entity) -> None:
    world.say(
        f"In a little village by {world.setting.place}, there was a small {hero.type} named {hero.id}."
    )
    world.say(
        f"{hero.pronoun().capitalize()} was brave in a quiet, heroic way, and {hero.pronoun('possessive')} heart was kind."
    )
    hero.memes["hope"] += 1


def helper_intro(world: TaleWorld, helper: Entity) -> None:
    world.say(
        f"{helper.id} lived near the lane and spoke in a gentle voice that made even hard days feel softer."
    )


def setup_item(world: TaleWorld, hero: Entity, item: Entity) -> None:
    world.say(
        f"One evening, {hero.id} carried {item.phrase} because {hero.pronoun('subject')} meant to give it as a gift."
    )
    hero.meters["distance"] += 1
    hero.memes["pride"] += 1


def enter_dim_place(world: TaleWorld, hero: Entity) -> None:
    world.say(
        f"{hero.id} walked toward {world.setting.place}, where the light grew dim and the trees looked like tall, still listeners."
    )
    if world.setting.dim:
        hero.memes["fear"] += 1


def sneak_event(world: TaleWorld, hero: Entity) -> None:
    hero.meters["distance"] += 1
    world.say(
        f"To keep the gift safe, {hero.id} had to sneak along the side path, soft as a mouse on straw."
    )


def twist_reveal(world: TaleWorld, hero: Entity, helper: Entity, item: Entity) -> None:
    hero.memes["fear"] += 1
    world.say(
        f"Then came a twist: a dark shape stepped from behind a tree, and {hero.id} gasped."
    )
    world.say(
        f'"Please do not be afraid," said {helper.id}. "I came only to help carry {item.phrase}."'
    )
    helper.memes["kindness"] += 1
    hero.memes["hope"] += 1


def dialogue_and_kindness(world: TaleWorld, hero: Entity, helper: Entity, item: Entity) -> None:
    world.say(
        f'"Why were you in such a hush?" asked {helper.id}.'
    )
    world.say(
        f'"I was trying to be heroic," said {hero.id}, "but I did not want the gift to spoil in the dark."'
    )
    world.say(
        f'"Then let us be heroic together," said {helper.id}, and {helper.pronoun("subject")} held up a small lantern.'
    )
    helper.memes["kindness"] += 1
    hero.memes["fear"] = max(0.0, hero.memes["fear"] - 1)
    hero.memes["hope"] += 1


def resolution(world: TaleWorld, hero: Entity, helper: Entity, item: Entity) -> None:
    hero.memes["fear"] = 0.0
    hero.memes["kindness"] += 1
    item.worn_by = None
    world.say(
        f"With the lantern between them, they walked on together, and {item.phrase} stayed safe and bright."
    )
    world.say(
        f"When they reached the village gate, {hero.id} gave the gift at last, and everyone smiled at the kindness of the deed."
    )


def tell(setting: Setting, item_cfg: Item, hero_name: str, hero_type: str, helper_name: str, helper_type: str) -> TaleWorld:
    world = TaleWorld(setting)
    hero = world.add(Entity(id=hero_name, kind="character", type=hero_type))
    helper = world.add(Entity(id=helper_name, kind="character", type=helper_type))
    item = world.add_item(Entity(
        id=item_cfg.id,
        kind="thing",
        type="thing",
        label=item_cfg.label,
        phrase=item_cfg.phrase,
        owner=hero.id,
        caretaker=helper.id,
        plural=item_cfg.plural,
    ))
    world.item_entity = item

    hero_intro(world, hero)
    helper_intro(world, helper)
    world.para()
    setup_item(world, hero, item)
    enter_dim_place(world, hero)
    sneak_event(world, hero)
    twist_reveal(world, hero, helper, item)
    world.para()
    dialogue_and_kindness(world, hero, helper, item)
    resolution(world, hero, helper, item)

    world.facts.update(
        hero=hero,
        helper=helper,
        item=item,
        setting=setting,
        item_cfg=item_cfg,
        sneaking=True,
        twist=True,
        kindness=True,
        resolved=True,
    )
    return world


# ---------------------------------------------------------------------------
# Reasonableness gate
# ---------------------------------------------------------------------------
def item_at_risk(setting: Setting, item: Item) -> bool:
    return setting.dim and item.can_get_lost


def compatible_fix(setting: Setting, item: Item) -> bool:
    return setting.dim and item.can_get_lost


def explain_rejection(setting: Setting, item: Item) -> str:
    return (
        f"(No story: {item.label} would not face a real risk in {setting.place}. "
        f"The folk-tale needs a dim place and an item that could be lost or spoiled.)"
    )


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
item_at_risk(S, I) :- dim(S), can_get_lost(I).
has_fix(S, I) :- item_at_risk(S, I), dim(S), can_get_lost(I).
valid_story(S, I) :- item_at_risk(S, I), has_fix(S, I).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid, s in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        if s.dim:
            lines.append(asp.fact("dim", sid))
    for iid, item in ITEMS.items():
        lines.append(asp.fact("item", iid))
        if item.can_get_lost:
            lines.append(asp.fact("can_get_lost", iid))
        if item.can_get_wet:
            lines.append(asp.fact("can_get_wet", iid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/2."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    import asp
    py = {(place, item) for place in SETTINGS for item in ITEMS if item_at_risk(SETTINGS[place], ITEMS[item]) and compatible_fix(SETTINGS[place], ITEMS[item])}
    clingo = set(asp_valid_combos())
    if py == clingo:
        print(f"OK: clingo gate matches python gate ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and python gate:")
    if py - clingo:
        print("  only in python:", sorted(py - clingo))
    if clingo - py:
        print("  only in clingo:", sorted(clingo - py))
    return 1


# ---------------------------------------------------------------------------
# Q&A
# ---------------------------------------------------------------------------
def generation_prompts(world: TaleWorld) -> list[str]:
    f = world.facts
    hero = f["hero"]
    item_cfg = f["item_cfg"]
    setting = f["setting"]
    return [
        f'Write a short folk tale for a small child about a brave {hero.type} named {hero.id} in {setting.place}, with a sneak and a twist.',
        f'Write a gentle story where {hero.id} carries {item_cfg.phrase} through a dim place and learns something kind from a helper.',
        f'Write a tale with dialogue, kindness, and a surprise reveal that ends with {item_cfg.label} staying safe.',
    ]


def story_qa(world: TaleWorld) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    helper = f["helper"]
    item = f["item"]
    setting = f["setting"]
    qa = [
        QAItem(
            question=f"Who is the brave child at the center of the tale?",
            answer=f"The tale is about {hero.id}, a little {hero.type} who tries to do something helpful in {setting.place}.",
        ),
        QAItem(
            question=f"What did {hero.id} carry through the dim place?",
            answer=f"{hero.id} carried {item.phrase} and wanted to keep it safe for the gift.",
        ),
        QAItem(
            question=f"Who turned out to be the dark shape in the twist?",
            answer=f"The dark shape was {helper.id}, who came only to help and speak kindly.",
        ),
        QAItem(
            question=f"What did {helper.id} say to make things better?",
            answer=f"{helper.id} said not to be afraid and offered to help carry {item.phrase} with a lantern.",
        ),
        QAItem(
            question=f"How did the story end for {item.label}?",
            answer=f"{item.phrase.capitalize()} stayed safe, and the gift was delivered without trouble.",
        ),
    ]
    return qa


def world_knowledge_qa(world: TaleWorld) -> list[QAItem]:
    return [
        QAItem(
            question="What is a lantern for?",
            answer="A lantern is a small light you can carry to help you see in the dark.",
        ),
        QAItem(
            question="What does it mean to be kind?",
            answer="Being kind means helping, speaking gently, and taking care of others.",
        ),
        QAItem(
            question="What is a twist in a story?",
            answer="A twist is a surprise that changes what the listener thought was happening.",
        ),
        QAItem(
            question="What does it mean to sneak?",
            answer="To sneak means to move quietly and carefully so you do not make much noise.",
        ),
    ]


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


# ---------------------------------------------------------------------------
# Generation
# ---------------------------------------------------------------------------
def valid_combos() -> list[tuple[str, str]]:
    return [
        (place, item)
        for place, setting in SETTINGS.items()
        for item, cfg in ITEMS.items()
        if item_at_risk(setting, cfg) and compatible_fix(setting, cfg)
    ]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Folk-tale storyworld: sneak, dim, heroic twist, dialogue, kindness.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--item", choices=ITEMS)
    ap.add_argument("--name")
    ap.add_argument("--helper")
    ap.add_argument("--hero-type", choices=HERO_TYPES)
    ap.add_argument("--helper-type", choices=HELPER_TYPES)
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
    combos = [c for c in valid_combos()
              if (args.place is None or c[0] == args.place)
              and (args.item is None or c[1] == args.item)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, item = rng.choice(sorted(combos))
    hero_type = args.hero_type or rng.choice(HERO_TYPES)
    helper_type = args.helper_type or rng.choice(HELPER_TYPES)
    hero_name = args.name or rng.choice(HERO_NAMES)
    helper_name = args.helper or rng.choice(HELPER_NAMES)
    return StoryParams(place=place, item=item, hero_name=hero_name, hero_type=hero_type,
                       helper_name=helper_name, helper_type=helper_type)


def generate(params: StoryParams) -> StorySample:
    world = tell(
        SETTINGS[params.place],
        ITEMS[params.item],
        params.hero_name,
        params.hero_type,
        params.helper_name,
        params.helper_type,
    )
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


def dump_trace(world: TaleWorld) -> str:
    lines = ["--- world trace ---"]
    for e in world.entities.values():
        lines.append(
            f"  {e.id}: type={e.type} meters={{{', '.join(f'{k}={v}' for k, v in e.meters.items() if v)}}} "
            f"memes={{{', '.join(f'{k}={v}' for k, v in e.memes.items() if v)}}}"
        )
    if world.item_entity:
        item = world.item_entity
        lines.append(f"  item: {item.label} worn_by={item.worn_by}")
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


CURATED = [
    StoryParams(place="dim_wood", item="bread", hero_name="Mira", hero_type="girl", helper_name="Grandma", helper_type="woman"),
    StoryParams(place="lantern_lane", item="shawl", hero_name="Ivo", hero_type="boy", helper_name="Mossy", helper_type="man"),
    StoryParams(place="hill_path", item="bell", hero_name="Lina", hero_type="girl", helper_name="Elder Rowan", helper_type="man"),
]


def asp_verify_program() -> str:
    return asp_program("#show valid_story/2.")


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_verify_program())
        return
    if args.verify:
        sys.exit(asp_verify())

    if args.asp:
        import asp
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible story combos:\n")
        for place, item in combos:
            print(f"  {place:12} {item}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
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

    for i, sample in enumerate(samples):
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.hero_name}: {p.item} in {p.place}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()

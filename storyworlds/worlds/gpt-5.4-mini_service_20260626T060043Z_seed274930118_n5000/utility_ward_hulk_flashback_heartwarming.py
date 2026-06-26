#!/usr/bin/env python3
"""
A heartwarming storyworld about a utility-room hulk, a small ward, and a
flashback that explains why help matters.
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
    traits: list[str] = field(default_factory=list)
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "mother", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class Place:
    label: str
    inside: bool = True
    affordances: set[str] = field(default_factory=set)


@dataclass
class Item:
    id: str
    label: str
    phrase: str
    region: str
    plural: bool = False
    genders: set[str] = field(default_factory=lambda: {"girl", "boy"})


@dataclass
class StoryParams:
    place: str
    item: str
    name: str
    gender: str
    parent: str
    trait: str
    seed: Optional[int] = None


class World:
    def __init__(self, place: Place) -> None:
        self.place = place
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.flashback_revealed = False

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


def scene_opening(world: World, hero: Entity, ward: Entity, hulk: Entity) -> None:
    world.say(
        f"{hero.id} was a little {hero.traits[0]} {hero.type} who spent afternoons "
        f"in the utility room beside {ward.label}."
    )
    world.say(
        f"At the far end of the room stood {hulk.label}, a huge but gentle hulk "
        f"who knew every shelf, switch, and squeaky hinge."
    )


def flashback(world: World, hero: Entity, ward: Entity, hulk: Entity) -> None:
    if world.flashback_revealed:
        return
    world.flashback_revealed = True
    world.para()
    world.say(
        f"Long ago, when {hero.id} was smaller, {ward.label} had been scared of the "
        f"dark utility room."
    )
    world.say(
        f"{hulk.label} had stayed close, carrying a lantern and humming until the "
        f"little {ward.type} could smile again."
    )
    world.say(
        f"Since then, {hero.id} had trusted {hulk.pronoun('object')} more than any "
        f"other helper in the house."
    )


def problem(world: World, hero: Entity, ward: Entity, item: Entity) -> None:
    hero.memes["worry"] = hero.memes.get("worry", 0) + 1
    world.para()
    world.say(
        f"One afternoon, {ward.label} looked at {item.phrase} and frowned."
    )
    world.say(
        f"It had slipped behind a heavy stack of boxes, and nobody could reach it."
    )


def hulk_help(world: World, hero: Entity, ward: Entity, hulk: Entity, item: Entity) -> None:
    hulk.meters["helpfulness"] = hulk.meters.get("helpfulness", 0) + 1
    world.say(
        f"{hero.id} called softly, and {hulk.label} knelt down instead of looming."
    )
    world.say(
        f"With careful hands, {hulk.pronoun('subject')} moved the boxes, found the "
        f"{item.label}, and gave it back without knocking anything else over."
    )
    ward.memes["relief"] = ward.memes.get("relief", 0) + 1
    hero.memes["joy"] = hero.memes.get("joy", 0) + 1


def ending(world: World, hero: Entity, ward: Entity, hulk: Entity, item: Entity) -> None:
    world.para()
    world.say(
        f"{ward.label} hugged {hero.pronoun('object')} first, then gave {hulk.pronoun('object')} "
        f"a careful squeeze around the middle."
    )
    world.say(
        f"The utility room felt warm and safe again, with the rescued {item.label} "
        f"back on the shelf and the big hulk smiling in the lamp glow."
    )


SETTINGS = {
    "utility": Place(label="the utility room", inside=True, affordances={"hide", "store", "fetch"}),
}

ITEMS = {
    "wardbox": Item(
        id="wardbox",
        label="ward's little tin box",
        phrase="a little tin box with a blue ribbon",
        region="shelf",
    ),
    "lantern": Item(
        id="lantern",
        label="lantern",
        phrase="a small brass lantern",
        region="floor",
    ),
}

TRAITS = ["brave", "gentle", "curious", "cheerful", "helpful"]
GIRL_NAMES = ["Maya", "Nora", "Lena", "Ivy", "Zoe"]
BOY_NAMES = ["Eli", "Theo", "Finn", "Noah", "Max"]


def valid_combos() -> list[tuple[str, str]]:
    return [("utility", item_id) for item_id in ITEMS]


@dataclass
class WorldState:
    place: Place
    hero: Entity
    ward: Entity
    hulk: Entity
    item: Entity


def tell(place: Place, item_def: Item, name: str, gender: str, parent: str, trait: str) -> World:
    world = World(place)
    hero = world.add(Entity(id=name, kind="character", type=gender, traits=["little", trait]))
    ward = world.add(Entity(id="Ward", kind="character", type="child", label="the ward"))
    hulk = world.add(Entity(id="Hulk", kind="character", type="hulk", label="the hulk"))
    item = world.add(Entity(
        id=item_def.id,
        type=item_def.id,
        label=item_def.label,
        phrase=item_def.phrase,
        owner=ward.id,
        caretaker=hero.id,
    ))
    scene_opening(world, hero, ward, hulk)
    flashback(world, hero, ward, hulk)
    problem(world, hero, ward, item)
    hulk_help(world, hero, ward, hulk, item)
    ending(world, hero, ward, hulk, item)
    world.facts.update(hero=hero, ward=ward, hulk=hulk, item=item, place=place, parent=parent)
    return world


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero, ward, hulk, item = f["hero"], f["ward"], f["hulk"], f["item"]
    return [
        QAItem(
            question=f"Who was the story mostly about in the utility room?",
            answer=f"It was about {hero.id}, who spent time with {ward.label} and the gentle hulk.",
        ),
        QAItem(
            question=f"What did the flashback show about {hulk.label}?",
            answer=(
                f"It showed that {hulk.label} had helped before, staying close with a lantern "
                f"when {ward.label} was scared of the utility room."
            ),
        ),
        QAItem(
            question=f"How did {hulk.label} help with the {item.label}?",
            answer=(
                f"{hulk.label} moved the boxes carefully, found the {item.label}, and gave it back "
                f"without making a mess."
            ),
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a utility room?",
            answer="A utility room is a room in a house where people keep useful things like supplies, tools, or cleaning items.",
        ),
        QAItem(
            question="What is a hulk in a story?",
            answer="A hulk is a very large person or creature, often strong, and in a kind story they can use that strength to help.",
        ),
        QAItem(
            question="What is a flashback?",
            answer="A flashback is when a story briefly shows something that happened earlier, so the reader understands why a character feels the way they do now.",
        ),
    ]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        'Write a heartwarming story set in a utility room with a gentle hulk and a small ward, and include a flashback.',
        f"Tell a short story where {f['hero'].id} remembers why {f['hulk'].label} is trusted.",
        "Write a child-friendly story about finding something lost in a utility room and ending with a warm hug.",
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== Story questions ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== World-knowledge questions ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Heartwarming utility-room hulk storyworld.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--item", choices=ITEMS)
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
    item_id = args.item or rng.choice(list(ITEMS))
    item = ITEMS[item_id]
    gender = args.gender or rng.choice(sorted(item.genders))
    if gender not in item.genders:
        raise StoryError("That item does not fit the chosen gender in this little world.")
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    parent = args.parent or rng.choice(["mother", "father"])
    trait = rng.choice(TRAITS)
    place = args.place or "utility"
    return StoryParams(place=place, item=item_id, name=name, gender=gender, parent=parent, trait=trait)


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.place], ITEMS[params.item], params.name, params.gender, params.parent, params.trait)
    story = world.render()
    return StorySample(
        params=params,
        story=story,
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for e in world.entities.values():
        bits = []
        if e.traits:
            bits.append(f"traits={e.traits}")
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        lines.append(f"{e.id}: {e.type} {' '.join(bits)}")
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


ASP_RULES = r"""
place(utility).
item(wardbox).
item(lantern).
flashback(utility).
heartwarming(utility).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for pid in SETTINGS:
        lines.append(asp.fact("place", pid))
        if SETTINGS[pid].inside:
            lines.append(asp.fact("inside", pid))
    for iid in ITEMS:
        lines.append(asp.fact("item", iid))
    lines.append(asp.fact("uses", "utility", "ward"))
    lines.append(asp.fact("uses", "utility", "hulk"))
    lines.append(asp.fact("feature", "flashback"))
    lines.append(asp.fact("style", "heartwarming"))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    return 0


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show place/1."))
        return
    if args.verify:
        sys.exit(asp_verify())

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        cur = [
            StoryParams(place="utility", item=item_id, name="Maya", gender="girl", parent="mother", trait="gentle")
            for item_id in ITEMS
        ]
        samples = [generate(p) for p in cur]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 20, 20):
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
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()

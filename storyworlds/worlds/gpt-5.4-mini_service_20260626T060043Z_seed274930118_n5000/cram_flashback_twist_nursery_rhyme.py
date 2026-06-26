#!/usr/bin/env python3
from __future__ import annotations

"""
storyworlds/worlds/gpt-5.4-mini_service_20260626T060043Z_seed274930118_n5000/cram_flashback_twist_nursery_rhyme.py
===============================================================================================================

A tiny Storyweavers world about a child who tries to cram things into a snug
place, with a flashback and a twist, told in a nursery-rhyme-like voice.

The world model tracks physical fullness and emotional feelings with meters and
memes. The story is generated from a simulated sequence of events rather than a
frozen paragraph.
"""

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
    container: Optional[str] = None
    capacity: int = 0
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman", "sister"}
        male = {"boy", "father", "dad", "man", "brother"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def noun(self) -> str:
        return self.label or self.type

    def obj(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str
    inside: bool = True
    mood: str = "quiet"


@dataclass
class Item:
    id: str
    label: str
    phrase: str
    size: int
    kind: str = "snack"
    bright: bool = False
    sticky: bool = False
    songy: bool = False


@dataclass
class Container:
    id: str
    label: str
    phrase: str
    capacity: int
    snug: bool = True
    lid: bool = False
    guards: set[str] = field(default_factory=set)


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.events: list[str] = []

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str) -> Entity:
        return self.entities[eid]

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)
            self.events.append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)

    def copy(self) -> "World":
        import copy
        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.facts = dict(self.facts)
        clone.paragraphs = [[]]
        return clone


def fits(container: Container, item: Item, count: int) -> bool:
    return count * item.size <= container.capacity


def select_container(item: Item) -> Optional[Container]:
    for c in CONTAINERS:
        if item.kind in c.guards or not c.guards:
            if fits(c, item, 3):
                return c
    return None


def reasonableness_ok(item: Item, container: Container) -> bool:
    return fits(container, item, 3)


def apply_cram(world: World, child: Entity, item: Item, container: Container) -> None:
    child.memes["eager"] = child.memes.get("eager", 0) + 1
    child.meters["cram"] = child.meters.get("cram", 0) + 1
    container_ent = world.get(container.id)
    container_ent.meters["full"] = container_ent.meters.get("full", 0) + 3
    child.meters["joy"] = child.meters.get("joy", 0) + 1


def flashback(world: World, child: Entity, container: Container, item: Item) -> None:
    world.say(
        f"Flashback: yesterday, {child.id} had placed just one {item.label} in the {container.label}, "
        f"and it had shut with a soft little click."
    )
    child.memes["memory"] = child.memes.get("memory", 0) + 1


def twist(world: World, child: Entity, parent: Entity, item: Item, container: Container) -> None:
    world.say(
        f"Twist: the {container.label} was never for lunch at all; it was a keepsake box for the night-song bells, "
        f"so the {item.label}s were only being packed for a safe ride home."
    )
    child.memes["surprise"] = child.memes.get("surprise", 0) + 1
    parent.memes["relief"] = parent.memes.get("relief", 0) + 1


def tell_story(world: World, child: Entity, parent: Entity, item: Item, container: Container) -> World:
    world.say(
        f"Little {child.id} in the {world.setting.place} liked to cram three bright {item.label}s into the {container.label}."
    )
    world.say(
        f"{child.pronoun('subject').capitalize()} hummed a nursery rhyme tune: 'Cram, cram, little light, fit in snug and hold it tight.'"
    )
    world.para()
    flashback(world, child, container, item)
    world.say(
        f"But now the lid would not sit straight, and {parent.id} frowned in a gentle way, "
        f"for the {container.label} looked ready to pop."
    )
    child.memes["worry"] = child.memes.get("worry", 0) + 1
    world.say(
        f"{child.id} slowed down and listened, while the {item.label}s made a bright little pile on the table."
    )
    twist(world, child, parent, item, container)
    world.para()
    world.say(
        f"So {child.id} did not cram after all; {child.pronoun('subject')} packed them neatly, one by one, "
        f"and the {container.label} closed with a tidy sound."
    )
    world.say(
        f"Under the lamp, the bells stayed safe, the {item.label}s stayed bright, and {child.id} skipped to bed with a sleepy smile."
    )
    world.facts.update(child=child, parent=parent, item=item, container=container)
    return world


SETTINGS = {
    "nook": Setting(place="the candlelit nook", inside=True, mood="quiet"),
    "kitchen": Setting(place="the warm little kitchen", inside=True, mood="cozy"),
    "attic": Setting(place="the attic by the moon window", inside=True, mood="dusty"),
}

ITEMS = {
    "berries": Item(id="berries", label="berries", phrase="shiny red berries", size=1, kind="snack", bright=True, sticky=False, songy=True),
    "pebbles": Item(id="pebbles", label="pebbles", phrase="smooth round pebbles", size=1, kind="keepsake", bright=False, sticky=False, songy=False),
    "cookies": Item(id="cookies", label="cookies", phrase="tiny sugar cookies", size=2, kind="snack", bright=True, sticky=True, songy=True),
}

CONTAINERS = [
    Container(id="box", label="box", phrase="a snug keepsake box", capacity=3, snug=True, lid=True, guards={"keepsake"}),
    Container(id="tin", label="tin", phrase="a small tin", capacity=4, snug=True, lid=True, guards={"snack"}),
    Container(id="basket", label="basket", phrase="a woven basket", capacity=6, snug=False, lid=False, guards={"snack", "keepsake"}),
]

NAMES = ["Mimi", "Nell", "Pip", "Teddy", "Rosy", "Benny"]
PARENT_NAMES = ["Mum", "Dad", "Mama", "Papa"]


@dataclass
class StoryParams:
    setting: str
    item: str
    container: str
    name: str
    parent: str
    seed: Optional[int] = None


def valid_combos() -> list[tuple[str, str, str]]:
    out = []
    for s in SETTINGS:
        for i in ITEMS:
            for c in CONTAINERS:
                if reasonableness_ok(ITEMS[i], c):
                    out.append((s, i, c.id))
    return out


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A small nursery-rhyme story world about cramming, flashback, and twist.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--item", choices=ITEMS)
    ap.add_argument("--container", choices=[c.id for c in CONTAINERS])
    ap.add_argument("--name")
    ap.add_argument("--parent", choices=PARENT_NAMES)
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
    if args.item and args.container:
        if not reasonableness_ok(ITEMS[args.item], next(c for c in CONTAINERS if c.id == args.container)):
            raise StoryError("That item does not reasonably fit in that container.")
    combos = valid_combos()
    if args.setting:
        combos = [c for c in combos if c[0] == args.setting]
    if args.item:
        combos = [c for c in combos if c[1] == args.item]
    if args.container:
        combos = [c for c in combos if c[2] == args.container]
    if not combos:
        raise StoryError("No valid story combination matches those choices.")
    setting, item, container = rng.choice(sorted(combos))
    return StoryParams(
        setting=setting,
        item=item,
        container=container,
        name=args.name or rng.choice(NAMES),
        parent=args.parent or rng.choice(PARENT_NAMES),
    )


def generate(params: StoryParams) -> StorySample:
    world = World(SETTINGS[params.setting])
    child = world.add(Entity(id=params.name, kind="character", type="child"))
    parent = world.add(Entity(id=params.parent, kind="character", type="parent"))
    item = ITEMS[params.item]
    container_def = next(c for c in CONTAINERS if c.id == params.container)
    container = world.add(Entity(id=container_def.id, type="container", label=container_def.label, phrase=container_def.phrase, capacity=container_def.capacity))

    if not reasonableness_ok(item, container_def):
        raise StoryError("Invalid item/container pairing for this world.")

    tell_story(world, child, parent, item, container_def)
    prompts = [
        f"Write a short nursery-rhyme story where {params.name} tries to cram {item.phrase} into {container.phrase}.",
        "Include a flashback and a twist, and keep the voice gentle and sing-song.",
        f"Tell a tiny story set in {world.setting.place} with a snug little surprise at the end.",
    ]
    story_qa = [
        QAItem(
            question=f"What did {params.name} try to do with the {item.label}?",
            answer=f"{params.name} tried to cram the {item.phrase} into the {container.phrase}.",
        ),
        QAItem(
            question="What did the flashback show?",
            answer=f"It showed that yesterday {params.name} had placed just one {item.label} in the {container.label}, and that had worked nicely.",
        ),
        QAItem(
            question="What was the twist?",
            answer=f"The twist was that the {container.label} was really meant for night-song bells, so the packing was about keeping them safe.",
        ),
    ]
    world_qa = [
        QAItem(
            question="What does it mean to cram something somewhere?",
            answer="To cram means to push too much into a space that is already small or snug.",
        ),
        QAItem(
            question="Why can a small container get too full?",
            answer="A small container can get too full when there is more inside than its space can hold neatly.",
        ),
    ]
    return StorySample(params=params, story=world.render(), prompts=prompts, story_qa=story_qa, world_qa=world_qa, world=world)


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world is not None:
        print(dump_trace(sample.world))
    if qa:
        print()
        print(format_qa(sample))


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        parts = []
        if e.meters:
            parts.append(f"meters={e.meters}")
        if e.memes:
            parts.append(f"memes={e.memes}")
        if e.capacity:
            parts.append(f"capacity={e.capacity}")
        lines.append(f"  {e.id:8} ({e.type}) {' '.join(parts)}")
    return "\n".join(lines)


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== story QA ==")
    for q in sample.story_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    lines.append("")
    lines.append("== world QA ==")
    for q in sample.world_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    return "\n".join(lines)


ASP_RULES = r"""
item(item_berries).
item(item_pebbles).
item(item_cookies).

container(container_box).
container(container_tin).
container(container_basket).

capacity(container_box, 3).
capacity(container_tin, 4).
capacity(container_basket, 6).

size(item_berries, 1).
size(item_pebbles, 1).
size(item_cookies, 2).

valid(I, C) :- item(I), container(C), size(I, S), capacity(C, Cap), 3 * S <= Cap.
"""


def asp_facts() -> str:
    import asp
    lines = []
    for iid, it in ITEMS.items():
        lines.append(asp.fact("item", f"item_{iid}"))
        lines.append(asp.fact("size", f"item_{iid}", it.size))
    for c in CONTAINERS:
        lines.append(asp.fact("container", f"container_{c.id}"))
        lines.append(asp.fact("capacity", f"container_{c.id}", c.capacity))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/2."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    py = {(f"item_{i}", f"container_{c}") for _, i, c in valid_combos()}
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: ASP matches Python ({len(py)} combos).")
        return 0
    print("MISMATCH:")
    print(" only in python:", sorted(py - cl))
    print(" only in asp:", sorted(cl - py))
    return 1


CURATED = [
    StoryParams(setting="nook", item="berries", container="tin", name="Mimi", parent="Mum"),
    StoryParams(setting="kitchen", item="cookies", container="basket", name="Pip", parent="Dad"),
    StoryParams(setting="attic", item="pebbles", container="box", name="Rosy", parent="Mama"),
]


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show valid/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print("\n".join(f"{a}" for a in asp_valid_combos()))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen = set()
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

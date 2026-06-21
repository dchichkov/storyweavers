#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/roman_misunderstanding_happy_ending_bravery_bedtime_story.py
=============================================================================================

A tiny bedtime story world about a child, a small Roman mask, a misunderstanding,
and a brave, happy ending.

The world is intentionally small:
- One child finds a Roman-looking toy.
- Another child misunderstands what it is and gets scared.
- A brave explanation and a calm adult help fix the misunderstanding.
- The ending is warm, gentle, and sleepy.

It supports the shared Storyweavers CLI:
    -n, --all, --seed, --trace, --qa, --json, --asp, --verify, --show-asp
"""

from __future__ import annotations

import argparse
import copy
import json
import os
import random
import sys
from dataclasses import dataclass, field
from typing import Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from results import QAItem, StoryError, StorySample  # noqa: E402

THRESHOLD = 1.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    role: str = ""
    traits: list[str] = field(default_factory=list)
    attrs: dict = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman"}
        male = {"boy", "father", "dad", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return {"mother": "mom", "father": "dad"}.get(self.type, self.type)
    @property
    def phrase(self) -> str:
        return str(getattr(self, "_phrase", None) or getattr(self, "label_word", None) or getattr(self, "label", None) or getattr(self, "id", self.__class__.__name__.lower()))

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)

    @property
    def tags(self):
        if not hasattr(self, "_tags"):
            object.__setattr__(self, "_tags", set())
        return self._tags


@dataclass
class Item:
    id: str
    label: str
    kind: str = "toy"
    roman: bool = False
    looks_like: str = ""
    fragile: bool = False
    safe: bool = True
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def phrase(self) -> str:
        return str(getattr(self, "_phrase", None) or getattr(self, "label_word", None) or getattr(self, "label", None) or getattr(self, "id", self.__class__.__name__.lower()))

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)

    @property
    def tags(self):
        if not hasattr(self, "_tags"):
            object.__setattr__(self, "_tags", set())
        return self._tags


@dataclass
class Room:
    id: str
    label: str
    bedtime: bool = True
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def phrase(self) -> str:
        return str(getattr(self, "_phrase", None) or getattr(self, "label_word", None) or getattr(self, "label", None) or getattr(self, "id", self.__class__.__name__.lower()))

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)

    @property
    def tags(self):
        if not hasattr(self, "_tags"):
            object.__setattr__(self, "_tags", set())
        return self._tags


@dataclass
class World:
    entities: dict[str, object] = field(default_factory=dict)
    fired: set[tuple] = field(default_factory=set)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    facts: dict = field(default_factory=dict)

    def add(self, ent):
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str):
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
        clone = World()
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        clone.facts = copy.deepcopy(self.facts)
        return clone
    @property
    def meters(self):
        if not hasattr(self, "_meters"):
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if not hasattr(self, "_memes"):
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes

    @property
    def tags(self):
        if not hasattr(self, "_tags"):
            object.__setattr__(self, "_tags", set())
        return self._tags


@dataclass
class StoryParams:
    child1: str
    child1_gender: str
    child2: str
    child2_gender: str
    parent: str
    parent_gender: str
    room: str
    roman_item: str
    misunderstanding: str
    seed: Optional[int] = None
    @property
    def meters(self):
        if not hasattr(self, "_meters"):
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if not hasattr(self, "_memes"):
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes

    @property
    def tags(self):
        if not hasattr(self, "_tags"):
            object.__setattr__(self, "_tags", set())
        return self._tags


CHILD_GIRLS = ["Mia", "Luna", "Nora", "Ivy", "Ella", "Zoe"]
CHILD_BOYS = ["Theo", "Owen", "Leo", "Finn", "Milo", "Eli"]
TRAITS = ["brave", "gentle", "sleepy", "curious", "kind"]
ROOMS = {
    "bedroom": Room(id="bedroom", label="the bedroom", bedtime=True),
    "nursery": Room(id="nursery", label="the nursery", bedtime=True),
    "attic": Room(id="attic", label="the attic", bedtime=False),
}
ROMAN_ITEMS = {
    "helmet": Item(id="helmet", label="little Roman helmet", roman=True, looks_like="a tiny shiny bowl", fragile=True, safe=True),
    "shield": Item(id="shield", label="toy Roman shield", roman=True, looks_like="a dinner plate", fragile=False, safe=True),
    "scroll": Item(id="scroll", label="rolled Roman scroll", roman=True, looks_like="a strange old letter", fragile=True, safe=True),
}
MISUNDERSTANDINGS = {
    "owl": "a spooky owl from the dark",
    "moon": "a face from the moon",
    "ghost": "a ghost from the hall",
}
PARENT_NAMES = ["Mom", "Dad"]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A bedtime story world about Roman toys, a misunderstanding, and bravery.")
    ap.add_argument("--room", choices=ROOMS)
    ap.add_argument("--roman-item", choices=ROMAN_ITEMS)
    ap.add_argument("--misunderstanding", choices=MISUNDERSTANDINGS)
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


def reasonableness(params: StoryParams) -> None:
    if params.roman_item not in ROMAN_ITEMS:
        raise StoryError("Unknown Roman item.")
    if params.room not in ROOMS:
        raise StoryError("Unknown room.")
    if params.misunderstanding not in MISUNDERSTANDINGS:
        raise StoryError("Unknown misunderstanding.")
    if not ROOMS[params.room].bedtime:
        raise StoryError("This story belongs in a bedtime room.")
    if not ROMAN_ITEMS[params.roman_item].roman:
        raise StoryError("The item must be Roman-themed.")


def valid_combos() -> list[tuple[str, str, str]]:
    out = []
    for room in ROOMS:
        if not ROOMS[room].bedtime:
            continue
        for item in ROMAN_ITEMS:
            for mis in MISUNDERSTANDINGS:
                out.append((room, item, mis))
    return out


def _set_memes(ent: Entity, **vals: float) -> None:
    for k, v in vals.items():
        ent.memes[k] = v


def _set_meters(ent: Entity, **vals: float) -> None:
    for k, v in vals.items():
        ent.meters[k] = v


def tell(params: StoryParams) -> World:
    reasonableness(params)
    world = World()
    child1 = world.add(Entity(id=params.child1, kind="character", type=params.child1_gender, role="brave child", traits=["brave"]))
    child2 = world.add(Entity(id=params.child2, kind="character", type=params.child2_gender, role="wary child", traits=["gentle"]))
    parent = world.add(Entity(id=params.parent, kind="character", type=params.parent_gender, role="parent"))
    room = world.add(ROOMS[params.room])
    item = world.add(ROMAN_ITEMS[params.roman_item])

    _set_memes(child1, bravery=2.0, joy=1.0)
    _set_memes(child2, worry=1.0)
    _set_memes(parent, calm=2.0)
    _set_meters(room, hush=1.0)
    _set_meters(item, gleam=1.0)

    world.say(
        f"At bedtime in {room.label}, {child1.id} and {child2.id} found {item.label}, "
        f"with its little shape looking like {item.looks_like}."
    )
    world.say(
        f"{child1.id} smiled. \"It is from Roman stories,\" {child1.pronoun()} whispered, "
        f"careful not to wake the house."
    )

    world.para()
    world.say(
        f"But {child2.id} took one sleepy look and gasped. \"No, that's {MISUNDERSTANDINGS[params.misunderstanding]}!\" "
        f"{child2.pronoun()} said, backing up under the blanket."
    )
    _set_memes(child2, fear=2.0)
    _set_memes(room, tension=1.0)

    world.para()
    _set_memes(child1, bravery=3.0)
    world.say(
        f"{child1.id} took a deep breath, held the little thing up in the lamp-light, and said, "
        f"\"It's only a toy. See the painted edges? It's Roman, not scary.\""
    )
    _set_memes(child2, curiosity=2.0)

    world.para()
    world.say(
        f"{params.parent} came softly to the door, knelt down, and nodded. "
        f"\"{child2.id}, {child1.id} is right. It is safe, and it is kind to ask before we guess,\" "
        f"{parent.pronoun()} said."
    )
    _set_memes(parent, reassurance=2.0)

    world.para()
    _set_memes(child2, fear=0.0, joy=2.0)
    _set_meters(room, tension=0.0, hush=2.0)
    world.say(
        f"{child2.id} blushed, then giggled. {child2.pronoun().capitalize()} touched the toy gently and said, "
        f"\"Oh. I thought it was a ghost. It is just Roman and shiny.\""
    )
    world.say(
        f"The two children tucked it beside the pillow, and the room grew soft and warm again."
    )
    world.say(
        f"Soon they were both under the quilt, brave enough to smile at the dark, while {params.parent} "
        f"turned off the lamp and left the little Roman treasure glowing safely in their dreams."
    )

    world.facts.update(
        child1=child1,
        child2=child2,
        parent=parent,
        room=room,
        item=item,
        misunderstanding=params.misunderstanding,
        outcome="happy",
    )
    return world


def generate(params: StoryParams) -> StorySample:
    world = tell(params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=[QAItem(question=q, answer=a) for q, a in story_qa(world)],
        world_qa=[QAItem(question=q, answer=a) for q, a in world_knowledge_qa(world)],
        world=world,
    )


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a bedtime story for a child who sees something Roman and misunderstands it at first, but learns it is safe.',
        f"Tell a gentle story where {f['child1'].id} finds a Roman toy, {f['child2'].id} gets worried, and everyone ends up calm and happy.",
        f'Write a cozy nighttime story that includes the word "roman" and ends with bravery and a happy ending.',
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    c1, c2, parent, item = f["child1"], f["child2"], f["parent"], f["item"]
    mis = f["misunderstanding"]
    return [
        ("What was the story about?",
         f"It was about {c1.id} and {c2.id} finding {item.label} at bedtime. The little Roman toy made the night feel surprising at first."),
        (f"Why did {c2.id} get scared?",
         f"{c2.id} thought the toy was {MISUNDERSTANDINGS[mis]}. That was a misunderstanding, because the toy was only a safe Roman thing."),
        (f"How did {c1.id} show bravery?",
         f"{c1.id} took a deep breath and explained what the toy really was. That brave moment helped turn the scared feeling into calm."),
        (f"What did {parent.id} do?",
         f"{parent.id} came softly and said the children should ask before they guess. That gentle help made everyone feel safe again."),
        ("How did the story end?",
         "It ended happily, with the children calm under the quilt and the Roman treasure kept safely by the pillow. The ending image shows that fear changed into comfort."),
    ]


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    return [
        ("What does Roman mean here?",
         "Roman means it belongs to the old Roman world of stories, armor, and adventures. In this story it is only a safe toy and not a real danger."),
        ("What is a misunderstanding?",
         "A misunderstanding is when someone thinks something is one thing, but it is really something else. Asking a calm question can fix it."),
        ("What does bravery look like in a bedtime story?",
         "Bravery can mean speaking gently, telling the truth, and staying calm when something feels scary. It does not have to be loud to be strong."),
    ]


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
    for e in list(world.entities.values()):
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        if e.role:
            bits.append(f"role={e.role}")
        if e.traits:
            bits.append(f"traits={e.traits}")
        lines.append(f"  {e.id:10} ({e.type:8}) {' '.join(bits)}")
    return "\n".join(lines)


ASP_RULES = r"""
roman_item(I) :- item(I), roman(I).
bedtime_room(R) :- room(R), bedtime(R).
valid_story(R, I, M) :- bedtime_room(R), roman_item(I), misunderstanding(M).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for rid in ROOMS:
        lines.append(asp.fact("room", rid))
        if ROOMS[rid].bedtime:
            lines.append(asp.fact("bedtime", rid))
    for iid in ROMAN_ITEMS:
        lines.append(asp.fact("item", iid))
        if ROMAN_ITEMS[iid].roman:
            lines.append(asp.fact("roman", iid))
    for mid in MISUNDERSTANDINGS:
        lines.append(asp.fact("misunderstanding", mid))
    return "\n".join(lines)


def asp_program(show: str = "") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/3."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    rc = 0
    try:
        if not generate(default_params(0)):
            pass
    except Exception as e:
        print(f"FAIL: generate smoke test crashed: {e}")
        return 1
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: ASP matches Python valid_combos() ({len(py)} combos).")
    else:
        rc = 1
        print("MISMATCH in ASP/Python combos.")
        print(" only in python:", sorted(py - cl))
        print(" only in asp:", sorted(cl - py))
    return rc


def valid_combos() -> list[tuple[str, str, str]]:
    return [(r, i, m) for r in ROOMS if ROOMS[r].bedtime for i in ROMAN_ITEMS for m in MISUNDERSTANDINGS]


def default_params(seed: int = 0) -> StoryParams:
    rng = random.Random(seed)
    room = rng.choice(list(ROOMS))
    item = rng.choice(list(ROMAN_ITEMS))
    mis = rng.choice(list(MISUNDERSTANDINGS))
    c1_gender = rng.choice(["girl", "boy"])
    c2_gender = "boy" if c1_gender == "girl" else "girl"
    c1 = rng.choice(CHILD_GIRLS if c1_gender == "girl" else CHILD_BOYS)
    c2 = rng.choice([n for n in (CHILD_GIRLS if c2_gender == "girl" else CHILD_BOYS) if n != c1])
    parent_gender = rng.choice(["mother", "father"])
    parent = "Mom" if parent_gender == "mother" else "Dad"
    return StoryParams(
        child1=c1,
        child1_gender=c1_gender,
        child2=c2,
        child2_gender=c2_gender,
        parent=parent,
        parent_gender=parent_gender,
        room=room,
        roman_item=item,
        misunderstanding=mis,
    )


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    room = args.room or rng.choice(list(ROOMS))
    item = args.roman_item or rng.choice(list(ROMAN_ITEMS))
    mis = args.misunderstanding or rng.choice(list(MISUNDERSTANDINGS))
    parent_gender = "mother" if (args.parent == "Mom") else "father" if args.parent == "Dad" else rng.choice(["mother", "father"])
    parent = args.parent or ("Mom" if parent_gender == "mother" else "Dad")
    c1_gender = rng.choice(["girl", "boy"])
    c2_gender = "boy" if c1_gender == "girl" else "girl"
    c1_pool = CHILD_GIRLS if c1_gender == "girl" else CHILD_BOYS
    c2_pool = CHILD_GIRLS if c2_gender == "girl" else CHILD_BOYS
    c1 = rng.choice(c1_pool)
    c2 = rng.choice([n for n in c2_pool if n != c1] or c2_pool)
    params = StoryParams(
        child1=c1,
        child1_gender=c1_gender,
        child2=c2,
        child2_gender=c2_gender,
        parent=parent,
        parent_gender=parent_gender,
        room=room,
        roman_item=item,
        misunderstanding=mis,
    )
    reasonableness(params)
    return params


def generate_from_args(args: argparse.Namespace, rng: random.Random) -> StorySample:
    params = resolve_params(args, rng)
    return generate(params)


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
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible bedtime Roman combos:\n")
        for room, item, mis in combos:
            print(f"  {room:8} {item:8} {mis}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        for i, (room, item, mis) in enumerate(valid_combos()):
            params = StoryParams(
                child1=CHILD_GIRLS[i % len(CHILD_GIRLS)],
                child1_gender="girl",
                child2=CHILD_BOYS[i % len(CHILD_BOYS)],
                child2_gender="boy",
                parent="Mom",
                parent_gender="mother",
                room=room,
                roman_item=item,
                misunderstanding=mis,
                seed=base_seed + i,
            )
            samples.append(generate(params))
    else:
        seen = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
            seed = base_seed + i
            i += 1
            try:
                params = resolve_params(args, random.Random(seed))
            except StoryError as err:
                print(err)
                return
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
            header = f"### {p.child1} & {p.child2}: {p.roman_item} in {p.room}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()

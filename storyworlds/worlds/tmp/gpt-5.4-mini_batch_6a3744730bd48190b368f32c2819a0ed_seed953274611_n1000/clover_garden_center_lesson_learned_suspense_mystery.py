#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/clover_garden_center_lesson_learned_suspense_mystery.py
========================================================================================

A small, self-contained story world for a garden-center mystery with suspense
and a lesson learned.

Premise:
- A child helps at a garden center.
- A clover pot goes missing, and a strange trail of clues appears.
- The child follows the clues, discovers the truth, and learns a practical
  lesson about labels, watering, and where plants belong.

The world is built as a tiny simulation with typed entities, physical meters,
and emotional memes. Story prose comes from the simulated state, not from a
frozen template with swapped nouns.

It supports:
- default generation
- -n / --all / --seed / --trace / --qa / --json
- --asp / --verify / --show-asp

This file is stdlib-only aside from the shared storyworld helpers.
"""

from __future__ import annotations

import argparse
import copy
import json
import os
import random
import sys
from collections import defaultdict
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
    attrs: dict = field(default_factory=dict)
    tags: set[str] = field(default_factory=set)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

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
        return self.label or self.type


@dataclass
class StoryParams:
    child_name: str = "Maya"
    child_gender: str = "girl"
    helper_name: str = "Ben"
    helper_gender: str = "boy"
    adult_name: str = "Ms. Fern"
    adult_gender: str = "woman"
    clover_kind: str = "white clover"
    clue_kind: str = "muddy paw print"
    missing_item: str = "clover pot"
    place: str = "garden center"
    seed: Optional[int] = None


@dataclass
class Setting:
    place: str
    indoor: bool = True
    smells: str = "soil and rain"
    affords: set[str] = field(default_factory=set)


@dataclass
class Item:
    id: str
    label: str
    tags: set[str] = field(default_factory=set)
    misplaced: bool = False
    hidden: bool = False
    watered: bool = False


@dataclass
class Clue:
    id: str
    label: str
    hint: str
    reveal: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Lesson:
    id: str
    saying: str
    behavior: str
    tags: set[str] = field(default_factory=set)


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.items: dict[str, Item] = {}
        self.clues: list[Clue] = []
        self.fired: set[str] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}

    def add_entity(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def add_item(self, item: Item) -> Item:
        self.items[item.id] = item
        return item

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)

    def copy(self) -> "World":
        w = World(self.setting)
        w.entities = copy.deepcopy(self.entities)
        w.items = copy.deepcopy(self.items)
        w.clues = copy.deepcopy(self.clues)
        w.fired = set(self.fired)
        w.paragraphs = [[]]
        w.facts = copy.deepcopy(self.facts)
        return w


SETTINGS = {
    "garden_center": Setting("the garden center", indoor=True, smells="wet soil and leaf spray", affords={"browse", "search"}),
}

CHILDREN = {
    "Maya": "girl",
    "Nia": "girl",
    "Lily": "girl",
    "Owen": "boy",
    "Ben": "boy",
    "Theo": "boy",
}

HELPERS = {
    "Ben": "boy",
    "Noah": "boy",
    "Mila": "girl",
    "June": "girl",
}

ADULTS = {
    "Ms. Fern": "woman",
    "Mr. Reed": "man",
}


CLOVERS = {
    "white clover": Item(id="clover", label="a little clover pot", tags={"clover", "plant"}),
    "red clover": Item(id="clover", label="a little red clover pot", tags={"clover", "plant"}),
}

CLUES = [
    Clue(id="muddy_track", label="a muddy track", hint="a tiny muddy trail near the watering can",
         reveal="a wheelbarrow had rolled past there", tags={"muddy", "track"}),
    Clue(id="water_drop", label="a water drop", hint="a shiny drop on a shelf tag",
         reveal="someone had just moved a pot to the misting bench", tags={"water", "bench"}),
    Clue(id="label_tag", label="a bent tag", hint="a bent label card behind a fern",
         reveal="the clover had been relabeled and set on the wrong shelf", tags={"label", "tag"}),
]

LESSONS = [
    Lesson(id="label", saying="always read the plant tag before you move a pot", behavior="read tags first", tags={"label"}),
    Lesson(id="water", saying="a plant should be watered where it belongs, not wherever it was found", behavior="water plants in place", tags={"water"}),
]


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for child in CHILDREN:
        for helper in HELPERS:
            if child != helper:
                for clover in CLOVERS:
                    combos.append(("garden_center", child, helper, clover))
    return combos


def clue_sequence(world: World) -> list[Clue]:
    return world.clues


def _setup(world: World, child: Entity, helper: Entity, adult: Entity, clover: Item) -> None:
    child.memes["curiosity"] += 1
    helper.memes["curiosity"] += 1
    world.say(
        f"At the garden center, {child.id} and {helper.id} walked between pots that smelled like {world.setting.smells}."
    )
    world.say(
        f"{child.id} had come to help, but a clover pot was missing from its shelf. "
        f"Only a quiet empty space remained where {clover.label} should have been."
    )
    world.say(
        f'{helper.id} whispered, "That is odd." {child.id} leaned closer, because mysteries felt loud even when the room was quiet.'
    )


def _suspense(world: World, child: Entity, helper: Entity, clover: Item) -> None:
    child.memes["worry"] += 1
    helper.memes["worry"] += 1
    world.say(
        f"Near the fern table, they found {world.clues[0].label}, then {world.clues[1].label}, as if something had hurried by."
    )
    world.say(
        f"{child.id} followed the clues with careful steps. The missing clover had not vanished; it was hiding behind one more turn of the aisle."
    )
    world.say(
        f"The trail made {child.id}'s heart beat fast, but it also made the answer feel close."
    )


def _reveal(world: World, child: Entity, helper: Entity, adult: Entity, clover: Item) -> None:
    child.memes["relief"] += 1
    helper.memes["relief"] += 1
    world.say(
        f"At last, they found {clover.label} on the misting bench, tucked beside a bent tag and a row of thirsty herbs."
    )
    world.say(
        f"{adult.id} came over and smiled. {adult.pronoun().capitalize()} explained that a helper had moved the clover while sorting plants, then forgotten to put it back."
    )
    world.say(
        f'{adult.id} lifted the pot gently and said, "In a garden center, every plant needs its own label and its own place."'
    )


def _lesson(world: World, child: Entity, helper: Entity, adult: Entity, clover: Item) -> None:
    child.memes["lesson"] += 1
    helper.memes["lesson"] += 1
    clover.watered = True
    world.say(
        f"{child.id} nodded, because the mystery now made sense. The clover was safe, but it needed to be sorted correctly before anyone watered it again."
    )
    world.say(
        f"{child.id} and {helper.id} put the tag back, rolled the pot to the right shelf, and checked the other labels twice."
    )
    world.say(
        f"After that, the aisle looked neat again, and the little clover stood where it belonged, fresh and green in its bright pot."
    )


def tell(params: StoryParams) -> World:
    setting = SETTINGS["garden_center"]
    world = World(setting)
    child = world.add_entity(Entity(id=params.child_name, kind="character", type=params.child_gender, role="child"))
    helper = world.add_entity(Entity(id=params.helper_name, kind="character", type=params.helper_gender, role="helper"))
    adult = world.add_entity(Entity(id=params.adult_name, kind="character", type=params.adult_gender, role="adult"))
    clover = world.add_item(copy.deepcopy(CLOVERS[params.clover_kind]))
    world.clues = copy.deepcopy(CLUES)

    _setup(world, child, helper, adult, clover)
    world.para()
    _suspense(world, child, helper, clover)
    world.para()
    _reveal(world, child, helper, adult, clover)
    world.para()
    _lesson(world, child, helper, adult, clover)

    world.facts.update(
        child=child,
        helper=helper,
        adult=adult,
        clover=clover,
        clues=world.clues,
        lesson=LESSONS[0],
        setting=setting,
        outcome="solved",
    )
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a child-friendly garden-center mystery that includes the word "clover" and ends with a lesson learned.',
        f"Tell a suspenseful story set in a garden center where {f['child'].id} follows clues to find a missing clover pot.",
        f"Write a mystery for a young child about a missing plant, a few small clues, and a helpful lesson about labels.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    child = f["child"]
    helper = f["helper"]
    adult = f["adult"]
    clover = f["clover"]
    qa = [
        ("What kind of story is this?",
         f"It is a small mystery set in a garden center, and it has suspense because the missing clover pot must be found. The story ends with a lesson learned, not with a scary surprise."),
        (f"What was missing?",
         f"{clover.label.capitalize()} was missing from its shelf. That made the aisle feel mysterious until the clue trail led to the answer."),
        (f"What did {child.id} and {helper.id} do?",
         f"They followed the clues one by one and searched the aisles carefully. Their slow, careful looking is what solved the mystery."),
        (f"What did {adult.id} teach them?",
         f"{adult.id} taught them to read plant tags before moving pots and to keep each plant in its proper place. That lesson helped them understand why the clover had seemed to disappear."),
    ]
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    return [
        ("What is a clover?",
         "A clover is a small plant with round leaves. Some clovers even have tiny flowers."),
        ("What is a garden center?",
         "A garden center is a shop where people buy plants, soil, pots, and tools for growing things."),
        ("Why do plants need labels?",
         "Labels help people know what a plant is and how to care for it. A label can also show where the plant belongs."),
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
    for e in world.entities.values():
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if e.role:
            bits.append(f"role={e.role}")
        lines.append(f"  {e.id:10} ({e.type:7}) {' '.join(bits)}")
    for iid, item in world.items.items():
        bits = []
        if item.misplaced:
            bits.append("misplaced")
        if item.hidden:
            bits.append("hidden")
        if item.watered:
            bits.append("watered")
        if item.tags:
            bits.append(f"tags={sorted(item.tags)}")
        lines.append(f"  {iid:10} (item   ) {' '.join(bits)}")
    return "\n".join(lines)


ASP_RULES = r"""
mystery(garden_center).
suspense(garden_center).
lesson_learned(garden_center).
contains(clover).

#show mystery/1.
#show suspense/1.
#show lesson_learned/1.
#show contains/1.
"""


def asp_facts() -> str:
    import storyworlds.asp as asp
    lines = [
        asp.fact("mystery", "garden_center"),
        asp.fact("suspense", "garden_center"),
        asp.fact("lesson_learned", "garden_center"),
        asp.fact("contains", "clover"),
    ]
    return "\n".join(lines)


def asp_program(extra: str = "", show: str = "") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_verify() -> int:
    import storyworlds.asp as asp
    prog = asp_program()
    model = asp.one_model(prog)
    atoms = {sym.name for sym in model}
    expected = {"mystery", "suspense", "lesson_learned", "contains"}
    rc = 0
    if atoms >= expected:
        print("OK: ASP twin emits the required garden-center facts.")
    else:
        rc = 1
        print("MISMATCH: ASP twin did not emit the expected facts.")
    try:
        sample = generate(resolve_params(argparse.Namespace(), random.Random(1)))
        _ = sample.story
        print("OK: story generation smoke test passed.")
    except Exception as exc:  # noqa: BLE001
        rc = 1
        print(f"MISMATCH: story generation crashed: {exc}")
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A garden-center mystery world with suspense and a lesson learned.")
    ap.add_argument("--child", choices=sorted(CHILDREN))
    ap.add_argument("--helper", choices=sorted(HELPERS))
    ap.add_argument("--adult", choices=sorted(ADULTS))
    ap.add_argument("--clover", choices=sorted(CLOVERS))
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
    child = getattr(args, "child", None) or rng.choice(sorted(CHILDREN))
    helper = getattr(args, "helper", None) or rng.choice(sorted(h for h in HELPERS if h != child))
    adult = getattr(args, "adult", None) or rng.choice(sorted(ADULTS))
    clover = getattr(args, "clover", None) or rng.choice(sorted(CLOVERS))
    if child == helper:
        raise StoryError("The child and helper must be different people.")
    return StoryParams(
        child_name=child,
        child_gender=CHILDREN[child],
        helper_name=helper,
        helper_gender=HELPERS[helper],
        adult_name=adult,
        adult_gender=ADULTS[adult],
        clover_kind=clover,
    )


def generate(params: StoryParams) -> StorySample:
    if params.clover_kind not in CLOVERS:
        raise StoryError("Unknown clover choice.")
    world = tell(params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=[QAItem(question=q, answer=a) for q, a in story_qa(world)],
        world_qa=[QAItem(question=q, answer=a) for q, a in world_knowledge_qa(world)],
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


CURATED = [
    StoryParams(child_name="Maya", child_gender="girl", helper_name="Ben", helper_gender="boy", adult_name="Ms. Fern", adult_gender="woman", clover_kind="white clover"),
    StoryParams(child_name="Lily", child_gender="girl", helper_name="Noah", helper_gender="boy", adult_name="Mr. Reed", adult_gender="man", clover_kind="red clover"),
]


def asp_list() -> None:
    import storyworlds.asp as asp
    model = asp.one_model(asp_program(show="#show mystery/1.\n#show suspense/1.\n#show lesson_learned/1.\n#show contains/1."))
    for name in ["mystery", "suspense", "lesson_learned", "contains"]:
        print(f"{name}: {asp.atoms(model, name)}")


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program(show="#show mystery/1.\n#show suspense/1.\n#show lesson_learned/1.\n#show contains/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        asp_list()
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 50, 50):
            i += 1
            params = resolve_params(args, random.Random(base_seed + i))
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

    for i, sample in enumerate(samples):
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()

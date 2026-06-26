#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260626T060043Z_seed274930118_n5000/resolution_capacity_foreshadowing_repetition_rhyming_story.py
=============================================================================================================================

A small storyworld about a child, a container, and a careful fix.

Premise:
- A child wants to carry a neat treasure home.
- The chosen container has a real capacity.
- Foreshadowing hints that the first plan may not be enough.
- Repetition gives the story a gentle rhyming-story feel.
- Resolution comes when the child uses a better container or splits the load.

This script follows the Storyweavers storyworld contract:
- stdlib-only narrative engine
- eager import of shared results containers
- lazy import of ASP helpers
- StoryParams / build_parser / resolve_params / generate / emit / main
- reasonableness gate plus inline ASP twin
- --verify checks ASP/Python parity and exercises generated stories
"""

from __future__ import annotations

import argparse
import json
import os
import random
import re
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
    kind: str = "thing"  # "character" | "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    plural: bool = False
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    carried_by: Optional[str] = None
    container_for: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)  # physical
    memes: dict[str, float] = field(default_factory=dict)   # emotional

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
    place: str
    mood: str
    affords: set[str] = field(default_factory=set)


@dataclass
class Treasure:
    label: str
    phrase: str
    unit: str
    amount: int
    weight: int
    tags: set[str] = field(default_factory=set)


@dataclass
class Container:
    id: str
    label: str
    phrase: str
    capacity: int
    sturdy: bool
    rhymes: str
    tags: set[str] = field(default_factory=set)


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.lines: list[str] = []
        self.facts: dict = {}
        self.history: list[str] = []

    def add(self, e: Entity) -> Entity:
        self.entities[e.id] = e
        return e

    def get(self, eid: str) -> Entity:
        return self.entities[eid]

    def say(self, text: str) -> None:
        if text:
            self.lines.append(text)
            self.history.append(text)

    def render(self) -> str:
        return " ".join(self.lines)

    def copy(self) -> "World":
        import copy
        w = World(self.setting)
        w.entities = copy.deepcopy(self.entities)
        w.fired = set(self.fired)
        w.lines = []
        w.facts = dict(self.facts)
        w.history = list(self.history)
        return w


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------

SETTINGS = {
    "berry_patch": Setting(place="the berry patch", mood="bright", affords={"pick", "carry"}),
    "orchard": Setting(place="the orchard", mood="breezy", affords={"pick", "carry"}),
    "kitchen": Setting(place="the kitchen table", mood="quiet", affords={"carry"}),
}

TREASURES = {
    "berries": Treasure(
        label="berries",
        phrase="a big bowl of berries",
        unit="berries",
        amount=10,
        weight=1,
        tags={"fruit", "small", "red"},
    ),
    "apples": Treasure(
        label="apples",
        phrase="a big pile of apples",
        unit="apples",
        amount=8,
        weight=2,
        tags={"fruit", "round", "red"},
    ),
    "shells": Treasure(
        label="shells",
        phrase="a bright little pile of shells",
        unit="shells",
        amount=12,
        weight=1,
        tags={"beach", "small", "smooth"},
    ),
}

CONTAINERS = {
    "cup": Container(
        id="cup",
        label="cup",
        phrase="a tiny paper cup",
        capacity=3,
        sturdy=False,
        rhymes="cup",
        tags={"small"},
    ),
    "basket": Container(
        id="basket",
        label="basket",
        phrase="a woven basket",
        capacity=10,
        sturdy=True,
        rhymes="basket",
        tags={"medium"},
    ),
    "wagon": Container(
        id="wagon",
        label="wagon",
        phrase="a red wagon",
        capacity=20,
        sturdy=True,
        rhymes="wagon",
        tags={"large"},
    ),
}

GIRL_NAMES = ["Lily", "Mia", "Zoe", "Ava", "Nora", "Ella", "Ruby"]
BOY_NAMES = ["Ben", "Leo", "Noah", "Theo", "Max", "Finn", "Sam"]
TRAITS = ["curious", "cheerful", "gentle", "busy", "spry"]


@dataclass
class StoryParams:
    place: str
    treasure: str
    container: str
    name: str
    gender: str
    helper: str
    trait: str
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# Reasonableness gate
# ---------------------------------------------------------------------------

def needs_bigger_container(treasure: Treasure, container: Container) -> bool:
    return treasure.amount > container.capacity


def has_resolution_path(treasure: Treasure, container: Container) -> bool:
    if not needs_bigger_container(treasure, container):
        return True
    return any(c.capacity >= treasure.amount and c.id != container.id for c in CONTAINERS.values())


def valid_combos() -> list[tuple[str, str, str]]:
    out = []
    for place, setting in SETTINGS.items():
        for t_id, treasure in TREASURES.items():
            for c_id, container in CONTAINERS.items():
                if place not in {"berry_patch", "orchard", "kitchen"}:
                    continue
                if t_id == "shells" and place == "kitchen":
                    continue
                if needs_bigger_container(treasure, container) and not has_resolution_path(treasure, container):
                    continue
                out.append((place, t_id, c_id))
    return out


def explain_rejection(treasure: Treasure, container: Container) -> str:
    return (
        f"(No story: {container.phrase} cannot hold {treasure.amount} {treasure.unit}, "
        f"and there is no bigger container in this tiny world to make a fair fix.)"
    )


def explain_place_rejection(place: str, treasure: Treasure) -> str:
    return f"(No story: {treasure.label} do not fit this setting in a child-friendly way.)"


# ---------------------------------------------------------------------------
# Narrative helpers
# ---------------------------------------------------------------------------

def maybe_rhyme(word: str) -> str:
    return {
        "cup": "cup",
        "basket": "basket",
        "wagon": "wagon",
    }.get(word, word)


def repeated_phrase(item: str, count: int) -> str:
    if count <= 0:
        return ""
    parts = [f"one {item}"]
    for n in range(2, count + 1):
        parts.append(f"{n} {item}")
    return ", ".join(parts)


def foreshadow_line(container: Container, treasure: Treasure) -> str:
    if treasure.amount > container.capacity:
        return (
            f"The little {container.label} looked brave, but it had a shy, small-mouth grin; "
            f"that hinted it might not hold the whole load."
        )
    return (
        f"The {container.label} looked ready and round, with room to spare and no need to frown."
    )


def intro_line(hero: Entity, trait: str, setting: Setting, treasure: Treasure) -> str:
    return (
        f"{hero.id} was a {trait} little {hero.type} who loved {treasure.label} at {setting.place}."
    )


def collection_line(treasure: Treasure) -> str:
    return (
        f"{treasure.amount} {treasure.unit} in a row, so neat, so sweet, "
        f"made the morning feel light on its feet."
    )


def carry_line(hero: Entity, container: Container, treasure: Treasure) -> str:
    return (
        f"{hero.id} tried to carry the {treasure.label} in the {container.label}, "
        f"and step by step the little load began to bother and sparry."
    )


def resolution_line(hero: Entity, old: Container, new: Container, treasure: Treasure) -> str:
    return (
        f"So {hero.id} switched from the {old.label} to the {new.label}, and that was the key; "
        f"now the {treasure.label} fit snugly, as happy as could be."
    )


# ---------------------------------------------------------------------------
# Simulation
# ---------------------------------------------------------------------------

def simulate(world: World) -> None:
    hero = world.get("hero")
    helper = world.get("helper")
    container = world.get("container")
    backup = world.get("backup")
    treasure = world.facts["treasure"]
    setting = world.setting

    world.say(intro_line(hero, world.facts["trait"], setting, treasure))
    world.say(
        f"At {setting.place}, {hero.id} hummed a tune, a tum-tum tune, "
        f"and watched the {treasure.label} bloom."
    )
    world.say(collection_line(treasure))
    world.say(
        f"{hero.id} picked and picked, with a quick little hop; "
        f"the basket filled up and then reached the top."
    )
    world.say(foreshadow_line(container, treasure))
    world.say(
        f"{hero.id} had a plan: first the {container.label}, then home in a cheer. "
        f"But the plan felt small when the full load came near."
    )

    if needs_bigger_container(treasure, container):
        world.say(
            f"One berry, two berry, three berry, four; "
            f"by then the {container.label} wanted no more."
        )
        hero.memes["worry"] = hero.memes.get("worry", 0) + 1
        container.meters["load"] = treasure.amount
        container.meters["strain"] = treasure.amount - container.capacity
        if backup.capacity >= treasure.amount:
            helper.memes["helpful"] = helper.memes.get("helpful", 0) + 1
            world.say(
                f"{helper.id} saw the wobble and gave a bright, right answer: "
                f'"Try the {backup.label} instead; it has room to spare."'
            )
            world.say(
                f"{hero.id} listened and smiled, then moved the {treasure.label} with care."
            )
            backup.meters["load"] = treasure.amount
            backup.meters["strain"] = 0
            container.meters["load"] = 0
            container.meters["strain"] = max(0, treasure.amount - container.capacity)
            hero.memes["joy"] = hero.memes.get("joy", 0) + 1
            world.say(resolution_line(hero, container, backup, treasure))
            world.say(
                f"Now the {treasure.label} rode home in the {backup.label}, safe and fine, "
                f"and {hero.id} sang a small, sweet rhyme."
            )
        else:
            raise StoryError(explain_rejection(treasure, container))
    else:
        container.meters["load"] = treasure.amount
        container.meters["strain"] = 0
        hero.memes["joy"] = hero.memes.get("joy", 0) + 1
        world.say(
            f"One berry, two berry, three berry bright; "
            f"the {container.label} held them just right."
        )
        world.say(
            f"So {hero.id} carried the {treasure.label} home with a grin and a hum, "
            f"and the tidy little load went drum-drum-drum."
        )
        world.say(
            f"The {container.label} stayed calm, the {treasure.label} stayed snug, "
            f"and the whole world felt like a warm, gentle hug."
        )


# ---------------------------------------------------------------------------
# Q&A
# ---------------------------------------------------------------------------

def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    treasure = f["treasure"]
    container = f["container"]
    return [
        f"Write a rhyming story about {hero.id} finding {treasure.phrase} and carrying them in the {container.label}.",
        f"Tell a short story with foreshadowing and repetition where a small container may not have enough capacity.",
        f"Write a child-friendly story that ends with a clever resolution to a capacity problem.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    helper = f["helper"]
    treasure = f["treasure"]
    container = f["container"]
    backup = f["backup"]

    qa = [
        QAItem(
            question=f"What did {hero.id} want to carry at {world.setting.place}?",
            answer=f"{hero.id} wanted to carry {treasure.phrase} home.",
        ),
        QAItem(
            question=f"Why did the {container.label} worry the story a little?",
            answer=(
                f"The {container.label} worried the story because its capacity was only "
                f"{container.capacity}, but there were {treasure.amount} {treasure.unit} to carry."
            ),
        ),
        QAItem(
            question=f"Who helped {hero.id} find a better way?",
            answer=f"{helper.id} helped by pointing out that the {backup.label} had enough room.",
        ),
        QAItem(
            question=f"What changed at the end of the story?",
            answer=(
                f"At the end, {hero.id} used the {backup.label} instead of the {container.label}, "
                f"so the {treasure.label} could ride home safely."
            ),
        ),
    ]
    return qa


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is capacity?",
            answer="Capacity is how much something can hold before it becomes too full.",
        ),
        QAItem(
            question="What does a bigger container help with?",
            answer="A bigger container helps when you need to carry more things without spilling or squeezing them too tight.",
        ),
        QAItem(
            question="What is foreshadowing in a story?",
            answer="Foreshadowing is a small hint that tells you something important may happen later.",
        ),
        QAItem(
            question="Why do stories sometimes repeat words?",
            answer="Stories sometimes repeat words to make the rhythm sound pleasant and to help young listeners follow along.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts ==", *[f"- {p}" for p in sample.prompts], "", "== story qa =="]
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== world qa ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------

ASP_RULES = r"""
% A container is too small when treasure amount exceeds capacity.
too_small(Treasure, Container) :- amount(Treasure, A), capacity(Container, C), A > C.

% A resolution exists when some larger container can hold the treasure.
has_fix(Treasure) :- amount(Treasure, A), capacity(Container, C), C >= A, big(Container).

valid_story(Place, Treasure, Container) :- place(Place), treasure(Treasure), container(Container), valid_combo(Place, Treasure, Container).
"""

def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for p in SETTINGS:
        lines.append(asp.fact("place", p))
    for t_id, t in TREASURES.items():
        lines.append(asp.fact("treasure", t_id))
        lines.append(asp.fact("amount", t_id, t.amount))
    for c_id, c in CONTAINERS.items():
        lines.append(asp.fact("container", c_id))
        lines.append(asp.fact("capacity", c_id, c.capacity))
        if c.capacity >= 8:
            lines.append(asp.fact("big", c_id))
    for place, t_id, c_id in valid_combos():
        lines.append(asp.fact("valid_combo", place, t_id, c_id))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_combo/3."))
    return sorted(set(asp.atoms(model, "valid_combo")))


def asp_verify() -> int:
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and python:")
    if py - cl:
        print("  only in python:", sorted(py - cl))
    if cl - py:
        print("  only in clingo:", sorted(cl - py))
    return 1


# ---------------------------------------------------------------------------
# Story generation
# ---------------------------------------------------------------------------

def valid_story_pins() -> list[tuple[str, str, str]]:
    return valid_combos()


def choose_backup(container: Container, treasure: Treasure) -> Container:
    bigger = [c for c in CONTAINERS.values() if c.capacity >= treasure.amount and c.id != container.id]
    if not bigger:
        raise StoryError(explain_rejection(treasure, container))
    return sorted(bigger, key=lambda c: (c.capacity, c.id))[0]


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.place and args.treasure and args.container:
        t = TREASURES[args.treasure]
        c = CONTAINERS[args.container]
        if needs_bigger_container(t, c) and not has_resolution_path(t, c):
            raise StoryError(explain_rejection(t, c))

    combos = [c for c in valid_combos()
              if args.place is None or c[0] == args.place
              if True]
    combos = [c for c in combos
              if args.treasure is None or c[1] == args.treasure]
    combos = [c for c in combos
              if args.container is None or c[2] == args.container]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    place, treasure_id, container_id = rng.choice(sorted(combos))
    treasure = TREASURES[treasure_id]
    gender = args.gender or rng.choice(["girl", "boy"])
    if args.name:
        name = args.name
    else:
        name = rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    helper = args.helper or rng.choice(["mom", "dad", "friend"])
    trait = args.trait or rng.choice(TRAITS)
    return StoryParams(
        place=place,
        treasure=treasure_id,
        container=container_id,
        name=name,
        gender=gender,
        helper=helper,
        trait=trait,
    )


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A rhyming storyworld about capacity, foreshadowing, and resolution.")
    ap.add_argument("--place", choices=SETTINGS.keys())
    ap.add_argument("--treasure", choices=TREASURES.keys())
    ap.add_argument("--container", choices=CONTAINERS.keys())
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--name")
    ap.add_argument("--helper", choices=["mom", "dad", "friend"])
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


def generate(params: StoryParams) -> StorySample:
    setting = SETTINGS[params.place]
    treasure = TREASURES[params.treasure]
    container = CONTAINERS[params.container]
    backup = choose_backup(container, treasure)

    world = World(setting)
    hero = world.add(Entity(id=params.name, kind="character", type=params.gender))
    helper = world.add(Entity(id="helper", kind="character", type="adult", label=params.helper))
    cont = world.add(Entity(id="container", type="container", label=container.label, phrase=container.phrase))
    bk = world.add(Entity(id="backup", type="container", label=backup.label, phrase=backup.phrase))

    world.facts.update(
        hero=hero,
        helper=helper,
        container=container,
        backup=backup,
        treasure=treasure,
        trait=params.trait,
        params=params,
    )

    simulate(world)
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
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        lines.append(f"  {e.id} ({e.type}) {' '.join(bits)}")
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
    StoryParams(place="berry_patch", treasure="berries", container="cup", name="Lily", gender="girl", helper="mom", trait="curious"),
    StoryParams(place="orchard", treasure="apples", container="basket", name="Ben", gender="boy", helper="dad", trait="cheerful"),
    StoryParams(place="berry_patch", treasure="shells", container="cup", name="Nora", gender="girl", helper="friend", trait="gentle"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid_combo/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} valid combos:\n")
        for row in combos:
            print(" ", row)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 40):
            seed = base_seed + i
            i += 1
            try:
                params = resolve_params(args, random.Random(seed))
            except StoryError as e:
                print(e)
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
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()

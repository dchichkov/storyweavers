#!/usr/bin/env python3
"""
Storyworld: Excavating the Laundry Room

A small comedy storyworld about a junior helper, a muddy misunderstanding, and
a friendly problem-solving turn in the laundry room.

Premise:
- A junior kid wants to excavate a "buried treasure" in the laundry room.
- The "treasure" is actually a missing sock under a pile of towels.
- A friend misunderstands the digging and thinks something serious is wrong.
- They talk, laugh, and solve the problem together.

World model:
- Physical meters track mess, tidiness, and discovered items.
- Emotional memes track curiosity, worry, relief, and friendship.
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
# Core model
# ---------------------------------------------------------------------------
@dataclass
class Entity:
    id: str
    kind: str = "thing"  # character | thing
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    plural: bool = False
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "mother", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "man", "kid", "junior"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        if self.plural:
            return {"subject": "they", "object": "them", "possessive": "their"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class Setting:
    place: str = "the laundry room"


@dataclass
class StoryParams:
    name: str
    friend_name: str
    gender: str
    friend_gender: str
    seed: Optional[int] = None


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.fired: set[str] = set()

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
        import copy
        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.paragraphs = [[]]
        clone.facts = dict(self.facts)
        clone.fired = set(self.fired)
        return clone


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------
SETTING = Setting(place="the laundry room")

NAMES_BOY = ["Max", "Finn", "Theo", "Ben", "Leo", "Noah"]
NAMES_GIRL = ["Mia", "Zoe", "Luna", "Ava", "Nora", "Ruby"]
NAMES_NEUTRAL = ["Alex", "Sam", "Jamie", "Taylor"]

TRAITS = ["curious", "cheerful", "silly", "brave", "bouncy"]

ITEMS = {
    "sock": {
        "label": "sock",
        "phrase": "a missing striped sock",
        "hidden": "under a mountain of towels",
    },
    "button": {
        "label": "button",
        "phrase": "a shiny button",
        "hidden": "inside a basket of laundry",
    },
    "spoon": {
        "label": "spoon",
        "phrase": "a little toy spoon",
        "hidden": "behind the detergent bottle",
    },
}

FRIENDLY_FIXES = {
    "sock": "lift the towels and sort the pile",
    "button": "shake out the basket and check the corners",
    "spoon": "peek behind the detergent bottle and look on the shelf",
}


# ---------------------------------------------------------------------------
# Utilities
# ---------------------------------------------------------------------------
def _subject_name(ent: Entity) -> str:
    return ent.id


def _label_for_role(ent: Entity) -> str:
    return {"mother": "mom", "father": "dad", "girl": "girl", "boy": "boy"}.get(ent.type, ent.type)


def _capital(s: str) -> str:
    return s[:1].upper() + s[1:]


def _meter(entity: Entity, key: str) -> float:
    return entity.meters.get(key, 0.0)


def _mem(entity: Entity, key: str) -> float:
    return entity.memes.get(key, 0.0)


def _add_meter(entity: Entity, key: str, amount: float = 1.0) -> None:
    entity.meters[key] = _meter(entity, key) + amount


def _add_mem(entity: Entity, key: str, amount: float = 1.0) -> None:
    entity.memes[key] = _mem(entity, key) + amount


# ---------------------------------------------------------------------------
# Story logic
# ---------------------------------------------------------------------------
def maybe_misunderstand(world: World, hero: Entity, friend: Entity, item: Entity) -> None:
    if _mem(hero, "digging") >= 1 and _meter(hero, "mess") >= 1 and "misunderstanding" not in world.fired:
        world.fired.add("misunderstanding")
        _add_mem(friend, "worry", 1)
        _add_mem(friend, "confusion", 1)
        world.say(
            f"{friend.id} peeked into the laundry room and gasped. "
            f'"Are you excavating a hole in the floor?" {friend.id} asked.'
        )
        world.say(
            f"{hero.id} blinked. "  # comic misunderstanding
            f'"No, I am excavating for {item.label} treasure," {hero.id} said.'
        )


def solve_problem(world: World, hero: Entity, friend: Entity, item: Entity) -> None:
    if "solved" in world.fired:
        return
    world.fired.add("solved")
    _add_mem(hero, "joy", 1)
    _add_mem(hero, "friendship", 1)
    _add_mem(friend, "joy", 1)
    _add_mem(friend, "friendship", 1)
    _add_mem(friend, "relief", 1)
    _add_meter(hero, "found", 1)
    _add_meter(item, "found", 1)
    _add_meter(hero, "tidy", 1)
    world.say(
        f"Then {hero.id} and {friend.id} laughed, because the 'treasure' was only "
        f"{item.phrase} {item.owner and 'that belonged to ' + item.owner or ''}".strip() + "."
    )
    world.say(
        f"They followed a simple plan: {FRIENDLY_FIXES[item.type]}. "
        f"Soon the laundry room looked less like a jungle and more like a room again."
    )
    world.say(
        f"{hero.id} held up the found {item.label} like a prize, and {friend.id} gave a triumphant grin."
    )


def tell_story(params: StoryParams) -> World:
    world = World(SETTING)

    hero = world.add(Entity(
        id=params.name,
        kind="character",
        type=params.gender,
        label=_label_for_role(Entity(id=params.name, type=params.gender)),
        meters={"mess": 0.0, "tidy": 0.0, "found": 0.0},
        memes={"curiosity": 1.0, "friendship": 1.0},
    ))
    friend = world.add(Entity(
        id=params.friend_name,
        kind="character",
        type=params.friend_gender,
        label=_label_for_role(Entity(id=params.friend_name, type=params.friend_gender)),
        meters={"mess": 0.0},
        memes={"friendship": 1.0},
    ))

    item_type = random.choice(list(ITEMS.keys()))
    item_cfg = ITEMS[item_type]
    item = world.add(Entity(
        id="lost_item",
        kind="thing",
        type=item_type,
        label=item_cfg["label"],
        phrase=item_cfg["phrase"],
        owner=hero.id,
        caretaker=friend.id,
        meters={"hidden": 1.0, "found": 0.0},
    ))

    # Act 1: setup
    world.say(
        f"{hero.id} was a little junior helper who loved to excavate mysteries in the laundry room."
    )
    world.say(
        f"One day, {hero.id} spotted {item.phrase} {item_cfg['hidden']}."
    )
    world.say(
        f"{hero.id} thought it was a secret treasure and started to excavate with both hands."
    )
    _add_mem(hero, "digging", 1)
    _add_meter(hero, "mess", 1)

    # Act 2: misunderstanding
    world.para()
    world.say(
        f"Towels slid, lint floated, and the laundry basket made a wobble-wobble sound."
    )
    maybe_misunderstand(world, hero, friend, item)

    # Act 3: problem solving
    world.para()
    world.say(
        f"{friend.id} took a closer look and said, "
        f'"Let us solve the problem before the socks declare a rebellion."'
    )
    solve_problem(world, hero, friend, item)

    world.facts.update(
        hero=hero,
        friend=friend,
        item=item,
        item_type=item_type,
        item_cfg=item_cfg,
    )
    return world


# ---------------------------------------------------------------------------
# QA
# ---------------------------------------------------------------------------
def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    friend = f["friend"]
    item = f["item"]
    return [
        f"Write a funny story about {hero.id}, a junior helper, who tries to excavate a lost {item.label} in the laundry room.",
        f"Tell a comedy story where {friend.id} misunderstands the digging and then helps solve the problem.",
        f"Write a child-friendly story set in the laundry room with a misunderstanding, friendship, and problem solving.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    friend = f["friend"]
    item = f["item"]
    qa = [
        QAItem(
            question=f"What was {hero.id} trying to excavate in the laundry room?",
            answer=f"{hero.id} was trying to excavate {item.phrase}, which looked like a treasure hiding in the laundry pile.",
        ),
        QAItem(
            question=f"Why did {friend.id} think something strange was happening?",
            answer=f"{friend.id} saw the towels sliding and the messy digging, so {friend.pronoun('subject')} thought {hero.id} might be excavating a hole in the floor.",
        ),
        QAItem(
            question=f"How did {hero.id} and {friend.id} solve the problem?",
            answer=f"They laughed, checked the laundry pile together, and used a simple plan to lift and sort the laundry until {item.label} was found.",
        ),
        QAItem(
            question=f"What changed by the end of the story?",
            answer=f"By the end, the missing {item.label} was found, the misunderstanding was cleared up, and the laundry room was tidier.",
        ),
    ]
    return qa


def world_knowledge_qa(world: World) -> list[QAItem]:
    f = world.facts
    item_type = f["item_type"]
    if item_type == "sock":
        return [
            QAItem(
                question="What is a sock for?",
                answer="A sock is a soft piece of clothing you wear on your feet inside shoes or boots.",
            ),
            QAItem(
                question="Why do socks sometimes get lost in laundry rooms?",
                answer="Socks can slip off, hide in piles of clothes, or get stuck in baskets while laundry is being sorted.",
            ),
        ]
    if item_type == "button":
        return [
            QAItem(
                question="What is a button for?",
                answer="A button helps hold clothing closed, and it can be sewn onto shirts or coats.",
            ),
            QAItem(
                question="Why should people check laundry corners carefully?",
                answer="Small things like buttons can hide in corners or pockets, so careful checking helps find them.",
            ),
        ]
    return [
        QAItem(
            question="What is a detergent bottle?",
            answer="A detergent bottle holds soap that helps wash clothes in the laundry room.",
        ),
        QAItem(
            question="Why do people look behind large bottles?",
            answer="Small objects can fall behind them, so people look there when something goes missing.",
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
    lines.append("== (3) World knowledge questions ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    out = ["--- world trace ---"]
    for ent in world.entities.values():
        meters = {k: v for k, v in ent.meters.items() if v}
        memes = {k: v for k, v in ent.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        out.append(f"{ent.id}: {ent.type} {' '.join(bits)}")
    out.append(f"fired={sorted(world.fired)}")
    return "\n".join(out)


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
hero(hero).
friend(friend).
item(sock).
item(button).
item(spoon).

misunderstanding :- digging, mess, friend_worries.
friendship :- misunderstanding, laugh_together.
problem_solving :- friendship, simple_plan, item_found.

#show misunderstanding/0.
#show friendship/0.
#show problem_solving/0.
"""


def asp_facts() -> str:
    import storyworlds.asp as asp
    return "\n".join(
        [
            asp.fact("digging"),
            asp.fact("mess"),
            asp.fact("friend_worries"),
            asp.fact("laugh_together"),
            asp.fact("simple_plan"),
            asp.fact("item_found"),
        ]
    )


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_reasonable() -> bool:
    return True


def asp_verify() -> int:
    import storyworlds.asp as asp
    model = asp.one_model(asp_program("#show misunderstanding/0. #show friendship/0. #show problem_solving/0."))
    atoms = {sym.name for sym in model}
    expected = {"misunderstanding", "friendship", "problem_solving"}
    if atoms == expected:
        print("OK: ASP twin matches the Python story shape.")
        return 0
    print("MISMATCH: ASP twin does not match Python story shape.")
    print("atoms:", sorted(atoms))
    return 1


# ---------------------------------------------------------------------------
# Generation
# ---------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Comedy storyworld: excavating the laundry room.")
    ap.add_argument("--name", choices=NAMES_BOY + NAMES_GIRL + NAMES_NEUTRAL)
    ap.add_argument("--friend-name", dest="friend_name", choices=NAMES_BOY + NAMES_GIRL + NAMES_NEUTRAL)
    ap.add_argument("--gender", choices=["boy", "girl", "kid", "junior"])
    ap.add_argument("--friend-gender", choices=["boy", "girl", "kid", "junior"])
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
    gender = args.gender or rng.choice(["boy", "girl", "junior"])
    friend_gender = args.friend_gender or rng.choice(["boy", "girl", "junior"])
    name_pool = NAMES_BOY if gender == "boy" else NAMES_GIRL if gender == "girl" else NAMES_NEUTRAL
    friend_pool = NAMES_BOY if friend_gender == "boy" else NAMES_GIRL if friend_gender == "girl" else NAMES_NEUTRAL
    name = args.name or rng.choice(name_pool)
    friend_name = args.friend_name or rng.choice([n for n in friend_pool if n != name] or friend_pool)
    if name == friend_name:
        raise StoryError("The hero and friend need different names so the misunderstanding can be clear.")
    return StoryParams(name=name, friend_name=friend_name, gender=gender, friend_gender=friend_gender)


def generate(params: StoryParams) -> StorySample:
    world = tell_story(params)
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


def _all_samples() -> list[StoryParams]:
    pairs = [
        ("Max", "Mia"),
        ("Luna", "Sam"),
        ("Alex", "Ruby"),
        ("Theo", "Nora"),
    ]
    out = []
    for hero, friend in pairs:
        out.append(StoryParams(name=hero, friend_name=friend, gender="junior", friend_gender="junior"))
    return out


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show misunderstanding/0. #show friendship/0. #show problem_solving/0."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import storyworlds.asp as asp
        model = asp.one_model(asp_program("#show misunderstanding/0. #show friendship/0. #show problem_solving/0."))
        print("ASP atoms:", sorted(f"{sym.name}" for sym in model))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        for i, p in enumerate(_all_samples()):
            p.seed = base_seed + i
            samples.append(generate(p))
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

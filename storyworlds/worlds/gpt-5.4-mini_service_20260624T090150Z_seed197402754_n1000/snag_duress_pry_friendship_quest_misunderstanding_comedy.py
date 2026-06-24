#!/usr/bin/env python3
"""
A small comedy storyworld about friendship, questing, a mistaken idea, and a
snag that adds harmless duress before a friend has to pry open the truth.

Premise:
A child wants to finish a tiny quest with a beloved friend.
A misunderstanding makes one friend think the other has caused a problem.
A snag creates duress, the friends pry apart the confusion, and friendship wins.
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


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    plural: bool = False
    owner: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "mother", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str
    texture: str


@dataclass
class Quest:
    id: str
    goal: str
    verb: str
    stumble: str
    finish: str
    clue: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Item:
    id: str
    label: str
    phrase: str
    fragile: bool = False
    important: bool = False


@dataclass
class StoryParams:
    setting: str
    quest: str
    item: str
    name: str
    friend_name: str
    seed: Optional[int] = None


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.facts: dict[str, object] = {}
        self.fired: set[str] = set()
        self.paragraphs: list[list[str]] = [[]]

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


SETTINGS = {
    "garden": Setting(place="the garden", texture="leafy"),
    "attic": Setting(place="the attic", texture="dusty"),
    "kitchen": Setting(place="the kitchen", texture="bright"),
    "shed": Setting(place="the shed", texture="quiet"),
}

QUESTS = {
    "snag": Quest(
        id="snag",
        goal="find the shiny key",
        verb="search for the shiny key",
        stumble="caught on a loop of string",
        finish="the key popped free with a tiny twang",
        clue="the loose string was only holding down a napkin",
        tags={"snag", "quest", "comedy"},
    ),
    "duress": Quest(
        id="duress",
        goal="save the cupcake map",
        verb="rescue the cupcake map",
        stumble="squished under a stack of bowls",
        finish="the bowls tipped aside with a harmless clatter",
        clue="the map was safe under a clean plate",
        tags={"duress", "quest", "comedy"},
    ),
    "pry": Quest(
        id="pry",
        goal="open the tiny toy chest",
        verb="open the tiny toy chest",
        stumble="stuck behind a stubborn latch",
        finish="the latch gave way after a gentle pry",
        clue="the chest was not locked at all, just sleepy",
        tags={"pry", "quest", "comedy"},
    ),
}

ITEMS = {
    "key": Item(id="key", label="key", phrase="a shiny brass key", important=True),
    "map": Item(id="map", label="map", phrase="a cupcake map", fragile=True, important=True),
    "chest": Item(id="chest", label="chest", phrase="a tiny toy chest", important=True),
}

GIRL_NAMES = ["Mia", "Luna", "Zoe", "Ava", "Nora", "Lily"]
BOY_NAMES = ["Leo", "Finn", "Max", "Theo", "Ben", "Eli"]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Comedy storyworld about friendship, quest, and misunderstanding.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--quest", choices=QUESTS)
    ap.add_argument("--item", choices=ITEMS)
    ap.add_argument("--name")
    ap.add_argument("--friend-name")
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("-n", type=int, default=1)
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--trace", action="store_true")
    ap.add_argument("--qa", action="store_true")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--asp", action="store_true")
    ap.add_argument("--verify", action="store_true")
    ap.add_argument("--show-asp", action="store_true")
    return ap


def valid_combos() -> list[tuple[str, str, str]]:
    return [(s, q, i) for s in SETTINGS for q in QUESTS for i in ITEMS if QUESTS[q].goal.split()[-1] or True]


def explain_rejection() -> str:
    return "(No story: the requested combination does not make a playful quest story.)"


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    combos = valid_combos()
    if args.setting:
        combos = [c for c in combos if c[0] == args.setting]
    if args.quest:
        combos = [c for c in combos if c[1] == args.quest]
    if args.item:
        combos = [c for c in combos if c[2] == args.item]
    if not combos:
        raise StoryError(explain_rejection())
    setting, quest, item = rng.choice(sorted(combos))
    name = args.name or rng.choice(GIRL_NAMES + BOY_NAMES)
    friend_name = args.friend_name or rng.choice([n for n in GIRL_NAMES + BOY_NAMES if n != name])
    return StoryParams(setting=setting, quest=quest, item=item, name=name, friend_name=friend_name)


def build_world(params: StoryParams) -> World:
    world = World(SETTINGS[params.setting])
    hero = world.add(Entity(id=params.name, kind="character", type="girl" if params.name in GIRL_NAMES else "boy"))
    friend = world.add(Entity(id=params.friend_name, kind="character", type="girl" if params.friend_name in GIRL_NAMES else "boy"))
    item = world.add(Entity(id=params.item, type=params.item, label=ITEMS[params.item].label, phrase=ITEMS[params.item].phrase, owner=hero.id))
    quest = QUESTS[params.quest]

    hero.memes["curiosity"] = 1
    friend.memes["friendship"] = 1
    hero.memes["friendship"] = 1

    world.say(f"{hero.id} and {friend.id} were best friends who loved small adventures.")
    world.say(f"They had a quest to {quest.goal} at {world.setting.place}, which was {world.setting.texture} and full of funny corners.")
    world.say(f"{hero.id} carried {item.phrase} because it looked important enough for a quest.")

    world.para()
    world.say(f"Then a little snag appeared: {quest.stumble}.")
    hero.meters["duress"] = 1
    friend.meters["duress"] = 1
    world.say(f"{hero.id} frowned, because {quest.clue} did not match what they first thought.")
    world.say(f"{friend.id} thought the trouble came from {hero.id}, and the misunderstanding made both of them feel a bit silly.")

    world.para()
    world.say(f"{friend.id} decided to pry at the idea, not the chest.")
    world.say(f"After a careful look, they saw that {quest.finish}.")
    world.say(f"That was the funny truth: the problem was only a harmless snag, not a real mistake.")
    world.say(f"{hero.id} laughed, {friend.id} laughed, and they finished the quest together by {quest.verb}.")
    world.say(f"In the end, friendship felt bigger than the misunderstanding, and the day ended with a grin at {world.setting.place}.")

    world.facts.update(hero=hero, friend=friend, item=item, quest=quest, setting=world.setting, resolved=True)
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    friend = f["friend"]
    quest = f["quest"]
    item = f["item"]
    return [
        f'Write a funny story about friendship, a quest, and a misunderstanding at {world.setting.place}.',
        f"Tell a comedy story where {hero.id} and {friend.id} try to {quest.verb} and must not lose {item.phrase}.",
        f'Write a child-friendly story using the words "snag", "duress", and "pry".',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    friend = f["friend"]
    quest = f["quest"]
    item = f["item"]
    return [
        QAItem(
            question=f"Who were the two friends in the story?",
            answer=f"The story was about {hero.id} and {friend.id}, who were best friends.",
        ),
        QAItem(
            question=f"What was their quest?",
            answer=f"They wanted to {quest.goal}.",
        ),
        QAItem(
            question=f"What caused the misunderstanding?",
            answer=f"A little snag made things look wrong at first, so {friend.id} thought {hero.id} had caused the trouble.",
        ),
        QAItem(
            question=f"How did they fix the problem?",
            answer=f"They took a closer look, pried apart the confusion, and found that {quest.finish}.",
        ),
        QAItem(
            question=f"What item did {hero.id} carry on the quest?",
            answer=f"{hero.id} carried {item.phrase}.",
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a snag?",
            answer="A snag is something caught or stuck on something else, like a thread on a nail or a sleeve on a hook.",
        ),
        QAItem(
            question="What does pry mean?",
            answer="To pry means to gently pull or open something by working at it carefully.",
        ),
        QAItem(
            question="What is a misunderstanding?",
            answer="A misunderstanding happens when people think the wrong thing at first, but then they learn the truth.",
        ),
        QAItem(
            question="What is friendship?",
            answer="Friendship is the caring bond between people who help, share, and enjoy being together.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== Prompts =="]
    for p in sample.prompts:
        lines.append(p)
    lines.append("")
    lines.append("== Story Q&A ==")
    for qa in sample.story_qa:
        lines.append(f"Q: {qa.question}")
        lines.append(f"A: {qa.answer}")
    lines.append("")
    lines.append("== World Q&A ==")
    for qa in sample.world_qa:
        lines.append(f"Q: {qa.question}")
        lines.append(f"A: {qa.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- trace ---"]
    for e in world.entities.values():
        lines.append(f"{e.id}: kind={e.kind} type={e.type} meters={e.meters} memes={e.memes}")
    return "\n".join(lines)


ASP_RULES = r"""
setting(garden).
setting(attic).
setting(kitchen).
setting(shed).

quest(snag).
quest(duress).
quest(pry).

item(key).
item(map).
item(chest).

valid(S,Q,I) :- setting(S), quest(Q), item(I).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for s in SETTINGS:
        lines.append(asp.fact("setting", s))
    for q in QUESTS:
        lines.append(asp.fact("quest", q))
    for i in ITEMS:
        lines.append(asp.fact("item", i))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    python_set = set(valid_combos())
    clingo_set = set(asp_valid_combos())
    if python_set == clingo_set:
        print(f"OK: clingo gate matches valid_combos() ({len(python_set)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    print("  only in clingo:", sorted(clingo_set - python_set))
    print("  only in python:", sorted(python_set - clingo_set))
    return 1


def generate(params: StoryParams) -> StorySample:
    world = build_world(params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_qa(world),
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
    StoryParams(setting="garden", quest="snag", item="key", name="Mia", friend_name="Leo"),
    StoryParams(setting="kitchen", quest="duress", item="map", name="Ava", friend_name="Finn"),
    StoryParams(setting="attic", quest="pry", item="chest", name="Nora", friend_name="Max"),
]


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"{len(asp_valid_combos())} valid combos:")
        for s, q, i in asp_valid_combos():
            print(f"  {s:8} {q:8} {i:8}")
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
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()

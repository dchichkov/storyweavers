#!/usr/bin/env python3
"""
storyworlds/worlds/king_trouble_try_friendship_whodunit.py
===========================================================

A small story world about a king in trouble, a careful try at solving a mystery,
and a friendship that makes the answer feel bright instead of scary.

Seed tale premise:
---
A king in a castle wakes up to trouble: his golden bell is missing before a big
visit. A small friend and the king try to solve the whodunit by looking at clues
in the hall, the stairs, and the garden. The "mystery" turns out to be a simple
mix-up, and the king learns to laugh with a friend instead of worrying alone.

World design:
---
- Physical meters track where items are, what is hidden, and whether a clue has
  been noticed.
- Emotional memes track worry, trust, curiosity, and friendship.
- The story is driven by state changes: missing object -> suspicion -> clue trail
  -> gentle reveal -> repaired friendship.

This is a standalone Storyweavers world script.
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
    kind: str = "thing"  # "character" | "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    plural: bool = False
    location: str = ""
    hidden: bool = False
    clues: list[str] = field(default_factory=list)
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def __post_init__(self) -> None:
        for k in ["distance", "hiddenness", "noticed", "evidence"]:
            self.meters.setdefault(k, 0.0)
        for k in ["worry", "trust", "curiosity", "friendship", "relief"]:
            self.memes.setdefault(k, 0.0)

    def pronoun(self, case: str = "subject") -> str:
        if self.type == "king":
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        if self.type in {"girl", "woman", "queen", "mother"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man", "prince", "page", "guard"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    name: str = "the castle"
    rooms: list[str] = field(default_factory=lambda: ["throne room", "hall", "stairway", "garden"])


@dataclass
class Mystery:
    id: str
    label: str
    phrase: str
    type: str
    starting_place: str
    clue: str
    reveal_place: str
    reveal_reason: str


@dataclass
class StoryParams:
    setting: str
    mystery: str
    hero_name: str
    hero_type: str
    friend_name: str
    friend_type: str
    king_name: str
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


def article(word: str) -> str:
    return "an" if word[:1].lower() in "aeiou" else "a"


def join_list(items: list[str]) -> str:
    if not items:
        return ""
    if len(items) == 1:
        return items[0]
    if len(items) == 2:
        return f"{items[0]} and {items[1]}"
    return ", ".join(items[:-1]) + f", and {items[-1]}"


SETTING = Setting()

MYSTERIES = {
    "bell": Mystery(
        id="bell",
        label="golden bell",
        phrase="a golden bell",
        type="bell",
        starting_place="throne room",
        clue="a bright ribbon snagged on a stair rail",
        reveal_place="garden bench",
        reveal_reason="the bell had been set down there while the king practiced a speech",
    ),
    "crownpin": Mystery(
        id="crownpin",
        label="crown pin",
        phrase="a tiny crown pin",
        type="pin",
        starting_place="hall",
        clue="a shiny pin mark on a cushion",
        reveal_place="the king's sleeve",
        reveal_reason="the pin had clipped onto the king's own cloak",
    ),
    "map": Mystery(
        id="map",
        label="folded map",
        phrase="a folded map of the garden paths",
        type="map",
        starting_place="stairway",
        clue="muddy little footprints near the door",
        reveal_place="a basket by the kitchen",
        reveal_reason="the map had been tucked away with the picnic napkins",
    ),
}

HERO_TYPES = ["child", "girl", "boy", "page"]
FRIEND_TYPES = ["friend", "page", "child", "guard"]
KING_TYPES = ["king"]

NAMES = ["Milo", "Nina", "Ari", "June", "Theo", "Mina", "Sage", "Lena", "Pip", "Ivy"]


def clue_sense(mystery: Mystery) -> str:
    return {
        "bell": "a thin ringing feeling in the air",
        "crownpin": "a tiny glint that looked like a question",
        "map": "a puzzly feeling, like the room was trying to hide a secret",
    }[mystery.id]


def setup_world(params: StoryParams) -> World:
    world = World(SETTING)
    mystery = MYSTERIES[params.mystery]

    king = world.add(Entity(
        id="king",
        kind="character",
        type="king",
        label=params.king_name,
        phrase=f"King {params.king_name}",
    ))
    hero = world.add(Entity(
        id="hero",
        kind="character",
        type=params.hero_type,
        label=params.hero_name,
        phrase=params.hero_name,
    ))
    friend = world.add(Entity(
        id="friend",
        kind="character",
        type=params.friend_type,
        label=params.friend_name,
        phrase=params.friend_name,
    ))
    object_ = world.add(Entity(
        id="mystery",
        kind="thing",
        type=mystery.type,
        label=mystery.label,
        phrase=mystery.phrase,
        owner="king",
        location=mystery.starting_place,
        hidden=True,
        clues=[mystery.clue],
    ))

    king.memes["worry"] += 2
    king.memes["trust"] += 0.5
    hero.memes["curiosity"] += 1
    friend.memes["friendship"] += 1
    friend.memes["trust"] += 1

    world.facts.update(
        king=king,
        hero=hero,
        friend=friend,
        mystery=object_,
        mystery_def=mystery,
    )
    return world


def introduce(world: World) -> None:
    king = world.facts["king"]
    mystery = world.facts["mystery_def"]
    world.say(
        f"In {world.setting.name}, King {king.label} woke up to trouble: "
        f"{article(mystery.phrase)} {mystery.label} was missing."
    )
    world.say(
        f"{king.label} frowned at the empty spot and said the day felt like "
        f"{clue_sense(mystery)}."
    )


def gather_clues(world: World) -> None:
    hero = world.facts["hero"]
    friend = world.facts["friend"]
    mystery = world.facts["mystery_def"]
    world.para()
    world.say(
        f"{hero.label} and {friend.label} tried to solve the whodunit without shouting."
    )
    world.say(
        f"They looked in the {join_list(['hall', 'stairway', 'garden'])}, because a mystery often leaves a trail."
    )
    hero.memes["curiosity"] += 1
    friend.memes["trust"] += 1
    world.facts["looked_rooms"] = ["hall", "stairway", "garden"]
    world.facts["clue"] = mystery.clue
    world.facts["clue_found"] = False


def find_clue(world: World) -> None:
    hero = world.facts["hero"]
    friend = world.facts["friend"]
    mystery = world.facts["mystery_def"]
    object_ = world.facts["mystery"]
    world.para()
    world.say(
        f"In the {mystery.reveal_place if mystery.id != 'bell' else 'garden'}, "
        f"{hero.label} found {mystery.clue}."
    )
    world.say(
        f"{friend.label} leaned closer and said, 'That is a clue, not a trouble all by itself.'"
    )
    object_.meters["noticed"] += 1
    object_.meters["evidence"] += 1
    hero.memes["curiosity"] += 1
    friend.memes["friendship"] += 1
    world.facts["clue_found"] = True


def suspect_turn(world: World) -> None:
    king = world.facts["king"]
    hero = world.facts["hero"]
    friend = world.facts["friend"]
    mystery = world.facts["mystery_def"]
    world.para()
    king.memes["worry"] += 1
    world.say(
        f"King {king.label} wondered if someone had taken {mystery.phrase} on purpose."
    )
    world.say(
        f"{hero.label} did not want to guess wildly, so {hero.pronoun('subject')} tried another careful look."
    )
    world.say(
        f"{friend.label} said, 'Let's try the places where the king had been busy today.'"
    )


def reveal(world: World) -> None:
    king = world.facts["king"]
    hero = world.facts["hero"]
    friend = world.facts["friend"]
    mystery = world.facts["mystery_def"]
    object_ = world.facts["mystery"]
    world.para()
    object_.hidden = False
    object_.location = mystery.reveal_place
    king.memes["worry"] = max(0.0, king.memes["worry"] - 2)
    king.memes["relief"] += 2
    king.memes["trust"] += 1
    hero.memes["friendship"] += 1
    friend.memes["friendship"] += 2
    world.say(
        f"At last, they found the answer: {mystery.reveal_reason}."
    )
    world.say(
        f"So the whodunit was not a thief at all, just a mix-up hiding in plain sight."
    )
    world.say(
        f"King {king.label} laughed, and {hero.label} and {friend.label} laughed too."
    )


def friendship_end(world: World) -> None:
    king = world.facts["king"]
    hero = world.facts["hero"]
    friend = world.facts["friend"]
    mystery = world.facts["mystery_def"]
    world.para()
    king.memes["friendship"] += 1
    hero.memes["friendship"] += 1
    friend.memes["relief"] += 1
    world.say(
        f"The king thanked {hero.label} and {friend.label} for trying so hard and staying kind."
    )
    world.say(
        f"By the end, the mystery was solved, the trouble was gone, and the three of them stood together like good friends."
    )
    world.say(
        f"{mystery.label.capitalize()} rested safely again, and the castle felt calm."
    )


def tell_world(params: StoryParams) -> World:
    world = setup_world(params)
    introduce(world)
    gather_clues(world)
    find_clue(world)
    suspect_turn(world)
    reveal(world)
    friendship_end(world)
    return world


def build_story_line(world: World) -> str:
    return world.render()


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    mystery = f["mystery_def"]
    hero = f["hero"]
    friend = f["friend"]
    king = f["king"]
    return [
        f"Write a short whodunit story for a child about King {king.label}, "
        f"{hero.label}, and {friend.label}, where a {mystery.label} goes missing.",
        f"Tell a gentle mystery set in a castle where the king is in trouble, "
        f"the friends try clues, and the answer is friendly, not scary.",
        f"Write a simple story that uses the words king, trouble, try, and friendship "
        f"while solving a tiny mystery.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    mystery = f["mystery_def"]
    hero = f["hero"]
    friend = f["friend"]
    king = f["king"]
    return [
        QAItem(
            question=f"Who was in trouble at the start of the story?",
            answer=f"King {king.label} was in trouble because {article(mystery.phrase)} {mystery.label} was missing.",
        ),
        QAItem(
            question=f"What did {hero.label} and {friend.label} try to do?",
            answer=f"They tried to solve the whodunit by looking for clues in the castle rooms.",
        ),
        QAItem(
            question=f"What clue did they find?",
            answer=f"They found {mystery.clue}.",
        ),
        QAItem(
            question=f"How did the mystery end?",
            answer=f"They learned it was a mix-up, not a thief, and the king felt calm again.",
        ),
        QAItem(
            question=f"What mattered most at the end?",
            answer=f"Friendship mattered most, because the king thanked the two friends for helping kindly.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a king?",
            answer="A king is a ruler of a kingdom or castle in many stories.",
        ),
        QAItem(
            question="What does try mean?",
            answer="Try means to make an effort to do something, even if it is hard at first.",
        ),
        QAItem(
            question="What is trouble?",
            answer="Trouble is a problem or worry that makes things harder for a while.",
        ),
        QAItem(
            question="What is friendship?",
            answer="Friendship is the kind feeling that grows when people help, trust, and enjoy each other.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== Story questions =="]
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== World questions ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== Prompts ==")
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for e in world.entities.values():
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if e.location:
            bits.append(f"location={e.location}")
        if e.hidden:
            bits.append("hidden=True")
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        lines.append(f"  {e.id} ({e.type}) {' '.join(bits)}")
    return "\n".join(lines)


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    lines.append(asp.fact("setting", "castle"))
    for room in SETTING.rooms:
        lines.append(asp.fact("room", room))
        lines.append(asp.fact("in_setting", "castle", room))
    for mid, m in MYSTERIES.items():
        lines.append(asp.fact("mystery", mid))
        lines.append(asp.fact("starts_in", mid, m.starting_place))
        lines.append(asp.fact("clue", mid, m.clue))
        lines.append(asp.fact("reveals_at", mid, m.reveal_place))
    lines.append(asp.fact("role", "king", "king"))
    lines.append(asp.fact("role", "hero", "child"))
    lines.append(asp.fact("role", "friend", "friend"))
    return "\n".join(lines)


ASP_RULES = r"""
% A mystery is valid when it has a start, a clue, and a reveal point.
valid_mystery(M) :- mystery(M), starts_in(M, _), clue(M, _), reveals_at(M, _).

% A whodunit story needs a king, a helper, and a valid mystery.
valid_story(M) :- valid_mystery(M), role(king, king), role(hero, child), role(friend, friend).

#show valid_story/1.
"""


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_mysteries() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/1."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    import asp
    py = sorted((mid,) for mid in MYSTERIES)
    clingo = asp_valid_mysteries()
    if py == clingo:
        print(f"OK: ASP matches Python registries ({len(py)} mysteries).")
        return 0
    print("MISMATCH between ASP and Python:")
    print("  python:", py)
    print("  clingo:", clingo)
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="A tiny castle whodunit about a king in trouble, careful trying, and friendship."
    )
    ap.add_argument("--setting", choices=["castle"], default="castle")
    ap.add_argument("--mystery", choices=sorted(MYSTERIES), default=None)
    ap.add_argument("--hero-name")
    ap.add_argument("--hero-type", choices=HERO_TYPES, default="child")
    ap.add_argument("--friend-name")
    ap.add_argument("--friend-type", choices=FRIEND_TYPES, default="friend")
    ap.add_argument("--king-name")
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
    mystery = args.mystery or rng.choice(sorted(MYSTERIES))
    return StoryParams(
        setting=args.setting,
        mystery=mystery,
        hero_name=args.hero_name or rng.choice(NAMES),
        hero_type=args.hero_type,
        friend_name=args.friend_name or rng.choice([n for n in NAMES if n != args.hero_name]),
        friend_type=args.friend_type,
        king_name=args.king_name or rng.choice(["Arden", "Basil", "Cedric", "Dorian", "Edwin"]),
        seed=args.seed,
    )


def generate(params: StoryParams) -> StorySample:
    world = tell_world(params)
    return StorySample(
        params=params,
        story=build_story_line(world),
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


CURATED = [
    StoryParams(setting="castle", mystery="bell", hero_name="Milo", hero_type="child", friend_name="Nina", friend_type="friend", king_name="Arden"),
    StoryParams(setting="castle", mystery="map", hero_name="Ivy", hero_type="child", friend_name="Theo", friend_type="page", king_name="Basil"),
    StoryParams(setting="castle", mystery="crownpin", hero_name="Pip", hero_type="page", friend_name="Lena", friend_type="friend", king_name="Cedric"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid_story/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"{len(MYSTERIES)} valid mysteries:")
        for mid in sorted(MYSTERIES):
            print(f"  {mid}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
            params = resolve_params(args, random.Random(base_seed + i))
            i += 1
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
            header = f"### {p.hero_name} and {p.friend_name}: {p.mystery}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()

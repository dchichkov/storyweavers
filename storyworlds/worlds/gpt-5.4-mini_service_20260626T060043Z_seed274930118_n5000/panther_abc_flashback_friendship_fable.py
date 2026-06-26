#!/usr/bin/env python3
"""
storyworlds/worlds/panther_abc_flashback_friendship_fable.py
============================================================

A small fable-style story world about a panther learning the abc with a friend,
told with a gentle flashback structure and a friendship turn.

The seed idea:
- A proud panther wants to show cleverness.
- A friend helps with the abc.
- The panther flashes back to an earlier mistake.
- Friendship turns embarrassment into a happy lesson.
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
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    traits: list[str] = field(default_factory=list)
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"panther"}:
            return {"subject": "they", "object": "them", "possessive": "their"}[case]
        if self.type in {"fox"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        if self.type in {"owl"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class World:
    setting: str
    entities: dict[str, Entity] = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    facts: dict = field(default_factory=dict)
    fired: set[tuple] = field(default_factory=set)

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


# ---------------------------------------------------------------------------
# Parameters
# ---------------------------------------------------------------------------
@dataclass
class StoryParams:
    setting: str = "the quiet glade"
    panther_name: str = "Pip"
    friend_name: str = "Milo"
    friend_type: str = "fox"
    lesson: str = "abc"
    seed: Optional[int] = None


SETTINGS = {
    "glade": "the quiet glade",
    "clearing": "the sunlit clearing",
    "hill": "the grassy hill",
}

FRIENDS = {
    "fox": {"label": "fox", "name": "Milo"},
    "owl": {"label": "owl", "name": "Nina"},
    "hare": {"label": "hare", "name": "Tess"},
}

PANTHER_NAMES = ["Pip", "Nova", "Sable", "Onyx", "Mara", "Kiri"]
LESSONS = ["abc", "the abc", "letters", "the letters"]


# ---------------------------------------------------------------------------
# Story engine
# ---------------------------------------------------------------------------
def build_world(params: StoryParams) -> World:
    world = World(setting=params.setting)
    panther = world.add(Entity(
        id=params.panther_name,
        kind="character",
        type="panther",
        traits=["proud", "curious", "gentle"],
        meters={"restlessness": 0.0},
        memes={"pride": 1.0, "joy": 0.0, "embarrassment": 0.0, "friendship": 0.0},
    ))
    friend = world.add(Entity(
        id=params.friend_name,
        kind="character",
        type=params.friend_type,
        label=params.friend_type,
        traits=["kind", "patient"],
        meters={"restlessness": 0.0},
        memes={"joy": 0.0, "friendship": 1.0},
    ))
    book = world.add(Entity(
        id="book",
        kind="thing",
        type="book",
        label="picture book",
        phrase="a bright picture book of the abc",
        owner=panther.id,
        meters={"clean": 1.0},
    ))
    chalk = world.add(Entity(
        id="chalk",
        kind="thing",
        type="chalk",
        label="chalk",
        phrase="a small stick of chalk",
        owner=friend.id,
        meters={"bright": 1.0},
    ))
    world.facts.update(panther=panther, friend=friend, book=book, chalk=chalk, params=params)
    return world


def flashback(world: World) -> None:
    panther: Entity = world.facts["panther"]
    world.say(
        f"In {world.setting}, {panther.id} loved to strut like a grand little king, "
        f"but {panther.pronoun('possessive')} paws still stumbled over the abc."
    )
    world.say(
        f"One morning, when the breeze was soft, {panther.id} remembered a day "
        f"when {panther.pronoun()} had laughed at the letters and then felt very small."
    )
    panther.memes["embarrassment"] += 1.0
    world.facts["flashback"] = True


def friendship_turn(world: World) -> None:
    panther: Entity = world.facts["panther"]
    friend: Entity = world.facts["friend"]
    book: Entity = world.facts["book"]
    chalk: Entity = world.facts["chalk"]

    world.para()
    world.say(
        f"{friend.id} saw the frown and sat beside {panther.id} with {chalk.label} "
        f"and the {book.label}."
    )
    world.say(
        f'"We can learn it together," {friend.id} said. "{panther.id}, you say the first '
        f"letter, and I will help with the next."'
    )
    panther.memes["friendship"] += 1.0
    friend.memes["friendship"] += 1.0
    panther.memes["joy"] += 1.0
    world.facts["help"] = True


def learning_scene(world: World) -> None:
    panther: Entity = world.facts["panther"]
    friend: Entity = world.facts["friend"]

    world.say(
        f"So {panther.id} took a careful breath and traced the abc in the dust with "
        f"{panther.pronoun('possessive')} claw."
    )
    world.say(
        f"{friend.id} cheered each small step, and soon the letters sounded easy, "
        f"like a song that knew its own tune."
    )
    panther.meters["skill"] = 1.0
    panther.memes["pride"] += 0.5
    panther.memes["joy"] += 1.0
    world.facts["learned"] = True


def ending(world: World) -> None:
    panther: Entity = world.facts["panther"]
    friend: Entity = world.facts["friend"]
    world.para()
    world.say(
        f"By sunset, {panther.id} could say the abc with a bright smile, and the old "
        f"embarrassment felt tiny beside {friend.id}'s faithful kindness."
    )
    world.say(
        f"The two friends walked home together, and {panther.id} carried the lesson "
        f"as carefully as a treasure: a friend can make even hard letters feel warm."
    )
    world.facts["resolved"] = True


def tell(params: StoryParams) -> World:
    world = build_world(params)
    flashback(world)
    friendship_turn(world)
    learning_scene(world)
    ending(world)
    return world


# ---------------------------------------------------------------------------
# Q&A
# ---------------------------------------------------------------------------
def generation_prompts(world: World) -> list[str]:
    p = world.facts["panther"]
    f = world.facts["friend"]
    return [
        'Write a short fable for children about a panther learning the abc with a friend.',
        f"Tell a gentle story about {p.id} feeling embarrassed, then remembering an old mistake in a flashback and learning from {f.id}.",
        f"Write a friendship story that includes the words panther and abc and ends with a kind lesson.",
    ]


def story_qa(world: World) -> list[QAItem]:
    p: Entity = world.facts["panther"]
    f: Entity = world.facts["friend"]
    return [
        QAItem(
            question=f"Who is the story mainly about?",
            answer=f"The story is mainly about {p.id}, a proud panther who learns the abc with help from {f.id}.",
        ),
        QAItem(
            question=f"Why did {p.id} feel embarrassed at first?",
            answer=f"{p.id} remembered an earlier time when {p.id} stumbled over the letters and felt small about it.",
        ),
        QAItem(
            question=f"What changed the story for {p.id}?",
            answer=f"{f.id}'s friendship changed the story, because {f.id} stayed kind and helped {p.id} learn step by step.",
        ),
        QAItem(
            question=f"How did the story end?",
            answer=f"It ended with {p.id} happily saying the abc and walking home with a warm lesson about friendship.",
        ),
    ]


KNOWLEDGE = {
    "panther": [
        QAItem(
            question="What is a panther?",
            answer="A panther is a big cat with a strong body and quiet feet.",
        ),
    ],
    "abc": [
        QAItem(
            question="What is the abc?",
            answer="The abc is the first set of letters children learn when they start reading.",
        ),
    ],
    "friendship": [
        QAItem(
            question="What is friendship?",
            answer="Friendship is a kind bond between people or animals who care about each other and help one another.",
        ),
    ],
    "flashback": [
        QAItem(
            question="What is a flashback in a story?",
            answer="A flashback is a part of a story that shows something that happened earlier.",
        ),
    ],
}


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [item for key in ["panther", "abc", "flashback", "friendship"] for item in KNOWLEDGE[key]]


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
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
panther(p1).
friend(f1).
lesson(abc).

needs_help(p1).
has_flashback(p1) :- needs_help(p1).
can_learn(p1) :- needs_help(p1), friend(f1), lesson(abc).
friendly_story :- has_flashback(p1), can_learn(p1), friend(f1).
#show needs_help/1.
#show has_flashback/1.
#show can_learn/1.
#show friendly_story/0.
"""


def asp_facts() -> str:
    import storyworlds.asp as asp
    return "\n".join([
        asp.fact("panther", "p1"),
        asp.fact("friend", "f1"),
        asp.fact("lesson", "abc"),
    ])


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import storyworlds.asp as asp
    model = asp.one_model(asp_program("#show friendly_story/0."))
    atoms = {sym.name for sym in model}
    ok = "friendly_story" in atoms
    if ok:
        print("OK: ASP story twin is consistent.")
        return 0
    print("MISMATCH: ASP story twin failed.")
    return 1


# ---------------------------------------------------------------------------
# Parameters and generation
# ---------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A fable about a panther, the abc, flashback, and friendship.")
    ap.add_argument("--setting", choices=sorted(SETTINGS))
    ap.add_argument("--panther-name", choices=PANTHER_NAMES)
    ap.add_argument("--friend-name")
    ap.add_argument("--friend-type", choices=sorted(FRIENDS))
    ap.add_argument("--lesson", choices=sorted(set(LESSONS)))
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
    setting_key = args.setting or rng.choice(sorted(SETTINGS))
    panther_name = args.panther_name or rng.choice(PANTHER_NAMES)
    friend_type = args.friend_type or rng.choice(sorted(FRIENDS))
    friend_name = args.friend_name or FRIENDS[friend_type]["name"]
    lesson = args.lesson or "abc"
    return StoryParams(
        setting=SETTINGS[setting_key],
        panther_name=panther_name,
        friend_name=friend_name,
        friend_type=friend_type,
        lesson=lesson,
    )


def generate(params: StoryParams) -> StorySample:
    world = tell(params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        bits = []
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        if e.traits:
            bits.append(f"traits={e.traits}")
        lines.append(f"  {e.id} ({e.type}) {' '.join(bits)}")
    lines.append(f"  facts={sorted(world.facts.keys())}")
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


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show friendly_story/0."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(asp_program("#show friendly_story/0."))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)

    samples: list[StorySample] = []
    if args.all:
        curated = [
            StoryParams(setting=SETTINGS["glade"], panther_name="Pip", friend_name="Milo", friend_type="fox", lesson="abc"),
            StoryParams(setting=SETTINGS["clearing"], panther_name="Nova", friend_name="Nina", friend_type="owl", lesson="abc"),
            StoryParams(setting=SETTINGS["hill"], panther_name="Sable", friend_name="Tess", friend_type="hare", lesson="abc"),
        ]
        samples = [generate(p) for p in curated]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 50, 50):
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            sample = generate(params)
            if sample.story not in seen:
                seen.add(sample.story)
                samples.append(sample)
            i += 1

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

#!/usr/bin/env python3
"""
storyworlds/worlds/cub_question_inner_monologue_sharing_twist_nursery.py
========================================================================

A small nursery-rhyme storyworld about a cub, a question, a shared toy,
an inner monologue, and a gentle twist.

Premise:
- A little cub wants something shiny or sweet.
- The cub quietly thinks about a question before acting.
- A sharing turn changes the outcome.
- A twist reveals the first wish was not the real need.
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
    owner: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)
    plural: bool = False

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"cub", "bear", "child"}:
            return {"subject": "they", "object": "them", "possessive": "their"}[case]
        if self.type in {"mother", "father", "friend", "squirrel", "hare", "owl"}:
            return {"subject": "they", "object": "them", "possessive": "their"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str = "the nursery glen"
    cozy: bool = True
    affords: set[str] = field(default_factory=lambda: {"share", "ask"})


@dataclass
class Treasure:
    id: str
    label: str
    phrase: str
    sparkle: str
    can_share: bool = True


@dataclass
class StoryParams:
    place: str
    cub_name: str
    friend_name: str
    treasure: str
    seed: Optional[int] = None


class World:
    def __init__(self, setting: Setting):
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[str] = set()
        self.facts: dict = {}

    def add(self, e: Entity) -> Entity:
        self.entities[e.id] = e
        return e

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
    "nursery_glen": Setting(place="the nursery glen", cozy=True, affords={"share", "ask"}),
    "mossy_hill": Setting(place="the mossy hill", cozy=True, affords={"share", "ask"}),
    "lantern_path": Setting(place="the lantern path", cozy=True, affords={"share", "ask"}),
}

TREASURES = {
    "berry": Treasure("berry", "berry", "a bright berry", "red"),
    "bell": Treasure("bell", "bell", "a little bell", "silver"),
    "book": Treasure("book", "picture book", "a small picture book", "golden"),
}

CUB_NAMES = ["Milo", "Pip", "Nico", "Toby", "Arlo", "Bram", "Ollie", "Finn"]
FRIEND_NAMES = ["Bee", "Wren", "Pip", "Dot", "Rue", "Luna", "Nell", "Rose"]


# ---------------------------------------------------------------------------
# Story logic
# ---------------------------------------------------------------------------

def tell(params: StoryParams) -> World:
    world = World(SETTINGS[params.place])
    cub = world.add(Entity(id=params.cub_name, kind="character", type="cub", label=params.cub_name))
    friend = world.add(Entity(id=params.friend_name, kind="character", type="friend", label=params.friend_name))
    treasure = world.add(Entity(id="treasure", kind="thing", type=params.treasure, label=TREASURES[params.treasure].label,
                                phrase=TREASURES[params.treasure].phrase, owner=friend.id))

    cub.memes["curious"] = 1
    cub.memes["wanting"] = 1
    friend.memes["kind"] = 1

    # Setup
    world.say(f"Little {cub.id} skipped along the {world.setting.place}, soft as a song.")
    world.say(f"{cub.id} saw {treasure.phrase} and felt a tingle in {cub.pronoun('possessive')} paws.")
    world.say(f"Beside the path, {friend.id} held {treasure.it()} and smiled so wide.")

    # Inner monologue
    world.para()
    world.say(f"\"I want that {treasure.label},\" thought {cub.id}, and {cub.pronoun('subject')} paused to think.")
    world.say(f"\"But sharing may shine brighter than grabbing in a blink.\"")
    world.say(f"{cub.id} wondered a question in {cub.pronoun('possessive')} tiny head: \"How can one wish stay warm and still leave room for two?\"")
    cub.memes["question"] = 1

    # Turning action
    world.para()
    world.say(f"{cub.id} asked the question out loud, gentle as rain.")
    world.say(f"{friend.id} laughed a little laugh and said, \"We can share again.\"")
    cub.memes["brave"] = 1

    # Sharing
    world.say(f"So {friend.id} shared {treasure.it()} at once, and {cub.id} shared a smile.")
    cub.memes["joy"] = 1
    friend.memes["joy"] = 1

    # Twist
    world.para()
    world.say(f"But then came the twist, twinkling bright: {cub.id} did not want the {treasure.label} most of all.")
    world.say(f"{cub.id} wanted {friend.id}'s company, the cozy game, and the kind reply.")
    world.say(f"Hand in hand, they went on, and the little {treasure.label} rang like a lullaby.")

    world.facts.update(cub=cub, friend=friend, treasure=treasure)
    return world


# ---------------------------------------------------------------------------
# QA
# ---------------------------------------------------------------------------

def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f"Write a nursery-rhyme story about a cub named {f['cub'].id} who has a question, shares, and learns a twist.",
        f"Tell a gentle story in rhyme where {f['cub'].id} wants {f['treasure'].phrase}, then decides to share with {f['friend'].id}.",
        "Write a short child-facing tale with inner monologue, sharing, and a surprising but happy ending.",
    ]


def story_qa(world: World) -> list[QAItem]:
    cub = world.facts["cub"]
    friend = world.facts["friend"]
    treasure = world.facts["treasure"]
    return [
        QAItem(
            question=f"Who is the story about?",
            answer=f"The story is about little {cub.id}, a curious cub who visits {world.setting.place}.",
        ),
        QAItem(
            question=f"What question did {cub.id} wonder?",
            answer=f"{cub.id} wondered how one wish could stay warm and still leave room for two.",
        ),
        QAItem(
            question=f"What did {cub.id} and {friend.id} do with {treasure.label}?",
            answer=f"They shared {treasure.it()} together, and both of them felt happy.",
        ),
        QAItem(
            question=f"What was the twist at the end?",
            answer=f"The twist was that {cub.id} did not want the {treasure.label} most of all; {cub.id} wanted {friend.id}'s company.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does sharing mean?",
            answer="Sharing means letting someone else use, hold, or enjoy something with you.",
        ),
        QAItem(
            question="What is a question?",
            answer="A question is a sentence that asks for an answer or more information.",
        ),
        QAItem(
            question="What is an inner monologue?",
            answer="An inner monologue is the quiet thinking words a character says inside their own mind.",
        ),
    ]


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------

ASP_RULES = r"""
cub(C) :- cub_name(C).
friend(F) :- friend_name(F).
treasure(T) :- treasure_kind(T).

can_share(T) :- treasure(T).
needs_question(C) :- cub(C).
good_story(C,F,T) :- cub(C), friend(F), treasure(T), can_share(T), needs_question(C).
"""

def asp_facts() -> str:
    import storyworlds.asp as asp
    lines = []
    for name in CUB_NAMES:
        lines.append(asp.fact("cub_name", name))
    for name in FRIEND_NAMES:
        lines.append(asp.fact("friend_name", name))
    for tid in TREASURES:
        lines.append(asp.fact("treasure_kind", tid))
    for sid in SETTINGS:
        lines.append(asp.fact("setting_kind", sid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import storyworlds.asp as asp
    model = asp.one_model(asp_program("#show good_story/3."))
    asp_set = set(asp.atoms(model, "good_story"))
    py_set = {(c, f, t) for c in CUB_NAMES for f in FRIEND_NAMES for t in TREASURES}
    if asp_set == py_set:
        print(f"OK: ASP and Python agree on {len(asp_set)} combinations.")
        return 0
    print("MISMATCH between ASP and Python.")
    print("only in ASP:", sorted(asp_set - py_set))
    print("only in Python:", sorted(py_set - asp_set))
    return 1


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Nursery-rhyme storyworld: cub, question, sharing, twist.")
    ap.add_argument("--place", choices=SETTINGS.keys())
    ap.add_argument("--cub-name", choices=CUB_NAMES)
    ap.add_argument("--friend-name", choices=FRIEND_NAMES)
    ap.add_argument("--treasure", choices=TREASURES.keys())
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
    place = args.place or rng.choice(list(SETTINGS))
    cub_name = args.cub_name or rng.choice(CUB_NAMES)
    friend_name = args.friend_name or rng.choice([n for n in FRIEND_NAMES if n != cub_name])
    treasure = args.treasure or rng.choice(list(TREASURES))
    if not SETTINGS[place].affords:
        raise StoryError("That setting cannot support the story.")
    return StoryParams(place=place, cub_name=cub_name, friend_name=friend_name, treasure=treasure)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        lines.append(f"  {e.id}: kind={e.kind} type={e.type} memes={dict(e.memes)} meters={dict(e.meters)}")
    return "\n".join(lines)


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    for p in sample.prompts:
        lines.append(p)
    lines.append("")
    lines.append("== story qa ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== world qa ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


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
        print(asp_program("#show good_story/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import storyworlds.asp as asp
        model = asp.one_model(asp_program("#show good_story/3."))
        print(sorted(asp.atoms(model, "good_story")))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        combos = [(p, c, f, t) for p in SETTINGS for c in CUB_NAMES for f in FRIEND_NAMES if f != c for t in TREASURES]
        for p, c, f, t in combos[: min(12, len(combos))]:
            samples.append(generate(StoryParams(place=p, cub_name=c, friend_name=f, treasure=t, seed=base_seed)))
    else:
        for i in range(max(1, args.n)):
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            samples.append(generate(params))

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

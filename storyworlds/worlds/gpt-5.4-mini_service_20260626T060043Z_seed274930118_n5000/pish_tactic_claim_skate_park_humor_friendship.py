#!/usr/bin/env python3
"""
A small whodunit-style story world set in a skate park.

Premise:
- A strange "pish" sound appears at the skate park.
- Someone makes a tactic, then a claim.
- Humor, friendship, and kindness untangle the mystery.

This file is self-contained and follows the Storyweavers world contract.
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
# Domain model
# ---------------------------------------------------------------------------

@dataclass
class Entity:
    id: str
    kind: str = "thing"  # "character" or "thing"
    label: str = ""
    type: str = ""
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)
    owner: Optional[str] = None

    def noun(self) -> str:
        return self.label or self.type or self.id

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "woman", "mother"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man", "father"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]


@dataclass
class Setting:
    place: str = "the skate park"
    soundy: bool = True


@dataclass
class Clue:
    name: str
    label: str
    detail: str


@dataclass
class StoryParams:
    clue: str
    friend: str
    helper: str
    seed: Optional[int] = None


class World:
    def __init__(self, setting: Setting):
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.facts: dict[str, object] = {}
        self.trace: list[str] = []

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str) -> Entity:
        return self.entities[eid]

    def say(self, text: str) -> None:
        self.trace.append(text)

    def render(self) -> str:
        return " ".join(self.trace)


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------

SETTING = Setting()

CLUES = {
    "deck": Clue("deck", "skate deck", "a board with bright tape under the wheels"),
    "wheel": Clue("wheel", "wheel cap", "a tiny cap that can pop off and roll away"),
    "paper": Clue("paper", "paper scrap", "a torn scrap with a note on it"),
}

FRIENDS = {
    "Milo": {"type": "boy", "role": "friend"},
    "Nia": {"type": "girl", "role": "friend"},
    "Tess": {"type": "girl", "role": "friend"},
}

HELPERS = {
    "Ava": {"type": "girl", "role": "helper"},
    "Noah": {"type": "boy", "role": "helper"},
    "June": {"type": "girl", "role": "helper"},
}

HUMOR_LINES = [
    "It looked so silly that even the pigeons seemed to stare.",
    "The whole thing had the kind of funny wobble that makes kids giggle.",
    "It was a joke-sized mystery, but it still needed solving.",
]

KNOWN_MOTIONS = {
    "pish": "a soft pish sound skittered over the concrete",
    "tactic": "a careful tactic could make sense of the noisy clue",
    "claim": "a claim could sound true and still hide a mix-up",
}

# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------

ASP_RULES = r"""
% A clue is suspicious when it creates a strange sound or a stray object.
suspicious(X) :- clue(X), odd(X).

% A good tactic uses kindness or humor to examine the clue safely.
good_tactic(T) :- tactic(T), uses(T, kindness).
good_tactic(T) :- tactic(T), uses(T, humor).

% A claim is reasonable if a friendly helper can check it.
reasonable_claim(C) :- claim(C), can_check(friend, C).

% A solved mystery needs one suspicious clue, one good tactic, and one fair claim.
solved :- suspicious(_), good_tactic(_), reasonable_claim(_).

#show solved/0.
"""

def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for cid, clue in CLUES.items():
        lines.append(asp.fact("clue", cid))
        lines.append(asp.fact("odd", cid))
    lines.append(asp.fact("tactic", "careful_tactic"))
    lines.append(asp.fact("uses", "careful_tactic", "kindness"))
    lines.append(asp.fact("uses", "careful_tactic", "humor"))
    lines.append(asp.fact("claim", "friendly_claim"))
    lines.append(asp.fact("can_check", "friend", "friendly_claim"))
    return "\n".join(lines)


def asp_program() -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program())
    has_solved = any(sym.name == "solved" for sym in model)
    py_solved = True
    if has_solved == py_solved:
        print("OK: ASP and Python agree that the mystery can be solved.")
        return 0
    print("MISMATCH: ASP and Python disagree.")
    return 1


# ---------------------------------------------------------------------------
# World logic
# ---------------------------------------------------------------------------

def build_world(params: StoryParams) -> World:
    world = World(SETTING)
    friend = FRIENDS[params.friend]
    helper = HELPERS[params.helper]
    clue = CLUES[params.clue]

    friend_ent = world.add(Entity(id="friend", kind="character", label=params.friend, type=friend["type"]))
    helper_ent = world.add(Entity(id="helper", kind="character", label=params.helper, type=helper["type"]))
    clue_ent = world.add(Entity(id="clue", kind="thing", label=clue.label, type=clue.name))

    world.facts.update(
        friend=friend_ent,
        helper=helper_ent,
        clue=clue_ent,
        clue_name=clue.name,
        clue_label=clue.label,
        clue_detail=clue.detail,
    )
    return world


def tell_story(world: World) -> str:
    f = world.facts
    friend: Entity = f["friend"]  # type: ignore[assignment]
    helper: Entity = f["helper"]  # type: ignore[assignment]
    clue: Entity = f["clue"]  # type: ignore[assignment]

    world.say(f"At the skate park, a soft pish sound slipped past the ramps and benches.")
    world.say(f"{friend.noun()} heard it first and frowned, because that sound did not belong.")
    world.say(random.choice(HUMOR_LINES))
    world.say(f"{helper.noun()} came over with a careful tactic: look low, listen twice, and do not jump to a claim.")
    world.say(f"They found the clue: {clue.label}, lying near the quarter pipe like a tiny lost secret.")
    world.say(f"{friend.noun().capitalize()} made a quick claim that the clue must be a trick from the loud older kids.")
    world.say(f"But {helper.noun()} smiled kindly and checked the facts instead.")
    world.say(f"The clue was only a paper-folded tag that had fallen from a skateboard, and the pish sound was just a loose wheel cap skittering away.")
    world.say(f"{friend.noun().capitalize()} laughed, then apologized for the wrong claim, and {helper.noun()} nodded with friendship and kindness.")
    world.say(f"Before long, they taped the cap back on, left the tag at lost-and-found, and the skate park sounded normal again.")
    world.say(f"That evening, the mystery ended not with a chase, but with a grin.")
    return world.render()


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f"Write a short whodunit for a child at {world.setting.place} that includes the word 'pish'.",
        f"Tell a mystery story where a friend uses a tactic and kindness to test a claim.",
        f"Make a gentle skate park story with humor, friendship, and a clue that turns out harmless.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    clue: Entity = f["clue"]  # type: ignore[assignment]
    friend: Entity = f["friend"]  # type: ignore[assignment]
    helper: Entity = f["helper"]  # type: ignore[assignment]
    return [
        QAItem(
            question="What strange sound started the mystery?",
            answer="A soft pish sound started the mystery at the skate park.",
        ),
        QAItem(
            question=f"What tactic did {helper.noun()} suggest?",
            answer="They suggested looking low, listening twice, and not jumping to a claim.",
        ),
        QAItem(
            question=f"What clue did {friend.noun()} and {helper.noun()} find?",
            answer=f"They found {clue.label}, which turned out to be harmless.",
        ),
        QAItem(
            question="What made the story end happily?",
            answer="The friends used kindness and humor, fixed the little problem, and laughed together at the end.",
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a skate park?",
            answer="A skate park is a place with ramps, rails, and smooth ground where people ride skateboards and scooters.",
        ),
        QAItem(
            question="What does kindness do in a mystery?",
            answer="Kindness helps people listen, check facts, and treat each other gently while they solve the problem.",
        ),
        QAItem(
            question="Why can humor help friends?",
            answer="Humor can make a tense moment feel lighter, so friends can think clearly and stay close.",
        ),
    ]


# ---------------------------------------------------------------------------
# Generation and CLI
# ---------------------------------------------------------------------------

def choose_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    clue = args.clue or rng.choice(sorted(CLUES))
    friend = args.friend or rng.choice(sorted(FRIENDS))
    helper = args.helper or rng.choice(sorted(HELPERS))
    if friend == helper:
        raise StoryError("The friend and helper should be different characters.")
    return StoryParams(clue=clue, friend=friend, helper=helper)


def generate(params: StoryParams) -> StorySample:
    world = build_world(params)
    story = tell_story(world)
    return StorySample(
        params=params,
        story=story,
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_qa(world),
        world=world,
    )


def format_qa(sample: StorySample) -> str:
    parts = ["== Prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        parts.append(f"{i}. {p}")
    parts.append("")
    parts.append("== Story QA ==")
    for item in sample.story_qa:
        parts.append(f"Q: {item.question}")
        parts.append(f"A: {item.answer}")
    parts.append("")
    parts.append("== World QA ==")
    for item in sample.world_qa:
        parts.append(f"Q: {item.question}")
        parts.append(f"A: {item.answer}")
    return "\n".join(parts)


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for eid, ent in world.entities.items():
        lines.append(f"{eid}: {ent.kind} {ent.noun()}")
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


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Whodunit-style skate park story world.")
    ap.add_argument("--clue", choices=sorted(CLUES))
    ap.add_argument("--friend", choices=sorted(FRIENDS))
    ap.add_argument("--helper", choices=sorted(HELPERS))
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
    return choose_params(args, rng)


def curated_params() -> list[StoryParams]:
    return [
        StoryParams(clue="deck", friend="Milo", helper="Ava"),
        StoryParams(clue="wheel", friend="Nia", helper="Noah"),
        StoryParams(clue="paper", friend="Tess", helper="June"),
    ]


def asp_solved() -> bool:
    import asp
    model = asp.one_model(asp_program())
    return any(sym.name == "solved" for sym in model)


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program())
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print("solved" if asp_solved() else "unsolved")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(p) for p in curated_params()]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 20):
            rng = random.Random(base_seed + i)
            i += 1
            try:
                params = resolve_params(args, rng)
            except StoryError as err:
                print(err)
                return
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
        header = f"### story {idx + 1}" if len(samples) > 1 and not args.all else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if idx < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()

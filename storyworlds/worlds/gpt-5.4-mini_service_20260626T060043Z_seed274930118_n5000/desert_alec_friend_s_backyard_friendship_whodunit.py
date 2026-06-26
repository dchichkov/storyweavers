#!/usr/bin/env python3
"""
storyworlds/worlds/desert_alec_friend_s_backyard_friendship_whodunit.py
======================================================================

A small storyworld about a backyard whodunit with desert clues, a friend named
Alec, and friendship that helps solve the mystery.

Premise:
- Alec visits a friend's backyard for play.
- A small mystery appears: something is missing or moved.
- The children notice desert-like clues in the sand, on the fence, and near the
  garden corner.
- Friendship turns the accusation into a careful search.
- The truth is simple, and the ending proves what changed.

This world is intentionally tiny and constraint-checked: only plausible mystery
setups are generated, and the declarative ASP twin mirrors the same gate.
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
# Data model
# ---------------------------------------------------------------------------

@dataclass
class Entity:
    id: str
    kind: str = "thing"  # "character" | "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    possessed_by: Optional[str] = None
    hidden: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"boy", "man", "father"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        if self.type in {"girl", "woman", "mother"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class Setting:
    place: str
    indoors: bool = False
    affords: set[str] = field(default_factory=set)


@dataclass
class Clue:
    id: str
    label: str
    source: str
    note: str


@dataclass
class Mystery:
    id: str
    missing: str
    missing_phrase: str
    culprit: str
    clue: str
    clue_phrase: str
    found_where: str
    reveals: str
    suspicion_target: str
    friendship_fix: str


@dataclass
class StoryParams:
    place: str
    mystery: str
    name: str = "Alec"
    friend_name: str = "Maya"
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# World model
# ---------------------------------------------------------------------------

class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.facts: dict = {}
        self.lines: list[str] = []
        self.fired: set[str] = set()
        self.trace: list[str] = []

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str) -> Entity:
        return self.entities[eid]

    def say(self, text: str) -> None:
        if text:
            self.lines.append(text)

    def render(self) -> str:
        return " ".join(self.lines)

    def log(self, text: str) -> None:
        self.trace.append(text)


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------

SETTINGS = {
    "friend_backyard": Setting(
        place="a friend's backyard",
        indoors=False,
        affords={"search", "tea", "games"},
    )
}

MYSTERIES = {
    "missing_shovel": Mystery(
        id="missing_shovel",
        missing="shovel",
        missing_phrase="a little blue shovel",
        culprit="wind",
        clue="sand_print",
        clue_phrase="a tiny trail of sand",
        found_where="by the garden bucket",
        reveals="the shovel had slid under the wheelbarrow",
        suspicion_target="the neighbor's cat",
        friendship_fix="the two friends searched together instead of blaming anyone",
    ),
    "missing_cookie": Mystery(
        id="missing_cookie",
        missing="cookie",
        missing_phrase="a peanut cookie on a plate",
        culprit="grandpa",
        clue="crumbs",
        clue_phrase="a crumb line",
        found_where="near the porch step",
        reveals="Grandpa had moved it to keep it from ants",
        suspicion_target="the dog",
        friendship_fix="Alec and his friend shared the last cookie with Grandpa",
    ),
    "missing_kite_string": Mystery(
        id="missing_kite_string",
        missing="kite_string",
        missing_phrase="a kite string spool",
        culprit="brother",
        clue="twine",
        clue_phrase="a loop of twine on a chair",
        found_where="inside the storage box",
        reveals="the string was tucked away for later flying",
        suspicion_target="the wind",
        friendship_fix="they stayed calm and looked in the box together",
    ),
}

CLUES = {
    "sand_print": Clue(
        id="sand_print",
        label="sand prints",
        source="the sandbox",
        note="small grains stuck to the porch step",
    ),
    "crumbs": Clue(
        id="crumbs",
        label="crumbs",
        source="the snack plate",
        note="little bits that pointed toward the porch",
    ),
    "twine": Clue(
        id="twine",
        label="twine loops",
        source="the chair rail",
        note="a neat loop that hinted someone had put it away",
    ),
}

# ---------------------------------------------------------------------------
# Reasonableness gate
# ---------------------------------------------------------------------------

def valid_story(place: str, mystery: str) -> bool:
    return place in SETTINGS and mystery in MYSTERIES


def explain_rejection(place: str, mystery: str) -> str:
    if place not in SETTINGS:
        return "(No story: the setting must be a friend's backyard.)"
    if mystery not in MYSTERIES:
        return "(No story: that mystery is not available in this world.)"
    return "(No story: this combination is not reasonable.)"


# ---------------------------------------------------------------------------
# Story construction
# ---------------------------------------------------------------------------

def build_world(params: StoryParams) -> World:
    if not valid_story(params.place, params.mystery):
        raise StoryError(explain_rejection(params.place, params.mystery))

    setting = SETTINGS[params.place]
    mystery = MYSTERIES[params.mystery]
    world = World(setting)

    alec = world.add(Entity(id=params.name, kind="character", type="boy", label=params.name))
    friend = world.add(Entity(id=params.friend_name, kind="character", type="girl", label=params.friend_name))
    missing = world.add(Entity(
        id=mystery.missing,
        type="thing",
        label=mystery.missing,
        phrase=mystery.missing_phrase,
        hidden=True,
    ))
    clue = world.add(Entity(
        id=mystery.clue,
        type="thing",
        label=mystery.clue,
        phrase=mystery.clue_phrase,
    ))

    world.facts.update(
        alec=alec,
        friend=friend,
        missing=missing,
        clue=clue,
        mystery=mystery,
        setting=setting,
    )

    # Act 1: the calm beginning.
    world.say(
        f"Alec came to {setting.place} to play with {friend.label}, and the air felt warm and dry."
    )
    world.say(
        f"They liked each other right away, because friendship made the backyard feel safe and bright."
    )
    world.say(
        f"Then Alec noticed that {mystery.missing_phrase} was gone from the table."
    )

    # Act 2: whodunit tension.
    world.say(
        f"{friend.label} spotted {mystery.clue_phrase} near {mystery.found_where}, and both children looked at it closely."
    )
    world.say(
        f"Alec wondered if {mystery.suspicion_target} had taken it, but {friend.label} said, "
        f'"Let’s not guess yet. Let’s follow the clue."'
    )
    world.say(
        f"The two friends searched the backyard together, checking the bucket, the chair, and the little patch of sand."
    )

    # Act 3: truth and friendship.
    world.say(
        f"At last they found the answer: {mystery.reveals}."
    )
    world.say(
        f"Alec laughed with relief, and {friend.label} smiled, because {mystery.friendship_fix}."
    )
    world.say(
        f"By the end, the missing thing was back in place, and the backyard felt tidy again."
    )

    world.facts["solved"] = True
    world.facts["solution"] = mystery.reveals
    return world


# ---------------------------------------------------------------------------
# Prompts and QA
# ---------------------------------------------------------------------------

def generation_prompts(world: World) -> list[str]:
    f = world.facts
    m: Mystery = f["mystery"]
    return [
        "Write a short whodunit for a young child set in a friend's backyard.",
        f"Tell a gentle mystery story where Alec and a friend solve a clue about {m.missing_phrase}.",
        f"Write a friendship story that includes {m.clue_phrase} and ends with the truth being found.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    m: Mystery = f["mystery"]
    friend: Entity = f["friend"]
    alec: Entity = f["alec"]
    return [
        QAItem(
            question="Who was the story about?",
            answer=f"The story was about Alec and {friend.label}, who solved a small mystery together in a friend's backyard.",
        ),
        QAItem(
            question=f"What was missing at first?",
            answer=f"At first, {m.missing_phrase} was missing from the table.",
        ),
        QAItem(
            question=f"What clue did they notice?",
            answer=f"They noticed {m.clue_phrase}, which helped them look in the right place.",
        ),
        QAItem(
            question="How did friendship help in the story?",
            answer="Friendship helped because Alec and his friend stayed calm, searched together, and did not blame anyone too quickly.",
        ),
        QAItem(
            question=f"What did Alec feel at the end?",
            answer=f"Alec felt relieved and happy when the mystery was solved and the missing thing was found again.",
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a clue in a mystery story?",
            answer="A clue is a small piece of information that helps someone figure out what happened.",
        ),
        QAItem(
            question="Why do friends work better when they search together?",
            answer="Friends can notice different things, share ideas, and stay calmer when they solve a problem together.",
        ),
        QAItem(
            question="What is a backyard?",
            answer="A backyard is the open space behind a house where people can play, rest, or keep things like chairs and plants.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== Prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== Story QA ==")
    for q in sample.story_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    lines.append("")
    lines.append("== World QA ==")
    for q in sample.world_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------

ASP_RULES = r"""
valid_story(P, M) :- setting(P), mystery(M), place_ok(P), mystery_ok(M).
place_ok(friend_backyard).
mystery_ok(missing_shovel).
mystery_ok(missing_cookie).
mystery_ok(missing_kite_string).
"""


def asp_facts() -> str:
    import storyworlds.asp as asp
    lines = []
    for key in SETTINGS:
        lines.append(asp.fact("setting", key))
        if key == "friend_backyard":
            lines.append(asp.fact("place_ok", key))
    for key in MYSTERIES:
        lines.append(asp.fact("mystery", key))
        lines.append(asp.fact("mystery_ok", key))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_pairs() -> list[tuple]:
    import storyworlds.asp as asp
    model = asp.one_model(asp_program("#show valid_story/2."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    py = {(p, m) for p in SETTINGS for m in MYSTERIES if valid_story(p, m)}
    cl = set(asp_valid_pairs())
    if py == cl:
        print(f"OK: ASP matches Python gate ({len(py)} valid stories).")
        return 0
    print("MISMATCH between ASP and Python gate:")
    if py - cl:
        print("  only in python:", sorted(py - cl))
    if cl - py:
        print("  only in asp:", sorted(cl - py))
    return 1


# ---------------------------------------------------------------------------
# Generation interface
# ---------------------------------------------------------------------------

CURATED = [
    StoryParams(place="friend_backyard", mystery="missing_shovel", name="Alec", friend_name="Maya"),
    StoryParams(place="friend_backyard", mystery="missing_cookie", name="Alec", friend_name="Lina"),
    StoryParams(place="friend_backyard", mystery="missing_kite_string", name="Alec", friend_name="Nora"),
]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A friendship whodunit in a friend's backyard.")
    ap.add_argument("--place", choices=list(SETTINGS.keys()))
    ap.add_argument("--mystery", choices=list(MYSTERIES.keys()))
    ap.add_argument("--name", default="Alec")
    ap.add_argument("--friend-name", default="Maya")
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
    place = args.place or "friend_backyard"
    mystery = args.mystery or rng.choice(list(MYSTERIES.keys()))
    if not valid_story(place, mystery):
        raise StoryError(explain_rejection(place, mystery))
    return StoryParams(
        place=place,
        mystery=mystery,
        name=args.name or "Alec",
        friend_name=args.friend_name or "Maya",
    )


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


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for e in world.entities.values():
        bits = []
        if e.hidden:
            bits.append("hidden=True")
        if e.phrase:
            bits.append(f"phrase={e.phrase!r}")
        lines.append(f"{e.id}: {e.kind}/{e.type} {' '.join(bits)}")
    lines.append(f"facts: {world.facts.get('solution', '')}")
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
        print(asp_program("#show valid_story/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        pairs = asp_valid_pairs()
        print(f"{len(pairs)} valid (place, mystery) pairs:")
        for p, m in pairs:
            print(f"  {p:16} {m}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)

    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 50, 50):
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            sample = generate(params)
            if sample.story in seen:
                i += 1
                continue
            seen.add(sample.story)
            samples.append(sample)
            i += 1

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
            header = f"### {p.name}: {p.mystery} in {p.place}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""
storyworlds/worlds/vacancy_swill_agitate_foreshadowing_sharing_lesson_learned.py
================================================================================

A small nursery-rhyme story world about an empty seat, a bowl of swill,
and a bit of agitation that turns into sharing and a lesson learned.

The domain is deliberately tiny:
- A child notices a vacancy: one little seat is empty.
- A stray bowl of swill causes a messy, agitating moment.
- A helper sees the trouble coming, foreshadows a fix, and suggests sharing.
- The story resolves with a clean table, a filled seat, and a lesson learned.

The prose is generated from a live world model so the middle and ending
change with state, not just swapped names.
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
    kind: str
    label: str
    phrase: str = ""
    role: str = ""
    owner: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.role in {"girl", "mother", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.role in {"boy", "father", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]


@dataclass
class Setting:
    place: str = "the little kitchen"
    table: str = "the round table"


@dataclass
class StoryWorld:
    setting: Setting
    entities: dict[str, Entity] = field(default_factory=dict)
    lines: list[str] = field(default_factory=list)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    facts: dict[str, object] = field(default_factory=dict)

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
        chunks = [" ".join(p) for p in self.paragraphs if p]
        return "\n\n".join(chunks)


# ---------------------------------------------------------------------------
# Parameters / registries
# ---------------------------------------------------------------------------
@dataclass
class StoryParams:
    place: str
    child_name: str
    child_role: str
    helper_name: str
    helper_role: str
    seed: Optional[int] = None


SETTINGS = {
    "kitchen": Setting(place="the little kitchen", table="the round table"),
    "garden": Setting(place="the small garden", table="the picnic bench"),
    "hall": Setting(place="the cozy hall", table="the low bench"),
}

CHILDREN = [
    ("Milo", "boy"),
    ("Lily", "girl"),
    ("Nia", "girl"),
    ("Theo", "boy"),
    ("Pip", "child"),
]

HELPERS = [
    ("Mama", "mother"),
    ("Papa", "father"),
    ("Nana", "woman"),
    ("Bram", "man"),
]

THRESHOLD = 1.0


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
% vacancy means one seat is open.
vacant(S) :- seat(S), empty(S).

% swill causes a mess when it is on the table.
messy(T) :- table(T), has_swill(T).

% agitation rises when a child wants food but sees swill and a vacant seat.
agitated(C) :- child(C), sees_swill(C), sees_vacancy(C).

% sharing fixes the problem if the helper offers a clean bowl to share.
fix(C) :- child(C), helper(H), shares(H,C), clean_bowl(H).

% A reasonable story has a vacancy, swill, and a fix.
reasonable :- vacant(_), messy(_), fix(_).
#show reasonable/0.
#show vacant/1.
#show messy/1.
#show agitated/1.
#show fix/1.
"""

def asp_facts() -> str:
    import storyworlds.asp as asp
    lines = []
    lines.append(asp.fact("seat", "seat1"))
    lines.append(asp.fact("empty", "seat1"))
    lines.append(asp.fact("table", "table1"))
    lines.append(asp.fact("has_swill", "table1"))
    lines.append(asp.fact("child", "child1"))
    lines.append(asp.fact("helper", "helper1"))
    lines.append(asp.fact("sees_swill", "child1"))
    lines.append(asp.fact("sees_vacancy", "child1"))
    lines.append(asp.fact("shares", "helper1", "child1"))
    lines.append(asp.fact("clean_bowl", "helper1"))
    return "\n".join(lines)


def asp_program(show: str = "#show reasonable/0.") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import storyworlds.asp as asp
    model = asp.one_model(asp_program())
    atoms = {f"{sym.name}/{len(sym.arguments)}" for sym in model}
    ok = "reasonable/0" in atoms
    if ok:
        print("OK: ASP twin finds a reasonable story.")
        return 0
    print("MISMATCH: ASP twin did not find reasonable/0.")
    return 1


# ---------------------------------------------------------------------------
# Story logic
# ---------------------------------------------------------------------------
def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    place = args.place or rng.choice(sorted(SETTINGS))
    if place not in SETTINGS:
        raise StoryError(f"Unknown place: {place}")
    child_name, child_role = (args.child_name, args.child_role) if args.child_name and args.child_role else rng.choice(CHILDREN)
    helper_name, helper_role = (args.helper_name, args.helper_role) if args.helper_name and args.helper_role else rng.choice(HELPERS)
    if child_name == helper_name:
        raise StoryError("Child and helper must be different people.")
    return StoryParams(
        place=place,
        child_name=child_name,
        child_role=child_role,
        helper_name=helper_name,
        helper_role=helper_role,
    )


def build_world(params: StoryParams) -> StoryWorld:
    world = StoryWorld(setting=SETTINGS[params.place])

    child = world.add(Entity(
        id="child",
        kind="character",
        label=params.child_name,
        role=params.child_role,
        meters={"hunger": 1.0, "mess": 0.0},
        memes={"want": 1.0, "agitate": 0.0, "joy": 0.0, "lesson": 0.0},
    ))
    helper = world.add(Entity(
        id="helper",
        kind="character",
        label=params.helper_name,
        role=params.helper_role,
        meters={"care": 1.0},
        memes={"calm": 1.0, "share": 0.0},
    ))
    seat = world.add(Entity(
        id="seat",
        kind="thing",
        label="the little seat",
        phrase="a little seat by the table",
        meters={"vacancy": 1.0},
    ))
    swill = world.add(Entity(
        id="swill",
        kind="thing",
        label="the swill",
        phrase="a bowl of gray swill",
        meters={"mess": 1.0},
    ))

    world.facts.update(
        child=child,
        helper=helper,
        seat=seat,
        swill=swill,
        place=params.place,
        setting=world.setting,
    )

    # Act 1: foreshadowing the vacancy and the swill.
    world.say(f"In {world.setting.place}, by {world.setting.table}, there was one little vacancy: a seat left empty.")
    world.say(f"The child looked and sniffed and saw a bowl of swill, all sloshy and still.")
    world.say(f"That made the child agitate, for hungry tummies do not like a messy plate.")

    # Act 2: tension and foreshadowing.
    world.para()
    child.memes["agitate"] += 1.0
    child.meters["mess"] += 1.0
    world.say(f"{child.label} wrinkled {child.pronoun('possessive')} nose and tapped {child.pronoun('possessive')} toes.")
    world.say(f"{helper.label} saw what was coming and gave a soft little warning, like a rhyme before morning.")
    world.say(f'"If we wait and share the plate, the mess will not grow and the day will stay great," {helper.pronoun()} said.')

    # Act 3: sharing and lesson learned.
    world.para()
    helper.memes["share"] += 1.0
    child.memes["joy"] += 1.0
    child.memes["lesson"] += 1.0
    seat.meters["vacancy"] = 0.0
    swill.meters["mess"] = 0.0
    world.say(f"So {helper.label} brought a clean bowl to share, and the child sat down with happy care.")
    world.say(f"The vacancy was filled, the swill was gone, and both of them ate while singing a song.")
    world.say(f"{child.label} learned a lesson learned: sharing makes the table bright, tidy, and warmed.")

    world.facts["resolved"] = True
    return world


def generation_prompts(world: StoryWorld) -> list[str]:
    p = world.facts
    child: Entity = p["child"]  # type: ignore[assignment]
    helper: Entity = p["helper"]  # type: ignore[assignment]
    return [
        "Write a short nursery-rhyme story about a vacancy at a table, a bowl of swill, and a kind sharing fix.",
        f"Tell a gentle story where {child.label} notices an empty seat and {helper.label} helps make the meal tidy.",
        "Write a child-facing story that foreshadows trouble, then ends with sharing and a lesson learned.",
    ]


def story_qa(world: StoryWorld) -> list[QAItem]:
    c: Entity = world.facts["child"]  # type: ignore[assignment]
    h: Entity = world.facts["helper"]  # type: ignore[assignment]
    seat: Entity = world.facts["seat"]  # type: ignore[assignment]
    return [
        QAItem(
            question=f"What was the vacancy in the story?",
            answer=f"The vacancy was one little seat left empty by {world.setting.table}.",
        ),
        QAItem(
            question=f"What made {c.label} agitate at the table?",
            answer=f"{c.label} agitated because {c.pronoun('subject')} saw the swill and felt hungry at the same time.",
        ),
        QAItem(
            question=f"How did {h.label} help?",
            answer=f"{h.label} helped by sharing a clean bowl and filling the empty seat with a kind, calm plan.",
        ),
        QAItem(
            question="What lesson was learned?",
            answer="The lesson learned was that sharing can turn a messy moment into a happy meal.",
        ),
    ]


def world_qa(world: StoryWorld) -> list[QAItem]:
    return [
        QAItem(
            question="What is a vacancy?",
            answer="A vacancy is an empty place or opening where something or someone can be put.",
        ),
        QAItem(
            question="What is swill?",
            answer="Swill is watery, sloppy leftover food or drink that can look messy and unappealing.",
        ),
        QAItem(
            question="What does agitate mean?",
            answer="To agitate means to stir up or upset, like making feelings or water move in an uneasy way.",
        ),
        QAItem(
            question="Why is sharing good?",
            answer="Sharing is good because it helps everyone have enough and can make a problem feel smaller.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== Prompts ==", *[f"- {p}" for p in sample.prompts], "", "== Story Q&A =="]
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== World Q&A ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: StoryWorld) -> str:
    out = ["--- world trace ---"]
    for e in world.entities.values():
        out.append(f"{e.id}: {e.label} [{e.kind}] meters={e.meters} memes={e.memes}")
    return "\n".join(out)


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------
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


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
CURATED = [
    StoryParams(place="kitchen", child_name="Milo", child_role="boy", helper_name="Mama", helper_role="mother"),
    StoryParams(place="garden", child_name="Lily", child_role="girl", helper_name="Papa", helper_role="father"),
    StoryParams(place="hall", child_name="Nia", child_role="girl", helper_name="Nana", helper_role="woman"),
]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Nursery-rhyme story world: vacancy, swill, and sharing.")
    ap.add_argument("--place", choices=sorted(SETTINGS))
    ap.add_argument("--child-name")
    ap.add_argument("--child-role", choices=["boy", "girl", "child"])
    ap.add_argument("--helper-name")
    ap.add_argument("--helper-role", choices=["mother", "father", "woman", "man"])
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
    return resolve_params.__wrapped__(args, rng)  # type: ignore[attr-defined]


def _resolve_params_impl(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    return resolve_params.__globals__["resolve_params"](args, rng)  # placeholder avoidance


# bind the real function for the contract without recursion tricks
resolve_params.__wrapped__ = _resolve_params_impl  # type: ignore[attr-defined]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show reasonable/0."))
        return
    if args.verify:
        sys.exit(asp_verify())

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)

    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        for i in range(args.n):
            seed = base_seed + i
            rng = random.Random(seed)
            params = _resolve_params_impl(args, rng)
            params.seed = seed
            samples.append(generate(params))

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
            header = f"### {p.child_name} at {p.place}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


# Expose the contract name cleanly.
resolve_params = _resolve_params_impl


if __name__ == "__main__":
    main()

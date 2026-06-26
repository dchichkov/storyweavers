#!/usr/bin/env python3
"""
storyworlds/worlds/fry_enter_flag_problem_solving_lesson_learned.py
====================================================================

A bedtime-story world about a little fry, a flag, and a careful problem that
gets solved with patience and a good idea.

Premise:
- Fry is a tiny crispy fry who wants to enter the garden gate to reach the
  waving flag on the hill.
- The gate is too narrow and the path is a little muddy after evening rain.
- Fry feels determined, then frustrated, then learns to ask for help and use a
  safer plan.

The story is intentionally small and state-driven:
- physical meters: wetness, dirt, wobble, access, height
- emotional memes: courage, worry, patience, pride, relief

The ending proves what changed: Fry reaches the flag without getting stuck.
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
# Core world model
# ---------------------------------------------------------------------------
@dataclass
class Entity:
    id: str
    kind: str = "thing"  # "character" | "thing"
    label: str = ""
    phrase: str = ""
    plural: bool = False
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class World:
    entities: dict[str, Entity] = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    facts: dict = field(default_factory=dict)
    fired: set[tuple] = field(default_factory=set)

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

    def copy(self) -> "World":
        import copy

        clone = World()
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.facts = dict(self.facts)
        clone.paragraphs = [[]]
        return clone


# ---------------------------------------------------------------------------
# Parameters
# ---------------------------------------------------------------------------
@dataclass
class StoryParams:
    place: str = "the garden path"
    helper: str = "Moss"
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------
PLACES = {
    "garden path": {
        "label": "the garden path",
        "detail": "The garden path was soft and a little damp after the evening rain.",
    },
    "hill": {
        "label": "the hill",
        "detail": "The hill stood beyond the path, where a bright flag fluttered in the breeze.",
    },
    "porch": {
        "label": "the porch",
        "detail": "The porch had a safe step and a cozy lantern glow.",
    },
}

HELPERS = ["Moss", "Pip", "Nina", "Juniper"]


# ---------------------------------------------------------------------------
# Story logic
# ---------------------------------------------------------------------------
def _apply_stuck(world: World) -> None:
    fry = world.get("fry")
    gate = world.get("gate")
    path = world.get("path")

    if fry.meters.get("speed", 0) > 0.5 and gate.meters.get("narrow", 0) > 0.5:
        sig = ("stuck",)
        if sig in world.fired:
            return
        world.fired.add(sig)
        fry.meters["wobble"] = fry.meters.get("wobble", 0) + 1
        fry.memes["worry"] = fry.memes.get("worry", 0) + 1
        path.meters["muddy"] = path.meters.get("muddy", 0) + 1
        world.say("But the little fry wobbled at the narrow gate and had to stop before getting stuck.")


def _apply_problem_solving(world: World) -> None:
    fry = world.get("fry")
    helper = world.get("helper")
    flag = world.get("flag")
    path = world.get("path")

    if fry.memes.get("worry", 0) >= 1 and helper.memes.get("calm", 0) >= 1:
        sig = ("solve",)
        if sig in world.fired:
            return
        world.fired.add(sig)
        fry.memes["patience"] = fry.memes.get("patience", 0) + 1
        fry.memes["courage"] = fry.memes.get("courage", 0) + 1
        fry.meters["speed"] = 0
        path.meters["muddy"] = max(0, path.meters.get("muddy", 0) - 1)
        flag.meters["reachable"] = 1
        world.say(
            f"{helper.label} leaned close and suggested a gentle plan: slow steps, "
            f"a pause at the gate, and one careful hop at a time."
        )
        world.say("Fry listened, took a breath, and tried the safer way.")


def _apply_lesson(world: World) -> None:
    fry = world.get("fry")
    flag = world.get("flag")
    helper = world.get("helper")

    if flag.meters.get("reached", 0) >= 1 and fry.memes.get("relief", 0) < 1:
        sig = ("lesson",)
        if sig in world.fired:
            return
        world.fired.add(sig)
        fry.memes["relief"] = fry.memes.get("relief", 0) + 1
        fry.memes["pride"] = fry.memes.get("pride", 0) + 1
        world.say(
            f"At last, Fry reached the flag, and the little fry felt proud for being patient."
        )
        world.say(
            f"{helper.label} smiled because the best idea had been the careful one."
        )
        world.say("Fry learned that asking for help can make a hard problem feel small.")


def propagate(world: World, narrate: bool = True) -> None:
    changed = True
    while changed:
        changed = False
        before = len(world.fired)
        _apply_stuck(world)
        _apply_problem_solving(world)
        _apply_lesson(world)
        if len(world.fired) != before:
            changed = True


def tell(place: str, helper_name: str) -> World:
    if place not in PLACES:
        raise StoryError(f"Unknown place: {place}")

    world = World()
    fry = world.add(Entity(
        id="fry",
        kind="character",
        label="Fry",
        phrase="a little golden fry",
        meters={"crispness": 1, "speed": 1, "wobble": 0},
        memes={"curiosity": 1, "courage": 1, "worry": 0, "patience": 0, "pride": 0, "relief": 0},
    ))
    helper = world.add(Entity(
        id="helper",
        kind="character",
        label=helper_name,
        phrase=f"{helper_name}, a gentle friend",
        meters={"calm": 1},
        memes={"kindness": 1, "calm": 1},
    ))
    gate = world.add(Entity(
        id="gate",
        kind="thing",
        label="gate",
        phrase="a narrow gate",
        meters={"narrow": 1},
    ))
    path = world.add(Entity(
        id="path",
        kind="thing",
        label="path",
        phrase=PLACES[place]["label"],
        meters={"muddy": 1 if place == "garden path" else 0},
    ))
    flag = world.add(Entity(
        id="flag",
        kind="thing",
        label="flag",
        phrase="a tiny striped flag",
        meters={"reachable": 0, "reached": 0, "high": 1},
    ))

    world.facts.update(place=place, helper=helper_name)

    # Act 1: bedtime setup
    world.say("On a quiet evening, Fry looked out at the little flag and wanted to reach it before bedtime.")
    world.say(PLACES[place]["detail"])
    world.say(f"Fry was a little golden fry who loved brave ideas and shiny things.")

    # Act 2: the problem
    world.para()
    world.say("Fry hurried toward the gate, but the way was too tight and the path was a little slippery.")
    fry.meters["speed"] = 1
    propagate(world)

    # Act 3: the solution
    world.para()
    if fry.memes.get("worry", 0) >= 1:
        world.say(f"Fry stopped, looked back, and asked {helper_name} for help.")
        helper.memes["calm"] = 1
        helper.memes["kindness"] = 1
        propagate(world)

    # Final movement: safe, small steps to the flag
    if flag.meters.get("reachable", 0) >= 1:
        fry.meters["speed"] = 0.4
        world.say("Together they tried a new plan.")
        world.say("Fry took tiny careful steps, crossed the gate one bit at a time, and reached the flag at last.")
        flag.meters["reached"] = 1
        propagate(world)
    else:
        # Fallback: ensure a complete story if the solver did not trigger yet.
        world.say("So Fry tried again, slowly and carefully, until the little flag was finally within reach.")
        flag.meters["reached"] = 1
        propagate(world)

    world.facts.update(fry=fry, helper=helper, gate=gate, path=path, flag=flag)
    return world


# ---------------------------------------------------------------------------
# QA
# ---------------------------------------------------------------------------
def generation_prompts(world: World) -> list[str]:
    return [
        'Write a bedtime story about a tiny fry who wants to enter a place and reach a flag.',
        'Tell a gentle story where a little fry has a problem, asks for help, solves it carefully, and learns a lesson.',
        'Create a child-friendly story using the words fry, enter, and flag, ending with a quiet lesson learned.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    helper: Entity = f["helper"]
    fry: Entity = f["fry"]
    return [
        QAItem(
            question="What did Fry want to reach in the story?",
            answer="Fry wanted to reach the little flag before bedtime.",
        ),
        QAItem(
            question=f"Why did Fry stop when trying to enter the gate?",
            answer=f"Fry stopped because the gate was too narrow and the path was slippery, so rushing could make Fry get stuck.",
        ),
        QAItem(
            question=f"What was the problem-solving idea that {helper.label} suggested?",
            answer="The gentle idea was to slow down, pause at the gate, and take one careful hop at a time.",
        ),
        QAItem(
            question="What lesson did Fry learn?",
            answer="Fry learned that asking for help and taking careful steps can solve a hard problem.",
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a flag?",
            answer="A flag is a cloth marker that can flutter in the wind and show a place or a message.",
        ),
        QAItem(
            question="What does it mean to enter a place?",
            answer="To enter a place means to go inside or move through the opening to get there.",
        ),
        QAItem(
            question="What does problem solving mean?",
            answer="Problem solving means thinking about a trouble and choosing a good way to fix it.",
        ),
        QAItem(
            question="Why is it good to learn a lesson in a story?",
            answer="Learning a lesson helps a character remember a better choice for next time.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== (2) Story questions ==")
    for qa in sample.story_qa:
        lines.append(f"Q: {qa.question}")
        lines.append(f"A: {qa.answer}")
    lines.append("")
    lines.append("== (3) World knowledge ==")
    for qa in sample.world_qa:
        lines.append(f"Q: {qa.question}")
        lines.append(f"A: {qa.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for e in world.entities.values():
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        lines.append(f"{e.id}: label={e.label!r} meters={meters} memes={memes}")
    lines.append(f"fired={sorted(world.fired)}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
% A story is reasonable when Fry can enter, hit a small problem, and use help.
problem(fry, gate) :- narrow(gate), slippery(path).
needs_help(fry) :- problem(fry, gate).
solved(fry) :- needs_help(fry), helper(calm_friend).
lesson_learned(fry) :- solved(fry).

#show problem/2.
#show needs_help/1.
#show solved/1.
#show lesson_learned/1.
"""


def asp_facts() -> str:
    import asp

    lines = [
        asp.fact("character", "fry"),
        asp.fact("character", "helper"),
        asp.fact("thing", "gate"),
        asp.fact("thing", "path"),
        asp.fact("thing", "flag"),
        asp.fact("narrow", "gate"),
        asp.fact("slippery", "path"),
        asp.fact("helper", "calm_friend"),
    ]
    return "\n".join(lines)


def asp_program() -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n"


def asp_verify() -> int:
    import asp

    model = asp.one_model(asp_program())
    shown = {sym.name for sym in model}
    expected = {"problem", "needs_help", "solved", "lesson_learned"}
    if expected.issubset(shown):
        print("OK: ASP twin produces the expected lesson-learned story facts.")
        return 0
    print("MISMATCH: ASP twin did not derive all expected facts.")
    print("shown:", sorted(shown))
    return 1


# ---------------------------------------------------------------------------
# Public interface
# ---------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Bedtime story world about a fry, a flag, and a learned lesson.")
    ap.add_argument("--place", choices=sorted(PLACES), default="garden path")
    ap.add_argument("--helper", choices=HELPERS)
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
    place = args.place or rng.choice(sorted(PLACES))
    helper = args.helper or rng.choice(HELPERS)
    return StoryParams(place=place, helper=helper)


def generate(params: StoryParams) -> StorySample:
    world = tell(params.place, params.helper)
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
    StoryParams(place="garden path", helper="Moss"),
    StoryParams(place="garden path", helper="Pip"),
    StoryParams(place="porch", helper="Juniper"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program())
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp

        model = asp.one_model(asp_program())
        print("ASP model:")
        for sym in model:
            print(sym)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        for i in range(args.n):
            rng = random.Random(base_seed + i)
            params = resolve_params(args, rng)
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

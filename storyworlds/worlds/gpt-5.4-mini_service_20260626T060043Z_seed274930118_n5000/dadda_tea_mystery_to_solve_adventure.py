#!/usr/bin/env python3
"""
storyworlds/worlds/dadda_tea_mystery_to_solve_adventure.py
==========================================================

A tiny adventure storyworld about a child, dadda, and a tea mystery to solve.

Premise:
- A child and dadda are preparing tea in a small place.
- Something important for tea goes missing or gets changed.
- The child follows clues on a simple adventure.
- They solve the mystery together and end with tea shared in a calm, happy scene.

This world keeps the story grounded in a simulated state:
- physical meters track things like warmth, wetness, missingness, mess, and foundness
- emotional memes track worry, curiosity, confidence, relief, and closeness

It also includes an inline ASP twin and a Python reasonableness gate.
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
# World entities
# ---------------------------------------------------------------------------
@dataclass
class Entity:
    id: str
    kind: str = "thing"  # character | thing | clue | place
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "child"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        if self.type in {"dadda", "dad", "father"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str
    indoors: bool
    routes: list[str]


@dataclass
class Mystery:
    id: str
    title: str
    missing: str
    culprit: str
    clue_kind: str
    fix_kind: str
    risk: str
    solved_with: str
    tags: set[str] = field(default_factory=set)


@dataclass
class StoryParams:
    place: str
    mystery: str
    child_name: str
    child_type: str
    dadda_name: str
    seed: Optional[int] = None


class World:
    def __init__(self, setting: Setting):
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.facts: dict = {}
        self.paragraphs: list[list[str]] = [[]]
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


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------
SETTINGS = {
    "kitchen": Setting(place="the kitchen", indoors=True, routes=["hallway", "garden door"]),
    "garden": Setting(place="the garden", indoors=False, routes=["porch", "hedge path"]),
    "porch": Setting(place="the porch", indoors=False, routes=["kitchen", "garden"]),
}

MYSTERIES = {
    "missing_spoon": Mystery(
        id="missing_spoon",
        title="the missing tea spoon",
        missing="tea spoon",
        culprit="the cat",
        clue_kind="pawprints",
        fix_kind="spoon",
        risk="the tea would be hard to stir",
        solved_with="a spoon found under the mat",
        tags={"cat", "spoon", "tea", "pawprints"},
    ),
    "spilled_tea": Mystery(
        id="spilled_tea",
        title="the spilled tea",
        missing="tea",
        culprit="a bump from the broom",
        clue_kind="wet trail",
        fix_kind="cloth",
        risk="the cups would stay empty",
        solved_with="a cloth and a fresh pot of tea",
        tags={"wet", "tea", "cloth"},
    ),
    "missing_teabags": Mystery(
        id="missing_teabags",
        title="the missing tea bags",
        missing="tea bags",
        culprit="the wind",
        clue_kind="rustling leaves",
        fix_kind="jar",
        risk="there would be no tea to brew",
        solved_with="tea bags tucked into a jar by the window",
        tags={"wind", "jar", "tea"},
    ),
}

CHILD_NAMES = ["Mia", "Noah", "Lily", "Ava", "Leo", "Ben", "Zoe", "Finn"]
DADDA_NAMES = ["Dadda", "Papa", "Dad", "Dada"]
CHILD_TYPES = ["girl", "boy"]


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
% A mystery is solvable when the place supports the search route and the fix
% matches the missing thing.
solvable(M) :- mystery(M), has_route(M), has_fix(M).

solved(M) :- solvable(M), mystery(M).

% A child and dadda can share tea after the mystery is solved.
happy_end(Tea, M) :- solved(M), tea_ready(Tea).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid, s in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        if s.indoors:
            lines.append(asp.fact("indoors", sid))
        for r in s.routes:
            lines.append(asp.fact("route", sid, r))
    for mid, m in MYSTERIES.items():
        lines.append(asp.fact("mystery", mid))
        lines.append(asp.fact("missing", mid, m.missing))
        lines.append(asp.fact("culprit", mid, m.culprit))
        lines.append(asp.fact("clue_kind", mid, m.clue_kind))
        lines.append(asp.fact("fix_kind", mid, m.fix_kind))
        lines.append(asp.fact("risk", mid, m.risk))
        lines.append(asp.fact("solved_with", mid, m.solved_with))
        for t in sorted(m.tags):
            lines.append(asp.fact("tag", mid, t))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_mysteries() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show solvable/1."))
    return sorted(set(asp.atoms(model, "solvable")))


def asp_verify() -> int:
    py = set(valid_mysteries())
    cl = set(asp_valid_mysteries())
    if py == cl:
        print(f"OK: clingo gate matches valid_mysteries() ({len(py)} mysteries).")
        return 0
    print("MISMATCH between clingo and Python reasonableness gate:")
    if cl - py:
        print("  only in clingo:", sorted(cl - py))
    if py - cl:
        print("  only in python:", sorted(py - cl))
    return 1


# ---------------------------------------------------------------------------
# Reasonableness gate
# ---------------------------------------------------------------------------
def valid_mysteries() -> list[str]:
    return list(MYSTERIES.keys())


def explain_rejection(mystery: Mystery, place: Setting) -> str:
    if place.indoors and mystery.id == "missing_teabags":
        return "(No story: this mystery does not have a clear indoor clue path here.)"
    if not place.indoors and mystery.id == "spilled_tea":
        return "(No story: a spilled-tea mystery needs a place with a clear table and cloth to search.)"
    return "(No story: that combination is not a good fit for a short tea mystery adventure.)"


# ---------------------------------------------------------------------------
# Story logic
# ---------------------------------------------------------------------------
def build_world(params: StoryParams) -> World:
    setting = SETTINGS[params.place]
    mystery = MYSTERIES[params.mystery]
    world = World(setting)

    child = world.add(Entity(id="child", kind="character", type=params.child_type, label=params.child_name))
    dadda = world.add(Entity(id="dadda", kind="character", type="dadda", label=params.dadda_name))

    tea = world.add(Entity(
        id="tea",
        kind="thing",
        type="tea",
        label="tea",
        phrase="warm tea",
        meters={"warmth": 1.0, "missing": 0.0, "ready": 0.0},
        memes={"comfort": 0.0},
    ))
    missing = world.add(Entity(
        id=mystery.missing.replace(" ", "_"),
        kind="thing",
        type="thing",
        label=mystery.missing,
        phrase=mystery.missing,
        meters={"missing": 0.0, "found": 0.0},
    ))
    clue = world.add(Entity(
        id="clue",
        kind="clue",
        type="clue",
        label=mystery.clue_kind,
        phrase=mystery.clue_kind,
        meters={"noticed": 0.0},
    ))
    fix = world.add(Entity(
        id="fix",
        kind="thing",
        type="tool",
        label=mystery.fix_kind,
        phrase=mystery.fix_kind,
        meters={"used": 0.0},
    ))

    world.facts.update(
        child=child,
        dadda=dadda,
        tea=tea,
        missing=missing,
        clue=clue,
        fix=fix,
        mystery=mystery,
        setting=setting,
    )
    return world


def tell_story(world: World) -> None:
    f = world.facts
    child: Entity = f["child"]
    dadda: Entity = f["dadda"]
    tea: Entity = f["tea"]
    mystery: Mystery = f["mystery"]
    setting: Setting = f["setting"]

    child.memes["curiosity"] = 1.0
    dadda.memes["calm"] = 1.0
    tea.meters["warmth"] = 1.0
    tea.meters["ready"] = 0.0

    world.say(
        f"{child.label} loved adventure days with {dadda.label}. "
        f"They were in {setting.place}, where the kettle was ready and the air smelled like tea."
    )
    world.say(
        f"Then {dadda.label} frowned. The {mystery.missing} was gone, and that meant {mystery.risk}."
    )

    world.para()
    child.memes["curiosity"] += 1.0
    world.say(
        f"{child.label} became a little detective and looked for a clue. "
        f"Near the doorway, {child.pronoun('subject')} noticed {mystery.clue_kind}."
    )
    world.say(
        f"{dadda.label} followed beside {child.pronoun('object')}, quiet and watchful, "
        f"because every good mystery needed two careful eyes."
    )

    world.para()
    if mystery.id == "missing_spoon":
        world.say(
            f"The clue led under the mat. There, tucked in the shadow, was the spoon, "
            f"and the cat was sitting nearby with a very innocent face."
        )
    elif mystery.id == "spilled_tea":
        world.say(
            f"The clue led to the broom by the table. A little wet trail showed where the cup had bumped over."
        )
    else:
        world.say(
            f"The clue led to the window, where the wind had nudged the tea bags into a jar on the sill."
        )

    world.say(
        f"{child.label} pointed proudly. {dadda.label} smiled because the mystery was solved at last."
    )
    tea.meters["ready"] = 1.0
    tea.memes["comfort"] = 1.0
    f["missing"].meters["found"] = 1.0
    f["clue"].meters["noticed"] = 1.0
    f["fix"].meters["used"] = 1.0
    child.memes["confidence"] = 1.0
    child.memes["joy"] = 1.0
    dadda.memes["relief"] = 1.0

    world.para()
    if mystery.id == "missing_spoon":
        world.say(
            f"{dadda.label} stirred the tea with the found spoon, and the warm smell drifted through the room."
        )
    elif mystery.id == "spilled_tea":
        world.say(
            f"{dadda.label} wiped the table dry, poured fresh tea, and the cups were full again."
        )
    else:
        world.say(
            f"{dadda.label} opened the jar, found the tea bags, and soon the kettle was making a happy hum."
        )
    world.say(
        f"{child.label} and {dadda.label} sat together with their tea, and the little adventure ended in a cozy sip."
    )


def generation_prompts(world: World) -> list[str]:
    m: Mystery = world.facts["mystery"]
    s: Setting = world.facts["setting"]
    return [
        f"Write a short adventure story for a child and dadda in {s.place} about {m.title}.",
        f"Tell a gentle mystery story where a child helps dadda solve a tea problem with clues.",
        f"Write a simple story that includes tea, a clue, and a happy ending after the mystery is solved.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child: Entity = f["child"]
    dadda: Entity = f["dadda"]
    mystery: Mystery = f["mystery"]
    setting: Setting = f["setting"]

    return [
        QAItem(
            question=f"Who went on the tea adventure in {setting.place}?",
            answer=f"{child.label} and {dadda.label} went on the tea adventure together.",
        ),
        QAItem(
            question=f"What was the mystery in the story?",
            answer=f"The mystery was {mystery.title}, and they had to solve it before the tea could be enjoyed.",
        ),
        QAItem(
            question=f"What clue helped them solve the mystery?",
            answer=f"They found {mystery.clue_kind}, and that clue led them to the answer.",
        ),
        QAItem(
            question=f"How did the story end?",
            answer=f"It ended with {child.label} and {dadda.label} sharing tea after the mystery was solved.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is tea?",
            answer="Tea is a warm drink people make by putting tea leaves or tea bags in hot water.",
        ),
        QAItem(
            question="What does a clue do in a mystery?",
            answer="A clue gives a small hint that helps a detective figure out what happened.",
        ),
        QAItem(
            question="Why do people solve mysteries?",
            answer="People solve mysteries to understand what went missing, what changed, or who caused a problem.",
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
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        parts = []
        if meters:
            parts.append(f"meters={meters}")
        if memes:
            parts.append(f"memes={memes}")
        lines.append(f"  {e.id:10} ({e.kind:7}) {' '.join(parts)}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Tea mystery adventure storyworld with dadda.")
    ap.add_argument("--place", choices=SETTINGS.keys())
    ap.add_argument("--mystery", choices=MYSTERIES.keys())
    ap.add_argument("--name")
    ap.add_argument("--dadda-name", dest="dadda_name")
    ap.add_argument("--child-type", choices=CHILD_TYPES)
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
    mystery_id = args.mystery or rng.choice(valid_mysteries())
    place = args.place or rng.choice(list(SETTINGS.keys()))

    if args.mystery and args.place:
        m = MYSTERIES[args.mystery]
        s = SETTINGS[args.place]
        if args.mystery == "missing_teabags" and s.indoors is False:
            pass
        elif args.mystery == "spilled_tea" and s.indoors is False:
            raise StoryError(explain_rejection(m, s))

    name = args.name or rng.choice(CHILD_NAMES)
    dadda_name = args.dadda_name or rng.choice(DADDA_NAMES)
    child_type = args.child_type or rng.choice(CHILD_TYPES)

    return StoryParams(
        place=place,
        mystery=mystery_id,
        child_name=name,
        child_type=child_type,
        dadda_name=dadda_name,
    )


def generate(params: StoryParams) -> StorySample:
    world = build_world(params)
    tell_story(world)
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


def asp_program_text(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program_text("#show solvable/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        model = asp.one_model(asp_program_text("#show solvable/1."))
        items = sorted(set(asp.atoms(model, "solvable")))
        print(f"{len(items)} solvable mysteries:")
        for (mid,) in items:
            print(f"  {mid}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        for mid in valid_mysteries():
            p = StoryParams(
                place="kitchen" if mid != "spilled_tea" else "kitchen",
                mystery=mid,
                child_name="Mia",
                child_type="girl",
                dadda_name="Dadda",
            )
            samples.append(generate(p))
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 50, 50):
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

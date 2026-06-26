#!/usr/bin/env python3
"""
Storyworld: piglet_suppress_problem_solving_reconciliation_mystery_to
=====================================================================

A small detective-story world for a curious piglet who tries to solve a mystery
without making a fuss, then learns that asking kindly works better than
suppressing worries.

Premise:
- A piglet detective notices a missing or misplaced item in a small setting.
- The piglet tries to suppress worry and solve it alone.
- The mystery becomes clearer through clues, and a helper or neighbor can join.
- The ending resolves with reconciliation: the piglet and another character
  understand each other, and the missing thing is found.

World model:
- Typed entities have physical meters and emotional memes.
- The simulated state drives narration; this is not a frozen paragraph.
- The story remains child-facing, concrete, and detective-like.

This file is self-contained except for the shared result containers and the lazy
ASP helper module.
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
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.meters:
            self.meters = {}
        if not self.memes:
            self.memes = {}

    def pronoun(self, case: str = "subject") -> str:
        if self.type == "piglet":
            return {"subject": "it", "object": "it", "possessive": "its"}[case]
        if self.type == "child":
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type == "adult":
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class Setting:
    place: str
    clue_place: str


@dataclass
class Mystery:
    label: str
    missing_item: str
    hidden_by: str
    solved_with: str
    worry_word: str
    clue_word: str
    solve_word: str
    reconcile_word: str


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict[str, object] = {}
        self.fired: set[tuple] = set()

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


@dataclass
class StoryParams:
    place: str
    mystery: str
    name: str
    helper: str
    seed: Optional[int] = None


SETTINGS = {
    "barn": Setting(place="the barn", clue_place="the hayloft"),
    "garden": Setting(place="the garden", clue_place="the flower bed"),
    "kitchen": Setting(place="the kitchen", clue_place="the pantry"),
    "playroom": Setting(place="the playroom", clue_place="the toy basket"),
}

MYSTERIES = {
    "missing_cookie": Mystery(
        label="the missing cookie",
        missing_item="cookie",
        hidden_by="a bowl",
        solved_with="following the crumbs",
        worry_word="worry",
        clue_word="crumb",
        solve_word="solved",
        reconcile_word="sorry",
    ),
    "lost_key": Mystery(
        label="the lost key",
        missing_item="key",
        hidden_by="a rug",
        solved_with="looking under the rug",
        worry_word="doubt",
        clue_word="scratch",
        solve_word="found",
        reconcile_word="understood",
    ),
    "buried_marble": Mystery(
        label="the buried marble",
        missing_item="marble",
        hidden_by="some dirt",
        solved_with="examining the shiny dirt trail",
        worry_word="nervousness",
        clue_word="shine",
        solve_word="revealed",
        reconcile_word="forgiven",
    ),
}

HELPERS = {
    "friend": "a small friend",
    "mother": "its mother",
    "neighbor": "a kind neighbor",
}

NAMES = ["Pip", "Milo", "Nori", "Tilly", "Poppy", "Bram"]
HELPER_ORDER = ["friend", "mother", "neighbor"]


class State:
    def __init__(self, world: World) -> None:
        self.world = world

    def p(self, eid: str) -> Entity:
        return self.world.get(eid)


def _say(world: World, text: str) -> None:
    world.say(text)


def reasonableness_gate(place: str, mystery: str) -> None:
    if place not in SETTINGS:
        raise StoryError("Unknown setting.")
    if mystery not in MYSTERIES:
        raise StoryError("Unknown mystery.")


def intro(world: World, piglet: Entity, helper: Entity, mystery: Mystery) -> None:
    _say(world, f"{piglet.id} was a little piglet detective who liked quiet clues and neat answers.")
    _say(world, f"One day, {piglet.id} noticed {mystery.label} and tried to keep {mystery.worry_word} out of {piglet.pronoun('possessive')} voice.")


def disturb(world: World, piglet: Entity, mystery: Mystery) -> None:
    piglet.memes["worry"] = piglet.memes.get("worry", 0.0) + 1
    piglet.memes["suppressed"] = piglet.memes.get("suppressed", 0.0) + 1
    _say(world, f"{piglet.id} looked around {world.setting.place} and kept quiet, even though the mystery felt big.")
    _say(world, f"{piglet.pronoun().capitalize()} tried to suppress {mystery.worry_word} and search alone.")


def add_clue(world: World, piglet: Entity, mystery: Mystery) -> None:
    clue = world.add(Entity(id="clue", type="thing", label=mystery.clue_word))
    clue.meters["noticed"] = 1
    piglet.meters["searching"] = piglet.meters.get("searching", 0.0) + 1
    _say(world, f"Near {world.setting.clue_place}, {piglet.id} found a small {mystery.clue_word} and paused.")
    _say(world, f"That clue made the answer feel closer, like a tiny lamp turning on.")


def solve(world: World, piglet: Entity, helper: Entity, mystery: Mystery) -> None:
    piglet.memes["confidence"] = piglet.memes.get("confidence", 0.0) + 1
    piglet.memes["worry"] = max(0.0, piglet.memes.get("worry", 0.0) - 1)
    world.facts["solved"] = True
    _say(world, f"{piglet.id} stopped hiding the {mystery.worry_word} and shared the clue with {helper.id}.")
    _say(world, f"Together they kept {mystery.solve_word} the mystery by {mystery.solved_with}.")


def reconcile(world: World, piglet: Entity, helper: Entity, mystery: Mystery) -> None:
    piglet.memes["relief"] = piglet.memes.get("relief", 0.0) + 1
    piglet.memes["friendship"] = piglet.memes.get("friendship", 0.0) + 1
    helper.memes["warmth"] = helper.memes.get("warmth", 0.0) + 1
    _say(world, f"{piglet.id} said {mystery.reconcile_word} to {helper.id}, and {helper.id} smiled back.")
    _say(world, f"The missing {mystery.missing_item} was there all along, tucked away by {mystery.hidden_by}, and everyone felt better.")


def tell(setting: Setting, mystery: Mystery, name: str, helper_kind: str) -> World:
    world = World(setting)
    piglet = world.add(Entity(id=name, kind="character", type="piglet", label="piglet"))
    helper = world.add(Entity(id="Helper", kind="character", type="adult" if helper_kind == "mother" else "child", label=HELPERS[helper_kind]))

    world.facts.update(piglet=piglet, helper=helper, mystery=mystery, setting=setting, helper_kind=helper_kind)
    intro(world, piglet, helper, mystery)
    world.para()
    disturb(world, piglet, mystery)
    add_clue(world, piglet, mystery)
    world.para()
    solve(world, piglet, helper, mystery)
    reconcile(world, piglet, helper, mystery)
    return world


def asp_facts() -> str:
    import asp
    lines = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for mid, m in MYSTERIES.items():
        lines.append(asp.fact("mystery", mid))
        lines.append(asp.fact("missing_item", mid, m.missing_item))
    for h in HELPER_ORDER:
        lines.append(asp.fact("helper_kind", h))
    return "\n".join(lines)


ASP_RULES = r"""
valid_story(P, M, H) :- setting(P), mystery(M), helper_kind(H).
"""


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_stories() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/3."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    py = {(p, m, h) for p in SETTINGS for m in MYSTERIES for h in HELPER_ORDER}
    asp_set = set(asp_valid_stories())
    if py == asp_set:
        print(f"OK: ASP matches Python ({len(py)} stories).")
        return 0
    print("MISMATCH between ASP and Python:")
    if py - asp_set:
        print("  only in python:", sorted(py - asp_set))
    if asp_set - py:
        print("  only in asp:", sorted(asp_set - py))
    return 1


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    piglet = f["piglet"]
    mystery = f["mystery"]
    helper = f["helper"]
    return [
        f'Write a short detective story for a child about {piglet.id}, a piglet who tries to suppress worry while solving {mystery.label}.',
        f"Tell a gentle mystery where {piglet.id} works through a clue with {helper.id} and ends by making peace.",
        f'Write a story in which a piglet detective notices a clue, solves "{mystery.label}", and learns not to hide feelings.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    piglet: Entity = f["piglet"]  # type: ignore[assignment]
    helper: Entity = f["helper"]  # type: ignore[assignment]
    mystery: Mystery = f["mystery"]  # type: ignore[assignment]
    setting: Setting = f["setting"]  # type: ignore[assignment]
    return [
        QAItem(
            question=f"Who is the detective in the story?",
            answer=f"The detective is {piglet.id}, a little piglet who tried to solve a mystery at {setting.place}.",
        ),
        QAItem(
            question=f"What did {piglet.id} try to do with {mystery.worry_word} at first?",
            answer=f"{piglet.id} tried to suppress {mystery.worry_word} and work alone, even though the mystery still felt important.",
        ),
        QAItem(
            question=f"What clue helped {piglet.id} solve {mystery.label}?",
            answer=f"A small {mystery.clue_word} near {setting.clue_place} helped {piglet.id} understand where to look next.",
        ),
        QAItem(
            question=f"Who helped {piglet.id} in the end?",
            answer=f"{helper.id} helped by listening, sharing the clue, and working together with the piglet detective.",
        ),
        QAItem(
            question=f"How did the story end?",
            answer=f"It ended with the mystery solved, the missing {mystery.missing_item} found, and {piglet.id} and {helper.id} feeling peaceful again.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a clue in a mystery story?",
            answer="A clue is a small piece of information that helps someone figure out what happened or where to look next.",
        ),
        QAItem(
            question="What does it mean to suppress a feeling?",
            answer="To suppress a feeling means to try to hold it back and not show it right away.",
        ),
        QAItem(
            question="What is reconciliation?",
            answer="Reconciliation is when people stop feeling upset and make peace with each other again.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
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


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    return "\n".join(lines)


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Piglet detective mystery storyworld.")
    ap.add_argument("--place", choices=SETTINGS.keys())
    ap.add_argument("--mystery", choices=MYSTERIES.keys())
    ap.add_argument("--name", choices=NAMES)
    ap.add_argument("--helper", choices=HELPER_ORDER)
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
    place = args.place or rng.choice(list(SETTINGS.keys()))
    mystery = args.mystery or rng.choice(list(MYSTERIES.keys()))
    name = args.name or rng.choice(NAMES)
    helper = args.helper or rng.choice(HELPER_ORDER)
    reasonableness_gate(place, mystery)
    return StoryParams(place=place, mystery=mystery, name=name, helper=helper)


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.place], MYSTERIES[params.mystery], params.name, params.helper)
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


CURATED = [
    StoryParams(place="barn", mystery="missing_cookie", name="Pip", helper="mother"),
    StoryParams(place="garden", mystery="buried_marble", name="Milo", helper="friend"),
    StoryParams(place="kitchen", mystery="lost_key", name="Nori", helper="neighbor"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid_story/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        stories = asp_valid_stories()
        print(f"{len(stories)} compatible stories:")
        for row in stories:
            print("  ", row)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        for i in range(max(args.n * 50, 50)):
            if len(samples) >= args.n:
                break
            params = resolve_params(args, random.Random(base_seed + i))
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

    for i, sample in enumerate(samples):
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.name}: {p.mystery} at {p.place}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""
storyworlds/worlds/imprint_surprise_magic_flashback_mystery.py
===============================================================

A small story world in a mystery style: a child notices an imprint, follows a
surprising clue, remembers a flashback, and discovers that a little bit of magic
explains what happened.

Seed tale premise:
- A child loses a treasured thing in a quiet room.
- An odd imprint appears near the missing place.
- A flashback reveals an earlier hint.
- A magical surprise turns the mystery into a gentle ending.

The simulated world tracks:
- physical meters: dust, shine, magic, hidden, noticed, open
- emotional memes: curiosity, worry, surprise, wonder, relief, trust, memory

The story is not a frozen template. The child investigates, notices evidence,
recalls a flashback, and uses that clue to reach the resolution.
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
    holds: list[str] = field(default_factory=list)
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def __post_init__(self) -> None:
        for k in ["dust", "shine", "magic", "hidden", "noticed", "open"]:
            self.meters.setdefault(k, 0.0)
        for k in ["curiosity", "worry", "surprise", "wonder", "relief", "trust", "memory"]:
            self.memes.setdefault(k, 0.0)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "mother", "grandmother", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "grandfather", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str = "the old library"
    quiet: bool = True


@dataclass
class Clue:
    imprint: str
    color: str
    shape: str
    found_near: str


@dataclass
class Relic:
    label: str
    phrase: str
    type: str
    owner: str


@dataclass
class StoryParams:
    setting: str
    clue: str
    relic: str
    name: str
    gender: str
    helper: str
    seed: Optional[int] = None


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.lines: list[list[str]] = [[]]
        self.fired: set[str] = set()
        self.facts: dict = {}
        self.trace: list[str] = []

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str) -> Entity:
        return self.entities[eid]

    def say(self, text: str) -> None:
        if text:
            self.lines[-1].append(text)

    def para(self) -> None:
        if self.lines[-1]:
            self.lines.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.lines if p)

    def copy(self) -> "World":
        import copy as _copy
        c = World(self.setting)
        c.entities = _copy.deepcopy(self.entities)
        c.fired = set(self.fired)
        c.facts = dict(self.facts)
        return c


def _entity_word(ent: Entity) -> str:
    return ent.label or ent.type


def _saw_imprint(world: World, child: Entity, clue: Clue) -> None:
    child.memes["curiosity"] += 1
    child.meters["noticed"] += 1
    world.say(
        f"{child.id} found a strange {clue.color} imprint near the {clue.found_near}. "
        f"It looked too neat to be an accident."
    )


def _flashback(world: World, child: Entity, clue: Clue) -> None:
    if world.facts.get("flashback_done"):
        return
    child.memes["memory"] += 1
    child.memes["surprise"] += 1
    world.facts["flashback_done"] = True
    world.say(
        f"Then {child.id} had a flashback: yesterday, {child.pronoun('possessive')} "
        f"{world.facts['helper'].label} had shown {child.pronoun('object')} a tiny "
        f"stamp that left the very same {clue.imprint}."
    )


def _inspect_magic(world: World, child: Entity, relic: Entity, clue: Clue) -> None:
    child.memes["wonder"] += 1
    relic.meters["hidden"] = 0.0
    relic.meters["open"] = 1.0
    world.say(
        f"{child.id} followed the clue to a narrow drawer. Inside, a little magic glow "
        f"covered {relic.phrase}, and the {clue.imprint} matched the stamp exactly."
    )


def _reveal_surprise(world: World, child: Entity, relic: Entity) -> None:
    child.memes["surprise"] += 1
    child.memes["relief"] += 1
    child.memes["trust"] += 1
    helper = world.facts["helper"]
    world.say(
        f"That was the surprise: {helper.id} had hidden {relic.phrase} there only to "
        f"keep it safe. The magic glow was just a soft charm that could find lost things."
    )
    world.say(
        f"{child.id} smiled, picked up {relic.phrase}, and the room felt calm again."
    )


def tell(setting: Setting, clue: Clue, relic: Relic, child_name: str, child_gender: str, helper_name: str) -> World:
    world = World(setting)
    child = world.add(Entity(id=child_name, kind="character", type=child_gender))
    helper = world.add(Entity(id=helper_name, kind="character", type="adult", label=helper_name))
    lost = world.add(Entity(
        id="relic",
        kind="thing",
        type=relic.type,
        label=relic.label,
        phrase=relic.phrase,
        owner=child.id,
        caretaker=helper.id,
        meters={"dust": 0.0, "shine": 1.0, "magic": 0.0, "hidden": 1.0, "noticed": 0.0, "open": 0.0},
    ))
    world.facts["child"] = child
    world.facts["helper"] = helper
    world.facts["relic"] = lost
    world.facts["clue"] = clue

    world.say(
        f"{child.id} was a small, careful {child_gender} who liked quiet places and little mysteries."
    )
    world.say(
        f"One afternoon, {child.id} noticed that {child.pronoun('possessive')} {relic.label} was missing."
    )
    world.say(
        f"The room was still, except for one curious {clue.color} imprint near the {clue.found_near}."
    )

    world.para()
    _saw_imprint(world, child, clue)
    world.say(
        f"{child.id} did not rush. {child.pronoun().capitalize()} knelt down, studied the shape, and wondered who had left it."
    )
    _flashback(world, child, clue)
    world.say(
        f"That memory made the clue feel less spooky and more useful."
    )

    world.para()
    _inspect_magic(world, child, lost, clue)
    _reveal_surprise(world, child, lost)

    world.facts["resolved"] = True
    return world


SETTINGS = {
    "library": Setting(place="the old library", quiet=True),
    "attic": Setting(place="the dusty attic", quiet=True),
    "workshop": Setting(place="the little workshop", quiet=False),
}

CLUES = {
    "star": Clue(imprint="star-shaped imprint", color="silver", shape="star", found_near="window seat"),
    "moon": Clue(imprint="moon-shaped imprint", color="blue", shape="moon", found_near="wooden desk"),
    "leaf": Clue(imprint="leaf-shaped imprint", color="green", shape="leaf", found_near="lamp stand"),
}

RELICS = {
    "book": Relic(label="storybook", phrase="the missing storybook", type="book", owner="child"),
    "key": Relic(label="little key", phrase="the missing little key", type="key", owner="child"),
    "bell": Relic(label="brass bell", phrase="the missing brass bell", type="bell", owner="child"),
}

NAMES = ["Milo", "Nia", "Pip", "Lena", "Toby", "Sana", "June", "Theo"]
GENDERS = ["girl", "boy"]
HELPERS = ["Aunt Mira", "Grandpa Joel", "Ms. Reed", "Uncle Ben"]


def reasonableness_gate(setting: Setting, clue: Clue, relic: Relic) -> bool:
    if setting.place == "the dusty attic" and relic.type == "book":
        return True
    if setting.place == "the old library" and relic.type in {"book", "key"}:
        return True
    if setting.place == "the little workshop" and relic.type in {"key", "bell"}:
        return True
    return False


def explain_rejection(setting: Setting, clue: Clue, relic: Relic) -> str:
    return (
        f"(No story: the clue and missing object do not fit this room. "
        f"Try a setting where a {relic.label} could plausibly be hidden and leave a {clue.imprint}.)"
    )


def valid_combos() -> list[tuple[str, str, str]]:
    out = []
    for s in SETTINGS:
        for c in CLUES:
            for r in RELICS:
                if reasonableness_gate(SETTINGS[s], CLUES[c], RELICS[r]):
                    out.append((s, c, r))
    return out


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    child = f["child"]
    clue = f["clue"]
    relic = f["relic"]
    return [
        f'Write a gentle mystery story for a small child that includes an {clue.imprint}.',
        f"Tell a story where {child.id} searches for {relic.phrase}, remembers a flashback, "
        f"and discovers a surprise with a little magic.",
        f'Write a child-friendly mystery ending with the word "imprint" and a happy reveal.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child = f["child"]
    helper = f["helper"]
    clue = f["clue"]
    relic = f["relic"]
    return [
        QAItem(
            question=f"What was missing at the start of the story?",
            answer=f"{child.id}'s {relic.phrase} was missing."
        ),
        QAItem(
            question=f"What strange clue did {child.id} notice?",
            answer=f"{child.id} noticed a {clue.imprint} near the {clue.found_near}."
        ),
        QAItem(
            question=f"What did the flashback help {child.id} remember?",
            answer=(
                f"The flashback reminded {child.id} that {helper.id} had shown "
                f"{child.pronoun('object')} the same little stamp yesterday."
            )
        ),
        QAItem(
            question=f"What made the ending a surprise?",
            answer=(
                f"The surprise was that {helper.id} had hidden {relic.phrase} safely "
                f"in the drawer, and the magic glow was only a charm to help find it."
            )
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is an imprint?",
            answer="An imprint is a mark or shape left behind after something presses on a surface."
        ),
        QAItem(
            question="What is a flashback in a story?",
            answer="A flashback is a moment when a story remembers something that happened earlier."
        ),
        QAItem(
            question="What does a mystery ask the reader to do?",
            answer="A mystery asks the reader to look for clues and figure out what happened."
        ),
        QAItem(
            question="Why can magic be helpful in a gentle story?",
            answer="Magic can make the clue feel special and help the character solve the problem in a kind way."
        ),
    ]


def format_qa(sample: StorySample) -> str:
    parts = ["== (1) Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        parts.append(f"{i}. {p}")
    parts.append("")
    parts.append("== (2) Story questions ==")
    for q in sample.story_qa:
        parts.append(f"Q: {q.question}")
        parts.append(f"A: {q.answer}")
    parts.append("")
    parts.append("== (3) World knowledge questions ==")
    for q in sample.world_qa:
        parts.append(f"Q: {q.question}")
        parts.append(f"A: {q.answer}")
    return "\n".join(parts)


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for e in world.entities.values():
        meters = {k: round(v, 2) for k, v in e.meters.items() if v}
        memes = {k: round(v, 2) for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        lines.append(f"  {e.id}: {e.type} {' '.join(bits)}")
    return "\n".join(lines)


@dataclass
class ASPItem:
    setting: str
    clue: str
    relic: str


ASP_RULES = r"""
setting_ok(library,book).
setting_ok(library,key).
setting_ok(attic,book).
setting_ok(workshop,key).
setting_ok(workshop,bell).

valid(S,C,R) :- setting_ok(S,R).
#show valid/3.
"""


def asp_facts() -> str:
    import storyworlds.asp as asp
    lines = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for cid, clue in CLUES.items():
        lines.append(asp.fact("clue", cid))
        lines.append(asp.fact("imprint", cid, clue.imprint))
    for rid, relic in RELICS.items():
        lines.append(asp.fact("relic", rid))
        lines.append(asp.fact("relic_type", rid, relic.type))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple[str, str, str]]:
    import storyworlds.asp as asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    py = set(valid_combos())
    asp_set = set(asp_valid_combos())
    if py == asp_set:
        print(f"OK: ASP matches Python gate ({len(py)} combos).")
        return 0
    print("MISMATCH:")
    if py - asp_set:
        print("  only in python:", sorted(py - asp_set))
    if asp_set - py:
        print("  only in asp:", sorted(asp_set - py))
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A tiny mystery world with imprint, surprise, magic, and flashback.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--clue", choices=CLUES)
    ap.add_argument("--relic", choices=RELICS)
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=GENDERS)
    ap.add_argument("--helper", choices=HELPERS)
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
    combos = valid_combos()
    combos = [
        c for c in combos
        if (args.setting is None or c[0] == args.setting)
        and (args.clue is None or c[1] == args.clue)
        and (args.relic is None or c[2] == args.relic)
    ]
    if not combos:
        raise StoryError("(No valid mystery matches the given options.)")
    setting, clue, relic = rng.choice(sorted(combos))
    name = args.name or rng.choice(NAMES)
    gender = args.gender or rng.choice(GENDERS)
    helper = args.helper or rng.choice(HELPERS)
    if not reasonableness_gate(SETTINGS[setting], CLUES[clue], RELICS[relic]):
        raise StoryError(explain_rejection(SETTINGS[setting], CLUES[clue], RELICS[relic]))
    return StoryParams(setting=setting, clue=clue, relic=relic, name=name, gender=gender, helper=helper)


def generate(params: StoryParams) -> StorySample:
    clue = CLUES[params.clue]
    relic = RELICS[params.relic]
    world = tell(SETTINGS[params.setting], clue, relic, params.name, params.gender, params.helper)
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
    StoryParams(setting="library", clue="star", relic="book", name="Milo", gender="boy", helper="Aunt Mira"),
    StoryParams(setting="attic", clue="moon", relic="book", name="Nia", gender="girl", helper="Grandpa Joel"),
    StoryParams(setting="workshop", clue="leaf", relic="bell", name="Pip", gender="boy", helper="Ms. Reed"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible combos:\n")
        for c in combos:
            print(" ", c)
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
            header = f"### {p.name}: {p.setting} / {p.clue} / {p.relic}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()

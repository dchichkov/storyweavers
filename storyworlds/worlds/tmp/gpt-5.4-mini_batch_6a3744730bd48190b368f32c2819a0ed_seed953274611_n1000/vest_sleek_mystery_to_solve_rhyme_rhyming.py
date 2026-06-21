#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/vest_sleek_mystery_to_solve_rhyme_rhyming.py
=============================================================================

A small story world for a rhyming mystery: a child spots a sleek vest, notices
it is missing something important, follows clues, and solves the puzzle with a
kind helper. The story is built from a simulated world state, not from a frozen
template.

Seed words: vest, sleek
Features: Mystery to Solve, Rhyme
Style: Rhyming Story
"""

from __future__ import annotations

import argparse
import copy
import json
import os
import random
import sys
from dataclasses import dataclass, field
from typing import Callable, Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from results import QAItem, StoryError, StorySample  # noqa: E402

THRESHOLD = 1.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    traits: list[str] = field(default_factory=list)
    role: str = ""
    attrs: dict = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=lambda: {})
    memes: dict[str, float] = field(default_factory=lambda: {})

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman"}
        male = {"boy", "father", "dad", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return self.label or self.type


@dataclass
class Setting:
    id: str
    place: str
    glow: str
    sounds: str
    clues: list[str] = field(default_factory=list)


@dataclass
class Mystery:
    id: str
    missing: str
    found_with: str
    question: str
    clue1: str
    clue2: str
    solved_line: str


@dataclass
class Helper:
    id: str
    type: str
    label: str
    gift: str
    advice: str


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}

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
        c = World(self.setting)
        c.entities = copy.deepcopy(self.entities)
        c.fired = set(self.fired)
        c.paragraphs = [[]]
        c.facts = copy.deepcopy(self.facts)
        return c


@dataclass
class Rule:
    name: str
    apply: Callable[[World], list[str]]


def _r_worry(world: World) -> list[str]:
    out = []
    for ent in world.entities.values():
        if ent.memes.get("worry", 0.0) < THRESHOLD:
            continue
        sig = ("worry", ent.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        ent.memes["search"] = ent.memes.get("search", 0.0) + 1
        out.append("__worry__")
    return out


def _r_notice(world: World) -> list[str]:
    out = []
    child = world.entities.get("child")
    clue = world.entities.get("clue")
    vest = world.entities.get("vest")
    if not child or not clue or not vest:
        return out
    if child.memes.get("search", 0.0) < THRESHOLD:
        return out
    sig = ("notice",)
    if sig in world.fired:
        return out
    if clue.meters.get("seen", 0.0) >= THRESHOLD and vest.meters.get("found", 0.0) < THRESHOLD:
        world.fired.add(sig)
        child.memes["curious"] = child.memes.get("curious", 0.0) + 1
        out.append("__notice__")
    return out


CAUSAL_RULES = [Rule("worry", _r_worry), Rule("notice", _r_notice)]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            bits = rule.apply(world)
            if bits:
                changed = True
                produced.extend(b for b in bits if not b.startswith("__"))
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def rhyme(a: str, b: str) -> str:
    return f"{a}, {b}"


def valid_combos() -> list[tuple[str, str]]:
    return [(s.id, m.id) for s in SETTINGS.values() for m in MYSTERIES.values()]


def explain_rejection() -> str:
    return "(No story: this world needs a mystery with a missing thing and a clue path.)"


def resolve_params(args: argparse.Namespace, rng: random.Random) -> "StoryParams":
    combos = [c for c in valid_combos()
              if (args.setting is None or c[0] == args.setting)
              and (args.mystery is None or c[1] == args.mystery)]
    if not combos:
        raise StoryError(explain_rejection())
    setting_id, mystery_id = rng.choice(sorted(combos))
    child = args.child or rng.choice(BOY_NAMES + GIRL_NAMES)
    helper = args.helper or rng.choice(HELPERS.keys())
    return StoryParams(setting=setting_id, mystery=mystery_id, child=child, helper=helper, seed=None)


@dataclass
class StoryParams:
    setting: str
    mystery: str
    child: str
    helper: str = "cat"
    seed: Optional[int] = None


SETTINGS = {
    "attic": Setting(id="attic", place="the attic", glow="a pale moon glow", sounds="a hush of dust", clues=["beam", "box"]),
    "closet": Setting(id="closet", place="the closet", glow="a tiny lamp glow", sounds="a soft hush", clues=["hook", "shelf"]),
    "hall": Setting(id="hall", place="the hall", glow="a sleek floor shine", sounds="a tap-tap echo", clues=["mat", "frame"]),
}

MYSTERIES = {
    "vest": Mystery(
        id="vest",
        missing="the vest",
        found_with="the cat",
        question="Who took the sleek vest?",
        clue1="A thread of gray fur was on the chair.",
        clue2="A tiny paw print pointed under the bench.",
        solved_line="The sleek vest was tucked by the cat, who had curled up in a neat little nest.",
    ),
    "key": Mystery(
        id="key",
        missing="the key",
        found_with="the mouse",
        question="Where did the small key go?",
        clue1="A crumb trail curved by the wall.",
        clue2="A squeak came from behind the box.",
        solved_line="The little key was near the mouse, under a box, like a shiny prize in a pounce.",
    ),
    "cap": Mystery(
        id="cap",
        missing="the cap",
        found_with="the pup",
        question="Who hid the bright cap?",
        clue1="A wet nose mark glowed on the stair.",
        clue2="A wagging tail tapped the air.",
        solved_line="The bright cap was with the pup, safe in a soft bed of fluff and snout.",
    ),
}

HELPERS = {
    "cat": Helper(id="cat", type="cat", label="cat", gift="purr", advice="follow the fur"),
    "mouse": Helper(id="mouse", type="mouse", label="mouse", gift="tiny squeak", advice="look for crumbs"),
    "pup": Helper(id="pup", type="dog", label="pup", gift="wag", advice="seek the soft spot"),
}

GIRL_NAMES = ["Lily", "Mia", "Nora", "Ava"]
BOY_NAMES = ["Max", "Leo", "Ben", "Theo"]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A rhyming mystery story world.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--mystery", choices=MYSTERIES)
    ap.add_argument("--child")
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


def tell(setting: Setting, mystery: Mystery, child_name: str, helper: Helper) -> World:
    world = World(setting)
    child = world.add(Entity(id=child_name, kind="character", type="girl" if child_name in GIRL_NAMES else "boy", role="sleuth", traits=["curious"]))
    vest = world.add(Entity(id="vest", kind="thing", type="thing", label="sleek vest"))
    clue = world.add(Entity(id="clue", kind="thing", type="thing", label="clue"))
    helper_ent = world.add(Entity(id=helper.id, kind="character", type=helper.type, label=helper.label, role="helper"))
    vest.meters["found"] = 0.0
    clue.meters["seen"] = 0.0
    child.memes["worry"] = 1.0
    world.say(f"In {setting.place}, {child.id} saw a sleek vest and felt a little whirl.")
    world.say(f"{setting.glow} and {setting.sounds} made the room feel like a place for a clue.")
    world.say(f'"{mystery.question}" {child.id} asked, and {helper.label_word} came near to help and to sing a rhyme.')
    world.para()
    world.say(f"{mystery.clue1} {mystery.clue2}")
    clue.meters["seen"] += 1
    propagate(world)
    world.say(f"{child.id} looked low and high, with a careful eye, and asked the {helper.label} to try.")
    helper_ent.memes["help"] = 1.0
    world.para()
    vest.meters["found"] += 1
    world.say(f"{mystery.solved_line}")
    child.memes["worry"] = 0.0
    child.memes["joy"] = 1.0
    world.say(f"{child.id} smiled, quite light, and held the vest snug and bright.")
    world.say(f"The sleet of doubt was gone; the mystery was done.")
    world.facts.update(setting=setting, mystery=mystery, child=child, helper=helper_ent, vest=vest, clue=clue)
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a rhyming mystery story for a young child that includes the words "vest" and "sleek".',
        f"Tell a gentle story where {f['child'].id} finds a sleek vest by solving a small mystery with a helper.",
        f'Write a short rhyme-filled tale with clues, a missing vest, and a happy ending.',
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    child = f["child"]
    mystery = f["mystery"]
    helper = f["helper"]
    return [
        ("What was the mystery?",
         f"The mystery was about the missing sleek vest. {child.id} wondered where it had gone and started looking for clues."),
        ("Who helped solve it?",
         f"The {helper.label} helped solve it. The helper pointed the way, and {child.id} followed the clues until the vest was found."),
        ("How did the story end?",
         f"It ended happily with the vest found again. {child.id} felt proud and calm because the puzzle was solved."),
    ]


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    return [
        ("What is a clue?",
         "A clue is a small piece of information that helps someone solve a mystery."),
        ("What does sleek mean?",
         "Sleek means smooth and shiny, like something that looks neat and slips along easily."),
        ("What is a mystery?",
         "A mystery is a puzzle that needs to be solved by noticing clues and thinking carefully."),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    lines.extend(f"{i+1}. {p}" for i, p in enumerate(sample.prompts))
    lines.append("")
    lines.append("== story QA ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== world QA ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        lines.append(f"  {e.id:8} ({e.type:7}) meters={e.meters} memes={e.memes} role={e.role}")
    lines.append(f"  fired rules: {sorted(n for n, *_ in world.fired)}")
    return "\n".join(lines)


CURATED = [
    StoryParams(setting="attic", mystery="vest", child="Lily", helper="cat"),
    StoryParams(setting="closet", mystery="key", child="Max", helper="mouse"),
    StoryParams(setting="hall", mystery="cap", child="Nora", helper="pup"),
]


def generate(params: StoryParams) -> StorySample:
    if params.setting not in SETTINGS or params.mystery not in MYSTERIES or params.helper not in HELPERS:
        raise StoryError("Invalid story parameters.")
    world = tell(SETTINGS[params.setting], MYSTERIES[params.mystery], params.child, HELPERS[params.helper])
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=[QAItem(question=q, answer=a) for q, a in story_qa(world)],
        world_qa=[QAItem(question=q, answer=a) for q, a in world_knowledge_qa(world)],
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


ASP_RULES = r"""
selected(setting(attic); setting(closet); setting(hall)).
mystery(vest; key; cap).
valid(S,M) :- selected(setting(S)), mystery(M).
#show valid/2.
"""


def asp_facts() -> str:
    import asp
    out = []
    for s in SETTINGS:
        out.append(asp.fact("selected", s))
    for m in MYSTERIES:
        out.append(asp.fact("mystery", m))
    return "\n".join(out)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/2."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    import io
    import contextlib

    ok = True
    if set(asp_valid_combos()) != set(valid_combos()):
        ok = False
        print("MISMATCH: ASP and Python combos differ.")
    try:
        sample = generate(CURATED[0])
        assert sample.story
        with contextlib.redirect_stdout(io.StringIO()):
            emit(sample)
    except Exception as exc:  # noqa: BLE001
        ok = False
        print(f"SMOKE TEST FAILED: {exc}")
    if ok:
        print("OK: ASP parity and story smoke test passed.")
        return 0
    return 1


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    combos = [c for c in valid_combos()
              if (args.setting is None or c[0] == args.setting)
              and (args.mystery is None or c[1] == args.mystery)]
    if not combos:
        raise StoryError(explain_rejection())
    setting, mystery = rng.choice(sorted(combos))
    child = args.child or rng.choice(GIRL_NAMES + BOY_NAMES)
    helper = args.helper or rng.choice(list(HELPERS))
    return StoryParams(setting=setting, mystery=mystery, child=child, helper=helper, seed=None)


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show valid/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        for combo in asp_valid_combos():
            print(combo)
        return
    seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        for i in range(args.n):
            params = resolve_params(args, random.Random(seed + i))
            params.seed = seed + i
            samples.append(generate(params))
    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return
    for i, sample in enumerate(samples):
        emit(sample, trace=args.trace, qa=args.qa, header=(f"### variant {i+1}" if len(samples) > 1 else ""))
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()

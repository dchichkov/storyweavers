#!/usr/bin/env python3
"""
storyworlds/worlds/mid_repetition_reconciliation_mystery.py
===========================================================

A small mystery storyworld about a mid-day mismatch, repeated clues, and a
reconciliation at the end.

Premise:
- A child notices the same strange sign appearing more than once.
- The repeated clue makes the situation feel mysterious instead of random.
- The child and a helper investigate, discover the cause, and reconcile.

The world is intentionally tiny and classical:
- a setting
- a protagonist
- a helper who may be mistaken at first
- a mystery object/action that repeats
- a cause that can be discovered
- a gentle resolution that restores trust

The story engine simulates physical meters and emotional memes.
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
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "mother", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class Setting:
    place: str
    indoor: bool = False
    repeats: set[str] = field(default_factory=set)


@dataclass
class Mystery:
    id: str
    clue: str
    repeat: str
    cause: str
    reveal: str
    tags: set[str] = field(default_factory=set)


@dataclass
class StoryParams:
    place: str
    mystery: str
    name: str
    gender: str
    helper: str
    trait: str
    seed: Optional[int] = None


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.seen_clues: list[str] = []

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


SETTINGS = {
    "school": Setting(place="the school hallway", indoor=True, repeats={"bell", "whisper"}),
    "library": Setting(place="the library", indoor=True, repeats={"tap", "note"}),
    "garden": Setting(place="the garden path", indoor=False, repeats={"rustle", "glint"}),
    "kitchen": Setting(place="the kitchen", indoor=True, repeats={"clink", "crumb"}),
}

MYSTERIES = {
    "bell": Mystery(
        id="bell",
        clue="the bell rang twice",
        repeat="the same bell sounded again",
        cause="the clock was striking the hour",
        reveal="the bell belonged to the clock in the hall",
        tags={"sound", "mid"},
    ),
    "note": Mystery(
        id="note",
        clue="a folded note appeared on the bench",
        repeat="the folded note appeared again",
        cause="the wind had blown it back from the doorway",
        reveal="the note had slipped from the helper's pocket",
        tags={"paper", "mid"},
    ),
    "glint": Mystery(
        id="glint",
        clue="a small glint flashed in the leaves",
        repeat="the glint flashed once more",
        cause="sunlight bounced off a spoon in the grass",
        reveal="the shiny thing was a spoon from lunch",
        tags={"light", "mid"},
    ),
    "crumb": Mystery(
        id="crumb",
        clue="crumbs kept showing up on the table",
        repeat="more crumbs showed up beside the plate",
        cause="a squirrel had nudged the open window and crumbs fell in",
        reveal="the crumbs came from the helper's biscuit",
        tags={"food", "mid"},
    ),
}


GIRL_NAMES = ["Lily", "Mia", "Zoe", "Ava", "Nora", "Ella"]
BOY_NAMES = ["Leo", "Ben", "Max", "Finn", "Theo", "Jack"]
TRAITS = ["curious", "careful", "brave", "patient", "quiet", "bright"]
HELPERS = ["teacher", "mother", "father", "librarian", "neighbor"]


ASP_RULES = r"""
place(S) :- setting(S).
mystery(M) :- clue_of(M,_).
repeats(M) :- repeat_of(M,_).
valid(S,M) :- setting(S), clue_of(M,_), repeat_of(M,_).
"""

def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid, s in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        if s.indoor:
            lines.append(asp.fact("indoor", sid))
        for r in sorted(s.repeats):
            lines.append(asp.fact("repeats_at", sid, r))
    for mid, m in MYSTERIES.items():
        lines.append(asp.fact("clue_of", mid, m.clue))
        lines.append(asp.fact("repeat_of", mid, m.repeat))
        lines.append(asp.fact("cause_of", mid, m.cause))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/2."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    py = {(p, m) for p in SETTINGS for m in MYSTERIES if p in SETTINGS}
    cl = set(asp_valid())
    if cl == py:
        print(f"OK: clingo gate matches python ({len(cl)} combos).")
        return 0
    print("MISMATCH")
    print("only in clingo:", sorted(cl - py))
    print("only in python:", sorted(py - cl))
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A tiny mystery world with repetition and reconciliation.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--mystery", choices=MYSTERIES)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--name")
    ap.add_argument("--helper", choices=HELPERS)
    ap.add_argument("--trait", choices=TRAITS)
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
    place = args.place or rng.choice(list(SETTINGS))
    mystery = args.mystery or rng.choice([m for m in MYSTERIES if place in SETTINGS])
    gender = args.gender or rng.choice(["girl", "boy"])
    if args.name:
        name = args.name
    else:
        name = rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    helper = args.helper or rng.choice(HELPERS)
    trait = args.trait or rng.choice(TRAITS)
    return StoryParams(place=place, mystery=mystery, name=name, gender=gender, helper=helper, trait=trait)


def tell(params: StoryParams) -> World:
    setting = SETTINGS[params.place]
    mystery = MYSTERIES[params.mystery]
    world = World(setting)
    hero = world.add(Entity(id=params.name, kind="character", type=params.gender))
    helper = world.add(Entity(id="helper", kind="character", type=params.helper, label=f"the {params.helper}"))
    clue = world.add(Entity(id="clue", type="thing", label=mystery.id, phrase=mystery.clue))

    hero.memes["curiosity"] = 1
    helper.memes["care"] = 1

    world.say(f"{hero.id} was a {params.trait} {params.gender} who liked quiet places and small puzzles.")
    world.say(f"At {setting.place}, {hero.id} noticed {mystery.clue}.")
    world.say(f"That was strange, because {mystery.repeat}.")

    world.para()
    world.say(f"{hero.id} looked again and again, trying to see if the clue was hiding a trick.")
    world.say(f"{helper.pronoun().capitalize()} came closer and said it was worth checking carefully.")
    if setting.indoor:
        world.say(f"The hall was still and bright, so the repeated sign felt even more mysterious.")

    world.para()
    hero.memes["worry"] = 1
    if params.helper in {"mother", "father", "teacher", "librarian"}:
        helper.memes["reassure"] = 1
    world.say(f"At last, they found the cause: {mystery.cause}.")
    world.say(f"The odd thing was not a warning at all. It was just a clue that kept coming back until they understood it.")

    world.para()
    hero.memes["relief"] = 1
    hero.memes["trust"] = 1
    helper.memes["trust"] = 1
    world.say(f"{hero.id} smiled and stopped worrying. {helper.pronoun().capitalize()} smiled too, because the answer made sense now.")
    world.say(f"In the end, {mystery.reveal}, and {hero.id} and {helper.pronoun('object')} felt better than before.")
    world.facts.update(hero=hero, helper=helper, mystery=mystery, setting=setting)
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    mystery = f["mystery"]
    return [
        f'Write a short mystery story for a young child where a clue repeats in the mid-day light and gets solved.',
        f"Tell a gentle story about {hero.id} noticing {mystery.clue} more than once and learning why it happened.",
        f'Write a child-friendly story that includes repetition, a small mystery, and a happy reconciliation at the end.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    helper = f["helper"]
    mystery = f["mystery"]
    place = f["setting"].place
    return [
        QAItem(
            question=f"What did {hero.id} notice at {place}?",
            answer=f"{hero.id} noticed {mystery.clue} at {place}.",
        ),
        QAItem(
            question=f"What made the clue feel mysterious?",
            answer=f"It felt mysterious because {mystery.repeat} and the same thing seemed to happen again.",
        ),
        QAItem(
            question=f"How did the story end for {hero.id} and {helper.label}?",
            answer=f"They found the cause, understood the clue, and felt calm and happy together at the end.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(question="What is a mystery?", answer="A mystery is something that is not understood at first and needs careful looking to solve."),
        QAItem(question="What is repetition?", answer="Repetition means something happens again, or a sound or sight shows up more than once."),
        QAItem(question="What does reconciliation mean?", answer="Reconciliation means people make peace again after worry or confusion and feel okay with each other."),
    ]


def format_qa(sample: StorySample) -> str:
    out = ["== prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        out.append(f"{i}. {p}")
    out.append("")
    out.append("== story qa ==")
    for item in sample.story_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    out.append("")
    out.append("== world qa ==")
    for item in sample.world_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    return "\n".join(out)


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for e in world.entities.values():
        bits = []
        if e.memes:
            bits.append(f"memes={e.memes}")
        if e.meters:
            bits.append(f"meters={e.meters}")
        lines.append(f"{e.id}: {e.type} {' '.join(bits)}")
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


CURATED = [
    StoryParams(place="school", mystery="bell", name="Mia", gender="girl", helper="teacher", trait="curious"),
    StoryParams(place="library", mystery="note", name="Leo", gender="boy", helper="librarian", trait="careful"),
    StoryParams(place="garden", mystery="glint", name="Nora", gender="girl", helper="neighbor", trait="bright"),
    StoryParams(place="kitchen", mystery="crumb", name="Ben", gender="boy", helper="mother", trait="patient"),
]


def valid_combos() -> list[tuple[str, str]]:
    return [(p, m) for p in SETTINGS for m in MYSTERIES if p in SETTINGS]


def explain_invalid() -> str:
    return "(No story: the requested choices do not form a reasonable mystery.)"


def resolve_all(args: argparse.Namespace) -> list[StoryParams]:
    return CURATED


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid()
        print(f"{len(combos)} compatible combos:")
        for place, mystery in combos:
            print(f"  {place:10} {mystery}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        params_list = resolve_all(args)
        samples = [generate(p) for p in params_list]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
            seed = base_seed + i
            i += 1
            params = resolve_params(args, random.Random(seed))
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

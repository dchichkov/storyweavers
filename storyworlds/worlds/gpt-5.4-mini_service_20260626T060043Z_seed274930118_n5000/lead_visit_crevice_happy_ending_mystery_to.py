#!/usr/bin/env python3
"""
storyworlds/worlds/lead_visit_crevice_happy_ending_mystery_to.py
=================================================================

A standalone story world for a tiny detective tale with:
- a lead investigator
- a visit to a crevice
- foreshadowing
- a mystery to solve
- a happy ending

The domain is intentionally small and constraint-checked. The core tension
comes from a clue that points toward a narrow crevice, and the resolution
comes from careful searching rather than danger or surprise violence.
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
    location: str = ""
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "woman", "mother"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man", "father"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str
    afford: set[str] = field(default_factory=set)


@dataclass
class Mystery:
    id: str
    clue: str
    hidden_place: str
    reveal_phrase: str
    solution_phrase: str
    foreshadow: str


@dataclass
class StoryParams:
    place: str
    mystery: str
    detective_name: str
    detective_type: str
    helper_name: str
    helper_type: str
    seed: Optional[int] = None


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
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


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------

SETTINGS = {
    "lantern_lane": Setting(place="Lantern Lane", afford={"visit", "search"}),
    "harbor_path": Setting(place="Harbor Path", afford={"visit", "search"}),
    "old_quarry": Setting(place="the old quarry", afford={"visit", "search"}),
}

MYSTERIES = {
    "missing_key": Mystery(
        id="missing_key",
        clue="a little brass key",
        hidden_place="crevice",
        reveal_phrase="a tiny shine from between two stones",
        solution_phrase="the key was tucked safely in the crevice",
        foreshadow="a thin line of light slipped from the rocks",
    ),
    "lost_note": Mystery(
        id="lost_note",
        clue="a folded note",
        hidden_place="crevice",
        reveal_phrase="paper edges peeking from a split in the stone",
        solution_phrase="the note was pressed into the crevice",
        foreshadow="a scrap of paper fluttered where the wall bent in",
    ),
    "spotted_marble": Mystery(
        id="spotted_marble",
        clue="a spotted marble",
        hidden_place="crevice",
        reveal_phrase="a round glint near the crack",
        solution_phrase="the marble was resting in the crevice",
        foreshadow="a bright dot flashed low by the rocks",
    ),
}

NAMES = ["Mina", "Jules", "Toby", "Nora", "Iris", "Owen", "Piper", "Theo"]
HELPERS = ["small friend", "cousin", "neighbor", "assistant"]
TRAITS = ["careful", "curious", "steady", "bright", "quiet"]


# ---------------------------------------------------------------------------
# Narrative helpers
# ---------------------------------------------------------------------------

def introduce(world: World, detective: Entity, helper: Entity, mystery: Mystery) -> None:
    world.say(
        f"{detective.id} was a {detective.memes['trait']} little detective who liked to notice what other people missed."
    )
    world.say(
        f"One day, {detective.id} learned that {mystery.clue} had gone missing, and {helper.id} stayed close with a small notebook."
    )


def foreshadow(world: World, mystery: Mystery) -> None:
    world.say(
        f"Before long, {mystery.foreshadow} near the wall, and that made {mystery.hidden_place} feel important."
    )


def visit(world: World, detective: Entity, helper: Entity, mystery: Mystery) -> None:
    world.say(
        f"{detective.id} and {helper.id} went to visit {world.setting.place}, where the stone wall had a narrow crevice."
    )
    world.say(
        f"{detective.id} said the mystery would probably be solved by looking where the clue seemed too small to matter."
    )


def search_crevice(world: World, detective: Entity, helper: Entity, mystery: Mystery) -> None:
    detective.memes["focus"] = detective.memes.get("focus", 0) + 1
    helper.memes["helpfulness"] = helper.memes.get("helpfulness", 0) + 1
    world.say(
        f"{helper.id} held the lantern while {detective.id} crouched and peered into the crevice."
    )
    world.say(
        f"There was {mystery.reveal_phrase}, and that was the clue they needed."
    )
    world.say(
        f"{detective.id} reached gently inside and found that {mystery.solution_phrase}."
    )


def resolve(world: World, detective: Entity, helper: Entity, mystery: Mystery) -> None:
    detective.memes["joy"] = detective.memes.get("joy", 0) + 1
    helper.memes["joy"] = helper.memes.get("joy", 0) + 1
    world.say(
        f"{detective.id} smiled, because the missing thing was not lost forever at all."
    )
    world.say(
        f"They carried it back together, and the whole little day ended with {helper.id} grinning beside the solved mystery."
    )


def tell(place: str, mystery_id: str, detective_name: str, detective_type: str,
         helper_name: str, helper_type: str) -> World:
    setting = SETTINGS[place]
    mystery = MYSTERIES[mystery_id]
    world = World(setting)

    detective = world.add(Entity(
        id=detective_name,
        kind="character",
        type=detective_type,
        memes={"trait": random.choice(TRAITS)},
    ))
    helper = world.add(Entity(
        id=helper_name,
        kind="character",
        type=helper_type,
        memes={"helpfulness": 0, "joy": 0},
    ))
    clue = world.add(Entity(
        id="clue",
        type="thing",
        label=mystery.clue,
        location="missing",
    ))
    world.facts.update(
        detective=detective,
        helper=helper,
        clue=clue,
        mystery=mystery,
        setting=setting,
    )

    introduce(world, detective, helper, mystery)
    world.para()
    foreshadow(world, mystery)
    visit(world, detective, helper, mystery)
    search_crevice(world, detective, helper, mystery)
    resolve(world, detective, helper, mystery)
    return world


# ---------------------------------------------------------------------------
# Q&A
# ---------------------------------------------------------------------------

def generation_prompts(world: World) -> list[str]:
    f = world.facts
    mystery: Mystery = f["mystery"]
    detective: Entity = f["detective"]
    helper: Entity = f["helper"]
    return [
        f'Write a short detective story for a young child about a missing {mystery.clue} and a crevice clue.',
        f"Tell a gentle mystery where {detective.id} and {helper.id} visit {world.setting.place} and solve the puzzle together.",
        f'Write a story with foreshadowing, a visit, and a happy ending that includes the word "crevice".',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    detective: Entity = f["detective"]
    helper: Entity = f["helper"]
    mystery: Mystery = f["mystery"]
    place = world.setting.place
    return [
        QAItem(
            question=f"Who was the lead detective in the story?",
            answer=f"{detective.id} was the lead detective, and {helper.id} helped by staying close and carrying the lantern.",
        ),
        QAItem(
            question=f"Where did they visit to look for the missing {mystery.clue}?",
            answer=f"They visited {place}, where the stone wall had a narrow crevice.",
        ),
        QAItem(
            question=f"What clue helped solve the mystery?",
            answer=f"They noticed {mystery.reveal_phrase}, which led them to the crevice and solved the mystery.",
        ),
        QAItem(
            question=f"How did the story end?",
            answer=f"It ended happily, because {mystery.solution_phrase} and they carried it back together.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a crevice?",
            answer="A crevice is a narrow crack or gap in a rock or wall where a small thing can hide.",
        ),
        QAItem(
            question="What does a detective do?",
            answer="A detective looks for clues and uses careful thinking to solve a mystery.",
        ),
        QAItem(
            question="What is foreshadowing in a story?",
            answer="Foreshadowing is when a story gives a small clue early that hints at something important later.",
        ),
    ]


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------

ASP_RULES = r"""
place(P) :- setting(P).
mystery(M) :- clue(M,_).
visit_ok(P,M) :- place(P), mystery(M), afford(P,visit).
has_crevice_clue(M) :- clue(M,_), hidden_place(M,crevice).
foreshadowed(M) :- foreshadow(M,_).
solvable(P,M) :- visit_ok(P,M), has_crevice_clue(M), foreshadowed(M).
happy_ending(M) :- solvable(P,M), place(P).
"""


def asp_facts() -> str:
    import storyworlds.asp as asp
    lines: list[str] = []
    for sid, setting in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        for a in sorted(setting.afford):
            lines.append(asp.fact("afford", sid, a))
    for mid, m in MYSTERIES.items():
        lines.append(asp.fact("clue", mid, m.clue))
        lines.append(asp.fact("hidden_place", mid, m.hidden_place))
        lines.append(asp.fact("foreshadow", mid, m.foreshadow))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import storyworlds.asp as asp
    program = asp_program("#show solvable/2. #show happy_ending/1.")
    model = asp.one_model(program)
    atoms = set((sym.name, tuple(a.string if a.type == a.type.String else a.number if a.type == a.type.Number else a.name for a in sym.arguments)) for sym in model)
    expected = set()
    for p in SETTINGS:
        for m in MYSTERIES:
            if "visit" in SETTINGS[p].afford and MYSTERIES[m].hidden_place == "crevice":
                expected.add(("solvable", (p, m)))
                expected.add(("happy_ending", (m,)))
    got = set()
    for sym in model:
        if sym.name in {"solvable", "happy_ending"}:
            args = []
            for a in sym.arguments:
                if a.type.name == "String":
                    args.append(a.string)
                elif a.type.name == "Number":
                    args.append(a.number)
                else:
                    args.append(a.name)
            got.add((sym.name, tuple(args)))
    if got != expected:
        print("MISMATCH between ASP and Python reasonableness gate.")
        print("expected:", sorted(expected))
        print("got:", sorted(got))
        return 1
    print(f"OK: ASP parity verified for {len(expected)} derived facts.")
    return 0


# ---------------------------------------------------------------------------
# Sample generation
# ---------------------------------------------------------------------------

def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    place = args.place or rng.choice(sorted(SETTINGS))
    mystery = args.mystery or rng.choice(sorted(MYSTERIES))
    detective_type = "girl" if (args.detective_type or rng.choice(["girl", "boy"])) == "girl" else "boy"
    helper_type = "girl" if rng.random() < 0.5 else "boy"

    if place not in SETTINGS:
        raise StoryError("Unknown place.")
    if mystery not in MYSTERIES:
        raise StoryError("Unknown mystery.")

    detective_name = args.detective_name or rng.choice(NAMES)
    helper_name = args.helper_name or rng.choice([n for n in NAMES if n != detective_name])

    return StoryParams(
        place=place,
        mystery=mystery,
        detective_name=detective_name,
        detective_type=detective_type,
        helper_name=helper_name,
        helper_type=helper_type,
    )


def generate(params: StoryParams) -> StorySample:
    world = tell(
        params.place,
        params.mystery,
        params.detective_name,
        params.detective_type,
        params.helper_name,
        params.helper_type,
    )
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        bits = []
        if e.location:
            bits.append(f"location={e.location}")
        if e.memes:
            bits.append(f"memes={dict(e.memes)}")
        lines.append(f"  {e.id:10} ({e.type:8}) {' '.join(bits)}")
    return "\n".join(lines)


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
    lines.append("== (3) World-knowledge questions ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
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
    ap = argparse.ArgumentParser(description="A tiny detective storyworld about a visit to a crevice.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--mystery", choices=MYSTERIES)
    ap.add_argument("--detective-name")
    ap.add_argument("--detective-type", choices=["girl", "boy"])
    ap.add_argument("--helper-name")
    ap.add_argument("--helper-type", choices=["girl", "boy"])
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


CURATED = [
    StoryParams("lantern_lane", "missing_key", "Mina", "girl", "Jules", "boy"),
    StoryParams("harbor_path", "lost_note", "Toby", "boy", "Nora", "girl"),
    StoryParams("old_quarry", "spotted_marble", "Iris", "girl", "Owen", "boy"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show solvable/2. #show happy_ending/1."))
        return
    if args.verify:
        sys.exit(asp_verify())

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        samples: list[StorySample] = []
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            sample = generate(params)
            i += 1
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
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.detective_name}: {p.mystery} at {p.place}"
        elif len(samples) > 1:
            header = f"### variant {idx + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if idx < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""
A small detective-story world about a munchkin, a pita, and a plus-shaped clue,
with kindness and dialogue driving the turn and resolution.

The premise:
- A little munchkin wants to solve a mystery.
- A pita sandwich vanishes from the lunch table.
- A plus sign shows up as a clue, but it is not the culprit.
- The solution comes through careful noticing, gentle questioning, and kindness.

This world is intentionally tiny and classical: one location, one case, one
suspect trail, and one satisfying reveal.
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
    kind: str = "thing"  # character | thing
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "mother", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def noun(self) -> str:
        return self.label or self.type


@dataclass
class Setting:
    place: str = "the kitchen"
    afford: set[str] = field(default_factory=lambda: {"case", "dialogue"})


@dataclass
class StoryParams:
    place: str = "kitchen"
    hero_name: str = "Milo"
    hero_type: str = "boy"
    helper_name: str = "Nia"
    helper_type: str = "girl"
    seed: Optional[int] = None


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict[str, object] = {}

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
    "kitchen": Setting(place="the kitchen", afford={"case", "dialogue"}),
    "hall": Setting(place="the hallway", afford={"case", "dialogue"}),
    "cafe": Setting(place="the little cafe", afford={"case", "dialogue"}),
}

# Seed words requested by the prompt.
SEED_WORDS = {"munchkin", "pita", "plus"}

# Clues and suspects in this tiny mystery.
CLUES = {
    "plus": {
        "label": "plus sign",
        "phrase": "a tiny plus-shaped note",
        "kindness_hint": "Someone had left the note as a helpful sign.",
    },
}

ITEMS = {
    "pita": {
        "label": "pita",
        "phrase": "a warm pita pocket with cheese",
    }
}

SUSPECTS = [
    "the cat",
    "the windy open window",
    "the crumbly napkin",
]


# ---------------------------------------------------------------------------
# Reasonableness gates
# ---------------------------------------------------------------------------
def reasonableness_ok(params: StoryParams) -> bool:
    return params.place in SETTINGS


def explain_rejection(params: StoryParams) -> str:
    return f"(No story: '{params.place}' is not a valid detective setting for this world.)"


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
% A story is valid when the place is known and the case includes the clue and the snack.
valid_place(P) :- setting(P).
valid_story(P) :- valid_place(P), clue(plus), item(pita).
"""


def asp_facts() -> str:
    import storyworlds.asp as asp
    lines: list[str] = []
    for place in SETTINGS:
        lines.append(asp.fact("setting", place))
    lines.append(asp.fact("clue", "plus"))
    lines.append(asp.fact("item", "pita"))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    try:
        import storyworlds.asp as asp
    except Exception as e:  # pragma: no cover
        print(f"ASP unavailable: {e}")
        return 1
    model = asp.one_model(asp_program("#show valid_story/1."))
    atoms = set(asp.atoms(model, "valid_story"))
    py = {("kitchen",), ("hall",), ("cafe",)}
    if atoms == py:
        print(f"OK: clingo gate matches Python gate ({len(py)} places).")
        return 0
    print("MISMATCH between clingo and Python gate.")
    print("clingo:", sorted(atoms))
    print("python:", sorted(py))
    return 1


# ---------------------------------------------------------------------------
# Story engine
# ---------------------------------------------------------------------------
def build_world(params: StoryParams) -> World:
    world = World(SETTINGS[params.place])

    hero = world.add(Entity(id=params.hero_name, kind="character", type=params.hero_type, label="the munchkin"))
    helper = world.add(Entity(id=params.helper_name, kind="character", type=params.helper_type, label="the helper"))
    pita = world.add(Entity(
        id="pita",
        kind="thing",
        type="food",
        label="pita",
        phrase=ITEMS["pita"]["phrase"],
        owner=hero.id,
        meters={"missing": 0.0},
        memes={"value": 1.0},
    ))
    clue = world.add(Entity(
        id="plus",
        kind="thing",
        type="clue",
        label="plus sign",
        phrase=CLUES["plus"]["phrase"],
        meters={"seen": 0.0},
        memes={"meaning": 0.0},
    ))

    # Beginning: a detective mood and the missing pita.
    world.say(f"{hero.id} was a little munchkin who liked solving tiny mysteries.")
    world.say(f"One afternoon, in {world.setting.place}, {hero.id} found that {pita.label} was gone from the table.")
    world.say(f"Near the napkins, {hero.id} noticed {clue.phrase}.")

    # Middle: curiosity, dialogue, and a false lead.
    world.para()
    hero.memes["curiosity"] = 1.0
    world.say(f'"Hmm," {hero.id} said, "who took the {pita.label}?"')
    world.say(f"{helper.id} looked around kindly and said, \"Let's ask gentle questions and follow the clues.\"")
    world.say(f"{hero.id} asked the cat, the window, and the napkin, but the answer did not fit.")
    world.say(f"{clue.label} did not mean a thief at all; it marked the spot where the pita had slid under the tray.")
    world.say(f"{hero.id} knelt down and found crumbs and a torn corner of paper beside it.")

    # Turn: kindness changes the case.
    world.para()
    helper.memes["kindness"] = 1.0
    hero.memes["understanding"] = 1.0
    pita.meters["missing"] = 1.0
    clue.meters["seen"] = 1.0
    clue.memes["meaning"] = 1.0
    world.say(f"{helper.id} smiled and helped lift the tray without laughing at the mistake.")
    world.say(f"That kind help made the mystery easier to solve.")
    world.say(f"{hero.id} saw that the pita had only fallen, not vanished.")

    # Ending: the snack returns, the clue makes sense, and the detective feels proud.
    pita.meters["missing"] = 0.0
    world.say(f"{hero.id} picked up the pita and set it back on the plate.")
    world.say(f'"I found it," {hero.id} said. "The plus sign was a clue, not a problem."')
    world.say(f"{helper.id} nodded. \"And you solved it kindly,\" {helper.id} said.")
    world.say(f"In the end, {hero.id} had a full pita, a clear clue, and a happy little detective smile.")

    world.facts.update(
        hero=hero,
        helper=helper,
        pita=pita,
        clue=clue,
        place=params.place,
        suspects=SUSPECTS,
    )
    return world


# ---------------------------------------------------------------------------
# QA
# ---------------------------------------------------------------------------
def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    return [
        f"Write a short detective story for a child where {hero.id} the munchkin looks for a missing pita and finds a plus-shaped clue.",
        "Tell a gentle mystery that uses kindness and dialogue to solve a small problem in a kitchen.",
        "Write a TinyStories-style detective tale about a munchkin, a pita, and a plus sign that turns out to be a clue.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    helper = f["helper"]
    return [
        QAItem(
            question=f"What kind of story was this about {hero.id}?",
            answer=f"It was a tiny detective story about {hero.id}, a little munchkin who solved a missing-pita mystery.",
        ),
        QAItem(
            question="What food was missing from the table?",
            answer="A pita was missing from the table, and that became the mystery to solve.",
        ),
        QAItem(
            question="What did the plus sign mean in the story?",
            answer="The plus sign was a clue that showed where the pita had slid under the tray.",
        ),
        QAItem(
            question=f"How did {helper.id} help?",
            answer=f"{helper.id} helped kindly by talking with {hero.id}, asking gentle questions, and lifting the tray without making fun of the mistake.",
        ),
        QAItem(
            question="How did the story end?",
            answer="The munchkin found the pita, understood the clue, and ended the case with a happy detective smile.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a detective?",
            answer="A detective is someone who looks carefully for clues to solve a mystery.",
        ),
        QAItem(
            question="What is a pita?",
            answer="A pita is a soft flat bread that can be used like a pocket for food.",
        ),
        QAItem(
            question="What does kindness mean?",
            answer="Kindness means being gentle, helpful, and caring to others.",
        ),
        QAItem(
            question="What is dialogue in a story?",
            answer="Dialogue is when characters speak to each other using words in quotation marks.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts -- asks that would produce this story =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== (2) Story questions -- answerable from the story text ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== (3) World-knowledge questions -- child level, no story needed ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Public interface
# ---------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Detective story world with a munchkin, a pita, a plus clue, kindness, and dialogue.")
    ap.add_argument("--place", choices=sorted(SETTINGS))
    ap.add_argument("--name")
    ap.add_argument("--helper")
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
    place = args.place or rng.choice(sorted(SETTINGS))
    params = StoryParams(
        place=place,
        hero_name=args.name or rng.choice(["Milo", "Nia", "Ari", "Toby", "Luna", "Pip"]),
        helper_name=args.helper or rng.choice(["Nia", "Ivy", "Rae", "June", "Oli", "Mina"]),
        hero_type="boy" if (args.name or "").lower() not in {"nia", "ivy", "rae", "june", "mina", "luna"} else "girl",
        helper_type="girl",
    )
    if not reasonableness_ok(params):
        raise StoryError(explain_rejection(params))
    return params


def generate(params: StoryParams) -> StorySample:
    if not reasonableness_ok(params):
        raise StoryError(explain_rejection(params))
    world = build_world(params)
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
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        lines.append(f"  {e.id:8} ({e.kind:8}) {' '.join(bits)}")
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
        print(asp_program("#show valid_story/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import storyworlds.asp as asp
        model = asp.one_model(asp_program("#show valid_story/1."))
        atoms = sorted(set(asp.atoms(model, "valid_story")))
        print(f"{len(atoms)} valid story setting(s):")
        for a in atoms:
            print(" ", a[0])
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)

    samples: list[StorySample] = []
    if args.all:
        for place in sorted(SETTINGS):
            p = StoryParams(place=place, seed=base_seed)
            samples.append(generate(p))
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 20, 20):
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
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""
storyworlds/worlds/characteristic_fever_cautionary_curiosity_suspense_mystery.py
=================================================================================

A small storyworld about a child with a fever, a curious mystery, and a cautious
turn toward care.

Seed-tale premise:
---
A child wakes up warm and weak with a fever, but something in the house keeps
making a tiny humming sound. The child wants to follow the sound and find out
what it is. A parent worries and asks the child to rest first. The mystery turns
out to be harmless, but only after the child listens, slows down, and lets the
grown-up handle the problem safely.

World model:
---
- physical meters: warm, tired, thirsty, noisy, solved
- emotional memes: curiosity, caution, worry, relief, patience
- state changes are driven by the child's fever, the hush of the house, and the
  discovery of a harmless cause

Story shape:
---
1) Setup: the child feels the fever and notices the strange clue.
2) Tension: curiosity pulls the child toward the sound, while cautionary care
   blocks the risky search.
3) Turn: the parent investigates, and the child learns the mystery is simple.
4) Ending image: the child rests, the house is quiet, and the fear lifts.

This file follows the Storyweavers storyworld contract and includes an inline
ASP twin for the reasonableness gate.
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
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    place: str = ""
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman"}
        male = {"boy", "father", "dad", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"

    @property
    def label_word(self) -> str:
        return {"mother": "mom", "father": "dad"}.get(self.type, self.type)


@dataclass
class Setting:
    place: str
    afford: set[str] = field(default_factory=set)


@dataclass
class Clue:
    id: str
    label: str
    source: str
    revealed_by: str
    harmless_reason: str
    detail: str


@dataclass
class StoryParams:
    setting: str
    clue: str
    name: str
    gender: str
    parent: str
    trait: str
    seed: Optional[int] = None


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[str] = set()
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


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------
SETTINGS = {
    "bedroom": Setting(place="the bedroom", afford={"rest", "listen"}),
    "hallway": Setting(place="the hallway", afford={"listen", "search"}),
    "kitchen": Setting(place="the kitchen", afford={"listen", "search"}),
    "living_room": Setting(place="the living room", afford={"listen", "search"}),
}

CLUES = {
    "hum": Clue(
        id="hum",
        label="tiny hum",
        source="the refrigerator",
        revealed_by="listening near the kitchen",
        harmless_reason="the refrigerator was running normally",
        detail="a soft humming came from the fridge door",
    ),
    "tick": Clue(
        id="tick",
        label="little ticking sound",
        source="the wall clock",
        revealed_by="looking up at the shelf",
        harmless_reason="the wall clock was just keeping time",
        detail="a neat ticking came from the old clock on the wall",
    ),
    "tap": Clue(
        id="tap",
        label="tap-tap sound",
        source="the rain on the window",
        revealed_by="standing by the window",
        harmless_reason="raindrops were tapping the glass",
        detail="something softly tapped the window again and again",
    ),
    "buzz": Clue(
        id="buzz",
        label="buzzing sound",
        source="a toy left on a charger",
        revealed_by="checking the toy basket",
        harmless_reason="a toy battery was charging and buzzing quietly",
        detail="a small buzzing came from a toy tucked beside a charger",
    ),
}

TRAITS = ["curious", "careful", "brave", "gentle", "quiet", "thoughtful"]
GIRL_NAMES = ["Mia", "Lily", "Nora", "Ava", "Zoe", "Ivy", "Ella", "Maya"]
BOY_NAMES = ["Ben", "Theo", "Noah", "Leo", "Finn", "Max", "Eli", "Sam"]


# ---------------------------------------------------------------------------
# Reasonableness gate
# ---------------------------------------------------------------------------
def valid_combos() -> list[tuple[str, str]]:
    combos = []
    for sname, setting in SETTINGS.items():
        for cid, clue in CLUES.items():
            if sname == "bedroom" and cid in {"hum", "tick"}:
                combos.append((sname, cid))
            elif sname != "bedroom" and "search" in setting.afford:
                combos.append((sname, cid))
    return combos


def explain_rejection(setting: str, clue: str) -> str:
    return (
        f"(No story: the clue {clue!r} does not fit a cautious mystery in {setting!r}.)"
    )


# ---------------------------------------------------------------------------
# Story simulation
# ---------------------------------------------------------------------------
def _touch_fever(world: World, child: Entity) -> None:
    child.meters["warm"] += 1
    child.meters["tired"] += 1
    child.memes["worry"] += 1
    world.say(
        f"{child.id} woke up warm and slow, with a fever that made the room feel too bright."
    )


def _notice_clue(world: World, child: Entity, clue: Clue) -> None:
    child.meters["noisy"] += 1
    child.memes["curiosity"] += 1
    world.say(
        f"Then {child.id} noticed {clue.detail}, and that tiny clue made {child.pronoun('object')} wonder what was hiding nearby."
    )


def _warn_rest(world: World, parent: Entity, child: Entity) -> None:
    parent.memes["caution"] += 1
    world.say(
        f'"You have a fever," {parent.label_word} said softly. "First we rest, drink water, and keep your strength."'
    )


def _search_risk(world: World, child: Entity) -> None:
    child.memes["restlessness"] = child.memes.get("restlessness", 0) + 1
    world.say(
        f"{child.id} wanted to sneak out and follow the sound, but the fever made even standing up feel wobbly."
    )


def _resolve(world: World, parent: Entity, child: Entity, clue: Clue) -> None:
    child.meters["solved"] += 1
    child.memes["relief"] += 1
    child.memes["curiosity"] += 1
    world.say(
        f"{parent.label_word} followed the clue instead and found that {clue.harmless_reason}."
    )
    world.say(
        f'{parent.label_word} came back smiling. "It was only {clue.source}," {parent.label_word} said. "Nothing scary at all."'
    )
    world.say(
        f"{child.id} sighed with relief, sipped cool water, and curled under the blanket while the mystery became simple and safe."
    )


def tell(setting: Setting, clue: Clue, hero_name: str, hero_type: str, parent_type: str, trait: str) -> World:
    world = World(setting)
    child = world.add(Entity(
        id=hero_name,
        kind="character",
        type=hero_type,
        meters={"warm": 0.0, "tired": 0.0, "noisy": 0.0, "solved": 0.0},
        memes={"curiosity": 0.0, "worry": 0.0, "relief": 0.0},
    ))
    parent = world.add(Entity(
        id="Parent",
        kind="character",
        type=parent_type,
        label="the parent",
        memes={"caution": 0.0},
    ))
    world.add(Entity(id=clue.id, type="thing", label=clue.label, place=clue.source))

    world.say(
        f"{child.id} was a {trait} {hero_type} who noticed every little sound in {setting.place}."
    )
    world.say(
        f"{child.id} thought {setting.place} felt strange that morning, because a faint sound kept coming and going."
    )
    world.para()

    _touch_fever(world, child)
    _notice_clue(world, child, clue)
    _warn_rest(world, parent, child)
    _search_risk(world, child)

    world.para()

    world.say(
        f"{child.id} tried to listen harder, but the fever blurred the edges of the room."
    )
    world.say(
        f"{parent.label_word} smiled kindly and looked for the sound in a careful way."
    )
    _resolve(world, parent, child, clue)

    world.facts.update(
        child=child,
        parent=parent,
        clue=clue,
        setting=setting,
        resolved=True,
    )
    return world


# ---------------------------------------------------------------------------
# Q&A
# ---------------------------------------------------------------------------
def generation_prompts(world: World) -> list[str]:
    f = world.facts
    child, parent, clue, setting = f["child"], f["parent"], f["clue"], f["setting"]
    return [
        f'Write a short mystery for a young child about {child.id}, a fever, and a small clue in {setting.place}.',
        f"Tell a cautionary story where {child.id} wants to follow a sound, but {parent.label_word} says to rest first.",
        f'Write a gentle suspense story that includes the word "{clue.label}" and ends with the mystery being harmless.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child, parent, clue, setting = f["child"], f["parent"], f["clue"], f["setting"]
    trait = next((t for t in child.memes.keys() if t == "curiosity"), "curious")
    return [
        QAItem(
            question=f"Why did {child.id} feel uneasy in {setting.place}?",
            answer=f"{child.id} felt warm and tired because a fever made the morning feel wrong.",
        ),
        QAItem(
            question=f"What made {child.id} want to look around the house?",
            answer=f"A tiny mystery sound kept returning, and {child.id}'s curiosity grew stronger when the clue appeared.",
        ),
        QAItem(
            question=f"What did {parent.label_word} want {child.id} to do first?",
            answer=f"{parent.label_word.capitalize()} wanted {child.id} to rest, drink water, and stay safe before searching.",
        ),
        QAItem(
            question=f"What was the mystery sound really from?",
            answer=f"It turned out to be {clue.source}, and it was harmless.",
        ),
        QAItem(
            question=f"How did the story end for {child.id}?",
            answer=f"{child.id} felt relieved, stayed under the blanket, and let the grown-up handle the mystery safely.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a fever?",
            answer="A fever is when your body feels hotter than usual because it is fighting sickness.",
        ),
        QAItem(
            question="Why should a child with a fever rest?",
            answer="Rest helps the body save energy so it can get better more comfortably.",
        ),
        QAItem(
            question="What does curiosity mean?",
            answer="Curiosity is the feeling that makes you want to know more about something new or strange.",
        ),
        QAItem(
            question="What is suspense in a story?",
            answer="Suspense is the feeling that something important or mysterious is about to be explained.",
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
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
valid_story(S, C) :- setting(S), clue(C), compatible(S, C).
compatible(bedroom, hum).
compatible(bedroom, tick).
compatible(hallway, hum).
compatible(hallway, tick).
compatible(hallway, tap).
compatible(hallway, buzz).
compatible(kitchen, hum).
compatible(kitchen, tap).
compatible(kitchen, buzz).
compatible(living_room, tick).
compatible(living_room, tap).
compatible(living_room, buzz).
"""


def asp_facts() -> str:
    import storyworlds.asp as asp
    lines: list[str] = []
    for s in SETTINGS:
        lines.append(asp.fact("setting", s))
    for c in CLUES:
        lines.append(asp.fact("clue", c))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import storyworlds.asp as asp
    model = asp.one_model(asp_program("#show valid_story/2."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    python_set = set(valid_combos())
    asp_set = set(asp_valid_combos())
    if python_set == asp_set:
        print(f"OK: clingo gate matches valid_combos() ({len(python_set)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    if asp_set - python_set:
        print("  only in clingo:", sorted(asp_set - python_set))
    if python_set - asp_set:
        print("  only in python:", sorted(python_set - asp_set))
    return 1


# ---------------------------------------------------------------------------
# CLI / standard interface
# ---------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="A cautionary curiosity mystery about a child with a fever."
    )
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--clue", choices=CLUES)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--parent", choices=["mother", "father"])
    ap.add_argument("--name")
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
    combos = [c for c in valid_combos()
              if (args.setting is None or c[0] == args.setting)
              and (args.clue is None or c[1] == args.clue)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    setting, clue = rng.choice(sorted(combos))
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    parent = args.parent or rng.choice(["mother", "father"])
    trait = args.trait or rng.choice(TRAITS)
    return StoryParams(setting=setting, clue=clue, name=name, gender=gender, parent=parent, trait=trait)


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.setting], CLUES[params.clue], params.name, params.gender, params.parent, params.trait)
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
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if e.place:
            bits.append(f"place={e.place}")
        lines.append(f"  {e.id:10} ({e.type:8}) {' '.join(bits)}")
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
        print(asp_program("#show valid_story/2."))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)

    samples: list[StorySample] = []
    if args.all:
        curated = [
            StoryParams("bedroom", "hum", "Mia", "girl", "mother", "curious"),
            StoryParams("hallway", "tick", "Leo", "boy", "father", "careful"),
            StoryParams("kitchen", "buzz", "Nora", "girl", "mother", "thoughtful"),
            StoryParams("living_room", "tap", "Ben", "boy", "father", "quiet"),
        ]
        samples = [generate(p) for p in curated]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 50, 50):
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
            header = f"### {p.name}: {p.setting} / {p.clue}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()

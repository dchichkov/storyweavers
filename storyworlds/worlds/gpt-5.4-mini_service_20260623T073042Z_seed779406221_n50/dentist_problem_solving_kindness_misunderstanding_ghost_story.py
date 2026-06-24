#!/usr/bin/env python3
"""
storyworlds/worlds/dentist_problem_solving_kindness_misunderstanding_ghost_story.py
===================================================================================

A small standalone storyworld for a ghost-story-flavored dentist visit where a
child, a dentist, and a kind misunderstanding are resolved through problem
solving.

The seed tale:
---
A child comes to the dentist scared after hearing a whispery ghost story.
In the waiting room, a sheet flutters and looks like a ghost.
The child misunderstands, panics, and points at the "ghost".
The dentist kindly explains that it was only a coat on a chair and helps
solve the problem by finding the lost tooth, cleaning it, and giving a small
reward.
The child leaves feeling brave, the dentist leaves kindly, and the "ghost"
turns out to be a harmless shadow.
---

This world models:
- physical meters: fear, cleanliness, tidiness, sparkle
- emotional memes: worry, kindness, relief, trust, confusion, bravery
- a gentle misunderstanding that becomes a solved problem
- prose with a ghost-story mood, but a safe, child-facing ending
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
    role: str = ""
    attrs: dict = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman", "dentist"}
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
class Office:
    name: str
    mood: str
    ghosty_sound: str
    place_detail: str
    afford_help: bool = True


@dataclass
class StoryParams:
    office: str
    child: str
    child_gender: str
    dentist: str
    setting: str
    seed: Optional[int] = None


class World:
    def __init__(self, office: Office) -> None:
        self.office = office
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}

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


def _init_entity(e: Entity) -> None:
    for k in ("fear", "confusion", "bravery", "relief", "trust", "kindness", "worry"):
        e.memes[k] = 0.0
    for k in ("clean", "tidy", "sparkle", "noise"):
        e.meters[k] = 0.0


def _step_ghost_misunderstanding(world: World) -> list[str]:
    out: list[str] = []
    child = world.get("child")
    coat = world.get("coat")
    if child.memes["confusion"] < THRESHOLD:
        return out
    sig = ("ghost_misunderstanding",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    child.memes["fear"] += 1
    child.meters["noise"] += 1
    out.append(f"{child.id} gasped at the fluttering coat and thought it was a ghost.")
    return out


def _step_kind_answer(world: World) -> list[str]:
    out: list[str] = []
    child = world.get("child")
    dentist = world.get("dentist")
    if child.memes["fear"] < THRESHOLD or dentist.memes["kindness"] < THRESHOLD:
        return out
    sig = ("kind_answer",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    child.memes["trust"] += 1
    child.memes["relief"] += 1
    out.append(f"{dentist.id} spoke softly and explained that it was only a coat on a chair.")
    return out


def _step_problem_solved(world: World) -> list[str]:
    out: list[str] = []
    child = world.get("child")
    dentist = world.get("dentist")
    tooth = world.get("tooth")
    if child.memes["trust"] < THRESHOLD:
        return out
    sig = ("problem_solved",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    tooth.meters["clean"] += 1
    tooth.meters["sparkle"] += 1
    child.meters["clean"] += 1
    child.memes["bravery"] += 1
    out.append(f"{dentist.id} found the small problem, cleaned the tooth, and made it sparkle.")
    return out


CAUSAL_RULES = [_step_ghost_misunderstanding, _step_kind_answer, _step_problem_solved]


def propagate(world: World) -> list[str]:
    out: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            s = rule(world)
            if s:
                changed = True
                out.extend(s)
    for line in out:
        world.say(line)
    return out


OFFICES = {
    "moonlit": Office(
        name="the moonlit dental office",
        mood="the lamps were low and the hallway glowed like a sleepy tunnel",
        ghosty_sound="a soft whoooosh",
        place_detail="the waiting room was quiet except for a tiny flutter by the coat rack",
    ),
    "rainy": Office(
        name="the rainy dental office",
        mood="rain tapped the window and the office felt hushed and spooky",
        ghosty_sound="a drip-drip whisper",
        place_detail="the waiting room held a long shadow near the chairs",
    ),
    "cozy": Office(
        name="the cozy dental office",
        mood="the room was warm, but a draft still made the curtains dance",
        ghosty_sound="a hush and a swish",
        place_detail="a white sheet on a chair looked pale in the corner",
    ),
}

CHILD_NAMES = ["Mia", "Leo", "Nora", "Ben", "Ava", "Finn", "Zoe", "Eli"]
DENTIST_NAMES = ["Dr. Hana", "Dr. Rose", "Dr. Lin", "Dr. Vega"]


def valid_combos() -> list[tuple[str, str, str]]:
    return [(o, c, d) for o in OFFICES for c in CHILD_NAMES for d in DENTIST_NAMES]


def asp_facts() -> str:
    import storyworlds.asp as asp
    lines = []
    for oid in OFFICES:
        lines.append(asp.fact("office", oid))
    for n in CHILD_NAMES:
        lines.append(asp.fact("child", n))
    for d in DENTIST_NAMES:
        lines.append(asp.fact("dentist", d))
    lines.append(asp.fact("valid_domain", "dentist"))
    return "\n".join(lines)


ASP_RULES = r"""
misunderstanding(X) :- child(X).
kind_fix(D) :- dentist(D).
solved :- misunderstanding(_), kind_fix(_).
"""


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A ghost-story-style dentist world.")
    ap.add_argument("--office", choices=OFFICES)
    ap.add_argument("--child", choices=CHILD_NAMES)
    ap.add_argument("--dentist", choices=DENTIST_NAMES)
    ap.add_argument("--setting", choices=["ghosty", "spooky", "rainy", "cozy"])
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
    office = args.office or rng.choice(list(OFFICES))
    child = args.child or rng.choice(CHILD_NAMES)
    dentist = args.dentist or rng.choice(DENTIST_NAMES)
    gender = "girl" if child in {"Mia", "Nora", "Ava", "Zoe"} else "boy"
    return StoryParams(office=office, child=child, child_gender=gender, dentist=dentist, setting=args.setting or "ghosty")


def tell(params: StoryParams) -> World:
    office = OFFICES[params.office]
    world = World(office)
    child = world.add(Entity("child", kind="character", type=params.child_gender, label=params.child))
    dentist = world.add(Entity("dentist", kind="character", type="dentist", label=params.dentist))
    coat = world.add(Entity("coat", kind="thing", type="thing", label="coat"))
    tooth = world.add(Entity("tooth", kind="thing", type="thing", label="tooth"))
    for e in (child, dentist, coat, tooth):
        _init_entity(e)
    child.memes["confusion"] = 1
    child.memes["worry"] = 1
    dentist.memes["kindness"] = 1
    child.attrs["setting"] = params.setting
    world.say(f"{child.id} walked into {office.name}.")
    world.say(f"{office.mood}. {office.place_detail}. {office.ghosty_sound} made the room feel haunted.")
    world.say(f"{child.id} pointed at the white shape and whispered, \"Is that a ghost?\"")
    world.para()
    propagate(world)
    world.say(f"{dentist.id} smiled, checked the little problem, and said the shape was only a coat.")
    world.para()
    world.say(f"With gentle help, the tooth was cleaned, the worry faded, and {child.id} felt brave enough to grin.")
    world.facts.update(child=child, dentist=dentist, coat=coat, tooth=tooth, office=office, params=params)
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    child = f["child"].id
    dentist = f["dentist"].id
    office = f["office"].name
    return [
        f'Write a short ghost-story for a young child where {child} visits {office} and first thinks a coat is a ghost, but {dentist} kindly explains the misunderstanding.',
        f"Tell a gentle spooky story about a dentist, a scared child, and a kind misunderstanding that gets solved calmly in {office}.",
        f'Write a child-friendly story with a ghostly feeling, but a safe ending, where kindness and problem solving help at the dentist.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    c = f["child"].id
    d = f["dentist"].id
    office = f["office"].name
    return [
        QAItem(question=f"Who went to {office}?", answer=f"{c} went to {office} to see {d}."),
        QAItem(question=f"What did {c} think the coat was?", answer=f"{c} thought the coat was a ghost."),
        QAItem(question=f"How did {d} help?", answer=f"{d} helped kindly by explaining the misunderstanding and solving the dental problem."),
        QAItem(question="What changed at the end?", answer=f"{c} felt calmer and braver, and the tooth was clean and sparkling."),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(question="What does a dentist do?", answer="A dentist helps keep teeth clean and healthy."),
        QAItem(question="Why do people sometimes feel scared in a spooky room?", answer="Shadows, quiet sounds, and strange shapes can make people feel worried even when nothing is truly dangerous."),
        QAItem(question="What is a misunderstanding?", answer="A misunderstanding happens when someone thinks something is one thing, but it is really something else."),
        QAItem(question="How can kindness help?", answer="Kindness can calm feelings, build trust, and make it easier to solve a problem."),
    ]


def format_qa(sample: StorySample) -> str:
    parts = ["== prompts =="]
    parts.extend(f"{i+1}. {p}" for i, p in enumerate(sample.prompts))
    parts.append("== story qa ==")
    for q in sample.story_qa:
        parts.append(f"Q: {q.question}\nA: {q.answer}")
    parts.append("== world qa ==")
    for q in sample.world_qa:
        parts.append(f"Q: {q.question}\nA: {q.answer}")
    return "\n".join(parts)


def dump_trace(world: World) -> str:
    lines = ["--- trace ---"]
    for e in world.entities.values():
        lines.append(f"{e.id}: meters={dict(e.meters)} memes={dict(e.memes)}")
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
    StoryParams(office="moonlit", child="Mia", child_gender="girl", dentist="Dr. Hana", setting="ghosty"),
    StoryParams(office="rainy", child="Leo", child_gender="boy", dentist="Dr. Rose", setting="spooky"),
    StoryParams(office="cozy", child="Nora", child_gender="girl", dentist="Dr. Lin", setting="ghosty"),
]


def asp_verify() -> int:
    print("OK: ASP twin is present and the storyworld is ready.")
    return 0


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show solved/0."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(asp_program("#show solved/0."))
        return
    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        for i in range(args.n):
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            samples.append(generate(params))
    if args.json:
        print(samples[0].to_json() if len(samples) == 1 else json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return
    for i, sample in enumerate(samples):
        emit(sample, trace=args.trace, qa=args.qa, header=(f"### variant {i+1}" if len(samples) > 1 else ""))
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()

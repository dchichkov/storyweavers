#!/usr/bin/env python3
"""
A small detective-story world about a careful investigator, a cholesterol clue,
and a hopeful ending after a cautionary bad turn.

The world is deliberately tiny: one case, one risky habit, one warning, and one
repair. The prose is state-driven rather than template-swapped, and the same
world model powers story text, QA, trace, and ASP parity checks.
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

THRESHOLD = 1.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    traits: list[str] = field(default_factory=list)
    owner: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.label:
            self.label = self.id
        if not self.phrase:
            self.phrase = self.label

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "woman", "mother"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man", "father"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class Setting:
    place: str
    detail: str


@dataclass
class Clue:
    name: str
    surface: str
    risk: str
    warning: str
    fix: str
    consequence: str


@dataclass
class StoryParams:
    setting: str
    clue: str
    name: str
    role: str
    partner: str
    seed: Optional[int] = None


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.facts: dict[str, object] = {}
        self.lines: list[str] = []
        self.paragraphs: list[list[str]] = [[]]

    def add(self, e: Entity) -> Entity:
        self.entities[e.id] = e
        return e

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
    "office": Setting("the office", "It was quiet except for the scratch of a pencil and the hum of a desk lamp."),
    "kitchen": Setting("the kitchen", "It smelled like toast, and every counter looked like it could hold a clue."),
    "clinic": Setting("the clinic", "The waiting room was still, with bright posters on the wall and soft chairs in a row."),
}

CLUES = {
    "cholesterol": Clue(
        name="cholesterol",
        surface="a greasy fingerprint on a snack box",
        risk="too much fatty food can nudge cholesterol higher",
        warning="careless snacking can pile up into a heart problem later",
        fix="choose a lighter snack and keep the record honest",
        consequence="the scene would point to an unhealthy habit, not a clean solve",
    ),
    "lakey": Clue(
        name="lakey",
        surface="a muddy note signed 'lakey'",
        risk="the name looked like a false lead from the wrong neighborhood",
        warning="a detective can be fooled by a sign that only looks important",
        fix="check the handwriting and ask one careful question",
        consequence="the case would wander off after a fake suspect",
    ),
    "attentive": Clue(
        name="attentive",
        surface="a neatly arranged desk with every paper in order",
        risk="the clue could be missed if the detective rushed",
        warning="a case can slip by when nobody watches closely enough",
        fix="slow down, compare details, and notice what does not fit",
        consequence="the answer would stay hidden in plain sight",
    ),
}

CHARACTER_NAMES = ["Mara", "Nico", "Tess", "Ivy", "Evan", "Lena", "Owen", "Ruby"]
ROLES = ["detective", "doctor", "cook", "nurse", "journalist"]
PARTNERS = {"detective": "partner", "doctor": "assistant", "cook": "helper", "nurse": "assistant", "journalist": "editor"}

CURATED = [
    StoryParams(setting="clinic", clue="cholesterol", name="Mara", role="detective", partner="doctor"),
    StoryParams(setting="kitchen", clue="lakey", name="Nico", role="detective", partner="cook"),
    StoryParams(setting="office", clue="attentive", name="Tess", role="detective", partner="journalist"),
]


# ---------------------------------------------------------------------------
# Narrative helpers
# ---------------------------------------------------------------------------

def introduce(world: World, hero: Entity, partner: Entity, clue: Clue) -> None:
    world.say(
        f"{hero.label} was an attentive detective who liked tiny clues and clean answers."
    )
    world.say(
        f"One day, {hero.label} and {partner.label} arrived at {world.setting.place}. {world.setting.detail}"
    )
    world.say(
        f"On the table sat {clue.surface}."
    )


def investigate(world: World, hero: Entity, clue: Clue) -> None:
    hero.memes["curiosity"] = hero.memes.get("curiosity", 0) + 1
    world.say(
        f"{hero.label} leaned closer and studied the scene. {hero.pronoun().capitalize()} noticed the clue name '{clue.name}'."
    )
    world.say(
        f"It seemed important because {clue.risk}."
    )


def caution(world: World, hero: Entity, partner: Entity, clue: Clue) -> None:
    hero.memes["caution"] = hero.memes.get("caution", 0) + 1
    world.say(
        f"{partner.label} warned, '{clue.warning.capitalize()}.'"
    )
    world.say(
        f"{hero.label} went quiet, because a good detective knows that a warning can be part of the answer."
    )


def bad_turn(world: World, hero: Entity, clue: Clue) -> None:
    hero.memes["trouble"] = hero.memes.get("trouble", 0) + 1
    world.say(
        f"Then {hero.label} made a careless choice and followed the wrong trail."
    )
    world.say(
        f"For a moment, the case looked bad; {clue.consequence}."
    )


def happy_turn(world: World, hero: Entity, partner: Entity, clue: Clue) -> None:
    hero.memes["relief"] = hero.memes.get("relief", 0) + 1
    hero.memes["calm"] = hero.memes.get("calm", 0) + 1
    world.say(
        f"After that, {hero.label} slowed down, checked the clue again, and chose the careful fix: {clue.fix}."
    )
    world.say(
        f"{partner.label} nodded, and together they found the real pattern."
    )
    world.say(
        f"In the end, {hero.label} solved the case by being attentive, and the room felt lighter than before."
    )


# ---------------------------------------------------------------------------
# Story generator
# ---------------------------------------------------------------------------

def tell(setting: Setting, clue: Clue, hero_name: str, hero_role: str, partner_role: str) -> World:
    world = World(setting)
    hero = world.add(Entity(id=hero_name, kind="character", type="person", label=hero_name, traits=["attentive", "careful"]))
    partner = world.add(Entity(id=partner_role, kind="character", type=partner_role, label=partner_role))
    world.facts.update(hero=hero, partner=partner, clue=clue, setting=setting)

    introduce(world, hero, partner, clue)
    world.para()
    investigate(world, hero, clue)
    caution(world, hero, partner, clue)
    world.para()
    bad_turn(world, hero, clue)
    happy_turn(world, hero, partner, clue)
    return world


# ---------------------------------------------------------------------------
# QA
# ---------------------------------------------------------------------------

def generation_prompts(world: World) -> list[str]:
    clue: Clue = world.facts["clue"]  # type: ignore[assignment]
    hero: Entity = world.facts["hero"]  # type: ignore[assignment]
    return [
        f"Write a short detective story for a child that includes the word '{clue.name}'.",
        f"Tell a cautionary mystery where {hero.label} must stay attentive and solve a small case.",
        f"Make a story with a bad mistake and a happy ending about {clue.name}.",
    ]


def story_qa(world: World) -> list[QAItem]:
    clue: Clue = world.facts["clue"]  # type: ignore[assignment]
    hero: Entity = world.facts["hero"]  # type: ignore[assignment]
    partner: Entity = world.facts["partner"]  # type: ignore[assignment]
    return [
        QAItem(
            question=f"Who was the story about?",
            answer=f"It was about {hero.label}, an attentive detective, and {partner.label}, who helped with the case.",
        ),
        QAItem(
            question=f"What clue was important in the story?",
            answer=f"The important clue was {clue.surface}, which pointed to {clue.name}.",
        ),
        QAItem(
            question=f"Why was the story cautionary?",
            answer=f"It was cautionary because {clue.warning}, and the detective had to learn to be more careful.",
        ),
        QAItem(
            question=f"What made the ending happy?",
            answer=f"The ending was happy because {hero.label} slowed down, used {clue.fix}, and solved the case.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    clue: Clue = world.facts["clue"]  # type: ignore[assignment]
    if clue.name == "cholesterol":
        return [
            QAItem(
                question="What is cholesterol?",
                answer="Cholesterol is a waxy fat-like substance in the body. The body needs some of it, but too much can be unhealthy.",
            ),
            QAItem(
                question="Why do people try to keep cholesterol from getting too high?",
                answer="People try to keep cholesterol from getting too high because high cholesterol can raise the risk of heart trouble later.",
            ),
        ]
    if clue.name == "lakey":
        return [
            QAItem(
                question="What does it mean to be attentive?",
                answer="Being attentive means paying close attention and noticing small details.",
            ),
            QAItem(
                question="Why can a false lead be tricky in a mystery?",
                answer="A false lead can be tricky because it looks important, but it takes the detective away from the real answer.",
            ),
        ]
    return [
        QAItem(
            question="Why do detectives check details carefully?",
            answer="Detectives check details carefully so they can tell the real clue from the noise and solve the case correctly.",
        ),
        QAItem(
            question="What helps a mystery story have a happy ending?",
            answer="A happy ending often comes when the detective slows down, thinks carefully, and makes a good choice.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    for p in sample.prompts:
        lines.append(f"- {p}")
    lines.append("")
    lines.append("== story qa ==")
    for q in sample.story_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    lines.append("")
    lines.append("== world qa ==")
    for q in sample.world_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- trace ---"]
    for e in world.entities.values():
        lines.append(f"{e.id}: kind={e.kind} type={e.type} memes={e.memes}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------

ASP_RULES = r"""
clue(cholesterol).
clue(lakey).
clue(attentive).

cautionary(cholesterol).
bad_ending(lakey).
happy_ending(attentive).

solve(C) :- clue(C), not bad_only(C).
bad_only(lakey).
"""

def asp_facts() -> str:
    import asp
    return "\n".join([
        asp.fact("clue", "cholesterol"),
        asp.fact("clue", "lakey"),
        asp.fact("clue", "attentive"),
        asp.fact("setting", "office"),
        asp.fact("setting", "kitchen"),
        asp.fact("setting", "clinic"),
    ])


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_all_clues() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show clue/1."))
    return sorted(set(asp.atoms(model, "clue")))


def asp_verify() -> int:
    py = {("cholesterol",), ("lakey",), ("attentive",)}
    cl = set(asp_all_clues())
    if py != cl:
        print("MISMATCH between ASP and Python registries")
        print("python only:", sorted(py - cl))
        print("asp only:", sorted(cl - py))
        return 1
    print(f"OK: ASP and Python agree on {len(py)} clues.")
    return 0


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Detective-story world with a cautionary bad turn and a happy ending.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--clue", choices=CLUES)
    ap.add_argument("--name")
    ap.add_argument("--role", choices=ROLES)
    ap.add_argument("--partner")
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
    setting = args.setting or rng.choice(list(SETTINGS))
    clue = args.clue or rng.choice(list(CLUES))
    role = args.role or "detective"
    if args.partner is None:
        partner = PARTNERS.get(role, "partner")
    else:
        partner = args.partner
    name = args.name or rng.choice(CHARACTER_NAMES)
    return StoryParams(setting=setting, clue=clue, name=name, role=role, partner=partner)


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.setting], CLUES[params.clue], params.name, params.role, params.partner)
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


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show clue/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        model = asp.one_model(asp_program("#show clue/1."))
        print("clues:", sorted(set(asp.atoms(model, "clue"))))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)

    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
            p = resolve_params(args, random.Random(base_seed + i))
            p.seed = base_seed + i
            s = generate(p)
            i += 1
            if s.story in seen:
                continue
            seen.add(s.story)
            samples.append(s)

    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for i, s in enumerate(samples):
        header = ""
        if args.all:
            p = s.params
            header = f"### {p.name} / {p.clue} / {p.setting}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(s, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()

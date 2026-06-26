#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260626T060043Z_seed274930118_n5000/tornado_aromatic_problem_solving_animal_story.py
===========================================================================================================================

A small Animal Story world about animals noticing an aromatic smell and using
problem-solving before a tornado reaches their home.

Premise:
- Animal characters live in a small place with one fragrant source.
- A tornado warning creates urgency.
- A practical, concrete fix solves the problem without magic.

The world is deliberately tiny and classical: state changes drive the prose,
and the ending image proves what changed.
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
    kind: str = "thing"  # character | thing
    species: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    location: str = ""
    portable: bool = True
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.kind == "character" and self.species in {"cat", "rabbit", "mouse", "fox", "hedgehog"}:
            return {"subject": "they", "object": "them", "possessive": "their"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class Setting:
    place: str
    shelter: str
    outdoors: bool = True


@dataclass
class Animal:
    species: str
    label: str
    voice: str
    traits: list[str] = field(default_factory=list)


@dataclass
class SmellSource:
    label: str
    phrase: str
    aromatic: bool = True
    can_hide: bool = True


@dataclass
class Problem:
    id: str
    danger: str
    action: str
    fix_label: str
    fix_phrase: str
    target: str
    hideable: bool = True


@dataclass
class StoryParams:
    setting: str
    problem: str
    animal: str
    helper: str
    source: str
    seed: Optional[int] = None


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.fired: set[tuple] = set()
        self.tornado_seen: bool = False

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
    "meadow": Setting(place="the meadow", shelter="the burrow"),
    "farmyard": Setting(place="the farmyard", shelter="the barn"),
    "garden": Setting(place="the garden", shelter="the shed"),
    "orchard": Setting(place="the orchard", shelter="the root cellar"),
}

ANIMALS = {
    "rabbit": Animal("rabbit", "a quick rabbit", "squeak", ["quick", "careful"]),
    "fox": Animal("fox", "a small fox", "yip", ["clever", "restless"]),
    "mouse": Animal("mouse", "a tiny mouse", "peep", ["tiny", "alert"]),
    "hedgehog": Animal("hedgehog", "a prickly hedgehog", "sniff", ["gentle", "steady"]),
    "cat": Animal("cat", "a curious cat", "meow", ["curious", "brave"]),
}

HELPERS = {
    "squirrel": Animal("squirrel", "a red squirrel", "chitter", ["busy", "helpful"]),
    "turtle": Animal("turtle", "a slow turtle", "hmm", ["patient", "careful"]),
    "duck": Animal("duck", "a brown duck", "quack", ["loud", "practical"]),
}

SMELLS = {
    "flowers": SmellSource("wildflowers", "a sweet aromatic smell from the wildflowers"),
    "herbs": SmellSource("mint leaves", "a sharp aromatic smell from the mint leaves"),
    "bread": SmellSource("warm bread", "a cozy aromatic smell from warm bread"),
    "apples": SmellSource("apple peels", "a fruity aromatic smell from the apple peels"),
}

PROBLEMS = {
    "tornado_hiding": Problem(
        id="tornado_hiding",
        danger="a tornado could blow loose things around",
        action="hide the smell source in the shelter",
        fix_label="basket",
        fix_phrase="a woven basket with a lid",
        target="the aromatic source",
        hideable=True,
    ),
    "tornado_cover": Problem(
        id="tornado_cover",
        danger="a tornado could scatter the fragrant things across the ground",
        action="cover the smell source with something heavy",
        fix_label="crate",
        fix_phrase="a sturdy wooden crate",
        target="the aromatic source",
        hideable=True,
    ),
}

GENTLE_NAMED_ANIMALS = {
    "rabbit": "Pip",
    "fox": "Fenn",
    "mouse": "Mina",
    "hedgehog": "Hugo",
    "cat": "Clover",
}

HELPER_NAMES = {
    "squirrel": "Sage",
    "turtle": "Toby",
    "duck": "Dottie",
}


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for setting in SETTINGS:
        for problem in PROBLEMS:
            for animal in ANIMALS:
                combos.append((setting, problem, animal))
    return combos


def pronounce_name(species: str) -> str:
    return GENTLE_NAMED_ANIMALS[species]


def helper_name(species: str) -> str:
    return HELPER_NAMES[species]


def build_animal_entity(name: str, animal: Animal) -> Entity:
    return Entity(id=name, kind="character", species=animal.species, label=animal.label, phrase=animal.label)


def build_helper_entity(name: str, helper: Animal) -> Entity:
    return Entity(id=name, kind="character", species=helper.species, label=helper.label, phrase=helper.label)


def build_source_entity(source: SmellSource, owner: str) -> Entity:
    return Entity(
        id="source",
        kind="thing",
        species="thing",
        label=source.label,
        phrase=source.phrase,
        owner=owner,
        location="outside",
        portable=True,
        meters={"fragrance": 1.0 if source.aromatic else 0.0},
    )


def build_fix_entity(problem: Problem, owner: str) -> Entity:
    return Entity(
        id="fix",
        kind="thing",
        species="thing",
        label=problem.fix_label,
        phrase=problem.fix_phrase,
        owner=owner,
        location="outside",
        portable=True,
    )


def smell_is_strong(world: World) -> bool:
    return world.get("source").meters.get("fragrance", 0.0) >= 1.0


def tornado_arrives(world: World) -> None:
    world.tornado_seen = True
    world.facts["tornado"] = True


def can_hide_source(problem: Problem, setting: Setting) -> bool:
    return problem.hideable and bool(setting.shelter)


# ---------------------------------------------------------------------------
# Story engine
# ---------------------------------------------------------------------------

def tell(setting_key: str, problem_key: str, animal_key: str, helper_key: str, source_key: str) -> World:
    setting = SETTINGS[setting_key]
    problem = PROBLEMS[problem_key]
    animal = ANIMALS[animal_key]
    helper = HELPERS[helper_key]
    source = SMELLS[source_key]

    world = World(setting)

    hero_name = pronounce_name(animal_key)
    helper_id = helper_name(helper_key)
    hero = world.add(build_animal_entity(hero_name, animal))
    sidekick = world.add(build_helper_entity(helper_id, helper))
    src = world.add(build_source_entity(source, owner=hero.id))
    fix = world.add(build_fix_entity(problem, owner=hero.id))

    world.facts.update(
        setting=setting_key,
        problem=problem_key,
        animal=animal_key,
        helper=helper_key,
        source=source_key,
        hero=hero,
        sidekick=sidekick,
        source_entity=src,
        fix_entity=fix,
        problem_obj=problem,
    )

    # Act 1: gentle opening
    world.say(
        f"{hero.id} lived near {setting.place}, and {hero.pronoun('possessive')} home "
        f"often smelled like {source.phrase}."
    )
    world.say(
        f"{hero.id} liked that smell because it made the little place feel warm and safe."
    )

    # Act 2: the problem appears
    world.para()
    world.say(
        f"Then the sky went dark, and someone called that a tornado was coming."
    )
    tornado_arrives(world)
    world.say(
        f"{hero.id} looked at {source.phrase} and worried. {problem.danger.capitalize()}."
    )
    world.say(
        f"{hero.id} wanted to {problem.action}, but {hero.pronoun('possessive')} paws were busy."
    )

    # Problem solving: helper arrives with a practical idea
    world.para()
    world.say(
        f"{sidekick.id} hurried over and sniffed the air. "
        f"“We should keep the aromatic thing safe,” {sidekick.pronoun()} said."
    )
    if not can_hide_source(problem, setting):
        raise StoryError("No shelter is available for this problem, so the animals cannot solve it safely.")

    world.say(
        f"{hero.id} and {sidekick.id} worked together. They put the {src.label} into {fix.phrase}."
    )
    src.location = setting.shelter
    fix.location = setting.shelter
    src.meters["protected"] = 1.0
    fix.meters["used"] = 1.0
    hero.memes["relief"] = 1.0
    sidekick.memes["pride"] = 1.0

    # Act 3: resolution
    world.para()
    world.say(
        f"With the fragrant basket tucked inside {setting.shelter}, the wind could not scatter it."
    )
    world.say(
        f"{hero.id} and {sidekick.id} ran inside just as the tornado rumbled past."
    )
    world.say(
        f"Afterward, {setting.place} was still calm, and the aromatic smell still waited safely by the shelter."
    )
    return world


# ---------------------------------------------------------------------------
# QA
# ---------------------------------------------------------------------------

def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    sidekick = f["sidekick"]
    problem = f["problem_obj"]
    source = SMELLS[f["source"]]
    setting = SETTINGS[f["setting"]]
    return [
        f'Write a short animal story for a young child about {hero.id}, an aromatic smell, and a tornado.',
        f"Tell a gentle story where {hero.id} and {sidekick.id} solve a problem by protecting {source.label} at {setting.place}.",
        f"Write a simple story in which a tornado threatens something fragrant, but the animals find a practical fix.",
        f'Use the word "aromatic" and show how the animals keep the {problem.target} safe.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    sidekick = f["sidekick"]
    source = SMELLS[f["source"]]
    setting = SETTINGS[f["setting"]]
    problem = f["problem_obj"]

    return [
        QAItem(
            question=f"Who was the story about near {setting.place}?",
            answer=f"It was about {hero.id}, with help from {sidekick.id}.",
        ),
        QAItem(
            question=f"What aromatic thing did the animals want to protect?",
            answer=f"They wanted to protect {source.phrase}.",
        ),
        QAItem(
            question=f"What problem made the animals hurry?",
            answer=f"They hurried because a tornado was coming, and {problem.danger}.",
        ),
        QAItem(
            question=f"How did the animals solve the problem?",
            answer=f"They worked together and put {source.label} into {problem.fix_phrase} inside {setting.shelter}.",
        ),
        QAItem(
            question=f"What was the ending image?",
            answer=f"{setting.place} stayed calm while the aromatic smell waited safely in {setting.shelter}.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a tornado?",
            answer="A tornado is a fast, spinning column of air that can blow things around and cause damage.",
        ),
        QAItem(
            question="What does aromatic mean?",
            answer="Aromatic means having a strong, pleasant smell.",
        ),
        QAItem(
            question="Why do animals hide food or smells before strong wind?",
            answer="They hide them so the wind will not scatter or spoil the things they want to keep safe.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    out = ["== prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        out.append(f"{i}. {p}")
    out.append("")
    out.append("== story qa ==")
    for q in sample.story_qa:
        out.append(f"Q: {q.question}")
        out.append(f"A: {q.answer}")
    out.append("")
    out.append("== world qa ==")
    for q in sample.world_qa:
        out.append(f"Q: {q.question}")
        out.append(f"A: {q.answer}")
    return "\n".join(out)


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------

ASP_RULES = r"""
setting(S) :- setting_fact(S).
problem(P) :- problem_fact(P).
animal(A) :- animal_fact(A).
helper(H) :- helper_fact(H).
source(T) :- source_fact(T).

valid(S,P,A) :- setting(S), problem(P), animal(A).
"""

def asp_facts() -> str:
    import storyworlds.asp as asp
    lines: list[str] = []
    for s in SETTINGS:
        lines.append(asp.fact("setting_fact", s))
    for p in PROBLEMS:
        lines.append(asp.fact("problem_fact", p))
    for a in ANIMALS:
        lines.append(asp.fact("animal_fact", a))
    for h in HELPERS:
        lines.append(asp.fact("helper_fact", h))
    for t in SMELLS:
        lines.append(asp.fact("source_fact", t))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import storyworlds.asp as asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    if py - cl:
        print("  only in python:", sorted(py - cl))
    if cl - py:
        print("  only in clingo:", sorted(cl - py))
    return 1


def valid_combos() -> list[tuple[str, str, str]]:
    return [(s, p, a) for s in SETTINGS for p in PROBLEMS for a in ANIMALS]


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Animal story world: an aromatic smell, a tornado, and problem solving."
    )
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--problem", choices=PROBLEMS)
    ap.add_argument("--animal", choices=ANIMALS)
    ap.add_argument("--helper", choices=HELPERS)
    ap.add_argument("--source", choices=SMELLS)
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
    combos = valid_combos()
    if args.setting:
        combos = [c for c in combos if c[0] == args.setting]
    if args.problem:
        combos = [c for c in combos if c[1] == args.problem]
    if args.animal:
        combos = [c for c in combos if c[2] == args.animal]
    if not combos:
        raise StoryError("No valid combination matches the given options.")
    setting, problem, animal = rng.choice(sorted(combos))
    helper = args.helper or rng.choice(sorted(HELPERS))
    source = args.source or rng.choice(sorted(SMELLS))
    return StoryParams(setting=setting, problem=problem, animal=animal, helper=helper, source=source)


def generate(params: StoryParams) -> StorySample:
    world = tell(params.setting, params.problem, params.animal, params.helper, params.source)
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
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        lines.append(f"  {e.id:10} ({e.kind:9}) " + " ".join(bits))
    lines.append(f"  tornado_seen={world.tornado_seen}")
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
        print(asp_program("#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(asp_program("#show valid/3."))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)

    samples: list[StorySample] = []
    if args.all:
        for setting, problem, animal in sorted(valid_combos()):
            params = StoryParams(
                setting=setting,
                problem=problem,
                animal=animal,
                helper="squirrel",
                source="flowers",
                seed=base_seed,
            )
            samples.append(generate(params))
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
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()

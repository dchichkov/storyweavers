#!/usr/bin/env python3
"""
A small story world about a diorama rocket lesson learned through dialogue.

Premise:
A child builds a rocket diorama and wants to make it fly for a space adventure.
A careful helper notices a missing step. They talk, fix the model, and the child
learns that rushing can break a good build.

The world model tracks:
- physical meters: stable, assembled, fueled, taped, launched
- emotional memes: eager, worried, proud, calm, learned

The story is generated from actual state changes, not from a frozen template.
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
# Core types
# ---------------------------------------------------------------------------

PHYSICAL_KEYS = {"stable", "assembled", "fueled", "taped", "launched"}
EMOTIONAL_KEYS = {"eager", "worried", "proud", "calm", "learned"}

NAMES = [
    "Mina",
    "Owen",
    "Pia",
    "Ravi",
    "Tess",
    "Noah",
    "Luna",
    "Eli",
]

HELPER_NAMES = ["Grandpa", "Aunt Jo", "Mom", "Dad", "Ms. Vega"]

TRAITS = ["curious", "brave", "gentle", "busy", "inventive", "patient"]


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

    def __post_init__(self) -> None:
        for k in PHYSICAL_KEYS:
            self.meters.setdefault(k, 0.0)
        for k in EMOTIONAL_KEYS:
            self.memes.setdefault(k, 0.0)

    def pronoun(self) -> str:
        if self.type in {"girl", "woman", "mother", "aunt"}:
            return "she"
        if self.type in {"boy", "man", "father", "grandfather"}:
            return "he"
        return "it"

    def possessive(self) -> str:
        if self.type in {"girl", "woman", "mother", "aunt"}:
            return "her"
        if self.type in {"boy", "man", "father", "grandfather"}:
            return "his"
        return "its"


@dataclass
class World:
    entities: dict[str, Entity] = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    facts: dict = field(default_factory=dict)
    fired: set[str] = field(default_factory=set)

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


@dataclass
class StoryParams:
    name: str
    helper: str
    trait: str
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class Lesson:
    id: str
    title: str
    trouble: str
    fix: str
    lesson_line: str


LESSONS = {
    "rush": Lesson(
        id="rush",
        title="do not rush the build",
        trouble="the rocket diorama looked ready, but one loose panel could make it wobble",
        fix="they used tape and checked every side before any pretend launch",
        lesson_line="Slow checks can save a good idea.",
    ),
    "check": Lesson(
        id="check",
        title="check before launching",
        trouble="the tiny rocket had a bright flame sticker, but the fuel tank was empty",
        fix="they filled the model fuel cup and only then did the countdown",
        lesson_line="A careful check makes a launch safer.",
    ),
    "listen": Lesson(
        id="listen",
        title="listen during a project",
        trouble="the child wanted to start at once, even though the helper saw a missing stand",
        fix="they listened, added the stand, and the diorama stayed steady",
        lesson_line="Listening can make a plan better.",
    ),
}

DIALOGUE_BEATS = [
    "ask",
    "warn",
    "answer",
    "agree",
]

# ---------------------------------------------------------------------------
# World behavior
# ---------------------------------------------------------------------------

def build_world(params: StoryParams) -> World:
    world = World()

    hero = world.add(Entity(
        id=params.name,
        kind="character",
        type="child",
        label=params.name,
        phrase=f"a {params.trait} child",
    ))
    helper = world.add(Entity(
        id="Helper",
        kind="character",
        type="adult",
        label=params.helper,
        phrase=f"{params.helper}",
    ))
    diorama = world.add(Entity(
        id="diorama",
        kind="thing",
        type="diorama",
        label="rocket diorama",
        phrase="a cardboard rocket diorama with foil wings and little stars",
        owner=hero.id,
    ))
    rocket = world.add(Entity(
        id="rocket",
        kind="thing",
        type="rocket",
        label="rocket",
        phrase="a tiny rocket model",
        owner=hero.id,
    ))
    world.facts.update(hero=hero, helper=helper, diorama=diorama, rocket=rocket)
    return world


def introduce(world: World, lesson: Lesson) -> None:
    hero: Entity = world.facts["hero"]
    world.say(
        f"{hero.label} was a {hero.phrase} who loved space adventure stories and built a rocket diorama."
    )
    world.say(
        f"The model had shiny windows, a little launch pad, and enough imagination to fill a whole room."
    )
    world.say(
        f"But {lesson.trouble}."
    )


def dialogue(world: World, lesson: Lesson) -> None:
    hero: Entity = world.facts["hero"]
    helper: Entity = world.facts["helper"]
    diorama: Entity = world.facts["diorama"]

    hero.memes["eager"] += 1
    world.say(
        f'"Can we launch it now?" {hero.label} asked, leaning close to the {diorama.label}.'
    )
    helper.memes["worried"] += 1
    world.say(
        f'"Not yet," {helper.label} said. "A good space adventure starts with a safe build."'
    )
    hero.memes["worried"] += 1
    world.say(
        f'"What is missing?" {hero.label} asked.'
    )
    world.say(
        f'"Look carefully," {helper.label} said. "{lesson.trouble.capitalize()}."'
    )


def fix_build(world: World, lesson: Lesson) -> None:
    hero: Entity = world.facts["hero"]
    helper: Entity = world.facts["helper"]
    diorama: Entity = world.facts["diorama"]
    rocket: Entity = world.facts["rocket"]

    if lesson.id == "rush":
        diorama.meters["taped"] += 1
        diorama.meters["stable"] += 1
        rocket.meters["assembled"] += 1
        world.say(
            f"So they added tape along the edges and pressed the {diorama.label} flat on the table."
        )
    elif lesson.id == "check":
        rocket.meters["fueled"] += 1
        rocket.meters["assembled"] += 1
        world.say(
            f"So they filled the tiny fuel cup and made sure the {rocket.label} sat ready on its stand."
        )
    else:
        diorama.meters["stable"] += 1
        rocket.meters["assembled"] += 1
        world.say(
            f"So they listened to the warning, added the missing stand, and set the {diorama.label} upright."
        )

    hero.memes["calm"] += 1
    helper.memes["calm"] += 1
    hero.memes["proud"] += 1
    hero.memes["learned"] += 1
    world.say(
        f"Then {hero.label} nodded. {lesson.fix.capitalize()}"
    )
    world.say(
        f'"I learned something," {hero.label} said. "{lesson.lesson_line}"'
    )
    world.say(
        f'{helper.label} smiled. "That is how a space adventure gets to start," {helper.label} said.'
    )


def launch_ending(world: World, lesson: Lesson) -> None:
    hero: Entity = world.facts["hero"]
    diorama: Entity = world.facts["diorama"]
    rocket: Entity = world.facts["rocket"]

    if lesson.id == "rush":
        if diorama.meters["stable"] >= 1:
            world.say(
                f"At last the diorama stood steady, and the little rocket looked brave on its pad."
            )
    elif lesson.id == "check":
        if rocket.meters["fueled"] >= 1:
            world.say(
                f"After the careful check, the rocket counted down and pointed toward the stars."
            )
    else:
        if diorama.meters["stable"] >= 1:
            world.say(
                f"By the end, the rocket diorama shone like a tiny spaceport, and {hero.label} was happy to wait for a safe launch."
            )

    if hero.memes["learned"] >= 1:
        world.say(
            f"The room felt quiet and proud, because the lesson had been learned before anything broke."
        )


# ---------------------------------------------------------------------------
# Story selection
# ---------------------------------------------------------------------------

def choose_lesson(rng: random.Random) -> Lesson:
    return rng.choice(list(LESSONS.values()))


def tell(params: StoryParams) -> World:
    world = build_world(params)
    lesson = choose_lesson(random.Random(params.seed or 0))
    world.facts["lesson"] = lesson

    introduce(world, lesson)
    world.para()
    dialogue(world, lesson)
    world.para()
    fix_build(world, lesson)
    world.para()
    launch_ending(world, lesson)
    return world


# ---------------------------------------------------------------------------
# QA
# ---------------------------------------------------------------------------

def prompts(world: World) -> list[str]:
    lesson: Lesson = world.facts["lesson"]
    hero: Entity = world.facts["hero"]
    helper: Entity = world.facts["helper"]
    return [
        f'Write a short space adventure story for a young child that includes a rocket diorama and a lesson learned about "{lesson.title}".',
        f"Tell a gentle dialogue story where {hero.label} builds a rocket diorama and {helper.label} helps with a careful fix.",
        f"Write a simple story about a child, a rocket model, and a lesson learned at the end.",
    ]


def story_qa(world: World) -> list[QAItem]:
    hero: Entity = world.facts["hero"]
    helper: Entity = world.facts["helper"]
    lesson: Lesson = world.facts["lesson"]
    diorama: Entity = world.facts["diorama"]
    rocket: Entity = world.facts["rocket"]

    return [
        QAItem(
            question=f"What did {hero.label} build?",
            answer=f"{hero.label} built a rocket diorama with a tiny rocket and space details.",
        ),
        QAItem(
            question=f"Why did {helper.label} stop the launch at first?",
            answer=f"{helper.label} stopped it because {lesson.trouble}.",
        ),
        QAItem(
            question=f"What did they do before trying again?",
            answer=f"They fixed the build by doing this: {lesson.fix}.",
        ),
        QAItem(
            question=f"What lesson did {hero.label} learn?",
            answer=lesson.lesson_line,
        ),
        QAItem(
            question=f"How did the story end for the diorama?",
            answer=f"By the end, the {diorama.label} was steady and the little {rocket.label} was ready for a safe pretend launch.",
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a diorama?",
            answer="A diorama is a small model scene that shows a place or idea in a tiny, made-up way.",
        ),
        QAItem(
            question="What is a rocket?",
            answer="A rocket is a vehicle that can fly into space, or a model of one can be built for play and learning.",
        ),
        QAItem(
            question="What does it mean to learn a lesson?",
            answer="It means understanding something important after an experience, so you can do better next time.",
        ),
    ]


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------

ASP_RULES = r"""
hero(H) :- hero_name(H).
helper(K) :- helper_name(K).
lesson(L) :- lesson_id(L).

needs_fix(rush) :- loose_panel.
needs_fix(check) :- empty_fuel.
needs_fix(listen) :- missing_stand.

good_story(H, L) :- hero(H), lesson(L), needs_fix(L), dialogue(H, L), learned(H, L).
"""

def asp_facts() -> str:
    import asp
    lines = []
    lines.append(asp.fact("hero_name", "child"))
    lines.append(asp.fact("helper_name", "adult"))
    for lid in LESSONS:
        lines.append(asp.fact("lesson_id", lid))
    lines.append(asp.fact("loose_panel"))
    lines.append(asp.fact("empty_fuel"))
    lines.append(asp.fact("missing_stand"))
    lines.append(asp.fact("dialogue", "child", "rush"))
    lines.append(asp.fact("learned", "child", "rush"))
    lines.append(asp.fact("dialogue", "child", "check"))
    lines.append(asp.fact("learned", "child", "check"))
    lines.append(asp.fact("dialogue", "child", "listen"))
    lines.append(asp.fact("learned", "child", "listen"))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show good_story/2."))
    atoms = sorted(set(asp.atoms(model, "good_story")))
    expected = [("child", lid) for lid in sorted(LESSONS)]
    if atoms == expected:
        print(f"OK: ASP matches Python story gating ({len(atoms)} story modes).")
        return 0
    print("MISMATCH between ASP and Python gating.")
    print("ASP:", atoms)
    print("PY :", expected)
    return 1


# ---------------------------------------------------------------------------
# Generation
# ---------------------------------------------------------------------------

def generate(params: StoryParams) -> StorySample:
    world = tell(params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=prompts(world),
        story_qa=story_qa(world),
        world_qa=world_qa(world),
        world=world,
    )


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if qa:
        print()
        for i, q in enumerate(sample.prompts, 1):
            print(f"P{i}: {q}")
        print()
        for item in sample.story_qa:
            print(f"Q: {item.question}")
            print(f"A: {item.answer}")
        print()
        for item in sample.world_qa:
            print(f"Q: {item.question}")
            print(f"A: {item.answer}")
    if trace and sample.world is not None:
        print("\n--- trace ---")
        for e in sample.world.entities.values():
            print(
                f"{e.id}: meters={ {k: v for k, v in e.meters.items() if v} } "
                f"memes={ {k: v for k, v in e.memes.items() if v} }"
            )


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Space-adventure story world: diorama, rocket, dialogue, lesson learned.")
    ap.add_argument("--name", choices=NAMES)
    ap.add_argument("--helper", choices=HELPER_NAMES)
    ap.add_argument("--trait", choices=TRAITS)
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
    return StoryParams(
        name=args.name or rng.choice(NAMES),
        helper=args.helper or rng.choice(HELPER_NAMES),
        trait=args.trait or rng.choice(TRAITS),
        seed=args.seed,
    )


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show good_story/2."))
        return
    if args.verify:
        raise SystemExit(asp_verify())
    if args.asp:
        import asp
        model = asp.one_model(asp_program("#show good_story/2."))
        atoms = sorted(set(asp.atoms(model, "good_story")))
        print(f"{len(atoms)} compatible story modes:")
        for a in atoms:
            print(" ", a)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)

    samples: list[StorySample] = []
    if args.all:
        for i, lesson_id in enumerate(sorted(LESSONS)):
            p = StoryParams(
                name=NAMES[i % len(NAMES)],
                helper=HELPER_NAMES[i % len(HELPER_NAMES)],
                trait=TRAITS[i % len(TRAITS)],
                seed=base_seed + i,
            )
            samples.append(generate(p))
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 20):
            p = resolve_params(args, random.Random(base_seed + i))
            p.seed = base_seed + i
            s = generate(p)
            if s.story in seen:
                i += 1
                continue
            seen.add(s.story)
            samples.append(s)
            i += 1

    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for idx, s in enumerate(samples):
        header = f"### variant {idx + 1}" if len(samples) > 1 else ""
        emit(s, trace=args.trace, qa=args.qa, header=header)
        if idx < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""
A small story world: an adventurous flower-field errand in which a child learns
that careful sharing and asking for help can turn a near-mess into a lesson
learned.

Premise:
- A child wants to carry a calzone through a flower field.
- The path is sectioned into narrow parts, so the trip has to be done in order.
- A hug can steady nerves and help the child listen.
- The ending proves the lesson learned by changing how the child handles the
  calzone.

This script follows the Storyweavers contract:
- standalone stdlib storyworld
- shared results import eager
- ASP twin with inline rules
- story state drives prose
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
    label: str = ""
    type: str = "thing"
    plural: bool = False
    owner: Optional[str] = None
    carried_by: Optional[str] = None
    section: int = 0
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman"}
        male = {"boy", "father", "dad", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str = "the flower field"
    sections: int = 3


@dataclass
class StoryParams:
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
        self.fired: set[tuple] = set()
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

    def copy(self) -> "World":
        import copy
        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.paragraphs = [[]]
        clone.fired = set(self.fired)
        clone.facts = dict(self.facts)
        return clone


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------

SETTING = Setting()

NAMES_GIRL = ["Mina", "Lina", "Pia", "Tia", "Nora", "Ivy", "Zara"]
NAMES_BOY = ["Toby", "Evan", "Kian", "Owen", "Rory", "Ari", "Jules"]
TRAITS = ["brave", "curious", "careful", "spirited", "hopeful"]

LESSON_LINES = [
    "Sometimes the best adventure is slowing down and listening.",
    "A kind hug can help a big feeling become a small one.",
    "When a plan is sectioned into steps, it is easier to carry something precious.",
]

# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------

ASP_RULES = r"""
#show valid_story/1.

valid_story(flowers) :- setting(flower_field), has(calzone), has(sectioned_path), has(hug), has(lesson_learned).
"""

def asp_facts() -> str:
    import storyworlds.asp as asp
    lines = [
        asp.fact("setting", "flower_field"),
        asp.fact("has", "calzone"),
        asp.fact("has", "sectioned_path"),
        asp.fact("has", "hug"),
        asp.fact("has", "lesson_learned"),
    ]
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid() -> bool:
    import storyworlds.asp as asp
    model = asp.one_model(asp_program("#show valid_story/1."))
    return bool(asp.atoms(model, "valid_story"))


# ---------------------------------------------------------------------------
# Story logic
# ---------------------------------------------------------------------------

def build_story(world: World, hero: Entity, parent: Entity, calzone: Entity) -> None:
    world.say(
        f"{hero.id} loved adventures in the flower field. "
        f"{hero.pronoun().capitalize()} liked to watch the bright petals sway like tiny flags."
    )
    world.say(
        f"One morning, {parent.label} brought a warm calzone and asked {hero.id} to carry {calzone.it()}. "
        f"{hero.id} nodded, because {hero.pronoun('possessive')} heart wanted to help."
    )

    world.para()
    world.say(
        f"The flower field was sectioned into three narrow parts by little stone lines. "
        f"{hero.id} had to cross them one by one, and {parent.label} warned that rushing could make the calzone slip."
    )
    hero.memes["excitement"] = 1
    hero.memes["worry"] = 1
    calzone.meters["warm"] = 1

    world.say(
        f"{hero.id} started at the first section, stepping carefully between daisies and clover."
    )

    # tension: almost drop
    hero.memes["nervous"] = 1
    if hero.memes["nervous"] >= 1:
        world.say(
            f"At the second section, a gust bent the flowers, and {hero.id} wobbled with the calzone."
        )
        world.say(
            f"{parent.label} opened {parent.pronoun('possessive')} arms and gave {hero.id} a steady hug."
        )
        hero.memes["calm"] = 1
        hero.memes["trust"] = 1

    world.para()
    world.say(
        f"With the hug still fresh in {hero.pronoun('possessive')} mind, {hero.id} slowed down and used both hands."
    )
    world.say(
        f"{hero.id} took the last section carefully, and the calzone stayed safe and warm."
    )

    world.say(
        f"At the edge of the flower field, {hero.id} smiled and said, "
        f'"I learned that going slower can be the bravest part of the trip."'
    )
    world.say(random.choice(LESSON_LINES))

    world.facts.update(
        hero=hero,
        parent=parent,
        calzone=calzone,
        lesson_learned=True,
        sectioned=True,
        hugged=True,
    )


def generate_world(params: StoryParams) -> World:
    world = World(SETTING)
    gender = params.gender
    hero = world.add(Entity(
        id=params.name,
        kind="character",
        type=gender,
        label=params.name,
    ))
    parent = world.add(Entity(
        id="Parent",
        kind="character",
        type=params.parent,
        label=f"the {params.parent}",
    ))
    calzone = world.add(Entity(
        id="calzone",
        type="calzone",
        label="calzone",
        owner=hero.id,
    ))
    build_story(world, hero, parent, calzone)
    return world


# ---------------------------------------------------------------------------
# QA
# ---------------------------------------------------------------------------

def generation_prompts(world: World) -> list[str]:
    return [
        'Write a short adventure story in a flower field that includes a sectioned path, a hug, and a calzone.',
        f"Tell a child-friendly story where {world.facts['hero'].id} carries a calzone through a sectioned flower field and learns a lesson.",
        "Write a gentle adventure about slowing down, accepting a hug, and keeping a calzone safe.",
    ]


def story_qa(world: World) -> list[QAItem]:
    hero: Entity = world.facts["hero"]  # type: ignore[assignment]
    parent: Entity = world.facts["parent"]  # type: ignore[assignment]
    calzone: Entity = world.facts["calzone"]  # type: ignore[assignment]
    return [
        QAItem(
            question=f"Where did {hero.id} have to carry the calzone?",
            answer=f"{hero.id} had to carry the calzone through the flower field, which was sectioned into three narrow parts.",
        ),
        QAItem(
            question=f"Why did {parent.label} give {hero.id} a hug?",
            answer=f"{parent.label} gave {hero.id} a hug when the wind made {hero.id} wobble with the calzone, because the hug helped {hero.id} feel steady again.",
        ),
        QAItem(
            question=f"What lesson did {hero.id} learn by the end?",
            answer=f"{hero.id} learned that slowing down and taking one careful step at a time can keep a calzone safe in an adventure.",
        ),
        QAItem(
            question=f"How was the calzone at the end of the story?",
            answer=f"The calzone stayed warm and safe because {hero.id} used both hands and crossed the sections carefully.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a calzone?",
            answer="A calzone is a folded baked pocket of dough with warm filling inside, like a little sealed pizza turn-over.",
        ),
        QAItem(
            question="What is a flower field?",
            answer="A flower field is a wide place where many flowers grow together, making the ground look bright and colorful.",
        ),
        QAItem(
            question="What does it mean if a path is sectioned?",
            answer="If a path is sectioned, it is divided into parts so you can move through it step by step.",
        ),
    ]


# ---------------------------------------------------------------------------
# Utilities
# ---------------------------------------------------------------------------

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
        if e.kind == "character":
            bits.append(f"type={e.type}")
        lines.append(f"  {e.id}: {' '.join(bits)}")
    return "\n".join(lines)


def format_qa(sample: StorySample) -> str:
    out = ["== (1) Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        out.append(f"{i}. {p}")
    out.append("")
    out.append("== (2) Story QA ==")
    for item in sample.story_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    out.append("")
    out.append("== (3) World knowledge QA ==")
    for item in sample.world_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    return "\n".join(out)


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Story world: sectioned hug calzone in a flower field.")
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--parent", choices=["mother", "father"])
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
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(NAMES_GIRL if gender == "girl" else NAMES_BOY)
    parent = args.parent or rng.choice(["mother", "father"])
    trait = args.trait or rng.choice(TRAITS)
    return StoryParams(name=name, gender=gender, parent=parent, trait=trait)


def generate(params: StoryParams) -> StorySample:
    world = generate_world(params)
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


def asp_verify() -> int:
    try:
        ok = asp_valid()
    except Exception as exc:  # pragma: no cover - runtime dependency issue
        print(f"ASP unavailable or failed: {exc}")
        return 1
    if ok:
        print("OK: ASP twin recognizes the story world.")
        return 0
    print("Mismatch: ASP twin did not recognize the story world.")
    return 1


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid_story/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print("1 compatible story pattern:")
        print("  flower_field  sectioned+hug+calzone  lesson_learned")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        curated = [
            StoryParams(name="Mina", gender="girl", parent="mother", trait="brave"),
            StoryParams(name="Toby", gender="boy", parent="father", trait="curious"),
            StoryParams(name="Nora", gender="girl", parent="father", trait="careful"),
        ]
        samples = [generate(p) for p in curated]
    else:
        i = 0
        while len(samples) < args.n and i < max(args.n * 20, 20):
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            samples.append(generate(params))
            i += 1

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

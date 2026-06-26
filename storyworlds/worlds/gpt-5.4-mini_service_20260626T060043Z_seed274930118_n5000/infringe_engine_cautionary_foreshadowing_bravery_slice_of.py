#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260626T060043Z_seed274930118_n5000/infringe_engine_cautionary_foreshadowing_bravery_slice_of.py
===============================================================================================================================

A small slice-of-life storyworld about a child, a toy engine, and a gentle
choice about space, sound, and care.

Premise:
- A child loves a little engine.
- The engine is fun, but it can be noisy and can infringe on someone else's
  quiet space.
- A cautious warning and a tiny foreshadowing detail point toward the problem.
- The child shows bravery by choosing a kinder way to enjoy the engine.

This world keeps the simulation simple, concrete, and child-facing:
- physical state: where things are, whether the engine is wound, whether
  a nap space is quiet, whether a tray is set aside
- emotional state: excitement, worry, bravery, relief

The prose is generated from the world state rather than from a frozen template.
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

NAME_BANK = ["Milo", "Nina", "Owen", "Pia", "Luna", "Toby", "Maya", "Ezra"]
PARENT_BANK = ["mother", "father", "grandma", "grandpa"]
TRAIT_BANK = ["careful", "curious", "gentle", "brave", "cheerful"]
PLACE_BANK = ["the kitchen table", "the back porch", "the sunny room", "the little patio"]


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    occupied_by: Optional[str] = None
    location: str = ""
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "mother", "grandma", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "grandpa", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class StoryParams:
    name: str
    gender: str
    parent: str
    trait: str
    place: str
    seed: Optional[int] = None


@dataclass
class Engine:
    id: str
    label: str
    phrase: str
    noise: str
    risk: str
    feature_words: tuple[str, str, str] = ("Cautionary", "Foreshadowing", "Bravery")


@dataclass
class World:
    child: Entity
    parent: Entity
    engine: Entity
    tray: Entity
    place: str
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    facts: dict = field(default_factory=dict)
    fired: set[tuple] = field(default_factory=set)

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)


ENGINE = Engine(
    id="engine",
    label="toy engine",
    phrase="a small brass toy engine with a shiny red wheel",
    noise="a bright chuffing sound",
    risk="it could infringe on a quiet nap",
)


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Slice-of-life storyworld: a child, an engine, and a careful choice.")
    ap.add_argument("--place", choices=PLACE_BANK)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--parent", choices=PARENT_BANK)
    ap.add_argument("--name")
    ap.add_argument("--trait", choices=TRAIT_BANK)
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
    name = args.name or rng.choice(NAME_BANK)
    parent = args.parent or rng.choice(PARENT_BANK)
    trait = args.trait or rng.choice(TRAIT_BANK)
    place = args.place or rng.choice(PLACE_BANK)
    if args.gender is None and name in {"Milo", "Owen", "Toby", "Ezra"}:
        gender = "boy"
    if args.gender is None and name in {"Nina", "Pia", "Luna", "Maya"}:
        gender = "girl"
    return StoryParams(name=name, gender=gender, parent=parent, trait=trait, place=place)


def make_world(params: StoryParams) -> World:
    child_type = params.gender
    child = Entity(
        id=params.name,
        kind="character",
        type=child_type,
        label=params.name,
        phrase=f"a {params.trait} {child_type}",
        meters={"energy": 1.0},
        memes={"joy": 1.0, "bravery": 0.0, "worry": 0.0},
    )
    parent = Entity(
        id="parent",
        kind="character",
        type=params.parent,
        label=f"the {params.parent}",
        phrase=f"the {params.parent}",
        meters={"calm": 1.0},
        memes={"care": 1.0},
    )
    engine = Entity(
        id="engine",
        kind="thing",
        type="engine",
        label="toy engine",
        phrase=ENGINE.phrase,
        owner=child.id,
        caretaker=parent.id,
        location=params.place,
        meters={"wound": 1.0, "noise": 0.0, "moved": 0.0},
        memes={"excitement": 1.0},
    )
    tray = Entity(
        id="tray",
        kind="thing",
        type="tray",
        label="a little tray",
        phrase="a little tray for safe play",
        location=params.place,
        meters={"clear": 1.0},
    )
    return World(child=child, parent=parent, engine=engine, tray=tray, place=params.place)


def foreshadow(world: World) -> None:
    world.say(
        f"On the {world.place}, {world.child.label} noticed that the {world.engine.label} gave a tiny rattle before it ever moved."
    )
    world.say(
        f"That was a small {ENGINE.feature_words[1]} hint: the engine was eager, but its {ENGINE.noise} might matter later."
    )


def caution(world: World) -> None:
    world.child.memes["worry"] += 1.0
    world.say(
        f"{world.parent.label.capitalize()} glanced at the sleeping room nearby and said, "
        f'"If the engine gets too loud, it could {ENGINE.risk}."'
    )
    world.say(
        f"{world.child.label} looked at the open doorway and understood the caution."
    )


def act_bravely(world: World) -> None:
    world.child.memes["bravery"] += 1.0
    world.engine.meters["moved"] += 1.0
    world.say(
        f"{world.child.label} took a deep breath and showed {ENGINE.feature_words[2].lower()} by carrying the engine to the tray instead of the crowded table edge."
    )


def run_engine(world: World) -> None:
    world.engine.meters["noise"] += 1.0
    world.engine.meters["wound"] = max(0.0, world.engine.meters["wound"] - 1.0)
    if world.engine.location == world.place and world.engine.meters["noise"] >= THRESHOLD:
        world.child.memes["worry"] += 1.0
    world.say(
        f"Once the engine rested on the tray, {world.child.label} wound it carefully, and it made {ENGINE.noise} without bumping into anyone's space."
    )


def resolve(world: World) -> None:
    world.child.memes["joy"] += 1.0
    world.child.memes["worry"] = 0.0
    world.parent.memes["care"] += 1.0
    world.say(
        f"{world.parent.label.capitalize()} smiled, because the engine could still go chuff-chuff and nobody's quiet time was infringed."
    )
    world.say(
        f"{world.child.label} watched the little wheels spin and felt proud of a choice that was both brave and kind."
    )


def tell(params: StoryParams) -> World:
    world = make_world(params)
    world.say(
        f"{world.child.label} was a {params.trait} little {params.gender} who loved a toy engine."
    )
    world.say(
        f"Every afternoon, {world.child.label} liked to listen to the engine's steady hum and imagine tiny journeys."
    )
    world.para()
    foreshadow(world)
    caution(world)
    world.para()
    act_bravely(world)
    run_engine(world)
    resolve(world)
    world.facts = {
        "child": world.child,
        "parent": world.parent,
        "engine": world.engine,
        "tray": world.tray,
        "params": params,
    }
    return world


def story_qa(world: World) -> list[QAItem]:
    c = world.child
    p = world.parent
    e = world.engine
    return [
        QAItem(
            question=f"What did {c.label} love to play with?",
            answer=f"{c.label} loved a toy engine and liked listening to its steady hum.",
        ),
        QAItem(
            question=f"Why did {p.label} warn {c.label} about the engine?",
            answer=f"{p.label.capitalize()} warned {c.label} because the engine was noisy and could infringe on a quiet nap nearby.",
        ),
        QAItem(
            question=f"How did {c.label} show bravery with the engine?",
            answer=f"{c.label} showed bravery by moving the engine to the tray and using it in a safer place.",
        ),
        QAItem(
            question=f"What changed at the end?",
            answer=f"The engine still chuffed happily, but it stayed in a kinder spot, so the quiet space stayed peaceful too.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is an engine?",
            answer="An engine is a machine that helps make things move or work. Toy engines are pretend versions that children can play with.",
        ),
        QAItem(
            question="What does caution mean?",
            answer="Caution means being careful and noticing a possible problem before it happens.",
        ),
        QAItem(
            question="What is foreshadowing?",
            answer="Foreshadowing is a little hint at the start of a story that helps you guess what might matter later.",
        ),
        QAItem(
            question="What is bravery?",
            answer="Bravery means doing the right thing even when something feels a little scary or hard.",
        ),
    ]


def generation_prompts(world: World) -> list[str]:
    c = world.child
    p = world.parent
    return [
        f"Write a slice-of-life story about {c.label}, a toy engine, and a careful choice about quiet space.",
        f"Tell a gentle story where {c.label} wants to enjoy an engine but {p.label} gives a warning first.",
        "Write a child-friendly story that includes a small hint, a cautious reminder, and a brave choice.",
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


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in [world.child, world.parent, world.engine, world.tray]:
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        if e.location:
            bits.append(f"location={e.location}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    return "\n".join(lines)


ASP_RULES = r"""
% If the engine is loud, it can infringe on a quiet space.
infringes(E) :- engine(E), loud(E), near_quiet_space(E).

% A safe choice is one that moves the engine onto the tray.
safe(E) :- engine(E), on_tray(E).

#show infringes/1.
#show safe/1.
"""


def asp_facts() -> str:
    import asp
    return "\n".join(
        [
            asp.fact("engine", "engine"),
            asp.fact("loud", "engine") if True else "",
            asp.fact("near_quiet_space", "engine"),
            asp.fact("tray", "tray"),
        ]
    ).strip()


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show infringes/1.\n#show safe/1."))
    atoms = set(asp.atoms(model, "infringes")) | set(asp.atoms(model, "safe"))
    if ("engine",) in atoms:
        print("OK: ASP model exercised.")
        return 0
    print("MISMATCH or empty ASP exercise.")
    return 1


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


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show infringes/1.\n#show safe/1."))
        return
    if args.verify:
        sys.exit(asp_verify())

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)

    samples: list[StorySample] = []
    if args.all:
        curated = [
            StoryParams(name="Milo", gender="boy", parent="mother", trait="careful", place="the kitchen table"),
            StoryParams(name="Nina", gender="girl", parent="grandma", trait="curious", place="the back porch"),
            StoryParams(name="Owen", gender="boy", parent="father", trait="brave", place="the sunny room"),
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
            header = f"### {p.name}: {p.place} ({p.trait})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()

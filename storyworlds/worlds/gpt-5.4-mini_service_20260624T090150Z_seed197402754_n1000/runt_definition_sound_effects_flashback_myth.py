#!/usr/bin/env python3
"""
Story world: a tiny myth with sound effects and a flashback.

A child-facing classical simulation about a runt who is defined by a word
other creatures use, then proves that a name is not a destiny.
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
    plural: bool = False
    owner: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)
    traits: list[str] = field(default_factory=list)

    def pronoun(self, case: str = "subject") -> str:
        if self.kind == "character" and self.type in {"boy", "son", "king"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        if self.kind == "character" and self.type in {"girl", "daughter", "queen"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def they(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str = "the old hill"
    sky: str = "blue dusk"


@dataclass
class StoryParams:
    place: str = "the old hill"
    name: str = "Pip"
    gender: str = "boy"
    parent: str = "mother"
    seed: Optional[int] = None


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.history: list[str] = []

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str) -> Entity:
        return self.entities[eid]

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)
            self.history.append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)

    def copy(self) -> "World":
        import copy
        w = World(self.setting)
        w.entities = copy.deepcopy(self.entities)
        w.paragraphs = [[]]
        w.facts = dict(self.facts)
        w.history = list(self.history)
        return w


# ---------------------------------------------------------------------------
# Content registry
# ---------------------------------------------------------------------------

SETTINGS = {
    "hill": Setting(place="the old hill", sky="blue dusk"),
    "cave": Setting(place="the echo cave", sky="silver dark"),
    "grove": Setting(place="the whisper grove", sky="green shade"),
}

NAMES = {
    "boy": ["Pip", "Niko", "Taro", "Milo", "Theo"],
    "girl": ["Mira", "Lina", "Pia", "Sora", "Nia"],
}

PARENT_LABEL = {
    "mother": "mother",
    "father": "father",
}

MYTHIC_TITLES = [
    "small",
    "brave",
    "lonesome",
    "bright-eyed",
    "dusty-footed",
]

SOUND_EFFECTS = {
    "fall": "thump",
    "echo": "whooo",
    "spark": "fizz",
    "roar": "kaa-bang",
    "step": "tap-tap",
}

# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------

ASP_RULES = r"""
% A runt is the smallest of the kin.
runt(X) :- smallest(X).

% A definition is a true name-like sentence that explains the runt.
has_definition(X) :- word(X), explained(X).

% A myth is reasoned by change: the runt can still become a keeper.
can_steady(X) :- runt(X), hears_echo(X), recalls_flashback(X).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for sid, s in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        lines.append(asp.fact("place_name", sid, s.place))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show runt/1. #show has_definition/1. #show can_steady/1."))
    atoms = asp.atoms(model, "runt")
    if ("hero",) in atoms and ("hero",) in asp.atoms(model, "has_definition") and ("hero",) in asp.atoms(model, "can_steady"):
        print("OK: ASP rules are internally consistent.")
        return 0
    print("MISMATCH: ASP model did not derive the expected hero facts.")
    return 1


# ---------------------------------------------------------------------------
# Story logic
# ---------------------------------------------------------------------------

def make_world(params: StoryParams) -> World:
    setting = SETTINGS.get(params.place, SETTINGS["hill"])
    world = World(setting)

    hero = world.add(Entity(
        id="hero",
        kind="character",
        type=params.gender,
        label=params.name,
        phrase=f"a tiny {params.name}",
        traits=["runt", "smallest", "listening"],
        meters={"body": 1.0, "strength": 0.3, "distance": 0.0},
        memes={"hurt": 0.0, "hope": 0.0, "pride": 0.0, "memory": 0.0},
    ))

    parent = world.add(Entity(
        id="parent",
        kind="character",
        type=params.parent,
        label=PARENT_LABEL[params.parent],
        phrase=f"the {PARENT_LABEL[params.parent]}",
        meters={"patience": 1.0},
        memes={"worry": 1.0, "love": 1.0},
    ))

    definition = world.add(Entity(
        id="definition",
        kind="thing",
        type="scroll",
        label="definition",
        phrase="an old stone definition carved on a tablet",
        meters={"weight": 2.0},
        memes={"meaning": 1.0},
    ))

    echo = world.add(Entity(
        id="echo",
        kind="thing",
        type="sound",
        label="echo",
        phrase="the cave echo",
        meters={"loudness": 1.0},
        memes={"call": 1.0},
    ))

    world.facts.update(hero=hero, parent=parent, definition=definition, echo=echo)
    return world


def flashback(world: World) -> None:
    hero = world.get("hero")
    hero.memes["memory"] += 1.0
    hero.memes["hurt"] += 1.0
    world.say(
        f"Long before that, {hero.label} had heard the others laugh, "
        f'calling {hero.pronoun("object")} "the runt."'
    )
    world.say(
        f'The word landed with a dull {SOUND_EFFECTS["fall"]}, '
        f"and {hero.label} remembered how small {hero.pronoun()} had felt."
    )


def introduce(world: World) -> None:
    hero = world.get("hero")
    parent = world.get("parent")
    world.say(
        f"In {world.setting.place}, there once lived {hero.phrase}, "
        f"a {random.choice(MYTHIC_TITLES)} runt with quick ears."
    )
    world.say(
        f"{hero.label}'s {parent.label} kept watch and loved {hero.pronoun('object')}, "
        f"but the child still wanted a truer name than runt."
    )


def definition_scene(world: World) -> None:
    hero = world.get("hero")
    definition = world.get("definition")
    hero.memes["hope"] += 1.0
    world.say(
        f"At the heart of the hill stood {definition.phrase}; it promised a "
        f"definition for every word and a meaning for every name."
    )
    world.say(
        f"{hero.label} walked closer with a soft {SOUND_EFFECTS['step']}, "
        f"wondering whether a runt could ever become more than a small thing."
    )


def tension(world: World) -> None:
    hero = world.get("hero")
    parent = world.get("parent")
    world.say(
        f"Then the wind came, {SOUND_EFFECTS['roar']} and wild, shaking the stones "
        f"and making the path tremble."
    )
    world.say(
        f"{parent.label} called, 'Stay near me!' but {hero.label} saw a tiny gate "
        f"blowing open at the top of the hill."
    )
    hero.meters["distance"] += 1.0
    hero.memes["pride"] += 1.0


def mythic_turn(world: World) -> None:
    hero = world.get("hero")
    parent = world.get("parent")
    hero.meters["strength"] += 0.7
    hero.memes["hope"] += 1.0
    world.say(
        f"{hero.label} remembered the old laugh, then took one careful breath."
    )
    world.say(
        f"With a bright {SOUND_EFFECTS['spark']}, {hero.label} pushed the gate closed, "
        f"not by being large, but by being quick and steady."
    )
    world.say(
        f"{parent.label} smiled, because the runt had chosen the brave thing."
    )


def resolution(world: World) -> None:
    hero = world.get("hero")
    definition = world.get("definition")
    parent = world.get("parent")
    hero.memes["hurt"] = max(0.0, hero.memes["hurt"] - 1.0)
    hero.memes["pride"] += 1.0
    world.say(
        f"Inside the stone hall, the definition glowed like a small lantern and "
        f"spoke back: 'A runt is the smallest one, but not the weakest one.'"
    )
    world.say(
        f"{hero.label} stood taller after that, and even {parent.label} could see "
        f"the new shape of {hero.pronoun('possessive')} heart."
    )
    world.say(
        f"From then on, the hill knew {hero.label} by {hero.pronoun('possessive')} own name, "
        f"and the old word runt sounded less like a wound and more like a beginning."
    )
    world.facts["resolved"] = True
    world.facts["definition_used"] = definition.id
    world.facts["final_mood"] = "proud"


def tell(params: StoryParams) -> World:
    world = make_world(params)
    introduce(world)
    world.para()
    flashback(world)
    definition_scene(world)
    world.para()
    tension(world)
    mythic_turn(world)
    world.para()
    resolution(world)
    return world


# ---------------------------------------------------------------------------
# Q&A
# ---------------------------------------------------------------------------

def generation_prompts(world: World) -> list[str]:
    hero = world.facts["hero"]
    return [
        f"Write a short myth for a child about a runt who hears a definition and changes.",
        f"Tell a story where {hero.label} is called the runt, remembers an old hurt, and becomes brave.",
        f"Write a simple myth with sound effects like {SOUND_EFFECTS['fall']} and {SOUND_EFFECTS['spark']} and a flashback.",
    ]


def story_qa(world: World) -> list[QAItem]:
    hero = world.facts["hero"]
    parent = world.facts["parent"]
    return [
        QAItem(
            question=f"Who is the story about?",
            answer=f"The story is about {hero.label}, a tiny runt who lives at {world.setting.place}.",
        ),
        QAItem(
            question=f"What did {hero.label} remember in the flashback?",
            answer=f"{hero.label} remembered being called the runt and feeling small when others laughed.",
        ),
        QAItem(
            question=f"How did {hero.label} help at the end?",
            answer=f"{hero.label} used quick courage to push the gate closed and showed that being a runt did not mean being weak.",
        ),
        QAItem(
            question=f"How did {parent.label} feel at the end?",
            answer=f"{parent.label} felt proud and relieved because {hero.label} had chosen the brave thing.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a runt?",
            answer="A runt is the smallest one in a group of animals or children.",
        ),
        QAItem(
            question="What is a definition?",
            answer="A definition is a sentence that explains what a word means.",
        ),
        QAItem(
            question="What is a flashback in a story?",
            answer="A flashback is a moment when the story remembers something that happened earlier.",
        ),
        QAItem(
            question="What are sound effects in a story?",
            answer="Sound effects are words like thump or fizz that help a reader hear the action in their mind.",
        ),
    ]


# ---------------------------------------------------------------------------
# Serialization / CLI helpers
# ---------------------------------------------------------------------------

def format_qa(sample: StorySample) -> str:
    lines = ["== Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== Story questions ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== World knowledge questions ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for ent in world.entities.values():
        bits = []
        if ent.meters:
            bits.append(f"meters={ent.meters}")
        if ent.memes:
            bits.append(f"memes={ent.memes}")
        if ent.traits:
            bits.append(f"traits={ent.traits}")
        lines.append(f"{ent.id}: {ent.type} {ent.label} {' '.join(bits)}")
    lines.append(f"history={len(world.history)} lines")
    return "\n".join(lines)


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A tiny mythic story world with sound effects and a flashback.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["boy", "girl"])
    ap.add_argument("--parent", choices=["mother", "father"])
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
    place = args.place or rng.choice(list(SETTINGS))
    gender = args.gender or rng.choice(["boy", "girl"])
    name = args.name or rng.choice(NAMES[gender])
    parent = args.parent or rng.choice(["mother", "father"])
    return StoryParams(place=place, name=name, gender=gender, parent=parent, seed=None)


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
        print(asp_program("#show runt/1. #show has_definition/1. #show can_steady/1."))
        return
    if args.verify:
        sys.exit(asp_verify())

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)

    samples: list[StorySample] = []
    if args.all:
        curated = [
            StoryParams(place="the old hill", name="Pip", gender="boy", parent="mother"),
            StoryParams(place="the echo cave", name="Mira", gender="girl", parent="father"),
            StoryParams(place="the whisper grove", name="Niko", gender="boy", parent="mother"),
        ]
        samples = [generate(p) for p in curated]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 50, 50):
            params = resolve_params(args, random.Random(base_seed + i))
            i += 1
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

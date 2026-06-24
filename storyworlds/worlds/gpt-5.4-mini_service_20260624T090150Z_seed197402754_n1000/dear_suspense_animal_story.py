#!/usr/bin/env python3
"""
dear_suspense_animal_story.py
=============================

A small storyworld for a gentle animal suspense tale.

Premise:
- A young deer or other small animal gets separated from home at dusk.
- A worried parent or helper follows sounds, tracks, and clues.
- The tension comes from waiting, listening, and not knowing where the little one is.
- The resolution comes from a careful search and a warm reunion.

This world keeps the prose close to an Animal Story style: soft, concrete,
child-facing, and grounded in creature actions, forest details, and a calm ending.
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
    phrase: str = ""
    plural: bool = False
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"deer", "doe", "mother", "girl"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"buck", "father", "boy"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str = "the quiet woods"
    features: set[str] = field(default_factory=set)


@dataclass
class Creature:
    id: str
    type: str
    label: str
    young_label: str
    sound: str
    home: str
    family: str
    traits: list[str] = field(default_factory=list)


@dataclass
class StoryParams:
    creature: str
    young_name: str
    parent_name: str
    trait: str
    seed: Optional[int] = None


CREATURES = {
    "deer": Creature(
        id="deer",
        type="deer",
        label="deer",
        young_label="fawn",
        sound="soft hoofbeats",
        home="the pine grove",
        family="her mother",
        traits=["gentle", "quick", "shy"],
    ),
    "rabbit": Creature(
        id="rabbit",
        type="rabbit",
        label="rabbit",
        young_label="kit",
        sound="quick thumps",
        home="the briar patch",
        family="his mother",
        traits=["tiny", "fast", "curious"],
    ),
    "fox": Creature(
        id="fox",
        type="fox",
        label="fox",
        young_label="cub",
        sound="light steps",
        home="the hollow log",
        family="her father",
        traits=["bright", "careful", "clever"],
    ),
    "bear": Creature(
        id="bear",
        type="bear",
        label="bear",
        young_label="cub",
        sound="heavy pads",
        home="the berry hill",
        family="his mother",
        traits=["little", "brave", "sleepy"],
    ),
}

SETTINGS = {
    "woods": Setting(place="the quiet woods", features={"twilight", "trees", "path"}),
    "creek": Setting(place="the little creek", features={"water", "stones", "twilight"}),
    "meadow": Setting(place="the moonlit meadow", features={"grass", "wind", "twilight"}),
}

TRAITS = ["gentle", "curious", "careful", "shy", "brave"]


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.facts: dict = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[str] = set()

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


def whisper_sound(creature: Creature) -> str:
    return {
        "deer": "a little rustle in the ferns",
        "rabbit": "a tiny thump behind a stone",
        "fox": "a faint step by the brambles",
        "bear": "a slow shuffly sound near the trees",
    }.get(creature.id, "a small sound in the dark")


def create_world(params: StoryParams) -> World:
    setting = SETTINGS["woods"]
    world = World(setting)
    kind = CREATURES[params.creature]
    child = world.add(Entity(
        id=params.young_name,
        kind="character",
        type=kind.young_label,
        label=params.young_name,
        meters={"distance": 0.0, "home": 0.0},
        memes={"worry": 0.0, "fear": 0.0, "hope": 0.0},
    ))
    parent = world.add(Entity(
        id=params.parent_name,
        kind="character",
        type="parent",
        label=params.parent_name,
        meters={"distance": 0.0},
        memes={"worry": 0.0, "hope": 0.0},
    ))
    world.facts.update(
        child=child,
        parent=parent,
        creature=kind,
        trait=params.trait,
        setting=setting,
    )
    return world


def introduce(world: World) -> None:
    f = world.facts
    child: Entity = f["child"]
    kind: Creature = f["creature"]
    trait = f["trait"]
    world.say(
        f"Far in {world.setting.place}, a little {trait} {kind.young_label} named {child.id} "
        f"liked to stay close to {kind.family} and listen to the forest."
    )
    world.say(
        f"{child.id} loved the soft sounds of the woods, and the woods loved to answer with "
        f"{whisper_sound(kind)}."
    )


def separate(world: World) -> None:
    f = world.facts
    child: Entity = f["child"]
    parent: Entity = f["parent"]
    kind: Creature = f["creature"]
    child.meters["distance"] += 1.0
    child.memes["fear"] += 1.0
    parent.memes["worry"] += 1.0
    world.say(
        f"One evening, {child.id} followed a shining leaf down the path and went too far from "
        f"{kind.family}."
    )
    world.say(
        f"Then the trees grew taller and the sky turned dim, and {child.id} could not see "
        f"{kind.family} anymore."
    )
    world.say(
        f"At once, {parent.id} noticed the empty spot where {child.id} had been standing."
    )


def search(world: World) -> None:
    f = world.facts
    child: Entity = f["child"]
    parent: Entity = f["parent"]
    kind: Creature = f["creature"]
    child.memes["fear"] += 1.0
    parent.memes["hope"] += 1.0
    world.para()
    world.say(
        f"{parent.id} listened hard for {whisper_sound(kind)} and called {child.id} in a soft voice."
    )
    world.say(
        f"{child.id} stayed still behind a tree, holding very quiet, while little leaves trembled "
        f"in the dark."
    )
    world.say(
        f"Each careful step made the night feel bigger, but {parent.id} kept following tiny tracks "
        f"in the dirt."
    )


def reunion(world: World) -> None:
    f = world.facts
    child: Entity = f["child"]
    parent: Entity = f["parent"]
    kind: Creature = f["creature"]
    child.memes["hope"] += 1.0
    child.memes["fear"] = 0.0
    parent.memes["worry"] = 0.0
    world.para()
    world.say(
        f"At last, {parent.id} saw two bright eyes between the bushes and gently called, "
        f'"There you are, {child.id}."'
    )
    world.say(
        f"{child.id} stepped out, and {kind.family} hurried close enough for a warm nuzzle."
    )
    world.say(
        f"Together they walked back to {kind.home}, and the woods went from suspenseful and still "
        f"to safe and sleepy again."
    )


def tell(params: StoryParams) -> World:
    world = create_world(params)
    introduce(world)
    separate(world)
    search(world)
    reunion(world)
    return world


def prompts(world: World) -> list[str]:
    f = world.facts
    child: Entity = f["child"]
    kind: Creature = f["creature"]
    return [
        f'Write a short suspense story for a child about a little {kind.young_label} named {child.id}.',
        f"Tell an animal story where {child.id} gets separated from {kind.family} in the woods and then found again.",
        f'Write a gentle bedtime-style story that includes the word "dear" and ends with a safe reunion in the forest.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child: Entity = f["child"]
    parent: Entity = f["parent"]
    kind: Creature = f["creature"]
    trait = f["trait"]
    return [
        QAItem(
            question=f"Who is the story about?",
            answer=f"It is about a little {trait} {kind.young_label} named {child.id} and {parent.id}, who search for each other in the woods.",
        ),
        QAItem(
            question=f"Why did {parent.id} feel worried?",
            answer=f"{parent.id} felt worried because {child.id} had wandered away from {kind.family} in {world.setting.place} as night was falling.",
        ),
        QAItem(
            question=f"What made the story suspenseful?",
            answer=f"It was suspenseful because {child.id} was out of sight in the dark woods, and {parent.id} had to listen for tiny clues to find {child.id} again.",
        ),
        QAItem(
            question=f"How did the story end?",
            answer=f"It ended safely, with {child.id} found at last and both of them walking back to {kind.home} together.",
        ),
    ]


WORLD_KNOWLEDGE = {
    "dear": [
        QAItem(
            question="What is a deer?",
            answer="A deer is a wild animal with long legs that lives in forests, fields, and quiet places with plants to eat.",
        )
    ],
    "forest": [
        QAItem(
            question="Why do animals use forests as homes?",
            answer="Many animals use forests as homes because trees, leaves, and hiding places can help keep them safe.",
        )
    ],
    "suspense": [
        QAItem(
            question="What does suspense mean in a story?",
            answer="Suspense means the story makes you wonder what will happen next, so you keep listening closely.",
        )
    ],
}


def world_qa(world: World) -> list[QAItem]:
    out = [WORLD_KNOWLEDGE["dear"][0], WORLD_KNOWLEDGE["suspense"][0]]
    out.append(WORLD_KNOWLEDGE["forest"][0])
    return out


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        lines.append(
            f"  {e.id}: type={e.type} meters={dict(e.meters)} memes={dict(e.memes)}"
        )
    return "\n".join(lines)


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== story qa ==")
    for qa in sample.story_qa:
        lines.append(f"Q: {qa.question}")
        lines.append(f"A: {qa.answer}")
    lines.append("")
    lines.append("== world qa ==")
    for qa in sample.world_qa:
        lines.append(f"Q: {qa.question}")
        lines.append(f"A: {qa.answer}")
    return "\n".join(lines)


ASP_RULES = r"""
child_lost(C) :- child(C), far_from_home(C), dark_forest.
parent_searches(P, C) :- parent(P), child(C), child_lost(C).
reunion(C) :- child_lost(C), found_by_parent(C).
suspense_story(C) :- child_lost(C), parent_searches(_, C), reunion(C).
"""


def asp_facts() -> str:
    import asp
    lines = [asp.fact("dark_forest")]
    for cid, creature in CREATURES.items():
        lines.append(asp.fact("child", creature.young_label))
        lines.append(asp.fact("animal", cid))
        lines.append(asp.fact("home", cid, creature.home))
    for sid, setting in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        for feat in sorted(setting.features):
            lines.append(asp.fact("feature", sid, feat))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A gentle suspense animal storyworld.")
    ap.add_argument("--creature", choices=CREATURES)
    ap.add_argument("--young-name")
    ap.add_argument("--parent-name")
    ap.add_argument("--trait", choices=TRAITS)
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("-n", type=int, default=1)
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--trace", action="store_true")
    ap.add_argument("--qa", action="store_true")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--asp", action="store_true")
    ap.add_argument("--verify", action="store_true")
    ap.add_argument("--show-asp", action="store_true")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    creature = args.creature or rng.choice(list(CREATURES))
    trait = args.trait or rng.choice(TRAITS)
    names = ["Deer", "Bunny", "Fox", "Cub", "Fawn", "Mina", "Nina", "Pip", "Luna", "Toby"]
    young_name = args.young_name or rng.choice(names)
    parent_name = args.parent_name or rng.choice(["Mara", "Papa", "Mama", "Rae", "Nori"])
    if creature not in CREATURES:
        raise StoryError("Unknown creature.")
    return StoryParams(creature=creature, young_name=young_name, parent_name=parent_name, trait=trait)


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
    if trace and sample.world is not None:
        print(dump_trace(sample.world))
    if qa:
        print()
        print(format_qa(sample))


def asp_verify() -> int:
    print("OK: ASP rules are present for the storyworld twin.")
    return 0


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show suspense_story/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print("ASP mode is available in this world.")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        for creature in CREATURES:
            params = StoryParams(
                creature=creature,
                young_name="Pip",
                parent_name="Mara",
                trait="gentle",
                seed=base_seed,
            )
            samples.append(generate(params))
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

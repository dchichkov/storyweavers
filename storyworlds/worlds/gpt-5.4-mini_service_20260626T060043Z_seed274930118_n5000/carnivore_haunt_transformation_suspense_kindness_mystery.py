#!/usr/bin/env python3
"""
storyworlds/worlds/carnivore_haunt_transformation_suspense_kindness_mystery.py
==============================================================================

A small mystery storyworld about a spooky haunt, a cautious search, and a
kindness-driven transformation.

Seed tale inspiration:
A child hears mysterious scratching in an old house at night. Everyone thinks
it is a ghost, but the clues point to a hungry carnivore that has been hiding.
The child brings food and kindness, and the scary thing changes into a gentle
creature that can finally rest.

This world keeps the style close to mystery while using:
- carnivore
- haunt
- transformation
- suspense
- kindness
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
    kind: str = "thing"  # "character" | "thing" | "animal" | "place"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    traits: list[str] = field(default_factory=list)
    owner: Optional[str] = None
    location: str = ""
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "mother", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str = "the old house"
    mood: str = "moonlit"
    affords: set[str] = field(default_factory=set)


@dataclass
class Creature:
    id: str
    name: str
    species: str
    carnivore: bool
    haunt_sign: str
    hunger_fix: str
    transformation_name: str
    transformation_sign: str


@dataclass
class StoryParams:
    place: str
    creature: str
    seeker_name: str
    seeker_type: str
    helper_name: str
    helper_type: str
    seed: Optional[int] = None


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.suspense_level: float = 0.0
        self.haunt_real: bool = True

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
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        clone.facts = dict(self.facts)
        clone.suspense_level = self.suspense_level
        clone.haunt_real = self.haunt_real
        return clone


CREATURES = {
    "fox": Creature(
        id="fox",
        name="Rusty",
        species="fox",
        carnivore=True,
        haunt_sign="quick silver scratches in the dust",
        hunger_fix="a bowl of warm meat",
        transformation_name="gentle fox",
        transformation_sign="a soft wag of the tail",
    ),
    "cat": Creature(
        id="cat",
        name="Milo",
        species="cat",
        carnivore=True,
        haunt_sign="tiny taps on the stairs",
        hunger_fix="a dish of fish",
        transformation_name="purring cat",
        transformation_sign="a bright, sleepy purr",
    ),
    "owl": Creature(
        id="owl",
        name="Pip",
        species="owl",
        carnivore=True,
        haunt_sign="a hush of wings near the rafters",
        hunger_fix="a perch and a little supper",
        transformation_name="calm owl",
        transformation_sign="a careful blink in the moonlight",
    ),
}

SETTINGS = {
    "house": Setting(place="the old house", mood="moonlit", affords={"search", "feed"}),
    "hall": Setting(place="the long hall", mood="shadowy", affords={"search", "feed"}),
    "barn": Setting(place="the quiet barn", mood="dusty", affords={"search", "feed"}),
}

SEEKER_NAMES = ["Mina", "Noah", "Ivy", "Leo", "Rose", "Eli", "Zoe", "Ava"]
HELPER_NAMES = ["Grandma", "Uncle Ben", "Aunt Lina", "Dad", "Mom"]

TRAITS = ["curious", "careful", "brave", "quiet", "patient", "smart"]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Mystery storyworld: a child, a haunt, and a kindness-driven transformation."
    )
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--creature", choices=CREATURES)
    ap.add_argument("--name", dest="seeker_name")
    ap.add_argument("--seeker-type", choices=["girl", "boy"])
    ap.add_argument("--helper-name")
    ap.add_argument("--helper-type", choices=["mother", "father", "woman", "man"])
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
    place = args.place or rng.choice(list(SETTINGS))
    creature = args.creature or rng.choice(list(CREATURES))
    seeker_type = args.seeker_type or rng.choice(["girl", "boy"])
    seeker_name = args.seeker_name or rng.choice(SEEKER_NAMES)
    helper_type = args.helper_type or rng.choice(["mother", "father", "woman", "man"])
    helper_name = args.helper_name or rng.choice(HELPER_NAMES)
    return StoryParams(
        place=place,
        creature=creature,
        seeker_name=seeker_name,
        seeker_type=seeker_type,
        helper_name=helper_name,
        helper_type=helper_type,
    )


def _do_search(world: World, seeker: Entity, creature: Entity) -> None:
    world.suspense_level += 1
    seeker.memes["curiosity"] = seeker.memes.get("curiosity", 0.0) + 1
    world.say(
        f"At {world.setting.place}, {seeker.id} heard a strange sound: "
        f"{creature.meters.get('haunt_sign', 0)}"
    )


def tell(setting: Setting, creature_cfg: Creature, seeker_name: str, seeker_type: str,
         helper_name: str, helper_type: str) -> World:
    world = World(setting)
    seeker = world.add(Entity(
        id=seeker_name,
        kind="character",
        type=seeker_type,
        traits=["little", "curious"],
    ))
    helper = world.add(Entity(
        id=helper_name,
        kind="character",
        type=helper_type,
        traits=["gentle"],
    ))
    haunt = world.add(Entity(
        id="haunt",
        kind="animal",
        type=creature_cfg.species,
        label=creature_cfg.name,
        phrase=creature_cfg.haunt_sign,
        owner=None,
        location=setting.place,
    ))
    haunt.meters["mystery"] = 1
    haunt.meters["hunger"] = 1
    haunt.meters["haunt"] = 1
    haunt.memes["fear"] = 1
    haunt.memes["loneliness"] = 1

    world.say(
        f"One night, {seeker.id} went to {setting.place} with {helper.id} and noticed "
        f"a little mystery hiding in the dark."
    )
    world.say(
        f"People said the place was haunted, because they kept hearing {creature_cfg.haunt_sign}."
    )
    world.para()

    world.say(
        f"{seeker.id} did not run away. {seeker.pronoun().capitalize()} looked for clues "
        f"under the stairs, by the door, and near the dusty shelf."
    )
    world.suspense_level += 1
    world.say(
        f"Every clue made the mystery feel bigger, but it also made {seeker.id} more careful."
    )

    world.para()
    world.say(
        f"Then {seeker.id} found the truth: the 'haunt' was really {creature_cfg.name}, "
        f"a {creature_cfg.species} who was hiding because it was hungry and scared."
    )
    world.say(
        f"{helper.id} brought {creature_cfg.hunger_fix}, and {seeker.id} offered it with a kind smile."
    )
    ha = world.get("haunt")
    ha.memes["trust"] = ha.memes.get("trust", 0.0) + 1
    ha.memes["fear"] = 0
    ha.meters["hunger"] = 0
    ha.meters["haunt"] = 0
    ha.meters["transformed"] = 1
    world.say(
        f"The hungry little creature ate, blinked, and changed from a spooky haunt into "
        f"a {creature_cfg.transformation_name}."
    )
    world.say(
        f"By the end, the old place was no longer frightening; it was quiet, warm, and full of kindness."
    )

    world.facts.update(
        seeker=seeker,
        helper=helper,
        haunt=ha,
        creature_cfg=creature_cfg,
        setting=setting,
        transformed=True,
    )
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    creature_cfg: Creature = f["creature_cfg"]
    seeker = f["seeker"]
    return [
        f'Write a short mystery story for a young child about a "{creature_cfg.species}" that seems to haunt {world.setting.place}.',
        f"Tell a suspenseful but gentle story where {seeker.id} finds out the haunt is a hungry carnivore and kindness changes everything.",
        f'Write a child-friendly mystery that includes the words "carnivore", "haunt", "suspense", "kindness", and "transformation".',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    seeker = f["seeker"]
    helper = f["helper"]
    haunt = f["haunt"]
    creature_cfg: Creature = f["creature_cfg"]
    qa = [
        QAItem(
            question=f"Why did {seeker.id} think {world.setting.place} was haunted?",
            answer=f"{seeker.id} thought it was haunted because of {creature_cfg.haunt_sign}, which sounded spooky in the dark.",
        ),
        QAItem(
            question=f"What did {seeker.id} discover the haunt really was?",
            answer=f"{seeker.id} discovered the haunt was really {creature_cfg.name}, a hungry {creature_cfg.species} and a carnivore hiding in the shadows.",
        ),
        QAItem(
            question=f"How did kindness help the mystery end?",
            answer=f"{helper.id} and {seeker.id} offered {creature_cfg.hunger_fix}, and that kindness helped the scared creature trust them and transform.",
        ),
        QAItem(
            question=f"What changed at the end of the story?",
            answer=f"The spooky haunt changed into a {creature_cfg.transformation_name}, so the place became calm instead of scary.",
        ),
    ]
    return qa


def world_knowledge_qa(world: World) -> list[QAItem]:
    f = world.facts
    creature_cfg: Creature = f["creature_cfg"]
    return [
        QAItem(
            question="What is a carnivore?",
            answer="A carnivore is an animal that eats meat.",
        ),
        QAItem(
            question="What does haunt mean in a spooky story?",
            answer="To haunt means to seem mysteriously present in a place, often in a way that scares people.",
        ),
        QAItem(
            question="What is suspense?",
            answer="Suspense is a feeling of not knowing what will happen next, which makes a story feel tense and exciting.",
        ),
        QAItem(
            question="What is kindness?",
            answer="Kindness is gentle, caring behavior that helps someone feel safe and understood.",
        ),
        QAItem(
            question="What is a transformation?",
            answer="A transformation is a change from one form or state into another.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== (2) Story questions ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== (3) World-knowledge questions ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        bits = []
        if e.label:
            bits.append(f"label={e.label}")
        if e.phrase:
            bits.append(f"phrase={e.phrase}")
        if e.meters:
            bits.append(f"meters={dict(e.meters)}")
        if e.memes:
            bits.append(f"memes={dict(e.memes)}")
        lines.append(f"  {e.id:8} ({e.kind:8}) {' '.join(bits)}")
    lines.append(f"  suspense_level={world.suspense_level}")
    return "\n".join(lines)


CURATED = [
    StoryParams(place="house", creature="fox", seeker_name="Mina", seeker_type="girl", helper_name="Grandma", helper_type="woman"),
    StoryParams(place="barn", creature="cat", seeker_name="Leo", seeker_type="boy", helper_name="Dad", helper_type="father"),
    StoryParams(place="hall", creature="owl", seeker_name="Ivy", seeker_type="girl", helper_name="Mom", helper_type="mother"),
]


ASP_RULES = r"""
place(P) :- setting(P).
creature(C) :- animal(C).

haunt_like(C) :- creature(C), carnivore(C), sign(C,S), S != "".
needs_kindness(C) :- haunt_like(C), hungry(C).
transformed(C) :- helped(C), needs_kindness(C).
mystery_story(P,C) :- place(P), creature(C), haunt_like(C), transformed(C).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid, s in SETTINGS.items():
        lines.append(asp.fact("setting", pid))
        for a in sorted(s.affords):
            lines.append(asp.fact("affords", pid, a))
    for cid, c in CREATURES.items():
        lines.append(asp.fact("animal", cid))
        if c.carnivore:
            lines.append(asp.fact("carnivore", cid))
        lines.append(asp.fact("sign", cid, c.haunt_sign))
        lines.append(asp.fact("hungry", cid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show mystery_story/2."))
    asp_set = set(asp.atoms(model, "mystery_story"))
    py_set = {
        (place, creature)
        for place in SETTINGS
        for creature in CREATURES
        if CREATURES[creature].carnivore
    }
    if asp_set == py_set:
        print(f"OK: clingo gate matches python reasoning ({len(py_set)} stories).")
        return 0
    print("MISMATCH between clingo and python reasoning:")
    print("  only in clingo:", sorted(asp_set - py_set))
    print("  only in python:", sorted(py_set - asp_set))
    return 1


def build_story(params: StoryParams) -> StorySample:
    world = tell(
        SETTINGS[params.place],
        CREATURES[params.creature],
        params.seeker_name,
        params.seeker_type,
        params.helper_name,
        params.helper_type,
    )
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
        print(asp_program("#show mystery_story/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        model = asp.one_model(asp_program("#show mystery_story/2."))
        stories = sorted(set(asp.atoms(model, "mystery_story")))
        print(f"{len(stories)} compatible mystery stories:")
        for place, creature in stories:
            print(f"  {place}  {creature}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [build_story(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 50, 50):
            seed = base_seed + i
            i += 1
            params = resolve_params(args, random.Random(seed))
            params.seed = seed
            sample = build_story(params)
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
            header = f"### {p.seeker_name}: {p.creature} at {p.place}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()

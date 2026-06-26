#!/usr/bin/env python3
"""
storyworlds/worlds/musty_cautionary_misunderstanding_mystery.py
===============================================================

A standalone story world for a small cautionary, misunderstanding-driven mystery.

Premise:
- A child explores a musty place and hears an odd sound.
- A careful warning is misunderstood at first.
- The search turns into a small mystery with a safe turn and a clear reveal.

The world is intentionally tiny: one place, one child, one worried helper,
one puzzling clue, and one sensible resolution.
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
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    protective: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "mother", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class Setting:
    place: str
    dark: bool = True
    musty: bool = True


@dataclass
class Clue:
    name: str
    sound: str
    cause: str
    risk: str
    reveal: str
    keyword: str = "musty"


@dataclass
class Gear:
    id: str
    label: str
    helps_with: set[str]
    note: str


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
        self.facts: dict = {}
        self.trace_log: list[str] = []

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str) -> Entity:
        return self.entities[eid]

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)
            self.trace_log.append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)

    def copy(self) -> "World":
        import copy
        w = World(self.setting)
        w.entities = copy.deepcopy(self.entities)
        w.fired = set(self.fired)
        return w


@dataclass
class StoryParams:
    place: str
    clue: str
    name: str
    gender: str
    helper: str
    trait: str
    seed: Optional[int] = None


PLACES = {
    "attic": Setting("the attic", dark=True, musty=True),
    "cellar": Setting("the cellar", dark=True, musty=True),
    "shed": Setting("the old shed", dark=True, musty=True),
}

CLUES = {
    "footsteps": Clue(
        name="footsteps",
        sound="soft footsteps",
        cause="a sleepy cat pacing on a shelf",
        risk="the child might trip over a loose board",
        reveal="the 'mystery footsteps' belonged to a cat",
    ),
    "rattle": Clue(
        name="rattle",
        sound="a small rattle",
        cause="jar lids tapping together in a box",
        risk="the child might knock over a stack of jars",
        reveal="the rattle came from jars jiggling in a basket",
    ),
    "whisper": Clue(
        name="whisper",
        sound="a whispery hiss",
        cause="wind slipping through a cracked window",
        risk="dust could blow into the child’s eyes",
        reveal="the whisper was only wind in the broken pane",
    ),
}

GEAR = {
    "lantern": Gear("lantern", "a little lantern", {"dark"}, "carry a little lantern"),
    "mask": Gear("mask", "a dust mask", {"musty"}, "put on a dust mask"),
    "gloves": Gear("gloves", "soft gloves", {"dusty"}, "wear soft gloves"),
}

TRAITS = ["curious", "careful", "brave", "quiet", "thoughtful"]
GIRL_NAMES = ["Mina", "Lina", "Tessa", "Ivy", "Nora", "Maya"]
BOY_NAMES = ["Theo", "Ben", "Eli", "Finn", "Owen", "Noah"]


def valid_combos() -> list[tuple[str, str]]:
    out = []
    for place in PLACES:
        for clue in CLUES:
            out.append((place, clue))
    return out


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A small musty mystery with a cautionary misunderstanding.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--clue", choices=CLUES)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--name")
    ap.add_argument("--helper", choices=["mother", "father"])
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
    combos = valid_combos()
    if args.place:
        combos = [c for c in combos if c[0] == args.place]
    if args.clue:
        combos = [c for c in combos if c[1] == args.clue]
    if not combos:
        raise StoryError("No valid mystery matches those options.")

    place, clue = rng.choice(combos)
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    helper = args.helper or rng.choice(["mother", "father"])
    trait = args.trait or rng.choice(TRAITS)
    return StoryParams(place=place, clue=clue, name=name, gender=gender, helper=helper, trait=trait)


def introduce(world: World, hero: Entity, helper: Entity, clue: Clue) -> None:
    world.say(
        f"{hero.id} was a {hero.memes.get('trait', 'curious')} little {hero.type} who liked noticing tiny clues."
    )
    world.say(
        f"One day, {hero.id} and {hero.pronoun('possessive')} {helper.label} went to {world.setting.place}, "
        f"which smelled {('musty' if world.setting.musty else 'old')} and a little forgotten."
    )
    world.say(
        f"Inside, {hero.id} heard {clue.sound} and felt sure something strange was hiding nearby."
    )


def warn_and_misunderstand(world: World, hero: Entity, helper: Entity, clue: Clue) -> None:
    hero.memes["worry"] = hero.memes.get("worry", 0) + 1
    world.say(
        f'"Let’s be careful," {helper.id} said. "This place is musty, dark, and old. Take {GEAR["lantern"].label} and {GEAR["mask"].label}."'
    )
    world.say(
        f"{hero.id} nodded, but {hero.pronoun('subject')} misunderstood the warning and thought it meant the sound was dangerous all by itself."
    )
    hero.memes["misunderstanding"] = 1
    world.say(
        f"So {hero.id} tiptoed closer, trying to solve the mystery before asking any more questions."
    )


def unsafe_search(world: World, hero: Entity, clue: Clue) -> None:
    if hero.memes.get("misunderstanding", 0) < THRESHOLD:
        return
    hero.meters["dust"] = hero.meters.get("dust", 0) + 1
    hero.memes["startle"] = hero.memes.get("startle", 0) + 1
    world.say(
        f"A puff of dust rose from the floor, and {hero.id} sneezed at the worst possible moment."
    )
    world.say(
        f"{clue.risk.capitalize()}, so {hero.id} stopped and looked back at the doorway."
    )


def reveal_and_fix(world: World, hero: Entity, helper: Entity, clue: Clue) -> None:
    hero.memes["misunderstanding"] = 0
    world.say(
        f"{helper.id} stepped closer with the lantern, smiled, and pointed at the real clue."
    )
    world.say(
        f"It was not a spooky secret at all: {clue.reveal}."
    )
    world.say(
        f"{hero.id} felt silly for a moment, then relieved. The warning had not been a riddle; it had been a kind way to stay safe."
    )
    world.say(
        f"Together they opened the box, checked the dusty corner, and left the {world.setting.place} tidy and calm."
    )


def tell(setting: Setting, clue: Clue, hero_name: str, hero_gender: str, helper_type: str, trait: str) -> World:
    world = World(setting)
    hero = world.add(Entity(id=hero_name, kind="character", type=hero_gender, memes={"trait": trait}))
    helper = world.add(Entity(id="Helper", kind="character", type=helper_type, label=f"the {helper_type}"))
    world.facts.update(hero=hero, helper=helper, clue=clue, setting=setting)

    introduce(world, hero, helper, clue)
    world.para()
    warn_and_misunderstand(world, hero, helper, clue)
    unsafe_search(world, hero, clue)
    world.para()
    reveal_and_fix(world, hero, helper, clue)
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    clue = f["clue"]
    setting = f["setting"]
    return [
        f"Write a short cautionary mystery for a small child in {setting.place} with a musty clue.",
        f"Tell a gentle story where {hero.id} misunderstands a warning and then learns what the sound really was.",
        f"Create a child-friendly mystery about {clue.sound}, old dust, and a safe ending.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    helper = f["helper"]
    clue = f["clue"]
    setting = f["setting"]
    return [
        QAItem(
            question=f"Where did {hero.id} go to hear the strange sound?",
            answer=f"{hero.id} went to {setting.place}, which smelled musty and felt a little spooky.",
        ),
        QAItem(
            question=f"What warning did {helper.id} give before the search?",
            answer=f"{helper.id} said to be careful because the place was musty and dark, and to take a lantern and a dust mask.",
        ),
        QAItem(
            question=f"What did {hero.id} misunderstand at first?",
            answer=f"{hero.id} misunderstood the warning and thought the sound itself must be dangerous, so {hero.pronoun('subject')} rushed closer too soon.",
        ),
        QAItem(
            question=f"What was the mystery sound really?",
            answer=f"The mystery was not spooky at all. It was {clue.cause}.",
        ),
        QAItem(
            question=f"How did the story end?",
            answer=f"{hero.id} understood the warning, felt relieved, and left {setting.place} calm and tidy with {helper.id}.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does musty mean?",
            answer="Musty means old, damp, and a little stale, like a room that has not had fresh air in a while.",
        ),
        QAItem(
            question="Why should you use a lantern in a dark place?",
            answer="A lantern helps you see where you are going, so you can avoid tripping or bumping into things.",
        ),
        QAItem(
            question="What is a misunderstanding?",
            answer="A misunderstanding happens when someone thinks something means one thing, but it really means something else.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== Prompts =="]
    for p in sample.prompts:
        lines.append(p)
    lines.append("")
    lines.append("== Story Q&A ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== World Q&A ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for e in world.entities.values():
        lines.append(f"{e.id}: kind={e.kind} type={e.type} meters={e.meters} memes={e.memes}")
    return "\n".join(lines)


ASP_RULES = r"""
valid_place(P) :- place(P).
valid_clue(C) :- clue(C).
valid_story(P, C) :- valid_place(P), valid_clue(C).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for p in PLACES:
        lines.append(asp.fact("place", p))
    for c in CLUES:
        lines.append(asp.fact("clue", c))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple[str, str]]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/2."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: ASP matches Python ({len(py)} combos).")
        return 0
    print("MISMATCH:")
    print("only python:", sorted(py - cl))
    print("only asp:", sorted(cl - py))
    return 1


def generate(params: StoryParams) -> StorySample:
    world = tell(PLACES[params.place], CLUES[params.clue], params.name, params.gender, params.helper, params.trait)
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
    StoryParams(place="attic", clue="footsteps", name="Mina", gender="girl", helper="mother", trait="curious"),
    StoryParams(place="cellar", clue="rattle", name="Theo", gender="boy", helper="father", trait="careful"),
    StoryParams(place="shed", clue="whisper", name="Ivy", gender="girl", helper="mother", trait="thoughtful"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid_story/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible story combos:")
        for p, c in combos:
            print(f"  {p} / {c}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)

    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
            seed = base_seed + i
            i += 1
            try:
                params = resolve_params(args, random.Random(seed))
            except StoryError as err:
                print(err)
                return
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

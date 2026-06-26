#!/usr/bin/env python3
"""
fault_bad_soccer_field_twist_surprise_quest.py
==============================================

A small bedtime-story world set on a soccer field, where a child faces a
broken plan, notices a fault, and turns a bad moment into a gentle quest with a
twist and a surprise.

The core premise:
- A child comes to the soccer field excited for play.
- Something is wrong with the field or equipment.
- A grown-up or helper spots the fault and explains the bad choice.
- The pair goes on a small quest to fix or replace what is needed.
- A twist reveals a surprising but kind solution.
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


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    role: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
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
    place: str = "the soccer field"
    surface: str = "grass"
    affordance: str = "play soccer"


@dataclass
class Fault:
    id: str
    label: str
    bad: str
    twist: str
    surprise: str
    quest: str
    fix: str
    kind: str = "field"
    severity: float = 1.0


@dataclass
class StoryParams:
    place: str
    fault: str
    name: str
    gender: str
    parent: str
    trait: str
    seed: Optional[int] = None


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.facts: dict[str, object] = {}
        self.paragraphs: list[list[str]] = [[]]

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


SETTINGS = {
    "soccer_field": Setting(place="the soccer field", surface="grass", affordance="play soccer"),
}

FAULTS = {
    "flat_ball": Fault(
        id="flat_ball",
        label="a flat soccer ball",
        bad="would not bounce right",
        twist="the ball had only slipped under the bench",
        surprise="a shiny spare ball waited in the coach's bag",
        quest="find a good ball before bedtime",
        fix="they borrowed the spare ball and the game could begin",
    ),
    "mud_patch": Fault(
        id="mud_patch",
        label="a muddy patch by the goal",
        bad="would make fast running slippery",
        twist="the mud had actually covered a tiny lost whistle",
        surprise="the whistle belonged to the coach and made a happy little beep",
        quest="find a clean way around the mud",
        fix="they walked around the patch and still made a goal",
    ),
    "missing_cone": Fault(
        id="missing_cone",
        label="a missing cone marker",
        bad="would confuse the practice line",
        twist="the missing cone was being used as a nest for a sleepy kitten",
        surprise="the kitten blinked up and purred like a tiny drum",
        quest="find another marker without upsetting the kitten",
        fix="they used a bright orange sock as the new marker",
    ),
}

GIRL_NAMES = ["Mia", "Lily", "Zoe", "Ava", "Nora", "Ella", "Maya"]
BOY_NAMES = ["Leo", "Finn", "Ben", "Theo", "Noah", "Eli", "Max"]
TRAITS = ["quiet", "brave", "curious", "gentle", "cheerful", "patient"]


def fault_causes_bad(fault: Fault) -> str:
    return f"{fault.label} {fault.bad}"


def setting_line(setting: Setting) -> str:
    return f"The {setting.place.removeprefix('the ')} looked calm in the soft evening light."


def introduce(world: World, hero: Entity, parent: Entity, fault: Fault) -> None:
    world.say(
        f"{hero.id} was a little {next(t for t in [hero.type, *hero.memes.keys()] if t)} child who loved the {world.setting.place}."
    )
    world.say(
        f"{hero.pronoun().capitalize()} and {parent.label} came there to {world.setting.affordance} before bedtime."
    )
    world.say(setting_line(world.setting))
    world.say(f"Then they noticed {fault.label}.")


def want_play(world: World, hero: Entity, fault: Fault) -> None:
    hero.memes["hope"] = hero.memes.get("hope", 0.0) + 1
    world.say(
        f"{hero.id} wanted to play right away, but {fault.label} meant the plan felt a little bad."
    )


def explain_fault(world: World, parent: Entity, hero: Entity, fault: Fault) -> None:
    hero.memes["worry"] = hero.memes.get("worry", 0.0) + 1
    world.say(
        f"{parent.label.capitalize()} pointed out that {fault.label} was the fault in the field."
    )
    world.say(
        f'"If we rush now," {parent.label} said softly, "the day could turn bad for everyone."'
    )


def quest(world: World, hero: Entity, parent: Entity, fault: Fault) -> None:
    hero.memes["quest"] = hero.memes.get("quest", 0.0) + 1
    world.say(
        f"So {hero.id} and {parent.label} began a small quest to {fault.quest}."
    )


def twist_and_surprise(world: World, hero: Entity, fault: Fault) -> None:
    world.say(f"On the way, there was a twist: {fault.twist}.")
    world.say(f"The surprise was {fault.surprise}.")


def resolve(world: World, hero: Entity, parent: Entity, fault: Fault) -> None:
    hero.memes["joy"] = hero.memes.get("joy", 0.0) + 1
    world.say(
        f"In the end, {fault.fix}, and {hero.id} felt warm and happy again."
    )
    world.say(
        f"{hero.id} looked back at the {world.setting.place} and smiled, because a bad day had turned kind."
    )


def tell(setting: Setting, fault: Fault, hero_name: str, hero_type: str, parent_type: str, trait: str) -> World:
    world = World(setting)
    hero = world.add(Entity(id=hero_name, kind="character", type=hero_type, memes={"kind": 1.0, trait: 1.0}))
    parent = world.add(Entity(id="Parent", kind="character", type=parent_type, label="parent"))
    world.facts.update(hero=hero, parent=parent, fault=fault, trait=trait)

    introduce(world, hero, parent, fault)
    world.para()
    want_play(world, hero, fault)
    explain_fault(world, parent, hero, fault)
    quest(world, hero, parent, fault)
    world.para()
    twist_and_surprise(world, hero, fault)
    resolve(world, hero, parent, fault)
    world.facts["resolved"] = True
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    fault = f["fault"]
    return [
        f'Write a bedtime story about {hero.id} at the soccer field where a small fault makes the day go bad, but a quest helps.',
        f"Tell a gentle story with a twist and a surprise about {fault.label} on a soccer field.",
        f"Write a child-friendly story about a soccer field, a quest, and a kind fix after something bad goes wrong.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    parent = f["parent"]
    fault = f["fault"]
    return [
        QAItem(
            question=f"Where does {hero.id} go in this story?",
            answer=f"{hero.id} goes to the soccer field with {parent.label} for a bedtime game.",
        ),
        QAItem(
            question=f"What was the fault in the story?",
            answer=f"The fault was {fault.label}, and it made the day feel bad at first.",
        ),
        QAItem(
            question=f"What did {hero.id} and {parent.label} do after they saw the problem?",
            answer=f"They went on a small quest to fix things in a gentle way.",
        ),
        QAItem(
            question="What was the twist?",
            answer=f"The twist was that {fault.twist}.",
        ),
        QAItem(
            question="What was the surprise?",
            answer=f"The surprise was {fault.surprise}.",
        ),
        QAItem(
            question="How did the story end?",
            answer=f"It ended with {fault.fix}, and the bad feeling changed into a happy bedtime moment.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a soccer field for?",
            answer="A soccer field is a place where people run, kick a ball, and play soccer.",
        ),
        QAItem(
            question="Why can a muddy patch be a problem on a field?",
            answer="A muddy patch can make shoes slip and make it harder to run safely.",
        ),
        QAItem(
            question="What does a flat ball do?",
            answer="A flat ball does not bounce or roll as well as a properly filled ball.",
        ),
        QAItem(
            question="What is a quest in a story?",
            answer="A quest is a small journey to find, fix, or learn something important.",
        ),
        QAItem(
            question="What is a twist in a story?",
            answer="A twist is a surprising change that makes the story go in a new direction.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== story qa ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== world qa ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        bits = []
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        lines.append(f"  {e.id:10} ({e.type:8}) {' '.join(bits)}")
    return "\n".join(lines)


ASP_RULES = r"""
setting(soccer_field).
place(soccer_field).

fault(flat_ball).
fault(mud_patch).
fault(missing_cone).

bad(flat_ball).
bad(mud_patch).
bad(missing_cone).

twist(flat_ball).
twist(mud_patch).
twist(missing_cone).

surprise(flat_ball).
surprise(mud_patch).
surprise(missing_cone).

quest(flat_ball).
quest(mud_patch).
quest(missing_cone).

valid_story(P, F) :- place(P), fault(F), bad(F), twist(F), surprise(F), quest(F).
"""


def asp_facts() -> str:
    import asp
    lines = [asp.fact("place", "soccer_field")]
    for fid in FAULTS:
        lines.append(asp.fact("fault", fid))
        lines.append(asp.fact("bad", fid))
        lines.append(asp.fact("twist", fid))
        lines.append(asp.fact("surprise", fid))
        lines.append(asp.fact("quest", fid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show valid_story/2."))
    clingo_set = set(asp.atoms(model, "valid_story"))
    py_set = {("soccer_field", fid) for fid in FAULTS}
    if clingo_set == py_set:
        print(f"OK: clingo gate matches Python ({len(py_set)} stories).")
        return 0
    print("MISMATCH between clingo and Python:")
    print("  only in clingo:", sorted(clingo_set - py_set))
    print("  only in python:", sorted(py_set - clingo_set))
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Bedtime story world: fault, bad, twist, surprise, quest, soccer field.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--fault", choices=FAULTS)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--parent", choices=["mother", "father"])
    ap.add_argument("--name")
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
    place = args.place or "soccer_field"
    fault = args.fault or rng.choice(list(FAULTS))
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    parent = args.parent or rng.choice(["mother", "father"])
    trait = args.trait or rng.choice(TRAITS)
    return StoryParams(place=place, fault=fault, name=name, gender=gender, parent=parent, trait=trait)


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.place], FAULTS[params.fault], params.name, params.gender, params.parent, params.trait)
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
    StoryParams(place="soccer_field", fault="flat_ball", name="Mia", gender="girl", parent="mother", trait="curious"),
    StoryParams(place="soccer_field", fault="mud_patch", name="Leo", gender="boy", parent="father", trait="gentle"),
    StoryParams(place="soccer_field", fault="missing_cone", name="Nora", gender="girl", parent="mother", trait="patient"),
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
        model = asp.one_model(asp_program("#show valid_story/2."))
        combos = sorted(set(asp.atoms(model, "valid_story")))
        print(f"{len(combos)} compatible story combinations:")
        for combo in combos:
            print(" ", combo)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 20):
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
        header = f"### variant {i+1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()

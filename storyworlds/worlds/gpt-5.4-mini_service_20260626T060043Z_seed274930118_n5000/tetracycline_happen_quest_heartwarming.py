#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260626T060043Z_seed274930118_n5000/tetracycline_happen_quest_heartwarming.py
===============================================================================================================

A small heartwarming story world about a caring quest for tetracycline.

Seed tale premise:
- Something unwell happens.
- A child, parent, or helper goes on a quest.
- They get tetracycline from a proper place.
- The sick one feels better, and the day ends warmly.

This script keeps the world model tiny but state-driven:
- physical meters track travel, carrying, and medicine delivery
- emotional memes track worry, hope, courage, and relief

The generated prose is intentionally gentle and child-facing.
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
# World entities
# ---------------------------------------------------------------------------
@dataclass
class Entity:
    id: str
    kind: str = "thing"  # character | thing
    label: str = ""
    type: str = "thing"
    plural: bool = False
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def __post_init__(self) -> None:
        for k in ["distance", "carried", "delivered", "sick", "healthy", "work"]:
            self.meters.setdefault(k, 0.0)
        for k in ["worry", "hope", "courage", "relief", "love"]:
            self.memes.setdefault(k, 0.0)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman"}
        male = {"boy", "father", "dad", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class Setting:
    place: str = "the little town"
    pharmacy: str = "the corner pharmacy"
    clinic: str = "the small clinic"
    home: str = "the warm home"


@dataclass
class StoryParams:
    setting: str
    hero_name: str
    hero_type: str
    companion_type: str
    patient_type: str
    patient_name: str
    seed: Optional[int] = None


SETTINGS = {
    "town": Setting(place="the little town", pharmacy="the corner pharmacy", clinic="the small clinic", home="the warm home"),
    "village": Setting(place="the village", pharmacy="the village pharmacy", clinic="the vet clinic", home="the cozy cottage"),
    "neighborhood": Setting(place="the neighborhood", pharmacy="the drugstore on the bright street", clinic="the neighborhood clinic", home="the snug house"),
}

HERO_NAMES = ["Mia", "Noah", "Lily", "Eli", "Ava", "Ben", "Zoe", "Theo"]
PATIENT_NAMES = ["Pip", "Sunny", "Bean", "Mo", "Poppy", "Nugget"]
CHAR_TYPES = ["girl", "boy"]
COMPANIONS = ["mother", "father", "grandmother", "grandfather"]
PATIENT_TYPES = ["puppy", "kitten", "bunny", "lamb"]


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict[str, object] = {}
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


# ---------------------------------------------------------------------------
# Reasonableness gate
# ---------------------------------------------------------------------------
def valid_story(params: StoryParams) -> bool:
    return params.setting in SETTINGS


def explain_invalid(params: StoryParams) -> str:
    return "(No story: the requested setting does not exist in this world.)"


# ---------------------------------------------------------------------------
# Plot actions
# ---------------------------------------------------------------------------
def arrive_home(world: World, hero: Entity, companion: Entity, patient: Entity) -> None:
    world.say(
        f"At {world.setting.home}, {patient.label} looked small and tired."
    )
    world.say(
        f"{hero.id} noticed that {patient.label} was not smiling much, and {companion.pronoun('subject')} noticed it too."
    )


def something_happens(world: World, patient: Entity) -> None:
    patient.meters["sick"] = 1
    patient.memes["worry"] += 1
    world.say(
        f"One quiet afternoon, something happened: {patient.label} sneezed, coughed, and curled up in a little bundle."
    )
    world.say(
        f"The room felt less bright right away, and everyone grew worried."
    )


def decide_quest(world: World, hero: Entity, companion: Entity, patient: Entity) -> None:
    hero.memes["courage"] += 1
    companion.memes["hope"] += 1
    world.say(
        f"{hero.id} promised to help. {companion.pronoun('subject').capitalize()} said they would go on a careful quest for the medicine the clinic had suggested."
    )
    world.say(
        f"They needed tetracycline, and they wanted to get it the right way from the pharmacy."
    )


def travel_to_pharmacy(world: World, hero: Entity, companion: Entity) -> None:
    hero.meters["distance"] += 1
    companion.meters["distance"] += 1
    world.say(
        f"Together they walked through {world.setting.place}, past quiet doors and soft window lights, until they reached {world.setting.pharmacy}."
    )


def get_medicine(world: World, hero: Entity) -> Entity:
    med = world.add(Entity(id="medicine", kind="thing", label="tetracycline", type="medicine"))
    med.meters["carried"] = 1
    hero.meters["carried"] += 1
    world.say(
        f"The helper at the counter handed them tetracycline with a kind smile, and {hero.id} held the bottle carefully in both hands."
    )
    return med


def return_home(world: World, hero: Entity, companion: Entity) -> None:
    hero.meters["distance"] += 1
    companion.meters["distance"] += 1
    world.say(
        f"They hurried back home, careful not to jostle the bottle, because the medicine mattered."
    )


def give_medicine(world: World, hero: Entity, patient: Entity, med: Entity) -> None:
    if med.meters["carried"] <= 0:
        raise StoryError("The tetracycline was never picked up, so it cannot be given.")
    med.meters["delivered"] = 1
    med.meters["carried"] = 0
    patient.meters["sick"] = 0
    patient.meters["healthy"] = 1
    patient.memes["worry"] = 0
    patient.memes["relief"] += 1
    hero.memes["hope"] += 1
    world.say(
        f"At last, {hero.id} gave the tetracycline to {patient.label} the way the doctor had said."
    )
    world.say(
        f"Little by little, {patient.label} stopped shaking, blinked awake, and nestled against {hero.id}'s side."
    )


def end_warmly(world: World, hero: Entity, companion: Entity, patient: Entity) -> None:
    hero.memes["love"] += 1
    companion.memes["relief"] += 1
    world.say(
        f"That night, {patient.label} slept safely in the warm home, and {hero.id} felt proud of the quest."
    )
    world.say(
        f"Nothing magical had happened, just a careful trip, a proper medicine, and a lot of love."
    )


# ---------------------------------------------------------------------------
# Story assembly
# ---------------------------------------------------------------------------
def tell(setting: Setting, hero_name: str, hero_type: str, companion_type: str, patient_type: str, patient_name: str) -> World:
    world = World(setting)
    hero = world.add(Entity(id=hero_name, kind="character", type=hero_type))
    companion = world.add(Entity(id=companion_type.capitalize(), kind="character", type=companion_type))
    patient = world.add(Entity(id=patient_name, kind="character", type=patient_type, label=patient_name))
    world.facts.update(hero=hero, companion=companion, patient=patient)

    world.say(
        f"{hero.id} lived in {setting.home} with {companion_type} and {patient.label}."
    )
    world.say(
        f"{hero.id} loved {patient.label}, and {patient.label} loved being near {hero.id}."
    )

    world.para()
    something_happens(world, patient)
    arrive_home(world, hero, companion, patient)

    world.para()
    decide_quest(world, hero, companion, patient)
    travel_to_pharmacy(world, hero, companion)
    med = get_medicine(world, hero)
    world.facts["medicine"] = med

    world.para()
    return_home(world, hero, companion)
    give_medicine(world, hero, patient, med)
    end_warmly(world, hero, companion, patient)

    world.facts["resolved"] = True
    return world


# ---------------------------------------------------------------------------
# Registries / ASP twin
# ---------------------------------------------------------------------------
def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for t in CHAR_TYPES:
        lines.append(asp.fact("hero_type", t))
    for c in COMPANIONS:
        lines.append(asp.fact("companion_type", c))
    for p in PATIENT_TYPES:
        lines.append(asp.fact("patient_type", p))
    lines.append(asp.fact("medicine", "tetracycline"))
    lines.append(asp.fact("happens_in_story", "happen"))
    lines.append(asp.fact("feature", "quest"))
    lines.append(asp.fact("style", "heartwarming"))
    return "\n".join(lines)


ASP_RULES = r"""
valid_story(S) :- setting(S), medicine(tetracycline), feature(quest), style(heartwarming).
#show valid_story/1.
"""


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_settings() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/1."))
    return sorted(set(asp.atoms(model, "valid_story")))


# ---------------------------------------------------------------------------
# QA
# ---------------------------------------------------------------------------
def generation_prompts(world: World) -> list[str]:
    return [
        'Write a heartwarming short story where something happens and a caring child goes on a quest for tetracycline.',
        f'Write a gentle story about {world.facts["hero"].id} helping {world.facts["patient"].label} with a medicine quest.',
        'Tell a warm story with a clear problem, a careful errand, and a happy ending.',
    ]


def story_qa(world: World) -> list[QAItem]:
    hero: Entity = world.facts["hero"]  # type: ignore[assignment]
    companion: Entity = world.facts["companion"]  # type: ignore[assignment]
    patient: Entity = world.facts["patient"]  # type: ignore[assignment]
    return [
        QAItem(
            question=f"What happened first to {patient.label}?",
            answer=f"{patient.label} got sick, sneezed, and looked tired, so everyone grew worried.",
        ),
        QAItem(
            question=f"What did {hero.id} and {companion.id} go looking for?",
            answer="They went on a careful quest for tetracycline from the pharmacy.",
        ),
        QAItem(
            question=f"How did the story end for {patient.label}?",
            answer=f"{patient.label} got the tetracycline, felt better, and curled up safely at home with the others.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a quest?",
            answer="A quest is a purposeful journey to find or do something important.",
        ),
        QAItem(
            question="What is tetracycline?",
            answer="Tetracycline is a medicine that doctors may prescribe to help treat certain infections.",
        ),
        QAItem(
            question="What does it mean when something happens?",
            answer="If something happens, it means an event or change takes place.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    out = ["== prompts =="]
    for p in sample.prompts:
        out.append(p)
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


def dump_trace(world: World) -> str:
    lines = ["--- trace ---"]
    for e in world.entities.values():
        m = {k: v for k, v in e.meters.items() if v}
        e2 = {k: v for k, v in e.memes.items() if v}
        parts = []
        if m:
            parts.append(f"meters={m}")
        if e2:
            parts.append(f"memes={e2}")
        lines.append(f"{e.id}: {e.kind} {e.type} {' '.join(parts)}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Heartwarming quest world with tetracycline and happen.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--name")
    ap.add_argument("--hero-type", choices=CHAR_TYPES)
    ap.add_argument("--companion-type", choices=COMPANIONS)
    ap.add_argument("--patient-type", choices=PATIENT_TYPES)
    ap.add_argument("--patient-name")
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
    setting = args.setting or rng.choice(list(SETTINGS))
    if setting not in SETTINGS:
        raise StoryError(explain_invalid(StoryParams(setting, "", "", "", "", "")))
    hero_type = args.hero_type or rng.choice(CHAR_TYPES)
    companion_type = args.companion_type or rng.choice(COMPANIONS)
    patient_type = args.patient_type or rng.choice(PATIENT_TYPES)
    hero_name = args.name or rng.choice(HERO_NAMES)
    patient_name = args.patient_name or rng.choice(PATIENT_NAMES)
    return StoryParams(
        setting=setting,
        hero_name=hero_name,
        hero_type=hero_type,
        companion_type=companion_type,
        patient_type=patient_type,
        patient_name=patient_name,
    )


def generate(params: StoryParams) -> StorySample:
    if not valid_story(params):
        raise StoryError(explain_invalid(params))
    world = tell(SETTINGS[params.setting], params.hero_name, params.hero_type, params.companion_type, params.patient_type, params.patient_name)
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
    import asp
    clingo_set = set(asp_valid_settings())
    python_set = {(k,) for k in SETTINGS}
    if clingo_set == python_set:
        print(f"OK: clingo gate matches Python ({len(clingo_set)} settings).")
        return 0
    print("MISMATCH between clingo and Python:")
    print("only in clingo:", sorted(clingo_set - python_set))
    print("only in python:", sorted(python_set - clingo_set))
    return 1


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid_story/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        settings = asp_valid_settings()
        print(f"{len(settings)} valid settings:\n")
        for s in settings:
            print(" ", s[0])
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        combos = [
            StoryParams("town", "Mia", "girl", "mother", "puppy", "Pip"),
            StoryParams("village", "Noah", "boy", "father", "kitten", "Sunny"),
            StoryParams("neighborhood", "Ava", "girl", "grandmother", "bunny", "Bean"),
        ]
        samples = [generate(p) for p in combos]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 20):
            i += 1
            seed = base_seed + i
            try:
                params = resolve_params(args, random.Random(seed))
                params.seed = seed
                sample = generate(params)
            except StoryError as err:
                print(err)
                return
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

    for idx, sample in enumerate(samples):
        header = f"### variant {idx + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if idx < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()

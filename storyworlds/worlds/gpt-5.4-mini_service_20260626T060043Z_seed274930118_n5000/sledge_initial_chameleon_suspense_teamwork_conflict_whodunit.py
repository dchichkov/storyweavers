#!/usr/bin/env python3
"""
A small story world: a careful whodunit in a garden workshop with a sledge,
a missing initial, a chameleon, suspense, teamwork, and conflict.

The seed premise:
A chameleon keeps changing color, a wooden sledge goes missing, and one tiny
initial carved into a tag becomes the clue that solves the mystery. The story
turns on suspicion, teamwork, and a gentle resolution.
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
    kind: str = "thing"  # character | thing | clue
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    carried_by: Optional[str] = None
    hidden_in: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)
    traits: list[str] = field(default_factory=list)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "mother", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class Setting:
    place: str = "the garden shed"
    indoor: bool = True
    affords: set[str] = field(default_factory=lambda: {"search", "hide", "assemble"})


@dataclass
class StoryParams:
    place: str
    hero_name: str
    helper_name: str
    suspect_name: str
    seed: Optional[int] = None


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.fired: set[tuple] = set()

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
    "shed": Setting(place="the garden shed", indoor=True),
    "greenhouse": Setting(place="the greenhouse", indoor=True),
    "porch": Setting(place="the porch", indoor=False),
}

NAMES = ["Mina", "Owen", "Clara", "Eli", "Iris", "Noah", "June", "Leo"]
TRAITS = ["curious", "careful", "brave", "patient", "sharp-eyed"]


@dataclass
class ObjectDef:
    label: str
    phrase: str
    hidden_spot: str


SLEDGES = {
    "wooden_sledge": ObjectDef(
        label="sledge",
        phrase="a sturdy wooden sledge with iron runners",
        hidden_spot="behind the paint tins",
    )
}

CLUES = {
    "initial_tag": ObjectDef(
        label="initial",
        phrase="a tiny brass tag with one engraved initial",
        hidden_spot="under a coil of rope",
    )
}


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
% A story is valid when the place can host a search, a sledge exists,
% and one clue points to one suspect.
has_sledge :- object(sledge).
has_clue :- object(initial).
valid_story(P) :- place(P), has_sledge, has_clue.
"""

def asp_facts() -> str:
    import asp
    lines = []
    for pid in SETTINGS:
        lines.append(asp.fact("place", pid))
    lines.append(asp.fact("object", "sledge"))
    lines.append(asp.fact("object", "initial"))
    return "\n".join(lines)

def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"

def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show valid_story/1."))
    asp_ok = bool(asp.atoms(model, "valid_story"))
    py_ok = True
    if asp_ok == py_ok:
        print("OK: ASP and Python parity verified.")
        return 0
    print("MISMATCH between ASP and Python.")
    return 1


# ---------------------------------------------------------------------------
# Story mechanics
# ---------------------------------------------------------------------------
def build_story(params: StoryParams) -> World:
    world = World(SETTINGS[params.place])

    hero = world.add(Entity(id=params.hero_name, kind="character", type="child", label=params.hero_name))
    helper = world.add(Entity(id=params.helper_name, kind="character", type="child", label=params.helper_name))
    suspect = world.add(Entity(id=params.suspect_name, kind="character", type="child", label=params.suspect_name, traits=["mischievous"]))
    chameleon = world.add(Entity(
        id="chameleon",
        kind="character",
        type="chameleon",
        label="the chameleon",
        phrase="a tiny chameleon that could fade into leaves and bark",
        traits=["changing", "quiet"],
    ))
    sledge = world.add(Entity(
        id="sledge",
        kind="thing",
        type="sledge",
        label="sledge",
        phrase=SLEDGES["wooden_sledge"].phrase,
        owner=helper.id,
    ))
    initial = world.add(Entity(
        id="initial",
        kind="clue",
        type="initial",
        label="initial",
        phrase=CLUES["initial_tag"].phrase,
        owner=helper.id,
        hidden_in=SLEDGES["wooden_sledge"].hidden_spot,
    ))

    # Act 1: setup
    world.say(
        f"{hero.id} and {helper.id} were in {world.setting.place}, where a curious little mystery had begun."
    )
    world.say(
        f"{helper.id} had brought {sledge.phrase}, but one part of the day felt wrong: the little tag on the handle was missing its initial."
    )
    world.say(
        f"Near the bench, a chameleon kept blinking from leaf-green to bark-brown, and that made everyone look twice."
    )

    # Act 2: suspicion and conflict
    world.para()
    suspect.memes["suspicion"] = 1
    hero.memes["suspense"] = 1
    world.say(
        f"{hero.id} whispered that the chameleon might have taken the clue, because it was the only one that could vanish so neatly."
    )
    world.say(
        f"But {helper.id} frowned. \"Let's not accuse too quickly,\" {helper.id} said, and that started a small conflict."
    )
    suspect.memes["conflict"] = 1
    world.say(
        f"{suspect.id} crossed {suspect.pronoun('possessive')} arms and said {hero.id} was being unfair."
    )

    # Act 3: teamwork reveals the truth
    world.para()
    helper.memes["teamwork"] = 1
    hero.memes["teamwork"] = 1
    world.say(
        f"Then {hero.id} and {helper.id} searched together: one looked by the rope, the other checked behind the paint tins."
    )
    initial.hidden_in = None
    initial.carried_by = chameleon.id
    world.say(
        f"At last, they found the tiny initial stuck to the chameleon's foot, where it had caught like a shiny crumb."
    )
    world.say(
        f"The chameleon had not stolen it on purpose; it had only stepped where the tag had fallen and carried it by accident."
    )
    world.say(
        f"{suspect.id} stopped frowning, and everyone laughed when the little clue came loose."
    )
    world.say(
        f"In the end, the sledge was whole again, the mystery was solved, and the chameleon settled green beside the toolbox, no longer the suspect but the surprise."
    )

    world.facts.update(
        hero=hero,
        helper=helper,
        suspect=suspect,
        chameleon=chameleon,
        sledge=sledge,
        initial=initial,
        place=params.place,
    )
    return world


# ---------------------------------------------------------------------------
# QA
# ---------------------------------------------------------------------------
def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a short whodunit for children set in {f["place"]} about a missing initial, a sledge, and a chameleon.',
        f'Tell a suspenseful story where {f["hero"].id} and {f["helper"].id} solve a tiny mystery by working together.',
        f'Write a gentle mystery that begins with a suspicious chameleon, has conflict, and ends with teamwork and a found clue.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero, helper, suspect, chameleon = f["hero"], f["helper"], f["suspect"], f["chameleon"]
    return [
        QAItem(
            question=f"What mystery did {hero.id} and {helper.id} try to solve?",
            answer="They tried to solve the mystery of the missing initial on the sledge's tag.",
        ),
        QAItem(
            question=f"Why did the chameleon seem suspicious at first?",
            answer="It seemed suspicious because it could change color and hide so well that the others thought it might have taken the clue.",
        ),
        QAItem(
            question=f"How did the story move from conflict to teamwork?",
            answer=f"{hero.id} and {helper.id} stopped arguing, searched together, and found the initial where the chameleon had accidentally carried it.",
        ),
        QAItem(
            question=f"Who was blamed before the truth came out?",
            answer=f"The chameleon was blamed first, while {f['suspect'].id} got upset during the argument.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a chameleon?",
            answer="A chameleon is a kind of lizard that can change color to blend in with its surroundings.",
        ),
        QAItem(
            question="What is a sledge?",
            answer="A sledge is a strong sled or hauling board used to move heavy things.",
        ),
        QAItem(
            question="What is an initial?",
            answer="An initial is the first letter of a name.",
        ),
        QAItem(
            question="Why do clues matter in a whodunit?",
            answer="Clues matter because they help people figure out what really happened.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== Prompts =="]
    for p in sample.prompts:
        lines.append(f"- {p}")
    lines.append("")
    lines.append("== Story QA ==")
    for q in sample.story_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    lines.append("")
    lines.append("== World QA ==")
    for q in sample.world_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- trace ---"]
    for e in world.entities.values():
        bits = []
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        if e.hidden_in:
            bits.append(f"hidden_in={e.hidden_in}")
        if e.carried_by:
            bits.append(f"carried_by={e.carried_by}")
        lines.append(f"{e.id}: {e.kind}/{e.type} {' '.join(bits)}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Generation
# ---------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A small whodunit story world.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--hero-name")
    ap.add_argument("--helper-name")
    ap.add_argument("--suspect-name")
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
    hero = args.hero_name or rng.choice(NAMES)
    helper = args.helper_name or rng.choice([n for n in NAMES if n != hero])
    suspect = args.suspect_name or rng.choice([n for n in NAMES if n not in {hero, helper}])
    if len({hero, helper, suspect}) < 3:
        raise StoryError("Need three different names for hero, helper, and suspect.")
    return StoryParams(place=place, hero_name=hero, helper_name=helper, suspect_name=suspect)


def generate(params: StoryParams) -> StorySample:
    world = build_story(params)
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
        print(asp_program("#show valid_story/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print("ASP mode: the inline rules are present and the story world is valid.")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        curated = [
            StoryParams(place="shed", hero_name="Mina", helper_name="Owen", suspect_name="Clara"),
            StoryParams(place="greenhouse", hero_name="Iris", helper_name="Leo", suspect_name="Noah"),
            StoryParams(place="porch", hero_name="June", helper_name="Eli", suspect_name="Clara"),
        ]
        samples = [generate(p) for p in curated]
    else:
        seen = set()
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

    for idx, sample in enumerate(samples):
        if len(samples) > 1:
            print(f"### variant {idx + 1}")
        emit(sample, trace=args.trace, qa=args.qa)
        if idx < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()

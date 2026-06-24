#!/usr/bin/env python3
"""
Standalone storyworld: ball + venetian + kindness twist bedtime story.

A small bedtime-domain simulation in the Storyweavers style. A child wants to
play with a ball near bedtime; the room has a venetian blind that changes the
light; a gentle kindness twist turns the delay into a calming routine.
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
class StoryParams:
    name: str
    gender: str
    parent: str
    place: str
    seed: Optional[int] = None


@dataclass
class Setting:
    place: str
    kind: str
    affords: set[str] = field(default_factory=set)


@dataclass
class Toy:
    label: str
    phrase: str
    type: str = "ball"


@dataclass
class ComfortItem:
    id: str
    label: str
    prepares: str
    helps: str


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}

    def add(self, e: Entity) -> Entity:
        self.entities[e.id] = e
        return e

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)


SETTINGS = {
    "bedroom": Setting(place="the bedroom", kind="inside", affords={"tuck", "twist"}),
    "nursery": Setting(place="the nursery", kind="inside", affords={"tuck", "twist"}),
}

BALLS = {
    "red_ball": Toy(label="red ball", phrase="a bright red ball"),
    "blue_ball": Toy(label="blue ball", phrase="a smooth blue ball"),
}

COMFORTS = {
    "blanket": ComfortItem(id="blanket", label="soft blanket", prepares="fold the soft blanket around the ball", helps="keep the room calm"),
    "lullaby": ComfortItem(id="lullaby", label="tiny lullaby", prepares="sing a tiny lullaby", helps="make sleepy air"),
}

GIRL_NAMES = ["Maya", "Lily", "Nora", "Zoe", "Ella"]
BOY_NAMES = ["Leo", "Ben", "Finn", "Theo", "Sam"]


def valid_combos() -> list[tuple[str, str]]:
    return [(place, ball_id) for place in SETTINGS for ball_id in BALLS]


def asp_facts() -> str:
    import asp
    lines = []
    for sid, s in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        lines.append(asp.fact("kind", sid, s.kind))
        for a in sorted(s.affords):
            lines.append(asp.fact("affords", sid, a))
    for bid in BALLS:
        lines.append(asp.fact("ball", bid))
    for cid, c in COMFORTS.items():
        lines.append(asp.fact("comfort", cid))
        lines.append(asp.fact("helps", cid, c.helps.replace(" ", "_")))
    return "\n".join(lines)


ASP_RULES = r"""
valid(Place, Ball) :- setting(Place), ball(Ball), affords(Place, tuck), affords(Place, twist).
"""


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/2."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    print(" only in clingo:", sorted(cl - py))
    print(" only in python:", sorted(py - cl))
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Bedtime storyworld with a ball, a venetian blind, and a kindness twist.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--parent", choices=["mother", "father"])
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
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    parent = args.parent or rng.choice(["mother", "father"])
    return StoryParams(name=name, gender=gender, parent=parent, place=place)


def generate(params: StoryParams) -> StorySample:
    world = World(SETTINGS[params.place])
    child = world.add(Entity(id=params.name, kind="character", type=params.gender))
    parent = world.add(Entity(id="Parent", kind="character", type=params.parent))
    ball = world.add(Entity(id="ball", type="ball", label="ball", phrase="a shiny bedtime ball", owner=child.id))
    blind = world.add(Entity(id="blind", type="thing", label="venetian blind", phrase="a venetian blind that striped the moonlight"))
    blanket = world.add(Entity(id="blanket", type="thing", label="blanket", phrase="a soft blanket"))

    child.memes["joy"] = 1
    child.memes["want"] = 1
    world.say(f"{child.id} was a sleepy little {params.gender} who loved {ball.label} more than a yawn.")
    world.say(f"In {world.setting.place}, a venetian blind made silver stripes on the wall, and {ball.label} seemed to glow in them.")
    world.para()
    world.say(f"Near bedtime, {child.id} wanted to bounce the {ball.label} one more time.")
    world.say(f"{parent.pronoun('possessive').capitalize()} { 'mother' if params.parent == 'mother' else 'father' } smiled, but said the ball would keep the room awake.")
    world.say(f"{child.id} hugged the {ball.label} and whispered that bedtime felt too quick.")
    child.memes["wistful"] = 1
    world.para()
    world.say(f"Then came the kindness twist: {parent.pronoun('subject').capitalize()} suggested they could {COMFORTS['blanket'].prepares} and tell the {ball.label} goodnight first.")
    world.say(f"{child.id} tucked the {ball.label} into the soft blanket, and the room grew calm instead of bouncy.")
    world.say(f"With the venetian stripes dim and the {ball.label} cozy and still, {child.id} yawned and fell asleep with a gentle smile.")

    world.facts.update(child=child, parent=parent, ball=ball, blind=blind, blanket=blanket, params=params)
    story_qa = [
        QAItem(question=f"What did {params.name} want to do with the ball before bed?", answer=f"{params.name} wanted to bounce the ball one more time before sleep."),
        QAItem(question=f"What did the parent suggest instead?", answer="The parent suggested a kindness twist: wrap the ball in a soft blanket and tell it goodnight first."),
        QAItem(question=f"What made the room look striped and dreamy?", answer="A venetian blind made silver stripes of light on the wall."),
    ]
    world_qa = [
        QAItem(question="What is a ball?", answer="A ball is a round toy that can roll, bounce, and be caught."),
        QAItem(question="What is a venetian blind?", answer="A venetian blind is a window covering made of slats that can let in light in stripes."),
        QAItem(question="What does kindness mean?", answer="Kindness means being gentle, caring, and thinking about how to help someone feel safe or happy."),
        QAItem(question="What is a bedtime routine?", answer="A bedtime routine is a calm set of little actions that helps a child get ready to sleep."),
    ]
    prompts = [
        f"Write a bedtime story about a child named {params.name}, a ball, and a venetian blind.",
        "Tell a gentle story where kindness changes a noisy choice into a sleepy one.",
        "Write a short bedtime story with a small twist that ends calmly and warmly.",
    ]
    return StorySample(params=params, story=world.render(), prompts=prompts, story_qa=story_qa, world_qa=world_qa, world=world)


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world is not None:
        print("--- world model state ---")
        for e in sample.world.entities.values():
            print(f"{e.id}: {e.type}")
    if qa:
        print()
        for section, items in [("Prompts", sample.prompts), ("Story QA", [f"Q: {q.question}\nA: {q.answer}" for q in sample.story_qa]), ("World QA", [f"Q: {q.question}\nA: {q.answer}" for q in sample.world_qa])]:
            print(f"== {section} ==")
            for item in items:
                print(item)
            print()


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show valid/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible combos:")
        for place, ball in combos:
            print(place, ball)
        return

    base = args.seed if args.seed is not None else random.randrange(2**31)
    samples = []
    if args.all:
        samples = [generate(StoryParams(name="Maya", gender="girl", parent="mother", place=place)) for place in SETTINGS]
    else:
        for i in range(args.n):
            params = resolve_params(args, random.Random(base + i))
            params.seed = base + i
            samples.append(generate(params))
    if args.json:
        print(samples[0].to_json() if len(samples) == 1 else json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return
    for i, sample in enumerate(samples):
        emit(sample, trace=args.trace, qa=args.qa, header=f"### variant {i+1}" if len(samples) > 1 else "")


if __name__ == "__main__":
    main()

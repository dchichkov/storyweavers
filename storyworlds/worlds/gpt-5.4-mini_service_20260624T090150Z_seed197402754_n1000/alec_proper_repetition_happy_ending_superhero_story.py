#!/usr/bin/env python3
"""
A small superhero story world about Alec Proper, repetition, and a happy ending.

Seed tale:
---
Alec Proper was a careful little hero who lived in a bright city with a tall clock tower.
Every morning, he checked his cape, his gloves, and his tiny rescue kit before patrol.
One day, a gust of wind kept knocking the same parcel down the same alley.
Alec tried once, then again, then again. The parcel kept slipping away.
He noticed the alley had a loose drain cover that made the wheel of his cart wobble.
Alec fixed the drain cover, lifted the parcel properly, and carried it to the bakery.
The baker smiled, the street stayed tidy, and Alec Proper felt proud because he had solved the problem the right way.

World model:
---
- Physical meters: wind, wobble, dirt, damage, crowd_safety, parcel_safety, repair, pride
- Emotional memes: patience, confidence, concern, relief, joy, repetition

Narrative instruments:
---
- Repetition: the hero makes several attempts before noticing the real cause.
- Happy ending: the final state visibly improves and the city is safe again.
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
    label: str = ""
    type: str = "thing"
    plural: bool = False
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.kind == "character":
            if self.type in {"boy", "man", "hero"}:
                return {"subject": "he", "object": "him", "possessive": "his"}[case]
            if self.type in {"girl", "woman"}:
                return {"subject": "she", "object": "her", "possessive": "her"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str = "the city"
    detail: str = "bright streets and a tall clock tower"


@dataclass
class StoryParams:
    name: str = "Alec Proper"
    title: str = "proper"
    seed: Optional[int] = None


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[str] = set()
        self.facts: dict = {}

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


@dataclass
class Scenario:
    id: str
    repeated_action: str
    repeated_attempt: str
    fix_action: str
    problem: str
    danger: str
    resolution: str


SCENARIOS = {
    "parcel": Scenario(
        id="parcel",
        repeated_action="carry the parcel",
        repeated_attempt="pick up the parcel again",
        fix_action="lift the parcel over the wobbling drain",
        problem="the wheel kept sliding on the loose drain cover",
        danger="the parcel might bump into the bakery door and get damaged",
        resolution="the drain cover was set straight and the parcel stayed safe",
    ),
    "kite": Scenario(
        id="kite",
        repeated_action="catch the kite",
        repeated_attempt="run after the kite again",
        fix_action="tie the line to a steady pole",
        problem="the wind kept tugging the kite into the same broken corner",
        danger="the kite might tear on the sharp fence",
        resolution="the line stayed steady and the kite flew high and safe",
    ),
    "toy": Scenario(
        id="toy",
        repeated_action="rescue the toy car",
        repeated_attempt="reach for the toy car again",
        fix_action="clear the little ramp and guide the car properly",
        problem="the toy car kept rolling into the same crack",
        danger="the car might get scratched and the child would feel sad",
        resolution="the crack was covered and the toy car rolled home happily",
    ),
}

SETTINGS = {
    "city": Setting(place="the city", detail="bright streets, a bakery lane, and a tall clock tower"),
    "harbor": Setting(place="the harbor", detail="quiet docks, gulls overhead, and a long wooden pier"),
    "park": Setting(place="the park", detail="wide paths, a fountain, and a row of old trees"),
}


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Superhero story world: Alec Proper, repetition, and a happy ending.")
    ap.add_argument("--name", choices=["Alec Proper", "Alec"], default="Alec Proper")
    ap.add_argument("--scenario", choices=SCENARIOS, default=None)
    ap.add_argument("--place", choices=SETTINGS, default="city")
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
    scenario = args.scenario or rng.choice(list(SCENARIOS))
    name = args.name
    if name == "Alec":
        name = "Alec Proper"
    return StoryParams(name=name, title="proper", seed=args.seed)


def reasonableness_gate(params: StoryParams, scenario: Scenario) -> None:
    if not params.name.strip():
        raise StoryError("A hero name is required.")
    if scenario.id not in SCENARIOS:
        raise StoryError("Unknown scenario.")
    if "Proper" not in params.name and params.name != "Alec":
        raise StoryError("This world is about Alec Proper; use Alec or Alec Proper.")


ASP_RULES = r"""
hero(alec).
hero(proper).

scenario(parcel; kite; toy).

repeats(parcel) :- scenario(parcel).
repeats(kite) :- scenario(kite).
repeats(toy) :- scenario(toy).

happy_end(parcel) :- repeats(parcel).
happy_end(kite) :- repeats(kite).
happy_end(toy) :- repeats(toy).

valid_story(H, S) :- hero(H), scenario(S), repeats(S), happy_end(S).
#show valid_story/2.
#show repeats/1.
#show happy_end/1.
"""


def asp_facts() -> str:
    import asp
    lines = []
    lines.append(asp.fact("hero", "alec"))
    lines.append(asp.fact("hero", "proper"))
    for sid in SCENARIOS:
        lines.append(asp.fact("scenario", sid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show valid_story/2."))
    atoms = set(asp.atoms(model, "valid_story"))
    py = {("alec", sid) for sid in SCENARIOS}
    if atoms == py:
        print(f"OK: clingo matches Python gate ({len(py)} stories).")
        return 0
    print("MISMATCH")
    print("clingo:", sorted(atoms))
    print("python:", sorted(py))
    return 1


def build_world(params: StoryParams, scenario: Scenario, setting: Setting) -> World:
    world = World(setting)
    hero = world.add(Entity(id="hero", kind="character", label=params.name, type="hero"))
    parcel = world.add(Entity(id="parcel", label="parcel", type="package", owner=hero.id))
    city = world.add(Entity(id="city", label=setting.place, type="place"))

    hero.memes.update({"patience": 0.0, "confidence": 0.0, "concern": 0.0, "relief": 0.0, "joy": 0.0, "repetition": 0.0})
    parcel.meters.update({"parcel_safety": 1.0, "damage": 0.0})
    city.meters.update({"wind": 0.0, "wobble": 0.0, "crowd_safety": 1.0, "repair": 0.0, "pride": 0.0})

    world.say(f"{params.name} was a proper little superhero who watched over {setting.place}.")
    world.say(f"Every day, {params.name} checked the cape, the gloves, and the rescue kit before patrol.")
    world.say(f"{setting.place.capitalize()} had {setting.detail}.")
    world.para()

    hero.memes["concern"] += 1
    city.meters["wind"] += 1
    world.say(f"One day, {scenario.problem}.")
    world.say(f"{params.name} tried to {scenario.repeated_action}.")
    for i in range(3):
        hero.memes["repetition"] += 1
        world.say(f"{params.name} tried again, but the same trouble came back.")
    world.para()

    hero.memes["confidence"] += 1
    world.say(f"Then {params.name} looked closely and noticed the real cause: a loose drain cover under the wheel.")
    city.meters["wobble"] += 1
    city.meters["repair"] += 1
    world.say(f"{params.name} chose to {scenario.fix_action}.")
    parcel.meters["parcel_safety"] += 1
    parcel.meters["damage"] = 0.0
    city.meters["crowd_safety"] += 1
    city.meters["pride"] += 1
    hero.memes["relief"] += 1
    hero.memes["joy"] += 1
    world.say(f"At last, {scenario.resolution}.")
    world.say(f"Everyone in {setting.place} cheered because the problem had been solved properly.")
    world.say(f"{params.name} smiled, and the city felt safe and calm again.")

    world.facts.update(hero=hero, parcel=parcel, city=city, scenario=scenario, setting=setting)
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    scenario: Scenario = f["scenario"]
    return [
        f'Write a superhero story for a young child about {f["hero"].label}, repetition, and a happy ending.',
        f"Tell a gentle story where a proper hero keeps trying to {scenario.repeated_action} until the real cause is found.",
        f'Write a simple story that repeats the trouble three times and ends with a safe, happy ending.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    scenario: Scenario = f["scenario"]
    hero: Entity = f["hero"]
    setting: Setting = f["setting"]
    return [
        QAItem(
            question=f"Who is the story about?",
            answer=f"It is about {hero.label}, a proper little superhero who protects {setting.place}.",
        ),
        QAItem(
            question=f"What kept happening again and again?",
            answer=f"{scenario.problem.capitalize()}. {hero.label} tried three times, but the same trouble kept coming back until the real cause was found.",
        ),
        QAItem(
            question=f"What did {hero.label} do to fix the problem?",
            answer=f"{hero.label} noticed the loose drain cover and chose to {scenario.fix_action}, which made everything safe again.",
        ),
        QAItem(
            question=f"How did the story end?",
            answer=f"It ended happily: {scenario.resolution}. {hero.label} smiled, and the city was safe.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does a superhero do?",
            answer="A superhero helps people, solves problems, and tries to keep others safe.",
        ),
        QAItem(
            question="What is repetition in a story?",
            answer="Repetition means the story does the same action or idea more than once on purpose, so readers notice it.",
        ),
        QAItem(
            question="What is a happy ending?",
            answer="A happy ending is when the problem gets fixed and the characters feel safe, glad, or proud.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts ==",]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== (2) Story questions ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== (3) World knowledge questions ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for e in world.entities.values():
        bits = []
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        lines.append(f"  {e.id} ({e.type}) {' '.join(bits)}")
    return "\n".join(lines)


def generate(params: StoryParams) -> StorySample:
    scenario = SCENARIOS.get("parcel")
    setting = SETTINGS["city"]
    world = build_world(params, scenario, setting)
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
        print(asp_program("#show valid_story/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        model = asp.one_model(asp_program("#show valid_story/2."))
        print(asp.atoms(model, "valid_story"))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        for name in ["Alec Proper"]:
            params = StoryParams(name=name, title="proper", seed=base_seed)
            sample = generate(params)
            samples.append(sample)
    else:
        for i in range(max(1, args.n)):
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            scenario = SCENARIOS[args.scenario or "parcel"]
            reasonableness_gate(params, scenario)
            world = build_world(params, scenario, SETTINGS[args.place])
            sample = StorySample(
                params=params,
                story=world.render(),
                prompts=generation_prompts(world),
                story_qa=story_qa(world),
                world_qa=world_knowledge_qa(world),
                world=world,
            )
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

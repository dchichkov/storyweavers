#!/usr/bin/env python3
"""
snow_repetition_misunderstanding_kindness_tall_tale.py
======================================================

A small storyworld about snow, repeating mistakes, a kind correction, and a
big, tall-tale-style ending.

Seed tale shape:
---
A child keeps trying to build the biggest snow hill in town. Each time, the snow
slips, the hill falls, and everyone misunderstands what the child is trying to
make. A kindly helper notices the pattern, explains the trick, and lends a
hand. Together they make something even bigger than planned.

The world model tracks:
- physical meters: snow depth, heap size, warmth, wind drift, packedness
- emotional memes: excitement, confusion, embarrassment, kindness, trust
- repeated attempts at a snowy task
- a misunderstanding that is corrected by kindness
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
        if self.type in {"girl", "mother", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Place:
    name: str
    outdoors: bool = True
    wind: str = "blustery"
    affords: set[str] = field(default_factory=set)


@dataclass
class Task:
    id: str
    verb: str
    gerund: str
    retry: str
    material: str
    result: str
    zone: set[str]
    keyword: str
    tags: set[str] = field(default_factory=set)


@dataclass
class HelpfulThing:
    id: str
    label: str
    prep: str
    tail: str
    helps: set[str] = field(default_factory=set)
    covers: set[str] = field(default_factory=set)
    plural: bool = False


class World:
    def __init__(self, place: Place) -> None:
        self.place = place
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
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

    def copy(self) -> "World":
        import copy
        clone = World(self.place)
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        return clone

    def characters(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.kind == "character"]

    def worn_items(self, actor: Entity) -> list[Entity]:
        return [e for e in self.entities.values() if e.worn_by == actor.id]


@dataclass
class Rule:
    name: str
    apply: callable


def _r_slide(world: World) -> list[str]:
    out: list[str] = []
    for actor in world.characters():
        if actor.meters.get("trying", 0) < THRESHOLD:
            continue
        if actor.meters.get("snow", 0) < THRESHOLD:
            continue
        if actor.meters.get("packed", 0) >= THRESHOLD:
            continue
        sig = ("slide", actor.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        actor.memes["frustration"] = actor.memes.get("frustration", 0) + 1
        actor.meters["heap"] = max(0.0, actor.meters.get("heap", 0.0) - 1.0)
        out.append(f"The snow kept sliding off instead of staying piled up.")
    return out


def _r_misunderstanding(world: World) -> list[str]:
    out: list[str] = []
    for actor in world.characters():
        if actor.memes.get("frustration", 0) < THRESHOLD:
            continue
        if actor.memes.get("confusion", 0) >= THRESHOLD:
            continue
        sig = ("misunderstanding", actor.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        actor.memes["confusion"] = actor.memes.get("confusion", 0) + 1
        out.append(f"Everyone thought the child was making a mess, not a mountain.")
    return out


def _r_kindness(world: World) -> list[str]:
    out: list[str] = []
    for actor in world.characters():
        if actor.memes.get("confusion", 0) < THRESHOLD:
            continue
        if actor.memes.get("kindness", 0) >= THRESHOLD:
            continue
        for helper in world.characters():
            if helper.id == actor.id:
                continue
            if helper.memes.get("kindness", 0) < THRESHOLD:
                continue
            sig = ("kindness", actor.id, helper.id)
            if sig in world.fired:
                continue
            world.fired.add(sig)
            actor.memes["trust"] = actor.memes.get("trust", 0) + 1
            actor.memes["confusion"] = max(0.0, actor.memes.get("confusion", 0) - 1.0)
            actor.meters["packed"] = 1.0
            out.append(f"A kind helper showed the trick for packing the snow just right.")
            out.append(f"Together they pressed, patted, and piled until the hill stood tall.")
            return out
    return out


CAUSAL_RULES = [Rule("slide", _r_slide), Rule("misunderstanding", _r_misunderstanding), Rule("kindness", _r_kindness)]


def propagate(world: World, narrate: bool = True) -> list[str]:
    out: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            lines = rule.apply(world)
            if lines:
                changed = True
                out.extend(lines)
    if narrate:
        for line in out:
            world.say(line)
    return out


def tall_tale_opening(hero: Entity, place: Place) -> str:
    return f"{hero.id} was a little {hero.type} with a big idea and a bigger laugh, and on snowy days {hero.pronoun()} could chase a dream all the way to {place.name}."


def describe_snow(place: Place) -> str:
    return f"The snow lay so deep and bright at {place.name} that even the fence posts looked like they were wearing white hats."


def attempt_line(hero: Entity, task: Task) -> str:
    return f"{hero.pronoun().capitalize()} tried to {task.verb}, tried again, and tried once more, because the snow was stubborn and the dream was tall."


def misunderstanding_line(helper: Entity, hero: Entity) -> str:
    return f"{helper.id} thought {hero.id} was making trouble, but really {hero.pronoun()} was making a miracle."


def ending_line(hero: Entity, task: Task) -> str:
    return f"In the end, {hero.id} had {task.gerund} done the right way, and the snow hill stood so high it looked like it might tickle the moon."


def predict(world: World, hero: Entity, task: Task) -> dict:
    sim = world.copy()
    sim.get(hero.id).meters["trying"] = 1.0
    sim.get(hero.id).meters["snow"] = 1.0
    propagate(sim, narrate=False)
    return {
        "misunderstanding": sim.get(hero.id).memes.get("confusion", 0) >= THRESHOLD,
        "packed": sim.get(hero.id).meters.get("packed", 0) >= THRESHOLD,
    }


def tell(place: Place, task: Task, hero_name: str, hero_type: str, helper_type: str) -> World:
    world = World(place)
    hero = world.add(Entity(id=hero_name, kind="character", type=hero_type))
    helper = world.add(Entity(id="Mabel", kind="character", type=helper_type))
    hero.meters["snow"] = 2.0
    hero.meters["trying"] = 1.0
    hero.meters["heap"] = 1.0
    hero.memes["excitement"] = 2.0
    helper.memes["kindness"] = 1.0

    world.say(tall_tale_opening(hero, place))
    world.say(describe_snow(place))
    world.say(f"{hero.id} wanted to {task.verb} and make the biggest {task.keyword} in the county, maybe the state, maybe the whole snowy side of the sky.")
    world.para()
    world.say(attempt_line(hero, task))
    world.say(f"But every time {hero.id} reached high, the snow puffed and slipped away with a whisk and a whoosh.")
    propagate(world, narrate=True)
    world.para()
    pred = predict(world, hero, task)
    if pred["misunderstanding"]:
        hero.memes["confusion"] = 1.0
        world.say(misunderstanding_line(helper, hero))
        world.say(f"{helper.id} came closer, smiled, and said, 'You do not need more force. You need more packing.'")
        helper.memes["kindness"] += 1.0
        hero.memes["kindness"] = hero.memes.get("kindness", 0) + 1.0
        propagate(world, narrate=True)
    world.para()
    hero.meters["packed"] = 1.0
    hero.meters["heap"] = 3.0
    hero.meters["snow"] = 3.0
    world.say(f"{hero.id} patted the snow like a baker patting dough, and {helper.id} handed over mittenfuls of fresh snow with a grin.")
    propagate(world, narrate=True)
    world.say(ending_line(hero, task))
    world.say(f"{hero.id} and {helper.id} stood beside the grand white hill, small as breadcrumbs next to a wedding cake, and laughed at how a misunderstanding had turned into a kindness-big ending.")
    world.facts.update(hero=hero, helper=helper, task=task, place=place)
    return world


PLACES = {
    "hill": Place(name="the hill", outdoors=True, wind="blustery", affords={"snowhill"}),
    "yard": Place(name="the yard", outdoors=True, wind="nippy", affords={"snowhill"}),
    "field": Place(name="the field", outdoors=True, wind="wild", affords={"snowhill"}),
}

TASKS = {
    "snowhill": Task(
        id="snowhill",
        verb="build the tallest snow hill",
        gerund="building the tallest snow hill",
        retry="pack the snow tighter",
        material="snow",
        result="a towering hill",
        zone={"hands"},
        keyword="snow",
        tags={"snow", "kindness", "misunderstanding", "repetition"},
    )
}

GIRL_NAMES = ["Mabel", "Nell", "June", "Ruby", "Ivy", "Lula"]
BOY_NAMES = ["Otis", "Eli", "Cal", "Finn", "Bram", "Jude"]


@dataclass
class StoryParams:
    place: str
    task: str
    name: str
    gender: str
    helper_gender: str
    seed: Optional[int] = None


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Tall tale snow storyworld with repetition, misunderstanding, and kindness.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--task", choices=TASKS)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--helper-gender", choices=["girl", "boy"])
    ap.add_argument("--name")
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
    place = args.place or rng.choice(list(PLACES))
    task = args.task or "snowhill"
    gender = args.gender or rng.choice(["girl", "boy"])
    helper_gender = args.helper_gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    return StoryParams(place=place, task=task, name=name, gender=gender, helper_gender=helper_gender)


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    return [
        f'Write a tall tale for young children about snow, repetition, misunderstanding, and kindness.',
        f"Tell a snowy story where {hero.id} keeps trying again and again until a kind helper shows a better way.",
        f"Write a short story about a child who misunderstands the snow at first but ends with a big, happy hill.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero, helper, task, place = f["hero"], f["helper"], f["task"], f["place"]
    return [
        QAItem(
            question=f"What was {hero.id} trying to make at {place.name}?",
            answer=f"{hero.id} was trying to make {task.result} by {task.verb} in the snow."
        ),
        QAItem(
            question=f"Why did {helper.id} come over to help?",
            answer=f"{helper.id} noticed the same problem happening over and over, and the snow kept slipping instead of staying piled up."
        ),
        QAItem(
            question=f"What changed after the kind helper showed the trick?",
            answer=f"After the helper showed how to pack the snow, {hero.id} could keep building, and the hill stood tall at the end."
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is snow?",
            answer="Snow is frozen water that falls from clouds and can pile up on the ground in soft, cold flakes."
        ),
        QAItem(
            question="Why do people pack snow into a snowball or snow hill?",
            answer="People pack snow so it sticks together better instead of falling apart."
        ),
        QAItem(
            question="What does kindness mean?",
            answer="Kindness means helping in a gentle, caring way and trying to make someone else feel better."
        ),
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
    for e in world.entities.values():
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        parts = []
        if meters:
            parts.append(f"meters={dict(meters)}")
        if memes:
            parts.append(f"memes={dict(memes)}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(parts)}")
    lines.append(f"  fired rules: {sorted({n for n, *_ in world.fired})}")
    return "\n".join(lines)


CURATED = [
    StoryParams(place="hill", task="snowhill", name="Mabel", gender="girl", helper_gender="boy"),
    StoryParams(place="yard", task="snowhill", name="Otis", gender="boy", helper_gender="girl"),
    StoryParams(place="field", task="snowhill", name="June", gender="girl", helper_gender="girl"),
]


ASP_RULES = r"""
repetition(hero) :- tries(hero, N), N >= 2.
misunderstanding(hero) :- confusion(hero).
kindness(hero) :- helped(hero).
good_story(hero) :- repetition(hero), misunderstanding(hero), kindness(hero).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for pid, place in PLACES.items():
        lines.append(asp.fact("place", pid))
        if place.outdoors:
            lines.append(asp.fact("outdoors", pid))
        for a in sorted(place.affords):
            lines.append(asp.fact("affords", pid, a))
    for tid, task in TASKS.items():
        lines.append(asp.fact("task", tid))
        lines.append(asp.fact("keyword", tid, task.keyword))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show good_story/1."))
    clingo = set(asp.atoms(model, "good_story"))
    python = {("hero",)}
    if clingo == python:
        print("OK: clingo gate matches python gate.")
        return 0
    print("MISMATCH between clingo and python gate.")
    return 1


def generate(params: StoryParams) -> StorySample:
    place = PLACES[params.place]
    task = TASKS[params.task]
    world = tell(place, task, params.name, params.gender, params.helper_gender)
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
        print(asp_program("#show good_story/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print("ASP mode is available for this world, but the core story engine is the primary path.")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(p) for p in CURATED]
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
            header = f"### {p.name}: {p.task} at {p.place}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260623T074642Z_seed779406221_n50/hip_addition_inner_monologue_kindness_superhero_story.py
================================================================================================

A small standalone storyworld in a superhero style.

Seed ingredients:
- hip
- addition
- Inner Monologue
- Kindness
- Superhero Story

The world is deliberately tiny: a young hero prepares for an addition challenge
while protecting a sore hip. A kind helper and the hero's inner monologue drive
the turn from frustration to a gentle, successful ending.
"""

from __future__ import annotations

import argparse
import copy
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
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)
    traits: list[str] = field(default_factory=list)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "woman", "mother"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man", "father"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]


@dataclass
class World:
    place: str
    entities: dict[str, Entity] = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    facts: dict = field(default_factory=dict)

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
        clone = World(self.place)
        clone.entities = copy.deepcopy(self.entities)
        clone.paragraphs = [[]]
        clone.facts = copy.deepcopy(self.facts)
        return clone


@dataclass
class StoryParams:
    place: str
    hero_name: str
    hero_type: str
    helper_name: str
    helper_type: str
    activity: str
    seed: Optional[int] = None


PLACES = {
    "schoolyard": "the schoolyard",
    "rooftop": "the rooftop",
    "library": "the city library",
    "park": "the park",
}

HEROES = {
    "girl": ["Mina", "Ivy", "Tara", "Nora"],
    "boy": ["Theo", "Ben", "Finn", "Leo"],
}

HELPERS = {
    "girl": ["Ruby", "Mila", "June"],
    "boy": ["Kai", "Noah", "Owen"],
}

ACTIONS = {
    "addition": {
        "verb": "solve the addition problem",
        "noun": "addition problem",
        "tool": "number cards",
        "challenge": "the numbers on the page kept shuffling in their head",
        "inner": "I can do this if I slow down and check one number at a time.",
        "turn": "the numbers lined up like little lights",
    }
}

CURATED = [
    StoryParams(place="schoolyard", hero_name="Mina", hero_type="girl",
                helper_name="Ruby", helper_type="girl", activity="addition"),
    StoryParams(place="rooftop", hero_name="Theo", hero_type="boy",
                helper_name="Kai", helper_type="boy", activity="addition"),
    StoryParams(place="library", hero_name="Ivy", hero_type="girl",
                helper_name="June", helper_type="girl", activity="addition"),
]


class WorldGate:
    @staticmethod
    def reasonableness(place: str, activity: str) -> None:
        if activity != "addition":
            raise StoryError("This tiny world only supports the addition story.")
        if place not in PLACES:
            raise StoryError("Unknown place for this storyworld.")


def build_world(params: StoryParams) -> World:
    world = World(PLACES[params.place])
    hero = world.add(Entity(
        id="hero",
        kind="character",
        type=params.hero_type,
        label=params.hero_name,
        traits=["little", "brave"],
    ))
    helper = world.add(Entity(
        id="helper",
        kind="character",
        type=params.helper_type,
        label=params.helper_name,
        traits=["kind", "steady"],
    ))
    problem = world.add(Entity(
        id="problem",
        kind="thing",
        type="paper",
        label="addition sheet",
        phrase="a bright addition sheet with two rows of stars",
        caretaker=helper.id,
    ))
    hero.meters["hip"] = 1.0
    hero.memes["worry"] = 1.0
    world.facts.update(hero=hero, helper=helper, problem=problem, params=params)
    return world


def inner_monologue(world: World, hero: Entity, action: dict) -> None:
    world.say(
        f"{hero.label} tightened up when {hero.pronoun('possessive')} hip felt sore, "
        f"and {hero.pronoun('subject')} thought, \"{action['inner']}\""
    )


def kind_help(world: World, helper: Entity, hero: Entity, action: dict) -> None:
    helper.memes["kindness"] = helper.memes.get("kindness", 0.0) + 1.0
    hero.memes["calm"] = hero.memes.get("calm", 0.0) + 1.0
    hero.meters["hip"] = max(0.0, hero.meters.get("hip", 0.0) - 0.5)
    world.say(
        f"{helper.label} noticed the careful face and slid over the number cards. "
        f"\"Let's do it one small step at a time,\" {helper.pronoun()} said."
    )


def solve_addition(world: World, hero: Entity, helper: Entity, action: dict) -> None:
    hero.memes["confidence"] = hero.memes.get("confidence", 0.0) + 1.0
    world.say(
        f"{hero.label} took a slow breath, counted each dot, and answered the "
        f"{action['noun']} by matching every group. {action['turn'].capitalize()}."
    )
    world.say(
        f"{helper.label} smiled beside {hero.pronoun('object')}, and the sore hip felt "
        f"small compared with the new win."
    )


def tell(place: str, hero_name: str, hero_type: str, helper_name: str, helper_type: str,
         activity: str) -> World:
    world = build_world(StoryParams(place, hero_name, hero_type, helper_name, helper_type, activity))
    hero = world.get("hero")
    helper = world.get("helper")
    action = ACTIONS[activity]

    world.say(
        f"{hero.label} was a little superhero who loved helping people in {world.place}."
    )
    world.say(
        f"{hero.label} had a brave cape, a sore hip, and a big wish to {action['verb']}."
    )
    world.para()
    world.say(
        f"At {world.place}, the {action['noun']} looked tricky because {action['challenge']}."
    )
    inner_monologue(world, hero, action)
    world.say(
        f"{hero.label} almost gave up, but {helper.label} came close with a kind grin."
    )
    kind_help(world, helper, hero, action)
    world.para()
    solve_addition(world, hero, helper, action)
    world.say(
        f"By the end, {hero.label} stood tall again, hip and heart both steadier, "
        f"and the city felt a little brighter."
    )
    return world


def generation_prompts(world: World) -> list[str]:
    p = world.facts["params"]
    return [
        f"Write a short superhero story set at {PLACES[p.place]} about {p.hero_name} and a kind helper.",
        f"Tell a child-friendly story where a sore hip makes an addition task hard, but kindness helps.",
        f"Write a story with inner monologue, courage, and a gentle ending about addition.",
    ]


def story_qa(world: World) -> list[QAItem]:
    hero = world.facts["hero"]
    helper = world.facts["helper"]
    problem = world.facts["problem"]
    return [
        QAItem(
            question=f"Who is the story about?",
            answer=f"The story is about {hero.label}, a little superhero who tries to solve an addition problem."
        ),
        QAItem(
            question=f"Why did {hero.label} need help?",
            answer=f"{hero.label} needed help because {hero.pronoun('possessive')} hip felt sore and the addition sheet looked hard at first."
        ),
        QAItem(
            question=f"How did {helper.label} help?",
            answer=f"{helper.label} helped by being kind, giving the number cards, and asking {hero.label} to take the problem one small step at a time."
        ),
        QAItem(
            question=f"What changed at the end?",
            answer=f"At the end, {hero.label} felt calmer and stronger, and the addition problem was solved."
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is addition?",
            answer="Addition is when you put numbers together to find a bigger total."
        ),
        QAItem(
            question="What is a hip?",
            answer="A hip is the part of the body on the side that helps a person sit, stand, and walk."
        ),
        QAItem(
            question="What does kindness mean?",
            answer="Kindness means being gentle, helpful, and caring toward someone else."
        ),
    ]


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        bits = []
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        if e.traits:
            bits.append(f"traits={e.traits}")
        lines.append(f"  {e.id}: {e.label} ({e.type}) {' '.join(bits)}")
    return "\n".join(lines)


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Superhero storyworld about hip, addition, inner monologue, and kindness.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--name")
    ap.add_argument("--helper")
    ap.add_argument("--activity", choices=ACTIONS)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--helper-gender", choices=["girl", "boy"])
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
    WorldGate.reasonableness(args.place or "park", args.activity or "addition")
    gender = args.gender or rng.choice(["girl", "boy"])
    helper_gender = args.helper_gender or rng.choice(["girl", "boy"])
    place = args.place or rng.choice(list(PLACES))
    hero_name = args.name or rng.choice(HEROES[gender])
    helper_name = args.helper or rng.choice(HELPERS[helper_gender])
    return StoryParams(place=place, hero_name=hero_name, hero_type=gender,
                       helper_name=helper_name, helper_type=helper_gender,
                       activity=args.activity or "addition")


def generate(params: StoryParams) -> StorySample:
    world = tell(params.place, params.hero_name, params.hero_type, params.helper_name, params.helper_type, params.activity)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


def format_qa(sample: StorySample) -> str:
    out = ["== prompts =="]
    out.extend(f"{i}. {p}" for i, p in enumerate(sample.prompts, 1))
    out.append("")
    out.append("== story qa ==")
    for item in sample.story_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    out.append("")
    out.append("== world qa ==")
    for item in sample.world_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    return "\n".join(out)


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world is not None:
        print(dump_trace(sample.world))
    if qa:
        print()
        print(format_qa(sample))


ASP_RULES = r"""
selected_place(P) :- place(P).
selected_activity(A) :- activity(A).
compatible(P,A) :- selected_place(P), selected_activity(A), place_supports(P,A).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for p in PLACES:
        lines.append(asp.fact("place", p))
    lines.append(asp.fact("activity", "addition"))
    for p in PLACES:
        lines.append(asp.fact("place_supports", p, "addition"))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show compatible/2."))
    got = set(asp.atoms(model, "compatible"))
    want = {(p, "addition") for p in PLACES}
    if got == want:
        print(f"OK: clingo gate matches Python world ({len(got)} combos).")
        return 0
    print("MISMATCH")
    print("only in clingo:", sorted(got - want))
    print("only in python:", sorted(want - got))
    return 1


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show compatible/2."))
        return
    if args.verify:
        sys.exit(asp_verify())

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)
    samples: list[StorySample] = []
    if args.all:
        curated = [
            StoryParams(place="schoolyard", hero_name="Mina", hero_type="girl", helper_name="Ruby", helper_type="girl", activity="addition"),
            StoryParams(place="rooftop", hero_name="Theo", hero_type="boy", helper_name="Kai", helper_type="boy", activity="addition"),
            StoryParams(place="library", hero_name="Ivy", hero_type="girl", helper_name="June", helper_type="girl", activity="addition"),
        ]
        samples = [generate(p) for p in curated]
    else:
        seen = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 20):
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            sample = generate(params)
            if sample.story in seen:
                i += 1
                continue
            seen.add(sample.story)
            samples.append(sample)
            i += 1

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

#!/usr/bin/env python3
"""
Standalone story world: competence, pastrami, teamwork, and a small adventure.

A child-friendly adventure premise:
A young helper wants to make a special pastrami sandwich for a picnic, but the
job is too tricky for one pair of hands. The story turns on competence growing
through teamwork: one character can slice, another can carry, and together they
finish a small quest with a happy ending.
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
# Domain model
# ---------------------------------------------------------------------------

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
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.meters:
            self.meters = {"weight": 0.0}
        if not self.memes:
            self.memes = {"joy": 0.0, "worry": 0.0, "competence": 0.0, "teamwork": 0.0}

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "mother", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Place:
    name: str
    feel: str
    afford: set[str] = field(default_factory=set)


@dataclass
class Task:
    id: str
    verb: str
    gerund: str
    challenge: str
    success: str
    requires: set[str] = field(default_factory=set)
    tags: set[str] = field(default_factory=set)


@dataclass
class Tool:
    id: str
    label: str
    help_text: str
    covers: set[str] = field(default_factory=set)
    tags: set[str] = field(default_factory=set)
    plural: bool = False


class World:
    def __init__(self, place: Place) -> None:
        self.place = place
        self.entities: dict[str, Entity] = {}
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


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------

PLACES = {
    "deli": Place(name="the little deli", feel="busy", afford={"make_sandwich"}),
    "kitchen": Place(name="the kitchen", feel="warm", afford={"make_sandwich"}),
    "camp": Place(name="the camp picnic table", feel="open", afford={"make_sandwich"}),
}

TASKS = {
    "make_sandwich": Task(
        id="make_sandwich",
        verb="make the pastrami sandwich",
        gerund="making the pastrami sandwich",
        challenge="the slices were slippery and the stack was too tall",
        success="the sandwich held together neatly",
        requires={"knife", "plate", "teamwork"},
        tags={"pastrami", "teamwork", "competence"},
    )
}

TOOLS = {
    "knife": Tool(id="knife", label="a small knife", help_text="carefully slice the pastrami", tags={"pastrami"}),
    "plate": Tool(id="plate", label="a wide plate", help_text="hold the layers steady", tags={"pastrami"}),
    "napkin": Tool(id="napkin", label="a clean napkin", help_text="keep sticky fingers clean", tags={"teamwork"}),
}

GIRL_NAMES = ["Mia", "Lena", "Ava", "Nora", "Ivy"]
BOY_NAMES = ["Owen", "Theo", "Max", "Eli", "Noah"]
TRAITS = ["brave", "curious", "careful", "kind", "cheerful"]


# ---------------------------------------------------------------------------
# Story parameters
# ---------------------------------------------------------------------------

@dataclass
class StoryParams:
    place: str
    task: str
    hero: str
    hero_gender: str
    partner: str
    partner_gender: str
    trait: str
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# World building and narration
# ---------------------------------------------------------------------------

class StoryWorld(World):
    pass


def _name_for_gender(gender: str, rng: random.Random) -> str:
    return rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)


def build_world(params: StoryParams) -> StoryWorld:
    world = StoryWorld(PLACES[params.place])
    hero = world.add(Entity(id=params.hero, kind="character", type=params.hero_gender))
    partner = world.add(Entity(id=params.partner, kind="character", type=params.partner_gender))
    sandwich = world.add(Entity(id="sandwich", type="sandwich", label="pastrami sandwich", phrase="a pastrami sandwich", owner=hero.id))
    knife = world.add(Entity(id="knife", type="tool", label="knife", phrase="a small knife"))
    plate = world.add(Entity(id="plate", type="tool", label="plate", phrase="a wide plate"))
    napkin = world.add(Entity(id="napkin", type="tool", label="napkin", phrase="a clean napkin"))

    task = TASKS[params.task]
    world.facts.update(hero=hero, partner=partner, sandwich=sandwich, knife=knife, plate=plate, napkin=napkin, task=task, place=world.place, params=params)

    # Act 1: setup
    world.say(f"{hero.id} was a {params.trait} little {hero.type} who loved adventure and good food.")
    world.say(f"{hero.id} especially loved pastrami because it smelled smoky and salty, like a tiny feast.")
    world.say(f"One day, {hero.id} and {partner.id} went to {world.place.name}, where a special picnic was waiting.")

    # Act 2: tension
    world.para()
    world.say(f"{hero.id} wanted to {task.verb}, but {task.challenge}.")
    world.say(f"{hero.id} tried to do it alone at first, yet the stack wobbled and the slices slid apart.")
    hero.memes["worry"] += 1
    hero.memes["competence"] += 0.5
    partner.memes["teamwork"] += 1

    # Turn: teamwork
    world.say(f"Then {partner.id} smiled and said, 'Let's work together.'")
    world.say(f"{partner.id} held the {plate.label} steady while {hero.id} used {knife.label} to slice carefully.")
    world.say(f"{hero.id} learned that competence was not just doing things fast; it was doing them well with help.")
    hero.memes["teamwork"] += 1
    hero.memes["competence"] += 1
    partner.memes["competence"] += 0.5
    partner.memes["joy"] += 1
    hero.memes["joy"] += 1

    # Act 3: resolution
    world.para()
    world.say(f"Together they stacked the pastrami, folded a napkin around the edges, and made the sandwich neat.")
    world.say(f"At last, {task.success}.")
    world.say(f"{hero.id} and {partner.id} carried it to the picnic table, proud as explorers returning with treasure.")
    world.say(f"Their teamwork had turned a tricky job into a small adventure, and the pastrami sandwich stayed whole and ready to share.")

    world.facts["resolved"] = True
    return world


# ---------------------------------------------------------------------------
# Q&A
# ---------------------------------------------------------------------------

def generation_prompts(world: StoryWorld) -> list[str]:
    p = world.facts["params"]
    task = world.facts["task"]
    return [
        f"Write a short adventure story for a young child about {p.hero} and {p.partner} learning competence through teamwork.",
        f"Tell a gentle story in which two helpers try to {task.verb} and use pastrami in a fun, concrete way.",
        f"Write a child-friendly tale where a tricky food task becomes easier because the characters work together.",
    ]


def story_qa(world: StoryWorld) -> list[QAItem]:
    p = world.facts["params"]
    hero = world.facts["hero"]
    partner = world.facts["partner"]
    task = world.facts["task"]
    place = world.facts["place"]
    return [
        QAItem(
            question=f"What did {hero.id} want to do at {place.name}?",
            answer=f"{hero.id} wanted to {task.verb}.",
        ),
        QAItem(
            question=f"Why did {hero.id} need help?",
            answer=f"{task.challenge.capitalize()} So {hero.id} needed teamwork to finish the job safely.",
        ),
        QAItem(
            question=f"How did {partner.id} help?",
            answer=f"{partner.id} held the plate steady and helped {hero.id} slice the pastrami carefully.",
        ),
        QAItem(
            question=f"What did {hero.id} learn in the story?",
            answer=f"{hero.id} learned that competence grows when helpers work together and stay calm.",
        ),
    ]


def world_knowledge_qa(world: StoryWorld) -> list[QAItem]:
    return [
        QAItem(
            question="What is pastrami?",
            answer="Pastrami is a cooked meat that people often put in sandwiches, and it usually tastes savory and smoky.",
        ),
        QAItem(
            question="What does teamwork mean?",
            answer="Teamwork means people help each other and share the work so a hard job becomes easier.",
        ),
        QAItem(
            question="What does competence mean?",
            answer="Competence means being able to do something well, especially after practice, care, or good help.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== story questions ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== world knowledge questions ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------

ASP_RULES = r"""
place(deli). place(kitchen). place(camp).
task(make_sandwich).
requires(make_sandwich,knife). requires(make_sandwich,plate). requires(make_sandwich,teamwork).
tool(knife). tool(plate). tool(napkin).
tag(make_sandwich,pastrami). tag(make_sandwich,teamwork). tag(make_sandwich,competence).

helpful(T, make_sandwich) :- tag(make_sandwich, T), tool_or_skill(T).
tool_or_skill(knife). tool_or_skill(plate). tool_or_skill(teamwork).

valid_story(P, make_sandwich) :- place(P), task(make_sandwich).
#show valid_story/2.
"""

def asp_facts() -> str:
    import asp
    lines = []
    for pid in PLACES:
        lines.append(asp.fact("place", pid))
    for tid, task in TASKS.items():
        lines.append(asp.fact("task", tid))
        for req in sorted(task.requires):
            lines.append(asp.fact("requires", tid, req))
        for tag in sorted(task.tags):
            lines.append(asp.fact("tag", tid, tag))
    for tid in TOOLS:
        lines.append(asp.fact("tool", tid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show valid_story/2."))
    clingo_set = set(asp.atoms(model, "valid_story"))
    python_set = {(place, "make_sandwich") for place in PLACES}
    if clingo_set == python_set:
        print(f"OK: clingo gate matches python ({len(clingo_set)} stories).")
        return 0
    print("MISMATCH:")
    print("clingo:", sorted(clingo_set))
    print("python:", sorted(python_set))
    return 1


# ---------------------------------------------------------------------------
# Generation
# ---------------------------------------------------------------------------

def valid_places() -> list[str]:
    return [k for k, v in PLACES.items() if "make_sandwich" in v.afford]


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    place = args.place or rng.choice(valid_places())
    if place not in PLACES:
        raise StoryError("Unknown place.")
    task = args.task or "make_sandwich"
    if task not in TASKS:
        raise StoryError("Unknown task.")
    hero_gender = args.gender or rng.choice(["girl", "boy"])
    partner_gender = args.partner_gender or ("boy" if hero_gender == "girl" else "girl")
    hero = args.hero or _name_for_gender(hero_gender, rng)
    partner = args.partner or _name_for_gender(partner_gender, rng)
    if hero == partner:
        partner = _name_for_gender(partner_gender, rng)
    trait = args.trait or rng.choice(TRAITS)
    return StoryParams(place=place, task=task, hero=hero, hero_gender=hero_gender, partner=partner, partner_gender=partner_gender, trait=trait)


def generate(params: StoryParams) -> StorySample:
    world = build_world(params)
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
        print("\n--- trace ---")
        hero = sample.world.facts["hero"]
        partner = sample.world.facts["partner"]
        print(f"hero.competence={hero.memes.get('competence', 0)} hero.teamwork={hero.memes.get('teamwork', 0)}")
        print(f"partner.competence={partner.memes.get('competence', 0)} partner.teamwork={partner.memes.get('teamwork', 0)}")
    if qa:
        print()
        print(format_qa(sample))


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Adventure story world about competence, pastrami, and teamwork.")
    ap.add_argument("--place", choices=sorted(PLACES))
    ap.add_argument("--task", choices=sorted(TASKS))
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--partner-gender", choices=["girl", "boy"])
    ap.add_argument("--hero")
    ap.add_argument("--partner")
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
        print(sorted(set(asp.atoms(model, "valid_story"))))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        i = 0
        for place in sorted(PLACES):
            params = StoryParams(
                place=place,
                task="make_sandwich",
                hero=_name_for_gender("girl", random.Random(base_seed + i)),
                hero_gender="girl",
                partner=_name_for_gender("boy", random.Random(base_seed + i + 1)),
                partner_gender="boy",
                trait=random.Random(base_seed + i + 2).choice(TRAITS),
                seed=base_seed + i,
            )
            samples.append(generate(params))
            i += 3
    else:
        seen: set[str] = set()
        attempts = 0
        while len(samples) < args.n and attempts < max(50, args.n * 20):
            seed = base_seed + attempts
            attempts += 1
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

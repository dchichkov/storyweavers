#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260626T060043Z_seed274930118_n5000/pull_hypothesis_problem_solving_foreshadowing_animal_story.py
===============================================================================================================

A tiny animal-story world about a small problem, a helpful hypothesis, and a
careful pull that solves it.

Premise:
- An animal notices a stuck object or friend in a small natural place.
- A first clue foreshadows the problem before it becomes obvious.
- The animal forms a hypothesis about what is wrong.
- The animal tries a reasonable pull-based fix.
- The story ends with the problem solved and the world visibly changed.

This script is self-contained and follows the Storyweavers world contract.
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
    kind: str = "thing"   # "character" | "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    plural: bool = False
    owner: Optional[str] = None
    partner: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.kind != "character":
            return {"subject": "it", "object": "it", "possessive": "its"}[case]
        gender = self.type
        if gender in {"fox", "wolf", "bear", "otter", "rabbit", "squirrel"}:
            return {"subject": "it", "object": "it", "possessive": "its"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def name_or_label(self) -> str:
        return self.label or self.id

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Place:
    name: str
    setting: str
    afford: str
    clue: str
    weather: str = ""


@dataclass
class Problem:
    id: str
    label: str
    phrase: str
    stuck_word: str
    pull_target: str
    danger: str
    foreshadow: str
    hypothesis: str
    solution: str
    solved_image: str


@dataclass
class StoryParams:
    place: str
    problem: str
    hero: str
    helper: str
    seed: Optional[int] = None


class World:
    def __init__(self, place: Place) -> None:
        self.place = place
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.events: list[str] = []

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str) -> Entity:
        return self.entities[eid]

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)
            self.events.append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)

    def copy(self) -> "World":
        import copy
        clone = World(self.place)
        clone.entities = copy.deepcopy(self.entities)
        clone.paragraphs = [[]]
        clone.facts = dict(self.facts)
        clone.events = list(self.events)
        return clone


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------

PLACES = {
    "riverbank": Place(
        name="the riverbank",
        setting="a bright riverbank with reeds",
        afford="pull",
        clue="the reeds leaned the same way as the current",
        weather="sunny",
    ),
    "burrow": Place(
        name="the burrow entrance",
        setting="a sandy burrow entrance under a root",
        afford="pull",
        clue="tiny scratches lined the dirt near the tunnel",
        weather="",
    ),
    "pond": Place(
        name="the pond edge",
        setting="a quiet pond edge with lily pads",
        afford="pull",
        clue="one lily pad kept bobbing in place",
        weather="misty",
    ),
    "meadow": Place(
        name="the meadow path",
        setting="a soft meadow path between tall grass",
        afford="pull",
        clue="a bent stem pointed toward the path stones",
        weather="breezy",
    ),
}

PROBLEMS = {
    "knot": Problem(
        id="knot",
        label="a tangled vine",
        phrase="a thick vine wrapped around a branch",
        stuck_word="stuck",
        pull_target="the vine",
        danger="the sap would gum up the leaves",
        foreshadow="The vine had a little twist in it, like it had been tugged before.",
        hypothesis="The vine was looped under the branch, so it would come free if pulled the right way.",
        solution="The animal pulled slowly, then switched to a gentle sideways tug.",
        solved_image="the vine slid loose and the branch sprang up again",
    ),
    "basket",
    : Problem(
        id="basket",
        label="a reed basket",
        phrase="a reed basket caught on a root",
        stuck_word="stuck",
        pull_target="the basket handle",
        danger="the basket might tear if yanked too hard",
        foreshadow="One handle hung lower than the other, as if it had snagged below.",
        hypothesis="The basket was hooked on a root, so a careful lift and pull would free it.",
        solution="The animal lifted one side, then gave the handle a steady pull.",
        solved_image="the basket popped free and rolled safely onto the path",
    ),
    "boat": Problem(
        id="boat",
        label="a little boat",
        phrase="a little boat nudged against mud",
        stuck_word="stuck",
        pull_target="the rope",
        danger="the rope kept the boat from drifting away",
        foreshadow="The rope had gone tight before the boat stopped moving.",
        hypothesis="The boat was pinned by mud, so pulling the rope while rocking it would help.",
        solution="The animal rocked the boat, then pulled the rope in one strong, sure motion.",
        solved_image="the boat drifted back into the water with a happy splash",
    ),
    "nest": Problem(
        id="nest",
        label="a nest basket",
        phrase="a nest basket tangled in grass",
        stuck_word="stuck",
        pull_target="the grass",
        danger="the eggs nearby should not be bumped",
        foreshadow="A few blades of grass were bent into a neat little arch.",
        hypothesis="The basket was snagged by grass, so pulling the grass apart would open a path.",
        solution="The animal parted the grass first, then pulled the basket free with care.",
        solved_image="the basket came loose and sat snug and safe on the ground",
    ),
}

HEROES = {
    "rabbit": {"name": "Ruby", "kind": "character", "type": "rabbit", "trait": "curious"},
    "fox": {"name": "Finn", "kind": "character", "type": "fox", "trait": "thoughtful"},
    "otter": {"name": "Pip", "kind": "character", "type": "otter", "trait": "playful"},
    "squirrel": {"name": "Sora", "kind": "character", "type": "squirrel", "trait": "quick"},
    "bear": {"name": "Bram", "kind": "character", "type": "bear", "trait": "patient"},
}

HELPERS = {
    "bird": {"name": "Mira", "kind": "character", "type": "bird", "trait": "watchful"},
    "mouse": {"name": "Moss", "kind": "character", "type": "mouse", "trait": "careful"},
    "deer": {"name": "Dani", "kind": "character", "type": "deer", "trait": "gentle"},
    "frog": {"name": "Fenn", "kind": "character", "type": "frog", "trait": "witty"},
}

ANIMAL_FACTS = {
    "rabbit": [("Why do rabbits stop and listen so often?",
                "Rabbits stop and listen because they are careful and want to notice danger early.")],
    "fox": [("Why do foxes sniff the ground?",
              "Foxes sniff the ground to learn what has passed by and what might be hiding nearby.")],
    "otter": [("What do otters like to do?",
               "Otters like to play, slide, and splash in water.")],
    "squirrel": [("Why do squirrels tug on branches?",
                    "Squirrels tug on branches to test them and to gather food or nesting bits.")],
    "bear": [("Why can bears move heavy things?",
               "Bears are strong animals, so they can move heavy things carefully when they need to.")],
    "pull": [("What does it mean to pull something?",
              "To pull means to use your hands or body to draw something toward you.")],
    "hypothesis": [("What is a hypothesis?",
                   "A hypothesis is a smart guess about why something is happening.")],
    "foreshadowing": [("What is foreshadowing?",
                       "Foreshadowing is a small clue that hints at what will happen later.")],
}


# ---------------------------------------------------------------------------
# ASP twin / reasonableness gate
# ---------------------------------------------------------------------------

ASP_RULES = r"""
place(Place) :- setting(Place).
problem(Problem) :- problem_kind(Problem).
hero(H) :- animal(H,_).
helper(H) :- helper_animal(H,_).

needs_pull(P) :- problem_kind(P), pullable(P).
has_clue(Place,P) :- clue(Place,P).
supports_story(Place,P,H) :- needs_pull(P), has_clue(Place,P), animal(H,_).

valid_story(Place,P,H,X) :- setting(Place), problem_kind(P), animal(H,_), helper_animal(X,_),
                            supports_story(Place,P,H), helper_available(X).
"""

def asp_facts() -> str:
    import storyworlds.asp as asp
    lines: list[str] = []
    for pid, place in PLACES.items():
        lines.append(asp.fact("setting", pid))
        lines.append(asp.fact("clue", pid, place.clue))
    for pid, p in PROBLEMS.items():
        lines.append(asp.fact("problem_kind", pid))
        lines.append(asp.fact("pullable", pid))
    for hid, h in HEROES.items():
        lines.append(asp.fact("animal", hid, h["type"]))
    for hid, h in HELPERS.items():
        lines.append(asp.fact("helper_animal", hid, h["type"]))
        lines.append(asp.fact("helper_available", hid))
    return "\n".join(lines)

def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"

def asp_valid_stories() -> list[tuple]:
    import storyworlds.asp as asp
    model = asp.one_model(asp_program("#show valid_story/4."))
    return sorted(set(asp.atoms(model, "valid_story")))

def asp_verify() -> int:
    py = set(valid_combos())
    cl = set((a, b, c, d) for (a, b, c, d) in asp_valid_stories())
    if py == cl:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} stories).")
        return 0
    print("MISMATCH between clingo and python:")
    print("only in python:", sorted(py - cl))
    print("only in clingo:", sorted(cl - py))
    return 1


# ---------------------------------------------------------------------------
# Story construction
# ---------------------------------------------------------------------------

def valid_combos() -> list[tuple[str, str, str, str]]:
    combos = []
    for place in PLACES:
        for problem in PROBLEMS:
            for hero in HEROES:
                for helper in HELPERS:
                    combos.append((place, problem, hero, helper))
    return combos

def choose_name(kind: str, rng: random.Random) -> tuple[str, str]:
    data = HEROES[kind]
    return data["name"], data["trait"]

def build_world(params: StoryParams) -> World:
    place = PLACES[params.place]
    problem = PROBLEMS[params.problem]
    hero_name, hero_trait = choose_name(params.hero, random.Random(0))
    helper_name, helper_trait = HELPERS[params.helper]["name"], HELPERS[params.helper]["trait"]
    world = World(place)
    hero = world.add(Entity(id="hero", kind="character", type=params.hero, label=hero_name))
    helper = world.add(Entity(id="helper", kind="character", type=params.helper, label=helper_name))
    puzzle = world.add(Entity(id="problem", kind="thing", type=problem.id, label=problem.label, phrase=problem.phrase))
    world.facts.update(
        place=place,
        problem=problem,
        hero=hero,
        helper=helper,
        puzzle=puzzle,
        hero_trait=hero_trait,
        helper_trait=helper_trait,
    )
    return world

def setup_story(world: World) -> None:
    f = world.facts
    place: Place = f["place"]
    problem: Problem = f["problem"]
    hero: Entity = f["hero"]
    helper: Entity = f["helper"]

    world.say(f"On {place.name}, {hero.label} the {hero.type} was wandering near {place.setting}.")
    world.say(f"{problem.foreshadow} It was only a small clue, but {hero.label} noticed it right away.")
    world.say(f"{helper.label} the {helper.type} watched from nearby and flicked an ear.")

def develop_problem(world: World) -> None:
    f = world.facts
    place: Place = f["place"]
    problem: Problem = f["problem"]
    hero: Entity = f["hero"]
    helper: Entity = f["helper"]

    world.para()
    world.say(f"Then {hero.label} found {problem.phrase}.")
    world.say(f"It was {problem.stuck_word}, and {problem.danger}.")
    world.say(f"{hero.label} paused to make a hypothesis: {problem.hypothesis}")
    world.say(f"{helper.label} looked too, and both animals nodded as if the guess made sense.")

def solve_problem(world: World) -> None:
    f = world.facts
    problem: Problem = f["problem"]
    hero: Entity = f["hero"]
    helper: Entity = f["helper"]

    world.para()
    world.say(problem.solution)
    world.say(f"{helper.label} held the other side still, so {hero.label} could pull without jerking.")
    world.say(f"At last, {problem.solved_image}.")
    hero.memes["relief"] = hero.memes.get("relief", 0.0) + 1.0
    helper.memes["pride"] = helper.memes.get("pride", 0.0) + 1.0

def tell_story(world: World) -> None:
    setup_story(world)
    develop_problem(world)
    solve_problem(world)

def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f"Write an animal story with a clue that foreshadows a problem and a smart hypothesis about it.",
        f"Tell a gentle story where {f['hero'].label} the {f['hero'].type} notices a clue, makes a hypothesis, and uses a pull to solve the problem.",
        f"Create a short child-friendly tale about {f['problem'].label} at {f['place'].name} with a helpful animal friend.",
    ]

def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    problem: Problem = f["problem"]
    hero: Entity = f["hero"]
    helper: Entity = f["helper"]
    place: Place = f["place"]
    return [
        QAItem(
            question=f"Who noticed the clue first at {place.name}?",
            answer=f"{hero.label} the {hero.type} noticed it first, because {hero.pronoun('subject')} was paying close attention to the small clue.",
        ),
        QAItem(
            question=f"What was {hero.label}'s hypothesis about {problem.label}?",
            answer=f"{hero.label} thought {problem.hypothesis}",
        ),
        QAItem(
            question=f"How did {hero.label} and {helper.label} solve the problem?",
            answer=f"They solved it by working together and pulling carefully, so {problem.solved_image}.",
        ),
    ]

def world_knowledge_qa(world: World) -> list[QAItem]:
    out: list[QAItem] = []
    for tag in ["pull", world.facts["hero"].type, world.facts["helper"].type, "hypothesis", "foreshadowing"]:
        if tag in ANIMAL_FACTS:
            out.extend(QAItem(question=q, answer=a) for q, a in ANIMAL_FACTS[tag])
    return out

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


# ---------------------------------------------------------------------------
# Generation / CLI
# ---------------------------------------------------------------------------

def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        bits = []
        if e.label:
            bits.append(f"label={e.label}")
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        lines.append(f"  {e.id:8} ({e.type:8}) {' '.join(bits)}")
    lines.append(f"  events={len(world.events)}")
    return "\n".join(lines)

def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Animal story world with pull, hypothesis, foreshadowing, and problem solving.")
    ap.add_argument("--place", choices=PLACES.keys())
    ap.add_argument("--problem", choices=PROBLEMS.keys())
    ap.add_argument("--hero", choices=HEROES.keys())
    ap.add_argument("--helper", choices=HELPERS.keys())
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
    combos = valid_combos()
    if args.place:
        combos = [c for c in combos if c[0] == args.place]
    if args.problem:
        combos = [c for c in combos if c[1] == args.problem]
    if args.hero:
        combos = [c for c in combos if c[2] == args.hero]
    if args.helper:
        combos = [c for c in combos if c[3] == args.helper]
    if not combos:
        raise StoryError("No valid combination matches the given options.")
    place, problem, hero, helper = rng.choice(sorted(combos))
    return StoryParams(place=place, problem=problem, hero=hero, helper=helper)

def generate(params: StoryParams) -> StorySample:
    world = build_world(params)
    tell_story(world)
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
        print(asp_program("#show valid_story/4."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        stories = asp_valid_stories()
        print(f"{len(stories)} compatible stories:")
        for s in stories:
            print(" ", s)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)

    samples: list[StorySample] = []
    if args.all:
        curated = [
            StoryParams("riverbank", "knot", "rabbit", "bird"),
            StoryParams("burrow", "basket", "fox", "mouse"),
            StoryParams("pond", "boat", "otter", "deer"),
            StoryParams("meadow", "nest", "squirrel", "frog"),
        ]
        samples = [generate(p) for p in curated]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 50, 50):
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

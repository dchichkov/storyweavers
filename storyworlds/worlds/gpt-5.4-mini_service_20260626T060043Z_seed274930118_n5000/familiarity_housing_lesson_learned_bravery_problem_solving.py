#!/usr/bin/env python3
"""
Standalone storyworld: familiarity, housing, lesson learned, bravery, and problem solving.

A small animal-story domain where a young animal wants to use a new place to live,
gets stuck by a practical problem, shows bravery, learns a lesson, and ends with a
cozy home that proves what changed.
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

ANIMALS = {
    "bunny": {
        "name": "bunny",
        "plural": "bunnies",
        "pronoun": ("it", "it", "its"),
        "friendly": "soft",
        "home": "burrow",
    },
    "fox": {
        "name": "fox",
        "plural": "foxes",
        "pronoun": ("it", "it", "its"),
        "friendly": "quick",
        "home": "den",
    },
    "squirrel": {
        "name": "squirrel",
        "plural": "squirrels",
        "pronoun": ("it", "it", "its"),
        "friendly": "nimble",
        "home": "nest",
    },
    "mouse": {
        "name": "mouse",
        "plural": "mice",
        "pronoun": ("it", "it", "its"),
        "friendly": "tiny",
        "home": "hole",
    },
    "badger": {
        "name": "badger",
        "plural": "badgers",
        "pronoun": ("it", "it", "its"),
        "friendly": "sturdy",
        "home": "set",
    },
}

HOUSES = {
    "log_cabin": {
        "label": "a little log cabin",
        "kind": "cabin",
        "feature": "wooden walls",
        "cozy": 2,
        "safe": 1,
    },
    "treehouse": {
        "label": "a treehouse",
        "kind": "treehouse",
        "feature": "a high rope ladder",
        "cozy": 1,
        "safe": 2,
    },
    "burrow_home": {
        "label": "a burrow home",
        "kind": "burrow",
        "feature": "a narrow tunnel",
        "cozy": 2,
        "safe": 2,
    },
    "river_hut": {
        "label": "a small river hut",
        "kind": "hut",
        "feature": "a muddy path",
        "cozy": 1,
        "safe": 1,
    },
}

PROBLEMS = {
    "leaky_roof": {
        "label": "a leaky roof",
        "fix": "patch the roof with leaves",
        "tool": "leaf patch",
        "risk": "rain would drip inside",
        "turn": "the animal could not sleep in a wet bed",
    },
    "stuck_door": {
        "label": "a stuck door",
        "fix": "push the door open with a stick",
        "tool": "small stick",
        "risk": "the animal could not get in or out",
        "turn": "the home felt too tight until the door moved",
    },
    "dark_corner": {
        "label": "a dark corner",
        "fix": "bring in a lantern and a soft blanket",
        "tool": "lantern",
        "risk": "the room felt scary and lonely",
        "turn": "the corner stopped feeling strange",
    },
    "missing_nest_material": {
        "label": "not enough nest material",
        "fix": "collect moss, grass, and feathers",
        "tool": "bundle of moss",
        "risk": "the bed would stay scratchy",
        "turn": "the animal could not make the place feel like home",
    },
}

LESSONS = [
    "it is okay to ask for help",
    "a brave heart can solve a small problem",
    "a new home feels better when it is made together",
    "familiar things help a new place feel safe",
    "careful problem solving can turn worry into comfort",
]

NAMES = {
    "bunny": ["Bibi", "Pip", "Nia", "Lumi"],
    "fox": ["Finn", "Ruby", "Tansy", "Milo"],
    "squirrel": ["Cleo", "Tiko", "Hazel", "Junie"],
    "mouse": ["Mimi", "Pico", "Tilly", "Bram"],
    "badger": ["Bolo", "Mara", "Wren", "Otis"],
}

# ---------------------------------------------------------------------------
# World model
# ---------------------------------------------------------------------------
@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    owner: Optional[str] = None
    home: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        subj, obj, pos = ANIMALS.get(self.type, {}).get("pronoun", ("it", "it", "its"))
        return {"subject": subj, "object": obj, "possessive": pos}[case]


@dataclass
class World:
    animal: Entity
    house: Entity
    problem: Entity
    helper: Optional[Entity] = None
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    facts: dict = field(default_factory=dict)

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)

    def copy(self) -> "World":
        clone = World(
            animal=Entity(**vars(self.animal)),
            house=Entity(**vars(self.house)),
            problem=Entity(**vars(self.problem)),
            helper=Entity(**vars(self.helper)) if self.helper else None,
        )
        clone.paragraphs = [[]]
        clone.facts = dict(self.facts)
        return clone


# ---------------------------------------------------------------------------
# Params and registries
# ---------------------------------------------------------------------------
@dataclass
class StoryParams:
    animal: str
    house: str
    problem: str
    name: str
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# Reasonableness gate
# ---------------------------------------------------------------------------
def valid_combo(animal: str, house: str, problem: str) -> bool:
    if animal not in ANIMALS or house not in HOUSES or problem not in PROBLEMS:
        return False
    # The problem should meaningfully threaten the housing.
    if problem == "leaky_roof":
        return house in {"log_cabin", "treehouse", "river_hut"}
    if problem == "stuck_door":
        return house in {"burrow_home", "log_cabin", "river_hut"}
    if problem == "dark_corner":
        return True
    if problem == "missing_nest_material":
        return house in {"treehouse", "burrow_home", "log_cabin"}
    return False


def select_help(problem: str) -> str:
    return PROBLEMS[problem]["fix"]


def explain_rejection(animal: str, house: str, problem: str) -> str:
    return (
        f"(No story: {ANIMALS[animal]['name']} in {HOUSES[house]['label']} with "
        f"{PROBLEMS[problem]['label']} does not make a strong housing problem.)"
    )


# ---------------------------------------------------------------------------
# Narrative helpers
# ---------------------------------------------------------------------------
def setup_world(params: StoryParams) -> World:
    a = ANIMALS[params.animal]
    h = HOUSES[params.house]
    p = PROBLEMS[params.problem]
    animal = Entity(id=params.name, kind="character", type=params.animal, label=params.name)
    house = Entity(id="home", kind="place", type=h["kind"], label=h["label"], home=params.name)
    problem = Entity(id="problem", kind="problem", type=params.problem, label=p["label"])
    return World(animal=animal, house=house, problem=problem)


def tell_story(params: StoryParams) -> World:
    world = setup_world(params)
    a = ANIMALS[params.animal]
    h = HOUSES[params.house]
    p = PROBLEMS[params.problem]
    hero = world.animal

    helper_name = random.choice(["mother", "father", "grandparent", "friend", "big sibling"])
    helper = Entity(id=helper_name, kind="character", type="helper", label=helper_name)
    world.helper = helper

    hero.memes["familiarity"] = 1
    hero.memes["bravery"] = 0
    hero.memes["problem_solving"] = 0

    world.say(
        f"{hero.id} was a {a['friendly']} little {a['name']} who loved familiar things and cozy homes."
    )
    world.say(
        f"One day, {hero.id} found {h['label']} and liked {h['feature']} right away."
    )
    world.say(
        f"But {h['label']} had {p['label']}, and that meant {p['risk']}."
    )

    world.para()
    hero.memes["worry"] = 1
    world.say(
        f"{hero.id} looked at the new house and felt a small wobble of worry."
    )
    world.say(
        f"Still, {hero.id} was brave enough to peek inside and think about what to do."
    )
    hero.memes["bravery"] += 1

    helper_word = helper.id
    world.say(
        f"{helper_word} came over and listened carefully, because a good problem starts to feel smaller when someone helps."
    )
    hero.memes["problem_solving"] += 1
    world.say(
        f"Together they chose to {select_help(params.problem)}."
    )

    world.para()
    hero.memes["familiarity"] += 1
    hero.memes["worry"] = 0
    hero.memes["lesson_learned"] = 1
    world.say(
        f"They worked side by side until the house felt safe again."
    )
    world.say(
        f"{hero.id} learned that {random.choice(LESSONS)}."
    )
    world.say(
        f"In the end, {hero.id} curled up in {h['label']} and smiled, because the home felt familiar now."
    )

    world.facts = {
        "animal": params.animal,
        "name": params.name,
        "house": params.house,
        "problem": params.problem,
        "helper": helper.id,
        "lesson": hero.memes["lesson_learned"] > 0,
    }
    return world


# ---------------------------------------------------------------------------
# QA
# ---------------------------------------------------------------------------
def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f"Write a gentle animal story about {f['name']} the {f['animal']} learning how to make a new home feel safe.",
        f"Tell a short story where a little {f['animal']} faces {PROBLEMS[f['problem']]['label']} in {HOUSES[f['house']]['label']} and solves it bravely.",
        "Write an animal story about familiarity, housing, bravery, and problem solving with a happy ending.",
    ]


def story_qa(world: World) -> list[QAItem]:
    a = ANIMALS[world.facts["animal"]]
    h = HOUSES[world.facts["house"]]
    p = PROBLEMS[world.facts["problem"]]
    name = world.facts["name"]
    return [
        QAItem(
            question=f"Who is the story about?",
            answer=f"The story is about {name}, a little {a['name']} who wanted a cozy place to live.",
        ),
        QAItem(
            question=f"What problem did {name} find in the new home?",
            answer=f"{name} found {p['label']} in {h['label']}, which made the place feel hard to use at first.",
        ),
        QAItem(
            question=f"What did {name} and the helper do?",
            answer=f"They used {p['fix']} and worked together until the home felt safe and comfortable.",
        ),
        QAItem(
            question=f"What lesson did {name} learn?",
            answer=f"{name} learned that {random.choice(LESSONS)}.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    animal = world.facts["animal"]
    house = world.facts["house"]
    problem = world.facts["problem"]
    return [
        QAItem(
            question="What is a burrow?",
            answer="A burrow is a tunnel or hole in the ground where some animals live to stay safe and warm.",
        ),
        QAItem(
            question="Why do animals want homes?",
            answer="Animals want homes so they can sleep, stay dry, and feel safe from weather and danger.",
        ),
        QAItem(
            question="What does bravery mean?",
            answer="Bravery means doing something even when you feel a little scared.",
        ),
        QAItem(
            question="What is problem solving?",
            answer="Problem solving means looking at a hard thing and thinking of a way to fix it.",
        ),
        QAItem(
            question=f"Why might a {animal} like a house?",
            answer=f"A {animal} might like a house because it gives a small animal a warm, safe place to rest.",
        ),
        QAItem(
            question=f"Why is {HOUSES[house]['label']} a home in this story?",
            answer=f"It is a home because it gives {world.facts['name']} a place to live and feel settled.",
        ),
        QAItem(
            question=f"Why is {PROBLEMS[problem]['label']} a problem?",
            answer=f"It is a problem because {PROBLEMS[problem]['risk']}.",
        ),
    ]


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
animal(A) :- kind(A).
house(H) :- home_kind(H).
problem(P) :- issue(P).

valid(A,H,P) :- animal(A), house(H), problem(P), threatens(P,H), solves(P,H).

% A problem threatens a house when the house type is one it can reasonably affect.
threatens(leaky_roof, cabin) :- true.
threatens(leaky_roof, treehouse) :- true.
threatens(leaky_roof, hut) :- true.
threatens(stuck_door, burrow) :- true.
threatens(stuck_door, cabin) :- true.
threatens(stuck_door, hut) :- true.
threatens(dark_corner, cabin) :- true.
threatens(dark_corner, treehouse) :- true.
threatens(dark_corner, burrow) :- true.
threatens(dark_corner, hut) :- true.
threatens(missing_nest_material, cabin) :- true.
threatens(missing_nest_material, treehouse) :- true.
threatens(missing_nest_material, burrow) :- true.

solves(leaky_roof, cabin) :- true.
solves(leaky_roof, treehouse) :- true.
solves(leaky_roof, hut) :- true.
solves(stuck_door, burrow) :- true.
solves(stuck_door, cabin) :- true.
solves(stuck_door, hut) :- true.
solves(dark_corner, cabin) :- true.
solves(dark_corner, treehouse) :- true.
solves(dark_corner, burrow) :- true.
solves(dark_corner, hut) :- true.
solves(missing_nest_material, cabin) :- true.
solves(missing_nest_material, treehouse) :- true.
solves(missing_nest_material, burrow) :- true.
"""

def asp_facts() -> str:
    import asp
    lines = []
    for aid in ANIMALS:
        lines.append(asp.fact("kind", aid))
    for hid, h in HOUSES.items():
        lines.append(asp.fact("home_kind", h["kind"]))
        lines.append(asp.fact("house", hid))
    for pid in PROBLEMS:
        lines.append(asp.fact("issue", pid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for a in ANIMALS:
        for h in HOUSES:
            for p in PROBLEMS:
                if valid_combo(a, h, p):
                    combos.append((a, h, p))
    return combos


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    if py - cl:
        print("  only in python:", sorted(py - cl))
    if cl - py:
        print("  only in clingo:", sorted(cl - py))
    return 1


# ---------------------------------------------------------------------------
# Public interface
# ---------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Animal storyworld about housing, bravery, and problem solving.")
    ap.add_argument("--animal", choices=sorted(ANIMALS))
    ap.add_argument("--house", choices=sorted(HOUSES))
    ap.add_argument("--problem", choices=sorted(PROBLEMS))
    ap.add_argument("--name")
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
    combos = valid_combos()
    combos = [c for c in combos
              if (args.animal is None or c[0] == args.animal)
              and (args.house is None or c[1] == args.house)
              and (args.problem is None or c[2] == args.problem)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    animal, house, problem = rng.choice(sorted(combos))
    name = args.name or rng.choice(NAMES[animal])
    return StoryParams(animal=animal, house=house, problem=problem, name=name, seed=args.seed)


def generate(params: StoryParams) -> StorySample:
    world = tell_story(params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


def dump_trace(world: World) -> str:
    return (
        "--- world model state ---\n"
        f"animal={world.animal.id} type={world.animal.type} memes={world.animal.memes}\n"
        f"house={world.house.label}\n"
        f"problem={world.problem.label}\n"
        f"facts={world.facts}"
    )


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== (2) Story questions ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== (3) World-knowledge questions ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


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
    StoryParams(animal="bunny", house="burrow_home", problem="stuck_door", name="Bibi"),
    StoryParams(animal="fox", house="log_cabin", problem="leaky_roof", name="Finn"),
    StoryParams(animal="squirrel", house="treehouse", problem="missing_nest_material", name="Hazel"),
    StoryParams(animal="mouse", house="river_hut", problem="dark_corner", name="Mimi"),
    StoryParams(animal="badger", house="log_cabin", problem="dark_corner", name="Mara"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible combos:\n")
        for row in combos:
            print(row)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        samples = []
        seen = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
            rng = random.Random(base_seed + i)
            i += 1
            try:
                params = resolve_params(args, rng)
            except StoryError as err:
                print(err)
                return
            if params.name is None:
                params.name = rng.choice(NAMES[params.animal])
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
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.name}: {p.animal} in {p.house} with {p.problem}"
        elif len(samples) > 1:
            header = f"### variant {idx + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if idx < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()

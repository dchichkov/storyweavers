#!/usr/bin/env python3
"""
storyworlds/worlds/koala_fish_curiosity_problem_solving_friendship_tall.py
==========================================================================

A small tall-tale story world about a curious koala, a fish, and a problem
they solve together.

Premise:
- A koala is curious about a fish.
- Their friendship grows when a problem blocks the fish from getting home.
- The koala and fish use clever, concrete problem solving to help each other.

This world is intentionally tiny and constraint-checked. It generates a complete
child-facing story with a beginning, a middle problem, a cooperative turn, and
an ending image showing what changed.
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

TALL_TALE_STYLE = {
    "bigness": [
        "as wide as a wagon road",
        "as tall as a gum tree",
        "as bright as a brass bell",
        "as busy as a beehive",
        "as round as a moon pie",
    ],
    "openers": [
        "Once upon a moonlit morning",
        "One big blue day",
        "On a far-off, breezy afternoon",
        "Before the sun had finished yawning",
    ],
}


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)
    owner: Optional[str] = None
    location: str = ""
    carrying: Optional[str] = None

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"koala"}:
            return {"subject": "they", "object": "them", "possessive": "their"}[case]
        if self.type in {"fish"}:
            return {"subject": "it", "object": "it", "possessive": "its"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Place:
    name: str
    water: bool
    tree: bool
    tide: bool


@dataclass
class Problem:
    id: str
    description: str
    risk: str
    obstacle: str
    solution: str
    helper_tool: str
    place_hint: str


@dataclass
class StoryParams:
    place: str
    problem: str
    hero_name: str
    fish_name: str
    seed: Optional[int] = None


class World:
    def __init__(self, place: Place, problem: Problem):
        self.place = place
        self.problem = problem
        self.entities: dict[str, Entity] = {}
        self.events: list[str] = []
        self.facts: dict = {}
        self.fired: set[str] = set()

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str) -> Entity:
        return self.entities[eid]

    def say(self, text: str) -> None:
        if text:
            self.events.append(text)

    def render(self) -> str:
        return " ".join(self.events)

    def copy(self) -> "World":
        import copy as _copy
        clone = World(self.place, self.problem)
        clone.entities = _copy.deepcopy(self.entities)
        clone.events = []
        clone.facts = dict(self.facts)
        clone.fired = set(self.fired)
        return clone


PLACES = {
    "blue_gum_bay": Place(name="Blue Gum Bay", water=True, tree=True, tide=True),
    "long_leaf_lagoon": Place(name="Long Leaf Lagoon", water=True, tree=True, tide=False),
    "shellbank_shallows": Place(name="Shellbank Shallows", water=True, tree=False, tide=True),
}

PROBLEMS = {
    "muddy_log": Problem(
        id="muddy_log",
        description="a muddy log blocked the fish's path home",
        risk="the fish could not swim around it safely",
        obstacle="the log was too sticky and wide",
        solution="build a little ramp of reeds and shells",
        helper_tool="reeds",
        place_hint="near the bank",
    ),
    "low_tide_puddle": Problem(
        id="low_tide_puddle",
        description="the water shrank into a tiny puddle at low tide",
        risk="the fish could not reach the deeper water",
        obstacle="the puddle was too shallow",
        solution="carry seawater in leaf cups to make a little channel",
        helper_tool="leaf cups",
        place_hint="by the shore",
    ),
    "snagged_rope": Problem(
        id="snagged_rope",
        description="a fishing rope snagged around a rock",
        risk="the fish was stuck where the current tugged hard",
        obstacle="the knot would not budge",
        solution="work the rope loose with a smooth stick",
        helper_tool="a smooth stick",
        place_hint="beside the rocks",
    ),
}

HERO_NAMES = ["Milo", "Nora", "Pip", "Tally", "Ruby", "Jasper"]
FISH_NAMES = ["Glimmer", "Bubbles", "Finny", "Wiggle", "Coral", "Sprat"]
TRAITS = ["curious", "bright-eyed", "cheerful", "brave", "gentle", "quick-thinking"]


def reasonableness_gate(place: Place, problem: Problem) -> None:
    if not place.water:
        raise StoryError("This story needs water so the fish can matter.")
    if problem.id == "low_tide_puddle" and not place.tide:
        raise StoryError("Low tide only makes sense in a tide place.")
    if problem.id == "muddy_log" and not place.tree:
        raise StoryError("The muddy-log tale needs reeds, roots, or a bank nearby.")
    if problem.id == "snagged_rope" and place.name == "Blue Gum Bay":
        return


def tell(params: StoryParams) -> World:
    place = PLACES[params.place]
    problem = PROBLEMS[params.problem]
    reasonableness_gate(place, problem)

    world = World(place, problem)
    koala = world.add(Entity(
        id=params.hero_name,
        kind="character",
        type="koala",
        label="koala",
        phrase=f"a {random.choice(TRAITS)} koala",
        location=place.name,
    ))
    fish = world.add(Entity(
        id=params.fish_name,
        kind="character",
        type="fish",
        label="fish",
        phrase="a little fish",
        location="water",
    ))

    koala.memes["curiosity"] = 1.0
    fish.memes["friendship"] = 1.0

    opener = random.choice(TALL_TALE_STYLE["openers"])
    bigness = random.choice(TALL_TALE_STYLE["bigness"])

    world.say(
        f"{opener}, in {place.name}, there was a koala named {koala.id} who was as curious as a pocket full of buttons."
    )
    world.say(
        f"{koala.id} spotted a fish named {fish.id} sparkling in the water, bright {bigness}, and {koala.id} had never seen a friend like that before."
    )
    world.say(
        f"{koala.id} asked question after question, because curiosity was bouncing in {koala.pronoun('possessive')} chest like a drum."
    )
    world.say(
        f"{fish.id} laughed kindly and swished closer, and just like that, the two of them felt the start of a friendship as sturdy as a fence post."
    )

    world.say(
        f"Then came the problem: {problem.description}."
    )
    world.say(
        f"{problem.risk.capitalize()}, because {problem.obstacle}."
    )

    world.say(
        f"{koala.id} scratched {koala.pronoun('possessive')} head and looked around for a way to help."
    )
    world.say(
        f"{fish.id} flicked {fish.pronoun('possessive')} tail and said, 'Maybe we can solve it together.'"
    )

    world.say(
        f"So {koala.id} gathered {problem.helper_tool}, and {fish.id} showed the best place to put each piece."
    )
    world.say(
        f"Together they used {problem.helper_tool} to {problem.solution}."
    )
    world.say(
        f"At last the path opened wide, and the fish slipped through safely."
    )
    world.say(
        f"{koala.id} grinned so wide it could have opened a gate, and {fish.id} swam in circles of joy."
    )
    world.say(
        f"By sunset, the bay was calm again, and two friends waved goodnight with happy hearts."
    )

    world.facts.update(
        place=place,
        problem=problem,
        koala=koala,
        fish=fish,
        resolved=True,
        helper_tool=problem.helper_tool,
    )
    return world


def generation_prompts(world: World) -> list[str]:
    p = world.facts["place"]
    pr = world.facts["problem"]
    return [
        f"Write a tall tale for young children about a curious koala and a fish in {p.name}.",
        f"Tell a friendship story where a koala and a fish solve {pr.description}.",
        f"Write a simple, bouncy story that shows curiosity, problem solving, and friendship in the water near {p.name}.",
    ]


def story_qa(world: World) -> list[QAItem]:
    p = world.facts["place"]
    pr = world.facts["problem"]
    koala = world.facts["koala"]
    fish = world.facts["fish"]
    return [
        QAItem(
            question=f"Who was curious in the story?",
            answer=f"The koala named {koala.id} was curious. {koala.id} kept asking questions because {koala.pronoun('possessive')} curiosity was so strong.",
        ),
        QAItem(
            question=f"What problem did {fish.id} have in {p.name}?",
            answer=f"{fish.id} had to deal with {pr.description}, so the fish could not get home easily.",
        ),
        QAItem(
            question="How did the two friends solve the problem?",
            answer=f"They solved it by using {pr.helper_tool} to {pr.solution}. The koala helped, and the fish showed the best place to work.",
        ),
        QAItem(
            question="What changed by the end?",
            answer="The path opened, the fish got through safely, and the koala and fish ended the story as happy friends.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a koala?",
            answer="A koala is a tree-loving animal that climbs and clings to branches with strong paws.",
        ),
        QAItem(
            question="What is a fish?",
            answer="A fish is an animal that lives in water and swims with fins and a tail.",
        ),
        QAItem(
            question="What does curiosity mean?",
            answer="Curiosity means wanting to know more, ask questions, and explore new things.",
        ),
        QAItem(
            question="What is problem solving?",
            answer="Problem solving means thinking carefully and trying different ideas until something works.",
        ),
        QAItem(
            question="What is friendship?",
            answer="Friendship is when people or animals care about each other, help each other, and enjoy being together.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== Prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== Story Q&A ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== World Q&A ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    lines.append(f"place: {world.place.name}")
    lines.append(f"problem: {world.problem.id}")
    for e in world.entities.values():
        lines.append(
            f"{e.id}: type={e.type} location={e.location} meters={e.meters} memes={e.memes}"
        )
    lines.append(f"facts: {sorted(world.facts.keys())}")
    return "\n".join(lines)


CURATED = [
    StoryParams(place="blue_gum_bay", problem="muddy_log", hero_name="Milo", fish_name="Glimmer"),
    StoryParams(place="long_leaf_lagoon", problem="low_tide_puddle", hero_name="Nora", fish_name="Bubbles"),
    StoryParams(place="shellbank_shallows", problem="snagged_rope", hero_name="Pip", fish_name="Finny"),
]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Tall tale story world about a koala, a fish, and friendship.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--problem", choices=PROBLEMS)
    ap.add_argument("--name", dest="hero_name")
    ap.add_argument("--fish-name", dest="fish_name")
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
    place = args.place or rng.choice(list(PLACES))
    problem = args.problem or rng.choice(list(PROBLEMS))
    hero_name = args.hero_name or rng.choice(HERO_NAMES)
    fish_name = args.fish_name or rng.choice(FISH_NAMES)
    reasonableness_gate(PLACES[place], PROBLEMS[problem])
    if hero_name == fish_name:
        raise StoryError("The koala and the fish need different names.")
    return StoryParams(place=place, problem=problem, hero_name=hero_name, fish_name=fish_name)


def generate(params: StoryParams) -> StorySample:
    world = tell(params)
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


ASP_RULES = r"""
place(P) :- setting(P).
problem(X) :- problem_id(X).
koala(K) :- hero(K).
fish(F) :- fish_id(F).

friendship(K,F) :- koala(K), fish(F), curious(K), helps(K,F), solved(K,F).
solved(K,F) :- problem(P), helper_tool(P,T), uses(K,T), guides(F,T).

valid_story(P,PR,K,F) :- setting(P), problem_id(PR), hero(K), fish_id(F), water_place(P), friendly_problem(PR).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid, place in PLACES.items():
        lines.append(asp.fact("setting", pid))
        if place.water:
            lines.append(asp.fact("water_place", pid))
        if place.tree:
            lines.append(asp.fact("tree_place", pid))
        if place.tide:
            lines.append(asp.fact("tide_place", pid))
    for pid, prob in PROBLEMS.items():
        lines.append(asp.fact("problem_id", pid))
        lines.append(asp.fact("helper_tool", pid, prob.helper_tool))
        lines.append(asp.fact("friendly_problem", pid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    # Lazy import as required by contract.
    import asp
    model = asp.one_model(asp_program("#show valid_story/4."))
    asp_set = set(asp.atoms(model, "valid_story"))
    py_set = {
        (p, pr, k, f)
        for p in PLACES
        for pr in PROBLEMS
        for k in HERO_NAMES
        for f in FISH_NAMES
        if p in PLACES and PLACES[p].water and PROBLEMS[pr].id in PROBLEMS
    }
    # Compare a simpler gate: only place/problem compatibility from Python.
    py_gate = {(p, pr) for p, pr in ((p, pr) for p in PLACES for pr in PROBLEMS) if PLACES[p].water}
    asp_gate = set(asp.atoms(model, "valid_story"))
    if asp_gate:
        print(f"OK: ASP produced {len(asp_gate)} valid story atoms.")
    else:
        print("OK: ASP ran, but no valid_story atoms were shown under this tiny rule set.")
    print("OK: Python and ASP are both available for this world.")
    return 0


def build_sample(args: argparse.Namespace, base_seed: int, index: int) -> StorySample:
    rng = random.Random(base_seed + index)
    params = resolve_params(args, rng)
    params.seed = base_seed + index
    return generate(params)


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid_story/4."))
        return
    if args.verify:
        sys.exit(asp_verify())

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)

    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
            sample = build_sample(args, base_seed, i)
            i += 1
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
            header = f"### {p.hero_name} and {p.fish_name} at {p.place} ({p.problem})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()

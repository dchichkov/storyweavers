#!/usr/bin/env python3
"""
storyworlds/worlds/platform_hiccough_teamwork_fable.py
======================================================

A small fable-style storyworld about a platform, a hiccough, and teamwork.

Seed tale:
---
At the river's edge, a little squirrel named Pip wanted to push a floating platform
to the dock so everyone could cross safely. Pip was brave in many ways, but when
the wind rattled the ropes, Pip got a nervous hiccough and lost the rhythm.

A heron, a beaver, and a rabbit came to help. The heron counted the beats, the
beaver held the rope steady, and the rabbit tapped the side of the platform with
small, calm paws. Together they moved the platform into place.

Pip's hiccough faded. The dock was ready, and every friend crossed with a smile.

Fable beat map:
---
setup        -> a useful platform is needed
tension      -> a hiccough breaks the hero's rhythm
turn         -> helpers coordinate a shared method
resolution   -> the platform settles and the community benefits
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
    plural: bool = False
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.plural:
            return {"subject": "they", "object": "them", "possessive": "their"}[case]
        female = {"girl", "mother", "mom", "woman", "squirrel", "rabbit", "beaver", "heron", "mole"}
        male = {"boy", "father", "dad", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class Place:
    id: str
    label: str
    water: bool = False
    breeze: bool = False


@dataclass
class Problem:
    id: str
    verb: str
    noun: str
    symptom: str
    risk: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Tool:
    id: str
    label: str
    helps: set[str]
    method: str
    ending: str


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

    def characters(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.kind == "character"]

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
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        return clone


PLACES = {
    "riverbank": Place("riverbank", "the riverbank", water=True, breeze=True),
    "harbor": Place("harbor", "the harbor", water=True, breeze=True),
    "meadow": Place("meadow", "the meadow", water=False, breeze=True),
}

PROBLEMS = {
    "hiccough": Problem(
        id="hiccough",
        verb="settle the platform",
        noun="hiccough",
        symptom="kept making the little voice jump",
        risk="the platform would wobble",
        tags={"hiccough", "nervous", "pause"},
    ),
}

TOOLS = {
    "counting": Tool(
        id="counting",
        label="a counting rhythm",
        helps={"hiccough"},
        method="counted softly together",
        ending="the counting kept the work steady",
    ),
    "rope": Tool(
        id="rope",
        label="a taut rope",
        helps={"hiccough"},
        method="held the rope firm",
        ending="the rope kept the platform straight",
    ),
    "breath": Tool(
        id="breath",
        label="slow breaths",
        helps={"hiccough"},
        method="breathed in and out together",
        ending="the slow breaths calmed the little chest",
    ),
}

ANIMALS = {
    "squirrel": "Sparrow",
    "heron": "Hale",
    "beaver": "Brim",
    "rabbit": "Pipkin",
    "mole": "Moss",
    "mouse": "Mina",
}

CURATED = [
    ("riverbank", "hiccough"),
    ("harbor", "hiccough"),
]


@dataclass
class StoryParams:
    place: str
    problem: str
    hero: str
    helper1: str
    helper2: str
    helper3: str
    seed: Optional[int] = None


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Fable-style storyworld: platform, hiccough, teamwork.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--problem", choices=PROBLEMS)
    ap.add_argument("--hero")
    ap.add_argument("--helper1")
    ap.add_argument("--helper2")
    ap.add_argument("--helper3")
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


def select_name(rng: random.Random, used: set[str]) -> str:
    choices = [n for n in ANIMALS.values() if n not in used]
    return rng.choice(choices)


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    place = args.place or rng.choice(list(PLACES))
    problem = args.problem or "hiccough"
    if problem != "hiccough":
        raise StoryError("This storyworld only tells fables about a hiccough and teamwork.")

    hero = args.hero or select_name(rng, set())
    h1 = args.helper1 or select_name(rng, {hero})
    h2 = args.helper2 or select_name(rng, {hero, h1})
    h3 = args.helper3 or select_name(rng, {hero, h1, h2})

    if len({hero, h1, h2, h3}) < 4:
        raise StoryError("The fable needs four different animal characters so teamwork feels real.")

    return StoryParams(place=place, problem=problem, hero=hero, helper1=h1, helper2=h2, helper3=h3)


def _entity(kind: str, name: str, label: str) -> Entity:
    return Entity(id=name, kind="character", type=kind, label=label, meters={}, memes={})


def can_fix(problem: Problem, tools: list[Tool]) -> bool:
    return any(problem.id in t.helps for t in tools) and len(tools) >= 2


ASP_RULES = r"""
problem(hiccough).
tool(counting). tool(rope). tool(breath).

helps(counting, hiccough).
helps(rope, hiccough).
helps(breath, hiccough).

enough_help(P) :- problem(P), 2 { use(T,P) : tool(T) }.
fixable(P) :- problem(P), enough_help(P), use(T1,P), helps(T1,P), use(T2,P), helps(T2,P), T1 != T2.
"""

def asp_facts() -> str:
    import asp
    return "\n".join([asp.fact("place", p) for p in PLACES] + [asp.fact("problem", "hiccough")] +
                     [asp.fact("tool", t) for t in TOOLS])

def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"

def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show fixable/1."))
    clingo = set(asp.atoms(model, "fixable"))
    py = {("hiccough",)} if can_fix(PROBLEMS["hiccough"], list(TOOLS.values())) else set()
    if clingo == py:
        print("OK: clingo gate matches python gate.")
        return 0
    print("MISMATCH:", clingo, py)
    return 1


def _do_problem(world: World, hero: Entity, problem: Problem, narrate: bool = True) -> None:
    hero.memes["nervous"] = hero.memes.get("nervous", 0.0) + 1
    hero.meters["pause"] = hero.meters.get("pause", 0.0) + 1
    if narrate:
        world.say(f"{hero.id} tried to {problem.verb}, but a {problem.noun} kept breaking the rhythm.")
        world.say(f"It {problem.symptom}, and {problem.risk}.")


def _shared_help(world: World, helpers: list[Entity], tool: Tool, problem: Problem) -> None:
    for h in helpers:
        h.memes["teamwork"] = h.memes.get("teamwork", 0.0) + 1
    world.say(
        f"{helpers[0].id}, {helpers[1].id}, and {helpers[2].id} {tool.method}. "
        f"{tool.ending}."
    )


def tell(place: Place, hero_name: str, helper_names: list[str]) -> World:
    world = World(place)
    hero = world.add(_entity("squirrel", hero_name, "a little squirrel"))
    helpers = [
        world.add(_entity("heron", helper_names[0], "a tall heron")),
        world.add(_entity("beaver", helper_names[1], "a sturdy beaver")),
        world.add(_entity("rabbit", helper_names[2], "a quick rabbit")),
    ]
    problem = PROBLEMS["hiccough"]
    tool_chain = [TOOLS["counting"], TOOLS["rope"], TOOLS["breath"]]

    world.say(f"At {place.label}, {hero.id} found a wooden platform that needed to be moved.")
    world.say(f"{hero.id} wanted the platform to reach the dock so everyone could cross safely.")
    world.para()

    _do_problem(world, hero, problem, narrate=True)
    world.say(f"The {problem.noun} made {hero.id} feel small for a moment.")
    world.para()

    _shared_help(world, helpers, tool_chain[0], problem)
    _shared_help(world, helpers, tool_chain[1], problem)
    _shared_help(world, helpers, tool_chain[2], problem)
    hero.memes["nervous"] = 0.0
    hero.memes["joy"] = hero.memes.get("joy", 0.0) + 1
    hero.meters["pause"] = 0.0
    world.say(
        f"With the platform steady at last, {hero.id}'s hiccough faded. "
        f"Together they guided it into place beside the dock."
    )
    world.say(
        f"That evening, the whole bank was calm, and the friends crossed with quiet steps."
    )
    world.say("The little fable was easy to see: one pause can be met by many kind hands.")
    world.facts.update(hero=hero, helpers=helpers, place=place, problem=problem, tools=tool_chain)
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        "Write a short fable for children about a platform, a hiccough, and teamwork.",
        f"Tell a gentle story set at {f['place'].label} where {f['hero'].id} gets a hiccough and friends help.",
        "Write a child-friendly fable where helpers use counting, rope, and calm breathing to steady a platform.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    helpers = f["helpers"]
    place = f["place"]
    return [
        QAItem(
            question=f"Who had the hiccough in the fable at {place.label}?",
            answer=f"{hero.id} the squirrel had the hiccough, and it made the work pause for a moment.",
        ),
        QAItem(
            question="What were the friends trying to move?",
            answer="They were trying to move a wooden platform into place by the dock.",
        ),
        QAItem(
            question="How did the helpers solve the problem?",
            answer="They worked as a team: one counted, one held the rope, and one helped everyone breathe slowly until the platform was steady.",
        ),
        QAItem(
            question="What changed by the end of the story?",
            answer=f"{hero.id}'s hiccough faded, the platform reached the dock, and everyone could cross safely.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is teamwork?",
            answer="Teamwork is when people help each other and do different jobs together to reach the same goal.",
        ),
        QAItem(
            question="What is a platform?",
            answer="A platform is a flat surface that can hold people, animals, or things so they can stand or travel on it.",
        ),
        QAItem(
            question="What is a hiccough?",
            answer="A hiccough is a quick, repeated jump in your breathing that can make you pause while you talk or work.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    lines += [f"{i}. {p}" for i, p in enumerate(sample.prompts, 1)]
    lines.append("")
    lines.append("== story qa ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== world qa ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for e in world.entities.values():
        lines.append(f"{e.id}: {e.type} meters={e.meters} memes={e.memes}")
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


def generate(params: StoryParams) -> StorySample:
    world = tell(PLACES[params.place], params.hero, [params.helper1, params.helper2, params.helper3])
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


def valid_combos() -> list[tuple[str, str]]:
    return [(p, "hiccough") for p in PLACES]


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show fixable/1."))
    return sorted(set(asp.atoms(model, "fixable")))


def build_default_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    return resolve_params(args, rng)


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    return StoryParams(
        place=args.place or rng.choice(list(PLACES)),
        problem=args.problem or "hiccough",
        hero=args.hero or "Pip",
        helper1=args.helper1 or "Hale",
        helper2=args.helper2 or "Brim",
        helper3=args.helper3 or "Pipkin",
    )


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show fixable/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(asp_valid_combos())
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        curated = [StoryParams(place=p, problem=pr, hero="Pip", helper1="Hale", helper2="Brim", helper3="Pipkin")
                   for p, pr in CURATED]
        samples = [generate(p) for p in curated]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 20):
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
        emit(sample, trace=args.trace, qa=args.qa, header=f"### variant {i+1}" if len(samples) > 1 else "")
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()

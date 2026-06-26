#!/usr/bin/env python3
"""
A heartwarming storyworld about a strange little transition: a timid child helps
a susceptible garden creature solve a problem, uncover a twist, and make a kind
transformation.
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
# Core world model
# ---------------------------------------------------------------------------

THRESHOLD = 1.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"  # character | thing
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    meter: dict[str, float] = field(default_factory=dict)
    meme: dict[str, float] = field(default_factory=dict)
    tags: set[str] = field(default_factory=set)

    def __post_init__(self):
        self.meter = dict(self.meter)
        self.meme = dict(self.meme)

    def pronoun(self, case: str = "subject") -> str:
        mapping = {
            "child": {"subject": "they", "object": "them", "possessive": "their"},
            "girl": {"subject": "she", "object": "her", "possessive": "her"},
            "boy": {"subject": "he", "object": "him", "possessive": "his"},
            "creature": {"subject": "it", "object": "it", "possessive": "its"},
        }
        return mapping.get(self.type, mapping["creature"])[case]

    def name_or_label(self) -> str:
        return self.label or self.id


@dataclass
class Place:
    name: str
    setting: str
    supports: set[str] = field(default_factory=set)


@dataclass
class Problem:
    id: str
    title: str
    symptom: str
    cause: str
    solution_tool: str
    twist: str
    transformation: str
    keyword: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Helper:
    id: str
    label: str
    tool: str
    effect: str
    kindness: str


class World:
    def __init__(self, place: Place):
        self.place = place
        self.entities: dict[str, Entity] = {}
        self.lines: list[str] = []
        self.facts: dict = {}

    def add(self, e: Entity) -> Entity:
        self.entities[e.id] = e
        return e

    def get(self, eid: str) -> Entity:
        return self.entities[eid]

    def say(self, text: str) -> None:
        if text:
            self.lines.append(text)

    def render(self) -> str:
        return " ".join(self.lines)


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------

PLACES = {
    "garden": Place(name="the garden", setting="outside", supports={"leaf", "hive", "stone"}),
    "attic": Place(name="the attic", setting="inside", supports={"box", "dust", "lamp"}),
    "workshop": Place(name="the workshop", setting="inside", supports={"gear", "clock", "rope"}),
    "courtyard": Place(name="the courtyard", setting="outside", supports={"fountain", "bench", "vine"}),
}

PROBLEMS = {
    "whispering_box": Problem(
        id="whispering_box",
        title="a strange box that kept whispering",
        symptom="it made a soft worried hum",
        cause="a tiny spring was stuck",
        solution_tool="a small key",
        twist="the box was not scary at all; it was asking for help",
        transformation="it became a music box that played a gentle tune",
        keyword="strange",
        tags={"strange", "problem", "twist", "transformation"},
    ),
    "shy_lantern": Problem(
        id="shy_lantern",
        title="a lantern that kept going dim",
        symptom="its light flickered like a sleepy blink",
        cause="dust was hiding on the glass",
        solution_tool="a soft cloth",
        twist="the lantern was not broken; it was only tired and dusty",
        transformation="it shone warm and bright again",
        keyword="susceptible",
        tags={"susceptible", "problem", "transformation"},
    ),
    "wobbly_bridge": Problem(
        id="wobbly_bridge",
        title="a little bridge that wobbled during a transition",
        symptom="it shook whenever anyone stepped on it",
        cause="one rope knot was loose",
        solution_tool="a knot puller",
        twist="the bridge was safe, but it needed careful attention for the change",
        transformation="it became steady enough for a happy crossing",
        keyword="transition",
        tags={"transition", "problem", "twist", "transformation"},
    ),
}

HELPERS = {
    "key": Helper(
        id="key",
        label="a small key",
        tool="key",
        effect="turned the stuck spring",
        kindness="careful",
    ),
    "cloth": Helper(
        id="cloth",
        label="a soft cloth",
        tool="cloth",
        effect="wiped away the dust",
        kindness="gentle",
    ),
    "puller": Helper(
        id="puller",
        label="a knot puller",
        tool="puller",
        effect="tugged the knot loose",
        kindness="patient",
    ),
}

CHILD_NAMES = ["Milo", "Nina", "Aria", "Jules", "Penny", "Theo", "Luna", "Eli"]
CREATURE_NAMES = ["Pip", "Moss", "Bibi", "Nori", "Tiko"]


# ---------------------------------------------------------------------------
# Story params
# ---------------------------------------------------------------------------

@dataclass
class StoryParams:
    place: str
    problem: str
    child_name: str
    child_type: str
    creature_name: str
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# Reasoning / ASP twin
# ---------------------------------------------------------------------------

ASP_RULES = r"""
kind_problem(P) :- problem(P).
kind_fix(P,H) :- problem(P), helper(H), needs(P,T), tool(H,T).
resolved(P) :- kind_fix(P,_).
twist(P) :- problem(P), surprise(P).
transform(P) :- resolved(P), resolved_to(P,_).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid in PLACES:
        lines.append(asp.fact("place", pid))
    for pid, p in PROBLEMS.items():
        lines.append(asp.fact("problem", pid))
        lines.append(asp.fact("needs", pid, p.solution_tool))
        lines.append(asp.fact("surprise", pid))
    for hid, h in HELPERS.items():
        lines.append(asp.fact("helper", hid))
        lines.append(asp.fact("tool", hid, h.tool))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def reasonableness_gate(place: Place, problem: Problem) -> bool:
    return problem.id in PROBLEMS and place.name and problem.solution_tool in {h.tool for h in HELPERS.values()}


# ---------------------------------------------------------------------------
# Story logic
# ---------------------------------------------------------------------------

def setup_world(params: StoryParams) -> World:
    place = PLACES[params.place]
    world = World(place)
    child = world.add(Entity(id=params.child_name, kind="character", type=params.child_type))
    creature = world.add(Entity(id=params.creature_name, kind="character", type="creature", label=params.creature_name))
    problem = PROBLEMS[params.problem]
    tool = world.add(Entity(id=problem.solution_tool, type="tool", label=HELPERS[{
        "a small key": "key",
        "a soft cloth": "cloth",
        "a knot puller": "puller",
    }[problem.solution_tool]].label))
    world.facts.update(child=child, creature=creature, problem=problem, tool=tool, place=place)
    return world


def tell(world: World) -> World:
    child: Entity = world.facts["child"]
    creature: Entity = world.facts["creature"]
    problem: Problem = world.facts["problem"]
    place: Place = world.facts["place"]

    world.say(f"One day at {place.name}, {child.name_or_label()} met {creature.name_or_label()}, a tiny friend with a strange little trouble.")
    world.say(f"{creature.name_or_label()} had {problem.symptom}, and {child.name_or_label()} could see it was making the poor friend look worried.")
    world.say(f"{child.name_or_label()} did not laugh. {child.pronoun('subject').capitalize()} knelt down and started to think of a kind way to help.")

    helper = HELPERS[problem.solution_tool if problem.solution_tool in {"key", "cloth", "puller"} else "key"]
    world.say(f"After a careful look, {child.name_or_label()} found {helper.label} and used it in a gentle, patient way.")
    world.say(f"It {helper.effect}, and the mystery answered itself: {problem.twist}.")

    creature.meter["relief"] = 1.0
    child.meme["pride"] = 1.0
    child.meme["care"] = 1.0
    creature.meme["trust"] = 1.0
    world.facts["helper"] = helper

    world.say(f"That was the twist, and it changed everything. {problem.transformation.capitalize()}.")
    world.say(f"{creature.name_or_label()} gave a bright little sound, and {child.name_or_label()} smiled because helping had turned the day warm and sweet.")
    return world


def generation_prompts(world: World) -> list[str]:
    p: Problem = world.facts["problem"]
    c: Entity = world.facts["child"]
    return [
        f'Write a heartwarming short story for a young child that includes the word "{p.keyword}" and a kind solution.',
        f"Tell a gentle story where {c.name_or_label()} helps a small friend with {p.title} and discovers a surprise.",
        f'Write a simple story about problem solving, a twist, and a transformation in {world.place.name}.',
    ]


def story_qa(world: World) -> list[QAItem]:
    child: Entity = world.facts["child"]
    creature: Entity = world.facts["creature"]
    problem: Problem = world.facts["problem"]
    helper: Helper = world.facts["helper"]
    place: Place = world.place
    return [
        QAItem(
            question=f"Who helped {creature.name_or_label()} at {place.name}?",
            answer=f"{child.name_or_label()} helped {creature.name_or_label()} at {place.name}.",
        ),
        QAItem(
            question=f"What problem did {creature.name_or_label()} have?",
            answer=f"{creature.name_or_label()} had {problem.symptom}, because {problem.cause}.",
        ),
        QAItem(
            question=f"What did {child.name_or_label()} use to fix it?",
            answer=f"{child.name_or_label()} used {helper.label}, and it {helper.effect}.",
        ),
        QAItem(
            question="What was the twist in the story?",
            answer=f"The twist was that {problem.twist}.",
        ),
        QAItem(
            question="What changed by the end?",
            answer=f"By the end, {problem.transformation}.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    problem: Problem = world.facts["problem"]
    helper: Helper = world.facts["helper"]
    qa = [
        QAItem(
            question="What does it mean to solve a problem?",
            answer="To solve a problem means to find a way to make a trouble better or go away.",
        ),
        QAItem(
            question="What is a twist in a story?",
            answer="A twist is a surprise that changes what you thought was happening.",
        ),
        QAItem(
            question="What is a transformation?",
            answer="A transformation is a change from one form or state into another.",
        ),
    ]
    if problem.keyword == "strange":
        qa.append(QAItem(
            question="What can strange mean?",
            answer="Strange means unusual or surprising, but not always bad.",
        ))
    if problem.keyword == "susceptible":
        qa.append(QAItem(
            question="What does susceptible mean?",
            answer="Susceptible means something can be easily affected by things like dust, weather, or feelings.",
        ))
    if problem.keyword == "transition":
        qa.append(QAItem(
            question="What is a transition?",
            answer="A transition is a change from one state or place to another, like moving from waiting to crossing.",
        ))
    qa.append(QAItem(
        question=f"What is {helper.label} used for?",
        answer=f"{helper.label.capitalize()} is used carefully to help fix the story's problem.",
    ))
    return qa


def format_qa(sample: StorySample) -> str:
    out = ["== prompts =="]
    out.extend(f"- {p}" for p in sample.prompts)
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


# ---------------------------------------------------------------------------
# ASP helpers
# ---------------------------------------------------------------------------

def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show resolved/1."))
    return sorted(set(asp.atoms(model, "resolved")))


def asp_verify() -> int:
    python_ok = all(reasonableness_gate(PLACES[p], PROBLEMS[k]) for p in PLACES for k in PROBLEMS)
    asp_ok = bool(asp_valid_combos())
    if python_ok and asp_ok:
        print("OK: ASP and Python gates are both satisfied.")
        return 0
    print("Mismatch between ASP and Python gates.")
    return 1


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

CURATED = [
    StoryParams(place="garden", problem="whispering_box", child_name="Milo", child_type="boy", creature_name="Pip"),
    StoryParams(place="attic", problem="shy_lantern", child_name="Nina", child_type="girl", creature_name="Moss"),
    StoryParams(place="courtyard", problem="wobbly_bridge", child_name="Aria", child_type="girl", creature_name="Bibi"),
]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Heartwarming problem-solving storyworld.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--problem", choices=PROBLEMS)
    ap.add_argument("--name", dest="child_name")
    ap.add_argument("--gender", dest="child_type", choices=["girl", "boy"])
    ap.add_argument("--creature")
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
    if args.problem and args.place:
        if not reasonableness_gate(PLACES[args.place], PROBLEMS[args.problem]):
            raise StoryError("No valid story matches that place and problem.")
    place = args.place or rng.choice(list(PLACES))
    problem = args.problem or rng.choice(list(PROBLEMS))
    child_type = args.child_type or rng.choice(["girl", "boy"])
    child_name = args.child_name or rng.choice(CHILD_NAMES)
    creature_name = args.creature or rng.choice(CREATURE_NAMES)
    return StoryParams(place=place, problem=problem, child_name=child_name, child_type=child_type, creature_name=creature_name)


def generate(params: StoryParams) -> StorySample:
    world = setup_world(params)
    tell(world)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


def dump_trace(world: World) -> str:
    lines = ["--- trace ---"]
    for e in world.entities.values():
        lines.append(f"{e.id}: meter={e.meter} meme={e.meme}")
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


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show resolved/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        model = asp.one_model(asp_program("#show resolved/1."))
        print(asp.atoms(model, "resolved"))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        for p in CURATED:
            samples.append(generate(p))
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 20):
            i += 1
            rng = random.Random(base_seed + i)
            try:
                params = resolve_params(args, rng)
            except StoryError as err:
                print(err)
                return
            params.seed = base_seed + i
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
        if len(samples) > 1:
            header = f"### variant {idx + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if idx < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/motley_problem_solving_animal_story.py
======================================================================

A small animal-story world about a motley group of friends solving a simple
problem together. The core premise is: a child-facing animal cast finds itself
stuck, searches for clues, tests a few ideas, and uses the right tool or plan to
make things work.

The word "motley" appears in every story, and the stories are driven by
simulated world state rather than fixed text swapping.
"""

from __future__ import annotations

import argparse
import copy
import json
import os
import random
import sys
from collections import defaultdict
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
    role: str = ""
    traits: list[str] = field(default_factory=list)
    attrs: dict = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman", "hen"}
        male = {"boy", "father", "dad", "man", "rooster"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    @property
    def label_word(self) -> str:
        return self.label or self.type


@dataclass
class AnimalKind:
    id: str
    noun: str
    sound: str
    home: str
    help_style: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Problem:
    id: str
    noun: str
    thing: str
    place: str
    stuck_verb: str
    mess: str
    risk: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Tool:
    id: str
    noun: str
    phrase: str
    action: str
    fits: set[str] = field(default_factory=set)
    solves: set[str] = field(default_factory=set)
    tags: set[str] = field(default_factory=set)


@dataclass
class StoryParams:
    animal1: str
    animal2: str
    problem: str
    tool: str
    helper: str
    seed: Optional[int] = None


class World:
    def __init__(self) -> None:
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
        clone = World()
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        clone.facts = copy.deepcopy(self.facts)
        return clone


ANIMALS = {
    "fox": AnimalKind("fox", "fox", "yip", "burrow", "quick"),
    "rabbit": AnimalKind("rabbit", "rabbit", "boing", "warren", "careful"),
    "bear": AnimalKind("bear", "bear", "grr", "cave", "strong"),
    "mouse": AnimalKind("mouse", "mouse", "squeak", "nest", "tiny"),
    "duck": AnimalKind("duck", "duck", "quack", "pond", "wavy"),
}

PROBLEMS = {
    "stuck_gate": Problem("stuck_gate", "gate", "a garden gate", "the garden path", "pushes",
                          "stuck shut", "blocks the way", tags={"gate", "stuck"}),
    "fallen_apple": Problem("fallen_apple", "apple", "a red apple", "the tree roots", "reaches",
                            "just out of reach", "cannot be picked", tags={"apple", "reach"}),
    "wet_bridge": Problem("wet_bridge", "bridge", "a little bridge", "the creek", "steps on",
                          "slippery with rain", "is too slick", tags={"bridge", "wet"}),
    "twisted_ribbon": Problem("twisted_ribbon", "ribbon", "a ribbon", "the play fence", "pulls",
                              "tangled up", "won't come loose", tags={"ribbon", "tangled"}),
}

TOOLS = {
    "stick": Tool("stick", "stick", "a long stick", "used as a lever", fits={"stuck", "reach"}, solves={"stuck_gate", "fallen_apple"}, tags={"stick"}),
    "towel": Tool("towel", "towel", "a soft towel", "used to dry things", fits={"wet"}, solves={"wet_bridge"}, tags={"towel"}),
    "twine": Tool("twine", "twine", "a bit of twine", "used to tie and pull", fits={"tangled"}, solves={"twisted_ribbon"}, tags={"twine"}),
    "bucket": Tool("bucket", "bucket", "a little bucket of water", "used to rinse away mud", fits={"wet"}, solves={"wet_bridge"}, tags={"bucket"}),
}

HABITS = ["curious", "gentle", "busy", "brave", "kind", "patient"]
NAMES = {
    "fox": ["Fin", "Fia", "Pip"],
    "rabbit": ["Ruby", "Rory", "Nia"],
    "bear": ["Bram", "Bess", "Milo"],
    "mouse": ["Mina", "Moss", "Mabel"],
    "duck": ["Dina", "Duke", "Dot"],
}


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for aid in ANIMALS:
        for pid, p in PROBLEMS.items():
            for tid, t in TOOLS.items():
                if pid in t.solves:
                    combos.append((aid, pid, tid))
    return combos


def explain_rejection(problem: Problem, tool: Tool) -> str:
    return (
        f"(No story: {tool.noun} does not fit this problem. "
        f"The animals need a tool that can really help with {problem.mess}.)"
    )


def best_tool() -> Tool:
    return next(iter(TOOLS.values()))


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Motley animal problem-solving story world.")
    ap.add_argument("--animal1", choices=ANIMALS)
    ap.add_argument("--animal2", choices=ANIMALS)
    ap.add_argument("--problem", choices=PROBLEMS)
    ap.add_argument("--tool", choices=TOOLS)
    ap.add_argument("--helper", choices=["friend", "adult", "sibling", "neighbor"])
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
    if args.problem and args.tool:
        p, t = PROBLEMS[args.problem], TOOLS[args.tool]
        if args.problem not in t.solves:
            raise StoryError(explain_rejection(p, t))
    combos = [c for c in valid_combos()
              if (args.animal1 is None or c[0] == args.animal1)
              and (args.problem is None or c[1] == args.problem)
              and (args.tool is None or c[2] == args.tool)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    animal1, problem, tool = rng.choice(sorted(combos))
    animal2 = args.animal2 or rng.choice([a for a in ANIMALS if a != animal1])
    helper = args.helper or rng.choice(["friend", "adult", "sibling", "neighbor"])
    return StoryParams(animal1=animal1, animal2=animal2, problem=problem, tool=tool, helper=helper)


def _make_character(world: World, aid: str, role: str) -> Entity:
    kind = ANIMALS[aid]
    return world.add(Entity(
        id=aid,
        kind="character",
        type={"fox": "boy", "rabbit": "girl", "bear": "boy", "mouse": "girl", "duck": "girl"}[aid],
        label=kind.noun,
        role=role,
        traits=["motley", "helpful"],
    ))


def tell(params: StoryParams) -> World:
    world = World()
    a = _make_character(world, params.animal1, "problem-solver")
    b = _make_character(world, params.animal2, "helper")
    prob = PROBLEMS[params.problem]
    tool = TOOLS[params.tool]

    a.memes["curiosity"] += 1
    b.memes["kindness"] += 1
    world.say(
        f"A motley little group of animals lived by the {ANIMALS[params.animal1].home}. "
        f"{a.id} and {b.id} were among the friends, and they liked to solve small troubles together."
    )
    world.say(
        f"One day, {a.id} found {prob.thing} {prob.place}. It was {prob.mess}, and that meant it {prob.risk}."
    )
    world.para()
    world.say(
        f'{a.id} sniffed and thought. "{a.pronoun().capitalize()} could not fix this alone," '
        f"{a.id} said, so {b.id} came closer to help."
    )
    world.say(
        f'Their little ideas were motley too: one try was too weak, another was too wobbly, '
        f'but then {b.id} noticed {tool.phrase}.'
    )
    world.para()
    prob_ent = world.add(Entity(id="problem", kind="thing", type="problem", label=prob.noun))
    prob_ent.meters["stuck"] = 1.0
    tool_ent = world.add(Entity(id="tool", kind="thing", type="tool", label=tool.noun))
    tool_ent.attrs["action"] = tool.action

    if params.problem == "stuck_gate":
        world.say(f"{b.id} pushed the gate with {tool.action}, and {a.id} held the other side.")
        world.say("The gate gave a soft creak and swung open at last.")
    elif params.problem == "fallen_apple":
        world.say(f"{b.id} used {tool.phrase} as a lever while {a.id} steadied the branch.")
        world.say("The apple dropped safely into the grass, plump and bright.")
    elif params.problem == "wet_bridge":
        world.say(f"{b.id} used {tool.phrase} to dry the slippery boards while {a.id} waited.")
        world.say("Soon the bridge was safe to cross, little by little.")
    else:
        world.say(f"{a.id} and {b.id} used {tool.phrase} to untwist the ribbon gently.")
        world.say("With a tiny tug, the ribbon came loose and fluttered free.")

    a.memes["joy"] += 1
    b.memes["joy"] += 1
    world.para()
    world.say(
        f"In the end, the motley friends smiled at their neat solution, and the path was clear again."
    )

    world.facts.update(
        a=a, b=b, prob=prob, tool=tool, helper=params.helper,
        solved=True, name1=a.id, name2=b.id
    )
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write an animal story that includes the word "motley" and shows two friends solving a problem together.',
        f"Tell a short story about {f['a'].id} and {f['b'].id} finding a problem and using {f['tool'].noun} to fix it.",
        f"Write a gentle animal story where a motley group works out a tricky problem with patience and teamwork.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    return [
        QAItem(
            question="What kind of group was in the story?",
            answer="It was a motley little group of animals, which means the friends were a mixed and lively bunch. They worked together even though they were different from one another."
        ),
        QAItem(
            question="What problem did the animals solve?",
            answer=f"They solved the problem of {f['prob'].thing} being {f['prob'].mess}. They used a patient plan so the trouble would stop."
        ),
        QAItem(
            question="How did the friends fix it?",
            answer=f"They used {f['tool'].phrase} and worked together. One friend held steady while the other did the careful part, so the problem was solved."
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does motley mean?",
            answer="Motley means mixed in a colorful or uneven way. It is a word for a group that has different kinds of people or animals in it."
        ),
        QAItem(
            question="What is teamwork?",
            answer="Teamwork means people or animals help each other and do a job together. It can make a hard problem easier to solve."
        ),
        QAItem(
            question="Why do animals need tools sometimes?",
            answer="Animals in stories use tools to reach, lift, dry, or untangle things they cannot fix by themselves. A good tool can make a problem much simpler."
        ),
    ]


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


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if e.role:
            bits.append(f"role={e.role}")
        lines.append(f"  {e.id:8} ({e.type:8}) {' '.join(bits)}")
    return "\n".join(lines)


ASP_RULES = r"""
valid(A,P,T) :- animal(A), problem(P), tool(T), solves(T,P).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for a in ANIMALS:
        lines.append(asp.fact("animal", a))
    for p in PROBLEMS:
        lines.append(asp.fact("problem", p))
    for t, tool in TOOLS.items():
        lines.append(asp.fact("tool", t))
        for p in sorted(tool.solves):
            lines.append(asp.fact("solves", t, p))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    import io
    from contextlib import redirect_stdout
    rc = 0
    if set(asp_valid_combos()) != set(valid_combos()):
        print("MISMATCH in valid_combos()")
        rc = 1
    try:
        sample = generate(resolve_params(argparse.Namespace(animal1=None, animal2=None, problem=None, tool=None, helper=None), random.Random(1)))
        buf = io.StringIO()
        with redirect_stdout(buf):
            emit(sample)
    except Exception as e:
        print(f"SMOKE TEST FAILED: {e}")
        rc = 1
    else:
        print("OK: verify smoke test passed.")
    return rc


CURATED = [
    StoryParams(animal1="fox", animal2="rabbit", problem="stuck_gate", tool="stick", helper="friend"),
    StoryParams(animal1="mouse", animal2="duck", problem="twisted_ribbon", tool="twine", helper="neighbor"),
    StoryParams(animal1="bear", animal2="fox", problem="wet_bridge", tool="towel", helper="adult"),
]


def generate(params: StoryParams) -> StorySample:
    if params.animal1 not in ANIMALS:
        raise StoryError("unknown animal1")
    if params.problem not in PROBLEMS:
        raise StoryError("unknown problem")
    if params.tool not in TOOLS:
        raise StoryError("unknown tool")
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


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print("\n".join(f"{a} {p} {t}" for a, p, t in asp_valid_combos()))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
            i += 1
            try:
                params = resolve_params(args, random.Random(base_seed + i))
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
        if len(samples) > 1:
            print(f"### variant {idx + 1}")
        emit(sample, trace=args.trace, qa=args.qa)
        if idx < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()

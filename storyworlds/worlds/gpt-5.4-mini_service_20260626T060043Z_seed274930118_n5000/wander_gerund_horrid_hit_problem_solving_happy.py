#!/usr/bin/env python3
"""
storyworlds/worlds/wander_gerund_horrid_hit_problem_solving_happy.py
====================================================================

A small slice-of-life story world about wandering, a horrid snag, and a
careful problem-solving turn that ends happily.

Seed premise:
- A child loves wandering around ordinary places.
- While wandering, they hit a horrid problem.
- A parent or helper notices, and they solve it together.
- The ending proves the day is safe, calm, and happy.

The domain is intentionally small and constraint-checked:
- setting + problem determine whether the situation is reasonable
- tool selection must actually help with the problem
- invalid explicit choices raise StoryError

This script follows the Storyweavers contract and includes an inline ASP twin
for parity verification.
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
# World data
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

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman"}
        male = {"boy", "father", "dad", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str
    indoor: bool
    affords: set[str] = field(default_factory=set)


@dataclass
class Problem:
    id: str
    verb: str
    gerund: str
    hit: str
    horrid: str
    mess: str
    zone: set[str]
    tags: set[str] = field(default_factory=set)


@dataclass
class Tool:
    id: str
    label: str
    phrase: str
    helps: set[str]
    prep: str
    tail: str
    plural: bool = False


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
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
        import copy
        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.paragraphs = [[]]
        clone.fired = set(self.fired)
        clone.facts = dict(self.facts)
        return clone


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------
SETTINGS = {
    "park": Setting("the park", False, affords={"wander"}),
    "street": Setting("the quiet street", False, affords={"wander"}),
    "market": Setting("the little market", False, affords={"wander"}),
    "library": Setting("the library steps", False, affords={"wander"}),
    "kitchen": Setting("the kitchen", True, affords={"wander"}),
}

PROBLEMS = {
    "puddle": Problem(
        id="puddle",
        verb="step around a puddle",
        gerund="wandering around the puddles",
        hit="hit a horrid puddle",
        horrid="horrid and slippery",
        mess="wet",
        zone={"feet"},
        tags={"wet", "puddle"},
    ),
    "spill": Problem(
        id="spill",
        verb="move past a spill",
        gerund="wandering past the spill",
        hit="hit a horrid spill",
        horrid="horrid and sticky",
        mess="sticky",
        zone={"feet"},
        tags={"sticky", "spill"},
    ),
    "mud": Problem(
        id="mud",
        verb="get around the mud",
        gerund="wandering through the mud",
        hit="hit a horrid patch of mud",
        horrid="horrid and squishy",
        mess="muddy",
        zone={"feet"},
        tags={"mud", "dirty"},
    ),
    "jammed_door": Problem(
        id="jammed_door",
        verb="open a jammed door",
        gerund="wandering up to the door",
        hit="hit a horrid jam",
        horrid="horrid and stuck",
        mess="stuck",
        zone={"hands"},
        tags={"door", "stuck"},
    ),
}

TOOLS = [
    Tool(
        id="boots",
        label="rain boots",
        phrase="their rain boots",
        helps={"wet", "muddy"},
        prep="put on their rain boots",
        tail="walked on without wet feet",
        plural=True,
    ),
    Tool(
        id="towel",
        label="a towel",
        phrase="a towel",
        helps={"wet", "sticky"},
        prep="use a towel to wipe it up",
        tail="kept the floor neat",
    ),
    Tool(
        id="rag",
        label="a rag",
        phrase="a soft rag",
        helps={"sticky", "stuck"},
        prep="pick up a soft rag",
        tail="smoothed the trouble away",
    ),
    Tool(
        id="key",
        label="the spare key",
        phrase="the spare key",
        helps={"stuck"},
        prep="find the spare key",
        tail="opened the door with a small click",
    ),
]

NAMES = ["Mina", "Theo", "Ivy", "Noah", "Lena", "Ben", "Maya", "Owen"]
TRAITS = ["curious", "cheerful", "gentle", "careful", "lively", "patient"]


# ---------------------------------------------------------------------------
# Params
# ---------------------------------------------------------------------------
@dataclass
class StoryParams:
    place: str
    problem: str
    tool: str
    name: str
    gender: str
    parent: str
    trait: str
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
problem_at_risk(P) :- problem(P), zone(P, Z), tool_region(T, Z), tool(T).
helps_tool(T, P) :- tool(T), problem(P), helps(T, M), mess(P, M).
valid_story(S, P, T) :- setting(S), problem(P), tool(T), setting_affords(S, wander),
                        problem_at_risk(P), helps_tool(T, P).
"""

def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid, s in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        if s.indoor:
            lines.append(asp.fact("indoor", sid))
        for a in sorted(s.affords):
            lines.append(asp.fact("setting_affords", sid, a))
    for pid, p in PROBLEMS.items():
        lines.append(asp.fact("problem", pid))
        lines.append(asp.fact("mess", pid, p.mess))
        for z in sorted(p.zone):
            lines.append(asp.fact("zone", pid, z))
    for t in TOOLS:
        lines.append(asp.fact("tool", t.id))
        for m in sorted(t.helps):
            lines.append(asp.fact("helps", t.id, m))
        if "wet" in t.helps or "muddy" in t.helps:
            lines.append(asp.fact("tool_region", t.id, "feet"))
        if "stuck" in t.helps:
            lines.append(asp.fact("tool_region", t.id, "hands"))
        if "sticky" in t.helps:
            lines.append(asp.fact("tool_region", t.id, "feet"))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_stories() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/3."))
    return sorted(set(asp.atoms(model, "valid_story")))


# ---------------------------------------------------------------------------
# Reasonableness gates
# ---------------------------------------------------------------------------
def problem_at_risk(problem: Problem) -> bool:
    return bool(problem.zone)


def select_tool(problem: Problem) -> Optional[Tool]:
    for tool in TOOLS:
        if problem.mess in tool.helps:
            return tool
    return None


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for place, setting in SETTINGS.items():
        if "wander" not in setting.affords:
            continue
        for pid, problem in PROBLEMS.items():
            if not problem_at_risk(problem):
                continue
            tool = select_tool(problem)
            if tool is None:
                continue
            combos.append((place, pid, tool.id))
    return combos


def explain_rejection(problem: Problem) -> str:
    tool = select_tool(problem)
    if tool is None:
        return f"(No story: nothing in the tool box helps with {problem.id}.)"
    return f"(No story: {tool.label} does not sensibly solve {problem.id}.)"


# ---------------------------------------------------------------------------
# Story world simulation
# ---------------------------------------------------------------------------
def _do_wander(world: World, hero: Entity, problem: Problem, narrate: bool = True) -> None:
    hero.meters["wandered"] = hero.meters.get("wandered", 0) + 1
    hero.memes["curiosity"] = hero.memes.get("curiosity", 0) + 1
    world.facts["wandering"] = True
    world.facts["problem"] = problem
    if narrate:
        world.say(f"{hero.pronoun().capitalize()} kept wandering, looking at little details along the way.")


def _hit_problem(world: World, hero: Entity, problem: Problem, narrate: bool = True) -> None:
    sig = ("hit", hero.id, problem.id)
    if sig in world.fired:
        return
    world.fired.add(sig)
    hero.memes["surprise"] = hero.memes.get("surprise", 0) + 1
    hero.memes["worry"] = hero.memes.get("worry", 0) + 1
    world.facts["hit_problem"] = problem.id
    if narrate:
        world.say(f"Then {hero.id} {problem.hit}. It was {problem.horrid}, so everyone had to stop and think.")


def predict_problem(world: World, hero: Entity, problem: Problem) -> bool:
    sim = world.copy()
    _do_wander(sim, hero, problem, narrate=False)
    _hit_problem(sim, hero, problem, narrate=False)
    return True


def setup_story(world: World, hero: Entity, parent: Entity, problem: Problem) -> None:
    world.say(f"{hero.id} was a little {hero.type} who liked to wander around and notice small things.")
    world.say(f"{hero.pronoun().capitalize()} loved {problem.gerund}, because the whole world felt calm and interesting.")
    world.say(f"One day, {hero.id} and {hero.pronoun('possessive')} {parent.label} went to {world.setting.place}.")
    world.say(f"{hero.id} was carrying a small bag and smiling at the ordinary morning.")


def conflict_story(world: World, hero: Entity, parent: Entity, problem: Problem) -> None:
    world.para()
    _do_wander(world, hero, problem, narrate=True)
    _hit_problem(world, hero, problem, narrate=True)
    world.say(f"{parent.label.capitalize()} looked down and said, \"Let's solve this together.\"")


def resolve_story(world: World, hero: Entity, parent: Entity, problem: Problem, tool: Tool) -> None:
    world.para()
    hero.memes["calm"] = hero.memes.get("calm", 0) + 1
    hero.memes["joy"] = hero.memes.get("joy", 0) + 1
    world.say(f"{hero.pronoun('possessive').capitalize()} {parent.label} chose to {tool.prep}.")
    world.say(
        f"That helped with the {problem.mess} part, and soon {hero.id} was back to "
        f"{problem.gerund} without a fuss."
    )
    world.say(
        f"{tool.tail.capitalize()}, and the walk felt easy again."
    )
    world.say(
        f"{hero.id} gave a happy grin, because the horrid moment had turned into a neat little fix."
    )


def tell(setting: Setting, problem: Problem, tool: Tool, name: str,
         gender: str, parent_type: str, trait: str) -> World:
    world = World(setting)
    hero = world.add(Entity(id=name, kind="character", type=gender, meters={}, memes={}))
    parent = world.add(Entity(id="Parent", kind="character", type=parent_type, label="parent"))
    world.facts["hero"] = hero
    world.facts["parent"] = parent
    world.facts["tool"] = tool
    world.facts["setting"] = setting

    setup_story(world, hero, parent, problem)
    conflict_story(world, hero, parent, problem)
    resolve_story(world, hero, parent, problem, tool)
    world.facts["resolved"] = True
    world.facts["trait"] = trait
    return world


# ---------------------------------------------------------------------------
# Q&A
# ---------------------------------------------------------------------------
def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    problem = f["problem"]
    tool = f["tool"]
    return [
        f'Write a short slice-of-life story about a child named {hero.id} who keeps wandering until they {problem.hit}.',
        f"Tell a gentle story where {hero.id} encounters something {problem.horrid} and solves it with {tool.label}.",
        f'Write a child-friendly story that includes "wandering", "horrid", and "hit", then ends happily.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero: Entity = f["hero"]
    parent: Entity = f["parent"]
    problem: Problem = f["problem"]
    tool: Tool = f["tool"]
    return [
        QAItem(
            question=f"What was {hero.id} doing before the trouble started?",
            answer=f"{hero.id} was wandering around {world.setting.place} and looking at small details.",
        ),
        QAItem(
            question=f"What happened when {hero.id} kept going?",
            answer=f"{hero.id} {problem.hit}, and the moment felt {problem.horrid}.",
        ),
        QAItem(
            question=f"How did {hero.id} and the {parent.label} solve the problem?",
            answer=f"They used {tool.label} to deal with the {problem.mess} problem, and that made the walk safe again.",
        ),
        QAItem(
            question=f"How did the story end?",
            answer=f"It ended with {hero.id} feeling happy and able to keep wandering in a calm, ordinary way.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    problem: Problem = world.facts["problem"]
    tool: Tool = world.facts["tool"]
    out = [
        QAItem(
            question="What does wandering mean?",
            answer="Wandering means walking around without rushing, usually while looking at things and going where they lead.",
        ),
        QAItem(
            question="What does horrid mean?",
            answer="Horrid means very unpleasant or awful, the kind of thing that makes you want to step back and fix it.",
        ),
        QAItem(
            question="Why do people use tools to solve small problems?",
            answer="People use tools because the right tool makes a problem easier to handle and helps them finish the job safely.",
        ),
    ]
    if "wet" in problem.tags:
        out.append(QAItem(question="What helps with wet messes?", answer="Things like towels and boots can help with wet messes."))
    if "sticky" in problem.tags:
        out.append(QAItem(question="What helps with sticky messes?", answer="A towel can help wipe up a sticky mess."))
    if "stuck" in problem.tags:
        out.append(QAItem(question="What helps with something stuck?", answer="A key or a rag can help with something stuck, depending on the problem."))
    if tool.id == "boots":
        out.append(QAItem(question="What are rain boots for?", answer="Rain boots help keep feet dry when the ground is wet or muddy."))
    return out


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
    lines.append("== (3) World knowledge ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Params / generation
# ---------------------------------------------------------------------------
def valid_gender_for_problem(problem: Problem, gender: str) -> bool:
    return True


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.problem and args.tool:
        problem = PROBLEMS[args.problem]
        tool = next((t for t in TOOLS if t.id == args.tool), None)
        if tool is None or problem.mess not in tool.helps:
            raise StoryError(explain_rejection(problem))

    combos = [c for c in valid_combos()
              if (args.place is None or c[0] == args.place)
              and (args.problem is None or c[1] == args.problem)
              and (args.tool is None or c[2] == args.tool)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, problem_id, tool_id = rng.choice(sorted(combos))
    name = args.name or rng.choice(NAMES)
    gender = args.gender or rng.choice(["girl", "boy"])
    parent = args.parent or rng.choice(["mother", "father"])
    trait = args.trait or rng.choice(TRAITS)
    return StoryParams(place=place, problem=problem_id, tool=tool_id, name=name,
                       gender=gender, parent=parent, trait=trait)


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.place], PROBLEMS[params.problem],
                 next(t for t in TOOLS if t.id == params.tool),
                 params.name, params.gender, params.parent, params.trait)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Slice-of-life story world: wandering, a horrid snag, and a happy fix."
    )
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--problem", choices=PROBLEMS)
    ap.add_argument("--tool", choices=[t.id for t in TOOLS])
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--parent", choices=["mother", "father"])
    ap.add_argument("--trait")
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


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted({n for n, *_ in world.fired})}")
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
    StoryParams(place="park", problem="puddle", tool="boots", name="Mina", gender="girl", parent="mother", trait="curious"),
    StoryParams(place="market", problem="spill", tool="towel", name="Theo", gender="boy", parent="father", trait="careful"),
    StoryParams(place="library", problem="jammed_door", tool="key", name="Ivy", gender="girl", parent="mother", trait="patient"),
    StoryParams(place="street", problem="mud", tool="boots", name="Ben", gender="boy", parent="father", trait="lively"),
]


def asp_verify() -> int:
    import asp
    py = set(valid_combos())
    model = asp.one_model(asp_program("#show valid_story/3."))
    cl = set(asp.atoms(model, "valid_story"))
    if py == cl:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    print("only in python:", sorted(py - cl))
    print("only in clingo:", sorted(cl - py))
    return 1


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/3."))
    return sorted(set(asp.atoms(model, "valid_story")))


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid_story/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible story combos:\n")
        for item in combos:
            print(" ", item)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)

    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
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

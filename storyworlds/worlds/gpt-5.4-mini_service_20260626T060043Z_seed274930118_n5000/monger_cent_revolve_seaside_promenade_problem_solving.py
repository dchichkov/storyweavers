#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260626T060043Z_seed274930118_n5000/monger_cent_revolve_seaside_promenade_problem_solving.py
==============================================================================================================================

A small fable-style storyworld set on a seaside promenade.

Premise:
- A careful shell-monger at the seaside promenade notices that a lost cent is
  spinning in circles in a fountain basin near the walk.
- The cent's endless revolving draws a little crowd and blocks the path.
- The monger solves the problem by using a simple, gentle method.
- The ending stresses reconciliation and a moral value: patience and kindness
  can settle trouble better than haste.

This script follows the Storyweavers contract: it models state, generates a
single authored story from simulation, exposes Q&A sets, and includes an ASP
twin of the reasonableness gate.
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
    kind: str = "thing"  # character | thing
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
        if self.type in {"monger"}:
            return {"subject": "they", "object": "them", "possessive": "their"}[case]
        if self.type in {"child", "girl", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str = "the seaside promenade"
    affordances: set[str] = field(default_factory=set)


@dataclass
class Problem:
    id: str
    label: str
    verb: str
    gerund: str
    mess: str
    zone: str
    requires: set[str] = field(default_factory=set)
    tags: set[str] = field(default_factory=set)


@dataclass
class Tool:
    id: str
    label: str
    phrase: str
    solves: set[str] = field(default_factory=set)
    helps: set[str] = field(default_factory=set)
    method: str = ""
    plural: bool = False


@dataclass
class World:
    setting: Setting
    entities: dict[str, Entity] = field(default_factory=dict)
    fired: set[tuple] = field(default_factory=set)
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
        import copy

        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        clone.facts = dict(self.facts)
        return clone


THRESHOLD = 1.0


# ---------------------------------------------------------------------------
# Registry content
# ---------------------------------------------------------------------------
SETTINGS = {
    "promenade": Setting(place="the seaside promenade", affordances={"revolve", "harbor"}),
}

PROBLEMS = {
    "cent": Problem(
        id="cent",
        label="cent",
        verb="revolve",
        gerund="revolving",
        mess="spin",
        zone="path",
        requires={"water", "shine"},
        tags={"cent", "revolve"},
    ),
    "kite": Problem(
        id="kite",
        label="kite string",
        verb="tangle",
        gerund="tangling",
        mess="snarl",
        zone="path",
        requires={"wind"},
        tags={"knot"},
    ),
}

TOOLS = [
    Tool(
        id="cloth",
        label="soft cloth",
        phrase="a soft cloth",
        solves={"shine"},
        helps={"cent"},
        method="lift the cent and stop it with the cloth",
    ),
    Tool(
        id="coin_box",
        label="small coin box",
        phrase="a small coin box",
        solves={"keep"},
        helps={"cent"},
        method="gather the cent and carry it to the stall",
    ),
    Tool(
        id="chalk",
        label="chalk mark",
        phrase="a chalk mark",
        solves={"guide"},
        helps={"kite"},
        method="mark a safe place to set the problem aside",
    ),
]

MORALS = [
    "Kind hands can solve a small trouble without making a bigger one.",
    "Patient choices often calm what haste makes worse.",
    "A gentle answer can turn a fuss into a friendly ending.",
]

NAMES = ["Mina", "Nico", "Lena", "Omar", "Iris", "Tavi"]
TRAITS = ["careful", "patient", "gentle", "bright", "steady"]


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
% A problem is at risk on the promenade when it affects the path.
problem_at_risk(P) :- problem(P), zone(P, path).

% A tool is a valid fix when it helps the problem and addresses one of its needs.
solves(T, P) :- tool(T), problem(P), helps(T, P), needs(P, Need), solves_need(T, Need).

valid_fix(P, T) :- problem_at_risk(P), solves(T, P).

valid_story(P, T) :- valid_fix(P, T).
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for sid, s in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        for a in sorted(s.affordances):
            lines.append(asp.fact("affords", sid, a))
    for pid, p in PROBLEMS.items():
        lines.append(asp.fact("problem", pid))
        lines.append(asp.fact("zone", pid, p.zone))
        for need in sorted(p.requires):
            lines.append(asp.fact("needs", pid, need))
        for t in sorted(p.tags):
            lines.append(asp.fact("tag", pid, t))
    for tool in TOOLS:
        lines.append(asp.fact("tool", tool.id))
        for n in sorted(tool.solves):
            lines.append(asp.fact("solves_need", tool.id, n))
        for p in sorted(tool.helps):
            lines.append(asp.fact("helps", tool.id, p))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_fixes() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("#show valid_fix/2."))
    return sorted(set(asp.atoms(model, "valid_fix")))


# ---------------------------------------------------------------------------
# Reasonableness gate
# ---------------------------------------------------------------------------
def problem_at_risk(problem: Problem) -> bool:
    return problem.zone == "path"


def select_tool(problem: Problem) -> Optional[Tool]:
    for tool in TOOLS:
        if problem.id in tool.helps and problem.requires & tool.solves:
            return tool
    return None


def valid_combos() -> list[tuple[str, str]]:
    combos = []
    for place, setting in SETTINGS.items():
        for pid, prob in PROBLEMS.items():
            if place == "promenade" and problem_at_risk(prob) and select_tool(prob):
                combos.append((place, pid))
    return combos


# ---------------------------------------------------------------------------
# Story generation
# ---------------------------------------------------------------------------
@dataclass
class StoryParams:
    place: str
    problem: str
    name: str
    trait: str
    seed: Optional[int] = None


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Fable-style seaside promenade storyworld about problem solving, reconciliation, and moral value."
    )
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--problem", choices=PROBLEMS)
    ap.add_argument("--name")
    ap.add_argument("--trait", choices=TRAITS)
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
    if args.problem:
        prob = PROBLEMS[args.problem]
        if not select_tool(prob):
            raise StoryError("No reasonable tool exists for that problem.")
    combos = [c for c in valid_combos()
              if (args.place is None or c[0] == args.place)
              and (args.problem is None or c[1] == args.problem)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, prob_id = rng.choice(sorted(combos))
    return StoryParams(
        place=place,
        problem=prob_id,
        name=args.name or rng.choice(NAMES),
        trait=args.trait or rng.choice(TRAITS),
    )


def tell(params: StoryParams) -> World:
    setting = SETTINGS[params.place]
    problem = PROBLEMS[params.problem]
    world = World(setting)

    hero = world.add(Entity(id=params.name, kind="character", type="monger"))
    problem_ent = world.add(Entity(id=problem.id, type="cent", label="cent", phrase="a bright cent"))
    crowd = world.add(Entity(id="crowd", kind="character", type="people", label="the crowd", plural=True))
    tool = select_tool(problem)
    if tool is None:
        raise StoryError("Internal mismatch: no tool found for a valid problem.")

    hero.memes["care"] = 1
    problem_ent.meters["spin"] = 1
    problem_ent.meters["blocked"] = 1

    world.say(f"At {setting.place}, there lived a {params.trait} monger named {params.name}.")
    world.say(f"{params.name} sold little shells and listened kindly to every passing tide.")
    world.say(f"One morning, {params.name} saw {problem_ent.label} {problem.gerund} in the stone basin near the walk.")
    world.para()
    world.say(f"The cent kept {problem.gerund}, and each turn made the path busier.")
    world.say(f"A few children stopped to stare, and the crowd began to grumble.")
    world.say(f"{params.name} knew that a small trouble could grow larger if nobody chose wisely.")

    world.facts.update(hero=hero, problem=problem_ent, crowd=crowd, tool=tool, moral=MORALS[0])

    world.para()
    world.say(f"{params.name} looked for a simple answer and found {tool.phrase} in the stall basket.")
    world.say(f"With {tool.phrase}, {params.name} used a gentle method to {tool.method}.")
    problem_ent.meters["spin"] = 0
    problem_ent.meters["blocked"] = 0
    hero.memes["relief"] = 1
    crowd.memes["calm"] = 1
    world.say(f"The cent stopped revolving at last, and the path opened again.")
    world.say(f"The children smiled, and the crowd's grumble turned into a hum of thanks.")

    world.para()
    world.say(f"Then {params.name} set the cent safely in a small coin box so it would not skitter away again.")
    world.say(f"The crowd apologized for its sharp words, and {params.name} answered with a kind nod.")
    world.say(f"By sunset, the promenade was peaceful, and everyone remembered that {MORALS[0].lower()}")

    world.facts.update(resolved=True, tool=tool, place=setting.place)
    return world


def generate(params: StoryParams) -> StorySample:
    world = tell(params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_qa(world),
        world=world,
    )


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    problem = f["problem"]
    return [
        "Write a short fable set on a seaside promenade about a monger who solves a spinning cent problem.",
        f"Tell a gentle story where {hero.id} notices a {problem.label} {problem.pronoun('subject') if hasattr(problem, 'pronoun') else 'it'} revolving near the walk.",
        "Make the ending teach that patience and kindness are valuable when a small problem blocks the way.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero: Entity = f["hero"]
    tool: Tool = f["tool"]
    problem: Entity = f["problem"]
    return [
        QAItem(
            question="Who solved the trouble on the seaside promenade?",
            answer=f"{hero.id}, the careful monger, solved it with a soft and patient method.",
        ),
        QAItem(
            question="What was the cent doing before the monger helped?",
            answer=f"It was revolving again and again near the path, which made the promenade harder to pass.",
        ),
        QAItem(
            question="What tool did the monger use to solve the problem?",
            answer=f"{hero.id} used {tool.phrase} to stop the cent from revolving and to carry it safely away.",
        ),
        QAItem(
            question="Why did the crowd stop grumbling?",
            answer="They calmed down because the problem was solved without a fuss and the path opened again.",
        ),
        QAItem(
            question="What lesson did the story end with?",
            answer=f"It ended with the moral that {MORALS[0].lower()}",
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a cent?",
            answer="A cent is a small coin, the kind of coin people may drop and later pick up again.",
        ),
        QAItem(
            question="What does revolve mean?",
            answer="To revolve means to turn around in circles again and again.",
        ),
        QAItem(
            question="What is a promenade?",
            answer="A promenade is a pleasant place to walk, often near the sea.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== Story questions =="]
    for q in sample.story_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    lines.append("")
    lines.append("== World knowledge questions ==")
    for q in sample.world_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    lines.append("")
    lines.append("== Prompts ==")
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    return "\n".join(lines)


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
        lines.append(f"  {e.id:10} ({e.type:9}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(n for n, *_ in world.fired)}")
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


def valid_story_combos() -> list[tuple]:
    return [("promenade", "cent")]


def asp_verify() -> int:
    import asp

    clingo_set = set(asp_valid_fixes())
    python_set = set(valid_combos())
    if clingo_set == python_set:
        print(f"OK: clingo gate matches valid_combos() ({len(clingo_set)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    if clingo_set - python_set:
        print("  only in clingo:", sorted(clingo_set - python_set))
    if python_set - clingo_set:
        print("  only in python:", sorted(python_set - clingo_set))
    return 1


def asp_valid_fixes() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("#show valid_fix/2."))
    return sorted(set(asp.atoms(model, "valid_fix")))


CURATED = [
    StoryParams(place="promenade", problem="cent", name="Mina", trait="careful"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid_fix/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        fixes = asp_valid_fixes()
        print(f"{len(fixes)} valid fixes:\n")
        for place, problem in fixes:
            print(f"  {place:10} {problem}")
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

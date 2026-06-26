#!/usr/bin/env python3
"""
storyworlds/worlds/proton_colossal_graduate_foreshadowing_moral_value_problem.py
================================================================================

A compact comedy storyworld about a graduate, a proton, and a colossal mix-up.

Seed image:
- A graduate is working in a campus lab.
- A tiny proton is important because it powers a playful device.
- A colossal machine gets stuck, and the graduate must solve the problem.
- Early clues foreshadow the trouble.
- A moral choice matters: tell the truth, ask for help, and fix the mess together.

The world is intentionally small and constraint-checked:
- If the proton is not relevant, no story is generated.
- If the problem cannot be solved with the available tools, the story is rejected.
- The story always resolves with a clear comedic ending image.

Style:
- Child-facing, concrete, and funny.
- Problem-solving is the engine of the plot.
- Foreshadowing appears as early clues.
- Moral value appears as a choice about honesty and helping others.
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
# Entity model
# ---------------------------------------------------------------------------
@dataclass
class Entity:
    id: str
    kind: str = "thing"  # character | thing | place
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    carried_by: Optional[str] = None
    active: bool = False
    colossal: bool = False
    broken: bool = False
    helpful: bool = False
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        female = {"woman", "girl", "mother", "mom", "professor"}
        male = {"man", "boy", "father", "dad", "graduate"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class StoryParams:
    name: str
    mentor: str
    setting: str
    seed: Optional[int] = None


@dataclass
class Place:
    id: str
    label: str
    features: set[str] = field(default_factory=set)


@dataclass
class Tool:
    id: str
    label: str
    phrase: str
    solves: set[str] = field(default_factory=set)


@dataclass
class Problem:
    id: str
    label: str
    clue: str
    consequence: str
    solved_by: set[str] = field(default_factory=set)


class World:
    def __init__(self, place: Place) -> None:
        self.place = place
        self.entities: dict[str, Entity] = {}
        self.facts: dict[str, object] = {}
        self.paragraphs: list[list[str]] = [[]]

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

    def characters(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.kind == "character"]


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------
PLACES = {
    "lab": Place("lab", "the campus lab", {"glass", "buttons", "beeps"}),
    "workshop": Place("workshop", "the makerspace workshop", {"tools", "rolls", "beeps"}),
    "stage": Place("stage", "the school stage", {"curtains", "lights", "beeps"}),
}

TOOLS = {
    "magnifier": Tool("magnifier", "a magnifying glass", "look closely at tiny clues", {"find"}),
    "wrench": Tool("wrench", "a small wrench", "loosen a stuck bolt", {"unstick"}),
    "gloves": Tool("gloves", "rubber gloves", "handle the proton safely", {"handle"}),
    "chalk": Tool("chalk", "chalk marks", "show a plan on the board", {"plan"}),
    "ramp": Tool("ramp", "a cardboard ramp", "guide the colossal cart", {"move"}),
}

PROBLEMS = {
    "stuck_cart": Problem(
        "stuck_cart",
        "a colossal cart stuck in the doorway",
        clue="the cart wheels made a squeaky, grumpy sound before they stopped",
        consequence="the doorway was blocked by a giant, wobbling pile of cardboard boxes",
        solved_by={"wrench", "ramp", "help"},
    ),
    "mixed_labels": Problem(
        "mixed_labels",
        "the proton labels got mixed up",
        clue="one label had a coffee stain shaped like a tiny cloud",
        consequence="everyone pointed at the wrong jar and laughed too hard to think",
        solved_by={"magnifier", "chalk", "honesty"},
    ),
    "tiny_leak": Problem(
        "tiny_leak",
        "a tiny proton bottle had a tiny leak",
        clue="a little beep-bloop sound came from the shelf before anyone noticed",
        consequence="the experiment table started to wobble like jelly",
        solved_by={"gloves", "magnifier", "honesty"},
    ),
}

MORAL_VALUES = {
    "honesty": "tell the truth right away",
    "help": "ask for help instead of pretending to know everything",
    "kindness": "share the work so nobody gets stuck alone",
}

GAGS = [
    "the machine sneezed a puff of confetti",
    "the clipboard slid off the table like it had important news",
    "the lab coat sleeves flapped like tiny parachutes",
    "the proton label looked far too serious for something so small",
]

GRADUATE_NAMES = [
    "Mina", "Toby", "Rosa", "Eli", "June", "Noah", "Mara", "Theo"
]

MENTORS = [
    "Professor Bean", "Dr. Lark", "Coach Noodle", "Professor Puff"
]

SETTINGS = ["lab", "workshop", "stage"]


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
% A problem is solvable when the required tool or value is present.
solvable(P) :- problem(P), needs(P, T), has(T).
solvable(P) :- problem(P), needs_value(P, V), has_value(V).

% A complete story requires the proton, a graduate, a colossal obstacle, and a fix.
complete(S) :- setting(S), graduate(g), proton(p), colossal(c), problem(S), solvable(S).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid, place in PLACES.items():
        lines.append(asp.fact("setting", sid))
        for feat in sorted(place.features):
            lines.append(asp.fact("feature", sid, feat))
    for tid, tool in TOOLS.items():
        lines.append(asp.fact("tool", tid))
        for s in sorted(tool.solves):
            lines.append(asp.fact("solves", tid, s))
    for pid, pr in PROBLEMS.items():
        lines.append(asp.fact("problem", pid))
        for s in sorted(pr.solved_by):
            if s in TOOLS:
                lines.append(asp.fact("needs", pid, s))
            else:
                lines.append(asp.fact("needs_value", pid, s))
    lines.append(asp.fact("graduate", "g"))
    lines.append(asp.fact("proton", "p"))
    lines.append(asp.fact("colossal", "c"))
    for v in MORAL_VALUES:
        lines.append(asp.fact("value", v))
    for t in TOOLS:
        lines.append(asp.fact("has", t))
    for v in MORAL_VALUES:
        lines.append(asp.fact("has_value", v))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show solvable/1."))
    asp_set = set(asp.atoms(model, "solvable"))
    py_set = set((pid,) for pid, pr in PROBLEMS.items() if reason_ok(pr)[0])
    if asp_set == py_set:
        print(f"OK: clingo gate matches Python gate ({len(asp_set)} problems).")
        return 0
    print("MISMATCH between clingo and Python gates:")
    print("  only in clingo:", sorted(asp_set - py_set))
    print("  only in python:", sorted(py_set - asp_set))
    return 1


# ---------------------------------------------------------------------------
# Reasonableness gate
# ---------------------------------------------------------------------------
def reason_ok(problem: Problem) -> tuple[bool, str]:
    if problem.id == "mixed_labels":
        return True, "labels can be fixed with careful reading and honesty"
    if problem.id == "stuck_cart":
        return True, "a ramp or wrench can move the colossal cart"
    if problem.id == "tiny_leak":
        return True, "gloves and honesty make the leak safe to fix"
    return False, "no sensible fix"


# ---------------------------------------------------------------------------
# Story engine
# ---------------------------------------------------------------------------
def choose_problem(rng: random.Random) -> Problem:
    probs = list(PROBLEMS.values())
    rng.shuffle(probs)
    for p in probs:
        ok, _ = reason_ok(p)
        if ok:
            return p
    raise StoryError("No valid problem can be told from these options.")


def build_world(params: StoryParams) -> World:
    place = PLACES[params.setting]
    world = World(place)

    grad = world.add(Entity(
        id="graduate",
        kind="character",
        type="graduate",
        label=params.name,
        phrase=f"a graduate named {params.name}",
    ))
    mentor = world.add(Entity(
        id="mentor",
        kind="character",
        type="professor",
        label=params.mentor,
        phrase=params.mentor,
        helpful=True,
    ))
    proton = world.add(Entity(
        id="proton",
        kind="thing",
        type="proton",
        label="proton",
        phrase="a tiny proton in a clear tube",
        active=True,
    ))
    colossal = world.add(Entity(
        id="colossal",
        kind="thing",
        type="machine",
        label="colossal cart",
        phrase="a colossal cart with squeaky wheels",
        colossal=True,
        broken=True,
    ))

    world.facts.update(
        graduate=grad,
        mentor=mentor,
        proton=proton,
        colossal=colossal,
        place=place,
    )
    return world


def narrate_setup(world: World, problem: Problem) -> None:
    g = world.get("graduate")
    m = world.get("mentor")
    p = world.get("proton")
    c = world.get("colossal")

    world.say(
        f"{g.label} was a graduate in {world.place.label}, "
        f"trying to finish one very serious-looking experiment."
    )
    world.say(
        f"On the desk sat {p.phrase}, and beside it loomed {c.phrase}."
    )
    world.say(
        f"{m.label} had warned, 'If the tiny proton wanders, the colossal thing may wobble.'"
    )
    world.say(
        f"That warning felt funny later, because it was exactly the kind of line that should have made everyone nervous."
    )
    world.say(problem.clue)
    world.say(random.choice(GAGS))


def solve_problem(world: World, problem: Problem) -> None:
    g = world.get("graduate")
    m = world.get("mentor")
    p = world.get("proton")
    c = world.get("colossal")

    if problem.id == "mixed_labels":
        world.para()
        world.say(
            f"{g.label} admitted the labels were mixed up, which was honest and a little embarrassing."
        )
        world.say(
            f"{m.label} did not laugh for long; {m.label.lower()} handed over {TOOLS['magnifier'].label} and pointed at the stain."
        )
        world.say(
            f"Together they looked closely, sorted the jars, and gave the proton its proper label again."
        )
        world.say(
            f"The joke was that the smallest thing in the room had caused the biggest confusion."
        )
        world.say(
            f"After that, the proton sat still, the colossal cart stayed calm, and everyone breathed like they'd just finished a race in socks."
        )
        world.facts["moral"] = "honesty"
        world.facts["tool"] = "magnifier"
        return

    if problem.id == "stuck_cart":
        world.para()
        world.say(
            f"{g.label} saw the doorway jammed shut by the colossal cart and did not pretend it was fine."
        )
        world.say(
            f"{g.label} called {m.label} for help, because asking for help is often the fastest way to look smart."
        )
        world.say(
            f"They used {TOOLS['ramp'].label} to guide the cart away from the door and a small wrench to loosen one stubborn bolt."
        )
        world.say(
            f"The cart rolled free with a squeak so dramatic it sounded proud of itself."
        )
        world.say(
            f"Then the proton was safe again, and the doorway was open enough for even the most serious scientist to do a silly little sidestep through."
        )
        world.facts["moral"] = "help"
        world.facts["tool"] = "ramp"
        return

    if problem.id == "tiny_leak":
        world.para()
        world.say(
            f"{g.label} noticed the tiny beep-bloop and told the truth right away."
        )
        world.say(
            f"That honest sentence saved the day, because {m.label} could help before the proton bottle made a bigger mess."
        )
        world.say(
            f"They put on {TOOLS['gloves'].label}, checked the shelf with {TOOLS['magnifier'].label}, and fixed the leak before the table could wobble any more."
        )
        world.say(
            f"The proton stayed safe, the colossal machine stopped shivering, and the whole lab looked relieved and slightly offended that a drip had made them hurry."
        )
        world.facts["moral"] = "honesty"
        world.facts["tool"] = "gloves"
        return


def ending(world: World, problem: Problem) -> None:
    g = world.get("graduate")
    m = world.get("mentor")
    p = world.get("proton")
    c = world.get("colossal")

    world.para()
    if problem.id == "mixed_labels":
        world.say(
            f"In the end, {g.label} taped the right label onto the proton jar, and the wrong jar became a funny joke for later."
        )
    elif problem.id == "stuck_cart":
        world.say(
            f"In the end, the colossal cart was no longer colossal trouble; it was just a cart that had learned manners in a doorway."
        )
    else:
        world.say(
            f"In the end, the proton bottle stopped beeping, and the whole room felt as calm as a lunch break."
        )
    world.say(
        f"{m.label} smiled, {g.label} grinned, and the tiny proton sat neatly beside the colossal machine like the smallest hero in the room."
    )
    world.say(
        f"It was a funny sort of victory: one honest graduate, one helpful mentor, one tiny proton, and one ridiculous colossal problem, all finally in the right place."
    )


def generate_story(params: StoryParams) -> StorySample:
    if params.setting not in PLACES:
        raise StoryError("Unknown setting.")
    world = build_world(params)
    problem = choose_problem(random.Random(params.seed or 0))
    narrate_setup(world, problem)
    solve_problem(world, problem)
    ending(world, problem)

    story = world.render()
    prompts = [
        f"Write a short comedy about a graduate, a proton, and a colossal problem in {world.place.label}.",
        f"Tell a funny story where {params.name} notices a clue, tells the truth, and fixes the problem with help.",
        f"Write a child-friendly story that uses the words proton, colossal, and graduate, and ends with a cheerful solution.",
    ]

    grad = world.get("graduate")
    mentor = world.get("mentor")
    tool_id = world.facts.get("tool", "magnifier")
    moral = world.facts.get("moral", "honesty")
    problem_name = problem.label

    story_qa = [
        QAItem(
            question=f"Who was the story about in {world.place.label}?",
            answer=f"It was about {grad.label}, a graduate working in {world.place.label} with help from {mentor.label}.",
        ),
        QAItem(
            question=f"What clue warned that something was about to go wrong?",
            answer=f"The clue was: {problem.clue}. That foreshadowed the problem before it got bigger.",
        ),
        QAItem(
            question=f"What was the big problem in the story?",
            answer=f"The big problem was {problem_name}. It made the lab or workshop look much more dramatic than it really was.",
        ),
        QAItem(
            question=f"How did {grad.label} solve the problem?",
            answer=(
                f"{grad.label} solved it by choosing {MORAL_VALUES[moral]}, using {TOOLS[tool_id].phrase}, "
                f"and working with {mentor.label} until the colossal trouble was fixed."
            ),
        ),
    ]

    world_qa = [
        QAItem(
            question="What is a proton?",
            answer="A proton is a tiny part of an atom. It is so small that you cannot see it with your eyes.",
        ),
        QAItem(
            question="What does colossal mean?",
            answer="Colossal means very, very big. A colossal thing can feel huge enough to fill a room.",
        ),
        QAItem(
            question="What is a graduate?",
            answer="A graduate is a person who has finished a course of study, like college or a special school program.",
        ),
        QAItem(
            question="Why is honesty a good moral value?",
            answer="Honesty helps people trust each other, notice problems early, and fix mistakes before they get worse.",
        ),
    ]

    return StorySample(
        params=params,
        story=story,
        prompts=prompts,
        story_qa=story_qa,
        world_qa=world_qa,
        world=world,
    )


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Comedy storyworld: a graduate, a proton, and a colossal problem.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--name")
    ap.add_argument("--mentor", choices=MENTORS)
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
    setting = args.setting or rng.choice(SETTINGS)
    name = args.name or rng.choice(GRADUATE_NAMES)
    mentor = args.mentor or rng.choice(MENTORS)
    return StoryParams(name=name, mentor=mentor, setting=setting)


def generation_prompts(sample: StorySample) -> list[str]:
    return list(sample.prompts)


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


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        bits = []
        if e.kind:
            bits.append(f"kind={e.kind}")
        if e.type:
            bits.append(f"type={e.type}")
        if e.phrase:
            bits.append(f"phrase={e.phrase!r}")
        if e.colossal:
            bits.append("colossal=True")
        if e.active:
            bits.append("active=True")
        if e.broken:
            bits.append("broken=True")
        if e.helpful:
            bits.append("helpful=True")
        lines.append(f"  {e.id:10} {' '.join(bits)}")
    lines.append(f"  place: {world.place.label}")
    lines.append(f"  facts: {world.facts}")
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
    StoryParams(name="Mina", mentor="Professor Bean", setting="lab"),
    StoryParams(name="Toby", mentor="Dr. Lark", setting="workshop"),
    StoryParams(name="Rosa", mentor="Coach Noodle", setting="stage"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show solvable/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        model = asp.one_model(asp_program("#show solvable/1."))
        sols = sorted(set(asp.atoms(model, "solvable")))
        print(f"{len(sols)} solvable problems:")
        for (pid,) in sols:
            print(f"  {pid}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)

    samples: list[StorySample] = []
    if args.all:
        for p in CURATED:
            samples.append(generate_story(p))
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 20):
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            sample = generate_story(params)
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

    for idx, sample in enumerate(samples):
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.name}: {p.setting}"
        elif len(samples) > 1:
            header = f"### variant {idx + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if idx < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()

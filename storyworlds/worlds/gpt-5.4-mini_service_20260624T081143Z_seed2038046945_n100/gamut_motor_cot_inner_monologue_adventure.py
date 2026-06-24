#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260624T081143Z_seed2038046945_n100/gamut_motor_cot_inner_monologue_adventure.py
=============================================================================================================

A small adventure storyworld built from the seed words:
gamut, motor, cot.

Premise:
- A curious child wants to make a toy motor work.
- The toy can only safely run through a gamut of tests and places if the child
  checks a few adventure-like conditions first.
- Inner monologue is a first-class feature: the child thinks through the plan,
  worries, and chooses a clever next step.
- The story keeps a gentle adventure tone: a tiny quest, a narrow danger, a
  turn, and a satisfying ending image.

The world is intentionally small and constraint-driven:
- the motor may be noisy, stuck, or out of battery;
- the cot can be safe, snug, or serve as the launch point for a toy expedition;
- the gamut is a bundle of little checks / choices the child considers;
- the story resolves by matching the right fix to the right problem.
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

THRESHOLD = 1.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"  # "character" | "thing"
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
        for k in ("noise", "stuck", "battery", "safe", "curiosity", "worry", "bravery", "joy"):
            self.meters.setdefault(k, 0.0)
            self.memes.setdefault(k, 0.0)

    def pronoun(self, case: str = "subject") -> str:
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str = "the little room"
    indoors: bool = True
    affords: set[str] = field(default_factory=set)


@dataclass
class Tool:
    id: str
    label: str
    phrase: str
    fix: str
    check: str
    requires: set[str] = field(default_factory=set)
    helps: set[str] = field(default_factory=set)


@dataclass
class Challenge:
    id: str
    label: str
    danger: str
    cause: str
    line: str
    tags: set[str] = field(default_factory=set)


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
        self.facts: dict = {}
        self.route: list[str] = []

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


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------

SETTINGS = {
    "room": Setting(place="the little room", indoors=True, affords={"cot", "motor", "gamut"}),
    "hall": Setting(place="the hallway", indoors=True, affords={"motor", "gamut"}),
    "garden": Setting(place="the garden path", indoors=False, affords={"gamut"}),
}

CHALLENGES = {
    "stuck": Challenge(
        id="stuck",
        label="a stuck toy motor",
        danger="stopped",
        cause="dust in the gears",
        line="The motor would not turn because dust had jammed the tiny gears.",
        tags={"motor", "mechanical"},
    ),
    "noise": Challenge(
        id="noise",
        label="a noisy toy motor",
        danger="loud",
        cause="a loose cap",
        line="The motor rattled loudly and sounded more like a drum than a helper.",
        tags={"motor", "sound"},
    ),
    "sleepy": Challenge(
        id="sleepy",
        label="a sleepy motor",
        danger="weak",
        cause="a tired battery",
        line="The motor blinked and slowed because its battery was nearly empty.",
        tags={"motor", "battery"},
    ),
}

TOOLS = {
    "cloth": Tool(
        id="cloth",
        label="a soft cloth",
        phrase="a soft cloth for wiping",
        fix="wipe the dust away",
        check="wiped clean",
        requires={"stuck"},
        helps={"stuck"},
    ),
    "cap": Tool(
        id="cap",
        label="a snug cap",
        phrase="a snug cap for the top",
        fix="press the loose cap back on",
        check="held tight",
        requires={"noise"},
        helps={"noise"},
    ),
    "battery": Tool(
        id="battery",
        label="a fresh battery",
        phrase="a fresh battery from the drawer",
        fix="swap in a fresh battery",
        check="buzzing brightly",
        requires={"sleepy"},
        helps={"sleepy"},
    ),
    "blanket": Tool(
        id="blanket",
        label="a small blanket",
        phrase="a small blanket for the cot",
        fix="make the cot feel safe and snug",
        check="quiet and snug",
        requires={"sleepy", "noise", "stuck"},
        helps={"safe"},
    ),
}

GAMUT_STEPS = [
    "look closely",
    "listen for the rattle",
    "touch the top gently",
    "check the battery door",
    "test the wheels on the floor",
]

GAMUT_PATHS = {
    "cot": ["look closely", "touch the top gently"],
    "motor": ["listen for the rattle", "check the battery door", "test the wheels on the floor"],
    "gamut": GAMUT_STEPS,
}

NAMES = ["Nia", "Leo", "Mina", "Owen", "Ari", "Ivy", "Finn", "June"]
TRAITS = ["curious", "brave", "careful", "bright-eyed", "patient"]


# ---------------------------------------------------------------------------
# Story params
# ---------------------------------------------------------------------------

@dataclass
class StoryParams:
    setting: str
    challenge: str
    tool: str
    name: str
    trait: str
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------

ASP_RULES = r"""
% A challenge is solvable when the chosen tool helps it.
solvable(C, T) :- challenge(C), tool(T), helps(T, C).

% The gamut is complete when the child can consider the steps tied to the chosen challenge.
step_needed(C, S) :- challenge(C), path(C, S).
complete(C) :- challenge(C), solvable(C, T), step_needed(C, _), tool(T).

#show solvable/2.
#show complete/1.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for cid, ch in CHALLENGES.items():
        lines.append(asp.fact("challenge", cid))
        for t in sorted(ch.tags):
            lines.append(asp.fact("tagged", cid, t))
    for tid, tool in TOOLS.items():
        lines.append(asp.fact("tool", tid))
        for c in sorted(tool.helps):
            lines.append(asp.fact("helps", tid, c))
    for cid, steps in GAMUT_PATHS.items():
        for s in steps:
            lines.append(asp.fact("path", cid, s))
    return "\n".join(lines)


def asp_program() -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n"


# ---------------------------------------------------------------------------
# Core simulation
# ---------------------------------------------------------------------------

def maybe_reason(world: World, child: Entity, challenge: Challenge) -> None:
    child.memes["curiosity"] += 1
    world.say(
        f"{child.label} stared at the {challenge.label} and thought, "
        f"Maybe this was a tiny adventure, and the right clue would come if I looked carefully."
    )


def introduce(world: World, child: Entity, challenge: Challenge, tool: Tool) -> None:
    world.say(
        f"{child.label} was a {world.facts['trait']} child who loved the hush before a brave idea."
    )
    world.say(
        f"One day, {child.label} found {challenge.label} beside {tool.phrase} and felt a spark of wonder."
    )


def check_gamut(world: World, child: Entity, challenge: Challenge) -> None:
    steps = GAMUT_PATHS["gamut"] if "gamut" in world.setting.affords else GAMUT_PATHS[challenge.id]
    world.route = list(steps)
    world.say(
        f"{child.label} began to trace a little gamut of checks: "
        + ", ".join(steps[:-1])
        + f", and {steps[-1]}."
    )


def problem(world: World, child: Entity, challenge: Challenge) -> None:
    if challenge.id == "stuck":
        world.say(challenge.line)
        child.memes["worry"] += 1
    elif challenge.id == "noise":
        world.say(challenge.line)
        child.memes["worry"] += 1
    else:
        world.say(challenge.line)
        child.memes["worry"] += 1


def choose_fix(world: World, child: Entity, challenge: Challenge, tool: Tool) -> None:
    child.memes["bravery"] += 1
    world.say(
        f"Inside, {child.label} thought, If I use {tool.label}, I can {tool.fix}."
    )
    if challenge.id not in tool.helps:
        raise StoryError(f"The tool {tool.id} does not solve the challenge {challenge.id}.")


def resolve(world: World, child: Entity, challenge: Challenge, tool: Tool) -> None:
    child.memes["joy"] += 1
    if tool.id == "cloth":
        world.say(
            f"{child.label} used {tool.label} to {tool.fix}. Soon the motor was {tool.check}, "
            f"and the little machine hummed like a friendly bee."
        )
    elif tool.id == "cap":
        world.say(
            f"{child.label} used {tool.label} to {tool.fix}. Soon the motor was {tool.check}, "
            f"and its rattle turned into a neat, steady whirr."
        )
    elif tool.id == "battery":
        world.say(
            f"{child.label} used {tool.label} to {tool.fix}. Soon the motor was {tool.check}, "
            f"and it spun with bright, new energy."
        )
    else:
        world.say(
            f"{child.label} used {tool.label} to make the cot feel safe and snug. "
            f"The little adventure ended with the motor quiet and the room warm and still."
        )


def tell(setting: Setting, challenge: Challenge, tool: Tool, name: str, trait: str) -> World:
    world = World(setting)
    child = world.add(Entity(id=name, kind="character", type="child", label=name))
    motor = world.add(Entity(id="motor", type="motor", label="toy motor", phrase="toy motor"))
    cot = world.add(Entity(id="cot", type="cot", label="cot", phrase="small cot"))
    world.facts.update(child=child, motor=motor, cot=cot, challenge=challenge, tool=tool, trait=trait)

    introduce(world, child, challenge, tool)
    world.para()
    maybe_reason(world, child, challenge)
    check_gamut(world, child, challenge)
    problem(world, child, challenge)
    choose_fix(world, child, challenge, tool)
    world.para()
    resolve(world, child, challenge, tool)
    return world


# ---------------------------------------------------------------------------
# QA
# ---------------------------------------------------------------------------

def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a gentle adventure story with inner monologue that uses the words "gamut", "motor", and "cot".',
        f"Tell a child-sized quest where {f['child'].label} thinks carefully about a {f['challenge'].label} and finds the right fix.",
        f"Write a short story in an adventure style where a child checks a gamut of clues before helping a toy motor.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child, challenge, tool = f["child"], f["challenge"], f["tool"]
    return [
        QAItem(
            question=f"What was {child.label} trying to help in the story?",
            answer=f"{child.label} was trying to help the toy motor, which had {challenge.label}.",
        ),
        QAItem(
            question=f"What did {child.label} think before making a choice?",
            answer=f"{child.label} thought that if the right clue showed up, {tool.fix} would help.",
        ),
        QAItem(
            question="What was the gamut in this story?",
            answer="The gamut was a small set of checks and clues the child followed to solve the problem.",
        ),
        QAItem(
            question=f"How did the story end for the motor?",
            answer=f"The motor ended up {tool.check} and ready for a calm finish.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a motor?",
            answer="A motor is a machine that makes something move or spin when it gets power.",
        ),
        QAItem(
            question="What is a cot?",
            answer="A cot is a small bed for a child or a baby.",
        ),
        QAItem(
            question="What does gamut mean?",
            answer="A gamut means a whole range or set of different things to check or consider.",
        ),
    ]


# ---------------------------------------------------------------------------
# ASP helpers
# ---------------------------------------------------------------------------

def asp_valid() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program())
    return sorted(set(asp.atoms(model, "solvable"))), sorted(set(asp.atoms(model, "complete")))


def asp_verify() -> int:
    if len(TOOLS) != 4 or len(CHALLENGES) != 3:
        raise StoryError("Registry size changed unexpectedly.")
    solvable = {(c, t) for c in CHALLENGES for t in TOOLS if c in TOOLS[t].helps}
    asp_solvable, asp_complete = asp_valid()
    asp_solvable_set = set(asp_solvable)
    if asp_solvable_set != solvable:
        print("MISMATCH between ASP and Python solvable pairs")
        print("only in ASP:", sorted(asp_solvable_set - solvable))
        print("only in Python:", sorted(solvable - asp_solvable_set))
        return 1
    if not asp_complete:
        print("MISMATCH: expected at least one complete() atom")
        return 1
    print(f"OK: ASP matches Python for {len(solvable)} solvable pairs.")
    return 0


def show_asp() -> str:
    return asp_program()


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A tiny adventure storyworld with inner monologue.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--challenge", choices=CHALLENGES)
    ap.add_argument("--tool", choices=TOOLS)
    ap.add_argument("--name")
    ap.add_argument("--trait", choices=["curious", "brave", "careful", "bright-eyed", "patient"])
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
    setting = args.setting or rng.choice(list(SETTINGS))
    challenge = args.challenge or rng.choice(list(CHALLENGES))
    tool = args.tool or rng.choice([t for t in TOOLS if challenge in TOOLS[t].helps])
    if challenge not in TOOLS[tool].helps:
        raise StoryError("Chosen tool does not solve the chosen challenge.")
    name = args.name or rng.choice(NAMES)
    trait = args.trait or rng.choice(TRAITS)
    return StoryParams(setting=setting, challenge=challenge, tool=tool, name=name, trait=trait)


def generate(params: StoryParams) -> StorySample:
    world = tell(
        SETTINGS[params.setting],
        CHALLENGES[params.challenge],
        TOOLS[params.tool],
        params.name,
        params.trait,
    )
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        lines.append(
            f"  {e.id:8} ({e.type:8}) "
            f"meters={{{', '.join(f'{k}: {v}' for k, v in e.meters.items() if v)}}} "
            f"memes={{{', '.join(f'{k}: {v}' for k, v in e.memes.items() if v)}}}"
        )
    lines.append(f"  route: {world.route}")
    return "\n".join(lines)


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
    StoryParams(setting="room", challenge="stuck", tool="cloth", name="Nia", trait="curious"),
    StoryParams(setting="room", challenge="noise", tool="cap", name="Leo", trait="careful"),
    StoryParams(setting="room", challenge="sleepy", tool="battery", name="Mina", trait="brave"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(show_asp())
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp

        model = asp.one_model(asp_program())
        print("solvable:", sorted(set(asp.atoms(model, "solvable"))))
        print("complete:", sorted(set(asp.atoms(model, "complete"))))
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
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.name}: {p.challenge} with {p.tool} in {p.setting}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()

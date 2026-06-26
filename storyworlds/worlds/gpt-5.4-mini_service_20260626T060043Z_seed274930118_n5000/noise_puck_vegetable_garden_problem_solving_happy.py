#!/usr/bin/env python3
"""
storyworlds/worlds/noise_puck_vegetable_garden_problem_solving_happy.py
========================================================================

A small pirate-tale storyworld set in a vegetable garden.

Premise:
- A curious young pirate visits a vegetable garden.
- A puck-shaped gate marker makes a loud noise when bumped.
- The noise startles tender seedlings and threatens the garden's peace.
- The pirate and a garden helper solve the problem by finding the source of the noise and padding the puck so it can be moved safely.

The world is intentionally small and state-driven:
- Entities carry physical meters and emotional memes.
- The plot turns on curiosity, noise, a problem to solve, and a happy ending.
- The story should feel authored, concrete, and complete rather than like an event log.
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


THRESHOLD = 1.0


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
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "woman", "mother"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man", "father"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def name_or_label(self) -> str:
        return self.id if self.kind == "character" else self.label or self.id


@dataclass
class Setting:
    place: str = "the vegetable garden"
    affords: set[str] = field(default_factory=set)


@dataclass
class Activity:
    id: str
    verb: str
    gerund: str
    rush: str
    noise: str
    mess: str
    keyword: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Problem:
    id: str
    label: str
    source: str
    risk: str
    fix: str
    cover: str
    guards: set[str]


@dataclass
class Solution:
    id: str
    label: str
    action: str
    result: str
    protects: set[str]


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
        self.facts: dict = {}
        self.noise_loud: bool = False
        self.problem_source: str = ""

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
        clone.noise_loud = self.noise_loud
        clone.problem_source = self.problem_source
        return clone


SETTINGS = {
    "vegetable_garden": Setting(place="the vegetable garden", affords={"investigate", "move_puck", "pad_puck"}),
}

ACTIVITIES = {
    "noise": Activity(
        id="noise",
        verb="investigate the noise",
        gerund="investigating the noise",
        rush="hurry toward the clatter",
        noise="a clatter and a clink",
        mess="startled",
        keyword="noise",
        tags={"noise", "curiosity"},
    ),
    "puck": Activity(
        id="puck",
        verb="move the puck",
        gerund="moving the puck",
        rush="push the puck along",
        noise="a hard clack",
        mess="bumped",
        keyword="puck",
        tags={"puck", "noise"},
    ),
}

PROBLEMS = {
    "puck_gate": Problem(
        id="puck_gate",
        label="a puck-shaped gate marker",
        source="the puck",
        risk="its clatter might startle the seedlings",
        fix="pad the puck with soft leaves",
        cover="soft leaves",
        guards={"noise"},
    ),
}

SOLUTIONS = {
    "leaves": Solution(
        id="leaves",
        label="a bundle of soft leaves",
        action="wrap the puck in soft leaves",
        result="the clatter turned into a small thump",
        protects={"noise"},
    ),
}

PIRATE_NAMES = ["Finn", "Mara", "Jory", "Tess", "Beck", "Nell", "Rory", "Ari"]
HELPER_NAMES = ["Old Root", "Moss", "Bean", "Penny", "Sprout"]


@dataclass
class StoryParams:
    setting: str
    activity: str
    name: str
    helper: str
    seed: Optional[int] = None


ASP_RULES = r"""
noise_problem(A) :- activity(A), causes_noise(A).
needs_fix(P) :- problem(P), caused_by(P, A), noise_problem(A).
can_fix(P, S) :- needs_fix(P), solution(S), protects(S, noise).
valid_story(S) :- setting(vegetable_garden), activity(noise), problem(puck_gate), can_fix(puck_gate, S).
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for sid, s in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        for a in sorted(s.affords):
            lines.append(asp.fact("affords", sid, a))
    for aid, a in ACTIVITIES.items():
        lines.append(asp.fact("activity", aid))
        if a.id == "noise":
            lines.append(asp.fact("causes_noise", aid))
    for pid, p in PROBLEMS.items():
        lines.append(asp.fact("problem", pid))
        lines.append(asp.fact("caused_by", pid, "noise"))
    for sid, s in SOLUTIONS.items():
        lines.append(asp.fact("solution", sid))
        for tag in sorted(s.protects):
            lines.append(asp.fact("protects", sid, tag))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_solutions() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("#show valid_story/1."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    py = {"leaves"}
    cl = {t[0] for t in asp_valid_solutions()}
    if py == cl:
        print("OK: ASP and Python agree on valid solutions.")
        return 0
    print("MISMATCH between ASP and Python:")
    print("  only in python:", sorted(py - cl))
    print("  only in clingo:", sorted(cl - py))
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Pirate tale in a vegetable garden with noise, puck, curiosity, problem solving, and a happy ending.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--activity", choices=ACTIVITIES)
    ap.add_argument("--name", choices=PIRATE_NAMES)
    ap.add_argument("--helper", choices=HELPER_NAMES)
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


def valid_combos() -> list[tuple[str, str]]:
    return [("vegetable_garden", "noise")]


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.activity and args.activity not in ACTIVITIES:
        raise StoryError("Unknown activity.")
    setting = args.setting or "vegetable_garden"
    activity = args.activity or "noise"
    if (setting, activity) not in valid_combos():
        raise StoryError("No valid combination matches the given options.")
    return StoryParams(
        setting=setting,
        activity=activity,
        name=args.name or rng.choice(PIRATE_NAMES),
        helper=args.helper or rng.choice(HELPER_NAMES),
    )


def generate(params: StoryParams) -> StorySample:
    world = World(SETTINGS[params.setting])

    pirate = world.add(Entity(id=params.name, kind="character", type="boy", memes={"curiosity": 1.0, "joy": 0.0}))
    helper = world.add(Entity(id=params.helper, kind="character", type="woman", memes={"calm": 1.0}))
    puck = world.add(Entity(id="puck", type="thing", label="puck", phrase="a puck-shaped gate marker"))
    leaves = world.add(Entity(id="leaves", type="thing", label="soft leaves", phrase="a bundle of soft leaves"))

    act = ACTIVITIES[params.activity]
    prob = PROBLEMS["puck_gate"]
    sol = SOLUTIONS["leaves"]

    # Act 1
    world.say(f"{pirate.id} was a curious little pirate who loved to poke around {world.setting.place}.")
    world.say(f"One bright day, {pirate.id} heard {act.noise} near {prob.label}.")
    world.say(f"{pirate.id} grinned, because curiosity always made {pirate.pronoun('object')} walk a little closer.")
    world.para()

    # Act 2
    world.say(f"At the gate, {pirate.id} found the {puck.label}, and when {pirate.pronoun('subject')} nudged it, there was {act.noise}.")
    world.noise_loud = True
    pirate.memes["curiosity"] += 1.0
    pirate.memes["worry"] = 1.0
    helper.memes["concern"] = 1.0
    world.say(f"The noise made the little tomato plants shiver, and even the beans seemed to listen.")
    world.say(f"{params.helper} the gardener said, \"That puck is causing trouble. We need to solve this kindly.\"")
    world.para()

    # Act 3
    world.say(f"{pirate.id} and {params.helper} looked closely, then chose a gentle fix.")
    world.say(f"They used {sol.label} to {sol.action}.")
    world.say(f"After that, {sol.result}, and the garden grew quiet again.")
    world.say(f"{pirate.id} smiled a pirate smile, happy to have turned a noisy problem into a safe one.")
    world.say(f"{prob.label.capitalize()} could stay where it was, and the seedlings slept in peace.")

    pirate.memes["joy"] = 1.0
    pirate.memes["worry"] = 0.0
    helper.memes["joy"] = 1.0
    world.facts = {
        "pirate": pirate,
        "helper": helper,
        "puck": puck,
        "leaves": leaves,
        "problem": prob,
        "solution": sol,
        "activity": act,
    }

    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    pirate = f["pirate"]
    return [
        'Write a short pirate tale for a young child set in a vegetable garden, with a curious hero, a noisy puck, a problem to solve, and a happy ending.',
        f"Tell a gentle story about {pirate.id}, a curious pirate, who hears a noise in the vegetable garden and helps fix it.",
        "Write a child-friendly story that includes the words noise and puck, and ends with the garden becoming peaceful again.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    pirate = f["pirate"]
    helper = f["helper"]
    prob = f["problem"]
    act = f["activity"]
    sol = f["solution"]
    return [
        QAItem(
            question=f"Why did {pirate.id} go closer to the puck in the vegetable garden?",
            answer=f"{pirate.id} was curious, so the noise made {pirate.pronoun('object')} walk closer to see what was happening.",
        ),
        QAItem(
            question=f"What problem did the puck cause?",
            answer=f"The puck made a clatter that could startle the seedlings, so {prob.label} was a noisy problem that needed care.",
        ),
        QAItem(
            question=f"How did {pirate.id} and {helper.id} solve the problem?",
            answer=f"They used {sol.label} and wrapped the puck so the noise calmed down.",
        ),
        QAItem(
            question=f"How did the story end for the vegetable garden?",
            answer="The garden became quiet and peaceful again, and the pirate felt happy about helping.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a vegetable garden?",
            answer="A vegetable garden is a place where people grow vegetables like tomatoes, beans, and carrots.",
        ),
        QAItem(
            question="What is curiosity?",
            answer="Curiosity is the feeling that makes you want to look, ask, and learn about something new.",
        ),
        QAItem(
            question="What can a loud noise do?",
            answer="A loud noise can startle plants, people, or animals and make them jump or worry for a moment.",
        ),
        QAItem(
            question="What is a puck?",
            answer="A puck is a small, hard, round object that can slide or bump with a clack.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== (2) Story questions ==")
    for q in sample.story_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    lines.append("")
    lines.append("== (3) World-knowledge questions ==")
    for q in sample.world_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        bits = []
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        lines.append(f"  {e.id:10} ({e.type:7}) {' '.join(bits)}")
    lines.append(f"  loud_noise={world.noise_loud}")
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


def asp_facts_program() -> str:
    return asp_program("#show valid_story/1.")


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_facts_program())
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp

        model = asp.one_model(asp_facts_program())
        items = sorted(set(asp.atoms(model, "valid_story")))
        print(f"{len(items)} valid solutions:")
        for (sid,) in items:
            print(f"  {sid}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(StoryParams(setting="vegetable_garden", activity="noise", name=name, helper=helper, seed=base_seed))
                   for name in PIRATE_NAMES[:3] for helper in HELPER_NAMES[:1]]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 20, 20):
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

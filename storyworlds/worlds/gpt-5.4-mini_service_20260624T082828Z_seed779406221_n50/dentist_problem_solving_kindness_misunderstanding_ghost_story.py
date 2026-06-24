#!/usr/bin/env python3
"""
A small storyworld about a child, a dentist, a spooky misunderstanding, and a
kind problem-solving turn that makes the clinic feel safe again.
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
        if self.type in {"girl", "mother", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str = "the dentist's office"
    indoors: bool = True


@dataclass
class StoryParams:
    place: str
    hero_name: str
    hero_type: str
    parent_type: str
    dentist_name: str
    misunderstanding: str
    problem: str
    kindness: str
    seed: Optional[int] = None


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.fired: set[str] = set()

    def add(self, e: Entity) -> Entity:
        self.entities[e.id] = e
        return e

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
        w = World(self.setting)
        w.entities = copy.deepcopy(self.entities)
        w.paragraphs = [[]]
        w.facts = dict(self.facts)
        w.fired = set(self.fired)
        return w


MESSY = {"sticky", "ache", "fear"}
REASONS = {
    "shadow": "a shadow on the wall",
    "mask": "a mask and shiny light",
    "whisper": "a quiet whisper from the hallway",
}
PROBLEMS = {
    "toothache": "a sore tooth",
    "stuck_food": "a tiny piece of food stuck between the teeth",
    "lost_brush": "a missing toothbrush at home",
}
KINDNESSES = {
    "explain": "explained what would happen next in a gentle voice",
    "show_tools": "showed the tools one by one and let the child look first",
    "count_breaths": "counted slow breaths together until the chair felt calm",
}
GIRL_NAMES = ["Mia", "Lily", "Nora", "Ava", "Zoe"]
BOY_NAMES = ["Leo", "Finn", "Noah", "Eli", "Theo"]


def make_story_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    return StoryParams(
        place=args.place or "the dentist's office",
        hero_name=args.name or rng.choice(GIRL_NAMES + BOY_NAMES),
        hero_type=args.gender or rng.choice(["girl", "boy"]),
        parent_type=args.parent or rng.choice(["mother", "father"]),
        dentist_name=args.dentist or rng.choice(["Dr. Lane", "Dr. Reed", "Dr. Kim"]),
        misunderstanding=args.misunderstanding or rng.choice(list(REASONS)),
        problem=args.problem or rng.choice(list(PROBLEMS)),
        kindness=args.kindness or rng.choice(list(KINDNESSES)),
    )


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A ghost-story-flavored dentist storyworld.")
    ap.add_argument("--place", default=None)
    ap.add_argument("--name", default=None)
    ap.add_argument("--gender", choices=["girl", "boy"], default=None)
    ap.add_argument("--parent", choices=["mother", "father"], default=None)
    ap.add_argument("--dentist", default=None)
    ap.add_argument("--misunderstanding", choices=list(REASONS), default=None)
    ap.add_argument("--problem", choices=list(PROBLEMS), default=None)
    ap.add_argument("--kindness", choices=list(KINDNESSES), default=None)
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
    if args.problem and args.misunderstanding == "whisper" and args.problem == "lost_brush":
        pass
    return make_story_params(args, rng)


def reasonableness_gate(params: StoryParams) -> None:
    if params.misunderstanding not in REASONS:
        raise StoryError("unknown misunderstanding")
    if params.problem not in PROBLEMS:
        raise StoryError("unknown problem")
    if params.kindness not in KINDNESSES:
        raise StoryError("unknown kindness")


def tell(params: StoryParams) -> World:
    setting = Setting(place=params.place)
    world = World(setting)
    hero = world.add(Entity(id="hero", kind="character", type=params.hero_type, label=params.hero_name))
    parent = world.add(Entity(id="parent", kind="character", type=params.parent_type, label=params.parent_type))
    dentist = world.add(Entity(id="dentist", kind="character", type="adult", label=params.dentist_name))
    problem = world.add(Entity(id="problem", type="problem", label=PROBLEMS[params.problem]))
    ghost = world.add(Entity(id="ghost", type="ghost", label="a ghostly shape"))

    hero.memes["fear"] = 1
    world.say(f"{hero.label} came to {world.setting.place} with {parent.label} on a quiet day.")
    world.say(f"{hero.label} peeked at the door and thought {REASONS[params.misunderstanding]}.")
    world.say(f"That made {hero.label} feel like {ghost.label} might be waiting inside.")
    world.para()

    world.say(f"But the real problem was {problem.label}. {dentist.label} noticed right away.")
    dentist.memes["kindness"] = 1
    world.say(f"{dentist.label} {KINDNESSES[params.kindness]} so {hero.label} would know they were safe.")
    world.say(f"Then {dentist.label} used a small careful plan to fix the {problem.label}.")
    problem.meters["fixed"] = 1
    hero.memes["understanding"] = 1
    hero.memes["fear"] = 0
    world.para()

    world.say(
        f"{hero.label} learned that the spooky thing was only {REASONS[params.misunderstanding]}, "
        f"and the helpful part was {dentist.label}'s kindness. "
        f"By the end, {hero.label} could sit still, smile, and leave with a clean, safe mouth."
    )

    world.facts = {
        "hero": hero,
        "parent": parent,
        "dentist": dentist,
        "problem": problem,
        "misunderstanding": params.misunderstanding,
        "kindness": params.kindness,
        "problem_key": params.problem,
        "world": world,
    }
    return world


ASP_RULES = r"""
misunderstanding_shadow.
misunderstanding_mask.
misunderstanding_whisper.

problem_toothache.
problem_stuck_food.
problem_lost_brush.

kindness_explain.
kindness_show_tools.
kindness_count_breaths.

spooky(M) :- misunderstanding(M).
needs_help(P) :- problem(P).
solves(K, P) :- kindness(K), problem(P).

reasonable_story(M, P, K) :- spooky(M), needs_help(P), solves(K, P).
"""


def asp_facts() -> str:
    import asp
    lines = ["misunderstanding(shadow).", "misunderstanding(mask).", "misunderstanding(whisper)."]
    lines += ["problem(toothache).", "problem(stuck_food).", "problem(lost_brush)."]
    lines += ["kindness(explain).", "kindness(show_tools).", "kindness(count_breaths)."]
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def generate(params: StoryParams) -> StorySample:
    reasonableness_gate(params)
    world = tell(params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=[
            "Write a gentle ghost-story-style tale about a child who is scared of a dentist because of a misunderstanding.",
            f"Tell a short story where {params.hero_name} thinks {REASONS[params.misunderstanding]} means a ghost, but the dentist solves a real problem kindly.",
            "Write a child-friendly story with a spooky feeling that ends in comfort, understanding, and a fixed problem.",
        ],
        story_qa=story_qa(world),
        world_qa=world_qa(world),
        world=world,
    )


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero: Entity = f["hero"]
    dentist: Entity = f["dentist"]
    problem: Entity = f["problem"]
    mis = f["misunderstanding"]
    kind = f["kindness"]
    return [
        QAItem(
            question=f"Why did {hero.label} feel scared at first?",
            answer=f"{hero.label} felt scared because {REASONS[mis]} seemed like a ghost was nearby.",
        ),
        QAItem(
            question=f"What was the real problem the dentist noticed?",
            answer=f"The real problem was {problem.label}, and {dentist.label} saw it right away.",
        ),
        QAItem(
            question=f"How did {dentist.label} help {hero.label}?",
            answer=f"{dentist.label} {KINDNESSES[kind]} and then used a careful plan to fix the problem.",
        ),
        QAItem(
            question=f"What changed by the end of the story?",
            answer=f"{hero.label} understood the misunderstanding, felt braver, and left after the problem was fixed.",
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does a dentist do?",
            answer="A dentist helps keep teeth healthy, checks for problems, and fixes hurting or dirty teeth.",
        ),
        QAItem(
            question="Why can a misunderstanding feel spooky?",
            answer="A misunderstanding can feel spooky when someone thinks something harmless is a ghost or a threat.",
        ),
        QAItem(
            question="Why is kindness helpful when someone is scared?",
            answer="Kindness helps because gentle words and patient actions make fear smaller and make it easier to solve a problem.",
        ),
    ]


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for e in world.entities.values():
        bits = []
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        lines.append(f"{e.id}: {e.label or e.type} {' '.join(bits)}")
    return "\n".join(lines)


def format_qa(sample: StorySample) -> str:
    out = ["== Story questions =="]
    for q in sample.story_qa:
        out.append(f"Q: {q.question}")
        out.append(f"A: {q.answer}")
    out.append("")
    out.append("== World questions ==")
    for q in sample.world_qa:
        out.append(f"Q: {q.question}")
        out.append(f"A: {q.answer}")
    return "\n".join(out)


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world is not None:
        print(dump_trace(sample.world))
    if qa:
        print()
        print(format_qa(sample))


def valid_stories() -> list[tuple[str, str, str]]:
    return [(m, p, k) for m in REASONS for p in PROBLEMS for k in KINDNESSES]


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show reasonable_story/3."))
    asp_set = set(asp.atoms(model, "reasonable_story"))
    py_set = set(valid_stories())
    if asp_set == py_set:
        print(f"OK: ASP matches Python ({len(py_set)} stories).")
        return 0
    print("MISMATCH")
    print("only in ASP:", sorted(asp_set - py_set))
    print("only in Python:", sorted(py_set - asp_set))
    return 1


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show reasonable_story/3."))
        return
    if args.verify:
        sys.exit(asp_verify())

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        for i, (m, p, k) in enumerate(valid_stories()):
            params = StoryParams(
                place="the dentist's office",
                hero_name=GIRL_NAMES[i % len(GIRL_NAMES)],
                hero_type="girl" if i % 2 == 0 else "boy",
                parent_type="mother" if i % 2 == 0 else "father",
                dentist_name=["Dr. Lane", "Dr. Reed", "Dr. Kim"][i % 3],
                misunderstanding=m,
                problem=p,
                kindness=k,
                seed=base_seed + i,
            )
            samples.append(generate(params))
    else:
        for i in range(args.n):
            rng = random.Random(base_seed + i)
            params = resolve_params(args, rng)
            params.seed = base_seed + i
            samples.append(generate(params))

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

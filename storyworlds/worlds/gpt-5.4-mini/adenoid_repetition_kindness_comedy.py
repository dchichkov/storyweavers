#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/adenoid_repetition_kindness_comedy.py
======================================================================

A tiny, self-contained storyworld about a child with a noisy adenoid, a bit of
repetition, and a lot of kindness.

Premise
-------
A child keeps repeating themselves because their adenoid makes their nose feel
blocked and their voice comes out funny. A kind friend, parent, or teacher helps
them through a small comic problem: they need to say a line, get understood, and
finish the moment with a gentle laugh and a practical fix.

This world is built to read like a complete children's story:
- a setup with a comic repetition problem,
- a turn where kindness changes the social state,
- a warm ending image showing what improved.

It supports the standard storyworld CLI:
    -n, --all, --seed, --trace, --qa, --json, --asp, --verify, --show-asp

It also includes a Python reasonableness gate and an inline ASP twin, with
parity checks in --verify.

The word "adenoid" is included in the story text and in world knowledge QA.
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
GATE_MIN = 2

NAME_POOL = ["Mia", "Noah", "Luna", "Eli", "Ivy", "Owen", "Nina", "Finn", "Ava", "Theo"]


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    role: str = ""
    attrs: dict = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman", "teacher"}
        male = {"boy", "father", "dad", "man", "doctor"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return {"mother": "mom", "father": "dad", "teacher": "teacher"}.get(self.type, self.type)


@dataclass
class Setting:
    id: str
    place: str
    detail: str
    mood: str


@dataclass
class Problem:
    id: str
    label: str
    symptom: str
    repeat_line: str
    funny_effect: str
    needs_kindness: bool = True


@dataclass
class KindAction:
    id: str
    label: str
    text: str
    effect: str
    can_fix: bool = True


class World:
    def __init__(self) -> None:
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
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
        clone.paragraphs = [[]]
        clone.fired = set(self.fired)
        return clone


def _r_relief(world: World) -> list[str]:
    out: list[str] = []
    child = world.get("child")
    if child.meters["calmed"] >= THRESHOLD and child.meters["helped"] >= THRESHOLD:
        sig = ("relief",)
        if sig not in world.fired:
            world.fired.add(sig)
            child.memes["relief"] += 1
            out.append("__relief__")
    return out


def _r_laugh(world: World) -> list[str]:
    out: list[str] = []
    child = world.get("child")
    helper = world.get("helper")
    if child.memes["relief"] >= THRESHOLD and helper.memes["kind"] >= THRESHOLD:
        sig = ("laugh",)
        if sig not in world.fired:
            world.fired.add(sig)
            child.memes["joy"] += 1
            helper.memes["joy"] += 1
            out.append("__laugh__")
    return out


RULES = [
    _r_relief,
    _r_laugh,
]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in RULES:
            lines = rule(world)
            if lines:
                changed = True
                produced.extend(s for s in lines if not s.startswith("__"))
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def reasonableness_ok(problem: Problem, action: KindAction) -> bool:
    return problem.needs_kindness and action.can_fix


def choose_names(rng: random.Random) -> tuple[str, str]:
    child = rng.choice(NAME_POOL)
    helper = rng.choice([n for n in NAME_POOL if n != child])
    return child, helper


def predict(world: World) -> dict:
    sim = world.copy()
    child = sim.get("child")
    problem = sim.facts["problem"]
    child.meters["blocked"] += 1
    child.memes["embarrassed"] += 1
    if problem.id == "speaking":
        child.meters["repeated"] += 1
    propagate(sim, narrate=False)
    return {"calmed": child.meters["calmed"] >= THRESHOLD}


def setup(world: World, setting: Setting, child: Entity, helper: Entity, parent: Entity, problem: Problem) -> None:
    world.say(
        f"On a bright morning at {setting.place}, {child.id} tried to say one simple thing. "
        f"But {problem.symptom}, and the word came out in a funny little loop."
    )
    world.say(
        f'"{problem.repeat_line}" {child.id} said. Then {child.id} said it again. '
        f'{problem.funny_effect}'
    )
    child.memes["embarrassed"] += 1
    helper.memes["kind"] += 1


def comic_repetition(world: World, child: Entity, problem: Problem) -> None:
    child.meters["repeated"] += 1
    world.say(
        f"{child.id} tried one more time. "
        f'"{problem.repeat_line}" {child.id} said, and then {child.id} said it one more time, '
        f"as if the sentence had put on little tap shoes."
    )


def warn_kindly(world: World, helper: Entity, child: Entity, problem: Problem, parent: Entity) -> None:
    pred = predict(world)
    helper.memes["kind"] += 1
    child.memes["seen"] += 1
    world.facts["predicted_calmed"] = pred["calmed"]
    world.say(
        f"{helper.id} listened closely and smiled. "
        f'"You do not need to rush," {helper.pronoun()} said. '
        f'"{parent.label_word.capitalize()} will help, and the funny part is not your fault. '
        f"Let's take a breath, then try again."'
    )


def small_kindness(world: World, helper: Entity, child: Entity) -> None:
    child.meters["helped"] += 1
    child.meters["calmed"] += 1
    helper.meters["helped"] += 1
    helper.memes["kind"] += 1
    world.say(
        f"{helper.id} handed {child.pronoun('object')} a cup of water and stood beside {child.pronoun('object')} "
        f"like a tiny guard at the microphone."
    )
    world.say(
        f"That kind move made {child.id}'s shoulders drop. The room felt less silly and more safe."
    )


def resolution(world: World, child: Entity, helper: Entity, parent: Entity, problem: Problem) -> None:
    child.memes["relief"] += 1
    world.say(
        f"{child.id} tried again, slowly this time. "
        f'"{problem.repeat_line}" {child.id} said, and this time everyone understood.'
    )
    world.say(
        f"{parent.label_word.capitalize()} laughed a warm laugh, not a mean one. "
        f"{helper.id} laughed too, because the whole thing was a little ridiculous and a little brave."
    )
    world.say(
        f"By the end, {child.id} was speaking with a grin, and the funny little loop had turned into a shared joke."
    )


SETTINGS = {
    "kitchen": Setting("kitchen", "the kitchen", "A big spoon sat in a bowl, and the fridge hummed like a sleepy dog.", "cozy"),
    "classroom": Setting("classroom", "the classroom", "A line of chairs waited by the rug, and the alphabet posters watched from the wall.", "bright"),
    "living_room": Setting("living_room", "the living room", "A couch made a bouncy mountain, and the lamp made a warm circle on the floor.", "homey"),
}

PROBLEMS = {
    "speaking": Problem(
        "speaking",
        "adenoid",
        "their adenoid made their nose feel stuffed up",
        "I said I want the red cup",
        "The sentence came out a bit blocked, like it had to squeeze through a tiny door.",
    ),
    "humming": Problem(
        "humming",
        "adenoid",
        "their adenoid made their voice sound extra nasal",
        "la-la-little song",
        "The humming bounced around in a funny squeaky way, like a rubber duck trying opera.",
    ),
    "sniffling": Problem(
        "sniffling",
        "adenoid",
        "their adenoid made them sniffle and pause",
        "I can do it, I can do it",
        "Every pause arrived with a sniff, as if the sentence needed a tissue before it could continue.",
    ),
}

ACTIONS = {
    "kind_listen": KindAction("kind_listen", "listen kindly", "listened kindly", "helped the child feel heard"),
    "water": KindAction("water", "offer water", "offered a sip of water", "helped the child settle"),
    "practice": KindAction("practice", "practice slowly", "helped them practice slowly", "gave the child room to try again"),
}

CURATED = [
    ("kitchen", "speaking", "kind_listen"),
    ("classroom", "humming", "water"),
    ("living_room", "sniffling", "practice"),
]


def valid_combos() -> list[tuple[str, str, str]]:
    return [(s, p, a) for s in SETTINGS for p in PROBLEMS for a in ACTIONS if reasonableness_ok(PROBLEMS[p], ACTIONS[a])]


@dataclass
class StoryParams:
    setting: str
    problem: str
    action: str
    child: str
    helper: str
    parent_type: str
    seed: Optional[int] = None


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Comedy storyworld about adenoid repetition and kindness.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--problem", choices=PROBLEMS)
    ap.add_argument("--action", choices=ACTIONS)
    ap.add_argument("--parent", choices=["mother", "father", "teacher"])
    ap.add_argument("--name")
    ap.add_argument("--helper")
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
    if args.problem and args.action and not reasonableness_ok(PROBLEMS[args.problem], ACTIONS[args.action]):
        raise StoryError("This problem/action pair is not a sensible kindness fix.")
    combos = [c for c in valid_combos()
              if (args.setting is None or c[0] == args.setting)
              and (args.problem is None or c[1] == args.problem)
              and (args.action is None or c[2] == args.action)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    setting, problem, action = rng.choice(sorted(combos))
    child = args.name or rng.choice(NAME_POOL)
    helper = args.helper or rng.choice([n for n in NAME_POOL if n != child])
    parent = args.parent or rng.choice(["mother", "father", "teacher"])
    return StoryParams(setting, problem, action, child, helper, parent)


def tell(params: StoryParams) -> World:
    world = World()
    setting = SETTINGS[params.setting]
    problem = PROBLEMS[params.problem]
    action = ACTIONS[params.action]
    child = world.add(Entity("child", kind="character", type="boy" if params.child in {"Noah", "Eli", "Owen", "Finn", "Theo"} else "girl", label=params.child))
    helper = world.add(Entity("helper", kind="character", type="girl" if params.helper in {"Mia", "Luna", "Ivy", "Nina", "Ava"} else "boy", label=params.helper))
    parent = world.add(Entity("parent", kind="character", type=params.parent_type, label=params.parent_type, role="parent"))
    world.facts["problem"] = problem
    world.facts["action"] = action
    world.facts["setting"] = setting

    setup(world, setting, child, helper, parent, problem)
    world.para()
    comic_repetition(world, child, problem)
    warn_kindly(world, helper, child, problem, parent)
    small_kindness(world, helper, child)
    propagate(world, narrate=False)
    world.para()
    resolution(world, child, helper, parent, problem)
    return world


def generation_prompts(world: World) -> list[str]:
    p = world.facts["problem"]
    a = world.facts["action"]
    s = world.facts["setting"]
    return [
        f"Write a funny children's story at {s.place} that includes the word adenoid and a repeated line.",
        f"Tell a comedy story where a child keeps repeating a sentence because of an adenoid, and a kind helper makes things better.",
        f"Write a gentle, silly story about adenoid trouble, repeated words, and kindness that ends with a laugh.",
    ]


def story_qa(world: World) -> list[QAItem]:
    child = world.get("child")
    helper = world.get("helper")
    parent = world.get("parent")
    problem = world.facts["problem"]
    action = world.facts["action"]
    return [
        QAItem(
            f"Why did {child.id} keep repeating themself?",
            f"{child.id} kept repeating themself because {problem.symptom}. That made the sentence come out funny and blocked, so they needed help and patience."
        ),
        QAItem(
            f"What did {helper.id} do to help?",
            f"{helper.id} responded with kindness and {action.text}. That helped {child.id} calm down and try again without feeling embarrassed."
        ),
        QAItem(
            "How did the story end?",
            f"It ended with a laugh and a clear sentence. The adenoid problem was still there, but kindness made the moment feel warm instead of awkward."
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            "What is an adenoid?",
            "An adenoid is a small bit of tissue near the nose and throat. If it gets enlarged, it can make breathing and speaking feel stuffy."
        ),
        QAItem(
            "Why can kindness help when someone is embarrassed?",
            "Kindness helps because it makes people feel safe instead of judged. When someone feels safe, they can calm down and try again."
        ),
        QAItem(
            "Why is repeating a line sometimes funny in a story?",
            "Repeating a line can be funny because it sounds unexpected and rhythmic. In a comedy story, the repetition becomes a little joke without hurting anyone."
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== (2) Story QA ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== (3) World knowledge QA ==")
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
        if e.label:
            bits.append(f"label={e.label}")
        if e.role:
            bits.append(f"role={e.role}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    return "\n".join(lines)


ASP_RULES = r"""
valid(S,P,A) :- setting(S), problem(P), action(A), needs_kindness(P), can_fix(A).
kindness_fix(P,A) :- problem(P), action(A), needs_kindness(P), can_fix(A).
outcome(calm) :- kindness_fix(P,A), valid(S,P,A).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for s in SETTINGS:
        lines.append(asp.fact("setting", s))
    for p, obj in PROBLEMS.items():
        lines.append(asp.fact("problem", p))
        if obj.needs_kindness:
            lines.append(asp.fact("needs_kindness", p))
    for a, obj in ACTIONS.items():
        lines.append(asp.fact("action", a))
        if obj.can_fix:
            lines.append(asp.fact("can_fix", a))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    import asp
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    rc = 0
    if set(asp_valid_combos()) == set(valid_combos()):
        print(f"OK: gate matches valid_combos() ({len(valid_combos())} combos).")
    else:
        print("MISMATCH in gate.")
        rc = 1
    try:
        sample = generate(resolve_params(build_parser().parse_args([]), random.Random(7)))
        _ = sample.story
        print("OK: default generate smoke test passed.")
    except Exception as exc:
        print(f"SMOKE TEST FAILED: {exc}")
        rc = 1
    return rc


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


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("", "#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        for row in asp_valid_combos():
            print(row)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)
    samples = []
    if args.all:
        samples = [generate(StoryParams(s, p, a, random.choice(NAME_POOL), random.choice(NAME_POOL), "mother"))
                   for s, p, a in CURATED]
    else:
        for i in range(args.n):
            params = resolve_params(args, random.Random(base_seed + i))
            samples.append(generate(params))

    if args.json:
        print(samples[0].to_json() if len(samples) == 1 else json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return
    for i, sample in enumerate(samples):
        emit(sample, trace=args.trace, qa=args.qa, header=(f"### variant {i+1}" if len(samples) > 1 else ""))
        if i + 1 < len(samples):
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()

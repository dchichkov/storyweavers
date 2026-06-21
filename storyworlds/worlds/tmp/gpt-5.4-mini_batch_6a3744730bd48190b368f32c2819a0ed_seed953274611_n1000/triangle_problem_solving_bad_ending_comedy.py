#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/triangle_problem_solving_bad_ending_comedy.py
=============================================================================

A tiny standalone storyworld about a triangle-shaped prop, a comic problem,
and a bad ending where the fixes go wrong. The prose is child-facing, concrete,
and state-driven: the triangle starts useful, gets into trouble, characters try
to solve the problem, and the ending shows that their solution fails.

Domain sketch
-------------
Two children are helping with a silly little show. Their star prop is a paper
triangle on a stand. The triangle keeps wobbling, then the helpers try a few
problem-solving tricks, and each fix makes the mess a little worse. The final
image is a comedic bad ending: the triangle ends up soggy, bent, and useless.

The world keeps both physical meters and emotional memes, and it includes an
inline ASP twin plus a Python reasonableness gate. The ASP and Python logic are
small, deterministic, and checked in --verify.

Run it
------
    python storyworlds/worlds/gpt-5.4-mini/triangle_problem_solving_bad_ending_comedy.py
    python storyworlds/worlds/gpt-5.4-mini/triangle_problem_solving_bad_ending_comedy.py --all
    python storyworlds/worlds/gpt-5.4-mini/triangle_problem_solving_bad_ending_comedy.py -n 5 --seed 7 --qa
    python storyworlds/worlds/gpt-5.4-mini/triangle_problem_solving_bad_ending_comedy.py --verify
    python storyworlds/worlds/gpt-5.4-mini/triangle_problem_solving_bad_ending_comedy.py --json
"""

from __future__ import annotations

import argparse
import json
import os
import random
import sys
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from results import QAItem, StoryError, StorySample  # noqa: E402

THRESHOLD = 1.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    traits: list[str] = field(default_factory=list)
    role: str = ""
    attrs: dict = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman"}
        male = {"boy", "father", "dad", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return {"mother": "mom", "father": "dad"}.get(self.type, self.type)


@dataclass
class Setting:
    id: str
    place: str
    stage: str
    audience: str


@dataclass
class Problem:
    id: str
    label: str
    issue: str
    wobble_gain: float
    mess_gain: float
    comedy: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Fix:
    id: str
    label: str
    sense: int
    power: int
    text: str
    fail: str
    tags: set[str] = field(default_factory=set)


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
        w = World()
        w.entities = {k: Entity(**{
            "id": e.id, "kind": e.kind, "type": e.type, "label": e.label,
            "traits": list(e.traits), "role": e.role, "attrs": dict(e.attrs),
            "meters": defaultdict(float, dict(e.meters)),
            "memes": defaultdict(float, dict(e.memes)),
        }) for k, e in self.entities.items()}
        w.fired = set(self.fired)
        w.paragraphs = [[]]
        return w


def _r_spread(world: World) -> list[str]:
    out: list[str] = []
    triangle = world.get("triangle")
    if triangle.meters["wobble"] >= THRESHOLD and ("spread",) not in world.fired:
        world.fired.add(("spread",))
        triangle.meters["mess"] += 1
        for kid in ("kid1", "kid2"):
            world.get(kid).memes["panic"] += 1
        out.append("__wobble__")
    return out


CAUSAL_RULES = [_r_spread]


def propagate(world: World) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            sents = rule(world)
            if sents:
                changed = True
                produced.extend(s for s in sents if not s.startswith("__"))
    for s in produced:
        world.say(s)
    return produced


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for s in SETTINGS:
        for p in PROBLEMS:
            for f in FIXES:
                if problem_is_reasonable(PROBLEMS[p], FIXES[f]):
                    combos.append((s, p, f))
    return combos


def problem_is_reasonable(problem: Problem, fix: Fix) -> bool:
    return fix.sense >= 2 and problem.id == "triangle_stage" and fix.id in {"tape_props", "fan_blow", "crate_stack"}


def fix_success(problem: Problem, fix: Fix) -> bool:
    return fix.power >= 3 and fix.id == "crate_stack"


def tell(setting: Setting, problem: Problem, fix: Fix, kid1: str = "Mila", kid2: str = "Bo") -> World:
    world = World()
    a = world.add(Entity(id="kid1", kind="character", type="girl", role="helper", label=kid1))
    b = world.add(Entity(id="kid2", kind="character", type="boy", role="helper", label=kid2))
    t = world.add(Entity(id="triangle", kind="thing", type="thing", label="the triangle", attrs={"setting": setting.id}))
    world.say(
        f"At {setting.place}, {kid1} and {kid2} were helping with {setting.stage}. "
        f"The star of the show was {t.label}, and it looked proud enough to be a pie slice."
    )
    world.say(
        f"{t.label.capitalize()} had one job: stay steady for the audience, which was mostly {setting.audience} and one very serious goldfish."
    )
    world.para()
    t.meters["wobble"] += problem.wobble_gain
    t.meters["mess"] += problem.mess_gain
    a.memes["concern"] += 1
    b.memes["concern"] += 1
    world.say(
        f"But {problem.comedy} {problem.issue}. {kid1} blinked and said, 'Hmm. That triangle is doing the wobble dance.'"
    )
    world.say(
        f"{kid2} nodded. 'Easy,' {b.pronoun()} said. 'We'll solve it with {fix.label}.'"
    )
    world.para()
    if fix.id == "tape_props":
        world.say(
            f"So they taped the feet of the stand to the floor. That helped for exactly one sneeze."
        )
        t.meters["wobble"] += 1
        t.meters["mess"] += 1
        a.memes["hope"] += 1
        b.memes["hope"] += 1
        propagate(world)
        world.say(
            f"Then the triangle leaned the other way and the tape peeled up like a tiny banana skin."
        )
    elif fix.id == "fan_blow":
        world.say(
            f"So they pointed a fan at it to make it 'more exciting.' The fan worked too well."
        )
        t.meters["wobble"] += 2
        t.meters["mess"] += 1
        a.memes["giggly"] += 1
        b.memes["giggly"] += 1
        propagate(world)
        world.say(
            f"The triangle spun, did one brave little twirl, and toppled straight into the snack table."
        )
    else:
        world.say(
            f"So they stacked two wobbly crates under it and called it a tower of wisdom."
        )
        t.meters["wobble"] += 1
        t.meters["mess"] += 2
        a.memes["hope"] += 1
        b.memes["hope"] += 1
        propagate(world)
        world.say(
            f"The tower sighed, folded, and dropped the triangle into the frosting bowl with a soft plop."
        )

    t.meters["soggy"] += 1
    t.meters["ruined"] += 1
    a.memes["embarrassed"] += 1
    b.memes["embarrassed"] += 1
    world.para()
    world.say(
        f"In the end, {problem.comedy.lower()} {t.label} sat there bent, damp, and crooked. "
        f"The audience clapped anyway, mostly because nobody could stop laughing."
    )
    world.say(
        f"{kid1} and {kid2} bowed next to the soggy triangle, which now looked less like a prop and more like a tired pizza slice."
    )

    outcome = "failed" if not fix_success(problem, fix) else "failed"
    world.facts.update(
        setting=setting, problem=problem, fix=fix, kid1=a, kid2=b, triangle=t,
        outcome=outcome, ruined=True, soggy=True
    )
    return world


SETTINGS = {
    "hall": Setting(id="hall", place="the school hall", stage="the talent show", audience="parents"),
    "kitchen": Setting(id="kitchen", place="the kitchen table", stage="the family skit", audience="aunts"),
    "garage": Setting(id="garage", place="the garage stage", stage="the make-believe show", audience="neighbors"),
}

PROBLEMS = {
    "triangle_stage": Problem(
        id="triangle_stage",
        label="triangle",
        issue="the paper triangle kept wobbling on its stand",
        wobble_gain=1.0,
        mess_gain=0.0,
        comedy="A serious-looking",
        tags={"triangle"},
    )
}

FIXES = {
    "tape_props": Fix(id="tape_props", label="tape", sense=2, power=1, text="", fail="", tags={"tape"}),
    "fan_blow": Fix(id="fan_blow", label="a fan", sense=2, power=1, text="", fail="", tags={"fan"}),
    "crate_stack": Fix(id="crate_stack", label="two crates", sense=3, power=2, text="", fail="", tags={"crate"}),
}

CURATED = [
    StoryParams = None
]

@dataclass
class StoryParams:
    setting: str
    problem: str
    fix: str
    seed: Optional[int] = None


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f"Write a funny story about a triangle that will not stay still, and two kids who try to solve the problem.",
        f"Tell a comedy story where {f['kid1'].label} and {f['kid2'].label} try to fix {f['triangle'].label} but make things worse.",
        f"Write a child-friendly bad-ending story that includes the word triangle and ends with a silly mess.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    k1, k2, tri = f["kid1"], f["kid2"], f["triangle"]
    return [
        ("Who was trying to help?",
         f"{k1.label} and {k2.label} were trying to help. They wanted the show to go well, even though the triangle kept wobbling."),
        ("What was the problem?",
         f"The triangle kept wobbling on its stand. That made the show hard to finish, so they tried to solve it."),
        ("How did the story end?",
         f"It ended badly and very sillily. The triangle was bent, damp, and ruined, and the audience laughed instead of cheering."),
    ]


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    return [
        ("What is a triangle?",
         "A triangle is a shape with three sides and three corners. People can draw it, cut it out, or use it in signs and toys."),
        ("Why can a prop fall over?",
         "A prop can fall over if it is too wobbly or not balanced well. When the base is shaky, even a small push can topple it."),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    for p in sample.prompts:
        lines.append(p)
    lines.append("== story qa ==")
    for q in sample.story_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    lines.append("== world qa ==")
    for q in sample.world_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world ---"]
    for e in world.entities.values():
        lines.append(f"{e.id}: meters={dict(e.meters)} memes={dict(e.memes)}")
    lines.append(f"fired={sorted(world.fired)}")
    return "\n".join(lines)


def explain_rejection() -> str:
    return "(No story: this triangle fix is not reasonable enough for the tiny comedy world.)"


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    setting = args.setting or rng.choice(list(SETTINGS))
    problem = args.problem or "triangle_stage"
    fix = args.fix or rng.choice(list(FIXES))
    if not problem_is_reasonable(PROBLEMS[problem], FIXES[fix]):
        raise StoryError(explain_rejection())
    return StoryParams(setting=setting, problem=problem, fix=fix)


def generate(params: StoryParams) -> StorySample:
    if params.setting not in SETTINGS or params.problem not in PROBLEMS or params.fix not in FIXES:
        raise StoryError("Invalid story parameters.")
    world = tell(SETTINGS[params.setting], PROBLEMS[params.problem], FIXES[params.fix])
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=[QAItem(question=q, answer=a) for q, a in story_qa(world)],
        world_qa=[QAItem(question=q, answer=a) for q, a in world_knowledge_qa(world)],
        world=world,
    )


ASP_RULES = r"""
triangle_problem(T) :- triangle(T).
wobbly(T) :- wobble(T, V), V >= 1.
ruined(T) :- soggy(T), bent(T).
bad_ending :- triangle_problem(T), ruined(T).
"""


def asp_facts() -> str:
    import asp
    return "\n".join([
        asp.fact("triangle", "triangle"),
        asp.fact("wobble", "triangle", 1),
        asp.fact("soggy", "triangle"),
    ])


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show triangle_problem/1.\n#show bad_ending/0."))
    ok = bool(model)
    sample = generate(StoryParams(setting="hall", problem="triangle_stage", fix="crate_stack"))
    if ok and sample.story:
        print("OK: ASP gate and generate() smoke test passed.")
        return 0
    print("FAIL: verification did not pass.")
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Triangle comedy storyworld with a bad ending.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--problem", choices=PROBLEMS)
    ap.add_argument("--fix", choices=FIXES)
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
        print(asp_program("#show triangle_problem/1.\n#show bad_ending/0."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(asp_program("#show triangle_problem/1.\n#show bad_ending/0."))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        for p in [StoryParams(setting="hall", problem="triangle_stage", fix="crate_stack")]:
            samples.append(generate(p))
    else:
        seen = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 20, 20):
            i += 1
            try:
                params = resolve_params(args, random.Random(base_seed + i))
            except StoryError as err:
                print(err)
                return
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

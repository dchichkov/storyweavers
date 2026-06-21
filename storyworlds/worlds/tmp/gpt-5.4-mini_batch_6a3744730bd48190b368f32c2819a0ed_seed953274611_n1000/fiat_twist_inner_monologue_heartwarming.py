#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/fiat_twist_inner_monologue_heartwarming.py
===========================================================================

A small, heartwarming storyworld about a child, a beloved old Fiat, a tiny
travel snag, and a gentle twist. The story uses a simulated world model with
physical meters and emotional memes, an inner-monologue beat, and a final
reversal that turns worry into warmth.

Seed words:
- fiat

Features:
- Twist
- Inner Monologue

Style:
- Heartwarming
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
from typing import Callable, Optional

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
class Place:
    id: str
    label: str
    scene: str
    indoors: bool = True
    tags: set[str] = field(default_factory=set)


@dataclass
class Problem:
    id: str
    label: str
    cause: str
    danger: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Fix:
    id: str
    label: str
    prep: str
    result: str
    power: int
    sense: int
    tags: set[str] = field(default_factory=set)


@dataclass
class StoryParams:
    place: str = "driveway"
    problem: str = "battery"
    fix: str = "jumper_cables"
    child_name: str = "Mina"
    child_gender: str = "girl"
    parent_name: str = "Dad"
    parent_gender: str = "man"
    twist: str = "grandma_visit"
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
        return clone


@dataclass
class Rule:
    name: str
    apply: Callable[[World], list[str]]


def _r_worry(world: World) -> list[str]:
    out = []
    car = world.get("fiat")
    if car.meters["broken"] >= THRESHOLD and ("worry", "child") not in world.fired:
        world.fired.add(("worry", "child"))
        child = world.get("child")
        child.memes["worry"] += 1
        out.append("__inner__")
    return out


def _r_relief(world: World) -> list[str]:
    out = []
    car = world.get("fiat")
    if car.meters["fixed"] >= THRESHOLD and ("relief", "child") not in world.fired:
        world.fired.add(("relief", "child"))
        child = world.get("child")
        child.memes["relief"] += 1
        child.memes["joy"] += 1
        out.append("__twist__")
    return out


CAUSAL_RULES = [Rule("worry", _r_worry), Rule("relief", _r_relief)]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            sents = rule.apply(world)
            if sents:
                changed = True
                produced.extend(s for s in sents if not s.startswith("__"))
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def problem_at_risk(problem: Problem) -> bool:
    return problem.id in {"battery", "flat_tire", "stuck_trunk"}


def sensible_fixes() -> list[Fix]:
    return [f for f in FIXES.values() if f.sense >= 2]


def fix_works(fix: Fix, problem: Problem) -> bool:
    return fix.power >= {"battery": 1, "flat_tire": 2, "stuck_trunk": 1}.get(problem.id, 99)


def _do_problem(world: World, narrate: bool = True) -> None:
    car = world.get("fiat")
    car.meters["broken"] += 1
    propagate(world, narrate=narrate)


def _apply_fix(world: World, fix: Fix, narrate: bool = True) -> None:
    car = world.get("fiat")
    car.meters["broken"] = 0
    car.meters["fixed"] += 1
    world.get("child").memes["hope"] += 1
    if narrate:
        world.say(fix.result)


def tell(place: Place, problem: Problem, fix: Fix, params: StoryParams) -> World:
    world = World()
    child = world.add(Entity(id="child", kind="character", type=params.child_gender, label=params.child_name, role="child"))
    parent = world.add(Entity(id="parent", kind="character", type=params.parent_gender, label=params.parent_name, role="parent"))
    fiat = world.add(Entity(id="fiat", kind="thing", type="car", label="the old Fiat", role="beloved_car"))
    world.add(Entity(id="keys", kind="thing", type="thing", label="the keys"))
    world.add(Entity(id="basket", kind="thing", type="thing", label="the basket"))
    world.facts["place"] = place
    world.facts["problem"] = problem
    world.facts["fix"] = fix
    world.facts["child"] = child
    world.facts["parent"] = parent
    world.facts["fiat"] = fiat

    world.say(
        f"{child.id} loved {place.label}, because it meant rides in the old Fiat and warm waves to people along the way."
    )
    world.say(
        f"That morning, {child.id} helped pack a basket for a visit and touched the Fiat's door with a hopeful hand."
    )
    world.para()
    world.say(
        f"But the Fiat would not go. {problem.cause.capitalize()} made it hesitate, and the quiet in the driveway suddenly felt very big."
    )
    _do_problem(world, narrate=False)
    world.say(
        f"{child.id} looked at the car and tried not to frown."
    )
    world.say(
        f'Inside, {child.id} thought, "Please start, please start. I wanted today to feel special."'
    )
    world.say(
        f"{parent.id} heard that little worry and knelt beside {child.id}."
    )

    if fix_works(fix, problem):
        world.para()
        world.say(
            f'{parent.id} smiled. "Here is the twist," {parent.pronoun()} said. '
            f'"We are not rushing away at all. {params.twist.replace("_", " ").capitalize()} means {child.id} gets to stay here and wait for Grandma to arrive."'
        )
        _apply_fix(world, fix, narrate=True)
        world.say(
            f"{child.id}'s worry softened into surprise. The Fiat was fixed, and the basket became a picnic on the front steps instead of a long drive."
        )
        world.say(
            f"Soon Grandma waved from the gate, and {child.id} laughed as the old Fiat shone in the sun like it had been waiting for that exact happy moment."
        )
    else:
        world.para()
        world.say(
            f'{parent.id} hugged {child.id} and said, "We can still make this kind."'
        )
        world.say(
            f"They called for help, stayed together, and turned the picnic into a front-porch celebration while the Fiat rested."
        )
        world.say(
            f"{child.id} decided a changed plan could still be a good one, as long as everyone was safe and together."
        )

    world.facts["outcome"] = "fixed" if fix_works(fix, problem) else "adapted"
    return world


PLACE_REGISTRY = {
    "driveway": Place(id="driveway", label="the driveway", scene="a bright driveway", tags={"car", "home"}),
    "garage": Place(id="garage", label="the garage", scene="a cozy garage", tags={"car", "home"}),
    "street": Place(id="street", label="the quiet street", scene="a quiet street", tags={"car", "travel"}),
}

PROBLEMS = {
    "battery": Problem(id="battery", label="a dead battery", cause="the battery was tired", danger="the car would not start", tags={"car", "fix"}),
    "flat_tire": Problem(id="flat_tire", label="a flat tire", cause="one tire had gone squishy", danger="the car could not roll safely", tags={"car", "fix"}),
    "stuck_trunk": Problem(id="stuck_trunk", label="a stuck trunk", cause="the trunk latch was jammed", danger="the basket could not get inside", tags={"car", "fix"}),
}

FIXES = {
    "jumper_cables": Fix(id="jumper_cables", label="jumper cables", prep="hook up the jumper cables", result="He hooked up the jumper cables, and the Fiat coughed, then purred back to life.", power=1, sense=3, tags={"battery", "car"}),
    "spare_tire": Fix(id="spare_tire", label="a spare tire", prep="change the tire", result="He changed the tire, and the Fiat stood tall again on its spare.", power=2, sense=3, tags={"flat_tire", "car"}),
    "gentle_push": Fix(id="gentle_push", label="a gentle push", prep="give the car a gentle push", result="They gave the Fiat a gentle push, and the trunk finally clicked shut with a tiny cheer.", power=1, sense=2, tags={"stuck_trunk", "car"}),
}

TWISTS = {
    "grandma_visit": "grandma_visit",
    "surprise_pie": "surprise_pie",
    "rainbow_ribbon": "rainbow_ribbon",
}

CHILD_NAMES = ["Mina", "Noah", "Lena", "Owen", "Mila", "Theo"]
PARENT_NAMES = ["Mom", "Dad", "Aunt June", "Uncle Ray"]


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for p in PLACE_REGISTRY:
        for prob in PROBLEMS.values():
            for fx in FIXES.values():
                if problem_at_risk(prob) and fix_works(fx, prob) and fx.sense >= 2:
                    combos.append((p, prob.id, fx.id))
    return combos


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Heartwarming Fiat storyworld with a twist and inner monologue.")
    ap.add_argument("--place", choices=PLACE_REGISTRY)
    ap.add_argument("--problem", choices=PROBLEMS)
    ap.add_argument("--fix", choices=FIXES)
    ap.add_argument("--child-name")
    ap.add_argument("--child-gender", choices=["girl", "boy"])
    ap.add_argument("--parent-name")
    ap.add_argument("--parent-gender", choices=["woman", "man"])
    ap.add_argument("--twist", choices=TWISTS)
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
    if args.problem and args.fix:
        prob = PROBLEMS[args.problem]
        fx = FIXES[args.fix]
        if not (problem_at_risk(prob) and fix_works(fx, prob) and fx.sense >= 2):
            raise StoryError("That fix does not reasonably solve that problem.")
    combos = [c for c in valid_combos()
              if (args.place is None or c[0] == args.place)
              and (args.problem is None or c[1] == args.problem)
              and (args.fix is None or c[2] == args.fix)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, problem, fix = rng.choice(sorted(combos))
    return StoryParams(
        place=place,
        problem=problem,
        fix=fix,
        child_name=args.child_name or rng.choice(CHILD_NAMES),
        child_gender=args.child_gender or rng.choice(["girl", "boy"]),
        parent_name=args.parent_name or rng.choice(PARENT_NAMES),
        parent_gender=args.parent_gender or rng.choice(["woman", "man"]),
        twist=args.twist or rng.choice(sorted(TWISTS)),
    )


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a heartwarming story about a child and the old Fiat, including the word "fiat".',
        f"Tell a gentle story where {f['child'].id} worries the Fiat will not start, but a parent reveals a kind twist.",
        f"Write a story with an inner monologue, a car problem, and a warm surprise ending.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child = f["child"]
    parent = f["parent"]
    problem = f["problem"]
    fix = f["fix"]
    qa = [
        QAItem(
            question=f"What was wrong with the Fiat?",
            answer=f"It had {problem.label}, so it could not do what the family needed right away. That was why {child.id} felt a pinch of worry in the driveway."
        ),
        QAItem(
            question=f"What did {child.id} think to {child.pronoun('object')}self?",
            answer=f"{child.id} silently hoped the Fiat would start and make the day special. That inner thought showed how much {child.id} cared about the trip."
        ),
    ]
    if f["outcome"] == "fixed":
        qa.append(
            QAItem(
                question="What was the twist in the story?",
                answer=f"The twist was that the family did not need to rush away at all. {parent.id} turned the plan into a home visit, and the Fiat got fixed in time for a happy welcome."
            )
        )
        qa.append(
            QAItem(
                question="How did the story end?",
                answer=f"It ended with the Fiat working again and everyone feeling warm and relieved. {child.id} could smile at the surprise instead of the worry."
            )
        )
    else:
        qa.append(
            QAItem(
                question="How did the family solve the problem?",
                answer=f"They changed the plan and stayed together safely while the Fiat rested. That way the day still felt kind, even though the car needed more time."
            )
        )
    return qa


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a Fiat?",
            answer="A Fiat is a kind of car. In stories like this, it can be an old family car that still feels loved."
        ),
        QAItem(
            question="What does jumper cables mean?",
            answer="Jumper cables are wires grown-ups use to help a car with a weak battery start again. They can bring back power when the battery is tired."
        ),
        QAItem(
            question="Why do people use a spare tire?",
            answer="A spare tire replaces a flat tire for a while. It helps the car roll safely until the broken tire can be fixed."
        ),
    ]


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
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if e.role:
            bits.append(f"role={e.role}")
        if e.label:
            bits.append(f"label={e.label!r}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    return "\n".join(lines)


def generate(params: StoryParams) -> StorySample:
    if params.place not in PLACE_REGISTRY:
        raise StoryError("Unknown place.")
    if params.problem not in PROBLEMS:
        raise StoryError("Unknown problem.")
    if params.fix not in FIXES:
        raise StoryError("Unknown fix.")
    place = PLACE_REGISTRY[params.place]
    problem = PROBLEMS[params.problem]
    fix = FIXES[params.fix]
    world = tell(place, problem, fix, params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


ASP_RULES = r"""
valid(P, Prob, Fix) :- place(P), problem(Prob), fix(Fix), works(Fix, Prob), sensible(Fix).
fixed :- chosen_fix(F), chosen_problem(P), works(F, P).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for p in PLACE_REGISTRY:
        lines.append(asp.fact("place", p))
    for pid, prob in PROBLEMS.items():
        lines.append(asp.fact("problem", pid))
        lines.append(asp.fact("cause", pid, prob.cause))
    for fid, fix in FIXES.items():
        lines.append(asp.fact("fix", fid))
        lines.append(asp.fact("works", fid, "battery" if fid == "jumper_cables" else ("flat_tire" if fid == "spare_tire" else "stuck_trunk")))
        lines.append(asp.fact("sense", fid, fix.sense))
    lines.append(asp.fact("sense_min", 2))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    rc = 0
    if set(asp_valid_combos()) != set(valid_combos()):
        rc = 1
        print("MISMATCH: ASP valid combos differ from Python.")
    try:
        sample = generate(resolve_params(build_parser().parse_args([]), random.Random(777)))
        _ = sample.story
        print("OK: generation smoke test passed.")
    except Exception as exc:  # noqa: BLE001
        print(f"SMOKE TEST FAILED: {exc}")
        return 1
    return rc


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
        combos = asp_valid_combos()
        print(f"{len(combos)} valid combos:")
        for row in combos:
            print("  ", row)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        curated = [
            StoryParams(place="driveway", problem="battery", fix="jumper_cables", child_name="Mina", child_gender="girl", parent_name="Dad", parent_gender="man", twist="grandma_visit"),
            StoryParams(place="garage", problem="flat_tire", fix="spare_tire", child_name="Noah", child_gender="boy", parent_name="Mom", parent_gender="woman", twist="surprise_pie"),
            StoryParams(place="street", problem="stuck_trunk", fix="gentle_push", child_name="Lena", child_gender="girl", parent_name="Aunt June", parent_gender="woman", twist="rainbow_ribbon"),
        ]
        samples = [generate(p) for p in curated]
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

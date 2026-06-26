#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260626T055019Z_seed926384711_n100/bolster_harsh_problem_solving_slice_of_life.py
========================================================================================================================

A small slice-of-life storyworld about noticing a problem, testing a fix, and
making a cozy outcome. The seed words are "bolster" and "harsh", and the story
space stays close to everyday problem solving.

World premise:
- A child notices something in a home or neighborhood setting feels harsh or
  uncomfortable.
- The child and a helper try a practical fix using a bolster or similar support.
- The world model tracks physical comfort, stability, and emotional relief.
- The ending proves the fix worked by changing the state of the place or object.

This script follows the Storyweavers contract:
- standalone stdlib storyworld script
- eager import of storyworlds/results.py
- lazy import of storyworlds/asp.py in ASP helpers
- StoryParams, registries, build_parser, resolve_params, generate, emit, main
- supports default run, -n, --all, --seed, --trace, --qa, --json, --asp,
  --verify, and --show-asp
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
    plural: bool = False
    protective: bool = False
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
    mood: str
    affords: set[str] = field(default_factory=set)


@dataclass
class Problem:
    id: str
    verb: str
    gerund: str
    harsh: str
    risk: str
    zone: set[str]
    keyword: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Fix:
    id: str
    label: str
    covers: set[str]
    solves: set[str]
    prep: str
    tail: str
    plural: bool = False


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.problem_zone: set[str] = set()
        self.facts: dict = {}

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str) -> Entity:
        return self.entities[eid]

    def characters(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.kind == "character"]

    def worn_items(self, actor: Entity) -> list[Entity]:
        return [e for e in self.entities.values() if e.worn_by == actor.id]

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
        clone.problem_zone = set(self.problem_zone)
        clone.paragraphs = [[]]
        return clone


def _embed_stability(world: World) -> list[str]:
    out: list[str] = []
    for actor in world.characters():
        if actor.meters.get("problem", 0.0) < THRESHOLD:
            continue
        for item in world.worn_items(actor):
            if item.protective:
                continue
            if item.id in world.fired:
                continue
            world.fired.add(("jostle", actor.id, item.id))
            item.meters["worn"] = item.meters.get("worn", 0.0) + 1
            out.append(f"{actor.pronoun('possessive').capitalize()} {item.label} shifted a little.")
    return out


def _resolve_comfort(world: World) -> list[str]:
    out: list[str] = []
    for obj in world.entities.values():
        if obj.meters.get("uneasy", 0.0) < THRESHOLD:
            continue
        if obj.meters.get("comfortable", 0.0) >= THRESHOLD:
            continue
        if ("comfort", obj.id) in world.fired:
            continue
        world.fired.add(("comfort", obj.id))
        obj.meters["comfortable"] = 1.0
        out.append(f"The little fix made {obj.label} feel much kinder.")
    return out


CAUSAL_RULES = [_embed_stability, _resolve_comfort]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            sents = rule(world)
            if sents:
                changed = True
                produced.extend(sents)
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def problem_needs_fix(problem: Problem, fix: Fix) -> bool:
    return bool(problem.zone & fix.covers and problem.id in fix.solves)


def select_fix(problem: Problem, fixes: list[Fix]) -> Optional[Fix]:
    for fx in fixes:
        if problem_needs_fix(problem, fx):
            return fx
    return None


def predict_fix(world: World, hero: Entity, problem: Problem, object_id: str) -> dict:
    sim = world.copy()
    _do_problem(sim, sim.get(hero.id), problem, narrate=False)
    obj = sim.entities.get(object_id)
    return {
        "uneasy": bool(obj and obj.meters.get("uneasy", 0.0) >= THRESHOLD),
        "comfortable": bool(obj and obj.meters.get("comfortable", 0.0) >= THRESHOLD),
    }


def _do_problem(world: World, actor: Entity, problem: Problem, narrate: bool = True) -> None:
    if problem.id not in world.setting.affords:
        return
    world.problem_zone = set(problem.zone)
    actor.meters["problem"] = actor.meters.get("problem", 0.0) + 1
    actor.memes["concern"] = actor.memes.get("concern", 0.0) + 1
    propagate(world, narrate=narrate)


def setting_detail(setting: Setting, problem: Problem) -> str:
    if setting.place == "the kitchen":
        return "The room had a busy morning feeling, with one corner that looked a little too hard."
    if setting.place == "the porch":
        return "The porch felt open and bright, but the seat there looked rough and plain."
    if setting.place == "the reading nook":
        return "The reading nook was quiet, yet the cushion had gone flat."
    return f"{setting.place.capitalize()} held a small everyday problem."


def introduce(world: World, hero: Entity) -> None:
    world.say(f"{hero.id} was a small {hero.type} who noticed details other people missed.")


def notice_harshness(world: World, hero: Entity, problem: Problem, object_: Entity) -> None:
    hero.memes["notice"] = hero.memes.get("notice", 0.0) + 1
    world.say(
        f"One afternoon, {hero.id} saw that {object_.phrase} felt {problem.harsh}. "
        f"{setting_detail(world.setting, problem)}"
    )


def want_to_help(world: World, hero: Entity, helper: Entity, problem: Problem) -> None:
    hero.memes["care"] = hero.memes.get("care", 0.0) + 1
    world.say(
        f"{hero.id} wanted to help, so {hero.pronoun()} went to {helper.label} and asked what to do."
    )


def explain(world: World, helper: Entity, problem: Problem, object_: Entity) -> None:
    world.say(
        f'"{object_.label.capitalize()} is too {problem.harsh}," {helper.label} said. '
        f'"We need a gentle fix, not a big fuss."'
    )


def try_bolster(world: World, hero: Entity, helper: Entity, problem: Problem, object_: Entity, fix: Fix) -> None:
    world.say(
        f'Together they found {fix.label} and decided to {fix.prep}. '
        f"It was a small, careful way to solve the problem."
    )
    object_.meters["uneasy"] = object_.meters.get("uneasy", 0.0) + 1
    fix_ent = world.add(Entity(
        id=fix.id,
        type="support",
        label=fix.label,
        owner=hero.id,
        caretaker=helper.id,
        protective=True,
        plural=fix.plural,
    ))
    fix_ent.worn_by = None
    object_.meters["comfortable"] = 1.0
    hero.memes["pride"] = hero.memes.get("pride", 0.0) + 1
    helper.memes["relief"] = helper.memes.get("relief", 0.0) + 1
    world.say(
        f"They tucked the {fix.label} in place, and {object_.label} stopped feeling so harsh."
    )
    world.say(
        f"After that, {hero.id} could stay nearby, and the little problem felt sorted out."
    )


SETTING_REGISTRY = {
    "kitchen": Setting(place="the kitchen", mood="busy", affords={"chair", "bench", "stool"}),
    "porch": Setting(place="the porch", mood="bright", affords={"bench", "seat", "step"}),
    "reading_nook": Setting(place="the reading nook", mood="quiet", affords={"cushion", "pillow", "chair"}),
}

PROBLEMS = {
    "hard_seat": Problem(
        id="hard_seat",
        verb="make a seat feel better",
        gerund="making a seat feel softer",
        harsh="too hard",
        risk="a sore back",
        zone={"seat"},
        keyword="bolster",
        tags={"bolster", "harsh", "comfort"},
    ),
    "wobbly_chair": Problem(
        id="wobbly_chair",
        verb="steady a chair",
        gerund="steadying a wobbly chair",
        harsh="shaky",
        risk="a tumble",
        zone={"chair"},
        keyword="bolster",
        tags={"bolster", "harsh", "stability"},
    ),
    "flat_cushion": Problem(
        id="flat_cushion",
        verb="make a cushion feel plumper",
        gerund="plumping a flat cushion",
        harsh="flat and stiff",
        risk="a tired sit",
        zone={"cushion"},
        keyword="bolster",
        tags={"bolster", "harsh", "comfort"},
    ),
}

FIXES = [
    Fix(id="bolster", label="a bolster pillow", covers={"seat", "chair", "cushion"}, solves={"hard_seat", "wobbly_chair", "flat_cushion"}, prep="slip the bolster pillow under it", tail="tucked the bolster pillow under the seat"),
    Fix(id="folded_blanket", label="a folded blanket", covers={"seat", "cushion"}, solves={"hard_seat", "flat_cushion"}, prep="fold the blanket and place it neatly", tail="laid the folded blanket in place"),
    Fix(id="book_stack", label="a stack of books", covers={"chair"}, solves={"wobbly_chair"}, prep="prop one leg carefully with books", tail="propped the chair with books"),
]

NAMES = ["Mia", "Leo", "Noah", "Ava", "Nina", "Eli", "June", "Owen"]
HELPERS = ["mother", "father", "grandma", "grandpa", "older sister", "older brother"]
TRAITS = ["patient", "curious", "kind", "gentle", "thoughtful", "cheerful"]


@dataclass
class StoryParams:
    place: str
    problem: str
    name: str
    helper: str
    trait: str
    seed: Optional[int] = None


def valid_combos() -> list[tuple[str, str]]:
    combos = []
    for place, setting in SETTING_REGISTRY.items():
        for pid, prob in PROBLEMS.items():
            if pid in {"hard_seat", "wobbly_chair", "flat_cushion"} and setting.affords:
                if select_fix(prob, FIXES):
                    combos.append((place, pid))
    return combos


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a short slice-of-life story for a child that includes the words "bolster" and "harsh".',
        f"Tell a gentle everyday story where {f['hero'].id} notices a harsh little problem at {f['setting'].place} and solves it with a bolster.",
        f"Write a simple story about practical problem solving, a supportive helper, and a tiny fix that makes a place feel cozy again.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    helper = f["helper"]
    problem = f["problem"]
    obj = f["object"]
    fix = f["fix"]
    return [
        QAItem(
            question=f"What did {hero.id} notice at {world.setting.place}?",
            answer=f"{hero.id} noticed that {obj.label} felt {problem.harsh}, which made the spot seem uncomfortable.",
        ),
        QAItem(
            question=f"How did {hero.id} and {helper.label} solve the problem?",
            answer=f"They used {fix.label} to support {obj.label}. That simple fix turned the harsh spot into a cozier one.",
        ),
        QAItem(
            question=f"Why was the fix a good idea?",
            answer=f"It was a good idea because it matched the problem: the seat or cushion needed support, and the bolster gave it just that.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does bolster mean here?",
            answer="Here, bolster means a pillow or support that helps hold something up and make it more comfortable.",
        ),
        QAItem(
            question="What does harsh mean?",
            answer="Harsh means rough, hard, or unpleasant, like something that feels too stiff or too strong.",
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
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        if e.protective:
            bits.append("protective=True")
        lines.append(f"  {e.id:10} ({e.type:10}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(a for a, *_ in world.fired))}")
    return "\n".join(lines)


def tell(setting: Setting, problem: Problem, hero_name: str, helper_type: str, trait: str) -> World:
    world = World(setting)
    hero = world.add(Entity(id=hero_name, kind="character", type="child"))
    helper = world.add(Entity(id="Helper", kind="character", type=helper_type, label=f"the {helper_type}"))
    obj = world.add(Entity(id="Object", type="thing", label="the seat", phrase="the seat"))
    if problem.id == "flat_cushion":
        obj.label = "the cushion"
        obj.phrase = "the cushion"
    elif problem.id == "wobbly_chair":
        obj.label = "the chair"
        obj.phrase = "the chair"
    else:
        obj.label = "the bench"
        obj.phrase = "the bench"

    introduce(world, hero)
    world.say(f"{hero.id} was {trait} and liked helping with little everyday jobs.")
    world.para()
    notice_harshness(world, hero, problem, obj)
    want_to_help(world, hero, helper, problem)
    explain(world, helper, problem, obj)
    world.para()
    fix = select_fix(problem, FIXES)
    if fix is None:
        raise StoryError("No reasonable fix exists for this problem.")
    try_bolster(world, hero, helper, problem, obj, fix)

    world.facts.update(hero=hero, helper=helper, problem=problem, object=obj, fix=fix, setting=setting)
    return world


CURATED = [
    StoryParams(place="reading_nook", problem="flat_cushion", name="Mia", helper="mother", trait="patient"),
    StoryParams(place="porch", problem="hard_seat", name="Leo", helper="grandma", trait="thoughtful"),
    StoryParams(place="kitchen", problem="wobbly_chair", name="Ava", helper="father", trait="curious"),
]


def explain_rejection(setting: Setting, problem: Problem) -> str:
    return f"(No story: this setting and problem do not produce a clear, fixable everyday scene.)"


ASP_RULES = r"""
problem_needs_fix(P, F) :- problem(P), fix(F), solves(F, P), covers(F, R), zone(P, R).
valid_story(S, P) :- setting(S), problem(P), problem_needs_fix(P, _).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid, s in SETTING_REGISTRY.items():
        lines.append(asp.fact("setting", sid))
        for a in sorted(s.affords):
            lines.append(asp.fact("affords", sid, a))
    for pid, p in PROBLEMS.items():
        lines.append(asp.fact("problem", pid))
        for z in sorted(p.zone):
            lines.append(asp.fact("zone", pid, z))
    for fx in FIXES:
        lines.append(asp.fact("fix", fx.id))
        for c in sorted(fx.covers):
            lines.append(asp.fact("covers", fx.id, c))
        for s in sorted(fx.solves):
            lines.append(asp.fact("solves", fx.id, s))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/2."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    print("  only in clingo:", sorted(cl - py))
    print("  only in python:", sorted(py - cl))
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Slice-of-life problem solving storyworld.")
    ap.add_argument("--place", choices=SETTING_REGISTRY)
    ap.add_argument("--problem", choices=PROBLEMS)
    ap.add_argument("--name")
    ap.add_argument("--helper", choices=["mother", "father", "grandma", "grandpa", "older sister", "older brother"])
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
    combos = valid_combos()
    if args.place:
        combos = [c for c in combos if c[0] == args.place]
    if args.problem:
        combos = [c for c in combos if c[1] == args.problem]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, problem = rng.choice(sorted(combos))
    name = args.name or rng.choice(NAMES)
    helper = args.helper or rng.choice(HELPERS)
    trait = args.trait or rng.choice(TRAITS)
    return StoryParams(place=place, problem=problem, name=name, helper=helper, trait=trait)


def valid_combos() -> list[tuple[str, str]]:
    combos = []
    for place, setting in SETTING_REGISTRY.items():
        for pid, problem in PROBLEMS.items():
            if place in SETTING_REGISTRY and select_fix(problem, FIXES):
                combos.append((place, pid))
    return combos


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTING_REGISTRY[params.place], PROBLEMS[params.problem], params.name, params.helper, params.trait)
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
        print(asp_program("#show valid_story/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        model = asp.one_model(asp_program("#show valid_story/2."))
        vals = sorted(set(asp.atoms(model, "valid_story")))
        print(f"{len(vals)} valid stories:")
        for v in vals:
            print(" ", v)
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
            params = resolve_params(args, random.Random(seed))
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
            header = f"### {p.name}: {p.problem} at {p.place}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()

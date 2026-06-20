#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/retort_negative_problem_solving_bravery_conflict_folk.py
=======================================================================================

A small folk-tale story world about a child who meets a conflict, gives a sharp
retort, notices the negative feeling that follows, and then solves the problem
with bravery and a clever, kind repair.

Seed words:
- retort
- negative

Theme:
- Folk Tale style
- Problem Solving
- Bravery
- Conflict

The world model keeps track of:
- a village place
- a small dispute over a useful object or task
- emotional meters for fear, pride, hurt, trust, and relief
- physical meters for damage, distance, and restored state

A complete story begins with a simple need, rises into a clash of words, turns
through a brave helpful choice, and ends with a visible change in the world.
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
SENSE_MIN = 2


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
class Setting:
    id: str
    label: str
    opening: str
    mood: str


@dataclass
class Problem:
    id: str
    noun: str
    possessive: str
    value: str
    need: str
    risk: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Retort:
    id: str
    line: str
    sting: str
    negative: str
    apology: str
    repair: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Fix:
    id: str
    verb: str
    method: str
    ending: str
    power: int
    sense: int
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
        clone = World()
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        clone.facts = copy.deepcopy(self.facts)
        return clone


@dataclass
class Rule:
    name: str
    tag: str
    apply: Callable[[World], list[str]]


def _r_negative(world: World) -> list[str]:
    out: list[str] = []
    for ent in world.entities.values():
        if ent.memes["hurt"] >= THRESHOLD and ("negative", ent.id) not in world.fired:
            world.fired.add(("negative", ent.id))
            ent.memes["trust"] -= 1
            ent.memes["shame"] += 1
            out.append("__negative__")
    return out


def _r_repair(world: World) -> list[str]:
    out: list[str] = []
    for ent in world.entities.values():
        if ent.meters["broken"] >= THRESHOLD and ("repair", ent.id) not in world.fired:
            world.fired.add(("repair", ent.id))
            ent.meters["broken"] = 0
            ent.meters["restored"] += 1
            out.append("__repair__")
    return out


CAUSAL_RULES = [Rule("negative", "social", _r_negative), Rule("repair", "physical", _r_repair)]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            items = rule.apply(world)
            if items:
                changed = True
                produced.extend(x for x in items if not x.startswith("__"))
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def sensible_fixes() -> list[Fix]:
    return [f for f in FIXES.values() if f.sense >= SENSE_MIN]


def valid_combo(problem: Problem, fix: Fix) -> bool:
    return problem.id in FIX_MAP and fix.id in FIX_MAP[problem.id]


def outcome_of(params: "StoryParams") -> str:
    fix = FIXES[params.fix]
    if params.bravery < 4:
        return "averted"
    return "solved" if fix.power >= PROBLEMS[params.problem].need_level + params.delay else "mended"


def explain_rejection(problem: Problem, fix: Fix) -> str:
    if fix.sense < SENSE_MIN:
        return f"(No story: the fix '{fix.id}' is too weak-minded for this tale. Try a wiser repair.)"
    return "(No story: this problem and fix do not belong together.)"


def explain_problem(problem_id: str) -> str:
    p = PROBLEMS[problem_id]
    return f"(No story: {p.noun} cannot be matched to the chosen folk-tale repair.)"


def story_intro(world: World, hero: Entity, elder: Entity, setting: Setting, problem: Problem) -> None:
    world.say(
        f"Once in {setting.label}, {hero.id} and {elder.id} lived under {setting.mood}. "
        f"{setting.opening}"
    )
    world.say(
        f"That day, {problem.noun} was in trouble, because {problem.need} and {problem.risk}."
    )


def spark_conflict(world: World, hero: Entity, elder: Entity, retort: Retort, problem: Problem) -> None:
    hero.memes["pride"] += 1
    elder.memes["hurt"] += 1
    world.say(
        f'{hero.id} frowned and gave a sharp retort: "{retort.line}" '
        f"The words felt bold, but the air turned negative."
    )
    world.say(
        f"{elder.id} went quiet at once. What had been a small worry grew into a stinging conflict."
    )


def show_bravery(world: World, hero: Entity, elder: Entity, problem: Problem) -> None:
    hero.memes["bravery"] += 1
    world.say(
        f"Then {hero.id} took a breath and chose bravery over the sting of the moment. "
        f"{hero.pronoun().capitalize()} looked at {elder.id} and saw that help was needed more than winning."
    )


def attempt_fix(world: World, hero: Entity, elder: Entity, problem: Problem, fix: Fix) -> None:
    world.say(
        f'{hero.id} said, "{fix.method.capitalize()}." '
        f"Together they used a simple plan: {fix.ending}."
    )
    problem_entity = world.get("problem")
    problem_entity.meters["broken"] += 1
    propagate(world, narrate=False)
    problem_entity.meters["broken"] = 0
    problem_entity.meters["restored"] += 1
    hero.memes["hurt"] = 0
    elder.memes["hurt"] = 0
    hero.memes["trust"] += 1
    elder.memes["trust"] += 1
    world.say(
        f"The fix worked, and the trouble settled down. What had seemed negative became useful again."
    )


def resolve_story(world: World, hero: Entity, elder: Entity, problem: Problem, fix: Fix) -> None:
    world.say(
        f"By the end, {problem.noun} was no longer stuck. The old trouble was mended, and the path was open again."
    )
    world.say(
        f"{elder.id} smiled at {hero.id}. \"That was a brave retort to soften,\" {elder.pronoun()} said, "
        f"\"and a better choice to solve.\""
    )
    world.say(
        f"{hero.id} stood a little taller beside the repaired thing, proud not of the sharp words, but of the kind repair."
    )


def tell(setting: Setting, problem: Problem, retort: Retort, fix: Fix, hero_name: str, hero_gender: str,
         elder_name: str, elder_gender: str, bravery: int = 5, delay: int = 0) -> World:
    world = World()
    hero = world.add(Entity(id=hero_name, kind="character", type=hero_gender, role="hero"))
    elder = world.add(Entity(id=elder_name, kind="character", type=elder_gender, role="elder"))
    p = world.add(Entity(id="problem", type="thing", label=problem.noun))
    hero.memes["bravery"] = float(bravery)
    hero.memes["trust"] = 1.0
    elder.memes["trust"] = 1.0
    world.facts.update(problem=problem, retort=retort, fix=fix, setting=setting, delay=delay)
    story_intro(world, hero, elder, setting, problem)
    world.para()
    spark_conflict(world, hero, elder, retort, problem)
    if hero.memes["bravery"] < 4:
        world.say(
            f"After the clash, {hero.id} felt negative and small for a moment, then saw the trouble still waiting."
        )
        world.para()
        show_bravery(world, hero, elder, problem)
        attempt_fix(world, hero, elder, problem, fix)
        world.para()
        resolve_story(world, hero, elder, problem, fix)
        outcome = "mended"
    else:
        world.para()
        show_bravery(world, hero, elder, problem)
        attempt_fix(world, hero, elder, problem, fix)
        world.para()
        resolve_story(world, hero, elder, problem, fix)
        outcome = "solved"
    world.facts.update(hero=hero, elder=elder, outcome=outcome)
    return world


SETTINGS = {
    "village": Setting("village", "a little village", "The cottages leaned close, and the hearth smoke rose in soft ribbons.", "quiet folk-tale weather"),
    "wood": Setting("wood", "the green wood", "The trees stood like old listeners, and the moss held the morning cool.", "forest hush"),
    "hill": Setting("hill", "the high hill", "The wind ran over the grass, and even the stones seemed to know old songs.", "bright hill wind"),
}

PROBLEMS = {
    "gate": Problem("gate", "the gate", "its", "stuck shut", "The village cart needed to pass", "and the apples were piling up outside", tags={"gate", "stuck"}),
    "well": Problem("well", "the well rope", "its", "frayed and loose", "The bucket needed to be lowered for water", "and the water jar was empty", tags={"well", "rope"}),
    "bridge": Problem("bridge", "the bridge board", "its", "wobbly", "The sheep needed to cross", "and one step could send it creaking", tags={"bridge", "board"}),
}

RETORTS = {
    "sharp": Retort("sharp", "You never listen!", "sharp", "negative", "I'm sorry; that was harsh.", "helping with the task", tags={"retort", "negative"}),
    "proud": Retort("proud", "I can do it myself!", "proud", "negative", "I'm sorry; I should have asked.", "trying together", tags={"retort", "bravery"}),
    "stubborn": Retort("stubborn", "Your way is slower!", "stubborn", "negative", "I'm sorry; I spoke too fast.", "finding a better plan", tags={"retort", "conflict"}),
}

FIXES = {
    "rope": Fix("rope", "tie a new rope", "they tied a fresh rope and tested it twice", "the rope held, steady and true", 4, 3, tags={"rope", "problem_solving"}),
    "wedge": Fix("wedge", "set a wooden wedge", "they slipped in a stout wedge and pushed the board flat", "the board stopped wobbling", 3, 3, tags={"wedge", "problem_solving"}),
    "oil": Fix("oil", "oil the hinges", "they oiled the hinges and worked the gate back and forth", "the gate swung open at last", 4, 2, tags={"oil", "problem_solving"}),
}

FIX_MAP = {
    "gate": {"oil"},
    "well": {"rope"},
    "bridge": {"wedge"},
}

GIRL_NAMES = ["Mira", "Hana", "Nia", "Tala", "Lena"]
BOY_NAMES = ["Bram", "Joss", "Finn", "Pavel", "Oren"]
ELDER_NAMES = ["Grandmother", "Grandfather", "Aunt", "Uncle"]


@dataclass
class StoryParams:
    setting: str
    problem: str
    retort: str
    fix: str
    hero_name: str
    hero_gender: str
    elder_name: str
    elder_gender: str
    bravery: int = 5
    delay: int = 0
    seed: Optional[int] = None


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for sid, problem in PROBLEMS.items():
        for rid, fix in FIXES.items():
            if valid_combo(problem, fix):
                combos.append((sid, rid, fix.id))
    return combos


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    p = f["problem"]
    r = f["retort"]
    fx = f["fix"]
    return [
        f'Write a short folk tale that uses the words "{r.sting}" and "{r.negative}" and ends with a problem being fixed.',
        f"Tell a village story where {f['hero'].id} makes a sharp retort, feels negative after the conflict, and then solves {p.noun}.",
        f'Write a brave folk-tale story for a small child, with a conflict, a retort, and a clever repair using "{fx.method}".',
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    hero, elder = f["hero"], f["elder"]
    problem, retort, fix = f["problem"], f["retort"], f["fix"]
    return [
        ("Who was the story about?",
         f"It was about {hero.id} and {elder.id}, who faced a small village problem together."),
        ("What did {0} say in the conflict?".format(hero.id),
         f"{hero.id} gave a retort: \"{retort.line}\". The words were sharp and made the moment feel negative."),
        ("How was the problem solved?",
         f"They used {fix.method} and made a careful repair. That was the brave, sensible answer to the conflict."),
        ("How did the story end?",
         f"It ended with {problem.noun} fixed and the tension gone. The scene changed from negative words to a useful solution."),
    ]


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags = set(f["problem"].tags) | set(f["retort"].tags) | set(f["fix"].tags)
    qa = []
    if "retort" in tags:
        qa.append(("What is a retort?",
                    "A retort is a quick reply, often sharp or clever. People can use a retort when they are upset or trying to answer back."))
    if "negative" in tags:
        qa.append(("What does negative mean?",
                    "Negative means something that feels bad, unhelpful, or opposite of hopeful. It can describe a mood, a feeling, or a reply."))
    if "problem_solving" in tags:
        qa.append(("What is problem solving?",
                    "Problem solving means looking at a trouble, thinking of a plan, and choosing a way to fix it."))
    if "bravery" in tags:
        qa.append(("What is bravery?",
                    "Bravery is being willing to do the right thing even when you feel nervous or worried."))
    if "conflict" in tags:
        qa.append(("What is conflict?",
                    "Conflict is when people disagree or are upset with each other. It can be solved by listening and making a better choice."))
    return qa


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
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    return "\n".join(lines)


CURATED = [
    StoryParams("village", "gate", "sharp", "oil", "Mira", "girl", "Grandmother", "woman", bravery=5),
    StoryParams("wood", "well", "proud", "rope", "Bram", "boy", "Grandfather", "man", bravery=6),
    StoryParams("hill", "bridge", "stubborn", "wedge", "Tala", "girl", "Aunt", "woman", bravery=4),
]


def explain_response(rid: str) -> str:
    r = RETORTS[rid]
    return f"(Refusing retort '{rid}': it scores too low on common sense (sense={SENSE_MIN-1} < {SENSE_MIN}).)"


def asp_facts() -> str:
    import asp
    lines = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for pid in PROBLEMS:
        lines.append(asp.fact("problem", pid))
    for rid, r in RETORTS.items():
        lines.append(asp.fact("retort", rid))
        lines.append(asp.fact("negative", rid))
    for fid, f in FIXES.items():
        lines.append(asp.fact("fix", fid))
        lines.append(asp.fact("sense", fid, f.sense))
        lines.append(asp.fact("power", fid, f.power))
    lines.append(asp.fact("sense_min", SENSE_MIN))
    return "\n".join(lines)


ASP_RULES = r"""
valid(S, R, F) :- setting(S), retort(R), fix(F), sense(F, X), sense_min(M), X >= M.
"""


def asp_program(extra: str = "", show: str = "") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    rc = 0
    if set(asp_valid_combos()) == set(valid_combos()):
        print(f"OK: ASP matches valid_combos() ({len(valid_combos())} combos).")
    else:
        rc = 1
        print("MISMATCH in ASP parity.")
    try:
        sample = generate(CURATED[0])
        if not sample.story.strip():
            raise RuntimeError("empty story")
        print("OK: generate/emit smoke test passed.")
    except Exception as exc:
        rc = 1
        print(f"SMOKE TEST FAILED: {exc}")
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A folk-tale story world about retorts, negative feelings, bravery, and problem solving.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--problem", choices=PROBLEMS)
    ap.add_argument("--retort", choices=RETORTS)
    ap.add_argument("--fix", choices=FIXES)
    ap.add_argument("--hero-name")
    ap.add_argument("--hero-gender", choices=["girl", "boy"])
    ap.add_argument("--elder-name")
    ap.add_argument("--elder-gender", choices=["woman", "man"])
    ap.add_argument("--bravery", type=int)
    ap.add_argument("--delay", type=int, choices=[0, 1, 2], default=0)
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
    setting = args.setting or rng.choice(list(SETTINGS))
    problem = args.problem or rng.choice(list(PROBLEMS))
    fix = args.fix or rng.choice(list(FIXES))
    if args.fix and args.fix not in FIXES:
        raise StoryError("Unknown fix.")
    if args.fix and args.problem:
        if not valid_combo(PROBLEMS[args.problem], FIXES[args.fix]):
            raise StoryError(explain_problem(args.problem))
    if args.retort and args.retort not in RETORTS:
        raise StoryError("Unknown retort.")
    retort = args.retort or rng.choice(list(RETORTS))
    hero_gender = args.hero_gender or rng.choice(["girl", "boy"])
    hero_name = args.hero_name or rng.choice(GIRL_NAMES if hero_gender == "girl" else BOY_NAMES)
    elder_gender = args.elder_gender or rng.choice(["woman", "man"])
    elder_name = args.elder_name or rng.choice(ELDER_NAMES)
    bravery = args.bravery if args.bravery is not None else rng.randint(3, 7)
    if RETORTS[retort].id == "sharp" and bravery < 4:
        bravery = 4
    return StoryParams(setting, problem, retort, fix, hero_name, hero_gender, elder_name, elder_gender, bravery, args.delay)


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.setting], PROBLEMS[params.problem], RETORTS[params.retort], FIXES[params.fix],
                 params.hero_name, params.hero_gender, params.elder_name, params.elder_gender, params.bravery, params.delay)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=[QAItem(q, a) for q, a in story_qa(world)],
        world_qa=[QAItem(q, a) for q, a in world_knowledge_qa(world)],
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
        print(asp_program(show="#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"{len(asp_valid_combos())} compatible combos:")
        for row in asp_valid_combos():
            print(" ", row)
        return
    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
            seed = base_seed + i
            i += 1
            try:
                p = resolve_params(args, random.Random(seed))
            except StoryError as err:
                print(err)
                return
            p.seed = seed
            s = generate(p)
            if s.story in seen:
                continue
            seen.add(s.story)
            samples.append(s)
    if args.json:
        print(samples[0].to_json() if len(samples) == 1 else json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return
    for i, sample in enumerate(samples):
        emit(sample, trace=args.trace, qa=args.qa, header=(f"### variant {i+1}" if len(samples) > 1 else ""))
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()

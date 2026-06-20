#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/alcohol_pajama_dialogue_problem_solving_tall_tale.py
====================================================================================

A standalone storyworld for a tall-tale style problem-solving story:
a child in pajamas goes on a ridiculous, dialogue-driven errand involving
alcohol (the cleaning kind) and solves a practical problem with a clever plan.

The domain is intentionally small:
- a child wants to help with a tall-tale-sized mess
- an adult warns about using alcohol safely
- the child and adult talk, inspect the problem, and choose a sensible fix
- the ending proves what changed with a concrete final image

This script follows the storyworld contract:
- stdlib only
- StoryParams, build_parser, resolve_params, generate, emit, main
- StoryError on invalid combinations
- QA generated from world state, not by parsing rendered prose
- inline ASP twin and Python reasonableness gate
- --verify checks parity and performs a smoke test
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

    tags: set[str] = field(default_factory=set)

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



    @property
    def phrase(self) -> str:
        return getattr(self, "_phrase", None) or self.label or self.id.replace("_", " ")

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)
@dataclass
class Item:
    id: str
    label: str
    phrase: str
    effect: str
    risk: str
    tags: set[str] = field(default_factory=set)

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = defaultdict(float)
            object.__setattr__(self, name, value)
            return value
        if name == "tags":
            value = set()
            object.__setattr__(self, name, value)
            return value
        if name in {"phrase", "label_word"}:
            return (getattr(self, "label", "") or getattr(self, "name", "") or getattr(self, "id", self.__class__.__name__.lower())).replace("_", " ")
        if name == "pronoun":
            return lambda case="subject": {"subject": "they", "object": "them", "possessive": "their"}[case]
        raise AttributeError(f"{self.__class__.__name__!r} object has no attribute {name!r}")


@dataclass
class Problem:
    id: str
    label: str
    scene: str
    size: str
    clue: str
    consequence: str
    tags: set[str] = field(default_factory=set)

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = defaultdict(float)
            object.__setattr__(self, name, value)
            return value
        if name == "tags":
            value = set()
            object.__setattr__(self, name, value)
            return value
        if name in {"phrase", "label_word"}:
            return (getattr(self, "label", "") or getattr(self, "name", "") or getattr(self, "id", self.__class__.__name__.lower())).replace("_", " ")
        if name == "pronoun":
            return lambda case="subject": {"subject": "they", "object": "them", "possessive": "their"}[case]
        raise AttributeError(f"{self.__class__.__name__!r} object has no attribute {name!r}")


@dataclass
class Fix:
    id: str
    label: str
    phrase: str
    method: str
    power: int
    sense: int
    tags: set[str] = field(default_factory=set)

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = defaultdict(float)
            object.__setattr__(self, name, value)
            return value
        if name == "tags":
            value = set()
            object.__setattr__(self, name, value)
            return value
        if name in {"phrase", "label_word"}:
            return (getattr(self, "label", "") or getattr(self, "name", "") or getattr(self, "id", self.__class__.__name__.lower())).replace("_", " ")
        if name == "pronoun":
            return lambda case="subject": {"subject": "they", "object": "them", "possessive": "their"}[case]
        raise AttributeError(f"{self.__class__.__name__!r} object has no attribute {name!r}")


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
        if eid not in self.entities:
            label = str(eid).replace("_", " ")
            self.entities[eid] = Entity(str(eid), label=label)
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
        w.entities = copy.deepcopy(self.entities)
        w.fired = set(self.fired)
        w.paragraphs = [[]]
        return w


@dataclass
class Rule:
    name: str
    apply: Callable[[World], list[str]]

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = defaultdict(float)
            object.__setattr__(self, name, value)
            return value
        if name == "tags":
            value = set()
            object.__setattr__(self, name, value)
            return value
        if name in {"phrase", "label_word"}:
            return (getattr(self, "label", "") or getattr(self, "name", "") or getattr(self, "id", self.__class__.__name__.lower())).replace("_", " ")
        if name == "pronoun":
            return lambda case="subject": {"subject": "they", "object": "them", "possessive": "their"}[case]
        raise AttributeError(f"{self.__class__.__name__!r} object has no attribute {name!r}")


def _r_smear(world: World) -> list[str]:
    out: list[str] = []
    for ent in list(world.entities.values()):
        if ent.meters["alcohol_spill"] < THRESHOLD:
            continue
        sig = ("smear", ent.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        if "floor" in world.entities:
            world.get("floor").meters["slick"] += 1
        for kid in [e for e in list(world.entities.values()) if e.role == "child"]:
            kid.memes["worry"] += 1
        out.append("__spill__")
    return out


CAUSAL_RULES = [Rule("smear", _r_smear)]


def propagate(world: World, narrate: bool = True) -> None:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            s = rule.apply(world)
            if s:
                changed = True
                produced.extend(x for x in s if not x.startswith("__"))
    if narrate:
        for line in produced:
            world.say(line)


def problem_risky(problem: Problem) -> bool:
    return problem.id in {"stain", "sticky_patch", "sleepy_spill"}


def fix_works(fix: Fix, problem: Problem) -> bool:
    return fix.power >= {"stain": 2, "sticky_patch": 3, "sleepy_spill": 2}[problem.id]


def sensible_fixes() -> list[Fix]:
    return [f for f in FIXES.values() if f.sense >= SENSE_MIN]


def reason_ok(item: Item, problem: Problem) -> bool:
    return problem_risky(problem) and "clean" in item.tags


def _clean_problem(world: World, item: Item, problem: Problem, narrate: bool = True) -> None:
    target = world.get("target")
    target.meters["fixed"] += 1
    target.meters["mess"] = 0
    world.get("floor").meters["slick"] = 0
    world.say(
        f"The grown-up tipped the {item.label} carefully, and the {problem.label} loosened right up."
    )
    if narrate:
        propagate(world, narrate=True)


def predict(world: World, item: Item, problem: Problem) -> dict:
    sim = world.copy()
    _clean_problem(sim, item, problem, narrate=False)
    return {"fixed": sim.get("target").meters["fixed"] >= THRESHOLD}


def setup(world: World, child: Entity, adult: Entity, item: Item, problem: Problem) -> None:
    child.memes["curiosity"] += 1
    child.memes["hope"] += 1
    world.say(
        f"On a windy morning, {child.id} bounced through the room in pajamas so striped they looked stitched from sunset and moonbeam."
    )
    world.say(
        f"{child.id} found a {problem.label} so big it might have needed its own post office."
    )
    world.say(
        f'"{adult.label_word.capitalize()}!" {child.id} called. "Can I use the {item.label}?"'
    )


def warn(world: World, adult: Entity, child: Entity, item: Item, problem: Problem) -> None:
    adult.memes["care"] += 1
    world.say(
        f'"Not unless we use it the right way," {adult.id} said. "{item.label.capitalize()} is for careful cleaning, not for play."'
    )
    world.say(
        f'"This {problem.label} is {problem.consequence}," {adult.id} added, "but I can help you fix it."'
    )


def think(world: World, child: Entity, problem: Problem) -> None:
    child.memes["thinking"] += 1
    world.say(
        f"{child.id} scratched {child.pronoun('possessive')} head, peered at the mess, and said, "
        f'"What if we move the heavy things first and use a little of the alcohol on the cloth?"'
    )


def agree(world: World, adult: Entity, child: Entity, item: Item, fix: Fix) -> None:
    child.memes["joy"] += 1
    world.say(
        f'"That is the right kind of idea," {adult.id} said. "We will open the window, wet the cloth a little, and wipe from the outside in."'
    )
    world.say(
        f"{child.id} nodded so hard {child.id}'s pajamas nearly flapped like flags in a storm."
    )
    world.say(
        f"Together they used {fix.phrase}, and the {problem.label} faded fast."
    )


def ending(world: World, child: Entity, adult: Entity, problem: Problem) -> None:
    world.say(
        f"Before long, the room smelled only faintly of soap and fresh air."
    )
    world.say(
        f"{child.id} stood in {child.pronoun('possessive')} pajamas beside a clean floor and grinned up at {adult.id}."
    )
    world.say(
        f'"Next time," {child.id} said, "I will ask first."'
    )
    world.say(
        f'"That is the bravest trick of all," {adult.id} replied, and the two of them laughed like thunder rolling politely away.'
    )


def fail_ending(world: World, child: Entity, adult: Entity, item: Item, problem: Problem) -> None:
    world.say(
        f"The wrong plan would have made the {problem.label} worse, so {adult.id} stopped it at once."
    )
    world.say(
        f"They put the {item.label} away, chose a safer fix, and the room came right again."
    )


ITEMS = {
    "alcohol": Item("alcohol", "alcohol", "a small bottle of alcohol", "cleaning", "unsafe", {"alcohol", "clean"}),
    "spray": Item("spray", "spray bottle", "a spray bottle", "mist", "unsafe", {"clean"}),
    "cloth": Item("cloth", "cloth", "a soft cloth", "wipe", "safe", {"clean"}),
}

PROBLEMS = {
    "stain": Problem("stain", "stain", "the stain", "big", "a deep brown trail on the table", "it clings like a stubborn barnacle", {"stain"}),
    "sticky_patch": Problem("sticky_patch", "sticky patch", "the sticky patch", "sticky", "a syrupy puddle on the floor", "it sticks to every step", {"sticky"}),
    "sleepy_spill": Problem("sleepy_spill", "sleepy spill", "the sleepy spill", "sprawled", "a sleepy spill on the counter", "it sits there like a lazy puddle", {"spill"}),
}

FIXES = {
    "cloth_wipe": Fix("cloth_wipe", "cloth wipe", "a damp cloth", "wipe gently", 2, 3, {"cloth"}),
    "spray_and_wipe": Fix("spray_and_wipe", "spray and wipe", "the spray bottle and a cloth", "spray a little and wipe", 3, 2, {"clean"}),
    "window_plus_wipe": Fix("window_plus_wipe", "window and wipe", "the open window and a cloth", "air it out and wipe", 2, 2, {"clean"}),
}

CHILD_NAMES = ["Milo", "Ivy", "Nell", "Otto", "Ruby", "June", "Toby", "Piper"]
ADULT_NAMES = ["Aunt June", "Uncle Ray", "Mom", "Dad"]


@dataclass
@dataclass
class StoryParams:
    item: str
    problem: str
    fix: str
    child_name: str
    child_gender: str
    adult_name: str
    seed: Optional[int] = None

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = defaultdict(float)
            object.__setattr__(self, name, value)
            return value
        if name == "tags":
            value = set()
            object.__setattr__(self, name, value)
            return value
        if name in {"phrase", "label_word"}:
            return (getattr(self, "label", "") or getattr(self, "name", "") or getattr(self, "id", self.__class__.__name__.lower())).replace("_", " ")
        if name == "pronoun":
            return lambda case="subject": {"subject": "they", "object": "them", "possessive": "their"}[case]
        raise AttributeError(f"{self.__class__.__name__!r} object has no attribute {name!r}")


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for iid, item in ITEMS.items():
        for pid, problem in PROBLEMS.items():
            if reason_ok(item, problem):
                for fid, fix in FIXES.items():
                    if fix_works(fix, problem):
                        combos.append((iid, pid, fid))
    return combos


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Tall-tale dialogue and problem-solving storyworld.")
    ap.add_argument("--item", choices=ITEMS)
    ap.add_argument("--problem", choices=PROBLEMS)
    ap.add_argument("--fix", choices=FIXES)
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--adult")
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
    if args.item and args.problem and not reason_ok(ITEMS[args.item], PROBLEMS[args.problem]):
        raise StoryError("No story: that item is for careful cleaning, but that problem is not the right kind of mess.")
    if args.fix and args.problem and not fix_works(FIXES[args.fix], PROBLEMS[args.problem]):
        raise StoryError("No story: that fix would be too weak for that problem.")
    combos = [c for c in valid_combos()
              if (args.item is None or c[0] == args.item)
              and (args.problem is None or c[1] == args.problem)
              and (args.fix is None or c[2] == args.fix)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    item, problem, fix = rng.choice(sorted(combos))
    gender = args.gender or rng.choice(["girl", "boy"])
    child_name = args.name or rng.choice(CHILD_NAMES)
    adult_name = args.adult or rng.choice(ADULT_NAMES)
    return StoryParams(item, problem, fix, child_name, gender, adult_name)


def tell(params: StoryParams) -> World:
    world = World()
    child = world.add(Entity(params.child_name, "character", params.child_gender, role="child", traits=["bold"]))
    adult = world.add(Entity(params.adult_name, "character", "adult", role="adult", traits=["careful"]))
    floor = world.add(Entity("floor", "thing", "floor", label="the floor"))
    item = ITEMS[params.item]
    problem = PROBLEMS[params.problem]
    fix = FIXES[params.fix]
    world.add(Entity("target", "thing", problem.id, label=problem.label))

    setup(world, child, adult, item, problem)
    world.para()
    warn(world, adult, child, item, problem)
    think(world, child, problem)
    world.para()
    if predict(world, item, problem)["fixed"]:
        agree(world, adult, child, item, fix)
        _clean_problem(world, item, problem)
        ending(world, child, adult, problem)
    else:
        fail_ending(world, child, adult, item, problem)
        _clean_problem(world, item, problem)

    world.facts.update(child=child, adult=adult, item=item, problem=problem, fix=fix, floor=floor)
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a tall-tale style story for a child in pajamas where "{f["item"].label}" helps solve "{f["problem"].label}".',
        f"Tell a dialogue-driven problem-solving story where {f['child'].id} asks about alcohol and the grown-up explains a careful cleaning plan.",
        f'Write a funny, exaggerated story that includes the word "alcohol" and ends with {f["child"].id} learning to ask first.',
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    child, adult, item, problem = f["child"], f["adult"], f["item"], f["problem"]
    return [
        ("Who is the story about?",
         f"It is about {child.id}, who is wandering around in pajamas, and {adult.id}, who helps with the problem."),
        ("What did {0} want to use?".format(child.id),
         f"{child.id} wanted to use {item.label} to help with the {problem.label}."),
        ("How was the problem solved?",
         f"They used a careful cleaning plan: first they talked, then they chose the right amount of alcohol, and then they wiped the mess away."),
        ("What changed by the end?",
         f"The mess was gone, the room smelled fresh, and {child.id} had learned to ask before using the cleaning supplies."),
    ]


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    return [
        ("What is alcohol used for in cleaning?",
         "Cleaning alcohol can help loosen grime and wipe away sticky messes when a grown-up uses it carefully."),
        ("Why wear pajamas at night?",
         "Pajamas are soft clothes people wear for sleep and for cozy lounging around the house."),
        ("Why should children ask before using cleaning liquids?",
         "Some cleaning liquids can be unsafe or need careful handling, so a grown-up should choose how to use them."),
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
    lines.append("== (3) World knowledge ==")
    for q in sample.world_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in list(world.entities.values()):
        m = {k: v for k, v in e.meters.items() if v}
        mm = {k: v for k, v in e.memes.items() if v}
        bits = []
        if m:
            bits.append(f"meters={dict(m)}")
        if mm:
            bits.append(f"memes={dict(mm)}")
        if e.role:
            bits.append(f"role={e.role}")
        lines.append(f"  {e.id:10} ({e.type:7}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted({n for n, *_ in world.fired})}")
    return "\n".join(lines)


CURATED = [
    StoryParams("alcohol", "stain", "cloth_wipe", "Mina", "girl", "Mom"),
    StoryParams("spray", "sticky_patch", "spray_and_wipe", "Jo", "boy", "Aunt June"),
    StoryParams("alcohol", "sleepy_spill", "window_plus_wipe", "Pia", "girl", "Dad"),
]


def explain_response(fid: str) -> str:
    return f"(Refusing fix '{fid}': it is too weak or not sensible enough for the story.)"


ASP_RULES = r"""
reason_ok(I,P) :- item(I), problem(P), risky(P), clean_item(I).
valid(I,P,F) :- reason_ok(I,P), fix(F), strong_enough(F,P).
outcome(solved) :- chosen(I,P,F), valid(I,P,F).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for iid, i in ITEMS.items():
        lines.append(asp.fact("item", iid))
        if "clean" in i.tags:
            lines.append(asp.fact("clean_item", iid))
    for pid, p in PROBLEMS.items():
        lines.append(asp.fact("problem", pid))
        lines.append(asp.fact("risky", pid))
    for fid, f in FIXES.items():
        lines.append(asp.fact("fix", fid))
        lines.append(asp.fact("strong_enough", fid, "stain" if f.power >= 2 else "sticky_patch"))
        if f.power >= 3:
            lines.append(asp.fact("strong_enough", fid, "sticky_patch"))
            lines.append(asp.fact("strong_enough", fid, "sleepy_spill"))
    return "\n".join(lines)


def asp_program(extra: str = "", show: str = "") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    import asp
    rc = 0
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: gate matches valid_combos() ({len(py)} combos).")
    else:
        rc = 1
        print("MISMATCH in gate.")
    try:
        sample = generate(resolve_params(argparse.Namespace(item=None, problem=None, fix=None, name=None, gender=None, adult=None), random.Random(7)))
        _ = sample.story
        print("OK: generate smoke test passed.")
    except Exception as e:
        raise SystemExit(f"VERIFY FAILED: {e}")
    return rc


def generate(params: StoryParams) -> StorySample:
    world = tell(params)
    return StorySample(params=params, story=world.render(), prompts=generation_prompts(world), story_qa=[QAItem(q, a) for q, a in story_qa(world)], world_qa=[QAItem(q, a) for q, a in world_knowledge_qa(world)], world=world)


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
        print(f"{len(asp_valid_combos())} compatible combos:")
        for combo in asp_valid_combos():
            print(" ", combo)
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
        emit(sample, trace=args.trace, qa=args.qa, header=(f"### variant {i+1}" if len(samples) > 1 else ""))
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()

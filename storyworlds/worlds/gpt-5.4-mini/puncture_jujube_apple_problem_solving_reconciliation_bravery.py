#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/puncture_jujube_apple_problem_solving_reconciliation_bravery.py
================================================================================================

A small standalone story world about a mysterious puncture, a jujube candy clue,
and a rescued apple basket.  The domain is intentionally tiny and classical: a
child notices something wrong, follows clues, solves the problem with tools and
care, apologizes after a misunderstanding, and ends with a brave, repaired,
peaceful image.

Style notes:
- Mystery-leaning atmosphere, but child-facing and concrete.
- State-driven prose: the story changes because meters/memes change.
- Includes the seed words: puncture, jujube, apple.
- Features emphasized: Problem Solving, Reconciliation, Bravery.
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

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
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
class Setting:
    id: str
    place: str
    mood: str
    clue_place: str

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = __import__("collections").defaultdict(float)
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
    puncture_source: str
    clue: str
    risk_text: str
    method_text: str
    followup: str
    tags: set[str] = field(default_factory=set)

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = __import__("collections").defaultdict(float)
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
    tool: str
    action: str
    success_text: str
    fail_text: str
    tags: set[str] = field(default_factory=set)

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = __import__("collections").defaultdict(float)
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
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
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
        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        return clone


@dataclass
class Rule:
    name: str
    tag: str
    apply: Callable[[World], list[str]]

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = __import__("collections").defaultdict(float)
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


def _r_worry(world: World) -> list[str]:
    out: list[str] = []
    for e in list(world.entities.values()):
        if e.meters["punctured"] < THRESHOLD:
            continue
        sig = ("worry", e.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        for k in list(world.entities.values()):
            if k.role in {"child", "helper"}:
                k.memes["worry"] += 1
        out.append("__worry__")
    return out


def _r_bravery(world: World) -> list[str]:
    out: list[str] = []
    if any(e.meters["punctured"] >= THRESHOLD for e in list(world.entities.values())):
        for e in list(world.entities.values()):
            if e.role == "child":
                sig = ("brave", e.id)
                if sig in world.fired:
                    continue
                world.fired.add(sig)
                e.memes["bravery"] += 1
                out.append("__brave__")
    return out


CAUSAL_RULES = [Rule("worry", "social", _r_worry), Rule("bravery", "social", _r_bravery)]


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


def predict_problem(world: World, problem: Problem) -> dict:
    sim = world.copy()
    _cause_puncture(sim, sim.get("basket"), problem, narrate=False)
    return {
        "punctured": sim.get("basket").meters["punctured"] >= THRESHOLD,
        "found_clue": sim.get("child").memes["curiosity"] >= THRESHOLD,
    }


def _cause_puncture(world: World, basket: Entity, problem: Problem, narrate: bool = True) -> None:
    basket.meters["punctured"] += 1
    basket.meters["leaking"] += 1
    propagate(world, narrate=narrate)


def arrive(world: World, child: Entity, helper: Entity) -> None:
    child.memes["curiosity"] += 1
    world.say(
        f"On a quiet afternoon in {world.setting.place}, {child.id} and {helper.id} "
        f"noticed a strange problem near the {world.setting.clue_place}. The air "
        f"felt still, as if it was holding a secret."
    )


def discover_clue(world: World, child: Entity, problem: Problem) -> None:
    world.say(
        f"{child.id} crouched down and spotted something small: a {problem.clue}."
        f" It looked like a clue, but it also looked like a mess."
    )


def explain_risk(world: World, helper: Entity, problem: Problem) -> None:
    helper.memes["care"] += 1
    world.say(
        f'"{problem.risk_text}," {helper.id} said softly. "{problem.method_text}."'
    )


def brave_try(world: World, child: Entity, problem: Problem) -> None:
    child.memes["bravery"] += 1
    world.say(
        f"{child.id} took a deep breath and looked closer. Brave eyes caught a tiny "
        f"trail near the apple basket, and that made the mystery feel solvable."
    )


def solve(world: World, helper: Entity, fix: Fix, basket: Entity) -> None:
    basket.meters["punctured"] = 0.0
    basket.meters["leaking"] = 0.0
    helper.memes["relief"] += 1
    world.say(
        f"At last, {helper.id} used {fix.tool} and {fix.action}. {fix.success_text}."
    )
    world.say(
        "The basket stopped leaking, and the little mystery finally made sense."
    )


def misunderstanding(world: World, child: Entity, helper: Entity) -> None:
    child.memes["hurt"] += 1
    world.say(
        f"For a moment, {child.id} thought {helper.id} was upset about the mess. "
        f"But {helper.id} knelt down, listened, and made room for an apology."
    )


def reconcile(world: World, child: Entity, helper: Entity, problem: Problem) -> None:
    child.memes["relief"] += 1
    helper.memes["relief"] += 1
    child.memes["love"] += 1
    helper.memes["love"] += 1
    world.say(
        f'{child.id} said, "I\'m sorry I rushed." {helper.id} smiled and said, '
        f'"Thank you for telling me. You were brave enough to help."'
    )
    world.say(
        f'Together they fixed the {problem.id} and promised to watch for clues '
        f"before panic ever got a chance to grow."
    )


def ending(world: World, child: Entity, helper: Entity) -> None:
    world.say(
        f"By evening, the {world.setting.place} was calm again. {child.id} and "
        f"{helper.id} sat beside the apple basket, sharing jujube candies and a "
        f"quiet grin, proud of the mystery they had solved together."
    )


SETTING_REGISTRY = {
    "market": Setting("market", "small market", "busy and bright", "apple stall"),
    "orchard": Setting("orchard", "apple orchard", "leafy and hushed", "wooden crate"),
    "kitchen": Setting("kitchen", "sunny kitchen", "warm and tidy", "counter"),
}

PROBLEMS = {
    "basket": Problem(
        "basket",
        "apple basket",
        "a tiny thorn",
        "jujube crumbs by the basket",
        "The basket might spill apples if it has a puncture",
        "A puncture can make the basket leak and wobble",
        "They needed to find the hole before more apples rolled away",
        tags={"puncture", "apple", "jujube"},
    ),
    "bag": Problem(
        "bag",
        "paper bag",
        "a sharp twig",
        "jujube wrappers in a corner",
        "The bag might tear open if it has a puncture",
        "A puncture can make the bag weak and droopy",
        "They needed to find the tear before the apples dropped",
        tags={"puncture", "apple", "jujube"},
    ),
}

FIXES = {
    "patch": Fix(
        "patch",
        "a sticker patch and a cloth strip",
        "pressed the patch over the puncture and tied it snugly",
        "It held, and the basket became steady again",
        "It slipped off, and the leak kept going",
        tags={"problem_solving"},
    ),
    "replace": Fix(
        "replace",
        "a stronger basket",
        "moved the apples into a safe basket",
        "The apples stopped rolling, and the mystery was solved",
        "The new basket was too small, and nothing fit",
        tags={"problem_solving"},
    ),
}

CHILD_NAMES = ["Mina", "Noah", "Lila", "Theo", "Rosa", "Eli"]


@dataclass
@dataclass
class StoryParams:
    setting: str
    problem: str
    fix: str
    child: str
    child_gender: str
    helper: str
    helper_gender: str
    seed: Optional[int] = None

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = __import__("collections").defaultdict(float)
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
    for s in SETTING_REGISTRY:
        for p in PROBLEMS:
            for f in FIXES:
                combos.append((s, p, f))
    return combos


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Mystery story world about puncture, jujube, and apple.")
    ap.add_argument("--setting", choices=SETTING_REGISTRY)
    ap.add_argument("--problem", choices=PROBLEMS)
    ap.add_argument("--fix", choices=FIXES)
    ap.add_argument("--child")
    ap.add_argument("--child-gender", choices=["girl", "boy"])
    ap.add_argument("--helper")
    ap.add_argument("--helper-gender", choices=["girl", "boy"])
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
    combos = [c for c in valid_combos()
              if (args.setting is None or c[0] == args.setting)
              and (args.problem is None or c[1] == args.problem)
              and (args.fix is None or c[2] == args.fix)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    setting, problem, fix = rng.choice(sorted(combos))
    child_gender = args.child_gender or rng.choice(["girl", "boy"])
    helper_gender = args.helper_gender or ("boy" if child_gender == "girl" else "girl")
    child = args.child or rng.choice(CHILD_NAMES)
    helper = args.helper or rng.choice([n for n in CHILD_NAMES if n != child])
    return StoryParams(setting, problem, fix, child, child_gender, helper, helper_gender)


def tell(params: StoryParams) -> World:
    world = World(SETTING_REGISTRY[params.setting])
    child = world.add(Entity(params.child, kind="character", type=params.child_gender, role="child"))
    helper = world.add(Entity(params.helper, kind="character", type=params.helper_gender, role="helper"))
    basket = world.add(Entity("basket", kind="thing", type="basket", label="apple basket"))
    problem = PROBLEMS[params.problem]
    fix = FIXES[params.fix]

    arrive(world, child, helper)
    world.para()
    discover_clue(world, child, problem)
    explain_risk(world, helper, problem)
    brave_try(world, child, problem)
    _cause_puncture(world, basket, problem)
    misunderstanding(world, child, helper)
    world.para()
    solve(world, helper, fix, basket)
    reconcile(world, child, helper, problem)
    world.para()
    ending(world, child, helper)

    world.facts.update(
        child=child, helper=helper, basket=basket, problem=problem, fix=fix,
        setting=world.setting, outcome="solved"
    )
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a short mystery story for a 3-to-5-year-old that includes the words "puncture", "jujube", and "apple".',
        f"Tell a child-facing story where {f['child'].id} notices a puncture near an apple basket, follows a jujube clue, and solves it bravely with {f['helper'].id}.",
        f"Write a gentle mystery about a small puncture, a sweet jujube clue, and an apple basket, ending in apology and reconciliation.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    child = f["child"]
    helper = f["helper"]
    problem = f["problem"]
    fix = f["fix"]
    return [
        (f"What problem did {child.id} notice?",
         f"{child.id} noticed a puncture near the {problem.label}. That hole made the basket leak and wobble."),
        (f"What clue helped them solve the mystery?",
         f"They found jujube crumbs and followed the little trail. The clue pointed them back to the apple basket."),
        (f"How did they fix the problem?",
         f"They used {fix.tool} and {fix.action}. That careful step stopped the puncture and made the basket steady again."),
        (f"How did the story end?",
         f"It ended with apology, reconciliation, and brave teamwork. {child.id} and {helper.id} shared jujube candies beside the apple basket after solving the mystery."),
    ]


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    return [
        ("What is a puncture?",
         "A puncture is a small hole made by something sharp. It can make a bag or basket leak or tear."),
        ("What is a jujube?",
         "A jujube is a sweet candy or fruit snack. In this story, it helps make the clue feel small and child-friendly."),
        ("Why are apples easy to notice in a basket?",
         "Apples are round and bright, so they stand out in a basket. If the basket has a problem, the apples can roll away and make the trouble obvious."),
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
    for e in list(world.entities.values()):
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if e.role:
            bits.append(f"role={e.role}")
        lines.append(f"  {e.id:8} ({e.type:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(n for n, *_ in world.fired)}")
    return "\n".join(lines)


ASP_RULES = r"""
punctured(E) :- meter(E, punctured, V), threshold(T), V >= T.
worry(C) :- role(C, child), punctured(basket).
brave(C) :- role(C, child), punctured(basket).
solved :- fix_applied.
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid in SETTING_REGISTRY:
        lines.append(asp.fact("setting", sid))
    for pid in PROBLEMS:
        lines.append(asp.fact("problem", pid))
    for fid in FIXES:
        lines.append(asp.fact("fix", fid))
    lines.append(asp.fact("threshold", 1))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("", "#show punctured/1.\n#show brave/1.\n#show worry/1."))
    _ = asp.atoms(model, "brave")
    ok = True
    try:
        sample = generate(resolve_params(build_parser().parse_args([]), random.Random(1)))
        _ = sample.story
    except Exception as exc:  # pragma: no cover
        print(f"SMOKE TEST FAILED: {exc}")
        return 1
    print("OK: smoke test story generated.")
    print(f"OK: ASP executed with {len(asp.atoms(model, 'brave'))} brave facts.")
    return 0 if ok else 1


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show setting/1.\n#show problem/1.\n#show fix/1."))
    settings = [a[0] for a in asp.atoms(model, "setting")]
    problems = [a[0] for a in asp.atoms(model, "problem")]
    fixes = [a[0] for a in asp.atoms(model, "fix")]
    return sorted({(s, p, f) for s in settings for p in problems for f in fixes})


def generate(params: StoryParams) -> StorySample:
    world = tell(params)
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


CURATED = [
    StoryParams("market", "basket", "patch", "Mina", "girl", "Noah", "boy"),
    StoryParams("orchard", "bag", "replace", "Eli", "boy", "Rosa", "girl"),
    StoryParams("kitchen", "basket", "patch", "Lila", "girl", "Theo", "boy"),
]


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("", "#show setting/1.\n#show problem/1.\n#show fix/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        for c in combos:
            print(" ".join(c))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 50, 50):
            i += 1
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            sample = generate(params)
            if sample.story in seen:
                continue
            seen.add(sample.story)
            samples.append(sample)

    if args.json:
        print(samples[0].to_json() if len(samples) == 1 else json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        emit(sample, trace=args.trace, qa=args.qa, header=(f"### variant {i+1}" if len(samples) > 1 else ""))
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.setting and args.problem and args.fix and (args.setting, args.problem, args.fix) not in valid_combos():
        raise StoryError("(No valid combination matches the given options.)")
    setting = args.setting or rng.choice(sorted(SETTING_REGISTRY))
    problem = args.problem or rng.choice(sorted(PROBLEMS))
    fix = args.fix or rng.choice(sorted(FIXES))
    child_gender = args.child_gender or rng.choice(["girl", "boy"])
    helper_gender = args.helper_gender or ("boy" if child_gender == "girl" else "girl")
    child = args.child or rng.choice(CHILD_NAMES)
    helper_choices = [n for n in CHILD_NAMES if n != child]
    helper = args.helper or rng.choice(helper_choices)
    return StoryParams(setting, problem, fix, child, child_gender, helper, helper_gender)


if __name__ == "__main__":
    main()

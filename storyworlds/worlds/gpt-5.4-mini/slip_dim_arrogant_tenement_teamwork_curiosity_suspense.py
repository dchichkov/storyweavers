#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/slip_dim_arrogant_tenement_teamwork_curiosity_suspense.py
=========================================================================================

A small bedtime-story world about a curious child in a slip-dim tenement who learns,
through suspense and teamwork, that being a little less arrogant makes room for help.

The world is built from a tiny simulation: a child explores a dim old tenement hall,
finds a stuck window-chain or similar small problem, calls a helper, and together they
solve it. The ending image proves the change: the hall becomes safer and softer, and
pride turns into shared work.
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
    dim: str
    sound: str
    cozy_finish: str

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
    phrase: str
    suspense: str
    fix_sense: int
    fix_power: int
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
class Helper:
    id: str
    label: str
    phrase: str
    method: str
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

    def characters(self) -> list[Entity]:
        return [e for e in list(self.entities.values()) if e.kind == "character"]

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


def _r_spread(world: World) -> list[str]:
    out: list[str] = []
    for ent in world.characters():
        if ent.meters["trouble"] < THRESHOLD:
            continue
        sig = ("trouble", ent.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        ent.memes["worry"] += 1
        out.append("__worry__")
    return out


CAUSAL_RULES = [Rule("trouble", "social", _r_spread)]


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


def sensible_helpers() -> list[Helper]:
    return [h for h in HELPERS.values() if h.id in {"lantern", "lantern_chain", "together"}]


def hazard(problem: Problem) -> bool:
    return problem.fix_sense >= SENSE_MIN


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for sid in SETTINGS:
        for pid, prob in PROBLEMS.items():
            for hid, h in HELPERS.items():
                if hazard(prob):
                    combos.append((sid, pid, hid))
    return combos


@dataclass
@dataclass
class StoryParams:
    setting: str
    problem: str
    helper: str
    child: str
    child_gender: str
    adult: str
    adult_gender: str
    trait: str
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


SETTINGS = {
    "tenement": Setting("tenement", "the old tenement", "slip-dim", "soft floorboards creaked", "the hall felt warm and safe again"),
    "stairwell": Setting("stairwell", "the narrow stairwell", "slip-dim", "a hush hung on every step", "the stairs glowed with a little lamp-light"),
    "landing": Setting("landing", "the shared landing", "slip-dim", "the pipes whispered in the walls", "the landing ended in a calm golden glow"),
}

PROBLEMS = {
    "stuck_window": Problem("stuck_window", "stuck window", "a window that would not budge", "the room felt close and dark", 2, 2, {"tenement", "suspense"}),
    "dark_hall": Problem("dark_hall", "dark hall", "the dim hall where the light was thin", "the shadows looked longer than they should", 2, 2, {"tenement", "suspense"}),
    "loose_latch": Problem("loose_latch", "loose latch", "a latch that clicked but never stayed shut", "the little click sounded lonely and uncertain", 2, 2, {"tenement", "curiosity"}),
}

HELPERS = {
    "lantern": Helper("lantern", "lamp", "a small lamp", "turning it on", {"teamwork"}),
    "lantern_chain": Helper("lantern_chain", "chain lamp", "a lamp on a chain", "pulling the chain together", {"teamwork"}),
    "together": Helper("together", "two hands", "two steady hands", "working side by side", {"teamwork"}),
}

GIRL_NAMES = ["Mina", "Lily", "Nora", "Ivy", "Zoe"]
BOY_NAMES = ["Theo", "Ben", "Milo", "Eli", "Finn"]
TRAITS = ["curious", "careful", "brave", "quiet", "thoughtful"]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Bedtime story world: curiosity, suspense, and teamwork in a slip-dim tenement.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--problem", choices=PROBLEMS)
    ap.add_argument("--helper", choices=HELPERS)
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--adult", choices=["mother", "father"])
    ap.add_argument("--adult-gender", choices=["mother", "father"])
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
    combos = [c for c in valid_combos()
              if (args.setting is None or c[0] == args.setting)
              and (args.problem is None or c[1] == args.problem)
              and (args.helper is None or c[2] == args.helper)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    setting, problem, helper = rng.choice(sorted(combos))
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    adult = args.adult or rng.choice(["mother", "father"])
    adult_gender = args.adult_gender or adult
    trait = args.trait or rng.choice(TRAITS)
    return StoryParams(setting, problem, helper, name, gender, adult, adult_gender, trait)


def tell(params: StoryParams) -> World:
    world = World()
    setting = SETTINGS[params.setting]
    problem = PROBLEMS[params.problem]
    helper = HELPERS[params.helper]
    child = world.add(Entity(params.child, "character", params.child_gender, role="child", traits=[params.trait]))
    adult = world.add(Entity(params.adult, "character", params.adult_gender, role="adult"))
    hall = world.add(Entity("hall", "thing", "hall", label=setting.place))
    child.memes["curiosity"] = 1
    child.memes["pride"] = 1
    adult.memes["care"] = 1

    world.say(f"In {setting.place}, {params.child} had a curious heart and an arrogant little grin. The day was so {setting.dim} that every shadow seemed to be listening.")
    world.say(f"{params.child} slipped along the boards and peered at {problem.phrase}. {problem.suspense}.")
    world.para()
    world.say(f'"I can fix it myself," {params.child} said, and the words sounded proud in the hush.')
    child.meters["trouble"] += 1
    propagate(world, narrate=False)
    world.say(f"But the problem stayed stubborn, and the quiet of the tenement only made it feel bigger.")
    world.say(f"Then {params.child} called for {params.adult}. That was the brave part.")
    world.para()
    world.say(f"{params.adult.capitalize()} came softly, and together they chose {helper.phrase}. They solved it by {helper.method}, with both sets of hands working at once.")
    child.memes["pride"] = 0
    child.memes["teamwork"] += 1
    adult.memes["teamwork"] += 1
    hall.meters["safe"] = 1
    world.say(f"The little fix worked at last. The hall sighed, the shadows grew smaller, and {setting.cozy_finish}.")
    world.say(f"{params.child} smiled up at {params.adult}, no longer so arrogant, and the tenement felt like a bedtime place again.")

    world.facts.update(
        setting=setting,
        problem=problem,
        helper=helper,
        child=child,
        adult=adult,
        hall=hall,
        outcome="fixed",
    )
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a bedtime story that includes the words "slip-dim", "arrogant", and "tenement" in a calm, child-friendly way.',
        f"Tell a story for a young child about {f['child'].id} exploring a slip-dim tenement, learning curiosity, suspense, and teamwork.",
        f'Write a gentle suspense story where a curious child in an old tenement stops being arrogant and asks for help.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child, adult, problem, helper = f["child"], f["adult"], f["problem"], f["helper"]
    return [
        QAItem(
            question=f"Why did {child.id} call for {adult.id}?",
            answer=f"{child.id} tried to solve {problem.label} alone, but it stayed stuck and felt bigger in the slip-dim hall. Calling {adult.id} let them work together, and teamwork solved the problem."),
        QAItem(
            question="How did the story show teamwork?",
            answer=f"{child.id} and {adult.id} used {helper.phrase} and fixed the problem by {helper.method}. The answer came from both of them helping at the same time, not from one person showing off."),
        QAItem(
            question=f"How did {child.id} change by the end?",
            answer=f"At the start, {child.id} was a little arrogant and wanted to do everything alone. By the end, {child.id} was smiling, calmer, and happy to share the job with {adult.id}."),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does curious mean?",
            answer="Curious means wanting to know more, look closer, and ask questions about things you do not yet understand."),
        QAItem(
            question="What is teamwork?",
            answer="Teamwork means people help each other and do a job together. Each person may do a different part, but they work toward the same goal."),
        QAItem(
            question="What is suspense in a story?",
            answer="Suspense is the feeling of wondering what will happen next. It can make a small problem feel quiet and important until the answer comes."),
    ]


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
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted({n for n, *_ in world.fired})}")
    return "\n".join(lines)


ASP_RULES = r"""
valid(S, P, H) :- setting(S), problem(P), helper(H), fix_sense(P, F), sense_min(M), F >= M.
outcome(fixed) :- valid(_, _, _).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for pid, p in PROBLEMS.items():
        lines.append(asp.fact("problem", pid))
        lines.append(asp.fact("fix_sense", pid, p.fix_sense))
        lines.append(asp.fact("fix_power", pid, p.fix_power))
    for hid in HELPERS:
        lines.append(asp.fact("helper", hid))
    lines.append(asp.fact("sense_min", SENSE_MIN))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    clingo_set, python_set = set(asp_valid_combos()), set(valid_combos())
    if clingo_set == python_set:
        print(f"OK: clingo gate matches valid_combos() ({len(clingo_set)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    if clingo_set - python_set:
        print("  only in clingo:", sorted(clingo_set - python_set))
    if python_set - clingo_set:
        print("  only in python:", sorted(python_set - clingo_set))
    return 1


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
        print(asp_program("", "#show valid/3.\n#show outcome/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"{len(asp_valid_combos())} compatible (setting, problem, helper) combos:")
        for s, p, h in asp_valid_combos():
            print(f"  {s:10} {p:15} {h}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)
    samples: list[StorySample] = []
    if args.all:
        curated = [
            StoryParams("tenement", "stuck_window", "lantern", "Mina", "girl", "mother", "curious"),
            StoryParams("stairwell", "dark_hall", "together", "Theo", "boy", "father", "thoughtful"),
            StoryParams("landing", "loose_latch", "lantern_chain", "Ivy", "girl", "mother", "brave"),
        ]
        samples = [generate(p) for p in curated]
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
            header = f"### {p.child} in the {p.setting} ({p.problem}, {p.helper})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()

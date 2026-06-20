#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/scale_jet_reconciliation_kindness_problem_solving_detective.py
==============================================================================================

A standalone story world for a tiny detective tale: two children, a mysterious
missing model jet, a tipped balance scale, a kind misunderstanding, and a gentle
reconciliation after the clues are solved.

The story world is intentionally small and classical:
- a problem appears in a detective-style playroom
- the children investigate by observing physical state changes
- kindness and problem solving turn suspicion into reconciliation
- the ending image proves what changed

Seed words used as narrative instruments:
- scale
- jet

Features:
- Reconciliation
- Kindness
- Problem Solving

Style:
- Detective Story
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
    attrs: dict = field(default_factory=dict)

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
    name: str
    place_sentence: str
    clue_sentence: str

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
class ClueObject:
    id: str
    label: str
    phrase: str
    kind: str
    attrs: dict = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))

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
    missing_sentence: str
    found_sentence: str
    risk_sentence: str

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
    label: str
    sense: int
    text: str
    qa_text: str
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
        clone.facts = dict(self.facts)
        return clone

    def characters(self) -> list[Entity]:
        return [e for e in list(self.entities.values()) if e.kind == "character"]


SETTING = Setting(
    "museum playroom",
    "The museum playroom was bright with posters of magnifying glasses and clue cards.",
    "On one wall, a little brass scale stood beside a display case with tiny toy cases.",
)

PROBLEMS = {
    "missing_jet": Problem(
        "missing_jet",
        "the missing jet",
        "A small model jet had vanished from the display table.",
        "The jet was found tucked somewhere safe again.",
        "The missing jet mattered because everyone feared someone had taken it without asking.",
    )
}

FIXES = {
    "apology_and_return": Fix(
        "apology_and_return",
        "an apology and a careful return",
        3,
        "walked to the owner, told the truth, apologized, and put the jet back on the table",
        "walked to the owner, told the truth, apologized, and put the jet back on the table",
        {"kindness", "reconciliation"},
    ),
    "note_and_sort": Fix(
        "note_and_sort",
        "a note and a careful sort-through",
        2,
        "wrote a note, checked the evidence tray, and sorted the pieces by color and shape",
        "wrote a note, checked the evidence tray, and sorted the pieces by color and shape",
        {"problem_solving"},
    ),
    "gentle_confession": Fix(
        "gentle_confession",
        "a gentle confession",
        3,
        "admitted the mistake kindly, asked for help, and looked under the scale",
        "admitted the mistake kindly, asked for help, and looked under the scale",
        {"kindness", "problem_solving"},
    ),
}

GIRL_NAMES = ["Lily", "Maya", "Nora", "Ivy", "Zoe", "June"]
BOY_NAMES = ["Theo", "Ben", "Max", "Finn", "Leo", "Owen"]


@dataclass
@dataclass
class StoryParams:
    setting: str = "museum playroom"
    problem: str = "missing_jet"
    fix: str = "gentle_confession"
    detective: str = "Lily"
    detective_gender: str = "girl"
    helper: str = "Theo"
    helper_gender: str = "boy"
    curator: str = "Mr. Hall"
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
    combos: list[tuple[str, str, str]] = []
    for s in SETTINGS:
        for p in PROBLEMS:
            for f in FIXES:
                combos.append((s, p, f))
    return combos


def explain_rejection(fix: Fix) -> str:
    return f"(No story: the fix '{fix.id}' is too flimsy for this detective tale.)"


def best_fix() -> Fix:
    return max(FIXES.values(), key=lambda f: f.sense)


def sensible_fixes() -> list[Fix]:
    return [f for f in FIXES.values() if f.sense >= 2]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="A tiny detective story world with a scale, a jet, kindness, and problem solving."
    )
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--problem", choices=PROBLEMS)
    ap.add_argument("--fix", choices=FIXES)
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("-n", type=int, default=1)
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--trace", action="store_true")
    ap.add_argument("--qa", action="store_true")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--asp", action="store_true")
    ap.add_argument("--verify", action="store_true")
    ap.add_argument("--show-asp", action="store_true")
    return ap


def asp_facts() -> str:
    import asp
    lines = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for pid in PROBLEMS:
        lines.append(asp.fact("problem", pid))
    for fid, f in FIXES.items():
        lines.append(asp.fact("fix", fid))
        lines.append(asp.fact("sense", fid, f.sense))
    lines.append(asp.fact("sense_min", 2))
    return "\n".join(lines)


ASP_RULES = r"""
sensible(F) :- fix(F), sense(F,S), sense_min(M), S >= M.
valid(S,P,F) :- setting(S), problem(P), fix(F).
"""


def asp_program(extra: str = "", show: str = "") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program(show="#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_sensible() -> list[str]:
    import asp
    model = asp.one_model(asp_program(show="#show sensible/1."))
    return sorted(v[0] for v in asp.atoms(model, "sensible"))


def asp_verify() -> int:
    import asp
    ok = True
    if set(asp_valid_combos()) != set(valid_combos()):
        ok = False
        print("MISMATCH: ASP valid combos differ from Python valid_combos().")
    if set(asp_sensible()) != {f.id for f in sensible_fixes()}:
        ok = False
        print("MISMATCH: ASP sensible fixes differ from Python gate.")
    try:
        sample = generate(resolve_params(build_parser().parse_args([]), random.Random(7)))
        if not sample.story.strip():
            ok = False
            print("MISMATCH: default generate produced empty story.")
    except Exception as exc:
        ok = False
        print(f"MISMATCH: generate crashed: {exc}")
    if ok:
        print("OK: ASP parity and generation smoke test passed.")
        return 0
    return 1


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.fix and FIXES[args.fix].sense < 2:
        raise StoryError(explain_rejection(FIXES[args.fix]))
    combos = [c for c in valid_combos()
              if (args.setting is None or c[0] == args.setting)
              and (args.problem is None or c[1] == args.problem)
              and (args.fix is None or c[2] == args.fix)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    setting, problem, fix = rng.choice(sorted(combos))
    detective_gender = rng.choice(["girl", "boy"])
    helper_gender = "boy" if detective_gender == "girl" else "girl"
    detective = args.__dict__.get("detective") or rng.choice(GIRL_NAMES if detective_gender == "girl" else BOY_NAMES)
    helper = args.__dict__.get("helper") or rng.choice(BOY_NAMES if helper_gender == "boy" else GIRL_NAMES)
    curator = "Ms. Reed" if rng.random() < 0.5 else "Mr. Hall"
    return StoryParams(setting, problem, fix, detective, detective_gender, helper, helper_gender, curator)


def _setup(world: World, detective: Entity, helper: Entity, curator: Entity, prob: Problem) -> None:
    detective.memes["curious"] += 1
    helper.memes["curious"] += 1
    world.say(
        f"{detective.id} and {helper.id} were playing detective in the {world.setting.name}. "
        f"{world.setting.place_sentence}"
    )
    world.say(
        f"Near the display table, {world.setting.clue_sentence} {prob.missing_sentence}"
    )
    world.say(
        f'"This looks like a case," said {detective.id}. "{prob.label} has to be found."'
    )


def _investigate(world: World, detective: Entity, helper: Entity, prob: Problem) -> None:
    detective.meters["attention"] += 1
    helper.meters["attention"] += 1
    world.say(
        f"{detective.id} checked the floor, and {helper.id} looked behind the papers. "
        f"Together they noticed a neat dust trail leading toward the scale."
    )
    world.say(
        f'"Maybe the clue was hidden by the scale," whispered {helper.id}. '
        f'"Let\'s solve it kindly."'
    )


def _suspect(world: World, detective: Entity, helper: Entity) -> None:
    detective.memes["worry"] += 1
    world.say(
        f"{detective.id} first suspected that someone had taken the jet on purpose, "
        f"but {helper.id} noticed a small gap and a bent label card instead."
    )
    world.say(
        f"That changed the case. The scale had tipped, and the missing jet might have slid away by accident."
    )


def _solve(world: World, detective: Entity, helper: Entity, curator: Entity, fix: Fix, prob: Problem) -> None:
    detective.memes["kindness"] += 1
    helper.memes["kindness"] += 1
    detective.memes["reconciliation"] += 1
    helper.memes["reconciliation"] += 1
    world.say(
        f"{detective.id} took a breath, then {fix.text}. {curator.label_word if curator.label else curator.id} smiled with relief."
    )
    world.say(
        f"The apology turned the mystery gentle again, and the problem was solved without any unkind words."
    )
    world.say(
        f"In the end, {prob.found_sentence} The model jet sat beside the brass scale, bright and safe."
    )


def _qa_prompt(world: World) -> list[str]:
    return [
        f'Write a detective story for a 3-to-5-year-old that includes the words "scale" and "jet".',
        f"Tell a small mystery where {world.facts['detective'].id} and {world.facts['helper'].id} solve a problem with kindness and reconciliation.",
        f"Write a gentle detective story where a missing jet is found after the children use problem solving instead of blaming anyone.",
    ]


def _story_qa(world: World) -> list[QAItem]:
    d = world.facts["detective"]
    h = world.facts["helper"]
    cur = world.facts["curator"]
    prob = world.facts["problem"]
    fix = world.facts["fix"]
    return [
        QAItem(
            question="What was the mystery?",
            answer=f"It was about the missing jet. The children followed clues in the museum playroom until they found it again."
        ),
        QAItem(
            question="What clue helped them solve it?",
            answer="The brass scale had tipped, which suggested the jet had slid rather than been stolen. That clue led them to look in a safe hiding place nearby."
        ),
        QAItem(
            question="How did they fix the problem?",
            answer=f"They used {fix.label} and spoke kindly. That led to reconciliation, because they solved the problem without blaming each other."
        ),
    ]


def _world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a scale?",
            answer="A scale is something you can use to compare how heavy things are. In a mystery, a tipped scale can be an important clue."
        ),
        QAItem(
            question="What is a jet?",
            answer="A jet is something that can fly very fast in the sky. Here it is a tiny model jet in a playroom case."
        ),
        QAItem(
            question="What is kindness?",
            answer="Kindness means using gentle words and helping other people. In a story, kindness can help fix hurt feelings and bring people back together."
        ),
        QAItem(
            question="What is problem solving?",
            answer="Problem solving means looking carefully for clues and trying a sensible plan. It helps people figure out what happened and what to do next."
        ),
    ]


def tell(params: StoryParams) -> World:
    world = World(SETTING)
    detective = world.add(Entity(params.detective, kind="character", type=params.detective_gender, role="detective"))
    helper = world.add(Entity(params.helper, kind="character", type=params.helper_gender, role="helper"))
    curator = world.add(Entity(params.curator, kind="character", type="man" if params.curator.startswith("Mr.") else "woman", role="curator", label=params.curator))
    prob = PROBLEMS[params.problem]
    fix = FIXES[params.fix]
    world.facts.update(detective=detective, helper=helper, curator=curator, problem=prob, fix=fix)

    _setup(world, detective, helper, curator, prob)
    world.para()
    _investigate(world, detective, helper, prob)
    _suspect(world, detective, helper)
    world.para()
    _solve(world, detective, helper, curator, fix, prob)
    world.facts["outcome"] = "reconciled"
    return world


def generate(params: StoryParams) -> StorySample:
    world = tell(params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=_qa_prompt(world),
        story_qa=_story_qa(world),
        world_qa=_world_qa(world),
        world=world,
    )


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world is not None:
        print("--- world model state ---")
        for e in sample.list(world.entities.values()):
            print(f"  {e.id}: role={e.role} memes={dict(e.memes)}")
    if qa:
        print()
        print("== prompts ==")
        for i, p in enumerate(sample.prompts, 1):
            print(f"{i}. {p}")
        print("\n== story QA ==")
        for item in sample.story_qa:
            print(f"Q: {item.question}\nA: {item.answer}")
        print("\n== world QA ==")
        for item in sample.world_qa:
            print(f"Q: {item.question}\nA: {item.answer}")


def format_story_qa(sample: StorySample) -> str:
    return sample.to_json()


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program(show="#show valid/3.\n#show sensible/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"sensible fixes: {', '.join(asp_sensible())}")
        for combo in asp_valid_combos():
            print(combo)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        curated = [
            StoryParams(detective="Lily", detective_gender="girl", helper="Theo", helper_gender="boy", curator="Mr. Hall", fix="gentle_confession"),
            StoryParams(detective="Nora", detective_gender="girl", helper="Max", helper_gender="boy", curator="Ms. Reed", fix="apology_and_return"),
            StoryParams(detective="Ben", detective_gender="boy", helper="Maya", helper_gender="girl", curator="Mr. Hall", fix="note_and_sort"),
        ]
        samples = [generate(p) for p in curated]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 50, 50):
            i += 1
            try:
                p = resolve_params(args, random.Random(base_seed + i))
            except StoryError as err:
                print(err)
                return
            p.seed = base_seed + i
            s = generate(p)
            if s.story in seen:
                continue
            seen.add(s.story)
            samples.append(s)

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

#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/gobble_problem_solving_transformation_whodunit.py
=================================================================================

A standalone storyworld for a tiny whodunit: something keeps going missing,
everyone hears a strange "gobble", and a child detective solves the mystery by
following clues instead of guessing. The transformation beat turns the culprit
from a sneaky snack-gobbler into an honest helper who fixes the mess.

The domain is intentionally small:
- one child detective
- one snack table / pantry scene
- one hungry suspect with a physical and emotional transformation
- one solution that uses careful clues and a shared fix

Run it:
    python storyworlds/worlds/gpt-5.4-mini/gobble_problem_solving_transformation_whodunit.py
    python storyworlds/worlds/gpt-5.4-mini/gobble_problem_solving_transformation_whodunit.py --all
    python storyworlds/worlds/gpt-5.4-mini/gobble_problem_solving_transformation_whodunit.py --qa --json
    python storyworlds/worlds/gpt-5.4-mini/gobble_problem_solving_transformation_whodunit.py --verify
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
    traits: list[str] = field(default_factory=list)
    role: str = ""
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
    detail: str
    clue_spot: str
    ending_image: str

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
class Suspect:
    id: str
    label: str
    sound: str
    hiding_place: str
    crumb_kind: str
    snack_kind: str
    cause: str
    transformation: str
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
    missing: str
    mess: str
    trail: str
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
    method: str
    action: str
    calm: str
    repair: str
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
        return clone


@dataclass
class Rule:
    name: str
    tag: str
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


def _r_alarm(world: World) -> list[str]:
    out: list[str] = []
    for e in list(world.entities.values()):
        if e.meters["missing"] >= THRESHOLD and ("alarm", e.id) not in world.fired:
            world.fired.add(("alarm", e.id))
            for ch in world.characters():
                ch.memes["worry"] += 1
            out.append("__alarm__")
    return out


def _r_clue(world: World) -> list[str]:
    out: list[str] = []
    detective = world.entities.get("detective")
    if detective and detective.memes["attention"] >= THRESHOLD and ("clue", "found") not in world.fired:
        world.fired.add(("clue", "found"))
        detective.memes["confidence"] += 1
        out.append("The detective noticed tiny crumbs on the floor and a little trail by the pantry.")
    return out


CAUSAL_RULES = [Rule("alarm", "social", _r_alarm), Rule("clue", "social", _r_clue)]


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


def suspicious_sound(problem: Problem, suspect: Suspect) -> bool:
    return suspect.sound == "gobble" and problem.missing == suspect.snack_kind


def sensible_fix(fix: Fix, problem: Problem) -> bool:
    return fix.sense >= 2 and fix.power >= 1 and bool(problem.missing)


def solve_detective(world: World, detective: Entity, setting: Setting, problem: Problem, suspect: Suspect) -> None:
    detective.memes["attention"] += 1
    world.say(
        f"On a quiet afternoon, {detective.id} found {problem.label} missing from {setting.place}. "
        f"{setting.detail}"
    )
    world.say(
        f'Then everyone heard a strange "{suspect.sound}" coming from {suspect.hiding_place}. '
        f'{detective.id} frowned and said, "That sounds like a clue."'
    )


def investigate(world: World, detective: Entity, suspect: Suspect, problem: Problem) -> None:
    detective.memes["attention"] += 1
    detective.meters["observations"] += 1
    world.say(
        f"{detective.id} looked at the floor, the pantry door, and the tiny marks near {suspect.hiding_place}. "
        f"There were {problem.trail}."
    )


def accuse(world: World, detective: Entity, suspect: Suspect) -> None:
    world.say(
        f'"I think {suspect.id} did it," {detective.id} whispered. '
        f'But instead of shouting, {detective.id} waited and checked one more clue.'
    )


def reveal(world: World, detective: Entity, suspect: Suspect, problem: Problem) -> None:
    suspect.meters["covered_crumbs"] += 1
    world.say(
        f"At last, {detective.id} opened the cabinet and found {suspect.label}, all sticky with crumbs. "
        f'"So {suspect.id} was the {problem.mess} gobbler," {detective.id} said.'
    )


def transform(world: World, suspect: Suspect) -> None:
    entity = world.get(suspect.id)
    entity.memes["shame"] = 0.0
    entity.memes["honesty"] += 1
    entity.meters["sneaky"] = 0.0
    entity.meters["helpful"] += 1
    world.say(
        f'{suspect.id} sighed and stopped hiding. "I was hungry," {suspect.id} admitted. '
        f"That honest moment changed everything."
    )
    world.say(
        f"After that, {suspect.id} became more helpful and promised to ask before gobbling snacks again."
    )


def fix_mess(world: World, detective: Entity, suspect: Suspect, fix: Fix, problem: Problem, setting: Setting) -> None:
    world.say(
        f"{detective.id} did not stay angry. {detective.id} used {fix.method} and asked {suspect.id} to help."
    )
    world.say(
        f"Together they {fix.action}. The {problem.mess} was cleaned up, and {suspect.id} made the {fix.repair} right again."
    )
    world.say(
        f"By evening, {setting.ending_image}, and the mystery felt small and solved."
    )


def tell(setting: Setting, problem: Problem, suspect: Suspect, fix: Fix, detective_name: str, detective_gender: str) -> World:
    world = World()
    detective = world.add(Entity(id=detective_name, kind="character", type=detective_gender, role="detective"))
    culprit = world.add(Entity(id=suspect.id, kind="character", type="thing", role="suspect", label=suspect.label))
    world.add(Entity(id="table", kind="thing", type="table", label="the table"))
    world.add(Entity(id="pantry", kind="thing", type="place", label="the pantry"))

    culprit.meters["sneaky"] = 1.0
    culprit.meters["crumbs"] = 1.0
    culprit.meters["missing"] = 1.0
    culprit.memes["hunger"] = 1.0
    culprit.memes["nervous"] = 1.0

    solve_detective(world, detective, setting, problem, suspect)
    world.para()
    investigate(world, detective, suspect, problem)
    accuse(world, detective, suspect)
    reveal(world, detective, suspect, problem)
    world.para()
    transform(world, suspect)
    fix_mess(world, detective, suspect, fix, problem, setting)

    detective.memes["satisfaction"] += 1
    culprit.meters["sneaky"] = 0.0
    culprit.meters["helpful"] += 1
    world.facts.update(
        detective=detective,
        suspect=culprit,
        setting=setting,
        problem=problem,
        fix=fix,
        solved=True,
        transformed=True,
        clue="crumb trail",
        sound=suspect.sound,
    )
    return world


SETTINGS = {
    "kitchen": Setting("kitchen", "the kitchen", "Sunlight shone on the counter, and a cookie jar sat by the sink.", "the pantry", "the snack table was neat again"),
    "classroom": Setting("classroom", "the classroom", "Paper stars hung from the ceiling, and little chairs stood in a row.", "the cubby", "the shelves were tidy again"),
    "picnic": Setting("picnic", "the picnic blanket", "The grass was soft, and a red basket waited beside the blanket.", "the basket", "the picnic blanket was clean again"),
}

SUSPECTS = {
    "turkey": Suspect("Milo", "a plump turkey", "gobble", "behind the curtain", "crumbs", "crackers", "gobbling the crackers", "honest helper", {"gobble", "snack"}),
    "goat": Suspect("Gogo", "a small goat", "gobble", "under the bench", "crumbs", "cookies", "gobbling the cookies", "calm helper", {"gobble", "snack"}),
    "frog": Suspect("Bubbles", "a hungry frog", "gobble", "by the flower pot", "crumbs", "snacks", "gobbling the snacks", "friendly helper", {"gobble", "snack"}),
}

PROBLEMS = {
    "cookies": Problem("cookies", "cookies", "cookies", "crumby mess", "tiny round crumbs", {"snack"}),
    "crackers": Problem("crackers", "crackers", "crackers", "crumby mess", "small pale crumbs", {"snack"}),
    "snacks": Problem("snacks", "snacks", "snacks", "crumby mess", "a little line of crumbs", {"snack"}),
}

FIXES = {
    "ask": Fix("ask", "kind questions", "ask the right questions", "stayed calm", "snack jar", 1, 3, {"problem-solving"}),
    "search": Fix("search", "careful searching", "search room by room", "stayed careful", "basket", 2, 3, {"problem-solving"}),
    "share": Fix("share", "sharing snacks", "share a plate of treats", "smiled kindly", "snack bowl", 2, 2, {"problem-solving", "transformation"}),
}


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for sid, setting in SETTINGS.items():
        for pid, problem in PROBLEMS.items():
            for suid, suspect in SUSPECTS.items():
                if suspicious_sound(problem, suspect):
                    combos.append((sid, pid, suid))
    return combos


@dataclass
@dataclass
class StoryParams:
    setting: str
    problem: str
    suspect: str
    fix: str
    detective_name: str
    detective_gender: str
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


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A tiny whodunit storyworld with gobbling clues, problem solving, and transformation.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--problem", choices=PROBLEMS)
    ap.add_argument("--suspect", choices=SUSPECTS)
    ap.add_argument("--fix", choices=FIXES)
    ap.add_argument("--detective")
    ap.add_argument("--gender", choices=["girl", "boy"])
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
    if args.fix and not sensible_fix(FIXES[args.fix], PROBLEMS[args.problem] if args.problem else next(iter(PROBLEMS.values()))):
        raise StoryError("That fix is too weak for this mystery.")
    combos = [c for c in valid_combos()
              if (args.setting is None or c[0] == args.setting)
              and (args.problem is None or c[1] == args.problem)
              and (args.suspect is None or c[2] == args.suspect)]
    if not combos:
        raise StoryError("(No valid whodunit combination matches the given options.)")
    setting, problem, suspect = rng.choice(sorted(combos))
    fix = args.fix or rng.choice(sorted(FIXES))
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.detective or rng.choice(["Lena", "Mina", "Tia", "Noah", "Eli", "Kai"])
    return StoryParams(setting, problem, suspect, fix, name, gender)


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a child-friendly whodunit story that includes the word "gobble" and shows a mystery being solved by clues.',
        f"Tell a story where {f['detective'].id} follows crumbs, discovers who was gobbling snacks, and helps turn the culprit into a better helper.",
        f"Write a mystery with a small transformation: the snack-gobbler admits what happened, helps repair the mess, and the ending feels calm.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    det = f["detective"]
    sus = f["suspect"]
    setting = f["setting"]
    problem = f["problem"]
    fix = f["fix"]
    return [
        QAItem(
            question="What was the mystery about?",
            answer=f"It was about {problem.label} going missing from {setting.place}. The clue was a line of crumbs, which helped point to the hungry suspect."
        ),
        QAItem(
            question="How did the detective solve the mystery?",
            answer=f"{det.id} looked carefully at the clues instead of guessing. The crumbs, the hiding place, and the strange gobble sound led {det.id} to {sus.id}."
        ),
        QAItem(
            question="How did the suspect change at the end?",
            answer=f"{sus.id} changed from sneaky to honest and helpful. After admitting the snack gobbling, {sus.id} helped clean up and promised to ask before taking food again."
        ),
        QAItem(
            question="Why did the detective choose that fix?",
            answer=f"{det.id} chose {fix.method} because it was calm and could help repair the problem. The fix gave everyone a way to solve the mystery without making the day worse."
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does gobble mean?",
            answer="Gobble is the sound or action of eating quickly and noisily. It can also remind people of a hungry turkey."
        ),
        QAItem(
            question="What should a detective do in a mystery?",
            answer="A detective should look for clues, think carefully, and ask smart questions. Guessing too fast can lead to the wrong answer."
        ),
        QAItem(
            question="What is a transformation in a story?",
            answer="A transformation is a change from one way of being to another. A character might go from sneaky to honest, or from worried to helpful."
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
        if e.label:
            bits.append(f"label={e.label}")
        lines.append(f"  {e.id:10} ({e.type:7}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted({n for n, *_ in world.fired})}")
    return "\n".join(lines)


ASP_RULES = r"""
gobble_case(S) :- suspect(S), sound(S, "gobble").
valid(O,P,S) :- setting(O), problem(P), suspect(S), gobble_case(S), missing(P, Snack), snack_of(S, Snack).
outcome(solved) :- detective_attention, clue_found, admit_transform.
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for pid, p in PROBLEMS.items():
        lines.append(asp.fact("problem", pid))
        lines.append(asp.fact("missing", pid, p.missing))
    for sid, s in SUSPECTS.items():
        lines.append(asp.fact("suspect", sid))
        lines.append(asp.fact("sound", sid, s.sound))
        lines.append(asp.fact("snack_of", sid, s.snack_kind))
    for fid in FIXES:
        lines.append(asp.fact("fix", fid))
    lines.append(asp.fact("detective_attention"))
    lines.append(asp.fact("clue_found"))
    lines.append(asp.fact("admit_transform"))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    rc = 0
    if set(asp_valid_combos()) == set(valid_combos()):
        print(f"OK: ASP gate matches valid_combos() ({len(valid_combos())} combos).")
    else:
        print("MISMATCH between ASP and Python gate.")
        rc = 1
    try:
        sample = generate(resolve_params(argparse.Namespace(setting=None, problem=None, suspect=None, fix=None, detective=None, gender=None), random.Random(7)))
        _ = sample.story
        print("OK: normal generation smoke test passed.")
    except Exception as exc:
        print(f"SMOKE TEST FAILED: {exc}")
        rc = 1
    return rc


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.setting], PROBLEMS[params.problem], SUSPECTS[params.suspect], FIXES[params.fix], params.detective_name, params.detective_gender)
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


CURATED = [
    StoryParams("kitchen", "cookies", "turkey", "ask", "Lena", "girl"),
    StoryParams("classroom", "crackers", "goat", "search", "Mina", "girl"),
    StoryParams("picnic", "snacks", "frog", "share", "Noah", "boy"),
]


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("", "#show valid/3.\n"))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"{len(asp_valid_combos())} compatible combos:")
        for combo in asp_valid_combos():
            print(" ", combo)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)
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
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()

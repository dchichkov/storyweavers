#!/usr/bin/env python3
"""
storyworlds/worlds/weaken_happy_ending_problem_solving_moral_value.py
====================================================================

A standalone story world for a tiny pirate-style tale about something weak,
a smart fix, and a happy ending.

Seed premise:
- A little pirate game turns tricky when a rope bridge or spar becomes weak.
- The children notice the problem, solve it with a sensible repair, and end with
  a safe, bright ending image that proves the change.

This world models:
- typed entities with physical meters and emotional memes
- a small forward-chaining causal engine
- a reasonableness gate for valid combinations
- a Python/ASP twin for parity checks
- story-grounded and world-knowledge QA

The storyword to include is: weaken
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
    phrase: str = ""
    role: str = ""
    wears: str = ""
    owner: str = ""
    helper: bool = False
    fixed: bool = False
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
        return self.label or self.type


@dataclass
class Setting:
    id: str
    place: str
    affordances: set[str] = field(default_factory=set)


@dataclass
class Problem:
    id: str
    label: str
    weak_part: str
    risk: str
    hint: str
    kind: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Fix:
    id: str
    label: str
    prep: str
    result: str
    power: int
    tags: set[str] = field(default_factory=set)


@dataclass
class Prize:
    id: str
    label: str
    phrase: str
    body: str
    plural: bool = False
    tags: set[str] = field(default_factory=set)


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.zone: str = ""

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str) -> Entity:
        return self.entities[eid]

    def characters(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.kind == "character"]

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
        clone.zone = self.zone
        clone.paragraphs = [[]]
        clone.facts = dict(self.facts)
        return clone


@dataclass
class Rule:
    name: str
    tag: str
    apply: Callable[[World], list[str]]


def _r_weakness(world: World) -> list[str]:
    out: list[str] = []
    bridge = world.entities.get("bridge")
    if not bridge:
        return out
    if bridge.meters["weak"] < THRESHOLD:
        return out
    sig = ("weakness", bridge.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    bridge.meters["unsafe"] += 1
    for kid in world.characters():
        kid.memes["worry"] += 1
    out.append("__weak__")
    return out


def _r_fix(world: World) -> list[str]:
    bridge = world.entities.get("bridge")
    if not bridge:
        return []
    if not bridge.fixed:
        return []
    sig = ("fixed", bridge.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    bridge.meters["unsafe"] = 0
    bridge.meters["strong"] += 1
    return ["__fixed__"]


CAUSAL_RULES = [
    Rule("weakness", "physical", _r_weakness),
    Rule("fix", "physical", _r_fix),
]


def propagate(world: World, narrate: bool = True) -> list[str]:
    out: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            sents = rule.apply(world)
            if sents:
                changed = True
                out.extend(s for s in sents if not s.startswith("__"))
    if narrate:
        for s in out:
            world.say(s)
    return out


def problem_at_risk(problem: Problem, prize: Prize) -> bool:
    return problem.kind in prize.tags


def select_fix(problem: Problem, prize: Prize) -> Optional[Fix]:
    for fix in FIXES.values():
        if problem.kind in fix.tags and prize.body in fix.tags:
            return fix
    return None


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for sid, setting in SETTINGS.items():
        for pid, problem in PROBLEMS.items():
            for tid, prize in PRIZES.items():
                if sid in problem.tags and problem_at_risk(problem, prize) and select_fix(problem, prize):
                    combos.append((sid, pid, tid))
    return combos


def predict_break(world: World, problem: Problem, prize: Prize) -> bool:
    sim = world.copy()
    sim.get("bridge").meters["weak"] += 1
    propagate(sim, narrate=False)
    return sim.get("bridge").meters["unsafe"] >= THRESHOLD


def tell(setting: Setting, problem: Problem, prize: Prize, fix: Fix,
         hero_name: str, helper_name: str, parent_name: str, hero_gender: str,
         helper_gender: str, parent_gender: str) -> World:
    world = World(setting)
    hero = world.add(Entity(id=hero_name, kind="character", type=hero_gender, role="hero"))
    helper = world.add(Entity(id=helper_name, kind="character", type=helper_gender, role="helper"))
    parent = world.add(Entity(id=parent_name, kind="character", type=parent_gender, role="parent", label=parent_name))
    bridge = world.add(Entity(id="bridge", type="bridge", label="rope bridge"))
    prize_ent = world.add(Entity(id="prize", type=prize.id, label=prize.label, phrase=prize.phrase, wears=prize.body, owner=hero.id))

    world.facts["hero"] = hero
    world.facts["helper"] = helper
    world.facts["parent"] = parent
    world.facts["bridge"] = bridge
    world.facts["prize"] = prize_ent
    world.facts["problem"] = problem
    world.facts["prize_cfg"] = prize
    world.facts["fix"] = fix
    world.facts["setting"] = setting

    hero.memes["joy"] += 1
    helper.memes["joy"] += 1

    world.say(f"{hero.id} and {helper.id} played pirates at {setting.place}.")
    world.say(f"They loved the shiny {prize.label} and the promise of treasure.")
    world.para()
    world.say(f"Then they noticed the {problem.label}: the {problem.weak_part} had started to weaken, and {problem.risk}.")
    bridge.meters["weak"] += 1
    propagate(world, narrate=True)
    world.say(f'"We need to fix it," said {helper.id}, because {problem.hint}.')
    hero.memes["worry"] += 1

    if predict_break(world, problem, prize):
        world.say(f'{hero.id} frowned, then listened. "We can use {fix.label} first."')
    world.para()
    bridge.fixed = True
    hero.memes["pride"] += 1
    helper.memes["pride"] += 1
    hero.memes["worry"] = 0
    helper.memes["worry"] = 0
    world.say(f"They used {fix.label} and {fix.result}.")
    propagate(world, narrate=True)
    world.say(f"After that, the {problem.weak_part} was solid again, and the {prize.label} stayed safe.")
    world.say(f"At the end, {hero.id} and {helper.id} sailed on, laughing beside the sturdy {problem.label}.")

    world.facts["resolved"] = True
    return world


SETTINGS = {
    "dock": Setting(id="dock", place="the dock", affordances={"pirates"}),
    "deck": Setting(id="deck", place="the little deck", affordances={"pirates"}),
    "cove": Setting(id="cove", place="the quiet cove", affordances={"pirates"}),
    "island": Setting(id="island", place="the island shore", affordances={"pirates"}),
}

PROBLEMS = {
    "rope": Problem(
        id="rope",
        label="rope bridge",
        weak_part="the rope",
        risk="it could snap under the children",
        hint="a broken bridge cannot carry treasure safely",
        kind="rope",
        tags={"dock", "deck", "cove", "island", "pirates"},
    ),
    "mast": Problem(
        id="mast",
        label="mast spar",
        weak_part="the spar",
        risk="the sail could sag and flop down",
        hint="a weak mast makes the pirate flag droop",
        kind="mast",
        tags={"dock", "deck", "cove", "island", "pirates"},
    ),
    "plank": Problem(
        id="plank",
        label="wooden plank",
        weak_part="the plank",
        risk="it could bend and dump the map",
        hint="a plank needs a stronger brace before the walk",
        kind="plank",
        tags={"dock", "deck", "cove", "island", "pirates"},
    ),
    "lamp": Problem(
        id="lamp",
        label="hanging lamp hook",
        weak_part="the hook",
        risk="the lamp could fall and go out",
        hint="a loose hook needs a careful tightening",
        kind="lamp",
        tags={"dock", "deck", "cove", "island", "pirates"},
    ),
}

FIXES = {
    "knots": Fix(id="knots", label="fresh knots", prep="tie new knots", result="the bridge held tight", power=2, tags={"rope", "body"}),
    "brace": Fix(id="brace", label="a wooden brace", prep="add a wooden brace", result="the spar stood straight again", power=2, tags={"mast", "body"}),
    "planks": Fix(id="planks", label="extra planks", prep="lay extra planks", result="the walk felt firm", power=2, tags={"plank", "body"}),
    "hook": Fix(id="hook", label="a stronger hook", prep="replace the hook", result="the lamp hung safe and still", power=2, tags={"lamp", "body"}),
}

PRIZES = {
    "map": Prize(id="map", label="treasure map", phrase="a bright treasure map", body="body", tags={"rope", "mast", "plank", "lamp"}),
    "chest": Prize(id="chest", label="toy chest", phrase="a painted toy chest", body="body", tags={"rope", "mast", "plank", "lamp"}),
    "flag": Prize(id="flag", label="pirate flag", phrase="a tiny pirate flag", body="body", tags={"rope", "mast", "plank", "lamp"}),
    "lantern": Prize(id="lantern", label="lantern", phrase="a small lantern", body="body", tags={"rope", "mast", "plank", "lamp"}),
}

GIRL_NAMES = ["Lily", "Mia", "Zoe", "Ava", "Ella", "Nora", "Rose"]
BOY_NAMES = ["Tom", "Ben", "Max", "Sam", "Leo", "Finn", "Eli"]
TRAITS = ["curious", "careful", "brave", "kind", "clever"]


@dataclass
class StoryParams:
    setting: str = ""
    problem: str = ""
    prize: str = ""
    hero_name: str = ""
    hero_gender: str = "girl"
    helper_name: str = ""
    helper_gender: str = "boy"
    parent_name: str = "Captain Mira"
    parent_gender: str = "woman"
    trait: str = "curious"
    seed: Optional[int] = None


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    helper = f["helper"]
    problem = f["problem"]
    prize = f["prize_cfg"]
    fix = f["fix"]
    return [
        f'Write a short pirate story for a little child that uses the word "weaken" and ends happily.',
        f"Tell a problem-solving story where {hero.id} and {helper.id} notice that {problem.label} has started to weaken, then repair it with {fix.label}.",
        f"Write a gentle pirate tale where the children protect {prize.label} by noticing a weak spot and fixing it before the game can continue.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero, helper, problem, prize, fix = f["hero"], f["helper"], f["problem"], f["prize_cfg"], f["fix"]
    setting = f["setting"]
    return [
        QAItem(
            question=f"What did {hero.id} and {helper.id} do at {setting.place}?",
            answer=f"They played pirates at {setting.place} and looked after the {prize.label}. The game started happily before they noticed a weak spot.",
        ),
        QAItem(
            question=f"What problem made the pirate game tricky?",
            answer=f"The {problem.label} started to weaken. That was a problem because {problem.risk}, so they had to stop and think.",
        ),
        QAItem(
            question=f"How did they solve the problem with the {problem.label}?",
            answer=f"They used {fix.label} and fixed it before it could get worse. The smart repair made the {problem.label} strong again.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does it mean when something weakens?",
            answer="When something weakens, it gets less strong than before. Weak things may bend, wobble, or break more easily.",
        ),
        QAItem(
            question="Why is a fix important when something is weak?",
            answer="A fix can make the weak thing strong enough to use again. That helps people stay safe and keep going.",
        ),
        QAItem(
            question="What is a pirate game?",
            answer="A pirate game is pretend play where children act like pirates. They might sail, search for treasure, and use maps or flags.",
        ),
        QAItem(
            question="What is a moral value?",
            answer="A moral value is a good way to act, like being kind, honest, or helpful. It guides people when they make choices.",
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
        bits = []
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if e.label:
            bits.append(f"label={e.label}")
        if e.role:
            bits.append(f"role={e.role}")
        lines.append(f"  {e.id:8} ({e.type:8}) {' '.join(bits)}")
    return "\n".join(lines)


ASP_RULES = r"""
weak_problem(B) :- bridge(B), weak(B).
at_risk(P) :- problem(P), prize(X), problem_kind(P, K), prize_tag(X, K).
has_fix(P) :- problem(P), prize(X), problem_kind(P, K), prize_tag(X, K), fix(F), fix_tag(F, K), body_ok(F, X).
resolved :- weak_problem(B), fixed(B).
valid(Setting, Problem, Prize) :- setting(Setting), problem(Problem), prize(Prize),
                                  setting_affords(Setting, pirates),
                                  problem_on(Problem, Setting),
                                  at_risk(Problem), has_fix(Problem).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid, s in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        for a in sorted(s.affordances):
            lines.append(asp.fact("setting_affords", sid, a))
    for pid, p in PROBLEMS.items():
        lines.append(asp.fact("problem", pid))
        lines.append(asp.fact("problem_kind", pid, p.kind))
        for t in sorted(p.tags):
            lines.append(asp.fact("problem_on", pid, t))
    for fid, f in FIXES.items():
        lines.append(asp.fact("fix", fid))
        lines.append(asp.fact("fix_tag", fid, *sorted(f.tags)[0:1]) if f.tags else asp.fact("fix_tag", fid, "body"))
    for rid, r in PRIZES.items():
        lines.append(asp.fact("prize", rid))
        for t in sorted(r.tags):
            lines.append(asp.fact("prize_tag", rid, t))
    lines.append(asp.fact("bridge", "bridge"))
    lines.append(asp.fact("weak", "bridge"))
    lines.append(asp.fact("fixed", "bridge"))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    import io
    import contextlib
    clingo_set = set(asp_valid_combos())
    python_set = set(valid_combos())
    rc = 0
    if clingo_set == python_set:
        print(f"OK: clingo gate matches valid_combos() ({len(clingo_set)} combos).")
    else:
        print("MISMATCH between clingo and valid_combos():")
        if clingo_set - python_set:
            print("  only in clingo:", sorted(clingo_set - python_set))
        if python_set - clingo_set:
            print("  only in python:", sorted(python_set - clingo_set))
        rc = 1
    try:
        sample = generate(resolve_params(build_parser().parse_args([]), random.Random(777)))
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            emit(sample, trace=True, qa=True)
        print("OK: smoke test generate/emit completed.")
    except Exception as exc:
        print(f"SMOKE TEST FAILED: {exc}")
        rc = 1
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Story world sketch: pirate problem solving, moral value, happy ending.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--problem", choices=PROBLEMS)
    ap.add_argument("--prize", choices=PRIZES)
    ap.add_argument("--hero-name")
    ap.add_argument("--hero-gender", choices=["girl", "boy"])
    ap.add_argument("--helper-name")
    ap.add_argument("--helper-gender", choices=["girl", "boy"])
    ap.add_argument("--parent-name")
    ap.add_argument("--parent-gender", choices=["woman", "man"])
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
              and (args.prize is None or c[2] == args.prize)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    setting, problem, prize = rng.choice(sorted(combos))
    hero_gender = args.hero_gender or rng.choice(["girl", "boy"])
    helper_gender = args.helper_gender or ("boy" if hero_gender == "girl" else "girl")
    hero_pool = GIRL_NAMES if hero_gender == "girl" else BOY_NAMES
    helper_pool = GIRL_NAMES if helper_gender == "girl" else BOY_NAMES
    hero_name = args.hero_name or rng.choice(hero_pool)
    helper_name = args.helper_name or rng.choice([n for n in helper_pool if n != hero_name] or helper_pool)
    parent_name = args.parent_name or "Captain Mira"
    parent_gender = args.parent_gender or "woman"
    trait = rng.choice(TRAITS)
    return StoryParams(
        setting=setting, problem=problem, prize=prize,
        hero_name=hero_name, hero_gender=hero_gender,
        helper_name=helper_name, helper_gender=helper_gender,
        parent_name=parent_name, parent_gender=parent_gender,
        trait=trait,
    )


def generate(params: StoryParams) -> StorySample:
    if params.setting not in SETTINGS or params.problem not in PROBLEMS or params.prize not in PRIZES:
        raise StoryError("Unknown story parameter.")
    setting = SETTINGS[params.setting]
    problem = PROBLEMS[params.problem]
    prize = PRIZES[params.prize]
    fix = select_fix(problem, prize)
    if fix is None:
        raise StoryError("No sensible fix exists for that problem and prize.")
    world = tell(setting, problem, prize, fix, params.hero_name, params.helper_name, params.parent_name, params.hero_gender, params.helper_gender, params.parent_gender)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


CURATED = [
    StoryParams(setting="dock", problem="rope", prize="map", hero_name="Lily", hero_gender="girl", helper_name="Tom", helper_gender="boy", parent_name="Captain Mira", parent_gender="woman", trait="curious"),
    StoryParams(setting="deck", problem="mast", prize="flag", hero_name="Ben", hero_gender="boy", helper_name="Mia", helper_gender="girl", parent_name="Captain Mira", parent_gender="woman", trait="careful"),
    StoryParams(setting="cove", problem="plank", prize="chest", hero_name="Ava", hero_gender="girl", helper_name="Finn", helper_gender="boy", parent_name="Captain Mira", parent_gender="woman", trait="clever"),
    StoryParams(setting="island", problem="lamp", prize="lantern", hero_name="Noah", hero_gender="boy", helper_name="Ella", helper_gender="girl", parent_name="Captain Mira", parent_gender="woman", trait="kind"),
]


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
        print(asp_program("#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (setting, problem, prize) combos:\n")
        for row in combos:
            print("  ", row)
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
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.hero_name}: {p.problem} at {p.setting} (prize: {p.prize})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()

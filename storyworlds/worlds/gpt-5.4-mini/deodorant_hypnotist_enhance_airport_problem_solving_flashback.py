#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/deodorant_hypnotist_enhance_airport_problem_solving_flashback.py
================================================================================================

A standalone storyworld for a tiny airport myth about a lost traveler, a kindly
hypnotist, a forgotten deodorant stick, a flashback to a previous lesson, and a
shared solution that helps everyone board on time.

The story model keeps one small domain:
- an airport gate with a tense problem,
- a magical-but-child-friendly hypnotist who calms panic,
- a deodorant stick as a practical object that becomes useful in an odd way,
- a flashback that reveals why the hero knows what to do,
- sharing that turns a private fix into a group solution.

The world is built as a tiny classical simulation with typed entities, physical
meters, emotional memes, forward causal rules, a reasonableness gate, and an
inline ASP twin for parity checks.
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
class AirportSetting:
    id: str
    scene: str
    gate: str
    crowd: str
    myth_frame: str


@dataclass
class Tool:
    id: str
    label: str
    phrase: str
    use: str
    gives_off: str
    safe: bool = True
    tags: set[str] = field(default_factory=set)


@dataclass
class Problem:
    id: str
    label: str
    symptom: str
    cause: str
    risk: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Fix:
    id: str
    label: str
    action: str
    effect: str
    power: int
    sense: int
    shareable: bool = False
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


def _r_panic(world: World) -> list[str]:
    out = []
    for e in world.entities.values():
        if e.memes["panic"] >= THRESHOLD:
            if ("panic", e.id) not in world.fired:
                world.fired.add(("panic", e.id))
                e.memes["confusion"] += 1
                out.append("__panic__")
    return out


def _r_shared_relief(world: World) -> list[str]:
    out = []
    if world.facts.get("shared_help") and ("shared", "gate") not in world.fired:
        world.fired.add(("shared", "gate"))
        for e in world.entities.values():
            if e.kind == "character":
                e.memes["relief"] += 1
        out.append("__relief__")
    return out


CAUSAL_RULES = [Rule("panic", "social", _r_panic), Rule("shared", "social", _r_shared_relief)]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced = []
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


def reasonableness(problem: Problem, fix: Fix) -> bool:
    return fix.sense >= SENSE_MIN and fix.power >= 1 and problem.id in {"stuck_gate", "lost_token", "noisy_line"}


def best_fix() -> Fix:
    return max(FIXES.values(), key=lambda f: f.sense)


def solve_capacity(problem: Problem, delay: int) -> int:
    return 1 + delay if problem.id != "noisy_line" else 2 + delay


def can_solve(fix: Fix, problem: Problem, delay: int) -> bool:
    return fix.power >= solve_capacity(problem, delay)


def flashback(world: World, hero: Entity, guide: Entity, problem: Problem) -> None:
    hero.memes["memory"] += 1
    world.say(
        f"At the airport gate, {hero.id} remembered a time at a stone bridge shrine "
        f"when {guide.id} had taught {hero.pronoun('object')} to breathe slowly and look for a clue."
    )
    world.say(
        f"That old lesson came back like moonlight on water: when a path seems blocked, "
        f"the answer may be small, calm, and shared."
    )


def intro(world: World, setting: AirportSetting, hero: Entity, guide: Entity) -> None:
    world.say(
        f"At {setting.scene}, beneath the bright ceiling lamps of {setting.gate}, "
        f"{hero.id} and {guide.id} stood among the humming crowd. {setting.myth_frame}"
    )
    world.say(
        f'{hero.id} was a young traveler seeking a clear way forward, while {guide.id}, '
        f"a gentle hypnotist with a soft voice, watched the line with patient eyes."
    )


def problem_arises(world: World, hero: Entity, problem: Problem, tool: Tool) -> None:
    hero.memes["worry"] += 1
    hero.memes["panic"] += 1
    world.say(
        f"But the gatekeeper had stopped the line: {problem.symptom}. "
        f"{problem.cause.capitalize()}, and the whole crowd began to murmur."
    )
    world.say(
        f"{hero.id} reached into {hero.pronoun('possessive')} bag and found {tool.phrase}, "
        f"wondering if {tool.label} could somehow {tool.use} and ease the trouble."
    )


def hypnotize(world: World, guide: Entity, hero: Entity) -> None:
    guide.memes["calm"] += 1
    hero.memes["calm"] += 1
    world.say(
        f"{guide.id} lifted a hand and spoke like a shepherd of stars. "
        f'"Breathe in. Breathe out. Your mind can become quiet enough to see."'
    )
    world.say(
        f"The words did not erase the problem, but they did lower the storm inside {hero.id}."
    )


def examine(world: World, hero: Entity, problem: Problem, tool: Tool) -> None:
    hero.memes["curiosity"] += 1
    world.say(
        f"{hero.id} looked again and noticed a tiny sign beside the gate. "
        f"It showed that the trouble was not the line itself, but a lost luggage tag and a missing pen."
    )
    if tool.safe:
        world.say(
            f"That was when {hero.id} remembered that {tool.label} could do more than {tool.use}; "
            f"it could also help mark a shared paper so no one had to wait confused."
        )


def share_solution(world: World, hero: Entity, guide: Entity, problem: Problem, tool: Tool, fix: Fix) -> None:
    hero.memes["sharing"] += 1
    guide.memes["sharing"] += 1
    world.facts["shared_help"] = True
    world.say(
        f"{hero.id} held up the {tool.label} and shared it with the traveler behind {hero.id}. "
        f"Then {hero.id} and {guide.id} used {fix.action}, and the line began to move."
    )
    world.say(
        f"The little fix was not grand like thunder, yet it worked: {fix.effect}, "
        f"and the waiting people smiled as if a cloud had opened."
    )


def resolve(world: World, setting: AirportSetting, hero: Entity, guide: Entity, fix: Fix) -> None:
    hero.memes["joy"] += 1
    hero.memes["relief"] += 1
    guide.memes["joy"] += 1
    guide.memes["relief"] += 1
    world.say(
        f"At last, {setting.gate} felt bright again. {hero.id} walked on, calmer now, "
        f"and {guide.id} nodded as if an old spell had been completed the proper way."
    )
    world.say(
        f"The story ended with {hero.id} carrying {fix.label} in {hero.pronoun('possessive')} hand, "
        f"no longer a mystery but a useful gift shared at the right time."
    )


def tell(setting: AirportSetting, problem: Problem, tool: Tool, fix: Fix,
         hero_name: str = "Mira", hero_type: str = "girl",
         guide_name: str = "Sage", guide_type: str = "woman") -> World:
    world = World()
    hero = world.add(Entity(id=hero_name, kind="character", type=hero_type, role="traveler"))
    guide = world.add(Entity(id=guide_name, kind="character", type=guide_type, role="hypnotist"))
    gate = world.add(Entity(id="gate", type="place", label=setting.gate))

    intro(world, setting, hero, guide)
    world.para()
    problem_arises(world, hero, problem, tool)
    hypnotize(world, guide, hero)
    flashback(world, hero, guide, problem)
    examine(world, hero, problem, tool)

    world.para()
    if can_solve(fix, problem, delay=1):
        share_solution(world, hero, guide, problem, tool, fix)
        resolve(world, setting, hero, guide, fix)
    else:
        world.say(
            f"Even so, the trick was too small for the trouble, and the gate stayed closed."
        )
        world.say(
            f"But {guide.id} stayed calm, and together they found the airport desk that kept spare pens and tags."
        )
        world.say(
            f"After asking for help, the waiting line slowly unknotted."
        )

    world.facts.update(
        setting=setting, problem=problem, tool=tool, fix=fix,
        hero=hero, guide=guide, gate=gate, outcome="solved",
        shared_help=world.facts.get("shared_help", False),
    )
    return world


SETTINGS = {
    "airport": AirportSetting(
        "airport",
        "the airport",
        "Gate Seven",
        "a tide of suitcases and rolling shoes",
        "It felt like a temple of departures, where every traveler carried a small fate."
    )
}

TOOLS = {
    "deodorant": Tool(
        "deodorant",
        "deodorant",
        "a stick of deodorant",
        "cool a sweaty palm and help leave a clear mark on paper",
        "a clean, fresh scent",
        tags={"deodorant", "sharing"},
    ),
    "marker": Tool(
        "marker",
        "marker",
        "a blue marker",
        "write a name on a tag",
        "a bold blue line",
        tags={"sharing"},
    ),
    "token": Tool(
        "token",
        "token",
        "a silver travel token",
        "signal the right helper",
        "a bright little shine",
        tags={"myth"},
    ),
}

PROBLEMS = {
    "stuck_gate": Problem(
        "stuck_gate",
        "a stuck gate line",
        "the boarding line had frozen",
        "the scanner needed a fresh name on the tag",
        "the travelers were growing nervous",
        tags={"problem_solving"},
    ),
    "lost_token": Problem(
        "lost_token",
        "a lost boarding token",
        "the key token had vanished",
        "the desk could not match the bag to its owner",
        "the next flight was in danger of leaving without them",
        tags={"flashback"},
    ),
    "noisy_line": Problem(
        "noisy_line",
        "a noisy line",
        "children were calling out and the line had become a swirl of noise",
        "nobody knew who was next",
        "the gatekeeper could not keep order",
        tags={"sharing"},
    ),
}

FIXES = {
    "label_share": Fix(
        "label_share",
        "shared labeling",
        "write a name together on a shared tag",
        "the scanner could read the bag and the people behind could see the plan",
        power=3,
        sense=3,
        shareable=True,
        tags={"sharing", "problem_solving"},
    ),
    "desk_help": Fix(
        "desk_help",
        "desk help",
        "ask the airport desk for a spare pen and tag",
        "the desk could finish the task and the gate could open",
        power=4,
        sense=3,
        shareable=True,
        tags={"problem_solving"},
    ),
    "breath_reset": Fix(
        "breath_reset",
        "a calm breathing spell",
        "breathe slowly and wait for the next instruction",
        "the panic settled enough for everyone to think",
        power=1,
        sense=2,
        shareable=False,
        tags={"flashback"},
    ),
}

HERO_NAMES = ["Mira", "Nico", "Lina", "Arin", "Tavi", "Sora"]
GUIDE_NAMES = ["Sage", "Iris", "Mara", "Talon", "Neris"]
TRAITS = ["curious", "gentle", "patient", "thoughtful", "brave"]


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for sid in SETTINGS:
        for pid, problem in PROBLEMS.items():
            for tid, tool in TOOLS.items():
                if problem.id == "stuck_gate" and tid in {"deodorant", "marker"}:
                    combos.append((sid, pid, tid))
                elif problem.id == "lost_token" and tid in {"marker", "token"}:
                    combos.append((sid, pid, tid))
                elif problem.id == "noisy_line" and tid in {"marker", "deodorant"}:
                    combos.append((sid, pid, tid))
    return combos


@dataclass
class StoryParams:
    setting: str
    problem: str
    tool: str
    fix: str
    hero: str
    hero_gender: str
    guide: str
    guide_gender: str
    trait: str
    seed: Optional[int] = None


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    return [
        f'Write a mythic airport story for a child that includes the words "deodorant" and "hypnotist".',
        f"Tell a story where {hero.id} solves an airport problem with a small shared object and a calm hypnotist.",
        f"Write a myth-style problem-solving story in an airport, with a flashback and a sharing moment.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero, guide, problem, tool, fix = f["hero"], f["guide"], f["problem"], f["tool"], f["fix"]
    return [
        QAItem(
            question=f"What problem did {hero.id} face at the airport?",
            answer=f"{hero.id} faced {problem.label}. The trouble made the gate feel stuck, so everyone had to slow down and think."
        ),
        QAItem(
            question=f"How did {guide.id} help {hero.id}?",
            answer=f"{guide.id} helped by speaking calmly like a hypnotist and reminding {hero.id} to breathe. That calm made it easier to notice a small solution."
        ),
        QAItem(
            question="What did they share to solve the problem?",
            answer=f"They shared {tool.label} and used {fix.action}. Because they shared it, the fix helped the whole line instead of only one person."
        ),
        QAItem(
            question="Why was there a flashback in the story?",
            answer="The flashback showed an older lesson returning at the right moment. It explained why the hero knew to stay calm and look for a small useful clue."
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is deodorant?",
            answer="Deodorant is something people use to smell fresher. In stories, it can also become a handy small object for a practical fix."
        ),
        QAItem(
            question="What does a hypnotist do?",
            answer="A hypnotist uses calm words and focus to help someone pay attention and settle their thoughts. In a child story, that can feel magical without being scary."
        ),
        QAItem(
            question="What does enhance mean?",
            answer="Enhance means to make something better, stronger, or clearer. A small shared tool can enhance a plan by helping it work well."
        ),
        QAItem(
            question="What is sharing?",
            answer="Sharing means letting other people use or enjoy something with you. It often turns one person's idea into a solution that helps everyone."
        ),
        QAItem(
            question="What is an airport?",
            answer="An airport is a place where airplanes take off and land, and travelers wait at gates before their flights."
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("\n== story qa ==")
    for q in sample.story_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    lines.append("\n== world qa ==")
    for q in sample.world_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
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
        lines.append(f"  {e.id:10} ({e.type:8}) {' '.join(bits)}")
    return "\n".join(lines)


def explain_rejection(problem: Problem, tool: Tool) -> str:
    return f"(No story: {tool.label} does not fit that airport problem well enough to make a sensible mythic fix.)"


def explain_fix(fid: str) -> str:
    f = FIXES[fid]
    better = ", ".join(sorted(x.id for x in FIXES.values() if x.sense >= SENSE_MIN))
    return f"(Refusing fix '{fid}': sense={f.sense} < {SENSE_MIN}. Try: {better}.)"


ASP_RULES = r"""
valid(S,P,T) :- setting(S), problem(P), tool(T), fit(P,T).
sensible(F) :- fix(F), sense(F, N), sense_min(M), N >= M.
solved(P,F) :- problem(P), fix(F), power(F, Pow), capacity(P, Need), Pow >= Need.
fit(stuck_gate, deodorant).
fit(stuck_gate, marker).
fit(lost_token, marker).
fit(lost_token, token).
fit(noisy_line, marker).
fit(noisy_line, deodorant).
"""


def asp_facts() -> str:
    import asp
    lines = [asp.fact("setting", sid) for sid in SETTINGS]
    for pid, p in PROBLEMS.items():
        lines.append(asp.fact("problem", pid))
        lines.append(asp.fact("capacity", pid, 1 if pid == "stuck_gate" else 2))
    for tid, t in TOOLS.items():
        lines.append(asp.fact("tool", tid))
    for fid, f in FIXES.items():
        lines.append(asp.fact("fix", fid))
        lines.append(asp.fact("sense", fid, f.sense))
        lines.append(asp.fact("power", fid, f.power))
    lines.append(asp.fact("sense_min", SENSE_MIN))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_sensible() -> list[str]:
    import asp
    model = asp.one_model(asp_program("", "#show sensible/1."))
    return sorted(v for (v,) in asp.atoms(model, "sensible"))


def asp_verify() -> int:
    import io
    import contextlib
    rc = 0
    if set(asp_valid_combos()) != set(valid_combos()):
        print("MISMATCH in valid combos.")
        rc = 1
    if set(asp_sensible()) != set(f.id for f in FIXES.values() if f.sense >= SENSE_MIN):
        print("MISMATCH in sensible fixes.")
        rc = 1
    try:
        sample = generate(resolve_params(argparse.Namespace(setting=None, problem=None, tool=None, fix=None, hero=None, hero_gender=None, guide=None, guide_gender=None, trait=None), random.Random(7)))
        _ = sample.story
    except Exception as e:
        print(f"SMOKE TEST FAILED: {e}")
        return 1
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        emit(sample, trace=True, qa=True)
    print("OK: verify smoke test passed.")
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Mythic airport storyworld with deodorant, hypnotist, enhance, flashback, and sharing.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--problem", choices=PROBLEMS)
    ap.add_argument("--tool", choices=TOOLS)
    ap.add_argument("--fix", choices=FIXES)
    ap.add_argument("--hero")
    ap.add_argument("--hero-gender", choices=["girl", "boy"])
    ap.add_argument("--guide")
    ap.add_argument("--guide-gender", choices=["woman", "man"])
    ap.add_argument("--trait", choices=TRAITS)
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
    combos = [c for c in valid_combos()
              if (args.setting is None or c[0] == args.setting)
              and (args.problem is None or c[1] == args.problem)
              and (args.tool is None or c[2] == args.tool)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    setting, problem, tool = rng.choice(sorted(combos))
    fix = args.fix or rng.choice(sorted(f.id for f in FIXES.values() if f.sense >= SENSE_MIN))
    if not reasonableness(PROBLEMS[problem], FIXES[fix]):
        raise StoryError(explain_fix(fix))
    hero_gender = args.hero_gender or rng.choice(["girl", "boy"])
    guide_gender = args.guide_gender or rng.choice(["woman", "man"])
    hero = args.hero or rng.choice(HERO_NAMES)
    guide = args.guide or rng.choice(GUIDE_NAMES)
    trait = args.trait or rng.choice(TRAITS)
    return StoryParams(setting, problem, tool, fix, hero, hero_gender, guide, guide_gender, trait)


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.setting], PROBLEMS[params.problem], TOOLS[params.tool], FIXES[params.fix], params.hero, params.hero_gender, params.guide, params.guide_gender)
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
    StoryParams("airport", "stuck_gate", "deodorant", "label_share", "Mira", "girl", "Sage", "woman", "curious"),
    StoryParams("airport", "lost_token", "marker", "desk_help", "Nico", "boy", "Mara", "woman", "patient"),
    StoryParams("airport", "noisy_line", "marker", "label_share", "Lina", "girl", "Talon", "man", "thoughtful"),
]


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("", "#show valid/3.\n#show sensible/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"sensible fixes: {', '.join(asp_sensible())}")
        for row in asp_valid_combos():
            print(row)
        return
    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 20):
            try:
                p = resolve_params(args, random.Random(base_seed + i))
            except StoryError as e:
                print(e)
                return
            p.seed = base_seed + i
            samples.append(generate(p))
            i += 1
    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return
    for i, s in enumerate(samples):
        emit(s, trace=args.trace, qa=args.qa, header=(f"### variant {i+1}" if len(samples) > 1 else ""))
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()

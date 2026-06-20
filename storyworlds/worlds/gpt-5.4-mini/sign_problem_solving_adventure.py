#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/sign_problem_solving_adventure.py
==================================================================

A small standalone storyworld for an adventure about finding and fixing a sign.
The domain is kid-sized and classical: a child explorer reaches a trail sign that
has fallen, learns what it should say, solves the problem with a careful plan,
and ends with a clear image proving the path is set right again.

The world model is state-driven. Typed entities carry physical meters and
emotional memes; rules update the world as the adventure unfolds. The story can
end in two plausible ways:

* **fixed**: the children repair the sign before the trail confuses anyone.
* **blocked**: the sign is too broken for a simple fix, so they call a ranger
  and keep the trail safe another way.

This script follows the Storyweavers world contract:
- stdlib-only and standalone
- imports storyworlds/results.py eagerly
- provides StoryParams, build_parser, resolve_params, generate, emit, main
- supports --all, -n, --seed, --trace, --qa, --json, --asp, --verify, --show-asp
- includes a Python reasonableness gate and inline ASP twin
- produces prompts, story-grounded QA, and world-knowledge QA from world state
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
class Setting:
    id: str
    place: str
    path: str
    terrain: str
    landmark: str
    sign_kind: str
    adventure_word: str


@dataclass
class Sign:
    id: str
    label: str
    kind: str
    message: str
    support: str
    broken_state: str
    fixed_state: str
    weathering: int = 1
    repairable: bool = True


@dataclass
class Tool:
    id: str
    label: str
    phrase: str
    use: str
    power: int
    sense: int
    tags: set[str] = field(default_factory=set)


@dataclass
class Solution:
    id: str
    label: str
    sense: int
    power: int
    text: str
    fail: str
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


def _r_scatter(world: World) -> list[str]:
    out: list[str] = []
    sign = world.entities.get("sign")
    if not sign:
        return out
    if sign.meters["wobble"] < THRESHOLD:
        return out
    sig = ("scatter", sign.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    world.get("path").meters["confusion"] += 1
    world.get("hero").memes["concern"] += 1
    out.append("__scatter__")
    return out


def _r_repair_ready(world: World) -> list[str]:
    out: list[str] = []
    tool = world.entities.get("tool")
    sign = world.entities.get("sign")
    if not tool or not sign:
        return out
    if sign.meters["wobble"] < THRESHOLD:
        return out
    if tool.meters["use"] < THRESHOLD:
        return out
    sig = ("ready", tool.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    world.get("hero").memes["hope"] += 1
    out.append("__ready__")
    return out


CAUSAL_RULES = [
    Rule("scatter", "physical", _r_scatter),
    Rule("repair_ready", "social", _r_repair_ready),
]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            out = rule.apply(world)
            if out:
                changed = True
                produced.extend(s for s in out if not s.startswith("__"))
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def sign_at_risk(sign: Sign) -> bool:
    return sign.repairable and sign.kind in {"trail", "camp", "bridge", "map"}


def sensible_solutions() -> list[Solution]:
    return [s for s in SOLUTIONS.values() if s.sense >= 2]


def firelike_effort(solution: Solution, sign: Sign, delay: int) -> int:
    return sign.weathering + delay


def can_fix(solution: Solution, sign: Sign, delay: int) -> bool:
    return solution.power >= firelike_effort(solution, sign, delay)


def predict_problem(world: World, sign_id: str, tool_id: str) -> dict:
    sim = world.copy()
    _do_attempt(sim, sim.get(sign_id), sim.get(tool_id), narrate=False)
    return {
        "wobble": sim.get(sign_id).meters["wobble"],
        "confusion": sim.get("path").meters["confusion"],
        "hope": sim.get("hero").memes["hope"],
    }


def _do_attempt(world: World, sign: Entity, tool: Entity, narrate: bool = True) -> None:
    sign.meters["wobble"] += 1
    sign.meters["broken"] += 1
    tool.meters["use"] += 1
    propagate(world, narrate=narrate)


def setup(world: World, hero: Entity, helper: Entity, setting: Setting) -> None:
    hero.memes["curiosity"] += 1
    helper.memes["calm"] += 1
    world.say(
        f"On a bright adventure morning, {hero.id} and {helper.id} followed "
        f"{setting.place} along {setting.path}. {setting.terrain.capitalize()} "
        f"flanked the trail, and a small {setting.sign_kind} stood ahead near {setting.landmark}."
    )
    world.say(
        f"{hero.id} loved how every turn in the trail felt like a new quest, "
        f"and {helper.id} liked solving little problems before they grew big."
    )


def notice_problem(world: World, hero: Entity, sign: Sign, setting: Setting) -> None:
    world.say(
        f"Then they saw the sign lean sideways. One edge was cracked, and its "
        f"{sign.label} looked too hard to read from the path."
    )
    world.say(
        f'"The map says this way," {hero.id} said, peering at the bent boards. '
        f'"But the sign is telling a messy story."'
    )


def plan(world: World, helper: Entity, hero: Entity, tool: Tool, sign: Sign) -> None:
    pred = predict_problem(world, "sign", "tool")
    world.facts["predicted_confusion"] = pred["confusion"]
    world.facts["predicted_hope"] = pred["hope"]
    world.say(
        f'{helper.id} knelt beside the trail and pointed to the crack. '
        f'"We can solve this," {helper.pronoun()} said. '
        f'"First we need a safe way to hold it steady."'
    )
    world.say(
        f'{hero.id} held up {tool.phrase} and listened carefully. '
        f'"We can {tool.use} it," {hero.pronoun()} said, "and then the sign can stand again."'
    )


def try_bad_idea(world: World, hero: Entity, bad: str) -> None:
    hero.memes["bravado"] += 1
    world.say(
        f'For a second, {hero.id} thought about {bad}, but the trail was too '
        f"important for a guess that might make things worse."
    )


def do_fix(world: World, helper: Entity, hero: Entity, sign: Sign, tool: Tool, solution: Solution) -> None:
    sign.meters["wobble"] = 0.0
    sign.meters["fixed"] += 1
    world.get("path").meters["confusion"] = 0.0
    world.say(
        f"{helper.id} used {tool.phrase} to {tool.use} the sign upright, and "
        f"{hero.id} held the post steady while it was secured."
    )
    world.say(
        f"In a moment, the {solution.label} worked. The {sign.label} stood straight "
        f"again, and the trail read clearly from far away."
    )


def call_ranger(world: World, hero: Entity, helper: Entity, sign: Sign) -> None:
    world.say(
        f"The crack was too deep for a quick fix, so {hero.id} waved to a ranger "
        f"on the ridge while {helper.id} kept the trail calm."
    )
    world.say(
        f"The ranger brought a proper brace, and soon the {sign.label} was safe "
        f"again for every hiker who came by."
    )


def ending(world: World, hero: Entity, helper: Entity, setting: Setting, sign: Sign) -> None:
    if sign.meters["fixed"] >= THRESHOLD:
        world.say(
            f"By the end, the sign pointed the right way, the trail was easy to read, "
            f"and {hero.id} grinned at the tiny problem they had solved together."
        )
    else:
        world.say(
            f"By the end, the path was safe, the sign had been repaired by a grown-up, "
            f"and {hero.id} and {helper.id} kept walking with a clear way ahead."
        )


def tell(setting: Setting, sign_def: Sign, tool: Tool, solution: Solution,
         hero_name: str = "Mina", helper_name: str = "Pip",
         hero_gender: str = "girl", helper_gender: str = "boy",
         delay: int = 0, break_level: int = 1) -> World:
    world = World()
    hero = world.add(Entity(id=hero_name, kind="character", type=hero_gender, role="hero"))
    helper = world.add(Entity(id=helper_name, kind="character", type=helper_gender, role="helper"))
    sign = world.add(Entity(id="sign", type="sign", label=sign_def.label))
    path = world.add(Entity(id="path", type="path", label="the path"))
    tool_ent = world.add(Entity(id="tool", type="tool", label=tool.label))
    sign.meters["break"] = float(break_level)
    world.facts["setting"] = setting
    world.facts["tool"] = tool_ent
    world.facts["solution"] = solution
    world.facts["sign_def"] = sign_def
    world.facts["delay"] = delay

    setup(world, hero, helper, setting)
    world.para()
    notice_problem(world, hero, sign_def, setting)
    plan(world, helper, hero, tool, sign_def)
    try_bad_idea(world, hero, "walking on and hoping the trail would fix itself")
    world.para()
    if can_fix(solution, sign_def, delay):
        _do_attempt(world, sign, tool_ent)
        do_fix(world, helper, hero, sign_def, tool, solution)
        sign.meters["fixed"] += 1
        outcome = "fixed"
    else:
        _do_attempt(world, sign, tool_ent)
        call_ranger(world, hero, helper, sign_def)
        outcome = "blocked"
    world.para()
    ending(world, hero, helper, setting, sign_def)
    world.facts.update(hero=hero, helper=helper, sign=sign, path=path, outcome=outcome)
    return world


SETTINGS = {
    "forest": Setting("forest", "the forest trail", "the winding path", "pine trees",
                      "wooden trail sign", "adventure"),
    "canyon": Setting("canyon", "the canyon path", "the narrow trail", "red cliffs",
                      "stone trail sign", "adventure"),
    "harbor": Setting("harbor", "the harbor walk", "the dock path", "salt air",
                      "post sign", "adventure"),
}

SIGNS = {
    "forest_sign": Sign("forest_sign", "trail sign", "trail sign",
                        "pointing to the camp", "steady post", "cracked and tilted",
                        "straight and clear", weathering=2, repairable=True),
    "canyon_sign": Sign("canyon_sign", "direction sign", "direction sign",
                        "showing the safe turn", "rock base", "splintered",
                        "firm and visible", weathering=3, repairable=True),
    "harbor_sign": Sign("harbor_sign", "dock sign", "dock sign",
                        "marking the way to the boat launch", "metal pole",
                        "bent and hard to read", "upright and bright", weathering=1, repairable=True),
}

TOOLS = {
    "rope": Tool("rope", "rope", "rope", "tie it tight", 2, 2, {"rope", "repair"}),
    "hammer": Tool("hammer", "hammer and nails", "hammer and nails", "nail the board back", 3, 3, {"repair"}),
    "brace": Tool("brace", "wooden brace", "wooden brace", "brace the post", 4, 3, {"repair"}),
}

SOLUTIONS = {
    "rope": Solution("rope", "rope", 2, 2, "tied the sign tight with rope", "tried to tie the sign, but it kept slipping", {"rope"}),
    "hammer": Solution("hammer", "hammer", 3, 3, "nailed the board back into place", "tried to hammer it, but the crack was too loose", {"hammer"}),
    "brace": Solution("brace", "brace", 4, 4, "used a wooden brace to hold the post straight", "used a brace, but the sign was too damaged", {"brace"}),
}

HEROES = ["Mina", "Tess", "Ari", "Jude", "Nora", "Finn"]
HELPERS = ["Pip", "Kai", "Luca", "Wren", "Milo", "June"]
TRAITS = ["careful", "curious", "brave", "thoughtful", "patient"]


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for sid, sign in SIGNS.items():
        if not sign_at_risk(sign):
            continue
        for tid, tool in TOOLS.items():
            for sol in SOLUTIONS.values():
                if sol.sense >= 2 and tool.sense >= 2:
                    combos.append((sid, tid, sol.id))
    return combos


@dataclass
class StoryParams:
    setting: str
    sign: str
    tool: str
    solution: str
    hero: str
    helper: str
    delay: int = 0
    break_level: int = 1
    seed: Optional[int] = None


KNOWLEDGE = {
    "sign": [("What is a sign?", "A sign is something that gives information, like directions or a warning. Signs help people know where to go.")],
    "trail": [("Why are trail signs useful?", "Trail signs show the safe path and help hikers avoid getting lost. They turn a confusing place into a clear one.")],
    "rope": [("What can rope be used for?", "Rope can tie things together or hold something steady. People use it to help fix or secure things.")],
    "brace": [("What does a brace do?", "A brace helps support something so it stays upright and steady. It is useful when a post or board is weak.")],
    "hammer": [("What do hammer and nails do?", "A hammer and nails can fasten a board in place. They help make a repair hold firmly.")],
    "ranger": [("Who helps on trails?", "A ranger helps keep trails safe and can fix problems in parks and forests. Rangers know how to handle tricky situations.")],
}
KNOWLEDGE_ORDER = ["sign", "trail", "rope", "hammer", "brace", "ranger"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    setting = f["setting"]
    return [
        f'Write an adventure story for a young child about finding a broken sign on {setting.place}.',
        f"Tell a problem-solving story where {f['hero'].id} and {f['helper'].id} repair a sign so the trail makes sense again.",
        f'Write a child-friendly adventure that includes the word "sign" and ends with a clear path forward.',
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    hero, helper, sign = f["hero"], f["helper"], f["sign"]
    setting = f["setting"]
    solution = f["solution"]
    qa = [
        ("Where were the children?",
         f"They were on {setting.place}, following {setting.path} near {setting.landmark}."),
        ("What problem did they find?",
         f"They found a bent sign that was hard to read, so the trail felt confusing."),
        ("How did they work together?",
         f"{helper.id} made a plan, and {hero.id} held the sign steady while the fix was done."),
    ]
    if f["outcome"] == "fixed":
        qa.append((
            "How was the problem solved?",
            f"They used {solution.label} to repair the sign, and that made the trail clear again. "
            f"The sign stood straight, so the adventure could continue safely."
        ))
    else:
        qa.append((
            "How was the problem solved?",
            f"The sign was too damaged for the quick fix, so they called a ranger. "
            f"The ranger brought a better repair, which kept the trail safe."
        ))
    qa.append((
        "How did the story end?",
        f"It ended with the sign readable again and the path easy to follow. "
        f"{hero.id} could keep adventuring without guessing where to go."
    ))
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags = {"sign", "trail", "ranger"}
    if world.facts["solution"].id == "rope":
        tags.add("rope")
    elif world.facts["solution"].id == "hammer":
        tags.add("hammer")
    else:
        tags.add("brace")
    out = []
    for tag in KNOWLEDGE_ORDER:
        if tag in tags:
            out.extend(KNOWLEDGE[tag])
    return out


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
        if e.attrs:
            bits.append(f"attrs={e.attrs}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams("forest", "forest_sign", "rope", "rope", "Mina", "Pip", 0, 1),
    StoryParams("canyon", "canyon_sign", "hammer", "hammer", "Ari", "Wren", 0, 2),
    StoryParams("harbor", "harbor_sign", "brace", "brace", "Nora", "Kai", 1, 3),
]


def explain_rejection(sign: Sign) -> str:
    if not sign_at_risk(sign):
        return "(No story: this sign is too ordinary for an adventure problem.)"
    return "(No story: the chosen sign cannot drive a useful problem-solving adventure.)"


def outcome_of(params: StoryParams) -> str:
    return "fixed" if can_fix(SOLUTIONS[params.solution], SIGNS[params.sign], params.delay) else "blocked"


def explain_solution(rid: str) -> str:
    r = SOLUTIONS[rid]
    better = " / ".join(sorted(s.id for s in sensible_solutions()))
    return f"(Refusing solution '{rid}': it scores too low on common sense (sense={r.sense}); try: {better}.)"


ASP_RULES = r"""
sign_at_risk(S) :- sign(S).
sensible(Sol) :- solution(Sol), sense(Sol, N), sense_min(M), N >= M.
can_fix(Sol, S) :- solution(Sol), sign(S), power(Sol, P), weathering(S, W), delay(D), P >= W + D.
outcome(fixed) :- chosen_sign(S), chosen_solution(Sol), can_fix(Sol, S).
outcome(blocked) :- chosen_sign(S), chosen_solution(Sol), not can_fix(Sol, S).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for sid, s in SIGNS.items():
        lines.append(asp.fact("sign", sid))
        lines.append(asp.fact("weathering", sid, s.weathering))
    for tid, t in TOOLS.items():
        lines.append(asp.fact("tool", tid))
        lines.append(asp.fact("sense", tid, t.sense))
    for sid, s in SOLUTIONS.items():
        lines.append(asp.fact("solution", sid))
        lines.append(asp.fact("sense", sid, s.sense))
        lines.append(asp.fact("power", sid, s.power))
    lines.append(asp.fact("sense_min", 2))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_sensible() -> list[str]:
    import asp
    model = asp.one_model(asp_program("", "#show sensible/1."))
    return sorted(x for (x,) in asp.atoms(model, "sensible"))


def asp_outcome(params: StoryParams) -> str:
    import asp
    extra = "\n".join([
        asp.fact("chosen_sign", params.sign),
        asp.fact("chosen_solution", params.solution),
        asp.fact("delay", params.delay),
    ])
    model = asp.one_model(asp_program(extra, "#show outcome/1."))
    atoms = asp.atoms(model, "outcome")
    return atoms[0][0] if atoms else "?"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show can_fix/2."))
    return sorted(set(asp.atoms(model, "can_fix")))


def asp_verify() -> int:
    rc = 0
    p = set((s, sol) for s, _, sol in valid_combos())
    c = set(asp_valid_combos())
    if c == p:
        print(f"OK: gate matches valid_combos() ({len(c)} combos).")
    else:
        rc = 1
        print("MISMATCH in the gate:")
        print("  only in clingo:", sorted(c - p))
        print("  only in python:", sorted(p - c))
    if set(asp_sensible()) == {s.id for s in sensible_solutions()}:
        print("OK: sensible solutions match.")
    else:
        rc = 1
        print("MISMATCH in sensible solutions.")
    smoke = []
    for pz in CURATED:
        smoke.append(generate(pz))
    if not all(s.story for s in smoke):
        rc = 1
        print("MISMATCH: smoke generate failed.")
    else:
        print(f"OK: generate smoke-tested on {len(smoke)} curated stories.")
    if any(asp_outcome(pz) != outcome_of(pz) for pz in CURATED):
        rc = 1
        print("MISMATCH: ASP outcome differs from Python.")
    else:
        print("OK: ASP outcomes match Python on curated stories.")
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Adventure storyworld about problem-solving around a sign.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--sign", choices=SIGNS)
    ap.add_argument("--tool", choices=TOOLS)
    ap.add_argument("--solution", choices=SOLUTIONS)
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
    if args.sign and args.sign in SIGNS and not sign_at_risk(SIGNS[args.sign]):
        raise StoryError(explain_rejection(SIGNS[args.sign]))
    if args.solution and SOLUTIONS[args.solution].sense < 2:
        raise StoryError(explain_solution(args.solution))
    sign_id = args.sign or rng.choice(list(SIGNS))
    tool_id = args.tool or rng.choice(list(TOOLS))
    sol_id = args.solution or rng.choice(list(SOLUTIONS))
    if args.sign and args.solution:
        if not can_fix(SOLUTIONS[sol_id], SIGNS[sign_id], 0):
            raise StoryError("(No valid combination matches the given options.)")
    if args.setting:
        setting = args.setting
    else:
        setting = rng.choice(list(SETTINGS))
    hero = rng.choice(HEROES)
    helper = rng.choice([h for h in HELPERS if h != hero])
    delay = 0 if args.solution != "brace" else rng.randint(0, 1)
    break_level = rng.randint(1, 3)
    return StoryParams(setting, sign_id, tool_id, sol_id, hero, helper, delay, break_level)


def generate(params: StoryParams) -> StorySample:
    world = tell(
        SETTINGS[params.setting],
        SIGNS[params.sign],
        TOOLS[params.tool],
        SOLUTIONS[params.solution],
        params.hero,
        params.helper,
        delay=params.delay,
        break_level=params.break_level,
    )
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
        print(asp_program("", "#show can_fix/2.\n#show sensible/1.\n#show outcome/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"sensible solutions: {', '.join(asp_sensible())}\n")
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible sign+solution pairs:\n")
        for s, sol in combos:
            print(f"  {s:12} {sol}")
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
            header = f"### {p.hero} and {p.helper}: {p.sign} via {p.solution} ({outcome_of(p)})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()

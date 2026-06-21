#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/prowl_babble_problem_solving_adventure.py
=========================================================================

A small adventure storyworld about a child who goes on a prowl, hears a babble,
and solves a problem with a clever, concrete plan.

The world is built around a tiny treasure-search adventure:
- The child and a companion prowl through a place.
- A babble from a hidden helper or creature hints at a problem.
- The child notices a blockage, clue, or missing item.
- The child solves it with a tool, helper, or simple action.
- The ending proves the change by showing the path open, the helper calm, or the
  prize recovered.

This script follows the Storyweavers world contract:
- typed entities with physical meters and emotional memes
- state-driven prose, not frozen template swapping
- a Python reasonableness gate and an inline ASP twin
- three Q&A sets grounded in simulated state
- CLI support for default generation, --all, --seed, --trace, --qa, --json,
  --asp, --verify, and --show-asp
"""

from __future__ import annotations

import argparse
import copy
import json
import os
import random
import sys
from collections import defaultdict
from dataclasses import dataclass, field, asdict
from typing import Callable, Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from results import QAItem, StoryError, StorySample  # noqa: E402

THRESHOLD = 1.0
HERO_NAMES = ["Mina", "Toby", "Lina", "Arlo", "Nina", "Jasper", "Maya", "Pip"]
COMPANION_NAMES = ["Bea", "Rin", "Ollie", "Tessa", "Kai", "June", "Zed", "Nia"]


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    role: str = ""
    attrs: dict = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "woman"}
        male = {"boy", "father", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return self.label or self.id


@dataclass
class Setting:
    id: str
    place: str
    scene: str
    dark_spot: str
    adventure_image: str


@dataclass
class Problem:
    id: str
    label: str
    clue_sound: str
    block: str
    source: str
    risk: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Tool:
    id: str
    label: str
    helps: set[str]
    text: str
    tags: set[str] = field(default_factory=set)


@dataclass
class SolveMove:
    id: str
    sense: int
    power: int
    text: str
    fail: str
    qa_text: str
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
        return clone


@dataclass
class Rule:
    name: str
    tag: str
    apply: Callable[[World], list[str]]


def _r_noise(world: World) -> list[str]:
    out: list[str] = []
    for ent in world.entities.values():
        if ent.meters["bother"] < THRESHOLD:
            continue
        sig = ("noise", ent.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        for kid in [e for e in world.entities.values() if e.role in {"hero", "companion"}]:
            kid.memes["alert"] += 1
        out.append("__noise__")
    return out


def _r_calm(world: World) -> list[str]:
    out: list[str] = []
    if world.facts.get("solved"):
        for kid in [e for e in world.entities.values() if e.role in {"hero", "companion"}]:
            if kid.memes["relief"] < THRESHOLD:
                kid.memes["relief"] += 1
        out.append("__calm__")
    return out


CAUSAL_RULES = [Rule("noise", "social", _r_noise), Rule("calm", "social", _r_calm)]


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


def hazard(problem: Problem, tool: Tool) -> bool:
    return problem.id in tool.helps


def sensible_moves() -> list[SolveMove]:
    return [m for m in MOVES.values() if m.sense >= 2]


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for sid in SETTINGS:
        for pid, problem in PROBLEMS.items():
            for tid, tool in TOOLS.items():
                if hazard(problem, tool):
                    combos.append((sid, pid, tid))
    return combos


@dataclass
class StoryParams:
    setting: str
    problem: str
    tool: str
    move: str
    hero: str
    hero_gender: str
    companion: str
    companion_gender: str
    seed: Optional[int] = None


SETTINGS = {
    "ruins": Setting("ruins", "the old ruins", "a ruin path with stone arches",
                     "a blocked archway", "moonlight on the stones"),
    "cove": Setting("cove", "the hidden cove", "a cove path with shells and reeds",
                    "a reed-choked tunnel", "waves silvering the water"),
    "garden": Setting("garden", "the lantern garden", "a garden path under vines",
                      "a vine-tangled gate", "lantern light on leaves"),
}

PROBLEMS = {
    "gate_jam": Problem("gate_jam", "the jammed gate", "creak-babble", "stuck gate",
                        "a rusted latch", "they cannot pass through", {"gate", "metal"}),
    "riddle_stream": Problem("riddle_stream", "the babbling stream", "babble-babble",
                             "splashing stream", "a fallen sign", "their map gets confusing",
                             {"water", "stream"}),
    "root_snarl": Problem("root_snarl", "the root snarl", "murmur-babble",
                          "root snarl", "a knot of roots", "the trail vanishes",
                          {"roots", "trail"}),
}

TOOLS = {
    "rope": Tool("rope", "a rope", {"gate_jam", "root_snarl"},
                 "tied the rope to the gate and pulled it open",
                 {"rope"}),
    "stick": Tool("stick", "a sturdy stick", {"root_snarl", "riddle_stream"},
                  "used the stick to lever the roots aside and point at the sign",
                  {"stick"}),
    "lantern": Tool("lantern", "a lantern", {"riddle_stream"},
                    "lifted the lantern high so the sign could be read",
                    {"light"}),
    "oil": Tool("oil", "a small bottle of oil", {"gate_jam"},
                "oiled the latch until it loosened with a soft click",
                {"oil"}),
}

MOVES = {
    "pry": SolveMove("pry", 3, 3,
                     "pried the gate until it swung open",
                     "pried at it, but the gate stayed jammed",
                     "pried the gate open"),
    "oil": SolveMove("oil", 3, 4,
                     "oiled the latch and opened the way",
                     "oiled it, but the rust won",
                     "oiled the latch and opened the way"),
    "lift": SolveMove("lift", 2, 2,
                      "lifted the lantern and read the sign clearly",
                      "lifted the lantern, but the dark still hid the words",
                      "lifted the lantern and made the path clear"),
    "push": SolveMove("push", 2, 2,
                      "pushed the roots aside and found the trail",
                      "pushed, but the roots still knotted the path",
                      "pushed the roots aside and found the trail"),
}

GENDER_NAMES = {"girl": HERO_NAMES, "boy": COMPANION_NAMES}


def explain_rejection(problem: Problem, tool: Tool) -> str:
    return f"(No story: {tool.label} does not help with {problem.label}, so there is no honest problem-solving path.)"


def outcome_of(params: StoryParams) -> str:
    return "solved" if hazard(PROBLEMS[params.problem], TOOLS[params.tool]) and params.move in MOVES else "unsolved"


ASP_RULES = r"""
hazard(P,T) :- problem(P), tool(T), helps(T,P).
valid(S,P,T) :- setting(S), problem(P), tool(T), hazard(P,T).
solved :- chosen_problem(P), chosen_tool(T), chosen_move(M), hazard(P,T), move(M).
"""


def asp_facts() -> str:
    import storyworlds.asp as asp
    lines = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for pid in PROBLEMS:
        lines.append(asp.fact("problem", pid))
    for tid, t in TOOLS.items():
        lines.append(asp.fact("tool", tid))
        for p in t.helps:
            lines.append(asp.fact("helps", tid, p))
    for mid in MOVES:
        lines.append(asp.fact("move", mid))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import storyworlds.asp as asp
    model = asp.one_model(asp_program("", "#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    rc = 0
    if set(asp_valid_combos()) == set(valid_combos()):
        print(f"OK: ASP matches valid_combos() ({len(valid_combos())} combos).")
    else:
        rc = 1
        print("MISMATCH between ASP and Python gate.")
    try:
        sample = generate(resolve_params(build_parser().parse_args([]), random.Random(777)))
        assert sample.story
        print("OK: generate smoke test passed.")
    except Exception as exc:
        rc = 1
        print(f"SMOKE TEST FAILED: {exc}")
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Adventure storyworld: prowl, babble, solve.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--problem", choices=PROBLEMS)
    ap.add_argument("--tool", choices=TOOLS)
    ap.add_argument("--move", choices=MOVES)
    ap.add_argument("--hero")
    ap.add_argument("--hero-gender", choices=["girl", "boy"])
    ap.add_argument("--companion")
    ap.add_argument("--companion-gender", choices=["girl", "boy"])
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
              and (args.tool is None or c[2] == args.tool)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    setting, problem, tool = rng.choice(sorted(combos))
    move = args.move or rng.choice(sorted(MOVES))
    if problem == "gate_jam" and move == "lift":
        raise StoryError(explain_rejection(PROBLEMS[problem], TOOLS[tool]))
    hg = args.hero_gender or rng.choice(["girl", "boy"])
    cg = args.companion_gender or ("boy" if hg == "girl" else "girl")
    hero = args.hero or rng.choice(GENDER_NAMES[hg])
    companion = args.companion or rng.choice(GENDER_NAMES[cg])
    return StoryParams(setting=setting, problem=problem, tool=tool, move=move,
                       hero=hero, hero_gender=hg, companion=companion,
                       companion_gender=cg)


def _do_problem(world: World, problem: Problem) -> None:
    world.get("problem").meters["bother"] += 1
    world.say(f"In the dark, {problem.label} gave off a {problem.clue_sound} sound.")
    world.say(f"It felt like a clue waiting to be solved.")


def tell(setting: Setting, problem: Problem, tool: Tool, move: SolveMove,
         hero: str, hero_gender: str, companion: str, companion_gender: str) -> World:
    world = World()
    h = world.add(Entity(id=hero, kind="character", type=hero_gender, role="hero"))
    c = world.add(Entity(id=companion, kind="character", type=companion_gender, role="companion"))
    p = world.add(Entity(id="problem", label=problem.label, role="problem"))
    h.memes["curious"] = 1
    c.memes["curious"] = 1
    world.say(f"{h.id} and {c.id} set out to prowl through {setting.place}.")
    world.say(f"{setting.scene}. {setting.adventure_image}.")
    world.para()
    _do_problem(world, problem)
    world.say(f"{c.id} heard the {problem.clue_sound} and babbled, 'Listen! That sound means something is stuck.'")
    world.say(f"{h.id} looked closer and saw {problem.source}.")
    world.para()
    h.memes["worry"] += 1
    world.say(f'"We can fix this," {h.id} said, and got ready with {tool.label}.')
    if hazard(problem, tool):
        world.facts["solved"] = True
        world.say(f"Together they {move.text}.")
        world.say(f"The {problem.block} opened, and the path was clear again.")
        world.say(f"They walked on, with the hidden way shining ahead of them.")
    else:
        world.say(f"They tried to solve it, but nothing changed.")
    world.facts.update(hero=h, companion=c, setting=setting, problem=problem, tool=tool, move=move)
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f"Write an adventure story that includes the words prowl and babble, where {f['hero'].id} and {f['companion'].id} solve a problem in {f['setting'].place}.",
        f"Tell a child-friendly problem-solving adventure about {f['problem'].label} and a helpful tool like {f['tool'].label}.",
        f"Write a short exploratory story where a clue sounds like a babble and the characters prowl until they fix the trouble.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    return [
        QAItem(question="Who went on the adventure?",
               answer=f"{f['hero'].id} and {f['companion'].id} went together to explore {f['setting'].place}."),
        QAItem(question="What problem did they find?",
               answer=f"They found {f['problem'].label}, and it made a noisy clue that helped them notice what was wrong."),
        QAItem(question="How did they solve it?",
               answer=f"They used {f['tool'].label} and worked together, which opened the way and showed that the problem was fixed."),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(question="What does it mean to prowl?",
               answer="To prowl means to move slowly and carefully while looking around for something."),
        QAItem(question="What does babble sound like?",
               answer="Babble sounds like quick, chattery, messy talking or a noisy little stream of sound."),
        QAItem(question="Why is it good to solve a problem carefully?",
               answer="Careful solving helps people choose the right tool and avoid making the trouble worse."),
    ]


def format_qa(sample: StorySample) -> str:
    out = ["== (1) Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        out.append(f"{i}. {p}")
    out.append("")
    out.append("== (2) Story QA ==")
    for item in sample.story_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    out.append("")
    out.append("== (3) World QA ==")
    for item in sample.world_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    return "\n".join(out)


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
    StoryParams(setting="ruins", problem="gate_jam", tool="oil", move="oil",
                hero="Mina", hero_gender="girl", companion="Toby", companion_gender="boy"),
    StoryParams(setting="cove", problem="riddle_stream", tool="lantern", move="lift",
                hero="Lina", hero_gender="girl", companion="Kai", companion_gender="boy"),
    StoryParams(setting="garden", problem="root_snarl", tool="rope", move="push",
                hero="Arlo", hero_gender="boy", companion="Nia", companion_gender="girl"),
]


def generate(params: StoryParams) -> StorySample:
    if params.setting not in SETTINGS or params.problem not in PROBLEMS or params.tool not in TOOLS or params.move not in MOVES:
        raise StoryError("Invalid params.")
    world = tell(SETTINGS[params.setting], PROBLEMS[params.problem], TOOLS[params.tool],
                 MOVES[params.move], params.hero, params.hero_gender,
                 params.companion, params.companion_gender)
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
        print(asp_program("", "#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"{len(asp_valid_combos())} compatible combinations:")
        for row in asp_valid_combos():
            print(" ", row)
        return
    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        for i in range(args.n):
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            samples.append(generate(params))
    if args.json:
        print(samples[0].to_json() if len(samples) == 1 else json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return
    for i, sample in enumerate(samples):
        emit(sample, trace=args.trace, qa=args.qa, header=(f"### variant {i+1}" if len(samples) > 1 else ""))
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()

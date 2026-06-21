#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/blur_majesty_vodka_problem_solving_fairy_tale.py
=================================================================================

A tiny fairy-tale storyworld about a child, a royal problem, and a gentle
problem-solving turn. The seed words are woven into the simulated world:
blur, majesty, vodka.

Premise
-------
A young helper in a castle notices that the queen's crystal lens has gone blurry
after a grown-up bottle of vodka tipped and left a slick, foggy mess. The helper
must think carefully, choose the right cloths and water, and restore the queen's
majesty without making the problem worse.

The story engine is small and classical:
- typed entities with physical meters and emotional memes
- a forward-causal world model
- a reasonableness gate
- an inline ASP twin
- grounded prompts and Q&A sets

This script is standalone and uses only the stdlib plus the shared repo helpers.
"""

from __future__ import annotations

import argparse
import copy
import io
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
    attrs: dict = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "queen", "woman", "mother"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "king", "man", "father"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]


@dataclass
class Setting:
    id: str
    name: str
    line: str
    light: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Problem:
    id: str
    label: str
    cause: str
    sign: str
    fix_need: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Tool:
    id: str
    label: str
    use: str
    power: int
    sense: int
    tags: set[str] = field(default_factory=set)


@dataclass
class StoryParams:
    setting: str
    problem: str
    tool: str
    hero_name: str
    hero_type: str
    ruler_name: str
    ruler_type: str
    helper_name: str
    helper_type: str
    seed: Optional[int] = None


class World:
    def __init__(self) -> None:
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}

    def add(self, e: Entity) -> Entity:
        self.entities[e.id] = e
        return e

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
        c = World()
        c.entities = copy.deepcopy(self.entities)
        c.fired = set(self.fired)
        c.paragraphs = [[]]
        return c


@dataclass
class Rule:
    name: str
    apply: Callable[[World], list[str]]


def _r_blur(world: World) -> list[str]:
    out = []
    lens = world.get("lens")
    spill = world.get("spill")
    if spill.meters["spilled"] < THRESHOLD:
        return out
    sig = ("blur",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    lens.meters["blurred"] += 1
    world.get("room").meters["mess"] += 1
    world.get("hero").memes["worry"] += 1
    out.append("__blur__")
    return out


def _r_damp(world: World) -> list[str]:
    out = []
    lens = world.get("lens")
    if lens.meters["blurred"] < THRESHOLD:
        return out
    sig = ("damp",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    world.get("cloth").meters["wet"] += 1
    out.append("A clean cloth grew damp and ready.")
    return out


CAUSAL_RULES = [Rule("blur", _r_blur), Rule("damp", _r_damp)]


def propagate(world: World, narrate: bool = True) -> list[str]:
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
        for s in produced:
            world.say(s)
    return produced


def hazard(problem: Problem, tool: Tool) -> bool:
    return problem.id == "vodka_spill" and tool.power >= 1


def valid_combos() -> list[tuple[str, str, str]]:
    return [("castle", "vodka_spill", t.id) for t in TOOLS if TOOLS[t].sense >= SENSE_MIN]


def predict(world: World) -> dict:
    sim = world.copy()
    sim.get("spill").meters["spilled"] += 1
    propagate(sim, narrate=False)
    return {"blurred": sim.get("lens").meters["blurred"] >= THRESHOLD}


def setup(world: World, hero: Entity, ruler: Entity, helper: Entity, setting: Setting) -> None:
    world.say(
        f"Once in a bright {setting.name}, {hero.id} served in the shadow of {ruler.id}'s "
        f"majesty. The halls shone {setting.light}, and every ribbon on the walls looked fit "
        f"for a song."
    )
    hero.memes["wonder"] += 1
    ruler.memes["dignity"] += 1
    helper.memes["kindness"] += 1


def trouble(world: World, hero: Entity, problem: Problem, setting: Setting) -> None:
    world.say(
        f"Then trouble came. A bottle of {problem.cause} tipped by the silver tray, and "
        f"a thin {problem.sign} spread over the crystal lens."
    )
    world.say(
        f"{hero.id} leaned in, but the picture was all {problem.sign} and no sparkle."
    )
    hero.memes["worry"] += 1


def think(world: World, helper: Entity, hero: Entity, problem: Problem) -> None:
    pred = predict(world)
    world.facts["predicted_blur"] = pred["blurred"]
    world.say(
        f"{helper.id} looked carefully and said, \"If we use the wrong thing, the blur will "
        f"stay, but if we solve it gently, the lens can shine again.\""
    )
    if pred["blurred"]:
        world.say(
            f"{helper.id} pointed to the slick ring on the glass and to the cloth drawer. "
            f"That was the clue."
        )


def solve(world: World, hero: Entity, helper: Entity, ruler: Entity, problem: Problem, tool: Tool) -> None:
    cloth = world.get("cloth")
    lens = world.get("lens")
    spill = world.get("spill")
    spill.meters["spilled"] = 0.0
    lens.meters["blurred"] = 0.0
    cloth.meters["used"] += 1
    hero.memes["joy"] += 1
    ruler.memes["relief"] += 1
    world.say(
        f"{hero.id} fetched the clean cloth, wiped the glass in slow circles, and then "
        f"moved the bottle of {problem.cause} far away from the table."
    )
    world.say(
        f"At last the blur vanished. The lens showed the candlelight clearly, and "
        f"{ruler.id}'s majesty looked bright again."
    )


def lesson(world: World, hero: Entity, helper: Entity, ruler: Entity, problem: Problem) -> None:
    world.say(
        f"{ruler.id} smiled and said, \"You solved it with care, not panic. That is true "
        f"courtly bravery.\""
    )
    world.say(
        f"{hero.id} bowed, proud and warm, and {helper.id} tucked the cloth back where it "
        f"belonged."
    )


SETTINGS = {
    "castle": Setting(id="castle", name="castle hall", line="a long marble hall", light="like gold"),
    "tower": Setting(id="tower", name="watch tower", line="a high stone room", light="like moonmilk"),
}

PROBLEMS = {
    "vodka_spill": Problem(
        id="vodka_spill",
        label="vodka spill",
        cause="vodka",
        sign="blur",
        fix_need="wipe the glass clean",
        tags={"vodka", "blur"},
    )
}

TOOLS = {
    "cloth": Tool(id="cloth", label="clean cloth", use="wipe", power=2, sense=3, tags={"cloth"}),
    "water": Tool(id="water", label="water bowl", use="rinse", power=1, sense=2, tags={"water"}),
    "ribbon": Tool(id="ribbon", label="silk ribbon", use="decorate", power=0, sense=0, tags={"ribbon"}),
}

PEOPLE = {
    "hero": ("Pip", "boy"),
    "ruler": ("Queen Mira", "queen"),
    "helper": ("Fae", "girl"),
}

NAMES = ["Pip", "Nell", "Ivo", "Lina", "Jasper", "Mara", "Orin", "Tess"]


def aspirational_tool_ids() -> list[str]:
    return [t.id for t in TOOLS.values() if t.sense >= SENSE_MIN]


def build_story(params: StoryParams) -> World:
    if params.setting not in SETTINGS:
        raise StoryError("Unknown setting.")
    if params.problem not in PROBLEMS:
        raise StoryError("Unknown problem.")
    if params.tool not in TOOLS:
        raise StoryError("Unknown tool.")
    tool = TOOLS[params.tool]
    if tool.sense < SENSE_MIN:
        raise StoryError(f"(Refusing tool '{tool.id}': too flimsy for a real fix.)")
    if not hazard(PROBLEMS[params.problem], tool):
        raise StoryError("(No story: this tool cannot help with this problem.)")

    world = World()
    hero = world.add(Entity(id=params.hero_name, kind="character", type=params.hero_type, role="hero"))
    ruler = world.add(Entity(id=params.ruler_name, kind="character", type=params.ruler_type, role="ruler"))
    helper = world.add(Entity(id=params.helper_name, kind="character", type=params.helper_type, role="helper"))
    room = world.add(Entity(id="room", type="room", label="castle room"))
    lens = world.add(Entity(id="lens", type="thing", label="crystal lens"))
    spill = world.add(Entity(id="spill", type="thing", label="vodka spill"))
    cloth = world.add(Entity(id="cloth", type="thing", label="clean cloth"))

    setup(world, hero, ruler, helper, SETTINGS[params.setting])
    world.para()
    trouble(world, hero, PROBLEMS[params.problem], SETTINGS[params.setting])
    think(world, helper, hero, PROBLEMS[params.problem])
    world.para()
    spill.meters["spilled"] += 1
    propagate(world, narrate=False)
    solve(world, hero, helper, ruler, PROBLEMS[params.problem], tool)
    lesson(world, hero, helper, ruler, PROBLEMS[params.problem])

    world.facts.update(
        hero=hero, ruler=ruler, helper=helper, room=room, lens=lens, spill=spill, cloth=cloth,
        setting=SETTINGS[params.setting], problem=PROBLEMS[params.problem], tool=tool,
        outcome="cleared", blurred_before=True, seed=params.seed,
    )
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        'Write a fairy tale about a child who solves a blur in a royal hall, and include the words "blur", "majesty", and "vodka".',
        f"Tell a gentle castle story where {f['hero'].id} notices a blur, thinks carefully, and helps {f['ruler'].id}'s majesty shine again.",
        f"Write a problem-solving fairy tale about a {f['problem'].cause} spill and a clean cloth, with a happy ending.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero, ruler, helper = f["hero"], f["ruler"], f["helper"]
    return [
        QAItem(
            question="What went wrong in the castle?",
            answer="A bottle of vodka tipped over and left a blur on the crystal lens. The glass looked foggy until someone cleaned it.",
        ),
        QAItem(
            question="How did the helper solve the problem?",
            answer=f"{helper.id} noticed the clue, then {hero.id} wiped the lens with a clean cloth and moved the bottle away. That fixed the blur without making a bigger mess.",
        ),
        QAItem(
            question="What changed by the end?",
            answer=f"The blur was gone, and {ruler.id}'s majesty looked bright again. The room went from foggy and worried to calm and shining.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a blur?",
            answer="A blur is something that looks fuzzy or unclear. It can happen when a surface is wet, dirty, or fogged up.",
        ),
        QAItem(
            question="What is majesty?",
            answer="Majesty means royal greatness or splendor. People use it for queens, kings, and other grand royal things.",
        ),
        QAItem(
            question="What should you do with a spilled liquid?",
            answer="You should clean it up carefully and move it away from anything it could harm. That keeps the place safe and stops the mess from spreading.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    for p in sample.prompts:
        lines.append(f"- {p}")
    lines.append("")
    lines.append("== story qa ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== world qa ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world ---"]
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
        lines.append(f"  {e.id}: {e.type} {' '.join(bits)}")
    lines.append(f"  fired={sorted({n for n, *_ in world.fired})}")
    return "\n".join(lines)


ASP_RULES = r"""
valid(S,P,T) :- setting(S), problem(P), tool(T), sense(T,N), sense_min(M), N >= M.
outcome(cleared) :- valid(_,_,_).
"""

def asp_facts() -> str:
    import asp
    parts = []
    for sid in SETTINGS:
        parts.append(asp.fact("setting", sid))
    for pid in PROBLEMS:
        parts.append(asp.fact("problem", pid))
    for tid, tool in TOOLS.items():
        parts.append(asp.fact("tool", tid))
        parts.append(asp.fact("sense", tid, tool.sense))
    parts.append(asp.fact("sense_min", SENSE_MIN))
    return "\n".join(parts)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    import asp
    rc = 0
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: ASP matches valid_combos() ({len(py)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos.")
        print("python-only:", sorted(py - cl))
        print("asp-only:", sorted(cl - py))
    try:
        sample = generate(resolve_params(build_parser().parse_args([]), random.Random(7)))
        buf = io.StringIO()
        old = sys.stdout
        try:
            sys.stdout = buf
            emit(sample)
        finally:
            sys.stdout = old
        print("OK: smoke-test generation and emit succeeded.")
    except Exception as e:
        rc = 1
        print(f"SMOKE TEST FAILED: {e}")
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A tiny fairy-tale problem-solving storyworld.")
    ap.add_argument("--setting", choices=sorted(SETTINGS))
    ap.add_argument("--problem", choices=sorted(PROBLEMS))
    ap.add_argument("--tool", choices=sorted(TOOLS))
    ap.add_argument("--hero-name")
    ap.add_argument("--hero-type", choices=["boy", "girl"])
    ap.add_argument("--ruler-name")
    ap.add_argument("--ruler-type", choices=["queen", "king"])
    ap.add_argument("--helper-name")
    ap.add_argument("--helper-type", choices=["boy", "girl"])
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
    hero_name = args.hero_name or rng.choice(NAMES)
    hero_type = args.hero_type or rng.choice(["boy", "girl"])
    ruler_name = args.ruler_name or "Queen Mira"
    ruler_type = args.ruler_type or "queen"
    helper_name = args.helper_name or rng.choice([n for n in NAMES if n != hero_name])
    helper_type = args.helper_type or ("girl" if hero_type == "boy" else "boy")
    return StoryParams(
        setting=setting, problem=problem, tool=tool,
        hero_name=hero_name, hero_type=hero_type,
        ruler_name=ruler_name, ruler_type=ruler_type,
        helper_name=helper_name, helper_type=helper_type,
    )


def generate(params: StoryParams) -> StorySample:
    if params.setting not in SETTINGS or params.problem not in PROBLEMS or params.tool not in TOOLS:
        raise StoryError("Invalid parameters.")
    world = build_story(params)
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


def valid_default() -> StoryParams:
    return StoryParams(
        setting="castle", problem="vodka_spill", tool="cloth",
        hero_name="Pip", hero_type="boy",
        ruler_name="Queen Mira", ruler_type="queen",
        helper_name="Fae", helper_type="girl",
    )


CURATED = [
    valid_default(),
]


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("", "#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print("compatible combos:")
        for row in asp_valid_combos():
            print(row)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
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
        emit(sample, trace=args.trace, qa=args.qa, header=f"### variant {i+1}" if len(samples) > 1 else "")
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()

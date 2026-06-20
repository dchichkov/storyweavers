#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/sensor_pensive_problem_solving_superhero_story.py
=================================================================================

A standalone story world for a small superhero tale about a pensive hero, a
useful sensor, and a problem-solving rescue.

Seed words:
- sensor
- pensive

Style:
- Superhero story

Feature:
- Problem solving

This world generates small, classical stories where a young hero notices a
trouble sign, thinks carefully, uses a sensor to understand what is happening,
and solves the problem with help from a calm teammate or grown-up. The world is
kept tiny on purpose: a few characters, a few props, one concrete problem, and a
clear ending image showing what changed.

The story engine is state-driven. Emotional and physical meters accumulate, and
the final prose reflects the simulated world rather than a frozen template.
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

    tags: set[str] = field(default_factory=set)

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
        return {"mother": "mom", "father": "dad"}.get(self.type, self.type)



    @property
    def phrase(self) -> str:
        return getattr(self, "_phrase", None) or self.label or self.id.replace("_", " ")

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)

@dataclass
class Hero:
    id: str
    title: str
    power: str
    costume: str
    emblem: str
    sensor_use: str
    pensive_line: str
    save_line: str
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
class Problem:
    id: str
    trouble: str
    sign: str
    location: str
    cause: str
    risk: str
    fix_kind: str
    fix_line: str
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
class Sensor:
    id: str
    label: str
    detects: set[str]
    glow: str
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
class Tool:
    id: str
    label: str
    phrase: str
    action: str
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


def propagate(world: World, narrate: bool = True) -> list[str]:
    out: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            s = rule.apply(world)
            if s:
                changed = True
                out.extend(s)
    if narrate:
        for line in out:
            world.say(line)
    return out


def _r_panic(world: World) -> list[str]:
    out: list[str] = []
    for e in list(world.entities.values()):
        if e.meters["trouble"] < THRESHOLD:
            continue
        sig = ("panic", e.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        for hero in list(world.entities.values()):
            if hero.role == "hero":
                hero.memes["focus"] += 1
                hero.memes["pensive"] += 1
        out.append("")
    return out


def _r_relief(world: World) -> list[str]:
    out: list[str] = []
    for e in list(world.entities.values()):
        if e.meters["fixed"] < THRESHOLD:
            continue
        sig = ("relief", e.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        for hero in list(world.entities.values()):
            if hero.role == "hero":
                hero.memes["relief"] += 1
        out.append("")
    return out


CAUSAL_RULES = [Rule("panic", _r_panic), Rule("relief", _r_relief)]


def reasonableness_gate(problem: Problem, sensor: Sensor, tool: Tool) -> bool:
    return problem.id in sensor.detects and problem.fix_kind == tool.id


def propose_solution(problem: Problem, tool: Tool) -> bool:
    return problem.fix_kind == tool.id


def setup_story(world: World, hero: Entity, sidekick: Entity, mentor: Entity,
                problem: Problem, sensor: Sensor, tool: Tool) -> None:
    hero.memes["care"] += 1
    sidekick.memes["trust"] += 1
    world.say(
        f"On a bright day in Star Harbor, {hero.id} stood on a rooftop in "
        f"{hero.label_word if hero.label_word else hero.type} colors, while "
        f"{sidekick.id} kept watch nearby. A little {sensor.label} blinked on "
        f"the hero belt, ready to notice trouble."
    )
    world.say(
        f"Then a problem began at {problem.location}: {problem.trouble}. "
        f"The first sign was {problem.sign}."
    )
    world.say(
        f"{hero.id} grew pensive and looked toward the streets. "
        f'\"{hero.pensive_line}\" {hero.pronoun()} whispered.'
    )
    world.say(
        f"{mentor.id} nodded. \"Use the {sensor.label} and think it through,\" "
        f"{mentor.pronoun()} said."
    )


def observe(world: World, hero: Entity, sensor: Sensor, problem: Problem) -> None:
    hero.memes["focus"] += 1
    world.say(
        f"{hero.id} aimed the {sensor.label} at {problem.location}, and it "
        f"{sensor.glow}. The reading matched the trouble exactly."
    )


def solve(world: World, hero: Entity, sidekick: Entity, mentor: Entity,
          problem: Problem, tool: Tool) -> None:
    world.say(
        f"Then {hero.id} made a plan. {hero.id} grabbed {tool.phrase} and "
        f"{tool.action}, while {sidekick.id} kept the path clear."
    )
    world.say(
        f"{hero.id} {problem.fix_line}. Soon {problem.location} was calm again, "
        f"and the danger that had been building was gone."
    )
    world.get("problem").meters["fixed"] += 1
    world.get("problem").meters["trouble"] = 0.0
    hero.memes["pride"] += 1
    sidekick.memes["joy"] += 1
    mentor.memes["relief"] += 1
    world.say(
        f"{mentor.id} smiled and said, \"That was brave and smart.\" "
        f"{hero.id} stood a little taller, and {sensor.label} rested quietly on "
        f"{hero.pronoun('possessive')} belt."
    )


def tell(hero_def: Hero, problem_def: Problem, sensor_def: Sensor, tool_def: Tool,
         hero_name: str, sidekick_name: str, mentor_name: str,
         hero_gender: str, sidekick_gender: str, mentor_type: str) -> World:
    world = World()
    hero = world.add(Entity(hero_name, kind="character", type=hero_gender,
                            role="hero", label=hero_def.title, traits=["pensive"]))
    sidekick = world.add(Entity(sidekick_name, kind="character", type=sidekick_gender,
                                role="sidekick", label="helper"))
    mentor = world.add(Entity(mentor_name, kind="character", type=mentor_type,
                              role="mentor", label="the mentor"))
    problem = world.add(Entity("problem", type="problem", label=problem_def.id))
    sensor = world.add(Entity(sensor_def.id, type="tool", label=sensor_def.label))
    tool = world.add(Entity(tool_def.id, type="tool", label=tool_def.label))
    problem.meters["trouble"] = 1.0

    setup_story(world, hero, sidekick, mentor, problem_def, sensor_def, tool_def)
    world.para()
    observe(world, hero, sensor, problem_def)
    propagate(world, narrate=False)
    world.para()
    solve(world, hero, sidekick, mentor, problem_def, tool_def)

    world.facts.update(
        hero=hero, sidekick=sidekick, mentor=mentor,
        problem=problem_def, sensor=sensor_def, tool=tool_def,
        solved=True, sensor_used=sensor_def.id, fix_kind=tool_def.id,
    )
    return world


HEROES = {
    "nova": Hero(
        id="Nova", title="Nova", power="careful planning", costume="blue cape",
        emblem="star", sensor_use="noticed the trouble with the sensor",
        pensive_line="Something here does not fit.",
        save_line="solved the problem with a steady plan",
        tags={"hero", "problem_solving", "sensor", "pensive"},
    ),
    "spark": Hero(
        id="Spark", title="Spark", power="quick thinking", costume="red cape",
        emblem="bolt", sensor_use="read the sensor twice",
        pensive_line="I need to think before I leap.",
        save_line="fixed the trouble with a smart idea",
        tags={"hero", "problem_solving", "sensor", "pensive"},
    ),
}

PROBLEMS = {
    "bridge_alarm": Problem(
        id="bridge_alarm",
        trouble="the bridge alarm kept chirping even though no one was in danger",
        sign="a tiny red light that would not stop blinking",
        location="the moon bridge",
        cause="a loose wire",
        risk="confusion for the crowd",
        fix_kind="patch",
        fix_line="used a patch kit to seal the loose wire and stop the false alarm",
        tags={"alarm", "sensor", "problem"},
    ),
    "power_glitch": Problem(
        id="power_glitch",
        trouble="the lights in the lighthouse flickered and nearly went dark",
        sign="a warm buzz from the power box",
        location="the lighthouse stairs",
        cause="a slipping battery pack",
        risk="dark stairs and a worried town",
        fix_kind="tighten",
        fix_line="tightened the battery pack until the lights shone steady again",
        tags={"power", "sensor", "problem"},
    ),
    "water_leak": Problem(
        id="water_leak",
        trouble="water was dripping into the subway control room",
        sign="a sensor beep that pointed to the ceiling",
        location="the subway tunnel",
        cause="a cracked pipe",
        risk="wet controls and a stalled train",
        fix_kind="seal",
        fix_line="sealed the crack with a quick repair gel and stopped the drip",
        tags={"water", "sensor", "problem"},
    ),
}

SENSORS = {
    "belt_sensor": Sensor("belt_sensor", "sensor", {"bridge_alarm", "power_glitch", "water_leak"}, "glowed green", {"sensor"}),
    "hand_sensor": Sensor("hand_sensor", "sensor", {"bridge_alarm", "water_leak"}, "clicked and glowed softly", {"sensor"}),
    "mask_sensor": Sensor("mask_sensor", "sensor", {"power_glitch"}, "pulsed blue", {"sensor"}),
}

TOOLS = {
    "patch": Tool("patch", "patch kit", "a small patch kit", "sealed the wire neatly", {"patch"}),
    "tighten": Tool("tighten", "wrench", "a bright wrench", "tightened the pack carefully", {"tighten"}),
    "seal": Tool("seal", "repair gel", "a tube of repair gel", "sealed the crack cleanly", {"seal"}),
}

NAMES = ["Nova", "Spark", "Ray", "Cleo", "Mira", "Ace", "Juno", "Zed"]
SIDEKICKS = ["Comet", "Byte", "Gleam", "Moss", "Lark", "Pip"]
MENTORS = ["Captain Dawn", "Aunt Beam", "Chief Halo"]



@dataclass
class StoryParams:
    hero: str
    problem: str
    sensor: str
    tool: str
    hero_name: str
    sidekick_name: str
    mentor_name: str
    hero_gender: str
    sidekick_gender: str
    mentor_type: str
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

CURATED = [
    {"hero": "nova", "problem": "bridge_alarm", "sensor": "belt_sensor", "tool": "patch"},
    {"hero": "spark", "problem": "power_glitch", "sensor": "mask_sensor", "tool": "tighten"},
    {"hero": "nova", "problem": "water_leak", "sensor": "hand_sensor", "tool": "seal"},
]



def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for hid, h in HEROES.items():
        for pid, p in PROBLEMS.items():
            for sid, s in SENSORS.items():
                for tid, t in TOOLS.items():
                    if reasonableness_gate(p, s, t):
                        combos.append((hid, pid, sid, tid))
    return combos


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Superhero story world with sensors and thoughtful problem solving.")
    ap.add_argument("--hero", choices=HEROES)
    ap.add_argument("--problem", choices=PROBLEMS)
    ap.add_argument("--sensor", choices=SENSORS)
    ap.add_argument("--tool", choices=TOOLS)
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
    if args.problem and args.sensor and args.tool:
        if not reasonableness_gate(PROBLEMS[args.problem], SENSORS[args.sensor], TOOLS[args.tool]):
            raise StoryError("That sensor and tool do not solve that problem.")
    combos = [c for c in valid_combos()
              if args.hero in (None, c[0])
              and args.problem in (None, c[1])
              and args.sensor in (None, c[2])
              and args.tool in (None, c[3])]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    hero, problem, sensor, tool = rng.choice(sorted(combos))
    return StoryParams(
        hero=hero,
        problem=problem,
        sensor=sensor,
        tool=tool,
        hero_name=rng.choice(NAMES),
        sidekick_name=rng.choice(SIDEKICKS),
        mentor_name=rng.choice(MENTORS),
        hero_gender=rng.choice(["girl", "boy"]),
        sidekick_gender=rng.choice(["girl", "boy"]),
        mentor_type=rng.choice(["mother", "father", "woman", "man"]),
    )


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a superhero story for a 3-to-5-year-old that includes the words "{f["sensor"].label}" and "pensive".',
        f"Tell a gentle problem-solving story where {f['hero'].id} notices trouble with a {f['sensor'].label} and fixes it with help.",
        f"Write a superhero adventure where a thoughtful hero uses a {f['sensor'].label} to solve a small problem safely.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    return [
        QAItem(
            question="What problem did the hero notice?",
            answer=f"{f['problem'].trouble.capitalize()}. {f['problem'].sign.capitalize()} showed the hero that something was wrong.",
        ),
        QAItem(
            question="How did the hero solve the problem?",
            answer=f"{f['hero'].id} used the {f['sensor'].label} to understand the trouble, then {f['tool'].label} helped fix it. The plan worked because the hero stayed calm and pensive.",
        ),
        QAItem(
            question="How did the story end?",
            answer=f"The danger was gone, the place was calm again, and {f['hero'].id} stood proudly beside the quiet sensor. It ended with a clear sign that the problem had been solved.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does a sensor do?",
            answer="A sensor notices changes and gives a signal, like a blink, beep, or glow, so someone can tell when something needs attention.",
        ),
        QAItem(
            question="What does pensive mean?",
            answer="Pensive means thinking carefully and quietly about what to do next. A pensive hero pauses instead of rushing.",
        ),
        QAItem(
            question="Why is problem solving important for a superhero?",
            answer="Problem solving helps a superhero figure out the right fix instead of making the trouble worse. It turns brave action into smart action.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    out = ["== (1) Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        out.append(f"{i}. {p}")
    out.append("")
    out.append("== (2) Story questions ==")
    for q in sample.story_qa:
        out.append(f"Q: {q.question}")
        out.append(f"A: {q.answer}")
    out.append("")
    out.append("== (3) World questions ==")
    for q in sample.world_qa:
        out.append(f"Q: {q.question}")
        out.append(f"A: {q.answer}")
    return "\n".join(out)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in list(world.entities.values()):
        bits = []
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if e.role:
            bits.append(f"role={e.role}")
        lines.append(f"  {e.id:12} ({e.type:8}) {' '.join(bits)}")
    return "\n".join(lines)


ASP_RULES = r"""
valid(H, P, S, T) :- hero(H), problem(P), sensor(S), tool(T),
                     detects(S, P), fixes(T, P).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for hid in HEROES:
        lines.append(asp.fact("hero", hid))
    for pid in PROBLEMS:
        lines.append(asp.fact("problem", pid))
    for sid, s in SENSORS.items():
        lines.append(asp.fact("sensor", sid))
        for p in sorted(s.detects):
            lines.append(asp.fact("detects", sid, p))
    for tid, t in TOOLS.items():
        lines.append(asp.fact("tool", tid))
        lines.append(asp.fact("fixes", tid, t.id))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/4."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    rc = 0
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
    else:
        rc = 1
        print("MISMATCH between clingo and Python gate.")
    try:
        sample = generate(resolve_params(build_parser().parse_args([]), random.Random(777)))
        _ = sample.story
        print("OK: normal story generation smoke test passed.")
    except Exception as exc:
        rc = 1
        print(f"SMOKE TEST FAILED: {exc}")
    return rc


def generate(params: StoryParams) -> StorySample:
    world = tell(
        HEROES[params.hero],
        PROBLEMS[params.problem],
        SENSORS[params.sensor],
        TOOLS[params.tool],
        params.hero_name,
        params.sidekick_name,
        params.mentor_name,
        params.hero_gender,
        params.sidekick_gender,
        params.mentor_type,
    )
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
        print(asp_program("#show valid/4."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"{len(asp_valid_combos())} compatible combos:")
        for row in asp_valid_combos():
            print(" ", row)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(StoryParams(**c, hero_name="Nova", sidekick_name="Comet", mentor_name="Captain Dawn",
                                        hero_gender="girl", sidekick_gender="boy", mentor_type="mother")) for c in CURATED]
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
        print(samples[0].to_json() if len(samples) == 1 else json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()

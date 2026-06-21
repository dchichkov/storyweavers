#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/ulterior_saloon_inherit_problem_solving_superhero_story.py
=========================================================================================

A standalone story world for a tiny superhero problem-solving tale:
a hero notices an ulterior motive around a dusty saloon inheritance,
spots the real trouble, and solves it with calm teamwork instead of force.

Seed words: ulterior, saloon, inherit
Style: Superhero Story
Feature: Problem Solving
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
        female = {"girl", "woman", "mother", "mom"}
        male = {"boy", "man", "father", "dad"}
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
    label: str
    detail: str
    hidden_spot: str
    mood: str

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
    clue: str
    real_issue: str
    fake_issue: str
    risk: str
    urgency: int = 1
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
    use: str
    effect: str
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
class Plan:
    id: str
    method: str
    power: int
    text: str
    result_text: str
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


def _r_worry(world: World) -> list[str]:
    out: list[str] = []
    hero = world.get("hero")
    if hero.meters["trouble"] < THRESHOLD or ("worry", hero.id) in world.fired:
        return out
    world.fired.add(("worry", hero.id))
    hero.memes["focus"] += 1
    out.append("__worry__")
    return out


def _r_relief(world: World) -> list[str]:
    out: list[str] = []
    if world.facts.get("solved") and ("relief", "team") not in world.fired:
        world.fired.add(("relief", "team"))
        for eid in ("hero", "friend"):
            world.get(eid).memes["relief"] += 1
        out.append("__relief__")
    return out


CAUSAL_RULES = [
    Rule("worry", "social", _r_worry),
    Rule("relief", "social", _r_relief),
]


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


def problem_risky(problem: Problem) -> bool:
    return problem.id == "false_alarm" or problem.urgency >= 1


def plan_effective(problem: Problem, plan: Plan) -> bool:
    return plan.power >= problem.urgency


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for sid in SETTINGS:
        for pid, pr in PROBLEMS.items():
            for plid, plan in PLANS.items():
                if problem_risky(pr) and plan_effective(pr, plan):
                    combos.append((sid, pid, plid))
    return combos


def setting_text(setting: Setting) -> str:
    return f"The {setting.label} sat quiet under the city lights, and {setting.detail}"


def introduce(world: World, hero: Entity, friend: Entity, setting: Setting) -> None:
    world.say(
        f"At the old {setting.label}, {hero.id} and {friend.id} stood like bright "
        f"stars in capes. {setting_text(setting)}"
    )
    world.say(
        f"They were used to helping people, but tonight something about the room felt "
        f"ulterior, like a secret hiding behind a smile."
    )


def detect(world: World, hero: Entity, problem: Problem) -> None:
    hero.memes["alert"] += 1
    hero.meters["trouble"] += 1
    world.say(
        f"{hero.id} spotted {problem.clue}. It looked like a small problem, but "
        f"{hero.pronoun('subject')} knew there might be an ulterior reason for it."
    )


def warn(world: World, friend: Entity, hero: Entity, problem: Problem) -> None:
    friend.memes["care"] += 1
    world.say(
        f"{friend.id} frowned. \"This does not feel right,\" {friend.pronoun()} said. "
        f"\"Someone may want us to rush in and miss the real issue.\""
    )
    world.say(
        f"Together they looked again and found the real trouble: {problem.real_issue}."
    )


def investigate(world: World, hero: Entity, tool: Tool, problem: Problem) -> None:
    hero.memes["curiosity"] += 1
    world.say(
        f"{hero.id} used {tool.label} to {tool.use}. That simple move {tool.effect}, "
        f"and the clue became easier to read."
    )
    world.say(
        f"Now the hidden spot near the saloon told the truth: {problem.fake_issue} was "
        f"only a distraction, while {problem.real_issue} was the thing that mattered."
    )


def solve(world: World, hero: Entity, friend: Entity, plan: Plan, problem: Problem) -> None:
    hero.memes["hope"] += 1
    friend.memes["hope"] += 1
    world.say(
        f"{hero.id} smiled and chose a calm plan. {plan.text}."
    )
    world.say(
        f"With that move, the team solved {problem.id}: {plan.result_text}."
    )
    world.facts["solved"] = True


def ending(world: World, setting: Setting) -> None:
    world.say(
        f"In the end, the old {setting.label} was safe again. The heroes stood in the "
        f"lamplight, ready to inherit the day with better wisdom than before."
    )


def tell(setting: Setting, problem: Problem, tool: Tool, plan: Plan,
         hero_name: str = "Nova", friend_name: str = "Torch",
         hero_type: str = "girl", friend_type: str = "boy") -> World:
    world = World()
    hero = world.add(Entity(id=hero_name, kind="character", type=hero_type, role="hero"))
    friend = world.add(Entity(id=friend_name, kind="character", type=friend_type, role="friend"))
    world.add(Entity(id="saloon", type="place", label=setting.label))
    world.facts.update(setting=setting, problem=problem, tool=tool, plan=plan)

    introduce(world, hero, friend, setting)
    world.para()
    detect(world, hero, problem)
    warn(world, friend, hero, problem)
    world.para()
    investigate(world, hero, tool, problem)
    solve(world, hero, friend, plan, problem)
    world.para()
    ending(world, setting)
    propagate(world, narrate=False)
    return world


SETTINGS = {
    "saloon": Setting(
        id="saloon",
        label="saloon",
        detail="the wooden floorboards creaked, and the old swinging doors shone with dust.",
        hidden_spot="behind the stage curtains",
        mood="dusty",
    ),
    "museum": Setting(
        id="museum",
        label="museum hall",
        detail="glass cases lined the walls, and the echo in the hall made every step sound important.",
        hidden_spot="behind a velvet rope",
        mood="quiet",
    ),
    "station": Setting(
        id="station",
        label="train station",
        detail="the benches were empty, and the big clock ticked like a patient drum.",
        hidden_spot="under a timetable board",
        mood="busy",
    ),
}

PROBLEMS = {
    "false_alarm": Problem(
        id="false_alarm",
        clue="a door left open near the saloon's back room",
        real_issue="a missing delivery box with the town's donations",
        fake_issue="a broken chair that only looked suspicious",
        risk="people might blame the wrong thing",
        urgency=1,
        tags={"ulterior", "saloon"},
    ),
    "stuck_gate": Problem(
        id="stuck_gate",
        clue="a gate that would not budge",
        real_issue="a spilled pile of gravel blocking the track",
        fake_issue="a rusty lock that was not the main problem",
        risk="the crowd might get trapped outside",
        urgency=2,
        tags={"saloon"},
    ),
    "missing_map": Problem(
        id="missing_map",
        clue="an empty frame where the map should hang",
        real_issue="the key to the donation room had been tucked in a drawer",
        fake_issue="a torn poster that made the wall look odd",
        risk="the team might waste time searching the wrong place",
        urgency=1,
        tags={"inherit"},
    ),
}

TOOLS = {
    "lamp": Tool("lamp", "a bright lamp", "shine across the floor", "made tiny clues sparkle", {"light"}),
    "magnifier": Tool("magnifier", "a magnifying glass", "check the scratches", "turned one clue into three clear ones", {"investigate"}),
    "scanner": Tool("scanner", "a pocket scanner", "scan the doorway", "showed where the marks had gone", {"tech"}),
}

PLANS = {
    "ask": Plan("ask", "ask the right question", 1,
                "They asked the caretaker who had seen the box last",
                "the caretaker remembered the drawer and pointed them the right way",
                {"talk"}),
    "follow": Plan("follow", "follow the trail", 1,
                   "They followed the scuffed floorboards one step at a time",
                   "the trail led straight to the donation room",
                   {"track"}),
    "lift": Plan("lift", "lift the loose board", 2,
                 "They lifted the loose board together and checked beneath it",
                 "the hidden key was right where the board had been hiding it",
                 {"search"}),
}

GIRL_NAMES = ["Nova", "Ruby", "Mira", "Zara", "Ivy", "Lena"]
BOY_NAMES = ["Torch", "Kai", "Jett", "Finn", "Miles", "Noah"]
TRAITS = ["brave", "careful", "clever", "kind", "steady", "quick"]


@dataclass
@dataclass
class StoryParams:
    setting: str
    problem: str
    tool: str
    plan: str
    hero: str
    hero_gender: str
    friend: str
    friend_gender: str
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


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    setting = f["setting"]
    problem = f["problem"]
    return [
        f'Write a superhero story for a young child set in a {setting.label} that uses the word "ulterior".',
        f"Tell a problem-solving story where {f['hero'].id} and {f['friend'].id} notice that "
        f"{problem.clue} hides a bigger truth.",
        f'Write a gentle hero story where the team does not rush, but instead investigates and solves '
        f'a tricky saloon problem.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    setting: Setting = f["setting"]
    problem: Problem = f["problem"]
    hero: Entity = world.get("hero")
    friend: Entity = world.get("friend")
    return [
        QAItem(
            question="Who are the heroes in the story?",
            answer=f"The heroes are {hero.id} and {friend.id}. They work like a small superhero team and stay calm together.",
        ),
        QAItem(
            question="What made the situation feel ulterior?",
            answer=f"The clue looked simple, but it was hiding a bigger truth. That made the problem feel ulterior because the real trouble was not the first thing they saw.",
        ),
        QAItem(
            question="How did they solve the problem?",
            answer=f"They used {f['tool'].label} and then {f['plan'].method}. That helped them find {problem.real_issue} instead of getting fooled by {problem.fake_issue}.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a saloon?",
            answer="A saloon is an old-style public room with doors, tables, and a rough wooden feel. In stories, it can be a place where something important needs fixing.",
        ),
        QAItem(
            question="What does inherit mean?",
            answer="To inherit means to receive something because it was passed on from someone before you. It can be money, a key, a room, or another kind of gift.",
        ),
        QAItem(
            question="What does problem solving mean?",
            answer="Problem solving means noticing what is wrong, thinking carefully, and choosing a useful fix. It is often better than rushing in without looking.",
        ),
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
    lines.append(f"  fired rules: {sorted(n for n, *_ in world.fired)}")
    return "\n".join(lines)


ASP_RULES = r"""
solved :- tool_used, chosen_plan.
tool_used :- tool(T), power(T, P), P >= 1.
chosen_plan :- plan(P), power(P, K), K >= 1.
valid(S, P, T) :- setting(S), problem(P), plan(T).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for pid, p in PROBLEMS.items():
        lines.append(asp.fact("problem", pid))
        lines.append(asp.fact("urgency", pid, p.urgency))
    for tid in TOOLS:
        lines.append(asp.fact("tool", tid))
        lines.append(asp.fact("power", tid, 1))
    for pid in PLANS:
        lines.append(asp.fact("plan", pid))
        lines.append(asp.fact("power", pid, PLANS[pid].power))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    rc = 0
    if set(asp_valid_combos()) != set(valid_combos()):
        print("MISMATCH: ASP and Python valid_combos disagree.")
        rc = 1
    else:
        print(f"OK: gate matches valid_combos() ({len(valid_combos())} combos).")
    sample = generate(resolve_params(argparse.Namespace(
        setting=None, problem=None, tool=None, plan=None,
        hero=None, hero_gender=None, friend=None, friend_gender=None,
        trait=None, seed=None
    ), random.Random(7)))
    if not sample.story.strip():
        print("MISMATCH: story generation produced empty output.")
        rc = 1
    else:
        print("OK: story generation smoke test passed.")
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A superhero problem-solving story world.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--problem", choices=PROBLEMS)
    ap.add_argument("--tool", choices=TOOLS)
    ap.add_argument("--plan", choices=PLANS)
    ap.add_argument("--hero")
    ap.add_argument("--hero-gender", choices=["girl", "boy"])
    ap.add_argument("--friend")
    ap.add_argument("--friend-gender", choices=["girl", "boy"])
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
    combos = valid_combos()
    if not combos:
        raise StoryError("No valid story combinations exist.")

    filtered = [
        c for c in combos
        if (args.setting is None or c[0] == args.setting)
        and (args.problem is None or c[1] == args.problem)
        and (args.tool is None or c[2] == args.tool)
        and (args.plan is None or c[2] == args.tool or True)
    ]
    if not filtered:
        raise StoryError("(No valid combination matches the given options.)")

    setting, problem, tool_id = rng.choice(sorted(filtered))
    plan_id = args.plan or rng.choice(sorted(PLANS))
    tool = args.tool or tool_id
    problem_obj = PROBLEMS[problem]

    hero_gender = args.hero_gender or "girl"
    friend_gender = args.friend_gender or "boy"
    hero = args.hero or rng.choice(GIRL_NAMES if hero_gender == "girl" else BOY_NAMES)
    friend_pool = [n for n in (GIRL_NAMES if friend_gender == "girl" else BOY_NAMES) if n != hero]
    friend = args.friend or rng.choice(friend_pool)
    trait = args.trait or rng.choice(TRAITS)
    return StoryParams(setting, problem, tool, plan_id, hero, hero_gender, friend, friend_gender, trait)


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.setting], PROBLEMS[params.problem], TOOLS[params.tool], PLANS[params.plan],
                 params.hero, params.friend, params.hero_gender, params.friend_gender)
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
    StoryParams("saloon", "false_alarm", "magnifier", "ask", "Nova", "girl", "Torch", "boy", "careful"),
    StoryParams("museum", "missing_map", "scanner", "follow", "Mira", "girl", "Kai", "boy", "clever"),
    StoryParams("station", "stuck_gate", "lamp", "lift", "Ruby", "girl", "Finn", "boy", "steady"),
]


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("", "#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"{len(asp_valid_combos())} compatible combos:")
        for row in asp_valid_combos():
            print("  ", row)
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
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for idx, sample in enumerate(samples):
        header = f"### variant {idx + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if idx < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")
if __name__ == "__main__":
    main()

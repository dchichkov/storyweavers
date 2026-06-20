#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/yenta_rewrite_geology_ist_flashback_inner_monologue.py
=======================================================================================

A standalone storyworld for a tiny superhero-style domain with:
- a geology-ist hero
- a chatty yenta who notices clues
- a rewrite of a rescue plan
- a flashback beat
- an inner-monologue beat
- a teamwork resolution

The story world builds a small causal simulation around a city emergency:
a rumor or clue is confusing at first, the hero remembers an earlier flashback,
the team thinks through the problem, rewrites the plan, and works together to
save the day.

It supports the standard storyworld CLI:
    --seed, -n, --all, --trace, --qa, --json, --asp, --verify, --show-asp
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
MIND_MIN = 1.0


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
        female = {"girl", "mother", "mom", "woman"}
        male = {"boy", "father", "dad", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return self.label or self.id



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
    damage: str
    clue: str
    danger: str
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
    rumor: str
    actual: str
    symptom: str
    cause: str
    severity: int
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
class Tool:
    id: str
    label: str
    effect: str
    power: int
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
    out = []
    for e in list(world.entities.values()):
        if e.meters["alarm"] < THRESHOLD:
            continue
        sig = ("alarm", e.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        world.get("team").memes["pressure"] += 1
        out.append("__alarm__")
    return out


def _r_teamwork(world: World) -> list[str]:
    out = []
    team = world.entities.get("team")
    if not team or team.memes["teamwork"] < THRESHOLD:
        return out
    sig = ("teamwork",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    team.meters["coordination"] += 1
    out.append("__teamwork__")
    return out


CAUSAL_RULES = [Rule("alarm", "social", _r_alarm), Rule("teamwork", "social", _r_teamwork)]


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


def problem_risk(problem: Problem, setting: Setting) -> bool:
    return problem.id in setting.tags or problem.actual in setting.tags


def choose_tool(problem: Problem, setting: Setting) -> Optional[Tool]:
    if problem.id == "sinkhole" and "bridge" in setting.tags:
        return TOOLS["reinforce"]
    if problem.id == "rockslide" and "tunnel" in setting.tags:
        return TOOLS["shovel"]
    if problem.id == "powerout" and "street" in setting.tags:
        return TOOLS["light"]
    return None


def predict(world: World, setting: Setting, problem: Problem) -> dict:
    sim = world.copy()
    _do_problem(sim, setting, problem, narrate=False)
    return {
        "alarm": sim.get("city").meters["alarm"],
        "pressure": sim.get("team").memes["pressure"],
    }


def _do_problem(world: World, setting: Setting, problem: Problem, narrate: bool = True) -> None:
    city = world.get("city")
    city.meters["alarm"] += problem.severity
    city.meters[problem.id] += 1
    propagate(world, narrate=narrate)


def intro(world: World, hero: Entity, partner: Entity, yenta: Entity, setting: Setting) -> None:
    world.say(
        f"{hero.id} was a geology-ist superhero who listened to the city the way other heroes listened for sirens. "
        f"On a bright day in {setting.place}, {partner.id} flew beside {hero.id}, and {yenta.id} waved from the corner with a notebook full of neighborhood news."
    )
    world.say(
        f'"{yenta.id} knows every rooftop rumor," {partner.id} said. "But {hero.id} knows every crack in the ground."'
    )


def flashback(world: World, hero: Entity, setting: Setting, problem: Problem) -> None:
    hero.memes["memory"] += 1
    world.say(
        f"As the wind changed, {hero.id} had a flashback to an older rescue. Back then, a broken bridge had looked harmless until the stones slipped."
    )
    world.say(
        f'{hero.id} took a slow breath. In {hero.pronoun("possessive")} inner monologue, {hero.pronoun()} thought, '
        f'"If the ground sounded wrong once before, it can sound wrong again. I need to check the clues, not the rumor."'
    )


def rumor(world: World, yenta: Entity, problem: Problem, setting: Setting) -> None:
    yenta.memes["talk"] += 1
    world.say(
        f"{yenta.id} hurried over and blurted, \"There is a {problem.rumor} near the {setting.place}!\" "
        f"She was a real yenta, always rushing in with half a story and a full voice."
    )


def assess(world: World, hero: Entity, partner: Entity, problem: Problem) -> None:
    hero.memes["focus"] += 1
    partner.memes["trust"] += 1
    world.say(
        f"{hero.id} knelt by the ground and tapped the stone. {partner.id} kept watch above, while {hero.id} listened for the hidden shake."
    )


def rewrite_plan(world: World, hero: Entity, partner: Entity, tool: Tool, problem: Problem) -> None:
    hero.memes["teamwork"] += 1
    partner.memes["teamwork"] += 1
    world.say(
        f'"We need to rewrite the rescue plan," {hero.id} said. "No guessing. We check, mark, and fix together."'
    )
    world.say(
        f"{partner.id} nodded at once. {partner.id} flashed the signal lights, and {hero.id} used {tool.label} to guide the path."
    )


def solve(world: World, hero: Entity, partner: Entity, tool: Tool, setting: Setting, problem: Problem) -> None:
    city = world.get("city")
    city.meters["alarm"] = max(0.0, city.meters["alarm"] - tool.power)
    city.memes["relief"] += 1
    world.say(
        f"Together they used {tool.label} to {tool.effect}. The danger faded, and the shaky place in {setting.place} held still again."
    )
    world.say(
        f"{yenta_name(world)} leaned over the railing and gasped, then laughed when she saw the heroes had fixed the real problem instead of chasing the rumor."
    )
    world.say(
        f"By sunset, {hero.id} and {partner.id} stood side by side on the safe street, and the city lights blinked on like tiny stars."
    )


def yenta_name(world: World) -> str:
    return world.facts["yenta"].id


def tell(setting: Setting, problem: Problem, tool: Tool, hero_name: str = "Nova",
         partner_name: str = "Bolt", yenta_name_: str = "Gertie") -> World:
    world = World()
    hero = world.add(Entity(id=hero_name, kind="character", type="girl", role="hero", label="the geology-ist"))
    partner = world.add(Entity(id=partner_name, kind="character", type="boy", role="partner", label="the teammate"))
    yenta = world.add(Entity(id=yenta_name_, kind="character", type="woman", role="yenta", label="the yenta"))
    city = world.add(Entity(id="city", kind="place", type="city", label=setting.place))
    team = world.add(Entity(id="team", kind="group", type="team", label="the team"))

    world.facts.update(hero=hero, partner=partner, yenta=yenta, city=city, team=team, setting=setting, problem=problem, tool=tool)

    intro(world, hero, partner, yenta, setting)
    world.para()
    rumor(world, yenta, problem, setting)
    flashback(world, hero, setting, problem)
    assess(world, hero, partner, problem)
    world.para()
    rewrite_plan(world, hero, partner, tool, problem)
    _do_problem(world, setting, problem, narrate=False)
    solve(world, hero, partner, tool, setting, problem)
    return world


SETTINGS = {
    "bridge": Setting("bridge", "the old bridge", "cracked stones", "bridge rumble", {"bridge", "street"}),
    "caves": Setting("caves", "the river cave", "fallen pebbles", "cave echo", {"tunnel", "cave"}),
    "subway": Setting("subway", "the subway platform", "shaking tiles", "train rumble", {"street", "tunnel"}),
}

PROBLEMS = {
    "sinkhole": Problem("sinkhole", "sinkhole", "ground drop", "the sidewalk dipped", "rain and loose dirt", 2, {"bridge", "street"}),
    "rockslide": Problem("rockslide", "rockslide", "rocks falling", "stones tumbled", "a cracked ledge", 2, {"tunnel", "cave"}),
    "powerout": Problem("powerout", "power outage", "darkness", "the lights went out", "a blown line", 1, {"street", "tunnel"}),
}

TOOLS = {
    "reinforce": Tool("reinforce", "reinforcement beams", "brace the bridge", 2, {"bridge"}),
    "shovel": Tool("shovel", "a rescue shovel", "clear the fallen stones", 2, {"tunnel", "cave"}),
    "light": Tool("light", "portable lanterns", "shine a path forward", 1, {"street", "tunnel"}),
}



@dataclass
class StoryParams:
    setting: str
    problem: str
    tool: str
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

CURATED = [
    ("bridge", "sinkhole", "reinforce"),
    ("caves", "rockslide", "shovel"),
    ("subway", "powerout", "light"),
]



def valid_combos() -> list[tuple[str, str, str]]:
    out = []
    for sid, s in SETTINGS.items():
        for pid, p in PROBLEMS.items():
            if not problem_risk(p, s):
                continue
            for tid, t in TOOLS.items():
                if t.id == choose_tool(p, s).id:
                    out.append((sid, pid, tid))
    return out


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a superhero story that includes the words "yenta", "rewrite", and "geology-ist".',
        f"Tell a story where {f['hero'].id} the geology-ist, {f['partner'].id}, and the yenta work as a team to fix a problem in {f['setting'].place}.",
        f"Write a flashback-driven superhero rescue where a rumor is wrong, the hero thinks it through, and the team rewrites the plan together.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    hero, partner, yenta, setting, problem, tool = f["hero"], f["partner"], f["yenta"], f["setting"], f["problem"], f["tool"]
    return [
        ("Who is the story about?",
         f"It is about {hero.id}, a geology-ist superhero, and {partner.id}, who helped on the rescue. {yenta.id}, the yenta, also brought the first rumor."),
        ("Why did {0} remember the old rescue?".format(hero.id),
         f"{hero.id} had a flashback because the new problem sounded like an old crack in the ground. That memory helped {hero.id} pause and check the clues instead of trusting the rumor."),
        ("How did they solve the problem?",
         f"They rewrote the rescue plan and used {tool.label} together. The teamwork let them fix the real danger in {setting.place} instead of chasing the wrong story."),
    ]


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    return [
        ("What does a geology-ist study?",
         "A geology-ist studies rocks, stones, soil, and the ground. That helps the geology-ist understand how the earth may crack or shift."),
        ("What is a flashback in a story?",
         "A flashback is when the story remembers something that happened earlier. It helps explain why a character thinks a certain way now."),
        ("What is teamwork?",
         "Teamwork is when people help each other and do a job together. Each helper uses a different skill, and that can make the job easier."),
        ("What does it mean to rewrite something?",
         "To rewrite something means to change the words or the plan and make it better. A hero might rewrite a rescue plan when the first idea is not safe enough."),
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
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    return "\n".join(lines)


ASP_RULES = r"""
risk(S,P) :- setting(S), problem(P).
teamwork :- helper(hero), helper(partner).
rewrite_plan :- risk(S,P), tool(T), chosen_tool(T).
ending(solved) :- rewrite_plan, teamwork.
"""


def asp_facts() -> str:
    import asp
    lines = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for pid in PROBLEMS:
        lines.append(asp.fact("problem", pid))
    for tid in TOOLS:
        lines.append(asp.fact("tool", tid))
    lines.append(asp.fact("helper", "hero"))
    lines.append(asp.fact("helper", "partner"))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    import asp
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    rc = 0
    if py == cl:
        print(f"OK: gate matches valid_combos() ({len(py)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid_combos():")
        print("  only python:", sorted(py - cl))
        print("  only clingo:", sorted(cl - py))
    # smoke test
    sample = generate(StoryParams(*CURATED[0]))
    if not sample.story.strip():
        print("MISMATCH: empty story")
        return 1
    print("OK: generation smoke test passed.")
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Superhero story world: yenta, rewrite, geology-ist.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--problem", choices=PROBLEMS)
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
    combos = valid_combos()
    if args.setting:
        combos = [c for c in combos if c[0] == args.setting]
    if args.problem:
        combos = [c for c in combos if c[1] == args.problem]
    if args.tool:
        combos = [c for c in combos if c[2] == args.tool]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    sid, pid, tid = rng.choice(sorted(combos))
    return StoryParams(sid, pid, tid)


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.setting], PROBLEMS[params.problem], TOOLS[params.tool])
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
        print(asp_program("", "#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"{len(valid_combos())} compatible combos:\n")
        for s, p, t in valid_combos():
            print(f"  {s:8} {p:10} {t}")
        return
    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(StoryParams(*c)) for c in CURATED]
    else:
        seen = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 50, 50):
            params = resolve_params(args, random.Random(base_seed + i))
            sample = generate(params)
            if sample.story not in seen:
                seen.add(sample.story)
                samples.append(sample)
            i += 1
    if args.json:
        print(samples[0].to_json() if len(samples) == 1 else json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return
    for i, sample in enumerate(samples):
        emit(sample, trace=args.trace, qa=args.qa, header=(f"### variant {i+1}" if len(samples) > 1 else ""))
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()

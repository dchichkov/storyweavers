#!/usr/bin/env python3
"""
A small superhero story world about a koala, a cog, repetition, and magic.

The story model:
- A hero sees a problem in a city scene.
- A magic cog causes a repeated mishap.
- The hero uses a repeating spell and a tool to fix it.
- The ending shows the city safe again.

This file is self-contained and follows the Storyweavers world contract.
"""

from __future__ import annotations

import argparse
import json
import os
import random
import sys
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
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"koala", "hero"}:
            return {"subject": "they", "object": "them", "possessive": "their"}[case]
        if self.type in {"girl", "woman", "mother"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man", "father"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str = "the clock tower square"
    affords: set[str] = field(default_factory=set)


@dataclass
class Power:
    name: str
    verb: str
    result: str
    repeat_word: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Problem:
    id: str
    label: str
    phrase: str
    risk: str
    zone: set[str]
    tags: set[str] = field(default_factory=set)


@dataclass
class Fix:
    id: str
    label: str
    prep: str
    tail: str
    guards: set[str] = field(default_factory=set)
    helps_repeat: bool = False
    helps_magic: bool = False


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
        self.facts: dict = {}
        self.echoes: int = 0

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
        import copy
        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.paragraphs = [[]]
        clone.fired = set(self.fired)
        clone.facts = dict(self.facts)
        clone.echoes = self.echoes
        return clone


@dataclass
class StoryParams:
    place: str
    hero_name: str
    sidekick: str
    problem: str
    power: str
    fix: str
    seed: Optional[int] = None


SETTINGS = {
    "clock_square": Setting(place="the clock tower square", affords={"jam", "echo"}),
    "museum": Setting(place="the museum hall", affords={"echo", "glow"}),
    "harbor": Setting(place="the harbor pier", affords={"jam", "glow"}),
}

POWERS = {
    "repeat": Power(
        name="repetition magic",
        verb="repeat the saving spell",
        result="the spell made the broken thing work again",
        repeat_word="Again!",
        tags={"repetition", "magic"},
    ),
    "spark": Power(
        name="magic sparkles",
        verb="spin a bright spell",
        result="the bright spell pushed the trouble back",
        repeat_word="Once more!",
        tags={"magic"},
    ),
}

PROBLEMS = {
    "jam": Problem(
        id="jam",
        label="jammed gear",
        phrase="a jammed clock cog",
        risk="stuck",
        zone={"hands"},
        tags={"cog", "repetition"},
    ),
    "echo": Problem(
        id="echo",
        label="echo trouble",
        phrase="a loud echo that kept repeating",
        risk="overwhelming",
        zone={"ears"},
        tags={"repetition"},
    ),
    "glow": Problem(
        id="glow",
        label="glow leak",
        phrase="a glowing crack in the city wall",
        risk="spreading",
        zone={"eyes"},
        tags={"magic"},
    ),
}

FIXES = {
    "wrench": Fix(
        id="wrench",
        label="a shiny wrench",
        prep="grab a shiny wrench and steady the cog",
        tail="turned the cog just enough to free it",
        guards={"jam"},
        helps_repeat=False,
        helps_magic=False,
    ),
    "chant": Fix(
        id="chant",
        label="a repeating chant",
        prep="say a repeating chant in a calm voice",
        tail="let the magic loop settle into a gentle rhythm",
        guards={"echo", "glow"},
        helps_repeat=True,
        helps_magic=True,
    ),
    "shield": Fix(
        id="shield",
        label="a moon shield",
        prep="raise a moon shield to hold back the light",
        tail="kept the glow from spreading farther",
        guards={"glow"},
        helps_repeat=False,
        helps_magic=True,
    ),
}

KOALA_NAMES = ["Kiki", "Milo", "Pip", "Luna", "Ari", "Nori", "Zig", "Poppy"]
HELPER_NAMES = ["Bea", "Tad", "Nia", "Ezra", "June", "Otis"]


def valid_combos() -> list[tuple[str, str, str]]:
    out = []
    for place, setting in SETTINGS.items():
        for problem_id in setting.affords:
            for power_id, power in POWERS.items():
                for fix_id, fix in FIXES.items():
                    problem = PROBLEMS[problem_id]
                    if problem_id in fix.guards and (power.helps_repeat or power.helps_magic):
                        out.append((place, problem_id, power_id))
                    elif problem_id in fix.guards and fix.id == "wrench" and problem_id == "jam":
                        out.append((place, problem_id, power_id))
    return sorted(set(out))


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A superhero story world about a koala and a cog.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--problem", choices=PROBLEMS)
    ap.add_argument("--power", choices=POWERS)
    ap.add_argument("--fix", choices=FIXES)
    ap.add_argument("--hero-name")
    ap.add_argument("--sidekick")
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
    combos = [(p, prob, powr, fix)
              for p in SETTINGS
              for prob in SETTINGS[p].affords
              for powr in POWERS
              for fix in FIXES
              if args.place in (None, p)
              and args.problem in (None, prob)
              and args.power in (None, powr)
              and args.fix in (None, fix)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, problem, power, fix = rng.choice(combos)
    hero_name = args.hero_name or rng.choice(KOALA_NAMES)
    sidekick = args.sidekick or rng.choice(HELPER_NAMES)
    return StoryParams(place=place, hero_name=hero_name, sidekick=sidekick,
                       problem=problem, power=power, fix=fix)


def reasonableness_gate(params: StoryParams) -> None:
    problem = PROBLEMS[params.problem]
    fix = FIXES[params.fix]
    power = POWERS[params.power]
    if params.problem not in fix.guards:
        raise StoryError("That fix would not honestly solve the problem.")
    if params.problem == "jam" and params.fix != "wrench":
        raise StoryError("A jammed cog needs a wrench or a similar careful tool.")
    if params.problem == "echo" and not fix.helps_repeat:
        raise StoryError("Echo trouble needs a fix that calms repetition.")
    if params.problem == "glow" and not fix.helps_magic:
        raise StoryError("Glow trouble needs a magical fix.")
    if "cog" not in problem.tags and params.problem == "jam":
        raise StoryError("The jam story needs the cog problem to be central.")
    if power.name == "repetition magic" and params.problem == "jam" and params.fix == "shield":
        raise StoryError("A shield does not help a jammed cog turn again.")


def tell(params: StoryParams) -> World:
    reasonableness_gate(params)
    world = World(SETTINGS[params.place])
    hero = world.add(Entity(id=params.hero_name, kind="character", type="koala", label=params.hero_name))
    sidekick = world.add(Entity(id=params.sidekick, kind="character", type="hero", label=params.sidekick))
    problem = world.add(Entity(id="problem", type="thing", label=PROBLEMS[params.problem].label,
                               phrase=PROBLEMS[params.problem].phrase))
    fix = world.add(Entity(id="fix", type="thing", label=FIXES[params.fix].label,
                           phrase=FIXES[params.fix].label))
    cog = world.add(Entity(id="cog", type="thing", label="cog", phrase="a little brass cog"))
    world.facts.update(hero=hero, sidekick=sidekick, problem=problem, fix=fix, cog=cog,
                       params=params, power=POWERS[params.power], place=SETTINGS[params.place])

    hero.memes["brave"] = 1
    hero.memes["care"] = 1
    world.say(f"{hero.id} was a tiny superhero koala with bright paws and a bold cape.")
    world.say(f"{hero.id} liked helping people in {world.setting.place}, where every street could become an adventure.")
    world.say(f"One day, {hero.id} saw {problem.phrase} near the clockwork heart of the city.")
    world.para()
    world.say(f"The trouble kept coming back again and again, like a worry that would not sit still.")
    world.say(f"{hero.id} said, \"{POWERS[params.power].repeat_word}\" and tried {POWERS[params.power].verb}.")
    world.say(f"{params.sidekick} hurried beside {hero.id} and pointed to the little cog that kept slipping.")
    world.say(f"That meant the team had to fix the cog before the city could feel calm again.")
    world.para()
    if params.fix == "wrench":
        world.say(f"{hero.id} chose to {FIXES[params.fix].prep}.")
        world.say(f"{FIXES[params.fix].tail.capitalize()}.")
        world.say(f"The cog clicked into place, and the jammed machine began to spin.")
    elif params.fix == "chant":
        world.say(f"{hero.id} chose to {FIXES[params.fix].prep}.")
        world.say(f"{FIXES[params.fix].tail.capitalize()}.")
        world.say(f"The repeating magic softened the strange loop until it sounded friendly.")
    else:
        world.say(f"{hero.id} chose to {FIXES[params.fix].prep}.")
        world.say(f"{FIXES[params.fix].tail.capitalize()}.")
        world.say(f"The glow shrank, and the city wall looked safe again.")
    world.say(f"At the end, {hero.id} stood under the lantern light, and the brave little cog turned once more.")
    return world


def generate(params: StoryParams) -> StorySample:
    world = tell(params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    params: StoryParams = f["params"]
    return [
        "Write a short superhero story for a young child about a koala, a cog, repetition, and magic.",
        f"Tell a gentle hero story where {params.hero_name} the koala helps at {params.place} when a cog problem keeps repeating.",
        f"Write a simple adventure that includes the words 'koala' and 'cog' and ends with the city safe again.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    params: StoryParams = f["params"]
    hero: Entity = f["hero"]
    sidekick: Entity = f["sidekick"]
    problem: Entity = f["problem"]
    fix: Entity = f["fix"]
    power: Power = f["power"]
    return [
        QAItem(
            question=f"Who is the hero of the story?",
            answer=f"The hero is {hero.id}, a tiny superhero koala who likes helping in {world.setting.place}.",
        ),
        QAItem(
            question=f"What was wrong in the city?",
            answer=f"The city had {problem.phrase}, and it kept causing trouble again and again.",
        ),
        QAItem(
            question=f"What did {hero.id} use to help?",
            answer=f"{hero.id} used {fix.label} and {power.name} to calm the problem down.",
        ),
        QAItem(
            question=f"Who helped {hero.id} near the end?",
            answer=f"{sidekick.id} helped by staying close and pointing out the slipping cog.",
        ),
        QAItem(
            question=f"How did the story end?",
            answer=f"It ended with the problem solved, the cog turning again, and the city feeling safe.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a cog?",
            answer="A cog is a toothed wheel that helps machines move and turn in a useful way.",
        ),
        QAItem(
            question="What does repetition mean?",
            answer="Repetition means doing or saying something again and again.",
        ),
        QAItem(
            question="What is magic in a story?",
            answer="Magic is special power that can do surprising things in a story world.",
        ),
        QAItem(
            question="What is a superhero?",
            answer="A superhero is a brave helper who uses special skills to protect others.",
        ),
    ]


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    return "\n".join(lines)


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
    lines.append("== (3) World knowledge questions ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


CURATED = [
    StoryParams(place="clock_square", hero_name="Kiki", sidekick="Bea", problem="jam", power="repeat", fix="wrench"),
    StoryParams(place="museum", hero_name="Milo", sidekick="Tad", problem="echo", power="repeat", fix="chant"),
    StoryParams(place="harbor", hero_name="Pip", sidekick="Nia", problem="glow", power="spark", fix="shield"),
]


ASP_RULES = r"""
% Facts:
% place(P), problem(Pr), power(Pw), fix(F)
% affinities:
% affords(P, Pr)
% guards(F, Pr)
% repeat_power(Pw)
% magic_power(Pw)
% repeat_fix(F)
% magic_fix(F)

valid(P, Pr, Pw, F) :- affords(P, Pr), guards(F, Pr), problem_ok(Pr, F, Pw).
problem_ok(jam, wrench, Pw) :- repeat_power(Pw).
problem_ok(echo, chant, Pw) :- repeat_power(Pw).
problem_ok(glow, shield, Pw) :- magic_power(Pw).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid, setting in SETTINGS.items():
        lines.append(asp.fact("place", pid))
        for pr in sorted(setting.affords):
            lines.append(asp.fact("affords", pid, pr))
    for pr_id, pr in PROBLEMS.items():
        lines.append(asp.fact("problem", pr_id))
    for pw_id, pw in POWERS.items():
        lines.append(asp.fact("power", pw_id))
        if "repetition" in pw.tags:
            lines.append(asp.fact("repeat_power", pw_id))
        if "magic" in pw.tags:
            lines.append(asp.fact("magic_power", pw_id))
    for f_id, fx in FIXES.items():
        lines.append(asp.fact("fix", f_id))
        for pr in sorted(fx.guards):
            lines.append(asp.fact("guards", f_id, pr))
        if fx.helps_repeat:
            lines.append(asp.fact("repeat_fix", f_id))
        if fx.helps_magic:
            lines.append(asp.fact("magic_fix", f_id))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/4."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    print("only in python:", sorted(py - cl))
    print("only in clingo:", sorted(cl - py))
    return 1


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
        import asp
        model = asp.one_model(asp_program("#show valid/4."))
        print(sorted(set(asp.atoms(model, "valid"))))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 20):
            seed = base_seed + i
            i += 1
            try:
                params = resolve_params(args, random.Random(seed))
                params.seed = seed
                sample = generate(params)
            except StoryError as err:
                print(err)
                return
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
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.hero_name}: {p.problem} at {p.place}"
        elif len(samples) > 1:
            header = f"### variant {idx + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if idx < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()

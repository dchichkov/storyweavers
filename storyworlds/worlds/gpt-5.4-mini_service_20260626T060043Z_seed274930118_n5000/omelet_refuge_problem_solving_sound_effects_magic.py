#!/usr/bin/env python3
"""
A standalone story world: omelet, refuge, problem solving, sound effects, and a
little splash of magic, told in a rhyming-story style.

The world premise:
- A child or small animal wants to make an omelet.
- A noisy problem appears outside, so they need refuge.
- They solve the problem with simple steps, sound effects, and a tiny magical
  helper.
- The ending proves the refuge is cozy and the omelet is complete.
"""

from __future__ import annotations

import argparse
import json
import os
import random
import re
import sys
from dataclasses import dataclass, field
from typing import Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from results import QAItem, StoryError, StorySample  # noqa: E402


# ---------------------------------------------------------------------------
# Shared helpers
# ---------------------------------------------------------------------------

def _article(noun: str) -> str:
    return "an" if noun[:1].lower() in "aeiou" else "a"


def _cap(s: str) -> str:
    return s[:1].upper() + s[1:] if s else s


def _join_clauses(parts: list[str]) -> str:
    parts = [p.strip() for p in parts if p and p.strip()]
    if not parts:
        return ""
    if len(parts) == 1:
        return parts[0]
    if len(parts) == 2:
        return parts[0] + " and " + parts[1]
    return ", ".join(parts[:-1]) + ", and " + parts[-1]


# ---------------------------------------------------------------------------
# World entities
# ---------------------------------------------------------------------------

@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    plural: bool = False
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "mother", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        if self.plural:
            return {"subject": "they", "object": "them", "possessive": "their"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def ref(self) -> str:
        return self.label or self.type

    def obj(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    name: str
    cozy: bool = True
    affords: set[str] = field(default_factory=set)


@dataclass
class Problem:
    id: str
    noun: str
    sound: str
    danger: str
    leak: str
    zone: str
    tag: str = ""


@dataclass
class Fix:
    id: str
    label: str
    prep: str
    effect: str
    covers: set[str] = field(default_factory=set)
    quiets: set[str] = field(default_factory=set)
    magical: bool = False


@dataclass
class OmeletGoal:
    label: str = "omelet"
    phrase: str = "a fluffy omelet"
    verb: str = "make an omelet"
    action: str = "whisk the eggs"
    finish: str = "flip the omelet"
    aroma: str = "golden and warm"


@dataclass
class StoryParams:
    setting: str
    problem: str
    fix: str
    name: str
    gender: str
    parent: str
    trait: str
    seed: Optional[int] = None


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
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


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------

SETTINGS = {
    "kitchen": Setting(name="the kitchen", cozy=True, affords={"cook", "refuge"}),
    "cottage": Setting(name="the cottage", cozy=True, affords={"cook", "refuge"}),
    "treehouse": Setting(name="the treehouse", cozy=True, affords={"cook", "refuge"}),
}

PROBLEMS = {
    "wind": Problem(
        id="wind",
        noun="wind",
        sound="whoooosh",
        danger="blew the towel off the table",
        leak="cold air slipped in",
        zone="window",
        tag="weather",
    ),
    "rain": Problem(
        id="rain",
        noun="rain",
        sound="pitter-patter",
        danger="spattered the sill",
        leak="drip-drip",
        zone="roof",
        tag="weather",
    ),
    "clatter": Problem(
        id="clatter",
        noun="clatter",
        sound="clink-clank",
        danger="jiggled the pan",
        leak="jingle-jangle",
        zone="floor",
        tag="noise",
    ),
    "dark": Problem(
        id="dark",
        noun="dark",
        sound="hush-hush",
        danger="made the room feel shy",
        leak="shade and hush",
        zone="lamp",
        tag="magic",
    ),
}

FIXES = {
    "blanket": Fix(
        id="blanket",
        label="a snug blanket fort",
        prep="tuck chairs together and drape a blanket over the top",
        effect="made a soft refuge",
        covers={"window", "floor"},
        quiets={"wind", "clatter"},
        magical=False,
    ),
    "lantern": Fix(
        id="lantern",
        label="a glowing lantern",
        prep="light the lantern with one bright spark",
        effect="pushed the dark away",
        covers={"lamp"},
        quiets={"dark"},
        magical=True,
    ),
    "spell": Fix(
        id="spell",
        label="a tiny rhyme spell",
        prep="whisper a sparkle rhyme and tap the spoon three times",
        effect="zipped the bad problem smaller",
        covers={"window", "roof", "floor", "lamp"},
        quiets={"wind", "rain", "clatter", "dark"},
        magical=True,
    ),
}

GOLDEN_GOAL = OmeletGoal()

NAMES = {
    "girl": ["Mia", "Luna", "Nora", "Ivy", "Ruby"],
    "boy": ["Leo", "Finn", "Theo", "Max", "Eli"],
}
TRAITS = ["brave", "curious", "cheery", "gentle", "spry"]
PARENTS = {"mother": "mom", "father": "dad"}


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------

ASP_RULES = r"""
% A problem can be sheltered when a fix quiets it and covers its zone.
sheltered(P, F) :- problem(P), fix(F), quiets(F, P), covers(F, Z), problem_zone(P, Z).
usable(F, P) :- problem(P), fix(F), sheltered(P, F).
valid_story(S, P, F) :- setting(S), problem(P), fix(F), usable(F, P), setting_affords(S, refuge).
"""

def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid, s in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        if s.cozy:
            lines.append(asp.fact("setting_affords", sid, "refuge"))
        lines.append(asp.fact("setting_affords", sid, "cook"))
    for pid, p in PROBLEMS.items():
        lines.append(asp.fact("problem", pid))
        lines.append(asp.fact("problem_zone", pid, p.zone))
        lines.append(asp.fact("quiets", "spell", pid) if pid in FIXES["spell"].quiets else "")
        lines.append(asp.fact("quiets", "blanket", pid) if pid in FIXES["blanket"].quiets else "")
        lines.append(asp.fact("quiets", "lantern", pid) if pid in FIXES["lantern"].quiets else "")
    for fid, f in FIXES.items():
        lines.append(asp.fact("fix", fid))
        for z in sorted(f.covers):
            lines.append(asp.fact("covers", fid, z))
        for pid in sorted(f.quiets):
            lines.append(asp.fact("quiets", fid, pid))
    return "\n".join(x for x in lines if x)

def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"

def asp_valid_stories() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/3."))
    return sorted(set(asp.atoms(model, "valid_story")))

def asp_verify() -> int:
    py = set(valid_stories())
    cl = set(asp_valid_stories())
    if py == cl:
        print(f"OK: ASP matches Python ({len(py)} stories).")
        return 0
    print("MISMATCH:")
    print("only in Python:", sorted(py - cl))
    print("only in ASP:", sorted(cl - py))
    return 1


# ---------------------------------------------------------------------------
# Reasonableness gates
# ---------------------------------------------------------------------------

def valid_stories() -> list[tuple[str, str, str]]:
    out: list[tuple[str, str, str]] = []
    for s in SETTINGS:
        for p in PROBLEMS:
            for f in FIXES:
                if is_reasonable(s, p, f):
                    out.append((s, p, f))
    return out

def is_reasonable(setting: str, problem: str, fix: str) -> bool:
    return setting in SETTINGS and problem in PROBLEMS and fix in FIXES

def explain_rejection(setting: str, problem: str, fix: str) -> str:
    return (
        f"(No story: the combination {setting}/{problem}/{fix} is not one of the "
        f"small, steady problem-solving patterns in this world.)"
    )


# ---------------------------------------------------------------------------
# Story generation
# ---------------------------------------------------------------------------

def _rhyming_opening(hero: Entity, goal: OmeletGoal, setting: Setting) -> str:
    return (
        f"{hero.id} had a wish so bright and light: to {goal.verb} just right. "
        f"In {setting.name}, so warm and sweet, {hero.pronoun('subject').capitalize()} "
        f"set out to make the day complete."
    )

def _problem_line(problem: Problem) -> str:
    return f"Then came {problem.sound}, all {problem.noun} and frown, and {problem.danger} in the little town."

def _solution_line(fix: Fix, problem: Problem) -> str:
    if fix.magical:
        return f"{fix.prep}, and—zip-zap-zoom!—the {problem.noun} grew small with a silver broom."
    return f"{fix.prep}, and—tap-tap—hop!—the {problem.noun} lost its grip and had to stop."

def _ending_line(hero: Entity, goal: OmeletGoal, fix: Fix, parent: Entity, setting: Setting) -> str:
    return (
        f"So {hero.id} could {goal.action}, then {goal.finish} with a sunny grin. "
        f"The {fix.label} made a refuge, and the {goal.label} came out golden within. "
        f"{parent.ref().capitalize()} clapped, 'Well done!' and the cozy room shone clear; "
        f"with safe, soft refuge all around, their little feast rang near."
    )

def tell(params: StoryParams) -> World:
    setting = SETTINGS[params.setting]
    problem = PROBLEMS[params.problem]
    fix = FIXES[params.fix]
    world = World(setting)

    hero = world.add(Entity(
        id=params.name,
        kind="character",
        type=params.gender,
        label=params.name,
        meters={"hope": 1.0, "courage": 1.0},
        memes={"delight": 1.0},
    ))
    parent = world.add(Entity(
        id=params.parent,
        kind="character",
        type=params.parent,
        label=PARENTS[params.parent],
        meters={"care": 1.0},
        memes={"warmth": 1.0},
    ))
    omelet = world.add(Entity(
        id="omelet",
        kind="thing",
        type="omelet",
        label="omelet",
        phrase="a fluffy omelet",
        owner=hero.id,
        caretaker=parent.id,
        meters={"warmth": 0.0, "done": 0.0},
    ))
    refuge = world.add(Entity(
        id="refuge",
        kind="thing",
        type="refuge",
        label="refuge",
        phrase="a snug refuge",
        owner=hero.id,
        meters={"cozy": 0.0},
    ))

    # Act 1
    world.say(_rhyming_opening(hero, GOLDEN_GOAL, setting))
    world.say(f"{hero.id} loved to whisk and grin, for an omelet made the morning sing.")
    world.para()

    # Act 2
    world.say(f"Just then, {problem.sound} went through the air, and {problem.danger} with a worried stare.")
    world.say(f"{hero.id} and {parent.ref()} both looked around: they needed refuge, safe and sound.")
    hero.memes["worry"] = 1.0
    parent.memes["alert"] = 1.0
    world.facts["problem"] = problem
    world.facts["fix"] = fix
    world.facts["omelet"] = omelet
    world.facts["refuge"] = refuge
    world.para()

    # Act 3
    world.say(_solution_line(fix, problem))
    if fix.magical:
        world.say("A tiny shimmer swirled and sang, like twinkling bells that gently rang.")
        refuge.meters["cozy"] = 1.0
    else:
        refuge.meters["cozy"] = 0.8
    omelet.meters["warmth"] = 1.0
    omelet.meters["done"] = 1.0
    world.say(_ending_line(hero, GOLDEN_GOAL, fix, parent, setting))

    world.facts.update(hero=hero, parent=parent, setting=setting)
    return world


# ---------------------------------------------------------------------------
# QA
# ---------------------------------------------------------------------------

def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        'Write a short rhyming story for a child about an omelet and a refuge.',
        f"Tell a gentle rhyme where {f['hero'].id} solves a noisy problem and still gets to make an omelet.",
        "Write a simple magical story with sound effects like whoooosh or pitter-patter and a cozy refuge.",
    ]

def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero: Entity = f["hero"]
    parent: Entity = f["parent"]
    problem: Problem = f["problem"]
    fix: Fix = f["fix"]
    setting: Setting = f["setting"]
    qa = [
        QAItem(
            question=f"What did {hero.id} want to make in {setting.name}?",
            answer=f"{hero.id} wanted to make an omelet, warm and golden, while staying in {setting.name}.",
        ),
        QAItem(
            question=f"What noisy problem appeared before the omelet was done?",
            answer=f"The {problem.noun} problem appeared with a {problem.sound} sound, and it made the room feel unsettled.",
        ),
        QAItem(
            question=f"How did {hero.id} and {parent.ref()} solve the problem?",
            answer=f"They used {fix.label} to build refuge, so the trouble got smaller and the cooking could continue.",
        ),
    ]
    if fix.magical:
        qa.append(QAItem(
            question=f"What part of the solution was magical?",
            answer=f"The magical part was {fix.prep}, which was followed by a sparkle-like change that made the problem quiet.",
        ))
    return qa

def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is an omelet?",
            answer="An omelet is a soft dish made by cooking beaten eggs in a pan, often folded and served warm.",
        ),
        QAItem(
            question="What does refuge mean?",
            answer="Refuge means a safe place where someone can rest, hide from trouble, or feel protected.",
        ),
        QAItem(
            question="Why do sound effects help in stories?",
            answer="Sound effects help readers imagine what is happening, like wind, rain, or a magical spark.",
        ),
        QAItem(
            question="Why can magic be useful in a story?",
            answer="Magic can solve a problem in a gentle, surprising way when the story needs a small wonder.",
        ),
    ]


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Rhyming story world: omelet and refuge with problem solving, sound effects, and magic.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--problem", choices=PROBLEMS)
    ap.add_argument("--fix", choices=FIXES)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--parent", choices=["mother", "father"])
    ap.add_argument("--name")
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
    if args.setting and args.problem and args.fix:
        if not is_reasonable(args.setting, args.problem, args.fix):
            raise StoryError(explain_rejection(args.setting, args.problem, args.fix))
    setting = args.setting or rng.choice(list(SETTINGS))
    problem = args.problem or rng.choice(list(PROBLEMS))
    fix = args.fix or rng.choice(list(FIXES))
    if not is_reasonable(setting, problem, fix):
        raise StoryError(explain_rejection(setting, problem, fix))
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(NAMES[gender])
    parent = args.parent or rng.choice(["mother", "father"])
    trait = args.trait or rng.choice(TRAITS)
    return StoryParams(setting=setting, problem=problem, fix=fix, name=name, gender=gender, parent=parent, trait=trait)

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

def format_qa(sample: StorySample) -> str:
    out = ["== Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        out.append(f"{i}. {p}")
    out.append("")
    out.append("== Story QA ==")
    for q in sample.story_qa:
        out.append(f"Q: {q.question}")
        out.append(f"A: {q.answer}")
    out.append("")
    out.append("== World QA ==")
    for q in sample.world_qa:
        out.append(f"Q: {q.question}")
        out.append(f"A: {q.answer}")
    return "\n".join(out)

def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for e in world.entities.values():
        bits = []
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        lines.append(f"{e.id}: {e.type} {' '.join(bits)}")
    return "\n".join(lines)

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
        print(asp_program("#show valid_story/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        model = asp.one_model(asp_program("#show valid_story/3."))
        stories = sorted(set(asp.atoms(model, "valid_story")))
        print(f"{len(stories)} compatible stories:")
        for s in stories:
            print(" ", s)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)

    samples: list[StorySample] = []
    if args.all:
        combos = valid_stories()
        for setting, problem, fix in combos:
            params = StoryParams(
                setting=setting,
                problem=problem,
                fix=fix,
                name="Mia",
                gender="girl",
                parent="mother",
                trait="curious",
                seed=base_seed,
            )
            samples.append(generate(params))
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 40, 40):
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            sample = generate(params)
            if sample.story not in seen:
                seen.add(sample.story)
                samples.append(sample)
            i += 1

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

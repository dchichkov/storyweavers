#!/usr/bin/env python3
"""
storyworlds/worlds/season_pagan_cease_subway_station_problem_solving.py
======================================================================

A small, self-contained story world for a tall-tale, problem-solving subway
station tale with rhyme. The seed idea is a child in a subway station notices
a season sign gone haywire just as a pagan parade is due to pass through, and
the station crew must cease the confusion by solving the problem in a clever,
rhymed way.

The world model tracks:
- physical meters: noise, confusion, crowding, brightness, readiness
- emotional memes: worry, courage, delight, relief, patience

The story is built from a live simulation, not a frozen paragraph. The hero,
helper, problem, and solution all affect the state and shape the prose.
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
# Core world model
# ---------------------------------------------------------------------------

SEASONS = ["spring", "summer", "autumn", "winter"]

@dataclass
class Entity:
    id: str
    kind: str = "thing"  # character | thing
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)
    traits: list[str] = field(default_factory=list)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "woman"}
        male = {"boy", "father", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class Setting:
    place: str = "the subway station"
    tunnels: int = 2
    noises: list[str] = field(default_factory=lambda: ["rumble", "echo", "clang"])


@dataclass
class Problem:
    id: str
    label: str
    cause: str
    effect: str
    clue: str
    messy: str


@dataclass
class Fix:
    id: str
    label: str
    method: str
    rhymed_line: str
    result: str


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.lines: list[str] = []
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.fired: set[tuple] = set()

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


# ---------------------------------------------------------------------------
# Story parameters
# ---------------------------------------------------------------------------

@dataclass
class StoryParams:
    season: str
    problem: str
    fix: str
    name: str
    gender: str
    helper: str
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------

SETTINGS = {
    "subway_station": Setting(place="the subway station", tunnels=3,
                              noises=["rattle", "rumble", "echo"]),
}

PROBLEMS = {
    "stuck_season_sign": Problem(
        id="stuck_season_sign",
        label="the season sign was stuck",
        cause="a jammed lever",
        effect="the platform kept showing the wrong season",
        clue="the arrow would not move when the wind turned",
        messy="confusion",
    ),
    "mixed_parade_notice": Problem(
        id="mixed_parade_notice",
        label="the parade notice had been mixed up",
        cause="a splash of spilled ink",
        effect="the notices for the pagan parade and the train times had been crossed",
        clue="the letters had bled together like rain on paper",
        messy="confusion",
    ),
}

FIXES = {
    "chalk_map": Fix(
        id="chalk_map",
        label="a chalk map",
        method="draw a clear map on the platform tiles",
        rhymed_line="If the signs won't speak, let the chalk marks sing; one tidy line can fix the thing.",
        result="the right platform became easy to read again",
    ),
    "banner_reset": Fix(
        id="banner_reset",
        label="a bright banner",
        method="hang a bright banner over the old notice board",
        rhymed_line="If the board is blurred and the words go dim, hang a bright banner right on its rim.",
        result="the notices looked plain and true again",
    ),
}

GIRL_NAMES = ["Mina", "Lila", "Nora", "Zuri", "Ivy", "Ruth"]
BOY_NAMES = ["Eli", "Theo", "Noah", "Bram", "Otto", "Finn"]
HELPERS = ["station master", "ticket clerk", "conductor", "porter"]


# ---------------------------------------------------------------------------
# Utility
# ---------------------------------------------------------------------------

def _meter(e: Entity, key: str, amount: float = 0.0) -> float:
    e.meters[key] = e.meters.get(key, 0.0) + amount
    return e.meters[key]


def _meme(e: Entity, key: str, amount: float = 0.0) -> float:
    e.memes[key] = e.memes.get(key, 0.0) + amount
    return e.memes[key]


def title_case_word(s: str) -> str:
    return s[:1].upper() + s[1:]


def clean_join(parts: list[str]) -> str:
    s = " ".join(p.strip() for p in parts if p and p.strip())
    s = re.sub(r"\s+", " ", s)
    s = re.sub(r"\s+([,.;!?])", r"\1", s)
    return s.strip()


# ---------------------------------------------------------------------------
# World actions
# ---------------------------------------------------------------------------

def set_up_world(params: StoryParams) -> World:
    world = World(SETTINGS["subway_station"])
    hero = world.add(Entity(
        id=params.name, kind="character", type=params.gender,
        traits=["small", "bright-eyed", "curious"],
    ))
    helper = world.add(Entity(
        id="helper", kind="character", type=params.helper, label=f"the {params.helper}",
        traits=["steady", "kind"],
    ))
    problem = PROBLEMS[params.problem]
    fix = FIXES[params.fix]
    season = world.add(Entity(
        id="season_sign", type="thing", label="season sign",
        phrase=f"a big brass sign with {params.season} painted in gold letters",
    ))
    notice = world.add(Entity(
        id="notice", type="thing", label="pagan parade notice",
        phrase="a parade notice for the pagan lantern walk",
    ))

    world.facts.update(hero=hero, helper=helper, problem=problem, fix=fix,
                       season_entity=season, notice=notice)
    return world


def intro(world: World) -> None:
    hero: Entity = world.facts["hero"]
    season = world.facts["season_entity"]
    world.say(
        f"{hero.id} was a little {hero.type} with quick feet and a bigger curiosity, "
        f"and one fine day {hero.pronoun('subject')} came down into {world.setting.place}."
    )
    world.say(
        f"Up above the ticket gate stood {season.phrase}, shining like a penny in a kettle, "
        f"and the whole station smelled of coffee, iron, and far-off rain."
    )


def problem_begins(world: World) -> None:
    hero: Entity = world.facts["hero"]
    problem: Problem = world.facts["problem"]
    helper: Entity = world.facts["helper"]

    _meme(hero, "curiosity", 1)
    _meter(hero, "brightness", 1)

    world.para()
    world.say(
        f"Then {problem.label}; {problem.effect}, and even the echo had a puzzled face."
    )
    world.say(
        f"{helper.label.capitalize()} frowned and said the station would have to cease the mix-up before the next train."
    )
    _meme(helper, "worry", 1)
    _meter(helper, "confusion", 1)


def observe_clue(world: World) -> None:
    hero: Entity = world.facts["hero"]
    problem: Problem = world.facts["problem"]
    world.say(
        f"{hero.id} did not fret. {hero.pronoun('subject').capitalize()} leaned in close, spotted that {problem.clue}, "
        f"and tapped a finger like a tiny detective with a trumpet-bright hunch."
    )
    _meme(hero, "courage", 1)
    _meter(hero, "attention", 1)


def solve_problem(world: World) -> None:
    hero: Entity = world.facts["hero"]
    helper: Entity = world.facts["helper"]
    problem: Problem = world.facts["problem"]
    fix: Fix = world.facts["fix"]
    season = world.facts["season_entity"]
    notice = world.facts["notice"]

    # Physical state changes
    _meter(season, "order", 1)
    _meter(notice, "order", 1)
    _meter(hero, "helped", 1)
    _meter(helper, "helped", 1)
    _meme(hero, "delight", 1)
    _meme(helper, "relief", 1)

    world.para()
    world.say(
        f"{hero.id} and {helper.label} made a plan. They chose {fix.label} and went to work "
        f"with the steady patience of ants hauling sugar."
    )
    world.say(
        f"{fix.method.capitalize()}, {hero.id} said, and {fix.rhymed_line}"
    )
    world.say(
        f"They followed the rhyme, straightened the signs, and fixed {problem.label} so neatly "
        f"that the station looked newly ironed."
    )


def resolution(world: World) -> None:
    hero: Entity = world.facts["hero"]
    helper: Entity = world.facts["helper"]
    problem: Problem = world.facts["problem"]
    fix: Fix = world.facts["fix"]
    season = world.facts["season_entity"]

    _meter(hero, "resolve", 1)
    _meter(helper, "resolve", 1)
    _meter(season, "order", 1)
    _meme(hero, "relief", 1)
    _meme(helper, "delight", 1)

    world.para()
    world.say(
        f"By the time the next train yawned into the platform, the whole station could read the season at a glance."
    )
    world.say(
        f"The pagan lantern walk had its own clear notice, the commuters had their clear path, and the old confusion had to cease."
    )
    world.say(
        f"{hero.id} smiled at the bright sign and went home with {helper.label}, proud as a fox in a fiddle shop."
    )


# ---------------------------------------------------------------------------
# Generation
# ---------------------------------------------------------------------------

def tell_story(params: StoryParams) -> World:
    world = set_up_world(params)
    intro(world)
    problem_begins(world)
    observe_clue(world)
    solve_problem(world)
    resolution(world)
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero: Entity = f["hero"]
    problem: Problem = f["problem"]
    fix: Fix = f["fix"]
    return [
        f"Write a tall tale about {hero.id} in a subway station where a season sign causes trouble and someone must cease the confusion.",
        f"Tell a child-friendly problem-solving story that includes the words season, pagan, and cease, and ends with a rhyme.",
        f"Write a short subway-station adventure where {problem.label} gets fixed by {fix.label}.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero: Entity = f["hero"]
    helper: Entity = f["helper"]
    problem: Problem = f["problem"]
    fix: Fix = f["fix"]
    season: Entity = f["season_entity"]

    return [
        QAItem(
            question=f"Where did {hero.id} find the problem?",
            answer=f"{hero.id} found it in the subway station, beside the brass season sign and the busy platform.",
        ),
        QAItem(
            question=f"What was wrong with the season sign?",
            answer=f"{problem.label}; {problem.effect}.",
        ),
        QAItem(
            question=f"Who helped {hero.id} solve the problem?",
            answer=f"{helper.label} helped {hero.id} by planning carefully and keeping the station calm.",
        ),
        QAItem(
            question=f"What did they use to fix things?",
            answer=f"They used {fix.label} and a clever plan, then followed the rhyme to set the signs right.",
        ),
        QAItem(
            question=f"What changed at the end of the story?",
            answer=f"The wrong messages stopped, the station became clear again, and the confusion had to cease.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a subway station?",
            answer="A subway station is a place where people wait for underground trains and look for the right platform.",
        ),
        QAItem(
            question="What is a season?",
            answer="A season is one part of the year, like spring, summer, autumn, or winter.",
        ),
        QAItem(
            question="What does cease mean?",
            answer="Cease means to stop or come to an end.",
        ),
        QAItem(
            question="What is a rhyme?",
            answer="A rhyme is a pair of words or lines that sound alike at the end, which can make a saying easy to remember.",
        ),
        QAItem(
            question="What is a pagan lantern walk?",
            answer="In this story, it is a festival parade with lanterns and notices, treated as a community event at the station.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    out = ["== Prompts ==", *[f"- {p}" for p in sample.prompts], "", "== Story Q&A =="]
    for q in sample.story_qa:
        out.append(f"Q: {q.question}")
        out.append(f"A: {q.answer}")
    out.append("")
    out.append("== World Q&A ==")
    for q in sample.world_qa:
        out.append(f"Q: {q.question}")
        out.append(f"A: {q.answer}")
    return "\n".join(out)


# ---------------------------------------------------------------------------
# Reasonableness / parameter resolution
# ---------------------------------------------------------------------------

def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for place in SETTINGS:
        for problem in PROBLEMS:
            for fix in FIXES:
                combos.append((place, problem, fix))
    return combos


def explain_rejection() -> str:
    return "(No story: that combination does not make a believable subway-station problem to solve.)"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Tall-tale subway station problem-solving storyworld.")
    ap.add_argument("--season", choices=SEASONS)
    ap.add_argument("--problem", choices=PROBLEMS)
    ap.add_argument("--fix", choices=FIXES)
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--helper", choices=HELPERS)
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
    season = args.season or rng.choice(SEASONS)
    problem = args.problem or rng.choice(list(PROBLEMS))
    fix = args.fix or rng.choice(list(FIXES))

    if args.gender and not args.name:
        name = rng.choice(GIRL_NAMES if args.gender == "girl" else BOY_NAMES)
    else:
        name = args.name or rng.choice(GIRL_NAMES + BOY_NAMES)
    gender = args.gender or ("girl" if name in GIRL_NAMES else "boy")
    helper = args.helper or rng.choice(HELPERS)

    return StoryParams(
        season=season, problem=problem, fix=fix, name=name, gender=gender, helper=helper
    )


def generate(params: StoryParams) -> StorySample:
    world = tell_story(params)
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


# ---------------------------------------------------------------------------
# Trace
# ---------------------------------------------------------------------------

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
        lines.append(f"  {e.id}: {e.type} {' '.join(bits)}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------

ASP_RULES = r"""
season(S) :- season_fact(S).
problem(P) :- problem_fact(P).
fix(F) :- fix_fact(F).

valid_story(S, P, F) :- season(S), problem(P), fix(F).
"""

def asp_facts() -> str:
    import storyworlds.asp as asp
    lines = []
    for s in SEASONS:
        lines.append(asp.fact("season_fact", s))
    for p in PROBLEMS:
        lines.append(asp.fact("problem_fact", p))
    for f in FIXES:
        lines.append(asp.fact("fix_fact", f))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import storyworlds.asp as asp
    model = asp.one_model(asp_program("#show valid_story/3."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    py = set(valid_combos())
    asp_set = set(asp_valid_combos())
    if py == asp_set:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    if py - asp_set:
        print("  only in python:", sorted(py - asp_set))
    if asp_set - py:
        print("  only in clingo:", sorted(asp_set - py))
    return 1


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

CURATED = [
    StoryParams(season="spring", problem="stuck_season_sign", fix="chalk_map", name="Mina", gender="girl", helper="station master"),
    StoryParams(season="winter", problem="mixed_parade_notice", fix="banner_reset", name="Eli", gender="boy", helper="ticket clerk"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid_story/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible stories:")
        for item in combos:
            print(" ", item)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 20):
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            sample = generate(params)
            if sample.story in seen:
                i += 1
                continue
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

#!/usr/bin/env python3
"""
A small nursery-rhyme storyworld about a child, a missing thing, and a careful
monthly plan.

Premise:
- A little character loves a monthly ritual.
- The ritual depends on a specific object, place, or helper.
- Something goes missing or becomes hard to use.

Turn:
- Suspense grows as the hero searches, worries, or waits.
- The world state tracks clues, time passing, and emotional tension.

Resolution:
- The hero solves the problem with a gentle, concrete action.
- The ending image proves the missing thing is found, fixed, or put to use.

This world deliberately keeps the prose simple, rhythmic, and child-facing,
with a nursery-rhyme feel rather than event-log narration.
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

MONTHS = [
    "January", "February", "March", "April", "May", "June",
    "July", "August", "September", "October", "November", "December",
]

# ---------------------------------------------------------------------------
# World model
# ---------------------------------------------------------------------------
@dataclass
class Entity:
    id: str
    kind: str = "thing"
    label: str = ""
    type: str = ""
    plural: bool = False
    owner: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "mother", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class World:
    month: str
    setting: str
    entities: dict[str, Entity] = field(default_factory=dict)
    facts: dict = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])

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
        clone = World(month=self.month, setting=self.setting)
        clone.entities = {
            k: Entity(
                id=v.id, kind=v.kind, label=v.label, type=v.type, plural=v.plural,
                owner=v.owner, meters=dict(v.meters), memes=dict(v.memes)
            )
            for k, v in self.entities.items()
        }
        clone.facts = dict(self.facts)
        clone.paragraphs = [[]]
        return clone


THRESHOLD = 1.0

# ---------------------------------------------------------------------------
# Story ingredients
# ---------------------------------------------------------------------------
@dataclass
class Setting:
    place: str
    sound: str
    clue_place: str


@dataclass
class Problem:
    id: str
    thing: str
    missing_from: str
    worry: str
    search: str
    fix: str
    rhyme: str
    clue: str
    solve_place: str


@dataclass
class StoryParams:
    month: str
    setting: str
    problem: str
    name: str
    gender: str
    helper: str
    seed: Optional[int] = None


SETTINGS = {
    "garden": Setting(place="the garden gate", sound="the leaves went rustle", clue_place="the flower pot"),
    "attic": Setting(place="the little attic", sound="the boards went creak", clue_place="the old trunk"),
    "kitchen": Setting(place="the warm kitchen", sound="the spoon went clink", clue_place="the sugar jar"),
    "porch": Setting(place="the front porch", sound="the boards went tap", clue_place="the rain boot tray"),
}

PROBLEMS = {
    "lantern": Problem(
        id="lantern",
        thing="little lantern",
        missing_from="the shelf",
        worry="the moonlight looked too dim",
        search="peek in the corners",
        fix="shine it again with a fresh little candle",
        rhyme="glow",
        clue="a tiny gleam",
        solve_place="the old trunk",
    ),
    "scarf": Problem(
        id="scarf",
        thing="striped scarf",
        missing_from="the peg",
        worry="the evening wind felt nippy",
        search="look behind the chairs",
        fix="wrap it snug and warm around the neck",
        rhyme="flow",
        clue="a soft stripe",
        solve_place="the chair back",
    ),
    "teacup": Problem(
        id="teacup",
        thing="teacup",
        missing_from="the tray",
        worry="tea time could not begin",
        search="tiptoe and look near the sink",
        fix="wash it and set it dry on a towel",
        rhyme="tea",
        clue="a small ring",
        solve_place="the sink basin",
    ),
    "kite": Problem(
        id="kite",
        thing="paper kite",
        missing_from="the hook",
        worry="the windy day was waiting",
        search="race to the fence and back",
        fix="tie a bright new string and let it climb",
        rhyme="sky",
        clue="a ribbon tail",
        solve_place="the porch bench",
    ),
}

HEROES = {
    "girl": ["Mina", "Nora", "Lily", "Pippa"],
    "boy": ["Ben", "Theo", "Robin", "Milo"],
}
HELPERS = {
    "mother": "mother",
    "father": "father",
    "grandma": "grandma",
    "grandpa": "grandpa",
}

# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
month(M) :- month_name(M).
problem(P) :- problem_name(P).
setting(S) :- setting_name(S).

needs_search(P) :- worry(P,_).
can_solve(P) :- clue(P,_), fix(P,_).

valid_story(M,S,P) :- month(M), setting(S), problem(P), needs_search(P), can_solve(P).
"""

def asp_facts() -> str:
    import storyworlds.asp as asp
    lines: list[str] = []
    for m in MONTHS:
        lines.append(asp.fact("month_name", m))
    for sid in SETTINGS:
        lines.append(asp.fact("setting_name", sid))
    for pid, p in PROBLEMS.items():
        lines.append(asp.fact("problem_name", pid))
        lines.append(asp.fact("worry", pid, p.worry))
        lines.append(asp.fact("clue", pid, p.clue))
        lines.append(asp.fact("fix", pid, p.fix))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_stories() -> list[tuple]:
    import storyworlds.asp as asp
    model = asp.one_model(asp_program("#show valid_story/3."))
    return sorted(set(asp.atoms(model, "valid_story")))


# ---------------------------------------------------------------------------
# Simulation helpers
# ---------------------------------------------------------------------------
def month_detail(month: str) -> str:
    return {
        "January": "the year was newborn and bright",
        "February": "the air was short and keen",
        "March": "the wind could skip and sing",
        "April": "raindrops danced on every sill",
        "May": "the flowers could not help but bloom",
        "June": "the days were long and honey-warm",
        "July": "the sunshine glowed and hummed",
        "August": "the garden was full of buzzing gold",
        "September": "the apples were ripe and round",
        "October": "the leaves went twirl and tumble",
        "November": "the nights grew deep and still",
        "December": "the windows shone with frosty light",
    }[month]


def predict_fix(world: World, problem: Problem) -> bool:
    sim = world.copy()
    missing = sim.get("missing")
    return bool(missing and missing.memes.get("found", 0.0) >= THRESHOLD)


def tell(world: World, hero: Entity, helper: Entity, problem: Problem) -> World:
    world.say(
        f"In {world.month}, {month_detail(world.month)}, and {world.setting} was quiet as a shell."
    )
    world.say(
        f"There lived little {hero.id}, who loved a soft monthly ritual with {hero.pronoun('possessive')} {problem.thing}."
    )
    world.say(
        f"Each month {hero.id} liked to {problem.rhyme}, but on this day the {problem.thing} was gone from {problem.missing_from}."
    )

    missing = world.add(Entity(id="missing", kind="thing", label=problem.thing, type=problem.thing))
    missing.memes["lost"] = 1.0

    world.para()
    world.say(
        f"{hero.id} looked here and there. {helper.id} came near and listened. "
        f"\"Hush now,\" {helper.id} said, \"let us {problem.search}.\""
    )
    world.say(
        f"But the room felt hushed and unsure, for {problem.worry}, and {hero.id} had to wait and wonder."
    )

    # Suspense: clue found in a likely place.
    world.para()
    world.say(
        f"Then {hero.id} saw {problem.clue} by {problem.solve_place}, small as a button and bright as dew."
    )
    missing.memes["found"] = 1.0
    world.say(
        f"{hero.id} followed the clue, slow and careful, and found the {problem.thing} tucked at {problem.solve_place}."
    )

    # Solve.
    world.para()
    if problem.id == "lantern":
        world.say(
            f"With a fresh little candle, {helper.id} helped {hero.id} {problem.fix}, and the room went gold-glow, glow."
        )
    elif problem.id == "scarf":
        world.say(
            f"{helper.id} helped {hero.id} {problem.fix}, and the scarf went warm and cozy once more."
        )
    elif problem.id == "teacup":
        world.say(
            f"{helper.id} helped {hero.id} {problem.fix}, and soon tea time could begin with a tiny happy sip."
        )
    else:
        world.say(
            f"{helper.id} helped {hero.id} {problem.fix}, and the kite rose high, high, high into the sky."
        )
    hero.memes["relief"] = 1.0
    hero.memes["joy"] = 1.0
    world.say(
        f"At the end, {hero.id} smiled, {problem.thing} was ready, and the little monthly ritual could begin."
    )

    world.facts.update(
        month=world.month,
        setting=world.setting,
        hero=hero,
        helper=helper,
        problem=problem,
        missing=missing,
    )
    return world


# ---------------------------------------------------------------------------
# Q&A
# ---------------------------------------------------------------------------
def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero: Entity = f["hero"]
    helper: Entity = f["helper"]
    problem: Problem = f["problem"]
    return [
        f'Write a short nursery-rhyme story for a child about {world.month} and a missing {problem.thing}.',
        f"Tell a suspenseful but gentle story where {hero.id} cannot find the {problem.thing} until {helper.id} helps solve the problem.",
        f'Create a simple rhyming story with the word "month" that ends with {problem.thing} being found.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero: Entity = f["hero"]
    helper: Entity = f["helper"]
    problem: Problem = f["problem"]
    return [
        QAItem(
            question=f"What was missing from {problem.missing_from} in the story?",
            answer=f"The {problem.thing} was missing, and that made {hero.id} worry for a little while.",
        ),
        QAItem(
            question=f"Who helped {hero.id} look for the missing {problem.thing}?",
            answer=f"{helper.id} helped by staying calm and suggesting a careful search.",
        ),
        QAItem(
            question=f"How did the problem get solved?",
            answer=f"{hero.id} followed a clue, found the {problem.thing}, and then {helper.id} helped fix it with a gentle, sensible step.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a month?",
            answer="A month is a part of the year. There are twelve months, and people use them to count time as the days go by.",
        ),
        QAItem(
            question="Why can a missing thing feel scary at first?",
            answer="A missing thing can feel scary because nobody knows where it went yet, so people worry until they search and find it.",
        ),
        QAItem(
            question="What helps with a problem when you cannot solve it alone?",
            answer="Calm searching, a helpful helper, and a clear clue can all help solve a problem.",
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
    lines.append("== (3) World knowledge ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = [f"--- trace: month={world.month} setting={world.setting} ---"]
    for e in world.entities.values():
        bits = []
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        lines.append(f"  {e.id}: {e.kind} {e.label or e.type} {' '.join(bits)}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Parameter resolution and generation
# ---------------------------------------------------------------------------
def valid_combos() -> list[tuple[str, str]]:
    out = []
    for month in MONTHS:
        for setting in SETTINGS:
            for problem in PROBLEMS:
                out.append((month, setting, problem))
    return out


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    month = args.month or rng.choice(MONTHS)
    setting = args.setting or rng.choice(list(SETTINGS))
    problem = args.problem or rng.choice(list(PROBLEMS))
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(HEROES[gender])
    helper = args.helper or rng.choice(list(HELPERS))
    return StoryParams(
        month=month,
        setting=setting,
        problem=problem,
        name=name,
        gender=gender,
        helper=helper,
    )


def generate(params: StoryParams) -> StorySample:
    world = World(month=params.month, setting=params.setting)
    hero = world.add(Entity(id=params.name, kind="character", type=params.gender, label=params.name))
    helper = world.add(Entity(id=HELPERS[params.helper], kind="character", type=params.helper, label=HELPERS[params.helper]))
    problem = PROBLEMS[params.problem]
    tell(world, hero, helper, problem)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
CURATED = [
    StoryParams(month="October", setting="garden", problem="lantern", name="Mina", gender="girl", helper="grandma"),
    StoryParams(month="December", setting="porch", problem="scarf", name="Theo", gender="boy", helper="mother"),
    StoryParams(month="April", setting="kitchen", problem="teacup", name="Lily", gender="girl", helper="father"),
    StoryParams(month="July", setting="attic", problem="kite", name="Milo", gender="boy", helper="grandpa"),
]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Nursery-rhyme storyworld about months, suspense, and problem solving.")
    ap.add_argument("--month", choices=MONTHS)
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--problem", choices=PROBLEMS)
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--helper", choices=list(HELPERS))
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


def asp_verify() -> int:
    import storyworlds.asp as asp
    py = set(valid_combos())
    model = asp.one_model(asp_program("#show valid_story/3."))
    cl = set(asp.atoms(model, "valid_story"))
    if py == cl:
        print(f"OK: ASP matches Python ({len(py)} combos).")
        return 0
    print("Mismatch between ASP and Python.")
    print("only python:", sorted(py - cl))
    print("only asp:", sorted(cl - py))
    return 1


def asp_valid_combos() -> list[tuple]:
    import storyworlds.asp as asp
    model = asp.one_model(asp_program("#show valid_story/3."))
    return sorted(set(asp.atoms(model, "valid_story")))


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
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible stories:\n")
        for m, s, p in combos[:200]:
            print(f"  {m:9} {s:8} {p:8}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 20, 20):
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            sample = generate(params)
            i += 1
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
            header = f"### {p.name}: {p.month}, {p.setting}, {p.problem}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()

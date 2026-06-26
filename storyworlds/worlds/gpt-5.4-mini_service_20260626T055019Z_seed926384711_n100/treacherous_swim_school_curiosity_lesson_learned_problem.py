#!/usr/bin/env python3
"""
treacherous_swim_school_curiosity_lesson_learned_problem.py
===========================================================

A compact storyworld for a swim-school tale about curiosity, a scary water
problem, and a gentle lesson learned through problem solving.

Premise:
- A child at swim school is curious about something in the deep lane.
- The child wants to explore it, but the water setup is treacherous for a small
  swimmer.
- A teacher notices the risk and helps the child solve the problem safely.
- The child learns that curiosity is good when it is paired with patience,
  asking for help, and the right gear.

This world is designed to produce heartwarming, child-facing stories with:
- a clear beginning
- a state-driven worry in the middle
- a helpful turn
- a clean ending image that proves what changed
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


# ---------------------------------------------------------------------------
# Small world model
# ---------------------------------------------------------------------------

THRESHOLD = 1.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"  # character | thing
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
        female = {"girl", "mother", "mom", "woman", "teacher"}
        male = {"boy", "father", "dad", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Place:
    id: str
    label: str
    indoor: bool = True
    affords: set[str] = field(default_factory=set)


@dataclass
class Activity:
    id: str
    verb: str
    gerund: str
    rush: str
    risk: str
    problem: str
    lesson: str
    zone: set[str]
    keyword: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Gear:
    id: str
    label: str
    prep: str
    tail: str
    protects: set[str]
    supports: set[str]
    plural: bool = False


@dataclass
class StoryParams:
    place: str
    activity: str
    gear: str
    name: str
    gender: str
    guide: str
    trait: str
    seed: Optional[int] = None


class World:
    def __init__(self, place: Place) -> None:
        self.place = place
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
        import copy
        w = World(self.place)
        w.entities = copy.deepcopy(self.entities)
        w.fired = set(self.fired)
        w.paragraphs = [[]]
        w.facts = dict(self.facts)
        return w


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------

PLACES = {
    "swim_school": Place(
        id="swim_school",
        label="the swim school",
        indoor=True,
        affords={"lane", "deep_end", "kickboard"},
    )
}

ACTIVITIES = {
    "treacherous_swim": Activity(
        id="treacherous_swim",
        verb="swim toward the deep lane",
        gerund="swimming in the deep lane",
        rush="dash toward the deep water",
        risk="the deep lane looked treacherous for a small swimmer",
        problem="the child could not reach the shiny dive ring safely",
        lesson="curiosity is best when it listens to safety",
        zone={"deep_end"},
        keyword="treacherous",
        tags={"treacherous", "curiosity", "lesson", "problem_solving"},
    ),
    "kickboard_game": Activity(
        id="kickboard_game",
        verb="practice with a kickboard",
        gerund="kicking with a bright kickboard",
        rush="grab the kickboard and kick fast",
        risk="the lane was still deep, but the kickboard made it safer",
        problem="the child wanted to get the floating star toy",
        lesson="good tools make hard jobs feel kinder",
        zone={"lane"},
        keyword="curiosity",
        tags={"curiosity", "problem_solving"},
    ),
}

GEAR = {
    "kickboard": Gear(
        id="kickboard",
        label="a bright kickboard",
        prep="hold a kickboard and stay with the teacher",
        tail="swam back and forth with the kickboard",
        protects={"lane", "deep_end"},
        supports={"problem_solving"},
    ),
    "pool_ring": Gear(
        id="pool_ring",
        label="a float ring",
        prep="use a float ring and keep one hand on the wall",
        tail="practiced with the float ring beside the lane",
        protects={"deep_end"},
        supports={"problem_solving"},
    ),
}

NAMES = ["Mia", "Noah", "Lena", "Eli", "Ava", "Sam", "Nina", "Theo"]
GENDERS = ["girl", "boy"]
TRAITS = ["curious", "gentle", "brave", "patient", "kind"]


# ---------------------------------------------------------------------------
# Story logic
# ---------------------------------------------------------------------------

def valid_combo(place_id: str, activity_id: str, gear_id: str) -> bool:
    if place_id not in PLACES or activity_id not in ACTIVITIES or gear_id not in GEAR:
        return False
    act = ACTIVITIES[activity_id]
    gear = GEAR[gear_id]
    return bool(act.zone & gear.protects) and "problem_solving" in act.tags and "problem_solving" in gear.supports


def valid_combos() -> list[tuple[str, str, str]]:
    out = []
    for p in PLACES:
        for a in ACTIVITIES:
            for g in GEAR:
                if valid_combo(p, a, g):
                    out.append((p, a, g))
    return out


def choose_guide(gender: str) -> str:
    return "teacher"


def setup_story(world: World, hero: Entity, guide: Entity, activity: Activity, gear: Gear) -> None:
    world.say(
        f"{hero.id} was a {hero.pronoun('subject').capitalize()}? No—{hero.id} was a little {hero.type} who loved {activity.keyword} ideas and noticed every shiny thing at {world.place.label}."
    )
    world.say(
        f"At swim school, {hero.id} liked {activity.gerund}, and {activity.risk}."
    )
    world.say(
        f"One day, {hero.id} saw {activity.problem}."
    )


def predict_problem(world: World, hero: Entity, activity: Activity) -> bool:
    sim = world.copy()
    sim.get(hero.id).memes["curiosity"] = 1.0
    return True


def solve_problem(world: World, hero: Entity, guide: Entity, activity: Activity, gear: Gear) -> None:
    hero.memes["curiosity"] += 1
    world.say(
        f"{hero.id} wanted to {activity.verb}, but {activity.risk}."
    )
    world.say(
        f"{guide.id} smiled and said, \"Let's solve this together.\""
    )
    world.say(
        f"They chose {gear.label}, because it could help {hero.id} stay safe in the water."
    )
    world.say(
        f"{hero.id} listened, and {hero.id} learned that asking for help can make curiosity feel brave instead of scary."
    )
    world.say(
        f"With {gear.label}, {hero.id} could {gear.tail}, and the shiny target stayed near the wall where it was safe to reach."
    )
    hero.memes["lesson_learned"] += 1
    hero.memes["pride"] += 1
    world.facts["resolved"] = True


def tell(place: Place, activity: Activity, gear: Gear, hero_name: str, gender: str, trait: str) -> World:
    world = World(place)

    hero = world.add(Entity(
        id=hero_name,
        kind="character",
        type=gender,
        meters={"tired": 0.0},
        memes={"curiosity": 0.0, "lesson_learned": 0.0, "pride": 0.0},
    ))
    guide = world.add(Entity(
        id="Teacher",
        kind="character",
        type="teacher",
        label="the teacher",
        meters={"calm": 1.0},
        memes={"care": 1.0},
    ))

    world.facts.update(
        hero=hero,
        guide=guide,
        activity=activity,
        gear=gear,
        trait=trait,
        place=place,
    )

    world.say(
        f"At {place.label}, {hero.id} was a {trait} little {gender} who came to swim school with a big curious heart."
    )
    world.say(
        f"{hero.id} noticed something glittering near the deep lane and leaned forward to look."
    )

    world.para()
    world.say(f"{activity.risk}.")
    world.say(f"{activity.problem}.")

    world.para()
    solve_problem(world, hero, guide, activity, gear)

    world.para()
    world.say(
        f"At the end, {hero.id} smiled beside {guide.pronoun('object')} and swam safely in the shallow lane, carrying the lesson home in a happy heart."
    )

    return world


# ---------------------------------------------------------------------------
# QA
# ---------------------------------------------------------------------------

def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    activity = f["activity"]
    return [
        f'Write a heartwarming story for a small child at {world.place.label} about {hero.id} and {activity.keyword}.',
        f"Tell a gentle story where {hero.id} feels curious at swim school, faces a treacherous water problem, and learns a safe lesson.",
        f"Write a child-friendly story about problem solving in the pool, with a caring teacher and a brave child named {hero.id}.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero: Entity = f["hero"]
    guide: Entity = f["guide"]
    activity: Activity = f["activity"]
    gear: Gear = f["gear"]
    trait = f["trait"]
    return [
        QAItem(
            question=f"Who was the story about at the swim school?",
            answer=f"It was about {hero.id}, a {trait} little {hero.type}, and {guide.label}.",
        ),
        QAItem(
            question=f"What made the pool feel treacherous for {hero.id}?",
            answer=f"The deep lane looked treacherous, and {activity.problem} made the problem feel bigger.",
        ),
        QAItem(
            question=f"How did {hero.id} solve the problem?",
            answer=f"{hero.id} listened to {guide.label}, used {gear.label}, and stayed safe while practicing.",
        ),
        QAItem(
            question=f"What lesson did {hero.id} learn?",
            answer=f"{hero.id} learned that curiosity is best when it listens to safety and asks for help.",
        ),
    ]


WORLD_KNOWLEDGE = {
    "treacherous": [
        (
            "What does treacherous mean?",
            "Treacherous means something is dangerous and not safe to trust without care.",
        )
    ],
    "curiosity": [
        (
            "What is curiosity?",
            "Curiosity is the feeling that makes someone want to look, ask, and learn more.",
        )
    ],
    "lesson": [
        (
            "What is a lesson learned?",
            "A lesson learned is a helpful idea that someone remembers after an experience.",
        )
    ],
    "problem_solving": [
        (
            "What is problem solving?",
            "Problem solving means finding a smart way to fix a difficulty step by step.",
        )
    ],
}


def world_knowledge_qa(world: World) -> list[QAItem]:
    tags = set(world.facts["activity"].tags)
    out: list[QAItem] = []
    for tag, items in WORLD_KNOWLEDGE.items():
        if tag in tags:
            out.extend(QAItem(question=q, answer=a) for q, a in items)
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
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        lines.append(f"  {e.id:8} ({e.type:9}) {' '.join(bits)}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------

ASP_RULES = r"""
place(swim_school).
activity(treacherous_swim).
activity(kickboard_game).
gear(kickboard).
gear(pool_ring).

curious(A) :- activity(A), activity_tag(A, curiosity).
problem_solving(A) :- activity(A), activity_tag(A, problem_solving).

treacherous(A) :- activity(A), activity_tag(A, treacherous).
needs_help(A) :- treacherous(A), curious(A).

safe_fix(A, G) :- activity(A), gear(G), protects(G, deep_end), supports(G, problem_solving).
safe_story(P, A, G) :- place(P), activity(A), gear(G), needs_help(A), safe_fix(A, G).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid, p in PLACES.items():
        lines.append(asp.fact("place", pid))
        if p.indoor:
            lines.append(asp.fact("indoor", pid))
        for a in sorted(p.affords):
            lines.append(asp.fact("affords", pid, a))
    for aid, a in ACTIVITIES.items():
        lines.append(asp.fact("activity", aid))
        for t in sorted(a.tags):
            lines.append(asp.fact("activity_tag", aid, t))
        for z in sorted(a.zone):
            lines.append(asp.fact("splashes", aid, z))
    for gid, g in GEAR.items():
        lines.append(asp.fact("gear", gid))
        for p in sorted(g.protects):
            lines.append(asp.fact("protects", gid, p))
        for s in sorted(g.supports):
            lines.append(asp.fact("supports", gid, s))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show safe_story/3."))
    return sorted(set(asp.atoms(model, "safe_story")))


def asp_verify() -> int:
    import asp
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    if py - cl:
        print("  only in python:", sorted(py - cl))
    if cl - py:
        print("  only in clingo:", sorted(cl - py))
    return 1


# ---------------------------------------------------------------------------
# Parameters / generation
# ---------------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A heartwarming swim-school storyworld about curiosity, lesson learned, and problem solving.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--activity", choices=ACTIVITIES)
    ap.add_argument("--gear", choices=GEAR)
    ap.add_argument("--gender", choices=GENDERS)
    ap.add_argument("--name")
    ap.add_argument("--guide", choices=["teacher"], default=None)
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
    if args.place:
        combos = [c for c in combos if c[0] == args.place]
    if args.activity:
        combos = [c for c in combos if c[1] == args.activity]
    if args.gear:
        combos = [c for c in combos if c[2] == args.gear]
    if not combos:
        raise StoryError("(No valid swim-school combination matches the given options.)")

    place, activity, gear = rng.choice(sorted(combos))
    gender = args.gender or rng.choice(GENDERS)
    name = args.name or rng.choice(NAMES)
    guide = args.guide or choose_guide(gender)
    trait = args.trait or rng.choice(TRAITS)

    return StoryParams(
        place=place,
        activity=activity,
        gear=gear,
        name=name,
        gender=gender,
        guide=guide,
        trait=trait,
    )


def generate(params: StoryParams) -> StorySample:
    world = tell(
        PLACES[params.place],
        ACTIVITIES[params.activity],
        GEAR[params.gear],
        params.name,
        params.gender,
        params.trait,
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
        print(asp_program("#show safe_story/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} safe story combos:\n")
        for place, activity, gear in combos:
            print(f"  {place:12} {activity:20} {gear}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)

    if args.all:
        samples = [generate(StoryParams(place=p, activity=a, gear=g, name="Mia", gender="girl", guide="teacher", trait="curious"))
                   for p, a, g in valid_combos()]
    else:
        samples = []
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 50, 50):
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
        header = ""
        if len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()

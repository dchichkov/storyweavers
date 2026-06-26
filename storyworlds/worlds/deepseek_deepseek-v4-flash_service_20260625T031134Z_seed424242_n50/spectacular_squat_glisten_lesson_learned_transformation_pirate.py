#!/usr/bin/env python3
"""
storyworlds/worlds/spectacular_squat_glisten_lesson_learned_transformation_pirate.py
==================================================================================

A standalone story world for a pirate transformation tale. A young pirate learns
that the most spectacular treasure isn't gold but the glisten of self-respect
earned through a humble squat of service.

Domain elements:
- Pirates, a ship, a quest, a challenge, a lesson learned, and a transformation
- Each story follows a young pirate who wants to prove themselves, faces a trial
  involving greed or pride, learns a lesson through a humble act (squat), and
  transforms into a better pirate.
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
from results import QAItem, StoryError, StorySample

THRESHOLD = 1.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "pirate"
    label: str = ""
    phrase: str = ""
    traits: list[str] = field(default_factory=list)
    owner: Optional[str] = None
    worn_by: Optional[str] = None
    region: str = ""
    protective: bool = False
    plural: bool = False
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        return {"subject": "they", "object": "them", "possessive": "their"}.get(case, "they")

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str = "the pirate ship"
    indoor: bool = True
    affords: set[str] = field(default_factory=lambda: {"dig", "climb", "sail"})


@dataclass
class Activity:
    id: str
    verb: str
    gerund: str
    rush: str
    mess: str
    zone: set[str]
    keyword: str = ""
    tags: set[str] = field(default_factory=set)


@dataclass
class Lesson:
    id: str
    label: str
    phrase: str
    truth: str


@dataclass
class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str) -> Entity:
        return self.entities[eid]

    def characters(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.kind == "character"]

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        chunks = [" ".join(p) for p in self.paragraphs if p]
        return "\n\n".join(chunks)

    def copy(self) -> "World":
        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        return clone


SETTINGS = {
    "ship": Setting(place="the pirate ship", indoor=True, affords={"dig", "climb", "sail"}),
    "island": Setting(place="the secret island", indoor=False, affords={"dig", "climb"}),
    "cove": Setting(place="the hidden cove", indoor=False, affords={"sail", "dig"}),
}

ACTIVITIES = {
    "dig": Activity(
        id="dig",
        verb="dig for treasure",
        gerund="digging for treasure",
        rush="grab the biggest shovel",
        mess="dirty",
        zone={"hands", "knees"},
        keyword="treasure",
        tags={"greed", "gold"},
    ),
    "climb": Activity(
        id="climb",
        verb="climb the tallest mast",
        gerund="climbing the mast",
        rush="scramble up the ropes",
        mess="scratched",
        zone={"hands", "knees"},
        keyword="mast",
        tags={"pride", "daring"},
    ),
    "sail": Activity(
        id="sail",
        verb="sail to the far reef",
        gerund="sailing the reef",
        rush="steer toward the sharp rocks",
        mess="tired",
        zone={"arms"},
        keyword="reef",
        tags={"bravery", "risk"},
    ),
}

LESSONS = [
    Lesson(id="greed", label="greed", phrase="the glisten of gold",
           truth="true treasure is in helping others"),
    Lesson(id="pride", label="pride", phrase="the spectacular climb",
           truth="humility is stronger than pride"),
    Lesson(id="anger", label="anger", phrase="the storm inside",
           truth="kindness calms the fiercest waves"),
]

PIRATE_NAMES = ["Redbeard", "Salty", "Coral", "Scout", "Gull", "Rigger", "Cappy", "Squall", "Rune", "Tide"]

TRAITS = ["greedy", "proud", "brave", "curious", "stubborn", "eager"]

GEAR = [
    {"id": "kindness", "label": "a kind word", "covers": set(), "guards": set(), "prep": "offer a kind word", "tail": "spoke with a gentle voice"},
    {"id": "helping", "label": "helping hands", "covers": set(), "guards": set(), "prep": "lend a hand to the crew", "tail": "worked together with the crew"},
]


def valid_combos() -> list[tuple]:
    combos = []
    for place, setting in SETTINGS.items():
        for act_id in setting.affords:
            for lesson in LESSONS:
                combos.append((place, act_id, lesson.id))
    return combos


@dataclass
class StoryParams:
    place: str
    activity: str
    lesson: str
    name: str
    trait: str
    seed: Optional[int] = None


def _enact_lesson(world: World, hero: Entity, lesson: Lesson) -> list[str]:
    out = []
    lesson_key = lesson.id
    if lesson_key == "greed":
        hero.memes["greed"] += 1
        hero.memes["conflict"] += 1
        out.append(f"{hero.id} felt the glisten of greed in their chest.")
    elif lesson_key == "pride":
        hero.memes["pride"] += 1
        hero.memes["conflict"] += 1
        out.append(f"{hero.id} felt a spectacular pride swelling up.")
    elif lesson_key == "anger":
        hero.memes["anger"] += 1
        hero.memes["conflict"] += 1
        out.append(f"{hero.id} felt a storm of anger inside.")
    return out


def _r_transform(world: World) -> list[str]:
    out = []
    for hero in world.characters():
        if hero.memes.get("conflict", 0) >= THRESHOLD and hero.memes.get("humble", 0) >= THRESHOLD:
            sig = ("transform", hero.id)
            if sig in world.fired:
                continue
            world.fired.add(sig)
            hero.memes["transformed"] = 1
            hero.memes["conflict"] = 0
            out.append(f"{hero.id} learned the lesson and transformed into a better pirate.")
    return out


CAUSAL_RULES = [
    {"apply": _r_transform, "tag": "social"},
]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            sents = rule["apply"](world)
            if sents:
                changed = True
                produced.extend(s for s in sents if s != "__conflict__")
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def introduce(world: World, hero: Entity) -> None:
    world.say(f"{hero.id} was a young pirate with a dream of finding something spectacular.")


def show_trait(world: World, hero: Entity, activity: Activity, lesson: Lesson) -> None:
    world.say(f"{hero.id} wanted to {activity.verb} and feel the {lesson.phrase}.")
    _enact_lesson(world, hero, lesson)


def challenge(world: World, hero: Entity, activity: Activity) -> None:
    world.say(f"On {world.setting.place}, the chance came. \"Now is the time to {activity.verb}!\" {hero.id} cheered.")


def struggle(world: World, hero: Entity, lesson: Lesson) -> None:
    world.say(f"But the {lesson.label} grew strong. {lesson.label} made {hero.id} forget the crew.")
    hero.memes["conflict"] += 1


def squat_of_service(world: World, hero: Entity) -> None:
    world.say(f"{hero.id} took a deep breath and did a humble squat, ready to help instead of take.")
    hero.memes["humble"] += 1
    propagate(world)


def transformation(world: World, hero: Entity, lesson: Lesson) -> None:
    if hero.memes.get("transformed", 0) >= THRESHOLD:
        world.say(f"The glisten of the lesson shone bright. {hero.id} was no longer just a pirate — {hero.id} was a friend.")
    else:
        world.say(f"{hero.id} still had work to do, but the path was clear.")


def tell(setting: Setting, activity: Activity, lesson: Lesson, name: str, trait: str) -> World:
    world = World(setting)
    hero = world.add(Entity(id=name, kind="character", type="pirate", traits=[trait, "young"]))
    capn = world.add(Entity(id="Captain", kind="character", type="captain", label="the captain"))
    crew = world.add(Entity(id="Crew", kind="character", type="crew", label="the crew"))

    introduce(world, hero)
    show_trait(world, hero, activity, lesson)
    world.para()
    challenge(world, hero, activity)
    struggle(world, hero, lesson)
    world.para()
    squat_of_service(world, hero)
    transformation(world, hero, lesson)

    world.facts.update(hero=hero, lesson=lesson, activity=activity, setting=setting)
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    lesson = f["lesson"]
    act = f["activity"]
    return [
        f"Write a story about {hero.id}, a young pirate who learns that {lesson.truth}.",
        f"A pirate tale about {act.gerund} and the lesson of {lesson.label}.",
        f"Tell how {hero.id} did a humble squat and found a spectacular glisten of wisdom.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    lesson = f["lesson"]
    act = f["activity"]
    qa = [
        QAItem(
            question=f"What did {hero.id} want to do at the start of the story?",
            answer=f"{hero.id} wanted to {act.verb} and find something spectacular.",
        ),
        QAItem(
            question=f"What lesson did {hero.id} learn?",
            answer=f"{hero.id} learned that {lesson.truth}. The {lesson.label} was not the answer.",
        ),
        QAItem(
            question=f"How did {hero.id} change by the end?",
            answer=f"{hero.id} did a humble squat, helped the crew, and transformed into a kinder pirate.",
        ),
    ]
    return qa


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(question="What does it mean to do a squat?",
               answer="A squat is when you bend your knees and lower your body, like getting ready to lift something or help someone."),
        QAItem(question="Why do pirates dig for treasure?",
               answer="Pirates dig for treasure to find gold and jewels, but the best treasure is learning to be a good friend."),
        QAItem(question="What is a lesson learned?",
               answer="A lesson learned is something you understand after an experience that makes you wiser."),
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
    for e in world.entities.values():
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        lines.append(f"  {e.id:12} ({e.type:8}) {' '.join(bits)}")
    return "\n".join(lines)


CURATED = [
    StoryParams(place="ship", activity="dig", lesson="greed", name="Redbeard", trait="greedy"),
    StoryParams(place="island", activity="climb", lesson="pride", name="Salty", trait="proud"),
    StoryParams(place="cove", activity="sail", lesson="anger", name="Coral", trait="stubborn"),
]


ASP_RULES = r"""
setting(ship). setting(island). setting(cove).
affords(ship, dig). affords(ship, climb). affords(ship, sail).
affords(island, dig). affords(island, climb).
affords(cove, sail). affords(cove, dig).

activity(dig). activity(climb). activity(sail).

lesson(greed). lesson(pride). lesson(anger).

valid(Place, A, L) :- setting(Place), affords(Place, A), activity(A), lesson(L).
"""


def asp_facts() -> str:
    lines = []
    for pid, s in SETTINGS.items():
        lines.append(f"setting({pid}).")
        for a in sorted(s.affords):
            lines.append(f"affords({pid},{a}).")
    for aid in ACTIVITIES:
        lines.append(f"activity({aid}).")
    for l in LESSONS:
        lines.append(f"lesson({l.id}).")
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    clingo_set = set(asp_valid_combos())
    python_set = set(valid_combos())
    if clingo_set == python_set:
        print(f"OK: clingo gate matches valid_combos() ({len(clingo_set)} combos).")
        return 0
    print("MISMATCH:")
    if clingo_set - python_set:
        print("  only in clingo:", sorted(clingo_set - python_set))
    if python_set - clingo_set:
        print("  only in python:", sorted(python_set - clingo_set))
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Pirate tale: spectacular squat, glisten, lesson learned, transformation.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--activity", choices=ACTIVITIES)
    ap.add_argument("--lesson", choices=[l.id for l in LESSONS])
    ap.add_argument("--name")
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
              if (args.place is None or c[0] == args.place)
              and (args.activity is None or c[1] == args.activity)
              and (args.lesson is None or c[2] == args.lesson)]
    if not combos:
        raise StoryError("No valid combination matches the given options.")
    place, activity, lesson = rng.choice(sorted(combos))
    name = args.name or rng.choice(PIRATE_NAMES)
    trait = rng.choice(TRAITS)
    return StoryParams(place=place, activity=activity, lesson=lesson, name=name, trait=trait)


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.place], ACTIVITIES[params.activity],
                 [l for l in LESSONS if l.id == params.lesson][0],
                 params.name, params.trait)
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
        print(asp_program("#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (place, activity, lesson) combos:")
        for c in combos:
            print(f"  {c[0]:9} {c[1]:8} {c[2]:8}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)

    samples = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 50, 50):
            seed = base_seed + i
            i += 1
            try:
                params = resolve_params(args, random.Random(seed))
            except StoryError as err:
                print(err)
                return
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
        if args.all:
            p = sample.params
            header = f"### {p.name}: {p.activity} at {p.place} (lesson: {p.lesson})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()

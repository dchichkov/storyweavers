#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260626T060043Z_seed274930118_n5000/curb_swim_school_rhyme_fable.py
==============================================================================================================

A small storyworld set at swim school, with a curb, rhyme, and a fable-like
turn: a hesitant child learns a lesson, then finds courage through a helper and
a simple sing-song routine.
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
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        mapping = {
            "girl": {"subject": "she", "object": "her", "possessive": "her"},
            "boy": {"subject": "he", "object": "him", "possessive": "his"},
        }
        return mapping.get(self.type, {"subject": "it", "object": "it", "possessive": "its"})[case]


@dataclass
class SwimSchool:
    place: str = "swim school"
    curb: str = "the curb by the pool"
    poolside: str = "the pool deck"
    affords: set[str] = field(default_factory=lambda: {"rim", "kick", "float"})


@dataclass
class Lesson:
    id: str
    verb: str
    gerund: str
    risk: str
    consequence: str
    rhythm: str
    keyword: str = "curb"
    tags: set[str] = field(default_factory=set)


@dataclass
class Aid:
    id: str
    label: str
    action: str
    rhyme: str
    supports: set[str]


@dataclass
class StoryParams:
    lesson: str
    name: str
    gender: str
    coach: str
    seed: Optional[int] = None


class World:
    def __init__(self, school: SwimSchool) -> None:
        self.school = school
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

    def copy(self) -> "World":
        import copy
        w = World(self.school)
        w.entities = copy.deepcopy(self.entities)
        w.facts = dict(self.facts)
        w.fired = set(self.fired)
        w.paragraphs = [[]]
        return w


SWIM_SCHOOL = SwimSchool()

LESSONS = {
    "rim": Lesson(
        id="rim",
        verb="step near the curb",
        gerund="stepping by the curb",
        risk="wobble",
        consequence="slip into a fuss",
        rhythm="step, tap, stop",
        keyword="curb",
        tags={"curb", "balance"},
    ),
    "kick": Lesson(
        id="kick",
        verb="kick beside the lane",
        gerund="kicking in time",
        risk="spray",
        consequence="splash the lesson board",
        rhythm="kick, kick, grin",
        keyword="curb",
        tags={"water", "rhythm"},
    ),
    "float": Lesson(
        id="float",
        verb="try a float",
        gerund="floating slowly",
        risk="fret",
        consequence="sink into doubt",
        rhythm="float, breathe, trust",
        keyword="curb",
        tags={"water", "calm"},
    ),
}

AIDS = {
    "chant": Aid(
        id="chant",
        label="a tiny chant",
        action="sing the steps",
        rhyme="rim and swim, bright and dim",
        supports={"wobble", "fret"},
    ),
    "board": Aid(
        id="board",
        label="a kick board",
        action="hold on and try again",
        rhyme="kick and stick, light and quick",
        supports={"spray"},
    ),
    "mat": Aid(
        id="mat",
        label="a foam mat",
        action="stand steady first",
        rhyme="stand and land, safe and grand",
        supports={"wobble", "spray"},
    ),
}

GIRL_NAMES = ["Mina", "Luna", "Nia", "Tessa", "Ivy", "Rosa"]
BOY_NAMES = ["Pip", "Theo", "Milo", "Arlo", "Finn", "Owen"]
COACHES = ["coach", "teacher", "trainer"]


def _narrate_rhyme(lesson: Lesson) -> str:
    return {
        "rim": "At the curb, the world felt blur and stir, but rhythm made the feet feel sure.",
        "kick": "By the blue pool line, the splashes shone like silver wine.",
        "float": "On quiet water, courage grew, like a boat that found its true blue hue.",
    }[lesson.id]


def _do_lesson(world: World, child: Entity, lesson: Lesson, narrate: bool = True) -> None:
    child.meters[lesson.risk] = child.meters.get(lesson.risk, 0.0) + 1.0
    child.memes["nervous"] = child.memes.get("nervous", 0.0) + 1.0
    if narrate:
        world.say(f"{child.id} wanted to {lesson.verb}, but {child.pronoun('possessive')} knees felt small and shy.")
        world.say(_narrate_rhyme(lesson))


def _choose_aid(lesson: Lesson) -> Optional[Aid]:
    for aid in AIDS.values():
        if lesson.risk in aid.supports:
            return aid
    return None


def tell(params: StoryParams) -> World:
    world = World(SWIM_SCHOOL)
    lesson = LESSONS[params.lesson]
    child = world.add(Entity(
        id=params.name,
        kind="character",
        type=params.gender,
        meters={},
        memes={},
    ))
    coach = world.add(Entity(
        id="coach",
        kind="character",
        type=params.coach,
        label=f"the {params.coach}",
        meters={},
        memes={},
    ))

    world.say(f"At swim school, little {child.id} came to the pool with a brave face and a shy heart.")
    world.say(f"The curb by the pool looked hard and still, and the water winked and waited.")
    world.say(f"{child.id} loved the lesson song: “{lesson.rhythm}.”")

    world.para()
    _do_lesson(world, child, lesson, narrate=True)
    world.say(f"But when {child.id} reached the curb, {child.pronoun('possessive')} courage began to wobble.")

    world.para()
    aid = _choose_aid(lesson)
    if aid is None:
        raise StoryError("No aid fits this lesson; the story cannot find a true fable-like turn.")

    world.facts.update(child=child, coach=coach, lesson=lesson, aid=aid)
    child.memes["hope"] = child.memes.get("hope", 0.0) + 1.0
    world.say(f"Then {coach.label} smiled and held up {aid.label}.")
    world.say(f'"{aid.rhyme}," said {coach.label}, "and {aid.action}."')
    child.memes["nervous"] = 0.0
    child.memes["brave"] = child.memes.get("brave", 0.0) + 1.0
    child.meters["skill"] = child.meters.get("skill", 0.0) + 1.0

    world.say(f"{child.id} listened, and the rhyme sounded like a handrail for the heart.")
    world.say(f"At once, {child.id} could {lesson.verb} without a frown, because the helper gave a safer way around.")
    world.para()
    world.say(f"By the end, {child.id} was {lesson.gerund}, smiling at the curb instead of fearing it.")
    world.say(f"The little lesson was plain: slow words and steady tools can turn a wobble into a win.")
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    child = f["child"]
    lesson = f["lesson"]
    aid = f["aid"]
    return [
        f'Write a short fable for a young child set at swim school that includes the word "curb".',
        f"Tell a rhyming story where {child.id} learns to {lesson.verb} with help from {aid.label}.",
        f"Write a gentle swim-school fable with a curb, a chant, and a brave ending.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child = f["child"]
    lesson = f["lesson"]
    aid = f["aid"]
    coach = f["coach"]
    return [
        QAItem(
            question=f"Where did {child.id} learn the lesson?",
            answer=f"{child.id} learned it at swim school, by the curb near the pool.",
        ),
        QAItem(
            question=f"What did {child.id} want to do before the helper spoke?",
            answer=f"{child.id} wanted to {lesson.verb}, but {child.pronoun('possessive')} heart felt shy.",
        ),
        QAItem(
            question=f"What helped {child.id} feel brave?",
            answer=f"{aid.label} helped, and {coach.label} taught the rhyme that made the steps feel steady.",
        ),
        QAItem(
            question=f"How did the story end?",
            answer=f"It ended with {child.id} {lesson.gerund}, smiling at the curb and feeling proud.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a curb?",
            answer="A curb is a raised edge beside a road, path, or walkway. It helps mark the side and keep people on the right path.",
        ),
        QAItem(
            question="What is a rhyme?",
            answer="A rhyme is when words sound alike at the end, like sing and swing.",
        ),
        QAItem(
            question="Why do coaches use simple chants?",
            answer="Coaches use simple chants to help children remember steps, keep time, and feel calmer while they learn.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    for p in sample.prompts:
        lines.append(p)
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
    out = ["--- trace ---"]
    for e in world.entities.values():
        out.append(f"{e.id}: meters={e.meters} memes={e.memes}")
    return "\n".join(out)


def asp_facts() -> str:
    import asp
    lines = [asp.fact("place", "swim_school"), asp.fact("feature", "curb"), asp.fact("feature", "rhyme")]
    for lid, lesson in LESSONS.items():
        lines.append(asp.fact("lesson", lid))
        lines.append(asp.fact("risk", lid, lesson.risk))
        for t in sorted(lesson.tags):
            lines.append(asp.fact("tags", lid, t))
    for aid in AIDS.values():
        lines.append(asp.fact("aid", aid.id))
        for s in sorted(aid.supports):
            lines.append(asp.fact("supports", aid.id, s))
    return "\n".join(lines)


ASP_RULES = r"""
shown_valid(L,A) :- lesson(L), aid(A), risk(L,R), supports(A,R).
#show shown_valid/2.
"""


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_pairs() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show shown_valid/2."))
    return sorted(set(asp.atoms(model, "shown_valid")))


def python_valid_pairs() -> list[tuple]:
    out = []
    for lid, lesson in LESSONS.items():
        for aid in AIDS.values():
            if lesson.risk in aid.supports:
                out.append((lid, aid.id))
    return sorted(out)


def asp_verify() -> int:
    a = set(asp_valid_pairs())
    p = set(python_valid_pairs())
    if a == p:
        print(f"OK: ASP matches Python ({len(a)} valid lesson-aid pairs).")
        return 0
    print("MISMATCH:")
    print("only in ASP:", sorted(a - p))
    print("only in Python:", sorted(p - a))
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Swim-school fable world with curb and rhyme.")
    ap.add_argument("--lesson", choices=LESSONS)
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--coach", choices=COACHES)
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
    lesson = args.lesson or rng.choice(list(LESSONS))
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    coach = args.coach or rng.choice(COACHES)
    return StoryParams(lesson=lesson, name=name, gender=gender, coach=coach)


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
    StoryParams(lesson="rim", name="Mina", gender="girl", coach="coach"),
    StoryParams(lesson="kick", name="Pip", gender="boy", coach="teacher"),
    StoryParams(lesson="float", name="Ivy", gender="girl", coach="trainer"),
]


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show shown_valid/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        pairs = asp_valid_pairs()
        print(f"{len(pairs)} valid lesson-aid pairs:")
        for a, b in pairs:
            print(f"  {a} -> {b}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 20):
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
        header = f"### variant {i + 1}" if len(samples) > 1 and not args.all else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()

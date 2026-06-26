#!/usr/bin/env python3
"""
A small storyworld for a rhyming marathon tale with repetition and a lesson learned.

This world models a child-friendly neighborhood marathon where a runner learns
that going too fast at the start makes the finish much harder. The story uses
repeated lines, rhyme-like phrasing, and a clear change in state: the runner
begins eager and hasty, grows tired, then learns to pace carefully and finish
strong.
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
# World model
# ---------------------------------------------------------------------------

@dataclass
class Entity:
    id: str
    kind: str = "thing"
    label: str = ""
    phrase: str = ""
    plural: bool = False
    owner: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Course:
    place: str
    start_phrase: str
    finish_phrase: str
    crowd_phrase: str
    length: int
    water_stop: bool = True


@dataclass
class Pace:
    label: str
    speed: float
    rhyme: str
    lesson: str


@dataclass
class World:
    course: Course
    entities: dict[str, Entity] = field(default_factory=dict)
    events: list[str] = field(default_factory=list)
    facts: dict = field(default_factory=dict)

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str) -> Entity:
        return self.entities[eid]

    def say(self, text: str) -> None:
        if text:
            self.events.append(text)

    def render(self) -> str:
        return " ".join(self.events)


# ---------------------------------------------------------------------------
# Content registries
# ---------------------------------------------------------------------------

COURSES = {
    "park_path": Course(
        place="the park path",
        start_phrase="The start line stood straight and bright",
        finish_phrase="The finish tape shimmered in the light",
        crowd_phrase="The crowd clapped softly, row by row",
        length=5,
        water_stop=True,
    ),
    "river_loop": Course(
        place="the river loop",
        start_phrase="The morning breeze was cool and sweet",
        finish_phrase="The ribbon finish waited at the street",
        crowd_phrase="The watchers waved and cheered the way",
        length=6,
        water_stop=True,
    ),
}

PACES = {
    "rush": Pace(
        label="rush-fast",
        speed=1.8,
        rhyme="dash",
        lesson="too much haste can make the race a waste",
    ),
    "steady": Pace(
        label="steady-step",
        speed=1.0,
        rhyme="glide",
        lesson="a steady pace can win the place",
    ),
    "slow": Pace(
        label="slow-and-sure",
        speed=0.8,
        rhyme="sway",
        lesson="slow and sure can help you endure",
    ),
}

NAMES = ["Milo", "Nina", "Toby", "Lena", "Arlo", "Ivy", "Penny", "Jules"]
TITLES = {
    "coach": "Coach Bean",
    "parent": "Mom",
    "friend": "Ziggy",
}


@dataclass
class StoryParams:
    course: str
    pace: str
    runner: str
    helper: str
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# State helpers
# ---------------------------------------------------------------------------

def _meter(entity: Entity, key: str) -> float:
    return entity.meters.get(key, 0.0)


def _meme(entity: Entity, key: str) -> float:
    return entity.memes.get(key, 0.0)


def _set_meter(entity: Entity, key: str, value: float) -> None:
    entity.meters[key] = value


def _add_meter(entity: Entity, key: str, delta: float) -> None:
    entity.meters[key] = _meter(entity, key) + delta


def _add_meme(entity: Entity, key: str, delta: float) -> None:
    entity.memes[key] = _meme(entity, key) + delta


# ---------------------------------------------------------------------------
# Simulation
# ---------------------------------------------------------------------------

def run_marathon(world: World, runner: Entity, pace: Pace) -> None:
    course = world.course
    _set_meter(runner, "distance", 0.0)
    _set_meter(runner, "tired", 0.0)
    _set_meter(runner, "water", 0.0)
    _set_meter(runner, "finish", 0.0)
    _add_meme(runner, "hope", 1.0)

    world.say(f"{runner.id} stood at {course.start_phrase}.")
    world.say(f"{course.crowd_phrase}, and {runner.id} smiled with bright-eyed style.")
    world.say(
        f"{runner.id} whispered, 'Run, run, run,' and started off with a {pace.rhyme}."
    )

    # Repetition: a child-friendly refrain that also marks state change.
    world.say(f"Run, run, run, {runner.id} went on. Run, run, run, until the first mile was gone.")

    # Initial burst.
    _add_meter(runner, "distance", 2.0 * pace.speed)
    _add_meter(runner, "tired", 1.4 if pace.label == "rush-fast" else 0.8)

    if pace.label == "rush-fast":
        _add_meme(runner, "impulse", 2.0)
        world.say(
            f"{runner.id} dashed ahead so quick and grand, but soon their legs felt heavy on the land."
        )
        world.say(
            f"The fast start felt fun, yet it came with a cost; the breath got short, and the rhythm was lost."
        )
    elif pace.label == "steady-step":
        _add_meme(runner, "calm", 1.5)
        world.say(
            f"{runner.id} kept a steady step and grin, like a song that starts soft and gathers within."
        )
    else:
        _add_meme(runner, "calm", 2.0)
        world.say(
            f"{runner.id} went slow and sure, with tiny light feet, like a drumbeat humming in the heat."
        )

    # Mid-course lesson: the helper gives advice if the runner is too tired or too quick.
    if _meter(runner, "tired") >= 1.0 or pace.label == "rush-fast":
        helper = world.get("helper")
        _add_meme(helper, "care", 1.0)
        world.say(
            f"{helper.label} called, 'Small steps help! Small steps, my dear! "
            f"Save some spark for the end so the finish stays near.'"
        )
        world.say(
            f"{runner.id} listened and learned. The lesson was clear: {pace.lesson}."
        )
        _add_meme(runner, "understanding", 2.0)
        _set_meter(runner, "tired", max(0.2, _meter(runner, "tired") - 0.7))
        _set_meter(runner, "finish", 1.0)

    # Water stop or rest stop.
    if course.water_stop:
        _add_meter(runner, "water", 1.0)
        world.say(
            f"At the water stop, {runner.id} took a sip and a smile, then trotted again in a wiser style."
        )

    # Final stretch.
    _add_meter(runner, "distance", 3.0)
    _add_meter(runner, "finish", 2.0)
    _add_meme(runner, "pride", 1.0)
    _add_meme(runner, "lesson_learned", 1.0)

    world.say(f"{course.finish_phrase}, and {runner.id} found a second wind.")
    world.say(
        f"Run, run, run, but not too fast; the careful pace helped {runner.id} last."
    )
    world.say(
        f"{runner.id} crossed the line with a happy cheer, knowing slow, smart choices can help you get there."
    )

    world.facts.update(
        runner=runner,
        helper=world.get("helper"),
        pace=pace,
        course=course,
    )


# ---------------------------------------------------------------------------
# Story assembly
# ---------------------------------------------------------------------------

def build_world(params: StoryParams) -> World:
    course = COURSES[params.course]
    pace = PACES[params.pace]
    world = World(course=course)

    runner = world.add(Entity(
        id=params.runner,
        kind="character",
        label=params.runner,
        meters={"distance": 0.0, "tired": 0.0, "water": 0.0, "finish": 0.0},
        memes={"hope": 0.0, "impulse": 0.0, "calm": 0.0, "understanding": 0.0, "pride": 0.0},
    ))
    helper = world.add(Entity(
        id="helper",
        kind="character",
        label=params.helper,
        meters={},
        memes={"care": 0.0},
    ))
    world.facts["runner"] = runner
    world.facts["helper"] = helper
    run_marathon(world, runner, pace)
    return world


def story_text(world: World) -> str:
    return world.render()


# ---------------------------------------------------------------------------
# Q&A
# ---------------------------------------------------------------------------

def generation_prompts(world: World) -> list[str]:
    f = world.facts
    runner = f["runner"]
    pace = f["pace"]
    course = f["course"]
    return [
        f"Write a short rhyming story about {runner.id} running a marathon at {course.place}.",
        f"Tell a child-friendly repetition story where {runner.id} learns that {pace.lesson}.",
        f"Write a gentle marathon tale with rhyme, repeated phrases, and a lesson learned.",
    ]


def story_qa(world: World) -> list[QAItem]:
    runner = world.facts["runner"]
    helper = world.facts["helper"]
    pace = world.facts["pace"]
    course = world.facts["course"]
    tired = _meter(runner, "tired")
    learned = _meme(runner, "lesson_learned") > 0
    return [
        QAItem(
            question=f"What kind of race did {runner.id} run at {course.place}?",
            answer=f"{runner.id} ran a marathon at {course.place}, which is a long race with a start and a finish.",
        ),
        QAItem(
            question=f"Why did {helper.label} tell {runner.id} to slow down?",
            answer=f"{helper.label} saw that {runner.id} was getting tired and needed a steadier pace to finish well.",
        ),
        QAItem(
            question=f"What lesson did {runner.id} learn by the end?",
            answer=f"{runner.id} learned that {pace.lesson}. That helped {runner.id} keep going and finish strong.",
        ),
        QAItem(
            question=f"How did {runner.id} feel after crossing the line?",
            answer=f"{runner.id} felt proud and happy after the marathon, because the careful finish turned the race into a win.",
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a marathon?",
            answer="A marathon is a very long running race. Runners need practice, patience, and steady effort to finish it.",
        ),
        QAItem(
            question="Why is it smart to keep a steady pace?",
            answer="A steady pace helps your body save energy, so you do not get too tired too soon.",
        ),
        QAItem(
            question="What does it mean to learn a lesson?",
            answer="Learning a lesson means you understand something important that helps you make a better choice next time.",
        ),
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


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------

ASP_RULES = r"""
runner_can_finish(Pace) :- pace(Pace).
lesson_learned(Pace) :- runner_can_finish(Pace), steady(Pace).
valid_story(Course, Pace) :- course(Course), pace(Pace), lesson(Pace).
"""

def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for cid, course in COURSES.items():
        lines.append(asp.fact("course", cid))
        lines.append(asp.fact("length", cid, course.length))
        if course.water_stop:
            lines.append(asp.fact("water_stop", cid))
    for pid, pace in PACES.items():
        lines.append(asp.fact("pace", pid))
        if pid == "steady":
            lines.append(asp.fact("steady", pid))
        lines.append(asp.fact("lesson", pid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_stories() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/2."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    python_set = {(c, p) for c in COURSES for p in PACES}
    clingo_set = set(asp_valid_stories())
    if python_set == clingo_set:
        print(f"OK: clingo gate matches Python ({len(clingo_set)} story pairs).")
        return 0
    print("MISMATCH between clingo and Python:")
    if clingo_set - python_set:
        print("  only in clingo:", sorted(clingo_set - python_set))
    if python_set - clingo_set:
        print("  only in python:", sorted(python_set - clingo_set))
    return 1


# ---------------------------------------------------------------------------
# Params, generation, emit
# ---------------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="A rhyming marathon storyworld with repetition and a lesson learned."
    )
    ap.add_argument("--course", choices=sorted(COURSES))
    ap.add_argument("--pace", choices=sorted(PACES))
    ap.add_argument("--runner")
    ap.add_argument("--helper", choices=["Coach Bean", "Mom", "Ziggy"])
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
    course = args.course or rng.choice(list(COURSES))
    pace = args.pace or rng.choice(list(PACES))
    runner = args.runner or rng.choice(NAMES)
    helper = args.helper or rng.choice(list(TITLES.values()))
    return StoryParams(course=course, pace=pace, runner=runner, helper=helper)


def generate(params: StoryParams) -> StorySample:
    world = build_world(params)
    return StorySample(
        params=params,
        story=story_text(world),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_qa(world),
        world=world,
    )


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
        lines.append(f"  {e.id:8} ({e.kind:9}) {' '.join(bits)}")
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


CURATED = [
    StoryParams(course="park_path", pace="rush", runner="Milo", helper="Coach Bean"),
    StoryParams(course="park_path", pace="steady", runner="Nina", helper="Mom"),
    StoryParams(course="river_loop", pace="slow", runner="Toby", helper="Ziggy"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid_story/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        model = asp.one_model(asp_program("#show valid_story/2."))
        pairs = sorted(set(asp.atoms(model, "valid_story")))
        print(f"{len(pairs)} compatible course/pace pairs:")
        for c, p in pairs:
            print(f"  {c:12} {p}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
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
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()

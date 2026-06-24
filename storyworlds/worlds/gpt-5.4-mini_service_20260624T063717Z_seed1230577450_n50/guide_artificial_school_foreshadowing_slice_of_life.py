#!/usr/bin/env python3
"""
storyworlds/worlds/guide_artificial_school_foreshadowing_slice_of_life.py
========================================================================

A small, self-contained storyworld about a school day, an artificial guide,
and gentle foreshadowing in a slice-of-life style.

The seed premise:
- In a school, a student relies on a guide.
- The guide is artificial: a small robot or tablet assistant.
- Quiet foreshadowing suggests a small problem later in the day.
- The turn is not a big adventure, but a small social correction that feels
  true to school life.

This script models a few concrete meters and memes:
- physical meters: charge, papers, dust, wetness
- emotional memes: calm, worry, trust, embarrassment, relief

The story world supports one compact premise with a state-driven turn:
a helpful artificial guide starts with a small hidden limitation, foreshadowed
early, which later matters during a routine school moment. The student notices,
adapts, and the day ends warmly.

Contract notes:
- stdlib-only script
- imports storyworlds/results eagerly
- imports storyworlds/asp lazily inside ASP helpers
- defines StoryParams, registries, build_parser, resolve_params, generate,
  emit, and main
- supports --trace, --qa, --json, --asp, --verify, --show-asp, --all, -n, --seed
"""

from __future__ import annotations

import argparse
import copy
import json
import os
import random
import sys
from dataclasses import dataclass, field
from typing import Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from results import QAItem, StoryError, StorySample  # noqa: E402

FORESHADOW_THRESHOLD = 1.0
HELPFUL_THRESHOLD = 1.0
LIMITATION_THRESHOLD = 1.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    carried_by: Optional[str] = None
    plural: bool = False
    artificial: bool = False
    guide: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.kind == "character":
            if self.type in {"girl", "woman"}:
                return {"subject": "she", "object": "her", "possessive": "her"}[case]
            if self.type in {"boy", "man"}:
                return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def them(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Location:
    name: str
    inside: bool = True
    tags: set[str] = field(default_factory=set)


@dataclass
class GuideDevice:
    id: str
    label: str
    phrase: str
    kind: str
    help_line: str
    limitation_line: str
    foreshadow_line: str
    tags: set[str] = field(default_factory=set)


@dataclass
class SchoolMoment:
    id: str
    setup: str
    tension: str
    turn: str
    ending: str
    limitation_tag: str
    tags: set[str] = field(default_factory=set)


class World:
    def __init__(self, location: Location) -> None:
        self.location = location
        self.entities: dict[str, Entity] = {}
        self.lines: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
        self.facts: dict = {}

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str) -> Entity:
        return self.entities[eid]

    def say(self, text: str) -> None:
        if text:
            self.lines[-1].append(text)

    def para(self) -> None:
        if self.lines[-1]:
            self.lines.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.lines if p)

    def copy(self) -> "World":
        w = World(self.location)
        w.entities = copy.deepcopy(self.entities)
        w.lines = [[]]
        w.fired = set(self.fired)
        w.facts = copy.deepcopy(self.facts)
        return w


@dataclass
class StoryParams:
    place: str
    guide: str
    moment: str
    name: str
    gender: str
    seed: Optional[int] = None


SCHOOL = {
    "classroom": Location(name="the classroom", inside=True, tags={"quiet", "lesson"}),
    "hallway": Location(name="the hallway", inside=True, tags={"crowd", "between"}),
    "library": Location(name="the library", inside=True, tags={"quiet", "book"}),
    "art_room": Location(name="the art room", inside=True, tags={"paint", "table"}),
    "lunchroom": Location(name="the lunchroom", inside=True, tags={"meal", "noise"}),
}

GUIDES = {
    "tablet": GuideDevice(
        id="tablet",
        label="a small tablet guide",
        phrase="a small tablet with a bright map",
        kind="tablet",
        help_line="the map glowed softly and showed the next turn",
        limitation_line="its battery icon had started to blink low",
        foreshadow_line="the little battery icon was already blinking in the corner",
        tags={"screen", "battery", "map"},
    ),
    "robot": GuideDevice(
        id="robot",
        label="a tiny robot guide",
        phrase="a tiny round robot with a sticker badge",
        kind="robot",
        help_line="its speaker gave a cheerful beep and pointed the way",
        limitation_line="one wheel clicked whenever it rolled too far",
        foreshadow_line="one wheel gave a quiet click whenever it turned too fast",
        tags={"wheel", "battery", "beep"},
    ),
    "badge": GuideDevice(
        id="badge",
        label="an artificial guide badge",
        phrase="an artificial guide badge clipped to a lanyard",
        kind="badge",
        help_line="the badge flashed a neat arrow for the class line",
        limitation_line="the tiny arrow lagged a little when the hall got crowded",
        foreshadow_line="its arrow had already lagged once near the door",
        tags={"badge", "arrow", "crowd"},
    ),
}

MOMENTS = {
    "map": SchoolMoment(
        id="map",
        setup="find the reading corner after morning bell",
        tension="the hallway turned crowded and the first map route got crowded too",
        turn="the student chose to follow the older hallway sign instead",
        ending="the student reached the reading corner and sat down with a sigh of relief",
        limitation_tag="battery",
        tags={"hallway", "reading", "map"},
    ),
    "page": SchoolMoment(
        id="page",
        setup="carry a stack of papers to the office",
        tension="the stack slipped a little when the bell rang and everyone moved",
        turn="the student steadied the pages with one careful hand",
        ending="the papers stayed neat on the office desk",
        limitation_tag="wheel",
        tags={"papers", "office", "quiet"},
    ),
    "art": SchoolMoment(
        id="art",
        setup="bring paint cups back to the sink",
        tension="a crowded table made the guide slow just when the cups needed balance",
        turn="the student paused, waited, and let the line clear before moving",
        ending="the paint cups got back safely and the art room stayed tidy",
        limitation_tag="arrow",
        tags={"art", "paint", "table"},
    ),
    "lunch": SchoolMoment(
        id="lunch",
        setup="find a seat with a lunch tray",
        tension="the lunchroom was noisy and the guide's voice got hard to hear",
        turn="the student looked up, spotted a free seat, and used that instead",
        ending="the lunch tray landed safely and the day felt ordinary in a good way",
        limitation_tag="battery",
        tags={"lunch", "noise", "tray"},
    ),
}

GIRL_NAMES = ["Mia", "Lily", "Ava", "Nora", "Zoe", "June", "Maya", "Ella"]
BOY_NAMES = ["Leo", "Theo", "Finn", "Noah", "Eli", "Max", "Ben", "Sam"]


def _female_type(gender: str) -> str:
    return "girl" if gender == "girl" else "boy"


def _story_name(gender: str, rng: random.Random) -> str:
    return rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)


def valid_combos() -> list[tuple[str, str]]:
    return [(place, guide) for place in SCHOOL for guide in GUIDES]


def explain_rejection(place: str, guide: str) -> str:
    return f"(No story: {guide} is not a valid guide choice for {place}.)"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="School slice-of-life with an artificial guide and gentle foreshadowing.")
    ap.add_argument("--place", choices=SCHOOL)
    ap.add_argument("--guide", choices=GUIDES)
    ap.add_argument("--moment", choices=MOMENTS)
    ap.add_argument("--gender", choices=["girl", "boy"])
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
    combos = valid_combos()
    if args.place and args.guide:
        if (args.place, args.guide) not in combos:
            raise StoryError(explain_rejection(args.place, args.guide))
    place = args.place or rng.choice(list(SCHOOL))
    guide = args.guide or rng.choice(list(GUIDES))
    moment = args.moment or rng.choice(list(MOMENTS))
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or _story_name(gender, rng)
    return StoryParams(place=place, guide=guide, moment=moment, name=name, gender=gender)


def _narrate(world: World, student: Entity, guide: GuideDevice, moment: SchoolMoment) -> None:
    world.say(f"{student.id} arrived at {world.location.name} with {guide.label}.")
    world.say(f"It looked ordinary at first, but {guide.foreshadow_line}.")
    world.para()
    world.say(f"Before long, {student.id} needed to {moment.setup}.")
    world.say(f"{guide.help_line}, which made the day feel easier.")
    world.say(f"Then {moment.tension}.")
    world.say(f"That was the small surprise the little warning had been hinting at.")
    world.para()
    world.say(f"{student.id} did not panic.")
    world.say(f"{moment.turn}.")
    world.say(f"In the end, {moment.ending}.")
    world.say(f"{student.id} smiled because {guide.label} had helped, even with its little limitation.")


def generate(params: StoryParams) -> StorySample:
    location = SCHOOL[params.place]
    guide_def = GUIDES[params.guide]
    moment = MOMENTS[params.moment]
    world = World(location)
    student = world.add(Entity(
        id=params.name,
        kind="character",
        type=_female_type(params.gender),
        label=params.name,
        meters={"charge": 0.0},
        memes={"calm": 1.0, "trust": 1.0},
    ))
    guide = world.add(Entity(
        id=guide_def.id,
        kind="thing",
        type=guide_def.kind,
        label=guide_def.label,
        phrase=guide_def.phrase,
        owner=student.id,
        carried_by=student.id,
        artificial=True,
        guide=True,
        meters={"charge": 1.0},
        memes={"helpful": 1.0},
    ))
    # State: foreshadowing and limitation are physical + emotional.
    guide.meters["charge"] = 0.4 if guide_def.id == "tablet" else 0.6
    guide.meters["limit"] = 1.0
    student.memes["worry"] = 0.0
    student.memes["relief"] = 0.0
    world.facts.update(student=student, guide=guide, guide_def=guide_def, moment=moment, location=location)
    _narrate(world, student, guide_def, moment)
    student.memes["calm"] += 1.0
    student.memes["relief"] += 1.0
    guide.meters["charge"] += 0.1
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
    student = f["student"]
    guide_def = f["guide_def"]
    moment = f["moment"]
    return [
        f"Write a short slice-of-life story about {student.id} at school with {guide_def.label} and a quiet foreshadowed problem.",
        f"Tell a gentle school story where an artificial guide seems helpful, but a small limitation matters later in the day.",
        f"Write a child-friendly story set in {world.location.name} that includes subtle foreshadowing and an ordinary, kind resolution.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    student = f["student"]
    guide_def = f["guide_def"]
    moment = f["moment"]
    return [
        QAItem(
            question=f"Who is the story about at {world.location.name}?",
            answer=f"The story is about {student.id}, who is at {world.location.name} with {guide_def.label}.",
        ),
        QAItem(
            question=f"What small clue hinted that {guide_def.label} might have trouble later?",
            answer=f"The clue was that {guide_def.foreshadow_line.lower()}.",
        ),
        QAItem(
            question=f"What did {student.id} do when the small problem showed up?",
            answer=f"{student.id} stayed calm, noticed the situation, and followed a simple everyday solution: {moment.turn}.",
        ),
        QAItem(
            question=f"How did the story end for {student.id}?",
            answer=f"It ended with {moment.ending}, so the school day felt steady again.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is an artificial guide?",
            answer="An artificial guide is a helpful made object, like a robot or device, that gives directions or reminders.",
        ),
        QAItem(
            question="What is foreshadowing?",
            answer="Foreshadowing is a small clue early in a story that hints something important may happen later.",
        ),
        QAItem(
            question="Why do school days often feel like slice of life stories?",
            answer="Because they are full of small everyday moments, like walking in halls, carrying papers, and finding a seat.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== story QA ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== world QA ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        lines.append(
            f"  {e.id:10} kind={e.kind:8} type={e.type:8} "
            f"meters={{{', '.join(f'{k}: {v}' for k, v in e.meters.items() if v)}}} "
            f"memes={{{', '.join(f'{k}: {v}' for k, v in e.memes.items() if v)}}}"
        )
    return "\n".join(lines)


CURATED = [
    StoryParams(place="classroom", guide="tablet", moment="map", name="Mia", gender="girl"),
    StoryParams(place="hallway", guide="robot", moment="page", name="Leo", gender="boy"),
    StoryParams(place="library", guide="badge", moment="page", name="Nora", gender="girl"),
    StoryParams(place="art_room", guide="tablet", moment="art", name="Finn", gender="boy"),
    StoryParams(place="lunchroom", guide="robot", moment="lunch", name="Ava", gender="girl"),
]


ASP_RULES = r"""
place(P) :- school_place(P).
guide(G) :- guide_kind(G).
moment(M) :- school_moment(M).

valid(P,G,M) :- school_place(P), guide_kind(G), school_moment(M).
compatible(P,G) :- school_place(P), guide_kind(G).

#show valid/3.
#show compatible/2.
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for p in SCHOOL:
        lines.append(asp.fact("school_place", p))
    for g in GUIDES:
        lines.append(asp.fact("guide_kind", g))
    for m in MOMENTS:
        lines.append(asp.fact("school_moment", m))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    import asp
    py = {(p, g, m) for p in SCHOOL for g in GUIDES for m in MOMENTS}
    cl = set(asp_valid())
    if py == cl:
        print(f"OK: clingo gate matches python ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and python:")
    print("only python:", sorted(py - cl))
    print("only clingo:", sorted(cl - py))
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
        print(asp_program("#show valid/3.\n#show compatible/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        vals = asp_valid()
        print(f"{len(vals)} compatible combos")
        for row in vals:
            print(row)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
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
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()

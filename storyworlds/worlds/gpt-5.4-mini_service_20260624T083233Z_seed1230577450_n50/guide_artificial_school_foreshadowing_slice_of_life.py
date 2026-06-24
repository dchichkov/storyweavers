#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260624T083233Z_seed1230577450_n50/guide_artificial_school_foreshadowing_slice_of_life.py
=============================================================================================================================

A small school storyworld about a child, a guide, and a gently foreshadowed
slice-of-life turn.

Premise:
- A student is new to a school routine and carries or receives a guide item.
- Something artificial in the school space acts as a small visual clue.
- Early details foreshadow a later, ordinary problem or helpful turn.
- The story resolves with a calm, child-facing change in the student's state.

The world is intentionally tiny: a school day, a few typed entities, and a
single causal arc that can be narrated in different concrete ways.
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
    carried_by: Optional[str] = None
    location: str = ""
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "student"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str = "the school"
    affords: set[str] = field(default_factory=set)


@dataclass
class GuideItem:
    id: str
    label: str
    phrase: str
    use: str
    clue: str
    kind: str
    helps_with: set[str] = field(default_factory=set)


@dataclass
class Foreshadow:
    id: str
    sign: str
    hint: str
    later: str


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

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)

    def copy(self) -> "World":
        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        clone.facts = copy.deepcopy(self.facts)
        return clone


def _entity_label(e: Entity) -> str:
    return e.label or e.id


def _article_phrase(s: str) -> str:
    if not s:
        return s
    return f"an {s}" if s[0].lower() in "aeiou" else f"a {s}"


def _do_routine(world: World, student: Entity, guide: GuideItem, narrate: bool = True) -> None:
    student.memes["confidence"] = student.memes.get("confidence", 0.0) + 1
    student.meters["readiness"] = student.meters.get("readiness", 0.0) + 1
    if guide.kind == "map":
        student.memes["orientation"] = student.memes.get("orientation", 0.0) + 1
    if guide.kind == "note":
        student.memes["calm"] = student.memes.get("calm", 0.0) + 1


def predict_later(world: World, student: Entity, guide: GuideItem, fs: Foreshadow) -> dict:
    sim = world.copy()
    _do_routine(sim, sim.get(student.id), guide, narrate=False)
    return {
        "ready": sim.entities[student.id].meters.get("readiness", 0.0) >= THRESHOLD,
        "calm": sim.entities[student.id].memes.get("calm", 0.0) >= THRESHOLD,
        "hint": fs.hint,
        "later": fs.later,
    }


def introduce(world: World, student: Entity) -> None:
    world.say(
        f"{student.id} was a little {student.type} who noticed quiet details at school."
    )


def setup(world: World, student: Entity, guide: GuideItem, art: Entity, fs: Foreshadow) -> None:
    world.say(
        f"On the first morning, {student.id} carried {guide.phrase} through {world.setting.place}."
    )
    world.say(
        f"Near the office, {student.pronoun('possessive').capitalize()} eyes caught sight of {art.phrase}."
    )
    world.say(
        f"It looked {fs.sign}, and that small sight would matter later."
    )


def tension(world: World, student: Entity, guide: GuideItem, fs: Foreshadow) -> None:
    student.memes["nervous"] = student.memes.get("nervous", 0.0) + 1
    world.say(
        f"At the noisy hallway turn, {student.id} paused and held {guide.label} a little tighter."
    )
    world.say(
        f"{guide.clue.capitalize()}, the guide seemed to say, even before anything went wrong."
    )


def turn(world: World, student: Entity, guide: GuideItem, fs: Foreshadow) -> None:
    student.memes["lost"] = student.memes.get("lost", 0.0) + 1
    world.say(
        f"When the bell rang, the crowd shuffled fast, and {student.id} almost took the wrong corridor."
    )
    world.say(
        f"Then {student.id} remembered the guide's clue: {fs.hint}."
    )
    _do_routine(world, student, guide)
    world.facts["foreshadow_used"] = fs.id


def resolve(world: World, student: Entity, guide: GuideItem, fs: Foreshadow) -> None:
    student.memes["nervous"] = 0.0
    student.memes["lost"] = 0.0
    student.memes["relief"] = student.memes.get("relief", 0.0) + 1
    world.say(
        f"{student.id} followed the guide and found the right room without rushing."
    )
    world.say(
        f"By then, the little {artificial_word()} detail had turned into a helpful sign, and {student.id} smiled."
    )
    world.say(
        f"{student.pronoun('subject').capitalize()} sat down in the right place, ready for the rest of the school day."
    )


def artificial_word() -> str:
    return "artificial"


def tell(setting: Setting, student_name: str, student_type: str, guide: GuideItem, art: Entity, fs: Foreshadow) -> World:
    world = World(setting)
    student = world.add(Entity(id=student_name, kind="character", type=student_type))
    guide_ent = world.add(Entity(
        id=guide.id,
        kind="thing",
        type=guide.kind,
        label=guide.label,
        phrase=guide.phrase,
        caretaker=student.id,
        carried_by=student.id,
    ))
    art_ent = world.add(art)

    introduce(world, student)
    setup(world, student, guide, art_ent, fs)
    world.para()
    tension(world, student, guide, fs)
    turn(world, student, guide, fs)
    world.para()
    resolve(world, student, guide, fs)

    world.facts.update(
        student=student,
        guide=guide,
        guide_ent=guide_ent,
        art=art_ent,
        foreshadow=fs,
        setting=setting,
    )
    return world


@dataclass
class StoryParams:
    place: str
    guide: str
    art: str
    foreshadow: str
    name: str
    kind: str
    seed: Optional[int] = None


SETTINGS = {
    "school": Setting(place="the school", affords={"hallway", "classroom", "office", "library"}),
}

GUIDES = {
    "map": GuideItem(
        id="map",
        label="a school map",
        phrase="a folded school map",
        use="help find the right room",
        clue="the blue line points to the classroom",
        kind="map",
        helps_with={"lost", "nervous"},
    ),
    "note": GuideItem(
        id="note",
        label="a homeroom note",
        phrase="a little note from the teacher",
        use="help remember the room number",
        clue="the room number is written at the top",
        kind="note",
        helps_with={"lost", "nervous"},
    ),
    "tour": GuideItem(
        id="tour",
        label="a student guide booklet",
        phrase="a student guide booklet",
        use="help with the first day",
        clue="the booklet points to the library first",
        kind="guide",
        helps_with={"lost", "nervous"},
    ),
}

ARTIFICIALS = {
    "flower": Entity(
        id="flower",
        kind="thing",
        type="decoration",
        label="artificial flowers",
        phrase="a pot of artificial flowers by the office door",
        location="office",
    ),
    "plant": Entity(
        id="plant",
        kind="thing",
        type="decoration",
        label="artificial plant",
        phrase="an artificial plant beside the hallway window",
        location="hallway",
    ),
    "fish": Entity(
        id="fish",
        kind="thing",
        type="decoration",
        label="artificial fish",
        phrase="an artificial fish mobile near the classroom shelf",
        location="classroom",
    ),
}

FORESHADOWS = {
    "blue": Foreshadow(
        id="blue",
        sign="carefully placed",
        hint="the blue line on the floor pointed toward the room",
        later="the blue line would keep the student from getting lost",
    ),
    "clock": Foreshadow(
        id="clock",
        sign="like it was waiting for someone to notice it",
        hint="the clock above the office already showed the right time",
        later="the clock would help the student arrive before the bell",
    ),
    "window": Foreshadow(
        id="window",
        sign="a little wobbly in the draft",
        hint="the window near the hall was open just a crack",
        later="the crack would remind the student to use the covered path",
    ),
}

NAMES = ["Mina", "Leo", "Ari", "Nia", "Jun", "Tessa", "Owen", "Maya"]
KINDS = ["girl", "boy", "student"]


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for place in SETTINGS:
        for guide in GUIDES:
            for art in ARTIFICIALS:
                combos.append((place, guide, art))
    return combos


def reasonableness_gate(place: str, guide: str, art: str) -> bool:
    return place == "school" and guide in GUIDES and art in ARTIFICIALS


def explain_rejection(place: str, guide: str, art: str) -> str:
    return "(No story: this tiny world only supports a school setting with a guide and an artificial clue.)"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="School slice-of-life storyworld with foreshadowing.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--guide", choices=GUIDES)
    ap.add_argument("--art", choices=ARTIFICIALS)
    ap.add_argument("--foreshadow", choices=FORESHADOWS)
    ap.add_argument("--name")
    ap.add_argument("--kind", choices=KINDS)
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
    place = args.place or "school"
    guide = args.guide or rng.choice(sorted(GUIDES))
    art = args.art or rng.choice(sorted(ARTIFICIALS))
    foreshadow = args.foreshadow or rng.choice(sorted(FORESHADOWS))
    if not reasonableness_gate(place, guide, art):
        raise StoryError(explain_rejection(place, guide, art))
    kind = args.kind or rng.choice(KINDS)
    name = args.name or rng.choice(NAMES)
    return StoryParams(place=place, guide=guide, art=art, foreshadow=foreshadow, name=name, kind=kind)


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a short slice-of-life school story that includes the words "guide" and "artificial".',
        f"Tell a gentle school story about {f['student'].id} using {f['guide'].label} to find the right room.",
        f"Write a classroom story where an {artificial_word()} detail quietly foreshadows what helps later.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    student: Entity = f["student"]
    guide: GuideItem = f["guide"]
    art: Entity = f["art"]
    fs: Foreshadow = f["foreshadow"]
    return [
        QAItem(
            question=f"Who is the story mostly about?",
            answer=f"The story is mostly about {student.id}, a little {student.type} having an ordinary school morning.",
        ),
        QAItem(
            question=f"What did {student.id} carry at the start of the story?",
            answer=f"{student.id} carried {guide.phrase}, which was the guide that helped {student.pronoun('object')} stay calm.",
        ),
        QAItem(
            question=f"What artificial thing did {student.id} notice first?",
            answer=f"{student.id} noticed {art.phrase} near the school office.",
        ),
        QAItem(
            question=f"How did the foreshadowing matter later?",
            answer=f"It mattered because the hint {fs.hint} helped {student.id} find the right room before the bell could make {student.pronoun('object')} nervous.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a guide for?",
            answer="A guide helps someone know where to go or what to do next.",
        ),
        QAItem(
            question="What does artificial mean?",
            answer="Artificial means made by people instead of growing or happening naturally.",
        ),
        QAItem(
            question="What is foreshadowing in a story?",
            answer="Foreshadowing is a small clue near the beginning that hints at something important later.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
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
    lines = ["--- world trace ---"]
    for e in world.entities.values():
        bits = []
        if e.location:
            bits.append(f"location={e.location}")
        if e.carried_by:
            bits.append(f"carried_by={e.carried_by}")
        if e.meters:
            bits.append(f"meters={dict(e.meters)}")
        if e.memes:
            bits.append(f"memes={dict(e.memes)}")
        lines.append(f"  {e.id}: {e.type} {' '.join(bits)}")
    return "\n".join(lines)


ASP_RULES = r"""
place_ok(school).
guide_ok(map).
guide_ok(note).
guide_ok(tour).
art_ok(flower).
art_ok(plant).
art_ok(fish).

valid_story(P, G, A) :- place_ok(P), guide_ok(G), art_ok(A).
"""


def asp_facts() -> str:
    import storyworlds.asp as asp
    lines = []
    for p in SETTINGS:
        lines.append(asp.fact("place_ok", p))
    for g in GUIDES:
        lines.append(asp.fact("guide_ok", g))
    for a in ARTIFICIALS:
        lines.append(asp.fact("art_ok", a))
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


def generate(params: StoryParams) -> StorySample:
    guide = GUIDES[params.guide]
    art = copy.deepcopy(ARTIFICIALS[params.art])
    fs = FORESHADOWS[params.foreshadow]
    world = tell(SETTINGS[params.place], params.name, params.kind, guide, art, fs)
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
    StoryParams(place="school", guide="map", art="flower", foreshadow="blue", name="Mina", kind="girl"),
    StoryParams(place="school", guide="note", art="plant", foreshadow="clock", name="Leo", kind="boy"),
    StoryParams(place="school", guide="tour", art="fish", foreshadow="window", name="Ari", kind="student"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid_story/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"{len(asp_valid_combos())} compatible school-story combos:")
        for combo in asp_valid_combos():
            print("  ", combo)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 40):
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
            header = f"### {p.name}: {p.guide} with {p.art} ({p.foreshadow})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()

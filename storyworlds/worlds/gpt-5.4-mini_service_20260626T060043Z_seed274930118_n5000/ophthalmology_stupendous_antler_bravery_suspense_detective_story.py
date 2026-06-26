#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260626T060043Z_seed274930118_n5000/ophthalmology_stupendous_antler_bravery_suspense_detective_story.py
==============================================================================================

A compact detective-story world set in an ophthalmology clinic, with bravery,
suspense, and one strangely stupendous antler clue.

Seed tale premise:
- A young detective visits an eye clinic because something important has gone
  missing.
- The waiting room feels suspenseful, and everyone is watching the eye chart.
- A stupendous antler-shaped clue points the detective toward the truth.
- Bravery lets the shy witness speak up, and the case ends with the missing
  item found exactly where it belongs.

The world model tracks physical meters and emotional memes, and the prose is
driven by state changes rather than a frozen template.
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
    carried_by: Optional[str] = None
    hidden: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "woman", "mother", "nurse"}
        male = {"boy", "man", "father", "doctor", "detective"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.type.endswith("s") else "it"


@dataclass
class Setting:
    place: str
    inside: bool = True
    details: str = ""


@dataclass
class Case:
    id: str
    missing: str
    clue: str
    clue_kind: str
    suspicion: str
    reveal: str
    route: str
    keyword: str
    tags: set[str] = field(default_factory=set)


@dataclass
class StoryParams:
    setting: str
    case: str
    name: str
    gender: str
    companion: str
    trait: str
    seed: Optional[int] = None


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.fired: set[str] = set()

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
        w = World(self.setting)
        w.entities = copy.deepcopy(self.entities)
        w.paragraphs = [[]]
        w.facts = dict(self.facts)
        w.fired = set(self.fired)
        return w


SETTINGS = {
    "clinic": Setting(
        place="the ophthalmology clinic",
        inside=True,
        details="The eye chart hung on the wall like a ladder of tiny secrets.",
    ),
    "waiting_room": Setting(
        place="the waiting room",
        inside=True,
        details="A fish tank bubbled softly beside a row of bright chairs.",
    ),
    "hallway": Setting(
        place="the long hallway",
        inside=True,
        details="Light glinted on the shiny floor and on the glass of every framed chart.",
    ),
}

CASES = {
    "missing_glasses": Case(
        id="missing_glasses",
        missing="glasses",
        clue="a stupendous antler-shaped keychain",
        clue_kind="antler",
        suspicion="someone had taken them away",
        reveal="the glasses were hanging on a coat hook by the nurse's desk",
        route="follow the antler clue to the coat hooks",
        keyword="ophthalmology",
        tags={"ophthalmology", "antler", "suspense", "bravery"},
    ),
    "lost_eye_patch": Case(
        id="lost_eye_patch",
        missing="eye patch",
        clue="a shiny receipt with an antler stamp",
        clue_kind="antler",
        suspicion="the patch had slipped into the wrong basket",
        reveal="the eye patch was tucked into the sticker box",
        route="check the baskets near the eye chart",
        keyword="stupendous",
        tags={"ophthalmology", "antler", "suspense"},
    ),
    "misplaced_contact_case": Case(
        id="misplaced_contact_case",
        missing="contact lens case",
        clue="a stupendous antler magnet",
        clue_kind="antler",
        suspicion="someone had moved it while cleaning",
        reveal="the case was on top of the book about birds and deer",
        route="search the shelf with the antler magnet",
        keyword="bravery",
        tags={"ophthalmology", "antler", "bravery"},
    ),
}

GIRL_NAMES = ["Mia", "Nora", "Ava", "Lily", "June", "Zoe", "Ivy", "Ruby"]
BOY_NAMES = ["Leo", "Eli", "Max", "Noah", "Theo", "Finn", "Jack", "Owen"]
TRAITS = ["curious", "steady", "brave", "careful", "stubborn", "gentle"]


def valid_combos() -> list[tuple[str, str]]:
    return [(s, c) for s in SETTINGS for c in CASES]


@dataclass
class Clue:
    label: str
    type: str
    shine: str
    leads_to: str
    reveals: str
    attention: str = ""


def build_story_world(params: StoryParams) -> World:
    setting = SETTINGS[params.setting]
    case = CASES[params.case]
    world = World(setting)

    detective = world.add(Entity(
        id=params.name,
        kind="character",
        type=params.gender,
        label=params.name,
        owner=None,
        caretaker=None,
    ))
    companion = world.add(Entity(
        id="companion",
        kind="character",
        type=params.companion,
        label=params.companion,
    ))
    doctor = world.add(Entity(
        id="doctor",
        kind="character",
        type="doctor",
        label="Dr. Vale",
    ))
    nurse = world.add(Entity(
        id="nurse",
        kind="character",
        type="nurse",
        label="Nurse Sera",
    ))
    missing = world.add(Entity(
        id="missing",
        type=case.missing,
        label=case.missing,
        phrase=f"the missing {case.missing}",
        owner=companion.id,
        hidden=True,
    ))
    clue = world.add(Entity(
        id="clue",
        type=case.clue_kind,
        label=case.clue_kind,
        phrase=case.clue,
    ))

    world.facts.update(
        detective=detective,
        companion=companion,
        doctor=doctor,
        nurse=nurse,
        missing=missing,
        clue=clue,
        case=case,
        setting=setting,
        trait=params.trait,
    )
    return world


def opening(world: World) -> None:
    f = world.facts
    d = f["detective"]
    c = f["companion"]
    case: Case = f["case"]
    trait = f["trait"]

    d.memes["curiosity"] = 1
    d.memes["bravery"] = 1
    world.say(
        f"{d.label} was a {trait} little detective who loved {world.setting.place} because every quiet room could hide a clue."
    )
    world.say(
        f"That day, {c.label}'s {case.missing} was gone, and the whole clinic felt suspenseful enough to make even the eye chart seem to hold its breath."
    )
    world.say(
        f"{d.label} promised to solve the case before the last patient left."
    )


def investigate(world: World) -> None:
    f = world.facts
    d = f["detective"]
    c = f["companion"]
    case: Case = f["case"]
    d.meters["search"] = d.meters.get("search", 0.0) + 1
    d.memes["suspense"] = d.memes.get("suspense", 0.0) + 1
    world.para()
    world.say(
        f"{d.label} walked past the bright glasses stand and the tall eye chart, looking for anything that matched the clue."
    )
    world.say(
        f"Near the chairs, {d.label} found {case.clue}. It was {case.clue.split()[-1] if ' ' in case.clue else case.clue}, and it looked stupendous."
    )
    world.say(
        f"{c.label} stared at it and whispered that the clue must mean the missing {case.missing} were close by."
    )


def tension(world: World) -> None:
    f = world.facts
    d = f["detective"]
    c = f["companion"]
    nurse = f["nurse"]
    case: Case = f["case"]
    d.memes["suspense"] = d.memes.get("suspense", 0.0) + 1
    c.memes["fear"] = c.memes.get("fear", 0.0) + 1
    nurse.memes["nervous"] = nurse.memes.get("nervous", 0.0) + 1
    world.say(
        f"The clue led {d.label} toward {case.route}, but the waiting room had gone quiet in a way that made every footstep feel important."
    )
    world.say(
        f"{c.label} looked worried, as if saying the wrong thing might make the mystery bigger."
    )
    world.say(
        f"Then {nurse.label} noticed the clue and turned pale, because she had moved something earlier and had not yet told anyone."
    )


def reveal(world: World) -> None:
    f = world.facts
    d = f["detective"]
    c = f["companion"]
    doctor = f["doctor"]
    nurse = f["nurse"]
    missing = f["missing"]
    case: Case = f["case"]

    nurse.memes["bravery"] = nurse.memes.get("bravery", 0.0) + 1
    c.memes["bravery"] = c.memes.get("bravery", 0.0) + 1
    d.memes["bravery"] = d.memes.get("bravery", 0.0) + 1
    world.para()
    world.say(
        f"At last, {nurse.label} took a brave breath and admitted the truth."
    )
    world.say(
        f"She had moved the {case.missing} while tidying the desk, and then it was hidden from view."
    )
    world.say(
        f"{d.label} followed the clue exactly where it pointed, and there was the answer: {case.reveal}."
    )
    missing.hidden = False
    missing.carried_by = c.id
    doctor.memes["relief"] = doctor.memes.get("relief", 0.0) + 1
    world.say(
        f"{doctor.label} smiled and said that bravery had solved what hurry had hidden."
    )
    world.say(
        f"{c.label} held the found {case.missing}, and the suspense in the room melted away at last."
    )


def tell_story(world: World) -> None:
    opening(world)
    investigate(world)
    tension(world)
    reveal(world)
    world.facts["resolved"] = True


def explain_rejection(setting: str, case: str) -> str:
    return f"(No story: the setting '{setting}' and case '{case}' were not recognized.)"


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    case: Case = f["case"]
    d = f["detective"]
    return [
        f'Write a short detective story for a child that includes the words "{case.keyword}", "{case.clue_kind}", and "suspense".',
        f"Tell a gentle mystery set in {world.setting.place} where {d.label} uses bravery to find {case.missing}.",
        f'Write a simple ophthalmology story where a stupendous antler clue helps solve a missing-item case.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    d = f["detective"]
    c = f["companion"]
    case: Case = f["case"]
    qa = [
        QAItem(
            question=f"Who was the detective in the story?",
            answer=f"The detective was {d.label}, a {f['trait']} child who kept watching for clues.",
        ),
        QAItem(
            question=f"What was missing from the clinic?",
            answer=f"The missing item was {case.missing}. That was the mystery {d.label} had to solve.",
        ),
        QAItem(
            question=f"What clue helped solve the case?",
            answer=f"The clue was {case.clue}. It pointed the detective toward the answer.",
        ),
        QAItem(
            question=f"Why did the room feel suspenseful?",
            answer=(
                f"It felt suspenseful because nobody knew where the {case.missing} had gone, "
                f"and everyone was waiting for the clue to make sense."
            ),
        ),
        QAItem(
            question=f"How did bravery matter in the story?",
            answer=(
                f"Bravery mattered when {f['nurse'].label} finally told the truth and when "
                f"{c.label} stayed calm enough to help look for the missing item."
            ),
        ),
    ]
    return qa


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is ophthalmology?",
            answer=(
                "Ophthalmology is the part of medicine that looks after eyes, sight, and eye health."
            ),
        ),
        QAItem(
            question="What does stupendous mean?",
            answer=(
                "Stupendous means amazingly big, wonderful, or impressive."
            ),
        ),
        QAItem(
            question="What is an antler?",
            answer=(
                "An antler is a branched horn that grows on the head of animals like deer."
            ),
        ),
        QAItem(
            question="What does bravery mean?",
            answer=(
                "Bravery means doing what is needed even when you feel nervous or scared."
            ),
        ),
        QAItem(
            question="What is suspense in a story?",
            answer=(
                "Suspense is the feeling of waiting to find out what will happen next."
            ),
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


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        parts = []
        if meters:
            parts.append(f"meters={dict(meters)}")
        if memes:
            parts.append(f"memes={dict(memes)}")
        if e.hidden:
            parts.append("hidden=True")
        lines.append(f"  {e.id:10} ({e.type:10}) {' '.join(parts)}")
    lines.append(f"  fired rules: {sorted(world.fired)}")
    return "\n".join(lines)


ASP_RULES = r"""
setting_choice(S) :- setting(S).
case_choice(C) :- case(C).

compatible(S, C) :- setting_choice(S), case_choice(C).

#show compatible/2.
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for s in SETTINGS:
        lines.append(asp.fact("setting", s))
    for c in CASES:
        lines.append(asp.fact("case", c))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show compatible/2."))
    return sorted(set(asp.atoms(model, "compatible")))


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


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.setting and args.setting not in SETTINGS:
        raise StoryError(explain_rejection(args.setting, args.case or ""))
    if args.case and args.case not in CASES:
        raise StoryError(explain_rejection(args.setting or "", args.case))
    setting = args.setting or rng.choice(list(SETTINGS))
    case = args.case or rng.choice(list(CASES))
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    companion = args.companion or rng.choice(["mother", "father", "nurse"])
    trait = args.trait or rng.choice(TRAITS)
    return StoryParams(setting=setting, case=case, name=name, gender=gender, companion=companion, trait=trait)


def generate(params: StoryParams) -> StorySample:
    world = build_story_world(params)
    tell_story(world)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="A detective story world set in ophthalmology, with suspense, bravery, and a stupendous antler clue."
    )
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--case", choices=CASES)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--name")
    ap.add_argument("--companion", choices=["mother", "father", "nurse"], default=None)
    ap.add_argument("--trait", choices=TRAITS)
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
    StoryParams(setting="clinic", case="missing_glasses", name="Mia", gender="girl", companion="mother", trait="curious"),
    StoryParams(setting="waiting_room", case="lost_eye_patch", name="Leo", gender="boy", companion="father", trait="careful"),
    StoryParams(setting="hallway", case="misplaced_contact_case", name="Nora", gender="girl", companion="nurse", trait="brave"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show compatible/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible setting/case combos:\n")
        for s, c in combos:
            print(f"  {s:14} {c}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
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
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.name}: {p.case} at {p.setting}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()

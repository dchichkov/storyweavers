#!/usr/bin/env python3
"""
Storyworld: a tiny whodunit about aerobics, butter, and a writer who learns a lesson.

Premise
-------
A writer brings a notebook to an aerobics studio. Someone leaves a buttery clue on a bench,
and everyone wonders who caused the mess. The truth is small, physical, and solvable:
a forgotten snack, a slippery towel, and a writer who notices the pattern.

Story shape
-----------
Setup:
    Introduce the writer, the studio, and the odd butter mark.
Tension:
    The writer asks careful questions, but the clue seems to point at the wrong person.
Turn:
    A simple trail of physical evidence reveals what really happened.
Resolution:
    The writer learns a lesson: in a mystery, it helps to look closely before blaming.

The world tracks:
- meters: physical state like butter, sweat, slipperiness, and cleanliness
- memes: emotional state like curiosity, worry, suspicion, relief, and lesson_learned
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
    kind: str = "thing"   # "character" | "thing" | "place"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    carried_by: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)
    traits: list[str] = field(default_factory=list)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman"}
        male = {"boy", "father", "dad", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    def it(self) -> str:
        return "them" if self.type in {"people"} else "it"


@dataclass
class StoryParams:
    place: str
    writer_name: str
    writer_type: str
    suspect_name: str
    suspect_type: str
    seed: Optional[int] = None


@dataclass
class Setting:
    place: str
    clue_spot: str
    lesson: str


@dataclass
class World:
    setting: Setting
    entities: dict[str, Entity] = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    facts: dict = field(default_factory=dict)

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
    "studio": Setting(place="the aerobics studio", clue_spot="bench", lesson="look closely before blaming"),
    "gym": Setting(place="the gym room", clue_spot="mat", lesson="check the clues first"),
    "hall": Setting(place="the community hall", clue_spot="chair", lesson="ask careful questions"),
}

WRITERS = [
    ("Mina", "girl"),
    ("Noah", "boy"),
    ("June", "girl"),
    ("Eli", "boy"),
]

SUSPECTS = [
    ("Coach Pat", "adult"),
    ("Aunt Rose", "adult"),
    ("Ben", "boy"),
    ("Tia", "girl"),
]


# ---------------------------------------------------------------------------
# Story helpers
# ---------------------------------------------------------------------------
def _article(word: str) -> str:
    return "an" if word[:1].lower() in "aeiou" else "a"


def _place_phrase(setting: Setting) -> str:
    return setting.place


def build_world(params: StoryParams) -> World:
    if params.place not in SETTINGS:
        raise StoryError("Unknown place.")
    setting = SETTINGS[params.place]
    world = World(setting=setting)

    writer = world.add(Entity(
        id="writer",
        kind="character",
        type=params.writer_type,
        label=params.writer_name,
        traits=["careful", "curious", "quiet"],
        meters={"butter": 0.0, "sweat": 0.0},
        memes={"curiosity": 1.0, "worry": 0.0, "suspicion": 0.0, "relief": 0.0, "lesson_learned": 0.0},
    ))
    suspect = world.add(Entity(
        id="suspect",
        kind="character",
        type=params.suspect_type,
        label=params.suspect_name,
        traits=["busy"],
        meters={"butter": 0.0, "sweat": 0.0},
        memes={"worry": 0.0},
    ))
    clue = world.add(Entity(
        id="clue",
        kind="thing",
        type="butter",
        label="butter",
        phrase="a buttery smear",
        meters={"freshness": 1.0, "smear": 1.0},
    ))
    notebook = world.add(Entity(
        id="notebook",
        kind="thing",
        type="notebook",
        label="notebook",
        phrase="a small notebook",
        owner=writer.id,
        carried_by=writer.id,
        meters={"clean": 1.0},
    ))
    snack = world.add(Entity(
        id="snack",
        kind="thing",
        type="snack",
        label="snack",
        phrase="a buttered roll",
        owner=suspect.id,
        meters={"butter": 1.0},
    ))

    world.facts.update(writer=writer, suspect=suspect, clue=clue, notebook=notebook, snack=snack)
    return world


def narrate_setup(world: World) -> None:
    f = world.facts
    writer = f["writer"]
    suspect = f["suspect"]
    place = world.setting.place
    writer.memes["curiosity"] += 1
    world.say(
        f"{writer.label} was {_article(writer.type)} {writer.traits[0]} writer who loved collecting small facts."
    )
    world.say(
        f"One afternoon, {writer.label} went to {place} with a notebook tucked under {writer.pronoun('possessive')} arm."
    )
    world.say(
        f"There, a buttery smear sat on the {world.setting.clue_spot}, bright as a secret."
    )
    world.say(
        f"{suspect.label} was nearby, and that made the whole room feel like a whodunit."
    )


def narrate_mystery(world: World) -> None:
    f = world.facts
    writer = f["writer"]
    suspect = f["suspect"]
    writer.memes["worry"] += 1
    writer.memes["suspicion"] += 1
    world.para()
    world.say(
        f"{writer.label} studied the mark, then looked at the floor, then at {suspect.label}."
    )
    world.say(
        f"{writer.label} thought the butter might prove who had been careless."
    )
    world.say(
        f"But the clue did not point to the nearest person the way a quick guess would."
    )


def narrate_turn(world: World) -> None:
    f = world.facts
    writer = f["writer"]
    suspect = f["suspect"]
    clue = f["clue"]

    # Physical chain of evidence
    writer.meters["sweat"] += 1.0
    clue.meters["smear"] += 0.5
    suspect.memes["worry"] += 1.0

    world.para()
    world.say(
        f"{writer.label} noticed a trail of tiny crumbs near the {world.setting.clue_spot}."
    )
    world.say(
        f"That trail led to {suspect.label}'s snack, not to {suspect.label} {writer.pronoun('possessive')} self."
    )
    world.say(
        f"The butter came from a roll that had tipped over when the room got crowded."
    )
    writer.memes["relief"] += 1


def narrate_resolution(world: World) -> None:
    f = world.facts
    writer = f["writer"]
    suspect = f["suspect"]
    lesson = world.setting.lesson

    writer.memes["lesson_learned"] += 1
    writer.memes["suspicion"] = 0.0
    world.para()
    world.say(
        f"{writer.label} closed {writer.pronoun('possessive')} notebook and smiled."
    )
    world.say(
        f"{writer.label} had learned a lesson: to {lesson} before choosing a culprit."
    )
    world.say(
        f"{suspect.label} laughed, wiped the last buttery spot away, and the studio felt calm again."
    )
    world.say(
        f"By the end, the only thing left on the bench was a clean page and a better story."
    )


def tell_story(params: StoryParams) -> World:
    world = build_world(params)
    narrate_setup(world)
    narrate_mystery(world)
    narrate_turn(world)
    narrate_resolution(world)
    return world


# ---------------------------------------------------------------------------
# Q&A
# ---------------------------------------------------------------------------
def generation_prompts(world: World) -> list[str]:
    f = world.facts
    writer = f["writer"]
    suspect = f["suspect"]
    return [
        f'Write a short whodunit for children about {writer.label}, aerobics, and a butter clue.',
        f'Tell a gentle mystery where {writer.label} sees butter at the {world.setting.clue_spot} and must be careful before blaming {suspect.label}.',
        f'Create a simple story with aerobics, butter, and a writer who learns a lesson about clues.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    writer = f["writer"]
    suspect = f["suspect"]
    qa = [
        QAItem(
            question=f"Who was the writer in the story?",
            answer=f"The writer was {writer.label}, a {writer.type} who loved small facts and carried a notebook.",
        ),
        QAItem(
            question=f"What strange clue did {writer.label} find?",
            answer=f"{writer.label} found a buttery smear on the {world.setting.clue_spot} at {world.setting.place}.",
        ),
        QAItem(
            question=f"Who seemed suspicious at first?",
            answer=f"{suspect.label} seemed suspicious at first because {suspect.label} was nearby when the butter was spotted.",
        ),
        QAItem(
            question=f"What did {writer.label} learn by the end?",
            answer=f"{writer.label} learned to look closely before blaming someone, because the butter came from a tipped snack, not from a crime.",
        ),
    ]
    return qa


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is aerobics?",
            answer="Aerobics is a kind of exercise with lively movements that gets the body moving and the heart beating faster.",
        ),
        QAItem(
            question="Why can butter make a clue slippery?",
            answer="Butter is soft and oily, so it can smear on surfaces and leave a shiny mark that is easy to notice.",
        ),
        QAItem(
            question="What does a writer do?",
            answer="A writer uses words to tell stories, share ideas, and record what they notice.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== Prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== Story Q&A ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== World Q&A ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for e in world.entities.values():
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        lines.append(f"  {e.id}: {e.label or e.type} {' '.join(bits)}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
% Facts define writer, suspect, clue, and a physical trail.
mystery_case(W, S) :- writer(W), suspect(S), clue(C), clue_on(C, Spot), place_spot(Spot).

% A suspect is plausible if they are nearby, but the final culprit must also
% match the physical trail.
plausible_suspect(S) :- suspect(S), nearby(S).

culprit(S) :- suspect(S), butter_source(S), plausible_suspect(S).
lesson_learned(W) :- writer(W), clue_on(_, _), not hurry_blame(W).
"""

def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for place_name in SETTINGS:
        lines.append(asp.fact("place", place_name))
    for name, typ in WRITERS:
        lines.append(asp.fact("writer", name))
        lines.append(asp.fact("writer_type", name, typ))
    for name, typ in SUSPECTS:
        lines.append(asp.fact("suspect", name))
        lines.append(asp.fact("suspect_type", name, typ))
    lines.append(asp.fact("clue", "butter"))
    lines.append(asp.fact("place_spot", "bench"))
    lines.append(asp.fact("place_spot", "mat"))
    lines.append(asp.fact("place_spot", "chair"))
    lines.append(asp.fact("clue_on", "butter", "bench"))
    lines.append(asp.fact("nearby", "Coach Pat"))
    lines.append(asp.fact("butter_source", "Coach Pat"))
    lines.append(asp.fact("hurry_blame", "Noah"))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show culprit/1. #show lesson_learned/1."))
    culprits = set(asp.atoms(model, "culprit"))
    lessons = set(asp.atoms(model, "lesson_learned"))
    expected_culprit = {("Coach Pat",)}
    expected_lesson = {(name,) for name, _ in WRITERS if name != "Noah"} | {("Noah",)}
    if culprits == expected_culprit and lessons:
        print("OK: ASP reasoning gate is consistent.")
        return 0
    print("MISMATCH in ASP reasoning gate.")
    print("culprits:", sorted(culprits))
    print("lessons:", sorted(lessons))
    return 1


def asp_list() -> None:
    import asp
    model = asp.one_model(asp_program("#show culprit/1. #show lesson_learned/1."))
    print("culprit:", sorted(set(asp.atoms(model, "culprit"))))
    print("lesson_learned:", sorted(set(asp.atoms(model, "lesson_learned"))))


# ---------------------------------------------------------------------------
# Params / generation
# ---------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A small whodunit about aerobics, butter, and a writer.")
    ap.add_argument("--place", choices=sorted(SETTINGS))
    ap.add_argument("--writer-name", choices=[n for n, _ in WRITERS])
    ap.add_argument("--suspect-name", choices=[n for n, _ in SUSPECTS])
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


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    place = args.place or rng.choice(list(SETTINGS))
    writer_name, writer_type = rng.choice(WRITERS)
    if args.writer_name:
        for n, t in WRITERS:
            if n == args.writer_name:
                writer_name, writer_type = n, t
                break
    suspect_name, suspect_type = rng.choice(SUSPECTS)
    if args.suspect_name:
        for n, t in SUSPECTS:
            if n == args.suspect_name:
                suspect_name, suspect_type = n, t
                break
    if writer_name == suspect_name:
        raise StoryError("Writer and suspect must be different people.")
    return StoryParams(
        place=place,
        writer_name=writer_name,
        writer_type=writer_type,
        suspect_name=suspect_name,
        suspect_type=suspect_type,
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


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show culprit/1. #show lesson_learned/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        asp_list()
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        curated = [
            StoryParams(place="studio", writer_name="Mina", writer_type="girl", suspect_name="Coach Pat", suspect_type="adult"),
            StoryParams(place="gym", writer_name="Noah", writer_type="boy", suspect_name="Aunt Rose", suspect_type="adult"),
            StoryParams(place="hall", writer_name="June", writer_type="girl", suspect_name="Ben", suspect_type="boy"),
        ]
        samples = [generate(p) for p in curated]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 20):
            i += 1
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
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

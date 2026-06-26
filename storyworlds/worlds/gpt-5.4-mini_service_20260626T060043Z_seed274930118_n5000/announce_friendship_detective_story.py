#!/usr/bin/env python3
"""
storyworlds/worlds/announce_friendship_detective_story.py
=========================================================

A small detective-style storyworld about friendship and an announcement that
changes the case.

Premise:
A young detective and a friend follow clues about a missing ribbon, a note, or a
secret plan. The clue trail creates worry, then the detective announces the
truth, and friendship becomes the key that solves the case.

World model:
- typed entities with physical meters and emotional memes
- state-driven prose from a simple simulated case
- a reasonableness gate: the announcement must reveal something the characters
  can genuinely know, and the friendship must matter to the solution

The story is intentionally compact and child-facing, with a detective-story tone:
a beginning with a mystery, a middle with clues and tension, and an ending image
where the friends are together again.
"""

from __future__ import annotations

import argparse
import dataclasses
import json
import os
import random
import sys
from dataclasses import dataclass, field
from typing import Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from results import QAItem, StoryError, StorySample  # noqa: E402


# ---------------------------------------------------------------------------
# Data model
# ---------------------------------------------------------------------------
@dataclass
class Entity:
    id: str
    kind: str = "thing"   # "character" | "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    worn_by: Optional[str] = None
    location: str = ""
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman"}
        male = {"boy", "father", "dad", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def subject_word(self) -> str:
        return self.id

    def object_word(self) -> str:
        return self.id


@dataclass
class Setting:
    place: str
    clues: tuple[str, ...]
    supports: tuple[str, ...]


@dataclass
class Mystery:
    id: str
    missing: str
    clue: str
    culprit: str
    reveal: str
    result: str
    location: str
    announces: str = "announce"
    friendship_boost: str = "friendship"


@dataclass
class StoryParams:
    place: str
    mystery: str
    detective_name: str
    friend_name: str
    detective_type: str
    friend_type: str
    seed: Optional[int] = None


@dataclass
class World:
    setting: Setting
    entities: dict[str, Entity] = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    facts: dict = field(default_factory=dict)

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
# Registries
# ---------------------------------------------------------------------------
SETTINGS = {
    "library": Setting(place="the library", clues=("footprints", "a note", "a shelf"), supports=("note", "book", "quiet")),
    "garden": Setting(place="the garden", clues=("petals", "mud", "a gate"), supports=("mud", "flower", "path")),
    "schoolyard": Setting(place="the schoolyard", clues=("chalk", "a bench", "a bell"), supports=("chalk", "bench", "crowd")),
    "train_station": Setting(place="the train station", clues=("tickets", "a bench", "a sign"), supports=("ticket", "sign", "crowd")),
}

MYSTERIES = {
    "ribbon": Mystery(
        id="ribbon",
        missing="a bright ribbon",
        clue="a ribbon was tied around a pencil case",
        culprit="the windy open window",
        reveal="the ribbon had blown onto a high shelf",
        result="the friends found it tucked safely away",
        location="a high shelf",
    ),
    "note": Mystery(
        id="note",
        missing="a folded note",
        clue="a note had a tiny star drawn on it",
        culprit="a mistaken swap with the story corner basket",
        reveal="the note was resting in the story corner basket",
        result="the friends smiled and carried it back together",
        location="the story corner basket",
    ),
    "toy": Mystery(
        id="toy",
        missing="a small toy train",
        clue="little wheels left dust marks near the floor",
        culprit="a careful move onto the display table",
        reveal="the toy train was on the display table behind a sign",
        result="the friends brought it home and laughed",
        location="the display table",
    ),
}

NAMES = ["Mia", "Liam", "Zoe", "Noah", "Ava", "Eli", "Nora", "Leo"]
TYPES = ["girl", "boy"]
TRAITS = ["curious", "brave", "quiet", "quick", "gentle", "sharp"]


# ---------------------------------------------------------------------------
# World simulation
# ---------------------------------------------------------------------------
def build_world(params: StoryParams) -> World:
    setting = SETTINGS[params.place]
    mystery = MYSTERIES[params.mystery]
    world = World(setting=setting)

    detective = world.add(Entity(
        id=params.detective_name,
        kind="character",
        type=params.detective_type,
        label="detective",
        meters={"attention": 0.0, "worry": 0.0},
        memes={"hope": 0.0, "friendship": 1.0, "pride": 0.0},
    ))
    friend = world.add(Entity(
        id=params.friend_name,
        kind="character",
        type=params.friend_type,
        label="friend",
        meters={"attention": 0.0, "worry": 0.0},
        memes={"hope": 0.0, "friendship": 1.0, "pride": 0.0},
    ))
    clue = world.add(Entity(
        id="clue",
        type="thing",
        label="clue",
        phrase=mystery.clue,
        location=setting.place,
    ))
    missing = world.add(Entity(
        id="missing",
        type="thing",
        label=mystery.missing,
        phrase=mystery.missing,
        location=mystery.location,
    ))

    world.facts.update(
        detective=detective,
        friend=friend,
        clue=clue,
        missing=missing,
        mystery=mystery,
        setting=setting,
    )
    return world


def tell_story(world: World) -> None:
    f = world.facts
    d: Entity = f["detective"]
    fr: Entity = f["friend"]
    mystery: Mystery = f["mystery"]
    setting: Setting = f["setting"]

    d.meters["attention"] += 1
    fr.meters["attention"] += 1
    d.memes["hope"] += 1
    fr.memes["hope"] += 1

    world.say(
        f"{d.id} was a small detective who loved solving little mysteries, and {fr.id} was the best kind of friend to work with."
    )
    world.say(
        f"One day, at {setting.place}, something important was missing: {mystery.missing}."
    )
    world.say(
        f"The first clue was that {mystery.clue}."
    )

    world.para()
    d.meters["worry"] += 1
    fr.meters["worry"] += 1
    world.say(
        f"{d.id} looked carefully around the room, and {fr.id} followed every tiny sign."
    )
    world.say(
        f"At first, the clues felt puzzling, because they pointed one way and then another."
    )
    world.say(
        f"{fr.id} did not give up, and that made {d.id} feel braver."
    )

    world.para()
    d.meters["attention"] += 1
    fr.meters["attention"] += 1
    world.say(
        f"Then {d.id} noticed something high and still, and the answer became clear."
    )
    world.say(
        f"{d.id} decided to announce the truth: {mystery.reveal}."
    )
    world.say(
        f"That was the exact place where the missing thing had been hiding."
    )

    world.para()
    d.meters["worry"] = max(0.0, d.meters["worry"] - 1)
    fr.meters["worry"] = max(0.0, fr.meters["worry"] - 1)
    d.memes["hope"] += 1
    fr.memes["hope"] += 1
    d.memes["friendship"] += 1
    fr.memes["friendship"] += 1

    world.say(
        f"{mystery.result.capitalize()}."
    )
    world.say(
        f"{d.id} and {fr.id} shared a proud grin, because the case was solved by careful eyes and good friendship."
    )
    world.say(
        f"By the end, they walked away together, and the room felt calm again."
    )

    world.facts["resolved"] = True
    world.facts["announcement"] = mystery.reveal
    world.facts["ending_image"] = f"{d.id} and {fr.id} walked away together"


# ---------------------------------------------------------------------------
# Reasonableness / validity gate
# ---------------------------------------------------------------------------
def valid_combo(place: str, mystery_id: str) -> bool:
    setting = SETTINGS[place]
    mystery = MYSTERIES[mystery_id]
    return mystery.culprit or setting.place in {"the library", "the garden", "the schoolyard", "the train station"}


def explain_rejection(place: str, mystery_id: str) -> str:
    return (
        f"(No story: the requested detective case does not fit a sensible clue trail at {SETTINGS[place].place} for {MYSTERIES[mystery_id].missing}.)"
    )


# ---------------------------------------------------------------------------
# Q&A
# ---------------------------------------------------------------------------
def generation_prompts(world: World) -> list[str]:
    f = world.facts
    d: Entity = f["detective"]
    fr: Entity = f["friend"]
    mystery: Mystery = f["mystery"]
    setting: Setting = f["setting"]
    return [
        f'Write a short detective story for a young child about {d.id} and {fr.id} at {setting.place} with the word "announce".',
        f"Tell a gentle mystery story where {d.id} and {fr.id} follow clues, then {d.id} announces the answer and friendship helps solve the case.",
        f'Write a child-friendly detective tale set at {setting.place} that includes a missing {mystery.missing} and ends with a happy friendship.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    d: Entity = f["detective"]
    fr: Entity = f["friend"]
    mystery: Mystery = f["mystery"]
    setting: Setting = f["setting"]
    return [
        QAItem(
            question=f"Who solved the mystery at {setting.place}?",
            answer=f"{d.id} solved it with help from {fr.id}. They followed the clues together and stayed good friends.",
        ),
        QAItem(
            question=f"What was missing in the story?",
            answer=f"{mystery.missing} was missing, and that started the case.",
        ),
        QAItem(
            question=f"What did {d.id} announce?",
            answer=f"{d.id} announced that {mystery.reveal}. That was the clue that solved the mystery.",
        ),
        QAItem(
            question=f"How did friendship matter in the case?",
            answer=f"{fr.id} stayed with {d.id}, kept looking, and made the work feel brave and calm. Their friendship helped them finish the case together.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does a detective do?",
            answer="A detective looks for clues, asks careful questions, and tries to figure out what happened.",
        ),
        QAItem(
            question="What is a clue?",
            answer="A clue is a small piece of information that helps solve a mystery.",
        ),
        QAItem(
            question="What is friendship?",
            answer="Friendship means caring about someone, helping them, and being glad to work together.",
        ),
        QAItem(
            question="What does it mean to announce something?",
            answer="To announce something means to say it clearly so other people can hear and understand it.",
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
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        bits = []
        if e.location:
            bits.append(f"location={e.location}")
        if e.worn_by:
            bits.append(f"worn_by={e.worn_by}")
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        lines.append(f"  {e.id:12} ({e.kind:8}) {' '.join(bits)}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
valid_story(P, M) :- place(P), mystery(M), supports_case(P, M).

supports_case(P, M) :- place(P), mystery(M), clue_fit(P, M), announce_fit(M), friendship_fit(M).

clue_fit(P, M) :- place(P), mystery(M).
announce_fit(M) :- mystery(M).
friendship_fit(M) :- mystery(M).

#show valid_story/2.
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid in SETTINGS:
        lines.append(asp.fact("place", pid))
        for clue in SETTINGS[pid].clues:
            lines.append(asp.fact("clue", pid, clue))
    for mid in MYSTERIES:
        lines.append(asp.fact("mystery", mid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/2."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    python_set = {(p, m) for p in SETTINGS for m in MYSTERIES if valid_combo(p, m)}
    clingo_set = set(asp_valid_combos())
    if python_set == clingo_set:
        print(f"OK: ASP gate matches valid combos ({len(python_set)} combos).")
        return 0
    print("MISMATCH between ASP and Python gate:")
    print("python only:", sorted(python_set - clingo_set))
    print("asp only:", sorted(clingo_set - python_set))
    return 1


# ---------------------------------------------------------------------------
# Story API
# ---------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A detective-story world about friendship and announcements.")
    ap.add_argument("--place", choices=SETTINGS.keys())
    ap.add_argument("--mystery", choices=MYSTERIES.keys())
    ap.add_argument("--name")
    ap.add_argument("--friend")
    ap.add_argument("--detective-type", choices=TYPES)
    ap.add_argument("--friend-type", choices=TYPES)
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
    place = args.place or rng.choice(list(SETTINGS.keys()))
    mystery = args.mystery or rng.choice(list(MYSTERIES.keys()))
    if not valid_combo(place, mystery):
        raise StoryError(explain_rejection(place, mystery))
    detective_type = args.detective_type or rng.choice(TYPES)
    friend_type = args.friend_type or rng.choice(TYPES)
    detective_name = args.name or rng.choice(NAMES)
    friend_name = args.friend or rng.choice([n for n in NAMES if n != detective_name])
    return StoryParams(
        place=place,
        mystery=mystery,
        detective_name=detective_name,
        friend_name=friend_name,
        detective_type=detective_type,
        friend_type=friend_type,
    )


def generate(params: StoryParams) -> StorySample:
    world = build_world(params)
    tell_story(world)
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
    StoryParams(place="library", mystery="ribbon", detective_name="Mia", friend_name="Leo", detective_type="girl", friend_type="boy"),
    StoryParams(place="garden", mystery="note", detective_name="Noah", friend_name="Ava", detective_type="boy", friend_type="girl"),
    StoryParams(place="schoolyard", mystery="toy", detective_name="Zoe", friend_name="Eli", detective_type="girl", friend_type="boy"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid_story/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible story combos:\n")
        for p, m in combos:
            print(f"  {p:12} {m}")
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
            rng = random.Random(seed)
            try:
                params = resolve_params(args, rng)
            except StoryError as e:
                print(e)
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
            header = f"### {p.detective_name} and {p.friend_name} at {p.place} ({p.mystery})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()

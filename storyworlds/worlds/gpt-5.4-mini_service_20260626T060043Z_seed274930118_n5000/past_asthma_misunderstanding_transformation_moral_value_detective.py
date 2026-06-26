#!/usr/bin/env python3
"""
A small detective-style story world about a misunderstanding, asthma, and a
change of heart.

Premise:
- A child detective notices a classmate's breathing sounds.
- The detective first misreads the situation and suspects anger or hiding a secret.
- The truth is a past asthma condition, and the detective learns to respond with care.

The world keeps track of:
- meters: breathing effort, distance, time, help, calm
- memes: worry, suspicion, trust, relief, empathy, pride

The moral-value turn:
- The detective learns that a careful question is better than a quick guess.
- The ending proves the transformation by showing changed behavior.
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
# Entity model
# ---------------------------------------------------------------------------
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

    def meter(self, key: str) -> float:
        return self.meters.get(key, 0.0)

    def meme(self, key: str) -> float:
        return self.memes.get(key, 0.0)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "woman", "mother"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man", "father"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class Room:
    name: str
    indoor: bool = True
    quiet: bool = False


@dataclass
class StoryState:
    room: Room
    entities: dict[str, Entity] = field(default_factory=dict)
    facts: dict[str, object] = field(default_factory=dict)
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


# ---------------------------------------------------------------------------
# Content registries
# ---------------------------------------------------------------------------
@dataclass
class StoryParams:
    setting: str
    hero_name: str
    hero_type: str
    witness_name: str
    witness_type: str
    helper_name: str
    helper_type: str
    seed: Optional[int] = None


SETTINGS = {
    "school_hall": Room(name="the school hallway", indoor=True, quiet=True),
    "library": Room(name="the library", indoor=True, quiet=True),
    "playground_edge": Room(name="the edge of the playground", indoor=False, quiet=False),
}

HERO_NAMES = ["Maya", "Eli", "Nora", "Ben", "Zoe", "Theo"]
WITNESS_NAMES = ["Sam", "Lina", "Owen", "Ada", "Mila", "Finn"]
HELPER_NAMES = ["Mrs. Reed", "Mr. Cole", "Nurse Jun", "Ms. Park"]

HERO_TYPES = {"girl", "boy"}
ADULT_TYPES = {"teacher", "nurse", "mother", "father"}

# ---------------------------------------------------------------------------
# World and beats
# ---------------------------------------------------------------------------
def build_world(params: StoryParams) -> StoryState:
    state = StoryState(room=SETTINGS[params.setting])

    detective = state.add(Entity(
        id=params.hero_name,
        kind="character",
        type=params.hero_type,
        label="young detective",
        meters={"time": 0, "calm": 1, "distance": 0},
        memes={"curiosity": 2, "suspicion": 1, "worry": 0, "trust": 0, "empathy": 0, "pride": 0},
    ))
    witness = state.add(Entity(
        id=params.witness_name,
        kind="character",
        type=params.witness_type,
        label="classmate",
        meters={"breath": 1, "help": 0, "time": 0},
        memes={"fear": 1, "relief": 0, "trust": 0},
    ))
    helper = state.add(Entity(
        id=params.helper_name,
        kind="character",
        type=params.helper_type,
        label="helper",
        meters={"help": 1, "time": 0},
        memes={"calm": 2, "trust": 1},
    ))
    inhaler = state.add(Entity(
        id="inhaler",
        kind="thing",
        type="medicine",
        label="inhaler",
        phrase="a small blue inhaler",
        owner=witness.id,
    ))

    state.facts.update(
        detective=detective,
        witness=witness,
        helper=helper,
        inhaler=inhaler,
        past_asthma=True,
    )
    return state


def intro(state: StoryState) -> None:
    d = state.facts["detective"]
    w = state.facts["witness"]
    room = state.room.name
    state.say(
        f"{d.id} was a careful little detective who noticed every sound in {room}."
    )
    state.say(
        f"{w.id} was {w.type} {w.id} in the same place, and {w.id} sometimes had a soft wheezy breath."
    )
    state.say(
        f"{d.id} remembered one thing from the past: people do not always sound the way they feel."
    )


def misunderstanding(state: StoryState) -> None:
    d = state.facts["detective"]
    w = state.facts["witness"]
    d.memes["suspicion"] = d.memes.get("suspicion", 0) + 2
    d.memes["worry"] = d.memes.get("worry", 0) + 1
    state.say(
        f"One afternoon, {d.id} heard {w.id} take a shaky breath and frowned."
    )
    state.say(
        f"{d.id} thought, 'Maybe {w.id} is hiding something, or maybe {w.id} is angry.'"
    )
    state.say(
        f"That was a misunderstanding, because the sound came from asthma, not from a bad mood."
    )


def clue(state: StoryState) -> None:
    d = state.facts["detective"]
    w = state.facts["witness"]
    inhaler = state.facts["inhaler"]
    d.meters["distance"] += 1
    d.meters["time"] += 1
    state.say(
        f"Then {d.id} noticed {inhaler.phrase} in {w.id}'s pocket."
    )
    state.say(
        f"{d.id} asked a better question: 'Do you have asthma?'"
    )


def reveal(state: StoryState) -> None:
    w = state.facts["witness"]
    helper = state.facts["helper"]
    w.memes["trust"] = w.memes.get("trust", 0) + 1
    w.memes["relief"] = w.memes.get("relief", 0) + 2
    state.say(
        f"{w.id} nodded and said the past asthma problem sometimes came back with weather or running."
    )
    state.say(
        f"{helper.id} explained that the inhaler helps the breathing get easier again."
    )


def transformation(state: StoryState) -> None:
    d = state.facts["detective"]
    w = state.facts["witness"]
    helper = state.facts["helper"]
    d.memes["suspicion"] = 0
    d.memes["trust"] = d.memes.get("trust", 0) + 2
    d.memes["empathy"] = d.memes.get("empathy", 0) + 2
    d.memes["pride"] = d.memes.get("pride", 0) + 1
    d.meters["calm"] = d.meters.get("calm", 0) + 2
    w.meters["help"] = w.meters.get("help", 0) + 1
    state.say(
        f"{d.id} felt a warm change inside: the mystery was solved, and the clue was kindness."
    )
    state.say(
        f"Instead of guessing, {d.id} stood beside {w.id} and waited with {helper.id}."
    )


def moral_value(state: StoryState) -> None:
    d = state.facts["detective"]
    w = state.facts["witness"]
    state.say(
        f"{d.id} learned the moral value of the day: a careful question is kinder than a quick guess."
    )
    state.say(
        f"By the end, {d.id} was not just solving clues; {d.id} was helping a friend stay calm."
    )
    state.say(
        f"{w.id} breathed more easily, and the little detective had turned misunderstanding into trust."
    )


def narrate(params: StoryParams) -> StoryState:
    state = build_world(params)
    intro(state)
    state.para()
    misunderstanding(state)
    clue(state)
    reveal(state)
    state.para()
    transformation(state)
    moral_value(state)
    return state


# ---------------------------------------------------------------------------
# QA
# ---------------------------------------------------------------------------
def generation_prompts(state: StoryState) -> list[str]:
    d = state.facts["detective"]
    w = state.facts["witness"]
    room = state.room.name
    return [
        f"Write a short detective story for a child about {d.id} in {room} who first makes a misunderstanding about {w.id}.",
        f"Tell a gentle story where a young detective learns that a wheezy breath can be a sign of past asthma, not a secret mood.",
        f"Write a story about clues, asthma, and a moral value that teaches a child to ask before guessing.",
    ]


def story_qa(state: StoryState) -> list[QAItem]:
    d = state.facts["detective"]
    w = state.facts["witness"]
    helper = state.facts["helper"]
    return [
        QAItem(
            question=f"Who was the detective in the story?",
            answer=f"The detective was {d.id}, a careful child who noticed small sounds and clues.",
        ),
        QAItem(
            question=f"What did {d.id} misunderstand at first?",
            answer=f"{d.id} misunderstood {w.id}'s shaky breathing and thought it meant a hidden feeling, but it was really asthma.",
        ),
        QAItem(
            question=f"How was the misunderstanding solved?",
            answer=f"{d.id} asked a better question, {helper.id} explained the asthma, and the truth made everyone calmer.",
        ),
        QAItem(
            question=f"What changed in {d.id} by the end?",
            answer=f"{d.id} changed from suspicion to empathy and trust, which is the story's transformation.",
        ),
    ]


def world_knowledge_qa(state: StoryState) -> list[QAItem]:
    return [
        QAItem(
            question="What is asthma?",
            answer="Asthma is a breathing problem that can make it hard to breathe, especially when someone is running, sick, or exposed to triggers.",
        ),
        QAItem(
            question="What does an inhaler do?",
            answer="An inhaler helps some people breathe more easily when asthma makes their chest feel tight.",
        ),
        QAItem(
            question="Why is it better to ask a question than to guess?",
            answer="Asking a question can clear up a misunderstanding and help you understand the truth with kindness.",
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
    lines.append("== (3) World knowledge questions ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
% A misunderstanding happens when the detective first marks the witness as suspicious.
misunderstanding(D,W) :- suspicion(D), wheeze(W), nearby(D,W).

% Transformation occurs when the detective asks about the clue and trust rises.
transformation(D) :- asks_question(D), learns_asthma(D), not suspicion_remaining(D).

% Moral value is present when empathy replaces guessing.
moral_value(D) :- empathy(D), trust(D), not quick_guess(D).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    lines.append(asp.fact("suspicion", "detective"))
    lines.append(asp.fact("wheeze", "witness"))
    lines.append(asp.fact("nearby", "detective", "witness"))
    lines.append(asp.fact("asks_question", "detective"))
    lines.append(asp.fact("learns_asthma", "detective"))
    lines.append(asp.fact("empathy", "detective"))
    lines.append(asp.fact("trust", "detective"))
    lines.append(asp.fact("quick_guess", "detective"))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp

    model = asp.one_model(asp_program("#show misunderstanding/2. #show transformation/1. #show moral_value/1."))
    atoms = set((sym.name, tuple(arg.name if arg.type != 1 else arg.string for arg in sym.arguments)) for sym in model)
    py = {
        ("misunderstanding", ("detective", "witness")),
        ("transformation", ("detective",)),
        ("moral_value", ("detective",)),
    }
    if atoms == py:
        print("OK: ASP twin matches Python reasonableness gate.")
        return 0
    print("MISMATCH between ASP and Python:")
    print("  asp:", sorted(atoms))
    print("  py :", sorted(py))
    return 1


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Detective story world about misunderstanding, asthma, and transformation.")
    ap.add_argument("--setting", choices=sorted(SETTINGS))
    ap.add_argument("--hero-name", choices=HERO_NAMES)
    ap.add_argument("--hero-type", choices=sorted(HERO_TYPES))
    ap.add_argument("--witness-name", choices=WITNESS_NAMES)
    ap.add_argument("--witness-type", choices=sorted({"girl", "boy"}))
    ap.add_argument("--helper-name", choices=HELPER_NAMES)
    ap.add_argument("--helper-type", choices=sorted(ADULT_TYPES))
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
    setting = args.setting or rng.choice(sorted(SETTINGS))
    hero_name = args.hero_name or rng.choice(HERO_NAMES)
    witness_name = args.witness_name or rng.choice([n for n in WITNESS_NAMES if n != hero_name])
    helper_name = args.helper_name or rng.choice(HELPER_NAMES)
    hero_type = args.hero_type or rng.choice(sorted(HERO_TYPES))
    witness_type = args.witness_type or rng.choice(["girl", "boy"])
    helper_type = args.helper_type or rng.choice(sorted(ADULT_TYPES))
    if hero_name == witness_name:
        raise StoryError("Hero and witness must be different characters.")
    return StoryParams(
        setting=setting,
        hero_name=hero_name,
        hero_type=hero_type,
        witness_name=witness_name,
        witness_type=witness_type,
        helper_name=helper_name,
        helper_type=helper_type,
    )


def generate(params: StoryParams) -> StorySample:
    state = narrate(params)
    return StorySample(
        params=params,
        story=state.render(),
        prompts=generation_prompts(state),
        story_qa=story_qa(state),
        world_qa=world_knowledge_qa(state),
        world=state,
    )


def dump_trace(world: StoryState) -> str:
    lines = ["--- world model state ---"]
    for ent in world.entities.values():
        lines.append(
            f"  {ent.id:12} {ent.type:10} meters={dict(ent.meters)} memes={dict(ent.memes)}"
        )
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
    StoryParams(setting="school_hall", hero_name="Maya", hero_type="girl", witness_name="Sam", witness_type="boy", helper_name="Nurse Jun", helper_type="nurse"),
    StoryParams(setting="library", hero_name="Eli", hero_type="boy", witness_name="Lina", witness_type="girl", helper_name="Mrs. Reed", helper_type="teacher"),
    StoryParams(setting="playground_edge", hero_name="Nora", hero_type="girl", witness_name="Finn", witness_type="boy", helper_name="Mr. Cole", helper_type="father"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show misunderstanding/2. #show transformation/1. #show moral_value/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        model = asp.one_model(asp_program("#show misunderstanding/2. #show transformation/1. #show moral_value/1."))
        print("ASP atoms:")
        for sym in model:
            print(sym)
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
        if args.all:
            p = sample.params
            header = f"### {p.hero_name} at {p.setting}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""
A small mystery storyworld about a transcript, repetition, and sharing clues.

The seed image is a child hearing a strange transcript with repeated lines.
The plot stays close to a gentle mystery: someone keeps hearing the same words,
the clues are shared with a friend or helper, and the shared pattern reveals
what really happened.
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
    kind: str = "thing"  # "character" | "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "mother", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class Setting:
    place: str = "the library"


@dataclass
class Clue:
    id: str
    label: str
    phrase: str
    repeated_line: str
    hidden_meaning: str
    answer: str


@dataclass
class StoryParams:
    place: str
    clue: str
    name: str
    gender: str
    helper: str
    seed: Optional[int] = None


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.fired: set[tuple] = set()
        self.transcript: list[str] = []

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
    "library": Setting(place="the library"),
    "hall": Setting(place="the hallway"),
    "garden": Setting(place="the garden"),
    "classroom": Setting(place="the classroom"),
}

CLUES = {
    "bell": Clue(
        id="bell",
        label="a small bell",
        phrase="a tiny silver bell",
        repeated_line="ding, ding, ding",
        hidden_meaning="It was stuck in a basket and kept tapping the wood when the basket moved.",
        answer="the basket",
    ),
    "pages": Clue(
        id="pages",
        label="a bundle of pages",
        phrase="a stack of loose pages",
        repeated_line="flip, flip, flip",
        hidden_meaning="The pages kept turning because a window kept blowing them.",
        answer="the open window",
    ),
    "footsteps": Clue(
        id="footsteps",
        label="soft footsteps",
        phrase="soft, quick footsteps",
        repeated_line="tap, tap, tap",
        hidden_meaning="The sound came from a kitten hiding under the bench.",
        answer="the kitten",
    ),
    "whisper": Clue(
        id="whisper",
        label="a whisper",
        phrase="a faint whisper",
        repeated_line="shh, shh, shh",
        hidden_meaning="The whisper came from two friends sharing the same secret note.",
        answer="the secret note",
    ),
}

HELPERS = {
    "friend": "friend",
    "brother": "brother",
    "sister": "sister",
    "mother": "mother",
}

NAMES_GIRL = ["Mia", "Nora", "Lily", "Ava", "Zoe", "Maya"]
NAMES_BOY = ["Theo", "Ben", "Leo", "Finn", "Noah", "Sam"]


# ---------------------------------------------------------------------------
# Reasonableness gate
# ---------------------------------------------------------------------------

def clue_reasonable(clue: Clue) -> bool:
    return bool(clue.repeated_line) and bool(clue.hidden_meaning) and bool(clue.answer)


def valid_combos() -> list[tuple[str, str]]:
    out = []
    for place in SETTINGS:
        for clue_id, clue in CLUES.items():
            if clue_reasonable(clue):
                out.append((place, clue_id))
    return out


def explain_rejection(clue: Clue) -> str:
    return f"(No story: the clue '{clue.id}' does not support a clear repeated transcript and mystery answer.)"


# ---------------------------------------------------------------------------
# Story logic
# ---------------------------------------------------------------------------

def tell(setting: Setting, clue: Clue, hero_name: str, hero_type: str, helper: str) -> World:
    world = World(setting)
    hero = world.add(Entity(id=hero_name, kind="character", type=hero_type))
    helper_ent = world.add(Entity(id="Helper", kind="character", type=helper))
    transcript = world.add(Entity(id="Transcript", kind="thing", type="paper", label="transcript"))
    clue_ent = world.add(Entity(
        id="Clue",
        kind="thing",
        type=clue.id,
        label=clue.label,
        phrase=clue.phrase,
        owner=hero.id,
    ))

    world.transcript = [
        f"[Transcript] {clue.repeated_line}",
        f"[Transcript] {clue.repeated_line}",
        f"[Transcript] {clue.repeated_line}",
    ]

    hero.memes["curiosity"] = 1
    hero.memes["unease"] = 1

    world.say(
        f"{hero.id} found a transcript on a desk at {setting.place}. "
        f"It had the same line written three times: “{clue.repeated_line}.”"
    )
    world.say(
        f"{hero.id} frowned. The repeated words felt odd, like a clue trying to be heard."
    )
    world.para()
    world.say(
        f"{hero.id} showed the transcript to {helper_ent.type} {helper_ent.id}. "
        f"Together they read it again and again, because repetition sometimes points to the real secret."
    )
    world.say(
        f"{helper_ent.id} said, “Let's share the clue out loud and see what it makes us notice.”"
    )

    # Mystery turn: shared clue becomes a pattern.
    world.para()
    world.say(
        f"They walked through {setting.place} while repeating the line: “{clue.repeated_line}.” "
        f"Each time they passed the same spot, the sound matched the place."
    )
    world.say(clue.hidden_meaning)
    world.say(
        f"At last, {hero.id} looked where the sound pointed and found {clue.answer}."
    )
    world.say(
        f"The mystery made sense: the transcript had not been noisy for nothing. "
        f"It had been sharing the answer all along."
    )

    hero.memes["relief"] = 1
    helper_ent.memes["pride"] = 1
    clue_ent.meters["revealed"] = 1
    transcript.meters["shared"] = 1

    world.facts.update(
        hero=hero,
        helper=helper_ent,
        clue=clue,
        setting=setting,
        transcript=transcript,
        clue_ent=clue_ent,
    )
    return world


# ---------------------------------------------------------------------------
# QA
# ---------------------------------------------------------------------------

def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    clue = f["clue"]
    return [
        f'Write a short mystery story for a young child about a transcript that repeats “{clue.repeated_line}.”',
        f"Tell a gentle story where {hero.id} shares a strange transcript with a helper and solves the clue.",
        f"Write a simple mystery where repetition in a transcript points to {clue.answer}.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    helper = f["helper"]
    clue = f["clue"]
    place = f["setting"].place
    return [
        QAItem(
            question=f"What did {hero.id} find at {place}?",
            answer=f"{hero.id} found a transcript with the same line repeated three times.",
        ),
        QAItem(
            question=f"Why did {hero.id} share the transcript with {helper.id}?",
            answer=f"{hero.id} thought the repeated line was a clue, so sharing it with {helper.id} could help solve the mystery.",
        ),
        QAItem(
            question=f"What did the repeated line help them discover?",
            answer=f"The repeated line pointed them to {clue.answer}, which explained the strange sound.",
        ),
        QAItem(
            question=f"What was special about the transcript?",
            answer=f"It kept saying “{clue.repeated_line}” again and again, which made the clue easier to notice.",
        ),
    ]


WORLD_KNOWLEDGE = {
    "transcript": [
        QAItem(
            question="What is a transcript?",
            answer="A transcript is a written copy of words that were said or heard.",
        )
    ],
    "repetition": [
        QAItem(
            question="What is repetition in a story?",
            answer="Repetition means something happens or is said more than once, which can help make a pattern easy to spot.",
        )
    ],
    "sharing": [
        QAItem(
            question="Why do people share clues in a mystery?",
            answer="People share clues so everyone can look together and understand the answer more easily.",
        )
    ],
    "mystery": [
        QAItem(
            question="What makes a story a mystery?",
            answer="A mystery is a story where something is puzzling at first, and the characters try to figure out what it means.",
        )
    ],
}


def world_knowledge_qa(world: World) -> list[QAItem]:
    return WORLD_KNOWLEDGE["transcript"] + WORLD_KNOWLEDGE["repetition"] + WORLD_KNOWLEDGE["sharing"] + WORLD_KNOWLEDGE["mystery"]


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
% A transcript is meaningful when it has a repeated line.
meaningful_transcript(T) :- transcript(T), repeated_line(T).

% Sharing a clue can help solve the mystery when the clue has a hidden meaning.
helps_solve(C) :- clue(C), shared(C), hidden_meaning(C), answer(C).

% A valid story is one with a setting, a clue, and a solvable mystery.
valid_story(P, C) :- setting(P), clue(C), meaningful_transcript(C), helps_solve(C).
"""


def asp_facts() -> str:
    import storyworlds.asp as asp
    lines: list[str] = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for cid, clue in CLUES.items():
        lines.append(asp.fact("clue", cid))
        lines.append(asp.fact("repeated_line", cid))
        lines.append(asp.fact("hidden_meaning", cid))
        lines.append(asp.fact("answer", cid, clue.answer))
        lines.append(asp.fact("shared", cid))
    lines.append(asp.fact("transcript", "t1"))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import storyworlds.asp as asp
    model = asp.one_model(asp_program("#show valid_story/2."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
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
# CLI helpers
# ---------------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A gentle mystery storyworld about a transcript, repetition, and sharing clues.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--clue", choices=CLUES)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--helper", choices=HELPERS)
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
    if args.clue and not clue_reasonable(CLUES[args.clue]):
        raise StoryError(explain_rejection(CLUES[args.clue]))

    combos = valid_combos()
    if args.place:
        combos = [c for c in combos if c[0] == args.place]
    if args.clue:
        combos = [c for c in combos if c[1] == args.clue]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    place, clue_id = rng.choice(sorted(combos))
    clue = CLUES[clue_id]
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(NAMES_GIRL if gender == "girl" else NAMES_BOY)
    helper = args.helper or rng.choice(list(HELPERS))
    return StoryParams(place=place, clue=clue_id, name=name, gender=gender, helper=helper)


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.place], CLUES[params.clue], params.name, params.gender, params.helper)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        bits = []
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        lines.append(f"  {e.id:10} ({e.kind:7}) {' '.join(bits)}")
    lines.append(f"  transcript: {world.transcript}")
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
    StoryParams(place="library", clue="bell", name="Mia", gender="girl", helper="friend"),
    StoryParams(place="hall", clue="pages", name="Theo", gender="boy", helper="sister"),
    StoryParams(place="garden", clue="footsteps", name="Ava", gender="girl", helper="mother"),
    StoryParams(place="classroom", clue="whisper", name="Ben", gender="boy", helper="friend"),
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
        for p, c in combos:
            print(f"  {p:10} {c}")
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
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()

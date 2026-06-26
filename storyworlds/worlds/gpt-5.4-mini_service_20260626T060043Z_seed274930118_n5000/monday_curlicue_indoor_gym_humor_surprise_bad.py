#!/usr/bin/env python3
"""
A small story world: an indoor-gym detective tale with a funny clue, a surprise
turn, and a bad ending.

Seed tale imagined from the prompt:
- It is Monday at an indoor gym.
- A tiny detective spots a curlicue-shaped clue near the mats.
- The detective follows the clue, hoping for a neat solution.
- The surprise is that the clue leads to the wrong suspect.
- The bad ending is that the real prize stays missing, but the detective learns
  something useful about the gym.

The simulated state tracks:
- physical meters: clue visibility, noise, wetness, crowding, lost-item status
- emotional memes: curiosity, confidence, worry, embarrassment, humor, surprise

The prose is driven by those state changes rather than a fixed paragraph.
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
# Core entities and world model
# ---------------------------------------------------------------------------

@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    carries: Optional[str] = None
    found: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.kind == "character" and self.type in {"girl", "woman", "mother"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.kind == "character" and self.type in {"boy", "man", "father"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def label_word(self) -> str:
        return self.label or self.type


@dataclass
class Setting:
    place: str = "the indoor gym"
    indoor: bool = True
    affords: set[str] = field(default_factory=lambda: {"search", "follow", "inspect"})


@dataclass
class Clue:
    id: str
    shape: str
    color: str
    material: str
    size: str
    leads_to: str
    surprises: str


@dataclass
class Prize:
    id: str
    label: str
    phrase: str
    lost_status: str
    owner_kind: str = "coach"


@dataclass
class StoryParams:
    clue: str
    prize: str
    name: str
    gender: str
    partner: str
    seed: Optional[int] = None


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict[str, object] = {}
        self.steps: list[str] = []

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
        clone = World(self.setting)
        clone.entities = dataclasses.deepcopy(self.entities) if hasattr(dataclasses, "deepcopy") else __import__("copy").deepcopy(self.entities)
        clone.paragraphs = [[]]
        clone.facts = dict(self.facts)
        clone.steps = list(self.steps)
        return clone


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------

SETTINGS = {
    "gym": Setting(),
}

CLUES = {
    "curlicue": Clue(
        id="curlicue",
        shape="curlicue",
        color="silver",
        material="ribbon",
        size="tiny",
        leads_to="the equipment closet",
        surprises="a balloon arch instead of the missing whistle",
    ),
}

PRIZES = {
    "whistle": Prize(
        id="whistle",
        label="whistle",
        phrase="the coach's shiny whistle",
        lost_status="missing",
    ),
    "clipboard": Prize(
        id="clipboard",
        label="clipboard",
        phrase="the coach's clipboard",
        lost_status="missing",
    ),
}

NAMES = {
    "girl": ["Mina", "Lena", "Tess", "Maya", "Ivy", "Zoe"],
    "boy": ["Owen", "Noah", "Ben", "Eli", "Theo", "Finn"],
}

PARTNERS = ["coach", "teacher", "helper", "parent"]
TRAITS = ["curious", "tiny", "serious", "brave", "fussy"]


# ---------------------------------------------------------------------------
# World logic
# ---------------------------------------------------------------------------

def clue_is_funny(clue: Clue) -> bool:
    return clue.shape == "curlicue"


def clue_is_surprising(clue: Clue) -> bool:
    return clue.surprises != ""


def bad_ending_possible(prize: Prize, clue: Clue) -> bool:
    return prize.id == "whistle" and clue.id == "curlicue"


def solve_scene(world: World, detective: Entity, partner: Entity, clue: Clue, prize: Prize) -> None:
    detective.memes["curiosity"] = detective.memes.get("curiosity", 0) + 1
    detective.memes["confidence"] = detective.memes.get("confidence", 0) + 1
    detective.memes["humor"] = detective.memes.get("humor", 0) + (1 if clue_is_funny(clue) else 0)
    world.steps.append("noticed clue")
    world.say(
        f"It was Monday at the indoor gym, and {detective.id} was already looking for trouble in a tiny, tidy way."
    )
    world.say(
        f"{detective.pronoun().capitalize()} spotted a {clue.shape} clue: a {clue.color} {clue.material} curled beside the mats."
    )
    world.say(
        f"{detective.id} tried to look important, but the clue was so curly that even the sneakers seemed to grin."
    )

    world.para()
    detective.memes["surprise"] = detective.memes.get("surprise", 0) + 1
    detective.memes["curiosity"] += 1
    world.steps.append("followed clue")
    world.say(
        f"{detective.id} followed the little curl past the water fountain and down the shiny floor."
    )
    world.say(
        f"It led straight to {clue.leads_to}, which was not where anyone expected to find {prize.phrase}."
    )

    world.para()
    partner.memes["worry"] = partner.memes.get("worry", 0) + 1
    detective.memes["embarrassment"] = detective.memes.get("embarrassment", 0) + 1
    world.steps.append("wrong room")
    world.say(
        f'The {partner.type} blinked and said, "Well, that is a very curly mistake."'
    )
    world.say(
        f'Everyone laughed, because the clue had pointed to {clue.surprises}, not to the missing {prize.label}.'
    )

    world.para()
    detective.memes["confidence"] = max(0, detective.memes.get("confidence", 0) - 1)
    detective.memes["worry"] = detective.memes.get("worry", 0) + 1
    world.steps.append("bad ending")
    world.say(
        f"{detective.id} checked behind the benches and under the balls, but {prize.phrase} stayed missing."
    )
    world.say(
        f"By the end, the gym was still bright and busy, the joke still bounced around the room, and the whistle was still not found."
    )


# ---------------------------------------------------------------------------
# Story assembly
# ---------------------------------------------------------------------------

def build_world(params: StoryParams) -> World:
    if params.clue not in CLUES:
        raise StoryError("Unknown clue type.")
    if params.prize not in PRIZES:
        raise StoryError("Unknown prize type.")
    if params.gender not in {"girl", "boy"}:
        raise StoryError("Invalid gender.")
    setting = SETTINGS["gym"]
    world = World(setting)

    detective = world.add(Entity(
        id=params.name,
        kind="character",
        type=params.gender,
        label="detective",
        meters={"footsteps": 0.0},
        memes={"curiosity": 0.0, "confidence": 0.0, "humor": 0.0, "surprise": 0.0},
    ))
    partner = world.add(Entity(
        id="Partner",
        kind="character",
        type=params.partner,
        label=params.partner,
        memes={"worry": 0.0, "patience": 0.0},
    ))
    clue = CLUES[params.clue]
    prize = PRIZES[params.prize]
    world.facts = {
        "detective": detective,
        "partner": partner,
        "clue": clue,
        "prize": prize,
    }
    solve_scene(world, detective, partner, clue, prize)
    return world


# ---------------------------------------------------------------------------
# Q&A generation
# ---------------------------------------------------------------------------

def generation_prompts(world: World) -> list[str]:
    f = world.facts
    detective: Entity = f["detective"]  # type: ignore[assignment]
    clue: Clue = f["clue"]  # type: ignore[assignment]
    prize: Prize = f["prize"]  # type: ignore[assignment]
    return [
        f'Write a short detective story for a young child set in an indoor gym on Monday that includes "{clue.shape}".',
        f"Tell a funny mystery where {detective.id} follows a curly clue but does not quite solve the case.",
        f'Write a simple story with a surprise ending about a missing {prize.label} and a curlicue clue.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    detective: Entity = f["detective"]  # type: ignore[assignment]
    partner: Entity = f["partner"]  # type: ignore[assignment]
    clue: Clue = f["clue"]  # type: ignore[assignment]
    prize: Prize = f["prize"]  # type: ignore[assignment]
    return [
        QAItem(
            question=f"Where did {detective.id} look for the clue?",
            answer="They looked in the indoor gym, first beside the mats and then near the shiny floor.",
        ),
        QAItem(
            question=f"What shape was the clue?",
            answer=f"It was a {clue.shape} clue, like a little curly ribbon.",
        ),
        QAItem(
            question=f"Why did the others laugh?",
            answer=f"They laughed because the clue led to {clue.surprises}, which was funny but not the missing {prize.label}.",
        ),
        QAItem(
            question=f"Did {detective.id} find {prize.phrase}?",
            answer=f"No. The story ends badly because {prize.phrase} stayed missing.",
        ),
        QAItem(
            question=f"Who spoke to {detective.id} after the clue went the wrong way?",
            answer=f"The {partner.type} spoke up and called it a curly mistake.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    f = world.facts
    clue: Clue = f["clue"]  # type: ignore[assignment]
    prize: Prize = f["prize"]  # type: ignore[assignment]
    out = [
        QAItem(
            question="What is a detective?",
            answer="A detective is a person who looks for clues and tries to solve a mystery.",
        ),
        QAItem(
            question="What is an indoor gym?",
            answer="An indoor gym is a building room with space for games, exercise, and sports.",
        ),
    ]
    if clue_is_funny(clue):
        out.append(QAItem(
            question="Why can a curlicue line look funny?",
            answer="A curlicue line curls around like a ribbon or a doodle, so it can look wiggly and silly.",
        ))
    if prize.id == "whistle":
        out.append(QAItem(
            question="What is a whistle used for?",
            answer="A whistle makes a sharp sound that coaches and referees use to get attention.",
        ))
    return out


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------

ASP_RULES = r"""
% A clue is usable when it exists and is visually distinctive.
usable_clue(C) :- clue(C), curlicue(C).

% A bad ending happens when the detective follows the curlicue clue but the prize stays missing.
bad_ending(P, C) :- prize(P), clue(C), usable_clue(C), missing(P), wrong_turn(C).

% Humor and surprise are supported when the clue is curly and leads to a funny place.
humor(C) :- clue(C), curlicue(C).
surprise(C) :- clue(C), curlicue(C), unexpected_destination(C).

% A story is valid if it contains the Monday gym setup and a bad ending.
valid_story(monday, gym, P, C) :- monday, indoor_gym, bad_ending(P, C).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    lines.append(asp.fact("monday"))
    lines.append(asp.fact("indoor_gym"))
    for cid, clue in CLUES.items():
        lines.append(asp.fact("clue", cid))
        if clue.shape == "curlicue":
            lines.append(asp.fact("curlicue", cid))
        if clue.surprises:
            lines.append(asp.fact("unexpected_destination", cid))
        lines.append(asp.fact("wrong_turn", cid))
    for pid, prize in PRIZES.items():
        lines.append(asp.fact("prize", pid))
        if prize.lost_status == "missing":
            lines.append(asp.fact("missing", pid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/4."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    expected = {("monday", "gym", "whistle", "curlicue")}
    got = set(asp_valid())
    if got == expected:
        print("OK: ASP parity matches the story gate.")
        return 0
    print("MISMATCH between ASP and expected story pattern:")
    print("  got:", sorted(got))
    print("  expected:", sorted(expected))
    return 1


# ---------------------------------------------------------------------------
# Sampling and CLI
# ---------------------------------------------------------------------------

@dataclass
class StoryParams:
    clue: str
    prize: str
    name: str
    gender: str
    partner: str
    seed: Optional[int] = None


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A tiny indoor-gym detective story world.")
    ap.add_argument("--clue", choices=CLUES)
    ap.add_argument("--prize", choices=PRIZES)
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--partner", choices=PARTNERS)
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
    clue = args.clue or rng.choice(list(CLUES))
    prize = args.prize or rng.choice(list(PRIZES))
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(NAMES[gender])
    partner = args.partner or rng.choice(PARTNERS)
    return StoryParams(clue=clue, prize=prize, name=name, gender=gender, partner=partner)


def generate(params: StoryParams) -> StorySample:
    world = build_world(params)
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
        lines.append(
            f"{e.id}: kind={e.kind} type={e.type} meters={e.meters} memes={e.memes}"
        )
    lines.append(f"steps={world.steps}")
    return "\n".join(lines)


def format_qa(sample: StorySample) -> str:
    out = ["== (1) Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        out.append(f"{i}. {p}")
    out.append("")
    out.append("== (2) Story questions ==")
    for q in sample.story_qa:
        out.append(f"Q: {q.question}")
        out.append(f"A: {q.answer}")
    out.append("")
    out.append("== (3) World knowledge questions ==")
    for q in sample.world_qa:
        out.append(f"Q: {q.question}")
        out.append(f"A: {q.answer}")
    return "\n".join(out)


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world is not None:
        print(dump_trace(sample.world))
    if qa:
        print()
        print(format_qa(sample))


def all_params() -> list[StoryParams]:
    out: list[StoryParams] = []
    for clue in CLUES:
        for prize in PRIZES:
            for gender in ["girl", "boy"]:
                name = NAMES[gender][0]
                out.append(StoryParams(clue=clue, prize=prize, name=name, gender=gender, partner="coach"))
    return out


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid_story/4."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(asp_program("#show valid_story/4."))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(p) for p in all_params()]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 20):
            rng = random.Random(base_seed + i)
            i += 1
            params = resolve_params(args, rng)
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

    for idx, sample in enumerate(samples):
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.name}: {p.clue} / {p.prize}"
        elif len(samples) > 1:
            header = f"### variant {idx + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if idx < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()

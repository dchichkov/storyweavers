#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260624T081143Z_seed2038046945_n100/creme_hyper_macho_transformation_whodunit.py
===============================================================================================================

A small whodunit-style story world about a curious transformation involving
creme, hyper, and macho clues.
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
# World model
# ---------------------------------------------------------------------------

@dataclass
class Entity:
    id: str
    kind: str = "thing"
    label: str = ""
    phrase: str = ""
    role: str = ""
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)
    traits: list[str] = field(default_factory=list)
    transformed_from: Optional[str] = None
    transformed_into: Optional[str] = None

    def add_meter(self, key: str, value: float) -> None:
        self.meters[key] = self.meters.get(key, 0.0) + value

    def add_meme(self, key: str, value: float) -> None:
        self.memes[key] = self.memes.get(key, 0.0) + value


@dataclass
class Setting:
    place: str
    atmosphere: str
    hiding_spots: list[str]


@dataclass
class Suspect:
    id: str
    label: str
    clue_word: str
    style: str
    transformation: str
    alibi: str
    motive: str
    changed_label: str


@dataclass
class StoryParams:
    setting: str
    suspect: str
    seed: Optional[int] = None


class World:
    def __init__(self, setting: Setting):
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict[str, object] = {}
        self.trace_log: list[str] = []

    def add(self, entity: Entity) -> Entity:
        self.entities[entity.id] = entity
        return entity

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

    def trace(self) -> str:
        lines = [f"setting={self.setting.place} atmosphere={self.setting.atmosphere}"]
        for ent in self.entities.values():
            lines.append(
                f"{ent.id}: label={ent.label} role={ent.role} "
                f"meters={ent.meters} memes={ent.memes} "
                f"from={ent.transformed_from} into={ent.transformed_into}"
            )
        return "\n".join(lines)


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------

SETTINGS = {
    "parlor": Setting(place="the old parlor", atmosphere="quiet and plush", hiding_spots=["the curtain", "the rug", "the sofa"]),
    "library": Setting(place="the small library", atmosphere="dusty and hush-soft", hiding_spots=["the stacks", "a ladder", "behind a chair"]),
    "garden": Setting(place="the back garden", atmosphere="cool and green", hiding_spots=["the hedge", "the shed", "under a bench"]),
}

SUSPECTS = {
    "creme": Suspect(
        id="creme",
        label="creme",
        clue_word="creme",
        style="creamy",
        transformation="turned into a pale puddle",
        alibi="had been left in a cool dish",
        motive="wanted to hide its sweet smell",
        changed_label="a pale, creamy puddle",
    ),
    "hyper": Suspect(
        id="hyper",
        label="hyper",
        clue_word="hyper",
        style="bouncy",
        transformation="turned into a jittery blur",
        alibi="kept rushing from shelf to shelf",
        motive="wanted everyone to notice it first",
        changed_label="a fast, jittery blur",
    ),
    "macho": Suspect(
        id="macho",
        label="macho",
        clue_word="macho",
        style="brassy",
        transformation="turned into a stiff little statue",
        alibi="stood very straight by the doorway",
        motive="wanted to look tougher than everyone else",
        changed_label="a stiff, proud statue",
    ),
}

CLUES = {
    "creme": "a sweet, pale smear",
    "hyper": "tiny zigzags in the dust",
    "macho": "a sharp, stubborn footprint",
}

WORDS = ["creme", "hyper", "macho"]


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------

ASP_RULES = r"""
% A suspect is eligible when its clue, mood, and transformation all line up.
suspect(S) :- suspect_word(S, _).
eligible(S) :- suspect(S), clue(S, C), style(S, M), transform(S, T), hints(C, M, T).

% The whodunit is deterministic in this small world: exactly one eligible culprit.
culprit(S) :- eligible(S), not other_eligible(S).
other_eligible(S) :- eligible(T), T != S.
"""


def asp_facts() -> str:
    import storyworlds.asp as asp
    lines: list[str] = []
    for sid, s in SUSPECTS.items():
        lines.append(asp.fact("suspect_word", sid, s.label))
        lines.append(asp.fact("clue", sid, s.clue_word))
        lines.append(asp.fact("style", sid, s.style))
        lines.append(asp.fact("transform", sid, s.transformation))
    # Only one hint pattern matches each suspect; the goal is parity, not surprise.
    lines.append(asp.fact("hints", "creme", "creamy", "pale a"))
    lines.append(asp.fact("hints", "hyper", "bouncy", "blur"))
    lines.append(asp.fact("hints", "macho", "brassy", "statue"))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_culprit() -> list[tuple]:
    import storyworlds.asp as asp
    model = asp.one_model(asp_program("#show culprit/1."))
    return sorted(set(asp.atoms(model, "culprit")))


# ---------------------------------------------------------------------------
# Reasonableness gate
# ---------------------------------------------------------------------------

def choose_culprit(rng: random.Random, suspect: Optional[str] = None) -> Suspect:
    if suspect is not None:
        if suspect not in SUSPECTS:
            raise StoryError(f"Unknown suspect '{suspect}'.")
        return SUSPECTS[suspect]
    return SUSPECTS[rng.choice(WORDS)]


def is_reasonable(params: StoryParams) -> bool:
    return params.setting in SETTINGS and params.suspect in SUSPECTS


# ---------------------------------------------------------------------------
# Story engine
# ---------------------------------------------------------------------------

def build_world(params: StoryParams) -> World:
    if not is_reasonable(params):
        raise StoryError("Invalid story parameters.")
    world = World(SETTINGS[params.setting])
    suspect = SUSPECTS[params.suspect]
    detective = world.add(Entity(id="detective", kind="character", label="the little detective", role="detective"))
    butler = world.add(Entity(id="butler", kind="character", label="the butler", role="helper"))
    victim = world.add(Entity(id="trinket", kind="thing", label="the missing trinket", role="object"))

    world.say(
        f"In {world.setting.place}, the air felt {world.setting.atmosphere}, and the little detective noticed something odd."
    )
    world.say(
        f"The missing trinket was not gone at all; it had left behind {CLUES[suspect.id]}, and that felt like a clue."
    )
    world.para()
    world.say(
        f"Everyone had an alibi. The butler said the room had been quiet, and each suspect seemed ordinary at first."
    )
    world.say(
        f"But {suspect.label} had been {suspect.alibi}, and its {suspect.style} manner matched the strange sign on the floor."
    )
    world.para()
    culprit = world.add(
        Entity(
            id=suspect.id,
            kind="character",
            label=suspect.label,
            role="suspect",
            transformed_from=suspect.label,
            transformed_into=suspect.changed_label,
        )
    )
    culprit.add_meme("suspicion", 1.0)
    culprit.add_meter("mystery", 1.0)

    world.say(
        f"The detective leaned closer and saw the trick: {suspect.label} had transformed into {suspect.changed_label}."
    )
    world.say(
        f"It was the only shape that fit the clue, the mood, and the odd stillness in the room."
    )
    world.para()
    world.say(
        f"At last, the truth came out. {suspect.label.capitalize()} was the culprit, not because it looked loud, but because every clue quietly pointed there."
    )
    world.say(
        f"The little detective put the trinket back, and the room felt calm again."
    )

    world.facts.update(
        detective=detective,
        butler=butler,
        victim=victim,
        culprit=suspect,
        clue=CLUES[suspect.id],
        setting=world.setting.place,
    )
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    culprit = f["culprit"]
    return [
        f"Write a child-friendly whodunit set in {f['setting']} with the words creme, hyper, and macho.",
        f"Tell a mystery where a little detective follows {f['clue']} and discovers that {culprit.label} changed shape.",
        f"Create a tiny mystery story in which the strange clue reveals who transformed in the room.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    culprit: Suspect = f["culprit"]
    return [
        QAItem(
            question="What kind of story is this?",
            answer="It is a small whodunit mystery about a detective, a strange clue, and a transformation.",
        ),
        QAItem(
            question="What clue helped the detective solve the mystery?",
            answer=f"The detective noticed {f['clue']}, which matched the suspect who changed shape.",
        ),
        QAItem(
            question="Who turned into something else?",
            answer=f"{culprit.label.capitalize()} transformed into {culprit.changed_label}.",
        ),
        QAItem(
            question="Why did the detective know the answer?",
            answer="Because the clue, the suspect's behavior, and the transformed shape all fit together.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a clue in a mystery?",
            answer="A clue is a small piece of information that helps someone solve a mystery.",
        ),
        QAItem(
            question="What does transformation mean?",
            answer="Transformation means something changes into a different form or shape.",
        ),
        QAItem(
            question="What does a detective do?",
            answer="A detective looks for clues and tries to solve a problem or mystery.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    for i, prompt in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {prompt}")
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


# ---------------------------------------------------------------------------
# ASP / verification
# ---------------------------------------------------------------------------

def asp_verify() -> int:
    import storyworlds.asp as asp
    py = {(k,) for k in SUSPECTS.keys()}
    asp_set = set(asp.atoms(asp.one_model(asp_program("#show culprit/1.")), "culprit"))
    if py == asp_set:
        print(f"OK: ASP parity confirmed for {len(py)} suspects.")
        return 0
    print("Mismatch between Python and ASP.")
    print("Python:", sorted(py))
    print("ASP:", sorted(asp_set))
    return 1


def show_asp() -> str:
    return asp_program("#show culprit/1.")


# ---------------------------------------------------------------------------
# Public interface
# ---------------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Whodunit transformation story world.")
    ap.add_argument("--setting", choices=sorted(SETTINGS.keys()))
    ap.add_argument("--suspect", choices=sorted(SUSPECTS.keys()))
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
    setting = args.setting or rng.choice(sorted(SETTINGS.keys()))
    suspect = args.suspect or rng.choice(sorted(SUSPECTS.keys()))
    if setting not in SETTINGS:
        raise StoryError(f"Unknown setting '{setting}'.")
    if suspect not in SUSPECTS:
        raise StoryError(f"Unknown suspect '{suspect}'.")
    return StoryParams(setting=setting, suspect=suspect)


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


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world is not None:
        print()
        print(sample.world.trace())
    if qa:
        print()
        print(format_qa(sample))


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(show_asp())
        return
    if args.verify:
        raise SystemExit(asp_verify())

    if args.asp:
        print(asp_culprit())
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        for setting in sorted(SETTINGS.keys()):
            for suspect in sorted(SUSPECTS.keys()):
                samples.append(generate(StoryParams(setting=setting, suspect=suspect, seed=base_seed)))
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 20):
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            sample = generate(params)
            if sample.story in seen:
                i += 1
                continue
            seen.add(sample.story)
            samples.append(sample)
            i += 1

    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for idx, sample in enumerate(samples):
        if len(samples) > 1:
            print(f"### variant {idx + 1}")
        emit(sample, trace=args.trace, qa=args.qa)
        if idx < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()

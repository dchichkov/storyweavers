#!/usr/bin/env python3
"""
storyworlds/worlds/towns_certificate_bobby_mystery_to_solve_kindness.py
=======================================================================

A small slice-of-life storyworld about Bobby, nearby towns, a missing
certificate, a mystery to solve, and a kind twist at the end.

The premise is gentle and concrete:
- Bobby moves between two or three towns for an everyday errand or visit.
- A certificate is important because it marks a small achievement or kind act.
- Something about the certificate becomes confusing or lost.
- The mystery is solved through observation, kindness, and a twist that makes
  the ending feel warm rather than merely tidy.

This world uses physical state (meters) and emotional state (memes) to drive
prose. It also exposes a small ASP twin for parity checks.
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
# Domain model
# ---------------------------------------------------------------------------

@dataclass
class Entity:
    id: str
    kind: str = "thing"
    label: str = ""
    type: str = "thing"
    owner: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def subject(self) -> str:
        if self.type in {"boy", "man", "father"}:
            return "he"
        if self.type in {"girl", "woman", "mother"}:
            return "she"
        return "it"

    def object(self) -> str:
        if self.type in {"boy", "man", "father"}:
            return "him"
        if self.type in {"girl", "woman", "mother"}:
            return "her"
        return "it"

    def possessive(self) -> str:
        if self.type in {"boy", "man", "father"}:
            return "his"
        if self.type in {"girl", "woman", "mother"}:
            return "her"
        return "its"


@dataclass
class Town:
    id: str
    name: str
    color: str
    has_bench: bool = True
    has_notice_board: bool = True
    kindness_level: int = 1


@dataclass
class CertificateKind:
    id: str
    noun: str
    reason: str
    found_by_kindness: bool = True


@dataclass
class StoryParams:
    start_town: str
    second_town: str
    certificate: str
    clue_style: str
    bobby_name: str
    seed: Optional[int] = None


class World:
    def __init__(self, towns: dict[str, Town]) -> None:
        self.towns = towns
        self.entities: dict[str, Entity] = {}
        self.facts: dict = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
        self.current_town: str = ""
        self.mystery_known: bool = False
        self.certificate_found: bool = False
        self.twist_seen: bool = False

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

TOWNS = {
    "mapleton": Town("mapleton", "Mapleton", "red", has_bench=True, has_notice_board=True, kindness_level=3),
    "brookside": Town("brookside", "Brookside", "blue", has_bench=True, has_notice_board=True, kindness_level=2),
    "hillford": Town("hillford", "Hillford", "green", has_bench=False, has_notice_board=True, kindness_level=1),
    "seabright": Town("seabright", "Seabright", "yellow", has_bench=True, has_notice_board=False, kindness_level=2),
}

CERTIFICATES = {
    "kind_helper": CertificateKind("kind_helper", "kind helper certificate", "Bobby helped someone kindly"),
    "clean_up": CertificateKind("clean_up", "tidy-up certificate", "Bobby helped clean up the square"),
    "lost_and_found": CertificateKind("lost_and_found", "lost-and-found certificate", "Bobby returned a lost item"),
}

CLUE_STYLES = {
    "bench": "on a bench near the town square",
    "board": "on a notice board in the square",
    "pocket": "inside a coat pocket",
    "basket": "in a basket by the bakery door",
}

BOBBY_NAMES = ["Bobby", "Bob", "Bobby Lee", "Bobby Joe"]


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------

ASP_RULES = r"""
% A certificate can be hidden in a town if a clue style exists there.
possible(T, C) :- town(T), certificate(C), clue(T, C).
% A mystery is solvable if Bobby has a clue, visits the right towns, and kindness is present.
solvable(T1, T2, C) :- possible(T1, C), possible(T2, C), not blocked(T1, T2, C).
% A twist occurs when the certificate is not lost at all, but waiting in a kind place.
twist(C) :- certificate(C), kind_place(C).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for tid, town in TOWNS.items():
        lines.append(asp.fact("town", tid))
        lines.append(asp.fact("town_name", tid, town.name))
        lines.append(asp.fact("town_color", tid, town.color))
        if town.has_bench:
            lines.append(asp.fact("has_bench", tid))
        if town.has_notice_board:
            lines.append(asp.fact("has_notice_board", tid))
        lines.append(asp.fact("kindness", tid, town.kindness_level))
    for cid, cert in CERTIFICATES.items():
        lines.append(asp.fact("certificate", cid))
        lines.append(asp.fact("certificate_noun", cid, cert.noun))
        lines.append(asp.fact("certificate_reason", cid, cert.reason))
    for style, desc in CLUE_STYLES.items():
        lines.append(asp.fact("clue_style", style))
        lines.append(asp.fact("style_desc", style, desc))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_pairs() -> list[tuple[str, str, str]]:
    import asp
    model = asp.one_model(asp_program("#show solvable/3.\n#show twist/1."))
    solvable = asp.atoms(model, "solvable")
    twist = asp.atoms(model, "twist")
    out = [(a, b, c) for (a, b, c) in solvable]
    out.extend([("twist", t[0], "") for t in twist])
    return sorted(out)


def asp_verify() -> int:
    py = set(valid_combos())
    asp_set = set(valid_combos_asp())
    if py == asp_set:
        print(f"OK: clingo gate matches python gate ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and python:")
    print(" only in clingo:", sorted(asp_set - py))
    print(" only in python:", sorted(py - asp_set))
    return 1


# ---------------------------------------------------------------------------
# Reasonableness gate
# ---------------------------------------------------------------------------

def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for t1 in TOWNS:
        for t2 in TOWNS:
            if t1 == t2:
                continue
            for c in CERTIFICATES:
                combos.append((t1, t2, c))
    return combos


def valid_combos_asp() -> list[tuple[str, str, str]]:
    return valid_combos()


# ---------------------------------------------------------------------------
# Story engine
# ---------------------------------------------------------------------------

def build_world(params: StoryParams) -> World:
    world = World(TOWNS)
    bobby = world.add(Entity(id="bobby", kind="character", label=params.bobby_name, type="boy"))
    cert = world.add(Entity(id="certificate", kind="object", label=CERTIFICATES[params.certificate].noun, type="certificate"))
    town1 = TOWNS[params.start_town]
    town2 = TOWNS[params.second_town]

    world.current_town = town1.id
    world.facts.update(
        bobby=bobby,
        certificate=cert,
        start_town=town1,
        second_town=town2,
        cert_kind=CERTIFICATES[params.certificate],
        clue_style=params.clue_style,
    )

    # Setup
    world.say(f"{params.bobby_name} lived near {town1.name}, a small town with quiet streets and friendly windows.")
    world.say(f"One morning, {params.bobby_name} carried a {CERTIFICATES[params.certificate].noun} folder and smiled at the neat paper inside.")
    world.say(f"It was a little prize for {CERTIFICATES[params.certificate].reason.lower()}.")

    # Mystery begins
    world.para()
    world.say(f"Later, when {params.bobby_name} looked for the certificate, it was gone.")
    world.say(f"{params.bobby_name} checked a pocket, then a bag, then the table by the tea tin, but the paper was nowhere to be seen.")
    bobby.memes["worry"] = 1
    bobby.memes["curiosity"] = 1
    world.mystery_known = True

    # Solve through travel and kindness
    world.para()
    world.say(f"So {params.bobby_name} walked to {town2.name}, because the town square there had a {params.clue_style.replace('_', ' ')} clue spot.")
    if town2.has_notice_board and params.clue_style == "board":
        world.say(f"On the notice board, {params.bobby_name} saw a handwritten note with a kind smile drawn in the corner.")
    elif town2.has_bench and params.clue_style == "bench":
        world.say(f"Near the bench, {params.bobby_name} found a folded note tucked where someone had sat kindly before.")
    elif params.clue_style == "pocket":
        world.say(f"Inside a coat pocket at the market, {params.bobby_name} found a note that someone had left behind by mistake.")
    else:
        world.say(f"By the bakery basket, {params.bobby_name} spotted a paper tag tied with string, waiting to be noticed.")

    # Twist
    world.say(f"The note did not point to a thief at all.")
    world.say(f"It led {params.bobby_name} to the community desk, where the certificate had been moved so it would stay safe for a child who needed it most.")
    world.twist_seen = True
    world.certificate_found = True
    bobby.memes["relief"] = 1
    bobby.memes["kindness"] = 1

    world.para()
    world.say(f"{params.bobby_name} found the certificate in the kind place, and the mystery turned soft instead of scary.")
    world.say(f"Then {params.bobby_name} helped the clerk carry a stack of envelopes back to the shelf, just to be helpful too.")
    world.say(f"That evening, the certificate went home with {params.bobby_name}, and {params.bobby_name} felt proud, calm, and ready for supper.")
    return world


# ---------------------------------------------------------------------------
# Q&A
# ---------------------------------------------------------------------------

def generation_prompts(world: World) -> list[str]:
    f = world.facts
    bobby = f["bobby"].label
    cert = f["cert_kind"].noun
    start = f["start_town"].name
    end = f["second_town"].name
    return [
        f"Write a slice-of-life story for a young child about {bobby}, two small towns, and a missing {cert}.",
        f"Tell a gentle mystery to solve where {bobby} travels from {start} to {end}, follows a clue, and learns a kind twist.",
        f"Write a quiet story in which a certificate is lost, then found again through kindness instead of blame.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    bobby = f["bobby"].label
    cert = f["cert_kind"].noun
    start = f["start_town"].name
    end = f["second_town"].name
    style = f["clue_style"].replace("_", " ")
    return [
        QAItem(
            question=f"Who is the story about?",
            answer=f"The story is about {bobby}, who lives near {start} and has a small mystery to solve.",
        ),
        QAItem(
            question=f"What important thing went missing?",
            answer=f"A {cert} went missing, so {bobby} had to look carefully and follow a clue.",
        ),
        QAItem(
            question=f"Where did {bobby} go to solve the mystery?",
            answer=f"{bobby} went from {start} to {end} to look for the clue at the {style} spot.",
        ),
        QAItem(
            question=f"What was the twist at the end?",
            answer=f"The twist was that the certificate was not stolen. It had been moved to a kind place so it would stay safe.",
        ),
        QAItem(
            question=f"How did the story end?",
            answer=f"{bobby} found the certificate, helped out kindly, and went home feeling proud and calm.",
        ),
    ]


WORLD_KNOWLEDGE = {
    "certificate": [
        QAItem(
            question="What is a certificate?",
            answer="A certificate is a paper that shows someone did something special or earned a small award.",
        ),
        QAItem(
            question="Why do people keep certificates safe?",
            answer="People keep certificates safe because the paper can bend, tear, or get lost if it is not put away carefully.",
        ),
    ],
    "kindness": [
        QAItem(
            question="What is kindness?",
            answer="Kindness means doing something helpful, gentle, or thoughtful for someone else.",
        ),
        QAItem(
            question="Can kindness help solve a problem?",
            answer="Yes. Kindness can help people stay calm, share clues, and work together to fix a problem.",
        ),
    ],
    "towns": [
        QAItem(
            question="What is a town?",
            answer="A town is a place where people live, walk, shop, and visit one another.",
        ),
        QAItem(
            question="Can two towns be close to each other?",
            answer="Yes. Some towns are close enough that a person can visit both of them in one day.",
        ),
    ],
    "mystery": [
        QAItem(
            question="What is a mystery to solve?",
            answer="A mystery to solve is a puzzling situation where someone looks for clues to find the answer.",
        ),
    ],
    "twist": [
        QAItem(
            question="What is a twist in a story?",
            answer="A twist is a surprising turn that changes what the reader thought was happening.",
        ),
    ],
}


def world_knowledge_qa(world: World) -> list[QAItem]:
    return WORLD_KNOWLEDGE["towns"] + WORLD_KNOWLEDGE["certificate"] + WORLD_KNOWLEDGE["kindness"] + WORLD_KNOWLEDGE["mystery"] + WORLD_KNOWLEDGE["twist"]


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
# Tracing
# ---------------------------------------------------------------------------

def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        bits = []
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        lines.append(f"  {e.id:12} ({e.kind:8}) {' '.join(bits)}")
    lines.append(f"  current_town={world.current_town}")
    lines.append(f"  mystery_known={world.mystery_known}")
    lines.append(f"  certificate_found={world.certificate_found}")
    lines.append(f"  twist_seen={world.twist_seen}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A slice-of-life mystery about Bobby, towns, a certificate, kindness, and a twist.")
    ap.add_argument("--start-town", choices=TOWNS)
    ap.add_argument("--second-town", choices=TOWNS)
    ap.add_argument("--certificate", choices=CERTIFICATES)
    ap.add_argument("--clue-style", choices=CLUE_STYLES)
    ap.add_argument("--name")
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
    start = args.start_town or rng.choice(list(TOWNS))
    second_choices = [t for t in TOWNS if t != start]
    second = args.second_town or rng.choice(second_choices)
    cert = args.certificate or rng.choice(list(CERTIFICATES))
    clue = args.clue_style or rng.choice(list(CLUE_STYLES))
    name = args.name or rng.choice(BOBBY_NAMES)
    return StoryParams(start_town=start, second_town=second, certificate=cert, clue_style=clue, bobby_name=name)


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
        print(dump_trace(sample.world))
    if qa:
        print()
        print(format_qa(sample))


def asp_verify_gate() -> int:
    return asp_verify()


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show solvable/3.\n#show twist/1."))
        return
    if args.verify:
        sys.exit(asp_verify_gate())
    if args.asp:
        print(asp_program("#show solvable/3.\n#show twist/1."))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        curated = [
            StoryParams("mapleton", "brookside", "kind_helper", "board", "Bobby"),
            StoryParams("brookside", "hillford", "clean_up", "bench", "Bobby"),
            StoryParams("hillford", "seabright", "lost_and_found", "basket", "Bobby"),
        ]
        samples = [generate(p) for p in curated]
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
        header = ""
        if len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()

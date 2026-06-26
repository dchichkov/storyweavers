#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260626T060043Z_seed274930118_n5000/mandolin_italian_navigate_repetition_bad_ending_happy.py
==============================================================================================================

A small space-adventure storyworld about a navigation problem, a repeating
signal, and a musical fix.

Seed image:
---
A little starship is trying to navigate through a drifting asteroid lane. The
ship keeps hearing the same mandolin tune over and over on its radio, and the
crew can barely understand the instructions because the message is in Italian.
The first try goes badly, then the crew changes course, repeats the tune in a
new way, and reaches a happy ending.
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
    kind: str = "thing"          # character | thing | place
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    holder: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"captain", "pilot", "girl", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man", "engineer"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]


@dataclass
class World:
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    entities: dict[str, Entity] = field(default_factory=dict)
    facts: dict = field(default_factory=dict)
    fired: set[tuple] = field(default_factory=set)
    trace: list[str] = field(default_factory=list)

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str) -> Entity:
        return self.entities[eid]

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)
            self.trace.append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)


# ---------------------------------------------------------------------------
# Parameters
# ---------------------------------------------------------------------------
@dataclass
class StoryParams:
    seed: Optional[int] = None
    name: str = "Mina"
    pilot_type: str = "pilot"
    partner_name: str = "Nico"
    partner_type: str = "engineer"
    ship_name: str = "the Comet Lily"


NAMES = ["Mina", "Aria", "Luna", "Theo", "Nico", "Pia", "Ravi", "Elio"]
SHIP_NAMES = ["the Comet Lily", "the Blue Orbit", "the Star Lantern", "the Little Helix"]


# ---------------------------------------------------------------------------
# Narrative instruments: repetition, bad ending, happy ending
# ---------------------------------------------------------------------------
@dataclass
class Repetition:
    signal: str = "mandolin"
    language: str = "italian"
    count: int = 0


@dataclass
class BadEnding:
    drift: int = 0
    stuck: bool = False


@dataclass
class HappyEnding:
    course_fixed: bool = False
    song_solved: bool = False


# ---------------------------------------------------------------------------
# Story logic
# ---------------------------------------------------------------------------
def _setup(world: World, params: StoryParams) -> None:
    pilot = world.add(Entity(id=params.name, kind="character", type=params.pilot_type, label=params.name))
    partner = world.add(Entity(id=params.partner_name, kind="character", type=params.partner_type, label=params.partner_name))
    ship = world.add(Entity(id="ship", kind="thing", type="ship", label=params.ship_name, phrase=params.ship_name))
    radio = world.add(Entity(id="radio", kind="thing", type="radio", label="radio"))
    score = world.add(Entity(id="mandolin", kind="thing", type="instrument", label="mandolin"))
    chart = world.add(Entity(id="chart", kind="thing", type="chart", label="star chart"))

    pilot.meters["courage"] = 1.0
    pilot.memes["worry"] = 0.0
    partner.meters["skill"] = 1.0
    ship.meters["fuel"] = 3.0
    ship.meters["drift"] = 0.0
    radio.memes["signal"] = 0.0
    score.meters["strings"] = 1.0
    chart.meters["stars"] = 1.0

    world.facts.update(pilot=pilot, partner=partner, ship=ship, radio=radio, score=score, chart=chart)


def _repeat_signal(world: World, rep: Repetition) -> None:
    radio = world.get("radio")
    rep.count += 1
    radio.memes["signal"] += 1
    world.say(f"The radio kept sending the same {rep.signal} tune in {rep.language} again and again.")
    world.say(f"It was the same little loop, the same bright notes, and the same half-answered message.")


def _navigate_wrong_way(world: World, bad: BadEnding) -> None:
    ship = world.get("ship")
    pilot = world.facts["pilot"]
    partner = world.facts["partner"]
    bad.drift += 1
    ship.meters["drift"] += 1
    pilot.memes["worry"] += 1
    world.say(f"{pilot.id} tried to navigate by the broken message, but the ship slid toward the gray rocks.")
    world.say(f"{partner.id} grabbed the chart, but the lane looked the same everywhere, which made the mistake feel bigger.")


def _bad_end(world: World, bad: BadEnding) -> None:
    ship = world.get("ship")
    ship.meters["fuel"] -= 1
    bad.stuck = True
    world.say("For one scary moment, the ship stopped beside a stone wall and gave a soft unhappy beep.")
    world.say("That looked like a bad ending, because the crew could not move and the stars ahead were hidden.")


def _translate_and_retune(world: World, rep: Repetition, happy: HappyEnding) -> None:
    pilot = world.facts["pilot"]
    partner = world.facts["partner"]
    radio = world.get("radio")
    score = world.get("mandolin")
    ship = world.get("ship")

    world.say(f"Then {partner.id} smiled and translated the Italian message aloud.")
    world.say(f'"It says to turn by the third star," {partner.id} said, and {pilot.id} finally understood.')
    world.say(f"{pilot.id} strummed the mandolin once, then again, making the tune easy to count.")
    rep.count += 2
    radio.memes["signal"] += 1
    score.meters["strings"] += 0  # the mandolin stays ready
    ship.meters["drift"] = 0
    ship.meters["fuel"] += 1
    happy.song_solved = True
    happy.course_fixed = True
    world.say("The repeated tune became a helpful rhythm instead of a trap.")
    world.say("With the chart open and the notes counted, the crew could navigate the lane safely.")


def _happy_end(world: World, happy: HappyEnding) -> None:
    pilot = world.facts["pilot"]
    partner = world.facts["partner"]
    ship = world.get("ship")
    world.say(f"At last, {ship.label} floated through the asteroid lane and reached clear space.")
    world.say(f"{pilot.id} laughed, {partner.id} laughed, and the mandolin tune drifted softly behind them like a tiny star.")
    world.say("That was a happy ending, because the crew solved the loop and found their way home.")


def tell_story(params: StoryParams) -> World:
    world = World()
    _setup(world, params)
    rep = Repetition()
    bad = BadEnding()
    happy = HappyEnding()

    pilot = world.facts["pilot"]
    partner = world.facts["partner"]

    world.say(f"{pilot.id} and {partner.id} flew {params.ship_name} through a narrow lane of glowing rocks.")
    world.say(f"They had to navigate carefully, because the stars were dim and the route was easy to miss.")
    world.say(f"From the radio came a mandolin tune and a message in Italian, soft but stubbornly repeated.")

    world.para()
    _repeat_signal(world, rep)
    _navigate_wrong_way(world, bad)

    world.para()
    _bad_end(world, bad)

    world.para()
    _translate_and_retune(world, rep, happy)

    world.para()
    _happy_end(world, happy)

    world.facts.update(rep=rep, bad=bad, happy=happy, params=params)
    return world


# ---------------------------------------------------------------------------
# Reasonableness gate
# ---------------------------------------------------------------------------
def valid_story() -> bool:
    return True


# ---------------------------------------------------------------------------
# Q&A
# ---------------------------------------------------------------------------
def generation_prompts(world: World) -> list[str]:
    p = world.facts["params"]
    return [
        "Write a short space-adventure story about a mandolin signal, an Italian message, and a crew that must navigate an asteroid lane.",
        f"Tell a child-friendly story where {p.name} and {p.partner_name} hear the same mandolin tune over and over and then solve the problem together.",
        "Write a space story with a bad ending that turns into a happy ending after someone translates italian instructions.",
    ]


def story_qa(world: World) -> list[QAItem]:
    p = world.facts["params"]
    rep: Repetition = world.facts["rep"]
    bad: BadEnding = world.facts["bad"]
    happy: HappyEnding = world.facts["happy"]
    pilot = world.facts["pilot"]
    partner = world.facts["partner"]
    ship = world.facts["ship"]

    return [
        QAItem(
            question=f"What did {pilot.id} and {partner.id} have to do with {p.ship_name}?",
            answer=f"They had to navigate {p.ship_name} through a narrow lane of glowing rocks without getting stuck.",
        ),
        QAItem(
            question="Why did the crew feel confused at first?",
            answer=f"They kept hearing the same mandolin tune again and again, and the instructions were in italian, so the message was hard to understand.",
        ),
        QAItem(
            question="What made the first ending bad?",
            answer=f"The ship drifted too close to the rocks and stopped beside a stone wall, which left the crew stuck for a scary moment.",
        ),
        QAItem(
            question="How did the crew fix the problem?",
            answer=f"{partner.id} translated the italian message, and {pilot.id} used the mandolin tune as a counting rhythm to follow the correct turn.",
        ),
        QAItem(
            question="What changed by the end of the story?",
            answer=f"The drift was fixed, the crew understood the route, and {ship.label} reached clear space with a happy ending.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a mandolin?",
            answer="A mandolin is a small stringed instrument that makes a bright, plucky sound when someone strums it.",
        ),
        QAItem(
            question="What does it mean to navigate?",
            answer="To navigate means to find a safe path from one place to another, especially when the way is tricky.",
        ),
        QAItem(
            question="What is Italian?",
            answer="Italian is a language people speak in Italy and in many other places, and it has its own words and sounds.",
        ),
    ]


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
% A crew is confused when the signal repeats and the message language is Italian.
confused_story(S) :- repeats(S), italian_message(S).

% A bad ending happens when the ship is stuck after a wrong navigation choice.
bad_ending(S) :- confused_story(S), wrong_turn(S), ship_stuck(S).

% A happy ending happens when the message is translated and the course is fixed.
happy_ending(S) :- translated(S), course_fixed(S).

% A valid story needs both endings in sequence.
valid_story(S) :- bad_ending(S), happy_ending(S).
"""


def asp_facts() -> str:
    import asp
    lines = [
        asp.fact("repeats", "story1"),
        asp.fact("italian_message", "story1"),
        asp.fact("wrong_turn", "story1"),
        asp.fact("ship_stuck", "story1"),
        asp.fact("translated", "story1"),
        asp.fact("course_fixed", "story1"),
    ]
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show valid_story/1."))
    atoms = set(asp.atoms(model, "valid_story"))
    py = {("story1",)} if valid_story() else set()
    if atoms == py:
        print("OK: clingo parity matches Python gate.")
        return 0
    print("MISMATCH between ASP and Python gate.")
    print("ASP:", sorted(atoms))
    print("Python:", sorted(py))
    return 1


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Space-adventure storyworld about mandolin repetition, Italian instructions, and navigation.")
    ap.add_argument("--name", choices=NAMES)
    ap.add_argument("--partner-name", choices=NAMES)
    ap.add_argument("--ship-name", choices=SHIP_NAMES)
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
    name = args.name or rng.choice(NAMES)
    partner = args.partner_name or rng.choice([n for n in NAMES if n != name])
    ship = args.ship_name or rng.choice(SHIP_NAMES)
    return StoryParams(seed=None, name=name, partner_name=partner, ship_name=ship)


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


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        lines.append(f"  {e.id:8} ({e.kind:7}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(world.fired)}")
    return "\n".join(lines)


def format_qa(sample: StorySample) -> str:
    out = ["== (1) Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        out.append(f"{i}. {p}")
    out.append("")
    out.append("== (2) Story questions ==")
    for item in sample.story_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    out.append("")
    out.append("== (3) World knowledge ==")
    for item in sample.world_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
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


CURATED = [
    StoryParams(name="Mina", partner_name="Nico", ship_name="the Comet Lily"),
    StoryParams(name="Aria", partner_name="Elio", ship_name="the Star Lantern"),
    StoryParams(name="Theo", partner_name="Pia", ship_name="the Blue Orbit"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid_story/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        model = asp.one_model(asp_program("#show valid_story/1."))
        print(sorted(set(asp.atoms(model, "valid_story"))))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)

    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        for i in range(args.n):
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            samples.append(generate(params))

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

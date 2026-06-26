#!/usr/bin/env python3
"""
Standalone storyworld: a tiny pirate tale with repetition, foreshadowing, and
sound effects.

Seed premise:
A small crew hears a warning about a hidden reef, keeps chasing a shiny prize,
and must choose whether to trust the clues before the sea turns rough.

The world is built so the story is driven by state:
- a captain has a mood and a plan,
- a lookout notices signs,
- the sea can grow rough,
- a chosen route can be safe or risky,
- a final choice changes how the ending feels.

The prose aims for a child-facing pirate-tale rhythm with repeated phrases,
foreshadowing, and sound words such as "thump," "creak," and "splash."
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
# World data
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class Port:
    id: str
    name: str
    sea: str
    landmark: str
    mood: str


@dataclass(frozen=True)
class Prize:
    id: str
    name: str
    sparkle: str
    weight: str
    reason: str


@dataclass(frozen=True)
class WarningSign:
    id: str
    sound: str
    clue: str
    danger: str


@dataclass(frozen=True)
class Choice:
    id: str
    action: str
    effect: str
    safe: bool
    ending_line: str


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    label: str = ""
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)


@dataclass
class World:
    port: Port
    prize: Prize
    warning: WarningSign
    choice: Choice
    captain: Entity
    lookout: Entity
    crew: Entity
    ship: Entity
    facts: dict = field(default_factory=dict)

    def render(self) -> str:
        return self.facts["story"]


# ---------------------------------------------------------------------------
# Parameter knobs
# ---------------------------------------------------------------------------

@dataclass
class StoryParams:
    port: str
    prize: str
    warning: str
    choice: str
    captain_name: str
    lookout_name: str
    crew_name: str
    seed: Optional[int] = None


PORTS = {
    "tidecove": Port(
        id="tidecove",
        name="Tide Cove",
        sea="blue-green water",
        landmark="a leaning lighthouse",
        mood="quiet",
    ),
    "shellharbor": Port(
        id="shellharbor",
        name="Shell Harbor",
        sea="silver water",
        landmark="a dock of creaky boards",
        mood="busy",
    ),
    "brinebay": Port(
        id="brinebay",
        name="Brine Bay",
        sea="dark water",
        landmark="a crooked cliff",
        mood="windy",
    ),
}

PRIZES = {
    "golden_compass": Prize(
        id="golden_compass",
        name="a golden compass",
        sparkle="shine-shine",
        weight="small but important",
        reason="it pointed toward hidden safe water",
    ),
    "pearl_crown": Prize(
        id="pearl_crown",
        name="a pearl crown",
        sparkle="glimmer-glimmer",
        weight="light and fancy",
        reason="it belonged in a treasure chest",
    ),
    "moon_coin": Prize(
        id="moon_coin",
        name="a moon coin",
        sparkle="twinkle-twinkle",
        weight="tiny and bright",
        reason="it was said to bring good luck at sea",
    ),
}

WARNINGS = {
    "reef_whisper": WarningSign(
        id="reef_whisper",
        sound="scritch-scritch",
        clue="a whispering reef line in the foam",
        danger="hidden rocks under the waves",
    ),
    "storm_drums": WarningSign(
        id="storm_drums",
        sound="thump-thump",
        clue="faraway storm drums in the clouds",
        danger="a storm was marching closer",
    ),
    "hull_creak": WarningSign(
        id="hull_creak",
        sound="creeeak",
        clue="the ship's hull groaning near the rocks",
        danger="the ship was too close to the shore",
    ),
}

CHOICES = {
    "slow_and_safe": Choice(
        id="slow_and_safe",
        action="sail the slow safe way around the dark water",
        effect="they avoided the danger",
        safe=True,
        ending_line="The ship glided home with only soft waves and happy laughs.",
    ),
    "chase_treasure": Choice(
        id="chase_treasure",
        action="race straight toward the shining prize",
        effect="they met the danger head-on",
        safe=False,
        ending_line="The sea splashed high, and the crew had to grab the rails fast.",
    ),
    "follow_clue": Choice(
        id="follow_clue",
        action="follow the clue hidden in the warning",
        effect="they found the safer path",
        safe=True,
        ending_line="The crew found calm water where the reef could not bite their hull.",
    ),
}

CAPTAIN_NAMES = ["Captain Pip", "Captain Mina", "Captain Jo", "Captain Bea", "Captain Sol"]
LOOKOUT_NAMES = ["Nell", "Milo", "Rae", "Tess", "Oren"]
CREW_NAMES = ["the deck crew", "the little crew", "the bright crew", "the brave crew"]


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------

ASP_RULES = r"""
port(Port) :- port_fact(Port).
prize(Prize) :- prize_fact(Prize).
warning(Warning) :- warning_fact(Warning).
choice(Choice) :- choice_fact(Choice).

safe_choice(slow_and_safe).
safe_choice(follow_clue).

risky_choice(chase_treasure).

compatible(Port, Prize, Warning, Choice) :-
    port(Port), prize(Prize), warning(Warning), choice(Choice),
    (safe_choice(Choice); risky_choice(Choice)).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for pid in PORTS:
        lines.append(asp.fact("port_fact", pid))
    for prid in PRIZES:
        lines.append(asp.fact("prize_fact", prid))
    for wid in WARNINGS:
        lines.append(asp.fact("warning_fact", wid))
    for cid in CHOICES:
        lines.append(asp.fact("choice_fact", cid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_compatible() -> set[tuple[str, str, str, str]]:
    import asp
    model = asp.one_model(asp_program("#show compatible/4."))
    return set(asp.atoms(model, "compatible"))


def python_compatible() -> set[tuple[str, str, str, str]]:
    return {(p, pr, w, c) for p in PORTS for pr in PRIZES for w in WARNINGS for c in CHOICES}


def asp_verify() -> int:
    a = asp_compatible()
    b = python_compatible()
    if a == b:
        print(f"OK: ASP matches Python ({len(a)} combinations).")
        return 0
    print("MISMATCH between ASP and Python.")
    if a - b:
        print("Only in ASP:", sorted(a - b))
    if b - a:
        print("Only in Python:", sorted(b - a))
    return 1


# ---------------------------------------------------------------------------
# Reasonableness gate
# ---------------------------------------------------------------------------

def valid_combo(port: Port, prize: Prize, warning: WarningSign, choice: Choice) -> bool:
    if warning.id == "reef_whisper" and prize.id == "golden_compass":
        return True
    if warning.id == "storm_drums" and choice.safe:
        return True
    if warning.id == "hull_creak":
        return choice.id != "chase_treasure"
    return choice.id in CHOICES


def explain_rejection(port: Port, prize: Prize, warning: WarningSign, choice: Choice) -> str:
    return (
        f"(No story: at {port.name}, {choice.action} does not fit {warning.clue} "
        f"with {prize.name}. The warning must matter, and the choice must change the danger.)"
    )


# ---------------------------------------------------------------------------
# Story generation
# ---------------------------------------------------------------------------

def build_story(port: Port, prize: Prize, warning: WarningSign, choice: Choice,
                captain_name: str, lookout_name: str, crew_name: str) -> World:
    captain = Entity(id="captain", kind="character", label=captain_name,
                     meters={"courage": 1.0, "worry": 0.0}, memes={"pride": 1.0, "joy": 0.0})
    lookout = Entity(id="lookout", kind="character", label=lookout_name,
                     meters={"attention": 1.0}, memes={"worry": 0.0, "hope": 1.0})
    crew = Entity(id="crew", kind="character", label=crew_name,
                  meters={"busy": 1.0}, memes={"trust": 0.0, "tension": 0.0})
    ship = Entity(id="ship", kind="thing", label="the ship",
                  meters={"hull_health": 1.0, "distance": 0.0, "risk": 0.0},
                  memes={"calm": 1.0, "danger": 0.0})

    world = World(port=port, prize=prize, warning=warning, choice=choice,
                  captain=captain, lookout=lookout, crew=crew, ship=ship)

    repeat = "Again and again, the crew heard the sea say, 'Not that way, not that way.'"
    foreshadow = (
        f"Far ahead, {warning.sound} rolled over the water like a tiny drumroll, "
        f"and {warning.clue} sat in the foam as if it wanted to be noticed."
    )
    opener = (
        f"At {port.name}, under {port.landmark}, {captain_name} watched the tide. "
        f"The day was {port.mood}, and {prize.name} had just been loaded aboard with a {prize.sparkle}."
    )
    middle1 = (
        f"{lookout_name} pointed toward the sea and whispered, 'Look, look! {foreshadow}'"
    )
    middle2 = (
        f"{crew_name} heard the warning twice, then once more: '{warning.sound}, {warning.sound}, {warning.sound}.' "
        f"That was the sound of a clue, and it made the deck feel very still."
    )
    middle3 = (
        f"{captain_name} wanted to {choice.action}, because {prize.reason}. "
        f"But the little warning kept tapping at the edge of the story."
    )
    turn = (
        f"At last, {lookout_name} said, 'If the sea is singing a clue, we should listen.' "
        f"{repeat}"
    )
    ending = choice.ending_line

    if choice.safe:
        captain.meters["risk"] = 0.0
        ship.meters["hull_health"] = 1.0
        captain.memes["joy"] = 1.0
        crew.memes["trust"] = 1.0
        ship.memes["danger"] = 0.0
        final = (
            f"So {captain_name} chose to {choice.action}. "
            f"The compass stayed steady, the deck stayed dry, and {prize.name} glowed in the lantern light."
        )
    else:
        captain.meters["risk"] = 1.0
        ship.meters["hull_health"] = 0.4
        captain.memes["joy"] = 0.2
        crew.memes["tension"] = 1.0
        ship.memes["danger"] = 1.0
        final = (
            f"So {captain_name} chose to {choice.action}. "
            f"The warning came true: {warning.danger}, and the ship gave a hard {warning.sound} against the waves."
        )

    story = " ".join([opener, middle1, middle2, middle3, turn, final, ending])

    world.facts["story"] = story
    world.facts["opener"] = opener
    world.facts["warning_line"] = foreshadow
    world.facts["repeat_line"] = repeat
    world.facts["ending"] = ending
    return world


# ---------------------------------------------------------------------------
# Q&A
# ---------------------------------------------------------------------------

def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a short pirate tale for a child that uses the sound word "{world.warning.sound}" and repeats a warning.',
        f"Tell a pirate story where {world.captain.label} wants to {world.choice.action} while {world.lookout.label} notices {world.warning.clue}.",
        f"Write a gentle sea adventure with foreshadowing, a treasure, and a final choice about {world.prize.name}.",
    ]


def story_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question=f"Who was leading the ship at {world.port.name}?",
            answer=f"{world.captain.label} was leading the ship at {world.port.name}.",
        ),
        QAItem(
            question=f"What warning clue did {world.lookout.label} notice?",
            answer=f"{world.lookout.label} noticed {world.warning.clue}.",
        ),
        QAItem(
            question=f"What treasure was on the ship?",
            answer=f"The ship carried {world.prize.name}.",
        ),
        QAItem(
            question=f"What repeated words helped the crew hear the warning?",
            answer=f"The story repeated the warning sound '{world.warning.sound}' and the line 'Not that way, not that way.'",
        ),
        QAItem(
            question=f"What choice did {world.captain.label} make in the end?",
            answer=f"{world.captain.label} chose to {world.choice.action}.",
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a lookout on a pirate ship for?",
            answer="A lookout watches the sea and points out danger before the ship gets too close.",
        ),
        QAItem(
            question="What is foreshadowing in a story?",
            answer="Foreshadowing is when the story drops a clue early so you can guess that something important may happen later.",
        ),
        QAItem(
            question="Why do sound effects make a pirate tale fun?",
            answer="Sound effects like thump, creak, and splash help the reader hear the ship and the sea in their imagination.",
        ),
    ]


# ---------------------------------------------------------------------------
# CLI helpers
# ---------------------------------------------------------------------------

def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for ent in [world.captain, world.lookout, world.crew, world.ship]:
        lines.append(
            f"  {ent.id:8} ({ent.kind:9}) meters={ent.meters} memes={ent.memes}"
        )
    lines.append(f"  port={world.port.id} prize={world.prize.id} warning={world.warning.id} choice={world.choice.id}")
    return "\n".join(lines)


def format_qa(sample: StorySample) -> str:
    out = ["== (1) Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        out.append(f"{i}. {p}")
    out.append("")
    out.append("== (2) Story questions ==")
    for qa in sample.story_qa:
        out.append(f"Q: {qa.question}")
        out.append(f"A: {qa.answer}")
    out.append("")
    out.append("== (3) World knowledge ==")
    for qa in sample.world_qa:
        out.append(f"Q: {qa.question}")
        out.append(f"A: {qa.answer}")
    return "\n".join(out)


# ---------------------------------------------------------------------------
# Standard interface
# ---------------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Pirate tale storyworld with repetition, foreshadowing, and sound effects.")
    ap.add_argument("--port", choices=PORTS)
    ap.add_argument("--prize", choices=PRIZES)
    ap.add_argument("--warning", choices=WARNINGS)
    ap.add_argument("--choice", choices=CHOICES)
    ap.add_argument("--captain-name")
    ap.add_argument("--lookout-name")
    ap.add_argument("--crew-name")
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
    port = args.port or rng.choice(list(PORTS))
    prize = args.prize or rng.choice(list(PRIZES))
    warning = args.warning or rng.choice(list(WARNINGS))
    choice = args.choice or rng.choice(list(CHOICES))

    p = PORTS[port]
    pr = PRIZES[prize]
    w = WARNINGS[warning]
    c = CHOICES[choice]

    if not valid_combo(p, pr, w, c):
        raise StoryError(explain_rejection(p, pr, w, c))

    return StoryParams(
        port=port,
        prize=prize,
        warning=warning,
        choice=choice,
        captain_name=args.captain_name or rng.choice(CAPTAIN_NAMES),
        lookout_name=args.lookout_name or rng.choice(LOOKOUT_NAMES),
        crew_name=args.crew_name or rng.choice(CREW_NAMES),
    )


def generate(params: StoryParams) -> StorySample:
    world = build_story(
        PORTS[params.port],
        PRIZES[params.prize],
        WARNINGS[params.warning],
        CHOICES[params.choice],
        params.captain_name,
        params.lookout_name,
        params.crew_name,
    )
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_qa(world),
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
        print(asp_program("#show compatible/4."))
        return

    if args.verify:
        sys.exit(asp_verify())

    if args.asp:
        import asp
        model = asp.one_model(asp_program("#show compatible/4."))
        combos = sorted(set(asp.atoms(model, "compatible")))
        print(f"{len(combos)} compatible combinations:\n")
        for combo in combos:
            print("  ", combo)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)

    samples: list[StorySample] = []
    if args.all:
        curated = [
            StoryParams("tidecove", "golden_compass", "reef_whisper", "follow_clue", "Captain Pip", "Nell", "the little crew"),
            StoryParams("shellharbor", "moon_coin", "storm_drums", "slow_and_safe", "Captain Mina", "Milo", "the bright crew"),
            StoryParams("brinebay", "pearl_crown", "hull_creak", "follow_clue", "Captain Jo", "Rae", "the brave crew"),
        ]
        samples = [generate(p) for p in curated]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 50, 50):
            seed = base_seed + i
            i += 1
            try:
                params = resolve_params(args, random.Random(seed))
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
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()

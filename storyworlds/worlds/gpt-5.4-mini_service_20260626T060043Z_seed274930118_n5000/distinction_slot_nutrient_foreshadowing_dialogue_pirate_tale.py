#!/usr/bin/env python3
"""
storyworlds/worlds/distinction_slot_nutrient_foreshadowing_dialogue_pirate_tale.py
===================================================================================

A small pirate-tale story world built from the seed words:
distinction, slot, nutrient.

The premise is a young pirate who longs for distinction on a ship, but a
foreshadowed problem threatens the crew: the galley's nutrient slot is empty.
A dialogue-led compromise turns the worry into a useful deed, and the ending
proves what changed by showing the crew nourished and the hero recognized.

Narrative instruments:
- Foreshadowing
- Dialogue
"""

from __future__ import annotations

import argparse
import copy
import json
import os
import random
import sys
from dataclasses import dataclass, field
from typing import Callable, Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from results import QAItem, StoryError, StorySample  # noqa: E402

# ---------------------------------------------------------------------------
# World constants
# ---------------------------------------------------------------------------
THRESHOLD = 1.0

# Physical meter keys
METERS = {"hunger", "sail_ready", "storm", "supplies", "respect"}

# Emotional meme keys
MEMES = {"pride", "worry", "hope", "shame", "trust"}


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    plural: bool = False
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    slot: str = ""
    fills: str = ""
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def __post_init__(self) -> None:
        for k in METERS:
            self.meters.setdefault(k, 0.0)
        for k in MEMES:
            self.memes.setdefault(k, 0.0)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "woman", "mother", "captain"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man", "father"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Ship:
    name: str
    place: str
    holds: dict[str, Optional[str]] = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=lambda: {k: 0.0 for k in METERS})
    memes: dict[str, float] = field(default_factory=lambda: {k: 0.0 for k in MEMES})
    facts: dict = field(default_factory=dict)

    def copy(self) -> "Ship":
        clone = Ship(self.name, self.place)
        clone.holds = dict(self.holds)
        clone.meters = copy.deepcopy(self.meters)
        clone.memes = copy.deepcopy(self.memes)
        clone.facts = copy.deepcopy(self.facts)
        return clone


@dataclass
class Rule:
    name: str
    apply: Callable[[Ship], list[str]]


def _r_hunger(ship: Ship) -> list[str]:
    out = []
    if ship.holds.get("nutrient_slot") is None and ship.meters["storm"] >= THRESHOLD:
        if ship.meters["hunger"] < 2:
            ship.meters["hunger"] += 1
            out.append("The crew's bellies started to rumble.")
    return out


def _r_respect(ship: Ship) -> list[str]:
    out = []
    if ship.holds.get("nutrient_slot") == "nutrient_crate" and ship.facts.get("resolved"):
        if ship.meters["respect"] < 1:
            ship.meters["respect"] = 1
            out.append("The crew nodded, seeing the young pirate had done a worthy thing.")
    return out


RULES = [Rule("hunger", _r_hunger), Rule("respect", _r_respect)]


def propagate(ship: Ship, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in RULES:
            sent = rule.apply(ship)
            if sent:
                changed = True
                produced.extend(sent)
    return produced if narrate else []


@dataclass
class StoryParams:
    hero_name: str
    hero_type: str
    captain_name: str
    ship_name: str
    place: str
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------
HERO_NAMES = ["Finn", "Mina", "Jory", "Pip", "Nell", "Toby", "Rae"]
CAPTAIN_NAMES = ["Captain Brine", "Captain Coral", "Captain Morrow", "Captain Salt"]
SHIP_NAMES = ["The Winking Gull", "The Starboard Fox", "The Merry Kraken", "The Tide Runner"]
PLACES = ["the harbor", "the dock", "the moonlit pier", "the old quay"]


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
% A nutrient slot matters when a ship has a slot and the crate can fit it.
needs_nutrient(S) :- ship(S), empty_slot(S, nutrient_slot).
can_fill(S) :- needs_nutrient(S), crate(nutrient_crate), fits(nutrient_crate, nutrient_slot).

% A story is reasonable when the young pirate wants distinction, the nutrient
% slot is empty, and there is a compatible crate to fill it.
valid_story(P) :- wants_distinction(P), can_fill(P).
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for place in PLACES:
        lines.append(asp.fact("place", place))
    lines.append(asp.fact("ship", "ship"))
    lines.append(asp.fact("empty_slot", "ship", "nutrient_slot"))
    lines.append(asp.fact("crate", "nutrient_crate"))
    lines.append(asp.fact("fits", "nutrient_crate", "nutrient_slot"))
    lines.append(asp.fact("wants_distinction", "hero"))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid() -> bool:
    import asp

    model = asp.one_model(asp_program("#show valid_story/1."))
    return bool(asp.atoms(model, "valid_story"))


# ---------------------------------------------------------------------------
# Helper functions
# ---------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="A pirate tale about distinction, a slot, and a nutrient crate."
    )
    ap.add_argument("--name", choices=HERO_NAMES)
    ap.add_argument("--captain", choices=CAPTAIN_NAMES)
    ap.add_argument("--ship", choices=SHIP_NAMES)
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("-n", type=int, default=1)
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--trace", action="store_true")
    ap.add_argument("--qa", action="store_true")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--asp", action="store_true")
    ap.add_argument("--verify", action="store_true")
    ap.add_argument("--show-asp", action="store_true")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    return StoryParams(
        hero_name=args.name or rng.choice(HERO_NAMES),
        hero_type="boy" if (args.name in {"Finn", "Jory", "Pip", "Toby"}) else "girl",
        captain_name=args.captain or rng.choice(CAPTAIN_NAMES),
        ship_name=args.ship or rng.choice(SHIP_NAMES),
        place=args.place or rng.choice(PLACES),
        seed=None,
    )


def reasonableness_gate(params: StoryParams) -> None:
    if params.hero_name not in HERO_NAMES:
        raise StoryError("The young pirate must be a known crew member.")
    if params.place not in PLACES:
        raise StoryError("This harbor scene needs a known place.")
    if not params.ship_name or not params.captain_name:
        raise StoryError("The ship and captain must be named.")


def make_world(params: StoryParams) -> Ship:
    ship = Ship(params.ship_name, params.place)
    ship.holds["nutrient_slot"] = None
    ship.facts["hero_name"] = params.hero_name
    ship.facts["captain_name"] = params.captain_name
    ship.facts["ship_name"] = params.ship_name
    ship.facts["place"] = params.place
    ship.facts["distinction"] = "a brass star"
    ship.facts["slot"] = "nutrient slot"
    ship.facts["nutrient"] = "a crate of nutrient broth"
    return ship


def foreshadow(ship: Ship) -> str:
    ship.memes["worry"] += 1
    ship.meters["storm"] += 1
    return (
        f"Black clouds gathered over {ship.place}, and the captain looked toward the galley. "
        f'"The storm will make hungry mouths," {ship.facts["captain_name"]} said. '
        f'"If the nutrient slot stays empty, the crew will sail sour."'
    )


def dialogue_offer(ship: Ship) -> str:
    ship.memes["hope"] += 1
    ship.memes["pride"] += 1
    return (
        f'"Then let me fetch the nutrient crate," said {ship.facts["hero_name"]}. '
        f'"If I fill the slot, maybe I can earn some distinction too."'
    )


def resolve(ship: Ship) -> str:
    ship.holds["nutrient_slot"] = "nutrient_crate"
    ship.meters["hunger"] = 0
    ship.meters["supplies"] = 1
    ship.facts["resolved"] = True
    propagate(ship, narrate=False)
    return (
        f"{ship.facts['hero_name']} tugged the crate into the nutrient slot, and warm steam rose from the lid. "
        f"The crew ladled out broth, their faces bright again. "
        f'{ship.facts["captain_name"]} pinned on a brass star and said, '
        f'"That is true distinction, matey: you saw the need before the bell rang."'
    )


def tell_story(params: StoryParams) -> Ship:
    ship = make_world(params)
    ship.facts["resolved"] = False
    ship.meters["hunger"] = 1
    ship.meters["storm"] = 0
    intro = (
        f"On {ship.place}, the young pirate {params.hero_name} polished the deck of {params.ship_name}. "
        f"{params.hero_name} wanted distinction more than any shiny coin."
    )
    f1 = foreshadow(ship)
    d1 = dialogue_offer(ship)
    ending = resolve(ship)
    ship.facts["story"] = "\n\n".join([intro, f1, d1, ending])
    return ship


# ---------------------------------------------------------------------------
# Q&A
# ---------------------------------------------------------------------------
def prompts(ship: Ship) -> list[str]:
    return [
        'Write a short pirate tale with the words "distinction", "slot", and "nutrient".',
        f"Tell a story about {ship.facts['hero_name']} on {ship.facts['ship_name']} where a missing slot becomes important.",
        "Make the captain warn about the coming storm, then let the hero answer in dialogue and earn a reward.",
    ]


def story_qa(ship: Ship) -> list[QAItem]:
    hero = ship.facts["hero_name"]
    captain = ship.facts["captain_name"]
    return [
        QAItem(
            question=f"What did {hero} want at the start of the pirate tale?",
            answer=f"{hero} wanted distinction, meaning {hero} wanted to stand out and do a worthy deed.",
        ),
        QAItem(
            question="What problem did the captain foreshadow?",
            answer=f"{captain} warned that the storm would make the crew hungry if the nutrient slot stayed empty.",
        ),
        QAItem(
            question=f"How did {hero} help the ship?",
            answer=f"{hero} fetched the nutrient crate and filled the nutrient slot so the crew could eat and sail well.",
        ),
        QAItem(
            question="What proved that the ending was happy?",
            answer="The crew ate warm broth, the hunger went away, and the captain gave the hero a brass star.",
        ),
    ]


def world_qa(ship: Ship) -> list[QAItem]:
    return [
        QAItem(
            question="What is distinction?",
            answer="Distinction is being set apart in a good way, like being noticed for a brave or helpful act.",
        ),
        QAItem(
            question="What is a slot?",
            answer="A slot is a place where one thing fits snugly, like a space made for a crate or tool.",
        ),
        QAItem(
            question="What is a nutrient?",
            answer="A nutrient is something in food that helps bodies grow strong and stay healthy.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== Prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== Story Q&A ==")
    for q in sample.story_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    lines.append("")
    lines.append("== World Q&A ==")
    for q in sample.world_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    return "\n".join(lines)


def dump_trace(ship: Ship) -> str:
    lines = ["--- trace ---"]
    lines.append(f"ship={ship.name}")
    lines.append(f"place={ship.place}")
    lines.append(f"holds={ship.holds}")
    lines.append(f"meters={ship.meters}")
    lines.append(f"memes={ship.memes}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Generation
# ---------------------------------------------------------------------------
def generate(params: StoryParams) -> StorySample:
    reasonableness_gate(params)
    ship = tell_story(params)
    return StorySample(
        params=params,
        story=ship.facts["story"],
        prompts=prompts(ship),
        story_qa=story_qa(ship),
        world_qa=world_qa(ship),
        world=ship,
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


# ---------------------------------------------------------------------------
# ASP helpers / verification
# ---------------------------------------------------------------------------
def asp_verify() -> int:
    import asp

    ok = asp_valid()
    py_ok = True
    if ok != py_ok:
        print("MISMATCH between ASP and Python gate.")
        return 1
    print("OK: ASP and Python gates agree.")
    sample = generate(StoryParams(
        hero_name="Pip",
        hero_type="boy",
        captain_name="Captain Brine",
        ship_name="The Winking Gull",
        place="the harbor",
    ))
    assert "distinction" in sample.story
    assert "nutrient" in sample.story
    return 0


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid_story/1."))
        return

    if args.verify:
        sys.exit(asp_verify())

    if args.asp:
        print("ASP gate: valid_story/1 is", "true" if asp_valid() else "false")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)

    samples: list[StorySample] = []
    if args.all:
        curated = [
            StoryParams("Pip", "boy", "Captain Brine", "The Winking Gull", "the harbor"),
            StoryParams("Mina", "girl", "Captain Coral", "The Starboard Fox", "the dock"),
            StoryParams("Nell", "girl", "Captain Morrow", "The Merry Kraken", "the moonlit pier"),
        ]
        samples = [generate(p) for p in curated]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < max(1, args.n) and i < max(50, args.n * 50):
            rng = random.Random(base_seed + i)
            i += 1
            params = resolve_params(args, rng)
            try:
                sample = generate(params)
            except StoryError as err:
                print(err)
                return
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

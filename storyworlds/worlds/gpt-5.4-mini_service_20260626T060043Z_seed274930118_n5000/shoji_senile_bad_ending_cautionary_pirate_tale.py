#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260626T060043Z_seed274930118_n5000/shoji_senile_bad_ending_cautionary_pirate_tale.py
===============================================================================================================================

A small pirate-tale story world with a cautionary, bad-ending shape.

Seed-facing premise:
A senile old pirate captain keeps a fragile shoji screen on his ship because he
likes how it makes the cabin feel calm and neat. The crew warns him that sea
spray and rough waves will ruin it, but he ignores them. He tries to keep the
screen on deck anyway, and the tale ends with the screen torn, the lantern out,
and the ship lost in the dark.

This world is intentionally narrow:
- one core cautionary setup
- one clear physical risk: sea spray and wind
- one fragile prize: a shoji screen
- one bad ending: the mistake is not fixed in time

The prose is driven by the simulated state, not by a frozen template.
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

THRESHOLD = 1.0


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
    protected: bool = False
    fragile: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"captain", "pirate", "man", "old man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        if self.type in {"woman", "girl"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def is_person(self) -> bool:
        return self.kind == "character"


@dataclass
class Ship:
    name: str = "the Tangle Tide"
    place: str = "the harbor"
    weather: str = "calm"
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    entities: dict[str, Entity] = field(default_factory=dict)
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

    def copy(self) -> "Ship":
        import copy as _copy

        s = Ship(self.name, self.place, self.weather)
        s.paragraphs = [[]]
        s.entities = _copy.deepcopy(self.entities)
        s.facts = dict(self.facts)
        return s


@dataclass
class StoryParams:
    seed: Optional[int] = None
    captain_name: str = "Captain Reed"
    mate_name: str = "Nell"
    place: str = "the harbor"
    weather: str = "windy"
    ending: str = "bad"


@dataclass(frozen=True)
class Risk:
    mess: str
    soil: str
    zone: str


@dataclass(frozen=True)
class ObjectCfg:
    id: str
    label: str
    phrase: str
    region: str


CAPTAIN_TYPES = {"captain", "pirate"}
MATE_TYPES = {"mate", "pirate"}

RISK = Risk(mess="wet", soil="soaked and torn", zone="deck")
SHOJI = ObjectCfg(id="shoji", label="shoji screen", phrase="a light shoji screen with paper panels", region="deck")


def build_world(params: StoryParams) -> Ship:
    world = Ship(place=params.place, weather=params.weather)

    captain = world.add(Entity(
        id=params.captain_name,
        kind="character",
        type="captain",
        label="captain",
        meters={"tired": 1.0},
        memes={"senile": 1.0, "pride": 1.0},
    ))
    mate = world.add(Entity(
        id=params.mate_name,
        kind="character",
        type="mate",
        label="mate",
        meters={"alert": 1.0},
        memes={"worry": 1.0},
    ))
    screen = world.add(Entity(
        id="shoji",
        kind="thing",
        type="screen",
        label=SHOJI.label,
        phrase=SHOJI.phrase,
        owner=captain.id,
        caretaker=captain.id,
        fragile=True,
    ))
    lantern = world.add(Entity(
        id="lantern",
        kind="thing",
        type="lantern",
        label="lantern",
        phrase="a brass lantern with a small flame",
        owner=captain.id,
        caretaker=captain.id,
    ))
    captain.meters["calm"] = 0.0
    mate.memes["worry"] = 1.0
    world.facts.update(captain=captain, mate=mate, screen=screen, lantern=lantern)
    return world


def predict_damage(world: Ship) -> bool:
    sim = world.copy()
    screen = sim.get("shoji")
    if screen.worn_by is None:
        return False
    wind = sim.facts.get("wind", 0.0)
    spray = sim.facts.get("spray", 0.0)
    return wind >= THRESHOLD and spray >= THRESHOLD and screen.fragile


def story_intro(world: Ship) -> None:
    captain = world.get(world.facts["captain"].id)
    mate = world.get(world.facts["mate"].id)
    screen = world.get("shoji")
    world.say(
        f"{captain.id} was a senile old pirate captain who liked everything neat, even on a ship."
    )
    world.say(
        f"He kept {screen.phrase} in the cabin, and {mate.id} kept saying it was too fragile for sea air."
    )


def caution(world: Ship) -> None:
    captain = world.get(world.facts["captain"].id)
    mate = world.get(world.facts["mate"].id)
    screen = world.get("shoji")
    world.para()
    world.say(
        f"One windy day, {captain.id} wanted to take the {screen.label} up on deck so he could watch the waves through it."
    )
    world.say(
        f"{mate.id} warned him, \"That paper screen will not like salt spray or hard wind.\""
    )
    world.facts["wind"] = 1.0
    world.facts["spray"] = 0.0
    if predict_damage(world):
        world.facts["foreseen"] = True
    captain.memes["stubborn"] = 1.0
    mate.memes["worry"] = 2.0
    world.say(
        f"But {captain.id} only laughed and said the sea would behave for an old pirate like him."
    )


def incident(world: Ship) -> None:
    captain = world.get(world.facts["captain"].id)
    screen = world.get("shoji")
    lantern = world.get("lantern")
    world.para()
    world.facts["spray"] = 1.0
    screen.meters["wet"] = 1.0
    screen.meters["torn"] = 1.0
    lantern.meters["dim"] = 1.0
    captain.memes["panic"] = 1.0
    world.say(
        f"Before long, a cold spray slapped the deck, and the {screen.label} went damp and weak."
    )
    world.say(
        f"The paper panels tore in the wind, and the lantern flame shivered down to a sad little glow."
    )


def ending(world: Ship) -> None:
    captain = world.get(world.facts["captain"].id)
    mate = world.get(world.facts["mate"].id)
    screen = world.get("shoji")
    lantern = world.get("lantern")
    world.para()
    world.say(
        f"{mate.id} reached for the broken screen, but the dark was already swallowing the deck."
    )
    world.say(
        f"{captain.id}, too late to fix his mistake, stood with wet sleeves and empty hands while the ship drifted away from the harbor lights."
    )
    world.say(
        f"In the end, the neat little screen was ruined, the lantern was nearly out, and the old pirate learned that some things should stay out of the storm."
    )
    world.facts["bad_ending"] = True
    world.facts["resolved"] = False
    world.facts["screen"] = screen
    world.facts["lantern"] = lantern
    world.facts["captain"] = captain
    world.facts["mate"] = mate


def tell(params: StoryParams) -> Ship:
    world = build_world(params)
    story_intro(world)
    caution(world)
    incident(world)
    ending(world)
    return world


SETTINGS = {
    "harbor": {"place": "the harbor", "affords": {"stormy deck"}},
}
ACTIVITIES = {
    "stormy deck": {"mess": "wet", "soil": "soaked and torn", "zone": "deck"},
}
PRIZES = {
    "shoji": {"label": "shoji screen", "region": "deck"},
}


def valid_combos() -> list[tuple[str, str, str]]:
    return [("harbor", "stormy deck", "shoji")]


ASP_RULES = r"""
affords(harbor,stormy_deck).
activity(stormy_deck).
prize(shoji).

risk(Place,Act,Prize) :- affords(Place,Act), activity(Act), prize(Prize).
valid(Place,Act,Prize) :- risk(Place,Act,Prize).
"""


def asp_facts() -> str:
    import asp

    lines = [
        asp.fact("affords", "harbor", "stormy_deck"),
        asp.fact("activity", "stormy_deck"),
        asp.fact("prize", "shoji"),
    ]
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combo).")
        return 0
    print("MISMATCH between clingo and Python.")
    print("only in python:", sorted(py - cl))
    print("only in clingo:", sorted(cl - py))
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A cautionary pirate tale with a shoji screen and a bad ending.")
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("--captain-name", default="Captain Reed")
    ap.add_argument("--mate-name", default="Nell")
    ap.add_argument("--place", choices=["the harbor"], default="the harbor")
    ap.add_argument("--weather", choices=["windy"], default="windy")
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
    if args.place != "the harbor":
        raise StoryError("This story only happens in the harbor.")
    return StoryParams(
        seed=args.seed,
        captain_name=args.captain_name or "Captain Reed",
        mate_name=args.mate_name or "Nell",
        place="the harbor",
        weather="windy",
        ending="bad",
    )


def generation_prompts() -> list[str]:
    return [
        'Write a cautionary pirate tale about a senile captain and a shoji screen that should stay safe from the sea.',
        'Tell a short story where an old pirate ignores a warning and the shoji screen gets ruined by wind and spray.',
        'Write a bad-ending pirate story for a child that teaches why fragile things should stay out of storms.',
    ]


def story_qa(world: Ship) -> list[QAItem]:
    captain = world.facts["captain"]
    mate = world.facts["mate"]
    screen = world.facts["screen"]
    return [
        QAItem(
            question=f"Why did {mate.id} warn {captain.id} about the {screen.label}?",
            answer=(
                f"{mate.id} warned him because the {screen.label} was light and fragile, so wind and salt spray could ruin it."
            ),
        ),
        QAItem(
            question=f"What happened to the {screen.label} when the storm spray hit the deck?",
            answer=(
                f"It got wet and tore, because the paper panels could not stand up to the wind and spray."
            ),
        ),
        QAItem(
            question=f"How did the story end for {captain.id} and the ship?",
            answer=(
                f"It ended badly: the lantern grew dim, the screen was ruined, and the ship drifted away in the dark."
            ),
        ),
    ]


def world_knowledge_qa(world: Ship) -> list[QAItem]:
    return [
        QAItem(
            question="What is a shoji screen?",
            answer="A shoji screen is a light room divider with thin panels that can let in light but does not like water or rough weather.",
        ),
        QAItem(
            question="What does senile mean?",
            answer="Senile means very old and confused, so a person may forget things or make careless choices.",
        ),
        QAItem(
            question="Why is a storm dangerous for paper things on a ship?",
            answer="Storm wind and salt spray can make paper wet, weak, and torn very quickly.",
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


def dump_trace(world: Ship) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        lines.append(f"  {e.id:12} ({e.kind:9}) meters={meters} memes={memes}")
    lines.append(f"  facts={world.facts}")
    return "\n".join(lines)


def generate(params: StoryParams) -> StorySample:
    world = tell(params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(),
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


CURATED = [StoryParams()]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        triples = asp_valid_combos()
        print(f"{len(triples)} compatible combos:")
        for t in triples:
            print("  ", t)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        for i in range(args.n):
            params = resolve_params(args, random.Random(base_seed + i))
            sample = generate(params)
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

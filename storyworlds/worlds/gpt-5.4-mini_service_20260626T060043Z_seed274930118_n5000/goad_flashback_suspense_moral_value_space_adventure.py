#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260626T060043Z_seed274930118_n5000/goad_flashback_suspense_moral_value_space_adventure.py
==============================================================================================================================

A small storyworld in a space-adventure style about a child crew member, a
careful mission, a goad into action, a flashback, and a moral-value decision.

Premise:
- A young astronaut on a small ship wants to explore a strange signal.
- A mentor warns them that the signal might be a trap or a stranded helper.
- A flashback reminds the hero why they promised to help carefully.
- Suspense rises as the ship approaches the unknown.
- The hero chooses a moral action that proves kindness matters more than haste.

This script keeps the story grounded in state changes:
- meters describe physical quantities like fuel, distance, hull light, beacon charge
- memes describe emotions and social forces like courage, fear, trust, guilt, hope

The featured "goad" is a social push that moves the hero from hesitation into
action. The flashback changes emotional state and explains why the choice matters.
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
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def m(self, key: str) -> float:
        return self.meters.get(key, 0.0)

    def e(self, key: str) -> float:
        return self.memes.get(key, 0.0)

    def pronoun(self, case: str = "subject") -> str:
        if self.kind == "character" and self.type in {"girl", "woman", "captain"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.kind == "character" and self.type in {"boy", "man", "pilot"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class Ship:
    name: str
    place: str
    sector: str
    danger: str


class World:
    def __init__(self, ship: Ship) -> None:
        self.ship = ship
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.trace: list[str] = []
        self.fired: set[tuple] = set()

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str) -> Entity:
        return self.entities[eid]

    def chars(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.kind == "character"]

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)
            self.trace.append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)

    def copy(self) -> "World":
        import copy as _copy
        w = World(self.ship)
        w.entities = _copy.deepcopy(self.entities)
        w.paragraphs = [[]]
        w.facts = dict(self.facts)
        w.fired = set(self.fired)
        return w


@dataclass
class StoryParams:
    place: str
    hero: str
    hero_type: str
    mentor: str
    mentor_type: str
    signal: str
    seed: Optional[int] = None


PLACES = {
    "orbital_outpost": Ship("Bright Finch", "Orbital Outpost 7", "blue ring sector", "a faint distress ping"),
    "moon_port": Ship("Bright Finch", "Moon Port Nine", "silver dust sector", "a blinking beacon"),
    "asteroid_dock": Ship("Bright Finch", "Asteroid Dock K-3", "rock garden sector", "a wobbly rescue light"),
}

HEROES = [
    ("Ari", "boy"),
    ("Mina", "girl"),
    ("Tess", "girl"),
    ("Jory", "boy"),
]

MENTORS = [
    ("Captain Vale", "captain"),
    ("Pilot Sera", "pilot"),
]

SIGNALS = {
    "distress": {
        "label": "distress ping",
        "mystery": "someone might be asking for help",
        "risk": "the ping could be a trap in the dark",
        "place_word": "signal",
    },
    "beacon": {
        "label": "blinking beacon",
        "mystery": "it might guide lost ships home",
        "risk": "it could lead them into broken rocks",
        "place_word": "beacon",
    },
    "light": {
        "label": "rescue light",
        "mystery": "a tiny ship might be stranded nearby",
        "risk": "the light could vanish before anyone arrives",
        "place_word": "light",
    },
}

EVENTS = {
    "drift": "drifting through the quiet dark",
    "scan": "scanning the dim corridor",
    "approach": "slowing the ship near the unknown glow",
}

KNOWLEDGE = {
    "space": [
        ("What is space?", "Space is the huge dark area beyond Earth's air, where stars, planets, and ships can travel."),
    ],
    "beacon": [
        ("What does a beacon do?", "A beacon sends out a light or signal so others can find a place or a ship."),
    ],
    "distress": [
        ("What is a distress signal?", "A distress signal is a message that says someone needs help."),
    ],
    "help": [
        ("Why is helping others important?", "Helping others is important because people feel safer and kinder when they support one another."),
    ],
    "courage": [
        ("What is courage?", "Courage means doing the right thing even when you feel nervous."),
    ],
}


class Rule:
    def __init__(self, name: str, apply):
        self.name = name
        self.apply = apply


def _r_suspense(world: World) -> list[str]:
    out: list[str] = []
    for ch in world.chars():
        if ch.e("fear") < THRESHOLD or ch.e("curiosity") < THRESHOLD:
            continue
        sig = ("suspense", ch.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        ch.memes["suspense"] = ch.e("suspense") + 1
        out.append(f"The unknown felt heavy, and {ch.id} held a careful breath.")
    return out


def _r_moral_value(world: World) -> list[str]:
    out: list[str] = []
    for ch in world.chars():
        if ch.e("compassion") < THRESHOLD or ch.e("guilt") < THRESHOLD:
            continue
        sig = ("moral", ch.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        ch.memes["resolve"] = ch.e("resolve") + 1
        out.append(f"{ch.id} remembered that kindness mattered more than winning or being first.")
    return out


RULES = [Rule("suspense", _r_suspense), Rule("moral_value", _r_moral_value)]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in RULES:
            xs = rule.apply(world)
            if xs:
                produced.extend(xs)
                changed = True
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def flashback(world: World, hero: Entity, mentor: Entity, signal_cfg: dict) -> None:
    hero.memes["memory"] = hero.e("memory") + 1
    hero.memes["compassion"] = hero.e("compassion") + 1
    world.say(
        f"Long ago, {hero.id} and {mentor.id} had found a lonely drone with a cracked light, "
        f"and they had promised to help first and ask questions after."
    )
    world.say(
        f"That promise returned now, bright as a small lamp in {hero.pronoun('possessive')} chest."
    )


def setup(world: World, hero: Entity, mentor: Entity, signal_cfg: dict) -> None:
    world.say(
        f"On the ship {world.ship.name}, {hero.id} was a young {hero.type} who loved every odd star on the map."
    )
    world.say(
        f"{hero.pronoun('subject').capitalize()} noticed the {signal_cfg['label']} near {world.ship.place}, and {mentor.id} grew quiet."
    )


def goad(world: World, mentor: Entity, hero: Entity, signal_cfg: dict) -> None:
    hero.memes["hesitation"] = hero.e("hesitation") + 1
    hero.memes["fear"] = hero.e("fear") + 1
    world.say(
        f"{mentor.id} gave a small goad and said, “If we wait too long, the {signal_cfg['label']} may fade.”"
    )
    world.say(
        f"{hero.id} wanted to move, but the dark corridor made {hero.pronoun('object')} unsure."
    )


def approach(world: World, hero: Entity, mentor: Entity, signal_cfg: dict) -> None:
    hero.meters["distance_to_signal"] = max(0.0, hero.meters.get("distance_to_signal", 3.0) - 1.0)
    hero.memes["curiosity"] = hero.e("curiosity") + 1
    world.say(
        f"They began {EVENTS['approach']}, and the {signal_cfg['label']} grew clearer ahead."
    )
    propagate(world, narrate=True)


def choose_kindness(world: World, hero: Entity, mentor: Entity, signal_cfg: dict) -> None:
    hero.memes["compassion"] = hero.e("compassion") + 1
    hero.memes["guilt"] = hero.e("guilt") + 1
    hero.meters["beacon_charge"] = hero.meters.get("beacon_charge", 0.0) + 1.0
    world.say(
        f"{hero.id} chose to answer the {signal_cfg['label']} with a rescue beam instead of rushing past it."
    )
    world.say(
        f"The ship sent a warm message and a guiding light, so whoever was out there would know help had come."
    )


def resolve(world: World, hero: Entity, mentor: Entity, signal_cfg: dict) -> None:
    hero.memes["fear"] = max(0.0, hero.e("fear") - 1.0)
    hero.memes["hope"] = hero.e("hope") + 1
    world.say(
        f"When the reply blinked back, {hero.id} saw a tiny salvage pod drifting safe in the beam."
    )
    world.say(
        f"{mentor.id} smiled, because the goad had led to bravery, the flashback had led to memory, "
        f"and memory had led to the right choice."
    )
    world.say(
        f"At last, the {signal_cfg['label']} was not a mystery to fear but a chance to help."
    )


def tell(ship: Ship, hero_name: str, hero_type: str, mentor_name: str, mentor_type: str, signal_key: str) -> World:
    world = World(ship)
    signal_cfg = SIGNALS[signal_key]
    hero = world.add(Entity(id=hero_name, kind="character", type=hero_type))
    mentor = world.add(Entity(id=mentor_name, kind="character", type=mentor_type))

    hero.meters["distance_to_signal"] = 3.0
    hero.meters["ship_light"] = 1.0
    hero.memes["curiosity"] = 1.0
    hero.memes["fear"] = 0.0
    mentor.memes["trust"] = 1.0

    world.facts.update(hero=hero, mentor=mentor, signal=signal_cfg, ship=ship)

    setup(world, hero, mentor, signal_cfg)
    world.para()
    world.say(f"{EVENTS['drift'].capitalize()}, the crew listened to the faint sound of the {signal_cfg['label']}.")
    goad(world, mentor, hero, signal_cfg)
    flashback(world, hero, mentor, signal_cfg)
    world.para()
    approach(world, hero, mentor, signal_cfg)
    choose_kindness(world, hero, mentor, signal_cfg)
    resolve(world, hero, mentor, signal_cfg)

    world.facts["resolved"] = True
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    mentor = f["mentor"]
    signal = f["signal"]["label"]
    return [
        f'Write a short space adventure for a small child about a {hero.type} who hears a {signal} and decides to help.',
        f'Tell a suspenseful but gentle story where {hero.id} gets a goad from {mentor.id}, remembers a flashback, and makes a kind choice.',
        f'Write a simple story in space that shows moral value by helping before hurrying away.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    mentor = f["mentor"]
    signal = f["signal"]["label"]
    place = f["ship"].place
    qa = [
        QAItem(
            question=f"Who is the story about on {f['ship'].name} near {place}?",
            answer=f"The story is about {hero.id}, a young {hero.type}, and {mentor.id}, who watches over the ship.",
        ),
        QAItem(
            question=f"What did {mentor.id} want {hero.id} to do about the {signal}?",
            answer=f"{mentor.id} wanted {hero.id} to act carefully instead of waiting too long, because the {signal} might fade or hide someone who needed help.",
        ),
        QAItem(
            question=f"What important memory did {hero.id} have before choosing what to do?",
            answer=f"{hero.id} remembered an earlier promise to help first when a lonely drone needed care, and that flashback made the right choice feel clear.",
        ),
        QAItem(
            question=f"How did the story end after {hero.id} heard the goad and thought about kindness?",
            answer=f"It ended with {hero.id} sending a rescue beam, helping the drifting pod, and proving that helping mattered more than rushing past.",
        ),
    ]
    return qa


def world_knowledge_qa(world: World) -> list[QAItem]:
    tags = {world.facts["signal"]["place_word"], "space", "help", "courage"}
    out: list[QAItem] = []
    for tag in tags:
        for q, a in KNOWLEDGE.get(tag, []):
            out.append(QAItem(question=q, answer=a))
    return out


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


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        meters = {k: round(v, 3) for k, v in e.meters.items() if v}
        memes = {k: round(v, 3) for k, v in e.memes.items() if v}
        parts = []
        if meters:
            parts.append(f"meters={meters}")
        if memes:
            parts.append(f"memes={memes}")
        lines.append(f"  {e.id:12} ({e.type:8}) {' '.join(parts)}")
    lines.append(f"  fired rules: {sorted({n for n, *_ in world.fired})}")
    return "\n".join(lines)


ASP_RULES = r"""
hero(H) :- character(H).
mentor(M) :- character(M).

suspense(H) :- fear(H), curiosity(H).
moral_value(H) :- compassion(H), guilt(H).

shown_suspense(H) :- suspense(H).
shown_moral_value(H) :- moral_value(H).

valid_story(Place, Signal, HeroType) :- place(Place), signal(Signal), hero_type(HeroType).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for key, ship in PLACES.items():
        lines.append(asp.fact("place", key))
        lines.append(asp.fact("ship_name", key, ship.name))
        lines.append(asp.fact("sector", key, ship.sector))
        lines.append(asp.fact("danger", key, ship.danger))
    for key in SIGNALS:
        lines.append(asp.fact("signal", key))
    for name, typ in HEROES:
        lines.append(asp.fact("hero_type", typ))
        lines.append(asp.fact("character", name))
    for name, typ in MENTORS:
        lines.append(asp.fact("mentor_type", typ))
        lines.append(asp.fact("character", name))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    # Simple parity check: the ASP twin should at least admit all declared story ingredients.
    model = asp.one_model(asp_program("#show place/1.\n#show signal/1.\n#show hero_type/1.\n"))
    atoms = set(asp.atoms(model, "place")) | set(asp.atoms(model, "signal")) | set(asp.atoms(model, "hero_type"))
    py = {("place", k) for k in PLACES} | {("signal", k) for k in SIGNALS} | {("hero_type", t) for _, t in HEROES}
    if atoms == py:
        print(f"OK: ASP twin matches registry facts ({len(py)} facts).")
        return 0
    print("MISMATCH between ASP twin and registry facts.")
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Space-adventure storyworld with goad, flashback, suspense, and moral value.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--hero")
    ap.add_argument("--hero-type", choices=sorted({t for _, t in HEROES}))
    ap.add_argument("--mentor")
    ap.add_argument("--mentor-type", choices=sorted({t for _, t in MENTORS}))
    ap.add_argument("--signal", choices=SIGNALS)
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
    place = args.place or rng.choice(list(PLACES))
    hero, hero_type = (args.hero, args.hero_type)
    if not hero:
        hero, hero_type = rng.choice(HEROES)
    elif not hero_type:
        hero_type = rng.choice(sorted({t for _, t in HEROES}))
    mentor = args.mentor or rng.choice([m for m, _ in MENTORS])
    mentor_type = args.mentor_type or rng.choice(sorted({t for _, t in MENTORS}))
    signal = args.signal or rng.choice(list(SIGNALS))
    return StoryParams(place=place, hero=hero, hero_type=hero_type, mentor=mentor, mentor_type=mentor_type, signal=signal)


def generate(params: StoryParams) -> StorySample:
    ship = PLACES[params.place]
    world = tell(ship, params.hero, params.hero_type, params.mentor, params.mentor_type, params.signal)
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
    StoryParams(place="orbital_outpost", hero="Ari", hero_type="boy", mentor="Captain Vale", mentor_type="captain", signal="distress"),
    StoryParams(place="moon_port", hero="Mina", hero_type="girl", mentor="Pilot Sera", mentor_type="pilot", signal="beacon"),
    StoryParams(place="asteroid_dock", hero="Tess", hero_type="girl", mentor="Captain Vale", mentor_type="captain", signal="light"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show place/1.\n#show signal/1.\n#show hero_type/1.\n"))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        model = asp.one_model(asp_program("#show place/1.\n#show signal/1.\n#show hero_type/1.\n"))
        print("ASP facts available:")
        for atom in sorted(set(asp.atoms(model, "place"))):
            print("place", atom)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 50, 50):
            p = resolve_params(args, random.Random(base_seed + i))
            p.seed = base_seed + i
            s = generate(p)
            i += 1
            if s.story in seen:
                continue
            seen.add(s.story)
            samples.append(s)

    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        header = f"### variant {i + 1}" if len(samples) > 1 and not args.all else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()

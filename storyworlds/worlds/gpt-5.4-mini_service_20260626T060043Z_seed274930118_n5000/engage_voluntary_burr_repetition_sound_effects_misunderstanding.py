#!/usr/bin/env python3
"""
A small pirate-tale storyworld with voluntary helping, repeated sound effects,
and a misunderstanding that gets cleared up by a gentle explanation.

The seed story inspiration:
- A child pirate wants to help the crew.
- A crank or winch makes a burr-burr sound.
- Another pirate misunderstands the sound and the action.
- The misunderstanding is resolved, and the crew happily engages the work together.

This script models the premise as a tiny simulation:
- characters have meters and memes
- the child can choose a voluntary action
- a repeated sound effect can raise confusion
- confusion can become a misunderstanding
- explanation clears the confusion and ends the story in a calm, friendly image
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


# ---------------------------------------------------------------------------
# World entities
# ---------------------------------------------------------------------------
@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    traits: list[str] = field(default_factory=list)
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def __post_init__(self) -> None:
        for key in ["tired", "ready", "work", "confusion", "joy", "trust", "pride"]:
            self.meters.setdefault(key, 0.0)
            self.memes.setdefault(key, 0.0)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "woman", "mother", "captain"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man", "father", "mate", "pirate"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class Place:
    name: str
    feature: str
    can_engage: set[str] = field(default_factory=set)


@dataclass
class Device:
    id: str
    label: str
    action_noun: str
    sound: str
    repeated_sound: str
    causes_confusion: bool = True


@dataclass
class World:
    place: Place
    entities: dict[str, Entity] = field(default_factory=dict)
    facts: dict = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    fired: set[tuple] = field(default_factory=set)

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

    def copy(self) -> "World":
        import copy

        clone = World(self.place)
        clone.entities = copy.deepcopy(self.entities)
        clone.facts = copy.deepcopy(self.facts)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        return clone


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------
PLACES = {
    "dock": Place(name="the dock", feature="a rope ladder and a salty rope coil", can_engage={"winch"}),
    "deck": Place(name="the deck", feature="a creaky mast and a shiny brass bell", can_engage={"bell", "winch"}),
    "harbor": Place(name="the harbor", feature="quiet water and bobbing boats", can_engage={"bell"}),
}

DEVICES = {
    "winch": Device(
        id="winch",
        label="the winch",
        action_noun="engage the winch",
        sound="burr",
        repeated_sound="burr-burr-burr",
    ),
    "bell": Device(
        id="bell",
        label="the bell",
        action_noun="engage the bell rope",
        sound="ding",
        repeated_sound="ding-ding",
        causes_confusion=False,
    ),
}

HERO_NAMES = ["Mira", "Jory", "Nell", "Pip", "Tess", "Cleo"]
CREW_ROLES = ["captain", "mate", "sailor", "pirate"]


@dataclass
class StoryParams:
    place: str
    device: str
    hero_name: str
    hero_type: str
    crew_type: str
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# Reasonableness gate
# ---------------------------------------------------------------------------
def valid_combos() -> list[tuple[str, str]]:
    out = []
    for place_id, place in PLACES.items():
        for device_id in DEVICES:
            if device_id in place.can_engage:
                out.append((place_id, device_id))
    return out


def explain_rejection(place_id: str, device_id: str) -> str:
    place = PLACES[place_id]
    device = DEVICES[device_id]
    return (
        f"(No story: {device.label} cannot be engaged at {place.name}. "
        f"That would not fit the ship's work, so the tale would not have a fair turn.)"
    )


# ---------------------------------------------------------------------------
# Simulation
# ---------------------------------------------------------------------------
def setup_world(params: StoryParams) -> World:
    world = World(PLACES[params.place])

    hero = world.add(
        Entity(
            id=params.hero_name,
            kind="character",
            type=params.hero_type,
            traits=["little", "curious", "helpful"],
        )
    )
    crew = world.add(
        Entity(
            id="Crewmate",
            kind="character",
            type=params.crew_type,
            label="the crew mate",
            traits=["seasoned", "careful"],
        )
    )
    device = world.add(
        Entity(
            id=params.device,
            kind="thing",
            type="device",
            label=DEVICES[params.device].label,
            phrase=DEVICES[params.device].label,
            owner=crew.id,
        )
    )
    world.facts.update(hero=hero, crew=crew, device=device, params=params)
    return world


def predict_confusion(world: World) -> bool:
    device = world.get(world.facts["params"].device)
    return DEVICES[device.id].causes_confusion


def start_story(world: World) -> None:
    hero: Entity = world.facts["hero"]
    crew: Entity = world.facts["crew"]
    device: Entity = world.facts["device"]
    place = world.place

    world.say(
        f"At {place.name}, {hero.id} was a little {hero.type} with a bright grin and a brave heart."
    )
    world.say(
        f"{hero.id} loved the salty wind, the swaying ropes, and the way every creak on the ship sounded like an adventure."
    )
    world.say(
        f"Nearby, {crew.label} kept {device.label} ready for work beside {place.feature}."
    )


def voluntary_help(world: World) -> None:
    hero: Entity = world.facts["hero"]
    device: Entity = world.facts["device"]
    hero.memes["joy"] += 1
    hero.memes["trust"] += 1
    hero.meters["ready"] += 1
    world.say(
        f"Without being asked, {hero.id} stepped closer and said, "
        f'"I want to help. I will {DEVICES[device.id].action_noun}!"'
    )
    world.say(
        f"{hero.id} reached for the handle all by {hero.pronoun('possessive')} self, feeling proud to help the crew."
    )


def sound_effects(world: World) -> None:
    hero: Entity = world.facts["hero"]
    device: Entity = world.facts["device"]
    crew: Entity = world.facts["crew"]

    if predict_confusion(world):
        world.say(
            f"The handle went {DEVICES[device.id].sound}! Then again: {DEVICES[device.id].sound}! "
            f"The little machine answered with {DEVICES[device.id].repeated_sound}."
        )
        hero.meters["work"] += 1
        hero.memes["pride"] += 1
        crew.memes["confusion"] += 1
    else:
        world.say(
            f"The rope went {DEVICES[device.id].sound}, nice and neat, and the deck stayed calm."
        )


def misunderstanding(world: World) -> None:
    hero: Entity = world.facts["hero"]
    crew: Entity = world.facts["crew"]
    device: Entity = world.facts["device"]

    if crew.memes["confusion"] < THRESHOLD:
        return

    world.say(
        f"{crew.label} frowned and said, "
        f'"Wait now — did you say burr? Are you saying the rope is broken, or that you are cold?"'
    )
    world.say(
        f"{hero.id} blinked. That was not what {hero.pronoun('subject')} meant at all."
    )
    hero.memes["confusion"] += 1
    world.facts["misunderstanding"] = True


def clarify(world: World) -> None:
    hero: Entity = world.facts["hero"]
    crew: Entity = world.facts["crew"]
    device: Entity = world.facts["device"]

    if not world.facts.get("misunderstanding"):
        return

    world.say(
        f"{hero.id} laughed and pointed at {device.label}. "
        f'"No, no — I meant I wanted to help by {DEVICES[device.id].action_noun}!"'
    )
    world.say(
        f"The crew mate smiled at the answer, because the repeated {DEVICES[device.id].repeated_sound} was only the machine doing its job."
    )
    crew.memes["confusion"] = 0.0
    crew.memes["joy"] += 1
    hero.memes["confusion"] = 0.0
    hero.memes["joy"] += 1
    hero.memes["trust"] += 1
    world.facts["resolved"] = True


def finish(world: World) -> None:
    hero: Entity = world.facts["hero"]
    crew: Entity = world.facts["crew"]
    device: Entity = world.facts["device"]

    world.say(
        f"Together they turned the handle again, and this time the work went smoothly: {DEVICES[device.id].repeated_sound}, "
        f"then steady and calm."
    )
    world.say(
        f"{hero.id} beamed beside {crew.label}, happy to have helped, and the ship felt ready to sail."
    )


def tell(params: StoryParams) -> World:
    world = setup_world(params)
    start_story(world)
    world.para()
    voluntary_help(world)
    sound_effects(world)
    misunderstanding(world)
    world.para()
    clarify(world)
    finish(world)
    return world


# ---------------------------------------------------------------------------
# QA
# ---------------------------------------------------------------------------
def generation_prompts(world: World) -> list[str]:
    p = world.facts["params"]
    return [
        f'Write a short pirate tale for a young child about {p.hero_name} helping on {PLACES[p.place].name}, with a repeated "{DEVICES[p.device].sound}" sound.',
        f"Tell a gentle shipboard story where a small {p.hero_type} helps voluntarily, but a crew mate first misunderstands the burr-burr sound.",
        f'Write a simple pirate story that includes an act of voluntary help, sound effects like "{DEVICES[p.device].repeated_sound}", and a cleared-up misunderstanding.',
    ]


def story_qa(world: World) -> list[QAItem]:
    p = world.facts["params"]
    hero: Entity = world.facts["hero"]
    crew: Entity = world.facts["crew"]
    device: Entity = world.facts["device"]
    return [
        QAItem(
            question=f"Why did {p.hero_name} go up to {device.label}?",
            answer=f"{p.hero_name} wanted to help on purpose, so {hero.pronoun('subject')} chose to {DEVICES[p.device].action_noun} without being asked.",
        ),
        QAItem(
            question=f"What sound did the machine make while {p.hero_name} worked?",
            answer=f"It went {DEVICES[p.device].repeated_sound}, which is a repeated sound effect that made the moment feel lively.",
        ),
        QAItem(
            question=f"Why did {crew.label} get confused at first?",
            answer=f"{crew.label} heard the burr-like sound and wondered if something was broken or if {p.hero_name} meant something else, so there was a misunderstanding.",
        ),
        QAItem(
            question=f"How was the misunderstanding fixed?",
            answer=f"{p.hero_name} explained the meaning clearly, and then {crew.label} understood that the sound was only the work of {device.label}.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does it mean to help voluntarily?",
            answer="It means choosing to help on your own, without someone forcing you.",
        ),
        QAItem(
            question="What is a misunderstanding?",
            answer="A misunderstanding happens when someone thinks a message means one thing, but it really means another.",
        ),
        QAItem(
            question="Why do stories repeat sound effects like burr-burr?",
            answer="Repetition of sound effects can make the action feel louder, funnier, or more lively to read aloud.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== Prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== Story QA ==")
    for qa in sample.story_qa:
        lines.append(f"Q: {qa.question}")
        lines.append(f"A: {qa.answer}")
    lines.append("")
    lines.append("== World QA ==")
    for qa in sample.world_qa:
        lines.append(f"Q: {qa.question}")
        lines.append(f"A: {qa.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for ent in world.entities.values():
        meters = {k: v for k, v in ent.meters.items() if v}
        memes = {k: v for k, v in ent.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        if bits:
            lines.append(f"{ent.id}: " + ", ".join(bits))
        else:
            lines.append(f"{ent.id}:")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
place(dock). place(deck). place(harbor).
device(winch). device(bell).
can_engage(dock,winch). can_engage(deck,winch). can_engage(deck,bell). can_engage(harbor,bell).

valid(Place,Device) :- can_engage(Place,Device).
#show valid/2.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for pid in PLACES:
        lines.append(asp.fact("place", pid))
    for did in DEVICES:
        lines.append(asp.fact("device", did))
    for pid, place in PLACES.items():
        for did in place.can_engage:
            lines.append(asp.fact("can_engage", pid, did))
    return "\n".join(lines)


def asp_program(show: str = "#show valid/2.") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program())
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    py = set(valid_combos())
    asp_set = set(asp_valid_combos())
    if py == asp_set:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and Python reasonableness gate:")
    if py - asp_set:
        print("  only in python:", sorted(py - asp_set))
    if asp_set - py:
        print("  only in clingo:", sorted(asp_set - py))
    return 1


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Pirate tale storyworld: voluntary help, burr sounds, and misunderstanding.")
    ap.add_argument("--place", choices=PLACES.keys())
    ap.add_argument("--device", choices=DEVICES.keys())
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--crew", choices=CREW_ROLES)
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
    combos = valid_combos()
    if args.place or args.device:
        combos = [
            c for c in combos
            if (args.place is None or c[0] == args.place)
            and (args.device is None or c[1] == args.device)
        ]
    if not combos:
        raise StoryError("(No valid pirate combination matches the given options.)")
    place, device = rng.choice(sorted(combos))
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(HERO_NAMES)
    crew = args.crew or rng.choice(CREW_ROLES)
    hero_type = "girl" if gender == "girl" else "boy"
    return StoryParams(place=place, device=device, hero_name=name, hero_type=hero_type, crew_type=crew)


def generate(params: StoryParams) -> StorySample:
    world = tell(params)
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
    StoryParams(place="deck", device="winch", hero_name="Mira", hero_type="girl", crew_type="captain"),
    StoryParams(place="dock", device="winch", hero_name="Pip", hero_type="boy", crew_type="mate"),
    StoryParams(place="harbor", device="bell", hero_name="Nell", hero_type="girl", crew_type="sailor"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program())
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible place/device combos:\n")
        for place, device in combos:
            print(f"  {place:8} {device}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 40, 40):
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
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.hero_name}: {p.device} at {p.place}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()

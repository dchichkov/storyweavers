#!/usr/bin/env python3
"""
Story world: a pirate tale about a compulsive little sailor, a blanket quest,
and a happy ending.

The seed premise:
- A small pirate crew sails to fetch a beloved blanket.
- The captain is compulsive about keeping things in order.
- The quest creates tension when the blanket is missing on a windy night.
- The crew solves it with planning, teamwork, and a happy ending.
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
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "woman", "mother", "captain"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man", "father", "matey"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class Place:
    id: str
    label: str
    weather: str = "windy"
    sea: bool = True


@dataclass
class Quest:
    id: str
    object_label: str
    object_phrase: str
    needed_at: str
    clue: str
    danger: str
    turn: str
    reward: str
    tags: set[str] = field(default_factory=set)


@dataclass
class StoryParams:
    place: str
    quest: str
    name: str
    gender: str
    captain: str
    seed: Optional[int] = None


class World:
    def __init__(self, place: Place) -> None:
        self.place = place
        self.entities: dict[str, Entity] = {}
        self.facts: dict = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
        self.trace_log: list[str] = []

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
        clone = World(self.place)
        clone.entities = {
            k: Entity(
                id=v.id, kind=v.kind, type=v.type, label=v.label, phrase=v.phrase,
                owner=v.owner, caretaker=v.caretaker, worn_by=v.worn_by,
                meters=dict(v.meters), memes=dict(v.memes),
            )
            for k, v in self.entities.items()
        }
        clone.fired = set(self.fired)
        return clone


PLACES = {
    "harbor": Place(id="harbor", label="the harbor", weather="windy", sea=True),
    "island": Place(id="island", label="the little island", weather="stormy", sea=True),
    "cove": Place(id="cove", label="the moon cove", weather="breezy", sea=True),
}

QUESTS = {
    "blanket": Quest(
        id="blanket",
        object_label="blanket",
        object_phrase="a soft blue blanket",
        needed_at="the sleeping deck",
        clue="a lantern glint on a rope pile",
        danger="the night breeze made the bunk cold",
        turn="they followed the clue to the laundry chest",
        reward="warm sleep",
        tags={"blanket", "cloth", "warmth"},
    ),
    "map": Quest(
        id="map",
        object_label="map",
        object_phrase="an old treasure map",
        needed_at="the captain's table",
        clue="a flutter under a crate",
        danger="the route would be lost without it",
        turn="they found it tucked under a compass",
        reward="a clear course home",
        tags={"map", "treasure", "paper"},
    ),
}

GIRL_NAMES = ["Mira", "Nina", "Luna", "Ivy", "Tess"]
BOY_NAMES = ["Finn", "Pip", "Rowan", "Jace", "Kit"]
TRAITS = ["curious", "brave", "cheerful", "stubborn"]

ASP_RULES = r"""
quest_has_object(blanket).
quest_has_object(map).

needs_warmth(blanket).
needs_navigation(map).

valid_story(P, Q) :- place(P), quest(Q).
"""

def asp_facts() -> str:
    import storyworlds.asp as asp
    lines = []
    for p in PLACES:
        lines.append(asp.fact("place", p))
    for q in QUESTS:
        lines.append(asp.fact("quest", q))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import storyworlds.asp as asp
    model = asp.one_model(asp_program("#show valid_story/2."))
    atoms = set(asp.atoms(model, "valid_story"))
    py = {(p, q) for p in PLACES for q in QUESTS}
    if atoms == py:
        print(f"OK: clingo gate matches Python ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and Python.")
    print("only in clingo:", sorted(atoms - py))
    print("only in python:", sorted(py - atoms))
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Pirate tale story world with a blanket quest.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--quest", choices=QUESTS)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--name")
    ap.add_argument("--captain", choices=["captain", "matey"], default="captain")
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


def valid_combos() -> list[tuple[str, str]]:
    return [(p, q) for p in PLACES for q in QUESTS]


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    combos = valid_combos()
    combos = [
        (p, q) for (p, q) in combos
        if (args.place is None or p == args.place)
        and (args.quest is None or q == args.quest)
    ]
    if not combos:
        raise StoryError("No valid pirate quest matches those options.")
    place, quest = rng.choice(combos)
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    captain = args.captain
    return StoryParams(place=place, quest=quest, name=name, gender=gender, captain=captain)


def _story_intro(world: World, hero: Entity, quest: Quest) -> None:
    world.say(
        f"On {world.place.label}, a little {hero.type} named {hero.id} served aboard a tiny ship."
        f" {hero.pronoun().capitalize()} was compulsive about neat ropes, tidy sails, and a folded bunk blanket."
    )
    world.say(
        f"{hero.pronoun().capitalize()} loved {quest.object_label} quests, because every clue felt like a treasure wave."
    )


def _story_turn(world: World, hero: Entity, captain: Entity, quest: Quest) -> None:
    world.para()
    world.say(
        f"One windy night, the deck turned chilly, and {quest.danger}."
        f" {hero.id} wanted {quest.object_phrase} right away, but it was missing."
    )
    hero.memes["worry"] = hero.memes.get("worry", 0) + 1
    captain.memes["concern"] = captain.memes.get("concern", 0) + 1
    world.say(
        f'"We must find the {quest.object_label}," said {captain.pronoun()}.'
        f' "A cozy ship is a happy ship."'
    )
    world.say(
        f"{hero.id} straightened the lantern, checked the mast, and followed {quest.clue}."
    )


def _story_resolution(world: World, hero: Entity, captain: Entity, quest: Quest) -> None:
    world.para()
    hero.memes["joy"] = hero.memes.get("joy", 0) + 1
    captain.memes["joy"] = captain.memes.get("joy", 0) + 1
    world.say(
        f"At last, {quest.turn}, and {hero.id} found {quest.object_phrase} tucked safe and dry."
    )
    world.say(
        f"{hero.id} shook it out, wrapped it around {hero.pronoun('object')}, and laughed."
        f" Soon the whole crew had {quest.reward}, and the ship felt warm again."
    )
    world.say(
        f"That night, the blanket stayed on the bunk, the ropes stayed neat, and the little pirate smiled into the dark."
    )


def tell(place: Place, quest: Quest, name: str, gender: str, captain_kind: str) -> World:
    world = World(place)
    hero = world.add(Entity(id=name, kind="character", type=gender, label=name))
    captain = world.add(Entity(id="Captain", kind="character", type=captain_kind, label="the captain"))
    blanket = world.add(Entity(
        id="blanket",
        kind="thing",
        type="blanket",
        label="blanket",
        phrase=quest.object_phrase,
        owner=hero.id,
        caretaker=captain.id,
    ))
    world.facts.update(hero=hero, captain=captain, blanket=blanket, quest=quest, place=place)
    _story_intro(world, hero, quest)
    _story_turn(world, hero, captain, quest)
    _story_resolution(world, hero, captain, quest)
    return world


def story_qa(world: World) -> list[QAItem]:
    hero = world.facts["hero"]
    captain = world.facts["captain"]
    quest = world.facts["quest"]
    return [
        QAItem(
            question=f"Who went on the {quest.object_label} quest?",
            answer=f"A little {hero.type} named {hero.id} went on the quest with {captain.label}.",
        ),
        QAItem(
            question=f"Why was {hero.id} looking for the {quest.object_label}?",
            answer=f"Because the night was windy and {quest.danger}, so {hero.id} needed the blanket to stay warm.",
        ),
        QAItem(
            question=f"What changed at the end of the story?",
            answer=f"The crew found the {quest.object_label}, the ship felt cozy again, and everyone got a happy ending.",
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    quest = world.facts["quest"]
    out = [
        QAItem(
            question="What is a blanket for?",
            answer="A blanket helps keep someone warm and cozy when they rest or sleep.",
        ),
        QAItem(
            question="What does compulsive mean?",
            answer="Compulsive means a person feels a very strong need to do something again and again, like keeping things very neat.",
        ),
    ]
    if "blanket" in quest.tags:
        out.append(QAItem(
            question="Why is a blanket useful on a windy ship?",
            answer="A blanket is useful because it helps block the cold and makes sleeping more comfortable.",
        ))
    return out


def format_qa(sample: StorySample) -> str:
    lines = ["== Story questions =="]
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== World questions ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- trace ---"]
    for e in world.entities.values():
        bits = []
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        lines.append(f"{e.id}: {e.type} {' '.join(bits)}")
    return "\n".join(lines)


def generate(params: StoryParams) -> StorySample:
    world = tell(PLACES[params.place], QUESTS[params.quest], params.name, params.gender, params.captain)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=[
            "Write a pirate tale about a compulsive little sailor and a missing blanket.",
            f"Tell a happy ending quest story set at {world.place.label}.",
        ],
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


CURATED = [
    StoryParams(place="harbor", quest="blanket", name="Mira", gender="girl", captain="captain"),
    StoryParams(place="cove", quest="blanket", name="Finn", gender="boy", captain="matey"),
]


def asp_valid_combos() -> list[tuple[str, str]]:
    import storyworlds.asp as asp
    model = asp.one_model(asp_program("#show valid_story/2."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


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
        for p, q in combos:
            print(f"  {p:8} {q}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 50, 50):
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

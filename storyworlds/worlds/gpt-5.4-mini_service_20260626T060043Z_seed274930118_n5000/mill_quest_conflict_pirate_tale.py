#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260626T060043Z_seed274930118_n5000/mill_quest_conflict_pirate_tale.py
===============================================================================================================

A small pirate-tale storyworld about a quest that runs into conflict at a mill.

Premise:
- A pirate crew must reach an old mill.
- The quest needs a simple treasure inside the mill.
- Another crew member worries the mill is guarded, so the captain must choose
  between rushing in and solving the conflict first.

The world model keeps physical meters and emotional memes:
- meters: distance, sail, wear, dust, treasure
- memes: hope, fear, conflict, trust, relief

The story is generated from state changes, not from a frozen paragraph.
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
# Data model
# ---------------------------------------------------------------------------
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

    def mm(self, key: str) -> float:
        return self.memes.get(key, 0.0)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "woman", "mother", "captain"}
        male = {"boy", "man", "father", "pirate", "sailor", "captain"}
        # Captain defaults to "they" in narration unless explicitly a person-type.
        if self.type in {"girl", "woman", "mother"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man", "father"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Place:
    id: str
    label: str
    kind: str = "place"
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)


@dataclass
class Quest:
    goal: str
    prize: str
    approach: str
    success_image: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Conflict:
    worry: str
    trigger: str
    risk: str
    turn: str
    tags: set[str] = field(default_factory=set)


class World:
    def __init__(self, place: Place, quest: Quest, conflict: Conflict) -> None:
        self.place = place
        self.quest = quest
        self.conflict = conflict
        self.entities: dict[str, Entity] = {}
        self.facts: dict[str, object] = {}
        self.paragraphs: list[list[str]] = [[]]

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
        import copy as _copy
        w = World(self.place, self.quest, self.conflict)
        w.entities = _copy.deepcopy(self.entities)
        w.facts = dict(self.facts)
        w.paragraphs = [[]]
        return w


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------
PLACES = {
    "mill": Place(id="mill", label="the old mill"),
    "harbor": Place(id="harbor", label="the windy harbor"),
    "islet": Place(id="islet", label="the tiny islet"),
}

QUESTS = {
    "lamp": Quest(
        goal="find the lantern hidden in the mill",
        prize="the lantern",
        approach="follow the moonlit path",
        success_image="the lantern glowing in a pirate hand",
        tags={"quest", "mill", "light"},
    ),
    "map": Quest(
        goal="recover the chart tucked inside the mill",
        prize="the chart",
        approach="climb the creaky stairs",
        success_image="the chart spread on a barrel",
        tags={"quest", "mill", "map"},
    ),
    "keys": Quest(
        goal="fetch the brass keys from the mill room",
        prize="the brass keys",
        approach="cross the rickety bridge",
        success_image="the brass keys jingling at the belt",
        tags={"quest", "mill", "keys"},
    ),
}

CONFLICTS = {
    "guard": Conflict(
        worry="the mill might be guarded by a stern watchman",
        trigger="a lantern bobbing in the window",
        risk="a loud dash could spoil the plan",
        turn="talk first, then step softly",
        tags={"conflict", "guard", "mill"},
    ),
    "storm": Conflict(
        worry="a storm might shake the mill boards",
        trigger="wind rattling the side door",
        risk="a rushed climb could send someone slipping",
        turn="wait for the gust to pass",
        tags={"conflict", "storm", "mill"},
    ),
    "share": Conflict(
        worry="two pirates might want the prize at once",
        trigger="both hands reaching for the same clue",
        risk="a squabble could break the search",
        turn="share the work and split the map",
        tags={"conflict", "crew", "quest"},
    ),
}

CREW_NAMES = ["Mara", "Jett", "Pia", "Rook", "Nell", "Toby", "Sail"]
CAPTAIN_NAMES = ["Captain Reed", "Captain Vela", "Captain Brine"]

TRAITS = ["bold", "curious", "brave", "wily", "cheerful"]


# ---------------------------------------------------------------------------
# Story parameters
# ---------------------------------------------------------------------------
@dataclass
class StoryParams:
    place: str
    quest: str
    conflict: str
    captain_name: str
    crew_name: str
    trait: str
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# Narrative helpers
# ---------------------------------------------------------------------------
def intro(world: World, captain: Entity, crew: Entity) -> None:
    world.say(
        f"{captain.id} was a {world.facts['trait']} pirate captain, and {crew.id} was "
        f"always ready for a sea-quest."
    )
    world.say(
        f"Together they loved a good {world.facts['quest'].goal.split(' ')[0]}-quest, "
        f"especially one that led to {world.place.label}."
    )


def set_sail(world: World, captain: Entity, crew: Entity) -> None:
    captain.meters["hope"] = captain.meters.get("hope", 0.0) + 1.0
    crew.meters["hope"] = crew.meters.get("hope", 0.0) + 1.0
    world.say(
        f"One dusk, they sailed toward {world.place.label}, with the spray cold on the bow "
        f"and the quest heavy in their thoughts."
    )


def approach_mill(world: World, captain: Entity, crew: Entity) -> None:
    captain.meters["distance"] = 0.0
    crew.meters["distance"] = 0.0
    world.say(
        f"The mill rose ahead, old and tall, with its boards creaking in the wind."
    )
    world.say(
        f"{world.facts['conflict'].worry.capitalize()}, and that made the captain slow down."
    )


def first_tension(world: World, captain: Entity, crew: Entity) -> None:
    captain.memes["hope"] = captain.memes.get("hope", 0.0) + 1.0
    crew.memes["fear"] = crew.memes.get("fear", 0.0) + 1.0
    world.say(
        f"{crew.id} pointed at {world.facts['conflict'].trigger}, and {crew.pronoun('subject')} "
        f"whispered that {world.facts['conflict'].risk}."
    )
    world.say(
        f"{captain.id} wanted to hurry, but the captain knew a quest could turn sour if "
        f"the crew arrived in a rush."
    )


def resolve_conflict(world: World, captain: Entity, crew: Entity) -> None:
    captain.memes["conflict"] = 0.0
    crew.memes["conflict"] = 0.0
    captain.memes["trust"] = captain.memes.get("trust", 0.0) + 1.0
    crew.memes["trust"] = crew.memes.get("trust", 0.0) + 1.0
    world.say(
        f"So {captain.id} chose a cleverer way: {world.facts['conflict'].turn}."
    )
    world.say(
        f"{crew.id} nodded, and the two pirates slipped through the mill together without a fuss."
    )


def complete_quest(world: World, captain: Entity, crew: Entity) -> None:
    prize = world.facts["quest"].prize
    captain.meters["treasure"] = captain.meters.get("treasure", 0.0) + 1.0
    crew.meters["treasure"] = crew.meters.get("treasure", 0.0) + 1.0
    captain.memes["relief"] = captain.memes.get("relief", 0.0) + 1.0
    crew.memes["relief"] = crew.memes.get("relief", 0.0) + 1.0
    world.say(
        f"Inside, they found {prize}, just where the clue had promised."
    )
    world.say(
        f"By sunrise, they were back on deck with {prize} safe and the mill behind them, "
        f"small against the brightening sky."
    )


def tell(place: Place, quest: Quest, conflict: Conflict, captain_name: str, crew_name: str, trait: str) -> World:
    world = World(place, quest, conflict)
    captain = world.add(Entity(id=captain_name, kind="character", type="captain", label="captain"))
    crew = world.add(Entity(id=crew_name, kind="character", type="pirate", label="crew mate"))
    captain.memes["hope"] = 0.0
    crew.memes["hope"] = 0.0

    world.facts.update(place=place, quest=quest, conflict=conflict, trait=trait,
                       captain=captain, crew=crew)

    intro(world, captain, crew)
    world.para()
    set_sail(world, captain, crew)
    approach_mill(world, captain, crew)
    world.para()
    first_tension(world, captain, crew)
    resolve_conflict(world, captain, crew)
    world.para()
    complete_quest(world, captain, crew)

    world.facts["resolved"] = True
    return world


# ---------------------------------------------------------------------------
# Q&A
# ---------------------------------------------------------------------------
def generation_prompts(world: World) -> list[str]:
    q = world.facts["quest"]
    c = world.facts["conflict"]
    return [
        f'Write a short pirate tale about a quest to {q.goal} and a conflict at {world.place.label}.',
        f"Tell a child-friendly story where a pirate captain and crew face {c.worry} before finding {q.prize}.",
        f"Write a small sea adventure with the words \"mill\", \"quest\", and \"conflict\".",
    ]


def story_qa(world: World) -> list[QAItem]:
    q = world.facts["quest"]
    c = world.facts["conflict"]
    captain = world.facts["captain"]
    crew = world.facts["crew"]
    return [
        QAItem(
            question=f"What was the pirate crew trying to do at {world.place.label}?",
            answer=f"They were trying to {q.goal}, and the journey led them to {world.place.label}.",
        ),
        QAItem(
            question=f"Why did {crew.id} worry near the mill?",
            answer=f"{crew.id} worried because {c.worry}. That made the quest feel tense for a moment.",
        ),
        QAItem(
            question=f"How did {captain.id} handle the conflict?",
            answer=f"{captain.id} chose to {c.turn}, and that helped the crew keep going together.",
        ),
        QAItem(
            question=f"What did they find when the quest was finished?",
            answer=f"They found {q.prize}, and at the end it was safe with the crew.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a mill?",
            answer="A mill is a building with big turning parts that can grind grain or make work happen with wind or water.",
        ),
        QAItem(
            question="What is a quest?",
            answer="A quest is a search for something important, like a treasure, a lost tool, or a needed clue.",
        ),
        QAItem(
            question="What is conflict in a story?",
            answer="Conflict is the problem or worry that makes the characters stop, think, and choose how to act.",
        ),
        QAItem(
            question="Why do pirates often work together?",
            answer="Pirates often work together because a ship is easier to handle when the crew shares the work and keeps watch.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
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
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
place(mill). place(harbor). place(islet).

quest(lamp). quest(map). quest(keys).
conflict(guard). conflict(storm). conflict(share).

at_mill(mill).
quest_needs_mill(lamp).
quest_needs_mill(map).
quest_needs_mill(keys).

valid_story(P, Q, C) :- place(P), quest(Q), conflict(C), at_mill(P), quest_needs_mill(Q).
#show valid_story/3.
"""


def asp_facts() -> str:
    import asp
    lines = []
    for p in PLACES:
        lines.append(asp.fact("place", p))
    for q in QUESTS:
        lines.append(asp.fact("quest", q))
    for c in CONFLICTS:
        lines.append(asp.fact("conflict", c))
    for p in PLACES:
        if p == "mill":
            lines.append(asp.fact("at_mill", p))
    for q in QUESTS:
        lines.append(asp.fact("quest_needs_mill", q))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_stories() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/3."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    py = {(p, q, c) for p in PLACES for q in QUESTS for c in CONFLICTS if p == "mill"}
    cl = set(asp_valid_stories())
    if py == cl:
        print(f"OK: clingo gate matches python gate ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and python gate:")
    print("python only:", sorted(py - cl))
    print("clingo only:", sorted(cl - py))
    return 1


# ---------------------------------------------------------------------------
# Generation and CLI
# ---------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A pirate quest storyworld with mill conflict.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--quest", choices=QUESTS)
    ap.add_argument("--conflict", choices=CONFLICTS)
    ap.add_argument("--captain-name")
    ap.add_argument("--crew-name")
    ap.add_argument("--trait", choices=TRAITS)
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
    place = args.place or "mill"
    quest = args.quest or rng.choice(list(QUESTS))
    conflict = args.conflict or rng.choice(list(CONFLICTS))
    captain_name = args.captain_name or rng.choice(CAPTAIN_NAMES)
    crew_name = args.crew_name or rng.choice(CREW_NAMES)
    trait = args.trait or rng.choice(TRAITS)
    if place != "mill":
        raise StoryError("This storyworld only supports the mill setting for the pirate tale.")
    return StoryParams(place=place, quest=quest, conflict=conflict,
                       captain_name=captain_name, crew_name=crew_name, trait=trait)


def generate(params: StoryParams) -> StorySample:
    world = tell(PLACES[params.place], QUESTS[params.quest], CONFLICTS[params.conflict],
                 params.captain_name, params.crew_name, params.trait)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for e in world.entities.values():
        lines.append(f"{e.id}: meters={e.meters} memes={e.memes}")
    return "\n".join(lines)


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
        print(asp_program("#show valid_story/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        stories = asp_valid_stories()
        print(f"{len(stories)} compatible stories:")
        for p, q, c in stories:
            print(f"  {p} {q} {c}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        curated = [
            StoryParams("mill", "lamp", "guard", "Captain Reed", "Mara", "bold"),
            StoryParams("mill", "map", "storm", "Captain Vela", "Rook", "curious"),
            StoryParams("mill", "keys", "share", "Captain Brine", "Pia", "wily"),
        ]
        samples = [generate(p) for p in curated]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 20):
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
            header = f"### {p.captain_name} / {p.crew_name} :: {p.quest} + {p.conflict}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""
Storyworld: a pirate tale with an alert, a gymnasium, a rogue, a moral value, and a quest.

A small classical simulation for a child-facing pirate story:
- A crew trains in the ship's gymnasium before a quest.
- An alert warns them that a rogue has slipped aboard.
- The captain must choose between suspicion and trust.
- The resolution proves a moral value: honesty and teamwork.

This file is self-contained except for the shared storyworld result containers
and the optional ASP helper.
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
# Content registries
# ---------------------------------------------------------------------------

@dataclass
class Place:
    id: str
    label: str
    detail: str
    affords: set[str] = field(default_factory=set)


@dataclass
class CharacterSpec:
    id: str
    kind: str
    type: str
    label: str
    trait: str
    moral_value: str
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)


@dataclass
class QuestSpec:
    id: str
    name: str
    goal: str
    danger: str
    reward: str
    clue: str


@dataclass
class RogueSpec:
    id: str
    label: str
    action: str
    motive: str
    caught_by: str


PLACES = {
    "ship_gym": Place(
        id="ship_gym",
        label="the ship's gymnasium",
        detail="The ship's gymnasium had rope ladders, wooden bars, and a place for practice swings.",
        affords={"train", "search", "speak"},
    ),
    "deck": Place(
        id="deck",
        label="the deck",
        detail="The deck was bright with sea spray and ready for a busy day.",
        affords={"alert", "search", "speak"},
    ),
    "cabin": Place(
        id="cabin",
        label="the cabin",
        detail="The cabin held maps, lanterns, and a small table for careful plans.",
        affords={"speak", "plan"},
    ),
}

HEROES = {
    "captain": CharacterSpec(
        id="captain",
        kind="character",
        type="captain",
        label="Captain Mira",
        trait="brave",
        moral_value="honesty",
        meters={"balance": 1.0},
        memes={"duty": 1.0, "trust": 1.0},
    ),
    "mate": CharacterSpec(
        id="mate",
        kind="character",
        type="mate",
        label="First Mate Finn",
        trait="busy",
        moral_value="teamwork",
        meters={"strength": 1.0},
        memes={"helpfulness": 1.0},
    ),
    "cook": CharacterSpec(
        id="cook",
        kind="character",
        type="cook",
        label="Cook Nia",
        trait="cheerful",
        moral_value="care",
        meters={"patience": 1.0},
        memes={"kindness": 1.0},
    ),
}

QUESTS = {
    "map": QuestSpec(
        id="map",
        name="the map quest",
        goal="find the lost star map",
        danger="a stormy shortcut",
        reward="a safe path to the hidden cove",
        clue="a silver compass",
    ),
    "island": QuestSpec(
        id="island",
        name="the island quest",
        goal="reach the island before sunset",
        danger="sharp rocks near the reef",
        reward="a chest of bright shells",
        clue="a red flag on the mast",
    ),
}

ROGUES = {
    "deckhand": RogueSpec(
        id="deckhand",
        label="a rogue deckhand",
        action="hide the compass",
        motive="to sneak a bigger share of the treasure",
        caught_by="the captain",
    ),
    "monkey": RogueSpec(
        id="monkey",
        label="a rogue monkey",
        action="snatch the map",
        motive="to steal shiny things for a nest",
        caught_by="the first mate",
    ),
}


# ---------------------------------------------------------------------------
# Result model
# ---------------------------------------------------------------------------

@dataclass
class StoryParams:
    place: str
    quest: str
    rogue: str
    hero: str
    seed: Optional[int] = None


@dataclass
class Entity:
    id: str
    kind: str
    type: str
    label: str
    trait: str = ""
    owner: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)


class World:
    def __init__(self, place: Place, quest: QuestSpec, rogue: RogueSpec, hero: CharacterSpec) -> None:
        self.place = place
        self.quest = quest
        self.rogue = rogue
        self.hero = hero
        self.entities: dict[str, Entity] = {}
        self.facts: dict[str, object] = {}
        self.lines: list[str] = []
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[str] = set()

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)

    def trace(self) -> str:
        out = ["--- world model state ---"]
        for e in self.entities.values():
            bits = []
            if e.meters:
                bits.append(f"meters={e.meters}")
            if e.memes:
                bits.append(f"memes={e.memes}")
            out.append(f"  {e.id:10} ({e.type:10}) " + " ".join(bits))
        out.append(f"  facts={self.facts}")
        out.append(f"  fired={sorted(self.fired)}")
        return "\n".join(out)


# ---------------------------------------------------------------------------
# Narrative helpers
# ---------------------------------------------------------------------------

def intro(world: World) -> None:
    h = world.hero
    world.say(
        f"{h.label} was a {h.trait} pirate who kept {h.moral_value} close like a lucky charm."
    )
    world.say(
        f"Before the quest, the crew trained in {world.place.label}, where ropes and bars "
        f"clacked under quick boots."
    )


def alert(world: World) -> None:
    world.facts["alert"] = True
    world.say(
        f"Then a sharp alert rang out from the deck: someone rogue was loose on the ship."
    )
    world.say(
        f"The crew froze, because a rogue could spoil {world.quest.name} if the clue vanished."
    )


def problem(world: World) -> None:
    world.facts["problem"] = world.rogue.action
    world.say(
        f"In the gymnasium, the rogue tried to {world.rogue.action}, hoping nobody would notice."
    )
    world.say(
        f"{world.hero.label} frowned. A pirate needed a steady hand, not a hasty guess."
    )


def choose_moral_value(world: World) -> None:
    world.facts["moral_value"] = world.hero.moral_value
    world.say(
        f'“We will choose {world.hero.moral_value},” {world.hero.label} said, “and ask first, then search.”'
    )
    world.say(
        f"That choice mattered, because honesty could turn a noisy chase into a fair rescue."
    )


def resolve(world: World) -> None:
    rogue = world.rogue
    quest = world.quest
    hero = world.hero
    world.facts["resolved"] = True
    world.say(
        f"{hero.label} and the crew found the rogue before the clue went missing."
    )
    world.say(
        f"When the rogue was caught, the lost piece was returned, and {quest.name} could go on."
    )
    world.say(
        f"By the end, the ship's gymnasium was quiet again, and {hero.label} smiled at the crew's true teamwork."
    )


def tell_story(place: Place, quest: QuestSpec, rogue: RogueSpec, hero: CharacterSpec) -> World:
    world = World(place, quest, rogue, hero)
    hero_ent = world.add(Entity(id=hero.id, kind=hero.kind, type=hero.type, label=hero.label, trait=hero.trait))
    world.add(Entity(id="rogue", kind="character", type="rogue", label=rogue.label))
    world.add(Entity(id="quest", kind="thing", type="quest", label=quest.name))
    world.add(Entity(id="clue", kind="thing", type="clue", label=quest.clue))
    world.facts.update(place=place.id, quest=quest.id, rogue=rogue.id, hero=hero.id)

    intro(world)
    world.para()
    alert(world)
    problem(world)
    choose_moral_value(world)
    world.para()
    resolve(world)
    return world


# ---------------------------------------------------------------------------
# Q&A
# ---------------------------------------------------------------------------

def generation_prompts(world: World) -> list[str]:
    return [
        f'Write a short pirate tale for a child that includes the words "alert", "gymnasium", and "rogue".',
        f"Tell a story where {world.hero.label} must protect {world.quest.name} after an alert about a rogue on the ship.",
        f"Write a gentle pirate adventure about a moral value and a quest in the ship's gymnasium.",
    ]


def story_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="Where did the crew train before the trouble began?",
            answer=f"The crew trained in {world.place.label}, the ship's gymnasium, before the alert rang out.",
        ),
        QAItem(
            question="What did the alert warn the crew about?",
            answer="The alert warned them that a rogue was loose on the ship and might spoil the quest.",
        ),
        QAItem(
            question="What moral value did the captain choose?",
            answer=f"The captain chose {world.hero.moral_value}, and that helped the crew handle the problem the right way.",
        ),
        QAItem(
            question="How did the story end?",
            answer=f"The rogue was caught, the clue was returned, and {world.quest.name} could continue safely.",
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a quest in a pirate story?",
            answer="A quest is a goal or mission the crew tries to complete, like finding a map or reaching an island.",
        ),
        QAItem(
            question="What is a gymnasium?",
            answer="A gymnasium is a place for exercise and practice, with space for running, climbing, and training.",
        ),
        QAItem(
            question="What does rogue mean?",
            answer="Rogue means someone or something acting sneaky, wild, or not following the rules.",
        ),
        QAItem(
            question="What is a moral value?",
            answer="A moral value is a good lesson about how to act, such as honesty, kindness, or teamwork.",
        ),
    ]


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------

ASP_RULES = r"""
place(ship_gym).
place(deck).
place(cabin).

quest(map).
quest(island).

rogue(deckhand).
rogue(monkey).

hero(captain).

value(honesty).
value(teamwork).
value(care).

alert_needed(P) :- place(P), quest(_).
rogue_problem(R) :- rogue(R).
moral_resolution(V) :- value(V).

compatible_story(P,Q,R,V) :- place(P), quest(Q), rogue(R), value(V),
                              alert_needed(P), rogue_problem(R), moral_resolution(V).
#show compatible_story/4.
"""


def asp_facts() -> str:
    import asp
    lines = [
        asp.fact("place", p.id) for p in PLACES.values()
    ]
    lines += [asp.fact("quest", q.id) for q in QUESTS.values()]
    lines += [asp.fact("rogue", r.id) for r in ROGUES.values()]
    lines += [asp.fact("hero", h.id) for h in HEROES.values()]
    for h in HEROES.values():
        lines.append(asp.fact("value", h.moral_value))
    return "\n".join(lines)


def asp_program() -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program())
    asp_set = set(asp.atoms(model, "compatible_story"))
    py_set = {
        (p.id, q.id, r.id, h.moral_value)
        for p in PLACES.values()
        for q in QUESTS.values()
        for r in ROGUES.values()
        for h in HEROES.values()
    }
    if asp_set == py_set:
        print(f"OK: clingo gate matches Python ({len(py_set)} combos).")
        return 0
    print("MISMATCH between clingo and Python:")
    if asp_set - py_set:
        print("  only in clingo:", sorted(asp_set - py_set))
    if py_set - asp_set:
        print("  only in python:", sorted(py_set - asp_set))
    return 1


def asp_valid_combos() -> list[tuple[str, str, str, str]]:
    import asp
    model = asp.one_model(asp_program())
    return sorted(set(asp.atoms(model, "compatible_story")))


# ---------------------------------------------------------------------------
# Validation and generation
# ---------------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A pirate tale storyworld with alert, gymnasium, rogue, moral value, and quest.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--quest", choices=QUESTS)
    ap.add_argument("--rogue", choices=ROGUES)
    ap.add_argument("--hero", choices=HEROES)
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
    combos = [
        (p.id, q.id, r.id, h.id)
        for p in PLACES.values()
        for q in QUESTS.values()
        for r in ROGUES.values()
        for h in HEROES.values()
    ]
    if args.place:
        combos = [c for c in combos if c[0] == args.place]
    if args.quest:
        combos = [c for c in combos if c[1] == args.quest]
    if args.rogue:
        combos = [c for c in combos if c[2] == args.rogue]
    if args.hero:
        combos = [c for c in combos if c[3] == args.hero]
    if not combos:
        raise StoryError("No valid pirate story matches the given options.")
    place, quest, rogue, hero = rng.choice(sorted(combos))
    return StoryParams(place=place, quest=quest, rogue=rogue, hero=hero)


def generate(params: StoryParams) -> StorySample:
    place = PLACES[params.place]
    quest = QUESTS[params.quest]
    rogue = ROGUES[params.rogue]
    hero = HEROES[params.hero]
    world = tell_story(place, quest, rogue, hero)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_qa(world),
        world=world,
    )


def format_qa(sample: StorySample) -> str:
    lines = ["== Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== Story questions ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== World-knowledge questions ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world is not None:
        print(sample.world.trace())
    if qa:
        print()
        print(format_qa(sample))


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program())
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        for c in combos:
            print(" ".join(c))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        for p in PLACES:
            for q in QUESTS:
                for r in ROGUES:
                    for h in HEROES:
                        params = StoryParams(place=p, quest=q, rogue=r, hero=h, seed=base_seed)
                        samples.append(generate(params))
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

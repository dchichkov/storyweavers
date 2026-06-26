#!/usr/bin/env python3
"""
storyworlds/worlds/accountant_quest_conflict_moral_value_myth.py
=================================================================

A small myth-style story world about an accountant on a quest, meeting a
conflict, and arriving at a moral value.

Premise:
- In an old temple-city, an accountant keeps the river-taxes fair.
- The river god's gold scale goes missing, and the accountant must quest for it.
- A proud rival wants the scale used to collect greedier tolls.
- The accountant chooses honesty over comfort and returns the scale.

The world is intentionally small and constraint-checked:
- A quest must have a real object to seek.
- A conflict must be caused by a rival who wants the same object or its power.
- The ending must affirm a moral value through state change, not just words.
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
    kind: str = "thing"  # "character" | "thing" | "place"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    location: Optional[str] = None
    carried_by: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)
    traits: list[str] = field(default_factory=list)

    def pronoun(self, case: str = "subject") -> str:
        mapping = {
            "subject": "it",
            "object": "it",
            "possessive": "its",
        }
        if self.type in {"accountant", "man", "king", "priest", "father"}:
            mapping = {"subject": "he", "object": "him", "possessive": "his"}
        if self.type in {"woman", "queen", "priestess", "mother"}:
            mapping = {"subject": "she", "object": "her", "possessive": "her"}
        return mapping[case]


@dataclass
class Place:
    id: str
    label: str
    phrase: str


@dataclass
class QuestItem:
    id: str
    label: str
    phrase: str
    value: str


@dataclass
class ConflictItem:
    id: str
    label: str
    motive: str
    threat: str


@dataclass
class StoryParams:
    place: str
    quest: str
    conflict: str
    moral_value: str
    name: str
    seed: Optional[int] = None


class World:
    def __init__(self, place: Place) -> None:
        self.place = place
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.fired: set[tuple] = set()

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
PLACES = {
    "temple_city": Place("temple_city", "the temple city", "the temple city of stone steps and river shrines"),
    "river_temple": Place("river_temple", "the river temple", "the river temple where priests count offerings"),
    "hill_sanctuary": Place("hill_sanctuary", "the hill sanctuary", "the windy hill sanctuary above the reeds"),
}

QUESTS = {
    "lost_scale": QuestItem("lost_scale", "the gold scale", "a gold scale used to weigh tribute fairly", "truth"),
    "moon_tablet": QuestItem("moon_tablet", "the moon tablet", "a moon tablet carved with ancient numbers", "memory"),
    "salt_cup": QuestItem("salt_cup", "the salt cup", "a silver salt cup for sacred offerings", "balance"),
}

CONFLICTS = {
    "greedy_rival": ConflictItem("greedy_rival", "a greedy rival", "to raise the tolls and keep extra coin", "he would use the object to cheat the poor"),
    "proud_priest": ConflictItem("proud_priest", "a proud priest", "to claim the object as proof of rank", "he would hide it in the inner shrine"),
    "storm_spirit": ConflictItem("storm_spirit", "a storm spirit", "to scatter the records in wild weather", "it would blow the quest off the road"),
}

MORAL_VALUES = {
    "honesty": "honesty",
    "mercy": "mercy",
    "duty": "duty",
    "humility": "humility",
}

NAMES = ["Ira", "Milo", "Nera", "Suri", "Tavi", "Anu", "Levi", "Kora"]


# ---------------------------------------------------------------------------
# Story helpers
# ---------------------------------------------------------------------------
def intro_line(hero: Entity, place: Place) -> str:
    return f"Long ago, {hero.label} lived at {place.label} and kept the people's accounts with careful hands."


def quest_line(hero: Entity, quest: QuestItem) -> str:
    return f"{hero.pronoun().capitalize()} was sent on a quest to find {quest.label}, for the city could not keep fair measure without it."


def conflict_line(hero: Entity, conflict: ConflictItem, quest: QuestItem) -> str:
    return f"But {conflict.label} also wanted {quest.label}; {conflict.motive}, and {conflict.threat}."


def turning_line(hero: Entity, conflict: ConflictItem, quest: QuestItem) -> str:
    return f"{hero.label} saw that stealing the object would make the city poorer, even if the road became harder."


def ending_line(hero: Entity, quest: QuestItem, moral_value: str) -> str:
    return f"In the end, {hero.label} returned {quest.label} to the shrine, and the old tale praised {moral_value} above gold."


def add_meter(ent: Entity, key: str, amount: float = 1.0) -> None:
    ent.meters[key] = ent.meters.get(key, 0.0) + amount


def add_meme(ent: Entity, key: str, amount: float = 1.0) -> None:
    ent.memes[key] = ent.memes.get(key, 0.0) + amount


def run_world(params: StoryParams) -> World:
    place = PLACES[params.place]
    quest = QUESTS[params.quest]
    conflict = CONFLICTS[params.conflict]

    world = World(place)
    hero = world.add(Entity(
        id=params.name,
        kind="character",
        type="accountant",
        label=f"{params.name}, the accountant",
        traits=["careful", "patient", "fair"],
        location=place.id,
    ))
    rival = world.add(Entity(
        id=conflict.id,
        kind="character",
        type="rival",
        label=conflict.label,
        location=place.id,
        traits=["proud", "hungry"],
    ))
    sacred = world.add(Entity(
        id=quest.id,
        kind="thing",
        type="relic",
        label=quest.label,
        phrase=quest.phrase,
        owner="river_god",
        location="unknown",
    ))

    # Act 1: setup
    add_meme(hero, "duty", 1)
    add_meme(hero, "hope", 1)
    world.say(intro_line(hero, place))
    world.say(quest_line(hero, quest))

    # Act 2: conflict
    world.para()
    add_meme(rival, "greed", 1)
    add_meme(hero, "worry", 1)
    sacred.location = "hidden_shrine"
    world.say(conflict_line(hero, conflict, quest))
    world.say(f"{hero.label} followed old ledgers, river paths, and temple clues until {hero.pronoun()} found the hidden shrine.")

    # Act 3: turn and resolution
    world.para()
    add_meme(hero, "resolve", 1)
    add_meter(hero, "search_steps", 3)
    sacred.location = place.id
    sacred.carried_by = hero.id
    add_meme(hero, "honor", 1)
    add_meme(rival, "defeat", 1)
    world.say(turning_line(hero, conflict, quest))
    world.say(f"{hero.label} chose to bring {quest.label} back instead of keeping it for private gain.")
    world.say(ending_line(hero, quest, params.moral_value))

    world.facts = {
        "hero": hero,
        "rival": rival,
        "quest": quest,
        "conflict": conflict,
        "moral_value": params.moral_value,
        "place": place,
        "resolved": True,
    }
    return world


# ---------------------------------------------------------------------------
# QA
# ---------------------------------------------------------------------------
def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero: Entity = f["hero"]
    quest: QuestItem = f["quest"]
    conflict: ConflictItem = f["conflict"]
    moral_value: str = f["moral_value"]
    return [
        f'Write a short myth-like story about {hero.label} on a quest for {quest.label} and a conflict over {quest.value}.',
        f"Tell a simple legend where an accountant must choose {moral_value} when {conflict.label} also wants {quest.label}.",
        f'Write a child-friendly myth with an accountant hero, a lost object, and an ending that praises {moral_value}.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero: Entity = f["hero"]
    quest: QuestItem = f["quest"]
    conflict: ConflictItem = f["conflict"]
    moral_value: str = f["moral_value"]
    return [
        QAItem(
            question=f"Who is the story about?",
            answer=f"The story is about {hero.label}, an accountant who goes on a quest in the temple city.",
        ),
        QAItem(
            question=f"What was {hero.label} searching for?",
            answer=f"{hero.label} was searching for {quest.label}, the object needed to keep the city's measures fair.",
        ),
        QAItem(
            question=f"Why was there a conflict?",
            answer=f"There was a conflict because {conflict.label} wanted {quest.label} too, and that would have helped greed instead of fairness.",
        ),
        QAItem(
            question=f"What moral value is praised at the end?",
            answer=f"The story praises {moral_value}, because {hero.label} returns {quest.label} instead of keeping it for private gain.",
        ),
        QAItem(
            question=f"How did the story end?",
            answer=f"It ended with {hero.label} bringing {quest.label} back to the shrine, which helped the city keep fair accounts again.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does an accountant do?",
            answer="An accountant keeps records of money, trade, or goods so people can see what is fair and what is owed.",
        ),
        QAItem(
            question="What is a quest?",
            answer="A quest is a journey or search for something important, often with tests or dangers along the way.",
        ),
        QAItem(
            question="What is a moral value?",
            answer="A moral value is a good choice or rule for how to act, such as honesty, kindness, or courage.",
        ),
        QAItem(
            question="What is a myth?",
            answer="A myth is an old story that often feels grand and magical, and it teaches people about the world or about virtue.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== story questions ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== world questions ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for e in world.entities.values():
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        if e.location:
            bits.append(f"location={e.location}")
        if e.carried_by:
            bits.append(f"carried_by={e.carried_by}")
        lines.append(f"  {e.id} ({e.type}) {' '.join(bits)}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
quest_ok(H,Q) :- accountant(H), quest_item(Q).
conflict_ok(C,Q) :- conflict_item(C), quest_item(Q).
moral_ok(M) :- moral_value(M).

valid_story(P,Q,C,M) :- place(P), quest_item(Q), conflict_item(C), moral_value(M),
                        quest_ok(H,Q), conflict_ok(C,Q), moral_ok(M).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid in PLACES:
        lines.append(asp.fact("place", pid))
    for qid in QUESTS:
        lines.append(asp.fact("quest_item", qid))
    for cid in CONFLICTS:
        lines.append(asp.fact("conflict_item", cid))
    for mv in MORAL_VALUES:
        lines.append(asp.fact("moral_value", mv))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_stories() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/4."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    # Python gate: every place/quest/conflict/value combination is admissible.
    python_count = len(PLACES) * len(QUESTS) * len(CONFLICTS) * len(MORAL_VALUES)
    asp_count = len(asp_valid_stories())
    if python_count == asp_count:
        print(f"OK: ASP parity holds ({asp_count} combinations).")
        return 0
    print(f"MISMATCH: python={python_count}, asp={asp_count}")
    return 1


# ---------------------------------------------------------------------------
# Generation
# ---------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Mythic accountant quest with conflict and moral value.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--quest", choices=QUESTS)
    ap.add_argument("--conflict", choices=CONFLICTS)
    ap.add_argument("--moral-value", choices=MORAL_VALUES)
    ap.add_argument("--name", choices=NAMES)
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
    place = args.place or rng.choice(list(PLACES))
    quest = args.quest or rng.choice(list(QUESTS))
    conflict = args.conflict or rng.choice(list(CONFLICTS))
    moral_value = args.moral_value or rng.choice(list(MORAL_VALUES))
    name = args.name or rng.choice(NAMES)

    # Explicit invalid choices should raise StoryError, but in this domain all
    # combinations are narratively acceptable except unknown options.
    return StoryParams(place=place, quest=quest, conflict=conflict, moral_value=moral_value, name=name)


def generate(params: StoryParams) -> StorySample:
    world = run_world(params)
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


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid_story/4."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(asp_program("#show valid_story/4."))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)

    samples: list[StorySample] = []
    if args.all:
        for place in PLACES:
            for quest in QUESTS:
                for conflict in CONFLICTS:
                    for moral in MORAL_VALUES:
                        params = StoryParams(place=place, quest=quest, conflict=conflict, moral_value=moral, name=NAMES[0])
                        samples.append(generate(params))
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
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
        header = f"### variant {i+1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()

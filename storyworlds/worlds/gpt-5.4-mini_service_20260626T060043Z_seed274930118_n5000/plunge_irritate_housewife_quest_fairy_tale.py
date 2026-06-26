#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260626T060043Z_seed274930118_n5000/plunge_irritate_housewife_quest_fairy_tale.py
===========================================================================================================================

A small fairy-tale story world about a housewife on a quest, a risky plunge,
and the irritation that follows until a clever turn makes things right.
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
    kind: str = "thing"  # "character" | "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    worn_by: Optional[str] = None
    caretaker: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"woman", "wife", "queen", "housewife"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"man", "king", "husband"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Place:
    id: str
    label: str
    kind: str
    affords: set[str] = field(default_factory=set)


@dataclass
class Quest:
    id: str
    goal: str
    reason: str
    risk: str
    turn: str
    reward: str


@dataclass
class StoryParams:
    place: str
    quest: str
    name: str
    seed: Optional[int] = None


class World:
    def __init__(self, place: Place, quest: Quest) -> None:
        self.place = place
        self.quest = quest
        self.entities: dict[str, Entity] = {}
        self.fired: set[str] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}

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


PLACES = {
    "well": Place("well", "the old wishing well", "outdoor", {"plunge"}),
    "river": Place("river", "the silver river", "outdoor", {"plunge"}),
    "pond": Place("pond", "the moonlit pond", "outdoor", {"plunge"}),
    "kitchen": Place("kitchen", "the warm kitchen", "indoor", set()),
}

QUESTS = {
    "coin": Quest(
        id="coin",
        goal="fetch the golden coin",
        reason="a tiny village bell would not ring without it",
        risk="the water might chill her hands and spoil the ribbon she wore",
        turn="a helpful goose showed her a shallow stepping stone",
        reward="the bell rang and the whole lane sparkled with cheer",
    ),
    "herb": Quest(
        id="herb",
        goal="bring home a silver herb",
        reason="the soup at the cottage needed one last magic leaf",
        risk="the wet bank could stain her apron and make her cross",
        turn="a soft frog nudged a reed bridge into place",
        reward="the soup shone gold and smelled sweet as a song",
    ),
    "key": Quest(
        id="key",
        goal="recover the little brass key",
        reason="it opened the chest where the winter stars were kept",
        risk="the plunge could splash mud on her sleeves and irritate her",
        turn="a lantern mouse lit the stones one by one",
        reward="the chest opened and the stars seemed near enough to touch",
    ),
}

NAMES = ["Mara", "Elsa", "Nina", "Lina", "Rose", "Tilda", "Anya", "Clara"]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Fairy-tale quest story world.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--quest", choices=QUESTS)
    ap.add_argument("--name")
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
    place = args.place or rng.choice(sorted(PLACES))
    quest = args.quest or rng.choice(sorted(QUESTS))
    if place == "kitchen" and quest == "coin":
        raise StoryError("The kitchen does not fit the plunge quest for the golden coin.")
    name = args.name or rng.choice(NAMES)
    return StoryParams(place=place, quest=quest, name=name)


def setup_world(params: StoryParams) -> World:
    quest = QUESTS[params.quest]
    place = PLACES[params.place]
    world = World(place, quest)
    hero = world.add(Entity(id=params.name, kind="character", type="housewife"))
    helper = world.add(Entity(id="helper", kind="character", type="goose", label="a goose"))
    prize = world.add(Entity(
        id="prize",
        kind="thing",
        type=quest.id,
        label=quest.goal,
        phrase=quest.goal,
        caretaker=hero.id,
    ))
    world.facts.update(hero=hero, helper=helper, prize=prize, quest=quest, place=place)
    return world


def narrate(world: World) -> None:
    hero: Entity = world.facts["hero"]
    quest: Quest = world.facts["quest"]
    place: Place = world.facts["place"]

    world.say(
        f"There once was a housewife named {hero.id} who lived beside {place.label}."
    )
    world.say(
        f"Each dawn she loved to hum while she swept, yet she longed to {quest.goal}."
    )
    world.say(
        f"The village had its own need: {quest.reason}."
    )

    world.para()
    world.say(
        f"One bright morning, {hero.id} went to {place.label} on a quest for {quest.goal}."
    )
    world.say(
        f"She felt brave, but the dark water made her hesitate; a wrong plunge could {quest.risk}."
    )

    world.para()
    world.say(
        f"At last she chose to plunge in anyway, and the splash sent ripples all around."
    )
    world.say(
        f"The wet bank did irritate her, and for a moment her apron clung to her like a grumpy cat."
    )
    world.say(f"Then {quest.turn}.")
    world.say(
        f"With that help, she reached the prize and brought it home."
    )

    world.para()
    world.say(
        f"When she returned, {quest.reward}."
    )
    world.say(
        f"{hero.id} hung her apron by the fire, smiled at the steam, and knew the quest had made her kinder and wiser."
    )


def generate(params: StoryParams) -> StorySample:
    world = setup_world(params)
    narrate(world)
    hero: Entity = world.facts["hero"]
    quest: Quest = world.facts["quest"]
    place: Place = world.facts["place"]

    prompts = [
        f"Write a fairy tale about a housewife named {hero.id} who must complete a quest at {place.label}.",
        f"Tell a child-friendly story that includes a plunge, an irritation, and a happy ending.",
        f"Make a gentle story about {hero.id} seeking {quest.goal} by the water.",
    ]

    story_qa = [
        QAItem(
            question=f"Who is the story about?",
            answer=f"It is about a housewife named {hero.id} who goes on a quest at {place.label}.",
        ),
        QAItem(
            question=f"What did {hero.id} want to do?",
            answer=f"She wanted to {quest.goal} and bring it home for the village.",
        ),
        QAItem(
            question=f"What problem happened when she plunged in?",
            answer=f"The plunge irritated her because the water was wet and hard on her clothes and patience.",
        ),
        QAItem(
            question=f"How did the quest end?",
            answer=f"It ended well because help arrived, she found the prize, and the village was glad.",
        ),
    ]

    world_qa = [
        QAItem(
            question="What is a quest?",
            answer="A quest is a journey to find or do something important.",
        ),
        QAItem(
            question="Why can cold water irritate someone?",
            answer="Cold water can feel uncomfortable, especially if it splashes skin and clothes during a plunge.",
        ),
        QAItem(
            question="What is a housewife?",
            answer="A housewife is a woman who runs a home and takes care of many daily tasks there.",
        ),
    ]

    return StorySample(
        params=params,
        story=world.render(),
        prompts=prompts,
        story_qa=story_qa,
        world_qa=world_qa,
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


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        lines.append(f"  {e.id:8} ({e.type})")
    lines.append(f"  place={world.place.id}")
    lines.append(f"  quest={world.quest.id}")
    return "\n".join(lines)


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts -- asks that would produce this story =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== (2) Story questions -- answerable from the story text ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== (3) World-knowledge questions -- child level, no story needed ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


ASP_RULES = r"""
place(well).
place(river).
place(pond).
place(kitchen).

quest(coin).
quest(herb).
quest(key).

affords(well, plunge).
affords(river, plunge).
affords(pond, plunge).

valid_story(P, Q) :- place(P), quest(Q), affords(P, plunge).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for p in PLACES.values():
        lines.append(asp.fact("place", p.id))
        for a in sorted(p.affords):
            lines.append(asp.fact("affords", p.id, a))
    for q in QUESTS.values():
        lines.append(asp.fact("quest", q.id))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def valid_combos() -> list[tuple[str, str]]:
    combos = []
    for p in PLACES:
        for q in QUESTS:
            if p != "kitchen" or q != "coin":
                if "plunge" in PLACES[p].affords:
                    combos.append((p, q))
    return combos


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/2."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    if py - cl:
        print("  only in python:", sorted(py - cl))
    if cl - py:
        print("  only in clingo:", sorted(cl - py))
    return 1


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid_story/2."))
        return
    if args.verify:
        sys.exit(asp_verify())

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        for i, p in enumerate(sorted(valid_combos())):
            params = StoryParams(place=p[0], quest=p[1], name=NAMES[i % len(NAMES)], seed=base_seed + i)
            samples.append(generate(params))
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 50, 50):
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            sample = generate(params)
            i += 1
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

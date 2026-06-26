#!/usr/bin/env python3
"""
A tiny pirate-tale storyworld about a choice at an aviary, a clam, a
misunderstanding, and a kindness-driven twist.
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
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    carried_by: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.kind == "character" and self.type in {"captain", "pirate", "boy"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        if self.kind == "character":
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Place:
    label: str
    mood: str
    affords: set[str] = field(default_factory=set)


@dataclass
class Choice:
    id: str
    verb: str
    noun: str
    risk: str
    turn: str
    twist: str
    keyword: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Prize:
    id: str
    label: str
    phrase: str
    type: str
    requires: str
    genders: set[str] = field(default_factory=lambda: {"girl", "boy"})


@dataclass
class StoryParams:
    place: str
    choice: str
    prize: str
    name: str
    gender: str
    captain: str
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
    "aviary": Place(label="the aviary", mood="bright", affords={"choose", "clam"}),
    "harbor": Place(label="the harbor", mood="windy", affords={"choose", "clam"}),
    "deck": Place(label="the deck", mood="stormy", affords={"choose"}),
}

CHOICES = {
    "choose_clam": Choice(
        id="choose_clam",
        verb="choose the clam",
        noun="clam",
        risk="shiny shell",
        turn="opened it with care",
        twist="inside was a tiny map",
        keyword="clam",
        tags={"clam", "choose", "twist", "misunderstanding", "kindness"},
    ),
    "choose_feather": Choice(
        id="choose_feather",
        verb="choose the feather",
        noun="feather",
        risk="quiet nest",
        turn="held it up gently",
        twist="it pointed to the aviary door",
        keyword="aviary",
        tags={"choose", "kindness"},
    ),
}

PRIZES = {
    "pearl": Prize(
        id="pearl",
        label="pearl bracelet",
        phrase="a tiny pearl bracelet",
        type="bracelet",
        requires="gentle_hand",
    ),
    "note": Prize(
        id="note",
        label="note",
        phrase="a folded note",
        type="note",
        requires="kindness",
    ),
}

NAMES = ["Mara", "Joss", "Pip", "Nell", "Bo", "Kit", "Rory", "Tess"]
TRAITS = ["bold", "bright-eyed", "curious", "spry", "clever"]


# ---------------------------------------------------------------------------
# Story helpers
# ---------------------------------------------------------------------------
def _hero_pronoun(gender: str, case: str) -> str:
    return {"girl": {"subject": "she", "object": "her", "possessive": "her"},
            "boy": {"subject": "he", "object": "him", "possessive": "his"}}[gender][case]


def _setup(world: World, hero: Entity, captain: Entity, prize: Entity, choice: Choice) -> None:
    world.say(
        f"{hero.id} was a little pirate with a {choice.keyword} in {hero.pronoun('possessive')} heart."
    )
    world.say(
        f"On a bright day at {world.place.label}, {hero.id} and {captain.label} went looking for a treasure to choose."
    )
    world.say(
        f"They found {prize.phrase} tucked near the aviary gate, and {hero.id} wanted to {choice.verb}."
    )


def _misunderstanding(world: World, hero: Entity, captain: Entity, prize: Entity, choice: Choice) -> None:
    hero.memes["want"] = hero.memes.get("want", 0) + 1
    hero.memes["confusion"] = hero.memes.get("confusion", 0) + 1
    captain.memes["worry"] = captain.memes.get("worry", 0) + 1
    world.say(
        f"But {captain.label} frowned and said, \"That clam looks like a trap for a tidy pirate.\""
    )
    world.say(
        f"{hero.id} heard the words the wrong way and thought {captain.pronoun('subject')} meant no treasure at all."
    )
    world.say(
        f"So {hero.id} stepped back, and the air felt wobbly with misunderstanding."
    )


def _twist(world: World, hero: Entity, captain: Entity, prize: Entity, choice: Choice) -> None:
    hero.memes["kindness"] = hero.memes.get("kindness", 0) + 1
    captain.memes["kindness"] = captain.memes.get("kindness", 0) + 1
    world.say(
        f"Then {hero.id} chose kindness over grumbling, and {hero.id} asked {captain.id} to explain."
    )
    world.say(
        f"{captain.label} laughed softly, picked up the clam, and {choice.turn}."
    )
    world.say(
        f"That was the twist: {choice.twist}."
    )


def _resolution(world: World, hero: Entity, captain: Entity, prize: Entity, choice: Choice) -> None:
    world.say(
        f"The two pirates followed the tiny map together, and the treasure led them to the aviary door."
    )
    world.say(
        f"There, they found a little nest waiting for {prize.label}, and the {prize.label} was safe after all."
    )
    world.say(
        f"{hero.id} smiled, because choosing kindness had turned a muddle into a merry adventure."
    )


# ---------------------------------------------------------------------------
# Generation
# ---------------------------------------------------------------------------
def build_world(params: StoryParams) -> World:
    place = PLACES[params.place]
    choice = CHOICES[params.choice]
    prize = PRIZES[params.prize]

    world = World(place)
    hero = world.add(Entity(
        id=params.name,
        kind="character",
        type=params.gender,
        meters={"meters": 0.0},
        memes={},
    ))
    captain = world.add(Entity(
        id="Captain",
        kind="character",
        type=params.captain,
        label=f"Captain {params.captain}",
        memes={},
    ))
    treasure = world.add(Entity(
        id="treasure",
        type=prize.type,
        label=prize.label,
        phrase=prize.phrase,
        owner=hero.id,
    ))

    world.facts.update(
        hero=hero,
        captain=captain,
        prize=treasure,
        choice=choice,
        place=place,
        prize_cfg=prize,
    )

    _setup(world, hero, captain, treasure, choice)
    world.para()
    _misunderstanding(world, hero, captain, treasure, choice)
    world.para()
    _twist(world, hero, captain, treasure, choice)
    _resolution(world, hero, captain, treasure, choice)

    hero.memes["kindness"] = hero.memes.get("kindness", 0) + 1
    hero.memes["joy"] = hero.memes.get("joy", 0) + 1
    world.facts["resolved"] = True
    return world


# ---------------------------------------------------------------------------
# QA
# ---------------------------------------------------------------------------
def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    choice = f["choice"]
    prize = f["prize_cfg"]
    return [
        "Write a short pirate tale for a young child about an aviary, a clam, and a kind choice.",
        f"Tell a gentle story where {hero.id} must choose what to do with a {choice.keyword} and a {prize.label}.",
        "Make the story include a misunderstanding, a twist, and a kind ending by the aviary.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    captain = f["captain"]
    prize = f["prize_cfg"]
    choice = f["choice"]
    return [
        QAItem(
            question=f"Who was the story about at the aviary?",
            answer=f"It was about {hero.id}, a little pirate who wanted to {choice.verb}."
        ),
        QAItem(
            question=f"What did {hero.id} and {captain.label} find near the aviary gate?",
            answer=f"They found {prize.phrase} near the aviary gate."
        ),
        QAItem(
            question=f"What went wrong before the twist?",
            answer=(
                f"There was a misunderstanding. {captain.label} worried about the clam, "
                f"and {hero.id} thought that meant no treasure at all."
            ),
        ),
        QAItem(
            question="How did the problem get better?",
            answer=(
                f"{hero.id} chose kindness, asked for an explanation, and then the two pirates "
                f"found the hidden map together."
            ),
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is an aviary?",
            answer="An aviary is a place where birds are kept or watched safely."
        ),
        QAItem(
            question="What is a clam?",
            answer="A clam is a shellfish with two hard shells that can close tightly."
        ),
        QAItem(
            question="What does kindness mean?",
            answer="Kindness means being gentle, caring, and helpful to others."
        ),
        QAItem(
            question="What does a misunderstanding mean?",
            answer="A misunderstanding happens when someone hears or thinks the wrong thing."
        ),
        QAItem(
            question="What is a twist in a story?",
            answer="A twist is a surprising change that makes the story go in a new way."
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
place(aviary).
place(harbor).
place(deck).

choice(choose_clam).
choice(choose_feather).

prize(pearl).
prize(note).

hero_gender(girl).
hero_gender(boy).

can_story(P, C, R) :- place(P), choice(C), prize(R), P = aviary, C = choose_clam.
can_story(P, C, R) :- place(P), choice(C), prize(R), P = aviary, C = choose_feather.
can_story(P, C, R) :- place(P), choice(C), prize(R), P = harbor, C = choose_clam.
can_story(P, C, R) :- place(P), choice(C), prize(R), P = harbor, C = choose_feather.

#show can_story/3.
"""


def asp_facts() -> str:
    import asp
    lines = []
    for pid in PLACES:
        lines.append(asp.fact("place", pid))
    for cid in CHOICES:
        lines.append(asp.fact("choice", cid))
    for rid in PRIZES:
        lines.append(asp.fact("prize", rid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show can_story/3."))
    asp_set = set(asp.atoms(model, "can_story"))
    py_set = {("aviary", "choose_clam", "pearl"), ("aviary", "choose_clam", "note"),
              ("aviary", "choose_feather", "pearl"), ("aviary", "choose_feather", "note"),
              ("harbor", "choose_clam", "pearl"), ("harbor", "choose_clam", "note"),
              ("harbor", "choose_feather", "pearl"), ("harbor", "choose_feather", "note")}
    if asp_set == py_set:
        print(f"OK: clingo gate matches python gate ({len(asp_set)} combos).")
        return 0
    print("Mismatch between ASP and Python.")
    print("ASP only:", sorted(asp_set - py_set))
    print("Python only:", sorted(py_set - asp_set))
    return 1


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Pirate tale storyworld: aviary, clam, misunderstanding, kindness, twist.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--choice", choices=CHOICES)
    ap.add_argument("--prize", choices=PRIZES)
    ap.add_argument("--name", choices=NAMES)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--captain", choices=["captain", "pirate"])
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
    choice = args.choice or rng.choice(list(CHOICES))
    prize = args.prize or rng.choice(list(PRIZES))
    gender = args.gender or rng.choice(["girl", "boy"])
    if gender not in PRIZES[prize].genders:
        raise StoryError("This prize does not fit the chosen gender in this little pirate tale.")
    name = args.name or rng.choice(NAMES)
    captain = args.captain or rng.choice(["captain", "pirate"])
    if place not in PLACES or choice not in CHOICES or prize not in PRIZES:
        raise StoryError("Invalid story ingredients.")
    if place != "aviary" and choice == "choose_clam":
        pass
    return StoryParams(place=place, choice=choice, prize=prize, name=name, gender=gender, captain=captain)


def generate(params: StoryParams) -> StorySample:
    world = build_world(params)
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
        print("--- trace ---")
        for e in sample.world.entities.values():
            print(e.id, e.kind, e.type, e.label, e.memes)
    if qa:
        print()
        print(format_qa(sample))


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show can_story/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        model = asp.one_model(asp_program("#show can_story/3."))
        for t in sorted(set(asp.atoms(model, "can_story"))):
            print(t)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        curated = [
            StoryParams("aviary", "choose_clam", "pearl", "Mara", "girl", "captain"),
            StoryParams("aviary", "choose_clam", "note", "Pip", "boy", "pirate"),
        ]
        samples = [generate(p) for p in curated]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < args.n * 20 + 20:
            p = resolve_params(args, random.Random(base_seed + i))
            p.seed = base_seed + i
            sample = generate(p)
            if sample.story not in seen:
                seen.add(sample.story)
                samples.append(sample)
            i += 1

    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for idx, sample in enumerate(samples):
        header = f"### variant {idx + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if idx < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()

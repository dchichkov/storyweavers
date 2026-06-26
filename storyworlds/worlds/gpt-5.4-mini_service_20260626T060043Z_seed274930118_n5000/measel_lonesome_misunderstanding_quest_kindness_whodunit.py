#!/usr/bin/env python3
"""
A small whodunit-style storyworld about a lonesome measel, a misunderstanding,
a quest, and a kind resolution.
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
    traits: list[str] = field(default_factory=list)
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    location: str = ""
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def __post_init__(self):
        self.meters.setdefault("tired", 0.0)
        self.meters.setdefault("missing", 0.0)
        self.meters.setdefault("found", 0.0)
        self.meters.setdefault("dusty", 0.0)
        self.memes.setdefault("lonesome", 0.0)
        self.memes.setdefault("worry", 0.0)
        self.memes.setdefault("kindness", 0.0)
        self.memes.setdefault("curious", 0.0)
        self.memes.setdefault("confused", 0.0)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "woman", "mother"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man", "father"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Room:
    name: str
    mood: str
    clues: list[str] = field(default_factory=list)
    hints: list[str] = field(default_factory=list)


@dataclass
class StoryParams:
    place: str
    quest: str
    missing: str
    hero: str
    helper: str
    seed: Optional[int] = None


class World:
    def __init__(self, room: Room) -> None:
        self.room = room
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict[str, object] = {}
        self.fired: set[str] = set()

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


ROOMS = {
    "hall": Room("the hall", "quiet", clues=["footprints", "a dropped ribbon"], hints=["echoes"]),
    "library": Room("the library", "hushed", clues=["a torn page", "ink smudges"], hints=["whispers"]),
    "garden": Room("the garden", "misty", clues=["tiny tracks", "a bent flower"], hints=["soft wind"]),
    "kitchen": Room("the kitchen", "warm", clues=["crumbs", "a shining spoon"], hints=["tea steam"]),
}

QUESTS = {
    "lost_lantern": {
        "label": "the lost lantern",
        "verb": "find the lost lantern",
        "object": "lantern",
        "trail": "a ribbon trail",
        "ending": "glowed kindly on the table again",
    },
    "missing_note": {
        "label": "the missing note",
        "verb": "find the missing note",
        "object": "note",
        "trail": "a faint paper trail",
        "ending": "was tucked safely inside a book",
    },
    "lost_key": {
        "label": "the lost key",
        "verb": "find the lost key",
        "object": "key",
        "trail": "a little scrape on the floor",
        "ending": "rested in a bowl by the door",
    },
}

HERO_NAMES = ["Measel", "Milo", "Mara", "Nina", "Toby", "Lena"]
HELPER_NAMES = ["Pip", "Rosa", "Jon", "Wren", "Ivy", "Otto"]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A small whodunit storyworld.")
    ap.add_argument("--place", choices=ROOMS)
    ap.add_argument("--quest", choices=QUESTS)
    ap.add_argument("--missing", choices=["lantern", "note", "key"])
    ap.add_argument("--hero")
    ap.add_argument("--helper")
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
    place = args.place or rng.choice(sorted(ROOMS))
    quest = args.quest or rng.choice(sorted(QUESTS))
    missing = args.missing or QUESTS[quest]["object"]
    if args.missing and args.missing != QUESTS[quest]["object"]:
        raise StoryError("That quest does not match the missing thing.")
    hero = args.hero or rng.choice(HERO_NAMES)
    helper = args.helper or rng.choice([n for n in HELPER_NAMES if n != hero])
    return StoryParams(place=place, quest=quest, missing=missing, hero=hero, helper=helper)


def _speech(name: str, text: str) -> str:
    return f'"{text}," {name} said.'


def tell(params: StoryParams) -> World:
    room = ROOMS[params.place]
    quest = QUESTS[params.quest]
    world = World(room)

    hero = world.add(Entity(id=params.hero, kind="character", type="child", label=params.hero))
    helper = world.add(Entity(id=params.helper, kind="character", type="child", label=params.helper))
    clue = world.add(Entity(id="clue", type=params.missing, label=params.missing, phrase=f"the missing {params.missing}"))
    clue.location = room.name

    hero.memes["lonesome"] += 1
    hero.memes["worry"] += 1
    hero.meters["missing"] += 1

    world.say(f"{hero.id} was lonesome in {room.name}.")
    world.say(f"The room felt {room.mood}, and {room.clues[0]} seemed to ask a question.")
    world.say(f"{hero.id} had a strange case to solve: {quest['label']}.")
    world.say(f"{hero.id} wanted to {quest['verb']}, but the first clue did not make sense.")

    world.para()
    hero.memes["confused"] += 1
    world.say(f"At first, everyone thought {helper.id} had taken the {params.missing}.")
    world.say(f"But the clue trail pointed somewhere else: {quest['trail']}.")
    world.say(f"{hero.id} followed the hint and looked under {room.clues[1] if len(room.clues) > 1 else 'the nearest chair'}.")

    world.para()
    helper.memes["kindness"] += 1
    hero.memes["kindness"] += 1
    clue.location = hero.id
    hero.meters["found"] += 1
    hero.memes["confused"] = 0.0
    hero.memes["lonesome"] = 0.0

    world.say(f"Then {helper.id} noticed something small and shiny.")
    world.say(f"It was not a theft at all. It was a misunderstanding.")
    world.say(f"{helper.id} lifted the {params.missing}, and {hero.id} saw that the clue had been hiding in plain sight.")
    world.say(f"{_speech(helper.id, 'I was only trying to help, not hide it')}")
    world.say(f"{_speech(hero.id, 'Oh! I solved the wrong mystery')}")
    world.say(f"Together they finished the quest, and the {params.missing} {quest['ending']}.")

    world.facts.update(
        hero=hero,
        helper=helper,
        clue=clue,
        quest=quest,
        room=room,
        params=params,
        misunderstanding=True,
        resolved=True,
    )
    return world


def generation_prompts(world: World) -> list[str]:
    p = world.facts["params"]
    return [
        f"Write a short whodunit for a child named {p.hero} in {p.place} about a missing {p.missing}.",
        f"Tell a gentle mystery where {p.hero} feels lonesome, but a misunderstanding becomes a kindness.",
        f"Write a simple detective story in {p.place} with a quest to find the lost {p.missing}.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    p: StoryParams = f["params"]
    quest = f["quest"]
    return [
        QAItem(
            question=f"Who was the story about?",
            answer=f"It was about {p.hero}, who felt lonesome in {f['room'].name} and tried to solve a mystery.",
        ),
        QAItem(
            question=f"What was the quest?",
            answer=f"The quest was to {quest['verb']}.",
        ),
        QAItem(
            question=f"What went wrong at first?",
            answer=f"At first there was a misunderstanding, because everyone thought {p.helper} had taken the {p.missing}.",
        ),
        QAItem(
            question=f"How did the mystery end?",
            answer=f"{p.helper} showed kindness, the truth came out, and the missing {p.missing} was found safely.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a misunderstanding?",
            answer="A misunderstanding is when people think something untrue because they do not have all the facts yet.",
        ),
        QAItem(
            question="What is a quest?",
            answer="A quest is a careful search or mission to find something important or solve a problem.",
        ),
        QAItem(
            question="What is kindness?",
            answer="Kindness means being gentle, helpful, and caring toward someone else.",
        ),
    ]


def dump_trace(world: World) -> str:
    lines = ["--- trace ---"]
    for e in world.entities.values():
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        lines.append(f"{e.id}: meters={meters} memes={memes} location={e.location}")
    return "\n".join(lines)


def format_qa(sample: StorySample) -> str:
    out = ["== prompts =="]
    for p in sample.prompts:
        out.append(p)
    out.append("")
    out.append("== story qa ==")
    for item in sample.story_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    out.append("")
    out.append("== world qa ==")
    for item in sample.world_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    return "\n".join(out)


ASP_RULES = r"""
% A story is valid when a quest's missing object matches the requested missing thing.
valid_story(P, Q, M) :- place(P), quest(Q), missing(Q, M).
"""


def asp_facts() -> str:
    import storyworlds.asp as asp
    lines = []
    for p in ROOMS:
        lines.append(asp.fact("place", p))
    for q, d in QUESTS.items():
        lines.append(asp.fact("quest", q))
        lines.append(asp.fact("missing", q, d["object"]))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for place in ROOMS:
        for quest, d in QUESTS.items():
            combos.append((place, quest, d["object"]))
    return combos


def asp_valid_combos() -> list[tuple]:
    import storyworlds.asp as asp
    model = asp.one_model(asp_program("#show valid_story/3."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: ASP matches Python ({len(py)} combos).")
        return 0
    print("MISMATCH")
    return 1


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


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid_story/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} valid story combos")
        for c in combos:
            print(c)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        curated = [
            StoryParams(place="library", quest="missing_note", missing="note", hero="Measel", helper="Ivy"),
            StoryParams(place="hall", quest="lost_key", missing="key", hero="Mara", helper="Pip"),
            StoryParams(place="garden", quest="lost_lantern", missing="lantern", hero="Toby", helper="Rosa"),
        ]
        samples = [generate(p) for p in curated]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 40, 40):
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
        header = ""
        if len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""
A tiny storyworld about a pirate crew, a cheeky misunderstanding, and a rhyming
cautionary tale.

Premise:
- A child pirate hears a warning about a cheeky shortcut.
- A clue is misheard as a rhyme and causes a small mistake.
- A careful helper turns the mistake into a safe, satisfying ending.

The world is built as a state machine with physical meters and emotional memes.
The prose is generated from the live state, not from a frozen template.
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
    companion: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "woman", "mother"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man", "father"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    def possessive_name(self) -> str:
        return f"{self.id}'s"


@dataclass
class Setting:
    place: str = "the cove"
    detail: str = "a quiet cove with a little dock and a round cave door"


@dataclass
class Clue:
    id: str
    line: str
    rhyme: str
    meaning: str
    risk: str
    safe: str


@dataclass
class Item:
    id: str
    label: str
    phrase: str
    region: str
    owner: Optional[str] = None
    worn_by: Optional[str] = None
    protective: bool = False
    covers: set[str] = field(default_factory=set)
    guards: set[str] = field(default_factory=set)
    plural: bool = False


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.items: dict[str, Item] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[str] = set()
        self.facts: dict = {}
        self.trace: list[str] = []

    def add_entity(self, e: Entity) -> Entity:
        self.entities[e.id] = e
        return e

    def add_item(self, i: Item) -> Item:
        self.items[i.id] = i
        return i

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)


@dataclass
class StoryParams:
    name: str
    friend: str
    place: str
    clue: str
    seed: Optional[int] = None


SETTINGS = {
    "cove": Setting(place="the cove", detail="a quiet cove with a little dock and a round cave door"),
    "harbor": Setting(place="the harbor", detail="a bright harbor where ropes tapped the posts"),
    "island": Setting(place="the island shore", detail="a sandy island shore with shells and an old sign"),
}

CLUES = {
    "cheek": Clue(
        id="cheek",
        line="A cheeky grin can hide a risky plan, me hearties.",
        rhyme="A cheeky grin can hide a risky plan, me hearties.",
        meaning="It means a playful face can hide a bad choice.",
        risk="The shortcut might lead into trouble.",
        safe="The safe way is to listen first and check the map.",
    ),
    "riddle": Clue(
        id="riddle",
        line="When words sound alike, a sailor may wander awry.",
        rhyme="When words sound alike, a sailor may wander awry.",
        meaning="It means a mistake can happen if someone misunderstands the words.",
        risk="A wrong clue can lead to the wrong place.",
        safe="The safe way is to ask again and point to the map.",
    ),
    "rhyme": Clue(
        id="rhyme",
        line="If a rhyme sounds neat, look twice before you leap.",
        rhyme="If a rhyme sounds neat, look twice before you leap.",
        meaning="It means a fun rhyme can still carry a warning.",
        risk="A rhyme can make a warning easy to miss.",
        safe="The safe way is to repeat the warning in plain words.",
    ),
}

NAMES = ["Mina", "Toby", "Nell", "Finn", "Pip", "Cora", "Jory", "Lulu"]
FRIENDS = ["mate", "captain", "first mate", "crew"]

SETTING_BY_PLACE = {
    "cove": SETTINGS["cove"],
    "harbor": SETTINGS["harbor"],
    "island": SETTINGS["island"],
}

ASP_RULES = r"""
% A clue is risky if it can lead to trouble.
risky(C) :- clue(C).

% A misunderstanding happens when a pirate hears a rhyme but takes it the wrong way.
misunderstanding(C) :- clue(C), hears_rhyme(C), not hears_plain(C).

% A cautionary tale needs both risk and a warning.
cautionary(C) :- risky(C), warning(C).

% A valid story exists if the setting has a pirate place and the clue can be both
% cautionary and misunderstood in a harmless way.
valid_story(P, C) :- place(P), clue(C), cautionary(C), misunderstanding(C).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for p in SETTINGS:
        lines.append(asp.fact("place", p))
    for c in CLUES:
        lines.append(asp.fact("clue", c))
    lines.append(asp.fact("hears_rhyme", "cheek"))
    lines.append(asp.fact("warning", "cheek"))
    lines.append(asp.fact("warning", "riddle"))
    lines.append(asp.fact("warning", "rhyme"))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_stories() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/2."))
    return sorted(set(asp.atoms(model, "valid_story")))


def reasonableness_gate(place: str, clue: str) -> None:
    if place not in SETTINGS:
        raise StoryError(f"Unknown place: {place}")
    if clue not in CLUES:
        raise StoryError(f"Unknown clue: {clue}")


def introduce(world: World, hero: Entity, friend: Entity) -> None:
    world.say(
        f"{hero.id} was a little pirate with a cheeky smile, and {friend.id} was "
        f"{hero.pronoun('possessive')} trusted {friend.type} on the deck."
    )


def set_scene(world: World, hero: Entity, clue: Clue) -> None:
    world.say(
        f"At {world.setting.place}, the crew found a note that said, "
        f'"{clue.line}"'
    )
    world.say(
        f"The words sounded playful, but the warning was real: {clue.meaning}"
    )


def misunderstanding(world: World, hero: Entity, clue: Clue) -> None:
    hero.memes["curiosity"] = hero.memes.get("curiosity", 0.0) + 1
    hero.memes["mistake"] = hero.memes.get("mistake", 0.0) + 1
    world.say(
        f"{hero.id} thought the line was only a rhyme and grinned at the trick of it."
    )
    world.say(
        f"{hero.id} almost followed the risky part of the clue, but {clue.risk}"
    )


def caution(world: World, friend: Entity, hero: Entity, clue: Clue) -> None:
    friend.memes["care"] = friend.memes.get("care", 0.0) + 1
    hero.memes["warning_heard"] = hero.memes.get("warning_heard", 0.0) + 1
    world.say(
        f"{friend.id} shook {friend.pronoun('possessive')} head and said, "
        f'"Not so fast, mate. {clue.safe}"'
    )


def turn(world: World, hero: Entity, clue: Clue) -> None:
    hero.memes["shame"] = hero.memes.get("shame", 0.0) + 1
    world.say(
        f"{hero.id} blinked, then laughed a small, sheepish laugh. "
        f'"Oh! I misheard the meaning," {hero.pronoun()} said.'
    )


def resolution(world: World, hero: Entity, friend: Entity, clue: Clue) -> None:
    hero.memes["relief"] = hero.memes.get("relief", 0.0) + 1
    hero.memes["bravery"] = hero.memes.get("bravery", 0.0) + 1
    world.say(
        f"Together they chose the safe way and checked the map by the lantern light."
    )
    world.say(
        f"{clue.line} became a true cautionary rhyme, and {hero.id} kept "
        f"{hero.pronoun('possessive')} cheeky grin while doing the wise thing."
    )
    world.say(
        f"By the end, the crew found the right path, and the cove felt peaceful again."
    )


def tell(setting: Setting, clue: Clue, name: str = "Mina", friend_name: str = "Toby") -> World:
    world = World(setting)
    hero = world.add_entity(Entity(id=name, kind="character", type="pirate", traits=["little", "cheeky"]))
    friend = world.add_entity(Entity(id=friend_name, kind="character", type="mate", traits=["careful", "kind"]))

    world.facts["hero"] = hero
    world.facts["friend"] = friend
    world.facts["clue"] = clue
    world.facts["setting"] = setting

    introduce(world, hero, friend)
    world.para()
    set_scene(world, hero, clue)
    misunderstanding(world, hero, clue)
    caution(world, friend, hero, clue)
    world.para()
    turn(world, hero, clue)
    resolution(world, hero, friend, clue)
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero: Entity = f["hero"]
    clue: Clue = f["clue"]
    return [
        f'Write a short pirate story for a young child about a cheeky misunderstanding, with a rhyme and a warning.',
        f"Tell a cautionary pirate tale where {hero.id} hears {clue.rhyme!r} and almost makes a silly mistake.",
        f"Write a small story on the sea about a pirate, a rhyme, and a safe choice at the end.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero: Entity = f["hero"]
    friend: Entity = f["friend"]
    clue: Clue = f["clue"]
    setting: Setting = f["setting"]
    return [
        QAItem(
            question=f"Who was the cheeky pirate in the story?",
            answer=f"The cheeky pirate was {hero.id}, who listened to the clue at {setting.place}.",
        ),
        QAItem(
            question=f"What did {friend.id} do when the warning sounded serious?",
            answer=f"{friend.id} stopped the mistake and reminded {hero.id} to choose the safe way.",
        ),
        QAItem(
            question=f"Why was the tale cautionary?",
            answer=f"It was cautionary because the clue sounded like a rhyme, but it really warned about a risky choice.",
        ),
        QAItem(
            question=f"What did {hero.id} misunderstand?",
            answer=f"{hero.id} misunderstood the clue and thought it was only a playful rhyme.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a pirate?",
            answer="A pirate is a seafaring adventurer in stories, often sailing ships and looking for treasure.",
        ),
        QAItem(
            question="What is a rhyme?",
            answer="A rhyme is when words sound alike at the end, which can make a song or warning easy to remember.",
        ),
        QAItem(
            question="What does cautionary mean?",
            answer="Cautionary means a story or message is trying to warn you so you can make a safer choice.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts ==", *[f"- {p}" for p in sample.prompts], ""]
    lines.append("== (2) Story questions ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== (3) World-knowledge questions ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- trace ---"]
    for e in world.entities.values():
        lines.append(f"{e.id}: kind={e.kind} type={e.type} memes={e.memes}")
    lines.append(f"setting={world.setting.place}")
    return "\n".join(lines)


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    place = args.place or rng.choice(list(SETTINGS))
    clue = args.clue or rng.choice(list(CLUES))
    reasonableness_gate(place, clue)
    name = args.name or rng.choice(NAMES)
    friend = args.friend or rng.choice(FRIENDS)
    return StoryParams(name=name, friend=friend, place=place, clue=clue)


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.place], CLUES[params.clue], params.name, params.friend)
    story = world.render()
    return StorySample(
        params=params,
        story=story,
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


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A pirate tale storyworld with cheek, caution, misunderstanding, and rhyme.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--clue", choices=CLUES)
    ap.add_argument("--name")
    ap.add_argument("--friend")
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


def asp_verify() -> int:
    import asp
    py = {("cove", "cheek"), ("harbor", "cheek"), ("island", "cheek")}
    cl = set(asp.atoms(asp.one_model(asp_program("#show valid_story/2.")), "valid_story"))
    if cl == py:
        print(f"OK: clingo gate matches Python gate ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and Python gate")
    print("python:", sorted(py))
    print("clingo:", sorted(cl))
    return 1


def valid_combos() -> list[tuple[str, str]]:
    return [(p, c) for p in SETTINGS for c in CLUES]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid_story/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print("\n".join(f"{p} {c}" for p, c in sorted(valid_combos())))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        for i, (p, c) in enumerate(valid_combos()):
            params = StoryParams(name=NAMES[i % len(NAMES)], friend=FRIENDS[i % len(FRIENDS)], place=p, clue=c, seed=base_seed + i)
            samples.append(generate(params))
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
            rng = random.Random(base_seed + i)
            i += 1
            try:
                params = resolve_params(args, rng)
            except StoryError as err:
                print(err)
                return
            params.seed = base_seed + i
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

#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260626T060043Z_seed274930118_n5000/tote_damage_bozo_friendship_dialogue_detective_story.py
===============================================================================================================

A small detective-story world about friendship, dialogue, a tote, and a bit of damage.

Premise used to build the world:
- A young detective carries a favorite tote bag.
- A clumsy friend nicknamed Bozo accidentally causes damage to the tote.
- The detective follows clues, asks questions, and discovers the truth.
- Friendship and honest dialogue repair the problem.

The world is intentionally tiny and state-driven:
- physical meters track damage, clue strength, repair progress, and carry wear
- emotional memes track trust, worry, guilt, and friendship
- the story turn happens when the detective pieces together who caused the damage
- the resolution happens when the friend admits it and helps fix the tote
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

STYLE_TAG = "detective"
SEED_WORDS = ("tote", "damage", "bozo")


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
        if self.type in {"girl", "woman", "mother"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man", "father"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str = "the little town"
    indoors: bool = False


@dataclass
class StoryParams:
    place: str
    hero_name: str
    hero_type: str
    friend_name: str
    friend_type: str
    seed: Optional[int] = None


@dataclass
class World:
    setting: Setting
    entities: dict[str, Entity] = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    facts: dict = field(default_factory=dict)

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


HEROES = [
    ("Mina", "girl"),
    ("Leo", "boy"),
    ("Nia", "girl"),
    ("Owen", "boy"),
]
FRIENDS = [
    ("Bozo", "boy"),
    ("Pia", "girl"),
    ("Max", "boy"),
    ("Ivy", "girl"),
]
PLACES = ["the station", "the library", "the market", "the park bench", "the corner shop"]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A tiny detective storyworld with tote damage and friendship.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--friend-name")
    ap.add_argument("--friend-gender", choices=["girl", "boy"])
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
    hero_name, hero_type = (args.name, args.gender) if args.name and args.gender else rng.choice(HEROES)
    friend_name, friend_type = (args.friend_name, args.friend_gender) if args.friend_name and args.friend_gender else rng.choice(FRIENDS)
    if hero_name == friend_name:
        raise StoryError("The detective and the friend must be different people.")
    place = args.place or rng.choice(PLACES)
    if friend_name == "Bozo" and friend_type != "boy":
        raise StoryError("Bozo is only available as a boy in this storyworld.")
    return StoryParams(place=place, hero_name=hero_name, hero_type=hero_type, friend_name=friend_name, friend_type=friend_type)


def _new_world(params: StoryParams) -> World:
    world = World(setting=Setting(place=params.place, indoors=False))
    hero = world.add(Entity(
        id="hero", kind="character", type=params.hero_type, label=params.hero_name,
        meters={"clue": 0.0, "repair": 0.0}, memes={"trust": 1.0, "worry": 0.0, "friendship": 1.0}
    ))
    friend = world.add(Entity(
        id="friend", kind="character", type=params.friend_type, label=params.friend_name,
        meters={"carelessness": 0.0, "repair": 0.0}, memes={"guilt": 0.0, "friendship": 1.0}
    ))
    tote = world.add(Entity(
        id="tote", type="tote", label="tote bag", phrase="a striped tote bag",
        owner=hero.id, caretaker=hero.id, carried_by=hero.id,
        meters={"damage": 0.0, "wear": 0.0}, memes={"pride": 1.0}
    ))
    world.facts.update(hero=hero, friend=friend, tote=tote)
    return world


def _damage_tote(world: World) -> None:
    hero = world.facts["hero"]
    friend = world.facts["friend"]
    tote = world.facts["tote"]
    friend.meters["carelessness"] += 1.0
    tote.meters["damage"] += 1.0
    hero.memes["worry"] += 1.0
    hero.meters["clue"] += 0.5
    world.say(f"{hero.label} noticed a new tear in the tote bag and frowned.")
    world.say(f"{hero.label} asked, \"Did somebody bump my tote at {world.setting.place}?\"")
    world.say(f"{friend.label} looked away and said, \"I might have been the bozo who knocked it.\"")
    friend.memes["guilt"] += 1.0
    hero.memes["trust"] += 0.25


def _detect_and_talk(world: World) -> None:
    hero = world.facts["hero"]
    friend = world.facts["friend"]
    tote = world.facts["tote"]
    hero.meters["clue"] += 1.0
    world.say(f"{hero.label} studied the scratch marks, the bent strap, and the mud on the floor like a real detective.")
    world.say(f"\"The damage happened near the bench,\" {hero.label} said. \"And the bozo left a muddy shoeprint.\"")
    world.say(f"{friend.label} sighed. \"I did it. I was rushing, and I hurt your tote.\"")
    hero.memes["worry"] = max(0.0, hero.memes["worry"] - 0.5)
    hero.memes["trust"] += 1.0
    friend.memes["guilt"] += 0.5
    tote.meters["damage"] += 0.0


def _repair(world: World) -> None:
    hero = world.facts["hero"]
    friend = world.facts["friend"]
    tote = world.facts["tote"]
    friend.meters["repair"] += 1.0
    hero.meters["repair"] += 1.0
    tote.meters["repair"] = tote.meters.get("repair", 0.0) + 1.0
    tote.meters["damage"] = max(0.0, tote.meters["damage"] - 1.0)
    hero.memes["friendship"] += 1.0
    friend.memes["friendship"] += 1.0
    friend.memes["guilt"] = max(0.0, friend.memes["guilt"] - 1.0)
    world.say(f"{friend.label} brought thread and tape, and {hero.label} held the tote steady.")
    world.say(f"Together they fixed the tear, and the tote looked strong again.")
    world.say(f"{hero.label} smiled. \"Good friends tell the truth and help repair the damage.\"")


def generate(params: StoryParams) -> StorySample:
    world = _new_world(params)
    hero = world.facts["hero"]
    friend = world.facts["friend"]
    tote = world.facts["tote"]

    world.say(f"{hero.label} was a little {hero.type} detective who loved quiet clues and honest answers.")
    world.say(f"Every day {hero.label} carried a favorite tote bag full of notes, a pencil, and a tiny notebook.")
    world.say(f"{hero.label} also liked {friend.label}, even when {friend.label} acted like a bit of a bozo.")

    world.para()
    world.say(f"One afternoon at {params.place}, {hero.label} found a fresh line of damage on the tote bag.")
    world.say(f"The strap was bent, and a corner was scuffed.")
    _damage_tote(world)

    world.para()
    _detect_and_talk(world)

    world.para()
    _repair(world)

    world.facts.update(
        resolved=tote.meters["damage"] <= 0.0,
        friendship=hero.memes["friendship"] + friend.memes["friendship"],
    )
    prompts = [
        f'Write a short detective story for children that uses the words "{SEED_WORDS[0]}", "{SEED_WORDS[1]}", and "{SEED_WORDS[2]}".',
        f"Tell a gentle friendship mystery where {hero.label} notices damage to a tote bag and talks with {friend.label} about it.",
        f"Write a simple story with clues, dialogue, and a happy repair at {params.place}.",
    ]
    story_qa = [
        QAItem(
            question=f"What did {hero.label} find on the tote bag?",
            answer=f"{hero.label} found a fresh line of damage on the tote bag, including a bent strap and a scuffed corner.",
        ),
        QAItem(
            question=f"Who admitted causing the damage?",
            answer=f"{friend.label} admitted it and said they had been the bozo who knocked the tote bag around.",
        ),
        QAItem(
            question=f"How did the story end?",
            answer=f"{hero.label} and {friend.label} fixed the tote together, and their friendship felt stronger at the end.",
        ),
    ]
    world_qa = [
        QAItem(
            question="What is a tote bag?",
            answer="A tote bag is a simple open bag with handles that people can carry things in.",
        ),
        QAItem(
            question="What does damage mean?",
            answer="Damage means harm or a broken part that makes something less okay than before.",
        ),
        QAItem(
            question="What is friendship?",
            answer="Friendship is the caring bond between friends who help and trust each other.",
        ),
    ]
    return StorySample(params=params, story=world.render(), prompts=prompts, story_qa=story_qa, world_qa=world_qa, world=world)


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world is not None:
        print(dump_trace(sample.world))
    if qa:
        print()
        print(format_qa(sample))


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
    lines.append("== (3) World-knowledge questions ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        bits = []
        if e.meters:
            bits.append(f"meters={dict(e.meters)}")
        if e.memes:
            bits.append(f"memes={dict(e.memes)}")
        if e.carried_by:
            bits.append(f"carried_by={e.carried_by}")
        lines.append(f"  {e.id:8} ({e.type:8}) {' '.join(bits)}")
    return "\n".join(lines)


ASP_RULES = r"""
damage_found(T) :- tote(T), tote_damage(T, D), D > 0.
friend_confesses(F) :- friend(F), guilt(F, G), G > 0.
repair_succeeds(T) :- damage_found(T), repair_progress(T, P), P > 0.
good_end :- damage_found(T), friend_confesses(F), repair_succeeds(T).
"""

def asp_facts() -> str:
    import asp
    lines = [
        asp.fact("tote", "tote"),
        asp.fact("friend", "friend"),
        asp.fact("tote_damage", "tote", 1),
        asp.fact("guilt", "friend", 1),
        asp.fact("repair_progress", "tote", 1),
    ]
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    try:
        import asp
    except Exception as err:  # pragma: no cover
        print(f"ASP unavailable: {err}")
        return 1
    model = asp.one_model(asp_program("#show good_end/0."))
    ok = any(sym.name == "good_end" for sym in model)
    if ok:
        print("OK: ASP twin can derive a good ending.")
        return 0
    print("MISMATCH: ASP twin failed to derive a good ending.")
    return 1


CURATED = [
    StoryParams(place="the library", hero_name="Mina", hero_type="girl", friend_name="Bozo", friend_type="boy"),
    StoryParams(place="the market", hero_name="Leo", hero_type="boy", friend_name="Pia", friend_type="girl"),
    StoryParams(place="the station", hero_name="Nia", hero_type="girl", friend_name="Max", friend_type="boy"),
]


def resolve_rejection(params: StoryParams) -> None:
    if params.hero_name == params.friend_name:
        raise StoryError("The detective and the friend must not be the same person.")


def generate_many(args: argparse.Namespace) -> list[StorySample]:
    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    out: list[StorySample] = []
    seen: set[str] = set()
    i = 0
    while len(out) < args.n and i < max(50, args.n * 20):
        seed = base_seed + i
        i += 1
        params = resolve_params(args, random.Random(seed))
        params.seed = seed
        resolve_rejection(params)
        sample = generate(params)
        if sample.story in seen:
            continue
        seen.add(sample.story)
        out.append(sample)
    return out


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show good_end/0."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(asp_program("#show good_end/0."))
        return

    samples = [generate(p) for p in CURATED] if args.all else generate_many(args)
    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for idx, sample in enumerate(samples):
        header = f"### variant {idx + 1}" if len(samples) > 1 and not args.all else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if idx < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()

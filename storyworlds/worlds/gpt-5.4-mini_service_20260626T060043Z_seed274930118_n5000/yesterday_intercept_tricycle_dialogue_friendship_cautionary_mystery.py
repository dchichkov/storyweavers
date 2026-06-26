#!/usr/bin/env python3
"""
A standalone storyworld script for a small mystery-style domain:
yesterday, an intercepted tricycle, a friendship, and a cautionary turn.

The model is a tiny classical simulation: a child notices a missing tricycle,
asks around, follows clues, and learns a gentle caution about borrowing
without asking. The ending proves what changed in the world state.
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
    kind: str = "thing"  # character | thing | place
    type: str = ""
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "mother", "aunt", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "uncle", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]


@dataclass
class Place:
    name: str
    detail: str


@dataclass
class Clue:
    id: str
    label: str
    reveals: str
    caution: str


@dataclass
class StoryParams:
    place: str
    hero: str
    friend: str
    tricycle: str
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
    "porch": Place("the porch", "a quiet porch with a low rail and two steps"),
    "yard": Place("the yard", "a narrow yard with a brick path and a gate"),
    "alley": Place("the alley", "a little alley between fences and climbing vines"),
}

HEROES = {
    "Mina": {"type": "girl", "trait": "curious"},
    "Noah": {"type": "boy", "trait": "careful"},
    "Lena": {"type": "girl", "trait": "gentle"},
    "Owen": {"type": "boy", "trait": "quiet"},
}

FRIENDS = {
    "Pip": {"type": "boy", "trait": "loyal"},
    "June": {"type": "girl", "trait": "steady"},
    "Arlo": {"type": "boy", "trait": "kind"},
    "Ivy": {"type": "girl", "trait": "bright"},
}

TRICYCLES = {
    "red": Clue("red", "a red tricycle", "fresh paint on the wheel", "no one should take it without asking"),
    "blue": Clue("blue", "a blue tricycle", "a bell that still jingled softly", "borrowing should be honest"),
    "yellow": Clue("yellow", "a yellow tricycle", "a ribbon caught in the handlebars", "a missing ride can worry a friend"),
}

PROMPTS = [
    'Write a short mystery story for a child that includes the word "yesterday".',
    'Tell a gentle friendship story where someone notices an intercepted tricycle and asks careful questions.',
    'Write a cautionary story with dialogue, clues, and a happy ending about borrowing a tricycle.',
]

ASP_RULES = r"""
place(porch;yard;alley).
hero_mood(curious;careful;gentle;quiet).
friend_trait(loyal;steady;kind;bright).
tricycle(red;blue;yellow).

mystery(Place,Hero,Friend,Tricycle) :- place(Place), tricycle(Tricycle).

#show mystery/4.
"""


def asp_facts() -> str:
    import asp
    lines = []
    for p in PLACES:
        lines.append(asp.fact("place", p))
    for h in HEROES:
        lines.append(asp.fact("hero", h))
    for f in FRIENDS:
        lines.append(asp.fact("friend", f))
    for t in TRICYCLES:
        lines.append(asp.fact("tricycle", t))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


# ---------------------------------------------------------------------------
# Story simulation
# ---------------------------------------------------------------------------
def introduce(world: World, hero: Entity, friend: Entity, tric: Entity) -> None:
    world.say(
        f"Yesterday, {hero.id} noticed that {tric.phrase} was missing from {world.place.name}."
    )
    world.say(
        f"{hero.id} was {hero.meters.get('trait', 0) and 'careful' or 'curious'}, and {friend.id} was the kind of friend who listened."
    )
    hero.memes["worry"] = 1
    friend.memes["care"] = 1
    world.facts["hero"] = hero
    world.facts["friend"] = friend
    world.facts["tricycle"] = tric


def question_around(world: World, hero: Entity, friend: Entity, tric: Entity) -> None:
    world.para()
    world.say(
        f'"Did you see {tric.phrase}?" {hero.id} asked. "It was here yesterday," {hero.pronoun()} said.'
    )
    world.say(
        f'"I saw someone intercept it near the gate," {friend.id} said. "But I also saw a ribbon caught on the handlebars."'
    )
    hero.memes["mystery"] = 1
    world.facts["clue"] = "ribbon"


def follow_clue(world: World, hero: Entity, friend: Entity, tric: Entity) -> None:
    world.para()
    world.say(
        f"{hero.id} and {friend.id} followed the clue to the gate, then to the alley, where the wheels had left a faint line in the dust."
    )
    world.say(
        f'"Maybe it was stolen?" {hero.id} whispered. "Or maybe somebody was trying to fix it and forgot to ask," {friend.id} said.'
    )
    hero.memes["fear"] = 1
    friend.memes["loyalty"] = 1
    world.facts["caution"] = "ask_before_borrowing"


def resolve(world: World, hero: Entity, friend: Entity, tric: Entity) -> None:
    world.para()
    tric.meters["found"] = 1
    tric.owner = hero.id
    world.say(
        f'Then a small voice answered from behind the porch. "I moved it," said {friend.id}. "I wanted to surprise {hero.id} by fixing the loose wheel."'
    )
    world.say(
        f'{hero.id} blinked, then smiled. "Next time, please ask first," {hero.id} said. {friend.id} nodded, and the two friends rolled {tric.phrase} back together.'
    )
    world.say(
        f"By evening, the tricycle was safe again, and {hero.id} knew the best mysteries end with honesty, not guessing."
    )
    hero.memes["relief"] = 1
    hero.memes["trust"] = 1
    friend.memes["shame"] = 0
    friend.memes["trust"] = 1


def tell(place_key: str, hero_name: str, friend_name: str, tric_key: str) -> World:
    world = World(PLACES[place_key])
    hero_cfg = HEROES[hero_name]
    friend_cfg = FRIENDS[friend_name]
    tric_cfg = TRICYCLES[tric_key]

    hero = world.add(Entity(id=hero_name, kind="character", type=hero_cfg["type"]))
    friend = world.add(Entity(id=friend_name, kind="character", type=friend_cfg["type"]))
    tric = world.add(Entity(id=tric_key, kind="thing", label=tric_cfg.label, phrase=tric_cfg.label, owner=hero.id))

    hero.meters["trait"] = 1
    friend.meters["trait"] = 1

    world.facts["place"] = world.place
    world.facts["mystery"] = "tricycle"

    introduce(world, hero, friend, tric)
    question_around(world, hero, friend, tric)
    follow_clue(world, hero, friend, tric)
    resolve(world, hero, friend, tric)
    return world


# ---------------------------------------------------------------------------
# Q&A
# ---------------------------------------------------------------------------
def story_qa(world: World) -> list[QAItem]:
    hero = world.facts["hero"]
    friend = world.facts["friend"]
    tric = world.facts["tricycle"]
    place = world.facts["place"].name
    return [
        QAItem(
            question=f"What was missing yesterday at {place}?",
            answer=f"Yesterday, {tric.phrase} was missing from {place}. That was the mystery {hero.id} and {friend.id} tried to solve.",
        ),
        QAItem(
            question=f"Who helped {hero.id} look for the tricycle?",
            answer=f"{friend.id} helped by listening, sharing a clue, and walking with {hero.id} to follow the tracks.",
        ),
        QAItem(
            question="What did they learn at the end?",
            answer="They learned to ask before moving someone else's thing, even when the reason seems kind or exciting.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a tricycle?",
            answer="A tricycle is a three-wheeled ride for a child to pedal and steer.",
        ),
        QAItem(
            question="What does intercept mean in this story?",
            answer="To intercept something means to stop it or take it in the middle of its path, often before it gets where it was going.",
        ),
        QAItem(
            question="Why is it important to ask before borrowing?",
            answer="Asking first shows respect. It helps friends trust each other and prevents worry or misunderstanding.",
        ),
    ]


def generation_prompts(world: World) -> list[str]:
    return PROMPTS


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


# ---------------------------------------------------------------------------
# ASP helpers
# ---------------------------------------------------------------------------
def asp_valid() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show mystery/4."))
    return sorted(set(asp.atoms(model, "mystery")))


def asp_verify() -> int:
    py = set((p, h, f, t) for p in PLACES for h in HEROES for f in FRIENDS for t in TRICYCLES)
    cl = set(asp_valid())
    if py == cl:
        print(f"OK: clingo and Python agree on {len(py)} mystery tuples.")
        return 0
    print("Mismatch between clingo and Python.")
    if cl - py:
        print("only in clingo:", sorted(cl - py))
    if py - cl:
        print("only in python:", sorted(py - cl))
    return 1


# ---------------------------------------------------------------------------
# Standard interface
# ---------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Mystery-friendship cautionary storyworld.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--hero", choices=HEROES)
    ap.add_argument("--friend", choices=FRIENDS)
    ap.add_argument("--tricycle", choices=TRICYCLES)
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
    hero = args.hero or rng.choice(list(HEROES))
    friend = args.friend or rng.choice([f for f in FRIENDS if f != hero])
    tricycle = args.tricycle or rng.choice(list(TRICYCLES))
    if friend == hero:
        raise StoryError("Hero and friend must be different characters.")
    return StoryParams(place=place, hero=hero, friend=friend, tricycle=tricycle)


def generate(params: StoryParams) -> StorySample:
    world = tell(params.place, params.hero, params.friend, params.tricycle)
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
    for ent in world.entities.values():
        bits = []
        if ent.owner:
            bits.append(f"owner={ent.owner}")
        if ent.meters:
            bits.append(f"meters={ent.meters}")
        if ent.memes:
            bits.append(f"memes={ent.memes}")
        lines.append(f"{ent.id}: {ent.kind} {ent.type} {' '.join(bits)}")
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
        print(asp_program("#show mystery/4."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        triples = asp_valid()
        print(f"{len(triples)} compatible mystery tuples.")
        for t in triples[:20]:
            print(" ", t)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)

    if args.all:
        samples = []
        for p in PLACES:
            for h in HEROES:
                for f in FRIENDS:
                    if f == h:
                        continue
                    for t in TRICYCLES:
                        samples.append(generate(StoryParams(place=p, hero=h, friend=f, tricycle=t)))
    else:
        samples = []
        seen = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 50, 50):
            i += 1
            params = resolve_params(args, random.Random(base_seed + i))
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

    for idx, sample in enumerate(samples):
        header = f"### variant {idx + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if idx < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()

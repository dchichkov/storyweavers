#!/usr/bin/env python3
"""
storyworlds/worlds/ebony_caustic_friendship_teamwork_nursery_rhyme.py
======================================================================

A tiny nursery-rhyme storyworld about friendship and teamwork in a small
garden path where an ebony bird and a friend must handle a caustic mess.

Seed tale:
---
Ebony the little crow loved to hop and sing in the garden. One day she found a
caustic silver bottle left by the shed. The bottle was tipped, and a sharp
puddle hissed on the stones. Her friend Mouse saw it too, and the two of them
worked together: one fetched water, one fetched sand, and together they made
the nasty puddle safe. Then they sat in the warm sun and laughed, glad that
friends can help friends.

This world models:
- physical meters: spill, wet, safe, carried, clean
- emotional memes: joy, worry, trust, care, teamwork, friendship

The story is narrated in a soft nursery-rhyme cadence with simple concrete
images and a clear turn from worry to teamwork to relief.
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
# Entities and world state
# ---------------------------------------------------------------------------
@dataclass
class Entity:
    id: str
    kind: str = "thing"  # "character" | "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=lambda: {"spill": 0.0, "wet": 0.0, "safe": 0.0, "clean": 0.0})
    memes: dict[str, float] = field(default_factory=lambda: {"joy": 0.0, "worry": 0.0, "trust": 0.0, "care": 0.0, "teamwork": 0.0, "friendship": 0.0})

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "mother", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        if self.kind == "character":
            return {"subject": "they", "object": "them", "possessive": "their"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class Setting:
    place: str = "the garden path"
    light: str = "warm"


@dataclass
class StoryParams:
    place: str
    hero: str
    friend: str
    seed: Optional[int] = None


class World:
    def __init__(self, setting: Setting):
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.lines: list[str] = []
        self.facts: dict = {}

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str) -> Entity:
        return self.entities[eid]

    def say(self, text: str) -> None:
        if text:
            self.lines.append(text)

    def render(self) -> str:
        return " ".join(self.lines)

    def chars(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.kind == "character"]


# ---------------------------------------------------------------------------
# Registry
# ---------------------------------------------------------------------------
SETTINGS = {
    "garden": Setting(place="the garden path", light="warm"),
    "yard": Setting(place="the yard", light="soft"),
    "orchard": Setting(place="the orchard path", light="golden"),
}

HEROES = {
    "ebony_crow": {
        "type": "crow",
        "label": "the ebony crow",
        "phrase": "an ebony little crow",
        "nickname": "Ebony",
    }
}

FRIENDS = {
    "mouse": {
        "type": "mouse",
        "label": "the mouse",
        "phrase": "a tiny mouse",
        "nickname": "Moss",
    },
    "rabbit": {
        "type": "rabbit",
        "label": "the rabbit",
        "phrase": "a bright little rabbit",
        "nickname": "Pip",
    },
}

ASP_RULES = r"""
% A caustic spill is unsafe unless teamwork gathers water and sand.
unsafe(S) :- spill(S), caustic(S), not neutralized(S).
neutralized(S) :- watered(S), sanded(S).
safe_story(P,H,F) :- friendship(H,F), teamwork(H,F), neutralized(spill1).
"""

# ---------------------------------------------------------------------------
# ASP facts
# ---------------------------------------------------------------------------
def asp_facts() -> str:
    import asp
    lines = [
        asp.fact("spill", "spill1"),
        asp.fact("caustic", "spill1"),
        asp.fact("friendship", "ebony", "friend"),
        asp.fact("teamwork", "ebony", "friend"),
    ]
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show safe_story/3."))
    ok = bool(asp.atoms(model, "safe_story"))
    if ok:
        print("OK: ASP model reaches a safe story.")
        return 0
    print("MISMATCH: ASP model did not reach a safe story.")
    return 1


# ---------------------------------------------------------------------------
# World logic
# ---------------------------------------------------------------------------
def build_world(params: StoryParams) -> World:
    setting = SETTINGS[params.place]
    world = World(setting)

    hero_cfg = HEROES[params.hero]
    friend_cfg = FRIENDS[params.friend]

    hero = world.add(Entity(
        id="ebony",
        kind="character",
        type=hero_cfg["type"],
        label=hero_cfg["label"],
        phrase=hero_cfg["phrase"],
    ))
    friend = world.add(Entity(
        id="friend",
        kind="character",
        type=friend_cfg["type"],
        label=friend_cfg["label"],
        phrase=friend_cfg["phrase"],
    ))
    spill = world.add(Entity(
        id="spill1",
        type="spill",
        label="caustic spill",
        phrase="a sharp little caustic puddle",
        caretaker="ebony",
    ))
    bucket = world.add(Entity(
        id="bucket",
        type="bucket",
        label="a bucket",
        phrase="a small bucket of water",
    ))
    sand = world.add(Entity(
        id="sand",
        type="sand",
        label="a tin of sand",
        phrase="a tin of soft sand",
    ))

    world.facts.update(hero=hero, friend=friend, spill=spill, bucket=bucket, sand=sand)
    return world


def _intro(world: World) -> None:
    hero: Entity = world.facts["hero"]
    friend: Entity = world.facts["friend"]
    world.say(
        f"In {world.setting.place}, there lived an ebony crow named Ebony, "
        f"and a friend who liked to follow along."
    )
    world.say(
        f"They sang by the stones and skipped in the {world.setting.light} light, "
        f"for friendship made the little day feel bright."
    )


def _turn(world: World) -> None:
    spill: Entity = world.facts["spill"]
    hero: Entity = world.facts["hero"]
    friend: Entity = world.facts["friend"]

    spill.meters["spill"] = 1.0
    spill.metes = spill.meters
    hero.memes["worry"] += 1
    friend.memes["worry"] += 1
    world.say(
        "Then Ebony saw a caustic puddle by the shed, and the sharp little puddle "
        "made both friends stop and look."
    )
    world.say(
        "It hissed on the stones and glimmered meanly, so they knew it must be "
        "handled with care."
    )


def _teamwork(world: World) -> None:
    hero: Entity = world.facts["hero"]
    friend: Entity = world.facts["friend"]
    bucket: Entity = world.facts["bucket"]
    sand: Entity = world.facts["sand"]
    spill: Entity = world.facts["spill"]

    hero.memes["friendship"] += 1
    friend.memes["friendship"] += 1
    hero.memes["teamwork"] += 1
    friend.memes["teamwork"] += 1
    hero.memes["trust"] += 1
    friend.memes["trust"] += 1

    world.say(
        f"Ebony fetched the bucket, and the friend fetched the tin of sand."
    )
    world.say(
        f"One tipped water in a gentle stream, and one scattered sand like snow."
    )

    spill.meters["spill"] = 0.0
    spill.meters["safe"] = 1.0
    spill.meters["clean"] = 1.0
    world.say(
        "Together they soothed the caustic puddle till it stopped hissing and grew safe."
    )


def _ending(world: World) -> None:
    hero: Entity = world.facts["hero"]
    friend: Entity = world.facts["friend"]
    world.say(
        f"Then Ebony and the friend sat in the warm grass and laughed in the sun."
    )
    world.say(
        "For when friends use teamwork side by side, even a caustic mess can turn to peace."
    )


def tell(params: StoryParams) -> World:
    world = build_world(params)
    _intro(world)
    world.say("")
    _turn(world)
    world.say("")
    _teamwork(world)
    world.say("")
    _ending(world)
    return world


# ---------------------------------------------------------------------------
# QA
# ---------------------------------------------------------------------------
def generation_prompts(world: World) -> list[str]:
    return [
        "Write a short nursery-rhyme story about an ebony bird and a friend who work together.",
        "Tell a gentle story where a caustic spill is made safe by friendship and teamwork.",
        "Make a child-friendly rhyme in which Ebony and a friend solve a messy problem together.",
    ]


def story_qa(world: World) -> list[QAItem]:
    hero: Entity = world.facts["hero"]
    friend: Entity = world.facts["friend"]
    return [
        QAItem(
            question="Who is the story about?",
            answer="It is about Ebony, an ebony crow, and a friend who helps Ebony handle the problem.",
        ),
        QAItem(
            question="What was wrong by the shed?",
            answer="A caustic puddle was on the stones, and it needed careful help before anyone could relax.",
        ),
        QAItem(
            question="How did Ebony and the friend fix the trouble?",
            answer="They used a bucket of water and a tin of sand, and together they made the spill safe.",
        ),
        QAItem(
            question="How did they feel at the end?",
            answer="They felt happy and calm, because friendship and teamwork turned worry into a good ending.",
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does friendship mean?",
            answer="Friendship means caring about someone, helping them, and enjoying time together.",
        ),
        QAItem(
            question="What does teamwork mean?",
            answer="Teamwork means people work together and each one helps in a useful way.",
        ),
        QAItem(
            question="What should you do with a caustic spill?",
            answer="You should keep away, get help, and use safe tools so the spill can be handled carefully.",
        ),
        QAItem(
            question="What does ebony mean?",
            answer="Ebony means very dark black, like the feathers of a crow or the shine of polished wood.",
        ),
    ]


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A tiny nursery-rhyme storyworld about ebony, caustic, friendship, and teamwork.")
    ap.add_argument("--place", choices=SETTINGS.keys())
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("-n", type=int, default=1)
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--trace", action="store_true")
    ap.add_argument("--qa", action="store_true")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--asp", action="store_true")
    ap.add_argument("--verify", action="store_true")
    ap.add_argument("--show-asp", action="store_true")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    place = args.place or rng.choice(list(SETTINGS.keys()))
    hero = "ebony_crow"
    friend = rng.choice(list(FRIENDS.keys()))
    return StoryParams(place=place, hero=hero, friend=friend, seed=args.seed)


def generate(params: StoryParams) -> StorySample:
    world = tell(params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_qa(world),
        world=world,
    )


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        lines.append(f"{e.id}: meters={ {k:v for k,v in e.meters.items() if v} } memes={ {k:v for k,v in e.memes.items() if v} }")
    return "\n".join(lines)


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world is not None:
        print(dump_trace(sample.world))
    if qa:
        print()
        for i, p in enumerate(sample.prompts, 1):
            print(f"Prompt {i}: {p}")
        print()
        for item in sample.story_qa:
            print(f"Q: {item.question}")
            print(f"A: {item.answer}")
        print()
        for item in sample.world_qa:
            print(f"Q: {item.question}")
            print(f"A: {item.answer}")


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show safe_story/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        model = asp.one_model(asp_program("#show safe_story/3."))
        print(f"{len(asp.atoms(model, 'safe_story'))} safe_story atoms")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        for place in SETTINGS:
            params = StoryParams(place=place, hero="ebony_crow", friend="mouse", seed=base_seed)
            samples.append(generate(params))
    else:
        for i in range(max(1, args.n)):
            rng = random.Random(base_seed + i)
            params = resolve_params(args, rng)
            params.seed = base_seed + i
            samples.append(generate(params))

    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        if len(samples) > 1:
            print(f"### variant {i + 1}")
        emit(sample, trace=args.trace, qa=args.qa)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()

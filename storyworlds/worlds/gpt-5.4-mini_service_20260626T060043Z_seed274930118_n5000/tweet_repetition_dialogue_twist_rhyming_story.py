#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260626T060043Z_seed274930118_n5000/tweet_repetition_dialogue_twist_rhyming_story.py
============================================================================================================

A small story world about a tiny bird, a curious tweet, and a rhyming turn.

Premise:
- A little bird wants to tweet a song at dawn.

Tension:
- The bird tries again and again, but the tweet sounds wrong and lonely.

Turn:
- Another bird answers in dialogue, and the repeated tweet is revealed to be a
  clue, not a mistake.

Resolution:
- The birds sing together, and the shared tweet becomes a happy chorus.

The world is constrained and simulated:
- physical meters track distance, warmth, and echoing sound
- emotional memes track hope, worry, and delight
- repetition matters: a tweet repeated too much can become a signal
- dialogue and a twist are state-driven, not bolted onto a frozen paragraph
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

# -----------------------------------------------------------------------------
# World model
# -----------------------------------------------------------------------------

THRESHOLD = 1.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    plural: bool = False
    owner: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"bird", "sparrow", "robin"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Place:
    name: str
    dawn: bool = True
    breeze: bool = False
    echo: bool = False
    perches: list[str] = field(default_factory=list)


@dataclass
class BirdSpec:
    name: str
    type: str
    trait: str


@dataclass
class StoryParams:
    place: str
    hero: str
    friend: str
    seed: Optional[int] = None


class World:
    def __init__(self, place: Place) -> None:
        self.place = place
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.fired: set[tuple] = set()
        self.trace: list[str] = []

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


# -----------------------------------------------------------------------------
# Registries
# -----------------------------------------------------------------------------

PLACES = {
    "bush": Place(name="the berry bush", dawn=True, breeze=True, echo=False, perches=["twig", "leaf"]),
    "pond": Place(name="the pond reeds", dawn=True, breeze=False, echo=True, perches=["reed", "stone"]),
    "roof": Place(name="the red roof", dawn=True, breeze=True, echo=True, perches=["chimney", "gutter"]),
}

BIRDS = {
    "pip": BirdSpec(name="Pip", type="bird", trait="tiny"),
    "mira": BirdSpec(name="Mira", type="bird", trait="bright"),
    "lulu": BirdSpec(name="Lulu", type="bird", trait="brave"),
    "taro": BirdSpec(name="Taro", type="bird", trait="quick"),
}

CURATED = [
    StoryParams(place="bush", hero="pip", friend="mira"),
    StoryParams(place="pond", hero="mira", friend="lulu"),
    StoryParams(place="roof", hero="lulu", friend="taro"),
]


# -----------------------------------------------------------------------------
# Simulation
# -----------------------------------------------------------------------------

def make_world(params: StoryParams) -> World:
    place = PLACES[params.place]
    world = World(place)
    hero_spec = BIRDS[params.hero]
    friend_spec = BIRDS[params.friend]

    hero = world.add(Entity(
        id=hero_spec.name,
        kind="character",
        type=hero_spec.type,
        label=hero_spec.name,
        phrase=f"a {hero_spec.trait} little bird",
        meters={"warmth": 1.0, "distance": 0.0, "echo": 0.0},
        memes={"hope": 1.0, "worry": 0.0, "joy": 0.0, "curiosity": 1.0},
    ))
    friend = world.add(Entity(
        id=friend_spec.name,
        kind="character",
        type=friend_spec.type,
        label=friend_spec.name,
        phrase=f"a {friend_spec.trait} little bird",
        meters={"warmth": 1.0, "distance": 1.0, "echo": 0.0},
        memes={"hope": 1.0, "worry": 0.0, "joy": 0.0, "curiosity": 1.0},
    ))
    world.facts["hero"] = hero
    world.facts["friend"] = friend
    world.facts["place"] = place
    return world


def repeat_tweet(world: World, hero: Entity, count: int = 3) -> None:
    hero.meters["echo"] += count
    hero.memes["hope"] += 0.5
    hero.memes["worry"] += 0.2 * max(0, count - 1)
    world.facts["repeats"] = count
    world.say(f"{hero.id} tried a tweet, a tweet, a sweet small tweet.")


def ask_and_answer(world: World, hero: Entity, friend: Entity) -> None:
    hero.meters["distance"] = 1.0
    friend.meters["distance"] = 1.0
    hero.memes["curiosity"] += 0.5
    friend.memes["curiosity"] += 0.5
    world.say(f'"Why do you tweet so neat?" asked {friend.id}, perched on a leaf.')
    world.say(f'"Because I seek a song to keep," said {hero.id}, "but it feels incomplete."')


def twist_reveal(world: World, hero: Entity, friend: Entity) -> None:
    # The repeated tweet wasn't only a song; it was a location clue.
    if world.place.echo:
        hero.memes["worry"] = max(0.0, hero.memes["worry"] - 0.5)
        friend.memes["joy"] += 1.0
        world.facts["twist"] = "echo"
        world.say(
            f"Then {friend.id} laughed, bright and fleet: "
            f'"Your tweet is not just song and beat; it bounces from the stones and reed."'
        )
        world.say(
            f'"That means the nest is near," said {hero.id}. '
            f'"My repeated tweet helped us read the trail indeed!"'
        )
    else:
        world.facts["twist"] = "reply"
        hero.memes["joy"] += 0.5
        friend.memes["joy"] += 0.5
        world.say(
            f"Then {friend.id} sang a matching tweet, and the two small birds made a rhythm sweet."
        )
        world.say(
            f'"It was a call, not a flaw," said {hero.id}. "A note that led my heart to meet."'
        )


def finish(world: World, hero: Entity, friend: Entity) -> None:
    hero.memes["joy"] += 1.5
    friend.memes["joy"] += 1.5
    hero.memes["hope"] += 1.0
    friend.memes["hope"] += 1.0
    world.say(
        f"So {hero.id} and {friend.id} made a duet in the dawnlit air, "
        f"tweeting together without a care."
    )
    world.say(
        f"The lonely tweet became a cheery song, and the little birds were brave and strong."
    )


def tell_story(params: StoryParams) -> World:
    world = make_world(params)
    hero = world.facts["hero"]
    friend = world.facts["friend"]

    world.say(
        f"At {world.place.name}, when the sky was pale and light, "
        f"{hero.id} was a tiny bird with a tune to share at first sight."
    )
    world.say(
        f"{hero.id} loved the dawn and liked to tweet; "
        f"her little throat made music neat."
    )
    world.para()

    repeat_tweet(world, hero, count=3)
    ask_and_answer(world, hero, friend)
    world.para()

    twist_reveal(world, hero, friend)
    finish(world, hero, friend)
    return world


# -----------------------------------------------------------------------------
# QA
# -----------------------------------------------------------------------------

def generation_prompts(world: World) -> list[str]:
    hero = world.facts["hero"]
    place = world.facts["place"]
    return [
        f'Write a short rhyming story about {hero.id} at {place.name} with a repeated tweet and a surprising twist.',
        f'Tell a child-friendly story where {hero.id} says "tweet" again and again, then a friend answers in dialogue.',
        f'Create a simple rhyme story with repetition, dialogue, and a twist about birds and a tweet.',
    ]


def story_qa(world: World) -> list[QAItem]:
    hero = world.facts["hero"]
    friend = world.facts["friend"]
    place = world.facts["place"]
    repeats = world.facts.get("repeats", 0)
    twist = world.facts.get("twist", "")
    return [
        QAItem(
            question=f"Who was the story about at {place.name}?",
            answer=f"It was about {hero.id}, a tiny bird who wanted to tweet a song at dawn.",
        ),
        QAItem(
            question=f"What did {hero.id} repeat before the other bird spoke?",
            answer=f"{hero.id} repeated a tweet, a tweet, a sweet small tweet, which showed the sound was important.",
        ),
        QAItem(
            question=f"Who answered {hero.id} in dialogue?",
            answer=f"{friend.id} answered first and asked why the tweet sounded so neat.",
        ),
        QAItem(
            question="What was the twist in the story?",
            answer=(
                "The repeated tweet was not just a song; it was also a clue. "
                "Because the place had echo, the tweet bounced and helped the birds understand the trail."
                if twist == "echo"
                else "The twist was that the second bird answered with the same tune, so the repeated tweet became a shared signal."
            ),
        ),
        QAItem(
            question=f"How many times did {hero.id} try the tweet at the beginning?",
            answer=f"{hero.id} tried it {repeats} times in a row, which made the sound feel repeated and important.",
        ),
    ]


WORLD_KNOWLEDGE = [
    QAItem(
        question="What is a tweet?",
        answer="A tweet is a short bird sound. Birds use tweets to sing, call, and answer one another.",
    ),
    QAItem(
        question="What is repetition in a story?",
        answer="Repetition means saying or doing something again and again on purpose, so it feels memorable and strong.",
    ),
    QAItem(
        question="What is dialogue?",
        answer="Dialogue is when characters speak to each other in a story.",
    ),
    QAItem(
        question="What is a twist in a story?",
        answer="A twist is a surprise that changes what the reader thinks is happening.",
    ),
    QAItem(
        question="Why do birds sing at dawn?",
        answer="Many birds sing at dawn to call to other birds and greet the new day.",
    ),
]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return list(WORLD_KNOWLEDGE)


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
        lines.append(
            f"  {e.id:8} ({e.kind:10}) meters={dict(e.meters)} memes={dict(e.memes)}"
        )
    lines.append(f"  place={world.place.name}")
    lines.append(f"  facts={{{', '.join(sorted(world.facts.keys()))}}}")
    return "\n".join(lines)


# -----------------------------------------------------------------------------
# ASP twin
# -----------------------------------------------------------------------------

ASP_RULES = r"""
hero(H) :- bird(H).
friend(F) :- bird(F).

repeated(H) :- tweet(H), tweet(H), tweet(H).
twist(echo) :- place(P), echo_place(P), repeated(H), bird(H).

shared_song(H,F) :- bird(H), bird(F), H != F, reply(F,H), tweet(H), tweet(F).
valid_story(P,H,F) :- place(P), bird(H), bird(F), H != F, repeated(H), dialogue(H,F), twist(echo).
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for pid, place in PLACES.items():
        lines.append(asp.fact("place", pid))
        if place.dawn:
            lines.append(asp.fact("dawn_place", pid))
        if place.breeze:
            lines.append(asp.fact("breeze_place", pid))
        if place.echo:
            lines.append(asp.fact("echo_place", pid))
        for perch in place.perches:
            lines.append(asp.fact("perch", pid, perch))

    for bid, bird in BIRDS.items():
        lines.append(asp.fact("bird", bid))
        lines.append(asp.fact("tweet", bid))
        lines.append(asp.fact("dialogue", bid, "x"))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_stories() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("#show valid_story/3."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    # Simple parity check: every curated story must be admissible.
    valid = set((p.place, p.hero, p.friend) for p in CURATED)
    asp_set = set(asp_valid_stories())
    if valid <= asp_set:
        print(f"OK: ASP accepts curated stories ({len(valid)} checked).")
        return 0
    print("MISMATCH between ASP and curated set:")
    print("  missing:", sorted(valid - asp_set))
    return 1


# -----------------------------------------------------------------------------
# CLI
# -----------------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Rhyming bird story with tweet, repetition, dialogue, and a twist.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--hero", choices=BIRDS)
    ap.add_argument("--friend", choices=BIRDS)
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
    hero = args.hero or rng.choice(list(BIRDS))
    friend = args.friend or rng.choice([k for k in BIRDS if k != hero])
    if hero == friend:
        raise StoryError("The hero and friend must be different birds.")
    return StoryParams(place=place, hero=hero, friend=friend)


def generate(params: StoryParams) -> StorySample:
    world = tell_story(params)
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
        stories = asp_valid_stories()
        print(f"{len(stories)} ASP-valid stories:")
        for row in stories:
            print("  ", row)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 20):
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

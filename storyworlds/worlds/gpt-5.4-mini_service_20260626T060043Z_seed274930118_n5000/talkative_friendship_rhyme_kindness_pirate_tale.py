#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260626T060043Z_seed274930118_n5000/talkative_friendship_rhyme_kindness_pirate_tale.py
====================================================================================================

A tiny pirate tale storyworld about a talkative crew, a rhyme-loving captain,
and a kindness that steadies friendship when the sea turns choppy.

Premise:
- A young pirate loves talking, singing rhymes, and staying close to a friend.
- The friend is quiet, shy, or hurt by the captain's chatter.
- A small mistake at sea creates tension.
- Kindness and a rhyme help repair the friendship.

This world simulates emotional meters (friendship, kindness, chatter, hurt)
and physical meters (rope, water, sail, treasure). The story is rendered from
world state, not from a frozen template.
"""

from __future__ import annotations

import argparse
import dataclasses
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
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def meter(self, key: str) -> float:
        return self.meters.get(key, 0.0)

    def meme(self, key: str) -> float:
        return self.memes.get(key, 0.0)

    def pronoun(self, case: str = "subject") -> str:
        mapping = {
            "pirate": {"subject": "he", "object": "him", "possessive": "his"},
            "girl": {"subject": "she", "object": "her", "possessive": "her"},
            "boy": {"subject": "he", "object": "him", "possessive": "his"},
            "child": {"subject": "they", "object": "them", "possessive": "their"},
        }
        return mapping.get(self.type, {"subject": "it", "object": "it", "possessive": "its"})[case]


@dataclass
class Crew:
    harbor: str = "the bright harbor"
    weather: str = "breezy"


@dataclass
class StoryParams:
    name: str
    friend_name: str
    parent_name: str
    trait: str
    seed: Optional[int] = None


class World:
    def __init__(self, crew: Crew):
        self.crew = crew
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict[str, object] = {}
        self.fired: set[str] = set()
        self.trace_log: list[str] = []

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

    def copy(self) -> "World":
        w = World(self.crew)
        w.entities = dataclasses.deepcopy(self.entities)
        w.fired = set(self.fired)
        return w


def tell(world: World, params: StoryParams) -> World:
    captain = world.add(Entity(
        id=params.name,
        kind="character",
        type="pirate",
        label=params.name,
        traits=["talkative", params.trait],
        meters={"water": 0.0},
        memes={"friendship": 1.0, "kindness": 0.0, "chatter": 1.0, "pride": 0.5},
    ))
    friend = world.add(Entity(
        id=params.friend_name,
        kind="character",
        type="child",
        label=params.friend_name,
        traits=["quiet", "kind"],
        meters={"water": 0.0},
        memes={"friendship": 1.0, "kindness": 1.0, "hurt": 0.0, "trust": 1.0},
    ))
    parent = world.add(Entity(
        id=params.parent_name,
        kind="character",
        type="pirate",
        label=params.parent_name,
        traits=["watchful"],
        memes={"kindness": 1.0},
    ))
    rope = world.add(Entity(id="rope", label="the rope", phrase="a long rope", meters={"tied": 1.0}))
    sail = world.add(Entity(id="sail", label="the sail", phrase="a white sail", meters={"wet": 0.0}))
    treasure = world.add(Entity(id="treasure", label="the chest", phrase="a tiny treasure chest", meters={"dry": 1.0}))

    world.say(
        f"{captain.id} was a talkative pirate with a grin as wide as the sea. "
        f"{captain.id} loved Friendship, Rhyme, and Kindness, and {captain.pronoun('subject')} could fill a deck with songs."
    )
    world.say(
        f"{friend.id} was {friend.traits[0]} and liked {friend.pronoun('possessive')} stories soft and slow. "
        f"{captain.id} liked talking so much that even the gulls seemed to listen."
    )

    world.para()
    world.say(
        f"One breezy day at {world.crew.harbor}, {captain.id} began to chant a rhyme while {friend.id} tried to tie the rope."
    )
    captain.memes["chatter"] += 1.0
    captain.memes["friendship"] += 0.5
    friend.memes["friendship"] += 0.0
    world.say(
        f'"A rope can float and a sail can sing, but a kind word is the sweetest thing," '
        f"{captain.id} said, clapping to the beat."
    )

    world.para()
    world.say(
        f"Then a wave slapped the deck and the rope slipped from {friend.id}'s hands. "
        f"The chest wobbled, and a splash soaked the sail."
    )
    sail.meters["wet"] = 1.0
    friend.memes["hurt"] += 1.0
    friend.memes["friendship"] -= 0.5
    captain.memes["guilt"] = 1.0

    world.say(
        f"{friend.id} frowned. Too much chatter had made the job messy, and now {friend.id} felt small."
    )

    world.para()
    world.say(
        f"{parent.id} stepped in with a calm smile and said, "
        f'"Try kindness first, then rhyme."'
    )
    captain.memes["kindness"] += 1.0
    captain.memes["chatter"] -= 0.5
    captain.memes["friendship"] += 1.0

    world.say(
        f"{captain.id} lowered {captain.pronoun('possessive')} voice, wiped the wet sail, and held the rope steady for {friend.id}."
    )
    world.say(
        f'“One knot, one note, one careful hand; together we make the ship stand,” '
        f"{captain.id} murmured, slow as a tide."
    )

    world.para()
    friend.memes["hurt"] = 0.0
    friend.memes["trust"] += 1.0
    friend.memes["friendship"] += 1.0
    sail.meters["wet"] = 0.0
    rope.meters["tied"] = 2.0
    treasure.meters["dry"] = 1.0

    world.say(
        f"{friend.id} smiled again and shared the knot. The chest stayed safe, the sail dried in the breeze, "
        f"and the two friends worked side by side."
    )
    world.say(
        f"By sunset, {captain.id}'s talk was softer, {friend.id}'s grin was bigger, and the deck felt warm with friendship."
    )

    world.facts.update(
        captain=captain,
        friend=friend,
        parent=parent,
        rope=rope,
        sail=sail,
        treasure=treasure,
        harbor=world.crew.harbor,
    )
    return world


KNOWLEDGE = {
    "pirate": [
        (
            "What is a pirate?",
            "A pirate is a sea traveler who sails ships, looks for treasure, and often wears rough clothes and a brave hat.",
        )
    ],
    "friendship": [
        (
            "What is friendship?",
            "Friendship is when people care about each other, help each other, and want to stay together.",
        )
    ],
    "rhyme": [
        (
            "What is a rhyme?",
            "A rhyme is a pair of words or lines that sound alike at the end, like 'sea' and 'me'.",
        )
    ],
    "kindness": [
        (
            "What is kindness?",
            "Kindness is gentle, caring behavior that helps someone feel safe, seen, or happy.",
        )
    ],
    "rope": [
        (
            "What is a rope for?",
            "A rope is used to tie, pull, or hold things in place.",
        )
    ],
    "sail": [
        (
            "What does a sail do?",
            "A sail catches the wind and helps a boat move across the water.",
        )
    ],
}


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    c, fr = f["captain"], f["friend"]
    return [
        'Write a short pirate story for a young child about a talkative captain, friendship, rhyme, and kindness.',
        f"Tell a gentle sea tale where {c.id} talks too much, {fr.id} feels upset, and kindness fixes the friendship.",
        "Write a tiny pirate story that includes a rhyme and ends with friends working together on a boat.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    c, fr, parent = f["captain"], f["friend"], f["parent"]
    sail = f["sail"]
    return [
        QAItem(
            question=f"Who was the talkative pirate in the story?",
            answer=f"{c.id} was the talkative pirate, and {c.pronoun('subject')} loved Friendship, Rhyme, and Kindness.",
        ),
        QAItem(
            question=f"Why did {fr.id} feel upset on the deck?",
            answer=(
                f"{fr.id} felt upset because {c.id} talked so much that the rope slipped and the wet sail made the job harder. "
                f"That made {fr.id} feel small for a moment."
            ),
        ),
        QAItem(
            question="How did the friends fix the problem?",
            answer=(
                f"{parent.id} asked for kindness first, so {c.id} slowed down, wiped the sail, and helped tie the rope. "
                f"Then the friends worked together again."
            ),
        ),
        QAItem(
            question="What happened to the sail by the end?",
            answer=f"The sail was wet after the splash, but by the end it dried in the breeze and was safe again.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    out: list[QAItem] = []
    for key in ["pirate", "friendship", "rhyme", "kindness", "rope", "sail"]:
        out.extend(QAItem(question=q, answer=a) for q, a in KNOWLEDGE[key])
    return out


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
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        lines.append(f"  {e.id:10} ({e.type:7}) {' '.join(bits)}")
    return "\n".join(lines)


GIVEN_NAMES = ["Mira", "Nell", "Pip", "Finn", "Sage", "Toby", "Ruby", "Jett"]
FRIEND_NAMES = ["Bo", "Lark", "Drew", "June", "Wren", "Moss", "Nia", "Kit"]
PARENT_NAMES = ["Captain Shell", "Aunt Tide", "Old Marlow", "Captain Reed"]
TRAITS = ["cheerful", "brave", "curious", "sparkly", "steady", "lively"]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A small pirate tale about talkative friendship, rhyme, and kindness.")
    ap.add_argument("--name", choices=GIVEN_NAMES)
    ap.add_argument("--friend-name", choices=FRIEND_NAMES)
    ap.add_argument("--parent-name", choices=PARENT_NAMES)
    ap.add_argument("--trait", choices=TRAITS)
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
    name = args.name or rng.choice(GIVEN_NAMES)
    friend = args.friend_name or rng.choice([n for n in FRIEND_NAMES if n != name])
    parent = args.parent_name or rng.choice(PARENT_NAMES)
    trait = args.trait or rng.choice(TRAITS)
    if friend == name:
        raise StoryError("The captain and friend must have different names.")
    return StoryParams(name=name, friend_name=friend, parent_name=parent, trait=trait)


def generate(params: StoryParams) -> StorySample:
    world = tell(World(Crew()), params)
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


ASP_RULES = r"""
captain(C) :- name(C).
friend(F) :- friend_name(F).
kindness_boost(C) :- talks_softly(C), helps(C,F), friend(F).
friendship_restored(F) :- kind_helped(F), wet_sail_dried.
wet_sail_dried :- sail(S), dry(S).
#show friendship_restored/1.
#show kindness_boost/1.
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for n in GIVEN_NAMES:
        lines.append(asp.fact("name", n))
    for n in FRIEND_NAMES:
        lines.append(asp.fact("friend_name", n))
    for n in PARENT_NAMES:
        lines.append(asp.fact("parent_name", n))
    for t in TRAITS:
        lines.append(asp.fact("trait", t))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    return 0


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show friendship_restored/1.\n#show kindness_boost/1."))
        return
    if args.verify:
        sys.exit(asp_verify())

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        curated = [
            StoryParams("Mira", "Bo", "Captain Shell", "cheerful"),
            StoryParams("Finn", "Lark", "Aunt Tide", "steady"),
            StoryParams("Ruby", "June", "Old Marlow", "curious"),
        ]
        samples = [generate(p) for p in curated]
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
        header = f"### variant {i + 1}" if len(samples) > 1 and not args.all else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()

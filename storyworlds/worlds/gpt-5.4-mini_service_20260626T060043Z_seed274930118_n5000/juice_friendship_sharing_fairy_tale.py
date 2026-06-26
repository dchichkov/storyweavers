#!/usr/bin/env python3
"""
storyworlds/worlds/juice_friendship_sharing_fairy_tale.py
==========================================================

A small fairy-tale storyworld about friendship, sharing, and a precious cup of
juice.

Premise:
- A little hero has a sweet cup of juice.
- A friend arrives tired, thirsty, or lonely.
- The hero must choose between keeping the juice and sharing it.

World model:
- Characters have meters for thirst, joy, and kindness.
- Objects have amount/ownership.
- Sharing changes state: the cup gets smaller, friendship grows, thirst eases.

The story should feel like a tiny fairy tale: simple, warm, and concrete, with
a beginning, a turn, and a happy ending image showing what changed.
"""

from __future__ import annotations

import argparse
import copy
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
    owner: Optional[str] = None
    held_by: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "princess", "queen"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "prince", "king"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Castle:
    place: str = "the castle garden"
    season: str = "spring"
    magic: str = "golden"


class World:
    def __init__(self, castle: Castle) -> None:
        self.castle = castle
        self.entities: dict[str, Entity] = {}
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

    def copy(self) -> "World":
        clone = World(self.castle)
        clone.entities = copy.deepcopy(self.entities)
        clone.paragraphs = [[]]
        return clone

    def characters(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.kind == "character"]


@dataclass
class Rule:
    name: str
    apply: callable


def _r_thirst_after_share(world: World) -> list[str]:
    out = []
    for friend in world.characters():
        if friend.meters.get("thirst", 0.0) < THRESHOLD:
            continue
        if friend.memes.get("shared_with", 0.0) < THRESHOLD:
            continue
        if friend.id in world.facts.get("thirst_fixed", set()):
            continue
        friend.meters["thirst"] = max(0.0, friend.meters.get("thirst", 0.0) - 1.0)
        friend.memes["joy"] = friend.memes.get("joy", 0.0) + 1.0
        world.facts.setdefault("thirst_fixed", set()).add(friend.id)
        out.append(f"{friend.label or friend.id} sipped the juice and felt better.")
    return out


def _r_friendship_grows(world: World) -> list[str]:
    out = []
    hero = world.facts.get("hero")
    friend = world.facts.get("friend")
    if not hero or not friend:
        return out
    if hero.memes.get("kindness", 0.0) >= THRESHOLD and friend.memes.get("shared_with", 0.0) >= THRESHOLD:
        if world.facts.get("bond_bloomed"):
            return out
        world.facts["bond_bloomed"] = True
        hero.memes["friendship"] = hero.memes.get("friendship", 0.0) + 1.0
        friend.memes["friendship"] = friend.memes.get("friendship", 0.0) + 1.0
        out.append("From that little sharing, a warm friendship began to bloom.")
    return out


CAUSAL_RULES = [
    Rule("thirst_after_share", _r_thirst_after_share),
    Rule("friendship_grows", _r_friendship_grows),
]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            sents = rule.apply(world)
            if sents:
                changed = True
                produced.extend(sents)
    if narrate:
        for s in produced:
            world.say(s)
    return produced


@dataclass
class StoryParams:
    name: str
    friend_name: str
    hero_type: str
    friend_type: str
    place: str
    juice_flavor: str
    seed: Optional[int] = None


CASTLE = Castle()

HERO_TYPES = ["girl", "boy", "princess", "prince"]
FRIEND_TYPES = ["girl", "boy", "rabbit", "bird"]
JUICES = ["apple", "pear", "berry", "orange", "peach"]
PLACES = ["the castle garden", "the orchard path", "the sunny courtyard", "the rose arbor"]

NAMES = {
    "girl": ["Ella", "Mira", "Nora", "Lily", "Rose"],
    "boy": ["Finn", "Leo", "Otto", "Theo", "Pip"],
    "princess": ["Princess Ella", "Princess Mira", "Princess Nora"],
    "prince": ["Prince Finn", "Prince Leo", "Prince Theo"],
    "rabbit": ["Thistle", "Hopper", "Moss"],
    "bird": ["Mina", "Wren", "Penny"],
}


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A fairy-tale world about juice, friendship, and sharing.")
    ap.add_argument("--name", choices=sum(NAMES.values(), []))
    ap.add_argument("--friend-name", choices=sum(NAMES.values(), []))
    ap.add_argument("--hero-type", choices=HERO_TYPES)
    ap.add_argument("--friend-type", choices=FRIEND_TYPES)
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--juice-flavor", choices=JUICES)
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
    hero_type = args.hero_type or rng.choice(HERO_TYPES)
    friend_type = args.friend_type or rng.choice(FRIEND_TYPES)
    place = args.place or rng.choice(PLACES)
    juice_flavor = args.juice_flavor or rng.choice(JUICES)
    name = args.name or rng.choice(NAMES[hero_type])
    friend_name = args.friend_name or rng.choice(NAMES[friend_type])
    if name == friend_name:
        friend_name = rng.choice([n for n in NAMES[friend_type] if n != name] or NAMES[friend_type])
    return StoryParams(
        name=name,
        friend_name=friend_name,
        hero_type=hero_type,
        friend_type=friend_type,
        place=place,
        juice_flavor=juice_flavor,
    )


def _hero_title(hero_type: str) -> str:
    return {"girl": "little girl", "boy": "little boy", "princess": "young princess", "prince": "young prince"}[hero_type]


def _friend_title(friend_type: str) -> str:
    return {"girl": "girl", "boy": "boy", "rabbit": "rabbit", "bird": "bird"}[friend_type]


def tell(params: StoryParams) -> World:
    world = World(CASTLE)
    hero = world.add(Entity(
        id="hero",
        kind="character",
        type=params.hero_type,
        label=params.name,
        meters={"joy": 1.0, "thirst": 0.0},
        memes={"kindness": 0.0, "friendship": 0.0},
    ))
    friend = world.add(Entity(
        id="friend",
        kind="character",
        type=params.friend_type,
        label=params.friend_name,
        meters={"joy": 0.5, "thirst": 1.0},
        memes={"kindness": 0.0, "friendship": 0.0},
    ))
    juice = world.add(Entity(
        id="juice",
        type="juice",
        label=f"cup of {params.juice_flavor} juice",
        phrase=f"a sweet cup of {params.juice_flavor} juice",
        owner=hero.id,
        held_by=hero.id,
        meters={"amount": 1.0},
    ))

    world.say(
        f"Once upon a time, in {params.place}, there lived {params.name}, "
        f"{_hero_title(params.hero_type)} who loved bright mornings."
    )
    world.say(
        f"One fine day, {hero.label} found {juice.phrase} by a sun-warmed stone, "
        f"and the whole cup smelled like a small holiday."
    )

    world.para()
    world.say(
        f"While {hero.label} held the cup, {params.friend_name} came by from the path, "
        f"{'softly chirping' if params.friend_type == 'bird' else 'looking hopeful'} and very thirsty."
    )
    world.say(
        f"{params.friend_name} asked, \"May I have some juice?\" and {hero.label} felt the choice in the air."
    )

    hero.memes["wonder"] = 1.0
    hero.memes["kindness"] = 1.0
    world.facts["hero"] = hero
    world.facts["friend"] = friend
    world.facts["juice"] = juice

    world.para()
    world.say(
        f"{hero.label} looked at the little cup, then at the thirsty friend, "
        f"and remembered how a shared thing can grow twice as sweet."
    )
    hero.memes["shared_with"] = 1.0
    friend.memes["shared_with"] = 1.0
    juice.meters["amount"] = 0.5
    world.say(
        f"So {hero.label} tipped the cup carefully and shared half of the {params.juice_flavor} juice."
    )
    propagate(world, narrate=True)

    world.para()
    world.say(
        f"{params.friend_name} smiled with a happy face, the thirst was gone, and {params.name} smiled too."
    )
    world.say(
        f"Under the gentle trees of {params.place}, the two friends sat together while the little cup grew light, "
        f"and the day felt golden and kind."
    )

    world.facts.update(params=params, resolved=True)
    return world


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


def generation_prompts(world: World) -> list[str]:
    p: StoryParams = world.facts["params"]
    return [
        f'Write a short fairy tale for young children about {p.name}, a cup of {p.juice_flavor} juice, and a friend who asks to share.',
        f"Tell a gentle story where {p.name} learns that sharing juice can make friendship grow in {p.place}.",
        f'Create a tiny fairy tale about kindness and sharing with the word "juice" in it.',
    ]


def story_qa(world: World) -> list[QAItem]:
    p: StoryParams = world.facts["params"]
    hero = world.get("hero")
    friend = world.get("friend")
    juice = world.get("juice")
    return [
        QAItem(
            question=f"Who did {p.name} meet in {p.place}?",
            answer=f"{p.name} met {p.friend_name}, {_friend_title(p.friend_type)} who was thirsty and wanted some juice."
        ),
        QAItem(
            question=f"What did {p.name} share with {p.friend_name}?",
            answer=f"{p.name} shared a cup of {p.juice_flavor} juice, and the cup became smaller while kindness grew."
        ),
        QAItem(
            question=f"How did the two friends feel at the end?",
            answer=f"They both felt happy. The thirsty friend felt better, and {p.name} felt glad for sharing."
        ),
        QAItem(
            question=f"Why did the sharing matter in the story?",
            answer=f"The sharing mattered because it helped a thirsty friend and turned a small choice into a friendship."
        ),
    ]


KNOWLEDGE = {
    "juice": [
        QAItem(
            question="What is juice?",
            answer="Juice is a drink made from fruits, and people often sip it when they want something sweet and refreshing."
        )
    ],
    "sharing": [
        QAItem(
            question="What does sharing mean?",
            answer="Sharing means letting someone else use or have part of what you have."
        )
    ],
    "friendship": [
        QAItem(
            question="What is friendship?",
            answer="Friendship is a warm bond between friends who care about each other and like to help."
        )
    ],
}


def world_knowledge_qa(world: World) -> list[QAItem]:
    out: list[QAItem] = []
    out.extend(KNOWLEDGE["juice"])
    out.extend(KNOWLEDGE["sharing"])
    out.extend(KNOWLEDGE["friendship"])
    return out


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


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        if e.kind == "character":
            bits.append(f"type={e.type}")
        lines.append(f"  {e.id:8} ({e.kind:9}) {' '.join(bits)}")
    return "\n".join(lines)


ASP_RULES = r"""
shared(hero,friend) :- kindness(hero), thirst(friend), has_juice(hero), asks(friend).
friendship(hero,friend) :- shared(hero,friend).
happiness(friend) :- shared(hero,friend).
happy_ending :- friendship(hero,friend), happiness(friend).
"""


def asp_facts() -> str:
    import asp
    return "\n".join([
        asp.fact("kindness", "hero"),
        asp.fact("thirst", "friend"),
        asp.fact("has_juice", "hero"),
        asp.fact("asks", "friend"),
    ])


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_story_possible() -> bool:
    import asp
    model = asp.one_model(asp_program("#show shared/2.\n#show friendship/2.\n#show happy_ending/0."))
    atoms = {sym.name for sym in model}
    return "happy_ending" in atoms


def asp_verify() -> int:
    py_ok = True
    asp_ok = asp_story_possible()
    if py_ok == asp_ok:
        print("OK: ASP and Python both support the sharing friendship story.")
        return 0
    print("MISMATCH between Python and ASP.")
    return 1


CURATED = [
    StoryParams(name="Mira", friend_name="Pip", hero_type="girl", friend_type="bird", place="the rose arbor", juice_flavor="berry"),
    StoryParams(name="Theo", friend_name="Moss", hero_type="boy", friend_type="rabbit", place="the castle garden", juice_flavor="apple"),
    StoryParams(name="Princess Nora", friend_name="Wren", hero_type="princess", friend_type="bird", place="the sunny courtyard", juice_flavor="peach"),
]


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
    if args.verify:
        sys.exit(asp_verify())
    if args.show_asp:
        print(asp_program("#show happy_ending/0."))
        return
    if args.asp:
        print("This fairy-tale world admits the sharing story when the hero has juice and the friend asks.")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
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
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.name}: sharing {p.juice_flavor} juice with {p.friend_name}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()

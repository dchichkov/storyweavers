#!/usr/bin/env python3
"""
A small pirate-tale story world about a stubborn bull's opposite: a generous
sharing lesson that ends happily.

Premise:
- A tiny crew sails with a proud bull named Bramble.
- Bramble wants the opposite of keeping everything to himself: he learns to
  share treasure, snacks, and the map.
- A friendship problem appears when the crew finds one small gold coin and one
  last coconut.
- The turn is a shared plan instead of a grabbing contest.
- The happy ending proves the lesson learned: sharing makes the ship calmer and
  the crew merrier.

This script follows the Storyweavers storyworld contract.
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
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.meters:
            self.meters = {"safety": 0.0, "treasure": 0.0, "food": 0.0}
        if not self.memes:
            self.memes = {"greed": 0.0, "joy": 0.0, "trust": 0.0, "worry": 0.0}

    def pronoun(self, case: str = "subject") -> str:
        male = {"boy", "man", "father", "captain", "bull"}
        female = {"girl", "woman", "mother"}
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str = "the little pirate ship"
    sea: str = "calm"


@dataclass
class Item:
    id: str
    label: str
    phrase: str
    type: str
    shareable: bool = True


@dataclass
class StoryParams:
    place: str
    item: str
    name: str
    friend: str
    seed: Optional[int] = None


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.facts: dict = {}
        self.paragraphs: list[list[str]] = [[]]
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

    def copy(self) -> "World":
        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.facts = copy.deepcopy(self.facts)
        clone.paragraphs = [[]]
        clone.fired = set(self.fired)
        return clone


def _r_share(world: World) -> list[str]:
    out: list[str] = []
    crew = [e for e in world.entities.values() if e.kind == "character"]
    for actor in crew:
        if actor.memes["trust"] < THRESHOLD:
            continue
        sig = ("share", actor.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        actor.memes["joy"] += 1
        out.append(f"{actor.label} shared the load instead of clutching it tight.")
    return out


def propagate(world: World, narrate: bool = True) -> list[str]:
    lines: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in (_r_share,):
            out = rule(world)
            if out:
                changed = True
                lines.extend(out)
    if narrate:
        for line in lines:
            world.say(line)
    return lines


SETTINGS = {
    "ship": Setting(place="the little pirate ship", sea="calm"),
    "island": Setting(place="the palm island dock", sea="blue"),
}

ITEMS = {
    "coin": Item(id="coin", label="gold coin", phrase="a tiny gold coin", type="coin"),
    "coconut": Item(id="coconut", label="coconut", phrase="a sweet coconut", type="coconut"),
    "map": Item(id="map", label="map", phrase="the treasure map", type="map", shareable=False),
}

NAMES = ["Bramble", "Milo", "Tessa", "Ruby", "Finn"]
FRIENDS = ["parrot", "mouse", "sailor", "deckhand"]


def build_world(params: StoryParams) -> World:
    world = World(SETTINGS[params.place])

    hero = world.add(Entity(id=params.name, kind="character", type="bull", label=params.name))
    friend = world.add(Entity(id="friend", kind="character", type="pirate", label=params.friend))
    item = world.add(Entity(
        id="item",
        type=ITEMS[params.item].type,
        label=ITEMS[params.item].label,
        phrase=ITEMS[params.item].phrase,
        owner=hero.id,
    ))
    map_item = world.add(Entity(
        id="map",
        type="map",
        label="map",
        phrase="the treasure map",
        owner=friend.id,
    ))

    hero.memes["greed"] += 1
    friend.memes["worry"] += 1

    world.say(
        f"On the little pirate ship, {hero.id} was a brave bull with a loud voice and a soft heart."
    )
    world.say(
        f"{hero.id} loved shiny things, but he wanted the opposite of selfishness more and more: he wanted to share."
    )
    world.say(
        f"One day, {hero.id} and {friend.label} found {item.phrase} beside {map_item.phrase}."
    )

    world.para()
    world.say(
        f"{hero.id} reached for {item.label} first, and {friend.label} frowned because there was only one."
    )
    world.say(
        f"The wind tugged at the sails, and the ship felt small when everyone wanted the same prize."
    )

    world.para()
    hero.memes["worry"] += 1
    friend.memes["trust"] += 1
    world.say(
        f"Then {hero.id} took a breath and said, 'Let's share it in turn.'"
    )
    world.say(
        f"{hero.id} gave {friend.label} the map, and {friend.label} split the {item.label} so both could have a piece."
    )
    hero.memes["trust"] += 2
    friend.memes["joy"] += 2
    hero.memes["joy"] += 2

    propagate(world)

    world.para()
    world.say(
        f"After that, the ship grew cheerful again. {hero.id} laughed, {friend.label} waved, and the little crew sailed on with full bellies and calm paws."
    )
    world.say(
        f"It was a happy ending, and {hero.id} learned that sharing can make even a bull's biggest wish feel better."
    )

    world.facts.update(hero=hero, friend=friend, item=item, map_item=map_item, params=params)
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    item = f["item"]
    return [
        f'Write a short pirate tale for a young child about {hero.id}, a bull who learns to share a {item.label}.',
        f'Tell a story with pirates, a shiny object, and a happy ending where the opposite of selfishness wins.',
        f'Write a gentle adventure on a ship where a bull learns a lesson about sharing and friendship.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    friend = f["friend"]
    item = f["item"]
    return [
        QAItem(
            question=f"Who learns the sharing lesson in the story?",
            answer=f"{hero.id}, the bull, learns that sharing is better than keeping everything for himself."
        ),
        QAItem(
            question=f"What did {hero.id} and {friend.label} find on the pirate ship?",
            answer=f"They found {item.phrase} and the treasure map."
        ),
        QAItem(
            question=f"What made the story end happily?",
            answer=f"{hero.id} decided to share, so the friends stopped arguing and sailed away happily."
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does sharing mean?",
            answer="Sharing means letting other people use or enjoy something too."
        ),
        QAItem(
            question="What is a pirate ship?",
            answer="A pirate ship is a boat pirates sail on the sea."
        ),
        QAItem(
            question="What is a lesson learned?",
            answer="A lesson learned is a good idea someone understands after something happens."
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== Story questions =="]
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== World questions ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


ASP_RULES = r"""
hero_is_bull(hero).
item_shareable(coin).
item_shareable(coconut).
lesson_learned(hero) :- choose_share(hero).
happy_ending :- lesson_learned(hero).

choose_share(hero) :- wants_opposite_of_selfish(hero), item_shareable(Item).
wants_opposite_of_selfish(hero).
"""


def asp_facts() -> str:
    import asp
    return "\n".join([
        asp.fact("hero_is_bull", "hero"),
        asp.fact("wants_opposite_of_selfish", "hero"),
        asp.fact("item_shareable", "coin"),
        asp.fact("item_shareable", "coconut"),
    ])


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Pirate tale story world about sharing and a happy ending.")
    ap.add_argument("--place", choices=sorted(SETTINGS))
    ap.add_argument("--item", choices=sorted(ITEMS))
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


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    place = args.place or rng.choice(sorted(SETTINGS))
    item = args.item or rng.choice(sorted(ITEMS))
    if not ITEMS[item].shareable:
        raise StoryError("This story needs a shareable prize so the lesson can be about sharing.")
    name = args.name or rng.choice(NAMES)
    friend = args.friend or rng.choice(FRIENDS)
    return StoryParams(place=place, item=item, name=name, friend=friend)


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


def dump_trace(world: World) -> str:
    lines = ["--- trace ---"]
    for e in world.entities.values():
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        lines.append(f"{e.id}: type={e.type} label={e.label} meters={meters} memes={memes}")
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


def asp_valid() -> bool:
    import asp
    model = asp.one_model(asp_program("#show happy_ending/0. #show lesson_learned/1."))
    atoms = {str(a) for a in model}
    return "happy_ending" in atoms and "lesson_learned(hero)" in atoms


def asp_verify() -> int:
    if asp_valid():
        print("OK: ASP twin is consistent with the sharing lesson.")
        return 0
    print("MISMATCH: ASP twin did not produce the expected lesson.")
    return 1


CURATED = [
    StoryParams(place="ship", item="coin", name="Bramble", friend="Captain Dot"),
    StoryParams(place="island", item="coconut", name="Milo", friend="Matey Pip"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show happy_ending/0. #show lesson_learned/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print("ASP mode available for the sharing lesson world.")
        return

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        base_seed = args.seed if args.seed is not None else random.randrange(2**31)
        samples = []
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 20):
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            sample = generate(params)
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

    for i, sample in enumerate(samples):
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.name} / {p.item} / {p.place}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260626T060043Z_seed274930118_n5000/passion_lonely_faker_kindness_friendship_pirate_tale.py
===============================================================================================================================

A small pirate-tale story world about a lonely faker who longs for friendship,
keeps a noisy passion for grand adventures, and finds that kindness can turn a
false boast into a true bond.

Premise:
- A lonely pirate crew has room for one more.
- The main character is a faker: they brag big, but they are scared of being
  left out.
- Their passion is for sea songs, treasure stories, and being noticed.

Turn:
- The faker's boast nearly causes trouble because the crew expects a real plan.
- The captain sees through the bluff and answers with kindness instead of anger.

Resolution:
- Friendship becomes the real treasure.
- The faker admits the truth, helps with an honest task, and is welcomed in.
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
    worn_by: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "woman", "mother", "captainess"}
        male = {"boy", "man", "father", "captain"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Harbor:
    place: str = "the dock"
    affords: set[str] = field(default_factory=set)


@dataclass
class Action:
    id: str
    verb: str
    gerund: str
    rush: str
    mess: str
    soil: str
    keyword: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Prize:
    label: str
    phrase: str
    type: str
    signal: str
    plural: bool = False


@dataclass
class Gift:
    id: str
    label: str
    use: str
    prep: str
    tail: str


class World:
    def __init__(self, harbor: Harbor) -> None:
        self.harbor = harbor
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}

    def add(self, e: Entity) -> Entity:
        self.entities[e.id] = e
        return e

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


def _inc(obj: Entity, key: str, amt: float = 1.0) -> None:
    obj.meters[key] = obj.meters.get(key, 0.0) + amt


def _mem(obj: Entity, key: str, amt: float = 1.0) -> None:
    obj.memes[key] = obj.memes.get(key, 0.0) + amt


def is_lonely(hero: Entity) -> bool:
    return hero.memes.get("lonely", 0.0) >= THRESHOLD


def has_friendship(hero: Entity) -> bool:
    return hero.memes.get("friendship", 0.0) >= THRESHOLD


def tell(world: World, hero_name: str, hero_type: str, captain_type: str) -> World:
    hero = world.add(Entity(
        id=hero_name,
        kind="character",
        type=hero_type,
        traits=["little", "lonely", "faker", "brave"],
    ))
    captain = world.add(Entity(
        id="Captain",
        kind="character",
        type=captain_type,
        label="the captain",
        traits=["steady", "kind"],
    ))
    crew = world.add(Entity(
        id="Crew",
        kind="character",
        type="sailors",
        label="the crew",
        plural=True,
        traits=["curious"],
    ))
    map_piece = world.add(Entity(
        id="map",
        type="map",
        label="map",
        phrase="a torn map with a red X",
        owner=hero.id,
    ))

    hero.meters["passion"] = 1.0
    _mem(hero, "lonely", 1.0)
    _mem(hero, "faker", 1.0)

    world.say(
        f"On the deck of a little pirate ship, {hero.id} was a lonely faker with a big passion for sea stories."
    )
    world.say(
        f"{hero.id} loved to sing rough shanties and point at clouds as if every one hid treasure."
    )
    world.say(
        f"One day, {hero.id} held up {hero.pronoun('possessive')} {map_piece.label} and boasted that {hero.pronoun()} knew the way to the golden cove."
    )

    world.para()
    _inc(hero, "noise", 1.0)
    _mem(crew, "doubt", 1.0)
    world.say(
        f"The crew leaned closer, but the map was only half real, and the boat began to drift toward a rocky bend."
    )
    world.say(
        f"{hero.id}'s proud words made {hero.pronoun('object')} feel warm for a moment, yet the worry in {hero.pronoun('possessive')} chest grew colder."
    )

    world.para()
    _mem(captain, "kindness", 1.0)
    _mem(captain, "friendship", 1.0)
    world.say(
        f"The captain did not scold {hero.id}. Instead, {captain.pronoun()} smiled kindly and said, \"A true friend does not need to pretend.\""
    )
    world.say(
        f"{captain.pronoun().capitalize()} handed over a small lantern and asked {hero.id} to help read the stars with honest eyes."
    )

    world.para()
    _mem(hero, "friendship", 1.0)
    _mem(hero, "kindness", 1.0)
    _mem(hero, "bravery", 1.0)
    _mem(hero, "lonely", -1.0)
    _mem(hero, "faker", -1.0)
    world.say(
        f"{hero.id} swallowed hard and admitted the truth: {hero.pronoun('possessive')} map was a fake, and {hero.pronoun()} had only wanted to seem important."
    )
    world.say(
        f"The crew listened, then laughed gently, not meanly, because the truth sounded better than the boast."
    )
    world.say(
        f"Together they turned the ship with the lantern, the stars, and {hero.id}'s careful help."
    )
    world.say(
        f"By sunrise, the boat reached a bright little bay, and {hero.id} was no longer lonely; {hero.pronoun()} had friendship, kindness, and a real place on deck."
    )

    world.facts.update(
        hero=hero,
        captain=captain,
        crew=crew,
        map_piece=map_piece,
        harbor=world.harbor,
        story_place=world.harbor.place,
    )
    return world


@dataclass
class StoryParams:
    name: str
    hero_type: str
    captain_type: str
    seed: Optional[int] = None


NAMES = ["Milo", "Nina", "Pip", "Jory", "Tess", "Rae", "Sailor", "Bram"]
HERO_TYPES = ["boy", "girl"]
CAPTAIN_TYPES = ["captain"]
HARBOR = Harbor(place="the dock", affords={"boast", "sing", "confess", "help"})


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    return [
        "Write a short pirate tale for a young child about a lonely faker who learns friendship through kindness.",
        f"Tell a gentle shipboard story where {hero.id} pretends to know a treasure route, then tells the truth and is welcomed in.",
        "Write a tiny pirate adventure that includes kindness, friendship, a fake map, and a happy sunrise ending.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    captain = f["captain"]
    return [
        QAItem(
            question=f"Why did {hero.id} feel bad after showing the map?",
            answer=(
                f"{hero.id} felt bad because the map was fake and {hero.pronoun()} had pretended to know the way. "
                f"{hero.pronoun().capitalize()} wanted attention, but that did not feel good for long."
            ),
        ),
        QAItem(
            question=f"What did the captain do instead of scolding {hero.id}?",
            answer=(
                f"The captain answered with kindness. {captain.pronoun().capitalize()} gave {hero.id} a lantern, "
                f"spoke gently, and asked for honest help."
            ),
        ),
        QAItem(
            question=f"How did {hero.id} change by the end of the story?",
            answer=(
                f"{hero.id} stopped pretending, admitted the truth, and joined the crew as a real friend. "
                f"{hero.pronoun().capitalize()} ended the story feeling less lonely and much more welcomed."
            ),
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is kindness?",
            answer="Kindness is when you treat someone gently and helpfully, especially when they are worried or embarrassed.",
        ),
        QAItem(
            question="What is friendship?",
            answer="Friendship is a caring bond between people who like each other, help each other, and spend time together.",
        ),
        QAItem(
            question="What is a pirate tale?",
            answer="A pirate tale is a sea adventure story with ships, maps, treasure, and brave sailors.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts -- asks that would produce this story ==",]
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
        bits = []
        if e.meters:
            bits.append(f"meters={dict(e.meters)}")
        if e.memes:
            bits.append(f"memes={dict(e.memes)}")
        lines.append(f"  {e.id:8} ({e.type:8}) {' '.join(bits)}")
    return "\n".join(lines)


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    lines.append(asp.fact("setting", "dock"))
    lines.append(asp.fact("affords", "dock", "boast"))
    lines.append(asp.fact("affords", "dock", "sing"))
    lines.append(asp.fact("affords", "dock", "confess"))
    lines.append(asp.fact("affords", "dock", "help"))
    lines.append(asp.fact("virtue", "kindness"))
    lines.append(asp.fact("virtue", "friendship"))
    lines.append(asp.fact("trait", "faker"))
    lines.append(asp.fact("trait", "lonely"))
    return "\n".join(lines)


ASP_RULES = r"""
#show valid_story/1.

valid_story(ok) :- virtue(kindness), virtue(friendship), trait(faker), trait(lonely), setting(dock).
"""


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show valid_story/1."))
    ok = bool(model)
    if ok:
        print("OK: ASP gate accepts the pirate tale world.")
        return 0
    print("MISMATCH: ASP gate rejected the pirate tale world.")
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Pirate tale story world with a lonely faker and a kind crew.")
    ap.add_argument("--name", choices=NAMES)
    ap.add_argument("--hero-type", choices=HERO_TYPES)
    ap.add_argument("--captain-type", choices=CAPTAIN_TYPES)
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
    name = args.name or rng.choice(NAMES)
    hero_type = args.hero_type or rng.choice(HERO_TYPES)
    captain_type = args.captain_type or "captain"
    return StoryParams(name=name, hero_type=hero_type, captain_type=captain_type, seed=args.seed)


def generate(params: StoryParams) -> StorySample:
    world = tell(World(HARBOR), params.name, params.hero_type, params.captain_type)
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
        print(asp_program("#show valid_story/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        model = asp.one_model(asp_program("#show valid_story/1."))
        print("ASP model:", asp.atoms(model, "valid_story"))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        curated = [
            StoryParams(name="Milo", hero_type="boy", captain_type="captain", seed=base_seed),
            StoryParams(name="Nina", hero_type="girl", captain_type="captain", seed=base_seed + 1),
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
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()

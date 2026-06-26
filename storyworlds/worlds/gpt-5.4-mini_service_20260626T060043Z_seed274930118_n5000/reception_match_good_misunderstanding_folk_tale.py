#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260626T060043Z_seed274930118_n5000/reception_match_good_misunderstanding_folk_tale.py
================================================================================================

A small folk-tale storyworld about a village reception, a "match," and a good
but mistaken first impression.

Core premise:
- A village holds a reception after a long journey home.
- The host wants to make a "good match" between two shy young people.
- The word "match" is misunderstood as a fire match, which causes a brief
  stir around the lanterns and the tea.
- The misunderstanding is cleared, and the tale ends with warmth, music, and
  the promised match made true.

The world model tracks physical state (meters) and emotional state (memes):
- lantern_warmth, tea_spill, ash, distance, bloom
- hope, worry, trust, embarrassment, relief

The prose is generated from simulated state rather than a frozen template.
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

# ---------------------------------------------------------------------------
# Small domain constants
# ---------------------------------------------------------------------------
THRESHOLD = 1.0

PEOPLE = ["girl", "boy", "woman", "man", "grandmother", "grandfather"]
NAMES = {
    "girl": ["Anya", "Mina", "Suri", "Lina", "Pema"],
    "boy": ["Taro", "Niko", "Borin", "Milan", "Arin"],
    "woman": ["Hana", "Riva", "Nelia", "Sorra", "Yuna"],
    "man": ["Oren", "Marek", "Dalen", "Eko", "Soren"],
    "grandmother": ["Baba Ilya", "Grandma Tila", "Nana Sera"],
    "grandfather": ["Grandpa Jori", "Old Pavo", "Grandfather Niran"],
}
TRAITS = ["kind", "shy", "bright", "gentle", "patient", "cheerful"]

# ---------------------------------------------------------------------------
# World entities
# ---------------------------------------------------------------------------
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
        if self.type in {"girl", "woman", "grandmother"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man", "grandfather"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str = "the village hall"
    outdoors: bool = False
    affords: set[str] = field(default_factory=set)


@dataclass
class StoryCast:
    host: str
    hero: str
    friend: str
    parent: str


@dataclass
class StoryParams:
    place: str
    host_kind: str
    hero_kind: str
    friend_kind: str
    host_name: str
    hero_name: str
    friend_name: str
    trait: str
    seed: Optional[int] = None


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
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
        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.paragraphs = [[]]
        clone.fired = set(self.fired)
        clone.facts = copy.deepcopy(self.facts)
        return clone


# ---------------------------------------------------------------------------
# Simulation rules
# ---------------------------------------------------------------------------
def _default_meter() -> dict[str, float]:
    return {"warmth": 0.0, "ash": 0.0, "tea_spill": 0.0, "distance": 0.0}


def _default_meme() -> dict[str, float]:
    return {"hope": 0.0, "worry": 0.0, "trust": 0.0, "embarrassment": 0.0, "relief": 0.0, "joy": 0.0}


def propagate(world: World, narrate: bool = True) -> list[str]:
    out: list[str] = []

    host = next((e for e in world.entities.values() if e.id.startswith("host")), None)
    hero = next((e for e in world.entities.values() if e.id.startswith("hero")), None)
    friend = next((e for e in world.entities.values() if e.id.startswith("friend")), None)
    matchbox = world.entities.get("match")
    if not host or not hero or not friend or not matchbox:
        return out

    # If the match is struck, warmth rises and the lanterns glow.
    if matchbox.meters.get("struck", 0.0) >= THRESHOLD and ("struck",) not in world.fired:
        world.fired.add(("struck",))
        host.meters["warmth"] = host.meters.get("warmth", 0.0) + 1.0
        world.say("The little flame made the lanterns glow softly over the reception table.")

    # Misunderstanding: the hero hears "match" and thinks it means the fire match.
    if hero.memes.get("worry", 0.0) >= THRESHOLD and friend.memes.get("worry", 0.0) >= THRESHOLD:
        if ("misunderstanding",) not in world.fired:
            world.fired.add(("misunderstanding",))
            hero.memes["embarrassment"] = hero.memes.get("embarrassment", 0.0) + 1.0
            friend.memes["embarrassment"] = friend.memes.get("embarrassment", 0.0) + 1.0
            out.append("The hall felt hushed, like everyone was waiting to hear what the word meant.")

    # Resolution: once the host explains, trust and relief rise.
    if host.memes.get("trust", 0.0) >= THRESHOLD and ("resolved",) not in world.fired:
        world.fired.add(("resolved",))
        hero.memes["worry"] = 0.0
        friend.memes["worry"] = 0.0
        hero.memes["relief"] = hero.memes.get("relief", 0.0) + 1.0
        friend.memes["relief"] = friend.memes.get("relief", 0.0) + 1.0
        hero.memes["joy"] = hero.memes.get("joy", 0.0) + 1.0
        friend.memes["joy"] = friend.memes.get("joy", 0.0) + 1.0
        out.append("The confusion lifted like mist over the road.")
    if narrate:
        for s in out:
            world.say(s)
    return out


# ---------------------------------------------------------------------------
# Story actions
# ---------------------------------------------------------------------------
def introduce(world: World, host: Entity, hero: Entity, friend: Entity) -> None:
    trait = next((t for t in hero.traits if t != "kind"), "kind")
    world.say(
        f"In the village, {host.id} was known for kind hands and a careful ear. "
        f"{hero.id} was a {trait} {hero.type} who liked quiet corners, and "
        f"{friend.id} was another shy soul who smiled at the ground."
    )


def reception_arrives(world: World, host: Entity, hero: Entity, friend: Entity) -> None:
    world.say(
        f"One evening, the neighbors gathered at {world.setting.place} for a reception with tea, bread, and bright cloth on the walls. "
        f"{host.id} welcomed {hero.id} and {friend.id} with a bow."
    )
    host.memes["hope"] = host.memes.get("hope", 0.0) + 1.0


def wants_good_match(world: World, host: Entity, hero: Entity, friend: Entity) -> None:
    host.memes["trust"] = host.memes.get("trust", 0.0) + 1.0
    hero.memes["hope"] = hero.memes.get("hope", 0.0) + 1.0
    friend.memes["hope"] = friend.memes.get("hope", 0.0) + 1.0
    world.say(
        f"{host.id} hoped to make a good match between {hero.id} and {friend.id}, because they both laughed at the same tiny things."
    )
    world.say(
        f"But when {host.id} said the word 'match,' the younger pair glanced at the matchbox beside the lamp and thought the host meant fire."
    )


def fear_the_spark(world: World, hero: Entity, friend: Entity) -> None:
    hero.memes["worry"] = hero.memes.get("worry", 0.0) + 1.0
    friend.memes["worry"] = friend.memes.get("worry", 0.0) + 1.0
    world.say(
        f"{hero.id} and {friend.id} looked at each other with round eyes. "
        f"They worried the host wanted them to strike the match or start a fuss."
    )


def show_the_match(world: World, host: Entity) -> None:
    matchbox = world.get("match")
    matchbox.meters["struck"] = 1.0
    propagate(world)
    world.say(
        f"{host.id} smiled, struck the match, and lit the lantern wick. "
        f"The flame was only for the tea table, warm and small as a firefly."
    )


def explain_good_match(world: World, host: Entity, hero: Entity, friend: Entity) -> None:
    world.say(
        f"Then {host.id} laughed kindly and said, 'A good match is not only a little fire-stick. "
        f"It can also mean two people who fit each other well.'"
    )
    world.say(
        f"{hero.id} and {friend.id} looked from the lantern to one another, and the meaning settled in like a bird on a branch."
    )
    host.memes["trust"] = host.memes.get("trust", 0.0) + 1.0
    propagate(world)


def end_with_dance(world: World, hero: Entity, friend: Entity, host: Entity) -> None:
    hero.memes["joy"] = hero.memes.get("joy", 0.0) + 1.0
    friend.memes["joy"] = friend.memes.get("joy", 0.0) + 1.0
    world.say(
        f"At last, {hero.id} and {friend.id} sat together by the warm tea, then rose to dance while {host.id} clapped along."
    )
    world.say(
        f"In that gentle hall, the good match was clear at last, and the little flame kept the room bright without burning anything at all."
    )


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------
SETTINGS = {
    "hall": Setting(place="the village hall", outdoors=False, affords={"reception"}),
    "court": Setting(place="the willow court", outdoors=True, affords={"reception"}),
    "porch": Setting(place="the long porch", outdoors=True, affords={"reception"}),
}


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
setting(hall).
setting(court).
setting(porch).

affords(hall,reception).
affords(court,reception).
affords(porch,reception).

kind(hero).
kind(friend).
kind(host).

% A match can mean two things in this tale:
% 1) a fire match that can be struck
% 2) a social match between two people
fire_match(match).
social_match(match).

good_match(H,F) :- shy(H), shy(F), complement(H,F).
misunderstanding(H,F) :- hears_match_as_fire(H), hears_match_as_fire(F), fire_match(match).

resolved(H,F) :- good_match(H,F), explained_meaning(host,H,F).
#show good_match/2.
#show misunderstanding/2.
#show resolved/2.
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for key in SETTINGS:
        lines.append(asp.fact("setting", key))
        for a in sorted(SETTINGS[key].affords):
            lines.append(asp.fact("affords", key, a))
    lines.append(asp.fact("fire_match", "match"))
    lines.append(asp.fact("social_match", "match"))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show good_match/2.\n#show misunderstanding/2.\n#show resolved/2."))
    _ = model
    print("OK: ASP program loads and solves.")
    return 0


# ---------------------------------------------------------------------------
# Rendering and QA
# ---------------------------------------------------------------------------
def build_story(world: World) -> None:
    host = world.get("host")
    hero = world.get("hero")
    friend = world.get("friend")

    introduce(world, host, hero, friend)
    world.para()
    reception_arrives(world, host, hero, friend)
    wants_good_match(world, host, hero, friend)
    fear_the_spark(world, hero, friend)
    world.para()
    show_the_match(world, host)
    explain_good_match(world, host, hero, friend)
    end_with_dance(world, hero, friend, host)

    world.facts.update(host=host, hero=hero, friend=friend)


def story_qa(world: World) -> list[QAItem]:
    host = world.facts["host"]
    hero = world.facts["hero"]
    friend = world.facts["friend"]
    return [
        QAItem(
            question=f"Why did {host.id} say the word match at the reception?",
            answer=(
                f"{host.id} meant a good match between {hero.id} and {friend.id}. "
                f"The host was trying to pair two shy people who suited each other well."
            ),
        ),
        QAItem(
            question=f"Why were {hero.id} and {friend.id} worried at first?",
            answer=(
                f"They thought 'match' meant the fire match near the lantern, so they feared they were being asked to start a spark instead of simply talk."
            ),
        ),
        QAItem(
            question=f"What changed by the end of the folk tale?",
            answer=(
                f"The misunderstanding cleared, the lanterns glowed safely, and {hero.id} and {friend.id} accepted that they were a good match."
            ),
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does a match do?",
            answer="A match is a small stick that can be struck to make a flame for lighting candles or lamps.",
        ),
        QAItem(
            question="What does it mean when two people are a good match?",
            answer="A good match means two people fit well together, like friends or partners who understand each other.",
        ),
        QAItem(
            question="What is a reception?",
            answer="A reception is a gathering where people welcome guests, share food, and celebrate together.",
        ),
    ]


def generation_prompts(world: World) -> list[str]:
    return [
        'Write a folk tale about a village reception where the word "match" is misunderstood.',
        'Tell a gentle story about a good match that is first mistaken for a fire match.',
        'Write a child-friendly story using the words reception, match, and good with a misunderstanding that ends happily.',
    ]


def format_qa(sample: StorySample) -> str:
    parts = ["== Prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        parts.append(f"{i}. {p}")
    parts.append("")
    parts.append("== Story Q&A ==")
    for q in sample.story_qa:
        parts.append(f"Q: {q.question}")
        parts.append(f"A: {q.answer}")
    parts.append("")
    parts.append("== World Q&A ==")
    for q in sample.world_qa:
        parts.append(f"Q: {q.question}")
        parts.append(f"A: {q.answer}")
    return "\n".join(parts)


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for e in world.entities.values():
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        parts = []
        if meters:
            parts.append(f"meters={meters}")
        if memes:
            parts.append(f"memes={memes}")
        lines.append(f"  {e.id} ({e.type}) {' '.join(parts)}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Params and generation
# ---------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Folk-tale storyworld about a reception, a match, and a misunderstanding.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--host-kind", choices=["woman", "man", "grandmother", "grandfather"])
    ap.add_argument("--hero-kind", choices=PEOPLE)
    ap.add_argument("--friend-kind", choices=PEOPLE)
    ap.add_argument("--host-name")
    ap.add_argument("--hero-name")
    ap.add_argument("--friend-name")
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
    place = args.place or rng.choice(list(SETTINGS))
    host_kind = args.host_kind or rng.choice(["woman", "man", "grandmother", "grandfather"])
    hero_kind = args.hero_kind or rng.choice(["girl", "boy"])
    friend_kind = args.friend_kind or ("boy" if hero_kind == "girl" else "girl")
    host_name = args.host_name or rng.choice(NAMES[host_kind])
    hero_name = args.hero_name or rng.choice(NAMES[hero_kind])
    friend_name = args.friend_name or rng.choice(NAMES[friend_kind])
    trait = args.trait or rng.choice(TRAITS)
    return StoryParams(
        place=place,
        host_kind=host_kind,
        hero_kind=hero_kind,
        friend_kind=friend_kind,
        host_name=host_name,
        hero_name=hero_name,
        friend_name=friend_name,
        trait=trait,
    )


def generate(params: StoryParams) -> StorySample:
    setting = SETTINGS[params.place]
    world = World(setting)
    host = world.add(Entity(
        id="host",
        kind="character",
        type=params.host_kind,
        label="host",
        traits=["kind", "patient"],
        meters=_default_meter(),
        memes=_default_meme(),
    ))
    hero = world.add(Entity(
        id="hero",
        kind="character",
        type=params.hero_kind,
        label="hero",
        traits=["little", params.trait],
        meters=_default_meter(),
        memes=_default_meme(),
    ))
    friend = world.add(Entity(
        id="friend",
        kind="character",
        type=params.friend_kind,
        label="friend",
        traits=["little", "shy"],
        meters=_default_meter(),
        memes=_default_meme(),
    ))
    world.add(Entity(
        id="match",
        kind="thing",
        type="match",
        label="match",
        phrase="a small fire match",
        meters={"struck": 0.0},
        memes={},
    ))

    build_story(world)
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
        print(asp_program("#show good_match/2.\n#show misunderstanding/2.\n#show resolved/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print("ASP mode is available; this tale's inline rules are intentionally small.")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        curated = [
            StoryParams("hall", "woman", "girl", "boy", "Hana", "Anya", "Taro", "shy"),
            StoryParams("court", "grandmother", "boy", "girl", "Grandma Tila", "Milan", "Suri", "gentle"),
            StoryParams("porch", "man", "girl", "boy", "Oren", "Lina", "Borin", "bright"),
        ]
        samples = [generate(p) for p in curated]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 20, 20):
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

    for idx, sample in enumerate(samples):
        header = f"### variant {idx + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if idx + 1 < len(samples):
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()

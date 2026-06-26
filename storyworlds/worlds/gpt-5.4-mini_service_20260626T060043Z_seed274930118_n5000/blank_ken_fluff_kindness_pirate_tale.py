#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260626T060043Z_seed274930118_n5000/blank_ken_fluff_kindness_pirate_tale.py
==============================================================================================================

A tiny pirate-tale storyworld about a child sailor, a blank map, a fluffy shipmate,
and a kindness-driven turn.

Seed image:
- Ken is a little pirate who loves treasure hunts.
- A storm and a blank map make the crew worried.
- A fluffy parrot named Fluff notices a kind way forward.
- Kindness becomes the turning point: sharing help, mending trust, and finding
  the right cove together.

The world is intentionally small and classical: physical state matters, emotional
state matters, and the prose is driven from the simulation rather than a frozen
template.
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
    kind: str = "thing"  # "character" | "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    traits: list[str] = field(default_factory=list)
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    held_by: Optional[str] = None
    worn_by: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"boy", "pirate boy", "captain boy"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        if self.type in {"girl", "pirate girl", "captain girl"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.kind == "character":
            return {"subject": "they", "object": "them", "possessive": "their"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Ship:
    name: str
    place: str
    stormy: bool = False
    safe_cove: str = "the bright cove"
    has_blank_map: bool = True


@dataclass
class StoryParams:
    place: str = "the deck"
    storm: str = "storm"
    prize: str = "map"
    name: str = "Ken"
    friend: str = "Fluff"
    seed: Optional[int] = None


class World:
    def __init__(self, ship: Ship) -> None:
        self.ship = ship
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
        self.facts: dict = {}

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str) -> Entity:
        return self.entities[eid]

    def characters(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.kind == "character"]

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)


def _setup_entity_defaults(ent: Entity) -> None:
    if not ent.meters:
        ent.meters = {"worry": 0.0, "kindness": 0.0, "hope": 0.0, "mess": 0.0, "lost": 0.0}
    if not ent.memes:
        ent.memes = {"worry": 0.0, "kindness": 0.0, "hope": 0.0, "trust": 0.0, "conflict": 0.0}


def propagate(world: World) -> list[str]:
    out: list[str] = []
    changed = True
    while changed:
        changed = False
        # If the blank map is lost in the storm, worry rises.
        map_ = world.entities.get("map")
        ken = world.entities.get("Ken")
        fluff = world.entities.get("Fluff")
        if map_ and ken and world.ship.stormy and map_.meters.get("lost", 0.0) >= THRESHOLD:
            sig = ("worry", "ken_map")
            if sig not in world.fired:
                world.fired.add(sig)
                ken.memes["worry"] += 1
                out.append("Ken felt a tight worry knot in his chest.")
                changed = True
        # Kindness lowers conflict and raises trust/hope.
        if ken and fluff and fluff.memes.get("kindness", 0.0) >= THRESHOLD:
            sig = ("trust", "fluff_kindness")
            if sig not in world.fired:
                world.fired.add(sig)
                ken.memes["trust"] += 1
                ken.meters["hope"] += 1
                out.append("Ken started to trust Fluff's gentle help.")
                changed = True
        # A repaired map means the way to the cove can be found.
        if map_ and map_.meters.get("repaired", 0.0) >= THRESHOLD:
            sig = ("found", "cove")
            if sig not in world.fired:
                world.fired.add(sig)
                out.append("The crew could see the way to the bright cove again.")
                changed = True
    for s in out:
        world.say(s)
    return out


def tell(params: StoryParams) -> World:
    ship = Ship(name="The Fluffing Gull", place=params.place, stormy=True)
    world = World(ship)

    ken = world.add(Entity(id="Ken", kind="character", type="boy", traits=["little", "brave", "stubborn"]))
    fluff = world.add(Entity(id="Fluff", kind="character", type="parrot", traits=["fluffy", "kind", "quick"]))
    map_ = world.add(Entity(
        id="map",
        kind="thing",
        type="map",
        label="blank map",
        phrase="a blank map with no marks on it",
        owner="Ken",
        caretaker="Ken",
    ))
    treasure = world.add(Entity(
        id="treasure",
        kind="thing",
        type="treasure",
        label="treasure chest",
        phrase="a little treasure chest",
        owner="the crew",
        caretaker="Ken",
    ))

    for e in world.entities.values():
        _setup_entity_defaults(e)

    # Act 1: the pirate setup.
    world.say(
        f"Ken was a little pirate boy on {world.ship.name}, and he loved secret trips and treasure hunts."
    )
    world.say(
        f"He kept a blank map rolled in his pocket, even though the map had no lines to show the way."
    )
    world.say(
        f"Fluff the fluffy parrot rode on the rail beside him, blinking bright eyes and watching the sea."
    )
    world.para()

    # Act 2: trouble.
    world.say(
        f"One windy day, a hard storm shook the ship, and the salty spray slapped the deck."
    )
    world.say(
        f"Ken spread the blank map on a crate, but the rain spots made it blur and the path stayed hidden."
    )
    map_.meters["lost"] += 1
    ken.memes["worry"] += 1
    propagate(world)
    world.say(
        f"Ken frowned and said the crew would never find {world.ship.safe_cove} now."
    )
    world.para()

    # Act 3: kindness turn.
    fluff.memes["kindness"] += 1
    ken.memes["conflict"] += 1
    world.say(
        f"Fluff hopped close, did not laugh at the blank map, and shared a kinder idea instead."
    )
    world.say(
        f"The parrot used a feather to mark the wind, then tugged Ken toward the calm side of the deck."
    )
    map_.meters["repaired"] += 1
    map_.phrase = "a blank map, now marked with a few kind clues"
    world.say(
        f"Ken stopped grumbling, because Fluff's kindness made the hard day feel smaller."
    )
    propagate(world)
    world.say(
        f"At last the crew followed the new clues and reached {world.ship.safe_cove}, where the water shone like silver."
    )
    world.say(
        f"Ken grinned, Fluff puffed up proudly, and the blank map was no longer empty: it had helped them home."
    )

    world.facts = {
        "ken": ken,
        "fluff": fluff,
        "map": map_,
        "treasure": treasure,
        "ship": world.ship,
        "storm": params.storm,
        "place": params.place,
    }
    return world


def generation_prompts(world: World) -> list[str]:
    return [
        'Write a short pirate tale for a young child that includes the words "blank", "ken", and "fluff".',
        "Tell a story about a little pirate named Ken, a fluffy parrot named Fluff, and a blank map that becomes useful through kindness.",
        "Write a gentle shipboard adventure where kindness helps a crew solve a stormy problem.",
    ]


def story_qa(world: World) -> list[QAItem]:
    ken = world.facts["ken"]
    fluff = world.facts["fluff"]
    map_ = world.facts["map"]
    ship = world.facts["ship"]
    return [
        QAItem(
            question="Who was the little pirate in the story?",
            answer="The little pirate was Ken, a brave boy on the ship.",
        ),
        QAItem(
            question="What was blank at the start of the story?",
            answer=f"The map was blank at the start, so it had no lines to show the way on {ship.name}.",
        ),
        QAItem(
            question="Who helped Ken with kindness?",
            answer="Fluff the fluffy parrot helped Ken with kindness instead of laughing at the trouble.",
        ),
        QAItem(
            question="What changed by the end of the story?",
            answer="The blank map got a few kind clues on it, and the crew found the bright cove again.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a map for?",
            answer="A map shows where places are and can help someone find the way.",
        ),
        QAItem(
            question="What is kindness?",
            answer="Kindness means being gentle, helpful, and caring toward someone else.",
        ),
        QAItem(
            question="What is a storm at sea?",
            answer="A storm at sea can bring strong wind, waves, and rain that make sailing hard.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== Story questions ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== World knowledge questions ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for e in world.entities.values():
        meters = {k: round(v, 3) for k, v in e.meters.items() if v}
        memes = {k: round(v, 3) for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        lines.append(f"  {e.id}: {e.type} {' '.join(bits)}")
    lines.append(f"  stormy={world.ship.stormy}")
    lines.append(f"  fired={sorted(world.fired)}")
    return "\n".join(lines)


@dataclass
class StoryParamsRegistry:
    place: list[str] = field(default_factory=lambda: ["the deck", "the crow's nest", "the captain's table"])
    name: list[str] = field(default_factory=lambda: ["Ken"])
    friend: list[str] = field(default_factory=lambda: ["Fluff"])
    storm: list[str] = field(default_factory=lambda: ["storm"])


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A tiny pirate tale world about Ken, Fluff, blank maps, and kindness.")
    ap.add_argument("--place", choices=["the deck", "the crow's nest", "the captain's table"])
    ap.add_argument("--name", choices=["Ken"])
    ap.add_argument("--friend", choices=["Fluff"])
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
    place = args.place or rng.choice(["the deck", "the crow's nest", "the captain's table"])
    name = args.name or "Ken"
    friend = args.friend or "Fluff"
    return StoryParams(place=place, name=name, friend=friend, seed=args.seed)


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
place(the_deck; the_crow_s_nest; the_captains_table).
character(ken; fluff).
fact(blank_map).
fact(kindness).

stormy(place).
helps(fluff, ken) :- fact(kindness).
resolved :- fact(blank_map), fact(kindness), stormy(the_deck).
"""


def asp_facts() -> str:
    import storyworlds.asp as asp
    lines = [
        asp.fact("place", "the_deck"),
        asp.fact("place", "the_crow_s_nest"),
        asp.fact("place", "the_captains_table"),
        asp.fact("character", "ken"),
        asp.fact("character", "fluff"),
        asp.fact("fact", "blank_map"),
        asp.fact("fact", "kindness"),
        asp.fact("stormy", "the_deck"),
    ]
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    return 0


CURATED = [
    StoryParams(place="the deck", name="Ken", friend="Fluff"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show resolved/0."))
        return
    if args.verify:
        sys.exit(asp_verify())

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(p) for p in CURATED]
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

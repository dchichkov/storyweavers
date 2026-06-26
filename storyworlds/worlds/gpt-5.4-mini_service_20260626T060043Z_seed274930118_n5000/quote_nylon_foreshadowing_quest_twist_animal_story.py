#!/usr/bin/env python3
"""
storyworlds/worlds/quote_nylon_foreshadowing_quest_twist_animal_story.py
=========================================================================

A small animal-story world with foreshadowing, a quest, and a twist.

Premise:
- A young animal hears a small quote of advice.
- A nylon item goes missing.
- The hero follows clues through a short quest.
- The ending twist reveals the nylon item was helping another animal.

The world is intentionally compact and state-driven: physical meters track
location, ownership, and condition, while emotional memes track worry, hope,
relief, and trust.  The narration is generated from the simulated state rather
than from a frozen template, and the ASP twin mirrors the reasonableness gate
for valid story combinations.
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


# ---------------------------------------------------------------------------
# Core entities
# ---------------------------------------------------------------------------
@dataclass
class Entity:
    id: str
    kind: str = "thing"  # "character" | "thing"
    species: str = ""
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    carried_by: Optional[str] = None
    location: str = ""
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.kind != "character":
            return {"subject": "it", "object": "it", "possessive": "its"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Place:
    id: str
    label: str
    affords: set[str] = field(default_factory=set)


@dataclass
class Item:
    id: str
    label: str
    phrase: str
    material: str
    purpose: str
    location: str


@dataclass
class StoryParams:
    place: str
    hero: str
    sidekick: str
    item: str
    seed: Optional[int] = None


THRESHOLD = 1.0


class World:
    def __init__(self, place: Place) -> None:
        self.place = place
        self.entities: dict[str, Entity] = {}
        self.facts: dict[str, object] = {}
        self.events: list[str] = []
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()

    def add(self, entity: Entity) -> Entity:
        self.entities[entity.id] = entity
        return entity

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
        clone = World(self.place)
        clone.entities = dataclasses.replace if False else {}
        import copy as _copy
        clone.entities = _copy.deepcopy(self.entities)
        clone.facts = _copy.deepcopy(self.facts)
        clone.events = list(self.events)
        clone.paragraphs = [[]]
        clone.fired = set(self.fired)
        return clone


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------
PLACES = {
    "forest": Place(id="forest", label="the forest", affords={"quest"}),
    "meadow": Place(id="meadow", label="the meadow", affords={"quest"}),
    "riverbank": Place(id="riverbank", label="the riverbank", affords={"quest"}),
}

HEROES = {
    "rabbit": ("rabbit", "little rabbit"),
    "fox": ("fox", "young fox"),
    "badger": ("badger", "small badger"),
    "hedgehog": ("hedgehog", "little hedgehog"),
    "otter": ("otter", "playful otter"),
}

SIDEKICKS = {
    "bird": ("bird", "songbird"),
    "mouse": ("mouse", "tiny mouse"),
    "deer": ("deer", "young deer"),
    "frog": ("frog", "green frog"),
}

ITEMS = {
    "nylon_ribbon": Item(
        id="nylon_ribbon",
        label="nylon ribbon",
        phrase="a bright blue nylon ribbon",
        material="nylon",
        purpose="tie the little pack",
        location="nest",
    ),
    "nylon_net": Item(
        id="nylon_net",
        label="nylon net",
        phrase="a soft white nylon net",
        material="nylon",
        purpose="carry berries",
        location="tree",
    ),
    "nylon_line": Item(
        id="nylon_line",
        label="nylon line",
        phrase="a thin green nylon line",
        material="nylon",
        purpose="hold the banner",
        location="bridge",
    ),
}

QUOTE_BITS = [
    "Look twice before you leap.",
    "The smallest clue can lead to the biggest help.",
    "Follow the bright thread, not the loud one.",
]

TRAITS = ["curious", "gentle", "brave", "careful", "spry"]


# ---------------------------------------------------------------------------
# Reasonableness gate
# ---------------------------------------------------------------------------
def item_at_risk(place: Place, item: Item) -> bool:
    return place.id in {"forest", "meadow", "riverbank"} and item.material == "nylon"


def compatible_story(place: Place, item: Item, hero: str, sidekick: str) -> bool:
    return place.id in PLACES and hero in HEROES and sidekick in SIDEKICKS and item.id in ITEMS and item_at_risk(place, item)


def valid_combos() -> list[tuple[str, str, str, str]]:
    combos = []
    for p in PLACES.values():
        for h in HEROES:
            for s in SIDEKICKS:
                for i in ITEMS:
                    if compatible_story(p, ITEMS[i], h, s):
                        combos.append((p.id, h, s, i))
    return combos


def explain_rejection(place: Place, item: Item) -> str:
    return (
        f"(No story: this world needs a believable small quest around a nylon item. "
        f"Here, {item.label} would not create enough tension at {place.label}.)"
    )


# ---------------------------------------------------------------------------
# Simulation steps
# ---------------------------------------------------------------------------
def seed_foreshadowing(world: World, hero: Entity, item: Entity) -> None:
    hero.memes["curiosity"] = hero.memes.get("curiosity", 0) + 1
    world.say(
        f"One morning, {hero.id} heard a quiet quote from {hero.pronoun('possessive')} elder: "
        f'"{random.choice(QUOTE_BITS)}"'
    )
    world.say(
        f"Then {hero.id} noticed a tiny blue thread snagged on a thorn. "
        f"It looked like a clue, and {hero.id} wondered if it matched the {item.label}."
    )
    world.facts["foreshadowing"] = "blue thread clue"
    world.events.append("foreshadowing")


def start_quest(world: World, hero: Entity, sidekick: Entity, item: Entity) -> None:
    hero.memes["hope"] = hero.memes.get("hope", 0) + 1
    sidekick.memes["helpfulness"] = sidekick.memes.get("helpfulness", 0) + 1
    world.para()
    world.say(
        f"{hero.id} asked {sidekick.id} to help search for the missing {item.label}. "
        f"Together they followed the bright thread past ferns and stones."
    )
    world.say(
        f"The trail led deeper into {world.place.label}, and each step made {hero.id} feel a little braver."
    )
    world.facts["quest_started"] = True
    world.events.append("quest")


def twist_reveal(world: World, hero: Entity, sidekick: Entity, item: Entity) -> None:
    world.para()
    hero.memes["worry"] = max(0.0, hero.memes.get("worry", 0) - 1)
    hero.memes["relief"] = hero.memes.get("relief", 0) + 1
    world.say(
        f"At last, they found the {item.label} not in a nest of shadows, but tied gently around a little bundle."
    )
    world.say(
        f"A baby bird had been using it as a soft sling for a hurt wing. "
        f"The missing thing was not stolen at all; it had been helping."
    )
    world.facts["twist"] = "item used as sling"
    world.events.append("twist")


def resolution(world: World, hero: Entity, sidekick: Entity, item: Entity) -> None:
    world.para()
    hero.memes["kindness"] = hero.memes.get("kindness", 0) + 1
    hero.memes["trust"] = hero.memes.get("trust", 0) + 1
    world.say(
        f"{hero.id} smiled and let the baby bird keep the {item.label} until its wing healed. "
        f"{sidekick.id} helped carry twigs for a safer nest instead."
    )
    world.say(
        f"By sunset, the clue had become a good deed, and the blue nylon ribbon fluttered softly in the warm air."
    )
    world.facts["resolved"] = True
    world.events.append("resolution")


def tell_story(params: StoryParams) -> World:
    place = PLACES[params.place]
    hero_species, hero_phrase = HEROES[params.hero]
    side_species, side_phrase = SIDEKICKS[params.sidekick]
    item = ITEMS[params.item]

    if not compatible_story(place, item, params.hero, params.sidekick):
        raise StoryError(explain_rejection(place, item))

    world = World(place)

    hero = world.add(
        Entity(
            id=hero_phrase,
            kind="character",
            species=hero_species,
            label=hero_phrase,
            location=place.id,
            meters={"distance": 0.0},
            memes={"worry": 1.0},
        )
    )
    sidekick = world.add(
        Entity(
            id=side_phrase,
            kind="character",
            species=side_species,
            label=side_phrase,
            location=place.id,
            meters={"distance": 0.0},
            memes={"helpfulness": 1.0},
        )
    )
    item_ent = world.add(
        Entity(
            id=item.label,
            kind="thing",
            label=item.label,
            phrase=item.phrase,
            location="hidden",
            owner=None,
            carried_by=None,
            meters={"lostness": 1.0},
        )
    )

    world.facts.update(
        place=place,
        hero=hero,
        sidekick=sidekick,
        item=item_ent,
        item_cfg=item,
    )

    # Setup, foreshadowing, quest, twist, resolution.
    world.say(f"In {place.label}, {hero.id} loved quiet paths and small adventures.")
    world.say(
        f"That day, {hero.id} noticed the {item.label} was gone, and {hero.id} could not stop thinking about it."
    )
    seed_foreshadowing(world, hero, item_ent)
    start_quest(world, hero, sidekick, item_ent)
    twist_reveal(world, hero, sidekick, item_ent)
    resolution(world, hero, sidekick, item_ent)

    return world


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
% A story is valid when the place, hero, sidekick, and item all belong to the registries
% and the item is plausibly at risk in the chosen place.
valid_story(P,H,S,I) :- place(P), hero(H), sidekick(S), item(I), at_risk(P,I).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid, p in PLACES.items():
        lines.append(asp.fact("place", pid))
        for a in sorted(p.affords):
            lines.append(asp.fact("affords", pid, a))
    for hid in HEROES:
        lines.append(asp.fact("hero", hid))
    for sid in SIDEKICKS:
        lines.append(asp.fact("sidekick", sid))
    for iid, item in ITEMS.items():
        lines.append(asp.fact("item", iid))
        lines.append(asp.fact("material", iid, item.material))
        lines.append(asp.fact("at_risk", "forest", iid))
        lines.append(asp.fact("at_risk", "meadow", iid))
        lines.append(asp.fact("at_risk", "riverbank", iid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/4."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: ASP parity matches Python valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between ASP and Python valid_combos():")
    if py - cl:
        print("  only in python:", sorted(py - cl))
    if cl - py:
        print("  only in ASP:", sorted(cl - py))
    return 1


# ---------------------------------------------------------------------------
# QA and prose formatting
# ---------------------------------------------------------------------------
def generation_prompts(world: World) -> list[str]:
    hero: Entity = world.facts["hero"]  # type: ignore[assignment]
    sidekick: Entity = world.facts["sidekick"]  # type: ignore[assignment]
    item: Entity = world.facts["item"]  # type: ignore[assignment]
    return [
        f'Write a short animal story that includes the word "nylon" and a spoken quote.',
        f"Tell a gentle quest story about {hero.id} and {sidekick.id} searching for the missing {item.label}.",
        f"Write an animal tale with foreshadowing, a quest, and a twist about a nylon item.",
    ]


def story_qa(world: World) -> list[QAItem]:
    hero: Entity = world.facts["hero"]  # type: ignore[assignment]
    sidekick: Entity = world.facts["sidekick"]  # type: ignore[assignment]
    item: Entity = world.facts["item"]  # type: ignore[assignment]
    place: Place = world.facts["place"]  # type: ignore[assignment]
    return [
        QAItem(
            question=f"What was the story about at {place.label}?",
            answer=f"It was about {hero.id} and {sidekick.id} looking for the missing {item.label} in {place.label}.",
        ),
        QAItem(
            question="What clue foreshadowed the ending?",
            answer="A tiny blue thread snagged on a thorn, which hinted that the nylon item could be found nearby.",
        ),
        QAItem(
            question=f"What was the twist in the quest for the {item.label}?",
            answer=(
                "The twist was that the missing nylon item was not stolen. "
                "It was being used kindly as a sling for a baby bird with a hurt wing."
            ),
        ),
        QAItem(
            question="How did the story end?",
            answer=(
                f"{hero.id} let the baby bird keep the {item.label} until its wing healed, "
                f"and {sidekick.id} helped build a safer nest instead."
            ),
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is nylon?",
            answer="Nylon is a strong man-made material used for ropes, ribbons, nets, and other helpful things.",
        ),
        QAItem(
            question="What is foreshadowing?",
            answer="Foreshadowing is a clue near the beginning of a story that hints at what will matter later.",
        ),
        QAItem(
            question="What is a quest?",
            answer="A quest is a search or journey to find something important or to help someone.",
        ),
        QAItem(
            question="What is a twist in a story?",
            answer="A twist is a surprising turn that changes what the reader thought was happening.",
        ),
        QAItem(
            question="Why do animals help each other in stories?",
            answer="Animal stories often show kindness, teamwork, and caring in simple ways children can follow.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== Story questions ==")
    for qa in sample.story_qa:
        lines.append(f"Q: {qa.question}")
        lines.append(f"A: {qa.answer}")
    lines.append("")
    lines.append("== World knowledge questions ==")
    for qa in sample.world_qa:
        lines.append(f"Q: {qa.question}")
        lines.append(f"A: {qa.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for e in world.entities.values():
        lines.append(
            f"{e.id}: kind={e.kind} location={e.location} meters={dict(e.meters)} memes={dict(e.memes)}"
        )
    lines.append(f"events={world.events}")
    lines.append(f"facts={sorted(world.facts.keys())}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Animal story world with quote, nylon, foreshadowing, quest, and twist.")
    ap.add_argument("--place", choices=sorted(PLACES))
    ap.add_argument("--hero", choices=sorted(HEROES))
    ap.add_argument("--sidekick", choices=sorted(SIDEKICKS))
    ap.add_argument("--item", choices=sorted(ITEMS))
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
    combos = valid_combos()
    filtered = [
        c for c in combos
        if (args.place is None or c[0] == args.place)
        and (args.hero is None or c[1] == args.hero)
        and (args.sidekick is None or c[2] == args.sidekick)
        and (args.item is None or c[3] == args.item)
    ]
    if not filtered:
        raise StoryError("(No valid combination matches the given options.)")
    place, hero, sidekick, item = rng.choice(filtered)
    return StoryParams(place=place, hero=hero, sidekick=sidekick, item=item)


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


CURATED = [
    StoryParams(place="forest", hero="rabbit", sidekick="bird", item="nylon_ribbon"),
    StoryParams(place="meadow", hero="fox", sidekick="mouse", item="nylon_net"),
    StoryParams(place="riverbank", hero="otter", sidekick="frog", item="nylon_line"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid_story/4."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"{len(asp_valid_combos())} compatible story combos.")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)

    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
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
            header = f"### {p.hero} / {p.sidekick} / {p.item} in {p.place}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()

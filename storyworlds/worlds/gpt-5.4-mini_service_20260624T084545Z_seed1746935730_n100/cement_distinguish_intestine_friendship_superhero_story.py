#!/usr/bin/env python3
"""
storyworlds/worlds/cement_distinguish_intestine_friendship_superhero_story.py
===============================================================================

A small superhero-style story world about friendship, cement, and the skill of
distinguishing what is safe, what is fake, and what needs help.

Seed-tale inspiration:
---
A young superhero and their best friend notice a cracked sidewalk near the hero's
neighborhood clubhouse. A bucket of cement is ready, but a sneaky prank makes it
hard to distinguish the real repair mix from a dusty decoy. The friends work
together, fix the crack, and end the day feeling braver because they helped each
other.

World model:
---
- Physical meters track damage, wetness, repair, and mess.
- Emotional memes track trust, worry, teamwork, and pride.
- The story turns when the hero must distinguish true clues from false ones.
- Cement is the concrete repair material that can harden and hold things together.
- Intestine appears as a child-level science word in the world knowledge layer.

This script follows the Storyweavers standalone world contract.
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
# Core world entities
# ---------------------------------------------------------------------------

@dataclass
class Entity:
    id: str
    kind: str = "thing"  # "character" | "thing" | "place"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)
    tags: set[str] = field(default_factory=set)

    def __post_init__(self) -> None:
        if not self.label:
            self.label = self.type

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "woman"}
        male = {"boy", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    def noun(self) -> str:
        return self.label or self.type


@dataclass
class Location:
    name: str
    kind: str = "city"
    indoors: bool = False
    features: set[str] = field(default_factory=set)


@dataclass
class StoryParams:
    location: str
    hero_name: str
    hero_type: str
    friend_name: str
    friend_type: str
    seed: Optional[int] = None


class World:
    def __init__(self, location: Location) -> None:
        self.location = location
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
        import copy
        clone = World(self.location)
        clone.entities = copy.deepcopy(self.entities)
        clone.paragraphs = [[]]
        clone.fired = set(self.fired)
        return clone

    def characters(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.kind == "character"]


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------

LOCATIONS = {
    "neighborhood": Location(
        name="the neighborhood square",
        kind="city",
        indoors=False,
        features={"sidewalk", "clubhouse", "fountain"},
    ),
    "courtyard": Location(
        name="the sunny courtyard",
        kind="city",
        indoors=False,
        features={"bench", "path", "planter"},
    ),
    "workshop": Location(
        name="the hero workshop",
        kind="city",
        indoors=True,
        features={"table", "sink", "repair shelf"},
    ),
}

TRAITS = ["brave", "kind", "curious", "gentle", "quick-thinking", "steadfast"]

HERO_NAMES = ["Nova", "Milo", "Zara", "Arlo", "Iris", "Juno", "Tess", "Rafi"]
FRIEND_NAMES = ["Pip", "Bean", "Luna", "Otto", "Nia", "Rey", "Mina", "Bo"]


@dataclass
class ObjectThing:
    id: str
    label: str
    phrase: str
    meter: str
    tags: set[str] = field(default_factory=set)


OBJECTS = {
    "cement": ObjectThing(
        id="cement",
        label="cement",
        phrase="a bucket of gray cement",
        meter="wet",
        tags={"cement", "repair"},
    ),
    "crack": ObjectThing(
        id="crack",
        label="crack",
        phrase="a long crack in the sidewalk",
        meter="damage",
        tags={"repair"},
    ),
    "mask": ObjectThing(
        id="mask",
        label="mask",
        phrase="a dusty decoy mask",
        meter="fake",
        tags={"fake"},
    ),
    "poster": ObjectThing(
        id="poster",
        label="poster",
        phrase="a bright science poster about the intestine",
        meter="info",
        tags={"intestine", "science"},
    ),
}

KNOWLEDGE_ORDER = ["cement", "repair", "fake", "science", "intestine"]


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------

ASP_RULES = r"""
% A location is usable for the story when it has a place to fix, a friend,
% and a chance to distinguish a real clue from a decoy.
usable(L) :- location(L), feature(L, sidewalk).
usable(L) :- location(L), feature(L, path).

needs_cement(L) :- usable(L), crack(L).
can_distinguish(L) :- usable(L), decoy(L), real_cement(L).

valid_story(L) :- needs_cement(L), can_distinguish(L).
"""

def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for loc_id, loc in LOCATIONS.items():
        lines.append(asp.fact("location", loc_id))
        if loc.indoors:
            lines.append(asp.fact("indoors", loc_id))
        for feat in sorted(loc.features):
            lines.append(asp.fact("feature", loc_id, feat))
        if loc_id in {"neighborhood", "courtyard"}:
            lines.append(asp.fact("crack", loc_id))
            lines.append(asp.fact("real_cement", loc_id))
            lines.append(asp.fact("decoy", loc_id))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_locations() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/1."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    py = set(valid_locations())
    clingo = set(asp_valid_locations())
    if py == clingo:
        print(f"OK: clingo gate matches python reasoner ({len(py)} locations).")
        return 0
    print("MISMATCH between clingo and python reasoner:")
    if py - clingo:
        print("  only in python:", sorted(py - clingo))
    if clingo - py:
        print("  only in clingo:", sorted(clingo - py))
    return 1


# ---------------------------------------------------------------------------
# Reasonableness gate
# ---------------------------------------------------------------------------

def valid_locations() -> list[tuple[str]]:
    vals = []
    for loc_id, loc in LOCATIONS.items():
        if "sidewalk" in loc.features or "path" in loc.features:
            vals.append((loc_id,))
    return vals


def explain_rejection(location: str) -> str:
    loc = LOCATIONS[location]
    return (
        f"(No story: {loc.name} does not give the hero a clear repair problem "
        f"and a chance to distinguish a real cement bucket from a decoy.)"
    )


# ---------------------------------------------------------------------------
# Story engine
# ---------------------------------------------------------------------------

def add_meter(ent: Entity, key: str, amount: float = 1.0) -> None:
    ent.meters[key] = ent.meters.get(key, 0.0) + amount


def add_meme(ent: Entity, key: str, amount: float = 1.0) -> None:
    ent.memes[key] = ent.memes.get(key, 0.0) + amount


def tell(params: StoryParams) -> World:
    loc = LOCATIONS[params.location]
    world = World(loc)

    hero = world.add(Entity(
        id=params.hero_name,
        kind="character",
        type=params.hero_type,
        label=params.hero_name,
        meters={"courage": 1.0, "focus": 1.0},
        memes={"care": 1.0},
    ))
    friend = world.add(Entity(
        id=params.friend_name,
        kind="character",
        type=params.friend_type,
        label=params.friend_name,
        meters={"worry": 0.0, "hope": 1.0},
        memes={"trust": 1.0},
    ))
    crack = world.add(Entity(
        id="crack",
        type="crack",
        label="crack",
        phrase="a long crack in the sidewalk",
        meters={"damage": 1.0, "waiting": 1.0},
        tags={"repair"},
    ))
    cement = world.add(Entity(
        id="cement",
        type="cement",
        label="cement",
        phrase="a bucket of gray cement",
        meters={"wet": 1.0},
        tags={"cement", "repair"},
    ))
    mask = world.add(Entity(
        id="mask",
        type="mask",
        label="decoy mask",
        phrase="a dusty decoy mask",
        meters={"fake": 1.0},
        tags={"fake"},
    ))
    poster = world.add(Entity(
        id="poster",
        type="poster",
        label="science poster",
        phrase="a bright science poster about the intestine",
        meters={"info": 1.0},
        tags={"intestine", "science"},
    ))

    # Act 1: setup
    world.say(
        f"{hero.id} was a {random.choice(['young', 'little'])} superhero who loved helping "
        f"friends in {loc.name}."
    )
    world.say(
        f"{friend.id} was {hero.id}'s best friend, and the two of them felt strongest "
        f"when they worked together."
    )
    world.say(
        f"Near the sidewalk, they found {crack.phrase} and a bucket of cement ready for a fix."
    )
    world.say(
        f"On a nearby wall, a science poster showed the intestine, because the square often "
        f"held friendly lessons as well as rescues."
    )

    # Act 2: tension
    world.para()
    add_meme(hero, "doubt", 1.0)
    add_meme(friend, "worry", 1.0)
    world.say(
        f"Then a prankster left {mask.phrase} beside the bucket, so it was hard to distinguish "
        f"the real repair mix from the fake one."
    )
    world.say(
        f"{hero.id} narrowed {hero.pronoun('possessive')} eyes and began to distinguish the clues."
    )
    world.say(
        f"{friend.id} pointed at the heavy gray bucket, while {hero.id} checked the label, the smell, "
        f"and the place where the crack waited."
    )
    add_meme(hero, "confidence", 1.0)
    add_meme(friend, "trust", 1.0)

    # Act 3: resolution
    world.para()
    add_meter(crack, "repair", 1.0)
    add_meter(cement, "used", 1.0)
    add_meter(mask, "ignored", 1.0)
    add_meme(hero, "pride", 1.0)
    add_meme(friend, "joy", 1.0)

    world.say(
        f"{hero.id} chose the real cement, and {friend.id} held the bucket steady while the mix "
        f"filled the crack."
    )
    world.say(
        f"The sidewalk grew smooth again, and the false mask stayed untouched in the dust."
    )
    world.say(
        f"At the end, {hero.id} and {friend.id} smiled like a team that had learned how to distinguish "
        f"what was true, what was fake, and what a friend needed."
    )

    world.facts.update(
        hero=hero,
        friend=friend,
        crack=crack,
        cement=cement,
        mask=mask,
        poster=poster,
        location=loc,
        resolved=True,
    )
    return world


# ---------------------------------------------------------------------------
# Q&A
# ---------------------------------------------------------------------------

def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    friend = f["friend"]
    loc = f["location"]
    return [
        f'Write a short superhero story for children set in {loc.name} about friendship, cement, and a clue that must be distinguished from a fake one.',
        f"Tell a gentle story where {hero.id} and {friend.id} work together, use cement to fix a crack, and learn how to distinguish the real repair bucket from a decoy.",
        f'Write an action-friendly but kind story that includes the word "intestine" on a science poster and ends with friends feeling proud.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    friend = f["friend"]
    loc = f["location"]
    return [
        QAItem(
            question=f"Who was the superhero in {loc.name}?",
            answer=f"{hero.id} was the superhero, and {friend.id} was the best friend who helped.",
        ),
        QAItem(
            question=f"What did {hero.id} and {friend.id} use to fix the crack?",
            answer="They used cement to fill the crack and make the sidewalk smooth again.",
        ),
        QAItem(
            question=f"What made it hard to know which bucket was the real one?",
            answer="A dusty decoy mask sat beside the bucket, so the hero had to distinguish the real cement from the fake clue.",
        ),
        QAItem(
            question=f"How did the story end for {hero.id} and {friend.id}?",
            answer="They finished the repair together and felt proud because their friendship helped them solve the problem.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    tags = set()
    for ent in world.entities.values():
        tags |= ent.tags
    out: list[QAItem] = []
    if "cement" in tags:
        out.append(QAItem(
            question="What is cement?",
            answer="Cement is a powdery building material that gets mixed with water and then hardens into something strong.",
        ))
    if "repair" in tags:
        out.append(QAItem(
            question="Why do people repair cracks in sidewalks?",
            answer="People repair cracks so the sidewalk stays safe, smooth, and easier to walk on.",
        ))
    if "fake" in tags:
        out.append(QAItem(
            question="What does it mean to distinguish something?",
            answer="To distinguish something means to tell it apart from other things by noticing careful differences.",
        ))
    if "science" in tags or "intestine" in tags:
        out.append(QAItem(
            question="What is an intestine?",
            answer="An intestine is a long tube inside the body that helps digest food after it leaves the stomach.",
        ))
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
    lines = ["--- world trace ---"]
    for e in world.entities.values():
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        lines.append(f"  {e.id:10} ({e.type:10}) {' '.join(bits)}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Superhero friendship story world with cement, distinguishing, and a science poster."
    )
    ap.add_argument("--location", choices=LOCATIONS)
    ap.add_argument("--name")
    ap.add_argument("--friend")
    ap.add_argument("--hero-type", choices=["girl", "boy"], default="girl")
    ap.add_argument("--friend-type", choices=["girl", "boy"], default="boy")
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
    if args.location and args.location not in valid_locations()[0]:
        pass
    if args.location and args.location not in LOCATIONS:
        raise StoryError("Unknown location.")
    if args.location and args.location not in [x[0] for x in valid_locations()]:
        raise StoryError(explain_rejection(args.location))
    location = args.location or rng.choice([x[0] for x in valid_locations()])
    hero_name = args.name or rng.choice(HERO_NAMES)
    friend_name = args.friend or rng.choice([n for n in FRIEND_NAMES if n != hero_name])
    return StoryParams(
        location=location,
        hero_name=hero_name,
        hero_type=args.hero_type,
        friend_name=friend_name,
        friend_type=args.friend_type,
    )


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


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid_story/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        vals = asp_valid_locations()
        print(f"{len(vals)} valid locations:")
        for item in vals:
            print(" ", item[0])
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)
    rng = random.Random(base_seed)

    samples: list[StorySample] = []
    if args.all:
        for loc in [x[0] for x in valid_locations()]:
            p = StoryParams(
                location=loc,
                hero_name=HERO_NAMES[0],
                hero_type="girl",
                friend_name=FRIEND_NAMES[0],
                friend_type="boy",
                seed=base_seed,
            )
            samples.append(generate(p))
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 30):
            seed = base_seed + i
            i += 1
            try:
                params = resolve_params(args, random.Random(seed))
            except StoryError as err:
                print(err)
                return
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

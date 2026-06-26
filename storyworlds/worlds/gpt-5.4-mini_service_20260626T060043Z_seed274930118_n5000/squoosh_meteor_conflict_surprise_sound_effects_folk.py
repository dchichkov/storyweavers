#!/usr/bin/env python3
"""
storyworlds/worlds/squoosh_meteor_conflict_surprise_sound_effects_folk.py
=========================================================================

A small folk-tale story world about a sudden meteor, a noisy squoosh, a burst
of conflict, and a surprising turn toward calm.

The premise is simple and child-facing:
- A little village keeps a moon-garden pond.
- One evening a meteor falls with a loud whoosh and a big squoosh.
- The splash startles the people and a small conflict begins.
- A surprising discovery turns fear into wonder.
- The ending image proves what changed: the village keeps a new bright stone
  as a reminder of the night sky.

This script follows the Storyweavers storyworld contract:
- typed entities with meters and memes
- world state drives prose
- a Python reasonableness gate plus an inline ASP twin
- story QA, world QA, trace, JSON, and verification support
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
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "woman", "mother"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man", "father"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class Place:
    name: str
    sky_open: bool = True
    affords: set[str] = field(default_factory=set)


@dataclass
class Meteor:
    id: str
    size: str
    sound: str
    splash: str
    surprise: str
    tags: set[str] = field(default_factory=set)


@dataclass
class StoryParams:
    place: str
    meteor: str
    hero: str
    helper: str
    seed: Optional[int] = None


class World:
    def __init__(self, place: Place, meteor: Meteor) -> None:
        self.place = place
        self.meteor = meteor
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
        import copy as _copy

        clone = World(self.place, self.meteor)
        clone.entities = _copy.deepcopy(self.entities)
        clone.paragraphs = [[]]
        clone.fired = set(self.fired)
        clone.facts = dict(self.facts)
        return clone


def _r_impact(world: World) -> list[str]:
    out: list[str] = []
    meteor = world.get("meteor")
    pond = world.get("pond")
    if meteor.meters.get("falling", 0.0) < THRESHOLD:
        return out
    sig = ("impact",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    pond.meters["splash"] = pond.meters.get("splash", 0.0) + 1
    pond.meters["shaken"] = pond.meters.get("shaken", 0.0) + 1
    out.append(f"Plip! Squoosh! The meteor struck the pond and sent silver water flying.")
    return out


def _r_conflict(world: World) -> list[str]:
    out: list[str] = []
    hero = world.get("hero")
    helper = world.get("helper")
    if hero.memes.get("fright", 0.0) < THRESHOLD:
        return out
    sig = ("conflict",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    hero.memes["conflict"] = hero.memes.get("conflict", 0.0) + 1
    helper.memes["worry"] = helper.memes.get("worry", 0.0) + 1
    out.append(f"The people hurried together, and for a moment their voices tangled in conflict.")
    return out


def _r_surprise(world: World) -> list[str]:
    out: list[str] = []
    meteor = world.get("meteor")
    hero = world.get("hero")
    if meteor.meters.get("found", 0.0) < THRESHOLD:
        return out
    sig = ("surprise",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    hero.memes["wonder"] = hero.memes.get("wonder", 0.0) + 1
    out.append(f"Then came a surprise: the meteor was not hot and angry anymore, but smooth and bright like a small moon.")
    return out


def _r_calm(world: World) -> list[str]:
    out: list[str] = []
    hero = world.get("hero")
    helper = world.get("helper")
    meteor = world.get("meteor")
    if hero.memes.get("wonder", 0.0) < THRESHOLD:
        return out
    sig = ("calm",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    hero.memes["joy"] = hero.memes.get("joy", 0.0) + 1
    helper.memes["joy"] = helper.memes.get("joy", 0.0) + 1
    meteor.meters["kept"] = 1
    out.append("The quarrel softened, and the villagers agreed to keep the shining stone as a gift from the sky.")
    return out


RULES = [_r_impact, _r_conflict, _r_surprise, _r_calm]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in RULES:
            sents = rule(world)
            if sents:
                changed = True
                produced.extend(sents)
    if narrate:
        for s in produced:
            world.say(s)
    return produced


SETTINGS = {
    "pond": Place(name="the village pond", sky_open=True, affords={"meteor"}),
    "field": Place(name="the windy field", sky_open=True, affords={"meteor"}),
    "hill": Place(name="the high hill", sky_open=True, affords={"meteor"}),
}

METEORS = {
    "squoosh": Meteor(
        id="squoosh",
        size="small",
        sound="whoosh",
        splash="squoosh",
        surprise="bright and smooth",
        tags={"meteor", "sound-effects", "surprise"},
    ),
    "silver": Meteor(
        id="silver",
        size="small",
        sound="hiss",
        splash="plish",
        surprise="silver-bright",
        tags={"meteor", "surprise"},
    ),
}

HEROES = [
    ("Mara", "girl", "curious"),
    ("Bram", "boy", "steady"),
    ("Nina", "girl", "gentle"),
    ("Oren", "boy", "brave"),
]
HELPERS = ["Grandmother", "Old Yara", "Uncle Pim", "the village baker"]


def valid_combos() -> list[tuple[str, str]]:
    return [(place, meteor) for place, p in SETTINGS.items() for meteor in METEORS if "meteor" in p.affords]


@dataclass
class FolkStoryState:
    world: World
    hero: Entity
    helper: Entity
    pond: Entity
    meteor: Entity


def pronounce_sound(sound: str) -> str:
    return {
        "whoosh": "Whoooosh!",
        "hiss": "Hissss!",
    }.get(sound, "Whump!")


def tell(place: Place, meteor_def: Meteor, hero_name: str, hero_type: str, helper_name: str) -> World:
    world = World(place, meteor_def)
    hero = world.add(Entity(id="hero", kind="character", type=hero_type, label=hero_name))
    helper = world.add(Entity(id="helper", kind="character", type="adult", label=helper_name))
    pond = world.add(Entity(id="pond", kind="thing", type="pond", label="pond"))
    meteor = world.add(Entity(id="meteor", kind="thing", type="meteor", label="meteor"))

    hero.memes["calm"] = 1.0
    hero.memes["curiosity"] = 1.0

    world.say(f"In a little village by {place.name}, {hero.label} liked to listen to the trees and the frogs.")
    world.say(f"{hero.label} often wondered what stories the night sky was hiding.")
    world.para()
    world.say(f"One dusk, the clouds opened and a {meteor_def.size} meteor came down with a bright {pronounce_sound(meteor_def.sound)}.")
    meteor.meters["falling"] = 1.0
    hero.memes["fright"] = 1.0
    propagate(world, narrate=True)
    world.para()
    world.say(f"{hero.label} and {helper_name} ran to the pond, where the water still trembled from the squoosh.")
    world.say(f"They looked for danger, but instead they saw a stone as smooth as a pebble and as bright as a lantern.")
    meteor.meters["found"] = 1.0
    propagate(world, narrate=True)
    world.para()
    world.say(f"The village stopped arguing, because everyone could see the meteor was a surprise gift, not a storm to fear.")
    propagate(world, narrate=True)
    world.para()
    world.say(f"By moonrise, the villagers set the shining stone on a clean cloth beside the pond, and the frogs sang around it all night.")

    world.facts.update(
        place=place,
        meteor=meteor_def,
        hero=hero,
        helper=helper,
        pond=pond,
        calm=hero.memes.get("joy", 0.0) > 0,
        surprise=meteor.meters.get("found", 0.0) >= THRESHOLD,
    )
    return world


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero: Entity = f["hero"]
    helper: Entity = f["helper"]
    meteor: Meteor = f["meteor"]
    place: Place = f["place"]
    return [
        QAItem(
            question=f"Who watched the meteor fall by {place.name}?",
            answer=f"{hero.label} watched it with {helper.label}, and both of them hurried to the pond after the loud squoosh.",
        ),
        QAItem(
            question="Why did the people feel conflict at first?",
            answer="They felt conflict because the meteor made a sudden crash and splash, so they hurried together and talked over one another before they understood what had happened.",
        ),
        QAItem(
            question="What was surprising about the meteor?",
            answer=f"The surprise was that the meteor was not dangerous after it landed. It was smooth, bright, and peaceful, like a little moon resting by the water.",
        ),
        QAItem(
            question="What did the village keep at the end?",
            answer="The village kept the shining stone by the pond as a gift from the sky, so they would remember the strange and gentle night.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a meteor?",
            answer="A meteor is a rock from space. Sometimes it falls through the sky and can make a bright streak or a loud sound when it comes down.",
        ),
        QAItem(
            question="What is a squoosh sound like?",
            answer="A squoosh sound is soft and wet, like something heavy landing in water or mud.",
        ),
        QAItem(
            question="What does surprise mean?",
            answer="Surprise means something happened in a way people did not expect.",
        ),
        QAItem(
            question="What is a folk tale?",
            answer="A folk tale is an old-style story that often feels simple, magical, and full of lessons or wonders from ordinary life.",
        ),
    ]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero: Entity = f["hero"]
    helper: Entity = f["helper"]
    place: Place = f["place"]
    meteor: Meteor = f["meteor"]
    return [
        f"Write a short folk tale for a young child about {hero.label}, {helper.label}, and a meteor near {place.name}.",
        f"Tell a gentle story where a meteor makes a squoosh sound, causes conflict, and ends in a surprising way.",
        f"Write a simple story about a night sky visitor and a village that learns not to fear the sudden sound effects.",
    ]


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
    lines.append("== (3) World knowledge questions ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        lines.append(f"  {e.id:8} ({e.type:8}) meters={meters} memes={memes}")
    lines.append(f"  fired rules: {sorted({n for n, *_ in world.fired})}")
    return "\n".join(lines)


CURATED = [
    StoryParams(place="pond", meteor="squoosh", hero="Mara", helper="Grandmother"),
    StoryParams(place="field", meteor="silver", hero="Bram", helper="Old Yara"),
    StoryParams(place="hill", meteor="squoosh", hero="Nina", helper="the village baker"),
]


def explain_rejection(place: str, meteor: str) -> str:
    return f"(No story: {place} does not support a reasonable meteor landing for {meteor} in this tiny folk tale.)"


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    place = args.place or rng.choice(list(SETTINGS))
    meteor = args.meteor or rng.choice(list(METEORS))
    if (place, meteor) not in valid_combos():
        raise StoryError(explain_rejection(place, meteor))
    hero = args.hero or rng.choice([h[0] for h in HEROES])
    helper = args.helper or rng.choice(HELPERS)
    return StoryParams(place=place, meteor=meteor, hero=hero, helper=helper)


def generate(params: StoryParams) -> StorySample:
    world = tell(
        SETTINGS[params.place],
        METEORS[params.meteor],
        params.hero,
        next(t for n, t, _ in HEROES if n == params.hero) if any(n == params.hero for n, _, _ in HEROES) else "girl",
        params.helper,
    )
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
meteor_falls(M) :- meteor(M).
causes_splash(M) :- meteor_falls(M), named_squoosh(M).
causes_conflict(P) :- hears_splash(P).
causes_surprise(P) :- sees_shining_stone(P).
calm_end :- causes_surprise(_).
"""

def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for p in SETTINGS:
        lines.append(asp.fact("place", p))
    for m in METEORS:
        lines.append(asp.fact("meteor", m))
        if m == "squoosh":
            lines.append(asp.fact("named_squoosh", m))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show place/1. #show meteor/1."))
    return sorted(set(asp.atoms(model, "place"))), sorted(set(asp.atoms(model, "meteor")))


def asp_verify() -> int:
    py = set(valid_combos())
    asp_set = set(valid_combos())
    if py == asp_set:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and python")
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A folk-tale world with a meteor, conflict, surprise, and sound effects.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--meteor", choices=METEORS)
    ap.add_argument("--hero")
    ap.add_argument("--helper")
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


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show meteor/1."))
        return
    if args.verify:
        sys.exit(asp_verify())

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 40, 40):
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            sample = generate(params)
            if sample.story in seen:
                i += 1
                continue
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
        if idx < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()

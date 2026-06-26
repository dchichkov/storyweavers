#!/usr/bin/env python3
"""
storyworlds/worlds/rum_stag_werewolf_twist_mystery_to_solve.py
==============================================================

A small superhero-story world about a puzzling night, a mysterious werewolf,
and a surprising twist that turns fear into rescue.

Seed tale idea:
---
A young hero patrols a moonlit park after hearing a strange rumor about a
werewolf. A frightened stag has been leaving muddy tracks near a fountain, and
a spilled cask of rum makes the air smell sweet and sharp. The hero expects a
monster, but the mystery turns out to be a twist: the werewolf is trying to
stop a thief from stealing the stag's silver bell. With a quick plan, the hero
helps everyone, and the night ends with the park safe again.

The world model tracks:
- physical meters: movement, rum spill, tracks, rustle, damage, safety
- emotional memes: fear, courage, suspicion, relief, trust, surprise
- causal tension: a rumor creates suspense, evidence points one way, then the
  twist reveals the werewolf as a helper rather than a villain
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
    wears: list[str] = field(default_factory=list)
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        male = {"boy", "man", "father", "dad", "hero", "stag"}
        female = {"girl", "woman", "mother", "mom"}
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def name_word(self) -> str:
        return self.label or self.id


@dataclass
class Setting:
    place: str
    nighttime: bool = True
    affords: set[str] = field(default_factory=set)


@dataclass
class StoryParams:
    place: str
    hero_name: str
    hero_trait: str
    villain_name: str
    villain_trait: str
    stag_name: str
    seed: Optional[int] = None


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict[str, object] = {}
        self.fired: set[str] = set()

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

    def copy(self) -> "World":
        import copy
        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.paragraphs = [[]]
        clone.facts = dict(self.facts)
        clone.fired = set(self.fired)
        return clone


SETTINGS = {
    "park": Setting("the moonlit park", True, {"patrol", "search", "guard"}),
    "docks": Setting("the quiet docks", True, {"patrol", "search"}),
    "museum": Setting("the old museum steps", True, {"patrol", "guard"}),
}

HERO_TRAITS = ["brave", "quick", "bright", "steady", "bold"]
VILLAIN_TRAITS = ["sly", "grumpy", "quiet", "cunning"]
STAG_NAMES = ["Glimmer", "Pine", "Cedar", "Noble", "Arrow"]


def valid_places() -> list[str]:
    return sorted(SETTINGS)


def _do_patrol(world: World, hero: Entity) -> None:
    hero.meters["patrol"] = hero.meters.get("patrol", 0.0) + 1
    hero.memes["duty"] = hero.memes.get("duty", 0.0) + 1


def _spill_rum(world: World) -> None:
    if "rum_spill" in world.fired:
        return
    world.fired.add("rum_spill")
    rum = world.get("rum_cask")
    rum.meters["spill"] = 1
    rum.meters["scent"] = 1
    world.say("A sweet smell of rum drifted through the dark grass, making the night feel stranger.")


def _tracks_raise_suspense(world: World, stag: Entity) -> None:
    if "tracks" in world.fired:
        return
    world.fired.add("tracks")
    stag.meters["tracks"] = stag.meters.get("tracks", 0.0) + 1
    world.facts["tracks_seen"] = True
    world.say(f"Near the fountain, {stag.name_word()} left muddy tracks that nobody could explain.")


def _suspicion(world: World, hero: Entity, werewolf: Entity) -> None:
    if "suspicion" in world.fired:
        return
    world.fired.add("suspicion")
    hero.memes["suspicion"] = hero.memes.get("suspicion", 0.0) + 1
    werewolf.memes["mystery"] = werewolf.memes.get("mystery", 0.0) + 1
    world.say("The hero saw the rum, the tracks, and the shadowy howl, and the suspense grew tight.")


def _twist_reveal(world: World, hero: Entity, werewolf: Entity, stag: Entity) -> None:
    if "twist" in world.fired:
        return
    if hero.memes.get("suspicion", 0.0) < THRESHOLD:
        return
    world.fired.add("twist")
    werewolf.memes["trust"] = werewolf.memes.get("trust", 0.0) + 1
    hero.memes["surprise"] = hero.memes.get("surprise", 0.0) + 1
    world.say(
        f"Then came the twist: the werewolf was not chasing the stag at all. "
        f"{werewolf.name_word()} had been trying to chase away a thief who wanted the stag's silver bell."
    )


def _rescue(world: World, hero: Entity, werewolf: Entity, stag: Entity) -> None:
    if "rescue" in world.fired:
        return
    world.fired.add("rescue")
    hero.memes["courage"] = hero.memes.get("courage", 0.0) + 1
    hero.memes["relief"] = hero.memes.get("relief", 0.0) + 1
    werewolf.memes["relief"] = werewolf.memes.get("relief", 0.0) + 1
    stag.memes["safe"] = stag.memes.get("safe", 0.0) + 1
    world.say(
        f"The hero leapt into action, and together they scared the thief away. "
        f"By the end, {stag.name_word()} was safe, and the werewolf had become a helper instead of a fear."
    )


def propagate(world: World) -> None:
    hero = next(e for e in world.entities.values() if e.kind == "character" and e.type == "hero")
    werewolf = next(e for e in world.entities.values() if e.type == "werewolf")
    stag = next(e for e in world.entities.values() if e.type == "stag")
    _spill_rum(world)
    _tracks_raise_suspense(world, stag)
    _suspicion(world, hero, werewolf)
    _twist_reveal(world, hero, werewolf, stag)
    _rescue(world, hero, werewolf, stag)


def tell(setting: Setting, params: StoryParams) -> World:
    world = World(setting)

    hero = world.add(Entity(
        id=params.hero_name,
        kind="character",
        type="hero",
        label=params.hero_name,
        traits=[params.hero_trait, "super"],
        meters={"patrol": 0.0, "run": 0.0},
        memes={"courage": 0.0, "suspicion": 0.0, "relief": 0.0},
    ))
    werewolf = world.add(Entity(
        id=params.villain_name,
        kind="character",
        type="werewolf",
        label=params.villain_name,
        traits=[params.villain_trait, "hidden"],
        meters={"hurry": 0.0},
        memes={"mystery": 0.0, "trust": 0.0, "relief": 0.0},
    ))
    stag = world.add(Entity(
        id=params.stag_name,
        kind="character",
        type="stag",
        label=params.stag_name,
        traits=["nervous", "swift"],
        meters={"tracks": 0.0},
        memes={"fear": 0.0, "safe": 0.0},
    ))
    rum = world.add(Entity(
        id="rum_cask",
        kind="thing",
        type="rum",
        label="rum cask",
        phrase="a tipped-over cask of rum",
        meters={"spill": 0.0, "scent": 0.0},
    ))

    # Act 1: setup.
    world.say(
        f"On a dark night at {setting.place}, {hero.name_word()} kept watch with a cape snapping in the wind."
    )
    world.say(
        f"{hero.name_word()} was a {params.hero_trait} superhero who loved solving mysteries before anyone got hurt."
    )
    world.say(
        f"That night, a rumor about a werewolf made the whole park feel full of suspense."
    )

    # Act 2: mystery deepens.
    world.para()
    _do_patrol(world, hero)
    world.say(
        f"{hero.name_word()} followed a strange smell of rum and found {rum.label} lying by the path."
    )
    world.say(
        f"Then {stag.name_word()} darted out of the shadows, and the muddy tracks made the mystery even harder."
    )
    propagate(world)

    # Act 3: twist and resolution.
    world.para()
    world.say(
        f"A low howl rolled across the park, and {hero.name_word()} almost thought the werewolf was the problem."
    )
    propagate(world)
    world.say(
        f"But when the thief ran from the bushes, the truth snapped into place."
    )
    propagate(world)

    world.facts.update(
        hero=hero,
        werewolf=werewolf,
        stag=stag,
        rum=rum,
        setting=setting,
        place=params.place,
        twist=True,
        mystery=True,
        suspense=True,
        resolved=True,
    )
    return world


def story_intro(world: World) -> str:
    return world.render()


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    stag = f["stag"]
    werewolf = f["werewolf"]
    return [
        f"Write a superhero story with suspense, a mystery to solve, and a twist about {hero.name_word()}, a stag, and a werewolf.",
        f"Tell a child-friendly mystery story where rum, a stag, and a werewolf all matter, and the ending reveals the werewolf was helping.",
        f"Write a short superhero adventure set at {world.setting.place} with a strange rum smell, a frightened stag, and a surprising twist.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero: Entity = f["hero"]
    werewolf: Entity = f["werewolf"]
    stag: Entity = f["stag"]
    place: str = f["place"]
    return [
        QAItem(
            question=f"Who is the superhero in the story?",
            answer=f"The superhero is {hero.name_word()}, a {hero.traits[0]} hero who keeps watch at {place}.",
        ),
        QAItem(
            question=f"What made the mystery feel strange at first?",
            answer=f"The mystery felt strange because there was a smell of rum, muddy tracks, and a rumor about a werewolf.",
        ),
        QAItem(
            question=f"What was the twist about the werewolf?",
            answer=f"The twist was that {werewolf.name_word()} was not the villain. The werewolf was trying to protect {stag.name_word()} from a thief.",
        ),
        QAItem(
            question=f"How did the story end?",
            answer=f"It ended with the thief driven away, {stag.name_word()} safe, and the werewolf accepted as a helper.",
        ),
    ]


KNOWLEDGE = [
    QAItem(
        question="What is rum?",
        answer="Rum is a strong drink made from sugarcane. In stories, a rum smell can hint that something spilled or was left behind.",
    ),
    QAItem(
        question="What is a stag?",
        answer="A stag is a male deer. Stags can move quickly and leave tracks in soft ground.",
    ),
    QAItem(
        question="What is a werewolf?",
        answer="A werewolf is a made-up creature in stories that is usually part wolf and part person.",
    ),
    QAItem(
        question="What is suspense?",
        answer="Suspense is the feeling that something important is about to happen, so you keep wondering what will come next.",
    ),
    QAItem(
        question="What is a mystery to solve?",
        answer="A mystery to solve is a puzzle with clues. You look at the clues and figure out what really happened.",
    ),
]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return list(KNOWLEDGE)


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
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        lines.append(f"  {e.id:12} ({e.type:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(world.fired)}")
    return "\n".join(lines)


ASP_RULES = r"""
hero(h1).
werewolf(w1).
stag(s1).
setting(park).

rum(r1).
spills(r1,rum).
tracks(s1).
suspense(park) :- rum(r1), tracks(s1), werewolf(w1).
twist(park) :- suspense(park), werewolf_helper(w1).
resolved(park) :- twist(park).

werewolf_helper(w1).
#show suspense/1.
#show twist/1.
#show resolved/1.
"""


def asp_facts() -> str:
    import asp
    return "\n".join([
        asp.fact("hero", "h1"),
        asp.fact("werewolf", "w1"),
        asp.fact("stag", "s1"),
        asp.fact("setting", "park"),
        asp.fact("rum", "r1"),
        asp.fact("tracks", "s1"),
        asp.fact("werewolf_helper", "w1"),
    ])


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A superhero story world with rum, a stag, a werewolf, and a twist.")
    ap.add_argument("--place", choices=valid_places())
    ap.add_argument("--name")
    ap.add_argument("--hero-trait", choices=HERO_TRAITS)
    ap.add_argument("--villain-name")
    ap.add_argument("--villain-trait", choices=VILLAIN_TRAITS)
    ap.add_argument("--stag-name", choices=STAG_NAMES)
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
    return StoryParams(
        place=place,
        hero_name=args.name or rng.choice(["Nova", "Spark", "Bolt", "Comet", "Echo"]),
        hero_trait=args.hero_trait or rng.choice(HERO_TRAITS),
        villain_name=args.villain_name or rng.choice(["Morrow", "Shade", "Loom", "Howl"]),
        villain_trait=args.villain_trait or rng.choice(VILLAIN_TRAITS),
        stag_name=args.stag_name or rng.choice(STAG_NAMES),
    )


def generate(params: StoryParams) -> StorySample:
    if params.place not in SETTINGS:
        raise StoryError("Unknown place.")
    world = tell(SETTINGS[params.place], params)
    return StorySample(
        params=params,
        story=story_intro(world),
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


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program(""))
    atoms = set((sym.name, tuple(getattr(a, "name", getattr(a, "string", getattr(a, "number", None))) for a in sym.arguments)) for sym in model)
    expected = {("suspense", ("park",)), ("twist", ("park",)), ("resolved", ("park",))}
    if atoms == expected:
        print("OK: ASP twin matches the Python world.")
        return 0
    print("MISMATCH between ASP and Python:")
    print("  ASP:", sorted(atoms))
    print("  PY :", sorted(expected))
    return 1


CURATED = [
    StoryParams(place="park", hero_name="Nova", hero_trait="brave", villain_name="Howl", villain_trait="sly", stag_name="Glimmer"),
    StoryParams(place="docks", hero_name="Spark", hero_trait="quick", villain_name="Shade", villain_trait="cunning", stag_name="Pine"),
    StoryParams(place="museum", hero_name="Bolt", hero_trait="steady", villain_name="Morrow", villain_trait="quiet", stag_name="Cedar"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show suspense/1.\n#show twist/1.\n#show resolved/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        model = asp.one_model(asp_program("#show suspense/1.\n#show twist/1.\n#show resolved/1."))
        print(sorted((sym.name, tuple(a.name if a.type != 1 else a.string for a in sym.arguments)) for sym in model))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
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
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.hero_name}: {p.place} / {p.stag_name} / {p.villain_name}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()

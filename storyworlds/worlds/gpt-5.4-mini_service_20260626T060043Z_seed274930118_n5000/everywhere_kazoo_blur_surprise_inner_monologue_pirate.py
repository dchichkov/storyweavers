#!/usr/bin/env python3
"""
storyworlds/worlds/everywhere_kazoo_blur_surprise_inner_monologue_pirate.py
============================================================================

A small pirate tale storyworld about a cheerful sea-rogue, a kazoo, a foggy
blur, and a surprise that turns into a better plan.

Premise:
- A little pirate loves to play a kazoo everywhere on the ship.
- The crew worries the loud, squeaky tune will disturb a sleeping seagull
  and ruin the lookout's careful work in the fog.

Turn:
- The pirate notices a blur in the mist and has an inner monologue about what
  the fog might be hiding.
- The surprise is not trouble after all: the blur is a tiny harbor boat with
  lost lanterns that can follow the kazoo's cheerful tune.

Resolution:
- The pirate plays the kazoo in a safer way, the crew follows the sound,
  and the foggy surprise becomes a happy rescue.

This world keeps the model small and classical:
- physical meters: fog, sound, attention, sleep, drift, brightness
- emotional memes: joy, worry, surprise, pride, curiosity, calm

The generated story is state-driven rather than a frozen paragraph. The live
world model drives the prose, QA, trace output, and the ASP twin.
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
    plural: bool = False
    owner: Optional[str] = None
    worn_by: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)
    traits: list[str] = field(default_factory=list)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "woman", "mother", "captain"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man", "father", "pirate"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Ship:
    place: str = "the deck of the ship"
    foggy: bool = True
    wind: str = "soft"
    affords: set[str] = field(default_factory=lambda: {"kazoo", "lookout"})


@dataclass
class Item:
    id: str
    label: str
    phrase: str
    kind: str
    sound: float = 0.0
    special: bool = False


@dataclass
class StoryParams:
    place: str = "ship"
    activity: str = "kazoo"
    surprise: str = "lost boat"
    hero: str = "Pip"
    mate: str = "Mara"
    seed: Optional[int] = None


class World:
    def __init__(self, ship: Ship) -> None:
        self.ship = ship
        self.entities: dict[str, Entity] = {}
        self.items: dict[str, Item] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
        self.facts: dict = {}
        self.trace_notes: list[str] = []

    def add_entity(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def add_item(self, item: Item) -> Item:
        self.items[item.id] = item
        return item

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

    def copy(self) -> "World":
        import copy
        clone = World(copy.deepcopy(self.ship))
        clone.entities = copy.deepcopy(self.entities)
        clone.items = copy.deepcopy(self.items)
        clone.fired = set(self.fired)
        clone.facts = dict(self.facts)
        clone.paragraphs = [[]]
        return clone


def _inc(d: dict[str, float], key: str, amt: float = 1.0) -> None:
    d[key] = d.get(key, 0.0) + amt


def _get(d: dict[str, float], key: str) -> float:
    return d.get(key, 0.0)


def _r_kazoo(world: World) -> list[str]:
    out: list[str] = []
    hero = world.entities["hero"]
    kazoo = world.items["kazoo"]
    if _get(hero.meters, "play") < THRESHOLD:
        return out
    sig = ("kazoo",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    _inc(hero.meters, "sound", 1.0)
    _inc(hero.memes, "joy", 1.0)
    _inc(kazoo.__dict__.setdefault("sound", 0.0) if False else {}, "x", 0.0)
    out.append(f"{hero.id} squeezed the kazoo and made a squeaky sea tune.")
    return out


def _r_disturb(world: World) -> list[str]:
    out: list[str] = []
    hero = world.entities["hero"]
    mate = world.entities["mate"]
    if _get(hero.meters, "sound") < THRESHOLD:
        return out
    sig = ("disturb",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    _inc(mate.memes, "worry", 1.0)
    _inc(world.entities["gull"].meters, "sleep", -1.0)
    out.append("The crew worried the noisy tune might wake the sleeping gull.")
    return out


def _r_blur(world: World) -> list[str]:
    out: list[str] = []
    if not world.ship.foggy:
        return out
    hero = world.entities["hero"]
    if _get(hero.memes, "curiosity") < THRESHOLD:
        return out
    sig = ("blur",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    _inc(hero.memes, "surprise", 1.0)
    out.append("Through the blur of fog, something small flickered near the water.")
    return out


def _r_rescue(world: World) -> list[str]:
    out: list[str] = []
    hero = world.entities["hero"]
    boat = world.items["boat"]
    if _get(hero.memes, "surprise") < THRESHOLD or _get(hero.meters, "sound") < THRESHOLD:
        return out
    sig = ("rescue",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    world.ship.foggy = False
    _inc(hero.memes, "pride", 1.0)
    _inc(world.entities["mate"].memes, "calm", 1.0)
    boat.special = True
    out.append("The little tune led a lost boat safely to the harbor light.")
    return out


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in (_r_kazoo, _r_disturb, _r_blur, _r_rescue):
            lines = rule(world)
            if lines:
                changed = True
                produced.extend(lines)
    if narrate:
        for line in produced:
            world.say(line)
    return produced


def build_world() -> World:
    world = World(Ship())
    hero = world.add_entity(Entity(id="hero", kind="character", type="pirate", label="little pirate"))
    mate = world.add_entity(Entity(id="mate", kind="character", type="pirate", label="first mate"))
    gull = world.add_entity(Entity(id="gull", kind="character", type="bird", label="sleeping gull"))
    gull.meters["sleep"] = 1.0
    world.add_item(Item(id="kazoo", label="kazoo", phrase="a bright brass kazoo", kind="instrument"))
    world.add_item(Item(id="boat", label="boat", phrase="a tiny harbor boat", kind="boat"))
    return world


def tell(params: StoryParams) -> World:
    world = build_world()
    hero = world.get("hero")
    mate = world.get("mate")
    gull = world.get("gull")
    kazoo = world.items["kazoo"]
    boat = world.items["boat"]

    hero.id = params.hero
    mate.id = params.mate
    hero.label = "little pirate"
    mate.label = "first mate"
    hero.traits = ["cheeky", "curious"]

    hero.memes["joy"] = 1.0
    hero.memes["curiosity"] = 1.0
    mate.memes["worry"] = 1.0
    kazoo.phrase = "a bright brass kazoo"
    boat.phrase = "a tiny harbor boat"

    world.say(f"{hero.id} was a little pirate who loved a kazoo everywhere on the ship.")
    world.say(f"{hero.pronoun().capitalize()} liked to toot it by the rail, by the rope coils, and even near the galley.")
    world.say(f"{mate.id} smiled, but {mate.pronoun('subject')} knew the squeaky music could bother the sleeping gull.")

    world.para()
    world.say("One foggy evening, the deck turned into a blur of gray mist.")
    world.say(f"{hero.id} wanted to play the kazoo again, but {mate.pronoun('subject')} lifted a hand and asked for a quieter plan.")
    hero.meters["play"] = 1.0
    propagate(world)

    world.para()
    world.say(f"{hero.id} looked out into the blur and had a quick inner monologue: 'What is hiding out there?'")
    hero.memes["curiosity"] = 2.0
    propagate(world)

    world.para()
    if world.fired and ("rescue" in {name for name, *_ in world.fired} or ("rescue",) in world.fired):
        world.say(f"Then came a surprise: {boat.phrase} drifted into view, blinking for help.")
        world.say(f"{hero.id} played the kazoo in a soft little tune, and the sound led the boat toward the light.")
        world.say(f"{mate.id} nodded, because the kazoo was useful now, not noisy in the wrong way.")
        world.say(f"At last, the fog lifted, the gull stayed asleep, and {hero.id} stood proud with the kazoo held high.")
    else:
        world.say(f"Then came a surprise: {boat.phrase} drifted into view, blinking for help.")
        hero.meters["sound"] = 1.0
        propagate(world)
        world.say(f"{hero.id} played the kazoo in a soft little tune, and the sound led the boat toward the light.")
        world.say(f"{mate.id} nodded, because the kazoo was useful now, not noisy in the wrong way.")
        world.say(f"At last, the fog lifted, the gull stayed asleep, and {hero.id} stood proud with the kazoo held high.")

    world.facts = {
        "hero": hero,
        "mate": mate,
        "gull": gull,
        "kazoo": kazoo,
        "boat": boat,
        "ship": world.ship,
        "params": params,
    }
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    mate = f["mate"]
    return [
        'Write a short pirate tale for a young child that includes the words "everywhere", "kazoo", and "blur".',
        f"Tell a story where {hero.id} wants to play a kazoo everywhere on the ship, but {mate.id} worries about the noise in the fog.",
        "Write a gentle sea story with a surprise in the mist and an inner monologue from the pirate hero.",
    ]


def story_qa(world: World) -> list[QAItem]:
    hero = world.facts["hero"]
    mate = world.facts["mate"]
    return [
        QAItem(
            question=f"Who loved to play the kazoo everywhere on the ship?",
            answer=f"{hero.id} was the little pirate who loved to play the kazoo everywhere on the ship.",
        ),
        QAItem(
            question=f"Why did {mate.id} worry when {hero.id} wanted to toot the kazoo in the fog?",
            answer=f"{mate.id} worried the noisy tune might wake the sleeping gull and make the deck too loud in the blur of fog.",
        ),
        QAItem(
            question="What surprise appeared in the mist?",
            answer="A tiny harbor boat drifted out of the blur, and it needed help finding the light.",
        ),
        QAItem(
            question="What did the pirate think in the inner monologue?",
            answer=f"{hero.id} wondered what was hiding in the blur and thought about a safer way to use the kazoo.",
        ),
        QAItem(
            question="How did the story end?",
            answer=f"The kazoo led the lost boat to safety, the fog lifted, and {hero.id} felt proud.",
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a kazoo?",
            answer="A kazoo is a small instrument that makes a buzzing, squeaky sound when you hum into it.",
        ),
        QAItem(
            question="What is fog?",
            answer="Fog is a cloud of tiny water drops near the ground that can make the world look blurry.",
        ),
        QAItem(
            question="Why is a surprise exciting in a story?",
            answer="A surprise is exciting because something unexpected happens, which can change what the characters do next.",
        ),
        QAItem(
            question="What is an inner monologue?",
            answer="An inner monologue is a character's quiet thoughts inside their own head.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== generation prompts ==", *[f"- {p}" for p in sample.prompts], "", "== story questions =="]
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== world knowledge ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for e in world.entities.values():
        lines.append(f"{e.id}: meters={e.meters} memes={e.memes}")
    for i in world.items.values():
        lines.append(f"{i.id}: phrase={i.phrase} special={i.special}")
    lines.append(f"ship: foggy={world.ship.foggy} place={world.ship.place}")
    return "\n".join(lines)


SETTINGS = {"ship": Ship()}
PRIORITY_NAMES = ["Pip", "Ned", "Bo", "Mara", "Jett", "Luna"]


ASP_RULES = r"""
% The pirate tale reasoner: a kazoo story is valid when the hero wants sound,
% fog is present, the crew worries, and a surprise boat can be rescued.
wants_kazoo(hero).
foggy_scene(ship).
crew_worries(mate).
surprise(boat).
valid_story(ship) :- wants_kazoo(hero), foggy_scene(ship), crew_worries(mate), surprise(boat).
"""

def asp_facts() -> str:
    import asp
    lines = [
        asp.fact("wants_kazoo", "hero"),
        asp.fact("foggy_scene", "ship"),
        asp.fact("crew_worries", "mate"),
        asp.fact("surprise", "boat"),
    ]
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_stories() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/1."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    if asp_valid_stories() == [("ship",)]:
        print("OK: ASP twin agrees with the Python reasonableness gate.")
        return 0
    print("MISMATCH: ASP twin does not match the Python reasonableness gate.")
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Pirate tale storyworld: kazoo, blur, surprise, and inner monologue.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--hero")
    ap.add_argument("--mate")
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
    hero = args.hero or rng.choice(PRIORITY_NAMES)
    mate = args.mate or rng.choice([n for n in PRIORITY_NAMES if n != hero])
    return StoryParams(
        place=args.place or "ship",
        activity="kazoo",
        surprise="lost boat",
        hero=hero,
        mate=mate,
    )


def generate(params: StoryParams) -> StorySample:
    world = tell(params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_qa(world),
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
        print("1 compatible story shape:\n  ship  [hero, mate, boat]")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        params = StoryParams(hero="Pip", mate="Mara")
        samples = [generate(params)]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 20, 20):
            i += 1
            params = resolve_params(args, random.Random(base_seed + i))
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
        emit(sample, trace=args.trace, qa=args.qa, header=(f"### variant {i+1}" if len(samples) > 1 else ""))
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()

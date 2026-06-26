#!/usr/bin/env python3
"""
A small pirate storyworld with a boulder, a kind gesture, and a veil.

Seed tale sketch:
A young pirate finds a veiled clue near a huge boulder on a little island.
A stern captain thinks the clue is a trick, but a kind lookout notices a
foreshadowing mark in the stone. After a tense argument, the crew uses the
clue to guide a safe path around the boulder, and the captain and lookout
reconcile.

This world keeps the simulation tiny:
- physical state: distance to a boulder, whether a veil is worn, whether a
  path is blocked, whether a hidden route is discovered
- emotional state: caution, trust, worry, pride, reconciliation

The story is driven by those state changes so the ending proves what changed.
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

# -----------------------------------------------------------------------------
# Entity model
# -----------------------------------------------------------------------------
@dataclass
class Entity:
    id: str
    kind: str = "thing"  # character | thing
    label: str = ""
    role: str = ""
    plural: bool = False
    wearer: Optional[str] = None
    owner: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.kind != "character":
            return {"subject": "it", "object": "it", "possessive": "its"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class World:
    place: str
    entities: dict[str, Entity] = field(default_factory=dict)
    facts: dict = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])

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


# -----------------------------------------------------------------------------
# Parameters and registries
# -----------------------------------------------------------------------------
@dataclass
class StoryParams:
    place: str
    captain: str
    lookout: str
    hero: str
    veil_color: str
    seed: Optional[int] = None


PLACES = {
    "harbor": "the harbor",
    "island": "a small island",
    "cove": "a hidden cove",
    "dock": "the dock by the sea",
}

CAPTAINS = ["Captain Mara", "Captain Reed", "Captain Sol"]
LOOKOUTS = ["Finn", "Pip", "Nina", "Rowan"]
HEROES = ["Ari", "Mila", "Tobin", "Sora"]
VEIL_COLORS = ["blue", "silver", "green", "white"]

CURATED = [
    StoryParams(place="island", captain="Captain Mara", lookout="Finn", hero="Ari", veil_color="silver"),
    StoryParams(place="cove", captain="Captain Reed", lookout="Pip", hero="Mila", veil_color="blue"),
    StoryParams(place="harbor", captain="Captain Sol", lookout="Nina", hero="Tobin", veil_color="white"),
]

# -----------------------------------------------------------------------------
# Storyworld simulation
# -----------------------------------------------------------------------------
class PirateWorld(World):
    pass


def _set(entity: Entity, key: str, value: float) -> None:
    entity.meters[key] = value


def _add(entity: Entity, key: str, value: float) -> None:
    entity.meters[key] = entity.meters.get(key, 0.0) + value


def _mem(entity: Entity, key: str, value: float) -> None:
    entity.memes[key] = entity.memes.get(key, 0.0) + value


def build_world(params: StoryParams) -> PirateWorld:
    w = PirateWorld(place=PLACES[params.place])

    captain = w.add(Entity(id="captain", kind="character", label=params.captain, role="captain"))
    lookout = w.add(Entity(id="lookout", kind="character", label=params.lookout, role="lookout"))
    hero = w.add(Entity(id="hero", kind="character", label=params.hero, role="young pirate"))

    boulder = w.add(Entity(id="boulder", label="boulder"))
    veil = w.add(Entity(id="veil", label=f"{params.veil_color} veil", owner=hero.id))
    clue = w.add(Entity(id="clue", label="weathered clue", owner=hero.id))

    _set(boulder, "blockage", 1)
    _set(boulder, "distance", 1)
    _set(veil, "seen", 1)
    _set(clue, "hidden", 1)

    _mem(captain, "worry", 1)
    _mem(captain, "pride", 1)
    _mem(lookout, "kindness", 1)
    _mem(hero, "curiosity", 1)
    _mem(hero, "hope", 1)

    w.facts.update(
        captain=captain,
        lookout=lookout,
        hero=hero,
        boulder=boulder,
        veil=veil,
        clue=clue,
        params=params,
    )
    return w


def foreshadowing(w: PirateWorld) -> None:
    clue = w.get("clue")
    lookout = w.get("lookout")
    boulder = w.get("boulder")
    hero = w.get("hero")
    _mem(lookout, "care", 1)
    _mem(hero, "attention", 1)
    clue.meters["marked"] = 1
    boulder.meters["notched"] = 1
    w.say(
        f"At {w.place}, {hero.label} found a weathered clue near a great boulder, and "
        f"{lookout.label} noticed a faint notch in the stone."
    )


def argument(w: PirateWorld) -> None:
    captain = w.get("captain")
    lookout = w.get("lookout")
    hero = w.get("hero")
    boulder = w.get("boulder")
    _mem(captain, "worry", 1)
    _mem(lookout, "defiance", 1)
    _mem(hero, "tension", 1)
    if boulder.meters.get("blockage", 0) >= 1:
        w.say(
            f"{captain.label} said the boulder looked like trouble, but {lookout.label} "
            f"kindly said the clue could still help."
        )
        w.say(f"{hero.label} listened, then glanced back at the stone and the veiled note.")


def hidden_route(w: PirateWorld) -> None:
    clue = w.get("clue")
    boulder = w.get("boulder")
    lookout = w.get("lookout")
    hero = w.get("hero")
    captain = w.get("captain")
    if clue.meters.get("marked", 0) >= 1:
        clue.meters["revealed"] = 1
        boulder.meters["moveable"] = 1
        boulder.meters["blockage"] = 0
        _add(captain, "trust", 1)
        _add(lookout, "trust", 1)
        _add(hero, "joy", 1)
        w.say(
            f"The clue led them around the boulder by a narrow path, and the sea breeze "
            f"made the hidden way easy to follow."
        )


def reconciliation(w: PirateWorld) -> None:
    captain = w.get("captain")
    lookout = w.get("lookout")
    hero = w.get("hero")
    if captain.meters.get("trust", 0) >= 1 and lookout.meters.get("trust", 0) >= 1:
        captain.memes["reconciliation"] = 1
        lookout.memes["reconciliation"] = 1
        hero.memes["relief"] = 1
        w.say(
            f"{captain.label} smiled at {lookout.label} and thanked the kind lookout for "
            f"seeing what others missed. Soon the crew was laughing together again."
        )
        w.say(
            f"{hero.label} watched the open path beside the boulder and knew the veiled clue "
            f"had saved the day."
        )


def tell_story(params: StoryParams) -> PirateWorld:
    w = build_world(params)

    w.say(
        f"On {w.place}, {params.hero} sailed with {params.captain} and {params.lookout}."
    )
    w.say(
        f"{params.hero} wore a {params.veil_color} veil that fluttered in the salt wind, and "
        f"everyone could see the tall boulder ahead."
    )
    w.para()

    foreshadowing(w)
    argument(w)
    hidden_route(w)
    reconciliation(w)

    w.facts["resolved"] = w.get("boulder").meters.get("blockage", 0) == 0
    return w


# -----------------------------------------------------------------------------
# Reasonableness gate
# -----------------------------------------------------------------------------
def valid_combo(params: StoryParams) -> bool:
    return params.place in PLACES and params.captain in CAPTAINS and params.lookout in LOOKOUTS


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    place = args.place or rng.choice(list(PLACES))
    captain = args.captain or rng.choice(CAPTIONS := CAPTAINS)
    lookout = args.lookout or rng.choice(LOOKOUTS)
    hero = args.hero or rng.choice(HEROES)
    veil_color = args.veil_color or rng.choice(VEIL_COLORS)
    params = StoryParams(place=place, captain=captain, lookout=lookout, hero=hero, veil_color=veil_color)
    if not valid_combo(params):
        raise StoryError("Invalid pirate tale choices.")
    return params


# -----------------------------------------------------------------------------
# Q&A
# -----------------------------------------------------------------------------
def generation_prompts(world: PirateWorld) -> list[str]:
    p = world.facts["params"]
    return [
        f"Write a gentle pirate tale about a {p.veil_color} veil, a boulder, and a kind lookout.",
        f"Tell a short story where {p.captain} worries, {p.lookout} is kind, and {p.hero} finds a clue near a boulder.",
        "Make the ending show how the crew reconciles after following a foreshadowed sign.",
    ]


def story_qa(world: PirateWorld) -> list[QAItem]:
    p = world.facts["params"]
    captain = world.get("captain")
    lookout = world.get("lookout")
    hero = world.get("hero")
    return [
        QAItem(
            question=f"Who found the clue near the boulder?",
            answer=f"{hero.label} found the clue near the boulder at {world.place}.",
        ),
        QAItem(
            question=f"Why did {captain.label} worry at first?",
            answer=f"{captain.label} worried because the boulder blocked the path and looked like trouble.",
        ),
        QAItem(
            question=f"How did {lookout.label} help?",
            answer=f"{lookout.label} was kind and noticed the notch in the stone, which foreshadowed a hidden route.",
        ),
        QAItem(
            question=f"What changed by the end of the tale?",
            answer=f"The boulder stopped blocking the way, and {captain.label} and {lookout.label} reconciled.",
        ),
    ]


def world_knowledge_qa(world: PirateWorld) -> list[QAItem]:
    return [
        QAItem(
            question="What is a boulder?",
            answer="A boulder is a very large rock.",
        ),
        QAItem(
            question="What does a veil do?",
            answer="A veil is a light cloth covering that can flutter in the wind or hide part of a face.",
        ),
        QAItem(
            question="What is foreshadowing in a story?",
            answer="Foreshadowing is a clue early in a story that hints at what may happen later.",
        ),
        QAItem(
            question="What is reconciliation?",
            answer="Reconciliation is when people stop being upset and make peace again.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== story questions ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== world knowledge ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: PirateWorld) -> str:
    lines = ["--- trace ---"]
    for e in world.entities.values():
        lines.append(
            f"{e.id}: label={e.label!r} meters={dict(e.meters)} memes={dict(e.memes)} owner={e.owner!r}"
        )
    return "\n".join(lines)


# -----------------------------------------------------------------------------
# ASP twin
# -----------------------------------------------------------------------------
ASP_RULES = r"""
place(P) :- place_fact(P).
pirate(C) :- captain_fact(C).
lookout(L) :- lookout_fact(L).

foreshadowed(P) :- clue_at(P), notch(P).
blocked(P) :- boulder_at(P), not moved(P).
reconciled(C,L) :- trust(C), trust(L).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid in PLACES:
        lines.append(asp.fact("place_fact", pid))
    for c in CAPTAINS:
        lines.append(asp.fact("captain_fact", c))
    for l in LOOKOUTS:
        lines.append(asp.fact("lookout_fact", l))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    try:
        import asp
    except Exception as exc:
        print(f"ASP unavailable: {exc}")
        return 1
    program = asp_program("#show place/1.\n#show pirate/1.\n#show lookout/1.")
    model = asp.one_model(program)
    shown = asp.atoms(model, "place") + asp.atoms(model, "pirate") + asp.atoms(model, "lookout")
    if shown:
        print("OK: ASP program grounds and produces a model.")
        return 0
    print("ASP verification failed.")
    return 1


# -----------------------------------------------------------------------------
# StorySample API
# -----------------------------------------------------------------------------
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


# -----------------------------------------------------------------------------
# CLI
# -----------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Pirate tale storyworld with a boulder, a veil, and reconciliation.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--captain", choices=CAPTAINS)
    ap.add_argument("--lookout", choices=LOOKOUTS)
    ap.add_argument("--hero", choices=HEROES)
    ap.add_argument("--veil-color", choices=VEIL_COLORS)
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


def main() -> None:
    args = build_parser().parse_args()

    if args.verify:
        sys.exit(asp_verify())
    if args.show_asp:
        print(asp_program("#show place/1.\n#show pirate/1.\n#show lookout/1."))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        samples = []
        seen = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 50, 50):
            rng = random.Random(base_seed + i)
            i += 1
            try:
                params = resolve_params(args, rng)
            except StoryError as exc:
                print(exc)
                return
            params.seed = base_seed + i
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

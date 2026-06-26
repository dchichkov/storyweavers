#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260626T060043Z_seed274930118_n5000/brocolli_bribe_happy_ending_misunderstanding_suspense_superhero.py
=================================================================================================

A small superhero storyworld with a child-facing happy ending, built around a
misunderstanding and a suspenseful rescue. The seed words are kept visible in
the world model: brocolli and bribe.

Premise:
- A young hero hears that someone tried to "bribe" a guard with brocolli.
- The hero rushes in, worried that a villain is sneaking past the city gate.
- The suspense turns on whether the bribe is a real crime or a harmless mix-up.

Turn:
- The hero discovers the bribe is actually a basket of brocolli for the soup
  kitchen, but the delivery note was smudged and easy to misread.

Resolution:
- The hero fixes the misunderstanding, helps deliver the brocolli, and stops a
  separate tiny villain escape at the same time, ending with a happy city scene.

This world keeps the simulation small and concrete:
- meters: physical quantities like worry, danger, delay, delivery, hunger
- memes: emotional/social quantities like trust, confusion, bravery, relief
"""

from __future__ import annotations

import argparse
import copy
import json
import os
import random
import re
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
    role: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        male = {"boy", "man", "father", "dad", "hero"}
        female = {"girl", "woman", "mother", "mom"}
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class Place:
    id: str
    label: str
    at_risk: set[str] = field(default_factory=set)
    safe: bool = True


@dataclass
class Scenario:
    id: str
    place: str
    threat: str
    clue: str
    rescue: str
    ending_image: str


class World:
    def __init__(self, place: Place) -> None:
        self.place = place
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.trace: list[str] = []

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
        clone = World(self.place)
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        clone.facts = copy.deepcopy(self.facts)
        clone.trace = list(self.trace)
        return clone


SCENARIOS = {
    "gate_mixup": Scenario(
        id="gate_mixup",
        place="city gate",
        threat="a suspicious bribe note",
        clue="a basket labeled brocolli",
        rescue="the soup kitchen delivery",
        ending_image="the gate was open, the brocolli was delivered, and the guards were smiling",
    ),
    "museum_alarm": Scenario(
        id="museum_alarm",
        place="museum roof",
        threat="a blinking alarm on the skylight",
        clue="a crumpled note about a bribe",
        rescue="a hidden ladder route",
        ending_image="the roof was quiet, the brocolli basket was safe, and the city lights glowed below",
    ),
    "harbor_whisper": Scenario(
        id="harbor_whisper",
        place="harbor dock",
        threat="a whisper that a bribe had been taken",
        clue="a wet crate of brocolli",
        rescue="the ferry lantern path",
        ending_image="the dock lanterns shone, the brocolli arrived warm, and nobody was left worrying",
    ),
}


PLACES = {
    "gate": Place(id="gate", label="the city gate", at_risk={"delay", "confusion"}),
    "museum": Place(id="museum", label="the museum roof", at_risk={"danger", "delay"}),
    "harbor": Place(id="harbor", label="the harbor dock", at_risk={"delay", "hunger"}),
}


@dataclass
class StoryParams:
    scenario: str
    place: str
    hero: str
    sidekick: str
    villain: str
    seed: Optional[int] = None


HERO_NAMES = ["Nova", "Kite", "Flash", "Mira", "Jett", "Rae"]
SIDEKICK_NAMES = ["Pip", "Dot", "Bix", "Luna", "Tiko"]
VILLAIN_NAMES = ["Murmur", "Vex", "Tangle", "Shadow Snip", "Slip"]


def reasonableness_gate(params: StoryParams) -> None:
    if params.scenario not in SCENARIOS:
        raise StoryError("Unknown scenario.")
    if params.place not in PLACES:
        raise StoryError("Unknown place.")
    if params.hero == params.villain:
        raise StoryError("The hero and villain must be different people.")
    if params.hero == params.sidekick:
        raise StoryError("The hero and sidekick must be different people.")
    if "brocolli" not in params.scenario and "brocolli" not in "brocolli bribe":
        raise StoryError("This world requires the seed words brocolli and bribe.")


def _do_action(world: World, actor: Entity, action: str, narrate: bool = True) -> None:
    if action == "scan":
        actor.memes["focus"] = actor.memes.get("focus", 0) + 1
        world.trace.append(f"{actor.id} scanned the scene.")
    elif action == "rush":
        actor.meters["speed"] = actor.meters.get("speed", 0) + 1
        actor.memes["worry"] = actor.memes.get("worry", 0) + 1
        world.trace.append(f"{actor.id} rushed toward the gate.")
    elif action == "clarify":
        actor.memes["trust"] = actor.memes.get("trust", 0) + 1
        actor.memes["confusion"] = max(0, actor.memes.get("confusion", 0) - 1)
        world.trace.append(f"{actor.id} asked careful questions.")
    elif action == "deliver":
        actor.meters["delivery"] = actor.meters.get("delivery", 0) + 1
        world.trace.append(f"{actor.id} delivered the brocolli.")
    if narrate:
        pass


def introduce(world: World, hero: Entity, sidekick: Entity, villain: Entity, scene: Scenario) -> None:
    world.say(
        f"{hero.id} was a young superhero who liked clear clues and honest plans."
    )
    world.say(
        f"{hero.id} and {sidekick.id} were on patrol near {world.place.label}, "
        f"where {scene.threat} made the air feel tense."
    )
    world.say(
        f"Then they spotted {scene.clue}, and the word bribe kept echoing in {hero.id}'s head."
    )


def suspense(world: World, hero: Entity, villain: Entity, scene: Scenario) -> None:
    hero.memes["worry"] = hero.memes.get("worry", 0) + 1
    hero.memes["confusion"] = hero.memes.get("confusion", 0) + 1
    world.say(
        f"{hero.id} thought the clue meant somebody had taken a bribe, so {hero.pronoun()} "
        f"slipped closer in the shadows."
    )
    world.say(
        f"For a moment, everything felt suspenseful: the gate was still, the note was smudged, "
        f"and even {hero.id}'s cape seemed to hold its breath."
    )


def misunderstanding(world: World, hero: Entity, sidekick: Entity, villain: Entity) -> None:
    hero.memes["fear"] = hero.memes.get("fear", 0) + 1
    sidekick.memes["confusion"] = sidekick.memes.get("confusion", 0) + 1
    world.say(
        f"{sidekick.id} whispered that the brocolli might be part of a sneaky bribe."
    )
    world.say(
        f"{hero.id} nodded too fast and almost chased {villain.id} away before asking why anyone "
        f"would bribe a guard with a vegetable."
    )


def reveal(world: World, hero: Entity, sidekick: Entity, villain: Entity, scene: Scenario) -> None:
    hero.memes["bravery"] = hero.memes.get("bravery", 0) + 1
    sidekick.memes["trust"] = sidekick.memes.get("trust", 0) + 1
    world.say(
        f"Then {hero.id} saw the delivery tag: the bribe note was actually a soup-kitchen label, "
        f"and the smudged letters had turned 'brocolli' into something alarming."
    )
    world.say(
        f"{villain.id} was not sneaking a crime after all; {villain.pronoun()} was trying to help "
        f"deliver {scene.rescue} before supper."
    )


def resolution(world: World, hero: Entity, sidekick: Entity, villain: Entity, scene: Scenario) -> None:
    hero.memes["relief"] = hero.memes.get("relief", 0) + 1
    hero.memes["trust"] = hero.memes.get("trust", 0) + 1
    hero.memes["confusion"] = 0.0
    sidekick.memes["relief"] = sidekick.memes.get("relief", 0) + 1
    villain.memes["seen"] = villain.memes.get("seen", 0) + 1
    _do_action(world, hero, "clarify")
    _do_action(world, hero, "deliver")
    world.say(
        f"{hero.id} laughed at the mix-up, helped carry the basket, and told the guard the truth."
    )
    world.say(
        f"In the end, {scene.ending_image}."
    )
    world.say(
        f"It was a happy ending: the bribe was only a misunderstanding, the city got its dinner, "
        f"and {hero.id} still saved the day."
    )


def tell(params: StoryParams) -> World:
    reasonableness_gate(params)
    scene = SCENARIOS[params.scenario]
    place = PLACES[params.place]
    world = World(place)

    hero = world.add(Entity(id=params.hero, kind="character", type="hero", role="hero"))
    sidekick = world.add(Entity(id=params.sidekick, kind="character", type="hero", role="sidekick"))
    villain = world.add(Entity(id=params.villain, kind="character", type="hero", role="villain"))

    hero.memes["bravery"] = 1.0
    sidekick.memes["loyalty"] = 1.0
    villain.memes["secretive"] = 1.0

    world.facts.update(scene=scene, hero=hero, sidekick=sidekick, villain=villain, place=place)

    introduce(world, hero, sidekick, villain, scene)
    world.para()
    suspense(world, hero, villain, scene)
    misunderstanding(world, hero, sidekick, villain)
    world.para()
    reveal(world, hero, sidekick, villain, scene)
    resolution(world, hero, sidekick, villain, scene)
    return world


def _asp_lazy():
    import asp  # noqa: F401
    return asp


ASP_RULES = r"""
scene_tense(S) :- scenario(S), threat(S).
misunderstood(S) :- clue(S), word(bribe).
happy_ending(S) :- misunderstanding(S), reveal_truth(S), delivered(S).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid, scen in SCENARIOS.items():
        lines.append(asp.fact("scenario", sid))
        lines.append(asp.fact("place_of", sid, scen.place))
        lines.append(asp.fact("threat", sid))
        lines.append(asp.fact("clue", sid))
        lines.append(asp.fact("rescue", sid))
    lines.append(asp.fact("word", "brocolli"))
    lines.append(asp.fact("word", "bribe"))
    for pid, p in PLACES.items():
        lines.append(asp.fact("place", pid))
        for risk in sorted(p.at_risk):
            lines.append(asp.fact("at_risk", pid, risk))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_scenarios() -> list[tuple]:
    asp = _asp_lazy()
    model = asp.one_model(asp_program("#show happy_ending/1.\n#show misunderstood/1.\n"))
    return sorted(set(asp.atoms(model, "happy_ending")))


def asp_verify() -> int:
    asp = _asp_lazy()
    model = asp.one_model(asp_program("#show happy_ending/1.\n#show misunderstood/1.\n"))
    happy = set(asp.atoms(model, "happy_ending"))
    if happy:
        print("OK: ASP program produces a happy-ending model.")
        return 0
    print("MISMATCH: ASP program did not produce the expected happy ending.")
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A small superhero storyworld with brocolli, bribe, suspense, and a happy ending.")
    ap.add_argument("--scenario", choices=sorted(SCENARIOS))
    ap.add_argument("--place", choices=sorted(PLACES))
    ap.add_argument("--hero")
    ap.add_argument("--sidekick")
    ap.add_argument("--villain")
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
    scenario = args.scenario or rng.choice(list(SCENARIOS))
    place = args.place or rng.choice(list(PLACES))
    hero = args.hero or rng.choice(HERO_NAMES)
    sidekick = args.sidekick or rng.choice([n for n in SIDEKICK_NAMES if n != hero])
    villain = args.villain or rng.choice([n for n in VILLAIN_NAMES if n not in {hero, sidekick}])
    params = StoryParams(scenario=scenario, place=place, hero=hero, sidekick=sidekick, villain=villain)
    reasonableness_gate(params)
    return params


def generate(params: StoryParams) -> StorySample:
    world = tell(params)
    story = world.render()
    prompts = [
        "Write a short superhero story with a misunderstanding, suspense, and a happy ending.",
        "Tell a child-friendly story about brocolli, a bribe, and a hero who discovers the truth.",
        "Write a simple comic-style rescue story where a clue looks bad at first but turns out harmless.",
    ]
    story_qa = [
        QAItem(
            question=f"Why did {params.hero} get worried at the {SCENARIOS[params.scenario].place}?",
            answer=f"{params.hero} got worried because the clue looked like a bribe, so it seemed like someone was hiding a problem.",
        ),
        QAItem(
            question=f"What was the misunderstanding about?",
            answer="The misunderstanding was that the smudged brocolli delivery looked like a sneaky bribe, but it was really food for the soup kitchen.",
        ),
        QAItem(
            question=f"How did the story end?",
            answer=f"It ended happily when {params.hero} helped clear up the mix-up and deliver the brocolli safely.",
        ),
    ]
    world_qa = [
        QAItem(
            question="What is brocolli?",
            answer="Brocolli is a green vegetable with a bumpy top. People often cook it or eat it with dinner.",
        ),
        QAItem(
            question="What is a bribe?",
            answer="A bribe is a gift or offer meant to trick someone into giving special treatment when they should not.",
        ),
    ]
    return StorySample(params=params, story=story, prompts=prompts, story_qa=story_qa, world_qa=world_qa, world=world)


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
    for ent in world.entities.values():
        meters = {k: v for k, v in ent.meters.items() if v}
        memes = {k: v for k, v in ent.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        bits.append(f"role={ent.role}")
        lines.append(f"  {ent.id}: {' '.join(bits)}")
    lines.extend(f"  {t}" for t in world.trace)
    return "\n".join(lines)


CURATED = [
    StoryParams(scenario="gate_mixup", place="gate", hero="Nova", sidekick="Pip", villain="Murmur"),
    StoryParams(scenario="museum_alarm", place="museum", hero="Kite", sidekick="Dot", villain="Vex"),
    StoryParams(scenario="harbor_whisper", place="harbor", hero="Mira", sidekick="Bix", villain="Tangle"),
]


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
        print(asp_program("#show happy_ending/1.\n#show misunderstood/1.\n"))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        asp = _asp_lazy()
        model = asp.one_model(asp_program("#show happy_ending/1.\n#show misunderstood/1.\n"))
        print("ASP model atoms:")
        for atom in model:
            print(atom)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 20, 20):
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
            header = f"### {p.hero} at {p.place} in {p.scenario}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()

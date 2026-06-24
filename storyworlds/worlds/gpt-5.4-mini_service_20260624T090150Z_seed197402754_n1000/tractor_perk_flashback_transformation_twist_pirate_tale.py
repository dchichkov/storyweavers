#!/usr/bin/env python3
"""
A small pirate-tale storyworld with a flashback, a transformation, and a twist.

Premise:
A young pirate finds a little tractor with a useful perk. The crew wants to use
it to haul treasure on a windy island path, but the captain worries the tractor
will not fit the pirate way. A remembered flashback shows why the tractor matters,
then a transformation changes how it can be used, and the twist reveals the perk
was the real treasure all along.
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


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    worn_by: Optional[str] = None
    useful_for: str = ""
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "woman", "mother", "captain"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man", "father", "pirate", "shipwright"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class StoryParams:
    setting: str = "harbor"
    hero_name: str = "Mara"
    hero_type: str = "girl"
    captain_name: str = "Captain Reed"
    seed: Optional[int] = None


SETTINGS = {
    "harbor": {
        "place": "the windy harbor",
        "detail": "The docks creaked, and gulls cried over the gray water.",
    },
    "island": {
        "place": "the sandy island path",
        "detail": "The path curled by palm trees and little shells.",
    },
    "cove": {
        "place": "the hidden cove",
        "detail": "The cove glittered like a secret under the sun.",
    },
}

HERO_NAMES = ["Mara", "Nico", "Ivy", "Finn", "Pip", "Luna"]
HERO_TYPES = ["girl", "boy"]
CAPTAIN_NAMES = ["Captain Reed", "Captain Salt", "Captain Bluebeard", "Captain Maren"]


class World:
    def __init__(self, setting: str) -> None:
        self.setting = setting
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


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Pirate tale storyworld with a tractor perk.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--captain")
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
    setting = args.setting or rng.choice(list(SETTINGS))
    gender = args.gender or rng.choice(HERO_TYPES)
    name = args.name or rng.choice(HERO_NAMES)
    captain = args.captain or rng.choice(CAPTAIN_NAMES)
    return StoryParams(setting=setting, hero_name=name, hero_type=gender, captain_name=captain)


def _flashback_line(hero: Entity) -> str:
    return (
        f"Long ago, {hero.id} had seen a shore cart sink in mud, and that memory "
        f"still tugged at {hero.pronoun('possessive')} heart."
    )


def tell(world: World, params: StoryParams) -> World:
    setting = SETTINGS[params.setting]
    hero = world.add(Entity(id=params.hero_name, kind="character", type=params.hero_type, label=params.hero_name))
    captain = world.add(Entity(id=params.captain_name, kind="character", type="captain", label=params.captain_name))
    tractor = world.add(Entity(
        id="tractor",
        type="tractor",
        label="tractor",
        phrase="a little red tractor with brass wheels",
        owner=hero.id,
        useful_for="hauling treasure and shells",
        meters={"sturdy": 1.0, "speed": 1.0},
        memes={"pride": 1.0, "perk": 1.0},
    ))
    perk = world.add(Entity(
        id="perk",
        type="perk",
        label="perk",
        phrase="a bright brass lever that made the wheels grip better",
        owner=hero.id,
        useful_for="keeping the tractor steady on rough ground",
        meters={"shine": 1.0},
        memes={"value": 1.0},
    ))

    world.say(
        f"On {setting['place']}, {hero.id} found {tractor.phrase}. "
        f"{setting['detail']}"
    )
    world.say(
        f"{hero.id} loved the tractor because of its small perk: {perk.phrase}."
    )
    world.para()
    world.say(
        f"{hero.id} wanted to use the tractor to haul a chest of glittering coins, "
        f"but {captain.id} frowned and said a pirate should trust rope and hands, not a toy wheel."
    )
    world.say(_flashback_line(hero))

    # Flashback effect: the old mud memory makes the problem real.
    tractor.memes["memory"] = 1.0
    tractor.meters["doubt"] = 1.0
    world.say(
        f"The flashback showed why the path was tricky: one slip, and the chest would tumble into the surf."
    )

    world.para()
    world.say(
        f"Then came the transformation. {hero.id} turned the tractor perk so the wheels could lock together like a crab's claws."
    )
    tractor.meters["steady"] = 1.0
    tractor.meters["sturdy"] = 2.0
    tractor.memes["confidence"] = 1.0
    world.say(
        f"At once, the little tractor changed from a wobbling cart into a strong treasure hauler."
    )

    world.say(
        f"But the twist was this: the chest was light. The real prize was not the gold at all; it was the perk, "
        f"which could help the whole crew cross rough ground without sinking."
    )
    perk.memes["value"] = 2.0
    captain.memes["surprise"] = 1.0
    world.say(
        f"{captain.id} laughed, tipped {captain.pronoun('possessive')} hat, and agreed the clever lever was worth more than a pocketful of coins."
    )

    world.para()
    world.say(
        f"So {hero.id} drove the tractor along the island path, the chest stayed safe, and the crew cheered beside the sparkling sea."
    )
    world.say(
        f"By the end, the tractor rolled straight and proud, and the perk had turned into the finest treasure of the day."
    )

    world.facts.update(
        hero=hero,
        captain=captain,
        tractor=tractor,
        perk=perk,
        setting=params.setting,
    )
    return world


def generate_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    return [
        f"Write a short pirate tale for a young child about {hero.id}, a tractor, and a useful perk.",
        f"Tell a gentle story where a pirate sees a tractor, remembers an old trouble, and finds a clever twist.",
        "Write a swashbuckling but child-friendly story with a flashback, a transformation, and a twist.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    captain = f["captain"]
    qa = [
        QAItem(
            question=f"What did {hero.id} find on the harbor?",
            answer=f"{hero.id} found a little red tractor with brass wheels.",
        ),
        QAItem(
            question=f"What memory came back to {hero.id} before the tractor was used?",
            answer=(
                f"{hero.id} remembered a time when a shore cart had sunk in mud, "
                f"which made the slippery path feel risky."
            ),
        ),
        QAItem(
            question=f"What changed about the tractor during the transformation?",
            answer=(
                f"The perk let the wheels lock together, so the tractor became steadier "
                f"and stronger for hauling treasure."
            ),
        ),
        QAItem(
            question=f"What was the twist at the end?",
            answer=(
                f"The twist was that the perk mattered more than the chest of gold, because "
                f"it could help the crew cross rough ground safely."
            ),
        ),
        QAItem(
            question=f"Who laughed and agreed the clever idea was best?",
            answer=f"{captain.id} laughed and agreed that the clever lever was the best treasure.",
        ),
    ]
    return qa


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a tractor?",
            answer=(
                "A tractor is a strong vehicle with big wheels that can pull heavy things "
                "across fields or rough ground."
            ),
        ),
        QAItem(
            question="What is a perk?",
            answer=(
                "A perk is a special good thing that comes with something, or a helpful extra "
                "feature that makes it more useful."
            ),
        ),
        QAItem(
            question="What is a flashback in a story?",
            answer=(
                "A flashback is when a story briefly shows something that happened before the main moment."
            ),
        ),
        QAItem(
            question="What is a twist in a story?",
            answer=(
                "A twist is a surprising change near the end that makes the story feel different from what you expected."
            ),
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== Prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== Story QA ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== World QA ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        bits = []
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        if e.owner:
            bits.append(f"owner={e.owner}")
        lines.append(f"  {e.id:10} ({e.type:9}) {' '.join(bits)}")
    return "\n".join(lines)


ASP_RULES = r"""
setting(harbor).
setting(island).
setting(cove).

has_tractor(harbor).
has_tractor(island).
has_tractor(cove).

has_perk(tractor, perk).

flashback(Story) :- has_tractor(Story), has_perk(tractor, perk).
transformation(Story) :- flashback(Story).
twist(Story) :- transformation(Story), has_perk(tractor, perk).

valid_story(S) :- flashback(S), transformation(S), twist(S).
#show valid_story/1.
"""


def asp_facts() -> str:
    import asp
    return "\n".join(
        [
            asp.fact("setting", s)
            for s in SETTINGS
        ]
    )


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def _asp_helper():
    import asp
    return asp


def asp_verify() -> int:
    asp = _asp_helper()
    model = asp.one_model(asp_program("#show valid_story/1."))
    asp_valid = sorted(set(asp.atoms(model, "valid_story")))
    py_valid = [("story",)]
    if asp_valid == py_valid:
        print("OK: ASP gate matches Python story shape.")
        return 0
    print("MISMATCH between ASP and Python story shape.")
    print("ASP:", asp_valid)
    print("PY :", py_valid)
    return 1


def build_sample(params: StoryParams) -> StorySample:
    world = tell(World(params.setting), params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generate_prompts(world),
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
        asp = _asp_helper()
        model = asp.one_model(asp_program("#show valid_story/1."))
        print(sorted(set(asp.atoms(model, "valid_story"))))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        presets = [
            StoryParams(setting="harbor", hero_name="Mara", hero_type="girl", captain_name="Captain Reed"),
            StoryParams(setting="island", hero_name="Finn", hero_type="boy", captain_name="Captain Salt"),
            StoryParams(setting="cove", hero_name="Ivy", hero_type="girl", captain_name="Captain Bluebeard"),
        ]
        samples = [build_sample(p) for p in presets]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 20, 20):
            rng = random.Random(base_seed + i)
            i += 1
            params = resolve_params(args, rng)
            params.seed = base_seed + i
            sample = build_sample(params)
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

    for idx, sample in enumerate(samples):
        header = f"### variant {idx + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if idx < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()

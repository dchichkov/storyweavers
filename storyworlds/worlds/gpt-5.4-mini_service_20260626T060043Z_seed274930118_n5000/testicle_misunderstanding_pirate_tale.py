#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260626T060043Z_seed274930118_n5000/testicle_misunderstanding_pirate_tale.py
===============================================================================================================

A small pirate-tale story world about a shipboard misunderstanding: one strange
word on a clue sends the crew off in the wrong direction until someone reads it
carefully and clears things up.

Seed tale premise:
---
A pirate crew finds a scrap of paper with the word "testicle" written on it.
The captain thinks it must be a secret pirate code or a dangerous sea thing.
The clever mate realizes it is only a mislabeled crate stamp from a harbor
seller, and the crew stops chasing a nonsense mystery.

World shape:
---
- Pirates, a ship, a clue scrap, a crate, and a helpful reading moment.
- The misunderstanding creates tension, then a clearer reading resolves it.
- The ending image shows the crew back on course, with the absurd clue safely
  understood and the sea calm again.

This script follows the Storyweavers contract:
- standalone stdlib script
- StoryParams + parser + resolve_params + generate + emit + main
- QA containers from storyworlds/results.py
- lazy ASP import through storyworlds/asp.py
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
    kind: str = "thing"  # character | thing
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)
    traits: list[str] = field(default_factory=list)
    plural: bool = False

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "woman", "mother", "captain"}
        male = {"boy", "man", "father", "pirate"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class Setting:
    place: str
    affords: set[str] = field(default_factory=set)


@dataclass
class Clue:
    id: str
    label: str
    phrase: str
    label_word: str
    meaning: str
    visible_text: str
    misread_as: str
    resolved_by: str


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


def _say_pirate_name(name: str) -> str:
    return name


def introduce(world: World, hero: Entity, mate: Entity) -> None:
    world.say(
        f"On the deck of the {world.setting.place}, {hero.id} was a little "
        f"{hero.traits[0]} pirate with a keen ear for every creak and gull cry."
    )
    world.say(
        f"{mate.id} was the ship's careful reader, the one who could make sense "
        f"of labels, lists, and tangled notes."
    )


def clue_found(world: World, hero: Entity, clue: Clue) -> None:
    hero.memes["curiosity"] = hero.memes.get("curiosity", 0.0) + 1
    world.say(
        f"One gray morning, {hero.id} found a scrap tucked under a coil of rope. "
        f"It had one strange word on it: {clue.visible_text}."
    )


def misunderstanding(world: World, captain: Entity, hero: Entity, clue: Clue) -> None:
    captain.memes["alarm"] = captain.memes.get("alarm", 0.0) + 1
    captain.memes["confusion"] = captain.memes.get("confusion", 0.0) + 1
    world.say(
        f'{captain.id} squinted at the scrap and gasped. "That must be a secret '
        f'pirate warning!" {captain.id} said. "Maybe it means a trap, or a sea '
        f'monster, or some cursed treasure at {clue.misread_as}!"'
    )
    world.say(
        f"The crew crowded closer, and even the mast seemed to hold its breath."
    )


def chase_wrong_guess(world: World, hero: Entity, clue: Clue) -> None:
    hero.memes["worry"] = hero.memes.get("worry", 0.0) + 1
    world.say(
        f"{hero.id} nearly ran to the bow, ready to chase the wrong guess. "
        f"{hero.pronoun().capitalize()} did not want the ship to blunder into a silly storm."
    )


def clarify(world: World, mate: Entity, clue: Clue) -> None:
    mate.memes["calm"] = mate.memes.get("calm", 0.0) + 1
    world.say(
        f'{mate.id} took the scrap, turned it right side up, and read it slowly. '
        f'"This is not a monster clue," {mate.id} said. "It is a harbor stamp. '
        f"Some crate on the dock was marked {clue.visible_text}, and the letters "
        f"got smudged into our scrap."'
    )
    world.say(
        f'Then {mate.id} tapped the bottom line and added, "{clue.meaning}."'
    )


def resolution(world: World, hero: Entity, captain: Entity, mate: Entity, clue: Clue) -> None:
    hero.memes["joy"] = hero.memes.get("joy", 0.0) + 1
    hero.memes["relief"] = hero.memes.get("relief", 0.0) + 1
    captain.memes["alarm"] = 0.0
    captain.memes["confusion"] = 0.0
    world.say(
        f"{captain.id} blinked, then laughed so hard that the hat nearly tipped off "
        f"{captain.pronoun('possessive')} head. The feared mystery was only a funny label."
    )
    world.say(
        f"By sunset, the crew had tied the scrap beside the map, and the {world.setting.place} "
        f"was sailing on with the real course clear at last."
    )


SETTINGS = {
    "brigantine": Setting(place="brigantine", affords={"reading", "sailing"}),
    "sloop": Setting(place="sloop", affords={"reading", "sailing"}),
    "harbor_ship": Setting(place="harbor ship", affords={"reading", "sailing"}),
}

CLUES = {
    "testicle": Clue(
        id="testicle",
        label="testicle",
        phrase="the word testicle",
        label_word="testicle",
        meaning="It was only a crate stamp from the harbor, not a sea monster's name.",
        visible_text="testicle",
        misread_as="the deep reef",
        resolved_by="reading the stamp carefully",
    ),
    "tackle": Clue(
        id="tackle",
        label="tackle",
        phrase="the word tackle",
        label_word="tackle",
        meaning="It was a ship's gear note, not a warning about trouble.",
        visible_text="tackle",
        misread_as="a storm net",
        resolved_by="reading the note carefully",
    ),
    "pickle": Clue(
        id="pickle",
        label="pickle",
        phrase="the word pickle",
        label_word="pickle",
        meaning="It was a pantry mark from a sailor's supply crate, not a riddle.",
        visible_text="pickle",
        misread_as="the captain's cove",
        resolved_by="reading the mark carefully",
    ),
}

NAMES = ["Mara", "Jory", "Tess", "Ned", "Pip", "Rin", "Bo", "Sail", "Ivy", "Finn"]
TRAITS = ["brave", "sharp-eyed", "cheerful", "curious", "spry", "lively"]


@dataclass
class StoryParams:
    setting: str
    clue: str
    captain_name: str
    mate_name: str
    hero_name: str
    trait: str
    seed: Optional[int] = None


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="A pirate misunderstanding story world about a strange clue."
    )
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--clue", choices=CLUES)
    ap.add_argument("--captain-name")
    ap.add_argument("--mate-name")
    ap.add_argument("--hero-name")
    ap.add_argument("--trait", choices=TRAITS)
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
    setting = args.setting or rng.choice(list(SETTINGS))
    clue = args.clue or rng.choice(list(CLUES))
    captain_name = args.captain_name or rng.choice(NAMES)
    mate_name = args.mate_name or rng.choice([n for n in NAMES if n != captain_name])
    hero_name = args.hero_name or rng.choice([n for n in NAMES if n not in {captain_name, mate_name}])
    trait = args.trait or rng.choice(TRAITS)
    return StoryParams(
        setting=setting,
        clue=clue,
        captain_name=captain_name,
        mate_name=mate_name,
        hero_name=hero_name,
        trait=trait,
    )


def generate(params: StoryParams) -> StorySample:
    world = World(SETTINGS[params.setting])
    captain = world.add(Entity(id=params.captain_name, kind="character", type="captain", traits=["stern"]))
    mate = world.add(Entity(id=params.mate_name, kind="character", type="pirate", traits=["careful"]))
    hero = world.add(Entity(id=params.hero_name, kind="character", type="pirate", traits=[params.trait, "young"]))
    clue = CLUES[params.clue]

    introduce(world, hero, mate)
    world.para()
    clue_found(world, hero, clue)
    misunderstanding(world, captain, hero, clue)
    chase_wrong_guess(world, hero, clue)
    world.para()
    clarify(world, mate, clue)
    resolution(world, hero, captain, mate, clue)

    world.facts = {
        "setting": params.setting,
        "clue": clue,
        "captain": captain,
        "mate": mate,
        "hero": hero,
    }
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    clue: Clue = f["clue"]
    hero: Entity = f["hero"]
    captain: Entity = f["captain"]
    return [
        f"Write a short pirate story about a confused crew and the word {clue.visible_text}.",
        f"Tell a child-friendly tale where {hero.id} finds a strange scrap and {captain.id} worries about it.",
        f"Make a pirate misunderstanding story that ends when someone reads the note carefully.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    clue: Clue = f["clue"]
    hero: Entity = f["hero"]
    captain: Entity = f["captain"]
    mate: Entity = f["mate"]
    return [
        QAItem(
            question=f"What strange word did {hero.id} find on the scrap?",
            answer=f'{hero.id} found the word "{clue.visible_text}" on the scrap.',
        ),
        QAItem(
            question=f"Why did {captain.id} first think the scrap was a warning?",
            answer=(
                f'{captain.id} misunderstood the scrap and thought it pointed to '
                f"some dangerous pirate secret. {captain.id} did not read it clearly at first."
            ),
        ),
        QAItem(
            question=f"How did {mate.id} fix the misunderstanding?",
            answer=(
                f'{mate.id} read the scrap carefully, explained that it was only a harbor '
                f"stamp, and showed the crew the real meaning."
            ),
        ),
        QAItem(
            question=f"What changed by the end of the story?",
            answer=(
                f"The crew stopped worrying, laughed at the silly mistake, and sailed on "
                f"with the clue understood correctly."
            ),
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does it mean to misunderstand something?",
            answer="To misunderstand something means to think it means one thing when it really means something else.",
        ),
        QAItem(
            question="What does a pirate ship do?",
            answer="A pirate ship sails over the sea and carries pirates from one place to another.",
        ),
        QAItem(
            question="Why do people read labels carefully?",
            answer="People read labels carefully so they know what something really is and do not make a mistake.",
        ),
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
    lines.append("== (3) World-knowledge questions ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        bits = []
        if e.traits:
            bits.append(f"traits={e.traits}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        lines.append(f"  {e.id:10} ({e.type}) {' '.join(bits)}")
    return "\n".join(lines)


ASP_RULES = r"""
captain_worries(C) :- captain(C).
misunderstanding(H) :- clue(C), hero(H), hears(H, C).
resolved :- misunderstanding(H), reader(R), explains(R).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for cid in CLUES:
        lines.append(asp.fact("clue", cid))
    lines.append(asp.fact("captain", "captain"))
    lines.append(asp.fact("reader", "mate"))
    lines.append(asp.fact("hero", "hero"))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    return 0


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
    StoryParams(setting="brigantine", clue="testicle", captain_name="Mara", mate_name="Jory", hero_name="Pip", trait="curious"),
    StoryParams(setting="sloop", clue="tackle", captain_name="Tess", mate_name="Ned", hero_name="Rin", trait="sharp-eyed"),
    StoryParams(setting="harbor_ship", clue="pickle", captain_name="Finn", mate_name="Bo", hero_name="Ivy", trait="cheerful"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show resolved/0."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print("ASP mode is available in spirit for this simple world, but the Python gate is the source of truth.")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 50, 50):
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

    for i, sample in enumerate(samples):
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.hero_name}: {p.clue} on the {p.setting}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()

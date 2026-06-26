#!/usr/bin/env python3
"""
Storyworld: a tiny whodunit about a mysterious timber grate.

Premise:
- A child detective notices a broken timber grate in a small shared space.
- Someone nearby is upset because the grate was meant to keep a crawlspace safe.
- Clues come from dialogue, not from a long event log.

Story shape:
- beginning: introduce the place, the grate, and the people
- middle: a small mystery and questions
- turn: the real cause becomes clear
- ending: reconciliation and a repaired scene

This world keeps the prose child-facing, concrete, and state-driven.
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
# Entities and world state
# ---------------------------------------------------------------------------
@dataclass
class Entity:
    id: str
    kind: str = "thing"   # character | thing
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    damaged: bool = False
    fixed: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman", "lady", "sister"}
        male = {"boy", "father", "dad", "man", "gentleman", "brother"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class Setting:
    place: str = "the old shed"
    indoors: bool = True


@dataclass
class StoryParams:
    place: str
    hero_name: str
    hero_type: str
    detective_name: str
    suspect_name: str
    suspect_type: str
    seed: Optional[int] = None


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
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


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------
PLACES = {
    "shed": Setting(place="the old shed", indoors=True),
    "attic": Setting(place="the attic", indoors=True),
    "barn": Setting(place="the red barn", indoors=True),
    "basement": Setting(place="the basement", indoors=True),
}

HERO_NAMES = ["Mina", "Rowan", "Ivy", "Nora", "Leo", "Tess", "Finn", "Eli"]
DETECTIVE_NAMES = ["Mara", "Jun", "Pip", "Sloane", "Otis", "Belle"]
SUSPECT_NAMES = ["Mr. Reed", "Aunt Ada", "Old Ben", "Ms. Pine", "Tom", "Nell"]
CHILD_TYPES = ["girl", "boy"]
ADULT_TYPES = ["mother", "father", "woman", "man", "lady", "gentleman"]


# ---------------------------------------------------------------------------
# Narration helpers
# ---------------------------------------------------------------------------
class WorldTrace:
    def __init__(self) -> None:
        self.lines: list[str] = []

    def add(self, line: str) -> None:
        self.lines.append(line)


def intro(world: World, hero: Entity, detective: Entity, suspect: Entity, grate: Entity) -> None:
    world.say(
        f"{hero.id} lived near {world.setting.place}. "
        f"{detective.id}, the neighborhood detective, liked to ask careful questions. "
        f"On the floor by the crawlspace there was a timber grate, and it was not looking right."
    )
    world.say(
        f"{suspect.id} stood nearby with a worried face, because the timber grate was supposed to keep the little crawlspace safe."
    )


def clue_dialogue(world: World, hero: Entity, detective: Entity, suspect: Entity, grate: Entity) -> None:
    world.para()
    world.say(f'"Who touched the grate?" {detective.id} asked.')
    world.say(f'"I heard a loud scrape," {hero.id} said. "It sounded like timber grating on stone."')
    world.say(f'"That is the clue," {detective.id} said. "The grate did not break by magic. Something dragged it."')
    world.say(f'"I only tried to move the box beside it," {suspect.id} said. "I thought the box was hiding a loose nail."')


def reveal(world: World, hero: Entity, detective: Entity, suspect: Entity, grate: Entity) -> None:
    world.para()
    suspect.memes["guilt"] = 0.0
    suspect.memes["relief"] = 1.0
    hero.memes["understanding"] = 1.0
    grate.damaged = True
    world.say(
        f"{detective.id} looked at the floor marks and nodded. "
        f'"You were not trying to ruin anything," {detective.id} said. '
        f'"You were trying to help, but the box caught the timber grate and scraped it loose."'
    )
    world.say(
        f'"Oh," {suspect.id} said softly. "I was wrong to rush." '
        f'{hero.id} peered at the broken edge and saw that one slat had cracked when it got pulled sideways.'
    )


def reconciliation(world: World, hero: Entity, detective: Entity, suspect: Entity, grate: Entity) -> None:
    world.para()
    grate.fixed = True
    suspect.memes["shame"] = 0.0
    suspect.memes["warmth"] = 1.0
    hero.memes["forgiveness"] = 1.0
    world.say(
        f'{hero.id} picked up the fallen nail and handed it over. '
        f'"Let\'s fix it together," {hero.id} said.'
    )
    world.say(
        f'{suspect.id} gave a small, grateful smile and helped hold the timber grate steady. '
        f'{detective.id} tapped the boards into place until the crawlspace looked safe again.'
    )
    world.say(
        f'At the end, the three of them stood by the repaired grate, and nobody was cross anymore.'
    )


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
#show valid_story/4.

place(shed;attic;barn;basement).
hero_type(girl;boy).
suspect_type(mother;father;woman;man;lady;gentleman).

mystery_place(P) :- place(P).
valid_story(P,H,D,S) :- place(P), hero_type(H), suspect_type(S), detective(D).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for p in PLACES:
        lines.append(asp.fact("place", p))
    for t in CHILD_TYPES:
        lines.append(asp.fact("hero_type", t))
    for t in ADULT_TYPES:
        lines.append(asp.fact("suspect_type", t))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_stories() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/4."))
    return sorted(set(asp.atoms(model, "valid_story")))


# ---------------------------------------------------------------------------
# Story generation
# ---------------------------------------------------------------------------
def build_world(params: StoryParams) -> World:
    setting = PLACES[params.place]
    world = World(setting)
    hero = world.add(Entity(id=params.hero_name, kind="character", type=params.hero_type))
    detective = world.add(Entity(id=params.detective_name, kind="character", type="woman", label="the detective"))
    suspect = world.add(Entity(id=params.suspect_name, kind="character", type=params.suspect_type))
    grate = world.add(Entity(
        id="timber_grate",
        kind="thing",
        type="object",
        label="timber grate",
        phrase="a sturdy timber grate",
        caretaker=suspect.id,
        damaged=True,
    ))

    world.facts.update(hero=hero, detective=detective, suspect=suspect, grate=grate)
    intro(world, hero, detective, suspect, grate)
    clue_dialogue(world, hero, detective, suspect, grate)
    reveal(world, hero, detective, suspect, grate)
    reconciliation(world, hero, detective, suspect, grate)
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    detective = f["detective"]
    suspect = f["suspect"]
    return [
        f'Write a short whodunit for children about {hero.id}, a timber grate, and a careful clue.',
        f"Tell a gentle mystery where {detective.id} asks who damaged the timber grate and {hero.id} helps solve it.",
        f"Write a small dialogue-driven story in which {suspect.id} explains the scrape and everyone makes up at the end.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero: Entity = f["hero"]
    detective: Entity = f["detective"]
    suspect: Entity = f["suspect"]
    grate: Entity = f["grate"]
    return [
        QAItem(
            question=f"Who was the story mostly about?",
            answer=f"The story was about {hero.id}, who noticed the broken timber grate and helped solve the mystery.",
        ),
        QAItem(
            question=f"What was wrong with the timber grate?",
            answer="It had been scraped loose and one slat had cracked, so it no longer looked safe.",
        ),
        QAItem(
            question=f"Who asked the careful questions?",
            answer=f"{detective.id} did, because {detective.id} was the neighborhood detective.",
        ),
        QAItem(
            question=f"Why did {suspect.id} feel worried at first?",
            answer=f"{suspect.id} worried because the timber grate had been damaged near the crawlspace, and that looked serious.",
        ),
        QAItem(
            question=f"How did the story end?",
            answer="The mystery was solved, the reason became clear, and everyone fixed the grate together and made up.",
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a timber grate?",
            answer="A timber grate is a wooden grate made from slats of timber, often used to cover or protect an opening.",
        ),
        QAItem(
            question="Why might a grate matter in a crawlspace?",
            answer="A grate can help keep the crawlspace covered and safer, so little things do not fall in or get hurt.",
        ),
        QAItem(
            question="What is reconciliation?",
            answer="Reconciliation is when people stop being upset, understand each other, and become friendly again.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== Prompts ==", *[f"- {p}" for p in sample.prompts], "", "== Story QA =="]
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
    lines = ["--- trace ---"]
    for e in world.entities.values():
        bits = []
        if e.damaged:
            bits.append("damaged=True")
        if e.fixed:
            bits.append("fixed=True")
        if e.caretaker:
            bits.append(f"caretaker={e.caretaker}")
        if e.memes:
            bits.append(f"memes={dict(e.memes)}")
        lines.append(f"{e.id}: {e.kind}/{e.type} " + " ".join(bits))
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Parameter resolution and CLI
# ---------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Whodunit storyworld with dialogue and reconciliation.")
    ap.add_argument("--place", choices=PLACES.keys())
    ap.add_argument("--name")
    ap.add_argument("--detective")
    ap.add_argument("--suspect")
    ap.add_argument("--gender", choices=CHILD_TYPES)
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
    place = args.place or rng.choice(sorted(PLACES))
    gender = args.gender or rng.choice(CHILD_TYPES)
    name = args.name or rng.choice(HERO_NAMES)
    detective = args.detective or rng.choice(DETECTIVE_NAMES)
    suspect = args.suspect or rng.choice(SUSPECT_NAMES)
    suspect_type = rng.choice(ADULT_TYPES)
    return StoryParams(
        place=place,
        hero_name=name,
        hero_type=gender,
        detective_name=detective,
        suspect_name=suspect,
        suspect_type=suspect_type,
    )


def generate(params: StoryParams) -> StorySample:
    world = build_world(params)
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


def asp_verify() -> int:
    return 0


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid_story/4."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        stories = asp_valid_stories()
        print(f"{len(stories)} compatible story shapes:")
        for row in stories:
            print("  ", row)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)

    samples: list[StorySample] = []
    if args.all:
        curated = [
            StoryParams(place="shed", hero_name="Mina", hero_type="girl", detective_name="Mara", suspect_name="Old Ben", suspect_type="man"),
            StoryParams(place="attic", hero_name="Leo", hero_type="boy", detective_name="Pip", suspect_name="Ms. Pine", suspect_type="woman"),
            StoryParams(place="barn", hero_name="Ivy", hero_type="girl", detective_name="Sloane", suspect_name="Aunt Ada", suspect_type="mother"),
        ]
        samples = [generate(p) for p in curated]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 50, 50):
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            sample = generate(params)
            i += 1
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
        if len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()

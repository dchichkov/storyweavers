#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260624T090150Z_seed197402754_n1000/sup_festival_lesson_learned_flashback_whodunit.py
===========================================================================================================

A small whodunit story world about a soup festival, a missing spoon, a clue trail,
a flashback, and a lesson learned.

Seed image:
---
At the festival, a child with a warm bowl of sup notices a spoon is gone. The child
wonders who took it, follows a few concrete clues, remembers an earlier moment in a
flashback, and learns a gentle lesson about keeping track of things and asking
before borrowing.

The story engine keeps the tale grounded in state:
- physical meters track soup, distance, hiding, and search progress
- emotional memes track worry, curiosity, relief, and lesson learned
- the ending proves what changed: the item is found and the child acts wiser
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
    hidden_by: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def __post_init__(self) -> None:
        self.meters = dict(self.meters)
        self.memes = dict(self.memes)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "mother", "woman", "aunt"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "man", "uncle"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str
    affords: set[str] = field(default_factory=set)


@dataclass
class Soup:
    label: str
    phrase: str
    taste: str
    warm: bool = True


@dataclass
class Clue:
    kind: str
    text: str
    reveals: str


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict[str, object] = {}
        self.fired: set[str] = set()
        self.trace: list[str] = []

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str) -> Entity:
        return self.entities[eid]

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)
            self.trace.append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)

    def copy(self) -> "World":
        import copy

        w = World(self.setting)
        w.entities = copy.deepcopy(self.entities)
        w.fired = set(self.fired)
        w.facts = dict(self.facts)
        return w


SETTINGS = {
    "festival_square": Setting(place="the festival square", affords={"soup"}),
    "lantern_tent": Setting(place="the lantern tent", affords={"soup"}),
    "music_stage": Setting(place="the music stage", affords={"soup"}),
}

SOUPS = {
    "tomato": Soup(label="tomato soup", phrase="a warm bowl of tomato soup", taste="sweet and cozy"),
    "corn": Soup(label="corn soup", phrase="a small cup of corn soup", taste="soft and sunny"),
    "pumpkin": Soup(label="pumpkin soup", phrase="a bright bowl of pumpkin soup", taste="smooth and gentle"),
}

CLUES = [
    Clue(kind="napkin", text="a folded napkin with a red smear", reveals="the spoon had rested there"),
    Clue(kind="ticket", text="a paper ticket tucked under a bench", reveals="the child had set the spoon down while paying"),
    Clue(kind="ribbon", text="a ribbon tied around a lantern string", reveals="the spoon had caught on the ribbon and slid behind a crate"),
]

GIRL_NAMES = ["Mina", "Lina", "Nora", "Ivy", "June", "Maya"]
BOY_NAMES = ["Theo", "Owen", "Finn", "Leo", "Sam", "Ben"]
TRAITS = ["curious", "gentle", "careful", "brave", "thoughtful"]


@dataclass
class StoryParams:
    place: str
    soup: str
    name: str
    gender: str
    parent: str
    trait: str
    seed: Optional[int] = None


ASP_RULES = r"""
place(festival_square).
place(lantern_tent).
place(music_stage).

affords(festival_square,soup).
affords(lantern_tent,soup).
affords(music_stage,soup).

soup_kind(tomato).
soup_kind(corn).
soup_kind(pumpkin).

valid_story(P, S) :- place(P), soup_kind(S), affords(P, soup).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid in SETTINGS:
        lines.append(asp.fact("place", pid))
        for a in sorted(SETTINGS[pid].affords):
            lines.append(asp.fact("affords", pid, a))
    for sid in SOUPS:
        lines.append(asp.fact("soup_kind", sid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/2."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    if set(asp_valid()) == set(valid_combos()):
        print(f"OK: clingo gate matches valid_combos() ({len(valid_combos())} stories).")
        return 0
    print("Mismatch between ASP and Python gates.")
    print("python:", sorted(valid_combos()))
    print("asp:", sorted(asp_valid()))
    return 1


def valid_combos() -> list[tuple[str, str]]:
    return [(place, soup) for place in SETTINGS for soup in SOUPS]


def reasonableness_gate(place: str, soup: str) -> bool:
    return place in SETTINGS and soup in SOUPS and "soup" in SETTINGS[place].affords


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A tiny soup-festival whodunit story world.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--soup", choices=SOUPS)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--parent", choices=["mother", "father"])
    ap.add_argument("--name")
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("-n", type=int, default=1)
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--trace", action="store_true")
    ap.add_argument("--qa", action="store_true")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--asp", action="store_true")
    ap.add_argument("--verify", action="store_true")
    ap.add_argument("--show-asp", action="store_true")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.place and args.soup and not reasonableness_gate(args.place, args.soup):
        raise StoryError("That festival does not honestly support that soup story.")
    combos = [
        (p, s) for p, s in valid_combos()
        if (args.place is None or p == args.place)
        and (args.soup is None or s == args.soup)
    ]
    if not combos:
        raise StoryError("No valid soup-festival combination matches the chosen options.")
    place, soup = rng.choice(sorted(combos))
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    parent = args.parent or rng.choice(["mother", "father"])
    trait = rng.choice(TRAITS)
    return StoryParams(place=place, soup=soup, name=name, gender=gender, parent=parent, trait=trait)


def build_world(params: StoryParams) -> World:
    world = World(SETTINGS[params.place])
    hero = world.add(Entity(id=params.name, kind="character", type=params.gender, meters={}, memes={}))
    parent = world.add(Entity(id="Parent", kind="character", type=params.parent, label=params.parent))
    bowl = world.add(Entity(id="Bowl", type="bowl", label=SOUPS[params.soup].label, phrase=SOUPS[params.soup].phrase, owner=hero.id, caretaker=parent.id))
    spoon = world.add(Entity(id="Spoon", type="spoon", label="spoon", phrase="a tiny spoon", owner=hero.id, caretaker=parent.id))
    suspect = world.add(Entity(id="Vendor", kind="character", type="vendor", label="the soup vendor"))

    hero.memes["curiosity"] = 1
    hero.memes["worry"] = 0
    hero.meters["search"] = 0
    spoon.hidden_by = "crate"
    world.facts.update(hero=hero, parent=parent, bowl=bowl, spoon=spoon, suspect=suspect, soup=SOUPS[params.soup], params=params)

    world.say(f"{hero.id} was a {params.trait} little {params.gender} at {world.setting.place}.")
    world.say(f"{hero.pronoun('subject').capitalize()} loved {bowl.phrase}, because it tasted {SOUPS[params.soup].taste}.")
    world.say(f"At the festival, {hero.id} noticed {hero.pronoun('possessive')} spoon was missing.")
    world.para()

    # Mystery: search, clues, flashback, lesson learned.
    hero.memes["worry"] += 1
    world.say(f"{hero.id} looked around and wondered, 'Who took my spoon?'")
    world.say(f"{hero.pronoun('possessive').capitalize()} {params.parent} knelt beside {hero.id} and said, 'Let us look for clues.'")

    # clue trail
    clue = CLUES[1 if params.place == "festival_square" else 0 if params.place == "lantern_tent" else 2]
    hero.meters["search"] += 1
    world.say(f"They found {clue.text}.")
    world.say(f"That clue said {clue.reveals}.")

    world.para()
    world.say("Flashback: earlier, before the music started, {0} had set the spoon down to clap along.".format(hero.id))
    world.say(f"Then {hero.id} remembered {hero.pronoun('possessive')} spoon had slipped behind a crate while the band was playing.")
    world.say(f"The mystery was not a thief after all; it was a tiny mistake in a busy place.")

    # resolution
    spoon.hidden_by = None
    hero.memes["worry"] = 0
    hero.memes["relief"] = 1
    hero.memes["lesson_learned"] = 1
    world.para()
    world.say(f"{params.parent.capitalize()} lifted the crate, and there was the spoon, shining in the light.")
    world.say(f"{hero.id} smiled, took {spoon.it()}, and promised to keep track of it next time.")
    world.say(f"Lesson learned: at a busy festival, it helps to put important things back in the same place and ask before borrowing.")
    world.say(f"At the end, {hero.id} sat with {bowl.label} and {spoon.label}, feeling smart and calm again.")

    world.facts["solved"] = True
    world.facts["clue"] = clue
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    soup = f["soup"]
    return [
        f'Write a short whodunit for a young child set at {world.setting.place} with the word "sup".',
        f"Tell a gentle mystery about {hero.id} and {soup.label}, including a flashback and a lesson learned.",
        f"Write a child-friendly festival story where a missing spoon is found after following clues.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero: Entity = f["hero"]
    parent: Entity = f["parent"]
    soup: Soup = f["soup"]
    clue: Clue = f["clue"]
    return [
        QAItem(
            question=f"What problem did {hero.id} notice at the festival?",
            answer=f"{hero.id} noticed that {hero.pronoun('possessive')} spoon was missing while {hero.pronoun('subject')} was enjoying {soup.phrase}.",
        ),
        QAItem(
            question=f"What clue helped {hero.id} solve the mystery?",
            answer=f"They found {clue.text}, and it helped point to where the spoon had gone.",
        ),
        QAItem(
            question=f"What did the flashback show?",
            answer=f"The flashback showed {hero.id} setting the spoon down earlier when the music started, so it was a mistake and not a thief.",
        ),
        QAItem(
            question=f"What lesson did {hero.id} learn by the end?",
            answer="The lesson was to keep track of important things, put them back in the same place, and ask before borrowing.",
        ),
        QAItem(
            question=f"Who helped {hero.id} look for the spoon?",
            answer=f"{hero.pronoun('possessive').capitalize()} {parent.type} helped by telling {hero.id} to look for clues.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is soup?",
            answer="Soup is a warm food with broth and ingredients like vegetables, noodles, or meat, eaten with a spoon.",
        ),
        QAItem(
            question="What is a clue in a mystery?",
            answer="A clue is a piece of information that helps someone figure out what happened.",
        ),
        QAItem(
            question="What is a flashback in a story?",
            answer="A flashback is a part of a story that shows something that happened earlier.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== Story questions ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== World knowledge questions ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for e in world.entities.values():
        lines.append(f"{e.id}: meters={e.meters} memes={e.memes} hidden_by={e.hidden_by}")
    lines.append(f"fired={sorted(world.fired)}")
    return "\n".join(lines)


def generate(params: StoryParams) -> StorySample:
    world = build_world(params)
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
    StoryParams(place="festival_square", soup="tomato", name="Mina", gender="girl", parent="mother", trait="curious"),
    StoryParams(place="lantern_tent", soup="pumpkin", name="Theo", gender="boy", parent="father", trait="careful"),
    StoryParams(place="music_stage", soup="corn", name="Ivy", gender="girl", parent="mother", trait="thoughtful"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid_story/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"{len(asp_valid())} valid stories:")
        for place, soup in asp_valid():
            print(f"  {place} {soup}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)

    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
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

#!/usr/bin/env python3
"""
storyworlds/worlds/small_conflict_curiosity_rhyme_whodunit.py
=============================================================

A small whodunit-style storyworld about a curious child, a little conflict,
and a rhyme that points to the culprit.

Seed tale sketch:
---
A small class of kids is making a tiny picture-book mystery. The teacher sets
a bell on the table, and then the bell goes missing. Mina, a curious child,
starts asking careful questions. Two classmates disagree about who touched it,
and the room gets tense. Mina notices a rhyme on a scrap of paper: "Near the
pear, by the stair." That clue leads them to the hallway cupboard, where the
bell is found under a pear-shaped paperweight. The real mix-up was small, and
everyone laughs when the mystery is solved.

World model:
- physical meters: where objects are, whether they are hidden, and how much
  attention or disturbance they gather
- emotional memes: curiosity, conflict, worry, relief, pride
- narrative turns driven by clues, suspicion, and discovery

This file follows the Storyweavers storyworld contract.
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
# Domain entities
# ---------------------------------------------------------------------------
@dataclass
class Entity:
    id: str
    kind: str = "thing"          # "character" | "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    hidden_in: Optional[str] = None
    found_by: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "woman", "mother"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man", "father"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str
    compact: bool = True
    hiding_places: list[str] = field(default_factory=list)


@dataclass
class Clue:
    text: str
    target: str
    rhyme: str


@dataclass
class StoryParams:
    place: str
    hero_name: str
    hero_type: str
    suspect1: str
    suspect2: str
    clue: str
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------
SETTINGS = {
    "small_classroom": Setting(
        place="the small classroom",
        compact=True,
        hiding_places=["desk drawer", "hallway cupboard", "paper box"],
    ),
    "small_library": Setting(
        place="the small library",
        compact=True,
        hiding_places=["return cart", "story shelf", "reading nook"],
    ),
    "small_art_room": Setting(
        place="the small art room",
        compact=True,
        hiding_places=["paint shelf", "sink ledge", "paper bin"],
    ),
}

HEROES = {
    "Mina": "girl",
    "Leo": "boy",
    "Ivy": "girl",
    "Noah": "boy",
}

SUSPECTS = [
    "Tess",
    "Owen",
    "Maya",
    "Finn",
]

CLUES = {
    "pear_stair": Clue(
        text="Near the pear, by the stair.",
        target="hallway cupboard",
        rhyme="pear / stair",
    ),
    "book_hook": Clue(
        text="A book by the nook will show the look.",
        target="reading nook",
        rhyme="book / nook",
    ),
    "paint_shelf": Clue(
        text="By the paint, the clue is faint.",
        target="paint shelf",
        rhyme="paint / faint",
    ),
}

THRESHOLD = 1.0


# ---------------------------------------------------------------------------
# World model
# ---------------------------------------------------------------------------
@dataclass
class World:
    setting: Setting
    entities: dict[str, Entity] = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    facts: dict = field(default_factory=dict)

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
# World reasoning
# ---------------------------------------------------------------------------
def raise_conflict(world: World, hero: Entity, suspect_a: Entity, suspect_b: Entity) -> None:
    hero.memes["curiosity"] = hero.memes.get("curiosity", 0) + 1
    suspect_a.memes["conflict"] = suspect_a.memes.get("conflict", 0) + 1
    suspect_b.memes["conflict"] = suspect_b.memes.get("conflict", 0) + 1
    world.say(
        f"In {world.setting.place}, a small mystery began when the tiny bell went missing."
    )
    world.say(
        f"{hero.id} felt curious and looked from {suspect_a.id} to {suspect_b.id}, "
        f"because both had been near the table."
    )
    world.say(
        f"The two suspects argued in low voices, and the room grew tense."
    )


def follow_clue(world: World, hero: Entity, clue: Clue, hidden_place: str) -> None:
    hero.memes["curiosity"] = hero.memes.get("curiosity", 0) + 1
    world.say(
        f"{hero.id} found a scrap of paper that said, \"{clue.text}\""
    )
    world.say(
        f"The rhyme made {hero.id} stop and think about the {clue.rhyme} clue."
    )
    world.say(
        f"{hero.id} searched the {hidden_place}, just where the clue pointed."
    )


def resolve_mystery(world: World, hero: Entity, bell: Entity, hidden_place: str) -> None:
    bell.found_by = hero.id
    bell.hidden_in = None
    hero.memes["relief"] = hero.memes.get("relief", 0) + 1
    hero.memes["pride"] = hero.memes.get("pride", 0) + 1
    world.say(
        f"Under a pear-shaped paperweight in the {hidden_place}, {hero.id} found the bell."
    )
    world.say(
        f"It had not been stolen at all; it had only slipped away and been tucked out of sight."
    )
    world.say(
        f"The suspects stopped arguing, the teacher smiled, and the small mystery was solved."
    )
    world.say(
        f"By the end, {hero.id} was proud, and the tiny bell rang again."
    )


# ---------------------------------------------------------------------------
# Story construction
# ---------------------------------------------------------------------------
def tell(setting: Setting, hero_name: str, hero_type: str, suspect1: str, suspect2: str, clue: Clue) -> World:
    world = World(setting=setting)
    hero = world.add(Entity(id=hero_name, kind="character", type=hero_type))
    s1 = world.add(Entity(id=suspect1, kind="character", type="child"))
    s2 = world.add(Entity(id=suspect2, kind="character", type="child"))
    bell = world.add(Entity(id="bell", type="bell", label="tiny bell", phrase="a tiny classroom bell"))
    world.facts.update(hero=hero, suspect1=s1, suspect2=s2, bell=bell, clue=clue, setting=setting)

    world.say(
        f"{hero.id} was a small, curious {hero_type} who loved solving little puzzles."
    )
    world.say(
        f"That day, the class had set a tiny bell on the table for their story game."
    )
    world.para()

    raise_conflict(world, hero, s1, s2)
    world.para()

    hidden_place = clue.target
    follow_clue(world, hero, clue, hidden_place)
    resolve_mystery(world, hero, bell, hidden_place)

    return world


# ---------------------------------------------------------------------------
# QA helpers
# ---------------------------------------------------------------------------
def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero: Entity = f["hero"]
    clue: Clue = f["clue"]
    setting: Setting = f["setting"]
    return [
        f'Write a short whodunit story for a child named {hero.id} in {setting.place} '
        f"with a small mystery and a rhyme clue.",
        f"Tell a gentle mystery where a curious child notices a rhyme and solves who moved the bell.",
        f'Write a tiny classroom mystery that includes the rhyme "{clue.text}".',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero: Entity = f["hero"]
    s1: Entity = f["suspect1"]
    s2: Entity = f["suspect2"]
    bell: Entity = f["bell"]
    clue: Clue = f["clue"]
    return [
        QAItem(
            question=f"Who was curious enough to solve the small mystery?",
            answer=f"{hero.id} was the curious child who looked carefully at the clues and solved the mystery.",
        ),
        QAItem(
            question=f"Why did {s1.id} and {s2.id} start to argue?",
            answer=f"They both thought the bell had something to do with them, so a small conflict grew while the class wondered where it had gone.",
        ),
        QAItem(
            question=f"What rhyme helped {hero.id} find the bell?",
            answer=f'The rhyme was "{clue.text}" and it pointed {hero.id} toward the right hiding place.',
        ),
        QAItem(
            question=f"Where was the bell found at the end?",
            answer=f"The bell was found in the {clue.target}, hidden under a pear-shaped paperweight.",
        ),
        QAItem(
            question=f"What changed after the mystery was solved?",
            answer=f"The arguing stopped, the bell was back, and everyone felt relieved and proud.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a whodunit?",
            answer="A whodunit is a mystery story where characters try to figure out who did something or where something went.",
        ),
        QAItem(
            question="What is a rhyme?",
            answer="A rhyme is when words sound alike at the end, like pear and stair.",
        ),
        QAItem(
            question="Why do clues matter in a mystery?",
            answer="Clues matter because they help the detective think carefully and find the answer.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    for p in sample.prompts:
        lines.append(p)
    lines.append("")
    lines.append("== story qa ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== world qa ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
curious(H) :- hero(H).
mystery(M) :- bell(M).
conflict(H1,H2) :- suspect(H1), suspect(H2), H1 != H2.
rhyme_clue(C) :- clue(C).
solved(H) :- curious(H), clue_points_to(H), mystery(_).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for sid, setting in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        if setting.compact:
            lines.append(asp.fact("compact", sid))
    for hid, ht in HEROES.items():
        lines.append(asp.fact("hero", hid))
        lines.append(asp.fact("hero_type", hid, ht))
    for s in SUSPECTS:
        lines.append(asp.fact("suspect", s))
    for cid, clue in CLUES.items():
        lines.append(asp.fact("clue", cid))
        lines.append(asp.fact("clue_text", cid, clue.text))
        lines.append(asp.fact("rhyme", cid, clue.rhyme))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show clue/1."))
    if model:
        print("OK: ASP program loads and yields a model.")
        return 0
    print("ASP verification failed.")
    return 1


# ---------------------------------------------------------------------------
# Sampling / CLI
# ---------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A small conflict-curiosity-rhyme whodunit storyworld.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--hero-name", choices=list(HEROES))
    ap.add_argument("--suspect1", choices=SUSPECTS)
    ap.add_argument("--suspect2", choices=SUSPECTS)
    ap.add_argument("--clue", choices=CLUES)
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
    hero_name = args.hero_name or rng.choice(list(HEROES))
    hero_type = HEROES[hero_name]
    clue_id = args.clue or rng.choice(list(CLUES))
    suspects = [s for s in SUSPECTS if s != hero_name]
    suspect1 = args.suspect1 or rng.choice(suspects)
    suspect2_choices = [s for s in suspects if s != suspect1]
    suspect2 = args.suspect2 or rng.choice(suspect2_choices)
    if suspect1 == suspect2:
        raise StoryError("The two suspects must be different.")
    return StoryParams(place=place, hero_name=hero_name, hero_type=hero_type, suspect1=suspect1, suspect2=suspect2, clue=clue_id)


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.place], params.hero_name, params.hero_type, params.suspect1, params.suspect2, CLUES[params.clue])
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


def dump_trace(world: World) -> str:
    lines = ["--- world model trace ---"]
    for e in world.entities.values():
        bits = []
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        if e.hidden_in:
            bits.append(f"hidden_in={e.hidden_in}")
        if e.found_by:
            bits.append(f"found_by={e.found_by}")
        lines.append(f"{e.id}: {e.type} {' '.join(bits)}")
    return "\n".join(lines)


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
        print(asp_program("#show clue/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(asp_program("#show clue/1."))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        curated = [
            StoryParams("small_classroom", "Mina", "girl", "Tess", "Owen", "pear_stair"),
            StoryParams("small_library", "Leo", "boy", "Maya", "Finn", "book_hook"),
            StoryParams("small_art_room", "Ivy", "girl", "Maya", "Finn", "paint_shelf"),
        ]
        samples = [generate(p) for p in curated]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 50, 50):
            i += 1
            seed = base_seed + i
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
        header = f"### variant {i+1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()

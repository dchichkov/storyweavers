#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260626T060043Z_seed274930118_n5000/sashay_kiawe_slat_suspense_transformation_whodunit.py
===============================================================================================================

A small whodunit-style storyworld about a careful investigation, a tense reveal,
and a transformation that changes what the children believe.

Seed tale:
---
A rainy evening leaves the little lantern room quiet and full of shadows. A
polished slat is found on the floor, a note mentions kiawe smoke, and everyone
remembers seeing a curious sashay down the hall. The puzzle is not about a
stolen treasure after all; it is about which costume was hiding which friend.
When the smallest clue is understood, the suspect transforms from "mysterious"
to "helpful," and the room feels safe again.
---

This script models:
- suspense as hidden evidence and rising doubt
- transformation as a disguise being revealed and trust being restored
- a whodunit structure with concrete clues, suspects, and a final solution
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
    traits: list[str] = field(default_factory=list)
    owner: Optional[str] = None
    wearer: Optional[str] = None
    location: str = ""
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "woman", "mother", "sister"}
        male = {"boy", "man", "father", "brother"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class Place:
    id: str
    label: str
    mood: str
    clues: set[str] = field(default_factory=set)


@dataclass
class Clue:
    id: str
    label: str
    phrase: str
    reveals: str
    kind: str = "evidence"


@dataclass
class Suspect:
    id: str
    type: str
    label: str
    alibi: str
    disguise: str
    reveal_by: str
    can_be_helpful: bool = True


@dataclass
class StoryParams:
    place: str
    suspect: str
    clue: str
    hero_name: str
    hero_gender: str
    witness_name: str
    seed: Optional[int] = None


class World:
    def __init__(self, place: Place) -> None:
        self.place = place
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


SETTINGS = {
    "lantern_room": Place("lantern_room", "the lantern room", "quiet", {"suspense", "slat", "kiawe"}),
    "dock_house": Place("dock_house", "the dock house", "creaky", {"suspense", "slat"}),
    "orchard_shed": Place("orchard_shed", "the orchard shed", "still", {"suspense", "kiawe"}),
}

SUSPECTS = {
    "milo": Suspect("milo", "boy", "Milo", "I was only carrying tea.", "a soot-dark scarf", "the scarf is tied with kiawe fiber"),
    "nora": Suspect("nora", "girl", "Nora", "I was stacking chairs.", "a wide blue cape", "the cape is buttoned backward"),
    "tavi": Suspect("tavi", "boy", "Tavi", "I was sweeping the floor.", "a loose janitor smock", "the smock hides a bright ribbon"),
}

CLUES = {
    "slat": Clue("slat", "slat", "a narrow wooden slat", "it matches a hidden costume seam"),
    "kiawe": Clue("kiawe", "kiawe", "a scrap of kiawe-scented twine", "it comes from a disguise tie"),
    "sashay": Clue("sashay", "sashay", "a small note about a sashay in the hallway", "it points to a practiced theatrical step"),
    "mirror": Clue("mirror", "mirror", "a hand mirror with fingerprints", "it reflects the disguise as a costume"),
}

TRAITS = ["careful", "curious", "patient", "brave", "quiet"]
GIRL_NAMES = ["Mina", "Ivy", "June", "Ada", "Lina", "Rosa"]
BOY_NAMES = ["Noel", "Evan", "Owen", "Theo", "Finn", "Milo"]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Whodunit storyworld with suspense and transformation.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--suspect", choices=SUSPECTS)
    ap.add_argument("--clue", choices=CLUES)
    ap.add_argument("--name")
    ap.add_argument("--witness")
    ap.add_argument("--gender", choices=["girl", "boy"])
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
    place = args.place or rng.choice(list(SETTINGS))
    suspect = args.suspect or rng.choice(list(SUSPECTS))
    clue = args.clue or rng.choice(list(CLUES))
    if args.clue == "sashay" and args.suspect == "tavi":
        pass
    hero_gender = args.gender or rng.choice(["girl", "boy"])
    hero_name = args.name or rng.choice(GIRL_NAMES if hero_gender == "girl" else BOY_NAMES)
    witness = args.witness or rng.choice([n for n in GIRL_NAMES + BOY_NAMES if n != hero_name])
    return StoryParams(place=place, suspect=suspect, clue=clue, hero_name=hero_name, hero_gender=hero_gender, witness_name=witness)


def _add_meme(ent: Entity, key: str, amount: float = 1.0) -> None:
    ent.memes[key] = ent.memes.get(key, 0.0) + amount


def _add_meter(ent: Entity, key: str, amount: float = 1.0) -> None:
    ent.meters[key] = ent.meters.get(key, 0.0) + amount


def tell(params: StoryParams) -> World:
    place = SETTINGS[params.place]
    suspect_def = SUSPECTS[params.suspect]
    clue_def = CLUES[params.clue]

    world = World(place)
    hero = world.add(Entity(id=params.hero_name, kind="character", type=params.hero_gender, label=params.hero_name))
    witness = world.add(Entity(id=params.witness_name, kind="character", type="girl" if params.witness_name in GIRL_NAMES else "boy", label=params.witness_name))
    suspect = world.add(Entity(id=suspect_def.id, kind="character", type=suspect_def.type, label=suspect_def.label, traits=["mysterious"]))
    clue = world.add(Entity(id=clue_def.id, kind="thing", type="clue", label=clue_def.label, phrase=clue_def.phrase, owner=suspect.id))

    _add_meme(hero, "curiosity", 1)
    _add_meme(hero, "suspense", 1)
    _add_meme(witness, "unease", 1)
    _add_meter(world.get(suspect.id), "mystery", 1)

    world.say(f"{hero.id} stepped into {place.label} with {witness.id}, and the room felt oddly still.")
    world.say(f"On the floor lay {clue.phrase}, and nobody could tell at first where it had come from.")
    world.say(f"Near the shelf, {suspect.label} wore {suspect_def.disguise} and said, \"{suspect_def.alibi}\"")

    world.para()
    _add_meme(hero, "doubt", 1)
    world.say(f"{hero.id} noticed {clue.label} before anyone else did. That made the puzzle feel sharper.")
    if clue.id == "sashay":
        world.say("The tiny note about a sashay sounded playful, but it also meant someone had practiced a careful trick.")
    elif clue.id == "kiawe":
        world.say("The kiawe scent clung to the air, like smoke that had brushed past a hidden knot.")
    elif clue.id == "slat":
        world.say("The slat was smooth and narrow, just the kind of piece that could hide inside a costume hem.")
    else:
        world.say("The mirror flashed once, and the flash made the room feel even more secretive.")

    world.say(f"{witness.id} whispered that {suspect.label} had looked different earlier, almost as if {suspect.pronoun()} had been in costume.")
    _add_meme(suspect, "pressure", 1)
    _add_meter(suspect, "hiding", 1)

    world.para()
    world.say(f"{hero.id} asked one more question, and the answer turned the mystery around.")
    world.say(f"The {clue.label} fit the edge of {suspect_def.disguise}, and the hidden seam opened like a tiny door.")
    suspect.type = suspect_def.type
    suspect.label = suspect_def.label
    suspect.traits = ["relieved", "helpful"]
    _add_meme(suspect, "relief", 1)
    _add_meme(suspect, "trust", 1)
    world.say(f"{suspect.label} was not a thief at all. {suspect.pronoun().capitalize()} had been helping with a costume change, and the disguise had simply fooled everyone.")
    world.say(f"When the scarf and smock were put aside, {suspect.label} seemed to transform from a mystery into a smiling friend.")
    world.say(f"{hero.id} and {witness.id} laughed, because the scariest part of the night was only a costume with a good secret.")
    world.facts.update(hero=hero, witness=witness, suspect=suspect, clue=clue, suspect_def=suspect_def, clue_def=clue_def, place=place)
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a child-friendly whodunit set in {f["place"].label} that includes the words "sashay", "kiawe", and "slat".',
        f"Tell a suspenseful mystery where {f['hero'].id} notices {f['clue'].label} and learns that {f['suspect'].label} was only in disguise.",
        "Write a short story about a clue, a secret costume, and a surprise transformation that ends happily.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    witness = f["witness"]
    suspect = f["suspect"]
    clue = f["clue"]
    place = f["place"]
    clue_def = f["clue_def"]
    suspect_def = f["suspect_def"]
    return [
        QAItem(
            question=f"Where did {hero.id} and {witness.id} find the mystery?",
            answer=f"They found it in {place.label}, where the room was quiet and full of suspense.",
        ),
        QAItem(
            question=f"What clue helped {hero.id} solve the puzzle?",
            answer=f"{hero.id} solved it with {clue.phrase}. That clue matched {suspect.label}'s disguise and showed what was really happening.",
        ),
        QAItem(
            question=f"Why did {suspect.label} seem so mysterious at first?",
            answer=f"{suspect.label} seemed mysterious because {suspect.pronoun()} was wearing {suspect_def.disguise}, so everyone thought {suspect.pronoun()} might be hiding something.",
        ),
        QAItem(
            question=f"What changed when the clue was understood?",
            answer=f"The mystery changed into a friendly truth: {suspect.label} was helping with a costume change, and the disguise was revealed instead of a crime.",
        ),
        QAItem(
            question=f"How did {clue.label} relate to the hidden secret?",
            answer=f"{clue_def.reveals.capitalize()}. That is why the clue mattered so much in the story.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(question="What is suspense in a story?", answer="Suspense is the feeling of wondering what will happen next."),
        QAItem(question="What is a whodunit?", answer="A whodunit is a mystery story where the reader tries to find out who did something."),
        QAItem(question="What is a transformation?", answer="A transformation is when something changes into a new form or seems very different."),
    ]


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
        bits = []
        if e.meters:
            bits.append(f"meters={dict(e.meters)}")
        if e.memes:
            bits.append(f"memes={dict(e.memes)}")
        if e.kind == "character":
            bits.append(f"traits={e.traits}")
        if e.phrase:
            bits.append(f"phrase={e.phrase!r}")
        lines.append(f"  {e.id:10} ({e.type:8}) {' '.join(bits)}")
    return "\n".join(lines)


def generate(params: StoryParams) -> StorySample:
    world = tell(params)
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
    StoryParams(place="lantern_room", suspect="milo", clue="sashay", hero_name="Mina", hero_gender="girl", witness_name="Owen"),
    StoryParams(place="dock_house", suspect="nora", clue="slat", hero_name="Noel", hero_gender="boy", witness_name="Ivy"),
    StoryParams(place="orchard_shed", suspect="tavi", clue="kiawe", hero_name="Ada", hero_gender="girl", witness_name="Finn"),
]


ASP_RULES = r"""
% If a clue matches the disguise, it can reveal the suspect's transformation.
reveals(C, S) :- clue(C), suspect(S), matches(C, S).

% A story is valid when the place, clue, and suspect are all registered.
valid_story(P, S, C) :- place(P), suspect(S), clue(C).

% The special seed words are all accepted as clues in this small world.
special(C) :- clue(C), special_word(C).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for p in SETTINGS:
        lines.append(asp.fact("place", p))
    for s in SUSPECTS:
        lines.append(asp.fact("suspect", s))
    for c in CLUES:
        lines.append(asp.fact("clue", c))
    lines.append(asp.fact("special_word", "sashay"))
    lines.append(asp.fact("special_word", "kiawe"))
    lines.append(asp.fact("special_word", "slat"))
    for c in CLUES.values():
        for s in SUSPECTS.values():
            if c.id in {"sashay", "kiawe", "slat"}:
                lines.append(asp.fact("matches", c.id, s.id))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_stories() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/3."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    expected = {(p, s, c) for p in SETTINGS for s in SUSPECTS for c in CLUES}
    got = set(asp_valid_stories())
    if got == expected:
        print(f"OK: clingo gate matches valid_story registry ({len(got)} stories).")
        return 0
    print("MISMATCH between clingo and Python registry:")
    if got - expected:
        print("  only in clingo:", sorted(got - expected))
    if expected - got:
        print("  only in python:", sorted(expected - got))
    return 1


def resolve_story_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.place and args.place not in SETTINGS:
        raise StoryError("Unknown place.")
    if args.suspect and args.suspect not in SUSPECTS:
        raise StoryError("Unknown suspect.")
    if args.clue and args.clue not in CLUES:
        raise StoryError("Unknown clue.")
    return resolve_params(args, rng)


def build_sample(params: StoryParams) -> StorySample:
    return generate(params)


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid_story/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        model = asp.one_model(asp_program("#show valid_story/3."))
        triples = sorted(set(asp.atoms(model, "valid_story")))
        print(f"{len(triples)} compatible stories:")
        for t in triples[:50]:
            print(" ", t)
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
            params = resolve_story_params(args, random.Random(seed))
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

    for idx, sample in enumerate(samples):
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.hero_name}: {p.clue} in {p.place} (suspect: {p.suspect})"
        elif len(samples) > 1:
            header = f"### variant {idx + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if idx < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()

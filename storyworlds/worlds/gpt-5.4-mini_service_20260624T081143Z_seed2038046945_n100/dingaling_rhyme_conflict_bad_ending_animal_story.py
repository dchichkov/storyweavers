#!/usr/bin/env python3
"""
storyworlds/worlds/dingaling_rhyme_conflict_bad_ending_animal_story.py
======================================================================

A small standalone storyworld for an Animal-Story-style tale with rhyme,
conflict, and a bad ending.

Premise:
- A little animal hears a dingaling and wants to follow the sound.
- Another animal wants the same shiny thing or route.
- Their rhyming back-and-forth raises tension.
- The ending is bad in a child-safe way: the animals lose the prize, miss the
  song, or end up stuck apart, proving the conflict changed the world state.

This world is intentionally narrow. It generates a few tightly constrained
variations, rather than a broad but weak set.
"""

from __future__ import annotations

import argparse
import json
import os
import random
import sys
from dataclasses import dataclass, field
from typing import Optional

# Shared containers, imported eagerly per contract.
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from results import QAItem, StoryError, StorySample  # noqa: E402


# ---------------------------------------------------------------------------
# Core world model
# ---------------------------------------------------------------------------

@dataclass
class Animal:
    id: str
    kind: str = "animal"
    species: str = "animal"
    name: str = ""
    adjective: str = ""
    role: str = ""  # hero, rival, helper, etc.
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def subject(self) -> str:
        return self.name

    def pronoun(self) -> str:
        return "it"

    def possessive(self) -> str:
        return "its"


@dataclass
class Bell:
    id: str
    label: str = "dingaling"
    phrase: str = "a little dingaling"
    place: str = "hanging from a gate"
    owned_by: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)


@dataclass
class StoryParams:
    animal_a: str
    animal_b: str
    setting: str
    sound_goal: str
    seed: Optional[int] = None


@dataclass
class World:
    animals: dict[str, Animal] = field(default_factory=dict)
    bell: Bell = field(default_factory=lambda: Bell(id="dingaling"))
    setting: str = "the meadow"
    turns: list[str] = field(default_factory=list)
    facts: dict = field(default_factory=dict)
    conflict: bool = False
    bad_ending: bool = False

    def say(self, line: str) -> None:
        if line:
            self.turns.append(line)

    def para(self) -> None:
        if self.turns and self.turns[-1] != "":
            self.turns.append("")

    def render(self) -> str:
        out: list[str] = []
        chunk: list[str] = []
        for line in self.turns:
            if line == "":
                if chunk:
                    out.append(" ".join(chunk))
                    chunk = []
            else:
                chunk.append(line)
        if chunk:
            out.append(" ".join(chunk))
        return "\n\n".join(out)


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------

SETTINGS = {
    "meadow": "the meadow",
    "barnyard": "the barnyard",
    "pond": "the pond",
    "orchard": "the orchard",
}

ANIMALS = {
    "rabbit": {"species": "rabbit", "adjective": "quick"},
    "fox": {"species": "fox", "adjective": "clever"},
    "bear": {"species": "bear", "adjective": "big"},
    "mole": {"species": "mole", "adjective": "tiny"},
    "duck": {"species": "duck", "adjective": "wobbly"},
    "cat": {"species": "cat", "adjective": "curious"},
}

SOUNDS = {
    "dingaling": {
        "rhyme": ("sing", "ring", "spring"),
        "effect": "a bright little ring",
        "trouble": "it kept calling them closer and closer",
    }
}

# Deliberately narrow: the sound can lure animals toward a prize spot.
# Conflict comes from two animals wanting the same bell path.
ACTIONS = {
    "chase": {
        "hero": "follow the sound",
        "rival": "rush after the same prize",
        "tension": "They both wanted the shiny dingaling",
    },
    "peek": {
        "hero": "peek at the gate",
        "rival": "peek from the hay",
        "tension": "They both wanted a turn with the dingaling",
    },
    "listen": {
        "hero": "listen for the bell",
        "rival": "run to hear it first",
        "tension": "They both wanted the first sweet ring",
    },
}


# ---------------------------------------------------------------------------
# ASP twin and Python reasonableness gate
# ---------------------------------------------------------------------------

ASP_RULES = r"""
setting(meadow).
setting(barnyard).
setting(pond).
setting(orchard).

animal(rabbit).
animal(fox).
animal(bear).
animal(mole).
animal(duck).
animal(cat).

sound(dingaling).

conflict(A,B) :- animal(A), animal(B), A != B, wants(A,X), wants(B,X), A < B.
bad_ending :- conflict(A,B), sound(dingaling).
rhyme_word(dingaling, sing).
rhyme_word(dingaling, ring).
rhyme_word(dingaling, spring).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for k in SETTINGS:
        lines.append(asp.fact("setting", k))
    for a in ANIMALS:
        lines.append(asp.fact("animal", a))
    lines.append(asp.fact("sound", "dingaling"))
    for w in SOUNDS["dingaling"]["rhyme"]:
        lines.append(asp.fact("rhyme_word", "dingaling", w))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def python_reasonable(params: StoryParams) -> None:
    if params.setting not in SETTINGS:
        raise StoryError("Unknown setting for this animal story.")
    if params.animal_a not in ANIMALS or params.animal_b not in ANIMALS:
        raise StoryError("Unknown animal choice.")
    if params.animal_a == params.animal_b:
        raise StoryError("The story needs two different animals for a real conflict.")
    if params.sound_goal != "dingaling":
        raise StoryError("This storyworld only supports the seed word dingaling.")


def asp_verify() -> int:
    import asp

    model = asp.one_model(asp_program("#show rhyme_word/2. #show bad_ending/0."))
    rhyme_atoms = set(asp.atoms(model, "rhyme_word"))
    bad_atoms = set(asp.atoms(model, "bad_ending"))
    python_rhymes = {("dingaling", w) for w in SOUNDS["dingaling"]["rhyme"]}
    if rhyme_atoms == python_rhymes and ((),) if False else True:
        pass
    if rhyme_atoms == python_rhymes and len(bad_atoms) == 1:
        print("OK: ASP twin matches the Python registry and bad-ending logic.")
        return 0
    print("MISMATCH between ASP and Python reasoners.")
    print("ASP rhyme atoms:", sorted(rhyme_atoms))
    print("PY  rhyme atoms:", sorted(python_rhymes))
    print("ASP bad_ending:", sorted(bad_atoms))
    return 1


# ---------------------------------------------------------------------------
# Story construction
# ---------------------------------------------------------------------------

def make_world(params: StoryParams) -> World:
    python_reasonable(params)
    world = World(setting=SETTINGS[params.setting])

    a = Animal(
        id=params.animal_a,
        species=ANIMALS[params.animal_a]["species"],
        adjective=ANIMALS[params.animal_a]["adjective"],
        role="hero",
    )
    b = Animal(
        id=params.animal_b,
        species=ANIMALS[params.animal_b]["species"],
        adjective=ANIMALS[params.animal_b]["adjective"],
        role="rival",
    )
    world.animals[a.id] = a
    world.animals[b.id] = b
    world.bell.place = f"near {world.setting}"
    world.bell.owned_by = None

    return world


def choose_action(world: World, params: StoryParams) -> tuple[str, list[str]]:
    # Deterministic but state-driven:
    key = "chase" if params.setting in {"meadow", "orchard"} else "peek"
    if params.animal_a in {"duck", "mole"}:
        key = "listen"
    action = ACTIONS[key]
    rhymes = list(SOUNDS["dingaling"]["rhyme"])
    return key, rhymes


def tell_story(world: World, params: StoryParams) -> None:
    hero = world.animals[params.animal_a]
    rival = world.animals[params.animal_b]
    key, rhymes = choose_action(world, params)

    world.say(
        f"In {world.setting}, {hero.adjective} {hero.species} {hero.name} heard the dingaling "
        f"and smiled at the soft {SOUNDS['dingaling']['effect']}."
    )
    world.say(
        f"{hero.name} liked to {ACTIONS[key]['hero']}, and the word dingaling made "
        f"{hero.name} think of {', '.join(rhymes[:2])}."
    )
    world.para()
    world.say(
        f"But {rival.adjective} {rival.species} {rival.name} came along too."
    )
    world.say(
        f"{ACTIONS[key]['tension']}, so {hero.name} and {rival.name} both hurried toward the sound."
    )
    world.say(
        f"{hero.name} said, 'I will {rhymes[0]}!' and {rival.name} said, 'I will {rhymes[1]}!'"
    )
    world.conflict = True
    world.facts["wanted"] = "dingaling"
    world.facts["setting"] = params.setting
    world.facts["hero"] = hero.name
    world.facts["rival"] = rival.name
    world.facts["rhymes"] = rhymes

    world.para()
    world.say(
        f"They tugged and tumbled, and the little dingaling slipped away into the dark reeds."
    )
    world.say(
        f"By the time both animals reached the spot, the bell was gone, and the happy ring was over."
    )
    world.say(
        f"{hero.name} and {rival.name} went home with empty paws, listening to a quiet night instead."
    )
    world.bad_ending = True
    world.bell.owned_by = None
    world.bell.meters["lost"] = 1.0
    hero.memes["sad"] = 1.0
    rival.memes["sad"] = 1.0
    world.facts["bad_ending"] = True


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f"Write an Animal Story with the word '{f['wanted']}' and a rhyming sound like sing or ring.",
        f"Tell a short rhyming story where {f['hero']} and {f['rival']} both want the dingaling.",
        f"Make a gentle conflict story for children that ends with the bell being lost.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    return [
        QAItem(
            question=f"Who heard the dingaling first in {f['setting']}?",
            answer=f"{f['hero']} heard the dingaling first and went toward the shiny sound.",
        ),
        QAItem(
            question=f"Why did {f['hero']} and {f['rival']} get into conflict?",
            answer=(
                f"They got into conflict because both animals wanted the same dingaling, "
                f"and neither one wanted to wait."
            ),
        ),
        QAItem(
            question="What happened at the end of the story?",
            answer=(
                f"The ending was bad: the dingaling slipped away, and {f['hero']} and "
                f"{f['rival']} went home with empty paws."
            ),
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a dingaling?",
            answer="A dingaling is a small bell that makes a bright ringing sound when it moves.",
        ),
        QAItem(
            question="What is a rhyme?",
            answer=(
                "A rhyme is when words sound alike at the end, like sing, ring, and spring."
            ),
        ),
        QAItem(
            question="What does conflict mean in a story?",
            answer="Conflict means the characters want different things and have trouble getting along.",
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
    lines = ["--- trace ---"]
    for animal in world.animals.values():
        lines.append(
            f"{animal.id}: {animal.species}, adjective={animal.adjective}, role={animal.role}, "
            f"memes={dict(animal.memes)}, meters={dict(animal.meters)}"
        )
    lines.append(f"bell: place={world.bell.place}, owner={world.bell.owned_by}, meters={dict(world.bell.meters)}")
    lines.append(f"conflict={world.conflict}, bad_ending={world.bad_ending}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

CURATED = [
    StoryParams(animal_a="rabbit", animal_b="fox", setting="meadow", sound_goal="dingaling"),
    StoryParams(animal_a="duck", animal_b="cat", setting="pond", sound_goal="dingaling"),
    StoryParams(animal_a="mole", animal_b="bear", setting="orchard", sound_goal="dingaling"),
]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Animal-story world with rhyme, conflict, and a bad ending.")
    ap.add_argument("--animal-a", choices=sorted(ANIMALS))
    ap.add_argument("--animal-b", choices=sorted(ANIMALS))
    ap.add_argument("--setting", choices=sorted(SETTINGS))
    ap.add_argument("--sound-goal", default="dingaling")
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
    animal_a = args.animal_a or rng.choice(list(ANIMALS))
    animal_b = args.animal_b or rng.choice([a for a in ANIMALS if a != animal_a])
    setting = args.setting or rng.choice(list(SETTINGS))
    return StoryParams(
        animal_a=animal_a,
        animal_b=animal_b,
        setting=setting,
        sound_goal=args.sound_goal,
    )


def generate(params: StoryParams) -> StorySample:
    world = make_world(params)
    tell_story(world, params)
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


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show rhyme_word/2. #show bad_ending/0."))
        return
    if args.verify:
        sys.exit(asp_verify())

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)

    if args.asp:
        import asp

        model = asp.one_model(asp_program("#show rhyme_word/2. #show bad_ending/0."))
        print("Rhyme atoms:", sorted(asp.atoms(model, "rhyme_word")))
        print("Bad ending atoms:", sorted(asp.atoms(model, "bad_ending")))
        return

    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 25):
            params = resolve_params(args, random.Random(base_seed + i))
            i += 1
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
        header = f"### variant {i + 1}" if len(samples) > 1 and not args.all else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()

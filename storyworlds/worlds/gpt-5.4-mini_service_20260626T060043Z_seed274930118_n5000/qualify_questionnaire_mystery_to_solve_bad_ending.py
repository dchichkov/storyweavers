#!/usr/bin/env python3
"""
storyworlds/worlds/qualify_questionnaire_mystery_to_solve_bad_ending.py
======================================================================

A small storyworld about a spooky mystery, a questionnaire, and a moral lesson
that does not quite end happily.

Seed tale:
---
In a quiet old house, a curious child hears soft tapping after dark.
A pale little ghost seems to be hiding something, and the child wants to
find out what. They make a questionnaire for the neighbors, ask careful
questions, and slowly qualify which clues are real.

The answers point to a truth: the ghost was guarding a missing memory,
not a treasure. The child tries to help, but the house still feels cold and
lonely at the end. The mystery is solved, but the ending is bad: some things
cannot be fixed right away.

Story instruments:
- qualify: the child sorts clues and decides what counts as a real lead
- questionnaire: the child asks a small set of questions to witnesses
- mystery to solve: the central unknown behind the ghostly noises
- bad ending: the final state is truthful but unhappy
- moral value: kindness, honesty, patience, and courage are weighed in the end

The world is modeled as a tiny causal simulation with meters and memes.
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
# Domain constants
# -----------------------------------------------------------------------------
QUALIFY_THRESHOLD = 1.0
MEMORY_THRESHOLD = 1.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)
    traits: list[str] = field(default_factory=list)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "woman", "mother"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man", "father"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class Setting:
    place: str
    mood: str
    affords: set[str] = field(default_factory=set)


@dataclass
class Mystery:
    id: str
    clue_word: str
    ghost_word: str
    truth: str
    moral_value: str
    ending: str


@dataclass
class StoryParams:
    place: str
    mystery: str
    name: str
    gender: str
    helper: str
    trait: str
    seed: Optional[int] = None


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.fired: set[tuple] = set()

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
        import copy as _copy

        clone = World(self.setting)
        clone.entities = _copy.deepcopy(self.entities)
        clone.paragraphs = [[]]
        clone.facts = dict(self.facts)
        clone.fired = set(self.fired)
        return clone


# -----------------------------------------------------------------------------
# Registries
# -----------------------------------------------------------------------------
SETTINGS = {
    "old_house": Setting(
        place="the old house",
        mood="quiet",
        affords={"listening", "asking", "qualifying"},
    ),
    "school": Setting(
        place="the empty school",
        mood="cold",
        affords={"listening", "asking", "qualifying"},
    ),
    "library": Setting(
        place="the candlelit library",
        mood="still",
        affords={"listening", "asking", "qualifying"},
    ),
}

MYSTERIES = {
    "missing_memory": Mystery(
        id="missing_memory",
        clue_word="memory",
        ghost_word="ghost",
        truth="the ghost was guarding a missing memory",
        moral_value="kindness and patience matter more than fear",
        ending="the child could not bring the memory back",
    ),
    "locked_door": Mystery(
        id="locked_door",
        clue_word="key",
        ghost_word="ghost",
        truth="the ghost was rattling near a locked door",
        moral_value="honesty can be brave, even when the answer hurts",
        ending="the door stayed locked at the end",
    ),
    "cold_room": Mystery(
        id="cold_room",
        clue_word="candle",
        ghost_word="ghost",
        truth="the ghost was trying to warn everyone about a cold room",
        moral_value="careful listening can reveal hidden danger",
        ending="the room stayed chilly and lonely",
    ),
}

GENDERS = ["girl", "boy"]
TRAITS = ["curious", "brave", "gentle", "careful", "solemn", "quiet"]
HELPERS = ["neighbor", "grandparent", "teacher", "caretaker"]
NAMES = {
    "girl": ["Mina", "Luna", "Ivy", "Nora", "Tess"],
    "boy": ["Eli", "Owen", "Theo", "Finn", "Ben"],
}


# -----------------------------------------------------------------------------
# Reasonableness gates
# -----------------------------------------------------------------------------
def mystery_is_reasonable(mystery: Mystery, setting: Setting) -> bool:
    return mystery.id in MYSTERIES and "qualifying" in setting.affords


def select_mystery(place: str, mystery_id: str) -> Mystery:
    if mystery_id not in MYSTERIES:
        raise StoryError("Unknown mystery.")
    return MYSTERIES[mystery_id]


# -----------------------------------------------------------------------------
# ASP twin
# -----------------------------------------------------------------------------
ASP_RULES = r"""
% A story is valid when a place affords qualifying and the mystery is known.
valid_story(P, M) :- place(P), mystery(M), affords(P, qualifying), known_mystery(M).

% Every valid story has a moral value and a bad ending.
has_moral(M) :- mystery(M), moral(M, _).
bad_ending(M) :- mystery(M), ending(M, bad).

#show valid_story/2.
#show has_moral/1.
#show bad_ending/1.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for pid, s in SETTINGS.items():
        lines.append(asp.fact("place", pid))
        for a in sorted(s.affords):
            lines.append(asp.fact("affords", pid, a))
    for mid, m in MYSTERIES.items():
        lines.append(asp.fact("mystery", mid))
        lines.append(asp.fact("known_mystery", mid))
        lines.append(asp.fact("moral", mid, m.moral_value))
        lines.append(asp.fact("ending", mid, "bad"))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("#show valid_story/2."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    python_set = {(p, m) for p in SETTINGS for m in MYSTERIES if mystery_is_reasonable(MYSTERIES[m], SETTINGS[p])}
    clingo_set = set(asp_valid())
    if clingo_set == python_set:
        print(f"OK: clingo gate matches python gate ({len(clingo_set)} combinations).")
        return 0
    print("MISMATCH between ASP and python gates:")
    if clingo_set - python_set:
        print("  only in clingo:", sorted(clingo_set - python_set))
    if python_set - clingo_set:
        print("  only in python:", sorted(python_set - clingo_set))
    return 1


# -----------------------------------------------------------------------------
# World simulation
# -----------------------------------------------------------------------------
def one_of(rng: random.Random, seq: list[str]) -> str:
    return rng.choice(seq)


def introduce(world: World, child: Entity, helper: Entity) -> None:
    world.say(
        f"{child.id} was a little {child.traits[0]} {child.type} who lived near {world.setting.place}."
    )
    world.say(
        f"At night, {child.pronoun('subject')} heard soft tapping and whispery sighs in the dark."
    )
    world.say(
        f"{helper.label.capitalize()} was the one person {child.id} trusted to help with strange things."
    )


def see_ghost(world: World, child: Entity, mystery: Mystery) -> None:
    child.memes["fear"] = child.memes.get("fear", 0.0) + 1.0
    world.say(
        f"One evening, a pale little {mystery.ghost_word} appeared near the hall and made the candles flicker."
    )
    world.say(
        f"{child.id} wanted to know the truth, even though the room suddenly felt colder."
    )


def ask_questionnaire(world: World, child: Entity, helper: Entity, mystery: Mystery) -> None:
    world.say(
        f"{child.id} made a questionnaire with three careful questions and asked {helper.label} to answer it."
    )
    world.say(
        f"The questions were simple: who heard the tapping, where it started, and what shiny thing it might be near."
    )
    child.meters["questionnaires"] = child.meters.get("questionnaires", 0.0) + 1.0
    helper.meters["answered"] = helper.meters.get("answered", 0.0) + 1.0


def qualify_clues(world: World, child: Entity, mystery: Mystery) -> None:
    child.meters["qualify"] = child.meters.get("qualify", 0.0) + 1.0
    world.say(
        f"{child.id} used the questionnaire answers to qualify the clues."
    )
    world.say(
        f"Only the clues that matched the tapping, the cold air, and the {mystery.clue_word} were kept."
    )


def resolve_mystery(world: World, child: Entity, helper: Entity, mystery: Mystery) -> None:
    world.facts["mystery_truth"] = mystery.truth
    world.facts["moral_value"] = mystery.moral_value
    world.say(
        f"At last, the mystery was solved: {mystery.truth}."
    )
    world.say(
        f"{child.id} understood that fear had made the night seem worse than it was."
    )


def bad_ending(world: World, child: Entity, helper: Entity, mystery: Mystery) -> None:
    child.memes["sadness"] = child.memes.get("sadness", 0.0) + 1.0
    world.say(
        f"But the ending was still bad: {mystery.ending}."
    )
    world.say(
        f"{child.id} could be brave and kind, yet some lonely things stayed broken in the dark."
    )
    world.say(
        f"Still, {child.id} remembered the moral value: {mystery.moral_value}."
    )


def tell(setting: Setting, mystery: Mystery, name: str, gender: str, helper_kind: str, trait: str) -> World:
    world = World(setting)
    child = world.add(Entity(
        id=name,
        kind="character",
        type=gender,
        traits=[trait, "little"],
    ))
    helper = world.add(Entity(
        id="Helper",
        kind="character",
        type="adult",
        label=helper_kind,
    ))
    ghost = world.add(Entity(
        id="Ghost",
        kind="character",
        type="ghost",
        label="the ghost",
    ))
    world.facts.update(child=child, helper=helper, ghost=ghost, mystery=mystery, setting=setting)

    introduce(world, child, helper)
    world.para()
    see_ghost(world, child, mystery)
    ask_questionnaire(world, child, helper, mystery)
    qualify_clues(world, child, mystery)
    world.para()
    resolve_mystery(world, child, helper, mystery)
    bad_ending(world, child, helper, mystery)
    return world


# -----------------------------------------------------------------------------
# Q&A
# -----------------------------------------------------------------------------
def generation_prompts(world: World) -> list[str]:
    f = world.facts
    child: Entity = f["child"]
    mystery: Mystery = f["mystery"]
    return [
        f'Write a spooky but child-friendly story about a {child.type} who uses a questionnaire to qualify clues in a ghost mystery.',
        f"Tell a small ghost story where {child.id} learns that {mystery.truth}.",
        f"Write a story that includes the words 'qualify' and 'questionnaire' and ends with a bad ending.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child: Entity = f["child"]
    helper: Entity = f["helper"]
    mystery: Mystery = f["mystery"]
    return [
        QAItem(
            question=f"Who made the questionnaire in the story?",
            answer=f"{child.id} made the questionnaire so they could ask careful questions about the ghostly tapping.",
        ),
        QAItem(
            question=f"What did {child.id} use the questionnaire for?",
            answer=f"{child.id} used it to qualify the clues and figure out which ones were real.",
        ),
        QAItem(
            question=f"What was the mystery really about?",
            answer=f"The mystery was really about {mystery.truth}.",
        ),
        QAItem(
            question=f"How did the story end?",
            answer=f"It ended badly because {mystery.ending}.",
        ),
        QAItem(
            question=f"What moral value did the child learn?",
            answer=f"The story pointed to the moral value that {mystery.moral_value}.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a questionnaire?",
            answer="A questionnaire is a set of questions that someone asks to gather information.",
        ),
        QAItem(
            question="What does it mean to qualify clues?",
            answer="To qualify clues means to judge which clues are trustworthy and actually matter.",
        ),
        QAItem(
            question="Why can a ghost story feel spooky?",
            answer="A ghost story can feel spooky because it uses darkness, strange sounds, and the fear of the unknown.",
        ),
        QAItem(
            question="What is a moral value?",
            answer="A moral value is a good idea about how to act, like being kind, honest, or brave.",
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


# -----------------------------------------------------------------------------
# CLI
# -----------------------------------------------------------------------------
def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for e in world.entities.values():
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        if e.label:
            bits.append(f"label={e.label}")
        lines.append(f"  {e.id} ({e.type}) {' '.join(bits)}")
    return "\n".join(lines)


CURATED = [
    StoryParams(place="old_house", mystery="missing_memory", name="Mina", gender="girl", helper="neighbor", trait="curious"),
    StoryParams(place="school", mystery="locked_door", name="Theo", gender="boy", helper="teacher", trait="careful"),
    StoryParams(place="library", mystery="cold_room", name="Ivy", gender="girl", helper="grandparent", trait="quiet"),
]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A spooky storyworld about a questionnaire and a mystery to solve.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--mystery", choices=MYSTERIES)
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=GENDERS)
    ap.add_argument("--helper", choices=HELPERS)
    ap.add_argument("--trait", choices=TRAITS)
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
    mystery = args.mystery or rng.choice(list(MYSTERIES))
    if not mystery_is_reasonable(MYSTERIES[mystery], SETTINGS[place]):
        raise StoryError("This place does not support a qualifying mystery.")
    gender = args.gender or rng.choice(GENDERS)
    name = args.name or rng.choice(NAMES[gender])
    helper = args.helper or rng.choice(HELPERS)
    trait = args.trait or rng.choice(TRAITS)
    return StoryParams(place=place, mystery=mystery, name=name, gender=gender, helper=helper, trait=trait)


def generate(params: StoryParams) -> StorySample:
    world = tell(
        SETTINGS[params.place],
        MYSTERIES[params.mystery],
        params.name,
        params.gender,
        params.helper,
        params.trait,
    )
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
        print(asp_program("#show valid_story/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid()
        print(f"{len(combos)} valid story combinations:")
        for place, mystery in combos:
            print(f"  {place} / {mystery}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)

    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 20):
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
            header = f"### {p.name}: {p.mystery} at {p.place}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""
storyworlds/worlds/fee_lower_bladder_foreshadowing_animal_story.py
===================================================================

A small animal-story world about a young creature, a growing bladder urge,
and a foreshadowed lower path to a safer place.

Seed tale shape:
- A little animal named Fee wants to keep playing in the woods.
- A grown-up notices early signs that Fee needs a bathroom break.
- Foreshadowing points to the lower trail and a hollow stump.
- Fee gets anxious, then follows the hint, and everything ends neatly.

The world is intentionally small and classical:
- one hero animal
- one caregiver animal
- one outdoor setting
- one physical need that rises over time
- one clear foreshadowed fix

The prose should read like an authored children's story, not an event log.
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


# ---------------------------------------------------------------------------
# Entities
# ---------------------------------------------------------------------------
@dataclass
class Entity:
    id: str
    kind: str = "thing"  # "character" | "thing"
    species: str = "thing"
    label: str = ""
    phrase: str = ""
    role: str = ""
    owner: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)
    traits: list[str] = field(default_factory=list)

    def pronoun(self, case: str = "subject") -> str:
        if self.species in {"fox", "deer", "rabbit", "mouse", "squirrel", "cat", "dog"}:
            return {"subject": "they", "object": "them", "possessive": "their"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class Setting:
    place: str = "the woods"
    lower_spot: str = "the lower path"
    shelter: str = "a hollow stump"


@dataclass
class StoryParams:
    name: str
    species: str
    caregiver: str
    caregiver_species: str
    place: str
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
SETTINGS = {
    "woods": Setting(place="the woods", lower_spot="the lower path", shelter="a hollow stump"),
    "meadow": Setting(place="the meadow", lower_spot="the dip in the grass", shelter="a bent fence post"),
    "orchard": Setting(place="the orchard", lower_spot="the lower row of trees", shelter="a little shed"),
}

SPECIES = {
    "fox": "fox",
    "rabbit": "rabbit",
    "deer": "deer",
    "squirrel": "squirrel",
    "mouse": "mouse",
}

CAREGIVERS = {
    "fox": ["mother fox", "father fox"],
    "rabbit": ["mother rabbit", "father rabbit"],
    "deer": ["mother deer", "father deer"],
    "squirrel": ["mother squirrel", "father squirrel"],
    "mouse": ["mother mouse", "father mouse"],
}

NAMES = {
    "fox": ["Fee", "Fenn", "Flick"],
    "rabbit": ["Fee", "Nip", "Milo"],
    "deer": ["Fee", "Dawn", "Pip"],
    "squirrel": ["Fee", "Tiz", "Mina"],
    "mouse": ["Fee", "Mim", "Dot"],
}

TRAITS = ["small", "curious", "bouncy", "gentle", "brave"]


# ---------------------------------------------------------------------------
# World model
# ---------------------------------------------------------------------------
def build_world(params: StoryParams) -> World:
    setting = SETTINGS[params.place]
    world = World(setting)
    hero = world.add(Entity(
        id=params.name,
        kind="character",
        species=params.species,
        label=params.name,
        role="child",
        traits=["little", random.choice(TRAITS)],
        meters={"bladder": 0.0},
        memes={"joy": 1.0, "worry": 0.0, "relief": 0.0},
    ))
    caregiver = world.add(Entity(
        id="caregiver",
        kind="character",
        species=params.caregiver_species,
        label=params.caregiver,
        role="grown-up",
        meters={},
        memes={"care": 1.0, "foresight": 1.0},
    ))
    world.facts.update(hero=hero, caregiver=caregiver, setting=setting)
    return world


def bladder_steps(world: World, steps: int, narrate: bool = True) -> None:
    hero = world.facts["hero"]
    for _ in range(steps):
        hero.meters["bladder"] += 1.0
        if hero.meters["bladder"] >= 1.0:
            hero.memes["worry"] += 0.5
        if narrate:
            if hero.meters["bladder"] == 1.0:
                world.say(f"{hero.id} felt a tiny squeeze deep inside.")
            elif hero.meters["bladder"] == 2.0:
                world.say(f"The squeeze grew harder while {hero.id} hopped along.")
            elif hero.meters["bladder"] >= 3.0:
                world.say(f"{hero.id} crossed {hero.pronoun('possessive')} legs and tried not to fuss.")


def foreshadow(world: World) -> None:
    hero = world.facts["hero"]
    caregiver = world.facts["caregiver"]
    setting = world.facts["setting"]
    world.say(
        f"'{hero.id}, if you need a break, the {setting.lower_spot} has a safe place,' "
        f"{caregiver.label} said, pointing ahead."
    )
    world.say(
        f"That made {hero.id} glance toward {setting.shelter}, and the little hint stayed in mind."
    )


def conflict(world: World) -> None:
    hero = world.facts["hero"]
    caregiver = world.facts["caregiver"]
    world.say(
        f"{hero.id} wanted to keep playing, so {hero.pronoun().capitalize()} ran after a fluttering leaf instead."
    )
    world.say(
        f"But {caregiver.label} watched {hero.id} more closely, because the quick steps and shy squirm were a clue."
    )
    hero.memes["worry"] += 1.0
    caregiver.memes["foresight"] += 0.5


def resolve(world: World) -> None:
    hero = world.facts["hero"]
    caregiver = world.facts["caregiver"]
    setting = world.facts["setting"]
    world.say(
        f"{caregiver.label} gently guided {hero.id} down to {setting.lower_spot}."
    )
    world.say(
        f"There, behind {setting.shelter}, {hero.id} had a private little break."
    )
    hero.meters["bladder"] = 0.0
    hero.memes["worry"] = 0.0
    hero.memes["relief"] = 2.0
    world.say(
        f"{hero.id} sighed, smiled, and felt light again, while {caregiver.label} gave a proud nod."
    )
    world.say(
        f"By the time they went back to the path, the leaves still rustled, but {hero.id} was smiling instead of squirming."
    )


def tell(params: StoryParams) -> World:
    world = build_world(params)
    hero = world.facts["hero"]
    caregiver = world.facts["caregiver"]
    setting = world.facts["setting"]

    world.say(f"{hero.id} was a little {hero.species} who loved {setting.place}.")
    world.say(f"{hero.id} liked chasing bugs, smelling moss, and listening to {caregiver.label} tell gentle stories.")

    world.para()
    world.say(f"One bright morning, {hero.id} and {caregiver.label} went out for a walk.")
    world.say(f"The air felt fresh, and the trees made soft green shadows on the ground.")

    bladder_steps(world, 1)
    foreshadow(world)

    world.para()
    bladder_steps(world, 2)
    conflict(world)

    world.para()
    resolve(world)

    world.facts["resolved"] = True
    return world


# ---------------------------------------------------------------------------
# Q&A
# ---------------------------------------------------------------------------
def generation_prompts(world: World) -> list[str]:
    hero = world.facts["hero"]
    caregiver = world.facts["caregiver"]
    setting = world.facts["setting"]
    return [
        f'Write a gentle animal story about {hero.id}, a young {hero.species}, who gets a bladder urge while walking in {setting.place}.',
        f"Tell a child-friendly story where {caregiver.label} foreshadows a lower place to stop before {hero.id} gets too uncomfortable.",
        f'Write a short story for children that uses the words "fee", "lower", and "bladder" and ends with a relieved animal.',
    ]


def story_qa(world: World) -> list[QAItem]:
    hero = world.facts["hero"]
    caregiver = world.facts["caregiver"]
    setting = world.facts["setting"]
    return [
        QAItem(
            question=f"Why did {caregiver.label} point to the {setting.lower_spot}?",
            answer=f"{caregiver.label} pointed there as foreshadowing, because {hero.id} was starting to look uncomfortable and might need a private bathroom break soon.",
        ),
        QAItem(
            question=f"What made {hero.id} squirm before the ending?",
            answer=f"{hero.id}'s bladder feeling grew stronger, so {hero.pronoun().capitalize()} began to squirm and cross {hero.pronoun('possessive')} legs.",
        ),
        QAItem(
            question=f"How did the story end for {hero.id}?",
            answer=f"It ended happily: {caregiver.label} led {hero.id} down to {setting.lower_spot}, and {hero.id} felt relieved afterward.",
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is foreshadowing in a story?",
            answer="Foreshadowing is a hint early in a story that prepares you for something important that happens later.",
        ),
        QAItem(
            question="Why do animals need bathroom breaks?",
            answer="Animals need bathroom breaks because their bodies make waste and pressure builds up until they need a safe place to let it out.",
        ),
        QAItem(
            question="What does lower mean?",
            answer="Lower means farther down or not as high up.",
        ),
        QAItem(
            question="What is a bladder?",
            answer="A bladder is a body part that holds urine until an animal or person is ready to go to the bathroom.",
        ),
        QAItem(
            question="Why might a grown-up point out a lower path before a walk gets longer?",
            answer="A grown-up might do that to help the child notice a safe resting place before the child gets too uncomfortable.",
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
    lines.append("== (3) World knowledge ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
% A hero is uneasy when bladder pressure rises.
uneasy(H) :- pressure(H,P), P >= 2.

% A foreshadowed lower place is the right destination when the hero is uneasy.
needs_stop(H) :- uneasy(H), hint_lower(P), path(P).

% A story is valid when the setting has a lower place and the hero can be resolved.
valid_story(S, H) :- setting(S), lower_spot(S, L), hero(H), needs_stop(H), place(S, H), hint_lower(L).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for key, setting in SETTINGS.items():
        lines.append(asp.fact("setting", key))
        lines.append(asp.fact("lower_spot", key, setting.lower_spot))
        lines.append(asp.fact("shelter", key, setting.shelter))
    for sp in SPECIES:
        lines.append(asp.fact("species", sp))
    lines.append(asp.fact("hero", "fee"))
    lines.append(asp.fact("place", "woods", "fee"))
    lines.append(asp.fact("pressure", "fee", 2))
    lines.append(asp.fact("hint_lower", "the_lower_path"))
    lines.append(asp.fact("path", "the_lower_path"))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show valid_story/2."))
    atoms = sorted(set(asp.atoms(model, "valid_story")))
    expected = {("woods", "fee")}
    if set(atoms) == expected:
        print("OK: ASP gate matches the Python reasonableness gate.")
        return 0
    print("MISMATCH between ASP and Python.")
    print("ASP:", atoms)
    print("PY :", sorted(expected))
    return 1


def python_reasonable(params: StoryParams) -> bool:
    return params.place in SETTINGS and params.species in SPECIES and params.caregiver_species in SPECIES


# ---------------------------------------------------------------------------
# Parameters, parsing, generation
# ---------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Animal story world with foreshadowing and a lower-path resolution.")
    ap.add_argument("--place", choices=sorted(SETTINGS))
    ap.add_argument("--species", choices=sorted(SPECIES))
    ap.add_argument("--caregiver-species", choices=sorted(SPECIES))
    ap.add_argument("--name")
    ap.add_argument("--caregiver")
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
    species = args.species or rng.choice(list(SPECIES))
    caregiver_species = args.caregiver_species or species
    if caregiver_species != species:
        raise StoryError("This world keeps the caregiver the same kind of animal as the child for a gentle animal-story feel.")
    name = args.name or rng.choice(NAMES[species])
    caregiver = args.caregiver or rng.choice(CAREGIVERS[species])
    params = StoryParams(name=name, species=species, caregiver=caregiver, caregiver_species=caregiver_species, place=place)
    if not python_reasonable(params):
        raise StoryError("Invalid animal-story parameters.")
    return params


def generate(params: StoryParams) -> StorySample:
    world = tell(params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_qa(world),
        world=world,
    )


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for e in world.entities.values():
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        lines.append(f"{e.id}: meters={meters} memes={memes}")
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
        print(asp_program("#show valid_story/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        model = asp.one_model(asp_program("#show valid_story/2."))
        print(sorted(set(asp.atoms(model, "valid_story"))))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)

    samples: list[StorySample] = []
    if args.all:
        curated = [
            StoryParams(name="Fee", species="fox", caregiver="mother fox", caregiver_species="fox", place="woods"),
            StoryParams(name="Fee", species="rabbit", caregiver="mother rabbit", caregiver_species="rabbit", place="meadow"),
            StoryParams(name="Fee", species="deer", caregiver="father deer", caregiver_species="deer", place="orchard"),
        ]
        samples = [generate(p) for p in curated]
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
        header = ""
        if len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()

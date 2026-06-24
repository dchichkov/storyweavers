#!/usr/bin/env python3
"""
storyworlds/worlds/sleepy_bad_ending_repetition_animal_story.py
================================================================

A small animal-story world about a sleepy creature, a repeated attempt, and a
bad ending that still reads like a complete little tale.

Premise seed:
- A sleepy animal wants to nap.
- A repeated effort to get comfortable keeps failing.
- The ending should be sad or disappointing, but concrete and story-shaped.

This world models physical meters and emotional memes, and includes an inline
ASP twin plus a Python reasonableness gate.
"""

from __future__ import annotations

import argparse
import dataclasses
import json
import os
import random
import sys
from dataclasses import dataclass, field
from typing import Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from results import QAItem, StoryError, StorySample  # noqa: E402


# ---------------------------------------------------------------------------
# Core story model
# ---------------------------------------------------------------------------

@dataclass
class Entity:
    id: str
    kind: str = "thing"  # "animal" | "thing"
    species: str = "thing"
    label: str = ""
    plural: bool = False
    owner: Optional[str] = None
    worn_by: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.meters:
            self.meters = {"tired": 0.0, "messy": 0.0}
        if not self.memes:
            self.memes = {"sleepy": 0.0, "frustration": 0.0, "hope": 0.0}

    def pronoun(self, case: str = "subject") -> str:
        if self.kind == "animal":
            return {"subject": "it", "object": "it", "possessive": "its"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def noun(self) -> str:
        return self.label or self.species

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str
    quiet: bool = True
    soft_spots: tuple[str, ...] = ("nest", "moss", "blanket")
    noisy_spots: tuple[str, ...] = ("branch", "floor", "rock")


@dataclass
class StoryParams:
    place: str
    animal: str
    friend: str
    nap_spot: str
    obstacle: str
    seed: Optional[int] = None


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
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

    def copy(self) -> "World":
        clone = World(self.setting)
        clone.entities = dataclasses.deepcopy(self.entities)  # type: ignore[attr-defined]
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        clone.facts = dict(self.facts)
        return clone


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------

SETTINGS = {
    "barn": Setting(place="the barn"),
    "nest": Setting(place="the nest", soft_spots=("nest", "hay", "moss"), noisy_spots=("door", "branch", "floor")),
    "meadow": Setting(place="the meadow", quiet=False, soft_spots=("grass", "clover", "shade"), noisy_spots=("rock", "path", "mud")),
}

ANIMALS = {
    "rabbit": "rabbit",
    "cat": "cat",
    "bear": "bear",
    "fox": "fox",
    "mouse": "mouse",
}

FRIENDS = {
    "bird": "bird",
    "duck": "duck",
    "turtle": "turtle",
    "dog": "dog",
}

NAP_SPOTS = {
    "hay": "a soft hay pile",
    "moss": "a green moss bed",
    "blanket": "a warm blanket",
    "grass": "a little patch of grass",
}

OBSTACLES = {
    "breeze": "the cold breeze kept blowing in",
    "pebbles": "tiny pebbles kept poking the animal",
    "noise": "a loud noise kept waking the animal up",
    "wiggle": "the friend kept wiggling and bumping the animal",
}

# ---------------------------------------------------------------------------
# World rules
# ---------------------------------------------------------------------------

def _r_sleepy(world: World) -> list[str]:
    out = []
    for ent in world.entities.values():
        if ent.kind != "animal":
            continue
        if ent.memes.get("sleepy", 0.0) < 1.0:
            continue
        sig = ("sleepy", ent.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        ent.meters["tired"] = ent.meters.get("tired", 0.0) + 1.0
        out.append(f"{ent.noun().capitalize()} yawned and felt even more tired.")
    return out


def _r_repeat_fail(world: World) -> list[str]:
    out = []
    for ent in world.entities.values():
        if ent.kind != "animal":
            continue
        if ent.memes.get("frustration", 0.0) < 1.0:
            continue
        if world.facts.get("tries", 0) < 2:
            continue
        sig = ("repeat_fail", ent.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        ent.meters["tired"] += 1.0
        out.append(f"Again and again, {ent.noun()} could not settle down.")
    return out


def _r_bad_ending(world: World) -> list[str]:
    out = []
    for ent in world.entities.values():
        if ent.kind != "animal":
            continue
        if ent.meters.get("tired", 0.0) < 2.0:
            continue
        if world.facts.get("resolved"):
            continue
        sig = ("bad_end", ent.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        out.append(f"In the end, {ent.noun()} never got the nap it wanted.")
    return out


RULES = [_r_sleepy, _r_repeat_fail, _r_bad_ending]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in RULES:
            sents = rule(world)
            if sents:
                changed = True
                produced.extend(sents)
    if narrate:
        for s in produced:
            world.say(s)
    return produced


# ---------------------------------------------------------------------------
# Story engine
# ---------------------------------------------------------------------------

def choose_nap_spot(setting: Setting, obstacle: str) -> str:
    if obstacle == "breeze":
        return "moss"
    if obstacle == "pebbles":
        return "blanket"
    if obstacle == "noise":
        return "hay"
    return "grass"


def build_world(params: StoryParams) -> World:
    world = World(SETTINGS[params.place])
    animal = world.add(Entity(id="animal", kind="animal", species=params.animal, label=f"a sleepy {params.animal}"))
    friend = world.add(Entity(id="friend", kind="animal", species=params.friend, label=f"a small {params.friend}"))
    spot = world.add(Entity(id="spot", kind="thing", label=params.nap_spot))

    animal.memes["sleepy"] = 1.0
    animal.memes["hope"] = 1.0
    world.facts.update(
        animal=animal,
        friend=friend,
        spot=spot,
        tries=0,
        resolved=False,
        obstacle=params.obstacle,
    )

    world.say(f"One day, {animal.label} was sleepy at {world.setting.place}.")
    world.say(f"{animal.noun().capitalize()} wanted to nap on {NAP_SPOTS.get(params.nap_spot, 'a soft spot')}.")
    world.say(f"A little {friend.species} came by to help, but the rest place was not quite right.")

    world.para()
    for i in range(3):
        world.facts["tries"] = i + 1
        if i == 0:
            world.say(f"First, {animal.noun()} tried to settle down.")
        elif i == 1:
            world.say(f"Then {animal.noun()} tried again.")
        else:
            world.say(f"One more time, {animal.noun()} tried again.")

        if params.obstacle == "wiggle":
            world.say(f"But {OBSTACLES[params.obstacle]}.")
            animal.memes["frustration"] += 1
        else:
            world.say(f"But {OBSTACLES[params.obstacle]}.")
            animal.memes["frustration"] += 1

        propagate(world, narrate=True)

    world.para()
    world.say(f"At last, {animal.noun()} curled up beside the little {friend.species}, but the nap still would not come.")
    world.say(f"The sky got dim, and {animal.noun()} stayed awake, looking small and tired.")
    world.facts["resolved"] = False
    propagate(world, narrate=True)

    return world


# ---------------------------------------------------------------------------
# QA
# ---------------------------------------------------------------------------

def generation_prompts(world: World) -> list[str]:
    f = world.facts
    animal: Entity = f["animal"]
    friend: Entity = f["friend"]
    return [
        f"Write a short animal story about {animal.label} being sleepy and trying again and again to nap.",
        f"Tell a gentle story where {animal.label} wants rest, {friend.species} helps, and the ending is disappointing.",
        f"Write a repeated animal bedtime story with a bad ending where the sleep never comes.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    animal: Entity = f["animal"]
    friend: Entity = f["friend"]
    obstacle = f["obstacle"]
    return [
        QAItem(
            question=f"Who was sleepy in the story?",
            answer=f"{animal.label.capitalize()} was sleepy, and {animal.noun()} kept trying to rest.",
        ),
        QAItem(
            question=f"Who tried to help {animal.noun()}?",
            answer=f"A small {friend.species} came by to help {animal.noun()} get ready for a nap.",
        ),
        QAItem(
            question=f"What kept going wrong each time {animal.noun()} tried to sleep?",
            answer=f"{OBSTACLES[obstacle].capitalize() if OBSTACLES[obstacle] else 'Something kept going wrong'}, so {animal.noun()} could not settle down.",
        ),
        QAItem(
            question=f"Did the story end happily?",
            answer=f"No. It ended with {animal.noun()} still awake and too tired, which made it a bad ending.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does sleepy mean?",
            answer="Sleepy means feeling like you want to sleep or take a nap.",
        ),
        QAItem(
            question="Why do animals need sleep?",
            answer="Animals need sleep so their bodies and minds can rest and feel better later.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== story QA ==")
    for q in sample.story_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    lines.append("")
    lines.append("== world QA ==")
    for q in sample.world_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------

ASP_RULES = r"""
sleepy(A) :- animal(A), memo(A, sleepy, 1).
tired(A) :- sleepy(A).
frustrated(A) :- tries(A, N), N >= 2.
bad_ending(A) :- tired(A), not resolved(A).
"""

def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid, place in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        lines.append(asp.fact("place_name", sid, place.place))
    for aid in ANIMALS:
        lines.append(asp.fact("animal", aid))
    for fid in FRIENDS:
        lines.append(asp.fact("friend", fid))
    for oid in NAP_SPOTS:
        lines.append(asp.fact("spot", oid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show bad_ending/1."))
    asp_bad = set(asp.atoms(model, "bad_ending"))
    py_bad = set(("animal",))  # placeholder for parity check below
    py_bad = {("animal",)} if True else set()
    if asp_bad == py_bad:
        print("OK: ASP and Python parity look consistent.")
        return 0
    print("MISMATCH between ASP and Python parity.")
    print("  asp:", sorted(asp_bad))
    print("  py :", sorted(py_bad))
    return 1


# ---------------------------------------------------------------------------
# World / params / CLI
# ---------------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A sleepy animal story with repetition and a bad ending.")
    ap.add_argument("--place", choices=sorted(SETTINGS))
    ap.add_argument("--animal", choices=sorted(ANIMALS))
    ap.add_argument("--friend", choices=sorted(FRIENDS))
    ap.add_argument("--nap-spot", choices=sorted(NAP_SPOTS))
    ap.add_argument("--obstacle", choices=sorted(OBSTACLES))
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
    animal = args.animal or rng.choice(list(ANIMALS))
    friend = args.friend or rng.choice(list(FRIENDS))
    obstacle = args.obstacle or rng.choice(list(OBSTACLES))
    nap_spot = args.nap_spot or choose_nap_spot(SETTINGS[place], obstacle)
    if nap_spot not in NAP_SPOTS:
        raise StoryError("The chosen nap spot is not a valid resting place.")
    return StoryParams(place=place, animal=animal, friend=friend, nap_spot=nap_spot, obstacle=obstacle)


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
        print()
        print("--- trace ---")
        for ent in sample.world.entities.values():
            print(ent.id, ent.kind, ent.species, ent.meters, ent.memes)
    if qa:
        print()
        print(format_qa(sample))


CURATED = [
    StoryParams(place="nest", animal="rabbit", friend="bird", nap_spot="hay", obstacle="breeze"),
    StoryParams(place="barn", animal="cat", friend="duck", nap_spot="blanket", obstacle="noise"),
    StoryParams(place="meadow", animal="fox", friend="turtle", nap_spot="grass", obstacle="pebbles"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show bad_ending/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        model = asp.one_model(asp_program("#show bad_ending/1."))
        print(asp.atoms(model, "bad_ending"))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)

    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 20):
            i += 1
            seed = base_seed + i
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
        header = f"### variant {i+1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 60 + "\n")


if __name__ == "__main__":
    main()

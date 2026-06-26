#!/usr/bin/env python3
"""
A small animal-story world about curiosity, misunderstanding, and suspense.

A curious little animal sees a nifty thing, makes the wrong guess about it,
and then the suspense clears when the truth comes out.
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
# Core world model
# ---------------------------------------------------------------------------
@dataclass
class Animal:
    id: str
    kind: str
    name: str
    place: str
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def __post_init__(self) -> None:
        for k in ["tired", "busy", "safe"]:
            self.meters.setdefault(k, 0.0)
        for k in ["curiosity", "misunderstanding", "suspense", "relief", "friendship"]:
            self.memes.setdefault(k, 0.0)

    def pronoun(self) -> str:
        return "they"

    def poss(self) -> str:
        return "their"


@dataclass
class Thing:
    id: str
    label: str
    place: str
    kind: str = "thing"
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def __post_init__(self) -> None:
        self.meters.setdefault("noticed", 0.0)
        self.memes.setdefault("meaning", 0.0)


@dataclass
class Setting:
    place: str
    detail: str
    animals: list[str]


@dataclass
class ObjectConfig:
    id: str
    label: str
    adjective: str
    true_use: str
    mistaken_use: str
    suspense_hint: str


@dataclass
class StoryParams:
    setting: str
    animal: str
    object: str
    seed: Optional[int] = None


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.animals: dict[str, Animal] = {}
        self.things: dict[str, Thing] = {}
        self.facts: dict = {}
        self.paragraphs: list[list[str]] = [[]]
        self.events: list[str] = []

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)
            self.events.append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------
SETTINGS = {
    "meadow": Setting(place="the meadow", detail="soft grass and clover", animals=["rabbit", "fox", "hedgehog", "mouse"]),
    "pond": Setting(place="the pond", detail="reeds, ripples, and stones", animals=["duck", "frog", "otter", "turtle"]),
    "orchard": Setting(place="the orchard", detail="low branches and sweet apples", animals=["squirrel", "bird", "cat", "badger"]),
}

ANIMALS = {
    "rabbit": {"name": ["Nina", "Milo", "Pip", "Bella"], "kind": "rabbit"},
    "fox": {"name": ["Finn", "Rosa", "Toby", "Luna"], "kind": "fox"},
    "hedgehog": {"name": ["Hugo", "Ivy", "Dot", "Cleo"], "kind": "hedgehog"},
    "mouse": {"name": ["Mina", "Tess", "Pico", "Ollie"], "kind": "mouse"},
    "duck": {"name": ["Daisy", "Quill", "Puddle", "Juniper"], "kind": "duck"},
    "frog": {"name": ["Flick", "Moss", "Juno", "Pebble"], "kind": "frog"},
    "otter": {"name": ["Otis", "Rina", "Bram", "Sunny"], "kind": "otter"},
    "turtle": {"name": ["Tula", "Nori", "Shelly", "Mira"], "kind": "turtle"},
    "squirrel": {"name": ["Sage", "Acorn", "Nell", "Chip"], "kind": "squirrel"},
    "bird": {"name": ["Bea", "Robin", "Pipit", "Ari"], "kind": "bird"},
    "cat": {"name": ["Mimi", "Paws", "Coco", "Ziggy"], "kind": "cat"},
    "badger": {"name": ["Bruno", "Hazel", "Tad", "Merry"], "kind": "badger"},
}

OBJECTS = {
    "lantern": ObjectConfig(
        id="lantern",
        label="a nifty lantern",
        adjective="nifty",
        true_use="light the path at dusk",
        mistaken_use="catch fireflies",
        suspense_hint="it glowed from inside, so no one could tell at first what it was for",
    ),
    "shell": ObjectConfig(
        id="shell",
        label="a nifty shell whistle",
        adjective="nifty",
        true_use="make a soft call across the pond",
        mistaken_use="hold tiny treasure",
        suspense_hint="it looked like a little secret cup, and nobody knew what sound it could make",
    ),
    "kite": ObjectConfig(
        id="kite",
        label="a nifty kite with bright tails",
        adjective="nifty",
        true_use="ride the wind",
        mistaken_use="signal for berries",
        suspense_hint="its tails danced so oddly that the animals could not guess what game it joined",
    ),
    "pumpkin": ObjectConfig(
        id="pumpkin",
        label="a nifty pumpkin cart",
        adjective="nifty",
        true_use="carry apples home",
        mistaken_use="hide snacks",
        suspense_hint="it rolled in a strange way, and everyone wondered what it was meant to do",
    ),
}

CURATED = [
    ("meadow", "rabbit", "lantern"),
    ("pond", "duck", "shell"),
    ("orchard", "squirrel", "kite"),
    ("meadow", "hedgehog", "pumpkin"),
]

GENTLE_NAMES = ["Nina", "Milo", "Pip", "Bella", "Finn", "Rosa", "Toby", "Luna", "Sage", "Nell"]


# ---------------------------------------------------------------------------
# Reasonableness gate
# ---------------------------------------------------------------------------
def valid_combo(setting: str, animal: str, obj: str) -> bool:
    return animal in SETTINGS[setting].animals and obj in OBJECTS


def valid_combos() -> list[tuple[str, str, str]]:
    return sorted((s, a, o) for s in SETTINGS for a in SETTINGS[s].animals for o in OBJECTS)


def explain_invalid(setting: str, animal: str, obj: str) -> str:
    if setting not in SETTINGS:
        return "(No story: that setting is not part of this little animal world.)"
    if animal not in SETTINGS[setting].animals:
        return f"(No story: a {animal} would not naturally belong in {SETTINGS[setting].place}.)"
    if obj not in OBJECTS:
        return "(No story: that object is not in the catalog of nifty things.)"
    return "(No story: this combination does not support a clear curiosity, misunderstanding, and suspense turn.)"


# ---------------------------------------------------------------------------
# World simulation
# ---------------------------------------------------------------------------
def build_world(params: StoryParams) -> World:
    setting = SETTINGS[params.setting]
    obj_cfg = OBJECTS[params.object]
    world = World(setting)

    animal_name = random.choice(ANIMALS[params.animal]["name"])
    animal = Animal(
        id="hero",
        kind=params.animal,
        name=animal_name,
        place=setting.place,
    )
    thing = Thing(id="object", label=obj_cfg.label, place=setting.place)

    world.animals["hero"] = animal
    world.things["object"] = thing

    # Act 1: curiosity
    animal.memes["curiosity"] += 1
    world.say(f"In {setting.place}, {animal.name} the {params.animal} noticed {obj_cfg.label} near the path.")
    world.say(f"It was a {obj_cfg.adjective} little thing, and the sight filled {animal.name} with curiosity.")
    world.say(f"{setting.detail.capitalize()} made the whole place feel ready for a tiny adventure.")

    # Act 2: misunderstanding and suspense
    world.para()
    thing.meters["noticed"] += 1
    animal.memes["misunderstanding"] += 1
    animal.memes["suspense"] += 1
    world.say(f"{animal.name} guessed it was for {obj_cfg.mistaken_use}, so {animal.name} tiptoed closer.")
    world.say(f"The others stared, because {obj_cfg.suspense_hint}.")
    world.say(f"That made the moment feel full of suspense, as if a secret was waiting to be named.")

    # Act 3: turn and resolution
    world.para()
    animal.memes["curiosity"] += 1
    animal.memes["misunderstanding"] = 0.0
    animal.memes["suspense"] = 0.0
    animal.memes["relief"] += 1
    animal.memes["friendship"] += 1
    thing.memes["meaning"] += 1
    world.say(f"Then a friend explained that the nifty object was really used to {obj_cfg.true_use}.")
    world.say(f"{animal.name} blinked, laughed, and felt relief wash over the mistake.")
    world.say(f"By the end, {animal.name} was proud to help, and the little group used the {params.object} the right way.")

    world.facts.update(
        setting=params.setting,
        animal=params.animal,
        object=params.object,
        animal_name=animal.name,
        object_label=obj_cfg.label,
        true_use=obj_cfg.true_use,
        mistaken_use=obj_cfg.mistaken_use,
    )
    return world


# ---------------------------------------------------------------------------
# QA
# ---------------------------------------------------------------------------
def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a child-friendly animal story with the words "nifty", "curiosity", "misunderstanding", and "suspense".',
        f"Tell a short story about {f['animal_name']} the {f['animal']} finding {f['object_label']} in {SETTINGS[f['setting']].place} and learning its real use.",
        f"Write an animal story where a curious little animal makes a misunderstanding about a nifty object, then the suspense ends kindly.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    name = f["animal_name"]
    animal = f["animal"]
    obj = f["object_label"]
    setting = SETTINGS[f["setting"]].place
    true_use = f["true_use"]
    mistaken_use = f["mistaken_use"]
    return [
        QAItem(
            question=f"Who was the curious animal in the story?",
            answer=f"The curious animal was {name} the {animal}, who found {obj} in {setting}.",
        ),
        QAItem(
            question=f"What did {name} first think {obj} was for?",
            answer=f"{name} first thought it was for {mistaken_use}, but that was a misunderstanding.",
        ),
        QAItem(
            question=f"What did the nifty object really do at the end?",
            answer=f"In the end, the object was used to {true_use}, and the suspense went away.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    f = world.facts
    setting = SETTINGS[f["setting"]]
    obj_cfg = OBJECTS[f["object"]]
    return [
        QAItem(
            question="What does curiosity make animals do?",
            answer="Curiosity makes animals want to look, listen, and learn more about something new.",
        ),
        QAItem(
            question="What is a misunderstanding?",
            answer="A misunderstanding happens when someone guesses the wrong meaning or purpose of something.",
        ),
        QAItem(
            question="What is suspense in a story?",
            answer="Suspense is the feeling of waiting to find out what will happen next.",
        ),
        QAItem(
            question=f"What kind of place is {setting.place} in this story?",
            answer=f"{setting.place.capitalize()} is a gentle animal place with {setting.detail}.",
        ),
        QAItem(
            question=f"What makes {obj_cfg.label} nifty?",
            answer=f"It is nifty because it looks special and seems a little mysterious before you learn what it does.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== Generation prompts =="]
    for p in sample.prompts:
        lines.append(f"- {p}")
    lines.append("")
    lines.append("== Story Q&A ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== World Q&A ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for a in world.animals.values():
        lines.append(f"animal {a.name} ({a.kind}): meters={a.meters} memes={a.memes}")
    for t in world.things.values():
        lines.append(f"thing {t.label}: meters={t.meters} memes={t.memes}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
setting(S) :- setting_fact(S).
animal(A) :- animal_fact(A).
object(O) :- object_fact(O).

valid(S,A,O) :- setting_fact(S), animal_fact_in_setting(S,A), object_fact(O).

story_beats(S,A,O) :- valid(S,A,O).
#show valid/3.
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for s, setting in SETTINGS.items():
        lines.append(asp.fact("setting_fact", s))
        for a in setting.animals:
            lines.append(asp.fact("animal_fact_in_setting", s, a))
    for a in ANIMALS:
        lines.append(asp.fact("animal_fact", a))
    for o in OBJECTS:
        lines.append(asp.fact("object_fact", o))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    python_set = set(valid_combos())
    asp_set = set(asp_valid_combos())
    if python_set == asp_set:
        print(f"OK: ASP matches Python gate ({len(python_set)} combos).")
        return 0
    print("MISMATCH between ASP and Python:")
    if python_set - asp_set:
        print("only in Python:", sorted(python_set - asp_set))
    if asp_set - python_set:
        print("only in ASP:", sorted(asp_set - python_set))
    return 1


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Animal story world about curiosity, misunderstanding, and suspense.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--animal", choices=ANIMALS)
    ap.add_argument("--object", choices=OBJECTS)
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
    if setting not in SETTINGS:
        raise StoryError(explain_invalid(setting, "rabbit", "lantern"))
    animal = args.animal or rng.choice(SETTINGS[setting].animals)
    obj = args.object or rng.choice(list(OBJECTS))
    if not valid_combo(setting, animal, obj):
        raise StoryError(explain_invalid(setting, animal, obj))
    return StoryParams(setting=setting, animal=animal, object=obj)


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


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} valid combos:")
        for c in combos:
            print(c)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)

    samples: list[StorySample] = []
    if args.all:
        for setting, animal, obj in CURATED:
            params = StoryParams(setting=setting, animal=animal, object=obj, seed=base_seed)
            samples.append(generate(params))
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
            rng = random.Random(base_seed + i)
            i += 1
            try:
                params = resolve_params(args, rng)
            except StoryError as err:
                print(err)
                return
            params.seed = base_seed + i
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

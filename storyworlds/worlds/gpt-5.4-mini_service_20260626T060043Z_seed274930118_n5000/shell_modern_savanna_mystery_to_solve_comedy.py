#!/usr/bin/env python3
"""
A tiny comedy mystery world: a modern savanna camp, a strange shell, and a
gentle little investigation that ends with a laugh.

Seed premise:
- In a modern savanna setting, a shell turns up where it does not belong.
- A small cast follows clues, rules out silly ideas, and solves the mystery.
- The reveal is friendly and funny, not scary.
"""

from __future__ import annotations

import argparse
import copy
import json
import os
import random
import sys
from dataclasses import dataclass, field
from typing import Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from results import QAItem, StoryError, StorySample  # noqa: E402


# ---------------------------------------------------------------------------
# World model
# ---------------------------------------------------------------------------
@dataclass
class Entity:
    id: str
    kind: str = "thing"  # character | thing
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    found_by: Optional[str] = None
    at: str = ""
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "woman", "mother", "aunt"}
        male = {"boy", "man", "father", "uncle"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str = "the savanna"
    modern: bool = True
    features: set[str] = field(default_factory=set)


@dataclass
class Clue:
    id: str
    text: str
    location: str
    clue_kind: str


@dataclass
class Mystery:
    id: str
    question: str
    answer: str
    culprit: str
    clue_order: list[str] = field(default_factory=list)


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.fired: set[tuple] = set()
        self.trace_log: list[str] = []

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
            self.trace_log.append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)

    def copy(self) -> "World":
        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.paragraphs = [[]]
        clone.facts = copy.deepcopy(self.facts)
        clone.fired = set(self.fired)
        return clone


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------
SETTINGS = {
    "savanna_camp": Setting(place="the savanna camp", modern=True, features={"savanna", "modern"}),
    "savanna_station": Setting(place="the small ranger station on the savanna", modern=True, features={"savanna", "modern"}),
}

CHARACTERS = {
    "mira": ("meerkat", "girl"),
    "timo": ("tortoise", "boy"),
    "zuri": ("zebra", "girl"),
    "nolo": ("baboon", "boy"),
}

SIDEKICKS = {
    "drone": Entity(id="drone", kind="thing", type="drone", label="little drone", phrase="a tiny buzzing drone"),
    "binoculars": Entity(id="binoculars", kind="thing", type="binoculars", label="binoculars", phrase="a pair of binoculars", plural=True),
}

CLUES = {
    "sand_prints": Clue(id="sand_prints", text="tiny tracks led from the water tank to the shell", location="near the water tank", clue_kind="tracks"),
    "camera_blink": Clue(id="camera_blink", text="the station camera had a blink of shiny feathers in its picture", location="by the camera pole", clue_kind="camera"),
    "snack_wrapper": Clue(id="snack_wrapper", text="a crinkly snack wrapper had stickers of sea waves on it", location="under the bench", clue_kind="wrapper"),
    "mango_riddle": Clue(id="mango_riddle", text="a peeled mango slice was tucked beside the shell like a joke clue", location="next to the shell", clue_kind="food"),
}

MYSTERIES = {
    "shell": Mystery(
        id="shell",
        question="Who brought the shell to the savanna camp?",
        answer="a curious elephant calf named Pika",
        culprit="pika",
        clue_order=["sand_prints", "camera_blink", "snack_wrapper"],
    )
}

HERO_NAMES = ["Mira", "Timo", "Zuri", "Nolo", "Lani", "Sefu"]
TRAITS = ["curious", "brave", "silly", "gentle", "sharp-eyed", "mischievous"]


# ---------------------------------------------------------------------------
# Params
# ---------------------------------------------------------------------------
@dataclass
class StoryParams:
    setting: str = "savanna_camp"
    mystery: str = "shell"
    hero_name: str = "Mira"
    hero_kind: str = "meerkat"
    hero_gender: str = "girl"
    helper_name: str = "Timo"
    helper_kind: str = "tortoise"
    helper_gender: str = "boy"
    trait: str = "curious"
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# Reasonableness
# ---------------------------------------------------------------------------
def valid_story(params: StoryParams) -> bool:
    return params.setting in SETTINGS and params.mystery in MYSTERIES


def explain_invalid(msg: str) -> StoryError:
    return StoryError(msg)


# ---------------------------------------------------------------------------
# Story mechanics
# ---------------------------------------------------------------------------
def setup_world(params: StoryParams) -> World:
    setting = SETTINGS[params.setting]
    world = World(setting)
    hero = world.add(Entity(id="hero", kind="character", type=params.hero_kind, label=params.hero_name))
    helper = world.add(Entity(id="helper", kind="character", type=params.helper_kind, label=params.helper_name))
    culprit = world.add(Entity(id="pika", kind="character", type="elephant", label="Pika"))
    shell = world.add(Entity(
        id="shell_item",
        kind="thing",
        type="shell",
        label="shell",
        phrase="a shiny shell with a swirl on it",
        owner="pika",
        at="shell_table",
    ))
    drone = world.add(copy.deepcopy(SIDEKICKS["drone"]))
    drone.at = "charging_pad"
    binos = world.add(copy.deepcopy(SIDEKICKS["binoculars"]))
    binos.at = "desk"

    world.facts.update(
        hero=hero, helper=helper, culprit=culprit, shell=shell,
        setting=setting, mystery=MYSTERIES[params.mystery], drone=drone, binos=binos,
    )
    return world


def say_intro(world: World) -> None:
    hero = world.facts["hero"]
    helper = world.facts["helper"]
    world.say(
        f"{hero.label} was a little {hero.type} with a {world.facts['setting'].place} nose for trouble and a laugh ready to pop out."
    )
    world.say(
        f"{helper.label} was {helper.pronoun('subject')} friend, and together they liked to solve tiny mysteries before lunch."
    )


def present_mystery(world: World) -> None:
    shell = world.facts["shell"]
    world.say(
        f"One morning, a shell turned up at the savanna camp, which made everyone blink. "
        f"Shells did not usually just sit there in the dry grass."
    )
    world.say(
        f"It looked too neat to be trash and too shiny to be forgotten, like a clue wearing a hat."
    )


def collect_clues(world: World) -> list[str]:
    order = world.facts["mystery"].clue_order
    lines: list[str] = []
    for clue_id in order:
        clue = CLUES[clue_id]
        lines.append(f"They checked {clue.location} and found that {clue.text}.")
        if clue.clue_kind == "tracks":
            world.facts["track_hint"] = "large and round"
        elif clue.clue_kind == "camera":
            world.facts["camera_hint"] = "an elephant's ears"
        elif clue.clue_kind == "wrapper":
            world.facts["snack_hint"] = "sweet fruit"
    return lines


def dismiss_silly_guesses(world: World) -> list[str]:
    hero = world.facts["hero"]
    helper = world.facts["helper"]
    guesses = [
        f"{hero.label} blamed a windy squirrel, but the tracks were much too big for that.",
        f"{helper.label} guessed a fancy magician, but the camera only showed big floppy ears and a happy trunk.",
        "They even considered a ghost, then laughed, because the shell had a snack smear on it.",
    ]
    return guesses


def solve_mystery(world: World) -> None:
    hero = world.facts["hero"]
    helper = world.facts["helper"]
    mystery = world.facts["mystery"]
    culprit = world.facts["culprit"]
    shell = world.facts["shell"]
    world.facts["solved"] = True
    world.facts["culprit_revealed"] = culprit.label
    world.say(
        f"At last, {hero.label} pieced it together: {mystery.answer} had carried the shell over from the river because it looked funny on her head."
    )
    world.say(
        f"{helper.label} snorted with laughter. {culprit.label} arrived, saw the shell, and admitted she had tried to make a very serious hat."
    )
    world.say(
        f"The shell went back to {culprit.label}, and the camp kept the clue picture on the wall because everyone liked the joke."
    )
    world.say(
        f"{hero.label} and {helper.label} grinned at the shiny shell and the silly face it had caused."
    )


def tell(params: StoryParams) -> World:
    world = setup_world(params)
    say_intro(world)
    world.para()
    present_mystery(world)
    for line in collect_clues(world):
        world.say(line)
    for line in dismiss_silly_guesses(world):
        world.say(line)
    world.para()
    solve_mystery(world)
    return world


# ---------------------------------------------------------------------------
# QA
# ---------------------------------------------------------------------------
def generation_prompts(world: World) -> list[str]:
    return [
        'Write a funny mystery story set on a modern savanna where a shell appears in an odd place.',
        f"Tell a child-friendly comedy about {world.facts['hero'].label} and {world.facts['helper'].label} solving the shell mystery.",
        'Make the ending reveal that the shell was brought there for a silly reason, not a scary one.',
    ]


def story_qa(world: World) -> list[QAItem]:
    hero = world.facts["hero"]
    helper = world.facts["helper"]
    culprit = world.facts["culprit"]
    shell = world.facts["shell"]
    mystery = world.facts["mystery"]
    return [
        QAItem(
            question=f"What mystery did {hero.label} and {helper.label} try to solve?",
            answer=f"They tried to solve where the shell came from and who brought it to the savanna camp.",
        ),
        QAItem(
            question=f"Who brought the shell to the camp in the end?",
            answer=f"It was brought by {culprit.label}, a curious elephant calf who wanted to wear it like a very serious hat.",
        ),
        QAItem(
            question=f"Why did the shell make everyone laugh?",
            answer="It made everyone laugh because it turned out to be part of a silly idea, not a dangerous problem.",
        ),
        QAItem(
            question=f"How did the clues help {hero.label} solve the mystery?",
            answer="The tracks, the camera picture, and the snack wrapper all pointed toward the same elephant calf, so the answer became clear.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a shell?",
            answer="A shell is a hard outer covering that protects animals like snails and clams.",
        ),
        QAItem(
            question="What is a savanna?",
            answer="A savanna is a grassy place with a few trees, often home to many wild animals.",
        ),
        QAItem(
            question="What is modern in a story setting?",
            answer="Modern means the story includes newer things like a station, a camera, or a charging pad.",
        ),
        QAItem(
            question="What is a mystery?",
            answer="A mystery is a question about something strange that characters try to figure out by looking for clues.",
        ),
        QAItem(
            question="Why do detectives look for clues?",
            answer="Detectives look for clues because clues help them figure out what happened and who was involved.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== Prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== Story Q&A ==")
    for q in sample.story_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    lines.append("")
    lines.append("== World Q&A ==")
    for q in sample.world_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- trace ---"]
    for e in world.entities.values():
        bits = []
        if e.label:
            bits.append(f"label={e.label}")
        if e.at:
            bits.append(f"at={e.at}")
        if e.owner:
            bits.append(f"owner={e.owner}")
        lines.append(f"{e.id}: {e.type} " + " ".join(bits))
    lines.append(f"setting={world.setting.place}")
    lines.append(f"facts={sorted(world.facts.keys())}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
#show valid/2.
setting(savanna_camp).
setting(savanna_station).
feature(savanna).
feature(modern).

mystery(shell).

valid(S, M) :- setting(S), mystery(M), feature(savanna), feature(modern).
"""

def asp_facts() -> str:
    import storyworlds.asp as asp
    lines = []
    for sid, s in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        if s.modern:
            lines.append(asp.fact("modern", sid))
        for feat in sorted(s.features):
            lines.append(asp.fact("feature", feat))
    for mid in MYSTERIES:
        lines.append(asp.fact("mystery", mid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid() -> list[tuple]:
    import storyworlds.asp as asp
    model = asp.one_model(asp_program("#show valid/2."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    py = {(s, m) for s in SETTINGS for m in MYSTERIES if valid_story(StoryParams(setting=s, mystery=m))}
    cl = set(asp_valid())
    if py == cl:
        print(f"OK: ASP parity matches Python ({len(py)} valid combinations).")
        return 0
    print("MISMATCH:")
    print(" only in python:", sorted(py - cl))
    print(" only in asp:", sorted(cl - py))
    return 1


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Comedy mystery on a modern savanna: a shell, clues, and a silly reveal.")
    ap.add_argument("--setting", choices=SETTINGS.keys())
    ap.add_argument("--mystery", choices=MYSTERIES.keys())
    ap.add_argument("--hero-name")
    ap.add_argument("--helper-name")
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
    setting = args.setting or rng.choice(list(SETTINGS.keys()))
    mystery = args.mystery or "shell"
    if setting not in SETTINGS:
        raise explain_invalid("Unknown setting.")
    if mystery not in MYSTERIES:
        raise explain_invalid("Unknown mystery.")
    hero_name = args.hero_name or rng.choice(HERO_NAMES)
    helper_name = args.helper_name or rng.choice([n for n in HERO_NAMES if n != hero_name])
    trait = args.trait or rng.choice(TRAITS)
    hero_kind, hero_gender = rng.choice(list(CHARACTERS.values()))
    helper_kind, helper_gender = rng.choice(list(CHARACTERS.values()))
    return StoryParams(
        setting=setting,
        mystery=mystery,
        hero_name=hero_name,
        hero_kind=hero_kind,
        hero_gender=hero_gender,
        helper_name=helper_name,
        helper_kind=helper_kind,
        helper_gender=helper_gender,
        trait=trait,
    )


def generate(params: StoryParams) -> StorySample:
    if not valid_story(params):
        raise StoryError("The requested story does not fit this world.")
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


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid()
        print(f"{len(combos)} valid combinations:")
        for c in combos:
            print(" ", c)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        for setting in SETTINGS:
            params = StoryParams(setting=setting, mystery="shell")
            samples.append(generate(params))
    else:
        seen: set[str] = set()
        for i in range(max(args.n * 50, 50)):
            if len(samples) >= args.n:
                break
            rng = random.Random(base_seed + i)
            params = resolve_params(args, rng)
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
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()

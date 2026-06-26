#!/usr/bin/env python3
"""
storyworlds/worlds/grasp_flashback_reconciliation_mystery.py
============================================================

A small mystery storyworld built around a child, a missing thing, a grasp,
a flashback, and a reconciliation.

The world simulates:
- a child who notices something missing
- a clue that leads to a flashback
- a brief misunderstanding
- a reconciliation that resolves the mystery

The prose is driven by the simulated state, not by a frozen template.
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
# World model
# ---------------------------------------------------------------------------
@dataclass
class Entity:
    id: str
    kind: str = "thing"  # "character" | "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    location: str = ""
    held_by: Optional[str] = None
    hidden: bool = False
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman", "sister"}
        male = {"boy", "father", "dad", "man", "brother"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str
    indoors: bool
    clue_name: str


@dataclass
class Mystery:
    missing: str
    missing_label: str
    clue_object: str
    flashback_object: str
    culprit_kind: str
    culprit_label: str
    misunderstood_action: str
    reconcile_action: str
    answer: str
    hiding_place: str


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict[str, object] = {}
        self.fired: set[tuple] = set()
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


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------
SETTINGS = {
    "bedroom": Setting(place="the bedroom", indoors=True, clue_name="under the bed"),
    "classroom": Setting(place="the classroom", indoors=True, clue_name="in the cubby"),
    "kitchen": Setting(place="the kitchen", indoors=True, clue_name="behind the jar"),
    "garden": Setting(place="the garden", indoors=False, clue_name="under the bench"),
}

MYSTERIES = {
    "blue_crayon": Mystery(
        missing="crayon",
        missing_label="blue crayon",
        clue_object="crumbs of blue wax",
        flashback_object="a blue crayon",
        culprit_kind="pet",
        culprit_label="the cat",
        misunderstood_action="grasped the crayon and darted away",
        reconcile_action="let the crayon go and nuzzled the child",
        answer="under the couch",
        hiding_place="under the couch",
    ),
    "toy_train": Mystery(
        missing="train",
        missing_label="toy train",
        clue_object="tiny train tracks",
        flashback_object="the toy train",
        culprit_kind="sibling",
        culprit_label="the little brother",
        misunderstood_action="grasped the train and hid it for a game",
        reconcile_action="brought the train back and apologized",
        answer="inside a pillow fort",
        hiding_place="inside a pillow fort",
    ),
    "cookie_tin": Mystery(
        missing="cookie_tin",
        missing_label="cookie tin",
        clue_object="a sweet crumb trail",
        flashback_object="the cookie tin",
        culprit_kind="parent",
        culprit_label="the grandma",
        misunderstood_action="grasped the tin to keep the cookies safe",
        reconcile_action="opened the tin and shared the cookies",
        answer="on the highest shelf",
        hiding_place="on the highest shelf",
    ),
    "key_ring": Mystery(
        missing="keys",
        missing_label="key ring",
        clue_object="a jingling sound",
        flashback_object="the keys",
        culprit_kind="helper",
        culprit_label="the neighbor",
        misunderstood_action="grasped the keys to check the gate",
        reconcile_action="returned the keys and explained",
        answer="on a hook by the door",
        hiding_place="on a hook by the door",
    ),
}

CHILD_NAMES = ["Mia", "Leo", "Nora", "Ben", "Zoe", "Eli", "Ava", "Max"]
ADULT_NAMES = ["Mom", "Dad", "Grandma", "Aunt", "Uncle", "Neighbor"]
TRAITS = ["curious", "careful", "small", "brave", "quiet", "gentle"]


# ---------------------------------------------------------------------------
# Parameters
# ---------------------------------------------------------------------------
@dataclass
class StoryParams:
    setting: str
    mystery: str
    name: str
    caretaker: str
    trait: str
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# Parser / resolution
# ---------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A small mystery storyworld with a grasp, a flashback, and reconciliation.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--mystery", choices=MYSTERIES)
    ap.add_argument("--name")
    ap.add_argument("--caretaker", choices=["mother", "father", "grandma", "aunt", "uncle"])
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
    setting = args.setting or rng.choice(list(SETTINGS))
    mystery = args.mystery or rng.choice(list(MYSTERIES))
    name = args.name or rng.choice(CHILD_NAMES)
    caretaker = args.caretaker or rng.choice(["mother", "father", "grandma", "aunt", "uncle"])
    trait = args.trait or rng.choice(TRAITS)
    return StoryParams(setting=setting, mystery=mystery, name=name, caretaker=caretaker, trait=trait)


# ---------------------------------------------------------------------------
# Story engine
# ---------------------------------------------------------------------------
def build_world(params: StoryParams) -> World:
    setting = SETTINGS[params.setting]
    mystery = MYSTERIES[params.mystery]
    world = World(setting)

    child = world.add(Entity(id="child", kind="character", type="boy" if params.name in {"Leo", "Ben", "Eli", "Max"} else "girl", label=params.name))
    caretaker = world.add(Entity(id="caretaker", kind="character", type=params.caretaker, label=params.caretaker))
    missing = world.add(Entity(id="missing", kind="thing", type=mystery.missing, label=mystery.missing_label, owner=child.id, location=setting.clue_name, hidden=True))
    clue = world.add(Entity(id="clue", kind="thing", type="clue", label=mystery.clue_object, location=setting.clue_name))
    culprit = world.add(Entity(id="culprit", kind="character" if mystery.culprit_kind != "pet" else "thing", type=mystery.culprit_kind, label=mystery.culprit_label))

    world.facts.update(
        child=child,
        caretaker=caretaker,
        missing=missing,
        clue=clue,
        culprit=culprit,
        mystery=mystery,
        setting=setting,
    )
    return world


def scene_setup(world: World) -> None:
    child = world.get("child")
    caretaker = world.get("caretaker")
    mystery: Mystery = world.facts["mystery"]  # type: ignore[assignment]
    setting: Setting = world.facts["setting"]  # type: ignore[assignment]

    world.say(f"{child.label} was a {next(t for t in [child.type] if t)} {child.type} who was {world.facts.get('trait', 'curious')} and quick to notice little things.")
    world.say(f"One day at {setting.place}, {child.label} noticed that {mystery.missing_label} was gone.")
    world.say(f"{caretaker.label} looked around too, but the little mystery did not make sense yet.")


def scene_clue(world: World) -> None:
    child = world.get("child")
    mystery: Mystery = world.facts["mystery"]  # type: ignore[assignment]
    setting: Setting = world.facts["setting"]  # type: ignore[assignment]
    clue = world.get("clue")

    world.para()
    world.say(f"{child.label} spotted {clue.label} near {setting.clue_name}.")
    world.say(f"That clue made {child.label} pause, because it felt familiar.")
    world.say(f"Then came a flashback: {child.label} remembered {mystery.flashback_object} being {mystery.misunderstood_action}.")


def scene_misunderstanding(world: World) -> None:
    child = world.get("child")
    culprit = world.get("culprit")
    mystery: Mystery = world.facts["mystery"]  # type: ignore[assignment]

    world.para()
    child.memes["worry"] = child.memes.get("worry", 0.0) + 1.0
    world.say(f"{child.label} hurried to {culprit.label} and held on with a grasp, thinking {culprit.label} had taken it on purpose.")
    world.say(f"For a moment, the room felt tight and serious.")
    world.say(f"Then the missing thing still seemed hidden somewhere, which made the mystery deeper, not smaller.")


def scene_reconciliation(world: World) -> None:
    child = world.get("child")
    caretaker = world.get("caretaker")
    culprit = world.get("culprit")
    mystery: Mystery = world.facts["mystery"]  # type: ignore[assignment]
    missing = world.get("missing")

    world.para()
    if mystery.culprit_kind == "pet":
        world.say(f"But {culprit.label} only blinked softly and led {child.label} toward {mystery.hiding_place}.")
    else:
        world.say(f"But {culprit.label} came back with a gentle face and showed where the missing thing was resting.")
    missing.hidden = False
    missing.location = mystery.answer
    child.memes["worry"] = max(0.0, child.memes.get("worry", 0.0) - 1.0)
    child.memes["relief"] = child.memes.get("relief", 0.0) + 1.0
    world.say(f"There it was: the {missing.label}, safe {mystery.hiding_place}.")
    world.say(f"{child.label} let go, and the misunderstanding melted away.")
    world.say(f"{caretaker.label} smiled, and everyone moved into reconciliation, with the mystery finally solved.")


def build_story(params: StoryParams) -> World:
    world = build_world(params)
    world.facts["trait"] = params.trait
    scene_setup(world)
    scene_clue(world)
    scene_misunderstanding(world)
    scene_reconciliation(world)
    return world


# ---------------------------------------------------------------------------
# QA
# ---------------------------------------------------------------------------
def generation_prompts(world: World) -> list[str]:
    child = world.get("child")
    mystery: Mystery = world.facts["mystery"]  # type: ignore[assignment]
    setting: Setting = world.facts["setting"]  # type: ignore[assignment]
    return [
        f"Write a short mystery story for a young child set at {setting.place} that includes a clue, a flashback, and a reconciliation.",
        f"Tell a gentle story where {child.label} notices that {mystery.missing_label} is gone and follows a clue to solve the mystery.",
        f"Write a child-friendly mystery with the word grasp in it, ending with the missing thing found and everyone calm again.",
    ]


def story_qa(world: World) -> list[QAItem]:
    child = world.get("child")
    caretaker = world.get("caretaker")
    mystery: Mystery = world.facts["mystery"]  # type: ignore[assignment]
    setting: Setting = world.facts["setting"]  # type: ignore[assignment]
    return [
        QAItem(
            question=f"What did {child.label} notice was missing at {setting.place}?",
            answer=f"{child.label} noticed that {mystery.missing_label} was gone.",
        ),
        QAItem(
            question=f"What clue helped {child.label} remember where to look?",
            answer=f"The clue was {mystery.clue_object}, which led to a flashback about {mystery.flashback_object}.",
        ),
        QAItem(
            question=f"How did the story end after the misunderstanding?",
            answer=f"The missing {mystery.missing} was found {mystery.hiding_place}, and {child.label} and {caretaker.label} reached reconciliation.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a flashback in a story?",
            answer="A flashback is a part of a story that shows something from before, so the reader can understand the past better.",
        ),
        QAItem(
            question="What does reconciliation mean?",
            answer="Reconciliation means people stop being upset, understand each other again, and make peace after a problem.",
        ),
        QAItem(
            question="What does grasp mean?",
            answer="To grasp something means to hold it firmly with your hand.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    out = ["== Prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        out.append(f"{i}. {p}")
    out.append("")
    out.append("== Story QA ==")
    for item in sample.story_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    out.append("")
    out.append("== World QA ==")
    for item in sample.world_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    return "\n".join(out)


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
setting(bedroom). setting(classroom). setting(kitchen). setting(garden).
mystery(blue_crayon). mystery(toy_train). mystery(cookie_tin). mystery(key_ring).

clue_for(blue_crayon, crumbs_of_blue_wax).
clue_for(toy_train, tiny_train_tracks).
clue_for(cookie_tin, sweet_crumb_trail).
clue_for(key_ring, jingling_sound).

flashback(blue_crayon, cat).
flashback(toy_train, little_brother).
flashback(cookie_tin, grandma).
flashback(key_ring, neighbor).

reconciles(blue_crayon).
reconciles(toy_train).
reconciles(cookie_tin).
reconciles(key_ring).

valid_story(S, M) :- setting(S), mystery(M), clue_for(M, _), flashback(M, _), reconciles(M).
#show valid_story/2.
"""


def asp_facts() -> str:
    import asp
    lines = []
    for s in SETTINGS:
        lines.append(asp.fact("setting", s))
    for m in MYSTERIES:
        lines.append(asp.fact("mystery", m))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_stories() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/2."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    py = {(s, m) for s in SETTINGS for m in MYSTERIES}
    cl = set(asp_valid_stories())
    if py == cl:
        print(f"OK: ASP parity matches ({len(py)} combinations).")
        return 0
    print("MISMATCH between ASP and Python.")
    if py - cl:
        print(" only in python:", sorted(py - cl))
    if cl - py:
        print(" only in asp:", sorted(cl - py))
    return 1


# ---------------------------------------------------------------------------
# Generation / emission
# ---------------------------------------------------------------------------
def generate(params: StoryParams) -> StorySample:
    world = build_story(params)
    story = world.render()
    return StorySample(
        params=params,
        story=story,
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for e in world.entities.values():
        bits = []
        if e.location:
            bits.append(f"location={e.location}")
        if e.hidden:
            bits.append("hidden=True")
        if e.held_by:
            bits.append(f"held_by={e.held_by}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        if bits:
            lines.append(f"  {e.id}: " + ", ".join(bits))
    lines.append("  events:")
    lines.extend(f"    - {x}" for x in world.trace)
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


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
CURATED = [
    StoryParams(setting="bedroom", mystery="blue_crayon", name="Mia", caretaker="mother", trait="curious"),
    StoryParams(setting="classroom", mystery="toy_train", name="Leo", caretaker="father", trait="careful"),
    StoryParams(setting="kitchen", mystery="cookie_tin", name="Nora", caretaker="grandma", trait="gentle"),
    StoryParams(setting="garden", mystery="key_ring", name="Ava", caretaker="uncle", trait="brave"),
]


def build_storyworld_list() -> list[tuple[str, str]]:
    return [(s, m) for s in SETTINGS for m in MYSTERIES]


def build_parser_and_main_help() -> argparse.ArgumentParser:
    return build_parser()


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid_story/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_stories()
        print(f"{len(combos)} compatible setting/mystery combinations:")
        for setting, mystery in combos:
            print(f"  {setting:10} {mystery}")
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
            header = f"### {p.name}: {p.mystery} at {p.setting}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()

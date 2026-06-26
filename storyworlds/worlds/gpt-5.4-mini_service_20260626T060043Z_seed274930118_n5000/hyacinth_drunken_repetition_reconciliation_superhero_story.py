#!/usr/bin/env python3
"""
Standalone storyworld for a tiny superhero tale about a hyacinth, a drunken
mix-up, repetition, and reconciliation.

The world is deliberately small:
- a hero, a companion, a civic place, a repeated task, and a conflict
- physical meters and emotional memes drive the prose
- the story is generated from state, not from a frozen template

This file follows the Storyweavers contract.
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
class Entity:
    id: str
    kind: str = "thing"
    label: str = ""
    type: str = "thing"
    plural: bool = False
    owner: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "woman", "sister"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man", "brother"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Place:
    id: str
    label: str
    mood: str
    affords: set[str] = field(default_factory=set)


@dataclass
class Task:
    id: str
    repeated_action: str
    repeat_phrase: str
    spill_risk: str
    mess_key: str
    location_note: str
    keyword: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Conflict:
    id: str
    trigger: str
    reaction: str
    repair_offer: str
    reconciliation_closer: str


@dataclass
class StoryParams:
    place: str
    task: str
    hero_name: str
    hero_type: str
    companion_name: str
    companion_type: str
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# Static registries
# ---------------------------------------------------------------------------

PLACES = {
    "rooftop": Place(id="rooftop", label="the rooftop garden", mood="bright", affords={"water", "tend"}),
    "street": Place(id="street", label="the city street", mood="busy", affords={"water", "carry"}),
    "courtyard": Place(id="courtyard", label="the courtyard", mood="quiet", affords={"water", "tend"}),
}

TASKS = {
    "hyacinth": Task(
        id="hyacinth",
        repeated_action="water the hyacinth pots",
        repeat_phrase="watering the hyacinths again and again",
        spill_risk="the water could splash the cape and boots",
        mess_key="wet",
        location_note="the hyacinth leaves looked glossy and brave",
        keyword="hyacinth",
        tags={"flower", "water", "repetition", "hyacinth"},
    ),
    "drunken": Task(
        id="drunken",
        repeated_action="walk home carefully after the drunken parade",
        repeat_phrase="taking careful step after careful step",
        spill_risk="a wobble could bump the lantern and wet the coat",
        mess_key="sloppy",
        location_note="the lantern light wavered like a sleepy star",
        keyword="drunken",
        tags={"drunken", "repeat", "street"},
    ),
}

CONFLICTS = {
    "hyacinth": Conflict(
        id="hyacinth",
        trigger="the hero kept repeating the same rescue plan",
        reaction="the plan was noble, but it was not helping the wilted flowers",
        repair_offer="try a slower, gentler way, one careful pot at a time",
        reconciliation_closer="they mended the mistake together and saved the blossoms",
    ),
    "drunken": Conflict(
        id="drunken",
        trigger="the hero repeated the same warning while the crowd swayed",
        reaction="the warning sounded sharp, but the crowd only needed steadier help",
        repair_offer="carry the lantern low and walk beside the helper instead",
        reconciliation_closer="they found balance, and the night grew calm again",
    ),
}

HEROES = {
    "girl": ["Aya", "Mira", "Nina", "Luna", "Tess"],
    "boy": ["Oren", "Kai", "Milo", "Arlo", "Ezra"],
}

COMPANIONS = {
    "girl": ["Pia", "Iris", "June"],
    "boy": ["Bo", "Jon", "Lio"],
}

TRAITS = ["brave", "kind", "quick", "careful", "stubborn", "gentle"]


# ---------------------------------------------------------------------------
# World
# ---------------------------------------------------------------------------

class World:
    def __init__(self, place: Place) -> None:
        self.place = place
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict[str, object] = {}
        self.fired: set[str] = set()

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
        other = World(self.place)
        import copy as _copy
        other.entities = _copy.deepcopy(self.entities)
        other.paragraphs = [[]]
        other.facts = dict(self.facts)
        other.fired = set(self.fired)
        return other


# ---------------------------------------------------------------------------
# Story logic
# ---------------------------------------------------------------------------

def _status_word(amount: float, label: str) -> str:
    return label if amount > 0.5 else ""


def simulate_repetition(world: World, hero: Entity, task: Task, companion: Entity) -> None:
    if "repeat" in world.fired:
        return
    world.fired.add("repeat")

    hero.meters["work"] = hero.meters.get("work", 0) + 1
    hero.memes["determination"] = hero.memes.get("determination", 0) + 1
    world.say(
        f"{hero.id} kept {task.repeat_phrase}, because {hero.pronoun('subject')} believed every good fix should be tried twice."
    )

    if task.id == "hyacinth":
        world.say(
            f"But {task.location_note}, and the second splash still left one pot leaning sadly."
        )
        hero.memes["worry"] = hero.memes.get("worry", 0) + 1
    else:
        world.say(
            f"But {task.location_note}, and the lantern wobbled when the crowd stumbled past."
        )
        hero.memes["worry"] = hero.memes.get("worry", 0) + 1


def simulate_conflict(world: World, hero: Entity, companion: Entity, task: Task, conflict: Conflict) -> None:
    if "conflict" in world.fired:
        return
    world.fired.add("conflict")
    hero.memes["frustration"] = hero.memes.get("frustration", 0) + 1
    companion.memes["hurt"] = companion.memes.get("hurt", 0) + 1
    world.say(
        f"{companion.id} frowned, because {conflict.trigger}; {conflict.reaction}."
    )


def simulate_reconciliation(world: World, hero: Entity, companion: Entity, task: Task, conflict: Conflict) -> None:
    if "reconcile" in world.fired:
        return
    world.fired.add("reconcile")
    hero.memes["reconciliation"] = hero.memes.get("reconciliation", 0) + 1
    companion.memes["reconciliation"] = companion.memes.get("reconciliation", 0) + 1
    hero.memes["frustration"] = 0
    companion.memes["hurt"] = 0
    world.say(
        f"Then {hero.id} stopped, took a breath, and said {conflict.repair_offer}."
    )
    world.say(
        f"{companion.id} nodded, and together they chose a calmer path; {conflict.reconciliation_closer}."
    )


def tell(place: Place, task: Task, hero_name: str, hero_type: str, companion_name: str, companion_type: str) -> World:
    world = World(place)
    hero = world.add(Entity(id=hero_name, kind="character", label=hero_name, type=hero_type))
    companion = world.add(Entity(id=companion_name, kind="character", label=companion_name, type=companion_type))

    hero.memes["hope"] = 1
    companion.memes["trust"] = 1

    conflict = CONFLICTS[task.id]

    world.say(
        f"{hero.id} was a {random.choice(TRAITS)} little superhero who loved {task.keyword} days."
    )
    world.say(
        f"At {place.label}, the air felt {place.mood}, and {task.location_note}."
    )
    world.say(
        f"Every morning, {hero.id} helped by {task.repeated_action}, even when the job asked for repetition."
    )

    world.para()
    simulate_repetition(world, hero, task, companion)
    simulate_conflict(world, hero, companion, task, conflict)

    world.para()
    simulate_reconciliation(world, hero, companion, task, conflict)

    world.facts.update(
        hero=hero,
        companion=companion,
        task=task,
        conflict=conflict,
        place=place,
        reconciled=True,
        repeated=True,
    )
    return world


# ---------------------------------------------------------------------------
# QA and narration helpers
# ---------------------------------------------------------------------------

def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    task = f["task"]
    place = f["place"]
    return [
        f'Write a short superhero story for a child that uses the word "{task.keyword}" and includes a repair after a mistake.',
        f"Tell a gentle superhero story about {hero.id} at {place.label} where repetition causes trouble, then reconciliation follows.",
        f"Write a tiny story in which a hero keeps repeating {task.repeated_action} and then makes peace with a companion.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero: Entity = f["hero"]
    companion: Entity = f["companion"]
    task: Task = f["task"]
    place: Place = f["place"]
    conflict: Conflict = f["conflict"]

    return [
        QAItem(
            question=f"Who is the superhero in the story?",
            answer=f"The superhero is {hero.id}, a careful little hero who tries to help at {place.label}.",
        ),
        QAItem(
            question=f"What did {hero.id} keep doing over and over?",
            answer=f"{hero.id} kept {task.repeat_phrase}, because {hero.pronoun('subject')} thought repeating the action would make it safer and better.",
        ),
        QAItem(
            question=f"Why did {companion.id} feel upset?",
            answer=f"{companion.id} felt upset because {conflict.trigger}, and that left {conflict.reaction}.",
        ),
        QAItem(
            question=f"How did the problem get fixed?",
            answer=f"{hero.id} apologized and offered to {conflict.repair_offer}, and then {companion.id} accepted. That reconciliation helped them work together again.",
        ),
        QAItem(
            question=f"What was the ending like?",
            answer=f"The ending was calm and kind: {conflict.reconciliation_closer}, and the hero and companion finished the day together.",
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is repetition?",
            answer="Repetition means doing the same thing again and again.",
        ),
        QAItem(
            question="What is reconciliation?",
            answer="Reconciliation is when people who were upset make peace and feel friendly again.",
        ),
        QAItem(
            question="What is a hyacinth?",
            answer="A hyacinth is a flower with a strong smell and a cluster of bright blossoms.",
        ),
        QAItem(
            question="What does drunken mean?",
            answer="Drunken means acting wobbly or unsteady because someone has had too much to drink.",
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


def dump_trace(world: World) -> str:
    parts = ["--- world model state ---"]
    for e in world.entities.values():
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        parts.append(f"  {e.id:10} ({e.kind}) {' '.join(bits)}")
    parts.append(f"  place={world.place.label}")
    return "\n".join(parts)


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------

ASP_RULES = r"""
% Facts describe the registry. The rules mirror the Python reasonableness gate.

repeat_theme(T) :- task(T), tag(T, repetition).
reconciliation_theme(T) :- task(T), tag(T, reconciliation).

valid_story(P, T) :- place(P), task(T), affords(P, water), repeat_theme(T), reconciliation_theme(T).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid, place in PLACES.items():
        lines.append(asp.fact("place", pid))
        for a in sorted(place.affords):
            lines.append(asp.fact("affords", pid, a))
    for tid, task in TASKS.items():
        lines.append(asp.fact("task", tid))
        for tag in sorted(task.tags):
            lines.append(asp.fact("tag", tid, tag))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_stories() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/2."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    python_set = {(pid, tid) for pid in PLACES for tid in TASKS if "water" in PLACES[pid].affords and "repetition" in TASKS[tid].tags and "reconciliation" in TASKS[tid].tags}
    asp_set = set(asp_valid_stories())
    if asp_set == python_set:
        print(f"OK: clingo gate matches Python gate ({len(asp_set)} stories).")
        return 0
    print("MISMATCH between clingo and Python gates:")
    if asp_set - python_set:
        print("  only in clingo:", sorted(asp_set - python_set))
    if python_set - asp_set:
        print("  only in python:", sorted(python_set - asp_set))
    return 1


# ---------------------------------------------------------------------------
# Parameters and generation
# ---------------------------------------------------------------------------

CURATED = [
    StoryParams(place="rooftop", task="hyacinth", hero_name="Mira", hero_type="girl", companion_name="Pia", companion_type="girl"),
    StoryParams(place="street", task="drunken", hero_name="Kai", hero_type="boy", companion_name="Bo", companion_type="boy"),
    StoryParams(place="courtyard", task="hyacinth", hero_name="Luna", hero_type="girl", companion_name="June", companion_type="girl"),
]

def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Tiny superhero storyworld: hyacinth, drunken, repetition, reconciliation.")
    ap.add_argument("--place", choices=sorted(PLACES))
    ap.add_argument("--task", choices=sorted(TASKS))
    ap.add_argument("--hero-name")
    ap.add_argument("--hero-type", choices=["girl", "boy"])
    ap.add_argument("--companion-name")
    ap.add_argument("--companion-type", choices=["girl", "boy"])
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
    place = args.place or rng.choice(sorted(PLACES))
    task = args.task or rng.choice(sorted(TASKS))
    hero_type = args.hero_type or rng.choice(["girl", "boy"])
    companion_type = args.companion_type or hero_type
    hero_name = args.hero_name or rng.choice(HEROES[hero_type])
    companion_name = args.companion_name or rng.choice(COMPANIONS[companion_type])

    if place not in PLACES:
        raise StoryError("Unknown place.")
    if task not in TASKS:
        raise StoryError("Unknown task.")

    if task == "drunken" and place == "rooftop":
        raise StoryError("The drunken crowd story belongs on the street, not the rooftop garden.")
    return StoryParams(
        place=place,
        task=task,
        hero_name=hero_name,
        hero_type=hero_type,
        companion_name=companion_name,
        companion_type=companion_type,
    )


def generate(params: StoryParams) -> StorySample:
    world = tell(
        PLACES[params.place],
        TASKS[params.task],
        params.hero_name,
        params.hero_type,
        params.companion_name,
        params.companion_type,
    )
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_qa(world),
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
        stories = asp_valid_stories()
        print(f"{len(stories)} valid stories:")
        for item in stories:
            print(" ", item)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)

    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            sample = generate(params)
            if sample.story in seen:
                i += 1
                continue
            seen.add(sample.story)
            samples.append(sample)
            i += 1

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
            header = f"### {p.hero_name} in {p.place} with {p.task}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()

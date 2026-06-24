#!/usr/bin/env python3
"""
storyworlds/worlds/improve_maintenance_moral_value_surprise_cautionary_fairy.py
==============================================================================

A tiny fairy-tale storyworld about a little kingdom's maintenance, where a
caretaker tries to improve a broken place, meets a surprise, and learns a
cautionary moral value.

The seed words are "improve" and "maintenance". The style is intentionally
fairy-tale-like: a humble helper, a magical place, a small danger, a surprise
turn, and a moral ending image.
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
# Entities and world state
# ---------------------------------------------------------------------------
@dataclass
class Entity:
    id: str
    kind: str = "thing"  # "character" | "thing" | "place"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    meters: dict[str, float] = field(default_factory=lambda: {})
    memes: dict[str, float] = field(default_factory=lambda: {})

    def pronoun(self) -> str:
        return "she" if self.type in {"girl", "queen", "woman", "fairy"} else "he" if self.type in {"boy", "king", "man"} else "it"


@dataclass
class Place:
    id: str
    label: str
    mood: str
    needs: str
    secret: str
    surprise: str


@dataclass
class Task:
    id: str
    verb: str
    improve_word: str
    tool: str
    risk: str
    result: str
    moral: str
    tags: set[str] = field(default_factory=set)


@dataclass
class StoryParams:
    place: str
    task: str
    hero_name: str
    hero_type: str
    helper_name: str
    helper_type: str
    seed: Optional[int] = None


class World:
    def __init__(self, place: Place, task: Task) -> None:
        self.place = place
        self.task = task
        self.entities: dict[str, Entity] = {}
        self.fired: set[str] = set()
        self.lines: list[str] = []
        self.facts: dict[str, object] = {}

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def say(self, text: str) -> None:
        if text:
            self.lines.append(text)

    def render(self) -> str:
        return " ".join(self.lines)

    def copy(self) -> "World":
        other = World(self.place, self.task)
        other.entities = {k: Entity(**{
            "id": v.id, "kind": v.kind, "type": v.type, "label": v.label,
            "phrase": v.phrase, "owner": v.owner, "caretaker": v.caretaker,
            "meters": dict(v.meters), "memes": dict(v.memes)
        }) for k, v in self.entities.items()}
        other.fired = set(self.fired)
        return other


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------
PLACES = {
    "tower": Place("tower", "the old tower", "crooked", "stone steps that need fixing", "a hidden bird nest", "a tiny golden key"),
    "bridge": Place("bridge", "the willow bridge", "worn", "wooden planks that need fixing", "a sleeping fish", "a silver ribbon"),
    "garden": Place("garden", "the moon garden", "messy", "paths that need clearing", "a lost lantern", "a glass pebble"),
}

TASKS = {
    "mend_steps": Task("mend_steps", "mend the steps", "improve the steps", "a small hammer", "splinters and slips", "the stairs became steady again", "Slow work can be safer than hurrying.", {"maintenance", "improve", "cautionary"}),
    "repair_bridge": Task("repair_bridge", "repair the bridge", "improve the bridge", "a brush of glue", "a loose board over the water", "the bridge stood firm", "Care for the weak place before you cross it.", {"maintenance", "improve", "cautionary"}),
    "clear_paths": Task("clear_paths", "clear the paths", "improve the paths", "a broom of reeds", "one hidden twist in the root-vine", "the garden path opened wide", "A tidy path saves a hurried foot.", {"maintenance", "improve", "cautionary"}),
}

HERO_NAMES = ["Lina", "Milo", "Pia", "Nico", "Tara", "Owen"]
HELPER_NAMES = ["Brim", "Faye", "Tobin", "Wren", "Sora", "Eli"]
TRAITS = ["kind", "careful", "brave", "gentle", "patient"]


# ---------------------------------------------------------------------------
# Reasonableness gate
# ---------------------------------------------------------------------------
def valid_combo(place: Place, task: Task) -> bool:
    if place.id == "tower" and task.id == "clear_paths":
        return False
    if place.id == "bridge" and task.id == "mend_steps":
        return False
    return True


def valid_combos() -> list[tuple[str, str]]:
    out = []
    for p in PLACES.values():
        for t in TASKS.values():
            if valid_combo(p, t):
                out.append((p.id, t.id))
    return out


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
valid(Place, Task) :- place(Place), task(Task), allowed(Place, Task).
"""

def asp_facts() -> str:
    import storyworlds.asp as asp
    lines = []
    for pid in PLACES:
        lines.append(asp.fact("place", pid))
    for tid in TASKS:
        lines.append(asp.fact("task", tid))
    for pid, tid in valid_combos():
        lines.append(asp.fact("allowed", pid, tid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple[str, str]]:
    import storyworlds.asp as asp
    model = asp.one_model(asp_program("#show valid/2."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    py = set(valid_combos())
    ap = set(asp_valid_combos())
    if py == ap:
        print(f"OK: ASP matches Python gate ({len(py)} combos).")
        return 0
    print("MISMATCH")
    print("python only:", sorted(py - ap))
    print("asp only:", sorted(ap - py))
    return 1


# ---------------------------------------------------------------------------
# Story engine
# ---------------------------------------------------------------------------
def build_story(world: World, hero: Entity, helper: Entity) -> None:
    task = world.task
    place = world.place

    world.say(f"Once in a fairy kingdom, {hero.id} was a {hero.type} who loved to {task.improve_word}.")
    world.say(f"{hero.id} lived near {place.label}, where {place.needs} and where the air felt {place.mood}.")
    world.say(f"One morning, {helper.id} came with {task.tool} and said they could do the maintenance together.")

    world.say(f"They went to {place.label} to {task.verb}.")
    world.facts["risk"] = task.risk
    world.facts["moral"] = task.moral

    # Surprise turn: a secret thing appears, changing the plan.
    world.say(f"Then came a surprise: {place.secret} was hiding in the place, and it blinked in the light.")
    world.facts["surprise"] = place.surprise

    # The risk matters and forces a careful action.
    hero.memes["worry"] = 1.0
    helper.memes["care"] = 1.0
    world.say(f"{hero.id} slowed down, because careless work could bring {task.risk}.")
    world.say(f"{helper.id} lifted the tool gently, and together they chose the safe way.")

    # Resolution and moral ending.
    hero.meters["skill"] = 1.0
    place_label = place.label
    world.say(f"At last, {task.result}, and the surprise was left safe and shining.")
    world.say(f"In the end, {hero.id} learned that {task.moral.lower()} The old {place_label} looked brighter, and the kingdom felt kinder.")


def generate_world(params: StoryParams) -> World:
    place = PLACES[params.place]
    task = TASKS[params.task]
    world = World(place, task)
    hero = world.add(Entity(id=params.hero_name, kind="character", type=params.hero_type, label=params.hero_name))
    helper = world.add(Entity(id=params.helper_name, kind="character", type=params.helper_type, label=params.helper_name))
    world.facts.update(hero=hero, helper=helper, place=place, task=task)
    build_story(world, hero, helper)
    return world


def generation_prompts(world: World) -> list[str]:
    place: Place = world.facts["place"]  # type: ignore[assignment]
    task: Task = world.facts["task"]  # type: ignore[assignment]
    hero: Entity = world.facts["hero"]  # type: ignore[assignment]
    return [
        f"Write a short fairy tale about {hero.id} trying to improve {place.label} through maintenance.",
        f"Tell a cautionary story where a kind helper notices a surprise while {hero.id} is doing {task.verb}.",
        f"Write a child-friendly fairy tale with a moral value ending about keeping an old place safe.",
    ]


def story_qa(world: World) -> list[QAItem]:
    place: Place = world.facts["place"]  # type: ignore[assignment]
    task: Task = world.facts["task"]  # type: ignore[assignment]
    hero: Entity = world.facts["hero"]  # type: ignore[assignment]
    helper: Entity = world.facts["helper"]  # type: ignore[assignment]
    return [
        QAItem(
            question=f"What did {hero.id} want to do at {place.label}?",
            answer=f"{hero.id} wanted to improve {place.label} by doing maintenance and making it safer.",
        ),
        QAItem(
            question=f"What surprise was hiding in {place.label}?",
            answer=f"The surprise was {place.surprise}, hiding quietly in {place.label}.",
        ),
        QAItem(
            question=f"What lesson did {hero.id} learn at the end?",
            answer=f"{hero.id} learned that {task.moral.lower()}",
        ),
        QAItem(
            question=f"Who helped {hero.id} with the work?",
            answer=f"{helper.id} helped {hero.id} with the maintenance work and kept the plan careful.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does maintenance mean?",
            answer="Maintenance means caring for something so it stays safe, neat, and useful for a long time.",
        ),
        QAItem(
            question="Why should people be careful when they improve an old place?",
            answer="People should be careful because old places can have weak spots, and a rushed fix can make things worse.",
        ),
        QAItem(
            question="What is a moral value in a fairy tale?",
            answer="A moral value is the gentle lesson the story wants to teach, like being careful or kind.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    parts = ["== prompts =="]
    parts.extend(sample.prompts)
    parts.append("")
    parts.append("== story qa ==")
    for qa in sample.story_qa:
        parts.append(f"Q: {qa.question}")
        parts.append(f"A: {qa.answer}")
    parts.append("")
    parts.append("== world qa ==")
    for qa in sample.world_qa:
        parts.append(f"Q: {qa.question}")
        parts.append(f"A: {qa.answer}")
    return "\n".join(parts)


def dump_trace(world: World) -> str:
    lines = ["--- trace ---"]
    lines.append(f"place: {world.place.id}")
    lines.append(f"task: {world.task.id}")
    for e in world.entities.values():
        lines.append(f"{e.id}: kind={e.kind} type={e.type} meters={e.meters} memes={e.memes}")
    lines.append(f"facts: {world.facts}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Fairy tale storyworld about maintenance, surprise, and moral value.")
    ap.add_argument("--place", choices=sorted(PLACES))
    ap.add_argument("--task", choices=sorted(TASKS))
    ap.add_argument("--hero-name")
    ap.add_argument("--hero-type", choices=["girl", "boy", "fairy", "child"])
    ap.add_argument("--helper-name")
    ap.add_argument("--helper-type", choices=["girl", "boy", "fairy", "child"])
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
    combos = valid_combos()
    if args.place and args.task and (args.place, args.task) not in combos:
        raise StoryError("No valid fairy-tale story matches those explicit options.")
    valid = [c for c in combos if (not args.place or c[0] == args.place) and (not args.task or c[1] == args.task)]
    if not valid:
        raise StoryError("No valid fairy-tale story matches those options.")
    place_id, task_id = rng.choice(valid)
    hero_type = args.hero_type or rng.choice(["girl", "boy", "fairy", "child"])
    helper_type = args.helper_type or rng.choice(["girl", "boy", "fairy", "child"])
    hero_name = args.hero_name or rng.choice(HERO_NAMES)
    helper_name = args.helper_name or rng.choice(HELPER_NAMES)
    return StoryParams(place=place_id, task=task_id, hero_name=hero_name, hero_type=hero_type, helper_name=helper_name, helper_type=helper_type)


def generate(params: StoryParams) -> StorySample:
    world = generate_world(params)
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
    StoryParams(place="tower", task="mend_steps", hero_name="Lina", hero_type="girl", helper_name="Brim", helper_type="fairy"),
    StoryParams(place="bridge", task="repair_bridge", hero_name="Milo", hero_type="boy", helper_name="Faye", helper_type="girl"),
    StoryParams(place="garden", task="clear_paths", hero_name="Pia", hero_type="girl", helper_name="Wren", helper_type="fairy"),
]


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show valid/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import storyworlds.asp as asp
        model = asp.one_model(asp_program("#show valid/2."))
        print(sorted(set(asp.atoms(model, "valid"))))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
            seed = base_seed + i
            i += 1
            try:
                params = resolve_params(args, random.Random(seed))
            except StoryError as e:
                print(e)
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
        emit(sample, trace=args.trace, qa=args.qa, header=(f"### variant {i+1}" if len(samples) > 1 else ""))
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()

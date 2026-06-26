#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260626T060043Z_seed274930118_n5000/arson_bad_ending_surprise_reconciliation_mystery.py
============================================================================================================

A tiny mystery storyworld about a suspicious fire, a bad ending, a surprise,
and a reconciliation.

The seed idea is a short tale in which a child notices smoke near a small
workshop, pieces together what happened, and learns that the surprising culprit
was trying to hide a mistake rather than cause harm. The ending is still sad:
a special keepsake is ruined. But the story also ends with apology, repair
work, and a calmer friendship.
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

THRESHOLD = 1.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    traits: list[str] = field(default_factory=list)
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "mother", "aunt", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "uncle", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class Scene:
    place: str
    smoke: str
    affordance: str


@dataclass
class Clue:
    label: str
    detail: str
    points_to: str
    reveals: str


@dataclass
class StoryParams:
    place: str
    child: str
    child_type: str
    helper: str
    helper_type: str
    suspect: str
    suspect_type: str
    clue: str
    seed: Optional[int] = None


class World:
    def __init__(self, scene: Scene) -> None:
        self.scene = scene
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
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

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)

    def copy(self) -> "World":
        clone = World(self.scene)
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        return clone


def _r_smoke(world: World) -> list[str]:
    out: list[str] = []
    for e in world.entities.values():
        if e.meters.get("fire", 0.0) < THRESHOLD:
            continue
        sig = ("smoke", e.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        e.meters["smoke"] = e.meters.get("smoke", 0.0) + 1
        out.append(f"Smoke curled up from the {e.label}.")
    return out


def _r_damage(world: World) -> list[str]:
    out: list[str] = []
    fire_source = world.facts.get("burn_target")
    if not fire_source:
        return out
    target = world.entities[fire_source]
    if target.meters.get("fire", 0.0) < THRESHOLD:
        return out
    if target.meters.get("damaged", 0.0) >= THRESHOLD:
        return out
    target.meters["damaged"] = 1
    out.append(f"The {target.label} blackened and cracked.")
    return out


def _r_confession(world: World) -> list[str]:
    out: list[str] = []
    suspect = world.get(world.facts["suspect"].id)
    if suspect.memes.get("guilt", 0.0) < THRESHOLD:
        return out
    sig = ("confess", suspect.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    out.append("__confess__")
    return out


RULES = [
    _r_smoke,
    _r_damage,
    _r_confession,
]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in RULES:
            bits = rule(world)
            if bits:
                changed = True
                for b in bits:
                    if b != "__confess__":
                        produced.append(b)
    if narrate:
        for s in produced:
            world.say(s)
    return produced


SCENES = {
    "workshop": Scene(place="the little workshop", smoke="sharp smoke", affordance="tools"),
    "barn": Scene(place="the old barn", smoke="thick smoke", affordance="hay"),
    "garage": Scene(place="the garage", smoke="gray smoke", affordance="paint cans"),
}

CLUES = {
    "charred_match": Clue(
        label="a charred match",
        detail="A burned match was found under the bench.",
        points_to="suspect",
        reveals="someone had been there close to the fire.",
    ),
    "scented_oil": Clue(
        label="a bottle of lamp oil",
        detail="A tipped bottle of lamp oil was hiding behind a box.",
        points_to="suspect",
        reveals="the fire had started near the oil.",
    ),
    "broken_jar": Clue(
        label="a broken jar",
        detail="A broken jar lay beside the ash, with sticky drops on the floor.",
        points_to="helper",
        reveals="the helper had tried to clean up too quickly.",
    ),
}

CHILD_NAMES = ["Maya", "Leo", "Nina", "Owen", "Zuri", "Ben", "Ava", "Noah"]
HELPER_NAMES = ["Aunt June", "Uncle Ray", "Mina", "Tom"]
SUSPECT_NAMES = ["Mr. Reed", "Mara", "Pip", "Mrs. Vale"]


@dataclass
class StoryState:
    child: Entity
    helper: Entity
    suspect: Entity
    clue: Clue
    burn_target: Entity
    resolution: str = ""
    surprise: str = ""
    bad_ending: str = ""


def _article(word: str) -> str:
    return "an" if word[:1].lower() in "aeiou" else "a"


def tell(params: StoryParams) -> World:
    world = World(SCENES[params.place])

    child = world.add(Entity(id=params.child, kind="character", type=params.child_type, traits=["curious", "careful"]))
    helper = world.add(Entity(id=params.helper, kind="character", type=params.helper_type, traits=["gentle", "nervous"]))
    suspect = world.add(Entity(id=params.suspect, kind="character", type=params.suspect_type, traits=["quiet", "shy"]))

    burn_target = world.add(Entity(id="keepsake", type="thing", label="paper lantern", phrase="a painted paper lantern"))
    clue = CLUES[params.clue]

    state = StoryState(child=child, helper=helper, suspect=suspect, clue=clue, burn_target=burn_target)
    world.facts.update(child=child, helper=helper, suspect=suspect, clue=clue, burn_target=burn_target, state=state)

    child.memes["worry"] = 1
    helper.memes["secret"] = 1
    suspect.memes["nervous"] = 1

    world.say(
        f"{child.id} liked quiet afternoons in {world.scene.place}. "
        f"{child.pronoun().capitalize()} noticed everything: dusty shelves, bent nails, and tiny noises."
    )
    world.say(
        f"Near the back wall sat {helper.pronoun('possessive')} favorite {burn_target.label}. "
        f"It was painted with stars and used in the moon-viewing festival every year."
    )

    world.para()
    world.say(
        f"Then {child.id} smelled {world.scene.smoke}. "
        f"{child.pronoun().capitalize()} found a dark mark on the floor and a wobbling trail of ash."
    )
    world.say(
        f"That looked like a mystery, and it also looked like arson: somebody had set a fire on purpose."
    )

    world.para()
    world.say(
        f"{child.id} followed the clues. {clue.detail} "
        f"{clue.reveals.capitalize()}"
    )
    if clue.label == "a charred match":
        suspect.memes["guilt"] = 1
        world.say(
            f"The match had {suspect.id}'s wax seal on the box, so {child.id} went to ask gentle questions."
        )
    elif clue.label == "a bottle of lamp oil":
        suspect.memes["guilt"] = 1
        world.say(
            f"The oil bottle had {suspect.id}'s fingerprints on it, so the trail pointed back to the quiet neighbor."
        )
    else:
        helper.memes["guilt"] = 1
        world.say(
            f"The broken jar showed that {helper.id} had tried to clean the mess before anyone saw it."
        )

    if clue.points_to == "suspect":
        world.say(
            f"At first, {child.id} thought {suspect.id} had done it out of spite. "
            f"But the story had a surprise waiting."
        )
        state.surprise = f"{suspect.id} had not wanted to hurt anyone."
        if suspect.id == "Mr. Reed":
            world.say(
                f"{suspect.id} finally admitted something odd: {suspect.pronoun().capitalize()} had tried to burn away a wet nest of weeds."
            )
        else:
            world.say(
                f"{suspect.id} finally admitted {suspect.pronoun()} had lit the flame to hide a torn notice before the fair."
            )
        suspect.memes["guilt"] = 1
        suspect.memes["remorse"] = 1
    else:
        world.say(
            f"The clue led to {helper.id}, and the surprise was that {helper.id} had been covering for {suspect.id}."
        )
        helper.memes["guilt"] = 1
        helper.memes["remorse"] = 1
        suspect.memes["guilt"] = 1
        suspect.memes["shame"] = 1

    world.para()
    world.say(
        f"The fire was put out, but the ending still felt bad. "
        f"The painted {burn_target.label} was ruined for the festival, and the room smelled smoky for days."
    )
    state.bad_ending = "The special lantern was too damaged to hang again."

    world.say(
        f"{child.id} did not cheer. {child.pronoun().capitalize()} stared at the blackened lantern and felt the sad truth of it."
    )

    world.para()
    if helper.memes.get("remorse", 0.0) >= THRESHOLD or suspect.memes.get("remorse", 0.0) >= THRESHOLD:
        world.say(
            f"Then came the reconciliation. {suspect.id} and {helper.id} both apologized, and {child.id} listened without yelling."
        )
        world.say(
            f"They swept the ash together, fixed the shelf, and made a new lantern from colored paper and glue."
        )
        world.say(
            f"By evening, nobody forgot the bad ending, but the room held a calmer feeling: three people working side by side."
        )
        state.resolution = "They repaired the room and forgave each other."
    else:
        world.say(
            f"Nobody could make the lantern right again, so {child.id} quietly placed the broken pieces in a box."
        )
        state.resolution = "The room stayed sad, but the clue was solved."

    world.facts["state"] = state
    return world


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child: Entity = f["child"]
    helper: Entity = f["helper"]
    suspect: Entity = f["suspect"]
    clue: Clue = f["clue"]
    burn_target: Entity = f["burn_target"]
    state: StoryState = f["state"]
    return [
        QAItem(
            question=f"What mystery did {child.id} notice in {world.scene.place}?",
            answer=(
                f"{child.id} noticed smoke, ash, and a burned mark in {world.scene.place}. "
                f"{child.pronoun().capitalize()} realized someone had started a fire on purpose."
            ),
        ),
        QAItem(
            question=f"What clue helped {child.id} follow the trail?",
            answer=(
                f"{clue.detail} That clue helped {child.id} figure out who was involved."
            ),
        ),
        QAItem(
            question=f"Why was the ending still bad even after the fire was solved?",
            answer=(
                f"The {burn_target.label} was ruined, so the festival keepsake could not be saved. "
                f"{state.bad_ending}"
            ),
        ),
        QAItem(
            question=f"What was the surprise in the mystery?",
            answer=(
                f"The surprise was that {state.surprise} What first looked mean was actually a messy mistake."
            ),
        ),
        QAItem(
            question=f"How did the story end after the apology?",
            answer=(
                f"{state.resolution} {child.id}, {helper.id}, and {suspect.id} worked together again after they made up."
            ),
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is arson?",
            answer=(
                "Arson is when someone sets a fire on purpose, usually in a place where the fire can hurt people or things."
            ),
        ),
        QAItem(
            question="Why do detectives look for clues?",
            answer=(
                "Detectives look for clues because clues help them understand what happened and who might be involved."
            ),
        ),
        QAItem(
            question="What is reconciliation?",
            answer=(
                "Reconciliation is when people stop being upset, apologize, and begin to trust each other again."
            ),
        ),
    ]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    child: Entity = f["child"]
    clue: Clue = f["clue"]
    return [
        f"Write a short mystery story for children about {child.id}, a suspicious fire, and {clue.label}.",
        "Tell a gentle detective story with a bad ending, a surprise reveal, and a reconciliation.",
        f"Write a story about arson in a small workshop where the ending stays sad but the people still make up.",
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
    lines.append("== (3) World knowledge questions ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        lines.append(f"  {e.id:12} ({e.type:8}) meters={meters} memes={memes}")
    return "\n".join(lines)


def select_reasonable(place: Optional[str], clue: Optional[str]) -> tuple[str, str]:
    places = list(SCENES)
    clues = list(CLUES)
    if place and place not in SCENES:
        raise StoryError("Unknown place.")
    if clue and clue not in CLUES:
        raise StoryError("Unknown clue.")
    p = place or random.choice(places)
    c = clue or random.choice(clues)
    return p, c


def valid_combos() -> list[tuple[str, str]]:
    return [(p, c) for p in SCENES for c in CLUES]


def explain_rejection(place: str, clue: str) -> str:
    return f"(No story: the mystery setup for {place!r} with clue {clue!r} is not available.)"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Mystery storyworld: arson, bad ending, surprise, reconciliation.")
    ap.add_argument("--place", choices=SCENES)
    ap.add_argument("--clue", choices=CLUES)
    ap.add_argument("--name")
    ap.add_argument("--helper")
    ap.add_argument("--suspect")
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("-n", type=int, default=1)
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--trace", action="store_true")
    ap.add_argument("--qa", action="store_true")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--asp", action="store_true")
    ap.add_argument("--verify", action="store_true")
    ap.add_argument("--show-asp", action="store_true")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    place, clue = select_reasonable(args.place, args.clue)
    child = args.name or rng.choice(CHILD_NAMES)
    helper = args.helper or rng.choice(HELPER_NAMES)
    suspect = args.suspect or rng.choice(SUSPECT_NAMES)
    child_type = "boy" if child in {"Leo", "Owen", "Ben", "Noah"} else "girl"
    helper_type = "aunt" if helper.startswith("Aunt") else "uncle" if helper.startswith("Uncle") else "woman"
    suspect_type = "man" if suspect in {"Mr. Reed", "Pip"} else "woman"
    return StoryParams(
        place=place,
        child=child,
        child_type=child_type,
        helper=helper,
        helper_type=helper_type,
        suspect=suspect,
        suspect_type=suspect_type,
        clue=clue,
    )


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


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world is not None:
        print(dump_trace(sample.world))
    if qa:
        print()
        print(format_qa(sample))


ASP_RULES = r"""
place(workshop).
place(barn).
place(garage).

clue(charred_match).
clue(scented_oil).
clue(broken_jar).

valid(Place, Clue) :- place(Place), clue(Clue).
#show valid/2.
"""


def asp_facts() -> str:
    import storyworlds.asp as asp
    lines: list[str] = []
    for p in SCENES:
        lines.append(asp.fact("place", p))
    for c in CLUES:
        lines.append(asp.fact("clue", c))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import storyworlds.asp as asp
    model = asp.one_model(asp_program("#show valid/2."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    print("only in python:", sorted(py - cl))
    print("only in clingo:", sorted(cl - py))
    return 1


CURATED = [
    StoryParams("workshop", "Maya", "girl", "Aunt June", "aunt", "Mr. Reed", "man", "charred_match"),
    StoryParams("barn", "Leo", "boy", "Uncle Ray", "uncle", "Mara", "woman", "scented_oil"),
    StoryParams("garage", "Nina", "girl", "Mina", "woman", "Pip", "man", "broken_jar"),
]


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show valid/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (place, clue) combos:\n")
        for p, c in combos:
            print(f"  {p:8} {c}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 50, 50):
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            sample = generate(params)
            i += 1
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
            header = f"### {p.child}: {p.place} / {p.clue}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()

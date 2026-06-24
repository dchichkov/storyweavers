#!/usr/bin/env python3
"""
storyworlds/worlds/pea_quest_detective_story.py
===============================================

A small detective-story world built from the seed word "pea" and the feature
"Quest".

Premise:
- A little detective gets a puzzling quest: find the missing pea needed to
  finish a tiny supper.
- The world has concrete clues, a helper, a suspect, and one final reveal.
- The ending proves the quest changed the world: the pea is found, the worry
  drops, and the meal is complete.

The prose is driven by simulated state:
- clues discovered increase certainty
- searching different places can reveal the pea
- worry and relief change the emotional state
- the final image depends on the recovered pea and the solved case
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
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    hidden_in: str = ""
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "woman"}
        male = {"boy", "father", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Place:
    id: str
    label: str
    kind: str
    can_hide_pea: bool = False
    clue: str = ""


@dataclass
class StoryParams:
    place: str
    suspect: str
    helper: str
    detective_name: str
    detective_type: str
    seed: Optional[int] = None


class World:
    def __init__(self) -> None:
        self.entities: dict[str, Entity] = {}
        self.places: dict[str, Place] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
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
        clone = World()
        clone.entities = copy.deepcopy(self.entities)
        clone.places = copy.deepcopy(self.places)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        clone.facts = copy.deepcopy(self.facts)
        return clone


PEA = Entity(
    id="pea",
    type="thing",
    label="pea",
    phrase="one bright green pea",
    caretaker="cook",
    hidden_in="soup",
    meters={"clean": 1.0},
)

SUSPECTS = {
    "cat": "The cat had soft paws and liked to nap in warm places.",
    "crumbs": "The crumbs were tiny, but they made a messy trail across the table.",
    "wind": "The wind could nudge a napkin or blow a light thing away.",
}

PLACES = {
    "kitchen": Place(id="kitchen", label="the kitchen", kind="room", can_hide_pea=False, clue="a spoon and a bowl"),
    "windowsill": Place(id="windowsill", label="the windowsill", kind="ledge", can_hide_pea=True, clue="a tiny pea-shaped speck"),
    "pocket": Place(id="pocket", label="the apron pocket", kind="cloth", can_hide_pea=True, clue="a soft little bulge"),
    "garden": Place(id="garden", label="the garden patch", kind="yard", can_hide_pea=True, clue="a small green track in the dirt"),
}

DETECTIVE_NAMES = ["Mia", "Pip", "Leo", "Nina", "Toby", "June"]
HELPERS = ["mother", "father", "grandparent", "neighbor"]


class DetectiveState:
    def __init__(self) -> None:
        self.clues: list[str] = []
        self.searches: int = 0
        self.certainty: float = 0.0
        self.worry: float = 0.0
        self.resolved: bool = False


def build_world(params: StoryParams) -> World:
    w = World()
    w.places = copy.deepcopy(PLACES)

    detective = w.add(Entity(
        id=params.detective_name,
        kind="character",
        type=params.detective_type,
        meters={"walk": 0.0},
        memes={"curiosity": 1.0, "worry": 0.0, "pride": 0.0},
    ))
    helper = w.add(Entity(
        id="helper",
        kind="character",
        type=params.helper,
        label=f"the {params.helper}",
        meters={"walk": 0.0},
        memes={"calm": 1.0, "hope": 1.0},
    ))
    suspect = w.add(Entity(
        id="suspect",
        kind="character",
        type=params.suspect,
        label=f"the {params.suspect}",
        meters={"walk": 0.0},
        memes={"nervous": 0.0},
    ))
    pea = w.add(copy.deepcopy(PEA))
    pea.hidden_in = params.place

    cook = w.add(Entity(
        id="cook",
        kind="character",
        type="adult",
        label="the cook",
        meters={"walk": 0.0},
        memes={"anxiety": 1.0, "relief": 0.0},
    ))
    cook.caretaker = None

    w.facts.update(
        detective=detective,
        helper=helper,
        suspect=suspect,
        cook=cook,
        pea=pea,
        place=params.place,
        state=DetectiveState(),
    )
    return w


def _search_place(world: World, state: DetectiveState, place_id: str) -> list[str]:
    out: list[str] = []
    place = world.places[place_id]
    detective = world.facts["detective"]
    helper = world.facts["helper"]
    pea = world.facts["pea"]

    state.searches += 1
    detective.meters["walk"] += 1
    helper.meters["walk"] += 1

    if place_id == pea.hidden_in and place.can_hide_pea:
        if ("found", place_id) not in world.fired:
            world.fired.add(("found", place_id))
            state.clues.append(place.clue)
            state.certainty += 1.0
            pea.hidden_in = "basket"
            pea.meters["found"] = 1.0
            detective.memes["pride"] += 1.0
            helper.memes["hope"] += 1.0
            out.append(f"In {place.label}, {detective.id} spotted the pea at last.")
            out.append(f"It had been hiding by {place.clue}.")
    else:
        state.worry += 0.3
        detective.memes["worry"] += 0.3
        out.append(f"{detective.id} checked {place.label}, but the pea was not there.")
    return out


def _deduce(world: World, state: DetectiveState) -> list[str]:
    out: list[str] = []
    detective = world.facts["detective"]
    helper = world.facts["helper"]
    suspect = world.facts["suspect"]
    pea = world.facts["pea"]

    if pea.hidden_in == "basket" and not state.resolved:
        state.resolved = True
        detective.memes["worry"] = 0.0
        helper.memes["calm"] += 0.5
        suspect.memes["nervous"] += 0.2
        out.append(f"{detective.id} knew the case was solved.")
        out.append(f"The {suspect.type} was only a bystander, not a thief.")
    return out


def propagate(world: World, state: DetectiveState, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    produced.extend(_deduce(world, state))
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def tell(params: StoryParams) -> World:
    world = build_world(params)
    state: DetectiveState = world.facts["state"]
    detective = world.facts["detective"]
    helper = world.facts["helper"]
    suspect = world.facts["suspect"]
    pea = world.facts["pea"]

    world.say(f"{detective.id} was a little detective with a big quest: find the missing pea.")
    world.say(f"The cook needed that pea to finish supper, and the whole kitchen felt hushed.")
    world.say(f"{helper.label if helper.label else 'The helper'} joined the search, while {suspect.label} sat nearby with a very innocent face.")

    world.para()
    world.say(f"{detective.id} looked at the clue trail on the table and said the pea had to be hiding somewhere small.")
    world.say(f"First {detective.id} searched {world.places['kitchen'].label}, where there was only {world.places['kitchen'].clue}.")
    for s in _search_place(world, state, "kitchen"):
        world.say(s)

    world.para()
    world.say(f"Then {detective.id} noticed a breeze near {world.places['windowsill'].label}.")
    world.say(f"That was a better guess, because little things like peas can roll into narrow places.")
    for s in _search_place(world, state, "windowsill"):
        world.say(s)
    propagate(world, state, narrate=True)

    if not state.resolved:
        world.para()
        world.say(f"{detective.id} still had one clue left, so {detective.id} checked the garden patch.")
        for s in _search_place(world, state, params.place if params.place in world.places else "garden"):
            world.say(s)
        propagate(world, state, narrate=True)

    world.para()
    if state.resolved:
        world.say(f"{detective.id} held up the pea like a prize and smiled.")
        world.say(f"The cook put the pea into the soup, and the kitchen smell turned warm and happy.")
        world.say(f"{helper.id} laughed, {suspect.label} relaxed, and the case of the missing pea was closed.")
    else:
        world.say(f"{detective.id} never gave up, but the pea stayed lost in the clues.")
        world.say(f"That made the quest feel unfinished, so the story cannot end there.")

    world.facts["state"] = state
    world.facts["resolved"] = state.resolved
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    detective = f["detective"]
    helper = f["helper"]
    suspect = f["suspect"]
    place = f["place"]
    return [
        f'Write a short detective story for a child about a pea quest in {place}.',
        f"Tell a mystery where {detective.id} and {helper.label} search for a pea and learn that {suspect.label} is not the culprit.",
        f"Write a gentle quest story with clues, a search, and a happy ending where the missing pea is found.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    detective = f["detective"]
    helper = f["helper"]
    suspect = f["suspect"]
    pea = f["pea"]
    state: DetectiveState = f["state"]
    place = f["place"]
    qa = [
        QAItem(
            question=f"What was {detective.id}'s quest?",
            answer=f"{detective.id}'s quest was to find the missing pea and help finish supper.",
        ),
        QAItem(
            question=f"Who helped {detective.id} look for the pea?",
            answer=f"{helper.label.capitalize()} helped {detective.id} search the rooms and follow the clues.",
        ),
        QAItem(
            question=f"Why did the kitchen feel tense at the start?",
            answer=f"The kitchen felt tense because the cook needed the pea, and nobody knew where it had gone.",
        ),
    ]
    if state.clues:
        qa.append(QAItem(
            question=f"What clue helped {detective.id} solve the case?",
            answer=f"{detective.id} found clues like {state.clues[0]}, which pointed the search toward the hiding place.",
        ))
    if state.resolved:
        qa.append(QAItem(
            question=f"Was {suspect.label} the thief?",
            answer=f"No. {suspect.label} was only nearby, and {detective.id} learned that the pea was hiding in {world.facts['pea'].hidden_in}.",
        ))
        qa.append(QAItem(
            question=f"What changed by the end of the pea quest?",
            answer=f"By the end, the pea was found, the worry dropped, and the cook could finish supper.",
        ))
    return qa


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a pea?",
            answer="A pea is a small green vegetable. People can eat peas in soup, with dinner, or on a plate.",
        ),
        QAItem(
            question="What does a detective do?",
            answer="A detective looks for clues and uses them to solve a mystery.",
        ),
        QAItem(
            question="What is a quest?",
            answer="A quest is a search for something important, like a missing object or a big goal.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== story qa ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== world qa ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for e in world.entities.values():
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        parts = []
        if meters:
            parts.append(f"meters={meters}")
        if memes:
            parts.append(f"memes={memes}")
        if e.hidden_in:
            parts.append(f"hidden_in={e.hidden_in}")
        lines.append(f"  {e.id}: ({e.type}) {' '.join(parts)}")
    state: DetectiveState = world.facts["state"]
    lines.append(f"  clues={state.clues}")
    lines.append(f"  searches={state.searches}")
    lines.append(f"  certainty={state.certainty}")
    lines.append(f"  worry={state.worry}")
    lines.append(f"  resolved={state.resolved}")
    return "\n".join(lines)


CURATED = [
    StoryParams(place="windowsill", suspect="cat", helper="mother", detective_name="Mia", detective_type="girl"),
    StoryParams(place="garden", suspect="wind", helper="father", detective_name="Pip", detective_type="boy"),
    StoryParams(place="pocket", suspect="crumbs", helper="grandparent", detective_name="June", detective_type="girl"),
]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A tiny detective-story quest about a missing pea.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--suspect", choices=SUSPECTS)
    ap.add_argument("--helper", choices=HELPERS)
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["girl", "boy"])
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
    place = args.place or rng.choice(list(PLACES))
    suspect = args.suspect or rng.choice(list(SUSPECTS))
    helper = args.helper or rng.choice(HELPERS)
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(DETECTIVE_NAMES)
    if args.gender == "girl" and name in {"Pip", "Leo", "Toby"}:
        name = rng.choice([n for n in DETECTIVE_NAMES if n not in {"Pip", "Leo", "Toby"}])
    if args.gender == "boy" and name in {"Mia", "Nina", "June"}:
        name = rng.choice([n for n in DETECTIVE_NAMES if n not in {"Mia", "Nina", "June"}])
    return StoryParams(place=place, suspect=suspect, helper=helper, detective_name=name, detective_type=gender)


def generate(params: StoryParams) -> StorySample:
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


ASP_RULES = r"""
place(kitchen). place(windowsill). place(pocket). place(garden).
suspect(cat). suspect(crumbs). suspect(wind).
helper(mother). helper(father). helper(grandparent). helper(neighbor).

can_hide_pea(windowsill).
can_hide_pea(pocket).
can_hide_pea(garden).

valid_story(P, S, H) :- place(P), suspect(S), helper(H), can_hide_pea(P).
"""

def asp_facts() -> str:
    import asp
    lines = []
    for pid in PLACES:
        lines.append(asp.fact("place", pid))
        if PLACES[pid].can_hide_pea:
            lines.append(asp.fact("can_hide_pea", pid))
    for s in SUSPECTS:
        lines.append(asp.fact("suspect", s))
    for h in HELPERS:
        lines.append(asp.fact("helper", h))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_stories() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/3."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    combos = {(p, s, h) for p in PLACES if PLACES[p].can_hide_pea for s in SUSPECTS for h in HELPERS}
    asp_set = set(asp_valid_stories())
    if asp_set == combos:
        print(f"OK: clingo gate matches Python gate ({len(combos)} stories).")
        return 0
    print("MISMATCH between clingo and Python:")
    print("only in clingo:", sorted(asp_set - combos))
    print("only in python:", sorted(combos - asp_set))
    return 1


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid_story/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"{len(asp_valid_stories())} compatible pea-quest detective stories")
        for p, s, h in asp_valid_stories():
            print(f"  {p:12} {s:10} {h}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
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
            header = f"### {p.detective_name}: pea quest in {p.place}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()

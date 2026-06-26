#!/usr/bin/env python3
"""
A standalone storyworld for a tiny detective tale: a clue is foreshadowed,
bravery is tested, and a final thrust into action solves the case.
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
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    plural: bool = False
    owner: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "woman", "mother"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man", "father"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Place:
    name: str
    atmosphere: str
    hiding_spots: list[str]


@dataclass
class Clue:
    id: str
    label: str
    phrase: str
    reveal: str
    weight: float = 1.0


@dataclass
class StoryParams:
    place: str
    clue: str
    name: str
    gender: str
    role: str
    seed: Optional[int] = None


class World:
    def __init__(self, place: Place):
        self.place = place
        self.entities: dict[str, Entity] = {}
        self.facts: dict = {}
        self.trace: list[str] = []
        self.paragraphs: list[list[str]] = [[]]
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
        import copy
        w = World(self.place)
        w.entities = copy.deepcopy(self.entities)
        w.facts = dict(self.facts)
        w.trace = list(self.trace)
        w.paragraphs = [[]]
        w.fired = set(self.fired)
        return w


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------
PLACES = {
    "library": Place("the library", "quiet aisles and whispering shelves", ["desk", "stack", "corner"]),
    "station": Place("the train station", "echoing footsteps and shiny floors", ["bench", "ticket window", "turnstile"]),
    "museum": Place("the museum", "long halls and glass cases", ["statue hall", "side room", "archway"]),
}

CLUES = {
    "button": Clue("button", "a brass button", "a brass button from a coat", "matched the porter"),
    "ticket": Clue("ticket", "a torn ticket stub", "a torn ticket stub with a time mark", "pointed to the late train"),
    "glove": Clue("glove", "a dark glove", "a dark glove with dust on the fingertips", "belonged to the guard"),
}

GIRL_NAMES = ["Mina", "Ivy", "Nora", "Zoe", "Lena", "Pia"]
BOY_NAMES = ["Theo", "Sam", "Leo", "Finn", "Milo", "Ezra"]


# ---------------------------------------------------------------------------
# Story behavior
# ---------------------------------------------------------------------------
def reasonableness_gate(place: str, clue: str) -> bool:
    return place in PLACES and clue in CLUES


def predict_solution(world: World, detective: Entity, clue: Clue) -> bool:
    sim = world.copy()
    sim.facts["noticed"] = True
    sim.facts["brave"] = True
    sim.facts["thrust"] = True
    return clue.weight >= 1.0


def introduce(world: World, detective: Entity) -> None:
    world.say(
        f"{detective.id} was a young detective who noticed tiny things other people missed."
    )


def foreshadow(world: World, clue: Clue) -> None:
    world.say(
        f"At first, {clue.phrase} seemed ordinary, but it sat where the light kept catching it."
    )
    world.say(
        f"That little glint was a clue, and it hinted that somebody had hurried through."
    )


def build_tension(world: World, detective: Entity, clue: Clue) -> None:
    detective.memes["curiosity"] = detective.memes.get("curiosity", 0) + 1
    detective.memes["worry"] = detective.memes.get("worry", 0) + 1
    world.say(
        f"{detective.id} studied the clue and felt a small chill. "
        f"If {clue.label} was here, then the missing thing was probably not far away."
    )


def bravery_turn(world: World, detective: Entity) -> None:
    detective.memes["bravery"] = detective.memes.get("bravery", 0) + 1
    world.say(
        f"Even so, {detective.id} took a breath and stepped deeper into the quiet place."
    )
    world.say(
        f"{detective.pronoun().capitalize()} was brave enough to keep going when the hallway felt eerie."
    )


def thrust_action(world: World, detective: Entity, clue: Clue) -> None:
    detective.meters["motion"] = detective.meters.get("motion", 0) + 1
    detective.memes["bravery"] = detective.memes.get("bravery", 0) + 1
    world.say(
        f"Then {detective.id} made one quick thrust forward, sliding a hand under the bench."
    )
    world.say(
        f"There, hidden in the dark, was the missing case file, just where the clue had suggested."
    )


def resolve(world: World, detective: Entity, clue: Clue) -> None:
    detective.memes["relief"] = detective.memes.get("relief", 0) + 1
    world.say(
        f"The clue made sense at last: it {clue.reveal}, and the mystery was solved."
    )
    world.say(
        f"{detective.id} brought the missing item back, and the whole room felt safe again."
    )


def tell(place: Place, clue: Clue, name: str, gender: str, role: str) -> World:
    world = World(place)
    detective = world.add(Entity(id=name, kind="character", type=gender, label=role))
    missing = world.add(Entity(id="missing", kind="thing", type="file", label="case file", phrase="the missing case file"))

    world.facts.update(detective=detective, clue=clue, missing=missing)

    introduce(world, detective)
    world.para()
    world.say(f"It was a day in {place.name}, with {place.atmosphere}.")
    foreshadow(world, clue)
    build_tension(world, detective, clue)
    world.para()
    bravery_turn(world, detective)
    thrust_action(world, detective, clue)
    resolve(world, detective, clue)
    world.facts["resolved"] = True
    return world


# ---------------------------------------------------------------------------
# Q&A
# ---------------------------------------------------------------------------
def prompts(world: World) -> list[str]:
    f = world.facts
    detective = f["detective"]
    clue = f["clue"]
    return [
        f'Write a short detective story for a child where {detective.id} finds {clue.phrase} and solves the case.',
        f'Tell a gentle mystery with foreshadowing, bravery, and one sudden thrust into action.',
        f'Write a simple detective tale set in {world.place.name} that ends with the clue paying off.',
    ]


def story_qa(world: World) -> list[QAItem]:
    d = world.facts["detective"]
    clue = world.facts["clue"]
    place = world.place.name
    return [
        QAItem(
            question=f"Who is the detective in the story?",
            answer=f"The detective is {d.id}, a child who keeps looking carefully until the clue makes sense."
        ),
        QAItem(
            question=f"What clue did {d.id} notice in {place}?",
            answer=f"{d.id} noticed {clue.phrase}, and it foreshadowed where the missing case file was hidden."
        ),
        QAItem(
            question=f"How did {d.id} solve the mystery?",
            answer=f"{d.id} solved it by staying brave, then making a quick thrust forward to reach the hidden file."
        ),
    ]


WORLD_KNOWLEDGE = {
    "button": [
        QAItem(
            question="What is a button on a coat?",
            answer="A button is a small round piece that helps fasten a coat or shirt closed."
        )
    ],
    "ticket": [
        QAItem(
            question="What is a ticket stub?",
            answer="A ticket stub is a small torn part of a ticket that can show where or when someone traveled."
        )
    ],
    "glove": [
        QAItem(
            question="What do gloves do?",
            answer="Gloves cover your hands and help keep them warm or clean."
        )
    ],
}


def world_qa(world: World) -> list[QAItem]:
    clue = world.facts["clue"].id
    return list(WORLD_KNOWLEDGE.get(clue, []))


def format_qa(sample: StorySample) -> str:
    out = ["== Prompts =="]
    for p in sample.prompts:
        out.append(p)
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
place_ok(P) :- place(P).
clue_ok(C) :- clue(C).
valid_story(P, C) :- place_ok(P), clue_ok(C).
"""


def asp_facts() -> str:
    import storyworlds.asp as asp
    lines = []
    for pid in PLACES:
        lines.append(asp.fact("place", pid))
    for cid in CLUES:
        lines.append(asp.fact("clue", cid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_stories() -> list[tuple]:
    import storyworlds.asp as asp
    model = asp.one_model(asp_program("#show valid_story/2."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    py = {(p, c) for p in PLACES for c in CLUES if reasonableness_gate(p, c)}
    asp_set = set(asp_valid_stories())
    if py == asp_set:
        print(f"OK: clingo gate matches python gate ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and python:")
    print("python only:", sorted(py - asp_set))
    print("clingo only:", sorted(asp_set - py))
    return 1


# ---------------------------------------------------------------------------
# API contract
# ---------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A tiny detective storyworld with foreshadowing and bravery.")
    ap.add_argument("--place", choices=PLACES.keys())
    ap.add_argument("--clue", choices=CLUES.keys())
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--role", choices=["detective", "kid detective", "young detective"])
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
    place = args.place or rng.choice(list(PLACES.keys()))
    clue = args.clue or rng.choice(list(CLUES.keys()))
    if not reasonableness_gate(place, clue):
        raise StoryError("No reasonable story combination matches those options.")
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    role = args.role or "young detective"
    return StoryParams(place=place, clue=clue, name=name, gender=gender, role=role)


def generate(params: StoryParams) -> StorySample:
    world = tell(PLACES[params.place], CLUES[params.clue], params.name, params.gender, params.role)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=prompts(world),
        story_qa=story_qa(world),
        world_qa=world_qa(world),
        world=world,
    )


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for e in world.entities.values():
        bits = []
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        lines.append(f"{e.id}: {', '.join(bits) if bits else 'no state'}")
    lines.append(f"facts={world.facts}")
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
        print(f"{len(asp_valid_stories())} compatible stories")
        for p, c in asp_valid_stories():
            print(p, c)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)

    samples: list[StorySample] = []
    if args.all:
        for p in PLACES:
            for c in CLUES:
                params = StoryParams(place=p, clue=c, name="Mina", gender="girl", role="young detective")
                samples.append(generate(params))
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            sample = generate(params)
            if sample.story not in seen:
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
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""
storyworlds/worlds/bugle_plaza_mystery_to_solve_humor_heartwarming.py
======================================================================

A small heartwarming mystery world set at a plaza, with a bugle, a few clues,
and a gentle humorous turn.

Premise:
- A child finds a bugle in the plaza.
- Nobody knows whose it is at first.
- The child follows funny clues and asks around.
- The mystery is solved when the right owner is found.
- The ending is warm: the bugle goes home, and the plaza gets music.

This world is state-driven: objects have physical meters and emotional memes,
and the story follows the changing state as clues are discovered, guesses are
made, and the mystery resolves.
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
# World data
# ---------------------------------------------------------------------------

@dataclass
class Entity:
    id: str
    kind: str = "thing"  # "character" | "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "woman", "mother", "grandmother"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man", "father", "grandfather"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Place:
    id: str
    label: str
    mood: str
    features: list[str] = field(default_factory=list)
    echoes: bool = False
    clocks: bool = False


@dataclass
class Mystery:
    id: str
    title: str
    setup: str
    clue: str
    reveal: str
    humor: str
    resolution: str
    tags: set[str] = field(default_factory=set)


@dataclass
class StoryParams:
    place: str
    mystery: str
    name: str
    helper: str
    seed: Optional[int] = None


class World:
    def __init__(self, place: Place) -> None:
        self.place = place
        self.entities: dict[str, Entity] = {}
        self.facts: dict = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()

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
        clone = World(self.place)
        clone.entities = copy.deepcopy(self.entities)
        clone.facts = copy.deepcopy(self.facts)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        return clone


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------

PLACES = {
    "plaza": Place(
        id="plaza",
        label="the plaza",
        mood="bright",
        features=["fountain", "benches", "brick paths", "a low stage"],
        echoes=True,
        clocks=True,
    ),
}

MYSTERIES = {
    "lost_bugle": Mystery(
        id="lost_bugle",
        title="the bugle with no owner",
        setup="a shiny bugle was found on a bench",
        clue="the bugle had a tiny sticker of a star",
        reveal="the sticker matched the visiting parade leader's music kit",
        humor="a sleepy pigeon kept marching like it had very important news",
        resolution="the bugle went back to its happy owner",
        tags={"bugle", "plaza", "lost", "music", "echo"},
    ),
    "echo_alarm": Mystery(
        id="echo_alarm",
        title="the strange sound in the plaza",
        setup="a bugle note bounced around the plaza like a rubber ball",
        clue="the fountain and the stone walls were making the note sound extra loud",
        reveal="the sound came from the bugle's echo, not from any trouble at all",
        humor="every pigeon looked offended by the loud note and one actually fluffed its feathers",
        resolution="the child learned the plaza was full of friendly echoes",
        tags={"bugle", "plaza", "echo", "sound"},
    ),
    "birthday_surprise": Mystery(
        id="birthday_surprise",
        title="the hidden birthday tune",
        setup="someone kept trying to hide a bugle behind a bench",
        clue="a scrap of ribbon and a whispered giggle pointed toward a surprise",
        reveal="the bugle was for a birthday song at the plaza stage",
        humor="the helper almost tripped over a ribbon loop and blamed the bench",
        resolution="the bugle helped start a warm birthday celebration",
        tags={"bugle", "plaza", "birthday", "music"},
    ),
}

CHILD_NAMES = ["Milo", "Nina", "Pip", "Tessa", "Arlo", "June", "Luca", "Ruby"]
HELPERS = ["grandma", "grandpa", "mom", "dad", "aunt", "uncle", "neighbor", "friend"]


# ---------------------------------------------------------------------------
# Reasonableness gate
# ---------------------------------------------------------------------------

def valid_combos() -> list[tuple[str, str]]:
    combos: list[tuple[str, str]] = []
    for place_id, place in PLACES.items():
        for mystery_id, mystery in MYSTERIES.items():
            if "plaza" in mystery.tags and "bugle" in mystery.tags:
                combos.append((place_id, mystery_id))
    return combos


def explain_rejection(place: Place, mystery: Mystery) -> str:
    return (
        f"(No story: {mystery.title} does not fit {place.label} well enough for this small world.)"
    )


# ---------------------------------------------------------------------------
# World simulation
# ---------------------------------------------------------------------------

def _loudness_for_echo(place: Place, mystery: Mystery) -> float:
    if place.echoes and "echo" in mystery.tags:
        return 1.0
    return 0.0


def build_world(params: StoryParams) -> World:
    place = PLACES[params.place]
    mystery = MYSTERIES[params.mystery]
    world = World(place)

    child = world.add(Entity(
        id=params.name,
        kind="character",
        type="child",
        label=params.name,
        meters={"curiosity": 0.0, "joy": 0.0},
        memes={"curiosity": 1.0, "worry": 0.0, "relief": 0.0, "delight": 0.0},
    ))
    helper = world.add(Entity(
        id="helper",
        kind="character",
        type=params.helper,
        label=f"the {params.helper}",
        meters={"kindness": 0.0},
        memes={"helpfulness": 1.0, "worry": 0.0, "relief": 0.0},
    ))
    bugle = world.add(Entity(
        id="bugle",
        kind="thing",
        type="bugle",
        label="bugle",
        phrase="a shiny brass bugle",
        owner=None,
        caretaker=None,
        meters={"shine": 1.0, "lostness": 1.0, "heard": 0.0},
        memes={"mystery": 1.0},
    ))
    owner = world.add(Entity(
        id="owner",
        kind="character",
        type="musician",
        label="the parade leader",
        meters={"patience": 1.0},
        memes={"worry": 0.2, "hope": 0.6, "gratitude": 0.0},
    ))

    world.facts.update(child=child, helper=helper, bugle=bugle, owner=owner, mystery=mystery)

    # Act 1
    world.say(
        f"{child.label} was in {place.label}, where the air felt bright and the stone paths were warm."
    )
    world.say(
        f"Near a bench, {mystery.setup}."
    )
    world.say(
        f"{child.label} picked it up carefully and said, 'A bugle? In a plaza? That sounds like a story trying to start.'"
    )
    bugle.meters["lostness"] = 1.0
    child.memes["curiosity"] += 1.0
    child.meters["curiosity"] += 1.0
    world.facts["found_bugle"] = True

    # Act 2
    world.para()
    world.say(
        f"{mystery.humor.capitalize()} {child.label} laughed, because the pigeon looked as if it wanted to salute the bugle."
    )
    world.say(
        f"{child.label} and {helper.label} asked around the plaza, listening for who might miss it."
    )
    if place.echoes:
        world.say(
            f"When {child.label} blew one tiny note, the plaza answered with a cheerful echo from the fountain."
        )
        bugle.meters["heard"] += 1.0
    child.memes["worry"] += 0.4
    helper.memes["worry"] += 0.2
    world.say(
        f"{child.label} wondered whether the note meant trouble, a joke, or both."
    )

    # Clue and deduction
    world.say(
        f"Then they noticed that {mystery.clue}."
    )
    world.facts["clue_seen"] = True
    child.memes["curiosity"] += 1.0
    helper.meters["kindness"] += 1.0
    child.meters["curiosity"] += 1.0

    # Reveal
    world.para()
    if params.mystery == "lost_bugle":
        world.say(
            f"{child.label} followed the star sticker to {owner.label}, who was looking under the stage steps with a worried face."
        )
        world.say(
            f"'Oh, there it is!' {owner.pronoun('subject').capitalize()} said, and {owner.pronoun('subject')} smiled so hard that the worry melted away."
        )
    elif params.mystery == "echo_alarm":
        world.say(
            f"{helper.label} laughed and said the bugle was not calling for help at all; the plaza was only making the sound bounce."
        )
        world.say(
            f"{child.label} tried another note and giggled when the fountain echoed back like a polite little trumpet."
        )
    else:
        world.say(
            f"{helper.label} spotted the ribbon, and soon {owner.label} arrived with a birthday grin and both hands full of cupcakes."
        )
        world.say(
            f"'I was hiding the bugle for the surprise,' {owner.pronoun('subject')} admitted, laughing at how serious the secret had looked."
        )

    # Resolution
    world.para()
    world.say(mystery.resolution.capitalize() + ".")
    child.memes["worry"] = max(0.0, child.memes["worry"] - 0.8)
    child.memes["relief"] += 1.0
    child.memes["delight"] += 1.0
    helper.memes["relief"] += 1.0
    owner.memes["gratitude"] += 1.0
    bugle.owner = owner.id if params.mystery in {"lost_bugle", "birthday_surprise"} else "plaza"
    bugle.caretaker = owner.id if params.mystery in {"lost_bugle", "birthday_surprise"} else None
    world.facts["solved"] = True

    if params.mystery == "echo_alarm":
        world.say(
            f"{child.label} learned that some mysteries are only the plaza being playful, and that made the echo feel friendly instead of strange."
        )
    else:
        world.say(
            f"{child.label} carried the bugle back with both hands, and the plaza seemed to stand a little taller as the right owner held it again."
        )
        world.say(
            f"Before long, the bugle sang out over the plaza, and the pigeons waddled away as if they were in the parade too."
        )

    return world


# ---------------------------------------------------------------------------
# Story generation and QA
# ---------------------------------------------------------------------------

def generation_prompts(world: World) -> list[str]:
    f = world.facts
    mystery: Mystery = f["mystery"]
    child: Entity = f["child"]
    return [
        f"Write a heartwarming children's mystery about {child.label} in the plaza and a bugle that needs solving.",
        f"Tell a short humorous story where a bugle causes a little mystery at {world.place.label} and ends kindly.",
        f"Write a gentle plaza story with a bugle, a clue, and a warm ending that explains what happened.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child: Entity = f["child"]
    helper: Entity = f["helper"]
    mystery: Mystery = f["mystery"]
    owner: Entity = f["owner"]

    return [
        QAItem(
            question=f"Where did {child.label} find the bugle?",
            answer=f"{child.label} found the bugle in {world.place.label}, near a bench.",
        ),
        QAItem(
            question=f"What made the mystery funny in the story?",
            answer=(
                f"The plaza's echo and the funny pigeon made it amusing. "
                f"{mystery.humor.capitalize()}."
            ),
        ),
        QAItem(
            question=f"Who helped {child.label} solve the mystery?",
            answer=f"{child.label} solved it with help from {helper.label}.",
        ),
        QAItem(
            question=f"What was the clue that helped solve the mystery?",
            answer=f"The clue was that {mystery.clue}.",
        ),
        QAItem(
            question=f"Who did the bugle belong to in the end?",
            answer=(
                f"In the end, the bugle belonged to {owner.label} if it was a lost-bugle story, "
                f"or it became part of the plaza's friendly music if the mystery was about echo."
            ),
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a bugle?",
            answer="A bugle is a brass horn that people can blow to make a bright, trumpet-like sound.",
        ),
        QAItem(
            question="What is a plaza?",
            answer="A plaza is an open public space with paths, benches, and places where people can gather.",
        ),
        QAItem(
            question="Why can an echo sound funny?",
            answer="An echo can sound funny because the same sound comes back again from walls or buildings a moment later.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts -- asks that would produce this story =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== (2) Story questions -- answerable from the story text ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== (3) World-knowledge questions -- child level, no story needed ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------

ASP_RULES = r"""
place_ok(P) :- place(P), plaza(P).
mystery_ok(M) :- mystery(M), bugle_topic(M), plaza_topic(M).
valid(P, M) :- place_ok(P), mystery_ok(M).
"""

def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid in PLACES:
        lines.append(asp.fact("place", pid))
        lines.append(asp.fact(pid))
    for mid, mystery in MYSTERIES.items():
        lines.append(asp.fact("mystery", mid))
        for tag in mystery.tags:
            if tag == "bugle":
                lines.append(asp.fact("bugle_topic", mid))
            if tag == "plaza":
                lines.append(asp.fact("plaza_topic", mid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/2."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    python_set = set(valid_combos())
    clingo_set = set(asp_valid_combos())
    if python_set == clingo_set:
        print(f"OK: clingo gate matches valid_combos() ({len(python_set)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    if python_set - clingo_set:
        print("  only in python:", sorted(python_set - clingo_set))
    if clingo_set - python_set:
        print("  only in clingo:", sorted(clingo_set - python_set))
    return 1


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Heartwarming plaza mystery: a child, a bugle, and a clue."
    )
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--mystery", choices=MYSTERIES)
    ap.add_argument("--name", choices=CHILD_NAMES)
    ap.add_argument("--helper", choices=HELPERS)
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
    if args.place and args.place not in PLACES:
        raise StoryError("Unknown place.")
    if args.mystery and args.mystery not in MYSTERIES:
        raise StoryError("Unknown mystery.")

    combos = [
        (p, m)
        for p, m in valid_combos()
        if (args.place is None or p == args.place)
        and (args.mystery is None or m == args.mystery)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    place, mystery = rng.choice(sorted(combos))
    name = args.name or rng.choice(CHILD_NAMES)
    helper = args.helper or rng.choice(HELPERS)
    return StoryParams(place=place, mystery=mystery, name=name, helper=helper)


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


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        lines.append(f"  {e.id:8} ({e.type:10}) {' '.join(bits)}")
    lines.append(f"  place: {world.place.label}")
    lines.append(f"  facts: {sorted(world.facts.keys())}")
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
        print(asp_program("#show valid/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible combos:\n")
        for p, m in combos:
            print(f"  {p:8} {m}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)

    samples: list[StorySample] = []
    if args.all:
        for p in CURATED:
            samples.append(generate(p))
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
            header = f"### {p.name}: {p.mystery} at {p.place}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


# Curated examples for --all
CURATED = [
    StoryParams(place="plaza", mystery="lost_bugle", name="Milo", helper="grandma"),
    StoryParams(place="plaza", mystery="echo_alarm", name="Nina", helper="dad"),
    StoryParams(place="plaza", mystery="birthday_surprise", name="Ruby", helper="friend"),
]


if __name__ == "__main__":
    main()

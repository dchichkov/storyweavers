#!/usr/bin/env python3
"""
storyworlds/worlds/housewife_turd_happy_ending_reconciliation_adventure.py
===========================================================================
A small standalone story world about a housewife, a turd, a little adventure,
and a happy reconciliation at the end.

The tale model:
- A housewife enjoys a small errand-like adventure around home and garden.
- She discovers a turd in the path, which blocks the cheerful plan.
- She cleans it up with a simple tool and learns who caused it.
- The misunderstanding is repaired, and the ending returns to warmth.

This world is intentionally small and constraint-checked:
- only a few settings and adventure routes exist,
- the turd must be plausibly encountered,
- the ending must include a real reconciliation,
- the story must resolve into a happy final image.

The world can be generated as text, JSON, or with Q&A.
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
    carried_by: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"woman", "housewife"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"man", "husband"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        if self.kind == "animal":
            return {"subject": "it", "object": "it", "possessive": "its"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str
    path: str
    afford: str
    detail: str


@dataclass
class Adventure:
    id: str
    verb: str
    gerund: str
    route: str
    risk: str
    keyword: str


@dataclass
class Cleanup:
    id: str
    tool: str
    action: str
    tail: str


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
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
        import copy as _copy

        clone = World(self.setting)
        clone.entities = _copy.deepcopy(self.entities)
        clone.paragraphs = [[]]
        clone.facts = dict(self.facts)
        clone.fired = set(self.fired)
        return clone


SETTINGS = {
    "kitchen": Setting(
        place="the kitchen",
        path="the tile by the back door",
        afford="walk",
        detail="The kitchen smelled like toast and morning light.",
    ),
    "garden": Setting(
        place="the garden",
        path="the stone path by the herbs",
        afford="walk",
        detail="The garden was bright, with leaves glittering after a rinse of water.",
    ),
    "yard": Setting(
        place="the yard",
        path="the narrow path near the fence",
        afford="walk",
        detail="The yard looked wide and breezy, with little footprints in the dust.",
    ),
}

ADVENTURES = {
    "stroll": Adventure(
        id="stroll",
        verb="follow the little path",
        gerund="following the little path",
        route="tiptoe down the path",
        risk="step on the mess",
        keyword="path",
    ),
    "seek": Adventure(
        id="seek",
        verb="look for the missing ribbon",
        gerund="looking for the missing ribbon",
        route="search around the path",
        risk="miss the mess",
        keyword="ribbon",
    ),
    "rescue": Adventure(
        id="rescue",
        verb="save the flower pot",
        gerund="saving the flower pot",
        route="hurry to the flower bed",
        risk="smear the mess",
        keyword="flower pot",
    ),
}

CLEANUPS = {
    "shovel": Cleanup(
        id="shovel",
        tool="a small shovel",
        action="scoop it up carefully",
        tail="scooped the turd into the compost bucket and washed her hands",
    ),
    "bag": Cleanup(
        id="bag",
        tool="a paper bag and a stick",
        action="pick it up without touching it",
        tail="wrapped the turd safely and threw the bag away",
    ),
    "water": Cleanup(
        id="water",
        tool="a bucket of water and soap",
        action="clean the path",
        tail="scrubbed the path until it shone again",
    ),
}

PEOPLE = ["Mara", "Nina", "Lena", "Tessa", "Rosa", "Ivy"]
HUSBANDS = ["Ben", "Owen", "Mark", "Jules", "Evan"]
PET_NAMES = ["Muffin", "Pip", "Biscuit"]


@dataclass
class StoryParams:
    place: str
    adventure: str
    cleanup: str
    name: str
    spouse: str
    pet: str
    seed: Optional[int] = None


CURATED = [
    StoryParams("garden", "stroll", "shovel", "Mara", "Ben", "Muffin"),
    StoryParams("yard", "seek", "bag", "Nina", "Owen", "Pip"),
    StoryParams("kitchen", "rescue", "water", "Lena", "Mark", "Biscuit"),
]


def setup_world(params: StoryParams) -> World:
    world = World(SETTINGS[params.place])
    wife = world.add(Entity(id=params.name, kind="character", type="housewife", label="housewife"))
    spouse = world.add(Entity(id=params.spouse, kind="character", type="husband", label="husband"))
    pet = world.add(Entity(id=params.pet, kind="animal", type="dog", label="small dog"))
    mess = world.add(Entity(
        id="turd",
        kind="thing",
        type="turd",
        label="turd",
        phrase="a little turd",
        caretaker=spouse.id,
    ))
    world.facts.update(
        wife=wife,
        spouse=spouse,
        pet=pet,
        mess=mess,
        setting=world.setting,
        adventure=ADVENTURES[params.adventure],
        cleanup=CLEANUPS[params.cleanup],
    )
    return world


def predict_mess(world: World, adventure: Adventure) -> bool:
    return adventure.keyword in {"path", "ribbon", "flower pot"}


def intro(world: World) -> None:
    wife = world.facts["wife"]
    adv = world.facts["adventure"]
    world.say(
        f"{wife.id} was a housewife who loved tiny adventures around {world.setting.place}."
    )
    world.say(
        f"She liked {adv.gerund}, because even an ordinary morning could feel like a quest."
    )


def setup_problem(world: World) -> None:
    wife = world.facts["wife"]
    spouse = world.facts["spouse"]
    pet = world.facts["pet"]
    world.para()
    world.say(world.setting.detail)
    world.say(
        f"{wife.id} went to {world.setting.path}, and there she found a turd right in the way."
    )
    world.say(
        f"{wife.id} frowned, because the dirty little lump could ruin the fun and make a bigger job."
    )
    world.say(
        f"At first, she thought {spouse.id} had forgotten to watch {pet.id}, so she felt a small knot of blame."
    )
    wife.memes["worry"] = wife.memes.get("worry", 0.0) + 1
    wife.memes["annoyance"] = wife.memes.get("annoyance", 0.0) + 1


def resolve(world: World) -> None:
    wife = world.facts["wife"]
    spouse = world.facts["spouse"]
    pet = world.facts["pet"]
    cleanup = world.facts["cleanup"]
    adv = world.facts["adventure"]

    world.para()
    world.say(
        f"Then {wife.id} took a breath and chose a kinder way forward."
    )
    world.say(
        f"She used {cleanup.tool} to {cleanup.action}, and soon {cleanup.tail}."
    )

    world.say(
        f"After that, {spouse.id} came over and explained that {pet.id} had been scared by a noisy cart, not naughty."
    )
    wife.memes["worry"] = 0.0
    wife.memes["annoyance"] = 0.0
    wife.memes["warmth"] = wife.memes.get("warmth", 0.0) + 1
    spouse.memes["relief"] = spouse.memes.get("relief", 0.0) + 1
    pet.memes["safe"] = pet.memes.get("safe", 0.0) + 1

    world.say(
        f"{wife.id} and {spouse.id} looked at each other, apologized for the quick blame, and forgave each other."
    )
    world.say(
        f"Together they laughed, petted {pet.id}, and finished the little adventure."
    )
    world.say(
        f"In the end, {wife.id} was {adv.gerund} again, the path was clean, and the morning felt bright and friendly."
    )


def tell(params: StoryParams) -> World:
    world = setup_world(params)
    intro(world)
    setup_problem(world)
    resolve(world)
    world.facts["resolved"] = True
    return world


def generation_prompts(world: World) -> list[str]:
    wife = world.facts["wife"]
    adv = world.facts["adventure"]
    cleanup = world.facts["cleanup"]
    return [
        f"Write a gentle adventure story about {wife.id}, a housewife, who finds a turd and fixes the day with {cleanup.tool}.",
        f"Tell a short happy-ending story where a housewife goes on a tiny {adv.verb} adventure and ends in reconciliation.",
        f"Write a child-friendly story about a housewife, a messy turd, and a warm apology that makes everything right again.",
    ]


def story_qa(world: World) -> list[QAItem]:
    wife = world.facts["wife"]
    spouse = world.facts["spouse"]
    pet = world.facts["pet"]
    cleanup = world.facts["cleanup"]
    adv = world.facts["adventure"]
    return [
        QAItem(
            question=f"Who was the story about?",
            answer=f"The story was about {wife.id}, a housewife who had a small adventure near {world.setting.place}.",
        ),
        QAItem(
            question=f"What did {wife.id} find on the path?",
            answer="She found a turd lying right in the way, and that made the little adventure messy for a moment.",
        ),
        QAItem(
            question=f"How did {wife.id} clean up the mess?",
            answer=f"She used {cleanup.tool} to handle it carefully, and then the path was clean again.",
        ),
        QAItem(
            question=f"What did {wife.id} and {spouse.id} do at the end?",
            answer=f"They apologized, forgave each other, and ended with a happy reconciliation while petting {pet.id}.",
        ),
        QAItem(
            question=f"Why did the story feel like an adventure?",
            answer=f"Because {wife.id} was not just staying still; she was {adv.gerund}, solving a problem, and finishing with a bright ending.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a turd?",
            answer="A turd is a piece of poop. It is dirty and needs to be cleaned up carefully.",
        ),
        QAItem(
            question="What does reconciliation mean?",
            answer="Reconciliation means people who were upset make peace again and feel friendly toward each other.",
        ),
        QAItem(
            question="What makes a story have a happy ending?",
            answer="A happy ending is when the problem gets solved and the characters finish feeling safe, calm, and glad.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== Prompts =="]
    for p in sample.prompts:
        lines.append(f"- {p}")
    lines.append("")
    lines.append("== Story QA ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== World QA ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for e in world.entities.values():
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        lines.append(f"{e.id}: {e.type} {' '.join(bits)}")
    return "\n".join(lines)


ASP_RULES = r"""
% The turd is a problem when it lies on the route of the adventure.
problem(A, T) :- adventure(A), turd(T), route(A, R), blocks(T, R).

% Cleanup is a valid reconciliation move when it can actually remove the mess.
fix(C, T) :- cleanup(C), turd(T), can_remove(C, T).

% A story is valid only if the adventure has a problem and a fix exists.
valid(P, A, C) :- place(P), adventure(A), cleanup(C), problem(A, _), fix(C, _).

% The ending is happy when reconciliation follows cleanup.
happy(P, A, C) :- valid(P, A, C).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid, s in SETTINGS.items():
        lines.append(asp.fact("place", pid))
        lines.append(asp.fact("path", pid, s.path))
    for aid, a in ADVENTURES.items():
        lines.append(asp.fact("adventure", aid))
        lines.append(asp.fact("route", aid, a.keyword))
        lines.append(asp.fact("blocks", "turd", a.keyword))
    for cid, c in CLEANUPS.items():
        lines.append(asp.fact("cleanup", cid))
        lines.append(asp.fact("can_remove", cid, "turd"))
    lines.append(asp.fact("turd", "turd"))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for place in SETTINGS:
        for adv in ADVENTURES:
            for cleanup in CLEANUPS:
                combos.append((place, adv, cleanup))
    return combos


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    combos = [c for c in valid_combos()
              if (args.place is None or c[0] == args.place)
              and (args.adventure is None or c[1] == args.adventure)
              and (args.cleanup is None or c[2] == args.cleanup)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, adv, cleanup = rng.choice(sorted(combos))
    name = args.name or rng.choice(PEOPLE)
    spouse = args.spouse or rng.choice(HUSBANDS)
    pet = args.pet or rng.choice(PET_NAMES)
    return StoryParams(place=place, adventure=adv, cleanup=cleanup, name=name, spouse=spouse, pet=pet)


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


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Housewife, turd, adventure, reconciliation, happy ending.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--adventure", choices=ADVENTURES)
    ap.add_argument("--cleanup", choices=CLEANUPS)
    ap.add_argument("--name")
    ap.add_argument("--spouse")
    ap.add_argument("--pet")
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


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    import asp
    a = set(asp_valid_combos())
    b = set(valid_combos())
    if a == b:
        print(f"OK: clingo gate matches valid_combos() ({len(a)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    if a - b:
        print(" only in clingo:", sorted(a - b))
    if b - a:
        print(" only in python:", sorted(b - a))
    return 1


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 20, 20):
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

    for idx, sample in enumerate(samples):
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.name}: {p.adventure} at {p.place}"
        elif len(samples) > 1:
            header = f"### variant {idx + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if idx < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()

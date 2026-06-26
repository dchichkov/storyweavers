#!/usr/bin/env python3
"""
A small storyworld for a rhyming kindness tale about lowering something safely
to help another child. The model tracks both physical height and emotional
warmth so the story can change from worry to kindness and back into peace.
"""

from __future__ import annotations

import argparse
import json
import os
import random
import sys
from dataclasses import dataclass, field, asdict
from typing import Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from results import QAItem, StoryError, StorySample  # noqa: E402


# ---------------------------------------------------------------------------
# Domain model
# ---------------------------------------------------------------------------

THRESHOLD = 1.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    is_lowerable: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def __post_init__(self) -> None:
        self.meters.setdefault("height", 0.0)
        self.meters.setdefault("care", 0.0)
        self.meters.setdefault("worry", 0.0)
        self.meters.setdefault("help", 0.0)
        self.meters.setdefault("reach", 0.0)
        self.memes.setdefault("kindness", 0.0)
        self.memes.setdefault("joy", 0.0)
        self.memes.setdefault("need", 0.0)
        self.memes.setdefault("pride", 0.0)
        self.memes.setdefault("relief", 0.0)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "mother", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]


@dataclass
class Place:
    name: str
    rhyme: str
    lower_zone: float
    can_see: bool = True


@dataclass
class Tool:
    id: str
    label: str
    phrase: str
    supports_lowering: bool = True


@dataclass
class StoryParams:
    place: str
    tool: str
    child_name: str
    child_type: str
    helper_name: str
    helper_type: str
    seed: Optional[int] = None


class World:
    def __init__(self, place: Place) -> None:
        self.place = place
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict[str, object] = {}
        self.fired: set[str] = set()

    def add(self, e: Entity) -> Entity:
        self.entities[e.id] = e
        return e

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


# ---------------------------------------------------------------------------
# Content
# ---------------------------------------------------------------------------

PLACES = {
    "hill": Place(name="the hill", rhyme="still", lower_zone=1.5),
    "porch": Place(name="the porch", rhyme="torch", lower_zone=1.2),
    "stage": Place(name="the stage", rhyme="page", lower_zone=1.4),
    "yard": Place(name="the yard", rhyme="card", lower_zone=1.0),
}

TOOLS = {
    "bucket": Tool(id="bucket", label="bucket", phrase="a bright red bucket"),
    "basket": Tool(id="basket", label="basket", phrase="a woven basket"),
    "lantern": Tool(id="lantern", label="lantern", phrase="a little lantern"),
}

CHILD_NAMES = ["Mina", "Toby", "Nora", "Pip", "Lila", "Rory", "Zoe", "Ben"]
HELPER_NAMES = ["Maya", "Otis", "Iris", "Noah", "Ari", "Mila", "Ezra", "June"]

RHYMES = {
    "setup": [
        "On a bright, light day, the {child} came to play.",
        "{child} loved to sing and swing and grin, with a happy little spin.",
    ],
    "problem": [
        "But the {tool} sat high, high up in sight, too far away to grasp just right.",
        "The {helper} saw the reach and knew the wish was not quite a dish.",
    ],
    "turn": [
        "So {helper} said, “Let kindness lead; I can help with what you need.”",
        "With careful hands and a gentle glow, {helper} chose to lower it slow.",
    ],
    "end": [
        "Down it came with a soft, small hum, and warm smiles bloomed for everyone.",
        "Then joy grew bright, and worries fell; the kind deed made the whole day swell.",
    ],
}

GIRL_TYPES = {"girl", "mother", "woman"}
BOY_TYPES = {"boy", "father", "man"}


# ---------------------------------------------------------------------------
# World logic
# ---------------------------------------------------------------------------

def build_world(params: StoryParams) -> World:
    place = PLACES[params.place]
    tool = TOOLS[params.tool]
    world = World(place)

    child = world.add(Entity(
        id=params.child_name,
        kind="character",
        type=params.child_type,
        label=params.child_name,
        phrase=params.child_name,
        meters={"height": 1.0, "care": 0.0, "worry": 0.0, "help": 0.0, "reach": 0.6},
        memes={"kindness": 0.1, "joy": 0.2, "need": 0.0, "pride": 0.1, "relief": 0.0},
    ))
    helper = world.add(Entity(
        id=params.helper_name,
        kind="character",
        type=params.helper_type,
        label=params.helper_name,
        phrase=params.helper_name,
        meters={"height": 1.1, "care": 0.6, "worry": 0.0, "help": 0.0, "reach": 1.0},
        memes={"kindness": 0.7, "joy": 0.3, "need": 0.0, "pride": 0.0, "relief": 0.0},
    ))
    item = world.add(Entity(
        id=tool.id,
        kind="thing",
        type=tool.label,
        label=tool.label,
        phrase=tool.phrase,
        owner=child.id,
        is_lowerable=True,
        meters={"height": place.lower_zone + 0.7, "care": 0.0, "worry": 0.0, "help": 0.0, "reach": 0.0},
        memes={"kindness": 0.0, "joy": 0.0, "need": 0.0, "pride": 0.0, "relief": 0.0},
    ))

    world.facts.update(child=child, helper=helper, item=item, place=place, tool=tool)
    return world


def problem_is_reasonable(world: World) -> bool:
    item = world.facts["item"]
    child = world.facts["child"]
    return item.meters["height"] > child.meters["reach"]


def can_help_by_lowering(world: World) -> bool:
    item = world.facts["item"]
    helper = world.facts["helper"]
    return item.is_lowerable and helper.meters["help"] >= 0.0


def do_setup(world: World) -> None:
    child = world.facts["child"]
    item = world.facts["item"]
    place = world.facts["place"]
    world.say(RHYMES["setup"][0].format(child=child.id))
    world.say(RHYMES["setup"][1].format(child=child.id))
    world.say(f"At {place.name}, {child.id} spied {item.phrase} high near the sky.")


def do_problem(world: World) -> None:
    child = world.facts["child"]
    helper = world.facts["helper"]
    item = world.facts["item"]
    child.memes["need"] += 1
    child.meters["worry"] += 1
    helper.meters["care"] += 1
    world.say(RHYMES["problem"][0].format(tool=item.label))
    world.say(
        f"{helper.id} noticed {child.id} stretch and strain, and gave a kind, calm glance again."
    )


def do_turn(world: World) -> None:
    helper = world.facts["helper"]
    child = world.facts["child"]
    item = world.facts["item"]
    helper.memes["kindness"] += 1
    helper.meters["help"] += 1
    world.say(RHYMES["turn"][0].format(helper=helper.id))
    world.say(RHYMES["turn"][1].format(helper=helper.id))
    item.meters["height"] = world.place.lower_zone - 0.2
    child.meters["reach"] += 0.6
    child.memes["joy"] += 0.5
    helper.memes["pride"] += 0.2


def do_resolution(world: World) -> None:
    child = world.facts["child"]
    helper = world.facts["helper"]
    item = world.facts["item"]
    child.memes["relief"] += 1
    helper.memes["relief"] += 1
    child.meters["worry"] = 0.0
    item.meters["worry"] = 0.0
    world.say(RHYMES["end"][0])
    world.say(
        f"{child.id} could reach the {item.label} at last, and {helper.id} smiled with peaceful bliss."
    )
    world.say(f"The kind little lowering made the whole day ring with a happy spring.")


def tell_story(world: World) -> None:
    do_setup(world)
    world.para()
    do_problem(world)
    world.para()
    if can_help_by_lowering(world):
        do_turn(world)
        do_resolution(world)
    else:
        raise StoryError("No reasonable lowering fix exists for this setup.")


# ---------------------------------------------------------------------------
# Parameter resolution
# ---------------------------------------------------------------------------

def valid_combos() -> list[tuple[str, str]]:
    return [(p, t) for p in PLACES for t in TOOLS]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A rhyming kindness storyworld about lowering.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--tool", choices=TOOLS)
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
    combos = valid_combos()
    if args.place:
        combos = [c for c in combos if c[0] == args.place]
    if args.tool:
        combos = [c for c in combos if c[1] == args.tool]
    if not combos:
        raise StoryError("No valid place/tool combination matches the given options.")

    place, tool = rng.choice(combos)
    child_type = rng.choice(["girl", "boy"])
    helper_type = rng.choice(["mother", "father"])
    child_name = rng.choice(CHILD_NAMES)
    helper_name = rng.choice([n for n in HELPER_NAMES if n != child_name])
    return StoryParams(
        place=place,
        tool=tool,
        child_name=child_name,
        child_type=child_type,
        helper_name=helper_name,
        helper_type=helper_type,
    )


# ---------------------------------------------------------------------------
# QA
# ---------------------------------------------------------------------------

def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a short rhyming story for a little child about kindness and the word "lower".',
        f"Tell a gentle story where {f['child'].id} cannot reach {f['item'].label} at {f['place'].name}, "
        f"and {f['helper'].id} helps by lowering it.",
        "Write a child-facing story with a problem, a kind fix, and a happy ending that rhymes lightly.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child = f["child"]
    helper = f["helper"]
    item = f["item"]
    place = f["place"]
    return [
        QAItem(
            question=f"What did {child.id} want to reach at {place.name}?",
            answer=f"{child.id} wanted to reach the {item.label}, which was sitting too high at {place.name}.",
        ),
        QAItem(
            question=f"How did {helper.id} show kindness in the story?",
            answer=f"{helper.id} showed kindness by helping lower the {item.label} so {child.id} could get it safely.",
        ),
        QAItem(
            question=f"What changed by the end?",
            answer=f"By the end, the {item.label} was lowered, the worry was gone, and both children felt happy and relieved.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does it mean to lower something?",
            answer="To lower something means to move it down to a lower place, often carefully and gently.",
        ),
        QAItem(
            question="What is kindness?",
            answer="Kindness means being gentle, caring, and helpful to someone else.",
        ),
        QAItem(
            question="Why is it helpful to lower an item for a child?",
            answer="It is helpful because a child may not be able to reach something high on their own.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    for p in sample.prompts:
        lines.append(p)
    lines.append("")
    lines.append("== story qa ==")
    for q in sample.story_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    lines.append("")
    lines.append("== world qa ==")
    for q in sample.world_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------

ASP_RULES = r"""
place(P) :- setting(P).
tool(T) :- lowerable(T).

problem(P,T) :- place(P), tool(T).

kind_fix(P,T) :- problem(P,T).
valid_story(P,T) :- kind_fix(P,T).
#show valid_story/2.
"""


def asp_facts() -> str:
    import storyworlds.asp as asp
    lines = []
    for pid in PLACES:
        lines.append(asp.fact("setting", pid))
    for tid in TOOLS:
        lines.append(asp.fact("lowerable", tid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple[str, str]]:
    import storyworlds.asp as asp
    model = asp.one_model(asp_program("#show valid_story/2."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    py = set(valid_combos())
    asp_set = set(asp_valid_combos())
    if py == asp_set:
        print(f"OK: ASP and Python agree on {len(py)} combinations.")
        return 0
    print("MISMATCH between ASP and Python:")
    if py - asp_set:
        print("  only in Python:", sorted(py - asp_set))
    if asp_set - py:
        print("  only in ASP:", sorted(asp_set - py))
    return 1


# ---------------------------------------------------------------------------
# Generation / emission
# ---------------------------------------------------------------------------

def generate(params: StoryParams) -> StorySample:
    world = build_world(params)
    tell_story(world)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for e in world.entities.values():
        lines.append(
            f"{e.id}: type={e.type} meters={{{', '.join(f'{k}={v:.2f}' for k, v in e.meters.items() if v)}}} "
            f"memes={{{', '.join(f'{k}={v:.2f}' for k, v in e.memes.items() if v)}}}"
        )
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
# Main
# ---------------------------------------------------------------------------

CURATED = [
    StoryParams(place="hill", tool="bucket", child_name="Mina", child_type="girl", helper_name="Maya", helper_type="mother"),
    StoryParams(place="porch", tool="basket", child_name="Toby", child_type="boy", helper_name="Iris", helper_type="father"),
    StoryParams(place="stage", tool="lantern", child_name="Lila", child_type="girl", helper_name="June", helper_type="mother"),
    StoryParams(place="yard", tool="bucket", child_name="Ben", child_type="boy", helper_name="Ari", helper_type="father"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid_story/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible story combos:")
        for place, tool in combos:
            print(f"  {place:6} {tool}")
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
            try:
                params = resolve_params(args, random.Random(seed))
            except StoryError as err:
                print(err)
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
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()

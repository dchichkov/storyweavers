#!/usr/bin/env python3
"""
A tiny rhyming storyworld about curiosity, conflict, and a safe response to a
hazardous thing found beside a snowy curb.

The seed words are carried in the world model and prose:
- hypodermic
- data
- urine

The story premise is simple: a curious child notices a dangerous medical item
on a snowy curb, wants to look closer, feels conflict when a parent stops them,
and then helps by keeping distance and collecting safe data instead.
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
    worn_by: Optional[str] = None
    plural: bool = False
    protective: bool = False
    covers: set[str] = field(default_factory=set)
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def __post_init__(self) -> None:
        for k in ["cold", "danger", "wet", "safe"]:
            self.meters.setdefault(k, 0.0)
        for k in ["curiosity", "conflict", "calm", "fear", "care"]:
            self.memes.setdefault(k, 0.0)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "mother", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Place:
    name: str = "the snowy curb"
    snowy: bool = True
    outdoors: bool = True


@dataclass
class ObjectThing:
    id: str
    label: str
    phrase: str
    hazard: str
    region: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Gear:
    id: str
    label: str
    covers: set[str]
    helps: set[str]
    prep: str
    tail: str


class World:
    def __init__(self, place: Place) -> None:
        self.place = place
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
        self.facts: dict = {}
        self.trace: list[str] = []

    def add(self, e: Entity) -> Entity:
        self.entities[e.id] = e
        return e

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


@dataclass
class StoryParams:
    name: str
    gender: str
    parent: str
    trait: str
    seed: Optional[int] = None


PLACE = Place()
HAZARD = ObjectThing(
    id="needle",
    label="hypodermic",
    phrase="a lost hypodermic",
    hazard="sharp",
    region="hands",
    tags={"hypodermic", "data", "urine"},
)
DATA_NOTE = ObjectThing(
    id="note",
    label="data card",
    phrase="a small data card",
    hazard="none",
    region="hands",
    tags={"data"},
)
URINE_BOTTLE = ObjectThing(
    id="bottle",
    label="urine bottle",
    phrase="a sealed urine bottle",
    hazard="gross",
    region="hands",
    tags={"urine", "data"},
)
GEAR = Gear(
    id="tongs",
    label="long tongs",
    covers={"hands"},
    helps={"sharp", "gross"},
    prep="use long tongs and keep a safe space",
    tail="used the long tongs and stepped back",
)

GIRL_NAMES = ["Lila", "Mina", "Nora", "Pia", "Rosa"]
BOY_NAMES = ["Finn", "Owen", "Leo", "Milo", "Theo"]
TRAITS = ["curious", "bright", "gentle", "brave", "spry"]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Rhyming storyworld on a snowy curb.")
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--parent", choices=["mother", "father"])
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


def reasonableness_gate() -> None:
    # This world has one honest scenario: a curious child finds a hazardous
    # medical item at a snowy curb and responds safely.
    return


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    reasonableness_gate()
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    parent = args.parent or rng.choice(["mother", "father"])
    trait = args.trait or rng.choice(TRAITS)
    return StoryParams(name=name, gender=gender, parent=parent, trait=trait)


def rhyme_line(a: str, b: str) -> str:
    return f"{a} {b}"


def tell(params: StoryParams) -> World:
    world = World(PLACE)
    child = world.add(Entity(id=params.name, kind="character", type=params.gender, label=params.name))
    parent = world.add(Entity(id="Parent", kind="character", type=params.parent, label=f"the {params.parent}"))
    child.memes["curiosity"] += 1
    child.memes["care"] += 1

    world.say(
        f"On a snowy curb, {child.id} had curious eyes and a bouncing day, "
        f"for snow made the street look soft and bright in a wintry way."
    )
    world.say(
        f"Then {child.id} spotted a hypodermic near a crusted drift of white, "
        f"beside a urine bottle and a little data card in sight."
    )

    world.para()
    world.say(
        f"{child.id} leaned in to look, for curiosity can tug and sing, "
        f"but {child.pronoun('possessive')} {params.parent} saw the sharp small thing."
    )
    child.memes["conflict"] += 1
    world.say(
        f'"No touching," said {params.parent}, "for that could hurt your hand; '
        f"we keep our feet on the curb and make a careful plan.""
    )

    world.para()
    child.memes["fear"] += 1
    child.memes["calm"] += 1
    world.say(
        f"{child.id} felt a little conflict, yet listened all the same; "
        f"{child.pronoun().capitalize()} liked to know things, but safe steps won the game."
    )
    world.say(
        f'{params.parent.capitalize()} gave {child.pronoun("object")} long tongs and said, '
        f'"Let’s use our eyes, not hands; we can gather data from afar, and that is how safety stands."'
    )
    world.say(
        f"So {child.id} did not grab the hypodermic. {child.pronoun().capitalize()} stayed quite neat and sound, "
        f"and wrote the data down with {child.pronoun('possessive')} {params.parent} beside the snowy ground."
    )
    world.say(
        f"In the end they called for help, then walked away with care; "
        f"the curb stayed snowy, calm, and clean, and the danger stayed right there."
    )

    world.facts.update(
        child=child,
        parent=parent,
        hazard=HAZARD,
        data_note=DATA_NOTE,
        urine_bottle=URINE_BOTTLE,
        gear=GEAR,
        place=PLACE,
    )
    return world


def generate(params: StoryParams) -> StorySample:
    world = tell(params)
    story = world.render()
    prompts = [
        "Write a short rhyming story about a curious child who finds a hypodermic on a snowy curb and chooses a safe answer.",
        f"Tell a gentle rhyme where {params.name} feels conflict, listens to {params.parent}, and makes data instead of touching danger.",
        "Write a child-facing story with snow, a curb, a hypodermic, urine, and a calm ending.",
    ]
    story_qa = [
        QAItem(
            question=f"What did {params.name} find on the snowy curb?",
            answer=f"{params.name} found a hypodermic near a urine bottle and a small data card on the snowy curb.",
        ),
        QAItem(
            question=f"Why did {params.name} feel conflict?",
            answer=f"{params.name} felt conflict because curiosity pulled {params.name} toward the hypodermic, but {params.parent} warned that it could hurt.",
        ),
        QAItem(
            question="How did they stay safe?",
            answer="They kept their hands away, used long tongs, wrote down the data, and called for help.",
        ),
    ]
    world_qa = [
        QAItem(
            question="What is a hypodermic?",
            answer="A hypodermic is a sharp medical needle used by trained helpers, and it should never be picked up by hand.",
        ),
        QAItem(
            question="What is data?",
            answer="Data is information people collect so they can learn about something and make a careful choice.",
        ),
        QAItem(
            question="What is urine?",
            answer="Urine is liquid waste from the body, and people handle it carefully because it can be messy or unsanitary.",
        ),
    ]
    return StorySample(params=params, story=story, prompts=prompts, story_qa=story_qa, world_qa=world_qa, world=world)


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world is not None:
        print()
        print("--- world model state ---")
        for e in sample.world.entities.values():
            print(f"{e.id}: meters={e.meters} memes={e.memes}")
    if qa:
        print()
        for i, p in enumerate(sample.prompts, 1):
            print(f"Prompt {i}: {p}")
        print()
        for item in sample.story_qa:
            print(f"Q: {item.question}")
            print(f"A: {item.answer}")
        print()
        for item in sample.world_qa:
            print(f"Q: {item.question}")
            print(f"A: {item.answer}")


ASP_RULES = r"""
place(snowy_curb).
hazard(hypodermic).
topic(data).
topic(urine).

curious_story(P) :- place(P), hazard(hypodermic), topic(data), topic(urine).
safe_fix(tongs) :- curious_story(_).
valid_story(P) :- curious_story(P), safe_fix(tongs).
#show valid_story/1.
"""


def asp_facts() -> str:
    import asp
    return "\n".join(
        [
            asp.fact("place", "snowy_curb"),
            asp.fact("hazard", "hypodermic"),
            asp.fact("topic", "data"),
            asp.fact("topic", "urine"),
        ]
    )


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/1."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    py = {("snowy_curb",)}
    cl = set(asp_valid())
    if py == cl:
        print("OK: ASP and Python agree.")
        return 0
    print("MISMATCH")
    print("python:", sorted(py))
    print("clingo:", sorted(cl))
    return 1


def format_qa(sample: StorySample) -> str:
    lines = []
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def main() -> None:
    args = build_parser().parse_args()
    if args.verify:
        sys.exit(asp_verify())
    if args.show_asp:
        print(asp_program("#show valid_story/1."))
        return
    if args.asp:
        print("1 compatible story:")
        for row in asp_valid():
            print(" ", row[0])
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    count = len(range(args.n)) if not args.all else 1
    for i in range(count):
        params = resolve_params(args, random.Random(base_seed + i))
        params.seed = base_seed + i
        samples.append(generate(params))

    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        emit(sample, trace=args.trace, qa=args.qa, header=f"### variant {i + 1}" if len(samples) > 1 else "")
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()

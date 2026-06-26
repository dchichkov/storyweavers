#!/usr/bin/env python3
"""
storyworlds/worlds/teeter_wilt_penitentiary_rhyme_nursery_rhyme.py
===================================================================

A tiny nursery-rhyme storyworld about a wobbling teeter-totter, a wilting
flower, and a kind plan near the penitentiary garden.

Premise:
- A child loves to teeter on a seesaw beside a small garden.
- The child also loves carrying a thirsty flower.
- A dry, sunny stretch makes the flower wilt.

Turn:
- The child notices the flower droop while the seesaw teeters.
- A helper explains that the garden near the penitentiary has a water pump.
- The child must choose: keep wobbling, or go water the flower.

Resolution:
- The child waters the flower, the wilt eases, and the rhyme ends with the
  flower bright again beside the teetering board.

The domain stays small and classical: one child, one toy, one plant, one helper,
one place, one problem, one fix.
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
    kind: str = "thing"  # character | thing
    label: str = ""
    type: str = ""
    plural: bool = False
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def __post_init__(self):
        self.meters.setdefault("wilt", 0.0)
        self.meters.setdefault("bounce", 0.0)
        self.memes.setdefault("worry", 0.0)
        self.memes.setdefault("joy", 0.0)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "mother", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class World:
    place: str
    entities: dict[str, Entity] = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    facts: dict = field(default_factory=dict)

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

    def copy(self) -> "World":
        import copy
        return World(self.place, entities=copy.deepcopy(self.entities), paragraphs=[[]], facts=dict(self.facts))


# ---------------------------------------------------------------------------
# Params / registries
# ---------------------------------------------------------------------------
@dataclass
class StoryParams:
    place: str
    name: str
    gender: str
    helper: str
    seed: Optional[int] = None


PLACES = {
    "yard": "the sunny yard by the fence",
    "garden": "the little garden near the penitentiary wall",
    "lane": "the narrow lane beside the garden gate",
}

NAMES = {
    "girl": ["Mia", "Luna", "Nora", "Ivy", "Ada"],
    "boy": ["Owen", "Theo", "Finn", "Ben", "Leo"],
}

HELPERS = {
    "gardener": Entity(id="gardener", kind="character", label="gardener", type="woman"),
    "guard": Entity(id="guard", kind="character", label="guard", type="man"),
}

ASP_RULES = r"""
place(yard).
place(garden).
place(lane).

character(child).
character(gardener).
character(guard).

thing(teeterboard).
thing(flower).
thing(pail).

at_risk(flower, wilt).
needs(wilt, water).

can_fix(garden, flower) :- place(garden), thing(flower).
valid_place(P) :- place(P).
valid_story(P) :- valid_place(P), can_fix(P, flower).
#show valid_story/1.
"""


def asp_facts() -> str:
    import asp
    lines = [
        asp.fact("place", "yard"),
        asp.fact("place", "garden"),
        asp.fact("place", "lane"),
        asp.fact("thing", "teeterboard"),
        asp.fact("thing", "flower"),
        asp.fact("thing", "pail"),
        asp.fact("needs", "wilt", "water"),
        asp.fact("at_risk", "flower", "wilt"),
        asp.fact("fixes", "pail", "water"),
        asp.fact("name_ok", "girl"),
        asp.fact("name_ok", "boy"),
    ]
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_places() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/1."))
    return sorted(set(asp.atoms(model, "valid_story")))


# ---------------------------------------------------------------------------
# Reasonableness gate
# ---------------------------------------------------------------------------
def valid_storyplace(place: str) -> bool:
    return place in PLACES


def explain_rejection(place: str) -> str:
    return f"(No story: {place!r} is not one of the little rhyme places.)"


# ---------------------------------------------------------------------------
# Story engine
# ---------------------------------------------------------------------------
def tell(params: StoryParams) -> World:
    if not valid_storyplace(params.place):
        raise StoryError(explain_rejection(params.place))

    world = World(PLACES[params.place])

    child = world.add(Entity(id=params.name, kind="character", label=params.name, type=params.gender))
    helper = world.add(Entity(id=params.helper, kind="character", label=params.helper, type="woman" if params.helper == "gardener" else "man"))
    board = world.add(Entity(id="teeterboard", kind="thing", label="teeter board", type="teeterboard"))
    flower = world.add(Entity(id="flower", kind="thing", label="flower", type="flower", caretaker=helper.id))
    pail = world.add(Entity(id="pail", kind="thing", label="pail of water", type="pail", owner=helper.id))

    # Act 1
    world.say(f"Little {child.id} loved to teeter on the teeter board, up and down in a merry rhyme.")
    world.say(f"{child.pronoun().capitalize()} also loved a bright flower carried close beside {child.pronoun('possessive')} heart.")
    world.say(f"Near the penitentiary garden, the air was dry, and the little flower began to wilt.")

    # Act 2
    world.para()
    child.memes["worry"] += 1
    board.meters["bounce"] += 1
    flower.meters["wilt"] += 1
    world.say(f"{child.id} saw the wilt and gave the board a teetering go, but the flower only drooped more and more.")
    world.say(f"The helper said, \"A pail of water will mend the day; come and we can make the flower sway.\"")
    world.say(f"{child.id} looked from the teeter board to the thirsty bloom, and chose the safer, kinder way.")

    # Act 3
    world.para()
    flower.meters["wilt"] = 0.0
    child.memes["worry"] = 0.0
    child.memes["joy"] += 1
    world.say(f"{child.id} carried the pail, and the flower drank.")
    world.say(f"With one cool splash, the wilt slid off, and the petals perked and pinked.")
    world.say(f"Then {child.id} teetered once more, with {flower.label} bright in the garden light, and the little rhyme ended right.")

    world.facts.update(child=child, helper=helper, board=board, flower=flower, pail=pail, place=params.place)
    return world


# ---------------------------------------------------------------------------
# Q&A
# ---------------------------------------------------------------------------
def generation_prompts(world: World) -> list[str]:
    p = world.facts["place"]
    child = world.facts["child"]
    return [
        f'Write a short nursery rhyme about {child.id}, a teeter board, and a flower that wilts near {p}.',
        f'Tell a gentle story for little children where a child named {child.id} must choose between teetering and watering a wilted flower.',
        f'Write a simple rhyming tale that includes the words "teeter", "wilt", and "penitentiary".',
    ]


def story_qa(world: World) -> list[QAItem]:
    child = world.facts["child"]
    helper = world.facts["helper"]
    place = world.facts["place"]
    flower = world.facts["flower"]
    return [
        QAItem(
            question=f"What did {child.id} love to do at {place}?",
            answer=f"{child.id} loved to teeter on the teeter board and play beside the little flower.",
        ),
        QAItem(
            question=f"Why did the flower in the story wilt?",
            answer="The air was dry, so the little flower drooped and wilted until someone brought water.",
        ),
        QAItem(
            question=f"Who helped {child.id} fix the wilted flower?",
            answer=f"The {helper.label} helped by offering a pail of water and a kinder way to play.",
        ),
        QAItem(
            question=f"What changed by the end of the story?",
            answer=f"By the end, the flower was bright again, and {child.id} could teeter happily beside it.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does wilt mean for a flower?",
            answer="When a flower wilts, it droops and looks tired because it needs water or better care.",
        ),
        QAItem(
            question="What is a teeter board?",
            answer="A teeter board is a board that goes up and down when children play on it together.",
        ),
        QAItem(
            question="What is a penitentiary?",
            answer="A penitentiary is a place where grown-ups may stay if they broke serious laws.",
        ),
        QAItem(
            question="What does a nursery rhyme sound like?",
            answer="A nursery rhyme sounds short, gentle, and musical, with simple words that can repeat and sing.",
        ),
    ]


# ---------------------------------------------------------------------------
# Serialization / formatting
# ---------------------------------------------------------------------------
def format_qa(sample: StorySample) -> str:
    lines = []
    lines.append("== (1) Generation prompts ==")
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
        bits = []
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        lines.append(f"  {e.id:10} ({e.kind:7}) {e.label:14} {' '.join(bits)}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
def asp_verify() -> int:
    import asp
    py = {("yard",), ("garden",), ("lane",)}
    clingo = set(asp_valid_places())
    if py == clingo:
        print(f"OK: clingo gate matches Python gate ({len(py)} places).")
        return 0
    print("MISMATCH between clingo and Python gate.")
    print("python:", sorted(py))
    print("clingo:", sorted(clingo))
    return 1


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A tiny nursery-rhyme storyworld about teeter, wilt, and penitentiary.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--name")
    ap.add_argument("--helper", choices=["gardener", "guard"])
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
    place = args.place or rng.choice(list(PLACES))
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(NAMES[gender])
    helper = args.helper or rng.choice(["gardener", "guard"])
    if place not in PLACES:
        raise StoryError(explain_rejection(place))
    return StoryParams(place=place, name=name, gender=gender, helper=helper)


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


CURATED = [
    StoryParams(place="garden", name="Mia", gender="girl", helper="gardener"),
    StoryParams(place="yard", name="Leo", gender="boy", helper="guard"),
    StoryParams(place="lane", name="Nora", gender="girl", helper="gardener"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid_story/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        model = asp.one_model(asp_program("#show valid_story/1."))
        vals = asp.atoms(model, "valid_story")
        print(f"{len(vals)} valid story places:")
        for v in vals:
            print(" ", v[0])
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen = set()
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
            header = f"### {p.name}: {p.place} ({p.gender}, helper={p.helper})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()

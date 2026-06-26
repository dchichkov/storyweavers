#!/usr/bin/env python3
"""
storyworlds/worlds/tram_nanny_mystery_to_solve_comedy.py
========================================================

A small standalone story world about a tram ride, a nanny, and a funny little
mystery that gets solved by looking closely instead of guessing wildly.

Premise:
- A child rides a tram with a nanny.
- Something strange is happening: a sound, a missing thing, or a mixed-up clue.
- The nanny and child follow clues.
- The answer is ordinary, but the search is playful and a little silly.

The world is modeled with physical meters and emotional memes so the story is
driven by state changes, not by a frozen paragraph with swapped names.
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
    carried_by: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def meter(self, key: str) -> float:
        return self.meters.get(key, 0.0)

    def meme(self, key: str) -> float:
        return self.memes.get(key, 0.0)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "woman", "mother", "nanny"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man", "father"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Tram:
    name: str = "the tram"
    stop: str = "the big city stop"
    route: str = "the bumpy street"
    sound: str = "ding-ding"
    place: str = "inside the tram"


@dataclass
class Mystery:
    id: str
    question: str
    clue1: str
    clue2: str
    clue3: str
    culprit: str
    reveal: str
    comic_mislead: str
    action: str
    solved_with: str
    tags: set[str] = field(default_factory=set)


@dataclass
class StoryParams:
    mystery: str
    name: str
    child_type: str
    nanny_type: str
    seed: Optional[int] = None


class World:
    def __init__(self, tram: Tram):
        self.tram = tram
        self.entities: dict[str, Entity] = {}
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
        import copy
        clone = World(self.tram)
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        clone.facts = dict(self.facts)
        return clone


def _tr_narrate(world: World, text: str) -> None:
    world.say(text)


def introduce(world: World, child: Entity, nanny: Entity) -> None:
    _tr_narrate(
        world,
        f"{child.id} was riding {world.tram.name} with {nanny.label}, and "
        f"{child.pronoun('subject')} had the sort of face that could spot a strange thing from a seat away.",
    )


def start_mystery(world: World, child: Entity, mystery: Mystery) -> None:
    child.memes["curiosity"] = child.meme("curiosity") + 1
    world.say(
        f"Then a mystery arrived: {mystery.question} "
        f"The sound seemed to pop up from nowhere, which made {child.id} wrinkle {child.pronoun('possessive')} nose."
    )


def clue_one(world: World, mystery: Mystery) -> None:
    world.say(mystery.clue1)


def clue_two(world: World, mystery: Mystery) -> None:
    world.say(mystery.clue2)


def clue_three(world: World, mystery: Mystery) -> None:
    world.say(mystery.clue3)


def mislead(world: World, mystery: Mystery) -> None:
    world.say(
        f"{mystery.comic_mislead} That guess was funny, but it was also wrong."
    )


def investigate(world: World, child: Entity, nanny: Entity, mystery: Mystery) -> None:
    child.memes["confused"] = child.meme("confused") + 1
    nanny.memes["patient"] = nanny.meme("patient") + 1
    world.say(
        f"{nanny.label} did not rush. Instead, {nanny.pronoun('subject')} "
        f"leaned down and said, \"Let's look with our eyes, not our guesses.\" "
        f"So they checked the floor, the seat, and the little bag beside them."
    )


def solve(world: World, child: Entity, nanny: Entity, mystery: Mystery) -> None:
    child.memes["confused"] = 0.0
    child.memes["joy"] = child.meme("joy") + 1
    nanny.memes["joy"] = nanny.meme("joy") + 1
    world.say(
        f"At last they found it: {mystery.reveal} "
        f"The mystery had been caused by {mystery.culprit}, and once they saw it, the whole tram ride felt silly instead of spooky."
    )
    world.say(
        f"{child.id} laughed so hard {child.pronoun('subject')} had to hold the rail, "
        f"and {nanny.label} smiled like {nanny.pronoun('subject')} had solved a tiny detective case before the next stop."
    )


def complete(world: World, child: Entity, nanny: Entity, mystery: Mystery) -> None:
    world.say(
        f"By the time {world.tram.stop} came into view, the answer was safe in plain sight and {world.tram.sound} sounded like a happy joke."
    )


MYSTERIES: dict[str, Mystery] = {
    "jingle": Mystery(
        id="jingle",
        question="Who keeps making the jingly sound under the seat?",
        clue1="A tiny jingle came again whenever the tram turned left.",
        clue2="It did not sound like a mouse, a trumpet, or a moonbeam.",
        clue3="The noise got louder whenever the bag with snacks slid across the seat.",
        culprit="a tin of coins in the snack bag",
        reveal="a small tin of coins had rolled into the lunch bag and was clinking against the crackers",
        comic_mislead="For a moment, the child blamed an invisible bus turtle.",
        action="jingle",
        solved_with="careful looking",
        tags={"sound", "bag", "coins"},
    ),
    "tap": Mystery(
        id="tap",
        question="Who is tapping so politely on the floor?",
        clue1="A tap-tap sounded under the bench like a tiny knock-knock joke.",
        clue2="The sound stopped when the tram was still and came back when it moved.",
        clue3="It was coming from right near the child's shoe, which was a very suspicious shoe indeed.",
        culprit="a loose marble in the shoe",
        reveal="a marble had slipped into the child's shoe and tapped the floor with every step",
        comic_mislead="The child accused the tram of having ticklish toes.",
        action="tap",
        solved_with="taking off the shoe and shaking it",
        tags={"shoe", "floor", "marble"},
    ),
    "hide": Mystery(
        id="hide",
        question="Where did the red ribbon hide?",
        clue1="The ribbon was easy to see a moment ago and then vanished like a magician's napkin.",
        clue2="It was not on the seat, not on the floor, and not in the child's pockets.",
        clue3="The nanny spotted one bright corner peeking out from the toy basket near the window.",
        culprit="the toy basket by the window",
        reveal="the ribbon had slipped into the toy basket and tucked itself under a stuffed bear",
        comic_mislead="The child blamed a sneaky breeze with excellent manners.",
        action="hide",
        solved_with="peeking into the basket",
        tags={"ribbon", "basket", "toy"},
    ),
}

CHILD_NAMES = ["Mia", "Leo", "Nora", "Finn", "Ava", "Theo", "Luca", "Zoe"]
CHILD_TYPES = ["girl", "boy"]
NANNY_TYPES = ["nanny", "woman", "man"]
TRAM = Tram()


def valid_combos() -> list[tuple[str, str, str]]:
    out = []
    for mystery_id, mystery in MYSTERIES.items():
        for child_type in CHILD_TYPES:
            for nanny_type in NANNY_TYPES:
                out.append((mystery_id, child_type, nanny_type))
    return out


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A comedic tram mystery story world.")
    ap.add_argument("--mystery", choices=sorted(MYSTERIES))
    ap.add_argument("--name")
    ap.add_argument("--child-type", choices=CHILD_TYPES)
    ap.add_argument("--nanny-type", choices=NANNY_TYPES)
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
    if args.mystery and args.mystery not in MYSTERIES:
        raise StoryError("Unknown mystery.")
    mystery = args.mystery or rng.choice(sorted(MYSTERIES))
    child_type = args.child_type or rng.choice(CHILD_TYPES)
    nanny_type = args.nanny_type or rng.choice(NANNY_TYPES)
    name = args.name or rng.choice(CHILD_NAMES)
    return StoryParams(mystery=mystery, name=name, child_type=child_type, nanny_type=nanny_type)


def tell(params: StoryParams) -> World:
    mystery = MYSTERIES[params.mystery]
    world = World(TRAM)

    child = world.add(Entity(id=params.name, kind="character", type=params.child_type, label=params.name))
    nanny = world.add(Entity(id="Nanny", kind="character", type=params.nanny_type, label="the nanny"))

    child.memes["curiosity"] = 1.0

    introduce(world, child, nanny)
    world.para()
    start_mystery(world, child, mystery)
    clue_one(world, mystery)
    mislead(world, mystery)
    clue_two(world, mystery)
    investigate(world, child, nanny, mystery)
    clue_three(world, mystery)
    solve(world, child, nanny, mystery)
    complete(world, child, nanny, mystery)

    world.facts.update(child=child, nanny=nanny, mystery=mystery, params=params)
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    child = f["child"]
    mystery = f["mystery"]
    return [
        f'Write a funny short story for a young child about {child.id} riding a tram with a nanny and solving a mystery.',
        f'Tell a comedic mystery set on a tram where a nanny helps a {child.type} figure out {mystery.question.lower()}',
        f'Write a simple story that begins on a tram, includes a nanny, and ends with the mystery being solved in a silly way.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child = f["child"]
    nanny = f["nanny"]
    mystery = f["mystery"]
    return [
        QAItem(
            question=f"Who was on the tram with {child.id}?",
            answer=f"{child.id} was on the tram with {nanny.label}. {nanny.label.capitalize()} helped {child.id} think carefully about the mystery.",
        ),
        QAItem(
            question=f"What was the mystery in the story?",
            answer=f"The mystery was: {mystery.question} They followed clues instead of making wild guesses.",
        ),
        QAItem(
            question=f"How did {child.id} and {nanny.label} solve it?",
            answer=f"They solved it with {mystery.solved_with}, which led them to {mystery.reveal}.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a tram?",
            answer="A tram is a city vehicle that rides on tracks and carries people from one stop to another.",
        ),
        QAItem(
            question="What does a nanny do?",
            answer="A nanny helps look after a child, keeps them safe, and gives gentle help when something is confusing.",
        ),
        QAItem(
            question="What should you do when something seems mysterious?",
            answer="It helps to look carefully, ask good questions, and check the clues before guessing.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== story QA ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== world QA ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for e in world.entities.values():
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        lines.append(f"  {e.id:8} ({e.type:7}) meters={meters} memes={memes}")
    return "\n".join(lines)


ASP_RULES = r"""
child_mystery(M) :- mystery(M).
valid_story(M, C, N) :- child_mystery(M), child_type(C), nanny_type(N).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for mid in MYSTERIES:
        lines.append(asp.fact("mystery", mid))
    for ct in CHILD_TYPES:
        lines.append(asp.fact("child_type", ct))
    for nt in NANNY_TYPES:
        lines.append(asp.fact("nanny_type", nt))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/3."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    if py - cl:
        print("  only in python:", sorted(py - cl))
    if cl - py:
        print("  only in clingo:", sorted(cl - py))
    return 1


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
    StoryParams(mystery="jingle", name="Mia", child_type="girl", nanny_type="nanny"),
    StoryParams(mystery="tap", name="Leo", child_type="boy", nanny_type="woman"),
    StoryParams(mystery="hide", name="Nora", child_type="girl", nanny_type="man"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid_story/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (mystery, child_type, nanny_type) combos:\n")
        for combo in combos:
            print("  ", combo)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
            i += 1
            seed = base_seed + i
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

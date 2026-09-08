#!/usr/bin/env python3
"""
A small child-friendly whodunit about Nooney, a missing garden fountain button,
and the surprising clue left by someone who had to urinate.
"""

from __future__ import annotations

import argparse
import json
import os
import random
import sys
from dataclasses import dataclass, field
from typing import Optional

_storyworlds_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if not os.path.exists(os.path.join(_storyworlds_dir, "results.py")):
    _storyworlds_dir = os.path.dirname(_storyworlds_dir)
sys.path.insert(0, _storyworlds_dir)
from results import QAItem, StoryError, StorySample  # noqa: E402


SLEUTHS = ["Luna", "Milo", "Pia", "Theo", "Nia", "Owen"]
HELPERS = ["Mrs. Finch", "Uncle Sol", "Coach Reed", "Dr. Bell"]
PLACES = ["the moonlit garden", "the town library", "the little museum", "the station courtyard"]
OBJECTS = ["the brass fountain button", "the blue library key", "the silver museum bell"]
CLUES = ["a damp paw print", "a yellow rain boot mark", "a curl of blue ribbon", "a trail of tiny pebbles"]
CULPRITS = ["the garden cat", "the wind-up delivery cart", "the shy groundskeeper", "the magpie"]
SEEDS = ["a fallen leaf", "a red marble", "a paper star", "a smooth white pebble"]

@dataclass
class Person:
    name: str
    role: str
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

@dataclass
class Mystery:
    missing: str
    place: str
    clue: str
    suspect: str
    motive: str
    truth: str
    discovery: str
    result: str

@dataclass
class World:
    sleuth: Person
    helper: Person
    mystery: Mystery
    facts: dict[str, object] = field(default_factory=dict)
    lines: list[str] = field(default_factory=list)

    def say(self, text: str) -> None:
        self.lines.append(text)

    def render(self) -> str:
        return " ".join(self.lines)

@dataclass
class StoryParams:
    sleuth: str
    helper: str
    place: str
    missing: str
    seed: Optional[int] = None

def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Generate a child-friendly whodunit mystery.")
    parser.add_argument("--sleuth", choices=SLEUTHS)
    parser.add_argument("--helper", choices=HELPERS)
    parser.add_argument("--place", choices=PLACES)
    parser.add_argument("--missing", choices=OBJECTS)
    parser.add_argument("-n", type=int, default=1)
    parser.add_argument("--all", action="store_true")
    parser.add_argument("--seed", type=int)
    parser.add_argument("--trace", action="store_true")
    parser.add_argument("--qa", action="store_true")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--asp", action="store_true")
    parser.add_argument("--verify", action="store_true")
    parser.add_argument("--show-asp", action="store_true")
    return parser

def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    return StoryParams(
        sleuth=args.sleuth or rng.choice(SLEUTHS),
        helper=args.helper or rng.choice(HELPERS),
        place=args.place or rng.choice(PLACES),
        missing=args.missing or rng.choice(OBJECTS),
        seed=args.seed,
    )

def valid_combo(params: StoryParams) -> bool:
    return params.sleuth != params.helper and params.missing in OBJECTS

def make_world(params: StoryParams) -> World:
    if not valid_combo(params):
        raise StoryError("The mystery needs a different sleuth and helper, plus a known missing object.")
    rng = random.Random(params.seed)
    clue = rng.choice(CLUES)
    suspect = rng.choice(CULPRITS)
    seed = rng.choice(SEEDS)
    motive = {
        "the garden cat": "it wanted the warm fountain ledge",
        "the wind-up delivery cart": "its loose wheel kept bumping the fountain",
        "the shy groundskeeper": "they meant to polish the button before the festival",
        "the magpie": "it liked anything bright and shiny",
    }[suspect]
    truth = {
        "the garden cat": f"The cat carried the button to a sunny flowerpot after mistaking it for a toy.",
        "the wind-up delivery cart": f"The cart nudged the button loose, and its wheel rolled it beneath a crate.",
        "the shy groundskeeper": f"The groundskeeper removed the button for polishing and forgot to tell anyone.",
        "the magpie": f"The magpie tucked the button beside its nest because it glittered.",
    }[suspect]
    discovery = {
        "the garden cat": "followed whisker scratches to a flowerpot",
        "the wind-up delivery cart": "matched the wheel marks to the crate",
        "the shy groundskeeper": "noticed polishing cloth fibers on the empty hook",
        "the magpie": "followed bright flashes toward the nest",
    }[suspect]
    result = {
        "the garden cat": "the cat received a wooden toy and the button returned to the fountain",
        "the wind-up delivery cart": "the button was lifted from beneath the crate and the cart received a wheel guard",
        "the shy groundskeeper": "the button was polished, returned, and the groundskeeper promised to speak up next time",
        "the magpie": "the button was swapped for a shiny bead and safely placed back on the fountain",
    }[suspect]
    mystery = Mystery(
        missing=params.missing,
        place=params.place,
        clue=clue,
        suspect=suspect,
        motive=motive,
        truth=truth,
        discovery=discovery,
        result=result,
    )
    return World(
        sleuth=Person(params.sleuth, "young detective", {"steps": 0}, {"curiosity": 1}),
        helper=Person(params.helper, "trusted helper", {"steps": 0}, {"patience": 1}),
        mystery=mystery,
        facts={"seed": seed, "urinate_note": "Nooney had to urinate and hurried toward the hedge, where a fresh clue caught Luna's eye."},
    )

def generate_story(world: World) -> None:
    s = world.sleuth
    h = world.helper
    m = world.mystery
    world.say(f"At twilight, {s.name} visited {m.place} with {h.name}, who loved a good mystery.")
    world.say(f"Suddenly, they discovered that {m.missing} had vanished from its usual place.")
    world.say(f'"A whodunit!" whispered {s.name}. "We should inspect the scene before guessing."')
    world.say(f'"Good plan," said {h.name}. "What do you notice?"')
    world.say(f"Near the empty spot lay {m.clue}, and beside the hedge was a note from Nooney: Nooney had needed to urinate and had hurried away before seeing who passed by.")
    world.say(f"Then {s.name} found {world.facts['seed']} beside the path. The clue showed that someone had traveled toward the fountain, not away from it.")
    world.say(f"{s.name} and {h.name} made a suspect list, but they did not blame anyone without evidence.")
    world.say(f"The trail led to {m.suspect}. Its possible reason was that {m.motive}.")
    world.say(f'"Did you take it?' asked {s.name}.')
    world.say(f'"I did not mean to make trouble," replied {m.suspect}.')
    world.say(f"Carefully, {s.name} {m.discovery}. {m.truth}")
    world.say(f"{h.name} smiled. 'The mystery is solved because you followed clues instead of rumors.'")
    world.say(f"At last, {m.result}. The fountain began to sparkle again, and Luna's notebook gained its first solved case.")

def story_qa(world: World) -> list[QAItem]:
    m = world.mystery
    return [
        QAItem("Who solved the mystery?", f"{world.sleuth.name} solved it with help from {world.helper.name}."),
        QAItem("What was missing?", f"{m.missing} was missing from {m.place}."),
        QAItem("What clue did Nooney leave behind?", f"Nooney's hurried trip to urinate led the detectives to notice the area beside the hedge and the nearby {m.clue}."),
        QAItem("Who had the missing object?", f"{m.suspect} had the object, and the evidence explained how it happened."),
        QAItem("How was the mystery solved?", f"{world.sleuth.name} {m.discovery}, which revealed the truth: {m.truth}"),
        QAItem("What lesson did the detectives learn?", "They learned to follow evidence carefully instead of blaming someone without proof."),
    ]

def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem("What is a clue?", "A clue is a detail that helps someone discover what happened."),
        QAItem("What is a suspect?", "A suspect is someone who might know about a mystery, but a suspect is not proven guilty."),
        QAItem("What does it mean to urinate?", "To urinate means to let urine leave the body; people should use a toilet or another appropriate private place."),
        QAItem("Why should detectives compare clues?", "Comparing clues helps detectives make a careful, fair explanation."),
    ]

def generation_prompts(world: World) -> list[str]:
    return [
        f"Write a child-friendly whodunit in which {world.sleuth.name} solves the disappearance of {world.mystery.missing}.",
        f"Include Nooney, who needs to urinate, and make the event lead to a useful clue near {world.mystery.place}.",
        "Show a detective using evidence, dialogue, and a fair solution rather than guessing.",
    ]

def dump_trace(world: World) -> str:
    m = world.mystery
    return "\n".join([
        "--- world model state ---",
        f"sleuth={world.sleuth.name} role={world.sleuth.role}",
        f"helper={world.helper.name} role={world.helper.role}",
        f"missing={m.missing} place={m.place}",
        f"clue={m.clue} suspect={m.suspect}",
        f"truth={m.truth}",
    ])

def format_qa(sample: StorySample) -> str:
    parts = ["== prompts =="]
    parts.extend(f"{i}. {p}" for i, p in enumerate(sample.prompts, 1))
    parts.append("")
    parts.append("== story QA ==")
    for item in sample.story_qa:
        parts.extend([f"Q: {item.question}", f"A: {item.answer}"])
    parts.append("")
    parts.append("== world QA ==")
    for item in sample.world_qa:
        parts.extend([f"Q: {item.question}", f"A: {item.answer}"])
    return "\n".join(parts)

def asp_facts() -> str:
    import asp
    lines = []
    for sleuth in SLEUTHS:
        lines.append(asp.fact("sleuth", sleuth))
    for helper in HELPERS:
        lines.append(asp.fact("helper", helper))
    for place in PLACES:
        lines.append(asp.fact("place", place))
    for missing in OBJECTS:
        lines.append(asp.fact("missing", missing))
    lines.append("evidence_based.")
    return "\n".join(lines)

ASP_RULES = r"""
valid(S,H,P,M) :- sleuth(S), helper(H), place(P), missing(M), evidence_based, S != H.
#show valid/4.
"""

def asp_program(show: str = "#show valid/4.") -> str:
    return asp_facts() + "\n" + ASP_RULES + "\n" + show + "\n"

def asp_valid() -> set[tuple]:
    import asp
    model = asp.one_model(asp_program())
    return set(asp.atoms(model, "valid"))

def asp_verify() -> int:
    import asp
    expected = {
        (s, h, p, m)
        for s in SLEUTHS
        for h in HELPERS
        for p in PLACES
        for m in OBJECTS
        if s != h
    }
    actual = asp_valid()
    if expected != actual:
        print("ASP/Python mismatch.")
        print("Only in Python:", sorted(expected - actual))
        print("Only in ASP:", sorted(actual - expected))
        return 1
    for params in [
        StoryParams("Luna", "Mrs. Finch", PLACES[0], OBJECTS[0], 1),
        StoryParams("Milo", "Coach Reed", PLACES[1], OBJECTS[1], 2),
    ]:
        sample = generate(params)
        if not sample.story or not sample.story_qa:
            print("Generated-story verification failed.")
            return 1
    print(f"OK: ASP/Python parity and generated stories verified ({len(actual)} combinations).")
    return 0

def generate(params: StoryParams) -> StorySample:
    world = make_world(params)
    generate_story(world)
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

CURATED = [
    StoryParams("Luna", "Mrs. Finch", PLACES[0], OBJECTS[0], 11),
    StoryParams("Milo", "Coach Reed", PLACES[1], OBJECTS[1], 22),
    StoryParams("Pia", "Uncle Sol", PLACES[2], OBJECTS[2], 33),
]

def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp or args.asp:
        print(asp_program())
        return
    if args.verify:
        raise SystemExit(asp_verify())

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        samples = []
        for index in range(args.n):
            rng = random.Random(base_seed + index)
            params = resolve_params(args, rng)
            params.seed = base_seed + index
            samples.append(generate(params))

    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([sample.to_dict() for sample in samples], indent=2, ensure_ascii=False))
        return

    for index, sample in enumerate(samples):
        emit(
            sample,
            trace=args.trace,
            qa=args.qa,
            header=f"### mystery {index + 1}" if len(samples) > 1 else "",
        )
        if index < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")

if __name__ == "__main__":
    main()

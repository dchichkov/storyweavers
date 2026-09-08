#!/usr/bin/env python3
"""
A standalone whodunit story world about a forbidden zone, an aversion, and a
twist discovered through careful inner thought.
"""

from __future__ import annotations

# Locate the shared StoryWorld helpers from any batch depth.
from pathlib import Path as _StoryPath
import sys as _StorySys
_storyworlds_root = next(parent for parent in _StoryPath(__file__).resolve().parents
                        if (parent / 'results.py').is_file() and (parent / 'asp.py').is_file())
_StorySys.path.insert(0, str(_storyworlds_root.parent))
_StorySys.path.insert(0, str(_storyworlds_root))


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

DETECTIVES = ["Luna", "Milo", "Nia", "Theo", "Sana", "Ivo"]
HELPERS = ["Mr. Finch", "Aunt Sol", "Ravi", "Miss Bell", "Dr. Moss"]
ZONES = ["the glasshouse", "the bell tower", "the old pantry", "the blue archive"]
OBJECTS = ["the silver key", "the moonstone", "the brass compass", "the red notebook"]
AVERSIONS = ["dust", "loud bells", "dark water", "sticky webs"]
MOTIVES = ["wanted to hide a mistake", "wanted to protect a friend", "wanted to win a wager", "wanted to keep a secret"]
CLUES = ["a clean crescent in the dust", "a thread caught on a hinge", "a warm cup beside a cold window", "a muddy print facing the wrong way"]

@dataclass
class Person:
    name: str
    role: str
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

@dataclass
class World:
    detective: Person
    helper: Person
    zone: str
    aversion: str
    object_name: str
    motive: str
    clue: str
    facts: dict = field(default_factory=dict)
    lines: list[str] = field(default_factory=list)

    def say(self, text: str) -> None:
        self.lines.append(text)

    def render(self) -> str:
        return " ".join(self.lines)

@dataclass
class StoryParams:
    detective: str
    helper: str
    zone: str
    aversion: str
    object_name: str
    seed: Optional[int] = None

def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="A small zone-aversion whodunit.")
    parser.add_argument("--detective", choices=DETECTIVES)
    parser.add_argument("--helper", choices=HELPERS)
    parser.add_argument("--zone", choices=ZONES)
    parser.add_argument("--aversion", choices=AVERSIONS)
    parser.add_argument("--object", dest="object_name", choices=OBJECTS)
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

def valid_combo(params: StoryParams) -> bool:
    return params.zone in ZONES and params.aversion in AVERSIONS and params.object_name in OBJECTS

def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    params = StoryParams(
        detective=args.detective or rng.choice(DETECTIVES),
        helper=args.helper or rng.choice(HELPERS),
        zone=args.zone or rng.choice(ZONES),
        aversion=args.aversion or rng.choice(AVERSIONS),
        object_name=args.object_name or rng.choice(OBJECTS),
        seed=args.seed,
    )
    if not valid_combo(params):
        raise StoryError("The requested zone, aversion, or object is not in the registry.")
    return params

def make_world(params: StoryParams) -> World:
    rng = random.Random(params.seed)
    detective = Person(params.detective, "detective", {"steps": 0.0}, {"curiosity": 1.0, "worry": 1.0})
    helper = Person(params.helper, "helper")
    return World(
        detective=detective,
        helper=helper,
        zone=params.zone,
        aversion=params.aversion,
        object_name=params.object_name,
        motive=rng.choice(MOTIVES),
        clue=rng.choice(CLUES),
        facts={"suspect": rng.choice(["the caretaker", "the gardener", "the curator", "the night watch"])}
    )

def generate_story(world: World) -> None:
    d, h = world.detective, world.helper
    suspect = world.facts["suspect"]
    world.say(f"At dusk, {d.name} was asked to investigate a mystery in {world.zone}.")
    world.say(f"{world.object_name} had vanished, and the only doorway led through a place that filled {d.name} with an aversion to {world.aversion}.")
    world.say(f'"You do not have to enter alone," said {h.name}. "Tell me what you notice."')
    world.say(f'"I notice that I want to run away," {d.name} answered. Inside, {d.name} thought, "If I let my aversion choose for me, the real clue may disappear."')
    d.memes["worry"] -= 0.5
    d.meters["steps"] += 1
    world.say(f"{d.name} entered {world.zone} slowly and found {world.clue}.")
    world.say(f'"The clue points toward {suspect}," whispered {d.name}. {h.name} shook their head. "Or it points toward someone who wants us to think that."')
    world.say(f"That warning revealed the twist: the apparent clue had been planted by {suspect}, but {suspect} was not the thief. The real thief had moved {world.object_name} to protect a friend.")
    world.say(f"{d.name} followed the cleanest trail, questioned the witnesses, and discovered that the missing object had been tucked beneath a harmless cloth in the same {world.zone}.")
    world.say(f"The culprit confessed that they {world.motive}. The object was returned, and the false clue was set aside.")
    world.say(f"Before leaving, {h.name} said, " + '"Courage is not loving every place. It is choosing carefully even when a place feels difficult."')
    world.say(f"{d.name} looked back at {world.zone}. The door still seemed unpleasant, but the mystery was solved because the aversion had been noticed, not obeyed.")

def story_qa(world: World) -> list[QAItem]:
    suspect = world.facts["suspect"]
    return [
        QAItem("Who solved the mystery?", f"{world.detective.name} solved the mystery by entering {world.zone} carefully and following the evidence."),
        QAItem("What was missing?", f"{world.object_name} was missing from {world.zone}."),
        QAItem("What aversion did the detective face?", f"{world.detective.name} felt an aversion to {world.aversion}, but continued with help."),
        QAItem("What was the twist?", f"The apparent clue seemed to blame {suspect}, but it had been planted; the real thief moved the object to protect a friend."),
        QAItem("How did inner thought help?", f"{world.detective.name} realized that letting an aversion choose would hide the real clue, so the detective paused and investigated."),
    ]

def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem("What is an aversion?", "An aversion is a strong feeling of dislike or discomfort toward something."),
        QAItem("What is a clue?", "A clue is a piece of information that helps someone solve a mystery."),
        QAItem("What is a twist?", "A twist is a surprising change in what the audience thought was true."),
        QAItem("What is a zone?", "A zone is a particular area or region with its own boundaries or purpose."),
    ]

def generation_prompts(world: World) -> list[str]:
    return [
        f"Write a child-friendly whodunit in {world.zone} where {world.detective.name} faces an aversion to {world.aversion}.",
        f"Include a spoken exchange with {world.helper.name}, an inner monologue, and a twist about {world.object_name}.",
    ]

def dump_trace(world: World) -> str:
    return "\n".join([
        "--- world model state ---",
        f"detective={world.detective.name} meters={world.detective.meters} memes={world.detective.memes}",
        f"helper={world.helper.name}",
        f"zone={world.zone} aversion={world.aversion}",
        f"object={world.object_name} planted_clue={world.clue}",
        f"apparent_suspect={world.facts['suspect']}",
    ])

def format_qa(sample: StorySample) -> str:
    parts = ["== prompts =="]
    parts.extend(f"{i}. {p}" for i, p in enumerate(sample.prompts, 1))
    parts.append("\n== story QA ==")
    for item in sample.story_qa:
        parts.extend([f"Q: {item.question}", f"A: {item.answer}"])
    parts.append("\n== world QA ==")
    for item in sample.world_qa:
        parts.extend([f"Q: {item.question}", f"A: {item.answer}"])
    return "\n".join(parts)

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

def emit(sample: StorySample, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world:
        print(dump_trace(sample.world))
    if qa:
        print(format_qa(sample))

def asp_facts() -> str:
    import asp
    lines = []
    for zone in ZONES:
        lines.append(asp.fact("zone", zone))
    for aversion in AVERSIONS:
        lines.append(asp.fact("aversion", aversion))
    for obj in OBJECTS:
        lines.append(asp.fact("object", obj))
    return "\n".join(lines)

ASP_RULES = r"""
valid(Z,A,O) :- zone(Z), aversion(A), object(O).
#show valid/3.
"""

def asp_program() -> str:
    return asp_facts() + "\n" + ASP_RULES

def asp_verify() -> int:
    import asp
    expected = {(z, a, o) for z in ZONES for a in AVERSIONS for o in OBJECTS}
    model = asp.one_model(asp_program())
    actual = set(asp.atoms(model, "valid"))
    if actual != expected:
        print("ASP/Python mismatch.")
        return 1
    for params in [StoryParams("Luna", "Mr. Finch", ZONES[0], AVERSIONS[0], OBJECTS[0], 4)]:
        sample = generate(params)
        if not sample.story or len(sample.story_qa) < 3:
            print("Generated-story verification failed.")
            return 1
    print(f"OK: ASP/Python parity verified for {len(actual)} combinations.")
    return 0

CURATED = [
    StoryParams("Luna", "Mr. Finch", "the glasshouse", "dust", "the silver key", 11),
    StoryParams("Milo", "Aunt Sol", "the bell tower", "loud bells", "the moonstone", 22),
    StoryParams("Nia", "Ravi", "the blue archive", "sticky webs", "the red notebook", 33),
]

def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp or args.asp:
        print(asp_program())
        return
    if args.verify:
        raise SystemExit(asp_verify())

    seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        for index in range(args.n):
            rng = random.Random(seed + index)
            params = resolve_params(args, rng)
            params.seed = seed + index
            samples.append(generate(params))

    if args.json:
        payload = samples[0].to_json() if len(samples) == 1 else json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False)
        print(payload)
        return

    for index, sample in enumerate(samples):
        emit(sample, trace=args.trace, qa=args.qa, header=f"### variant {index + 1}" if len(samples) > 1 else "")
        if index + 1 < len(samples):
            print("\n" + "=" * 70 + "\n")

if __name__ == "__main__":
    main()

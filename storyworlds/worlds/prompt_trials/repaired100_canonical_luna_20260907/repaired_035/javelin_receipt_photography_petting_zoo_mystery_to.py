#!/usr/bin/env python3
"""
A gentle petting-zoo ghost mystery about a javelin, a receipt, and photography.
"""

from __future__ import annotations

import argparse
import json
import os
import random
import sys
from dataclasses import dataclass, field
from typing import Optional

_here = os.path.dirname(os.path.abspath(__file__))
_storyworlds = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(_here))))
if not os.path.exists(os.path.join(_storyworlds, "results.py")):
    _storyworlds = os.path.dirname(os.path.dirname(_here))
sys.path.insert(0, _storyworlds)
from results import QAItem, StoryError, StorySample  # noqa: E402


@dataclass(frozen=True)
class EntitySpec:
    id: str
    label: str
    kind: str
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)


@dataclass(frozen=True)
class Case:
    id: str
    clue: str
    wrong_guess: str
    truth: str
    teamwork: str
    lesson: str
    ending: str


@dataclass
class StoryParams:
    setting: str
    object_focus: str
    evidence: str
    name: str
    teammate: str
    seed: Optional[int] = None


@dataclass
class Entity:
    id: str
    label: str
    kind: str
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)


@dataclass
class World:
    setting: str
    entities: dict[str, Entity] = field(default_factory=dict)
    facts: dict[str, object] = field(default_factory=dict)
    events: list[str] = field(default_factory=list)

    def add(self, entity: Entity) -> Entity:
        self.entities[entity.id] = entity
        return entity

    def event(self, text: str) -> None:
        self.events.append(text)


SETTINGS = {
    "petting_zoo": "the petting zoo",
}

OBJECTS = {
    "javelin": EntitySpec(
        "javelin",
        "a small practice javelin",
        "object",
        {"visible": 1.0, "safe": 0.0},
        {"mystery": 1.0},
    ),
    "receipt": EntitySpec(
        "receipt",
        "a crumpled receipt",
        "evidence",
        {"visible": 1.0, "dry": 1.0},
        {"clue": 1.0},
    ),
}

EVIDENCE = {
    "photography": EntitySpec(
        "photography",
        "photography",
        "activity",
        {"light": 1.0},
        {"curiosity": 1.0},
    ),
}

NAMES = ["Luna", "Milo", "Nia", "Theo", "Pip", "Rosa"]
TEAMMATES = ["Sam", "Ivy", "Noah", "Mae", "Owen", "Zoe"]

CASES = {
    "moonlight": Case(
        "moonlight",
        "a pale flash in a photograph beside the goat pen",
        "that a ghost had carried the javelin away",
        "the javelin had been placed behind the hay cart while a keeper repaired a loose fence board",
        "followed the receipt's time stamp, checked the photographs, and asked the keeper instead of chasing a frightening guess",
        "Good detectives let evidence guide them, even when a shadow looks like a ghost.",
        "The last photograph showed the javelin safely beside the hay cart, while a goat blinked at the moon.",
    ),
    "blue_stamp": Case(
        "blue_stamp",
        "a blue shape reflected in a photograph of the lamb shelter",
        "that a ghost had stamped the receipt and stolen the javelin",
        "a blue rain cover had slipped over the javelin when a sudden shower sent everyone indoors",
        "compared the receipt's ink mark with the shelter's blue gate and found the covered javelin",
        "Teamwork turns a spooky guess into a careful answer.",
        "In the final photograph, the blue cover rested on a bench and the lambs slept without a sound.",
    ),
    "hoofprint": Case(
        "hoofprint",
        "a tiny hoofprint crossing the receipt in a close-up photograph",
        "that an invisible visitor had taken the javelin to the pony yard",
        "a curious goat had nudged the receipt beneath a crate, while the javelin leaned against the feed shed",
        "used photography to enlarge the hoofprint, then searched together from the crate to the shed",
        "A strange clue deserves patience before it deserves fear.",
        "The final picture caught the goat beside the crate, chewing a harmless paper corner.",
    ),
    "fence_light": Case(
        "fence_light",
        "a bright line hovering above the fence in a sunset photograph",
        "that a ghost was carrying the javelin through the air",
        "sunlight had flashed from the javelin's metal tip after it was set down for safety",
        "held the receipt flat, photographed the fence from two angles, and found the ordinary reflection",
        "When friends test a clue together, shadows become easier to understand.",
        "The sunset made one last golden line on the javelin while the rabbits rustled nearby.",
    ),
}

ASP_RULES = r"""
valid_setting(S) :- setting(S).
valid_object(O) :- object(O).
valid_evidence(E) :- evidence(E).
compatible(S,O,E) :- valid_setting(S), valid_object(O), valid_evidence(E).
"""


def valid_combos() -> list[tuple[str, str, str]]:
    return [
        (setting, obj, evidence)
        for setting in SETTINGS
        for obj in OBJECTS
        for evidence in EVIDENCE
    ]


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    setting = args.setting or rng.choice(list(SETTINGS))
    object_focus = args.object_focus or rng.choice(list(OBJECTS))
    evidence = args.evidence or rng.choice(list(EVIDENCE))
    if setting not in SETTINGS:
        raise StoryError(f"Unknown setting: {setting}")
    if object_focus not in OBJECTS:
        raise StoryError(f"Unknown object focus: {object_focus}")
    if evidence not in EVIDENCE:
        raise StoryError(f"Unknown evidence: {evidence}")
    name = args.name or rng.choice(NAMES)
    teammate = args.teammate or rng.choice(TEAMMATES)
    if name == teammate:
        raise StoryError("The investigator and teammate must have different names.")
    return StoryParams(setting, object_focus, evidence, name, teammate)


def build_world(params: StoryParams) -> World:
    world = World(SETTINGS[params.setting])
    for spec in list(OBJECTS.values()) + list(EVIDENCE.values()):
        world.add(Entity(spec.id, spec.label, spec.kind, dict(spec.meters), dict(spec.memes)))
    luna = world.add(Entity("investigator", params.name, "character", memes={"curiosity": 1.0}))
    teammate = world.add(Entity("teammate", params.teammate, "character", memes={"teamwork": 1.0}))
    world.facts.update(
        investigator=luna,
        teammate=teammate,
        object_focus=params.object_focus,
        evidence=params.evidence,
    )
    return world


def _rng(params: StoryParams) -> random.Random:
    seed = params.seed if params.seed is not None else sum(ord(c) for c in repr(params))
    return random.Random(seed ^ 0xA17E)


def _choose(rng: random.Random, items: list[str]) -> str:
    return rng.choice(items)


def generate(params: StoryParams) -> StorySample:
    if params.setting not in SETTINGS:
        raise StoryError(f"Unknown setting: {params.setting}")
    if params.object_focus not in OBJECTS:
        raise StoryError(f"Unknown object focus: {params.object_focus}")
    if params.evidence not in EVIDENCE:
        raise StoryError(f"Unknown evidence: {params.evidence}")

    world = build_world(params)
    rng = _rng(params)
    case = rng.choice(list(CASES.values()))
    investigator = world.entities["investigator"]
    teammate = world.entities["teammate"]
    javelin = world.entities["javelin"]
    receipt = world.entities["receipt"]
    photography = world.entities["photography"]

    world.event("mystery noticed")
    opening = _choose(rng, [
        f"At the petting zoo, {params.name} was taking photographs when a pale blur appeared beside the goat pen.",
        f"The petting zoo was quiet at dusk, and {params.name} used photography to capture the sleepy animals.",
        f"{params.name} loved photography, especially when the petting zoo grew silver under the evening sky.",
    ])
    clue = (
        f"In one picture, {case.clue}. "
        f"On the ground nearby lay {receipt.label}, and a small practice javelin was gone from its rack."
    )
    investigator.memes["worry"] = 1.0
    javelin.meters["missing"] = 1.0
    receipt.memes["clue"] = 2.0
    world.event("receipt found")

    dialogue = _choose(rng, [
        f'"A ghost took the javelin," whispered {params.name}. "{params.teammate}, look at this receipt."',
        f'"The photograph looks spooky," said {params.name}. {params.teammate} replied, "Then let us check every clue before we decide."',
        f'"Should we run?" asked {params.name}. "Not yet," said {params.teammate}. "The receipt may tell us where to look."',
    ])
    wrong = f"{params.name} wondered {case.wrong_guess}, but {params.teammate} pointed to the receipt and the photographs."
    team = (
        f"Together they {case.teamwork}. "
        f'"The picture shows what happened, but not always why," said {params.teammate}. '
        f'"Then we ask someone who knows," answered {params.name}.'
    )
    world.event("teamwork applied")
    investigator.memes["worry"] = 0.0
    investigator.memes["relief"] = 1.0
    teammate.memes["teamwork"] = 2.0
    javelin.meters["missing"] = 0.0
    javelin.meters["safe"] = 1.0
    world.event("mystery solved")
    resolution = f"The keeper explained that {case.truth}. {case.lesson}"
    ending = case.ending
    story = " ".join([opening, clue, dialogue, wrong, team, resolution, ending])

    prompts = [
        "Write a gentle Ghost Story set in a petting zoo with a javelin, a receipt, and photography.",
        "Tell a Mystery to Solve where teamwork replaces a frightening guess with evidence.",
        f"Write a child-friendly story about {params.name} learning a Lesson Learned through careful photography.",
    ]
    story_qa = [
        QAItem("Where did the mystery happen?", "The mystery happened at the petting zoo."),
        QAItem(
            "What objects became important clues?",
            "A small practice javelin, a crumpled receipt, and photographs became important clues.",
        ),
        QAItem(
            "How did the team solve the mystery?",
            f"{params.name} and {params.teammate} studied the receipt and photographs, then {case.teamwork}.",
        ),
        QAItem(
            "What was the ghostly-looking sight really connected to?",
            f"It was connected to the truth that {case.truth}.",
        ),
        QAItem("What lesson was learned?", f"The lesson was that {case.lesson}"),
    ]
    world_qa = [
        QAItem(
            "Why can a photograph be useful in a mystery?",
            "A photograph can preserve a detail that people missed and give investigators something concrete to examine.",
        ),
        QAItem(
            "Why should teammates compare clues?",
            "Teammates can notice different details and test a frightening idea before accepting it.",
        ),
        QAItem(
            "What is a receipt?",
            "A receipt is a paper record showing what was bought, when it was bought, or where a transaction happened.",
        ),
        QAItem(
            "What makes a ghost story gentle for young readers?",
            "A gentle ghost story may feel mysterious, but its tension resolves safely through care, evidence, and friendship.",
        ),
    ]
    return StorySample(
        params=params,
        story=story,
        prompts=prompts,
        story_qa=story_qa,
        world_qa=world_qa,
        world=world,
    )


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for entity in world.entities.values():
        meters = {k: v for k, v in entity.meters.items() if v}
        memes = {k: v for k, v in entity.memes.items() if v}
        lines.append(f"{entity.id}: meters={meters} memes={memes}")
    lines.append(f"events={world.events}")
    return "\n".join(lines)


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    lines.extend(f"{i}. {p}" for i, p in enumerate(sample.prompts, 1))
    lines.append("")
    lines.append("== story qa ==")
    for item in sample.story_qa:
        lines.extend([f"Q: {item.question}", f"A: {item.answer}"])
    lines.append("")
    lines.append("== world qa ==")
    for item in sample.world_qa:
        lines.extend([f"Q: {item.question}", f"A: {item.answer}"])
    return "\n".join(lines)


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world:
        print(dump_trace(sample.world))
    if qa:
        print()
        print(format_qa(sample))


def asp_facts() -> str:
    from storyworlds import asp
    lines = []
    for setting in SETTINGS:
        lines.append(asp.fact("setting", setting))
    for obj in OBJECTS:
        lines.append(asp.fact("object", obj))
    for evidence in EVIDENCE:
        lines.append(asp.fact("evidence", evidence))
    return "\n".join(lines)


def asp_program(show: str = "#show compatible/3.") -> str:
    return asp_facts() + "\n" + ASP_RULES + "\n" + show + "\n"


def asp_valid_combos() -> list[tuple]:
    from storyworlds import asp
    model = asp.one_model(asp_program())
    return sorted(set(asp.atoms(model, "compatible")))


def asp_verify() -> int:
    try:
        py = set(valid_combos())
        clingo = set(asp_valid_combos())
    except Exception as exc:
        print(f"ASP verification unavailable: {exc}")
        return 1
    if py != clingo:
        print("ASP/Python mismatch")
        print("python only:", sorted(py - clingo))
        print("ASP only:", sorted(clingo - py))
        return 1
    for index, combo in enumerate(sorted(py)[:3]):
        params = StoryParams(*combo, name="Luna", teammate="Sam", seed=index)
        sample = generate(params)
        if not sample.story or "petting zoo" not in sample.story:
            print("Generated-story verification failed")
            return 1
    print(f"OK: ASP matches Python ({len(py)} combinations), and generated stories passed.")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="A gentle petting-zoo ghost mystery.")
    parser.add_argument("--setting", choices=SETTINGS)
    parser.add_argument("--object-focus", choices=OBJECTS)
    parser.add_argument("--evidence", choices=EVIDENCE)
    parser.add_argument("--name")
    parser.add_argument("--teammate")
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


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program())
        return
    if args.verify:
        raise SystemExit(asp_verify())
    if args.asp:
        for combo in asp_valid_combos():
            print(combo)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        for setting, obj, evidence in valid_combos():
            params = StoryParams(setting, obj, evidence, "Luna", "Sam", base_seed)
            samples.append(generate(params))
    else:
        seen = set()
        for index in range(max(args.n, 0)):
            seed = base_seed + index
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
            print(json.dumps([sample.to_dict() for sample in samples], indent=2, ensure_ascii=False))
        return

    for index, sample in enumerate(samples):
        emit(
            sample,
            trace=args.trace,
            qa=args.qa,
            header=f"### variant {index + 1}" if len(samples) > 1 else "",
        )
        if index + 1 < len(samples):
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()

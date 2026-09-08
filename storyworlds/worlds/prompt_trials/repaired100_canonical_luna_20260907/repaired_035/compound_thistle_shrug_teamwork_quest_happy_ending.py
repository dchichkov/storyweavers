#!/usr/bin/env python3
"""
A small detective-story world about a compound, a prickly thistle, and a
teamwork quest with a happy ending.
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


@dataclass(frozen=True)
class Place:
    id: str
    label: str
    feature: str


@dataclass(frozen=True)
class Clue:
    id: str
    label: str
    detail: str


@dataclass(frozen=True)
class Tool:
    id: str
    label: str
    use: str


PLACES = {
    "garden_compound": Place(
        "garden_compound",
        "the garden compound",
        "a square courtyard enclosed by a low wooden fence",
    ),
    "old_compound": Place(
        "old_compound",
        "the old compound",
        "a quiet yard with a gate, a shed, and a stone path",
    ),
    "school_compound": Place(
        "school_compound",
        "the school compound",
        "a sunny courtyard behind the little school",
    ),
}

CLUES = {
    "yellow_petal": Clue(
        "yellow_petal",
        "a yellow petal",
        "a yellow petal caught on the latch",
    ),
    "twine": Clue(
        "twine",
        "a loop of twine",
        "a loop of twine trailing from the herb bed",
    ),
    "muddy_arrow": Clue(
        "muddy_arrow",
        "a muddy arrow",
        "a small muddy arrow pointing toward the tool shed",
    ),
}

TOOLS = {
    "basket": Tool(
        "basket",
        "a wide basket",
        "hold the thistle safely",
    ),
    "gloves": Tool(
        "gloves",
        "thick garden gloves",
        "grip the prickly stem without getting poked",
    ),
    "rake": Tool(
        "rake",
        "a small rake",
        "clear the path around the thistle",
    ),
}

NAMES = ["Luna", "Milo", "Ivy", "Theo", "Nia", "Owen"]
HELPERS = ["Pip", "Zara", "Ben", "Mara", "Sam", "June"]

GENDERS = {
    "Luna": "girl",
    "Ivy": "girl",
    "Nia": "girl",
    "Zara": "girl",
    "Mara": "girl",
    "June": "girl",
    "Milo": "boy",
    "Theo": "boy",
    "Owen": "boy",
    "Ben": "boy",
    "Sam": "child",
    "Pip": "child",
}


@dataclass
class Entity:
    id: str
    kind: str
    label: str
    type: str = "thing"
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)


@dataclass
class World:
    place: Place
    entities: dict[str, Entity] = field(default_factory=dict)
    facts: dict[str, object] = field(default_factory=dict)
    trace: list[str] = field(default_factory=list)

    def add(self, entity: Entity) -> Entity:
        self.entities[entity.id] = entity
        return entity

    def note(self, text: str) -> None:
        self.trace.append(text)


@dataclass
class StoryParams:
    place: str
    name: str
    helper: str
    clue: str
    tool: str
    seed: Optional[int] = None


def valid_combos() -> list[tuple[str, str, str, str]]:
    return [
        (place, clue, tool, "quest")
        for place in PLACES
        for clue in CLUES
        for tool in TOOLS
    ]


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    place = args.place or rng.choice(list(PLACES))
    clue = args.clue or rng.choice(list(CLUES))
    tool = args.tool or rng.choice(list(TOOLS))
    if place not in PLACES:
        raise StoryError(f"Unknown place: {place}")
    if clue not in CLUES:
        raise StoryError(f"Unknown clue: {clue}")
    if tool not in TOOLS:
        raise StoryError(f"Unknown tool: {tool}")
    name = args.name or rng.choice(NAMES)
    helper = args.helper or rng.choice(HELPERS)
    if name == helper:
        raise StoryError("The detective and helper must have different names.")
    return StoryParams(place, name, helper, clue, tool, args.seed)


def build_world(params: StoryParams) -> World:
    place = PLACES[params.place]
    world = World(place)
    detective = world.add(
        Entity(
            "detective",
            "character",
            params.name,
            GENDERS.get(params.name, "child"),
            memes={"curiosity": 1.0, "courage": 1.0},
        )
    )
    helper = world.add(
        Entity(
            "helper",
            "character",
            params.helper,
            GENDERS.get(params.helper, "child"),
            memes={"teamwork": 0.0},
        )
    )
    world.add(
        Entity(
            "thistle",
            "plant",
            "the thistle",
            "thistle",
            meters={"prickly": 1.0, "blocking_path": 1.0},
        )
    )
    world.add(Entity("gate", "object", "the compound gate", "gate"))
    world.facts.update(
        {
            "detective": detective,
            "helper": helper,
            "clue": CLUES[params.clue],
            "tool": TOOLS[params.tool],
            "quest": "move the thistle away from the narrow path",
            "compound": place.label,
        }
    )
    return world


def pronoun(entity: Entity, case: str = "subject") -> str:
    if entity.type == "girl":
        return {"subject": "she", "object": "her", "possessive": "her"}[case]
    if entity.type == "boy":
        return {"subject": "he", "object": "him", "possessive": "his"}[case]
    return {"subject": "they", "object": "them", "possessive": "their"}[case]


def generate(params: StoryParams) -> StorySample:
    if params.place not in PLACES:
        raise StoryError(f"Unknown place: {params.place}")
    if params.clue not in CLUES:
        raise StoryError(f"Unknown clue: {params.clue}")
    if params.tool not in TOOLS:
        raise StoryError(f"Unknown tool: {params.tool}")

    world = build_world(params)
    detective = world.entities["detective"]
    helper = world.entities["helper"]
    thistle = world.entities["thistle"]
    clue = CLUES[params.clue]
    tool = TOOLS[params.tool]

    rng = random.Random(params.seed if params.seed is not None else 17)

    opening = rng.choice(
        [
            f"On a bright morning, {detective.label} entered {world.place.label}, "
            f"{world.place.feature}.",
            f"{world.place.label} was peaceful that morning, and {detective.label} "
            f"was ready for a careful detective quest.",
            f"{detective.label} loved solving small mysteries, so {detective.label} "
            f"was pleased to explore {world.place.label}.",
        ]
    )
    discovery = (
        f"Near the gate, {detective.label} noticed a thorny thistle leaning across "
        f"the walking path. The prickly plant made the path hard to use."
    )
    clue_sentence = (
        f"A real detective looked for evidence. Soon {clue.detail} appeared beside "
        f"the thistle."
    )
    suspicion = (
        f"At first, {detective.label} gave a little shrug and wondered if someone "
        f"had left the thistle there by mistake."
    )
    dialogue_one = (
        f"\"I can pull it away,\" said {detective.label}. "
        f"\"Wait,\" replied {helper.label}. \"The thistle may shelter a tiny insect.\""
    )
    explanation = (
        f"{helper.label} pointed to a small green caterpillar resting beneath the "
        f"leaves. The clue showed that the quest was not to destroy the thistle, "
        f"but to move it carefully."
    )
    dialogue_two = (
        f"\"Then we need teamwork,\" said {detective.label}. "
        f"\"You hold the {tool.label}, and I will guide the stems,\" said {helper.label}."
    )

    tool_action = tool.use
    work = (
        f"Together they used {tool.label} to {tool_action}. "
        f"{detective.label} steadied the roots while {helper.label} cleared a safe "
        f"new place beside the fence."
    )
    thistle["meters"] if False else None
    thistle.meters["blocking_path"] = 0.0
    thistle.meters["safe_place"] = 1.0
    thistle.meters["protected"] = 1.0
    helper.memes["teamwork"] = 1.0
    detective.memes["relief"] = 1.0
    world.note("The clue revealed that the thistle sheltered a caterpillar.")
    world.note("The children moved the thistle instead of harming it.")
    world.note("The path became clear while the thistle remained protected.")

    ending = (
        f"The path through the compound was clear again, and the caterpillar stayed "
        f"safe among the thistle leaves. The happy ending came when {detective.label} "
        f"and {helper.label} saw the plant standing proudly beside the fence."
    )
    final_image = (
        f"A yellow butterfly soon fluttered above the thistle, while the two friends "
        f"walked through the compound together."
    )

    story = " ".join(
        [
            opening,
            discovery,
            clue_sentence,
            suspicion,
            dialogue_one,
            explanation,
            dialogue_two,
            work,
            ending,
            final_image,
        ]
    )

    prompts = [
        "Write a gentle detective story using compound, thistle, and shrug.",
        f"Tell a teamwork quest about {params.name} and {params.helper} in {world.place.label}.",
        "Write a child-friendly mystery with a happy ending.",
    ]
    story_qa = [
        QAItem(
            "Where did the detective investigate?",
            f"{detective.label} investigated the mystery in {world.place.label}.",
        ),
        QAItem(
            "What blocked the path?",
            "A prickly thistle leaned across the walking path.",
        ),
        QAItem(
            "What clue changed the detective's idea?",
            f"The clue was {clue.detail}, and it helped show that the thistle needed care.",
        ),
        QAItem(
            "How did teamwork solve the quest?",
            f"{detective.label} and {helper.label} used {tool.label} together, moved the thistle safely, and cleared the path.",
        ),
        QAItem(
            "How did the story end?",
            "The path was clear, the caterpillar was safe, and the friends enjoyed a happy ending beside the thistle.",
        ),
    ]
    world_qa = [
        QAItem(
            "What is a compound?",
            "A compound is an enclosed place made of several areas or buildings, often surrounded by a fence or wall.",
        ),
        QAItem(
            "What is a thistle?",
            "A thistle is a flowering plant with prickly leaves or stems.",
        ),
        QAItem(
            "Why is teamwork useful?",
            "Teamwork is useful because people can share jobs, notice different clues, and solve a problem more safely together.",
        ),
        QAItem(
            "What is a quest?",
            "A quest is a purposeful journey or task in which someone searches, learns, and works toward a goal.",
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
    lines.append(f"place: {world.place.label}")
    for entity in world.entities.values():
        meters = {k: v for k, v in entity.meters.items() if v}
        memes = {k: v for k, v in entity.memes.items() if v}
        lines.append(
            f"{entity.id}: meters={meters or {}} memes={memes or {}}"
        )
    lines.extend(f"event: {line}" for line in world.trace)
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


def emit(
    sample: StorySample,
    *,
    trace: bool = False,
    qa: bool = False,
    header: str = "",
) -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world is not None:
        print(dump_trace(sample.world))
    if qa:
        print()
        print(format_qa(sample))


ASP_RULES = r"""
valid(Place, Clue, Tool) :-
    place(Place),
    clue(Clue),
    tool(Tool),
    quest(quest).
"""


def asp_facts() -> str:
    import asp

    lines = []
    for place in PLACES:
        lines.append(asp.fact("place", place))
    for clue in CLUES:
        lines.append(asp.fact("clue", clue))
    for tool in TOOLS:
        lines.append(asp.fact("tool", tool))
    lines.append(asp.fact("quest", "quest"))
    return "\n".join(lines)


def asp_program(show: str = "#show valid/3.") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program())
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    python_set = {
        (place, clue, tool)
        for place, clue, tool, _ in valid_combos()
    }
    clingo_set = set(asp_valid_combos())
    if python_set != clingo_set:
        print("MISMATCH between Python and ASP compatibility sets.")
        print("Only in Python:", sorted(python_set - clingo_set))
        print("Only in ASP:", sorted(clingo_set - python_set))
        return 1
    for seed in range(3):
        params = StoryParams(
            place="garden_compound",
            name="Luna",
            helper="Pip",
            clue="yellow_petal",
            tool="basket",
            seed=seed,
        )
        sample = generate(params)
        if "happy ending" not in sample.story:
            print("Generated-story verification failed.")
            return 1
    print(f"OK: ASP matches Python ({len(python_set)} combinations).")
    print("OK: generated stories passed.")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="A detective story about a thistle, teamwork, and a happy ending."
    )
    parser.add_argument("--place", choices=PLACES)
    parser.add_argument("--name")
    parser.add_argument("--helper")
    parser.add_argument("--clue", choices=CLUES)
    parser.add_argument("--tool", choices=TOOLS)
    parser.add_argument("-n", type=int, default=1)
    parser.add_argument("--seed", type=int)
    parser.add_argument("--all", action="store_true")
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
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible combinations:")
        for combo in combos:
            print(" ", combo)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        for place, clue, tool, _ in valid_combos():
            params = StoryParams(
                place=place,
                name="Luna",
                helper="Pip",
                clue=clue,
                tool=tool,
            )
            samples.append(generate(params))
    else:
        seen: set[str] = set()
        attempts = 0
        while len(samples) < max(1, args.n) and attempts < max(50, args.n * 50):
            seed = base_seed + attempts
            attempts += 1
            params = resolve_params(args, random.Random(seed))
            params.seed = seed
            sample = generate(params)
            if sample.story not in seen:
                seen.add(sample.story)
                samples.append(sample)

    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([sample.to_dict() for sample in samples], indent=2))
        return

    for index, sample in enumerate(samples):
        emit(
            sample,
            trace=args.trace,
            qa=args.qa,
            header=f"### variant {index + 1}" if len(samples) > 1 else "",
        )
        if index < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()

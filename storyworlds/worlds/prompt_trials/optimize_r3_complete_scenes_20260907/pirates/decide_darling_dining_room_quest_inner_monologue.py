#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import random
import sys
from dataclasses import dataclass, field
from typing import Any, Optional

HERE = os.path.abspath(__file__)
for parent in [os.path.dirname(HERE), *([os.path.dirname(HERE)] * 0)]:
    pass
_probe = os.path.dirname(HERE)
while _probe and _probe != os.path.dirname(_probe):
    candidate = os.path.join(_probe, "results.py")
    if os.path.exists(candidate):
        sys.path.insert(0, _probe)
        break
    _probe = os.path.dirname(_probe)
from pathlib import Path as _StoryPath
_storyworlds_root = next(parent for parent in _StoryPath(__file__).resolve().parents
                        if (parent / 'results.py').is_file() and (parent / 'asp.py').is_file())
sys.path.insert(0, str(_storyworlds_root))
from results import QAItem, StoryError, StorySample  # noqa: E402


@dataclass
class Entity:
    id: str
    kind: str
    label: str
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)


@dataclass
class StoryParams:
    path: str
    child: str
    helper: str
    seed: Optional[int] = None


@dataclass
class World:
    params: StoryParams
    entities: dict[str, Entity] = field(default_factory=dict)
    facts: dict[str, Any] = field(default_factory=dict)
    scenes: list[str] = field(default_factory=list)

    def add(self, entity: Entity) -> Entity:
        self.entities[entity.id] = entity
        return entity

    def scene(self, text: str) -> None:
        self.scenes.append(text)

    def render(self) -> str:
        return "\n\n".join(self.scenes)


NAMES = [
    ("Mara", "Jonah"),
    ("Lena", "Owen"),
    ("Nia", "Caleb"),
    ("Ruby", "Evan"),
]
PATHS = ("lantern", "recipe", "missing_spoon")
PATH_INFO = {
    "lantern": {
        "trouble": "The dining room was dim, and the table was set for a surprise supper.",
        "learned": "A jar of fireflies on the sideboard could glow safely, but only after someone carried it carefully.",
        "decision": "They decided to ask an adult before moving the jar.",
        "resolution": "With Dad's help, they placed the glowing jar beside the plates, and the table shone with gentle green dots.",
        "object": "the jar of fireflies",
        "lesson": "ask before carrying something fragile",
    },
    "recipe": {
        "trouble": "The pancake recipe had a blank step, and the batter waited in a bowl.",
        "learned": "A floury thumbprint on the card showed that Grandma had folded the missing corner under the recipe box.",
        "decision": "They decided to look closely together instead of guessing.",
        "resolution": "They found the missing step, added the milk, and served warm pancakes in a bright stack.",
        "object": "the folded recipe card",
        "lesson": "look for clues before guessing",
    },
    "missing_spoon": {
        "trouble": "One place at the dining table had no spoon, so the birthday pudding could not be served.",
        "learned": "A faint trail of sugar led from the table toward the toy cupboard.",
        "decision": "They decided to follow the trail and listen before blaming anyone.",
        "resolution": "They found the spoon in a teddy bear's picnic tin and returned it before the pudding melted.",
        "object": "the missing spoon",
        "lesson": "follow evidence before blaming",
    },
}


def choose_path(rng: random.Random) -> str:
    return rng.choice(PATHS)


def build_world(params: StoryParams, rng: random.Random) -> World:
    data = PATH_INFO[params.path]
    world = World(params)
    child = world.add(Entity(params.child, "character", params.child,
                             memes={"curiosity": 1.0, "care": 1.0}))
    helper = world.add(Entity(params.helper, "character", params.helper,
                              memes={"patience": 1.0}))
    room = world.add(Entity("dining_room", "place", "dining room",
                            meters={"warmth": 1.0}))
    world.facts.update(child=child, helper=helper, room=room, data=data)
    openings = [
        f"In the dining room, {params.child} was getting ready for a small family surprise.",
        f"Rain tapped the windows while {params.child} and {params.helper} worked in the dining room.",
    ]
    world.scene(rng.choice(openings))
    world.scene(data["trouble"])
    world.scene(
        f'"What should we do, darling?" {params.child} asked. '
        f'"Let us search for one clue at a time," {params.helper} replied.'
    )
    world.scene(
        f"They began a little quest around the table. {data['learned']}"
    )
    child.memes["understanding"] = 1.0
    helper.memes["trust"] = 1.0
    world.scene(
        f'"Now I know what to do," {params.child} said. {data["decision"]}'
    )
    child.memes["good_judgment"] = 1.0
    world.scene(
        f"For a moment, suspense tightened the quiet room. Then {data['resolution']}"
    )
    world.facts["resolved"] = True
    world.facts["object"] = data["object"]
    world.facts["lesson"] = data["lesson"]
    return world


def prompts(world: World) -> list[str]:
    data = world.facts["data"]
    return [
        f"Write a heartwarming dining-room quest in which {world.params.child} must decide what to do about {data['object']}.",
        f"Tell a suspenseful but gentle story where {world.params.child} learns a clue from {world.params.helper} and solves a dining-room problem.",
    ]


def story_qa(world: World) -> list[QAItem]:
    p = world.params
    d = world.facts["data"]
    return [
        QAItem(
            f"What trouble did {p.child} find in the dining room?",
            d["trouble"],
        ),
        QAItem(
            f"What did {p.child} learn during the quest?",
            d["learned"],
        ),
        QAItem(
            f"What did {p.child} decide to do?",
            d["decision"],
        ),
        QAItem(
            "How was the problem resolved?",
            d["resolution"],
        ),
        QAItem(
            "What did the children learn from the quest?",
            f"They learned to {world.facts['lesson']}.",
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            "Why is it helpful to look for clues?",
            "Clues give us information, so we can make a careful choice instead of guessing.",
        ),
        QAItem(
            "Why should children ask for help with fragile or unfamiliar things?",
            "A trusted grown-up can help keep people and special objects safe.",
        ),
    ]


def generate(params: StoryParams) -> StorySample:
    rng = random.Random(params.seed)
    world = build_world(params, rng)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=prompts(world),
        story_qa=story_qa(world),
        world_qa=world_qa(world),
        world=world,
    )


ASP_RULES = r"""
trouble(lantern). trouble(recipe). trouble(missing_spoon).
valid(P) :- trouble(P).
#show valid/1.
"""


def asp_facts() -> str:
    import asp
    return "\n".join(asp.fact("trouble", path) for path in PATHS)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Dining-room decision quests.")
    parser.add_argument("--path", choices=PATHS)
    parser.add_argument("--child")
    parser.add_argument("--helper")
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


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    path = args.path or choose_path(rng)
    if path not in PATH_INFO:
        raise StoryError("The selected quest has no dining-room resolution.")
    pair = rng.choice(NAMES)
    child = args.child or pair[0]
    helper = args.helper or pair[1]
    if child == helper:
        raise StoryError("The child and helper must have different names.")
    return StoryParams(path=path, child=child, helper=helper)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for entity in world.entities.values():
        lines.append(
            f"{entity.id}: kind={entity.kind}, meters={entity.meters}, memes={entity.memes}"
        )
    lines.append(f"facts={world.facts['object']}, resolved={world.facts['resolved']}")
    return "\n".join(lines)


def format_qa(sample: StorySample) -> str:
    lines = ["== Generation prompts =="]
    lines.extend(f"{i}. {text}" for i, text in enumerate(sample.prompts, 1))
    lines.append("\n== Story questions ==")
    for item in sample.story_qa:
        lines.extend([f"Q: {item.question}", f"A: {item.answer}"])
    lines.append("\n== World knowledge ==")
    for item in sample.world_qa:
        lines.extend([f"Q: {item.question}", f"A: {item.answer}"])
    return "\n".join(lines)


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False,
         header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world:
        print(dump_trace(sample.world))
    if qa:
        print(format_qa(sample))


def asp_program() -> str:
    return asp_facts() + "\n" + ASP_RULES


def asp_check() -> int:
    import asp
    model = asp.one_model(asp_program())
    found = {item[0] for item in asp.atoms(model, "valid")}
    expected = set(PATHS)
    if found != expected:
        print(f"ASP mismatch: {sorted(found)} != {sorted(expected)}")
        return 1
    print(f"OK: ASP recognizes {len(found)} quest paths.")
    return 0


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program())
        return
    if args.verify:
        sys.exit(asp_check())
    if args.asp:
        import asp
        model = asp.one_model(asp_program())
        for path, in sorted(asp.atoms(model, "valid")):
            print(path)
        return

    base = args.seed if args.seed is not None else random.randrange(2**31)
    params_list: list[StoryParams] = []
    if args.all:
        for index, path in enumerate(PATHS):
            params_list.append(
                StoryParams(path=path, child=NAMES[index][0], helper=NAMES[index][1],
                            seed=base + index)
            )
    else:
        for index in range(args.n):
            rng = random.Random(base + index)
            params = resolve_params(args, rng)
            params.seed = base + index
            params_list.append(params)

    samples = [generate(params) for params in params_list]
    if args.json:
        payload = samples[0].to_dict() if len(samples) == 1 else [s.to_dict() for s in samples]
        print(json.dumps(payload, indent=2, ensure_ascii=False))
        return
    for index, sample in enumerate(samples):
        if len(samples) > 1:
            print(f"### quest {index + 1}\n")
        emit(sample, trace=args.trace, qa=args.qa)
        if index + 1 < len(samples):
            print("\n" + "=" * 60 + "\n")


if __name__ == "__main__":
    main()

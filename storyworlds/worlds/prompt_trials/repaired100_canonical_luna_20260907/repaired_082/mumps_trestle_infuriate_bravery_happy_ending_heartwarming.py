#!/usr/bin/env python3
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

_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if not os.path.exists(os.path.join(_root, "results.py")):
    _root = os.path.dirname(_root)
sys.path.insert(0, _root)
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
    setting: str = "hill_trestle"
    child: str = "Luna"
    helper: str = "Aunt Mara"
    seed: Optional[int] = None


@dataclass(frozen=True)
class Setting:
    id: str
    label: str
    danger: str
    safe_place: str


SETTINGS = {
    "hill_trestle": Setting(
        "hill_trestle",
        "the old wooden trestle above Fern Creek",
        "a loose plank",
        "the warm station house",
    )
}
CHILDREN = ["Luna", "Nia", "Toby", "Milo"]
HELPERS = ["Aunt Mara", "Uncle Sol", "Grandma Bea"]
ASP_RULES = r"""
valid(S) :- setting(S), has_safe_place(S), has_trestle(S).
#show valid/1.
"""


class World:
    def __init__(self, setting: Setting):
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.facts: dict[str, object] = {}
        self.events: list[str] = []

    def add(self, entity: Entity) -> Entity:
        self.entities[entity.id] = entity
        return entity


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="A heartwarming bravery story about Luna, mumps, and a trestle."
    )
    parser.add_argument("--setting", choices=SETTINGS, default=None)
    parser.add_argument("--child", default=None)
    parser.add_argument("--helper", default=None)
    parser.add_argument("-n", type=int, default=1)
    parser.add_argument("--all", action="store_true")
    parser.add_argument("--seed", type=int, default=None)
    parser.add_argument("--trace", action="store_true")
    parser.add_argument("--qa", action="store_true")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--asp", action="store_true")
    parser.add_argument("--verify", action="store_true")
    parser.add_argument("--show-asp", action="store_true")
    return parser


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    setting = args.setting or "hill_trestle"
    if setting not in SETTINGS:
        raise StoryError(f"Unknown setting: {setting}")
    child = args.child or rng.choice(CHILDREN)
    helper = args.helper or rng.choice(HELPERS)
    if child == helper:
        raise StoryError("The child and helper must be different people.")
    return StoryParams(setting=setting, child=child, helper=helper)


def build_story(params: StoryParams) -> World:
    if params.setting not in SETTINGS:
        raise StoryError(f"Unsupported setting: {params.setting}")
    setting = SETTINGS[params.setting]
    world = World(setting)
    child = world.add(Entity("child", "child", params.child))
    helper = world.add(Entity("helper", "adult", params.helper))
    trestle = world.add(Entity("trestle", "bridge", "the old wooden trestle"))
    child.meters.update({"illness": 1.0, "distance_to_help": 1.0})
    child.memes.update({"fear": 1.0, "bravery": 0.0})
    helper.memes["care"] = 1.0
    trestle.meters["loose_plank"] = 1.0

    world.events.extend(
        [
            f"{child.label} felt sick with mumps and stayed close to {setting.safe_place}.",
            f"A little cart carrying medicine stopped on the far side of {trestle.label}.",
            f"The {setting.danger} made the crossing unsafe.",
        ]
    )
    world.facts.update(child=child, helper=helper, trestle=trestle)
    return world


def render_story(world: World) -> str:
    child: Entity = world.facts["child"]
    helper: Entity = world.facts["helper"]
    trestle: Entity = world.facts["trestle"]
    setting = world.setting

    child.memes["bravery"] = 1.0
    child.memes["hope"] = 1.0
    child.meters["distance_to_help"] = 0.0
    trestle.meters["loose_plank"] = 0.0
    world.events.extend(
        [
            f"{helper.label} tied a bright scarf to the safe rail and checked every board.",
            f"{child.label} stayed still, drank water, and called kindly across the creek.",
            "The medicine reached the station house without anyone stepping on the loose plank.",
            f"{child.label} recovered while neighbors repaired the trestle together.",
        ]
    )
    return (
        f"On a bright morning, {child.label} was resting in {setting.safe_place}, "
        f"because mumps had made {child.label}'s cheeks sore and tired. "
        f"Across Fern Creek, a small cart held the medicine that would help.\n\n"
        f"The cart waited beside {trestle.label}, but {setting.danger} made the crossing dangerous. "
        f"\"I can go across,\" said {child.label}. \"No,\" said {helper.label}. "
        f"\"Being brave means choosing a safe way to help.\"\n\n"
        f"{child.label} took a slow breath. Instead of rushing, {child.label} pointed to the station bell. "
        f"\"Ring it from here,\" {child.label} said. \"Then the cart driver will know where to wait.\" "
        f"{helper.label} waved a bright scarf, and a neighbor hurried to meet the cart at the safe end.\n\n"
        f"The medicine arrived without a risky step. {child.label} rested, drank water, and let "
        f"{helper.label} care for {child.label}. Soon the fever faded. Neighbors repaired "
        f"{trestle.label} with strong boards, and the first safe crossing ended in cheers. "
        f"{child.label} smiled from the station porch, proud that bravery had protected everyone. "
        f"The happy ending was warm as a shared blanket: the bridge was safe, the medicine was near, "
        f"and every caring heart had helped."
    )


def generation_prompts(world: World) -> list[str]:
    child: Entity = world.facts["child"]
    return [
        f"Write a heartwarming story about {child.label}, mumps, and a trestle.",
        "Show bravery as choosing a safe plan instead of taking a dangerous shortcut.",
        "End with neighbors helping one another and a clear happy ending.",
    ]


def story_qa(world: World) -> list[QAItem]:
    child: Entity = world.facts["child"]
    helper: Entity = world.facts["helper"]
    return [
        QAItem(
            f"Why was {child.label} resting in the station house?",
            f"{child.label} was resting because mumps had made {child.label}'s cheeks sore and tired.",
        ),
        QAItem(
            f"What danger did {helper.label} notice?",
            f"{helper.label} noticed that a loose plank made the trestle unsafe to cross.",
        ),
        QAItem(
            f"How did {child.label} show bravery?",
            f"{child.label} showed bravery by choosing a safe plan and ringing the station bell instead of rushing across the trestle.",
        ),
        QAItem(
            "How did the story end happily?",
            "The medicine arrived safely, the child recovered, and neighbors repaired the trestle together.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            "What is a trestle?",
            "A trestle is a supporting bridge or framework, often made from beams, that carries a path or track over a gap.",
        ),
        QAItem(
            "Why should someone with mumps rest and receive care?",
            "Someone with mumps should rest and receive advice from a trusted adult or health professional because the illness can cause painful swelling and tiredness.",
        ),
        QAItem(
            "What is bravery?",
            "Bravery is doing what is right or helpful while still paying attention to danger and making a careful choice.",
        ),
    ]


def generate(params: StoryParams) -> StorySample:
    world = build_story(params)
    story = render_story(world)
    return StorySample(
        params=params,
        story=story,
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts =="]
    lines.extend(f"{i}. {prompt}" for i, prompt in enumerate(sample.prompts, 1))
    lines.append("")
    lines.append("== (2) Story questions ==")
    for item in sample.story_qa:
        lines.extend([f"Q: {item.question}", f"A: {item.answer}"])
    lines.append("")
    lines.append("== (3) World-knowledge questions ==")
    for item in sample.world_qa:
        lines.extend([f"Q: {item.question}", f"A: {item.answer}"])
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for entity in world.entities.values():
        meters = {k: v for k, v in entity.meters.items() if v}
        memes = {k: v for k, v in entity.memes.items() if v}
        lines.append(
            f"  {entity.label}: kind={entity.kind}, meters={meters}, memes={memes}"
        )
    lines.append(f"  events={len(world.events)}")
    return "\n".join(lines)


def asp_facts() -> str:
    import asp

    setting = SETTINGS["hill_trestle"]
    return "\n".join(
        [
            asp.fact("setting", setting.id),
            asp.fact("has_safe_place", setting.id),
            asp.fact("has_trestle", setting.id),
        ]
    )


def asp_program() -> str:
    return f"{asp_facts()}\n{ASP_RULES}"


def asp_valid() -> set[tuple]:
    import asp

    model = asp.one_model(asp_program())
    return set(asp.atoms(model, "valid"))


def valid_combos() -> list[tuple[str]]:
    return [("hill_trestle",)]


def asp_verify() -> int:
    expected = set(valid_combos())
    actual = asp_valid()
    if expected != actual:
        print("MISMATCH:")
        print("python only:", sorted(expected - actual))
        print("clingo only:", sorted(actual - expected))
        return 1
    for params in [
        StoryParams("hill_trestle", "Luna", "Aunt Mara", 1),
        StoryParams("hill_trestle", "Nia", "Uncle Sol", 2),
    ]:
        sample = generate(params)
        if not sample.story or "mumps" not in sample.story or "trestle" not in sample.story:
            print("Generated-story verification failed.")
            return 1
    print("OK: ASP/Python parity and generated stories verified.")
    return 0


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


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program())
        return
    if args.verify:
        raise SystemExit(asp_verify())
    if args.asp:
        rows = sorted(asp_valid())
        print(f"{len(rows)} compatible setting(s):")
        for row in rows:
            print(" ", row)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        curated = [
            StoryParams("hill_trestle", "Luna", "Aunt Mara", base_seed),
            StoryParams("hill_trestle", "Nia", "Uncle Sol", base_seed + 1),
            StoryParams("hill_trestle", "Milo", "Grandma Bea", base_seed + 2),
        ]
        samples = [generate(params) for params in curated]
    else:
        seen: set[str] = set()
        for offset in range(max(args.n * 20, 20)):
            if len(samples) >= args.n:
                break
            seed = base_seed + offset
            rng = random.Random(seed)
            params = resolve_params(args, rng)
            params.seed = seed
            sample = generate(params)
            if sample.story not in seen:
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
        if index < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()

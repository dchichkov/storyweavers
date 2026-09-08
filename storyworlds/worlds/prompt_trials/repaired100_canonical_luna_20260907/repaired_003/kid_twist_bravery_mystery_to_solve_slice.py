#!/usr/bin/env python3
"""
A small slice-of-life storyworld about a kid, a brave question, and a mystery
hidden in an ordinary afternoon.
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


@dataclass
class StoryParams:
    setting: str
    seed: Optional[int] = None
    kid_name: str = "Luna"
    helper_name: str = "Milo"
    object_name: str = "red mitten"


@dataclass
class Entity:
    id: str
    kind: str
    label: str
    type: str
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def inc_meter(self, key: str, amount: float = 1.0) -> None:
        self.meters[key] = self.meters.get(key, 0.0) + amount

    def inc_meme(self, key: str, amount: float = 1.0) -> None:
        self.memes[key] = self.memes.get(key, 0.0) + amount


@dataclass
class World:
    setting: str
    kid: Entity
    helper: Entity
    mystery: Entity
    places: list[str]
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    facts: dict = field(default_factory=dict)

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)

    def trace(self) -> str:
        lines = ["--- world model state ---"]
        for entity in [self.kid, self.helper, self.mystery]:
            meters = {k: v for k, v in entity.meters.items() if v}
            memes = {k: v for k, v in entity.memes.items() if v}
            bits = []
            if meters:
                bits.append(f"meters={meters}")
            if memes:
                bits.append(f"memes={memes}")
            lines.append(f"  {entity.id:12} ({entity.kind:10}) {' '.join(bits)}")
        lines.append(f"  setting: {self.setting}")
        lines.append(f"  places: {', '.join(self.places)}")
        return "\n".join(lines)


SETTINGS = {
    "kitchen": "the kitchen",
    "porch": "the porch",
    "bedroom": "the bedroom",
    "yard": "the yard",
}

NAMES = ["Luna", "Maya", "Theo", "Nia", "Owen", "Zoe"]
HELPERS = ["Milo", "Ari", "Dad", "Gran", "Sam"]
OBJECTS = ["red mitten", "blue marble", "yellow key", "paper star"]

CLUES = {
    "red mitten": (
        "A red thread peeked from beneath the low shelf.",
        "followed the thread past the basket",
        "The mitten had slipped into the laundry basket when someone carried in the washing.",
        "returned the mitten to the coat hook",
    ),
    "blue marble": (
        "Something round clicked softly whenever the door moved.",
        "knelt down and watched the door's bottom edge",
        "The marble had rolled into the door track and was bumping as the door opened.",
        "placed the marble in its small toy cup",
    ),
    "yellow key": (
        "A tiny brass glint flashed beside the watering can.",
        "looked carefully around the watering can",
        "The key had fallen from a pocket while the garden tools were being put away.",
        "set the key in the family bowl",
    ),
    "paper star": (
        "A pale corner fluttered behind the curtain.",
        "held the curtain still and reached behind it",
        "A paper star from yesterday's craft had caught on the curtain rod.",
        "taped the star to the refrigerator",
    ),
}

OPENINGS = {
    "kitchen": "On an ordinary Saturday morning, Luna helped Milo put away the breakfast things in the kitchen.",
    "porch": "After lunch, Luna and Milo sat on the porch while a warm breeze moved the paper napkins.",
    "bedroom": "Before getting ready for bed, Luna and Milo tidied the bedroom together.",
    "yard": "In the late afternoon, Luna and Milo carried a basket of garden things across the yard.",
}


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="A slice-of-life storyworld about a kid solving a small mystery."
    )
    parser.add_argument("--setting", choices=SETTINGS)
    parser.add_argument("--seed", type=int, default=None)
    parser.add_argument("--name", choices=NAMES)
    parser.add_argument("--helper", choices=HELPERS)
    parser.add_argument("--object", dest="object_name", choices=OBJECTS)
    parser.add_argument("--trace", action="store_true")
    parser.add_argument("--qa", action="store_true")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--all", action="store_true")
    parser.add_argument("-n", type=int, default=1)
    parser.add_argument("--asp", action="store_true")
    parser.add_argument("--verify", action="store_true")
    parser.add_argument("--show-asp", action="store_true")
    return parser


def _validate_params(params: StoryParams) -> None:
    if params.setting not in SETTINGS:
        raise StoryError("Choose a familiar everyday setting.")
    if params.kid_name == params.helper_name:
        raise StoryError("The kid and helper need different names.")
    if params.object_name not in OBJECTS:
        raise StoryError("The mystery object must be one of the registered ordinary objects.")


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    params = StoryParams(
        setting=args.setting or rng.choice(list(SETTINGS)),
        seed=args.seed,
        kid_name=args.name or rng.choice(NAMES),
        helper_name=args.helper or rng.choice(HELPERS),
        object_name=args.object_name or rng.choice(OBJECTS),
    )
    _validate_params(params)
    return params


def make_world(params: StoryParams) -> World:
    kid = Entity(params.kid_name, "character", params.kid_name, "kid")
    helper = Entity(params.helper_name, "character", params.helper_name, "helper")
    mystery = Entity("mystery_object", "thing", params.object_name, "lost object")
    places = ["the starting spot", "the nearby shelf", "the final hiding place"]
    return World(SETTINGS[params.setting], kid, helper, mystery, places)


def _build_story(world: World, params: StoryParams) -> None:
    rng = random.Random((params.seed or 0) + 31337)
    kid = world.kid
    helper = world.helper
    mystery = world.mystery
    clue, action, reveal, cleanup = CLUES[mystery.label]

    kid.memes["worry"] = 1.0
    kid.memes["bravery"] = 0.0
    mystery.meters["hidden"] = 1.0
    helper.memes["patience"] = 1.0

    world.say(OPENINGS[params.setting])
    world.say(
        f"When Luna reached for the last cup, she noticed that the {mystery.label} "
        f"was missing from its usual place."
    )
    world.say(
        f'"Did you see my {mystery.label}?" Luna asked. '
        f'"Not yet," said {helper.label}, "but we can look carefully together."'
    )

    world.para()
    world.say(clue)
    world.say(
        f"Luna wanted to pretend the mystery was too hard, but {helper.label} pointed to "
        f"the small clue instead of guessing."
    )
    world.say(
        f'"What if I cannot find it?" Luna asked. '
        f'"Then we will learn from the next clue," {helper.label} replied.'
    )
    kid.inc_meme("bravery", 1.0)
    kid.inc_meter("careful_steps", 1.0)
    world.say(
        f"Luna took a slow breath and {action}. "
        f"That was bravery: not feeling sure, but continuing with care."
    )

    world.para()
    world.say(reveal)
    mystery.meters["hidden"] = 0.0
    mystery.meters["found"] = 1.0
    kid.memes["worry"] = 0.25
    world.say(
        f"The mystery had a simple answer. Nobody had taken the {mystery.label}; "
        f"it had moved during an ordinary household task."
    )
    world.say(
        f'"So the clue was telling us where to look," Luna said. '
        f'"Exactly," said {helper.label}. "Questions can be useful when we listen to the answers."'
    )

    world.para()
    kid.inc_meme("relief", 1.0)
    world.say(f"Together they {cleanup}.")
    world.say(
        f"Later, the {mystery.label} rested where it belonged, and Luna felt proud. "
        f"The little mystery had changed into a little lesson: careful questions can make a kid brave."
    )

    world.facts.update(
        clue=clue,
        action=action,
        reveal=reveal,
        cleanup=cleanup,
        found=True,
        brave=True,
    )


def generation_prompts(world: World) -> list[str]:
    return [
        f"Write a gentle slice-of-life story about a kid solving a small mystery in {world.setting}.",
        f"Tell a story where bravery means looking carefully for a missing {world.mystery.label}.",
        "Write a child-facing story with a twist, a brief dialogue exchange, and an ordinary object found in an unexpected place.",
    ]


def story_qa(world: World) -> list[QAItem]:
    kid = world.kid.label
    helper = world.helper.label
    obj = world.mystery.label
    return [
        QAItem(
            question=f"What mystery did {kid} need to solve?",
            answer=f"{kid} needed to find the missing {obj}.",
        ),
        QAItem(
            question=f"How did {helper} help {kid}?",
            answer=f"{helper} stayed patient, noticed the small clue, and searched together with {kid} instead of guessing.",
        ),
        QAItem(
            question="What was the twist?",
            answer=f"The {obj} had not been stolen or carried away on purpose; it had moved during an ordinary household task.",
        ),
        QAItem(
            question="How did the kid show bravery?",
            answer=f"The kid felt unsure but took a careful step, followed the clue, asked questions, and kept searching.",
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is bravery?",
            answer="Bravery is continuing carefully even when you feel uncertain or afraid.",
        ),
        QAItem(
            question="Why are clues useful?",
            answer="Clues give people sensible information about where to look and what may have happened.",
        ),
        QAItem(
            question="Why can an ordinary mystery be fun?",
            answer="An ordinary mystery invites careful noticing and can reveal an interesting reason behind a small surprise.",
        ),
        QAItem(
            question="What makes a helpful partner?",
            answer="A helpful partner listens, stays patient, and searches with you instead of making fun of your worry.",
        ),
    ]


ASP_RULES = r"""
lost_object(O) :- object(O), hidden(O).
careful_search(K) :- kid(K), clue_found(K), brave_step(K).
solved(O) :- lost_object(O), careful_search(K), reveal(O).
good_story(K,O) :- kid(K), object(O), solved(O).
"""


def asp_facts() -> str:
    import storyworlds.asp as asp

    lines = []
    for setting in SETTINGS:
        lines.append(asp.fact("setting", setting))
    for name in NAMES:
        lines.append(asp.fact("kid_name", name))
    for obj in OBJECTS:
        safe = obj.replace(" ", "_")
        lines.append(asp.fact("object", safe))
        lines.append(asp.fact("hidden", safe))
    lines.append(asp.fact("kid", "kid"))
    lines.append(asp.fact("clue_found", "kid"))
    lines.append(asp.fact("brave_step", "kid"))
    for obj in OBJECTS:
        lines.append(asp.fact("reveal", obj.replace(" ", "_")))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def _python_reasonable(params: StoryParams) -> bool:
    return (
        params.setting in SETTINGS
        and params.kid_name in NAMES
        and params.object_name in OBJECTS
        and params.kid_name != params.helper_name
    )


def asp_verify() -> int:
    probe = StoryParams(setting="kitchen", kid_name="Luna", helper_name="Milo", object_name="red mitten")
    if not _python_reasonable(probe):
        print("MISMATCH: Python reasonableness gate failed.")
        return 1
    sample = generate(probe)
    if not sample.world or not sample.world.facts.get("found") or not sample.world.facts.get("brave"):
        print("MISMATCH: generated story did not solve its mystery.")
        return 1
    try:
        import storyworlds.asp as asp
        models = asp.solve(asp_program("#show good_story/2."), models=1)
        if not models:
            print("MISMATCH: ASP twin found no good story.")
            return 1
    except ImportError:
        print("OK: Python parity verified; clingo unavailable.")
        return 0
    print("OK: Python and ASP parity verified.")
    return 0


def generate(params: StoryParams) -> StorySample:
    _validate_params(params)
    world = make_world(params)
    _build_story(world, params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_qa(world),
        world=world,
    )


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
        print(sample.world.trace())
    if qa:
        print("\n== Generation prompts ==")
        for index, prompt in enumerate(sample.prompts, 1):
            print(f"{index}. {prompt}")
        print("\n== Story questions ==")
        for item in sample.story_qa:
            print(f"Q: {item.question}")
            print(f"A: {item.answer}")
        print("\n== World questions ==")
        for item in sample.world_qa:
            print(f"Q: {item.question}")
            print(f"A: {item.answer}")


CURATED = [
    StoryParams("kitchen", kid_name="Luna", helper_name="Milo", object_name="red mitten"),
    StoryParams("porch", kid_name="Maya", helper_name="Ari", object_name="blue marble"),
    StoryParams("bedroom", kid_name="Theo", helper_name="Gran", object_name="paper star"),
    StoryParams("yard", kid_name="Nia", helper_name="Sam", object_name="yellow key"),
]


def build_all_samples() -> list[StorySample]:
    return [generate(params) for params in CURATED]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show good_story/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        try:
            import storyworlds.asp as asp
            models = asp.solve(asp_program("#show good_story/2."), models=1)
            print("ASP model found." if models else "ASP found no model.")
        except ImportError:
            print("ASP mode requires clingo.")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    if args.all:
        samples = build_all_samples()
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
            header=f"### variant {index + 1}" if len(samples) > 1 else "",
        )
        if index < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()

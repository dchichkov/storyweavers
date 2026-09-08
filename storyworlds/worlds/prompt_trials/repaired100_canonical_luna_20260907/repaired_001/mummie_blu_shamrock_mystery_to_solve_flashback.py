#!/usr/bin/env python3
"""
A gentle bedtime mystery about Mummie, Blu, and a lucky shamrock.

Mummie remembers a vanished shamrock in a flashback. Blu helps solve
the mystery by following a small trail of green clues.
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
while not os.path.exists(os.path.join(_storyworlds_dir, "results.py")):
    parent = os.path.dirname(_storyworlds_dir)
    if parent == _storyworlds_dir:
        break
    _storyworlds_dir = parent
sys.path.insert(0, _storyworlds_dir)
from results import QAItem, StoryError, StorySample  # noqa: E402


SETTINGS = {
    "moonlit_cottage": "the moonlit cottage",
    "quiet_garden": "the quiet garden",
    "hilltop_house": "the little house on the hill",
}
NAMES = ["Luna", "Pip", "Nora", "Milo"]
HELPERS = ["Blu", "Bramble", "Misty"]
SHAMROCK_PLACES = {
    "moonlit_cottage": "the round kitchen window",
    "quiet_garden": "the sleepy fountain",
    "hilltop_house": "the window seat",
}


@dataclass
class Entity:
    id: str
    kind: str
    label: str
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)


@dataclass
class World:
    place: str
    entities: dict[str, Entity] = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    facts: dict = field(default_factory=dict)

    def add(self, entity: Entity) -> Entity:
        self.entities[entity.id] = entity
        return entity

    def say(self, text: str) -> None:
        self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)


@dataclass
class StoryParams:
    place: str
    name: str
    helper: str
    seed: Optional[int] = None


CLUES = [
    ("a tiny green thread", "the thread led beneath the rocking chair"),
    ("three damp leaf prints", "the prints crossed the rug toward the garden door"),
    ("a soft green sparkle", "the sparkle winked beside the old flowerpot"),
]

FLASHBACKS = [
    "Mummie remembered an afternoon when she had tucked the shamrock into a blue ribbon for safekeeping.",
    "Mummie remembered carrying the shamrock home after a warm rain, while Blu danced around her boots.",
    "Mummie remembered placing the shamrock near the window and promising that its luck would be shared.",
]


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="A bedtime mystery about Mummie, Blu, and a shamrock.")
    parser.add_argument("--place", choices=SETTINGS)
    parser.add_argument("--name")
    parser.add_argument("--helper", choices=HELPERS)
    parser.add_argument("-n", type=int, default=1)
    parser.add_argument("--seed", type=int, default=None)
    parser.add_argument("--all", action="store_true")
    parser.add_argument("--trace", action="store_true")
    parser.add_argument("--qa", action="store_true")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--asp", action="store_true")
    parser.add_argument("--verify", action="store_true")
    parser.add_argument("--show-asp", action="store_true")
    return parser


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    return StoryParams(
        place=args.place or rng.choice(list(SETTINGS)),
        name=args.name or rng.choice(NAMES),
        helper=args.helper or rng.choice(HELPERS),
    )


def tell(params: StoryParams, rng: random.Random) -> World:
    if params.place not in SETTINGS:
        raise StoryError(f"Unknown place: {params.place}")
    if not params.name.strip():
        raise StoryError("The child needs a name.")
    if not params.helper.strip():
        raise StoryError("The mystery needs a helper.")

    world = World(SETTINGS[params.place])
    child = world.add(Entity("child", "character", params.name, memes={"curiosity": 1}))
    helper = world.add(Entity("blu", "character", params.helper, memes={"kindness": 1}))
    mummie = world.add(Entity("mummie", "character", "Mummie", memes={"memory": 1}))
    shamrock = world.add(Entity("shamrock", "object", "the shamrock", meters={"luck": 1}))
    clue, clue_path = rng.choice(CLUES)
    flashback = rng.choice(FLASHBACKS)
    hiding_place = SHAMROCK_PLACES[params.place]

    world.say(
        f"At bedtime in {world.place}, {child.label} noticed that Mummie's precious shamrock "
        "was missing from the little saucer by the lamp."
    )
    world.say(
        f"Mummie looked under the saucer and sighed. \"I had it before the moon came up,\" "
        f"she said. \"Can you help me solve this mystery, {child.label}?\""
    )
    world.say(
        f"{helper.label} sniffed the rug and gave a small, hopeful bark. "
        f"Then {child.label} found {clue}; {clue_path}."
    )
    world.para()

    world.say(f"Mummie closed her eyes, and a flashback floated through her thoughts: {flashback}")
    world.say(
        f"\"The blue ribbon!\" cried {child.label}. \"Maybe the shamrock followed it.\" "
        f"\"Then we should look gently,\" said {helper.label}. \"A mystery is solved best by careful eyes.\""
    )
    world.say(
        f"Together they followed the green trail to {hiding_place}. Behind a flowerpot, "
        f"the shamrock rested in a fold of the blue ribbon, safe and bright."
    )
    world.say(
        f"Mummie hugged {child.label} and {helper.label}. \"You remembered, listened, and looked together,\" "
        "she whispered. \"That is the luckiest thing of all.\""
    )
    world.say(
        f"After the shamrock returned to its saucer, the moon made a green patch of light on the floor, "
        f"and {child.label} fell asleep knowing that even a small mystery can end softly."
    )

    child.memes["relief"] = 1
    helper.memes["helpfulness"] = 1
    shamrock.meters["found"] = 1
    world.facts.update(
        child=child,
        helper=helper,
        mummie=mummie,
        shamrock=shamrock,
        clue=clue,
        clue_path=clue_path,
        flashback=flashback,
        hiding_place=hiding_place,
    )
    return world


def generation_prompts(world: World) -> list[str]:
    child = world.facts["child"]
    return [
        f"Write a bedtime mystery in which {child.label} helps Mummie find a missing shamrock with Blu.",
        "Tell a gentle story using a flashback, a green clue, and a peaceful ending.",
        "Write a child-friendly mystery to solve about a shamrock that disappears before bedtime.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child = f["child"]
    helper = f["helper"]
    return [
        QAItem(
            question=f"Who helped {child.label} solve the mystery of the missing shamrock?",
            answer=f"{child.label} worked with Mummie and {helper.label}. They followed a green clue and remembered the blue ribbon.",
        ),
        QAItem(
            question="What did Mummie remember in her flashback?",
            answer=f"Mummie remembered {f['flashback']}",
        ),
        QAItem(
            question="Where was the shamrock found?",
            answer=f"The shamrock was found at {f['hiding_place']}, tucked into a fold of the blue ribbon.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a shamrock?",
            answer="A shamrock is a small plant with three rounded leaves, often used as a sign of good luck.",
        ),
        QAItem(
            question="What is a flashback?",
            answer="A flashback is a moment in a story that shows something remembered from earlier.",
        ),
        QAItem(
            question="What does it mean to solve a mystery?",
            answer="To solve a mystery means to discover what happened by noticing clues and connecting them carefully.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    lines.extend(sample.prompts)
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


ASP_RULES = r"""
needed(mystery).
needed(flashback).
needed(shamrock).
needed(mummie).
needed(blu).
valid_story :- needed(mystery), needed(flashback), needed(shamrock),
               needed(mummie), needed(blu).
"""


def asp_facts() -> str:
    import asp
    return "\n".join(
        [
            asp.fact("needed", "mummie"),
            asp.fact("needed", "blu"),
            asp.fact("needed", "shamrock"),
            asp.fact("needed", "mystery"),
            asp.fact("needed", "flashback"),
        ]
    )


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    try:
        import asp
    except Exception as exc:
        print(f"ASP unavailable: {exc}")
        return 1
    model = asp.one_model(asp_program("#show valid_story/0."))
    if any(atom == "valid_story" for atom in model):
        print("OK: ASP story requirements are satisfied.")
        return 0
    print("MISMATCH: ASP story requirements are not satisfied.")
    return 1


def generate(params: StoryParams) -> StorySample:
    world = tell(params, random.Random(params.seed))
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
        print("\n-- trace --")
        for entity in sample.world.entities.values():
            print(
                f"{entity.id}: kind={entity.kind} label={entity.label} "
                f"meters={entity.meters} memes={entity.memes}"
            )
    if qa:
        print("\n" + format_qa(sample))


def main() -> None:
    args = build_parser().parse_args()

    if args.verify:
        raise SystemExit(asp_verify())
    if args.show_asp or args.asp:
        print(asp_program("#show valid_story/0."))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        for place in SETTINGS:
            for name in NAMES[:2]:
                params = StoryParams(place=place, name=name, helper="Blu", seed=base_seed)
                samples.append(generate(params))
    else:
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
        if index + 1 < len(samples):
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()

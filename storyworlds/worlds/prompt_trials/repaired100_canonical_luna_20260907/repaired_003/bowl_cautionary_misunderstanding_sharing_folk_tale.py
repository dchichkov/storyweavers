#!/usr/bin/env python3
"""
A small folk-tale storyworld about a bowl, a misunderstanding, and sharing.
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
    village: str
    seed: Optional[int] = None
    child_name: str = "Luna"
    neighbor_name: str = "Toma"
    bowl_kind: str = "blue clay bowl"
    feast: str = "berry porridge"


@dataclass
class Entity:
    id: str
    kind: str
    label: str
    type: str
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def change_meter(self, key: str, amount: float) -> None:
        self.meters[key] = self.meters.get(key, 0.0) + amount

    def change_meme(self, key: str, amount: float) -> None:
        self.memes[key] = self.memes.get(key, 0.0) + amount


@dataclass
class World:
    village: str
    child: Entity
    neighbor: Entity
    bowl: Entity
    porridge: Entity
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    facts: dict = field(default_factory=dict)

    def say(self, text: str) -> None:
        self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)

    def trace(self) -> str:
        lines = ["--- world model state ---"]
        for entity in [self.child, self.neighbor, self.bowl, self.porridge]:
            meters = {k: v for k, v in entity.meters.items() if v}
            memes = {k: v for k, v in entity.memes.items() if v}
            details = []
            if meters:
                details.append(f"meters={meters}")
            if memes:
                details.append(f"memes={memes}")
            lines.append(f"  {entity.id:10} ({entity.kind:9}) {' '.join(details)}")
        lines.append(f"  village: {self.village}")
        return "\n".join(lines)


VILLAGES = {
    "willow": "the village beneath the willows",
    "hill": "the hill village",
    "river": "the village beside the river",
    "orchard": "the orchard village",
}

NAMES = ["Luna", "Mira", "Nia", "Suri", "Oren"]
NEIGHBORS = ["Toma", "Pema", "Rafi", "Anya"]
BOWLS = ["blue clay bowl", "red wooden bowl", "green stone bowl"]
FEASTS = ["berry porridge", "honey cakes", "warm bean stew"]

SCENES = {
    "willow": [
        "{child} lived in the village beneath the willows, where neighbors left food on one long table.",
        "In the village beneath the willows, {child} carried a bowl to the evening table beneath the trees.",
    ],
    "hill": [
        "{child} lived in the hill village, where every path curled around a shared cooking fire.",
        "One golden morning in the hill village, {child} carried a bowl toward the common fire.",
    ],
    "river": [
        "{child} lived in the village beside the river, where families shared supper after drawing water.",
        "At sunset in the village beside the river, {child} brought a bowl to the riverside table.",
    ],
    "orchard": [
        "{child} lived in the orchard village, where ripe fruit was counted carefully but eaten together.",
        "When the apple trees were bright with fruit, {child} carried a bowl through the orchard village.",
    ],
}

MISUNDERSTANDINGS = [
    (
        "A gust lifted the cloth covering the table, and the bowl rolled out of sight.",
        "I thought you took my bowl because you wanted the feast for yourself.",
        "The bowl had slipped behind a basket, and no one had taken it.",
        "looked behind the basket",
    ),
    (
        "The evening bell rang just as {neighbor} carried the bowl toward the fire.",
        "I thought you were hiding the food from me.",
        "The bell had startled {neighbor}, who was only moving the bowl to a warmer place.",
        "carried the bowl back to the table",
    ),
    (
        "A little fox-shaped shadow crossed the wall, and the bowl was suddenly empty.",
        "I thought you ate everything without asking.",
        "A kitten had licked the last spoonful while everyone watched the strange shadow.",
        "filled the bowl again from the cooking pot",
    ),
]

LESSONS = [
    "A guess can grow large in the dark, but a kind question can make it small.",
    "Before guarding a meal, ask what happened; truth is often hiding nearby.",
    "A shared table has room for patience as well as food.",
]


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="A cautionary folk tale about a bowl, a misunderstanding, and sharing."
    )
    parser.add_argument("--village", choices=VILLAGES)
    parser.add_argument("--seed", type=int, default=None)
    parser.add_argument("--name", choices=NAMES)
    parser.add_argument("--neighbor", choices=NEIGHBORS)
    parser.add_argument("--bowl", choices=BOWLS)
    parser.add_argument("--feast", choices=FEASTS)
    parser.add_argument("-n", type=int, default=1)
    parser.add_argument("--all", action="store_true")
    parser.add_argument("--trace", action="store_true")
    parser.add_argument("--qa", action="store_true")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--asp", action="store_true")
    parser.add_argument("--verify", action="store_true")
    parser.add_argument("--show-asp", action="store_true")
    return parser


def validate(params: StoryParams) -> None:
    if params.village not in VILLAGES:
        raise StoryError("Choose a village with a shared table.")
    if params.child_name == params.neighbor_name:
        raise StoryError("The child and neighbor must have different names.")
    if "bowl" not in params.bowl_kind:
        raise StoryError("The story needs a bowl.")
    if not params.feast:
        raise StoryError("The shared meal cannot be empty.")


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    params = StoryParams(
        village=args.village or rng.choice(list(VILLAGES)),
        seed=args.seed,
        child_name=args.name or rng.choice(NAMES),
        neighbor_name=args.neighbor or rng.choice(NEIGHBORS),
        bowl_kind=args.bowl or rng.choice(BOWLS),
        feast=args.feast or rng.choice(FEASTS),
    )
    validate(params)
    return params


def make_world(params: StoryParams) -> World:
    child = Entity(
        id="child",
        kind="character",
        label=params.child_name,
        type="child",
        memes={"trust": 0.5, "patience": 0.2},
    )
    neighbor = Entity(
        id="neighbor",
        kind="character",
        label=params.neighbor_name,
        type="neighbor",
        memes={"trust": 0.5},
    )
    bowl = Entity(
        id="bowl",
        kind="thing",
        label=params.bowl_kind,
        type="serving bowl",
        meters={"food": 1.0, "visible": 1.0},
    )
    porridge = Entity(
        id="meal",
        kind="thing",
        label=params.feast,
        type="shared meal",
        meters={"servings": 2.0},
    )
    return World(
        village=VILLAGES[params.village],
        child=child,
        neighbor=neighbor,
        bowl=bowl,
        porridge=porridge,
    )


def build_story(world: World, params: StoryParams) -> None:
    rng = random.Random((params.seed or 0) + 4517)
    child = world.child
    neighbor = world.neighbor
    bowl = world.bowl
    meal = world.porridge

    opening = rng.choice(SCENES[params.village]).format(child=child.label)
    event, accusation, truth, action = rng.choice(MISUNDERSTANDINGS)
    event = event.format(neighbor=neighbor.label)
    accusation = accusation.format(neighbor=neighbor.label)
    truth = truth.format(neighbor=neighbor.label)
    lesson = rng.choice(LESSONS)

    child.memes["worry"] = 0.4
    bowl.meters["food"] = 1.0
    meal.meters["servings"] = 2.0

    world.say(opening)
    world.say(
        f"That night, {child.label} filled a {bowl.label} with {meal.label} and set it "
        f"on the table for everyone."
    )
    world.say(event)

    world.para()
    world.say(
        f'{child.label} frowned at {neighbor.label}. "{accusation}" '
        f'{neighbor.label} blinked and held up both hands. '
        f'"Please ask me what happened before you decide I did wrong."'
    )
    child.change_meme("worry", 0.2)
    child.change_meme("patience", 0.5)
    child.change_meter("questions_asked", 1.0)

    world.say(
        f"{child.label} took a slow breath and asked, "
        f'"Where was the {bowl.label} going, and who saw it last?"'
    )
    neighbor.change_meme("trust", 0.3)
    child.change_meme("trust", 0.2)

    world.para()
    world.say(truth)
    bowl.meters["visible"] = 1.0
    bowl.meters["food"] = 0.5
    child.memes["worry"] = 0.0
    world.say(
        f"The mistake felt heavy for a moment, so {child.label} spoke plainly. "
        f'"I am sorry, {neighbor.label}. I guessed instead of asking."'
    )
    world.say(
        f'{neighbor.label} smiled. "Then let us mend the mistake together." '
        f'They {action}, and the warm smell of supper rose into the evening air.'
    )

    world.para()
    child.change_meme("sharing", 1.0)
    neighbor.change_meme("sharing", 1.0)
    meal.meters["servings"] = 0.0
    bowl.meters["shared"] = 1.0
    world.say(
        f"{child.label} divided the {meal.label} between two smaller plates, "
        f"leaving the {bowl.label} bright and clean between them."
    )
    world.say(
        f"They ate side by side while the villagers listened. {lesson} "
        f"From then on, the bowl was passed with a question, a thank-you, and enough for one more friend."
    )

    world.facts.update(
        event=event,
        accusation=accusation,
        truth=truth,
        action=action,
        lesson=lesson,
        bowl=bowl.label,
        meal=meal.label,
    )


def prompts(world: World) -> list[str]:
    return [
        f"Tell a cautionary folk tale about {world.child.label}, a bowl, and a misunderstanding at a shared table.",
        f"Write a gentle story in which {world.child.label} asks {world.neighbor.label} a question before making an accusation.",
        f"Create a child-friendly folk tale where a bowl and a shared meal teach the value of patience and sharing.",
    ]


def story_questions(world: World) -> list[QAItem]:
    child = world.child.label
    neighbor = world.neighbor.label
    return [
        QAItem(
            question=f"Why did {child} become upset with {neighbor}?",
            answer=f"{child} misunderstood what happened to the bowl and guessed that {neighbor} had taken or hidden the food.",
        ),
        QAItem(
            question=f"How did {child} discover the truth?",
            answer=f"{child} stopped guessing and asked where the bowl had been, which revealed that the bowl had moved for an innocent reason.",
        ),
        QAItem(
            question="What did the bowl teach the villagers?",
            answer="It taught them to ask kind questions before blaming someone and to share food after making peace.",
        ),
        QAItem(
            question="How did the story end?",
            answer=f"{child} and {neighbor} divided the {world.porridge.label} and ate together beside the clean bowl.",
        ),
    ]


def world_questions(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a misunderstanding?",
            answer="A misunderstanding is a mistaken idea about what someone meant or what happened.",
        ),
        QAItem(
            question="Why is asking a question helpful?",
            answer="A question can reveal facts that a quick guess misses and can prevent an unfair accusation.",
        ),
        QAItem(
            question="What does sharing mean?",
            answer="Sharing means giving others a fair part of something so people can enjoy it together.",
        ),
        QAItem(
            question="What is a cautionary tale?",
            answer="A cautionary tale tells about a mistake and shows a lesson that may help people make wiser choices.",
        ),
    ]


ASP_RULES = r"""
has_bowl(B) :- bowl(B).
shared_meal(M) :- meal(M), servings(M,2).
patient(C) :- asks_question(C).
misunderstanding_resolved(C) :- patient(C), learns_truth(C).
sharing_good(C) :- misunderstanding_resolved(C), shares(C).
folk_tale_wise(C) :- sharing_good(C), apologizes(C).
"""


def asp_facts() -> str:
    import storyworlds.asp as asp

    lines = []
    for village in VILLAGES:
        lines.append(asp.fact("village", village))
    for bowl in BOWLS:
        safe = bowl.replace(" ", "_")
        lines.append(asp.fact("bowl", safe))
    for feast in FEASTS:
        safe = feast.replace(" ", "_")
        lines.append(asp.fact("meal", safe))
    lines.append(asp.fact("servings", "berry_porridge", 2))
    lines.append(asp.fact("asks_question", "child"))
    lines.append(asp.fact("learns_truth", "child"))
    lines.append(asp.fact("shares", "child"))
    lines.append(asp.fact("apologizes", "child"))
    return "\n".join(lines)


def asp_program(show: str = "#show folk_tale_wise/1.") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def python_reasonable(params: StoryParams) -> bool:
    try:
        validate(params)
    except StoryError:
        return False
    return True


def asp_verify() -> int:
    params = StoryParams(village="willow")
    if not python_reasonable(params):
        print("MISMATCH: Python reasonableness gate failed.")
        return 1
    try:
        import storyworlds.asp as asp

        model = asp.one_model(asp_program())
        atoms = asp.atoms(model, "folk_tale_wise")
        if ("child",) not in atoms:
            print("MISMATCH: ASP twin did not derive the expected lesson.")
            return 1
    except Exception as exc:
        print(f"ASP unavailable or failed: {exc}")
        return 1
    sample = generate(params)
    if "bowl" not in sample.story.lower() or "share" not in sample.story.lower():
        print("MISMATCH: generated story omitted required domain facts.")
        return 1
    print("OK: Python and ASP agree on the bowl-sharing folk tale.")
    return 0


def generate(params: StoryParams) -> StorySample:
    validate(params)
    world = make_world(params)
    build_story(world, params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=prompts(world),
        story_qa=story_questions(world),
        world_qa=world_questions(world),
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
        for i, prompt in enumerate(sample.prompts, 1):
            print(f"{i}. {prompt}")
        print("\n== Story questions ==")
        for item in sample.story_qa:
            print(f"Q: {item.question}")
            print(f"A: {item.answer}")
        print("\n== World questions ==")
        for item in sample.world_qa:
            print(f"Q: {item.question}")
            print(f"A: {item.answer}")


CURATED = [
    StoryParams(village="willow", child_name="Luna", neighbor_name="Toma", bowl_kind="blue clay bowl", feast="berry porridge"),
    StoryParams(village="hill", child_name="Mira", neighbor_name="Pema", bowl_kind="red wooden bowl", feast="honey cakes"),
    StoryParams(village="river", child_name="Nia", neighbor_name="Rafi", bowl_kind="green stone bowl", feast="warm bean stew"),
    StoryParams(village="orchard", child_name="Suri", neighbor_name="Anya", bowl_kind="blue clay bowl", feast="berry porridge"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program())
        return
    if args.verify:
        raise SystemExit(asp_verify())
    if args.asp:
        print(asp_program())
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    if args.all:
        samples = [generate(params) for params in CURATED]
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
        header = f"### variant {index + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if index < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()

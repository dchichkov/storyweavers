#!/usr/bin/env python3
"""
A heartwarming storyworld about an excavator, a dependent friend, and the
bravery that grows through friendship.
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
    child_name: str = "Luna"
    friend_name: str = "Pip"
    machine_name: str = "Sunny"
    challenge: str = "a muddy hill"
    style: str = "heartwarming"


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
    child: Entity
    dependent: Entity
    excavator: Entity
    hill: Entity
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
        for entity in (self.child, self.dependent, self.excavator, self.hill):
            meters = {k: v for k, v in entity.meters.items() if v}
            memes = {k: v for k, v in entity.memes.items() if v}
            details = []
            if meters:
                details.append(f"meters={meters}")
            if memes:
                details.append(f"memes={memes}")
            lines.append(
                f"  {entity.id:12} ({entity.kind:10}) {' '.join(details)}"
            )
        lines.append(f"  setting: {self.setting}")
        return "\n".join(lines)


SETTINGS = {
    "meadow": "the meadow edge",
    "orchard": "the old orchard",
    "riverside": "the riverside field",
    "hilltop": "the hilltop garden",
}

NAMES = ["Luna", "Milo", "Nia", "Theo", "Iris"]
FRIENDS = ["Pip", "Bram", "Clover", "Toby", "Wren"]
MACHINES = ["Sunny", "Goldie", "Little Digger", "Amber"]
CHALLENGES = [
    "a muddy hill",
    "a buried garden gate",
    "a narrow trench",
    "a fallen pile of stones",
]

OPENINGS = {
    "meadow": [
        "{child} visited {setting} with {friend}, who depended on a small bridge to reach the flower patch.",
        "At {setting}, {child} and {friend} found the morning path blocked by wet earth.",
    ],
    "orchard": [
        "{child} and {friend} met beneath the apple trees at {setting}.",
        "After a night of rain, {child} joined {friend} in the orchard to inspect the crooked path.",
    ],
    "riverside": [
        "Near {setting}, {child} noticed that the rain had changed the familiar path.",
        "{child} and {friend} arrived at {setting} just as the river breeze lifted the last clouds.",
    ],
    "hilltop": [
        "On {setting}, {child} found {friend} waiting beside a steep, muddy path.",
        "The garden on {setting} needed help, and {child} came with {friend} to see what could be done.",
    ],
}


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="A heartwarming excavator story about friendship and bravery."
    )
    parser.add_argument("--setting", choices=SETTINGS)
    parser.add_argument("--seed", type=int, default=None)
    parser.add_argument("--name", choices=NAMES)
    parser.add_argument("--friend", choices=FRIENDS)
    parser.add_argument("--machine", choices=MACHINES)
    parser.add_argument("--challenge", choices=CHALLENGES)
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
        raise StoryError("Choose a known setting for the excavator story.")
    if params.child_name == params.friend_name:
        raise StoryError("The child and dependent friend must have different names.")
    if params.challenge not in CHALLENGES:
        raise StoryError("Choose a listed, manageable construction challenge.")


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    params = StoryParams(
        setting=args.setting or rng.choice(list(SETTINGS)),
        seed=args.seed,
        child_name=args.name or rng.choice(NAMES),
        friend_name=args.friend or rng.choice(FRIENDS),
        machine_name=args.machine or rng.choice(MACHINES),
        challenge=args.challenge or rng.choice(CHALLENGES),
    )
    _validate_params(params)
    return params


def make_world(params: StoryParams) -> World:
    child = Entity(
        id="child",
        kind="character",
        label=params.child_name,
        type="young helper",
        memes={"friendship": 0.0, "bravery": 0.0},
    )
    dependent = Entity(
        id="dependent",
        kind="character",
        label=params.friend_name,
        type="dependent friend",
        memes={"trust": 0.0, "belonging": 0.0},
    )
    excavator = Entity(
        id="excavator",
        kind="machine",
        label=params.machine_name,
        type="small excavator",
        meters={"fuel": 1.0, "digging_power": 1.0},
    )
    hill = Entity(
        id="challenge",
        kind="place",
        label=params.challenge,
        type="obstacle",
        meters={"blocked": 1.0, "risk": 1.0},
    )
    return World(
        setting=SETTINGS[params.setting],
        child=child,
        dependent=dependent,
        excavator=excavator,
        hill=hill,
    )


def _build_story(world: World, params: StoryParams) -> None:
    child = world.child
    friend = world.dependent
    machine = world.excavator
    hill = world.hill
    rng = random.Random((params.seed or 0) + 31847)

    opening = rng.choice(OPENINGS[params.setting]).format(
        child=child.label,
        friend=friend.label,
        setting=world.setting,
    )
    world.say(opening)
    world.say(
        f"{friend.label} was dependent on the little path because the steep mud "
        f"made every step uncertain. {child.label} wanted to help, but the "
        f"excavator named {machine.label} looked enormous beside the flowers."
    )
    world.say(
        f'"What if I make the {params.challenge} worse?" {child.label} whispered. '
        f'"You do not have to be fearless," said {friend.label}. "Just stay with me."'
    )

    child.memes["friendship"] = 1.0
    friend.memes["trust"] = 1.0
    world.para()
    world.say(
        f"{child.label} took a slow breath. Inside, a small thought answered, "
        f'"I can be careful, and I do not have to do this alone."'
    )
    child.memes["bravery"] = 1.0
    child.inc_meter("steady_choices", 1.0)
    friend.inc_meter("safe_waiting", 1.0)
    world.say(
        f"{child.label} climbed into {machine.label}, kept both hands gentle on "
        f"the controls, and began with the smallest scoop."
    )
    machine.inc_meter("careful_scoops", 1.0)
    hill.meters["risk"] = 0.5

    world.para()
    world.say(
        f"The first scoop moved only a little soil. Then {friend.label} called, "
        f'"A stone is tucked under the roots. Try from the left!"'
    )
    world.say(
        f"{child.label} listened, turned the excavator slowly, and lifted the "
        f"stone without shaking the young plants. The path opened like a quiet smile."
    )
    machine.inc_meter("careful_scoops", 2.0)
    hill.meters["blocked"] = 0.0
    hill.meters["risk"] = 0.0
    friend.memes["belonging"] = 1.0

    world.para()
    world.say(
        f"{friend.label} crossed the cleared ground safely and reached for "
        f"{child.label}'s hand. Together they placed a bright ribbon beside the path "
        f"so everyone would know where to walk."
    )
    child.inc_meme("joy", 1.0)
    friend.inc_meme("joy", 1.0)
    world.say(
        f"{child.label} looked at the resting excavator and smiled. The machine "
        f"had moved the earth, but friendship had helped {child.label} find the courage "
        f"to move one careful thought at a time."
    )
    world.say(
        f"By sunset, {friend.label} was safe on the flower side of the path, "
        f"and {machine.label} rested beneath a golden sky while two friends planned "
        f"what they would build together next."
    )

    world.facts.update(
        opening=opening,
        challenge=params.challenge,
        friend_helped=True,
        obstacle_cleared=True,
        brave_choice=True,
        inner_thought="I can be careful, and I do not have to do this alone.",
    )


def generation_prompts(world: World) -> list[str]:
    return [
        f"Write a heartwarming story about {world.child.label}, an excavator, and a dependent friend at {world.setting}.",
        f"Tell a gentle tale where friendship helps a child use an excavator bravely and carefully.",
        f"Write a story with an inner monologue, a small construction challenge, helpful dialogue, and a hopeful ending.",
    ]


def story_qa(world: World) -> list[QAItem]:
    child = world.child.label
    friend = world.dependent.label
    machine = world.excavator.label
    return [
        QAItem(
            question=f"Why did {friend} need help?",
            answer=(
                f"{friend} depended on the path because the muddy obstacle made "
                f"walking safely difficult."
            ),
        ),
        QAItem(
            question=f"How did {child} show bravery?",
            answer=(
                f"{child} admitted feeling worried, listened to {friend}, and used "
                f"{machine} carefully instead of giving up."
            ),
        ),
        QAItem(
            question="What did the friends discover?",
            answer=(
                "They discovered that bravery can be careful and that friendship "
                "makes a difficult task feel possible."
            ),
        ),
        QAItem(
            question="What changed at the end?",
            answer=(
                f"The obstacle was cleared, {friend} could cross safely, and the "
                f"two friends planned another kind project together."
            ),
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is an excavator?",
            answer=(
                "An excavator is a construction machine with a bucket and arm "
                "for moving soil, stones, and other materials."
            ),
        ),
        QAItem(
            question="What does dependent mean?",
            answer=(
                "Dependent means needing support or help from another person or thing."
            ),
        ),
        QAItem(
            question="What is bravery?",
            answer=(
                "Bravery is choosing a careful, helpful action even when you feel worried."
            ),
        ),
        QAItem(
            question="How can friendship help?",
            answer=(
                "Friendship can offer encouragement, useful ideas, and a sense that "
                "no one has to face a hard task alone."
            ),
        ),
    ]


ASP_RULES = r"""
safe_plan(C) :- careful(C), supported(C), obstacle_cleared(C).
brave(C) :- worried(C), safe_plan(C).
friendship_grows(C,F) :- brave(C), encourages(F), helps(C,F).
good_story(C,F,M) :- friendship_grows(C,F), machine(M), safe_plan(C).
"""


def asp_facts() -> str:
    import storyworlds.asp as asp

    lines = []
    for setting in SETTINGS:
        lines.append(asp.fact("setting", setting))
    for name in NAMES:
        lines.append(asp.fact("child_name", name))
    for friend in FRIENDS:
        lines.append(asp.fact("dependent_name", friend))
    for machine in MACHINES:
        lines.append(asp.fact("machine", machine.replace(" ", "_")))
    for challenge in CHALLENGES:
        lines.append(asp.fact("obstacle", challenge.replace(" ", "_")))
    lines.extend(
        [
            asp.fact("worried", "child"),
            asp.fact("careful", "child"),
            asp.fact("supported", "child"),
            asp.fact("encourages", "dependent"),
            asp.fact("helps", "child", "dependent"),
            asp.fact("obstacle_cleared", "child"),
        ]
    )
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def _python_reasonable(params: StoryParams) -> bool:
    return (
        params.setting in SETTINGS
        and params.child_name != params.friend_name
        and params.machine_name in MACHINES
        and params.challenge in CHALLENGES
    )


def asp_verify() -> int:
    params = StoryParams(setting="meadow")
    if not _python_reasonable(params):
        print("MISMATCH: Python reasonableness gate failed.")
        return 1
    sample = generate(params)
    if not sample.world or not sample.world.facts.get("obstacle_cleared"):
        print("MISMATCH: generated story did not clear its obstacle.")
        return 1
    try:
        import storyworlds.asp as asp

        model = asp.one_model(asp_program("#show good_story/3."))
        if not any(symbol.name == "good_story" for symbol in model):
            print("MISMATCH: ASP twin found no good story.")
            return 1
    except ImportError:
        print("OK: Python gate and generated story verified; clingo unavailable.")
        return 0
    print("OK: Python and ASP checks agree.")
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
    StoryParams(
        setting="meadow",
        child_name="Luna",
        friend_name="Pip",
        machine_name="Sunny",
        challenge="a muddy hill",
    ),
    StoryParams(
        setting="orchard",
        child_name="Milo",
        friend_name="Clover",
        machine_name="Goldie",
        challenge="a buried garden gate",
    ),
    StoryParams(
        setting="riverside",
        child_name="Nia",
        friend_name="Bram",
        machine_name="Little Digger",
        challenge="a narrow trench",
    ),
    StoryParams(
        setting="hilltop",
        child_name="Theo",
        friend_name="Wren",
        machine_name="Amber",
        challenge="a fallen pile of stones",
    ),
]


def build_all_samples() -> list[StorySample]:
    return [generate(params) for params in CURATED]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show good_story/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        try:
            import storyworlds.asp as asp

            models = asp.solve(asp_program("#show good_story/3."), models=1)
            print(f"ASP models found: {len(models)}")
        except ImportError:
            print("ASP mode requires clingo, which is not installed.")
        return

    if args.n < 1:
        raise StoryError("The number of stories must be at least one.")

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

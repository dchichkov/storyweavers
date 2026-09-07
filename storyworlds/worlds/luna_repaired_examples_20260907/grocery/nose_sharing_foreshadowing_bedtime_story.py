#!/usr/bin/env python3
"""
A gentle bedtime storyworld about a curious nose, a shared mooncake, and a
small warning that helps friends choose kindness before trouble arrives.
"""

from __future__ import annotations

import argparse
import json
import os
import random
import sys
from dataclasses import dataclass, field
from typing import Optional

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(HERE))))
sys.path.insert(0, os.path.join(ROOT, "storyworlds"))
from results import QAItem, StoryError, StorySample  # noqa: E402


@dataclass
class Entity:
    id: str
    kind: str
    label: str
    location: str
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)


@dataclass
class World:
    entities: dict[str, Entity] = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    facts: dict[str, object] = field(default_factory=dict)

    def add(self, entity: Entity) -> Entity:
        self.entities[entity.id] = entity
        return entity

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)


@dataclass
class StoryParams:
    child: str
    friend: str
    moon: str
    treat: str
    sharing: str
    foreshadowing: str
    ending: str
    seed: Optional[int] = None


@dataclass(frozen=True)
class Sharing:
    temptation: str
    choice: str
    lesson: str


@dataclass(frozen=True)
class Foreshadowing:
    sign: str
    meaning: str
    help: str


@dataclass(frozen=True)
class Ending:
    image: str
    line: str


NAMES = ["Nora", "Milo", "Lumi", "Pip", "Tessa", "Oren", "Mina", "Sol"]
MOONS = ["the sleepy moon", "the silver moon", "the round moon", "the little moon"]

SHARING = {
    "half": Sharing(
        temptation="keep the warmest piece tucked beneath the blanket",
        choice="break the treat into two equal pieces and offer the larger-looking one first",
        lesson="a shared joy can make even a small treat feel large",
    ),
    "welcome": Sharing(
        temptation="save the treat only for an old friend",
        choice="make room beside the pillow and welcome a new visitor to the midnight snack",
        lesson="kindness grows when there is room for one more",
    ),
    "last_bite": Sharing(
        temptation="hide the last sweet bite behind a book",
        choice="pass the last bite back and forth until each friend had tasted it",
        lesson="giving away the last bit can leave the heart full",
    ),
    "lantern": Sharing(
        temptation="carry the brightest lantern alone",
        choice="hold the lantern between them so both friends could see",
        lesson="a light shared by two friends shines farther",
    ),
}

FORESHADOWING = {
    "peppermint": Foreshadowing(
        sign="a cool peppermint scent slipped beneath the bedroom door",
        meaning="the old house would soon need someone to notice a hidden draft",
        help="followed the scent to a loose window latch",
    ),
    "tickle": Foreshadowing(
        sign="the child's nose gave one tiny tickle whenever the curtain moved",
        meaning="the night breeze was carrying something small toward the bed",
        help="lifted the blanket and found a fallen feather before it could tickle anyone awake",
    ),
    "cinnamon": Foreshadowing(
        sign="a cinnamon smell curled out from under the toy chest",
        meaning="something warm and forgotten was waiting there",
        help="looked under the chest and found a cooling cup of cocoa",
    ),
    "rain": Foreshadowing(
        sign="the nose noticed the soft, wet smell of rain before the first drop tapped the roof",
        meaning="the open skylight needed to be closed",
        help="climbed onto a sturdy stool and shut the skylight",
    ),
}

ENDINGS = {
    "dreamboat": Ending(
        "Soon the pillows became a little boat sailing across a quiet blue dream",
        "The friends slept peacefully, sharing the moonlight and the last warm smile.",
    ),
    "window": Ending(
        "At the window, the moon laid a pale path across the floor",
        "Every careful nose and every generous hand rested beneath its gentle glow.",
    ),
    "blanket": Ending(
        "The blanket rose and fell like a calm hill around the two friends",
        "Outside, the night whispered that sharing made a safe place warmer.",
    ),
    "star": Ending(
        "One bright star blinked above the roof as the bedroom grew still",
        "Even the smallest kindness seemed to shine all the way up to the sky.",
    ),
}


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="A sharing bedtime story about a curious nose.")
    parser.add_argument("--child")
    parser.add_argument("--friend")
    parser.add_argument("--moon", choices=MOONS)
    parser.add_argument("--treat", default="a warm mooncake")
    parser.add_argument("--sharing", choices=SHARING)
    parser.add_argument("--foreshadowing", choices=FORESHADOWING)
    parser.add_argument("--ending", choices=ENDINGS)
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
    child = args.child or rng.choice(NAMES)
    friend = args.friend or rng.choice([name for name in NAMES if name != child])
    if child == friend:
        raise StoryError("The bedtime friends need different names.")
    return StoryParams(
        child=child,
        friend=friend,
        moon=args.moon or rng.choice(MOONS),
        treat=args.treat,
        sharing=args.sharing or rng.choice(tuple(SHARING)),
        foreshadowing=args.foreshadowing or rng.choice(tuple(FORESHADOWING)),
        ending=args.ending or rng.choice(tuple(ENDINGS)),
    )


def tell(params: StoryParams) -> World:
    sharing = SHARING[params.sharing]
    sign = FORESHADOWING[params.foreshadowing]
    ending = ENDINGS[params.ending]

    world = World()
    child = world.add(Entity(params.child, "child", params.child, "bedroom"))
    friend = world.add(Entity(params.friend, "friend", params.friend, "bedroom"))
    nose = world.add(Entity("nose", "body", "curious nose", "bedroom"))
    moon = world.add(Entity("moon", "moon", params.moon, "sky"))
    treat = world.add(Entity("treat", "food", params.treat, "bedroom"))

    world.facts.update(
        child=child,
        friend=friend,
        nose=nose,
        moon=moon,
        treat=treat,
        sharing=sharing,
        sign=sign,
        ending=ending,
    )

    world.say(
        f"Once, when the house was quiet and bedtime had tucked the stars into the sky, "
        f"{child.label} heard a soft rustle beside the pillow."
    )
    world.say(
        f"{child.label}'s nose lifted first. It knew the sweet smell of {treat.label} "
        f"before {child.label} even opened their eyes."
    )
    world.say(
        f"Beside the bed, {friend.label} was waiting beneath the glow of {moon.label}, "
        f"holding the treat with both hands."
    )

    world.para()
    nose.meters["scent"] = 1.0
    world.say(f"Then the nose noticed something else: {sign.sign}.")
    world.say(
        f"It was a small warning, but {child.label} remembered that a small warning "
        f"could become important before morning."
    )
    world.facts["warning_heard"] = True

    world.para()
    child.memes["want"] = 1.0
    friend.memes["want"] = 1.0
    world.say(
        f"For one sleepy moment, {child.label} was tempted to {sharing.temptation}."
    )
    world.say(
        f"But {friend.label} looked hopeful, and the nose kept remembering the strange sign."
    )
    world.say(
        f"Together, they chose to {sharing.choice}."
    )
    child.memes["generosity"] = 1.0
    friend.memes["generosity"] = 1.0

    world.para()
    world.say(
        f"After the first bite, {child.label} and {friend.label} {sign.help}."
    )
    world.say(
        f"The room grew safer, and the sweet smell of {treat.label} no longer had to hide "
        f"beneath a worry."
    )
    world.facts["danger_prevented"] = sign.meaning
    world.facts["resolved"] = True

    world.say(
        f"They smiled at one another and understood that {sharing.lesson}."
    )
    world.say(f"{ending.image}.")
    world.say(ending.line)
    return world


def generate(params: StoryParams) -> StorySample:
    world = tell(params)
    child = world.facts["child"]
    friend = world.facts["friend"]
    sign = world.facts["sign"]
    sharing = world.facts["sharing"]
    return StorySample(
        params=params,
        story=world.render(),
        prompts=[
            f"Write a gentle bedtime story about {child.label}, {friend.label}, and a curious nose.",
            f"Include a small warning: {sign.sign}.",
            f"Show how sharing {params.treat} helps the friends feel safe and close.",
        ],
        story_qa=[
            QAItem(
                f"What did {child.label}'s nose notice first?",
                f"{child.label}'s nose noticed the sweet smell of {params.treat} before anything else.",
            ),
            QAItem(
                "What small warning appeared in the bedroom?",
                f"The nose noticed that {sign.sign}.",
            ),
            QAItem(
                f"How did {child.label} and {friend.label} practice sharing?",
                f"They chose to {sharing.choice}.",
            ),
            QAItem(
                "What did the friends learn?",
                f"They learned that {sharing.lesson}.",
            ),
        ],
        world_qa=[
            QAItem(
                "What is a nose used for?",
                "A nose helps a person breathe and notice smells.",
            ),
            QAItem(
                "Why can a small warning be helpful?",
                "A small warning can give someone time to notice a problem and make a safe choice.",
            ),
            QAItem(
                "Why is sharing kind?",
                "Sharing lets other people enjoy something too and can make friendship stronger.",
            ),
        ],
        world=world,
    )


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for entity in world.entities.values():
        lines.append(
            f"  {entity.id:8} ({entity.kind:6}) location={entity.location} "
            f"meters={entity.meters} memes={entity.memes}"
        )
    lines.append(f"  facts: warning_heard={world.facts.get('warning_heard')}, "
                 f"danger_prevented={world.facts.get('danger_prevented')}, "
                 f"resolved={world.facts.get('resolved')}")
    return "\n".join(lines)


def show_qa_item(item: QAItem) -> str:
    return f"Q: {item.question}\nA: {item.answer}"


ASP_RULES = r"""
valid_domain(bedroom).
has_feature(bedroom,sharing).
has_feature(bedroom,foreshadowing).
uses_object(bedroom,nose).
valid_story(bedroom,nose,sharing,foreshadowing).
"""


def asp_facts() -> str:
    import asp
    return "\n".join(
        [
            asp.fact("valid_domain", "bedroom"),
            asp.fact("has_feature", "bedroom", "sharing"),
            asp.fact("has_feature", "bedroom", "foreshadowing"),
            asp.fact("uses_object", "bedroom", "nose"),
        ]
    )


def asp_program(show: str = "#show valid_story/4.") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_stories() -> set[tuple]:
    import asp
    model = asp.one_model(asp_program())
    return set(asp.atoms(model, "valid_story"))


def asp_verify() -> int:
    expected = {("bedroom", "nose", "sharing", "foreshadowing")}
    actual = asp_valid_stories()
    if actual != expected:
        print(f"ASP mismatch: expected {sorted(expected)}, got {sorted(actual)}")
        return 1
    sample = generate(
        StoryParams(
            child="Nora",
            friend="Milo",
            moon="the sleepy moon",
            treat="a warm mooncake",
            sharing="half",
            foreshadowing="peppermint",
            ending="dreamboat",
        )
    )
    if not sample.story or "nose" not in sample.story.lower():
        print("Generated story verification failed.")
        return 1
    print("OK: ASP parity and generated story checks passed.")
    return 0


CURATED = [
    StoryParams("Nora", "Milo", "the sleepy moon", "a warm mooncake", "half", "peppermint", "dreamboat"),
    StoryParams("Lumi", "Pip", "the silver moon", "a honey biscuit", "welcome", "rain", "window"),
    StoryParams("Tessa", "Oren", "the round moon", "a cinnamon bun", "last_bite", "cinnamon", "blanket"),
    StoryParams("Mina", "Sol", "the little moon", "a lantern-shaped cookie", "lantern", "tickle", "star"),
]


def emit(sample: StorySample, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world is not None:
        print(dump_trace(sample.world))
    if qa:
        print()
        for index, prompt in enumerate(sample.prompts, 1):
            print(f"[Prompt {index}] {prompt}")
        for item in sample.story_qa + sample.world_qa:
            print()
            print(show_qa_item(item))


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program())
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        print("Compatible story shapes:")
        for item in sorted(asp.atoms(asp.one_model(asp_program()), "valid_story")):
            print(" ", item)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    if args.all:
        samples = [generate(params) for params in CURATED]
    else:
        samples = []
        seen: set[str] = set()
        for index in range(max(args.n, 1) * 30):
            if len(samples) >= max(args.n, 1):
                break
            try:
                params = resolve_params(args, random.Random(base_seed + index))
            except StoryError as error:
                print(error)
                return
            params.seed = base_seed + index
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
            header=f"### bedtime variant {index + 1}" if len(samples) > 1 else "",
        )
        if index < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()

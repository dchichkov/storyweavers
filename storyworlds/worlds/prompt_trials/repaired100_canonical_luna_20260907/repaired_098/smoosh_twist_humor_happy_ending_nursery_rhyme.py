#!/usr/bin/env python3
"""A tiny nursery-rhyme world about a smoosh, a twist, and a happy ending."""

from __future__ import annotations

# Locate the shared StoryWorld helpers from any batch depth.
from pathlib import Path as _StoryPath
import sys as _StorySys
_storyworlds_root = next(parent for parent in _StoryPath(__file__).resolve().parents
                        if (parent / 'results.py').is_file() and (parent / 'asp.py').is_file())
_StorySys.path.insert(0, str(_storyworlds_root.parent))
_StorySys.path.insert(0, str(_storyworlds_root))


import argparse
import hashlib
import json
import random
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from results import QAItem, StoryError, StorySample  # noqa: E402


@dataclass
class Character:
    name: str
    kind: str
    role: str
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)


@dataclass
class Place:
    name: str
    kind: str
    meters: dict[str, float] = field(default_factory=dict)


@dataclass
class Treat:
    name: str
    shape: str
    owner: str
    smooshed: bool = False
    rescued: bool = False


@dataclass
class World:
    meadow: Place
    luna: Character
    helper: Character
    treat: Treat
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


@dataclass(frozen=True)
class SmooshCase:
    object_name: str
    cause: str
    first_guess: str
    twist: str
    helper_action: str
    repair: str
    joke: str
    ending: str
    lesson: str


@dataclass
class StoryParams:
    seed: Optional[int] = None
    meadow_name: str = "the Dimpled Meadow"
    luna_name: str = "Luna"
    luna_kind: str = "rabbit"
    helper_name: str = "Toby"
    helper_kind: str = "turtle"
    treat_name: str = "the moon-cake"
    treat_shape: str = "a star"
    case: str = "cake"
    route: str = "moon"


MEADOWS = {
    "the Dimpled Meadow": Place("the Dimpled Meadow", "meadow"),
    "the Button Meadow": Place("the Button Meadow", "meadow"),
    "the Wiggly Meadow": Place("the Wiggly Meadow", "meadow"),
}

LUNAS = [
    ("Luna", "rabbit"),
    ("Lulu", "mouse"),
    ("Nell", "hedgehog"),
]

HELPERS = [
    ("Toby", "turtle"),
    ("Pip", "duck"),
    ("Marnie", "goat"),
]

CASES = {
    "cake": SmooshCase(
        "the moon-cake",
        "a round moon-cake was waiting for Luna's birthday tea",
        "the cake had been squashed by a hungry bear",
        "the bear was only a round blue balloon rolling under the table",
        "held the tray steady while Luna followed the crumbs backward",
        "lifted the cake with two spoons and tucked it into a clean star mold",
        "the cake looked so flat that a ladybug asked whether it needed a pillow",
        "the moon-cake shone like a star while everyone ate tiny triangle pieces",
        "a funny-looking problem can have a gentle cause, so look closely before blaming anyone",
    ),
    "hat": SmooshCase(
        "the mayor's hat",
        "a tall hat was needed for the meadow's afternoon parade",
        "a goat had sat on it while practicing a marching song",
        "the goat had been innocent; a sleepy breeze had folded the hat beneath a picnic blanket",
        "pulled the blanket back while Toby blocked the breeze with his shell",
        "puffed the hat with warm air and pinned its ribbon straight",
        "the hat sprang up and landed on the mayor's nose like a teacup",
        "the parade began with the hat bobbing proudly above a row of giggling friends",
        "patience and a small repair can restore something that first looks ruined",
    ),
    "drum": SmooshCase(
        "the pudding drum",
        "a pudding-filled drum was meant to make a cheerful parade beat",
        "a giant had thumped it too hard",
        "no giant had touched it; a pudding spoon had slipped inside and made the drum bulge",
        "tilted the drum gently while Luna listened for the spoon",
        "removed the spoon and added a wooden rim around the pudding bowl",
        "the drum said plop instead of boom, which made the marching ants dance backward",
        "the pudding drum kept a soft plop beat as the parade twirled home",
        "a careful listener can find a surprising cause without making a bigger mess",
    ),
    "ribbon": SmooshCase(
        "the rainbow ribbon",
        "a long ribbon was needed to decorate the wishing tree",
        "a fox had tangled it into a knotty nest",
        "the fox had not touched it; the ribbon had wrapped around a sleepy kite tail",
        "asked the kite to hold still while Toby loosened one loop at a time",
        "smoothed the ribbon and tied it in three bright bows",
        "the kite sneezed, and every bow bounced onto Luna's ears",
        "the wishing tree wore three bows while the kite sailed in a careful circle",
        "untangling slowly can solve a knot that hurrying would tighten",
    ),
}

ROUTES = ("moon", "riddle", "dialogue", "parade", "backward")

ASP_RULES = r"""
smoosh(C) :- treat(C), compressed(C).
twist(C) :- smoosh(C), surprising_cause(C).
happy_ending(C) :- twist(C), repaired(C), shared(C).
valid_story(C) :- treat(C), smoosh(C), twist(C), happy_ending(C).
"""


def case_id(value: str) -> str:
    return "".join(ch if ch.isalnum() else "_" for ch in value.lower()).strip("_")


def asp_facts() -> str:
    import asp

    lines = []
    for key, case in CASES.items():
        cid = case_id(key)
        lines.extend(
            [
                asp.fact("treat", cid),
                asp.fact("compressed", cid),
                asp.fact("surprising_cause", cid),
                asp.fact("repaired", cid),
                asp.fact("shared", cid),
            ]
        )
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp

    model = asp.one_model(asp_program("#show happy_ending/1."))
    actual = set(asp.atoms(model, "happy_ending"))
    expected = {(case_id(key),) for key in CASES}
    if actual == expected:
        print(f"OK: clingo gate matches python reasoning ({len(expected)} cases).")
        return 0
    print("MISMATCH between clingo and python reasoning.")
    print("clingo:", sorted(actual))
    print("python:", sorted(expected))
    return 1


def story_rng(params: StoryParams) -> random.Random:
    text = "|".join(
        str(value)
        for value in (
            params.seed,
            params.meadow_name,
            params.luna_name,
            params.luna_kind,
            params.helper_name,
            params.helper_kind,
            params.treat_name,
            params.treat_shape,
            params.case,
            params.route,
        )
    )
    digest = hashlib.sha256(text.encode("utf-8")).digest()
    return random.Random(int.from_bytes(digest[:8], "big"))


def build_world(params: StoryParams) -> World:
    if params.meadow_name not in MEADOWS:
        raise StoryError(f"Unknown meadow: {params.meadow_name}")
    if params.case not in CASES:
        raise StoryError(f"Unknown smoosh case: {params.case}")
    if not params.luna_name.strip() or not params.helper_name.strip():
        raise StoryError("Character names must not be empty.")
    meadow = MEADOWS[params.meadow_name]
    return World(
        meadow=Place(meadow.name, meadow.kind),
        luna=Character(params.luna_name, params.luna_kind, "little investigator"),
        helper=Character(params.helper_name, params.helper_kind, "patient helper"),
        treat=Treat(params.treat_name, params.treat_shape, params.luna_name),
    )


def tell_story(world: World, params: StoryParams) -> None:
    rng = story_rng(params)
    luna = world.luna
    helper = world.helper
    treat = world.treat
    case = CASES[params.case]
    meadow = world.meadow

    luna.memes.update(curiosity=1, courage=0)
    helper.memes.update(patience=1, cheer=1)

    openings = {
        "moon": (
            f"By the pale little moon in {meadow.name}, {luna.name} found {treat.name} "
            f"looking less like {treat.shape} and more like a sleepy pancake."
        ),
        "riddle": (
            f"What is flat, funny, and meant for tea? In {meadow.name}, {luna.name} "
            f"asked this riddle when {case.object_name} was smooshed."
        ),
        "dialogue": (
            f'"Oh dear, oh my!" cried {luna.name} in {meadow.name}. '
            f'"Who gave {case.object_name} such a smoosh?"'
        ),
        "parade": (
            f"Before the meadow parade, {luna.name} carried {case.object_name} "
            f"through {meadow.name}; but a bump made it smoosh with a flop and a thump."
        ),
        "backward": (
            f"At the happy end, {case.ending}. But first, in {meadow.name}, "
            f"{luna.name} had to solve the smoosh of {case.object_name}."
        ),
    }
    world.say(openings[params.route])
    world.say(
        rng.choice(
            [
                f"The trouble mattered because {case.cause}.",
                f"Everyone cared, for {case.cause}.",
                f"A tiny frown grew large because {case.cause}.",
            ]
        )
    )
    world.say(
        f'"Do not pout at the smoosh," said {helper.name} the {helper.kind}. '
        f'"Let us look before we blame."'
    )
    world.say(
        f'"Aha!" said {luna.name}. "A twist may be hiding under this funny shape."'
    )

    world.para()
    world.say(f"First, {luna.name} guessed that {case.first_guess}.")
    world.say(
        rng.choice(
            [
                f"But the crumbs and bent grass disagreed: {case.twist}.",
                f"Then a wobbly clue showed the twist: {case.twist}.",
                f"Just then, the truth did a cartwheel: {case.twist}.",
            ]
        )
    )
    world.say(
        f'"There is the twist!" cried {helper.name}. '
        f'"{case.twist.capitalize()}."'
    )
    world.say(f"Together they discovered that {case.cause}.")

    world.para()
    world.say(
        f"{luna.name} stood brave and {helper.name} {case.helper_action}."
    )
    luna.memes["courage"] = 1
    luna.meters["safe_steps"] = 2
    world.say(
        rng.choice(
            [
                f"Then they {case.repair}.",
                f"With a gentle lift, they {case.repair}.",
                f"One careful, merry minute later, they {case.repair}.",
            ]
        )
    )
    treat.smooshed = True
    treat.rescued = True
    world.meters = {"problem_seen": 1, "problem_repaired": 1}
    world.facts.update(
        case=case,
        cause=case.cause,
        twist=case.twist,
        repair=case.repair,
        lesson=case.lesson,
        ending=case.ending,
        joke=case.joke,
        solved=True,
    )

    world.para()
    world.say(
        f"Then came the humor: {case.joke.capitalize()}! "
        f"Even the grumpiest beetle giggled."
    )
    world.say(
        f'"What did we learn?" asked {helper.name}. '
        f'{luna.name} answered, "{case.lesson.capitalize()}."'
    )
    world.say(
        rng.choice(
            [
                f"With a hop and a clap, {case.ending.capitalize()}.",
                f"And so, with everyone singing, {case.ending.capitalize()}.",
                f"At last the meadow rang with rhyme: {case.ending.capitalize()}.",
            ]
        )
    )


def generation_prompts(world: World) -> list[str]:
    case = world.facts["case"]
    return [
        f"Write a nursery rhyme about {world.luna.name} finding a smooshed {world.treat.name}.",
        f"Include this twist: {case.twist}.",
        f"End happily after the characters {case.repair}.",
    ]


def story_qa(world: World) -> list[QAItem]:
    case = world.facts["case"]
    luna = world.luna
    helper = world.helper
    return [
        QAItem(
            question=f"What was smooshed in {world.meadow.name}?",
            answer=f"{case.object_name} was smooshed while {luna.name} was preparing for the meadow's special event.",
        ),
        QAItem(
            question=f"What was the twist in {luna.name}'s mystery?",
            answer=f"The twist was that {case.twist}. This explained the funny shape without blaming the wrong creature.",
        ),
        QAItem(
            question=f"How did {luna.name} and {helper.name} fix the problem?",
            answer=f"{luna.name} and {helper.name} {case.helper_action}, and then they {case.repair}.",
        ),
        QAItem(
            question="Where did the humor appear?",
            answer=f"The humor appeared when {case.joke}. It helped everyone laugh after the worry was understood.",
        ),
        QAItem(
            question="How did the story end happily?",
            answer=f"It ended happily because {case.ending}. The repaired object could be enjoyed by everyone.",
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does smoosh mean?",
            answer="Smoosh means to press or squash something so it becomes flatter or softer.",
        ),
        QAItem(
            question="What is a twist in a story?",
            answer="A twist is a surprising change that reveals a different explanation than the first guess.",
        ),
        QAItem(
            question="Why can humor help during a problem?",
            answer="Humor can make people feel less worried while they carefully work out what happened.",
        ),
        QAItem(
            question="What makes an ending happy?",
            answer="A happy ending shows that the problem has been safely solved and the characters can share joy.",
        ),
        QAItem(
            question="Why should a character look for evidence before blaming someone?",
            answer="Evidence helps the character find the real cause and treat other characters fairly.",
        ),
    ]


def generate(params: StoryParams) -> StorySample:
    world = build_world(params)
    tell_story(world, params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_qa(world),
        world=world,
    )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Nursery-rhyme storyworld about a smoosh, a twist, and a happy ending."
    )
    parser.add_argument("-n", type=int, default=1)
    parser.add_argument("--all", action="store_true")
    parser.add_argument("--seed", type=int, default=None)
    parser.add_argument("--trace", action="store_true")
    parser.add_argument("--qa", action="store_true")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--asp", action="store_true")
    parser.add_argument("--verify", action="store_true")
    parser.add_argument("--show-asp", action="store_true")
    parser.add_argument("--meadow", choices=sorted(MEADOWS))
    parser.add_argument("--luna-name")
    parser.add_argument("--helper-name")
    parser.add_argument("--case", choices=sorted(CASES))
    return parser


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    meadow_name = args.meadow or rng.choice(sorted(MEADOWS))
    luna_name, luna_kind = rng.choice(LUNAS)
    helper_name, helper_kind = rng.choice(HELPERS)
    case_key = args.case or rng.choice(sorted(CASES))
    case = CASES[case_key]
    return StoryParams(
        seed=args.seed,
        meadow_name=meadow_name,
        luna_name=args.luna_name or luna_name,
        luna_kind=luna_kind,
        helper_name=args.helper_name or helper_name,
        helper_kind=helper_kind,
        treat_name=case.object_name,
        treat_shape="a star",
        case=case_key,
        route=rng.choice(ROUTES),
    )


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for character in (world.luna, world.helper):
        lines.append(
            f"{character.name}: meters={character.meters} memes={character.memes}"
        )
    lines.append(
        f"{world.treat.name}: shape={world.treat.shape!r} "
        f"smooshed={world.treat.smooshed} rescued={world.treat.rescued}"
    )
    lines.append(f"meadow: {world.meadow.name!r} meters={world.meadow.meters}")
    lines.append(
        f"resolution: solved={world.facts.get('solved')} "
        f"twist={world.facts.get('twist')!r}"
    )
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
        print("\n== prompts ==")
        for index, prompt in enumerate(sample.prompts, 1):
            print(f"{index}. {prompt}")
        print("\n== story qa ==")
        for item in sample.story_qa:
            print(f"Q: {item.question}\nA: {item.answer}")
        print("\n== world qa ==")
        for item in sample.world_qa:
            print(f"Q: {item.question}\nA: {item.answer}")


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show happy_ending/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp

        model = asp.one_model(asp_program("#show happy_ending/1."))
        print(sorted(set(asp.atoms(model, "happy_ending"))))
        return

    if args.n < 1:
        raise StoryError("-n must be at least 1.")

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    count = 4 if args.all else args.n
    samples = []
    for index in range(count):
        params = resolve_params(args, random.Random(base_seed + index))
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

#!/usr/bin/env python3
"""A gentle bedtime storyworld about a snack hung in haste and checked with care."""

from __future__ import annotations

import argparse
import hashlib
import json
import random
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

ROOT = next((p for p in Path(__file__).resolve().parents if (p / "results.py").is_file()), None)
if ROOT is None:
    raise RuntimeError("Could not find storyworlds/results.py")
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
from results import QAItem, StoryError, StorySample  # noqa: E402


@dataclass
class Creature:
    name: str
    species: str
    role: str
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)


@dataclass
class Place:
    name: str
    description: str
    ending_image: str
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)


@dataclass
class Snack:
    name: str
    kind: str
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)


@dataclass
class HangingPoint:
    name: str
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)


@dataclass(frozen=True)
class BedtimeCase:
    clue: str
    first_test: str
    failed_reason: str
    decisive_clue: str
    cause: str
    repair: str
    initial_hang: str
    sound: str
    ending_image: str
    safe_resolution: bool = True


@dataclass
class StoryParams:
    seed: Optional[int] = None
    child_name: str = "Willa"
    helper_name: str = "Aunt Bramble"
    room: str = "willow_cottage"
    case: str = "loose_peg"
    route: str = "moonrise"


@dataclass
class World:
    room: Place
    child: Creature
    helper: Creature
    snack: Snack
    hanging_point: HangingPoint
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    facts: dict = field(default_factory=dict)

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(part) for part in self.paragraphs if part)


ROOMS = {
    "willow_cottage": Place(
        name="Willow Cottage",
        description="a round window looked out on the sleeping willows",
        ending_image="the willow leaves beyond the round window settled into stillness",
    ),
    "fern_burrow": Place(
        name="Fern Burrow",
        description="fern fronds brushed softly past the little door",
        ending_image="the fern fronds by the burrow door stopped swaying",
    ),
    "bluebell_loft": Place(
        name="Bluebell Loft",
        description="bluebell shadows rested beneath the small window",
        ending_image="bluebell shadows lay still beneath the loft window",
    ),
}

CASES = {
    "loose_peg": BedtimeCase(
        clue="a thin crack circled the peg where it met the wall",
        first_test="set the snack safely in a wooden bowl and pressed the empty peg with one finger",
        failed_reason="the peg rocked even with no weight on it",
        decisive_clue="a thin crack circled the peg where it met the wall",
        cause="the old peg had loosened in the wall, so even a light snack pouch could slip",
        repair="Aunt Bramble fixed a broad, low hook into the solid doorframe; then Willa hung the pouch there and gave it three gentle tugs",
        initial_hang="hooked it onto the old wall peg",
        sound="creak",
        ending_image="the cracked peg stood empty beside the sturdy new doorframe hook",
    ),
    "swinging_loop": BedtimeCase(
        clue="the long ribbon reached past the peg and curled against the curtain",
        first_test="closed the window and watched the empty ribbon loop",
        failed_reason="the loop still brushed the curtain with the window shut",
        decisive_clue="the long ribbon reached past the peg and curled against the curtain",
        cause="the ribbon loop was too long, and the curtain caught it whenever the pouch swayed",
        repair="Willa shortened the loop with a secure double knot, and Aunt Bramble checked it before Willa rehung the pouch and gave it three gentle tugs",
        initial_hang="let its long ribbon loop dangle from the low peg",
        sound="rustle",
        ending_image="the short ribbon loop hung clear of the curtain",
    ),
    "slipping_knot": BedtimeCase(
        clue="the ribbon tail slid through the hurried single knot each time the pouch lifted",
        first_test="held the pouch safely in a bowl and pressed the peg",
        failed_reason="the peg stayed firm, so a loose peg was not the trouble",
        decisive_clue="the ribbon tail slid through the hurried single knot each time the pouch lifted",
        cause="Willa had tied one loose knot in her haste, and the ribbon kept slipping free",
        repair="Aunt Bramble showed Willa a snug double knot; Willa retied the loop and gave it three gentle tugs",
        initial_hang="tied one quick knot around the low peg",
        sound="tick",
        ending_image="the neat double knot held the snack pouch safely in place",
    ),
}

ROUTES = ("moonrise", "question", "last_lamp")
REFRAIN = "Hang it low, tug it slow."
NAME_RE = re.compile(r"^[A-Za-z][A-Za-z '-]{0,31}$")


ASP_RULES = r"""
resolved(C) :- case(C), has_clue(C), has_repair(C), repeated_safe_test(C).
"""


def validate_name(name: str, field_name: str) -> str:
    cleaned = name.strip()
    if not NAME_RE.fullmatch(cleaned):
        raise StoryError(
            f"Invalid {field_name}: use a short name containing letters, spaces, apostrophes, or hyphens."
        )
    return cleaned


def python_reasonable_case(case_id: str) -> bool:
    case = CASES.get(case_id)
    return bool(
        case
        and case.safe_resolution
        and case.clue
        and case.first_test
        and case.failed_reason
        and case.decisive_clue
        and case.cause
        and case.repair
        and case.ending_image
    )


def build_world(params: StoryParams) -> World:
    if params.room not in ROOMS:
        raise StoryError(f"Unknown room: {params.room}. Choose from {', '.join(sorted(ROOMS))}.")
    if params.case not in CASES:
        raise StoryError(f"Unknown bedtime snag: {params.case}. Choose from {', '.join(sorted(CASES))}.")
    if params.route not in ROUTES:
        raise StoryError(f"Unknown story route: {params.route}. Choose from {', '.join(ROUTES)}.")
    if not python_reasonable_case(params.case):
        raise StoryError(f"The bedtime snag {params.case!r} has no safe, complete resolution.")

    child_name = validate_name(params.child_name, "child name")
    helper_name = validate_name(params.helper_name, "helper name")
    if child_name.casefold() == helper_name.casefold():
        raise StoryError("The child and helper need different names.")

    room_template = ROOMS[params.room]
    room = Place(
        name=room_template.name,
        description=room_template.description,
        ending_image=room_template.ending_image,
        meters={"quiet": 0.72, "darkness": 0.55},
        memes={"coziness": 0.8},
    )
    child = Creature(
        name=child_name,
        species="field mouse",
        role="bedtime snack helper",
        meters={"sleepiness": 0.72, "careful_checks": 0},
        memes={"haste": 0.85, "worry": 0.45, "calm": 0.1},
    )
    helper = Creature(
        name=helper_name,
        species="field mouse",
        role="patient grown-up",
        meters={"safe_checks": 0},
        memes={"patience": 1.0, "warmth": 0.9},
    )
    snack = Snack(
        name="apple-and-oat snack pouch",
        kind="tomorrow's dawn-walk snack",
        meters={"hung": 0, "secure": 0, "caught_over_bowl": 0},
        memes={"comfort": 0.7},
    )
    hanging_point = HangingPoint(
        name="low peg beside the door",
        meters={
            "peg_stability": 0.25 if params.case == "loose_peg" else 0.95,
            "loop_clearance": 0.25 if params.case == "swinging_loop" else 0.95,
            "knot_hold": 0.2 if params.case == "slipping_knot" else 0.95,
            "tested": 0,
        },
        memes={"trust": 0.2},
    )
    return World(
        room=room,
        child=child,
        helper=helper,
        snack=snack,
        hanging_point=hanging_point,
    )


def story_rng(params: StoryParams) -> random.Random:
    text = "|".join(
        str(value)
        for value in (
            params.seed,
            params.child_name,
            params.helper_name,
            params.room,
            params.case,
            params.route,
        )
    )
    digest = hashlib.sha256(text.encode("utf-8")).digest()
    return random.Random(int.from_bytes(digest[:8], "big"))


def tell_story(world: World, params: StoryParams) -> None:
    child, helper, room, snack, point = (
        world.child,
        world.helper,
        world.room,
        world.snack,
        world.hanging_point,
    )
    case = CASES[params.case]
    rng = story_rng(params)

    openings = {
        "moonrise": (
            f"Moonlight folded itself over {room.name}, where {room.description}. "
            f"At bedtime, {child.name} the little field mouse packed an apple-and-oat snack "
            "for tomorrow's dawn walk."
        ),
        "question": (
            f'"Will our snack be ready for the dawn walk?" {child.name} asked in {room.name}, '
            f"where {room.description}. The last bedtime lamp glowed beside the little field mouse."
        ),
        "last_lamp": (
            f"The last lamp in {room.name} was growing dim, and {room.description}. "
            f"{child.name}, a sleepy little field mouse, still had one bedtime job: prepare "
            "an apple-and-oat snack for tomorrow's dawn walk."
        ),
    }
    world.say(openings[params.route])
    world.say(
        f"Sleepiness tugged at {child.name}, and in her haste she {case.initial_hang}. "
        f"The pouch made a tiny {case.sound} and began to sway."
    )
    snack.meters["hung"] = 1
    point.memes["trust"] = 0.2

    world.para()
    world.say(
        f'"That sound means I should not hurry," {child.name} said. '
        f'"Let us listen before the snack slips," {helper.name} replied.'
    )
    world.say(
        f'{child.name} lowered the pouch into a wooden bowl so it could not fall. '
        f'"What is our little rule?" asked {helper.name}. Together they whispered, '
        f'"{REFRAIN}"'
    )
    world.say(
        rng.choice(
            [
                f'{child.name} repeated, "{REFRAIN}" and began the check again, slowly.',
                f'"{REFRAIN}" {child.name} whispered once more, then watched the peg instead of rushing.',
                f'{child.name} took one quiet breath. "{REFRAIN}" she said, ready to test what had happened.',
            ]
        )
    )
    snack.meters["hung"] = 0
    snack.meters["caught_over_bowl"] = 1

    world.para()
    world.say(f"First, {child.name} {case.first_test}.")
    world.say(
        rng.choice(
            [
                f"The first guess did not fit: {case.failed_reason}.",
                f"They learned something by testing gently: {case.failed_reason}.",
                f'"That is not what I expected," said {child.name}, because {case.failed_reason}.',
            ]
        )
    )
    world.say(
        rng.choice(
            [
                f"Then they found the clue that mattered: {case.decisive_clue}.",
                f'{helper.name} pointed without touching. {case.decisive_clue.capitalize()}.',
                f"By looking closely instead of guessing, they noticed that {case.decisive_clue}.",
            ]
        )
    )
    world.say(f"Now the little mystery made sense: {case.cause}.")

    world.para()
    world.say(
        f'"I was in such a hurry that I nearly missed it," {child.name} said. '
        f'"Now we know what to do," {helper.name} answered, and they worked together.'
    )
    world.say(f"{case.repair}.")
    snack.meters["hung"] = 1
    snack.meters["secure"] = 1
    point.meters["tested"] = 3
    point.memes["trust"] = 1.0
    child.meters["careful_checks"] = 3
    child.memes.update(haste=0.15, worry=0.1, calm=0.95)
    helper.meters["safe_checks"] = 1
    helper.memes["pride"] = 1.0
    room.meters["quiet"] = 1.0
    room.memes["coziness"] = 1.0

    world.say(
        f'Together they breathed their rule once more: "{REFRAIN}" '
        f"The pouch hung safely above its wooden bowl, and {case.ending_image}. "
        f"At last, {room.ending_image}. The sleepy mice curled up as the house grew quiet."
    )

    world.facts.update(
        case=case,
        case_id=params.case,
        cause=case.cause,
        repair=case.repair,
        clue=case.decisive_clue,
        solved=True,
        refrain=REFRAIN,
        safe_repeated_test=True,
    )


def generation_prompts(world: World) -> list[str]:
    facts = world.facts
    case = facts["case"]
    return [
        f"Tell a cozy bedtime story about {world.child.name} preparing a snack in {world.room.name}.",
        f"Show how {world.child.name} discovers that {case.cause} by listening and testing carefully.",
        f"Include the repeated bedtime rule, “{REFRAIN}” End with a quiet image of the safely hung snack.",
    ]


def story_qa(world: World) -> list[QAItem]:
    child, helper = world.child, world.helper
    case = world.facts["case"]
    return [
        QAItem(
            question=f"What was {child.name} preparing before bedtime?",
            answer=(
                f"{child.name} was preparing an apple-and-oat snack pouch for tomorrow's dawn walk. "
                "She wanted it ready before she went to sleep."
            ),
        ),
        QAItem(
            question=f"Why did the snack pouch make a sound when {child.name} hung it?",
            answer=(
                f"{case.cause.capitalize()}. The little sound warned {child.name} and {helper.name} "
                "to pause and check the hanging place before trusting it."
            ),
        ),
        QAItem(
            question=f"What did {child.name} and {helper.name} learn from their first test?",
            answer=(
                f"They learned that {case.failed_reason}. That result ruled out their first guess "
                "and helped them look for a more useful clue."
            ),
        ),
        QAItem(
            question=f"What clue helped them understand the bedtime snag?",
            answer=(
                f"They noticed that {case.decisive_clue}. That clue showed them that {case.cause}."
            ),
        ),
        QAItem(
            question=f"How did they make the snack safe to leave for morning?",
            answer=(
                f"{case.repair}. They repeated a gentle three-tug check so they could see that "
                "the pouch was secure before settling down."
            ),
        ),
        QAItem(
            question=f"What repeated rule helped {child.name} slow down?",
            answer=(
                f"{child.name} repeated, “{REFRAIN}” The rhyme reminded her to hang the snack "
                "carefully and test it instead of acting in haste."
            ),
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="Why can haste make a small job harder?",
            answer=(
                "Haste can make someone skip a useful check. Taking a quiet moment to look and test "
                "can prevent a small problem from becoming a bigger one."
            ),
        ),
        QAItem(
            question="Why is it useful to repeat a safety check?",
            answer=(
                "Repeating a simple check can help someone notice whether a hook, knot, or other "
                "support is steady before placing something on it."
            ),
        ),
        QAItem(
            question="What is a bedtime snack pouch?",
            answer=(
                "It is a small bag that can hold a snack. In this story, the pouch held food prepared "
                "for a walk the next morning."
            ),
        ),
        QAItem(
            question="Why should a heavy or loose hook be handled by a grown-up?",
            answer=(
                "A grown-up can choose a sturdy place and use the right tools safely. A child can "
                "help by watching from a safe spot and checking the finished result gently."
            ),
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


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for case_id, case in sorted(CASES.items()):
        if python_reasonable_case(case_id):
            lines.extend(
                (
                    asp.fact("case", case_id),
                    asp.fact("has_clue", case_id),
                    asp.fact("has_repair", case_id),
                    asp.fact("repeated_safe_test", case_id),
                )
            )
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp

    model = asp.one_model(asp_program("#show resolved/1."))
    asp_resolved = set(asp.atoms(model, "resolved"))
    py_resolved = {
        (case_id,) for case_id in CASES if python_reasonable_case(case_id)
    }
    if asp_resolved != py_resolved:
        print("MISMATCH between clingo and Python bedtime reasoning.")
        print("clingo:", sorted(asp_resolved))
        print("python:", sorted(py_resolved))
        return 1

    for index, case_id in enumerate(CASES):
        sample = generate(
            StoryParams(seed=9100 + index, case=case_id, route=ROUTES[index % len(ROUTES)])
        )
        if not sample.world or not sample.world.facts.get("solved"):
            print(f"FAILED: generated story did not resolve {case_id}.")
            return 1
        if sample.story.count(REFRAIN) < 3:
            print(f"FAILED: repeated bedtime rule is missing from {case_id}.")
            return 1
        if not any('"' in sentence for paragraph in sample.story.split("\n\n") for sentence in paragraph.split(". ")):
            print(f"FAILED: generated story has no spoken dialogue for {case_id}.")
            return 1
        if any(marker in sample.story for marker in ("{case}", "None", "TODO", "case_id")):
            print(f"FAILED: generated story leaked a scaffold for {case_id}.")
            return 1

    print(f"OK: clingo matches Python reasoning and all {len(CASES)} bedtime stories pass.")
    return 0


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for entity in (world.room, world.child, world.helper, world.snack, world.hanging_point):
        lines.append(
            f"{entity.name}: meters={entity.meters} memes={getattr(entity, 'memes', {})}"
        )
    lines.append(
        f"bedtime snag: clue={world.facts['clue']!r} "
        f"cause={world.facts['cause']!r} solved={world.facts['solved']}"
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


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="A cozy bedtime story about a snack hung in haste and checked with care."
    )
    parser.add_argument("--seed", type=int, default=None)
    parser.add_argument("-n", type=int, default=1)
    parser.add_argument("--all", action="store_true")
    parser.add_argument("--trace", action="store_true")
    parser.add_argument("--qa", action="store_true")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--asp", action="store_true")
    parser.add_argument("--verify", action="store_true")
    parser.add_argument("--show-asp", action="store_true")
    parser.add_argument("--room", choices=sorted(ROOMS))
    parser.add_argument("--case", choices=sorted(CASES))
    parser.add_argument("--route", choices=ROUTES)
    parser.add_argument("--child-name")
    parser.add_argument("--helper-name")
    return parser


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    return StoryParams(
        seed=args.seed,
        child_name=args.child_name or "Willa",
        helper_name=args.helper_name or "Aunt Bramble",
        room=args.room or rng.choice(sorted(ROOMS)),
        case=args.case or rng.choice(sorted(CASES)),
        route=args.route or rng.choice(ROUTES),
    )


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()

    if args.show_asp:
        print(asp_program("#show resolved/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp

        model = asp.one_model(asp_program("#show resolved/1."))
        print(sorted(set(asp.atoms(model, "resolved"))))
        return
    if args.n < 1:
        parser.error("-n must be at least 1")

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    count = len(CASES) if args.all else args.n
    samples: list[StorySample] = []
    for index in range(count):
        rng = random.Random(base_seed + index)
        params = resolve_params(args, rng)
        if args.all:
            params.case = list(CASES)[index]
        params.seed = base_seed + index
        samples.append(generate(params))

    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([sample.to_dict() for sample in samples], indent=2, ensure_ascii=False))
        return

    for index, sample in enumerate(samples):
        header = f"### bedtime variation {index + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if index < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()

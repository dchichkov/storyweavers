#!/usr/bin/env python3
"""A gentle bedtime storyworld about a snack, a hasty knot, and a hanging pouch."""

from __future__ import annotations

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
    species: str
    role: str
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)


@dataclass
class Place:
    name: str
    kind: str
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)


@dataclass
class Snack:
    name: str
    kind: str
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)


@dataclass
class Peg:
    name: str
    kind: str = "wooden peg"
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)


@dataclass(frozen=True)
class KnotCase:
    trouble: str
    worry: str
    first_check: str
    first_result: str
    clue: str
    cause: str
    safe_action: str
    repair: str
    ending: str
    fix: str


@dataclass
class StoryParams:
    seed: Optional[int] = None
    setting: str = "the little pine room"
    lead_name: str = "Luna"
    lead_species: str = "mouse"
    helper_name: str = "Pip"
    helper_species: str = "dormouse"
    snack: str = "apple bites"
    case: str = "loose_knot"
    route: str = "moon_first"


@dataclass
class World:
    room: Place
    lead: Character
    helper: Character
    snack: Snack
    peg: Peg
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


CASES = {
    "loose_knot": KnotCase(
        trouble="the snack pouch slipped down and began to sway",
        worry="the apple bites might tumble onto the floor",
        first_check="looked closely at the knot without pulling the pouch",
        first_result="the knot looked snug at first, but its smooth tail kept sliding",
        clue="the little loop had no tucked end to hold it in place",
        cause="a single smooth loop was slipping along the rounded wooden peg",
        safe_action="held the pouch still while Pip set a small bowl beneath it",
        repair="they emptied the pouch, tied a double loop with its end tucked in, and tested it with a wooden button",
        ending="the pouch rested quietly on the peg, and the apple bites waited safely inside",
        fix="a double loop with its end tucked in held the pouch securely",
    ),
    "tilted_peg": KnotCase(
        trouble="the snack pouch leaned sideways on its peg",
        worry="the pouch could slide off before the snack was put away",
        first_check="checked whether the pouch was too heavy",
        first_result="the pouch was light, yet it still leaned toward the wall",
        clue="the wooden peg rocked a little where it met the wall",
        cause="a loosened peg was tilting under even the small pouch",
        safe_action="lifted the pouch down and asked Pip to call Auntie Fern",
        repair="Auntie Fern secured the peg while the two friends waited, then Luna tested it with an empty pouch",
        ending="the straight peg held the empty pouch steady beneath the quiet moon",
        fix="an adult secured the loose peg before the pouch was hung again",
    ),
    "long_ribbon": KnotCase(
        trouble="the snack pouch swung toward the curtain",
        worry="the moving pouch might brush the snack against the dusty fabric",
        first_check="closed the window to see whether a breeze was moving the pouch",
        first_result="the curtain grew still, but the pouch kept brushing its edge",
        clue="the long ribbon reached all the way to the curtain with each little swing",
        cause="the ribbon was long enough to catch the curtain whenever the pouch moved",
        safe_action="took the pouch down instead of tugging it away from the curtain",
        repair="they folded the ribbon shorter, tied it securely, and checked that the pouch hung clear of the cloth",
        ending="a neat little pouch hung clear of the curtain while the room settled into stillness",
        fix="shortening and securing the ribbon kept the pouch away from the curtain",
    ),
}

SETTINGS = (
    "the little pine room",
    "the blue attic room",
    "the quiet burrow room",
)
SNACKS = (
    "apple bites",
    "oat biscuits",
    "pear pieces",
)
CHARACTERS = (
    ("Luna", "mouse", "Pip", "dormouse"),
    ("Mira", "hare", "Tumble", "dormouse"),
    ("Nell", "squirrel", "Kit", "mouse"),
)
ROUTES = ("moon_first", "snack_first", "quiet_first")
REFRAIN = "One small pause, then one gentle step."


ASP_RULES = r"""
reasonable(C) :- case(C), has_worry(C), has_clue(C), has_fix(C), safe(C), has_ending(C).
#show reasonable/1.
"""


def python_reasonableness_gate(case_id: str) -> bool:
    case = CASES.get(case_id)
    if case is None:
        return False
    return all((
        bool(case.worry),
        bool(case.clue),
        bool(case.fix),
        bool(case.safe_action),
        bool(case.ending),
        case.ending != case.trouble,
    ))


def asp_facts() -> str:
    import asp

    lines = []
    for case_id, case in sorted(CASES.items()):
        lines.extend((
            asp.fact("case", case_id),
            asp.fact("has_worry", case_id),
            asp.fact("has_clue", case_id),
            asp.fact("has_fix", case_id),
            asp.fact("has_ending", case_id),
        ))
        if case.safe_action:
            lines.append(asp.fact("safe", case_id))
    return "\n".join(lines)


def asp_program() -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n"


def asp_verify() -> int:
    import asp

    model = asp.one_model(asp_program())
    asp_cases = {args[0] for args in asp.atoms(model, "reasonable")}
    py_cases = {case_id for case_id in CASES if python_reasonableness_gate(case_id)}
    if asp_cases != py_cases:
        print("MISMATCH between clingo and Python reasonableness gates.")
        print("clingo:", sorted(asp_cases))
        print("python:", sorted(py_cases))
        return 1

    failures = []
    for index, case_id in enumerate(sorted(CASES)):
        params = StoryParams(
            seed=1000 + index,
            case=case_id,
            snack=SNACKS[index % len(SNACKS)],
            route=ROUTES[index % len(ROUTES)],
        )
        sample = generate(params)
        if sample.story.count(REFRAIN) != 3:
            failures.append(f"{case_id}: refrain did not appear exactly three times")
        if "?" not in sample.story or not any(mark in sample.story for mark in ('"', "“")):
            failures.append(f"{case_id}: missing a spoken exchange")
        if not sample.world.facts.get("solved"):
            failures.append(f"{case_id}: story did not resolve its problem")
        if CASES[case_id].ending not in sample.story:
            failures.append(f"{case_id}: ending image missing")
    if failures:
        print("Generated-story verification failed:")
        for failure in failures:
            print("-", failure)
        return 1

    print(f"OK: clingo and Python agree on {len(py_cases)} cases; generated stories passed.")
    return 0


def story_rng(params: StoryParams) -> random.Random:
    values = (
        params.seed, params.setting, params.lead_name, params.lead_species,
        params.helper_name, params.helper_species, params.snack, params.case,
        params.route,
    )
    digest = hashlib.sha256("|".join(str(v) for v in values).encode("utf-8")).digest()
    return random.Random(int.from_bytes(digest[:8], "big"))


def build_world(params: StoryParams) -> World:
    if params.setting not in SETTINGS:
        raise StoryError(f"Unknown bedtime setting: {params.setting}")
    if params.snack not in SNACKS:
        raise StoryError(f"Unknown snack: {params.snack}")
    if params.case not in CASES:
        raise StoryError(f"Unknown hanging-pouch problem: {params.case}")
    if params.route not in ROUTES:
        raise StoryError(f"Unknown story opening: {params.route}")
    if not params.lead_name.strip() or not params.helper_name.strip():
        raise StoryError("Character names must not be empty.")
    if not python_reasonableness_gate(params.case):
        raise StoryError(f"The story problem {params.case!r} has no safe, reasonable resolution.")

    return World(
        room=Place(name=params.setting, kind="bedroom"),
        lead=Character(params.lead_name, params.lead_species, "careful snack keeper"),
        helper=Character(params.helper_name, params.helper_species, "sleepy friend"),
        snack=Snack(params.snack, "bedtime snack", meters={"weight_kg": 0.08}),
        peg=Peg(name="the rounded wooden peg", meters={"height_m": 0.7}),
    )


def tell_story(world: World, params: StoryParams) -> None:
    lead, helper, room, snack, peg = (
        world.lead, world.helper, world.room, world.snack, world.peg
    )
    case = CASES[params.case]
    rng = story_rng(params)

    lead.memes.update(hurried=1.0, worry=0.5, patience=0.0)
    helper.memes.update(kindness=1.0, attentiveness=0.8)
    room.meters["light_level"] = 0.2
    room.memes["calm"] = 0.7
    peg.meters.update(stability=0.5, height_m=0.7)
    snack.meters["secure"] = 0.0

    openings = {
        "moon_first": (
            f"Moonlight made a pale square on {room.name} as {lead.name} prepared "
            f"a little bedtime snack of {snack.name}."
        ),
        "snack_first": (
            f"{lead.name} had just packed {snack.name} into a small cloth pouch "
            f"when bedtime came to {room.name}."
        ),
        "quiet_first": (
            f"The house was growing quiet, and {room.name} smelled faintly of "
            f"{snack.name} as {lead.name} reached for the pouch."
        ),
    }
    world.say(openings[params.route])
    world.say(
        f"Wanting to finish before the last stripe of moonlight moved, {lead.name} "
        f"hastily tried to hang the pouch on {peg.name}. Then {case.trouble}."
    )
    world.say(
        rng.choice((
            f'"Why is it moving?" asked {helper.name}. "I hurried," said {lead.name}. '
            f'"Let us hold it still before anything falls."',
            f'"That pouch is swaying," said {helper.name}. "I tied it too fast," '
            f'{lead.name} replied. "Please help me keep it still while I look."',
        ))
    )
    world.say(f'{lead.name} whispered, "{REFRAIN}"')
    lead.memes["hurried"] = 0.0
    lead.memes["patience"] = 0.5

    world.para()
    world.say(f"Together, they {case.first_check}.")
    world.say(f"That first check did not solve it: {case.first_result}.")
    world.say(f"Then {helper.name} noticed something small: {case.clue}.")
    world.say(f'"Now I know what to check," said {lead.name}. {case.cause.capitalize()}.')
    world.say(f'{helper.name} answered, "Good noticing. We can fix that without rushing."')
    world.say(f'{lead.name} repeated, "{REFRAIN}"')
    world.say(f"First, {lead.name} {case.safe_action}.")
    world.say(f"Then {case.repair}.")
    lead.memes.update(worry=0.0, patience=1.0, confidence=0.8)
    helper.memes["pride"] = 1.0
    snack.meters["secure"] = 1.0
    peg.meters["stability"] = 1.0
    room.memes["calm"] = 1.0

    world.para()
    world.say(
        f"Before they climbed into bed, {helper.name} asked, "
        f'"What will you remember next time?"'
    )
    world.say(
        f'"I can pause, check the little clue, and ask for help," {lead.name} '
        f"said. {lead.name} murmured, “{REFRAIN}”"
    )
    world.say(f"At last, {case.ending}.")
    world.facts.update(
        case_id=params.case,
        case=case,
        cause=case.cause,
        fix=case.fix,
        solved=True,
        repeated_refrain=REFRAIN,
        ending=case.ending,
    )


def generation_prompts(world: World) -> list[str]:
    case = world.facts["case"]
    return [
        f"Write a gentle bedtime story about {world.lead.name} hanging a pouch of {world.snack.name} in {world.room.name}.",
        f"Show how {world.lead.name} and {world.helper.name} discover that {case.cause}.",
        f"Use the repeated line “{REFRAIN}” three times, and end with this image: {case.ending}.",
    ]


def story_qa(world: World) -> list[QAItem]:
    case = world.facts["case"]
    lead, helper = world.lead, world.helper
    return [
        QAItem(
            question=f"What went wrong when {lead.name} tried to hang the snack pouch?",
            answer=f"{case.trouble.capitalize()}. It mattered because {case.worry}.",
        ),
        QAItem(
            question=f"What clue helped {lead.name} and {helper.name} understand the problem?",
            answer=f"{helper.name} noticed that {case.clue}. That showed them that {case.cause}.",
        ),
        QAItem(
            question=f"How did the friends make the pouch safe?",
            answer=f"{lead.name} {case.safe_action}. Then {case.repair.capitalize()}.",
        ),
        QAItem(
            question=f"What did {lead.name} learn before going to bed?",
            answer=(
                f"{lead.name} learned to pause, look for a small clue, and ask for help "
                f"instead of hurrying. That choice led to this peaceful ending: {case.ending}."
            ),
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="Why should a hanging snack pouch be tied securely?",
            answer="A secure knot helps keep the pouch from slipping and spilling its snack.",
        ),
        QAItem(
            question="What can someone do when a small problem feels confusing?",
            answer="They can pause, look carefully for clues, and ask a trusted person for help.",
        ),
        QAItem(
            question="Why is a bedtime story sometimes quiet and repetitive?",
            answer="A gentle repeated line can make a story feel familiar and help its characters settle down.",
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


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    lead_name, lead_species, helper_name, helper_species = rng.choice(CHARACTERS)
    return StoryParams(
        seed=args.seed,
        setting=args.setting or rng.choice(SETTINGS),
        lead_name=args.lead_name or lead_name,
        lead_species=lead_species,
        helper_name=args.helper_name or helper_name,
        helper_species=helper_species,
        snack=args.snack or rng.choice(SNACKS),
        case=args.case or rng.choice(sorted(CASES)),
        route=rng.choice(ROUTES),
    )


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for entity in (world.room, world.lead, world.helper, world.snack, world.peg):
        lines.append(
            f"{entity.name}: meters={entity.meters} memes={entity.memes}"
        )
    lines.append(
        f"problem={world.facts['case_id']} cause={world.facts['cause']!r} "
        f"solved={world.facts['solved']} fix={world.facts['fix']!r}"
    )
    return "\n".join(lines)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="A bedtime story about a snack pouch, haste, and a careful hang."
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
    parser.add_argument("--setting", choices=SETTINGS)
    parser.add_argument("--snack", choices=SNACKS)
    parser.add_argument("--case", choices=sorted(CASES))
    parser.add_argument("--lead-name")
    parser.add_argument("--helper-name")
    return parser


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
        print(asp_program())
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp

        model = asp.one_model(asp_program())
        print(sorted(set(asp.atoms(model, "reasonable"))))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    count = 3 if args.all else args.n
    if count < 1:
        raise StoryError("Please request at least one story with -n.")
    samples = []
    for index in range(count):
        seed = base_seed + index
        params = resolve_params(args, random.Random(seed))
        params.seed = seed
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

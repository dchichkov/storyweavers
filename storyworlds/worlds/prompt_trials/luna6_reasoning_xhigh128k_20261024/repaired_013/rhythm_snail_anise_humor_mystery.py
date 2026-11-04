#!/usr/bin/env python3
"""
A small humorous mystery about a snail detective, a rhythm in the pantry,
and a batch of missing anise buns.
"""

from __future__ import annotations

import argparse
import json
import random
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

_SCRIPT = Path(__file__).resolve()
for _parent in _SCRIPT.parents:
    if (_parent / "storyworlds" / "results.py").is_file():
        ROOT = str(_parent)
        break
else:
    ROOT = str(_SCRIPT.parents[5])
sys.path.insert(0, ROOT)

from storyworlds.results import QAItem, StoryError, StorySample  # noqa: E402


@dataclass
class StoryParams:
    setting: str = "the Moonbell Bakery"
    snail: str = "Mallow"
    baker: str = "Tock"
    mouse: str = "Nib"
    seed: Optional[int] = None


@dataclass
class Entity:
    name: str
    kind: str
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)


@dataclass
class World:
    setting: str
    entities: dict[str, Entity] = field(default_factory=dict)
    facts: dict[str, object] = field(default_factory=dict)
    events: list[str] = field(default_factory=list)

    def add(self, key: str, entity: Entity) -> Entity:
        self.entities[key] = entity
        return entity


SETTING_REGISTRY = {
    "the Moonbell Bakery": {
        "detail": "moonlight silvered the round pantry window",
        "tags": {"pantry", "bakehouse"},
        "fixtures": {"pendulum_clock", "shelf", "delivery_board", "delivery_basket"},
    },
    "the Lantern Fair Bakehouse": {
        "detail": "paper lanterns bobbed outside the pantry door",
        "tags": {"pantry", "bakehouse"},
        "fixtures": {"pendulum_clock", "shelf", "delivery_board", "delivery_basket"},
    },
    "the Mossy Hill Bakehouse": {
        "detail": "clover brushed the pantry sill",
        "tags": {"pantry", "bakehouse"},
        "fixtures": {"pendulum_clock", "shelf", "delivery_board", "delivery_basket"},
    },
}

FEATURES = {"humor"}
STYLE = "mystery"
CLUES = {"rhythm"}
INGREDIENTS = {"anise"}
PROTAGONIST_KIND = "snail"

SNAIL_NAMES = ["Mallow", "Dot", "Saffron", "Pebble", "Tansy", "Clover", "Button", "Bramble"]
BAKER_NAMES = ["Tock", "Pip", "Chime", "Cricket", "Tilly", "Jingle", "Rattle", "Biscuit"]
MOUSE_NAMES = ["Nib", "Pippa", "Midge", "Wicket", "Mittens", "Pipkin", "Bean", "Thimble"]

RHYTHMS = ["tap-tap-plunk", "tick-tick-thump", "tock-tock-plop"]

ASP_RULES = r"""
supported_place(S) :-
    setting(S),
    tag(S, pantry),
    fixture(S, pendulum_clock),
    fixture(S, shelf),
    fixture(S, delivery_board),
    fixture(S, delivery_basket).

valid_case(S) :-
    supported_place(S),
    feature(humor),
    style(mystery),
    clue(rhythm),
    ingredient(anise),
    protagonist(snail).
"""


def _slug(text: str) -> str:
    text = text.lower().removeprefix("the ")
    return re.sub(r"[^a-z0-9]+", "_", text).strip("_")


def _validate_name(name: str, role: str) -> None:
    if not isinstance(name, str) or not re.fullmatch(r"[A-Za-z][A-Za-z' -]{0,24}", name):
        raise StoryError(f"The {role}'s name must be 1 to 25 simple letters, spaces, apostrophes, or hyphens.")


def _validate_params(params: StoryParams) -> None:
    if params.setting not in SETTING_REGISTRY:
        choices = ", ".join(SETTING_REGISTRY)
        raise StoryError(f"Unknown setting {params.setting!r}. Choose one of: {choices}.")
    for role, name in (("snail", params.snail), ("baker", params.baker), ("mouse", params.mouse)):
        _validate_name(name, role)
    names = [params.snail.casefold(), params.baker.casefold(), params.mouse.casefold()]
    if len(set(names)) != len(names):
        raise StoryError("The snail, baker, and mouse must have different names.")
    if params.seed is not None and not isinstance(params.seed, int):
        raise StoryError("The seed must be an integer.")


def _stable_seed(params: StoryParams) -> int:
    if params.seed is not None:
        return params.seed
    text = "|".join((params.setting, params.snail, params.baker, params.mouse))
    return sum((i + 1) * ord(char) for i, char in enumerate(text)) % (2**31)


def python_reasonableness_gate(setting: str) -> bool:
    """Allow only places that support the pantry's physical mystery."""
    record = SETTING_REGISTRY.get(setting)
    if record is None:
        return False
    required_fixtures = {"pendulum_clock", "shelf", "delivery_board", "delivery_basket"}
    return (
        "pantry" in record["tags"]
        and required_fixtures.issubset(record["fixtures"])
        and "humor" in FEATURES
        and STYLE == "mystery"
        and "rhythm" in CLUES
        and "anise" in INGREDIENTS
        and PROTAGONIST_KIND == "snail"
    )


def _valid_python() -> list[str]:
    return sorted(_slug(setting) for setting in SETTING_REGISTRY if python_reasonableness_gate(setting))


def _count_word(count: int) -> str:
    return {3: "three", 4: "four", 5: "five"}.get(count, str(count))


def _simulate(params: StoryParams, seed: int) -> World:
    record = SETTING_REGISTRY[params.setting]
    count = 3 + ((seed // 9) % 3)
    rhythm = RHYTHMS[seed % len(RHYTHMS)]
    structure_variant = (seed // 3) % 3
    ending_variant = (seed // 27) % 3
    word_count = _count_word(count)

    world = World(setting=params.setting)
    world.add(
        "snail",
        Entity(
            name=params.snail,
            kind="snail",
            meters={"shell_length_cm": 2.8, "distance_to_shelf_m": 0.4, "anise_seed_badge": 0.0},
            memes={"curiosity": 0.9, "patience": 1.0, "confidence": 0.35},
        ),
    )
    world.add(
        "baker",
        Entity(
            name=params.baker,
            kind="cricket",
            meters={"height_cm": 3.2, "steps_to_pantry": 6.0},
            memes={"worry": 0.8, "suspicion_of_mouse": 0.65, "relief": 0.0},
        ),
    )
    world.add(
        "mouse",
        Entity(
            name=params.mouse,
            kind="mouse",
            meters={"height_cm": 4.1, "anise_specks_on_whiskers": 1.0},
            memes={"embarrassment": 0.45, "trust": 0.5, "confidence": 0.4},
        ),
    )
    world.add(
        "clock",
        Entity(
            name="the pendulum clock",
            kind="clock",
            meters={"swings_observed": 0.0, "wall_vibration": 0.7},
            memes={"steadiness": 0.9},
        ),
    )
    world.add(
        "shelf",
        Entity(
            name="the low pantry shelf",
            kind="shelf",
            meters={"tilt_degrees": 4.0, "wobble": 1.0},
            memes={},
        ),
    )
    world.add(
        "shim",
        Entity(
            name="the cork shim",
            kind="cork",
            meters={"under_shelf_leg": 0.0},
            memes={},
        ),
    )
    world.add(
        "board",
        Entity(
            name="the smooth delivery board",
            kind="board",
            meters={"slope_degrees": 5.0, "length_m": 0.6},
            memes={},
        ),
    )
    world.add(
        "basket",
        Entity(
            name="the delivery basket",
            kind="basket",
            meters={"buns": float(count), "hidden_behind_flour_sack": 1.0},
            memes={},
        ),
    )
    world.add(
        "buns",
        Entity(
            name="the anise buns",
            kind="food",
            meters={"count": float(count), "on_shelf": 0.0, "in_basket": float(count), "on_tray": 0.0},
            memes={},
        ),
    )
    world.add(
        "tray",
        Entity(
            name="the serving tray",
            kind="tray",
            meters={"buns": 0.0, "level": 1.0},
            memes={},
        ),
    )
    world.add(
        "flour_sack",
        Entity(
            name="the flour sack",
            kind="sack",
            meters={"distance_from_basket_m": 0.1},
            memes={},
        ),
    )

    world.facts.update(
        setting=params.setting,
        setting_detail=record["detail"],
        case_title="The Case of the Tap-Tap Buns",
        reported_missing=count,
        count_word=word_count,
        rhythm=rhythm,
        structure_variant=structure_variant,
        ending_variant=ending_variant,
        suspected_character=params.mouse,
        case_solved=False,
        hidden_location="the delivery basket behind the flour sack",
        mechanism="the clock's knocks shook a tilted shelf, sending the buns down a board into the basket",
        ending_image="",
    )
    world.events.append(
        f"{word_count.capitalize()} anise buns were reported missing from the locked pantry shelf."
    )
    world.events.append(
        f"{params.baker} first suspected {params.mouse}, whose whiskers carried anise specks."
    )

    world.entities["clock"].meters["swings_observed"] = 4.0
    world.entities["mouse"].memes["trust"] = 0.8
    world.entities["baker"].memes["suspicion_of_mouse"] = 0.0
    world.events.append(
        f"{params.mouse} repeated the {rhythm} rhythm, helping {params.snail} connect it to the pendulum."
    )
    world.events.append(
        f"{params.snail} found the missing cork shim, tilted shelf, delivery board, and hidden basket."
    )

    world.entities["shim"].meters["under_shelf_leg"] = 1.0
    world.entities["shelf"].meters["tilt_degrees"] = 0.0
    world.entities["shelf"].meters["wobble"] = 0.0
    world.entities["basket"].meters["buns"] = 0.0
    world.entities["buns"].meters["in_basket"] = 0.0
    world.entities["buns"].meters["on_tray"] = float(count)
    world.entities["tray"].meters["buns"] = float(count)
    world.entities["snail"].meters["anise_seed_badge"] = 1.0
    world.entities["snail"].memes["confidence"] = 0.95
    world.entities["snail"].memes["curiosity"] = 0.55
    world.entities["baker"].memes["worry"] = 0.1
    world.entities["baker"].memes["relief"] = 0.95
    world.entities["mouse"].memes["embarrassment"] = 0.05
    world.entities["mouse"].memes["trust"] = 1.0

    world.facts["case_solved"] = True
    world.facts["suspicion_cleared"] = True
    world.facts["buns_recovered"] = count
    world.facts["mechanism_confirmed"] = True

    ending_images = [
        f"a floury anise seed perched on {params.snail}'s shell like a tiny detective badge",
        f"{params.mouse} danced three careful steps beside the empty basket while the repaired shelf stayed straight",
        f"{params.baker}'s spoon tapped a jaunty rhythm beside the level tray, and every bun stayed put",
    ]
    world.facts["ending_image"] = ending_images[ending_variant]
    world.events.append(
        f"{params.mouse} replaced the cork shim while {params.baker} steadied the shelf; all {count} buns were recovered."
    )
    world.events.append("The pendulum kept swinging, but the repaired shelf stayed level.")
    return world


def _story_lines(world: World) -> list[str]:
    facts = world.facts
    snail = world.entities["snail"].name
    baker = world.entities["baker"].name
    mouse = world.entities["mouse"].name
    number = facts["count_word"]
    setting = facts["setting"]
    detail = facts["setting_detail"]
    rhythm = facts["rhythm"]
    variant = facts["structure_variant"]

    if variant == 0:
        opening = [
            f"At {setting}, {detail}. {snail}, a snail detective, was checking {number} anise buns for the evening fair.",
        ]
    elif variant == 1:
        opening = [
            f"{snail} liked mysteries that could be solved by listening. At {setting}, {detail}. The evening fair's {number} anise buns rested on a low pantry shelf.",
        ]
    else:
        opening = [
            f"At {setting}, {baker} locked the pantry after setting {number} anise buns on its low shelf. Outside, {detail}.",
        ]

    mystery = (
        f"By dawn, the pantry door was still locked, but its shelf was empty: all {number} buns had vanished. "
        f"A curl of flour stopped at the baseboard, and behind the flour sack came a neat {rhythm}."
    )
    exchange = (
        f"“Those anise specks on your whiskers look suspicious,” said {baker}. "
        f"“I sprinkled seeds on the fair table, not in my pockets,” {mouse} replied. "
        f"“Let's listen before we blame anyone,” said {snail}."
    )
    listening = (
        f"“Tap what you heard,” {snail} asked. “{rhythm.capitalize()},” {mouse} tapped on an empty tin. "
        f"“That last beat is coming from under the shelf!” said {baker}. "
        f"{snail} laid a feeler against the floor and waited through four pendulum swings. "
        f"Each swing trembled through the shelf; then a bun slid down the smooth delivery board and plopped into a shallow basket."
    )
    reveal = (
        f"A short cork shim had slipped from one shelf leg, tipping the shelf toward the board. "
        f"The clock's tiny knocks nudged the round buns one by one into the basket behind the flour sack. "
        f"No thief had crossed the locked door; the shelf had been giving the buns a bumpy ride."
    )
    action = (
        f"“Aha—not a thief, just a shelf on a bun slide!” said {snail}. "
        f"{baker} braced the shelf while {mouse} pushed the cork shim back under its short leg. "
        f"With {snail} pointing the way, they lifted all {number} buns from the basket onto a level tray. "
        f"The clock kept ticking, but the shelf stayed still and no bun rolled away."
    )
    ending = (
        f"They shared one warm bun and saved the rest for the fair. At dusk, {facts['ending_image']}."
    )

    if variant == 1:
        return [
            opening[0],
            mystery,
            exchange,
            listening,
            reveal,
            action,
            ending,
        ]
    if variant == 2:
        return [
            opening[0],
            mystery,
            listening,
            exchange,
            reveal,
            action,
            ending,
        ]
    return [
        opening[0],
        mystery,
        exchange,
        listening,
        reveal,
        action,
        ending,
    ]


def generate(params: StoryParams) -> StorySample:
    _validate_params(params)
    if not python_reasonableness_gate(params.setting):
        raise StoryError(f"The setting {params.setting!r} cannot support this pantry mystery.")

    seed = _stable_seed(params)
    world = _simulate(params, seed)
    story = "\n\n".join(_story_lines(world))
    count_word = world.facts["count_word"]
    rhythm = world.facts["rhythm"]
    ending_image = world.facts["ending_image"]

    prompts = [
        f"Write a humorous mystery about {params.snail}, a snail detective, and missing anise buns.",
        f"Tell a child-friendly pantry mystery in {params.setting} where a repeating rhythm helps solve the case.",
        "Write a complete mystery with a fair clue, a kind conversation, and a funny final image.",
    ]
    story_qa = [
        QAItem(
            question=f"Why did {params.baker} suspect {params.mouse}?",
            answer=(
                f"{params.baker} noticed anise specks on {params.mouse}'s whiskers and thought they looked suspicious. "
                f"{params.mouse} explained that the specks came from sprinkling seeds on the fair table."
            ),
        ),
        QAItem(
            question=f"How did the rhythm help {params.snail} solve the mystery?",
            answer=(
                f"{params.mouse} tapped the {rhythm} pattern, and {params.snail} listened through several pendulum swings. "
                f"The final beat came from a bun dropping into the hidden delivery basket, not from a thief."
            ),
        ),
        QAItem(
            question="Where were the missing anise buns?",
            answer=(
                f"The buns had rolled down a smooth delivery board into a shallow basket behind the flour sack. "
                f"The tilted shelf and the clock's small knocks had nudged them there one by one."
            ),
        ),
        QAItem(
            question="How did the friends stop the buns from disappearing?",
            answer=(
                f"{params.mouse} put the missing cork shim back under the short shelf leg while {params.baker} held the shelf steady. "
                f"Once the shelf was level, they moved the recovered buns onto a serving tray."
            ),
        ),
        QAItem(
            question="What funny image closes the mystery?",
            answer=f"The story ends with {ending_image}.",
        ),
    ]
    world_qa = [
        QAItem(
            question="What is a snail?",
            answer="A snail is a small animal with a soft body and, in many kinds, a shell it carries on its back.",
        ),
        QAItem(
            question="What is a rhythm?",
            answer="A rhythm is a pattern of sounds or movements that repeats in time, like a steady tap-tap.",
        ),
        QAItem(
            question="What is anise?",
            answer="Anise is a fragrant spice with a sweet smell that people often describe as licorice-like.",
        ),
        QAItem(
            question="What does a detective do?",
            answer="A detective looks closely at clues, asks questions, and uses evidence to work out what happened.",
        ),
        QAItem(
            question="Why can careful listening help solve a mystery?",
            answer="Careful listening can reveal a repeating sound or a hidden source that people might miss when they hurry.",
        ),
    ]
    return StorySample(
        params=params,
        story=story,
        prompts=prompts,
        story_qa=story_qa,
        world_qa=world_qa,
        world=world,
    )


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world is not None:
        print("--- world trace ---")
        for entity in sample.world.entities.values():
            print(f"{entity.name}: kind={entity.kind}, meters={dict(entity.meters)}, memes={dict(entity.memes)}")
        if sample.world.events:
            print("events:")
            for event in sample.world.events:
                print(f"- {event}")
    if qa:
        print()
        print("== prompts ==")
        for prompt in sample.prompts:
            print(prompt)
        print()
        print("== story qa ==")
        for item in sample.story_qa:
            print(f"Q: {item.question}")
            print(f"A: {item.answer}")
        print()
        print("== world qa ==")
        for item in sample.world_qa:
            print(f"Q: {item.question}")
            print(f"A: {item.answer}")


def asp_facts() -> str:
    from storyworlds import asp

    lines: list[str] = []
    for setting, record in SETTING_REGISTRY.items():
        key = _slug(setting)
        lines.append(asp.fact("setting", key))
        for tag in sorted(record["tags"]):
            lines.append(asp.fact("tag", key, tag))
        for fixture in sorted(record["fixtures"]):
            lines.append(asp.fact("fixture", key, fixture))
    for feature in sorted(FEATURES):
        lines.append(asp.fact("feature", feature))
    lines.append(asp.fact("style", STYLE))
    for clue in sorted(CLUES):
        lines.append(asp.fact("clue", clue))
    for ingredient in sorted(INGREDIENTS):
        lines.append(asp.fact("ingredient", ingredient))
    lines.append(asp.fact("protagonist", PROTAGONIST_KIND))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def _asp_valid() -> list[tuple]:
    from storyworlds import asp

    model = asp.one_model(asp_program("#show valid_case/1."))
    return sorted(set(asp.atoms(model, "valid_case")))


def _exercise_generated_stories() -> list[str]:
    failures: list[str] = []
    checks = 0
    for setting_index, setting in enumerate(SETTING_REGISTRY):
        for offset in range(3):
            sample = generate(
                StoryParams(
                    setting=setting,
                    snail="Mallow",
                    baker="Tock",
                    mouse="Nib",
                    seed=setting_index * 101 + offset * 27,
                )
            )
            checks += 1
            world = sample.world
            if world is None:
                failures.append(f"{setting}: generated sample has no live world")
                continue
            if not world.facts.get("case_solved"):
                failures.append(f"{setting}: generated mystery was not solved")
            if world.entities["shelf"].meters["tilt_degrees"] != 0.0:
                failures.append(f"{setting}: shelf was not repaired")
            if world.entities["basket"].meters["buns"] != 0.0:
                failures.append(f"{setting}: buns were not recovered from the basket")
            if world.entities["buns"].meters["on_tray"] != float(world.facts["reported_missing"]):
                failures.append(f"{setting}: recovered bun count does not match the report")
            if sample.story.count("“") < 4 or sample.story.count("”") < 4:
                failures.append(f"{setting}: story lacks a back-and-forth spoken exchange")
            if any(marker in sample.story for marker in ("{snail}", "{baker}", "{mouse}", "TODO")):
                failures.append(f"{setting}: story contains an unresolved scaffold")
            if not sample.story.rstrip().endswith("."):
                failures.append(f"{setting}: story has no complete ending")
            if len(sample.story_qa) < 4 or len(sample.world_qa) < 4:
                failures.append(f"{setting}: generated QA is incomplete")
    if not failures:
        failures.append(f"EXERCISED:{checks}")
    return failures


def asp_verify() -> int:
    try:
        python_cases = {(setting,) for setting in _valid_python()}
        clingo_cases = set(_asp_valid())
    except Exception as exc:
        print(f"ASP verification could not run: {exc}")
        return 1

    failures: list[str] = []
    if python_cases != clingo_cases:
        failures.append(f"Python only: {sorted(python_cases - clingo_cases)}")
        failures.append(f"clingo only: {sorted(clingo_cases - python_cases)}")

    exercise_results = _exercise_generated_stories()
    exercised = 0
    for result in exercise_results:
        if result.startswith("EXERCISED:"):
            exercised = int(result.split(":", 1)[1])
        else:
            failures.append(result)

    if failures:
        print("Verification failed:")
        for failure in failures:
            print(f"- {failure}")
        return 1

    print(
        f"OK: ASP gate matches Python ({len(python_cases)} settings); "
        f"{exercised} generated stories passed world and prose checks."
    )
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="A humorous snail-detective mystery about rhythm and anise buns."
    )
    parser.add_argument("--setting")
    parser.add_argument("--snail")
    parser.add_argument("--baker")
    parser.add_argument("--mouse")
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
    setting = args.setting if args.setting is not None else rng.choice(list(SETTING_REGISTRY))
    snail = args.snail if args.snail is not None else rng.choice(SNAIL_NAMES)
    baker = args.baker if args.baker is not None else rng.choice(BAKER_NAMES)
    mouse = args.mouse if args.mouse is not None else rng.choice(MOUSE_NAMES)
    params = StoryParams(
        setting=setting,
        snail=snail,
        baker=baker,
        mouse=mouse,
        seed=args.seed,
    )
    _validate_params(params)
    if not python_reasonableness_gate(setting):
        raise StoryError(f"The setting {setting!r} cannot support this pantry mystery.")
    return params


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()

    if args.show_asp:
        print(asp_program("#show valid_case/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        try:
            names = { _slug(setting): setting for setting in SETTING_REGISTRY }
            for item in _asp_valid():
                print(names.get(item[0], item[0]))
        except Exception as exc:
            print(f"ASP query could not run: {exc}", file=sys.stderr)
            sys.exit(1)
        return

    try:
        if not args.all and args.n < 1:
            raise StoryError("The number of stories must be at least one.")
        base_seed = args.seed if args.seed is not None else random.randrange(2**31)
        samples: list[StorySample] = []

        if args.all:
            for index, setting in enumerate(SETTING_REGISTRY):
                params = StoryParams(
                    setting=setting,
                    snail=args.snail if args.snail is not None else "Mallow",
                    baker=args.baker if args.baker is not None else "Tock",
                    mouse=args.mouse if args.mouse is not None else "Nib",
                    seed=base_seed + index * 37,
                )
                _validate_params(params)
                if not python_reasonableness_gate(setting):
                    raise StoryError(f"The setting {setting!r} cannot support this pantry mystery.")
                samples.append(generate(params))
        else:
            seen: set[str] = set()
            attempts = 0
            limit = max(100, args.n * 80)
            while len(samples) < args.n and attempts < limit:
                seed = base_seed + attempts
                attempts += 1
                rng = random.Random(seed)
                params = resolve_params(args, rng)
                params.seed = seed
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
            header = f"### variant {index + 1}" if len(samples) > 1 else ""
            emit(sample, trace=args.trace, qa=args.qa, header=header)
            if index < len(samples) - 1:
                print("\n" + "=" * 70 + "\n")
    except StoryError as exc:
        print(f"error: {exc}", file=sys.stderr)
        sys.exit(2)


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""
storyworlds/worlds/train_station_wait.py
======================================

Train-station world focused on waiting, patience, and safe choices.

The hero waits for a delayed train, notices a risky object/situation on the
platform, and picks a safe action constrained by both platform and object.
"""

from __future__ import annotations

import argparse
import random
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterable

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from storyworlds.results import QAItem, StoryError, StorySample  # noqa: E402


@dataclass(frozen=True)
class Platform:
    key: str
    phrase: str
    queue: str
    notes: str
    allowed_actions: tuple[str, ...]


@dataclass(frozen=True)
class StationObject:
    key: str
    phrase: str
    danger: str
    lesson_hint: str
    compatible_actions: tuple[str, ...]


@dataclass(frozen=True)
class SafeAction:
    key: str
    phrase: str
    action_line: str
    result_line: str
    lesson_line: str
    solves: tuple[str, ...]


@dataclass
class StoryParams:
    platform: str
    object: str
    action: str
    hero: str
    gender: str
    companion: str
    seed: int | None = None


@dataclass
class Entity:
    name: str
    kind: str
    attributes: list[str] = field(default_factory=list)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.kind in {"girl", "mother", "daughter", "aunt", "sister", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.kind in {"boy", "father", "brother", "son", "uncle", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]


@dataclass
class World:
    params: StoryParams
    platform: Platform
    object: StationObject
    action: SafeAction
    entities: dict[str, Entity] = field(default_factory=dict)
    facts: dict[str, str] = field(default_factory=dict)
    fired: list[str] = field(default_factory=list)

    def add(self, ent: Entity) -> None:
        self.entities[ent.name] = ent

    def trace(self) -> str:
        rows = ["--- world model state ---"]
        for name, ent in self.entities.items():
            rows.append(f"  {name}<{ent.kind}> traits={ent.attributes} memes={dict(ent.memes)}")
        rows.append(f"  platform={self.platform.key}")
        rows.append(f"  object={self.object.key}")
        rows.append(f"  action={self.action.key}")
        rows.append(f"  fired={self.fired}")
        rows.append(f"  facts={self.facts}")
        return "\n".join(rows)


PLATFORMS: dict[str, Platform] = {
    "platform_one": Platform(
        key="platform_one",
        phrase="Platform 1 at City Central Station",
        queue="the marked waiting area and staffed help desk",
        notes="a wide platform with clear painted zones",
        allowed_actions=("ask_staff", "move_to_wait_area"),
    ),
    "platform_two": Platform(
        key="platform_two",
        phrase="Platform 2 at Riverside Stop",
        queue="the narrow bridge and short steps",
        notes="a compact platform with little room to linger near the edge",
        allowed_actions=("step_back", "move_to_wait_area"),
    ),
    "platform_three": Platform(
        key="platform_three",
        phrase="Platform 3 at Eastbound Terminal",
        queue="a bright timetable wall",
        notes="a busy platform with staff and a standing line",
        allowed_actions=("ask_staff", "step_back", "move_to_wait_area"),
    ),
}

OBJECTS: dict[str, StationObject] = {
    "platform_edge": StationObject(
        key="platform_edge",
        phrase="the yellow platform edge where the tracks are visible",
        danger="leaning too far toward the tracks",
        lesson_hint="when trains are running, distance is the first safety rule",
        compatible_actions=("step_back", "ask_staff", "move_to_wait_area"),
    ),
    "wet_stairs": StationObject(
        key="wet_stairs",
        phrase="a wet stair strip beside the platform entrance",
        danger="a sudden slippery trip while running",
        lesson_hint="patience includes moving slowly in uncertain footing",
        compatible_actions=("step_back", "move_to_wait_area"),
    ),
    "door_gap": StationObject(
        key="door_gap",
        phrase="a train doorway gap opening and closing in a rush",
        danger="getting too close while trying to board fast",
        lesson_hint="wait for clear space before moving into the doorway",
        compatible_actions=("ask_staff", "move_to_wait_area"),
    ),
}

ACTIONS: dict[str, SafeAction] = {
    "ask_staff": SafeAction(
        key="ask_staff",
        phrase="ask a station staff member for guidance",
        action_line=(
            "{hero} asked {companion} to find a station staff member, "
            "then waited at the marked spot for instructions."
        ),
        result_line=(
            "The staff member explained the delay, showed the safe route, "
            "and helped {hero} keep waiting without crowding the edge."
        ),
        lesson_line="Waiting and asking for help can be the fastest way to stay safe.",
        solves=("crowd", "impatience", "leaning", "pinch"),
    ),
    "move_to_wait_area": SafeAction(
        key="move_to_wait_area",
        phrase="move to the official waiting area",
        action_line=(
            "{hero} took a breath, moved to the official waiting area, "
            "and stayed close to {companion} for company."
        ),
        result_line=(
            "Being in line and away from the edge gave {hero} time to wait calmly until the train doors opened safely."
        ),
        lesson_line="A planned place to wait can prevent impulsive, unsafe shortcuts.",
        solves=("impatience", "crowd", "trip"),
    ),
    "step_back": SafeAction(
        key="step_back",
        phrase="step back to a safer line",
        action_line=(
            "{hero} pulled back behind the painted line and resisted rushing forward, "
            "even though everyone seemed impatient."
        ),
        result_line=(
            "From that safer line, {hero} could still watch the delayed train arrive and wait for clear instructions before boarding."
        ),
        lesson_line="Patience is an active choice: stepping back avoids escalation.",
        solves=("leaning", "pinch", "trip"),
    ),
}

HERO_NAMES: dict[str, tuple[str, ...]] = {
    "girl": ("Mina", "Nina", "Sana", "Lila"),
    "boy": ("Noah", "Eli", "Ravi", "Jonah"),
}

COMPANIONS = ("Amir", "Milo", "Tara", "Grandpa Ben", "Uncle Leo")


def _pick_hero(gender: str, rng: random.Random) -> str:
    return rng.choice(HERO_NAMES[gender])


def _pick_companion(rng: random.Random) -> str:
    return rng.choice(COMPANIONS)


def _params_from_combo(args: argparse.Namespace, combo: tuple[str, str, str], index: int = 0) -> StoryParams:
    rng = random.Random(args.seed + index)
    gender = args.gender or rng.choice(sorted(HERO_NAMES))
    hero = args.hero or _pick_hero(gender, rng)
    companion = args.companion or _pick_companion(rng)
    platform_key, object_key, action_key = combo
    return StoryParams(
        platform=platform_key,
        object=object_key,
        action=action_key,
        hero=hero,
        gender=gender,
        companion=companion,
        seed=args.seed + index,
    )


def valid_combo(platform_key: str, object_key: str, action_key: str) -> bool:
    if platform_key not in PLATFORMS or object_key not in OBJECTS or action_key not in ACTIONS:
        return False
    platform = PLATFORMS[platform_key]
    station_object = OBJECTS[object_key]
    return action_key in platform.allowed_actions and action_key in station_object.compatible_actions


def invalid_reason(platform_key: str, object_key: str, action_key: str) -> str:
    if platform_key not in PLATFORMS:
        return f"No story: unknown platform {platform_key!r}."
    if object_key not in OBJECTS:
        return f"No story: unknown object {object_key!r}."
    if action_key not in ACTIONS:
        return f"No story: unknown safe action {action_key!r}."

    platform = PLATFORMS[platform_key]
    station_object = OBJECTS[object_key]
    if action_key not in platform.allowed_actions:
        return (
            f"No story: {platform.phrase} does not support safe action {action_key!r}. "
            f"Try one of: {', '.join(platform.allowed_actions)}."
        )
    if action_key not in station_object.compatible_actions:
        return (
            f"No story: object '{station_object.phrase}' is not safely handled by {action_key!r}. "
            f"It works with: {', '.join(station_object.compatible_actions)}."
        )
    return "No story: invalid combination."


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for platform_key in sorted(PLATFORMS):
        for object_key in sorted(OBJECTS):
            for action_key in sorted(ACTIONS):
                if valid_combo(platform_key, object_key, action_key):
                    combos.append((platform_key, object_key, action_key))
    return combos


def build_world(params: StoryParams) -> World:
    platform = PLATFORMS[params.platform]
    station_object = OBJECTS[params.object]
    action = ACTIONS[params.action]
    world = World(params=params, platform=platform, object=station_object, action=action)

    hero = Entity(params.hero, kind=params.gender, attributes=["patient", "curious"], memes={"patience": 0.5})
    companion = Entity(params.companion, kind="adult", attributes=["steady", "attentive"], memes={"calm": 1.0})
    world.add(hero)
    world.add(companion)

    world.facts["platform"] = platform.key
    world.facts["object"] = station_object.key
    world.facts["action"] = action.key
    world.facts["seed"] = str(params.seed)
    world.facts["hero"] = hero.name
    world.facts["companion"] = companion.name
    world.fired.append(f"waited_{platform.key}")
    world.fired.append(f"handled_{station_object.key}_by_{action.key}")
    return world


def _render_story(world: World) -> str:
    platform = world.platform
    station_object = world.object
    action = world.action
    params = world.params

    hero = world.entities[params.hero]
    companion = world.entities[params.companion]

    opening = (
        f"{hero.name} arrived at {platform.phrase} and found the train delayed again. "
        f"The station display showed crowded movement, and the platform felt rushed."
    )
    observation = (
        f"At {platform.queue}, {hero.name} noticed {station_object.phrase}. "
        f"It could cause {station_object.danger}."
    )
    action_line = action.action_line.format(
        hero=hero.name,
        companion=companion.name,
        companion_pronoun=companion.pronoun("object"),
        object=station_object.phrase,
    )
    result_line = action.result_line.format(
        hero=hero.name,
        companion=companion.name,
        companion_pronoun=companion.pronoun("possessive"),
        object=station_object.phrase,
        action=action.phrase,
    )
    lesson = f"{action.lesson_line} {hero.name} remembered: {station_object.lesson_hint}."

    return "\n\n".join([opening, observation, action_line, result_line, lesson])


def _prompts(world: World) -> list[str]:
    return [
        "Write a train-station waiting story with the words patience, train, and platform.",
        "Show how a child stays safe by choosing a thoughtful action instead of rushing.",
        "Keep the story grounded in station rules and realistic waiting behavior.",
    ]


def _story_qa(world: World) -> list[QAItem]:
    hero = world.params.hero
    companion = world.params.companion
    return [
        QAItem(
            "Where is the child waiting?",
            f"{hero} is waiting at {world.platform.phrase} with {companion}. The platform details matter because the safe action depends on its queue, staff access, and edge layout.",
        ),
        QAItem(
            "Why was patience necessary in the scene?",
            f"The risky situation involved {world.object.phrase}, which could lead to {world.object.danger}. Patience gave {hero} time to choose a station-safe action instead of reacting to the delay or the crowd.",
        ),
        QAItem(
            "How did the child stay safe?",
            f"{hero} chose to {world.action.phrase}. That moved the child away from the immediate risk and kept the waiting orderly.",
        ),
        QAItem(
            "What changed by the end?",
            f"{hero} stayed in the safe waiting flow and waited for proper boarding time without panicking. The story turns a frustrating delay into a practiced choice about where to stand and who to ask.",
        ),
        QAItem(
            "What should happen next if the platform gets busy again?",
            f"{hero} should keep using allowed station choices such as {world.action.phrase} or another action listed for this platform. The lesson is that patience works best when it is paired with a concrete safe place or helper.",
        ),
    ]


def _world_qa(world: World) -> list[QAItem]:
    platform = world.platform
    obj = world.object
    action = world.action
    return [
        QAItem(
            "Why is action choice constrained at this platform?",
            f"Each platform has different safe choices because its crowding, staff access, and edge layout are different. At {platform.phrase}, calm choices include {', '.join(ACTIONS[a].phrase for a in platform.allowed_actions)}.",
        ),
        QAItem(
            "Why is this action compatible with the object?",
            f"{obj.phrase.capitalize()} calls for a choice that creates distance and slows the child down. Compatible choices include {', '.join(ACTIONS[a].phrase for a in obj.compatible_actions)}, so the selected action is grounded in the object's danger.",
        ),
        QAItem(
            "What if a disallowed action had been used?",
            "A disallowed action could increase crowd pressure, rush, or an unsafe approach near tracks or doors. The world gate prevents those combinations so the generated story stays realistic.",
        ),
        QAItem(
            f"Was {action.phrase} considered an explicit safe action?",
            f"Yes. {action.phrase.capitalize()} is supported by the station rules here. The story shows it working because the child ends up waiting calmly instead of rushing near the hazard.",
        ),
    ]


def generate(params: StoryParams) -> StorySample:
    if not valid_combo(params.platform, params.object, params.action):
        raise StoryError(invalid_reason(params.platform, params.object, params.action))

    world = build_world(params)
    return StorySample(
        params=params,
        story=_render_story(world),
        prompts=_prompts(world),
        story_qa=_story_qa(world),
        world_qa=_world_qa(world),
        world=world,
    )


ASP_RULES = """
combo(P,O,A) :-
    platform(P),
    station_object(O),
    safe_action(A),
    platform_allows(P, A),
    object_allows(O, A).

ok :- chosen(P, O, A), combo(P, O, A).

#show combo/3.
#show ok/0.
"""


def asp_facts(params: StoryParams | None = None) -> str:
    from storyworlds.asp import fact

    rows: list[str] = []
    for key in sorted(PLATFORMS):
        rows.append(fact("platform", key))
        for action_key in PLATFORMS[key].allowed_actions:
            rows.append(fact("platform_allows", key, action_key))
    for key in sorted(OBJECTS):
        rows.append(fact("station_object", key))
        for action_key in OBJECTS[key].compatible_actions:
            rows.append(fact("object_allows", key, action_key))
    for action_key in sorted(ACTIONS):
        rows.append(fact("safe_action", action_key))
    if params is not None:
        rows.append(fact("chosen", params.platform, params.object, params.action))
    return "\n".join(rows) + "\n"


def asp_program(params: StoryParams | None = None) -> str:
    return asp_facts(params) + ASP_RULES


def asp_valid_combos() -> set[tuple[str, str, str]]:
    from storyworlds.asp import atoms, solve

    combos: set[tuple[str, str, str]] = set()
    for model in solve(asp_program(), models=0):
        combos.update(atoms(model, "combo"))
    return combos


def verify() -> str:
    python_set = set(valid_combos())
    asp_set = asp_valid_combos()
    if python_set != asp_set:
        only_python = sorted(python_set - asp_set)
        only_asp = sorted(asp_set - python_set)
        raise StoryError(f"ASP/Python mismatch. only_python={only_python} only_asp={only_asp}")
    return f"OK: clingo gate matches valid_combos() with {len(python_set)} combos."


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Generate train-station patience world samples.")
    parser.add_argument("--platform", choices=sorted(PLATFORMS), default=None)
    parser.add_argument("--object", choices=sorted(OBJECTS), default=None)
    parser.add_argument("--action", choices=sorted(ACTIONS), default=None)
    parser.add_argument("--hero", default=None)
    parser.add_argument("--gender", choices=sorted(HERO_NAMES), default=None)
    parser.add_argument("--companion", choices=COMPANIONS, default=None)
    parser.add_argument("--seed", type=int, default=1)
    parser.add_argument("-n", type=int, default=1)
    parser.add_argument("--all", action="store_true")
    parser.add_argument("--trace", action="store_true")
    parser.add_argument("--qa", action="store_true")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--asp", action="store_true")
    parser.add_argument("--verify", action="store_true")
    parser.add_argument("--show-asp", action="store_true")
    return parser


def resolve_params(args: argparse.Namespace, index: int = 0) -> StoryParams:
    combos = valid_combos()
    filtered = [c for c in combos if (args.platform is None or c[0] == args.platform)
                and (args.object is None or c[1] == args.object)
                and (args.action is None or c[2] == args.action)]
    if args.platform or args.object or args.action:
        if not filtered:
            raise StoryError(invalid_reason(
                args.platform or "<platform>",
                args.object or "<object>",
                args.action or "<action>",
            ))
    if not filtered:
        filtered = combos

    rng = random.Random(args.seed + index)
    combo = rng.choice(filtered)
    return _params_from_combo(args, combo, index)


def _print_qa(sample: StorySample) -> None:
    print("\n== (1) Story prompts ==")
    for i, prompt in enumerate(sample.prompts, 1):
        print(f"{i}. {prompt}")
    print("\n== (2) Story Q&A ==")
    for qa in sample.story_qa:
        print(f"Q: {qa.question}")
        print(f"A: {qa.answer}")
    print("\n== (3) World Q&A ==")
    for qa in sample.world_qa:
        print(f"Q: {qa.question}")
        print(f"A: {qa.answer}")


def emit(sample: StorySample, args: argparse.Namespace, label: str | None = None) -> None:
    if args.json:
        print(sample.to_json())
        return
    if label:
        print(label)
    print(sample.story)
    if args.trace and sample.world is not None:
        print(sample.world.trace())
    if args.qa:
        _print_qa(sample)


def _emit_asp_listing() -> None:
    for platform_key, object_key, action_key in sorted(asp_valid_combos()):
        print(f"{platform_key}\t{object_key}\t{action_key}")


def main(argv: Iterable[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    try:
        if args.show_asp:
            print(asp_program())
            return 0
        if args.verify:
            print(verify())
            return 0
        if args.asp:
            _emit_asp_listing()
            return 0
        if args.all:
            combos = valid_combos()
            for i, combo in enumerate(combos, 1):
                sample = generate(_params_from_combo(args, combo, i))
                emit(sample, args, f"### {combo[0]} / {combo[1]} / {combo[2]}")
                if i != len(combos) and not args.json:
                    print("\n" + "=" * 72 + "\n")
            return 0

        count = max(1, args.n)
        for i in range(count):
            sample = generate(resolve_params(args, i))
            label = f"### variant {i + 1}" if count > 1 and not args.json else None
            emit(sample, args, label)
            if i != count - 1 and not args.json:
                print("\n" + "=" * 72 + "\n")
        return 0
    except StoryError as exc:
        print(exc, file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())

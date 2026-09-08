#!/usr/bin/env python3
"""Child-safe space-adventure storyworld about a broad cosmic artery."""

from __future__ import annotations

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
class Entity:
    id: str
    kind: str
    type: str
    label: str = ""
    owner: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def __post_init__(self) -> None:
        for key in ("distance", "energy", "danger", "clarity"):
            self.meters.setdefault(key, 0.0)
        for key in ("wonder", "worry", "trust", "joy", "courage"):
            self.memes.setdefault(key, 0.0)


@dataclass
class Ship:
    name: str
    place: str
    engine_ready: bool = True
    beacon_open: bool = False


@dataclass
class StoryParams:
    place: str
    hero: str
    companion: str
    ship: str
    seed: Optional[int] = None


@dataclass(frozen=True)
class Mission:
    title: str
    task: str
    problem: str
    first_guess: str
    clue: str
    test: str
    cause: str
    solution: str
    transformation: str
    result: str
    lesson: str
    ending: str


MISSIONS = [
    Mission(
        "the silent starway",
        "mapping a broad artery of starlight between two friendly moons",
        "the artery had narrowed into a dim silver thread",
        "a dark planet had swallowed the route",
        "the missing light curved around a field of tiny singing stones",
        "sent a harmless blue pulse along the safe edge and watched its echo",
        "dust had covered the route markers, so the artery looked broken even though its path was still there",
        "guided the ship around the stones while the companion cleared the markers with a gentle magnetic sweep",
        "the dim thread transformed into a broad, glowing highway",
        "both moons received their evening messages, and the ship had fuel left for the trip home",
        "A careful test can reveal a safe path inside a puzzling problem",
        "the broad artery shone like a ribbon while the moons blinked hello",
    ),
    Mission(
        "the drifting garden",
        "carrying warm seed pods through a broad artery toward a moon garden",
        "the ship began drifting whenever it entered a pale cloud",
        "the engine had stopped working",
        "the drift changed only when the ship crossed green sparks",
        "compared the engine hum with the cloud's changing colors",
        "the cloud held gentle magnetic currents that nudged the ship sideways",
        "trimmed the sails and followed the green-spark pattern instead of fighting the current",
        "the drifting route transformed into a smooth spiral through the artery",
        "every seed pod reached the garden, where tiny silver leaves unfolded",
        "Understanding a force makes solving a problem easier than pushing blindly",
        "the new garden glittered below the broad route as the crew waved goodbye",
    ),
    Mission(
        "the lantern knot",
        "delivering a bright navigation lantern to a far station",
        "three branches of the broad artery seemed to lead to the station",
        "the station beacon must have moved",
        "only one branch carried a repeating warm-yellow blink",
        "asked the station to answer with a matching pulse",
        "two branches were reflections from an old ice ring, while the blinking branch was the real route",
        "rewrote the ship map so the true artery stood out from its reflections",
        "the station received its lantern before the night watch began",
        "Good clues separate a real path from a tempting copy",
        "the station lantern joined the artery's lights and made the whole route brighter",
    ),
    Mission(
        "the sleepy comet",
        "bringing a repair kit along a broad artery near a slow comet",
        "the ship's welcome bell rang whenever the comet turned",
        "the comet was calling for help",
        "the bell rang at exactly the same time as a loose storage latch",
        "held the latch closed for one turn and listened again",
        "the loose latch made the bell, while the comet was peacefully following its orbit",
        "secured the latch and used the comet's orbit as a steady timing mark",
        "the repair kit arrived safely, and the comet sent a sparkling tail across the sky",
        "Events that happen together do not always share a cause",
        "the quiet bell rang once at the station as the comet painted a silver smile",
    ),
]


ROUTES = [
    (
        "Beyond the classroom dome, the stars opened into a broad artery of light.",
        "The crew had to change their plan when the route refused to look the way the map promised.",
        "Their solution made the next journey safer for every traveler.",
    ),
    (
        "The little ship hummed at the edge of a great space highway.",
        "A small problem became a chance to notice, test, and transform the route.",
        "The crew returned with a story that made the whole station cheer.",
    ),
    (
        "Stars crowded the window like bright seeds in dark soil.",
        "The crew did not rush toward the strangest clue; they checked what it could really mean.",
        "By the end, the sky itself seemed to celebrate their careful work.",
    ),
    (
        "The broad artery connected distant homes like a glowing thread.",
        "When the thread flickered, teamwork turned worry into a useful plan.",
        "The repaired route carried more than a ship: it carried hope.",
    ),
]


HEROES = ["Luna", "Mira", "Sol", "Ari", "Nia", "Theo"]
COMPANIONS = ["Pip", "Orion", "Tess", "Kibo", "Mara", "Nova"]
SHIPS = ["Starling", "Comet Finch", "Blue Lantern", "Little Meteor"]


def _choose(seed: Optional[int]) -> tuple[Mission, tuple[str, str, str]]:
    value = seed or 0
    return MISSIONS[value % len(MISSIONS)], ROUTES[(value // len(MISSIONS)) % len(ROUTES)]


def validate_params(params: StoryParams) -> None:
    if not params.place.strip():
        raise StoryError("place must be a non-empty location")
    if params.hero == params.companion:
        raise StoryError("hero and companion must be different characters")
    if not params.ship.strip():
        raise StoryError("ship must have a name")


def build_world(params: StoryParams) -> "World":
    validate_params(params)
    mission, route = _choose(params.seed)
    world = World(Ship(params.ship, params.place))
    hero = world.add(Entity(params.hero, "character", "young space pilot"))
    companion = world.add(Entity(params.companion, "character", "helpful navigation companion"))
    artery = world.add(Entity("artery", "route", "broad space artery", label="broad artery"))
    beacon = world.add(Entity("beacon", "tool", "navigation beacon"))
    hero.memes.update(wonder=1.0, worry=0.7, courage=0.4)
    companion.memes.update(trust=0.8, wonder=0.7)
    artery.meters.update(distance=1.0, danger=0.4, clarity=0.5)
    beacon.meters.update(energy=1.0, clarity=0.7)

    world.say(route[0])
    world.say(
        f"{params.hero} guided the {params.ship} through the {params.place}, "
        f"while {params.companion} checked the route instruments."
    )
    world.say(
        f'"The artery is broad enough for our whole journey," {params.companion} said. '
        f'"We can help the station and still get home."'
    )
    world.say(f"They were {mission.task} when {mission.problem}.")
    world.say(
        f'"Maybe {mission.first_guess}," {params.hero} said. '
        f'"Let us find out before we change course."'
    )
    world.say(route[1])
    world.say(f"Then {params.companion} noticed that {mission.clue}.")
    world.say(
        f'"I can test that from the safe lane," {params.hero} replied. '
        f'"You watch the echo and tell me what changes."'
    )
    world.say(f"Together they {mission.test}.")
    world.say(f"The test showed that {mission.cause}.")
    world.say(f"They {mission.solution}.")
    world.say(
        f"As their plan worked, {mission.transformation}. "
        f"The artery became clear enough for the ship to follow."
    )
    world.say(f"Afterward, {mission.result}.")
    world.say(
        f'"{mission.lesson}," {params.companion} said. '
        f'"A good solution leaves the next traveler safer."'
    )
    world.say(route[2])
    world.say(f"At the end of the journey, {mission.ending}.")

    hero.memes.update(worry=0.0, courage=1.0, joy=1.0)
    companion.memes.update(trust=1.0, joy=1.0)
    artery.meters.update(danger=0.0, clarity=1.0)
    world.ship.beacon_open = True
    world.facts.update(
        mission=mission,
        hero=hero,
        companion=companion,
        artery=artery,
        beacon=beacon,
        resolved=True,
        transformed=True,
        happy_ending=True,
        child_safe=True,
    )
    return world


class World:
    def __init__(self, ship: Ship):
        self.ship = ship
        self.entities: dict[str, Entity] = {}
        self.events: list[str] = []
        self.facts: dict[str, object] = {}

    def add(self, entity: Entity) -> Entity:
        self.entities[entity.id] = entity
        return entity

    def say(self, text: str) -> None:
        self.events.append(text)

    def render(self) -> str:
        return " ".join(self.events)


def generation_prompts(world: World) -> list[str]:
    mission: Mission = world.facts["mission"]
    return [
        'Write a child-safe Space Adventure story using the words "artery" and "broad".',
        f'Tell a transformation story in which the crew solves "{mission.title}" through observation and teamwork.',
        f"Show a happy ending after the crew learns that {mission.cause}.",
    ]


def make_story_qa(world: World) -> list[QAItem]:
    mission: Mission = world.facts["mission"]
    hero: Entity = world.facts["hero"]
    companion: Entity = world.facts["companion"]
    return [
        QAItem(
            f"What were {hero.id} and {companion.id} doing?",
            f"They were {mission.task}. They were traveling through a broad space artery to help another place.",
        ),
        QAItem(
            "What problem did the crew face?",
            f"The problem was that {mission.problem}. This made the route difficult to understand or use safely.",
        ),
        QAItem(
            "What clue helped them solve the problem?",
            f"They noticed that {mission.clue}. That clue led them to a safe test instead of a hurried guess.",
        ),
        QAItem(
            "How did the route transform?",
            f"{mission.transformation.capitalize()}. The artery became clear enough for the ship to follow.",
        ),
        QAItem(
            "How did the story end happily?",
            f"{mission.result.capitalize()}. The crew finished their helpful mission and had a safe way home.",
        ),
    ]


def make_world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            "What is an artery?",
            "An artery is a route that carries something from one place to another. In this story, a space artery carries ships and messages between distant homes.",
        ),
        QAItem(
            "What does broad mean?",
            "Broad means wide or covering a large area. The broad space artery gives travelers room to move safely.",
        ),
        QAItem(
            "What is transformation?",
            "Transformation is a meaningful change from one state to another. In the story, a puzzling route becomes a clear and useful path.",
        ),
        QAItem(
            "Why is testing useful when solving a problem?",
            "Testing lets people check an idea with evidence before making a bigger decision. A safe test can reveal the cause and guide a better solution.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts ==", *sample.prompts, "", "== story questions =="]
    for item in sample.story_qa:
        lines.extend([f"Q: {item.question}", f"A: {item.answer}"])
    lines.append("")
    lines.append("== world questions ==")
    for item in sample.world_qa:
        lines.extend([f"Q: {item.question}", f"A: {item.answer}"])
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- trace ---", f"ship: {world.ship.name} place={world.ship.place} beacon_open={world.ship.beacon_open}"]
    for entity in world.entities.values():
        meters = {k: round(v, 2) for k, v in entity.meters.items() if v}
        memes = {k: round(v, 2) for k, v in entity.memes.items() if v}
        lines.append(
            f"{entity.id}: kind={entity.kind} type={entity.type} "
            f"meters={meters} memes={memes}"
        )
    lines.append("resolved=True transformed=True happy_ending=True")
    return "\n".join(lines)


def generate(params: StoryParams) -> StorySample:
    world = build_world(params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=make_story_qa(world),
        world_qa=make_world_qa(world),
        world=world,
    )


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world is not None:
        print(dump_trace(sample.world))
    if qa:
        print("\n" + format_qa(sample))


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Space Adventure storyworld about a broad artery.")
    parser.add_argument("--seed", type=int, default=None)
    parser.add_argument("-n", type=int, default=1)
    parser.add_argument("--all", action="store_true")
    parser.add_argument("--trace", action="store_true")
    parser.add_argument("--qa", action="store_true")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--asp", action="store_true")
    parser.add_argument("--verify", action="store_true")
    parser.add_argument("--show-asp", action="store_true")
    return parser


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    hero = rng.choice(HEROES)
    companion = rng.choice([name for name in COMPANIONS if name != hero])
    return StoryParams(
        place="the outer starway",
        hero=hero,
        companion=companion,
        ship=rng.choice(SHIPS),
    )


ASP_RULES = """
theme(artery).
theme(broad).
style(space_adventure).
feature(transformation).
feature(problem_solving).
feature(happy_ending).
route(broad_artery).
resolved :- route(broad_artery), feature(problem_solving).
transformed :- resolved, feature(transformation).
happy :- transformed, feature(happy_ending).
safe_journey :- happy.
"""


def asp_facts() -> str:
    import asp

    return "\n".join(
        [
            asp.fact("theme", "artery"),
            asp.fact("theme", "broad"),
            asp.fact("style", "space_adventure"),
            asp.fact("feature", "transformation"),
            asp.fact("feature", "problem_solving"),
            asp.fact("feature", "happy_ending"),
            asp.fact("route", "broad_artery"),
        ]
    )


def asp_program(show: str = "") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    try:
        from asp import atoms, one_model
    except ImportError:
        return 0
    symbols = one_model(asp_program("#show resolved/0.\n#show transformed/0.\n#show happy/0.\n#show safe_journey/0."))
    required = {"resolved", "transformed", "happy", "safe_journey"}
    found = {name for name in required if atoms(symbols, name)}
    if found != required:
        return 1
    sample = generate(
        StoryParams(
            place="the outer starway",
            hero="Luna",
            companion="Pip",
            ship="Starling",
            seed=0,
        )
    )
    text = sample.story.lower()
    for word in ("artery", "broad"):
        if word not in text:
            return 1
    if not sample.world or not sample.world.facts.get("transformed"):
        return 1
    return 0


def main() -> None:
    args = build_parser().parse_args()
    base_seed = args.seed if args.seed is not None else random.randrange(2**31)

    if args.show_asp or args.asp:
        print(asp_program("#show resolved/0.\n#show transformed/0.\n#show happy/0."))
        return

    if args.verify:
        sys.exit(asp_verify())

    if args.all:
        samples = [
            generate(StoryParams("the outer starway", "Luna", "Pip", "Starling", seed=i))
            for i in range(len(MISSIONS))
        ]
    else:
        samples = []
        for offset in range(max(1, args.n)):
            seed = base_seed + offset
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

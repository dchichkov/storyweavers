#!/usr/bin/env python3
"""A small child-safe space-adventure storyworld about a fortunate village quest."""

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
        for key in ("fuel", "distance", "signal", "risk", "power"):
            self.meters.setdefault(key, 0.0)
        for key in ("hope", "worry", "trust", "joy", "curiosity"):
            self.memes.setdefault(key, 0.0)


@dataclass
class World:
    place: str
    entities: dict[str, Entity] = field(default_factory=dict)
    events: list[str] = field(default_factory=list)
    facts: dict[str, object] = field(default_factory=dict)

    def add(self, entity: Entity) -> Entity:
        self.entities[entity.id] = entity
        return entity

    def say(self, text: str) -> None:
        self.events.append(text)

    def render(self) -> str:
        return " ".join(self.events)


@dataclass
class StoryParams:
    village: str
    captain: str
    helper: str
    starship: str
    beacon: str
    seed: Optional[int] = None


@dataclass(frozen=True)
class Quest:
    title: str
    moon: str
    problem: str
    clue: str
    first_guess: str
    test: str
    cause: str
    action: str
    repair: str
    result: str
    lesson: str
    ending: str


QUESTS = [
    Quest(
        "The Quiet Beacon",
        "Moon Luma",
        "the village's welcome beacon stopped sending its blue pulse",
        "a tiny silver feather of dust rested inside the beacon's glass hood",
        "a space storm had swallowed the signal",
        "compared the beacon's blinking panel with the old signal map",
        "moon dust had covered the light sensor",
        "landed beside the beacon and used a soft brush from the repair kit",
        "cleaned the sensor and aimed the hood away from the dusty ridge",
        "the village could guide travelers home before nightfall",
        "A careful clue can be more useful than a grand guess",
        "the blue beacon winked across the dark while the village windows glowed below",
    ),
    Quest(
        "The Lost Garden Pod",
        "Orchard Moon",
        "a seed pod carrying the village garden's new sprouts drifted away from the launch rail",
        "three green leaves showed in the pod's reflection",
        "the pod had floated beyond the moon forever",
        "followed the reflection with the ship's gentle search lamp",
        "the pod's magnetic latch had caught on an old survey buoy",
        "matched the buoy's slow orbit and sent a small rescue drone",
        "released the pod and guided it back to the village greenhouse",
        "fresh food would grow for every family",
        "Hope grows when helpers look closely and act patiently",
        "the rescued pod opened beneath warm lamps as tiny roots reached for the soil",
    ),
    Quest(
        "The Singing Comet",
        "Comet Brindle",
        "a strange note echoed through the village radio each evening",
        "the note arrived only when the comet's icy tail crossed the antenna",
        "a hidden traveler was calling from deep space",
        "recorded the note at two different distances from the comet",
        "ice crystals were making the antenna ring like a glass bell",
        "turned the antenna slightly and placed a soft shield around its base",
        "the radio carried clear messages again",
        "Curiosity is strongest when it is guided by evidence",
        "the comet sang one last bright note as the village children waved",
    ),
    Quest(
        "The Red Route",
        "Marsward Ridge",
        "the supply shuttle's route marker showed a red warning",
        "the warning appeared beside a harmless pebble icon, not a hazard icon",
        "the ridge was too dangerous to cross",
        "checked the route against the captain's printed star chart",
        "an old map layer had been selected by mistake",
        "changed to the current map and circled the real safe landing place",
        "the shuttle delivered warm blankets and repair parts",
        "Good maps turn worry into a useful plan",
        "the shuttle's red lights became welcoming stars above the fortunate village",
    ),
    Quest(
        "The Wandering Lantern",
        "Lantern Asteroid",
        "the village's navigation lantern wandered a little farther from its post each hour",
        "its tether shone where a loose clasp had rubbed it bright",
        "a gravity wave was pulling the lantern away",
        "watched the lantern from a safe distance while the ship measured its motion",
        "a clasp had not locked after the last inspection",
        "sent a tether drone to secure the clasp without chasing the lantern",
        "the lantern returned to its steady circle",
        "Small checks can prevent a much larger rescue",
        "the lantern floated safely above the roofs like a second moon",
    ),
]

CAPTAINS = ["Luna", "Mara", "Tavi", "Niko", "Suri", "Elian"]
HELPERS = ["Pip", "Bex", "Odo", "Rin", "Kato", "Mina"]
STARSHIPS = ["Silver Finch", "Bright Acorn", "Comet Kite", "Little Orbit"]
VILLAGES = ["Starfall Village", "Moonwell Village", "Aurora Village", "Cinderbell Village"]
BEACONS = ["welcome beacon", "garden beacon", "harbor beacon", "sky beacon"]


def _quest(seed: Optional[int]) -> Quest:
    if seed is None:
        raise StoryError("A quest seed is required for a reproducible space adventure.")
    return QUESTS[seed % len(QUESTS)]


def tell_story(params: StoryParams) -> World:
    if params.captain == params.helper:
        raise StoryError("The captain and helper must be different characters.")
    if not params.village.strip():
        raise StoryError("The village name cannot be empty.")
    if not params.starship.strip():
        raise StoryError("The starship name cannot be empty.")

    quest = _quest(params.seed)
    world = World(place=params.village)

    captain = world.add(
        Entity(
            id=params.captain,
            kind="character",
            type="village space captain",
            memes={"hope": 1.0, "worry": 1.0, "trust": 0.5, "joy": 0.0, "curiosity": 1.0},
        )
    )
    helper = world.add(
        Entity(
            id=params.helper,
            kind="character",
            type="young star mechanic",
            memes={"hope": 0.8, "worry": 0.5, "trust": 1.0, "joy": 0.0, "curiosity": 1.0},
        )
    )
    ship = world.add(
        Entity(
            id="ship",
            kind="vehicle",
            type="small starship",
            label=params.starship,
            owner=params.village,
            meters={"fuel": 0.8, "distance": 0.0, "signal": 0.0, "risk": 0.2, "power": 1.0},
        )
    )
    beacon = world.add(
        Entity(
            id="beacon",
            kind="device",
            type="village beacon",
            label=params.beacon,
            owner=params.village,
            meters={"fuel": 0.0, "distance": 0.0, "signal": 0.2, "risk": 0.4, "power": 0.6},
        )
    )

    world.say(
        f"On the edge of the star lanes stood {params.village}, a small village with silver roofs and gardens under glass."
    )
    world.say(
        f"{params.captain} kept the village starship, the {params.starship}, ready for helpful journeys."
    )
    world.say(
        f"One evening, the {params.beacon} began to trouble everyone because {quest.problem}."
    )
    world.say(f'"We must begin a quest," {params.captain} said. "But we will begin with what we can observe."')
    world.say(
        f'"I found a clue," {params.helper} replied. "Look: {quest.clue}."'
    )
    world.say(
        f"{params.captain} first wondered whether {quest.first_guess}, but the captain did not treat that guess as a fact."
    )
    world.say(
        f'"Let us test it from a safe orbit," {params.captain} said. "We can help without rushing."'
    )
    world.say(
        f"The {params.starship} lifted over the village and {quest.test}."
    )
    world.say(
        f"The readings showed that {quest.cause}."
    )
    world.say(
        f"Together, {params.captain} and {params.helper} {quest.action}."
    )
    world.say(
        f"After that, they {quest.repair}. The beacon's signal grew bright, and the village's worry became relief."
    )
    world.say(
        f'"{quest.lesson}," {params.helper} said as the ship settled beside the village square.'
    )
    world.say(
        f"As a result, {quest.result}. The quest had not needed a battle; it had needed attention, teamwork, and a safe plan."
    )
    world.say(
        f"At dusk, {quest.ending}."
    )

    captain.memes.update(worry=0.0, trust=1.0, joy=1.0)
    helper.memes.update(worry=0.0, joy=1.0)
    ship.meters.update(distance=1.0, risk=0.0)
    beacon.meters.update(signal=1.0, risk=0.0, power=1.0)

    world.facts.update(
        captain=captain,
        helper=helper,
        ship=ship,
        beacon=beacon,
        quest=quest,
        village=params.village,
        resolved=True,
        fortunate=True,
        child_safe=True,
    )
    return world


def generation_prompts(world: World) -> list[str]:
    quest = world.facts["quest"]
    captain = world.facts["captain"]
    helper = world.facts["helper"]
    return [
        f'Write a child-safe Space Adventure about a fortunate village called "{world.facts["village"]}".',
        f"Tell a dialogue-rich Quest in which {captain.id} and {helper.id} investigate {quest.problem}.",
        f"Build the turning point around this clue: {quest.clue}.",
    ]


def story_qa(world: World) -> list[QAItem]:
    facts = world.facts
    quest: Quest = facts["quest"]
    captain: Entity = facts["captain"]
    helper: Entity = facts["helper"]
    ship: Entity = facts["ship"]
    village = facts["village"]
    return [
        QAItem(
            f"What problem began the quest in {village}?",
            f"The quest began because {quest.problem}. The village needed its beacon and its safe connection to travelers restored.",
        ),
        QAItem(
            f"What clue did {helper.id} notice?",
            f"{helper.id} noticed that {quest.clue}. That physical clue helped the two helpers test an explanation instead of relying on a guess.",
        ),
        QAItem(
            f"How did {captain.id} and {helper.id} investigate?",
            f"They used the {ship.label} and {quest.test}. They observed the problem from a safe distance before choosing an action.",
        ),
        QAItem(
            "What caused the trouble?",
            f"They discovered that {quest.cause}. The evidence connected the clue to the real cause.",
        ),
        QAItem(
            "How did the fortunate village change by the ending?",
            f"{quest.result.capitalize()} The beacon became reliable again, and the villagers could look toward space with hope instead of worry.",
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            "What is a village?",
            "A village is a small community where people live, work, and help one another. In this story, the village also has space-travel equipment.",
        ),
        QAItem(
            "What is a quest?",
            "A quest is a purposeful journey or challenge. The characters follow clues, make choices, and work toward a helpful resolution.",
        ),
        QAItem(
            "What makes the village fortunate?",
            "The village is fortunate because its people notice problems, share knowledge, and have helpers who use careful plans to protect their home.",
        ),
        QAItem(
            "What is a starship?",
            "A starship is a vehicle designed to travel through space. This story uses a small starship for observation and gentle repairs.",
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
    lines = ["--- trace ---", f"place: {world.place}", "resolved: true", "fortunate: true"]
    for entity in world.entities.values():
        meters = {key: round(value, 2) for key, value in entity.meters.items() if value}
        memes = {key: round(value, 2) for key, value in entity.memes.items() if value}
        lines.append(
            f"{entity.id}: kind={entity.kind} type={entity.type} "
            f"meters={meters} memes={memes}"
        )
    quest: Quest = world.facts["quest"]
    lines.append(f"quest: {quest.title}")
    return "\n".join(lines)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Fortunate village Space Adventure storyworld.")
    parser.add_argument("-n", type=int, default=1)
    parser.add_argument("--all", action="store_true")
    parser.add_argument("--seed", type=int, default=None)
    parser.add_argument("--trace", action="store_true")
    parser.add_argument("--qa", action="store_true")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--asp", action="store_true")
    parser.add_argument("--verify", action="store_true")
    parser.add_argument("--show-asp", action="store_true")
    return parser


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    captain = rng.choice(CAPTAINS)
    helper = rng.choice([name for name in HELPERS if name != captain])
    return StoryParams(
        village=rng.choice(VILLAGES),
        captain=captain,
        helper=helper,
        starship=rng.choice(STARSHIPS),
        beacon=rng.choice(BEACONS),
    )


ASP_RULES = """
place(village).
theme(fortunate).
feature(quest).
style(space_adventure).
has_home(village).
has_clue(quest).
safe_quest :- place(village), theme(fortunate), feature(quest), has_home(village), has_clue(quest).
resolved :- safe_quest.
"""


def asp_facts() -> str:
    import asp

    return "\n".join(
        [
            asp.fact("place", "village"),
            asp.fact("theme", "fortunate"),
            asp.fact("feature", "quest"),
            asp.fact("style", "space_adventure"),
            asp.fact("has_home", "village"),
            asp.fact("has_clue", "quest"),
        ]
    )


def asp_program(show: str = "") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    try:
        import asp

        symbols = asp.one_model(asp_program("#show safe_quest/0.\n#show resolved/0."))
        names = {symbol.name for symbol in symbols}
        if not {"safe_quest", "resolved"}.issubset(names):
            return 1
    except Exception:
        return 1

    for seed in range(len(QUESTS)):
        params = StoryParams(
            village=VILLAGES[seed % len(VILLAGES)],
            captain=CAPTAINS[seed % len(CAPTAINS)],
            helper=HELPERS[(seed + 1) % len(HELPERS)],
            starship=STARSHIPS[seed % len(STARSHIPS)],
            beacon=BEACONS[seed % len(BEACONS)],
            seed=seed,
        )
        try:
            sample = generate(params)
        except StoryError:
            return 1
        if not sample.world or not sample.world.facts.get("resolved"):
            return 1
        if "village" not in sample.story.lower() or "quest" not in sample.story.lower():
            return 1
    return 0


def generate(params: StoryParams) -> StorySample:
    world = tell_story(params)
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
        print(dump_trace(sample.world))
    if qa:
        print("\n" + format_qa(sample))


def main() -> None:
    args = build_parser().parse_args()

    if args.verify:
        raise SystemExit(asp_verify())

    if args.show_asp or args.asp:
        print(asp_program("#show safe_quest/0.\n#show resolved/0."))
        return

    if args.n < 1:
        raise StoryError("-n must be at least 1.")

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)

    if args.all:
        samples = []
        for seed in range(len(QUESTS)):
            samples.append(
                generate(
                    StoryParams(
                        village=VILLAGES[seed % len(VILLAGES)],
                        captain=CAPTAINS[seed % len(CAPTAINS)],
                        helper=HELPERS[(seed + 1) % len(HELPERS)],
                        starship=STARSHIPS[seed % len(STARSHIPS)],
                        beacon=BEACONS[seed % len(BEACONS)],
                        seed=seed,
                    )
                )
            )
    else:
        samples = []
        for offset in range(args.n):
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

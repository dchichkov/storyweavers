#!/usr/bin/env python3
"""
A small pirate tale about concentric rings, dwindling fuel, and a quest saved
when a misunderstanding is cleared away.

The world models a little ship, its crew, a ringed sea marker, and a fuel
lantern.  Their meters and memes change as the quest moves from confusion to
careful listening.
"""

from __future__ import annotations

import argparse
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
class Entity:
    id: str
    kind: str
    label: str
    location: str = ""
    owner: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def __post_init__(self) -> None:
        for key in ("fuel", "distance", "danger", "confusion", "trust", "hope"):
            self.meters.setdefault(key, 0.0)
        for key in ("quest", "worry", "courage", "patience", "pride"):
            self.memes.setdefault(key, 0.0)


@dataclass
class StoryParams:
    captain: str
    deckhand: str
    ship: str = "the Little Comet"
    sea: str = "the Blueglass Sea"
    ring_pattern: str = "three concentric rings"
    fuel_kind: str = "blue lantern fuel"
    route: str = "the quiet northern passage"
    variation: int = 0
    seed: Optional[int] = None


@dataclass(frozen=True)
class Route:
    key: str
    landmark: str
    rings: str
    clue: str
    false_belief: str
    true_meaning: str
    danger: str
    ending: str


ROUTES = [
    Route(
        "moon",
        "Moonwake Reef",
        "three concentric rings of pale coral",
        "the smallest ring points toward water that glows at night",
        "the captain thought the outer ring marked the way in",
        "the rings were a map: start outside, then follow each curve toward the moonlit channel",
        "a sandbar waited beyond the wrong turn",
        "the ship reached the reef as silver fish flashed beneath its keel",
    ),
    Route(
        "bell",
        "Bellfin Island",
        "four concentric rings cut into a black stone",
        "the bell-shaped center means safe anchorage",
        "the deckhand believed every ring was a separate island",
        "the rings all belonged to one marker and the center was the harbor",
        "a fog bank hid the island's sharp eastern rocks",
        "the crew dropped anchor beneath a warm island bell",
    ),
    Route(
        "star",
        "Starling Shoal",
        "five concentric circles painted on a red buoy",
        "the broken line in the middle faces the hidden channel",
        "the captain thought the broken line was a crack to avoid",
        "it was an arrow showing where the shoal opened",
        "a crosscurrent tugged hard at the ship",
        "the ship slipped through while stars appeared one by one",
    ),
    Route(
        "whale",
        "Whalebone Point",
        "two broad concentric rings around a bone-white post",
        "the inner ring marks the place where fresh water rises",
        "the deckhand thought the outer ring marked the spring",
        "the crew nearly sailed past the only drinking water",
        "clear water bubbled into every cup before dawn",
    ),
]

CAPTAINS = ["Luna", "Mara", "Sable", "Nell", "Piper", "Iris"]
DECKHANDS = ["Finn", "Cato", "Bram", "Ollie", "Rook", "Tavi"]


class World:
    def __init__(self, params: StoryParams) -> None:
        self.params = params
        self.entities: dict[str, Entity] = {}
        self.parts: list[list[str]] = [[]]
        self.facts: dict[str, object] = {}

    def add(self, entity: Entity) -> None:
        self.entities[entity.id] = entity

    def say(self, text: str) -> None:
        self.parts[-1].append(text)

    def paragraph(self) -> None:
        if self.parts[-1]:
            self.parts.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(part) for part in self.parts if part)


def setup_world(params: StoryParams, route: Route) -> World:
    world = World(params)
    world.add(Entity("captain", "character", params.captain, "deck"))
    world.add(Entity("deckhand", "character", params.deckhand, "deck"))
    world.add(Entity("ship", "ship", params.ship, "sea", owner=params.captain))
    world.add(Entity("fuel", "resource", params.fuel_kind, "fuel locker"))
    world.add(Entity("marker", "landmark", route.landmark, "horizon"))
    ship = world.entities["ship"]
    fuel = world.entities["fuel"]
    ship.meters["fuel"] = 6
    ship.meters["distance"] = 0
    ship.meters["danger"] = 0
    fuel.meters["fuel"] = 6
    for person in ("captain", "deckhand"):
        world.entities[person].memes["quest"] = 1
        world.entities[person].meters["trust"] = 1
    return world


def tell_story(world: World, route: Route) -> None:
    p = world.params
    captain = world.entities["captain"]
    deckhand = world.entities["deckhand"]
    ship = world.entities["ship"]
    fuel = world.entities["fuel"]

    world.say(
        f"Captain {p.captain} sailed {p.ship} across {p.sea}, with "
        f"{p.deckhand} at the wheel and a quest tucked beneath the compass."
    )
    world.say(
        f"They sought {route.landmark}, where an old sailor promised a safe "
        f"passage and a bright surprise."
    )
    world.say(
        f"At noon, the lookout spotted {route.rings} floating beside the route."
    )
    world.say(
        f'"There is our guide," said {p.captain}. '
        f'"Steer toward the outer ring."'
    )
    world.say(
        f'"The center is closer," answered {p.deckhand}. '
        f'"I think the middle ring is the way."'
    )

    world.paragraph()
    world.say(
        f"The two pirates had a misunderstanding. {p.captain} heard "
        f"{p.deckhand} say to turn away from the marker, while {p.deckhand} "
        f"meant to follow its rings inward."
    )
    world.say(
        f"They chose different turns, and {p.ship} began to circle the "
        f"concentric sign instead of crossing the water."
    )
    ship.meters["fuel"] -= 2
    fuel.meters["fuel"] -= 2
    ship.meters["distance"] += 1
    ship.meters["danger"] += 1
    captain.memes["worry"] += 1
    deckhand.memes["worry"] += 1
    world.say(
        f"The fuel lantern burned lower. {p.captain} frowned and cried, "
        f'"You told me to leave the rings!"'
    )
    world.say(
        f'"No," said {p.deckhand}. "I said the center was our next mark. '
        f'We are looking at the same clue from opposite sides."'
    )

    world.paragraph()
    world.say(
        f"Captain {p.captain} lowered the spyglass. Instead of shouting, "
        f"the captain asked, " + f'"Show me what you mean, {p.deckhand}."'
    )
    world.say(
        f"{p.deckhand} traced the rings in the air. "
        f'"Start at the wide edge," they explained, '
        f'"then follow every curve until the center opens."'
    )
    world.say(
        f"The clue became plain: {route.clue}. "
        f"{route.true_meaning.capitalize()}."
    )
    captain.memes["patience"] += 1
    deckhand.memes["patience"] += 1
    captain.meters["trust"] += 1
    deckhand.meters["trust"] += 1
    captain.memes["courage"] += 1
    deckhand.memes["courage"] += 1
    ship.meters["fuel"] -= 1
    fuel.meters["fuel"] -= 1
    ship.meters["distance"] += 3
    ship.meters["danger"] = max(0, ship.meters["danger"] - 1)
    world.say(
        f"They trimmed the sail, saved the remaining {p.fuel_kind}, and "
        f"guided {p.ship} along the true route."
    )

    world.paragraph()
    world.say(
        f"At sunset, {route.ending}. The quest was safe because the pirates "
        f"had stopped guessing and started listening."
    )
    world.say(
        f"{p.captain} grinned at {p.deckhand}. "
        f'"A map can have many circles," the captain said, '
        f'"but a crew needs one meaning."'
    )
    world.say(
        f'"And one clear question," replied {p.deckhand}. '
        f'"Next time, I will ask before I turn the wheel."'
    )
    world.say(
        f"The last blue flame trembled in its cup, while the concentric rings "
        f"shone behind them like a quiet promise."
    )

    world.facts.update(
        route=route,
        fuel_left=int(fuel.meters["fuel"]),
        misunderstanding=True,
        resolved=True,
        ending=route.ending,
        clue=route.clue,
        true_meaning=route.true_meaning,
    )


def story_qa(world: World) -> list[QAItem]:
    p = world.params
    route: Route = world.facts["route"]
    return [
        QAItem(
            "Who led the quest?",
            f"Captain {p.captain} led the quest, with {p.deckhand} helping aboard {p.ship}.",
        ),
        QAItem(
            "What did the pirates find on the sea?",
            f"They found {route.rings} near {route.landmark}.",
        ),
        QAItem(
            "What was the misunderstanding?",
            f"{p.captain} thought {p.deckhand} meant to leave the marker, but {p.deckhand} meant to follow the rings inward.",
        ),
        QAItem(
            "Why did the fuel matter?",
            f"The ship spent fuel while circling the marker, so the crew had to save the remaining {world.facts['fuel_left']} units for the true route.",
        ),
        QAItem(
            "How did the pirates solve the problem?",
            f"They stopped arguing, asked for an explanation, and learned that {route.true_meaning}.",
        ),
        QAItem(
            "How did the quest end?",
            f"{route.ending.capitalize()} The quest succeeded because the crew listened carefully.",
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            "What does concentric mean?",
            "Concentric shapes share the same center, like rings drawn inside one another.",
        ),
        QAItem(
            "What is fuel?",
            "Fuel is a material used to provide energy for a machine, vehicle, or fire.",
        ),
        QAItem(
            "What is a quest?",
            "A quest is an important journey or task undertaken to reach a goal.",
        ),
        QAItem(
            "What is a misunderstanding?",
            "A misunderstanding happens when people understand the same words or event in different ways.",
        ),
    ]


def generation_prompts() -> list[str]:
    return [
        "Write a child-friendly pirate tale about a quest guided by concentric rings and threatened by dwindling fuel.",
        "Tell a pirate story in which a misunderstanding changes the route, then careful listening saves the quest.",
        "Create a short adventure with a ship, fuel, a concentric sea marker, and a spoken conversation that resolves confusion.",
    ]


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Pirate tale world about a concentric marker, fuel, and a repaired misunderstanding."
    )
    parser.add_argument("--captain")
    parser.add_argument("--deckhand")
    parser.add_argument("--ship", default="the Little Comet")
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
    captain = args.captain or rng.choice(CAPTAINS)
    deckhand = args.deckhand or rng.choice(DECKHANDS)
    if captain == deckhand:
        raise StoryError("The captain and deckhand must have different names.")
    route = rng.choice(ROUTES)
    return StoryParams(
        captain=captain,
        deckhand=deckhand,
        ship=args.ship,
        ring_pattern=route.rings,
        variation=rng.getrandbits(63),
        seed=args.seed,
    )


def generate(params: StoryParams) -> StorySample:
    route = next(route for route in ROUTES if route.rings == params.ring_pattern)
    world = setup_world(params, route)
    tell_story(world)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(),
        story_qa=story_qa(world),
        world_qa=world_qa(world),
        world=world,
    )


ASP_RULES = r"""
child(captain).
child(deckhand).
quest_active.
marker(concentric_rings).
fuel_available.
misunderstanding.
asks_question.
follows_rings.
resolved.

misunderstanding_resolved :-
    misunderstanding,
    asks_question,
    follows_rings,
    fuel_available.

successful_quest :-
    quest_active,
    marker(concentric_rings),
    misunderstanding_resolved.

#show misunderstanding_resolved/0.
#show successful_quest/0.
"""


def asp_facts() -> str:
    import asp
    return "\n".join(
        [
            asp.fact("child", "captain"),
            asp.fact("child", "deckhand"),
            asp.fact("quest_active"),
            asp.fact("marker", "concentric_rings"),
            asp.fact("fuel_available"),
            asp.fact("misunderstanding"),
            asp.fact("asks_question"),
            asp.fact("follows_rings"),
            asp.fact("resolved"),
        ]
    )


def asp_program(show: str = "#show successful_quest/0.") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program())
    names = {symbol.name for symbol in model}
    if "successful_quest" not in names or "misunderstanding_resolved" not in names:
        print("MISMATCH: ASP twin did not resolve the pirate quest.")
        return 1
    for params in curated_params():
        sample = generate(params)
        if "misunderstanding" not in sample.story.lower():
            print("MISMATCH: generated story omitted the misunderstanding.")
            return 1
        if "fuel" not in sample.story.lower():
            print("MISMATCH: generated story omitted fuel.")
            return 1
    print("OK: ASP and Python agree that careful listening saves the quest.")
    return 0


def curated_params() -> list[StoryParams]:
    return [
        StoryParams(
            "Luna",
            "Finn",
            ring_pattern=ROUTES[0].rings,
            variation=11,
        ),
        StoryParams(
            "Mara",
            "Cato",
            ring_pattern=ROUTES[1].rings,
            variation=22,
        ),
        StoryParams(
            "Sable",
            "Rook",
            ring_pattern=ROUTES[2].rings,
            variation=33,
        ),
    ]


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for entity in world.entities.values():
        meters = {k: v for k, v in entity.meters.items() if v}
        memes = {k: v for k, v in entity.memes.items() if v}
        parts = [f"kind={entity.kind}", f"location={entity.location}"]
        if meters:
            parts.append(f"meters={meters}")
        if memes:
            parts.append(f"memes={memes}")
        lines.append(f"{entity.label}: " + " ".join(parts))
    return "\n".join(lines)


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    lines.extend(sample.prompts)
    lines.append("")
    lines.append("== story qa ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== world qa ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program())
        return
    if args.verify:
        raise SystemExit(asp_verify())

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    if args.all:
        samples = [generate(params) for params in curated_params()]
    else:
        samples = []
        for index in range(max(1, args.n)):
            rng = random.Random(base_seed + index)
            try:
                params = resolve_params(args, rng)
            except StoryError as error:
                print(error)
                return
            samples.append(generate(params))

    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([sample.to_dict() for sample in samples], indent=2, ensure_ascii=False))
        return

    for index, sample in enumerate(samples):
        print(sample.story)
        if args.trace and sample.world is not None:
            print()
            print(dump_trace(sample.world))
        if args.qa:
            print()
            print(format_qa(sample))
        if index < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""
A small Pirate Tale storyworld about a historic shutter, friendship, and solving
a practical problem together.
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

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, ROOT)
from results import QAItem, StoryError, StorySample  # noqa: E402


@dataclass
class Entity:
    id: str
    kind: str
    type: str
    label: str
    owner: Optional[str] = None
    carried_by: Optional[str] = None
    meters: dict[str, float] = field(
        default_factory=lambda: {
            "distance": 0.0,
            "strength": 0.0,
            "safety": 0.0,
            "readiness": 0.0,
        }
    )
    memes: dict[str, float] = field(
        default_factory=lambda: {
            "worry": 0.0,
            "courage": 0.0,
            "trust": 0.0,
            "joy": 0.0,
            "relief": 0.0,
        }
    )


@dataclass
class Setting:
    place: str
    weather: str
    landmark: str


@dataclass
class StoryParams:
    captain: str
    captain_type: str
    friend: str
    friend_type: str
    shutter_name: str
    island: str
    scenario_index: int = 0
    detail_variant: int = 0
    seed: Optional[int] = None


SCENARIOS = [
    {
        "place": "the old lighthouse on Lantern Island",
        "weather": "a hard sea wind",
        "landmark": "the black-and-gold lighthouse",
        "problem": "The historic wooden shutter had come loose above the lantern room.",
        "risk": "Without it, flying spray could crack the beacon glass before nightfall.",
        "clue": "A line of blue paint on the deck matched a stripe on the shutter hinge.",
        "wrong": "The captain tried to pull the shutter down alone, but the wind swung it wider.",
        "method": "They tied a rope to the rail, used a spare oar as a brace, and lowered the shutter one careful handspan at a time.",
        "result": "The historic shutter settled back over the lantern window and kept the beacon dry.",
        "lesson": "a trusted friend can make a dangerous job manageable",
        "image": "the lighthouse beam swept over calm water while the repaired shutter rested snugly beside it",
        "dialogue": "A captain may choose the course, but a friend can steady the ship",
    },
    {
        "place": "the historic fort at Gull Rock",
        "weather": "a gray tide rolling beneath the cliffs",
        "landmark": "the fort's cracked red flag tower",
        "problem": "A storm had jammed the historic shutter of the signal room.",
        "risk": "The crew could not see the harbor clearly enough to warn a fishing boat.",
        "clue": "The friend noticed that the lower hinge moved whenever the bell rope was pulled.",
        "wrong": "They pushed at the shutter from the wrong side, wedging it tighter in its frame.",
        "method": "They rang the bell to lift the rope, slipped a flat plank beneath the hinge, and eased the shutter open together.",
        "result": "The signal keeper could see the harbor and raise a safe-weather flag.",
        "lesson": "careful observation is stronger than stubborn force",
        "image": "a green flag snapped above the fort as the fishing boat crossed the bright channel",
        "dialogue": "Let us watch what the hinge is telling us before we push again",
    },
    {
        "place": "the museum ship Starling",
        "weather": "warm rain drumming on the deck",
        "landmark": "the ship's carved wooden stern",
        "problem": "The historic cabin shutter was swollen shut, trapping a box of old maps inside.",
        "risk": "The damp air could ruin the maps before the museum keeper arrived.",
        "clue": "The friend found dry candle wax along one edge of the frame.",
        "wrong": "The captain hammered the center, and a small crack appeared in the old wood.",
        "method": "They warmed the frame with a lantern, rubbed wax along the edge, and pulled together when the tide lifted the ship.",
        "result": "The shutter opened without breaking, and the maps were carried into a dry chest.",
        "lesson": "protecting an old treasure may require patience instead of power",
        "image": "the preserved maps gleamed beneath glass while rain faded beyond the cabin",
        "dialogue": "Old wood remembers gentle hands better than loud blows",
    },
    {
        "place": "the ruined watchtower at Compass Cove",
        "weather": "fog curling around the rocks",
        "landmark": "a leaning watchtower above the cove",
        "problem": "The historic shutter hid the tower's compass, and the crew had lost their bearing.",
        "risk": "Sailing on a guessed direction could send the boat toward hidden reefs.",
        "clue": "The friend heard gulls calling from the open-water side of the tower.",
        "wrong": "The captain chose the brightest patch of fog, but it led toward the reef line.",
        "method": "They waited for the gull calls, marked the safe direction with chalk, and opened the shutter using a hooked boat pole.",
        "result": "The compass pointed them home through the fog.",
        "lesson": "good teamwork combines different kinds of knowledge",
        "image": "the compass needle steadied while the boat's lantern glowed beside the returning gulls",
        "dialogue": "Your ears found the water, and my hands can reach the shutter",
    },
    {
        "place": "the historic harbor archive",
        "weather": "a bright wind snapping the pennants",
        "landmark": "the archive's round stone tower",
        "problem": "A warped shutter covered the archive's only window, where the harbor chart was stored.",
        "risk": "The crew needed the chart before sailing around a newly exposed sandbar.",
        "clue": "The friend saw that the shutter was blocked by one fallen brass pin.",
        "wrong": "They searched the whole room for a secret key that had never been needed.",
        "method": "They swept the floor, found the pin beneath a chest, and used it to reset the hinge while holding the shutter steady.",
        "result": "The chart became visible, and the crew marked the sandbar before casting off.",
        "lesson": "solving a problem starts with noticing what is actually in the way",
        "image": "the marked chart lay open beside a ready compass and a coil of clean rope",
        "dialogue": "The door is not locked, matey; one little pin is simply in the wrong place",
    },
]


CAPTAIN_NAMES = ["Luna", "Maris", "Captain Bea", "Nell", "Sable"]
CAPTAIN_TYPES = ["captain", "pirate", "sailor"]
FRIEND_NAMES = ["Pip", "Toby", "Mara", "Finn", "Cora"]
FRIEND_TYPES = ["deckhand", "parrot", "cartographer", "sailor", "shipwright"]
ISLANDS = ["Lantern Island", "Gull Rock", "Compass Cove", "Brasswater Bay"]


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.facts: dict[str, object] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.trace_log: list[str] = []

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
        return "\n\n".join(" ".join(part) for part in self.paragraphs if part)

    def log(self, text: str) -> None:
        self.trace_log.append(text)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Pirate Tale: a historic shutter, friendship, and a solved problem."
    )
    parser.add_argument("--captain")
    parser.add_argument("--captain-type")
    parser.add_argument("--friend")
    parser.add_argument("--friend-type")
    parser.add_argument("--shutter")
    parser.add_argument("--island")
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
    captain = args.captain or rng.choice(CAPTAIN_NAMES)
    captain_type = args.captain_type or rng.choice(CAPTAIN_TYPES)
    friend = args.friend or rng.choice(FRIEND_NAMES)
    friend_type = args.friend_type or rng.choice(FRIEND_TYPES)
    shutter_name = args.shutter or rng.choice(
        ["the harbor shutter", "the old shutter", "the brass-hinged shutter"]
    )
    island = args.island or rng.choice(ISLANDS)
    if captain.casefold() == friend.casefold():
        raise StoryError("captain and friend must have different names")
    if captain_type not in CAPTAIN_TYPES:
        raise StoryError(f"unknown captain type: {captain_type}")
    if friend_type not in FRIEND_TYPES:
        raise StoryError(f"unknown friend type: {friend_type}")
    return StoryParams(
        captain=captain,
        captain_type=captain_type,
        friend=friend,
        friend_type=friend_type,
        shutter_name=shutter_name,
        island=island,
        scenario_index=rng.randrange(len(SCENARIOS)),
        detail_variant=rng.randrange(10000),
    )


def tell(params: StoryParams) -> World:
    scenario = SCENARIOS[params.scenario_index % len(SCENARIOS)]
    setting = Setting(
        place=scenario["place"],
        weather=scenario["weather"],
        landmark=scenario["landmark"],
    )
    world = World(setting)

    captain = world.add(
        Entity(
            id="captain",
            kind="person",
            type=params.captain_type,
            label=params.captain,
        )
    )
    friend = world.add(
        Entity(
            id="friend",
            kind="person",
            type=params.friend_type,
            label=params.friend,
        )
    )
    shutter = world.add(
        Entity(
            id="shutter",
            kind="object",
            type="historic_shutter",
            label=params.shutter_name,
        )
    )
    ship = world.add(
        Entity(id="ship", kind="vehicle", type="sailing_ship", label="the Sea Finch")
    )

    world.facts.update(
        captain=captain,
        friend=friend,
        shutter=shutter,
        ship=ship,
        scenario=scenario,
    )

    captain.memes["courage"] = 1.0
    friend.memes["trust"] = 1.0
    shutter.meters["readiness"] = 0.2
    ship.meters["safety"] = 0.5

    openings = [
        f"At dawn, {params.captain} the {params.captain_type} sailed the Sea Finch toward {params.island}.",
        f"The Sea Finch reached {params.island} while {scenario['weather']} curled around {scenario['landmark']}.",
        f"Before the tide turned, {params.captain} guided the Sea Finch to {params.island}.",
    ]
    world.say(openings[params.detail_variant % len(openings)])
    world.say(
        f"They had come to inspect {params.shutter_name}, a historic wooden panel that protected an important room."
    )
    world.say(
        f"{params.friend} the {params.friend_type} climbed beside the captain, carrying a coil of rope and a small tool pouch."
    )
    world.para()

    captain.memes["worry"] += 1.0
    shutter.meters["distance"] = 1.0
    world.say(scenario["problem"])
    world.say(scenario["risk"])
    world.say(f'"We have little time," {params.captain} said. "I can fix it alone."')
    world.say(
        f'"You do not have to," {params.friend} replied. "Tell me what you see, and I will help you choose a safer way."'
    )
    world.say(scenario["wrong"])
    world.para()

    friend.memes["trust"] += 1.0
    captain.memes["worry"] -= 0.5
    world.say(scenario["clue"])
    world.say(
        f"{params.captain} listened to {params.friend}, and the two friends studied the hinge before touching the old wood again."
    )
    world.say(scenario["method"])
    world.para()

    shutter.meters["safety"] = 1.0
    shutter.meters["readiness"] = 1.0
    shutter.memes["relief"] = 1.0
    captain.memes["trust"] += 1.0
    friend.memes["joy"] += 1.0
    ship.meters["safety"] = 1.0
    shutter.carried_by = "friend"

    world.say(scenario["result"])
    world.say(
        f'"That was fine seamanship," {params.captain} said. "{params.friend}, your careful eye saved the day."'
    )
    world.say(
        f'"And your listening made room for my idea," {params.friend} answered. "That is what friends are for."'
    )
    world.para()

    captain.memes["relief"] += 1.0
    world.say(
        f"The crew checked the room together, then returned to the Sea Finch with the problem solved."
    )
    world.say(f"{params.captain} understood that {scenario['lesson']}.")
    world.say(f"By sunset, {scenario['image']}.")
    world.log(f"scenario={params.scenario_index % len(SCENARIOS)}")
    world.log("historic_shutter_repaired=true")
    world.log("friendship_used_for_problem_solving=true")
    return world


def generation_prompts(world: World) -> list[str]:
    captain: Entity = world.facts["captain"]  # type: ignore[assignment]
    friend: Entity = world.facts["friend"]  # type: ignore[assignment]
    shutter: Entity = world.facts["shutter"]  # type: ignore[assignment]
    scenario: dict[str, str] = world.facts["scenario"]  # type: ignore[assignment]
    return [
        f"Write a child-friendly Pirate Tale about {captain.label} and {friend.label} repairing {shutter.label}.",
        f"Tell a story set at {world.setting.place} where friendship helps solve this problem: {scenario['problem']}",
        f'Include the words "historic" and "shutter", plus a brief spoken exchange that changes the sailors\' plan.',
    ]


def story_qa(world: World) -> list[QAItem]:
    captain: Entity = world.facts["captain"]  # type: ignore[assignment]
    friend: Entity = world.facts["friend"]  # type: ignore[assignment]
    shutter: Entity = world.facts["shutter"]  # type: ignore[assignment]
    scenario: dict[str, str] = world.facts["scenario"]  # type: ignore[assignment]
    return [
        QAItem(
            question=f"Why did {captain.label} and {friend.label} visit {world.setting.place}?",
            answer=f"They visited {world.setting.place} to repair {shutter.label}, the historic shutter protecting an important room.",
        ),
        QAItem(
            question=f"What danger did the broken shutter cause?",
            answer=f"{scenario['risk']}",
        ),
        QAItem(
            question=f"What clue helped the friends solve the problem?",
            answer=f"{scenario['clue']} The clue showed them where to work instead of using force.",
        ),
        QAItem(
            question=f"How did the friends repair the shutter?",
            answer=f"{scenario['method']} Their shared plan protected the old wood and made the room safe.",
        ),
        QAItem(
            question="What did the pirate friends learn?",
            answer=f"They learned that {scenario['lesson']}. Listening to each other made the solution safer.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a shutter?",
            answer="A shutter is a panel that covers a window or opening. It can protect a room from weather, light, or danger.",
        ),
        QAItem(
            question="What does historic mean?",
            answer="Historic means important or interesting because it belongs to the past and helps tell us about earlier times.",
        ),
        QAItem(
            question="How does friendship help solve problems?",
            answer="Friendship helps people listen, share ideas, encourage one another, and combine different skills to find a safer solution.",
        ),
        QAItem(
            question="Why should old objects be handled carefully?",
            answer="Old objects may be fragile or valuable, so careful handling can preserve them while still allowing people to use or study them.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    lines.extend(sample.prompts)
    lines.extend(["", "== story qa =="])
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.extend(["", "== world qa =="])
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- trace ---"]
    for entity in world.entities.values():
        meters = {k: round(v, 2) for k, v in entity.meters.items() if v}
        memes = {k: round(v, 2) for k, v in entity.memes.items() if v}
        details = [f"type={entity.type}"]
        if meters:
            details.append(f"meters={meters}")
        if memes:
            details.append(f"memes={memes}")
        lines.append(f"{entity.id}: " + ", ".join(details))
    lines.extend(world.trace_log)
    return "\n".join(lines)


ASP_RULES = r"""
entity(captain).
entity(friend).
entity(shutter).
entity(ship).

repaired(shutter) :- braced(shutter), worked_together(captain,friend), historic(shutter).
safe(ship) :- repaired(shutter).
friendship_success :- listened(captain,friend), worked_together(captain,friend).
happy_end :- safe(ship), friendship_success.

#show repaired/1.
#show safe/1.
#show friendship_success/0.
#show happy_end/0.
"""


def asp_facts() -> str:
    import asp

    return "\n".join(
        [
            asp.fact("historic", "shutter"),
            asp.fact("braced", "shutter"),
            asp.fact("worked_together", "captain", "friend"),
            asp.fact("listened", "captain", "friend"),
        ]
    )


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp

    model = asp.one_model(
        asp_program(
            "#show repaired/1. #show safe/1. "
            "#show friendship_success/0. #show happy_end/0."
        )
    )
    actual = {f"{symbol.name}/{len(symbol.arguments)}" for symbol in model}
    expected = {
        "repaired/1",
        "safe/1",
        "friendship_success/0",
        "happy_end/0",
    }
    if actual != expected:
        print(f"MISMATCH: {sorted(actual)} != {sorted(expected)}")
        return 1
    for params in CURATED:
        sample = generate(params)
        if "historic" not in sample.story or "shutter" not in sample.story:
            print("MISMATCH: generated story omitted required seed words")
            return 1
        if not sample.story_qa:
            print("MISMATCH: generated story has no story QA")
            return 1
    print("OK: ASP parity check and generated-story checks passed.")
    return 0


def generate(params: StoryParams) -> StorySample:
    world = tell(params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
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
        print()
        print(dump_trace(sample.world))
    if qa:
        print()
        print(format_qa(sample))


CURATED = [
    StoryParams(
        captain="Luna",
        captain_type="captain",
        friend="Pip",
        friend_type="deckhand",
        shutter_name="the old shutter",
        island="Lantern Island",
        scenario_index=0,
        detail_variant=1,
    ),
    StoryParams(
        captain="Maris",
        captain_type="pirate",
        friend="Cora",
        friend_type="shipwright",
        shutter_name="the brass-hinged shutter",
        island="Gull Rock",
        scenario_index=1,
        detail_variant=4,
    ),
    StoryParams(
        captain="Nell",
        captain_type="sailor",
        friend="Finn",
        friend_type="cartographer",
        shutter_name="the harbor shutter",
        island="Compass Cove",
        scenario_index=3,
        detail_variant=7,
    ),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(
            asp_program(
                "#show repaired/1. #show safe/1. "
                "#show friendship_success/0. #show happy_end/0."
            )
        )
        return

    if args.verify:
        sys.exit(asp_verify())

    if args.asp:
        import asp

        model = asp.one_model(
            asp_program(
                "#show repaired/1. #show safe/1. "
                "#show friendship_success/0. #show happy_end/0."
            )
        )
        print("ASP model:", " ".join(str(atom) for atom in model))
        return

    if args.n < 1:
        raise StoryError("-n must be at least 1")

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(params) for params in CURATED]
    else:
        seen: set[str] = set()
        attempt = 0
        while len(samples) < args.n and attempt < max(args.n * 20, 20):
            rng = random.Random(base_seed + attempt)
            params = resolve_params(args, rng)
            params.seed = base_seed + attempt
            attempt += 1
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
        header = (
            f"### variant {index + 1}"
            if len(samples) > 1 and not args.all
            else ""
        )
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if index < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()

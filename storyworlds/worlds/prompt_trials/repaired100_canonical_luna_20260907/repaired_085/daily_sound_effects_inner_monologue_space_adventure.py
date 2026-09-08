#!/usr/bin/env python3
"""A small dialogue-rich space adventure about a daily repair mission."""

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
    label: str
    owner: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def __post_init__(self) -> None:
        for key in ("power", "oxygen", "distance", "risk", "signal"):
            self.meters.setdefault(key, 0.0)
        for key in ("calm", "worry", "trust", "wonder", "relief"):
            self.memes.setdefault(key, 0.0)


@dataclass
class Ship:
    name: str
    location: str
    daily_route: str
    systems: dict[str, bool] = field(default_factory=dict)


@dataclass
class StoryParams:
    hero: str
    partner: str
    ship: str
    destination: str
    mission: str
    seed: Optional[int] = None


@dataclass(frozen=True)
class Mission:
    title: str
    hazard: str
    clue: str
    guess: str
    test: str
    cause: str
    action: str
    repair: str
    result: str
    lesson: str
    ending: str


MISSIONS = [
    Mission(
        "the quiet beacon",
        "the daily navigation beacon stopped answering",
        "its tiny status light blinked twice whenever the ship passed the moon",
        "the beacon had simply run out of power",
        "compared the beacon's blink with the ship's solar-panel log",
        "moon dust had covered one panel during a small meteor shower",
        "turned the ship toward the safe side of the moon and sent a repair drone",
        "brushed the dust away and tightened the beacon's loose solar hinge",
        "the beacon sent a bright route signal, and the crew reached the station before sunset",
        "A small repeated clue can guide a large decision",
        "the beacon blinked green while the stars gathered like silver buttons",
    ),
    Mission(
        "the singing antenna",
        "the daily radio check filled the cabin with a strange whistle",
        "the whistle rose whenever the antenna faced the blue planet",
        "a space creature was hiding in the signal",
        "rotated the antenna one careful degree at a time",
        "a loose antenna ring was vibrating in the planet's magnetic wind",
        "kept the ship in a safe orbit and asked mission control for a repair window",
        "secured the ring and recorded the clear frequency",
        "the daily message reached home with every word intact",
        "Sound can be evidence when someone listens carefully",
        "the repaired antenna whispered one clean beep into the dark",
    ),
    Mission(
        "the red warning tile",
        "a red tile flashed beside the daily water tank reading",
        "the tank level stayed full while the tile flashed only during a pump hum",
        "the ship was losing all its water",
        "checked the second gauge and listened beside the pump",
        "a loose sensor wire trembled against the pump housing",
        "switched to the backup gauge and called the engineer",
        "clipped the wire safely after the pump cooled",
        "the crew had enough water and no one had to panic",
        "A warning deserves attention, but not every warning means the worst",
        "fresh water hummed through the pipes as Earth rose beyond the window",
    ),
    Mission(
        "the drifting tool case",
        "the daily inspection found a tool case drifting outside the cargo hatch",
        "its tether was bright but its locking light was dark",
        "the case would float away forever",
        "matched the tether mark with the cargo hatch record",
        "the case had been clipped to a practice loop instead of the real anchor",
        "sealed the hatch and used the ship's robotic arm",
        "moved the case to the marked anchor and tested the lock",
        "the tools returned safely before the next repair began",
        "Labels and checks protect useful things in a weightless place",
        "the tool case clicked home as the cabin lights made a soft chime",
    ),
    Mission(
        "the sleepy engine",
        "the daily engine pulse sounded slower than usual",
        "the pulse slowed only when the ship crossed a cold shadow",
        "the engine was about to stop",
        "compared the pulse with the shadow map and the warm-side reading",
        "the cold shadow changed a harmless temperature sensor's timing",
        "held the ship on its planned course and asked the pilot to verify the readings",
        "warmed the sensor after leaving the shadow and reset its clock",
        "the engine kept its steady beat all the way to the moon station",
        "A patient comparison can separate danger from a harmless change",
        "the engine thumped steadily while the crew shared morning fruit",
    ),
]


ROUTES = [
    (
        "Every morning, the little ship made the same careful loop around the stars.",
        "The routine changed when one familiar sound or light refused to behave.",
        "By the next daily check, the crew had turned a worry into a useful habit.",
    ),
    (
        "The crew liked their daily spaceflight because each task had a clear place.",
        "Then a small signal made the cockpit feel much larger and much quieter.",
        "Their ordinary route became an adventure they could explain to the next crew.",
    ),
    (
        "Beyond the moon, the ship carried breakfast, tools, and a promise to return.",
        "A clue in the ship's sounds helped the astronauts choose care over haste.",
        "The stars looked the same, but the crew now noticed more of what they said.",
    ),
    (
        "The daily route began with a checklist and the gentle tick of cabin clocks.",
        "One odd detail interrupted the list and sent the crew toward a safe investigation.",
        "They finished the route with a repaired system and a calmer checklist.",
    ),
]


HEROES = ["Luna", "Mara", "Jon", "Tess", "Ravi", "Nia"]
PARTNERS = ["Sol", "Iris", "Beck", "Ari", "Milo", "Zee"]
SHIPS = ["Starling", "Comet Finch", "Blue Lantern", "Little Orbit"]
DESTINATIONS = ["the moon station", "the red research buoy", "the cloud observatory", "the far garden satellite"]
MISSIONS_TEXT = [
    "checking the daily navigation systems",
    "delivering seed packets to a research station",
    "recording the morning sounds of space",
    "carrying a fresh weather map to the moon station",
]


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


def choose_mission(seed: Optional[int]) -> tuple[Mission, tuple[str, str, str]]:
    value = 0 if seed is None else seed
    return MISSIONS[value % len(MISSIONS)], ROUTES[(value // len(MISSIONS)) % len(ROUTES)]


def tell_story(params: StoryParams) -> World:
    if params.hero == params.partner:
        raise StoryError("hero and partner must be different astronauts")
    if not params.destination.strip():
        raise StoryError("destination must not be empty")
    if not params.ship.strip():
        raise StoryError("ship must not be empty")

    mission, route = choose_mission(params.seed)
    ship = Ship(
        name=params.ship,
        location="high orbit",
        daily_route=params.destination,
        systems={"life_support": True, "navigation": True, "communication": True},
    )
    world = World(ship)
    hero = world.add(Entity(params.hero, "character", "astronaut", params.hero))
    partner = world.add(Entity(params.partner, "character", "astronaut", params.partner))
    vessel = world.add(Entity("vessel", "vehicle", "spacecraft", params.ship))
    hazard = world.add(Entity("mission_signal", "device", "space-system", mission.title))

    hero.memes.update(calm=0.7, worry=0.4, wonder=0.8)
    partner.memes.update(calm=0.8, trust=0.7)
    vessel.meters.update(power=0.9, oxygen=0.95, risk=0.2)
    hazard.meters.update(risk=0.7, signal=0.2)

    opening, turn, reflection = route
    world.say(opening)
    world.say(
        f"On the {params.ship}, {params.hero} was {params.mission} while "
        f"{params.partner} prepared the daily log for {params.destination}."
    )
    world.say(f'"Checklist ready," {params.partner} said. "The stars are waiting."')
    world.say(
        f'"And the ship is listening," {params.hero} replied. '
        f'"Let us make this daily check count."'
    )
    world.say(f"Then the cockpit announced {mission.hazard}.")
    world.say(f"[BEEP-BEEP] A small warning light pulsed beside the main screen.")
    world.say(
        f"{params.hero} thought, *If I choose too quickly, I might turn a small trouble "
        f"into a dangerous one.*"
    )
    world.say(f'"My first thought is that {mission.guess}," {params.hero} said.')
    world.say(f'"Maybe," {params.partner} answered, "but what does the clue tell us?"')
    world.say(turn)
    world.say(f"They observed that {mission.clue}.")
    world.say(f"[CLICK... HUM...] The ship answered as they {mission.test}.")
    world.say(
        f"The comparison showed that {mission.cause}. "
        f"{params.hero} took a slow breath and marked the finding in the daily log."
    )
    world.say(f'"Now we know what to do," {params.partner} said.')
    world.say(f'"Carefully, and together," {params.hero} replied.')
    world.say(
        f"They {mission.action}. The astronauts stayed inside the safe procedure "
        f"while the ship kept its protective systems running."
    )
    world.say(f"Afterward, they {mission.repair}.")
    world.say(f"[WHIRR... BEEP!] The repaired system answered with a steady signal.")
    world.say(f"As a result, {mission.result}.")
    world.say(f'"{mission.lesson}," {params.partner} said.')
    world.say(
        f"{params.hero} smiled. *The daily checklist is not a cage,* "
        f"{params.hero} thought. *It is a map that helps us notice the stars.*"
    )
    world.say(reflection)
    world.say(f"At the end of the route, {mission.ending}")

    hero.memes.update(calm=1.0, worry=0.0, relief=1.0)
    partner.memes.update(trust=1.0, relief=1.0)
    vessel.meters.update(risk=0.0, signal=1.0)
    hazard.meters.update(risk=0.0, signal=1.0)

    world.facts.update(
        hero=hero,
        partner=partner,
        vessel=vessel,
        hazard=hazard,
        mission=mission,
        clue=mission.clue,
        cause=mission.cause,
        action=mission.action,
        repair=mission.repair,
        result=mission.result,
        lesson=mission.lesson,
        resolved=True,
        child_safe=True,
    )
    return world


def generation_prompts(world: World) -> list[str]:
    facts = world.facts
    mission = facts["mission"]
    hero = facts["hero"]
    partner = facts["partner"]
    return [
        'Write a child-safe Space Adventure using the word "daily," sound effects, and inner monologue.',
        f"Tell a dialogue-rich daily space adventure about {hero.id} and {partner.id}.",
        f"Build the story around the clue that {mission.clue}",
        "Show how careful teamwork changes the astronauts' decision and repairs the ship.",
    ]


def story_qa(world: World) -> list[QAItem]:
    facts = world.facts
    hero = facts["hero"]
    partner = facts["partner"]
    mission = facts["mission"]
    return [
        QAItem(
            f"What was {hero.id} doing at the beginning?",
            f"{hero.id} was checking the daily ship systems while {partner.id} prepared the log for the destination.",
        ),
        QAItem(
            f"What first worried {hero.id} and {partner.id}?",
            f"They noticed that {mission.hazard}. A warning light and a sound made the routine check feel urgent.",
        ),
        QAItem(
            "What clue helped them understand the problem?",
            f"They noticed that {mission.clue}. That clue led them to compare observations instead of trusting a guess.",
        ),
        QAItem(
            "What caused the trouble?",
            f"They discovered that {mission.cause}. The astronauts learned this by using a safe test.",
        ),
        QAItem(
            "How did the astronauts solve the problem?",
            f"They {mission.action} Then they {mission.repair}, while keeping the ship's protective systems running.",
        ),
        QAItem(
            "What changed by the end of the adventure?",
            f"{mission.result} The crew also learned that {mission.lesson.lower()}.",
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            "What is a daily checklist?",
            "A daily checklist is a short list of tasks completed each day. It helps people notice changes and remember important safety steps.",
        ),
        QAItem(
            "Why are sound effects useful in a space story?",
            "Sound effects make actions easier to imagine. A beep, click, or hum can also give characters a clue about what a machine is doing.",
        ),
        QAItem(
            "What is inner monologue?",
            "Inner monologue is a character's private thought. It lets readers understand what the character is considering without replacing spoken conversation.",
        ),
        QAItem(
            "Why should astronauts compare clues before acting?",
            "Comparing clues helps astronauts tell a real danger from a harmless change. It supports careful choices and protects the crew and spacecraft.",
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
    lines = ["--- trace ---", f"ship: {world.ship.name} location={world.ship.location}"]
    for entity in world.entities.values():
        meters = {k: round(v, 2) for k, v in entity.meters.items() if v}
        memes = {k: round(v, 2) for k, v in entity.memes.items() if v}
        lines.append(
            f"{entity.id}: kind={entity.kind} type={entity.type} "
            f"meters={meters} memes={memes}"
        )
    mission = world.facts["mission"]
    lines.append(f"mission: {mission.title}; resolved={world.facts['resolved']}")
    return "\n".join(lines)


HERO_NAMES = HEROES
PARTNER_NAMES = PARTNERS


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Daily sound-effects and inner-monologue Space Adventure storyworld."
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
    return parser


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    hero = rng.choice(HERO_NAMES)
    partners = [name for name in PARTNER_NAMES if name != hero]
    return StoryParams(
        hero=hero,
        partner=rng.choice(partners),
        ship=rng.choice(SHIPS),
        destination=rng.choice(DESTINATIONS),
        mission=rng.choice(MISSIONS_TEXT),
    )


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


ASP_RULES = r"""
place(high_orbit).
theme(daily).
feature(sound_effects).
feature(inner_monologue).
style(space_adventure).
system(navigation).
system(communication).
safe_mission :-
    theme(daily),
    feature(sound_effects),
    feature(inner_monologue),
    style(space_adventure),
    system(navigation),
    system(communication).
"""


def asp_facts() -> str:
    import asp

    facts = [
        asp.fact("place", "high_orbit"),
        asp.fact("theme", "daily"),
        asp.fact("feature", "sound_effects"),
        asp.fact("feature", "inner_monologue"),
        asp.fact("style", "space_adventure"),
        asp.fact("system", "navigation"),
        asp.fact("system", "communication"),
    ]
    return "\n".join(facts)


def asp_program(show: str = "") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    try:
        import asp

        symbols = asp.one_model(
            asp_program(
                "#show safe_mission/0.\n"
                "#show theme/1.\n"
                "#show feature/1."
            )
        )
        names = {str(symbol) for symbol in symbols}
        required = {
            "safe_mission",
            "theme(daily)",
            "feature(sound_effects)",
            "feature(inner_monologue)",
        }
        if not required.issubset(names):
            return 1

        for seed in range(8):
            rng = random.Random(seed)
            args = argparse.Namespace()
            params = resolve_params(args, rng)
            params.seed = seed
            sample = generate(params)
            if not sample.story or not sample.story_qa:
                return 1
            if "daily" not in sample.story.lower():
                return 1
            if "[BEEP-BEEP]" not in sample.story and "[CLICK" not in sample.story:
                return 1
            if "thought" not in sample.story:
                return 1
        return 0
    except Exception:
        return 1


def main() -> None:
    args = build_parser().parse_args()

    if args.n < 1:
        raise SystemExit("-n must be at least 1")

    if args.show_asp or args.asp:
        print(asp_program("#show safe_mission/0."))
        return

    if args.verify:
        raise SystemExit(asp_verify())

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)

    if args.all:
        samples = [
            generate(
                StoryParams(
                    hero="Luna",
                    partner="Sol",
                    ship="Starling",
                    destination="the moon station",
                    mission="checking the daily navigation systems",
                    seed=index,
                )
            )
            for index in range(len(MISSIONS))
        ]
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
            print(
                json.dumps(
                    [sample.to_dict() for sample in samples],
                    indent=2,
                    ensure_ascii=False,
                )
            )
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

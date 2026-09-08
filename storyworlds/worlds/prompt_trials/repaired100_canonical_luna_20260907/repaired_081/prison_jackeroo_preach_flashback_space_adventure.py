#!/usr/bin/env python3
"""
Story world: a small space adventure about a prison, a jackeroo, and a
flashback that changes a risky plan into a careful rescue.
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
import random
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "storyworlds"))
from results import QAItem, StoryError, StorySample  # noqa: E402


@dataclass
class Entity:
    id: str
    kind: str
    label: str
    phrase: str = ""
    owner: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)


@dataclass
class Ship:
    name: str
    deck: str = "the quiet observation deck"
    prison: str = "the orbital holding station"
    outside: str = "the dark field beyond the airlock"


@dataclass
class StoryParams:
    ship: str = "Comet Lantern"
    hero_name: str = "Luna"
    helper_name: str = "Rafi"
    incident: str = "stuck_beacon"
    telling_mode: str = "flashback opening"
    seed: Optional[int] = None


class World:
    def __init__(self, ship: Ship) -> None:
        self.ship = ship
        self.entities: dict[str, Entity] = {}
        self.facts: dict[str, object] = {}
        self.lines: list[str] = []

    def add(self, entity: Entity) -> Entity:
        self.entities[entity.id] = entity
        return entity

    def say(self, text: str) -> None:
        self.lines.append(text)

    def render(self) -> str:
        return " ".join(self.lines)


SHIP_REGISTRY = {
    "Comet Lantern": Ship("Comet Lantern"),
    "Star Finch": Ship("Star Finch"),
    "Aurora Kite": Ship("Aurora Kite"),
}

HERO_NAMES = ["Luna", "Milo", "Nia", "Tao", "Remy"]
HELPER_NAMES = ["Rafi", "Ari", "Zia", "Juno", "Pax"]

INCIDENTS = {
    "stuck_beacon": {
        "premise": "A tiny guidance beacon had slipped into the old prison's service rail and blinked for help.",
        "mistake": "{hero} reached for it with a long metal hook, hoping to pull it free in one quick tug.",
        "clue": "{helper} noticed that the beacon's light pulsed whenever the station rotated, so its cable was caught under a moving panel.",
        "change": "They switched off the panel, used a soft loop, and guided the cable out before lifting the beacon.",
        "result": "The beacon came free without a spark, and its gentle signal led the repair shuttle home.",
        "lesson": "slow down when a rescue tool might make a hidden problem worse",
        "ending": "The old prison window glowed with the beacon's steady green light as the shuttle crossed the stars.",
    },
    "lost_message": {
        "premise": "A message from a frightened young traveler was trapped inside the prison's sealed communication box.",
        "mistake": "{hero} planned to force the box open before the message faded.",
        "clue": "{helper} remembered that the box received power only when the station's small moon passed overhead.",
        "change": "They waited for the moonlight, entered the release code, and copied the message before opening the box.",
        "result": "The traveler received an answer, and no one damaged the prison's emergency communicator.",
        "lesson": "patience can reveal a safer way to help",
        "ending": "A reply shimmered across the communicator while the moon slipped past the prison bars.",
    },
    "floating_supply": {
        "premise": "A supply case floated outside the prison, carrying medicine needed by a sick guard.",
        "mistake": "{hero} pushed off after it without checking the airlock tether.",
        "clue": "{helper} replayed a safety recording and saw a loose strap curl near the outer hatch.",
        "change": "They secured the strap, clipped two safety lines, and used a gentle air puff to guide the case back.",
        "result": "The medicine returned safely, and everyone stayed connected to the ship.",
        "lesson": "a brave rescue still needs a careful plan",
        "ending": "The medicine case rested beside the prison door as the crew watched stars move silently beyond it.",
    },
}

TELLING_MODES = [
    "flashback opening",
    "dialogue opening",
    "mystery opening",
    "problem first",
    "quiet reflection",
]

ASP_RULES = r"""
ship(S) :- ship_name(S).
prison(P) :- prison_name(P).
jackeroo(J) :- jackeroo_name(J).
flashback(F) :- flashback_name(F).
safe_rescue(R) :- rescue(R), prepared(R), careful(R).
learned(J) :- jackeroo(J), lesson_recorded(J).
signal_restored(P) :- prison(P), beacon_fixed(P).
"""


def asp_facts() -> str:
    import asp

    facts = []
    for name in SHIP_REGISTRY:
        facts.append(asp.fact("ship_name", name))
    facts.extend(
        [
            asp.fact("prison_name", "orbital_prison"),
            asp.fact("jackeroo_name", "jackeroo"),
            asp.fact("flashback_name", "safety_flashback"),
            asp.fact("rescue", "beacon_rescue"),
            asp.fact("prepared", "beacon_rescue"),
            asp.fact("careful", "beacon_rescue"),
            asp.fact("lesson_recorded", "jackeroo"),
            asp.fact("beacon_fixed", "orbital_prison"),
        ]
    )
    return "\n".join(facts)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp

    model = asp.one_model(
        asp_program(
            "#show prison/1.\n#show jackeroo/1.\n#show flashback/1.\n"
            "#show safe_rescue/1.\n#show learned/1.\n#show signal_restored/1."
        )
    )
    found = set()
    for symbol in model:
        args = []
        for arg in symbol.arguments:
            if arg.type.name == "Number":
                args.append(arg.number)
            elif arg.type.name == "String":
                args.append(arg.string)
            else:
                args.append(arg.name)
        found.add((symbol.name, tuple(args)))
    wanted = {
        ("prison", ("orbital_prison",)),
        ("jackeroo", ("jackeroo",)),
        ("flashback", ("safety_flashback",)),
        ("safe_rescue", ("beacon_rescue",)),
        ("learned", ("jackeroo",)),
        ("signal_restored", ("orbital_prison",)),
    }
    if found == wanted:
        print("OK: ASP and Python parity looks good.")
        return 0
    print("MISMATCH between ASP and Python reasoning.")
    print("ASP:", sorted(found))
    print("PY :", sorted(wanted))
    return 1


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="A space adventure about a prison, a jackeroo, and a useful flashback."
    )
    parser.add_argument("--ship", choices=SHIP_REGISTRY)
    parser.add_argument("--name")
    parser.add_argument("--helper")
    parser.add_argument("--incident", choices=INCIDENTS)
    parser.add_argument("--telling-mode", choices=TELLING_MODES)
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
    ship = args.ship or rng.choice(list(SHIP_REGISTRY))
    hero = args.name or rng.choice(HERO_NAMES)
    choices = [name for name in HELPER_NAMES if name != hero]
    helper = args.helper or rng.choice(choices)
    if helper == hero:
        raise StoryError("The helper must be a different character from the hero.")
    return StoryParams(
        ship=ship,
        hero_name=hero,
        helper_name=helper,
        incident=args.incident or rng.choice(list(INCIDENTS)),
        telling_mode=args.telling_mode or rng.choice(TELLING_MODES),
    )


def generate(params: StoryParams) -> StorySample:
    if params.ship not in SHIP_REGISTRY:
        raise StoryError(f"Unknown ship: {params.ship}")
    if params.incident not in INCIDENTS:
        raise StoryError(f"Unknown incident: {params.incident}")
    if params.hero_name == params.helper_name:
        raise StoryError("The hero and helper must be different characters.")

    ship = SHIP_REGISTRY[params.ship]
    incident = INCIDENTS[params.incident]
    rng = random.Random(
        params.seed
        if params.seed is not None
        else f"{params.ship}:{params.hero_name}:{params.helper_name}:{params.incident}"
    )
    world = World(ship)

    hero = world.add(
        Entity(
            "hero",
            "character",
            params.hero_name,
            phrase="the young jackeroo",
            meters={"courage": 1.0, "care": 0.0},
            memes={"worry": 0.0, "curiosity": 1.0},
        )
    )
    helper = world.add(
        Entity(
            "helper",
            "character",
            params.helper_name,
            phrase="the patient station guide",
            meters={"observation": 1.0},
            memes={"trust": 1.0},
        )
    )
    prison = world.add(
        Entity(
            "prison",
            "place",
            "orbital prison",
            phrase=ship.prison,
            meters={"safety": 0.5, "signal": 0.0},
            memes={"loneliness": 1.0, "hope": 0.0},
        )
    )
    beacon = world.add(
        Entity(
            "beacon",
            "device",
            "guidance beacon",
            phrase="a palm-sized guidance beacon",
            owner="prison",
            meters={"signal": 0.2, "risk": 1.0},
            memes={"urgency": 1.0},
        )
    )

    if params.telling_mode == "flashback opening":
        world.say(
            f"Before the rescue, {params.hero_name} remembered a lesson from an earlier flight near {ship.prison}."
        )
        world.say(
            f"In the flashback, a hurried pull had made a loose cable spark, so the young jackeroo had learned to stop and look."
        )
        world.say(
            f"“That memory may help us now,” {params.helper_name} said. “Tell me what you notice before you touch anything.”"
        )
        world.say(
            f"“I will,” {params.hero_name} replied. “The old prison deserves a careful rescue.”"
        )
    elif params.telling_mode == "dialogue opening":
        world.say(
            f"“The prison is calling,” {params.hero_name} said, as a small light blinked beyond {ship.deck}."
        )
        world.say(
            f"“Then we will answer carefully,” {params.helper_name} replied."
        )
    elif params.telling_mode == "mystery opening":
        world.say(
            f"A green blink appeared beside {ship.prison}, but no one could tell why the old prison was sending it."
        )
        world.say(
            f"“Something is trapped,” {params.hero_name} whispered. “We need a clue.”"
        )
    elif params.telling_mode == "problem first":
        world.say(incident["premise"].format(hero=params.hero_name, helper=params.helper_name))
    else:
        world.say(
            f"Stars shone beyond {ship.deck} while {params.hero_name}, the ship's young jackeroo, checked the route to {ship.prison}."
        )

    world.say(
        f"The prison's guidance beacon had slipped into a service rail, and its weak light trembled across the spacecraft window."
    )
    if params.telling_mode != "problem first":
        world.say(incident["premise"].format(hero=params.hero_name, helper=params.helper_name))

    world.say(incident["mistake"].format(hero=params.hero_name, helper=params.helper_name))
    hero.meters["courage"] += 1.0
    hero.memes["worry"] += 1.0
    beacon.meters["risk"] += 1.0
    prison.memes["hope"] = 0.5

    world.say(
        f'“Wait,” {params.helper_name} said. “We should not preach at the problem or pretend courage means rushing.”'
    )
    world.say(
        f'“You are right,” {params.hero_name} answered. “I can listen to the prison and learn from the flashback.”'
    )
    world.say(
        f"They watched the beacon through one slow turn of the station and compared its blinking with the movement of the rail."
    )
    world.say(incident["clue"].format(hero=params.hero_name, helper=params.helper_name))
    world.say(
        f"The flashback changed {params.hero_name}'s choice: instead of pulling harder, the jackeroo asked what the hidden cable needed."
    )

    beacon.meters["risk"] = 0.0
    beacon.meters["signal"] = 1.0
    prison.meters["safety"] = 1.0
    prison.meters["signal"] = 1.0
    prison.memes["hope"] = 1.0
    hero.meters["care"] = 1.0
    hero.memes["worry"] = 0.0
    hero.memes["pride"] = 1.0

    world.say(incident["change"].format(hero=params.hero_name, helper=params.helper_name))
    world.say(
        f"What had seemed like a stubborn prison mechanism became a problem they could solve by observing its rhythm."
    )
    world.say(incident["result"].format(hero=params.hero_name, helper=params.helper_name))
    world.say(
        f"{params.hero_name} did not preach a grand speech. Instead, the jackeroo showed the lesson by checking every tether before returning to the ship."
    )
    world.say(
        f'“A good rescue leaves people safer,” {params.hero_name} said.'
    )
    world.say(
        f'“And a good flashback can guide a better choice,” {params.helper_name} replied.'
    )
    world.say(incident["ending"].format(hero=params.hero_name, helper=params.helper_name))

    world.facts.update(
        hero=hero,
        helper=helper,
        prison=prison,
        beacon=beacon,
        flashback=True,
        transformed=True,
        lesson=incident["lesson"],
        clue=incident["clue"].format(hero=params.hero_name, helper=params.helper_name),
        change=incident["change"].format(hero=params.hero_name, helper=params.helper_name),
        result=incident["result"].format(hero=params.hero_name, helper=params.helper_name),
    )

    prompts = [
        f"Write a child-facing Space Adventure about {params.hero_name}, a jackeroo helping an orbital prison.",
        f"Use a Flashback to show how {params.hero_name} learns not to rush the rescue.",
        f"Include {params.helper_name}'s advice, a clear clue, a transformation, and a gentle lesson without preaching.",
    ]
    story_qa = [
        QAItem(
            "What problem did the prison have?",
            incident["premise"].format(hero=params.hero_name, helper=params.helper_name),
        ),
        QAItem(
            "What did the flashback teach the jackeroo?",
            f"The flashback taught {params.hero_name} to stop, observe hidden risks, and choose a safer rescue.",
        ),
        QAItem(
            "What clue explained the danger?",
            incident["clue"].format(hero=params.hero_name, helper=params.helper_name),
        ),
        QAItem(
            "How did the rescue change?",
            incident["change"].format(hero=params.hero_name, helper=params.helper_name),
        ),
        QAItem(
            "What proved that the rescue worked?",
            incident["result"].format(hero=params.hero_name, helper=params.helper_name),
        ),
    ]
    world_qa = [
        QAItem(
            "What is a prison?",
            "A prison is a place where people are kept under guard and cannot leave freely.",
        ),
        QAItem(
            "What is a jackeroo?",
            "A jackeroo is a young worker learning practical skills, especially on a ranch or station.",
        ),
        QAItem(
            "Why can a flashback help a story?",
            "A flashback shows an earlier event so a character can understand the present and make a wiser choice.",
        ),
    ]

    return StorySample(
        params=params,
        story=world.render(),
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
        print("--- trace ---")
        for key, entity in sample.world.entities.items():
            print(f"{key}: {entity.label} meters={entity.meters} memes={entity.memes}")
    if qa:
        print("\n== prompts ==")
        for prompt in sample.prompts:
            print(prompt)
        print("\n== story qa ==")
        for item in sample.story_qa:
            print(f"Q: {item.question}\nA: {item.answer}")
        print("\n== world qa ==")
        for item in sample.world_qa:
            print(f"Q: {item.question}\nA: {item.answer}")


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(
            asp_program(
                "#show prison/1.\n#show jackeroo/1.\n#show flashback/1.\n"
                "#show safe_rescue/1.\n#show learned/1.\n#show signal_restored/1."
            )
        )
        return
    if args.verify:
        raise SystemExit(asp_verify())

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        for index, incident in enumerate(INCIDENTS):
            params = StoryParams(
                ship=list(SHIP_REGISTRY)[index % len(SHIP_REGISTRY)],
                hero_name=HERO_NAMES[index % len(HERO_NAMES)],
                helper_name=HELPER_NAMES[index % len(HELPER_NAMES)],
                incident=incident,
                telling_mode=TELLING_MODES[index % len(TELLING_MODES)],
                seed=base_seed + index,
            )
            samples.append(generate(params))
    else:
        seen: set[str] = set()
        index = 0
        while len(samples) < max(1, args.n) and index < max(50, args.n * 20):
            params = resolve_params(args, random.Random(base_seed + index))
            params.seed = base_seed + index
            sample = generate(params)
            if sample.story not in seen:
                seen.add(sample.story)
                samples.append(sample)
            index += 1

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

#!/usr/bin/env python3
"""A small space-adventure story world about Mop, a newly born robot."""

from __future__ import annotations

import argparse
import json
import random
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Optional


STORYWORLDS_DIR = next(
    parent for parent in Path(__file__).resolve().parents if parent.name == "storyworlds"
)
sys.path.insert(0, str(STORYWORLDS_DIR))
from results import QAItem, StoryError, StorySample  # noqa: E402


@dataclass
class Entity:
    """A typed storyworld entity with physical meters and emotional memes."""

    name: str
    kind: str
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)


@dataclass(frozen=True)
class Incident:
    key: str
    title: str
    onset: str
    sound: str
    clue: str
    report: str
    engineer_reply: str
    repair: str
    repair_sound: str
    cause_answer: str
    spill_liters: float
    flow_liters_per_minute: float


@dataclass
class StoryParams:
    captain: str
    engineer: str
    ship: str
    destination: str
    incident: str
    seed: Optional[int] = None


@dataclass
class World:
    hero: Entity
    captain: Entity
    engineer: Entity
    ship: Entity
    beacon: Entity
    destination: str
    location: str
    incident: Incident
    deck_state: str = "slick"
    source_stopped: bool = False
    clue_found: bool = False
    mop_finished: bool = False
    mission_complete: bool = False
    facts: dict[str, Any] = field(default_factory=dict)

    def render(self) -> str:
        return str(self.facts.get("story", ""))


CREW_NAMES = ["Ari", "Bea", "Cy", "Dara", "Emi", "Finn"]
SHIP_NAMES = ["Starling", "Comet Kite", "Moon Finch"]
DESTINATIONS = ["Glass Crater", "Echo Ridge", "Lumen Basin"]

INCIDENTS: dict[str, Incident] = {
    "pouch": Incident(
        key="pouch",
        title="The Pouch Under the Crate",
        onset="A cargo crate shifted against its rack.",
        sound="KA-THUNK!",
        clue="A narrow blue trail ran from the puddle to a dented water pouch wedged under the crate.",
        report="The pouch under the crate is leaking; its cap is dented",
        engineer_reply="use the cargo hook to lift the crate and tighten the pouch cap",
        repair=(
            "Captain {captain} held the cargo hook steady while Engineer {engineer} "
            "lifted the crate, tightened the pouch cap, and set it upright in its rack."
        ),
        repair_sound="K-CLICK!",
        cause_answer=(
            "Mop followed a narrow blue trail to a dented water pouch beneath the cargo crate. "
            "The crew tightened the pouch cap, which stopped the leak."
        ),
        spill_liters=1.1,
        flow_liters_per_minute=0.25,
    ),
    "tube": Incident(
        key="tube",
        title="The Hissing Tube",
        onset="The air recycler trembled as the ship changed course.",
        sound="HSSSS... drip, drip!",
        clue=(
            "Fresh beads clung to the loose condensate tube beneath the recycler, "
            "which hissed with each small vibration."
        ),
        report="the loose tube under the recycler is still dripping",
        engineer_reply="close the marked valve and clip the tube back into its bracket",
        repair=(
            "Engineer {engineer} closed the marked valve, clipped the condensate tube "
            "back into its bracket, and checked the joint."
        ),
        repair_sound="CHAK-CLICK!",
        cause_answer=(
            "Mop spotted fresh beads beneath the loose condensate tube. "
            "The engineer closed the marked valve and secured the tube, stopping the drip."
        ),
        spill_liters=0.8,
        flow_liters_per_minute=0.3,
    ),
    "ice_case": Incident(
        key="ice_case",
        title="The Moon-Ice Case",
        onset="A silver sample case tapped its holder beside the rover hatch.",
        sound="TINK... plip!",
        clue=(
            "A frost ring circled the case holding the Moon-ice sample, "
            "and its little latch hung open."
        ),
        report="the Moon-ice sample case is open and melting",
        engineer_reply="move the vial into our spare sealed pod and latch the case",
        repair=(
            "Captain {captain} held the spare pod steady while Engineer {engineer} "
            "sealed the ice vial inside and latched the sample case."
        ),
        repair_sound="SNICK!",
        cause_answer=(
            "Mop noticed frost around the unlatched Moon-ice case. "
            "The crew sealed the vial in a spare pod and latched the case to keep more meltwater off the deck."
        ),
        spill_liters=0.6,
        flow_liters_per_minute=0.12,
    ),
}

CAPTAIN_ORDERS = [
    "Stay on the dry strip. Find what is feeding the spill before we clean.",
    "Don't cross the wet deck yet. Follow the drops from the safe side.",
]

ENDING_IMAGES = [
    "Three golden flashes crossed the dusty trail at {destination}, making the safe way easy to spot.",
    "The beacon blinked from {destination}, and the rover's tires rested safely on the dry ground beneath it.",
    "One golden pulse followed another over {destination}; the dim trail now had a bright guide home.",
]


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Generate a sound-filled space adventure about Mop, a newly born cleaning robot."
    )
    parser.add_argument("--captain", choices=CREW_NAMES)
    parser.add_argument("--engineer", choices=CREW_NAMES)
    parser.add_argument("--ship", choices=SHIP_NAMES)
    parser.add_argument("--destination", choices=DESTINATIONS)
    parser.add_argument("--incident", choices=list(INCIDENTS))
    parser.add_argument("-n", type=int, default=1, help="number of stories to generate")
    parser.add_argument("--all", action="store_true", help="generate one story for each incident")
    parser.add_argument("--seed", type=int, default=None)
    parser.add_argument("--trace", action="store_true")
    parser.add_argument("--qa", action="store_true")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--asp", action="store_true")
    parser.add_argument("--verify", action="store_true")
    parser.add_argument("--show-asp", action="store_true")
    return parser


def valid_incidents() -> list[str]:
    return list(INCIDENTS)


def valid_crew() -> list[str]:
    return list(CREW_NAMES)


def valid_ships() -> list[str]:
    return list(SHIP_NAMES)


def valid_destinations() -> list[str]:
    return list(DESTINATIONS)


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    captain = args.captain or rng.choice(CREW_NAMES)
    engineer = args.engineer
    if engineer is None:
        engineer = rng.choice([name for name in CREW_NAMES if name != captain])
    return StoryParams(
        captain=captain,
        engineer=engineer,
        ship=args.ship or rng.choice(SHIP_NAMES),
        destination=args.destination or rng.choice(DESTINATIONS),
        incident=args.incident or rng.choice(list(INCIDENTS)),
        seed=getattr(args, "seed", None),
    )


def _reasonableness_gate(params: StoryParams) -> None:
    if params.captain not in CREW_NAMES:
        raise StoryError("That captain is not part of this little space crew.")
    if params.engineer not in CREW_NAMES:
        raise StoryError("That engineer is not part of this little space crew.")
    if params.captain == params.engineer:
        raise StoryError("The captain and engineer need different names so their turns are clear.")
    if params.ship not in SHIP_NAMES:
        raise StoryError("That ship does not belong in this lunar adventure.")
    if params.destination not in DESTINATIONS:
        raise StoryError("That destination is outside this little Moon map.")
    if params.incident not in INCIDENTS:
        raise StoryError("That spill does not have a safe source and repair in this world.")


def _make_world(params: StoryParams, incident: Incident) -> World:
    hero = Entity(
        name="Mop",
        kind="new cleaning robot",
        meters={
            "battery_percent": 100.0,
            "pad_water_liters": 0.0,
            "pad_capacity_liters": 2.0,
        },
        memes={"curiosity": 0.85, "confidence": 0.42, "caution": 0.9},
    )
    captain = Entity(
        name=params.captain,
        kind="captain",
        meters={"suit_air_minutes": 90.0},
        memes={"calm": 0.82, "trust_in_mop": 0.35},
    )
    engineer = Entity(
        name=params.engineer,
        kind="ship engineer",
        meters={"tool_readiness": 1.0},
        memes={"focus": 0.88, "confidence": 0.78},
    )
    ship = Entity(
        name=params.ship,
        kind="lunar survey ship",
        meters={
            "hull_integrity": 100.0,
            "deck_gravity_g": 0.8,
            "deck_water_liters": incident.spill_liters,
            "leak_rate_liters_per_minute": incident.flow_liters_per_minute,
        },
        memes={"crew_calm": 0.7},
    )
    beacon = Entity(
        name="guide beacon",
        kind="navigation beacon",
        meters={"battery_percent": 100.0, "signal_strength": 0.0},
        memes={"reliability": 0.95},
    )
    return World(
        hero=hero,
        captain=captain,
        engineer=engineer,
        ship=ship,
        beacon=beacon,
        destination=params.destination,
        location="the Moon's Lantern Bay and the Starling's rover hatch",
        incident=incident,
    )


def generate(params: StoryParams) -> StorySample:
    _reasonableness_gate(params)
    rng = random.Random(params.seed if params.seed is not None else 0)
    incident = INCIDENTS[params.incident]
    world = _make_world(params, incident)

    # The story's turn is a sequence of physical state changes: find the source,
    # stop the flow, dry the deck, and only then continue the mission.
    world.clue_found = True
    world.facts["clue"] = incident.clue
    world.facts["risk"] = (
        "The shallow puddle made the rover hatch slippery, so a boot or wheel could slide."
    )

    world.source_stopped = True
    world.ship.meters["leak_rate_liters_per_minute"] = 0.0
    world.facts["source_repair"] = incident.repair.format(
        captain=params.captain, engineer=params.engineer
    )

    water = float(world.ship.meters["deck_water_liters"])
    world.hero.meters["pad_water_liters"] = water
    world.ship.meters["deck_water_liters"] = 0.0
    world.deck_state = "dry"
    world.mop_finished = True
    world.hero.meters["battery_percent"] -= 4.0
    world.hero.memes["confidence"] = 0.88
    world.captain.memes["trust_in_mop"] = 0.92
    world.facts["cleaning_method"] = (
        "Mop marked the wet edge, lifted the water with its absorbent pad, "
        "and sealed the wet pad in a recovery cup."
    )

    world.mission_complete = True
    world.beacon.meters["signal_strength"] = 1.0
    world.facts["ending_image"] = rng.choice(ENDING_IMAGES).format(
        destination=params.destination
    )
    world.facts["incident_title"] = incident.title

    order = rng.choice(CAPTAIN_ORDERS)
    repair_line = world.facts["source_repair"]
    ending = world.facts["ending_image"]

    paragraphs = [
        (
            "Mop was born in the Moon's Lantern Bay, where a blue spark woke the little robot "
            "inside a clean silver shell. Its first sound was a cheerful \"BEEP!\" as a soft "
            "mop pad unfolded beneath one arm. Captain "
            f"{params.captain} and Engineer {params.engineer} welcomed their new crewmate "
            f"aboard the {params.ship}. Their first trip was to carry a guide beacon to "
            f"{params.destination}, so other rovers could find the trail."
        ),
        (
            f"During the final rover check, {incident.onset} {incident.sound} The "
            f"{params.ship}'s floor gravity drew the drops into a shallow, slick puddle "
            "beside the rover hatch. Mop's amber safety light blinked: a boot or rover "
            "wheel could slide there. \"I can mop it now,\" Mop offered. "
            f"\"{order}\" Captain {params.captain} replied. Mop kept its wheels on the "
            f"dry strip and swept its lamp across the spill. {incident.clue} "
            f"\"{incident.report}!\" Mop called. \"Good catch,\" Engineer "
            f"{params.engineer} said. f\"I will {incident.engineer_reply}.\""
        ),
        (
            f"{repair_line} {incident.repair_sound} The final drops stopped. Only then "
            "did Mop set a blinking marker beside the puddle, lower its clean pad, and "
            "draw the water into a sealed recovery cup. \"SHFF, SHFF!\" went the pad. "
            "Mop's floor lamp changed from amber to blue: the hatch deck was dry. Captain "
            f"{params.captain} tested the ramp while Engineer {params.engineer} watched "
            "the repaired source; the rover rolled out without slipping. At "
            f"{params.destination}, the crew planted the guide beacon beside the trail. "
            f"{ending} Mop watched its light blink back from the rover. It had been born "
            "that morning, and its careful eyes had already helped the crew make a safe way home."
        ),
    ]
    # Remove the quote marker used to keep the dialogue template visibly separate
    # from the surrounding f-string, while preserving natural spoken words.
    paragraphs[1] = paragraphs[1].replace('said. f"I will', 'said. "I will')
    story = "\n\n".join(paragraphs)
    world.facts["story"] = story
    world.facts["sounds"] = [
        "BEEP!",
        incident.sound,
        incident.repair_sound,
        "SHFF, SHFF!",
    ]

    prompts = [
        f"Write a gentle space adventure called {incident.title} about Mop, a newly born cleaning robot.",
        (
            f"Tell a child-friendly story aboard the {params.ship} in which a clue helps the crew "
            f"find the source of a slick deck near {params.destination}."
        ),
        (
            f"Include spoken teamwork, vivid sound effects, a safe use for a mop, and a bright "
            f"ending image at {params.destination}."
        ),
    ]

    story_qa = [
        QAItem(
            question=f"What was causing the puddle in {incident.title}?",
            answer=incident.cause_answer,
        ),
        QAItem(
            question="Why did Mop wait before cleaning the puddle?",
            answer=(
                "Mop waited because water was still leaking and the hatch deck was slippery. "
                "Captain "
                f"{params.captain} asked it to find the source from the dry strip before anyone cleaned."
            ),
        ),
        QAItem(
            question="How did the crew stop more water from reaching the deck?",
            answer=f"{repair_line} That stopped the leak before Mop began cleaning.",
        ),
        QAItem(
            question="How did Mop make the rover hatch safe again?",
            answer=(
                "After the crew stopped the leak, Mop marked the wet edge, lifted the water "
                "with its absorbent pad, and sealed the wet pad in a recovery cup. "
                "Its floor lamp showed that the hatch deck was dry."
            ),
        ),
        QAItem(
            question=f"What changed by the time the crew reached {params.destination}?",
            answer=(
                f"The crew reached {params.destination} without anyone slipping and planted "
                "a bright guide beacon beside the trail, giving future rovers a safe way to follow."
            ),
        ),
    ]

    world_qa = [
        QAItem(
            question="What is a mop used for?",
            answer=(
                "A mop has an absorbent head that can pick up water from a floor. "
                "A person or robot should first make sure the water's source is under control."
            ),
        ),
        QAItem(
            question="Why can a puddle be risky near a rover hatch?",
            answer=(
                "A wet floor can be slippery, so a person or a rover wheel might slide. "
                "The crew should keep away from the wet patch until it is safe and dry."
            ),
        ),
        QAItem(
            question="What does a guide beacon do?",
            answer=(
                "A guide beacon gives off a light or signal that helps travelers find a route, "
                "especially when a trail is dim or hard to see."
            ),
        ),
        QAItem(
            question="Why should a crew find a leak before mopping?",
            answer=(
                "If water is still flowing, it can make the floor wet again. "
                "Stopping the source first lets the crew clean up safely and check that the floor stays dry."
            ),
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
        world = sample.world
        print()
        print("--- trace ---")
        for label, entity in (
            ("hero", world.hero),
            ("captain", world.captain),
            ("engineer", world.engineer),
            ("ship", world.ship),
            ("beacon", world.beacon),
        ):
            print(
                f"{label}={entity.name!r}, kind={entity.kind!r}, "
                f"meters={entity.meters}, memes={entity.memes}"
            )
        print(
            f"location={world.location!r}, incident={world.incident.title!r}, "
            f"clue_found={world.clue_found}, source_stopped={world.source_stopped}, "
            f"deck_state={world.deck_state!r}, mop_finished={world.mop_finished}, "
            f"mission_complete={world.mission_complete}"
        )
        print(f"facts={world.facts}")

    if qa:
        print()
        print("== prompts ==")
        for index, prompt in enumerate(sample.prompts, 1):
            print(f"{index}. {prompt}")
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


ASP_RULES = r"""
valid_incident(I) :-
    incident(I),
    clue_available(I),
    safe_repair(I),
    mop_compatible(I),
    mop_ready.
valid_crew(N) :- crew(N).
valid_ship(S) :- ship(S).
valid_destination(D) :- destination(D).
valid_crew_pair(C,E) :- crew(C), crew(E), C != E.

#show valid_incident/1.
#show valid_crew/1.
#show valid_ship/1.
#show valid_destination/1.
#show valid_crew_pair/2.
"""


def asp_facts() -> str:
    import asp

    facts: list[str] = []
    for key in INCIDENTS:
        facts.extend(
            [
                asp.fact("incident", key),
                asp.fact("clue_available", key),
                asp.fact("safe_repair", key),
                asp.fact("mop_compatible", key),
            ]
        )
    facts.append(asp.fact("mop_ready"))
    facts.extend(asp.fact("crew", name) for name in CREW_NAMES)
    facts.extend(asp.fact("ship", name) for name in SHIP_NAMES)
    facts.extend(asp.fact("destination", name) for name in DESTINATIONS)
    return "\n".join(facts)


def asp_program() -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n"


def asp_valid_registry() -> dict[str, set[tuple]]:
    import asp

    model = asp.one_model(asp_program())
    predicates = [
        "valid_incident",
        "valid_crew",
        "valid_ship",
        "valid_destination",
        "valid_crew_pair",
    ]
    return {predicate: set(asp.atoms(model, predicate)) for predicate in predicates}


def asp_verify() -> int:
    python_registry = {
        "valid_incident": {(key,) for key in valid_incidents()},
        "valid_crew": {(name,) for name in valid_crew()},
        "valid_ship": {(name,) for name in valid_ships()},
        "valid_destination": {(name,) for name in valid_destinations()},
        "valid_crew_pair": {
            (captain, engineer)
            for captain in CREW_NAMES
            for engineer in CREW_NAMES
            if captain != engineer
        },
    }
    clingo_registry = asp_valid_registry()

    parity_ok = True
    for predicate, python_values in python_registry.items():
        clingo_values = clingo_registry.get(predicate, set())
        if python_values == clingo_values:
            print(f"OK: ASP and Python agree on {predicate} ({len(python_values)} choices).")
            continue
        parity_ok = False
        print(f"MISMATCH for {predicate}:")
        if python_values - clingo_values:
            print("  only in Python:", sorted(python_values - clingo_values))
        if clingo_values - python_values:
            print("  only in ASP:", sorted(clingo_values - python_values))

    stories_ok = True
    for index, key in enumerate(INCIDENTS):
        captain = CREW_NAMES[index % len(CREW_NAMES)]
        engineer = CREW_NAMES[(index + 1) % len(CREW_NAMES)]
        params = StoryParams(
            captain=captain,
            engineer=engineer,
            ship=SHIP_NAMES[index % len(SHIP_NAMES)],
            destination=DESTINATIONS[index % len(DESTINATIONS)],
            incident=key,
            seed=900 + index,
        )
        sample = generate(params)
        world = sample.world
        if world is None:
            stories_ok = False
            print(f"FAIL: generated story for {key!r} has no live world.")
            continue
        checks = [
            "Mop was born" in sample.story,
            INCIDENTS[key].clue in sample.story,
            "Mop said" in sample.story or "Mop offered" in sample.story,
            "replied" in sample.story or "said." in sample.story,
            world.clue_found,
            world.source_stopped,
            world.mop_finished,
            world.mission_complete,
            world.deck_state == "dry",
            world.ship.meters["deck_water_liters"] == 0.0,
            len(sample.story_qa) >= 4,
            all(item.question and item.answer for item in sample.story_qa),
        ]
        if all(checks):
            print(f"OK: generated and exercised {INCIDENTS[key].title}.")
        else:
            stories_ok = False
            print(f"FAIL: generated story checks did not pass for {INCIDENTS[key].title}.")

    invalid_cases = [
        StoryParams(
            captain="Ari",
            engineer="Ari",
            ship=SHIP_NAMES[0],
            destination=DESTINATIONS[0],
            incident=next(iter(INCIDENTS)),
        ),
        StoryParams(
            captain="Ari",
            engineer="Bea",
            ship="Unknown Ship",
            destination=DESTINATIONS[0],
            incident=next(iter(INCIDENTS)),
        ),
        StoryParams(
            captain="Ari",
            engineer="Bea",
            ship=SHIP_NAMES[0],
            destination=DESTINATIONS[0],
            incident="unknown_spill",
        ),
    ]
    for params in invalid_cases:
        try:
            generate(params)
        except StoryError:
            continue
        stories_ok = False
        print("FAIL: an unreasonable parameter set was not rejected.")

    if stories_ok:
        print("OK: invalid parameter sets are rejected with a legible story error.")
    return 0 if parity_ok and stories_ok else 1


def generation_samples(args: argparse.Namespace) -> list[StoryParams]:
    base = args.seed if args.seed is not None else random.randrange(2**31)

    if args.all:
        samples: list[StoryParams] = []
        for index, key in enumerate(INCIDENTS):
            captain = args.captain or CREW_NAMES[index % len(CREW_NAMES)]
            if args.engineer is not None:
                engineer = args.engineer
            else:
                engineer = next(name for name in CREW_NAMES if name != captain)
            samples.append(
                StoryParams(
                    captain=captain,
                    engineer=engineer,
                    ship=args.ship or SHIP_NAMES[index % len(SHIP_NAMES)],
                    destination=args.destination
                    or DESTINATIONS[index % len(DESTINATIONS)],
                    incident=key,
                    seed=base + index,
                )
            )
        return samples

    if args.n < 1:
        raise StoryError("Choose at least one story with -n.")
    return [
        resolve_params(args, random.Random(base + index))
        for index in range(args.n)
    ]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program())
        return
    if args.verify:
        raise SystemExit(asp_verify())
    if args.asp:
        registry = asp_valid_registry()
        print("ASP-valid incidents:")
        for (key,) in sorted(registry["valid_incident"]):
            print(f"- {INCIDENTS[key].title}")
        return

    try:
        samples = [generate(params) for params in generation_samples(args)]
    except StoryError as exc:
        print(f"error: {exc}", file=sys.stderr)
        raise SystemExit(2) from exc

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
        header = f"### variant {index + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if index < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()

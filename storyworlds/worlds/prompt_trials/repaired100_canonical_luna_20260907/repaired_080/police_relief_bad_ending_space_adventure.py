#!/usr/bin/env python3
"""
Standalone storyworld: police relief / bad ending / space adventure.

A small space-police simulation in which a relief crate must cross a dangerous
moon, while a rushed choice leads to a bad ending that still teaches why
careful rescue work matters.
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

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from results import QAItem, StoryError, StorySample  # noqa: E402


THRESHOLD = 1.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    owner: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]


@dataclass
class World:
    entities: dict[str, Entity] = field(default_factory=dict)
    fired: set[tuple] = field(default_factory=set)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    facts: dict = field(default_factory=dict)

    def add(self, entity: Entity) -> Entity:
        self.entities[entity.id] = entity
        return entity

    def get(self, entity_id: str) -> Entity:
        if entity_id not in self.entities:
            raise StoryError(f"Unknown entity: {entity_id}")
        return self.entities[entity_id]

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)


@dataclass
class StoryParams:
    officer_name: str
    pilot_name: str
    ship_name: str = "Star Lantern"
    scenario: int = 0
    opening: int = 0
    tension: int = 0
    dialogue: int = 0
    ending: int = 0
    seed: Optional[int] = None


OFFICER_NAMES = ["Luna", "Mira", "Nia", "Tess", "Iris", "Ava", "Zara", "Pia"]
PILOT_NAMES = ["Sol", "Remy", "Kai", "Orin", "Juno", "Milo", "Taro", "Bea"]
GIRL_NAMES = {"Luna", "Mira", "Nia", "Tess", "Iris", "Ava", "Zara", "Pia", "Juno", "Bea"}
BOY_NAMES = {"Sol", "Kai", "Orin", "Milo", "Taro", "Remy"}

SCENARIOS = [
    {
        "relief": "a silver case of oxygen masks and warm food",
        "place": "the dark side of Moon Kestrel",
        "danger": "a dust storm began folding the landing beacons flat",
        "clue": "the old mining rail still flashed three blue lights at a time",
        "bad_choice": "the crew followed the brightest signal without checking its pattern",
        "action": "the rover rolled into a shallow crater and its wheels lost the firm ground",
        "consequence": "the relief case remained sealed, but the stranded rover could not reach the waiting miners before their shelter lights went dark",
        "image": "the blue beacons blinked beyond the crater while the unopened relief case sat beneath a veil of red dust",
        "lesson": "In space, courage must travel with careful checking; a fast rescue can become a dangerous delay.",
    },
    {
        "relief": "a crate of medicine, blankets, and bright fruit",
        "place": "the ice tunnels of Europa",
        "danger": "a crack opened across the marked rescue path",
        "clue": "tiny heat marks showed that the safer tunnel curved behind the silent antenna",
        "bad_choice": "the pilot trusted the shortest route and ignored the heat marks",
        "action": "the rescue skiff drifted toward thin ice and had to shut down its engine",
        "consequence": "the medicine was safe, but the skiff could not dock with the cold research team",
        "image": "the relief crate glowed in the quiet skiff as blue ice spread between it and the station",
        "lesson": "A police rescue protects lives best when every clue is treated as important.",
    },
    {
        "relief": "a bundle of power cells for a stranded weather station",
        "place": "the windy plains of Mars",
        "danger": "a red storm erased the road markers",
        "clue": "old rover tracks curved toward a ridge where the station's mirror flashed",
        "bad_choice": "the crew raced straight toward a false reflection on the salt flats",
        "action": "the patrol rover overheated and stopped beside an empty survey tower",
        "consequence": "the power cells never reached the station before its last heater faded",
        "image": "the false tower shone in the sunset while the real station waited beyond the storm",
        "lesson": "Relief work needs patience, evidence, and teamwork, not only a brave engine.",
    },
    {
        "relief": "a box of water beads for a family trapped on a tiny moon",
        "place": "the Echo Moon's canyon maze",
        "danger": "every sound bounced from a different wall",
        "clue": "the family's beacon answered only after the police ship sent two short pulses",
        "bad_choice": "the crew answered every echo and mistook noise for a direction",
        "action": "the shuttle landed at an empty canyon mouth and spent its fuel searching",
        "consequence": "the family heard the shuttle but could not be found before the rescue window closed",
        "image": "one real beacon blinked beyond the canyon while a dry water-bead box rested in the shuttle",
        "lesson": "Listening carefully is part of bravery when relief depends on finding the right voice.",
    },
]

OPENINGS = [
    "Far beyond Earth, where stars glittered like crumbs on black velvet, a police ship patrolled the quiet between moons.",
    "The spaceport clock had just struck midnight when the police cruiser lifted above the silver roofs.",
    "Near a small moon with a blue ring, the stars seemed close enough for a child to count.",
    "The patrol ship hummed through space while a comet dragged a pale tail behind it.",
    "On the edge of the galaxy, one red warning light blinked beside a very ordinary lunchbox.",
]

TENSIONS = [
    "The problem grew quickly, because the people waiting for relief had only a short supply of air, warmth, or power.",
    "No one wanted to waste a minute, yet every wrong turn could spend the fuel needed for the return trip.",
    "The crew felt the clock pressing on them like a heavy moon.",
    "The radio crackled, and the waiting voices made the empty stars feel suddenly enormous.",
    "Even the ship's cheerful computer stopped humming and displayed one serious yellow question mark.",
]

DIALOGUES = [
    '"The quickest path is not always the safest path," Luna said. "Let us check the beacon."',
    '"I see the signal," said {officer}. "But I do not yet know what it means."',
    '"We are police," {pilot} replied. "Our job is to protect people, not to win a race."',
    '"Tell me the clue again," said {officer}. "A careful answer can save fuel and lives."',
    '"I want to hurry too," {pilot} said, "but I will not hurry past the evidence."',
]

ENDINGS = [
    "The stars kept shining, but the crew understood that a rescue story can end sadly when caution is left behind.",
    "The ship turned home with a quiet cabin and a lesson written in every blinking instrument.",
    "No alarm rang for victory; only the soft engine reminded them to learn before trying again.",
    "The empty landing pad waited under the stars, holding a promise that the next patrol would be wiser.",
]


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="A space-adventure story about police relief and a bad ending."
    )
    parser.add_argument("--officer-name")
    parser.add_argument("--pilot-name")
    parser.add_argument("--ship-name", default="Star Lantern")
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
    officer = args.officer_name or rng.choice(OFFICER_NAMES)
    pilot = args.pilot_name or rng.choice(PILOT_NAMES)
    if officer == pilot:
        pilot = rng.choice([name for name in PILOT_NAMES if name != officer])
    return StoryParams(
        officer_name=officer,
        pilot_name=pilot,
        ship_name=args.ship_name or "Star Lantern",
        scenario=rng.randrange(len(SCENARIOS)),
        opening=rng.randrange(len(OPENINGS)),
        tension=rng.randrange(len(TENSIONS)),
        dialogue=rng.randrange(len(DIALOGUES)),
        ending=rng.randrange(len(ENDINGS)),
    )


def build_world(params: StoryParams) -> World:
    world = World()
    officer_type = "girl" if params.officer_name in GIRL_NAMES else "boy" if params.officer_name in BOY_NAMES else "person"
    pilot_type = "girl" if params.pilot_name in GIRL_NAMES else "boy" if params.pilot_name in BOY_NAMES else "person"
    world.add(Entity("Officer", "character", officer_type, params.officer_name))
    world.add(Entity("Pilot", "character", pilot_type, params.pilot_name))
    world.add(Entity("Police", "organization", "police", "space police"))
    world.add(Entity("Relief", "cargo", "relief", "relief supplies", owner="Police"))
    world.add(Entity("Ship", "vehicle", "ship", params.ship_name, owner="Police"))
    world.facts["params"] = params
    return world


def tell(world: World) -> None:
    params: StoryParams = world.facts["params"]
    scenario = SCENARIOS[params.scenario % len(SCENARIOS)]
    officer = world.get("Officer")
    pilot = world.get("Pilot")
    ship = world.get("Ship")
    relief = world.get("Relief")

    world.facts["scenario"] = scenario
    world.say(OPENINGS[params.opening % len(OPENINGS)])
    world.say(
        f"Officer {officer.label} and pilot {pilot.label} flew the police ship {ship.label} "
        f"toward {scenario['place']}. They carried {scenario['relief']} in the relief case."
    )
    world.say(
        f"The people there needed the supplies, and the police promised to bring help before the "
        f"station's emergency lights went out."
    )

    world.para()
    officer.memes["responsible"] = 1
    pilot.memes["worried"] = 1
    relief.meters["needed"] = 1
    world.say(f"Then {scenario['danger']}.")
    world.say(TENSIONS[params.tension % len(TENSIONS)])
    world.say(f"The useful clue was nearby: {scenario['clue']}.")
    dialogue = DIALOGUES[params.dialogue % len(DIALOGUES)].format(
        officer=officer.label,
        pilot=pilot.label,
    )
    world.say(dialogue)
    world.say(
        f"But the bad choice came next: {scenario['bad_choice']}. "
        f"{scenario['action']}."
    )

    world.para()
    world.say(
        f"{officer.label} tried to call the waiting people, while {pilot.label} worked the controls. "
        f"The police ship could not safely reach the landing place."
    )
    world.say(
        f"The relief was still aboard, but being close was not the same as helping. "
        f"{scenario['consequence']}."
    )
    relief.meters["delivered"] = 0
    world.facts["resolved"] = False
    world.facts["bad_ending"] = True
    world.facts["clue"] = scenario["clue"]
    world.facts["bad_choice"] = scenario["bad_choice"]
    world.facts["consequence"] = scenario["consequence"]
    world.facts["ending_image"] = scenario["image"]

    world.para()
    world.say(
        f"In the last sight, {scenario['image']}. "
        f"This was a bad ending, not because the officers did not care, but because "
        f"they acted before they had understood the danger."
    )
    world.say(scenario["lesson"])
    world.say(ENDINGS[params.ending % len(ENDINGS)])


def generation_prompts(world: World) -> list[str]:
    params: StoryParams = world.facts["params"]
    scenario = world.facts["scenario"]
    return [
        f"Write a child-facing space adventure about police officer {params.officer_name} delivering relief.",
        f"Set the adventure aboard {params.ship_name}, traveling to {scenario['place']} with {scenario['relief']}.",
        f"Write a bad-ending rescue story in which the clue '{scenario['clue']}' is ignored and the crew learns why careful police relief work matters.",
    ]


def story_qa(world: World) -> list[QAItem]:
    params: StoryParams = world.facts["params"]
    scenario = world.facts["scenario"]
    return [
        QAItem(
            question="Who carried the relief supplies?",
            answer=f"Police officer {params.officer_name} and pilot {params.pilot_name} carried the relief supplies aboard the police ship {params.ship_name}.",
        ),
        QAItem(
            question="Where were they trying to go?",
            answer=f"They were trying to reach {scenario['place']} to deliver {scenario['relief']}.",
        ),
        QAItem(
            question="What clue could have helped them?",
            answer=f"The clue was that {scenario['clue']}. Checking it would have helped them choose more safely.",
        ),
        QAItem(
            question="What bad choice caused the trouble?",
            answer=f"The crew made the bad choice of {scenario['bad_choice']}. They acted before fully checking the evidence.",
        ),
        QAItem(
            question="Why was the ending bad?",
            answer=f"The ending was bad because {scenario['consequence']}. The relief stayed aboard instead of reaching the people who needed it.",
        ),
        QAItem(
            question="What image showed the result?",
            answer=f"The final image showed that {scenario['image']}. It made the failed delivery visible.",
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does police mean in this story?",
            answer="Police are people whose job is to protect others, respond to danger, and help keep communities safe.",
        ),
        QAItem(
            question="What is relief?",
            answer="Relief is help or supplies given to people who are suffering or facing an emergency.",
        ),
        QAItem(
            question="Why should rescuers check clues?",
            answer="Rescuers should check clues because a rushed guess can lead them away from the people who need help.",
        ),
        QAItem(
            question="What makes an ending bad?",
            answer="An ending is bad when an important goal fails and people are left facing the consequence of the mistake.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== Prompts =="]
    lines.extend(f"{i}. {prompt}" for i, prompt in enumerate(sample.prompts, 1))
    lines.append("")
    lines.append("== Story QA ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== World QA ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for entity in world.entities.values():
        parts = []
        if entity.meters:
            parts.append(f"meters={entity.meters}")
        if entity.memes:
            parts.append(f"memes={entity.memes}")
        lines.append(f"{entity.id}: {' '.join(parts) if parts else '(quiet)'}")
    lines.append(f"facts={{bad_ending: {world.facts.get('bad_ending', False)}, resolved: {world.facts.get('resolved', False)}}}")
    return "\n".join(lines)


ASP_RULES = r"""
police_team :- police, officer, pilot.
relief_needed :- relief, emergency.
bad_choice :- rushed, clue_ignored.
failed_delivery :- bad_choice, relief_needed.
careful_rescue :- police_team, clue_checked, relief_needed.
"""


def asp_facts() -> str:
    import asp
    return "\n".join(
        [
            asp.fact("police"),
            asp.fact("officer"),
            asp.fact("pilot"),
            asp.fact("relief"),
            asp.fact("emergency"),
            asp.fact("rushed"),
            asp.fact("clue_ignored"),
        ]
    )


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(
        asp_program(
            "#show police_team/0. #show relief_needed/0. "
            "#show bad_choice/0. #show failed_delivery/0."
        )
    )
    names = {f"{symbol.name}/{len(symbol.arguments)}" for symbol in model}
    required = {"police_team/0", "relief_needed/0", "bad_choice/0", "failed_delivery/0"}
    if not required.issubset(names):
        raise StoryError(f"ASP parity failed; missing atoms: {sorted(required - names)}")
    for params in CURATED:
        sample = generate(params)
        if not sample.world or not sample.world.facts.get("bad_ending"):
            raise StoryError("Generated story verification failed to preserve the bad ending.")
        if sample.world.facts.get("resolved"):
            raise StoryError("Generated story incorrectly marked relief as delivered.")
    print("OK: ASP twin and generated bad-ending stories agree.")
    return 0


def asp_valid() -> str:
    return asp_program(
        "#show police_team/0. #show relief_needed/0. "
        "#show bad_choice/0. #show failed_delivery/0."
    )


CURATED = [
    StoryParams(
        officer_name="Luna",
        pilot_name="Sol",
        ship_name="Star Lantern",
        scenario=0,
        opening=0,
        tension=0,
        dialogue=0,
        ending=0,
    ),
    StoryParams(
        officer_name="Mira",
        pilot_name="Kai",
        ship_name="Comet Finch",
        scenario=1,
        opening=2,
        tension=3,
        dialogue=4,
        ending=1,
    ),
    StoryParams(
        officer_name="Nia",
        pilot_name="Orin",
        ship_name="Blue Arrow",
        scenario=2,
        opening=3,
        tension=1,
        dialogue=2,
        ending=3,
    ),
    StoryParams(
        officer_name="Tess",
        pilot_name="Juno",
        ship_name="Moon Mender",
        scenario=3,
        opening=1,
        tension=4,
        dialogue=3,
        ending=2,
    ),
]


def generate(params: StoryParams) -> StorySample:
    world = build_world(params)
    tell(world)
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
        print()
        print(format_qa(sample))


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program(
            "#show police_team/0. #show relief_needed/0. "
            "#show bad_choice/0. #show failed_delivery/0."
        ))
        return

    if args.verify:
        sys.exit(asp_verify())

    if args.asp:
        import asp
        model = asp.one_model(asp_valid())
        print("\n".join(str(atom) for atom in model))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(params) for params in CURATED]
    else:
        seen: set[str] = set()
        index = 0
        while len(samples) < max(0, args.n) and index < max(args.n * 50, 50):
            seed = base_seed + index
            index += 1
            params = resolve_params(args, random.Random(seed))
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
        params = sample.params
        if args.all:
            header = f"### {params.officer_name} / {params.pilot_name} aboard {params.ship_name}"
        elif len(samples) > 1:
            header = f"### variant {index + 1}"
        else:
            header = ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if index < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()

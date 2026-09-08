#!/usr/bin/env python3
"""A small space-adventure world about machinery, a thermos, and a shared cab."""

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
sys.path.insert(0, _storyworlds_dir)
from results import QAItem, StoryError, StorySample  # noqa: E402


@dataclass
class Thing:
    id: str
    label: str
    kind: str
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)


@dataclass
class World:
    place: str
    hero: Thing
    partner: Thing
    machine: Thing
    thermos: Thing
    cab: Thing
    facts: dict = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])

    def say(self, text: str) -> None:
        self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)


@dataclass(frozen=True)
class Mission:
    id: str
    danger: str
    clue: str
    plan: str
    transformation: str
    bad_ending: str
    ending: str


MISSIONS = {
    "frozen_relay": Mission(
        "frozen_relay",
        "a frozen relay was choking the station's power",
        "blue frost covered the panel while one warm light blinked beneath it",
        "share the thermos heat, melt only the safe bolts, and send the repair cab along the marked rail",
        "the stubborn machinery unfolded into a bright solar sail",
        "the cab would have stalled in the dark while the station lost its last warm room",
        "the sail opened like a small sunrise and carried power through every station window",
    ),
    "dust_moon": Mission(
        "dust_moon",
        "moon dust had clogged the mining machinery",
        "the dust swirled away whenever the cab's little fan turned toward the intake",
        "share warm drink, use the fan as a gentle brush, and guide the cab around the fragile drill",
        "the dusty machine changed into a patient seed-sifter",
        "the drill would have jammed and buried the crew's only path home",
        "silver seeds tumbled into trays as the transformed machine hummed softly",
    ),
    "comet_bridge": Mission(
        "comet_bridge",
        "a comet bridge kept folding before the survey cab could cross",
        "each fold happened after three blue sparks reached the bridge's hinge",
        "share the thermos, count the sparks aloud, and drive only when the hinge light turned green",
        "the machinery became a bridge of glowing stepping stones",
        "the cab would have drifted beyond the comet and left the travelers stranded",
        "the stepping stones glittered behind the cab like a trail of friendly stars",
    ),
    "quiet_orbit": Mission(
        "quiet_orbit",
        "the station machinery had gone silent above a lonely planet",
        "the thermos lid vibrated whenever the cab pointed toward the planet's dark side",
        "share the last warm sip, follow the vibration, and let the cab carry the repair tools",
        "the silent machinery transformed into a listening antenna",
        "the crew would have missed the planet's call and flown past the rescue signal",
        "the antenna caught a gentle beep, and a lost weather balloon answered",
    ),
}

PLACES = {
    "orbital_station": "the Lantern Station",
    "comet_rim": "the bright rim of a comet",
    "red_moon": "the red moon's quiet repair bay",
}

NAMES = ["Luna", "Mara", "Niko", "Tavi", "Jo", "Pax"]
PARTNERS = ["Orin", "Sela", "Bex", "Rumi", "Kato", "Ivo"]

OPENINGS = [
    "The stars were sharp as pins outside the cockpit glass.",
    "The little station drifted above a blue world.",
    "A comet shone like a lantern in the dark.",
    "The space route looked easy until the warning lights blinked.",
]

@dataclass
class StoryParams:
    place: str = "orbital_station"
    mission: str = "frozen_relay"
    name: str = "Luna"
    partner_name: str = "Orin"
    opening: int = 0
    seed: Optional[int] = None
    samples: list = field(default_factory=list)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="A space adventure about sharing, transformation, and a dangerous choice.")
    parser.add_argument("--place", choices=PLACES)
    parser.add_argument("--mission", choices=MISSIONS)
    parser.add_argument("--name")
    parser.add_argument("--partner-name")
    parser.add_argument("-n", type=int, default=1)
    parser.add_argument("--seed", type=int)
    parser.add_argument("--all", action="store_true")
    parser.add_argument("--trace", action="store_true")
    parser.add_argument("--qa", action="store_true")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--asp", action="store_true")
    parser.add_argument("--verify", action="store_true")
    parser.add_argument("--show-asp", action="store_true")
    return parser


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    name = args.name or rng.choice(NAMES)
    partner = args.partner_name or rng.choice([x for x in PARTNERS if x != name])
    return StoryParams(
        place=args.place or rng.choice(list(PLACES)),
        mission=args.mission or rng.choice(list(MISSIONS)),
        name=name,
        partner_name=partner,
        opening=rng.randrange(len(OPENINGS)),
    )


def validate(params: StoryParams) -> None:
    if params.place not in PLACES:
        raise StoryError(f"Unknown space setting: {params.place}")
    if params.mission not in MISSIONS:
        raise StoryError(f"Unknown mission: {params.mission}")
    if not params.name.strip() or not params.partner_name.strip():
        raise StoryError("Crew names must not be empty.")
    if params.name == params.partner_name:
        raise StoryError("The pilot and partner need different names.")


def tell(params: StoryParams) -> World:
    validate(params)
    mission = MISSIONS[params.mission]
    hero = Thing(params.name, params.name, "pilot", memes={"courage": 0.0, "care": 0.0})
    partner = Thing(params.partner_name, params.partner_name, "partner", memes={"care": 0.0})
    machine = Thing("repair_machine", "the station machinery", "machinery", meters={"power": 1.0, "danger": 1.0})
    thermos = Thing("shared_thermos", "the thermos", "thermos", meters={"warmth": 1.0})
    cab = Thing("repair_cab", "the repair cab", "cab", meters={"fuel": 1.0})
    world = World(PLACES[params.place], hero, partner, machine, thermos, cab)
    world.facts.update(mission=mission, shared=False, transformed=False, resolved=False, bad_ending_avoided=False)

    world.say(f"{OPENINGS[params.opening % len(OPENINGS)]} {world.place} circled the stars while {hero.label} guided {cab.label} beside {machine.label}.")
    world.say(f"{mission.danger.capitalize()}. If the crew rushed, {mission.bad_ending}.")
    world.para()

    hero.memes["courage"] += 1
    world.say(f'"Should I push the red switch?" asked {hero.label}.')
    world.say(f'"Not yet," said {partner.label}. "Let us see what the machine is telling us."')
    world.say(f"{mission.clue.capitalize()}. The two astronauts leaned close instead of guessing.")
    world.para()

    partner.memes["care"] += 1
    hero.memes["care"] += 1
    thermos.meters["warmth"] -= 0.5
    world.facts["shared"] = True
    world.say(f"{hero.label} opened {thermos.label}. They shared its warm drink, giving the cold repair tools enough heat to work.")
    world.say(f'"A small share can make a large difference," said {partner.label}.')
    world.say(f'"Then we will use only what we need," {hero.label} replied.')
    world.say(f"Together they decided to {mission.plan}.")
    world.para()

    machine.meters["danger"] = 0.0
    machine.meters["power"] = 2.0
    cab.meters["fuel"] -= 0.25
    world.facts["transformed"] = True
    world.facts["bad_ending_avoided"] = True
    world.say(f"The plan worked. The machinery shuddered, flashed, and transformed: {mission.transformation}.")
    world.say(f"{cab.label} rolled safely through the repair lane while {hero.label} and {partner.label} shared the controls.")
    world.para()

    world.facts["resolved"] = True
    world.say(f"They had avoided a bad ending because they listened, shared, and changed the machine instead of forcing it.")
    world.say(f"{mission.ending}. The nearly empty thermos rested between the two friends as the stars blinked approval.")
    return world


def generate(params: StoryParams) -> StorySample:
    world = tell(params)
    mission = world.facts["mission"]
    return StorySample(
        params=params,
        story=world.render(),
        prompts=[
            "Write a child-friendly space adventure where sharing helps a crew solve a machinery problem.",
            f"Include a thermos and a repair cab while transforming the machinery through careful teamwork.",
            f"Show how the crew avoids this bad ending: {mission.bad_ending}.",
        ],
        story_qa=[
            QAItem(
                f"Why did {world.hero.label} and {world.partner.label} share the thermos?",
                "They shared the thermos so warm liquid could heat the repair tools and help them work carefully.",
            ),
            QAItem(
                "What happened to the machinery?",
                f"The machinery transformed: {mission.transformation}.",
            ),
            QAItem(
                "How did the crew avoid the bad ending?",
                f"They avoided it by noticing the clue, sharing their warmth, and following this plan: {mission.plan}.",
            ),
            QAItem(
                "What happened at the end?",
                mission.ending,
            ),
        ],
        world_qa=[
            QAItem("What is machinery?", "Machinery is a group of working parts that can use power to do a job."),
            QAItem("What is a thermos?", "A thermos is a container designed to keep a drink warm or cold for a long time."),
            QAItem("What is a cab?", "A cab is a small vehicle or enclosed section used to carry people or guide equipment."),
            QAItem("Why can sharing help a team?", "Sharing supplies, ideas, and responsibility can give a team more ways to solve a problem."),
        ],
        world=world,
    )


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts =="]
    lines.extend(f"{i}. {p}" for i, p in enumerate(sample.prompts, 1))
    lines.append("\n== (2) Story questions ==")
    for item in sample.story_qa:
        lines.extend([f"Q: {item.question}", f"A: {item.answer}"])
    lines.append("\n== (3) World-knowledge questions ==")
    for item in sample.world_qa:
        lines.extend([f"Q: {item.question}", f"A: {item.answer}"])
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for thing in [world.hero, world.partner, world.machine, world.thermos, world.cab]:
        lines.append(f"  {thing.label}: meters={thing.meters}, memes={thing.memes}")
    lines.append(f"  shared={world.facts['shared']} transformed={world.facts['transformed']} resolved={world.facts['resolved']}")
    return "\n".join(lines)


ASP_RULES = r"""
clue_seen :- machinery_dangerous, thermos_shared.
safe_plan :- clue_seen, cab_guided.
transformed_machinery :- safe_plan.
bad_ending_avoided :- transformed_machinery.
#show clue_seen/0.
#show safe_plan/0.
#show transformed_machinery/0.
#show bad_ending_avoided/0.
"""


def asp_facts() -> str:
    import asp
    return "\n".join([
        asp.fact("machinery_dangerous"),
        asp.fact("thermos_shared"),
        asp.fact("cab_guided"),
    ])


def asp_program(show: str = "") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program())
    names = {symbol.name for symbol in model}
    expected = {"clue_seen", "safe_plan", "transformed_machinery", "bad_ending_avoided"}
    if expected <= names:
        print("OK: ASP twin matches the Python transformation and ending gate.")
        return 0
    print("MISMATCH between ASP and Python.")
    print("  asp:", sorted(names))
    print("  expected:", sorted(expected))
    return 1


def emit(sample: StorySample, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world:
        print(dump_trace(sample.world))
    if qa:
        print()
        print(format_qa(sample))


def main() -> None:
    args = build_parser().parse_args()
    if args.verify:
        raise SystemExit(asp_verify())
    if args.show_asp:
        print(asp_program("#show clue_seen/0. #show safe_plan/0. #show transformed_machinery/0. #show bad_ending_avoided/0."))
        return
    if args.asp:
        import asp
        model = asp.one_model(asp_program())
        print("\n".join(sorted(str(atom) for atom in model)))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    if args.all:
        params_list = [
            StoryParams(place=place, mission=mission, name="Luna", partner_name="Orin", opening=i % len(OPENINGS), seed=base_seed + i)
            for i, (place, mission) in enumerate((p, m) for p in PLACES for m in MISSIONS)
        ]
    else:
        params_list = []
        for i in range(args.n):
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            params_list.append(params)

    samples = [generate(params) for params in params_list]
    if args.json:
        print(samples[0].to_json() if len(samples) == 1 else json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return
    for i, sample in enumerate(samples):
        emit(sample, trace=args.trace, qa=args.qa, header=f"### variant {i + 1}" if len(samples) > 1 else "")
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()

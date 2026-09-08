#!/usr/bin/env python3
"""
A cautionary pirate tale about an armoire, a foolish division, and a clever
way to repel trouble before it boards the ship.
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

_worlds = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if not os.path.exists(os.path.join(_worlds, "results.py")):
    _worlds = os.path.dirname(_worlds)
sys.path.insert(0, _worlds)
from results import QAItem, StoryError, StorySample  # noqa: E402


@dataclass
class Entity:
    id: str
    label: str
    kind: str
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)


@dataclass
class Setting:
    id: str
    label: str
    affordances: set[str]


@dataclass
class World:
    setting: Setting
    entities: dict[str, Entity] = field(default_factory=dict)
    facts: dict = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])

    def add(self, entity: Entity) -> Entity:
        self.entities[entity.id] = entity
        return entity

    def say(self, text: str) -> None:
        self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)


@dataclass
class Armoire:
    id: str
    label: str
    compartments: int
    sealed: bool
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)


@dataclass
class Division:
    id: str
    name: str
    safe: bool
    danger: str
    remedy: str


SETTINGS = {
    "saltwind_deck": Setting(
        id="saltwind_deck",
        label="the Saltwind deck",
        affordances={"armoire", "division", "repel"},
    )
}

ARMOIRES = {
    "captains_armoire": Armoire(
        id="captains_armoire",
        label="the captain's cedar armoire",
        compartments=3,
        sealed=False,
    )
}

DIVISIONS = {
    "cargo_division": Division(
        id="cargo_division",
        name="the cargo division",
        safe=False,
        danger="a greedy division can leave one side of the ship weak and easy to board",
        remedy="divide the supplies by need, then leave a visible reserve for emergencies",
    )
}

NAMES = ["Luna", "Mara", "Pip", "Tessa", "Nell"]
TRAITS = ["careful", "curious", "steady", "bright-eyed", "brave"]

CASES = [
    {
        "problem": "the crew divided the ship's biscuits into equal piles, though the smallest sailors needed fewer days of food on deck and the night watch needed extra",
        "temptation": "lock the biggest pile in the armoire and let the loudest pirates choose first",
        "clue": "a trail of crumbs leading from the low shelf to the night-watch bell",
        "turn": "the missing biscuits had been carried by hungry deck hands during a long storm watch, while a sealed chest of spare water sat untouched",
        "action": "marked three armoire shelves for daily food, watch food, and reserve food",
        "proof": "every sailor received a meal, the night watch had enough for its long shift, and the reserve stayed dry",
        "ending": "the armoire stood open beneath the lantern, with three honest labels swinging from its shelves",
    },
    {
        "problem": "the crew made a foolish division of the sailcloth, giving every boat the same-sized square even though one boat had a torn mast and another had none",
        "temptation": "cut the last strong cloth in half and hope the sea would forgive the mistake",
        "clue": "blue threads snagged on the armoire's lowest hinge",
        "turn": "the torn boat had quietly borrowed cloth before dawn, while the untouched boat had hidden its spare roll behind the armoire",
        "action": "opened the armoire, counted every roll, and divided cloth according to damage rather than shouting",
        "proof": "the torn mast was patched, the spare roll was returned, and each boat could sail safely",
        "ending": "fresh patches bellied in the wind as the armoire's doors clicked shut on a neat cloth ledger",
    },
    {
        "problem": "the first mate divided the watch into two equal groups but forgot that one group had never learned how to repel boarders",
        "temptation": "give everyone the same sword and pretend equal numbers meant equal safety",
        "clue": "a practice shield wedged behind the armoire",
        "turn": "the quiet sailors had been waiting for a lesson, not refusing their duty",
        "action": "stored shields and signal flags in separate armoire compartments and taught the unready group before assigning the watches",
        "proof": "both groups could sound the alarm, raise a shield, and repel a training boarding party",
        "ending": "the crew cheered as signal flags flew, while the armoire guarded the gear like a patient old sailor",
    },
]


def valid_combos() -> list[tuple[str, str, str]]:
    return [
        (place, division, armoire)
        for place, setting in SETTINGS.items()
        for division in DIVISIONS
        for armoire in ARMOIRES
        if {"armoire", "division", "repel"} <= setting.affordances
    ]


def explain_rejection() -> str:
    return "The chosen setting must support an armoire, a fair division, and a plan to repel danger."


@dataclass
class StoryParams:
    place: str
    division: str
    armoire: str
    hero_name: str
    trait: str
    seed: Optional[int] = None


def build_world(params: StoryParams) -> World:
    if (params.place, params.division, params.armoire) not in valid_combos():
        raise StoryError(explain_rejection())
    setting = SETTINGS[params.place]
    division = DIVISIONS[params.division]
    armoire = ARMOIRES[params.armoire]
    rng = random.Random(params.seed)
    case = rng.choice(CASES)
    world = World(setting)
    hero = world.add(Entity(
        id="hero",
        label=params.hero_name,
        kind="pirate",
        meters={"reach": 1.0, "alertness": 0.8},
        memes={"caution": 0.7, "confidence": 0.6},
    ))
    captain = world.add(Entity(
        id="captain",
        label="Captain Brine",
        kind="captain",
        meters={"reach": 1.2, "alertness": 0.8},
        memes={"trust": 0.7},
    ))
    armoire_entity = world.add(Entity(
        id="armoire",
        label=armoire.label,
        kind="armoire",
        meters={"height": 2.0, "width": 1.1},
        memes={"order": 0.2},
    ))
    world.facts.update(
        hero=hero,
        captain=captain,
        armoire=armoire,
        division=division,
        case=case,
        cautionary=True,
        repel=True,
    )

    openings = [
        "On a salt-bright morning, the little pirate ship Lantern Gull rocked beneath a red sky.",
        "The sea was calm, but calm seas can hide foolish plans.",
        "At dawn, the Lantern Gull's deck shone like a wet coin, and Captain Brine called the crew together.",
    ]
    world.say(rng.choice(openings))
    world.say(
        f"{params.hero_name}, a {params.trait} young pirate, served aboard the ship. "
        f"Beside the mast stood {armoire.label}, a cedar armoire with three sturdy compartments."
    )
    world.say(f"That day, {case['problem']}. The plan sounded tidy, but tidy is not always fair.")

    world.para()
    world.say(
        f"The first mate pointed at the armoire. \"We will use {case['temptation']},\" he declared."
    )
    world.say(
        f"{params.hero_name} shook {params.hero_name}'s head. \"Captain, equal piles may still make an unsafe division. "
        f"Who needs what, and how will we repel trouble if the wrong gear is hidden?\""
    )
    world.say(
        f"Captain Brine answered, \"Good question, sailor. Find the clue before the tide turns.\""
    )
    world.say(f"{params.hero_name} inspected the deck instead of grabbing the largest share. {case['clue']}.")

    world.para()
    world.say(
        f"The clue changed the plan: {case['turn']}. "
        f"The captain rubbed his chin, and the crew stopped arguing."
    )
    world.say(
        f"{params.hero_name} {case['action']}. The captain helped, but every sailor checked the count aloud."
    )
    world.say(
        f"They also made a small safety drill: if danger came over the rail, the crew would sound the bell, "
        f"take the right gear, and repel the boarders together."
    )
    world.say(f"At last, {case['proof']}.")

    world.para()
    world.say(
        f"Captain Brine gave {params.hero_name} the first key to {armoire.label}. "
        f"\"Keep it open to inspection,\" he said. \"A hidden division grows crooked.\""
    )
    world.say(
        f"The cautionary lesson was clear: {division.danger.capitalize()}. "
        f"A wise crew will {division.remedy}."
    )
    world.say(f"By sunset, {case['ending']}.")
    world.facts["resolved"] = True
    return world


KNOWLEDGE = [
    QAItem("What is an armoire?", "An armoire is a tall cupboard with doors used for storing things."),
    QAItem("What does division mean?", "Division means separating something into parts or groups."),
    QAItem("What does repel mean?", "Repel means to push danger or an attacker away."),
    QAItem("What is a cautionary tale?", "A cautionary tale is a story that warns people about the results of foolish choices."),
    QAItem("What is a pirate?", "A pirate is a sailor in an adventure story who travels by ship and follows a rough life at sea."),
]


def generation_prompts(world: World) -> list[str]:
    case = world.facts["case"]
    return [
        f"Write a cautionary pirate tale about an armoire and a fair division beginning when {case['problem']}.",
        "Tell a child-facing sea adventure in which a young pirate discovers that equal portions are not always fair.",
        "Write a story where an armoire stores useful gear and a careful crew learns how to repel danger.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    case = f["case"]
    hero = f["hero"].label
    return [
        QAItem(
            "What was wrong with the crew's first division?",
            f"The first division looked equal but ignored different needs. {case['problem'].capitalize()}.",
        ),
        QAItem(
            "What clue changed the plan?",
            f"The clue was {case['clue']}. It led the crew to inspect the real arrangement instead of trusting a quick guess.",
        ),
        QAItem(
            "How did the armoire help?",
            f"{hero} used the armoire's compartments to label and organize supplies, so the crew could count them and find the right gear quickly.",
        ),
        QAItem(
            "How did the crew prepare to repel danger?",
            "They practiced sounding the bell, taking the right equipment, and working together rather than pretending equal numbers guaranteed safety.",
        ),
        QAItem(
            "What cautionary lesson did the pirates learn?",
            f"They learned that {f['division'].danger}. A fair division must consider need and remain open to checking.",
        ),
    ]


ASP_RULES = r"""
#show valid/3.
valid(P,D,A) :- place(P), division(D), armoire(A), affords(P,armoire), affords(P,division), affords(P,repel).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for pid, setting in SETTINGS.items():
        lines.append(asp.fact("place", pid))
        for affordance in sorted(setting.affordances):
            lines.append(asp.fact("affords", pid, affordance))
    for did in DIVISIONS:
        lines.append(asp.fact("division", did))
    for aid in ARMOIRES:
        lines.append(asp.fact("armoire", aid))
    return "\n".join(lines)


def asp_program(show: str = "#show valid/3.") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program())
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    py = set(valid_combos())
    clingo = set(asp_valid_combos())
    if py != clingo:
        print("ASP/Python mismatch.")
        print("Only in Python:", sorted(py - clingo))
        print("Only in ASP:", sorted(clingo - py))
        return 1
    for params in curated_params():
        sample = generate(params)
        if not sample.story or len(sample.story.split()) < 80:
            print("Generated story failed verification.")
            return 1
    print(f"OK: ASP and Python agree on {len(py)} valid combination(s); stories exercised.")
    return 0


def generate(params: StoryParams) -> StorySample:
    world = build_world(params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=list(KNOWLEDGE),
        world=world,
    )


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    lines.append(f"setting={world.setting.label}")
    for entity in world.entities.values():
        lines.append(
            f"{entity.label}: kind={entity.kind}; meters={entity.meters}; memes={entity.memes}"
        )
    lines.append(f"resolved={world.facts.get('resolved', False)}")
    return "\n".join(lines)


def format_qa(sample: StorySample) -> str:
    lines = ["== Generation prompts =="]
    lines.extend(f"{i}. {p}" for i, p in enumerate(sample.prompts, 1))
    lines.append("\n== Story questions ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}\nA: {item.answer}")
    lines.append("\n== World knowledge ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}\nA: {item.answer}")
    return "\n".join(lines)


def curated_params() -> list[StoryParams]:
    return [
        StoryParams(
            place="saltwind_deck",
            division="cargo_division",
            armoire="captains_armoire",
            hero_name="Luna",
            trait="careful",
            seed=96096,
        )
    ]


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Cautionary pirate tale about an armoire, division, and repel."
    )
    parser.add_argument("--place", choices=SETTINGS)
    parser.add_argument("--division", choices=DIVISIONS)
    parser.add_argument("--armoire", choices=ARMOIRES)
    parser.add_argument("--name")
    parser.add_argument("--trait", choices=TRAITS)
    parser.add_argument("-n", type=int, default=1)
    parser.add_argument("--all", action="store_true")
    parser.add_argument("--seed", type=int)
    parser.add_argument("--trace", action="store_true")
    parser.add_argument("--qa", action="store_true")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--asp", action="store_true")
    parser.add_argument("--verify", action="store_true")
    parser.add_argument("--show-asp", action="store_true")
    return parser


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    combos = valid_combos()
    if args.place:
        combos = [c for c in combos if c[0] == args.place]
    if args.division:
        combos = [c for c in combos if c[1] == args.division]
    if args.armoire:
        combos = [c for c in combos if c[2] == args.armoire]
    if not combos:
        raise StoryError(explain_rejection())
    place, division, armoire = rng.choice(combos)
    return StoryParams(
        place=place,
        division=division,
        armoire=armoire,
        hero_name=args.name or rng.choice(NAMES),
        trait=args.trait or rng.choice(TRAITS),
        seed=args.seed,
    )


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
    if args.show_asp:
        print(asp_program())
        return
    if args.verify:
        raise SystemExit(asp_verify())
    if args.asp:
        print(f"{len(asp_valid_combos())} compatible story combination(s):")
        for combo in asp_valid_combos():
            print("  " + " ".join(map(str, combo)))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in curated_params()]
    else:
        seen = set()
        for index in range(max(args.n, 1) * 20):
            if len(samples) >= args.n:
                break
            seed = base_seed + index
            local_args = argparse.Namespace(**vars(args))
            local_args.seed = seed
            params = resolve_params(local_args, random.Random(seed))
            params.seed = seed
            sample = generate(params)
            if sample.story not in seen:
                seen.add(sample.story)
                samples.append(sample)

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
        if index + 1 < len(samples):
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()

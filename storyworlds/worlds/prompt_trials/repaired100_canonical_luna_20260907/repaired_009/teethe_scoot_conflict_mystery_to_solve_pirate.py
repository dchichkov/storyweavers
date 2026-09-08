#!/usr/bin/env python3
"""
A small pirate storyworld about teething trouble and a mysterious scoot.
A young deckhand must discover why the ship's treasure cart keeps moving,
then settle a conflict by listening carefully and helping a tiny stowaway.
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

_storyworlds_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if not os.path.exists(os.path.join(_storyworlds_dir, "results.py")):
    _storyworlds_dir = os.path.dirname(_storyworlds_dir)
sys.path.insert(0, _storyworlds_dir)
from results import QAItem, StoryError, StorySample  # noqa: E402


@dataclass
class Entity:
    id: str
    kind: str
    label: str
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)


@dataclass(frozen=True)
class Mystery:
    id: str
    clue: str
    cause: str
    solution: str
    consequence: str


@dataclass(frozen=True)
class Conflict:
    id: str
    accusation: str
    truth: str
    repair: str


@dataclass
class Setting:
    id: str
    place: str
    affordances: set[str]


@dataclass
class World:
    setting: Setting
    entities: dict[str, Entity] = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    facts: dict[str, object] = field(default_factory=dict)

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


SETTINGS = {
    "deck": Setting(
        "deck",
        "the moonlit deck",
        {"rope", "cart", "wind", "lantern"},
    ),
    "cove": Setting(
        "cove",
        "a bright pirate cove",
        {"rope", "cart", "wind", "lantern"},
    ),
    "wharf": Setting(
        "wharf",
        "the busy wharf",
        {"rope", "cart", "wind", "lantern"},
    ),
}

MYSTERIES = {
    "rolling_chest": Mystery(
        "rolling_chest",
        "small tooth marks dotted the cart's wooden wheel",
        "a teething cabin pup had been scooting the cart to reach a cool rope knot",
        "offer the pup a clean teething ring and wedge the cart safely",
        "the missing map stayed dry and the pup stopped chewing the wheel",
    ),
    "moving_barrel": Mystery(
        "moving_barrel",
        "a trail of shiny biscuit crumbs led beneath the barrel",
        "a hungry parrot had been pulling a loose ribbon tied to the barrel",
        "follow the crumbs, feed the parrot, and tie the barrel with a proper knot",
        "the barrel stayed put and the parrot returned the ribbon",
    ),
    "vanishing_boot": Mystery(
        "vanishing_boot",
        "one boot was damp and smelled of seaweed",
        "a little seal had been nudging the boot toward a tide pool",
        "place a fish-shaped toy by the water and carry the boot back",
        "the sailor found both boots and the seal splashed happily away",
    ),
}

CONFLICTS = {
    "blame": Conflict(
        "blame",
        "the first mate blamed the youngest deckhand for the trouble",
        "the deckhand had not moved anything; the hidden animal had",
        "speak honestly, show the clues, and solve the problem without blaming anyone",
    ),
    "rush": Conflict(
        "rush",
        "the crew argued about grabbing the wandering object at once",
        "a quick grab could spill the cargo or frighten the small creature",
        "pause, listen, and make a gentle plan before touching the cargo",
    ),
    "ownership": Conflict(
        "ownership",
        "two sailors argued over who should keep the mysterious found object",
        "the object belonged to the whole crew and had to be returned safely",
        "let the crew share the discovery and return the object to its proper place",
    ),
}

NAMES = ["Luna", "Mara", "Pip", "Nico", "Tavi", "Rae"]
CAPTAINS = ["Captain Coral", "Captain Flint", "Captain Maribel"]
TRAITS = ["curious", "brave", "patient", "cheerful", "clever"]


ASP_RULES = r"""
valid_setting(S) :- setting(S), affords(S, rope), affords(S, cart).
valid_mystery(M) :- mystery(M), clue(M), cause(M), solution(M).
valid_conflict(C) :- conflict(C), accusation(C), truth(C), repair(C).
valid_story(S, M, C) :- valid_setting(S), valid_mystery(M), valid_conflict(C).
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for sid, setting in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        for affordance in sorted(setting.affordances):
            lines.append(asp.fact("affords", sid, affordance))
    for mid, mystery in MYSTERIES.items():
        lines.extend(
            [
                asp.fact("mystery", mid),
                asp.fact("clue", mid),
                asp.fact("cause", mid),
                asp.fact("solution", mid),
            ]
        )
    for cid, conflict in CONFLICTS.items():
        lines.extend(
            [
                asp.fact("conflict", cid),
                asp.fact("accusation", cid),
                asp.fact("truth", cid),
                asp.fact("repair", cid),
            ]
        )
    return "\n".join(lines)


def asp_program(show: str = "#show valid_story/3.") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def valid_combos() -> list[tuple[str, str, str]]:
    return [
        (setting, mystery, conflict)
        for setting in SETTINGS
        for mystery in MYSTERIES
        for conflict in CONFLICTS
    ]


def asp_valid() -> set[tuple]:
    import asp

    model = asp.one_model(asp_program())
    return set(asp.atoms(model, "valid_story"))


@dataclass
class StoryParams:
    setting: str
    mystery: str
    conflict: str
    name: str
    captain: str
    trait: str
    opening: int = 0
    turn: int = 0
    ending: int = 0
    seed: Optional[int] = None


def _check_params(params: StoryParams) -> None:
    if params.setting not in SETTINGS:
        raise StoryError(f"Unknown setting: {params.setting}")
    if params.mystery not in MYSTERIES:
        raise StoryError(f"Unknown mystery: {params.mystery}")
    if params.conflict not in CONFLICTS:
        raise StoryError(f"Unknown conflict: {params.conflict}")
    if not params.name.strip():
        raise StoryError("A deckhand needs a name.")
    if not params.captain.strip():
        raise StoryError("A pirate tale needs a captain.")


def build_world(params: StoryParams) -> World:
    _check_params(params)
    setting = SETTINGS[params.setting]
    mystery = MYSTERIES[params.mystery]
    conflict = CONFLICTS[params.conflict]

    world = World(setting)
    hero = world.add(
        Entity(
            params.name,
            "deckhand",
            params.name,
            meters={"cargo_risk": 0.0, "wheel_wear": 0.0},
            memes={"curiosity": 1.0, "worry": 0.0, "courage": 0.0, "kindness": 0.0},
        )
    )
    captain = world.add(
        Entity(
            "captain",
            "captain",
            params.captain,
            meters={"cargo_risk": 0.0},
            memes={"trust": 0.0, "patience": 0.0},
        )
    )
    cart = world.add(
        Entity(
            "cart",
            "cargo cart",
            "the treasure cart",
            meters={"cargo_risk": 1.0, "wheel_wear": 0.0},
            memes={},
        )
    )
    pup = world.add(
        Entity(
            "pup",
            "animal",
            "a little cabin pup",
            meters={"teething": 1.0, "hunger": 0.0},
            memes={"comfort": 0.0},
        )
    )

    openings = [
        (
            f"{hero.label} was a {params.trait} pirate deckhand aboard a small ship. "
            f"One bright morning, {hero.label} worked on {setting.place} while "
            f"{captain.label} counted the cargo."
        ),
        (
            f"At {setting.place}, the crew heard a strange bump. "
            f"{hero.label}, the ship's {params.trait} deckhand, looked up from a coil of rope "
            f"and saw the treasure cart scoot three inches by itself."
        ),
        (
            f"The sea was calm, but the work on {setting.place} was not. "
            f"{hero.label} had just polished the lantern when the treasure cart rolled away "
            f"from the captain's boots."
        ),
        (
            f"Every pirate aboard knew that {hero.label} was {params.trait}. "
            f"That was useful when a mystery appeared beside the cargo cart at {setting.place}."
        ),
    ]

    world.say(openings[params.opening % len(openings)])
    world.say(
        f"The cart gave another little scoot, and {mystery.clue}. "
        f"No one could tell what was moving it."
    )
    world.para()

    world.say(f"{conflict.accusation.capitalize()}.")
    world.say(
        f'"I did not touch the cart," {hero.label} said. '
        f'"Then show us what you know," {captain.label} replied.'
    )
    hero.memes["worry"] += 1
    cart.meters["cargo_risk"] += 1

    world.para()
    world.say(
        f"{hero.label} did not shout back. Instead, the deckhand knelt beside the wheel "
        f"and studied the clues. {mystery.clue.capitalize()}."
    )
    world.say(
        f'"A mystery needs more than a guess," {hero.label} said. '
        f'"Let us follow the trail before we blame anyone."'
    )
    captain.memes["patience"] += 1
    hero.memes["courage"] += 1

    world.para()
    world.say(f"The trail led beneath the cart, where the crew discovered that {mystery.cause}.")
    world.say(
        f"The frightened little creature tried to scoot away. "
        f"{hero.label} lowered a hand and said, "
        f'"Easy, matey. We can fix this without making you afraid."'
    )
    hero.memes["kindness"] += 1
    pup.memes["comfort"] += 1
    pup.meters["teething"] = 0.0
    cart.meters["cargo_risk"] = 0.0
    cart.meters["wheel_wear"] = 0.0

    world.para()
    plans = [
        f"{hero.label} followed the plan to {mystery.solution}.",
        f"Together, the pirates decided to {mystery.solution}.",
        f"The captain listened, and the crew helped {hero.label} {mystery.solution}.",
        f"With a calm word and a careful knot, {hero.label} chose to {mystery.solution}.",
    ]
    world.say(plans[params.turn % len(plans)])
    world.say(
        f"{mystery.consequence.capitalize()}. "
        f"The cart stayed firm, and the deck grew quiet again."
    )
    captain.memes["trust"] += 1

    world.para()
    endings = [
        f"At sunset, {captain.label} thanked {hero.label} for solving the mystery without a fight. "
        f"The little pup slept beside its new teething ring while the sea shone like blue glass.",
        f"The crew cheered when the cargo was safe. {hero.label} scratched the pup's ears, "
        f"and the once-scooting cart rested peacefully beneath the lantern.",
        f"By evening, the argument had faded into laughter. "
        f"{captain.label} tied a bright ribbon around the cart, and the pup proudly carried its toy.",
        f"That night, {hero.label} wrote the clue in the ship's log. "
        f"Beside the cart, the happy pup gnawed its ring instead of the wheel.",
    ]
    world.say(endings[params.ending % len(endings)])

    world.facts.update(
        hero=hero,
        captain=captain,
        cart=cart,
        pup=pup,
        mystery=mystery,
        conflict=conflict,
    )
    return world


def prompts(world: World) -> list[str]:
    mystery = world.facts["mystery"]
    hero = world.facts["hero"]
    return [
        f"Write a child-friendly pirate tale about {hero.label} solving a mystery involving teethe and scoot.",
        f"Tell a pirate story where a treasure cart scoots away, a conflict begins, and careful clues reveal why.",
        f"Write a gentle pirate adventure about a deckhand who helps a teething animal instead of blaming it.",
    ]


def story_qa(world: World) -> list[QAItem]:
    hero = world.facts["hero"]
    captain = world.facts["captain"]
    mystery = world.facts["mystery"]
    conflict = world.facts["conflict"]
    return [
        QAItem(
            "What mystery did the pirates need to solve?",
            "They needed to discover why the treasure cart kept scooting away.",
        ),
        QAItem(
            f"Why did {captain.label} first become upset with {hero.label}?",
            f"{captain.label} thought {hero.label} might have moved the cart, but the clues later showed that was not true.",
        ),
        QAItem(
            "What clue helped reveal the truth?",
            f"The pirates noticed that {mystery.clue}.",
        ),
        QAItem(
            "How did the crew settle their conflict?",
            f"They listened, followed the clues, and chose to {conflict.repair}.",
        ),
        QAItem(
            "What changed at the end?",
            "The cargo was safe, the cart stopped scooting, and the small animal had a kinder thing to chew.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            "What does teethe mean?",
            "To teethe means to grow new teeth, which can make a young animal want to chew safe objects.",
        ),
        QAItem(
            "What does scoot mean?",
            "To scoot means to move a short distance quickly or with little steps.",
        ),
        QAItem(
            "What is a conflict?",
            "A conflict is a disagreement or problem between people that needs care and a fair solution.",
        ),
        QAItem(
            "What is a mystery to solve?",
            "A mystery to solve is a question whose answer is discovered by noticing clues and thinking carefully.",
        ),
        QAItem(
            "What is a pirate deck?",
            "A pirate deck is the floor or working space on a ship.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    sections = ["== prompts =="]
    sections.extend(sample.prompts)
    sections.append("")
    sections.append("== story qa ==")
    for item in sample.story_qa:
        sections.append(f"Q: {item.question}")
        sections.append(f"A: {item.answer}")
    sections.append("")
    sections.append("== world qa ==")
    for item in sample.world_qa:
        sections.append(f"Q: {item.question}")
        sections.append(f"A: {item.answer}")
    return "\n".join(sections)


def generate(params: StoryParams) -> StorySample:
    world = build_world(params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for entity in world.entities.values():
        meters = {k: v for k, v in entity.meters.items() if v}
        memes = {k: v for k, v in entity.memes.items() if v}
        lines.append(f"{entity.label}: meters={meters} memes={memes}")
    return "\n".join(lines)


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


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Pirate storyworld about teething, scooting, conflict, and a mystery."
    )
    parser.add_argument("--setting", choices=sorted(SETTINGS))
    parser.add_argument("--mystery", choices=sorted(MYSTERIES))
    parser.add_argument("--conflict", choices=sorted(CONFLICTS))
    parser.add_argument("--name")
    parser.add_argument("--captain", choices=CAPTAINS)
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
    setting = args.setting or rng.choice(sorted(SETTINGS))
    mystery = args.mystery or rng.choice(sorted(MYSTERIES))
    conflict = args.conflict or rng.choice(sorted(CONFLICTS))
    return StoryParams(
        setting=setting,
        mystery=mystery,
        conflict=conflict,
        name=args.name or rng.choice(NAMES),
        captain=args.captain or rng.choice(CAPTAINS),
        trait=args.trait or rng.choice(TRAITS),
        opening=rng.randrange(4),
        turn=rng.randrange(4),
        ending=rng.randrange(4),
    )


def asp_verify() -> int:
    python_answers = set(valid_combos())
    asp_answers = asp_valid()
    if python_answers == asp_answers:
        print(f"OK: ASP and Python agree on {len(python_answers)} valid stories.")
        for params in CURATED:
            generate(params)
        print("OK: curated stories generated successfully.")
        return 0
    print("Mismatch between ASP and Python:")
    print("Only Python:", sorted(python_answers - asp_answers))
    print("Only ASP:", sorted(asp_answers - python_answers))
    return 1


CURATED = [
    StoryParams(
        setting="deck",
        mystery="rolling_chest",
        conflict="blame",
        name="Luna",
        captain="Captain Coral",
        trait="curious",
    ),
    StoryParams(
        setting="cove",
        mystery="moving_barrel",
        conflict="rush",
        name="Mara",
        captain="Captain Flint",
        trait="patient",
        opening=1,
        turn=1,
        ending=1,
    ),
    StoryParams(
        setting="wharf",
        mystery="vanishing_boot",
        conflict="ownership",
        name="Pip",
        captain="Captain Maribel",
        trait="clever",
        opening=2,
        turn=2,
        ending=2,
    ),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp or args.asp:
        print(asp_program())
        return

    if args.verify:
        raise SystemExit(asp_verify())

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(params) for params in CURATED]
    else:
        seen: set[str] = set()
        attempts = 0
        while len(samples) < args.n and attempts < max(50, args.n * 50):
            rng = random.Random(base_seed + attempts)
            params = resolve_params(args, rng)
            params.seed = base_seed + attempts
            sample = generate(params)
            if sample.story not in seen:
                seen.add(sample.story)
                samples.append(sample)
            attempts += 1

    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([sample.to_dict() for sample in samples], indent=2, ensure_ascii=False))
        return

    for index, sample in enumerate(samples):
        header = f"### variant {index + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if index < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()

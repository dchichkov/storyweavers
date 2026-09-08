#!/usr/bin/env python3
"""
kiss_sugar_sentry_twist_bad_ending_bravery.py
==============================================

A small Pirate Tale world about a brave deckhand, a sugar-coated kiss,
and a sentry whose warning reveals a dangerous twist.

The story model tracks physical meters and emotional memes.  A tempting
sweet, a guarded treasure, and a choice between courage and care produce
different endings, including an intentionally bad ending for the lookout
who ignores the warning.
"""

from __future__ import annotations

import argparse
import json
import os
import random
import sys
from dataclasses import dataclass, field
from typing import Optional

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
sys.path.insert(0, ROOT)
from results import QAItem, StoryError, StorySample  # noqa: E402


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class Setting:
    place: str
    affords: set[str] = field(default_factory=set)


@dataclass
class Cargo:
    id: str
    label: str
    lure: str
    danger: str


@dataclass
class Watch:
    id: str
    name: str
    warning: str
    gerund: str


@dataclass
class World:
    setting: Setting
    entities: dict[str, Entity] = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    facts: dict = field(default_factory=dict)

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
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)


SETTINGS = {
    "deck": Setting("the moonlit deck", {"watch"}),
}

CARGO = {
    "sugar": Cargo(
        "sugar",
        "a sugar kiss",
        "smell sweet enough to make a sailor forget the sea",
        "a sticky trail leading toward the captain's locked chest",
    )
}

WATCHES = {
    "sentry": Watch(
        "sentry",
        "the harbor sentry",
        "the fog is hiding a false starboard light",
        "keeping watch",
    )
}

NAMES = ["Luna", "Mara", "Pip", "Tess", "Nell"]
SPECIES = ["parrot", "cat", "mouse", "puppy", "fox"]
TRAITS = ["brave", "curious", "steady", "clever", "kind"]
HELPERS = ["Sentry", "Captain", "Bo"]
SCENARIOS = [
    {
        "id": "false_light",
        "premise": "The ship drifted toward a reef while a sugar kiss cooled beside the captain's spyglass.",
        "twist": "The bright beacon ahead was not a harbor lamp at all, but a lantern tied to a pirate's decoy buoy.",
        "mistake": "reached for the sugar kiss instead of studying the dark water",
        "clue": "the sentry's bell ringing three sharp times",
        "repair": "climbed the rigging, covered the false light, and guided the ship toward the real stars",
        "lesson": "bravery means acting when a warning matters more than a treat",
        "ending": "the ship sailed safely past the reef, with the sugar kiss shared under a sky full of honest stars",
    },
    {
        "id": "empty_chest",
        "premise": "A sugar kiss marked the deck beside a chest that everyone believed held the queen's map.",
        "twist": "The chest was empty, and the sugar had been sprinkled in a trail toward a trapdoor.",
        "mistake": "opened the chest loudly and laughed at the dusty scraps inside",
        "clue": "the sentry pointing to fresh boot marks beneath the table",
        "repair": "whispered the warning to the crew, barred the trapdoor, and returned the map scraps to the sentry",
        "lesson": "bravery can be quiet, careful, and shared",
        "ending": "the false treasure stayed shut while the real map dried safely beside the warm galley stove",
    },
    {
        "id": "storm_signal",
        "premise": "A kiss-shaped sugar cloud floated from the galley as a storm curled around the ship.",
        "twist": "The cloud was smoke from a torn sail, not the sweet steam the crew had expected.",
        "mistake": "chased the sugary smell toward the bow without checking the rigging",
        "clue": "the sentry's wet flag snapping from the wrong side of the mast",
        "repair": "told the crew what was wrong, tied a safety rope, and helped lower the torn sail",
        "lesson": "bravery grows when someone tells the truth before danger grows",
        "ending": "the repaired sail filled at dawn, and the last sugar kiss rested in the sentry's dry mitten",
    },
]

OPENINGS = [
    "At dawn, {hero} the {trait} {species} stood on the moonlit deck with salt on {possessive} whiskers.",
    "The pirate ship creaked beneath a violet sky when {hero}, a {trait} {species}, began {watch}.",
    "A brass bell woke {hero} before breakfast, and the young {species} hurried onto the moonlit deck.",
    "Beyond the rail, the sea glittered like a treasure chest as {hero} the {species} took the first watch.",
]

DIALOGUE = [
    '"Do not chase the sweet smell," said {helper}. "Tell me what you see beyond it."',
    '"That warning is real," {helper} said. "Will you help me keep the crew safe?"',
    '"A brave sailor listens before leaping," said {helper}. "Look again."',
    '"The kiss can wait," {helper} whispered. "The ship cannot."',
]

VALID_ENDINGS = {"brave", "bad"}


def valid_combos() -> list[tuple[str, str, str]]:
    return [
        (place, watch, cargo)
        for place, setting in SETTINGS.items()
        for watch in setting.affords
        for cargo in CARGO
        if watch in WATCHES
    ]


ASP_RULES = r"""
place(deck).
affords(deck,watch).
watch(sentry).
cargo(sugar).
valid(Place,Watch,Cargo) :- place(Place), affords(Place,Watch), watch(Watch), cargo(Cargo).
#show valid/3.
"""


def asp_facts() -> str:
    import asp

    lines = []
    for place in SETTINGS:
        lines.append(asp.fact("place", place))
    for place, setting in SETTINGS.items():
        for watch in sorted(setting.affords):
            lines.append(asp.fact("affords", place, watch))
    for watch in WATCHES:
        lines.append(asp.fact("watch", watch))
    for cargo in CARGO:
        lines.append(asp.fact("cargo", cargo))
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
    if py == clingo:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between Python and clingo:")
    print("  only in Python:", sorted(py - clingo))
    print("  only in clingo:", sorted(clingo - py))
    return 1


@dataclass
class StoryParams:
    place: str
    watch: str
    cargo: str
    name: str
    species: str
    helper: str
    trait: str
    ending: str = "brave"
    scenario: str = "false_light"
    seed: Optional[int] = None
    telling: int = 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Pirate Tale: a sugar kiss, a sentry, and a brave twist.")
    parser.add_argument("--place", choices=SETTINGS)
    parser.add_argument("--watch", choices=WATCHES)
    parser.add_argument("--cargo", choices=CARGO)
    parser.add_argument("--name")
    parser.add_argument("--species", choices=SPECIES)
    parser.add_argument("--helper", choices=HELPERS)
    parser.add_argument("--trait", choices=TRAITS)
    parser.add_argument("--ending", choices=sorted(VALID_ENDINGS))
    parser.add_argument("--scenario", choices=[s["id"] for s in SCENARIOS])
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
    combos = [
        combo for combo in valid_combos()
        if args.place is None or combo[0] == args.place
        if args.watch is None or combo[1] == args.watch
        if args.cargo is None or combo[2] == args.cargo
    ]
    if not combos:
        raise StoryError("No valid pirate combination matches the requested options.")
    place, watch, cargo = rng.choice(combos)
    name = args.name or rng.choice(NAMES)
    species = args.species or rng.choice(SPECIES)
    helper = args.helper or rng.choice(HELPERS)
    trait = args.trait or rng.choice(TRAITS)
    ending = args.ending or rng.choice(sorted(VALID_ENDINGS))
    scenario = args.scenario or rng.choice(SCENARIOS)["id"]
    return StoryParams(
        place=place,
        watch=watch,
        cargo=cargo,
        name=name,
        species=species,
        helper=helper,
        trait=trait,
        ending=ending,
        scenario=scenario,
        telling=rng.randrange(1_000_000),
    )


def run_brave_path(world: World, hero: Entity, helper: Entity, scenario: dict, cargo: Cargo, watch: Watch) -> None:
    hero.memes["bravery"] = 2
    hero.memes["trust"] = 1
    hero.meters["danger"] = 0
    helper.memes["relief"] = 1
    world.facts["resolved"] = True
    world.say(
        f"{hero.id} swallowed the wish for {cargo.label}, took a deep breath, "
        f"and answered the {watch.name}'s warning."
    )
    world.say(
        f"{hero.id} {scenario['repair']}. The crew worked together because "
        f"{hero.id} had been brave enough to speak."
    )


def run_bad_path(world: World, hero: Entity, helper: Entity, scenario: dict, cargo: Cargo, watch: Watch) -> None:
    hero.memes["bravery"] = 0
    hero.memes["regret"] = 2
    hero.meters["danger"] = 2
    helper.memes["alarm"] = 2
    world.facts["resolved"] = False
    world.say(
        f"{hero.id} ignored the {watch.name} and bit into {cargo.label}. "
        f"The sugary taste hid the first groan of the ship's timbers."
    )
    world.say(
        f"By the time {hero.id} looked up, {scenario['twist'].capitalize()} "
        f"The crew scrambled, and the bright promise of the voyage became a bad ending."
    )


def generate(params: StoryParams) -> StorySample:
    setting = SETTINGS[params.place]
    cargo = CARGO[params.cargo]
    watch = WATCHES[params.watch]
    scenario = next(item for item in SCENARIOS if item["id"] == params.scenario)
    rng = random.Random(params.telling)

    world = World(setting)
    hero = world.add(Entity(params.name, "character", params.species))
    helper = world.add(Entity(params.helper, "character", "adult"))
    world.add(Entity("kiss", "thing", "sweet", label="kiss"))
    world.add(Entity("sugar", "thing", "cargo", label="sugar"))
    world.add(Entity("sentry", "character", "sentry", label="sentry"))

    values = {
        "hero": hero.id,
        "helper": helper.id,
        "species": params.species,
        "trait": params.trait,
        "possessive": hero.pronoun("possessive"),
        "watch": watch.gerund,
    }

    opening = rng.choice(OPENINGS).format(**values)
    dialogue = rng.choice(DIALOGUE).format(**values)
    turn_line = rng.choice([
        "That was the twist: the thing that looked cheerful had been hiding the danger.",
        f"For the first time, {hero.id} understood that a brave choice could taste less sweet and matter much more.",
        "The deck seemed to tilt between a tempting promise and a warning that needed an answer.",
    ])

    world.say(opening)
    world.say(
        f"Near the wheel lay {cargo.label}, a little kiss of {params.cargo} that "
        f"could {cargo.lure}."
    )
    world.para()
    world.say(
        f"The {watch.name} raised a lantern. {scenario['premise']} "
        f"{hero.id} {scenario['mistake']}."
    )
    world.say(dialogue)
    world.para()
    world.say(f"Then came the turn. {scenario['clue'].capitalize()}. {turn_line}")
    world.say(f"{scenario['twist']} {hero.id} finally saw the danger.")
    world.say(f'"I choose the crew first," {hero.id} said. "I will help."')
    world.para()

    if params.ending == "brave":
        run_brave_path(world, hero, helper, scenario, cargo, watch)
        world.say(
            f"{helper.id} clasped {hero.id}'s paw. \"That was bravery,\" "
            f"{helper.id} said. \"You listened, then acted.\""
        )
        world.say(
            f"When the sea calmed, {hero.id} shared the {cargo.label} with the crew. "
            f"{scenario['ending']}"
        )
    else:
        run_bad_path(world, hero, helper, scenario, cargo, watch)
        world.say(
            f"The {watch.name} saved what could be saved, but {hero.id} felt the "
            f"weight of the choice long after the sugar had melted."
        )
        world.say(
            f"The bad ending left {scenario['ending']} "
            f"Even a small warning deserves a brave answer."
        )

    world.facts.update({
        "hero": hero,
        "helper": helper,
        "cargo": cargo,
        "watch": watch,
        "scenario": scenario,
        "ending": params.ending,
        "twist": scenario["twist"],
        "clue": scenario["clue"],
        "repair": scenario["repair"],
        "lesson": scenario["lesson"],
        "resolved": world.facts.get("resolved", False),
    })

    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_qa(world),
        world=world,
    )


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        "Write a child-friendly Pirate Tale containing a kiss, sugar, and a sentry.",
        f"Tell how {f['hero'].id} discovers a twist and must choose bravery over a tempting treat.",
        "Write a pirate story with both a brave ending and the possibility of a bad ending.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    watch = f["watch"]
    cargo = f["cargo"]
    if f["ending"] == "brave":
        outcome = (
            f"{hero.id} listened to {watch.name}, helped repair the danger, and shared "
            f"{cargo.label} only after the crew was safe."
        )
    else:
        outcome = (
            f"{hero.id} ignored {watch.name} long enough for danger to grow; the "
            f"tempting {cargo.label} led to a bad ending."
        )
    return [
        QAItem(
            question=f"What was tempting {hero.id} on the ship?",
            answer=f"{hero.id} was tempted by {cargo.label}, whose sweet smell made the danger easy to overlook.",
        ),
        QAItem(
            question="What was the twist?",
            answer=f"The twist was that {f['twist']} This changed the problem from a simple treat to a serious danger.",
        ),
        QAItem(
            question=f"What warning did {watch.name} give?",
            answer=f"{watch.name} gave this important clue: {f['clue']}. It helped reveal what was really happening.",
        ),
        QAItem(
            question=f"How did {hero.id} show bravery?",
            answer=(
                f"{hero.id} {f['repair']} "
                if f["ending"] == "brave"
                else f"{hero.id} should have answered the warning sooner; ignoring it caused the bad ending."
            ),
        ),
        QAItem(
            question="What does the ending teach?",
            answer=f"The story teaches that {f['lesson']}.",
        ),
        QAItem(question="What happened at the end?", answer=outcome),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a sentry?",
            answer="A sentry is a person or creature who keeps watch and warns others about danger.",
        ),
        QAItem(
            question="What is sugar?",
            answer="Sugar is a sweet substance often used to flavor food and treats.",
        ),
        QAItem(
            question="What is a kiss?",
            answer="A kiss is a gentle touch with the lips, often used to show affection or care.",
        ),
        QAItem(
            question="What is bravery?",
            answer="Bravery means facing a difficult or frightening situation while choosing to do what is right.",
        ),
        QAItem(
            question="What is a twist in a story?",
            answer="A twist is a surprising change that reveals the situation is different from what it first seemed.",
        ),
        QAItem(
            question="What is a bad ending?",
            answer="A bad ending is an ending in which a poor choice leaves danger, loss, or regret instead of solving the problem.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== Prompts =="]
    lines.extend(f"- {prompt}" for prompt in sample.prompts)
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
        meters = {key: value for key, value in entity.meters.items() if value}
        memes = {key: value for key, value in entity.memes.items() if value}
        details = []
        if meters:
            details.append(f"meters={meters}")
        if memes:
            details.append(f"memes={memes}")
        lines.append(f"{entity.id}: {entity.type} {' '.join(details)}".rstrip())
    lines.append(f"facts: resolved={world.facts.get('resolved')}, ending={world.facts.get('ending')}")
    return "\n".join(lines)


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world is not None:
        print(dump_trace(sample.world))
    if qa:
        print()
        print(format_qa(sample))


CURATED = [
    StoryParams(
        place="deck",
        watch="sentry",
        cargo="sugar",
        name="Luna",
        species="parrot",
        helper="Sentry",
        trait="brave",
        ending="brave",
        scenario="false_light",
        telling=101,
    ),
    StoryParams(
        place="deck",
        watch="sentry",
        cargo="sugar",
        name="Mara",
        species="cat",
        helper="Captain",
        trait="curious",
        ending="bad",
        scenario="empty_chest",
        telling=202,
    ),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program())
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible combos:")
        for combo in combos:
            print(" ", combo)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(params) for params in CURATED]
    else:
        seen: set[str] = set()
        index = 0
        while len(samples) < args.n and index < max(args.n * 30, 30):
            seed = base_seed + index
            index += 1
            try:
                params = resolve_params(args, random.Random(seed))
            except StoryError as error:
                print(error)
                return
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
        header = f"### variant {index + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if index < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()

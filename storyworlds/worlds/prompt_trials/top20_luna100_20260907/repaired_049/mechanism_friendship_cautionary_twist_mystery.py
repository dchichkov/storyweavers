#!/usr/bin/env python3
"""
A child-facing mystery storyworld about a strange mechanism, friendship, and a
cautionary twist.
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
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)


@dataclass
class World:
    entities: dict[str, Entity] = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    facts: dict = field(default_factory=dict)
    fired: set[str] = field(default_factory=set)

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


@dataclass(frozen=True)
class Case:
    opening: str
    clue: str
    danger: str
    false_lead: str
    mechanism: str
    careful_action: str
    twist: str
    result: str
    ending: str
    lesson: str


@dataclass
class StoryParams:
    place: str
    mechanism: str
    name: str
    friend: str
    trait: str
    seed: Optional[int] = None


PLACES = {
    "clocktower": "the abandoned clocktower",
    "boathouse": "the old boathouse",
    "greenhouse": "the glass greenhouse",
}

MECHANISMS = {
    "brass_wheel": "a brass wheel",
    "bell_key": "a bell-shaped key",
    "mirror_latch": "a mirror latch",
}

NAMES = ["Luna", "Mira", "Nia", "Tessa", "Ivy", "Suri"]
FRIENDS = ["Pip", "Theo", "Milo", "June", "Ari", "Bo"]
TRAITS = ["curious", "patient", "brave", "careful", "observant"]

CASES = [
    Case(
        "For three nights, a pale light blinked inside the abandoned clocktower.",
        "Luna found tiny wet footprints leading away from the tower, though the night had been dry.",
        "A loose stair could drop anyone who climbed too quickly.",
        "A crow perched on the roof made the tower seem watched.",
        "The brass wheel turned only when a hidden weight beneath the stair was lifted.",
        "Luna and her friend marked the loose stair, tied a cord around it, and tested the wheel from the floor.",
        "The blinking light was not a ghost's signal at all; it was a safety lamp connected to the old clock.",
        "The friends reset the weight, and the lamp shone steadily.",
        "At dawn, the clocktower showed one calm golden light instead of three mysterious flashes.",
        "A mystery is safer when friends test clues before they chase a frightening answer.",
    ),
    Case(
        "A bell rang from the old boathouse whenever the moon rose.",
        "The mud below the door held two sets of footprints, but one set ended at the water.",
        "The rotten dock could break beneath a rushing investigator.",
        "A silver fish jumping near the boathouse seemed to point toward the lake.",
        "The bell-shaped key opened a dry signal box hidden behind a life ring.",
        "Luna kept her friend on firm ground while they used a boat hook to draw the life ring close.",
        "The second footprint trail belonged to a heron; the bell had been ringing because wind moved the key inside the box.",
        "They secured the key and repaired the box without stepping onto the rotten dock.",
        "By morning, the boathouse bell rang only when a real boat needed help.",
        "A clever clue does not make a dangerous shortcut wise.",
    ),
    Case(
        "The glass greenhouse whispered at midnight, although every window was shut.",
        "A row of leaves trembled in a perfect line toward a locked potting bench.",
        "The roof glass was cracked above the bench.",
        "A shadow crossing the moon made the whisper sound like a hidden visitor.",
        "The mirror latch opened a vent beneath the bench and redirected air through hollow bamboo stems.",
        "Luna and her friend stood outside the cracked roof, used a long-handled mirror, and opened the vent from safety.",
        "The secret whisper came from the greenhouse breathing through its old watering pipes.",
        "The air flowed quietly, and the seedlings stopped shaking.",
        "In the morning, sunlight crossed the repaired vent and made the plants sparkle.",
        "Friendship means warning one another when wonder begins to hide a risk.",
    ),
    Case(
        "A locked cupboard in the village hall clicked every evening.",
        "Dust showed that the cupboard door had not opened, but the floor beneath it had shifted.",
        "Pulling the cupboard could make the tall shelves topple.",
        "Someone had scratched a tiny arrow beside the lock.",
        "A brass wheel under the floor turned the cupboard's hidden stabilizer.",
        "Luna asked her friend to hold the shelf line while she used a broom handle to turn the wheel.",
        "The arrow was left by an old caretaker, not by a thief; it warned people not to pull the cupboard.",
        "The stabilizer settled the shelves, and the clicking stopped.",
        "The hall remained quiet while the warning arrow was painted bright blue.",
        "A cautionary mark can be a gift from someone who solved the danger before you.",
    ),
]


def meter(entity: Entity, key: str) -> float:
    return entity.meters.get(key, 0.0)


def meme(entity: Entity, key: str) -> float:
    return entity.memes.get(key, 0.0)


def add_meter(entity: Entity, key: str, amount: float = 1.0) -> None:
    entity.meters[key] = meter(entity, key) + amount


def add_meme(entity: Entity, key: str, amount: float = 1.0) -> None:
    entity.memes[key] = meme(entity, key) + amount


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Generate a friendship mystery about a mechanism and a cautionary twist."
    )
    parser.add_argument("--place", choices=PLACES)
    parser.add_argument("--mechanism", choices=MECHANISMS)
    parser.add_argument("--name")
    parser.add_argument("--friend")
    parser.add_argument("--trait", choices=TRAITS)
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
    place = args.place or rng.choice(list(PLACES))
    mechanism = args.mechanism or rng.choice(list(MECHANISMS))
    name = args.name or rng.choice(NAMES)
    friend = args.friend or rng.choice([n for n in FRIENDS if n != name])
    trait = args.trait or rng.choice(TRAITS)
    if name == friend:
        raise StoryError("The detective and friend must have different names.")
    return StoryParams(place, mechanism, name, friend, trait, args.seed)


def reasonableness_gate(params: StoryParams) -> None:
    if params.place not in PLACES:
        raise StoryError("The chosen place is not in the mystery registry.")
    if params.mechanism not in MECHANISMS:
        raise StoryError("The chosen mechanism is not in the mystery registry.")
    if params.name == params.friend:
        raise StoryError("A friendship mystery needs two different friends.")


def choose_case(params: StoryParams) -> Case:
    value = params.seed
    if value is None:
        value = sum((i + 1) * ord(c) for i, c in enumerate(
            f"{params.place}|{params.mechanism}|{params.name}|{params.friend}"
        ))
    return CASES[value % len(CASES)]


def tell(world: World, params: StoryParams) -> None:
    case = choose_case(params)
    hero = world.add(Entity(params.name, "character", "child", params.name))
    friend = world.add(Entity(params.friend, "character", "friend", params.friend))
    device = world.add(
        Entity(
            "mechanism",
            "thing",
            "mechanism",
            MECHANISMS[params.mechanism],
        )
    )
    add_meme(hero, "curiosity")
    add_meme(friend, "trust")

    world.say(
        f"{params.name}, a {params.trait} child, visited {PLACES[params.place]} with {params.friend}."
    )
    world.say(case.opening)
    world.say(
        f"Near the door, they discovered {MECHANISMS[params.mechanism]}, an old mechanism with a bright scratch across its center."
    )
    world.para()

    world.say(case.clue)
    world.say(case.danger)
    world.say(f"The first clue pointed toward an easy answer: {case.false_lead}")
    world.say(
        f'"Let us not touch it yet," {params.friend} said. "{case.danger.split(".")[0]}."'
    )
    world.say(
        f'"You are right," {params.name} replied. "We can learn more without stepping into danger."'
    )
    add_meme(hero, "caution")
    add_meme(friend, "caution")
    world.para()

    world.say(f"They studied the mechanism. {case.mechanism}")
    world.say(
        f"{params.name} wanted to follow the exciting clue, but friendship changed the plan: {case.careful_action}"
    )
    add_meter(hero, "evidence", 1.0)
    add_meter(friend, "help", 1.0)
    world.say(
        f"Then came the twist: {case.twist}"
    )
    add_meme(hero, "understanding")
    world.para()

    world.say(f"The mystery was solved safely. {case.result}")
    world.say(
        f"{params.friend} smiled. " 
        f'"A good mystery should leave everyone safer," {params.friend} said.'
    )
    world.say(f"{params.name} agreed, and the caution became part of the solution: {case.lesson}")
    world.say(case.ending)

    world.facts.update(
        hero=hero,
        friend=friend,
        device=device,
        case=case,
        place=PLACES[params.place],
    )


def generate(params: StoryParams) -> StorySample:
    reasonableness_gate(params)
    world = World()
    tell(world, params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(),
        world=world,
    )


def generation_prompts(world: World) -> list[str]:
    hero = world.facts["hero"]
    friend = world.facts["friend"]
    device = world.facts["device"]
    return [
        f"Write a child-friendly mystery in which {hero.id} and {friend.id} investigate {device.label}.",
        "Include a mechanism, a friendship exchange, a cautionary danger, and a surprising twist.",
        "Let the clues change the characters' plan instead of making them rush into danger.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    friend = f["friend"]
    case = f["case"]
    device = f["device"]
    return [
        QAItem(
            f"Who investigated the mystery?",
            f"{hero.id} investigated the mystery with {friend.id}, their friend and careful partner.",
        ),
        QAItem(
            "What mechanism did they find?",
            f"They found {device.label}, an old mechanism connected to the strange event.",
        ),
        QAItem(
            "What danger did they notice?",
            f"They noticed this danger: {case.danger}",
        ),
        QAItem(
            "How did friendship help?",
            f"{friend.id} warned {hero.id}, and together they chose to investigate safely: {case.careful_action}",
        ),
        QAItem(
            "What was the twist?",
            f"The surprising twist was that {case.twist}",
        ),
        QAItem(
            "How did the mystery end?",
            f"They solved it safely because {case.result}",
        ),
        QAItem(
            "What caution did they learn?",
            f"They learned that {case.lesson}",
        ),
    ]


def world_knowledge_qa() -> list[QAItem]:
    return [
        QAItem(
            "What is a mechanism?",
            "A mechanism is a set of parts that work together to cause an action, such as turning, opening, or moving.",
        ),
        QAItem(
            "Why is caution useful in a mystery?",
            "Caution is useful because it lets people examine clues without creating a new danger.",
        ),
        QAItem(
            "How can friendship help investigators?",
            "Friends can notice different clues, warn one another, and make safer decisions together.",
        ),
        QAItem(
            "What is a twist?",
            "A twist is a surprising change in what a story seems to mean.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== Prompts =="]
    lines.extend(f"{i}. {p}" for i, p in enumerate(sample.prompts, 1))
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
    lines = ["--- trace ---"]
    for entity in world.entities.values():
        lines.append(
            f"{entity.id}: {entity.type} meters={entity.meters} memes={entity.memes}"
        )
    return "\n".join(lines)


ASP_RULES = r"""
place(clocktower). place(boathouse). place(greenhouse).
mechanism(brass_wheel). mechanism(bell_key). mechanism(mirror_latch).
valid(P,M) :- place(P), mechanism(M).
"""


def asp_facts() -> str:
    import asp
    return "\n".join(
        [
            asp.fact("place", "clocktower"),
            asp.fact("place", "boathouse"),
            asp.fact("place", "greenhouse"),
            asp.fact("mechanism", "brass_wheel"),
            asp.fact("mechanism", "bell_key"),
            asp.fact("mechanism", "mirror_latch"),
        ]
    )


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combinations() -> set[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/2."))
    return set(asp.atoms(model, "valid"))


def valid_combinations() -> set[tuple]:
    return {(place, mechanism) for place in PLACES for mechanism in MECHANISMS}


def asp_verify() -> int:
    expected = valid_combinations()
    actual = asp_valid_combinations()
    if expected != actual:
        print(f"MISMATCH: Python={sorted(expected)} ASP={sorted(actual)}")
        return 1
    for params in [
        StoryParams("clocktower", "brass_wheel", "Luna", "Pip", "curious"),
        StoryParams("greenhouse", "mirror_latch", "Mira", "Theo", "careful"),
    ]:
        generate(params)
    print(f"OK: ASP matches Python ({len(expected)} combinations); stories generated.")
    return 0


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
    if trace and sample.world:
        print(dump_trace(sample.world))
    if qa:
        print()
        print(format_qa(sample))


CURATED = [
    StoryParams("clocktower", "brass_wheel", "Luna", "Pip", "curious"),
    StoryParams("boathouse", "bell_key", "Mira", "Theo", "patient"),
    StoryParams("greenhouse", "mirror_latch", "Nia", "June", "careful"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid/2."))
        return
    if args.verify:
        raise SystemExit(asp_verify())
    if args.asp:
        print(asp_program("#show valid/2."))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        for index in range(max(args.n, 1) * 20):
            if len(samples) >= args.n:
                break
            seed = base_seed + index
            rng = random.Random(seed)
            try:
                params = resolve_params(args, rng)
                params.seed = seed
                sample = generate(params)
            except StoryError as error:
                print(error)
                return
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
        header = ""
        if args.all:
            header = f"### {sample.params.name}: {sample.params.place}"
        elif len(samples) > 1:
            header = f"### variant {index + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if index < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()

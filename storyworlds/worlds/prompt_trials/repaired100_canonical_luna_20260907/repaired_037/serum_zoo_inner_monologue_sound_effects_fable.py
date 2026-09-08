#!/usr/bin/env python3
"""
A small fable world about a serum, a zoo, an inner promise, and careful listening.

A young keeper must decide whether to rush a helpful serum to a sick animal.
Soft sound effects and an inner monologue guide a patient choice.
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

sys.path.insert(
    0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
)
from results import QAItem, StoryError, StorySample  # noqa: E402


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)


@dataclass
class Setting:
    place: str
    affords: set[str] = field(default_factory=set)


@dataclass
class StoryState:
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


@dataclass
class StoryParams:
    place: str
    keeper_name: str
    animal_name: str
    serum_kind: str
    seed: Optional[int] = None
    incident: int = 0
    opening: int = 0
    reflection: int = 0


SETTINGS = {
    "zoo": Setting("the zoo", {"serum", "clinic", "animal"}),
}

KEEPER_NAMES = ["Luna", "Mara", "Nia", "Tessa", "Pia", "Ravi"]
ANIMAL_NAMES = ["Pip", "Kito", "Bibi", "Momo", "Tala", "Zuri"]
SERUM_KINDS = ["cooling serum", "brightening serum", "healing serum"]

INCIDENTS = [
    {
        "animal": "a young elephant",
        "sound": "Clang! went the clinic gate, and the elephant gave a tired rumble.",
        "urge": "run straight across the enclosure with the serum",
        "clue": "the keeper's boots were muddy, the path was slick, and the clinic bell was still silent",
        "action": "Luna closed the gate, rang the clinic bell, and waited on the marked path",
        "cause": "the rain had made the shortcut unsafe, but the clinic staff were ready nearby",
        "lesson": "help must be swift, but it must also be safe",
        "ending": "When the elephant felt better, its trunk curled around a clean bell rope.",
    },
    {
        "animal": "a sleepy red panda",
        "sound": "Tap-tap-tap went a bamboo branch against the window.",
        "urge": "open the medicine box and pour the serum without checking its label",
        "clue": "two bottles stood together, but only one carried the animal's name",
        "action": "Luna held both bottles under the lamp and asked the veterinarian to read the label",
        "cause": "the other bottle was a harmless cleaning liquid, not medicine",
        "lesson": "a kind purpose still needs a careful check",
        "ending": "The red panda blinked from its hammock while the labeled bottle rested safely in the clinic.",
    },
    {
        "animal": "a little penguin",
        "sound": "Plip, plip, plip went water beneath the icy door.",
        "urge": "carry the serum through the wet floor alone",
        "clue": "the floor shone like glass and a yellow caution sign leaned beside the door",
        "action": "Luna called for a helper and carried the serum after the floor was dried",
        "cause": "a melting pipe had made a slippery patch",
        "lesson": "asking for help is a brave way to protect a good plan",
        "ending": "The penguin splashed happily while the dry path gleamed beside the pool.",
    },
    {
        "animal": "a gentle tortoise",
        "sound": "Scritch, scritch went a tiny claw behind the supply shelf.",
        "urge": "move the heavy shelf quickly to reach the serum",
        "clue": "a small tortoise hatchling was resting behind it, and the shelf could wobble",
        "action": "Luna stopped, called the keeper, and moved the shelf together",
        "cause": "the shelf had been hiding a little visitor, not blocking an empty space",
        "lesson": "patience protects the quiet creatures we do not expect",
        "ending": "The hatchling found a sunny stone, and the serum reached the waiting tortoise.",
    },
    {
        "animal": "a golden lion cub",
        "sound": "Whoosh! sighed the wind through the tall grass.",
        "urge": "leave the safe walkway and chase the drifting clinic tag",
        "clue": "the tag had blown toward the service gate, where visitors were not allowed",
        "action": "Luna stayed on the walkway and called the keeper with a radio",
        "cause": "the wind had carried the tag, while the serum was already safe in the clinic",
        "lesson": "not every moving thing deserves to be chased",
        "ending": "The lion cub yawned beneath the shade while the tag hung calmly on its hook.",
    },
]

OPENINGS = [
    "At dawn, {keeper} worked in {place}, where every gate had a purpose and every creature had a name.",
    "Before the visitors arrived, {keeper} carried a small case through {place}.",
    "The morning bells of {place} rang softly as {keeper} checked the animal clinic.",
    "In {place}, {keeper} believed that a quiet helper could make a very great difference.",
]

REFLECTIONS = [
    '"I wanted to hurry," {keeper} said, "but my careful thought showed me the safer road."',
    '"The serum mattered," {keeper} whispered, "and so did the way I carried it."',
    '"A pause is not a failure," {keeper} decided. "It can protect the whole plan."',
    '"I listened before I acted," {keeper} said. "That helped me notice what was true."',
]


ASP_RULES = r"""
#show valid/2.
setting(zoo).
affords(zoo,serum).
affords(zoo,clinic).
affords(zoo,animal).
valid(P,A) :- setting(P), affords(P,A).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for place, setting in SETTINGS.items():
        lines.append(asp.fact("setting", place))
        for affordance in sorted(setting.affords):
            lines.append(asp.fact("affords", place, affordance))
    return "\n".join(lines)


def asp_program(show: str = "#show valid/2.") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def python_valid() -> list[tuple[str, str]]:
    return sorted((place, item) for place, setting in SETTINGS.items() for item in setting.affords)


def asp_valid() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program())
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    py = set(python_valid())
    clingo = set(asp_valid())
    if py == clingo:
        print(f"OK: clingo gate matches python gate ({len(py)} combinations).")
        return 0
    print("MISMATCH between clingo and python:")
    print("  only in clingo:", sorted(clingo - py))
    print("  only in python:", sorted(py - clingo))
    return 1


def build_world(params: StoryParams) -> StoryState:
    if params.place not in SETTINGS:
        raise StoryError(f"Unknown place: {params.place}")
    if not params.keeper_name.strip() or not params.animal_name.strip():
        raise StoryError("Keeper and animal names must not be empty.")

    incident = INCIDENTS[params.incident % len(INCIDENTS)]
    world = StoryState(SETTINGS[params.place])
    keeper = world.add(Entity(
        params.keeper_name,
        kind="character",
        type="keeper",
        memes={"care": 1.0, "worry": 0.2},
        meters={"distance_to_clinic": 12.0},
    ))
    animal = world.add(Entity(
        params.animal_name,
        kind="character",
        type="animal",
        label=incident["animal"],
        caretaker=keeper.id,
        memes={"comfort": 0.2},
        meters={"health": 0.45},
    ))
    serum = world.add(Entity(
        "serum",
        type="medicine",
        label=params.serum_kind,
        owner="clinic",
        meters={"distance_to_clinic": 0.0},
        memes={"help": 1.0},
    ))
    clinic = world.add(Entity("clinic", type="place", label="the animal clinic"))

    world.say(OPENINGS[params.opening % len(OPENINGS)].format(
        keeper=keeper.id, place=world.setting.place
    ))
    world.say(f"Inside the clinic waited {params.serum_kind}, meant for {incident['animal']}.")
    world.say(f"{incident['sound']} {keeper.id} heard the animal's weak call.")
    world.say(
        f'"I must {incident["urge"]}," {keeper.id} said. '
        f'But inside, {keeper.id} thought, "A good helper does not let worry choose the fastest path."'
    )

    world.para()
    world.say(f'{keeper.id} paused and noticed that {incident["clue"]}.')
    world.say(f'"Did you hear that?" {keeper.id} asked. "Yes," said a nearby helper. "Let us check before we move."')
    world.say(incident["action"] + ".")
    world.say(REFLECTIONS[params.reflection % len(REFLECTIONS)].format(keeper=keeper.id))
    world.say(f"The careful choice showed that {incident['cause']}.")

    world.para()
    world.say(
        f"The animal received the {params.serum_kind} while {keeper.id} watched calmly. "
        f"Its breathing grew easier, and the worried sounds faded."
    )
    world.say(
        f'"You helped me by listening," the helper told {keeper.id}. '
        f'"And you helped me by speaking up," {keeper.id} replied.'
    )
    world.say(f"{incident['ending']} The zoo grew peaceful again.")
    world.facts.update(
        keeper=keeper,
        animal=animal,
        serum=serum,
        clinic=clinic,
        incident=incident,
        lesson=incident["lesson"],
    )
    return world


def generation_prompts(world: StoryState) -> list[str]:
    f = world.facts
    return [
        f"Write a fable set in a zoo where {f['keeper'].id} carries serum to {f['animal'].label}.",
        "Include an inner monologue and clear sound effects that change the character's decision.",
        "End with a concrete image showing that careful help made the animal and zoo safer.",
    ]


def story_qa(world: StoryState) -> list[QAItem]:
    f = world.facts
    incident = f["incident"]
    keeper = f["keeper"].id
    return [
        QAItem(
            "Who carried the serum?",
            f"{keeper} carried the serum through the zoo and chose a safe way to deliver it.",
        ),
        QAItem(
            "What did the sound effect make the keeper notice?",
            f"The sound helped {keeper} pause and notice that {incident['clue']}.",
        ),
        QAItem(
            "What did the keeper first want to do?",
            f"{keeper} first wanted to {incident['urge']}, but the inner thought about safe helping changed that plan.",
        ),
        QAItem(
            "How did the keeper solve the problem?",
            f"{keeper} {incident['action'].lower()}. This allowed the serum to reach the animal without creating another danger.",
        ),
        QAItem(
            "What is the fable's lesson?",
            f"The lesson is that {incident['lesson']}.",
        ),
    ]


def world_knowledge_qa(world: StoryState) -> list[QAItem]:
    return [
        QAItem(
            "What is a serum?",
            "A serum is a liquid prepared for a medical purpose, such as helping treat or protect a living thing.",
        ),
        QAItem(
            "Why should medicine be checked before it is given?",
            "Medicine should be checked so the right treatment reaches the right patient in a safe way.",
        ),
        QAItem(
            "What does a zoo keeper do?",
            "A zoo keeper cares for animals, watches their needs, and helps keep their spaces safe.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts =="]
    lines.extend(f"{i}. {prompt}" for i, prompt in enumerate(sample.prompts, 1))
    lines.append("")
    lines.append("== (2) Story questions ==")
    for item in sample.story_qa:
        lines.extend([f"Q: {item.question}", f"A: {item.answer}"])
    lines.append("")
    lines.append("== (3) World-knowledge questions ==")
    for item in sample.world_qa:
        lines.extend([f"Q: {item.question}", f"A: {item.answer}"])
    return "\n".join(lines)


def dump_trace(world: StoryState) -> str:
    lines = ["--- world model state ---"]
    for entity in world.entities.values():
        lines.append(
            f"  {entity.id:12} type={entity.type:10} "
            f"meters={entity.meters} memes={entity.memes}"
        )
    lines.append(f"  facts: {world.facts}")
    return "\n".join(lines)


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    place = args.place or "zoo"
    if place not in SETTINGS:
        raise StoryError(f"Unknown place: {place}")
    keeper = args.name or rng.choice(KEEPER_NAMES)
    animal = args.animal or rng.choice(ANIMAL_NAMES)
    if keeper == animal:
        animal = rng.choice([name for name in ANIMAL_NAMES if name != keeper])
    serum_kind = args.serum or rng.choice(SERUM_KINDS)
    return StoryParams(
        place=place,
        keeper_name=keeper,
        animal_name=animal,
        serum_kind=serum_kind,
        incident=rng.randrange(len(INCIDENTS)),
        opening=rng.randrange(len(OPENINGS)),
        reflection=rng.randrange(len(REFLECTIONS)),
    )


def generate(params: StoryParams) -> StorySample:
    world = build_world(params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
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
        description="Fable storyworld about serum, inner monologue, and sound effects at a zoo."
    )
    parser.add_argument("--place", choices=SETTINGS, default=None)
    parser.add_argument("--name", default=None)
    parser.add_argument("--animal", default=None)
    parser.add_argument("--serum", choices=SERUM_KINDS, default=None)
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


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program())
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        values = asp_valid()
        print(f"{len(values)} valid combinations:\n")
        for place, item in values:
            print(f"  {place:8} {item}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        for index, keeper in enumerate(KEEPER_NAMES[:len(SETTINGS)]):
            params = StoryParams(
                place="zoo",
                keeper_name=keeper,
                animal_name=ANIMAL_NAMES[index],
                serum_kind=SERUM_KINDS[index % len(SERUM_KINDS)],
                incident=index % len(INCIDENTS),
                opening=index % len(OPENINGS),
                reflection=index % len(REFLECTIONS),
            )
            samples.append(generate(params))
    else:
        seen: set[str] = set()
        attempt = 0
        while len(samples) < max(0, args.n) and attempt < max(50, args.n * 20):
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

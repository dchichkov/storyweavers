#!/usr/bin/env python3
"""
A small slice-of-life storyworld about twins, a dim hall, a magical ouch,
and the moral value of telling the truth while solving a mystery.
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
    kind: str = "thing"
    label: str = ""
    role: str = ""
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def __post_init__(self) -> None:
        for key in ("light", "ouch", "distance", "clue", "trust", "courage", "wonder"):
            self.meters.setdefault(key, 0.0)
            self.memes.setdefault(key, 0.0)


@dataclass
class Hall:
    label: str = "the upstairs hall"
    dim: bool = True
    magic: str = "the moon-lamp"
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def __post_init__(self) -> None:
        for key in ("brightness", "mystery", "safety"):
            self.meters.setdefault(key, 0.0)
            self.memes.setdefault(key, 0.0)


@dataclass
class World:
    hall: Hall
    entities: dict[str, Entity] = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    facts: dict[str, object] = field(default_factory=dict)
    fired: set[str] = field(default_factory=set)

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
        return "\n\n".join(" ".join(part) for part in self.paragraphs if part)


TWIN_PAIRS = [
    ("Luna", "Milo"),
    ("Nia", "Nico"),
    ("Tessa", "Theo"),
    ("Mara", "Max"),
]
CLUES = [
    "a small silver thread caught on the banister",
    "two muddy dots beneath the umbrella stand",
    "a warm footprint beside the cold radiator",
    "a blue button resting under the hall table",
]
MYSTERIES = [
    "the moon-lamp had gone dim even though its crystal was still warm",
    "a tiny golden key had vanished from the bowl by the stairs",
    "the family photograph had turned to face the wall",
    "a soft bell kept ringing from the closed coat cupboard",
]
MAGIC_EFFECTS = [
    "It glowed brighter whenever someone spoke honestly.",
    "It hummed softly when a clue was placed beside it.",
    "It cast a second shadow whenever a secret was being kept.",
    "It warmed the floor beneath the person who needed courage.",
]


@dataclass
class StoryParams:
    name: str
    twin: str
    clue: str
    mystery: str
    magic_effect: str
    seed: Optional[int] = None
    telling: int = 0


def _pronoun(name: str, case: str = "subject") -> str:
    if name in {"Luna", "Nia", "Tessa", "Mara"}:
        return {"subject": "she", "object": "her", "possessive": "her"}[case]
    return {"subject": "he", "object": "him", "possessive": "his"}[case]


def tell(params: StoryParams) -> World:
    hall = Hall()
    world = World(hall)
    hero = world.add(Entity("hero", "character", params.name, "twin"))
    twin = world.add(Entity("twin", "character", params.twin, "twin"))
    lamp = world.add(Entity("lamp", "thing", "the moon-lamp", "magic"))
    hero.memes["trust"] = 1.0
    twin.memes["trust"] = 1.0
    hall.meters["brightness"] = 0.3
    hall.meters["mystery"] = 1.0

    rng = random.Random(params.seed if params.seed is not None else 0)
    openings = [
        f"{params.name} and {params.twin} shared a room, a homework table, and a habit of walking through the hall together.",
        f"Every evening, the twins {params.name} and {params.twin} crossed the upstairs hall before bedtime.",
        f"The hall was usually the brightest place in the house after sunset, because the twins loved its little moon-lamp.",
    ]
    transitions = [
        "The ordinary evening changed when",
        "That was when the twins noticed that",
        "Just as they reached the stairs,",
    ]
    honest_lines = [
        f'"I bumped the table," {params.name} admitted. "I was hurrying, and I felt an ouch."',
        f'"I saw something move," {params.twin} said. "But I was too scared to say so at first."',
        f'"Let us tell the whole truth," {params.name} replied. "The clue may help us."',
    ]
    action_lines = [
        f"{params.name} placed the clue beside the lamp, while {params.twin} checked the floor with a flashlight.",
        f"The twins followed the clue together, stopping whenever the dim light made the hall feel strange.",
        f"They measured the little marks with a ruler from the homework drawer instead of guessing.",
    ]
    opening = openings[params.telling % len(openings)]
    transition = rng.choice(transitions)
    honest_line = rng.choice(honest_lines)
    action_line = rng.choice(action_lines)

    world.say(opening)
    world.say(
        f"{transition} {params.mystery}. "
        f"The hall became ouch-dim, not dark enough to frighten them, but dim enough to hide a useful detail."
    )
    world.say(f"The moon-lamp whispered, '{params.magic_effect}'")
    world.para()

    world.say(
        f"{params.name} reached toward the lamp and felt a quick ouch in { _pronoun(params.name, 'possessive') } finger."
    )
    hero.meters["ouch"] += 1
    hero.memes["courage"] += 1
    world.say(
        f'"Did you get hurt?" {params.twin} asked. '
        f'"A little," {params.name} said. "The ouch is a clue, not a reason to hide what happened."'
    )
    world.say(
        f"Near the skirting board, they found {params.clue}. "
        "It did not explain everything, but it proved that someone or something had passed through the hall."
    )
    world.say(honest_line)
    hero.memes["trust"] += 1
    twin.memes["trust"] += 1

    world.para()
    world.say(action_line)
    world.say(
        f"The clue led to a loose panel beneath the hall table. Behind it lay the missing object, "
        f"along with a note from the twins' grandmother: 'A mystery grows in the dark, but truth gives it a door.'"
    )
    hall.meters["mystery"] = 0.0
    hall.meters["brightness"] = 1.0
    hall.dim = False
    lamp.meters["light"] = 1.0
    hero.memes["wonder"] += 1
    twin.memes["wonder"] += 1
    world.say(
        f"The moon-lamp brightened until the hall looked gentle again. {params.name} and {params.twin} "
        "understood that their honesty had helped them notice what fear tried to hide."
    )
    world.say(
        f"The moral value was clear: telling the truth, even about a small mistake or a small ouch, "
        "protects trust and makes hard mysteries easier to solve."
    )
    world.say(
        f"At bedtime, the twins left the hall light glowing softly, and the once ouch-dim floor shone "
        "with two matching slippers side by side."
    )

    world.facts.update(
        hero=hero,
        twin=twin,
        lamp=lamp,
        hall=hall,
        clue=params.clue,
        mystery=params.mystery,
        magic_effect=params.magic_effect,
        solved=True,
        moral_value="honesty protects trust and helps people solve problems together",
        ending="two matching slippers side by side in the softly glowing hall",
    )
    return world


def generation_prompts(world: World) -> list[str]:
    hero = world.facts["hero"]
    twin = world.facts["twin"]
    hall = world.facts["hall"]
    return [
        f"Write a slice-of-life story about twins {hero.label} and {twin.label} solving a mystery in {hall.label}.",
        f"Include a magical moon-lamp, an ouch-dim hall, and the clue {world.facts['clue']}.",
        "Show through dialogue why honesty is a moral value and end with a concrete changed image.",
    ]


def story_qa(world: World) -> list[QAItem]:
    hero = world.facts["hero"]
    twin = world.facts["twin"]
    return [
        QAItem(
            "Who are the main characters?",
            f"The main characters are the twins {hero.label} and {twin.label}, who work together in the upstairs hall.",
        ),
        QAItem(
            "What mystery did the twins need to solve?",
            f"They needed to solve the mystery of how {world.facts['mystery'].removeprefix('the ')}.",
        ),
        QAItem(
            "What made the hall ouch-dim?",
            "The hall became ouch-dim when the moon-lamp lost its brightness, leaving enough light to see but enough dimness to hide clues.",
        ),
        QAItem(
            "What clue helped the twins?",
            f"The clue was {world.facts['clue']}. It showed that someone or something had passed through the hall.",
        ),
        QAItem(
            "How did honesty help solve the mystery?",
            f"The twins admitted what they had seen and what had happened, so they could examine the clues together instead of hiding their mistakes.",
        ),
        QAItem(
            "What moral value does the story teach?",
            f"The story teaches that {world.facts['moral_value']}.",
        ),
        QAItem(
            "What final image shows that the problem changed?",
            f"The final image shows {world.facts['ending']}, proving that the hall is bright and peaceful again.",
        ),
    ]


KNOWLEDGE = [
    QAItem("What is magic in a story?", "Magic is an unusual power or event that helps create wonder or change."),
    QAItem("What is a mystery?", "A mystery is a question or problem whose answer must be discovered from clues."),
    QAItem("What is a moral value?", "A moral value is a good principle, such as honesty, kindness, or courage, that guides choices."),
    QAItem("What does dim mean?", "Dim means not very bright."),
    QAItem("What is a twin?", "A twin is one of two children born from the same pregnancy."),
]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return list(KNOWLEDGE)


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts =="]
    lines.extend(f"{i}. {p}" for i, p in enumerate(sample.prompts, 1))
    lines.append("")
    lines.append("== (2) Story questions ==")
    for item in sample.story_qa:
        lines.extend([f"Q: {item.question}", f"A: {item.answer}"])
    lines.append("")
    lines.append("== (3) World knowledge ==")
    for item in sample.world_qa:
        lines.extend([f"Q: {item.question}", f"A: {item.answer}"])
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    lines.append(
        f"  hall: dim={world.hall.dim} meters={world.hall.meters} memes={world.hall.memes}"
    )
    for entity in world.entities.values():
        lines.append(
            f"  {entity.id}: label={entity.label!r} meters={entity.meters} memes={entity.memes}"
        )
    lines.append(f"  solved={world.facts.get('solved')}")
    return "\n".join(lines)


def asp_facts() -> str:
    import asp
    return "\n".join(
        [
            asp.fact("place", "hall"),
            asp.fact("dim", "hall"),
            asp.fact("character", "twin"),
            asp.fact("character", "twin2"),
            asp.fact("magic", "moon_lamp"),
            asp.fact("clue", "silver_thread"),
            asp.fact("honesty", "truth_told"),
            asp.fact("in", "moon_lamp", "hall"),
            asp.fact("found", "silver_thread", "hall"),
        ]
    )


ASP_RULES = r"""
safe_clue(C) :- clue(C), found(C, hall).
mystery_solvable(hall) :- safe_clue(_), magic(moon_lamp).
trust_preserved(twin) :- honesty(truth_told).
valid(hall) :- dim(hall), mystery_solvable(hall), trust_preserved(twin).
#show safe_clue/1.
#show mystery_solvable/1.
#show trust_preserved/1.
#show valid/1.
"""


def asp_program() -> str:
    return asp_facts() + "\n" + ASP_RULES


def asp_verify() -> int:
    try:
        import asp
        model = asp.one_model(asp_program())
    except ImportError:
        print("ASP verification unavailable: clingo is not installed.")
        return 0
    valid = set(asp.atoms(model, "valid"))
    if valid == {("hall",)}:
        print("OK: ASP gate agrees with Python reasonableness.")
        return 0
    print("MISMATCH: ASP and Python disagree.")
    print("ASP atoms:", sorted(valid))
    return 1


def _validate(params: StoryParams) -> None:
    if not params.name or not params.twin:
        raise StoryError("Both twins need names.")
    if params.name == params.twin:
        raise StoryError("The twins need distinct names.")
    if not params.clue:
        raise StoryError("The mystery needs a concrete clue.")
    if not params.mystery:
        raise StoryError("The story needs a mystery to solve.")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Hall, twin, ouch-dim: a magical moral mystery storyworld."
    )
    parser.add_argument("--name", choices=[pair[0] for pair in TWIN_PAIRS])
    parser.add_argument("--twin", choices=[pair[1] for pair in TWIN_PAIRS])
    parser.add_argument("--clue", choices=CLUES)
    parser.add_argument("--mystery", choices=MYSTERIES)
    parser.add_argument("--magic-effect", choices=MAGIC_EFFECTS)
    parser.add_argument("--telling", type=int, choices=range(3))
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
    pair = rng.choice(TWIN_PAIRS)
    name = args.name or pair[0]
    twin = args.twin or pair[1]
    return StoryParams(
        name=name,
        twin=twin,
        clue=args.clue or rng.choice(CLUES),
        mystery=args.mystery or rng.choice(MYSTERIES),
        magic_effect=args.magic_effect or rng.choice(MAGIC_EFFECTS),
        seed=None,
        telling=args.telling if args.telling is not None else rng.randrange(3),
    )


def generate(params: StoryParams) -> StorySample:
    _validate(params)
    world = tell(params)
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


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program())
        return
    if args.verify:
        raise SystemExit(asp_verify())
    if args.asp:
        try:
            import asp
            model = asp.one_model(asp_program())
            print("ASP model:", " ".join(str(atom) for atom in model))
        except ImportError:
            print("ASP mode unavailable: clingo is not installed.")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        for index, pair in enumerate(TWIN_PAIRS):
            params = StoryParams(
                name=pair[0],
                twin=pair[1],
                clue=CLUES[index % len(CLUES)],
                mystery=MYSTERIES[index % len(MYSTERIES)],
                magic_effect=MAGIC_EFFECTS[index % len(MAGIC_EFFECTS)],
                seed=base_seed + index,
                telling=index % 3,
            )
            samples.append(generate(params))
    else:
        for index in range(args.n):
            rng = random.Random(base_seed + index)
            params = resolve_params(args, rng)
            params.seed = base_seed + index
            samples.append(generate(params))

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

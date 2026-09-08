#!/usr/bin/env python3
"""
A tiny whodunit world about a missing friendship cross, a mistaken clue, and
the twist that reveals a helpful friend rather than a thief.
"""

from __future__ import annotations

import argparse
import json
import os
import random
import sys
from dataclasses import dataclass, field
from typing import Optional

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = HERE
while ROOT != os.path.dirname(ROOT) and not os.path.exists(os.path.join(ROOT, "results.py")):
    ROOT = os.path.dirname(ROOT)
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
    location: str = ""
    carrying: Optional[str] = None


@dataclass
class Setting:
    place: str
    rooms: tuple[str, ...]
    clues: set[str]


@dataclass(frozen=True)
class Case:
    id: str
    opening: str
    disappearance: str
    false_clue: str
    question: str
    reveal: str
    twist: str
    ending: str
    object_place: str


@dataclass
class World:
    setting: Setting
    entities: dict[str, Entity] = field(default_factory=dict)
    facts: dict[str, object] = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
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
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)


SETTING = Setting(
    place="the old town library",
    rooms=("the reading room", "the map hall", "the garden door"),
    clues={"cross", "friendship", "misunderstanding", "twist"},
)

CASES = [
    Case(
        "rainy_map_hall",
        "Rain tapped the tall windows of the old town library while Luna and her friends prepared the Friendship Fair.",
        "The silver cross that marked the fair's welcome table had vanished from the map hall.",
        "A trail of blue chalk crossed the floor and pointed toward the garden door, where Theo had been seen.",
        "Did Theo take the cross, or had the chalk been pointing to something else?",
        "Luna followed the chalk to a loose map pin and found a second trail scratched beneath it.",
        "The twist was that Theo had moved the cross to the garden door so rain would not stain it; he had planned a surprise display and told nobody.",
        "The friends apologized, hung the dry cross above the welcome table, and laughed at how quickly a clue had become a misunderstanding.",
        "the garden door",
    ),
    Case(
        "quiet_reading_room",
        "Luna was arranging storybooks when the library bell rang for the Friendship Fair.",
        "The little wooden cross belonging to the fair's friendship game was missing from the reading room.",
        "Mara's red ribbon lay beside the empty cushion, and Mara had left in a hurry.",
        "Was the ribbon proof of guilt, or was it only a sign that Mara had been nearby?",
        "Luna noticed a thread of red ribbon caught on the window latch and traced it to a basket of folded banners.",
        "The twist was that Mara had carried the cross with the banners to make a secret friendship sign, but a gust had blown the basket shut.",
        "Mara freed the cross, and the friends made the sign together before the first visitors arrived.",
        "the reading room",
    ),
    Case(
        "garden_door_case",
        "At sunset, Luna and Pip set lanterns around the library garden door for a celebration of friendship.",
        "The brass cross used to open the fair's clue box disappeared between two songs.",
        "A muddy pawprint led toward Pip's satchel, and Pip had been the last friend near the box.",
        "Could a muddy print tell the whole story?",
        "Luna compared the print with the wet garden path and saw that it pointed away from the satchel.",
        "The twist was that a friendly garden dog had nudged the cross under the satchel while chasing a moth; Pip had only tried to cover it so nobody would trip.",
        "The friends thanked Pip, rescued the cross from beneath the satchel, and gave the dog the first lantern to carry.",
        "the garden door",
    ),
    Case(
        "map_pin_mystery",
        "The library map hall glowed with candlelight as Luna prepared a friendship treasure hunt.",
        "The painted cross that marked the final treasure had disappeared from the map.",
        "A torn note said, 'I needed it,' and the handwriting looked like Nia's.",
        "Had Nia taken the cross because she wanted the treasure alone?",
        "Luna held the note beside the candle and saw that its missing words had been folded under the map.",
        "The twist was that Nia had written, 'I needed it safe,' then hidden the cross from a leaking roof; the fold made the message sound selfish.",
        "Nia unfolded the note, and the friends repaired the map together before sharing the treasure.",
        "the map hall",
    ),
]


NAMES = ["Luna", "Mina", "Pip", "Theo", "Mara", "Nia"]
ANIMALS = ["rabbit", "otter", "fox", "mouse", "badger", "sparrow"]
TRAITS = ["curious", "patient", "brave", "thoughtful", "lively", "careful"]

DIALOGUES = [
    ('"A clue is not a verdict," said {friend}.', '"Then let us ask what it means," Luna replied.'),
    ('"We should listen before we accuse anyone," said {friend}.', '"Friendship deserves a fair question," said Luna.'),
    ('"The cross must have left a story behind," whispered {friend}.', '"We will follow the story, not our worry," Luna answered.'),
    ('"Something does not fit," said {friend}.', '"That may be the twist," Luna replied.'),
]


@dataclass
class StoryParams:
    name: str
    animal: str
    trait: str
    friend_name: str
    friend_animal: str
    case: str
    seed: Optional[int] = None


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Whodunit story about a cross, friendship, and a misunderstanding."
    )
    parser.add_argument("--name", choices=NAMES)
    parser.add_argument("--animal", choices=ANIMALS)
    parser.add_argument("--trait", choices=TRAITS)
    parser.add_argument("--friend-name", choices=NAMES)
    parser.add_argument("--friend-animal", choices=ANIMALS)
    parser.add_argument("--case", choices=[c.id for c in CASES])
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
    name = args.name or "Luna"
    friend_choices = [n for n in NAMES if n != name]
    friend_name = args.friend_name or rng.choice(friend_choices)
    animal = args.animal or rng.choice(ANIMALS)
    friend_animal = args.friend_animal or rng.choice([a for a in ANIMALS if a != animal])
    return StoryParams(
        name=name,
        animal=animal,
        trait=args.trait or rng.choice(TRAITS),
        friend_name=friend_name,
        friend_animal=friend_animal,
        case=args.case or rng.choice([c.id for c in CASES]),
    )


def tell(params: StoryParams) -> World:
    case = next(c for c in CASES if c.id == params.case)
    world = World(SETTING)
    hero = world.add(Entity(
        id=params.name,
        kind="character",
        type=params.animal,
        label=f"{params.trait} {params.animal}",
        location="the map hall",
        meters={"attention": 0.0, "questions": 0.0},
        memes={"worry": 1.0, "trust": 0.0},
    ))
    friend = world.add(Entity(
        id=params.friend_name,
        kind="character",
        type=params.friend_animal,
        label=f"friend {params.friend_animal}",
        location="the reading room",
        meters={"help": 0.0},
        memes={"patience": 1.0, "trust": 1.0},
    ))
    cross = world.add(Entity(
        id="cross",
        kind="object",
        type="cross",
        label="the friendship cross",
        location=case.object_place,
        meters={"importance": 1.0},
        memes={"meaning": 1.0},
    ))
    world.facts.update(hero=hero, friend=friend, cross=cross, case=case, params=params)

    world.say(case.opening)
    world.say(
        f"{params.name}, a {params.trait} {params.animal}, and {params.friend_name}, "
        f"a loyal {params.friend_animal}, were keeping watch over the friendship cross."
    )
    world.say(case.disappearance)
    world.para()

    dialogue = DIALOGUES[(params.seed or 0) % len(DIALOGUES)]
    world.say(f"{params.name} noticed the first clue. {case.false_clue}")
    world.say(dialogue[0].format(friend=params.friend_name))
    world.say(dialogue[1].format(friend=params.friend_name))
    world.facts["question"] = case.question
    world.facts["clue"] = case.false_clue
    hero.meters["attention"] += 1
    hero.meters["questions"] += 1
    friend.meters["help"] += 1
    world.say(f"{params.name} asked, \"{case.question}\"")
    world.say(
        f"Instead of blaming {params.friend_name}, the friends checked the room, the floor, "
        "and the places where a careful helper might have carried the cross."
    )
    world.say(case.reveal)
    world.say(case.twist)
    world.fired.add("misunderstanding_cleared")
    hero.memes["worry"] = 0.0
    hero.memes["trust"] += 1
    friend.memes["trust"] += 1
    cross.location = case.object_place
    world.para()
    world.say(case.ending)
    world.say(
        f"The friendship cross shone above the table, and {params.name} remembered that "
        "a good whodunit needs curiosity, kindness, and room for one more clue."
    )
    return world


def generation_prompts(world: World) -> list[str]:
    case: Case = world.facts["case"]  # type: ignore[assignment]
    hero: Entity = world.facts["hero"]  # type: ignore[assignment]
    friend: Entity = world.facts["friend"]  # type: ignore[assignment]
    return [
        f"Write a child-friendly Whodunit about {hero.id}, {friend.id}, and a missing cross.",
        f"Show how friendship helps {hero.id} solve this misunderstanding: {case.question}",
        f"End with a twist that explains the clue and proves the cross is safe.",
    ]


def story_qa(world: World) -> list[QAItem]:
    case: Case = world.facts["case"]  # type: ignore[assignment]
    hero: Entity = world.facts["hero"]  # type: ignore[assignment]
    friend: Entity = world.facts["friend"]  # type: ignore[assignment]
    return [
        QAItem(
            f"Where did {hero.id} and {friend.id} find the mystery?",
            "They found the mystery in the old town library during preparations for the Friendship Fair.",
        ),
        QAItem(
            "What disappeared?",
            "The friendship cross disappeared from the fair's display.",
        ),
        QAItem(
            "What misleading clue caused the misunderstanding?",
            case.false_clue,
        ),
        QAItem(
            f"What did {hero.id} and {friend.id} do instead of blaming someone?",
            f"{hero.id} and {friend.id} asked questions and checked the clues carefully before deciding what had happened.",
        ),
        QAItem(
            "What was the twist?",
            case.twist,
        ),
        QAItem(
            "How did the story end?",
            case.ending,
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            "What is a cross?",
            "A cross is a shape made by two lines that meet, and it can also be a meaningful sign or object.",
        ),
        QAItem(
            "What is a whodunit?",
            "A whodunit is a mystery story in which characters investigate clues to discover who caused an event.",
        ),
        QAItem(
            "What is a misunderstanding?",
            "A misunderstanding happens when someone interprets words or clues incorrectly.",
        ),
        QAItem(
            "Why is friendship useful during a mystery?",
            "Friendship is useful because trusted friends can share observations, ask gentle questions, and correct mistakes together.",
        ),
        QAItem(
            "What is a twist?",
            "A twist is a surprising change in what the reader thought was happening.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts =="]
    lines.extend(f"{i}. {p}" for i, p in enumerate(sample.prompts, 1))
    lines.append("")
    lines.append("== (2) Story questions ==")
    for item in sample.story_qa:
        lines.extend([f"Q: {item.question}", f"A: {item.answer}"])
    lines.append("")
    lines.append("== (3) World-knowledge questions ==")
    for item in sample.world_qa:
        lines.extend([f"Q: {item.question}", f"A: {item.answer}"])
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for entity in world.entities.values():
        lines.append(
            f"  {entity.id:8} type={entity.type:10} location={entity.location!r} "
            f"meters={entity.meters} memes={entity.memes}"
        )
    lines.append(f"  fired rules: {sorted(world.fired)}")
    return "\n".join(lines)


def valid_story(params: StoryParams) -> bool:
    return (
        params.name in NAMES
        and params.friend_name in NAMES
        and params.name != params.friend_name
        and params.animal in ANIMALS
        and params.friend_animal in ANIMALS
        and params.animal != params.friend_animal
        and params.trait in TRAITS
        and params.case in {c.id for c in CASES}
    )


def generate(params: StoryParams) -> StorySample:
    if not valid_story(params):
        raise StoryError("The names, animals, trait, or case do not fit this friendship whodunit.")
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


ASP_RULES = r"""
valid_case(C) :- case(C), has_cross(C), has_friendship(C), has_misunderstanding(C), has_twist(C).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for name in NAMES:
        lines.append(asp.fact("name", name))
    for animal in ANIMALS:
        lines.append(asp.fact("animal", animal))
    for trait in TRAITS:
        lines.append(asp.fact("trait", trait))
    for case in CASES:
        lines.extend([
            asp.fact("case", case.id),
            asp.fact("has_cross", case.id),
            asp.fact("has_friendship", case.id),
            asp.fact("has_misunderstanding", case.id),
            asp.fact("has_twist", case.id),
        ])
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show valid_case/1."))
    actual = set(asp.atoms(model, "valid_case"))
    expected = {(case.id,) for case in CASES}
    if actual == expected:
        print(f"OK: clingo gate matches python gate ({len(expected)} cases).")
        for case in CASES:
            params = StoryParams("Luna", "rabbit", "curious", "Pip", "otter", case.id, 1)
            generate(params)
        print("OK: generated stories exercised.")
        return 0
    print("MISMATCH between clingo and python.")
    print("only in clingo:", sorted(actual - expected))
    print("only in python:", sorted(expected - actual))
    return 1


CURATED = [
    StoryParams("Luna", "rabbit", "curious", "Pip", "otter", "rainy_map_hall", 0),
    StoryParams("Mina", "fox", "patient", "Theo", "mouse", "quiet_reading_room", 1),
    StoryParams("Luna", "sparrow", "careful", "Nia", "badger", "map_pin_mystery", 2),
]


def build_story_from_args(args: argparse.Namespace) -> list[StorySample]:
    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    seen: set[str] = set()
    index = 0
    while len(samples) < args.n and index < max(50, args.n * 50):
        rng = random.Random(base_seed + index)
        params = resolve_params(args, rng)
        params.seed = base_seed + index
        index += 1
        sample = generate(params)
        if sample.story in seen:
            continue
        seen.add(sample.story)
        samples.append(sample)
    return samples


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show valid_case/1."))
        return
    if args.verify:
        raise SystemExit(asp_verify())
    if args.asp:
        import asp
        model = asp.one_model(asp_program("#show valid_case/1."))
        cases = sorted(set(asp.atoms(model, "valid_case")))
        print(f"{len(cases)} valid whodunit cases.")
        for case in cases:
            print(case[0])
        return

    samples = [generate(params) for params in CURATED] if args.all else build_story_from_args(args)
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

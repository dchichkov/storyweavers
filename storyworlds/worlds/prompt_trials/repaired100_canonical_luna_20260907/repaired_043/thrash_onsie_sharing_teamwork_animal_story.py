#!/usr/bin/env python3
"""
A standalone Animal Story world about sharing, teamwork, and a rough little
thrash that helps Onsie learn how to work with friends.
"""

from __future__ import annotations

import argparse
import json
import os
import random
import sys
from dataclasses import dataclass, field
from typing import Optional

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, "storyworlds"))
from results import QAItem, StoryError, StorySample  # noqa: E402


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    owner: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.meters:
            self.meters = {"energy": 0.0, "burden": 0.0, "stability": 1.0}
        if not self.memes:
            self.memes = {"joy": 0.0, "worry": 0.0, "trust": 0.0}


@dataclass
class Setting:
    place: str
    affordances: set[str]


@dataclass
class StoryParams:
    place: str
    hero_type: str
    friend_type: str
    name: str
    friend_name: str
    seed: Optional[int] = None


@dataclass(frozen=True)
class Incident:
    title: str
    task: str
    load: str
    problem: str
    clue: str
    lesson: str
    ending: str


SETTINGS = {
    "meadow": Setting("the meadow", {"share", "carry"}),
    "orchard": Setting("the orchard", {"share", "carry"}),
    "pond": Setting("the pond", {"share", "carry"}),
    "woodland_path": Setting("the woodland path", {"share", "carry"}),
}

ANIMAL_TYPES = ["rabbit", "fox", "bear", "squirrel", "otter"]
CHARACTER_NAMES = {
    "rabbit": ["Luna", "Pip", "Nina"],
    "fox": ["Onsie", "Finn", "Tara"],
    "bear": ["Benny", "Mara", "Tess"],
    "squirrel": ["Suki", "Jax", "Milo"],
    "otter": ["Ollie", "Rin", "Mina"],
}

INCIDENTS = [
    Incident(
        "the berry basket trip",
        "carry ripe berries to the picnic",
        "a wide basket filled with berries",
        "Onsie tried to drag the whole basket alone, and it began to thrash from side to side",
        "berries rolled toward a muddy rut whenever one pair of paws pulled harder",
        "A shared load is lighter when everyone takes a fair part",
        "the friends reached the picnic with every berry safe in a basket held steady by many paws",
    ),
    Incident(
        "the shelter-building day",
        "bring soft leaves to a small woodland shelter",
        "a bundle of broad leaves tied with grass",
        "the leaf bundle started to thrash in the wind while Onsie tugged from the wrong side",
        "the grass knot stayed firm, but the bundle leaned toward the strongest gust",
        "Teamwork means listening before pulling",
        "the finished shelter stood quietly while the animals shared its shade",
    ),
    Incident(
        "the pond picnic",
        "carry lunch across the sunny bank",
        "a tray of apples, reeds, and little cakes",
        "the tray began to thrash when Onsie hurried around a slippery stone",
        "the food stayed safe only when two animals held the handles and another watched the path",
        "Sharing jobs helps friends move carefully",
        "the animals spread the food on a clean cloth and saved the last cake for one another",
    ),
    Incident(
        "the lantern walk",
        "place warm lanterns along the evening path",
        "a box of small lanterns",
        "the box gave a noisy thrash when Onsie lifted it with one paw",
        "the lanterns were not broken; they simply needed two steady holders",
        "Careful teamwork can turn a noisy problem into a calm plan",
        "the path glowed with lanterns that every friend had helped place",
    ),
]

OPENINGS = [
    "{hero} the {hero_type} met {friend} the {friend_type} at {place} before the sun was high.",
    "At {place}, {hero} the {hero_type} and {friend} the {friend_type} made a plan for a helpful day.",
    "A bright morning found {hero} and {friend} beside {place}, ready to help their animal neighbors.",
    "Near {place}, {hero} the {hero_type} noticed {friend} the {friend_type} preparing for an important job.",
]

REACTIONS = [
    "Onsie's ears drooped, but {hero} did not laugh.",
    "The sudden movement made everyone step back and take a breath.",
    "{hero} placed both paws on the ground and looked for a safer way.",
    "The friends stopped before the load could roll into trouble.",
]

DIALOGUES = [
    '"I can do it faster alone," Onsie said. "Maybe, but we can do it more safely together," {hero} replied.',
    '"Why is it thrashing?" asked Onsie. "{load} is uneven in your paws," said {hero}. "Let us share it."',
    '"You take one side, and I will take the other," said {hero}. Onsie nodded. "Then we will walk at the same pace."',
    '"I thought asking for help meant I was weak," Onsie admitted. "{hero} smiled. "Sharing the work makes every friend stronger."',
]

REFLECTIONS = [
    "They checked the ground before taking another step.",
    "Each animal named the job they could do best.",
    "They counted together so nobody carried too much.",
    "When one friend slowed down, the others slowed down too.",
]


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict[str, object] = {}
        self.fired: set[str] = set()

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


def _stable_seed(*parts: str) -> int:
    return sum((i + 1) * ord(c) for i, c in enumerate("|".join(parts)))


def apply_thrash(load: Entity) -> None:
    load.meters["energy"] += 1.0
    load.meters["stability"] = 0.0
    load.meters["burden"] += 1.0


def share_load(world: World, load: Entity, hero: Entity, friend: Entity) -> None:
    if "shared" in world.fired:
        return
    world.fired.add("shared")
    load.meters["stability"] = 1.0
    load.meters["burden"] = 0.0
    hero.memes["trust"] += 1.0
    friend.memes["trust"] += 1.0
    hero.memes["joy"] += 1.0
    friend.memes["joy"] += 1.0


def reasonable(world: World) -> bool:
    return (
        "share" in world.setting.affordances
        and "carry" in world.setting.affordances
        and "load" in world.entities
        and "hero" in world.entities
        and "friend" in world.entities
    )


def tell(params: StoryParams) -> World:
    setting = SETTINGS[params.place]
    world = World(setting)
    rng = random.Random(
        params.seed
        if params.seed is not None
        else _stable_seed(params.place, params.hero_type, params.friend_type, params.name, params.friend_name)
    )
    incident = rng.choice(INCIDENTS)

    hero = world.add(Entity(params.name, "character", params.hero_type))
    friend = world.add(Entity(params.friend_name, "character", params.friend_type))
    load = world.add(Entity("load", "thing", "shared_load", incident.load))

    hero.memes["joy"] = 1.0
    friend.memes["joy"] = 1.0
    friend.memes["worry"] = 1.0
    apply_thrash(load)

    if not reasonable(world):
        raise StoryError("The setting must provide a shared load and a safe place for teamwork.")

    values = {
        "hero": hero.id,
        "friend": friend.id,
        "hero_type": hero.type,
        "friend_type": friend.type,
        "place": setting.place,
        "load": incident.load,
    }
    opening = rng.choice(OPENINGS).format(**values)
    reaction = rng.choice(REACTIONS).format(**values)
    dialogue = rng.choice(DIALOGUES).format(**values)
    reflection = rng.choice(REFLECTIONS).format(**values)

    world.say(f"{opening} They were ready to {incident.task}.")
    world.say(f"{incident.problem}. {reaction}")
    world.para()
    world.say(f"They watched closely. {incident.clue}.")
    world.say(dialogue)
    world.para()

    share_load(world, load, hero, friend)
    world.say(f"Together, they changed the plan. {reflection} They carried the load in small, even steps.")
    world.say(f"Onsie smiled because nobody had been left to struggle alone. {incident.lesson}.")
    world.para()
    world.say(f"As the day ended, {incident.ending}.")
    world.facts = {
        "hero": hero,
        "friend": friend,
        "load": load,
        "incident": incident,
        "setting": setting,
        "shared": load.meters["stability"] == 1.0,
        "thrash_stopped": load.meters["stability"] == 1.0,
    }
    return world


def generation_prompts(world: World) -> list[str]:
    incident: Incident = world.facts["incident"]  # type: ignore[assignment]
    hero: Entity = world.facts["hero"]  # type: ignore[assignment]
    friend: Entity = world.facts["friend"]  # type: ignore[assignment]
    return [
        f"Write an Animal Story about {hero.id} and {friend.id} learning sharing and teamwork during {incident.title}.",
        f"Tell a gentle story in which Onsie sees a load thrash, listens to a friend, and changes the plan.",
        f"Write a child-friendly story showing why {incident.lesson.lower()}.",
    ]


def story_qa(world: World) -> list[QAItem]:
    hero: Entity = world.facts["hero"]  # type: ignore[assignment]
    friend: Entity = world.facts["friend"]  # type: ignore[assignment]
    incident: Incident = world.facts["incident"]  # type: ignore[assignment]
    setting: Setting = world.facts["setting"]  # type: ignore[assignment]
    return [
        QAItem(
            f"What were {hero.id} and {friend.id} doing?",
            f"They were at {setting.place} preparing to {incident.task}.",
        ),
        QAItem(
            "What went wrong with the load?",
            f"{incident.problem}. The load moved wildly because one animal was trying to manage too much alone.",
        ),
        QAItem(
            "What clue helped the friends make a better plan?",
            f"They noticed that {incident.clue}. This showed them that the load needed steady helpers.",
        ),
        QAItem(
            f"How did {hero.id} and Onsie solve the problem?",
            f"They shared the load, took opposite sides, and walked at the same pace instead of pulling alone.",
        ),
        QAItem(
            "What did Onsie learn?",
            f"Onsie learned that {incident.lesson}. Asking for help made the work safer and kinder.",
        ),
        QAItem(
            "What final image showed that the plan worked?",
            f"The story ended with this image: {incident.ending}.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            "What does sharing mean?",
            "Sharing means giving others a fair chance to use, enjoy, or help with something.",
        ),
        QAItem(
            "What is teamwork?",
            "Teamwork is when people or animals cooperate, listen, and combine their efforts to reach a goal.",
        ),
        QAItem(
            "Why can a load thrash when one animal carries it?",
            "A load can thrash when it is uneven or moving faster than the carrier can control.",
        ),
        QAItem(
            "How can friends carry something safely?",
            "Friends can share the weight, communicate, move at the same pace, and stop when the load becomes unstable.",
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


ASP_RULES = r"""
animal(rabbit).
animal(fox).
animal(bear).
animal(squirrel).
animal(otter).

setting(meadow).
setting(orchard).
setting(pond).
setting(woodland_path).

supports_sharing(meadow).
supports_sharing(orchard).
supports_sharing(pond).
supports_sharing(woodland_path).

supports_carrying(meadow).
supports_carrying(orchard).
supports_carrying(pond).
supports_carrying(woodland_path).

valid_story(Place, Hero, Friend) :-
    setting(Place),
    animal(Hero),
    animal(Friend),
    supports_sharing(Place),
    supports_carrying(Place).
"""


def asp_facts() -> str:
    import asp

    lines = []
    for place in SETTINGS:
        lines.append(asp.fact("setting", place))
        lines.append(asp.fact("supports_sharing", place))
        lines.append(asp.fact("supports_carrying", place))
    for animal in ANIMAL_TYPES:
        lines.append(asp.fact("animal", animal))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_stories() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("#show valid_story/3."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    expected = {
        (place, hero, friend)
        for place in SETTINGS
        for hero in ANIMAL_TYPES
        for friend in ANIMAL_TYPES
    }
    actual = set(asp_valid_stories())
    if actual == expected:
        print(f"OK: ASP gate matches Python expectations ({len(actual)} combinations).")
        return 0
    print("MISMATCH between ASP and Python expectations:")
    print("only in ASP:", sorted(actual - expected))
    print("only in Python:", sorted(expected - actual))
    return 1


CURATED = [
    StoryParams("meadow", "rabbit", "fox", "Luna", "Onsie"),
    StoryParams("orchard", "bear", "squirrel", "Benny", "Onsie"),
    StoryParams("pond", "otter", "rabbit", "Ollie", "Onsie"),
]


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Animal Story world about sharing, teamwork, thrash, and Onsie.")
    parser.add_argument("--place", choices=SETTINGS)
    parser.add_argument("--hero-type", choices=ANIMAL_TYPES)
    parser.add_argument("--friend-type", choices=ANIMAL_TYPES)
    parser.add_argument("--name")
    parser.add_argument("--friend-name")
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


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    hero_type = args.hero_type or rng.choice(ANIMAL_TYPES)
    friend_type = args.friend_type or "fox"
    name = args.name or rng.choice(CHARACTER_NAMES[hero_type])
    friend_name = args.friend_name or "Onsie"
    if name == friend_name:
        choices = [n for n in CHARACTER_NAMES[hero_type] if n != friend_name]
        name = rng.choice(choices)
    return StoryParams(
        place=args.place or rng.choice(list(SETTINGS)),
        hero_type=hero_type,
        friend_type=friend_type,
        name=name,
        friend_name=friend_name,
    )


def generate(params: StoryParams) -> StorySample:
    world = tell(params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for entity in world.entities.values():
        meters = {k: v for k, v in entity.meters.items() if v}
        memes = {k: v for k, v in entity.memes.items() if v}
        lines.append(
            f"  {entity.id:8} ({entity.type:12}) meters={meters} memes={memes}"
        )
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


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid_story/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        rows = asp_valid_stories()
        print(f"{len(rows)} compatible story triples:")
        for row in rows:
            print(" ", row)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        attempt = 0
        while len(samples) < args.n and attempt < max(50, args.n * 50):
            seed = base_seed + attempt
            attempt += 1
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
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.name}: {p.place} ({p.hero_type} + {p.friend_type})"
        elif len(samples) > 1:
            header = f"### variant {index + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if index < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()

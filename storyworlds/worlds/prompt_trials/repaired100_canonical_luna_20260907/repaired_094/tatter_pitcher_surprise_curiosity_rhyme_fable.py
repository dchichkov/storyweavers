#!/usr/bin/env python3
"""
A tiny fable world about a tattered pitcher, a curious fox, and a surprising rhyme.
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
import random
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from results import QAItem, StoryError, StorySample  # noqa: E402


@dataclass
class Entity:
    id: str
    kind: str
    label: str
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)


@dataclass
class Setting:
    place: str
    affordances: set[str] = field(default_factory=set)


@dataclass
class World:
    setting: Setting
    entities: dict[str, Entity] = field(default_factory=dict)
    facts: dict[str, object] = field(default_factory=dict)

    def add(self, entity: Entity) -> Entity:
        self.entities[entity.id] = entity
        return entity


TALES = [
    {
        "place": "the hill garden",
        "water": "the thirsty beans",
        "repair": "a strip of blue cloth",
        "rhyme": "A tatter can flatter when kindness is fatter",
        "surprise": "the pitcher poured one last bright stream through its tear",
        "ending": "the beans lifted their green leaves before sunset",
    },
    {
        "place": "the village well",
        "water": "the baker's cooling herbs",
        "repair": "a soft golden thread",
        "rhyme": "A cracked little pitcher can still be a giver",
        "surprise": "the pitcher chimed like a tiny bell when the moon touched its rim",
        "ending": "the herbs smelled fresh enough to make the whole lane smile",
    },
    {
        "place": "the orchard wall",
        "water": "the smallest apple tree",
        "repair": "a red ribbon from a basket",
        "rhyme": "A tatter may scatter, yet care makes it matter",
        "surprise": "the pitcher left a silver trail that led to a hidden spring",
        "ending": "the young tree opened three pale blossoms",
    },
    {
        "place": "the fox's woodland doorstep",
        "water": "a row of drooping clover",
        "repair": "a woven reed band",
        "rhyme": "A pitcher with a tatter can still bring laughter",
        "surprise": "the pitcher reflected a star in its muddy side",
        "ending": "the clover stood up and welcomed the evening bees",
    },
]


def make_world(params: "StoryParams") -> World:
    if params.tale_index < 0 or params.tale_index >= len(TALES):
        raise StoryError("tale_index must select a known fable")
    if params.hero_kind not in {"fox", "hare", "mouse"}:
        raise StoryError("hero_kind must be fox, hare, or mouse")

    tale = TALES[params.tale_index]
    world = World(Setting(tale["place"], {"carry", "inspect", "repair", "share"}))
    hero = world.add(Entity(
        "hero", "animal", params.hero_name,
        meters={"steps": 0.0},
        memes={"curiosity": 1.0, "worry": 0.0, "kindness": 0.0},
    ))
    pitcher = world.add(Entity(
        "pitcher", "object", "the tattered pitcher",
        meters={"water": 1.0, "leak": 1.0},
        memes={"usefulness": 0.4, "shame": 0.0},
    ))
    friend = world.add(Entity(
        "friend", "animal", params.friend_name,
        meters={"patience": 1.0},
        memes={"wisdom": 1.0},
    ))
    world.facts.update(
        tale=tale,
        hero=hero,
        pitcher=pitcher,
        friend=friend,
        noticed_tatter=False,
        curiosity_tested=False,
        rhyme_found=False,
        pitcher_repaired=False,
        surprise_revealed=False,
        garden_helped=False,
    )
    return world


def tell(params: "StoryParams") -> World:
    world = make_world(params)
    f = world.facts
    tale = f["tale"]
    hero: Entity = f["hero"]
    pitcher: Entity = f["pitcher"]
    friend: Entity = f["friend"]

    hero.meters["steps"] += 1
    world.facts["noticed_tatter"] = True
    pitcher.memes["shame"] += 1.0

    intro = [
        f"In {world.setting.place}, {hero.label} found {pitcher.label} beside a stone.",
        f"One warm morning, {hero.label} carried {pitcher.label} through {world.setting.place}.",
        f"At the edge of {world.setting.place}, a tatter fluttered on an old pitcher.",
    ][params.route % 3]
    world.facts["opening"] = intro
    world.facts["tension"] = f"The pitcher leaked while carrying water for {tale['water']}."
    world.facts["method"] = f"{hero.label} followed curiosity instead of throwing the pitcher away."

    world.facts["curiosity_tested"] = True
    hero.memes["curiosity"] += 1.0
    hero.memes["kindness"] += 1.0
    hero.meters["steps"] += 2
    world.facts["rhyme_found"] = True

    world.facts["dialogue"] = (
        f'"This tatter makes the pitcher useless," said {hero.label}. '
        f'"Is it useless, or only asking for help?" asked {friend.label}. '
        f'{hero.label} looked closer. "Let us test it before we judge it."'
    )

    pitcher.meters["leak"] = 0.0
    pitcher.meters["water"] = 1.0
    pitcher.memes["usefulness"] += 0.8
    pitcher.memes["shame"] = 0.0
    world.facts["pitcher_repaired"] = True
    world.facts["garden_helped"] = True
    world.facts["surprise_revealed"] = True
    return world


def render(world: World) -> str:
    f = world.facts
    tale = f["tale"]
    hero: Entity = f["hero"]
    friend: Entity = f["friend"]
    return "\n\n".join([
        f"{f['opening']} {hero.label} saw that its side had a tatter, and {tale['water']} were dry.",
        f"{f['tension']} {f['dialogue']}",
        f"Curiosity led {hero.label} to wrap the tear with {tale['repair']}. Then came a little rhyme: “{tale['rhyme']}” {friend.label} smiled, but {hero.label} kept watching the old pitcher.",
        f"To everyone's surprise, {tale['surprise']}. The tattered pitcher had not been perfect, yet it had carried enough water to help.",
        f"{tale['ending']}. {hero.label} learned that a thing with a flaw may still have a gift to share, if a curious heart takes time to find it.",
    ])


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    tale = f["tale"]
    return [
        f"Write a child-friendly fable at {world.setting.place} about a tattered pitcher helping {tale['water']}.",
        f"Use Surprise, Curiosity, and Rhyme to show how {f['hero'].label} discovers the pitcher's hidden value.",
        f"Include this moral idea: a flaw does not erase a useful gift.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    tale = f["tale"]
    hero: Entity = f["hero"]
    return [
        QAItem(
            f"Why did {hero.label} inspect the tattered pitcher?",
            f"{hero.label} inspected it because it was leaking while {tale['water']} needed water. Curiosity made {hero.label} test the pitcher instead of discarding it.",
        ),
        QAItem(
            "What surprising thing happened?",
            f"The surprise was that {tale['surprise']}. The pitcher still helped after its tear was repaired.",
        ),
        QAItem(
            "What lesson did the fable teach?",
            "The fable taught that a flaw does not erase a useful gift. Patient kindness can reveal what something is still able to do.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem("What is a pitcher?", "A pitcher is a container used for holding and pouring liquid."),
        QAItem("What is a tatter?", "A tatter is a small torn or ragged piece of cloth or material."),
        QAItem("What is curiosity?", "Curiosity is the wish to learn more by asking questions and looking closely."),
        QAItem("What is a fable?", "A fable is a short story, often with animals, that teaches a lesson."),
    ]


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for entity in world.entities.values():
        lines.append(
            f"  {entity.id:8} ({entity.kind:7}) "
            f"meters={entity.meters} memes={entity.memes}"
        )
    lines.append(f"  facts={world.facts}")
    return "\n".join(lines)


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts =="]
    lines.extend(f"{i}. {p}" for i, p in enumerate(sample.prompts, 1))
    lines.append("")
    lines.append("== (2) Story questions ==")
    for item in sample.story_qa:
        lines.extend([f"Q: {item.question}", f"A: {item.answer}"])
    lines.append("")
    lines.append("== (3) World knowledge questions ==")
    for item in sample.world_qa:
        lines.extend([f"Q: {item.question}", f"A: {item.answer}"])
    return "\n".join(lines)


@dataclass
class StoryParams:
    hero_name: str
    hero_kind: str
    friend_name: str
    tale_index: int = 0
    route: int = 0
    seed: Optional[int] = None


HERO_NAMES = {
    "fox": ["Fenn", "Ruby", "Pip"],
    "hare": ["Hazel", "Tobin", "Lark"],
    "mouse": ["Milo", "Mina", "Pip"],
}
FRIENDS = ["Old Badger", "Aunt Wren", "Grandmother Mole", "Wise Tortoise"]


ASP_RULES = r"""
repaired :- noticed_tatter, curiosity_tested, pitcher_repaired.
helped :- repaired, garden_helped.
surprise :- helped, surprise_revealed.
good_ending :- surprise, rhyme_found.
"""


def asp_facts(world: Optional[World] = None) -> str:
    import asp
    if world is None:
        facts = ["noticed_tatter", "curiosity_tested", "pitcher_repaired",
                 "garden_helped", "surprise_revealed", "rhyme_found"]
    else:
        f = world.facts
        facts = [
            name for name in (
                "noticed_tatter", "curiosity_tested", "pitcher_repaired",
                "garden_helped", "surprise_revealed", "rhyme_found"
            ) if f.get(name)
        ]
    return "\n".join(asp.fact(name) for name in facts)


def asp_program(show: str = "#show good_ending/0.") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="A fable about a tattered pitcher.")
    parser.add_argument("--name")
    parser.add_argument("--kind", choices=["fox", "hare", "mouse"])
    parser.add_argument("--friend")
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
    kind = args.kind or rng.choice(list(HERO_NAMES))
    name = args.name or rng.choice(HERO_NAMES[kind])
    friend = args.friend or rng.choice(FRIENDS)
    return StoryParams(
        hero_name=name,
        hero_kind=kind,
        friend_name=friend,
        tale_index=rng.randrange(len(TALES)),
        route=rng.randrange(3),
    )


def generate(params: StoryParams) -> StorySample:
    world = tell(params)
    return StorySample(
        params=params,
        story=render(world),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


def emit(sample: StorySample, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world is not None:
        print(dump_trace(sample.world))
    if qa:
        print()
        print(format_qa(sample))


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program())
    names = {symbol.name for symbol in model}
    if "good_ending" in names:
        print("OK: ASP twin matches the repaired, helpful pitcher story state.")
        return 0
    print("MISMATCH: ASP twin did not derive good_ending.")
    return 1


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program())
        return
    if args.verify:
        sample = generate(StoryParams("Fenn", "fox", "Old Badger"))
        if not sample.story or "tattered pitcher" not in sample.story:
            raise StoryError("verification story was not generated")
        sys.exit(asp_verify())
    if args.asp:
        import asp
        model = asp.one_model(asp_program())
        print("ASP atoms:", " ".join(sorted(symbol.name for symbol in model)))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    count = len(TALES) if args.all else max(1, args.n)
    samples: list[StorySample] = []
    for index in range(count):
        seed = base_seed + index
        params = resolve_params(args, random.Random(seed))
        params.seed = seed
        if args.all:
            params.tale_index = index % len(TALES)
        samples.append(generate(params))

    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([sample.to_dict() for sample in samples], indent=2, ensure_ascii=False))
        return

    for index, sample in enumerate(samples):
        emit(sample, trace=args.trace, qa=args.qa, header=f"### variant {index + 1}" if len(samples) > 1 else "")
        if index < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()

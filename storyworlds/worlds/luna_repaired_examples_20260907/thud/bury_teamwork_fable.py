#!/usr/bin/env python3
"""
A small fable world about burying a seed together.
"""

from __future__ import annotations

import argparse
import json
import os
import random
import sys
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from results import QAItem, StoryError, StorySample  # noqa: E402


@dataclass
class Entity:
    id: str
    kind: str
    type: str
    label: str
    role: str = ""
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))


@dataclass
class Place:
    id: str
    label: str
    tags: set[str] = field(default_factory=set)


@dataclass
class World:
    place: Place
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
        return "\n\n".join(" ".join(part) for part in self.paragraphs if part)


@dataclass(frozen=True)
class FableArc:
    key: str
    object_name: str
    trouble: str
    tool: str
    opening: tuple[str, str]
    problem: tuple[str, str]
    teamwork: tuple[str, str]
    ending: tuple[str, str]
    moral: str


ARCS = (
    FableArc(
        key="acorn",
        object_name="acorn",
        trouble="the hard ground would not open",
        tool="a smooth little stone",
        opening=(
            "Near {place}, {a} found an acorn beneath an oak tree.",
            "{b} dreamed it might become a sheltering tree for every small creature.",
        ),
        problem=(
            "They tried to bury it, but the dry earth held tight.",
            "The acorn rolled away, and each friend pulled in a different direction.",
        ),
        teamwork=(
            "{a} loosened the soil with a twig while {b} carried water in a leaf.",
            "Together they made a small, soft hollow and tucked the acorn inside.",
        ),
        ending=(
            "Rain filled the hollow, and a green shoot rose beside the oak.",
            "The friends bowed to the sprout, glad that shared work had given it a start.",
        ),
        moral="A small task grows easier when willing helpers share it.",
    ),
    FableArc(
        key="bean",
        object_name="bean",
        trouble="a thorny patch guarded the garden bed",
        tool="a broad leaf",
        opening=(
            "At {place}, {a} found a bright bean beside the garden wall.",
            "{b} said, 'Let us bury it, and perhaps it will feed a hungry bird.'",
        ),
        problem=(
            "The best patch was hidden beneath prickly weeds.",
            "One friend could not hold the weeds aside and dig at once.",
        ),
        teamwork=(
            "{a} held the weeds back with {tool}, while {b} dug a neat place.",
            "Then they changed jobs and covered the bean with warm earth.",
        ),
        ending=(
            "Soon two green leaves lifted above the soil like tiny flags.",
            "A sparrow found shade there, and the friends shared a happy nod.",
        ),
        moral="When hands take turns, a thorny job can become a gentle one.",
    ),
    FableArc(
        key="bulb",
        object_name="flower bulb",
        trouble="the planting hollow kept filling with pebbles",
        tool="a patient paw",
        opening=(
            "In {place}, {a} discovered a flower bulb shaped like a little moon.",
            "{b} promised to bury it where spring sunlight could find it.",
        ),
        problem=(
            "Each time they dug, pebbles tumbled back into the hollow.",
            "Their first plan failed because neither friend watched the loose stones.",
        ),
        teamwork=(
            "{a} cleared the pebbles with {tool}, while {b} guarded the hollow.",
            "Working side by side, they placed the bulb deep and covered it softly.",
        ),
        ending=(
            "In spring, a golden flower opened where the bulb had slept.",
            "Bees hummed above it, and the friends remembered their careful teamwork.",
        ),
        moral="Careful helpers accomplish what hurried workers leave unfinished.",
    ),
    FableArc(
        key="seed",
        object_name="seed",
        trouble="the riverbank soil kept sliding away",
        tool="a bundle of grass",
        opening=(
            "Beside the river at {place}, {a} found a tiny seed.",
            "{b} wished to bury it where the morning sun touched the bank.",
        ),
        problem=(
            "The loose soil slid downhill whenever they made a hole.",
            "The little seed nearly floated away on a trickle of water.",
        ),
        teamwork=(
            "{a} pressed {tool} along the bank while {b} made a sheltered hollow.",
            "Together they buried the seed and built a small rim around it.",
        ),
        ending=(
            "The next morning, a brave green stem stood above the riverbank.",
            "The flowing water passed by, while the young plant held fast.",
        ),
        moral="Two steady hearts can give a small hope a safe place to grow.",
    ),
)


PLACES = {
    "oak_grove": Place("oak_grove", "the oak grove", {"outdoors", "trees"}),
    "garden": Place("garden", "the village garden", {"outdoors", "plants"}),
    "riverbank": Place("riverbank", "the quiet riverbank", {"outdoors", "water"}),
}

NAMES = {
    "fox": ["Fenn", "Rusty", "Pip"],
    "rabbit": ["Clover", "Nell", "Hazel"],
    "badger": ["Bran", "Moss", "Bramble"],
    "squirrel": ["Suri", "Nutmeg", "Tansy"],
}

CURATED = [
    ("oak_grove", "Fenn", "Clover", "fox", "rabbit"),
    ("garden", "Bran", "Tansy", "badger", "squirrel"),
    ("riverbank", "Hazel", "Pip", "rabbit", "fox"),
]


@dataclass
class StoryParams:
    place: str
    hero_name: str
    helper_name: str
    hero_kind: str = "fox"
    helper_kind: str = "rabbit"
    seed: Optional[int] = None


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="A teamwork fable about burying a seed.")
    parser.add_argument("--place", choices=PLACES)
    parser.add_argument("--hero")
    parser.add_argument("--helper")
    parser.add_argument("--hero-kind", choices=NAMES)
    parser.add_argument("--helper-kind", choices=NAMES)
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
    place = args.place or rng.choice(list(PLACES))
    hero_kind = args.hero_kind or rng.choice(list(NAMES))
    helper_kind = args.helper_kind or rng.choice([kind for kind in NAMES if kind != hero_kind])
    hero_name = args.hero or rng.choice(NAMES[hero_kind])
    helper_name = args.helper or rng.choice([name for name in NAMES[helper_kind] if name != hero_name])
    return StoryParams(place, hero_name, helper_name, hero_kind, helper_kind)


def tell(params: StoryParams) -> World:
    if params.place not in PLACES:
        raise StoryError("Unknown place.")
    if params.hero_kind not in NAMES or params.helper_kind not in NAMES:
        raise StoryError("Unknown animal kind.")
    if params.hero_name == params.helper_name:
        raise StoryError("The hero and helper must have different names.")

    rng = random.Random(params.seed if params.seed is not None else sum(ord(c) for c in params.hero_name + params.helper_name))
    arc = rng.choice(ARCS)
    world = World(PLACES[params.place])
    hero = world.add(Entity(params.hero_name, "character", params.hero_kind, params.hero_name, "hero"))
    helper = world.add(Entity(params.helper_name, "character", params.helper_kind, params.helper_name, "helper"))
    seed = world.add(Entity("seedling", "thing", arc.object_name, arc.object_name))

    values = {
        "a": hero.label,
        "b": helper.label,
        "place": world.place.label,
        "tool": arc.tool,
    }

    for sentence in arc.opening:
        world.say(sentence.format(**values))
    world.para()

    hero.memes["hope"] += 1
    helper.memes["hope"] += 1
    seed.meters["buried"] = 0
    for sentence in arc.problem:
        world.say(sentence.format(**values))
    world.para()

    hero.memes["helpfulness"] += 1
    helper.memes["helpfulness"] += 1
    hero.meters["teamwork"] += 1
    helper.meters["teamwork"] += 1
    seed.meters["buried"] = 1
    seed.meters["safe"] = 1
    for sentence in arc.teamwork:
        world.say(sentence.format(**values))
    world.para()

    hero.memes["joy"] += 1
    helper.memes["joy"] += 1
    seed.meters["grown"] = 1
    for sentence in arc.ending:
        world.say(sentence.format(**values))

    world.facts.update(
        hero=hero,
        helper=helper,
        seed=seed,
        arc=arc,
        object_name=arc.object_name,
        trouble=arc.trouble,
        tool=arc.tool,
        result=arc.ending[0].format(**values),
        moral=arc.moral,
    )
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        'Write a child-friendly fable that uses the word "bury" and shows teamwork.',
        f"Tell a fable about {f['hero'].label} and {f['helper'].label} solving this problem together: {f['trouble']}.",
        f"Write a gentle fable about burying a {f['object_name']} with a clear moral.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    return [
        QAItem(
            "What problem did the friends face?",
            f"They faced a planting problem: {f['trouble']}. Their first effort was not enough because they needed to work together.",
        ),
        QAItem(
            "How did the friends use teamwork?",
            f"They shared the work by using {f['tool']}: {f['arc'].teamwork[0].format(a=f['hero'].label, b=f['helper'].label, tool=f['tool'])}",
        ),
        QAItem(
            "What showed that their work succeeded?",
            f"The ending showed the change clearly: {f['result']}",
        ),
        QAItem(
            "What lesson does the fable teach?",
            f"The lesson is: {f['moral']}",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            "What does bury mean?",
            "To bury something means to place it under soil or another covering.",
        ),
        QAItem(
            "What is teamwork?",
            "Teamwork means sharing a job and helping one another reach the same goal.",
        ),
        QAItem(
            "Why do seeds need soil?",
            "Seeds need soil to hold them in place and provide a place where roots can begin to grow.",
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


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for entity in world.entities.values():
        meters = {key: value for key, value in entity.meters.items() if value}
        memes = {key: value for key, value in entity.memes.items() if value}
        lines.append(f"  {entity.id}: type={entity.type}, meters={meters}, memes={memes}")
    return "\n".join(lines)


ASP_RULES = r"""
buried(seed) :- seed(seed), buried_meter(seed, 1).
teamwork(hero, helper) :- hero(hero), helper(helper), worked(hero), worked(helper).
grown(seed) :- buried(seed), teamwork(_, _).
#show buried/1.
#show teamwork/2.
#show grown/1.
"""


def asp_facts() -> str:
    import asp
    return "\n".join(
        [
            asp.fact("seed", "seed"),
            asp.fact("buried_meter", "seed", 1),
            asp.fact("hero", "hero"),
            asp.fact("helper", "helper"),
            asp.fact("worked", "hero"),
            asp.fact("worked", "helper"),
        ]
    )


def asp_program(show: str = "") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    try:
        model = asp.one_model(asp_program())
        names = {symbol.name for symbol in model}
        if "buried" not in names or "grown" not in names:
            print("ASP parity check failed.")
            return 1
        sample = generate(StoryParams("oak_grove", "Fenn", "Clover", "fox", "rabbit", 3))
        if "bury" not in sample.story.lower() and "buried" not in sample.story.lower():
            print("Generated story omitted the burial turn.")
            return 1
    except Exception as exc:
        print(f"Verification failed: {exc}")
        return 1
    print("OK: smoke tests passed.")
    return 0


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


def emit(sample: StorySample, trace: bool = False, qa: bool = False, header: str = "") -> None:
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
        import asp
        model = asp.one_model(asp_program())
        print([str(symbol) for symbol in model])
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    if args.all:
        samples = [
            generate(StoryParams(place, hero, helper, hero_kind, helper_kind, base_seed + i))
            for i, (place, hero, helper, hero_kind, helper_kind) in enumerate(CURATED)
        ]
    else:
        samples = []
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
        emit(sample, trace=args.trace, qa=args.qa, header=f"### variant {index + 1}" if len(samples) > 1 else "")
        if index + 1 < len(samples):
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()

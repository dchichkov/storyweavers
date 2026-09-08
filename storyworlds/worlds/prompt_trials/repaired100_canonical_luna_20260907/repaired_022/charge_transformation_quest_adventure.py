#!/usr/bin/env python3
"""
A small storyworld about Luna, a charge, and a transformation quest.

Luna must carry a fading charge through a dark garden to wake the Moon Lantern.
The charge changes form as Luna learns that careful help is stronger than a
frightened rush.
"""

from __future__ import annotations

import argparse
import json
import random
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

HERE = Path(__file__).resolve()
ROOT = next(parent for parent in HERE.parents if (parent / "results.py").is_file())
sys.path.insert(0, str(ROOT))
from results import QAItem, StoryError, StorySample  # noqa: E402


NAME_POOL = ["Luna", "Mira", "Tavi", "Niko", "Ari", "Sela"]
HELPER_POOL = ["her brother", "her grandmother", "a careful fox", "her friend Pip"]
PATH_POOL = ["the fern tunnel", "the glass bridge", "the whispering garden", "the old hill path"]
CHARGE_POOL = ["a blue spark", "a warm amber bead", "a silver glow", "a tiny gold flame"]


@dataclass
class StoryParams:
    name: str = "Luna"
    helper: str = "her brother"
    path: str = "the fern tunnel"
    charge: str = "a blue spark"
    seed: Optional[int] = None


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    label: str = ""
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def __post_init__(self) -> None:
        for key in ("charge", "distance", "wind", "warmth"):
            self.meters.setdefault(key, 0.0)
        for key in ("worry", "courage", "trust", "relief", "wonder"):
            self.memes.setdefault(key, 0.0)


@dataclass
class World:
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


def subject(label: str) -> str:
    return label[:1].upper() + label[1:]


def seed_number(params: StoryParams) -> int:
    if params.seed is not None:
        return params.seed
    return int.from_bytes(
        f"{params.name}|{params.helper}|{params.path}|{params.charge}".encode(),
        "little",
    )


def tell_world(params: StoryParams) -> World:
    rng = random.Random(seed_number(params))
    w = World()
    luna = w.add(Entity(params.name, "character", params.name))
    helper = w.add(Entity("helper", "character", params.helper))
    charge = w.add(Entity("charge", "magical charge", params.charge))
    lantern = w.add(Entity("lantern", "goal", "the Moon Lantern"))

    route = params.path
    obstacle = rng.choice([
        "a gust shook the hanging vines",
        "a shadow crossed the stepping stones",
        "a rain of leaves covered the trail",
        "a little stream spilled across the path",
    ])
    clue = rng.choice([
        "the charge brightened whenever Luna held it near a calm breath",
        "the safest stones were marked by round drops of moonlight",
        "the wind weakened behind a wall of broad leaves",
        "the charge grew warmer when Luna and her helper moved together",
    ])
    transformation = rng.choice([
        "The spark became a glowing compass",
        "The amber bead unfolded into a tiny lantern",
        "The silver glow stretched into a shining bridge",
        "The gold flame changed into a bright winged moth",
    ])
    ending = rng.choice([
        "The Moon Lantern lit the garden, and every dewdrop shone like a small star.",
        "Warm light spilled over the hill, showing the way home through the quiet grass.",
        "The garden woke in a ring of blue flowers, each one holding a dot of gentle light.",
        "The lantern hummed above the gate while Luna carried its first brave glow in her hands.",
    ])

    luna.meters["charge"] = 5
    luna.meters["distance"] = 7
    luna.memes["worry"] = 1
    w.facts.update(
        params=params,
        route=route,
        obstacle=obstacle,
        clue=clue,
        transformation=transformation,
        ending=ending,
        resolved=False,
    )

    w.say(f"At dusk, {params.name} found {params.charge} sleeping beneath a silver leaf.")
    w.say(
        f"The old Moon Lantern had gone dark, and only this charge could wake it beyond {route}."
    )
    w.say(f"{params.name} tucked the charge into a clear shell and began the quest.")
    w.para()

    w.say(f"Halfway along the trail, {obstacle}.")
    w.say(
        f"The wind tugged at the shell, and the charge shrank to a trembling dot of light."
    )
    luna.meters["charge"] = 2
    luna.meters["wind"] = 3
    luna.memes["worry"] = 4
    w.say(f'"If I hurry, I can still reach the lantern!" {params.name} said.')
    w.say(
        f'"If you hurry, the charge may fade,' said {params.helper}. 'Let us watch what it needs."'
    )
    w.para()

    w.say(f"Together they noticed that {clue}.")
    luna.memes["trust"] = 2
    luna.memes["courage"] = 2
    luna.memes["worry"] = 1
    luna.meters["wind"] = 1
    luna.meters["charge"] = 3
    w.say(
        f"{params.name} slowed down. {params.helper} shielded the shell, and Luna matched each step to a quiet breath."
    )
    w.say(f"The charge warmed, and {transformation.lower()} before their eyes.")
    luna.meters["charge"] = 6
    luna.meters["warmth"] = 4
    luna.memes["wonder"] = 3
    w.say(f'"It changed because we changed our plan," {params.name} whispered.')
    w.say(f'"And because you let me help," said {params.helper}.')
    w.para()

    w.say(
        f"The transformed charge guided them through {route} and brought them to the Moon Lantern."
    )
    w.say(f"{params.name} placed it in the lantern's empty heart.")
    w.say(ending)
    w.facts["resolved"] = True
    w.facts["solution"] = "Luna slowed down, accepted help, and used the transformed charge."
    return w


def generation_prompts(world: World) -> list[str]:
    p: StoryParams = world.facts["params"]
    return [
        f"Write an adventure about {p.name} carrying {p.charge} through {p.path} to wake the Moon Lantern.",
        f"Tell a child-friendly transformation quest in which {p.name} learns that a charge becomes stronger through patience and help.",
        f"Create an adventure with {p.name}, {p.helper}, a fading charge, a dangerous path, and a magical transformation.",
    ]


def story_qa(world: World) -> list[QAItem]:
    p: StoryParams = world.facts["params"]
    return [
        QAItem(
            f"What quest does {p.name} begin?",
            f"{p.name} begins a quest to carry {p.charge} through {p.path} and wake the Moon Lantern.",
        ),
        QAItem(
            "What makes the quest difficult?",
            f"{world.facts['obstacle'].capitalize()}, and the charge shrinks when the wind pulls at its shell.",
        ),
        QAItem(
            "What clue helps Luna solve the problem?",
            f"{world.facts['clue'].capitalize()}. This shows Luna and her helper that slowing down will protect the charge.",
        ),
        QAItem(
            "How does the charge transform?",
            f"{world.facts['transformation']} after Luna accepts help, moves carefully, and follows the useful clue.",
        ),
        QAItem(
            "How does the story end?",
            world.facts["ending"],
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            "What is a charge in this story?",
            "A charge is a small store of magical energy that can power the Moon Lantern.",
        ),
        QAItem(
            "What is a transformation?",
            "A transformation is a change in form or condition, such as a spark becoming a lantern.",
        ),
        QAItem(
            "What is a quest?",
            "A quest is a purposeful journey with a goal, obstacles, and a result.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== Prompts =="]
    lines.extend(f"{i}. {prompt}" for i, prompt in enumerate(sample.prompts, 1))
    lines.append("")
    lines.append("== Story QA ==")
    for item in sample.story_qa:
        lines.extend([f"Q: {item.question}", f"A: {item.answer}"])
    lines.append("")
    lines.append("== World QA ==")
    for item in sample.world_qa:
        lines.extend([f"Q: {item.question}", f"A: {item.answer}"])
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for entity in world.entities.values():
        meters = {k: round(v, 2) for k, v in entity.meters.items() if v}
        memes = {k: round(v, 2) for k, v in entity.memes.items() if v}
        lines.append(f"  {entity.id} ({entity.kind}) meters={meters} memes={memes}")
    lines.append(f"  facts={world.facts}")
    return "\n".join(lines)


ASP_RULES = r"""
charged(Child) :- carries(Child, Charge), charge(Charge).
transformed(Charge) :- charged(Child), accepts_help(Child), patience(Child).
quest_complete(Child) :- transformed(Charge), reaches_lantern(Child).
valid_quest(Child) :- quest_complete(Child).
"""


def asp_facts() -> str:
    import asp

    return "\n".join(
        [
            asp.fact("charge", "moon_charge"),
            asp.fact("carries", "luna", "moon_charge"),
            asp.fact("accepts_help", "luna"),
            asp.fact("patience", "luna"),
            asp.fact("reaches_lantern", "luna"),
        ]
    )


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    try:
        import asp
    except Exception as err:
        print(f"ASP unavailable: {err}")
        return 1
    model = asp.one_model(
        asp_program("#show charged/1.\n#show transformed/1.\n#show quest_complete/1.\n#show valid_quest/1.")
    )
    actual = {
        ("charged", tuple(x)) for x in asp.atoms(model, "charged")
    } | {
        ("transformed", tuple(x)) for x in asp.atoms(model, "transformed")
    } | {
        ("quest_complete", tuple(x)) for x in asp.atoms(model, "quest_complete")
    } | {
        ("valid_quest", tuple(x)) for x in asp.atoms(model, "valid_quest")
    }
    expected = {
        ("charged", ("luna",)),
        ("transformed", ("moon_charge",)),
        ("quest_complete", ("luna",)),
        ("valid_quest", ("luna",)),
    }
    if actual != expected:
        print("MISMATCH between ASP and Python parity:")
        print("  ASP:", sorted(actual))
        print("  PY :", sorted(expected))
        return 1
    sample = generate(StoryParams(seed=17))
    if not sample.story or not sample.world.facts["resolved"]:
        print("Generated story verification failed.")
        return 1
    print("OK: ASP parity and generated story checks passed.")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Luna's charge transformation quest adventure.")
    parser.add_argument("--name", choices=NAME_POOL)
    parser.add_argument("--helper", choices=HELPER_POOL)
    parser.add_argument("--path", choices=PATH_POOL)
    parser.add_argument("--charge", choices=CHARGE_POOL)
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
    return StoryParams(
        name=args.name or rng.choice(NAME_POOL),
        helper=args.helper or rng.choice(HELPER_POOL),
        path=args.path or rng.choice(PATH_POOL),
        charge=args.charge or rng.choice(CHARGE_POOL),
    )


def validate(params: StoryParams) -> None:
    if not params.name.strip():
        raise StoryError("name must not be empty")
    if params.path not in PATH_POOL:
        raise StoryError(f"unknown quest path: {params.path}")
    if params.charge not in CHARGE_POOL:
        raise StoryError(f"unknown charge: {params.charge}")


def generate(params: StoryParams) -> StorySample:
    validate(params)
    world = tell_world(params)
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
        print(asp_program("#show charged/1.\n#show transformed/1.\n#show quest_complete/1.\n#show valid_quest/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        try:
            import asp
        except Exception as err:
            raise SystemExit(f"ASP unavailable: {err}")
        model = asp.one_model(
            asp_program("#show charged/1.\n#show transformed/1.\n#show quest_complete/1.\n#show valid_quest/1.")
        )
        print(sorted(
            [(name, args_) for name in ("charged", "transformed", "quest_complete", "valid_quest")
             for args_ in asp.atoms(model, name)]
        ))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        for index, path in enumerate(PATH_POOL):
            params = StoryParams(
                name=NAME_POOL[index % len(NAME_POOL)],
                helper=HELPER_POOL[index % len(HELPER_POOL)],
                path=path,
                charge=CHARGE_POOL[index % len(CHARGE_POOL)],
                seed=base_seed + index,
            )
            samples.append(generate(params))
    else:
        seen: set[str] = set()
        index = 0
        while len(samples) < max(0, args.n):
            seed = base_seed + index
            index += 1
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

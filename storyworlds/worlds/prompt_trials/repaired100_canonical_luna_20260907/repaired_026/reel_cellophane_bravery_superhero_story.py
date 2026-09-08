#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import random
import sys
from dataclasses import dataclass, field
from typing import Optional

_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
if os.path.exists(os.path.join(_root, "results.py")):
    sys.path.insert(0, _root)
else:
    sys.path.insert(0, os.path.dirname(_root))
from results import QAItem, StoryError, StorySample  # noqa: E402


@dataclass
class Entity:
    id: str
    kind: str
    label: str
    owner: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)


@dataclass
class World:
    place: str
    entities: dict[str, Entity] = field(default_factory=dict)
    facts: dict[str, object] = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])

    def add(self, entity: Entity) -> Entity:
        self.entities[entity.id] = entity
        return entity

    def get(self, key: str) -> Entity:
        return self.entities[key]

    def say(self, text: str) -> None:
        self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)


@dataclass
class StoryParams:
    seed: Optional[int] = None
    hero: str = "Luna"
    helper: str = "Bolt"
    place: str = "the Skybridge"
    reel_kind: str = "rescue reel"
    cellophane_color: str = "silver"
    challenge: str = "a gust has torn a child’s kite toward the edge of the Skybridge"


HERO_NAMES = ["Luna", "Nova", "Ari", "Maya", "Skye"]
HELPER_NAMES = ["Bolt", "Pip", "Echo", "Rex", "Tiko"]
PLACES = ["the Skybridge", "the Moonlit Market", "the Star Tower", "the Cloud Park"]
REEL_KINDS = ["rescue reel", "silver rescue reel", "skyline reel"]
CELLOPHANE_COLORS = ["silver", "blue", "golden", "rainbow"]
CHALLENGES = [
    "a gust has torn a child’s kite toward the edge of the Skybridge",
    "a little robot is stranded on a high delivery platform",
    "a parade banner is whipping loose above the crowded square",
    "a puppy’s bright balloon has tangled on a tower antenna",
]


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="A superhero story about Luna, a reel, and cellophane.")
    parser.add_argument("--hero")
    parser.add_argument("--helper")
    parser.add_argument("--place")
    parser.add_argument("--reel-kind")
    parser.add_argument("--cellophane-color")
    parser.add_argument("--challenge")
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
    hero = args.hero or rng.choice(HERO_NAMES)
    helper = args.helper or rng.choice([name for name in HELPER_NAMES if name != hero])
    place = args.place or rng.choice(PLACES)
    reel_kind = args.reel_kind or rng.choice(REEL_KINDS)
    color = args.cellophane_color or rng.choice(CELLOPHANE_COLORS)
    challenge = args.challenge or rng.choice(CHALLENGES)
    if hero == helper:
        raise StoryError("The hero and helper must have different names.")
    if not hero.strip() or not helper.strip():
        raise StoryError("Hero and helper names cannot be empty.")
    if "reel" not in reel_kind.lower():
        raise StoryError("The equipment must be a reel.")
    if not place.strip():
        raise StoryError("The setting cannot be empty.")
    return StoryParams(
        seed=args.seed,
        hero=hero,
        helper=helper,
        place=place,
        reel_kind=reel_kind,
        cellophane_color=color,
        challenge=challenge,
    )


def make_world(params: StoryParams) -> World:
    world = World(params.place)
    hero = world.add(Entity(
        "hero",
        "superhero",
        params.hero,
        meters={"height": 1.7, "distance": 0.0, "safety": 0.3},
        memes={"bravery": 0.5, "worry": 0.5, "trust": 0.2, "relief": 0.0},
    ))
    helper = world.add(Entity(
        "helper",
        "helper",
        params.helper,
        meters={"distance": 0.0},
        memes={"bravery": 0.3, "worry": 0.4, "trust": 0.4},
    ))
    reel = world.add(Entity(
        "reel",
        "reel",
        params.reel_kind,
        owner=params.hero,
        meters={"length": 18.0, "strength": 0.9, "tension": 0.0},
        memes={"reliability": 0.9},
    ))
    cellophane = world.add(Entity(
        "cellophane",
        "cellophane",
        f"{params.cellophane_color} cellophane",
        meters={"length": 6.0, "strength": 0.35, "visibility": 0.8},
        memes={"cheer": 0.8},
    ))
    world.facts.update(hero=hero, helper=helper, reel=reel, cellophane=cellophane)
    return world


def tell(params: StoryParams) -> World:
    world = make_world(params)
    rng = random.Random((params.seed or 0) ^ 0xBRAA if False else (params.seed or 0) ^ 0xB7A6)
    hero = world.get("hero")
    helper = world.get("helper")
    reel = world.get("reel")
    cellophane = world.get("cellophane")

    world.facts.update(
        challenge=params.challenge,
        method=f"secured the {cellophane.label} to the {reel.label} before sending it across the gap",
        danger="the wind could snap the line and carry the child toward the drop",
        ending="the child landed safely while the cellophane shimmered like a tiny cape in the sunlight",
        lesson="Bravery is not the absence of fear; it is choosing a careful helpful action while fear is present.",
    )

    openings = [
        f"At {params.place}, {params.hero} watched over the city from a bright rooftop.",
        f"The alarms chimed across {params.place}, where {params.hero} and {params.helper} were helping neighbors.",
        f"High above {params.place}, {params.hero} checked the rescue gear before the afternoon patrol.",
    ]
    world.say(rng.choice(openings))
    world.say(f"Then {params.challenge}. The loose kite tugged hard, and the wind made the high ledge dangerous.")
    world.para()

    world.say(f"{params.helper} pointed at the drop. \"That is too far! What can we do?\"")
    world.say(f"{params.hero} held the {reel.label} and noticed a sheet of {cellophane.label}. \"We can make a safe guide,\" {params.hero} said. \"Stay with me and watch the line.\"")
    world.say(f"The first idea was risky because {world.facts['danger']}. {params.hero}'s worry rose, but so did {params.hero}'s bravery.")
    world.say(f"\"I am scared,\" {params.hero} admitted. \"I will still take the careful next step.\"")
    world.para()

    world.say(f"{params.hero} {world.facts['method']}.")
    world.say(f"{params.helper} braced the reel against a heavy rail. \"The line is steady!\" {params.helper} called.")
    world.say(f"{params.hero} moved slowly, clipped the guide to the kite string, and pulled it away from the edge instead of rushing.")
    world.say(f"The child reached the safe side. \"You saved my kite!\" the child cried.")
    world.say(f"\"You helped too,\" {params.hero} told {params.helper}. \"A brave team checks every knot.\"")
    world.para()

    world.say(f"By sunset, {world.facts['ending']}.")
    world.say(f"{params.helper} smiled. \"I thought bravery meant never feeling afraid.\"")
    world.say(f"{params.hero} shook their head. \"It means feeling afraid and helping wisely anyway.\"")

    hero.memes["bravery"] = 1.0
    hero.memes["worry"] = 0.1
    hero.memes["trust"] = 0.9
    hero.memes["relief"] = 1.0
    helper.memes["bravery"] = 0.8
    helper.memes["trust"] = 0.9
    reel.meters["tension"] = 0.0
    reel.meters["safety"] = 1.0
    cellophane.meters["length"] = 5.0
    world.facts["rescued"] = True
    world.facts["hero_bravery"] = True
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f"Write a Superhero Story in which {world.get('hero').label} uses a reel and cellophane to solve this danger: {f['challenge']}.",
        f"Tell a child-friendly superhero adventure showing that bravery means acting carefully despite fear. Include {world.get('reel').label} and {world.get('cellophane').label}.",
        f"Write a short story where {world.get('hero').label} and {world.get('helper').label} work as a team, use a reel, and rescue someone safely.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = world.get("hero").label
    helper = world.get("helper").label
    reel = world.get("reel").label
    cellophane = world.get("cellophane").label
    return [
        QAItem(
            f"What danger did {hero} face at the beginning?",
            f"At the beginning, {f['challenge']}, and the wind made the high ledge dangerous.",
        ),
        QAItem(
            f"How did {hero} use the reel and cellophane?",
            f"{hero} secured the {cellophane} to the {reel} to make a careful guide across the gap.",
        ),
        QAItem(
            f"Why was the rescue risky?",
            f"The wind could snap the line and carry the child toward the drop, so {hero} had to move slowly and check every knot.",
        ),
        QAItem(
            f"How did {helper} help?",
            f"{helper} braced the reel against a heavy rail and watched the line while {hero} guided the kite away from the edge.",
        ),
        QAItem(
            "What did the ending show about bravery?",
            f"The ending showed that {f['lesson']}",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            "What is a reel?",
            "A reel is a spool or device that holds and winds something such as string, wire, or film.",
        ),
        QAItem(
            "What is cellophane?",
            "Cellophane is a thin, clear, flexible material often used to wrap objects.",
        ),
        QAItem(
            "What is bravery?",
            "Bravery is choosing to do something helpful or right even when you feel afraid.",
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
        meters = {k: round(v, 3) for k, v in entity.meters.items()}
        memes = {k: round(v, 3) for k, v in entity.memes.items()}
        owner = f" owner={entity.owner}" if entity.owner else ""
        lines.append(f"  {entity.id}: {entity.kind} {entity.label}{owner} meters={meters} memes={memes}")
    lines.append(f"  rescued={world.facts.get('rescued', False)}")
    return "\n".join(lines)


ASP_RULES = r"""
safe_reel(R) :- reel(R), strength(R, S), S >= 0.8.
careful_hero(H) :- hero(H), bravery(H, B), B >= 0.8.
rescue_possible(H, R) :- careful_hero(H), safe_reel(R), not broken(R).
"""


def asp_facts() -> str:
    import storyworlds.asp as asp
    return "\n".join([
        asp.fact("hero", "hero"),
        asp.fact("reel", "reel"),
        asp.fact("strength", "reel", 0.9),
        asp.fact("bravery", "hero", 1.0),
    ])


def asp_program(show: str = "#show rescue_possible/2.") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import storyworlds.asp as asp
    model = asp.one_model(asp_program("#show safe_reel/1. #show careful_hero/1. #show rescue_possible/2."))
    shown = {(sym.name, tuple(
        arg.number if arg.type.name == "Number" else arg.name
        for arg in sym.arguments
    )) for sym in model}
    expected = {
        ("safe_reel", ("reel",)),
        ("careful_hero", ("hero",)),
        ("rescue_possible", ("hero", "reel")),
    }
    if shown != expected:
        print("MISMATCH between ASP and Python assumptions.")
        print("got:", sorted(shown))
        print("expected:", sorted(expected))
        return 1
    sample = generate(StoryParams(seed=7))
    if "reel" not in sample.story.lower() or "cellophane" not in sample.story.lower():
        print("MISMATCH: generated story omitted required seed words.")
        return 1
    if not sample.world.facts.get("rescued"):
        print("MISMATCH: generated story did not resolve the rescue.")
        return 1
    print("OK: ASP parity and generated-story checks passed.")
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
        print()
        print(dump_trace(sample.world))
    if qa:
        print()
        print(format_qa(sample))


CURATED = [
    StoryParams(seed=1, hero="Luna", helper="Bolt", place="the Skybridge", reel_kind="rescue reel", cellophane_color="silver", challenge=CHALLENGES[0]),
    StoryParams(seed=2, hero="Nova", helper="Echo", place="the Star Tower", reel_kind="skyline reel", cellophane_color="blue", challenge=CHALLENGES[1]),
    StoryParams(seed=3, hero="Ari", helper="Pip", place="the Cloud Park", reel_kind="silver rescue reel", cellophane_color="rainbow", challenge=CHALLENGES[2]),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program())
        return
    if args.verify:
        raise SystemExit(asp_verify())
    if args.asp:
        import storyworlds.asp as asp
        print("ASP atoms:")
        for symbol in asp.one_model(asp_program()):
            print(symbol)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(params) for params in CURATED]
    else:
        seen: set[str] = set()
        for offset in range(max(args.n * 20, 20)):
            if len(samples) >= args.n:
                break
            seed = base_seed + offset
            try:
                params = resolve_params(args, random.Random(seed))
            except StoryError:
                continue
            params.seed = seed
            sample = generate(params)
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

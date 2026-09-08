#!/usr/bin/env python3
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

_here = os.path.dirname(os.path.abspath(__file__))
_root = os.path.dirname(os.path.dirname(os.path.dirname(_here)))
sys.path.insert(0, _root)
from results import QAItem, StoryError, StorySample  # noqa: E402


@dataclass
class Entity:
    id: str
    kind: str
    label: str
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)
    location: str = "the tool shed"

    def __post_init__(self) -> None:
        for key in ("ink", "risk", "care", "pride", "fear", "wisdom"):
            self.meters.setdefault(key, 0.0)
            self.memes.setdefault(key, 0.0)


@dataclass
class StoryParams:
    name: str
    animal: str
    elder: str
    tool: str
    seed: Optional[int] = None
    telling: int = 0


@dataclass
class World:
    params: StoryParams
    entities: dict[str, Entity] = field(default_factory=dict)
    facts: dict[str, object] = field(default_factory=dict)
    paragraphs: list[str] = field(default_factory=list)
    fired: set[str] = field(default_factory=set)

    def add(self, entity: Entity) -> Entity:
        self.entities[entity.id] = entity
        return entity

    def say(self, text: str) -> None:
        self.paragraphs.append(text)

    def render(self) -> str:
        return "\n\n".join(self.paragraphs)


NAMES = ["Luna", "Mira", "Pip", "Niko", "Tavi"]
ANIMALS = ["fox", "rabbit", "mouse", "badger", "squirrel"]
ELDERS = ["Grandma", "Uncle Rowan", "Aunt Fern", "Old Moss"]
TOOLS = ["a wooden hammer", "a bright red wrench", "a brass shovel", "a little saw"]

OPENINGS = [
    "{name} the {animal} believed every tool had a secret waiting to be discovered.",
    "In the days when tools whispered to careful paws, {name} the {animal} loved the shed most of all.",
    "{name} the {animal} entered the tool shed with bright eyes and a proud little tail.",
    "The tool shed stood behind the garden like an old wooden castle, and {name} the {animal} wished to be its cleverest keeper.",
]

TALES = [
    {
        "danger": "a bottle of blue marking ink stood uncapped beside the workbench",
        "goal": "make a proud sign for the garden gate",
        "temptation": "stamp the sign quickly and show everyone the result",
        "warning": "A quick paw can leave a lasting blot.",
        "old": "A careless apprentice once spilled ink across the shed map and could no longer tell the safe paths from the forbidden ones.",
        "clue": "a bead of ink trembled at the bottle's lip whenever the bench shook",
        "fix": "placed the bottle in a steady tray, capped it between marks, and tested the tool on scrap wood first",
        "result": "the sign was clear, the tools stayed clean, and the garden path remained easy to read",
        "lesson": "a small blot begins when pride moves faster than care",
        "ending": "That evening, the clean sign gleamed by the gate, while the blue ink rested quietly beneath its cap.",
    },
    {
        "danger": "a leaking tin of red stain waited beside a pile of dry shavings",
        "goal": "repair the shed door before a storm arrived",
        "temptation": "drag the heavy door through the narrow aisle alone",
        "warning": "Do not let hurry turn one drop into a river.",
        "old": "Long ago, one rushed helper knocked over a stain tin, and the red trail led every creature to the wrong shelter.",
        "clue": "the tin rocked whenever the door scraped the floor",
        "fix": "asked the elder to steady the door, moved the stain tin to a high shelf, and swept the shavings away",
        "result": "the door was mended before the rain, and no spark or stain found the dry shavings",
        "lesson": "strength is safer when it listens to warning",
        "ending": "Rain drummed on the repaired door, but inside the shed the red tin stood still as a sleeping ember.",
    },
    {
        "danger": "a dark oil blot spread beneath the old lantern",
        "goal": "find a missing garden key",
        "temptation": "light the lantern and search under every bench",
        "warning": "A bright answer is not wise if it wakes a hidden danger.",
        "old": "In an elder tale, a careless flame crossed an oil blot and frightened the whole orchard into flight.",
        "clue": "the lantern wick smelled sharp, and the dark blot shone on the floorboards",
        "fix": "opened the shutters, used a long-handled grabber, and asked the elder to clean the oil before any flame was lit",
        "result": "the key was found without fire, and the floor was made safe",
        "lesson": "seeing clearly sometimes means refusing the brightest shortcut",
        "ending": "Moonlight found the key beneath the bench, and the clean floor reflected it like a small silver star.",
    },
]

KNOWLEDGE = [
    ("What is a blot?", "A blot is a dark or wet mark made when liquid spreads where it should not."),
    ("Why can a blot be dangerous in a tool shed?", "A blot can make a floor slippery, stain a map, or spread near dry shavings and other unsafe materials."),
    ("What is a cautionary tale?", "A cautionary tale shows a danger so characters can learn to make a wiser choice."),
    ("Why should tools be used carefully?", "Careful tool use protects the worker, the shed, and everyone who depends on the work."),
]


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    return StoryParams(
        name=args.name or rng.choice(NAMES),
        animal=args.animal or rng.choice(ANIMALS),
        elder=args.elder or rng.choice(ELDERS),
        tool=args.tool or rng.choice(TOOLS),
        seed=args.seed,
        telling=args.telling if args.telling is not None else rng.randrange(len(TALES)),
    )


def build_world(params: StoryParams) -> World:
    if not params.name or not params.animal:
        raise StoryError("A cautionary tool-shed tale needs a named young keeper.")
    if params.telling < 0 or params.telling >= len(TALES):
        raise StoryError("The chosen tale is not available.")
    tale = TALES[params.telling]
    world = World(params)
    hero = world.add(Entity("hero", "character", params.name))
    elder = world.add(Entity("elder", "character", params.elder))
    tool = world.add(Entity("tool", "thing", params.tool))
    ink = world.add(Entity("blot", "thing", "the dangerous blot"))
    hero.memes["pride"] = 1.0
    hero.meters["risk"] = 1.0
    world.facts.update(hero=hero, elder=elder, tool=tool, blot=ink, tale=tale)
    return world


def tell(params: StoryParams) -> World:
    world = build_world(params)
    hero = world.entities["hero"]
    elder = world.entities["elder"]
    tale = world.facts["tale"]
    rng = random.Random((params.seed or 0) ^ 0xB10F7)

    world.say(OPENINGS[params.telling % len(OPENINGS)].format(name=params.name, animal=params.animal))
    world.say(
        f"In the tool shed, {params.name}'s goal was to {tale['goal']} with {params.tool}. "
        f"Yet {tale['danger']}."
    )
    world.say(
        f"{params.name} reached toward the tempting shortcut: {tale['temptation']}. "
        f"The dust seemed to applaud."
    )
    world.say(f'"{tale["warning"]}" said {params.elder}, placing one careful paw on the bench.')
    world.say(f'"But the work must be finished," {params.name} replied. "How can caution help me now?"')
    world.say(
        f'"By helping you notice what haste hides," {params.elder} answered. '
        f'Look closely at the shed."'
    )

    world.para = lambda: None
    world.say(
        f"A cold memory passed through the rafters. Long before {params.name} was born, "
        f"{tale['old']}"
    )
    world.say(
        f"Then {params.name} noticed the clue: {tale['clue']}. "
        "The proud plan suddenly looked less clever."
    )
    hero.memes["pride"] = 0.0
    hero.memes["fear"] = 1.0
    hero.memes["wisdom"] = 1.0
    hero.meters["risk"] = 0.0
    world.say(
        f'"The warning was not meant to stop the work," {params.name} said. '
        f'"It was meant to stop the blot from becoming a disaster."'
    )
    world.say(
        f"{params.name} chose patience and {tale['fix']}. "
        f"{params.name} worked slowly while {params.elder} watched the dangerous places."
    )
    world.say(
        f"The plan worked: {tale['result']}. "
        f"The tool shed grew quiet, as if its old beams approved."
    )
    world.say(f"The cautionary lesson was clear: {tale['lesson']}.")
    world.say(tale["ending"])
    world.facts["resolved"] = True
    world.facts["lesson_learned"] = tale["lesson"]
    return world


def generate(params: StoryParams) -> StorySample:
    world = tell(params)
    hero = world.entities["hero"]
    elder = world.entities["elder"]
    tale = world.facts["tale"]
    prompts = [
        f"Write a cautionary myth about {hero.label}, a young {params.animal}, in a tool shed where {tale['danger']}.",
        f"Tell how {hero.label} learns from an old warning about a blot and changes the plan to {tale['fix']}.",
        f"End with a concrete image proving that {hero.label} chose care over pride: {tale['ending']}",
    ]
    story_qa = [
        QAItem("Who is the story about?", f"The story is about {hero.label}, a young {params.animal} learning to work carefully in the tool shed."),
        QAItem("What danger appeared?", f"The danger was that {tale['danger']}."),
        QAItem("What did the elder warn?", f"{elder.label} warned, '{tale['warning']}'"),
        QAItem("What clue changed the plan?", f"The clue was that {tale['clue']}. It showed that the quick choice could make the blot worse."),
        QAItem("How was the problem solved?", f"{hero.label} solved it when {tale['fix']}."),
        QAItem("What lesson was learned?", f"The lesson was that {tale['lesson']}."),
        QAItem("What final image proves the change?", f"The ending shows that {tale['ending']}"),
    ]
    world_qa = [QAItem(q, a) for q, a in KNOWLEDGE]
    return StorySample(params=params, story=world.render(), prompts=prompts, story_qa=story_qa, world_qa=world_qa, world=world)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for ent in world.entities.values():
        meters = {k: v for k, v in ent.meters.items() if v}
        memes = {k: v for k, v in ent.memes.items() if v}
        lines.append(f"  {ent.id}: {ent.label}; meters={meters}; memes={memes}; location={ent.location}")
    lines.append(f"  resolved={world.facts.get('resolved', False)}")
    return "\n".join(lines)


def format_qa(sample: StorySample) -> str:
    out = ["== (1) Generation prompts =="]
    out.extend(f"{i}. {p}" for i, p in enumerate(sample.prompts, 1))
    out.append("\n== (2) Story questions ==")
    for item in sample.story_qa:
        out.extend([f"Q: {item.question}", f"A: {item.answer}"])
    out.append("\n== (3) World knowledge ==")
    for item in sample.world_qa:
        out.extend([f"Q: {item.question}", f"A: {item.answer}"])
    return "\n".join(out)


def asp_facts() -> str:
    import asp
    return "\n".join([
        asp.fact("setting", "tool_shed"),
        asp.fact("danger", "blot"),
        asp.fact("requires", "care"),
        asp.fact("warning", "haste"),
        asp.fact("safe_method", "slow_work"),
    ])


ASP_RULES = r"""
risk(blot) :- danger(blot), requires(care).
lesson_learned :- warning(haste), safe_method(slow_work).
valid :- setting(tool_shed), risk(blot), lesson_learned.
#show risk/1.
#show lesson_learned/0.
#show valid/0.
"""


def asp_program() -> str:
    return asp_facts() + "\n" + ASP_RULES


def asp_verify() -> int:
    try:
        import asp
        model = asp.one_model(asp_program())
        valid = bool(asp.atoms(model, "valid"))
        sample = generate(StoryParams("Luna", "fox", "Grandma", "a wooden hammer", 7, 0))
        if valid and "blot" in sample.story.lower() and "tool shed" in sample.story.lower():
            print("OK: ASP gate agrees with Python story.")
            return 0
        print("MISMATCH: ASP and Python disagree.")
        return 1
    except ImportError:
        print("ASP verification unavailable: clingo is not installed.")
        return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Cautionary tool-shed blot myth.")
    parser.add_argument("--name", choices=NAMES)
    parser.add_argument("--animal", choices=ANIMALS)
    parser.add_argument("--elder", choices=ELDERS)
    parser.add_argument("--tool", choices=TOOLS)
    parser.add_argument("--telling", type=int, choices=range(len(TALES)))
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


def emit(sample: StorySample, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world:
        print(dump_trace(sample.world))
    if qa:
        print("\n" + format_qa(sample))


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
            print(json.dumps({"facts": asp_facts(), "models": [str(m) for m in asp.solve(asp_program(), models=1)]}, indent=2))
        except ImportError:
            print(asp_program())
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples = []
    if args.all:
        for i in range(len(TALES)):
            params = StoryParams(
                name=NAMES[i % len(NAMES)],
                animal=ANIMALS[i % len(ANIMALS)],
                elder=ELDERS[i % len(ELDERS)],
                tool=TOOLS[i % len(TOOLS)],
                seed=base_seed + i,
                telling=i,
            )
            samples.append(generate(params))
    else:
        for i in range(args.n):
            rng = random.Random(base_seed + i)
            params = resolve_params(args, rng)
            params.seed = base_seed + i
            samples.append(generate(params))

    if args.json:
        print(json.dumps([s.to_dict() for s in samples] if len(samples) != 1 else samples[0].to_dict(), indent=2, ensure_ascii=False))
        return
    for i, sample in enumerate(samples):
        emit(sample, trace=args.trace, qa=args.qa, header=f"### variant {i + 1}" if len(samples) > 1 else "")
        if i + 1 < len(samples):
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()

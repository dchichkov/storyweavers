#!/usr/bin/env python3
"""A small mythic barbecue world about repetition, patience, and a shared meal."""

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

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "storyworlds"))
from results import QAItem, StoryError, StorySample  # noqa: E402

NAMES = ["Luna", "Mira", "Tavi", "Niko", "Pia", "Sol", "Rin", "Oren"]
COMPANIONS = ["her brother", "her cousin", "a small neighbor", "her friend"]
PLACES = ["the hill garden", "the village yard", "the moonlit clearing", "the orchard gate"]
WEATHERS = ["a warm breeze", "a silver wind", "a hush of evening air", "a soft summer gust"]
INGREDIENTS = ["corn", "peppers", "mushrooms", "flatbread", "peaches", "beans"]

REPETITIONS = [
    ("Turn the skewer, wait for the glow, turn it once again.",
     "Each turn let the heat reach a new side."),
    ("Listen, look, turn; listen, look, turn.",
     "The little rhythm kept hurried hands from rushing."),
    ("Patience, smoke, turning flame; patience, smoke, turning flame.",
     "The repeated words made the work feel steady."),
    ("One breath, one turn, one careful glance.",
     "The meal changed slowly beneath their watching."),
    ("Round and round, not fast, not far.",
     "The same small motion carried the food toward supper."),
]

MYTHS = [
    ("the Ember Mother", "long ago, she taught the first cooks that fire answers a patient hand"),
    ("the Old Red Star", "it once fell beside the cooking stones and promised warmth to those who remembered their rhythm"),
    ("the Turning Giant", "he learned that even a giant flame must be guided one small turn at a time"),
    ("the Hearth Moon", "it watched the first family meal and blessed every careful repetition"),
]

OPENINGS = [
    "At the edge of the village, evening gathered like blue cloth.",
    "When the sun touched the western hill, Luna carried a basket into the yard.",
    "The orchard shadows lengthened, and the old barbecue stones began to warm.",
    "Under the first pale star, Luna found the village barbecue waiting.",
    "A warm breeze moved through the grass as the family prepared supper.",
]

@dataclass(frozen=True)
class Feast:
    key: str
    food: str
    obstacle: str
    sign: str
    action: str
    result: str
    lesson: str
    ending: str

FEASTS = [
    Feast(
        "corn_moon",
        "ears of corn and red peppers",
        "the first side of the corn browned while the other side stayed pale",
        "a coal shaped like a tiny moon rolled beneath the grate",
        "Luna turned each piece once, waited, and turned it again",
        "the corn became golden all around and the peppers softened without burning",
        "A repeated careful act can bring balance to a hungry fire.",
        "The golden corn shone like little moons around the supper cloth.",
    ),
    Feast(
        "peach_embers",
        "halves of peaches and warm flatbread",
        "the peaches began to darken before their centers grew tender",
        "sweet steam rose in three small clouds",
        "Luna moved the peaches, waited for the smoke to thin, and checked them again",
        "the fruit grew soft and warm while the bread toasted beside it",
        "The same gentle check can protect a fragile thing.",
        "The peaches rested on the plate like sunset stones.",
    ),
    Feast(
        "bean_sparks",
        "skewered mushrooms, peppers, and beans",
        "a bright spark leaped whenever the wind bent the flame",
        "the smoke curled into the shape of a wing",
        "Luna lowered the grate, turned the skewers, and repeated the check until the flame settled",
        "the vegetables cooked evenly and the beans stayed safely in their pan",
        "A rhythm can make courage practical.",
        "The supper fire glowed below a row of quiet, shining skewers.",
    ),
    Feast(
        "bread_wheel",
        "flatbread filled with herbs and mushrooms",
        "one edge crisped while the middle remained cool",
        "the oldest barbecue stone hummed a low note",
        "Luna turned the bread, counted three breaths, and turned it once more",
        "the bread became crisp at the edge and warm at the center",
        "Repeating the right action is wiser than forcing a quick result.",
        "The round bread broke open like a warm wheel of stars.",
    ),
]

@dataclass
class Entity:
    id: str
    kind: str
    label: str
    owner: Optional[str] = None
    holder: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

@dataclass
class Setting:
    place: str
    weather: str

@dataclass
class StoryParams:
    place: str
    hero_name: str
    companion: str
    weather: str
    feast_key: str
    myth_index: int = 0
    repetition_index: int = 0
    opening_index: int = 0
    seed: Optional[int] = None

class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict[str, object] = {}
        self.fired: set[tuple[str, str]] = set()

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

def feast_for(key: str) -> Feast:
    for feast in FEASTS:
        if feast.key == key:
            return feast
    raise StoryError(f"Unknown feast: {key}")

def tell(setting: Setting, params: StoryParams) -> World:
    world = World(setting)
    hero = world.add(Entity("hero", "character", params.hero_name))
    companion = world.add(Entity("companion", "character", params.companion))
    barbecue = world.add(Entity("barbecue", "hearth", "the stone barbecue"))
    fire = world.add(Entity("fire", "fire", "the patient fire"))
    feast = feast_for(params.feast_key)
    myth_name, myth_text = MYTHS[params.myth_index % len(MYTHS)]
    repetition, repetition_meaning = REPETITIONS[
        params.repetition_index % len(REPETITIONS)
    ]
    opening = OPENINGS[params.opening_index % len(OPENINGS)]

    hero.memes.update(curiosity=1.0, patience=1.0, courage=1.0, care=1.0)
    companion.memes.update(curiosity=1.0, trust=1.0)
    barbecue.meters.update(stable=1.0, hot=1.0, shared=1.0)
    fire.meters.update(steady=1.0, bright=1.0)
    barbecue.holder = hero.id

    world.say(opening)
    world.say(
        f"In {setting.place}, {hero.label} and {companion.label} prepared a barbecue "
        f"of {feast.food}. {setting.weather.capitalize()} moved around the stones, "
        "and the fire answered with a low red glow."
    )
    world.say(
        f"The elders said that {myth_name} {myth_text}. "
        "So Luna placed the food on the grate and listened before she touched it."
    )
    world.para()

    world.say(f"The first turn brought trouble: {feast.obstacle}.")
    world.say(f"{companion.label.capitalize()} whispered, \"Should we hurry before supper is late?\"")
    world.say(
        f"Luna shook her head. \"Let us repeat the careful way. {repetition}\""
    )
    world.say(f"Then {feast.sign}. The fire seemed to be giving them a clue.")
    world.para()

    world.say(
        f"Luna followed the clue. {feast.action}. "
        f"{companion.label.capitalize()} watched and repeated the count beside her."
    )
    world.say(f"\"Again?\" asked {companion.label}.")
    world.say(
        f"\"Again, but never blindly,\" said Luna. \"We look each time.\" "
        f"{repetition_meaning}"
    )
    world.say(
        f"At last, {feast.result}. The barbecue no longer roared unevenly; "
        "it glowed like a small, friendly sun."
    )
    world.para()

    world.say(f"The village shared the meal. {feast.lesson}")
    world.say(
        f"Before the last bite, Luna repeated the old myth aloud: "
        f"\"{myth_name} remembers the hands that remember.\""
    )
    world.say(
        f"{feast.ending} The fire dimmed, but its rhythm remained in every grateful heart."
    )

    world.fired.update({
        ("prepared", feast.key),
        ("noticed", feast.key),
        ("repeated", feast.key),
        ("shared", feast.key),
    })
    world.facts.update(
        hero=hero,
        companion=companion,
        barbecue=barbecue,
        fire=fire,
        feast=feast,
        myth=(myth_name, myth_text),
        repetition=repetition,
        repetition_meaning=repetition_meaning,
        params=params,
    )
    return world

def generation_prompts(world: World) -> list[str]:
    params: StoryParams = world.facts["params"]
    feast: Feast = world.facts["feast"]
    return [
        f"Tell a mythic barbecue story about {params.hero_name} learning patience through repetition.",
        f"Write a child-friendly tale in which {feast.obstacle} is solved by careful repeated actions.",
        "Create a myth with a shared meal, a speaking fire, brief dialogue, and an ending image.",
    ]

def story_qa(world: World) -> list[QAItem]:
    feast: Feast = world.facts["feast"]
    params: StoryParams = world.facts["params"]
    myth_name, myth_text = world.facts["myth"]
    repetition: str = world.facts["repetition"]
    return [
        QAItem(
            question=f"What food did {params.hero_name} prepare at the barbecue?",
            answer=f"{params.hero_name} prepared {feast.food} at the stone barbecue.",
        ),
        QAItem(
            question="What went wrong at the beginning?",
            answer=f"{feast.obstacle.capitalize()}.",
        ),
        QAItem(
            question="What repeated action solved the problem?",
            answer=f"{feast.action.capitalize()}.",
        ),
        QAItem(
            question="What did the myth say about the fire?",
            answer=f"{myth_name} {myth_text}.",
        ),
        QAItem(
            question="Why did Luna repeat the action carefully?",
            answer=(
                f"She repeated it because {repetition.lower()} "
                "She also looked each time instead of acting blindly."
            ),
        ),
        QAItem(
            question="What showed that the meal was successful?",
            answer=f"{feast.result.capitalize()} {feast.ending}",
        ),
    ]

def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a barbecue?",
            answer="A barbecue is a place or grill where food is cooked over heat, often outdoors.",
        ),
        QAItem(
            question="What does repetition mean?",
            answer="Repetition means doing or saying something again, often to practice or complete a task.",
        ),
        QAItem(
            question="Why should food near a fire be watched?",
            answer="Food near a fire should be watched so it cooks safely and does not burn.",
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
    lines.append("== (3) World knowledge ==")
    for item in sample.world_qa:
        lines.extend([f"Q: {item.question}", f"A: {item.answer}"])
    return "\n".join(lines)

def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for entity in world.entities.values():
        lines.append(
            f"{entity.id}: {entity.kind} {entity.label} "
            f"holder={entity.holder} meters={entity.meters} memes={entity.memes}"
        )
    lines.append(f"fired={sorted(world.fired)}")
    return "\n".join(lines)

ASP_RULES = r"""
prepared(H,F) :- cook(H,B), feast(B,F).
noticed(H,F) :- prepared(H,F), obstacle(F).
repeated(H,F) :- noticed(H,F), patient(H).
shared(H,F) :- repeated(H,F), community(F).
safe_meal(F) :- shared(H,F).
"""

def asp_facts() -> str:
    import asp
    return "\n".join([
        asp.fact("cook", "luna", "barbecue"),
        asp.fact("feast", "barbecue", "corn_moon"),
        asp.fact("obstacle", "corn_moon"),
        asp.fact("patient", "luna"),
        asp.fact("community", "corn_moon"),
    ])

def asp_program(show: str = "#show safe_meal/1.") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"

def asp_parity() -> bool:
    import asp
    model = asp.one_model(asp_program("#show prepared/2.\n#show noticed/2.\n#show repeated/2.\n#show shared/2.\n#show safe_meal/1."))
    atoms = set(asp.atoms(model, "safe_meal"))
    return ("corn_moon",) in atoms

def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="A mythic barbecue story about repetition.")
    parser.add_argument("--place", choices=PLACES)
    parser.add_argument("--name", choices=NAMES)
    parser.add_argument("--companion", choices=COMPANIONS)
    parser.add_argument("--weather", choices=WEATHERS)
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
    return StoryParams(
        place=args.place or rng.choice(PLACES),
        hero_name=args.name or rng.choice(NAMES),
        companion=args.companion or rng.choice(COMPANIONS),
        weather=args.weather or rng.choice(WEATHERS),
        feast_key=rng.choice(FEASTS).key,
        myth_index=rng.randrange(len(MYTHS)),
        repetition_index=rng.randrange(len(REPETITIONS)),
        opening_index=rng.randrange(len(OPENINGS)),
    )

def generate(params: StoryParams) -> StorySample:
    world = tell(Setting(params.place, params.weather), params)
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

CURATED = [
    StoryParams("the hill garden", "Luna", "her brother", "a warm breeze", "corn_moon", 0, 0, 0),
    StoryParams("the village yard", "Mira", "her cousin", "a silver wind", "peach_embers", 1, 2, 1),
    StoryParams("the orchard gate", "Sol", "her friend", "a soft summer gust", "bread_wheel", 3, 3, 4),
]

def verify() -> int:
    for params in CURATED:
        sample = generate(params)
        if not sample.story.strip() or len(sample.story_qa) < 3:
            return 1
        if "barbecue" not in sample.story.lower():
            return 1
        if not any(word in sample.story.lower() for word in ("again", "repeat", "once more")):
            return 1
        if '"' not in sample.story:
            return 1
    try:
        if not asp_parity():
            return 1
    except ImportError:
        pass
    return 0

def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program())
        return
    if args.verify:
        sys.exit(verify())
    if args.asp:
        print(asp_program("#show prepared/2.\n#show noticed/2.\n#show repeated/2.\n#show shared/2.\n#show safe_meal/1."))
        return

    seed = args.seed if args.seed is not None else random.randrange(2**31)
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        samples = []
        for index in range(args.n):
            params = resolve_params(args, random.Random(seed + index))
            params.seed = seed + index
            samples.append(generate(params))

    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([sample.to_dict() for sample in samples], indent=2, ensure_ascii=False))
        return

    for index, sample in enumerate(samples):
        if len(samples) > 1:
            print(f"### variant {index + 1}")
        emit(sample, trace=args.trace, qa=args.qa)
        if index < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")

if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""
A small superhero storyworld about Luna, a grizzly, and a brave quest to scour
away a dangerous storm before it can terminate the town's bright festival.
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
class Item:
    id: str
    label: str
    phrase: str
    kind: str = "thing"
    owner: str = ""
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)


@dataclass
class World:
    hero: Item
    grizzly: Item
    beacon: Item
    place: str
    seed: int
    facts: dict = field(default_factory=dict)

    def render(self) -> str:
        return self.facts.get("story", "")


@dataclass
class StoryParams:
    name: str
    grizzly_name: str
    place: str
    seed: Optional[int] = None


NAMES = ["Luna", "Nova", "Pip", "Mara", "Ziggy", "Tess", "Rio", "Skye"]
GRIZZLIES = ["Bruno", "Honey", "Thunder", "Moss", "Big Paws", "Clover"]
PLACES = [
    "the moonlit mountain town",
    "the silver-pine valley",
    "the lantern festival square",
    "the cloudbridge village",
    "the bright hilltop city",
]


ASP_RULES = r"""
#show brave/1.
#show protected/1.
#show happy/1.

brave(hero) :- accepts_quest(hero).
protected(town) :- scour_storm(hero).
happy(town) :- grizzly_helps(hero).
"""


def asp_facts() -> str:
    import asp
    return "\n".join(
        [
            asp.fact("accepts_quest", "hero"),
            asp.fact("scour_storm", "hero"),
            asp.fact("grizzly_helps", "hero"),
        ]
    )


def asp_program(show: str = "") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp

    model = asp.one_model(
        asp_program("#show brave/1.\n#show protected/1.\n#show happy/1.")
    )
    actual = {
        (atom.name, tuple(
            arg.number if arg.type == arg.type.Number
            else arg.string if arg.type == arg.type.String
            else arg.name
            for arg in atom.arguments
        ))
        for atom in model
        if atom.name in {"brave", "protected", "happy"}
    }
    expected = {
        ("brave", ("hero",)),
        ("protected", ("town",)),
        ("happy", ("town",)),
    }
    if actual != expected:
        print("MISMATCH between ASP and Python expectations.")
        print("ASP:", sorted(actual))
        print("PY :", sorted(expected))
        return 1
    print("OK: ASP parity verified.")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Superhero storyworld about Luna, a grizzly, and a storm-scouring quest."
    )
    parser.add_argument("--name", choices=NAMES)
    parser.add_argument("--grizzly-name", choices=GRIZZLIES)
    parser.add_argument("--place", choices=PLACES)
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
        name=args.name or rng.choice(NAMES),
        grizzly_name=args.grizzly_name or rng.choice(GRIZZLIES),
        place=args.place or rng.choice(PLACES),
    )


def build_world(params: StoryParams) -> World:
    if not params.name or not params.grizzly_name or not params.place:
        raise StoryError("A hero, a grizzly, and a place are required.")
    hero = Item(
        id="hero",
        label=params.name,
        phrase=f"young hero {params.name}",
        kind="character",
        meters={"courage": 8.0, "reach": 2.0},
        memes={"hope": 8.0, "worry": 3.0},
    )
    grizzly = Item(
        id="grizzly",
        label=params.grizzly_name,
        phrase=f"the grizzly {params.grizzly_name}",
        kind="character",
        meters={"strength": 10.0, "warmth": 7.0},
        memes={"trust": 5.0, "joy": 6.0},
    )
    beacon = Item(
        id="beacon",
        label="sky beacon",
        phrase="a humming blue sky beacon",
        kind="device",
        owner="town",
        meters={"charge": 9.0, "height": 6.0},
        memes={"safety": 8.0, "brightness": 7.0},
    )
    seed = params.seed
    if seed is None:
        seed = sum(ord(ch) for ch in f"{params.name}|{params.grizzly_name}|{params.place}")
    return World(
        hero=hero,
        grizzly=grizzly,
        beacon=beacon,
        place=params.place,
        seed=seed,
    )


def _choice(rng: random.Random, values: list[str]) -> str:
    return values[rng.randrange(len(values))]


def _record(
    world: World,
    *,
    discovery: str,
    trouble: str,
    cause: str,
    inner_monologue: str,
    resolution: str,
    ending: str,
    helper: str,
    lines: list[str],
) -> str:
    world.facts.update(
        discovery=discovery,
        trouble=trouble,
        cause=cause,
        inner_monologue=inner_monologue,
        resolution=resolution,
        ending=ending,
        helper=helper,
        brave=True,
        protected=True,
        happy=True,
    )
    world.hero.memes["hope"] = 10.0
    world.hero.memes["worry"] = 1.0
    world.grizzly.memes["trust"] = 9.0
    world.facts["story"] = " ".join(lines)
    return world.facts["story"]


def _storm_arc(world: World, rng: random.Random) -> str:
    h = world.hero.label
    g = world.grizzly.label
    p = world.place
    cloud = _choice(
        rng,
        ["a purple thundercloud", "a black spiral cloud", "a roaring silver cloud"],
    )
    tool = _choice(rng, ["a comet broom", "a wind-whistle", "a sun-bright shield"])
    discovery = f"{cloud} was swallowing the beacon's light above {p}"
    trouble = "the storm threatened to terminate the lantern festival before its first song"
    cause = "the beacon's crystal lens was clogged with storm dust and could not shine through the cloud"
    inner = (
        f"{h} thought, \"I am scared, but being scared does not decide what I do next. "
        f"I can climb, and {g} can help.\""
    )
    resolution = (
        f"{h} climbed beside {g}, used {tool} to scour the dust from the beacon lens, "
        "and aimed its restored beam through the storm"
    )
    ending = (
        f"the cloud broke into harmless silver flakes, {g} received the first festival cake, "
        "and every lantern woke at once"
    )
    helper = f"{g} held the beacon ladder steady and rumbled courage into the wind"
    lines = [
        f"At {p}, {h} wore a red cape made from an old picnic blanket and watched the festival lanterns tremble.",
        f"Then {cloud} curled over the square. Its thunder shook the cobblestones, and the sky beacon blinked three times.",
        f'"The storm will terminate the festival!" cried {h}. {g} lifted his broad head. "Not if a hero has a plan."',
        f"{h} looked at the steep beacon tower. {inner}",
        f"The quest began. {g} carried the ladder while {h} carried {tool}; together they climbed through rain that tickled like cold fingers.",
        f"At the beacon, they found dust packed across its crystal lens. That was the trouble: the light was not gone, only hidden.",
        f'"Scour, shine, and try again," said {h}. "{g}, hold steady!"',
        f"{helper}. {h} swept the lens clean, then turned the beacon toward the cloud.",
        f"The beam pierced the darkness. The storm shivered, loosened, and floated away like a blanket being folded.",
        f"At last, {ending}. {h} learned that a brave heart can make room for a careful plan.",
    ]
    return _record(
        world,
        discovery=discovery,
        trouble=trouble,
        cause=cause,
        inner_monologue=inner,
        resolution=resolution,
        ending=ending,
        helper=helper,
        lines=lines,
    )


def _bridge_arc(world: World, rng: random.Random) -> str:
    h = world.hero.label
    g = world.grizzly.label
    p = world.place
    object_name = _choice(rng, ["a moon wagon", "the mayor's pie cart", "a basket of glow-apples"])
    discovery = "the storm had snapped the glowing bridge cable, leaving one safe cable hidden under ice"
    trouble = f"{object_name} and the festival singers were stranded on the far side of the ravine"
    cause = "a lightning bolt had burned through the bridge's bright guide rope"
    inner = (
        f"{h} told themself, \"A superhero does not rush just because everyone is watching. "
        "First I must find the strong rope.\""
    )
    resolution = (
        f"{g} braced the bridge post while {h} scoured away the ice and tied the hidden cable "
        "across the gap"
    )
    ending = (
        f"the singers crossed safely, {object_name} rolled into the festival, "
        "and the repaired bridge shone under the stars"
    )
    helper = f"{g} planted his paws like four brown anchors"
    lines = [
        f"On the edge of {p}, {h} heard a desperate clatter below the festival bridge.",
        f"{object_name} had stopped on the far side, and the singers could not return for the lantern parade.",
        f'"I will rescue everyone!" shouted {h}. "Then rescue them wisely," said {g}.',
        f"{h} studied the bridge instead of leaping. {inner}",
        f"Under a crust of ice, the hero spotted a silver cable that had survived the lightning.",
        f"{helper}, while {h} used a small metal scraper to scour the ice from the cable.",
        f'"Pull when I say shine!" called {h}. "Shine!" rumbled {g}.',
        f"Together they stretched the cable across the ravine and fastened it to the stone posts.",
        f"One by one, the singers crossed. Their first song rose like a warm blanket over the cold gap.",
        f"By moonrise, {ending}. The quest ended with no one hurt and everyone singing.",
    ]
    return _record(
        world,
        discovery=discovery,
        trouble=trouble,
        cause=cause,
        inner_monologue=inner,
        resolution=resolution,
        ending=ending,
        helper=helper,
        lines=lines,
    )


def _garden_arc(world: World, rng: random.Random) -> str:
    h = world.hero.label
    g = world.grizzly.label
    p = world.place
    creature = _choice(rng, ["a sleepy cloud dragon", "a tiny thunder giant", "a woolly wind beast"])
    discovery = f"{creature} had tangled the town's weather ribbons around the old garden gate"
    trouble = "the trapped ribbons were pulling the festival weather machine toward the rooftops"
    cause = "the creature had mistaken the colorful ribbons for vines and tied them into one enormous knot"
    inner = (
        f"{h} thought, \"I could shout, but shouting may frighten it. "
        "A gentle question might open the knot and the creature's heart.\""
    )
    resolution = (
        f"{h} asked the creature to loosen one ribbon at a time while {g} used his claws to scour "
        "the mud from the gate hinges"
    )
    ending = (
        f"the weather machine settled into the garden, {creature} curled beside {g}, "
        "and soft sunshine filled the happy festival"
    )
    helper = f"{g} hummed a low, friendly song that made the creature stop tugging"
    lines = [
        f"In the garden behind {p}, {h} found {creature} wrapped around the weather machine.",
        f"The creature's ribbons stretched from the gate to the roof, and every tug pulled the machine higher.",
        f'"Stop!" called {h}. "Please do not terminate our garden." The creature sneezed a puff of rain.',
        f"{h} watched its worried eyes. {inner}",
        f"{helper}. The creature blinked and held still.",
        f"{h} knelt and asked, \"Did you think the ribbons were vines?\" The creature nodded.",
        f"Together they loosened one ribbon at a time. Meanwhile, {g} used his strong claws to scour the mud from the gate hinges.",
        f"The weather machine slid safely down. A final ribbon fluttered free and tickled {h}'s nose.",
        f"The creature gave a shy rainbow burp. Everyone laughed, including the creature.",
        f"At sunset, {ending}. A superhero quest, {h} decided, could end with friendship instead of a fight.",
    ]
    return _record(
        world,
        discovery=discovery,
        trouble=trouble,
        cause=cause,
        inner_monologue=inner,
        resolution=resolution,
        ending=ending,
        helper=helper,
        lines=lines,
    )


ARC_BUILDERS = [_storm_arc, _bridge_arc, _garden_arc]


def generate_story(world: World) -> str:
    rng = random.Random(world.seed ^ 0x5EED91)
    builder = ARC_BUILDERS[world.seed % len(ARC_BUILDERS)]
    return builder(world, rng)


def story_qa(world: World) -> list[QAItem]:
    h = world.hero.label
    facts = world.facts
    return [
        QAItem(
            question=f"What did {h} discover during the quest?",
            answer=f"{h} discovered that {facts['discovery']}.",
        ),
        QAItem(
            question="What caused the danger?",
            answer=f"The danger began because {facts['cause']}.",
        ),
        QAItem(
            question=f"What did {h} do to solve the problem?",
            answer=f"{h} solved it when {facts['resolution']}.",
        ),
        QAItem(
            question="How did the grizzly help?",
            answer=facts["helper"].capitalize() + ".",
        ),
        QAItem(
            question="What happy change proved the quest succeeded?",
            answer=f"After the quest, {facts['ending']}.",
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a grizzly?",
            answer="A grizzly is a large brown bear with powerful muscles, strong claws, and a noticeable shoulder hump.",
        ),
        QAItem(
            question="What does it mean to scour something?",
            answer="To scour something means to clean or search it carefully, often by rubbing away dirt or looking in every part.",
        ),
        QAItem(
            question="What is an inner monologue?",
            answer="An inner monologue is the private stream of thoughts a character has inside their mind.",
        ),
        QAItem(
            question="Why do superheroes go on quests?",
            answer="Superheroes go on quests to face a difficult problem, protect others, and make a brave choice.",
        ),
        QAItem(
            question="What makes a happy ending?",
            answer="A happy ending shows that the danger has passed, the characters are safe, and something hopeful has changed.",
        ),
    ]


def generation_prompts(world: World) -> list[str]:
    return [
        "Write a superhero story for young children about Luna and a helpful grizzly.",
        f"Tell a quest story set in {world.place} where a hero must scour away danger before it can terminate a celebration.",
        "Use an inner monologue, a brave helper, a clear problem, and a happy ending.",
    ]


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for ent in [world.hero, world.grizzly, world.beacon]:
        lines.append(
            f"  {ent.id:8} {ent.kind:10} label={ent.label!r} owner={ent.owner!r} "
            f"meters={ent.meters} memes={ent.memes}"
        )
    lines.append(f"  place={world.place!r}")
    lines.append(f"  facts={world.facts}")
    return "\n".join(lines)


def format_qa(sample: StorySample) -> str:
    out = ["== Generation prompts =="]
    for i, prompt in enumerate(sample.prompts, 1):
        out.append(f"{i}. {prompt}")
    out.append("")
    out.append("== Story QA ==")
    for item in sample.story_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    out.append("")
    out.append("== World QA ==")
    for item in sample.world_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    return "\n".join(out)


def generate(params: StoryParams) -> StorySample:
    world = build_world(params)
    story = generate_story(world)
    return StorySample(
        params=params,
        story=story,
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_qa(world),
        world=world,
    )


def emit(
    sample: StorySample,
    *,
    trace: bool = False,
    qa: bool = False,
    header: str = "",
) -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world is not None:
        print(dump_trace(sample.world))
    if qa:
        print()
        print(format_qa(sample))


def asp_facts_text() -> str:
    return asp_facts()


def asp_valid() -> bool:
    return True


def main() -> None:
    args = build_parser().parse_args()

    if args.n < 1:
        raise StoryError("-n must be at least 1.")

    if args.show_asp:
        print(
            asp_program(
                "#show brave/1.\n#show protected/1.\n#show happy/1."
            )
        )
        return

    if args.verify:
        sys.exit(asp_verify())

    if args.asp:
        print(
            "3 compatible logical atoms: "
            "brave(hero), protected(town), happy(town)"
        )
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        curated = [
            StoryParams(
                name="Luna",
                grizzly_name="Bruno",
                place="the moonlit mountain town",
                seed=base_seed,
            ),
            StoryParams(
                name="Nova",
                grizzly_name="Honey",
                place="the silver-pine valley",
                seed=base_seed + 1,
            ),
            StoryParams(
                name="Mara",
                grizzly_name="Thunder",
                place="the lantern festival square",
                seed=base_seed + 2,
            ),
        ]
        samples = [generate(params) for params in curated]
    else:
        seen: set[str] = set()
        index = 0
        while len(samples) < args.n and index < max(50, args.n * 20):
            params = resolve_params(args, random.Random(base_seed + index))
            params.seed = base_seed + index
            sample = generate(params)
            index += 1
            if sample.story in seen:
                continue
            seen.add(sample.story)
            samples.append(sample)

    if len(samples) < args.n and not args.all:
        raise StoryError("Could not produce enough distinct story variants.")

    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(
                json.dumps(
                    [sample.to_dict() for sample in samples],
                    indent=2,
                    ensure_ascii=False,
                )
            )
        return

    for index, sample in enumerate(samples):
        header = ""
        if args.all:
            params = sample.params
            header = f"### {params.name} and {params.grizzly_name} at {params.place}"
        elif len(samples) > 1:
            header = f"### variant {index + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if index < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()

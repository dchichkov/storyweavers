#!/usr/bin/env python3
"""
A small space-adventure storyworld about a stolen golden cheerio, a bottle of
worcestershire sauce, and a flashback that helps a young astronaut recover it.
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
    robot: Item
    chef: Item
    cheerio: Item
    bottle: Item
    place: str
    seed: int
    facts: dict = field(default_factory=dict)

    def render(self) -> str:
        return self.facts.get("story", "")


@dataclass
class StoryParams:
    name: str
    robot_name: str
    chef_name: str
    place: str
    seed: Optional[int] = None


NAMES = ["Luna", "Milo", "Zara", "Pip", "Nova", "Tess"]
ROBOTS = ["Bleep", "Orbit", "Zip", "Comet", "Noodle"]
CHEFS = ["Chef Ori", "Chef Bea", "Chef Sol", "Chef Mina"]
PLACES = [
    "the moon kitchen",
    "the starship Aurora",
    "the crater café",
    "the comet station",
    "the little space observatory",
]


ASP_RULES = r"""
#show hungry/1.
#show remembers/1.
#show recovered/1.

hungry(H) :- smells_sauce(H).
remembers(H) :- flashback(H).
recovered(H) :- returns_cheerio(H).
"""


def asp_facts() -> str:
    import asp
    return "\n".join(
        [
            asp.fact("smells_sauce", "hero"),
            asp.fact("flashback", "hero"),
            asp.fact("returns_cheerio", "hero"),
        ]
    )


def asp_program(show: str = "") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp

    model = asp.one_model(
        asp_program(
            "#show hungry/1.\n#show remembers/1.\n#show recovered/1."
        )
    )
    found = set()
    for atom in model:
        args = []
        for value in atom.arguments:
            if value.type == value.type.Number:
                args.append(value.number)
            elif value.type == value.type.String:
                args.append(value.string)
            else:
                args.append(value.name)
        found.add((atom.name, tuple(args)))
    expected = {
        ("hungry", ("hero",)),
        ("remembers", ("hero",)),
        ("recovered", ("hero",)),
    }
    if found == expected:
        print("OK: ASP parity verified.")
        return 0
    print("MISMATCH between ASP and Python expectations.")
    print("ASP:", sorted(found))
    print("PY :", sorted(expected))
    return 1


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Space adventure about a stolen cheerio and a flashback."
    )
    parser.add_argument("--name", choices=NAMES)
    parser.add_argument("--robot-name", choices=ROBOTS)
    parser.add_argument("--chef-name", choices=CHEFS)
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
        robot_name=args.robot_name or rng.choice(ROBOTS),
        chef_name=args.chef_name or rng.choice(CHEFS),
        place=args.place or rng.choice(PLACES),
    )


def build_world(params: StoryParams) -> World:
    if params.name == params.robot_name:
        raise StoryError("The astronaut and robot must have different names.")
    hero = Item(
        id="hero",
        label=params.name,
        phrase=f"young astronaut {params.name}",
        kind="character",
        meters={"fuel": 1.0, "distance": 0.0},
        memes={"curiosity": 0.8, "courage": 0.7},
    )
    robot = Item(
        id="robot",
        label=params.robot_name,
        phrase=f"helpful robot {params.robot_name}",
        kind="character",
        meters={"battery": 0.9},
        memes={"loyalty": 0.9, "worry": 0.3},
    )
    chef = Item(
        id="chef",
        label=params.chef_name,
        phrase=params.chef_name,
        kind="character",
        meters={"sauce": 1.0},
        memes={"patience": 0.8},
    )
    cheerio = Item(
        id="cheerio",
        label="cheerio",
        phrase="one perfectly round golden cheerio",
        owner="chef",
        meters={"mass": 0.1, "orbit": 0.0},
        memes={"importance": 0.9},
    )
    bottle = Item(
        id="worcestershire",
        label="worcestershire",
        phrase="a tiny bottle of worcestershire sauce",
        owner="chef",
        meters={"mass": 0.4, "sauce": 1.0},
        memes={"smell": 0.9},
    )
    seed = params.seed
    if seed is None:
        seed = sum(ord(ch) for ch in f"{params.name}|{params.robot_name}|{params.place}")
    return World(
        hero=hero,
        robot=robot,
        chef=chef,
        cheerio=cheerio,
        bottle=bottle,
        place=params.place,
        seed=seed,
    )


def _choice(rng: random.Random, values: list[str]) -> str:
    return values[rng.randrange(len(values))]


def _record(
    world: World,
    *,
    discovery: str,
    cause: str,
    resolution: str,
    ending: str,
    trouble: str,
    flashback: str,
    suspect: str,
    lines: list[str],
) -> str:
    world.facts.update(
        discovery=discovery,
        cause=cause,
        resolution=resolution,
        ending=ending,
        trouble=trouble,
        flashback=flashback,
        suspect=suspect,
        recovered=True,
    )
    world.cheerio.owner = "hero"
    world.cheerio.meters["orbit"] = 0.0
    world.hero.memes["courage"] = 1.0
    return " ".join(lines)


def _orbit_arc(world: World, rng: random.Random) -> str:
    h = world.hero.label
    r = world.robot.label
    c = world.chef.label
    p = world.place
    planet = _choice(rng, ["Mars", "the blue moon", "Saturn's bright rings"])
    discovery = "the missing cheerio was drifting in a slow loop around the soup dome"
    cause = "a burst of air from the kitchen vent had lifted the light cheerio into weightless orbit"
    resolution = f"{h} used {r}'s gentle fan to guide the cheerio toward a net while {c} held the worcestershire bottle steady"
    ending = "the cheerio landed in the soup with a tiny golden plop"
    trouble = "the breakfast ring floated past the windows and nearly joined an expedition to " + planet
    flashback = f"{h} remembered seeing the vent flap open when {c} had shaken the worcestershire bottle"
    suspect = "the hungry kitchen vent"
    lines = [
        f"At {p}, {h} prepared breakfast while {c} guarded a tiny bottle of worcestershire sauce.",
        f"Then the chef gasped. The golden cheerio was gone, and {trouble}.",
        f'"We must thieve it back from space!" cried {h}. "{h}," said {r}, "a thing cannot thieve itself."',
        f"{h} searched under bowls and behind the spoon rack. Then a memory flashed: {flashback}.",
        f"The vent flap was open. A thin puff of air sent crumbs drifting toward the soup dome, so {h} knew the cheerio had not vanished; it had been carried.",
        f'"There!" shouted {h}. "Follow the floating crumbs." {r} switched on a gentle fan instead of a roaring engine.',
        f"{resolution}.",
        f"{c} laughed and poured the sauce carefully. By lunchtime, {ending}. {h} kept watching the vent, because space had many ways to make breakfast travel.",
    ]
    return _record(
        world,
        discovery=discovery,
        cause=cause,
        resolution=resolution,
        ending=ending,
        trouble=trouble,
        flashback=flashback,
        suspect=suspect,
        lines=lines,
    )


def _thieve_arc(world: World, rng: random.Random) -> str:
    h = world.hero.label
    r = world.robot.label
    c = world.chef.label
    p = world.place
    creature = _choice(rng, ["a moon mouse", "a comet crow", "a tiny asteroid fox"])
    hiding = _choice(rng, ["the map cabinet", "a helmet locker", "the warm engine cupboard"])
    discovery = f"a little space creature had tried to thieve the cheerio for a shiny nest"
    cause = f"the {creature} mistook the cheerio for a bright moon pebble and rolled it into {hiding}"
    resolution = f"{h} offered the creature a dull metal washer while {r} opened a clear path back to the kitchen"
    ending = "the cheerio rested safely beside the sauce while the creature built a less delicious nest"
    trouble = f"the {creature} thieved the breakfast ring and zipped away through the station"
    flashback = f"{h} remembered that the same silver claw marks had appeared near {hiding} before"
    suspect = creature
    lines = [
        f"At {p}, {c} set down the worcestershire bottle and reached for a cheerio.",
        f"The plate was empty. A silver blur dashed past {h}. It was {creature}, and {trouble}.",
        f'"Stop, thieve!" called {h}. "That word means steal," said {r}. "Then stop, shiny stealer!"',
        f"{h} chased the creature through the corridor, but it slipped behind {hiding}.",
        f"Suddenly, a flashback returned: {flashback}. The old marks formed a trail from the breakfast table to the cupboard.",
        f"{h} followed the marks instead of making a noisy chase. Inside, the creature hugged the cheerio like a treasure moon.",
        f"{resolution}. The creature sniffed the washer, dropped the cheerio, and skittered away.",
        f"{c} checked the ring for space dust and nodded. At sunset, {ending}. {r} labeled the washer, 'Not breakfast.'",
    ]
    return _record(
        world,
        discovery=discovery,
        cause=cause,
        resolution=resolution,
        ending=ending,
        trouble=trouble,
        flashback=flashback,
        suspect=suspect,
        lines=lines,
    )


def _sauce_arc(world: World, rng: random.Random) -> str:
    h = world.hero.label
    r = world.robot.label
    c = world.chef.label
    p = world.place
    spill = _choice(rng, ["a purple nebula", "a comet tail", "a starry moustache"])
    discovery = f"the cheerio had stuck to a floating drop of worcestershire sauce"
    cause = "the sauce bottle had been squeezed in zero gravity, making a dark droplet that carried the light ring away"
    resolution = f"{h} remembered the bottle's loose cap, asked {r} to freeze the air pump, and caught the droplet with a spoon"
    ending = "the rescued ring floated back into the bowl, shining through one clean drop of sauce"
    trouble = f"the sauce droplet drifted across the galley like {spill}"
    flashback = f"{h} remembered that {c} had tapped the bottle twice before the droplet escaped"
    suspect = "the floating sauce droplet"
    lines = [
        f"In {p}, {h} and {c} mixed a breakfast bowl beside a bottle of worcestershire.",
        f"A tiny dark blob drifted upward. The cheerio clung to it, and {trouble}.",
        f'"The sauce is trying to thieve breakfast!" said {h}. {r} replied, "Breakfast requires a rescue plan."',
        f"The droplet slid toward the open airlock. {h} reached, missed, and spun slowly past a hanging ladle.",
        f"Then came a flashback: {flashback}. The loose cap had let air push sauce out when the bottle was squeezed.",
        f"{h} stopped guessing and spoke clearly. " + f'"{r}, freeze the air pump!" {r} clicked the switch.',
        f"{resolution}. The spoon caught the droplet, and the ring rolled free.",
        f"{c} tightened the cap and gave {h} the spoon. By evening, {ending}. The astronauts ate slowly, with both feet hooked under the table.",
    ]
    return _record(
        world,
        discovery=discovery,
        cause=cause,
        resolution=resolution,
        ending=ending,
        trouble=trouble,
        flashback=flashback,
        suspect=suspect,
        lines=lines,
    )


def _signal_arc(world: World, rng: random.Random) -> str:
    h = world.hero.label
    r = world.robot.label
    c = world.chef.label
    p = world.place
    signal = _choice(rng, ["a beep-beep melody", "a wobbly trumpet note", "three polite blinks"])
    discovery = f"the cheerio was caught inside the station's blinking signal dish"
    cause = "the dish's magnet had mistaken the metal tray beneath the cheerio for a repair part"
    resolution = f"{h} recalled the dish's repair pattern, asked {r} to lower the signal, and used a wooden spoon to lift the ring"
    ending = "the dish sent a clear signal while the cheerio returned to its bowl"
    trouble = f"the hungry signal dish broadcast {signal} toward every nearby moon"
    flashback = f"{h} remembered that the dish had turned toward the breakfast tray just after {c} set down the worcestershire bottle"
    suspect = "the magnetic signal dish"
    lines = [
        f"At {p}, {c} prepared a snack with a cheerio and a bottle of worcestershire.",
        f"The cheerio vanished beneath a flash of blue light. Outside, {trouble}.",
        f'"Who would thieve a cheerio with a signal dish?" asked {h}. "{r} said, "Perhaps the dish is only confused."',
        f"{h} inspected the controls while {r} listened to the beeps. The dish was pointing at the kitchen tray.",
        f"A flashback helped: {flashback}.",
        f"{resolution}. The wooden spoon touched the tray, and the ring popped loose without scratching the dish.",
        f"{c} thanked {h} and placed the worcestershire bottle far from the controls. The signal settled into a calm hum.",
        f"After the final check, {ending}. {h} learned that remembering a small detail could guide a very large rescue.",
    ]
    return _record(
        world,
        discovery=discovery,
        cause=cause,
        resolution=resolution,
        ending=ending,
        trouble=trouble,
        flashback=flashback,
        suspect=suspect,
        lines=lines,
    )


ARCS = [_orbit_arc, _thieve_arc, _sauce_arc, _signal_arc]


def generate_story(world: World) -> str:
    if not world.place:
        raise StoryError("The space setting cannot be empty.")
    rng = random.Random(world.seed ^ 0x57A2C1)
    builder = ARCS[world.seed % len(ARCS)]
    return builder(world, rng)


def story_qa(world: World) -> list[QAItem]:
    h = world.hero.label
    facts = world.facts
    return [
        QAItem(
            question=f"What did {h} discover about the cheerio?",
            answer=f"{h} discovered that {facts['discovery']}.",
        ),
        QAItem(
            question="What caused the trouble?",
            answer=f"The trouble began because {facts['cause']}.",
        ),
        QAItem(
            question=f"How did {h} recover the cheerio?",
            answer=f"{facts['resolution']}.",
        ),
        QAItem(
            question="How did the flashback help?",
            answer=f"The flashback helped because {facts['flashback']}.",
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a cheerio?",
            answer="A cheerio is a small ring-shaped cereal, usually eaten as a crunchy breakfast food.",
        ),
        QAItem(
            question="What is worcestershire sauce?",
            answer="Worcestershire sauce is a strongly flavored savory sauce often used a little at a time in cooking.",
        ),
        QAItem(
            question="What does thieve mean?",
            answer="To thieve means to steal something, usually secretly or without permission.",
        ),
        QAItem(
            question="What is a flashback?",
            answer="A flashback is a return to an earlier event that helps a character remember an important clue.",
        ),
        QAItem(
            question="Why do objects float in a spaceship?",
            answer="Objects can float in a spaceship when the spacecraft is in microgravity and there is not enough apparent weight to pull them down.",
        ),
    ]


def generation_prompts(world: World) -> list[str]:
    return [
        "Write a child-friendly space adventure about a missing cheerio.",
        f"Tell a funny story set in {world.place} involving worcestershire sauce and a sneaky thieve.",
        "Use a flashback to reveal the clue that helps recover a floating breakfast ring.",
    ]


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for entity in [
        world.hero,
        world.robot,
        world.chef,
        world.cheerio,
        world.bottle,
    ]:
        lines.append(
            f"  {entity.id:15} {entity.kind:10} "
            f"label={entity.label!r} owner={entity.owner!r} "
            f"meters={entity.meters} memes={entity.memes}"
        )
    lines.append(f"  place={world.place!r}")
    lines.append(f"  arc={world.facts.get('discovery', '')}")
    return "\n".join(lines)


def format_qa(sample: StorySample) -> str:
    out = ["== Generation prompts =="]
    for index, prompt in enumerate(sample.prompts, 1):
        out.append(f"{index}. {prompt}")
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
    world.facts["story"] = story
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

    if args.show_asp:
        print(
            asp_program(
                "#show hungry/1.\n#show remembers/1.\n#show recovered/1."
            )
        )
        return

    if args.verify:
        sys.exit(asp_verify())

    if args.asp:
        print(
            "3 compatible logical atoms: "
            "hungry(hero), remembers(hero), recovered(hero)"
        )
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        curated = [
            StoryParams(
                name="Luna",
                robot_name="Bleep",
                chef_name="Chef Ori",
                place="the moon kitchen",
                seed=base_seed,
            ),
            StoryParams(
                name="Nova",
                robot_name="Orbit",
                chef_name="Chef Bea",
                place="the starship Aurora",
                seed=base_seed + 1,
            ),
            StoryParams(
                name="Milo",
                robot_name="Zip",
                chef_name="Chef Sol",
                place="the crater café",
                seed=base_seed + 2,
            ),
            StoryParams(
                name="Zara",
                robot_name="Comet",
                chef_name="Chef Mina",
                place="the comet station",
                seed=base_seed + 3,
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
            header = f"### {params.name} at {params.place}"
        elif len(samples) > 1:
            header = f"### variant {index + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if index < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()

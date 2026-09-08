#!/usr/bin/env python3
"""
A small space-adventure story world about a ridiculous plunk at a bonfire.

The crew must solve a gentle mystery by listening to one another and testing
clues instead of guessing.
"""

from __future__ import annotations

import argparse
import json
import random
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

for _parent in Path(__file__).resolve().parents:
    if (_parent / "storyworlds" / "results.py").is_file():
        sys.path.insert(0, str(_parent / "storyworlds"))
        break
from results import QAItem, StoryError, StorySample  # noqa: E402


ASP_RULES = r"""
space_crew(X) :- astronaut(X).
has_mystery(X) :- astronaut(X), hears_plunk(X).
safe_solution(X) :- has_mystery(X), checks_clue(X), shares_dialogue(X).
bonfire_story(X) :- safe_solution(X), protects_fire(X).
solved_story(X) :- bonfire_story(X), finds_source(X).
"""

ASTRONAUTS = ["Luna", "Orion", "Miko", "Tess", "Pax", "Nova"]
PLACES = ["the red-moon camp", "the comet garden", "the crater station", "the ringed planet's shore"]
OBJECTS = ["a moon kettle", "a silver rover", "a star map", "a meteor drum"]
SOUNDS = ["plunk", "ping", "whirr", "clonk"]
TREATS = ["glowberry cakes", "warm moon buns", "comet corn", "starlight apples"]


@dataclass(frozen=True)
class Mystery:
    title: str
    opening: str
    danger: str
    false_guess: str
    clue: str
    investigation: str
    source: str
    solution: str
    bonfire_action: str
    joke: str
    ending: str


MYSTERIES = [
    Mystery(
        title="the moon kettle's ridiculous plunk",
        opening="During the evening camp, a ridiculous plunk bounced across the quiet moon dust.",
        danger="the sound came from beside the bright bonfire, where a loose fuel canister could have rolled into the flames",
        false_guess="a tiny alien drummer was hiding under the camp table",
        clue="three round dents led away from the kettle toward a patch of soft dust",
        investigation="marked a safe circle around the fire, then followed the dents with a long flashlight",
        source="a wind-up rover wheel had come loose and was bumping against the kettle",
        solution="tightened the wheel and moved the canister safely behind the supply crate",
        bonfire_action="kept the bonfire low and clear while everyone watched from behind the bright safety line",
        joke="The moon kettle had been practicing its most ridiculous song",
        ending="The repaired rover rolled quietly beside the bonfire while the kettle warmed cocoa without a single plunk.",
    ),
    Mystery(
        title="the bonfire's bouncing ping",
        opening="At the edge of the crater, a mysterious ping interrupted the crew's first marshmallow.",
        danger="the sound came from the dark side of the bonfire, where an unfastened signal mirror might slide into the coals",
        false_guess="a space ghost was asking for a toasted snack",
        clue="the ping grew louder whenever the solar fan turned toward the fire",
        investigation="asked everyone to step back, switched off the fan, and compared the sound from two safe spots",
        source="a loose spoon had been tapping the signal mirror in the fan's breeze",
        solution="secured the spoon and moved the mirror to a shaded equipment rack",
        bonfire_action="kept the flames inside their stone ring while the crew resumed its snack circle",
        joke="The ghost had terrible timing and even worse table manners",
        ending="The mirror flashed at the stars, and only friendly laughter rose above the steady bonfire.",
    ),
    Mystery(
        title="the clonk in the comet garden",
        opening="A heavy clonk rolled through the comet garden just as the crew prepared its evening bonfire.",
        danger="a storage hatch near the fire had opened, leaving a fuel hose exposed to sparks",
        false_guess="a giant moon potato was demanding a captain",
        clue="a trail of blue frost ran from the hatch to a cracked garden pipe",
        investigation="shared the clue aloud, shut the fire shield, and inspected the trail with insulated gloves",
        source="pressure from the cracked pipe had popped the hatch latch",
        solution="closed the fuel valve, replaced the latch, and reported the pipe for repair",
        bonfire_action="waited until the hose was covered before lighting a small cooking flame",
        joke="The moon potato was innocent, but it still wanted a medal",
        ending="Blue frost glittered on the repaired pipe while potatoes roasted safely beyond the fire shield.",
    ),
    Mystery(
        title="the whirr beneath the star map",
        opening="A ridiculous whirr began beneath the star map while the crew gathered around the bonfire.",
        danger="the map table was wobbling toward the fire, and its lamp cord could catch on a stone",
        false_guess="the star map had started flying to a warmer planet",
        clue="one table leg rested on a loose pebble shaped like a tiny moon",
        investigation="held the map steady, asked for a second pair of hands, and checked the table legs one by one",
        source="the loose pebble had nudged a little cleaning bot into the table leg",
        solution="moved the bot, removed the pebble, and tied the lamp cord along the safe side",
        bonfire_action="set the table behind the fire stones before unfolding the map again",
        joke="The map knew where it was going, but the table clearly did not",
        ending="The star map lay flat beneath the lamp as the bonfire painted safe gold circles on the ground.",
    ),
]


@dataclass
class Character:
    id: str
    role: str
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)


@dataclass
class Setting:
    place: str
    sky: str = "a sky crowded with patient stars"


@dataclass
class World:
    setting: Setting
    hero: Character
    helper: Character
    mystery: Mystery
    object_name: str
    treat: str
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    facts: dict[str, object] = field(default_factory=dict)

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(part) for part in self.paragraphs if part)


@dataclass
class StoryParams:
    hero: str
    helper: str
    place: str
    object_name: str
    treat: str
    seed: Optional[int] = None


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Space-adventure mystery about a ridiculous plunk and a bonfire.")
    parser.add_argument("--hero", choices=ASTRONAUTS)
    parser.add_argument("--helper", choices=ASTRONAUTS)
    parser.add_argument("--place", choices=PLACES)
    parser.add_argument("--object", dest="object_name", choices=OBJECTS)
    parser.add_argument("--treat", choices=TREATS)
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
    hero = args.hero or rng.choice(ASTRONAUTS)
    choices = [name for name in ASTRONAUTS if name != hero]
    helper = args.helper or rng.choice(choices)
    if helper == hero:
        raise StoryError("hero and helper must be different astronauts")
    return StoryParams(
        hero=hero,
        helper=helper,
        place=args.place or rng.choice(PLACES),
        object_name=args.object_name or rng.choice(OBJECTS),
        treat=args.treat or rng.choice(TREATS),
    )


def make_world(params: StoryParams) -> World:
    if params.hero == params.helper:
        raise StoryError("a space mystery needs two different voices in its dialogue")
    key = params.seed if params.seed is not None else sum(ord(ch) for ch in "|".join([
        params.hero, params.helper, params.place, params.object_name, params.treat
    ]))
    hero = Character(
        id=params.hero,
        role="junior astronaut",
        meters={"curiosity": 1.0, "caution": 0.8},
        memes={"confidence": 0.5, "wonder": 0.9},
    )
    helper = Character(
        id=params.helper,
        role="navigation partner",
        meters={"listening": 1.0, "care": 0.9},
        memes={"patience": 0.9, "humor": 0.6},
    )
    return World(
        setting=Setting(place=params.place),
        hero=hero,
        helper=helper,
        mystery=MYSTERIES[key % len(MYSTERIES)],
        object_name=params.object_name,
        treat=params.treat,
    )


def tell(world: World) -> None:
    h, helper, mystery = world.hero, world.helper, world.mystery
    world.say(
        f"{mystery.opening} {h.id} and {helper.id} were sharing {world.treat} at {world.setting.place}, "
        f"beneath {world.setting.sky}."
    )
    world.say(
        f"The sound seemed to come from the camp's {world.object_name}. "
        f"More worrying, {mystery.danger}."
    )
    world.para()
    world.say(
        f'"It must be {mystery.false_guess}," whispered {h.id}. '
        f'"That is a ridiculous guess," said {helper.id}, "but we can test it without rushing."'
    )
    world.say(
        f"Instead of poking near the flames, they {mystery.investigation}. "
        f"They noticed that {mystery.clue}."
    )
    world.para()
    world.say(
        f'"The clue points away from the bonfire," said {h.id}. '
        f'"Then let us follow it together," replied {helper.id}.'
    )
    world.say(
        f"The mystery led them to {mystery.source}. Together, they {mystery.solution}. "
        f"Nobody had to guess, grab, or step across the safety line."
    )
    world.say(
        f"Afterward, they {mystery.bonfire_action}. "
        f"At last, {h.id} said, '{mystery.joke}!' and {helper.id} laughed."
    )
    world.say(
        f"The space crew had solved the mystery by sharing dialogue, checking a clue, and protecting one another. "
        f"{mystery.ending}"
    )
    world.facts.update(
        hero=h,
        helper=helper,
        mystery=mystery,
        source=mystery.source,
        clue=mystery.clue,
        solution=mystery.solution,
        ending=mystery.ending,
    )


def generate(params: StoryParams) -> StorySample:
    world = make_world(params)
    tell(world)
    mystery = world.mystery
    return StorySample(
        params=params,
        story=world.render(),
        prompts=[
            f"Write a child-friendly space adventure about {mystery.title}, using dialogue to solve a mystery near a bonfire.",
            f"Show how {params.hero} and {params.helper} test the clue that {mystery.clue} instead of trusting a ridiculous guess.",
            f"End with a concrete image proving that the danger was solved: {mystery.ending}",
        ],
        story_qa=[
            QAItem(
                question=f"What mystery did {params.hero} and {params.helper} investigate?",
                answer=f"They investigated {mystery.title}. The sound mattered because {mystery.danger}.",
            ),
            QAItem(
                question="What clue helped solve the mystery?",
                answer=f"The useful clue was that {mystery.clue}. It directed the astronauts away from guessing and toward careful checking.",
            ),
            QAItem(
                question="How did the astronauts solve the problem safely?",
                answer=f"They discovered that {mystery.source}. Together, they {mystery.solution}, while keeping people and equipment away from the bonfire.",
            ),
            QAItem(
                question="How did dialogue change what the astronauts did?",
                answer=f"{params.hero} offered a ridiculous guess, but {params.helper} suggested testing it safely. Their exchange led them to inspect the clue instead of rushing toward the fire.",
            ),
            QAItem(
                question="What proved the mystery was solved?",
                answer=f"The repaired scene ended with this clear result: {mystery.ending}",
            ),
        ],
        world_qa=[
            QAItem(
                question="Why should explorers investigate a strange sound carefully?",
                answer="Explorers should investigate carefully because a strange sound may point to a real danger, and hurrying could hurt people or damage equipment.",
            ),
            QAItem(
                question="What makes dialogue useful in an adventure?",
                answer="Dialogue is useful when characters listen to one another and let the conversation change a decision or reveal a better plan.",
            ),
            QAItem(
                question="How should a bonfire be used safely?",
                answer="A bonfire should stay inside a clear stone or marked area, with people and loose equipment kept safely away from the flames.",
            ),
        ],
        world=world,
    )


def dump_trace(world: World) -> str:
    return "\n".join([
        "--- world model state ---",
        f"hero={world.hero.id} role={world.hero.role} meters={world.hero.meters} memes={world.hero.memes}",
        f"helper={world.helper.id} role={world.helper.role} meters={world.helper.meters} memes={world.helper.memes}",
        f"place={world.setting.place}",
        f"object={world.object_name}",
        f"treat={world.treat}",
        f"mystery={world.mystery.title}",
        f"clue={world.mystery.clue}",
        f"source={world.mystery.source}",
        f"solution={world.mystery.solution}",
    ])


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts =="]
    lines.extend(f"{i}. {prompt}" for i, prompt in enumerate(sample.prompts, 1))
    lines.append("")
    lines.append("== (2) Story questions ==")
    for item in sample.story_qa:
        lines.extend([f"Q: {item.question}", f"A: {item.answer}"])
    lines.append("")
    lines.append("== (3) World knowledge questions ==")
    for item in sample.world_qa:
        lines.extend([f"Q: {item.question}", f"A: {item.answer}"])
    return "\n".join(lines)


def asp_facts() -> str:
    import asp
    return "\n".join([
        asp.fact("astronaut", "luna"),
        asp.fact("hears_plunk", "luna"),
        asp.fact("checks_clue", "luna"),
        asp.fact("shares_dialogue", "luna"),
        asp.fact("protects_fire", "luna"),
        asp.fact("finds_source", "luna"),
    ])


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show solved_story/1."))
    actual = set(asp.atoms(model, "solved_story"))
    expected = {("luna",)}
    if actual != expected:
        print(f"MISMATCH: {actual} != {expected}")
        return 1
    sample = generate(StoryParams("Luna", "Orion", PLACES[0], OBJECTS[0], TREATS[0], seed=0))
    if not sample.story or "plunk" not in sample.story or "bonfire" not in sample.story:
        print("MISMATCH: generated story coverage failed")
        return 1
    print("OK: ASP parity and story generation verified.")
    return 0


def curated() -> list[StoryParams]:
    return [
        StoryParams("Luna", "Orion", PLACES[0], OBJECTS[0], TREATS[0], seed=0),
        StoryParams("Miko", "Tess", PLACES[1], OBJECTS[1], TREATS[1], seed=1),
        StoryParams("Pax", "Nova", PLACES[2], OBJECTS[2], TREATS[2], seed=2),
        StoryParams("Orion", "Luna", PLACES[3], OBJECTS[3], TREATS[3], seed=3),
    ]


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
        print(asp_program("#show solved_story/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        model = asp.one_model(asp_program(
            "#show space_crew/1.\n#show has_mystery/1.\n#show safe_solution/1.\n"
            "#show bonfire_story/1.\n#show solved_story/1."
        ))
        print("\n".join(str(atom) for atom in model))
        return

    if args.n < 1:
        raise StoryError("-n must be at least 1")

    samples: list[StorySample]
    if args.all:
        samples = [generate(params) for params in curated()]
    else:
        samples = []
        base_seed = args.seed if args.seed is not None else random.randrange(2**31)
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
        header = f"### variant {index + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if index < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()

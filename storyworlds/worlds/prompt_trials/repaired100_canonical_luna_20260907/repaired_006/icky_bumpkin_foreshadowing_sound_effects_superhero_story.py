#!/usr/bin/env python3
"""
A gentle superhero story about an icky bumpkin, a hidden warning, and brave care.
"""

from __future__ import annotations

import argparse
import json
import os
import random
import sys
from dataclasses import dataclass, field

_storyworlds_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if not os.path.exists(os.path.join(_storyworlds_dir, "results.py")):
    _storyworlds_dir = os.path.dirname(_storyworlds_dir)
sys.path.insert(0, _storyworlds_dir)
from results import QAItem, StoryError, StorySample  # noqa: E402


NAMES = ("Luna", "Milo", "Tess", "Niko", "Zara", "Pip")
BUMPkin_NAMES = ("Benny", "Bumpkin", "Bram", "Bo")
PLACES = (
    "a bright city rooftop above Moonbeam Street",
    "a little town square beside the bell tower",
    "a rainy park under the silver clouds",
    "a busy harbor where gulls circled the lighthouse",
)
POWERS = (
    "a glowing moon shield",
    "super-speedy sneakers",
    "a cape that could catch falling things",
    "a gentle beam of star-light",
)
SOUNDS = (
    "WHOOSH!",
    "KAPOW!",
    "ZING!",
    "CLANG!",
)
WARNINGS = (
    "three blue sparks blinked above the old fountain",
    "the pigeons suddenly flew in one careful circle",
    "a tiny red light winked beneath the bridge",
    "the wind hummed the same note twice",
)
DANGERS = (
    "a loose festival sign",
    "a runaway delivery cart",
    "a wobbling water tank",
    "a giant bundle of balloons",
)
ENDINGS = (
    "At sunset, the hero's cape fluttered like a brave little flag above the safe town.",
    "That night, the rescued crowd cheered while the moon shone on the quiet street.",
    "The next morning, a bright badge appeared on the hero's jacket: LISTEN, THEN LEAP.",
)


@dataclass
class Entity:
    id: str
    label: str
    kind: str = "thing"
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)


@dataclass
class World:
    place: str
    entities: dict[str, Entity] = field(default_factory=dict)
    fired: set[str] = field(default_factory=set)
    facts: dict[str, str] = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])

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


@dataclass
class StoryParams:
    seed: int | None = None
    hero_name: str = "Luna"
    bumpkin_name: str = "Benny"
    place: str = PLACES[0]
    power: str = POWERS[0]
    warning: str = WARNINGS[0]
    danger: str = DANGERS[0]
    sound: str = SOUNDS[0]
    ending: str = ENDINGS[0]


def build_world(params: StoryParams) -> World:
    world = World(params.place)
    hero = world.add(Entity("hero", params.hero_name, "character", {"bravery": 1.0}, {"attention": 0.0}))
    bumpkin = world.add(Entity("bumpkin", params.bumpkin_name, "character", {"distance": 1.0}, {"worry": 1.0}))
    hazard = world.add(Entity("hazard", params.danger, "hazard", {"danger": 1.0}, {}))
    world.facts.update(
        hero=hero.label,
        bumpkin=bumpkin.label,
        warning=params.warning,
        danger=hazard.label,
        power=params.power,
        sound=params.sound,
        ending=params.ending,
    )
    world.say(
        f"On {params.place}, {hero.label} watched over the town with {params.power}. "
        f"Everyone called {bumpkin.label} an icky bumpkin because mud, jam, and old leaves always seemed to follow him."
    )
    world.say(
        f"Then {params.warning}. It was a small clue, but it made {hero.label} pause."
    )
    world.para()
    world.say(
        f'"Look out!" cried {bumpkin.label}. "That warning means trouble is coming!"'
    )
    world.say(
        f'"I hear you," said {hero.label}. "Show me where the danger is, and we will help together."'
    )
    hero.memes["attention"] = 1.0
    world.fired.add("foreshadowing")
    world.say(
        f"Behind the corner, the {params.danger} began to wobble toward the crowd. "
        f"{params.sound} {hero.label} sprang forward, while {bumpkin.label} pointed to a strong rope beside the fountain."
    )
    world.para()
    world.say(
        f"{hero.label} raised {params.power} and slowed the {params.danger}. "
        f"{bumpkin.label} grabbed the rope with both muddy hands and pulled."
    )
    world.say(
        f"{params.sound} The danger stopped just before it reached the children. "
        f"The icky bumpkin had noticed the warning first, and the superhero had listened."
    )
    hero.memes["attention"] = 2.0
    hero.memes["trust"] = 1.0
    bumpkin.memes["worry"] = 0.0
    bumpkin.memes["courage"] = 1.0
    hazard.meters["danger"] = 0.0
    world.fired.add("rescue")
    world.say(
        f"The crowd cheered for both friends. {bumpkin.label} wiped mud from his nose and smiled. "
        f"{params.ending}"
    )
    return world


ASP_RULES = r"""
warning_seen :- warning.
danger_stopped :- warning_seen, helper_points, hero_listens.
rescue :- danger_stopped.
#show warning_seen/0.
#show danger_stopped/0.
#show rescue/0.
"""


def asp_facts() -> str:
    import asp
    return "\n".join(
        (
            asp.fact("warning"),
            asp.fact("helper_points"),
            asp.fact("hero_listens"),
        )
    )


def asp_program(show: str = "") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program())
    names = {str(atom) for atom in model}
    expected = {"warning_seen", "danger_stopped", "rescue"}
    if expected.issubset(names):
        print("OK: ASP and Python agree on the foreshadowed rescue.")
        return 0
    print("MISMATCH between ASP and Python.")
    print(sorted(names))
    return 1


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    seed = args.seed if args.seed is not None else 0
    return StoryParams(
        seed=seed,
        hero_name=rng.choice(NAMES),
        bumpkin_name=rng.choice(BUMPkin_NAMES),
        place=rng.choice(PLACES),
        power=rng.choice(POWERS),
        warning=rng.choice(WARNINGS),
        danger=rng.choice(DANGERS),
        sound=rng.choice(SOUNDS),
        ending=rng.choice(ENDINGS),
    )


def generate(params: StoryParams) -> StorySample:
    if not params.hero_name.strip() or not params.bumpkin_name.strip():
        raise StoryError("Hero and bumpkin names must not be empty.")
    if params.hero_name == params.bumpkin_name:
        raise StoryError("The hero and bumpkin need different names.")
    world = build_world(params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=[
            "Write a superhero story with an icky bumpkin who notices an important warning.",
            f"Include foreshadowing through this clue: {params.warning}.",
            f"Use the sound effect {params.sound} during the rescue.",
        ],
        story_qa=[
            QAItem(
                "Who noticed the warning first?",
                f"{params.bumpkin_name} noticed the warning first and told {params.hero_name}.",
            ),
            QAItem(
                "What danger did the friends stop?",
                f"They stopped the {params.danger} before it reached the crowd.",
            ),
            QAItem(
                "How did the rescue succeed?",
                f"{params.hero_name} used {params.power}, while {params.bumpkin_name} used the rope to hold the danger still.",
            ),
            QAItem(
                "Why was the warning important?",
                f"The warning foreshadowed the {params.danger}, giving the friends time to act safely.",
            ),
        ],
        world_qa=[
            QAItem(
                "What is foreshadowing?",
                "Foreshadowing is a clue that hints something important may happen later.",
            ),
            QAItem(
                "Why can sound effects help a superhero story?",
                "Sound effects make action easier to imagine and show when a sudden event happens.",
            ),
        ],
        world=world,
    )


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    lines.extend(sample.prompts)
    lines.append("")
    lines.append("== story qa ==")
    for item in sample.story_qa:
        lines.extend((f"Q: {item.question}", f"A: {item.answer}"))
    lines.append("")
    lines.append("== world qa ==")
    for item in sample.world_qa:
        lines.extend((f"Q: {item.question}", f"A: {item.answer}"))
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for entity in world.entities.values():
        lines.append(
            f"{entity.id}: meters={entity.meters} memes={entity.memes}"
        )
    lines.append(f"fired={sorted(world.fired)}")
    return "\n".join(lines)


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
    parser = build_parser()
    args = parser.parse_args()
    if args.show_asp:
        print(asp_program("#show warning_seen/0.\n#show danger_stopped/0.\n#show rescue/0."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        model = asp.one_model(asp_program())
        print([str(atom) for atom in model])
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    count = len(NAMES) * len(BUMPkin_NAMES) if args.all else max(1, args.n)
    samples = []
    for index in range(count):
        seed = base_seed + index
        params = resolve_params(argparse.Namespace(seed=seed), random.Random(seed))
        samples.append(generate(params))

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
        if index + 1 < len(samples):
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()

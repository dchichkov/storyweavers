#!/usr/bin/env python3
"""
A standalone folk-tale storyworld about an accident, a damper, logical thinking,
kindness, and a small surprise.
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


VILLAGES = ["Hazel Hollow", "Mossy Brook", "Thistle Glen", "Willowmere"]
HEROES = ["Luna", "Mara", "Nell", "Pip"]
HELPERS = ["Grandmother Elsi", "Old Bram", "Aunt Sela", "Uncle Rowan"]
OBJECTS = ["the mill wheel", "the bell tower", "the bridge gate", "the cider press"]
DAMPERS = ["a wool blanket", "a clay shield", "a leather pad", "a bundle of reeds"]
TRAITS = ["patient", "clever", "kind", "curious"]
SEEDS = [101, 203, 307, 401]

ACCIDENTS = [
    {
        "id": "wheel_spark",
        "premise": "a loose branch struck the mill wheel, and a shower of sparks leaped toward the dry hay",
        "risk": "the hay could catch fire",
        "clue": "the sparks stopped whenever the wheel slowed",
        "plan": "close the water gate, clear the hay, and slow the wheel before touching the branch",
        "kindness": "carried the miller's frightened puppy to a cool patch beneath the elder tree",
        "result": "the branch was removed and not one straw caught fire",
        "surprise": "when the wheel turned again, it played a gentle rhythm like a wooden drum",
        "lesson": "A calm mind can find the order hidden inside a frightening accident.",
    },
    {
        "id": "bell_rope",
        "premise": "the bell rope snapped during a storm and sent the great bell swinging above the square",
        "risk": "the bell might fall and hurt someone",
        "clue": "the bell swung less whenever everyone stepped away from the tower",
        "plan": "empty the square, brace the tower door, and wait for the bell to stop before climbing",
        "kindness": "shared a warm shawl with the youngest child who had come looking for her mother",
        "result": "the bell settled safely and the rope was replaced",
        "surprise": "a tiny bird flew from the bell's hollow and landed on the new rope",
        "lesson": "When danger moves, distance and patience are wiser than a brave-looking rush.",
    },
    {
        "id": "bridge_gate",
        "premise": "a cart wheel broke beside the bridge gate and left the gate crooked across the road",
        "risk": "the cart could roll into the stream",
        "clue": "the cart shifted toward the water whenever the gate was pulled",
        "plan": "block the cart, guide travelers around the footpath, and lift the gate only after the wheel was secured",
        "kindness": "helped an old traveler carry a basket of apples along the dry path",
        "result": "the cart was repaired and the gate opened without a splash",
        "surprise": "one apple rolled from the basket and bobbed downstream like a bright little boat",
        "lesson": "A logical plan protects both the great trouble and the small traveler nearby.",
    },
]


@dataclass
class Person:
    name: str
    role: str
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)


@dataclass
class Accident:
    object_name: str
    damper: str
    data: dict
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)


@dataclass
class World:
    hero: Person
    helper: Person
    village: str
    accident: Accident
    facts: dict = field(default_factory=dict)
    lines: list[str] = field(default_factory=list)

    def say(self, text: str) -> None:
        self.lines.append(text)

    def render(self) -> str:
        return " ".join(self.lines)


@dataclass
class StoryParams:
    hero: str
    helper: str
    village: str
    object_name: str
    damper: str
    trait: str
    seed: Optional[int] = None


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="A folk tale of an accident softened by a damper, logic, kindness, and surprise.")
    parser.add_argument("--hero", choices=HEROES)
    parser.add_argument("--helper", choices=HELPERS)
    parser.add_argument("--village", choices=VILLAGES)
    parser.add_argument("--object", dest="object_name", choices=OBJECTS)
    parser.add_argument("--damper", choices=DAMPERS)
    parser.add_argument("--trait", choices=TRAITS)
    parser.add_argument("-n", type=int, default=1)
    parser.add_argument("--all", action="store_true")
    parser.add_argument("--seed", type=int, default=None)
    parser.add_argument("--trace", action="store_true")
    parser.add_argument("--qa", action="store_true")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--asp", action="store_true")
    parser.add_argument("--verify", action="store_true")
    parser.add_argument("--show-asp", action="store_true")
    return parser


def valid_combo(params: StoryParams) -> bool:
    return (
        params.hero in HEROES
        and params.helper in HELPERS
        and params.village in VILLAGES
        and params.object_name in OBJECTS
        and params.damper in DAMPERS
        and params.trait in TRAITS
    )


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    params = StoryParams(
        hero=args.hero or rng.choice(HEROES),
        helper=args.helper or rng.choice(HELPERS),
        village=args.village or rng.choice(VILLAGES),
        object_name=args.object_name or rng.choice(OBJECTS),
        damper=args.damper or rng.choice(DAMPERS),
        trait=args.trait or rng.choice(TRAITS),
        seed=args.seed,
    )
    if not valid_combo(params):
        raise StoryError("The chosen folk-tale names or tools do not belong to this world.")
    return params


def make_world(params: StoryParams) -> World:
    stable = params.seed if params.seed is not None else sum(ord(c) for c in repr(params))
    rng = random.Random(stable)
    data = rng.choice(ACCIDENTS)
    accident = Accident(
        object_name=params.object_name,
        damper=params.damper,
        data=data,
        meters={"danger": 1.0, "distance": 0.0},
        memes={"fear": 0.5, "trust": 0.5, "kindness": 0.0, "surprise": 0.0},
    )
    hero = Person(
        params.hero,
        "village child",
        meters={"courage": 1.0, "care": 1.0},
        memes={"worry": 0.5, "logic": 0.0, "kindness": 0.0},
    )
    helper = Person(
        params.helper,
        "wise helper",
        meters={"wisdom": 1.0},
        memes={"patience": 1.0},
    )
    return World(hero, helper, params.village, accident, {"opening": rng.choice([
        "At the edge of the green valley,",
        "Long ago, beside a laughing brook,",
        "In a village where every roof had moss,",
        "One golden morning in the hills,",
    ])})


def generate_story(world: World) -> None:
    h, helper, a = world.hero, world.helper, world.accident
    d = a.data
    world.say(f"{world.facts['opening']} {h.name}, a {h.role}, lived in {world.village}.")
    world.say(f"One morning, an accident disturbed {a.object_name}: {d['premise']}.")
    world.say(f"{h.name} reached for {a.damper}, but {helper.name} called, \"Wait. What danger do you see?\"")
    world.say(f"\"{d['risk']},\" said {h.name}. \"And I notice that {d['clue']}.\"")
    h.memes["logic"] += 1.0
    world.say(f"\"Then let us be logical,\" said {helper.name}. \"We will {d['plan']}.\"")
    world.say(f"{h.name} answered, \"I will remember the order, and I will help anyone who is frightened.\"")
    world.say(f"Together they used {a.damper} as a gentle damper while the villagers moved back.")
    a.meters["distance"] = 1.0
    a.meters["danger"] = 0.0
    h.memes["kindness"] += 1.0
    world.say(f"With care, {h.name} {d['kindness']}. Then {d['result']}.")
    a.memes["fear"] = 0.0
    a.memes["surprise"] += 1.0
    world.say(f"Just when everyone expected silence, {d['surprise']}.")
    world.say(f"{helper.name} smiled and said, \"The best surprises often wait behind a careful choice.\"")
    world.say(f"And so {h.name} learned that {d['lesson']} The villagers went home with warm hearts and wiser hands.")


def story_qa(world: World) -> list[QAItem]:
    h, helper, a = world.hero, world.helper, world.accident
    d = a.data
    return [
        QAItem("Who helped solve the accident?", f"{h.name} worked with {helper.name}, the wise helper from {world.village}."),
        QAItem("What danger did the accident create?", f"The accident created this danger: {d['risk']}."),
        QAItem(f"Why did {h.name} wait before acting?", f"{h.name} waited because {d['clue']}."),
        QAItem("How was the damper used?", f"The villagers used {a.damper} as a gentle damper while they moved away and followed the logical plan."),
        QAItem("What kindness did the hero show?", f"{h.name} {d['kindness']}."),
        QAItem("What was the surprise?", f"The surprise was that {d['surprise']}."),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem("What is an accident?", "An accident is something harmful or unexpected that happens without being planned."),
        QAItem("What is a damper?", "A damper is something that softens movement, sound, heat, or force."),
        QAItem("What does logical mean?", "Logical means using clear reasons and a sensible order to decide what to do."),
        QAItem("What is kindness?", "Kindness means caring about others and helping them gently."),
        QAItem("What is surprise?", "A surprise is something unexpected that suddenly happens."),
    ]


def generation_prompts(world: World) -> list[str]:
    return [
        "Write a child-friendly folk tale in which an accident is solved by logical thinking, a damper, and kindness.",
        f"Tell how {world.hero.name} and {world.helper.name} protect {world.village} after an accident involving {world.accident.object_name}.",
        f"End with a gentle surprise and show how the damper changes the danger.",
    ]


def dump_trace(world: World) -> str:
    a = world.accident
    return "\n".join([
        "--- world model state ---",
        f"hero={world.hero.name} meters={world.hero.meters} memes={world.hero.memes}",
        f"helper={world.helper.name} role={world.helper.role}",
        f"village={world.village}",
        f"object={a.object_name} damper={a.damper}",
        f"danger_meter={a.meters['danger']} distance_meter={a.meters['distance']}",
        f"accident={a.data['id']} surprise={a.data['surprise']}",
    ])


def format_qa(sample: StorySample) -> str:
    sections = ["== prompts =="]
    sections.extend(f"{i}. {p}" for i, p in enumerate(sample.prompts, 1))
    sections.append("\n== story QA ==")
    for item in sample.story_qa:
        sections.extend([f"Q: {item.question}", f"A: {item.answer}"])
    sections.append("\n== world QA ==")
    for item in sample.world_qa:
        sections.extend([f"Q: {item.question}", f"A: {item.answer}"])
    return "\n".join(sections)


def asp_facts() -> str:
    import asp
    lines = []
    for value in HEROES:
        lines.append(asp.fact("hero", value))
    for value in HELPERS:
        lines.append(asp.fact("helper", value))
    for value in VILLAGES:
        lines.append(asp.fact("village", value))
    for value in OBJECTS:
        lines.append(asp.fact("object", value))
    for value in DAMPERS:
        lines.append(asp.fact("damper", value))
    for value in TRAITS:
        lines.append(asp.fact("trait", value))
    return "\n".join(lines)


ASP_RULES = r"""
choice(H,He,V,O,D,T) :- hero(H), helper(He), village(V), object(O), damper(D), trait(T).
logical(D) :- damper(D).
valid(H,He,V,O,D,T) :- choice(H,He,V,O,D,T), logical(D).
#show valid/6.
"""


def asp_program(show: str = "#show valid/6.") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid() -> set[tuple]:
    import asp
    model = asp.one_model(asp_program())
    return set(asp.atoms(model, "valid"))


def asp_verify() -> int:
    python_values = {
        (hero, helper, village, obj, damper, trait)
        for hero in HEROES
        for helper in HELPERS
        for village in VILLAGES
        for obj in OBJECTS
        for damper in DAMPERS
        for trait in TRAITS
        if valid_combo(StoryParams(hero, helper, village, obj, damper, trait))
    }
    clingo_values = asp_valid()
    if python_values == clingo_values:
        print(f"OK: clingo gate matches Python ({len(clingo_values)} combinations).")
        for params in [
            StoryParams("Luna", HELPERS[0], VILLAGES[0], OBJECTS[0], DAMPERS[0], TRAITS[0]),
            StoryParams(HEROES[1], HELPERS[1], VILLAGES[1], OBJECTS[1], DAMPERS[1], TRAITS[1]),
        ]:
            generate(params)
        print("OK: generated stories exercised.")
        return 0
    print("MISMATCH")
    print("only in clingo:", sorted(clingo_values - python_values))
    print("only in Python:", sorted(python_values - clingo_values))
    return 1


def generate(params: StoryParams) -> StorySample:
    world = make_world(params)
    generate_story(world)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_qa(world),
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


CURATED = [
    StoryParams("Luna", "Grandmother Elsi", "Hazel Hollow", "the mill wheel", "a wool blanket", "patient", 101),
    StoryParams("Mara", "Old Bram", "Mossy Brook", "the bell tower", "a clay shield", "clever", 203),
    StoryParams("Nell", "Aunt Sela", "Thistle Glen", "the bridge gate", "a leather pad", "kind", 307),
]


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp or args.asp:
        print(asp_program())
        return
    if args.verify:
        raise SystemExit(asp_verify())

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen = set()
        for index in range(max(1, args.n)):
            rng = random.Random(base_seed + index)
            params = resolve_params(args, rng)
            params.seed = base_seed + index
            sample = generate(params)
            while sample.story in seen:
                params.seed += 1
                sample = generate(params)
            seen.add(sample.story)
            samples.append(sample)

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

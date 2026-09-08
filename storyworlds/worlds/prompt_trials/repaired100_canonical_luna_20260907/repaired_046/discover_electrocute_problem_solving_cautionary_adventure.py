#!/usr/bin/env python3
"""A child-safe cautionary adventure about discovering why a lamp is dangerous."""

from __future__ import annotations

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


@dataclass(frozen=True)
class Entity:
    id: str
    kind: str
    label: str
    role: str
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)
    traits: tuple[str, ...] = ()


@dataclass
class StoryParams:
    place: str = "the old lighthouse"
    hero: str = "Luna"
    helper: str = "Tavi"
    object_name: str = "the brass signal lamp"
    seed: Optional[int] = None


PLACES = {
    "lighthouse": "the old lighthouse",
    "workshop": "the hilltop workshop",
    "station": "the little mountain station",
    "cabin": "the ranger's cabin",
}
HEROES = ["Luna", "Mara", "Niko", "Suri", "Pip"]
HELPERS = ["Tavi", "Bea", "Oren", "Jae", "Miko"]
OBJECTS = [
    "the brass signal lamp",
    "the red trail lantern",
    "the silver weather radio",
    "the blue repair light",
]

INCIDENTS = [
    {
        "name": "the wet cord",
        "problem": "a puddle had reached a cracked cord beside the lamp",
        "clue": "dark water glittered beneath the split rubber",
        "danger": "touching the cord could electrocute someone",
        "safe_job": "keep everyone away from the puddle",
        "helper_job": "fetch the caretaker and point out the damaged cord",
        "result": "the caretaker unplugged the circuit and replaced the cord",
        "ending": "the repaired lamp shone safely over a dry, bright floor",
    },
    {
        "name": "the fallen cover",
        "problem": "a metal cover had fallen away from a humming control box",
        "clue": "a warning picture showed a lightning bolt beside the open box",
        "danger": "touching the exposed parts could electrocute someone",
        "safe_job": "stand back and mark the danger with a bright scarf",
        "helper_job": "call the ranger and keep the path clear",
        "result": "the ranger switched off the power and fastened a new cover",
        "ending": "the warning picture rested under a firmly closed cover",
    },
    {
        "name": "the frayed switch",
        "problem": "the switch wire was frayed where it entered the lantern",
        "clue": "tiny copper threads poked through the worn covering",
        "danger": "grabbing the wire could electrocute someone",
        "safe_job": "leave the switch untouched and guide others around it",
        "helper_job": "find the spare sign and tell the guide what happened",
        "result": "the guide shut off the power and fitted a new switch",
        "ending": "the lantern blinked once, then glowed steadily behind its safe switch",
    },
    {
        "name": "the humming puddle",
        "problem": "a storm had soaked the floor below a humming heater",
        "clue": "the hum stopped when the caretaker pulled the main switch",
        "danger": "stepping into the water near the heater could electrocute someone",
        "safe_job": "stay on the dry wooden step and warn the others",
        "helper_job": "bring the caretaker without crossing the wet floor",
        "result": "the power was turned off and the soaked heater was removed",
        "ending": "fresh boards covered the floor while rain tapped harmlessly outside",
    },
]

OPENINGS = [
    "Luna loved adventures, especially the kind that began with a mystery.",
    "At dawn, Luna climbed toward a place where clouds brushed the roof.",
    "The mountain path curled upward, and Luna followed a flash of brass.",
    "A storm had passed, leaving the world sparkling and full of clues.",
    "Luna and Tavi were searching for a safe beacon before sunset.",
]


@dataclass
class World:
    params: StoryParams
    entities: dict[str, Entity] = field(default_factory=dict)
    facts: dict[str, object] = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])

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
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Cautionary electrical-safety adventure.")
    parser.add_argument("--place", choices=PLACES)
    parser.add_argument("--hero", choices=HEROES)
    parser.add_argument("--helper", choices=HELPERS)
    parser.add_argument("--object", dest="object_name", choices=OBJECTS)
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


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    place_key = args.place or rng.choice(list(PLACES))
    hero = args.hero or rng.choice(HEROES)
    helper = args.helper or rng.choice(HELPERS)
    if helper == hero:
        helper = rng.choice([name for name in HELPERS if name != hero])
    return StoryParams(
        place=PLACES[place_key],
        hero=hero,
        helper=helper,
        object_name=args.object_name or rng.choice(OBJECTS),
    )


def _incident(params: StoryParams) -> dict[str, str]:
    seed = params.seed if params.seed is not None else 0
    return INCIDENTS[seed % len(INCIDENTS)]


def tell(params: StoryParams) -> World:
    if params.hero == params.helper:
        raise StoryError("hero and helper must be different characters")
    if params.place not in PLACES.values():
        raise StoryError("place must come from the place registry")
    if params.object_name not in OBJECTS:
        raise StoryError("object must come from the object registry")

    incident = _incident(params)
    w = World(params)
    hero = w.add(Entity(
        id="hero",
        kind="character",
        label=params.hero,
        role="careful explorer",
        meters={"curiosity": 1.0, "danger": 0.0},
        memes={"caution": 1.0, "confidence": 1.0},
        traits=("observant",),
    ))
    helper = w.add(Entity(
        id="helper",
        kind="character",
        label=params.helper,
        role="trusted teammate",
        meters={"distance": 1.0},
        memes={"trust": 1.0, "caution": 1.0},
        traits=("helpful",),
    ))
    object_entity = w.add(Entity(
        id="object",
        kind="device",
        label=params.object_name,
        role="electrical device",
        meters={"power": 1.0, "wetness": 1.0},
        memes={"warning": 1.0},
        traits=("useful", "unsafe-until-checked"),
    ))

    opening = OPENINGS[(params.seed or 0) % len(OPENINGS)]
    w.say(opening)
    w.say(
        f"{params.hero} and {params.helper} reached {params.place} and discovered "
        f"{params.object_name} waiting near the doorway."
    )
    w.say(
        f"“It could help us find the trail,” said {params.hero}. "
        f"“But we inspect it before touching anything,” answered {params.helper}."
    )

    w.para()
    w.say(f"Their first clue was clear: {incident['problem']}.")
    w.say(f"{params.hero} noticed that {incident['clue']}.")
    w.say(
        f"“I know what this means,” said {params.hero}. "
        f"{incident['danger'].capitalize()}”
    )
    w.say(
        f"{params.helper} took one careful step back. “Then we will not test it with our hands. "
        f"We will solve the problem safely.”"
    )
    hero.meters["danger"] += 1.0
    hero.memes["caution"] += 1.0
    helper.memes["trust"] += 1.0

    w.para()
    w.say(f"{params.hero} decided to {incident['safe_job']}.")
    w.say(f"{params.helper} agreed to {incident['helper_job']}.")
    w.say(
        f"Together they followed the safety plan: they did not touch the device, "
        f"the water, or any bare wire. Their calm choices gave the grown-up room to help."
    )
    w.say(
        f"“You discovered the danger before it became an accident,” said {params.helper}."
    )
    w.say(
        f"{params.hero} smiled. “An adventure is better when everyone comes home safely.”"
    )
    w.say(f"Then {incident['result']}.")

    hero.meters["danger"] = 0.0
    hero.memes["confidence"] += 1.0
    helper.memes["trust"] += 1.0

    w.para()
    w.say(f"At last, {incident['ending']}.")
    w.say(
        f"{params.hero} and {params.helper} continued their journey, carrying a lesson "
        f"stronger than any storm: electricity can be useful, but a strange or damaged "
        f"device must be left alone while a trusted adult makes it safe."
    )

    w.facts.update(
        hero=hero,
        helper=helper,
        object_entity=object_entity,
        incident=incident["name"],
        problem=incident["problem"],
        clue=incident["clue"],
        danger=incident["danger"],
        safe_job=incident["safe_job"],
        helper_job=incident["helper_job"],
        result=incident["result"],
        ending=incident["ending"],
        discovered=True,
        electrocution_avoided=True,
        problem_solving=True,
        cautionary=True,
        dialogue=True,
    )
    return w


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f"Write an adventure in which {world.params.hero} and {world.params.helper} discover that {f['problem']}.",
        f"Tell a cautionary problem-solving story where they avoid danger because {f['clue']}.",
        "Use child-friendly dialogue to explain why nobody should touch a damaged electrical device.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = world.params.hero
    helper = world.params.helper
    return [
        QAItem(
            question=f"What did {hero} and {helper} discover?",
            answer=f"They discovered {f['problem']}, and they noticed that {f['clue']}.",
        ),
        QAItem(
            question=f"Why did {hero} stay away from the device?",
            answer=f"{hero} stayed away because {f['danger']}.",
        ),
        QAItem(
            question=f"How did {hero} and {helper} solve the problem?",
            answer=f"{hero} chose to {f['safe_job']}, while {helper} worked to {f['helper_job']}. Then {f['result']}.",
        ),
        QAItem(
            question="What proved that their caution worked?",
            answer=f"The danger was handled safely: {f['result']}, and {f['ending']}.",
        ),
        QAItem(
            question="What lesson did the adventure teach?",
            answer="A child should never touch a damaged electrical device, wet electrical equipment, or exposed wire. The safe choice is to move away and tell a trusted adult.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does it mean to discover something?",
            answer="To discover something means to notice or learn about it, often by looking carefully.",
        ),
        QAItem(
            question="Why can electricity be dangerous?",
            answer="Electricity can hurt a person, especially when wires are damaged or electricity meets water.",
        ),
        QAItem(
            question="What should a child do around a damaged electrical device?",
            answer="A child should not touch it, should move away, and should tell a trusted adult.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    lines.extend(sample.prompts)
    lines.append("")
    lines.append("== story qa ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== world qa ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- trace ---"]
    for entity in world.entities.values():
        lines.append(
            f"{entity.id}: kind={entity.kind} meters={entity.meters} "
            f"memes={entity.memes} traits={list(entity.traits)}"
        )
    lines.append(f"facts={world.facts['incident']}, discovered={world.facts['discovered']}, "
                 f"electrocution_avoided={world.facts['electrocution_avoided']}")
    return "\n".join(lines)


ASP_RULES = r"""
#show valid_place/1.
#show valid_object/1.
#show safe_choice/1.

valid_place(lighthouse).
valid_place(workshop).
valid_place(station).
valid_place(cabin).

valid_object(brass_signal_lamp).
valid_object(red_trail_lantern).
valid_object(silver_weather_radio).
valid_object(blue_repair_light).

safe_choice(step_away).
safe_choice(tell_adult).

unsafe_choice(touch_damaged_device).
electrical_danger :- unsafe_choice(touch_damaged_device).
"""


def asp_facts() -> str:
    import asp
    lines = [asp.fact("place_key", key) for key in PLACES]
    lines.extend(asp.fact("object_key", key.replace(" ", "_")) for key in (
        "brass signal lamp",
        "red trail lantern",
        "silver weather radio",
        "blue repair light",
    ))
    return "\n".join(lines)


def asp_program(show: str = "") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program())
    places = set(asp.atoms(model, "valid_place"))
    objects = set(asp.atoms(model, "valid_object"))
    expected_places = {(key,) for key in PLACES}
    expected_objects = {
        ("brass_signal_lamp",),
        ("red_trail_lantern",),
        ("silver_weather_radio",),
        ("blue_repair_light",),
    }
    if places != expected_places or objects != expected_objects:
        print("MISMATCH: ASP registry facts do not match Python registries")
        return 1
    for seed in range(8):
        params = StoryParams(seed=seed)
        sample = generate(params)
        if "electrocute" not in sample.story or "discover" not in sample.story:
            print("MISMATCH: generated story omitted required narrative words")
            return 1
    print("OK: ASP/Python parity and generated-story checks passed.")
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


CURATED = [
    StoryParams(place=PLACES["lighthouse"], hero="Luna", helper="Tavi",
                object_name="the brass signal lamp", seed=0),
    StoryParams(place=PLACES["workshop"], hero="Mara", helper="Bea",
                object_name="the red trail lantern", seed=1),
    StoryParams(place=PLACES["station"], hero="Niko", helper="Oren",
                object_name="the silver weather radio", seed=2),
    StoryParams(place=PLACES["cabin"], hero="Suri", helper="Jae",
                object_name="the blue repair light", seed=3),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid_place/1.\n#show valid_object/1.\n#show safe_choice/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print("Valid places:")
        for key in PLACES:
            print(f"  {key}")
        print("\nValid electrical objects:")
        for value in OBJECTS:
            print(f"  {value}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(params) for params in CURATED]
    else:
        seen: set[str] = set()
        attempt = 0
        while len(samples) < args.n and attempt < max(args.n * 50, 50):
            params = resolve_params(args, random.Random(base_seed + attempt))
            params.seed = base_seed + attempt
            sample = generate(params)
            if sample.story not in seen:
                seen.add(sample.story)
                samples.append(sample)
            attempt += 1

    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([sample.to_dict() for sample in samples],
                             indent=2, ensure_ascii=False))
        return

    for index, sample in enumerate(samples):
        header = ""
        if args.all:
            header = f"### {sample.params.hero} and {sample.params.helper} at {sample.params.place}"
        elif len(samples) > 1:
            header = f"### variant {index + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if index < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()

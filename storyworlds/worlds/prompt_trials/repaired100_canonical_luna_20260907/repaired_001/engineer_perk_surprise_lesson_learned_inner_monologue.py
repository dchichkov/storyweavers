#!/usr/bin/env python3
"""
A tall-tale storyworld about an engineer, an unexpected perk, and a lesson learned.

Luna's seed tale:
An eager young engineer builds a wonderful machine for the town fair.
A surprising extra feature seems like a useful perk, but it sends the machine
somewhere no one expected. The engineer's inner monologue becomes a lesson:
good builders test every part, especially the part they did not plan.
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


SETTINGS = {
    "town_square": "the town square",
    "hill_fair": "the hilltop fairground",
    "river_green": "the riverside green",
    "orchard_gate": "the orchard gate",
}

PLACE_DETAILS = {
    "town_square": ("beside the tall clock", "the fountain"),
    "hill_fair": ("above the striped tents", "the windmill"),
    "river_green": ("near the willow trees", "the footbridge"),
    "orchard_gate": ("between the apple carts", "the biggest apple tree"),
}

NAMES = ["Luna", "Milo", "Pia", "Theo", "Nora", "Bram", "Ivy", "Sol"]
HELPERS = ["grandmother", "teacher", "neighbor", "uncle"]

MACHINE_PLANS = {
    "cloud_cart": {
        "name": "a cloud-catching cart",
        "verb": "build a cloud-catching cart",
        "purpose": "carry picnic baskets above the fair",
        "materials": "wooden wheels, bright canvas, and copper pipes",
        "action": "lift gently into the sky",
    },
    "rainbow_lifter": {
        "name": "a rainbow-lifting machine",
        "verb": "build a rainbow-lifting machine",
        "purpose": "raise a rainbow over the celebration",
        "materials": "painted gears, glass hoops, and a silver handle",
        "action": "turn sunlight into a shining arch",
    },
    "giant_kite": {
        "name": "a giant kite engine",
        "verb": "build a giant kite engine",
        "purpose": "pull a banner across the fairground",
        "materials": "bamboo ribs, red cloth, and little brass fans",
        "action": "pull the banner in a smooth circle",
    },
}

PERKS = [
    {
        "id": "song",
        "label": "a cheerful singing perk",
        "effect": "it began singing a loud marching song",
        "surprise": "the song made every loose wheel turn in time",
        "lesson": "test a machine's unexpected gifts before inviting a crowd",
    },
    {
        "id": "bounce",
        "label": "a springy bouncing perk",
        "effect": "it gave every part an enormous bounce",
        "surprise": "the machine hopped like a giant tin frog",
        "lesson": "a useful extra movement still needs a safe stopping place",
    },
    {
        "id": "wind",
        "label": "a pocket-wind perk",
        "effect": "it blew a strong wind from its tiny side fan",
        "surprise": "the wind filled every banner and pushed the machine uphill",
        "lesson": "even a small fan can change a whole plan",
    },
    {
        "id": "glow",
        "label": "a starry glowing perk",
        "effect": "it flashed bright stars from its brass buttons",
        "surprise": "the glowing stars attracted every firefly in the valley",
        "lesson": "a dazzling feature should be checked before it becomes the main event",
    },
]

INTRODUCTIONS = [
    "announced that she would build a machine grand enough to make the mayor's hat wobble",
    "rolled out a blueprint so wide that three dogs used it as shade",
    "declared that ordinary inventions were too small for the coming celebration",
    "told everyone that her next machine would make the clouds curious",
]

@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    owner: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def __post_init__(self) -> None:
        self.meters = dict(self.meters)
        self.memes = dict(self.memes)

    def pronoun(self, case: str = "subject") -> str:
        if self.kind != "character":
            return {"subject": "it", "object": "it", "possessive": "its"}[case]
        if self.type in {"girl", "grandmother", "woman", "aunt"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "uncle", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]


@dataclass
class World:
    place: str
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
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)


@dataclass
class StoryParams:
    place: str
    name: str
    helper: str
    seed: Optional[int] = None


class WorldModel:
    def __init__(self, world: World) -> None:
        self.world = world
        self.events: list[str] = []

    def surprise(self, hero: Entity, machine: Entity, perk: dict, landmark: str) -> None:
        hero.memes["surprise"] = hero.memes.get("surprise", 0) + 1
        machine.memes["wildness"] = machine.memes.get("wildness", 0) + 1
        self.events.append("surprise")
        self.world.say(
            f"Then came the surprise: {perk['surprise']}. "
            f"The machine rolled toward {landmark}, carrying the fair's biggest banner with it."
        )

    def resolve(self, hero: Entity, helper: Entity, machine: Entity, perk: dict, landing: str) -> None:
        hero.memes["understanding"] = hero.memes.get("understanding", 0) + 1
        helper.memes["patience"] = helper.memes.get("patience", 0) + 1
        machine.meters["safety"] = 1
        self.events.append("lesson")
        self.world.say(
            f"{helper.label.capitalize()} caught the loose brake at {landing}, and {hero.label} "
            "added a wooden stop before trying the engine again."
        )
        self.world.say(
            f"The machine did not perform the grand show that day, but it made one small, safe "
            "circle while everyone cheered."
        )
        self.world.say(
            f"By sunset, {hero.label} had learned that {perk['lesson']}."
        )


@dataclass
class Machine:
    id: str
    label: str
    purpose: str
    materials: str
    action: str
    perk: str
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="A tall tale about an engineer, a perk, and a lesson learned."
    )
    parser.add_argument("--place", choices=SETTINGS)
    parser.add_argument("--name")
    parser.add_argument("--helper", choices=HELPERS)
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
    place = args.place or rng.choice(list(SETTINGS))
    name = args.name or rng.choice(NAMES)
    helper = args.helper or rng.choice(HELPERS)
    return StoryParams(place=place, name=name, helper=helper)


def tell(params: StoryParams, rng: random.Random) -> World:
    if params.place not in SETTINGS:
        raise StoryError(f"Unknown place: {params.place}")
    if params.helper not in HELPERS:
        raise StoryError(f"Unknown helper: {params.helper}")
    if not params.name or not params.name.strip():
        raise StoryError("The engineer needs a name.")

    world = World(place=SETTINGS[params.place])
    hero = world.add(
        Entity(
            id="hero",
            kind="character",
            type="girl" if params.name in {"Luna", "Pia", "Nora", "Ivy"} else "boy",
            label=params.name,
            memes={"curiosity": 1, "confidence": 2},
        )
    )
    helper = world.add(
        Entity(
            id="helper",
            kind="character",
            type=params.helper,
            label=params.helper,
            memes={"care": 1},
        )
    )

    plan = rng.choice(list(MACHINE_PLANS.values()))
    perk = rng.choice(PERKS)
    first_count = rng.randint(4, 7)
    second_count = rng.randint(3, 6)
    required = first_count + second_count
    built = required
    landmark, landing = PLACE_DETAILS[params.place]

    machine = world.add(
        Entity(
            id="machine",
            type="engineered_machine",
            label=plan["name"],
            owner=hero.id,
            meters={"sturdiness": 2, "safety": 0},
            memes={"promise": 2},
        )
    )
    perk_entity = world.add(
        Entity(
            id="perk",
            type="perk",
            label=perk["label"],
            owner=hero.id,
            memes={"unexpected": 1},
        )
    )

    world.say(
        f"One bright morning in {world.place}, {hero.label}, a young engineer, "
        f"{rng.choice(INTRODUCTIONS)}."
    )
    world.say(
        f"{hero.label} planned to {plan['verb']} so it could {plan['purpose']} {landmark}. "
        f"The machine would use {plan['materials']} and {plan['action']}."
    )
    world.say(
        f"{helper.label.capitalize()} helped measure {first_count} pieces for the frame and "
        f"{second_count} pieces for the wheels. Together they counted {built} pieces, exactly enough."
    )
    world.para()

    world.say(
        f"While tightening the last copper screw, {hero.label} discovered {perk['label']} "
        "hidden inside the control box."
    )
    world.say(
        f"\"Should we keep it?\" asked {helper.label}. "
        f"\"Of course,\" said {hero.label}. \"A good engineer never wastes a perk!\""
    )
    world.say(
        f"Inside, {hero.label} thought, \"This is perfect. Nothing surprising can happen "
        "inside a machine I built myself.\""
    )
    world.say(
        f"That was a very confident thought, and it was also the wrong thought."
    )

    model = WorldModel(world)
    model.surprise(hero, machine, perk, landmark)
    world.para()

    world.say(
        f"{hero.label} chased the machine past {landing}. \"Turn the silver handle!\" "
        f"called {helper.label}. \"I am turning it!\" answered {hero.label}. "
        "The two voices changed the plan at once: instead of making the machine fly, "
        "they decided to make it stop."
    )
    model.resolve(hero, helper, machine, perk, landing)

    world.say(
        f"At dusk, the repaired machine rested beside {landmark}. Its new wooden stop was plain, "
        f"but it kept the {perk['label']} from racing away, and {hero.label} smiled at the "
        "small circle that proved the lesson had stuck."
    )

    world.facts.update(
        hero=hero,
        helper=helper,
        machine=machine,
        perk=perk,
        perk_entity=perk_entity,
        plan=plan,
        built=built,
        required=required,
        first_count=first_count,
        second_count=second_count,
        landmark=landmark,
        landing=landing,
    )
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f"Write a tall tale about engineer {f['hero'].label} building {f['machine'].label}.",
        f"Tell a child-friendly story where {f['perk']['label']} causes a surprise and teaches a lesson.",
        "Include a brief inner monologue, spoken dialogue, a surprising machine, and a lesson learned.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    helper = f["helper"]
    machine = f["machine"]
    perk = f["perk"]
    return [
        QAItem(
            question=f"What did engineer {hero.label} build, and what was its unexpected perk?",
            answer=(
                f"{hero.label} built {machine.label} to {f['plan']['purpose']}. "
                f"The machine used {f['plan']['materials']}, and its unexpected perk was "
                f"{perk['label']}, which {perk['effect']}."
            ),
        ),
        QAItem(
            question=f"What surprise happened when {hero.label} started the machine?",
            answer=(
                f"When {hero.label} started it, {perk['surprise']}. The machine rolled toward "
                f"{f['landmark']}, so {hero.label} and {helper.label} changed their plan and "
                f"worked together to stop it safely."
            ),
        ),
        QAItem(
            question=f"What lesson did {hero.label} learn?",
            answer=(
                f"{hero.label} learned that {perk['lesson']}. The lesson mattered because the "
                f"unexpected {perk['label']} changed how the machine moved, and a wooden stop "
                "made the repaired machine safe."
            ),
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does an engineer do?",
            answer=(
                "An engineer designs, builds, and tests useful things such as machines, bridges, "
                "and tools."
            ),
        ),
        QAItem(
            question="What is a perk?",
            answer=(
                "A perk is an extra benefit or special feature that comes along with something."
            ),
        ),
        QAItem(
            question="Why should engineers test machines?",
            answer=(
                "Engineers test machines to discover surprises, find unsafe parts, and make the "
                "machines work reliably."
            ),
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    lines.extend(sample.prompts)
    lines.append("")
    lines.append("== story QA ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== world QA ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


ASP_RULES = r"""
role(engineer).
concept(perk).
feature(surprise).
feature(lesson_learned).
feature(inner_monologue).
safe_after_test.
valid_story :- role(engineer), concept(perk), feature(surprise),
                feature(lesson_learned), feature(inner_monologue),
                safe_after_test.
#show valid_story/0.
"""


def asp_facts() -> str:
    import asp
    return "\n".join(
        [
            asp.fact("role", "engineer"),
            asp.fact("concept", "perk"),
            asp.fact("feature", "surprise"),
            asp.fact("feature", "lesson_learned"),
            asp.fact("feature", "inner_monologue"),
            asp.fact("safe_after_test"),
        ]
    )


def asp_program(show: str = "#show valid_story/0.") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    try:
        import asp
    except Exception as exc:
        print(f"ASP unavailable: {exc}")
        return 1

    model = asp.one_model(asp_program())
    atoms = set(asp.atoms(model, "valid_story"))
    if atoms == {()}:
        print("OK: ASP parity matches Python story requirements.")
        return 0
    print("MISMATCH between ASP and Python.")
    print("ASP:", sorted(atoms))
    print("PY:", [()])
    return 1


def generate(params: StoryParams) -> StorySample:
    rng = random.Random(params.seed)
    world = tell(params, rng)
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
        print("\n-- trace --")
        for entity in sample.world.entities.values():
            print(
                f"{entity.id}: type={entity.type} label={entity.label} "
                f"meters={entity.meters} memes={entity.memes}"
            )
    if qa:
        print()
        print(format_qa(sample))


def main() -> None:
    args = build_parser().parse_args()

    if args.verify:
        sys.exit(asp_verify())
    if args.show_asp or args.asp:
        print(asp_program())
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        combos = [
            StoryParams(place=place, name=name, helper=helper, seed=base_seed)
            for place in SETTINGS
            for name in NAMES[:2]
            for helper in HELPERS[:1]
        ]
        samples = [generate(params) for params in combos]
    else:
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

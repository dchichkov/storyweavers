#!/usr/bin/env python3
"""
A small heartwarming storyworld about a careful rescue, a ratchet, and a happy wag.
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

sys.path.insert(
    0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
)
from results import QAItem, StoryError, StorySample  # noqa: E402


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    owner: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)


@dataclass
class Setting:
    place: str
    affords: set[str] = field(default_factory=set)


@dataclass
class StoryState:
    setting: Setting
    entities: dict[str, Entity] = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    facts: dict = field(default_factory=dict)

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
    place: str
    child_name: str
    dog_name: str
    seed: Optional[int] = None
    opening: int = 0
    discovery: int = 0
    reflection: int = 0
    ending: int = 0


SETTINGS = {
    "orchard": Setting("the orchard path", {"cart", "ratchet"}),
    "shed": Setting("the warm shed", {"cart", "ratchet"}),
    "garden": Setting("the garden gate", {"cart", "ratchet"}),
}

CHILD_NAMES = ["Luna", "Mara", "Theo", "Nia", "Pip", "Owen"]
DOG_NAMES = ["Bramble", "Puddle", "Clover", "Moss", "Wicket", "Sunny"]

OPENINGS = [
    "{child} carried a basket past {place} while {dog} trotted beside her.",
    "In the soft gold of afternoon, {child} and {dog} visited {place}.",
    "{child} was helping Aunt Jo near {place}, with {dog} wagging at her heels.",
    "A little breeze moved through {place} as {child} brought {dog} along to help.",
]

DISCOVERIES = [
    {
        "object": "an old garden cart",
        "problem": "one wooden wheel had slipped into a shallow rut",
        "urge": "pull hard and trample the soft flowers beside the path",
        "inner": "If I hurry, I might make the cart move, but I might hurt the flowers too.",
        "tool": "a small ratchet",
        "method": "Aunt Jo showed her how to fit the ratchet onto the loose wheel bolt and turn it one click at a time.",
        "repair": "The wheel rose out of the rut without crushing a single bloom.",
        "lesson": "care can be strong without being rough",
        "ending": "The cart rolled home, and Bramble's tail made a bright, steady wag beside the flowers.",
    },
    {
        "object": "a red wagon",
        "problem": "its handle was caught under a fallen branch",
        "urge": "trample across the herb bed to reach the handle faster",
        "inner": "The shortest way is not always the kindest way.",
        "tool": "a bright steel ratchet",
        "method": "They loosened the branch's little carrier clamp with the ratchet while staying on the stepping stones.",
        "repair": "The branch lifted away, and the wagon came free without bending the herbs.",
        "lesson": "a patient path can protect the things growing nearby",
        "ending": "The red wagon carried fresh herbs home while Clover gave a proud wag.",
    },
    {
        "object": "a handcart",
        "problem": "a small pin had jammed near its axle",
        "urge": "trample the weeds around it and yank until something snapped",
        "inner": "I want to fix this now, but wanting is not the same as knowing how.",
        "tool": "Grandpa's ratchet",
        "method": "Grandpa let her hold the ratchet while he explained each gentle turn.",
        "repair": "The pin slid free, and the handcart stood ready for its next load.",
        "lesson": "asking for help can turn a stuck moment into shared work",
        "ending": "The handcart carried apples toward the porch, followed by Moss's delighted wag.",
    },
    {
        "object": "a blue garden wagon",
        "problem": "its latch had locked beside a muddy puddle",
        "urge": "trample straight through the mud and tug the latch with both hands",
        "inner": "Being brave does not mean making the biggest mess.",
        "tool": "a ratchet with a wooden handle",
        "method": "They laid a plank across the puddle and used the ratchet to loosen the latch from solid ground.",
        "repair": "The wagon opened, and the muddy water stayed below the plank.",
        "lesson": "a steady plan can make room for courage and kindness",
        "ending": "The blue wagon crossed the plank, and Sunny's tail gave a thankful wag.",
    },
]

REFLECTIONS = [
    "{child} thought, I was ready to rush, but the careful way helped everyone.",
    "{child} told herself, A tool is most helpful when a thoughtful person guides it.",
    "{child} wondered, Maybe kindness is not softness alone; maybe it is careful strength.",
    "{child} thought, I did not fix this by myself, but I helped, and that feels wonderful.",
]

ENDINGS = [
    "Aunt Jo smiled, and the children shared the first apples from the cart.",
    "They washed their hands together before carrying the harvest inside.",
    "The rescued wagon rested by the porch, ready for tomorrow's good work.",
    "As evening settled, everyone had a job to do and someone kind beside them.",
]


ASP_RULES = r"""
#show valid/2.
setting(orchard). setting(shed). setting(garden).
affords(orchard,cart). affords(orchard,ratchet).
affords(shed,cart). affords(shed,ratchet).
affords(garden,cart). affords(garden,ratchet).
valid(P,T) :- setting(P), affords(P,T).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for place, setting in SETTINGS.items():
        lines.append(asp.fact("setting", place))
        for item in sorted(setting.affords):
            lines.append(asp.fact("affords", place, item))
    return "\n".join(lines)


def asp_program(show: str = "#show valid/2.") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def python_valid() -> list[tuple[str, str]]:
    return sorted((place, item) for place, setting in SETTINGS.items() for item in setting.affords)


def asp_valid() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program())
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    py = set(python_valid())
    clingo = set(asp_valid())
    if py == clingo:
        print(f"OK: clingo gate matches python gate ({len(py)} combinations).")
        return 0
    print("MISMATCH between clingo and python:")
    print("  only in clingo:", sorted(clingo - py))
    print("  only in python:", sorted(py - clingo))
    return 1


def build_world(params: StoryParams) -> StoryState:
    if params.place not in SETTINGS:
        raise StoryError(f"Unknown place: {params.place}")
    if params.child_name == params.dog_name:
        raise StoryError("The child and dog must have different names.")

    setting = SETTINGS[params.place]
    scene = DISCOVERIES[params.discovery % len(DISCOVERIES)]
    world = StoryState(setting)

    child = world.add(Entity(
        params.child_name,
        kind="character",
        type="child",
        memes={"kindness": 0.6, "impatience": 0.4},
    ))
    dog = world.add(Entity(
        params.dog_name,
        kind="character",
        type="dog",
        memes={"trust": 0.7, "joy": 0.5},
    ))
    aunt = world.add(Entity(
        "Aunt Jo",
        kind="character",
        type="helper",
        memes={"patience": 0.9},
    ))
    cart = world.add(Entity(
        "cart",
        type="vehicle",
        label=scene["object"],
        owner="Aunt Jo",
        meters={"wheel_alignment": 0.2, "distance_to_safety": 2.0},
    ))
    ratchet = world.add(Entity(
        "ratchet",
        type="tool",
        label=scene["tool"],
        owner="Aunt Jo",
        meters={"handle_reach": 0.8},
    ))

    place = setting.place
    world.say(OPENINGS[params.opening % len(OPENINGS)].format(
        child=child.id, dog=dog.id, place=place
    ))
    world.say(f"Near the path, they found {scene['object']}: {scene['problem']}.")
    world.say(
        f'"I can fix it quickly!" {child.id} said. '
        f'"Let us first see what it needs," Aunt Jo replied.'
    )
    world.say(f"{dog.id} gave an uncertain wag and looked from the cart to {child.id}.")

    world.para()
    world.say(f"{child.id} wanted to {scene['urge']}.")
    world.say(scene["inner"])
    world.say(
        f'"Could we use the {scene["tool"]} instead?" {child.id} asked. '
        f'"Yes," said Aunt Jo, "and we can keep our feet on the safe path."'
    )
    world.say(scene["method"])
    world.say(f"{child.id} breathed slowly and turned the tool one careful click at a time.")
    world.say(scene["repair"])
    world.say(f"{dog.id} leaned close, then gave a joyful wag when the wheel moved.")

    world.para()
    world.say(REFLECTIONS[params.reflection % len(REFLECTIONS)].format(child=child.id))
    world.say(
        f'"You helped by noticing the danger and choosing a gentler way," Aunt Jo told {child.id}. '
        f'"And {dog.id} helped by reminding us to stay hopeful."'
    )
    world.say(f'"We fixed it together," {child.id} replied.')
    world.say(ENDINGS[params.ending % len(ENDINGS)])
    world.say(scene["ending"])

    world.facts.update(
        child=child,
        dog=dog,
        helper=aunt,
        cart=cart,
        ratchet=ratchet,
        scene=scene,
        place=place,
        repaired=True,
    )
    return world


def generation_prompts(world: StoryState) -> list[str]:
    f = world.facts
    return [
        f"Write a heartwarming story about {f['child'].id} repairing {f['scene']['object']} in {f['place']}.",
        f"Tell a gentle story with a ratchet, a careful choice not to trample nearby plants, and {f['dog'].id}'s happy wag.",
        f"Write child-friendly dialogue and inner monologue showing how {f['child'].id} learns to repair something with help.",
    ]


def story_qa(world: StoryState) -> list[QAItem]:
    f = world.facts
    scene = f["scene"]
    child = f["child"]
    dog = f["dog"]
    return [
        QAItem(
            question=f"What was wrong with {scene['object']}?",
            answer=f"{scene['object'].capitalize()} had a problem: {scene['problem']}.",
        ),
        QAItem(
            question=f"What did {child.id} first want to do?",
            answer=f"{child.id} wanted to {scene['urge']}, but then realized that rushing could hurt the nearby plants.",
        ),
        QAItem(
            question="How did the ratchet help?",
            answer=f"Aunt Jo showed them how to use {scene['tool']} carefully. {scene['method']}",
        ),
        QAItem(
            question=f"What did {dog.id}'s wag show?",
            answer=f"{dog.id}'s happy wag showed relief and joy when the repair succeeded.",
        ),
        QAItem(
            question=f"What did {child.id} learn?",
            answer=f"{child.id} learned that {scene['lesson']}.",
        ),
    ]


def world_knowledge_qa(world: StoryState) -> list[QAItem]:
    return [
        QAItem(
            question="What is a ratchet?",
            answer="A ratchet is a hand tool that turns a nut or bolt in small controlled steps.",
        ),
        QAItem(
            question="Why should people avoid trampling plants?",
            answer="People should avoid trampling plants because careful footsteps protect living things from being crushed.",
        ),
        QAItem(
            question="What can a dog's wag communicate?",
            answer="A dog's wag can communicate feelings such as excitement, friendliness, or relief, depending on the situation.",
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
    lines.append("== (3) World-knowledge questions ==")
    for item in sample.world_qa:
        lines.extend([f"Q: {item.question}", f"A: {item.answer}"])
    return "\n".join(lines)


def dump_trace(world: StoryState) -> str:
    lines = ["--- world model state ---"]
    for entity in world.entities.values():
        lines.append(
            f"  {entity.id:10} ({entity.type:9}) "
            f"meters={entity.meters} memes={entity.memes}"
        )
    lines.append(f"  facts: {world.facts}")
    return "\n".join(lines)


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    place = args.place or rng.choice(list(SETTINGS))
    child_name = args.child or rng.choice(CHILD_NAMES)
    dog_name = args.dog or rng.choice([name for name in DOG_NAMES if name != child_name])
    return StoryParams(
        place=place,
        child_name=child_name,
        dog_name=dog_name,
        seed=args.seed,
        opening=rng.randrange(len(OPENINGS)),
        discovery=rng.randrange(len(DISCOVERIES)),
        reflection=rng.randrange(len(REFLECTIONS)),
        ending=rng.randrange(len(ENDINGS)),
    )


def generate(params: StoryParams) -> StorySample:
    world = build_world(params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
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


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Heartwarming repair storyworld with a ratchet, a wag, and careful feet."
    )
    parser.add_argument("--place", choices=sorted(SETTINGS))
    parser.add_argument("--child")
    parser.add_argument("--dog")
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


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program())
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        for place, tool in asp_valid():
            print(f"{place:10} {tool}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        for i, place in enumerate(SETTINGS):
            params = StoryParams(
                place=place,
                child_name=CHILD_NAMES[i % len(CHILD_NAMES)],
                dog_name=DOG_NAMES[i % len(DOG_NAMES)],
                discovery=i % len(DISCOVERIES),
                opening=i % len(OPENINGS),
                reflection=i % len(REFLECTIONS),
                ending=i % len(ENDINGS),
                seed=base_seed,
            )
            samples.append(generate(params))
    else:
        seen: set[str] = set()
        for i in range(max(1, args.n) * 30):
            if len(samples) >= max(1, args.n):
                break
            rng = random.Random(base_seed + i)
            params = resolve_params(args, rng)
            params.seed = base_seed + i
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
        if index + 1 < len(samples):
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()

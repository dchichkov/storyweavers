#!/usr/bin/env python3
"""
A gentle ghost story about ing, squoosh, and the kindness of sharing a compliment.
"""

from __future__ import annotations

import argparse
import json
import os
import random
import sys
from dataclasses import dataclass, field
from typing import Optional

_here = os.path.dirname(os.path.abspath(__file__))
_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(_here))))
if not os.path.exists(os.path.join(_root, "results.py")):
    _root = os.path.dirname(os.path.dirname(os.path.dirname(_here)))
sys.path.insert(0, _root)
from results import QAItem, StoryError, StorySample  # noqa: E402


@dataclass(frozen=True)
class Setting:
    id: str
    place: str
    atmosphere: str
    sound: str


@dataclass(frozen=True)
class ObjectChoice:
    id: str
    label: str
    texture: str
    sound: str


@dataclass(frozen=True)
class Spirit:
    id: str
    name: str
    pronoun: str
    favorite: str


@dataclass
class Entity:
    id: str
    kind: str
    label: str
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)


@dataclass
class World:
    setting: Setting
    entities: dict[str, Entity] = field(default_factory=dict)
    facts: dict[str, object] = field(default_factory=dict)
    events: list[str] = field(default_factory=list)
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


SETTINGS = {
    "attic": Setting("attic", "the old attic", "moonlight lay in silver squares", "creak"),
    "hall": Setting("hall", "the quiet hallway", "blue shadows leaned against the walls", "tap"),
    "garden": Setting("garden", "the moonlit garden", "dew shone like tiny stars", "rustle"),
}

OBJECTS = {
    "pillow": ObjectChoice("pillow", "a round velvet pillow", "soft", "squoosh"),
    "blanket": ObjectChoice("blanket", "a patchwork blanket", "warm", "fwump"),
    "cushion": ObjectChoice("cushion", "a striped cushion", "springy", "plop"),
}

SPIRITS = {
    "luna": Spirit("luna", "Luna", "she", "beautiful sounds"),
    "moss": Spirit("moss", "Moss", "they", "kind words"),
    "pip": Spirit("pip", "Pip", "he", "secret songs"),
}

NAMES = ["Mara", "Theo", "Nia", "Sam", "Ivy", "Owen"]


@dataclass
class StoryParams:
    setting: str
    object: str
    spirit: str
    name: str
    seed: Optional[int] = None


def valid_combos() -> list[tuple[str, str, str]]:
    return [(s, o, g) for s in SETTINGS for o in OBJECTS for g in SPIRITS]


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    for field_name, registry in (
        ("setting", SETTINGS),
        ("object", OBJECTS),
        ("spirit", SPIRITS),
    ):
        value = getattr(args, field_name, None)
        if value is not None and value not in registry:
            raise StoryError(f"Unknown {field_name}: {value}")
    choices = [
        combo
        for combo in valid_combos()
        if getattr(args, "setting", None) in (None, combo[0])
        and getattr(args, "object", None) in (None, combo[1])
        and getattr(args, "spirit", None) in (None, combo[2])
    ]
    if not choices:
        raise StoryError("No compatible story choices remain.")
    setting, obj, spirit = rng.choice(choices)
    return StoryParams(
        setting=setting,
        object=obj,
        spirit=spirit,
        name=getattr(args, "name", None) or rng.choice(NAMES),
    )


def build_world(params: StoryParams) -> World:
    setting = SETTINGS[params.setting]
    obj = OBJECTS[params.object]
    spirit = SPIRITS[params.spirit]
    world = World(setting)
    child = world.add(Entity("child", "character", params.name))
    ghost = world.add(Entity("ghost", "spirit", spirit.name))
    prop = world.add(Entity("object", "thing", obj.label))
    child.memes.update({"curiosity": 1.0, "kindness": 0.0, "sharing": 0.0})
    ghost.memes.update({"lonely": 1.0, "relief": 0.0})
    prop.meters.update({"softness": 1.0, "shared": 0.0})
    world.facts.update({
        "child": child,
        "ghost": ghost,
        "object": prop,
        "object_choice": obj,
        "spirit_choice": spirit,
        "compliment_shared": False,
        "squished": False,
    })
    return world


def generate(params: StoryParams) -> StorySample:
    if params.setting not in SETTINGS:
        raise StoryError(f"Unknown setting: {params.setting}")
    if params.object not in OBJECTS:
        raise StoryError(f"Unknown object: {params.object}")
    if params.spirit not in SPIRITS:
        raise StoryError(f"Unknown spirit: {params.spirit}")

    world = build_world(params)
    rng = random.Random(
        params.seed if params.seed is not None else sum(ord(c) for c in params.name)
    )
    child = world.entities["child"]
    ghost = world.entities["ghost"]
    prop = world.entities["object"]
    obj = OBJECTS[params.object]
    spirit = SPIRITS[params.spirit]

    world.say(
        f"At midnight, {params.name} tiptoed into {world.setting.place}, where "
        f"{world.setting.atmosphere}."
    )
    world.say(
        f"A tiny ghost named {spirit.name} floated beside {obj.label}. "
        f"Every time the ghost touched it, the room made a little {obj.sound}."
    )
    world.para()

    world.events.append("ghost_arrived")
    world.say(f"\"Squoosh!\" went the {obj.label}.")
    world.say(
        f"{params.name} jumped, but then smiled. \"That was a wonderful sound,\" "
        f"{params.name} said."
    )
    world.say(
        f"{spirit.name} blinked. \"You really think so?\" the ghost asked. "
        f"\"I do,\" said {params.name}. \"Your squoosh is cheerful.\""
    )
    world.para()

    ghost.memes["lonely"] = 0.0
    ghost.memes["relief"] = 1.0
    child.memes["kindness"] = 1.0
    child.memes["sharing"] = 1.0
    prop.meters["shared"] = 1.0
    world.facts["compliment_shared"] = True
    world.facts["squished"] = True
    world.events.append("compliment_shared")

    world.say(
        f"The compliment warmed the ghost more than any candle. {spirit.name} "
        f"offered the {obj.label}. \"Would you like to share the sound with me?\""
    )
    world.say(
        f"{params.name} pressed the {obj.label}, and together they made it sing: "
        f"\"{obj.sound}, {obj.sound}!\""
    )
    world.say(
        f"Then {params.name} shared the compliment too. \"Anyone who hears your "
        f"sound will know you are good at making lonely rooms feel friendly.\""
    )
    world.para()

    ending = rng.choice([
        f"By dawn, the ghost was no longer lonely, and the last gentle {obj.sound} floated through {world.setting.place}.",
        f"When morning came, {spirit.name} drifted happily beside {obj.label}, carrying the shared compliment like a little lantern.",
        f"The moon slipped away, but the kindness stayed, hiding in every soft {obj.sound}.",
    ])
    world.say(ending)

    story = world.render()
    prompts = [
        "Write a gentle ghost story using ing, squoosh, and compliment.",
        f"Tell a child-friendly ghost story in {world.setting.place} about sharing and kindness.",
        "Write a spooky-but-gentle story where a sound effect helps two friends feel less lonely.",
    ]
    story_qa = [
        QAItem(
            question="Who made the squoosh sound?",
            answer=f"The little ghost named {spirit.name} made the squoosh sound with {obj.label}.",
        ),
        QAItem(
            question=f"What compliment did {params.name} give?",
            answer=f"{params.name} said that the ghost's squoosh was a wonderful and cheerful sound.",
        ),
        QAItem(
            question="How did sharing change the ghost?",
            answer=f"Sharing the {obj.label} and the compliment helped the ghost feel less lonely and more relieved.",
        ),
        QAItem(
            question="What happened at the end?",
            answer=f"At dawn, the ghost and the child were friends, and a gentle {obj.sound} floated through {world.setting.place}.",
        ),
    ]
    world_qa = [
        QAItem(
            question="What is kindness?",
            answer="Kindness means choosing words or actions that help someone feel safe, valued, or less alone.",
        ),
        QAItem(
            question="Why can a compliment help?",
            answer="A sincere compliment can show someone that their effort or special quality has been noticed.",
        ),
        QAItem(
            question="What is sharing?",
            answer="Sharing means allowing another person to enjoy, use, or take part in something with you.",
        ),
        QAItem(
            question="What does a sound effect do in a story?",
            answer="A sound effect helps readers imagine what is happening and can make a moment feel playful, surprising, or spooky.",
        ),
    ]
    return StorySample(
        params=params,
        story=story,
        prompts=prompts,
        story_qa=story_qa,
        world_qa=world_qa,
        world=world,
    )


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for entity in world.entities.values():
        meters = {k: v for k, v in entity.meters.items() if v}
        memes = {k: v for k, v in entity.memes.items() if v}
        lines.append(
            f"{entity.id}: kind={entity.kind}, meters={meters}, memes={memes}"
        )
    lines.append(f"events={world.events}")
    lines.append(f"facts={world.facts}")
    return "\n".join(lines)


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    lines.extend(f"{i}. {p}" for i, p in enumerate(sample.prompts, 1))
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


ASP_RULES = r"""
valid(Setting, Object, Spirit) :-
    setting(Setting),
    object(Object),
    spirit(Spirit).

kindness_resolves(Setting, Object, Spirit) :-
    valid(Setting, Object, Spirit),
    compliment(Spirit),
    sharing(Object),
    sound_effect(Object).
"""


def asp_facts() -> str:
    import asp

    lines = []
    for key in SETTINGS:
        lines.append(asp.fact("setting", key))
    for key in OBJECTS:
        lines.extend([
            asp.fact("object", key),
            asp.fact("sharing", key),
            asp.fact("sound_effect", key),
        ])
    for key in SPIRITS:
        lines.extend([
            asp.fact("spirit", key),
            asp.fact("compliment", key),
        ])
    return "\n".join(lines)


def asp_program(show: str = "#show valid/3.") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program())
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    python_values = set(valid_combos())
    asp_values = set(asp_valid_combos())
    if python_values != asp_values:
        print("ASP/Python parity failure.")
        print("Only in Python:", sorted(python_values - asp_values))
        print("Only in ASP:", sorted(asp_values - python_values))
        return 1
    for setting, obj, spirit in valid_combos()[:5]:
        sample = generate(
            StoryParams(setting, obj, spirit, "Mara", seed=17)
        )
        if not sample.story or "squoosh" not in sample.story.lower():
            print("Generated story exercise failed.")
            return 1
    print(f"OK: ASP matches Python for {len(python_values)} combinations.")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="A gentle ghost story about sharing a compliment."
    )
    parser.add_argument("--setting", choices=sorted(SETTINGS))
    parser.add_argument("--object", choices=sorted(OBJECTS))
    parser.add_argument("--spirit", choices=sorted(SPIRITS))
    parser.add_argument("--name")
    parser.add_argument("-n", type=int, default=1)
    parser.add_argument("--all", action="store_true")
    parser.add_argument("--seed", type=int)
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
        raise SystemExit(asp_verify())
    if args.asp:
        for combo in asp_valid_combos():
            print(combo)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        for setting, obj, spirit in valid_combos():
            samples.append(
                generate(
                    StoryParams(
                        setting=setting,
                        object=obj,
                        spirit=spirit,
                        name="Mara",
                        seed=base_seed,
                    )
                )
            )
    else:
        seen: set[str] = set()
        attempt = 0
        while len(samples) < max(1, args.n):
            seed = base_seed + attempt
            attempt += 1
            params = resolve_params(args, random.Random(seed))
            params.seed = seed
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

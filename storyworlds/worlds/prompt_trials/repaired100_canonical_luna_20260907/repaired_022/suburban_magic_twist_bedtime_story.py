#!/usr/bin/env python3
"""
A small suburban bedtime storyworld about magic, a puzzling twist, and a
kindness that changes the ending.
"""

from __future__ import annotations

import argparse
import json
import random
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

HERE = Path(__file__).resolve()
ROOT = next((p for p in HERE.parents if (p / "results.py").is_file()), HERE.parent)
sys.path.insert(0, str(ROOT))
from results import QAItem, StoryError, StorySample  # noqa: E402


NAME_POOL = ["Luna", "Milo", "Nora", "Theo", "Ivy", "Zoe", "Finn", "Maya"]
HELPER_POOL = ["Grandma", "Dad", "Mom", "Uncle Sam", "Mrs. Bell"]
SUBURBAN_PLACES = ["Maple Street", "Clover Lane", "Juniper Court", "Willow Avenue"]
MAGIC_OBJECTS = ["a moonlit teacup", "a silver key", "a paper star", "a tiny blue lantern"]
TWISTS = ["the magic worked backward", "the spell belonged to a lonely garden gnome", "the smallest wish became the biggest one", "the moon had hidden a message in the shadows"]


@dataclass
class StoryParams:
    name: str = "Luna"
    helper: str = "Grandma"
    place: str = "Maple Street"
    magic_object: str = "a moonlit teacup"
    twist: str = "the magic worked backward"
    seed: Optional[int] = None


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    label: str = ""
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def __post_init__(self) -> None:
        for key in ("glow", "distance", "warmth"):
            self.meters.setdefault(key, 0.0)
        for key in ("wonder", "worry", "courage", "relief", "kindness"):
            self.memes.setdefault(key, 0.0)


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
        return "\n\n".join(" ".join(part) for part in self.paragraphs if part)


def seed_number(params: StoryParams) -> int:
    if params.seed is not None:
        return params.seed
    return int.from_bytes(
        f"{params.name}|{params.helper}|{params.place}|{params.magic_object}|{params.twist}".encode(),
        "little",
    )


def tell_world(params: StoryParams) -> World:
    rng = random.Random(seed_number(params))
    w = World(place=params.place)
    child = w.add(Entity(params.name, "character", params.name))
    helper = w.add(Entity("helper", "character", params.helper))
    magic = w.add(Entity("magic_object", "object", params.magic_object))
    child.memes["wonder"] = 2
    child.meters["distance"] = 4
    magic.meters["glow"] = 1
    w.facts.update(child=child, helper=helper, magic=magic, params=params)

    opening_detail = rng.choice([
        "porch lights blinked softly",
        "sprinklers whispered over sleepy lawns",
        "a faraway dog gave one polite bark",
        "the windows of the houses shone like little stars",
    ])
    w.say(f"On {params.place}, in a quiet suburban neighborhood, {params.name} was getting ready for bed.")
    w.say(f"Outside, {opening_detail}, and the moon rested above the rooftops.")
    w.say(f"Under the pillow, {params.name} found {params.magic_object}.")
    w.say(f"When {params.name} touched it, a thread of magic curled through the room.")
    w.para()

    child.memes["wonder"] += 1
    child.memes["worry"] += 1
    magic.meters["glow"] += 2
    w.say(f"{params.name} whispered, \"I wish everyone on {params.place} could have the sweetest dream tonight.\"")
    w.say(f"{params.helper} stepped into the doorway and asked, \"Did you make a wish, little one?\"")
    w.say(f"\"I did,\" said {params.name}. \"But the magic feels peculiar.\"")
    w.say(f"Then came the twist: {params.twist}.")
    w.say("Instead of filling the houses with dreams, the magic pulled every sleepy sound into one bright little bubble above the street.")
    child.memes["worry"] += 2
    child.meters["distance"] = 7
    w.para()

    w.say(f"{params.helper} sat beside {params.name} and listened carefully.")
    w.say(f"\"Magic sometimes needs a gentle direction,\" said {params.helper}. \"What does the bubble need?\"")
    w.say(f"{params.name} noticed a tiny tear shining inside it. \"It needs someone to hear the lonely dream first.\"")
    w.say(f"Together, they carried {params.magic_object} to the front step and spoke kindly to the bubble.")
    w.say(f"\"You do not have to hold every dream alone,\" {params.name} told it.")
    w.say(f"The bubble opened, and soft dreams floated toward each home like warm feathers.")
    child.memes["courage"] += 2
    child.memes["kindness"] += 2
    child.memes["relief"] += 2
    child.memes["worry"] = 0
    child.meters["distance"] = 1
    magic.meters["glow"] = 5
    magic.meters["warmth"] = 3
    w.para()

    w.say(f"{params.helper} tucked {params.magic_object} safely beside the bed.")
    w.say(f"\"What was the lonely dream?\" asked {params.name}.")
    w.say(f"\"It was waiting for a friend,\" said {params.helper}. \"And tonight, it found one.\"")
    w.say(f"{params.name} smiled as the suburban street grew quiet again.")
    w.say("By morning, every porch held a small silver feather, and nobody remembered seeing it arrive.")
    w.facts.update(
        resolved=True,
        twist=params.twist,
        solution="They listened to the lonely dream and guided the magic with kindness.",
        ending="By morning, every porch held a small silver feather, and nobody remembered seeing it arrive.",
    )
    return w


def generation_prompts(world: World) -> list[str]:
    p: StoryParams = world.facts["params"]
    return [
        f"Write a gentle bedtime story about {p.name} discovering magic on {p.place}.",
        f"Tell a suburban bedtime tale with {p.magic_object}, a surprising twist, and a kind resolution.",
        f"Create a sleepy story in which {p.name} learns that magic works best when someone listens.",
    ]


def story_qa(world: World) -> list[QAItem]:
    p: StoryParams = world.facts["params"]
    return [
        QAItem(
            f"Where does {p.name}'s bedtime adventure happen?",
            f"{p.name}'s adventure happens on {p.place}, in a quiet suburban neighborhood.",
        ),
        QAItem(
            f"What magical object does {p.name} find?",
            f"{p.name} finds {p.magic_object} under the pillow.",
        ),
        QAItem(
            "What surprising twist changes the spell?",
            f"The twist is that {p.twist}; the magic gathers the neighborhood's sleepy sounds into one bubble instead of giving everyone dreams.",
        ),
        QAItem(
            "How do the characters solve the magical problem?",
            "They listen to the lonely dream and guide the magic with kindness, allowing gentle dreams to float to every home.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem("What is a bedtime story?", "A bedtime story is a gentle tale told before sleep to comfort, delight, or spark imagination."),
        QAItem("What is a suburban neighborhood?", "A suburban neighborhood is a place with homes, streets, gardens, and neighbors near a town or city."),
        QAItem("What is a twist in a story?", "A twist is an unexpected change that makes the story mean something new or sends it in a surprising direction."),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== Prompts =="]
    lines.extend(f"{i}. {p}" for i, p in enumerate(sample.prompts, 1))
    lines.append("\n== Story QA ==")
    for item in sample.story_qa:
        lines.extend([f"Q: {item.question}", f"A: {item.answer}"])
    lines.append("\n== World QA ==")
    for item in sample.world_qa:
        lines.extend([f"Q: {item.question}", f"A: {item.answer}"])
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for entity in world.entities.values():
        meters = {k: round(v, 2) for k, v in entity.meters.items() if v}
        memes = {k: round(v, 2) for k, v in entity.memes.items() if v}
        lines.append(f"  {entity.id} ({entity.kind}) meters={meters} memes={memes}")
    lines.append(f"  facts={world.facts}")
    return "\n".join(lines)


ASP_RULES = r"""
dreams_released :- kind(magic_object), listened_to_lonely_dream, kindness_used.
valid_story :- suburban_place, magic_object, twist, dreams_released.
"""


def asp_facts() -> str:
    import asp
    return "\n".join([
        asp.fact("suburban_place", "maple_street"),
        asp.fact("suburban_place", "clover_lane"),
        asp.fact("suburban_place", "juniper_court"),
        asp.fact("suburban_place", "willow_avenue"),
        asp.fact("magic_object", "moonlit_teacup"),
        asp.fact("magic_object", "silver_key"),
        asp.fact("magic_object", "paper_star"),
        asp.fact("magic_object", "tiny_blue_lantern"),
        asp.fact("twist", "magic_works_backward"),
        asp.fact("kind", "magic_object"),
        asp.fact("listened_to_lonely_dream"),
        asp.fact("kindness_used"),
    ])


def asp_program(show: str = "#show valid_story/0.") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    try:
        import asp
        model = asp.one_model(asp_program())
    except Exception as err:
        print(f"ASP unavailable: {err}")
        return 1
    valid = bool(asp.atoms(model, "valid_story"))
    if not valid:
        print("ASP parity failed: valid story was not derived.")
        return 1
    for seed in range(5):
        sample = generate(StoryParams(seed=seed))
        if "twist" not in sample.story.lower() or not sample.world.facts["resolved"]:
            print("Generated-story verification failed.")
            return 1
    print("OK: ASP parity and generated stories verified.")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Suburban magic twist bedtime storyworld.")
    parser.add_argument("--name", choices=NAME_POOL)
    parser.add_argument("--helper", choices=HELPER_POOL)
    parser.add_argument("--place", choices=SUBURBAN_PLACES)
    parser.add_argument("--magic-object", choices=MAGIC_OBJECTS)
    parser.add_argument("--twist", choices=TWISTS)
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
        name=args.name or rng.choice(NAME_POOL),
        helper=args.helper or rng.choice(HELPER_POOL),
        place=args.place or rng.choice(SUBURBAN_PLACES),
        magic_object=args.magic_object or rng.choice(MAGIC_OBJECTS),
        twist=args.twist or rng.choice(TWISTS),
    )


def generate(params: StoryParams) -> StorySample:
    world = tell_world(params)
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


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program())
        return
    if args.verify:
        raise SystemExit(asp_verify())
    if args.asp:
        import asp
        model = asp.one_model(asp_program("#show valid_story/0."))
        print(asp.atoms(model, "valid_story"))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        for i, place in enumerate(SUBURBAN_PLACES):
            params = StoryParams(
                name=NAME_POOL[i % len(NAME_POOL)],
                helper=HELPER_POOL[i % len(HELPER_POOL)],
                place=place,
                magic_object=MAGIC_OBJECTS[i % len(MAGIC_OBJECTS)],
                twist=TWISTS[i % len(TWISTS)],
                seed=base_seed + i,
            )
            samples.append(generate(params))
    else:
        seen: set[str] = set()
        for i in range(max(args.n * 50, 50)):
            if len(samples) >= args.n:
                break
            seed = base_seed + i
            params = resolve_params(args, random.Random(seed))
            params.seed = seed
            sample = generate(params)
            if sample.story not in seen:
                seen.add(sample.story)
                samples.append(sample)

    if args.json:
        print(
            samples[0].to_json()
            if len(samples) == 1
            else json.dumps([sample.to_dict() for sample in samples], indent=2, ensure_ascii=False)
        )
        return

    for index, sample in enumerate(samples):
        emit(
            sample,
            trace=args.trace,
            qa=args.qa,
            header=f"### variant {index + 1}" if len(samples) > 1 else "",
        )
        if index < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()

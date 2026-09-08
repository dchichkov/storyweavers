#!/usr/bin/env python3
"""
A small mythic home story about Luna, a listening hearth, and a surprise visitor.

Seed tale:
---
Luna lived in a little home beneath a hill where the moon touched the chimney.
Each night she swept the hearth and spoke kindly to the quiet house.
One evening, the door answered her greeting with three soft knocks.
Luna asked who was there, but the voice outside only whispered, "I have forgotten my name."
She opened the door and found a small star wrapped in a fallen leaf.
The star had lost its way from the sky. Luna shared warm bread, listened to its story,
and placed it on the chimney. At midnight, the moon lifted the star home.
The next morning, a silver path shone across Luna's floor, so she knew kindness could guide
even a lost light.
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

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if not os.path.exists(os.path.join(ROOT, "results.py")):
    ROOT = os.path.dirname(ROOT)
sys.path.insert(0, ROOT)
from results import QAItem, StoryError, StorySample  # noqa: E402


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    label: str = ""
    type: str = "thing"
    owner: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.kind == "character":
            if self.type in {"girl", "woman", "moon"}:
                return {"subject": "she", "object": "her", "possessive": "her"}[case]
            if self.type in {"boy", "man"}:
                return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class Setting:
    place: str = "Luna's home"
    detail: str = "a round room, a warm hearth, and a chimney beneath the moon"


@dataclass
class StoryParams:
    name: str = "Luna"
    title: str = "the listening hearth"
    seed: Optional[int] = None
    visitor: str = "star"
    house: str = "hill"
    dialogue: int = 0
    surprise: int = 0
    ending: int = 0


@dataclass
class World:
    setting: Setting
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


@dataclass(frozen=True)
class Visitor:
    id: str
    label: str
    lost_sign: str
    gift: str
    home_image: str
    clue: str


@dataclass(frozen=True)
class House:
    id: str
    label: str
    detail: str
    threshold: str


VISITORS = {
    "star": Visitor(
        id="star",
        label="a small fallen star",
        lost_sign="its light flickered instead of shining steadily",
        gift="a thread of silver light",
        home_image="the deep blue sky",
        clue="three bright sparks hidden in the leaf",
    ),
    "moon-moth": Visitor(
        id="moon-moth",
        label="a moon-moth with a torn wing",
        lost_sign="one pale wing trembled whenever it tried to fly",
        gift="a soft dusting of moon-gold",
        home_image="the moonlit garden",
        clue="a tiny crescent pattern on the torn wing",
    ),
    "rain-cloud": Visitor(
        id="rain-cloud",
        label="a little rain cloud in a woolly bundle",
        lost_sign="only one drop fell from it at a time",
        gift="a cool blue bead of rain",
        home_image="the high valley clouds",
        clue="a faint rumble tucked inside the bundle",
    ),
}

HOUSES = {
    "hill": House(
        id="hill",
        label="the hill home",
        detail="a round stone home beneath a grassy hill",
        threshold="a blue door with a brass moon knocker",
    ),
    "forest": House(
        id="forest",
        label="the forest home",
        detail="a little wooden home among whispering pines",
        threshold="a green door with an acorn latch",
    ),
    "shore": House(
        id="shore",
        label="the shore home",
        detail="a white shell home beside a quiet shore",
        threshold="a pearl door with a rope handle",
    ),
}

DIALOGUE_STYLES = (
    (
        '"Good evening," Luna said. "Who is knocking?"',
        '"I do not know," whispered the voice. "I have forgotten my name."',
        '"Then come inside," Luna answered. "We can remember together."',
    ),
    (
        '"The house heard you," Luna said. "Are you afraid?"',
        '"A little," said the voice. "The dark made every road look the same."',
        '"My hearth is small, but it has room for a traveler," Luna said.',
    ),
    (
        '"Tell me what you remember," Luna asked.',
        '"I remember warmth, a shining path, and a home far above," said the visitor.',
        '"Those memories are a map," Luna replied. "We will follow them."',
    ),
)

SURPRISE_STYLES = (
    "When Luna lifted the leaf, she expected a beetle, but a tiny star blinked up at her.",
    "The visitor stepped across the threshold, and the whole home suddenly filled with the smell of rain.",
    "Luna opened the little bundle, expecting a stone, but a moon-moth unfolded one silver wing.",
    "The empty hearth gave a soft golden cough, and a lost light rose from its ashes.",
)

ENDING_STYLES = (
    "In the morning, a silver path crossed Luna's floor from the hearth to the door.",
    "At dawn, the home wore a small shining mark above its threshold, like a promise.",
    "The next day, every quiet corner of the house seemed to know the visitor's name.",
    "When Luna swept the floor, the last bright specks curled into the shape of a tiny welcome.",
)


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Mythic home story world about Luna, dialogue, and surprise.")
    ap.add_argument("--name", choices=["Luna", "Luna Moon"], default="Luna")
    ap.add_argument("--visitor", choices=VISITORS, default=None)
    ap.add_argument("--house", choices=HOUSES, default=None)
    ap.add_argument("--dialogue", type=int, choices=range(len(DIALOGUE_STYLES)), default=None)
    ap.add_argument("--surprise", type=int, choices=range(len(SURPRISE_STYLES)), default=None)
    ap.add_argument("--ending", type=int, choices=range(len(ENDING_STYLES)), default=None)
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("-n", type=int, default=1)
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--trace", action="store_true")
    ap.add_argument("--qa", action="store_true")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--asp", action="store_true")
    ap.add_argument("--verify", action="store_true")
    ap.add_argument("--show-asp", action="store_true")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    return StoryParams(
        name=args.name,
        seed=args.seed,
        visitor=args.visitor or rng.choice(list(VISITORS)),
        house=args.house or rng.choice(list(HOUSES)),
        dialogue=args.dialogue if args.dialogue is not None else rng.randrange(len(DIALOGUE_STYLES)),
        surprise=args.surprise if args.surprise is not None else rng.randrange(len(SURPRISE_STYLES)),
        ending=args.ending if args.ending is not None else rng.randrange(len(ENDING_STYLES)),
    )


def reasonableness_gate(params: StoryParams) -> None:
    if not params.name.strip():
        raise StoryError("Luna needs a name.")
    if params.visitor not in VISITORS:
        raise StoryError("Unknown visitor.")
    if params.house not in HOUSES:
        raise StoryError("Unknown home.")
    if not 0 <= params.dialogue < len(DIALOGUE_STYLES):
        raise StoryError("Unknown dialogue style.")
    if not 0 <= params.surprise < len(SURPRISE_STYLES):
        raise StoryError("Unknown surprise.")
    if not 0 <= params.ending < len(ENDING_STYLES):
        raise StoryError("Unknown ending.")


ASP_RULES = r"""
home(hill).
home(forest).
home(shore).

visitor(star).
visitor(moon_moth).
visitor(rain_cloud).

dialogue.
surprise.

welcomes(hill, star) :- home(hill), visitor(star), dialogue.
welcomes(forest, moon_moth) :- home(forest), visitor(moon_moth), dialogue.
welcomes(shore, rain_cloud) :- home(shore), visitor(rain_cloud), dialogue.

returns_home(star) :- visitor(star), surprise.
returns_home(moon_moth) :- visitor(moon_moth), surprise.
returns_home(rain_cloud) :- visitor(rain_cloud), surprise.

myth_complete(H, V) :- welcomes(H, V), returns_home(V).
#show myth_complete/2.
#show welcomes/2.
#show returns_home/1.
"""


def asp_facts() -> str:
    import asp
    return "\n".join(
        [
            *(asp.fact("home", h) for h in HOUSES),
            *(asp.fact("visitor", v.replace("-", "_")) for v in VISITORS),
            asp.fact("dialogue"),
            asp.fact("surprise"),
        ]
    )


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show myth_complete/2."))
    actual = set(asp.atoms(model, "myth_complete"))
    expected = {("hill", "star"), ("forest", "moon_moth"), ("shore", "rain_cloud")}
    if actual == expected:
        print(f"OK: clingo matches Python myth gate ({len(expected)} complete myths).")
        return 0
    print("MISMATCH")
    print("clingo:", sorted(actual))
    print("python:", sorted(expected))
    return 1


def build_world(params: StoryParams, visitor: Visitor, house: House) -> World:
    setting = Setting(place=house.label, detail=house.detail + ", " + house.threshold)
    world = World(setting)
    luna = world.add(Entity(id="luna", kind="character", label=params.name, type="girl"))
    guest = world.add(Entity(id="guest", kind="character", label=visitor.label, type="visitor"))
    hearth = world.add(Entity(id="hearth", label="the hearth", type="hearth"))
    home = world.add(Entity(id="home", label=house.label, type="home"))

    luna.memes.update({"kindness": 0.0, "wonder": 0.0, "trust": 0.0, "relief": 0.0})
    guest.meters.update({"belonging": 0.1, "light": 0.4, "safety": 0.3})
    hearth.meters.update({"warmth": 0.8, "welcome": 0.2})
    home.meters.update({"quiet": 1.0, "open": 0.0, "magic": 0.2})

    world.say(f"{params.name} lived in {house.detail}.")
    world.say(f"Every evening, {params.name} swept the hearth and spoke gently to the home.")
    world.say(f"The room held {house.threshold}, a round hearth, and a window open to {visitor.home_image}.")
    world.para()

    luna.memes["kindness"] += 0.3
    world.say("One evening, three soft knocks sounded at the door.")
    world.say(SURPRISE_STYLES[params.surprise])
    world.say(f"The visitor was {visitor.label}, and {visitor.lost_sign}.")
    world.say(f"Wrapped in a fallen leaf, it carried the clue: {visitor.clue}.")
    world.say(f"The little home grew quiet, as if it too were waiting for an answer.")
    world.para()

    dialogue = DIALOGUE_STYLES[params.dialogue]
    world.say(dialogue[0])
    world.say(dialogue[1])
    world.say(dialogue[2])
    luna.memes["trust"] += 0.8
    hearth.meters["welcome"] = 1.0
    home.meters["open"] = 1.0
    guest.meters["safety"] = 0.8
    guest.meters["belonging"] = 0.7
    world.say(f"{params.name} shared warm bread and set the visitor beside the hearth.")
    world.say(f"As it ate, the visitor remembered {visitor.home_image}, a path of light, and the sound of its true home.")
    world.para()

    world.say(f"Then {params.name} carried the visitor to the chimney and lifted it toward the night.")
    world.say(f"The moon answered with a pale bridge, and the visitor's lost light rose along it.")
    world.say(f"Before leaving, the visitor gave {params.name} {visitor.gift}.")
    luna.memes["wonder"] += 1.0
    luna.memes["relief"] += 1.0
    guest.meters["light"] = 1.0
    guest.meters["belonging"] = 1.0
    home.meters["magic"] = 1.0
    world.say(ENDING_STYLES[params.ending])
    world.say(f"{params.name} smiled, because a home is not only where someone lives; it is where a lost traveler is welcomed.")
    world.facts.update(
        luna=luna,
        guest=guest,
        hearth=hearth,
        home=home,
        visitor=visitor,
        house=house,
        setting=setting,
    )
    return world


def generation_prompts(world: World) -> list[str]:
    visitor: Visitor = world.facts["visitor"]
    house: House = world.facts["house"]
    return [
        f"Write a gentle myth about Luna welcoming {visitor.label} into {house.label}.",
        "Use dialogue so the visitor's words change what Luna decides to do.",
        "Include a surprising reveal, a warm home, and a magical return home.",
    ]


def story_qa(world: World) -> list[QAItem]:
    visitor: Visitor = world.facts["visitor"]
    house: House = world.facts["house"]
    luna: Entity = world.facts["luna"]
    return [
        QAItem(
            question="Who lived in the home?",
            answer=f"{luna.label} lived in {house.label}, where she cared for the hearth and welcomed travelers.",
        ),
        QAItem(
            question="What surprising visitor came to the door?",
            answer=f"{visitor.label} came to the door, hidden in a fallen leaf and unable to find its way home.",
        ),
        QAItem(
            question="What did the visitor say?",
            answer="The visitor said that it had forgotten its name and needed help remembering its home.",
        ),
        QAItem(
            question="How did Luna help?",
            answer=f"Luna listened, shared warm bread, and used the chimney and moonlight to guide the visitor back to {visitor.home_image}.",
        ),
        QAItem(
            question="What changed at the end?",
            answer=f"The visitor returned home, and {house.label} received a magical sign that kindness had made it a place of welcome.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a home?",
            answer="A home is a place where someone can rest, belong, and feel cared for.",
        ),
        QAItem(
            question="Why is dialogue useful in a story?",
            answer="Dialogue lets characters speak to one another, share knowledge, and change what they decide or do.",
        ),
        QAItem(
            question="What is a surprise in a story?",
            answer="A surprise is an unexpected discovery that changes how a character understands the moment.",
        ),
        QAItem(
            question="What is a myth?",
            answer="A myth is a memorable traditional-style tale that uses wonder, symbols, and magic to explore a meaningful idea.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts =="]
    for i, prompt in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {prompt}")
    lines.append("")
    lines.append("== (2) Story questions ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== (3) World knowledge questions ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for entity in world.entities.values():
        parts = []
        if entity.meters:
            parts.append(f"meters={entity.meters}")
        if entity.memes:
            parts.append(f"memes={entity.memes}")
        lines.append(f"  {entity.id} ({entity.type}) {' '.join(parts)}")
    return "\n".join(lines)


def generate(params: StoryParams) -> StorySample:
    reasonableness_gate(params)
    visitor = VISITORS[params.visitor]
    house = HOUSES[params.house]
    world = build_world(params, visitor, house)
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
        print(asp_program("#show myth_complete/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        model = asp.one_model(asp_program("#show myth_complete/2."))
        print(asp.atoms(model, "myth_complete"))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        index = 0
        for house_id in HOUSES:
            for visitor_id in VISITORS:
                rng = random.Random(base_seed + index)
                params = StoryParams(
                    name="Luna",
                    seed=base_seed + index,
                    visitor=visitor_id,
                    house=house_id,
                    dialogue=rng.randrange(len(DIALOGUE_STYLES)),
                    surprise=rng.randrange(len(SURPRISE_STYLES)),
                    ending=rng.randrange(len(ENDING_STYLES)),
                )
                samples.append(generate(params))
                index += 1
    else:
        for i in range(max(1, args.n)):
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            samples.append(generate(params))

    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([sample.to_dict() for sample in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()

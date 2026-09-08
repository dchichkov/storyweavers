#!/usr/bin/env python3
"""
A child-friendly pirate tale about Joey, a frayed rope, and a wise choice.

Joey wants to help aboard a little pirate ship, but a frayed rope makes
the tempting shortcut unsafe. A careful choice turns a small problem into
a useful lesson learned.
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


PLACES = {
    "cove": "Whispering Cove",
    "island": "Coconut Island",
    "harbor": "Bluebell Harbor",
    "reef": "Moonlit Reef",
}

PLACE_DETAILS = {
    "cove": ("a quiet cove", "a painted rowboat", "a shelf of black rocks"),
    "island": ("a green island", "a crooked palm tree", "a sandy beach"),
    "harbor": ("a busy harbor", "a stack of fish crates", "the old lighthouse"),
    "reef": ("a bright reef", "a floating barrel", "a coral arch"),
}

NAMES = ["Joey", "Milo", "Tess", "Pip", "Nora", "Sam"]
CAPTAINS = ["Captain Mira", "Captain Blue", "Captain Ada", "Captain Finn"]

CHOICES = {
    "inspect": {
        "label": "inspect the rope before using it",
        "verb": "inspected",
        "result": "Joey found the frayed place before anyone climbed",
    },
    "ask": {
        "label": "ask the captain for advice",
        "verb": "asked",
        "result": "the captain showed Joey a safer way",
    },
    "tie": {
        "label": "tie a fresh knot and add a spare rope",
        "verb": "tied",
        "result": "the new knot held while the spare rope made the climb steady",
    },
}


@dataclass
class Entity:
    id: str
    kind: str
    label: str
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)


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


@dataclass
class StoryParams:
    place: str
    name: str
    captain: str
    choice: str = "inspect"
    seed: Optional[int] = None


@dataclass
class StoryModel:
    world: World

    def resolve_rope(self, rope: Entity, choice: dict[str, str], hero: Entity, captain: Entity) -> None:
        rope.memes["danger"] = 0
        rope.meters["strength"] = 1
        hero.memes["confidence"] = hero.memes.get("confidence", 0) + 1
        captain.memes["trust"] = captain.memes.get("trust", 0) + 1
        self.world.say(
            f"Joey {choice['verb']} the rope and used the careful plan. "
            f"{choice['result'].capitalize()}."
        )

    def complete_task(self, hero: Entity, captain: Entity, boat: str, landmark: str) -> None:
        hero.memes["wisdom"] = hero.memes.get("wisdom", 0) + 1
        self.world.say(
            f"Together, Joey and {captain.label} moved the treasure map to {boat}. "
            f"They reached the deck safely and tied it beside {landmark}."
        )
        self.world.say(
            f"Joey smiled. The lesson learned was simple: a brave pirate does not rush "
            "past a warning. A good choice keeps the whole crew safe."
        )


@dataclass
class _Args:
    place: Optional[str] = None
    name: Optional[str] = None
    captain: Optional[str] = None
    choice: Optional[str] = None
    n: int = 1
    seed: Optional[int] = None
    all: bool = False
    trace: bool = False
    qa: bool = False
    json: bool = False
    asp: bool = False
    verify: bool = False
    show_asp: bool = False


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="A pirate tale about Joey and a careful choice.")
    parser.add_argument("--place", choices=sorted(PLACES))
    parser.add_argument("--name", choices=NAMES)
    parser.add_argument("--captain", choices=CAPTAINS)
    parser.add_argument("--choice", choices=sorted(CHOICES))
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
    if args.n < 0:
        raise StoryError("-n cannot be negative")
    return StoryParams(
        place=args.place or rng.choice(sorted(PLACES)),
        name=args.name or rng.choice(NAMES),
        captain=args.captain or rng.choice(CAPTAINS),
        choice=args.choice or rng.choice(sorted(CHOICES)),
    )


def tell(params: StoryParams, rng: random.Random) -> World:
    if params.place not in PLACES:
        raise StoryError(f"unknown place: {params.place}")
    if params.choice not in CHOICES:
        raise StoryError(f"unknown choice: {params.choice}")

    setting, boat, landmark = PLACE_DETAILS[params.place]
    world = World(place=PLACES[params.place])
    hero = world.add(Entity("joey", "character", params.name))
    captain = world.add(Entity("captain", "character", params.captain))
    rope = world.add(Entity("fray", "tool", "the frayed rope"))
    map_entity = world.add(Entity("map", "treasure", "the treasure map"))
    choice = CHOICES[params.choice]

    rope.meters["strength"] = 0.35
    rope.memes["danger"] = 1
    hero.memes["eagerness"] = 1

    world.say(
        f"One breezy morning at {world.place}, {hero.label} sailed with {captain.label} "
        f"to a {setting} in search of a treasure map."
    )
    world.say(
        f"The map was tucked inside {boat}, but the boat had drifted near {landmark}. "
        f"A rope stretched from the ship to the boat, and one part of it was frayed."
    )
    world.say(
        f"Joey grabbed the rope and said, \"I can cross first!\" "
        f"{captain.label} called, \"Wait, Joey. What do you notice?\""
    )
    world.say(
        f"Joey looked again. \"The rope has a fray,\" Joey said. "
        f"\"Then we need a careful choice,\" said {captain.label}."
    )
    world.para()

    model = StoryModel(world)
    model.resolve_rope(rope, choice, hero, captain)
    model.complete_task(hero, captain, boat, landmark)

    world.facts.update(
        hero=hero,
        captain=captain,
        rope=rope,
        map=map_entity,
        boat=boat,
        landmark=landmark,
        choice=choice,
        setting=setting,
    )
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f"Write a pirate tale about {f['hero'].label}, a frayed rope, and a careful choice.",
        "Tell a child-friendly story in which a pirate learns that slowing down can keep friends safe.",
        "Write a short Lesson Learned tale with Joey, a fray, a captain, and a treasure map.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"].label
    captain = f["captain"].label
    choice = f["choice"]["label"]
    return [
        QAItem(
            question=f"What problem did {hero} notice before crossing to the boat?",
            answer=(
                f"{hero} noticed that the rope stretching to the boat had a fray, "
                "so it might not hold a careless climber."
            ),
        ),
        QAItem(
            question=f"What choice did {hero} make with help from {captain}?",
            answer=f"{hero} chose to {choice}, instead of rushing across the unsafe rope.",
        ),
        QAItem(
            question="What lesson did the pirate crew learn?",
            answer=(
                "They learned that a brave pirate should stop at a warning, make a careful "
                "choice, and protect the whole crew before reaching for treasure."
            ),
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a fray?",
            answer="A fray is a place where threads or strands have come loose from rope or cloth.",
        ),
        QAItem(
            question="Why should a pirate inspect a rope?",
            answer="A pirate should inspect a rope to find damage before trusting it with people or supplies.",
        ),
        QAItem(
            question="What is a choice?",
            answer="A choice is a decision between two or more possible actions.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    lines.extend(sample.prompts)
    lines.extend(["", "== story QA =="])
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.extend(["", "== world QA =="])
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


ASP_RULES = r"""
dangerous(rope) :- frayed(rope).
safe_choice(inspect).
safe_choice(ask).
safe_choice(tie).
valid_choice(C) :- safe_choice(C).
lesson_learned :- valid_choice(inspect).
lesson_learned :- valid_choice(ask).
lesson_learned :- valid_choice(tie).
"""


def asp_facts() -> str:
    import asp

    facts = [
        asp.fact("frayed", "rope"),
        *(asp.fact("safe_choice", choice) for choice in CHOICES),
    ]
    return "\n".join(facts)


def asp_program(show: str = "#show lesson_learned/0.") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    try:
        import asp
    except Exception as exc:
        print(f"ASP unavailable: {exc}")
        return 1

    model = asp.one_model(asp_program())
    atoms = set(asp.atoms(model, "lesson_learned"))
    if () in atoms:
        print("OK: ASP lesson parity matches Python.")
        return 0
    print("MISMATCH: ASP did not derive lesson_learned.")
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


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world is not None:
        print("\n-- trace --")
        for entity in sample.world.entities.values():
            print(
                f"{entity.id}: kind={entity.kind} label={entity.label} "
                f"meters={entity.meters} memes={entity.memes}"
            )
    if qa:
        print("\n" + format_qa(sample))


def main() -> None:
    args = build_parser().parse_args()

    if args.verify:
        raise SystemExit(asp_verify())
    if args.show_asp or args.asp:
        print(asp_program())
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        for place in sorted(PLACES):
            for choice in sorted(CHOICES):
                params = StoryParams(
                    place=place,
                    name="Joey",
                    captain="Captain Mira",
                    choice=choice,
                    seed=base_seed,
                )
                samples.append(generate(params))
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

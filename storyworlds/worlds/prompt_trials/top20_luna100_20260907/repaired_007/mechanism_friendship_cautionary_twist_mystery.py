#!/usr/bin/env python3
"""
A small mystery storyworld about a strange mechanism, loyal friends, and a
cautionary twist: careful listening reveals that the apparent danger is a
safety device protecting something precious.
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
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from results import QAItem, StoryError, StorySample  # noqa: E402


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    @property
    def phrase(self) -> str:
        return self.label or self.id.replace("_", " ")


@dataclass
class Place:
    id: str
    label: str
    tags: set[str] = field(default_factory=set)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))


@dataclass
class World:
    place: Place
    entities: dict[str, Entity] = field(default_factory=dict)
    facts: dict[str, object] = field(default_factory=dict)
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


@dataclass(frozen=True)
class Arc:
    key: str
    object_name: str
    clue: str
    danger: str
    mechanism: str
    twist: str
    opening: tuple[str, str]
    discovery: tuple[str, str]
    dialogue: tuple[str, str]
    ending: tuple[str, str]


ARCS = (
    Arc(
        key="clocktower",
        object_name="the brass clockwork bird",
        clue="three soft clicks behind the old clock",
        danger="a spring-loaded beak snapping near a hidden key",
        mechanism="a counterweight lifted the bird only when two small levers were pressed together",
        twist="the bird was not attacking anyone; it was guarding a nest of letters from a child who had once lived there",
        opening=(
            "In the quiet clock tower, {a} and {b} followed three soft clicks behind the old clock.",
            "A brass clockwork bird waited in the dust, with one bright eye turned toward a locked drawer.",
        ),
        discovery=(
            "{a} spotted a thin red thread running from the bird to the floor.",
            "{b} noticed that the thread trembled whenever the tower bell moved.",
        ),
        dialogue=(
            '"Do not pull it yet," said {b}. "A warning can be a clue, not a challenge."',
            '"Then we watch together," said {a}. Their friendship made them patient enough to listen.',
        ),
        ending=(
            "When they pressed the two levers together, the bird rose gently and opened the drawer.",
            "Inside were old letters, safe at last, and the friends left the mechanism undisturbed.",
        ),
    ),
    Arc(
        key="greenhouse",
        object_name="the glasshouse watering machine",
        clue="a silver drip beneath a locked bench",
        danger="a wheel that began turning whenever someone touched the bench",
        mechanism="a hidden float lowered a latch after the water tray became too full",
        twist="the alarming machine was a safety device that stopped the greenhouse from flooding",
        opening=(
            "At the empty greenhouse, {a} and {b} heard a silver drip beneath a locked bench.",
            "A little watering machine shone there, though no gardener stood nearby.",
        ),
        discovery=(
            "{a} saw a line of wet soil leading from the machine to a tray of thirsty seedlings.",
            "{b} found a float bobbing in the tray and a tiny bell tied to its arm.",
        ),
        dialogue=(
            '"If we force the wheel, we may break the garden," said {a}.',
            '"Let us fill the tray slowly and see what the machine is trying to say," replied {b}.',
        ),
        ending=(
            "The float rose, the wheel stopped, and every seedling received just enough water.",
            "The friends smiled at the quiet bell, wiser about strange tools and careful choices.",
        ),
    ),
    Arc(
        key="lighthouse",
        object_name="the lantern-room mechanism",
        clue="a blue flash beneath the lighthouse stairs",
        danger="a metal arm swinging across the narrow passage",
        mechanism="a turning gear shifted the arm away only when the lamp shutter was closed",
        twist="the moving arm marked a safe path for rescuers during storms",
        opening=(
            "Near the lighthouse stairs, {a} and {b} saw a blue flash beneath the lantern room.",
            "A metal arm swept across the passage, then vanished behind a panel.",
        ),
        discovery=(
            "{a} found salt on the gear teeth and footprints near the emergency lamp.",
            "{b} read a faded arrow: close the shutter before crossing.",
        ),
        dialogue=(
            '"Running past it would be foolish," said {b}.',
            '"We will follow the arrow together," said {a}. "Friends do not hurry one another into danger."',
        ),
        ending=(
            "They closed the shutter, and the mechanism swung the arm aside to reveal a safe stair.",
            "At the top, the lamp blinked over the sea, showing why the mystery had needed care.",
        ),
    ),
)


@dataclass
class StoryParams:
    place: str
    hero_name: str
    friend_name: str
    hero_gender: str = "boy"
    friend_gender: str = "girl"
    seed: Optional[int] = None
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))


PLACES = {
    "clock_tower": Place("clock_tower", "the quiet clock tower", {"old", "mysterious"}),
    "greenhouse": Place("greenhouse", "the empty greenhouse", {"glass", "growing"}),
    "lighthouse": Place("lighthouse", "the windy lighthouse", {"sea", "storm"}),
}

NAMES = {
    "boy": ["Leo", "Milo", "Sam", "Theo"],
    "girl": ["Luna", "Mia", "Nora", "Zoe"],
}

CURATED = [
    StoryParams("clock_tower", "Milo", "Luna", "boy", "girl"),
    StoryParams("greenhouse", "Theo", "Nora", "boy", "girl"),
    StoryParams("lighthouse", "Luna", "Sam", "girl", "boy"),
]


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="A friendship mystery about a hidden mechanism.")
    parser.add_argument("--place", choices=PLACES)
    parser.add_argument("--hero")
    parser.add_argument("--friend")
    parser.add_argument("--hero-gender", choices=NAMES)
    parser.add_argument("--friend-gender", choices=NAMES)
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
    hero_gender = args.hero_gender or rng.choice(list(NAMES))
    friend_gender = args.friend_gender or ("girl" if hero_gender == "boy" else "boy")
    hero = args.hero or rng.choice(NAMES[hero_gender])
    choices = [name for name in NAMES[friend_gender] if name != hero]
    friend = args.friend or rng.choice(choices)
    return StoryParams(
        place=args.place or rng.choice(list(PLACES)),
        hero_name=hero,
        friend_name=friend,
        hero_gender=hero_gender,
        friend_gender=friend_gender,
    )


def tell(params: StoryParams) -> World:
    if params.place not in PLACES:
        raise StoryError(f"Unknown place: {params.place}.")
    if params.hero_name == params.friend_name:
        raise StoryError("The two friends must have different names.")
    if params.hero_gender not in NAMES or params.friend_gender not in NAMES:
        raise StoryError("Both genders must be boy or girl.")

    rng = random.Random(params.seed if params.seed is not None else sum(map(ord, params.place)))
    arc = ARCS[rng.randrange(len(ARCS))]
    world = World(PLACES[params.place])
    hero = world.add(Entity("hero", "character", params.hero_gender, params.hero_name))
    friend = world.add(Entity("friend", "character", params.friend_gender, params.friend_name))
    machine = world.add(Entity("mechanism", "device", "mechanism", arc.object_name))
    clue = world.add(Entity("clue", "thing", "clue", arc.clue))

    values = {"a": hero.phrase, "b": friend.phrase}
    for line in arc.opening:
        world.say(line.format(**values))
    world.para()

    hero.memes["curiosity"] += 1
    friend.memes["caution"] += 1
    machine.meters["hidden"] = 1
    for line in arc.discovery:
        world.say(line.format(**values))
    world.para()

    hero.meters["observed"] += 1
    friend.meters["observed"] += 1
    hero.memes["trust"] += 1
    friend.memes["trust"] += 1
    for line in arc.dialogue:
        world.say(line.format(**values))
    world.para()

    machine.meters["understood"] = 1
    machine.meters["safe"] = 1
    hero.memes["relief"] += 1
    friend.memes["relief"] += 1
    for line in arc.ending:
        world.say(line.format(**values))

    world.facts.update(
        hero=hero.phrase,
        friend=friend.phrase,
        object_name=arc.object_name,
        clue=arc.clue,
        danger=arc.danger,
        mechanism=arc.mechanism,
        twist=arc.twist,
        ending=arc.ending[-1].format(**values),
        arc=arc.key,
    )
    return world


def generate(params: StoryParams) -> StorySample:
    world = tell(params)
    facts = world.facts
    return StorySample(
        params=params,
        story=world.render(),
        prompts=[
            "Write a child-friendly mystery about a mechanism and two friends who choose caution.",
            f"Tell a mystery in {world.place.label} where {facts['clue']} leads to a safe discovery.",
            "Include a surprising but gentle twist showing that careful friendship prevented harm.",
        ],
        story_qa=[
            QAItem(
                "What first made the friends curious?",
                f"They became curious when they noticed {facts['clue']} near {facts['object_name']}."
            ),
            QAItem(
                "Why did the friends avoid forcing the mechanism?",
                f"They avoided forcing it because it seemed connected to {facts['danger']}; careful observation was safer."
            ),
            QAItem(
                "What was the mystery's twist?",
                f"The twist was that {facts['twist']}. The strange mechanism was protecting something rather than causing trouble."
            ),
            QAItem(
                "How did friendship help?",
                f"{facts['hero']} and {facts['friend']} shared clues, listened to each other, and waited until they understood {facts['mechanism']}."
            ),
        ],
        world_qa=[
            QAItem(
                "What is a mechanism?",
                "A mechanism is a set of moving parts that works together to perform a job."
            ),
            QAItem(
                "Why can caution be useful?",
                "Caution gives people time to notice risks and choose a safer action instead of rushing."
            ),
        ],
        world=world,
    )


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for entity in world.entities.values():
        meters = {k: v for k, v in entity.meters.items() if v}
        memes = {k: v for k, v in entity.memes.items() if v}
        lines.append(
            f"  {entity.id}: type={entity.type} meters={meters} memes={memes}"
        )
    return "\n".join(lines)


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts =="]
    lines.extend(f"{i}. {prompt}" for i, prompt in enumerate(sample.prompts, 1))
    lines.append("")
    lines.append("== (2) Story questions ==")
    for item in sample.story_qa:
        lines.extend([f"Q: {item.question}", f"A: {item.answer}"])
    lines.append("")
    lines.append("== (3) World-knowledge questions ==")
    for item in sample.world_qa:
        lines.extend([f"Q: {item.question}", f"A: {item.answer}"])
    return "\n".join(lines)


ASP_RULES = r"""
device(mechanism).
observed(hero).
observed(friend).
cautious(friend).
understood(mechanism) :- observed(hero), observed(friend), cautious(friend).
safe(mechanism) :- understood(mechanism).
outcome(protected) :- safe(mechanism).
"""


def asp_facts() -> str:
    import asp
    return "\n".join(
        [
            asp.fact("device", "mechanism"),
            asp.fact("observed", "hero"),
            asp.fact("observed", "friend"),
            asp.fact("cautious", "friend"),
        ]
    )


def asp_program(show: str = "#show outcome/1.") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    try:
        model = asp.one_model(asp_program())
        if not asp.atoms(model, "outcome"):
            print("ASP parity failed: no protected outcome.")
            return 1
        sample = generate(StoryParams("clock_tower", "Milo", "Luna", seed=3))
        if "mechanism" not in sample.story.lower() and "clockwork" not in sample.story.lower():
            print("Generation parity failed: mechanism absent.")
            return 1
        if not sample.story_qa:
            print("Generation parity failed: missing questions.")
            return 1
    except Exception as exc:
        print(f"Verification failed: {exc}")
        return 1
    print("OK: smoke tests passed.")
    return 0


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
        model = asp.one_model(asp_program())
        print(asp.atoms(model, "outcome"))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    if args.all:
        samples = [generate(params) for params in CURATED]
    else:
        samples = []
        seen: set[str] = set()
        for index in range(max(1, args.n)):
            rng = random.Random(base_seed + index)
            params = resolve_params(args, rng)
            params.seed = base_seed + index
            sample = generate(params)
            if sample.story in seen:
                continue
            seen.add(sample.story)
            samples.append(sample)

    if args.json:
        payload = samples[0].to_dict() if len(samples) == 1 else [sample.to_dict() for sample in samples]
        print(json.dumps(payload, indent=2, ensure_ascii=False))
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

#!/usr/bin/env python3
"""
A small mystery storyworld about a curious mechanism, friendship, and a
cautionary twist. Two friends investigate a hidden clockwork signal and learn
that careful questions can protect a secret place.
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


THRESHOLD = 1.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    role: str = ""
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
class MysteryArc:
    key: str
    object_name: str
    opening: tuple[str, str]
    clue: tuple[str, str]
    question: tuple[str, str]
    twist: tuple[str, str]
    ending: tuple[str, str]
    mechanism: str
    danger: str
    solution: str


ARCS = (
    MysteryArc(
        key="silver_latch",
        object_name="a silver latch",
        opening=(
            "In {place}, {a} and {b} found a silver latch hidden beneath a loose floorboard.",
            "A tiny arrow on it pointed toward the old bell tower.",
        ),
        clue=(
            "When {a} touched the latch, a soft click answered from inside the wall.",
            "{b} noticed three dusty footprints leading away from it.",
        ),
        question=(
            '"Should we follow the footprints?" asked {a}.',
            '"Only after we learn what the latch does," said {b}. "A mystery can hide a warning."',
        ),
        twist=(
            "Together they turned the latch one careful notch and heard the bell tower door unlock.",
            "But the mechanism also released a row of loose bricks above the path.",
        ),
        ending=(
            "{b} spotted the danger, and the friends stepped back before the bricks fell.",
            "Behind the safe door they found a lost birdhouse key, not treasure, and returned it to the caretaker.",
        ),
        mechanism="a silver latch that unlocked the bell tower and loosened a row of bricks",
        danger="loose bricks could fall onto anyone rushing beneath them",
        solution="they turned the latch slowly, noticed the loose bricks, and moved away before helping the caretaker",
    ),
    MysteryArc(
        key="whisper_wheel",
        object_name="a wooden wheel",
        opening=(
            "In {place}, {a} and {b} discovered a wooden wheel behind a curtain of ivy.",
            "A thread tied to its handle disappeared into the dark garden shed.",
        ),
        clue=(
            "The wheel gave one whispering click whenever the wind touched it.",
            "{a} found a tiny painted moon on its rim, while {b} found a second moon on the shed door.",
        ),
        question=(
            '"Maybe the wheel opens the shed," said {a}.',
            '"Maybe," replied {b}, "but we should tell someone before we pull a hidden thread."',
        ),
        twist=(
            "They called the gardener and turned the wheel together while he watched.",
            "The mechanism lifted the shed latch, but it also pulled a net across the doorway.",
        ),
        ending=(
            "The gardener stopped the net before it snapped shut, and he thanked the friends for waiting.",
            "Inside was a box of moon-shaped labels for the garden plants, so the mystery helped everyone name the flowers.",
        ),
        mechanism="a wooden wheel that lifted a latch and pulled a hidden net",
        danger="a net could snap across the doorway",
        solution="they brought the gardener, turned the wheel slowly, and stopped the net safely",
    ),
    MysteryArc(
        key="blue_pin",
        object_name="a blue pin",
        opening=(
            "In {place}, {a} found a blue pin tucked inside an old map case.",
            "Its point fit a round hole beside the community garden gate.",
        ),
        clue=(
            "A faint humming came from the gate when the pin was held nearby.",
            "{b} saw that the map marked a circle around the pond, not a path through it.",
        ),
        question=(
            '"The pin must open something," said {a}.',
            '"Let us read the map first," said {b}. "A map may tell us where not to step."',
        ),
        twist=(
            "They inserted the pin gently, and a small mechanism opened a panel in the gate.",
            "Inside the panel, a spring-loaded rake swung across the muddy shortcut.",
        ),
        ending=(
            "The friends stayed behind the line marked on the map until the rake settled.",
            "The panel held a note explaining that the rake protected new seedlings, and their careful friendship saved the garden.",
        ),
        mechanism="a blue pin that opened a panel and moved a spring-loaded rake",
        danger="the rake could sweep across the muddy shortcut",
        solution="they followed the map's warning, stayed behind the line, and waited for the rake to settle",
    ),
    MysteryArc(
        key="clockwork_key",
        object_name="a clockwork key",
        opening=(
            "In {place}, {a} and {b} spotted a clockwork key beneath a bench.",
            "Its brass teeth matched a little box beside the fountain.",
        ),
        clue=(
            "The box ticked three times, then stopped whenever a shadow crossed it.",
            "{b} found a message scratched underneath: Please ask before opening.",
        ),
        question=(
            '"We could turn the key now," said {a}.',
            '"We could," said {b}, "but the message is part of the mystery, too."',
        ),
        twist=(
            "They asked the fountain keeper, who let them turn the key one notch.",
            "The mechanism opened the box, but a bright alarm bell rang for the whole square.",
        ),
        ending=(
            "The keeper quickly quieted the bell and smiled because the friends had followed the note.",
            "The box contained a missing signal flag, and their caution brought it back to the town parade.",
        ),
        mechanism="a clockwork key that opened a box and rang a bright alarm bell",
        danger="the alarm could frighten people and bring everyone running",
        solution="they asked the fountain keeper, turned the key one notch, and let him quiet the alarm",
    ),
)


PLACES = {
    "bell_tower": Place("bell_tower", "the old bell tower", {"tower", "public"}),
    "garden_shed": Place("garden_shed", "the community garden", {"garden", "public"}),
    "town_square": Place("town_square", "the quiet town square", {"square", "public"}),
    "library_yard": Place("library_yard", "the library yard", {"yard", "public"}),
}

NAMES = {
    "boy": ["Milo", "Theo", "Finn", "Arlo", "Sam"],
    "girl": ["Luna", "Maya", "Nora", "Ivy", "Zoe"],
}


@dataclass
class StoryParams:
    place: str
    hero_name: str
    friend_name: str
    hero_gender: str = "girl"
    friend_gender: str = "boy"
    seed: Optional[int] = None
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))


def valid_combos() -> list[tuple[str, str]]:
    return [(place, arc.key) for place in PLACES for arc in ARCS]


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    hero_gender = args.hero_gender or rng.choice(["girl", "boy"])
    friend_gender = args.friend_gender or ("boy" if hero_gender == "girl" else "girl")
    hero_name = args.hero or rng.choice(NAMES[hero_gender])
    choices = [name for name in NAMES[friend_gender] if name != hero_name]
    friend_name = args.friend or rng.choice(choices)
    return StoryParams(
        place=args.place or rng.choice(list(PLACES)),
        hero_name=hero_name,
        friend_name=friend_name,
        hero_gender=hero_gender,
        friend_gender=friend_gender,
    )


def tell(params: StoryParams) -> World:
    if params.place not in PLACES:
        raise StoryError(f"Unknown place: {params.place}.")
    if params.hero_name == params.friend_name:
        raise StoryError("The two friends must have different names.")
    if params.hero_gender not in NAMES or params.friend_gender not in NAMES:
        raise StoryError("Each character must have a supported gender.")

    rng = random.Random(params.seed if params.seed is not None else 0)
    arc = ARCS[rng.randrange(len(ARCS))]
    place = PLACES[params.place]
    world = World(place)
    hero = world.add(Entity(params.hero_name, "character", params.hero_gender, params.hero_name, "hero"))
    friend = world.add(Entity(params.friend_name, "character", params.friend_gender, params.friend_name, "friend"))
    mechanism = world.add(Entity("mechanism", "object", "mechanism", arc.object_name, "mystery"))
    mechanism.meters["hidden"] = 1.0
    mechanism.meters["dangerous"] = 1.0
    hero.memes["curious"] = 1.0
    friend.memes["careful"] = 1.0

    values = {"place": place.label, "a": hero.phrase, "b": friend.phrase}
    for line in arc.opening:
        world.say(line.format(**values))
    world.para()

    mechanism.meters["clue_found"] = 1.0
    for line in arc.clue:
        world.say(line.format(**values))
    world.para()

    for line in arc.question:
        world.say(line.format(**values))
    world.para()

    mechanism.meters["tested"] = 1.0
    mechanism.meters["danger_revealed"] = 1.0
    for line in arc.twist:
        world.say(line.format(**values))
    world.para()

    mechanism.meters["safe"] = 1.0
    mechanism.meters["solved"] = 1.0
    hero.memes["trust"] += 1.0
    friend.memes["trust"] += 1.0
    hero.memes["joy"] += 1.0
    friend.memes["joy"] += 1.0
    for line in arc.ending:
        world.say(line.format(**values))

    world.facts.update(
        hero=hero,
        friend=friend,
        mechanism=mechanism,
        place=place,
        arc=arc,
        danger=arc.danger,
        solution=arc.solution,
        ending=arc.ending[-1].format(**values),
    )
    return world


def generate(params: StoryParams) -> StorySample:
    world = tell(params)
    facts = world.facts
    return StorySample(
        params=params,
        story=world.render(),
        prompts=[
            "Write a child-friendly mystery about a strange mechanism and two friends who investigate carefully.",
            f"Tell a cautionary friendship story set in {facts['place'].label} where {facts['mechanism'].phrase} hides a surprise.",
            "Write a mystery with a twist that shows why asking questions before touching a mechanism is wise.",
        ],
        story_qa=[
            QAItem(
                "What mystery did the friends investigate?",
                f"They investigated {facts['mechanism'].phrase}. Clues showed that it was connected to {facts['danger']}."
            ),
            QAItem(
                "What caution did the friends learn?",
                f"They learned to ask questions and move slowly because {facts['danger']}. Their careful plan was that {facts['solution']}."
            ),
            QAItem(
                "How did friendship help solve the mystery?",
                f"{facts['hero'].phrase} and {facts['friend'].phrase} shared clues and listened to each other. Their trust helped them stay safe and solve the mystery."
            ),
            QAItem(
                "What proved the story had a happy ending?",
                f"The final image showed the change: {facts['ending']}"
            ),
        ],
        world_qa=[
            QAItem(
                "What is a mechanism?",
                "A mechanism is a set of parts that work together to make something move, open, close, or signal."
            ),
            QAItem(
                "Why is caution useful near a strange machine?",
                "Caution is useful because a machine may move suddenly or hide a danger. People can ask questions, read clues, and get help before touching it."
            ),
        ],
        world=world,
    )


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


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for entity in world.entities.values():
        meters = {key: value for key, value in entity.meters.items() if value}
        memes = {key: value for key, value in entity.memes.items() if value}
        lines.append(
            f"  {entity.id:10} ({entity.type:10}) "
            f"meters={meters} memes={memes}"
        )
    return "\n".join(lines)


ASP_RULES = r"""
clue_found(M) :- mechanism(M), hidden(M), clue(M).
danger_revealed(M) :- mechanism(M), tested(M), dangerous(M).
safe(M) :- danger_revealed(M), careful_friend(F), asks(F).
solved(M) :- safe(M), clue_found(M).
outcome(solved) :- mechanism(M), solved(M).
"""


def asp_facts() -> str:
    import asp
    facts = [
        asp.fact("mechanism", "mechanism"),
        asp.fact("hidden", "mechanism"),
        asp.fact("dangerous", "mechanism"),
        asp.fact("clue", "mechanism"),
        asp.fact("tested", "mechanism"),
        asp.fact("careful_friend", "friend"),
        asp.fact("asks", "friend"),
    ]
    return "\n".join(facts)


def asp_program(show: str = "#show outcome/1.") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show outcome/1."))
    return asp.atoms(model, "outcome")


def asp_verify() -> int:
    import asp
    try:
        model = asp.one_model(asp_program())
        if ("solved",) not in asp.atoms(model, "outcome"):
            print("ASP parity failed: mechanism was not solved.")
            return 1
    except Exception as exc:
        print(f"ASP smoke test failed: {exc}")
        return 1

    try:
        params = StoryParams("bell_tower", "Luna", "Milo", seed=7)
        sample = generate(params)
        if not sample.story.strip() or "mechanism" not in sample.story.lower():
            print("Generation smoke test failed.")
            return 1
    except Exception as exc:
        print(f"Generation smoke test failed: {exc}")
        return 1

    print("OK: smoke tests passed.")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="A cautious friendship mystery about a mechanism.")
    parser.add_argument("--place", choices=sorted(PLACES))
    parser.add_argument("--hero")
    parser.add_argument("--friend")
    parser.add_argument("--hero-gender", choices=["boy", "girl"])
    parser.add_argument("--friend-gender", choices=["boy", "girl"])
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


def emit(sample: StorySample, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world is not None:
        print()
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
        print(asp_valid_combos())
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        curated = [
            StoryParams("bell_tower", "Luna", "Milo", seed=base_seed),
            StoryParams("garden_shed", "Maya", "Theo", seed=base_seed + 1),
            StoryParams("town_square", "Nora", "Finn", seed=base_seed + 2),
            StoryParams("library_yard", "Ivy", "Arlo", seed=base_seed + 3),
        ]
        samples = [generate(params) for params in curated]
    else:
        seen: set[str] = set()
        for offset in range(max(args.n * 20, 20)):
            if len(samples) >= args.n:
                break
            seed = base_seed + offset
            params = resolve_params(args, random.Random(seed))
            params.seed = seed
            sample = generate(params)
            if sample.story in seen:
                continue
            seen.add(sample.story)
            samples.append(sample)

    if not samples:
        raise StoryError("No stories could be generated.")

    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([sample.to_dict() for sample in samples], indent=2, ensure_ascii=False))
        return

    for index, sample in enumerate(samples, 1):
        emit(
            sample,
            trace=args.trace,
            qa=args.qa,
            header=f"### variant {index}" if len(samples) > 1 else "",
        )
        if index < len(samples):
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()

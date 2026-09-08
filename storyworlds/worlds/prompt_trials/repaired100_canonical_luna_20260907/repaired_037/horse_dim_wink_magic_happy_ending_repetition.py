#!/usr/bin/env python3
"""
A tiny fairy-tale world about a dim horse, a magical wink, and the value of
trying a kind solution more than once.
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

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
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
    name: str
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
    hero_name: str
    horse_name: str
    seed: Optional[int] = None
    trial: int = 0
    opening: int = 0
    dialogue: int = 0
    ending: int = 0


SETTINGS = {
    "moon_meadow": Setting("the moon meadow", {"grass", "starlight"}),
    "rose_road": Setting("the rose road", {"grass", "starlight"}),
    "castle_lane": Setting("the castle lane", {"grass", "starlight"}),
}

HERO_NAMES = ["Luna", "Mira", "Elian", "Pia", "Nora", "Tomas"]
HORSE_NAMES = ["Brindle", "Clover", "Dapple", "Hazel", "Pipkin", "Silver"]

OPENINGS = [
    "At the edge of {place}, Princess {hero} found a horse named {horse}.",
    "Once, beneath a pale moon, {hero} walked along {place} and heard a soft hoofbeat.",
    "In a little kingdom, {hero} met {horse} beside {place} just before sunset.",
    "Every evening, {hero} visited {place}, where {horse} waited beneath the first star.",
]

TRIALS = [
    {
        "problem": "The horse's lantern-bright coat had grown horse-dim, and the road to the castle lost its glow.",
        "magic": "a silver star slept inside the horse's left eyelid",
        "action": "offer the horse a warm apple and ask it to wink kindly",
        "response": "The horse tried one wink, but its eyelid only trembled.",
        "clue": "a tiny silver spark appeared whenever the horse heard a gentle voice",
        "fix": "They would repeat the kind greeting until the magic remembered its way home.",
        "ending": "At the third wink, the hidden star opened like a flower.",
        "lesson": "kind magic may need patience and another try",
    },
    {
        "problem": "The horse-dim fog had covered the bridge, so even the castle bells sounded far away.",
        "magic": "a moonstone was tucked beneath the horse's blue mane",
        "action": "brush the mane and invite the horse to wink at the bridge",
        "response": "The first wink made one small silver puddle in the fog.",
        "clue": "the fog thinned each time the horse felt safe",
        "fix": "They repeated the gentle brushing and the quiet invitation, never pulling or shouting.",
        "ending": "On the third wink, the bridge shone from end to end.",
        "lesson": "a calm heart can make room for a second chance",
    },
    {
        "problem": "A dark spell had made the horse dim, and the kingdom's flowers folded their sleepy heads.",
        "magic": "a golden eyelash carried the queen's forgotten blessing",
        "action": "sing a small song and ask the horse for one brave wink",
        "response": "The horse gave a wink, but only one daisy lifted its head.",
        "clue": "more flowers opened whenever the song was sung softly",
        "fix": "They sang the same kind song again, then again, while the horse listened.",
        "ending": "The third wink sent golden color dancing through every flower.",
        "lesson": "repeating a gentle effort can wake hidden hope",
    },
]

DIALOGUES = [
    (
        '"Why are you so dim, dear horse?" {hero} asked.',
        '"I remember the light," said {horse}, "but I need someone patient."',
    ),
    (
        '"May I try a little magic?" {hero} whispered.',
        '"Try kindly," replied {horse}. "Magic listens to kindness."',
    ),
    (
        '"Should we stop after one wink?" asked {hero}.',
        '"Not if the first try was gentle," said {horse}. "We can try once more."',
    ),
]

ENDINGS = [
    '"You were never truly lost," {hero} told {horse}. "You only needed time."',
    '"The light was waiting in you," {hero} said. The horse answered with a happy wink.',
    '"We tried, listened, and tried again," {hero} said. "That is a fine kind of courage."',
]


ASP_RULES = r"""
#show valid/2.
setting(moon_meadow). setting(rose_road). setting(castle_lane).
affords(moon_meadow,grass). affords(moon_meadow,starlight).
affords(rose_road,grass). affords(rose_road,starlight).
affords(castle_lane,grass). affords(castle_lane,starlight).
valid(P,A) :- setting(P), affords(P,A).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for name, setting in SETTINGS.items():
        lines.append(asp.fact("setting", name))
        for affordance in sorted(setting.affords):
            lines.append(asp.fact("affords", name, affordance))
    return "\n".join(lines)


def asp_program(show: str = "#show valid/2.") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def python_valid() -> list[tuple[str, str]]:
    return sorted((place, affordance) for place, setting in SETTINGS.items()
                  for affordance in setting.affords)


def asp_valid() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program())
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    py = set(python_valid())
    clingo = set(asp_valid())
    if py == clingo:
        print(f"OK: clingo gate matches python gate ({len(py)} combinations).")
        for _ in range(3):
            params = StoryParams("moon_meadow", "Luna", "Brindle")
            sample = generate(params)
            if not sample.story.strip():
                print("Generated story was empty.")
                return 1
        return 0
    print("MISMATCH between clingo and python:")
    print("  only in clingo:", sorted(clingo - py))
    print("  only in python:", sorted(py - clingo))
    return 1


def build_world(params: StoryParams) -> StoryState:
    if params.place not in SETTINGS:
        raise StoryError(f"Unknown place: {params.place}.")
    if params.hero_name == params.horse_name:
        raise StoryError("The hero and horse must have different names.")

    setting = SETTINGS[params.place]
    trial = TRIALS[params.trial % len(TRIALS)]
    world = StoryState(setting)
    hero = world.add(Entity(params.hero_name, "character", "child",
                            memes={"hope": 1.0, "patience": 0.0}))
    horse = world.add(Entity(params.horse_name, "character", "horse",
                             memes={"light": 0.2, "trust": 0.4},
                             meters={"brightness": 0.2}))
    star = world.add(Entity("hidden_star", "thing", "magic",
                            owner=horse.id, meters={"brightness": 1.0}))
    world.facts.update(hero=hero, horse=horse, star=star, trial=trial)

    world.say(OPENINGS[params.opening % len(OPENINGS)].format(
        place=setting.name, hero=hero.id, horse=horse.id
    ))
    world.say(trial["problem"])
    world.say(f"{hero.id} noticed that {trial['magic']}.")
    first, second = DIALOGUES[params.dialogue % len(DIALOGUES)]
    world.say(first.format(hero=hero.id, horse=horse.id))
    world.say(second.format(hero=hero.id, horse=horse.id))

    world.para()
    world.say(f"{hero.id} decided to {trial['action']}.")
    world.say(trial["response"])
    world.say(f"Then {hero.id} saw that {trial['clue']}.")
    world.say(f"{hero.id} tried again. {trial['fix']}")
    world.say(f"The same kind words were spoken once, twice, and three times.")
    world.say(trial["ending"])

    horse.meters["brightness"] = 1.0
    horse.memes["trust"] = 1.0
    hero.memes["patience"] = 1.0
    world.facts["resolved"] = True

    world.para()
    world.say(ENDINGS[params.ending % len(ENDINGS)].format(hero=hero.id, horse=horse.id))
    world.say(
        f"The {horse.id} trotted beside {hero.id}, bright enough to guide every traveler home."
    )
    world.say(f"And whenever the road grew dim, {horse.id} gave a cheerful wink.")
    return world


def generation_prompts(world: StoryState) -> list[str]:
    trial = world.facts["trial"]
    return [
        f"Write a fairy tale about {world.facts['horse'].id}, a horse-dim horse who discovers magic.",
        f"Tell a happy-ending story in {world.setting.name} where a wink and repeated kindness restore light.",
        f"Write a child-friendly fairy tale with dialogue, magic, repetition, and a horse that becomes bright again.",
    ]


def story_qa(world: StoryState) -> list[QAItem]:
    hero = world.facts["hero"]
    horse = world.facts["horse"]
    trial = world.facts["trial"]
    return [
        QAItem("Who helped the dim horse?", f"{hero.id} helped {horse.id} by listening, speaking kindly, and trying again."),
        QAItem("What magical sign helped solve the problem?", f"The horse's wink revealed the magic and helped restore its hidden light."),
        QAItem("Why did the first attempt not solve everything?", f"The first attempt was gentle, but the magic needed patience and another try."),
        QAItem("What happened after the repeated kind effort?", trial["ending"]),
        QAItem("What lesson did the story teach?", f"The story taught that {trial['lesson']}."),
    ]


def world_knowledge_qa(world: StoryState) -> list[QAItem]:
    return [
        QAItem("What is a horse?", "A horse is a large animal with four legs that people can care for and sometimes ride."),
        QAItem("What is a wink?", "A wink is a brief closing of one eye, often used as a friendly signal."),
        QAItem("What does a happy ending mean?", "A happy ending is a conclusion in which the main problem is safely resolved and the characters find joy or peace."),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts =="]
    lines.extend(f"{i}. {prompt}" for i, prompt in enumerate(sample.prompts, 1))
    lines.append("\n== (2) Story questions ==")
    for item in sample.story_qa:
        lines.extend([f"Q: {item.question}", f"A: {item.answer}"])
    lines.append("\n== (3) World-knowledge questions ==")
    for item in sample.world_qa:
        lines.extend([f"Q: {item.question}", f"A: {item.answer}"])
    return "\n".join(lines)


def dump_trace(world: StoryState) -> str:
    lines = ["--- world model state ---"]
    for entity in world.entities.values():
        lines.append(
            f"  {entity.id:12} ({entity.type:8}) "
            f"meters={entity.meters} memes={entity.memes}"
        )
    lines.append(f"  setting: {world.setting.name}")
    lines.append(f"  facts: resolved={world.facts.get('resolved', False)}")
    return "\n".join(lines)


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    place = args.place or rng.choice(list(SETTINGS))
    hero = args.name or rng.choice(HERO_NAMES)
    horse = args.horse or rng.choice(HORSE_NAMES)
    if hero == horse:
        horse = rng.choice([name for name in HORSE_NAMES if name != hero])
    return StoryParams(
        place=place,
        hero_name=hero,
        horse_name=horse,
        seed=args.seed,
        trial=rng.randrange(len(TRIALS)),
        opening=rng.randrange(len(OPENINGS)),
        dialogue=rng.randrange(len(DIALOGUES)),
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
    parser = argparse.ArgumentParser(description="Fairy-tale world of a magical horse-dim wink.")
    parser.add_argument("--place", choices=sorted(SETTINGS))
    parser.add_argument("--name")
    parser.add_argument("--horse")
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
        raise SystemExit(asp_verify())
    if args.asp:
        for place, affordance in asp_valid():
            print(f"{place:12} {affordance}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        for place in SETTINGS:
            samples.append(generate(StoryParams(
                place=place,
                hero_name="Luna",
                horse_name="Brindle",
                trial=list(SETTINGS).index(place) % len(TRIALS),
            )))
    else:
        seen: set[str] = set()
        for index in range(max(1, args.n) * 30):
            if len(samples) >= max(1, args.n):
                break
            rng = random.Random(base_seed + index)
            params = resolve_params(args, rng)
            params.seed = base_seed + index
            sample = generate(params)
            if sample.story not in seen:
                seen.add(sample.story)
                samples.append(sample)

    if args.json:
        payload = samples[0].to_dict() if len(samples) == 1 else [sample.to_dict() for sample in samples]
        print(json.dumps(payload, indent=2, ensure_ascii=False))
        return

    for index, sample in enumerate(samples):
        emit(sample, trace=args.trace, qa=args.qa,
             header=f"### variant {index + 1}" if len(samples) > 1 else "")
        if index + 1 < len(samples):
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()

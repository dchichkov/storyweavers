#!/usr/bin/env python3
"""
A small mythic storyworld about sweat, a stubborn mountain gate, and solving
a conflict before the sun reaches its highest point.

Seed word: sweat
Features: Problem Solving, Conflict, Foreshadowing
Style: Myth
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


PLACES = [
    "the Valley of Seven Bells",
    "the hill beneath the sleeping sun",
    "the cedar pass",
    "the moonlit mountain road",
]
HERO_NAMES = ["Luna", "Mira", "Aster", "Nera", "Solin", "Tavi"]
HELPER_NAMES = ["Orin", "Pella", "Kato", "Ilya", "Bram", "Suri"]
HERO_KINDS = ["young moon-keeper", "village runner", "apprentice star-reader", "goat-herder"]
HELPER_KINDS = ["bronze-smith", "stone-cutter", "wind-listener", "keeper of old songs"]
TOOLS = ["a cedar lever", "a braided rope", "a bronze wedge", "a smooth river stone"]
OMENS = [
    "a red line appeared around the sun before dawn",
    "three crows flew west and would not call",
    "the oldest bell trembled without being touched",
    "a cool star vanished from the morning sky",
]
ENDINGS = [
    "When the gate opened, a bright river of sun spilled across the valley.",
    "The mountain breathed out warm light, and every bell below answered.",
    "Behind the gate lay a spring that shone like a piece of dawn.",
    "The valley filled with gold, and even the quarrel seemed small beneath it.",
]
LESSONS = [
    "They learned that strength can move a stone, but listening finds the place to push.",
    "They learned that a warning is not a command to fear; it is an invitation to prepare.",
    "They learned that solving a problem together can mend the friendship damaged by blame.",
    "They learned that old songs often hide practical wisdom inside beautiful words.",
]


@dataclass
class Entity:
    id: str
    kind: str
    label: str
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)


@dataclass
class Setting:
    place: str
    danger: str = "the sun-gate may remain shut"


@dataclass
class Mood:
    conflict: bool = True
    foreshadowing: bool = True
    solved: bool = False


@dataclass
class StoryParams:
    place: str
    hero_name: str
    hero_kind: str
    helper_name: str
    helper_kind: str
    seed: Optional[int] = None


class World:
    def __init__(self, setting: Setting, mood: Mood) -> None:
        self.setting = setting
        self.mood = mood
        self.entities: dict[str, Entity] = {}
        self.facts: dict[str, object] = {}
        self.lines: list[list[str]] = [[]]

    def add(self, entity: Entity) -> Entity:
        self.entities[entity.id] = entity
        return entity

    def say(self, text: str) -> None:
        if text:
            self.lines[-1].append(text)

    def para(self) -> None:
        if self.lines[-1]:
            self.lines.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(part) for part in self.lines if part)


def tell(params: StoryParams) -> World:
    if params.hero_name == params.helper_name:
        raise StoryError("hero and helper must have different names")
    if not params.place:
        raise StoryError("a myth needs a named place")

    world = World(Setting(params.place), Mood())
    hero = world.add(Entity(params.hero_name, "hero", params.hero_kind))
    helper = world.add(Entity(params.helper_name, "helper", params.helper_kind))
    gate = world.add(Entity("sun_gate", "relic", "the stone sun-gate"))
    rng = random.Random(
        params.seed
        if params.seed is not None
        else "|".join(
            [params.place, params.hero_name, params.hero_kind, params.helper_name, params.helper_kind]
        )
    )
    tool = rng.choice(TOOLS)
    omen = rng.choice(OMENS)
    ending = rng.choice(ENDINGS)
    lesson = rng.choice(LESSONS)
    riddle = rng.choice(
        [
            "The gate opens for the hand that pushes where the shadow points.",
            "A mountain yields when two feet stand on opposite sides of the same promise.",
            "Do not fight the stone's face; find the crack beneath its pride.",
        ]
    )

    hero.meters.update(strength=2.0, sweat=0.0)
    hero.memes.update(courage=1.0, frustration=0.0)
    helper.meters.update(strength=1.0)
    helper.memes.update(worry=1.0, trust=0.5)
    gate.meters.update(weight=10.0, opening=0.0)

    world.say(
        f"In {world.setting.place}, the people said that the first light of each day slept behind a stone sun-gate."
    )
    world.say(
        f"One morning, {omen}, and the elders warned that {world.setting.danger}."
    )
    world.say(
        f"{params.hero_name}, a {params.hero_kind}, climbed toward the gate with {params.helper_name}, a {params.helper_kind}."
    )
    world.para()
    world.say(
        f"The gate was sealed by a round stone wheel, and no one could move it. Sweat gathered on {params.hero_name}'s brow as they pushed."
    )
    world.say(
        f'"Push harder!" cried {params.hero_name}. "The sun will not wait for your old songs."'
    )
    world.say(
        f'"And your hurried pushing will crack the wheel," answered {params.helper_name}. "You never listen when you are afraid."'
    )
    world.say(
        f"The words struck harder than the stone. {params.hero_name} accused {params.helper_name} of being timid, while {params.helper_name} accused {params.hero_name} of turning every warning into a contest."
    )
    world.para()
    world.say(
        f"Then {params.hero_name} noticed that the sweat falling from the brow made dark dots on the dust. Each dot rested beneath a narrow groove in the gate."
    )
    world.say(
        f"The old omen returned to memory, and {params.helper_name} sang the riddle: {riddle}"
    )
    world.say(
        f'{params.hero_name} lowered the {tool} and asked, "What do the grooves tell us?"'
    )
    world.say(
        f'{params.helper_name} replied, "They form a path. We should stop fighting the gate and work with its weight."'
    )
    world.say(
        f"Together they placed the {tool} beneath the shadowed edge, tied the rope around the wheel, and waited until their breathing matched."
    )
    world.say(
        f"On the third pull, the wheel shifted. The sweat, fear, and anger that had divided them became a shared rhythm."
    )
    world.para()
    world.say(
        f"{params.hero_name} said, " + '"I was trying to be brave by refusing to listen."'
    )
    world.say(
        f"{params.helper_name} answered, " + '"And I was hiding fear inside my warning. I should have shown you the path."'
    )
    world.say(
        f"They pulled once more, not as rivals but as guardians of the valley. The stone sun-gate opened."
    )
    world.say(f"{ending} {lesson}")
    world.say(
        f"From that day onward, when sweat shone on their brows, {params.hero_name} and {params.helper_name} remembered that a difficult stone might be asking for a wiser hand."
    )

    hero.meters["sweat"] = 1.0
    hero.memes.update(courage=1.0, frustration=0.0, trust=1.0)
    helper.memes.update(worry=0.0, trust=1.0)
    gate.meters["opening"] = 1.0
    world.mood.solved = True
    world.facts.update(
        hero=hero,
        helper=helper,
        gate=gate,
        tool=tool,
        omen=omen,
        riddle=riddle,
        ending=ending,
        lesson=lesson,
    )
    return world


def generation_prompts(world: World) -> list[str]:
    return [
        f"Write a myth set in {world.setting.place} where sweat reveals a clue.",
        "Include a conflict between two helpers that changes through problem solving.",
        "Foreshadow the solution with an omen, an old riddle, or a repeated natural sign.",
    ]


def story_questions(world: World) -> list[QAItem]:
    hero = world.facts["hero"]
    helper = world.facts["helper"]
    return [
        QAItem(
            question=f"Why did {hero.id} and {helper.id} argue?",
            answer=f"They argued because {hero.id} wanted to push the sun-gate harder, while {helper.id} feared that hurried force would crack the wheel. Their fear turned into blame.",
        ),
        QAItem(
            question="What foreshadowed the way to open the gate?",
            answer=f"The omen and the sweat-dots revealed the hidden grooves. The old riddle also warned them to follow the gate's shadowed path instead of fighting its face.",
        ),
        QAItem(
            question="How did they solve the problem?",
            answer=f"They placed the {world.facts['tool']} beneath the shadowed edge, tied a rope around the wheel, matched their breathing, and pulled together.",
        ),
        QAItem(
            question="How did the conflict change?",
            answer=f"They admitted their mistakes. The hero had refused to listen, and the helper had hidden fear inside a warning, so they chose to work as guardians rather than rivals.",
        ),
        QAItem(
            question="What happened when the gate opened?",
            answer=world.facts["ending"],
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is sweat?",
            answer="Sweat is salty water made by the body when it becomes hot or works hard.",
        ),
        QAItem(
            question="What is foreshadowing?",
            answer="Foreshadowing is a clue placed earlier in a story that hints at something important later.",
        ),
        QAItem(
            question="What is problem solving?",
            answer="Problem solving means understanding a difficulty, testing an idea, and choosing a useful way forward.",
        ),
    ]


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for entity in world.entities.values():
        meters = {k: v for k, v in entity.meters.items() if v}
        memes = {k: v for k, v in entity.memes.items() if v}
        details = []
        if meters:
            details.append(f"meters={meters}")
        if memes:
            details.append(f"memes={memes}")
        lines.append(f"  {entity.id} ({entity.label}) {' '.join(details)}")
    return "\n".join(lines)


def format_qa(sample: StorySample) -> str:
    lines = ["== Generation prompts =="]
    lines.extend(f"{i}. {prompt}" for i, prompt in enumerate(sample.prompts, 1))
    lines.append("")
    lines.append("== Story questions ==")
    for item in sample.story_qa:
        lines.extend([f"Q: {item.question}", f"A: {item.answer}"])
    lines.append("")
    lines.append("== World knowledge ==")
    for item in sample.world_qa:
        lines.extend([f"Q: {item.question}", f"A: {item.answer}"])
    return "\n".join(lines)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Mythic sweat, conflict, and problem-solving storyworld.")
    parser.add_argument("--place", choices=PLACES)
    parser.add_argument("--hero-name")
    parser.add_argument("--helper-name")
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
    hero_name = args.hero_name or rng.choice(HERO_NAMES)
    helper_choices = [name for name in HELPER_NAMES if name != hero_name]
    helper_name = args.helper_name or rng.choice(helper_choices)
    if hero_name == helper_name:
        raise StoryError("hero and helper must have different names")
    return StoryParams(
        place=args.place or rng.choice(PLACES),
        hero_name=hero_name,
        hero_kind=rng.choice(HERO_KINDS),
        helper_name=helper_name,
        helper_kind=rng.choice(HERO_KINDS + HELPER_KINDS),
    )


def generate(params: StoryParams) -> StorySample:
    world = tell(params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_questions(world),
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


def asp_facts() -> str:
    return "\n".join(
        [
            "domain(myth).",
            "feature(sweat).",
            "feature(problem_solving).",
            "feature(conflict).",
            "feature(foreshadowing).",
            "resolved(conflict, problem_solving).",
            "reveals(sweat, clue).",
            "opens(problem_solving, sun_gate).",
        ]
    )


ASP_RULES = r"""
valid_world :-
    domain(myth),
    feature(sweat),
    feature(problem_solving),
    feature(conflict),
    feature(foreshadowing),
    resolved(conflict, problem_solving),
    reveals(sweat, clue),
    opens(problem_solving, sun_gate).
#show valid_world/0.
"""


def asp_program(show: str = "#show valid_world/0.") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp

    model = asp.one_model(asp_program())
    values = set(asp.atoms(model, "valid_world"))
    if values == {()}:
        params = StoryParams(
            place=PLACES[0],
            hero_name="Luna",
            hero_kind=HERO_KINDS[0],
            helper_name="Orin",
            helper_kind=HELPER_KINDS[0],
            seed=17,
        )
        sample = generate(params)
        required = ["sweat", "gate", "riddle", "together"]
        if all(word in sample.story.lower() for word in required):
            print("OK: ASP facts, Python world, and generated story agree.")
            return 0
        print("MISMATCH: generated story omitted a required narrative element")
        return 1
    print(f"MISMATCH: ASP model was {values}")
    return 1


def main() -> None:
    args = build_parser().parse_args()
    if args.n < 1:
        raise StoryError("-n must be at least 1")
    if args.show_asp:
        print(asp_program())
        return
    if args.asp:
        import asp

        model = asp.one_model(asp_program())
        print("\n".join(str(atom) for atom in model))
        return
    if args.verify:
        raise SystemExit(asp_verify())

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        rng = random.Random(base_seed)
        params = resolve_params(args, rng)
        params.seed = base_seed
        samples.append(generate(params))
    else:
        seen: set[str] = set()
        attempt = 0
        while len(samples) < args.n and attempt < max(50, args.n * 20):
            rng = random.Random(base_seed + attempt)
            params = resolve_params(args, rng)
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
            print(json.dumps([sample.to_dict() for sample in samples], indent=2, ensure_ascii=False))
        return

    for index, sample in enumerate(samples):
        emit(
            sample,
            trace=args.trace,
            qa=args.qa,
            header=f"### story {index + 1}" if len(samples) > 1 else "",
        )
        if index < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()

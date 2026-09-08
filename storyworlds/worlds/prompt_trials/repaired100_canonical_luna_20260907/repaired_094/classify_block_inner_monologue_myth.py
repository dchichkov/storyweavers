#!/usr/bin/env python3
"""
A small mythic storyworld about a child who must classify a strange stone
before an old block can be moved from the village spring.
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
import random
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from results import QAItem, StoryError, StorySample  # noqa: E402


@dataclass
class Entity:
    id: str
    kind: str
    label: str
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)
    region: str = ""


@dataclass
class Setting:
    name: str
    affordances: set[str] = field(default_factory=set)


@dataclass
class World:
    setting: Setting
    entities: dict[str, Entity] = field(default_factory=dict)
    facts: dict[str, object] = field(default_factory=dict)
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


TALES = [
    {
        "place": "the moonlit spring",
        "stone": "a warm blue stone",
        "mark": "a pale spiral",
        "block": "the old stone block",
        "danger": "the spring had begun to whisper beneath it",
        "classification": "a moon-stone, a keeper of water",
        "cause": "the block was not a fallen wall stone; it was a sleeping seal",
        "action": "placed the moon-stone in the spiral hollow",
        "result": "the block lifted like a slow eyelid",
        "image": "clear water rose, carrying a silver reflection of the moon",
    },
    {
        "place": "the valley shrine",
        "stone": "a red-speckled stone",
        "mark": "three little cuts",
        "block": "the gate block",
        "danger": "the shrine path was closing as roots curled around it",
        "classification": "a hearth-stone, warm with the memory of a fire",
        "cause": "the block guarded an ancient root gate",
        "action": "held the hearth-stone against the three cuts",
        "result": "the roots loosened and the gate block rolled aside",
        "image": "red light glowed under the roots, and the village path opened",
    },
    {
        "place": "the hill of bells",
        "stone": "a green-veined stone",
        "mark": "a tiny bell shape",
        "block": "the bell block",
        "danger": "the hill bells had fallen silent before the storm",
        "classification": "a wind-stone, made to wake sleeping bells",
        "cause": "the block covered the mouth of the hill's first bell",
        "action": "set the wind-stone beside the bell shape",
        "result": "the block trembled and slid down the grassy slope",
        "image": "one deep bell note crossed the valley and frightened the storm away",
    },
    {
        "place": "the cedar cave",
        "stone": "a white stone with a dark stripe",
        "mark": "a closed eye",
        "block": "the cave block",
        "danger": "the cave animals could not reach their winter store",
        "classification": "a dream-stone, a gentle key for hidden doors",
        "cause": "the block sealed the cave's sleeping doorway",
        "action": "laid the dream-stone beneath the closed eye",
        "result": "the block sank into the floor without a sound",
        "image": "warm seeds gleamed in the cave while the animals curled safely beside them",
    },
    {
        "place": "the river of stars",
        "stone": "a black stone dusted with gold",
        "mark": "a five-pointed star",
        "block": "the river block",
        "danger": "the river had stopped carrying its starlit boats",
        "classification": "a sky-stone, heavy with a fallen star",
        "cause": "the block was a sleeping giant's hand across the riverbed",
        "action": "placed the sky-stone beneath the star mark",
        "result": "the giant hand opened and the river ran again",
        "image": "the little star boats sailed toward dawn",
    },
]


def build_world(params: "StoryParams") -> World:
    tale = TALES[params.tale_index % len(TALES)]
    setting = Setting(tale["place"], {"observe", "classify", "move", "listen"})
    world = World(setting)

    hero = world.add(Entity(
        "hero", "child", params.name,
        meters={"steps": 0.0, "careful_checks": 0.0},
        memes={"wonder": 1.0, "doubt": 0.0, "courage": 0.0, "relief": 0.0},
        region=tale["place"],
    ))
    elder = world.add(Entity(
        "elder", "guide", params.guide,
        meters={"staff_taps": 0.0},
        memes={"patience": 1.0, "trust": 1.0},
        region=tale["place"],
    ))
    stone = world.add(Entity(
        "mystery_stone", "artifact", tale["stone"],
        meters={"warmth": 1.0, "weight": 1.0},
        memes={"mystery": 1.0},
        region=tale["place"],
    ))
    block = world.add(Entity(
        "block", "barrier", tale["block"],
        meters={"weight": 3.0, "stillness": 1.0},
        memes={"sleep": 1.0},
        region=tale["place"],
    ))

    world.facts.update(
        tale=tale,
        hero=hero,
        elder=elder,
        stone=stone,
        block=block,
        classified=False,
        block_moved=False,
        listened=False,
        solved=False,
    )
    return world


def narrate(params: "StoryParams") -> World:
    world = build_world(params)
    f = world.facts
    tale = f["tale"]
    hero: Entity = f["hero"]
    elder: Entity = f["elder"]
    stone: Entity = f["stone"]

    openings = [
        f"In the first hour before sunrise, {hero.label} came to {world.setting.name}, where {tale['block']} lay across the path.",
        f"The people said that {world.setting.name} had once answered every honest question. That morning, {hero.label} found {tale['block']} blocking its way.",
        f"Long ago, the valley gave names to every thing. Only {tale['stone']} beside {tale['block']} had no name yet.",
        f"When the sky was still violet, {hero.label} heard the old warning from {world.setting.name}: {tale['danger']}.",
    ]
    world.say(openings[params.route % len(openings)])
    world.say(f"Beside the barrier rested {stone.label}, bearing {tale['mark']}.")
    world.say(f"{hero.label} touched it, then pulled back. The stone was warm, though the morning air was cold.")
    world.para()

    hero.memes["doubt"] += 1.0
    world.say(f'"Do not move the {tale["block"]} yet," {elder.label} said. "First, learn what the stone is."')
    world.say(f"{hero.label} looked inward: *If I call it wrongly, I may wake what sleeps beneath the block.*")
    world.say(f'"How can I know its kind?" {hero.label} asked.')
    world.say(f'"Classify it by what it does," {elder.label} replied. "A name should follow a truth, not replace one."')
    world.say(f"{hero.label} listened for a pulse, felt the warmth, and traced {tale['mark']}.")
    hero.meters["careful_checks"] += 3.0
    f["listened"] = True
    world.para()

    f["classified"] = True
    hero.memes["courage"] += 1.0
    world.say(f"{hero.label} understood: the stone was {tale['classification']}.")
    world.say(f"Inside, {hero.label} thought, *The block is part of the question. I must not fight it as if it were only a wall.*")
    world.say(f'"I know its class now," {hero.label} said. "It belongs with the mark."')
    world.say(f'"Then give the stone its true place," {elder.label} said, and stepped back.')
    world.say(f"{hero.label} {tale['action']}.")
    world.say(f"The earth answered. {tale['cause']}; {tale['result']}.")
    f["block_moved"] = True
    f["solved"] = True
    hero.memes["relief"] += 1.0
    world.para()

    world.say(f"{tale['image']}.")
    world.say(f"{hero.label} carried the lesson home: to classify a mystery is to notice its nature, and a careful name can show the way through a block.")
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    tale = f["tale"]
    return [
        f"Write a mythic child-facing tale at {world.setting.name} where a child must classify {tale['stone']} before moving {tale['block']}.",
        f"Tell a myth about a block, a marked stone, and an inner monologue that changes the hero's choice.",
        f"Write a story in which the hero learns that classification means discovering what a thing truly does.",
    ]


def story_questions(world: World) -> list[QAItem]:
    f = world.facts
    tale = f["tale"]
    hero: Entity = f["hero"]
    elder: Entity = f["elder"]
    return [
        QAItem(
            f"What was blocking the way at {world.setting.name}?",
            f"{tale['block']} was blocking the way. It was important because it was connected to the mystery beneath the marked stone.",
        ),
        QAItem(
            f"How did {hero.label} classify the strange stone?",
            f"{hero.label} listened to the stone, felt its warmth, and traced {tale['mark']}. Those observations showed that it was {tale['classification']}.",
        ),
        QAItem(
            f"What advice did {elder.label} give?",
            f"{elder.label} told {hero.label} to learn what the stone was before trying to move the block. The guide said a true name should follow careful observation.",
        ),
        QAItem(
            "How was the problem solved?",
            f"The problem was solved when the correctly classified stone was placed where it belonged. Then {tale['result']}.",
        ),
        QAItem(
            "What did the hero learn?",
            f"The hero learned that classifying something means noticing its nature and purpose. A careful understanding can reveal how to pass a barrier safely.",
        ),
    ]


def world_questions(world: World) -> list[QAItem]:
    return [
        QAItem(
            "What does it mean to classify something?",
            "To classify something means to decide what kind of thing it is by noticing its important qualities.",
        ),
        QAItem(
            "What is an inner monologue?",
            "An inner monologue is the private stream of thoughts a character has inside their mind.",
        ),
        QAItem(
            "What is a myth?",
            "A myth is an old-style story that uses extraordinary events to explain a truth, a custom, or the nature of the world.",
        ),
        QAItem(
            "Why can a block be more than an obstacle in a story?",
            "A block can also hide a secret, protect something, or show that a character must understand a problem before acting.",
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
    lines.append("== (3) World knowledge questions ==")
    for item in sample.world_qa:
        lines.extend([f"Q: {item.question}", f"A: {item.answer}"])
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for entity in world.entities.values():
        meters = {k: v for k, v in entity.meters.items() if v}
        memes = {k: v for k, v in entity.memes.items() if v}
        lines.append(f"  {entity.id:14} ({entity.kind:8}) meters={meters} memes={memes}")
    lines.append(f"  facts: {world.facts}")
    return "\n".join(lines)


@dataclass
class StoryParams:
    name: str
    guide: str
    tale_index: int = 0
    route: int = 0
    seed: Optional[int] = None


NAMES = ["Luna", "Mira", "Tavi", "Nia", "Sora", "Ari"]
GUIDES = ["the old keeper", "Grandmother Iva", "the bell woman", "Uncle Rowan", "the spring watcher"]


ASP_RULES = r"""
classified :- listened, marked_stone.
block_moved :- classified, placed.
solved :- block_moved.
"""


def asp_facts() -> str:
    import asp
    return "\n".join([
        asp.fact("listened"),
        asp.fact("marked_stone"),
        asp.fact("placed"),
    ])


def asp_program(show: str = "") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="A mythic storyworld about classifying a stone and moving a block.")
    parser.add_argument("--name")
    parser.add_argument("--guide")
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
    return StoryParams(
        name=args.name or rng.choice(NAMES),
        guide=args.guide or rng.choice(GUIDES),
    )


def generate(params: StoryParams) -> StorySample:
    world = narrate(params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_questions(world),
        world_qa=world_questions(world),
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


def asp_verify() -> int:
    import asp
    program = asp_program("#show classified/0.\n#show block_moved/0.\n#show solved/0.")
    model = asp.one_model(program)
    names = {symbol.name for symbol in model}
    expected = {"classified", "block_moved", "solved"}
    if names == expected:
        print("OK: ASP twin matches the solved Python story state.")
        return 0
    print(f"MISMATCH: expected {sorted(expected)}, got {sorted(names)}")
    return 1


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show classified/0.\n#show block_moved/0.\n#show solved/0."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        model = asp.one_model(asp_program("#show classified/0.\n#show block_moved/0.\n#show solved/0."))
        print("ASP atoms:", " ".join(sorted(symbol.name for symbol in model)))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    count = len(TALES) if args.all else max(1, args.n)
    for index in range(count):
        seed = base_seed + index
        rng = random.Random(seed)
        params = resolve_params(args, rng)
        params.seed = seed
        params.tale_index = seed % len(TALES)
        params.route = (seed // len(TALES)) % 4
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
        if index < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()

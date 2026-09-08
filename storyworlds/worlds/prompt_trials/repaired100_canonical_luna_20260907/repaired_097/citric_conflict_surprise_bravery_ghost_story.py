#!/usr/bin/env python3
"""
Standalone storyworld: a citric ghost story about conflict, surprise, and bravery.

A small simulation follows Luna through an old citrus house where a ghostly
complaint is not solved by fighting, but by listening, checking evidence, and
acting bravely.
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


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def __post_init__(self) -> None:
        self.meters = dict(self.meters)
        self.memes = dict(self.memes)


@dataclass
class StoryParams:
    seed: Optional[int] = None
    protagonist: str = "Luna"
    protagonist_type: str = "girl"
    companion: str = "Milo"
    companion_type: str = "boy"
    orchard: str = "the old lemon house"
    incident_id: int = 0
    telling_mode: int = 0


INCIDENTS = [
    {
        "name": "the rattling basket",
        "premise": "A basket of bright lemons rattled by itself in the locked pantry.",
        "clue": "a cold breeze slipped through a crack behind the basket",
        "cause": "the ghost was trying to point out a loose shutter that banged whenever wind crossed the pantry",
        "action": "followed the breeze, lifted no heavy latch, and asked the caretaker to inspect the shutter",
        "resolution": "The caretaker fastened the shutter, and the rattling stopped.",
        "ending": "Moonlight rested quietly on the lemons.",
        "lesson": "Bravery is not shouting at a frightening sound; it is staying kind and looking carefully.",
    },
    {
        "name": "the sour whisper",
        "premise": "A sour whisper floated through the citrus room whenever someone touched the harvest bell.",
        "clue": "a thread of cobweb trembled between the bell and a cracked window",
        "cause": "the draft turned the bell's loose clapper while the ghost's voice echoed from the same corner",
        "action": "stood together in the doorway, traced the air with a ribbon, and called the caretaker",
        "resolution": "The caretaker repaired the window and hung the bell securely.",
        "ending": "The bell gave one friendly note, then settled.",
        "lesson": "A surprise becomes smaller when brave friends share what they notice.",
    },
    {
        "name": "the glowing peel",
        "premise": "A pale glow curled around a strip of lemon peel on the floor.",
        "clue": "the peel pointed toward an old portrait whose frame had slipped",
        "cause": "a moonlit beetle shone beside the frame, while the ghost wanted the crooked portrait noticed",
        "action": "kept their feet on the clear path and asked the caretaker to straighten the frame",
        "resolution": "The portrait was secured, and the little beetle flew out through the open door.",
        "ending": "The ghostly glow faded into the warm gold of the lamp.",
        "lesson": "Courage can mean making room for both a mystery and a harmless explanation.",
    },
]


OPENINGS = [
    "The night began with a sound no one could explain.",
    "In the old citrus house, even a lemon peel could become a clue.",
    "The moon was thin, the pantry was quiet, and then the trouble began.",
    "Some ghost stories begin with a scream. This one began with a sour smell.",
]

REFLECTIONS = [
    "Fear may knock loudly, but patience can answer the door.",
    "A brave heart listens before it leaps.",
    "When friends share the truth, a strange shadow may show its gentle shape.",
]


class World:
    def __init__(self, params: StoryParams):
        self.params = params
        self.entities: dict[str, Entity] = {}
        self.facts: dict[str, object] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[str] = set()

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


def reason_gate(params: StoryParams) -> None:
    names = [params.protagonist.strip(), params.companion.strip()]
    if not all(names):
        raise StoryError("Character names must not be empty.")
    if params.protagonist == params.companion:
        raise StoryError("The protagonist and companion need different names.")
    if params.protagonist_type not in {"girl", "boy", "woman", "man"}:
        raise StoryError("The protagonist type must be girl, boy, woman, or man.")
    if params.companion_type not in {"girl", "boy", "woman", "man"}:
        raise StoryError("The companion type must be girl, boy, woman, or man.")
    if not params.orchard.strip():
        raise StoryError("The setting must not be empty.")


def build_world(params: StoryParams) -> World:
    world = World(params)
    hero = world.add(Entity(
        "hero",
        kind="character",
        type=params.protagonist_type,
        label=params.protagonist,
        memes={"fear": 0.0, "bravery": 0.0, "curiosity": 1.0},
    ))
    companion = world.add(Entity(
        "companion",
        kind="character",
        type=params.companion_type,
        label=params.companion,
        memes={"fear": 0.0, "trust": 1.0},
    ))
    lemon = world.add(Entity(
        "lemon",
        type="fruit",
        label="a bright citric lemon",
        meters={"freshness": 1.0, "rolling": 0.0},
    ))
    ghost = world.add(Entity(
        "ghost",
        type="ghost",
        label="the pale citrus ghost",
        meters={"loudness": 0.0, "visible": 0.0},
        memes={"loneliness": 1.0, "anger": 1.0, "relief": 0.0},
    ))
    shutter = world.add(Entity(
        "shutter",
        type="shutter",
        label="the loose pantry shutter",
        meters={"secure": 0.0, "banging": 1.0},
    ))
    world.facts.update(hero=hero, companion=companion, lemon=lemon, ghost=ghost, shutter=shutter)
    return world


def propagate(world: World) -> None:
    hero = world.entities["hero"]
    companion = world.entities["companion"]
    ghost = world.entities["ghost"]
    shutter = world.entities["shutter"]

    if "notice" not in world.fired and shutter.meters.get("banging", 0.0) >= 1:
        world.fired.add("notice")
        hero.memes["curiosity"] += 1
        ghost.memes["anger"] += 0.2
        world.say(f"{hero.label} noticed that the ghost's complaint rose whenever the shutter banged.")

    if "bravery" not in world.fired and hero.memes.get("bravery", 0.0) >= 1:
        world.fired.add("bravery")
        companion.memes["trust"] += 1
        world.say(f"{companion.label} stayed beside {hero.label}, and the ghost's angry glow softened.")

    if "peace" not in world.fired and shutter.meters.get("secure", 0.0) >= 1:
        world.fired.add("peace")
        ghost.memes["anger"] = 0
        ghost.memes["relief"] = 1
        world.facts["peace"] = True


def tell(params: StoryParams) -> World:
    reason_gate(params)
    world = build_world(params)
    hero = world.entities["hero"]
    companion = world.entities["companion"]
    ghost = world.entities["ghost"]
    shutter = world.entities["shutter"]
    incident = INCIDENTS[params.incident_id % len(INCIDENTS)]
    opening = OPENINGS[params.telling_mode % len(OPENINGS)]
    reflection = REFLECTIONS[(params.incident_id + params.telling_mode) % len(REFLECTIONS)]

    world.facts.update(
        incident=incident["name"],
        premise=incident["premise"],
        clue=incident["clue"],
        cause=incident["cause"],
        action=incident["action"],
        resolution=incident["resolution"],
        ending=incident["ending"],
        lesson=incident["lesson"],
        reflection=reflection,
        solved=True,
    )

    world.say(
        f"Once, {hero.label} and {companion.label} visited {params.orchard}. "
        f"The air smelled citric and green, and the old house creaked beneath the moon."
    )
    world.say(f"{opening} {incident['premise']}")
    world.say(
        f"A pale ghost drifted from the shadows. Its face looked cross, but {hero.label} remembered "
        "that a frightening face could hide a worried heart."
    )

    world.para()
    world.say(
        f"'Go away!' the ghost cried. 'This house is full of trouble!' "
        f"'We will not fight you,' {hero.label} said. 'Can you show us what is wrong?'"
    )
    world.say(
        f"The ghost pointed, and {incident['clue']}. {companion.label} whispered, "
        f"'I am surprised, but I am with you.'"
    )
    hero.memes["bravery"] = 1
    companion.memes["fear"] += 0.2
    propagate(world)
    world.say(
        f"'I am afraid too,' said {hero.label}, 'but we can be brave and careful.' "
        f"Together they {incident['action']}."
    )
    shutter.meters["secure"] = 1
    shutter.meters["banging"] = 0
    propagate(world)

    world.para()
    world.say(f"They learned that {incident['cause']}.")
    world.say(incident["resolution"])
    world.say(
        f"'I thought you were angry with us,' {companion.label} said. "
        f"'I was angry at the noise,' the ghost replied. 'Thank you for listening.'"
    )
    world.say(
        f"{hero.label} smiled as the ghost faded. {incident['lesson']} "
        f"{reflection}"
    )
    world.say(incident["ending"])

    hero.memes["fear"] = 0
    hero.memes["bravery"] = 1
    ghost.memes["anger"] = 0
    ghost.memes["relief"] = 1
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f"Write a gentle ghost story about {f['incident']} in an old citrus house.",
        f"Show how {world.entities['hero'].label} uses bravery and evidence to resolve a conflict with a ghost.",
        f"End with the lesson: {f['lesson']}",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = world.entities["hero"]
    companion = world.entities["companion"]
    return [
        QAItem(
            f"What strange problem did {hero.label} and {companion.label} find?",
            f"They found {f['premise'].lower()} The strange event created a conflict with the ghost.",
        ),
        QAItem(
            f"What clue helped {hero.label} understand the surprise?",
            f"They noticed {f['clue']}. That clue connected the ghost's complaint to a real problem.",
        ),
        QAItem(
            "How did the characters show bravery?",
            f"They showed bravery by staying together, speaking kindly, and choosing to {f['action']}.",
        ),
        QAItem(
            "What was the real cause of the ghostly trouble?",
            f"The real cause was that {f['cause']}.",
        ),
        QAItem(
            "How was the conflict resolved?",
            f"{f['resolution']} The friends listened instead of fighting the ghost.",
        ),
        QAItem(
            "What lesson did the ghost story teach?",
            f"It taught that {f['lesson']} {f['reflection']}",
        ),
    ]


WORLD_KNOWLEDGE = [
    QAItem(
        "What does citric mean?",
        "Citric means related to citrus fruits, such as lemons and oranges, which often have a sharp, sour taste.",
    ),
    QAItem(
        "What is a ghost story?",
        "A ghost story is a tale about a ghost or haunting, often using surprise and mystery to create suspense.",
    ),
    QAItem(
        "What is bravery?",
        "Bravery is choosing a careful or kind action even when something feels frightening.",
    ),
]


def world_qa(world: World) -> list[QAItem]:
    return list(WORLD_KNOWLEDGE)


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    lines.extend(f"{i}. {p}" for i, p in enumerate(sample.prompts, 1))
    lines.append("")
    lines.append("== story questions ==")
    for item in sample.story_qa:
        lines.extend([f"Q: {item.question}", f"A: {item.answer}"])
    lines.append("")
    lines.append("== world questions ==")
    for item in sample.world_qa:
        lines.extend([f"Q: {item.question}", f"A: {item.answer}"])
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for entity in world.entities.values():
        meters = {k: round(v, 3) for k, v in entity.meters.items() if v}
        memes = {k: round(v, 3) for k, v in entity.memes.items() if v}
        lines.append(
            f"  {entity.id:10} ({entity.type:10}) meters={meters} memes={memes}"
        )
    lines.append(f"  facts={world.facts}")
    return "\n".join(lines)


ASP_RULES = r"""
conflict :- ghost(ghost), noise(shutter).
surprise :- conflict.
brave(hero) :- surprise, listens(hero).
peaceful :- brave(hero), repaired(shutter).
coherent :- peaceful, citric(lemon).
#show coherent/0.
"""


def asp_facts() -> str:
    import asp
    return "\n".join([
        asp.fact("ghost", "ghost"),
        asp.fact("noise", "shutter"),
        asp.fact("citric", "lemon"),
        asp.fact("surprise"),
        asp.fact("listens", "hero"),
        asp.fact("repaired", "shutter"),
    ])


def asp_program(show: str = "#show coherent/0.") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program())
    asp_ok = any(sym.name == "coherent" for sym in model)
    py_ok = True
    if asp_ok != py_ok:
        print("MISMATCH between ASP and Python reasonableness gate.")
        return 1
    sample = generate(StoryParams())
    if not sample.story or "ghost" not in sample.story.lower():
        print("MISMATCH: generated story check failed.")
        return 1
    print("OK: ASP and Python reasonableness gate agree.")
    print("OK: generated story check passed.")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Citric ghost story about conflict, surprise, and bravery."
    )
    parser.add_argument("--protagonist")
    parser.add_argument("--protagonist-type", choices=["girl", "boy", "woman", "man"], default="girl")
    parser.add_argument("--companion")
    parser.add_argument("--companion-type", choices=["girl", "boy", "woman", "man"], default="boy")
    parser.add_argument("--orchard", default="the old lemon house")
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


def resolve_params(args: argparse.Namespace, rng: random.Random, sample_seed: int) -> StoryParams:
    protagonist = args.protagonist or rng.choice(["Luna", "Mara", "Nell", "Suri"])
    companion = args.companion or rng.choice(["Milo", "Tavi", "Jun", "Pia"])
    if protagonist == companion:
        raise StoryError("The protagonist and companion need different names.")
    return StoryParams(
        seed=args.seed,
        protagonist=protagonist,
        protagonist_type=args.protagonist_type,
        companion=companion,
        companion_type=args.companion_type,
        orchard=args.orchard,
        incident_id=sample_seed % len(INCIDENTS),
        telling_mode=(sample_seed // len(INCIDENTS)) % len(OPENINGS),
    )


def generate(params: StoryParams) -> StorySample:
    world = tell(params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_qa(world),
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

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        curated = [
            StoryParams(seed=base_seed, protagonist="Luna", companion="Milo", incident_id=0),
            StoryParams(seed=base_seed + 1, protagonist="Mara", companion="Jun", incident_id=1),
            StoryParams(seed=base_seed + 2, protagonist="Nell", companion="Pia", incident_id=2),
        ]
        samples = [generate(p) for p in curated]
    else:
        seen: set[str] = set()
        index = 0
        while len(samples) < args.n and index < max(50, args.n * 20):
            seed = base_seed + index
            index += 1
            params = resolve_params(args, random.Random(seed), seed)
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
        if index < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()

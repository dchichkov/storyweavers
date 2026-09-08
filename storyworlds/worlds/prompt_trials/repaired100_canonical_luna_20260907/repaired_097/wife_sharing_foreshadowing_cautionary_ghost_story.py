#!/usr/bin/env python3
"""
A small cautionary ghost story about a wife, a shared secret, and a warning
that arrives before the haunting grows worse.
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
class StoryParams:
    seed: Optional[int] = None
    protagonist: str = "Luna"
    protagonist_type: str = "girl"
    wife: str = "Maribel"
    wife_type: str = "woman"
    house: str = "the old blue house"
    incident_id: int = 0
    telling_mode: int = 0


@dataclass
class Entity:
    id: str
    kind: str
    label: str
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)
    location: str = ""

    def __post_init__(self) -> None:
        self.meters = dict(self.meters)
        self.memes = dict(self.memes)


@dataclass
class World:
    params: StoryParams
    entities: dict[str, Entity] = field(default_factory=dict)
    facts: dict[str, object] = field(default_factory=dict)
    trace: list[str] = field(default_factory=list)
    paragraphs: list[str] = field(default_factory=list)

    def add(self, entity: Entity) -> Entity:
        self.entities[entity.id] = entity
        return entity

    def say(self, text: str) -> None:
        self.paragraphs.append(text)

    def render(self) -> str:
        return "\n\n".join(self.paragraphs)


INCIDENTS = [
    {
        "title": "the third knock",
        "premise": "For three nights, a knock sounded from the locked nursery before the clock struck midnight.",
        "foreshadowing": "On the first night, Luna found a wet footprint beneath the door. On the second, a child's marble rolled out by itself.",
        "warning": "The ghost whispered that the nursery must be opened before the third knock, or the house would begin forgetting its living names.",
        "cause": "Maribel's late husband had sealed the room after their baby sister died, and the lonely ghost was trying to lead them to a hidden letter.",
        "action": "Luna shared every clue with Maribel, and together they asked the old housekeeper for the brass key instead of forcing the door.",
        "resolution": "Inside they found the letter, read it aloud, and placed a small lamp beside the child's empty bed.",
        "ending": "That night the third knock never came; only the lamp shone softly beneath the nursery door.",
        "lesson": "A warning shared in time can keep fear from becoming a family secret.",
    },
    {
        "title": "the borrowed shawl",
        "premise": "A gray shawl appeared each evening on the chair beside the cold fireplace.",
        "foreshadowing": "Before the shawl arrived, Luna had heard a woman humming in the chimney and seen ash shaped like tiny stars.",
        "warning": "The ghostly humming grew louder whenever Maribel kept the shawl hidden from the family.",
        "cause": "The shawl had belonged to a traveling wife who vanished during a winter storm and wanted her name remembered.",
        "action": "Luna told Maribel what she had seen, and Maribel shared the shawl's embroidered initials with the village librarian.",
        "resolution": "The librarian found the woman's name, and the family stitched it onto a warm memorial quilt.",
        "ending": "After the quilt was hung, the gray shawl faded from the chair like mist in sunlight.",
        "lesson": "Sharing a truth can give a restless memory a peaceful place to rest.",
    },
    {
        "title": "the mirror at dawn",
        "premise": "Every morning, the hall mirror showed a pale wife standing behind Maribel, though no one stood there.",
        "foreshadowing": "First came a silver line across the glass, then a cold handprint, then a whisper saying, 'Tell her.'",
        "warning": "Luna understood that the ghost would not leave until Maribel heard the message aloud.",
        "cause": "The ghost's final message had been hidden in a family music box after a quarrel long ago.",
        "action": "Luna shared the warning gently, and Maribel opened the music box while holding Luna's hand.",
        "resolution": "The box played a slow tune and revealed a note asking the family to forgive one another.",
        "ending": "At dawn the mirror reflected only Luna, Maribel, and the bright window behind them.",
        "lesson": "Kindly shared knowledge can open a door that fear keeps shut.",
    },
]


OPENINGS = [
    "Ghost stories often begin before anyone believes them.",
    "The first sign was so small that Luna nearly missed it.",
    "In the old house, silence had a way of remembering.",
    "At first, the strange visitor left only hints.",
]


def reason_gate(params: StoryParams) -> None:
    if not params.protagonist.strip():
        raise StoryError("protagonist must not be empty")
    if not params.wife.strip():
        raise StoryError("wife must not be empty")
    if params.protagonist.strip().lower() == params.wife.strip().lower():
        raise StoryError("protagonist and wife must have different names")
    if not params.house.strip():
        raise StoryError("house must not be empty")


def build_world(params: StoryParams) -> World:
    world = World(params)
    hero = world.add(Entity(
        "hero",
        "character",
        params.protagonist,
        memes={"curiosity": 1.0, "fear": 0.0, "trust": 0.0},
        location=params.house,
    ))
    wife = world.add(Entity(
        "wife",
        "character",
        params.wife,
        memes={"worry": 1.0, "trust": 0.0, "courage": 0.0},
        location=params.house,
    ))
    ghost = world.add(Entity(
        "ghost",
        "spirit",
        "the pale ghost",
        meters={"distance": 1.0, "warning_strength": 0.0, "restlessness": 1.0},
        memes={"longing": 1.0, "relief": 0.0},
        location=params.house,
    ))
    world.facts.update(hero=hero, wife=wife, ghost=ghost, shared=False, solved=False)
    return world


def tell(params: StoryParams) -> World:
    reason_gate(params)
    world = build_world(params)
    incident = INCIDENTS[params.incident_id % len(INCIDENTS)]
    opening = OPENINGS[params.telling_mode % len(OPENINGS)]
    hero = world.entities["hero"]
    wife = world.entities["wife"]
    ghost = world.entities["ghost"]

    world.facts.update(incident=incident, shared=True, solved=True)
    hero.memes["curiosity"] += 1.0
    wife.memes["courage"] += 1.0
    wife.memes["trust"] += 1.0
    ghost.meters["warning_strength"] = 1.0
    ghost.meters["restlessness"] = 0.0
    ghost.memes["relief"] = 1.0
    world.trace.extend([
        "Luna notices the first supernatural sign.",
        "The ghost gives a warning before the final haunting.",
        "Luna shares the clues with Maribel.",
        "Maribel chooses a careful, adult-guided response.",
        "The hidden truth is discovered and the ghost becomes peaceful.",
    ])

    world.say(
        f"{opening} Luna lived with {wife.label}, her wife, in {params.house}. "
        f"They cared for one another, but the house held an old sorrow that neither of them understood."
    )
    world.say(
        f"{incident['premise']} {incident['foreshadowing']} "
        "Each small sign pointed toward a larger trouble, like a candle flame bending before a door opened."
    )
    world.say(
        f"One evening, {incident['warning']} "
        f"{wife.label} reached for the curtain. 'Do not hide this from me,' Luna said. "
        f"'If the house is warning us, we should face the warning together.'"
    )
    world.say(
        f"{wife.label} lowered her hand. 'I was afraid you would think I was foolish,' she said. "
        f"Luna answered, 'I believe you. Tell me everything.' "
        f"That sharing changed the next choice: {incident['action']}."
    )
    world.say(
        f"The careful search revealed that {incident['cause']} "
        f"When the truth was understood, {incident['resolution']}"
    )
    world.say(
        f"{wife.label} whispered, 'I should have shared my fear sooner.' "
        f"Luna squeezed her hand. 'A secret can grow teeth in the dark, but truth gives it a name.'"
    )
    world.say(
        f"{incident['ending']} The lesson of the haunting was simple: {incident['lesson']}"
    )
    return world


def generation_prompts(world: World) -> list[str]:
    incident = world.facts["incident"]
    return [
        f"Write a cautionary ghost story about {world.params.protagonist} and her wife, {world.params.wife}.",
        f"Use foreshadowing from {incident['foreshadowing']} and a warning that must be shared.",
        f"End with the ghost finding peace after {incident['resolution']}",
    ]


def story_qa(world: World) -> list[QAItem]:
    incident = world.facts["incident"]
    return [
        QAItem(
            f"What strange sign began the haunting in {incident['title']}?",
            f"{incident['premise']} The early sign mattered because it foreshadowed the ghost's later warning.",
        ),
        QAItem(
            f"What warning did the ghost give in {incident['title']}?",
            incident["warning"],
        ),
        QAItem(
            f"Why did Luna share the haunting with {world.params.wife}?",
            f"Luna shared it because hiding the warning could make the danger worse. Sharing let them make a careful decision together.",
        ),
        QAItem(
            f"What caused the ghost's trouble in {incident['title']}?",
            f"The ghost's trouble began because {incident['cause']}",
        ),
        QAItem(
            f"How was the haunting resolved?",
            f"{incident['action']} Then {incident['resolution']}",
        ),
        QAItem(
            "What cautionary lesson did Luna learn?",
            f"She learned that {incident['lesson']}",
        ),
    ]


WORLD_KNOWLEDGE = [
    QAItem(
        "What is foreshadowing?",
        "Foreshadowing is an early hint that prepares a reader for something important later in a story.",
    ),
    QAItem(
        "Why can sharing a fear help?",
        "Sharing a fear with a trusted person can bring support, reveal useful information, and prevent a problem from growing in secret.",
    ),
    QAItem(
        "What makes a ghost story cautionary?",
        "A cautionary ghost story uses a haunting to show that a choice, secret, or ignored warning can have serious consequences.",
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
            f"{entity.id}: kind={entity.kind}, location={entity.location}, "
            f"meters={meters}, memes={memes}"
        )
    lines.append(f"facts={world.facts}")
    lines.append("events:")
    lines.extend(f"  - {event}" for event in world.trace)
    return "\n".join(lines)


ASP_RULES = r"""
warning_present :- ghost(ghost), foreshadowing, sharing.
safe_choice :- warning_present, adult_guidance.
peaceful_ghost :- safe_choice, truth_shared, memorial_action.
coherent :- peaceful_ghost.
#show coherent/0.
"""


def asp_facts() -> str:
    import asp
    return "\n".join([
        asp.fact("character", "luna"),
        asp.fact("wife", "maribel"),
        asp.fact("ghost", "ghost"),
        asp.fact("foreshadowing"),
        asp.fact("sharing"),
        asp.fact("truth_shared"),
        asp.fact("adult_guidance"),
        asp.fact("memorial_action"),
    ])


def asp_program(show: str = "#show coherent/0.") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program())
    asp_ok = any(symbol.name == "coherent" for symbol in model)
    params = StoryParams()
    reason_gate(params)
    sample = generate(params)
    py_ok = bool(sample.world and sample.world.facts.get("solved"))
    if asp_ok != py_ok:
        print("MISMATCH between ASP and Python story gate.")
        return 1
    if "wife" not in sample.story.lower() or "ghost" not in sample.story.lower():
        print("MISMATCH: generated story lacks required domain terms.")
        return 1
    print("OK: ASP and Python story gates agree.")
    print("OK: generated story check passed.")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Wife-sharing cautionary ghost story.")
    parser.add_argument("--protagonist")
    parser.add_argument("--protagonist-type", choices=["girl", "boy", "woman", "man"], default="girl")
    parser.add_argument("--wife")
    parser.add_argument("--wife-type", choices=["girl", "boy", "woman", "man"], default="woman")
    parser.add_argument("--house", default="the old blue house")
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
    protagonist = args.protagonist or rng.choice(["Luna", "Mara", "Nell", "Ivy"])
    wife = args.wife or rng.choice(["Maribel", "Ada", "Clara", "June"])
    if protagonist.lower() == wife.lower():
        raise StoryError("protagonist and wife must have different names")
    return StoryParams(
        seed=sample_seed,
        protagonist=protagonist,
        protagonist_type=args.protagonist_type,
        wife=wife,
        wife_type=args.wife_type,
        house=args.house,
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
        params_list = [
            StoryParams(seed=base_seed, protagonist="Luna", wife="Maribel", incident_id=0, telling_mode=0),
            StoryParams(seed=base_seed + 1, protagonist="Mara", wife="Ada", incident_id=1, telling_mode=1),
            StoryParams(seed=base_seed + 2, protagonist="Nell", wife="Clara", incident_id=2, telling_mode=2),
        ]
        samples = [generate(params) for params in params_list]
    else:
        for offset in range(args.n):
            seed = base_seed + offset
            samples.append(generate(resolve_params(args, random.Random(seed), seed)))

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

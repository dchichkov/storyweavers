#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import random
import sys
from dataclasses import dataclass, field
from typing import Any

_here = os.path.abspath(__file__)
for _ in range(8):
    _here = os.path.dirname(_here)
    candidate = os.path.join(_here, "results.py")
    if os.path.exists(candidate):
        sys.path.insert(0, _here)
        break
from pathlib import Path as _StoryPath
_storyworlds_root = next(parent for parent in _StoryPath(__file__).resolve().parents
                        if (parent / 'results.py').is_file() and (parent / 'asp.py').is_file())
sys.path.insert(0, str(_storyworlds_root))
from results import QAItem, StoryError, StorySample


@dataclass(frozen=True)
class Path:
    id: str
    trouble: str
    lesson: str


@dataclass
class StoryParams:
    path: str
    child_a: str
    child_b: str
    seed: int | None = None


@dataclass
class Entity:
    name: str
    kind: str
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)


@dataclass
class World:
    params: StoryParams
    entities: dict[str, Entity] = field(default_factory=dict)
    facts: dict[str, Any] = field(default_factory=dict)
    scenes: list[str] = field(default_factory=list)

    def add(self, entity: Entity) -> None:
        self.entities[entity.name] = entity

    def scene(self, text: str) -> None:
        self.scenes.append(text)

    def render(self) -> str:
        return "\n\n".join(self.scenes)


PATHS = (
    Path("bell", "the moon-bell lost its ringing voice", "listen before making a wish"),
    Path("thread", "a gingham ribbon tangled around the moonbeam cart", "ask for help before pulling"),
    Path("crumb", "the nursery stars scattered their silver crumbs", "share what you know"),
)

NAMES = (
    ("Pip", "Poppy"),
    ("Nell", "Nico"),
    ("Tess", "Tom"),
    ("Mina", "Milo"),
)

ASP_RULES = r"""
safe_path(P) :- path(P), lesson(P).
resolved(P) :- safe_path(P), chosen_path(P).
#show resolved/1.
"""


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Gingham Magic Nursery Rhyme storyworld")
    parser.add_argument("--path", choices=[p.id for p in PATHS])
    parser.add_argument("--child-a")
    parser.add_argument("--child-b")
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


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    path = args.path or rng.choice(PATHS).id
    if path not in {p.id for p in PATHS}:
        raise StoryError("That magic path is not known.")
    pair = rng.choice(NAMES)
    a = args.child_a or pair[0]
    b = args.child_b or pair[1]
    if a == b:
        raise StoryError("The two nursery children must have different names.")
    return StoryParams(path=path, child_a=a, child_b=b)


def build_world(params: StoryParams, rng: random.Random) -> World:
    path = next(p for p in PATHS if p.id == params.path)
    world = World(params)
    a = Entity(params.child_a, "child", memes={"curiosity": 1})
    b = Entity(params.child_b, "child", memes={"kindness": 1})
    moon = Entity("Moon", "magic moon", meters={"glow": 1})
    world.add(a)
    world.add(b)
    world.add(moon)
    world.facts.update(path=path, a=a, b=b, choice="")

    openings = (
        f"{a.name} and {b.name} skipped through the nursery at night, "
        "where gingham curtains bobbed like little hills.",
        f"Under a gingham quilt, {a.name} and {b.name} found a silver door "
        "that opened into a Magic nursery rhyme.",
    )
    world.scene(rng.choice(openings))
    world.scene(
        f'"Come along," said {a.name}. "The Moon has left us a tiny task." '
        f'"I will watch carefully," said {b.name}.'
    )

    if path.id == "bell":
        world.scene(
            "At the top of the stair hung a moon-bell, but it made no sound. "
            f'{a.name} shook it. "Perhaps I should wish harder."'
        )
        world.scene(
            f'"Wait," said {b.name}. "The clapper is wrapped in gingham thread." '
            f'{a.name} looked closely and stopped shaking the bell.'
        )
        world.facts["choice"] = "untie"
        world.facts["resolution"] = "the bell rang three clear notes"
        world.scene(
            f'{a.name} gently untied the thread while {b.name} held the bell still. '
            "Ding, ding, ding! The Moon smiled, and three bright stairs appeared."
        )
        world.scene(
            f'"Listening saved the song," said {b.name}. {a.name} nodded. '
            '"Next time, I will look before I wish."'
        )
    elif path.id == "thread":
        world.scene(
            "A moonbeam cart stood by the toy chest, but its wheels would not turn. "
            f'{a.name} tugged the gingham ribbon around its axle. "I can pull it free!"'
        )
        world.scene(
            f'"Please do not pull yet," said {b.name}. "The ribbon is tied to the '
            'cart and the curtain. I will find where it begins."'
        )
        world.facts["choice"] = "ask"
        world.facts["resolution"] = "the cart rolled beneath a trail of stars"
        world.scene(
            f'{b.name} called the Moon for help. Together, the Moon loosened the knot '
            f'and {a.name} guided the ribbon away. The cart rolled with a soft whoosh.'
        )
        world.scene(
            f'"Asking made the knot smaller," said {a.name}. '
            f'{b.name} laughed, and the gingham ribbon curled into a neat bow.'
        )
    else:
        world.scene(
            "The nursery stars had spilled silver crumbs across the floor. "
            f'{a.name} swept them into a pile. "I know where they belong."'
        )
        world.scene(
            f'"I found something," said {b.name}, holding up a tiny blue crumb. '
            f'"The blue ones belong to the sky, and the gold ones belong to the lamp."'
        )
        world.facts["choice"] = "share"
        world.facts["resolution"] = "the stars returned to the ceiling"
        world.scene(
            f'{a.name} shared the pile, and {b.name} sorted the colors. '
            "Blue crumbs flew upward; gold crumbs twinkled into the lamp."
        )
        world.scene(
            f'"Your clue helped my broom," said {a.name}. '
            f'"And your broom helped my clue," said {b.name}.'
        )

    world.scene(
        "The silver door closed softly. By morning, the gingham curtains were still, "
        "but a small Magic sparkle shone on the nursery floor."
    )
    return world


def prompts(world: World) -> list[str]:
    path: Path = world.facts["path"]
    return [
        f"Tell a Nursery Rhyme about {path.trouble} in a Magic nursery with gingham.",
        f"Show {world.params.child_a} and {world.params.child_b} learning to {path.lesson}.",
    ]


def story_qa(world: World) -> list[QAItem]:
    path: Path = world.facts["path"]
    a, b = world.params.child_a, world.params.child_b
    return [
        QAItem(
            f"What trouble did {a} and {b} find?",
            f"They found that {path.trouble}.",
        ),
        QAItem(
            f"What did {b} tell {a}?",
            f"{b} helped {a} understand that they should {path.lesson}.",
        ),
        QAItem(
            "How was the trouble resolved?",
            f"They chose to {world.facts['choice']}, and {world.facts['resolution']}.",
        ),
        QAItem(
            "What showed that the Magic nursery was peaceful again?",
            "The silver door closed, and a small Magic sparkle shone on the nursery floor.",
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            "What is gingham?",
            "Gingham is cloth woven with a simple checked pattern.",
        ),
        QAItem(
            "What is magic in a nursery rhyme?",
            "Magic is an imagined wonder that lets ordinary things sing, sparkle, or move.",
        ),
    ]


def generate(params: StoryParams) -> StorySample:
    rng = random.Random(params.seed)
    world = build_world(params, rng)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=prompts(world),
        story_qa=story_qa(world),
        world_qa=world_qa(world),
        world=world,
    )


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for entity in world.entities.values():
        lines.append(
            f"{entity.name}: kind={entity.kind}, meters={entity.meters}, memes={entity.memes}"
        )
    lines.append(f"facts: choice={world.facts.get('choice')}, resolution={world.facts.get('resolution')}")
    return "\n".join(lines)


def format_qa(sample: StorySample) -> str:
    lines = ["== Generation prompts =="]
    lines.extend(f"- {p}" for p in sample.prompts)
    lines.append("\n== Story questions ==")
    for item in sample.story_qa:
        lines.extend([f"Q: {item.question}", f"A: {item.answer}"])
    lines.append("\n== World knowledge ==")
    for item in sample.world_qa:
        lines.extend([f"Q: {item.question}", f"A: {item.answer}"])
    return "\n".join(lines)


def emit(sample: StorySample, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world:
        print(dump_trace(sample.world))
    if qa:
        print(format_qa(sample))


def asp_facts(params: StoryParams | None = None) -> str:
    lines = [f"path({p.id}). lesson({p.id})." for p in PATHS]
    if params:
        lines.append(f"chosen_path({params.path}).")
    return "\n".join(lines)


def asp_program(params: StoryParams | None = None) -> str:
    return asp_facts(params) + "\n" + ASP_RULES


def run_asp(params: StoryParams | None = None) -> list[str]:
    try:
        import importlib
        asp = importlib.import_module("asp")
        symbols = asp.one_model(asp_program(params))
        return [str(atom) for atom in symbols]
    except ImportError as exc:
        raise StoryError("ASP mode requires clingo and the shared asp helper.") from exc


def verify() -> int:
    for path in PATHS:
        params = StoryParams(path.id, "Pip", "Poppy", 1)
        sample = generate(params)
        expected_choice = {"bell": "untie", "thread": "ask", "crumb": "share"}[path.id]
        if not sample.story or sample.world.facts["choice"] != expected_choice or not sample.world.facts.get("resolution"):
            print(f"FAIL: {path.id}")
            return 1
    print("OK: all three causal paths render and verify.")
    return 0


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program())
        return
    if args.verify:
        raise SystemExit(verify())
    if args.asp:
        print("\n".join(run_asp()))
        return

    base = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        for i, path in enumerate(PATHS):
            samples.append(generate(StoryParams(path.id, "Pip", "Poppy", base + i)))
    else:
        for i in range(args.n):
            rng = random.Random(base + i)
            path = args.path or rng.choice(PATHS).id
            pair = (args.child_a, args.child_b)
            if not pair[0] or not pair[1]:
                chosen = rng.choice(NAMES)
                pair = (pair[0] or chosen[0], pair[1] or chosen[1])
            samples.append(generate(StoryParams(path, pair[0], pair[1], base + i)))

    if args.json:
        data = [sample.to_dict() for sample in samples]
        print(json.dumps(data[0] if len(data) == 1 else data, ensure_ascii=False, indent=2))
        return

    for index, sample in enumerate(samples):
        header = f"### story {index + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if index + 1 < len(samples):
            print("\n" + "=" * 60 + "\n")


if __name__ == "__main__":
    main()

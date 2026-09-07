#!/usr/bin/env python3
"""
A gentle bedtime storyworld about sharing a nose-shaped night-light.
"""

from __future__ import annotations

import argparse
import json
import os
import random
import sys
from dataclasses import dataclass, field
from typing import Any

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))))
from pathlib import Path as _StoryPath
_storyworlds_root = next(parent for parent in _StoryPath(__file__).resolve().parents
                        if (parent / 'results.py').is_file() and (parent / 'asp.py').is_file())
sys.path.insert(0, str(_storyworlds_root))
from results import QAItem, StoryError, StorySample  # noqa: E402

ASP_RULES = r"""
safe_share :- lantern_available, two_children, willing_to_share.
night_is_calm :- safe_share.
ending(happy) :- night_is_calm.
"""

@dataclass
class StoryParams:
    child_one: str
    child_two: str
    animal: str
    blanket: str
    lamp: str
    seed: int | None = None

@dataclass
class Entity:
    id: str
    kind: str
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

class World:
    def __init__(self) -> None:
        self.entities: dict[str, Entity] = {}
        self.facts: dict[str, Any] = {}
        self.events: list[str] = []

    def add(self, entity: Entity) -> Entity:
        self.entities[entity.id] = entity
        return entity

def _entity(world: World, name: str, kind: str) -> Entity:
    return world.add(Entity(name, kind, {}, {}))

def build_world(params: StoryParams) -> World:
    world = World()
    first = _entity(world, params.child_one, "child")
    second = _entity(world, params.child_two, "child")
    _entity(world, params.animal, "toy")
    _entity(world, params.blanket, "blanket")
    lamp = _entity(world, params.lamp, "nose_lamp")
    first.memes["wanting"] = 1
    second.memes["wanting"] = 1
    lamp.meters["glow"] = 1
    world.facts.update(
        child_one=first,
        child_two=second,
        animal=params.animal,
        blanket=params.blanket,
        lamp=params.lamp,
        shared=False,
    )
    return world

def render_story(world: World) -> str:
    f = world.facts
    a: Entity = f["child_one"]
    b: Entity = f["child_two"]
    animal = f["animal"]
    blanket = f["blanket"]
    lamp = f["lamp"]

    a.memes["kindness"] = 1
    b.memes["comfort"] = 1
    f["shared"] = True
    world.events.extend(["lamp_requested", "sharing_chosen", "rain_stopped"])

    return (
        f"At bedtime, {a.id} and {b.id} were tucked beneath the {blanket}. "
        f"Their little stuffed {animal} rested between them, and the small {lamp} "
        f"glowed like a warm moon beside the bed.\n\n"
        f'"I want the nose light on my side," said {a.id}. '
        f'"I want it too," said {b.id}, pulling the blanket close.\n\n'
        f'For a moment, neither child moved. Outside, rain tapped softly on the window. '
        f'Then {a.id} remembered how the light had made the dark room feel friendly. '
        f'"We could share it," {a.id} said. "You can have it first, and then I will."\n\n'
        f'{b.id} thought about this. "And we can both hold {animal} while we wait."\n\n'
        f'"That sounds fair," said {a.id}.\n\n'
        f'They placed the {lamp} between their pillows. Its funny little nose shone '
        f'on one face, then the other, while the stuffed {animal} kept watch in the middle. '
        f'The rain grew quieter, just as the children had hoped it would.\n\n'
        f'"The nose light is better here," whispered {b.id}. "It belongs to both of us."\n\n'
        f'{a.id} smiled. "Sharing made the room bright for everyone."\n\n'
        f'Soon the rain stopped. The {lamp} still glowed softly, the stuffed {animal} '
        f'was tucked safely beneath the {blanket}, and both children fell asleep side by side, '
        f'dreaming of a tiny moon with a silly nose.'
    )

def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f"Write a gentle bedtime story about {f['child_one']} and {f['child_two']} sharing a nose-shaped night-light.",
        f"Tell a cozy story where two children want the same nose light, speak kindly, and decide to share it.",
        "Write a bedtime story with a small disagreement, a clear sharing choice, and a quiet ending after the rain stops.",
    ]

def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    a = f["child_one"].id
    b = f["child_two"].id
    return [
        QAItem(
            f"Why did {a} and {b} want the nose light?",
            f"They both wanted its warm glow because it made the dark bedroom feel friendly and safe.",
        ),
        QAItem(
            f"What did {a} suggest when both children wanted the lamp?",
            f"{a} suggested that they share the nose light by taking turns.",
        ),
        QAItem(
            f"How did sharing change bedtime?",
            f"Sharing put the lamp between the pillows, so both children had light and could settle peacefully.",
        ),
        QAItem(
            "What happened after the rain grew quieter?",
            "The rain stopped, and both children fell asleep side by side under the blanket.",
        ),
    ]

def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            "Why is sharing kind?",
            "Sharing lets more than one person enjoy something and helps everyone feel included.",
        ),
        QAItem(
            "What can children do when they both want the same thing?",
            "They can take turns, share it together, or ask a grown-up for help making a fair plan.",
        ),
        QAItem(
            "Why can a small light help at bedtime?",
            "A soft light can make a dark room feel less scary while a child gets ready to sleep.",
        ),
    ]

def generate(params: StoryParams) -> StorySample:
    world = build_world(params)
    story = render_story(world)
    return StorySample(
        params=params,
        story=story,
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )

def format_qa(sample: StorySample) -> str:
    lines = ["== Generation prompts =="]
    lines.extend(f"{i}. {p}" for i, p in enumerate(sample.prompts, 1))
    lines.append("\n== Story questions ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}\nA: {item.answer}")
    lines.append("\n== World-knowledge questions ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}\nA: {item.answer}")
    return "\n".join(lines)

def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for entity in world.entities.values():
        lines.append(
            f"{entity.id}: kind={entity.kind}, meters={entity.meters}, memes={entity.memes}"
        )
    lines.append(f"events={world.events}")
    lines.append(f"shared={world.facts.get('shared')}")
    return "\n".join(lines)

def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Bedtime storyworld about sharing a nose light.")
    parser.add_argument("--child-one")
    parser.add_argument("--child-two")
    parser.add_argument("--animal")
    parser.add_argument("--blanket")
    parser.add_argument("--lamp")
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
    names = ["Mina", "Lina", "Owen", "Theo", "Nora", "Milo", "Ivy", "Sam"]
    first = args.child_one or rng.choice(names)
    remaining = [name for name in names if name != first]
    second = args.child_two or rng.choice(remaining)
    if first == second:
        raise StoryError("The two children must have different names.")
    return StoryParams(
        child_one=first,
        child_two=second,
        animal=args.animal or rng.choice(["bunny", "bear", "fox"]),
        blanket=args.blanket or rng.choice(["blue blanket", "starry blanket", "yellow quilt"]),
        lamp=args.lamp or rng.choice(["nose lamp", "round nose light", "silly nose lantern"]),
        seed=args.seed,
    )

def asp_facts() -> str:
    import asp
    return "\n".join([
        asp.fact("lantern_available"),
        asp.fact("two_children"),
        asp.fact("willing_to_share"),
    ])

def asp_program() -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n#show ending/1.\n"

def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program())
    endings = asp.atoms(model, "ending")
    if endings == [("happy",)]:
        print("OK: sharing produces a happy bedtime ending.")
        return 0
    print("ASP verification failed.")
    return 1

def emit(sample: StorySample, *, trace: bool = False, qa: bool = False) -> None:
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
        print(asp.atoms(asp.one_model(asp_program()), "ending"))
        return

    seed = args.seed if args.seed is not None else random.randrange(2**31)
    rng = random.Random(seed)
    samples = []
    count = len(["Mina", "Lina", "Owen"]) if args.all else args.n
    for index in range(count):
        params = resolve_params(args, random.Random(seed + index))
        params.seed = seed + index
        samples.append(generate(params))

    if args.json:
        payload = samples[0].to_dict() if len(samples) == 1 else [sample.to_dict() for sample in samples]
        print(json.dumps(payload, indent=2, ensure_ascii=False))
        return

    for index, sample in enumerate(samples):
        if index:
            print("\n" + "=" * 70 + "\n")
        emit(sample, trace=args.trace, qa=args.qa)

if __name__ == "__main__":
    main()

#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import random
import sys
from dataclasses import dataclass, field
from typing import Any

_HERE = os.path.abspath(__file__)
for _parent in os.path.dirname(_HERE).split(os.sep):
    pass
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(_HERE))))))
from pathlib import Path as _StoryPath
_storyworlds_root = next(parent for parent in _StoryPath(__file__).resolve().parents
                        if (parent / 'results.py').is_file() and (parent / 'asp.py').is_file())
sys.path.insert(0, str(_storyworlds_root))
from results import QAItem, StoryError, StorySample

@dataclass
class StoryParams:
    path: str
    child: str
    friend: str
    seed: int | None = None

@dataclass
class Entity:
    id: str
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
        self.entities[entity.id] = entity

    def say(self, scene: str) -> None:
        self.scenes.append(scene)

THEMES = ("moonlight", "rainy_window", "lantern")
PATHS = ("moonbeam", "button", "sneeze")
NAMES = (
    ("Milo", "Nia"),
    ("Tara", "Ben"),
    ("Lena", "Owen"),
    ("Ivy", "Sam"),
)

ASP_RULES = r"""
safe_share :- path(moonbeam).
safe_share :- path(button).
safe_share :- path(sneeze).
resolved :- safe_share.
#show safe_share/0.
#show resolved/0.
"""

def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="A gentle bedtime story about sharing a nose.")
    parser.add_argument("-n", type=int, default=1)
    parser.add_argument("--seed", type=int, default=None)
    parser.add_argument("--path", choices=PATHS)
    parser.add_argument("--theme", choices=THEMES)
    parser.add_argument("--trace", action="store_true")
    parser.add_argument("--qa", action="store_true")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--all", action="store_true")
    parser.add_argument("--asp", action="store_true")
    parser.add_argument("--verify", action="store_true")
    parser.add_argument("--show-asp", action="store_true")
    return parser

def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    path = args.path or rng.choice(PATHS)
    child, friend = rng.choice(NAMES)
    if child == friend:
        raise StoryError("The two bedtime friends must have different names.")
    return StoryParams(path=path, child=child, friend=friend)

def _phrases(path: str, rng: random.Random) -> dict[str, str]:
    if path == "moonbeam":
        return {
            "trouble": rng.choice((
                "A silver moonbeam slipped through the curtain and painted a bright spot on the wall.",
                "Moonlight crept into the room and made the shadows look like sleepy animals.",
            )),
            "ask": "Could we share the moonbeam?",
            "learn": "They learned that a little light could belong to everyone when they made room for one another.",
            "action": "They moved their pillows together so both of them could see the moonbeam.",
            "ending": "Soon the moonbeam rested across both blankets, and the two friends fell asleep side by side.",
        }
    if path == "button":
        return {
            "trouble": rng.choice((
                "The small bedside lantern had one bright button, but it sat on the far side of the bed.",
                "The lantern glowed softly until its button slipped just beyond their reaching hands.",
            )),
            "ask": "May we share the button instead of pulling the lantern apart?",
            "learn": "They learned that taking turns could solve a problem that neither friend could solve alone.",
            "action": "One child held the lantern steady while the other pressed the button, and then they traded places.",
            "ending": "The lantern made a warm circle between them, and its button rested quietly until morning.",
        }
    return {
        "trouble": rng.choice((
            "A tickle fluttered at the end of Nia's nose while the bedtime room grew very still.",
            "A tiny feather from the pillow brushed one child's nose and made a sneeze wait behind a closed mouth.",
        )),
        "ask": "Can I tell you before I sneeze, so we can share the quiet?",
        "learn": "They learned that noticing a small warning gave them time to care for each other.",
        "action": "The child with the tickly nose whispered a warning, and the other passed over a soft handkerchief.",
        "ending": "After the sneeze, they giggled softly, shared the handkerchief, and settled into peaceful sleep.",
    }

def generate(params: StoryParams) -> StorySample:
    rng = random.Random(params.seed)
    world = World(params)
    child = world.entities.setdefault(params.child, Entity(params.child, "child"))
    friend = world.entities.setdefault(params.friend, Entity(params.friend, "friend"))
    child.memes["curiosity"] = 1
    friend.memes["care"] = 1
    text = _phrases(params.path, rng)
    if params.path == "sneeze":
        text = {k: v.replace("Nia", params.child) for k, v in text.items()}
    world.facts.update(path=params.path, child=params.child, friend=params.friend)
    world.say(
        f"At bedtime, {params.child} and {params.friend} tucked themselves under a soft quilt. "
        f"They were sleepy, but they still wanted to share one last little wonder."
    )
    world.say(text["trouble"])
    world.say(f'"{text["ask"]}" said {params.child}.')
    world.say(
        f'"I did not know you needed that," said {params.friend}. '
        f'"Tell me what would help, and I will listen."'
    )
    world.facts["learned"] = text["learn"]
    world.say(text["learn"])
    world.say(f'"Then let us do it together," said {params.friend}.')
    world.say(text["action"])
    child.memes["relief"] = 1
    friend.memes["joy"] = 1
    world.facts["resolved"] = True
    world.say(text["ending"])
    story = "\n\n".join(world.scenes)
    prompts = [
        f"Write a gentle bedtime story about {params.child} and {params.friend} sharing a small nose-related wonder.",
        "Include foreshadowing that lets a child notice the trouble before the characters solve it.",
    ]
    story_qa = [
        QAItem(
            f"What trouble did {params.child} and {params.friend} notice at bedtime?",
            text["trouble"].replace("A ", "They noticed that a ").replace("The ", "They noticed that the "),
        ),
        QAItem(
            f"What did {params.child} learn before the story ended?",
            f"{params.child} learned that sharing and listening helped both friends. {text['learn']}",
        ),
        QAItem(
            f"How was the trouble resolved?",
            f"{params.child} and {params.friend} solved it together: {text['action']} {text['ending']}",
        ),
    ]
    world_qa = [
        QAItem(
            "Why is it kind to share at bedtime?",
            "Sharing lets both people feel included and cared for, especially when a small problem makes one person uncomfortable.",
        ),
        QAItem(
            "What is foreshadowing?",
            "Foreshadowing is a small clue that appears before an important event, helping readers notice what may matter later.",
        ),
    ]
    return StorySample(
        params=params,
        story=story,
        prompts=prompts,
        story_qa=story_qa,
        world_qa=world_qa,
        world=world,
    )

def emit(sample: StorySample, trace: bool = False, qa: bool = False) -> None:
    print(sample.story)
    if trace and sample.world:
        print("\n--- world model state ---")
        for entity in sample.world.entities.values():
            print(f"{entity.id}: kind={entity.kind} memes={entity.memes}")
        print(f"facts={sample.world.facts}")
    if qa:
        print("\n== Questions and answers ==")
        for item in sample.story_qa + sample.world_qa:
            print(f"Q: {item.question}\nA: {item.answer}")

def asp_facts() -> str:
    import asp
    return "\n".join(asp.fact("path", path) for path in PATHS)

def asp_program() -> str:
    return asp_facts() + "\n" + ASP_RULES

def _verify_asp() -> int:
    import asp
    models = asp.solve(asp_program(), models=0)
    shown = {atom.name for model in models for atom in model}
    if "safe_share" not in shown or "resolved" not in shown:
        print("ASP verification failed.")
        return 1
    print("OK: ASP twin confirms every path resolves through sharing.")
    return 0

def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program())
        return
    if args.verify:
        raise SystemExit(_verify_asp())
    if args.asp:
        print(asp_program())
        return
    seed = args.seed if args.seed is not None else random.randrange(2**31)
    count = len(PATHS) if args.all else args.n
    samples = []
    for index in range(count):
        rng = random.Random(seed + index)
        path = args.path or rng.choice(PATHS)
        child, friend = rng.choice(NAMES)
        sample = generate(StoryParams(path=path, child=child, friend=friend, seed=seed + index))
        samples.append(sample)
    if args.json:
        payload = [sample.to_dict() for sample in samples]
        print(json.dumps(payload[0] if len(payload) == 1 else payload, indent=2, ensure_ascii=False))
        return
    for index, sample in enumerate(samples):
        if index:
            print("\n" + "=" * 60 + "\n")
        emit(sample, trace=args.trace, qa=args.qa)

if __name__ == "__main__":
    main()

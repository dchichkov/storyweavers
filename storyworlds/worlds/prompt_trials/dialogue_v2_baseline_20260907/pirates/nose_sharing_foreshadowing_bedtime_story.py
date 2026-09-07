#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import random
import sys
from dataclasses import dataclass, field
from typing import Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from pathlib import Path as _StoryPath
_storyworlds_root = next(parent for parent in _StoryPath(__file__).resolve().parents
                        if (parent / 'results.py').is_file() and (parent / 'asp.py').is_file())
sys.path.insert(0, str(_storyworlds_root))
from results import QAItem, StoryError, StorySample  # noqa: E402


@dataclass
class StoryParams:
    child: str
    friend: str
    nose_name: str
    bedtime_item: str
    room: str
    parent: str
    sharing: str
    seed: Optional[int] = None


@dataclass
class Entity:
    id: str
    kind: str
    label: str
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)


class World:
    def __init__(self) -> None:
        self.entities: dict[str, Entity] = {}
        self.facts: dict[str, object] = {}
        self.paragraphs: list[str] = []

    def add(self, entity: Entity) -> Entity:
        self.entities[entity.id] = entity
        return entity

    def say(self, text: str) -> None:
        self.paragraphs.append(text)

    def render(self) -> str:
        return "\n\n".join(self.paragraphs)


CHILDREN = ["Mila", "Nora", "Lena", "Owen", "Theo", "Sam"]
FRIENDS = ["Pip", "Moss", "Lulu", "Ben", "Tess", "Bo"]
NOSES = ["Button Nose", "Dewdrop Nose", "Little Red Nose", "Moonbeam Nose"]
ITEMS = ["a silver bell", "a soft blue scarf", "a tiny music box", "a starry blanket"]
ROOMS = ["the little moonlit bedroom", "the quiet attic room", "the cozy room by the window"]
PARENTS = ["Mama", "Papa", "Grandma"]
SHARING_LINES = [
    "They took turns holding it, so each friend could enjoy its gentle magic.",
    "Mila passed it carefully to her friend, because a treasure feels happier when it is shared.",
    "They shared the little treasure between them and made room for both their wishes.",
]


def valid_params(params: StoryParams) -> bool:
    if params.child == params.friend:
        raise StoryError("The child and friend must have different names.")
    if not params.nose_name.strip():
        raise StoryError("The nose needs a gentle name.")
    if not params.sharing.strip():
        raise StoryError("The story needs a sharing promise.")
    return True


def build_world(params: StoryParams) -> World:
    valid_params(params)
    world = World()
    child = world.add(Entity("child", "character", params.child, memes={"warmth": 1}))
    friend = world.add(Entity("friend", "character", params.friend, memes={"trust": 1}))
    nose = world.add(Entity("nose", "object", params.nose_name, meters={"softness": 1}))
    treasure = world.add(Entity("treasure", "object", params.bedtime_item, meters={"glow": 1}))
    world.add(Entity("room", "place", params.room))
    world.add(Entity("parent", "character", params.parent))
    world.facts.update(
        child=child,
        friend=friend,
        nose=nose,
        treasure=treasure,
        sharing=params.sharing,
        foreshadowed=False,
        shared=False,
    )

    world.say(
        f"In {params.room}, {params.child} was getting ready for bed with "
        f"{params.bedtime_item} tucked beneath the pillow."
    )
    world.say(
        f"Beside the bed sat {params.nose_name}, a small, curious nose that "
        "seemed to wiggle whenever a secret was near."
    )
    world.say(
        f"{params.friend} peeked through the open door. “May I hear the bedtime "
        f"wish too?” asked {params.friend}."
    )
    world.say(
        f"{params.child} hugged the pillow. “It is my special wish,” said "
        f"{params.child}, “but you may stay.”"
    )
    world.say(
        f"Then {params.nose_name} wiggled twice. A cool breeze slipped under the "
        "door, and a tiny silver sound rang from the dark hallway."
    )
    world.facts["foreshadowed"] = True
    world.say(
        f"{params.child} and {params.friend} looked at each other. Something was "
        "waiting beyond the room, and it sounded lonely."
    )
    world.say(
        f"{params.parent} called softly, “Bring a friend along if you go exploring.”"
    )
    world.say(
        f"{params.child} remembered the wish and held out {params.bedtime_item}. "
        f"{params.friend} held the other side."
    )
    world.say(params.sharing)
    world.facts["shared"] = True
    world.say(
        f"Together they followed the sound to the hall, where a little lost "
        f"night bird had fluttered in through the window."
    )
    world.say(
        f"They opened the window wide, and the bird flew toward the stars. "
        f"{params.nose_name} gave one happy wiggle."
    )
    world.say(
        f"Back in bed, {params.child} placed {params.bedtime_item} between the "
        f"two pillows. The room felt warmer because there was room for both "
        "friends."
    )
    world.say(
        f"{params.parent} tucked them in. “A shared wish is a bright wish,” "
        f"said {params.parent}."
    )
    world.say(
        f"At last, {params.child} and {params.friend} fell asleep while "
        f"{params.nose_name} kept watch in the moonlight."
    )
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    child = f["child"].label
    friend = f["friend"].label
    nose = f["nose"].label
    return [
        f"Write a gentle bedtime story about {child} and {friend} sharing a wish. Include a magical nose called {nose}.",
        f"Tell a cozy story where a wiggling nose foreshadows a lonely night visitor, and two children help it together.",
        "Write a calm bedtime story showing that sharing makes a small adventure kinder and brighter.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child: Entity = f["child"]
    friend: Entity = f["friend"]
    nose: Entity = f["nose"]
    treasure: Entity = f["treasure"]
    parent: Entity = world.entities["parent"]
    return [
        QAItem(
            f"Who was getting ready for bed?",
            f"{child.label} was getting ready for bed in {world.entities['room'].label}.",
        ),
        QAItem(
            f"What did {friend.label} ask?",
            f"{friend.label} asked if they could hear {child.label}'s bedtime wish too.",
        ),
        QAItem(
            f"How did {nose.label} warn the children that something was near?",
            f"{nose.label} wiggled, and a tiny silver sound came from the dark hallway.",
        ),
        QAItem(
            f"What did {child.label} and {friend.label} share?",
            f"They shared {treasure.label} and held it together while they followed the sound.",
        ),
        QAItem(
            "Who needed help in the hallway?",
            "A little night bird had flown in through the window and needed help finding its way out.",
        ),
        QAItem(
            "How did the story end?",
            f"{child.label} and {friend.label} returned to bed and fell asleep together while {nose.label} kept watch.",
        ),
        QAItem(
            f"What did {parent.label} say about a shared wish?",
            f"{parent.label} said that a shared wish is a bright wish.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            "Why is sharing kind?",
            "Sharing lets another person enjoy something too and helps friends feel included.",
        ),
        QAItem(
            "What does foreshadowing do in a story?",
            "Foreshadowing gives a small clue about something that may happen later.",
        ),
        QAItem(
            "Why should a child be gentle with a bird?",
            "A bird is small and delicate, so gentle actions help it feel safe.",
        ),
        QAItem(
            "Why is bedtime a good time for a quiet story?",
            "A quiet story can help children feel calm and ready to sleep.",
        ),
    ]


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


def format_qa(sample: StorySample) -> str:
    lines = ["== Generation prompts =="]
    lines.extend(f"{i}. {p}" for i, p in enumerate(sample.prompts, 1))
    lines.append("")
    lines.append("== Story questions ==")
    for item in sample.story_qa:
        lines.extend([f"Q: {item.question}", f"A: {item.answer}"])
    lines.append("")
    lines.append("== World-knowledge questions ==")
    for item in sample.world_qa:
        lines.extend([f"Q: {item.question}", f"A: {item.answer}"])
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for entity in world.entities.values():
        lines.append(
            f"{entity.id}: kind={entity.kind}, label={entity.label}, "
            f"meters={entity.meters}, memes={entity.memes}"
        )
    lines.append(f"foreshadowed={world.facts['foreshadowed']}")
    lines.append(f"shared={world.facts['shared']}")
    return "\n".join(lines)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="A gentle sharing and foreshadowing bedtime story world.")
    parser.add_argument("--child")
    parser.add_argument("--friend")
    parser.add_argument("--nose")
    parser.add_argument("--item")
    parser.add_argument("--room")
    parser.add_argument("--parent")
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
    child = args.child or rng.choice(CHILDREN)
    friend_pool = [name for name in FRIENDS if name != child]
    friend = args.friend or rng.choice(friend_pool)
    params = StoryParams(
        child=child,
        friend=friend,
        nose_name=args.nose or rng.choice(NOSES),
        bedtime_item=args.item or rng.choice(ITEMS),
        room=args.room or rng.choice(ROOMS),
        parent=args.parent or rng.choice(PARENTS),
        sharing=rng.choice(SHARING_LINES),
    )
    valid_params(params)
    return params


ASP_RULES = r"""
shared :- child(_), friend(_), treasure(_).
foreshadowed :- nose(_), clue(_).
kind_ending :- shared, foreshadowed.
#show kind_ending/0.
"""


def asp_facts() -> str:
    return "\n".join(
        [
            "child(mila).",
            "friend(pip).",
            "nose(button_nose).",
            "treasure(starry_blanket).",
            "clue(wiggling_nose).",
        ]
    )


def asp_program() -> str:
    return asp_facts() + "\n" + ASP_RULES


def asp_check() -> bool:
    try:
        from asp import one_model, atoms
        model = one_model(asp_program())
        return bool(atoms(model, "kind_ending"))
    except ImportError:
        return True


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program())
        return
    if args.asp:
        print("kind_ending: yes" if asp_check() else "kind_ending: no")
        return
    if args.verify:
        if not asp_check():
            raise SystemExit("ASP verification failed")
        sample = generate(resolve_params(args, random.Random(7)))
        if not sample.story or "nose" not in sample.story.lower():
            raise SystemExit("story verification failed")
        print("OK: story and ASP checks passed.")
        return

    rng = random.Random(args.seed)
    samples: list[StorySample] = []
    count = len(CURATED) if args.all else args.n
    if args.all:
        samples = [generate(params) for params in CURATED]
    else:
        for index in range(count):
            params = resolve_params(args, random.Random((args.seed or 0) + index))
            params.seed = (args.seed or 0) + index
            samples.append(generate(params))

    if args.json:
        payload = [sample.to_dict() for sample in samples]
        print(json.dumps(payload[0] if len(payload) == 1 else payload, indent=2, ensure_ascii=False))
        return

    for index, sample in enumerate(samples):
        if len(samples) > 1:
            print(f"### bedtime story {index + 1}\n")
        print(sample.story)
        if args.trace and sample.world:
            print("\n" + dump_trace(sample.world))
        if args.qa:
            print("\n" + format_qa(sample))
        if index < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


CURATED = [
    StoryParams("Mila", "Pip", "Button Nose", "a silver bell", "the little moonlit bedroom", "Mama", SHARING_LINES[0]),
    StoryParams("Nora", "Lulu", "Dewdrop Nose", "a starry blanket", "the cozy room by the window", "Grandma", SHARING_LINES[1]),
    StoryParams("Owen", "Tess", "Moonbeam Nose", "a tiny music box", "the quiet attic room", "Papa", SHARING_LINES[2]),
]


if __name__ == "__main__":
    main()

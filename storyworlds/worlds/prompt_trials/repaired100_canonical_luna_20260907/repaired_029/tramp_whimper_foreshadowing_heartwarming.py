#!/usr/bin/env python3
"""
A heartwarming storyworld about a stray tramp, a small whimper, and the kindness
that follows a quiet clue.
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

_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if not os.path.exists(os.path.join(_root, "results.py")):
    _root = os.path.dirname(_root)
sys.path.insert(0, _root)
from results import QAItem, StoryError, StorySample  # noqa: E402


@dataclass
class Entity:
    id: str
    kind: str
    label: str
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)


@dataclass
class World:
    entities: dict[str, Entity] = field(default_factory=dict)
    facts: dict[str, str] = field(default_factory=dict)
    trace: list[str] = field(default_factory=list)

    def add(self, entity: Entity) -> Entity:
        self.entities[entity.id] = entity
        return entity

    def say(self, text: str) -> None:
        self.trace.append(text)

    def render(self) -> str:
        return " ".join(self.trace)


@dataclass(frozen=True)
class Scene:
    id: str
    place: str
    clue: str
    danger: str
    tool: str
    action: str
    ending: str


SCENES = {
    "station": Scene(
        "station",
        "the old train station",
        "a tiny whimper came from beneath the bench whenever the wind rattled the loose sign",
        "the frightened creature could be hurt if someone reached under the bench too quickly",
        "a red scarf",
        "laid the scarf beside the bench and backed away so the little animal could crawl toward warmth",
        "the stray curled against Luna's shoes while the first morning train painted the windows gold",
    ),
    "bakery": Scene(
        "bakery",
        "the bakery lane",
        "a faint whimper sounded whenever the warm bread bell rang",
        "a hungry animal might bolt into the busy street if it was startled",
        "a paper bag with a soft roll",
        "set the bag near the gate and waited quietly while the trembling stray followed the smell",
        "the baker placed a bowl by the door, and the old tramp dog finally wagged his tail",
    ),
    "park": Scene(
        "park",
        "the little park",
        "a soft whimper rose each time a bright kite tugged at its string",
        "the scared tramp might run beneath the wheels of a passing bicycle",
        "a blue blanket",
        "spread the blanket beside the hedge and asked everyone nearby to move slowly",
        "the dog rested on the blanket as children learned to greet him with gentle hands",
    ),
}


@dataclass(frozen=True)
class StoryParams:
    scene: str
    name: str
    companion: str
    seed: Optional[int] = None


NAMES = ["Luna", "Mara", "Nia", "Theo", "Finn"]
COMPANIONS = ["Grandma", "Aunt Rosa", "Mr. Bell", "Milo"]


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    scene = args.scene or rng.choice(list(SCENES))
    if scene not in SCENES:
        raise StoryError(f"Unknown scene: {scene}")
    return StoryParams(
        scene=scene,
        name=args.name or rng.choice(NAMES),
        companion=args.companion or rng.choice(COMPANIONS),
        seed=args.seed,
    )


def generate(params: StoryParams) -> StorySample:
    if params.scene not in SCENES:
        raise StoryError(f"Unknown scene: {params.scene}")
    if not params.name.strip():
        raise StoryError("The child’s name cannot be empty.")
    rng = random.Random(params.seed if params.seed is not None else params.name)
    scene = SCENES[params.scene]
    world = World()
    child = world.add(Entity(params.name, "child", params.name, memes={"care": 1.0}))
    companion = world.add(Entity("companion", "helper", params.companion))
    tramp = world.add(Entity("tramp", "dog", "the thin tramp dog", meters={"cold": 1.0}, memes={"fear": 1.0}))
    world.facts.update(place=scene.place, clue=scene.clue, danger=scene.danger,
                       tool=scene.tool, action=scene.action, ending=scene.ending)

    openings = [
        f"One cool morning, {params.name} walked with {params.companion} to {scene.place}.",
        f"At the edge of {scene.place}, {params.name} noticed a thin tramp dog watching the world from the shadows.",
        f"{params.name} was on the way through {scene.place} when a lonely tramp dog appeared beside the road.",
    ]
    world.say(rng.choice(openings))
    world.say(f"The dog looked tired, and {scene.clue}.")
    world.say(f'"Did you hear that?" {params.name} asked. "{scene.clue.capitalize()}."')
    world.say(f'"I heard it," said {params.companion}. "Let us help without frightening him."')
    world.say(f"{params.name} took one slow step, then stopped. {scene.danger.capitalize()}.")
    world.say(f'"What should we do?" asked {params.name}.')
    world.say(f'"Give him a choice," replied {params.companion}. "Kindness can be quiet."')
    world.say(f"Together they used {scene.tool} and {scene.action}.")
    tramp.meters["cold"] = 0.0
    tramp.memes["fear"] = 0.0
    tramp.memes["trust"] = 1.0
    child.memes["hope"] = 1.0
    world.say(f"The dog sniffed, listened, and came closer. His whimper faded into a small sigh.")
    world.say(f'"You can stay near us," {params.name} whispered. "You do not have to be alone."')
    world.say(f'{params.companion} smiled. "We will find you a safe home, one gentle step at a time."')
    world.say(scene.ending)
    world.say("The quiet clue had led to a brave kindness, and the kindness had made room for trust.")

    return StorySample(
        params=params,
        story=world.render(),
        prompts=[
            f"Write a heartwarming story about {params.name} noticing a tramp dog at {scene.place}.",
            f"Use foreshadowing: let {scene.clue} lead to a careful rescue.",
            "Include a brief dialogue in which kindness changes what the child decides to do.",
        ],
        story_qa=[
            QAItem(f"Where did {params.name} meet the tramp dog?",
                    f"{params.name} met the tramp dog at {scene.place}."),
            QAItem("What clue foreshadowed that the dog needed help?",
                    f"The clue was that {scene.clue}."),
            QAItem("Why did the child move slowly?",
                    f"{scene.danger.capitalize()}"),
            QAItem("How did the child and helper gain the dog's trust?",
                    f"They used {scene.tool} and {scene.action}."),
            QAItem("What changed at the end?",
                    f"The dog's whimper faded, and {scene.ending}."),
        ],
        world_qa=[
            QAItem("What is a tramp?",
                    "A tramp is a person or animal who wanders from place to place without a settled home."),
            QAItem("What is a whimper?",
                    "A whimper is a soft, unhappy sound often made when someone is afraid, hurt, or lonely."),
            QAItem("What is foreshadowing?",
                    "Foreshadowing is an early clue that hints at something important that will happen later."),
            QAItem("Why should people approach a frightened animal gently?",
                    "A gentle approach gives the animal space to feel safe instead of making it run or hide."),
        ],
        world=world,
    )


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts =="]
    lines.extend(f"{i}. {p}" for i, p in enumerate(sample.prompts, 1))
    lines.append("\n== (2) Story questions ==")
    for item in sample.story_qa:
        lines.extend([f"Q: {item.question}", f"A: {item.answer}"])
    lines.append("\n== (3) World knowledge questions ==")
    for item in sample.world_qa:
        lines.extend([f"Q: {item.question}", f"A: {item.answer}"])
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for entity in world.entities.values():
        lines.append(f"  {entity.id}: {entity.kind}, meters={entity.meters}, memes={entity.memes}")
    return "\n".join(lines)


ASP_RULES = """
safe_choice(Scene) :- place(Scene), clue(Scene).
rescued(Dog) :- safe_choice(Scene), dog(Dog), trust(Dog).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for scene in SCENES.values():
        lines.append(asp.fact("place", scene.id))
        lines.append(asp.fact("clue", scene.id))
    lines.append(asp.fact("dog", "tramp"))
    lines.append(asp.fact("trust", "tramp"))
    return "\n".join(lines)


def asp_program(show: str = "#show rescued/1.") -> str:
    return asp_facts() + "\n" + ASP_RULES + "\n" + show + "\n"


def asp_verify() -> int:
    import asp
    models = asp.solve(asp_program(), models=1)
    found = set(asp.atoms(models[0], "rescued")) if models else set()
    if found == {("tramp",)}:
        print("OK: ASP rescue gate agrees with the Python world.")
        return 0
    print("ASP verification failed.")
    return 1


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="A heartwarming tramp-and-whimper storyworld.")
    parser.add_argument("--scene", choices=SCENES)
    parser.add_argument("--name")
    parser.add_argument("--companion")
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
        print(asp_program())
        return

    base = args.seed if args.seed is not None else random.randrange(2**31)
    params_list = []
    if args.all:
        params_list = [
            StoryParams(scene=scene_id, name=NAMES[i % len(NAMES)],
                        companion=COMPANIONS[i % len(COMPANIONS)], seed=base + i)
            for i, scene_id in enumerate(SCENES)
        ]
    else:
        for i in range(max(0, args.n)):
            rng = random.Random(base + i)
            params = resolve_params(args, rng)
            params_list.append(StoryParams(params.scene, params.name, params.companion, base + i))

    samples = [generate(params) for params in params_list]
    if args.json:
        print(samples[0].to_json() if len(samples) == 1 else json.dumps(
            [sample.to_dict() for sample in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        if len(samples) > 1:
            print(f"### variant {i + 1}")
        print(sample.story)
        if args.trace:
            print(dump_trace(sample.world))
        if args.qa:
            print(format_qa(sample))
        if i + 1 < len(samples):
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()

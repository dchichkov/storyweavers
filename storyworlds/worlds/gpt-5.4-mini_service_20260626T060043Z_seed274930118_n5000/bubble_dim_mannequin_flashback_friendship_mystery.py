#!/usr/bin/env python3
"""
A small mystery storyworld about a bubble-dim mannequin, a friendship clue,
and a brief flashback that helps solve the problem.
"""

from __future__ import annotations

import argparse
import json
import os
import random
import sys
from dataclasses import dataclass, field
from typing import Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from results import QAItem, StoryError, StorySample  # noqa: E402


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    label: str = ""
    type: str = "thing"
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)
    owner: Optional[str] = None
    place: str = ""

    def pronoun(self, case: str = "subject") -> str:
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class Scene:
    place: str = "the attic"
    clue_place: str = "the hallway"
    afford_dim: bool = True
    afford_flashback: bool = True
    afford_friendship: bool = True


@dataclass
class MysteryItem:
    label: str
    type: str
    dim_state: str
    reveal_state: str


@dataclass
class StoryParams:
    place: str
    clue_place: str
    item: str
    hero_name: str
    friend_name: str
    seed: Optional[int] = None


SCENES = {
    "attic": Scene(place="the attic", clue_place="the dusty hallway"),
    "library": Scene(place="the library", clue_place="the back shelf"),
    "gallery": Scene(place="the gallery", clue_place="the long corridor"),
}

ITEMS = {
    "mannequin": MysteryItem(
        label="mannequin",
        type="mannequin",
        dim_state="looked bubble-dim",
        reveal_state="shone bright again",
    ),
    "bubble_dim_mannequin": MysteryItem(
        label="bubble-dim mannequin",
        type="mannequin",
        dim_state="turned bubble-dim",
        reveal_state="looked normal again",
    ),
}

HERO_NAMES = ["Mina", "Owen", "Lia", "Noah", "Tessa", "Eli"]
FRIEND_NAMES = ["Pip", "Jules", "Nina", "Sam", "Bea", "Rory"]


class World:
    def __init__(self, scene: Scene) -> None:
        self.scene = scene
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict[str, object] = {}

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)


def flashback_line(hero: str, friend: str, item: MysteryItem) -> str:
    return (
        f"{hero} remembered a flashback from yesterday, when {friend} had laughed "
        f"and said the {item.label} only looked strange in the half-light."
    )


def resolve_mystery(world: World, hero: Entity, friend: Entity, item: Entity) -> None:
    world.say(
        f"In the {world.scene.place}, {hero.id} found the {item.label} standing still "
        f"near a quiet mirror."
    )
    world.say(
        f"It was {item.meters.get('dim', 0):.0f} bubble-dim, and that made the room feel like a mystery."
    )
    world.para()
    world.say(
        f"{hero.id} and {friend.id} searched the {world.scene.clue_place} together."
    )
    world.say(
        f"Then {hero.id} noticed a tiny friendship note tucked behind the base."
    )
    world.say(flashback_line(hero.id, friend.id, ITEMS[item.type]))
    world.say(
        f"They opened the curtains, and the {item.label} {ITEMS[item.type].reveal_state}."
    )
    world.say(
        f"It was only the light after all, and the two friends smiled because the mystery had an easy answer."
    )


def build_world(params: StoryParams) -> World:
    scene = SCENES[params.place]
    world = World(scene)
    hero = world.add(Entity(id=params.hero_name, kind="character", type="child"))
    friend = world.add(Entity(id=params.friend_name, kind="character", type="child"))
    item_cfg = ITEMS[params.item]
    item = world.add(Entity(id="item", kind="thing", label=item_cfg.label, type=item_cfg.type))
    item.meters["dim"] = 1
    world.facts.update(hero=hero, friend=friend, item=item, item_cfg=item_cfg)
    world.say(
        f"{hero.id} and {friend.id} liked solving little mysteries together."
    )
    world.say(
        f"One evening, they went to {scene.place} and found a {item.label} that had gone bubble-dim."
    )
    world.para()
    world.say(
        f"{hero.id} felt curious, but also a little worried, because the dim shape looked odd in the shadows."
    )
    world.say(
        f"{friend.id} promised to help, and that made the search feel friendly instead of scary."
    )
    world.para()
    resolve_mystery(world, hero, friend, item)
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero: Entity = f["hero"]  # type: ignore[assignment]
    friend: Entity = f["friend"]  # type: ignore[assignment]
    item: Entity = f["item"]  # type: ignore[assignment]
    return [
        f'Write a short mystery story for a young child about a bubble-dim {item.label} in {world.scene.place}.',
        f"Tell a gentle story where {hero.id} and {friend.id} solve a small friendship mystery with a flashback clue.",
        f"Write a simple story that includes the words 'bubble-dim', 'mannequin', 'flashback', and 'friendship'.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero: Entity = f["hero"]  # type: ignore[assignment]
    friend: Entity = f["friend"]  # type: ignore[assignment]
    item: Entity = f["item"]  # type: ignore[assignment]
    return [
        QAItem(
            question=f"Who were the two friends in the story?",
            answer=f"The two friends were {hero.id} and {friend.id}. They worked together the whole time.",
        ),
        QAItem(
            question=f"What made the {item.label} look strange at first?",
            answer=f"The {item.label} looked bubble-dim because the room was shadowy and the light was weak.",
        ),
        QAItem(
            question="What flashback helped solve the mystery?",
            answer=(
                f"{hero.id} remembered that {friend.id} had said the {item.label} only looked strange in half-light, "
                f"so the friends checked the curtains and found the answer."
            ),
        ),
        QAItem(
            question="How did friendship help in the story?",
            answer=(
                f"Friendship helped because {friend.id} stayed calm, promised to help, and searched with {hero.id} until the mystery was solved."
            ),
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a mannequin?",
            answer="A mannequin is a human-shaped model used to show clothes or display items in a shop or room.",
        ),
        QAItem(
            question="What is a flashback in a story?",
            answer="A flashback is a memory of something that happened earlier, shown again so the reader can understand the present better.",
        ),
        QAItem(
            question="What does friendship mean?",
            answer="Friendship means people care about each other, help each other, and feel happier together.",
        ),
        QAItem(
            question="Why can shadows make something look mysterious?",
            answer="Shadows hide details, so a familiar thing can look odd or surprising until the light changes.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    out = ["== Story questions =="]
    for q in sample.story_qa:
        out.append(f"Q: {q.question}")
        out.append(f"A: {q.answer}")
    out.append("")
    out.append("== World questions ==")
    for q in sample.world_qa:
        out.append(f"Q: {q.question}")
        out.append(f"A: {q.answer}")
    return "\n".join(out)


def asp_facts() -> str:
    import storyworlds.asp as asp
    lines = [
        asp.fact("scene", "attic"),
        asp.fact("scene", "library"),
        asp.fact("scene", "gallery"),
        asp.fact("item", "mannequin"),
        asp.fact("item", "bubble_dim_mannequin"),
        asp.fact("theme", "flashback"),
        asp.fact("theme", "friendship"),
        asp.fact("theme", "mystery"),
        asp.fact("dims", "bubble_dim_mannequin"),
        asp.fact("dims", "mannequin"),
    ]
    return "\n".join(lines)


ASP_RULES = r"""
valid_story(S,I) :- scene(S), item(I), dims(I).
#show valid_story/2.
"""


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A small mystery storyworld with a bubble-dim mannequin.")
    ap.add_argument("--place", choices=SCENES.keys())
    ap.add_argument("--clue-place", choices=[s.clue_place for s in SCENES.values()])
    ap.add_argument("--item", choices=ITEMS.keys())
    ap.add_argument("--name")
    ap.add_argument("--friend")
    ap.add_argument("-n", type=int, default=1)
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--trace", action="store_true")
    ap.add_argument("--qa", action="store_true")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--asp", action="store_true")
    ap.add_argument("--verify", action="store_true")
    ap.add_argument("--show-asp", action="store_true")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    place = args.place or rng.choice(list(SCENES.keys()))
    scene = SCENES[place]
    clue_place = args.clue_place or scene.clue_place
    item = args.item or rng.choice(list(ITEMS.keys()))
    name = args.name or rng.choice(HERO_NAMES)
    friend = args.friend or rng.choice(FRIEND_NAMES)
    if name == friend:
        raise StoryError("The hero and friend must be different names.")
    return StoryParams(place=place, clue_place=clue_place, item=item, hero_name=name, friend_name=friend)


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
        print()
        print("--- trace ---")
        for e in sample.world.entities.values():
            print(f"{e.id}: kind={e.kind} label={e.label} meters={e.meters} memes={e.memes}")
    if qa:
        print()
        print(format_qa(sample))


def asp_verify() -> int:
    import storyworlds.asp as asp
    model = asp.one_model(asp_program("#show valid_story/2."))
    got = set(asp.atoms(model, "valid_story"))
    want = {("attic", "mannequin"), ("attic", "bubble_dim_mannequin"),
            ("library", "mannequin"), ("library", "bubble_dim_mannequin"),
            ("gallery", "mannequin"), ("gallery", "bubble_dim_mannequin")}
    if got == want:
        print(f"OK: clingo gate matches Python story set ({len(want)} combos).")
        return 0
    print("MISMATCH between clingo and Python story set.")
    print("only in clingo:", sorted(got - want))
    print("only in python:", sorted(want - got))
    return 1


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show valid_story/2."))
        return
    if args.verify:
        sys.exit(asp_verify())

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        for place in SCENES:
            for item in ITEMS:
                params = StoryParams(
                    place=place,
                    clue_place=SCENES[place].clue_place,
                    item=item,
                    hero_name=HERO_NAMES[0],
                    friend_name=FRIEND_NAMES[0],
                )
                samples.append(generate(params))
    else:
        i = 0
        seen: set[str] = set()
        while len(samples) < args.n and i < args.n * 40:
            seed = base_seed + i
            i += 1
            params = resolve_params(args, random.Random(seed))
            params.seed = seed
            sample = generate(params)
            if sample.story in seen:
                continue
            seen.add(sample.story)
            samples.append(sample)

    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for idx, sample in enumerate(samples):
        if len(samples) > 1:
            print(f"### variant {idx + 1}")
        emit(sample, trace=args.trace, qa=args.qa)
        if idx < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()

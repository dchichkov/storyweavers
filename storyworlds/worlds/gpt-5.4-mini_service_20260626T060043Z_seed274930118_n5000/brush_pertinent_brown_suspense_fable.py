#!/usr/bin/env python3
"""
A small fable-like storyworld about a brown brush, a pertinent problem, and a
suspenseful choice.
"""

from __future__ import annotations

import argparse
import dataclasses
import json
import os
import random
import sys
from dataclasses import dataclass, field
from typing import Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from results import QAItem, StoryError, StorySample  # noqa: E402


@dataclass
class Character:
    name: str
    kind: str
    memo: dict[str, float] = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=dict)

    def say(self, pronoun: str, case: str = "subject") -> str:
        if self.kind == "rabbit":
            return {"subject": "it", "object": "it", "possessive": "its"}[case]
        if self.kind == "fox":
            return {"subject": "it", "object": "it", "possessive": "its"}[case]
        return {"subject": pronoun, "object": pronoun, "possessive": pronoun + "'s"}[case]


@dataclass
class Brush:
    color: str = "brown"
    label: str = "brush"
    clean: bool = True
    helpful: bool = True
    owner: str = "Milo"


@dataclass
class World:
    place: str
    dusk: bool = True
    fog: bool = True
    characters: dict[str, Character] = field(default_factory=dict)
    brush: Brush = field(default_factory=Brush)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    facts: dict = field(default_factory=dict)
    fired: set[str] = field(default_factory=set)

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)


@dataclass
class StoryParams:
    place: str = "the hedge path"
    hero: str = "Milo"
    friend: str = "Pip"
    seed: Optional[int] = None


PLACES = {
    "hedge": "the hedge path",
    "bank": "the river bank",
    "orchard": "the orchard trail",
}

NAMES = ["Milo", "Pip", "Tara", "Nina", "Bram", "Luna"]
FRIENDS = ["Pip", "Dot", "Tess", "Hare", "Wren", "Fox"]
KIND_BY_NAME = {
    "Milo": "mouse",
    "Pip": "rabbit",
    "Tara": "mouse",
    "Nina": "mouse",
    "Bram": "badger",
    "Luna": "rabbit",
    "Dot": "bird",
    "Tess": "hedgehog",
    "Hare": "rabbit",
    "Fox": "fox",
}


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Brown brush suspense fable storyworld.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--name", choices=NAMES)
    ap.add_argument("--friend", choices=FRIENDS)
    ap.add_argument("-n", type=int, default=1)
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("--trace", action="store_true")
    ap.add_argument("--qa", action="store_true")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--asp", action="store_true")
    ap.add_argument("--verify", action="store_true")
    ap.add_argument("--show-asp", action="store_true")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    place = args.place or rng.choice(list(PLACES))
    hero = args.name or rng.choice(NAMES)
    friend = args.friend or rng.choice(FRIENDS)
    if hero == friend:
        raise StoryError("The hero and friend must be different characters.")
    return StoryParams(place=place, hero=hero, friend=friend, seed=None)


def make_world(params: StoryParams) -> World:
    world = World(place=PLACES[params.place])
    hero_kind = KIND_BY_NAME.get(params.hero, "mouse")
    friend_kind = KIND_BY_NAME.get(params.friend, "rabbit")
    world.characters[params.hero] = Character(name=params.hero, kind=hero_kind)
    world.characters[params.friend] = Character(name=params.friend, kind=friend_kind)
    world.brush.owner = params.hero
    return world


def introduce(world: World, hero: Character) -> None:
    world.say(
        f"In {world.place}, {hero.name} was a small {hero.kind} who liked neat paths and quiet mornings."
    )
    world.say(
        f"Under a shelf in the burrow, {hero.name} kept a brown brush, and that brush was very pertinent to the day."
    )


def suspense_turn(world: World, hero: Character, friend: Character) -> None:
    hero.memo["worry"] = 1.0
    world.say(
        f"That afternoon, fog drifted over {world.place}, and a narrow track vanished under tangled twigs."
    )
    world.say(
        f"{friend.name} whispered that something important had rolled into the thorns just beyond the bend."
    )
    world.say(
        f"{hero.name} peered ahead and saw only a brown shape trembling in the brush, which made the whole path feel suspenseful."
    )


def solve(world: World, hero: Character, friend: Character) -> None:
    hero.memo["bravery"] = 1.0
    world.say(
        f"{hero.name} took the brown brush in a careful paw and brushed the twigs aside one by one."
    )
    world.say(
        f"At last, the hidden thing turned out to be {friend.name}'s lost ribbon, snagged and waiting."
    )
    world.say(
        f"{friend.name} laughed with relief, and {hero.name} tucked the brush away again, glad that patience had helped more than fear."
    )
    world.say(
        f"By sunset, the path was clear, the ribbon was safe, and the brown brush had done a very kind day's work."
    )


def tell(params: StoryParams) -> World:
    world = make_world(params)
    hero = world.characters[params.hero]
    friend = world.characters[params.friend]
    introduce(world, hero)
    world.para()
    suspense_turn(world, hero, friend)
    world.para()
    solve(world, hero, friend)
    world.facts.update(
        place=params.place,
        hero=params.hero,
        friend=params.friend,
        brush_color=world.brush.color,
        brush_label=world.brush.label,
    )
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a short fable for children set at {f["place"]} about a brown brush and a suspenseful hidden problem.',
        f"Tell a gentle story where {f['hero']} uses a brown brush to solve a careful mystery for {f['friend']}.",
        'Write a suspenseful fable that includes the words "brown", "brush", and "pertinent".',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    return [
        QAItem(
            question=f"Who found the brown brush useful in the story?",
            answer=f"{f['hero']} found the brown brush useful because it helped clear the path and reveal the hidden ribbon.",
        ),
        QAItem(
            question=f"What made the middle of the story suspenseful?",
            answer=f"The middle felt suspenseful because fog hid the trail and something important was trembling in the brush.",
        ),
        QAItem(
            question=f"What did {f['friend']} lose?",
            answer=f"{f['friend']} lost a ribbon that had snagged in the thorns.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a brush used for?",
            answer="A brush is used to sweep, smooth, or clean things by moving its bristles across them.",
        ),
        QAItem(
            question="What does pertinent mean?",
            answer="Pertinent means closely connected to the matter at hand, so it matters to the problem being solved.",
        ),
        QAItem(
            question="What does brown mean?",
            answer="Brown is a color like earth, wood, or old leaves.",
        ),
    ]


def asp_facts() -> str:
    import storyworlds.asp as asp
    return "\n".join(
        [
            asp.fact("place", "hedge") + " " + asp.fact("place", "bank") + " " + asp.fact("place", "orchard"),
            asp.fact("brush", "brown"),
            asp.fact("quality", "pertinent"),
            asp.fact("quality", "suspenseful"),
        ]
    )


ASP_RULES = r"""
good_story(P) :- place(P).
"""  # minimal twin for parity checks


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import storyworlds.asp as asp
    model = asp.one_model(asp_program("#show good_story/1."))
    asp_places = sorted(set(asp.atoms(model, "good_story")))
    py_places = [(p,) for p in sorted(PLACES)]
    if asp_places == py_places:
        print(f"OK: clingo gate matches Python registry ({len(py_places)} places).")
        return 0
    print("MISMATCH between clingo and Python registry:")
    print("  clingo:", asp_places)
    print("  python:", py_places)
    return 1


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world is not None:
        print("--- world model state ---")
        print(f"place={sample.world.place}")
        print(f"brush={sample.world.brush.color} {sample.world.brush.label}")
        for name, char in sample.world.characters.items():
            print(f"{name}: kind={char.kind} memo={dict(char.memo)} meters={dict(char.meters)}")
    if qa:
        print()
        print("== prompts ==")
        for p in sample.prompts:
            print(p)
        print()
        print("== story qa ==")
        for item in sample.story_qa:
            print(f"Q: {item.question}")
            print(f"A: {item.answer}")
        print()
        print("== world qa ==")
        for item in sample.world_qa:
            print(f"Q: {item.question}")
            print(f"A: {item.answer}")


def generate(params: StoryParams) -> StorySample:
    world = tell(params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


CURATED = [
    StoryParams(place="hedge", hero="Milo", friend="Pip"),
    StoryParams(place="orchard", hero="Luna", friend="Fox"),
    StoryParams(place="bank", hero="Tara", friend="Dot"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show good_story/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import storyworlds.asp as asp
        model = asp.one_model(asp_program("#show good_story/1."))
        print(sorted(set(asp.atoms(model, "good_story"))))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)

    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
            params = resolve_params(args, random.Random(base_seed + i))
            sample = generate(params)
            if sample.story in seen:
                i += 1
                continue
            seen.add(sample.story)
            samples.append(sample)
            i += 1

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

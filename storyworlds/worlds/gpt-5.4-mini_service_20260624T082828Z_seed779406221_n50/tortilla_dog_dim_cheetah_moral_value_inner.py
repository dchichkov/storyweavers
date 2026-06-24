#!/usr/bin/env python3
"""
tortilla_dog_dim_cheetah_moral_value_inner.py
=============================================

A small Adventure-style story world about a tortilla, a dim dog, and a cheetah,
with a mystery to solve, an inner monologue, and a moral choice.

Premise:
A child explorer finds a missing tortilla on a trail near a windy lookout.
A dim but loyal dog wants to chase clues, while a quick cheetah knows how to
scan the high grass. The hero must choose between blaming the wrong creature
or listening carefully and solving the mystery.

World model:
- Physical state is tracked in meters: location, carried items, tracks, smell,
  hunger, distance, and clue strength.
- Emotional state is tracked in memes: worry, bravery, curiosity, guilt, trust,
  relief, and pride.
- The story resolves when the true cause is found and the hero makes a moral
  choice that helps someone instead of accusing them.

Seed words:
- tortilla
- dog-dim
- cheetah

Style:
- Adventure, child-facing, concrete, state-driven, with a clear mystery turn.
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

THRESHOLD = 1.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    friendly: bool = True
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.kind == "character":
            if self.type in {"girl", "child", "explorer"}:
                return {"subject": "she", "object": "her", "possessive": "her"}[case]
            if self.type in {"boy", "dog", "cheetah"}:
                return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def them(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Place:
    name: str
    indoors: bool = False
    windy: bool = False
    high_grass: bool = False
    trail: bool = True


@dataclass
class StoryParams:
    place: str
    hero: str
    hero_type: str
    dog_name: str
    cheetah_name: str
    tortilla_owner: str
    seed: Optional[int] = None


class World:
    def __init__(self, place: Place) -> None:
        self.place = place
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict[str, object] = {}
        self.fired: set[tuple] = set()

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str) -> Entity:
        return self.entities[eid]

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)

    def copy(self) -> "World":
        import copy
        c = World(self.place)
        c.entities = copy.deepcopy(self.entities)
        c.paragraphs = [[]]
        c.facts = dict(self.facts)
        c.fired = set(self.fired)
        return c


PLACES = {
    "trail": Place(name="the trail", indoors=False, windy=True, high_grass=True, trail=True),
    "canyon_edge": Place(name="the canyon edge", indoors=False, windy=True, high_grass=False, trail=True),
    "market_path": Place(name="the market path", indoors=False, windy=False, high_grass=False, trail=True),
    "sunny_gully": Place(name="the sunny gully", indoors=False, windy=False, high_grass=True, trail=True),
}

HERO_TYPES = {
    "girl": "girl",
    "boy": "boy",
    "child": "child",
}

CURIOUS_NAMES = ["Mina", "Toby", "Luna", "Iris", "Pico", "Nora", "Eli", "Zed"]
DOG_NAMES = ["Brindle", "Muffin", "Patch", "Scout"]
CHEETAH_NAMES = ["Suri", "Flash", "Tikka", "Dash"]


@dataclass
class Gear:
    id: str
    label: str
    helps_with: set[str]


@dataclass
class Mystery:
    title: str
    culprit: str
    clue_source: str
    moral_choice: str


GEAR = {
    "rope_tie": Gear(id="rope_tie", label="a rope tie", helps_with={"wind", "trail"}),
    "lantern": Gear(id="lantern", label="a tiny lantern", helps_with={"darkness", "search"}),
    "snack_bag": Gear(id="snack_bag", label="a snack bag", helps_with={"hunger", "share"}),
}

MYSTERIES = {
    "tortilla_missing": Mystery(
        title="the missing tortilla",
        culprit="wind",
        clue_source="crumbs and flutter marks",
        moral_choice="not blame the dim dog before checking the clues",
    )
}


def narration_intro(world: World, hero: Entity, dog: Entity, cheetah: Entity) -> None:
    world.say(
        f"{hero.id} was a curious little explorer who loved the trail and noticed small things."
    )
    world.say(
        f"{hero.id} traveled with {dog.id}, a dim but loyal dog, and {cheetah.id}, a fast cheetah who could spot clues in the grass."
    )


def setup_items(world: World, hero: Entity, tortilla_owner: Entity) -> Entity:
    tortilla = world.add(Entity(
        id="tortilla",
        kind="thing",
        type="food",
        label="tortilla",
        phrase="a warm tortilla wrapped in paper",
        owner=tortilla_owner.id,
        meters={"fresh": 1.0, "smell": 1.0},
        memes={"value": 1.0},
    ))
    world.say(
        f"{hero.id} carried a warm tortilla for the walk, and {tortilla_owner.id} said it should stay safe until lunch."
    )
    return tortilla


def smell_clue(world: World, tortilla: Entity) -> None:
    tortilla.meters["fresh"] -= 0.3
    tortilla.meters["smell"] += 0.2
    world.facts["clue_smell"] = tortilla.meters["smell"]
    world.say(
        "Soon the paper felt light in the wind, and a faint tortilla smell drifted along the path."
    )


def lose_tortilla(world: World, tortilla: Entity) -> None:
    tortilla.meters["lost"] = 1.0
    tortilla.owner = None
    world.say(
        "Then a gust swirled through the trail, and the tortilla slipped from the paper and vanished."
    )


def inner_monologue(world: World, hero: Entity, dog: Entity, cheetah: Entity) -> None:
    hero.memes["worry"] = hero.memes.get("worry", 0.0) + 1.0
    hero.memes["curiosity"] = hero.memes.get("curiosity", 0.0) + 1.0
    world.say(
        f"{hero.id} thought, 'I need to be careful. {dog.id} looks so eager, but I should not blame a friend just because the mystery is hard.'"
    )
    world.say(
        f"Inside, {hero.id} wondered whether the wind, the trail, or one of their helpers had nudged the tortilla away."
    )


def investigate(world: World, hero: Entity, dog: Entity, cheetah: Entity, tortilla: Entity) -> None:
    hero.meters["steps"] = hero.meters.get("steps", 0.0) + 4.0
    dog.meters["sniff"] = dog.meters.get("sniff", 0.0) + 1.0
    cheetah.meters["scan"] = cheetah.meters.get("scan", 0.0) + 1.0
    world.say(
        f"{dog.id} sniffed the dirt, and {cheetah.id} leaped to a rock to scan the high grass."
    )
    world.say(
        f"{cheetah.id} found flutter marks near the trail, while {dog.id} found only a half-circle of crumbs."
    )
    world.facts["clues"] = ["flutter marks", "crumbs", "wind"]
    tortilla.meters["lost"] = 1.0


def moral_turn(world: World, hero: Entity, dog: Entity, cheetah: Entity) -> None:
    hero.memes["guilt"] = hero.memes.get("guilt", 0.0) + 0.5
    hero.memes["trust"] = hero.memes.get("trust", 0.0) + 1.0
    world.say(
        f"{hero.id} almost guessed that {dog.id} had taken the tortilla, but the crumbs and flutter marks did not fit that idea."
    )
    world.say(
        f"{hero.id} said, 'No, {dog.id} is helping. We should trust the clues and not jump to the wrong answer.'"
    )
    world.say(
        f"That was the moral choice: it was kinder and wiser to look again than to blame a loyal friend."
    )


def resolve(world: World, hero: Entity, dog: Entity, cheetah: Entity, tortilla: Entity) -> None:
    tortilla.owner = hero.id
    tortilla.meters["fresh"] = 0.9
    hero.memes["relief"] = hero.memes.get("relief", 0.0) + 1.0
    hero.memes["pride"] = hero.memes.get("pride", 0.0) + 1.0
    world.say(
        f"At last {cheetah.id} led them to a low branch where the tortilla had snagged in a strip of paper."
    )
    world.say(
        f"{hero.id} lifted it free, laughed with relief, and shared a grateful pat for {dog.id} and a happy grin for {cheetah.id}."
    )
    world.say(
        f"The tortilla was safe again, and {hero.id} walked on with a clearer heart."
    )


def tell_story(params: StoryParams) -> World:
    place = PLACES[params.place]
    world = World(place)

    hero = world.add(Entity(id=params.hero, kind="character", type=params.hero_type))
    dog = world.add(Entity(id=params.dog_name, kind="character", type="dog", friendly=True, meters={"sniff": 0.0}, memes={"loyalty": 1.0}))
    cheetah = world.add(Entity(id=params.cheetah_name, kind="character", type="cheetah", friendly=True, meters={"scan": 0.0}, memes={"speed": 1.0}))
    owner = world.add(Entity(id=params.tortilla_owner, kind="character", type="adult", friendly=True))

    tortilla = setup_items(world, hero, owner)
    narration_intro(world, hero, dog, cheetah)
    world.para()
    smell_clue(world, tortilla)
    lose_tortilla(world, tortilla)
    inner_monologue(world, hero, dog, cheetah)
    world.para()
    investigate(world, hero, dog, cheetah, tortilla)
    moral_turn(world, hero, dog, cheetah)
    world.para()
    resolve(world, hero, dog, cheetah, tortilla)

    world.facts.update(
        hero=hero,
        dog=dog,
        cheetah=cheetah,
        tortilla=tortilla,
        owner=owner,
        place=place,
        mystery=MYSTERIES["tortilla_missing"],
        resolved=True,
    )
    return world


def valid_places() -> list[str]:
    return list(PLACES.keys())


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Adventure storyworld: tortilla, dog-dim, and cheetah solve a mystery.")
    ap.add_argument("--place", choices=valid_places())
    ap.add_argument("--hero")
    ap.add_argument("--hero-type", choices=list(HERO_TYPES))
    ap.add_argument("--dog-name")
    ap.add_argument("--cheetah-name")
    ap.add_argument("--tortilla-owner")
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
    place = args.place or rng.choice(valid_places())
    hero_type = args.hero_type or rng.choice(["girl", "boy", "child"])
    hero = args.hero or rng.choice(CURIOUS_NAMES)
    dog_name = args.dog_name or rng.choice(DOG_NAMES)
    cheetah_name = args.cheetah_name or rng.choice(CHEETAH_NAMES)
    tortilla_owner = args.tortilla_owner or "Aunt Ray"
    return StoryParams(
        place=place,
        hero=hero,
        hero_type=hero_type,
        dog_name=dog_name,
        cheetah_name=cheetah_name,
        tortilla_owner=tortilla_owner,
    )


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    dog = f["dog"]
    cheetah = f["cheetah"]
    return [
        f"Write a short adventure story for a child named {hero.id} who loses a tortilla on {f['place'].name}.",
        f"Tell a mystery story where {dog.id}, a dim but loyal dog, and {cheetah.id}, a clever cheetah, help find a missing tortilla.",
        "Write a gentle adventure with an inner monologue, a moral choice, and a clear clue-driven ending.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    dog = f["dog"]
    cheetah = f["cheetah"]
    tortilla = f["tortilla"]
    owner = f["owner"]
    place = f["place"].name
    return [
        QAItem(
            question=f"Who was the story about on {place}?",
            answer=f"It was about {hero.id}, who went adventuring with {dog.id} the dim dog and {cheetah.id} the cheetah.",
        ),
        QAItem(
            question=f"What mystery did {hero.id} need to solve?",
            answer=f"{hero.id} needed to solve the mystery of the missing tortilla.",
        ),
        QAItem(
            question=f"Why didn't {hero.id} blame {dog.id} for the missing tortilla?",
            answer=f"{hero.id} noticed the crumbs and flutter marks did not match a dog being naughty, so it was more honest to trust the clues than to blame {dog.id}.",
        ),
        QAItem(
            question=f"What happened at the end to the tortilla?",
            answer=f"The tortilla was found snagged on a low branch, and {hero.id} lifted it free and kept it safe again for {owner.id}.",
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a tortilla?",
            answer="A tortilla is a soft flat bread that people can fill or eat with meals.",
        ),
        QAItem(
            question="What is a cheetah?",
            answer="A cheetah is a very fast wild cat with spots and long legs.",
        ),
        QAItem(
            question="Why do dogs sniff the ground?",
            answer="Dogs sniff the ground because their noses help them find scents and clues.",
        ),
        QAItem(
            question="What does it mean to be fair?",
            answer="Being fair means listening carefully and not blaming someone without a good reason.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== Generation prompts =="]
    for p in sample.prompts:
        lines.append(f"- {p}")
    lines.append("")
    lines.append("== Story Q&A ==")
    for qa in sample.story_qa:
        lines.append(f"Q: {qa.question}")
        lines.append(f"A: {qa.answer}")
    lines.append("")
    lines.append("== World Q&A ==")
    for qa in sample.world_qa:
        lines.append(f"Q: {qa.question}")
        lines.append(f"A: {qa.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for e in world.entities.values():
        parts = []
        if e.meters:
            parts.append(f"meters={e.meters}")
        if e.memes:
            parts.append(f"memes={e.memes}")
        lines.append(f"{e.id} ({e.type}): " + ", ".join(parts))
    return "\n".join(lines)


ASP_RULES = r"""
hero(X) :- character(X), hero_role(X).
dog(X) :- character(X), dog_role(X).
cheetah(X) :- character(X), cheetah_role(X).

at_risk(tortilla) :- windy(place), tortilla_present(tortilla).
clue(wind) :- flutter_marks.
clue(not_dog) :- crumbs, loyal_dog.

fair_choice(hero) :- clue(wind), clue(not_dog), not blame_dog.
moral_value(hero) :- fair_choice(hero), trust_clues.
resolved(tortilla) :- found_on_branch, lifted_free.

#show at_risk/1.
#show fair_choice/1.
#show resolved/1.
"""


def asp_facts() -> str:
    import asp
    lines = []
    for name, place in PLACES.items():
        lines.append(asp.fact("place", name))
        if place.windy:
            lines.append(asp.fact("windy", name))
        if place.high_grass:
            lines.append(asp.fact("high_grass", name))
    lines.append(asp.fact("tortilla_present", "tortilla"))
    lines.append(asp.fact("flutter_marks"))
    lines.append(asp.fact("crumbs"))
    lines.append(asp.fact("loyal_dog"))
    lines.append(asp.fact("trust_clues"))
    lines.append(asp.fact("found_on_branch"))
    lines.append(asp.fact("lifted_free"))
    lines.append(asp.fact("hero_role", "hero"))
    lines.append(asp.fact("dog_role", "dog"))
    lines.append(asp.fact("cheetah_role", "cheetah"))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show at_risk/1. #show fair_choice/1. #show resolved/1."))
    atoms = set((sym.name, tuple(getattr(a, "name", getattr(a, "string", getattr(a, "number", None))) for a in sym.arguments)) for sym in model)
    expected = {("at_risk", ("tortilla",)), ("fair_choice", ("hero",)), ("resolved", ("tortilla",))}
    if atoms == expected:
        print("OK: ASP parity matches Python world logic.")
        return 0
    print("MISMATCH:")
    print("  asp:", sorted(atoms))
    print("  expected:", sorted(expected))
    return 1


def asp_validity() -> list[tuple[str]]:
    import asp
    model = asp.one_model(asp_program("#show at_risk/1."))
    return sorted(set(asp.atoms(model, "at_risk")))


def generate(params: StoryParams) -> StorySample:
    world = tell_story(params)
    story = world.render()
    return StorySample(
        params=params,
        story=story,
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
        print(asp_program("#show at_risk/1. #show fair_choice/1. #show resolved/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        model = asp.one_model(asp_program("#show at_risk/1. #show fair_choice/1. #show resolved/1."))
        print("\n".join(str(a) for a in model))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        curated = [
            StoryParams(place="trail", hero="Mina", hero_type="girl", dog_name="Brindle", cheetah_name="Suri", tortilla_owner="Aunt Ray"),
            StoryParams(place="sunny_gully", hero="Toby", hero_type="boy", dog_name="Scout", cheetah_name="Flash", tortilla_owner="Uncle Jae"),
            StoryParams(place="market_path", hero="Luna", hero_type="child", dog_name="Patch", cheetah_name="Tikka", tortilla_owner="Grandma Sol"),
        ]
        samples = [generate(p) for p in curated]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 50, 50):
            rng = random.Random(base_seed + i)
            i += 1
            params = resolve_params(args, rng)
            params.seed = base_seed + i
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

    for i, sample in enumerate(samples):
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.hero} on {p.place} with {p.dog_name} and {p.cheetah_name}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()

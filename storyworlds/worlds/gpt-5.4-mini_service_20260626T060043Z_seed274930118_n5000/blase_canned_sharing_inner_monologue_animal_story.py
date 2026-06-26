#!/usr/bin/env python3
"""
Animal-story world: a blase animal, a canned treat, sharing, and inner monologue.

A small classical story simulation about a pet or woodland animal who acts
blase about a canned snack, thinks to itself, and learns to share.
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
class Creature:
    name: str
    species: str
    role: str = "animal"
    kind: str = "character"
    meters: dict[str, float] = field(default_factory=lambda: {"hunger": 0.0})
    memes: dict[str, float] = field(default_factory=lambda: {"blase": 0.0, "kindness": 0.0, "greed": 0.0, "joy": 0.0})
    inventory: list[str] = field(default_factory=list)

    def pronoun(self) -> str:
        return "it"

    def poss(self) -> str:
        return "its"


@dataclass
class CannedItem:
    label: str = "canned treat"
    kind: str = "food"
    sealed: bool = True
    opened: bool = False
    shared_with: list[str] = field(default_factory=list)
    meters: dict[str, float] = field(default_factory=lambda: {"fullness": 1.0})
    memes: dict[str, float] = field(default_factory=dict)


@dataclass
class Setting:
    place: str = "the sunny yard"
    description: str = "a quiet place with a bowl, a fence, and a warm patch of grass"


@dataclass
class StoryParams:
    place: str = "the sunny yard"
    hero_name: str = "Milo"
    hero_species: str = "cat"
    friend_name: str = "Pip"
    friend_species: str = "rabbit"
    seed: Optional[int] = None


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, object] = {}
        self.events: list[str] = []
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict[str, object] = {}

    def add(self, eid: str, obj: object) -> object:
        self.entities[eid] = obj
        return obj

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)


def _animal_article(species: str) -> str:
    return "an" if species[:1].lower() in "aeiou" else "a"


def _inner_monologue(creature: Creature, item: CannedItem) -> str:
    if creature.memes["blase"] >= 1.0:
        return f"{creature.name} thought, 'It's only a canned treat. I don't need to fuss over it.'"
    if creature.meters["hunger"] >= 1.0:
        return f"{creature.name} thought, 'I am very hungry, and that can smells too good to keep to myself.'"
    return f"{creature.name} thought, 'Maybe sharing would make this snack more fun.'"


def _open_can(world: World, hero: Creature, item: CannedItem) -> None:
    item.sealed = False
    item.opened = True
    hero.meters["hunger"] += 1.0
    hero.memes["joy"] += 0.5
    world.say(
        f"In {world.setting.place}, {hero.name} found a shiny canned treat near the bowl."
    )
    world.say(
        f"{hero.name} sniffed it, then shrugged in a blase way."
    )
    world.say(_inner_monologue(hero, item))
    world.say(f"At last, {hero.name} popped the can open.")
    world.facts["opened"] = True


def _watch_friend(world: World, hero: Creature, friend: Creature, item: CannedItem) -> None:
    world.say(
        f"Then {friend.name} came closer and looked at the open can with hopeful eyes."
    )
    world.say(
        f"{hero.name} noticed {friend.name} waiting and felt a little tug in its chest."
    )
    hero.memes["kindness"] += 1.0
    hero.memes["greed"] += 0.5
    world.say(
        f"{hero.name} thought, 'I could keep every bite, but sharing might feel nicer.'"
    )
    world.facts["friend_watching"] = True


def _share(world: World, hero: Creature, friend: Creature, item: CannedItem) -> None:
    if not item.opened:
        raise StoryError("The canned treat must be opened before sharing.")
    item.shared_with.append(friend.name)
    hero.memes["joy"] += 1.0
    friend.memes["joy"] += 1.0
    hero.memes["blase"] = max(0.0, hero.memes["blase"] - 0.5)
    world.say(
        f"{hero.name} tipped the can toward {friend.name} and shared the snack."
    )
    world.say(
        f"{friend.name} nibbled happily, and the two animals ate together in the warm light."
    )
    world.say(
        f"By the end, {hero.name} was no longer blase. It felt proud of being kind."
    )
    world.facts["shared"] = True


def tell(params: StoryParams) -> World:
    world = World(Setting(place=params.place))
    hero = world.add("hero", Creature(name=params.hero_name, species=params.hero_species))
    friend = world.add("friend", Creature(name=params.friend_name, species=params.friend_species))
    can = world.add("can", CannedItem())

    hero.memes["blase"] = 1.0
    hero.meters["hunger"] = 0.5

    world.say(
        f"{hero.name} was {_animal_article(hero.species)} {hero.species} with a blase look and a soft tail."
    )
    world.say(
        f"{friend.name} was {_animal_article(friend.species)} {friend.species} who loved a friendly snack."
    )
    world.say(
        f"One afternoon at {world.setting.place}, a canned treat waited beside a little bowl."
    )

    world.para()
    _open_can(world, hero, can)
    _watch_friend(world, hero, friend, can)

    world.para()
    _share(world, hero, friend, can)

    world.facts.update(
        hero=hero,
        friend=friend,
        can=can,
        params=params,
        setting=world.setting,
    )
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero: Creature = f["hero"]
    friend: Creature = f["friend"]
    return [
        f"Write a short animal story about {hero.name}, a blase {hero.species}, and a canned treat.",
        f"Tell a gentle story where {hero.name} thinks quietly to itself and then shares food with {friend.name}.",
        f"Make a tiny animal story that includes sharing, inner monologue, and a canned snack at {world.setting.place}.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero: Creature = f["hero"]
    friend: Creature = f["friend"]
    can: CannedItem = f["can"]
    return [
        QAItem(
            question=f"Who found the canned treat at {world.setting.place}?",
            answer=f"{hero.name} found the canned treat at {world.setting.place}."
        ),
        QAItem(
            question=f"What did {hero.name} do after thinking to itself about the can?",
            answer=f"{hero.name} opened the can and then shared the snack with {friend.name}."
        ),
        QAItem(
            question=f"How did the story end for {hero.name}?",
            answer=f"The story ended with {hero.name} feeling proud and less blase after sharing."
        ),
        QAItem(
            question=f"Did {friend.name} get to eat from the can?",
            answer=f"Yes. {hero.name} shared the open canned treat, so {friend.name} ate happily too."
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does sharing mean?",
            answer="Sharing means letting someone else use, enjoy, or eat part of something with you."
        ),
        QAItem(
            question="What is a canned food item?",
            answer="A canned food item is food sealed inside a metal can so it stays fresh until it is opened."
        ),
        QAItem(
            question="What is an inner monologue?",
            answer="An inner monologue is the quiet thinking a character does inside its own head."
        ),
    ]


def format_qa(sample: StorySample) -> str:
    out = ["== Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        out.append(f"{i}. {p}")
    out.append("")
    out.append("== Story QA ==")
    for q in sample.story_qa:
        out.append(f"Q: {q.question}")
        out.append(f"A: {q.answer}")
    out.append("")
    out.append("== World QA ==")
    for q in sample.world_qa:
        out.append(f"Q: {q.question}")
        out.append(f"A: {q.answer}")
    return "\n".join(out)


ASP_RULES = r"""
hero(H). friend(F). can(C).
blase(H) :- hero(H).
opened(C) :- can(C), opened_can(C).
shared(H,F,C) :- opened(C), hero(H), friend(F), can(C).
happy(H) :- shared(H,_,_).
happy(F) :- shared(_,F,_).
"""


def asp_facts() -> str:
    import asp
    return "\n".join([
        asp.fact("hero", "hero"),
        asp.fact("friend", "friend"),
        asp.fact("can", "can"),
        asp.fact("opened_can", "can"),
    ])


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Animal story world with sharing and inner monologue.")
    ap.add_argument("--place", default=None)
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("-n", type=int, default=1)
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--trace", action="store_true")
    ap.add_argument("--qa", action="store_true")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--asp", action="store_true")
    ap.add_argument("--verify", action="store_true")
    ap.add_argument("--show-asp", action="store_true")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    place = args.place or rng.choice(["the sunny yard", "the quiet porch", "the little barn"])
    return StoryParams(
        place=place,
        hero_name=rng.choice(["Milo", "Nori", "Penny", "Toto", "Luna"]),
        hero_species=rng.choice(["cat", "fox", "raccoon", "bear", "mouse"]),
        friend_name=rng.choice(["Pip", "Mimi", "Dot", "Bram", "Kiki"]),
        friend_species=rng.choice(["rabbit", "dog", "hedgehog", "squirrel", "duck"]),
        seed=args.seed,
    )


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


def dump_trace(world: World) -> str:
    hero: Creature = world.entities["hero"]
    friend: Creature = world.entities["friend"]
    can: CannedItem = world.entities["can"]
    return "\n".join([
        "--- world trace ---",
        f"place: {world.setting.place}",
        f"hero: {hero.name} {hero.species} meters={hero.meters} memes={hero.memes}",
        f"friend: {friend.name} {friend.species} meters={friend.meters} memes={friend.memes}",
        f"can: sealed={can.sealed} opened={can.opened} shared_with={can.shared_with}",
    ])


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world is not None:
        print(dump_trace(sample.world))
    if qa:
        print()
        print(format_qa(sample))


def asp_verify() -> int:
    try:
        import asp
    except Exception as exc:  # pragma: no cover
        print(f"ASP unavailable: {exc}")
        return 1
    model = asp.one_model(asp_program("#show shared/3. #show happy/1."))
    shared = set(asp.atoms(model, "shared"))
    if ("hero", "friend", "can") not in shared:
        print("MISMATCH: ASP model did not derive sharing.")
        return 1
    print("OK: ASP twin derives sharing as expected.")
    return 0


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show shared/3. #show happy/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        model = asp.one_model(asp_program("#show shared/3. #show happy/1."))
        print("shared:", asp.atoms(model, "shared"))
        print("happy:", asp.atoms(model, "happy"))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        params_list = [
            StoryParams(place="the sunny yard", hero_name="Milo", hero_species="cat", friend_name="Pip", friend_species="rabbit"),
            StoryParams(place="the quiet porch", hero_name="Nori", hero_species="fox", friend_name="Mimi", friend_species="duck"),
            StoryParams(place="the little barn", hero_name="Penny", hero_species="bear", friend_name="Dot", friend_species="squirrel"),
        ]
        samples = [generate(p) for p in params_list]
    else:
        for i in range(args.n):
            params = resolve_params(args, random.Random(base_seed + i))
            samples.append(generate(params))

    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()

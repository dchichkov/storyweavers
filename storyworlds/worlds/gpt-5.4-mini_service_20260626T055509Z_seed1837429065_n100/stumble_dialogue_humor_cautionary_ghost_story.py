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
from results import QAItem, StoryError, StorySample  # noqa: E402


@dataclass
class Place:
    key: str
    label: str
    eerie: str
    affords: set[str] = field(default_factory=set)


@dataclass
class Item:
    key: str
    label: str
    phrase: str
    light: bool = False
    fragile: bool = False


@dataclass
class Character:
    key: str
    name: str
    role: str
    pronoun_subject: str
    pronoun_object: str
    pronoun_possessive: str
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def say(self, text: str) -> str:
        return f'"{text}"'


@dataclass
class StoryParams:
    place: str
    hero_name: str
    companion_name: str
    item: str
    seed: Optional[int] = None


@dataclass
class World:
    place: Place
    hero: Character
    companion: Character
    item: Item
    moon: str = "thin"
    house_noise: str = "soft creaks"
    fired: set[tuple] = field(default_factory=set)
    lines: list[str] = field(default_factory=list)
    facts: dict = field(default_factory=dict)

    def say(self, text: str) -> None:
        if text:
            self.lines.append(text)

    def render(self) -> str:
        return "\n\n".join(self.lines)


PLACES = {
    "old_house": Place(
        key="old_house",
        label="the old house at the end of the lane",
        eerie="Its windows looked like sleepy eyes, and the hallway kept a cold hush.",
        affords={"stumble", "whisper"},
    ),
    "cellar": Place(
        key="cellar",
        label="the cellar under the bakery",
        eerie="The stairs went down like a throat, and the air smelled of dust and apples.",
        affords={"stumble", "whisper"},
    ),
    "attic": Place(
        key="attic",
        label="the attic above the library",
        eerie="The rafters leaned close, and old trunks made the room feel full of secrets.",
        affords={"stumble", "whisper"},
    ),
}

ITEMS = {
    "lantern": Item(key="lantern", label="lantern", phrase="a little brass lantern", light=True),
    "key": Item(key="key", label="key", phrase="a tiny iron key", fragile=False),
    "ribbon": Item(key="ribbon", label="ribbon", phrase="a pale blue ribbon", fragile=True),
}

HEROES = ["Mina", "Theo", "Lina", "Eli", "June", "Pip", "Noa", "Iris"]
COMPANIONS = ["Grandma", "Uncle Remy", "Aunt Sol", "Mr. Bell", "Nana"]
ADVENTURE_VERBS = {
    "stumble": "stumble",
    "whisper": "whisper",
}


def _make_char(name: str, role: str, pronouns: tuple[str, str, str]) -> Character:
    return Character(
        key=name.lower(),
        name=name,
        role=role,
        pronoun_subject=pronouns[0],
        pronoun_object=pronouns[1],
        pronoun_possessive=pronouns[2],
    )


def _hero_pronouns(seed: int) -> tuple[str, str, str]:
    return (("she", "her", "her") if seed % 2 == 0 else ("he", "him", "his"))


def _companion_pronouns() -> tuple[str, str, str]:
    return ("they", "them", "their")


def valid_combos() -> list[tuple[str, str]]:
    combos = []
    for p in PLACES:
        for i in ITEMS:
            combos.append((p, i))
    return combos


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Ghost-story world: a child, a dark place, a stumble, and a cautionary turn."
    )
    ap.add_argument("--place", choices=sorted(PLACES))
    ap.add_argument("--item", choices=sorted(ITEMS))
    ap.add_argument("--hero-name")
    ap.add_argument("--companion-name")
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
    if args.place and args.place not in PLACES:
        raise StoryError(f"Unknown place: {args.place}")
    if args.item and args.item not in ITEMS:
        raise StoryError(f"Unknown item: {args.item}")
    combos = [c for c in valid_combos()
              if (args.place is None or c[0] == args.place)
              and (args.item is None or c[1] == args.item)]
    if not combos:
        raise StoryError("No valid story matches those choices.")
    place, item = rng.choice(sorted(combos))
    hero_name = args.hero_name or rng.choice(HEROES)
    companion_name = args.companion_name or rng.choice(COMPANIONS)
    return StoryParams(place=place, hero_name=hero_name, companion_name=companion_name, item=item)


def _build_world(params: StoryParams) -> World:
    place = PLACES[params.place]
    item = ITEMS[params.item]
    hero = _make_char(params.hero_name, "child", _hero_pronouns(sum(map(ord, params.hero_name))))
    companion = _make_char(params.companion_name, "elder", _companion_pronouns())
    return World(place=place, hero=hero, companion=companion, item=item)


def _setup(world: World) -> None:
    world.say(f"{world.hero.name} and {world.companion.name} went to {world.place.label}.")
    world.say(world.place.eerie)
    if world.item.light:
        world.say(
            f"{world.hero.name} carried {world.hero.pronoun_possessive} {world.item.phrase} like a tiny brave star."
        )
    else:
        world.say(
            f"{world.hero.name} clutched {world.hero.pronoun_possessive} {world.item.phrase} and tried not to think about the dark."
        )


def _warn(world: World) -> None:
    world.hero.memes["curiosity"] = world.hero.memes.get("curiosity", 0.0) + 1
    world.companion.memes["caution"] = world.companion.memes.get("caution", 0.0) + 1
    world.say(
        f"{world.companion.name} said, {world.companion.say('Mind the stairs. Old places like this love a surprise.')}"
    )
    world.say(
        f"{world.hero.name} answered, {world.hero.say('I will. I am not scared at all.')}"
    )


def _stumble(world: World) -> None:
    world.hero.meters["stumble"] = world.hero.meters.get("stumble", 0.0) + 1
    world.hero.memes["fright"] = world.hero.memes.get("fright", 0.0) + 1
    world.companion.memes["alarm"] = world.companion.memes.get("alarm", 0.0) + 1
    world.say(
        f"Then {world.hero.name} stumbled on a loose board, and the lantern bobbled in {world.hero.pronoun_possessive} hand."
    )
    world.say(
        f"{world.companion.name} gasped, {world.companion.say('Easy there! The floor is telling on itself.')}"
    )


def _humor_and_caution(world: World) -> None:
    if world.item.light:
        world.say(
            f"The little brass lantern blinked its warm circle across the wall, and for one silly second the shadow of a coat hook looked like a crooked ghost."
        )
    elif world.item.key:
        world.say(
            f"The tiny iron key skittered across the boards and chimed like a nervous spoon."
        )
    else:
        world.say(
            f"The pale blue ribbon fluttered up and landed on {world.hero.name}'s nose, which made the dark seem less fierce and more ridiculous."
        )
    world.say(
        f"{world.hero.name} let out a shaky laugh and said, {world.hero.say('I guess old houses like to make me dance.')}"
    )
    world.say(
        f"{world.companion.name} smiled, but {world.companion.say('A joke is good. A watchful step is better.')}"
    )


def _resolve(world: World) -> None:
    world.hero.memes["relief"] = world.hero.memes.get("relief", 0.0) + 1
    world.companion.memes["relief"] = world.companion.memes.get("relief", 0.0) + 1
    world.say(
        f"{world.companion.name} steadied {world.hero.name} by the elbow, and together they took the stairs one careful step at a time."
    )
    world.say(
        f"At the top, {world.hero.name} found {world.hero.pronoun_possessive} footing again, and the old house went back to being only a house."
    )
    world.say(
        f"{world.hero.name} tucked {world.hero.pronoun_possessive} {world.item.label} safely away and said, {world.hero.say('Next time, I will watch my feet as well as the shadows.')}"
    )


def generate(params: StoryParams) -> StorySample:
    world = _build_world(params)
    _setup(world)
    world.lines.append("")
    _warn(world)
    _stumble(world)
    _humor_and_caution(world)
    world.lines.append("")
    _resolve(world)
    world.facts = {
        "place": world.place.key,
        "hero_name": world.hero.name,
        "companion_name": world.companion.name,
        "item": world.item.key,
        "stumbled": True,
        "cautionary": True,
        "humor": True,
    }
    prompts = [
        f'Write a short ghost story for children that includes the word "stumble" and a gentle warning.',
        f"Tell a spooky-but-kind story about {world.hero.name} and {world.companion.name} at {world.place.label}.",
        f'Write a brief story where someone stumbles, hears a spooky joke, and learns to be careful.',
    ]
    story_qa = [
        QAItem(
            question=f"Why did {world.companion.name} warn {world.hero.name} at {world.place.label}?",
            answer=f"{world.companion.name} warned {world.hero.name} because the place was dark and old, and the stairs could surprise a careful walker.",
        ),
        QAItem(
            question=f"What happened after {world.hero.name} stumbled?",
            answer=f"{world.hero.name} stumbled on a loose board, got a little frightened, and then {world.companion.name} steadied {world.hero.pronoun_object} and helped {world.hero.name} keep going.",
        ),
        QAItem(
            question=f"How did the story keep from becoming too scary?",
            answer=f"The story added a small joke about a shadow, so the ghostly moment stayed playful while still reminding {world.hero.name} to be careful.",
        ),
    ]
    world_qa = [
        QAItem(
            question="What does it mean to stumble?",
            answer="To stumble means to trip or lose your footing for a moment.",
        ),
        QAItem(
            question="Why do people carry lanterns in dark places?",
            answer="People carry lanterns so they can see the floor, the stairs, and anything they might trip over.",
        ),
    ]
    return StorySample(params=params, story=world.render(), prompts=prompts, story_qa=story_qa, world_qa=world_qa, world=world)


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world is not None:
        print(dump_trace(sample.world))
    if qa:
        print()
        print(format_qa(sample))


def dump_trace(world: World) -> str:
    parts = ["--- world model state ---"]
    parts.append(f"place={world.place.key}")
    parts.append(f"hero={world.hero.name} meters={world.hero.meters} memes={world.hero.memes}")
    parts.append(f"companion={world.companion.name} meters={world.companion.meters} memes={world.companion.memes}")
    parts.append(f"item={world.item.key}")
    return "\n".join(parts)


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== (2) Story questions ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== (3) World-knowledge questions ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


ASP_RULES = r"""
place(P) :- setting(P).
story(P,I) :- place(P), item(I).
cautionary(P,I) :- story(P,I), risky(P), light(I).
risky(old_house).
risky(cellar).
risky(attic).
light(lantern).
valid(P,I) :- story(P,I), cautionary(P,I).
#show valid/2.
"""


def asp_facts() -> str:
    import storyworlds.asp as asp
    lines: list[str] = []
    for p in PLACES.values():
        lines.append(asp.fact("setting", p.key))
        if "stumble" in p.affords:
            lines.append(asp.fact("risky", p.key))
    for i in ITEMS.values():
        lines.append(asp.fact("item", i.key))
        if i.light:
            lines.append(asp.fact("light", i.key))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import storyworlds.asp as asp
    model = asp.one_model(asp_program("#show valid/2."))
    clingo_set = set(asp.atoms(model, "valid"))
    py_set = set((p, i) for p, i in valid_combos() if PLACES[p].key in {"old_house", "cellar", "attic"} and ITEMS[i].light)
    if clingo_set == py_set:
        print(f"OK: clingo gate matches Python gate ({len(clingo_set)} combos).")
        return 0
    print("MISMATCH between clingo and Python gate:")
    print("only in clingo:", sorted(clingo_set - py_set))
    print("only in python:", sorted(py_set - clingo_set))
    return 1


def build_asp_story_list() -> list[tuple[str, str]]:
    import storyworlds.asp as asp
    model = asp.one_model(asp_program("#show valid/2."))
    return sorted(set(asp.atoms(model, "valid")))


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        items = build_asp_story_list()
        for p, i in items:
            print(f"{p} {i}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        curated = [
            StoryParams(place="old_house", hero_name="Mina", companion_name="Grandma", item="lantern"),
            StoryParams(place="cellar", hero_name="Theo", companion_name="Mr. Bell", item="key"),
            StoryParams(place="attic", hero_name="Lina", companion_name="Aunt Sol", item="ribbon"),
        ]
        samples = [generate(p) for p in curated]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
            rng = random.Random(base_seed + i)
            i += 1
            try:
                params = resolve_params(args, rng)
            except StoryError as err:
                print(err)
                return
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

    for idx, sample in enumerate(samples):
        header = ""
        if len(samples) > 1:
            header = f"### variant {idx + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if idx < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
